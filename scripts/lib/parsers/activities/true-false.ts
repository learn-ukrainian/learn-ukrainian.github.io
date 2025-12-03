/**
 * True-false activity parser
 *
 * Parses true/false statements with callout answers:
 *
 * ## true-false: True or False?
 * > Determine if each statement is true or false
 *
 * 1. Трипільські поселення були найбільшими в Європі.
 *    > [!answer] true
 *    > [!explanation] До 15 000 жителів — більше, ніж будь-де.
 *
 * 2. Скіфи були слов'янським народом.
 *    > [!answer] false
 *    > [!explanation] Скіфи говорили іранськими мовами.
 */

import { ActivityParser } from './base';
import { TrueFalseContent, TrueFalseStatement, ParseContext } from '../../types';

export class TrueFalseParser extends ActivityParser<TrueFalseContent> {
  readonly type = 'true-false' as const;

  protected parseContent(content: string, ctx: ParseContext): TrueFalseContent {
    const statements: TrueFalseStatement[] = [];
    const body = this.getContentBody(content);

    // Try checkbox format first: - [x] statement or - [ ] statement
    const checkboxMatches = body.matchAll(/^-\s*\[([ xX])\]\s*(.+?)(?:\n\s*>\s*(.+?))?(?=\n-\s*\[|\n*$)/gms);
    const checkboxResults = [...checkboxMatches];

    if (checkboxResults.length > 0) {
      for (const match of checkboxResults) {
        const isChecked = match[1].toLowerCase() === 'x';
        const statement = match[2].trim();
        const explanation = match[3]?.trim() || '';

        statements.push({
          statement,
          isTrue: isChecked,
          explanation,
        });
      }
      return { type: 'true-false', statements };
    }

    // Fall back to numbered format with [!answer] callouts
    const itemMatches = body.matchAll(/(\d+)\.\s+([\s\S]*?)(?=\n\d+\.|$)/g);

    for (const match of itemMatches) {
      const itemContent = match[2].trim();

      // Split into statement and answer block
      const lines = itemContent.split('\n');
      const statementLines: string[] = [];
      const answerLines: string[] = [];

      let inAnswerBlock = false;
      for (const line of lines) {
        if (line.match(/>\s*\[!/)) {
          inAnswerBlock = true;
        }
        if (inAnswerBlock) {
          answerLines.push(line);
        } else {
          statementLines.push(line);
        }
      }

      const statement = statementLines.join(' ').trim();
      const answerBlock = answerLines.join('\n');

      // Parse answer from callouts
      const { answer, explanation } = this.parseAnswerBlock(answerBlock);

      // Determine boolean value
      const isTrue = this.parseBoolean(answer);

      const stmt: TrueFalseStatement = {
        statement,
        isTrue,
        explanation: explanation || '',
      };

      statements.push(stmt);
    }

    return {
      type: 'true-false',
      statements,
    };
  }

  /**
   * Parse boolean from various string formats
   */
  private parseBoolean(value: string): boolean {
    const normalized = value.toLowerCase().trim();
    const trueValues = ['true', 'правда', 'так', 'yes', '1', 't'];
    return trueValues.includes(normalized);
  }
}
