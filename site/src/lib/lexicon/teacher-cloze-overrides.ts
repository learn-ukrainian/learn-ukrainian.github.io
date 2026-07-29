import overrideData from '../../data/lexicon-teacher-cloze-overrides.json';

const overrideIds = overrideData.excludedClozeIds;
const excludedTeacherClozeIds = new Set(
  Array.isArray(overrideIds)
    ? overrideIds.filter((clozeId): clozeId is string => typeof clozeId === 'string')
    : [],
);

/** Removes teacher-cloze cards whose public content must not be served. */
export function filterTeacherClozeItems<T extends { clozeId: string }>(items: readonly T[]): T[] {
  return items.filter((item) => !excludedTeacherClozeIds.has(item.clozeId));
}
