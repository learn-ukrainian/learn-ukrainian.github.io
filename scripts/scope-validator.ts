#!/usr/bin/env npx ts-node
/**
 * Scope Validator Script
 *
 * Validates module content against curriculum plan definitions.
 * Detects out-of-scope grammar, vocabulary, and transliteration violations.
 *
 * Usage:
 *   npx ts-node scripts/scope-validator.ts [lang] [module-range]
 *
 * Examples:
 *   npx ts-node scripts/scope-validator.ts l2-uk-en           # Validate all modules
 *   npx ts-node scripts/scope-validator.ts l2-uk-en 1-30      # Validate A1 only
 *   npx ts-node scripts/scope-validator.ts l2-uk-en 5         # Validate single module
 */

import * as fs from 'fs';
import * as path from 'path';

// =============================================================================
// Types
// =============================================================================

interface ScopeViolation {
  type: 'error' | 'warning' | 'info';
  category: 'grammar' | 'vocabulary' | 'transliteration' | 'scope' | 'verb-class';
  message: string;
  line?: number;
  context?: string;
}

interface ValidationResult {
  moduleNum: number;
  title: string;
  level: string;
  violations: ScopeViolation[];
}

// =============================================================================
// Transliteration Detection
// =============================================================================

// Pattern: Ukrainian word followed by (latin transliteration)
// Examples: читати (chytaty), знати (znaty), Я (ya)
// This catches real transliteration like "читати (chytaty)" but NOT "(book)" or "(masculine)"
const TRANSLITERATION_PATTERN = /[а-яіїєґ']+\s*\(([a-z']+)\)/gi;

// English words in parentheses that are NOT transliteration (translations, grammar labels)
const TRANSLATION_WORDS = new Set([
  // Grammar labels
  'masculine', 'feminine', 'neuter', 'plural', 'singular',
  'nominative', 'accusative', 'genitive', 'dative', 'locative', 'instrumental', 'vocative',
  'informal', 'formal', 'imperfective', 'perfective',
  'subject', 'object', 'location', 'possession', 'means', 'address',
  'animate', 'inanimate', 'hard', 'soft',
  // Common English translations
  'book', 'table', 'window', 'lamp', 'coffee', 'tea', 'water', 'bread',
  'apple', 'banana', 'orange', 'pear', 'potato', 'carrot', 'onion', 'tomato',
  'chicken', 'meat', 'milk', 'cheese', 'fruit', 'vegetables',
  'room', 'house', 'city', 'street', 'school', 'work', 'home',
  'read', 'write', 'go', 'come', 'see', 'hear', 'eat', 'drink', 'sleep',
  'was', 'were', 'did', 'went', 'said', 'heard',
  'small', 'large', 'big', 'new', 'old', 'good', 'bad',
  'tomorrow', 'yesterday', 'today', 'soon', 'later', 'now',
  'with', 'without', 'from', 'to', 'in', 'on', 'at', 'for', 'by',
  'straight', 'left', 'right', 'back', 'forward',
  'there', 'here', 'where', 'when', 'how', 'why', 'what', 'who',
  'my', 'your', 'his', 'her', 'our', 'their',
  'this', 'that', 'these', 'those',
  'all', 'some', 'many', 'few', 'much', 'little',
  'completion', 'through', 'completely', 'master', 'future', 'past',
  'absence', 'seashore', 'frost', 'cold', 'berries', 'harvest', 'leaves',
  'porridge', 'sandwiches', 'espresso', 'americano', 'cappuccino', 'latte',
  'croissant', 'sandwich', 'salad', 'soup', 'jam',
  'bring', 'tasty', 'takeaway', 'bookstore', 'medium', 'dark', 'light',
  'market', 'often', 'supermarket', 'cart', 'receipt',
  'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
  'january', 'february', 'march', 'april', 'may', 'june',
  'july', 'august', 'september', 'october', 'november', 'december',
  'day', 'week', 'month', 'year', 'hour', 'minute', 'second',
  'success', 'tree', 'flower', 'class', 'profession', 'people', 'things',
  'leg', 'river', 'student', 'letter', 'angel', 'god', 'time',
  'exit', 'entrance', 'out', 'in', 'over', 'under', 'across', 'behind',
  'nearest', 'imperatives', 'turn', 'cross', 'opposite',
  'watched', 'studied', 'transport', 'carry', 'can',
]);

function isTransliteration(latinText: string): boolean {
  // If it's a known English word/label, it's NOT transliteration
  if (TRANSLATION_WORDS.has(latinText.toLowerCase())) {
    return false;
  }
  // If it contains common Ukrainian transliteration patterns, it IS transliteration
  // Ukrainian transliterations often have: kh, zh, sh, ch, shch, ts, yi, ya, ye, yu
  const ukrainianPatterns = /kh|zh|sh|ch|ts|yi|ya|ye|yu|iy|yy|'|ii/i;
  if (ukrainianPatterns.test(latinText)) {
    return true;
  }
  // Single short words that look like transliteration
  if (latinText.length <= 3 && /^[a-z]+$/i.test(latinText)) {
    // Could be transliteration like "ya", "ye", "vi", "my"
    const shortTranslit = ['ya', 'ye', 'yi', 'yu', 'vi', 'my', 'ty', 'vy', 'ne', 'tak', 'ni'];
    if (shortTranslit.includes(latinText.toLowerCase())) {
      return true;
    }
  }
  return false;
}

// =============================================================================
// Verb Class Detection
// =============================================================================

// Class II verbs (-ити/-іти) - introduced in Module 08
const CLASS_II_VERBS = [
  'говорити', 'робити', 'бачити', 'дивитися', 'ходити', 'їздити', 'летіти',
  'бігти', 'сидіти', 'стояти', 'лежати', 'спати', 'любити', 'хотіти',
  'вчити', 'вчитися', 'просити', 'дякувати', 'вітати', 'телефонувати', 'купувати',
  'знаходити', 'пам\'ятати', 'забувати',
];

// Irregular verbs - introduced in Module 08
const IRREGULAR_VERBS = [
  'хотіти', 'їсти', 'пити', 'бути', 'йти', 'їхати',
];

// Reflexive verb pattern (-ся/-сь) - introduced in Module 25
const REFLEXIVE_PATTERN = /\b\w+[тсн][ия]ся\b|\b\w+[тсн][ия]сь\b/gi;

// Past tense patterns - introduced in Module 21
// Masculine: -в (читав, робив)
// Feminine: -ла (читала, робила)
// Neuter: -ло (читало, робило)
// Plural: -ли (читали, робили)
const PAST_TENSE_PATTERNS = [
  /\b[а-яіїєґ']+[аяоеиі]в\b/gi,   // masculine: читав, робив, був
  /\b[а-яіїєґ']+[аяоеиі]ла\b/gi,  // feminine: читала, робила, була
  /\b[а-яіїєґ']+[аяоеиі]ло\b/gi,  // neuter: читало, робило, було
  /\b[а-яіїєґ']+[аяоеиі]ли\b/gi,  // plural: читали, робили, були
];

// Exceptions - words that look like past tense but aren't
const PAST_TENSE_EXCEPTIONS = new Set([
  'стіл', 'стола', 'столу',  // table (not past tense)
  'вікно', 'вікна',          // window
  'село', 'села',            // village
  'слово', 'слова',          // word
  'молоко', 'молока',        // milk
  'яблуко', 'яблука',        // apple
  'число', 'числа',          // number
  'місто', 'міста',          // city
]);

// Future tense (буду + inf) - introduced in Module 22
const FUTURE_TENSE_WORDS = ['буду', 'будеш', 'буде', 'будемо', 'будете', 'будуть'];

// =============================================================================
// Time Words (Module 23)
// =============================================================================

const TIME_WORDS = [
  'завтра', 'вчора', 'сьогодні', 'зараз', 'потім', 'тоді',
  'рано', 'пізно', 'вранці', 'увечері', 'вдень', 'вночі',
  'понеділок', 'вівторок', 'середа', 'четвер', 'п\'ятниця', 'субота', 'неділя',
  'січень', 'лютий', 'березень', 'квітень', 'травень', 'червень',
  'липень', 'серпень', 'вересень', 'жовтень', 'листопад', 'грудень',
  'година', 'хвилина', 'секунда', 'тиждень', 'місяць', 'рік',
];

// =============================================================================
// Adjectives (Module 26)
// =============================================================================

const ADJECTIVES = [
  'великий', 'великa', 'велике', 'великі',
  'малий', 'мала', 'мале', 'малі',
  'новий', 'нова', 'нове', 'нові',
  'старий', 'стара', 'старе', 'старі',
  'добрий', 'добра', 'добре', 'добрі',
  'гарний', 'гарна', 'гарне', 'гарні',
  'поганий', 'погана', 'погане', 'погані',
  'красивий', 'красива', 'красиве', 'красиві',
  'цікавий', 'цікава', 'цікаве', 'цікаві',
  'сучасний', 'сучасна', 'сучасне', 'сучасні',
  'швидкий', 'швидка', 'швидке', 'швидкі',
  'повільний', 'повільна', 'повільне', 'повільні',
  'довгий', 'довга', 'довге', 'довгі',
  'короткий', 'коротка', 'коротке', 'короткі',
  'гарячий', 'гаряча', 'гаряче', 'гарячі',
  'холодний', 'холодна', 'холодне', 'холодні',
  'важкий', 'важка', 'важке', 'важкі',
  'легкий', 'легка', 'легке', 'легкі',
  // Accusative forms
  'цікаву', 'нову', 'довгого', 'красиві', 'сучасну',
];

// =============================================================================
// Possessives
// =============================================================================

// Module 05: мій/твій only
// Module 14: його/її/наш/ваш/їхній
const POSSESSIVES_MODULE_14 = [
  'його', 'її',
  'наш', 'наша', 'наше', 'наші',
  'ваш', 'ваша', 'ваше', 'ваші',
  'їхній', 'їхня', 'їхнє', 'їхні',
];

// =============================================================================
// Validation Logic
// =============================================================================

function getLevelFromModule(moduleNum: number): string {
  if (moduleNum <= 30) return 'A1';
  if (moduleNum <= 60) return 'A2';
  if (moduleNum <= 80) return 'A2+';
  if (moduleNum <= 120) return 'B1';
  if (moduleNum <= 160) return 'B1+';
  if (moduleNum <= 200) return 'B2';
  return 'B2+';
}

function shouldSkipLine(line: string, checkType: string): boolean {
  // Skip answer blocks for all checks
  if (line.includes('[!answer]')) return true;
  // Skip "Coming Next" sections
  if (line.includes('Coming Next') || line.includes('🎯')) return true;
  // Skip section titles that describe future content
  if (line.includes('Module') && /will learn|coming|later/i.test(line)) return true;

  // For vocabulary checks, skip table rows (we have a separate vocab count check)
  if (checkType === 'vocabulary' && line.startsWith('|') && line.includes('|')) return true;

  // For verb-class checks, don't skip tables - we want to catch verbs in tables too
  // For grammar checks on adjectives/tenses, skip only the vocab table section
  // (handled by checking if we're in vocab section)

  return false;
}

function isInVocabSection(lines: string[], lineIdx: number): boolean {
  // Check if current line is within a Vocabulary section
  for (let i = lineIdx; i >= 0; i--) {
    if (/^# (?:Vocabulary|Словник)/i.test(lines[i])) return true;
    if (/^# [A-ZА-ЯІЇЄҐ]/.test(lines[i]) && !/Vocabulary|Словник/i.test(lines[i])) return false;
  }
  return false;
}

function validateModule(modulePath: string, moduleNum: number): ValidationResult {
  const content = fs.readFileSync(modulePath, 'utf-8');
  const violations: ScopeViolation[] = [];

  // Extract title from frontmatter
  const titleMatch = content.match(/^title:\s*(.+)$/m);
  const title = titleMatch ? titleMatch[1].trim() : `Module ${moduleNum}`;
  const level = getLevelFromModule(moduleNum);

  const lines = content.split('\n');

  // ==========================================================================
  // 1. Transliteration Check (after Module 10)
  // ==========================================================================
  if (moduleNum > 10) {
    lines.forEach((line, idx) => {
      if (shouldSkipLine(line, 'transliteration')) return;
      // Skip IPA columns (contain /.../)
      if (line.includes('/') && /\/[^/]+\//.test(line)) return;
      // Skip vocab section for transliteration (IPA is fine there)
      if (isInVocabSection(lines, idx)) return;

      // Find Ukrainian word + (latin) pattern
      let match;
      const pattern = /([а-яіїєґ']+)\s*\(([a-z']+)\)/gi;
      while ((match = pattern.exec(line)) !== null) {
        const latinPart = match[2];
        if (isTransliteration(latinPart)) {
          violations.push({
            type: 'error',
            category: 'transliteration',
            message: `Transliteration: "${match[0]}" (remove after Module 10)`,
            line: idx + 1,
            context: line.trim().substring(0, 80),
          });
        }
      }
    });
  }

  // ==========================================================================
  // 2. Class II Verbs Check
  // Module 06 = Class I only, Module 08 = Class II
  // So Modules 1-7 should not have Class II verbs in practice/drills
  // ==========================================================================
  if (moduleNum < 8) {
    const classIIFound = new Set<string>();
    for (const verb of CLASS_II_VERBS) {
      // Note: \b doesn't work with Cyrillic, use lookaround with Cyrillic chars
      const pattern = new RegExp(`(?<![а-яіїєґ'])${verb}(?![а-яіїєґ'])`, 'gi');
      lines.forEach((line, idx) => {
        if (shouldSkipLine(line, 'verb-class')) return;
        if (pattern.test(line)) {
          classIIFound.add(verb);
        }
      });
    }
    // Report each verb once
    for (const verb of classIIFound) {
      violations.push({
        type: 'warning',
        category: 'verb-class',
        message: `Class II verb "${verb}" used before Module 08`,
      });
    }
  }

  // ==========================================================================
  // 3. Irregular Verbs Check (before Module 08)
  // ==========================================================================
  if (moduleNum < 8) {
    const irregularFound = new Set<string>();
    for (const verb of IRREGULAR_VERBS) {
      // Note: \b doesn't work with Cyrillic, use lookaround with Cyrillic chars
      const pattern = new RegExp(`(?<![а-яіїєґ'])${verb}(?![а-яіїєґ'])`, 'gi');
      lines.forEach((line, idx) => {
        if (shouldSkipLine(line, 'verb-class')) return;
        if (pattern.test(line)) {
          irregularFound.add(verb);
        }
      });
    }
    for (const verb of irregularFound) {
      violations.push({
        type: 'warning',
        category: 'verb-class',
        message: `Irregular verb "${verb}" used before Module 08`,
      });
    }
  }

  // ==========================================================================
  // 4. Reflexive Verbs Check (before Module 25)
  // ==========================================================================
  if (moduleNum < 25) {
    const reflexiveFound = new Set<string>();
    lines.forEach((line, idx) => {
      if (shouldSkipLine(line, 'grammar')) return;
      // Skip if explaining reflexives conceptually
      if (/reflexive|рефлексив|-ся ending/i.test(line)) return;
      const matches = line.match(REFLEXIVE_PATTERN);
      if (matches) {
        for (const match of matches) {
          reflexiveFound.add(match.toLowerCase());
        }
      }
    });
    for (const verb of reflexiveFound) {
      violations.push({
        type: 'warning',
        category: 'grammar',
        message: `Reflexive verb "${verb}" used before Module 25`,
      });
    }
  }

  // ==========================================================================
  // 5. Past Tense Check (before Module 21)
  // ==========================================================================
  if (moduleNum < 21) {
    const pastTenseFound = new Set<string>();
    lines.forEach((line, idx) => {
      if (shouldSkipLine(line, 'grammar')) return;
      // Skip lines explaining future content
      if (/past tense|минулий час/i.test(line)) return;
      // Skip vocab section
      if (isInVocabSection(lines, idx)) return;

      for (const pattern of PAST_TENSE_PATTERNS) {
        const matches = line.match(pattern);
        if (matches) {
          for (const match of matches) {
            // Skip known exceptions
            if (PAST_TENSE_EXCEPTIONS.has(match.toLowerCase())) continue;
            // Skip if it's in a "will learn" context
            if (/will|later|module \d+/i.test(line)) continue;
            pastTenseFound.add(match.toLowerCase());
          }
        }
      }
    });
    for (const form of pastTenseFound) {
      violations.push({
        type: 'warning',
        category: 'grammar',
        message: `Past tense form "${form}" used before Module 21`,
      });
    }
  }

  // ==========================================================================
  // 6. Future Tense Check (before Module 22)
  // ==========================================================================
  if (moduleNum < 22) {
    const futureFound = new Set<string>();
    for (const word of FUTURE_TENSE_WORDS) {
      const pattern = new RegExp(`\\b${word}\\b`, 'gi');
      lines.forEach((line, idx) => {
        if (shouldSkipLine(line, 'grammar')) return;
        if (isInVocabSection(lines, idx)) return;
        if (pattern.test(line)) {
          futureFound.add(word);
        }
      });
    }
    for (const word of futureFound) {
      violations.push({
        type: 'warning',
        category: 'grammar',
        message: `Future tense "${word}" used before Module 22`,
      });
    }
  }

  // ==========================================================================
  // 7. Time Words Check (before Module 23)
  // ==========================================================================
  if (moduleNum < 23) {
    const timeWordsFound = new Set<string>();
    for (const word of TIME_WORDS) {
      // Allow сьогодні and зараз as basic time references
      if (['сьогодні', 'зараз'].includes(word.toLowerCase())) continue;
      const pattern = new RegExp(`\\b${word}\\b`, 'gi');
      lines.forEach((line, idx) => {
        if (shouldSkipLine(line, 'vocabulary')) return;
        if (isInVocabSection(lines, idx)) return;
        if (pattern.test(line)) {
          timeWordsFound.add(word);
        }
      });
    }
    for (const word of timeWordsFound) {
      violations.push({
        type: 'info',
        category: 'vocabulary',
        message: `Time word "${word}" used before Module 23`,
      });
    }
  }

  // ==========================================================================
  // 8. Adjectives Check (before Module 26)
  // ==========================================================================
  if (moduleNum < 26) {
    const adjectivesFound = new Set<string>();
    for (const adj of ADJECTIVES) {
      // Allow "добре" as adverb (good/well/okay)
      if (adj === 'добре') continue;
      const pattern = new RegExp(`\\b${adj}\\b`, 'gi');
      lines.forEach((line, idx) => {
        if (shouldSkipLine(line, 'grammar')) return;
        if (isInVocabSection(lines, idx)) return;
        if (pattern.test(line)) {
          adjectivesFound.add(adj);
        }
      });
    }
    for (const adj of adjectivesFound) {
      violations.push({
        type: 'warning',
        category: 'grammar',
        message: `Adjective "${adj}" used before Module 26`,
      });
    }
  }

  // ==========================================================================
  // 9. Advanced Possessives Check (before Module 14)
  // ==========================================================================
  if (moduleNum < 14) {
    const possessivesFound = new Set<string>();
    for (const poss of POSSESSIVES_MODULE_14) {
      const pattern = new RegExp(`\\b${poss}\\b`, 'gi');
      lines.forEach((line, idx) => {
        if (shouldSkipLine(line, 'grammar')) return;
        if (isInVocabSection(lines, idx)) return;
        if (pattern.test(line)) {
          possessivesFound.add(poss);
        }
      });
    }
    for (const poss of possessivesFound) {
      violations.push({
        type: 'warning',
        category: 'grammar',
        message: `Possessive "${poss}" used before Module 14`,
      });
    }
  }

  // ==========================================================================
  // 10. Vocabulary Count Check
  // ==========================================================================
  const vocabMatch = content.match(
    /# (?:Vocabulary|Словник)[^\n]*\n([\s\S]*?)(?=\n---|$)/i
  );
  if (vocabMatch) {
    const tableMatch = vocabMatch[1].match(/\|[^\n]+\|\n\|[-|\s]+\|\n([\s\S]*?)(?=\n\n|$)/);
    if (tableMatch) {
      const rows = tableMatch[1].trim().split('\n').filter(r => r.includes('|'));
      const vocabCount = rows.length;

      // Module-specific targets from curriculum plan
      const moduleTargets: Record<number, number> = {
        1: 20, 2: 20, 3: 25, 4: 20, 5: 40, 6: 25, 7: 20, 8: 25, 9: 35, 10: 10,
        11: 25, 12: 20, 13: 30, 14: 20, 15: 40, 16: 25, 17: 25, 18: 45, 19: 10, 20: 10,
        21: 25, 22: 25, 23: 40, 24: 25, 25: 30, 26: 35, 27: 30, 28: 25, 29: 35, 30: 10,
      };

      const target = moduleTargets[moduleNum];
      if (target && vocabCount > target * 1.2) {  // Allow 20% over
        violations.push({
          type: 'warning',
          category: 'vocabulary',
          message: `Vocabulary count ${vocabCount} exceeds plan target ${target} (+${Math.round((vocabCount/target - 1) * 100)}%)`,
        });
      }
    }
  }

  return {
    moduleNum,
    title,
    level,
    violations,
  };
}

// =============================================================================
// Main
// =============================================================================

function main(): void {
  const args = process.argv.slice(2);
  const lang = args[0] || 'l2-uk-en';
  const rangeArg = args[1];

  const curriculumPath = path.join(__dirname, '..', 'curriculum', lang);
  const modulesDir = path.join(curriculumPath, 'modules');

  if (!fs.existsSync(modulesDir)) {
    console.error(`Modules directory not found: ${modulesDir}`);
    process.exit(1);
  }

  // Parse module range
  let startModule = 1;
  let endModule = 200;

  if (rangeArg) {
    if (rangeArg.includes('-')) {
      const [start, end] = rangeArg.split('-').map(Number);
      startModule = start;
      endModule = end;
    } else {
      startModule = endModule = parseInt(rangeArg);
    }
  }

  console.log(`\n🔍 Scope Validator: ${lang} (modules ${startModule}-${endModule})\n`);
  console.log('======================================================================\n');

  // Get all module files in range
  const files = fs.readdirSync(modulesDir)
    .filter(f => f.match(/^module-\d+\.md$/))
    .map(f => ({
      file: f,
      num: parseInt(f.match(/\d+/)?.[0] || '0'),
    }))
    .filter(f => f.num >= startModule && f.num <= endModule)
    .sort((a, b) => a.num - b.num);

  let totalViolations = 0;
  let modulesWithIssues = 0;
  const results: ValidationResult[] = [];

  for (const { file, num } of files) {
    const modulePath = path.join(modulesDir, file);
    const result = validateModule(modulePath, num);
    results.push(result);

    if (result.violations.length > 0) {
      modulesWithIssues++;
      totalViolations += result.violations.length;

      console.log(`📋 Module ${num}: ${result.title} (${result.level})`);

      // Group violations by category for cleaner output
      const byCategory: Record<string, ScopeViolation[]> = {};
      for (const v of result.violations) {
        if (!byCategory[v.category]) byCategory[v.category] = [];
        byCategory[v.category].push(v);
      }

      for (const [category, violations] of Object.entries(byCategory)) {
        console.log(`  [${category}]`);
        // Dedupe similar messages
        const seen = new Set<string>();
        for (const v of violations) {
          const key = v.message;
          if (seen.has(key)) continue;
          seen.add(key);

          const icon = v.type === 'error' ? '❌' : v.type === 'warning' ? '⚠️' : 'ℹ️';
          const count = violations.filter(x => x.message === key).length;
          const countStr = count > 1 ? ` (×${count})` : '';
          console.log(`    ${icon} ${v.message}${countStr}`);
        }
      }
      console.log();
    }
  }

  // Summary
  console.log('======================================================================\n');
  console.log('📊 SUMMARY\n');
  console.log(`  Modules scanned: ${files.length}`);
  console.log(`  Modules with issues: ${modulesWithIssues}`);
  console.log(`  Total violations: ${totalViolations}`);

  // Count by type
  const byType = { error: 0, warning: 0, info: 0 };
  const byCategory: Record<string, number> = {};

  for (const r of results) {
    for (const v of r.violations) {
      byType[v.type]++;
      byCategory[v.category] = (byCategory[v.category] || 0) + 1;
    }
  }

  console.log(`\n  By Severity:`);
  console.log(`    ❌ Errors: ${byType.error}`);
  console.log(`    ⚠️  Warnings: ${byType.warning}`);
  console.log(`    ℹ️  Info: ${byType.info}`);

  console.log(`\n  By Category:`);
  for (const [cat, count] of Object.entries(byCategory).sort((a, b) => b[1] - a[1])) {
    console.log(`    ${cat}: ${count}`);
  }

  console.log();
}

main();
