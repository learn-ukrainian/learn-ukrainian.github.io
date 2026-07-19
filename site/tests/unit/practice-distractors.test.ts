import { beforeEach, describe, expect, test } from 'vitest';
import { meaningDistractors } from '@site/src/components/LexiconPractice';
import { loadState } from '@site/src/lib/lexicon/srs';
import type { PracticeDeckData, PracticeLexeme } from '@site/src/lib/lexicon/srs';

const NOW = new Date('2026-06-23T12:00:00.000Z');

function lexeme(lemmaId: string, cefr: string): PracticeLexeme {
  return {
    lemmaId,
    lemma: lemmaId,
    lemmaPlain: lemmaId,
    gloss: `${lemmaId} gloss`,
    ipa: null,
    pos: 'noun',
    cefr,
    heritage: null,
    severity: null,
    paradigm: { cases: { nominative: { singular: lemmaId } } },
  };
}

function deck(rows: { id: string; cefr: string }[]): PracticeDeckData {
  return {
    deckVersion: 'distractor-test',
    level: rows[0]?.cefr ?? 'A1',
    lexemes: rows.map((row) => lexeme(row.id, row.cefr)),
    cloze: [],
    stress: [],
    classify: [],
    paradigm: [],
    synonym: [],
    heritage: [],
    index: rows.map((row, index) => ({
      lemmaId: row.id,
      lemma: row.id,
      cefr: row.cefr,
      modes: ['flashcards', 'choice'],
      hasCloze: false,
      clozeIds: [],
      newOrder: index,
    })),
  };
}

beforeEach(() => {
  localStorage.clear();
  loadState(localStorage, NOW);
});

describe('meaningDistractors', () => {
  test('prefers same-CEFR distractors when enough exist', () => {
    const rows = [
      { id: 'answer', cefr: 'B1' },
      ...Array.from({ length: 5 }, (_, index) => ({ id: `b1-${index}`, cefr: 'B1' })),
      ...Array.from({ length: 5 }, (_, index) => ({ id: `a1-${index}`, cefr: 'A1' })),
    ];
    const testDeck = deck(rows);
    const answer = testDeck.lexemes[0]!;

    const distractors = meaningDistractors(answer, testDeck, 3);

    expect(distractors).toHaveLength(3);
    expect(distractors.every((candidate) => candidate.cefr === 'B1')).toBe(true);
    expect(distractors.some((candidate) => candidate.lemmaId === 'answer')).toBe(false);
  });

  test('falls back to the next CEFR ring when same-level is exhausted', () => {
    const rows = [
      { id: 'answer', cefr: 'B1' },
      { id: 'b1-peer', cefr: 'B1' },
      ...Array.from({ length: 5 }, (_, index) => ({ id: `a2-${index}`, cefr: 'A2' })),
    ];
    const testDeck = deck(rows);
    const answer = testDeck.lexemes[0]!;

    const distractors = meaningDistractors(answer, testDeck, 3);

    expect(distractors).toHaveLength(3);
    expect(distractors[0]?.cefr).toBe('B1');
    expect(distractors[1]?.cefr).toBe('A2');
    expect(distractors[2]?.cefr).toBe('A2');
  });

  test('never returns the answer or a candidate with the same headword', () => {
    const rows = [
      { id: 'answer', cefr: 'A1' },
      { id: 'answer-clone', cefr: 'A1' },
      ...Array.from({ length: 5 }, (_, index) => ({ id: `peer-${index}`, cefr: 'A1' })),
    ];
    const testDeck = deck(rows);
    // Force answer-clone to share the answer's headword by giving it the same gloss.
    testDeck.lexemes[1] = { ...testDeck.lexemes[1]!, gloss: 'answer gloss' };
    const answer = testDeck.lexemes[0]!;

    const distractors = meaningDistractors(answer, testDeck, 3);

    expect(distractors).toHaveLength(3);
    expect(distractors.some((candidate) => candidate.lemmaId === 'answer')).toBe(false);
    expect(distractors.some((candidate) => candidate.lemmaId === 'answer-clone')).toBe(false);
  });

  test('returns at most the requested limit', () => {
    const rows = [
      { id: 'answer', cefr: 'A2' },
      ...Array.from({ length: 20 }, (_, index) => ({ id: `peer-${index}`, cefr: 'A2' })),
    ];
    const testDeck = deck(rows);
    const answer = testDeck.lexemes[0]!;

    const distractors = meaningDistractors(answer, testDeck, 3);

    expect(distractors).toHaveLength(3);
  });

  test('returns fewer than limit when the pool is small', () => {
    const rows = [
      { id: 'answer', cefr: 'A1' },
      { id: 'only-peer', cefr: 'A1' },
    ];
    const testDeck = deck(rows);
    const answer = testDeck.lexemes[0]!;

    const distractors = meaningDistractors(answer, testDeck, 3);

    expect(distractors).toHaveLength(1);
    expect(distractors[0]?.lemmaId).toBe('only-peer');
  });
});
