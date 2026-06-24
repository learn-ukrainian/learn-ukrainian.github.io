export const LEARNER_LEVEL_STORAGE_KEY = "lu-learner-level";

export const CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"] as const;

export type CefrLevel = (typeof CEFR_LEVELS)[number];
export type LevelFilter = CefrLevel | "all";

const CEFR_RANK = new Map<CefrLevel, number>(
  CEFR_LEVELS.map((level, index) => [level, index]),
);

export interface DailyLevelRow {
  cefr?: string;
}

export interface LexiconBrowseRow {
  l: string;
  s: string;
  g: string | null;
  r?: string;
  k?: string;
  c?: string;
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

export function filterByCumulativeLevel<T extends DailyLevelRow>(
  rows: readonly T[],
  selectedLevel: unknown,
): T[] {
  const cap = normalizeCefrLevel(selectedLevel);
  const capRank = CEFR_RANK.get(cap) ?? 0;

  return rows.filter((row) => {
    const level = parseCefrLevel(row.cefr);
    if (!level) return false;
    return (CEFR_RANK.get(level) ?? Number.POSITIVE_INFINITY) <= capRank;
  });
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
