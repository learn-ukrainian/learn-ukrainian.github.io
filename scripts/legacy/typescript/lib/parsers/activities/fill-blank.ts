/**
 * Fill-blank activity parser
 *
 * Parses fill-in-the-blank exercises with callout answers:
 *
 * ## fill-blank: Fill Title
 * > Instructions here
 *
 * 1. Він ___ (відкривати/відкрити) вікно кожен ранок.
 *    > [!answer] відкриває
 *    > [!explanation] Habitual action requires imperfective
 *
 * 2. Sentence with ___ blank.
 *    > [!answer] answer
 *    > [!alt] alternative answer
 */

import { ActivityParser } from './base';
import { FillBlankContent, FillBlankItem, ParseContext } from '../../types';

/**
 *
 */
export class FillBlankParser extends ActivityParser<FillBlankContent> {
  readonly type = 'fill-blank' as const;

  /**
   *
   */
  protected parseContent(content: string, ctx: ParseContext): FillBlankContent {
    const items: FillBlankItem[] = [];
    const body = this.getContentBody(content);

    // Split by numbered items
    const itemMatches = body.matchAll(/(\d+)\.\s+([\s\S]*?)(?=\n\d+\.|$)/g);

    for (const match of itemMatches) {
      const itemContent = match[2].trim();

      // Split into prompt (before callouts) and answer block (callouts)
      const lines = itemContent.split('\n');
      const promptLines: string[] = [];
      const answerLines: string[] = [];

      let inAnswerBlock = false;
      for (const line of lines) {
        if (line.match(/^\s*(?:>|-|\*)\s*\[!/)) {
          inAnswerBlock = true;
        }
        if (inAnswerBlock) {
          answerLines.push(line);
        } else {
          promptLines.push(line);
        }
      }

      let prompt = promptLines.join('\n').trim();
      const answerBlock = answerLines.join('\n');

      // Parse answer from callouts
      const { answer, explanation, alternatives } = this.parseAnswerBlock(answerBlock);

      // Parse options from [!options] callout
      const optionsMatch = answerBlock.match(/>\s*\[!options\]\s*(.+)/);
      const options = optionsMatch
        ? optionsMatch[1].split('|').map(o => o.trim()).filter(Boolean)
        : undefined;

      // Strip hints from blank pattern: ___ (hint) -> ___
      // We do NOT want to show hints in the final UI as per user request
      prompt = prompt.replace(/___\s*\(([^)]+)\)/g, '___');
      const hints = undefined; // Force hints to be undefined

      const item: FillBlankItem = {
        prompt,
        answer,
      };

      if (hints) item.hints = hints;
      if (explanation) item.explanation = explanation;
      if (alternatives && alternatives.length > 0) item.alternatives = alternatives;
      if (options && options.length > 0) item.options = options;

      items.push(item);
    }

    return {
      type: 'fill-blank',
      items,
    };
  }
}
