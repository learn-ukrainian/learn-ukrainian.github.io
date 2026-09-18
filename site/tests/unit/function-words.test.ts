import { describe, expect, it } from 'vitest';
import {
  functionWordFeedbackFor,
  type PracticeFunctionWordCard,
  resolveCausalPrepositionRule,
  resolveConjunctionHomophoneRule,
  resolveDurationPrepositionRule,
  resolveParticleHyphenationRule,
  resolveParticleNeRule,
  resolvePrepositionHyphenationRule,
} from '../../src/lib/lexicon/function-words';

describe('function-words', () => {
  it('resolves preposition hyphenation accurately', () => {
    // Initial з-/із- prepositions must be hyphenated
    expect(resolvePrepositionHyphenationRule('з-під').requiresHyphen).toBe(true);
    expect(resolvePrepositionHyphenationRule('з-за').requiresHyphen).toBe(true);
    expect(resolvePrepositionHyphenationRule('із-за').requiresHyphen).toBe(true);
    expect(resolvePrepositionHyphenationRule('з-поміж').requiresHyphen).toBe(true);
    expect(resolvePrepositionHyphenationRule('з-понад').requiresHyphen).toBe(true);

    // Other compound prepositions are solid
    expect(resolvePrepositionHyphenationRule('посеред').requiresHyphen).toBe(false);
    expect(resolvePrepositionHyphenationRule('задля').requiresHyphen).toBe(false);
    expect(resolvePrepositionHyphenationRule('заради').requiresHyphen).toBe(false);
    expect(resolvePrepositionHyphenationRule('внаслідок').requiresHyphen).toBe(false);
    expect(resolvePrepositionHyphenationRule('напередодні').requiresHyphen).toBe(false);
  });

  it('resolves causal government (завдяки vs через) by semantic polarity', () => {
    // Favorable / positive cause -> завдяки
    const pos = resolveCausalPrepositionRule(true);
    expect(pos.choice).toBe('завдяки');
    expect(pos.ruleUa).toContain('позитивних');

    // Adverse / negative cause -> через
    const neg = resolveCausalPrepositionRule(false);
    expect(neg.choice).toBe('через');
    expect(neg.ruleUa).toContain('небажаних');
  });

  it('resolves duration (протягом) vs literal draft (на протязі)', () => {
    expect(resolveDurationPrepositionRule(true).choice).toBe('протягом');
    expect(resolveDurationPrepositionRule(false).choice).toBe('на протязі');
  });

  it('resolves conjunction homophones (§ 43)', () => {
    // проте vs про те
    expect(resolveConjunctionHomophoneRule('проте', true).choice).toBe('проте');
    expect(resolveConjunctionHomophoneRule('проте', false).choice).toBe('про те');

    // зате vs за те
    expect(resolveConjunctionHomophoneRule('зате', true).choice).toBe('зате');
    expect(resolveConjunctionHomophoneRule('зате', false).choice).toBe('за те');

    // щоб vs що б
    expect(resolveConjunctionHomophoneRule('щоб', true).choice).toBe('щоб');
    expect(resolveConjunctionHomophoneRule('щоб', false).choice).toBe('що б');

    // якби vs як би
    expect(resolveConjunctionHomophoneRule('якби', true).choice).toBe('якби');
    expect(resolveConjunctionHomophoneRule('якби', false).choice).toBe('як би');

    // якщо vs як що
    expect(resolveConjunctionHomophoneRule('якщо', true).choice).toBe('якщо');
    expect(resolveConjunctionHomophoneRule('якщо', false).choice).toBe('як що');

    // також vs так же
    expect(resolveConjunctionHomophoneRule('також', true).choice).toBe('також');
    expect(resolveConjunctionHomophoneRule('також', false).choice).toBe('так же');

    // теж vs те ж
    expect(resolveConjunctionHomophoneRule('теж', true).choice).toBe('теж');
    expect(resolveConjunctionHomophoneRule('теж', false).choice).toBe('те ж');

    expect(() => resolveConjunctionHomophoneRule('невідомий', true)).toThrowError();
  });

  it('resolves particle не orthography (§ 44, п. 1)', () => {
    // Bound root verbs -> разом
    expect(
      resolveParticleNeRule({ pos: 'verb', cannotStandWithoutNe: true }).orthography,
    ).toBe('разом');

    // Regular verbs -> окремо
    expect(resolveParticleNeRule({ pos: 'verb' }).orthography).toBe('окремо');
    expect(resolveParticleNeRule({ pos: 'gerund' }).orthography).toBe('окремо');

    // Contrast with 'а' -> окремо
    expect(resolveParticleNeRule({ pos: 'noun', hasContrast: true }).orthography).toBe('окремо');
    expect(resolveParticleNeRule({ pos: 'adj', hasContrast: true }).orthography).toBe('окремо');

    // New concepts -> разом
    expect(resolveParticleNeRule({ pos: 'noun', formsNewConcept: true }).orthography).toBe('разом');
    expect(resolveParticleNeRule({ pos: 'adj', formsNewConcept: true }).orthography).toBe('разом');
    expect(resolveParticleNeRule({ pos: 'adv', formsNewConcept: true }).orthography).toBe('разом');

    // Participles: isolated (разом) vs with dependents (окремо)
    expect(resolveParticleNeRule({ pos: 'participle', hasDependentWords: false }).orthography).toBe(
      'разом',
    );
    expect(resolveParticleNeRule({ pos: 'participle', hasDependentWords: true }).orthography).toBe(
      'окремо',
    );
  });

  it('resolves particle hyphenation and split by preposition (§ 44, п. 2)', () => {
    // Enclitics -бо, -но, -то, -от
    expect(resolveParticleHyphenationRule({ particle: 'бо' }).orthography).toBe('дефіс');
    expect(resolveParticleHyphenationRule({ particle: 'но' }).orthography).toBe('дефіс');
    expect(resolveParticleHyphenationRule({ particle: 'то' }).orthography).toBe('дефіс');
    expect(resolveParticleHyphenationRule({ particle: 'от' }).orthography).toBe('дефіс');

    // Таки: postpositive (дефіс) vs prepositive (окремо)
    expect(
      resolveParticleHyphenationRule({ particle: 'таки', positionAfterWord: true }).orthography,
    ).toBe('дефіс');
    expect(
      resolveParticleHyphenationRule({ particle: 'таки', positionAfterWord: false }).orthography,
    ).toBe('окремо');

    // Будь-, хтозна-, казна-: direct (дефіс) vs split (окремо)
    expect(
      resolveParticleHyphenationRule({ particle: 'будь', hasInterveningPreposition: false })
        .orthography,
    ).toBe('дефіс');
    expect(
      resolveParticleHyphenationRule({ particle: 'хтозна', hasInterveningPreposition: false })
        .orthography,
    ).toBe('дефіс');
    expect(
      resolveParticleHyphenationRule({ particle: 'будь', hasInterveningPreposition: true })
        .orthography,
    ).toBe('окремо');
    expect(
      resolveParticleHyphenationRule({ particle: 'хтозна', hasInterveningPreposition: true })
        .orthography,
    ).toBe('окремо');
  });

  it('provides targeted feedback for correct and distractor choices', () => {
    const card: PracticeFunctionWordCard = {
      id: 'prep_hyphen_z_pid_1',
      category: 'preposition_hyphenated',
      cefrLevel: 'A2',
      prompt: 'Кошеня визирнуло _______ дивана й злякано нявкнуло.',
      fullSentence: 'Кошеня визирнуло з-під дивана й злякано нявкнуло.',
      sentenceBefore: 'Кошеня визирнуло',
      sentenceAfter: 'дивана й злякано нявкнуло.',
      correctAnswer: 'з-під',
      options: ['з-під', 'зпід', 'з під', 'із під'],
      distractors: [
        {
          form: 'зпід',
          interferenceType: 'missing_hyphen_preposition',
          explanationUa: 'Складні прийменники з «з-» пишуться через дефіс.',
          explanationEn: 'Compound prepositions with z- are hyphenated.',
        },
      ],
      ruleCitation: 'Правопис 2019, § 42, п. 1',
      ruleSummary: {
        uk: 'Складні прийменники з «з-» пишуться через дефіс: з-під, з-за.',
        en: 'Compound prepositions with z- are hyphenated.',
      },
    };

    const correctRes = functionWordFeedbackFor(card, 'з-під');
    expect(correctRes.isCorrect).toBe(true);
    expect(correctRes.explanationUa).toContain('Правильно!');

    const distractorRes = functionWordFeedbackFor(card, 'зпід');
    expect(distractorRes.isCorrect).toBe(false);
    expect(distractorRes.interferenceType).toBe('missing_hyphen_preposition');
    expect(distractorRes.explanationUa).toContain('дефіс');

    const unknownRes = functionWordFeedbackFor(card, 'інше');
    expect(unknownRes.isCorrect).toBe(false);
    expect(unknownRes.explanationUa).toContain('Неправильно.');
  });
});
