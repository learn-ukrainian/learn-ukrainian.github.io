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
 */

import { ActivityParser } from './base';
import { OrderContent, ParseContext } from '../../types';

export class OrderParser extends ActivityParser<OrderContent> {
  readonly type = 'order' as const;

  protected parseContent(content: string, ctx: ParseContext): OrderContent {
    const items: string[] = [];
    const body = this.getContentBody(content);

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
