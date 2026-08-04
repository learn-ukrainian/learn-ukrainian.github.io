export interface OriginInput {
  text: string;
  source: string;
}

export interface FormattedOrigin {
  /** Cleaned, trimmed, learner-facing etymology prose. */
  text: string;
  /** Short learner-facing attribution (e.g. "Wiktionary"). */
  source: string;
}

const KAIKKI_SOURCE = "kaikki/Wiktionary (CC BY-SA 3.0)";
const MAX_LENGTH = 160;

// Matches a parenthetical that contains Latin-script characters.
// Tolerates one level of nested parentheses, which Wiktionary uses for
// transliterations: (naštovx(núty)). Never strip quote- or markup-bearing
// parens (XSS fixtures, code, etc.) — only transliteration-style content.
const LATIN_PARENTHETICAL_RE =
  /\((?=[^)"<>]*[A-Za-z])(?:[^()"<>]|\([^()"<>]*\))+\)/g;

// Imperial-comparison clauses that Kaikki sometimes appends.
// Keep the sentence's own period before the clause; only drop the clause itself.
const COMPARE_CLAUSE_RE = /(?:\s*,\s*)?\b[Cc]ompare\s+[A-Z][a-z]+\b[^.]*\.?/g;

// Borrowed-looking license/source fragments that should never be prose.
const SOURCE_FRAGMENT_RE = /\bkaikki\/Wiktionary\b|\(CC BY-SA[^)]*\)/g;

// Internal mphdict/ESUM labels are not learner-facing etymology prose.
const ESUM_LABEL_RE = /Стаття\s+ЕСУМ|етимонів\s*:/i;

function collapseWhitespace(value: string): string {
  return value.replace(/\s+/g, " ").trim();
}

function truncate(value: string, limit: number): string {
  if (value.length <= limit) return value;
  const breakpoint = value.lastIndexOf(" ", limit);
  const end = breakpoint > 0 ? breakpoint : limit;
  return `${value.slice(0, end)}…`;
}

function sentenceCase(value: string): string {
  if (!value) return value;
  return value.charAt(0).toLocaleUpperCase("uk") + value.slice(1);
}

function isEmptyOrPunctuation(value: string): boolean {
  return value.length === 0 || /^[\s\p{P}]+$/u.test(value);
}

/**
 * Clean a raw Kaikki/Wiktionary etymology string so it reads as intentional
 * learner-facing prose. Returns `null` when the result would be garbage,
 * empty, or an internal source label rather than real etymology.
 */
export function cleanOriginText(value: string | undefined | null): string | null {
  if (!value) return null;

  let text = collapseWhitespace(value);
  if (isEmptyOrPunctuation(text)) return null;

  text = text
    .replace(LATIN_PARENTHETICAL_RE, "")
    .replace(COMPARE_CLAUSE_RE, "")
    .replace(SOURCE_FRAGMENT_RE, "")
    .replace(/\s+/g, " ")
    .trim();

  // Pull stray punctuation back against the preceding word instead of deleting it.
  text = text.replace(/\s+([.,])/g, "$1").trim();

  if (isEmptyOrPunctuation(text)) return null;
  if (ESUM_LABEL_RE.test(text)) return null;

  text = sentenceCase(text);
  return truncate(text, MAX_LENGTH);
}

/**
 * Return a short learner-facing source label.
 */
export function formatOriginSource(source: string | undefined | null): string {
  if (!source) return "";
  if (source === KAIKKI_SOURCE || source.includes("Wiktionary")) {
    return "Wiktionary";
  }
  return source;
}

/**
 * Format an origin block for display. Fails closed: any unusable input
 * becomes `null` so callers can hide the surface instead of showing a raw dump.
 */
export function formatOrigin(
  input: OriginInput | undefined | null,
): FormattedOrigin | null {
  if (!input) return null;
  const text = cleanOriginText(input.text);
  if (!text) return null;
  const source = formatOriginSource(input.source);
  return { text, source };
}
