import { useEffect, useMemo, useRef, useState } from 'react';
import FlashcardDeck from './FlashcardDeck';
import {
  combinePracticeShards,
  czNorm,
  isWrongCaseAnswer,
  loadState,
  masteredCount,
  rateCard,
  selectNextPracticeItem,
  uaPlural,
  validateClozeOptions,
  type ChoicePolarity,
  type PracticeClozeItem,
  type PracticeDeckData,
  type PracticeIndexShard,
  type PracticeLexeme,
  type PracticeLexemeShard,
  type PracticeModeFilter,
  type PracticeRating,
  type PracticeSelection,
  type SelectionHistoryItem,
} from '../lib/lexicon/srs';

interface LexiconPracticeProps {
  deckLevel?: string;
  shardBaseUrl?: string;
  initialDeck?: PracticeDeckData | PracticeLexeme[];
  initialMode?: PracticeModeFilter;
  autoStart?: boolean;
  advanceDelayMs?: number;
}

interface StreakState {
  version: 1;
  current: number;
  lastPracticeDate: string | null;
}

interface ChoiceOption {
  label: string;
  correct: boolean;
}

interface ClozeFeedback {
  kind: 'correct' | 'case-miss' | 'wrong-word';
  text: string;
}

const STREAK_KEY = 'lu-lexicon-practice-streak';
const MASTERED_THRESHOLD = 21;

const RATING_LABELS: Record<PracticeRating, string> = {
  again: 'Again',
  hard: 'Hard',
  good: 'Good',
  easy: 'Easy',
};

const MODE_LABELS: Record<PracticeModeFilter, string> = {
  mixed: 'Mixed',
  flashcards: 'Flashcards',
  matching: 'Matching',
  choice: 'Choice',
  cloze: 'Cloze',
};

const HERITAGE_COLORS: Record<string, string> = {
  native: '#0f766e',
  inherited: '#0f766e',
  borrowed: '#7c3aed',
  loanword: '#7c3aed',
  calque: '#b45309',
  avoid: '#b91c1c',
};

function todayKey(date = new Date()): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function previousDayKey(date = new Date()): string {
  const previous = new Date(date);
  previous.setDate(previous.getDate() - 1);
  return todayKey(previous);
}

function readStreak(): StreakState {
  try {
    const raw = window.localStorage.getItem(STREAK_KEY);
    if (!raw) return { version: 1, current: 0, lastPracticeDate: null };
    const parsed = JSON.parse(raw) as Partial<StreakState>;
    if (parsed.version !== 1 || typeof parsed.current !== 'number') {
      return { version: 1, current: 0, lastPracticeDate: null };
    }
    return {
      version: 1,
      current: parsed.current,
      lastPracticeDate: parsed.lastPracticeDate ?? null,
    };
  } catch {
    return { version: 1, current: 0, lastPracticeDate: null };
  }
}

function writeStreak(streak: StreakState): void {
  try {
    window.localStorage.setItem(STREAK_KEY, JSON.stringify(streak));
  } catch {
    // SRS storage warning is handled by the caller.
  }
}

function recordStreak(date = new Date()): StreakState {
  const current = readStreak();
  const today = todayKey(date);
  if (current.lastPracticeDate === today) return current;
  const nextCount = current.lastPracticeDate === previousDayKey(date) ? current.current + 1 : 1;
  const next = { version: 1 as const, current: nextCount, lastPracticeDate: today };
  writeStreak(next);
  return next;
}

function heritageTagColor(heritage: string | null): string | undefined {
  if (!heritage) return undefined;
  return HERITAGE_COLORS[heritage.toLowerCase()] ?? '#334155';
}

function cardData(entry: PracticeLexeme) {
  return {
    front: entry.lemma,
    back: entry.gloss,
    subtitle: entry.ipa ?? entry.pos ?? undefined,
    tag: entry.cefr ?? undefined,
    tagColor: heritageTagColor(entry.heritage),
  };
}

function normalizeInitialDeck(initialDeck?: PracticeDeckData | PracticeLexeme[]): PracticeDeckData | null {
  if (!initialDeck) return null;
  if (!Array.isArray(initialDeck)) return initialDeck;
  const lexemes = initialDeck.map((entry) => {
    const legacy = entry as PracticeLexeme & { slug?: string; example?: string | null };
    const lemmaId = legacy.lemmaId ?? legacy.slug ?? legacy.lemma;
    return {
      ...entry,
      lemmaId,
      lemmaPlain: legacy.lemmaPlain ?? czNorm(legacy.lemma),
      severity: legacy.severity ?? null,
      paradigm: legacy.paradigm ?? { cases: {} },
    };
  });
  return {
    deckVersion: 'test-fixture',
    level: lexemes[0]?.cefr ?? 'A1',
    index: lexemes.map((entry, index) => ({
      lemmaId: entry.lemmaId,
      lemma: entry.lemma,
      cefr: entry.cefr ?? 'A1',
      modes: ['flashcards', 'matching', 'choice'],
      hasCloze: false,
      clozeIds: [],
      newOrder: index,
    })),
    lexemes,
    cloze: [],
  };
}

function historyFromSelection(selection: PracticeSelection): SelectionHistoryItem {
  return {
    itemId: selection.itemId,
    lemmaId: selection.lemma.lemmaId,
    mode: selection.mode,
    clozeId: selection.cloze?.clozeId,
    sentenceFrameId: selection.cloze?.sentenceFrameId,
    blankCase: selection.cloze?.blankCase,
    recallDirection: selection.recallDirection,
    choicePolarity: selection.choicePolarity,
    lapsed: selection.lapsed,
  };
}

function orderedChoiceOptions(
  selection: PracticeSelection,
  deck: PracticeDeckData,
  polarity: ChoicePolarity,
): ChoiceOption[] {
  const sameBand = deck.lexemes.filter(
    (candidate) =>
      candidate.lemmaId !== selection.lemma.lemmaId &&
      candidate.cefr === selection.lemma.cefr &&
      candidate.gloss !== selection.lemma.gloss,
  );
  const distractors = sameBand
    .sort((left, right) => left.lemmaId.localeCompare(right.lemmaId))
    .slice(0, 3);
  if (distractors.length < 3) return [];
  const answer = polarity === 'word-to-meaning' ? selection.lemma.gloss : selection.lemma.lemma;
  const options = [
    { label: answer, correct: true },
    ...distractors.map((entry) => ({
      label: polarity === 'word-to-meaning' ? entry.gloss : entry.lemma,
      correct: false,
    })),
  ];
  const answerIndex = selection.itemId.length % options.length;
  const [first] = options.splice(0, 1);
  options.splice(answerIndex, 0, first);
  return options;
}

function choicePrompt(selection: PracticeSelection): string {
  if (selection.choicePolarity === 'word-to-meaning') {
    return `What does ${selection.lemma.lemma} mean?`;
  }
  return `Which word means ${selection.lemma.gloss}?`;
}

function clozeParts(item: PracticeClozeItem): [string, string] {
  const [before, ...after] = item.sentence.split('___');
  return [before, after.join('___')];
}

function shouldLoadCloze(mode: PracticeModeFilter): boolean {
  return mode === 'mixed' || mode === 'cloze';
}

export default function LexiconPractice({
  deckLevel = 'A1',
  shardBaseUrl = '/lexicon',
  initialDeck,
  initialMode = 'mixed',
  autoStart = false,
  advanceDelayMs = 650,
}: LexiconPracticeProps) {
  const [deck, setDeck] = useState<PracticeDeckData | null>(() => normalizeInitialDeck(initialDeck));
  const [clozeLoaded, setClozeLoaded] = useState(() => {
    const normalized = normalizeInitialDeck(initialDeck);
    return Boolean(normalized && normalized.cloze.length > 0);
  });
  const [started, setStarted] = useState(autoStart);
  const [mode, setMode] = useState<PracticeModeFilter>(initialMode);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState('');
  const [revision, setRevision] = useState(0);
  const [history, setHistory] = useState<SelectionHistoryItem[]>([]);
  const [answerLocked, setAnswerLocked] = useState(false);
  const [streak, setStreak] = useState<StreakState>({
    version: 1,
    current: 0,
    lastPracticeDate: null,
  });
  const [mastered, setMastered] = useState(0);
  const [correctToday, setCorrectToday] = useState(0);
  const [storageWarning, setStorageWarning] = useState<string | null>(null);
  const [clozeInput, setClozeInput] = useState('');
  const [clozeFeedback, setClozeFeedback] = useState<ClozeFeedback | null>(null);
  const [clozeAttemptRecorded, setClozeAttemptRecorded] = useState(false);
  const stageRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const state = loadState();
    setStreak(readStreak());
    setMastered(masteredCount(MASTERED_THRESHOLD));
    if (state.flags.corrupt || state.flags.migrationFailed) {
      setStorageWarning('Progress is paused until browser storage is readable.');
    } else if (state.flags.clockJump) {
      setStorageWarning('Review timing may be off because device clock changed.');
    }
  }, []);

  const selection = useMemo(() => {
    if (!deck) return null;
    return selectNextPracticeItem(deck, {
      history,
      modeFilter: mode,
      now: new Date(),
    });
  }, [deck, history, mode, revision]);

  useEffect(() => {
    setAnswerLocked(false);
    setClozeInput('');
    setClozeFeedback(null);
    setClozeAttemptRecorded(false);
    if (selection) {
      window.setTimeout(() => stageRef.current?.focus(), 0);
    }
  }, [selection?.itemId]);

  useEffect(() => {
    if (!started) return;
    document.title = `${MODE_LABELS[mode]} Practice - Word Atlas`;
  }, [mode, started]);

  async function ensureDeck(includeCloze = shouldLoadCloze(mode)): Promise<PracticeDeckData | null> {
    if (deck && (!includeCloze || clozeLoaded)) return deck;
    setLoading(true);
    setError(null);
    try {
      let nextDeck = deck;
      if (!nextDeck) {
        const [indexResponse, lexemeResponse] = await Promise.all([
          fetch(`${shardBaseUrl}/practice-index.${deckLevel}.json`),
          fetch(`${shardBaseUrl}/practice-lexemes.${deckLevel}.json`),
        ]);
        if (!indexResponse.ok || !lexemeResponse.ok) {
          throw new Error('Practice shard request failed');
        }
        const indexShard = (await indexResponse.json()) as PracticeIndexShard;
        const lexemeShard = (await lexemeResponse.json()) as PracticeLexemeShard;
        nextDeck = combinePracticeShards(indexShard, lexemeShard);
      }
      if (includeCloze && !clozeLoaded) {
        const clozeResponse = await fetch(`${shardBaseUrl}/practice-cloze.${deckLevel}.json`);
        if (clozeResponse.ok) {
          const clozeShard = (await clozeResponse.json()) as { cloze: PracticeClozeItem[] };
          nextDeck = { ...nextDeck, cloze: clozeShard.cloze };
          setClozeLoaded(true);
        }
      }
      setDeck(nextDeck);
      return nextDeck;
    } catch {
      setError('Practice deck could not be loaded.');
      return null;
    } finally {
      setLoading(false);
    }
  }

  async function start(nextMode: PracticeModeFilter = mode) {
    setMode(nextMode);
    setStarted(true);
    await ensureDeck(shouldLoadCloze(nextMode));
  }

  function refreshProgress() {
    const state = loadState();
    setMastered(masteredCount(MASTERED_THRESHOLD));
    if (state.flags.corrupt || state.flags.migrationFailed) {
      setStorageWarning('Progress is paused until browser storage is readable.');
    }
    setRevision((value) => value + 1);
  }

  function completeSelection(current: PracticeSelection) {
    setHistory((items) => [...items.slice(-49), historyFromSelection(current)]);
    refreshProgress();
  }

  function recordReview(current: PracticeSelection, rating: PracticeRating) {
    try {
      rateCard(current.lemma.lemmaId, current.mode, rating, new Date());
      setStreak(recordStreak());
      if (rating === 'good' || rating === 'easy') {
        setCorrectToday((value) => value + 1);
      }
      setFeedback(`${current.lemma.lemma}: ${RATING_LABELS[rating]}`);
    } catch {
      setStorageWarning('Progress is paused until browser storage is readable.');
    }
  }

  function rateAndComplete(current: PracticeSelection, rating: PracticeRating) {
    recordReview(current, rating);
    completeSelection(current);
  }

  useEffect(() => {
    if (!started || !selection || selection.mode !== 'flashcards') return undefined;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.altKey || event.ctrlKey || event.metaKey) return;
      const key = event.key.toLowerCase();
      const rating =
        key === 'a' || key === '1'
          ? 'again'
          : key === 'h' || key === '2'
            ? 'hard'
            : key === 'g' || key === '3'
              ? 'good'
              : key === 'e' || key === '4'
                ? 'easy'
                : null;
      if (!rating) return;
      event.preventDefault();
      rateAndComplete(selection, rating);
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [started, selection]);

  function handleChoice(option: ChoiceOption) {
    if (!selection || answerLocked) return;
    const rating = option.correct ? 'good' : 'again';
    recordReview(selection, rating);
    setAnswerLocked(true);
    setFeedback(option.correct ? `${selection.lemma.lemma}: Correct` : `${selection.lemma.lemma}: Again`);
    window.setTimeout(() => {
      setAnswerLocked(false);
      completeSelection(selection);
    }, advanceDelayMs);
  }

  function submitCloze(value: string, source: 'typed' | 'chip') {
    if (!selection?.cloze || answerLocked) return;
    const answer = value.trim();
    if (!answer) return;
    const cloze = selection.cloze;
    const correct = czNorm(answer) === czNorm(cloze.form);
    const caseMiss = isWrongCaseAnswer(answer, selection.lemma, cloze);

    if (correct) {
      if (!clozeAttemptRecorded) {
        recordReview(selection, 'good');
      }
      setClozeFeedback({
        kind: 'correct',
        text: `✓ ${cloze.form} (${cloze.caseRule.caseLabel})`,
      });
      setAnswerLocked(true);
      window.setTimeout(() => {
        setAnswerLocked(false);
        completeSelection(selection);
      }, advanceDelayMs);
      return;
    }

    if (caseMiss) {
      if (!clozeAttemptRecorded) {
        recordReview(selection, 'hard');
        setClozeAttemptRecorded(true);
      }
      setClozeInput('');
      setClozeFeedback({
        kind: 'case-miss',
        text: `✓ Правильне слово! Тепер постав його у ${cloze.caseRule.caseLabel}: ${cloze.caseRule.feedback}`,
      });
      return;
    }

    if (!clozeAttemptRecorded) {
      recordReview(selection, 'again');
      setClozeAttemptRecorded(true);
    }
    setClozeFeedback({ kind: 'wrong-word', text: '✗ Не те слово' });
    if (source === 'chip') {
      setAnswerLocked(true);
      window.setTimeout(() => {
        setAnswerLocked(false);
        completeSelection(selection);
      }, advanceDelayMs);
    }
  }

  const dueCount = deck ? deck.index.length : 0;
  const correctLabel = `${correctToday} ${uaPlural(correctToday)}`;

  return (
    <section className="lexicon-practice" aria-labelledby="lexicon-practice-title">
      <div className="lexicon-practice-toolbar">
        <div>
          <h2 id="lexicon-practice-title">Practice Hub</h2>
          <p className="lexicon-practice-status" aria-live="polite">
            {feedback || (started ? 'Ready' : 'Not started')}
          </p>
        </div>
        <div className="lexicon-practice-modes" role="group" aria-label="Practice mode">
          {(['mixed', 'flashcards', 'matching', 'choice', 'cloze'] as PracticeModeFilter[]).map(
            (practiceMode) => (
              <button
                type="button"
                key={practiceMode}
                className={mode === practiceMode ? 'active' : ''}
                onClick={() => void start(practiceMode)}
              >
                {MODE_LABELS[practiceMode]}
              </button>
            ),
          )}
        </div>
      </div>

      <div className="lexicon-practice-progress">
        <div aria-label={`${dueCount} practice words loaded`}>
          <span>{deck ? dueCount : '—'}</span>
          <strong>Words</strong>
        </div>
        <div aria-label={`${streak.current} day streak`}>
          <span>{streak.current}</span>
          <strong>Day streak</strong>
        </div>
        <div aria-label={correctLabel}>
          <span>{correctToday}</span>
          <strong>{uaPlural(correctToday)}</strong>
        </div>
        <div aria-label={`${mastered} mastered flashcards`}>
          <span>{mastered}</span>
          <strong>Mastered</strong>
        </div>
      </div>

      {storageWarning && <p className="lexicon-practice-warning">{storageWarning}</p>}

      {!started && (
        <div className="lexicon-practice-start">
          <button type="button" onClick={() => void start(mode)}>
            Start Practice
          </button>
        </div>
      )}

      {loading && <p className="lexicon-practice-muted">Loading…</p>}
      {error && <p className="lexicon-practice-warning">{error}</p>}
      {started && deck && deck.index.length === 0 && (
        <p className="lexicon-practice-muted">No practice cards yet.</p>
      )}

      {started && deck && deck.index.length > 0 && (
        <div className="lexicon-practice-stage" ref={stageRef} tabIndex={-1}>
          {selection ? (
            <PracticeItem
              selection={selection}
              deck={deck}
              answerLocked={answerLocked}
              clozeInput={clozeInput}
              clozeFeedback={clozeFeedback}
              onClozeInput={setClozeInput}
              onFlashcardRating={(rating) => rateAndComplete(selection, rating)}
              onChoice={handleChoice}
              onClozeSubmit={submitCloze}
            />
          ) : (
            <p className="lexicon-practice-muted">All due cards are done for now.</p>
          )}
        </div>
      )}
    </section>
  );
}

function PracticeItem({
  selection,
  deck,
  answerLocked,
  clozeInput,
  clozeFeedback,
  onClozeInput,
  onFlashcardRating,
  onChoice,
  onClozeSubmit,
}: {
  selection: PracticeSelection;
  deck: PracticeDeckData;
  answerLocked: boolean;
  clozeInput: string;
  clozeFeedback: ClozeFeedback | null;
  onClozeInput(value: string): void;
  onFlashcardRating(rating: PracticeRating): void;
  onChoice(option: ChoiceOption): void;
  onClozeSubmit(value: string, source: 'typed' | 'chip'): void;
}) {
  if (selection.mode === 'flashcards') {
    return (
      <>
        <FlashcardDeck key={selection.itemId} cards={[cardData(selection.lemma)]} />
        <div className="lexicon-rating-bar" role="group" aria-label="Rate this card">
          {(['again', 'hard', 'good', 'easy'] as const).map((rating) => (
            <button type="button" key={rating} onClick={() => onFlashcardRating(rating)}>
              {RATING_LABELS[rating]}
            </button>
          ))}
        </div>
      </>
    );
  }

  if (selection.mode === 'cloze' && selection.cloze) {
    return (
      <PracticeCloze
        selection={selection}
        input={clozeInput}
        feedback={clozeFeedback}
        answerLocked={answerLocked}
        onInput={onClozeInput}
        onSubmit={onClozeSubmit}
      />
    );
  }

  const options = orderedChoiceOptions(selection, deck, selection.choicePolarity);
  if (!options.length) {
    return <p className="lexicon-practice-muted">No option-ready cards are due right now.</p>;
  }
  const prompt =
    selection.mode === 'matching'
      ? selection.recallDirection === 'uk-to-meaning'
        ? `Match ${selection.lemma.lemma}`
        : `Match ${selection.lemma.gloss}`
      : choicePrompt(selection);
  return (
    <div className="lexicon-choice" data-testid={`practice-${selection.mode}`}>
      <p className="lexicon-choice-prompt">{prompt}</p>
      <ul className="lexicon-option-list">
        {options.map((option) => (
          <li key={option.label}>
            <button type="button" disabled={answerLocked} onClick={() => onChoice(option)}>
              {option.label}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

function PracticeCloze({
  selection,
  input,
  feedback,
  answerLocked,
  onInput,
  onSubmit,
}: {
  selection: PracticeSelection;
  input: string;
  feedback: ClozeFeedback | null;
  answerLocked: boolean;
  onInput(value: string): void;
  onSubmit(value: string, source: 'typed' | 'chip'): void;
}) {
  const cloze = selection.cloze;
  if (!cloze) return null;
  const [before, after] = clozeParts(cloze);
  const optionErrors = validateClozeOptions(cloze);
  return (
    <div className="lexicon-cloze" data-testid="practice-cloze">
      <p className="lexicon-cloze-translation">{cloze.clozeEn}</p>
      <form
        className="lexicon-cloze-row"
        onSubmit={(event) => {
          event.preventDefault();
          onSubmit(input, 'typed');
        }}
      >
        <span>{before}</span>
        <input
          value={input}
          disabled={answerLocked}
          aria-label={`Answer in ${cloze.caseRule.caseLabel}`}
          onChange={(event) => onInput(event.currentTarget.value)}
        />
        <span>{after}</span>
        <button type="submit" disabled={answerLocked}>
          Check
        </button>
      </form>
      {optionErrors.length > 0 ? (
        <p className="lexicon-practice-warning">Cloze options failed validation.</p>
      ) : (
        <ul className="lexicon-option-list lexicon-cloze-options">
          {cloze.options.map((option) => (
            <li key={option.optionId}>
              <button
                type="button"
                disabled={answerLocked}
                onClick={() => onSubmit(option.label, 'chip')}
              >
                {option.label}
              </button>
            </li>
          ))}
        </ul>
      )}
      {feedback && (
        <p
          className={`lexicon-cloze-feedback ${feedback.kind}`}
          role={feedback.kind === 'wrong-word' ? 'alert' : 'status'}
          aria-live="polite"
        >
          {feedback.text}
        </p>
      )}
    </div>
  );
}
