/**
 * Module parser
 *
 * Main entry point for parsing markdown modules into structured data.
 * Orchestrates frontmatter, sections, activities, and vocabulary parsing.
 */

import { ParsedModule, ParseContext, Activity, VocabWord, Section } from '../types';
import { parseFrontmatter } from './frontmatter';
import { parseSections, parsePhases } from './sections';
import { parseVocabulary, parseLetterGroups, buildVocabularySection } from './vocabulary';
import { parseActivities } from './activities';

// =============================================================================
// Module Parser
// =============================================================================

export interface ParseOptions {
  languagePair?: string;
  imageMap?: Map<string, string>;
}

/**
 * Parse a complete module from markdown content
 */
export function parseModule(markdown: string, options: ParseOptions = {}): ParsedModule {
  // Parse frontmatter
  const { frontmatter, body } = parseFrontmatter(markdown);

  // Build parse context
  const ctx: ParseContext = {
    level: frontmatter.level,
    moduleNum: frontmatter.module,
    languagePair: options.languagePair || 'l2-uk-en',
    imageMap: options.imageMap || new Map(),
    activityCounters: new Map(),
  };

  // Parse vocabulary (do this early to populate imageMap if needed)
  const { vocabulary, reviewVocabulary, restBody: bodyAfterVocab } = parseVocabulary(body, ctx.moduleNum);

  // Parse letter groups (for alphabet modules)
  const { letterGroups, restBody: bodyAfterLetters } = parseLetterGroups(bodyAfterVocab);

  // Parse activities
  const { activities, restBody: bodyAfterActivities } = parseActivities(bodyAfterLetters, ctx);

  // Parse sections from remaining content
  const sections = parseSections(bodyAfterActivities);

  return {
    frontmatter,
    sections,
    activities,
    vocabulary,
    reviewVocabulary,
    rawMarkdown: markdown,
  };
}

/**
 * Parse module with all context for JSON/HTML generation
 */
export function parseModuleWithContext(
  markdown: string,
  languagePair: string,
  imageMap?: Map<string, string>
): {
  parsed: ParsedModule;
  ctx: ParseContext;
} {
  const parsed = parseModule(markdown, { languagePair, imageMap });

  const ctx: ParseContext = {
    level: parsed.frontmatter.level,
    moduleNum: parsed.frontmatter.module,
    languagePair,
    imageMap: imageMap || new Map(),
    activityCounters: new Map(),
  };

  return { parsed, ctx };
}

// =============================================================================
// Exports
// =============================================================================

export { parseFrontmatter } from './frontmatter';
export { parseSections, parsePhases } from './sections';
export { parseVocabulary, parseLetterGroups, buildVocabularySection } from './vocabulary';
export { parseActivities, parseActivity, getParserForHeader } from './activities';

// Re-export activity parsers for direct use
export * from './activities';
