#!/usr/bin/env npx ts-node
/**
 * Exercise Generator for Curricula-Opus
 *
 * Generates additional activities for modules based on:
 * - Vocabulary words
 * - Example sentences from lesson content
 * - Grammar patterns
 *
 * Activity Types by Difficulty:
 * - Type A (Recognition/Easy): match-up, true-false, group-sort
 * - Type B (Production/Medium): fill-in, quiz
 * - Type C (Synthesis/Hard): unjumble, transform
 *
 * Usage:
 *   npx ts-node scripts/generate-exercises.ts              # All modules
 *   npx ts-node scripts/generate-exercises.ts 1-80         # Pre-B1 only
 *   npx ts-node scripts/generate-exercises.ts 5            # Single module
 */

import { readFile, writeFile, readdir } from 'fs/promises';
import { join } from 'path';
import { existsSync } from 'fs';

// =============================================================================
// CONFIGURATION
// =============================================================================

const ROOT_DIR = join(__dirname, '..');
const MODULES_DIR = join(ROOT_DIR, 'curriculum', 'l2-uk-en', 'modules');

// Target activity counts by level
const TARGET_ACTIVITIES: Record<string, { total: number; typeA: number; typeB: number; typeC: number }> = {
  'A1': { total: 6, typeA: 3, typeB: 2, typeC: 1 },
  'A2': { total: 6, typeA: 2, typeB: 3, typeC: 2 },
  'A2+': { total: 7, typeA: 2, typeB: 3, typeC: 2 },
  'B1': { total: 8, typeA: 2, typeB: 3, typeC: 3 },
  'B2': { total: 8, typeA: 2, typeB: 3, typeC: 3 },
};

// =============================================================================
// TYPES
// =============================================================================

interface VocabWord {
  word: string;
  ipa: string;
  english: string;
  pos: string;
  gender: string;
  note: string;
}

interface ExampleSentence {
  ukrainian: string;
  english: string;
  source: string;
}

interface ModuleData {
  moduleNum: number;
  level: string;
  title: string;
  vocabulary: VocabWord[];
  examples: ExampleSentence[];
  existingActivities: string[];
  grammarTopics: string[];
}

interface GeneratedActivity {
  type: string;
  title: string;
  titleUk?: string;
  content: string;
  difficulty: 'A' | 'B' | 'C';
}

// =============================================================================
// PARSING FUNCTIONS
// =============================================================================

function getLevelFromModule(num: number): string {
  if (num <= 30) return 'A1';
  if (num <= 60) return 'A2';
  if (num <= 80) return 'A2+';
  if (num <= 140) return 'B1';
  if (num <= 190) return 'B2';
  return 'C1';
}

function parseVocabulary(content: string): VocabWord[] {
  const words: VocabWord[] = [];

  // Find vocabulary section (English or Ukrainian header)
  const vocabMatch = content.match(/# (Vocabulary|Словник)\n\n\|[^\n]+\|[\s\S]*?\n\n/);
  if (!vocabMatch) return words;

  const lines = vocabMatch[0].split('\n').filter(l =>
    l.startsWith('|') &&
    !l.includes('---') &&
    !l.includes('Word') &&
    !l.includes('Слово') &&
    !l.includes('IPA')
  );

  for (const line of lines) {
    const cells = line.split('|').map(c => c.trim()).filter(Boolean);
    if (cells.length >= 3) {
      words.push({
        word: cells[0],
        ipa: cells[1] || '',
        english: cells[2],
        pos: cells[3] || '',
        gender: cells[4] || '',
        note: cells[5] || '',
      });
    }
  }

  return words;
}

function parseExamples(content: string): ExampleSentence[] {
  const examples: ExampleSentence[] = [];
  const seen = new Set<string>();

  // Find ALL table rows and look for Ukrainian/English pairs in any columns
  const tableRowMatches = content.matchAll(/\|([^|\n]+(?:\|[^|\n]+)+)\|/g);

  for (const match of tableRowMatches) {
    const cells = match[1].split('|').map(c => c.trim());

    // Skip header/separator rows
    if (cells.some(c => c.includes('---') || c === 'Word' || c === 'IPA' || c === 'Gender' || c === 'Form')) continue;

    // Look for Ukrainian-English pairs in adjacent cells
    for (let i = 0; i < cells.length - 1; i++) {
      const ukr = cells[i].replace(/\*\*/g, '').replace(/\*/g, '').replace(/\([^)]+\)/g, '').trim();
      const eng = cells[i + 1].replace(/\*\*/g, '').replace(/\*/g, '').trim();

      // Check if this is a Ukrainian-English pair (Ukrainian has Cyrillic, English has Latin)
      if (/[а-яіїєґ]/i.test(ukr) && /^[a-z]/i.test(eng) && !eng.includes('---')) {
        // Must be a meaningful phrase (3+ chars, multiple words preferred for sentences)
        if (ukr.length >= 3 && eng.length >= 3 && !seen.has(ukr)) {
          seen.add(ukr);
          examples.push({
            ukrainian: ukr,
            english: eng,
            source: 'table',
          });
        }
      }
    }
  }

  // Also find inline examples like: **Вона говорить українською.** - She speaks Ukrainian.
  const inlineMatches = content.matchAll(/\*\*([^*]+)\*\*\s*[-–—]\s*([^.\n]+\.?)/g);

  for (const match of inlineMatches) {
    const ukr = match[1].trim();
    const eng = match[2].trim();

    if (/[а-яіїєґ]/i.test(ukr) && /[a-z]/i.test(eng) && !seen.has(ukr)) {
      seen.add(ukr);
      examples.push({
        ukrainian: ukr,
        english: eng,
        source: 'inline',
      });
    }
  }

  return examples;
}

function parseExistingActivities(content: string): string[] {
  const activities: string[] = [];
  const matches = content.matchAll(/## (quiz|match-up|group-sort|fill-in|true-false|unjumble|order|translate):/gi);

  for (const match of matches) {
    activities.push(match[1].toLowerCase());
  }

  return activities;
}

function parseGrammarTopics(content: string): string[] {
  const topics: string[] = [];

  // Extract from frontmatter grammar field
  const grammarMatch = content.match(/grammar:\n([\s\S]*?)(?=---|\n[a-z]+:)/);
  if (grammarMatch) {
    const lines = grammarMatch[1].split('\n').filter(l => l.trim().startsWith('-'));
    for (const line of lines) {
      topics.push(line.replace(/^\s*-\s*/, '').trim());
    }
  }

  return topics;
}

// Cache for accumulated vocabulary from previous modules
const vocabCache: Map<number, VocabWord[]> = new Map();

async function loadAccumulatedVocabulary(upToModule: number): Promise<VocabWord[]> {
  // Check cache
  if (vocabCache.has(upToModule)) {
    return vocabCache.get(upToModule)!;
  }

  const allVocab: VocabWord[] = [];
  const seen = new Set<string>();

  for (let num = 1; num <= upToModule; num++) {
    const padded = String(num).padStart(2, '0');
    const modulePath = join(MODULES_DIR, `module-${padded}.md`);

    try {
      if (!existsSync(modulePath)) continue;
      const content = await readFile(modulePath, 'utf-8');
      const vocab = parseVocabulary(content);

      for (const word of vocab) {
        if (!seen.has(word.word)) {
          seen.add(word.word);
          allVocab.push(word);
        }
      }
    } catch {
      // Skip modules that can't be read
    }
  }

  vocabCache.set(upToModule, allVocab);
  return allVocab;
}

async function parseModule(modulePath: string): Promise<ModuleData | null> {
  try {
    const content = await readFile(modulePath, 'utf-8');

    // Parse frontmatter
    const fmMatch = content.match(/---\n([\s\S]*?)\n---/);
    if (!fmMatch) return null;

    const fm = fmMatch[1];
    const moduleMatch = fm.match(/module:\s*(\d+)/);
    const levelMatch = fm.match(/level:\s*(\S+)/);
    const titleMatch = fm.match(/title:\s*"([^"]+)"/);

    if (!moduleMatch) return null;

    const moduleNum = parseInt(moduleMatch[1]);

    // Load accumulated vocabulary from all previous modules
    const accumulatedVocab = await loadAccumulatedVocabulary(moduleNum);

    return {
      moduleNum,
      level: levelMatch ? levelMatch[1] : getLevelFromModule(moduleNum),
      title: titleMatch ? titleMatch[1] : `Module ${moduleNum}`,
      vocabulary: accumulatedVocab, // Use accumulated vocab instead of just this module
      examples: parseExamples(content),
      existingActivities: parseExistingActivities(content),
      grammarTopics: parseGrammarTopics(content),
    };
  } catch (err) {
    console.error(`Error parsing ${modulePath}:`, err);
    return null;
  }
}

// =============================================================================
// ACTIVITY GENERATORS
// =============================================================================

function generateMatchUp(data: ModuleData, variant: number): GeneratedActivity | null {
  const vocab = data.vocabulary.filter(w => w.english && w.word);
  if (vocab.length < 6) return null;

  // Shuffle and take up to 12 items
  const shuffled = vocab.sort(() => Math.random() - 0.5).slice(0, 12);

  const titles = [
    'Vocabulary Match',
    'Word Pairs',
    'Match Ukrainian to English',
  ];

  let content = `> Match each Ukrainian word with its English translation.\n\n`;
  content += `| Left | Right |\n|------|-------|\n`;

  for (const w of shuffled) {
    content += `| ${w.word} | ${w.english} |\n`;
  }

  return {
    type: 'match-up',
    title: titles[variant % titles.length],
    content,
    difficulty: 'A',
  };
}

function generateTrueFalse(data: ModuleData): GeneratedActivity | null {
  const statements: string[] = [];

  // Generate statements from vocabulary
  for (const w of data.vocabulary.slice(0, 6)) {
    if (w.gender && w.pos === 'noun') {
      // True statement
      statements.push(`- [x] "${w.word}" is ${w.gender === 'm' ? 'masculine' : w.gender === 'f' ? 'feminine' : 'neuter'}.\n   > Correct! ${w.word} is ${w.gender === 'm' ? 'masculine' : w.gender === 'f' ? 'feminine' : 'neuter'}.`);
    }
  }

  // Generate false statements
  const genderMap: Record<string, string> = { 'm': 'masculine', 'f': 'feminine', 'n': 'neuter' };
  const wrongGenders = ['m', 'f', 'n'];

  for (const w of data.vocabulary.slice(6, 12)) {
    if (w.gender && w.pos === 'noun') {
      const wrong = wrongGenders.find(g => g !== w.gender) || 'f';
      statements.push(`- [ ] "${w.word}" is ${genderMap[wrong]}.\n   > Incorrect. ${w.word} is ${genderMap[w.gender]}.`);
    }
  }

  if (statements.length < 4) return null;

  let content = `> Determine if each statement is true or false.\n\n`;
  content += statements.slice(0, 10).join('\n\n') + '\n';

  return {
    type: 'true-false',
    title: 'True or False?',
    content,
    difficulty: 'A',
  };
}

function generateGroupSort(data: ModuleData): GeneratedActivity | null {
  // Group by gender
  const byGender: Record<string, string[]> = { 'm': [], 'f': [], 'n': [], 'pl': [] };

  for (const w of data.vocabulary) {
    if (w.gender && byGender[w.gender]) {
      byGender[w.gender].push(w.word);
    }
  }

  // Check if we have enough items
  const validGroups = Object.entries(byGender).filter(([_, items]) => items.length >= 2);
  if (validGroups.length < 2) return null;

  let content = `> Sort these words by their grammatical gender.\n\n`;

  const genderNames: Record<string, string> = {
    'm': 'Masculine',
    'f': 'Feminine',
    'n': 'Neuter',
    'pl': 'Plural',
  };

  for (const [gender, items] of validGroups) {
    content += `### ${genderNames[gender]}\n`;
    // Use up to 6 items per group
    for (const item of items.slice(0, 6)) {
      content += `- ${item}\n`;
    }
    content += '\n';
  }

  return {
    type: 'group-sort',
    title: 'Sort by Gender',
    content,
    difficulty: 'A',
  };
}

function generateFillIn(data: ModuleData): GeneratedActivity | null {
  // For early modules (A1), accept shorter phrases; for later modules require longer sentences
  const minLen = data.moduleNum <= 30 ? 5 : 10;
  const minWords = data.moduleNum <= 30 ? 2 : 3;

  const examples = data.examples.filter(e => e.ukrainian.length >= minLen);

  let content = `> Choose the correct word to complete each sentence.\n\n`;

  // Adaptive count: modules 1-10: 8 items, 11-30: 12, 31+: 18
  const targetCount = data.moduleNum <= 10 ? 8 : data.moduleNum <= 30 ? 12 : 18;
  let num = 1;

  // Collect all vocab words for distractors
  const allVocabWords = data.vocabulary.map(v => v.word).filter(w => w.length > 1);

  // First, use example sentences
  const usedExamples = examples.slice(0, targetCount);

  for (const ex of usedExamples) {
    if (num > targetCount) break;
    const words = ex.ukrainian.split(/\s+/);
    if (words.length < minWords) continue;

    // For 2-word phrases, blank the first word; for longer, blank middle
    const targetIdx = words.length === 2 ? 0 : Math.floor(words.length / 2);
    const targetWord = words[targetIdx].replace(/[.,!?]/g, '');
    if (targetWord.length <= 1) continue;

    const blanked = words.map((w, i) => i === targetIdx ? '___' : w).join(' ');

    // Generate distractors from vocabulary
    const distractors = allVocabWords
      .filter(a => a !== targetWord)
      .sort(() => Math.random() - 0.5)
      .slice(0, 3);

    content += `${num}. ${blanked}\n`;
    content += `   > [!answer] ${targetWord}\n`;
    if (distractors.length >= 3) {
      content += `   > [!options] ${[targetWord, ...distractors].join(' | ')}\n`;
    }
    content += `\n`;
    num++;
  }

  // If we don't have enough examples, generate from vocabulary
  if (num <= targetCount && data.vocabulary.length >= 8) {
    const shuffledVocab = [...data.vocabulary].sort(() => Math.random() - 0.5);

    for (const word of shuffledVocab) {
      if (num > targetCount) break;
      if (!word.english || word.word.length <= 1) continue;

      // Create a translation fill-in: "___ means [english]"
      const distractors = allVocabWords
        .filter(w => w !== word.word)
        .sort(() => Math.random() - 0.5)
        .slice(0, 3);

      if (distractors.length < 3) continue;

      content += `${num}. ___ — "${word.english}"\n`;
      content += `   > [!answer] ${word.word}\n`;
      content += `   > [!options] ${[word.word, ...distractors].join(' | ')}\n`;
      content += `\n`;
      num++;
    }
  }

  // Return null if no items were generated
  if (num === 1) return null;

  return {
    type: 'fill-in',
    title: 'Fill in the Blank',
    content,
    difficulty: 'B',
  };
}

function generateQuiz(data: ModuleData, variant: number): GeneratedActivity | null {
  const vocab = data.vocabulary.filter(w => w.english && w.word);
  if (vocab.length < 8) return null;

  let content = `> Choose the correct answer.\n\n`;

  const shuffled = vocab.sort(() => Math.random() - 0.5);

  // Adaptive count: modules 1-10: 6-8 items, 11-30: 10-12, 31+: 15-18
  const targetCount = data.moduleNum <= 10 ? 8 : data.moduleNum <= 30 ? 12 : 18;
  for (let i = 0; i < Math.min(targetCount, shuffled.length); i++) {
    const correct = shuffled[i];
    const wrongs = shuffled.filter((_, idx) => idx !== i).slice(0, 3);

    content += `${i + 1}. What does "${correct.word}" mean?\n`;

    // Shuffle options
    const options = [correct.english, ...wrongs.map(w => w.english)].sort(() => Math.random() - 0.5);

    for (const opt of options) {
      const marker = opt === correct.english ? '[x]' : '[ ]';
      content += `   - ${marker} ${opt}\n`;
    }
    content += `   > "${correct.word}" means "${correct.english}"\n\n`;
  }

  return {
    type: 'quiz',
    title: variant === 0 ? 'Vocabulary Quiz' : 'Meaning Check',
    content,
    difficulty: 'B',
  };
}

function generateUnjumble(data: ModuleData): GeneratedActivity | null {
  // For early modules, accept 2-word phrases; for later, require 3+
  const minWords = data.moduleNum <= 30 ? 2 : 3;

  const examples = data.examples.filter(e => {
    const words = e.ukrainian.split(/\s+/);
    return words.length >= minWords && words.length <= 8;
  });

  if (examples.length < 3) return null;

  let content = `> Drag the words into the correct order to form a sentence.\n\n`;

  // Adaptive count: modules 1-10: 8 items, 11-30: 12, 31+: 18
  const targetCount = data.moduleNum <= 10 ? 8 : data.moduleNum <= 30 ? 12 : 18;
  const usedExamples = examples.slice(0, targetCount);
  let num = 1;

  for (const ex of usedExamples) {
    const words = ex.ukrainian.split(/\s+/).map(w => w.replace(/[.,!?]/g, ''));
    const shuffled = [...words].sort(() => Math.random() - 0.5);

    content += `${num}. ${shuffled.join(' / ')}\n`;
    content += `   > [!answer] ${ex.ukrainian}\n`;
    content += `   > (${ex.english})\n\n`;
    num++;
  }

  return {
    type: 'unjumble',
    title: 'Word Order',
    content,
    difficulty: 'C',
  };
}

function generateTransform(data: ModuleData): GeneratedActivity | null {
  // This needs grammar-specific logic based on module type
  // For now, return null - will implement per grammar topic
  return null;
}

// =============================================================================
// MAIN GENERATOR
// =============================================================================

function generateActivities(data: ModuleData, enrich: boolean = false): GeneratedActivity[] {
  const activities: GeneratedActivity[] = [];
  const targets = TARGET_ACTIVITIES[data.level] || TARGET_ACTIVITIES['A1'];

  const existing = data.existingActivities;

  // Type A (Recognition) - generate if needed
  if (!existing.includes('match-up')) {
    const activity = generateMatchUp(data, 0);
    if (activity) activities.push(activity);
  }

  if (!existing.includes('true-false')) {
    const activity = generateTrueFalse(data);
    if (activity) activities.push(activity);
  }

  if (!existing.includes('group-sort') && data.vocabulary.length >= 8) {
    const activity = generateGroupSort(data);
    if (activity) activities.push(activity);
  }

  // Type B (Production) - ALWAYS generate when enriching, otherwise only if missing
  if (enrich || !existing.includes('fill-in')) {
    if (data.examples.length >= 3) {
      const activity = generateFillIn(data);
      if (activity) activities.push(activity);
    }
  }

  // Additional quiz variant if we have vocabulary
  if (data.vocabulary.length >= 8) {
    const activity = generateQuiz(data, 1);
    if (activity) activities.push(activity);
  }

  // Type C (Synthesis) - ALWAYS generate when enriching, otherwise only if missing
  if (enrich || (!existing.includes('unjumble') && !existing.includes('order'))) {
    const activity = generateUnjumble(data);
    if (activity) activities.push(activity);
  }

  return activities;
}

/**
 * Remove existing fill-in and unjumble activities from content
 */
function removeExistingActivities(content: string, types: string[]): string {
  let result = content;

  for (const type of types) {
    // Match activity block from ## type: to next ## or section divider
    const pattern = new RegExp(
      `\n## ${type}:[^\n]*\n(?:(?!## |# |---)[^\n]*\n)*`,
      'gi'
    );
    result = result.replace(pattern, '\n');
  }

  // Clean up multiple blank lines
  result = result.replace(/\n{3,}/g, '\n\n');

  return result;
}

function formatActivity(activity: GeneratedActivity): string {
  return `## ${activity.type}: ${activity.title}\n\n${activity.content}`;
}

async function processModule(modulePath: string, dryRun: boolean = false, enrich: boolean = false): Promise<void> {
  const data = await parseModule(modulePath);
  if (!data) {
    console.log(`  Skipping (couldn't parse)`);
    return;
  }

  const targets = TARGET_ACTIVITIES[data.level] || TARGET_ACTIVITIES['A1'];
  const currentCount = data.existingActivities.length;

  // Skip if already has enough activities (unless enriching)
  if (!enrich && currentCount >= targets.total) {
    console.log(`  Already has ${currentCount}/${targets.total} activities`);
    return;
  }

  const newActivities = generateActivities(data, enrich);

  if (newActivities.length === 0) {
    console.log(`  No new activities to add (insufficient content)`);
    return;
  }

  if (enrich) {
    console.log(`  Enriching: replacing fill-in/unjumble with ${newActivities.length} new activities`);
  } else {
    console.log(`  Adding ${newActivities.length} activities (${currentCount} → ${currentCount + newActivities.length})`);
  }

  if (dryRun) {
    for (const act of newActivities) {
      console.log(`    + ${act.type}: ${act.title} (${act.difficulty})`);
    }
    return;
  }

  // Read and potentially clean content
  let content = await readFile(modulePath, 'utf-8');

  // If enriching, remove existing fill-in and unjumble activities first
  if (enrich) {
    content = removeExistingActivities(content, ['fill-in', 'unjumble', 'order']);
  }

  // Find the end of Activities section (before Vocabulary/Словник)
  // Match both English and Ukrainian section headers, with or without ---
  const vocabPattern = /\n(---\n\n)?# (Vocabulary|Словник)/;
  const vocabMatch = content.match(vocabPattern);
  if (!vocabMatch || vocabMatch.index === undefined) {
    console.log(`  Can't find Vocabulary section marker`);
    return;
  }

  // Insert before the vocabulary section
  const insertPoint = vocabMatch.index;
  if (insertPoint < 0) {
    console.log(`  Can't find insertion point`);
    return;
  }

  const formattedActivities = newActivities.map(formatActivity).join('\n\n');
  const newContent = content.slice(0, insertPoint) + '\n\n' + formattedActivities + content.slice(insertPoint);

  await writeFile(modulePath, newContent);
  console.log(`  Written!`);
}

// =============================================================================
// CLI
// =============================================================================

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const dryRun = args.includes('--dry-run');
  const enrich = args.includes('--enrich');
  const rangeArg = args.find(a => !a.startsWith('--'));

  // Parse module range
  let startModule = 1;
  let endModule = 80; // Default to pre-B1 only

  if (rangeArg) {
    if (rangeArg.includes('-')) {
      const [start, end] = rangeArg.split('-').map(Number);
      startModule = start;
      endModule = end;
    } else {
      startModule = endModule = parseInt(rangeArg);
    }
  }

  console.log(`\nExercise Generator for Modules ${startModule}-${endModule}`);
  if (enrich) console.log('MODE: --enrich (replacing existing fill-in/unjumble)');
  console.log(dryRun ? '(DRY RUN - no files will be modified)\n' : '\n');

  for (let num = startModule; num <= endModule; num++) {
    const padded = String(num).padStart(2, '0');
    const modulePath = join(MODULES_DIR, `module-${padded}.md`);

    if (!existsSync(modulePath)) {
      continue;
    }

    console.log(`Module ${padded}:`);
    await processModule(modulePath, dryRun, enrich);
  }

  console.log('\nDone!');
}

main().catch(console.error);
