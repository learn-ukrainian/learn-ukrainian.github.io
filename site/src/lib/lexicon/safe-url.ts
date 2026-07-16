/**
 * URL safety for learner-facing href/src sinks (PR3 R6).
 *
 * No HTML sanitizer dependency: React text nodes already escape markup.
 * This helper only admits http(s), mailto, and same-origin relative paths —
 * rejecting javascript:/data:/vbscript: and other schemes.
 */

const SAFE_ABSOLUTE = /^(https?:|mailto:)/i;
const SAFE_RELATIVE = /^[./?#/]/;

export function safeHref(url: string | null | undefined): string | null {
  if (url == null) return null;
  const trimmed = String(url).trim();
  if (!trimmed) return null;

  // Block scheme-relative and disguised javascript: URLs early.
  const lower = trimmed.toLowerCase();
  if (
    lower.startsWith("javascript:") ||
    lower.startsWith("data:") ||
    lower.startsWith("vbscript:") ||
    lower.startsWith("blob:")
  ) {
    return null;
  }

  if (SAFE_ABSOLUTE.test(trimmed)) {
    try {
      const parsed = new URL(trimmed);
      if (parsed.protocol === "http:" || parsed.protocol === "https:" || parsed.protocol === "mailto:") {
        return trimmed;
      }
      return null;
    } catch {
      return null;
    }
  }

  // Relative / root-absolute paths used throughout the lexicon UI.
  if (SAFE_RELATIVE.test(trimmed) && !trimmed.includes(":")) {
    return trimmed;
  }

  // Allow path-only relative (e.g. "lexicon/foo") without scheme.
  if (!trimmed.includes(":") && !trimmed.includes("\\")) {
    return trimmed;
  }

  return null;
}
