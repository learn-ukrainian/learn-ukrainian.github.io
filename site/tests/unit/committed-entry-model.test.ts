import { describe, expect, test } from "vitest";

import { getCommittedEntryModelCounts } from "@site/src/lib/lexicon/committed-entry-model";

describe("committed Atlas entry-model counts", () => {
  test("derives public counts from committed search artifacts", () => {
    expect(
      getCommittedEntryModelCounts(
        [
          { l: "кіт", s: "кіт", t: "lemma" },
          { l: "ні в сих ні в тих", s: "ні-в-сих-ні-в-тих", t: "phraseologism" },
        ],
        [{ a: "кота", s: "кіт" }],
      ),
    ).toMatchObject({
      total_reviewed_entries: 2,
      alias_records: 1,
      reviewed_entries_by_type: {
        lemma: 1,
        phraseologism: 1,
      },
    });
  });

  test("rejects a search projection that cannot represent a public article", () => {
    expect(() => getCommittedEntryModelCounts([{ l: "кіт", t: "unknown" }], [])).toThrow(
      "Committed Atlas search index row 0 has an invalid entry type.",
    );
  });
});
