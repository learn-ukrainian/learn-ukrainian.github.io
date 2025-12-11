/**
 * JSON Renderer
 *
 * Generates Vibe-format JSON from parsed modules
 * Simplified output: sections with raw markdown, Vibe handles extraction
 */

import {
  ParsedModule,
  VibeModule,
  VibeLesson,
  VibeActivity,
  VibeSection,
  VocabularySection,
  Activity,
  RenderContext,
  ModuleType,
} from '../types';
import { buildVocabularySection } from '../parsers/vocabulary';

// =============================================================================
// JSON Output Generator
// =============================================================================

/**
 * Generate complete Vibe JSON module
 */
export function renderVibeJson(parsed: ParsedModule, ctx: RenderContext): VibeModule {
  const { frontmatter, sections, activities, vocabulary, reviewVocabulary, rawMarkdown } = parsed;

  // Build lesson object
  const lesson = buildVibeLesson(parsed, ctx);

  // Build activity objects
  const vibeActivities = activities.map(a => buildVibeActivity(a, frontmatter.level));

  // Build vocabulary section (includes both new and review words)
  const vocabSection = buildVocabularySection(
    vocabulary,
    frontmatter.module,
    frontmatter.level,
    frontmatter.phase,
    frontmatter.transliteration,
    undefined, // letterGroups
    reviewVocabulary
  );

  return {
    $schema: '../../../schemas/vibe-module.schema.json',
    lesson,
    activities: vibeActivities,
    vocabulary: vocabSection,
  };
}

// =============================================================================
// Lesson Builder
// =============================================================================

/**
 *
 */
function buildVibeLesson(parsed: ParsedModule, ctx: RenderContext): VibeLesson {
  const { frontmatter, sections, rawMarkdown } = parsed;
  const now = new Date().toISOString();

  // Infer moduleType from tags
  const moduleType = inferModuleType(frontmatter.tags);

  // Calculate immersion level based on CEFR level
  const immersionLevel = getImmersionLevel(frontmatter.level);

  // Build simplified sections (name + raw markdown content)
  const vibeSections = buildVibeSections(sections);

  const lesson: VibeLesson = {
    id: `lesson-uk-${frontmatter.level}-${padNumber(frontmatter.module)}`,
    moduleId: `mod-uk-${frontmatter.level}-${padNumber(frontmatter.module)}`,
    languagePair: ctx.languagePair,
    subject: 'language',
    owner: 'curricula-opus',
    visibility: 'public',
    language: 'uk',
    targetLevel: frontmatter.level,
    phase: frontmatter.phase,
    moduleNumber: frontmatter.module,
    moduleType,
    pedagogy: frontmatter.pedagogy,
    immersionLevel,
    title: frontmatter.title,
    subtitle: frontmatter.subtitle,
    description: frontmatter.objectives[0] || frontmatter.title,
    objectives: frontmatter.objectives,
    grammarFocus: frontmatter.grammar || [],
    tags: frontmatter.tags,
    totalDuration: frontmatter.duration,
    transliterationMode: frontmatter.transliteration,
    sections: vibeSections,
    rawMarkdown,
    createdAt: now,
    modifiedAt: now,
    version: 2,
  };

  // Add Ukrainian title if present
  if (frontmatter.titleUk) {
    lesson.titleUk = frontmatter.titleUk;
  }

  // Add Ukrainian description if objectives have Ukrainian version
  if (frontmatter.objectivesUk && frontmatter.objectivesUk.length > 0) {
    lesson.descriptionUk = frontmatter.objectivesUk[0];
    lesson.objectivesUk = frontmatter.objectivesUk;
  }

  return lesson;
}

// =============================================================================
// Module Type Inference
// =============================================================================

const MODULE_TYPE_MAPPINGS: { type: ModuleType; tags: string[] }[] = [
  { type: 'checkpoint', tags: ['checkpoint', 'review', 'assessment'] },
  { type: 'history', tags: ['history'] },
  { type: 'biography', tags: ['biography'] },
  { type: 'idioms', tags: ['idioms', 'phraseology'] },
  { type: 'literature', tags: ['literature', 'poetry', 'prose'] },
  { type: 'culture', tags: ['culture', 'regions', 'music'] },
  { type: 'skills', tags: ['skills', 'academic', 'writing'] },
  { type: 'functional', tags: ['functional', 'dialogue', 'role-play'] },
  { type: 'vocabulary', tags: ['vocabulary', 'vocab'] },
  { type: 'grammar', tags: ['grammar', 'cases', 'verbs', 'aspect'] },
];

/**
 *
 */
function inferModuleType(tags: string[]): ModuleType {
  const tagSet = new Set(tags.map(t => t.toLowerCase()));

  for (const mapping of MODULE_TYPE_MAPPINGS) {
    if (mapping.tags.some(tag => tagSet.has(tag))) {
      return mapping.type;
    }
  }

  return 'grammar';
}

// =============================================================================
// Immersion Level
// =============================================================================

/**
 *
 */
function getImmersionLevel(level: string): number {
  // Returns percentage of Ukrainian content (0.0 = all English, 1.0 = all Ukrainian)
  const levels: Record<string, number> = {
    'A1': 0.30,   // 70% EN / 30% UK
    'A2': 0.40,   // 60% EN / 40% UK
    'A2+': 0.50,  // 50% EN / 50% UK
    'B1': 0.60,   // 40% EN / 60% UK
    'B1+': 0.70,  // 30% EN / 70% UK
    'B2': 0.85,   // 15% EN / 85% UK
    'B2+': 0.90,  // 10% EN / 90% UK
    'C1': 0.95,   // 5% EN / 95% UK
    'C2': 0.98,   // 2% EN / 98% UK
  };
  return levels[level] ?? 0.50;
}

// =============================================================================
// Section Builder
// =============================================================================

/**
 *
 */
function buildVibeSections(sections: { id: string; type: string; title: string; titleUk?: string; content: string }[]): VibeSection[] {
  return sections.map(s => ({
    id: s.id,
    name: s.titleUk || s.title,
    nameEn: s.titleUk ? s.title : undefined,
    type: s.type,
    content: s.content,
  }));
}

// =============================================================================
// Activity Builder
// =============================================================================

/**
 *
 */
function buildVibeActivity(activity: Activity, level: string): VibeActivity {
  const now = new Date().toISOString();

  return {
    id: activity.id,
    type: activity.type,
    title: activity.title,
    titleUk: activity.titleUk,
    description: activity.description,
    content: activity.content,
    subject: 'language',
    owner: 'curricula-opus',
    visibility: 'public',
    language: 'uk',
    difficultyLevel: level,
    duration: 5, // Default 5 minutes per activity
    tags: activity.tags || [],
    createdAt: now,
    modifiedAt: now,
  };
}

// =============================================================================
// Utilities
// =============================================================================

/**
 *
 */
function padNumber(num: number): string {
  return num.toString().padStart(2, '0');
}

// =============================================================================
// Exports
// =============================================================================

export { renderVibeJson as render };
