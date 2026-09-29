/** Display-only labels for teacher-deck choices; artifact text stays intact. */
export function teacherOptionDisplay(label: string, lang: 'en' | 'uk'): string {
  const sense = lang === 'en' ? label.split(/[,;]|\s+\/\s+/, 1)[0]! : label;
  const plain = sense.trim()
    .replace(/[.!?;:,…]+$/u, '')
    .replace(/\s*\([^)]*\)$/u, '')
    .trim();
  // Stress belongs in the dedicated stress exercise, not as a clue in other choices.
  const display = (lang === 'uk' ? plain.replace(/\u0301/g, '') : plain).toLocaleLowerCase(lang);
  return lang === 'en' ? display.replace(/^to\s+/u, '') : display;
}
