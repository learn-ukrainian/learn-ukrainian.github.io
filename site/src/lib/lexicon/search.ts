export interface SearchRow {
  l: string;
  s: string;
  g: string | null;
  r?: string;
  k?: string;
  c?: string;
}

const CYRILLIC_RE = /[\u0400-\u04ff]/;
const LATIN_RE = /[A-Za-z]/;
const ESCAPE_RE = /[&<>"']/g;
const ESCAPE_MAP: Record<string, string> = {
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': "&quot;",
  "'": "&#39;",
};

function normalizeText(value: string): string {
  // NFC first (composes e.g. Latin "é" → "é"), then strip any *residual*
  // combining acute (U+0301). Ukrainian stressed Cyrillic vowels have no
  // precomposed form, so NFC leaves their stress mark standalone and this removes
  // it (на́голос → наголос) for accent-insensitive search — while precomposed Latin
  // accents and, crucially, the breve composing й (и+U+0306) and the diaeresis
  // composing ї (і+U+0308) are left intact.
  return value.normalize("NFC").replace(/\u0301/g, "").toLocaleLowerCase("uk-UA");
}

function escapeHtml(value: string): string {
  return value.replace(ESCAPE_RE, (c) => ESCAPE_MAP[c] ?? c);
}

function compareByLemma(a: SearchRow, b: SearchRow): number {
  const left = normalizeText(a.l);
  const right = normalizeText(b.l);
  if (left < right) return -1;
  if (left > right) return 1;
  return a.s < b.s ? -1 : a.s > b.s ? 1 : 0;
}

export function normalize(q: string): string {
  return normalizeText(q).trim();
}

function matchTier(row: SearchRow, nq: string): number | null {
  const hasLatin = LATIN_RE.test(nq);
  const hasCyrillic = CYRILLIC_RE.test(nq);
  const useLemma = hasCyrillic || !hasLatin;
  const useLatin = hasLatin;
  const lemma = normalizeText(row.l);
  const romanized = row.r ? normalize(row.r) : "";
  const gloss = row.g ? normalize(row.g) : "";

  if (useLemma && lemma === nq) return 0;
  if (useLemma && lemma.startsWith(nq)) return 1;
  if (useLatin && romanized.startsWith(nq)) return 2;
  if (useLemma && lemma.includes(nq)) return 3;
  if (useLatin && romanized.includes(nq)) return 4;
  if (useLatin && gloss.includes(nq)) return 5;
  return null;
}

export function rankMatches(rows: SearchRow[], q: string, limit = 12): SearchRow[] {
  const nq = normalize(q);
  if (!nq || limit <= 0) return [];

  return rows
    .map((row, index) => ({ row, index, tier: matchTier(row, nq) }))
    .filter((item): item is { row: SearchRow; index: number; tier: number } => item.tier !== null)
    .sort((a, b) => a.tier - b.tier || compareByLemma(a.row, b.row) || a.index - b.index)
    .slice(0, limit)
    .map((item) => item.row);
}

export function highlight(text: string, q: string): string {
  const source = String(text).normalize("NFC");
  const needle = normalize(q);
  if (!needle) return escapeHtml(source);

  const haystack = normalizeText(source);
  const index = haystack.indexOf(needle);
  if (index < 0) return escapeHtml(source);

  const before = source.slice(0, index);
  const match = source.slice(index, index + needle.length);
  const after = source.slice(index + needle.length);
  return `${escapeHtml(before)}<mark>${escapeHtml(match)}</mark>${escapeHtml(after)}`;
}
