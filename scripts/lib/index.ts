/**
 * Curricula Opus Generator Library
 *
 * Main entry point for the refactored generator architecture.
 *
 * Usage:
 *   import { parseModule, renderHtml, renderVibeJson } from './lib';
 */

// Types
export * from './types';

// Parsers
export {
  parseModule,
  parseModuleWithContext,
  parseFrontmatter,
  parseSections,
  parsePhases,
  parseVocabulary,
  parseLetterGroups,
  parseActivities,
} from './parsers';

// Renderers
export { renderVibeJson } from './renderers/json';
export { renderHtml, getTemplate } from './renderers/html';

// Utils
export {
  // Files
  readTextFile,
  writeTextFile,
  readJsonFile,
  writeJsonFile,
  findModuleFiles,
  getModulePath,
  getHtmlOutputPath,
  getJsonOutputPath,
  getLevelFromModuleNum,
  fileExists,
  ensureDir,
  // Markdown
  markdownToHtml,
  createMarkdownConverter,
  parseCallouts,
  extractAnswer,
  hasAnswers,
  calloutStyles,
  answerToggleScript,
} from './utils';
