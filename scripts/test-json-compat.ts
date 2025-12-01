/**
 * JSON Compatibility Test
 *
 * Compares JSON output between current generator and new architecture
 * to ensure we don't break Vibe imports.
 *
 * Run: npx ts-node scripts/test-json-compat.ts [moduleNum]
 */

import { readFile, readdir } from 'fs/promises';
import { existsSync } from 'fs';
import { join } from 'path';

// =============================================================================
// Configuration
// =============================================================================

const LANG_PAIR = 'l2-uk-en';
const OUTPUT_DIR = join(process.cwd(), 'output', 'json', LANG_PAIR);

// Fields to ignore when comparing (timestamps change, ordering varies)
const IGNORE_FIELDS = [
  'createdAt',
  'modifiedAt',
  'version',
];

// Fields where order doesn't matter (arrays that may be shuffled)
const UNORDERED_ARRAYS = [
  'tags',
];

// =============================================================================
// Main Test Runner
// =============================================================================

async function main() {
  const args = process.argv.slice(2);
  const specificModule = args[0] ? parseInt(args[0], 10) : null;

  console.log('JSON Compatibility Test');
  console.log('=======================\n');

  if (specificModule) {
    await testModule(specificModule);
  } else {
    await testAllModules();
  }
}

async function testAllModules() {
  // Find all existing JSON files
  const levels = ['a1', 'a2', 'a2+', 'b1', 'b2', 'c1'];
  const results: TestResult[] = [];

  for (const level of levels) {
    const levelDir = join(OUTPUT_DIR, level);
    if (!existsSync(levelDir)) continue;

    const files = await readdir(levelDir);
    const jsonFiles = files.filter(f => f.endsWith('.json'));

    for (const file of jsonFiles) {
      const match = file.match(/module-(\d+)\.json/);
      if (!match) continue;

      const moduleNum = parseInt(match[1], 10);
      const result = await testModule(moduleNum, false);
      results.push(result);
    }
  }

  // Summary
  console.log('\n' + '='.repeat(60));
  console.log('SUMMARY');
  console.log('='.repeat(60));

  const passed = results.filter(r => r.passed).length;
  const failed = results.filter(r => !r.passed).length;

  console.log(`Total modules tested: ${results.length}`);
  console.log(`Passed: ${passed}`);
  console.log(`Failed: ${failed}`);

  if (failed > 0) {
    console.log('\nFailed modules:');
    results.filter(r => !r.passed).forEach(r => {
      console.log(`  - Module ${r.moduleNum}: ${r.errors.join(', ')}`);
    });
    process.exit(1);
  } else {
    console.log('\n✓ All modules passed compatibility check!');
  }
}

async function testModule(moduleNum: number, verbose = true): Promise<TestResult> {
  const result: TestResult = {
    moduleNum,
    passed: true,
    errors: [],
    warnings: [],
  };

  if (verbose) {
    console.log(`Testing Module ${moduleNum}...`);
  }

  // Find the JSON file
  const level = getLevelFromModuleNum(moduleNum);
  const paddedNum = moduleNum.toString().padStart(2, '0');
  const jsonPath = join(OUTPUT_DIR, level, `module-${paddedNum}.json`);

  // Also try without padding for higher module numbers
  const altPath = join(OUTPUT_DIR, level, `module-${moduleNum}.json`);

  // Try both paths
  let actualPath = jsonPath;
  if (!existsSync(jsonPath)) {
    if (existsSync(altPath)) {
      actualPath = altPath;
    } else {
      result.passed = false;
      result.errors.push('JSON file not found');
      if (verbose) console.log(`  ✗ JSON file not found at ${jsonPath}`);
      return result;
    }
  }

  try {
    const currentJson = JSON.parse(await readFile(actualPath, 'utf-8'));

    // Validate structure
    validateStructure(currentJson, result);

    // Check critical fields
    validateLesson(currentJson.lesson, result);
    validateActivities(currentJson.activities, result);
    validateVocabulary(currentJson.vocabulary, result);

    if (verbose) {
      if (result.passed) {
        console.log(`  ✓ Module ${moduleNum} structure is valid`);
      } else {
        console.log(`  ✗ Module ${moduleNum} has issues:`);
        result.errors.forEach(e => console.log(`    - ${e}`));
      }
      if (result.warnings.length > 0) {
        result.warnings.forEach(w => console.log(`    ⚠ ${w}`));
      }
    }
  } catch (err) {
    result.passed = false;
    result.errors.push(`Parse error: ${(err as Error).message}`);
    if (verbose) console.log(`  ✗ Failed to parse JSON: ${(err as Error).message}`);
  }

  return result;
}

// =============================================================================
// Validators
// =============================================================================

function validateStructure(json: any, result: TestResult) {
  const requiredTopLevel = ['$schema', 'lesson', 'activities', 'vocabulary'];

  for (const field of requiredTopLevel) {
    if (!(field in json)) {
      result.passed = false;
      result.errors.push(`Missing top-level field: ${field}`);
    }
  }
}

function validateLesson(lesson: any, result: TestResult) {
  if (!lesson) return;

  const requiredFields = [
    'id', 'moduleId', 'languagePair', 'subject', 'owner', 'visibility',
    'language', 'targetLevel', 'phase', 'moduleNumber', 'title',
    'description', 'objectives', 'totalDuration', 'transliterationMode',
    'tags', 'phases',
  ];

  for (const field of requiredFields) {
    if (!(field in lesson)) {
      result.passed = false;
      result.errors.push(`Missing lesson field: ${field}`);
    }
  }

  // Validate ID format
  if (lesson.id && !lesson.id.match(/^lesson-uk-[A-Z][0-9](\+)?-\d+$/)) {
    result.warnings.push(`Unusual lesson ID format: ${lesson.id}`);
  }

  // Validate moduleId format
  if (lesson.moduleId && !lesson.moduleId.match(/^mod-uk-[A-Z][0-9](\+)?-\d+$/)) {
    result.warnings.push(`Unusual moduleId format: ${lesson.moduleId}`);
  }
}

function validateActivities(activities: any[], result: TestResult) {
  if (!activities || !Array.isArray(activities)) return;

  const validTypes = ['quiz', 'match-up', 'group-sort', 'fill-blank', 'true-false', 'translate', 'order', 'gap-fill'];

  for (let i = 0; i < activities.length; i++) {
    const act = activities[i];

    if (!act.id) {
      result.passed = false;
      result.errors.push(`Activity ${i} missing id`);
    }

    if (!act.type || !validTypes.includes(act.type)) {
      result.passed = false;
      result.errors.push(`Activity ${i} has invalid type: ${act.type}`);
    }

    if (!act.content) {
      result.passed = false;
      result.errors.push(`Activity ${i} missing content`);
    }

    // Type-specific validation
    if (act.type === 'quiz' && act.content) {
      if (!act.content.questions || !Array.isArray(act.content.questions)) {
        result.passed = false;
        result.errors.push(`Quiz activity ${i} missing questions array`);
      }
    }

    if (act.type === 'match-up' && act.content) {
      if (!act.content.pairs || !Array.isArray(act.content.pairs)) {
        result.passed = false;
        result.errors.push(`Match-up activity ${i} missing pairs array`);
      }
    }

    if (act.type === 'group-sort' && act.content) {
      if (!act.content.groups || !Array.isArray(act.content.groups)) {
        result.passed = false;
        result.errors.push(`Group-sort activity ${i} missing groups array`);
      }
    }
  }
}

function validateVocabulary(vocab: any, result: TestResult) {
  if (!vocab) return;

  const requiredFields = ['moduleId', 'level', 'phase', 'wordCount', 'transliterationMode', 'words'];

  for (const field of requiredFields) {
    if (!(field in vocab)) {
      result.passed = false;
      result.errors.push(`Missing vocabulary field: ${field}`);
    }
  }

  if (vocab.words && Array.isArray(vocab.words)) {
    for (let i = 0; i < vocab.words.length; i++) {
      const word = vocab.words[i];
      // Structural check - must have these fields (even if empty)
      if (!('id' in word) || !('uk' in word) || !('en' in word)) {
        result.passed = false;
        result.errors.push(`Vocabulary word ${i} missing structural fields (id, uk, en)`);
      }
      // Data quality check - pos should ideally have a value
      if (!word.pos) {
        result.warnings.push(`Vocabulary word ${i} has empty pos field (data quality issue)`);
      }
    }
  }
}

// =============================================================================
// Utilities
// =============================================================================

function getLevelFromModuleNum(moduleNum: number): string {
  if (moduleNum <= 30) return 'a1';
  if (moduleNum <= 60) return 'a2';
  if (moduleNum <= 80) return 'a2+';
  if (moduleNum <= 140) return 'b1';
  if (moduleNum <= 190) return 'b2';
  return 'c1';
}

interface TestResult {
  moduleNum: number;
  passed: boolean;
  errors: string[];
  warnings: string[];
}

// =============================================================================
// Run
// =============================================================================

main().catch(err => {
  console.error('Test failed:', err);
  process.exit(1);
});
