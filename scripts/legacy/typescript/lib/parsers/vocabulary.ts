/**
 * Vocabulary parser
 *
 * Parses vocabulary tables from module markdown.
 *
 * Supported table formats:
 *
 * 3 columns (B2+): Слово | Переклад | Примітки
 * 4 columns (B2):  Слово | Вимова | Переклад | Приклад
 * 5 columns (B1):  Word | IPA | English | POS | Note
 * 6 columns:       Word | IPA | English | POS | Gender | Note
 * 7 columns (A1):  Word | Translit | IPA | English | POS | Gender | Note
 *
 * Also handles letter groups for alphabet modules:
 * # Letter Groups
 * **True Friends:** а б в
 * **False Friends:** г р с
 * **New Letters:** ж ш щ
 */

import { VocabWord, VocabularySection, LetterGroup } from '../types';

// =============================================================================
// Vocabulary Parser
// =============================================================================

/**
 * Parse vocabulary section from markdown body
 * Handles both # Vocabulary (new words) and # Review Vocabulary sections
 */
export function parseVocabulary(body: string, moduleNum: number): {
  vocabulary: VocabWord[];
  reviewVocabulary: VocabWord[];
  restBody: string;
} {
  const vocabulary: VocabWord[] = [];
  const reviewVocabulary: VocabWord[] = [];
  let restBody = body;

  // Find main vocabulary section (new words)
  const vocabMatch = body.match(
    /# (?:Vocabulary|Словник)[^\n]*\n([\s\S]*?)(?=\n---|\n# (?:Letter Groups|Підсумок|Summary|Review Vocabulary|Activities|Вправи)|$)/
  );

  if (vocabMatch) {
    const vocabContent = vocabMatch[1];
    restBody = restBody.replace(vocabMatch[0], '');

    // Find table in vocab content - capture header row too
    const tableMatch = vocabContent.match(/(\|[^\n]+\|)\n\|[-|\s]+\|\n([\s\S]*?)(?=\n\n|$)/);

    if (tableMatch) {
      // Parse header to get expected column count
      const headerRow = tableMatch[1];
      const headerCells = headerRow.split('|').slice(1, -1).map(c => c.trim());
      const expectedCols = headerCells.length;

      const rows = tableMatch[2].trim().split('\n');

      for (let i = 0; i < rows.length; i++) {
        const row = rows[i];
        // Split by |, remove first/last empty strings from split
        const rawCells = row.split('|');
        const cells = rawCells.slice(1, -1).map(c => c.trim());

        // Pad cells to match header column count (for rows with missing trailing columns)
        while (cells.length < expectedCols) {
          cells.push('');
        }

        // Need at least 2 columns (word + translation)
        if (cells.length >= 2 && cells[0]) {
          const word = parseVocabRow(cells, moduleNum, i);
          word.isNew = true;
          word.firstModule = moduleNum;
          vocabulary.push(word);
        }
      }
    }
  }

  // Find review vocabulary section (words from earlier modules)
  const reviewMatch = restBody.match(
    /# Review Vocabulary\n([\s\S]*?)(?=\n---|\n# (?:Letter Groups|Підсумок|Summary|Вправи|Activities)|$)/
  );

  if (reviewMatch) {
    const reviewContent = reviewMatch[1];
    restBody = restBody.replace(reviewMatch[0], '');

    // Find table in review content
    // Review table format: | Word | First Module |
    const tableMatch = reviewContent.match(/\|[^\n]+\|\n\|[-|\s]+\|\n([\s\S]*?)(?=\n\n|$)/);

    if (tableMatch) {
      const rows = tableMatch[1].trim().split('\n');

      for (let i = 0; i < rows.length; i++) {
        const row = rows[i];
        // Split by |, remove first/last empty strings from split, but keep empty columns
        const rawCells = row.split('|');
        const cells = rawCells.slice(1, -1).map(c => c.trim());

        // Review table: Word | First Module
        if (cells.length >= 2 && cells[0]) {
          const uk = cells[0] || '';
          const firstModuleStr = cells[1] || '';
          const firstModule = parseInt(firstModuleStr) || 0;

          const word: VocabWord = {
            id: generateVocabId(uk, moduleNum, i + 1000), // Offset ID to avoid collision
            uk,
            en: '', // Not stored in review table
            pos: 'noun',
            isNew: false,
            firstModule,
          };

          reviewVocabulary.push(word);
        }
      }
    }
  }

  return { vocabulary, reviewVocabulary, restBody };
}

/**
 * Parse a single vocabulary row into VocabWord
 *
 * Supports multiple table formats:
 * - 3 columns: Word | Translation | Notes (B2+ simplified)
 * - 4 columns: Word | IPA | Translation | Example (B2 with pronunciation)
 * - 5 columns: Word | IPA | English | POS | Note (B1)
 * - 6 columns: Word | IPA | English | POS | Gender | Note
 * - 7 columns: Word | Translit | IPA | English | POS | Gender | Note
 */
function parseVocabRow(cells: string[], moduleNum: number, index: number): VocabWord {
  let uk: string, translit: string | undefined, ipa: string | undefined;
  let en: string, pos: string, gender: 'f' | 'm' | 'n' | undefined, note: string | undefined;

  if (cells.length >= 7) {
    // 7 columns: Word | Translit | IPA | English | POS | Gender | Note
    uk = cells[0]?.trim() || '';
    translit = cells[1]?.trim() || undefined;
    ipa = cells[2]?.trim() || undefined;
    en = cells[3]?.trim() || '';
    pos = cells[4]?.trim() || 'noun';
    gender = parseGender(cells[5]?.trim());
    note = cells[6]?.trim() || undefined;
  } else if (cells.length === 6) {
    // 6 columns: Word | IPA | English | POS | Gender | Note
    uk = cells[0]?.trim() || '';
    translit = undefined;
    ipa = cells[1]?.trim() || undefined;
    en = cells[2]?.trim() || '';
    pos = cells[3]?.trim() || 'noun';
    gender = parseGender(cells[4]?.trim());
    note = cells[5]?.trim() || undefined;
  } else if (cells.length === 5) {
    // 5 columns: Word | IPA | English | POS | Note
    uk = cells[0]?.trim() || '';
    translit = undefined;
    ipa = cells[1]?.trim() || undefined;
    en = cells[2]?.trim() || '';
    pos = cells[3]?.trim() || 'noun';
    gender = undefined;
    note = cells[4]?.trim() || undefined;
  } else if (cells.length === 4) {
    // 4 columns: Word | IPA | Translation | Example
    // IPA starts with /
    uk = cells[0]?.trim() || '';
    translit = undefined;
    ipa = cells[1]?.trim() || undefined;
    en = cells[2]?.trim() || '';
    pos = 'noun'; // Not specified in this format
    gender = undefined;
    note = cells[3]?.trim() || undefined; // Example as note
  } else if (cells.length === 3) {
    // 3 columns: Word | Translation | Notes (simplified B2+ format)
    uk = cells[0]?.trim() || '';
    translit = undefined;
    ipa = undefined;
    en = cells[1]?.trim() || '';
    pos = 'noun'; // Not specified in this format
    gender = undefined;
    note = cells[2]?.trim() || undefined;
  } else {
    // 2 columns: Word | Translation (minimum)
    uk = cells[0]?.trim() || '';
    translit = undefined;
    ipa = undefined;
    en = cells[1]?.trim() || '';
    pos = 'noun';
    gender = undefined;
    note = undefined;
  }

  // Generate ID from Ukrainian word
  const id = generateVocabId(uk, moduleNum, index);

  const word: VocabWord = {
    id,
    uk,
    en,
    pos,
  };

  if (translit && translit !== '-') word.translit = translit;
  if (ipa && ipa !== '-') word.ipa = ipa;
  if (gender) word.gender = gender;
  if (note && note !== '-') word.note = note;

  return word;
}

/**
 * Parse gender from string
 */
function parseGender(str: string | undefined): 'f' | 'm' | 'n' | undefined {
  if (!str || str === '-') return undefined;
  const g = str.toLowerCase().charAt(0);
  if (g === 'f' || g === 'm' || g === 'n') return g;
  return undefined;
}

/**
 * Generate vocabulary item ID
 */
function generateVocabId(uk: string, moduleNum: number, index: number): string {
  // Transliterate to ASCII for ID
  const slug = transliterateToAscii(uk).toLowerCase().replace(/\s+/g, '-');
  return `v-${slug}-${moduleNum}-${index}`;
}

/**
 * Simple transliteration for ID generation
 */
function transliterateToAscii(uk: string): string {
  const map: Record<string, string> = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'h', 'ґ': 'g',
    'д': 'd', 'е': 'e', 'є': 'ye', 'ж': 'zh', 'з': 'z',
    'и': 'y', 'і': 'i', 'ї': 'yi', 'й': 'y', 'к': 'k',
    'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p',
    'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f',
    'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
    'ь': '', 'ю': 'yu', 'я': 'ya', "'": '',
  };

  return uk
    .toLowerCase()
    .split('')
    .map(c => map[c] || c)
    .join('');
}

// =============================================================================
// Letter Groups Parser
// =============================================================================

/**
 * Parse letter groups section (for alphabet modules)
 */
export function parseLetterGroups(body: string): {
  letterGroups: LetterGroup[];
  restBody: string;
} {
  const groups: LetterGroup[] = [];

  // Find letter groups section - stop at next # header or end of file
  const match = body.match(/# Letter Groups\n([\s\S]*?)(?=\n# |\n---\s*$|$)/);

  if (!match) {
    return { letterGroups: [], restBody: body };
  }

  const content = match[1];
  const restBody = body.replace(match[0], '');

  // Parse **Group Name:** letters format
  const groupPatterns = [
    { name: 'True Friends', pattern: /\*\*True Friends[^:]*:\*\*\s*(.+)/i },
    { name: 'False Friends', pattern: /\*\*False Friends[^:]*:\*\*\s*(.+)/i },
    { name: 'New Letters', pattern: /\*\*New Letters[^:]*:\*\*\s*(.+)/i },
  ];

  for (const { name, pattern } of groupPatterns) {
    const groupMatch = content.match(pattern);
    if (groupMatch) {
      const letters = groupMatch[1].trim().split(/\s+/).filter(Boolean);
      groups.push({ name, letters });
    }
  }

  return { letterGroups: groups, restBody };
}

// =============================================================================
// Build Vocabulary Section
// =============================================================================

/**
 * Build VocabularySection object for JSON output
 */
export function buildVocabularySection(
  vocabulary: VocabWord[],
  moduleNum: number,
  level: string,
  phase: string,
  transliterationMode: string,
  letterGroups?: LetterGroup[],
  reviewVocabulary?: VocabWord[]
): VocabularySection {
  const newWordCount = vocabulary.length;
  const reviewWordCount = reviewVocabulary?.length || 0;

  const section: VocabularySection = {
    moduleId: `mod-uk-${level}-${moduleNum}`,
    level,
    phase,
    wordCount: newWordCount + reviewWordCount, // Total words in module
    newWordCount,
    reviewWordCount,
    transliterationMode,
    words: vocabulary,
  };

  if (reviewVocabulary && reviewVocabulary.length > 0) {
    section.reviewWords = reviewVocabulary;
  }

  if (letterGroups && letterGroups.length > 0) {
    section.letterGroups = letterGroups;
  }

  return section;
}

// =============================================================================
// Exports
// =============================================================================

export { parseVocabulary as parse };
