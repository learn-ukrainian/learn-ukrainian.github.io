/** Route helpers shared by the docs page (`src/pages/[...slug].astro`). */

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

/** `a1/<module>/<n>` (with or without extension) is lesson `n` of a module; anything else is not. */
export function lessonRoute(id: string, track: string): { module: string; n: number } | undefined {
  const parts = id.replace(/\.mdx?$/, '').split('/').filter(Boolean);
  if (parts.length !== 3 || parts[0] !== track || !/^\d+$/.test(parts[2])) return undefined;
  return { module: parts[1], n: Number(parts[2]) };
}
