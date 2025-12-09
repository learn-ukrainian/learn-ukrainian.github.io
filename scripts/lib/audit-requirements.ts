/**
 * Audit Requirements Configuration
 *
 * Quality targets for module auditing. These are aspirational goals
 * that define what a "rich" module should have at each level.
 *
 * Separate from grammar constraints (which come from curriculum plans).
 */

export interface LevelRequirements {
  // Activity requirements
  activityCount: number;           // Minimum number of activities
  itemsPerActivity: number;        // Target items per activity
  fillInWords: [number, number];   // Word count range for fill-in sentences
  unjumbleWords: [number, number]; // Word count range for unjumble sentences

  // Vocabulary requirements
  newWordsMin: number;             // Minimum new vocab words
  newWordsMax: number;             // Maximum new vocab words (before suggesting split)

  // Content requirements
  minWordCount: number;            // Minimum words in explanatory content
  engagementBoxes: number;         // Minimum engagement boxes (💡, ⚡, etc.)

  // Immersion
  immersionLevel: number;          // Target Ukrainian % (0.0 - 1.0)

  // Transliteration (for Ukrainian)
  transliterationMode: 'full' | 'partial' | 'first-only' | 'none';
}

/**
 * Level requirements based on CEFR and MODULE-RICHNESS-GUIDELINES.md
 */
export const LEVEL_REQUIREMENTS: Record<string, LevelRequirements> = {
  'A1': {
    activityCount: 8,
    itemsPerActivity: 12,
    fillInWords: [5, 8],
    unjumbleWords: [5, 8],
    newWordsMin: 18,
    newWordsMax: 30, // Increased to match Guidelines
    minWordCount: 750, // Increased from 600 to match Guidelines
    engagementBoxes: 3, // Increased to 3
    immersionLevel: 0.30, // Note: Overridden by module-audit.ts for M01-M15
    transliterationMode: 'full',
  },
  'A2': {
    activityCount: 10,
    itemsPerActivity: 12,
    fillInWords: [6, 10],
    unjumbleWords: [6, 10],
    newWordsMin: 22,
    newWordsMax: 35, // Increased
    minWordCount: 1000, // Increased from 700 to match Guidelines
    engagementBoxes: 4, // Increased
    immersionLevel: 0.40,
    transliterationMode: 'partial',
  },
  'A2+': {
    activityCount: 12,
    itemsPerActivity: 15,
    fillInWords: [8, 12],
    unjumbleWords: [8, 12],
    newWordsMin: 35,
    newWordsMax: 45,
    minWordCount: 800,
    engagementBoxes: 2,
    immersionLevel: 0.50,
    transliterationMode: 'first-only',  // First occurrence only
  },
  'B1': {
    activityCount: 14,
    itemsPerActivity: 20,
    fillInWords: [10, 15],
    unjumbleWords: [10, 15],
    newWordsMin: 28,
    newWordsMax: 35,
    minWordCount: 900,
    engagementBoxes: 2,
    immersionLevel: 0.60,
    transliterationMode: 'none',
  },
  'B1+': {
    activityCount: 14,
    itemsPerActivity: 20,
    fillInWords: [11, 16],
    unjumbleWords: [11, 16],
    newWordsMin: 28,
    newWordsMax: 35,
    minWordCount: 950,
    engagementBoxes: 2,
    immersionLevel: 0.70,
    transliterationMode: 'none',
  },
  'B2': {
    activityCount: 16,
    itemsPerActivity: 22,
    fillInWords: [12, 18],
    unjumbleWords: [12, 18],
    newWordsMin: 30,
    newWordsMax: 40,
    minWordCount: 1000,
    engagementBoxes: 2,
    immersionLevel: 0.85,
    transliterationMode: 'none',
  },
  'B2+': {
    activityCount: 16,
    itemsPerActivity: 22,
    fillInWords: [13, 19],
    unjumbleWords: [13, 19],
    newWordsMin: 30,
    newWordsMax: 40,
    minWordCount: 1050,
    engagementBoxes: 2,
    immersionLevel: 0.90,
    transliterationMode: 'none',
  },
  'C1': {
    activityCount: 16,
    itemsPerActivity: 24,
    fillInWords: [14, 22],
    unjumbleWords: [14, 22],
    newWordsMin: 35,
    newWordsMax: 45,
    minWordCount: 1100,
    engagementBoxes: 2,
    immersionLevel: 0.95,
    transliterationMode: 'none',
  },
  'C2': {
    activityCount: 16,
    itemsPerActivity: 24,
    fillInWords: [15, 24],
    unjumbleWords: [15, 24],
    newWordsMin: 35,
    newWordsMax: 45,
    minWordCount: 1200,
    engagementBoxes: 2,
    immersionLevel: 0.98,
    transliterationMode: 'none',
  },
};

/**
 * Engagement box patterns to detect in content
 */
export const ENGAGEMENT_PATTERNS = [
  />\s*💡\s*\*\*(?:Did You Know|Чи знали ви)/g,
  />\s*⚡\s*\*\*(?:Pro Tip|Порада)/g,
  />\s*📜\s*\*\*(?:History Bite|Історична довідка)/g,
  />\s*🎭\s*\*\*(?:Culture Corner|Культурний куточок)/g,
  />\s*🔍\s*\*\*(?:Myth Buster|Руйнуємо міфи)/g,
  />\s*🎯\s*\*\*(?:Fun Fact|Цікавий факт)/g,
  />\s*🔗\s*\*\*(?:Language Link|Мовний зв'язок)/g,
  />\s*🌍\s*\*\*(?:Real World|Реальний світ)/g,
  />\s*🎬\s*\*\*(?:Pop Culture|Поп-культура)/g,
];

/**
 * Activity types and their priority order
 */
export const ACTIVITY_PRIORITY: Record<string, number> = {
  'quiz': 1,
  'match-up': 2,
  'group-sort': 3,
  'true-false': 4,
  'select': 5,
  'anagram': 6,
  'fill-in': 7,
  'unjumble': 8,
  'translate': 9,
};

/**
 * Get requirements for a level, with fallback to closest match
 */
export function getRequirements(level: string): LevelRequirements {
  // Direct match
  if (LEVEL_REQUIREMENTS[level]) {
    return LEVEL_REQUIREMENTS[level];
  }

  // Handle sub-levels by falling back to parent
  const baseLevel = level.replace('+', '');
  if (LEVEL_REQUIREMENTS[baseLevel]) {
    return LEVEL_REQUIREMENTS[baseLevel];
  }

  // Default to B1 if unknown
  console.warn(`Unknown level "${level}", using B1 defaults`);
  return LEVEL_REQUIREMENTS['B1'];
}

/**
 * Immersion tolerance (±10%)
 */
export const IMMERSION_TOLERANCE = 0.10;
