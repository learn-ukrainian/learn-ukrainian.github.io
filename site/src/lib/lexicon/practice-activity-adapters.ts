import type { ErrorCorrectionItemProps } from '../../components/ErrorCorrection';
import type { UnjumbleQuestionProps } from '../../components/Unjumble';
import { seededPracticeHash, type PracticeHeritageItem } from './srs';

export type HeritagePracticePresentation =
  | { kind: 'mc' }
  | { kind: 'error-correction'; item: HeritageErrorCorrectionItem }
  | { kind: 'unjumble'; item: HeritageUnjumbleQuestion };

export type HeritageErrorCorrectionItem = Pick<
  ErrorCorrectionItemProps,
  'sentence' | 'errorWord' | 'correctForm' | 'options' | 'explanation'
>;

export type HeritageUnjumbleQuestion = Pick<
  UnjumbleQuestionProps,
  'words' | 'answer' | 'hint' | 'wordsAreJumbled'
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

function sourceOptions(item: PracticeHeritageItem): string[] | null {
  const options = Array.from(
    new Set(item.options.map((option) => option.label.trim()).filter(Boolean)),
  );
  return options.includes(item.answer) ? options : null;
}

function correctSentenceTokens(item: PracticeHeritageItem): string[] | null {
  const sentence = fillSingleBlank(item.prompt, item.answer);
  if (!sentence) return null;
  const tokens = sentence.split(/\s+/).filter((token) => CONTENT_TOKEN.test(token));
  return tokens.length >= 4 ? tokens : null;
}

function jumbledTokens(tokens: readonly string[], seed: number, item: PracticeHeritageItem): string[] {
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
 * A presentation is derived from the persisted session seed, so a resumed card
 * keeps its interaction while sharing the untouched heritage card key and SRS state.
 */
export function selectHeritagePracticePresentation(
  item: PracticeHeritageItem,
  sessionSeed: number,
): HeritagePracticePresentation {
  const presentations: HeritagePracticePresentation[] = [{ kind: 'mc' }];
  const errorCorrection = heritageToErrorCorrection(item);
  if (errorCorrection) presentations.push({ kind: 'error-correction', item: errorCorrection });
  const unjumble = heritageToUnjumble(item, sessionSeed);
  if (unjumble) presentations.push({ kind: 'unjumble', item: unjumble });
  return presentations[seededPracticeHash(sessionSeed, `heritage-presentation:${item.srsKey}`) % presentations.length];
}
