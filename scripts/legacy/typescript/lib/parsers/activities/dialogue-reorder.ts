/**
 * Dialogue reorder activity parser
 *
 * Parses dialogue reconstruction exercises:
 *
 * ## dialogue-reorder: At the café
 * > Put the dialogue in the correct order.
 *
 * - speaker: Офіціант
 *   line: Добрий день! Що будете замовляти?
 * - speaker: Клієнт
 *   line: Добрий день. Каву, будь ласка.
 * - speaker: Офіціант
 *   line: Велику чи маленьку?
 * - speaker: Клієнт
 *   line: Велику з молоком.
 */

import { ActivityParser } from './base';
import { ParseContext } from '../../types';

// =============================================================================
// Types
// =============================================================================

export interface DialogueLine {
  speaker: string;
  line: string;
}

export interface DialogueReorderContent {
  type: 'dialogue-reorder';
  lines: DialogueLine[];  // correct order
}

// =============================================================================
// Parser
// =============================================================================

export class DialogueReorderParser extends ActivityParser<DialogueReorderContent> {
  readonly type = 'dialogue-reorder' as const;

  canParse(header: string): boolean {
    const match = header.match(/^([\w-]+):\s*/);
    if (!match) return false;
    const type = match[1].toLowerCase();
    return type === 'dialogue-reorder' || type === 'reorder-dialogue' || type === 'dialogue';
  }

  protected parseContent(content: string, ctx: ParseContext): DialogueReorderContent {
    const body = this.getContentBody(content);
    const lines: DialogueLine[] = [];

    // Parse YAML-like list items
    // - speaker: Name
    //   line: Text
    const itemMatches = body.matchAll(/-\s*speaker:\s*(.+)\n\s*line:\s*(.+)/gi);

    for (const match of itemMatches) {
      lines.push({
        speaker: match[1].trim(),
        line: match[2].trim(),
      });
    }

    // Alternative format: numbered lines with speaker in brackets
    // 1. [Офіціант] Добрий день!
    if (lines.length === 0) {
      const numberedMatches = body.matchAll(/\d+\.\s*\[([^\]]+)\]\s*(.+)/g);
      for (const match of numberedMatches) {
        lines.push({
          speaker: match[1].trim(),
          line: match[2].trim(),
        });
      }
    }

    return {
      type: 'dialogue-reorder',
      lines,
    };
  }
}
