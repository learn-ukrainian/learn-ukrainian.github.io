/**
 * Section parser
 *
 * Parses module sections and PPP phases from markdown.
 *
 * Sections are identified by # headers:
 * - # Lesson Content (intro)
 * - # Presentation
 * - # Practice
 * - # Production
 * - # Summary / Підсумок
 * - # Vocabulary / Словник
 * - # Activities / Вправи
 */

import { Section, VibePhase, VibePhaseItem } from '../types';

// =============================================================================
// Section Types
// =============================================================================

type SectionType =
  | 'intro'
  | 'content'
  | 'practice'
  | 'summary'
  | 'vocabulary'
  | 'activities'
  | 'diagnostic'
  | 'analysis'
  | 'consolidation'
  | 'application';

interface SectionMapping {
  pattern: RegExp;
  type: SectionType;
  titleEn: string;
  titleUk?: string;
}

const sectionMappings: SectionMapping[] = [
  { pattern: /^# (?:Lesson Content|Вступ|Introduction)/i, type: 'intro', titleEn: 'Introduction', titleUk: 'Вступ' },
  { pattern: /^# (?:Presentation|Prezentatsiya)/i, type: 'content', titleEn: 'Presentation' },
  { pattern: /^# (?:Practice|Практика)/i, type: 'practice', titleEn: 'Practice', titleUk: 'Практика' },
  { pattern: /^# (?:Production|Produktsiya)/i, type: 'content', titleEn: 'Production' },
  { pattern: /^# (?:Diagnostic|Діагностика)/i, type: 'diagnostic', titleEn: 'Diagnostic', titleUk: 'Діагностика' },
  { pattern: /^# (?:Analysis|Аналіз)/i, type: 'analysis', titleEn: 'Analysis', titleUk: 'Аналіз' },
  { pattern: /^# (?:Consolidation|Закріплення)/i, type: 'consolidation', titleEn: 'Consolidation', titleUk: 'Закріплення' },
  { pattern: /^# (?:Application|Застосування)/i, type: 'application', titleEn: 'Application', titleUk: 'Застосування' },
  { pattern: /^# (?:Summary|Підсумок)/i, type: 'summary', titleEn: 'Summary', titleUk: 'Підсумок' },
  { pattern: /^# (?:Vocabulary|Словник)/i, type: 'vocabulary', titleEn: 'Vocabulary', titleUk: 'Словник' },
  { pattern: /^# (?:Activities|Вправи)/i, type: 'activities', titleEn: 'Activities', titleUk: 'Вправи' },
];

/**
 * Parse standard sections from module body
 */
export function parseSections(body: string): Section[] {
  const sections: Section[] = [];

  // Find all known section headers and their positions
  const foundHeaders: { index: number; mapping: SectionMapping; matchLength: number }[] = [];

  for (const mapping of sectionMappings) {
    // We need to match globally and multiline to find all occurrences
    // mapping.pattern is likely /^.../i, so we need to ensure 'gm' flags
    const flags = (mapping.pattern.flags || '') + 'gm';
    // Remove duplicate flags if any
    const uniqueFlags = Array.from(new Set(flags.split(''))).join('');

    const regex = new RegExp(mapping.pattern.source, uniqueFlags);
    let match;
    while ((match = regex.exec(body)) !== null) {
      foundHeaders.push({
        index: match.index,
        mapping: mapping,
        matchLength: match[0].length
      });
    }
  }

  // Sort by position to process in order
  foundHeaders.sort((a, b) => a.index - b.index);

  // Extract content between headers
  for (let i = 0; i < foundHeaders.length; i++) {
    const current = foundHeaders[i];
    const next = foundHeaders[i + 1];

    const startPos = current.index + current.matchLength;
    const endPos = next ? next.index : body.length;

    const content = body.slice(startPos, endPos).trim();

    sections.push({
      id: `section-${current.mapping.type}-${i}`,
      type: current.mapping.type,
      title: current.mapping.titleEn,
      titleUk: current.mapping.titleUk,
      content: content
    });
  }

  return sections;
}

// =============================================================================
// PPP/TTT Phase Parser
// =============================================================================

interface PhaseConfig {
  name: string;
  duration: number;
}

const defaultPhases: PhaseConfig[] = [
  // PPP
  { name: 'presentation', duration: 15 },
  { name: 'practice', duration: 20 },
  { name: 'production', duration: 10 },
  // TTT
  { name: 'diagnostic', duration: 10 },
  { name: 'analysis', duration: 15 },
  { name: 'consolidation', duration: 15 },
  { name: 'application', duration: 10 },
];

/**
 * Parse PPP/TTT phases from markdown body
 * Returns phases for Vibe JSON format
 */
export function parsePhases(body: string, totalDuration: number): {
  phases: VibePhase[];
  restBody: string;
} {
  const phases: VibePhase[] = [];

  // Find PPP/TTT sections
  // Looks for # or ## Header followed by content
  const phasePattern = /^(?:#|##) (Presentation|Practice|Production|Diagnostic|Analysis|Consolidation|Application)\n([\s\S]*?)(?=\n(?:#|##) (?:Presentation|Practice|Production|Diagnostic|Analysis|Consolidation|Application|Summary|Activities|Vocabulary|Словник|Підсумок|Вправи)|$)/gim;

  let restBody = body;
  let match;

  while ((match = phasePattern.exec(body)) !== null) {
    const phaseName = match[1].toLowerCase();
    const content = match[2].trim();

    // Parse items (## subsections become phase items)
    const items = parsePhaseItems(content);

    // Calculate duration (proportional to default)
    const config = defaultPhases.find(p => p.name === phaseName);
    // Default to 10 if not found, roughly scaled to 45 min lesson
    const duration = config ? Math.round((config.duration / 45) * totalDuration) : 10;

    phases.push({
      id: `phase-${phaseName}`,
      name: phaseName,
      duration,
      items,
    });

    // Remove from rest body
    restBody = restBody.replace(match[0], '');
  }

  return { phases, restBody };
}

/**
 * Parse phase items from PPP section content
 */
function parsePhaseItems(content: string): VibePhaseItem[] {
  const items: VibePhaseItem[] = [];

  // Split by ## subsections
  const parts = content.split(/(?=^## )/m).filter(Boolean);

  for (const part of parts) {
    if (part.startsWith('## ')) {
      // Check if it's an activity reference
      const activityMatch = part.match(/^## ([\w-]+):\s*(.+)/);
      if (activityMatch) {
        items.push({
          type: 'activity',
          activityId: `act-${activityMatch[1]}`,
        });
      } else {
        // Canvas/content item
        items.push({
          type: 'canvas',
          canvasData: '{}',
          teacherNotes: part.replace(/^## .+\n/, '').trim(),
        });
      }
    } else if (part.trim()) {
      // Non-headed content
      items.push({
        type: 'canvas',
        canvasData: '{}',
        teacherNotes: part.trim(),
      });
    }
  }

  // If no subsections, treat whole content as one item
  if (items.length === 0 && content.trim()) {
    items.push({
      type: 'canvas',
      canvasData: '{}',
      teacherNotes: content.trim(),
    });
  }

  return items;
}

// =============================================================================
// Exports
// =============================================================================

// export { parseSections }; // Removed duplicate
export { parseSections as parse };
