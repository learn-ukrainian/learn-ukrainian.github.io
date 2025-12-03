/**
 * Base activity parser class
 *
 * All activity parsers extend this class and implement:
 * - type: The activity type they handle
 * - canParse: Whether they can parse a given header
 * - parseContent: Parse activity-specific content
 */

import { Activity, ActivityContent, ActivityType, ParseContext } from '../../types';
import { parseCallouts, extractAnswer, CalloutBlock } from '../../utils/markdown';

// =============================================================================
// Base Parser
// =============================================================================

export abstract class ActivityParser<T extends ActivityContent = ActivityContent> {
  abstract readonly type: ActivityType;

  /**
   * Check if this parser can handle the given header
   * Header format: "type: Title" (e.g., "quiz: Letter Quiz")
   */
  canParse(header: string): boolean {
    const match = header.match(/^([\w-]+):\s*/);
    return match ? this.normalizeType(match[1]) === this.type : false;
  }

  /**
   * Parse a complete activity section
   */
  parse(header: string, content: string, ctx: ParseContext): Activity<T> {
    const title = this.extractTitle(header);
    const instructions = this.extractInstructions(content);
    const activityContent = this.parseContent(content, ctx);

    return {
      id: this.generateId(ctx),
      type: this.type,
      title,
      description: instructions || title,
      instructions,
      content: activityContent,
    };
  }

  /**
   * Parse activity-specific content
   * Implemented by each activity parser
   */
  protected abstract parseContent(content: string, ctx: ParseContext): T;

  // =============================================================================
  // Helper Methods
  // =============================================================================

  /**
   * Normalize activity type names
   * Handles aliases like fill-in → gap-fill
   */
  protected normalizeType(type: string): ActivityType {
    const typeMap: Record<string, ActivityType> = {
      'fill-in': 'fill-blank',
      'fillin': 'fill-blank',
      'fill': 'fill-blank',
      'tf': 'true-false',
      'truefalse': 'true-false',
      'matchup': 'match-up',
      'match': 'match-up',
      'sort': 'group-sort',
      'groupsort': 'group-sort',
      'reorder': 'order',
      // Note: unjumble/unscramble/word-order handled by UnjumbleParser
      // Note: select is handled by SelectParser
    };
    const normalized = type.toLowerCase().replace(/\s+/g, '-');
    return (typeMap[normalized] || normalized) as ActivityType;
  }

  /**
   * Extract title from header line
   * "quiz: My Quiz Title" → "My Quiz Title"
   */
  protected extractTitle(header: string): string {
    const match = header.match(/^[\w-]+:\s*(.+)$/);
    return match ? match[1].trim() : header;
  }

  /**
   * Extract instructions from blockquote lines at start of content
   * Combines multiple > lines into single string
   */
  protected extractInstructions(content: string): string {
    const lines: string[] = [];
    for (const line of content.split('\n')) {
      if (line.startsWith('>') && !line.match(/>\s*\[!/)) {
        // Skip callout blocks (> [!answer], etc.)
        lines.push(line.replace(/^>\s*/, '').trim());
      } else if (lines.length > 0) {
        break; // Stop at first non-instruction line
      }
    }
    return lines.join(' ');
  }

  /**
   * Generate unique activity ID
   */
  protected generateId(ctx: ParseContext): string {
    const typeSlug = this.type.replace(/-/g, '');
    return `act-${ctx.level.toLowerCase()}-${ctx.moduleNum}-${typeSlug}`;
  }

  /**
   * Parse answer from callout syntax
   * > [!answer] answer text
   * > [!explanation] explanation text
   * > [!alt] alternative answer
   */
  protected parseAnswerBlock(text: string): {
    answer: string;
    explanation?: string;
    alternatives?: string[];
  } {
    return extractAnswer(text);
  }

  /**
   * Parse all callouts from a text block
   */
  protected parseCalloutBlocks(text: string): CalloutBlock[] {
    return parseCallouts(text);
  }

  /**
   * Split content by numbered items (1. 2. 3.)
   * Returns array of { number, content } objects
   */
  protected parseNumberedItems(content: string): Array<{ number: number; content: string }> {
    const items: Array<{ number: number; content: string }> = [];

    // Match numbered items: "1. content" potentially spanning multiple lines
    const regex = /^(\d+)\.\s+([\s\S]*?)(?=^\d+\.|$)/gm;
    let match;

    while ((match = regex.exec(content)) !== null) {
      items.push({
        number: parseInt(match[1], 10),
        content: match[2].trim(),
      });
    }

    return items;
  }

  /**
   * Remove instructions and callouts from content to get the "body"
   * Useful for parsing the main content area
   */
  protected getContentBody(content: string): string {
    // Remove leading instructions
    let body = content.replace(/^(?:>\s*[^\[!].*\n)+/, '');

    // We keep callout blocks as they contain answers
    return body.trim();
  }
}
