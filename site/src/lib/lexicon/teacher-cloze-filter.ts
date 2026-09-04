/**
 * Privacy/exclusion filter for teacher-authored cloze items (#6544). Split out
 * of custom-decks.ts (#7671) so it has no dependency on the raw ~6.8MB
 * `lexicon-teacher-cloze.json` source file: the client only ever needs this
 * filter applied to the runtime-fetched `practice-cloze.teacher.json` shard,
 * and the build-time key generator (scripts/generate-teacher-lesson-keys.mjs)
 * needs the exact same rule applied to the raw source — sharing this module
 * keeps both in lockstep instead of duplicating the exclusion list and the
 * private-name scrub.
 */

const EXCLUDED_TEACHER_CLOZE_IDS = new Set([
  'teacher_cloze_57',
  'teacher_cloze_581',
  'teacher_cloze_1521',
]);

// Keep scrubbed teacher-name markers out of public source text while preserving the
// privacy filter for the Latin, Ukrainian, and Russian spellings found in old data.
const PRIVATE_TEACHER_NAME_MARKERS = [
  [97, 108, 111, 110, 97],
  [1072, 1083, 1100, 1086, 1085, 1072],
  [1072, 1083, 1105, 1085, 1072],
].map((codePoints) => String.fromCodePoint(...codePoints));

function containsPrivateTeacherName(value: unknown): boolean {
  if (typeof value === 'string') {
    const normalized = value.toLowerCase();
    return PRIVATE_TEACHER_NAME_MARKERS.some((marker) => normalized.includes(marker));
  }
  if (Array.isArray(value)) {
    return value.some(containsPrivateTeacherName);
  }
  if (value && typeof value === 'object') {
    return Object.values(value).some(containsPrivateTeacherName);
  }
  return false;
}

/** Removes teacher-cloze cards whose public content must not be served. */
export function filterTeacherClozeItems<T extends { clozeId: string }>(items: readonly T[]): T[] {
  return items.filter(
    (item) => !EXCLUDED_TEACHER_CLOZE_IDS.has(item.clozeId) && !containsPrivateTeacherName(item),
  );
}
