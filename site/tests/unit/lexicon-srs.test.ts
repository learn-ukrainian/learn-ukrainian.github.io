import { beforeEach, describe, expect, test } from 'vitest';
import {
  SRS_BACKUP_KEY,
  SRS_STORAGE_KEY,
  detectClockJump,
  getDueQueue,
  loadState,
  masteredCount,
  rateCard,
  saveState,
  type PracticeDeckEntry,
} from '@site/src/lib/lexicon/srs';

const NOW = new Date('2026-06-23T12:00:00.000Z');

function deck(slugs: string[]): PracticeDeckEntry[] {
  return slugs.map((slug) => ({
    lemma: slug,
    slug,
    gloss: `${slug} gloss`,
    ipa: null,
    pos: 'noun',
    cefr: 'A1',
    heritage: null,
    example: null,
    audioKey: null,
  }));
}

beforeEach(() => {
  localStorage.clear();
  loadState(localStorage, NOW);
});

describe('lexicon SRS facade', () => {
  test('schedules deterministically with FSRS defaults', () => {
    const first = rateCard('alpha', 'good', NOW);
    localStorage.clear();
    loadState(localStorage, NOW);
    const second = rateCard('alpha', 'good', NOW);

    expect(second).toEqual(first);
    expect(first.reps).toBe(1);
    expect(first.due).toBe(new Date('2026-06-23T12:10:00.000Z').getTime());
  });

  test('round-trips state through localStorage', () => {
    rateCard('alpha', 'easy', NOW);
    const before = loadState(localStorage, NOW);
    const reloaded = loadState(localStorage, NOW);

    expect(reloaded.cards.get('alpha')).toEqual(before.cards.get('alpha'));
    expect(reloaded.reviews).toHaveLength(1);
  });

  test('migrates version 1 storage and writes backup', () => {
    const oldRaw = JSON.stringify({
      version: 1,
      cards: {
        alpha: {
          due: '2026-06-24T12:00:00.000Z',
          stability: 12,
          difficulty: 4,
          elapsed_days: 0,
          scheduled_days: 1,
          learning_steps: 0,
          reps: 3,
          lapses: 0,
          state: 2,
          last_review: '2026-06-23T12:00:00.000Z',
        },
      },
      reviews: [],
    });
    localStorage.setItem(SRS_STORAGE_KEY, oldRaw);

    const state = loadState(localStorage, NOW);

    expect(state.flags.migrated).toBe(true);
    expect(state.flags.backupWritten).toBe(true);
    expect(localStorage.getItem(SRS_BACKUP_KEY)).toBe(oldRaw);
    expect(state.cards.get('alpha')?.due).toBe(new Date('2026-06-24T12:00:00.000Z').getTime());
    expect(JSON.parse(localStorage.getItem(SRS_STORAGE_KEY) ?? '{}').version).toBe(2);
  });

  test('backs up existing raw state before save overwrites it', () => {
    rateCard('alpha', 'good', NOW);
    const firstRaw = localStorage.getItem(SRS_STORAGE_KEY);

    rateCard('alpha', 'hard', new Date('2026-06-23T12:10:00.000Z'));

    expect(localStorage.getItem(SRS_BACKUP_KEY)).toBe(firstRaw);
  });

  test('keeps corrupt storage and surfaces fallback flag', () => {
    localStorage.setItem(SRS_STORAGE_KEY, '{not json');

    const state = loadState(localStorage, NOW);
    const result = saveState(state, localStorage, NOW.getTime());

    expect(state.flags.corrupt).toBe(true);
    expect(result.ok).toBe(false);
    expect(localStorage.getItem(SRS_STORAGE_KEY)).toBe('{not json');
  });

  test('detects clock jumps beyond seven days', () => {
    expect(detectClockJump(NOW, new Date('2026-07-02T12:00:00.000Z'))).toEqual({
      direction: 'forward',
      deltaDays: 9,
    });
    expect(detectClockJump(NOW, new Date('2026-06-25T12:00:00.000Z'))).toBeNull();
  });

  test('due queue includes new cards and excludes future reviews', () => {
    const entries = deck(['alpha', 'beta']);

    rateCard('alpha', 'good', NOW);

    expect(getDueQueue(entries, NOW).map((entry) => entry.slug)).toEqual(['beta']);
  });

  test('counts mastered cards above stability threshold', () => {
    const state = loadState(localStorage, NOW);
    state.cards.set('alpha', {
      due: NOW.getTime(),
      stability: 30,
      difficulty: 4,
      elapsed_days: 0,
      scheduled_days: 30,
      learning_steps: 0,
      reps: 5,
      lapses: 0,
      state: 2,
    });
    state.cards.set('beta', {
      due: NOW.getTime(),
      stability: 5,
      difficulty: 4,
      elapsed_days: 0,
      scheduled_days: 5,
      learning_steps: 0,
      reps: 2,
      lapses: 0,
      state: 2,
    });

    expect(masteredCount(21)).toBe(1);
  });
});
