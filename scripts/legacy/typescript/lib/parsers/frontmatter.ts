/**
 * Frontmatter parser
 *
 * Parses YAML frontmatter from module markdown files.
 *
 * Note: 'module' and 'level' are now derived from file path, not frontmatter.
 * Files are stored in: curriculum/{langPair}/{level}/{num}-{slug}.md
 * Example: curriculum/l2-uk-en/a1/01-the-cyrillic-code-i.md
 *
 * Example frontmatter:
 * ---
 * title: The Cyrillic Code I
 * subtitle: Visual Recognition
 * phase: A1.1
 * duration: 45
 * transliteration: full
 * tags: [alphabet, reading, cyrillic]
 * objectives:
 *   - Recognize Cyrillic letters
 *   - Match letters to sounds
 * grammar:
 *   - Letter recognition
 * ---
 */

import { Frontmatter } from '../types';

// =============================================================================
// Parser
// =============================================================================

/**
 * Parse YAML frontmatter from markdown content
 * Returns the frontmatter object and the remaining body
 */
export function parseFrontmatter(content: string): {
  frontmatter: Frontmatter;
  body: string;
} {
  const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);

  if (!frontmatterMatch) {
    throw new Error('No frontmatter found in module');
  }

  const yamlContent = frontmatterMatch[1];
  const body = frontmatterMatch[2];

  const frontmatter = parseYaml(yamlContent);

  // Validate required fields
  validateFrontmatter(frontmatter);

  return { frontmatter: frontmatter as unknown as Frontmatter, body };
}

// =============================================================================
// YAML Parser (Simple Implementation)
// =============================================================================

/**
 * Simple YAML parser for frontmatter
 * Handles common cases without external dependencies
 */
function parseYaml(yaml: string): Record<string, unknown> {
  const result: Record<string, unknown> = {};
  const lines = yaml.split('\n');

  let currentKey: string | null = null;
  let currentArray: (string | number | boolean)[] = [];
  let inArray = false;

  for (const line of lines) {
    // Skip empty lines
    if (!line.trim()) continue;

    // Array item (starts with -)
    if (line.match(/^\s+-\s+/)) {
      const value = line.replace(/^\s+-\s+/, '').trim();
      if (inArray && currentKey) {
        currentArray.push(parseValue(value));
      }
      continue;
    }

    // If we were in an array, save it
    if (inArray && currentKey) {
      result[currentKey] = currentArray;
      currentArray = [];
      inArray = false;
    }

    // Key: value pair
    const kvMatch = line.match(/^(\w+):\s*(.*)$/);
    if (kvMatch) {
      const key = kvMatch[1];
      const value = kvMatch[2].trim();

      if (!value) {
        // No value means array follows
        currentKey = key;
        inArray = true;
        currentArray = [];
      } else if (value.startsWith('[') && value.endsWith(']')) {
        // Inline array: [item1, item2]
        result[key] = parseInlineArray(value);
      } else {
        // Simple value
        result[key] = parseValue(value);
      }
    }
  }

  // Don't forget last array if exists
  if (inArray && currentKey) {
    result[currentKey] = currentArray;
  }

  return result;
}

/**
 * Parse inline array: [item1, item2, item3]
 */
function parseInlineArray(str: string): string[] {
  const content = str.slice(1, -1); // Remove [ and ]
  return content.split(',').map(s => parseValue(s.trim()) as string);
}

/**
 * Parse a single YAML value
 */
function parseValue(value: string): string | number | boolean {
  // Remove quotes
  if ((value.startsWith('"') && value.endsWith('"')) ||
    (value.startsWith("'") && value.endsWith("'"))) {
    return value.slice(1, -1);
  }

  // Boolean
  if (value === 'true') return true;
  if (value === 'false') return false;

  // Number
  const num = Number(value);
  if (!isNaN(num) && value !== '') return num;

  return value;
}

// =============================================================================
// Validation
// =============================================================================

/**
 * Validate frontmatter has required fields
 *
 * Note: 'module' and 'level' are now derived from file path, not frontmatter.
 * They're kept as optional for backwards compatibility.
 */
function validateFrontmatter(fm: Record<string, unknown>): void {
  // module and level are now derived from path, not required in frontmatter
  const required = ['title', 'phase', 'duration', 'transliteration', 'tags', 'objectives', 'pedagogy'];

  for (const field of required) {
    if (!(field in fm)) {
      throw new Error(`Missing required frontmatter field: ${field}`);
    }
  }

  // Set defaults for module and level (will be overwritten by generator from path)
  if (!('module' in fm)) {
    fm.module = 0;  // Placeholder, overwritten by generator
  }
  if (!('level' in fm)) {
    fm.level = 'A1';  // Placeholder, overwritten by generator
  }

  // Validate level if present
  const validLevels = ['A1', 'A2', 'A2+', 'B1', 'B1+', 'B2', 'B2+', 'C1'];
  if (fm.level && !validLevels.includes(fm.level as string)) {
    throw new Error(`Invalid level: ${fm.level}. Must be one of: ${validLevels.join(', ')}`);
  }

  // Validate transliteration
  const validTranslit = ['full', 'partial', 'first-occurrence', 'none'];
  if (!validTranslit.includes(fm.transliteration as string)) {
    throw new Error(`Invalid transliteration: ${fm.transliteration}. Must be one of: ${validTranslit.join(', ')}`);
  }
}

// =============================================================================
// Exports
// =============================================================================

export { parseFrontmatter as parse };
