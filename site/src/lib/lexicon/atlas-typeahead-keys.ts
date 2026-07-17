/**
 * Pure keyboard helpers for Atlas typeahead (Enter exact-match + Escape dismiss).
 */

import { normalize } from "./search";

export interface TypeaheadNavItem {
  lemma: string;
  slug: string;
}

/**
 * Enter with no Arrow selection prefers an exact lemma/slug match; otherwise
 * the first suggestion. When activeIndex >= 0, the highlighted item wins.
 */
export function resolveTypeaheadEnterSelection<T extends TypeaheadNavItem>(
  query: string,
  items: readonly T[],
  activeIndex: number,
): T | null {
  if (!items.length) return null;
  if (activeIndex >= 0 && activeIndex < items.length) {
    return items[activeIndex] ?? null;
  }
  const trimmed = query.trim();
  if (!trimmed) return items[0] ?? null;
  const needle = normalize(trimmed);
  const exact =
    items.find((item) => item.lemma === trimmed || item.slug === trimmed) ??
    items.find(
      (item) => normalize(item.lemma) === needle || normalize(item.slug) === needle,
    );
  return exact ?? items[0] ?? null;
}

/** First Escape closes an open listbox; second Escape clears the input. */
export function resolveTypeaheadEscapeAction(
  listboxOpen: boolean,
): "close-listbox" | "clear-input" {
  return listboxOpen ? "close-listbox" : "clear-input";
}
