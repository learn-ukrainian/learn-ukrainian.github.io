/**
 * Background colors for option chips and tiles. Their label is always white, so
 * every entry keeps a contrast ratio of at least 4.5:1 against #FFFFFF (WCAG AA).
 */
export const CHIP_COLORS = [
  '#C62828',
  '#C2185B',
  '#7B1FA2',
  '#512DA8',
  '#303F9F',
  '#1565C0',
  '#0277BD',
  '#00838F',
  '#00796B',
  '#2E7D32',
  '#33691E',
  '#BF360C',
  '#B23C17',
  '#6D4C41',
];

/** Stable color for a chip: the same text and position always get the same color. */
export function pickChipColor(text: string, index: number): string {
  const charSum = text.split('').reduce((sum, char) => sum + char.charCodeAt(0), 0);
  return CHIP_COLORS[(charSum + index) % CHIP_COLORS.length];
}
