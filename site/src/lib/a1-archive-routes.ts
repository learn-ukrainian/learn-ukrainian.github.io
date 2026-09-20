/** Upgraded `/a1/` is a scratch rebuild. Previous edition lives only at `/a1-v1/`. */
export function archiveBookmarkPaths<T extends { id: string; data: { draft?: boolean } }>(_entries: T[]) {
  return [] as { slug: string; entry: T }[];
}
