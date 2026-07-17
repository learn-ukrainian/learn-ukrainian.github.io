import { describe, expect, test } from "vitest";
import {
  resolveTypeaheadEnterSelection,
  resolveTypeaheadEscapeAction,
} from "@site/src/lib/lexicon/atlas-typeahead-keys";

describe("resolveTypeaheadEnterSelection", () => {
  const items = [
    { lemma: "гаряча вода", slug: "гаряча-вода" },
    { lemma: "вода", slug: "вода" },
    { lemma: "водний", slug: "водний" },
  ];

  test("Enter with no highlight prefers the exact typed lemma", () => {
    const chosen = resolveTypeaheadEnterSelection("вода", items, -1);
    expect(chosen?.slug).toBe("вода");
  });

  test("Enter with no highlight prefers an exact multiword lemma", () => {
    const chosen = resolveTypeaheadEnterSelection("гаряча вода", items, -1);
    expect(chosen?.slug).toBe("гаряча-вода");
  });

  test("Enter with highlight selects the highlighted item", () => {
    const chosen = resolveTypeaheadEnterSelection("вода", items, 0);
    expect(chosen?.slug).toBe("гаряча-вода");
  });

  test("Enter without an exact match falls back to the first suggestion", () => {
    const chosen = resolveTypeaheadEnterSelection("вод", items, -1);
    expect(chosen?.slug).toBe("гаряча-вода");
  });

  test("empty suggestion list returns null", () => {
    expect(resolveTypeaheadEnterSelection("вода", [], -1)).toBeNull();
  });
});

describe("resolveTypeaheadEscapeAction", () => {
  test("first Escape closes an open listbox", () => {
    expect(resolveTypeaheadEscapeAction(true)).toBe("close-listbox");
  });

  test("second Escape clears the input when the listbox is closed", () => {
    expect(resolveTypeaheadEscapeAction(false)).toBe("clear-input");
  });
});
