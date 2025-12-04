/**
 * vocab-sqlite.ts
 *
 * SQLite-based vocabulary database with expression support.
 * Replaces the CSV-based vocab-db.ts for richer data management.
 *
 * Features:
 * - Lemmas (single words) with full metadata
 * - Expressions (multi-word units) with type classification
 * - Expression-to-lemma component linking
 * - First-appearance tracking
 * - Module vocabulary tracking
 */

import Database, { Database as DatabaseType } from 'better-sqlite3';
import * as fs from 'fs';
import * as path from 'path';

// =============================================================================
// Types
// =============================================================================

export interface Lemma {
  id: string;
  uk: string;
  ipa?: string;
  en: string;
  pos: string;
  gender?: string;
  first_module: number;
  level: string;
  notes?: string;
}

export type ExpressionType = 'idiom' | 'collocation' | 'phrase' | 'proverb';
export type Register = 'formal' | 'informal' | 'neutral';

export interface Expression {
  id: string;
  uk: string;
  ipa?: string;
  en: string;
  type: ExpressionType;
  literal_en?: string;
  register: Register;
  first_module: number;
  level: string;
  notes?: string;
  components?: ExpressionComponent[];
}

export interface ExpressionComponent {
  expression_id: string;
  lemma_id?: string;
  word: string;
  position: number;
}

export interface VocabEntry {
  type: 'lemma' | 'expression';
  id: string;
  uk: string;
  ipa?: string;
  en: string;
  first_module: number;
  level: string;
  // Lemma-specific
  pos?: string;
  gender?: string;
  // Expression-specific
  expression_type?: ExpressionType;
  register?: Register;
  literal_en?: string;
  components?: ExpressionComponent[];
}

// =============================================================================
// Level Configuration
// =============================================================================

export const LEVEL_RANGES: Record<string, [number, number]> = {
  'A1': [1, 30],
  'A2': [31, 60],
  'A2+': [61, 80],
  'B1': [81, 120],
  'B1+': [121, 160],
  'B2': [161, 235],
  'B2+': [236, 310],
  'C1': [311, 400],
};

export function getLevelFromModule(moduleNum: number): string {
  for (const [level, [start, end]] of Object.entries(LEVEL_RANGES)) {
    if (moduleNum >= start && moduleNum <= end) {
      return level;
    }
  }
  return 'C1';
}

// =============================================================================
// ID Generation
// =============================================================================

function transliterateToAscii(uk: string): string {
  const map: Record<string, string> = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'h', 'ґ': 'g',
    'д': 'd', 'е': 'e', 'є': 'ye', 'ж': 'zh', 'з': 'z',
    'и': 'y', 'і': 'i', 'ї': 'yi', 'й': 'y', 'к': 'k',
    'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p',
    'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f',
    'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
    'ь': '', 'ю': 'yu', 'я': 'ya', "'": '', "\u2019": '',
    ' ': '-',
  };

  return uk
    .toLowerCase()
    .split('')
    .map(c => map[c] ?? c)
    .join('')
    .replace(/[^a-z0-9-]/g, '')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
}

export function generateLemmaId(uk: string): string {
  const slug = transliterateToAscii(uk);
  return `lemma-${slug}`;
}

export function generateExpressionId(uk: string): string {
  const slug = transliterateToAscii(uk);
  return `expr-${slug}`;
}

// =============================================================================
// Expression Detection
// =============================================================================

/**
 * Detect if a vocabulary entry is an expression (multi-word)
 */
export function isExpression(uk: string): boolean {
  // Multiple words = expression
  const words = uk.trim().split(/\s+/);
  return words.length > 1;
}

/**
 * Detect expression type based on patterns
 */
export function detectExpressionType(uk: string, en: string): ExpressionType {
  const ukLower = uk.toLowerCase();
  const enLower = en.toLowerCase();

  // Idiom patterns
  if (
    ukLower.includes('ні...ні') ||
    ukLower.includes('чи...чи') ||
    ukLower.startsWith('як ') ||
    enLower.includes('idiom') ||
    enLower.includes('literally:')
  ) {
    return 'idiom';
  }

  // Proverb patterns (usually longer, complete sentences)
  if (
    ukLower.includes('хто') && ukLower.includes('той') ||
    ukLower.endsWith('.') ||
    enLower.includes('proverb')
  ) {
    return 'proverb';
  }

  // Collocation: verb + noun patterns
  const words = uk.split(/\s+/);
  if (words.length === 2) {
    // Common collocation pattern: verb + noun
    return 'collocation';
  }

  // Default to phrase
  return 'phrase';
}

/**
 * Extract component words from an expression
 */
export function extractComponents(uk: string): string[] {
  return uk
    .trim()
    .split(/\s+/)
    .filter(w => w.length > 0);
}

// =============================================================================
// Vocabulary Database Class
// =============================================================================

export class VocabDatabase {
  private db: DatabaseType;
  private dbPath: string;

  constructor(curriculumPath: string) {
    this.dbPath = path.join(curriculumPath, 'vocabulary.db');

    if (!fs.existsSync(this.dbPath)) {
      throw new Error(`Database not found: ${this.dbPath}. Run vocab:init first.`);
    }

    this.db = new Database(this.dbPath);
    this.db.pragma('foreign_keys = ON');
  }

  // ===========================================================================
  // Lemma Operations
  // ===========================================================================

  getLemma(uk: string): Lemma | undefined {
    const row = this.db.prepare(`
      SELECT * FROM lemmas WHERE uk = ?
    `).get(uk.toLowerCase().trim()) as Lemma | undefined;
    return row;
  }

  getLemmaById(id: string): Lemma | undefined {
    return this.db.prepare(`SELECT * FROM lemmas WHERE id = ?`).get(id) as Lemma | undefined;
  }

  addLemma(lemma: Omit<Lemma, 'id'>): Lemma {
    const uk = lemma.uk.toLowerCase().trim();
    const id = generateLemmaId(uk);
    const level = lemma.level || getLevelFromModule(lemma.first_module);

    // Check if lemma already exists (by uk or by id)
    let existing = this.getLemma(uk);
    if (!existing) {
      existing = this.getLemmaById(id);
    }

    if (existing) {
      // Update existing
      this.db.prepare(`
        UPDATE lemmas SET
          ipa = COALESCE(?, ipa),
          en = COALESCE(?, en),
          pos = COALESCE(?, pos),
          gender = COALESCE(?, gender),
          first_module = MIN(first_module, ?),
          notes = COALESCE(?, notes)
        WHERE id = ?
      `).run(
        lemma.ipa || null,
        lemma.en || null,
        lemma.pos || null,
        lemma.gender || null,
        lemma.first_module,
        lemma.notes || null,
        existing.id
      );
    } else {
      // Insert new
      this.db.prepare(`
        INSERT INTO lemmas (id, uk, ipa, en, pos, gender, first_module, level, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
      `).run(
        id,
        uk,
        lemma.ipa || null,
        lemma.en,
        lemma.pos || 'noun',
        lemma.gender || null,
        lemma.first_module,
        level,
        lemma.notes || null
      );
    }

    // Return by id to ensure we get the right entry
    const lemmaId = existing?.id || id;
    return this.getLemmaById(lemmaId)!;
  }

  getAllLemmas(): Lemma[] {
    return this.db.prepare(`SELECT * FROM lemmas ORDER BY first_module, uk`).all() as Lemma[];
  }

  getLemmasByModule(moduleNum: number): Lemma[] {
    return this.db.prepare(`
      SELECT * FROM lemmas WHERE first_module = ? ORDER BY uk
    `).all(moduleNum) as Lemma[];
  }

  // ===========================================================================
  // Expression Operations
  // ===========================================================================

  getExpression(uk: string): Expression | undefined {
    const row = this.db.prepare(`
      SELECT * FROM expressions WHERE uk = ?
    `).get(uk.toLowerCase().trim()) as Expression | undefined;

    if (row) {
      row.components = this.getExpressionComponents(row.id);
    }

    return row;
  }

  getExpressionById(id: string): Expression | undefined {
    const row = this.db.prepare(`SELECT * FROM expressions WHERE id = ?`).get(id) as Expression | undefined;
    if (row) {
      row.components = this.getExpressionComponents(row.id);
    }
    return row;
  }

  addExpression(expr: Omit<Expression, 'id' | 'components'>, componentWords: string[]): Expression {
    const uk = expr.uk.toLowerCase().trim();
    const id = generateExpressionId(uk);
    const level = expr.level || getLevelFromModule(expr.first_module);

    // Check if expression already exists (by uk or by id)
    let existing = this.getExpression(uk);
    if (!existing) {
      existing = this.getExpressionById(id);
    }

    if (existing) {
      // Update existing
      this.db.prepare(`
        UPDATE expressions SET
          ipa = COALESCE(?, ipa),
          en = COALESCE(?, en),
          type = COALESCE(?, type),
          literal_en = COALESCE(?, literal_en),
          register = COALESCE(?, register),
          first_module = MIN(first_module, ?),
          notes = COALESCE(?, notes)
        WHERE id = ?
      `).run(
        expr.ipa || null,
        expr.en || null,
        expr.type || null,
        expr.literal_en || null,
        expr.register || null,
        expr.first_module,
        expr.notes || null,
        existing.id
      );
    } else {
      // Insert new
      this.db.prepare(`
        INSERT INTO expressions (id, uk, ipa, en, type, literal_en, register, first_module, level, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `).run(
        id,
        uk,
        expr.ipa || null,
        expr.en,
        expr.type || 'phrase',
        expr.literal_en || null,
        expr.register || 'neutral',
        expr.first_module,
        level,
        expr.notes || null
      );
    }

    // Add/update components
    const exprId = existing?.id || id;
    this.setExpressionComponents(exprId, componentWords);

    // Return by id to ensure we get the right entry
    return this.getExpressionById(exprId)!;
  }

  private getExpressionComponents(expressionId: string): ExpressionComponent[] {
    return this.db.prepare(`
      SELECT * FROM expression_components
      WHERE expression_id = ?
      ORDER BY position
    `).all(expressionId) as ExpressionComponent[];
  }

  private setExpressionComponents(expressionId: string, words: string[]): void {
    // Clear existing components
    this.db.prepare(`DELETE FROM expression_components WHERE expression_id = ?`).run(expressionId);

    // Add new components
    const insert = this.db.prepare(`
      INSERT INTO expression_components (expression_id, lemma_id, word, position)
      VALUES (?, ?, ?, ?)
    `);

    for (let i = 0; i < words.length; i++) {
      const word = words[i].toLowerCase().trim();
      const lemma = this.getLemma(word);
      insert.run(expressionId, lemma?.id || null, word, i);
    }
  }

  getAllExpressions(): Expression[] {
    const rows = this.db.prepare(`SELECT * FROM expressions ORDER BY first_module, uk`).all() as Expression[];
    return rows.map(row => {
      row.components = this.getExpressionComponents(row.id);
      return row;
    });
  }

  getExpressionsByModule(moduleNum: number): Expression[] {
    const rows = this.db.prepare(`
      SELECT * FROM expressions WHERE first_module = ? ORDER BY uk
    `).all(moduleNum) as Expression[];

    return rows.map(row => {
      row.components = this.getExpressionComponents(row.id);
      return row;
    });
  }

  // ===========================================================================
  // Unified Entry Operations
  // ===========================================================================

  /**
   * Add a vocabulary entry (auto-detects lemma vs expression)
   */
  addEntry(uk: string, en: string, moduleNum: number, ipa?: string, pos?: string, gender?: string, notes?: string): VocabEntry {
    if (isExpression(uk)) {
      const type = detectExpressionType(uk, en);
      const components = extractComponents(uk);

      const expr = this.addExpression({
        uk,
        ipa,
        en,
        type,
        register: 'neutral',
        first_module: moduleNum,
        level: getLevelFromModule(moduleNum),
        notes,
      }, components);

      return {
        type: 'expression',
        id: expr.id,
        uk: expr.uk,
        ipa: expr.ipa,
        en: expr.en,
        first_module: expr.first_module,
        level: expr.level,
        expression_type: expr.type,
        register: expr.register,
        components: expr.components,
      };
    } else {
      const lemma = this.addLemma({
        uk,
        ipa,
        en,
        pos: pos || 'noun',
        gender,
        first_module: moduleNum,
        level: getLevelFromModule(moduleNum),
        notes,
      });

      return {
        type: 'lemma',
        id: lemma.id,
        uk: lemma.uk,
        ipa: lemma.ipa,
        en: lemma.en,
        first_module: lemma.first_module,
        level: lemma.level,
        pos: lemma.pos,
        gender: lemma.gender,
      };
    }
  }

  /**
   * Get a vocabulary entry (lemma or expression)
   */
  getEntry(uk: string): VocabEntry | undefined {
    if (isExpression(uk)) {
      const expr = this.getExpression(uk);
      if (expr) {
        return {
          type: 'expression',
          id: expr.id,
          uk: expr.uk,
          ipa: expr.ipa,
          en: expr.en,
          first_module: expr.first_module,
          level: expr.level,
          expression_type: expr.type,
          register: expr.register,
          literal_en: expr.literal_en,
          components: expr.components,
        };
      }
    } else {
      const lemma = this.getLemma(uk);
      if (lemma) {
        return {
          type: 'lemma',
          id: lemma.id,
          uk: lemma.uk,
          ipa: lemma.ipa,
          en: lemma.en,
          first_module: lemma.first_module,
          level: lemma.level,
          pos: lemma.pos,
          gender: lemma.gender,
        };
      }
    }
    return undefined;
  }

  /**
   * Get first module for any entry
   */
  getFirstModule(uk: string): number | undefined {
    const entry = this.getEntry(uk);
    return entry?.first_module;
  }

  /**
   * Check if entry is new in this module
   */
  isNewWord(uk: string, moduleNum: number): boolean {
    const firstModule = this.getFirstModule(uk);
    return firstModule === undefined || firstModule === moduleNum;
  }

  // ===========================================================================
  // Statistics
  // ===========================================================================

  getStats(): {
    totalLemmas: number;
    totalExpressions: number;
    byLevel: Record<string, { lemmas: number; expressions: number }>;
    byType: Record<string, number>;
    byPOS: Record<string, number>;
  } {
    const totalLemmas = (this.db.prepare(`SELECT COUNT(*) as count FROM lemmas`).get() as { count: number }).count;
    const totalExpressions = (this.db.prepare(`SELECT COUNT(*) as count FROM expressions`).get() as { count: number }).count;

    const lemmasByLevel = this.db.prepare(`
      SELECT level, COUNT(*) as count FROM lemmas GROUP BY level
    `).all() as { level: string; count: number }[];

    const exprsByLevel = this.db.prepare(`
      SELECT level, COUNT(*) as count FROM expressions GROUP BY level
    `).all() as { level: string; count: number }[];

    const byLevel: Record<string, { lemmas: number; expressions: number }> = {};
    for (const row of lemmasByLevel) {
      byLevel[row.level] = { lemmas: row.count, expressions: 0 };
    }
    for (const row of exprsByLevel) {
      if (!byLevel[row.level]) {
        byLevel[row.level] = { lemmas: 0, expressions: 0 };
      }
      byLevel[row.level].expressions = row.count;
    }

    const byType: Record<string, number> = {};
    const typeRows = this.db.prepare(`
      SELECT type, COUNT(*) as count FROM expressions GROUP BY type
    `).all() as { type: string; count: number }[];
    for (const row of typeRows) {
      byType[row.type] = row.count;
    }

    const byPOS: Record<string, number> = {};
    const posRows = this.db.prepare(`
      SELECT pos, COUNT(*) as count FROM lemmas GROUP BY pos
    `).all() as { pos: string; count: number }[];
    for (const row of posRows) {
      byPOS[row.pos] = row.count;
    }

    return {
      totalLemmas,
      totalExpressions,
      byLevel,
      byType,
      byPOS,
    };
  }

  // ===========================================================================
  // Cleanup
  // ===========================================================================

  close(): void {
    this.db.close();
  }
}

// =============================================================================
// Singleton Instance
// =============================================================================

let dbInstance: VocabDatabase | null = null;

export function getVocabDatabase(curriculumPath: string): VocabDatabase {
  if (!dbInstance) {
    dbInstance = new VocabDatabase(curriculumPath);
  }
  return dbInstance;
}

export function resetVocabDatabase(): void {
  if (dbInstance) {
    dbInstance.close();
    dbInstance = null;
  }
}
