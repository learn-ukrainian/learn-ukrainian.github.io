/**
 * Gap-fill activity parser
 *
 * Parses text passages with multiple blanks:
 *
 * ## gap-fill: Complete the Text
 * > Fill in the blanks with the correct words
 *
 * > Я ___ (hint1) до школи. Там ___ (hint2) мої друзі.
 *
 * > [!answer] йду, чекають
 *
 * Or with **Answers:** legacy format:
 * **Answers:** йду, чекають
 */

import { ActivityParser } from './base';
import { GapFillContent, GapFillBlank, ParseContext } from '../../types';

export class GapFillParser extends ActivityParser<GapFillContent> {
  readonly type = 'gap-fill' as const;

  protected parseContent(content: string, ctx: ParseContext): GapFillContent {
    // Extract the text with blanks (blockquote lines that aren't callouts)
    const textLines: string[] = [];
    let foundText = false;
    let hasSeenCallout = false;

    for (const line of content.split('\n')) {
      // Skip callout blocks
      if (line.match(/>\s*\[!/)) {
        hasSeenCallout = true;
        continue;
      }

      // Collect blockquote text before callouts
      if (line.startsWith('>') && !hasSeenCallout) {
        textLines.push(line.replace(/^>\s*/, ''));
        foundText = true;
      } else if (foundText && !line.trim()) {
        // Allow blank lines within text
      } else if (foundText && !line.startsWith('>')) {
        // Stop at non-blockquote, non-blank line
        break;
      }
    }

    const text = textLines.join('\n').trim();

    // Extract hints from ___ (hint) pattern
    const blanks: GapFillBlank[] = [];
    const blankMatches = text.matchAll(/___\s*(?:\(([^)]+)\))?/g);
    let index = 0;
    for (const match of blankMatches) {
      blanks.push({
        index,
        hint: match[1] || undefined,
      });
      index++;
    }

    // Extract answers
    let answers: string[] = [];

    // Try callout format first
    const { answer: calloutAnswer } = this.parseAnswerBlock(content);
    if (calloutAnswer) {
      answers = this.parseAnswerList(calloutAnswer);
    } else {
      // Try legacy format: **Answers:** ans1, ans2
      const legacyMatch = content.match(/\*\*Answers?:\*\*\s*(.+)/i);
      if (legacyMatch) {
        answers = this.parseAnswerList(legacyMatch[1]);
      }
    }

    return {
      type: 'gap-fill',
      text,
      blanks,
      answers,
    };
  }

  /**
   * Parse answer list from comma or semicolon separated string
   */
  private parseAnswerList(answerStr: string): string[] {
    return answerStr
      .split(/[,;]/)
      .map(a => a.trim())
      .filter(Boolean);
  }
}
