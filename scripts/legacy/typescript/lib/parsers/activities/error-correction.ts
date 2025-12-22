/**
 * Error-correction activity parser
 *
 * Parses error identification and correction exercises:
 *
 * ## error-correction: Find and Fix
 * > Each sentence has ONE error. Find the incorrect word, then choose the correct form.
 *
 * 1. Я бачу студент у бібліотеці.
 *    > [!error] студент
 *    > [!answer] студента
 *    > [!options] студент | студента | студенту | студентом
 *    > [!explanation] Animate masculine accusative = genitive form
 *
 * 2. Це моя книга, а це твоя.
 *    > [!error] none
 *    > [!answer] ✓
 *    > [!explanation] No error - keeps learners alert
 */

import { ActivityParser } from './base';
import { ParseContext, ErrorCorrectionContent, ErrorCorrectionItem } from '../../types';

// =============================================================================
// Parser
// =============================================================================

/**
 *
 */
export class ErrorCorrectionParser extends ActivityParser<ErrorCorrectionContent> {
  readonly type = 'error-correction' as const;

  /**
   *
   */
  canParse(header: string): boolean {
    const match = header.match(/^([\w-]+):\s*/);
    if (!match) return false;
    const type = match[1].toLowerCase();
    return type === 'error-correction' || type === 'errorcorrection' || type === 'error-correct';
  }

  /**
   *
   */
  protected parseContent(content: string, ctx: ParseContext): ErrorCorrectionContent {
    const items: ErrorCorrectionItem[] = [];
    const body = this.getContentBody(content);

    // Split by numbered items
    const itemMatches = body.matchAll(/(\d+)\.\s+([\s\S]*?)(?=\n\d+\.|$)/g);

    for (const match of itemMatches) {
      const itemContent = match[2].trim();

      // Split into sentence (before callouts) and callout block
      const lines = itemContent.split('\n');
      const sentenceLines: string[] = [];
      const calloutLines: string[] = [];

      let inCalloutBlock = false;
      for (const line of lines) {
        if (line.match(/>\s*\[!/)) {
          inCalloutBlock = true;
        }
        if (inCalloutBlock) {
          calloutLines.push(line);
        } else {
          sentenceLines.push(line);
        }
      }

      const sentence = sentenceLines.join(' ').trim();
      const calloutBlock = calloutLines.join('\n');

      // Parse callouts
      const errorMatch = calloutBlock.match(/>\s*\[!error\]\s*(.+)/);
      const answerMatch = calloutBlock.match(/>\s*\[!answer\]\s*(.+)/);
      const optionsMatch = calloutBlock.match(/>\s*\[!options\]\s*(.+)/);
      const explanationMatch = calloutBlock.match(/>\s*\[!explanation\]\s*(.+)/);

      // Extract values
      const errorWordRaw = errorMatch ? errorMatch[1].trim() : '';
      const errorWord = errorWordRaw.toLowerCase() === 'none' ? null : errorWordRaw;
      const correctForm = answerMatch ? answerMatch[1].trim() : '';
      const options = optionsMatch
        ? optionsMatch[1].split('|').map(o => o.trim()).filter(Boolean)
        : [];
      const explanation = explanationMatch ? explanationMatch[1].trim() : '';

      // Validate item has required fields
      if (sentence && (errorWord !== undefined) && correctForm) {
        items.push({
          sentence,
          errorWord,
          correctForm,
          options,
          explanation,
        });
      }
    }

    return {
      type: 'error-correction',
      items,
    };
  }
}
