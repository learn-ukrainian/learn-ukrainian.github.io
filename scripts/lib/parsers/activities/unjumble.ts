/**
 * Unjumble activity parser
 *
 * Parses word reordering exercises:
 *
 * ## unjumble: Word Order
 * > Put the words in the correct order to form a sentence.
 *
 * 1. Це / твоя / сумка
 *    > [!answer] Це твоя сумка?
 *    > (Is this your bag?)
 *
 * 2. моя / Де / ручка
 *    > [!answer] Де моя ручка?
 */

import { ActivityParser } from './base';
import { ParseContext } from '../../types';

export interface UnjumbleItem {
  words: string[];
  answer: string;
  translation?: string;
}

export interface UnjumbleContent {
  type: 'unjumble';
  items: UnjumbleItem[];
}

export class UnjumbleParser extends ActivityParser<UnjumbleContent> {
  readonly type = 'unjumble' as const;

  canParse(header: string): boolean {
    const match = header.match(/^([\w-]+):\s*/);
    if (!match) return false;
    const type = match[1].toLowerCase();
    return type === 'unjumble' || type === 'unscramble' || type === 'word-order';
  }

  protected parseContent(content: string, ctx: ParseContext): UnjumbleContent {
    const items: UnjumbleItem[] = [];
    const body = this.getContentBody(content);

    // Split by numbered items
    const itemMatches = body.matchAll(/(\d+)\.\s+([\s\S]*?)(?=\n\d+\.|$)/g);

    for (const match of itemMatches) {
      const itemContent = match[2].trim();
      const lines = itemContent.split('\n');

      // First line has jumbled words: "Це / твоя / сумка"
      const jumbledLine = lines[0].trim();
      const words = jumbledLine.split(/\s*\/\s*/).map(w => w.trim()).filter(Boolean);

      // Parse answer from callout
      const answerLines = lines.slice(1).join('\n');
      const { answer } = this.parseAnswerBlock(answerLines);

      // Extract translation from parentheses: > (Is this your bag?)
      let translation: string | undefined;
      const transMatch = answerLines.match(/>\s*\(([^)]+)\)/);
      if (transMatch) {
        translation = transMatch[1].trim();
      }

      if (words.length > 0) {
        items.push({
          words,
          answer: answer || words.join(' '),
          translation,
        });
      }
    }

    return {
      type: 'unjumble',
      items,
    };
  }
}
