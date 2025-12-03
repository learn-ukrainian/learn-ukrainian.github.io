/**
 * renumber-b2.ts
 *
 * Renumbers B2 modules from 141-190 to 161-210.
 * Updates:
 * - Module filenames
 * - Frontmatter (module number)
 * - vocabulary.db (first_module references)
 * - Review Vocabulary sections in all modules
 * - Output files (HTML/JSON)
 *
 * Usage:
 *   npx ts-node scripts/renumber-b2.ts [--dry-run]
 */

import * as fs from 'fs';
import * as path from 'path';
import Database from 'better-sqlite3';

// =============================================================================
// Configuration
// =============================================================================

const OLD_START = 141;
const OLD_END = 190;
const OFFSET = 20; // New number = old number + 20

const CURRICULUM_DIR = path.join(__dirname, '..', 'curriculum', 'l2-uk-en');
const MODULES_DIR = path.join(CURRICULUM_DIR, 'modules');
const OUTPUT_DIR = path.join(__dirname, '..', 'output');
const VOCAB_DB = path.join(CURRICULUM_DIR, 'vocabulary.db');

const DRY_RUN = process.argv.includes('--dry-run');

// =============================================================================
// Helpers
// =============================================================================

function log(msg: string) {
  console.log(DRY_RUN ? `[DRY-RUN] ${msg}` : msg);
}

function oldToNew(oldNum: number): number {
  return oldNum + OFFSET;
}

function padNum(n: number): string {
  return n.toString().padStart(2, '0');
}

// =============================================================================
// Phase 1: Rename Module Files
// =============================================================================

function renameModuleFiles(): void {
  log('\n=== Phase 1: Renaming module files ===\n');

  // Rename in reverse order to avoid conflicts (190->210, then 189->209, etc.)
  for (let oldNum = OLD_END; oldNum >= OLD_START; oldNum--) {
    const newNum = oldToNew(oldNum);
    const oldFile = path.join(MODULES_DIR, `module-${padNum(oldNum)}.md`);
    const newFile = path.join(MODULES_DIR, `module-${newNum}.md`);

    if (fs.existsSync(oldFile)) {
      log(`  ${path.basename(oldFile)} -> ${path.basename(newFile)}`);
      if (!DRY_RUN) {
        fs.renameSync(oldFile, newFile);
      }
    } else {
      log(`  [SKIP] ${path.basename(oldFile)} does not exist`);
    }
  }
}

// =============================================================================
// Phase 2: Update Frontmatter
// =============================================================================

function updateFrontmatter(): void {
  log('\n=== Phase 2: Updating frontmatter ===\n');

  for (let oldNum = OLD_START; oldNum <= OLD_END; oldNum++) {
    const newNum = oldToNew(oldNum);
    const file = path.join(MODULES_DIR, `module-${newNum}.md`);

    if (!fs.existsSync(file)) {
      log(`  [SKIP] ${path.basename(file)} does not exist`);
      continue;
    }

    let content = fs.readFileSync(file, 'utf-8');

    // Update module number in frontmatter
    const oldModuleLine = `module: ${oldNum}`;
    const newModuleLine = `module: ${newNum}`;

    if (content.includes(oldModuleLine)) {
      content = content.replace(oldModuleLine, newModuleLine);
      log(`  ${path.basename(file)}: module ${oldNum} -> ${newNum}`);

      if (!DRY_RUN) {
        fs.writeFileSync(file, content, 'utf-8');
      }
    } else {
      log(`  [WARN] ${path.basename(file)}: module line not found`);
    }
  }
}

// =============================================================================
// Phase 3: Update Review Vocabulary References in ALL Modules
// =============================================================================

function updateReviewVocabulary(): void {
  log('\n=== Phase 3: Updating Review Vocabulary references ===\n');

  const files = fs.readdirSync(MODULES_DIR).filter(f => f.endsWith('.md'));
  let updatedCount = 0;

  for (const file of files) {
    const filePath = path.join(MODULES_DIR, file);
    let content = fs.readFileSync(filePath, 'utf-8');
    let modified = false;

    // Update Review Vocabulary table references
    // Pattern: | word | 141 | -> | word | 161 |
    for (let oldNum = OLD_START; oldNum <= OLD_END; oldNum++) {
      const newNum = oldToNew(oldNum);

      // Match patterns like "| 141 |" or "| 141|" at end of line
      const patterns = [
        new RegExp(`\\| ${oldNum} \\|`, 'g'),
        new RegExp(`\\| ${oldNum}\\|`, 'g'),
        new RegExp(`\\| ${oldNum}$`, 'gm'),
      ];

      for (const pattern of patterns) {
        if (pattern.test(content)) {
          content = content.replace(pattern, (match) => {
            return match.replace(oldNum.toString(), newNum.toString());
          });
          modified = true;
        }
      }
    }

    if (modified) {
      log(`  ${file}: Updated Review Vocabulary references`);
      updatedCount++;
      if (!DRY_RUN) {
        fs.writeFileSync(filePath, content, 'utf-8');
      }
    }
  }

  log(`  Total files updated: ${updatedCount}`);
}

// =============================================================================
// Phase 4: Update Vocabulary Database
// =============================================================================

function updateVocabularyDb(): void {
  log('\n=== Phase 4: Updating vocabulary.db ===\n');

  if (!fs.existsSync(VOCAB_DB)) {
    log('  [SKIP] vocabulary.db not found');
    return;
  }

  if (DRY_RUN) {
    log('  [DRY-RUN] Would update lemmas and expressions tables');
    return;
  }

  const db = new Database(VOCAB_DB);

  try {
    // Update lemmas
    const lemmaResult = db.prepare(`
      UPDATE lemmas
      SET first_module = first_module + ?
      WHERE first_module >= ? AND first_module <= ?
    `).run(OFFSET, OLD_START, OLD_END);
    log(`  Updated ${lemmaResult.changes} lemmas`);

    // Update expressions
    const exprResult = db.prepare(`
      UPDATE expressions
      SET first_module = first_module + ?
      WHERE first_module >= ? AND first_module <= ?
    `).run(OFFSET, OLD_START, OLD_END);
    log(`  Updated ${exprResult.changes} expressions`);

    // Update module_vocabulary
    const mvResult = db.prepare(`
      UPDATE module_vocabulary
      SET module_num = module_num + ?
      WHERE module_num >= ? AND module_num <= ?
    `).run(OFFSET, OLD_START, OLD_END);
    log(`  Updated ${mvResult.changes} module_vocabulary entries`);

  } finally {
    db.close();
  }
}

// =============================================================================
// Phase 5: Update Output Files
// =============================================================================

function updateOutputFiles(): void {
  log('\n=== Phase 5: Renaming output files ===\n');

  const levels = ['b2']; // B2 modules are in b2 folder
  const formats = ['html', 'json'];

  for (const format of formats) {
    for (const level of levels) {
      const dir = path.join(OUTPUT_DIR, format, 'l2-uk-en', level);

      if (!fs.existsSync(dir)) {
        log(`  [SKIP] ${dir} does not exist`);
        continue;
      }

      // Rename in reverse order
      for (let oldNum = OLD_END; oldNum >= OLD_START; oldNum--) {
        const newNum = oldToNew(oldNum);
        const oldFile = path.join(dir, `module-${padNum(oldNum)}.${format}`);
        const newFile = path.join(dir, `module-${newNum}.${format}`);

        if (fs.existsSync(oldFile)) {
          log(`  ${format}/${level}: module-${padNum(oldNum)} -> module-${newNum}`);
          if (!DRY_RUN) {
            fs.renameSync(oldFile, newFile);
          }
        }
      }
    }
  }
}

// =============================================================================
// Phase 6: Update Curriculum Plan Files
// =============================================================================

function updateCurriculumPlans(): void {
  log('\n=== Phase 6: Updating curriculum plan files ===\n');

  const planFiles = [
    path.join(CURRICULUM_DIR, 'curriculum-plan.md'),
    path.join(CURRICULUM_DIR, 'B2-CURRICULUM-PLAN.md'),
  ];

  for (const file of planFiles) {
    if (!fs.existsSync(file)) {
      log(`  [SKIP] ${path.basename(file)} not found`);
      continue;
    }

    let content = fs.readFileSync(file, 'utf-8');
    let modified = false;

    // Update module range references
    // 141-190 -> 161-210
    // 141-165 -> 161-185
    // 166-190 -> 186-210
    const replacements: [RegExp, string][] = [
      [/\b141-190\b/g, '161-210'],
      [/\b141-165\b/g, '161-185'],
      [/\b166-190\b/g, '186-210'],
      [/\bModules 141-190\b/g, 'Modules 161-210'],
      [/\bmodules 141-190\b/g, 'modules 161-210'],
    ];

    // Also update individual module numbers in tables
    for (let oldNum = OLD_START; oldNum <= OLD_END; oldNum++) {
      const newNum = oldToNew(oldNum);
      // Match "| 141 |" pattern in tables
      replacements.push([
        new RegExp(`\\| ${oldNum} \\|`, 'g'),
        `| ${newNum} |`
      ]);
    }

    for (const [pattern, replacement] of replacements) {
      if (pattern.test(content)) {
        content = content.replace(pattern, replacement);
        modified = true;
      }
    }

    if (modified) {
      log(`  ${path.basename(file)}: Updated module references`);
      if (!DRY_RUN) {
        fs.writeFileSync(file, content, 'utf-8');
      }
    }
  }
}

// =============================================================================
// Main
// =============================================================================

function main(): void {
  console.log('╔════════════════════════════════════════════════════════════╗');
  console.log('║  B2 Module Renumbering: 141-190 → 161-210                  ║');
  console.log('╚════════════════════════════════════════════════════════════╝');

  if (DRY_RUN) {
    console.log('\n⚠️  DRY RUN MODE - No changes will be made\n');
  }

  renameModuleFiles();
  updateFrontmatter();
  updateReviewVocabulary();
  updateVocabularyDb();
  updateOutputFiles();
  updateCurriculumPlans();

  console.log('\n✅ Renumbering complete!');

  if (!DRY_RUN) {
    console.log('\nNext steps:');
    console.log('  1. Review changes: git diff');
    console.log('  2. Regenerate output: npx ts-node scripts/generate.ts l2-uk-en');
    console.log('  3. Commit: git add -A && git commit -m "Renumber B2 modules 141-190 → 161-210"');
  }
}

main();
