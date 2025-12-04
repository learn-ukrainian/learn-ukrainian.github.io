/**
 * vocab-db.ts
 *
 * Vocabulary database module for tracking first appearances.
 * Used by the generator and vocabulary scripts.
 *
 * Features:
 * - Loads vocabulary.csv into memory
 * - Provides lookup for first appearance of lemmas
 * - Supports incremental updates when new modules are created
 */

import * as fs from 'fs';
import * as path from 'path';

// =============================================================================
// Types
// =============================================================================

export interface VocabDbEntry {
  lemma: string;
  ipa: string;
  english: string;
  pos: string;
  gender: string;
  module: number;
  level: string;
  note: string;
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

// Vocabulary targets from curriculum plans
export const VOCAB_TARGETS: Record<string, { cumulative: number; perModule: number }> = {
  'A1': { cumulative: 500, perModule: 17 },
  'A2': { cumulative: 820, perModule: 11 },
  'A2+': { cumulative: 1600, perModule: 40 },
  'B1': { cumulative: 2500, perModule: 25 },
  'B1+': { cumulative: 3500, perModule: 25 },
  'B2': { cumulative: 5000, perModule: 25 },
  'B2+': { cumulative: 6500, perModule: 25 },
  'C1': { cumulative: 9000, perModule: 30 },
};

/**
 * Get CEFR level from module number
 */
export function getLevelFromModule(moduleNum: number): string {
  for (const [level, [start, end]] of Object.entries(LEVEL_RANGES)) {
    if (moduleNum >= start && moduleNum <= end) {
      return level;
    }
  }
  return 'C1';
}

// =============================================================================
// Vocabulary Database Class
// =============================================================================

export class VocabDatabase {
  private entries: Map<string, VocabDbEntry> = new Map();
  private csvPath: string;

  constructor(curriculumPath: string) {
    this.csvPath = path.join(curriculumPath, 'vocabulary.csv');
    this.load();
  }

  /**
   * Load vocabulary.csv into memory
   */
  load(): void {
    this.entries.clear();

    if (!fs.existsSync(this.csvPath)) {
      console.log(`[VocabDB] No vocabulary.csv found at ${this.csvPath}`);
      return;
    }

    const content = fs.readFileSync(this.csvPath, 'utf-8');
    const lines = content.trim().split('\n');

    // Skip header
    for (let i = 1; i < lines.length; i++) {
      const entry = this.parseCsvLine(lines[i]);
      if (entry) {
        this.entries.set(entry.lemma.toLowerCase(), entry);
      }
    }

    console.log(`[VocabDB] Loaded ${this.entries.size} entries`);
  }

  /**
   * Parse a CSV line into VocabDbEntry
   */
  private parseCsvLine(line: string): VocabDbEntry | null {
    // Handle quoted fields
    const fields: string[] = [];
    let current = '';
    let inQuotes = false;

    for (let i = 0; i < line.length; i++) {
      const char = line[i];
      if (char === '"') {
        inQuotes = !inQuotes;
      } else if (char === ',' && !inQuotes) {
        fields.push(current);
        current = '';
      } else {
        current += char;
      }
    }
    fields.push(current);

    if (fields.length < 7) return null;

    return {
      lemma: fields[0] || '',
      ipa: fields[1] || '',
      english: fields[2] || '',
      pos: fields[3] || 'noun',
      gender: fields[4] || '-',
      module: parseInt(fields[5]) || 0,
      level: fields[6] || '',
      note: fields[7] || '',
    };
  }

  /**
   * Get the first appearance module for a lemma
   * Returns undefined if lemma is not in database
   */
  getFirstModule(lemma: string): number | undefined {
    const entry = this.entries.get(lemma.toLowerCase());
    return entry?.module;
  }

  /**
   * Check if a lemma is new in this module
   * Returns true if this is the first module where the lemma appears
   */
  isNewWord(lemma: string, moduleNum: number): boolean {
    const firstModule = this.getFirstModule(lemma);
    if (firstModule === undefined) {
      // Not in database - treat as new
      return true;
    }
    return firstModule === moduleNum;
  }

  /**
   * Get all entries
   */
  getAllEntries(): VocabDbEntry[] {
    return Array.from(this.entries.values());
  }

  /**
   * Get entry by lemma
   */
  getEntry(lemma: string): VocabDbEntry | undefined {
    return this.entries.get(lemma.toLowerCase());
  }

  /**
   * Add or update an entry (keeps earliest module number)
   */
  addEntry(entry: VocabDbEntry): boolean {
    const key = entry.lemma.toLowerCase();
    const existing = this.entries.get(key);

    if (!existing || entry.module < existing.module) {
      this.entries.set(key, entry);
      return true;
    }
    return false;
  }

  /**
   * Save entries back to CSV
   */
  save(): void {
    const entries = Array.from(this.entries.values())
      .sort((a, b) => a.module - b.module || a.lemma.localeCompare(b.lemma, 'uk'));

    const escape = (s: string): string => {
      if (s.includes(',') || s.includes('"') || s.includes('\n')) {
        return `"${s.replace(/"/g, '""')}"`;
      }
      return s;
    };

    const header = 'lemma,ipa,english,pos,gender,module,level,note,image_url';
    const rows = entries.map(e => [
      escape(e.lemma),
      escape(e.ipa),
      escape(e.english),
      escape(e.pos),
      escape(e.gender),
      e.module.toString(),
      escape(e.level),
      escape(e.note),
      '',
    ].join(','));

    const csv = [header, ...rows].join('\n') + '\n';
    fs.writeFileSync(this.csvPath, csv, 'utf-8');
    console.log(`[VocabDB] Saved ${entries.length} entries to ${this.csvPath}`);
  }

  /**
   * Get statistics
   */
  getStats(): {
    total: number;
    byLevel: Record<string, number>;
    byPOS: Record<string, number>;
  } {
    const byLevel: Record<string, number> = {};
    const byPOS: Record<string, number> = {};

    for (const entry of this.entries.values()) {
      byLevel[entry.level] = (byLevel[entry.level] || 0) + 1;
      byPOS[entry.pos] = (byPOS[entry.pos] || 0) + 1;
    }

    return {
      total: this.entries.size,
      byLevel,
      byPOS,
    };
  }
}

// =============================================================================
// Singleton Instance
// =============================================================================

let dbInstance: VocabDatabase | null = null;

/**
 * Get or create the vocabulary database instance
 */
export function getVocabDatabase(curriculumPath: string): VocabDatabase {
  if (!dbInstance) {
    dbInstance = new VocabDatabase(curriculumPath);
  }
  return dbInstance;
}

/**
 * Reset the singleton (for testing)
 */
export function resetVocabDatabase(): void {
  dbInstance = null;
}
