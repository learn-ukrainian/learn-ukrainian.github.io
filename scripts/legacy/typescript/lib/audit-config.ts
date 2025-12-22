/**
 * Audit Configuration Types and Parser
 *
 * Extracts audit requirements from curriculum plan markdown files.
 * Source of truth: docs/l2-uk-en/*-CURRICULUM-PLAN.md
 *
 * Module numbering:
 * - Curriculum files use LEVEL-INTERNAL numbers: a2/01-xxx.md, b1/01-xxx.md
 * - Grammar requirements in plans use level-internal numbers
 * - This config uses level-internal numbers throughout
 */

export interface GrammarRequirement {
  feature: string;           // e.g., "Accusative", "Adjectives"
  allowedFromModule: number | null;  // null = not allowed at this level (level-internal number)
  notes?: string;
}

export interface LevelConfig {
  level: string;             // A1, A2, B1, B2, C1, C2
  moduleCount: number;       // number of modules at this level
  vocabularyTarget: number;  // new words for this level
  cumulativeVocab: number;   // total words by end of level
  immersionLevel: number;    // 0.0-1.0
  grammarRequirements: GrammarRequirement[];
  checkpointInterval: number; // every N modules
}

export interface AuditConfig {
  languagePair: string;      // e.g., "l2-uk-en"
  levels: Record<string, LevelConfig>;
}

/**
 * Level directory names in the curriculum
 */
export const LEVEL_DIRS: Record<string, string> = {
  'A1': 'a1',
  'A2': 'a2',
  'A2+': 'a2-plus',
  'B1': 'b1',
  'B1+': 'b1-plus',
  'B2': 'b2',
  'C1': 'c1',
  'C2': 'c2'
};

/**
 * Get the level directory for a given CEFR level
 */
export function getLevelDir(level: string): string {
  return LEVEL_DIRS[level] || level.toLowerCase();
}

/**
 * Parse module count from header line like "**Modules:** 01-30 (30 modules)"
 */
function parseModuleCount(content: string): number {
  // Try to extract count from parentheses: "(30 modules)"
  const countMatch = content.match(/\((\d+)\s*modules?\)/i);
  if (countMatch) {
    return parseInt(countMatch[1], 10);
  }

  // Fallback: parse range and compute count
  const rangeMatch = content.match(/\*\*Modules:\*\*\s*(\d+)-(\d+)/);
  if (rangeMatch) {
    const start = parseInt(rangeMatch[1], 10);
    const end = parseInt(rangeMatch[2], 10);
    return end - start + 1;
  }
  return 30; // Default
}

/**
 * Parse vocabulary target from lines like:
 * "**Vocabulary Target:** ~750 words"
 * "**Vocabulary Target:** ~1,050 words (level), ~1,800 cumulative"
 */
function parseVocabularyTargets(content: string): { level: number; cumulative: number } {
  // Try format with "level" and "cumulative"
  const fullMatch = content.match(/\*\*Vocabulary Target:\*\*\s*~?([\d,]+)\s*words?\s*\(level\)[,\s]*~?([\d,]+)\s*cumulative/i);
  if (fullMatch) {
    return {
      level: parseInt(fullMatch[1].replace(/,/g, ''), 10),
      cumulative: parseInt(fullMatch[2].replace(/,/g, ''), 10)
    };
  }

  // Try simpler format "~750 words"
  const simpleMatch = content.match(/\*\*Vocabulary Target:\*\*\s*~?([\d,]+)\s*words?/i);
  if (simpleMatch) {
    const level = parseInt(simpleMatch[1].replace(/,/g, ''), 10);
    return { level, cumulative: level }; // A1 level = cumulative
  }

  return { level: 0, cumulative: 0 };
}

/**
 * Parse case requirements from the Cases table in grammar requirements section.
 *
 * Looks for the section: "#### Cases" or "##### Cases" followed by a table.
 * A1 format: | Case | Ukrainian | Allowed at A1 | Key Patterns |
 * A2 format: | Case | Ukrainian | New at A2 | Key Uses |
 */
function parseCaseRequirements(content: string): GrammarRequirement[] {
  const requirements: GrammarRequirement[] = [];

  // Find the Cases section (#### or ##### header)
  const caseSectionMatch = content.match(/#{3,5}\s*Cases\s*\([^)]+\)[^#]*\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|[\s\S]*?(?=#{3,5}|$)/i);
  if (!caseSectionMatch) return requirements;

  const caseSection = caseSectionMatch[0];

  // Match table rows for cases within this section
  // Cases may be wrapped in ** for emphasis
  const caseTableRegex = /\|\s*\*{0,2}(Nominative|Accusative|Genitive|Dative|Locative|Instrumental|Vocative)\*{0,2}\s*\|\s*\*{0,2}([^|*]+)\*{0,2}\s*\|\s*([^|]+)\s*\|/gi;

  let match;
  while ((match = caseTableRegex.exec(caseSection)) !== null) {
    const caseName = match[1];
    const status = match[3].trim();

    let allowedFromModule: number | null = null;

    if (status.includes('✅')) {
      // Check for "From MXX" or just "MXX" pattern
      const moduleMatch = status.match(/(?:From\s*)?M(\d+)/i);
      if (moduleMatch) {
        allowedFromModule = parseInt(moduleMatch[1], 10);
      } else {
        // Just "✅" means from module 1
        allowedFromModule = 1;
      }
    } else if (status.match(/From\s*A[12]/i)) {
      // "From A1" or "From A2" means it was learned in previous level
      // At this level it's available from module 1
      allowedFromModule = 1;
    }
    // ❌ or nothing means null (not allowed at this level)

    requirements.push({
      feature: caseName,
      allowedFromModule,
      notes: match[2]?.trim()
    });
  }

  return requirements;
}

/**
 * Parse adjective requirements
 * Look for patterns like "From M26+" or "✅ From M26"
 */
function parseAdjectiveRequirements(content: string): GrammarRequirement[] {
  const requirements: GrammarRequirement[] = [];

  // Look for adjective section
  const adjSection = content.match(/#{3,4}\s*Adjectives[^#]*/i);
  if (adjSection) {
    const fromModule = adjSection[0].match(/From\s*M(\d+)/i);
    if (fromModule) {
      requirements.push({
        feature: 'Adjectives',
        allowedFromModule: parseInt(fromModule[1], 10)
      });
    }
  }

  // Also check for explicit "Adjectives" row in tables
  const tableMatch = content.match(/\|\s*Adjectives[^|]*\|\s*(✅\s*From\s*M(\d+)|❌[^|]*)\s*\|/i);
  if (tableMatch && tableMatch[2]) {
    requirements.push({
      feature: 'Adjectives',
      allowedFromModule: parseInt(tableMatch[2], 10)
    });
  }

  return requirements;
}

/**
 * Parse свій (reflexive possessive) requirements
 */
function parseSviyRequirement(content: string): GrammarRequirement | null {
  // Look for "свій" mentions
  if (content.includes('свій')) {
    // Check if explicitly not allowed - various patterns
    // "No свій", "свій - A2/B1 topic", "❌ свій"
    const notAllowed = content.match(/No\s+свій|свій.*(?:A2|B1|B2|C1|C2)\s*topic|❌.*свій|свій.*NOT\s+allowed/i);
    if (notAllowed) {
      return {
        feature: 'свій',
        allowedFromModule: null,
        notes: 'NOT allowed at this level'
      };
    }

    // Check if allowed at this level
    const allowed = content.match(/✅.*свій|свій.*✅|NEW at [AB]\d.*свій/i);
    if (allowed) {
      return {
        feature: 'свій',
        allowedFromModule: 1,
        notes: 'Reflexive possessive'
      };
    }
  }

  return null;
}

/**
 * Extract immersion level from content
 * Look for patterns like "**Immersion:** 15% English / 85% Ukrainian"
 */
function parseImmersionLevel(content: string, level: string): number {
  const match = content.match(/\*\*Immersion:\*\*\s*(\d+)%\s*English\s*\/\s*(\d+)%\s*Ukrainian/i);
  if (match) {
    return parseFloat(match[2]) / 100;
  }

  // Default immersion levels per CEFR
  const defaults: Record<string, number> = {
    'A1': 0.30,
    'A2': 0.40,
    'A2+': 0.50,
    'B1': 0.60,
    'B1+': 0.70,
    'B2': 0.85,
    'C1': 0.95,
    'C2': 0.98
  };

  return defaults[level] || 0.50;
}

/**
 * Parse a curriculum plan markdown file and extract level config
 */
export function parseCurriculumPlan(content: string, level: string): LevelConfig {
  const moduleCount = parseModuleCount(content);
  const vocabTargets = parseVocabularyTargets(content);
  const immersionLevel = parseImmersionLevel(content, level);

  const grammarRequirements: GrammarRequirement[] = [
    ...parseCaseRequirements(content),
    ...parseAdjectiveRequirements(content)
  ];

  const sviyReq = parseSviyRequirement(content);
  if (sviyReq) {
    grammarRequirements.push(sviyReq);
  }

  return {
    level,
    moduleCount,
    vocabularyTarget: vocabTargets.level,
    cumulativeVocab: vocabTargets.cumulative,
    immersionLevel,
    grammarRequirements,
    checkpointInterval: 10 // Standard: every 10 modules
  };
}

/**
 * Load all curriculum plans for a language pair
 */
export async function loadAuditConfig(
  languagePair: string,
  readFile: (path: string) => Promise<string>
): Promise<AuditConfig> {
  const levels = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'];
  const config: AuditConfig = {
    languagePair,
    levels: {}
  };

  for (const level of levels) {
    const planPath = `docs/${languagePair}/${level}-CURRICULUM-PLAN.md`;
    try {
      const content = await readFile(planPath);
      config.levels[level] = parseCurriculumPlan(content, level);
    } catch (error) {
      // Plan file doesn't exist for this level
      console.warn(`No curriculum plan found for ${level}: ${planPath}`);
    }
  }

  return config;
}

/**
 * Get grammar requirements for a specific level and module number
 * @param level - CEFR level (A1, A2, B1, etc.)
 * @param moduleNum - Level-internal module number (1-30 for A1, 1-50 for A2, etc.)
 */
export function getGrammarRequirementsForModule(
  config: AuditConfig,
  level: string,
  moduleNum: number
): GrammarRequirement[] {
  const levelConfig = config.levels[level];
  if (!levelConfig) return [];

  // Filter requirements - only those allowed by this module number
  return levelConfig.grammarRequirements.filter(req => {
    if (req.allowedFromModule === null) return false;
    return req.allowedFromModule <= moduleNum;
  });
}

/**
 * Check if a grammar feature is allowed for a specific level and module
 * @param level - CEFR level (A1, A2, B1, etc.)
 * @param moduleNum - Level-internal module number
 * @param feature - Grammar feature name
 */
export function isFeatureAllowed(
  config: AuditConfig,
  level: string,
  moduleNum: number,
  feature: string
): boolean {
  const levelConfig = config.levels[level];
  if (!levelConfig) return false;

  const requirement = levelConfig.grammarRequirements.find(
    r => r.feature.toLowerCase() === feature.toLowerCase()
  );

  // If no restriction found for this feature, it's allowed
  if (!requirement) return true;
  // If explicitly not allowed at this level
  if (requirement.allowedFromModule === null) return false;
  // Check if the feature is introduced by this module
  return requirement.allowedFromModule <= moduleNum;
}

/**
 * Get all features that are NOT allowed at a given level
 * Useful for checking what to flag as violations
 */
export function getForbiddenFeatures(
  config: AuditConfig,
  level: string
): string[] {
  const levelConfig = config.levels[level];
  if (!levelConfig) return [];

  return levelConfig.grammarRequirements
    .filter(req => req.allowedFromModule === null)
    .map(req => req.feature);
}

/**
 * Get the module number at which a feature is introduced
 * Returns null if the feature is not allowed at this level
 */
export function getFeatureIntroModule(
  config: AuditConfig,
  level: string,
  feature: string
): number | null {
  const levelConfig = config.levels[level];
  if (!levelConfig) return null;

  const requirement = levelConfig.grammarRequirements.find(
    r => r.feature.toLowerCase() === feature.toLowerCase()
  );

  return requirement?.allowedFromModule ?? null;
}
