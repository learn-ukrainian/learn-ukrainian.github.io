/**
 * vocab-scan.ts
 *
 * Scans all module markdown files and populates the SQLite vocabulary database.
 * Detects lemmas vs expressions and tracks first appearances.
 *
 * Usage:
 *   npx ts-node scripts/vocab-scan.ts [curriculum] [moduleNum]
 *
 * Examples:
 *   npx ts-node scripts/vocab-scan.ts l2-uk-en        # Scan all modules
 *   npx ts-node scripts/vocab-scan.ts l2-uk-en 82    # Scan single module
 */

import * as fs from 'fs';
import * as path from 'path';
import {
  VocabDatabase,
  getVocabDatabase,
  resetVocabDatabase,
  isExpression,
  getLevelFromModule,
} from './lib/vocab-sqlite';

// =============================================================================
// Configuration
// =============================================================================

const CURRICULUM_DIR = path.join(__dirname, '..', 'curriculum');
const DEFAULT_CURRICULUM = 'l2-uk-en';

// =============================================================================
// Types
// =============================================================================

interface VocabRow {
  uk: string;
  ipa?: string;
  en: string;
  pos?: string;
  gender?: string;
  notes?: string;
}

interface ScanResult {
  moduleNum: number;
  level: string;
  lemmasAdded: number;
  expressionsAdded: number;
  lemmasUpdated: number;
  expressionsUpdated: number;
}

// =============================================================================
// Vocabulary Extraction
// =============================================================================

/**
 * Extract vocabulary rows from module markdown
 */
function extractVocabulary(content: string, moduleNum: number): VocabRow[] {
  const rows: VocabRow[] = [];

  // Find vocabulary section (main, not review)
  const vocabMatch = content.match(
    /# (?:Vocabulary|Словник)[^\n]*\n([\s\S]*?)(?=\n---|\n# (?:Letter Groups|Підсумок|Summary|Review Vocabulary|Вправи|Activities)|$)/i
  );

  if (!vocabMatch) {
    return rows;
  }

  const vocabContent = vocabMatch[1];

  // Find table in vocab content
  const tableMatch = vocabContent.match(/\|[^\n]+\|\n\|[-|\s]+\|\n([\s\S]*?)(?=\n\n|$)/);

  if (!tableMatch) {
    return rows;
  }

  const tableRows = tableMatch[1].trim().split('\n');

  for (const row of tableRows) {
    if (!row.trim() || !row.includes('|')) continue;

    const cells = row.split('|').map(c => c.trim()).filter(c => c);
    if (cells.length < 2) continue;

    const vocabRow = parseVocabRow(cells, moduleNum);
    if (vocabRow.uk) {
      rows.push(vocabRow);
    }
  }

  return rows;
}

/**
 * Parse a vocabulary table row
 * Handles multiple column formats
 */
function parseVocabRow(cells: string[], moduleNum: number): VocabRow {
  let uk = '';
  let ipa: string | undefined;
  let en = '';
  let pos: string | undefined;
  let gender: string | undefined;
  let notes: string | undefined;

  if (cells.length >= 7) {
    // 7 columns: Word | Translit | IPA | English | POS | Gender | Note
    uk = cells[0] || '';
    // translit = cells[1]; // Skip
    ipa = cells[2] || undefined;
    en = cells[3] || '';
    pos = cells[4] || undefined;
    gender = normalizeGender(cells[5]);
    notes = cells[6] || undefined;
  } else if (cells.length === 6) {
    // 6 columns: Word | IPA | English | POS | Gender | Note
    uk = cells[0] || '';
    ipa = cells[1] || undefined;
    en = cells[2] || '';
    pos = cells[3] || undefined;
    gender = normalizeGender(cells[4]);
    notes = cells[5] || undefined;
  } else if (cells.length === 5) {
    // 5 columns: Word | IPA | English | POS | Gender
    uk = cells[0] || '';
    ipa = cells[1] || undefined;
    en = cells[2] || '';
    pos = cells[3] || undefined;
    gender = normalizeGender(cells[4]);
  } else if (cells.length === 4) {
    // 4 columns: Word | IPA | English | Notes
    uk = cells[0] || '';
    ipa = cells[1] || undefined;
    en = cells[2] || '';
    notes = cells[3] || undefined;
  } else if (cells.length === 3) {
    // 3 columns: Word | Translation | Notes
    uk = cells[0] || '';
    en = cells[1] || '';
    notes = cells[2] || undefined;
  } else if (cells.length === 2) {
    // 2 columns: Word | Translation
    uk = cells[0] || '';
    en = cells[1] || '';
  }

  // Clean up values
  uk = uk.replace(/\*\*/g, '').trim();
  ipa = ipa && ipa !== '-' ? ipa.trim() : undefined;
  en = en.replace(/\*\*/g, '').trim();
  pos = pos && pos !== '-' ? normalizePOS(pos) : undefined;
  notes = notes && notes !== '-' ? notes.trim() : undefined;

  return { uk, ipa, en, pos, gender, notes };
}

/**
 * Normalize gender value
 */
function normalizeGender(value: string | undefined): string | undefined {
  if (!value || value === '-' || value === '') return undefined;
  const v = value.toLowerCase().trim();
  if (v.startsWith('m')) return 'm';
  if (v.startsWith('f')) return 'f';
  if (v.startsWith('n')) return 'n';
  if (v === 'pl' || v === 'plural') return 'pl';
  return undefined;
}

/**
 * Normalize POS value
 */
function normalizePOS(value: string): string {
  const v = value.toLowerCase().trim();
  const posMap: Record<string, string> = {
    'noun': 'noun',
    'verb': 'verb',
    'adj': 'adj',
    'adjective': 'adj',
    'adv': 'adv',
    'adverb': 'adv',
    'prep': 'prep',
    'preposition': 'prep',
    'conj': 'conj',
    'conjunction': 'conj',
    'pron': 'pron',
    'pronoun': 'pron',
    'num': 'num',
    'number': 'num',
    'numeral': 'num',
    'phrase': 'phrase',
    'particle': 'particle',
    'part': 'particle',
    'interj': 'interjection',
    'interjection': 'interjection',
    'collocation': 'collocation',
  };
  return posMap[v] || 'noun';
}

// =============================================================================
// Module Processing
// =============================================================================

/**
 * Process a single module and add vocabulary to database
 */
function processModule(
  modulePath: string,
  moduleNum: number,
  db: VocabDatabase
): ScanResult {
  const content = fs.readFileSync(modulePath, 'utf-8');
  const level = getLevelFromModule(moduleNum);

  const result: ScanResult = {
    moduleNum,
    level,
    lemmasAdded: 0,
    expressionsAdded: 0,
    lemmasUpdated: 0,
    expressionsUpdated: 0,
  };

  // Extract vocabulary from MD
  const vocabRows = extractVocabulary(content, moduleNum);

  if (vocabRows.length === 0) {
    return result;
  }

  for (const row of vocabRows) {
    // Check if entry already exists
    const existing = db.getEntry(row.uk);

    // Add or update entry
    const entry = db.addEntry(
      row.uk,
      row.en,
      moduleNum,
      row.ipa,
      row.pos,
      row.gender,
      row.notes
    );

    if (entry.type === 'expression') {
      if (existing) {
        result.expressionsUpdated++;
      } else {
        result.expressionsAdded++;
      }
    } else {
      if (existing) {
        result.lemmasUpdated++;
      } else {
        result.lemmasAdded++;
      }
    }
  }

  return result;
}

/**
 * Process all modules in a curriculum
 */
async function processAllModules(curriculumPath: string, db: VocabDatabase): Promise<ScanResult[]> {
  // Use shared file discovery logic
  const curriculumName = path.basename(curriculumPath);

  // Dynamic import or require since processAllModules was sync-ish in structure but findModuleFiles is async
  // We need to change processAllModules to async (it is called by main which can await)
  const { findModuleFiles } = require('./lib/utils/files');
  const moduleFiles = await findModuleFiles(curriculumName);

  const results: ScanResult[] = [];

  console.log(`Found ${moduleFiles.length} module files\n`);

  for (const file of moduleFiles) {
    const start = Date.now();
    // processModule is sync, reading file content
    const result = processModule(file.path, file.moduleNum, db);
    results.push(result);

    const total = result.lemmasAdded + result.expressionsAdded + result.lemmasUpdated + result.expressionsUpdated;
    if (total > 0) {
      const exprStr = result.expressionsAdded > 0 ? ` (+${result.expressionsAdded} expr)` : '';
      console.log(`  Module ${file.moduleNum.toString().padStart(3)} (${result.level}): ${result.lemmasAdded} lemmas${exprStr}`);
    }
  }

  return results;
}

// =============================================================================
// Main
// =============================================================================

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const curriculum = args[0] || DEFAULT_CURRICULUM;
  const moduleNum = args[1] ? parseInt(args[1]) : null;

  const curriculumPath = path.join(CURRICULUM_DIR, curriculum);
  const dbPath = path.join(curriculumPath, 'vocabulary.db');

  if (!fs.existsSync(curriculumPath)) {
    console.error(`Curriculum not found: ${curriculumPath}`);
    process.exit(1);
  }

  if (!fs.existsSync(dbPath)) {
    console.error(`Database not found: ${dbPath}`);
    console.error(`Run 'npm run vocab:init' first.`);
    process.exit(1);
  }

  console.log(`\n=== Vocabulary Scanner ===\n`);
  console.log(`Curriculum: ${curriculum}`);
  console.log(`Database: ${dbPath}`);
  if (moduleNum) {
    console.log(`Module: ${moduleNum}`);
  } else {
    console.log(`Mode: All modules`);
  }
  console.log();

  // Reset singleton to ensure fresh connection
  resetVocabDatabase();
  const db = getVocabDatabase(curriculumPath);

  let results: ScanResult[];

  if (moduleNum) {
    // Process single module - try to find it via getModulePath from utils
    // Using require to avoid top-level import issues if files.ts changed
    const { getModulePath } = require('./lib/utils/files');
    const modulePath = getModulePath(curriculum, moduleNum);

    if (!fs.existsSync(modulePath)) {
      console.error(`Module not found: ${modulePath}`);
      process.exit(1);
    }
    results = [processModule(modulePath, moduleNum, db)];
  } else {
    // Process all modules
    results = await processAllModules(curriculumPath, db);
  }

  // Summary
  console.log('\n--- Summary ---\n');

  const totalLemmas = results.reduce((sum, r) => sum + r.lemmasAdded, 0);
  const totalExprs = results.reduce((sum, r) => sum + r.expressionsAdded, 0);
  const updatedLemmas = results.reduce((sum, r) => sum + r.lemmasUpdated, 0);
  const updatedExprs = results.reduce((sum, r) => sum + r.expressionsUpdated, 0);

  console.log(`Modules processed: ${results.length}`);
  console.log(`New lemmas: ${totalLemmas}`);
  console.log(`New expressions: ${totalExprs}`);
  console.log(`Updated lemmas: ${updatedLemmas}`);
  console.log(`Updated expressions: ${updatedExprs}`);

  // Show database stats
  const stats = db.getStats();
  console.log('\n--- Database Stats ---\n');
  console.log(`Total lemmas: ${stats.totalLemmas}`);
  console.log(`Total expressions: ${stats.totalExpressions}`);

  console.log('\nBy Level:');
  for (const level of ['A1', 'A2', 'A2+', 'B1', 'B1+', 'B2', 'B2+', 'C1']) {
    const data = stats.byLevel[level];
    if (data) {
      console.log(`  ${level}: ${data.lemmas} lemmas, ${data.expressions} expressions`);
    }
  }

  console.log('\nBy Expression Type:');
  for (const [type, count] of Object.entries(stats.byType)) {
    console.log(`  ${type}: ${count}`);
  }

  console.log('\nBy Part of Speech:');
  const sortedPOS = Object.entries(stats.byPOS).sort((a, b) => b[1] - a[1]);
  for (const [pos, count] of sortedPOS.slice(0, 10)) {
    console.log(`  ${pos}: ${count}`);
  }

  db.close();

  console.log(`\n=== Done ===\n`);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
