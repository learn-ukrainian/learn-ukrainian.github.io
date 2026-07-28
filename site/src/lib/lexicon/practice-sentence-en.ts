/**
 * Returns displayable English practice-sentence text, excluding generator
 * placeholders that are not learner-facing translations.
 */
export function usablePracticeSentenceEnglish(value: string | null | undefined): string | null {
  const sentence = value?.trim();
  if (!sentence || /^context sentence for\b/i.test(sentence)) return null;
  return sentence;
}
