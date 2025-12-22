/**
 * Activity parser registry
 *
 * Exports all activity parsers and provides a unified interface
 * for parsing any activity type.
 */

import { Activity, ActivityContent, ParseContext } from '../../types';
import { ActivityParser } from './base';
import { QuizParser } from './quiz';
import { MatchUpParser } from './match-up';
import { GroupSortParser } from './group-sort';
import { FillBlankParser } from './fill-blank';
import { TrueFalseParser } from './true-false';
import { TranslateParser } from './translate';
import { GapFillParser } from './gap-fill';
import { UnjumbleParser } from './unjumble';
import { AnagramParser } from './anagram';
import { SelectParser } from './select';
import { ErrorCorrectionParser } from './error-correction';
import { ClozeParser } from './cloze';
import { DialogueReorderParser } from './dialogue-reorder';
import { MarkTheWordsParser } from './mark-the-words';

// =============================================================================
// Parser Registry
// =============================================================================

const parsers: ActivityParser[] = [
  new SelectParser(),    // Must be before FillBlankParser to handle select: headers
  new ErrorCorrectionParser(),  // Must be before FillBlankParser
  new ClozeParser(),     // Must be before GapFillParser
  new DialogueReorderParser(),
  new MarkTheWordsParser(),
  new QuizParser(),
  new MatchUpParser(),
  new GroupSortParser(),
  new FillBlankParser(),
  new TrueFalseParser(),
  new TranslateParser(),
  new UnjumbleParser(),
  new AnagramParser(),
  new GapFillParser(),
];

/**
 * Find parser for a given header
 */
export function getParserForHeader(header: string): ActivityParser | undefined {
  return parsers.find(p => p.canParse(header));
}

/**
 * Parse a single activity from header and content
 */
export function parseActivity(
  header: string,
  content: string,
  ctx: ParseContext
): Activity | null {
  const parser = getParserForHeader(header);
  if (!parser) {
    console.warn(`No parser found for activity header: ${header}`);
    return null;
  }
  return parser.parse(header, content, ctx);
}

/**
 * Get the number of items in an activity (for validation)
 */
function getActivityItemCount(activity: Activity): number {
  const content = activity.content as any;
  if (content?.items) return content.items.length;
  if (content?.pairs) return content.pairs.length;
  if (content?.groups) return content.groups.length;
  if (content?.statements) return content.statements.length;
  if (content?.questions) return content.questions.length;
  return 0;
}

/**
 * Parse all activities from markdown content
 * Finds "# Activities" or "# Вправи" section and parses all ## subsections
 */
export function parseActivities(body: string, ctx: ParseContext): {
  activities: Activity[];
  restBody: string;
} {
  const activities: Activity[] = [];

  // Find activities section
  const activitiesMatch = body.match(
    /# (?:Activities|Вправи)[ \t]*\n([\s\S]*?)(?=\n---|\n# (?:Vocabulary|Словник|Summary|Підсумок)|$)/
  );

  if (!activitiesMatch) {
    return { activities: [], restBody: body };
  }

  const activitiesContent = activitiesMatch[1];
  const restBody = body.replace(activitiesMatch[0], '');

  // Split by ## headers
  const sections = activitiesContent.split(/\n## /).filter(Boolean);

  for (const section of sections) {
    const lines = section.trim().split('\n');
    const header = lines[0];
    const content = lines.slice(1).join('\n').trim();

    const activity = parseActivity(header, content, ctx);
    if (activity) {
      // Warn if activity parsed but has no items (likely format mismatch)
      const itemCount = getActivityItemCount(activity);
      if (itemCount === 0) {
        console.warn(`⚠️  Activity "${activity.title}" (${activity.type}) has 0 items - check markdown format`);
      }
      activities.push(activity);
    }
  }

  return { activities, restBody };
}

// =============================================================================
// Exports
// =============================================================================

export { ActivityParser } from './base';
export { QuizParser } from './quiz';
export { MatchUpParser } from './match-up';
export { GroupSortParser } from './group-sort';
export { FillBlankParser } from './fill-blank';
export { TrueFalseParser } from './true-false';
export { TranslateParser } from './translate';
export { UnjumbleParser } from './unjumble';
export { AnagramParser } from './anagram';
export { GapFillParser } from './gap-fill';
export { SelectParser } from './select';
export { ErrorCorrectionParser } from './error-correction';
export { ClozeParser } from './cloze';
export { DialogueReorderParser } from './dialogue-reorder';
export { MarkTheWordsParser } from './mark-the-words';
