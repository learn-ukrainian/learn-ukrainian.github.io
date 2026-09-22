export const LEARNER_LEVEL_STORAGE_KEY = "lu-learner-level";

export const CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"] as const;

export type CefrLevel = (typeof CEFR_LEVELS)[number];
export type LevelFilter = CefrLevel | "all";

const CEFR_RANK = new Map<CefrLevel, number>(
  CEFR_LEVELS.map((level, index) => [level, index]),
);

export interface DailyLevelRow {
  cefr?: string | null;
}

export interface LexiconBrowseRow {
  l: string;
  s: string;
  g: string | null;
  r?: string;
  k?: string;
  c?: string;
  cls?: string;
  hay?: string;
}

export const UKRAINIAN_ALPHABET = [
  "А",
  "Б",
  "В",
  "Г",
  "Ґ",
  "Д",
  "Е",
  "Є",
  "Ж",
  "З",
  "И",
  "І",
  "Ї",
  "Й",
  "К",
  "Л",
  "М",
  "Н",
  "О",
  "П",
  "Р",
  "С",
  "Т",
  "У",
  "Ф",
  "Х",
  "Ц",
  "Ч",
  "Ш",
  "Щ",
  "Ь",
  "Ю",
  "Я",
] as const;

export type UkrainianLetter = (typeof UKRAINIAN_ALPHABET)[number];

const UKRAINIAN_LETTERS = new Set<string>(UKRAINIAN_ALPHABET);

export function normalizeCefrLevel(
  value: unknown,
  fallback: CefrLevel = "A1",
): CefrLevel {
  const normalized = String(value ?? "").trim().toUpperCase();
  return CEFR_LEVELS.includes(normalized as CefrLevel)
    ? (normalized as CefrLevel)
    : fallback;
}

export function parseCefrLevel(value: unknown): CefrLevel | null {
  const normalized = String(value ?? "").trim().toUpperCase();
  return CEFR_LEVELS.includes(normalized as CefrLevel)
    ? (normalized as CefrLevel)
    : null;
}

export function normalizeLevelFilter(value: unknown): LevelFilter {
  const normalized = String(value ?? "").trim().toUpperCase();
  if (!normalized || normalized === "ALL") return "all";
  return CEFR_LEVELS.includes(normalized as CefrLevel)
    ? (normalized as CefrLevel)
    : "all";
}

/**
 * Return all rows in a deterministic order that prefers the learner's level.
 * CEFR is guidance only: higher-level, lower-level, and unlevelled rows remain
 * eligible. Unknown or malformed CEFR values sort after known levels without
 * receiving an inferred placement.
 */
export function prioritizeByLearnerLevel<T extends DailyLevelRow>(
  rows: readonly T[],
  selectedLevel: unknown,
): T[] {
  const targetRank = CEFR_RANK.get(normalizeCefrLevel(selectedLevel)) ?? 0;

  return rows
    .map((row, index) => {
      const level = parseCefrLevel(row.cefr);
      const known = level !== null;
      const rank = known ? (CEFR_RANK.get(level) ?? CEFR_LEVELS.length) : CEFR_LEVELS.length;
      return {
        row,
        index,
        known,
        rank,
        distance: known ? Math.abs(rank - targetRank) : 0,
        aboveTarget: known && rank > targetRank ? 1 : 0,
      };
    })
    .sort(
      (left, right) =>
        Number(right.known) - Number(left.known) ||
        left.distance - right.distance ||
        left.aboveTarget - right.aboveTarget ||
        left.rank - right.rank ||
        left.index - right.index,
    )
    .map(({ row }) => row);
}

/**
 * Narrow daily-pool rows to the exact selected CEFR (#6727).
 *
 * WotD level tabs and the practice Words-of-the-Day zone must *filter*, not
 * re-rank: selecting B2 shows only B2 rows from the pool. Soft CEFR preference
 * (`prioritizeByLearnerLevel`) still applies to practice *session* scheduling;
 * this helper is the hard tab/status filter. Unknown CEFR rows are excluded.
 * Invalid selections normalize to A1 via `normalizeCefrLevel`.
 *
 * Historical name: once meant ≤ selected level; WotD status copy (`B2 · N слів`)
 * requires exact match so the count is not a lie.
 */
export function filterByCumulativeLevel<T extends DailyLevelRow>(
  rows: readonly T[],
  selectedLevel: unknown,
): T[] {
  const level = normalizeCefrLevel(selectedLevel);
  return rows.filter((row) => parseCefrLevel(row.cefr) === level);
}

export function filterRowsByLevel<T extends { c?: string }>(
  rows: readonly T[],
  selectedLevel: unknown,
): T[] {
  const level = normalizeLevelFilter(selectedLevel);
  if (level === "all") return [...rows];
  return rows.filter((row) => parseCefrLevel(row.c) === level);
}

export function firstUkrainianLetter(value: string): UkrainianLetter | null {
  const normalized = value.normalize("NFC").trim().toLocaleUpperCase("uk-UA");
  for (const char of normalized) {
    if (UKRAINIAN_LETTERS.has(char)) return char as UkrainianLetter;
    if (/\p{Letter}/u.test(char)) return null;
  }
  return null;
}

export function populatedUkrainianLetters(
  rows: readonly Pick<LexiconBrowseRow, "l">[],
): UkrainianLetter[] {
  const populated = new Set<UkrainianLetter>();
  for (const row of rows) {
    const letter = firstUkrainianLetter(row.l);
    if (letter) populated.add(letter);
  }
  return UKRAINIAN_ALPHABET.filter((letter) => populated.has(letter));
}

export function filterRowsByLetter<T extends Pick<LexiconBrowseRow, "l">>(
  rows: readonly T[],
  selectedLetter: unknown,
): T[] {
  const letter = String(selectedLetter ?? "").toLocaleUpperCase(
    "uk-UA",
  ) as UkrainianLetter;
  if (!UKRAINIAN_LETTERS.has(letter)) return [];
  return rows.filter((row) => firstUkrainianLetter(row.l) === letter);
}

export function isCefrAtLeast(
  level: unknown,
  minLevel: CefrLevel,
): boolean {
  const current = parseCefrLevel(level);
  if (!current) return false;
  const currentRank = CEFR_RANK.get(current) ?? -1;
  const minRank = CEFR_RANK.get(minLevel) ?? 0;
  return currentRank >= minRank;
}

export const MODE_MIN_LEVELS: Partial<Record<string, CefrLevel>> = {
  paronym: "A2",
  heritage: "A2",
};

export interface ModeLevelRequirement {
  mode: string;
  minLevel: CefrLevel | null;
  isGated: boolean;
  badgeText: string | null;
  tooltip: { uk: string; en: string } | null;
  feedback: { uk: string; en: string } | null;
  note: { uk: string; en: string } | null;
}

export function calculateModeLevelRequirement(
  mode: string,
  learnerLevel: unknown,
  modeCount: number = 0,
): ModeLevelRequirement {
  const minLevel = MODE_MIN_LEVELS[mode] ?? null;
  if (!minLevel) {
    return {
      mode,
      minLevel: null,
      isGated: false,
      badgeText: null,
      tooltip: null,
      feedback: null,
      note: null,
    };
  }

  const meetsLevel = isCefrAtLeast(learnerLevel, minLevel);
  const isGated = !meetsLevel && modeCount <= 0;

  if (!isGated) {
    return {
      mode,
      minLevel,
      isGated: false,
      badgeText: null,
      tooltip: null,
      feedback: null,
      note: null,
    };
  }

  const badgeText = `${minLevel}+`;
  let feedback = {
    uk: `Цей режим доступний з рівня ${minLevel} — змініть рівень для тренування`,
    en: `This mode is available starting at ${minLevel} level — switch level to practice`,
  };

  if (mode === "paronym") {
    feedback = {
      uk: `Пароніми доступні з рівня ${minLevel} — змініть рівень для тренування`,
      en: `Paronyms are available starting at ${minLevel} level — switch level to practice`,
    };
  } else if (mode === "heritage") {
    feedback = {
      uk: `Питома лексика доступна з рівня ${minLevel} — змініть рівень для тренування`,
      en: `Heritage exercises are available starting at ${minLevel} level — switch level to practice`,
    };
  }

  const note = {
    uk: `Доступно з рівня ${minLevel}`,
    en: `Available from ${minLevel} level`,
  };

  return {
    mode,
    minLevel,
    isGated: true,
    badgeText,
    tooltip: feedback,
    feedback,
    note,
  };
}
