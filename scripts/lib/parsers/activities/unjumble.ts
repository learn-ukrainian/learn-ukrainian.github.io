/**
 * Unjumble activity parser
 *
 * Parses word reordering exercises. Supports two formats:
 *
 * Slash-separated (explicit word boundaries):
 * ## unjumble: Word Order
 * 1. Це / твоя / сумка
 *    > [!answer] Це твоя сумка?
 *    > (Is this your bag?)
 *
 * Space-separated (implicit word boundaries):
 * ## unjumble: Word Order
 * 1. немає мене часу У
 *    > [!answer] У мене немає часу.
 *    > (I don't have time.)
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
  isUnjumble: true;
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

      // First line has jumbled words: "Це / твоя / сумка" or "Це твоя сумка"
      const jumbledLine = lines[0].trim();
      // Support both slash-separated (explicit) and space-separated (implicit) formats
      const hasSlashes = jumbledLine.includes('/');
      const words = hasSlashes
        ? jumbledLine.split(/\s*\/\s*/).map(w => w.trim()).filter(Boolean)
        : jumbledLine.split(/\s+/).filter(Boolean);

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
      isUnjumble: true,
      items,
    };
  }
}
