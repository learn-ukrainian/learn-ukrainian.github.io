import type { AtlasEntryModelCounts } from "./atlasDb.ts";

const ENTRY_TYPES = [
  "lemma",
  "expression",
  "phraseologism",
  "proverb",
  "multiword_term",
  "proper_name",
] as const;

type EntryType = (typeof ENTRY_TYPES)[number];

function isEntryType(value: unknown): value is EntryType {
  return typeof value === "string" && (ENTRY_TYPES as readonly string[]).includes(value);
}

/**
 * Derive the public Atlas aggregate from its committed runtime projections.
 *
 * The SQLite database is an Atlas-production input, not a prerequisite for
 * consuming the published search and alias artifacts during normal site runs.
 */
export function getCommittedEntryModelCounts(
  searchIndex: unknown,
  searchAliases: unknown,
): AtlasEntryModelCounts {
  if (!Array.isArray(searchIndex)) {
    throw new Error("Committed Atlas search index must be an array.");
  }
  if (!Array.isArray(searchAliases)) {
    throw new Error("Committed Atlas search aliases must be an array.");
  }

  const counts = Object.fromEntries(ENTRY_TYPES.map((entryType) => [entryType, 0])) as AtlasEntryModelCounts["reviewed_entries_by_type"];
  for (const [index, row] of searchIndex.entries()) {
    const entryType = row && typeof row === "object" ? (row as { t?: unknown }).t : undefined;
    if (!isEntryType(entryType)) {
      throw new Error(`Committed Atlas search index row ${index} has an invalid entry type.`);
    }
    counts[entryType] += 1;
  }

  return {
    reviewed_entries_by_type: counts,
    total_reviewed_entries: searchIndex.length,
    alias_records: searchAliases.length,
    candidate_evidence_count: 0,
    candidate_evidence_by_bucket: {},
    noise_rejected: 0,
  };
}
