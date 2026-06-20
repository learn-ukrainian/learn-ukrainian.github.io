import type { APIRoute } from "astro";
import manifest from "../../data/lexicon-manifest.json";

/**
 * Static client-side search index for the Word Atlas typeahead.
 *
 * Emits one compact record per lemma — `l` (lemma), `s` (url_slug), `g` (gloss) —
 * so the typeahead can find any of the ~4k+ (growing to 10k+) entries from any
 * page without a `<select>` that cannot scale. Prerendered at build, so it stays
 * in sync with the manifest automatically. ~251 KB at 4148 entries.
 */
interface ManifestEntry {
  lemma: string;
  url_slug: string;
  gloss: string | null;
}

export const GET: APIRoute = () => {
  const entries = (manifest as { entries: ManifestEntry[] }).entries.map((e) => ({
    l: e.lemma,
    s: e.url_slug,
    g: e.gloss ?? null,
  }));
  return new Response(JSON.stringify(entries), {
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "public, max-age=3600",
    },
  });
};
