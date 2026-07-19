/**
 * Atlas → Practice deep-link contract (#5435).
 *
 * Practice hub reads `?lemmaId=` on `/words-of-the-day/practice/` and focuses a
 * single-lemma mixed session when the lemma is in the practice pool
 * (`LexiconPractice` `initializeFocusedPractice`). Missing lemmas surface an
 * honest pool-miss notice rather than a dead end.
 */

export const ATLAS_PRACTICE_PATH = "/words-of-the-day/practice/" as const;
export const ATLAS_PRACTICE_LEMMA_PARAM = "lemmaId" as const;

/** Build a same-origin Practice hub URL focused on the given Atlas lemma id/slug. */
export function atlasPracticeHref(lemmaId: string): string {
  const id = String(lemmaId ?? "").trim();
  if (!id) return ATLAS_PRACTICE_PATH;
  const params = new URLSearchParams({ [ATLAS_PRACTICE_LEMMA_PARAM]: id });
  return `${ATLAS_PRACTICE_PATH}?${params.toString()}`;
}
