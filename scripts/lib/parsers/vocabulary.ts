/**
 * Vocabulary parser
 *
 * Parses vocabulary tables from module markdown.
 *
 * Table format:
 * | Ukrainian | Transliteration | IPA | English | POS | Gender | Notes |
 * |-----------|-----------------|-----|---------|-----|--------|-------|
 * | слово     | slovo           | /ˈslɔwɔ/ | word | noun | n | - |
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
 */
export function parseVocabulary(body: string, moduleNum: number): {
  vocabulary: VocabWord[];
  restBody: string;
} {
  const vocabulary: VocabWord[] = [];

  // Find vocabulary section
  const vocabMatch = body.match(
    /# (?:Vocabulary|Словник)[^\n]*\n([\s\S]*?)(?=\n---|\n# (?:Letter Groups|Підсумок|Summary)|$)/
  );

  if (!vocabMatch) {
    return { vocabulary: [], restBody: body };
  }

  const vocabContent = vocabMatch[1];
  const restBody = body.replace(vocabMatch[0], '');

  // Find table in vocab content
  const tableMatch = vocabContent.match(/\|[^\n]+\|\n\|[-|\s]+\|\n([\s\S]*?)(?=\n\n|$)/);

  if (tableMatch) {
    const rows = tableMatch[1].trim().split('\n');

    for (let i = 0; i < rows.length; i++) {
      const row = rows[i];
      const cells = row.split('|').filter(c => c.trim());

      if (cells.length >= 4) {
        const word = parseVocabRow(cells, moduleNum, i);
        vocabulary.push(word);
      }
    }
  }

  return { vocabulary, restBody };
}

/**
 * Parse a single vocabulary row into VocabWord
 *
 * Supports two table formats:
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
  } else {
    // 6 columns: Word | IPA | English | POS | Gender | Note
    uk = cells[0]?.trim() || '';
    translit = undefined;
    ipa = cells[1]?.trim() || undefined;
    en = cells[2]?.trim() || '';
    pos = cells[3]?.trim() || 'noun';
    gender = parseGender(cells[4]?.trim());
    note = cells[5]?.trim() || undefined;
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

  // Find letter groups section
  const match = body.match(/# Letter Groups\n([\s\S]*?)$/);

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
  letterGroups?: LetterGroup[]
): VocabularySection {
  const section: VocabularySection = {
    moduleId: `mod-uk-${level}-${moduleNum}`,
    level,
    phase,
    wordCount: vocabulary.length,
    transliterationMode,
    words: vocabulary,
  };

  if (letterGroups && letterGroups.length > 0) {
    section.letterGroups = letterGroups;
  }

  return section;
}

// =============================================================================
// Exports
// =============================================================================

export { parseVocabulary as parse };
