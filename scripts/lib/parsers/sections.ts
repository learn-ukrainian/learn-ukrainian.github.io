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

type SectionType = 'intro' | 'content' | 'practice' | 'summary' | 'vocabulary' | 'activities';

interface SectionMapping {
  pattern: RegExp;
  type: SectionType;
  titleEn: string;
  titleUk?: string;
}

const sectionMappings: SectionMapping[] = [
  { pattern: /^# (?:Lesson Content|Вступ|Introduction)/i, type: 'intro', titleEn: 'Introduction', titleUk: 'Вступ' },
  { pattern: /^# Presentation/i, type: 'content', titleEn: 'Presentation' },
  { pattern: /^# (?:Practice|Практика)/i, type: 'practice', titleEn: 'Practice', titleUk: 'Практика' },
  { pattern: /^# Production/i, type: 'content', titleEn: 'Production' },
  { pattern: /^# (?:Summary|Підсумок)/i, type: 'summary', titleEn: 'Summary', titleUk: 'Підсумок' },
  { pattern: /^# (?:Vocabulary|Словник)/i, type: 'vocabulary', titleEn: 'Vocabulary', titleUk: 'Словник' },
  { pattern: /^# (?:Activities|Вправи)/i, type: 'activities', titleEn: 'Activities', titleUk: 'Вправи' },
];

// =============================================================================
// Section Parser
// =============================================================================

/**
 * Parse sections from markdown body
 */
export function parseSections(body: string): Section[] {
  const sections: Section[] = [];

  // Split by # headers (level 1)
  const parts = body.split(/(?=^# )/m).filter(Boolean);

  for (const part of parts) {
    const lines = part.trim().split('\n');
    const header = lines[0];
    const content = lines.slice(1).join('\n').trim();

    // Skip if no header or empty content
    if (!header.startsWith('# ')) continue;

    // Find matching section type
    const mapping = sectionMappings.find(m => m.pattern.test(header));

    // Extract title from header (text after "# ")
    const headerTitle = header.replace(/^# /, '').trim();

    if (mapping) {
      // Known section type
      const titleMatch = header.match(/^# [^:]+:\s*(.+)$/);
      const customTitle = titleMatch ? titleMatch[1].trim() : undefined;

      const section: Section = {
        id: `section-${mapping.type}`,
        type: mapping.type,
        title: customTitle || mapping.titleEn,
        content,
      };

      if (mapping.titleUk) {
        section.titleUk = mapping.titleUk;
      }

      sections.push(section);
    } else {
      // Unknown section - treat as 'content' type
      // This handles free-form section titles like "# Але vs Проте"
      const sectionId = headerTitle
        .toLowerCase()
        .replace(/[^a-zа-яіїєґ0-9]+/g, '-')
        .replace(/^-|-$/g, '')
        .substring(0, 30);

      sections.push({
        id: `section-${sectionId}`,
        type: 'content',
        title: headerTitle,
        content,
      });
    }
  }

  return sections;
}

// =============================================================================
// PPP Phase Parser
// =============================================================================

interface PhaseConfig {
  name: string;
  duration: number;
}

const defaultPhases: PhaseConfig[] = [
  { name: 'presentation', duration: 15 },
  { name: 'practice', duration: 20 },
  { name: 'production', duration: 10 },
];

/**
 * Parse PPP phases from markdown body
 * Returns phases for Vibe JSON format
 */
export function parsePhases(body: string, totalDuration: number): {
  phases: VibePhase[];
  restBody: string;
} {
  const phases: VibePhase[] = [];

  // Find PPP sections
  const pppPattern = /# (Presentation|Practice|Production)\n([\s\S]*?)(?=\n# (?:Presentation|Practice|Production|Summary|Activities|Vocabulary|Словник|Підсумок|Вправи)|$)/gi;

  let restBody = body;
  let match;

  while ((match = pppPattern.exec(body)) !== null) {
    const phaseName = match[1].toLowerCase();
    const content = match[2].trim();

    // Parse items (## subsections become phase items)
    const items = parsePhaseItems(content);

    // Calculate duration (proportional to default)
    const config = defaultPhases.find(p => p.name === phaseName);
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

export { parseSections as parse };
