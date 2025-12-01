/**
 * Comprehensive Migration Script
 *
 * Converts ALL existing markdown patterns to the universal format.
 * See docs/MARKDOWN-FORMAT.md for specification.
 */

import * as fs from 'fs';
import * as path from 'path';

const MODULES_DIR = path.join(__dirname, '../curriculum/l2-uk-en/modules');

interface MigrationResult {
  file: string;
  changes: string[];
  warnings: string[];
}

/**
 * Check if a line is inside a table (contains |)
 */
function isTableLine(line: string): boolean {
  return line.includes('|') && (line.trim().startsWith('|') || line.includes(' | '));
}

/**
 * Check if a line is a section header
 */
function isHeaderLine(line: string): boolean {
  return /^#{1,6}\s/.test(line.trim());
}

/**
 * Check if arrow is used for transformation (should stay visible)
 */
function isTransformationArrow(line: string, prevLine: string, nextLine: string): boolean {
  // Tables always show transformations
  if (isTableLine(line)) return true;

  // Headers always visible
  if (isHeaderLine(line)) return true;

  // Inline examples in regular text (not indented, not starting with number/bullet for exercise)
  // Pattern: "word → word" as part of explanation
  if (!line.match(/^\s*[\d\-\*]\.*\s/) && !line.match(/^\s*>/)) {
    // Check if it looks like an example, not an exercise answer
    // Examples usually have context around the arrow, not just "→ answer"
    const arrowMatch = line.match(/(.+)→(.+)/);
    if (arrowMatch) {
      const before = arrowMatch[1].trim();
      const after = arrowMatch[2].trim();
      // If there's substantial content before the arrow, it's likely an example
      if (before.length > 3 && !before.match(/^[\d]+\.\s*$/) && !before.includes('___')) {
        return true;
      }
    }
  }

  return false;
}

/**
 * Migrate a single file
 */
function migrateFile(filePath: string, dryRun: boolean): MigrationResult {
  const fileName = path.basename(filePath);
  const result: MigrationResult = {
    file: fileName,
    changes: [],
    warnings: [],
  };

  let content = fs.readFileSync(filePath, 'utf-8');
  const lines = content.split('\n');
  const newLines: string[] = [];

  for (let i = 0; i < lines.length; i++) {
    let line = lines[i];
    const prevLine = i > 0 ? lines[i - 1] : '';
    const nextLine = i < lines.length - 1 ? lines[i + 1] : '';

    // Skip if already migrated
    if (line.includes('> [!answer]') || line.includes('> [!explanation]') || line.includes('> [!alt]')) {
      newLines.push(line);
      continue;
    }

    // Skip tables and headers - transformations stay visible
    if (isTableLine(line) || isHeaderLine(line)) {
      newLines.push(line);
      continue;
    }

    let modified = false;

    // Pattern 1: Indented arrow answer (most common)
    // "   → **answer**" or "   → answer"
    const indentedArrowMatch = line.match(/^(\s+)→\s*(.+)$/);
    if (indentedArrowMatch && !isTransformationArrow(line, prevLine, nextLine)) {
      const [, indent, answer] = indentedArrowMatch;

      // Check for explanation in parentheses
      const explanationMatch = answer.match(/^(.+?)\s*\(([^)]+)\)\s*$/);
      if (explanationMatch) {
        newLines.push(`${indent}> [!answer] ${explanationMatch[1].trim()}`);
        newLines.push(`${indent}> [!explanation] ${explanationMatch[2].trim()}`);
        result.changes.push(`Line ${i + 1}: Split arrow+explanation`);
      } else {
        newLines.push(`${indent}> [!answer] ${answer.trim()}`);
        result.changes.push(`Line ${i + 1}: Indented arrow → callout`);
      }
      modified = true;
    }

    // Pattern 2: List item arrow answer
    // "   - → **answer**"
    const listArrowMatch = line.match(/^(\s*)[-*]\s*→\s*(.+)$/);
    if (!modified && listArrowMatch) {
      const [, indent, answer] = listArrowMatch;
      newLines.push(`${indent}> [!answer] ${answer.trim()}`);
      result.changes.push(`Line ${i + 1}: List arrow → callout`);
      modified = true;
    }

    // Pattern 3: True/False with emoji
    // "→ ✅ **Правда.** explanation" or "→ ❌ **Міф.** explanation"
    const trueFalseMatch = line.match(/^(\s*)→\s*(✅|❌)\s*\*\*(Правда|Міф)\.?\*\*\.?\s*(.*)$/);
    if (!modified && trueFalseMatch) {
      const [, indent, emoji, verdict, explanation] = trueFalseMatch;
      newLines.push(`${indent}> [!answer] ${verdict}`);
      if (explanation.trim()) {
        newLines.push(`${indent}> [!explanation] ${explanation.trim()}`);
      }
      result.changes.push(`Line ${i + 1}: True/false → callout`);
      modified = true;
    }

    // Pattern 4: Blockquote with arrow - ALMOST ALWAYS explanatory content
    // Blockquotes with → are used to explain grammar rules and transformations
    // They should stay visible. Only very specific patterns are answers.
    const blockquoteArrowMatch = line.match(/^(\s*)>\s*(.+?)\s*→\s*(.+)$/);
    if (!modified && blockquoteArrowMatch) {
      // Keep blockquote arrows as-is - they're explanatory content
      newLines.push(line);
      modified = true;
    }

    // Pattern 5: Numbered exercise with inline arrow answer
    // "1. Question → answer" or "1. Question ___ → answer"
    const numberedInlineMatch = line.match(/^(\s*)(\d+)\.\s*(.+?)\s*→\s*(.+)$/);
    if (!modified && numberedInlineMatch) {
      const [, indent, num, question, answer] = numberedInlineMatch;
      // Check if question part has blanks or looks like exercise
      if (question.includes('___') || question.includes('_') || question.length < 80) {
        newLines.push(`${indent}${num}. ${question.trim()}`);
        newLines.push(`${indent}   > [!answer] ${answer.trim()}`);
        result.changes.push(`Line ${i + 1}: Split numbered inline answer`);
        modified = true;
      }
    }

    // Pattern 6: Standalone arrow at line start (after exercise)
    // "→ answer" at start of line (with possible leading whitespace)
    const standaloneArrowMatch = line.match(/^(\s*)→\s+([^→].+)$/);
    if (!modified && standaloneArrowMatch && !isTransformationArrow(line, prevLine, nextLine)) {
      const [, indent, answer] = standaloneArrowMatch;
      // Check if previous line looks like a question
      if (prevLine.match(/\?|\___|\d+\./) || prevLine.trim().length > 0) {
        const explanationMatch = answer.match(/^(.+?)\s*\(([^)]+)\)\s*$/);
        if (explanationMatch) {
          newLines.push(`${indent}> [!answer] ${explanationMatch[1].trim()}`);
          newLines.push(`${indent}> [!explanation] ${explanationMatch[2].trim()}`);
          result.changes.push(`Line ${i + 1}: Standalone arrow+explanation`);
        } else {
          newLines.push(`${indent}> [!answer] ${answer.trim()}`);
          result.changes.push(`Line ${i + 1}: Standalone arrow → callout`);
        }
        modified = true;
      }
    }

    if (!modified) {
      newLines.push(line);
    }
  }

  const newContent = newLines.join('\n');

  if (newContent !== content && !dryRun) {
    fs.writeFileSync(filePath, newContent);
  }

  return result;
}

/**
 * Run validation on migrated file
 */
function validateFile(filePath: string): string[] {
  const content = fs.readFileSync(filePath, 'utf-8');
  const lines = content.split('\n');
  const errors: string[] = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Check for remaining arrow answers (not in tables/headers)
    if (line.includes('→') && !isTableLine(line) && !isHeaderLine(line)) {
      // Check if it looks like an answer pattern that wasn't migrated
      if (line.match(/^\s+→\s*\*\*/) || line.match(/^\s*[-*]\s*→/)) {
        errors.push(`Line ${i + 1}: Unmigrated arrow answer: "${line.trim()}"`);
      }
    }
  }

  return errors;
}

/**
 * Main migration function
 */
function migrate(dryRun: boolean = false): void {
  console.log(`\n${'='.repeat(60)}`);
  console.log(dryRun ? '🔍 DRY RUN: Analyzing migration' : '🔄 MIGRATING to universal format');
  console.log(`${'='.repeat(60)}\n`);

  const files = fs.readdirSync(MODULES_DIR)
    .filter(f => f.endsWith('.md'))
    .sort((a, b) => {
      const numA = parseInt(a.match(/\d+/)?.[0] || '0');
      const numB = parseInt(b.match(/\d+/)?.[0] || '0');
      return numA - numB;
    });

  let totalChanges = 0;
  let totalWarnings = 0;
  const allWarnings: string[] = [];

  for (const file of files) {
    const filePath = path.join(MODULES_DIR, file);
    const result = migrateFile(filePath, dryRun);

    if (result.changes.length > 0 || result.warnings.length > 0) {
      console.log(`\n📄 ${file}:`);

      if (result.changes.length > 0) {
        console.log(`   ✓ ${result.changes.length} changes`);
        totalChanges += result.changes.length;
      }

      if (result.warnings.length > 0) {
        result.warnings.forEach(w => {
          console.log(`   ⚠️  ${w}`);
          allWarnings.push(`${file}: ${w}`);
        });
        totalWarnings += result.warnings.length;
      }
    }

    // Run validation
    if (!dryRun) {
      const errors = validateFile(filePath);
      if (errors.length > 0) {
        console.log(`   ❌ Validation errors:`);
        errors.forEach(e => console.log(`      ${e}`));
      }
    }
  }

  console.log(`\n${'='.repeat(60)}`);
  console.log('SUMMARY');
  console.log(`${'='.repeat(60)}`);
  console.log(`Total files: ${files.length}`);
  console.log(`Total changes: ${totalChanges}`);
  console.log(`Total warnings: ${totalWarnings}`);

  if (allWarnings.length > 0) {
    console.log(`\n⚠️  Items needing manual review:`);
    allWarnings.forEach(w => console.log(`   - ${w}`));
  }

  console.log(`${'='.repeat(60)}\n`);
}

// Parse arguments
const args = process.argv.slice(2);
const dryRun = args.includes('--dry-run') || args.includes('-n');

migrate(dryRun);
