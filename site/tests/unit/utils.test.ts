import { describe, test, expect, vi } from 'vitest';
import { shuffle, shuffleNotCorrect, stripMarkdown } from '@site/src/components/utils';

describe('shuffle', () => {
  test('returns an array of the same length', () => {
    const arr = [1, 2, 3, 4, 5];
    expect(shuffle(arr)).toHaveLength(arr.length);
  });

  test('contains the same elements', () => {
    const arr = ['a', 'b', 'c', 'd'];
    expect(shuffle(arr).sort()).toEqual([...arr].sort());
  });

  test('does not mutate the original array', () => {
    const arr = [1, 2, 3];
    const copy = [...arr];
    shuffle(arr);
    expect(arr).toEqual(copy);
  });

  test('handles empty array', () => {
    expect(shuffle([])).toEqual([]);
  });

  test('handles single-element array', () => {
    expect(shuffle(['x'])).toEqual(['x']);
  });
});

describe('shuffleNotCorrect', () => {
  test('returns an array of the same length', () => {
    const arr = ['a', 'b', 'c'];
    const correct = ['a', 'b', 'c'];
    expect(shuffleNotCorrect(arr, correct)).toHaveLength(arr.length);
  });

  test('contains the same elements', () => {
    const arr = ['x', 'y', 'z'];
    const correct = ['x', 'y', 'z'];
    const result = shuffleNotCorrect(arr, correct);
    expect(result.sort()).toEqual([...arr].sort());
  });

  test('never returns the correct order (10 independent runs)', () => {
    // Use a longer array so the probability of an accidental match is negligible
    const arr = ['a', 'b', 'c', 'd', 'e'];
    for (let i = 0; i < 10; i++) {
      const result = shuffleNotCorrect([...arr], [...arr]);
      const isCorrect = result.every((v, idx) => v === arr[idx]);
      expect(isCorrect).toBe(false);
    }
  });

  test('handles two-element arrays by forcing a swap', () => {
    // With only 2 elements there's only one other permutation
    const result = shuffleNotCorrect(['a', 'b'], ['a', 'b']);
    expect(result).toEqual(['b', 'a']);
  });
});

describe('stripMarkdown', () => {
  test('removes bold markers', () => {
    expect(stripMarkdown('Hello **world**')).toBe('Hello world');
  });

  test('removes multiple bold sections', () => {
    expect(stripMarkdown('**foo** and **bar**')).toBe('foo and bar');
  });

  test('leaves plain text unchanged', () => {
    expect(stripMarkdown('no markdown here')).toBe('no markdown here');
  });

  test('handles empty string', () => {
    expect(stripMarkdown('')).toBe('');
  });
});
