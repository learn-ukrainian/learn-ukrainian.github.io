/**
 * Order activity parser
 *
 * Parses ordering/sequencing exercises:
 *
 * ## order: Chronology
 * > Arrange events in chronological order
 *
 * 1. Заснування Ольвії греками
 * 2. Розквіт Трипільської культури
 * 3. Знахідка пекторалі в Товстій Могилі
 *
 * > [!answer] 2, 1, 3
 * > [!explanation] Трипілля → Ольвія → Пектораль
 *
 * Also handles word-jumble format (when items contain "/"):
 *
 * 1. автобусом / роботу / Я / на / їду
 *    > [!answer] Я їду на роботу автобусом.
 */

import { ActivityParser } from './base';
import { OrderContent, ParseContext } from '../../types';

interface UnjumbleItem {
  words: string[];
  answer: string;
  translation?: string;
}

interface UnjumbleContent {
  type: 'order';
  isUnjumble: true;
  items: UnjumbleItem[];
}

export class OrderParser extends ActivityParser<OrderContent | UnjumbleContent> {
  readonly type = 'order' as const;

  protected parseContent(content: string, ctx: ParseContext): OrderContent | UnjumbleContent {
    const body = this.getContentBody(content);

    // Check if this is a word-jumble format (items contain "/")
    const firstItemMatch = body.match(/\d+\.\s+([^\n]+)/);
    if (firstItemMatch && firstItemMatch[1].includes('/')) {
      return this.parseAsUnjumble(body);
    }

    return this.parseAsSequence(body);
  }

  /**
   * Parse as word-jumble (unjumble) activity
   */
  private parseAsUnjumble(body: string): UnjumbleContent {
    const items: UnjumbleItem[] = [];

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

      // Extract translation from parentheses
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
      type: 'order',
      isUnjumble: true,
      items,
    };
  }

  /**
   * Parse as sequence ordering activity
   */
  private parseAsSequence(body: string): OrderContent {
    const items: string[] = [];

    // Extract numbered items (before answer callout)
    const itemLines = body.split('\n').filter(line => !line.startsWith('>'));
    const itemMatches = itemLines.join('\n').matchAll(/(\d+)\.\s+(.+)/g);

    for (const match of itemMatches) {
      items.push(match[2].trim());
    }

    // Parse correct order from answer callout
    const { answer, explanation } = this.parseAnswerBlock(body);

    // Parse order from answer (e.g., "2, 1, 3" or "2,1,3" or "2 1 3")
    const correctOrder = this.parseOrderArray(answer, items.length);

    const result: OrderContent = {
      type: 'order',
      items,
      correctOrder,
    };

    if (explanation) {
      result.explanation = explanation;
    }

    return result;
  }

  /**
   * Parse order array from answer string
   * Handles: "2, 1, 3" or "2,1,3" or "2 1 3"
   * Returns 0-indexed array (converts from 1-indexed)
   */
  private parseOrderArray(answer: string, expectedLength: number): number[] {
    if (!answer) {
      // Default: items are already in correct order
      return Array.from({ length: expectedLength }, (_, i) => i);
    }

    // Split by comma, space, or any combination
    const parts = answer.split(/[,\s]+/).filter(Boolean);

    return parts.map(p => {
      const num = parseInt(p.trim(), 10);
      // Convert from 1-indexed to 0-indexed
      return isNaN(num) ? 0 : num - 1;
    });
  }
}
