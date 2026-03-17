import React from 'react';

/**
 * Simple seeded PRNG (mulberry32). Produces the same sequence for the same seed,
 * so SSR and client hydration get identical shuffle results.
 */
function seededRandom(seed: number): () => number {
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
function deriveSeed<T>(array: T[]): number {
  let hash = 0;
  const str = JSON.stringify(array);
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash + str.charCodeAt(i)) | 0;
  }
  return hash;
}

/**
 * Fisher-Yates shuffle - returns a new shuffled array.
 * Deterministic: uses a seed derived from array content so SSR and client
 * produce the same result (no hydration mismatch).
 */
export function shuffle<T>(array: T[]): T[] {
  const result = [...array];
  const rand = seededRandom(deriveSeed(array));
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
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
