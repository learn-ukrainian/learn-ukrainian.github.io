/**
 * Match-up activity parser
 *
 * Parses matching pairs from table format:
 *
 * ## match-up: Match Title
 * > Instructions here
 *
 * | Ukrainian | English |
 * |-----------|---------|
 * | слово     | word    |
 * | книга     | book    |
 */

import { ActivityParser } from './base';
import { MatchUpContent, MatchPair, ParseContext } from '../../types';

export class MatchUpParser extends ActivityParser<MatchUpContent> {
  readonly type = 'match-up' as const;

  protected parseContent(content: string, ctx: ParseContext): MatchUpContent {
    const pairs: MatchPair[] = [];

    // Parse markdown table
    // Format: | left | right |
    const tableMatch = content.match(/\|[^\n]+\|\n\|[-|\s]+\|\n([\s\S]*?)(?=\n\n|$)/);

    if (tableMatch) {
      const rows = tableMatch[1].trim().split('\n');

      for (const row of rows) {
        const cells = row.split('|').filter(c => c.trim());
        if (cells.length >= 2) {
          const left = cells[0].trim();
          const right = cells[1].trim();

          const pair: MatchPair = { left, right };

          // Add image URLs if available in context
          if (ctx.imageMap) {
            const leftImage = ctx.imageMap.get(left.toLowerCase());
            const rightImage = ctx.imageMap.get(right.toLowerCase());
            if (leftImage) pair.leftImageUrl = leftImage;
            if (rightImage) pair.rightImageUrl = rightImage;
          }

          pairs.push(pair);
        }
      }
    }

    return {
      type: 'match-up',
      pairs,
      shuffleRight: true,
    };
  }
}
