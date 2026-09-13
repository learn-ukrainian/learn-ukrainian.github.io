/** A1 upgrade edition: modules live on the track landing; lessons live under a module. */

export function normalizeDocId(id: string): string {
  return id.replace(/\.mdx?$/, '').replace(/\/index$/, '');
}

export function docParts(id: string): string[] {
  return normalizeDocId(id).split('/').filter(Boolean);
}

export function isUpgradedModuleLanding(id: string, lessons: unknown): boolean {
  const parts = docParts(id);
  return parts[0] === 'a1' && parts.length === 2 && Array.isArray(lessons);
}

export function isUpgradedLesson(id: string): boolean {
  const parts = docParts(id);
  return parts[0] === 'a1' && parts.length === 3 && /^\d+$/.test(parts[2]);
}

export function moduleSlugFromDoc(id: string): string | undefined {
  const parts = docParts(id);
  if (parts[0] !== 'a1' || parts.length < 2) return undefined;
  return parts[1];
}

export function lessonNumberFromDoc(id: string): string | undefined {
  const parts = docParts(id);
  if (!isUpgradedLesson(id)) return undefined;
  return String(Number(parts[2])).padStart(2, '0');
}
