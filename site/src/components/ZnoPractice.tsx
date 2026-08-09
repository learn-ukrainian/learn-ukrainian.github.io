import { useMemo, useState } from 'react';
import { cardKey, loadState, rateCard, type PracticeRating } from '../lib/lexicon/srs';
import stressDeck from '../data/practice-zno.stress.json';
import paronymDeck from '../data/practice-zno.paronym.json';
import lexicalNormDeck from '../data/practice-zno.lexical-norm.json';

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

const DEFAULT_DECKS = [stressDeck, paronymDeck, lexicalNormDeck] as ZnoPracticeDeck[];

function taskCountLabel(count: number): string {
  const tail = count % 100;
  if (tail >= 11 && tail <= 14) return `${count} завдань`;
  if (count % 10 === 1) return `${count} завдання`;
  if (count % 10 >= 2 && count % 10 <= 4) return `${count} завдання`;
  return `${count} завдань`;
}

function nextDueItem(items: readonly ZnoPracticeItem[], currentId: string | null): ZnoPracticeItem | null {
  if (!items.length) return null;
  const now = Date.now();
  const cards = loadState().cards;
  return [...items]
    .filter((item) => item.znoTaskId !== currentId || items.length === 1)
    .sort((left, right) => {
      const leftDue = cards.get(cardKey(left.znoTaskId, 'choice'))?.due ?? 0;
      const rightDue = cards.get(cardKey(right.znoTaskId, 'choice'))?.due ?? 0;
      const leftPriority = leftDue <= now ? 0 : 1;
      const rightPriority = rightDue <= now ? 0 : 1;
      return leftPriority - rightPriority || leftDue - rightDue || left.znoTaskId.localeCompare(right.znoTaskId);
    })[0] ?? null;
}

export default function ZnoPractice({ decks = DEFAULT_DECKS }: { decks?: readonly ZnoPracticeDeck[] }) {
  const [activeDeckId, setActiveDeckId] = useState<string | null>(null);
  const [itemId, setItemId] = useState<string | null>(null);
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const [rated, setRated] = useState(false);
  const activeDeck = decks.find((deck) => deck.deckId === activeDeckId) ?? null;
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
      <h2>ЗНО / НМТ</h2>
      <p>Офіційні завдання з української мови для інтервального повторення.</p>
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
        <div className="zno-practice-item" data-testid="zno-practice-item">
          <p className="zno-practice-title">{activeDeck.title}</p>
          {activeDeck.thinDeck ? <p role="status">Невелика добірка: {taskCountLabel(activeDeck.items.length)}.</p> : null}
          <p lang="uk" style={{ whiteSpace: 'pre-wrap' }}>{currentItem.stem}</p>
          <ul className="zno-practice-options">
            {currentItem.options.map((option, index) => {
              const isCorrect = rated && index === currentItem.correctIndex;
              const isWrong = rated && index === selectedIndex && index !== currentItem.correctIndex;
              return (
                <li key={`${currentItem.znoTaskId}-${index}`}>
                  <button
                    type="button"
                    disabled={rated}
                    className={isCorrect ? 'correct' : isWrong ? 'wrong' : undefined}
                    onClick={() => answer(index)}
                  >
                    {'АБВГД'[index]}. {option}
                  </button>
                </li>
              );
            })}
          </ul>
          {rated ? (
            <p role="status" data-testid="zno-practice-verdict">
              {selectedIndex === currentItem.correctIndex ? '✓ Правильно' : `✗ Правильна відповідь: ${currentItem.correctLetter}`}
            </p>
          ) : null}
          <p className="zno-practice-attribution" lang="uk">{currentItem.attribution}</p>
          <button type="button" onClick={next} disabled={!rated}>Наступне завдання</button>
          <button type="button" onClick={() => setActiveDeckId(null)}>До колод</button>
        </div>
      ) : (
        <p role="status">У цій колоді поки немає придатних завдань.</p>
      )}
    </section>
  );
}
