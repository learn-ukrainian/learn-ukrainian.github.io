/**
 * Split text into user-perceived graphemes (letters), keeping combining
 * marks — e.g. the combining acute U+0301 used for Ukrainian stress
 * (а́, о́) — attached to the base letter instead of becoming their own cell.
 */
export function toGraphemes(text: string): string[] {
  if (typeof Intl !== 'undefined' && typeof Intl.Segmenter === 'function') {
    const segmenter = new Intl.Segmenter(undefined, { granularity: 'grapheme' });
    return Array.from(segmenter.segment(text), (s) => s.segment);
  }

  // Fallback: iterate by code point (handles surrogate pairs) and fold any
  // combining mark (\p{M}) into the preceding grapheme.
  const graphemes: string[] = [];
  for (const ch of text) {
    if (/\p{M}/u.test(ch) && graphemes.length > 0) {
      graphemes[graphemes.length - 1] += ch;
    } else {
      graphemes.push(ch);
    }
  }
  return graphemes;
}
