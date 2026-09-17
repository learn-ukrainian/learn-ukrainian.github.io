/** A1 upgrade edition: modules live on the track landing; lessons live under a module. */

import { A1_UNITS } from '../data/a1-v1-modules';

export function normalizeDocId(id: string): string {
  return id.replace(/\.mdx?$/, '').replace(/\/index$/, '');
}

/** English title from the bilingual A1 manifest (landing cards already use this). */
export function a1ManifestTitleEn(slug: string | undefined): string | undefined {
  if (!slug) return undefined;
  for (const unit of A1_UNITS) {
    const hit = unit.items.find((item) => item.slug === slug);
    if (hit?.titleEn) return hit.titleEn;
  }
  return undefined;
}

/**
 * A1 left-nav label: Ukrainian primary with English support.
 * Skips when the published title is already bilingual (`UA · EN`).
 */
export function withA1EnglishNavLabel(label: string, titleEn?: string): string {
  const trimmed = label.trim();
  if (!titleEn) return trimmed;
  if (trimmed.includes(' · ') || trimmed.includes(titleEn)) return trimmed;
  return `${trimmed} · ${titleEn}`;
}

export function docParts(id: string): string[] {
  return normalizeDocId(id).split('/').filter(Boolean);
}

export function isUpgradedModuleLanding(id: string, lessons: unknown): boolean {
  const parts = docParts(id);
  return parts[0] === 'a1' && parts.length === 2 && Array.isArray(lessons);
}

export type ModuleLesson = { n: number; title: string; minutes: number; href: string };

/** Keep bilingual title/sub from the A1 map when a module unlocks. */
export function withManifestCopy<T extends { title?: string }>(
  item: { num: number; slug: string; title: string; titleEn: string; sub: string; subEn: string },
  upgraded: T & { sidebar?: { order?: number }; lessons?: ModuleLesson[] },
) {
  return {
    num: upgraded.sidebar?.order ?? item.num,
    slug: item.slug,
    title: (typeof upgraded.title === 'string' && upgraded.title) ? upgraded.title : item.title,
    titleEn: item.titleEn,
    sub: item.sub,
    subEn: item.subEn,
    status: 'active' as const,
    lessons: upgraded.lessons,
  };
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
