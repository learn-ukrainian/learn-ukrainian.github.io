import React from 'react';

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
