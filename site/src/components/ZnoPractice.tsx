import { useEffect, useImperativeHandle, useRef, useState, type ReactNode, type Ref } from 'react';
import { cardKey, DEFAULT_NEW_PER_SESSION, loadState, rateCard } from '../lib/lexicon/srs';
import { CHROME_STRINGS } from '../lib/i18n/chrome';
import { useChromeLocale } from '../lib/i18n/useChromeLocale';
import znoDeckMeta from '../data/practice-zno-meta.json';

export interface ZnoCharMark {
  start: number;
  end: number;
  style?: 'underline' | 'bold';
}

export interface ZnoPracticeItem {
  znoTaskId: string;
  znoMode: 'choice';
  taskFormat: 'single-choice';
  stem: string;
  options: string[];
  optionMarks?: ZnoCharMark[][];
  stemMarks?: ZnoCharMark[];
  correctLetter: string;
  correctIndex: number;
  year: number;
  exam: 'zno' | 'nmt';
  session: string;
  taskNo: number;
  topicTag: string;
  attribution: string;
}

export interface ZnoPracticeDeck {
  deckId: string;
  title: string;
  thinDeck: boolean;
  items: ZnoPracticeItem[];
}

export interface ZnoPracticeProps {
  decks?: ZnoPracticeDeck[];
  /**
   * When supplied by the practice hub, render this deck directly inside the
   * hub's session frame rather than exposing the legacy standalone deck picker.
   */
  deck?: ZnoPracticeDeck | null;
  onBackToDecks?: () => void;
  /** Let the hub's exit button show this session's summary before leaving. */
  sessionControlsRef?: Ref<ZnoSessionControls>;
}

export interface ZnoSessionControls {
  endSession(): void;
}

export interface ZnoPracticeDeckMeta {
  deckId: string;
  title: string;
  thinDeck: boolean;
  itemCount: number;
}

/**
 * Deck picker metadata (title, thin-deck note, item count) with no task
 * content — pre-derived at build time by scripts/generate-zno-deck-meta.ts.
 * The practice hub's deck grid renders from this; a deck's actual items load
 * on demand via `loadZnoDeck` only once the learner opens it (#7671).
 */
export const ZNO_PRACTICE_DECK_META = znoDeckMeta as ZnoPracticeDeckMeta[];

/** One dynamic-import chunk per deck, so opening one deck never pulls in the rest. */
const ZNO_DECK_LOADERS: Record<string, () => Promise<{ default: ZnoPracticeDeck }>> = {
  'zno-stress': () => import('../data/practice-zno.stress.json') as Promise<{ default: ZnoPracticeDeck }>,
  'zno-paronym': () => import('../data/practice-zno.paronym.json') as Promise<{ default: ZnoPracticeDeck }>,
  'zno-lexical-norm': () => import('../data/practice-zno.lexical-norm.json') as Promise<{ default: ZnoPracticeDeck }>,
  'zno-morphological-norm': () => import('../data/practice-zno.morphological-norm.json') as Promise<{ default: ZnoPracticeDeck }>,
  'zno-syntactic-norm': () => import('../data/practice-zno.syntactic-norm.json') as Promise<{ default: ZnoPracticeDeck }>,
  'zno-orthography': () => import('../data/practice-zno.orthography.json') as Promise<{ default: ZnoPracticeDeck }>,
  'zno-morphology': () => import('../data/practice-zno.morphology.json') as Promise<{ default: ZnoPracticeDeck }>,
  'zno-syntax': () => import('../data/practice-zno.syntax.json') as Promise<{ default: ZnoPracticeDeck }>,
  'zno-phonetics': () => import('../data/practice-zno.phonetics.json') as Promise<{ default: ZnoPracticeDeck }>,
};

/** Loads one ZNO deck's full task content on demand. `null` for an unknown deckId. */
export async function loadZnoDeck(deckId: string): Promise<ZnoPracticeDeck | null> {
  const loader = ZNO_DECK_LOADERS[deckId];
  if (!loader) return null;
  const mod = await loader();
  return mod.default;
}

function dayKey(now = new Date()): string {
  return now.toISOString().slice(0, 10);
}

/** FNV-1a — small, deterministic, good enough to spread task ids across a day's seed. */
function hashSeed(input: string): number {
  let hash = 2166136261;
  for (let i = 0; i < input.length; i += 1) {
    hash ^= input.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

/**
 * Splits an official-source stem into its leading task instruction and the
 * remaining reading passage/sentence body, so the UI can render them as two
 * visually distinct blocks instead of one flat wall of text (#6620). Stems
 * without a second line (most stress/paronym items) have no passage.
 */
export function splitStem(stem: string): { instruction: string; passage: string | null } {
  const newlineIndex = stem.indexOf('\n');
  if (newlineIndex === -1) return { instruction: stem.trim(), passage: null };
  const instruction = stem.slice(0, newlineIndex).trim();
  const passage = stem.slice(newlineIndex + 1).trim();
  return { instruction, passage: passage.length > 0 ? passage : null };
}

/** Render plain text with optional char-range highlights (official booklet marks). */
export function renderMarkedText(text: string, marks: readonly ZnoCharMark[] | undefined): ReactNode {
  if (!marks?.length) return text;
  const sorted = [...marks]
    .map((mark) => ({
      ...mark,
      start: Math.max(0, Math.min(mark.start, text.length)),
      end: Math.max(0, Math.min(mark.end, text.length)),
    }))
    .filter((mark) => mark.end > mark.start)
    .sort((left, right) => left.start - right.start);
  const parts: ReactNode[] = [];
  let cursor = 0;
  sorted.forEach((mark, index) => {
    if (mark.start < cursor) return;
    if (mark.start > cursor) parts.push(text.slice(cursor, mark.start));
    const marked = text.slice(mark.start, mark.end);
    if (mark.style === 'bold') {
      parts.push(<strong key={`mark-${index}`} className="zno-practice-mark zno-practice-mark-bold">{marked}</strong>);
    } else {
      parts.push(<span key={`mark-${index}`} className="zno-practice-mark zno-practice-mark-underline">{marked}</span>);
    }
    cursor = mark.end;
  });
  if (cursor < text.length) parts.push(text.slice(cursor));
  return parts;
}

/** Snapshot due cards and a bounded allowance of new tasks, once per session. */
function sessionQueue(
  items: readonly ZnoPracticeItem[],
  sessionSeed: string | number,
  newAllowance = DEFAULT_NEW_PER_SESSION,
): ZnoPracticeItem[] {
  const now = Date.now();
  const cards = loadState().cards;
  const uniqueItems = [...new Map(items.map((item) => [item.znoTaskId, item])).values()];
  const due = uniqueItems.filter((item) => {
    const card = cards.get(cardKey(item.znoTaskId, 'choice'));
    return card !== undefined && card.due <= now;
  });
  const fresh = uniqueItems.filter((item) => !cards.has(cardKey(item.znoTaskId, 'choice')));
  const seededOrder = (left: ZnoPracticeItem, right: ZnoPracticeItem) =>
    hashSeed(`${sessionSeed}:${left.znoTaskId}`) - hashSeed(`${sessionSeed}:${right.znoTaskId}`);
  due.sort((left, right) =>
    (cards.get(cardKey(left.znoTaskId, 'choice'))?.due ?? 0)
      - (cards.get(cardKey(right.znoTaskId, 'choice'))?.due ?? 0) || seededOrder(left, right));
  return [...due, ...fresh.sort(seededOrder).slice(0, newAllowance)];
}

export function nextDueItem(
  items: readonly ZnoPracticeItem[],
  currentId: string | null,
  sessionSeed: string | number = dayKey(),
  excludedIds?: ReadonlySet<string>,
): ZnoPracticeItem | null {
  return sessionQueue(items, sessionSeed).find((item) =>
    item.znoTaskId !== currentId && !excludedIds?.has(item.znoTaskId)) ?? null;
}

/** Shared className + data-* attrs for the ZNO single-choice option buttons —
 * mirrors LexiconPractice's mcOptionAttrs so the two choice UIs never drift
 * into inconsistent selected/correct/wrong marking again (#6620). */
function znoOptionAttrs(index: number, correctIndex: number, selectedIndex: number | null, rated: boolean) {
  const selected = selectedIndex === index;
  const correct = rated && index === correctIndex;
  const wrong = rated && selected && index !== correctIndex;
  const classes = ['zno-practice-option'];
  if (selected) classes.push('selected');
  if (correct) classes.push('correct');
  if (wrong) classes.push('wrong');
  return {
    className: classes.join(' '),
    'data-selected': selected ? 'true' : undefined,
    'data-correct': correct ? 'true' : undefined,
    'data-wrong': wrong ? 'true' : undefined,
  } as const;
}

type SessionPhase =
  | { kind: 'first' | 'retry' | 'review'; items: readonly ZnoPracticeItem[]; index: number; selectedIndex: number | null }
  | { kind: 'summary' };

interface ZnoSessionState {
  queue: readonly ZnoPracticeItem[];
  answers: ReadonlyMap<string, number>;
  retryUsed: boolean;
  phase: SessionPhase;
}

function createSession(deck: ZnoPracticeDeck, dueOnly = false): ZnoSessionState {
  const queue = sessionQueue(deck.items, Math.random(), dueOnly ? 0 : DEFAULT_NEW_PER_SESSION);
  return {
    queue,
    answers: new Map(),
    retryUsed: false,
    phase: queue.length ? { kind: 'first', items: queue, index: 0, selectedIndex: null } : { kind: 'summary' },
  };
}

function ZnoSession({ deck, onExit, sessionControlsRef }: {
  deck: ZnoPracticeDeck;
  onExit(): void;
  sessionControlsRef?: Ref<ZnoSessionControls>;
}) {
  const chromeLocale = useChromeLocale();
  const chrome = CHROME_STRINGS[chromeLocale];
  const [session, setSession] = useState(() => createSession(deck));
  const headingRef = useRef<HTMLHeadingElement>(null);
  const { queue, answers, phase } = session;
  useImperativeHandle(sessionControlsRef, () => ({
    endSession: () => {
      if (phase.kind === 'summary') onExit();
      else setSession((current) => ({ ...current, phase: { kind: 'summary' } }));
    },
  }), [phase.kind, onExit]);
  const currentItem = phase.kind === 'summary' ? null : phase.items[phase.index];
  const selectedIndex = phase.kind === 'summary' ? null
    : phase.kind === 'review' && currentItem ? answers.get(currentItem.znoTaskId) ?? null : phase.selectedIndex;
  const rated = phase.kind === 'review' || selectedIndex !== null;
  const missed = queue.filter((item) => answers.has(item.znoTaskId) && answers.get(item.znoTaskId) !== item.correctIndex);
  const unanswered = queue.filter((item) => !answers.has(item.znoTaskId));
  const correct = queue.length - missed.length - unanswered.length;
  const topicErrors = new Map<string, number>();
  missed.forEach((item) => topicErrors.set(item.topicTag, (topicErrors.get(item.topicTag) ?? 0) + 1));

  useEffect(() => {
    headingRef.current?.focus();
  }, [phase.kind, currentItem?.znoTaskId]);

  function answer(index: number) {
    if (!currentItem || rated || phase.kind === 'summary' || phase.kind === 'review') return;
    const nextAnswers = new Map(answers);
    if (phase.kind === 'first') {
      rateCard(currentItem.znoTaskId, 'choice', index === currentItem.correctIndex ? 'good' : 'again');
      nextAnswers.set(currentItem.znoTaskId, index);
    }
    setSession({ ...session, answers: nextAnswers, phase: { ...phase, selectedIndex: index } });
  }

  function next() {
    if (phase.kind === 'summary' || !rated) return;
    setSession({ ...session, phase: phase.index + 1 < phase.items.length
      ? { ...phase, index: phase.index + 1, selectedIndex: null }
      : { kind: 'summary' } });
  }

  if (phase.kind === 'summary') {
    const dueQueue = sessionQueue(deck.items, dayKey(), 0);
    const cards = loadState().cards;
    const futureDue = deck.items.flatMap((item) => {
      const card = cards.get(cardKey(item.znoTaskId, 'choice'));
      return card && card.due > Date.now() ? [card.due] : [];
    });
    const nextDue = futureDue.length ? new Date(Math.min(...futureDue)) : null;
    return (
      <div className="lexicon-session-summary" data-testid="zno-session-summary">
        <h2 ref={headingRef} tabIndex={-1}>{chrome['practice.sessionComplete']}</h2>
        <p>{deck.title}</p>
        <dl className="lexicon-session-summary-stats">
          <div><dt>{chrome['zno.firstAttemptScore']}</dt><dd data-testid="zno-session-score">{correct}/{queue.length}</dd></div>
          <div><dt>{chrome['zno.unanswered']}</dt><dd>{unanswered.length}</dd></div>
        </dl>
        {unanswered.length > 0 ? (
          <section data-testid="zno-session-unanswered">
            <h3>{chrome['zno.unanswered']}</h3>
            <ul>{unanswered.map((item) => <li key={item.znoTaskId} lang="uk">{item.stem}</li>)}</ul>
          </section>
        ) : null}
        {missed.length > 0 ? (
          <section data-testid="zno-session-topic-errors">
            <h3>{chrome['zno.errorsByTopic']}</h3>
            <ul>{[...topicErrors].map(([topic, count]) => <li key={topic}><span lang="uk">{topic}</span>: {count}</li>)}</ul>
          </section>
        ) : null}
        {nextDue ? <p>{chrome['practice.nextDue']}: <time dateTime={nextDue.toISOString()}>{nextDue.toLocaleString(chromeLocale === 'uk' ? 'uk-UA' : 'en-GB')}</time></p> : null}
        <div className="lexicon-session-summary-actions">
          {missed.length > 0 ? <>
            <button type="button" className="btn" onClick={() => setSession({ ...session, phase: { kind: 'review', items: missed, index: 0, selectedIndex: null } })}>{chrome['zno.reviewErrors']}</button>
            {!session.retryUsed ? <button type="button" className="btn" onClick={() => setSession({ ...session, retryUsed: true, phase: { kind: 'retry', items: missed, index: 0, selectedIndex: null } })}>{chrome['zno.retryMissedOnce']}</button> : null}
          </> : null}
          {dueQueue.length > 0 ? <button type="button" className="btn btn-accent" onClick={() => setSession(createSession(deck, true))}>{chrome['zno.continueDue']}</button> : null}
          <button type="button" className="btn" onClick={onExit}>{chrome['zno.exit']}</button>
        </div>
      </div>
    );
  }

  if (!currentItem) return null;
  const { instruction, passage } = splitStem(currentItem.stem);
  const isCorrectAnswer = rated && selectedIndex === currentItem.correctIndex;
  return (
    <div className="zno-practice-item" data-testid="zno-practice-item">
      <h3 ref={headingRef} tabIndex={-1} className="zno-practice-title">{deck.title}</h3>
      <p role="status" data-testid="zno-session-progress">
        {phase.kind === 'first' ? chrome['practice.sessionProgress'] : phase.kind === 'retry' ? chrome['zno.retryMissedOnce'] : chrome['zno.reviewErrors']}
        {' · '}{phase.kind === 'first' ? `${answers.size}/${queue.length}` : `${phase.index + 1}/${phase.items.length}`}
      </p>
      {deck.thinDeck ? <p className="zno-practice-thin">{chrome['zno.smallCollection']}: {deck.items.length}</p> : null}
      <p className="zno-practice-instruction" lang="uk">{instruction}</p>
      {passage ? (
        <p className="zno-practice-passage" lang="uk" style={{ whiteSpace: 'pre-wrap' }}>
          {renderMarkedText(passage, currentItem.stemMarks)}
        </p>
      ) : null}
      <ul className="zno-practice-options">
        {currentItem.options.map((option, index) => (
          <li key={`${currentItem.znoTaskId}-${index}`}>
            <button
              type="button"
              disabled={rated}
              onClick={() => answer(index)}
              aria-label={`${'АБВГД'[index]} ${option}`}
              {...znoOptionAttrs(index, currentItem.correctIndex, selectedIndex, rated)}
            >
              <span className="zno-practice-option-key">{'АБВГД'[index]}</span>{' '}
              <span className="zno-practice-option-text" lang="uk">{renderMarkedText(option, currentItem.optionMarks?.[index])}</span>
            </button>
          </li>
        ))}
      </ul>
      {rated ? (
        <p
          role="status"
          data-testid="zno-practice-verdict"
          className={isCorrectAnswer ? 'zno-practice-verdict correct' : 'zno-practice-verdict wrong'}
          data-correct={isCorrectAnswer ? 'true' : undefined}
          data-wrong={isCorrectAnswer ? undefined : 'true'}
        >
          {isCorrectAnswer ? `✓ ${chrome['practice.verdict.correct']}` : `✗ ${chrome['zno.correctAnswer']}: ${currentItem.correctLetter}`}
        </p>
      ) : null}
      <p className="zno-practice-attribution" lang="uk">{currentItem.attribution}</p>
      <div className="zno-practice-actions">
        <button type="button" className="zno-practice-next" onClick={next} disabled={!rated}>{chrome['zno.nextTask']}</button>
        <button type="button" className="zno-practice-back" onClick={() => setSession({ ...session, phase: { kind: 'summary' } })}>
          {phase.kind === 'first' ? chrome['zno.endSession'] : chrome['zno.backToSummary']}
        </button>
      </div>
    </div>
  );
}

export default function ZnoPractice({
  decks = [],
  deck: controlledDeck,
  onBackToDecks,
  sessionControlsRef,
}: ZnoPracticeProps) {
  const chrome = CHROME_STRINGS[useChromeLocale()];
  const [activeDeckId, setActiveDeckId] = useState<string | null>(null);
  const activeDeck = controlledDeck ?? decks.find((deck) => deck.deckId === activeDeckId) ?? null;
  return (
    <section className="zno-practice" aria-label={chrome['zno.practiceLabel']} data-testid="zno-practice">
      {!controlledDeck ? <>
        <h2>ЗНО / НМТ</h2>
        <p>{chrome['zno.description']}</p>
      </> : null}
      {activeDeck ? (
        <ZnoSession key={activeDeck.deckId} deck={activeDeck} sessionControlsRef={sessionControlsRef} onExit={() => {
          if (controlledDeck) onBackToDecks?.();
          else setActiveDeckId(null);
        }} />
      ) : (
        <div className="zno-practice-decks">
          {decks.map((deck) => (
            <button key={deck.deckId} type="button" onClick={() => setActiveDeckId(deck.deckId)} data-testid={`zno-deck-${deck.deckId}`}>
              <strong lang="uk">{deck.title}</strong> · {deck.items.length}
              {deck.thinDeck ? <span> · {chrome['zno.smallCollection']}</span> : null}
            </button>
          ))}
        </div>
      )}
    </section>
  );
}
