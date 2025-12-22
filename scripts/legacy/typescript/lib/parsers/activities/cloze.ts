/**
 * Cloze activity parser
 *
 * Parses passage-level fill-in-the-blank with multiple blanks and options:
 *
 * ## cloze: Complete the passage
 * > Fill in the blanks with the correct words.
 *
 * Мене звати Оксана. Я [___:1] в Києві. Щодня я [___:2] на роботу автобусом.
 *
 * 1. живу | працюю | сплю
 * 2. їду | йду | біжу
 *
 * > [!answer] живу, їду
 */

import { ActivityParser } from './base';
import { ParseContext } from '../../types';

// =============================================================================
// Types
// =============================================================================

export interface ClozeBlank {
  index: number;        // 0-based index in text
  optionIndex: number;  // which option list (1-based from markdown)
  options: string[];    // available choices
  answer: string;       // correct answer
}

export interface ClozeContent {
  type: 'cloze';
  text: string;         // passage with [___:N] markers
  blanks: ClozeBlank[];
}

// =============================================================================
// Parser
// =============================================================================

export class ClozeParser extends ActivityParser<ClozeContent> {
  readonly type = 'cloze' as const;

  canParse(header: string): boolean {
    const match = header.match(/^([\w-]+):\s*/);
    if (!match) return false;
    const type = match[1].toLowerCase();
    return type === 'cloze' || type === 'cloze-passage';
  }

  protected parseContent(content: string, ctx: ParseContext): ClozeContent {
    const body = this.getContentBody(content);

    // Extract the passage text (everything before numbered option lists)
    const lines = body.split('\n');
    const textLines: string[] = [];
    const optionLines: string[] = [];
    let inOptions = false;

    for (const line of lines) {
      // Check if this is an option line (starts with number followed by period)
      if (line.match(/^\d+\.\s+/)) {
        inOptions = true;
      }

      // Skip callout lines
      if (line.match(/>\s*\[!/)) {
        continue;
      }

      if (inOptions) {
        optionLines.push(line);
      } else if (line.trim() && !line.startsWith('>')) {
        textLines.push(line);
      }
    }

    const text = textLines.join('\n').trim();

    // Parse option lists: "1. option1 | option2 | option3"
    const optionLists: Map<number, string[]> = new Map();
    for (const line of optionLines) {
      const match = line.match(/^(\d+)\.\s+(.+)/);
      if (match) {
        const optionIndex = parseInt(match[1], 10);
        const options = match[2].split('|').map(o => o.trim()).filter(Boolean);
        optionLists.set(optionIndex, options);
      }
    }

    // Parse answers from callout
    const { answer: answerStr } = this.parseAnswerBlock(content);
    const answers = answerStr
      ? answerStr.split(',').map(a => a.trim()).filter(Boolean)
      : [];

    // Find all blanks in text: [___:N]
    const blanks: ClozeBlank[] = [];
    const blankMatches = text.matchAll(/\[___:(\d+)\]/g);
    let index = 0;

    for (const match of blankMatches) {
      const optionIndex = parseInt(match[1], 10);
      const options = optionLists.get(optionIndex) || [];
      const answer = answers[index] || options[0] || '';

      blanks.push({
        index,
        optionIndex,
        options,
        answer,
      });
      index++;
    }

    return {
      type: 'cloze',
      text,
      blanks,
    };
  }
}
