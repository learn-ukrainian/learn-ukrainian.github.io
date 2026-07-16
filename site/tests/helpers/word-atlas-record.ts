import type { EntryRecord } from "@site/src/lib/lexicon/atlas-data-source";
import type { LexiconEntry } from "@site/src/lib/lexicon/atlasDb";
import { normalize as normalizeAtlasSearchText } from "@site/src/lib/lexicon/search";
import type { PracticeLevel } from "@site/src/lib/lexicon/runtime-contract";

const MORPHOLOGY_SUPPRESSED = new Set([
  "multiword_term",
  "expression",
  "phraseologism",
  "proverb",
]);

/** Build an EntryRecord for unit tests that previously passed bare LexiconEntry props. */
export function entryRecordFromParts(
  entry: LexiconEntry,
  options?: {
    componentLinkTargets?: Map<string, string>;
    lemmaEntries?: LexiconEntry[];
    practiceLevels?: PracticeLevel[];
  },
): EntryRecord {
  const targets = options?.componentLinkTargets ?? new Map<string, string>();
  const lemmaSlugs = new Set(
    (options?.lemmaEntries ?? [])
      .filter((item) => item.entry_type === "lemma")
      .map((item) => item.url_slug),
  );
  const componentLinks = MORPHOLOGY_SUPPRESSED.has(entry.entry_type ?? "")
    ? (entry.lemma.match(/[\p{L}\p{M}]+(?:['’][\p{L}\p{M}]+)*/gu) ?? []).map((text) => {
        const targetSlug = targets.get(normalizeAtlasSearchText(text)) ?? null;
        if (targetSlug && lemmaSlugs.has(targetSlug) && targetSlug !== entry.url_slug) {
          return { text, targetSlug };
        }
        return { text, targetSlug: null };
      })
    : [];

  return {
    slug: entry.url_slug,
    kind: entry.entry_type == null ? "form_route" : "article",
    entry,
    aliases: [],
    relations: [],
    provenance: [],
    renderContext: {
      componentLinks,
      practiceLevels: options?.practiceLevels ?? [],
    },
  };
}

export function articleProps(
  entry: LexiconEntry,
  options?: Parameters<typeof entryRecordFromParts>[1] & {
    generatedAt?: string;
    manifestVersion?: string;
  },
) {
  return {
    record: entryRecordFromParts(entry, options),
    generatedAt: options?.generatedAt ?? "test",
    manifestVersion: options?.manifestVersion ?? "test",
  };
}
