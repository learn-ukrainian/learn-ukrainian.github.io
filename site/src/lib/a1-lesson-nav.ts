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

export function hrefFromRouteId(id: string): string {
  return `/${normalizeDocId(id)}/`;
}

/** Frontmatter prev/next may be a full path or a relative slug. Never prefix a path that is already absolute. */
export function resolveNavHref(raw: string, track: string): string {
  const trimmed = raw.trim();
  if (!trimmed) return `/${track}/`;
  if (trimmed.startsWith('/')) {
    return trimmed.endsWith('/') ? trimmed : `${trimmed}/`;
  }
  const slug = trimmed.replace(/^\/+|\/+$/g, '');
  return `/${track}/${slug}/`;
}

export type NavDoc = {
  id: string;
  lessons?: unknown;
  order?: number;
};

/** Module landings (by sidebar order) with each module's lessons after its landing. */
export function a1CourseSequence(docs: NavDoc[]): string[] {
  const modules = docs
    .filter((doc) => isUpgradedModuleLanding(doc.id, doc.lessons))
    .sort((a, b) => (a.order ?? 999) - (b.order ?? 999));
  const sequence: string[] = [];
  for (const module of modules) {
    const slug = moduleSlugFromDoc(module.id);
    sequence.push(normalizeDocId(module.id));
    const lessons = docs
      .filter((doc) => isUpgradedLesson(doc.id) && moduleSlugFromDoc(doc.id) === slug)
      .sort((a, b) => Number(lessonNumberFromDoc(a.id) ?? 0) - Number(lessonNumberFromDoc(b.id) ?? 0));
    for (const lesson of lessons) sequence.push(normalizeDocId(lesson.id));
  }
  return sequence;
}

export function a1AdjacentHrefs(currentId: string, docs: NavDoc[]): { prev?: string; next?: string } {
  const sequence = a1CourseSequence(docs);
  const current = normalizeDocId(currentId);
  const index = sequence.indexOf(current);
  if (index < 0) return {};
  return {
    prev: index > 0 ? hrefFromRouteId(sequence[index - 1]) : '/a1/',
    next: index < sequence.length - 1 ? hrefFromRouteId(sequence[index + 1]) : '/a1/',
  };
}
