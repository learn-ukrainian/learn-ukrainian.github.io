import { beforeEach, describe, expect, test } from 'vitest';
import {
  ALL_NUMBERS,
  ALL_UKRAINIAN_CASES,
  CASE_FILTER_STORAGE_KEY,
  CASE_PRESETS,
  DEFAULT_CASE_FILTER,
  detectPreset,
  loadCaseFilter,
  matchesCaseFilter,
  normalizeCaseKey,
  saveCaseFilter,
  type CaseFilterState,
  type UkrainianCaseKey,
  type UkrainianNumberKey,
} from '@site/src/lib/lexicon/case-filter';
import type { PracticeSelection } from '@site/src/lib/lexicon/srs';

describe('case-filter', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  describe('normalizeCaseKey', () => {
    test('normalizes Ukrainian case names', () => {
      expect(normalizeCaseKey('називний')).toBe('називний');
      expect(normalizeCaseKey(' Родовий ')).toBe('родовий');
      expect(normalizeCaseKey('ДАВАЛЬНИЙ')).toBe('давальний');
      expect(normalizeCaseKey('знахідний')).toBe('знахідний');
      expect(normalizeCaseKey('орудний')).toBe('орудний');
      expect(normalizeCaseKey('місцевий')).toBe('місцевий');
      expect(normalizeCaseKey('кличний')).toBe('кличний');
    });

    test('normalizes English internal case names', () => {
      expect(normalizeCaseKey('nominative')).toBe('називний');
      expect(normalizeCaseKey('genitive')).toBe('родовий');
      expect(normalizeCaseKey('dative')).toBe('давальний');
      expect(normalizeCaseKey('accusative')).toBe('знахідний');
      expect(normalizeCaseKey('instrumental')).toBe('орудний');
      expect(normalizeCaseKey('locative')).toBe('місцевий');
      expect(normalizeCaseKey('vocative')).toBe('кличний');
    });

    test('returns null for invalid or empty names', () => {
      expect(normalizeCaseKey('')).toBeNull();
      expect(normalizeCaseKey(null)).toBeNull();
      expect(normalizeCaseKey(undefined)).toBeNull();
      expect(normalizeCaseKey('unknown_case')).toBeNull();
    });
  });

  describe('presets', () => {
    test('defines required quick presets', () => {
      expect(CASE_PRESETS['all-oblique']).toBeDefined();
      expect(CASE_PRESETS['vocative-only']).toBeDefined();
      expect(CASE_PRESETS['dative-locative']).toBeDefined();
      expect(CASE_PRESETS['plural-endings']).toBeDefined();

      // All Oblique Cases excludes nominative
      expect(CASE_PRESETS['all-oblique'].cases).not.toContain('називний');
      expect(CASE_PRESETS['all-oblique'].cases).toHaveLength(6);

      // Vocative Only
      expect(CASE_PRESETS['vocative-only'].cases).toEqual(['кличний']);

      // Dative & Locative Contrast
      expect(CASE_PRESETS['dative-locative'].cases).toEqual(['давальний', 'місцевий']);

      // Plural Endings
      expect(CASE_PRESETS['plural-endings'].numbers).toEqual(['plural']);
      expect(CASE_PRESETS['plural-endings'].cases).toHaveLength(7);
    });

    test('detectPreset matches presets correctly', () => {
      expect(
        detectPreset(
          ['родовий', 'давальний', 'знахідний', 'орудний', 'місцевий', 'кличний'],
          ['singular', 'plural'],
        ),
      ).toBe('all-oblique');

      expect(detectPreset(['кличний'], ['singular', 'plural'])).toBe('vocative-only');
      expect(detectPreset(['давальний', 'місцевий'], ['singular', 'plural'])).toBe(
        'dative-locative',
      );
      expect(
        detectPreset(ALL_UKRAINIAN_CASES, ['plural']),
      ).toBe('plural-endings');

      expect(detectPreset(['родовий'], ['singular'])).toBe('custom');
    });
  });

  describe('localStorage persistence', () => {
    test('returns default filter when storage is empty', () => {
      const filter = loadCaseFilter();
      expect(filter.cases).toEqual(ALL_UKRAINIAN_CASES);
      expect(filter.numbers).toEqual(ALL_NUMBERS);
      expect(filter.activePreset).toBe('all');
    });

    test('saves and loads filter state', () => {
      const state: CaseFilterState = {
        cases: ['давальний', 'місцевий'],
        numbers: ['singular'],
        activePreset: 'custom',
      };
      saveCaseFilter(state);

      const loaded = loadCaseFilter();
      expect(loaded.cases).toEqual(['давальний', 'місцевий']);
      expect(loaded.numbers).toEqual(['singular']);
      expect(loaded.activePreset).toBe('custom');
    });

    test('falls back gracefully on corrupt localStorage data', () => {
      window.localStorage.setItem(CASE_FILTER_STORAGE_KEY, 'invalid json{{');
      const loaded = loadCaseFilter();
      expect(loaded.cases).toEqual(ALL_UKRAINIAN_CASES);
      expect(loaded.numbers).toEqual(ALL_NUMBERS);
    });
  });

  describe('matchesCaseFilter', () => {
    function makeCandidate(
      caseName: string,
      number: UkrainianNumberKey,
    ): Pick<PracticeSelection, 'mode' | 'paradigm'> {
      return {
        mode: 'paradigm',
        paradigm: {
          paradigmId: 'test:1',
          lemmaId: 'test',
          lemma: 'тест',
          slot: {
            case: caseName,
            number,
            labelUk: `${caseName}, ${number}`,
          },
          form: 'тестом',
          options: [],
        },
      };
    }

    test('allows non-paradigm modes unconditionally', () => {
      const nonParadigmCandidate: Pick<PracticeSelection, 'mode' | 'paradigm'> = {
        mode: 'cloze',
      };
      expect(
        matchesCaseFilter(nonParadigmCandidate, {
          cases: ['кличний'],
          numbers: ['singular'],
          activePreset: 'custom',
        }),
      ).toBe(true);
    });

    test('filters paradigm items by case', () => {
      const filter: CaseFilterState = {
        cases: ['давальний', 'місцевий'],
        numbers: ['singular', 'plural'],
        activePreset: 'dative-locative',
      };

      expect(matchesCaseFilter(makeCandidate('давальний', 'singular'), filter)).toBe(true);
      expect(matchesCaseFilter(makeCandidate('місцевий', 'plural'), filter)).toBe(true);
      expect(matchesCaseFilter(makeCandidate('родовий', 'singular'), filter)).toBe(false);
      expect(matchesCaseFilter(makeCandidate('називний', 'plural'), filter)).toBe(false);
    });

    test('filters paradigm items by number', () => {
      const filter: CaseFilterState = {
        cases: [...ALL_UKRAINIAN_CASES],
        numbers: ['plural'],
        activePreset: 'plural-endings',
      };

      expect(matchesCaseFilter(makeCandidate('родовий', 'plural'), filter)).toBe(true);
      expect(matchesCaseFilter(makeCandidate('родовий', 'singular'), filter)).toBe(false);
    });

    test('handles English case names in candidate slot', () => {
      const filter: CaseFilterState = {
        cases: ['кличний'],
        numbers: ['singular', 'plural'],
        activePreset: 'vocative-only',
      };

      expect(matchesCaseFilter(makeCandidate('vocative', 'singular'), filter)).toBe(true);
      expect(matchesCaseFilter(makeCandidate('genitive', 'singular'), filter)).toBe(false);
    });

    test('active-session filter change: committed non-matching card is rejected by stabilization guard', () => {
      // User initially was on default (all cases) and had a nominative card committed
      const committedCandidate = makeCandidate('називний', 'plural') as PracticeSelection;
      (committedCandidate as any).itemId = 'item_nom_pl';

      // User switches preset to "vocative-only"
      const vocativeFilter: CaseFilterState = {
        cases: ['кличний'],
        numbers: ['singular', 'plural'],
        activePreset: 'vocative-only',
      };

      // The poolFilter predicate evaluates matchesCaseFilter
      const poolFilter = (candidate: PracticeSelection) => matchesCaseFilter(candidate, vocativeFilter);

      // Verify that committed selection fails poolFilter
      expect(poolFilter(committedCandidate)).toBe(false);

      // In LexiconPractice selection stabilization:
      // if poolFilter returns false, committed.selection must NOT be retained
      const freshSelection = makeCandidate('кличний', 'singular') as PracticeSelection;
      (freshSelection as any).itemId = 'item_voc_sg';

      const committed = {
        historyLen: 0,
        selection: committedCandidate,
      };

      const history = [];
      const selectionDeck = { index: [{ itemId: 'item_nom_pl' }, { itemId: 'item_voc_sg' }] };
      const itemIdPresentInDeck = (deck: any, id: string) => deck.index.some((i: any) => i.itemId === id);

      // Simulation of LexiconPractice line 3100-3108 stabilization check:
      let effectiveSelection = freshSelection;
      if (
        committed &&
        committed.historyLen === history.length &&
        freshSelection &&
        freshSelection.itemId !== committed.selection.itemId &&
        itemIdPresentInDeck(selectionDeck, committed.selection.itemId) &&
        (!poolFilter || poolFilter(committed.selection))
      ) {
        effectiveSelection = committed.selection;
      }

      // Must pick the fresh vocative card, NOT retain the committed nominative card
      expect(effectiveSelection.itemId).toBe('item_voc_sg');
    });
  });
});
