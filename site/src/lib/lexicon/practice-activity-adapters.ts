import type { ErrorCorrectionItemProps } from '../../components/ErrorCorrection';
import type { FillInQuestionProps } from '../../components/FillIn';
import type { MatchPair } from '../../components/MatchUp';
import type { MarkTheWordsActivityProps } from '../../components/MarkTheWords';
import type { UnjumbleQuestionProps } from '../../components/Unjumble';
import { seededPracticeHash, type PracticeHeritageItem } from './srs';

export type HeritagePracticePresentation =
  | { kind: 'mc' }
  | { kind: 'error-correction'; item: HeritageErrorCorrectionItem }
  | { kind: 'unjumble'; item: HeritageUnjumbleQuestion }
  | { kind: 'fill-in'; item: HeritageFillInQuestion }
  | { kind: 'match-up'; item: HeritageMatchUpQuestion }
  | { kind: 'mark-the-words'; item: HeritageMarkTheWordsQuestion };

export type HeritageErrorCorrectionItem = Pick<
  ErrorCorrectionItemProps,
  'sentence' | 'errorWord' | 'correctForm' | 'options' | 'explanation'
>;

export type HeritageUnjumbleQuestion = Pick<
  UnjumbleQuestionProps,
  'words' | 'answer' | 'hint' | 'wordsAreJumbled'
>;

export type HeritageFillInQuestion = Pick<FillInQuestionProps, 'sentence' | 'answer' | 'options'>;

export type HeritageMatchUpQuestion = {
  pairs: MatchPair[];
};

export type HeritageMarkTheWordsQuestion = Pick<
  MarkTheWordsActivityProps,
  'text' | 'correctWords' | 'instruction'
>;

const BLANK = '___';
const CONTENT_TOKEN = /[\p{L}\p{N}]/u;

function fillSingleBlank(prompt: string, replacement: string): string | null {
  if (!prompt || !replacement) return null;
  const firstBlank = prompt.indexOf(BLANK);
  if (firstBlank < 0 || prompt.indexOf(BLANK, firstBlank + BLANK.length) >= 0) return null;
  return `${prompt.slice(0, firstBlank)}${replacement}${prompt.slice(firstBlank + BLANK.length)}`.trim();
}

function contentWords(text: string): string[] {
  return text.match(/[\p{L}\p{M}\p{N}’'-]+/gu) ?? [];
}

function appearsExactlyOnce(sentence: string, phrase: string): boolean {
  const sentenceWords = contentWords(sentence).map((word) => word.toLocaleLowerCase());
  const phraseWords = contentWords(phrase).map((word) => word.toLocaleLowerCase());
  if (phraseWords.length === 0 || phraseWords.length > sentenceWords.length) return false;

  let matches = 0;
  for (let start = 0; start <= sentenceWords.length - phraseWords.length; start += 1) {
    if (phraseWords.every((word, index) => sentenceWords[start + index] === word)) matches += 1;
  }
  return matches === 1;
}

function targetWordsAppearExactlyOnce(sentence: string, targetWords: readonly string[]): boolean {
  const sentenceWords = contentWords(sentence).map((word) => word.toLocaleLowerCase());
  const targets = targetWords.map((word) => word.toLocaleLowerCase());
  return (
    new Set(targets).size === targets.length &&
    targets.every((target) => sentenceWords.filter((word) => word === target).length === 1)
  );
}

function sourceOptions(item: PracticeHeritageItem): string[] | null {
  const options = Array.from(
    new Set(item.options.map((option) => option.label.trim()).filter(Boolean)),
  );
  return options.includes(item.answer) ? options : null;
}

function heritageMatchPair(item: PracticeHeritageItem): MatchPair | null {
  const options = sourceOptions(item);
  const left = item.calque.trim();
  const right = item.answer.trim();
  if (!options || !left || !right || left.toLocaleLowerCase() === right.toLocaleLowerCase())
    return null;
  return { left, right, lemmaId: item.lemmaId };
}

function correctSentenceTokens(item: PracticeHeritageItem): string[] | null {
  const sentence = fillSingleBlank(item.prompt, item.answer);
  if (!sentence) return null;
  const tokens = sentence.split(/\s+/).filter((token) => CONTENT_TOKEN.test(token));
  return tokens.length >= 4 ? tokens : null;
}

function jumbledTokens(
  tokens: readonly string[],
  seed: number,
  item: PracticeHeritageItem,
): string[] {
  const result = [...tokens];
  let state = seededPracticeHash(seed, `heritage-unjumble:${item.srsKey}`) || 1;
  for (let index = result.length - 1; index > 0; index -= 1) {
    state = (state * 1664525 + 1013904223) >>> 0;
    const target = state % (index + 1);
    [result[index], result[target]] = [result[target], result[index]];
  }
  if (result.every((token, index) => token === tokens[index]) && result.length > 1) {
    result.push(result.shift()!);
  }
  return result;
}

/**
 * Adapts only unambiguous, source-backed heritage frames. Frames with multiple
 * blanks, missing source choices, or repeated calque spans stay in heritage MC.
 */
export function heritageToErrorCorrection(
  item: PracticeHeritageItem,
): HeritageErrorCorrectionItem | null {
  const sentence = fillSingleBlank(item.prompt, item.calque);
  const options = sourceOptions(item);
  if (!sentence || !options || !item.calque.trim() || !item.answer.trim()) return null;
  if (contentWords(item.calque).length !== 1) return null;
  if (!appearsExactlyOnce(sentence, item.calque)) return null;
  return {
    sentence,
    errorWord: item.calque,
    correctForm: item.answer,
    options,
    explanation: item.rationaleUk || item.rationale,
  };
}

/**
 * Retains source token spelling and punctuation while excluding standalone
 * punctuation noise. Four content tokens keeps this a sentence-building task.
 */
export function heritageToUnjumble(
  item: PracticeHeritageItem,
  sessionSeed: number,
): HeritageUnjumbleQuestion | null {
  const tokens = correctSentenceTokens(item);
  if (!tokens) return null;
  return {
    words: jumbledTokens(tokens, sessionSeed, item).join(' / '),
    answer: tokens.join(' '),
    hint: item.rationaleUk || item.rationale,
    wordsAreJumbled: true,
  };
}

/**
 * Keeps the reviewed blank and its original answer bank intact. The component
 * supports typing, but Practice only offers chips when the reviewed source
 * supplied them, rather than manufacturing distractors.
 */
export function heritageToFillIn(item: PracticeHeritageItem): HeritageFillInQuestion | null {
  const options = sourceOptions(item);
  if (!fillSingleBlank(item.prompt, item.answer) || !options) return null;
  return {
    sentence: item.prompt,
    answer: item.answer,
    options,
  };
}

/**
 * A marked target must be the one reviewed correction span in its corrected
 * frame. Repeated targets are rejected so the learner never has to infer which
 * occurrence a source record meant.
 */
export function heritageToMarkTheWords(
  item: PracticeHeritageItem,
): HeritageMarkTheWordsQuestion | null {
  const options = sourceOptions(item);
  const text = fillSingleBlank(item.prompt, item.answer);
  const correctWords = contentWords(item.answer);
  if (
    !options ||
    !text ||
    correctWords.length === 0 ||
    !appearsExactlyOnce(text, item.answer) ||
    !targetWordsAppearExactlyOnce(text, correctWords)
  )
    return null;
  return {
    text,
    correctWords,
    instruction: 'Позначте питоме українське слово або сполуку.',
  };
}

/**
 * A board is made from reviewed calque-to-correction relations only. It always
 * includes the scheduled card, caps density at four pairs, and fails closed
 * unless at least two unique source pairs can be shown.
 */
export function heritageToMatchUp(
  item: PracticeHeritageItem,
  availableItems: readonly PracticeHeritageItem[],
  sessionSeed: number,
): HeritageMatchUpQuestion | null {
  const primary = heritageMatchPair(item);
  if (!primary) return null;

  const pairs = [primary];
  const seenLeft = new Set([primary.left.toLocaleLowerCase()]);
  const seenRight = new Set([primary.right.toLocaleLowerCase()]);
  const start =
    seededPracticeHash(sessionSeed, `heritage-match-up:${item.srsKey}`) %
    Math.max(availableItems.length, 1);

  for (let offset = 0; offset < availableItems.length && pairs.length < 4; offset += 1) {
    const candidate = availableItems[(start + offset) % availableItems.length];
    if (!candidate || candidate.heritageId === item.heritageId) continue;
    const pair = heritageMatchPair(candidate);
    if (!pair) continue;
    const left = pair.left.toLocaleLowerCase();
    const right = pair.right.toLocaleLowerCase();
    if (seenLeft.has(left) || seenRight.has(right)) continue;
    pairs.push(pair);
    seenLeft.add(left);
    seenRight.add(right);
  }

  return pairs.length >= 2 ? { pairs } : null;
}

/**
 * A presentation is derived from the persisted session seed, so a resumed card
 * keeps its interaction while sharing the untouched heritage card key and SRS state.
 */
export function selectHeritagePracticePresentation(
  item: PracticeHeritageItem,
  sessionSeed: number,
  availableItems: readonly PracticeHeritageItem[] = [],
): HeritagePracticePresentation {
  const presentations: HeritagePracticePresentation[] = [{ kind: 'mc' }];
  const errorCorrection = heritageToErrorCorrection(item);
  if (errorCorrection) presentations.push({ kind: 'error-correction', item: errorCorrection });
  const unjumble = heritageToUnjumble(item, sessionSeed);
  if (unjumble) presentations.push({ kind: 'unjumble', item: unjumble });
  const fillIn = heritageToFillIn(item);
  if (fillIn) presentations.push({ kind: 'fill-in', item: fillIn });
  const matchUp = heritageToMatchUp(item, availableItems, sessionSeed);
  if (matchUp) presentations.push({ kind: 'match-up', item: matchUp });
  const markTheWords = heritageToMarkTheWords(item);
  if (markTheWords) presentations.push({ kind: 'mark-the-words', item: markTheWords });
  return presentations[
    seededPracticeHash(sessionSeed, `heritage-presentation:${item.srsKey}`) % presentations.length
  ];
}
