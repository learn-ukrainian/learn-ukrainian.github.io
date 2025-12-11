/**
 * Translate activity parser
 *
 * Parses translation exercises with callout answers:
 *
 * ## translate: Translation Practice
 * > Translate the following sentences
 *
 * 1. I'm opening the window.
 *    > [!answer] Я відкриваю вікно.
 *
 * 2. She opened the door.
 *    > [!answer] Вона відкрила двері.
 *    > [!alt] Вона відчинила двері.
 */

import { ActivityParser } from './base';
import { TranslateContent, TranslateItem, ParseContext } from '../../types';

/**
 *
 */
export class TranslateParser extends ActivityParser<TranslateContent> {
  readonly type = 'translate' as const;

  /**
   *
   */
  protected parseContent(content: string, ctx: ParseContext): TranslateContent {
    const items: TranslateItem[] = [];
    const body = this.getContentBody(content);

    // Detect translation direction from instructions or content
    const direction = this.detectDirection(content);

    // Split by numbered items
    const itemMatches = body.matchAll(/(\d+)\.\s+([\s\S]*?)(?=\n\d+\.|$)/g);

    for (const match of itemMatches) {
      const itemContent = match[2].trim();

      // Split into source and answer block
      const lines = itemContent.split('\n');
      const sourceLines: string[] = [];
      const answerLines: string[] = [];

      let inAnswerBlock = false;
      for (const line of lines) {
        if (line.match(/>\s*\[!/)) {
          inAnswerBlock = true;
        }
        if (inAnswerBlock) {
          answerLines.push(line);
        } else {
          sourceLines.push(line);
        }
      }

      const source = sourceLines.join(' ').trim();
      const answerBlock = answerLines.join('\n');

      // Parse answer from callouts
      const { answer, explanation, alternatives } = this.parseAnswerBlock(answerBlock);

      const item: TranslateItem = {
        source,
        answer,
      };

      if (alternatives && alternatives.length > 0) {
        item.alternatives = alternatives;
      }
      if (explanation) {
        item.explanation = explanation;
      }

      items.push(item);
    }

    return {
      type: 'translate',
      items,
      direction,
    };
  }

  /**
   * Detect translation direction from content
   * Default: to-uk (English to Ukrainian)
   */
  private detectDirection(content: string): 'to-uk' | 'to-en' {
    // Check instructions for explicit direction
    const instructions = this.extractInstructions(content).toLowerCase();

    if (instructions.includes('to english') || instructions.includes('на англійську')) {
      return 'to-en';
    }

    if (instructions.includes('to ukrainian') || instructions.includes('на українську')) {
      return 'to-uk';
    }

    // Try to detect from first item's language
    // If source looks like English (Latin script), it's to-uk
    const firstItem = content.match(/\d+\.\s+([^\n]+)/);
    if (firstItem) {
      const source = firstItem[1].trim();
      const hasCyrillic = /[а-яіїєґА-ЯІЇЄҐ]/.test(source);
      return hasCyrillic ? 'to-en' : 'to-uk';
    }

    return 'to-uk'; // Default
  }
}
