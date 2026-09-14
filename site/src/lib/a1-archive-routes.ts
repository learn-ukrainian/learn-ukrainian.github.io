/** Preserve old A1 bookmarks until a published replacement occupies that route. */
export function archiveBookmarkPaths<T extends { id: string; data: { draft?: boolean } }>(entries: T[]) {
  const normalize = (id: string) => id.replace(/\.mdx?$/, '').replace(/\/index$/, '');
  const published = entries.filter(entry => !entry.data.draft);
  const occupied = new Set(published.map(entry => normalize(entry.id)));
  return published.flatMap(entry => {
    const id = normalize(entry.id);
    if (!/^a1-v1\/[^/]+$/.test(id)) return [];
    const slug = id.replace(/^a1-v1\//, 'a1/');
    return occupied.has(slug) ? [] : [{ slug, entry }];
  });
}
