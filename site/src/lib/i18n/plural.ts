/**
 * Pluralization helper for Ukrainian count-noun agreement.
 * Standard rules:
 * - 'one' (ends in 1, except 11) -> singular nominative (e.g. «1 форма»)
 * - 'few' (ends in 2-4, except 12-14) -> plural nominative/paucal (e.g. «2 форми»)
 * - 'many' / other (everything else: 0, 5-9, 11-14) -> genitive plural (e.g. «5 форм»)
 */
export function pluralizeUk(n: number, forms: [string, string, string]): string {
  const rules = new Intl.PluralRules('uk-UA');
  const rule = rules.select(n);
  switch (rule) {
    case 'one':
      return forms[0];
    case 'few':
      return forms[1];
    case 'many':
    case 'other':
    default:
      return forms[2];
  }
}
