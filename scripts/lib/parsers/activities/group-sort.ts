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
 *
 * Also handles **Bold:** format:
 *
 * **Group 1 (descriptor):**
 * - item1
 * - item2
 *
 * Also handles markdown table format:
 *
 * | Group 1 | Group 2 | Group 3 |
 * |---------|---------|---------|
 * | item1   | item4   | item7   |
 * | item2   | item5   | item8   |
 *
 * Also handles labeled-item format:
 *
 * **group1 | group2 | group3**
 * - item1 | group1
 * - item2 | group2
 */

import { ActivityParser } from './base';
import { GroupSortContent, SortGroup, SortItem, ParseContext } from '../../types';

/**
 *
 */
export class GroupSortParser extends ActivityParser<GroupSortContent> {
  readonly type = 'group-sort' as const;

  /**
   *
   */
  protected parseContent(content: string, ctx: ParseContext): GroupSortContent {
    const groups: SortGroup[] = [];

    // Try labeled-item format: **group1 | group2** followed by - item | group
    const labeledMatch = content.match(/\*\*([^*]+\|[^*]+)\*\*\n([\s\S]*?)(?=\n\n|$)/);
    if (labeledMatch && content.match(/^-\s+.+\s*\|\s*.+$/m)) {
      return this.parseLabeledFormat(labeledMatch[1], labeledMatch[2], ctx);
    }

    // Try table format (| Header1 | Header2 |)
    const tableMatch = content.match(/\|([^\n]+)\|\n\|[-|\s]+\|\n([\s\S]*?)(?=\n\n|$)/);
    if (tableMatch) {
      return this.parseTableFormat(tableMatch[1], tableMatch[2], ctx);
    }

    // Try ### header format
    let groupMatches = [...content.matchAll(/### (.+)\n([\s\S]*?)(?=\n###|$)/g)];

    // If no ### groups found, try **Bold:** format
    if (groupMatches.length === 0) {
      groupMatches = [...content.matchAll(/\*\*(.+?):\*\*\n([\s\S]*?)(?=\n\*\*|$)/g)];
    }

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

  /**
   * Parse markdown table format:
   * | Group 1 | Group 2 | Group 3 |
   * |---------|---------|---------|
   * | item1   | item4   | item7   |
   * | item2   | item5   | item8   |
   */
  private parseTableFormat(headerLine: string, bodyLines: string, ctx: ParseContext): GroupSortContent {
    // Parse header row to get group names
    const headers = headerLine.split('|').map(h => h.trim()).filter(Boolean);

    // Initialize groups
    const groups: SortGroup[] = headers.map(header => {
      const nameMatch = header.match(/^(.+?)(?:\s*\((.+?)\))?$/);
      const name = nameMatch ? nameMatch[1].trim() : header;
      const nameUk = nameMatch?.[2]?.trim();
      const id = name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');

      const group: SortGroup = {
        id,
        name,
        items: [],
      };

      if (nameUk) {
        group.nameUk = nameUk;
      }

      return group;
    });

    // Parse body rows
    const rows = bodyLines.trim().split('\n');
    for (const row of rows) {
      const cells = row.split('|').map(c => c.trim()).filter(Boolean);

      cells.forEach((cell, colIndex) => {
        if (colIndex < groups.length && cell) {
          // Handle imageMap if present
          if (ctx.imageMap) {
            const itemImage = ctx.imageMap.get(cell.toLowerCase());
            if (itemImage) {
              groups[colIndex].items.push({ text: cell, imageUrl: itemImage });
              return;
            }
          }
          groups[colIndex].items.push(cell);
        }
      });
    }

    return {
      type: 'group-sort',
      groups,
      shuffleItems: true,
    };
  }

  /**
   * Parse labeled-item format:
   * **group1 | group2 | group3**
   * - item1 | group1
   * - item2 | group2
   */
  private parseLabeledFormat(headerLine: string, bodyLines: string, ctx: ParseContext): GroupSortContent {
    // Parse header to get group names
    const groupNames = headerLine.split('|').map(g => g.trim()).filter(Boolean);

    // Initialize groups
    const groupMap = new Map<string, SortGroup>();
    const groups: SortGroup[] = groupNames.map(name => {
      const id = name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
      const group: SortGroup = {
        id,
        name,
        items: [],
      };
      groupMap.set(name.toLowerCase(), group);
      return group;
    });

    // Parse items: - item | groupName
    const itemMatches = bodyLines.matchAll(/^-\s+(.+?)\s*\|\s*(.+)$/gm);

    for (const match of itemMatches) {
      const itemText = match[1].trim();
      const groupName = match[2].trim().toLowerCase();

      const group = groupMap.get(groupName);
      if (group) {
        // Handle imageMap if present
        if (ctx.imageMap) {
          const itemImage = ctx.imageMap.get(itemText.toLowerCase());
          if (itemImage) {
            group.items.push({ text: itemText, imageUrl: itemImage });
            continue;
          }
        }
        group.items.push(itemText);
      }
    }

    return {
      type: 'group-sort',
      groups,
      shuffleItems: true,
    };
  }
}
