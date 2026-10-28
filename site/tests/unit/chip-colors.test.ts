import { describe, expect, test } from 'vitest';
import { CHIP_COLORS, pickChipColor } from '@site/src/components/chipColors';

function luminance(hex: string): number {
  const [r, g, b] = [1, 3, 5].map((i) => {
    const channel = parseInt(hex.slice(i, i + 2), 16) / 255;
    return channel <= 0.03928 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

describe('chip colors', () => {
  test.each(CHIP_COLORS)('%s keeps white label text at WCAG AA contrast', (color) => {
    const ratio = (1 + 0.05) / (luminance(color) + 0.05);
    expect(ratio).toBeGreaterThanOrEqual(4.5);
  });

  test('a chip keeps its color for the same text and position', () => {
    expect(pickChipColor('кіт', 2)).toBe(pickChipColor('кіт', 2));
    expect(CHIP_COLORS).toContain(pickChipColor('кіт', 2));
  });
});
