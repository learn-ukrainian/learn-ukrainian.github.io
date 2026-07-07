import { beforeEach, describe, expect, test } from 'vitest';
import { State } from 'ts-fsrs';
import {
  WEAK_AREA_MIN_BUCKET_ATTEMPTS,
  WEAK_AREA_MIN_TOTAL_REVIEWS,
  caseLabelUk,
  computeWeakAreas,
  focusModeForWeakness,
  matchesWeakness,
  weakCaseChips,
  type WeakArea,
} from '@site/src/lib/lexicon/weak-areas';
import {
  cardKey,
  loadState,
  selectNextPracticeItem,
  type PracticeClozeItem,
  type PracticeDeckData,
  type PracticeMode,
  type PracticeRating,
  type PracticeSelection,
  type ReviewLogEntry,
} from '@site/src/lib/lexicon/srs';

const NOW = new Date('2026-06-23T12:00:00.000Z');

let reviewClock = NOW.getTime();

function review(
  overrides: Partial<ReviewLogEntry> & { mode: PracticeMode; rating: PracticeRating },
): ReviewLogEntry {
  reviewClock += 1000;
  return {
    cardKey: cardKey(overrides.lemmaId ?? 'lex', overrides.mode),
    lemmaId: overrides.lemmaId ?? 'lex',
    state: State.Review,
    due: reviewClock,
    stability: 4,
    difficulty: 5,
    elapsed_days: 1,
    last_elapsed_days: 1,
    scheduled_days: 1,
    learning_steps: 0,
    review: reviewClock,
    ...overrides,
  };
}

/** N cloze reviews of one case, `misses` of them recorded as a miss rating. */
function clozeCase(caseKey: string, total: number, misses: number, missRating: PracticeRating = 'again') {
  return Array.from({ length: total }, (_unused, index) =>
    review({
      mode: 'cloze',
      blankCase: caseKey,
      rating: index < misses ? missRating : 'good',
      lemmaId: `${caseKey}-${index}`,
    }),
  );
}

beforeEach(() => {
  reviewClock = NOW.getTime();
  localStorage.clear();
  loadState(localStorage, NOW);
});

describe('computeWeakAreas', () => {
  test('ranks weak cases from a known lapse pattern with stable ordering', () => {
    const log = [
      ...clozeCase('genitive', 10, 6), // 0.60 miss → weak
      ...clozeCase('accusative', 10, 1), // 0.10 miss → strong
      ...clozeCase('instrumental', 10, 5, 'hard'), // 0.50 (hard counts) → weak
    ];

    const areas = computeWeakAreas(log);
    const cases = areas.filter((area) => area.dimension === 'case');

    expect(cases.map((area) => area.key)).toEqual(['genitive', 'instrumental']);
    expect(cases[0]).toMatchObject({ key: 'genitive', label: 'родовий', attempts: 10, misses: 6 });
    expect(cases[0].lapseRate).toBeCloseTo(0.6, 5);
    expect(cases[1]).toMatchObject({ key: 'instrumental', label: 'орудний' });
    // Worst-first ordering holds across the whole ranked list.
    expect(areas[0].lapseRate).toBeGreaterThanOrEqual(areas[1].lapseRate);

    // Recomputing the same log yields byte-identical ordering (deterministic).
    expect(computeWeakAreas(log)).toEqual(areas);

    // The surfaced chip set is cases-only, capped, and matches the ranking.
    expect(weakCaseChips(log).map((chip) => chip.label)).toEqual(['родовий', 'орудний']);
  });

  test('returns no chips below the minimum-data threshold (no noise for new learners)', () => {
    const log = clozeCase('genitive', WEAK_AREA_MIN_TOTAL_REVIEWS - 1, WEAK_AREA_MIN_TOTAL_REVIEWS - 1);
    expect(log.length).toBeLessThan(WEAK_AREA_MIN_TOTAL_REVIEWS);
    expect(computeWeakAreas(log)).toEqual([]);
    expect(weakCaseChips(log)).toEqual([]);
  });

  test('excludes buckets below the per-bucket attempts floor even at 100% miss', () => {
    const log = [
      ...clozeCase('genitive', WEAK_AREA_MIN_BUCKET_ATTEMPTS - 1, WEAK_AREA_MIN_BUCKET_ATTEMPTS - 1),
      ...clozeCase('accusative', 22, 0), // pads total over the threshold, but is strong
    ];
    expect(log.length).toBeGreaterThanOrEqual(WEAK_AREA_MIN_TOTAL_REVIEWS);
    expect(weakCaseChips(log)).toEqual([]);
  });

  test('excludes buckets below the lapse-rate threshold', () => {
    const log = clozeCase('accusative', 25, 2); // 0.08 miss → strong
    expect(weakCaseChips(log)).toEqual([]);
  });

  test('detects a weak heritage kind from the log', () => {
    const log = [
      ...Array.from({ length: 8 }, (_u, i) =>
        review({ mode: 'heritage', heritageKind: 'lexical', rating: i < 5 ? 'again' : 'good', lemmaId: `h-${i}` }),
      ),
      ...clozeCase('accusative', 15, 0),
    ];
    const heritage = computeWeakAreas(log).filter((area) => area.dimension === 'heritage');
    expect(heritage).toHaveLength(1);
    expect(heritage[0]).toMatchObject({ key: 'lexical', dimension: 'heritage' });
  });
});

describe('caseLabelUk', () => {
  test('maps case slugs to Ukrainian names and falls back to the slug', () => {
    expect(caseLabelUk('genitive')).toBe('родовий');
    expect(caseLabelUk('instrumental')).toBe('орудний');
    expect(caseLabelUk('unknown-case')).toBe('unknown-case');
  });
});

describe('matchesWeakness + poolFilter', () => {
  const genitive: WeakArea = {
    dimension: 'case',
    key: 'genitive',
    label: 'родовий',
    attempts: 10,
    misses: 6,
    lapseRate: 0.6,
  };

  function candidate(partial: Partial<PracticeSelection>): PracticeSelection {
    return partial as PracticeSelection;
  }

  test('matches only candidates on the weak dimension', () => {
    expect(matchesWeakness(candidate({ mode: 'cloze', cloze: { blankCase: 'genitive' } as PracticeClozeItem }), genitive)).toBe(true);
    expect(matchesWeakness(candidate({ mode: 'cloze', cloze: { blankCase: 'accusative' } as PracticeClozeItem }), genitive)).toBe(false);
    expect(matchesWeakness(candidate({ mode: 'flashcards' }), genitive)).toBe(false);

    const modeWeak: WeakArea = { dimension: 'mode', key: 'choice', label: 'вибір', attempts: 9, misses: 4, lapseRate: 0.44 };
    expect(matchesWeakness(candidate({ mode: 'choice' }), modeWeak)).toBe(true);
    expect(matchesWeakness(candidate({ mode: 'flashcards' }), modeWeak)).toBe(false);
  });

  test('focus mode is cloze for a case weakness', () => {
    expect(focusModeForWeakness(genitive)).toBe('cloze');
  });

  test('a weakness poolFilter restricts the session pool to only matching items', () => {
    const deck = clozeDeck();
    const genitivePool = collectClozeCases(deck, genitive);
    // Every item the selector can serve under the genitive filter is genitive — nothing leaks.
    expect(genitivePool.size).toBe(1);
    expect(genitivePool.has('genitive')).toBe(true);

    const accusative: WeakArea = { ...genitive, key: 'accusative', label: 'знахідний' };
    const accusativePool = collectClozeCases(deck, accusative);
    expect(accusativePool.size).toBe(1);
    expect(accusativePool.has('accusative')).toBe(true);
  });
});

/** Drive the selector through the deck under a weakness filter; collect every served case. */
function collectClozeCases(deck: PracticeDeckData, weakness: WeakArea): Set<string> {
  const cases = new Set<string>();
  for (let iteration = 0; iteration < 12; iteration += 1) {
    const selection = selectNextPracticeItem(deck, {
      now: NOW,
      modeFilter: 'cloze',
      sessionSeed: iteration,
      poolFilter: (item) => matchesWeakness(item, weakness),
    });
    if (selection?.cloze) cases.add(selection.cloze.blankCase);
  }
  return cases;
}

function clozeItem(lemmaId: string, blankCase: string): PracticeClozeItem {
  return {
    clozeId: `${lemmaId}-cloze`,
    lemmaId,
    sentenceFrameId: `${lemmaId}-frame`,
    sentence: 'Це ___.',
    blankCase,
    form: lemmaId,
    caseRule: {
      ruleId: `${blankCase}-rule`,
      case: blankCase,
      caseLabel: caseLabelUk(blankCase),
      trigger: 'test',
      triggerLabel: 'тест',
      feedback: 'feedback',
    },
    clozeEn: 'This is.',
    options: [],
  };
}

function clozeDeck(): PracticeDeckData {
  const specs = [
    { lemmaId: 'knyha', blankCase: 'genitive' },
    { lemmaId: 'robota', blankCase: 'accusative' },
    { lemmaId: 'misto', blankCase: 'genitive' },
  ];
  return {
    deckVersion: 'weak-area-test',
    level: 'A1',
    lexemes: specs.map((spec) => ({
      lemmaId: spec.lemmaId,
      lemma: spec.lemmaId,
      lemmaPlain: spec.lemmaId,
      gloss: `${spec.lemmaId} gloss`,
      ipa: null,
      pos: 'noun',
      cefr: 'A1',
      heritage: null,
      severity: null,
      paradigm: { cases: {} },
    })),
    index: specs.map((spec, order) => ({
      lemmaId: spec.lemmaId,
      lemma: spec.lemmaId,
      cefr: 'A1',
      modes: ['cloze'] as PracticeMode[],
      hasCloze: true,
      clozeIds: [`${spec.lemmaId}-cloze`],
      newOrder: order,
    })),
    cloze: specs.map((spec) => clozeItem(spec.lemmaId, spec.blankCase)),
  };
}
