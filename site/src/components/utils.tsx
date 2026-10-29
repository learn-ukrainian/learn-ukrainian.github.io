import React, { useCallback, useEffect, useLayoutEffect, useMemo, useState } from 'react';

/**
 * Simple seeded PRNG (mulberry32). Produces the same sequence for the same seed,
 * so SSR and client hydration get identical shuffle results.
 */
export function seededRandom(seed: number): () => number {
  return () => {
    seed |= 0; seed = seed + 0x6D2B79F5 | 0;
    let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}

/**
 * Derive a numeric seed from array content so shuffle is deterministic.
 */
export function deriveSeed<T>(array: T[]): number {
  let hash = 0;
  const str = JSON.stringify(array);
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash + str.charCodeAt(i)) | 0;
  }
  return hash;
}

/**
 * Comparable identity of each item. `keyOf` names the displayed value, so options
 * with the same text count as the same option even when callers wrap them with
 * their authored index.
 */
function itemKeys<T>(list: T[], keyOf: (item: T) => unknown): string[] {
  return list.map((item) => JSON.stringify(keyOf(item)));
}

const itself = (item: unknown) => item;

function sameKeys(a: string[], b: string[]): boolean {
  return a.length === b.length && a.every((key, i) => key === b[i]);
}

/**
 * Fisher-Yates shuffle of 0..n-1 driven by `rand`. The displayed sequence of
 * `keys` never equals `avoid` (`null` for no restriction): a draw that does is
 * rotated until it differs, which is impossible only when every key is equal.
 */
function permutation(keys: string[], rand: () => number, avoid: string[] | null): number[] {
  const n = keys.length;
  const order = Array.from({ length: n }, (_, i) => i);
  for (let i = n - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    [order[i], order[j]] = [order[j], order[i]];
  }
  for (let turns = 1; avoid && turns < n && sameKeys(order.map((i) => keys[i]), avoid); turns++) {
    order.push(order.shift()!);
  }
  return order;
}

/**
 * Fisher-Yates shuffle - returns a new shuffled array.
 * Deterministic: uses a seed derived from array content so SSR and client
 * produce the same result (no hydration mismatch). Never returns source order
 * for two or more distinct items, because option lists are authored answer-first.
 */
export function shuffle<T>(array: T[], keyOf: (item: T) => unknown = itself): T[] {
  const keys = itemKeys(array, keyOf);
  return permutation(keys, seededRandom(deriveSeed(array)), keys).map((i) => array[i]);
}

const useIsomorphicLayoutEffect = typeof window === 'undefined' ? useEffect : useLayoutEffect;

/**
 * Hydration-safe fresh shuffles of one or more choice lists.
 *
 * The first render (server and the hydrating client) uses the deterministic
 * `shuffle`, so markup matches. A layout effect then draws a uniformly random
 * order per list before the first paint, and `reshuffle()` draws a new one for
 * each retry that differs from the order on screen. Callers keep their own original-index
 * bookkeeping (map to `{ ..., origIndex }` first), so scoring and per-option
 * feedback still point at the authored option.
 */
export function useShuffledLists<T>(
  lists: T[][],
  keyOf: (item: T) => unknown = itself,
): { lists: T[][]; reshuffle: () => void } {
  const [orders, setOrders] = useState<number[][] | null>(null);
  // Content signature, so callers may pass fresh-but-equal arrays on each render.
  const signature = JSON.stringify(lists);
  const shown = useMemo(
    () => lists.map((list, i) => {
      const order = orders?.[i];
      return order && order.length === list.length ? order.map((j) => list[j]) : shuffle(list, keyOf);
    }),
    [signature, orders],
  );
  const drawFresh = useCallback(() => {
    setOrders((previous) => lists.map((list, i) => {
      // The first draw is unrestricted (avoiding the server order would force
      // source order for two-item lists); a retry never repeats the order on screen.
      const keys = itemKeys(list, keyOf);
      const shownOrder = previous?.[i];
      const avoid = shownOrder && shownOrder.length === list.length ? shownOrder.map((j) => keys[j]) : null;
      return permutation(keys, Math.random, avoid);
    }));
  }, [signature]);
  useIsomorphicLayoutEffect(drawFresh, [drawFresh]);
  return { lists: shown, reshuffle: drawFresh };
}

/** Single-list form of `useShuffledLists`. */
export function useShuffledChoices<T>(
  list: T[],
  keyOf: (item: T) => unknown = itself,
): { choices: T[]; reshuffle: () => void } {
  const { lists, reshuffle } = useShuffledLists([list], keyOf);
  return { choices: lists[0], reshuffle };
}

/**
 * Shuffle ensuring result is NEVER in the same order as correctOrder
 * Useful for anagram/unjumble where we don't want to show the answer
 */
export function shuffleNotCorrect<T>(array: T[], correctOrder: T[]): T[] {
  const arraysEqual = (a: T[], b: T[]) =>
    a.length === b.length && a.every((val, idx) => val === b[idx]);

  // Try shuffling up to 10 times
  for (let attempt = 0; attempt < 10; attempt++) {
    const result = shuffle(array);
    if (!arraysEqual(result, correctOrder)) {
      return result;
    }
  }

  // Force difference by rotating
  const result = shuffle(array);
  if (result.length >= 2 && arraysEqual(result, correctOrder)) {
    result.push(result.shift()!);
  }
  return result;
}

/**
 * Parse simple markdown (bold **text**) and return React elements
 */
export function parseMarkdown(text: string): React.ReactNode {
    if (!text) return text;

    // Split by **text** pattern
    const parts = text.split(/(\*\*[^*]+\*\*)/g);

    return parts.map((part, index) => {
        // Check if this part is bold (**text**)
        if (part.startsWith('**') && part.endsWith('**')) {
            const boldText = part.slice(2, -2);
            return <strong key={index}>{boldText}</strong>;
        }
        return part;
    });
}

/**
 * Strip markdown formatting and return plain text
 */
export function stripMarkdown(text: string): string {
    if (!text) return text;
    return text.replace(/\*\*([^*]+)\*\*/g, '$1');
}
