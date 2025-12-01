/**
 * Group-sort activity parser
 *
 * Parses sorting groups with ### headers:
 *
 * ## group-sort: Sort Title
 * > Instructions here
 *
 * ### Group 1 (descriptor)
 * - item1
 * - item2
 *
 * ### Group 2 (descriptor)
 * - item3
 * - item4
 */

import { ActivityParser } from './base';
import { GroupSortContent, SortGroup, SortItem, ParseContext } from '../../types';

export class GroupSortParser extends ActivityParser<GroupSortContent> {
  readonly type = 'group-sort' as const;

  protected parseContent(content: string, ctx: ParseContext): GroupSortContent {
    const groups: SortGroup[] = [];

    // Parse ### groups
    const groupMatches = content.matchAll(/### (.+)\n([\s\S]*?)(?=\n###|$)/g);

    for (const match of groupMatches) {
      const fullName = match[1].trim();
      const itemsBlock = match[2];

      // Extract group name and optional descriptor
      // "True Friends (справжні друзі)" → name: "True Friends", nameUk: "справжні друзі"
      const nameMatch = fullName.match(/^(.+?)(?:\s*\((.+?)\))?$/);
      const name = nameMatch ? nameMatch[1].trim() : fullName;
      const nameUk = nameMatch?.[2]?.trim();

      // Parse bullet items
      const rawItems = itemsBlock.match(/-\s+(.+)/g)?.map(m => m.replace(/^-\s+/, '').trim()) || [];

      // Convert items to objects if they have images
      const items: (string | SortItem)[] = rawItems.map(item => {
        if (ctx.imageMap) {
          const itemImage = ctx.imageMap.get(item.toLowerCase());
          if (itemImage) {
            return { text: item, imageUrl: itemImage };
          }
        }
        return item;
      });

      // Generate group ID from name
      const id = name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');

      const group: SortGroup = {
        id,
        name,
        items,
      };

      if (nameUk) {
        group.nameUk = nameUk;
      }

      groups.push(group);
    }

    return {
      type: 'group-sort',
      groups,
      shuffleItems: true,
    };
  }
}
