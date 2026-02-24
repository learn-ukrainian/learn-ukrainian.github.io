import React from 'react';

/**
 * Fisher-Yates shuffle - returns a new shuffled array
 */
export function shuffle<T>(array: T[]): T[] {
  const result = [...array];
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
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
