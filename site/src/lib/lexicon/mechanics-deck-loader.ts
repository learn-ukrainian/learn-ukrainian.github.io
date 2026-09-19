import {
  nounMechanicsFeedbackFor,
  type PracticeNounMechanicsCard,
} from './noun-mechanics';
import {
  adjectiveMechanicsFeedbackFor,
  type PracticeAdjectiveMechanicsCard,
} from './adjective-mechanics';
import {
  verbMechanicsFeedbackFor,
  type PracticeVerbMechanicsCard,
} from './verb-mechanics';
import {
  pronounMechanicsFeedbackFor,
  type PracticePronounMechanicsCard,
} from './pronoun-mechanics';
import {
  numeralMechanicsFeedbackFor,
  type PracticeNumeralMechanicsCard,
} from './numeral-mechanics';
import {
  adverbMechanicsFeedbackFor,
  type PracticeAdverbMechanicsCard,
} from './adverb-mechanics';
import {
  functionWordFeedbackFor,
  type PracticeFunctionWordCard,
} from './function-words';
import {
  interjectionMechanicsFeedbackFor,
  type PracticeInterjectionMechanicsCard,
} from './interjection-mechanics';

export type MechanicsPosKey =
  | 'noun'
  | 'adjective'
  | 'verb'
  | 'pronoun'
  | 'numeral'
  | 'adverb'
  | 'function_words'
  | 'interjection';

export const ALL_MECHANICS_POS_KEYS: MechanicsPosKey[] = [
  'noun',
  'adjective',
  'verb',
  'pronoun',
  'numeral',
  'adverb',
  'function_words',
  'interjection',
];

export interface NormalizedMechanicsCard {
  id: string;
  pos: MechanicsPosKey;
  category: string;
  cefrLevel: string;
  prompt: string;
  options: string[];
  correctAnswer: string;
  ruleCitation: string;
  ruleSummary: { uk: string; en: string };
  evaluate: (selectedOption: string, locale?: 'uk' | 'en') => {
    isCorrect: boolean;
    feedback: string;
    ruleCitation: string;
    ruleSummary: string;
  };
}

export interface MechanicsDeckMeta {
  pos: MechanicsPosKey;
  titleUk: string;
  titleEn: string;
  descriptionUk: string;
  descriptionEn: string;
  itemCount: number;
  accent: 'blue' | 'teal' | 'purple' | 'orange';
}

export const MECHANICS_DECK_META: Record<MechanicsPosKey, MechanicsDeckMeta> = {
  noun: {
    pos: 'noun',
    titleUk: 'Іменник',
    titleEn: 'Noun',
    descriptionUk: 'Закінчення -а/-у в родовому, кличний відмінок, чергування в орудному',
    descriptionEn: 'Genitive -а/-у endings, vocative case, instrumental mutations',
    itemCount: 75,
    accent: 'purple',
  },
  adjective: {
    pos: 'adjective',
    titleUk: 'Прикметник',
    titleEn: 'Adjective',
    descriptionUk: 'Ступені порівняння, тверда/м’яка групи, присвійні суфікси',
    descriptionEn: 'Degrees of comparison, hard/soft groups, possessive suffixes',
    itemCount: 65,
    accent: 'teal',
  },
  verb: {
    pos: 'verb',
    titleUk: 'Дієслово',
    titleEn: 'Verb',
    descriptionUk: 'I та II дієвідміни, видові пари, наказовий спосіб, дієприкметники',
    descriptionEn: 'I & II conjugations, aspectual pairs, imperatives, participles',
    itemCount: 80,
    accent: 'blue',
  },
  pronoun: {
    pos: 'pronoun',
    titleUk: 'Займенник',
    titleEn: 'Pronoun',
    descriptionUk: 'Приставний н- з прийменниками, правопис неозначених та заперечних',
    descriptionEn: 'Epenthetic n- with prepositions, indefinite & negative spelling',
    itemCount: 60,
    accent: 'orange',
  },
  numeral: {
    pos: 'numeral',
    titleUk: 'Числівник',
    titleEn: 'Numeral',
    descriptionUk: 'Відмінювання 50–80, 200–900, узгодження 2/3/4 vs 5+ з іменниками',
    descriptionEn: 'Declension of 50–80, 200–900, government 2/3/4 vs 5+ with nouns',
    itemCount: 60,
    accent: 'purple',
  },
  adverb: {
    pos: 'adverb',
    titleUk: 'Прислівник',
    titleEn: 'Adverb',
    descriptionUk: 'Правопис разом, окремо, через дефіс, ступені порівняння',
    descriptionEn: 'Spelling solid, separate, hyphenated, degrees of comparison',
    itemCount: 75,
    accent: 'teal',
  },
  function_words: {
    pos: 'function_words',
    titleUk: 'Службові слова',
    titleEn: 'Function Words',
    descriptionUk: 'Складні прийменники, правопис сполучників проте/зате, частки не/ні, -бо, -но',
    descriptionEn: 'Compound prepositions, conjunctions проте/зате, particles не/ні, -бо, -но',
    itemCount: 42,
    accent: 'blue',
  },
  interjection: {
    pos: 'interjection',
    titleUk: 'Вигук',
    titleEn: 'Interjection',
    descriptionUk: 'Емоційні, спонукальні, етикетні формули, звуконаслідування та пунктуація',
    descriptionEn: 'Emotional, volitional, etiquette formulas, onomatopoeia & punctuation',
    itemCount: 60,
    accent: 'orange',
  },
};

const MECHANICS_LOADERS: Record<MechanicsPosKey, () => Promise<{ default: any }>> = {
  noun: () => import('../../data/practice-mechanics/noun_mechanics_deck.json'),
  adjective: () => import('../../data/practice-mechanics/adjective_mechanics_deck.json'),
  verb: () => import('../../data/practice-mechanics/verb_mechanics_deck.json'),
  pronoun: () => import('../../data/practice-mechanics/pronoun_mechanics_deck.json'),
  numeral: () => import('../../data/practice-mechanics/numeral_mechanics_deck.json'),
  adverb: () => import('../../data/practice-mechanics/adverb_mechanics_deck.json'),
  function_words: () => import('../../data/practice-mechanics/function_words_deck.json'),
  interjection: () => import('../../data/practice-mechanics/interjection_mechanics_deck.json'),
};

export async function loadMechanicsDeck(pos: MechanicsPosKey): Promise<NormalizedMechanicsCard[]> {
  const loader = MECHANICS_LOADERS[pos];
  if (!loader) return [];
  const mod = await loader();
  const raw = mod.default;
  const rawCards: any[] = raw.cards ?? [];

  return rawCards.map((c: any): NormalizedMechanicsCard => {
    switch (pos) {
      case 'noun': {
        const card = c as PracticeNounMechanicsCard;
        return {
          id: card.card_id,
          pos,
          category: card.category,
          cefrLevel: card.cefr_level,
          prompt: card.prompt_sentence,
          options: card.options,
          correctAnswer: card.correct_answer,
          ruleCitation: card.pravopys_section,
          ruleSummary: { uk: card.rule_summary.ua, en: card.rule_summary.en },
          evaluate: (opt, locale = 'uk') => {
            const loc = locale === 'uk' ? 'ua' : 'en';
            const res = nounMechanicsFeedbackFor(card, opt, loc);
            return {
              isCorrect: res.isCorrect,
              feedback: res.feedback,
              ruleCitation: res.pravopysSection,
              ruleSummary: res.ruleSummary,
            };
          },
        };
      }
      case 'adjective': {
        const card = c as PracticeAdjectiveMechanicsCard;
        return {
          id: card.card_id,
          pos,
          category: card.category,
          cefrLevel: card.cefr_level,
          prompt: card.prompt_sentence,
          options: card.options,
          correctAnswer: card.correct_answer,
          ruleCitation: card.pravopys_section,
          ruleSummary: { uk: card.rule_summary.ua, en: card.rule_summary.en },
          evaluate: (opt, locale = 'uk') => {
            const loc = locale === 'uk' ? 'ua' : 'en';
            const res = adjectiveMechanicsFeedbackFor(card, opt, loc);
            return {
              isCorrect: res.isCorrect,
              feedback: res.feedback,
              ruleCitation: res.pravopysSection,
              ruleSummary: res.ruleSummary,
            };
          },
        };
      }
      case 'verb': {
        const card = c as PracticeVerbMechanicsCard;
        return {
          id: card.card_id,
          pos,
          category: card.category,
          cefrLevel: card.cefr_level,
          prompt: card.prompt_sentence,
          options: card.options,
          correctAnswer: card.correct_answer,
          ruleCitation: card.pravopys_section,
          ruleSummary: { uk: card.rule_summary.ua, en: card.rule_summary.en },
          evaluate: (opt, locale = 'uk') => {
            const loc = locale === 'uk' ? 'ua' : 'en';
            const res = verbMechanicsFeedbackFor(card, opt, loc);
            return {
              isCorrect: res.isCorrect,
              feedback: res.feedback,
              ruleCitation: res.pravopysSection,
              ruleSummary: res.ruleSummary,
            };
          },
        };
      }
      case 'pronoun': {
        const card = c as PracticePronounMechanicsCard;
        const ruleUk = card.rule_summary?.ua ?? (card as any).ruleSummary?.uk ?? '';
        const ruleEn = card.rule_summary?.en ?? (card as any).ruleSummary?.en ?? '';
        const citation = card.pravopys_section ?? (card as any).ruleCitation ?? '';
        return {
          id: card.card_id ?? (card as any).id,
          pos,
          category: card.category,
          cefrLevel: card.cefr_level ?? (card as any).cefrLevel,
          prompt: card.prompt_sentence ?? (card as any).prompt,
          options: card.options,
          correctAnswer: card.correct_answer ?? (card as any).correctAnswer,
          ruleCitation: citation,
          ruleSummary: { uk: ruleUk, en: ruleEn },
          evaluate: (opt, locale = 'uk') => {
            const loc = locale === 'uk' ? 'ua' : 'en';
            const res = pronounMechanicsFeedbackFor(card, opt, loc);
            return {
              isCorrect: res.isCorrect,
              feedback: res.feedback,
              ruleCitation: res.ruleCitation,
              ruleSummary: res.ruleSummary,
            };
          },
        };
      }
      case 'numeral': {
        const card = c as PracticeNumeralMechanicsCard;
        return {
          id: card.card_id,
          pos,
          category: card.category,
          cefrLevel: card.cefr_level,
          prompt: card.prompt_sentence,
          options: card.options,
          correctAnswer: card.correct_answer,
          ruleCitation: card.pravopys_section,
          ruleSummary: { uk: card.rule_summary.ua, en: card.rule_summary.en },
          evaluate: (opt, locale = 'uk') => {
            const res = numeralMechanicsFeedbackFor(card, opt);
            return {
              isCorrect: res.isCorrect,
              feedback: locale === 'uk' ? res.feedbackUa : res.feedbackEn,
              ruleCitation: res.ruleCitation,
              ruleSummary: locale === 'uk' ? card.rule_summary.ua : card.rule_summary.en,
            };
          },
        };
      }
      case 'adverb': {
        const card = c as PracticeAdverbMechanicsCard;
        const prompt = card.prompt.replace(/_{3,}/g, '___');
        return {
          id: card.id,
          pos,
          category: card.category,
          cefrLevel: (card as any).cefr_level ?? 'B1',
          prompt,
          options: card.options,
          correctAnswer: card.correct_answer,
          ruleCitation: card.rule_citation,
          ruleSummary: { uk: card.rule_summary.ua, en: card.rule_summary.en },
          evaluate: (opt, locale = 'uk') => {
            const res = adverbMechanicsFeedbackFor(card, opt);
            return {
              isCorrect: res.isCorrect,
              feedback: locale === 'uk' ? res.feedbackUa : res.feedbackEn,
              ruleCitation: res.ruleCitation,
              ruleSummary: locale === 'uk' ? card.rule_summary.ua : card.rule_summary.en,
            };
          },
        };
      }
      case 'function_words': {
        const card = c as PracticeFunctionWordCard;
        return {
          id: card.id,
          pos,
          category: card.category,
          cefrLevel: card.cefrLevel,
          prompt: card.prompt,
          options: card.options,
          correctAnswer: card.correctAnswer,
          ruleCitation: card.ruleCitation,
          ruleSummary: { uk: card.ruleSummary.uk, en: card.ruleSummary.en },
          evaluate: (opt, locale = 'uk') => {
            const res = functionWordFeedbackFor(card, opt);
            return {
              isCorrect: res.isCorrect,
              feedback: locale === 'uk' ? res.explanationUa : res.explanationEn,
              ruleCitation: res.ruleCitation,
              ruleSummary: locale === 'uk' ? res.ruleUa : res.ruleEn,
            };
          },
        };
      }
      case 'interjection': {
        const card = c as PracticeInterjectionMechanicsCard;
        const prompt = card.prompt.replace(/_{3,}/g, '___');
        return {
          id: card.id,
          pos,
          category: card.category,
          cefrLevel: (card as any).cefr_level ?? 'B1',
          prompt,
          options: card.options,
          correctAnswer: card.correct_answer,
          ruleCitation: card.rule_citation ?? (card as any).pravopys_section ?? '',
          ruleSummary: { uk: card.rule_summary.ua, en: card.rule_summary.en },
          evaluate: (opt, locale = 'uk') => {
            const res = interjectionMechanicsFeedbackFor(card, opt);
            return {
              isCorrect: res.isCorrect,
              feedback: locale === 'uk' ? res.feedbackUa : res.feedbackEn,
              ruleCitation: res.ruleCitation,
              ruleSummary: locale === 'uk' ? card.rule_summary.ua : card.rule_summary.en,
            };
          },
        };
      }
      default: {
        throw new Error(`Unsupported mechanics pos key: ${pos}`);
      }
    }
  });
}
