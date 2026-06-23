import React, { useEffect, useMemo, useState } from 'react';
import FlashcardDeck from './FlashcardDeck';
import Quiz from './Quiz';
import { shuffleNotCorrect } from './utils';
import {
  getDueQueue,
  loadState,
  masteredCount,
  rateCard,
  type PracticeDeckEntry,
  type PracticeRating,
} from '../lib/lexicon/srs';

type PracticeMode = 'flashcards' | 'quiz';

interface LexiconPracticeProps {
  deckUrl?: string;
  initialDeck?: PracticeDeckEntry[];
  initialMode?: PracticeMode;
  autoStart?: boolean;
  advanceDelayMs?: number;
}

interface QuizQuestionModel {
  entry: PracticeDeckEntry;
  options: string[];
}

interface StreakState {
  version: 1;
  current: number;
  lastPracticeDate: string | null;
}

const STREAK_KEY = 'lu-lexicon-practice-streak';
const MASTERED_THRESHOLD = 21;

const RATING_LABELS: Record<PracticeRating, string> = {
  again: 'Again',
  hard: 'Hard',
  good: 'Good',
  easy: 'Easy',
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
    return {
      version: 1,
      current: typeof parsed.current === 'number' ? parsed.current : 0,
      lastPracticeDate: typeof parsed.lastPracticeDate === 'string' ? parsed.lastPracticeDate : null,
    };
  } catch {
    return { version: 1, current: 0, lastPracticeDate: null };
  }
}

function writeStreak(next: StreakState): void {
  try {
    window.localStorage.setItem(STREAK_KEY, JSON.stringify(next));
  } catch {
    // Storage can be unavailable in hardened browser contexts.
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

function cardData(entry: PracticeDeckEntry) {
  return {
    front: entry.lemma,
    back: entry.gloss,
    subtitle: entry.ipa ?? entry.pos ?? undefined,
    tag: entry.cefr ?? undefined,
    tagColor: heritageTagColor(entry.heritage),
  };
}

function uniqueGlosses(entries: PracticeDeckEntry[]): string[] {
  const seen = new Set<string>();
  const glosses: string[] = [];
  for (const entry of entries) {
    if (seen.has(entry.gloss)) continue;
    seen.add(entry.gloss);
    glosses.push(entry.gloss);
  }
  return glosses;
}

function quizFor(entry: PracticeDeckEntry, deck: PracticeDeckEntry[]): QuizQuestionModel | null {
  const sameBand = deck.filter(
    (candidate) =>
      candidate.slug !== entry.slug &&
      candidate.cefr === entry.cefr &&
      candidate.gloss !== entry.gloss,
  );
  const distractors = shuffleNotCorrect(uniqueGlosses(sameBand), uniqueGlosses(sameBand)).slice(0, 3);
  if (distractors.length < 3) return null;
  const ordered = [entry.gloss, ...distractors];
  return {
    entry,
    options: shuffleNotCorrect(ordered, ordered),
  };
}

export default function LexiconPractice({
  deckUrl = '/lexicon/practice-deck.json',
  initialDeck,
  initialMode = 'flashcards',
  autoStart = false,
  advanceDelayMs = 650,
}: LexiconPracticeProps) {
  const [deck, setDeck] = useState<PracticeDeckEntry[] | null>(initialDeck ?? null);
  const [started, setStarted] = useState(autoStart);
  const [mode, setMode] = useState<PracticeMode>(initialMode);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState('');
  const [revision, setRevision] = useState(0);
  const [answerLocked, setAnswerLocked] = useState(false);
  const [streak, setStreak] = useState<StreakState>({
    version: 1,
    current: 0,
    lastPracticeDate: null,
  });
  const [mastered, setMastered] = useState(0);
  const [storageWarning, setStorageWarning] = useState<string | null>(null);

  useEffect(() => {
    const state = loadState();
    setStreak(readStreak());
    setMastered(masteredCount(MASTERED_THRESHOLD));
    if (state.flags.corrupt || state.flags.migrationFailed) {
      setStorageWarning('Progress is paused until browser storage is readable.');
    } else if (state.flags.clockJump) {
      setStorageWarning('Review timing may be off because the device clock changed.');
    }
  }, []);

  const dueQueue = useMemo(() => {
    if (!deck) return [];
    return getDueQueue(deck, new Date());
  }, [deck, revision]);

  const quizQuestion = useMemo(() => {
    if (!deck) return null;
    for (const entry of dueQueue) {
      const question = quizFor(entry, deck);
      if (question) return question;
    }
    return null;
  }, [deck, dueQueue]);

  async function ensureDeck(): Promise<PracticeDeckEntry[] | null> {
    if (deck) return deck;
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(deckUrl);
      if (!response.ok) throw new Error(`Deck request failed: ${response.status}`);
      const loaded = (await response.json()) as PracticeDeckEntry[];
      setDeck(loaded);
      return loaded;
    } catch {
      setError('Practice deck could not be loaded.');
      return null;
    } finally {
      setLoading(false);
    }
  }

  async function start(nextMode: PracticeMode = mode) {
    setMode(nextMode);
    setStarted(true);
    await ensureDeck();
  }

  function refreshProgress() {
    const state = loadState();
    setMastered(masteredCount(MASTERED_THRESHOLD));
    if (state.flags.corrupt || state.flags.migrationFailed) {
      setStorageWarning('Progress is paused until browser storage is readable.');
    }
    setRevision((value) => value + 1);
  }

  function recordReview(entry: PracticeDeckEntry, rating: PracticeRating) {
    try {
      rateCard(entry.slug, rating, new Date());
      setStreak(recordStreak());
      setFeedback(`${entry.lemma}: ${RATING_LABELS[rating]}`);
      refreshProgress();
    } catch {
      setStorageWarning('Progress is paused until browser storage is readable.');
    }
  }

  useEffect(() => {
    if (!started || mode !== 'flashcards' || !dueQueue[0]) return undefined;
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
      recordReview(dueQueue[0], rating);
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [started, mode, dueQueue]);

  function handleQuizClick(event: React.MouseEvent<HTMLDivElement>) {
    if (!quizQuestion || answerLocked) return;
    const target = event.target instanceof HTMLElement ? event.target.closest('button') : null;
    if (!target || !target.closest('[data-activity="quiz-options"]')) return;
    const selected = target.textContent?.trim();
    if (!selected) return;
    const correct = selected === quizQuestion.entry.gloss;
    try {
      rateCard(quizQuestion.entry.slug, correct ? 'good' : 'again', new Date());
      setStreak(recordStreak());
      setFeedback(correct ? `${quizQuestion.entry.lemma}: Correct` : `${quizQuestion.entry.lemma}: Again`);
      setAnswerLocked(true);
      window.setTimeout(() => {
        setAnswerLocked(false);
        refreshProgress();
      }, advanceDelayMs);
    } catch {
      setStorageWarning('Progress is paused until browser storage is readable.');
    }
  }

  const currentFlashcard = dueQueue[0] ?? null;
  const dueCountLabel = deck ? String(dueQueue.length) : '—';

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
          <button
            type="button"
            className={mode === 'flashcards' ? 'active' : ''}
            onClick={() => void start('flashcards')}
          >
            Flashcards
          </button>
          <button type="button" className={mode === 'quiz' ? 'active' : ''} onClick={() => void start('quiz')}>
            Quiz
          </button>
        </div>
      </div>

      <div className="lexicon-practice-progress" aria-label="Practice progress">
        <div>
          <span>{dueCountLabel}</span>
          <strong>Due today</strong>
        </div>
        <div>
          <span>{streak.current}</span>
          <strong>Day streak</strong>
        </div>
        <div>
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

      {started && deck && deck.length === 0 && <p className="lexicon-practice-muted">No practice cards yet.</p>}

      {started && deck && deck.length > 0 && mode === 'flashcards' && (
        <div className="lexicon-practice-stage">
          {currentFlashcard ? (
            <>
              <PracticeFlashcard entry={currentFlashcard} />
              <div className="lexicon-rating-bar" role="group" aria-label="Rate this card">
                {(['again', 'hard', 'good', 'easy'] as const).map((rating) => (
                  <button type="button" key={rating} onClick={() => recordReview(currentFlashcard, rating)}>
                    {RATING_LABELS[rating]}
                  </button>
                ))}
              </div>
            </>
          ) : (
            <p className="lexicon-practice-muted">All due cards are done for now.</p>
          )}
        </div>
      )}

      {started && deck && deck.length > 0 && mode === 'quiz' && (
        <div className="lexicon-practice-stage" data-testid="practice-quiz" onClickCapture={handleQuizClick}>
          {quizQuestion ? (
            <PracticeQuiz model={quizQuestion} />
          ) : (
            <p className="lexicon-practice-muted">No quiz-ready cards are due right now.</p>
          )}
        </div>
      )}
    </section>
  );
}

function PracticeFlashcard({ entry }: { entry: PracticeDeckEntry }) {
  return <FlashcardDeck key={entry.slug} cards={[cardData(entry)]} />;
}

function PracticeQuiz({ model }: { model: QuizQuestionModel }) {
  return (
    <Quiz
      key={model.entry.slug}
      instruction="Choose the meaning"
      questions={[
        {
          question: `What does ${model.entry.lemma} mean?`,
          options: model.options.map((text) => ({
            text,
            correct: text === model.entry.gloss,
          })),
          explanation: model.entry.example ?? undefined,
        },
      ]}
    />
  );
}
