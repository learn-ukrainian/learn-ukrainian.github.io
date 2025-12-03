/**
 * standardize-b1-vocab.ts
 *
 * Standardizes B1 vocabulary sections (modules 81-140) to the tier 3 format:
 * | Слово | Вимова | Переклад | ЧМ | Примітка |
 *
 * Handles three current formats:
 * 1. | Word | IPA | English | POS | Note | (5 cols) - direct translation
 * 2. | Word | IPA | English | Gender | (4 cols) - restructure, ЧМ=ім, Примітка=gender
 * 3. | Word | IPA | English | Notes | (4 cols) - restructure, ЧМ=-, Примітка=notes
 *
 * Usage:
 *   npx ts-node scripts/standardize-b1-vocab.ts [--dry-run]
 */

import * as fs from 'fs';
import * as path from 'path';

const MODULES_DIR = path.join(__dirname, '..', 'curriculum', 'l2-uk-en', 'modules');
const DRY_RUN = process.argv.includes('--dry-run');

// POS translations
const POS_MAP: Record<string, string> = {
  'noun': 'ім',
  'verb': 'дієсл',
  'adj': 'прикм',
  'adv': 'присл',
  'prep': 'прийм',
  'conj': 'сполучн',
  'pron': 'займ',
  'phrase': 'фраза',
  'interj': 'вигук',
  'part': 'частка',
  '-': '-',
  '': '-',
};

function log(msg: string) {
  console.log(DRY_RUN ? `[DRY-RUN] ${msg}` : msg);
}

function translatePOS(pos: string): string {
  const lower = pos.toLowerCase().trim();
  return POS_MAP[lower] || lower || '-';
}

function processModule(moduleNum: number): { changed: boolean; format: string } {
  const padded = moduleNum.toString().padStart(2, '0');
  const filePath = path.join(MODULES_DIR, `module-${padded}.md`);

  if (moduleNum >= 100) {
    // No padding for 3-digit modules
    const filePath3 = path.join(MODULES_DIR, `module-${moduleNum}.md`);
    if (fs.existsSync(filePath3)) {
      return processFile(filePath3, moduleNum);
    }
  }

  if (!fs.existsSync(filePath)) {
    log(`  [SKIP] module-${padded}.md not found`);
    return { changed: false, format: 'not_found' };
  }

  return processFile(filePath, moduleNum);
}

function processFile(filePath: string, moduleNum: number): { changed: boolean; format: string } {
  let content = fs.readFileSync(filePath, 'utf-8');
  const lines = content.split('\n');
  let modified = false;
  let detectedFormat = 'unknown';

  // Find vocabulary section
  let inVocabSection = false;
  let vocabHeaderLineIdx = -1;
  let vocabTableHeaderIdx = -1;
  let vocabTableSeparatorIdx = -1;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Detect vocabulary section start
    if (line.match(/^# (Vocabulary|Словник)\s*$/)) {
      inVocabSection = true;
      vocabHeaderLineIdx = i;
      continue;
    }

    // Detect Review Vocabulary (different section)
    if (line.match(/^# Review Vocabulary/)) {
      inVocabSection = false;
      continue;
    }

    // Detect next section
    if (inVocabSection && line.match(/^#[^#]/)) {
      inVocabSection = false;
      continue;
    }

    // Find the main vocab table header (not Review Vocabulary)
    if (inVocabSection && line.startsWith('| Word |')) {
      vocabTableHeaderIdx = i;
      vocabTableSeparatorIdx = i + 1;

      // Detect format
      if (line.includes('| POS |') && line.includes('| Note |')) {
        detectedFormat = '5col_pos_note';
      } else if (line.includes('| Gender |')) {
        detectedFormat = '4col_gender';
      } else if (line.includes('| Notes |')) {
        detectedFormat = '4col_notes';
      } else {
        detectedFormat = 'other';
      }
      break;
    }
  }

  if (vocabTableHeaderIdx === -1) {
    // Check if already standardized
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].startsWith('| Слово |')) {
        return { changed: false, format: 'already_standardized' };
      }
    }
    log(`  [WARN] module-${moduleNum}: No vocab table found`);
    return { changed: false, format: 'no_table' };
  }

  // Process based on format
  const newLines = [...lines];

  if (detectedFormat === '5col_pos_note') {
    // Simple header translation
    newLines[vocabTableHeaderIdx] = '| Слово | Вимова | Переклад | ЧМ | Примітка |';
    newLines[vocabTableSeparatorIdx] = '|-------|--------|----------|-----|----------|';

    // Translate POS values in data rows
    for (let i = vocabTableSeparatorIdx + 1; i < newLines.length; i++) {
      const line = newLines[i];
      if (!line.startsWith('|')) break;
      if (line.startsWith('| Word |')) break; // Hit another table

      const cols = line.split('|').map(c => c.trim());
      if (cols.length >= 6) {
        // cols: ['', 'Word', 'IPA', 'English', 'POS', 'Note', '']
        cols[4] = translatePOS(cols[4]);
        newLines[i] = '| ' + cols.slice(1, -1).join(' | ') + ' |';
      }
    }
    modified = true;

  } else if (detectedFormat === '4col_gender') {
    // Restructure: add ЧМ column with 'ім', move Gender to Примітка
    newLines[vocabTableHeaderIdx] = '| Слово | Вимова | Переклад | ЧМ | Примітка |';
    newLines[vocabTableSeparatorIdx] = '|-------|--------|----------|-----|----------|';

    for (let i = vocabTableSeparatorIdx + 1; i < newLines.length; i++) {
      const line = newLines[i];
      if (!line.startsWith('|')) break;
      if (line.startsWith('| Word |')) break;

      const cols = line.split('|').map(c => c.trim());
      if (cols.length >= 5) {
        // cols: ['', 'Word', 'IPA', 'English', 'Gender', '']
        const word = cols[1];
        const ipa = cols[2];
        const english = cols[3];
        const gender = cols[4];
        newLines[i] = `| ${word} | ${ipa} | ${english} | ім | ${gender} |`;
      }
    }
    modified = true;

  } else if (detectedFormat === '4col_notes') {
    // Restructure: add ЧМ column with '-', keep Notes as Примітка
    newLines[vocabTableHeaderIdx] = '| Слово | Вимова | Переклад | ЧМ | Примітка |';
    newLines[vocabTableSeparatorIdx] = '|-------|--------|----------|-----|----------|';

    for (let i = vocabTableSeparatorIdx + 1; i < newLines.length; i++) {
      const line = newLines[i];
      if (!line.startsWith('|')) break;
      if (line.startsWith('| Word |')) break;

      const cols = line.split('|').map(c => c.trim());
      if (cols.length >= 5) {
        // cols: ['', 'Word', 'IPA', 'English', 'Notes', '']
        const word = cols[1];
        const ipa = cols[2];
        const english = cols[3];
        const notes = cols[4];
        newLines[i] = `| ${word} | ${ipa} | ${english} | - | ${notes} |`;
      }
    }
    modified = true;

  } else {
    log(`  [WARN] module-${moduleNum}: Unhandled format: ${detectedFormat}`);
    return { changed: false, format: detectedFormat };
  }

  if (modified && !DRY_RUN) {
    fs.writeFileSync(filePath, newLines.join('\n'), 'utf-8');
  }

  return { changed: modified, format: detectedFormat };
}

function main() {
  console.log('╔════════════════════════════════════════════════════════════╗');
  console.log('║  B1 Vocabulary Standardization (Modules 81-140)            ║');
  console.log('║  Target: | Слово | Вимова | Переклад | ЧМ | Примітка |     ║');
  console.log('╚════════════════════════════════════════════════════════════╝');

  if (DRY_RUN) {
    console.log('\n⚠️  DRY RUN MODE - No changes will be made\n');
  }

  const stats = {
    '5col_pos_note': 0,
    '4col_gender': 0,
    '4col_notes': 0,
    'already_standardized': 0,
    'other': 0,
    'no_table': 0,
    'not_found': 0,
  };

  for (let m = 81; m <= 140; m++) {
    const result = processModule(m);
    stats[result.format as keyof typeof stats]++;

    if (result.changed) {
      log(`  module-${m}: ${result.format} → standardized`);
    }
  }

  console.log('\n=== Summary ===');
  console.log(`  5-column (POS/Note): ${stats['5col_pos_note']} modules`);
  console.log(`  4-column (Gender):   ${stats['4col_gender']} modules`);
  console.log(`  4-column (Notes):    ${stats['4col_notes']} modules`);
  console.log(`  Already standard:    ${stats['already_standardized']} modules`);
  console.log(`  Other/Unknown:       ${stats['other']} modules`);
  console.log(`  No table found:      ${stats['no_table']} modules`);

  if (!DRY_RUN) {
    console.log('\n✅ Standardization complete!');
  }
}

main();
