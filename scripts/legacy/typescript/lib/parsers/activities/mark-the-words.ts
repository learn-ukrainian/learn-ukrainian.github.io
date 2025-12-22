/**
 * Mark the words activity parser
 *
 * Parses word identification exercises:
 *
 * ## mark-the-words: Find the accusative nouns
 * > Click all nouns in the accusative case.
 *
 * Я бачу [книгу] на столі. Марія читає [газету] і п'є [каву].
 */

import { ActivityParser } from './base';
import { ParseContext } from '../../types';

// =============================================================================
// Types
// =============================================================================

export interface MarkTheWordsContent {
  type: 'mark-the-words';
  text: string;           // full text with markers removed for display
  correctWords: string[]; // words that should be selected
}

// =============================================================================
// Parser
// =============================================================================

export class MarkTheWordsParser extends ActivityParser<MarkTheWordsContent> {
  readonly type = 'mark-the-words' as const;

  canParse(header: string): boolean {
    const match = header.match(/^([\w-]+):\s*/);
    if (!match) return false;
    const type = match[1].toLowerCase();
    return type === 'mark-the-words' || type === 'mark-words' || type === 'markwords';
  }

  protected parseContent(content: string, ctx: ParseContext): MarkTheWordsContent {
    const body = this.getContentBody(content);

    // Find all marked words: [word]
    const correctWords: string[] = [];
    const markedMatches = body.matchAll(/\[([^\]]+)\]/g);

    for (const match of markedMatches) {
      correctWords.push(match[1].trim());
    }

    // Remove the brackets to get display text
    const text = body
      .replace(/\[([^\]]+)\]/g, '$1')
      .trim();

    return {
      type: 'mark-the-words',
      text,
      correctWords,
    };
  }
}
