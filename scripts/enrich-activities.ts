#!/usr/bin/env npx ts-node
/**
 * Enrich Module Activities
 *
 * Uses vocabulary.db (SQLite) for proper vocabulary data:
 * - Part of speech filtering (nouns, verbs, adjectives)
 * - Proper gender for agreement
 * - Accumulated vocabulary for refreshers
 *
 * Usage:
 *   npx ts-node scripts/enrich-activities.ts l2-uk-en 1-100
 */

import { readFile, writeFile } from 'fs/promises';
import { existsSync } from 'fs';
import { join } from 'path';
import Database from 'better-sqlite3';

// =============================================================================
// Types
// =============================================================================

interface LevelConfig {
  level: string;
  moduleRange: [number, number];
  totalActivities: number;
  itemsPerActivity: number;
  refresherPercent: number;
  language: 'en' | 'uk';
  sentenceComplexity: 'simple' | 'medium' | 'complex' | 'advanced';
}

interface Lemma {
  uk: string;
  en: string;
  pos: string;
  gender: string | null;
  first_module: number;
}

// =============================================================================
// Configuration
// =============================================================================

const LEVEL_CONFIGS: LevelConfig[] = [
  {
    level: 'A1',
    moduleRange: [1, 30],
    totalActivities: 6,
    itemsPerActivity: 10,
    refresherPercent: 20,
    language: 'en',
    sentenceComplexity: 'simple',
  },
  {
    level: 'A2',
    moduleRange: [31, 60],
    totalActivities: 8,
    itemsPerActivity: 12,
    refresherPercent: 30,
    language: 'en',
    sentenceComplexity: 'medium',
  },
  {
    level: 'A2+',
    moduleRange: [61, 80],
    totalActivities: 10,
    itemsPerActivity: 14,
    refresherPercent: 40,
    language: 'uk',
    sentenceComplexity: 'complex',
  },
  {
    level: 'B1',
    moduleRange: [81, 100],
    totalActivities: 12,
    itemsPerActivity: 16,
    refresherPercent: 40,
    language: 'uk',
    sentenceComplexity: 'advanced',
  },
];

// =============================================================================
// Sentence Templates by Complexity (gender-aware)
// =============================================================================

// Templates with {noun} placeholder and gender markers:
// {m} = masculine, {f} = feminine, {n} = neuter
// Format: [template, genders_array] - genders it works with

interface NounTemplate {
  template: string;
  genders: Array<'m' | 'f' | 'n'>;
}

const NOUN_TEMPLATES: Record<string, NounTemplate[]> = {
  simple: [
    // 4-6 words - basic sentences with nouns
    { template: 'Це мій {noun}.', genders: ['m'] },
    { template: 'Це моя {noun}.', genders: ['f'] },
    { template: 'Це моє {noun}.', genders: ['n'] },
    { template: 'Де мій {noun}?', genders: ['m'] },
    { template: 'Де моя {noun}?', genders: ['f'] },
    { template: 'Де моє {noun}?', genders: ['n'] },
    { template: 'Я бачу {noun}.', genders: ['m', 'f', 'n'] },
    { template: 'Він має {noun}.', genders: ['m', 'f', 'n'] },
    { template: 'Вона любить {noun}.', genders: ['m', 'f', 'n'] },
    { template: 'Ми купуємо {noun}.', genders: ['m', 'f', 'n'] },
    { template: 'Тут є {noun}.', genders: ['m', 'f', 'n'] },
  ],
  medium: [
    // 6-10 words
    { template: 'Це мій новий {noun}.', genders: ['m'] },
    { template: 'Це моя нова {noun}.', genders: ['f'] },
    { template: 'Це моє нове {noun}.', genders: ['n'] },
    { template: 'Де ваш великий {noun}?', genders: ['m'] },
    { template: 'Де ваша велика {noun}?', genders: ['f'] },
    { template: 'Де ваше велике {noun}?', genders: ['n'] },
    { template: 'Я хочу купити цей {noun}.', genders: ['m'] },
    { template: 'Я хочу купити цю {noun}.', genders: ['f'] },
    { template: 'Я хочу купити це {noun}.', genders: ['n'] },
    { template: 'Мій брат має хороший {noun}.', genders: ['m'] },
    { template: 'Мій брат має хорошу {noun}.', genders: ['f'] },
    { template: 'Мій брат має хороше {noun}.', genders: ['n'] },
    { template: 'Цей {noun} коштує сто гривень.', genders: ['m'] },
    { template: 'Ця {noun} коштує сто гривень.', genders: ['f'] },
    { template: 'Це {noun} коштує сто гривень.', genders: ['n'] },
  ],
  complex: [
    // 10-15 words
    { template: 'Я хочу купити цей {noun}, але він занадто дорогий.', genders: ['m'] },
    { template: 'Я хочу купити цю {noun}, але вона занадто дорога.', genders: ['f'] },
    { template: 'Я хочу купити це {noun}, але воно занадто дороге.', genders: ['n'] },
    { template: 'Мій друг сказав, що його {noun} дуже зручний.', genders: ['m'] },
    { template: 'Моя сестра сказала, що її {noun} дуже зручна.', genders: ['f'] },
    { template: 'Вони сказали, що це {noun} дуже зручне.', genders: ['n'] },
    { template: 'Цей {noun} належить моєму другові з Києва.', genders: ['m'] },
    { template: 'Ця {noun} належить моїй подрузі з Києва.', genders: ['f'] },
    { template: 'Це {noun} належить моєму другові з Києва.', genders: ['n'] },
    { template: 'Вони довго шукали хороший {noun}, але не знайшли.', genders: ['m'] },
    { template: 'Вони довго шукали хорошу {noun}, але не знайшли.', genders: ['f'] },
    { template: 'Вони довго шукали хороше {noun}, але не знайшли.', genders: ['n'] },
  ],
  advanced: [
    // 15-25 words
    { template: 'Незважаючи на високу ціну, цей {noun} вартий кожної гривні.', genders: ['m'] },
    { template: 'Незважаючи на високу ціну, ця {noun} варта кожної гривні.', genders: ['f'] },
    { template: 'Незважаючи на високу ціну, це {noun} варте кожної гривні.', genders: ['n'] },
    { template: 'Коли я вперше побачив цей {noun}, я одразу захотів його купити.', genders: ['m'] },
    { template: 'Коли я вперше побачила цю {noun}, я одразу захотіла її купити.', genders: ['f'] },
    { template: 'Коли я вперше побачив це {noun}, я одразу захотів його купити.', genders: ['n'] },
    { template: 'Мій колега порадив мені цей {noun}, і я дуже задоволений вибором.', genders: ['m'] },
    { template: 'Моя колега порадила мені цю {noun}, і я дуже задоволена вибором.', genders: ['f'] },
    { template: 'Мій колега порадив мені це {noun}, і я дуже задоволений вибором.', genders: ['n'] },
    { template: 'Ми нарешті знайшли {noun}, який ідеально підходить для нас.', genders: ['m'] },
    { template: 'Ми нарешті знайшли {noun}, яка ідеально підходить для нас.', genders: ['f'] },
    { template: 'Ми нарешті знайшли {noun}, яке ідеально підходить для нас.', genders: ['n'] },
  ],
};

// Templates for adjectives
const ADJ_TEMPLATES = {
  simple: [
    'Це дуже {adj}.',
    'Він не {adj}.',
    'Вона така {adj}!',
    'Чи це {adj}?',
  ],
  medium: [
    'Цей будинок дуже {adj}.',
    'Моя кімната занадто {adj}.',
    'Ваша ідея здається {adj}.',
    'Ця книга надзвичайно {adj}.',
  ],
  complex: [
    'Я вважаю, що ця пропозиція є занадто {adj} для нас.',
    'Цей варіант здається мені найбільш {adj} з усіх.',
  ],
  advanced: [
    'Незважаючи на те, що цей підхід видається {adj}, він має багато переваг.',
  ],
};

// Templates for verbs
const VERB_TEMPLATES = {
  simple: [
    'Я люблю {verb}.',
    'Він хоче {verb}.',
    'Ми можемо {verb}.',
    'Вона вміє {verb}.',
  ],
  medium: [
    'Я хочу навчитися {verb}.',
    'Вони планують {verb} завтра.',
    'Чи ти вмієш добре {verb}?',
    'Мій брат любить {verb} щодня.',
  ],
  complex: [
    'Я давно мріяв навчитися {verb}, і нарешті маю таку можливість.',
    'Моя сестра каже, що їй подобається {verb} у вільний час.',
  ],
  advanced: [
    'Незважаючи на те, що {verb} вимагає багато часу, це приносить велике задоволення.',
  ],
};

// =============================================================================
// Paths
// =============================================================================

const ROOT = join(__dirname, '..');
const MODULES_DIR = join(ROOT, 'curriculum', 'l2-uk-en', 'modules');
const VOCAB_DB = join(ROOT, 'curriculum', 'l2-uk-en', 'vocabulary.db');

// =============================================================================
// Database
// =============================================================================

let db: Database.Database;

function getDb(): Database.Database {
  if (!db) {
    db = new Database(VOCAB_DB, { readonly: true });
  }
  return db;
}

function getVocabForModule(moduleNum: number): Lemma[] {
  const stmt = getDb().prepare(`
    SELECT uk, en, pos, gender, first_module
    FROM lemmas
    WHERE first_module = ?
    ORDER BY uk
  `);
  return stmt.all(moduleNum) as Lemma[];
}

function getAccumulatedVocab(upToModule: number): Lemma[] {
  const stmt = getDb().prepare(`
    SELECT uk, en, pos, gender, first_module
    FROM lemmas
    WHERE first_module <= ?
    ORDER BY first_module, uk
  `);
  return stmt.all(upToModule) as Lemma[];
}

function getNouns(lemmas: Lemma[]): Lemma[] {
  return lemmas.filter(l => l.pos === 'noun');
}

function getAdjectives(lemmas: Lemma[]): Lemma[] {
  return lemmas.filter(l => l.pos === 'adj' || l.pos === 'adjective');
}

function getVerbs(lemmas: Lemma[]): Lemma[] {
  return lemmas.filter(l => l.pos === 'verb');
}

// =============================================================================
// Utilities
// =============================================================================

function shuffle<T>(arr: T[]): T[] {
  const result = [...arr];
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
}

function pick<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

function pickN<T>(arr: T[], n: number): T[] {
  return shuffle(arr).slice(0, Math.min(n, arr.length));
}

function getLevelConfig(moduleNum: number): LevelConfig {
  for (const config of LEVEL_CONFIGS) {
    if (moduleNum >= config.moduleRange[0] && moduleNum <= config.moduleRange[1]) {
      return config;
    }
  }
  return LEVEL_CONFIGS[0];
}

// =============================================================================
// Sentence Generation
// =============================================================================

function generateNounSentence(
  noun: Lemma,
  complexity: 'simple' | 'medium' | 'complex' | 'advanced'
): { sentence: string; answer: string } | null {
  const templates = NOUN_TEMPLATES[complexity];

  // Filter templates by gender
  const gender = (noun.gender || 'm') as 'm' | 'f' | 'n';
  const validTemplates = templates.filter(t => t.genders.includes(gender));

  if (validTemplates.length === 0) return null;

  const templateObj = pick(validTemplates);
  const sentence = templateObj.template.replace('{noun}', '___');

  return { sentence, answer: noun.uk };
}

function generateAdjSentence(
  adj: Lemma,
  complexity: 'simple' | 'medium' | 'complex' | 'advanced'
): { sentence: string; answer: string } {
  const templates = ADJ_TEMPLATES[complexity] || ADJ_TEMPLATES.simple;
  const template = pick(templates);
  const sentence = template.replace('{adj}', '___');
  return { sentence, answer: adj.uk };
}

function generateVerbSentence(
  verb: Lemma,
  complexity: 'simple' | 'medium' | 'complex' | 'advanced'
): { sentence: string; answer: string } {
  const templates = VERB_TEMPLATES[complexity] || VERB_TEMPLATES.simple;
  const template = pick(templates);
  const sentence = template.replace('{verb}', '___');
  return { sentence, answer: verb.uk };
}

// =============================================================================
// Activity Generators
// =============================================================================

function generateFillIn(
  config: LevelConfig,
  currentVocab: Lemma[],
  allVocab: Lemma[]
): string {
  const title = config.language === 'uk' ? 'Доповніть речення' : 'Complete the Sentences';
  const instruction = config.language === 'uk'
    ? 'Оберіть правильне слово.'
    : 'Choose the correct word to complete each sentence.';

  let content = `## fill-in: ${title}\n\n> ${instruction}\n\n`;

  // Separate by POS
  const nouns = getNouns(currentVocab);
  const adjs = getAdjectives(currentVocab);
  const verbs = getVerbs(currentVocab);
  const allNouns = getNouns(allVocab);
  const allAdjs = getAdjectives(allVocab);
  const allVerbs = getVerbs(allVocab);

  const items: Array<{ sentence: string; answer: string; distractors: string[] }> = [];

  // Generate noun sentences
  for (const noun of pickN(nouns, Math.ceil(config.itemsPerActivity * 0.5))) {
    const result = generateNounSentence(noun, config.sentenceComplexity);
    if (!result) continue;
    const { sentence, answer } = result;
    const distractors = pickN(allNouns.filter(n => n.uk !== answer), 3).map(n => n.uk);
    items.push({ sentence, answer, distractors });
  }

  // Generate adj sentences
  for (const adj of pickN(adjs, Math.ceil(config.itemsPerActivity * 0.25))) {
    const { sentence, answer } = generateAdjSentence(adj, config.sentenceComplexity);
    const distractors = pickN(allAdjs.filter(a => a.uk !== answer), 3).map(a => a.uk);
    items.push({ sentence, answer, distractors });
  }

  // Generate verb sentences
  for (const verb of pickN(verbs, Math.ceil(config.itemsPerActivity * 0.25))) {
    const { sentence, answer } = generateVerbSentence(verb, config.sentenceComplexity);
    const distractors = pickN(allVerbs.filter(v => v.uk !== answer), 3).map(v => v.uk);
    items.push({ sentence, answer, distractors });
  }

  // Shuffle and output
  let num = 1;
  for (const item of shuffle(items).slice(0, config.itemsPerActivity)) {
    const options = shuffle([item.answer, ...item.distractors]);
    content += `${num}. ${item.sentence}\n`;
    content += `   > [!answer] ${item.answer}\n`;
    content += `   > [!options] ${options.join(' | ')}\n\n`;
    num++;
  }

  return content;
}

function generateUnjumble(
  config: LevelConfig,
  currentVocab: Lemma[]
): string {
  const title = config.language === 'uk' ? 'Побудуйте речення' : 'Build the Sentence';
  const instruction = config.language === 'uk'
    ? 'Розташуйте слова в правильному порядку.'
    : 'Arrange the words in the correct order.';

  let content = `## unjumble: ${title}\n\n> ${instruction}\n\n`;

  const nouns = getNouns(currentVocab);
  const templates = NOUN_TEMPLATES[config.sentenceComplexity];

  let num = 1;
  for (const noun of pickN(nouns, config.itemsPerActivity)) {
    // Pick template that matches gender
    const gender = (noun.gender || 'm') as 'm' | 'f' | 'n';
    const validTemplates = templates.filter(t => t.genders.includes(gender));
    if (validTemplates.length === 0) continue;

    const templateObj = pick(validTemplates);
    const sentence = templateObj.template.replace('{noun}', noun.uk);

    // Jumble words
    const words = sentence.replace(/[.!?,]/g, '').split(/\s+/);
    const jumbled = shuffle(words);

    content += `${num}. ${jumbled.join(' / ')}\n`;
    content += `   > [!answer] ${sentence}\n`;
    content += `   > (${noun.en})\n\n`;
    num++;
  }

  return content;
}

function generateMatchUp(
  config: LevelConfig,
  currentVocab: Lemma[],
  refresherVocab: Lemma[]
): string {
  const title = config.language === 'uk' ? 'Знайдіть пари' : 'Match the Pairs';
  const instruction = config.language === 'uk'
    ? "З'єднайте українські слова з англійськими."
    : 'Match Ukrainian words to their English meanings.';

  let content = `## match-up: ${title}\n\n> ${instruction}\n\n`;
  content += '| Left | Right |\n|------|-------|\n';

  const refresherCount = Math.floor(config.itemsPerActivity * config.refresherPercent / 100);
  const currentCount = config.itemsPerActivity - refresherCount;

  const selected = [
    ...pickN(currentVocab, currentCount),
    ...pickN(refresherVocab, refresherCount),
  ];

  for (const v of shuffle(selected)) {
    content += `| ${v.uk} | ${v.en} |\n`;
  }

  content += '\n';
  return content;
}

function generateQuiz(
  config: LevelConfig,
  currentVocab: Lemma[],
  allVocab: Lemma[]
): string {
  const title = config.language === 'uk' ? 'Перевірка значень' : 'Meaning Check';
  const instruction = config.language === 'uk'
    ? 'Оберіть правильну відповідь.'
    : 'Choose the correct answer.';

  let content = `## quiz: ${title}\n\n> ${instruction}\n\n`;

  const selected = pickN(currentVocab, config.itemsPerActivity);

  let num = 1;
  for (const v of selected) {
    const question = config.language === 'uk'
      ? `Що означає "${v.uk}"?`
      : `What does "${v.uk}" mean?`;

    const wrongAnswers = pickN(allVocab.filter(x => x.uk !== v.uk), 3).map(x => x.en);
    const allOptions = shuffle([v.en, ...wrongAnswers]);
    const correctIndex = allOptions.indexOf(v.en);

    content += `${num}. ${question}\n`;
    for (let i = 0; i < allOptions.length; i++) {
      const marker = i === correctIndex ? '[x]' : '[ ]';
      content += `   - ${marker} ${allOptions[i]}\n`;
    }
    content += `   > "${v.uk}" means "${v.en}"\n\n`;
    num++;
  }

  return content;
}

function generateTrueFalse(
  config: LevelConfig,
  currentVocab: Lemma[],
  allVocab: Lemma[]
): string {
  const title = config.language === 'uk' ? 'Правда чи ні?' : 'True or False?';
  const instruction = config.language === 'uk'
    ? 'Визначте, чи правильне твердження.'
    : 'Determine if each statement is true or false.';

  let content = `## true-false: ${title}\n\n> ${instruction}\n\n`;

  const selected = pickN(currentVocab, Math.min(10, currentVocab.length));

  for (const v of selected) {
    const isTrue = Math.random() > 0.5;

    if (isTrue) {
      content += `- [x] "${v.uk}" means "${v.en}"\n`;
      content += `   > Correct!\n\n`;
    } else {
      const wrongMeaning = pick(allVocab.filter(x => x.uk !== v.uk))?.en || 'something';
      content += `- [ ] "${v.uk}" means "${wrongMeaning}"\n`;
      content += `   > Incorrect. "${v.uk}" means "${v.en}"\n\n`;
    }
  }

  return content;
}

function generateGroupSort(
  config: LevelConfig,
  currentVocab: Lemma[]
): string {
  const title = config.language === 'uk' ? 'Сортування за родом' : 'Sort by Gender';
  const instruction = config.language === 'uk'
    ? 'Розподіліть слова за родами.'
    : 'Sort the nouns into gender categories.';

  let content = `## group-sort: ${title}\n\n> ${instruction}\n\n`;

  const nouns = getNouns(currentVocab);
  const masculine = nouns.filter(n => n.gender === 'm');
  const feminine = nouns.filter(n => n.gender === 'f');
  const neuter = nouns.filter(n => n.gender === 'n');

  const mLabel = config.language === 'uk' ? 'Чоловічий рід' : 'Masculine';
  const fLabel = config.language === 'uk' ? 'Жіночий рід' : 'Feminine';
  const nLabel = config.language === 'uk' ? 'Середній рід' : 'Neuter';

  if (masculine.length >= 2) {
    content += `### ${mLabel}\n`;
    for (const n of pickN(masculine, 6)) content += `- ${n.uk}\n`;
    content += '\n';
  }
  if (feminine.length >= 2) {
    content += `### ${fLabel}\n`;
    for (const n of pickN(feminine, 6)) content += `- ${n.uk}\n`;
    content += '\n';
  }
  if (neuter.length >= 2) {
    content += `### ${nLabel}\n`;
    for (const n of pickN(neuter, 6)) content += `- ${n.uk}\n`;
    content += '\n';
  }

  return content;
}

// =============================================================================
// Main Enrichment
// =============================================================================

function removeActivitiesSection(content: string): string {
  return content.replace(
    /\n# (?:Activities|Вправи)\n[\s\S]*?(?=\n# (?:Vocabulary|Словник|Summary|Підсумок|Review)|---\s*\n# |$)/,
    '\n'
  ).replace(/\n{3,}/g, '\n\n');
}

async function enrichModule(moduleNum: number): Promise<void> {
  const padded = String(moduleNum).padStart(2, '0');
  const path = join(MODULES_DIR, `module-${padded}.md`);

  if (!existsSync(path)) {
    console.log(`  Module ${moduleNum}: not found, skipping`);
    return;
  }

  const config = getLevelConfig(moduleNum);
  console.log(`  Module ${moduleNum} (${config.level}): generating ${config.totalActivities} activities...`);

  let content = await readFile(path, 'utf-8');

  // Load vocabulary from database
  const currentVocab = getVocabForModule(moduleNum);
  const allVocab = getAccumulatedVocab(moduleNum);
  const refresherVocab = allVocab.filter(v => v.first_module < moduleNum);

  if (currentVocab.length < 3) {
    // For review modules, use refresher vocab
    if (refresherVocab.length < 10) {
      console.log(`    Skipping: only ${currentVocab.length} current, ${refresherVocab.length} refresher vocab`);
      return;
    }
    console.log(`    Review module: using ${refresherVocab.length} refresher vocab`);
  }

  // Use current vocab if available, otherwise use recent refresher vocab
  const vocabToUse = currentVocab.length >= 3 ? currentVocab : pickN(refresherVocab, 20);

  // Remove old activities
  content = removeActivitiesSection(content);

  // Find insertion point
  const vocabIndex = content.search(/\n# (?:Vocabulary|Словник)/);
  const insertPoint = vocabIndex > 0 ? vocabIndex : content.length;

  // Generate new activities
  const header = config.language === 'uk' ? '# Вправи' : '# Activities';
  let activities = `\n${header}\n\n`;

  activities += generateFillIn(config, vocabToUse, allVocab);
  activities += generateUnjumble(config, vocabToUse);
  activities += generateMatchUp(config, vocabToUse, refresherVocab);
  activities += generateQuiz(config, vocabToUse, allVocab);

  if (config.totalActivities >= 6) {
    activities += generateTrueFalse(config, vocabToUse, allVocab);
  }
  if (config.totalActivities >= 8 && getNouns(vocabToUse).length >= 6) {
    activities += generateGroupSort(config, vocabToUse);
  }

  activities += '---\n';

  // Insert
  const newContent = content.slice(0, insertPoint) + activities + content.slice(insertPoint);
  await writeFile(path, newContent, 'utf-8');

  console.log(`    Done: ${currentVocab.length} current, ${refresherVocab.length} refreshers`);
}

async function main() {
  const args = process.argv.slice(2);
  if (args.length < 1) {
    console.log('Usage: npx ts-node scripts/enrich-activities.ts l2-uk-en [range]');
    process.exit(1);
  }

  const range = args[1] || '1-100';
  let start: number, end: number;

  if (range.includes('-')) {
    [start, end] = range.split('-').map(Number);
  } else {
    start = end = parseInt(range, 10);
  }

  console.log(`\nEnriching modules ${start}-${end} using vocabulary.db...\n`);

  for (let i = start; i <= end; i++) {
    try {
      await enrichModule(i);
    } catch (err) {
      console.error(`  Error on module ${i}:`, err);
    }
  }

  if (db) db.close();
  console.log('\nDone!');
}

main().catch(console.error);
