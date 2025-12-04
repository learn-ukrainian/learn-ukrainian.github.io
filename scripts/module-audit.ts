#!/usr/bin/env npx ts-node
/**
 * Module Audit Script
 *
 * Finds non-compliant, broken, or under-enriched modules.
 * Checks against MODULE-RICHNESS-GUIDELINES.md requirements.
 *
 * Usage:
 *   npx ts-node scripts/module-audit.ts [lang] [module-range] [--fix]
 *
 * Examples:
 *   npx ts-node scripts/module-audit.ts l2-uk-en           # Audit all modules
 *   npx ts-node scripts/module-audit.ts l2-uk-en 41-65     # Audit range
 *   npx ts-node scripts/module-audit.ts l2-uk-en 47        # Audit single module
 *   npx ts-node scripts/module-audit.ts l2-uk-en 81-90 --fix  # Generate fix prompts
 *
 * Options:
 *   --fix    Generate actionable fix prompts for each module with issues.
 *            Prompts are sorted by severity (most issues first).
 *            Copy-paste prompts directly to Claude to fix modules.
 */

import * as fs from 'fs';
import * as path from 'path';
import {
  getVocabDatabase,
  resetVocabDatabase,
  VocabDatabase,
} from './lib/vocab-sqlite';

// =============================================================================
// Types
// =============================================================================

interface Issue {
  type: 'error' | 'warning' | 'info';
  category: string;
  message: string;
  line?: number;
  context?: string;
}

interface ModuleAudit {
  module: number;
  title: string;
  level: string;
  issues: Issue[];
  stats: {
    activities: number;
    activityTypes: string[];
    vocabCount: number;
    hasVocabSection: boolean;
    hasSummary: boolean;
    wordCount: number;
    engagementBoxes: number;
    itemsPerActivity: number[];
    vocabDuplicates: string[];  // Words already introduced in earlier modules
  };
}

// =============================================================================
// Requirements from MODULE-RICHNESS-GUIDELINES.md
// =============================================================================

interface LevelRequirements {
  moduleRange: [number, number];
  newWordsMin: number;
  newWordsMax: number;
  activityCount: number;
  itemsPerActivity: number;
  fillInWords: [number, number];
  unjumbleWords: [number, number];
  immersionLevel: number;  // Target Ukrainian percentage (0.0 - 1.0)
}

// =============================================================================
// Requirements based on Ukrainian State Standard (September 2024)
// Source: docs/l2-uk-en/UKRAINIAN-CEFR-RESEARCH.md
// =============================================================================

// QUALITY TARGETS - these are ambitious goals, not bare minimums
// Good modules should comfortably exceed these values
const LEVEL_REQUIREMENTS: Record<string, LevelRequirements> = {
  'A1': {
    moduleRange: [1, 30],
    newWordsMin: 18, newWordsMax: 25,      // Target ~20 new words per module
    activityCount: 8,                       // 8 activities for variety
    itemsPerActivity: 12,                   // Solid practice per activity
    fillInWords: [5, 8],                    // "Моя сестра ___ в лікарні" (5-8 words)
    unjumbleWords: [5, 8],
    immersionLevel: 0.30,
  },
  'A2': {
    moduleRange: [31, 60],
    newWordsMin: 22, newWordsMax: 30,      // Target ~25 new words
    activityCount: 10,                      // More activity variety
    itemsPerActivity: 12,
    fillInWords: [6, 10],                   // Compound sentences with connectors
    unjumbleWords: [6, 10],
    immersionLevel: 0.40,
  },
  'A2+': {
    moduleRange: [61, 80],
    newWordsMin: 35, newWordsMax: 45,      // Vocabulary expansion phase
    activityCount: 12,
    itemsPerActivity: 15,
    fillInWords: [8, 12],                   // Subordinate clauses, more complexity
    unjumbleWords: [8, 12],
    immersionLevel: 0.50,
  },
  'B1': {
    moduleRange: [81, 120],
    newWordsMin: 28, newWordsMax: 35,      // Solid vocabulary growth
    activityCount: 14,                      // Rich activity set
    itemsPerActivity: 20,
    fillInWords: [10, 15],                  // Complex sentences, conditionals
    unjumbleWords: [10, 15],
    immersionLevel: 0.60,
  },
  'B1+': {
    moduleRange: [121, 160],
    newWordsMin: 28, newWordsMax: 35,
    activityCount: 14,
    itemsPerActivity: 20,
    fillInWords: [11, 16],                  // Participles, extended complexity
    unjumbleWords: [11, 16],
    immersionLevel: 0.70,
  },
  'B2': {
    moduleRange: [161, 200],
    newWordsMin: 30, newWordsMax: 40,      // Advanced vocabulary
    activityCount: 16,                      // Maximum activity variety
    itemsPerActivity: 22,
    fillInWords: [12, 18],                  // Sophisticated structures, passive
    unjumbleWords: [12, 18],
    immersionLevel: 0.85,
  },
  'B2+': {
    moduleRange: [201, 240],
    newWordsMin: 30, newWordsMax: 40,
    activityCount: 16,
    itemsPerActivity: 22,
    fillInWords: [13, 19],                  // Advanced stylistic variation
    unjumbleWords: [13, 19],
    immersionLevel: 0.90,
  },
  'C1': {
    moduleRange: [241, 400],
    newWordsMin: 35, newWordsMax: 45,      // Rich academic vocabulary
    activityCount: 16,
    itemsPerActivity: 24,
    fillInWords: [14, 22],                  // Advanced academic/literary
    unjumbleWords: [14, 22],
    immersionLevel: 0.95,
  },
};

// Tolerance for immersion level deviation (±10%)
const IMMERSION_TOLERANCE = 0.10;

// =============================================================================
// Grammar Topics by Level (Ukrainian State Standard September 2024)
// These are used to validate that modules cover appropriate grammar content
// =============================================================================

interface GrammarRequirement {
  topic: string;
  patterns: RegExp[];  // Patterns to detect this grammar topic in content
  required: boolean;   // Is this required for the level?
}

const LEVEL_GRAMMAR: Record<string, GrammarRequirement[]> = {
  'A1': [
    { topic: 'Cyrillic alphabet', patterns: [/(?:алфавіт|alphabet|кирилиц|cyrillic)/i], required: true },
    { topic: 'Noun gender', patterns: [/(?:рід іменник|gender|masculine|feminine|neuter|чоловічий|жіночий|середній)/i], required: true },
    { topic: 'Nominative case', patterns: [/(?:називний|nominative)/i], required: true },
    { topic: 'Accusative case', patterns: [/(?:знахідний|accusative)/i], required: true },
    { topic: 'Present tense', patterns: [/(?:теперішній час|present tense)/i], required: true },
    { topic: 'Past tense', patterns: [/(?:минулий час|past tense)/i], required: true },
    { topic: 'Personal pronouns', patterns: [/(?:особові займенник|personal pronoun|я, ти, він)/i], required: true },
  ],
  'A2': [
    { topic: 'Genitive case', patterns: [/(?:родовий|genitive)/i], required: true },
    { topic: 'Dative case', patterns: [/(?:давальний|dative)/i], required: true },
    { topic: 'Locative case', patterns: [/(?:місцевий|locative)/i], required: true },
    { topic: 'Aspect introduction', patterns: [/(?:вид дієслова|aspect|доконан|недоконан|perfective|imperfective)/i], required: true },
    { topic: 'Comparative adjectives', patterns: [/(?:вищий ступінь|comparative|більш|менш|-іший|-ший)/i], required: true },
    { topic: 'Euphony rules', patterns: [/(?:евфонія|euphony|у\/в|і\/й|з\/із\/зі)/i], required: true },
    { topic: 'Reflexive verbs', patterns: [/(?:зворотн|reflexive|-ся\b)/i], required: true },
  ],
  'A2+': [
    { topic: 'Instrumental case', patterns: [/(?:орудний|instrumental)/i], required: true },
    { topic: 'Vocative case', patterns: [/(?:кличний|vocative)/i], required: true },
    { topic: 'Verbs of motion', patterns: [/(?:дієслова руху|motion verb|йти|ходити|їхати|їздити)/i], required: true },
    { topic: 'Relative clauses', patterns: [/(?:підрядні речення|relative clause|який|яка|яке)/i], required: true },
  ],
  'B1': [
    { topic: 'Aspect mastery', patterns: [/(?:вид дієслова|aspect|доконан|недоконан)/i], required: true },
    { topic: 'Motion verbs with prefixes', patterns: [/(?:при-|ви-|за-|пере-|дієслова руху з префікс|prefixed motion)/i], required: true },
    { topic: 'Conditional mood', patterns: [/(?:умовний спосіб|conditional|якби|б\b)/i], required: true },
    { topic: 'Past passive participles', patterns: [/(?:пасивний дієприкметник|passive participle|-ний\b|-тий\b)/i], required: true },
    { topic: 'Reported speech', patterns: [/(?:непряма мова|reported speech|indirect speech)/i], required: true },
    { topic: 'Purpose clauses', patterns: [/(?:мета|purpose|щоб)/i], required: true },
  ],
  'B1+': [
    { topic: 'Adverbial participles', patterns: [/(?:дієприслівник|adverbial participle|-учи|-ючи|-вши)/i], required: true },
    { topic: 'Impersonal passive', patterns: [/(?:-но\/-то|impersonal passive|написано|зроблено)/i], required: true },
    { topic: 'Numeral declension', patterns: [/(?:відмінювання числівник|numeral declension|collective numeral|двоє|троє)/i], required: true },
  ],
  'B2': [
    { topic: 'All passive forms', patterns: [/(?:пасив|passive|будується|-ся\b|-ний\b|-тий\b|-но\/-то)/i], required: true },
    { topic: 'Active participles', patterns: [/(?:активний дієприкметник|active participle|-учий|-ючий|-лий)/i], required: true },
    { topic: 'Functional styles', patterns: [/(?:функціональний стиль|register|стиль|офіційний|науковий|розмовний|публіцистичний|художній)/i], required: true },
    { topic: 'Phraseology', patterns: [/(?:фразеологі|прислів|idiom|proverb|приказк|крилат)/i], required: true },
    { topic: 'Word formation', patterns: [/(?:словотвір|word formation|суфікс|префікс|-ння\b|-ець\b|-ач\b)/i], required: false },
  ],
  'B2+': [
    { topic: 'Synonymy', patterns: [/(?:синонім|synonym)/i], required: true },
    { topic: 'Register control', patterns: [/(?:регістр|register|formal|informal|офіційний|неофіційний)/i], required: true },
    { topic: 'Historical content', patterns: [/(?:історі|history|Київська Русь|козак|гетьман)/i], required: true },
  ],
  'C1': [
    { topic: 'Archaic forms', patterns: [/(?:архаїчн|archaic|застарілий|церковнослов)/i], required: false },
    { topic: 'Dialectal awareness', patterns: [/(?:діалект|dialect|говірк|регіональн)/i], required: false },
    { topic: 'Literary devices', patterns: [/(?:метафор|епітет|метонімі|синекдох|metaphor|epithet)/i], required: true },
    { topic: 'Academic writing', patterns: [/(?:академічн|academic|наукови|essay|есе)/i], required: true },
  ],
};

// =============================================================================
// Audit Functions
// =============================================================================

function auditModule(filePath: string, vocabDb?: VocabDatabase): ModuleAudit {
  const content = fs.readFileSync(filePath, 'utf8');
  const lines = content.split('\n');
  const issues: Issue[] = [];
  const vocabDuplicates: string[] = [];

  // Extract frontmatter
  const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);
  const frontmatter = frontmatterMatch ? frontmatterMatch[1] : '';

  const moduleNum = parseInt(frontmatter.match(/module:\s*(\d+)/)?.[1] || '0');
  const title = frontmatter.match(/title:\s*"?([^"\n]+)"?/)?.[1] || 'Unknown';
  const level = frontmatter.match(/level:\s*(\w+\+?)/)?.[1] || 'Unknown';

  const req = LEVEL_REQUIREMENTS[level];

  // ==========================================================================
  // 1. BROKEN FORMAT DETECTION
  // ==========================================================================

  // Old order format: - [N] text
  const orderFormatMatches = content.matchAll(/^- \[(\d+)\]\s+(.+)$/gm);
  for (const match of orderFormatMatches) {
    const lineNum = content.substring(0, match.index).split('\n').length;
    issues.push({
      type: 'error',
      category: 'broken-format',
      message: `Old order format "- [${match[1]}]" should be unjumble format`,
      line: lineNum,
      context: match[0].substring(0, 60),
    });
  }

  // Arrow in answer position (indented arrow)
  const arrowAnswerMatches = content.matchAll(/^(\s{2,})→\s*\*?\*?(.+)$/gm);
  for (const match of arrowAnswerMatches) {
    const lineNum = content.substring(0, match.index).split('\n').length;
    // Skip if it's in a table or transformation context
    const prevLines = content.substring(0, match.index).split('\n').slice(-3).join('\n');
    if (!prevLines.includes('|') && !prevLines.match(/^\s*-\s+\w+\s*→/m)) {
      issues.push({
        type: 'error',
        category: 'broken-format',
        message: 'Arrow answer format should use > [!answer]',
        line: lineNum,
        context: match[0].substring(0, 60),
      });
    }
  }

  // Old pairs: format
  if (content.match(/^pairs:\s*$/m)) {
    const lineNum = content.split('\n').findIndex(l => l.match(/^pairs:\s*$/)) + 1;
    issues.push({
      type: 'error',
      category: 'broken-format',
      message: 'Old "pairs:" format should use table format',
      line: lineNum,
    });
  }

  // Old groups: format
  if (content.match(/^groups:\s*$/m)) {
    const lineNum = content.split('\n').findIndex(l => l.match(/^groups:\s*$/)) + 1;
    issues.push({
      type: 'error',
      category: 'broken-format',
      message: 'Old "groups:" format should use ### Category format',
      line: lineNum,
    });
  }

  // ==========================================================================
  // 2. ACTIVITY ANALYSIS
  // ==========================================================================

  // Count activities and their types
  const activityHeaders = content.match(/^## (quiz|match-up|group-sort|fill-in|true-false|unjumble|select|order|translate):\s*(.*)$/gim) || [];
  const activityCount = activityHeaders.length;
  const activityTypes = [...new Set(activityHeaders.map(h => h.match(/## (\w+(-\w+)?):/i)?.[1]?.toLowerCase() || ''))];

  // Count items per activity
  const itemsPerActivity: number[] = [];
  const activitySections = content.matchAll(/## (quiz|match-up|group-sort|fill-in|true-false|unjumble|select|order|translate):[^\n]*\n([\s\S]*?)(?=\n## |\n# |\n---\n# |$)/gi);

  for (const actMatch of activitySections) {
    const actType = actMatch[1].toLowerCase();
    const actContent = actMatch[2];
    let itemCount = 0;

    if (actType === 'quiz' || actType === 'select') {
      itemCount = (actContent.match(/^\d+\.\s+/gm) || []).length;
    } else if (actType === 'match-up') {
      itemCount = Math.max(0, (actContent.match(/^\|[^|]+\|/gm) || []).length - 2);
    } else if (actType === 'group-sort') {
      itemCount = (actContent.match(/^- .+$/gm) || []).length;
    } else if (actType === 'true-false') {
      itemCount = (actContent.match(/^- \[[ x]\]/gm) || []).length;
    } else if (actType === 'fill-in' || actType === 'unjumble') {
      itemCount = (actContent.match(/^\d+\.\s+/gm) || []).length;
    }

    itemsPerActivity.push(itemCount);
  }

  // Check for missing Activities section
  if (!content.match(/# (?:Activities|Вправи)/)) {
    issues.push({
      type: 'warning',
      category: 'missing-content',
      message: 'No Activities section found',
    });
  }

  // Check activity count against requirements
  if (req && activityCount < req.activityCount) {
    issues.push({
      type: 'warning',
      category: 'requirements',
      message: `Only ${activityCount} activities (${level} requires ${req.activityCount})`,
    });
  }

  // Check activity diversity (at least 3 different types)
  if (activityCount >= 3 && activityTypes.length < 3) {
    issues.push({
      type: 'warning',
      category: 'requirements',
      message: `Low activity diversity: only ${activityTypes.length} types (need 3+): ${activityTypes.join(', ')}`,
    });
  }

  // Check items per activity against requirements
  if (req) {
    for (let i = 0; i < itemsPerActivity.length; i++) {
      if (itemsPerActivity[i] < req.itemsPerActivity && itemsPerActivity[i] > 0) {
        issues.push({
          type: 'info',
          category: 'requirements',
          message: `Activity ${i + 1} has only ${itemsPerActivity[i]} items (${level} target: ${req.itemsPerActivity})`,
        });
      }
    }
  }

  // ==========================================================================
  // 3. ACTIVITY VALIDATION
  // ==========================================================================

  // Check for quiz without correct answer marked
  const quizSections = content.matchAll(/## quiz:[^\n]*\n([\s\S]*?)(?=\n## |\n# |\n---\n|$)/gi);
  for (const quizMatch of quizSections) {
    const quizContent = quizMatch[1];
    // Split by numbered items using lookahead, then filter to actual questions
    const questions = quizContent.split(/(?=^\d+\.\s+)/m).filter(p => p.match(/^\d+\./));
    for (let qNum = 0; qNum < questions.length; qNum++) {
      if (!questions[qNum].includes('[x]')) {
        const lineNum = content.substring(0, quizMatch.index).split('\n').length;
        issues.push({
          type: 'error',
          category: 'broken-activity',
          message: `Quiz question ${qNum + 1} has no correct answer marked [x]`,
          line: lineNum,
        });
      }
    }
  }

  // Check for unjumble without answers
  const unjumbleSections = content.matchAll(/## unjumble:[^\n]*\n([\s\S]*?)(?=\n## |\n# |\n---\n|$)/gi);
  for (const unjMatch of unjumbleSections) {
    const unjContent = unjMatch[1];
    const items = unjContent.match(/^\d+\.\s+/gm) || [];
    const answers = unjContent.match(/>\s*\[!answer\]/g) || [];
    if (items.length > answers.length) {
      const lineNum = content.substring(0, unjMatch.index).split('\n').length;
      issues.push({
        type: 'error',
        category: 'broken-activity',
        message: `Unjumble has ${items.length} items but only ${answers.length} answers`,
        line: lineNum,
      });
    }

    // Check unjumble word count
    if (req) {
      const unjumbleItems = unjContent.matchAll(/^\d+\.\s+([^\n]+)/gm);
      for (const item of unjumbleItems) {
        const wordCount = item[1].split(/\s*\/\s*/).length;
        if (wordCount > 0 && (wordCount < req.unjumbleWords[0] || wordCount > req.unjumbleWords[1])) {
          const lineNum = content.substring(0, unjMatch.index).split('\n').length;
          issues.push({
            type: 'info',
            category: 'complexity',
            message: `Unjumble item has ${wordCount} words (${level} target: ${req.unjumbleWords[0]}-${req.unjumbleWords[1]})`,
            line: lineNum,
          });
          break; // Only report once per activity
        }
      }
    }
  }

  // Check for fill-in without answers
  const fillSections = content.matchAll(/## fill-in:[^\n]*\n([\s\S]*?)(?=\n## |\n# |\n---\n|$)/gi);
  for (const fillMatch of fillSections) {
    const fillContent = fillMatch[1];
    const blanks = fillContent.match(/___/g) || [];
    const answers = fillContent.match(/>\s*\[!answer\]/g) || [];
    if (blanks.length > answers.length) {
      const lineNum = content.substring(0, fillMatch.index).split('\n').length;
      issues.push({
        type: 'warning',
        category: 'broken-activity',
        message: `Fill-in has ${blanks.length} blanks but only ${answers.length} answers`,
        line: lineNum,
      });
    }
  }

  // Check for match-up without table
  const matchSections = content.matchAll(/## match-up:[^\n]*\n([\s\S]*?)(?=\n## |\n# |\n---\n|$)/gi);
  for (const matchMatch of matchSections) {
    const matchContent = matchMatch[1];
    if (!matchContent.includes('|')) {
      const lineNum = content.substring(0, matchMatch.index).split('\n').length;
      issues.push({
        type: 'error',
        category: 'broken-activity',
        message: 'Match-up activity missing table format',
        line: lineNum,
      });
    }
  }

  // ==========================================================================
  // 4. VOCABULARY ANALYSIS
  // ==========================================================================

  const vocabSection = content.match(/# (?:Vocabulary|Словник)\n([\s\S]*?)(?=\n# |$)/);
  const hasVocabSection = !!vocabSection;
  let vocabCount = 0;

  if (vocabSection) {
    const vocabContent = vocabSection[1];
    const tableRows = vocabContent.match(/^\|[^|]+\|/gm) || [];
    vocabCount = Math.max(0, tableRows.length - 2); // Subtract header and separator

    // Check for empty vocab
    if (vocabCount === 0) {
      issues.push({
        type: 'warning',
        category: 'missing-content',
        message: 'Vocabulary section exists but no entries found',
      });
    }

    // Check vocab count against requirements
    if (req) {
      if (vocabCount < req.newWordsMin) {
        issues.push({
          type: 'warning',
          category: 'requirements',
          message: `Only ${vocabCount} vocab words (${level} requires ${req.newWordsMin}-${req.newWordsMax})`,
        });
      } else if (vocabCount > req.newWordsMax + 10) {
        issues.push({
          type: 'info',
          category: 'requirements',
          message: `High vocab count: ${vocabCount} words (${level} target: ${req.newWordsMin}-${req.newWordsMax}) - consider splitting`,
        });
      }
    }
  } else {
    issues.push({
      type: 'warning',
      category: 'missing-content',
      message: 'No Vocabulary section found',
    });
  }

  // ==========================================================================
  // 4b. VOCABULARY DUPLICATE CHECK (cascade detection)
  // ==========================================================================

  // Check if any vocab words in this module were already introduced earlier
  if (vocabSection && vocabDb) {
    const vocabContent = vocabSection[1];

    // Extract Ukrainian words from vocab table (first column)
    const vocabTableMatch = vocabContent.match(/\|[^\n]+\|\n\|[-|\s]+\|\n([\s\S]*?)(?=\n\n|\n---|\n#|$)/);
    if (vocabTableMatch) {
      const tableRows = vocabTableMatch[1].trim().split('\n');
      for (const row of tableRows) {
        if (!row.includes('|')) continue;
        const cells = row.split('|').map(c => c.trim()).filter(c => c);
        if (cells.length < 1) continue;

        const ukWord = cells[0].replace(/\*\*/g, '').trim();
        if (!ukWord || ukWord.includes('---')) continue;

        // Check if word exists in DB with earlier first_module
        const entry = vocabDb.getEntry(ukWord);
        if (entry && entry.first_module < moduleNum) {
          vocabDuplicates.push(`${ukWord} (introduced in module ${entry.first_module})`);
        }
      }
    }

    if (vocabDuplicates.length > 0) {
      issues.push({
        type: 'warning',
        category: 'vocab-duplicate',
        message: `${vocabDuplicates.length} vocab word(s) already introduced in earlier modules - remove from this module's vocab`,
      });
    }
  }

  // ==========================================================================
  // 5. ENGAGEMENT BOXES
  // ==========================================================================

  // Check for engagement boxes (💡 Did You Know, ⚡ Pro Tip, 📜 History Bite, 🎭 Culture Corner, 🎬 Pop Culture, etc.)
  const engagementPatterns = [
    />\s*💡\s*\*\*Did You Know/g,
    />\s*⚡\s*\*\*Pro Tip/g,
    />\s*📜\s*\*\*History Bite/g,
    />\s*🎭\s*\*\*Culture Corner/g,
    />\s*🔍\s*\*\*Myth Buster/g,
    />\s*🎯\s*\*\*Fun Fact/g,
    />\s*🔗\s*\*\*Language Link/g,
    />\s*🌍\s*\*\*Real World/g,
    />\s*🎬\s*\*\*Pop Culture/g,
  ];

  let engagementBoxes = 0;
  for (const pattern of engagementPatterns) {
    engagementBoxes += (content.match(pattern) || []).length;
  }

  if (engagementBoxes === 0) {
    issues.push({
      type: 'warning',
      category: 'enrichment',
      message: 'No engagement boxes found (💡 Did You Know, ⚡ Pro Tip, etc.)',
    });
  } else if (engagementBoxes < 2) {
    issues.push({
      type: 'info',
      category: 'enrichment',
      message: `Only ${engagementBoxes} engagement box (recommend 2+ per module)`,
    });
  }

  // ==========================================================================
  // 6. STRUCTURE CHECKS
  // ==========================================================================

  // Check for Summary section
  const hasSummary = !!content.match(/# (?:Summary|Підсумок)/);
  if (!hasSummary) {
    issues.push({
      type: 'info',
      category: 'missing-content',
      message: 'No Summary section found',
    });
  }

  // Check for Introduction
  if (!content.match(/# (?:Introduction|Вступ|Lesson Content)/)) {
    issues.push({
      type: 'info',
      category: 'missing-content',
      message: 'No Introduction/Вступ section found',
    });
  }

  // ==========================================================================
  // 7. CONTENT DEPTH / DRY NARRATION
  // ==========================================================================

  // Get main content (excluding frontmatter, activities, vocab, summary)
  const mainContent = content
    .replace(/^---[\s\S]*?---/, '')
    .replace(/# (?:Activities|Вправи)[\s\S]*?(?=# (?:Vocabulary|Словник)|$)/, '')
    .replace(/# (?:Vocabulary|Словник)[\s\S]*?(?=# |$)/, '')
    .replace(/# (?:Summary|Підсумок)[\s\S]*$/, '');

  const wordCount = mainContent.split(/\s+/).filter(w => w.length > 2).length;

  // Check for minimal lesson content - these are QUALITY targets
  // Good modules should have substantial explanatory content
  const minWordCount: Record<string, number> = {
    'A1': 600,      // Substantial explanation in English for beginners
    'A2': 700,      // More context and examples
    'A2+': 800,     // Richer content as immersion increases
    'B1': 900,      // Complex grammar needs thorough explanation
    'B1+': 950,     // Continued depth
    'B2': 1000,     // Advanced topics need substantial treatment
    'B2+': 1050,    // Historical/cultural content requires depth
    'C1': 1100,     // Academic-level depth
  };

  const minWords = minWordCount[level] || 500;
  if (wordCount < minWords) {
    issues.push({
      type: 'warning',
      category: 'enrichment',
      message: `Low content word count: ${wordCount} words (${level} should have ${minWords}+)`,
    });
  }

  // Check for placeholder text
  const placeholders = [
    /TODO/gi,
    /FIXME/gi,
    /\[placeholder\]/gi,
    /\[TBD\]/gi,
    /\[to be added\]/gi,
  ];
  for (const pattern of placeholders) {
    const matches = content.matchAll(pattern);
    for (const match of matches) {
      const lineNum = content.substring(0, match.index).split('\n').length;
      issues.push({
        type: 'warning',
        category: 'incomplete',
        message: `Placeholder text found: "${match[0]}"`,
        line: lineNum,
      });
    }
  }

  // ==========================================================================
  // 8. PRONUNCIATION GUIDANCE (B2+ Grammar Modules)
  // ==========================================================================

  if (['B2', 'C1', 'C2'].includes(level)) {
    const isGrammarModule = frontmatter.match(/tags:.*grammar/i) || title.toLowerCase().includes('grammar');
    if (isGrammarModule && !content.match(/# (?:Pronunciation|Вимова)/i)) {
      issues.push({
        type: 'info',
        category: 'requirements',
        message: 'B2+ grammar module should include pronunciation guidance section',
      });
    }
  }

  // ==========================================================================
  // 9. CHECKPOINT MODULES (every 10th: 10, 20, 30, etc.)
  // ==========================================================================

  const isCheckpoint = moduleNum % 10 === 0;
  const isReviewModule = frontmatter.match(/tags:.*(?:review|checkpoint)/i) || title.toLowerCase().includes('checkpoint');

  if (isCheckpoint || isReviewModule) {
    // Check for named character - supports both formats:
    // Format 1: "Ліам, 26, Irish, Dublin"
    // Format 2: "**Ліам** (26, Irish, Dublin)"
    const hasCharacterName = content.match(/(?:\*\*)?(?:Ліам|Софія|Марко|Олена|Джон|Анна|Микола|Катерина|Емма|Сара|Хосе|Акіко|Олівер|Fatima|Марія|Томас|Юлія|\w+)(?:\*\*)?\s*[\(,]\s*\d+,?\s*(?:Irish|American|British|Canadian|German|French|Ukrainian|Polish|Australian|Brazilian|Japanese|Spanish)/i);
    if (!hasCharacterName) {
      issues.push({
        type: 'warning',
        category: 'checkpoint',
        message: 'Checkpoint missing named character (e.g., "Ліам, 26, Irish, Dublin")',
      });
    }

    // Check for dialogue tables
    const hasDialogueTable = content.match(/\|\s*(?:Speaker|Мовець|Хто)\s*\|.*\|.*\|/i);
    if (!hasDialogueTable) {
      issues.push({
        type: 'warning',
        category: 'checkpoint',
        message: 'Checkpoint missing dialogue tables (Speaker | Ukrainian | English)',
      });
    }

    // Check for testimonies (multiple learner quotes) - look for quotation patterns with learner experiences
    const testimonies = content.match(/>\s*\*"[^"]+"\*/g) || [];  // Matches: > *"quote"*
    const altTestimonies = content.match(/["«»].*(?:дуже|легко|важко|цікаво|подобається|learned|clicked|scared|helped|trick|emotional|started).*["«»\*]/gi) || [];
    const totalTestimonies = Math.max(testimonies.length, altTestimonies.length);
    if (totalTestimonies < 2) {
      issues.push({
        type: 'info',
        category: 'checkpoint',
        message: `Checkpoint has only ${totalTestimonies} testimonies (recommend 3-4 learner quotes)`,
      });
    }

    // Check for story/narrative opening
    const hasNarrative = content.match(/(?:journal|diary|journal entry|story|щоденник|історія)/i) ||
                         content.match(/^(?:День \d+|Day \d+|Today|Сьогодні)/m);
    if (!hasNarrative) {
      issues.push({
        type: 'info',
        category: 'checkpoint',
        message: 'Checkpoint may lack opening narrative (journal entry, story)',
      });
    }
  }

  // ==========================================================================
  // 10. ACTIVITY ORDER (should follow priority)
  // ==========================================================================

  const activityPriority: Record<string, number> = {
    'quiz': 1,
    'match-up': 2,
    'group-sort': 3,
    'true-false': 4,
    'select': 5,
    'order': 6,
    'fill-in': 7,
    'unjumble': 8,
  };

  const activityOrder: { type: string; index: number }[] = [];
  const activityOrderMatches = content.matchAll(/^## (quiz|match-up|group-sort|fill-in|true-false|unjumble|select|order):/gim);
  let actIdx = 0;
  for (const match of activityOrderMatches) {
    activityOrder.push({ type: match[1].toLowerCase(), index: actIdx++ });
  }

  // Check if high-load activities come before low-load ones (not ideal)
  let lastPriority = 0;
  let orderViolations = 0;
  for (const act of activityOrder) {
    const priority = activityPriority[act.type] || 5;
    if (priority < lastPriority - 2) {
      // Allow some flexibility (2 priority levels)
      orderViolations++;
    }
    lastPriority = priority;
  }

  if (orderViolations >= 2) {
    issues.push({
      type: 'info',
      category: 'activity-order',
      message: `Activity order may be suboptimal (high-load activities before low-load). Current order: ${activityOrder.map(a => a.type).join(' → ')}`,
    });
  }

  // ==========================================================================
  // 11. CONVERSATION/DIALOGUE QUALITY
  // ==========================================================================

  // Check for dialogue tables in non-checkpoint modules too (good practice)
  const dialogueTables = content.match(/\|\s*(?:Speaker|Мовець|Хто|Person|Особа|A|B)\s*\|/gi) || [];
  const hasConversationalContent = content.match(/(?:conversation|dialogue|діалог|розмова)/i);

  if (hasConversationalContent && dialogueTables.length === 0) {
    issues.push({
      type: 'info',
      category: 'enrichment',
      message: 'Module mentions dialogue/conversation but has no dialogue tables',
    });
  }

  // ==========================================================================
  // 12. CONTENT QUALITY & RICHNESS
  // ==========================================================================

  // Check for PPP structure (warm-up/presentation/practice/production)
  const hasWarmUp = !!content.match(/^##\s*(?:warm-?up|introduction|вступ|розігрів)/im);
  const hasPresentation = !!content.match(/^##\s*(?:presentation|theory|теорія|пояснення)/im);
  const hasPractice = !!content.match(/^##\s*(?:practice|guided|практика)/im);
  const hasProduction = !!content.match(/^##\s*(?:production|free|вироб|творч)/im);

  const pppCount = [hasWarmUp, hasPresentation, hasPractice, hasProduction].filter(Boolean).length;
  if (pppCount < 2 && !isCheckpoint && !isReviewModule) {
    issues.push({
      type: 'info',
      category: 'content-quality',
      message: `Limited lesson structure: only ${pppCount}/4 PPP sections (warm-up/presentation/practice/production)`,
    });
  }

  // Check for examples in content (lessons should have multiple examples)
  const examplePatterns = [
    /(?:example|приклад|наприклад):/gi,
    /^\s*[-•]\s*\*\*[^*]+\*\*\s*[-–—]\s*.+/gm, // Bullet with bold + explanation
    /^\s*\d+\.\s+\*\*[^*]+\*\*/gm, // Numbered with bold
  ];
  let exampleCount = 0;
  for (const pattern of examplePatterns) {
    exampleCount += (content.match(pattern) || []).length;
  }

  // Also count example sentences in tables
  const tableExamples = content.match(/\|\s*[А-Яа-яЇїІіЄєҐґ'].+\s*\|\s*[A-Za-z].+\s*\|/g) || [];
  exampleCount += Math.min(tableExamples.length, 10); // Cap table examples

  // QUALITY targets - examples are key to learning
  const minExamples: Record<string, number> = {
    'A1': 12,   // Beginners need lots of examples
    'A2': 15,   // More variety and context
    'A2+': 18,  // Rich example coverage
    'B1': 22,   // Complex grammar needs many illustrations
    'B1+': 24,  // Continued example depth
    'B2': 26,   // Advanced structures well-illustrated
    'B2+': 28,  // Historical/cultural examples
    'C1': 30,   // Academic-level illustration
  };
  const reqExamples = minExamples[level] || 10;
  if (exampleCount < reqExamples) {
    issues.push({
      type: 'warning',
      category: 'content-quality',
      message: `Low example count: ~${exampleCount} examples (${level} should have ${reqExamples}+)`,
    });
  }

  // Check for common mistakes section (Типові помилки)
  const hasCommonMistakes = !!content.match(/(?:common mistake|типов[іа] помилк|avoid|уникай)/i);
  if (!hasCommonMistakes && ['B1', 'B2', 'C1'].includes(level)) {
    issues.push({
      type: 'info',
      category: 'content-quality',
      message: 'No common mistakes section (Типові помилки) - recommended for B1+',
    });
  }

  // Check for cultural context
  const hasCulturalContent = !!content.match(/(?:культур|tradition|традиц|custom|звичай|Ukraine|Україн|history|історі)/i);
  if (!hasCulturalContent && !isCheckpoint) {
    issues.push({
      type: 'info',
      category: 'content-quality',
      message: 'No cultural context detected - consider adding Ukrainian culture references',
    });
  }

  // ==========================================================================
  // 13. NARRATIVE RICHNESS & ANTI-PATTERNS
  // ==========================================================================

  // Narrative richness is measured by QUALITY indicators, not just prose ratio.
  // A good module has: engagement boxes, explanatory prose, context, examples.
  // Tables are pedagogically appropriate - we don't penalize them.

  // Level-specific narrative expectations:
  // A1: More English explanation, less narrative depth expected
  // A2: Transitional - more context expected
  // B1+: Rich narrative, mostly Ukrainian prose

  // QUALITY targets for narrative richness
  // Engagement boxes, prose explanations, and examples drive learning
  const narrativeRequirements: Record<string, {
    minEngagementBoxes: number;
    minProseLines: number;  // Lines >30 chars that explain/contextualize
    minExamples: number;    // Example sentences (Ukrainian + translation)
  }> = {
    'A1': { minEngagementBoxes: 3, minProseLines: 12, minExamples: 6 },   // Rich scaffolding for beginners
    'A2': { minEngagementBoxes: 3, minProseLines: 15, minExamples: 8 },   // More context building
    'A2+': { minEngagementBoxes: 4, minProseLines: 18, minExamples: 8 },  // Deeper explanations
    'B1': { minEngagementBoxes: 4, minProseLines: 22, minExamples: 10 },  // Substantial narrative
    'B1+': { minEngagementBoxes: 4, minProseLines: 25, minExamples: 10 }, // Rich cultural/authentic content
    'B2': { minEngagementBoxes: 4, minProseLines: 28, minExamples: 10 },  // Advanced explanations
    'B2+': { minEngagementBoxes: 5, minProseLines: 32, minExamples: 12 }, // Historical depth
    'C1': { minEngagementBoxes: 4, minProseLines: 35, minExamples: 12 },  // Academic richness
  };

  const narrativeReq = narrativeRequirements[level];

  // Count prose lines: explanatory text (not tables, headers, or activity items)
  const proseLines = mainContent.split('\n').filter(line => {
    const trimmed = line.trim();
    return trimmed.length > 30 &&
      !trimmed.startsWith('|') &&
      !trimmed.startsWith('-') &&
      !trimmed.startsWith('>') &&
      !trimmed.startsWith('#') &&
      !trimmed.match(/^\d+\./) &&
      !trimmed.match(/^\[/) &&       // Not markdown links/images
      !trimmed.match(/^---/) &&      // Not dividers
      !trimmed.match(/^```/);        // Not code blocks
  });

  // Count example sentences (Ukrainian text with English in parentheses or after —)
  const examples = mainContent.match(/[\u0400-\u04FF].{5,}(?:\(|—|–).{3,}/g) || [];

  // Check narrative richness
  if (narrativeReq && !isCheckpoint) {
    const narrativeScore = {
      engagementBoxes: engagementBoxes,
      proseLines: proseLines.length,
      examples: examples.length,
    };

    // Calculate deficiency
    const deficiencies: string[] = [];

    if (narrativeScore.engagementBoxes < narrativeReq.minEngagementBoxes) {
      deficiencies.push(`engagement boxes: ${narrativeScore.engagementBoxes}/${narrativeReq.minEngagementBoxes}`);
    }
    if (narrativeScore.proseLines < narrativeReq.minProseLines) {
      deficiencies.push(`explanatory prose: ${narrativeScore.proseLines}/${narrativeReq.minProseLines} lines`);
    }
    if (narrativeScore.examples < narrativeReq.minExamples) {
      deficiencies.push(`examples: ${narrativeScore.examples}/${narrativeReq.minExamples}`);
    }

    if (deficiencies.length >= 2) {
      issues.push({
        type: 'warning',
        category: 'narrative',
        message: `Low narrative richness (${deficiencies.join(', ')})`,
      });
    } else if (deficiencies.length === 1) {
      issues.push({
        type: 'info',
        category: 'narrative',
        message: `Could improve: ${deficiencies[0]}`,
      });
    }
  }

  // ==========================================================================
  // 14. IMMERSION LEVEL CHECK (Ukrainian vs English percentage)
  // ==========================================================================

  // Immersion measures overall language balance in the module content.
  // INCLUDES tables (vocabulary tables are learning content).
  // EXCLUDES: markdown syntax, frontmatter, code blocks, pure punctuation.

  // Level-specific immersion targets with WIDER tolerance for lower levels:
  // A1: 30% ±15% (lots of English explanation is fine)
  // A2: 40% ±15%
  // A2+: 50% ±12%
  // B1: 60% ±10%
  // B2: 85% ±10%
  // C1: 95% ±5%

  // Checkpoint modules have HIGHER immersion targets (they test learned material)
  // They contain dialogue tables, testimonies, and character narratives - naturally more Ukrainian
  const immersionConfig: Record<string, { target: number; tolerance: number }> = isCheckpoint ? {
    'A1': { target: 0.55, tolerance: 0.25 },   // Checkpoints: 55% ±25% (30%-80%)
    'A2': { target: 0.55, tolerance: 0.20 },   // 35%-75%
    'A2+': { target: 0.60, tolerance: 0.18 },  // 42%-78%
    'B1': { target: 0.70, tolerance: 0.15 },   // 55%-85%
    'B1+': { target: 0.80, tolerance: 0.12 },  // 68%-92%
    'B2': { target: 0.90, tolerance: 0.08 },   // 82%-98%
    'B2+': { target: 0.92, tolerance: 0.06 },  // 86%-98%
    'C1': { target: 0.95, tolerance: 0.05 },   // 90%-100%
  } : {
    'A1': { target: 0.30, tolerance: 0.15 },   // Regular modules: 30% ±15%
    'A2': { target: 0.40, tolerance: 0.15 },
    'A2+': { target: 0.50, tolerance: 0.12 },
    'B1': { target: 0.60, tolerance: 0.10 },
    'B1+': { target: 0.70, tolerance: 0.10 },
    'B2': { target: 0.85, tolerance: 0.10 },
    'B2+': { target: 0.90, tolerance: 0.08 },
    'C1': { target: 0.95, tolerance: 0.05 },
  };

  // Clean text for immersion analysis
  const textForImmersion = mainContent
    .replace(/```[\s\S]*?```/g, '')     // Remove code blocks
    .replace(/[#*_`\[\](){}|<>\-]/g, '') // Remove markdown syntax
    .replace(/\d+/g, '');               // Remove numbers

  const cyrillicChars = (textForImmersion.match(/[\u0400-\u04FF]/g) || []).length;
  const latinChars = (textForImmersion.match(/[a-zA-Z]/g) || []).length;
  const totalChars = cyrillicChars + latinChars;

  const immersionReq = immersionConfig[level];

  if (totalChars > 200 && immersionReq) {
    // Exception: Modules 1-3 are alphabet-teaching modules where low Ukrainian % is expected
    // These modules need extensive English explanations for Cyrillic letters
    const isAlphabetModule = moduleNum >= 1 && moduleNum <= 3;

    if (!isAlphabetModule) {
      const actualImmersion = cyrillicChars / totalChars;
      const targetImmersion = immersionReq.target;
      const tolerance = immersionReq.tolerance;
      const deviation = actualImmersion - targetImmersion;

      if (Math.abs(deviation) > tolerance) {
        const actualPercent = Math.round(actualImmersion * 100);
        const targetPercent = Math.round(targetImmersion * 100);
        const tolerancePercent = Math.round(tolerance * 100);
        const direction = deviation > 0 ? 'too much Ukrainian' : 'too much English';

        issues.push({
          type: 'warning',
          category: 'immersion',
          message: `Immersion imbalance: ${actualPercent}% Ukrainian (target: ${targetPercent}% ±${tolerancePercent}%) - ${direction}`,
        });
      }
    }
  }

  // Check for text walls (sections with no breaks)
  const sections = mainContent.split(/^#+ /m);
  for (const section of sections) {
    const sectionLines = section.split('\n').filter(l => l.trim().length > 0);
    const consecutiveTextLines = sectionLines.filter(l =>
      !l.startsWith('|') && !l.startsWith('-') && !l.startsWith('>') && !l.match(/^\d+\./)
    );

    // Check for 15+ consecutive lines without visual break
    let maxConsecutive = 0;
    let current = 0;
    for (const line of sectionLines) {
      if (line.startsWith('|') || line.startsWith('-') || line.startsWith('>') || line.match(/^#+\s/) || line.match(/^\d+\./)) {
        maxConsecutive = Math.max(maxConsecutive, current);
        current = 0;
      } else if (line.trim().length > 30) {
        current++;
      }
    }
    maxConsecutive = Math.max(maxConsecutive, current);

    if (maxConsecutive > 15) {
      issues.push({
        type: 'info',
        category: 'narrative',
        message: `Text wall detected: ${maxConsecutive} consecutive lines without visual break`,
      });
      break; // Only report once
    }
  }

  // Check for real-world/authentic content markers
  const hasAuthenticContent = !!content.match(/(?:real|authentic|actual|справжн|реальн|new article|стаття|news|новин|menu|меню|sign|вивіска)/i);
  const mentionsMedia = !!content.match(/(?:video|відео|audio|аудіо|song|пісня|podcast|film|фільм)/i);

  if (!hasAuthenticContent && !mentionsMedia && ['B1', 'B2', 'C1'].includes(level)) {
    issues.push({
      type: 'info',
      category: 'content-quality',
      message: 'No authentic materials detected (real texts, media) - recommended for B1+',
    });
  }

  // ==========================================================================
  // 14. SENTENCE COMPLEXITY ANALYSIS
  // ==========================================================================

  // Check sentence length in activities matches level
  // QUALITY targets for sentence complexity in activities
  // These are word counts for ACTIVITY sentences (fill-in, unjumble)
  // Real lesson content should have natural sentence lengths
  const sentenceComplexity: Record<string, { min: number; max: number }> = {
    'A1': { min: 5, max: 8 },     // "Моя мама працює в лікарні" (5) - not trivial!
    'A2': { min: 6, max: 10 },    // Compound with connectors, prepositions
    'A2+': { min: 8, max: 12 },   // Subordinate clauses, complex structures
    'B1': { min: 10, max: 15 },   // Complex sentences, conditionals, aspect
    'B1+': { min: 11, max: 16 },  // Participles, extended complexity
    'B2': { min: 12, max: 18 },   // Sophisticated structures, passive
    'B2+': { min: 13, max: 19 },  // Advanced stylistic variation
    'C1': { min: 14, max: 22 },   // Advanced academic/literary
  };

  const levelComplexity = sentenceComplexity[level];
  if (levelComplexity) {
    // Sample sentences from fill-in and unjumble activities
    const activitySentences: string[] = [];

    // Get fill-in sentences
    const fillInMatches = content.matchAll(/^\d+\.\s+([^_\n]+___[^\n]+)/gm);
    for (const match of fillInMatches) {
      activitySentences.push(match[1]);
    }

    // Get unjumble jumbled words (count the words)
    const unjumbleMatches = content.matchAll(/^\d+\.\s+([^/\n]+(?:\/[^/\n]+)+)/gm);
    for (const match of unjumbleMatches) {
      activitySentences.push(match[1]);
    }

    if (activitySentences.length >= 3) {
      const wordCounts = activitySentences.map(s =>
        s.split(/[\s/]+/).filter(w => w.length > 0 && !w.match(/^[_]+$/)).length
      );
      const avgWords = Math.round(wordCounts.reduce((a, b) => a + b, 0) / wordCounts.length);

      if (avgWords < levelComplexity.min - 2) {
        issues.push({
          type: 'warning',
          category: 'complexity',
          message: `Activity sentences too simple: avg ${avgWords} words (${level} target: ${levelComplexity.min}-${levelComplexity.max})`,
        });
      } else if (avgWords > levelComplexity.max + 3) {
        issues.push({
          type: 'warning',
          category: 'complexity',
          message: `Activity sentences too complex: avg ${avgWords} words (${level} target: ${levelComplexity.min}-${levelComplexity.max})`,
        });
      }
    }
  }

  // ==========================================================================
  // 15. SELF-ASSESSMENT & LEARNING AIDS
  // ==========================================================================

  // Check for self-assessment or checklist
  const hasSelfAssessment = !!content.match(/(?:self-assessment|checklist|I can now|Тепер я вмію|можу|check yourself|перевір себе)/i);
  if (!hasSelfAssessment && !isCheckpoint && ['B1', 'B2', 'C1'].includes(level)) {
    issues.push({
      type: 'info',
      category: 'content-quality',
      message: 'No self-assessment checklist - recommended for B1+ modules',
    });
  }

  // Check for grammar tables (expected in grammar modules)
  const isGrammarModule = frontmatter.match(/tags:.*grammar/i) || title.toLowerCase().includes('grammar') ||
                          title.match(/case|відмін|verb|дієсл|aspect|вид/i);
  const hasGrammarTable = content.match(/\|[^|]+\|[^|]+\|[^|]+\|/) &&
                          (content.match(/\|\s*(?:Form|Форма|Case|Відмінок|Singular|Однина|Person|Особа)/i));

  if (isGrammarModule && !hasGrammarTable) {
    issues.push({
      type: 'warning',
      category: 'content-quality',
      message: 'Grammar module lacks conjugation/declension tables',
    });
  }

  return {
    module: moduleNum,
    title,
    level,
    issues,
    stats: {
      activities: activityCount,
      activityTypes,
      vocabCount,
      hasVocabSection,
      hasSummary,
      wordCount,
      engagementBoxes,
      itemsPerActivity,
      vocabDuplicates,
    },
  };
}

// =============================================================================
// Fix Prompt Generator
// =============================================================================

function generateFixPrompt(audit: ModuleAudit): string {
  const errors = audit.issues.filter(i => i.type === 'error');
  const warnings = audit.issues.filter(i => i.type === 'warning');

  // Group issues by category for clearer instructions
  const issuesByCategory: Record<string, Issue[]> = {};
  for (const issue of [...errors, ...warnings]) {
    if (!issuesByCategory[issue.category]) {
      issuesByCategory[issue.category] = [];
    }
    issuesByCategory[issue.category].push(issue);
  }

  // Level-specific QUALITY TARGETS (based on Ukrainian State Standard September 2024)
  // These are ambitious goals - good modules should meet or exceed them
  const levelReqs: Record<string, string> = {
    'A1': 'Activities: 8+, 12 items each | Vocab: 18-25 | Sentences: 5-8 words | Content: 600+ words | Examples: 12+',
    'A2': 'Activities: 10+, 12 items each | Vocab: 22-30 | Sentences: 6-10 words | Content: 700+ words | Examples: 15+',
    'A2+': 'Activities: 12+, 15 items each | Vocab: 35-45 | Sentences: 8-12 words | Content: 800+ words | Examples: 18+',
    'B1': 'Activities: 14+, 20 items each | Vocab: 28-35 | Sentences: 10-15 words | Content: 900+ words | Examples: 22+',
    'B1+': 'Activities: 14+, 20 items each | Vocab: 28-35 | Sentences: 11-16 words | Content: 950+ words | Examples: 24+',
    'B2': 'Activities: 16+, 22 items each | Vocab: 30-40 | Sentences: 12-18 words | Content: 1000+ words | Examples: 26+',
    'B2+': 'Activities: 16+, 22 items each | Vocab: 30-40 | Sentences: 13-19 words | Content: 1050+ words | Examples: 28+',
    'C1': 'Activities: 16+, 24 items each | Vocab: 35-45 | Sentences: 14-22 words | Content: 1100+ words | Examples: 30+',
  };

  // Build the fix prompt
  const lines: string[] = [];
  lines.push(`Review and fix module ${audit.module} (${audit.title}, ${audit.level}).`);
  lines.push('');
  lines.push(`**${audit.level} Requirements:** ${levelReqs[audit.level] || 'See guidelines'}`);
  lines.push('');

  // Priority 1: Broken formats (must fix)
  if (issuesByCategory['broken-format'] || issuesByCategory['broken-activity']) {
    lines.push('## 🔴 FIX BROKEN FORMATS:');
    for (const issue of [...(issuesByCategory['broken-format'] || []), ...(issuesByCategory['broken-activity'] || [])]) {
      lines.push(`- ${issue.message}`);
    }
    lines.push('');
  }

  // Priority 1b: Vocabulary duplicates (cascade fix)
  if (issuesByCategory['vocab-duplicate']) {
    lines.push('## 🔴 REMOVE DUPLICATE VOCABULARY:');
    lines.push('The following words were already introduced in earlier modules. Remove them from this module\'s Vocabulary section:');
    for (const dup of audit.stats.vocabDuplicates) {
      lines.push(`- ${dup}`);
    }
    lines.push('');
    lines.push('After removing, run `npm run vocab:build` to rebuild the vocabulary database.');
    lines.push('');
  }

  // Priority 2: Requirements (activity count, vocab)
  if (issuesByCategory['requirements']) {
    lines.push('## 🟡 MEET REQUIREMENTS:');
    const reqIssues = issuesByCategory['requirements'];

    // Activity count
    const activityIssue = reqIssues.find(i => i.message.includes('activities'));
    if (activityIssue) {
      const match = activityIssue.message.match(/Only (\d+) activities.*requires (\d+)/);
      if (match) {
        const current = parseInt(match[1]);
        const required = parseInt(match[2]);
        lines.push(`- Add ${required - current} more activities (currently ${current}, need ${required})`);
        lines.push(`  Priority order: quiz → match-up → group-sort → true-false → fill-in → unjumble`);
      }
    }

    // Vocab count
    const vocabIssue = reqIssues.find(i => i.message.includes('vocab'));
    if (vocabIssue) {
      lines.push(`- ${vocabIssue.message}`);
    }

    // Item counts
    const itemIssues = reqIssues.filter(i => i.message.includes('items'));
    if (itemIssues.length > 0) {
      const target = itemIssues[0].message.match(/target: (\d+)/)?.[1] || '?';
      lines.push(`- Expand activities to ${target} items each`);
    }
    lines.push('');
  }

  // Priority 3: Enrichment
  if (issuesByCategory['enrichment']) {
    lines.push('## 🟡 ADD ENRICHMENT:');
    for (const issue of issuesByCategory['enrichment']) {
      if (issue.message.includes('engagement boxes')) {
        lines.push('- Add 2+ engagement boxes: 💡 Did You Know, ⚡ Pro Tip, 🎭 Culture Corner, 📜 History Bite');
      } else {
        lines.push(`- ${issue.message}`);
      }
    }
    lines.push('');
  }

  // Priority 4: Content quality
  if (issuesByCategory['content-quality']) {
    lines.push('## 🟡 IMPROVE CONTENT:');
    for (const issue of issuesByCategory['content-quality']) {
      if (issue.message.includes('example count')) {
        lines.push('- Add more examples with Ukrainian + English translations');
      } else if (issue.message.includes('PPP')) {
        lines.push('- Add lesson structure: ## warm-up, ## presentation, ## practice, ## production');
      } else if (issue.message.includes('Grammar module lacks')) {
        lines.push('- Add conjugation/declension tables for grammar forms');
      } else {
        lines.push(`- ${issue.message}`);
      }
    }
    lines.push('');
  }

  // Priority 5: Narrative
  if (issuesByCategory['narrative']) {
    lines.push('## 🟡 ENRICH NARRATIVE:');
    for (const issue of issuesByCategory['narrative']) {
      if (issue.message.includes('Dry narration')) {
        lines.push('- Add explanatory prose between tables/lists - explain WHY, not just WHAT');
        lines.push('- Include real-world usage examples and context');
      } else {
        lines.push(`- ${issue.message}`);
      }
    }
    lines.push('');
  }

  // Priority 6: Complexity
  if (issuesByCategory['complexity']) {
    lines.push('## 🟡 ADJUST COMPLEXITY:');
    for (const issue of issuesByCategory['complexity']) {
      lines.push(`- ${issue.message}`);
    }
    lines.push('');
  }

  // Priority 7: Checkpoint requirements
  if (issuesByCategory['checkpoint']) {
    lines.push('## 🟡 CHECKPOINT REQUIREMENTS:');
    for (const issue of issuesByCategory['checkpoint']) {
      if (issue.message.includes('named character')) {
        lines.push('- Add named character: "Name, age, nationality, city" (e.g., "Ліам, 26, Irish, Dublin")');
      } else if (issue.message.includes('dialogue tables')) {
        lines.push('- Add dialogue table: | Speaker | Ukrainian | English |');
      } else if (issue.message.includes('testimonies')) {
        lines.push('- Add 3-4 learner testimonies with names and quotes');
      } else {
        lines.push(`- ${issue.message}`);
      }
    }
    lines.push('');
  }

  // Add quality review checklist
  lines.push('## ✅ ALSO REVIEW:');
  lines.push('- Grammar/spelling accuracy in Ukrainian');
  lines.push('- Natural, useful examples (not textbook-dry)');
  lines.push('- Cultural accuracy and sensitivity');
  lines.push('- Activity answers are correct');
  lines.push('- Engagement boxes are interesting/memorable');
  lines.push('');

  // Add regeneration reminder
  lines.push('After fixing, regenerate: `npx ts-node scripts/generate.ts l2-uk-en ' + audit.module + '`');

  return lines.join('\n');
}

// =============================================================================
// Main
// =============================================================================

function main() {
  const args = process.argv.slice(2);

  // Check for --fix flag
  const fixMode = args.includes('--fix');
  const filteredArgs = args.filter(a => !a.startsWith('--'));

  const lang = filteredArgs[0] || 'l2-uk-en';
  const rangeArg = filteredArgs[1];

  const curriculumDir = path.join(process.cwd(), 'curriculum', lang);
  const modulesDir = path.join(curriculumDir, 'modules');

  if (!fs.existsSync(modulesDir)) {
    console.error(`Directory not found: ${modulesDir}`);
    process.exit(1);
  }

  // Initialize vocabulary database for duplicate detection
  const vocabDbPath = path.join(curriculumDir, 'vocabulary.db');
  let vocabDb: VocabDatabase | undefined;
  if (fs.existsSync(vocabDbPath)) {
    resetVocabDatabase();
    vocabDb = getVocabDatabase(curriculumDir);
    console.log(`📚 Vocabulary database loaded for duplicate detection`);
  } else {
    console.log(`⚠️  No vocabulary.db found - skipping vocab duplicate check`);
  }

  // Parse range
  let minModule = 1;
  let maxModule = 999;
  if (rangeArg) {
    if (rangeArg.includes('-')) {
      const [min, max] = rangeArg.split('-').map(Number);
      minModule = min;
      maxModule = max;
    } else {
      minModule = maxModule = parseInt(rangeArg);
    }
  }

  // Find module files
  const files = fs.readdirSync(modulesDir)
    .filter(f => f.match(/^module-\d+\.md$/))
    .map(f => ({
      path: path.join(modulesDir, f),
      num: parseInt(f.match(/module-(\d+)/)?.[1] || '0'),
    }))
    .filter(f => f.num >= minModule && f.num <= maxModule)
    .sort((a, b) => a.num - b.num);

  console.log(`\n🔍 Module Audit: ${lang} (modules ${minModule}-${maxModule})\n`);
  console.log('='.repeat(70));

  let totalErrors = 0;
  let totalWarnings = 0;
  let totalInfo = 0;
  const problemModules: ModuleAudit[] = [];

  for (const file of files) {
    const audit = auditModule(file.path, vocabDb);

    const errors = audit.issues.filter(i => i.type === 'error').length;
    const warnings = audit.issues.filter(i => i.type === 'warning').length;
    const infos = audit.issues.filter(i => i.type === 'info').length;

    totalErrors += errors;
    totalWarnings += warnings;
    totalInfo += infos;

    if (audit.issues.length > 0) {
      problemModules.push(audit);
    }
  }

  // Print results grouped by category
  const categories = [
    'broken-format',
    'broken-activity',
    'vocab-duplicate',  // Vocab cascade detection
    'checkpoint',
    'requirements',
    'missing-content',
    'incomplete',
    'enrichment',
    'content-quality',
    'narrative',
    'immersion',
    'activity-order',
    'complexity',
  ];

  for (const category of categories) {
    const modulesWithCategory = problemModules.filter(m =>
      m.issues.some(i => i.category === category)
    );

    if (modulesWithCategory.length === 0) continue;

    console.log(`\n📋 ${category.toUpperCase()}`);
    console.log('-'.repeat(70));

    for (const audit of modulesWithCategory) {
      const categoryIssues = audit.issues.filter(i => i.category === category);
      if (categoryIssues.length === 0) continue;

      console.log(`\n  Module ${audit.module}: ${audit.title} (${audit.level})`);
      for (const issue of categoryIssues) {
        const icon = issue.type === 'error' ? '❌' : issue.type === 'warning' ? '⚠️' : 'ℹ️';
        const lineInfo = issue.line ? `:${issue.line}` : '';
        console.log(`    ${icon} ${issue.message}${lineInfo}`);
        if (issue.context) {
          console.log(`       → ${issue.context}`);
        }
      }
    }
  }

  // Summary
  console.log('\n' + '='.repeat(70));
  console.log('\n📊 SUMMARY\n');
  console.log(`  Modules scanned: ${files.length}`);
  console.log(`  Modules with issues: ${problemModules.length}`);
  console.log(`  ❌ Errors: ${totalErrors}`);
  console.log(`  ⚠️  Warnings: ${totalWarnings}`);
  console.log(`  ℹ️  Info: ${totalInfo}`);

  // Stats by level
  const byLevel: Record<string, { total: number; withIssues: number }> = {};
  for (const file of files) {
    const audit = problemModules.find(p => p.module === file.num);
    const level = audit?.level || 'Unknown';
    if (!byLevel[level]) byLevel[level] = { total: 0, withIssues: 0 };
    byLevel[level].total++;
    if (audit) byLevel[level].withIssues++;
  }

  console.log('\n  By Level:');
  for (const [level, stats] of Object.entries(byLevel)) {
    console.log(`    ${level}: ${stats.withIssues}/${stats.total} with issues`);
  }

  // List clean modules
  const cleanModules = files.filter(f =>
    !problemModules.some(p => p.module === f.num)
  );
  if (cleanModules.length > 0 && cleanModules.length <= 30) {
    console.log(`\n  ✅ Clean modules: ${cleanModules.map(f => f.num).join(', ')}`);
  } else if (cleanModules.length > 30) {
    console.log(`\n  ✅ Clean modules: ${cleanModules.length} modules have no issues`);
  }

  // Fix mode: generate prompts for each module
  if (fixMode && problemModules.length > 0) {
    // Sort by severity (most issues first)
    const sorted = [...problemModules].sort((a, b) => {
      const aErrors = a.issues.filter(i => i.type === 'error').length;
      const bErrors = b.issues.filter(i => i.type === 'error').length;
      const aWarnings = a.issues.filter(i => i.type === 'warning').length;
      const bWarnings = b.issues.filter(i => i.type === 'warning').length;
      if (aErrors !== bErrors) return bErrors - aErrors;
      return bWarnings - aWarnings;
    });

    console.log('\n' + '='.repeat(70));
    console.log('\n🔧 FIX MODE - Prompts for each module:\n');

    for (let i = 0; i < sorted.length; i++) {
      const audit = sorted[i];
      const errCount = audit.issues.filter(i => i.type === 'error').length;
      const warnCount = audit.issues.filter(i => i.type === 'warning').length;

      console.log('─'.repeat(70));
      console.log(`\n📝 [${i + 1}/${sorted.length}] Module ${audit.module} (${errCount} errors, ${warnCount} warnings)\n`);
      console.log(generateFixPrompt(audit));
      console.log('');
    }

    // Also output a summary prompt for batch fixing
    console.log('─'.repeat(70));
    console.log('\n📋 QUICK COPY - Module numbers to fix (priority order):\n');
    console.log(sorted.map(a => a.module).join(', '));
    console.log('');
  }

  // Exit code
  if (totalErrors > 0) {
    process.exit(1);
  }
}

main();
