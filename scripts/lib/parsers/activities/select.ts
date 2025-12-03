/**
 * Select activity parser
 *
 * Parses multi-select exercises with checkbox format:
 *
 * ## select: Category Selection
 * > Identify which items belong to each category.
 *
 * 1. Which are transport vehicles?
 *    - [x] автобус
 *    - [ ] ручка
 *    - [x] поїзд
 *    - [ ] ніж
 *
 * 2. Which are writing tools?
 *    - [x] ручка
 *    - [ ] автобус
 *    - [x] олівець
 */

import { ActivityParser } from './base';
import { ParseContext } from '../../types';

export interface SelectItem {
  question: string;
  options: Array<{
    text: string;
    correct: boolean;
  }>;
}

export interface SelectContent {
  type: 'select';
  items: SelectItem[];
}

export class SelectParser extends ActivityParser<SelectContent> {
  readonly type = 'select' as const;

  canParse(header: string): boolean {
    const match = header.match(/^([\w-]+):\s*/);
    if (!match) return false;
    return match[1].toLowerCase() === 'select';
  }

  protected parseContent(content: string, ctx: ParseContext): SelectContent {
    const items: SelectItem[] = [];
    const body = this.getContentBody(content);

    // Split by numbered items
    const itemMatches = body.matchAll(/(\d+)\.\s+([\s\S]*?)(?=\n\d+\.|$)/g);

    for (const match of itemMatches) {
      const itemContent = match[2].trim();
      const lines = itemContent.split('\n');

      // First line is the question
      const question = lines[0].trim();

      // Parse checkbox options
      const options: Array<{ text: string; correct: boolean }> = [];
      for (const line of lines.slice(1)) {
        const checkboxMatch = line.match(/^\s*-\s*\[([ xX])\]\s*(.+)/);
        if (checkboxMatch) {
          options.push({
            text: checkboxMatch[2].trim(),
            correct: checkboxMatch[1].toLowerCase() === 'x',
          });
        }
      }

      if (question && options.length > 0) {
        items.push({ question, options });
      }
    }

    return {
      type: 'select',
      items,
    };
  }
}
