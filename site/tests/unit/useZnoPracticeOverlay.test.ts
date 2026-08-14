import { describe, expect, test } from "vitest";
import { act, renderHook } from "@testing-library/react";
import { ZNO_PRACTICE_DECKS } from "@site/src/components/ZnoPractice";
import { useZnoPracticeOverlay, ZNO_MODE_META } from "@site/src/components/useZnoPracticeOverlay";

describe("useZnoPracticeOverlay", () => {
  test("resolves the published ZNO deck catalog by deckId", () => {
    const { result } = renderHook(() => useZnoPracticeOverlay());
    expect(result.current.activeZnoDeck).toBeNull();

    act(() => {
      result.current.setActiveZnoDeckId("zno-stress");
    });
    expect(result.current.activeZnoDeck).toBe(
      ZNO_PRACTICE_DECKS.find((deck) => deck.deckId === "zno-stress"),
    );
    expect(result.current.activeZnoDeck?.items.length).toBeGreaterThan(0);

    act(() => {
      result.current.setActiveZnoDeckId(null);
    });
    expect(result.current.activeZnoDeck).toBeNull();
  });

  test("keeps one overlay meta entry per published ZNO deck", () => {
    const deckIds = ZNO_PRACTICE_DECKS.map((deck) => deck.deckId);
    expect(Object.keys(ZNO_MODE_META).sort()).toEqual([...deckIds].sort());
    for (const deck of ZNO_PRACTICE_DECKS) {
      expect(ZNO_MODE_META[deck.deckId].description.length).toBeGreaterThan(0);
      expect(ZNO_MODE_META[deck.deckId].descriptionEn.length).toBeGreaterThan(0);
    }
  });
});
