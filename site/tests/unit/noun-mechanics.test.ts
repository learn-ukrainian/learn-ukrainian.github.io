import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import {
  NOUN_MECHANICS_CATEGORY_KEYS,
  NOUN_MECHANICS_INTERFERENCE_KEYS,
  nounMechanicsFeedbackFor,
  type PracticeNounMechanicsCard,
  resolveAnimacyAccusativeRule,
  resolveInstrumentalSingularRule,
  resolveNounGenitiveRule,
  resolveNounVocativeRule,
} from '../../src/lib/lexicon/noun-mechanics';

describe('noun-mechanics', () => {
  it('resolves II declension Genitive endings accurately per § 82', () => {
    // Concrete being / item
    const concrete = resolveNounGenitiveRule(true);
    expect(concrete.ending).toBe('-а / -я');
    expect(concrete.ruleUa).toContain('істот');

    // Settlement / measure
    const settle = resolveNounGenitiveRule(false, true);
    expect(settle.ending).toBe('-а / -я');
    expect(settle.ruleUa).toContain('міста');

    // Mass substance / abstract concept / collective
    const mass = resolveNounGenitiveRule(false, false);
    expect(mass.ending).toBe('-у / -ю');
    expect(mass.ruleUa).toContain('речовини');
  });

  it('resolves Vocative endings accurately per §§ 73, 87', () => {
    // II declension hard stem -> -e with mutation
    const hard = resolveNounVocativeRule(2, 'hard');
    expect(hard.ending).toBe('-е');
    expect(hard.ruleUa).toContain('чергуванням');

    // II declension velar / diminutive -> -u
    const velar = resolveNounVocativeRule(2, 'hard', true);
    expect(velar.ending).toBe('-у');
    expect(velar.ruleUa).toContain('задньоязиковий');

    // II declension soft stem -> -yu
    const soft = resolveNounVocativeRule(2, 'soft');
    expect(soft.ending).toBe('-ю');
    expect(soft.ruleUa).toContain("м'якої групи");

    // I declension hard stem -> -o
    const decl1Hard = resolveNounVocativeRule(1, 'hard');
    expect(decl1Hard.ending).toBe('-о');
    expect(decl1Hard.ruleUa).toContain('I відміни твердої');

    // I declension soft affectionate -> -yu
    const decl1Aff = resolveNounVocativeRule(1, 'soft', false, true);
    expect(decl1Aff.ending).toBe('-ю');
    expect(decl1Aff.ruleUa).toContain('Пестливі');
  });

  it('resolves II declension Instrumental singular endings accurately per § 80', () => {
    // Hard stem -> -om
    expect(resolveInstrumentalSingularRule('hard').ending).toBe('-ом');

    // Mixed sibilant stem -> -em
    const sibilant = resolveInstrumentalSingularRule('mixed');
    expect(sibilant.ending).toBe('-ем');
    expect(sibilant.ruleUa).toContain('шиплячий');

    // Soft stem -> -em / -yem
    expect(resolveInstrumentalSingularRule('soft').ending).toBe('-ем / -єм');
  });

  it('resolves masculine Accusative animacy distinction', () => {
    const anim = resolveAnimacyAccusativeRule(true);
    expect(anim.caseForm).toContain('Родовий');
    expect(anim.ruleUa).toContain('істот');

    const inanim = resolveAnimacyAccusativeRule(false);
    expect(inanim.caseForm).toContain('Називний');
    expect(inanim.ruleUa).toContain('неістот');
  });

  it('produces targeted feedback for learner responses', () => {
    const sampleCard: PracticeNounMechanicsCard = {
      card_id: 'test_nizh_1',
      category: 'inst_ii_mixed_sibilant_em',
      cefr_level: 'A1',
      prompt_sentence: 'Мама нарізала хліб гострим ___.',
      blank_target: 'ножем',
      correct_answer: 'ножем',
      options: ['ножем', 'ножом', 'ніж', 'ножим'],
      distractors: [
        {
          text: 'ножом',
          interference_type: 'false_instrumental_om_for_sibilant',
          explanation: {
            ua: 'Основа на шиплячий вимагає -ем.',
            en: 'Sibilant stems require -em.',
          },
        },
        {
          text: 'ніж',
          interference_type: 'false_vocative_nominative',
          explanation: {
            ua: 'Називний замість орудного.',
            en: 'Nominative instead of instrumental.',
          },
        },
        {
          text: 'ножим',
          interference_type: 'false_instrumental_im_for_noun',
          explanation: {
            ua: 'Помилкове прикметникове закінчення.',
            en: 'Adjective ending.',
          },
        },
      ],
      pravopys_section: '§ 80',
      rule_summary: {
        ua: 'Основа на шиплячий приймає -ем.',
        en: 'Sibilant stems take -em.',
      },
    };

    // Correct selection
    const correctRes = nounMechanicsFeedbackFor(sampleCard, 'ножем', 'ua');
    expect(correctRes.isCorrect).toBe(true);
    expect(correctRes.feedback).toContain('Правильно');

    // Distractor selection
    const distRes = nounMechanicsFeedbackFor(sampleCard, 'ножом', 'ua');
    expect(distRes.isCorrect).toBe(false);
    expect(distRes.feedback).toBe('Основа на шиплячий вимагає -ем.');

    // Fallback unknown selection
    const fallbackRes = nounMechanicsFeedbackFor(sampleCard, 'ножа', 'en');
    expect(fallbackRes.isCorrect).toBe(false);
    expect(fallbackRes.feedback).toContain('Incorrect');
  });

  it('validates committed noun mechanics deck parity and type adherence', () => {
    const candidates = [
      resolve(__dirname, '../../../data/practice/noun_mechanics_deck.json'),
      resolve(process.cwd(), '../data/practice/noun_mechanics_deck.json'),
      resolve(process.cwd(), 'data/practice/noun_mechanics_deck.json'),
    ];
    const deckPath = candidates.find((p) => existsSync(p));
    expect(deckPath).toBeDefined();

    const raw = readFileSync(deckPath!, 'utf-8');
    const parsed = JSON.parse(raw);

    expect(parsed.version).toBe('1.0.0');
    expect(parsed.card_count).toBeGreaterThanOrEqual(50);
    expect(parsed.cards).toHaveLength(parsed.card_count);

    const validCategories = new Set<string>(NOUN_MECHANICS_CATEGORY_KEYS);
    const validInterferences = new Set<string>(NOUN_MECHANICS_INTERFERENCE_KEYS);

    for (const card of parsed.cards as PracticeNounMechanicsCard[]) {
      expect(validCategories.has(card.category)).toBe(true);
      expect(card.options).toHaveLength(4);
      expect(card.distractors).toHaveLength(3);
      expect(card.options).toContain(card.correct_answer);

      for (const distractor of card.distractors) {
        expect(validInterferences.has(distractor.interference_type)).toBe(true);
        expect(distractor.explanation.ua).toBeTruthy();
        expect(distractor.explanation.en).toBeTruthy();
      }
    }
  });
});
