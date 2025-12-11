/**
 * vocab-init.ts
 *
 * Initialize a fresh SQLite vocabulary database.
 *
 * Usage:
 *   npx ts-node scripts/vocab-init.ts [curriculum]
 *
 * Example:
 *   npx ts-node scripts/vocab-init.ts l2-uk-en
 *
 * This creates:
 *   curriculum/{curriculum}/vocabulary.db
 */

import Database from 'better-sqlite3';
import * as fs from 'fs';
import * as path from 'path';

// =============================================================================
// Configuration
// =============================================================================

const CURRICULUM_DIR = path.join(__dirname, '..', 'curriculum');
const DEFAULT_CURRICULUM = 'l2-uk-en';

// =============================================================================
// Schema
// =============================================================================

const SCHEMA = `
-- Lemmas: single words
CREATE TABLE IF NOT EXISTS lemmas (
  id TEXT PRIMARY KEY,
  uk TEXT UNIQUE NOT NULL,
  ipa TEXT,
  en TEXT,
  pos TEXT DEFAULT 'noun',
  gender TEXT,
  first_module INTEGER,
  level TEXT,
  notes TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Expressions: multi-word units (idioms, collocations, phrases)
CREATE TABLE IF NOT EXISTS expressions (
  id TEXT PRIMARY KEY,
  uk TEXT UNIQUE NOT NULL,
  ipa TEXT,
  en TEXT,
  type TEXT DEFAULT 'phrase',  -- idiom, collocation, phrase, proverb
  literal_en TEXT,             -- literal translation for idioms
  register TEXT DEFAULT 'neutral',  -- formal, informal, neutral
  first_module INTEGER,
  level TEXT,
  notes TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Expression components: links expressions to their component lemmas
CREATE TABLE IF NOT EXISTS expression_components (
  expression_id TEXT NOT NULL REFERENCES expressions(id) ON DELETE CASCADE,
  lemma_id TEXT REFERENCES lemmas(id) ON DELETE SET NULL,
  word TEXT NOT NULL,          -- The word as it appears (may differ from lemma)
  position INTEGER NOT NULL,   -- Word position in expression (0-indexed)
  PRIMARY KEY (expression_id, position)
);

-- Module vocabulary: tracks which vocab appears in which modules
CREATE TABLE IF NOT EXISTS module_vocabulary (
  module_num INTEGER NOT NULL,
  entry_type TEXT NOT NULL,    -- 'lemma' or 'expression'
  entry_id TEXT NOT NULL,
  is_new INTEGER DEFAULT 1,    -- 1 if first introduced, 0 if review
  PRIMARY KEY (module_num, entry_type, entry_id)
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_lemmas_uk ON lemmas(uk);
CREATE INDEX IF NOT EXISTS idx_lemmas_first_module ON lemmas(first_module);
CREATE INDEX IF NOT EXISTS idx_lemmas_level ON lemmas(level);

CREATE INDEX IF NOT EXISTS idx_expressions_uk ON expressions(uk);
CREATE INDEX IF NOT EXISTS idx_expressions_first_module ON expressions(first_module);
CREATE INDEX IF NOT EXISTS idx_expressions_type ON expressions(type);

CREATE INDEX IF NOT EXISTS idx_expr_components_lemma ON expression_components(lemma_id);
CREATE INDEX IF NOT EXISTS idx_module_vocab_module ON module_vocabulary(module_num);

-- Trigger to update updated_at on lemmas
CREATE TRIGGER IF NOT EXISTS lemmas_updated_at
  AFTER UPDATE ON lemmas
  BEGIN
    UPDATE lemmas SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
  END;

-- Trigger to update updated_at on expressions
CREATE TRIGGER IF NOT EXISTS expressions_updated_at
  AFTER UPDATE ON expressions
  BEGIN
    UPDATE expressions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
  END;
`;

// =============================================================================
// Main
// =============================================================================

/**
 *
 */
function main(): void {
  const args = process.argv.slice(2);
  const curriculum = args[0] || DEFAULT_CURRICULUM;
  const force = args.includes('--force');

  const curriculumPath = path.join(CURRICULUM_DIR, curriculum);
  const dbPath = path.join(curriculumPath, 'vocabulary.db');

  if (!fs.existsSync(curriculumPath)) {
    console.error(`Curriculum not found: ${curriculumPath}`);
    process.exit(1);
  }

  // Check if DB exists
  if (fs.existsSync(dbPath)) {
    if (force) {
      console.log(`Removing existing database: ${dbPath}`);
      fs.unlinkSync(dbPath);
    } else {
      console.error(`Database already exists: ${dbPath}`);
      console.error(`Use --force to overwrite.`);
      process.exit(1);
    }
  }

  console.log(`\n=== Vocabulary Database Initialization ===\n`);
  console.log(`Curriculum: ${curriculum}`);
  console.log(`Database: ${dbPath}\n`);

  // Create database
  const db = new Database(dbPath);

  // Enable foreign keys
  db.pragma('foreign_keys = ON');

  // Create schema
  console.log('Creating schema...');
  db.exec(SCHEMA);

  // Verify tables exist
  const tables = db.prepare(`
    SELECT name FROM sqlite_master WHERE type='table' ORDER BY name
  `).all() as { name: string }[];

  console.log('\nCreated tables:');
  for (const table of tables) {
    const count = db.prepare(`SELECT COUNT(*) as count FROM ${table.name}`).get() as { count: number };
    console.log(`  - ${table.name} (${count.count} rows)`);
  }

  // Show indexes
  const indexes = db.prepare(`
    SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%' ORDER BY name
  `).all() as { name: string }[];

  console.log('\nCreated indexes:');
  for (const index of indexes) {
    console.log(`  - ${index.name}`);
  }

  db.close();

  console.log(`\n✅ Database initialized: ${dbPath}`);
  console.log('\nNext steps:');
  console.log('  1. Run vocab:scan to populate from module MDs');
  console.log('  2. Run vocab:enrich to update MDs from DB');
  console.log(`\n=== Done ===\n`);
}

main();
