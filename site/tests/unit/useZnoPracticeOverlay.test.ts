import { describe, expect, test } from "vitest";
import { act, renderHook, waitFor } from "@testing-library/react";
import { loadZnoDeck, ZNO_PRACTICE_DECK_META } from "@site/src/components/ZnoPractice";
import { useZnoPracticeOverlay, ZNO_MODE_META } from "@site/src/components/useZnoPracticeOverlay";

describe("useZnoPracticeOverlay", () => {
  test("resolves the published ZNO deck catalog by deckId (#7671: loads on demand)", async () => {
    const { result } = renderHook(() => useZnoPracticeOverlay());
    expect(result.current.activeZnoDeck).toBeNull();
    expect(result.current.activeZnoDeckLoading).toBe(false);

    act(() => {
      result.current.setActiveZnoDeckId("zno-stress");
    });
    // Selecting a deck flips the loading flag before its chunk resolves.
    expect(result.current.activeZnoDeckLoading).toBe(true);
    expect(result.current.activeZnoDeck).toBeNull();

    const expectedDeck = await loadZnoDeck("zno-stress");
    await waitFor(() => expect(result.current.activeZnoDeck).not.toBeNull());
    expect(result.current.activeZnoDeckLoading).toBe(false);
    expect(result.current.activeZnoDeck).toEqual(expectedDeck);
    expect(result.current.activeZnoDeck?.items.length).toBeGreaterThan(0);

    act(() => {
      result.current.setActiveZnoDeckId(null);
    });
    expect(result.current.activeZnoDeck).toBeNull();
    expect(result.current.activeZnoDeckLoading).toBe(false);
  });

  test("keeps one overlay meta entry per published ZNO deck", () => {
    const deckIds = ZNO_PRACTICE_DECK_META.map((deck) => deck.deckId);
    expect(Object.keys(ZNO_MODE_META).sort()).toEqual([...deckIds].sort());
    for (const deck of ZNO_PRACTICE_DECK_META) {
      expect(ZNO_MODE_META[deck.deckId].description.length).toBeGreaterThan(0);
      expect(ZNO_MODE_META[deck.deckId].descriptionEn.length).toBeGreaterThan(0);
      expect(deck.itemCount).toBeGreaterThan(0);
    }
  });
});
