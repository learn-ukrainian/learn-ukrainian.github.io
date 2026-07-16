/**
 * Shared Atlas search/entry text normalization (TypeScript side of the dual contract).
 * Must stay byte-compatible with ``scripts/atlas/normalization.py``.
 */
export function normalizeAtlasText(value: string): string {
  return value.normalize("NFC").replace(/\u0301/g, "").toLocaleLowerCase("uk-UA").trim();
}

/** NFC-normalize a URL slug before SHA-256 hashing (no case/stress mutation). */
export function normalizeSlugForHash(slug: string): string {
  return slug.normalize("NFC");
}
