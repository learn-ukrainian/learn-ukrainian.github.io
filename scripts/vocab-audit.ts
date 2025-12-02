/**
 * vocab-audit.ts
 *
 * Scans module markdown for Ukrainian words and checks them against the vocabulary database.
 * Reports words that are:
 *   - Not in the database at all
 *   - Introduced in later modules (shouldn't appear yet)
 *
 * Usage:
 *   npx ts-node scripts/vocab-audit.ts [curriculum] [moduleNum]
 *
 * Examples:
 *   npx ts-node scripts/vocab-audit.ts l2-uk-en 81     # Audit single module
 *   npx ts-node scripts/vocab-audit.ts l2-uk-en 81-100 # Audit range
 *   npx ts-node scripts/vocab-audit.ts l2-uk-en        # Audit all modules
 */

import * as fs from 'fs';
import * as path from 'path';
import {
  getVocabDatabase,
  resetVocabDatabase,
  VocabEntry,
} from './lib/vocab-sqlite';

// =============================================================================
// Configuration
// =============================================================================

const CURRICULUM_DIR = path.join(__dirname, '..', 'curriculum');
const DEFAULT_CURRICULUM = 'l2-uk-en';

// Common Ukrainian words to ignore (grammatical particles, very basic words)
const IGNORE_WORDS = new Set([
  // Articles/particles
  'а', 'і', 'й', 'та', 'чи', 'або', 'ні', 'не', 'так', 'от', 'ось', 'ж', 'же', 'б', 'би',
  // Pronouns (usually taught very early)
  'я', 'ти', 'він', 'вона', 'воно', 'ми', 'ви', 'вони',
  'мене', 'тебе', 'його', 'її', 'нас', 'вас', 'їх',
  'мені', 'тобі', 'йому', 'їй', 'нам', 'вам', 'їм',
  'мій', 'моя', 'моє', 'мої', 'твій', 'твоя', 'твоє', 'твої',
  'наш', 'наша', 'наше', 'наші', 'ваш', 'ваша', 'ваше', 'ваші',
  'цей', 'ця', 'це', 'ці', 'той', 'та', 'те', 'ті',
  'який', 'яка', 'яке', 'які', 'що', 'хто', 'де', 'як', 'коли', 'чому',
  // Prepositions
  'в', 'у', 'на', 'з', 'із', 'зі', 'до', 'від', 'для', 'про', 'за', 'під', 'над', 'між', 'через', 'без', 'при', 'по',
  // Conjunctions
  'але', 'проте', 'однак', 'тому', 'бо', 'якщо', 'коли', 'щоб', 'хоча', 'хоч',
  // Very common verbs (taught in A1)
  'є', 'бути', 'мати', 'могти', 'хотіти', 'знати', 'робити', 'йти', 'їхати',
  // Numbers
  'один', 'одна', 'одне', 'два', 'дві', 'три', 'чотири', 'п\'ять',
  // Basic adverbs
  'тут', 'там', 'дуже', 'ще', 'вже', 'теж', 'також', 'тільки', 'лише',
]);

// Sections to potentially skip or flag differently
const METADATA_SECTIONS = ['---']; // YAML frontmatter

// =============================================================================
// Types
// =============================================================================

interface WordOccurrence {
  word: string;
  normalized: string;
  section: string;
  line: number;
  context: string;
}

interface AuditResult {
  moduleNum: number;
  totalUkrainianWords: number;
  uniqueWords: number;
  missingFromDb: WordInfo[];
  introducedLater: WordInfo[];
  inVocabSection: string[];
}

interface WordInfo {
  word: string;
  occurrences: WordOccurrence[];
  firstModule?: number;
}

// =============================================================================
// Ukrainian Word Detection
// =============================================================================

/**
 * Check if a character is Cyrillic
 */
function isCyrillic(char: string): boolean {
  const code = char.charCodeAt(0);
  return (code >= 0x0400 && code <= 0x04FF) || // Cyrillic block
         (code >= 0x0500 && code <= 0x052F);   // Cyrillic Supplement
}

/**
 * Check if a word is Ukrainian (contains Cyrillic characters)
 */
function isUkrainianWord(word: string): boolean {
  return word.split('').some(isCyrillic);
}

/**
 * Normalize a Ukrainian word for comparison
 */
function normalizeWord(word: string): string {
  return word
    .toLowerCase()
    .replace(/[«»„""'']/g, '') // Remove quotes
    .replace(/^[—–-]+|[—–-]+$/g, '') // Remove leading/trailing dashes
    .replace(/[.,!?;:()[\]{}]/g, '') // Remove punctuation
    .trim();
}

/**
 * Extract all Ukrainian words from text with their positions
 */
function extractUkrainianWords(content: string, moduleNum: number): WordOccurrence[] {
  const occurrences: WordOccurrence[] = [];
  const lines = content.split('\n');

  let currentSection = 'frontmatter';
  let inFrontmatter = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const lineNum = i + 1;

    // Track frontmatter
    if (line === '---') {
      if (!inFrontmatter && i === 0) {
        inFrontmatter = true;
        continue;
      } else if (inFrontmatter) {
        inFrontmatter = false;
        currentSection = 'content';
        continue;
      }
    }

    if (inFrontmatter) continue;

    // Track sections
    if (line.startsWith('# ')) {
      currentSection = line.substring(2).trim();
    } else if (line.startsWith('## ')) {
      currentSection = line.substring(3).trim();
    } else if (line.startsWith('### ')) {
      currentSection = line.substring(4).trim();
    }

    // Skip vocabulary table rows (these are intentional vocabulary)
    if (currentSection.toLowerCase().includes('словник') ||
        currentSection.toLowerCase().includes('vocabulary')) {
      continue;
    }

    // Skip Review Vocabulary section
    if (currentSection.toLowerCase().includes('review vocabulary')) {
      continue;
    }

    // Extract words from line
    // Split on whitespace and common delimiters, keeping Ukrainian apostrophe
    const words = line.split(/[\s\t,.:;!?()\[\]{}<>«»„""''\/|—–]+/);

    for (const word of words) {
      if (!word || word.length < 2) continue;
      if (!isUkrainianWord(word)) continue;

      const normalized = normalizeWord(word);
      if (!normalized || normalized.length < 2) continue;
      if (IGNORE_WORDS.has(normalized)) continue;

      // Get context (surrounding text)
      const contextStart = Math.max(0, line.indexOf(word) - 20);
      const contextEnd = Math.min(line.length, line.indexOf(word) + word.length + 20);
      const context = line.substring(contextStart, contextEnd).trim();

      occurrences.push({
        word,
        normalized,
        section: currentSection,
        line: lineNum,
        context: context.length > 50 ? context.substring(0, 50) + '...' : context,
      });
    }
  }

  return occurrences;
}

/**
 * Extract words from Словник section (to exclude from missing report)
 */
function extractVocabSectionWords(content: string): string[] {
  const vocabWords: string[] = [];

  // Find vocabulary section
  const vocabMatch = content.match(
    /# (?:Vocabulary|Словник)[^\n]*\n([\s\S]*?)(?=\n---|\n# (?!#))/i
  );

  if (!vocabMatch) return vocabWords;

  const vocabContent = vocabMatch[1];
  const lines = vocabContent.split('\n');

  for (const line of lines) {
    if (!line.includes('|')) continue;
    const cells = line.split('|').map(c => c.trim()).filter(c => c);
    if (cells.length >= 1 && !cells[0].includes('---') && !cells[0].toLowerCase().includes('word')) {
      const word = cells[0].replace(/\*\*/g, '').trim();
      if (word && isUkrainianWord(word)) {
        vocabWords.push(normalizeWord(word));
      }
    }
  }

  return vocabWords;
}

// =============================================================================
// Database Checking
// =============================================================================

/**
 * Check words against the vocabulary database
 */
function checkWordsAgainstDb(
  occurrences: WordOccurrence[],
  moduleNum: number,
  db: any,
  vocabSectionWords: string[]
): AuditResult {
  // Group occurrences by normalized word
  const wordMap = new Map<string, WordOccurrence[]>();

  for (const occ of occurrences) {
    const existing = wordMap.get(occ.normalized) || [];
    existing.push(occ);
    wordMap.set(occ.normalized, existing);
  }

  const missingFromDb: WordInfo[] = [];
  const introducedLater: WordInfo[] = [];

  const vocabSet = new Set(vocabSectionWords);

  for (const [normalized, occs] of wordMap.entries()) {
    // Skip if word is in Словник section
    if (vocabSet.has(normalized)) continue;

    // Check database
    const entry = db.getEntry(normalized);

    if (!entry) {
      // Try without apostrophe variations
      const withoutApostrophe = normalized.replace(/['ʼ']/g, '');
      const entryAlt = db.getEntry(withoutApostrophe);

      if (!entryAlt) {
        missingFromDb.push({
          word: normalized,
          occurrences: occs,
        });
      } else if (entryAlt.first_module > moduleNum) {
        introducedLater.push({
          word: normalized,
          occurrences: occs,
          firstModule: entryAlt.first_module,
        });
      }
    } else if (entry.first_module > moduleNum) {
      introducedLater.push({
        word: normalized,
        occurrences: occs,
        firstModule: entry.first_module,
      });
    }
  }

  // Sort by number of occurrences (most frequent first)
  missingFromDb.sort((a, b) => b.occurrences.length - a.occurrences.length);
  introducedLater.sort((a, b) => b.occurrences.length - a.occurrences.length);

  return {
    moduleNum,
    totalUkrainianWords: occurrences.length,
    uniqueWords: wordMap.size,
    missingFromDb,
    introducedLater,
    inVocabSection: vocabSectionWords,
  };
}

// =============================================================================
// Module Processing
// =============================================================================

/**
 * Process a single module
 */
function processModule(
  modulePath: string,
  moduleNum: number,
  db: any
): AuditResult {
  const content = fs.readFileSync(modulePath, 'utf-8');

  // Extract Ukrainian words from content
  const occurrences = extractUkrainianWords(content, moduleNum);

  // Extract words from Словник section
  const vocabSectionWords = extractVocabSectionWords(content);

  // Check against database
  return checkWordsAgainstDb(occurrences, moduleNum, db, vocabSectionWords);
}

/**
 * Print audit results
 */
function printResults(result: AuditResult): void {
  console.log(`\n${'='.repeat(60)}`);
  console.log(`MODULE ${result.moduleNum}`);
  console.log('='.repeat(60));

  console.log(`\nTotal Ukrainian words found: ${result.totalUkrainianWords}`);
  console.log(`Unique words: ${result.uniqueWords}`);
  console.log(`Words in Словник: ${result.inVocabSection.length}`);

  if (result.missingFromDb.length > 0) {
    console.log(`\n${'─'.repeat(40)}`);
    console.log(`MISSING FROM DATABASE: ${result.missingFromDb.length} words`);
    console.log('─'.repeat(40));

    for (const info of result.missingFromDb.slice(0, 30)) { // Limit to 30
      console.log(`\n  "${info.word}" (${info.occurrences.length}x)`);
      // Show first 3 occurrences
      for (const occ of info.occurrences.slice(0, 3)) {
        console.log(`    - [${occ.section}] L${occ.line}: "${occ.context}"`);
      }
      if (info.occurrences.length > 3) {
        console.log(`    ... and ${info.occurrences.length - 3} more occurrences`);
      }
    }

    if (result.missingFromDb.length > 30) {
      console.log(`\n  ... and ${result.missingFromDb.length - 30} more words`);
    }
  }

  if (result.introducedLater.length > 0) {
    console.log(`\n${'─'.repeat(40)}`);
    console.log(`INTRODUCED IN LATER MODULES: ${result.introducedLater.length} words`);
    console.log('─'.repeat(40));

    for (const info of result.introducedLater.slice(0, 20)) { // Limit to 20
      console.log(`\n  "${info.word}" (first in module ${info.firstModule}, ${info.occurrences.length}x here)`);
      for (const occ of info.occurrences.slice(0, 2)) {
        console.log(`    - [${occ.section}] L${occ.line}: "${occ.context}"`);
      }
    }

    if (result.introducedLater.length > 20) {
      console.log(`\n  ... and ${result.introducedLater.length - 20} more words`);
    }
  }

  if (result.missingFromDb.length === 0 && result.introducedLater.length === 0) {
    console.log(`\n  All Ukrainian words are properly introduced in vocabulary.`);
  }
}

// =============================================================================
// Main
// =============================================================================

function main(): void {
  const args = process.argv.slice(2);
  const curriculum = args[0] || DEFAULT_CURRICULUM;
  let moduleRange = args[1];

  const curriculumPath = path.join(CURRICULUM_DIR, curriculum);
  const dbPath = path.join(curriculumPath, 'vocabulary.db');
  const modulesDir = path.join(curriculumPath, 'modules');

  if (!fs.existsSync(curriculumPath)) {
    console.error(`Curriculum not found: ${curriculumPath}`);
    process.exit(1);
  }

  if (!fs.existsSync(dbPath)) {
    console.error(`Database not found: ${dbPath}`);
    console.error(`Run 'npm run vocab:init' first.`);
    process.exit(1);
  }

  console.log(`\n${'='.repeat(60)}`);
  console.log('VOCABULARY AUDIT');
  console.log('='.repeat(60));
  console.log(`\nCurriculum: ${curriculum}`);
  console.log(`Database: ${dbPath}`);

  // Reset singleton and get database
  resetVocabDatabase();
  const db = getVocabDatabase(curriculumPath);

  // Determine which modules to process
  let modulesToProcess: number[] = [];

  if (!moduleRange) {
    // All modules
    const files = fs.readdirSync(modulesDir)
      .filter(f => f.match(/^module-\d+\.md$/))
      .map(f => parseInt(f.match(/\d+/)?.[0] || '0'))
      .sort((a, b) => a - b);
    modulesToProcess = files;
    console.log(`Mode: All modules (${files.length})`);
  } else if (moduleRange.includes('-')) {
    // Range
    const [start, end] = moduleRange.split('-').map(n => parseInt(n));
    for (let i = start; i <= end; i++) {
      modulesToProcess.push(i);
    }
    console.log(`Mode: Modules ${start}-${end}`);
  } else {
    // Single module
    modulesToProcess = [parseInt(moduleRange)];
    console.log(`Mode: Module ${moduleRange}`);
  }

  // Process modules
  let totalMissing = 0;
  let totalLater = 0;

  for (const moduleNum of modulesToProcess) {
    const modulePath = path.join(modulesDir, `module-${moduleNum}.md`);

    if (!fs.existsSync(modulePath)) {
      console.log(`\nModule ${moduleNum}: File not found, skipping`);
      continue;
    }

    const result = processModule(modulePath, moduleNum, db);
    printResults(result);

    totalMissing += result.missingFromDb.length;
    totalLater += result.introducedLater.length;
  }

  // Summary
  console.log(`\n${'='.repeat(60)}`);
  console.log('SUMMARY');
  console.log('='.repeat(60));
  console.log(`\nModules audited: ${modulesToProcess.length}`);
  console.log(`Total words missing from DB: ${totalMissing}`);
  console.log(`Total words introduced later: ${totalLater}`);

  db.close();

  console.log(`\n${'='.repeat(60)}\n`);
}

main();
