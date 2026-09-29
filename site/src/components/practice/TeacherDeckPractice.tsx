/**
 * Practice panel for a deck that practises from served artifacts — the teacher
 * vocabulary deck ("Dev's example deck", #8843 scope 4).
 *
 * The deck files are fetched only when this panel mounts (the deck is selected).
 * Meanings are always the teacher's English (`en` = `teacherEn` with the source
 * aspect label); there is no fallback to CEFR shards. Scheduling, the daily queue,
 * continuity and migration live in `lib/lexicon/teacher-deck-srs.ts`.
 */
import { type ReactNode, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import MatchUp from '../MatchUp';
import PracticeFlashcard from '../PracticeFlashcard';
import PracticeStress from '../PracticeStress';
import ChromeText, { ChromeDual } from '../../lib/i18n/ChromeText';
import type { ChromeLocale } from '../../lib/i18n/chrome';
import {
  isPracticeStorageEphemeral,
  practiceStorage,
  type PracticeRating,
  type StorageLike,
} from '../../lib/lexicon/srs';
import {
  entryClozeItems,
  entryGrammarItems,
  type ArtifactDeckPracticeConfig,
  type TeacherCardKind,
  type TeacherDeck,
  type TeacherDeckEntry,
} from '../../lib/lexicon/teacher-deck';
import {
  applyDeckReview,
  migrateLegacyPracticeState,
  pickMatchingRound,
  planDeckDay,
  previewDeckIntervals,
  readDeckProgress,
  readLegacyPracticeCards,
  recordDeckReview,
  schedulableKinds,
  writeDeckProgress,
  type DeckPlan,
  type DeckProgress,
  type DeckQueueSlot,
  type DeckSettings,
} from '../../lib/lexicon/teacher-deck-srs';

const RATING_LABELS: Record<PracticeRating, { uk: string; en: string }> = {
  again: { uk: 'Ще раз', en: 'Again' },
  hard: { uk: 'Важко', en: 'Hard' },
  good: { uk: 'Добре', en: 'Good' },
  easy: { uk: 'Легко', en: 'Easy' },
};
const RATING_ORDER: PracticeRating[] = ['again', 'hard', 'good', 'easy'];
const SECONDS_PER_ITEM = 20;
const STORAGE_WARNING = {
  uk: 'Прогрес не зберігається — сховище браузера недоступне або переповнене.',
  en: 'Progress is not being saved — browser storage is unavailable or full.',
};

const KIND_LABELS: Record<TeacherCardKind, { uk: string; en: string }> = {
  recognition: { uk: 'Упізнавання (укр → англ)', en: 'Recognition (UK → EN)' },
  production: { uk: 'Відтворення (англ → укр)', en: 'Recall (EN → UK)' },
  cloze: { uk: 'Речення з пропуском', en: 'Cloze sentences' },
  grammar: { uk: 'Граматика', en: 'Grammar' },
};

export interface TeacherDeckPracticeProps {
  deckId: string;
  titleUk: string;
  titleEn: string;
  config: ArtifactDeckPracticeConfig;
  chromeLocale: ChromeLocale;
  /** Loads and validates the deck (fetched lazily, once per mount). */
  loadDeck: () => Promise<TeacherDeck>;
  /** The host's deck switcher, shown on the deck overview. */
  deckSwitcher?: ReactNode;
  onSessionActiveChange?: (active: boolean) => void;
  storage?: StorageLike;
  now?: () => number;
}

type Phase = 'overview' | 'session' | 'matching';

interface ObjectiveAnswer {
  slot: DeckQueueSlot;
  chosen: string;
  correct: boolean;
}

function normalizeAttempt(value: string): string {
  return value
    .normalize('NFC')
    .replace(/́/g, '')
    .replace(/[’ʼ`‘]/g, "'")
    .replace(/\s+/g, ' ')
    .trim()
    .toLocaleLowerCase('uk');
}

export default function TeacherDeckPractice({
  deckId,
  titleUk,
  titleEn,
  config,
  chromeLocale,
  loadDeck,
  deckSwitcher,
  onSessionActiveChange,
  storage: storageProp,
  now: nowProp,
}: TeacherDeckPracticeProps) {
  const now = useCallback(() => (nowProp ? nowProp() : Date.now()), [nowProp]);
  const storage = useMemo(() => storageProp ?? practiceStorage(), [storageProp]);
  const defaults = useMemo<DeckSettings>(
    () => ({ newPerDay: config.newPerDay, reviewCap: config.reviewCap }),
    [config.newPerDay, config.reviewCap],
  );
  const [deck, setDeck] = useState<TeacherDeck | null>(null);
  const [loadError, setLoadError] = useState(false);
  const [reloadToken, setReloadToken] = useState(0);
  const [progress, setProgress] = useState<DeckProgress | null>(null);
  const [plan, setPlan] = useState<DeckPlan | null>(null);
  const [phase, setPhase] = useState<Phase>('overview');
  const [answer, setAnswer] = useState<ObjectiveAnswer | null>(null);
  // Blocked localStorage falls back to session-only memory: warn like CEFR practice does.
  const [storageFailed, setStorageFailedState] = useState(() => !storageProp && isPracticeStorageEphemeral());
  // Once a write fails, storage holds stale progress: keep working from memory.
  const storageFailedRef = useRef(storageFailed);
  const setStorageFailed = useCallback((failed: boolean) => {
    storageFailedRef.current = failed;
    setStorageFailedState(failed);
  }, []);
  const [matchingSeed, setMatchingSeed] = useState(0);
  const [matchingComplete, setMatchingComplete] = useState(false);
  const headingRef = useRef<HTMLHeadingElement>(null);
  const nextRef = useRef<HTMLButtonElement>(null);
  const matchingAgainRef = useRef<HTMLButtonElement>(null);
  const previousPhaseRef = useRef<Phase>('overview');

  useEffect(() => {
    let cancelled = false;
    setLoadError(false);
    loadDeck()
      .then((loaded) => {
        if (cancelled) return;
        let stored = readDeckProgress(storage, deckId, defaults);
        if (!stored.migration) {
          stored = migrateLegacyPracticeState(loaded, stored, readLegacyPracticeCards(storage), now());
          if (!writeDeckProgress(storage, stored)) setStorageFailed(true);
        }
        setDeck(loaded);
        setProgress(stored);
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        console.error('Teacher deck failed to load', error);
        setLoadError(true);
      });
    return () => {
      cancelled = true;
    };
    // Load once per selection (and on retry); clock/storage identity changes do not refetch.
  }, [loadDeck, deckId, reloadToken]);

  useEffect(() => {
    onSessionActiveChange?.(phase !== 'overview');
  }, [onSessionActiveChange, phase]);
  useEffect(() => () => onSessionActiveChange?.(false), [onSessionActiveChange]);

  /** Plan today against `next`, persist the queue, and make it current. */
  const commit = useCallback(
    (next: DeckProgress) => {
      if (!deck) return null;
      const planned = planDeckDay(deck, next, now());
      const saved = { ...next, queue: planned.queue };
      if (!writeDeckProgress(storage, saved)) setStorageFailed(true);
      setProgress(saved);
      setPlan(planned);
      return planned;
    },
    [deck, now, setStorageFailed, storage],
  );

  const preview = useMemo(
    () => (deck && progress && phase === 'overview' ? planDeckDay(deck, progress, now()) : null),
    [deck, now, phase, progress],
  );

  const kindCounts = useMemo(() => {
    const counts: Record<TeacherCardKind, number> = { recognition: 0, production: 0, cloze: 0, grammar: 0 };
    if (deck) for (const entry of deck.entries) for (const kind of schedulableKinds(deck, entry)) counts[kind] += 1;
    return counts;
  }, [deck]);

  const matchingPairs = useMemo(
    () => (deck && progress ? pickMatchingRound(deck, progress, matchingSeed) : []),
    [deck, matchingSeed, progress],
  );
  const matchingTiles = useMemo(
    () => matchingPairs.map((entry) => ({ left: entry.uk, right: entry.en })),
    [matchingPairs],
  );

  const updateSettings = (patch: Partial<DeckSettings>) => {
    if (!progress) return;
    const latest = storageFailedRef.current ? progress : readDeckProgress(storage, deckId, defaults);
    const next = { ...latest, settings: { ...latest.settings, ...patch } };
    const normalized = readSettingsInput(next.settings, defaults);
    const saved = { ...next, settings: normalized };
    if (!writeDeckProgress(storage, saved)) setStorageFailed(true);
    setProgress(saved);
  };

  const startSession = () => {
    if (!progress) return;
    // Re-read so a second tab's reviews are included before planning.
    const planned = commit(storageFailedRef.current ? progress : readDeckProgress(storage, deckId, defaults));
    if (!planned) return;
    setAnswer(null);
    setPhase('session');
  };

  const rate = (slot: DeckQueueSlot, rating: PracticeRating) => {
    if (!deck || !progress) return null;
    // Read-apply-write so a reload or a second tab never applies a review twice.
    const result = storageFailedRef.current
      ? { ...applyDeckReview(deck, progress, slot, rating, now()), ok: false }
      : recordDeckReview(storage, deck, defaults, slot, rating, now());
    if (!result.ok) setStorageFailed(true);
    return commit(result.progress);
  };

  const answerObjective = (slot: DeckQueueSlot, chosen: string, correct: boolean) => {
    if (answer) return;
    setAnswer({ slot, chosen, correct });
    rate(slot, correct ? 'good' : 'again');
  };

  const current: DeckQueueSlot | null = answer?.slot ?? plan?.pending[0] ?? null;
  const currentEntry = current && deck ? deck.entriesById.get(current.entryId) ?? null : null;

  useEffect(() => {
    if (phase === 'overview') {
      if (previousPhaseRef.current !== 'overview') headingRef.current?.focus();
    } else if (phase === 'matching' && matchingComplete) {
      matchingAgainRef.current?.focus();
    } else if (phase === 'session' && answer) {
      nextRef.current?.focus();
    } else {
      headingRef.current?.focus();
    }
    previousPhaseRef.current = phase;
  }, [phase, current?.slotId, answer, matchingComplete]);

  const title = (
    <h2 ref={headingRef} tabIndex={-1} data-testid="practice-daily-deck-title">
      <ChromeDual uk={`Слова дня — ${titleUk}`} en={`Words of the day — ${titleEn}`} />
    </h2>
  );

  if (loadError) {
    return (
      <div className="teacher-deck" data-testid="teacher-deck-practice">
        {title}
        {deckSwitcher}
        <div className="lexicon-practice-fallback" data-testid="teacher-deck-load-error">
          <p className="lexicon-practice-warning" role="alert">
            <ChromeText k="practice.loadError" />
          </p>
          <button type="button" className="btn btn-accent" onClick={() => setReloadToken((token) => token + 1)}>
            <ChromeText k="practice.retry" />
          </button>
        </div>
      </div>
    );
  }

  if (!deck || !progress) {
    return (
      <div className="teacher-deck" data-testid="teacher-deck-practice">
        {title}
        {deckSwitcher}
        <p className="lexicon-practice-muted" data-testid="teacher-deck-loading">
          <ChromeText k="practice.loading" />
        </p>
      </div>
    );
  }

  const storageNotice = storageFailed ? (
    <p className="lexicon-practice-warning" role="alert" data-testid="teacher-deck-storage-warning">
      <ChromeDual uk={STORAGE_WARNING.uk} en={STORAGE_WARNING.en} />
    </p>
  ) : null;

  if (phase === 'matching') {
    return (
      <div className="teacher-deck lexicon-practice-stage-shell" data-testid="teacher-deck-matching">
        <div className="lexicon-practice-stage-bar">
          <button type="button" className="stage-back" onClick={() => setPhase('overview')}>
            <ChromeText k="practice.home" />
          </button>
          <h2 ref={headingRef} tabIndex={-1}>
            <ChromeDual uk="Пари: слово — значення" en="Matching: word — meaning" />
          </h2>
        </div>
        <p className="lexicon-practice-muted">
          <ChromeDual
            uk="Тренування без оцінювання: розклад повторень не змінюється."
            en="Practice only: this round does not change your review schedule."
          />
        </p>
        <MatchUp
          key={matchingSeed}
          pairs={matchingTiles}
          isUkrainian={chromeLocale === 'uk'}
          onComplete={() => setMatchingComplete(true)}
        />
        {matchingComplete ? (
          <div className="teacher-deck-actions">
            <button
              type="button"
              ref={matchingAgainRef}
              className="btn btn-accent"
              data-testid="teacher-deck-matching-again"
              onClick={() => {
                setMatchingComplete(false);
                setMatchingSeed((seed) => seed + 1);
              }}
            >
              <ChromeDual uk="Ще одна гра" en="Another round" />
            </button>
          </div>
        ) : null}
      </div>
    );
  }

  if (phase === 'session') {
    if (!current || !currentEntry) {
      return (
        <div className="teacher-deck" data-testid="teacher-deck-session-done">
          <h2 ref={headingRef} tabIndex={-1}>
            <ChromeText k="practice.sessionComplete" />
          </h2>
          {storageNotice}
          <p data-testid="teacher-deck-session-summary">
            <ChromeDual
              uk={`Сьогодні: ${plan?.stats.reviewsDoneToday ?? 0} повторень, ${plan?.stats.newDoneToday ?? 0} нових слів.`}
              en={`Today: ${plan?.stats.reviewsDoneToday ?? 0} reviews, ${plan?.stats.newDoneToday ?? 0} new words.`}
            />
          </p>
          {plan && plan.stats.dueBacklog > 0 ? (
            <p className="lexicon-practice-muted" data-testid="teacher-deck-backlog-left">
              <ChromeDual
                uk={`Ще ${plan.stats.dueBacklog} карток чекають на повторення (денний ліміт вичерпано).`}
                en={`${plan.stats.dueBacklog} cards are still due (daily review cap reached).`}
              />
            </p>
          ) : null}
          <div className="teacher-deck-actions">
            {matchingPairs.length > 0 ? (
              <button type="button" className="btn" onClick={() => setPhase('matching')}>
                <ChromeDual uk="Пари: слово — значення" en="Matching round" />
              </button>
            ) : null}
            <button type="button" className="btn btn-accent" onClick={() => setPhase('overview')}>
              <ChromeText k="practice.home" />
            </button>
          </div>
        </div>
      );
    }
    const done = (plan?.stats.completedToday ?? 0) - (answer ? 1 : 0);
    const total = (plan?.stats.completedToday ?? 0) + (plan?.pending.length ?? 0);
    return (
      <div className="teacher-deck lexicon-practice-stage-shell" data-testid="teacher-deck-session">
        <div className="lexicon-practice-stage-bar">
          <button type="button" className="stage-back" onClick={() => setPhase('overview')}>
            <ChromeText k="practice.home" />
          </button>
          <h2 ref={headingRef} tabIndex={-1}>
            <ChromeDual uk={titleUk} en={titleEn} />
          </h2>
          <span className="queue-pill" data-testid="teacher-deck-progress">
            {Math.min(done + 1, total)}/{total}
          </span>
          <button
            type="button"
            ref={nextRef}
            className="btn btn-accent queue-next-btn"
            data-testid={answer ? 'teacher-deck-next' : undefined}
            disabled={!answer}
            style={{ visibility: answer ? 'visible' : 'hidden' }}
            onClick={() => setAnswer(null)}
          >
            <ChromeText k="practice.nextArrow" />
          </button>
        </div>
        {storageNotice}
        <div className="lexicon-practice-stage" data-slot-kind={current.kind} data-origin={current.origin}>
          {current.origin === 'new' ? (
            <p className="teacher-deck-new-tag" data-testid="teacher-deck-new-word">
              <ChromeDual uk="Нове слово" en="New word" />
            </p>
          ) : null}
          <TeacherSlot
            key={current.slotId}
            deck={deck}
            entry={currentEntry}
            slot={current}
            card={progress.cards[current.cardId]}
            now={now}
            answer={answer}
            chromeLocale={chromeLocale}
            onRate={(rating) => rate(current, rating)}
            onObjective={(chosen, correct) => answerObjective(current, chosen, correct)}
          />
        </div>
      </div>
    );
  }

  const stats = preview?.stats;
  const expected = stats ? stats.plannedReviews + stats.plannedNew + stats.plannedRepeats : 0;
  const minutes = Math.max(1, Math.round((expected * SECONDS_PER_ITEM) / 60));
  const resumable = Boolean(stats && stats.completedToday > 0 && expected > 0);
  return (
    <div className="teacher-deck" data-testid="teacher-deck-practice">
      {title}
      {deckSwitcher}
      {storageNotice}
      <div className="k3-stats" data-testid="teacher-deck-stats" role="group">
        <div className="k3-stat">
          <span className="k3-stat-value" data-testid="teacher-deck-due">{stats?.dueBacklog ?? 0}</span>
          <span className="k3-stat-label"><ChromeDual uk="До повторення" en="Due" /></span>
        </div>
        <div className="k3-stat">
          <span className="k3-stat-value" data-testid="teacher-deck-introduced">
            {stats?.introduced ?? 0}/{stats?.total ?? deck.entries.length}
          </span>
          <span className="k3-stat-label"><ChromeDual uk="Слів почато" en="Words started" /></span>
        </div>
        <div className="k3-stat">
          <span className="k3-stat-value">{stats?.newDoneToday ?? 0}/{progress.settings.newPerDay}</span>
          <span className="k3-stat-label"><ChromeDual uk="Нових сьогодні" en="New today" /></span>
        </div>
        <div className="k3-stat">
          <span className="k3-stat-value">{stats?.reviewsDoneToday ?? 0}/{progress.settings.reviewCap}</span>
          <span className="k3-stat-label"><ChromeDual uk="Повторень сьогодні" en="Reviews today" /></span>
        </div>
      </div>

      <fieldset className="teacher-deck-settings" data-testid="teacher-deck-settings">
        <legend><ChromeDual uk="Денний обсяг" en="Daily amount" /></legend>
        <label>
          <ChromeDual uk="Нових слів на день" en="New words per day" />
          <input
            type="number"
            min={0}
            max={500}
            inputMode="numeric"
            data-testid="teacher-deck-new-per-day"
            value={progress.settings.newPerDay}
            onChange={(event) => updateSettings({ newPerDay: Number(event.target.value) })}
          />
        </label>
        <label>
          <ChromeDual uk="Ліміт повторень на день" en="Review cap per day" />
          <input
            type="number"
            min={0}
            max={5000}
            inputMode="numeric"
            data-testid="teacher-deck-review-cap"
            value={progress.settings.reviewCap}
            onChange={(event) => updateSettings({ reviewCap: Number(event.target.value) })}
          />
        </label>
      </fieldset>

      <p className="k3-session-scope" data-testid="teacher-deck-session-size">
        <ChromeDual
          uk={`Сьогодні: ${stats?.plannedReviews ?? 0} до повторення + ${stats?.plannedNew ?? 0} нових${stats?.plannedRepeats ? ` + ${stats.plannedRepeats} ще раз` : ''} ≈ ${minutes} хв`}
          en={`Today: ${stats?.plannedReviews ?? 0} due + ${stats?.plannedNew ?? 0} new${stats?.plannedRepeats ? ` + ${stats.plannedRepeats} again` : ''} ≈ ${minutes} min`}
        />
      </p>
      {expected > 0 ? (
        <button
          type="button"
          className="btn btn-accent k3-session-primary"
          data-testid="teacher-deck-start"
          onClick={startSession}
        >
          {resumable ? (
            <ChromeDual uk="Продовжити сьогоднішню практику" en="Continue today's practice" />
          ) : (
            <ChromeDual uk="Почати практику" en="Start practice" />
          )}
        </button>
      ) : (
        <p className="lexicon-practice-muted" data-testid="teacher-deck-nothing-today">
          {stats && stats.dueBacklog > 0 ? (
            <ChromeDual
              uk={`Денний ліміт повторень вичерпано; ще ${stats.dueBacklog} карток чекають.`}
              en={`Daily review cap reached; ${stats.dueBacklog} cards are still due.`}
            />
          ) : (
            <ChromeDual uk="На сьогодні все." en="All done for today." />
          )}
        </p>
      )}

      <div className="teacher-deck-modes" data-testid="teacher-deck-modes">
        <h3><ChromeDual uk="Що є в цій колоді" en="In this deck" /></h3>
        <ul>
          {(Object.keys(kindCounts) as TeacherCardKind[])
            .filter((kind) => kindCounts[kind] > 0)
            .map((kind) => (
              <li key={kind} data-testid={`teacher-deck-kind-${kind}`}>
                <ChromeDual uk={KIND_LABELS[kind].uk} en={KIND_LABELS[kind].en} />: {kindCounts[kind]}
              </li>
            ))}
        </ul>
        {matchingPairs.length > 0 ? (
          <button
            type="button"
            className="btn"
            data-testid="teacher-deck-matching-start"
            onClick={() => {
              setMatchingComplete(false);
              setPhase('matching');
            }}
          >
            <ChromeDual uk="Пари: слово — значення" en="Matching round" />
          </button>
        ) : null}
      </div>
    </div>
  );
}

function readSettingsInput(settings: DeckSettings, defaults: DeckSettings): DeckSettings {
  const clamp = (value: number, fallback: number, max: number) =>
    Number.isFinite(value) ? Math.min(max, Math.max(0, Math.round(value))) : fallback;
  return {
    newPerDay: clamp(settings.newPerDay, defaults.newPerDay, 500),
    reviewCap: clamp(settings.reviewCap, defaults.reviewCap, 5000),
  };
}

// --------------------------------------------------------------------------- one slot

interface TeacherSlotProps {
  deck: TeacherDeck;
  entry: TeacherDeckEntry;
  slot: DeckQueueSlot;
  card: DeckProgress['cards'][string] | undefined;
  now: () => number;
  answer: ObjectiveAnswer | null;
  chromeLocale: ChromeLocale;
  onRate: (rating: PracticeRating) => void;
  onObjective: (chosen: string, correct: boolean) => void;
}

interface Option {
  label: string;
  correct: boolean;
}

function TeacherSlot({ deck, entry, slot, card, now, answer, chromeLocale, onRate, onObjective }: TeacherSlotProps) {
  const presentation = slot.presentation;
  const locked = answer?.slot.slotId === slot.slotId;
  const intervals = useMemo(() => previewDeckIntervals(card, now()), [card, now]);

  if (presentation.type === 'recognition-flashcard') {
    return (
      <div data-testid="teacher-deck-recognition-flashcard">
        <PracticeFlashcard
          card={{ front: entry.uk, pronunciationLemma: entry.multiword ? undefined : entry.uk, back: entry.en }}
          ratingLabels={RATING_LABELS}
          intervalPreviews={intervals}
          onRate={onRate}
          chromeLocale={chromeLocale}
        />
      </div>
    );
  }

  if (presentation.type === 'production-flashcard') {
    return <ProductionFlashcard entry={entry} intervals={intervals} chromeLocale={chromeLocale} onRate={onRate} />;
  }

  if (presentation.type === 'recognition-choice' || presentation.type === 'production-choice') {
    const choice = presentation.type === 'recognition-choice'
      ? entry.cards.recognition.choice
      : entry.cards.production?.choice;
    if (!choice) return null;
    return (
      <ChoiceStage
        testId={`teacher-deck-${presentation.type}`}
        prompt={<span lang={choice.direction === 'uk-en' ? 'uk' : 'en'}>{choice.prompt}</span>}
        instruction={
          choice.direction === 'uk-en'
            ? <ChromeDual uk="Що означає це слово?" en="What does this mean?" />
            : <ChromeDual uk="Як це українською?" en="How do you say this in Ukrainian?" />
        }
        options={choice.options.map((option) => ({ label: option.label, correct: option.kind === 'answer' }))}
        optionLang={choice.direction === 'uk-en' ? 'en' : 'uk'}
        answer={locked ? answer : null}
        onChoose={onObjective}
        feedback={locked && answer ? (
          <ChromeDual
            uk={`${entry.uk} — ${entry.en}`}
            en={`${entry.uk} — ${entry.en}`}
          />
        ) : null}
      />
    );
  }

  if (presentation.type === 'cloze') {
    const item = entryClozeItems(deck, entry).find((candidate) => candidate.clozeId === presentation.clozeId);
    if (!item) return null;
    const [before, after] = splitBlank(item.sentence);
    return (
      <ChoiceStage
        testId="teacher-deck-cloze"
        prompt={
          <span lang="uk">
            {before}
            <span className="cloze-blank">{locked ? item.form : '___'}</span>
            {after}
          </span>
        }
        instruction={<ChromeText k="practice.chooseCorrect" />}
        options={item.options.map((option) => ({ label: option.label, correct: option.kind === 'answer' }))}
        optionLang="uk"
        answer={locked ? answer : null}
        onChoose={onObjective}
        feedback={locked ? (
          <>
            <span>{entry.uk} — {entry.en}</span>
            {item.clozeEn ? (
              <span className="teacher-deck-cloze-en" lang="en" data-testid="teacher-deck-cloze-en">
                {item.clozeEn}
              </span>
            ) : null}
            <span className="teacher-deck-attribution">
              {item.source === 'teacher-lesson'
                ? <ChromeDual uk="Речення з уроку вчительки" en="Sentence from the teacher's lesson" />
                : <ChromeDual uk="Речення з підручника" en="Textbook sentence" />}
            </span>
          </>
        ) : null}
      />
    );
  }

  const found = entryGrammarItems(deck, entry).find(
    (candidate) => candidate.item && presentation.type === 'grammar' && idOf(candidate) === presentation.itemId,
  );
  if (!found || presentation.type !== 'grammar') return null;

  if (found.mode === 'stress') {
    const item = found.item;
    const selected = locked && answer ? Number(answer.chosen) : null;
    return (
      <div className="lexicon-stress" data-testid="teacher-deck-grammar-stress">
        <p className="lexicon-choice-prompt mc-q">
          <ChromeDual uk="Де наголос?" en="Where is the stress?" />
        </p>
        <PracticeStress
          item={item}
          selectedPosition={selected}
          answerLocked={locked}
          onSelect={(position) => onObjective(String(position), position === item.stressIndex)}
        />
        {locked ? (
          <p className="lexicon-drill-feedback" data-testid="teacher-deck-feedback" lang="uk">
            {item.stressed} — {entry.en}
          </p>
        ) : null}
      </div>
    );
  }

  if (found.mode === 'paradigm') {
    const item = found.item;
    return (
      <ChoiceStage
        testId="teacher-deck-grammar-paradigm"
        prompt={<span lang="uk">{item.lemma} → {item.slot.labelUk}</span>}
        instruction={<ChromeDual uk="Оберіть правильну форму" en="Choose the correct form" />}
        options={item.options.map((option) => ({ label: option.label, correct: option.kind === 'answer' }))}
        optionLang="uk"
        answer={locked ? answer : null}
        onChoose={onObjective}
        feedback={locked ? <span lang="uk">{item.lemma} ({item.slot.labelUk}): {item.form}</span> : null}
      />
    );
  }

  if (found.mode === 'classify') {
    const item = found.item;
    const set = item.sets.find((candidate) => candidate.setId === presentation.setId) ?? item.sets[0];
    if (!set) return null;
    const correctValues = set.answers ?? [set.answer];
    return (
      <ChoiceStage
        testId="teacher-deck-grammar-classify"
        prompt={<span lang="uk">{item.lemma}: {set.setLabelUk}</span>}
        instruction={<ChromeText k="practice.chooseCorrect" />}
        options={set.options.map((option) => ({ label: option.labelUk, correct: correctValues.includes(option.value) }))}
        optionLang="uk"
        answer={locked ? answer : null}
        onChoose={onObjective}
        feedback={locked ? <span lang="uk">{item.lemma} — {set.answerLabelUk}</span> : null}
      />
    );
  }

  const item = found.item;
  const antonym = found.mode === 'antonym';
  return (
    <ChoiceStage
      testId={`teacher-deck-grammar-${found.mode}`}
      prompt={
        <span lang="uk">
          {antonym ? 'Антонім' : 'Синонім'} до «{item.prompt}»
        </span>
      }
      instruction={<ChromeText k="practice.chooseCorrect" />}
      options={item.options.map((option) => ({ label: option.label, correct: option.kind === 'answer' }))}
      optionLang="uk"
      answer={locked ? answer : null}
      onChoose={onObjective}
      feedback={locked ? <span lang="uk">{item.prompt} — {item.answer}</span> : null}
    />
  );
}

function idOf(found: ReturnType<typeof entryGrammarItems>[number]): string {
  switch (found.mode) {
    case 'stress':
      return found.item.stressId;
    case 'paradigm':
      return found.item.paradigmId;
    case 'classify':
      return found.item.classifyId;
    default:
      return found.item.synonymId;
  }
}

function splitBlank(sentence: string): [string, string] {
  const index = sentence.indexOf('___');
  if (index < 0) return [sentence, ''];
  return [sentence.slice(0, index), sentence.slice(index + 3)];
}

// --------------------------------------------------------------------------- stages

function ChoiceStage({
  testId,
  prompt,
  instruction,
  options,
  optionLang,
  answer,
  onChoose,
  feedback,
}: {
  testId: string;
  prompt: ReactNode;
  instruction: ReactNode;
  options: Option[];
  optionLang: 'uk' | 'en';
  answer: ObjectiveAnswer | null;
  onChoose: (chosen: string, correct: boolean) => void;
  feedback: ReactNode;
}) {
  const locked = Boolean(answer);
  const optionsRef = useRef(options);
  optionsRef.current = options;

  useEffect(() => {
    if (locked) return undefined;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.altKey || event.ctrlKey || event.metaKey) return;
      const target = event.target as HTMLElement | null;
      if (target?.closest?.('input, textarea, select, [contenteditable="true"]')) return;
      const digit = Number.parseInt(event.key, 10);
      const option = optionsRef.current[digit - 1];
      if (!option) return;
      event.preventDefault();
      onChoose(option.label, option.correct);
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [locked, onChoose]);

  return (
    <div className="lexicon-choice" data-testid={testId}>
      <p className="lexicon-choice-prompt mc-q" data-testid="teacher-deck-prompt">{prompt}</p>
      <p className="mc-sub">{instruction}</p>
      <ul className="lexicon-option-list mc-options">
        {options.map((option, index) => {
          const selected = answer?.chosen === option.label;
          const classes = ['mc-opt'];
          if (selected) classes.push('selected');
          if (locked && option.correct) classes.push('correct');
          if (locked && selected && !option.correct) classes.push('wrong');
          return (
            <li key={`${option.label}-${index}`}>
              <button
                type="button"
                className={classes.join(' ')}
                data-correct={locked && option.correct ? 'true' : undefined}
                data-wrong={locked && selected && !option.correct ? 'true' : undefined}
                disabled={locked}
                onClick={() => onChoose(option.label, option.correct)}
              >
                <span className="mc-key">{index + 1}</span>
                <span lang={optionLang}>{option.label}</span>
              </button>
            </li>
          );
        })}
      </ul>
      {locked && answer ? (
        <p
          className={`lexicon-drill-feedback ${answer.correct ? 'correct' : 'wrong'}`}
          data-testid="teacher-deck-feedback"
          role="status"
        >
          <strong>
            {answer.correct ? <ChromeDual uk="Правильно!" en="Correct!" /> : <ChromeDual uk="Неправильно." en="Not quite." />}
          </strong>{' '}
          {feedback}
        </p>
      ) : null}
    </div>
  );
}

/** EN→UK recall: the learner types an attempt (or gives up) before the answer shows, then self-rates. */
function ProductionFlashcard({
  entry,
  intervals,
  chromeLocale,
  onRate,
}: {
  entry: TeacherDeckEntry;
  intervals: Record<PracticeRating, string>;
  chromeLocale: ChromeLocale;
  onRate: (rating: PracticeRating) => void;
}) {
  const [attempt, setAttempt] = useState('');
  const [revealed, setRevealed] = useState<{ attempt: string } | null>(null);
  const [rated, setRated] = useState(false);
  const firstRatingRef = useRef<HTMLButtonElement>(null);
  const matches = revealed ? normalizeAttempt(revealed.attempt) === normalizeAttempt(entry.uk) : false;

  useEffect(() => {
    if (revealed) firstRatingRef.current?.focus();
  }, [revealed]);

  useEffect(() => {
    if (!revealed || rated) return undefined;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.altKey || event.ctrlKey || event.metaKey) return;
      const target = event.target as HTMLElement | null;
      if (target?.closest?.('input, textarea, select, [contenteditable="true"]')) return;
      const index = Number(event.key) - 1;
      if (!Number.isInteger(index) || index < 0 || index >= RATING_ORDER.length) return;
      event.preventDefault();
      setRated(true);
      onRate(RATING_ORDER[index]!);
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [revealed, rated, onRate]);

  return (
    <div className="teacher-deck-production" data-testid="teacher-deck-production-flashcard">
      <p className="lexicon-choice-prompt mc-q" data-testid="teacher-deck-prompt" lang="en">{entry.en}</p>
      {!revealed ? (
        <form
          className="teacher-deck-attempt"
          onSubmit={(event) => {
            event.preventDefault();
            if (attempt.trim()) setRevealed({ attempt });
          }}
        >
          <label>
            <span className="mc-sub">
              <ChromeDual uk="Напишіть українською, потім перевірте" en="Type it in Ukrainian, then check" />
            </span>
            <input
              type="text"
              lang="uk"
              autoComplete="off"
              autoCapitalize="off"
              spellCheck={false}
              data-testid="teacher-deck-attempt"
              value={attempt}
              onChange={(event) => setAttempt(event.target.value)}
            />
          </label>
          <div className="teacher-deck-actions">
            <button type="submit" className="btn btn-accent" data-testid="teacher-deck-reveal" disabled={!attempt.trim()}>
              <ChromeDual uk="Перевірити" en="Check" />
            </button>
            <button
              type="button"
              className="btn"
              data-testid="teacher-deck-dont-know"
              onClick={() => setRevealed({ attempt: '' })}
            >
              <ChromeDual uk="Не знаю" en="I don't know" />
            </button>
          </div>
        </form>
      ) : (
        <div className="teacher-deck-reveal" data-testid="teacher-deck-revealed">
          <p className="flashcard-word" lang="uk" data-testid="teacher-deck-answer">{entry.uk}</p>
          {revealed.attempt ? (
            <p className={matches ? 'correct' : 'wrong'} data-testid="teacher-deck-attempt-result">
              <ChromeDual uk="Ваша відповідь:" en="Your answer:" /> <span lang="uk">{revealed.attempt}</span>{' '}
              {matches ? '✓' : ''}
            </p>
          ) : null}
          <p className="mc-sub">
            <ChromeDual uk="Наскільки добре ви згадали?" en="How well did you recall it?" />
          </p>
          <div className="lexicon-rating-bar rating-bar" role="group" data-revealed="true" data-locked={rated ? 'true' : 'false'}>
            {RATING_ORDER.map((rating, index) => (
              <button
                key={rating}
                type="button"
                ref={index === 0 ? firstRatingRef : undefined}
                className="rate-btn"
                data-rate={rating}
                data-testid={`teacher-deck-rate-${rating}`}
                aria-keyshortcuts={String(index + 1)}
                disabled={rated}
                onClick={() => {
                  setRated(true);
                  onRate(rating);
                }}
              >
                <span className="rk">{index + 1}</span>
                <span className="rt" lang={chromeLocale}>{RATING_LABELS[rating][chromeLocale]}</span>
                <span className="ri">{intervals[rating]}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
