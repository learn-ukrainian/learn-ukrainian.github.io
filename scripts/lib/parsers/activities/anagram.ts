/**
 * Anagram activity parser
 *
 * Parses letter reordering exercises (single words):
 *
 * ## anagram: Word Spelling
 * > Arrange the letters to form the correct word.
 *
 * 1. а м м а
 *    > [!answer] мама
 *    > (mom)
 *
 * 2. о т а т
 *    > [!answer] тато
 *    > (dad)
 */

import { ActivityParser } from './base';
import { ParseContext } from '../../types';

export interface AnagramItem {
  letters: string[];
  answer: string;
  translation?: string;
}

export interface AnagramContent {
  type: 'anagram';
  isAnagram: true;
  items: AnagramItem[];
}

export class AnagramParser extends ActivityParser<AnagramContent> {
  readonly type = 'anagram' as const;

  canParse(header: string): boolean {
    const match = header.match(/^([\w-]+):\s*/);
    if (!match) return false;
    const type = match[1].toLowerCase();
    return type === 'anagram' || type === 'letter-scramble' || type === 'word-scramble';
  }

  protected parseContent(content: string, ctx: ParseContext): AnagramContent {
    const items: AnagramItem[] = [];
    const body = this.getContentBody(content);

    // Split by numbered items
    const itemMatches = body.matchAll(/(\d+)\.\s+([\s\S]*?)(?=\n\d+\.|$)/g);

    for (const match of itemMatches) {
      const itemContent = match[2].trim();
      const lines = itemContent.split('\n');

      // First line has scrambled letters: "а м м а"
      const scrambledLine = lines[0].trim();
      const letters = scrambledLine.split(/[\s\/]+/).map(l => l.trim()).filter(Boolean);

      // Parse answer from callout
      const answerLines = lines.slice(1).join('\n');
      const { answer } = this.parseAnswerBlock(answerLines);

      // Extract translation from parentheses: > (mom)
      let translation: string | undefined;
      const transMatch = answerLines.match(/>\s*\(([^)]+)\)/);
      if (transMatch) {
        translation = transMatch[1].trim();
      }

      if (letters.length > 0) {
        items.push({
          letters,
          answer: answer || letters.join(''),
          translation,
        });
      }
    }

    return {
      type: 'anagram',
      isAnagram: true,
      items,
    };
  }
}
