#!/usr/bin/env npx ts-node
/**
 * Automated HTML/JSON output tests
 *
 * Checks:
 * - All modules generate valid JSON
 * - HTML has required structure
 * - B1+ modules have immersive sections
 * - B2 modules have quiz activities
 * - Vocabulary is present
 */

import { readFile, readdir } from 'fs/promises';
import { join } from 'path';
import { existsSync } from 'fs';

const OUTPUT_DIR = join(__dirname, '..', 'output');

interface TestResult {
  module: string;
  level: string;
  passed: boolean;
  errors: string[];
  warnings: string[];
}

async function testModule(jsonPath: string, htmlPath: string): Promise<TestResult> {
  const errors: string[] = [];
  const warnings: string[] = [];

  const moduleName = jsonPath.split('/').pop()?.replace('.json', '') || 'unknown';
  const level = jsonPath.includes('/c1/') ? 'C1' :
                jsonPath.includes('/b2+/') ? 'B2+' :
                jsonPath.includes('/b2/') ? 'B2' :
                jsonPath.includes('/b1+/') ? 'B1+' :
                jsonPath.includes('/b1/') ? 'B1' :
                jsonPath.includes('/a2+/') ? 'A2+' :
                jsonPath.includes('/a2/') ? 'A2' : 'A1';

  // Test 1: JSON is valid
  let json: any;
  try {
    const content = await readFile(jsonPath, 'utf-8');
    json = JSON.parse(content);
  } catch (e) {
    errors.push(`Invalid JSON: ${e}`);
    return { module: moduleName, level, passed: false, errors, warnings };
  }

  // Test 2: Required fields exist
  if (!json.lesson) errors.push('Missing lesson object');
  if (!json.vocabulary) errors.push('Missing vocabulary object');

  // Test 3: Lesson has title and level
  if (json.lesson) {
    if (!json.lesson.title) errors.push('Missing lesson.title');
    if (!json.lesson.targetLevel) errors.push('Missing lesson.targetLevel');
  }

  // Test 4: B1+ modules should have immersive sections
  if (['B1', 'B1+', 'B2', 'B2+', 'C1'].includes(level)) {
    const sections = json.lesson?.immersiveSections || [];
    if (sections.length === 0) {
      warnings.push('B1+ module has no immersive sections');
    } else if (sections.length < 3) {
      warnings.push(`Only ${sections.length} immersive sections (expected 3+)`);
    }

    // Check for intro and summary
    const hasIntro = sections.some((s: any) => s.type === 'intro');
    const hasSummary = sections.some((s: any) => s.type === 'summary');
    if (!hasIntro) warnings.push('Missing intro section');
    if (!hasSummary) warnings.push('Missing summary section');
  }

  // Test 5: Activities exist for B2+
  if (['B2', 'B2+', 'C1'].includes(level)) {
    const activities = json.activities || [];
    if (activities.length === 0) {
      warnings.push('B2+ module has no structured activities');
    }
  }

  // Test 6: Vocabulary exists
  const vocabWords = json.vocabulary?.words || [];
  if (vocabWords.length === 0) {
    warnings.push('No vocabulary words');
  }

  // Test 7: HTML exists and has content
  if (existsSync(htmlPath)) {
    try {
      const html = await readFile(htmlPath, 'utf-8');

      // Check for required HTML sections
      if (!html.includes('id="lesson"')) errors.push('HTML missing lesson section');
      if (!html.includes('id="vocab"')) errors.push('HTML missing vocab section');

      // Check for quiz data in B2+
      if (['B2', 'B2+', 'C1'].includes(level) && !html.includes('quizData') && !html.includes('quizData=')) {
        warnings.push('HTML has no quiz data');
      }

      // Check vocab data
      if (!html.includes('vocabData') && !html.includes('vocabData=')) {
        warnings.push('HTML has no vocab data');
      }

    } catch (e) {
      errors.push(`Cannot read HTML: ${e}`);
    }
  } else {
    errors.push('HTML file does not exist');
  }

  return {
    module: moduleName,
    level,
    passed: errors.length === 0,
    errors,
    warnings,
  };
}

async function main() {
  console.log('\n🧪 Running HTML/JSON Output Tests\n');

  const results: TestResult[] = [];
  const langPair = 'l2-uk-en';
  const levels = ['a1', 'a2', 'a2+', 'b1', 'b2'];

  for (const level of levels) {
    const jsonDir = join(OUTPUT_DIR, 'json', langPair, level);
    const htmlDir = join(OUTPUT_DIR, 'html', langPair, level);

    if (!existsSync(jsonDir)) continue;

    const files = await readdir(jsonDir);
    const jsonFiles = files.filter(f => f.endsWith('.json'));

    for (const jsonFile of jsonFiles) {
      const jsonPath = join(jsonDir, jsonFile);
      const htmlPath = join(htmlDir, jsonFile.replace('.json', '.html'));

      const result = await testModule(jsonPath, htmlPath);
      results.push(result);
    }
  }

  // Summary
  const passed = results.filter(r => r.passed).length;
  const failed = results.filter(r => !r.passed).length;
  const withWarnings = results.filter(r => r.warnings.length > 0).length;

  console.log(`📊 Results: ${passed} passed, ${failed} failed, ${withWarnings} with warnings\n`);

  // Show failures
  const failures = results.filter(r => !r.passed);
  if (failures.length > 0) {
    console.log('❌ FAILURES:');
    for (const f of failures) {
      console.log(`  ${f.module} (${f.level})`);
      for (const e of f.errors) {
        console.log(`    - ${e}`);
      }
    }
    console.log('');
  }

  // Show warnings (grouped by type)
  const warningCounts = new Map<string, number>();
  for (const r of results) {
    for (const w of r.warnings) {
      warningCounts.set(w, (warningCounts.get(w) || 0) + 1);
    }
  }

  if (warningCounts.size > 0) {
    console.log('⚠️  WARNINGS:');
    for (const [warning, count] of [...warningCounts.entries()].sort((a, b) => b[1] - a[1])) {
      console.log(`  ${count}x ${warning}`);
    }
    console.log('');
  }

  // Exit code
  process.exit(failed > 0 ? 1 : 0);
}

main().catch(console.error);
