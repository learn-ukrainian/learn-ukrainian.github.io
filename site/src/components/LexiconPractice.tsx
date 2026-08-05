import { type CSSProperties, type ReactElement, useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import MatchUp from './MatchUp';
import PracticeDailyDeck from './PracticeDailyDeck';
import PracticeErrorBoundary from './PracticeErrorBoundary';
import PracticeFlashcard from './PracticeFlashcard';
import PracticeFormRail, { type FormRailVerdict } from './PracticeFormRail';
import PracticeSessionSummary, { type SessionSummaryStats } from './PracticeSessionSummary';
import PracticeStress from './PracticeStress';
import ChromeText, { ChromeDual } from '../lib/i18n/ChromeText';
import { CHROME_STRINGS, type ChromeKey } from '../lib/i18n/chrome';
import {
  DEFAULT_NEW_PER_DAY,
  DAILY_PRACTICE_DECK_SIZE,
  PUBLISHED_PRACTICE_LEVELS,
  SRS_STORAGE_FULL_WARNING,
  buildSessionPoolConstraintState,
  classifyDailyPracticeOrigin,
  clearPracticeSessionSnapshots,
  combinePracticeShards,
  deriveDailyPracticeRows,
  extendWithLowerDecks,
  itemIdPresentInDeck,
  computeSessionScope,
  computeTodayRingDenominator,
  czNorm,
  isCaseClozeDrill,
  isPracticeNewCard,
  isPracticeSessionResumable,
  isWrongCaseAnswer,
  loadState,
  masteredCount,
  nextDuePreviewTime,
  parseCardKey,
  previewRatingIntervals,
  rateCard,
  recentSessionHistory,
  resolveSessionCompletion,
  readNewCardsDailyState,
  readPracticeSessionSnapshots,
  selectNextPracticeItem,
  seededAnswerIndex,
  sessionPoolAllowsCandidate,
  stripIdentityClozeForLemmaFocus,
  stripStressMarks,
  uaPlural,
  validateClozeOptions,
  writeNewCardsDailyState,
  writePracticeSessionSnapshot,
  type ChoicePolarity,
  type DailyPracticeDeckSnapshot,
  type PracticeClozeItem,
  type PracticeClozeShard,
  type PracticeDeckData,
  type PracticeHeritageItem,
  type PracticeHeritageShard,
  type PracticeParonymItem,
  type PracticeParonymShard,
  type PracticeIndexItem,
  type PracticeIndexShard,
  type PracticeLexeme,
  type PracticeLexemeShard,
  type PracticeModeFilter,
  type PracticeRating,
  type PracticeSelection,
  type PracticeSessionIdentity,
  type PracticeSessionSnapshot,
  type PracticeSessionSnapshots,
  type ReviewLogEntry,
  type SelectionHistoryItem,
  type SessionBudget,
  type SessionScopeStats,
  type PracticeClassifySet,
} from '../lib/lexicon/srs';
import {
  focusModeForWeakness,
  matchesWeakness,
  weakCaseChips,
  type WeakArea,
} from '../lib/lexicon/weak-areas';
import {
  CEFR_LEVELS,
  LEARNER_LEVEL_STORAGE_KEY,
  prioritizeByLearnerLevel,
  normalizeCefrLevel,
  type CefrLevel,
} from '../lib/lexicon/levels';
import { dateSeed, deckSeed, pickDaily, reRollSeed, type DailyWord } from '../lib/lexicon/daily';
import {
  filterTeacherClozeItems,
  getCachedLowercaseLemmaKeySet,
  getTeacherLessonVirtualDeck,
  readLocalCustomSets,
  saveLocalCustomSet,
  deleteLocalCustomSet,
  type CustomSet,
} from '../lib/lexicon/custom-decks';
import { syncCustomSetsToDrive, requestGoogleAccessToken, setInMemoryAccessToken, getInMemoryAccessToken } from '../lib/lexicon/google-drive-sync';
import { usablePracticeSentenceEnglish } from '../lib/lexicon/practice-sentence-en';
import { searchShardForQuery, type SearchRow, type SearchShardManifest } from '../lib/lexicon/search';
import { LexiconCustomDeckManager } from './LexiconCustomDeckManager';


/**
 * Practice chrome labels — pure locale via ChromeText CSS (data-chrome-locale).
 * A1 English scaffolding is for item content glosses only (#5503), never dual chrome.
 */
function PracticeChromeLabel({ k }: { k: ChromeKey }): ReactElement {
  return <ChromeText k={k} />;
}

/** Dynamic chrome phrases (interpolated numbers) — pure locale via CSS, never slash-dual. */
function PracticeChromeDual({ uk, en }: { uk: string; en: string }): ReactElement {
  return <ChromeDual en={en} uk={uk} />;
}

interface AtlasDeckMatch {
  lemma: string;
  slug: string;
  gloss: string | null;
  cefr: string | null;
}

interface DeckKeyResolution {
  practice: PracticeLexeme | null;
  atlas: AtlasDeckMatch | null;
}

function cleanDeckKey(key: string): string {
  return key.replace(/\(.*?\)/g, '').trim() || key;
}

function keyLookupVariants(key: string): string[] {
  return Array.from(new Set([key, cleanDeckKey(key)].map((value) => value.toLocaleLowerCase())));
}

function practiceLexemesByKey(lexemes: readonly PracticeLexeme[]): Map<string, PracticeLexeme> {
  const byKey = new Map<string, PracticeLexeme>();
  for (const entry of lexemes) {
    byKey.set(entry.lemmaId.toLocaleLowerCase(), entry);
    byKey.set(entry.lemma.toLocaleLowerCase(), entry);
  }
  return byKey;
}

function searchRowsByKey(rows: readonly SearchRow[]): Map<string, SearchRow> {
  const byKey = new Map<string, SearchRow>();
  for (const entry of rows) {
    byKey.set(entry.s.toLocaleLowerCase(), entry);
    byKey.set(entry.l.toLocaleLowerCase(), entry);
  }
  return byKey;
}

/**
 * Resolve deck keys through the practice cores first, then Atlas's prefix shards.
 * The complete index is deliberately reserved for a missing/broken shard manifest
 * or a shard lookup that cannot find an exact key: it is a compatibility fallback,
 * not the normal custom-deck transport.
 */
async function resolveDeckKeyMetadata(
  lemmaKeys: readonly string[],
  lexemes: readonly PracticeLexeme[],
  cache: Map<string, Promise<unknown>>,
): Promise<Map<string, DeckKeyResolution>> {
  const practiceByKey = practiceLexemesByKey(lexemes);
  const resolutions = new Map<string, DeckKeyResolution>();
  const unresolved: string[] = [];

  for (const key of lemmaKeys) {
    const practice = keyLookupVariants(key)
      .map((variant) => practiceByKey.get(variant))
      .find((entry): entry is PracticeLexeme => Boolean(entry)) ?? null;
    resolutions.set(key, { practice, atlas: null });
    if (!practice) unresolved.push(key);
  }

  // The common case is a deck entirely covered by the practice cores. Do not
  // download any Atlas index artifact in that case.
  if (unresolved.length === 0) return resolutions;

  let rows: SearchRow[] = [];
  let needsFullIndexFallback = false;
  try {
    const manifest = await getShardJson<SearchShardManifest>('/lexicon/search-shards.json', cache);
    const shardPaths = Array.from(
      new Set(
        unresolved.flatMap((key) =>
          keyLookupVariants(key)
            .map((variant) => searchShardForQuery(manifest, variant)?.path)
            .filter((path): path is string => Boolean(path)),
        ),
      ),
    );
    if (shardPaths.length === 0) {
      needsFullIndexFallback = true;
    } else {
      rows = (await Promise.all(
        shardPaths.map((path) => getShardJson<SearchRow[]>(path, cache)),
      )).flat();
      const shardRowsByKey = searchRowsByKey(rows);
      needsFullIndexFallback = unresolved.some(
        (key) => !keyLookupVariants(key).some((variant) => shardRowsByKey.has(variant)),
      );
    }
  } catch {
    needsFullIndexFallback = true;
  }

  if (needsFullIndexFallback) {
    // Last resort only: older/static deployments can lack a manifest or a
    // relevant shard even though their legacy complete index still has the row.
    rows = await getShardJson<SearchRow[]>('/lexicon/search-index.json', cache).catch(() => []);
  }

  const atlasByKey = searchRowsByKey(rows);
  for (const key of unresolved) {
    const atlasRow = keyLookupVariants(key)
      .map((variant) => atlasByKey.get(variant))
      .find((entry): entry is SearchRow => Boolean(entry));
    if (!atlasRow) continue;
    const gloss = atlasRow.g ? cleanGloss(atlasRow.g) : '';
    resolutions.set(key, {
      practice: null,
      atlas: {
        lemma: atlasRow.l,
        slug: atlasRow.s,
        // Search-index text can be a dictionary definition. Only retain the
        // same concise first-sense labels eligible for practice cards.
        gloss: isPhraseGloss(gloss) ? null : gloss,
        cefr: atlasRow.c ?? null,
      },
    });
  }
  return resolutions;
}

function ensureDeckCustomSetCoverage(
  deck: PracticeDeckData,
  lemmaKeys: string[],
  resolutions: ReadonlyMap<string, DeckKeyResolution>,
): PracticeDeckData {
  if (!deck || !lemmaKeys || lemmaKeys.length === 0) return deck;
  const existingIndexLemmas = new Set<string>();
  for (const item of deck.index ?? []) {
    existingIndexLemmas.add(item.lemmaId.toLocaleLowerCase());
    existingIndexLemmas.add(item.lemma.toLocaleLowerCase());
  }
  const newIndexItems: PracticeIndexItem[] = [];
  const newLexemes: PracticeLexeme[] = [];

  const clozeByLemma = new Map<string, string[]>();
  for (const c of deck.cloze ?? []) {
    const key1 = (c.lemmaId || '').toLowerCase();
    const key2 = (c.lemma || '').toLowerCase();
    if (key1) {
      if (!clozeByLemma.has(key1)) clozeByLemma.set(key1, []);
      clozeByLemma.get(key1)!.push(c.clozeId);
    }
    if (key2 && key2 !== key1) {
      if (!clozeByLemma.has(key2)) clozeByLemma.set(key2, []);
      clozeByLemma.get(key2)!.push(c.clozeId);
    }
  }

  let indexModified = false;
  const updatedIndex = (deck.index ?? []).map((item) => {
    const keyLower = item.lemmaId.toLowerCase();
    const customClozeIds = clozeByLemma.get(keyLower) ?? [];
    if (customClozeIds.length === 0) return item;

    const mergedClozeIds = Array.from(new Set([...(item.clozeIds ?? []), ...customClozeIds]));
    const hasCloze = mergedClozeIds.length > 0;
    const modesSet = new Set(item.modes ?? []);
    modesSet.add('flashcards');
    if (hasCloze) modesSet.add('cloze');

    const nextModes = Array.from(modesSet) as PracticeIndexItem['modes'];
    const modesChanged = nextModes.length !== (item.modes ?? []).length;
    const clozeIdsChanged = mergedClozeIds.length !== (item.clozeIds ?? []).length;
    const hasClozeChanged = hasCloze !== item.hasCloze;

    if (modesChanged || clozeIdsChanged || hasClozeChanged) {
      indexModified = true;
      return {
        ...item,
        clozeIds: mergedClozeIds,
        hasCloze,
        modes: nextModes,
      };
    }
    return item;
  });

  let orderCounter = (deck.index ?? []).length + 1;
  for (const key of lemmaKeys) {
    const keyLower = key.toLowerCase();
    if (!existingIndexLemmas.has(keyLower)) {
      existingIndexLemmas.add(keyLower);
      const cleanKey = cleanDeckKey(key);
      const atlas = resolutions.get(key)?.atlas ?? null;
      const matchedClozeIds = clozeByLemma.get(keyLower) ?? [];
      const hasCloze = matchedClozeIds.length > 0;

      // Learner-layout P0-3 / Opus P0-2: an unmatched custom-deck key has no resolved
      // practice-core content — claiming the full mode list here promised exercises
      // (e.g. a "5" on the Heritage card) that the active session then couldn't
      // deliver, landing the learner in an instant empty-mode dead end. Only claim
      // the modes this key actually resolves content for; other modes appear once
      // real shard data resolves them (same honesty rule as the built shards).
      newIndexItems.push({
        lemmaId: atlas?.slug ?? key,
        lemma: atlas?.lemma ?? cleanKey,
        cefr: atlas?.cefr ?? null,
        modes: hasCloze ? ['flashcards', 'cloze'] : ['flashcards'],
        hasCloze,
        clozeIds: matchedClozeIds,
        newOrder: orderCounter++,
      });

      newLexemes.push({
        lemmaId: atlas?.slug ?? key,
        lemma: atlas?.lemma ?? cleanKey,
        lemmaPlain: atlas?.lemma ?? cleanKey,
        ipa: null,
        gloss: atlas?.gloss ?? cleanKey,
        pos: null,
        cefr: atlas?.cefr ?? null,
        heritage: null,
        severity: null,
        paradigm: { cases: {} },
      });
    }
  }

  if (newIndexItems.length === 0 && !indexModified) return deck;

  return {
    ...deck,
    index: [...updatedIndex, ...newIndexItems],
    lexemes: [...(deck.lexemes ?? []), ...newLexemes],
  };
}


interface LexiconPracticeProps {
  deckLevel?: string;
  shardBaseUrl?: string;
  initialDeck?: PracticeDeckData | PracticeLexeme[];
  initialMode?: PracticeModeFilter;
  autoStart?: boolean;
}

interface StreakState {
  version: 1;
  current: number;
  lastPracticeDate: string | null;
}

interface ChoiceOption {
  label: string;
  correct: boolean;
  kind?: 'answer' | 'calque' | 'distractor';
}

interface HeritageFeedback {
  kind: 'correct' | 'calque' | 'wrong';
  textUk: string;
  textEn?: string;
  citations?: string[];
}

function heritageSeverityLabel(severity: PracticeHeritageItem['severity']): { uk: string; en: string } {
  return severity === 'russianism'
    ? { uk: 'Російська калька', en: 'Russian calque' }
    : { uk: 'Лексичне збагачення', en: 'Vocabulary enrichment' };
}

interface ParonymFeedback {
  kind: 'correct' | 'wrong';
  textUk: string;
  textEn?: string;
}

interface ClozeFeedback {
  kind: 'correct' | 'case-miss' | 'wrong-word';
  textUk: string;
  textEn?: string;
}

/** Result of scoring an item, carried until the learner completes/advances it. */
interface CompletionOutcome {
  nextUnresolved: Set<string>;
  nextDeferred: PracticeLexeme[];
}

const STREAK_KEY = 'lu-lexicon-practice-streak';
const DAILY_REROLL_KEY = 'lu-lexicon-daily-reroll';
const MASTERED_THRESHOLD = 21;
type SessionPhase = 'idle' | 'active' | 'summary';

// Load/error chrome strings live in CHROME_STRINGS (practice.loadError / retry / poolMiss).

function makePracticeSessionSeed(): number {
  return (Date.now() ^ Math.floor(Math.random() * 4294967296)) >>> 0;
}

const CASE_GLOSSES: Record<string, string> = {
  'називний': 'nominative',
  'родовий': 'genitive',
  'давальний': 'dative',
  'знахідний': 'accusative',
  'орудний': 'instrumental',
  'місцевий': 'locative',
  'кличний': 'vocative',
  'однина': 'singular',
  'множина': 'plural',
  'чоловічий': 'masculine',
  'жіночий': 'feminine',
  'середній': 'neuter',
  'рід': 'gender',
  'відмінок': 'case',
};

function translateGrammarTerm(ukLabel: string): string {
  if (!ukLabel) return '';
  const norm = ukLabel.toLowerCase().trim();
  const parts = norm.split(/[\s,]+/);
  if (norm.includes('відмінок')) {
    const caseName = parts.find(p => p !== 'відмінок' && p !== 'і' && CASE_GLOSSES[p]);
    const caseEn = caseName ? CASE_GLOSSES[caseName] : '';
    const otherParts = parts.filter(p => p !== 'відмінок' && p !== caseName).map(p => CASE_GLOSSES[p] || p);
    if (caseEn) {
      const caseStr = `${caseEn} case`;
      return otherParts.length > 0 ? `${caseStr}, ${otherParts.join(', ')}` : caseStr;
    }
  }

  if (norm.includes('рід')) {
    const genderName = parts.find(p => p !== 'рід' && CASE_GLOSSES[p]);
    const genderEn = genderName ? CASE_GLOSSES[genderName] : '';
    const otherParts = parts.filter(p => p !== 'рід' && p !== genderName).map(p => CASE_GLOSSES[p] || p);
    if (genderEn) {
      const genderStr = `${genderEn} gender`;
      return otherParts.length > 0 ? `${genderStr}, ${otherParts.join(', ')}` : genderStr;
    }
  }

  const translatedParts = parts.map(part => {
    if (CASE_GLOSSES[part]) return CASE_GLOSSES[part];
    for (const [uk, en] of Object.entries(CASE_GLOSSES)) {
      if (part.includes(uk)) return en;
    }
    return part;
  });

  return translatedParts.join(', ');
}

function translateStorageWarning(warning: string | null): { uk: string; en: string } | null {
  if (!warning) return null;
  if (warning.includes('переповнене') || warning.includes('SRS_STORAGE_FULL_WARNING')) {
    return {
      uk: 'Прогрес не зберігається — сховище переповнене',
      en: 'Progress not saved — storage is full',
    };
  }
  if (warning.includes('сховище браузера')) {
    return {
      uk: 'Прогрес призупинено, доки сховище браузера не стане доступним.',
      en: 'Progress suspended until browser storage becomes available.',
    };
  }
  if (warning.includes('годинник пристрою')) {
    return {
      uk: 'Час повторення може бути неточним: змінився годинник пристрою.',
      en: 'Review schedule may be inaccurate: device clock changed.',
    };
  }
  return { uk: warning, en: warning };
}

const RATING_LABELS: Record<PracticeRating, { uk: string; en: string }> = {
  again: { uk: 'Ще раз', en: 'Again' },
  hard: { uk: 'Важко', en: 'Hard' },
  good: { uk: 'Добре', en: 'Good' },
  easy: { uk: 'Легко', en: 'Easy' },
};

type VisiblePracticeModeFilter = Extract<
  PracticeModeFilter,
  | 'mixed'
  | 'flashcards'
  | 'matching'
  | 'choice'
  | 'cloze'
  | 'stress'
  | 'classify'
  | 'paradigm'
  | 'synonym'
  | 'paronym'
  | 'heritage'
>;

const MODE_CARD_ORDER: VisiblePracticeModeFilter[] = [
  'mixed',
  'flashcards',
  'matching',
  'choice',
  'cloze',
  'stress',
  'classify',
  'paradigm',
  'synonym',
  'paronym',
  'heritage',
];

const MODE_META: Record<
  VisiblePracticeModeFilter,
  {
    title: string;
    en: string;
    description: string;
    descriptionEn: string;
    step: string;
    stepEn: string;
    accent: 'blue' | 'teal' | 'purple' | 'orange';
  }
> = {
  mixed: {
    title: 'Мікс',
    en: 'Mixed',
    description: 'Чергуйте картки, добір, вибір і пропуски, щоб не звикати до одного типу підказки.',
    descriptionEn: 'Rotate flashcards, matching, choice, and fill-in-the-blank options to avoid getting used to a single prompt type.',
    step: 'Змішана сесія',
    stepEn: 'Mixed session',
    accent: 'orange',
  },
  flashcards: {
    title: 'Флешкартки',
    en: 'Flashcards',
    description: 'Картка за карткою з інтервальним повторенням. Згадайте значення, тоді оцініть відповідь.',
    descriptionEn: 'Card by card with spaced repetition. Recall the meaning, then rate your response.',
    step: 'Розпізнавання',
    stepEn: 'Recognition',
    accent: 'blue',
  },
  matching: {
    title: 'Добір пар',
    en: 'Matching',
    description: 'З’єднайте українські слова з їхніми значеннями для швидкого закріплення зв’язків.',
    descriptionEn: 'Connect Ukrainian words with their meanings to quickly reinforce associations.',
    step: 'Зіставлення',
    stepEn: 'Matching',
    accent: 'teal',
  },
  choice: {
    title: 'Вибір',
    en: 'Choice',
    description: 'Оберіть правильне значення або слово серед близьких варіантів з цієї ж колоди.',
    descriptionEn: 'Select the correct meaning or word from close alternatives within the same deck.',
    step: 'Перевірка',
    stepEn: 'Verification',
    accent: 'purple',
  },
  cloze: {
    title: 'Пропуск',
    en: 'Cloze',
    description: 'Впишіть слово у потрібній формі. Відмінок має збігатися з реченням.',
    descriptionEn: 'Write the word in the correct form. The case must match the sentence.',
    step: 'Відмінювання',
    stepEn: 'Declension',
    accent: 'orange',
  },
  stress: {
    title: 'Наголос',
    en: 'Stress',
    description: 'Оберіть голосну, на яку падає наголос у слові.',
    descriptionEn: 'Select the vowel that carries the stress in the word.',
    step: 'Форма слова',
    stepEn: 'Word Form',
    accent: 'teal',
  },
  classify: {
    title: 'Група',
    en: 'Classify',
    description: 'Визначте граматичну групу слова за даними VESUM.',
    descriptionEn: 'Determine the grammatical group of the word based on VESUM data.',
    step: 'Морфологія',
    stepEn: 'Morphology',
    accent: 'purple',
  },
  paradigm: {
    title: 'Форма',
    en: 'Paradigm',
    description: 'Оберіть форму слова для потрібного відмінка й числа.',
    descriptionEn: 'Select the correct word form for the required case and number.',
    step: 'Парадигма',
    stepEn: 'Paradigm',
    accent: 'blue',
  },
  synonym: {
    title: 'Синоніми',
    en: 'Synonyms',
    description: 'Доберіть синонім або антонім до українського слова.',
    descriptionEn: 'Match a synonym or antonym for the Ukrainian word.',
    step: 'Лексика',
    stepEn: 'Vocabulary',
    accent: 'orange',
  },
  paronym: {
    title: 'Пароніми',
    en: 'Paronyms',
    description: 'Розрізняйте близькі за звуковим складом, але різні за значенням слова.',
    descriptionEn: 'Distinguish words that sound similar but have different meanings.',
    step: 'Лексика',
    stepEn: 'Vocabulary',
    accent: 'purple',
  },
  heritage: {
    title: 'Спадщина',
    en: 'Heritage',
    description: 'Оберіть питоме українське слово.',
    descriptionEn: 'Choose the native Ukrainian word.',
    step: 'Питома лексика',
    stepEn: 'Native vocabulary',
    accent: 'teal',
  },
};

function visiblePracticeMode(mode: PracticeModeFilter): VisiblePracticeModeFilter {
  return mode in MODE_META ? (mode as VisiblePracticeModeFilter) : 'mixed';
}

/** P0-3: the mode count must be part of the card's accessible name, not aria-hidden. */
function modeCountAccessibleSuffix(count: number, chromeLocale: 'en' | 'uk'): string {
  return chromeLocale === 'uk'
    ? `${count} ${uaPlural(count, { one: 'вправа', few: 'вправи', many: 'вправ' })}`
    : `${count} ${count === 1 ? 'exercise' : 'exercises'}`;
}

const HERITAGE_COLORS: Record<string, string> = {
  native: 'var(--lu-teal)',
  inherited: 'var(--lu-teal)',
  borrowed: 'var(--lu-purple)',
  loanword: 'var(--lu-purple)',
  calque: 'var(--lu-orange)',
  avoid: 'var(--lu-red)',
};

const MEANING_MC_MAX_WORDS = 4;
const MEANING_MC_MAX_CHARS = 32;
const FUNCTION_POS = new Set([
  'adp',
  'conj',
  'conjunction',
  'det',
  'determiner',
  'interj',
  'interjection',
  'particle',
  'prep',
  'preposition',
  'pron',
  'pronoun',
  'sconj',
]);
const FUNCTION_GLOSS_HEADWORDS = new Set([
  'and',
  'because',
  'but',
  'if',
  'nor',
  'or',
  'than',
  'that',
  'though',
  'unless',
  'until',
  'when',
  'where',
  'whether',
  'while',
  'yet',
]);

function cleanGloss(gloss: string): string {
  return gloss.split(/[;,]/, 1)[0].replace(/\s+/g, ' ').trim();
}

function glossLabel(entry: PracticeLexeme): string {
  return entry.glossClean?.trim() || cleanGloss(entry.gloss);
}

function glossHeadword(entry: PracticeLexeme): string {
  return glossLabel(entry).toLocaleLowerCase('en-US').split(/\s+/)[0] ?? '';
}

export function isEnglishLearnerGloss(label: string): boolean {
  const clean = label.trim();
  if (!clean) return false;
  const latinLetters = clean.match(/\p{Script=Latin}/gu)?.length ?? 0;
  const cyrillicLetters = clean.match(/\p{Script=Cyrillic}/gu)?.length ?? 0;
  return latinLetters > cyrillicLetters;
}

function postAnswerSentenceEnglish(
  feedback: HeritageFeedback | ParonymFeedback | ClozeFeedback | null,
  raw: string | null | undefined,
): string | null {
  // Intentional all-level post-answer English answer key; this is not dual-chrome.
  return feedback ? usablePracticeSentenceEnglish(raw) : null;
}

function isPhraseGloss(label: string): boolean {
  const clean = label.replace(/\s+/g, ' ').trim();
  // Count alphanumeric tokens (ignoring standalone punctuation) to match the
  // Python deck generator's `_meaning_label_word_count` regex exactly, so the
  // served deck and this runtime guard never disagree on eligibility.
  const wordCount = clean ? (clean.match(/[^\W_]+(?:[-'][^\W_]+)?/gu) || []).length : 0;
  return (
    !clean ||
    clean.length > MEANING_MC_MAX_CHARS ||
    wordCount > MEANING_MC_MAX_WORDS ||
    clean.includes('?') ||
    clean.includes('(') ||
    clean.includes(')')
  );
}

export function isMeaningMcEligible(entry: PracticeLexeme): boolean {
  const label = glossLabel(entry);
  if (entry.meaningMcEligible === false) return false;
  // Judge the CLEAN first-sense label, not the raw multi-sense gloss: a word like
  // "dog; hound" has a perfectly concise glossClean ("dog") and must stay eligible.
  if (!isEnglishLearnerGloss(label)) return false;
  if (isPhraseGloss(label)) return false;
  if (FUNCTION_GLOSS_HEADWORDS.has(glossHeadword(entry))) return false;
  if (entry.pos && FUNCTION_POS.has(entry.pos.toLocaleLowerCase('en-US'))) return false;
  return entry.meaningMcEligible ?? true;
}

function todayKey(date = new Date()): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function previousDayKey(date = new Date()): string {
  const previous = new Date(date);
  previous.setDate(previous.getDate() - 1);
  return todayKey(previous);
}

/**
 * #6132: re-roll count for today's featured/daily pick set — how many times the
 * learner has tapped «Перемішати» since the calendar day started. Scoped to
 * `dateKey` so a day change (not just a page reload) resets the draw back to the
 * default (count 0), matching the existing dateSeed(today) behavior it composes with.
 */
function readDailyReRollCount(dateKey: string): number {
  if (typeof window === 'undefined') return 0;
  try {
    const raw = window.localStorage.getItem(DAILY_REROLL_KEY);
    if (!raw) return 0;
    const parsed = JSON.parse(raw) as { date?: string; count?: number };
    return parsed.date === dateKey && typeof parsed.count === 'number' ? parsed.count : 0;
  } catch {
    return 0;
  }
}

function writeDailyReRollCount(dateKey: string, count: number): void {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(DAILY_REROLL_KEY, JSON.stringify({ date: dateKey, count }));
  } catch {
    // Persisting the re-roll count is best-effort; the in-memory count still applies.
  }
}

function readStreak(): StreakState {
  try {
    const raw = window.localStorage.getItem(STREAK_KEY);
    if (!raw) return { version: 1, current: 0, lastPracticeDate: null };
    const parsed = JSON.parse(raw) as Partial<StreakState>;
    if (parsed.version !== 1 || typeof parsed.current !== 'number') {
      return { version: 1, current: 0, lastPracticeDate: null };
    }
    return {
      version: 1,
      current: parsed.current,
      lastPracticeDate: parsed.lastPracticeDate ?? null,
    };
  } catch {
    return { version: 1, current: 0, lastPracticeDate: null };
  }
}

function writeStreak(streak: StreakState): void {
  try {
    window.localStorage.setItem(STREAK_KEY, JSON.stringify(streak));
  } catch {
    // SRS storage warning is handled by the caller.
  }
}

function recordStreak(date = new Date()): StreakState {
  const current = readStreak();
  const today = todayKey(date);
  if (current.lastPracticeDate === today) return current;
  const nextCount = current.lastPracticeDate === previousDayKey(date) ? current.current + 1 : 1;
  const next = { version: 1 as const, current: nextCount, lastPracticeDate: today };
  writeStreak(next);
  return next;
}

function heritageTagColor(heritage: string | null): string | undefined {
  if (!heritage) return undefined;
  return HERITAGE_COLORS[heritage.toLowerCase()] ?? 'var(--lu-text-muted)';
}

/** P0-4: heritage on the flashcard back must be a text chip, not color-only. */
const HERITAGE_LABEL_KEYS: Record<string, ChromeKey> = {
  native: 'practice.heritageNative',
  inherited: 'practice.heritageInherited',
  borrowed: 'practice.heritageBorrowed',
  loanword: 'practice.heritageBorrowed',
  calque: 'practice.heritageCalque',
  avoid: 'practice.heritageAvoid',
};

function heritageLabelText(heritage: string | null, chromeLocale: 'en' | 'uk'): string | undefined {
  if (!heritage) return undefined;
  const key = HERITAGE_LABEL_KEYS[heritage.toLowerCase()];
  return key ? CHROME_STRINGS[chromeLocale][key] : undefined;
}

function displayPracticeForm(value: string, learnerLevel: CefrLevel): string {
  return learnerLevel === 'A1' ? value : stripStressMarks(value);
}

function cardData(entry: PracticeLexeme, learnerLevel: CefrLevel, chromeLocale: 'en' | 'uk') {
  return {
    front: displayPracticeForm(entry.lemma, learnerLevel),
    back: entry.gloss,
    subtitle: entry.ipa ?? entry.pos ?? undefined,
    tag: entry.cefr ?? undefined,
    tagColor: heritageTagColor(entry.heritage),
    heritageLabel: heritageLabelText(entry.heritage, chromeLocale),
  };
}

function clozeExample(cloze: PracticeClozeItem): { example: string; exampleEn: string | null } | null {
  const sentence = cloze.sentence?.trim();
  const form = cloze.form?.trim();
  if (!sentence || !form || !/_{3,}/.test(sentence)) return null;

  return {
    example: sentence.replace(/_{3,}/g, form),
    exampleEn: cloze.clozeEn?.trim() || null,
  };
}

export function addDailyExamples(
  lexemes: Map<string, PracticeLexeme>,
  clozeItems: readonly PracticeClozeItem[],
): Map<string, PracticeLexeme> {
  const fallbackByLemma = new Map<string, { example: string; exampleEn: string | null }>();
  for (const item of clozeItems) {
    if (fallbackByLemma.has(item.lemmaId)) continue;
    const example = clozeExample(item);
    if (example) fallbackByLemma.set(item.lemmaId, example);
  }

  const enriched = new Map<string, PracticeLexeme>();
  for (const [lemmaId, lexeme] of lexemes) {
    if (lexeme.example?.trim()) {
      enriched.set(lemmaId, lexeme);
      continue;
    }
    const fallback = fallbackByLemma.get(lemmaId);
    enriched.set(
      lemmaId,
      fallback
        ? { ...lexeme, example: fallback.example, exampleEn: lexeme.exampleEn ?? fallback.exampleEn }
        : lexeme,
    );
  }
  return enriched;
}

function hasLoadedDrillShards(deck: PracticeDeckData | null): boolean {
  return Boolean(
    deck &&
      (deck.cloze.length > 0 ||
        (deck.stress?.length ?? 0) > 0 ||
        (deck.classify?.length ?? 0) > 0 ||
        (deck.paradigm?.length ?? 0) > 0 ||
        (deck.synonym?.length ?? 0) > 0 ||
        (deck.paronym?.length ?? 0) > 0 ||
        (deck.heritage?.length ?? 0) > 0),
  );
}

function normalizeInitialDeck(initialDeck?: PracticeDeckData | PracticeLexeme[]): PracticeDeckData | null {
  if (!initialDeck) return null;
  if (!Array.isArray(initialDeck)) return initialDeck;
  const lexemes = initialDeck.map((entry) => {
    const legacy = entry as PracticeLexeme & { slug?: string; example?: string | null };
    const lemmaId = legacy.lemmaId ?? legacy.slug ?? legacy.lemma;
    const glossClean = legacy.glossClean ?? cleanGloss(legacy.gloss);
    const meaningMcEligible = legacy.meaningMcEligible ?? (
      isEnglishLearnerGloss(glossClean) && !isPhraseGloss(glossClean)
    );
    return {
      ...entry,
      lemmaId,
      lemmaPlain: legacy.lemmaPlain ?? czNorm(legacy.lemma),
      glossClean,
      meaningMcEligible,
      severity: legacy.severity ?? null,
      paradigm: legacy.paradigm ?? { cases: {} },
    };
  });
  const deckGuidanceLevel = lexemes.find((entry) => entry.cefr)?.cefr ?? 'unknown';
  return {
    deckVersion: 'test-fixture',
    level: deckGuidanceLevel,
    index: lexemes.map((entry, index) => ({
      lemmaId: entry.lemmaId,
      lemma: entry.lemma,
      cefr: entry.cefr ?? null,
      modes: entry.meaningMcEligible ? ['flashcards', 'matching', 'choice'] : ['flashcards'],
      hasCloze: false,
      clozeIds: [],
      newOrder: index,
    })),
    lexemes,
    cloze: [],
    stress: [],
    classify: [],
    paradigm: [],
    synonym: [],
  };
}

function historyFromSelection(selection: PracticeSelection): SelectionHistoryItem {
  return {
    itemId: selection.itemId,
    lemmaId: selection.lemma.lemmaId,
    mode: selection.mode,
    clozeId: selection.cloze?.clozeId,
    sentenceFrameId: selection.cloze?.sentenceFrameId,
    blankCase: selection.cloze?.blankCase,
    classifySetId: selection.classifySetId,
    heritageId: selection.heritage?.heritageId,
    recallDirection: selection.recallDirection,
    choicePolarity: selection.choicePolarity,
    lapsed: selection.lapsed,
  };
}

/**
 * #6132: a fresh session's `history` starts from the learner's most recent same-day
 * reviews instead of always `[]`, so `selectNextPracticeItem`'s spacing/anti-monotony
 * logic reacts immediately — without this, starting a second same-day session opened
 * with the exact same opening picks as the first.
 */
function seedCrossSessionHistory(now: Date): SelectionHistoryItem[] {
  return recentSessionHistory(loadState().reviews, now.getTime());
}

function reviewLemmaId(selection: PracticeSelection): string {
  const parsed = parseCardKey(selection.cardKey);
  if (!parsed.quarantined && parsed.mode === selection.mode) return parsed.lemmaId;
  return selection.lemma.lemmaId;
}

function orderedChoiceOptions(
  selection: PracticeSelection,
  deck: PracticeDeckData,
  polarity: ChoicePolarity,
  sessionSeed: number,
  learnerLevel: CefrLevel,
): ChoiceOption[] {
  if (!isMeaningMcEligible(selection.lemma)) return [];
  const distractors = meaningDistractors(selection.lemma, deck, 3);
  if (distractors.length < 3) return [];
  const answer = polarity === 'word-to-meaning'
    ? glossLabel(selection.lemma)
    : displayPracticeForm(selection.lemma.lemma, learnerLevel);
  const options = [
    { label: answer, correct: true },
    ...distractors.map((entry) => ({
      label: polarity === 'word-to-meaning' ? glossLabel(entry) : displayPracticeForm(entry.lemma, learnerLevel),
      correct: false,
    })),
  ];
  const answerIndex = seededAnswerIndex(sessionSeed, selection.itemId, options.length);
  const [first] = options.splice(0, 1);
  options.splice(answerIndex, 0, first);
  return options;
}

function cefrRank(level: string | null | undefined): number {
  const rank = CEFR_LEVELS.indexOf(level as CefrLevel);
  return rank >= 0 ? rank : CEFR_LEVELS.length;
}

export function meaningDistractors(
  answer: PracticeLexeme,
  deck: PracticeDeckData,
  limit: number,
): PracticeLexeme[] {
  const answerHeadword = glossHeadword(answer);
  const answerLength = glossLabel(answer).length;
  const answerRank = cefrRank(answer.cefr);
  const candidatePool = deck.lexemes.filter(
    (candidate) =>
      candidate.lemmaId !== answer.lemmaId &&
      isMeaningMcEligible(candidate) &&
      glossHeadword(candidate) !== answerHeadword,
  );

  // Build concentric CEFR rings around the answer. Distractors stay
  // semantically comparable because we exhaust the closest ring before
  // moving outward; this prevents a B1 answer from being undermined by A1
  // distractors or an A1 answer from being ambushed by C1 vocabulary.
  const rings = new Map<number, PracticeLexeme[]>();
  for (const candidate of candidatePool) {
    const gap = Math.abs(cefrRank(candidate.cefr) - answerRank);
    const bucket = rings.get(gap) ?? [];
    bucket.push(candidate);
    rings.set(gap, bucket);
  }
  const sortedGaps = [...rings.keys()].sort((left, right) => left - right);

  const seenLabels = new Set<string>();
  const result: PracticeLexeme[] = [];
  for (const gap of sortedGaps) {
    const ring = rings.get(gap) ?? [];
    const picked = ring
      .sort((left, right) => {
        const leftPos = left.pos === answer.pos ? 0 : 1;
        const rightPos = right.pos === answer.pos ? 0 : 1;
        if (leftPos !== rightPos) return leftPos - rightPos;
        const leftLen = Math.abs(glossLabel(left).length - answerLength);
        const rightLen = Math.abs(glossLabel(right).length - answerLength);
        return leftLen - rightLen || left.lemmaId.localeCompare(right.lemmaId);
      })
      .filter((entry) => {
        const key = glossLabel(entry).toLocaleLowerCase('en-US');
        if (seenLabels.has(key)) return false;
        seenLabels.add(key);
        return true;
      });
    result.push(...picked);
    if (result.length >= limit) break;
  }
  return result.slice(0, limit);
}

function matchingPairs(selection: PracticeSelection, deck: PracticeDeckData, learnerLevel: CefrLevel) {
  if (!isMeaningMcEligible(selection.lemma)) return [];
  const distractors = meaningDistractors(selection.lemma, deck, 5);
  if (distractors.length < 2) return [];
  const entries = [selection.lemma, ...distractors];
  if (!entries.every(isMeaningMcEligible)) return [];
  return entries.map((entry) => ({
    left: displayPracticeForm(entry.lemma, learnerLevel),
    right: glossLabel(entry),
    lemmaId: entry.lemmaId,
  }));
}

export function nextMatchingPromptIndex(
  currentPromptIndex: number | null,
  matchedPairIndexes: ReadonlySet<number>,
  pairCount: number,
): number | null {
  if (currentPromptIndex === null || !matchedPairIndexes.has(currentPromptIndex)) {
    return currentPromptIndex;
  }
  for (let index = 0; index < pairCount; index += 1) {
    if (!matchedPairIndexes.has(index)) return index;
  }
  return null;
}

function choicePrompt(selection: PracticeSelection, learnerLevel: CefrLevel): { uk: string; en: string } {
  const lemma = displayPracticeForm(selection.lemma.lemma, learnerLevel);
  if (selection.choicePolarity === 'word-to-meaning') {
    return {
      uk: `Що означає «${lemma}»?`,
      en: `What does «${lemma}» mean?`,
    };
  }
  return {
    uk: `Яке слово означає «${glossLabel(selection.lemma)}»?`,
    en: `Which word means «${glossLabel(selection.lemma)}»?`,
  };
}

function classifySet(selection: PracticeSelection): PracticeClassifySet | null {
  const sets = selection.classify?.sets ?? [];
  if (!sets.length) return null;
  return sets.find((set) => set.setId === selection.classifySetId) ?? sets[0] ?? null;
}

function drillChoiceOptions(
  selection: PracticeSelection,
  showEnglishSubtitles: boolean,
  learnerLevel: CefrLevel,
): ChoiceOption[] | null {
  const selectedSet = classifySet(selection);
  if (selectedSet) {
    return selectedSet.options.map((option) => ({
      label: showEnglishSubtitles
        ? (option.labelEn
           ? `${option.labelUk} (${option.labelEn})`
           : (translateGrammarTerm(option.labelUk) !== option.labelUk
              ? `${option.labelUk} (${translateGrammarTerm(option.labelUk)})`
              : option.labelUk))
        : option.labelUk,
      correct: selectedSet.answers?.includes(option.value) ?? option.value === selectedSet.answer,
    }));
  }
  if (selection.paradigm) {
    return selection.paradigm.options.map((option) => ({
      label: displayPracticeForm(option.label, learnerLevel),
      correct: option.kind === 'answer',
    }));
  }
  if (selection.synonym) {
    return selection.synonym.options.map((option) => ({
      label: displayPracticeForm(option.label, learnerLevel),
      correct: option.kind === 'answer',
    }));
  }
  return null;
}

function heritageOptions(item: PracticeHeritageItem): ChoiceOption[] {
  const answer = czNorm(item.answer);
  const calque = czNorm(item.calque);
  return item.options.map((option) => {
    const label = czNorm(option.label);
    const correct = label === answer;
    return {
      label: option.label,
      correct,
      kind: correct ? 'answer' : label === calque ? 'calque' : 'distractor',
    };
  });
}

function heritageFeedbackFor(item: PracticeHeritageItem, option: ChoiceOption): HeritageFeedback {
  if (option.correct) {
    return {
      kind: 'correct',
      textUk: 'Правильно',
      textEn: 'Correct',
    };
  }
  if (option.kind === 'calque') {
    return {
      kind: 'calque',
      textUk: item.rationaleUk ? `⚠️ калька; ${item.rationaleUk}` : '⚠️ калька',
      textEn: item.rationaleUk && item.rationale ? `⚠️ calque; ${item.rationale}` : '⚠️ calque',
      citations: item.citations,
    };
  }
  return {
    kind: 'wrong',
    textUk: 'Ще раз',
    textEn: 'Again',
  };
}

function drillChoicePrompt(
  selection: PracticeSelection,
  learnerLevel: CefrLevel,
): { promptUk: string; promptEn: string; subtitleUk: string; subtitleEn?: string } | null {
  if (selection.stress) {
    return {
      promptUk: `Де наголос у слові «${selection.stress.unstressed}»?`,
      promptEn: `Where is the stress in the word «${selection.stress.unstressed}»?`,
      subtitleUk: 'Оберіть наголошену голосну',
      subtitleEn: 'Select the stressed vowel',
    };
  }
  const selectedSet = classifySet(selection);
  const lemma = displayPracticeForm(selection.lemma.lemma, learnerLevel);
  if (selectedSet) {
    const setLabelUk = selectedSet.setLabelUk;
    const setLabelEn = selectedSet.setLabelEn || translateGrammarTerm(setLabelUk);
    const hasMultipleAnswers = (selectedSet.answers?.length ?? 0) > 1;
    return {
      promptUk: `До якої групи належить «${lemma}»?`,
      promptEn: `Which group does «${lemma}» belong to?`,
      subtitleUk: hasMultipleAnswers
        ? `${setLabelUk} · можливі кілька правильних відповідей`
        : setLabelUk,
      subtitleEn: hasMultipleAnswers
        ? `${setLabelEn} · Multiple answers may be correct`
        : setLabelEn,
    };
  }
  if (selection.paradigm) {
    const slotUk = selection.paradigm.slot.labelUk;
    const slotEn = selection.paradigm.slot.labelEn || translateGrammarTerm(slotUk);
    return {
      promptUk: `Яка форма від «${lemma}»?`,
      promptEn: `Which form is from «${lemma}»?`,
      subtitleUk: slotUk,
      subtitleEn: slotEn,
    };
  }
  if (selection.synonym) {
    const isAntonym = selection.synonym.polarity === 'antonym';
    return {
      promptUk: isAntonym
        ? `Оберіть антонім до «${selection.synonym.prompt}»`
        : `Оберіть синонім до «${selection.synonym.prompt}»`,
      promptEn: isAntonym
        ? `Choose an antonym for «${selection.synonym.prompt}»`
        : `Choose a synonym for «${selection.synonym.prompt}»`,
      subtitleUk: 'Оберіть правильну відповідь',
      subtitleEn: 'Select the correct answer',
    };
  }
  return null;
}

function clozeParts(item: PracticeClozeItem): [string, string] {
  const [before, ...after] = item.sentence.split('___');
  return [before, after.join('___')];
}

function slotPromptParts(prompt: string): [string, string] {
  const [before, ...after] = prompt.split('___');
  return [before, after.join('___')];
}

function shouldLoadCloze(mode: PracticeModeFilter): boolean {
  return ['mixed', 'cloze', 'stress', 'classify', 'paradigm', 'synonym', 'paronym', 'heritage'].includes(mode);
}

function sessionScopeIndexForMode(
  index: PracticeIndexItem[],
  modeFilter: PracticeModeFilter,
): PracticeIndexItem[] {
  if (modeFilter === 'mixed') return index;
  return index
    .filter((item) => item.modes.includes(modeFilter))
    .map((item) => ({ ...item, modes: [modeFilter] }));
}

/** Shared match test for the Selected Deck filter (Teacher Lesson or a Custom Set),
 * keyed on lemmaId/lemma the same way for both index-level planning and per-candidate
 * selection — a single definition so the two can never drift apart. */
function deckFilterAllowsLemma(
  lemmaId: string,
  lemma: string,
  allowedKeys: ReadonlySet<string> | null,
): boolean {
  if (!allowedKeys) return true;
  return allowedKeys.has(lemmaId.toLowerCase()) || allowedKeys.has(lemma.toLowerCase());
}

/** Narrow a level's practice index to the active deck filter BEFORE computing session
 * scope, so a session's planned total/due count/estimate reflect the SELECTED deck
 * rather than the full level (F2 follow-up, PR #5837 review: "the chosen set actually
 * drives the next session" applies to the session's size, not just its item content —
 * without this, switching to a 1-word custom deck still planned a session sized off the
 * full level index). */
function filterIndexByDeckFilter(
  index: PracticeIndexItem[],
  allowedKeys: ReadonlySet<string> | null,
): PracticeIndexItem[] {
  if (!allowedKeys) return index;
  return index.filter((item) => deckFilterAllowsLemma(item.lemmaId, item.lemma, allowedKeys));
}

/**
 * Resolves the active deck once per render. `null` deliberately preserves the
 * existing fail-open behaviour for "all" and a deleted custom-deck selection.
 */
function resolveDeckLemmaKeySet(
  deckFilter: string,
  customSets: CustomSet[],
): ReadonlySet<string> | null {
  if (deckFilter === 'all') return null;
  if (deckFilter === 'virtual_teacher_lesson') {
    return getCachedLowercaseLemmaKeySet(getTeacherLessonVirtualDeck().lemma_keys);
  }
  const customSet = customSets.find((set) => set.id === deckFilter);
  return customSet ? getCachedLowercaseLemmaKeySet(customSet.lemma_keys) : null;
}

/**
 * D10 (design delta 2026-07-27): the raw lemma keys owned by the active deck filter,
 * or `null` for 'all' — meaning the atlas-global daily pool applies unchanged (D2).
 * Mirrors `deckFilterAllowsLemma`'s own key resolution so the daily zone can never
 * disagree with the session/estimate machinery about which deck owns which lemma.
 */
function resolveDeckLemmaKeys(deckFilter: string, customSets: CustomSet[]): string[] | null {
  if (deckFilter === 'all') return null;
  if (deckFilter === 'virtual_teacher_lesson') return getTeacherLessonVirtualDeck().lemma_keys;
  return customSets.find((s) => s.id === deckFilter)?.lemma_keys ?? [];
}

/** Learner level persisted in the shared `lu-learner-level` key (also used by Words of the Day). */
function readLearnerLevel(fallback: CefrLevel): CefrLevel {
  if (typeof window === 'undefined') return fallback;
  try {
    return normalizeCefrLevel(window.localStorage.getItem(LEARNER_LEVEL_STORAGE_KEY), fallback);
  } catch {
    return fallback;
  }
}

function writeLearnerLevel(level: CefrLevel): void {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(LEARNER_LEVEL_STORAGE_KEY, level);
  } catch {
    // Persisting the preference is best-effort; the in-memory selection still applies.
  }
}

/** All published practice shards; learner level is a preference, not a hard cap. */
function levelsForPractice(): CefrLevel[] {
  return [...PUBLISHED_PRACTICE_LEVELS] as CefrLevel[];
}

/** Concatenate per-level decks into one cumulative deck (CEFR shards are disjoint). */
function mergeDecks(decks: PracticeDeckData[], level: CefrLevel): PracticeDeckData {
  if (decks.length === 0) throw new Error('mergeDecks called with no decks');
  // Delegate to the shared extend for consistency (new deck identity for selector cache).
  const [first, ...rest] = decks;
  const base = { ...first, level };
  return extendWithLowerDecks(base, rest);
}

/** Encode an Atlas lemma route from the verified lemmaId. */
function atlasLemmaHref(lemmaId: string): string {
  return `/lexicon/${encodeURIComponent(lemmaId)}/`;
}

/** Resolve either a practice item id or the bare lemma that Atlas links provide. */
function resolvePracticeIndexItem(
  index: PracticeIndexItem[],
  target: string,
): PracticeIndexItem | null {
  const normalizedTarget = czNorm(target);
  if (!normalizedTarget) return null;

  return (
    [...index]
      .reverse()
      .find((item) => item.lemmaId === target || czNorm(item.lemma) === normalizedTarget) ?? null
  );
}

/** Pure-locale practice chrome message (both locales in DOM; CSS shows one). */
function PureLocalePracticeMessage({ uk, en }: { uk: string; en: string }) {
  return <ChromeDual uk={uk} en={en} />;
}

/** Bare hard-stem adjective case labels (`знахідний`) → «у знахідний відмінок». */
function casePhraseAccusative(caseLabel: string): string {
  return `у ${caseLabel} відмінок`;
}

/** Digit 1–n shortcuts for multiple-choice option lists (drill/choice). */
function DigitChoiceShortcuts({
  options,
  answerLocked,
  onChoice,
}: {
  options: ChoiceOption[];
  answerLocked: boolean;
  onChoice(option: ChoiceOption): void;
}) {
  useEffect(() => {
    if (answerLocked || options.length === 0) return undefined;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.altKey || event.ctrlKey || event.metaKey) return;
      const target = event.target as HTMLElement | null;
      if (target?.closest?.('button, a, input, textarea, select, [role="button"]')) return;
      const digit = Number.parseInt(event.key, 10);
      if (!Number.isFinite(digit) || digit < 1 || digit > options.length) return;
      event.preventDefault();
      onChoice(options[digit - 1]!);
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [answerLocked, onChoice, options]);
  return null;
}

/** Deduped fetch for practice and Atlas JSON by URL. Concurrent or repeated callers share the promise. */
async function getShardJson<T>(url: string, cache: Map<string, Promise<unknown>>): Promise<T> {
  let p = cache.get(url) as Promise<T> | undefined;
  if (!p) {
    p = fetch(url).then((res) => {
      if (!res.ok) {
        // Tag the HTTP status so callers can tell an unpublished shard (404,
        // soft-skippable) from a real load fault (network / server error).
        const err = new Error(`Shard fetch failed: ${url}`) as Error & { status?: number };
        err.status = res.status;
        throw err;
      }
      return res.json() as Promise<T>;
    });
    // On failure allow retry next time
    p = p.catch((err) => {
      cache.delete(url);
      throw err;
    });
    cache.set(url, p);
  }
  return p;
}

export default function LexiconPractice(props: LexiconPracticeProps) {
  return (
    <PracticeErrorBoundary>
      <LexiconPracticeIsland {...props} />
    </PracticeErrorBoundary>
  );
}

function LexiconPracticeIsland({
  deckLevel = 'A1',
  shardBaseUrl = '/lexicon',
  initialDeck,
  initialMode = 'mixed',
  autoStart = false,
}: LexiconPracticeProps) {
  const [deck, setDeck] = useState<PracticeDeckData | null>(() => normalizeInitialDeck(initialDeck));
  const [clozeLoaded, setClozeLoaded] = useState(() => {
    const normalized = normalizeInitialDeck(initialDeck);
    return hasLoadedDrillShards(normalized);
  });
  const [sessionPhase, setSessionPhase] = useState<SessionPhase>(autoStart ? 'active' : 'idle');
  const [sessionSeed, setSessionSeed] = useState(() => makePracticeSessionSeed());
  const [mode, setMode] = useState<PracticeModeFilter>(initialMode);
  const [sessionBudget, setSessionBudget] = useState<SessionBudget>(20);
  const [sessionPlan, setSessionPlan] = useState<SessionScopeStats | null>(null);
  const [plannedReviews, setPlannedReviews] = useState(0);
  const [plannedTotal, setPlannedTotal] = useState(0);
  const [sessionCompleted, setSessionCompleted] = useState(0);
  const [reviewsCompleted, setReviewsCompleted] = useState(0);
  const [sessionNewIntroduced, setSessionNewIntroduced] = useState(0);
  const [extensionUsed, setExtensionUsed] = useState(0);
  const [unresolvedCardKeys, setUnresolvedCardKeys] = useState<Set<string>>(() => new Set());
  const [deferredLemmas, setDeferredLemmas] = useState<PracticeLexeme[]>([]);
  const [sessionCorrect, setSessionCorrect] = useState(0);
  const [sessionLapsed, setSessionLapsed] = useState(0);
  const [advancedToReview, setAdvancedToReview] = useState<string[]>([]);
  const [resumeSnapshots, setResumeSnapshots] = useState<PracticeSessionSnapshots>({});
  const [learnerLevel, setLearnerLevel] = useState<CefrLevel>(() =>
    readLearnerLevel(normalizeCefrLevel(deckLevel)),
  );
  const [focusedLemmaId, setFocusedLemmaId] = useState<string | null>(null);
  const [focusLookupMiss, setFocusLookupMiss] = useState(false);
  // §6b weak-area focus: when set, the session poolFilter is narrowed to this weakness.
  const [focusWeakness, setFocusWeakness] = useState<WeakArea | null>(null);
  const [reviewLog, setReviewLog] = useState<ReviewLogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{ uk: string; en?: string } | null>(null);
  const [revision, setRevision] = useState(0);
  const [history, setHistory] = useState<SelectionHistoryItem[]>([]);
  const [answerLocked, setAnswerLocked] = useState(false);
  // After ANY answer (correct or wrong), park the scored outcome here instead of
  // auto-advancing so the learner explicitly continues via «Далі →» or Enter.
  const [pendingOutcome, setPendingOutcome] = useState<CompletionOutcome | null>(null);
  const [streak, setStreak] = useState<StreakState>({
    version: 1,
    current: 0,
    lastPracticeDate: null,
  });
  const [, setMastered] = useState(0);
  const [completedToday, setCompletedToday] = useState(0);
  const [dailyNewCount, setDailyNewCount] = useState(0);
  const [storageWarning, setStorageWarning] = useState<string | null>(null);
  const [clozeInput, setClozeInput] = useState('');
  const [clozeFeedback, setClozeFeedback] = useState<ClozeFeedback | null>(null);
  const [clozeAttemptRecorded, setClozeAttemptRecorded] = useState(false);
  // Opus P0-6: a case-miss used to clear the input and loop forever with no lock —
  // a learner who knew the word but not the case could cycle its paradigm
  // indefinitely. Cap case-misses so the second one locks and reveals via the
  // existing PracticeFormRail path, same as any other locked cloze result.
  const [clozeCaseMissCount, setClozeCaseMissCount] = useState(0);
  const clozeCaseMissOutcomeRef = useRef<CompletionOutcome | null>(null);
  const [heritageFeedback, setHeritageFeedback] = useState<HeritageFeedback | null>(null);
  const [paronymFeedback, setParonymFeedback] = useState<ParonymFeedback | null>(null);
  const [stressSelectedPosition, setStressSelectedPosition] = useState<number | null>(null);
  const [paradigmSelectedLabel, setParadigmSelectedLabel] = useState<string | null>(null);
  const [paronymSelectedLabel, setParonymSelectedLabel] = useState<string | null>(null);
  const [heritageSelectedLabel, setHeritageSelectedLabel] = useState<string | null>(null);
  const [customSets, setCustomSets] = useState<CustomSet[]>(() => readLocalCustomSets());
  const [selectedDeckFilter, setSelectedDeckFilter] = useState<string>('all');
  const [isDriveSyncing, setIsDriveSyncing] = useState(false);
  const [driveSyncMsg, setDriveSyncMsg] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newSetTitle, setNewSetTitle] = useState('');
  const [newSetLemmas, setNewSetLemmas] = useState('');
  // D7: changing deck/level while a session is active or resumable offers a fresh
  // session instead of silently discarding progress. `pendingDeckSwitch` holds the
  // NOT-YET-APPLIED choice; the chip visually reverts until the learner decides.
  const [pendingDeckSwitch, setPendingDeckSwitch] = useState<
    { kind: 'deck'; value: string } | { kind: 'level'; value: CefrLevel } | null
  >(null);
  const deckLemmaKeySet = useMemo(
    () => resolveDeckLemmaKeySet(selectedDeckFilter, customSets),
    [customSets, selectedDeckFilter],
  );

  const handleGoogleDriveSync = useCallback(async () => {
    setIsDriveSyncing(true);
    setDriveSyncMsg('Авторизація через Google...');
    try {
      let token = getInMemoryAccessToken();
      if (!token) {
        token = await requestGoogleAccessToken();
      }
      setDriveSyncMsg('Синхронізація з Google Drive...');
      const result = await syncCustomSetsToDrive(token);
      setIsDriveSyncing(false);
      if (result.success) {
        setDriveSyncMsg(`Успішно! Синхронізовано колод: ${result.customSetsSynced}`);
        setCustomSets(readLocalCustomSets());
      } else {
        setDriveSyncMsg(`Помилка: ${result.message}`);
      }
    } catch (err: any) {
      setIsDriveSyncing(false);
      setDriveSyncMsg(err?.message || 'Google Auth Error');
    }
  }, []);

  const handleCreateCustomSetSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    if (!newSetTitle.trim()) return;
    const lemmas = newSetLemmas
      .split(/[\n,;]+/)
      .map((s) => s.trim())
      .filter(Boolean);
    const created = saveLocalCustomSet({
      title: newSetTitle.trim(),
      lemma_keys: lemmas,
    });
    setCustomSets(readLocalCustomSets());
    setSelectedDeckFilter(created.id);
    setShowCreateModal(false);
    setNewSetTitle('');
    setNewSetLemmas('');
  }, [newSetTitle, newSetLemmas]);

  const [dueIndex, setDueIndex] = useState<PracticeIndexItem[] | null>(null);
  const [dailySnapshot, setDailySnapshot] = useState<DailyPracticeDeckSnapshot | null>(null);
  const [dailyLexemes, setDailyLexemes] = useState<Map<string, PracticeLexeme>>(() => new Map());
  const [dailySnapshotLoading, setDailySnapshotLoading] = useState(false);
  const [dailyReRollCount, setDailyReRollCount] = useState(() => readDailyReRollCount(todayKey()));
  // #6146: the calendar day `dailyReRollCount` was established for. `useState`'s
  // initializer only runs at mount, so a tab left open across local midnight would
  // otherwise keep applying yesterday's re-roll offset to today's `dateSeed` — the
  // picks-fetch effect below and the midnight timer both compare against this to
  // catch the rollover and reset the count back to the day's default draw (0).
  const dailyReRollDateRef = useRef(todayKey());
  // #6132: explicit re-draw of today's featured set — see the effect below that folds
  // this count into the pickDaily seed via `reRollSeed`.
  const reRollDailyPicks = useCallback(() => {
    const dateKey = todayKey();
    // #6146: a tap landing before the day-rollover reset has run (midnight timer not
    // yet fired, effect not yet re-run) must not continue incrementing yesterday's
    // count — start the new day's re-roll sequence at 1, not stale-count + 1.
    const dayChanged = dailyReRollDateRef.current !== dateKey;
    dailyReRollDateRef.current = dateKey;
    setDailyReRollCount((count) => {
      const next = (dayChanged ? 0 : count) + 1;
      writeDailyReRollCount(dateKey, next);
      return next;
    });
  }, []);
  // #6146: catch a day rollover while the tab stays open (idle, no props changing) by
  // arming a timer for the next local midnight rather than polling. On fire, reset the
  // re-roll count if the day actually advanced, then rearm for the following midnight.
  useEffect(() => {
    let timeoutId: ReturnType<typeof setTimeout>;
    const armForNextMidnight = () => {
      const now = new Date();
      const nextMidnight = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1, 0, 0, 5);
      timeoutId = setTimeout(() => {
        const currentDateKey = todayKey();
        if (dailyReRollDateRef.current !== currentDateKey) {
          dailyReRollDateRef.current = currentDateKey;
          setDailyReRollCount(0);
        }
        armForNextMidnight();
      }, Math.max(0, nextMidnight.getTime() - now.getTime()));
    };
    armForNextMidnight();
    return () => clearTimeout(timeoutId);
  }, []);
  const [hoveredMode, setHoveredMode] = useState<VisiblePracticeModeFilter | null>(null);
  const [publishedLevels] = useState<Set<CefrLevel>>(
    () => new Set(PUBLISHED_PRACTICE_LEVELS as unknown as CefrLevel[]),
  );
  const stageRef = useRef<HTMLDivElement | null>(null);
  const deckRequestId = useRef(0);
  const sessionStartedAtRef = useRef(Date.now());
  const didInitRef = useRef(false);
  // Consumption source of truth for the parked answer outcome. `advancePending`
  // claims it via this ref (not the closed-over `pendingOutcome` state) so a rapid
  // double-advance (double-Enter, or Enter+click) before React re-renders resolves to
  // exactly ONE `completeSelection` — the second call reads a null ref and no-ops.
  const pendingOutcomeRef = useRef<CompletionOutcome | null>(null);
  const advanceButtonRef = useRef<HTMLButtonElement | null>(null);
  // Selection ref used to stabilize the in-flight item across live deck merges (pool growth from
  // background level shards). While history length is unchanged we keep returning the
  // prior selection object so a B1 card is not yanked when an A1/A2 shard lands mid-item.
  const committedSelectionRef = useRef<{ selection: PracticeSelection; historyLen: number } | null>(null);
  // Deduping cache for shard JSON fetches (by full URL) so index shards fetched by the eager
  // due-count effect are not re-fetched by ensure, and no shard is fetched twice.
  const shardJsonCacheRef = useRef(new Map<string, Promise<unknown>>());
  const [chromeLocale, setChromeLocale] = useState<'en' | 'uk'>(() =>
    typeof document !== 'undefined'
      ? ((document.documentElement.dataset.chromeLocale as 'en' | 'uk') || 'en')
      : 'en',
  );
  useEffect(() => {
    if (typeof document === 'undefined') return;
    const el = document.documentElement;
    setChromeLocale((el.dataset.chromeLocale as 'en' | 'uk') || 'en');
    const obs = new MutationObserver(() =>
      setChromeLocale((el.dataset.chromeLocale as 'en' | 'uk') || 'en'),
    );
    obs.observe(el, { attributes: true, attributeFilter: ['data-chrome-locale'] });
    return () => obs.disconnect();
  }, []);
  // Content glosses only (A1 pedagogy + EN chrome). Practice chrome is pure
  // chromeLocale via ChromeText/ChromeDual — never slash-dual (#5503).
  const showEnglishSubtitles = learnerLevel === 'A1' || chromeLocale === 'en';

  // D10: the Words-of-the-Day zone's source line names the active deck. `null`
  // for 'all' (and for a stale/deleted deck id) falls back to the plain title.
  const activeDeckTitles = useMemo(() => {
    if (selectedDeckFilter === 'all') return null;
    if (selectedDeckFilter === 'virtual_teacher_lesson') {
      return { uk: 'Відібрана добірка', en: 'Curated Deck' };
    }
    const title = customSets.find((s) => s.id === selectedDeckFilter)?.title;
    return title ? { uk: title, en: title } : null;
  }, [selectedDeckFilter, customSets]);

  const matchedSelectedRatingRef = useRef<PracticeRating | null>(null);
  const matchingTargetOutcomeRef = useRef<CompletionOutcome | null>(null);

  // Reset all per-item feedback/lock state. Shared by the selection-change effect and
  // `advancePending` so a wrong answer that re-surfaces the SAME item (a lapsed card the
  // selector picks again — same `itemId`, so the effect does not re-fire) still starts
  // clean: no stale lock, cloze input/feedback, or parked outcome.
  const resetItemFeedback = useCallback(() => {
    setAnswerLocked(false);
    setClozeInput('');
    setClozeFeedback(null);
    setClozeAttemptRecorded(false);
    setClozeCaseMissCount(0);
    clozeCaseMissOutcomeRef.current = null;
    setHeritageFeedback(null);
    setParonymFeedback(null);
    setStressSelectedPosition(null);
    setParadigmSelectedLabel(null);
    setParonymSelectedLabel(null);
    setHeritageSelectedLabel(null);
    setPendingOutcome(null);
    pendingOutcomeRef.current = null;
    matchedSelectedRatingRef.current = null;
    matchingTargetOutcomeRef.current = null;
  }, []);

  useEffect(() => {
    if (didInitRef.current) return;
    didInitRef.current = true;

    const state = loadState();
    setStreak(readStreak());
    setMastered(masteredCount(MASTERED_THRESHOLD));
    setDailyNewCount(readNewCardsDailyState().count);
    setReviewLog([...state.reviews]);

    if (state.flags.storageFull) {
      setStorageWarning(SRS_STORAGE_FULL_WARNING);
    } else if (state.flags.storageWriteFailed || state.flags.corrupt || state.flags.migrationFailed) {
      setStorageWarning('Прогрес призупинено, доки сховище браузера не стане доступним.');
    } else if (state.flags.clockJump) {
      setStorageWarning('Час повторення може бути неточним: змінився годинник пристрою.');
    }

    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const target = params.get('lemmaId');
      if (target) {
        // Keep #4744's single reactive auto-start path: initialize the resolved focus,
        // then let the focusedLemmaId effect below create the session exactly once.
        clearPracticeSessionSnapshots();
        setResumeSnapshots({});
        void initializeFocusedPractice(target);
      } else {
        const snapshots = readPracticeSessionSnapshots();
        const identity = currentSessionIdentity();
        const resumableSnapshots = Object.fromEntries(
          Object.entries(snapshots).filter(([, snapshot]) =>
            isPracticeSessionResumable(snapshot, Date.now(), identity),
          ),
        ) as PracticeSessionSnapshots;
        setResumeSnapshots(resumableSnapshots);
      }
    }
  }, []);

  useEffect(() => {
    const normalized = normalizeInitialDeck(initialDeck);
    if (normalized) {
      setDeck(normalized);
      setClozeLoaded(hasLoadedDrillShards(normalized));
    }
  }, [initialDeck]);

  useEffect(() => {
    const isAutoStartTrigger = autoStart || Boolean(focusedLemmaId);
    if (!isAutoStartTrigger || !deck || plannedTotal > 0) return;

    if (focusedLemmaId) {
      // Lemma deep-link: only that word, and never identity cloze (blank = the
      // same citation form the learner already knows they are drilling — e.g.
      // «новий» practice filling «___ рік»). Case drills stay (inflect the form).
      const filtered = stripIdentityClozeForLemmaFocus(deck, focusedLemmaId);
      const alreadyFocused =
        deck.index.length === filtered.index.length &&
        deck.index.every((item) => item.lemmaId === focusedLemmaId);
      const clozeAlreadyStripped =
        alreadyFocused &&
        filtered.index.every((item) => {
          const current = deck.index.find((row) => row.lemmaId === item.lemmaId);
          return (
            current &&
            current.clozeIds.join('\0') === item.clozeIds.join('\0') &&
            current.modes.join('\0') === item.modes.join('\0')
          );
        });
      if (!clozeAlreadyStripped) {
        setDeck(filtered);
        return;
      }
    }

    const plan = computeSessionScope(
      sessionScopeIndexForMode(filterIndexByDeckFilter(deck.index, deckLemmaKeySet), mode),
      sessionBudget,
      { dailyNewCount },
    );
    resetSessionTracking(plan, sessionBudget);

    // Persist an initial snapshot for this newly started session so it is resumable.
    const nextSeed = makePracticeSessionSeed();
    setSessionSeed(nextSeed);
    sessionStartedAtRef.current = Date.now();
    const seededHistory = seedCrossSessionHistory(new Date());
    setHistory(seededHistory);
    const reviewSlots = sessionBudget === 'until-zero' ? plan.dueReviews : Math.min(plan.dueReviews, sessionBudget);
    const snapshot: PracticeSessionSnapshot = {
      sessionSeed: nextSeed,
      history: seededHistory,
      budget: sessionBudget,
      completed: 0,
      modeFilter: mode,
      level: learnerLevel,
      deckId: selectedDeckFilter,
      dateSeed: dateSeed(new Date()),
      startedAt: sessionStartedAtRef.current,
      extensionUsed: 0,
      sessionNewIntroduced: 0,
      plannedReviews: reviewSlots,
      plannedNew: plan.plannedNew,
      plannedTotal: plan.plannedTotal,
      reviewsCompleted: 0,
      unresolvedCardKeys: [],
    };
    writePracticeSessionSnapshot(mode, snapshot);
    setResumeSnapshots((snapshots) => ({ ...snapshots, [mode]: snapshot }));
  }, [
    autoStart,
    deck,
    deckLemmaKeySet,
    dailyNewCount,
    focusedLemmaId,
    learnerLevel,
    mode,
    plannedTotal,
    sessionBudget,
  ]);

  useEffect(() => {
    const page = document.querySelector('.lexicon-practice-page');
    if (!page) return undefined;
    if (sessionPhase === 'active') {
      page.setAttribute('data-in-session', 'true');
    } else {
      page.removeAttribute('data-in-session');
    }
    return () => page.removeAttribute('data-in-session');
  }, [sessionPhase]);

  // §6b: the weak-area chips are derived from `reviewLog` and only surface on the idle
  // home. Re-derive the log from storage every time we (re)enter idle so the chips reflect
  // the JUST-finished session's ratings — the in-session `refreshProgress` updates apply to
  // the active React tree, but a return to idle from summary/«Додому» must re-read the
  // persisted log so a newly-fixed (or newly-weak) case is shown or dropped immediately.
  useEffect(() => {
    if (!didInitRef.current || sessionPhase !== 'idle') return;
    setReviewLog([...loadState().reviews]);
  }, [sessionPhase]);

  // Eager-load ONLY the lightweight per-level index shards on mount (and on a
  // pre-session level change) so the «До повторення» tile + today ring reflect the
  // learner's real SRS due-count immediately — the most motivating number on the
  // home, and the reason a returning learner opens this page. The heavy
  // lexeme/cloze shards stay lazy until a mode actually starts (ensureDeck). Once a
  // full deck is loaded its own `index` supersedes this. The `cancelled` flag drops
  // a stale fetch when the learner switches level before it resolves.
  useEffect(() => {
    if (deck) {
      setDueIndex(null);
      return;
    }
    let cancelled = false;
    void (async () => {
      try {
        const batches = await Promise.all(
          levelsForPractice().map(async (shardLevel) => {
            const url = `${shardBaseUrl}/practice-index.${shardLevel}.json`;
            try {
              const shard = await getShardJson<PracticeIndexShard>(url, shardJsonCacheRef.current);
              return shard.items ?? [];
            } catch {
              return [];
            }
          }),
        );
        if (!cancelled) setDueIndex(batches.flat());
      } catch {
        if (!cancelled) setDueIndex(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [deck, learnerLevel, shardBaseUrl]);

  // D2 (design delta 2026-07-26): the Words-of-the-Day zone renders the SAME 12
  // lemmas as /words-of-the-day/ — pickDaily(prioritizeByLearnerLevel(pool, level),
  // dateSeed(now), 12) over /lexicon/daily-pool.json. This is recomputed fresh
  // from (pool, level, date) on every run rather than reused from a persisted
  // snapshot, so there is no stale cache to silently pin the carousel on one
  // word across days (confirmed live bug: борщ every visit, while the page
  // itself showed a rotating 12). Loads lexeme cores only for the levels
  // represented among today's picks so the preview rows have verified
  // lemma/gloss/pos data. The daily pool and practice-core shards are built
  // independently, so an orphaned pool row is normalized into a displayable
  // preview card from its verified pool metadata rather than rendering as —.
  //
  // D10 (amendment, 2026-07-27): 'All Words' keeps the above unchanged. Any other
  // deck filter draws the daily picks FROM THAT DECK instead — pickDaily(deckPool,
  // dateSeed(now) + deckSeed(deckId), 12) — so the featured zone (and its default
  // session) react to the learner's deck choice, not just the atlas-global pool.
  //
  // #6132: the operator's complaint was the SAME 12 every session that day, with no
  // way to see a different set without waiting for UTC midnight. `dailyReRollCount`
  // (persisted per calendar day) folds into the seed via `reRollSeed` — a re-roll tap
  // still produces a deterministic, testable draw, it just adds a third seed term.
  useEffect(() => {
    if (sessionPhase !== 'idle') return;

    // #6146: defends against the midnight timer not having fired yet (e.g. this effect
    // re-runs from an unrelated dependency change in the first seconds of a new day) —
    // re-check the rollover here too rather than trusting the timer alone. Bail this run;
    // the reset below re-triggers the effect (dailyReRollCount is a dependency) with the
    // correct day-zero count.
    const currentDateKey = todayKey();
    if (dailyReRollDateRef.current !== currentDateKey) {
      dailyReRollDateRef.current = currentDateKey;
      if (dailyReRollCount !== 0) {
        setDailyReRollCount(0);
        return;
      }
    }

    let cancelled = false;
    setDailySnapshotLoading(true);

    void (async () => {
      try {
        const now = new Date();
        const dateKey = todayKey(now);
        const state = loadState();
        const indexSource = deck?.index ?? dueIndex ?? [];
        const deckLemmaKeys = resolveDeckLemmaKeys(selectedDeckFilter, customSets);

        let picks: DailyWord[] = [];
        let representedLevels: Set<string>;

        if (deckLemmaKeys === null) {
          const pool = await getShardJson<DailyWord[]>(
            '/lexicon/daily-pool.json',
            shardJsonCacheRef.current,
          );
          const eligiblePool = prioritizeByLearnerLevel(pool, learnerLevel);
          picks = pickDaily(
            eligiblePool,
            dateSeed(now) + reRollSeed(dailyReRollCount),
            DAILY_PRACTICE_DECK_SIZE,
          );

          // Fetch lexeme cores only for levels represented among today's picks —
          // or all selected-level cores for the defined fallback when the daily
          // pool is empty.
          const levelsForDailyPreview = picks.length > 0
            ? picks.map((word) => word.cefr)
            : levelsForPractice();
          representedLevels = new Set(
            levelsForDailyPreview.filter((cefr): cefr is string => Boolean(cefr)),
          );
        } else {
          // A deck's words can sit at any level (or none — an unverified custom
          // import). Resolve its keys across the learner's complete accessible
          // range used for atlas-global picks. That gives level-less custom keys
          // their verified metadata without treating a missing CEFR as A1.
          representedLevels = new Set<string>(levelsForPractice());
        }

        // The atlas branch can skip this fetch once `deck` already covers the
        // learner's levels. The deck-scoped branch cannot: `deck` only gets
        // per-lemma coverage for the ACTIVE deck filter when a drill mode has
        // loaded cloze (`ensureDeckCustomSetCoverage`), which the idle setup
        // screen has often never triggered — so it fetches independently.
        const levelEntries = deck && deckLemmaKeys === null
          ? []
          : await Promise.all(
              Array.from(representedLevels).map(async (level) => {
                try {
                  const [lexemeShard, clozeShard] = await Promise.all([
                    getShardJson<PracticeLexemeShard>(
                      `${shardBaseUrl}/practice-lexemes.${level}.json`,
                      shardJsonCacheRef.current,
                    ),
                    getShardJson<PracticeClozeShard>(
                      `${shardBaseUrl}/practice-cloze.${level}.json`,
                      shardJsonCacheRef.current,
                    ).catch(() => null),
                  ]);
                  return {
                    lexemes: lexemeShard.lexemes ?? [],
                    cloze: clozeShard?.cloze ?? [],
                  };
                } catch {
                  return { lexemes: [], cloze: [] };
                }
              }),
            );

        if (cancelled) return;
        const merged = new Map<string, PracticeLexeme>();
        for (const entry of deck?.lexemes ?? []) {
          merged.set(entry.lemmaId, entry);
        }
        for (const entry of levelEntries.flatMap((batch) => batch.lexemes)) {
          merged.set(entry.lemmaId, entry);
        }
        const lexemes = addDailyExamples(merged, [
          ...(deck?.cloze ?? []),
          ...levelEntries.flatMap((batch) => batch.cloze),
        ]);
        // Both the preview and the live session use this one resolver. It skips
        // Atlas entirely when practice cores already cover the selected deck,
        // otherwise it probes only the relevant search-prefix shards.
        const deckKeyResolutions = deckLemmaKeys === null
          ? new Map<string, DeckKeyResolution>()
          : await resolveDeckKeyMetadata(
              deckLemmaKeys,
              Array.from(lexemes.values()),
              shardJsonCacheRef.current,
            );

        let displayablePicks: DailyWord[];
        if (deckLemmaKeys !== null) {
          // Case-insensitive lookup, matching `deckFilterAllowsLemma`'s own
          // lemmaId-or-lemma comparison — deck keys are free-form learner input.
          const lexemesByLower = new Map<string, PracticeLexeme>();
          for (const entry of lexemes.values()) {
            lexemesByLower.set(entry.lemmaId.toLowerCase(), entry);
            lexemesByLower.set(entry.lemma.toLowerCase(), entry);
          }
          const deckPool: DailyWord[] = deckLemmaKeys.map((key) => {
            const match = lexemes.get(key) ?? lexemesByLower.get(key.toLowerCase()) ?? null;
            const cleanKey = cleanDeckKey(key);
            const atlasMatch = deckKeyResolutions.get(key)?.atlas ?? null;
            // Practice lexemes are richer than the search index. If neither
            // source recognizes a deck key, preserve the unlinked orphan card.
            return {
              lemma: match?.lemma ?? atlasMatch?.lemma ?? cleanKey,
              slug: match?.lemmaId ?? atlasMatch?.slug ?? key,
              gloss: match?.gloss ?? atlasMatch?.gloss ?? cleanKey,
              hasAtlasEntry: Boolean(match ?? atlasMatch),
              cefr: match?.cefr ?? atlasMatch?.cefr ?? undefined,
              pos: match?.pos ?? undefined,
              example: match?.example ?? undefined,
              exampleEn: match?.exampleEn ?? undefined,
            };
          });
          displayablePicks = pickDaily(
            deckPool,
            dateSeed(now) + deckSeed(selectedDeckFilter) + reRollSeed(dailyReRollCount),
            DAILY_PRACTICE_DECK_SIZE,
          );
        } else {
          for (const word of picks) {
            if (lexemes.has(word.slug)) continue;
            // The daily pool is itself a verified learner-facing source. Preserve
            // its unified pick even when the independently generated practice
            // shard lacks that lemma, using the metadata available on the row.
            lexemes.set(word.slug, {
              lemmaId: word.slug,
              lemma: word.lemma,
              lemmaPlain: word.lemma,
              ipa: null,
              gloss: word.gloss ?? word.lemma,
              pos: null,
              cefr: word.cefr ?? null,
              heritage: null,
              severity: null,
              paradigm: { cases: {} },
            });
          }
          // A genuinely empty daily pool has no unified pick set. In that case,
          // deterministically use the selected level's curated practice cores
          // rather than render an empty daily card.
          const fallbackPool: DailyWord[] = Array.from(lexemes.values()).map((lexeme) => ({
            lemma: lexeme.lemma,
            slug: lexeme.lemmaId,
            gloss: lexeme.gloss,
            hasAtlasEntry: true,
            cefr: lexeme.cefr ?? undefined,
          }));
          displayablePicks = picks.length > 0
            ? picks
            : pickDaily(fallbackPool, dateSeed(now) + reRollSeed(dailyReRollCount), DAILY_PRACTICE_DECK_SIZE);
        }

        const snapshot: DailyPracticeDeckSnapshot = {
          version: 2,
          date: dateKey,
          level: learnerLevel,
          deckVersion: deckLemmaKeys !== null ? selectedDeckFilter : 'daily-pool',
          createdAt: now.getTime(),
          items: displayablePicks.map((word) => ({
            lemmaId: word.slug,
            origin: classifyDailyPracticeOrigin(word.slug, indexSource, state.cards, now),
            lemma: word.lemma,
            gloss: word.gloss,
            hasAtlasEntry: word.hasAtlasEntry ?? true,
            cefr: word.cefr ?? null,
            pos: word.pos ?? null,
            example: word.example ?? null,
            exampleEn: word.exampleEn ?? null,
            exampleProvenance: word.exampleProvenance ?? null,
            etymology: word.etymology ?? null,
          })),
        };

        if (cancelled) return;
        setDailyLexemes(lexemes);
        setDailySnapshot(snapshot);
      } catch {
        if (!cancelled) setDailySnapshot(null);
      } finally {
        if (!cancelled) setDailySnapshotLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [
    deck?.index,
    deck?.lexemes,
    deck?.cloze,
    dueIndex,
    learnerLevel,
    sessionPhase,
    shardBaseUrl,
    selectedDeckFilter,
    customSets,
    dailyReRollCount,
  ]);

  const indexForStats = (deck?.index ?? dueIndex ?? []).filter(
    (item) => !focusedLemmaId || item.lemmaId === focusedLemmaId
  );

  // #6132 mode honesty: the lightweight index shard (`dueIndex`, or `deck.index` once
  // loaded) already carries each lemma's available modes, so the mode grid can show a
  // real per-mode count for the ACTIVE deck filter before the learner ever taps a card
  // — instead of mixed silently collapsing toward whichever modes happen to have
  // content and leaving an empty tap as the only way to discover a mode has nothing.
  const modeCounts = useMemo(() => {
    const filtered = filterIndexByDeckFilter(indexForStats, deckLemmaKeySet);
    const counts: Partial<Record<VisiblePracticeModeFilter, number>> = { mixed: filtered.length };
    for (const visibleMode of MODE_CARD_ORDER) {
      if (visibleMode === 'mixed') continue;
      counts[visibleMode] = filtered.filter((item) => item.modes.includes(visibleMode)).length;
    }
    return counts;
  }, [deckLemmaKeySet, indexForStats]);
  // P0-3: a mode is only disabled once the index has actually loaded and confirms
  // zero content — not during the transient pre-load tick where every count is 0.
  // A real custom deck's synthesized items (`ensureDeckCustomSetCoverage`) only exist
  // on the full `deck` built by `ensureDeck()` — the lightweight idle `dueIndex` never
  // carries them — so for a custom deck, wait for `deck` itself rather than trusting
  // a `dueIndex`-only count of 0 that would otherwise disable every mode forever.
  const isCustomDeckSelected = selectedDeckFilter !== 'all' && selectedDeckFilter !== 'virtual_teacher_lesson';
  const modeDataLoaded = isCustomDeckSelected ? deck !== null : deck !== null || dueIndex !== null;

  const sessionPoolConstraints = useMemo(
    () =>
      buildSessionPoolConstraintState({
        plannedReviews,
        reviewsCompleted,
        sessionNewIntroduced,
        dailyNewCount,
      }),
    [dailyNewCount, plannedReviews, reviewsCompleted, sessionNewIntroduced],
  );

  const poolFilter = useCallback(
    (candidate: PracticeSelection) => {
      if (!sessionPoolAllowsCandidate(candidate, sessionPoolConstraints)) return false;
      // A weak-area focus session narrows the pool to items matching the tapped
      // weakness on top of the normal §6b session constraints (no parallel path).
      if (focusWeakness && !matchesWeakness(candidate, focusWeakness)) return false;
      return true;
    },
    [focusWeakness, sessionPoolConstraints],
  );

  // Pass a deck-scoped index into the selector, rather than constructing every
  // candidate and rejecting it later in poolFilter. The wrapper is memoized by the
  // loaded deck and active key-set, so FSRS revision ticks still refresh due state
  // without rebuilding the full all-level candidate universe for curated/custom decks.
  const selectionDeck = useMemo(() => {
    if (!deck || !deckLemmaKeySet) return deck;
    const index = filterIndexByDeckFilter(deck.index, deckLemmaKeySet);
    return index.length === deck.index.length ? deck : { ...deck, index };
  }, [deck, deckLemmaKeySet]);

  const weakChips = useMemo(() => weakCaseChips(reviewLog), [reviewLog]);

  const selection = useMemo(() => {
    if (!selectionDeck || sessionPhase !== 'active') return null;
    const fresh = selectNextPracticeItem(selectionDeck, {
      history,
      modeFilter: mode,
      now: new Date(),
      sessionSeed,
      poolFilter: sessionPhase === 'active' ? poolFilter : undefined,
    });
    // Stabilize in-flight selection across live merges from background level shards.
    // The selector cache (per deck identity) produces a new pool, but we keep the exact
    // prior selection object (for same history length) so the user is not yanked mid-item
    // and #4740/#4744 flows are unperturbed. Once history advances on complete, fresh pick
    // uses the grown pool.
    const committed = committedSelectionRef.current;
    if (
      committed &&
      committed.historyLen === history.length &&
      fresh &&
      fresh.itemId !== committed.selection.itemId &&
      itemIdPresentInDeck(selectionDeck, committed.selection.itemId)
    ) {
      return committed.selection;
    }
    return fresh;
  }, [history, mode, poolFilter, revision, selectionDeck, sessionPhase, sessionSeed]);

  // Pin the board for the life of the selection to avoid mid-board changes.
  const pairsRef = useRef<{ itemId: string; pairs: ReturnType<typeof matchingPairs> } | null>(null);
  const pairs = useMemo(() => {
    if (!selection || selection.mode !== 'matching' || !deck) return [];
    if (pairsRef.current && pairsRef.current.itemId === selection.itemId) {
      return pairsRef.current.pairs;
    }
    const computed = matchingPairs(selection, deck, learnerLevel);
    pairsRef.current = { itemId: selection.itemId, pairs: computed };
    return computed;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [learnerLevel, selection?.itemId]);

  useEffect(() => {
    resetItemFeedback();
    if (selection) {
      // Record for stabilization across future deck swaps (bg merges).
      committedSelectionRef.current = { selection, historyLen: history.length };
      window.setTimeout(() => stageRef.current?.focus(), 0);
    }
  }, [selection?.itemId, resetItemFeedback]);

  // Rate the selected lemma if matched but never completed (due to session abort/unmount)
  useEffect(() => {
    const prevSelection = selection;
    return () => {
      if (matchedSelectedRatingRef.current && prevSelection) {
        try {
          rateCard(
            prevSelection.lemma.lemmaId,
            prevSelection.mode,
            matchedSelectedRatingRef.current,
            new Date(),
            {
              blankCase: prevSelection.cloze?.blankCase,
              heritageKind: prevSelection.heritage?.kind,
            }
          );
        } catch (e) {
          // ignore or handle storage warning
        }
        matchedSelectedRatingRef.current = null;
      }
    };
  }, [selection]);

  const handleMatchingMatch = useCallback((pairIndex: number, rating: PracticeRating) => {
    const pair = pairs[pairIndex];
    if (!pair || !pair.lemmaId) return;

    if (pairIndex === 0) {
      if (sessionCompleted === 0) {
        matchedSelectedRatingRef.current = rating;
      } else {
        if (selection) {
          const outcome = recordReview(selection, rating);
          matchingTargetOutcomeRef.current = outcome;
        }
      }
    } else {
      try {
        rateCard(pair.lemmaId, 'matching', rating, new Date());
      } catch (e) {
        setStorageWarning('Прогрес призупинено, доки сховище браузера не стане доступним.');
      }
    }
  }, [pairs, selection, sessionCompleted]);

  // While an answer dwells, Enter is a second way to advance (alongside the
  // «Далі →» button) — the disabled option buttons blur to <body>, so we listen at
  // the window level rather than on the stage. Bail when focus is already on an
  // interactive control (Atlas links, «← Додому», the «Далі →» button itself).
  useEffect(() => {
    if (!pendingOutcome) return undefined;
    const handleEnter = (event: KeyboardEvent) => {
      if (event.key !== 'Enter') return;
      const target = event.target as HTMLElement | null;
      if (target?.closest?.('button, a, input, textarea, select, [role="button"]')) return;
      event.preventDefault();
      advancePending();
    };
    window.addEventListener('keydown', handleEnter);
    return () => window.removeEventListener('keydown', handleEnter);
  }, [pendingOutcome, selection]);

  // Answer dwell: move focus to «Далі →» so keyboard/SR users keep their place
  // after the clicked (now-disabled) option blurs to <body>. D6 moved Далі into the
  // top status row specifically so it is reachable without scrolling — but a tall
  // prompt (e.g. rating buttons below the fold) can leave the page scrolled down
  // from answering, and a plain `.focus()` only nudges the nearest edge into view.
  // Reset scroll to the top explicitly so the status row (and Далі) is guaranteed
  // visible. `useLayoutEffect` (not `useEffect`) runs before the browser paints, so
  // there is no visible scroll-jump flash after the result renders.
  useLayoutEffect(() => {
    if (!pendingOutcome) return;
    window.scrollTo({ top: 0, behavior: 'auto' });
    advanceButtonRef.current?.focus({ preventScroll: true });
  }, [pendingOutcome]);

  useEffect(() => {
    if (sessionPhase !== 'active') return;
    const previousTitle = document.title;
    document.title = `${MODE_META[visiblePracticeMode(mode)].title} — Практика слів дня`;
    return () => {
      document.title = previousTitle;
    };
  }, [mode, sessionPhase]);

  async function ensureDeck(
    includeCloze = shouldLoadCloze(mode),
    options: { level?: CefrLevel; force?: boolean; deckFilter?: string } = {},
  ): Promise<PracticeDeckData | null> {
    // `level`/`force`/`deckFilter` are passed explicitly on a level or deck change so we
    // don't read the stale `learnerLevel`/`deck`/`selectedDeckFilter` closures before
    // their state updates have flushed.
    const level = options.level ?? learnerLevel;
    const force = options.force ?? false;
    const deckFilter = options.deckFilter ?? selectedDeckFilter;
    const current = force ? null : deck;
    if (current && (!includeCloze || clozeLoaded)) {
      setError(null);
      return current;
    }
    const requestId = ++deckRequestId.current;
    setLoading(true);
    setError(null);
    try {
      let nextDeck = current;
      let nextClozeLoaded = clozeLoaded;
      const levels = levelsForPractice();
      const targetLevel = levels.includes(level) ? level : levels[0]!;
      const otherLevels = levels.filter((lv) => lv !== targetLevel);
      const needDrills = includeCloze && (force || !clozeLoaded);
      const deckLemmaKeys = resolveDeckLemmaKeys(deckFilter, customSets);
      let deckKeyResolutions: Map<string, DeckKeyResolution> | null = null;

      if (!nextDeck) {
        // PROGRESSIVE: Load the SELECTED level's core shards (index + lexemes) FIRST.
        // The session can start on this deck immediately; every other published level
        // is backgrounded because the learner level is a preference, not a cap.
        const indexUrl = `${shardBaseUrl}/practice-index.${targetLevel}.json`;
        const lexUrl = `${shardBaseUrl}/practice-lexemes.${targetLevel}.json`;
        const [indexShard, lexemeShard] = await Promise.all([
          getShardJson<PracticeIndexShard>(indexUrl, shardJsonCacheRef.current),
          getShardJson<PracticeLexemeShard>(lexUrl, shardJsonCacheRef.current),
        ]);
        nextDeck = combinePracticeShards(indexShard, lexemeShard);
        if (deckLemmaKeys !== null) {
          deckKeyResolutions = await resolveDeckKeyMetadata(
            deckLemmaKeys,
            nextDeck.lexemes ?? [],
            shardJsonCacheRef.current,
          );
          nextDeck = ensureDeckCustomSetCoverage(nextDeck, deckLemmaKeys, deckKeyResolutions);
        }
        // The first committed deck must already contain Atlas-enriched custom
        // entries; background growth may safely extend it after this.
        if (deckRequestId.current === requestId) setDeck(nextDeck);

        // Fire-and-forget background load of the remaining *cores*. Merge into live pool
        // as they arrive; selector cache per deck identity (#4656) receives the new deck
        // object and recomputes candidates for the grown pool on next select (stabilized
        // for in-flight item).
        if (otherLevels.length > 0) {
          void (async () => {
            const bgId = deckRequestId.current;
            const otherCores = (
              await Promise.all(
                otherLevels.map(async (lv) => {
                  try {
                    const iUrl = `${shardBaseUrl}/practice-index.${lv}.json`;
                    const lUrl = `${shardBaseUrl}/practice-lexemes.${lv}.json`;
                    const [i, l] = await Promise.all([
                      getShardJson<PracticeIndexShard>(iUrl, shardJsonCacheRef.current),
                      getShardJson<PracticeLexemeShard>(lUrl, shardJsonCacheRef.current),
                    ]);
                    return combinePracticeShards(i, l);
                  } catch {
                    // Failed background shard degrades gracefully; session continues.
                    return null;
                  }
                }),
              )
            ).filter((d): d is PracticeDeckData => d !== null);
            if (deckRequestId.current !== bgId || otherCores.length === 0) return;
            setDeck((prev) => {
              if (!prev) return mergeDecks(otherCores, level);
              return extendWithLowerDecks(prev, otherCores);
            });
          })();
        }
      }

      if (needDrills) {
        // Load drill shards for the *selected* level (may block this call if mode requires
        // them, e.g. initialMode=cloze or mixed). Other drill shards are background.
        // This also defers drill-kind shards for basic modes (flashcards etc) until a
        // drill mode surfaces (optional path kept clean).
        const drillUrls = [
          `${shardBaseUrl}/practice-cloze.${targetLevel}.json`,
          `${shardBaseUrl}/practice-stress.${targetLevel}.json`,
          `${shardBaseUrl}/practice-classify.${targetLevel}.json`,
          `${shardBaseUrl}/practice-paradigm.${targetLevel}.json`,
          `${shardBaseUrl}/practice-synonym.${targetLevel}.json`,
          `${shardBaseUrl}/practice-paronym.${targetLevel}.json`,
          `${shardBaseUrl}/practice-heritage.${targetLevel}.json`,
          `${shardBaseUrl}/practice-antonym.${targetLevel}.json`,
        ];
        const drillResults = await Promise.all(
          drillUrls.map((u) =>
            getShardJson<any>(u, shardJsonCacheRef.current).catch(() => ({})),
          ),
        );
        const [clozeR, stressR, classifyR, paradigmR, synonymR, paronymR, heritageR, antonymR] = drillResults;
        nextDeck = {
          ...nextDeck!,
          cloze: [...(nextDeck!.cloze ?? []), ...((clozeR as { cloze?: PracticeClozeItem[] }).cloze ?? [])],
          stress: [...(nextDeck!.stress ?? []), ...((stressR as { stress?: any[] }).stress ?? [])],
          classify: [...(nextDeck!.classify ?? []), ...((classifyR as { classify?: any[] }).classify ?? [])],
          paradigm: [...(nextDeck!.paradigm ?? []), ...((paradigmR as { paradigm?: any[] }).paradigm ?? [])],
          synonym: [...(nextDeck!.synonym ?? []), ...((synonymR as { synonym?: any[] }).synonym ?? [])],
          paronym: [...(nextDeck!.paronym ?? []), ...((paronymR as { paronym?: any[] }).paronym ?? [])],
          heritage: [...(nextDeck!.heritage ?? []), ...((heritageR as { heritage?: any[] }).heritage ?? [])],
          antonym: [...(nextDeck!.antonym ?? []), ...((antonymR as { antonym?: any[] }).antonym ?? [])],
        };

        // Merge teacher deck pre-generated cloze items if active
        if (deckFilter === 'virtual_teacher_lesson') {
          try {
            const teacherClozeShard = await getShardJson<{ cloze?: PracticeClozeItem[] }>(
              `${shardBaseUrl}/practice-cloze.teacher.json`,
              shardJsonCacheRef.current,
            );
            if (teacherClozeShard?.cloze && teacherClozeShard.cloze.length > 0) {
              nextDeck = {
                ...nextDeck!,
                cloze: [
                  ...(nextDeck!.cloze ?? []),
                  ...filterTeacherClozeItems(teacherClozeShard.cloze),
                ],
              };
            }
          } catch {
            // Degrades gracefully if teacher cloze shard is missing
          }
        }

        // Merge custom set document cloze items if active
        if (deckFilter !== 'all' && deckFilter !== 'virtual_teacher_lesson') {
          const activeSet = customSets.find((s) => s.id === deckFilter);
          if (activeSet) {
            if (activeSet.cloze_items && activeSet.cloze_items.length > 0) {
              nextDeck = {
                ...nextDeck,
                cloze: [...(nextDeck.cloze ?? []), ...activeSet.cloze_items],
              };
            }
          }
        }

        nextClozeLoaded = true;

        // Background drills for the remaining published levels (merge live when they land).
        if (otherLevels.length > 0) {
          void (async () => {
            const bgId = deckRequestId.current;
            const otherDrillBatches = await Promise.all(
              otherLevels.map(async (lv) => {
                const urls = [
                  `${shardBaseUrl}/practice-cloze.${lv}.json`,
                  `${shardBaseUrl}/practice-stress.${lv}.json`,
                  `${shardBaseUrl}/practice-classify.${lv}.json`,
                  `${shardBaseUrl}/practice-paradigm.${lv}.json`,
                  `${shardBaseUrl}/practice-synonym.${lv}.json`,
                  `${shardBaseUrl}/practice-paronym.${lv}.json`,
                  `${shardBaseUrl}/practice-heritage.${lv}.json`,
                  `${shardBaseUrl}/practice-antonym.${lv}.json`,
                ];
                const rs = await Promise.all(
                  urls.map((u) => getShardJson<any>(u, shardJsonCacheRef.current).catch(() => ({}))),
                );
                return {
                  cloze: (rs[0] as { cloze?: PracticeClozeItem[] }).cloze ?? [],
                  stress: (rs[1] as { stress?: any[] }).stress ?? [],
                  classify: (rs[2] as { classify?: any[] }).classify ?? [],
                  paradigm: (rs[3] as { paradigm?: any[] }).paradigm ?? [],
                  synonym: (rs[4] as { synonym?: any[] }).synonym ?? [],
                  paronym: (rs[5] as { paronym?: any[] }).paronym ?? [],
                  heritage: (rs[6] as { heritage?: any[] }).heritage ?? [],
                  antonym: (rs[7] as { antonym?: any[] }).antonym ?? [],
                };
              }),
            );
            if (deckRequestId.current !== bgId) return;
            setDeck((prev) => {
              if (!prev) return prev;
              return {
                ...prev,
                cloze: [...(prev.cloze ?? []), ...otherDrillBatches.flatMap((b) => b.cloze)],
                stress: [...(prev.stress ?? []), ...otherDrillBatches.flatMap((b) => b.stress)],
                classify: [...(prev.classify ?? []), ...otherDrillBatches.flatMap((b) => b.classify)],
                paradigm: [...(prev.paradigm ?? []), ...otherDrillBatches.flatMap((b) => b.paradigm)],
                synonym: [...(prev.synonym ?? []), ...otherDrillBatches.flatMap((b) => b.synonym)],
                paronym: [...(prev.paronym ?? []), ...otherDrillBatches.flatMap((b) => b.paronym)],
                heritage: [...(prev.heritage ?? []), ...otherDrillBatches.flatMap((b) => b.heritage)],
                antonym: [...(prev.antonym ?? []), ...otherDrillBatches.flatMap((b) => b.antonym)],
              };
            });
          })();
        }
      }

      // A custom/teacher deck may contain a valid Atlas word outside the
      // practice-core lexemes. Resolve it before committing the deck, so the
      // actual session (including a flashcard-only session) receives the same
      // real slug and card-safe gloss as the idle preview.
      if (deckLemmaKeys !== null) {
        deckKeyResolutions ??= await resolveDeckKeyMetadata(
          deckLemmaKeys,
          nextDeck!.lexemes ?? [],
          shardJsonCacheRef.current,
        );
        // Re-run the synchronous merge after a custom cloze document was added,
        // so its IDs attach to the already-resolved custom index item.
        nextDeck = ensureDeckCustomSetCoverage(nextDeck!, deckLemmaKeys, deckKeyResolutions);
      }

      // Ignore the result if a newer fetch (e.g. a later level switch) has superseded this one.
      if (deckRequestId.current !== requestId) return nextDeck!;
      setDeck(nextDeck!);
      setClozeLoaded(nextClozeLoaded);
      setError(null);
      return nextDeck!;
    } catch {
      if (deckRequestId.current === requestId) {
        setError(CHROME_STRINGS.uk['practice.loadError']);
      }
      return null;
    } finally {
      if (deckRequestId.current === requestId) setLoading(false);
    }
  }

  async function initializeFocusedPractice(target: string) {
    setLoading(true);
    setError(null);
    setFocusLookupMiss(false);

    try {
      const initialDeck = deck;
      const initialMatch = initialDeck
        ? resolvePracticeIndexItem(initialDeck.index, target)
        : null;
      let matchedIndexItem = initialMatch;
      if (!matchedIndexItem) {
        const indexShards = await Promise.all(
          levelsForPractice().map(async (level) => {
            try {
              return await getShardJson<PracticeIndexShard>(
                `${shardBaseUrl}/practice-index.${level}.json`,
                shardJsonCacheRef.current,
              );
            } catch (err) {
              // A 404 means the level is not published yet: skip it and keep
              // scanning the remaining shards — the focused lemma may live in
              // another published level. Any other fault is a real load failure
              // and must surface as the fetch-error fallback.
              if ((err as { status?: number } | null)?.status === 404) return null;
              throw err;
            }
          }),
        );
        matchedIndexItem = resolvePracticeIndexItem(
          indexShards.flatMap((shard) => shard?.items ?? []),
          target,
        );
      }

      if (!matchedIndexItem) {
        setFocusedLemmaId(null);
        setFocusLookupMiss(true);
        setSessionPhase('idle');
        return;
      }

      // The cumulative index is small. A null lexical CEFR is transported in
      // the first published shard; keep that transport fact separate from the
      // missing lexical metadata rather than assigning it A1.
      const matchedLevel = matchedIndexItem.cefr
        ? normalizeCefrLevel(matchedIndexItem.cefr, learnerLevel)
        : levelsForPractice()[0]!;
      let loadedDeck = initialMatch
        ? initialDeck
        : await ensureDeck(shouldLoadCloze('mixed'), { level: matchedLevel, force: true });
      if (!loadedDeck && !initialMatch) {
        // A failed shared shard promise is evicted by getShardJson. Retry the focused
        // deck once so a transient init failure cannot outlive the successful exercise.
        loadedDeck = await ensureDeck(shouldLoadCloze('mixed'), { level: matchedLevel, force: true });
      }
      if (!loadedDeck) return;

      const resolvedItem = resolvePracticeIndexItem(loadedDeck.index, target);
      if (!resolvedItem) {
        // An index/lexeme deploy mismatch is a real data-load fault, not a word that
        // simply is not in the learner's available practice pool.
        setError(CHROME_STRINGS.uk['practice.loadError']);
        setSessionPhase('idle');
        return;
      }

      setError(null);
      setFocusedLemmaId(resolvedItem.lemmaId);
      setMode('mixed');
      setSessionBudget(10);
      setSessionPhase('active');
    } catch {
      // Only request failures reach the load fallback. A completed lookup miss remains
      // a usable hub with a concise bilingual notice.
      setError(CHROME_STRINGS.uk['practice.loadError']);
      setSessionPhase('idle');
    } finally {
      setLoading(false);
    }
  }

  function resetSessionTracking(plan: SessionScopeStats, budget: SessionBudget) {
    const reviewSlots =
      budget === 'until-zero' ? plan.dueReviews : Math.min(plan.dueReviews, budget);
    setSessionPlan(plan);
    setPlannedReviews(reviewSlots);
    setPlannedTotal(plan.plannedTotal);
    setSessionCompleted(0);
    setReviewsCompleted(0);
    setSessionNewIntroduced(0);
    setExtensionUsed(0);
    setUnresolvedCardKeys(new Set());
    setDeferredLemmas([]);
    setSessionCorrect(0);
    setSessionLapsed(0);
    setAdvancedToReview([]);
  }

  function buildSessionSnapshot(
    overrides: Partial<PracticeSessionSnapshot> = {},
  ): PracticeSessionSnapshot {
    return {
      sessionSeed,
      history,
      budget: sessionBudget,
      completed: sessionCompleted,
      modeFilter: mode,
      level: learnerLevel,
      deckId: selectedDeckFilter,
      dateSeed: dateSeed(new Date()),
      startedAt: sessionStartedAtRef.current,
      extensionUsed,
      sessionNewIntroduced,
      plannedReviews,
      plannedNew: sessionPlan?.plannedNew ?? 0,
      plannedTotal,
      reviewsCompleted,
      unresolvedCardKeys: [...unresolvedCardKeys],
      ...overrides,
    };
  }

  function clearResumeSnapshot(nextMode: PracticeModeFilter) {
    writePracticeSessionSnapshot(nextMode, null);
    setResumeSnapshots((snapshots) => {
      const nextSnapshots = { ...snapshots };
      delete nextSnapshots[nextMode];
      return nextSnapshots;
    });
  }

  function clearResumeSnapshots() {
    clearPracticeSessionSnapshots();
    setResumeSnapshots({});
  }

  function persistSessionSnapshot(
    overrides: Partial<PracticeSessionSnapshot> = {},
    options: { force?: boolean } = {},
  ) {
    if (!options.force && sessionPhase !== 'active') return;
    const snapshot = buildSessionSnapshot(overrides);
    writePracticeSessionSnapshot(mode, snapshot);
    setResumeSnapshots((snapshots) => ({ ...snapshots, [mode]: snapshot }));
  }

  function effectiveSessionTarget(): number {
    return plannedTotal + extensionUsed;
  }

  function openSummary(deferred: PracticeLexeme[] = deferredLemmas) {
    if (deferred.length) setDeferredLemmas(deferred);
    clearResumeSnapshot(mode);
    setSessionPhase('summary');
  }

  async function beginSession(
    nextMode: PracticeModeFilter = 'mixed',
    budget: SessionBudget = sessionBudget,
    resume?: PracticeSessionSnapshot,
    // §6b: the weak-area focus is passed EXPLICITLY here (never read from `focusWeakness`
    // setState timing before the call) so the empty-pool probe below and the session's
    // `poolFilter` see the same, deterministic value. A resumed session passes no focus,
    // so `focusWeakness` is always cleared on resume — the focus is session-transient by
    // design and is intentionally NOT persisted to `PracticeSessionSnapshot`.
    focus: WeakArea | null = null,
    // F1 (PR #5837 review): an accepted level/deck switch passes the ACCEPTED values here
    // explicitly, so the deck load and the persisted snapshot use them directly instead of
    // racing the `learnerLevel`/`selectedDeckFilter` state updates that triggered this call.
    overrides?: { level?: CefrLevel; deckFilter?: string },
  ) {
    // A pinned selection is only valid within the session that created it. Without this
    // reset, returning home with an empty history lets the selector reuse the previous
    // mode's card when the learner starts a different mode.
    committedSelectionRef.current = null;
    setMode(nextMode);
    setSessionBudget(budget);
    setError(null);
    setFocusLookupMiss(false);
    const effectiveLevel = overrides?.level ?? learnerLevel;
    const effectiveDeckFilter = overrides?.deckFilter ?? selectedDeckFilter;
    let loadedDeck = await ensureDeck(
      shouldLoadCloze(nextMode),
      overrides ? { level: overrides.level, deckFilter: overrides.deckFilter, force: true } : undefined,
    );
    if (!loadedDeck) return;
    if (focusedLemmaId) {
      loadedDeck = {
        ...loadedDeck,
        index: loadedDeck.index.filter((item) => item.lemmaId === focusedLemmaId),
      };
      setDeck(loadedDeck);
    }
    // A focus session must never strand the learner in an itemless «active» phase. Probe
    // the loaded deck under the SAME combined filter the session would apply (weakness +
    // §6b pool constraints); if nothing matches, clear the focus, surface the idle notice,
    // and stay on the home rather than opening an empty session.
    if (
      focus &&
      !selectNextPracticeItem(loadedDeck, {
        modeFilter: nextMode,
        now: new Date(),
        sessionSeed: makePracticeSessionSeed(),
        poolFilter: (candidate) =>
          sessionPoolAllowsCandidate(candidate, sessionPoolConstraints) &&
          matchesWeakness(candidate, focus),
      })
    ) {
      setFocusWeakness(null);
      setFeedback({
        uk: 'Немає вправ для цього фокуса — колода оновиться після практики',
        en: 'No exercises for this focus — the deck will refresh after practice',
      });
      clearResumeSnapshot(nextMode);
      setSessionPhase('idle');
      return;
    }
    setFocusWeakness(focus);
    // A session is starting for real — drop any stale idle notice (e.g. the empty-focus
    // message) so the active status line reads «Сесія …» cleanly.
    setFeedback(null);
    const index = sessionScopeIndexForMode(
      filterIndexByDeckFilter(
        loadedDeck.index,
        resolveDeckLemmaKeySet(effectiveDeckFilter, customSets),
      ),
      nextMode,
    );
    const plan = computeSessionScope(index, budget, { dailyNewCount });
    const nextSeed = resume?.sessionSeed ?? makePracticeSessionSeed();
    const seededHistory = resume ? resume.history : seedCrossSessionHistory(new Date());
    if (resume) {
      sessionStartedAtRef.current = resume.startedAt;
      setSessionSeed(nextSeed);
      setHistory(seededHistory);
      setSessionCompleted(resume.completed);
      setPlannedReviews(resume.plannedReviews ?? plan.dueReviews);
      setPlannedTotal(resume.plannedTotal ?? plan.plannedTotal);
      setReviewsCompleted(resume.reviewsCompleted ?? 0);
      setSessionNewIntroduced(resume.sessionNewIntroduced ?? 0);
      setExtensionUsed(resume.extensionUsed ?? 0);
      setUnresolvedCardKeys(new Set(resume.unresolvedCardKeys ?? []));
      setSessionPlan(plan);
    } else {
      sessionStartedAtRef.current = Date.now();
      setSessionSeed(nextSeed);
      setHistory(seededHistory);
      resetSessionTracking(plan, budget);
    }
    setSessionPhase('active');
    const reviewSlots = budget === 'until-zero' ? plan.dueReviews : Math.min(plan.dueReviews, budget);
    const snapshot: PracticeSessionSnapshot = {
      sessionSeed: nextSeed,
      history: seededHistory,
      budget,
      completed: resume?.completed ?? 0,
      modeFilter: nextMode,
      level: effectiveLevel,
      deckId: effectiveDeckFilter,
      dateSeed: dateSeed(new Date()),
      startedAt: sessionStartedAtRef.current,
      extensionUsed: resume?.extensionUsed ?? 0,
      sessionNewIntroduced: resume?.sessionNewIntroduced ?? 0,
      plannedReviews: resume?.plannedReviews ?? reviewSlots,
      plannedNew: plan.plannedNew,
      plannedTotal: resume?.plannedTotal ?? plan.plannedTotal,
      reviewsCompleted: resume?.reviewsCompleted ?? 0,
      unresolvedCardKeys: resume?.unresolvedCardKeys ?? [],
    };
    writePracticeSessionSnapshot(nextMode, snapshot);
    setResumeSnapshots((snapshots) => ({ ...snapshots, [nextMode]: snapshot }));
  }

  async function startSession(
    budget: SessionBudget = 20,
    nextMode: PracticeModeFilter = 'mixed',
    focus: WeakArea | null = null,
    overrides?: { level?: CefrLevel; deckFilter?: string },
  ) {
    clearResumeSnapshot(nextMode);
    await beginSession(nextMode, budget, undefined, focus, overrides);
  }

  function currentSessionIdentity(): PracticeSessionIdentity {
    return { level: learnerLevel, deckId: selectedDeckFilter, dateSeed: dateSeed(new Date()) };
  }

  async function resumeSession(nextMode: PracticeModeFilter) {
    const snapshot = resumeSnapshots[nextMode];
    if (
      !snapshot ||
      snapshot.modeFilter !== nextMode ||
      !isPracticeSessionResumable(snapshot, Date.now(), currentSessionIdentity())
    ) {
      return;
    }
    // A resumed session starts with NO focus: the weakness is session-transient (never
    // persisted to the snapshot), so `beginSession(..., focus=null)` clears `focusWeakness`.
    await beginSession(nextMode, snapshot.budget, snapshot, null);
  }

  /**
   * D5: «Почати наново» discards the resumable snapshot outright (no confirmation
   * modal — sessions are cheap) and seeds a brand-new session for it instead.
   */
  async function restartMixedSession() {
    clearResumeSnapshots();
    setFocusWeakness(null);
    await startSession(sessionBudget, 'mixed');
  }

  async function startFocusMode(nextMode: PracticeModeFilter) {
    await startSession(sessionBudget, nextMode, null);
  }

  /**
   * §6b: tapping a weak-area chip starts a focus session filtered to that weakness.
   * The weakness is passed EXPLICITLY through `startSession` → `beginSession` (not via a
   * pre-start `setFocusWeakness`), so the empty-pool probe and the session `poolFilter`
   * share one deterministic value and an itemless focus never strands the learner.
   */
  async function startWeakAreaFocus(weakness: WeakArea) {
    await startSession(sessionBudget, focusModeForWeakness(weakness), weakness);
  }

  function clearFocus() {
    setFocusedLemmaId(null);
    setFocusLookupMiss(false);
    setFocusWeakness(null);
    setDeck(null);
    setDueIndex(null);
    committedSelectionRef.current = null;
    clearResumeSnapshots();
    setSessionPhase('idle');
  }

  async function changeLevel(nextLevel: CefrLevel) {
    if (nextLevel === learnerLevel || !publishedLevels.has(nextLevel)) return;
    setLearnerLevel(nextLevel);
    writeLearnerLevel(nextLevel);
    setClozeLoaded(false);
    setHistory([]);
    committedSelectionRef.current = null;
    clearResumeSnapshots();
    if (sessionPhase === 'active') {
      await ensureDeck(shouldLoadCloze(mode), { level: nextLevel, force: true });
    } else {
      setDeck(null);
      setSessionPhase('idle');
    }
  }

  // D7: a session in progress (active) or resumable (idle with a stored snapshot) is
  // "law" until the learner explicitly agrees to trade it in — so a deck/level tap
  // parks the choice in `pendingDeckSwitch` and asks, instead of silently recomputing
  // out from under a session the learner may still want to finish.
  function hasActiveOrResumableSession(): boolean {
    return sessionPhase === 'active' || Boolean(resumeSnapshots.mixed);
  }

  function requestDeckSwitch(nextDeckFilter: string) {
    if (nextDeckFilter === selectedDeckFilter) return;
    if (hasActiveOrResumableSession()) {
      setPendingDeckSwitch({ kind: 'deck', value: nextDeckFilter });
      return;
    }
    setSelectedDeckFilter(nextDeckFilter);
  }

  function requestLevelSwitch(nextLevel: CefrLevel) {
    if (nextLevel === learnerLevel || !publishedLevels.has(nextLevel)) return;
    if (hasActiveOrResumableSession()) {
      setPendingDeckSwitch({ kind: 'level', value: nextLevel });
      return;
    }
    void changeLevel(nextLevel);
  }

  function declineDeckSwitch() {
    setPendingDeckSwitch(null);
  }

  async function acceptDeckSwitch() {
    if (!pendingDeckSwitch) return;
    const change = pendingDeckSwitch;
    setPendingDeckSwitch(null);
    setSessionPhase('idle');
    clearResumeSnapshots();
    setClozeLoaded(false);
    setHistory([]);
    committedSelectionRef.current = null;
    // F1 (PR #5837 review): the accepted level/deck is threaded through `startSession` as
    // an explicit override rather than relied upon via `learnerLevel`/`selectedDeckFilter`
    // state — those setters below schedule a re-render but do NOT update the closures this
    // same synchronous call chain reads, so without the override the session that follows
    // would silently load the PRIOR level/deck while the UI claims the accepted one.
    const overrides: { level?: CefrLevel; deckFilter?: string } =
      change.kind === 'deck' ? { deckFilter: change.value } : { level: change.value };
    if (change.kind === 'deck') {
      setSelectedDeckFilter(change.value);
    } else {
      setLearnerLevel(change.value);
      writeLearnerLevel(change.value);
    }
    await startSession(sessionBudget, 'mixed', null, overrides);
  }

  function refreshProgress() {
    const state = loadState();
    setMastered(masteredCount(MASTERED_THRESHOLD));
    setReviewLog([...state.reviews]);
    if (state.flags.storageFull) {
      setStorageWarning(SRS_STORAGE_FULL_WARNING);
    } else if (state.flags.storageWriteFailed || state.flags.corrupt || state.flags.migrationFailed) {
      setStorageWarning('Прогрес призупинено, доки сховище браузера не стане доступним.');
    } else if (storageWarning === SRS_STORAGE_FULL_WARNING) {
      setStorageWarning(null);
    }
    setRevision((value) => value + 1);
  }

  function recordReview(
    current: PracticeSelection,
    rating: PracticeRating,
  ): { nextUnresolved: Set<string>; nextDeferred: PracticeLexeme[] } {
    const wasNew = isPracticeNewCard(current.cardState);
    const nextUnresolved = new Set(unresolvedCardKeys);
    let nextDeferred = [...deferredLemmas];
    try {
      rateCard(reviewLemmaId(current), current.mode, rating, new Date(), {
        blankCase: current.cloze?.blankCase,
        heritageKind: current.heritage?.kind,
      });
      setStreak(recordStreak());
      if (rating === 'good' || rating === 'easy') {
        setSessionCorrect((value) => value + 1);
      }
      if (rating === 'again') {
        setSessionLapsed((value) => value + 1);
      }
      if (wasNew && rating !== 'again') {
        const daily = readNewCardsDailyState();
        const nextDaily = { date: daily.date, count: daily.count + 1 };
        writeNewCardsDailyState(nextDaily);
        setDailyNewCount(nextDaily.count);
        setSessionNewIntroduced((value) => value + 1);
      }
      if (!wasNew) {
        setReviewsCompleted((value) => value + 1);
      }
      if (wasNew && (rating === 'good' || rating === 'easy')) {
        setAdvancedToReview((items) =>
          items.includes(current.lemma.lemma) ? items : [...items, current.lemma.lemma],
        );
      }
      if (rating === 'again') {
        nextUnresolved.add(current.cardKey);
        if (!nextDeferred.some((entry) => entry.lemmaId === current.lemma.lemmaId)) {
          nextDeferred = [...nextDeferred, current.lemma];
        }
      } else if (rating === 'good' || rating === 'easy') {
        if (nextUnresolved.delete(current.cardKey)) {
          nextDeferred = nextDeferred.filter((entry) => entry.lemmaId !== current.lemma.lemmaId);
        }
      }
      setUnresolvedCardKeys(nextUnresolved);
      setDeferredLemmas(nextDeferred);
      setFeedback({
        uk: `${current.lemma.lemma}: ${RATING_LABELS[rating].uk}`,
        en: `${current.lemma.lemma}: ${RATING_LABELS[rating].en}`,
      });
    } catch {
      setStorageWarning('Прогрес призупинено, доки сховище браузера не стане доступним.');
    }
    return { nextUnresolved, nextDeferred };
  }

  function completeSelection(
    current: PracticeSelection,
    outcome: { nextUnresolved: Set<string>; nextDeferred: PracticeLexeme[] },
  ) {
    setHistory((items) => [...items.slice(-49), historyFromSelection(current)]);
    const nextCompleted = sessionCompleted + 1;
    setSessionCompleted(nextCompleted);
    setCompletedToday((value) => value + 1);
    refreshProgress();
    persistSessionSnapshot({ completed: nextCompleted });
    const decision = resolveSessionCompletion({
      completed: nextCompleted,
      plannedTotal,
      extensionUsed,
      unresolvedCount: outcome.nextUnresolved.size,
    });
    if (decision === 'continue') return;
    if (decision === 'extend') {
      setExtensionUsed((value) => value + 1);
      return;
    }
    if (decision === 'summary-with-deferred') {
      openSummary(outcome.nextDeferred);
      return;
    }
    openSummary();
  }

  function rateAndComplete(current: PracticeSelection, rating: PracticeRating) {
    const outcome = recordReview(current, rating);
    completeSelection(current, outcome);
  }

  function handleFlashcardRating(rating: PracticeRating) {
    if (!selection) return;
    const outcome = recordReview(selection, rating);
    setAnswerLocked(true);
    pendingOutcomeRef.current = outcome;
    setPendingOutcome(outcome);
  }

  function handleMatchingComplete() {
    if (!selection) return;
    let outcome: CompletionOutcome | null = null;
    if (sessionCompleted === 0) {
      const rating = matchedSelectedRatingRef.current || 'good';
      matchedSelectedRatingRef.current = null;
      outcome = recordReview(selection, rating);
    } else {
      outcome = matchingTargetOutcomeRef.current;
      matchingTargetOutcomeRef.current = null;
      if (!outcome) {
        outcome = recordReview(selection, 'good');
      }
    }
    setAnswerLocked(true);
    pendingOutcomeRef.current = outcome;
    setPendingOutcome(outcome);
  }

  /** Complete the parked selection once the learner chooses to advance. */
  function advancePending() {
    // Claim the outcome via the ref FIRST so a second synchronous invocation (a rapid
    // double-Enter, or Enter racing a «Далі» click) reads null and no-ops — the closed-over
    // `pendingOutcome` state is stale within the same tick and cannot guard against this.
    const outcome = pendingOutcomeRef.current;
    if (!outcome || !selection) return;
    pendingOutcomeRef.current = null;
    resetItemFeedback();
    completeSelection(selection, outcome);
  }

  function handleStressSelect(position: number) {
    if (!selection?.stress || answerLocked) return;
    setStressSelectedPosition(position);
    const correct = position === selection.stress.stressIndex;
    const rating = correct ? 'good' : 'again';
    const outcome = recordReview(selection, rating);
    setFeedback({
      uk: `${selection.stress.unstressed}: ${correct ? 'Правильно' : 'Ще раз'}`,
      en: `${selection.stress.unstressed}: ${correct ? 'Correct' : 'Again'}`,
    });
    setAnswerLocked(true);
    pendingOutcomeRef.current = outcome;
    setPendingOutcome(outcome);
  }

  function handleChoice(option: ChoiceOption) {
    if (!selection || answerLocked) return;
    const rating = option.correct ? 'good' : 'again';
    const outcome = recordReview(selection, rating);
    const nextHeritageFeedback = selection.heritage
      ? heritageFeedbackFor(selection.heritage, option)
      : null;
    const nextParonymFeedback = selection.paronym
      ? paronymFeedbackFor(selection.paronym, option)
      : null;
    setAnswerLocked(true);
    if (selection.paradigm) setParadigmSelectedLabel(option.label);
    if (selection.paronym) setParonymSelectedLabel(option.label);
    if (selection.heritage) setHeritageSelectedLabel(option.label);
    setHeritageFeedback(nextHeritageFeedback);
    setParonymFeedback(nextParonymFeedback);
    setFeedback({
      uk: option.correct ? `${selection.lemma.lemma}: Правильно` : `${selection.lemma.lemma}: Ще раз`,
      en: option.correct ? `${selection.lemma.lemma}: Correct` : `${selection.lemma.lemma}: Again`,
    });
    // Correct and wrong both dwell — never auto-advance; learner continues via «Далі →» / Enter.
    pendingOutcomeRef.current = outcome;
    setPendingOutcome(outcome);
  }

  function submitCloze(value: string, source: 'typed' | 'chip') {
    if (!selection?.cloze) return;
    const answer = value.trim();
    if (source === 'chip') {
      // Suggestions populate the input; only the explicit Check action commits.
      if (!answerLocked) setClozeInput(answer);
      return;
    }
    if (answerLocked || !answer) return;
    const cloze = selection.cloze;
    const correct = czNorm(answer) === czNorm(cloze.form);
    const caseMiss = isWrongCaseAnswer(answer, selection.lemma, cloze);

    if (correct) {
      const outcome = clozeAttemptRecorded
        ? { nextUnresolved: new Set(unresolvedCardKeys), nextDeferred: [...deferredLemmas] }
        : recordReview(selection, 'good');
      setClozeFeedback({
        kind: 'correct',
        textUk: `✓ ${cloze.form} (${cloze.caseRule.caseLabel})`,
        textEn: `✓ ${cloze.form} (${translateGrammarTerm(cloze.caseRule.caseLabel)})`,
      });
      setAnswerLocked(true);
      pendingOutcomeRef.current = outcome;
      setPendingOutcome(outcome);
      return;
    }

    if (caseMiss) {
      if (!clozeAttemptRecorded) {
        clozeCaseMissOutcomeRef.current = recordReview(selection, 'hard');
        setClozeAttemptRecorded(true);
      }
      const nextCaseMissCount = clozeCaseMissCount + 1;
      setClozeCaseMissCount(nextCaseMissCount);
      const exhausted = nextCaseMissCount >= 2;
      // Keep the typed value (select it, don't clear it) — a chip tap that put the
      // right lemma in the box must not be destroyed on the first case-miss.
      setClozeFeedback({
        kind: 'case-miss',
        textUk: `→ Правильне слово. Тепер постав його ${casePhraseAccusative(cloze.caseRule.caseLabel)}: ${cloze.caseRule.feedback}`,
        textEn: `→ Correct word. Now put it in the ${translateGrammarTerm(cloze.caseRule.caseLabel)}: ${cloze.caseRule.feedback}`,
      });
      if (exhausted) {
        setAnswerLocked(true);
        if (clozeCaseMissOutcomeRef.current) {
          pendingOutcomeRef.current = clozeCaseMissOutcomeRef.current;
          setPendingOutcome(clozeCaseMissOutcomeRef.current);
        }
      }
      return;
    }

    if (!clozeAttemptRecorded) {
      const outcome = recordReview(selection, 'again');
      setClozeAttemptRecorded(true);
      setClozeFeedback({
        kind: 'wrong-word',
        textUk: '✗ Не те слово',
        textEn: '✗ Not that word',
      });
      setAnswerLocked(true);
      pendingOutcomeRef.current = outcome;
      setPendingOutcome(outcome);
      return;
    }

    setClozeFeedback({
      kind: 'wrong-word',
      textUk: '✗ Не те слово',
      textEn: '✗ Not that word',
    });
    setAnswerLocked(true);
  }

  const homeScope = useMemo(
    () =>
      indexForStats.length
        ? computeSessionScope(
            filterIndexByDeckFilter(indexForStats, deckLemmaKeySet),
            sessionBudget,
            { dailyNewCount },
          )
        : null,
    [dailyNewCount, deckLemmaKeySet, indexForStats, sessionBudget],
  );
  const dailyRows = useMemo(
    () =>
      dailySnapshot
        ? deriveDailyPracticeRows(dailySnapshot, null, reviewLog, new Date())
        : { pendingDue: [], pendingNew: [], done: [] },
    [dailySnapshot, reviewLog],
  );
  const todayDenominator = useMemo(
    () =>
      indexForStats.length
        ? computeTodayRingDenominator(indexForStats, { dailyNewCount })
        : 0,
    [completedToday, dailyNewCount, indexForStats, revision],
  );
  const todayPct =
    todayDenominator > 0
      ? Math.min(100, (completedToday / todayDenominator) * 100)
      : completedToday > 0
        ? 100
        : 0;
  const todayRingStyle = { '--pct': String(todayPct) } as CSSProperties;
  const stageMode: PracticeModeFilter = selection?.mode ?? mode;
  const visibleStageMode = visiblePracticeMode(stageMode);
  const stageTitleUk =
    mode === 'mixed' && selection && visibleStageMode !== 'mixed'
      ? `Мікс · ${MODE_META[visibleStageMode].title}`
      : MODE_META[visibleStageMode].title;
  const stageTitleEn =
    mode === 'mixed' && selection && visibleStageMode !== 'mixed'
      ? `Mixed · ${MODE_META[visibleStageMode].en}`
      : MODE_META[visibleStageMode].en;
  const progressLabel = `${sessionCompleted}/${effectiveSessionTarget()}`;
  const dailySnapshotIds = useMemo(
    () => new Set(dailySnapshot?.items.map((item) => item.lemmaId) ?? []),
    [dailySnapshot],
  );
  const summaryStats: SessionSummaryStats = {
    correct: sessionCorrect,
    lapsed: sessionLapsed,
    advancedToReview: advancedToReview.filter((lemma) =>
      dailySnapshotIds.size === 0
        ? true
        : Array.from(dailyLexemes.values()).some(
            (entry) => entry.lemma === lemma && dailySnapshotIds.has(entry.lemmaId),
          ),
    ),
    streak: streak.current,
    nextDueLabel: formatNextDueLabel(nextDuePreviewTime()),
    deferredLemmas: deferredLemmas.filter((entry) => dailySnapshotIds.has(entry.lemmaId)),
  };

  function finishPractice() {
    setSessionPhase('idle');
    setFocusWeakness(null);
    setHistory([]);
    setDeck(null);
    setClozeLoaded(false);
  }

  // P0-2: every active-phase empty state gets the same three-part block instead of
  // a text-only dead end — what happened, the single best next action as a primary
  // button, and (where it makes sense) up to two real-content secondary modes.
  function renderPracticeEmptyState(
    messageKey: ChromeKey,
    testId: string,
    secondaryModes: VisiblePracticeModeFilter[] = [],
  ) {
    const primaryIsFlashcards = messageKey === 'practice.clozePreparing' && (modeCounts.flashcards ?? 0) > 0;
    return (
      <div className="practice-empty-state" data-testid={testId}>
        <p className="lexicon-practice-muted">
          <PracticeChromeLabel k={messageKey} />
        </p>
        <button
          type="button"
          className="btn btn-accent practice-empty-primary"
          data-testid={`${testId}-primary`}
          onClick={() => {
            if (primaryIsFlashcards) {
              void startFocusMode('flashcards');
            } else {
              finishPractice();
            }
          }}
        >
          <PracticeChromeLabel k={primaryIsFlashcards ? 'practice.startFlashcardsCta' : 'practice.backToModes'} />
        </button>
        {secondaryModes.length > 0 ? (
          <div className="practice-empty-secondary">
            {secondaryModes
              .filter((secondaryMode) => (modeCounts[secondaryMode] ?? 0) > 0)
              .map((secondaryMode) => {
                const meta = MODE_META[secondaryMode];
                const count = modeCounts[secondaryMode] ?? 0;
                return (
                  <button
                    key={secondaryMode}
                    type="button"
                    className="btn practice-empty-secondary-btn"
                    onClick={() => void startFocusMode(secondaryMode)}
                  >
                    <ChromeDual uk={`${meta.title} · ${count}`} en={`${meta.en} · ${count}`} />
                  </button>
                );
              })}
          </div>
        ) : null}
      </div>
    );
  }

  return (
    <section className="lexicon-practice" aria-label={CHROME_STRINGS[chromeLocale]['practice.ariaLabel']}>
      {sessionPhase !== 'idle' || feedback ? (
      <p className="lexicon-practice-status" aria-live="polite">
        {feedback ? (
          <PureLocalePracticeMessage uk={feedback.uk} en={feedback.en ?? feedback.uk} />
        ) : sessionPhase === 'active' ? (
          <>
            <PracticeChromeDual uk={`Сесія ${progressLabel}`} en={`Session ${progressLabel}`} />
          </>
        ) : (
          <>
            <PracticeChromeLabel k="practice.sessionComplete" />
          </>
        )}
      </p>
      ) : null}

      {storageWarning && (() => {
        const warn = translateStorageWarning(storageWarning);
        return warn ? (
          <p className="lexicon-practice-warning" role="alert">
            <PureLocalePracticeMessage uk={warn.uk} en={warn.en ?? warn.uk} />
          </p>
        ) : null;
      })()}

      {focusLookupMiss && (
        <p className="lexicon-practice-warning" role="status" data-testid="practice-lemma-missing">
          <PureLocalePracticeMessage
            uk={CHROME_STRINGS.uk['practice.poolMiss']}
            en={CHROME_STRINGS.en['practice.poolMiss']}
          />
        </p>
      )}

      {sessionPhase === 'idle' && (
        <>
          {focusedLemmaId && (
            <div
              className="k3-decks-wrapper shadow-sm rounded-xl p-3 my-2 bg-base-200/50"
              data-testid="practice-dashboard-decks"
              style={{
                background: 'var(--lu-surface-raised)',
                border: '1px solid var(--lu-teal, #146e78)',
                padding: '0.75rem 1rem',
                borderRadius: '8px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                color: 'var(--lu-text)',
                marginBottom: '0.5rem'
              }}
            >
              <span>
                🎯 <strong>
                  <PracticeChromeLabel k="practice.focusPractice" />
                </strong> «{focusedLemmaId}»
              </span>
              <button
                type="button"
                onClick={clearFocus}
                style={{
                  padding: '4px 8px',
                  fontSize: '0.8rem',
                  border: '1px solid var(--lu-border)',
                  borderRadius: '4px',
                  background: 'var(--lu-surface)',
                  color: 'var(--lu-text-muted)',
                  cursor: 'pointer'
                }}
              >
                <PracticeChromeLabel k="practice.clearFocus" />
              </button>
            </div>
          )}

          <div className="k3-practice-dashboard">
            <div className="k3-hero" data-testid="practice-dashboard-hero">
              <h1><ChromeText k="practice.heroTitle" /></h1>
              <p className="k3-hero-subtitle"><ChromeText k="practice.heroSubtitle" /></p>
              <p className="k3-hero-epigraph" lang="uk">
                «Мова — це серце народу: гине мова — гине народ» — Іван Огієнко
              </p>

              <div
                className="k3-levels"
                role="group"
                aria-label={CHROME_STRINGS[chromeLocale]['practice.level']}
              >
                <span className="k3-levels-label"><ChromeText k="practice.level" /></span>
                {CEFR_LEVELS.map((level) => {
                  const published = publishedLevels.has(level);
                  return (
                    <button
                      type="button"
                      key={level}
                      className={learnerLevel === level ? 'active' : ''}
                      aria-pressed={learnerLevel === level}
                      disabled={!published}
                      title={published ? undefined : CHROME_STRINGS[chromeLocale]['practice.c2Soon']}
                      onClick={() => requestLevelSwitch(level)}
                    >
                      {level}
                      {!published ? (
                        <span className="k3-level-soon"><ChromeText k="practice.c2Soon" /></span>
                      ) : null}
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="k3-stats" data-testid="practice-dashboard-stats" role="group" aria-label={CHROME_STRINGS[chromeLocale]['practice.stats']}>
              <div className="k3-stat">
                <span className="k3-stat-value">{dailyRows.pendingDue.length}</span>
                <span className="k3-stat-label"><ChromeText k="practice.statusDue" /></span>
              </div>
              <div className="k3-stat">
                <span className="k3-stat-value">{dailyRows.pendingNew.length}</span>
                <span className="k3-stat-label"><ChromeText k="practice.statusNew" /></span>
              </div>
              <div className="k3-stat">
                <span className="k3-stat-value">{dailyRows.done.length}</span>
                <span className="k3-stat-label"><ChromeText k="practice.statusDone" /></span>
              </div>
              <div className="k3-stat">
                <span className="k3-stat-value">🔥 {streak.current}</span>
                <span className="k3-stat-label"><ChromeText k="practice.streak" /></span>
              </div>
            </div>

            <div className="k3-words" data-testid="practice-dashboard-words">
              {dailySnapshotLoading || !dailySnapshot ? (
                <div className="practice-daily-deck k3-words-loading" data-testid="practice-daily-deck-loading">
                  <div className="daily-deck-header">
                    <h2>
                      {activeDeckTitles ? (
                        <ChromeDual
                          uk={`Слова дня — ${activeDeckTitles.uk}`}
                          en={`Words of the day — ${activeDeckTitles.en}`}
                        />
                      ) : (
                        <ChromeText k="practice.wordsTitle" />
                      )}
                    </h2>
                  </div>
                  <div className="daily-deck-preview-shell">
                    <div className="flashcard daily-preview-card">
                      <div className="flashcard-inner">
                        <div className="flashcard-front">
                          <span className="flashcard-word">—</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  <details className="daily-deck-details">
                    <summary><ChromeText k="practice.showWords" /></summary>
                  </details>
                </div>
              ) : (
                <PracticeDailyDeck
                  snapshot={dailySnapshot}
                  rows={dailyRows}
                  lexemes={dailyLexemes}
                  atlasLemmaHref={atlasLemmaHref}
                  chromeLocale={chromeLocale}
                  learnerLevel={learnerLevel}
                  deckTitleUk={activeDeckTitles?.uk}
                  deckTitleEn={activeDeckTitles?.en}
                  onReRoll={reRollDailyPicks}
                />
              )}
            </div>

            <div className="k3-session" data-testid="practice-dashboard-session">
              <div className="k3-session-overview">
                <div
                  className="k3-session-size"
                  role="group"
                  aria-label={CHROME_STRINGS[chromeLocale]['practice.sessionTitle']}
                >
                  <span className="k3-session-label"><ChromeText k="practice.sessionSizeLabel" /></span>
                  <div className="k3-session-budgets">
                    {([10, 20, 'until-zero'] as const).map((budget) => (
                      <button
                        key={String(budget)}
                        type="button"
                        className={sessionBudget === budget ? 'active' : ''}
                        aria-pressed={sessionBudget === budget}
                        data-testid={`practice-session-budget-${budget === 'until-zero' ? 'until-zero' : budget}`}
                        onClick={() => setSessionBudget(budget)}
                      >
                        <ChromeText
                          k={
                            budget === 10
                              ? 'practice.sessionSize10'
                              : budget === 20
                                ? 'practice.sessionSize20'
                                : 'practice.sessionSizeUntilZero'
                          }
                        />
                      </button>
                    ))}
                  </div>
                </div>
                {homeScope ? (
                  <p className="k3-session-scope" data-testid="practice-session-scope">
                    <ChromeDual
                      uk={`${homeScope.dueReviews} до повторення + ${homeScope.plannedNew} нових ≈ ${homeScope.estimatedMinutes} хв`}
                      en={`${homeScope.dueReviews} due + ${homeScope.plannedNew} new ≈ ${homeScope.estimatedMinutes} min`}
                    />
                  </p>
                ) : null}
              </div>
              <button
                type="button"
                className="btn btn-accent k3-session-primary"
                data-testid="practice-start-session"
                disabled={loading}
                onClick={() => {
                  setFocusWeakness(null);
                  if (resumeSnapshots.mixed) {
                    void resumeSession('mixed');
                  } else {
                    void startSession(sessionBudget, 'mixed');
                  }
                }}
              >
                <ChromeText k={resumeSnapshots.mixed ? 'practice.sessionResume' : 'practice.sessionStart'} />
              </button>
              {resumeSnapshots.mixed ? (
                <button
                  type="button"
                  className="btn k3-session-reset"
                  data-testid="practice-reset-session"
                  data-reset-mode="mixed"
                  onClick={() => void restartMixedSession()}
                >
                  <ChromeText k="practice.sessionRestart" />
                </button>
              ) : null}
            </div>

            <div className="k3-secondary" data-testid="practice-dashboard-secondary">
            {weakChips.length > 0 ? (
              <div className="lexicon-weak-areas" data-testid="practice-weak-areas">
                <div
                  className="lexicon-weak-chips"
                  role="group"
                  aria-label={CHROME_STRINGS[chromeLocale]['practice.weakAreas']}
                >
                  {weakChips.map((weakness) => (
                    <button
                      type="button"
                      key={`${weakness.dimension}:${weakness.key}`}
                      className="lexicon-weak-chip"
                      data-testid={`practice-weak-chip-${weakness.key}`}
                      onClick={() => void startWeakAreaFocus(weakness)}
                    >
                      {weakness.label}
                    </button>
                  ))}
                </div>
              </div>
            ) : null}

            <div className="k3-modes">
              <h2><ChromeText k="practice.modesTitle" /></h2>
              <p id="mode-detail-line" aria-live="polite" className="k3-mode-detail">
                {chromeLocale === 'uk'
                  ? MODE_META[hoveredMode ?? 'mixed'].description
                  : MODE_META[hoveredMode ?? 'mixed'].descriptionEn}
              </p>
              <div
                className="k3-mode-grid"
                role="group"
                aria-label={CHROME_STRINGS[chromeLocale]['practice.modesTitle']}
              >
                {MODE_CARD_ORDER.map((practiceMode) => {
                  const meta = MODE_META[practiceMode];
                  const modeCount = modeCounts[practiceMode] ?? 0;
                  const modeEmpty = practiceMode !== 'mixed' && modeDataLoaded && modeCount === 0;
                  return (
                    <button
                      key={practiceMode}
                      type="button"
                      className="k3-mode-card"
                      data-mode={practiceMode}
                      data-accent={meta.accent}
                      data-mode-count={modeCount}
                      data-mode-empty={modeEmpty ? 'true' : undefined}
                      disabled={modeEmpty}
                      aria-disabled={modeEmpty}
                      aria-describedby="mode-detail-line"
                      onMouseEnter={() => setHoveredMode(practiceMode)}
                      onMouseLeave={() => setHoveredMode(null)}
                      onFocus={() => setHoveredMode(practiceMode)}
                      onBlur={() => setHoveredMode(null)}
                      onClick={() => void startFocusMode(practiceMode)}
                    >
                      <span className="k3-mode-title">{chromeLocale === 'uk' ? meta.title : meta.en}</span>
                      <span className="k3-mode-step">{chromeLocale === 'uk' ? meta.step : meta.stepEn}</span>
                      <span className="k3-mode-desc">
                        {chromeLocale === 'uk' ? meta.description : meta.descriptionEn}
                      </span>
                      {modeEmpty ? (
                        <span className="k3-mode-empty-note">
                          <ChromeText k="practice.modeNoExercises" />
                        </span>
                      ) : null}
                      <span
                        className="k3-mode-count"
                        data-testid={`practice-mode-count-${practiceMode}`}
                      >
                        <span aria-hidden="true">{modeCount}</span>
                        <span className="sr-only">
                          {modeCountAccessibleSuffix(modeCount, chromeLocale)}
                        </span>
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
            </div>
          </div>

          {/*
           * Opus P0-1: account sync and deck management are power-user actions, not
           * the first thing a learner should be asked to decide. They used to render
           * above the whole dashboard, pushing the primary Start/Resume CTA down and
           * putting the HARD-1/HARD-2 above-the-fold gates at risk. Folded here,
           * below the mode grid, behind the same disclosure pattern the page already
           * uses for secondary material.
           */}
          <details className="k3-practice-sources" data-testid="practice-secondary-tools">
            <summary><ChromeText k="practice.secondaryToolsTitle" /></summary>
            <div className="k3-practice-sources-content">
              <div className="k3-drive-sync-bar" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <button
                  type="button"
                  className="btn btn-sm"
                  style={{ background: 'var(--lu-accent-blue, #2563eb)', color: '#fff', borderRadius: '8px', padding: '0.4rem 0.8rem', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}
                  onClick={handleGoogleDriveSync}
                  disabled={isDriveSyncing}
                >
                  <span>☁️</span>
                  <span>{isDriveSyncing ? 'Синхронізація...' : 'Увійти та синхронізувати з Google Drive'}</span>
                </button>
                {driveSyncMsg ? <span style={{ fontSize: '0.85rem', color: 'var(--lu-text-muted)' }}>{driveSyncMsg}</span> : null}
              </div>

              <div className="k3-deck-filter-bar" style={{ margin: '1rem 0 0', padding: '0.75rem 1rem', background: 'var(--lu-bg-card, rgba(255,255,255,0.05))', borderRadius: '12px', border: '1px solid var(--lu-border, rgba(255,255,255,0.1))' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <span style={{ fontWeight: 'bold', fontSize: '0.95rem' }}>
                    {chromeLocale === 'uk' ? '📚 Колоди та добірки слів' : '📚 Word Decks & Collections'}
                  </span>
                  <button
                    type="button"
                    className="btn btn-sm btn-accent"
                    onClick={() => setShowCreateModal(true)}
                    style={{ fontSize: '0.8rem', padding: '0.25rem 0.6rem' }}
                  >
                    ⚙️ {chromeLocale === 'uk' ? 'Менеджер колод / Імпорт' : 'Manage Decks / Import'}
                  </button>
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                  <button
                    type="button"
                    className={`btn btn-sm ${selectedDeckFilter === 'all' ? 'btn-primary shadow-md' : 'btn-ghost'}`}
                    onClick={() => requestDeckSwitch('all')}
                    style={selectedDeckFilter === 'all' ? { border: '2px solid #3b82f6', fontWeight: 800 } : {}}
                  >
                    {selectedDeckFilter === 'all' ? '✓ ' : ''}🌐 {chromeLocale === 'uk' ? `Всі слова (${learnerLevel})` : `All Words (${learnerLevel})`}
                  </button>
                  <button
                    type="button"
                    className={`btn btn-sm ${selectedDeckFilter === 'virtual_teacher_lesson' ? 'btn-primary shadow-md' : 'btn-ghost'}`}
                    onClick={() => requestDeckSwitch('virtual_teacher_lesson')}
                    style={selectedDeckFilter === 'virtual_teacher_lesson' ? { border: '2px solid #3b82f6', fontWeight: 800 } : {}}
                  >
                    {selectedDeckFilter === 'virtual_teacher_lesson' ? '✓ ' : ''}🎓 {chromeLocale === 'uk' ? 'Відібрана добірка' : 'Curated Deck'}
                  </button>
                  {customSets.map((set) => (
                    <button
                      key={set.id}
                      type="button"
                      className={`btn btn-sm ${selectedDeckFilter === set.id ? 'btn-primary shadow-md' : 'btn-ghost'}`}
                      onClick={() => requestDeckSwitch(set.id)}
                      style={selectedDeckFilter === set.id ? { border: '2px solid #3b82f6', fontWeight: 800 } : {}}
                    >
                      {selectedDeckFilter === set.id ? '✓ ' : ''}⭐ {set.title} ({set.lemma_keys.length})
                    </button>
                  ))}
                </div>
                {pendingDeckSwitch ? (
                  <div className="k3-switch-offer" data-testid="practice-switch-session-offer" role="status">
                    <span><ChromeText k="practice.switchSessionOffer" /></span>
                    <div className="k3-switch-offer-actions">
                      <button
                        type="button"
                        className="btn btn-sm btn-accent"
                        data-testid="practice-switch-session-accept"
                        onClick={acceptDeckSwitch}
                      >
                        <ChromeText k="practice.switchSessionAccept" />
                      </button>
                      <button
                        type="button"
                        className="btn btn-sm"
                        data-testid="practice-switch-session-decline"
                        onClick={declineDeckSwitch}
                      >
                        <ChromeText k="practice.switchSessionDecline" />
                      </button>
                    </div>
                  </div>
                ) : null}
              </div>

              {showCreateModal ? (
                <LexiconCustomDeckManager
                  chromeLocale={chromeLocale}
                  activeDeckFilter={selectedDeckFilter}
                  shardBaseUrl={shardBaseUrl}
                  onSelectDeckFilter={(id) => {
                    // F2 (PR #5837 review): route through the same guarded switch flow as the
                    // deck-filter chips — the manager must offer a fresh session too, not
                    // silently swap the deck under an active/resumable one.
                    setCustomSets(readLocalCustomSets());
                    requestDeckSwitch(id);
                  }}
                  onClose={() => {
                    setShowCreateModal(false);
                    setCustomSets(readLocalCustomSets());
                  }}
                />
              ) : null}
            </div>
          </details>
        </>
      )}
      {loading && (
        <p className="lexicon-practice-muted">
          <PracticeChromeLabel k="practice.loading" />
        </p>
      )}
      {error && !selection && (
        <div className="lexicon-practice-fallback" data-testid="practice-fetch-error">
          <p className="lexicon-practice-warning">
            <PureLocalePracticeMessage
              uk={error}
              en={CHROME_STRINGS.en['practice.loadError']}
            />
          </p>
          <button type="button" className="btn btn-accent" onClick={() => window.location.reload()}>
            <ChromeText k="practice.retry" />
          </button>
        </div>
      )}

      {sessionPhase === 'summary' && (
        <PracticeSessionSummary
          stats={summaryStats}
          chromeLocale={chromeLocale}
          onAnotherSession={() => {
            // A fresh «another session» is never a focus session — startSession(focus=null)
            // clears any weakness so the next session is the full pool for `mode`.
            void startSession(sessionBudget, mode, null);
          }}
          onDone={finishPractice}
        />
      )}

      {sessionPhase === 'active' && (
        <div className="lexicon-practice-stage-shell">
          <div className="lexicon-practice-stage-bar">
            <button type="button" className="stage-back" onClick={finishPractice}>
              <PracticeChromeLabel k="practice.home" />
            </button>
            <h2>
              <PracticeChromeDual uk={stageTitleUk} en={stageTitleEn} />
            </h2>
            <span
              className="queue-pill"
              aria-label={`${CHROME_STRINGS[chromeLocale]['practice.progress']} ${progressLabel}`}
              data-testid="practice-session-progress"
            >
              {progressLabel}
            </span>
            {pendingOutcome ? (
              <button
                ref={advanceButtonRef}
                type="button"
                className="btn btn-accent queue-next-btn"
                data-testid="practice-advance-button"
                onClick={advancePending}
              >
                <PracticeChromeLabel k="practice.nextArrow" />
              </button>
            ) : null}
          </div>

          {deck && deck.index.length === 0 &&
            renderPracticeEmptyState('practice.noCards', 'practice-no-cards')}

          {deck && deck.index.length > 0 && (
            <div className="lexicon-practice-stage" ref={stageRef} tabIndex={-1}>
              {selection ? (
                <>
                  <PracticeItem
                    key={selection.cardKey}
                    selection={selection}
                    deck={deck}
                    pairs={pairs}
                    sessionSeed={sessionSeed}
                    answerLocked={answerLocked}
                    clozeInput={clozeInput}
                    clozeFeedback={clozeFeedback}
                    heritageFeedback={heritageFeedback}
                    paronymFeedback={paronymFeedback}
                    stressSelectedPosition={stressSelectedPosition}
                    paradigmSelectedLabel={paradigmSelectedLabel}
                    paronymSelectedLabel={paronymSelectedLabel}
                    heritageSelectedLabel={heritageSelectedLabel}
                    onClozeInput={setClozeInput}
                    onFlashcardRating={handleFlashcardRating}
                    onChoice={handleChoice}
                    onStressSelect={handleStressSelect}
                    onMatchingComplete={handleMatchingComplete}
                    onMatchingMatch={handleMatchingMatch}
                    onClozeSubmit={submitCloze}
                    onBackToModes={finishPractice}
                    showEnglishSubtitles={showEnglishSubtitles}
                    chromeLocale={chromeLocale}
                    learnerLevel={learnerLevel}
                  />
                </>
              ) : mode === 'cloze' && deck.cloze.length === 0 ? (
                renderPracticeEmptyState('practice.clozePreparing', 'practice-cloze-empty', ['matching', 'choice'])
              ) : mode === 'heritage' && (deck.heritage?.length ?? 0) === 0 ? (
                renderPracticeEmptyState('practice.heritagePreparing', 'practice-heritage-empty', ['flashcards', 'choice'])
              ) : mode === 'paronym' && (deck.paronym?.length ?? 0) === 0 ? (
                renderPracticeEmptyState('practice.paronymPreparing', 'practice-paronym-empty', ['flashcards', 'choice'])
              ) : (
                renderPracticeEmptyState('practice.allCaughtUp', 'practice-all-caught-up')
              )}
            </div>
          )}
        </div>
      )}
    </section>
  );
}

function formatNextDueLabel(nextDue: Date | null): { uk: string; en: string } | null {
  if (!nextDue) return null;
  const hours = nextDue.getHours().toString().padStart(2, '0');
  const minutes = nextDue.getMinutes().toString().padStart(2, '0');
  const remainingMs = nextDue.getTime() - Date.now();
  const remaining = Math.max(1, Math.ceil(remainingMs / (60 * 60 * 1000)));
  const hoursWord = uaPlural(remaining, { one: 'година', few: 'години', many: 'годин' });
  return {
    uk: `ще ${remaining} ${hoursWord} о ${hours}:${minutes}`,
    en: `in ${remaining}h at ${hours}:${minutes}`,
  };
}

function PracticeItem({
  selection,
  deck,
  pairs,
  sessionSeed,
  answerLocked,
  clozeInput,
  clozeFeedback,
  heritageFeedback,
  paronymFeedback,
  stressSelectedPosition,
  paradigmSelectedLabel,
  paronymSelectedLabel,
  heritageSelectedLabel,
  onClozeInput,
  onFlashcardRating,
  onChoice,
  onStressSelect,
  onMatchingComplete,
  onMatchingMatch,
  onClozeSubmit,
  onBackToModes,
  showEnglishSubtitles,
  chromeLocale,
  learnerLevel,
}: {
  selection: PracticeSelection;
  deck: PracticeDeckData;
  pairs: ReturnType<typeof matchingPairs>;
  sessionSeed: number;
  answerLocked: boolean;
  clozeInput: string;
  clozeFeedback: ClozeFeedback | null;
  heritageFeedback: HeritageFeedback | null;
  paronymFeedback: ParonymFeedback | null;
  stressSelectedPosition: number | null;
  paradigmSelectedLabel: string | null;
  paronymSelectedLabel: string | null;
  heritageSelectedLabel: string | null;
  onClozeInput(value: string): void;
  onFlashcardRating(rating: PracticeRating): void;
  onChoice(option: ChoiceOption): void;
  onStressSelect(position: number): void;
  onMatchingComplete(): void;
  onMatchingMatch?: (pairIndex: number, rating: PracticeRating) => void;
  onClozeSubmit(value: string, source: 'typed' | 'chip'): void;
  /** P0-2: option-build failures (empty matching/choice pools) get a real exit, not just prose. */
  onBackToModes(): void;
  showEnglishSubtitles: boolean;
  chromeLocale: 'en' | 'uk';
  learnerLevel: CefrLevel;
}) {
  const [matchingPromptIndex, setMatchingPromptIndex] = useState<number | null>(0);
  const matchedPairIndexesRef = useRef<Set<number>>(new Set());

  if (selection.mode === 'flashcards') {
    const intervalPreviews = previewRatingIntervals(
      selection.lemma.lemmaId,
      selection.mode,
      new Date(),
    );
    return (
      <PracticeFlashcard
        card={cardData(selection.lemma, learnerLevel, chromeLocale)}
        ratingLabels={RATING_LABELS}
        intervalPreviews={intervalPreviews}
        onRate={onFlashcardRating}
        chromeLocale={chromeLocale}
      />
    );
  }

  if (selection.mode === 'stress' && selection.stress) {
    const drillPrompt = drillChoicePrompt(selection, learnerLevel);
    return (
      <div className="lexicon-stress" data-testid="practice-stress-stage">
        {drillPrompt ? (
          <p className="lexicon-choice-prompt mc-q" data-testid="practice-form-prompt">
            <span lang="uk">
              {drillPrompt.promptUk}
              {drillPrompt.subtitleUk ? (
                <>
                  {' '}
                  <span className="mc-descriptor">— {drillPrompt.subtitleUk}</span>
                </>
              ) : null}
            </span>
            {showEnglishSubtitles ? (
              <span
                className="btn-sub"
                lang="en"
                style={{
                  display: 'inline',
                  fontSize: '0.85em',
                  fontWeight: 'normal',
                  color: 'var(--lu-text-muted)',
                }}
              >
                {' '}
                / {drillPrompt.promptEn}
                {drillPrompt.subtitleEn ? ` — ${drillPrompt.subtitleEn}` : ''}
              </span>
            ) : null}
          </p>
        ) : null}
        <PracticeStress
          item={selection.stress}
          selectedPosition={stressSelectedPosition}
          answerLocked={answerLocked}
          onSelect={onStressSelect}
        />
      </div>
    );
  }

  if (selection.mode === 'cloze' && selection.cloze) {
    const cloze = selection.cloze;
    const railVerdict: FormRailVerdict = !clozeFeedback
      ? 'idle'
      : clozeFeedback.kind === 'correct'
        ? 'correct'
        : 'wrong';
    return (
      <div className="lexicon-cloze-wrapper">
        <PracticeCloze
          selection={selection}
          input={clozeInput}
          feedback={clozeFeedback}
          answerLocked={answerLocked}
          onInput={onClozeInput}
          onSubmit={onClozeSubmit}
          showEnglishSubtitles={showEnglishSubtitles}
          learnerLevel={learnerLevel}
          chromeLocale={chromeLocale}
        />
        {answerLocked ? (
          <PracticeFormRail
            source={{
              label: displayPracticeForm(cloze.form, learnerLevel),
              value: displayPracticeForm(selection.lemma.lemma, learnerLevel),
            }}
            actual={{
              label: displayPracticeForm(clozeInput, learnerLevel),
              value: displayPracticeForm(clozeInput, learnerLevel),
            }}
            verdict={railVerdict}
            chromeLocale={chromeLocale}
          />
        ) : null}
      </div>
    );
  }

  if (selection.mode === 'heritage' && selection.heritage) {
    return (
      <PracticeHeritage
        item={selection.heritage}
        feedback={heritageFeedback}
        answerLocked={answerLocked}
        selectedLabel={heritageSelectedLabel}
        chromeLocale={chromeLocale}
        onChoice={onChoice}
        showEnglishSubtitles={showEnglishSubtitles}
        learnerLevel={learnerLevel}
      />
    );
  }

  if (selection.mode === 'paronym' && selection.paronym) {
    return (
      <PracticeParonym
        item={selection.paronym}
        feedback={paronymFeedback}
        answerLocked={answerLocked}
        selectedLabel={paronymSelectedLabel}
        chromeLocale={chromeLocale}
        onChoice={onChoice}
        showEnglishSubtitles={showEnglishSubtitles}
        learnerLevel={learnerLevel}
      />
    );
  }

  const drillOptions = drillChoiceOptions(selection, showEnglishSubtitles, learnerLevel);
  const drillPrompt = drillChoicePrompt(selection, learnerLevel);
  if (drillOptions && drillPrompt) {
    return (
      <div className="lexicon-choice" data-testid={`practice-${selection.mode}`}>
        <DigitChoiceShortcuts
          options={drillOptions}
          answerLocked={answerLocked}
          onChoice={onChoice}
        />
        <p className="lexicon-choice-prompt mc-q" data-testid="practice-form-prompt">
          <span lang="uk">
            {drillPrompt.promptUk}
            {drillPrompt.subtitleUk ? (
              <>
                {' '}
                <span className="mc-descriptor">— {drillPrompt.subtitleUk}</span>
              </>
            ) : null}
          </span>
          {showEnglishSubtitles ? (
            <span
              className="btn-sub"
              lang="en"
              style={{
                display: 'inline',
                fontSize: '0.85em',
                fontWeight: 'normal',
                color: 'var(--lu-text-muted)',
              }}
            >
              {' '}
              / {drillPrompt.promptEn}
              {drillPrompt.subtitleEn ? ` — ${drillPrompt.subtitleEn}` : ''}
            </span>
          ) : null}
        </p>
        <ul className="lexicon-option-list mc-options">
          {drillOptions.map((option, index) => (
            <li key={`${option.label}-${index}`}>
              <button
                className={`mc-opt${answerLocked && option.correct ? ' correct' : ''}`}
                type="button"
                disabled={answerLocked}
                onClick={() => onChoice(option)}
              >
                <span className="mc-key">{index + 1}</span>
                <span>{option.label}</span>
              </button>
            </li>
          ))}
        </ul>
        {selection.mode === 'paradigm' && answerLocked && paradigmSelectedLabel !== null ? (
          <PracticeFormRail
            source={{
              label: displayPracticeForm(selection.lemma.lemma, learnerLevel),
              value: displayPracticeForm(selection.lemma.lemma, learnerLevel),
            }}
            actual={{
              label: displayPracticeForm(paradigmSelectedLabel, learnerLevel),
              value: displayPracticeForm(paradigmSelectedLabel, learnerLevel),
            }}
            verdict={drillOptions.some((o) => o.correct && o.label === paradigmSelectedLabel) ? 'correct' : 'wrong'}
            chromeLocale={chromeLocale}
          />
        ) : null}
      </div>
    );
  }

  if (selection.mode === 'matching') {
    if (!pairs.length) {
      return (
        <div className="practice-empty-state" data-testid="practice-match-empty">
          <p className="lexicon-practice-muted">
            <PracticeChromeLabel k="practice.noMatchCards" />
          </p>
          <button
            type="button"
            className="btn btn-accent practice-empty-primary"
            onClick={onBackToModes}
          >
            <PracticeChromeLabel k="practice.backToModes" />
          </button>
        </div>
      );
    }
    const matchedCount = matchedPairIndexesRef.current.size;
    const totalPairs = pairs.length;
    return (
      <div data-testid="practice-matching">
        <MatchUp
          key={selection.cardKey}
          pairs={pairs}
          instruction={(
            <ChromeDual
              uk={`Доберіть пари · ${matchedCount} з ${totalPairs}`}
              en={`Match pairs · ${matchedCount} of ${totalPairs}`}
            />
          )}
          isUkrainian={chromeLocale === 'uk'}
          matchedPairCoding="semantic-four"
          onComplete={onMatchingComplete}
          onMatch={(pairIndex, rating) => {
            matchedPairIndexesRef.current.add(pairIndex);
            setMatchingPromptIndex((currentPromptIndex) => {
              return nextMatchingPromptIndex(
                currentPromptIndex,
                matchedPairIndexesRef.current,
                pairs.length,
              );
            });
            onMatchingMatch?.(pairIndex, rating);
          }}
        />
      </div>
    );
  }

  const options = orderedChoiceOptions(selection, deck, selection.choicePolarity, sessionSeed, learnerLevel);
  if (!options.length) {
    return (
      <div className="practice-empty-state" data-testid="practice-choice-empty">
        <p className="lexicon-practice-muted">
          <PracticeChromeLabel k="practice.noChoiceCards" />
        </p>
        <button
          type="button"
          className="btn btn-accent practice-empty-primary"
          onClick={onBackToModes}
        >
          <PracticeChromeLabel k="practice.backToModes" />
        </button>
      </div>
    );
  }
  const prompt = choicePrompt(selection, learnerLevel);
  return (
    <div className="lexicon-choice" data-testid={`practice-${selection.mode}`}>
      <DigitChoiceShortcuts
        options={options}
        answerLocked={answerLocked}
        onChoice={onChoice}
      />
      <p className="lexicon-choice-prompt mc-q">
        <span lang="uk">{prompt.uk}</span>
        {showEnglishSubtitles ? (
          <span className="btn-sub" lang="en" style={{ display: 'block', fontSize: '0.85em', fontWeight: 'normal', color: 'var(--lu-text-muted)', marginTop: '0.25rem' }}>
            / {prompt.en}
          </span>
        ) : null}
      </p>
      <p className="mc-sub">
        <PracticeChromeLabel k="practice.chooseCorrect" />
      </p>
      <ul className="lexicon-option-list mc-options">
        {options.map((option, index) => (
          <li key={`${option.label}-${index}`}>
            <button
              className={`mc-opt${answerLocked && option.correct ? ' correct' : ''}`}
              type="button"
              disabled={answerLocked}
              onClick={() => onChoice(option)}
            >
              <span className="mc-key">{index + 1}</span>
              <span>{option.label}</span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

function paronymOptions(item: PracticeParonymItem): ChoiceOption[] {
  return item.options.map((option) => ({
    label: option.label,
    correct: option.label === item.answer,
  }));
}

function paronymFeedbackFor(item: PracticeParonymItem, option: ChoiceOption): ParonymFeedback {
  if (option.correct) {
    return {
      kind: 'correct',
      textUk: `Правильно! ${item.distinction_gloss_uk}`,
      textEn: 'Correct!',
    };
  }
  return {
    kind: 'wrong',
    textUk: `Неправильно. ${item.distinction_gloss_uk}`,
    textEn: 'Incorrect.',
  };
}

function PracticeParonym({
  item,
  feedback,
  answerLocked,
  selectedLabel,
  chromeLocale,
  onChoice,
  showEnglishSubtitles,
  learnerLevel,
}: {
  item: PracticeParonymItem;
  feedback: ParonymFeedback | null;
  answerLocked: boolean;
  selectedLabel: string | null;
  chromeLocale: 'en' | 'uk';
  onChoice(option: ChoiceOption): void;
  showEnglishSubtitles: boolean;
  learnerLevel: CefrLevel;
}) {
  const [before, after] = slotPromptParts(item.prompt).map((part) => displayPracticeForm(part, learnerLevel));
  const options = paronymOptions(item);
  const slotText = feedback?.kind === 'correct' ? displayPracticeForm(item.answer, learnerLevel) : '___';
  const sentenceEnglish = postAnswerSentenceEnglish(feedback, item.promptEn);
  return (
    <div className="lexicon-paronym" data-testid="practice-paronym">
      <p className="paronym-task">
        <PracticeChromeLabel k="practice.chooseParonym" />
      </p>
      <p className="paronym-sentence">
        <span>{before}</span>
        <span className={feedback?.kind === 'correct' ? 'paronym-slot filled' : 'paronym-slot'}>
          {slotText}
        </span>
        <span>{after}</span>
      </p>
      {sentenceEnglish ? (
        <p className="cz-translate" data-testid="practice-paronym-sentence-en" lang="en">
          {sentenceEnglish}
        </p>
      ) : null}
      <ul className="lexicon-option-list mc-options">
        {options.map((option, index) => (
          <li key={`${option.label}-${index}`}>
            <button
              className={`mc-opt${answerLocked && option.correct ? ' correct' : ''}`}
              type="button"
              disabled={answerLocked}
              onClick={() => onChoice(option)}
            >
              <span>{displayPracticeForm(option.label, learnerLevel)}</span>
            </button>
          </li>
        ))}
      </ul>
      {feedback ? (
        <div
          className={`paronym-feedback ${feedback.kind}`}
          role={feedback.kind === 'wrong' ? 'alert' : 'status'}
          aria-live="polite"
          data-testid="practice-paronym-feedback"
        >
          <p>
            <span lang="uk">{feedback.textUk}</span>
            {showEnglishSubtitles && feedback.textEn ? (
              <span className="btn-sub" lang="en">/ {feedback.textEn}</span>
            ) : null}
          </p>
          <PracticeFormRail
            source={{
              label: `${displayPracticeForm(item.lemma, learnerLevel)} / ${displayPracticeForm(item.confusable, learnerLevel)}`,
              value: displayPracticeForm(item.lemma, learnerLevel),
            }}
            actual={{
              label: displayPracticeForm(selectedLabel ?? '', learnerLevel),
              value: displayPracticeForm(selectedLabel ?? '', learnerLevel),
            }}
            verdict={feedback.kind}
            chromeLocale={chromeLocale}
          />
          <div style={{ marginTop: '0.4rem' }}>
            <a
              href={atlasLemmaHref(item.lemmaId)}
              target="_blank"
              rel="noopener noreferrer"
              aria-label={CHROME_STRINGS[chromeLocale]['practice.openInAtlasTab']}
              style={{ fontSize: '0.85rem', textDecoration: 'underline', color: 'inherit', fontWeight: 'bold' }}
            >
              <PracticeChromeLabel k="practice.openInAtlasArrow" />
            </a>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function PracticeHeritage({
  item,
  feedback,
  answerLocked,
  selectedLabel,
  chromeLocale,
  onChoice,
  showEnglishSubtitles,
  learnerLevel,
}: {
  item: PracticeHeritageItem;
  feedback: HeritageFeedback | null;
  answerLocked: boolean;
  selectedLabel: string | null;
  chromeLocale: 'en' | 'uk';
  onChoice(option: ChoiceOption): void;
  showEnglishSubtitles: boolean;
  learnerLevel: CefrLevel;
}) {
  const [before, after] = slotPromptParts(item.prompt).map((part) => displayPracticeForm(part, learnerLevel));
  const options = heritageOptions(item);
  const slotText = feedback?.kind === 'correct'
    ? displayPracticeForm(selectedLabel ?? item.answer, learnerLevel)
    : '___';
  const sentenceEnglish = postAnswerSentenceEnglish(feedback, item.promptEn);
  const severityLabel = heritageSeverityLabel(item.severity);
  return (
    <div className="lexicon-heritage" data-testid="practice-heritage">
      <p className="heritage-task">
        <PracticeChromeLabel k="practice.chooseNative" />
      </p>
      <p className="heritage-severity" data-testid="practice-heritage-severity">
        <span lang="uk">{severityLabel.uk}</span>
        {showEnglishSubtitles ? <span className="btn-sub" lang="en">/ {severityLabel.en}</span> : null}
      </p>
      <p className="heritage-sentence">
        <span>{before}</span>
        <span className={feedback?.kind === 'correct' ? 'heritage-slot filled' : 'heritage-slot'}>
          {slotText}
        </span>
        <span>{after}</span>
      </p>
      {sentenceEnglish ? (
        <p className="cz-translate" data-testid="practice-heritage-sentence-en" lang="en">
          {sentenceEnglish}
        </p>
      ) : null}
      <ul className="lexicon-option-list mc-options">
        {options.map((option, index) => (
          <li key={`${option.label}-${index}`}>
            <button
              className={`mc-opt${answerLocked && option.correct ? ' correct' : ''}`}
              type="button"
              disabled={answerLocked}
              onClick={() => onChoice(option)}
            >
              <span>{displayPracticeForm(option.label, learnerLevel)}</span>
            </button>
          </li>
        ))}
      </ul>
      {feedback ? (
        <div
          className={`heritage-feedback ${feedback.kind}`}
          role={feedback.kind === 'wrong' ? 'alert' : 'status'}
          aria-live="polite"
          data-testid="practice-heritage-feedback"
        >
          <p>
            <span lang="uk">{feedback.textUk}</span>
            {showEnglishSubtitles && feedback.textEn ? (
              <span className="btn-sub" lang="en">/ {feedback.textEn}</span>
            ) : null}
          </p>
          {feedback.kind === 'calque' && feedback.citations?.length ? (
            <p className="heritage-citation">
              <PracticeChromeDual
                uk={`Джерело: ${feedback.citations.join('; ')}`}
                en={`Source: ${feedback.citations.join('; ')}`}

              />
            </p>
          ) : null}
          <PracticeFormRail
            source={{
              label: displayPracticeForm(item.nativeLemma ?? item.lemma ?? '', learnerLevel),
              value: displayPracticeForm(item.nativeLemma ?? item.lemma ?? '', learnerLevel),
            }}
            actual={{
              label: displayPracticeForm(item.answer, learnerLevel),
              value: displayPracticeForm(item.answer, learnerLevel),
            }}
            verdict={feedback.kind}
            chromeLocale={chromeLocale}
          />
          <div style={{ marginTop: '0.4rem' }}>
            <a
              href={atlasLemmaHref(item.lemmaId)}
              target="_blank"
              rel="noopener noreferrer"
              aria-label={CHROME_STRINGS[chromeLocale]['practice.openInAtlasTab']}
              style={{ fontSize: '0.85rem', textDecoration: 'underline', color: 'inherit', fontWeight: 'bold' }}
            >
              <PracticeChromeLabel k="practice.openInAtlasArrow" />
            </a>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function PracticeCloze({
  selection,
  input,
  feedback,
  answerLocked,
  onInput,
  onSubmit,
  showEnglishSubtitles,
  learnerLevel,
  chromeLocale,
}: {
  selection: PracticeSelection;
  input: string;
  feedback: ClozeFeedback | null;
  answerLocked: boolean;
  onInput(value: string): void;
  onSubmit(value: string, source: 'typed' | 'chip'): void;
  showEnglishSubtitles: boolean;
  learnerLevel: CefrLevel;
  chromeLocale: 'en' | 'uk';
}) {
  const clozeInputRef = useRef<HTMLInputElement | null>(null);
  // Opus P0-6: a case-miss keeps the typed value (it is not cleared) — select it
  // instead so the next keystroke replaces it cleanly, rather than requiring a
  // manual clear before the learner can try the correct case.
  useEffect(() => {
    if (feedback?.kind === 'case-miss' && !answerLocked) {
      clozeInputRef.current?.select();
    }
  }, [feedback, answerLocked]);
  const cloze = selection.cloze;
  if (!cloze) return null;
  const [before, after] = clozeParts(cloze).map((part) => displayPracticeForm(part, learnerLevel));
  const caseDrill = isCaseClozeDrill(cloze, selection.lemma);
  const displayLemma = displayPracticeForm(selection.lemma.lemma, learnerLevel);
  // Case drills name the dictionary form on purpose (inflect it).
  // Non-case / dictionary-form inserts must NOT name the answer — that turns
  // a real blank (e.g. textbook inventory with ___) into a giveaway.
  const clozePrompt = caseDrill
    ? {
      uk: `Поставте слово „${displayLemma}” у правильному відмінку.`,
      en: `Put the word „${displayLemma}” in the correct case.`,
    }
    : {
      uk: 'Вставте пропущене слово.',
      en: 'Fill in the missing word.',
    };

  const optionErrors = validateClozeOptions(cloze);
  const blankText = feedback?.kind === 'correct' ? cloze.form : input.trim() || '?';
  const displayBlankText = displayPracticeForm(blankText, learnerLevel);
  const usableEnglish = usablePracticeSentenceEnglish(cloze.clozeEn);
  // A1/EN chrome gets scaffolding before an answer; the answer-key remains all-level.
  const sentenceEnglish = feedback || showEnglishSubtitles ? usableEnglish : null;
  const blankClass = [
    'cz-blank',
    displayBlankText !== '?' ? 'filled' : '',
    feedback?.kind === 'wrong-word' ? 'bad' : '',
    feedback?.kind === 'case-miss' ? 'case-miss' : '',
  ]
    .filter(Boolean)
    .join(' ');
  return (
    <div className="lexicon-cloze" data-testid="practice-cloze">
      <p className="cz-task">
        <PracticeChromeDual {...clozePrompt} />
      </p>
      <p className="cz-sentence">
        <span>{before}</span>
        <span className={blankClass}>{displayBlankText}</span>
        <span>{after}</span>
      </p>
      {sentenceEnglish ? (
        <p
          className="lexicon-cloze-translation cz-translate"
          data-testid="practice-cloze-sentence-en"
          lang="en"
        >
          {sentenceEnglish}
        </p>
      ) : null}
      {cloze.attribution && 'uk' in cloze.attribution ? (
        <p className="lexicon-cloze-attribution">
          <PracticeChromeLabel k="practice.sentenceWith" />{' '}
          {cloze.attribution.sourceUrl ? (
            <a href={cloze.attribution.sourceUrl}>{cloze.attribution.source}</a>
          ) : (
            cloze.attribution.source
          )}
          : {cloze.attribution.uk.author} ({cloze.attribution.uk.license})
          {showEnglishSubtitles ? (
            <>
              {' '}
              / {cloze.attribution.en.author} ({cloze.attribution.en.license})
            </>
          ) : null}
        </p>
      ) : cloze.attribution ? (
        <p className="lexicon-cloze-attribution" data-testid="practice-cloze-source-attribution">
          <PracticeChromeLabel k="practice.sourcePrefix" /> {cloze.attribution.label} ({cloze.attribution.source})
          {cloze.attribution.title ? ` — ${cloze.attribution.title}` : ''}
          {cloze.attribution.locator ? `, ${cloze.attribution.locator}` : ''}
        </p>
      ) : null}
      <form
        className="lexicon-cloze-row cz-input-row"
        onSubmit={(event) => {
          event.preventDefault();
          onSubmit(input, 'typed');
        }}
      >
        <input
          ref={clozeInputRef}
          className="cz-input"
          value={input}
          disabled={answerLocked}
          placeholder={CHROME_STRINGS[chromeLocale]['practice.typeWord']}
          autoComplete="off"
          autoCapitalize="off"
          autoCorrect="off"
          spellCheck={false}
          lang="uk"
          aria-label={clozePrompt[chromeLocale]}
          onChange={(event) => onInput(event.currentTarget.value)}
        />
        <button className="btn btn-accent" type="submit" disabled={answerLocked}>
          <PracticeChromeLabel k="practice.check" />
        </button>
      </form>
      {optionErrors.length > 0 ? (
        <p className="lexicon-practice-warning">
          <PracticeChromeLabel k="practice.clozeOptionsFailed" />
        </p>
      ) : (
        <>
          <div className="cz-or">
            <PracticeChromeLabel k="practice.orChoose" />
          </div>
          <ul className="lexicon-option-list lexicon-cloze-options cz-options">
          {cloze.options.map((option) => (
            <li key={option.optionId}>
              <button
                type="button"
                className={`cz-chip${answerLocked && option.label === cloze.form ? ' correct' : ''}`}
                disabled={answerLocked}
                onClick={() => onSubmit(option.label, 'chip')}
              >
                {displayPracticeForm(option.label, learnerLevel)}
              </button>
            </li>
          ))}
          </ul>
        </>
      )}
      {feedback && (
        <div>
          <p
            className={`lexicon-cloze-feedback ${feedback.kind}`}
            role={feedback.kind === 'wrong-word' ? 'alert' : 'status'}
            aria-live="polite"
          >
            <span lang="uk">{feedback.textUk}</span>
            {showEnglishSubtitles && feedback.textEn ? (
              <span className="btn-sub" lang="en">/ {feedback.textEn}</span>
            ) : null}
          </p>
          <div style={{ marginTop: '0.4rem' }}>
            <a
              href={atlasLemmaHref(selection.lemma.lemmaId)}
              target="_blank"
              rel="noopener noreferrer"
              aria-label={CHROME_STRINGS[chromeLocale]['practice.openInAtlasTab']}
              style={{ fontSize: '0.85rem', textDecoration: 'underline', color: 'inherit', fontWeight: 'bold' }}
            >
              <PracticeChromeLabel k="practice.openInAtlasArrow" />
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
