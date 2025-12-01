/**
 * JSON Renderer
 *
 * Generates Vibe-format JSON from parsed modules
 */

import {
  ParsedModule,
  VibeModule,
  VibeLesson,
  VibeActivity,
  VocabularySection,
  Activity,
  RenderContext,
} from '../types';
import { parsePhases } from '../parsers/sections';
import { buildVocabularySection } from '../parsers/vocabulary';

// =============================================================================
// JSON Output Generator
// =============================================================================

/**
 * Generate complete Vibe JSON module
 */
export function renderVibeJson(parsed: ParsedModule, ctx: RenderContext): VibeModule {
  const { frontmatter, sections, activities, vocabulary, rawMarkdown } = parsed;

  // Build lesson object
  const lesson = buildVibeLesson(parsed, ctx);

  // Build activity objects
  const vibeActivities = activities.map(a => buildVibeActivity(a, frontmatter.level));

  // Build vocabulary section
  const vocabSection = buildVocabularySection(
    vocabulary,
    frontmatter.module,
    frontmatter.level,
    frontmatter.phase,
    frontmatter.transliteration
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

function buildVibeLesson(parsed: ParsedModule, ctx: RenderContext): VibeLesson {
  const { frontmatter, sections, rawMarkdown } = parsed;
  const now = new Date().toISOString();

  // Parse PPP phases from markdown
  const { phases } = parsePhases(rawMarkdown, frontmatter.duration);

  // Build immersive sections for B1+ content
  const immersiveSections = sections.filter(s =>
    s.type === 'intro' || s.type === 'content' || s.type === 'summary'
  );

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
    title: frontmatter.title,
    subtitle: frontmatter.subtitle,
    description: frontmatter.objectives[0] || frontmatter.title,
    objectives: frontmatter.objectives,
    grammarFocus: frontmatter.grammar || [],
    tags: frontmatter.tags,
    totalDuration: frontmatter.duration,
    transliterationMode: frontmatter.transliteration,
    phases: phases.length > 0 ? phases : [],
    createdAt: now,
    modifiedAt: now,
    version: 1,
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

  // Add immersive sections for B1+ content
  if (immersiveSections.length > 0 && isImmersiveLevel(frontmatter.level)) {
    lesson.immersiveSections = immersiveSections;
    lesson.rawMarkdown = rawMarkdown;
  }

  return lesson;
}

// =============================================================================
// Activity Builder
// =============================================================================

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

function padNumber(num: number): string {
  return num.toString().padStart(2, '0');
}

function isImmersiveLevel(level: string): boolean {
  return ['B1', 'B2', 'C1', 'C2'].includes(level);
}

// =============================================================================
// Exports
// =============================================================================

export { renderVibeJson as render };
