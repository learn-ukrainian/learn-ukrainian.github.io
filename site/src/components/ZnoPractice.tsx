import { useMemo, useState } from 'react';
import { cardKey, loadState, rateCard, type PracticeRating } from '../lib/lexicon/srs';
import stressDeck from '../data/practice-zno.stress.json';
import paronymDeck from '../data/practice-zno.paronym.json';
import lexicalNormDeck from '../data/practice-zno.lexical-norm.json';
import morphologicalNormDeck from '../data/practice-zno.morphological-norm.json';
import syntacticNormDeck from '../data/practice-zno.syntactic-norm.json';
import orthographyDeck from '../data/practice-zno.orthography.json';
import morphologyDeck from '../data/practice-zno.morphology.json';
import syntaxDeck from '../data/practice-zno.syntax.json';
import phoneticsDeck from '../data/practice-zno.phonetics.json';

export interface ZnoPracticeItem {
  znoTaskId: string;
  znoMode: 'choice';
  taskFormat: 'single-choice';
  stem: string;
  options: string[];
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
}

export const ZNO_PRACTICE_DECKS = [
  stressDeck,
  paronymDeck,
  lexicalNormDeck,
  morphologicalNormDeck,
  syntacticNormDeck,
  orthographyDeck,
  morphologyDeck,
  syntaxDeck,
  phoneticsDeck,
] as ZnoPracticeDeck[];

function taskCountLabel(count: number): string {
  const tail = count % 100;
  if (tail >= 11 && tail <= 14) return `${count} завдань`;
  if (count % 10 === 1) return `${count} завдання`;
  if (count % 10 >= 2 && count % 10 <= 4) return `${count} завдання`;
  return `${count} завдань`;
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

export function nextDueItem(items: readonly ZnoPracticeItem[], currentId: string | null): ZnoPracticeItem | null {
  if (!items.length) return null;
  const now = Date.now();
  const cards = loadState().cards;
  const seedDay = dayKey();
  return [...items]
    .filter((item) => item.znoTaskId !== currentId || items.length === 1)
    .sort((left, right) => {
      const leftDue = cards.get(cardKey(left.znoTaskId, 'choice'))?.due ?? 0;
      const rightDue = cards.get(cardKey(right.znoTaskId, 'choice'))?.due ?? 0;
      const leftPriority = leftDue <= now ? 0 : 1;
      const rightPriority = rightDue <= now ? 0 : 1;
      if (leftPriority !== rightPriority) return leftPriority - rightPriority;
      if (leftDue !== rightDue) return leftDue - rightDue;
      // Stable per-day shuffle among equally-due items: without this, ties always
      // broke alphabetically by znoTaskId, so the same repeated stems (14 unique
      // stress stems cloned across 27 items) surfaced in lockstep every session.
      return hashSeed(`${seedDay}:${left.znoTaskId}`) - hashSeed(`${seedDay}:${right.znoTaskId}`);
    })[0] ?? null;
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

export default function ZnoPractice({
  decks = ZNO_PRACTICE_DECKS,
  deck: controlledDeck,
  onBackToDecks,
}: ZnoPracticeProps) {
  const [activeDeckId, setActiveDeckId] = useState<string | null>(null);
  const [itemId, setItemId] = useState<string | null>(null);
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const [rated, setRated] = useState(false);
  const activeDeck = controlledDeck ?? decks.find((deck) => deck.deckId === activeDeckId) ?? null;
  const currentItem = useMemo(
    () => activeDeck?.items.find((item) => item.znoTaskId === itemId) ?? nextDueItem(activeDeck?.items ?? [], null),
    [activeDeck, itemId],
  );

  function start(deck: ZnoPracticeDeck) {
    setActiveDeckId(deck.deckId);
    setItemId(nextDueItem(deck.items, null)?.znoTaskId ?? null);
    setSelectedIndex(null);
    setRated(false);
  }

  function backToDecks() {
    if (controlledDeck) {
      onBackToDecks?.();
      return;
    }
    setActiveDeckId(null);
  }

  function answer(index: number) {
    if (!currentItem || rated) return;
    setSelectedIndex(index);
    const rating: PracticeRating = index === currentItem.correctIndex ? 'good' : 'again';
    rateCard(currentItem.znoTaskId, 'choice', rating);
    setRated(true);
  }

  function next() {
    if (!activeDeck || !currentItem) return;
    setItemId(nextDueItem(activeDeck.items, currentItem.znoTaskId)?.znoTaskId ?? null);
    setSelectedIndex(null);
    setRated(false);
  }

  return (
    <section className="zno-practice" aria-label="Практика ЗНО та НМТ" data-testid="zno-practice">
      {!controlledDeck ? (
        <>
          <h2>ЗНО / НМТ</h2>
          <p>Офіційні завдання з української мови для інтервального повторення.</p>
        </>
      ) : null}
      {!activeDeck ? (
        <div className="zno-practice-decks">
          {decks.map((deck) => (
            <button key={deck.deckId} type="button" onClick={() => start(deck)} data-testid={`zno-deck-${deck.deckId}`}>
              <strong>{deck.title}</strong> · {taskCountLabel(deck.items.length)}
              {deck.thinDeck ? <span> · Невелика добірка</span> : null}
            </button>
          ))}
        </div>
      ) : currentItem ? (
        (() => {
          const { instruction, passage } = splitStem(currentItem.stem);
          const isCorrectAnswer = rated && selectedIndex === currentItem.correctIndex;
          return (
            <div className="zno-practice-item" data-testid="zno-practice-item">
              <p className="zno-practice-title">{activeDeck.title}</p>
              {activeDeck.thinDeck ? <p role="status" className="zno-practice-thin">Невелика добірка: {taskCountLabel(activeDeck.items.length)}.</p> : null}
              <p className="zno-practice-instruction" lang="uk">{instruction}</p>
              {passage ? (
                <p className="zno-practice-passage" lang="uk" style={{ whiteSpace: 'pre-wrap' }}>{passage}</p>
              ) : null}
              <ul className="zno-practice-options">
                {currentItem.options.map((option, index) => (
                  <li key={`${currentItem.znoTaskId}-${index}`}>
                    <button
                      type="button"
                      disabled={rated}
                      onClick={() => answer(index)}
                      {...znoOptionAttrs(index, currentItem.correctIndex, selectedIndex, rated)}
                    >
                      <span className="zno-practice-option-key">{'АБВГД'[index]}</span>{' '}
                      <span className="zno-practice-option-text" lang="uk">{option}</span>
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
                  {isCorrectAnswer ? '✓ Правильно' : `✗ Правильна відповідь: ${currentItem.correctLetter}`}
                </p>
              ) : null}
              <p className="zno-practice-attribution" lang="uk">{currentItem.attribution}</p>
              <div className="zno-practice-actions">
                <button type="button" className="zno-practice-next" onClick={next} disabled={!rated}>Наступне завдання</button>
                <button type="button" className="zno-practice-back" onClick={backToDecks}>До колод</button>
              </div>
            </div>
          );
        })()
      ) : (
        <p role="status">У цій колоді поки немає придатних завдань.</p>
      )}
    </section>
  );
}
