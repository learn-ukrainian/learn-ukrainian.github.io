/**
 * Unified Case Engine - Case & Number Filter Module (#8167).
 *
 * Provides pure, React-free types, constants, presets, and predicates
 * for multi-select case and number filtering in nominal declension drills.
 * Persists learner preferences to localStorage under `lexicon-case-selector-filter`.
 */

import type { PracticeSelection } from './srs';

export type UkrainianCaseKey =
  | 'називний'
  | 'родовий'
  | 'давальний'
  | 'знахідний'
  | 'орудний'
  | 'місцевий'
  | 'кличний';

export type UkrainianNumberKey = 'singular' | 'plural';

export type CasePresetId =
  | 'all-oblique'
  | 'vocative-only'
  | 'dative-locative'
  | 'plural-endings'
  | 'all';

export interface CaseFilterState {
  cases: UkrainianCaseKey[];
  numbers: UkrainianNumberKey[];
  activePreset: CasePresetId | 'custom';
}

export const ALL_UKRAINIAN_CASES: readonly UkrainianCaseKey[] = [
  'називний',
  'родовий',
  'давальний',
  'знахідний',
  'орудний',
  'місцевий',
  'кличний',
] as const;

export const ALL_NUMBERS: readonly UkrainianNumberKey[] = ['singular', 'plural'] as const;

export const CASE_LABELS_MAP: Record<UkrainianCaseKey, { uk: string; en: string }> = {
  називний: { uk: 'Називний (мн.)', en: 'Nominative (pl.)' },
  родовий: { uk: 'Родовий', en: 'Genitive' },
  давальний: { uk: 'Давальний', en: 'Dative' },
  знахідний: { uk: 'Знахідний', en: 'Accusative' },
  орудний: { uk: 'Орудний', en: 'Instrumental' },
  місцевий: { uk: 'Місцевий', en: 'Locative' },
  кличний: { uk: 'Кличний', en: 'Vocative' },
};

export const NUMBER_LABELS_MAP: Record<UkrainianNumberKey, { uk: string; en: string }> = {
  singular: { uk: 'Однина', en: 'Singular' },
  plural: { uk: 'Множина', en: 'Plural' },
};

export interface CasePreset {
  id: CasePresetId;
  labelUk: string;
  labelEn: string;
  cases: UkrainianCaseKey[];
  numbers: UkrainianNumberKey[];
}

export const CASE_PRESETS: Record<CasePresetId, CasePreset> = {
  'all-oblique': {
    id: 'all-oblique',
    labelUk: 'Усі непрямі відмінки',
    labelEn: 'All Oblique Cases',
    cases: ['родовий', 'давальний', 'знахідний', 'орудний', 'місцевий', 'кличний'],
    numbers: ['singular', 'plural'],
  },
  'vocative-only': {
    id: 'vocative-only',
    labelUk: 'Тільки кличний',
    labelEn: 'Vocative Only',
    cases: ['кличний'],
    numbers: ['singular', 'plural'],
  },
  'dative-locative': {
    id: 'dative-locative',
    labelUk: 'Давальний і місцевий',
    labelEn: 'Dative & Locative Contrast',
    cases: ['давальний', 'місцевий'],
    numbers: ['singular', 'plural'],
  },
  'plural-endings': {
    id: 'plural-endings',
    labelUk: 'Закінчення множини',
    labelEn: 'Plural Endings',
    cases: ['називний', 'родовий', 'давальний', 'знахідний', 'орудний', 'місцевий', 'кличний'],
    numbers: ['plural'],
  },
  all: {
    id: 'all',
    labelUk: 'Усі відмінки',
    labelEn: 'All Cases',
    cases: ['називний', 'родовий', 'давальний', 'знахідний', 'орудний', 'місцевий', 'кличний'],
    numbers: ['singular', 'plural'],
  },
};

export const CASE_FILTER_STORAGE_KEY = 'lexicon-case-selector-filter';

export const DEFAULT_CASE_FILTER: CaseFilterState = {
  cases: [...ALL_UKRAINIAN_CASES],
  numbers: [...ALL_NUMBERS],
  activePreset: 'all',
};

const ENGLISH_TO_UKRAINIAN_CASE: Record<string, UkrainianCaseKey> = {
  nominative: 'називний',
  genitive: 'родовий',
  dative: 'давальний',
  accusative: 'знахідний',
  instrumental: 'орудний',
  locative: 'місцевий',
  vocative: 'кличний',
};

/** Normalizes internal or Ukrainian case names to standard UkrainianCaseKey. */
export function normalizeCaseKey(raw: string | undefined | null): UkrainianCaseKey | null {
  if (!raw) return null;
  const key = raw.trim().toLowerCase();
  if (ALL_UKRAINIAN_CASES.includes(key as UkrainianCaseKey)) {
    return key as UkrainianCaseKey;
  }
  if (key in ENGLISH_TO_UKRAINIAN_CASE) {
    return ENGLISH_TO_UKRAINIAN_CASE[key];
  }
  return null;
}

/** Determines if a set of cases and numbers exactly matches a preset. */
export function detectPreset(
  cases: readonly UkrainianCaseKey[],
  numbers: readonly UkrainianNumberKey[],
): CasePresetId | 'custom' {
  const caseSet = new Set(cases);
  const numberSet = new Set(numbers);

  for (const preset of Object.values(CASE_PRESETS)) {
    if (
      preset.cases.length === caseSet.size &&
      preset.cases.every((c) => caseSet.has(c)) &&
      preset.numbers.length === numberSet.size &&
      preset.numbers.every((n) => numberSet.has(n))
    ) {
      return preset.id;
    }
  }
  return 'custom';
}

/** Load stored filter preferences from localStorage, falling back to default. */
export function loadCaseFilter(): CaseFilterState {
  if (typeof window === 'undefined' || !window.localStorage) {
    return { ...DEFAULT_CASE_FILTER };
  }
  try {
    const raw = window.localStorage.getItem(CASE_FILTER_STORAGE_KEY);
    if (!raw) return { ...DEFAULT_CASE_FILTER };
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object') return { ...DEFAULT_CASE_FILTER };

    const cases = Array.isArray(parsed.cases)
      ? (parsed.cases
          .map((c: string) => normalizeCaseKey(c))
          .filter(Boolean) as UkrainianCaseKey[])
      : [...ALL_UKRAINIAN_CASES];

    const numbers = Array.isArray(parsed.numbers)
      ? (parsed.numbers.filter((n: string) =>
          ALL_NUMBERS.includes(n as UkrainianNumberKey),
        ) as UkrainianNumberKey[])
      : [...ALL_NUMBERS];

    // Ensure at least one case and number selected to avoid completely blank drills
    const safeCases = cases.length > 0 ? cases : [...ALL_UKRAINIAN_CASES];
    const safeNumbers = numbers.length > 0 ? numbers : [...ALL_NUMBERS];
    const activePreset = detectPreset(safeCases, safeNumbers);

    return {
      cases: safeCases,
      numbers: safeNumbers,
      activePreset,
    };
  } catch {
    return { ...DEFAULT_CASE_FILTER };
  }
}

/** Save case filter preferences to localStorage. */
export function saveCaseFilter(state: CaseFilterState): void {
  if (typeof window === 'undefined' || !window.localStorage) return;
  try {
    window.localStorage.setItem(
      CASE_FILTER_STORAGE_KEY,
      JSON.stringify({
        cases: state.cases,
        numbers: state.numbers,
        activePreset: state.activePreset,
      }),
    );
  } catch {
    // LocalStorage quota or access denied - fail silently
  }
}

/** Predicate testing whether a candidate practice card matches the case & number filter. */
export function matchesCaseFilter(
  candidate: Pick<PracticeSelection, 'mode' | 'paradigm'>,
  filter: CaseFilterState,
): boolean {
  if (candidate.mode !== 'paradigm' || !candidate.paradigm) return true;

  const slot = candidate.paradigm.slot;
  const normalizedCase = normalizeCaseKey(slot.case);
  if (!normalizedCase) return false;

  // Filter by case
  if (filter.cases.length > 0 && !filter.cases.includes(normalizedCase)) {
    return false;
  }

  // Filter by number (singular / plural)
  if (filter.numbers.length > 0 && !filter.numbers.includes(slot.number)) {
    return false;
  }

  return true;
}
