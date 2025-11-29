#!/usr/bin/env npx ts-node
/**
 * Curricula-Opus Generator
 *
 * Parses module Markdown files and generates:
 * - Vibe-compatible JSON (output/json/)
 * - HTML preview (output/html/)
 *
 * Source: curriculum/[lang]/modules/module-XX.md
 *
 * Usage:
 *   npm run generate                    # Generate all
 *   npm run generate l2-uk-en           # Generate for Ukrainian
 *   npm run generate l2-uk-en 1         # Generate only module 01
 */

import { mkdir, writeFile, readFile, readdir } from 'fs/promises';
import { join, dirname } from 'path';
import { existsSync } from 'fs';
import * as showdown from 'showdown';

// Initialize markdown converter
const mdConverter = new showdown.Converter({
  tables: true,
  strikethrough: true,
  simpleLineBreaks: true,
});

// ============================================================================
// CONFIGURATION
// ============================================================================

const ROOT_DIR = join(__dirname, '..');
const CURRICULUM_DIR = join(ROOT_DIR, 'curriculum');
const OUTPUT_DIR = join(ROOT_DIR, 'output');
const OWNER_ID = 'curricula-opus';

// ============================================================================
// TYPES
// ============================================================================

interface ModuleFrontmatter {
  module: number;
  title: string;
  subtitle?: string;
  level: string;
  phase: string;
  duration: number;
  transliteration: string;
  tags: string[];
  objectives: string[];
  grammar: string[];
}

interface LessonPhase {
  id: string;
  name: string;
  duration: number;
  items: Array<{
    type: string;
    canvasData?: string;
    teacherNotes?: string;
    activityId?: string;
  }>;
}

interface Activity {
  id: string;
  type: string;
  title: string;
  description: string;
  content: any;
}

interface VocabWord {
  id: string;
  uk: string;
  translit: string;
  ipa: string;
  en: string;
  pos: string;
  gender?: string;
  note?: string;
}

interface LetterGroups {
  trueFriends: string[];
  falseFriends: string[];
  newLetters: string[];
}

interface ParsedModule {
  frontmatter: ModuleFrontmatter;
  phases: LessonPhase[];
  activities: Activity[];
  vocabulary: VocabWord[];
  letterGroups?: LetterGroups;
}

// ============================================================================
// UTILITIES
// ============================================================================

async function ensureDir(path: string): Promise<void> {
  if (!existsSync(path)) {
    await mkdir(path, { recursive: true });
  }
}

async function writeJSON(path: string, data: any): Promise<void> {
  await ensureDir(dirname(path));
  await writeFile(path, JSON.stringify(data, null, 2));
  console.log(`  ✓ ${path.replace(ROOT_DIR, '')}`);
}

async function writeHTML(path: string, html: string): Promise<void> {
  await ensureDir(dirname(path));
  await writeFile(path, html);
  console.log(`  ✓ ${path.replace(ROOT_DIR, '')}`);
}

function padNumber(n: number, len: number = 2): string {
  return String(n).padStart(len, '0');
}

function generateId(prefix: string, level: string, moduleNum: number, suffix?: string): string {
  const base = `${prefix}-uk-${level}-${padNumber(moduleNum)}`;
  return suffix ? `${base}-${suffix}` : base;
}

// ============================================================================
// MARKDOWN PARSER
// ============================================================================

function parseFrontmatter(content: string): { frontmatter: ModuleFrontmatter; body: string } {
  const match = content.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  if (!match) throw new Error('No frontmatter found');

  const yaml = match[1];
  const body = match[2];

  // Simple YAML parser for our structure
  const fm: any = {};
  let currentKey = '';
  let inArray = false;
  let arrayItems: string[] = [];

  for (const line of yaml.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed) continue;

    // Array item
    if (trimmed.startsWith('- ')) {
      arrayItems.push(trimmed.slice(2).trim());
      continue;
    }

    // If we were in an array, save it
    if (inArray && arrayItems.length > 0) {
      fm[currentKey] = arrayItems;
      arrayItems = [];
      inArray = false;
    }

    // Key: value
    const kvMatch = trimmed.match(/^(\w+):\s*(.*)$/);
    if (kvMatch) {
      currentKey = kvMatch[1];
      const value = kvMatch[2].trim();

      if (value === '') {
        // Array follows
        inArray = true;
      } else if (value.startsWith('[') && value.endsWith(']')) {
        // Inline array
        fm[currentKey] = value.slice(1, -1).split(',').map(s => s.trim());
      } else if (value.startsWith('"') && value.endsWith('"')) {
        fm[currentKey] = value.slice(1, -1);
      } else if (!isNaN(Number(value))) {
        fm[currentKey] = Number(value);
      } else {
        fm[currentKey] = value;
      }
    }
  }

  // Handle final array
  if (inArray && arrayItems.length > 0) {
    fm[currentKey] = arrayItems;
  }

  return { frontmatter: fm as ModuleFrontmatter, body };
}

function parsePhases(body: string, moduleNum: number): { phases: LessonPhase[]; restBody: string } {
  const phases: LessonPhase[] = [];
  const phaseNames = ['warm-up', 'presentation', 'practice', 'production'];
  const durations: Record<string, number> = {
    'warm-up': 5,
    'presentation': 15,
    'practice': 15,
    'production': 10,
  };

  // Find "# Lesson Content" section
  const lessonMatch = body.match(/# Lesson Content\n([\s\S]*?)(?=\n---|\n# Activities|$)/);
  if (!lessonMatch) return { phases: [], restBody: body };

  const lessonContent = lessonMatch[1];
  let restBody = body.replace(lessonMatch[0], '');

  // Split by ## headers
  const sections = lessonContent.split(/\n## /).filter(Boolean);

  for (const section of sections) {
    const lines = section.trim().split('\n');
    const headerLine = lines[0].toLowerCase();
    const phaseName = phaseNames.find(p => headerLine.startsWith(p));

    if (phaseName) {
      const content = lines.slice(1).join('\n').trim();
      const items: LessonPhase['items'] = [];

      // Split by ### for subsections
      const subSections = content.split(/\n### /).filter(Boolean);

      for (const sub of subSections) {
        const subLines = sub.trim().split('\n');
        const title = subLines[0].trim();
        const subContent = subLines.slice(1).join('\n').trim();

        if (subContent) {
          items.push({
            type: 'canvas',
            canvasData: '{}',
            teacherNotes: `${title}\n\n${subContent}`,
          });
        }
      }

      // If no subsections, treat whole content as one item
      if (items.length === 0 && content) {
        items.push({
          type: 'canvas',
          canvasData: '{}',
          teacherNotes: content,
        });
      }

      phases.push({
        id: `phase-${phaseName}`,
        name: phaseName,
        duration: durations[phaseName] || 10,
        items,
      });
    }
  }

  return { phases, restBody };
}

function parseActivities(body: string, level: string, moduleNum: number): { activities: Activity[]; restBody: string } {
  const activities: Activity[] = [];

  // Find "# Activities" section
  const activitiesMatch = body.match(/# Activities\n([\s\S]*?)(?=\n---|\n# Vocabulary|$)/);
  if (!activitiesMatch) return { activities: [], restBody: body };

  const activitiesContent = activitiesMatch[1];
  let restBody = body.replace(activitiesMatch[0], '');

  // Split by ## headers
  const sections = activitiesContent.split(/\n## /).filter(Boolean);

  for (const section of sections) {
    const lines = section.trim().split('\n');
    const headerMatch = lines[0].match(/^([\w-]+):\s*(.+)$/);

    if (headerMatch) {
      const type = headerMatch[1];
      const title = headerMatch[2].trim();
      const content = lines.slice(1).join('\n').trim();

      // Parse instructions (> lines at start)
      const instructionsMatch = content.match(/^>\s*(.+)$/m);
      const instructions = instructionsMatch ? instructionsMatch[1] : '';

      const actId = generateId('act', level, moduleNum, type.replace('-', ''));
      let actContent: any = { type, instructions };

      if (type === 'match-up') {
        // Parse table
        const tableMatch = content.match(/\|[^\n]+\|\n\|[-|\s]+\|\n([\s\S]*?)(?=\n\n|$)/);
        if (tableMatch) {
          const rows = tableMatch[1].trim().split('\n');
          actContent.pairs = rows.map(row => {
            const cells = row.split('|').filter(c => c.trim());
            return { left: cells[0]?.trim() || '', right: cells[1]?.trim() || '' };
          });
          actContent.shuffleRight = true;
        }
      } else if (type === 'quiz') {
        // Parse numbered questions
        const questions: any[] = [];
        const qMatches = content.matchAll(/(\d+)\.\s+(.+?)\n([\s\S]*?)(?=\n\d+\.|$)/g);

        for (const qMatch of qMatches) {
          const questionText = qMatch[2].trim();
          const optionsBlock = qMatch[3];

          const options: string[] = [];
          let correctIndex = 0;
          let explanation = '';

          // Parse options
          const optMatches = optionsBlock.matchAll(/-\s+\[([x ])\]\s+(.+)/g);
          let i = 0;
          for (const optMatch of optMatches) {
            options.push(optMatch[2].trim());
            if (optMatch[1] === 'x') correctIndex = i;
            i++;
          }

          // Parse explanation
          const expMatch = optionsBlock.match(/>\s+(.+)$/m);
          if (expMatch) explanation = expMatch[1].trim();

          questions.push({
            question: questionText,
            options,
            correctIndex,
            explanation,
          });
        }

        actContent.questions = questions;
        actContent.shuffleQuestions = true;
        actContent.shuffleOptions = true;
        actContent.showCorrectAnswers = true;
      } else if (type === 'group-sort') {
        // Parse ### groups
        const groups: any[] = [];
        const groupMatches = content.matchAll(/### (.+)\n([\s\S]*?)(?=\n###|$)/g);

        for (const gMatch of groupMatches) {
          const name = gMatch[1].trim();
          const itemsBlock = gMatch[2];
          const items = itemsBlock.match(/-\s+(.+)/g)?.map(m => m.replace(/^-\s+/, '').trim()) || [];
          groups.push({ name, items });
        }

        actContent.groups = groups;
        actContent.shuffleItems = true;
      }

      activities.push({
        id: actId,
        type,
        title,
        description: instructions || title,
        content: actContent,
      });
    }
  }

  return { activities, restBody };
}

function parseVocabulary(body: string, moduleNum: number): { vocabulary: VocabWord[]; restBody: string } {
  const vocabulary: VocabWord[] = [];

  // Find "# Vocabulary" section
  const vocabMatch = body.match(/# Vocabulary\n([\s\S]*?)(?=\n---|\n# Letter Groups|$)/);
  if (!vocabMatch) return { vocabulary: [], restBody: body };

  const vocabContent = vocabMatch[1];
  let restBody = body.replace(vocabMatch[0], '');

  // Parse table
  const tableMatch = vocabContent.match(/\|[^\n]+\|\n\|[-|\s]+\|\n([\s\S]*?)(?=\n\n|$)/);
  if (tableMatch) {
    const rows = tableMatch[1].trim().split('\n');
    let wordIndex = 1;

    for (const row of rows) {
      const cells = row.split('|').map(c => c.trim()).filter(Boolean);
      if (cells.length >= 5) {
        vocabulary.push({
          id: `v-m${padNumber(moduleNum)}-${padNumber(wordIndex, 3)}`,
          uk: cells[0] || '',
          translit: cells[1] || '',
          ipa: cells[2] || '',
          en: cells[3] || '',
          pos: cells[4] || '',
          gender: cells[5] || undefined,
          note: cells[6] || undefined,
        });
        wordIndex++;
      }
    }
  }

  return { vocabulary, restBody };
}

function parseLetterGroups(body: string): LetterGroups | undefined {
  const match = body.match(/# Letter Groups\n([\s\S]*?)$/);
  if (!match) return undefined;

  const content = match[1];
  const groups: LetterGroups = {
    trueFriends: [],
    falseFriends: [],
    newLetters: [],
  };

  const tfMatch = content.match(/## True Friends\n(.+)/);
  if (tfMatch) groups.trueFriends = tfMatch[1].trim().split(/\s+/);

  const ffMatch = content.match(/## False Friends\n(.+)/);
  if (ffMatch) groups.falseFriends = ffMatch[1].trim().split(/\s+/);

  const nlMatch = content.match(/## New Letters\n(.+)/);
  if (nlMatch) groups.newLetters = nlMatch[1].trim().split(/\s+/);

  return groups;
}

function parseModule(content: string): ParsedModule {
  const { frontmatter, body } = parseFrontmatter(content);
  const { phases, restBody: body2 } = parsePhases(body, frontmatter.module);
  const { activities, restBody: body3 } = parseActivities(body2, frontmatter.level, frontmatter.module);
  const { vocabulary } = parseVocabulary(body3, frontmatter.module);
  const letterGroups = parseLetterGroups(body3);

  return { frontmatter, phases, activities, vocabulary, letterGroups };
}

// ============================================================================
// JSON GENERATOR
// ============================================================================

function generateVibeJSON(parsed: ParsedModule, langPair: string): any {
  const { frontmatter: fm, phases, activities, vocabulary, letterGroups } = parsed;
  const now = new Date().toISOString().split('T')[0] + 'T00:00:00Z';

  // Add activity references to phases
  const phasesWithActivities = phases.map(phase => ({
    ...phase,
    items: [
      ...phase.items,
      ...activities.filter(a => {
        // Add activities to appropriate phase
        if (phase.name === 'presentation' && a.type === 'match-up') return true;
        if (phase.name === 'practice' && (a.type === 'quiz' || a.type === 'group-sort')) return true;
        return false;
      }).map(a => ({ type: 'activity', activityId: a.id })),
    ],
  }));

  return {
    $schema: '../../../schemas/vibe-module.schema.json',
    lesson: {
      id: generateId('lesson', fm.level, fm.module),
      moduleId: generateId('mod', fm.level, fm.module),
      languagePair: langPair,
      subject: 'language',
      methodology: 'ppp',
      owner: OWNER_ID,
      visibility: 'public',
      language: 'uk',
      targetLevel: fm.level,
      phase: fm.phase,
      moduleNumber: fm.module,
      title: fm.title,
      subtitle: fm.subtitle,
      description: fm.objectives?.[0] || fm.title,
      objectives: fm.objectives || [],
      grammarFocus: fm.grammar || [],
      totalDuration: fm.duration,
      transliterationMode: fm.transliteration,
      tags: fm.tags || [],
      version: 1,
      createdAt: now,
      modifiedAt: now,
      phases: phasesWithActivities,
    },
    activities: activities.map(a => ({
      ...a,
      subject: 'language',
      owner: OWNER_ID,
      visibility: 'public',
      language: 'uk',
      difficultyLevel: fm.level,
      duration: 5,
      tags: fm.tags || [],
      createdAt: now,
      modifiedAt: now,
    })),
    vocabulary: {
      moduleId: generateId('mod', fm.level, fm.module),
      level: fm.level,
      phase: fm.phase,
      wordCount: vocabulary.length,
      transliterationMode: fm.transliteration,
      ...(letterGroups ? { letterGroups } : {}),
      words: vocabulary,
    },
  };
}

// ============================================================================
// NAVIGATION TYPES
// ============================================================================

interface NavInfo {
  prevModule?: { num: number; title: string };
  nextModule?: { num: number; title: string };
  level: string;
  langPair: string;
}

// ============================================================================
// HTML GENERATOR
// ============================================================================

function generateHTML(vibeJSON: any, nav: NavInfo): string {
  const { lesson, activities, vocabulary } = vibeJSON;
  const vocab = vocabulary.words;
  const levelLower = nav.level.toLowerCase();

  const matchActivity = activities.find((a: any) => a.type === 'match-up');
  const quizActivity = activities.find((a: any) => a.type === 'quiz');
  const sortActivity = activities.find((a: any) => a.type === 'group-sort');

  const theoryContent = lesson.phases
    .flatMap((phase: any) => phase.items
      .filter((item: any) => item.type === 'canvas' && item.teacherNotes)
      .map((item: any) => {
        const lines = item.teacherNotes.split('\n');
        const title = lines[0];
        const content = lines.slice(1).join('\n').trim();
        return { title, content };
      })
    );

  // Navigation links
  const prevLink = nav.prevModule
    ? `<a href="module-${padNumber(nav.prevModule.num)}.html" class="module-nav-link">← Module ${padNumber(nav.prevModule.num)}</a>`
    : `<span class="module-nav-link disabled">← Prev</span>`;
  const nextLink = nav.nextModule
    ? `<a href="module-${padNumber(nav.nextModule.num)}.html" class="module-nav-link">Module ${padNumber(nav.nextModule.num)} →</a>`
    : `<span class="module-nav-link disabled">Next →</span>`;

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Module ${padNumber(lesson.moduleNumber)}: ${lesson.title} | Ukrainian ${lesson.targetLevel}</title>
  <style>
    :root { --primary: #1a5fb4; --primary-light: #3584e4; --success: #26a269; --warning: #e5a50a; --danger: #c01c28; --bg: #fafafa; --card-bg: #fff; --text: #1e1e1e; --text-muted: #5e5e5e; --border: #e0e0e0; }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; }
    .top-nav { background: #2e2e2e; color: white; padding: 0.5rem 2rem; display: flex; justify-content: space-between; align-items: center; font-size: 0.875rem; }
    .top-nav a { color: white; text-decoration: none; }
    .top-nav a:hover { text-decoration: underline; }
    .module-nav { display: flex; gap: 1rem; align-items: center; }
    .module-nav-link { color: rgba(255,255,255,0.8); text-decoration: none; padding: 0.25rem 0.5rem; }
    .module-nav-link:hover { color: white; }
    .module-nav-link.disabled { color: rgba(255,255,255,0.3); pointer-events: none; }
    .nav { position: sticky; top: 0; background: var(--primary); color: white; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; z-index: 100; }
    .nav h1 { font-size: 1.25rem; }
    .nav-tabs { display: flex; gap: 0.5rem; }
    .nav-tab { background: rgba(255,255,255,0.2); border: none; color: white; padding: 0.5rem 1rem; border-radius: 4px; cursor: pointer; }
    .nav-tab.active { background: white; color: var(--primary); }
    main { max-width: 1000px; margin: 0 auto; padding: 2rem; }
    .section { display: none; } .section.active { display: block; }
    .lesson-header { text-align: center; margin-bottom: 2rem; padding: 2rem; background: linear-gradient(135deg, #e8f4fd, #f0e8fd); border-radius: 12px; }
    .level-badge { background: var(--primary); color: white; padding: 0.25rem 0.75rem; border-radius: 4px; font-size: 0.875rem; }
    .card { background: var(--card-bg); border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); padding: 1.5rem; margin-bottom: 1.5rem; }
    .card h3 { color: var(--primary); margin-bottom: 1rem; }
    .canvas-note { background: #fffbeb; border-left: 4px solid var(--warning); padding: 1rem; margin: 1rem 0; border-radius: 0 8px 8px 0; }
    .canvas-note h4 { color: var(--warning); margin-bottom: 0.5rem; }
    .md-content { line-height: 1.7; }
    .md-content p { margin: 0.75rem 0; }
    .md-content ul, .md-content ol { margin: 0.75rem 0; padding-left: 1.5rem; }
    .md-content li { margin: 0.25rem 0; }
    .md-content strong { color: var(--primary); }
    .md-content blockquote { background: #e8f4fd; border-left: 4px solid var(--primary); padding: 0.75rem 1rem; margin: 1rem 0; border-radius: 0 8px 8px 0; }
    .md-content blockquote p { margin: 0.25rem 0; }
    .md-content table { width: 100%; border-collapse: collapse; margin: 1rem 0; font-size: 0.9rem; }
    .md-content th, .md-content td { border: 1px solid var(--border); padding: 0.5rem 0.75rem; text-align: left; }
    .md-content th { background: #f5f5f5; font-weight: 600; }
    .md-content code { background: #f0f0f0; padding: 0.125rem 0.375rem; border-radius: 4px; font-family: monospace; font-size: 0.9em; }
    .letter-groups { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin: 1.5rem 0; }
    .letter-group { border: 2px solid var(--border); border-radius: 8px; padding: 1rem; text-align: center; }
    .letter-group.true-friends { border-color: var(--success); } .letter-group.true-friends .letters { color: var(--success); }
    .letter-group.false-friends { border-color: var(--danger); } .letter-group.false-friends .letters { color: var(--danger); }
    .letter-group.new-letters { border-color: var(--primary); } .letter-group.new-letters .letters { color: var(--primary); }
    .letters { font-size: 1.75rem; letter-spacing: 0.3rem; }
    .match-container { display: flex; gap: 3rem; padding: 1rem; position: relative; }
    .match-column { flex: 1; display: flex; flex-direction: column; gap: 0.75rem; }
    .match-item { background: var(--card-bg); border: 2px solid var(--border); border-radius: 8px; padding: 1rem; text-align: center; font-size: 1.25rem; cursor: pointer; }
    .match-item.selected { border-color: var(--primary); background: #e8f4fd; }
    .match-item.matched { border-color: var(--success); background: #e8f8f0; }
    .match-item.wrong { border-color: var(--danger); background: #fde8e8; }
    .match-lines { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; }
    .quiz-question { border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem; }
    .quiz-question.answered { pointer-events: none; }
    .quiz-question .cyrillic { font-size: 1.5rem; color: var(--primary); font-weight: 600; }
    .quiz-options { display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.75rem; margin-top: 1rem; }
    .quiz-option { background: #f5f5f5; border: 2px solid var(--border); border-radius: 8px; padding: 1rem; cursor: pointer; text-align: center; }
    .quiz-option.correct { border-color: var(--success); background: #d4edda; }
    .quiz-option.wrong { border-color: var(--danger); background: #f8d7da; }
    .quiz-explanation { margin-top: 1rem; padding: 1rem; background: #e8f4fd; border-radius: 8px; display: none; }
    .quiz-explanation.show { display: block; }
    .sort-pool { background: #f5f5f5; border: 2px dashed var(--border); border-radius: 12px; padding: 1.5rem; min-height: 80px; margin-bottom: 1rem; }
    .sort-items { display: flex; flex-wrap: wrap; gap: 0.5rem; justify-content: center; }
    .sort-item { background: var(--card-bg); border: 2px solid var(--border); border-radius: 8px; padding: 0.75rem 1.25rem; font-size: 1.5rem; cursor: grab; }
    .sort-item.correct { border-color: var(--success); background: #e8f8f0; }
    .sort-item.wrong { border-color: var(--danger); background: #fde8e8; }
    .sort-groups { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }
    .sort-group { border: 2px solid var(--border); border-radius: 12px; padding: 1rem; min-height: 150px; }
    .sort-group.drag-over { border-color: var(--primary); background: #e8f4fd; }
    .sort-group h4 { font-size: 0.875rem; text-align: center; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 2px solid var(--border); }
    .sort-group.true-friends h4 { color: var(--success); border-color: var(--success); }
    .sort-group.false-friends h4 { color: var(--danger); border-color: var(--danger); }
    .sort-group.new-letters h4 { color: var(--primary); border-color: var(--primary); }
    .vocab-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 1rem; }
    .vocab-card { border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem; text-align: center; }
    .vocab-card .uk { font-size: 1.75rem; font-weight: 600; color: var(--primary); }
    .vocab-card .translit { color: var(--text-muted); font-style: italic; }
    .vocab-card .en { font-weight: 500; margin: 0.25rem 0; }
    .vocab-card .note { font-size: 0.75rem; color: #613583; background: #f0e8fd; padding: 0.25rem 0.5rem; border-radius: 4px; }
    .btn { padding: 0.75rem 1.5rem; border: none; border-radius: 8px; cursor: pointer; }
    .btn-primary { background: var(--primary); color: white; }
    .btn-outline { background: transparent; border: 2px solid var(--border); }
    .btn-group { display: flex; gap: 1rem; justify-content: center; margin-top: 1.5rem; }
    .score-display { text-align: center; padding: 1rem; background: linear-gradient(135deg, #e8f8f0, #e8f4fd); border-radius: 8px; margin-bottom: 1rem; }
    .score-display .score { font-size: 2rem; font-weight: 700; color: var(--success); }
    .completion-message { text-align: center; padding: 2rem; background: linear-gradient(135deg, #d4edda, #e8f4fd); border-radius: 12px; margin-top: 1rem; display: none; }
    .completion-message.show { display: block; }
    footer { text-align: center; padding: 2rem; color: var(--text-muted); }
    @media (max-width: 768px) { .nav { flex-direction: column; gap: 1rem; } .letter-groups, .sort-groups, .quiz-options { grid-template-columns: 1fr; } .match-container { flex-direction: column; } }
  </style>
</head>
<body>
  <div class="top-nav">
    <a href="../index.html">← ${nav.langPair} Curriculum</a>
    <div class="module-nav">
      ${prevLink}
      <a href="index.html" class="module-nav-link">${nav.level} Index</a>
      ${nextLink}
    </div>
  </div>
  <nav class="nav">
    <h1>Module ${padNumber(lesson.moduleNumber)}: ${lesson.title}</h1>
    <div class="nav-tabs">
      <button class="nav-tab active" data-section="lesson">Lesson</button>
      ${matchActivity ? '<button class="nav-tab" data-section="match">Match</button>' : ''}
      ${quizActivity ? '<button class="nav-tab" data-section="quiz">Quiz</button>' : ''}
      ${sortActivity ? '<button class="nav-tab" data-section="sort">Sort</button>' : ''}
      <button class="nav-tab" data-section="vocab">Vocab</button>
    </div>
  </nav>
  <main>
    <section id="lesson" class="section active">
      <div class="lesson-header">
        <span class="level-badge">${lesson.targetLevel} · ${lesson.phase}</span>
        <h2 style="font-size:2rem;margin:0.5rem 0">${lesson.title}</h2>
        ${lesson.subtitle ? `<p style="color:var(--text-muted)">${lesson.subtitle}</p>` : ''}
      </div>
      ${vocabulary.letterGroups ? `<div class="card"><h3>Letter Groups</h3><div class="letter-groups">
        <div class="letter-group true-friends"><h4>✓ True Friends</h4><p class="letters">${vocabulary.letterGroups.trueFriends?.join(' ')}</p></div>
        <div class="letter-group false-friends"><h4>⚠ False Friends</h4><p class="letters">${vocabulary.letterGroups.falseFriends?.join(' ')}</p></div>
        <div class="letter-group new-letters"><h4>★ New Letters</h4><p class="letters">${vocabulary.letterGroups.newLetters?.join(' ')}</p></div>
      </div></div>` : ''}
      <div class="card"><h3>Theory</h3>${theoryContent.map((t: any) => `<div class="canvas-note"><h4>${t.title}</h4><div class="md-content">${mdConverter.makeHtml(t.content)}</div></div>`).join('')}</div>
      <div class="btn-group"><button class="btn btn-primary" onclick="showSection('${matchActivity ? 'match' : quizActivity ? 'quiz' : 'vocab'}')">Start →</button></div>
    </section>
    ${matchActivity ? `<section id="match" class="section"><div class="card"><h3>${matchActivity.title}</h3>
      <div class="score-display"><span class="score"><span id="match-score">0</span>/${matchActivity.content.pairs.length}</span></div>
      <div class="match-container" id="match-container"><svg class="match-lines" id="match-lines"></svg>
        <div class="match-column" id="match-left">${matchActivity.content.pairs.map((p: any, i: number) => `<div class="match-item" data-pair="${i}">${p.left}</div>`).join('')}</div>
        <div class="match-column" id="match-right">${[...matchActivity.content.pairs].sort(() => Math.random() - 0.5).map((p: any, i: number) => `<div class="match-item" data-pair="${matchActivity.content.pairs.findIndex((x: any) => x.right === p.right)}">${p.right}</div>`).join('')}</div>
      </div>
      <div class="completion-message" id="match-complete"><h3>Perfect!</h3></div>
      <div class="btn-group"><button class="btn btn-outline" onclick="resetMatch()">Reset</button><button class="btn btn-primary" onclick="showSection('${quizActivity ? 'quiz' : 'vocab'}')">Next →</button></div>
    </div></section>` : ''}
    ${quizActivity ? `<section id="quiz" class="section"><div class="card"><h3>${quizActivity.title}</h3>
      <div class="score-display"><span class="score"><span id="quiz-score">0</span>/${quizActivity.content.questions.length}</span></div>
      <div id="quiz-container"></div>
      <div class="completion-message" id="quiz-complete"><h3>Complete!</h3></div>
      <div class="btn-group"><button class="btn btn-outline" onclick="resetQuiz()">Reset</button><button class="btn btn-primary" onclick="showSection('${sortActivity ? 'sort' : 'vocab'}')">Next →</button></div>
    </div></section>` : ''}
    ${sortActivity ? `<section id="sort" class="section"><div class="card"><h3>${sortActivity.title}</h3>
      <div class="score-display"><span class="score"><span id="sort-score">0</span>/${sortActivity.content.groups.reduce((a: number, g: any) => a + g.items.length, 0)}</span></div>
      <div class="sort-pool" id="sort-pool"><div class="sort-items" id="sort-items"></div></div>
      <div class="sort-groups">${sortActivity.content.groups.map((g: any, i: number) => `<div class="sort-group ${['true-friends', 'false-friends', 'new-letters'][i]}" data-group="${['true-friends', 'false-friends', 'new-letters'][i]}"><h4>${g.name.split('(')[0].trim()}</h4><div class="sort-items"></div></div>`).join('')}</div>
      <div class="completion-message" id="sort-complete"><h3>All Sorted!</h3></div>
      <div class="btn-group"><button class="btn btn-outline" onclick="resetSort()">Reset</button><button class="btn btn-primary" onclick="showSection('vocab')">Vocab →</button></div>
    </div></section>` : ''}
    <section id="vocab" class="section"><div class="card"><h3>Vocabulary (${vocab.length})</h3><div class="vocab-grid" id="vocab-grid"></div></div>
      <div class="btn-group"><button class="btn btn-primary" onclick="showSection('lesson')">← Back</button></div>
    </section>
  </main>
  <footer>Module ${padNumber(lesson.moduleNumber)} · curricula-opus</footer>
  <script>
    const matchPairs=${matchActivity ? JSON.stringify(matchActivity.content.pairs) : '[]'};
    const quizData=${quizActivity ? JSON.stringify(quizActivity.content.questions) : '[]'};
    const sortData=${sortActivity ? JSON.stringify(Object.fromEntries(sortActivity.content.groups.map((g: any, i: number) => [['true-friends', 'false-friends', 'new-letters'][i], g.items]))) : '{}'};
    const vocabData=${JSON.stringify(vocab.map((v: any) => ({ uk: v.uk, translit: v.translit, en: v.en, note: v.note || '' })))};
    const totalSort=${sortActivity ? sortActivity.content.groups.reduce((a: number, g: any) => a + g.items.length, 0) : 0};
    function showSection(id){document.querySelectorAll('.section').forEach(s=>s.classList.remove('active'));document.querySelectorAll('.nav-tab').forEach(t=>t.classList.remove('active'));document.getElementById(id)?.classList.add('active');document.querySelector('[data-section="'+id+'"]')?.classList.add('active');}
    document.querySelectorAll('.nav-tab').forEach(t=>t.addEventListener('click',()=>showSection(t.dataset.section)));
    let matchSel=null,matchScore=0,matchPairsArr=[];
    document.querySelectorAll('#match-left .match-item').forEach(item=>{item.addEventListener('click',()=>{if(item.classList.contains('matched'))return;document.querySelectorAll('#match-left .match-item').forEach(i=>i.classList.remove('selected'));item.classList.add('selected');matchSel={el:item,pair:item.dataset.pair};});});
    document.querySelectorAll('#match-right .match-item').forEach(item=>{item.addEventListener('click',()=>{if(item.classList.contains('matched')||!matchSel)return;if(matchSel.pair===item.dataset.pair){matchSel.el.classList.remove('selected');matchSel.el.classList.add('matched');item.classList.add('matched');matchPairsArr.push({left:matchSel.el,right:item});matchScore++;document.getElementById('match-score').textContent=matchScore;drawLines();if(matchScore===matchPairs.length)document.getElementById('match-complete').classList.add('show');}else{item.classList.add('wrong');setTimeout(()=>item.classList.remove('wrong'),300);}matchSel=null;});});
    function drawLines(){const svg=document.getElementById('match-lines'),c=document.getElementById('match-container');if(!svg||!c)return;const r=c.getBoundingClientRect();svg.innerHTML='';svg.setAttribute('viewBox','0 0 '+r.width+' '+r.height);matchPairsArr.forEach(p=>{const lr=p.left.getBoundingClientRect(),rr=p.right.getBoundingClientRect();const line=document.createElementNS('http://www.w3.org/2000/svg','line');line.setAttribute('x1',lr.right-r.left);line.setAttribute('y1',lr.top+lr.height/2-r.top);line.setAttribute('x2',rr.left-r.left);line.setAttribute('y2',rr.top+rr.height/2-r.top);line.setAttribute('stroke','#26a269');line.setAttribute('stroke-width','2');svg.appendChild(line);});}
    function resetMatch(){matchSel=null;matchScore=0;matchPairsArr=[];document.getElementById('match-score').textContent='0';document.getElementById('match-complete')?.classList.remove('show');document.getElementById('match-lines').innerHTML='';document.querySelectorAll('#match-container .match-item').forEach(i=>i.classList.remove('matched','selected','wrong'));}
    window.addEventListener('resize',drawLines);
    let quizScore=0,quizAns=0;
    function initQuiz(){const c=document.getElementById('quiz-container');if(!c||!quizData.length)return;c.innerHTML='';quizData.forEach((q,i)=>{const sh=[...q.options].sort(()=>Math.random()-0.5);const cor=sh.indexOf(q.options[q.correctIndex]);const div=document.createElement('div');div.className='quiz-question';div.innerHTML='<h4>Q'+(i+1)+': '+q.question+'</h4><div class="quiz-options">'+sh.map((o,j)=>'<div class="quiz-option" data-c="'+(j===cor)+'" data-q="'+i+'">'+o+'</div>').join('')+'</div><div class="quiz-explanation" id="exp-'+i+'">'+q.explanation+'</div>';c.appendChild(div);});document.querySelectorAll('.quiz-option').forEach(o=>o.addEventListener('click',handleQuiz));}
    function handleQuiz(e){const opt=e.target,q=opt.closest('.quiz-question');if(q.classList.contains('answered'))return;q.classList.add('answered');if(opt.dataset.c==='true'){opt.classList.add('correct');quizScore++;}else{opt.classList.add('wrong');q.querySelector('[data-c="true"]').classList.add('correct');}document.getElementById('exp-'+opt.dataset.q).classList.add('show');document.getElementById('quiz-score').textContent=quizScore;quizAns++;if(quizAns===quizData.length)document.getElementById('quiz-complete').classList.add('show');}
    function resetQuiz(){quizScore=0;quizAns=0;document.getElementById('quiz-score').textContent='0';document.getElementById('quiz-complete')?.classList.remove('show');initQuiz();}
    let sortScore=0,dragItem=null;
    function initSort(){const pool=document.getElementById('sort-items');if(!pool||!Object.keys(sortData).length)return;const all=Object.values(sortData).flat().sort(()=>Math.random()-0.5);pool.innerHTML='';all.forEach(letter=>{const group=Object.keys(sortData).find(g=>sortData[g].includes(letter));const item=document.createElement('div');item.className='sort-item';item.textContent=letter;item.draggable=true;item.dataset.group=group;item.addEventListener('dragstart',e=>{dragItem=item;item.classList.add('dragging');});item.addEventListener('dragend',()=>{item.classList.remove('dragging');dragItem=null;});pool.appendChild(item);});document.querySelectorAll('.sort-group').forEach(g=>{g.addEventListener('dragover',e=>{e.preventDefault();g.classList.add('drag-over');});g.addEventListener('dragleave',()=>g.classList.remove('drag-over'));g.addEventListener('drop',e=>{e.preventDefault();g.classList.remove('drag-over');if(!dragItem)return;if(g.dataset.group===dragItem.dataset.group){dragItem.classList.add('correct');g.querySelector('.sort-items').appendChild(dragItem);dragItem.draggable=false;sortScore++;document.getElementById('sort-score').textContent=sortScore;if(sortScore===totalSort)document.getElementById('sort-complete').classList.add('show');}else{dragItem.classList.add('wrong');setTimeout(()=>dragItem.classList.remove('wrong'),300);}});});}
    function resetSort(){sortScore=0;document.getElementById('sort-score').textContent='0';document.getElementById('sort-complete')?.classList.remove('show');document.querySelectorAll('.sort-group .sort-items').forEach(g=>g.innerHTML='');initSort();}
    function initVocab(){const grid=document.getElementById('vocab-grid');if(!grid)return;grid.innerHTML='';vocabData.forEach(v=>{const card=document.createElement('div');card.className='vocab-card';card.innerHTML='<div class="uk">'+v.uk+'</div><div class="translit">'+v.translit+'</div><div class="en">'+v.en+'</div>'+(v.note?'<div class="note">'+v.note+'</div>':'');grid.appendChild(card);});}
    document.addEventListener('DOMContentLoaded',()=>{initQuiz();initSort();initVocab();});
  </script>
</body>
</html>`;
}

// ============================================================================
// INDEX PAGE GENERATORS
// ============================================================================

function generateLevelIndex(modules: Array<{ num: number; title: string; subtitle?: string; phase: string; duration?: number; tags?: string[] }>, level: string, langPair: string): string {
  // Define phase colors
  const phaseColors: Record<string, { bg: string; accent: string; light: string }> = {
    'A1.1': { bg: '#059669', accent: '#10b981', light: '#d1fae5' },
    'A1.2': { bg: '#0891b2', accent: '#06b6d4', light: '#cffafe' },
    'A1.3': { bg: '#0284c7', accent: '#0ea5e9', light: '#e0f2fe' },
    'A2.1': { bg: '#2563eb', accent: '#3b82f6', light: '#dbeafe' },
    'A2.2': { bg: '#7c3aed', accent: '#8b5cf6', light: '#ede9fe' },
    'A2.3': { bg: '#9333ea', accent: '#a855f7', light: '#f3e8ff' },
    'A2+.1': { bg: '#be185d', accent: '#ec4899', light: '#fce7f3' },
    'A2+.2': { bg: '#9d174d', accent: '#f472b6', light: '#fce7f3' },
    'A2+.3': { bg: '#831843', accent: '#fb7185', light: '#ffe4e6' },
    'B1.1': { bg: '#c026d3', accent: '#d946ef', light: '#fae8ff' },
    'B1.2': { bg: '#db2777', accent: '#ec4899', light: '#fce7f3' },
  };
  const defaultColor = { bg: '#6b7280', accent: '#9ca3af', light: '#f3f4f6' };

  // Group modules by phase
  const phases = [...new Set(modules.map(m => m.phase))];

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${level} Modules | Ukrainian for English Speakers</title>
  <style>
    :root {
      --primary: #1a5fb4;
      --bg: #f8fafc;
      --card-bg: #fff;
      --text: #1e293b;
      --text-muted: #64748b;
      --border: #e2e8f0;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; }

    .top-nav { background: #1e293b; color: white; padding: 0.75rem 2rem; font-size: 0.875rem; }
    .top-nav a { color: white; text-decoration: none; opacity: 0.9; }
    .top-nav a:hover { opacity: 1; text-decoration: underline; }

    header { background: linear-gradient(135deg, #1e40af, #7c3aed); color: white; padding: 3rem 2rem; text-align: center; }
    header h1 { font-size: 2.75rem; margin-bottom: 0.5rem; font-weight: 700; }
    header p { opacity: 0.9; font-size: 1.125rem; }

    main { max-width: 1200px; margin: 0 auto; padding: 2rem; }

    .phase-section { margin-bottom: 3rem; }
    .phase-header {
      display: flex;
      align-items: center;
      gap: 1rem;
      margin-bottom: 1.5rem;
      padding-bottom: 0.75rem;
      border-bottom: 2px solid var(--border);
    }
    .phase-header h2 {
      font-size: 1.25rem;
      font-weight: 600;
      color: var(--text);
    }
    .phase-count {
      background: var(--border);
      color: var(--text-muted);
      padding: 0.25rem 0.75rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 500;
    }

    .tile-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 1.25rem;
    }

    .tile {
      background: var(--card-bg);
      border-radius: 16px;
      overflow: hidden;
      text-decoration: none;
      color: inherit;
      transition: transform 0.2s, box-shadow 0.2s;
      box-shadow: 0 1px 3px rgba(0,0,0,0.08);
      display: flex;
      flex-direction: column;
    }
    .tile:hover {
      transform: translateY(-4px);
      box-shadow: 0 12px 24px rgba(0,0,0,0.12);
    }

    .tile-header {
      padding: 1.25rem 1.25rem 1rem;
      display: flex;
      align-items: flex-start;
      gap: 1rem;
    }
    .tile-num {
      width: 48px;
      height: 48px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 1.125rem;
      color: white;
      flex-shrink: 0;
    }
    .tile-titles {
      flex: 1;
      min-width: 0;
    }
    .tile-title {
      font-size: 1rem;
      font-weight: 600;
      color: var(--text);
      margin-bottom: 0.25rem;
      line-height: 1.3;
    }
    .tile-subtitle {
      font-size: 0.875rem;
      color: var(--text-muted);
      line-height: 1.4;
    }

    .tile-footer {
      padding: 0.875rem 1.25rem;
      background: #f8fafc;
      border-top: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-top: auto;
    }
    .tile-phase {
      font-size: 0.75rem;
      font-weight: 600;
      padding: 0.25rem 0.625rem;
      border-radius: 6px;
    }
    .tile-meta {
      font-size: 0.75rem;
      color: var(--text-muted);
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .tile-meta svg {
      width: 14px;
      height: 14px;
      opacity: 0.6;
    }

    footer { text-align: center; padding: 3rem 2rem; color: var(--text-muted); font-size: 0.875rem; }

    @media (max-width: 640px) {
      .tile-grid { grid-template-columns: 1fr; }
      header { padding: 2rem 1rem; }
      header h1 { font-size: 2rem; }
      main { padding: 1.5rem 1rem; }
    }
  </style>
</head>
<body>
  <div class="top-nav">
    <a href="../index.html">← ${langPair} Curriculum</a>
  </div>
  <header>
    <h1>Level ${level}</h1>
    <p>Ukrainian for English Speakers · ${modules.length} Modules</p>
  </header>
  <main>
    ${phases.map(phase => {
      const phaseModules = modules.filter(m => m.phase === phase);
      const colors = phaseColors[phase] || defaultColor;
      return `
    <section class="phase-section">
      <div class="phase-header">
        <h2>${phase}</h2>
        <span class="phase-count">${phaseModules.length} modules</span>
      </div>
      <div class="tile-grid">
        ${phaseModules.map(m => {
          const c = phaseColors[m.phase] || defaultColor;
          return `
        <a href="module-${padNumber(m.num)}.html" class="tile">
          <div class="tile-header">
            <div class="tile-num" style="background: ${c.bg};">${padNumber(m.num)}</div>
            <div class="tile-titles">
              <div class="tile-title">${m.title}</div>
              ${m.subtitle ? `<div class="tile-subtitle">${m.subtitle}</div>` : ''}
            </div>
          </div>
          <div class="tile-footer">
            <span class="tile-phase" style="background: ${c.light}; color: ${c.bg};">${m.phase}</span>
            <span class="tile-meta">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              ${m.duration || 45} min
            </span>
          </div>
        </a>`;
        }).join('')}
      </div>
    </section>`;
    }).join('')}
  </main>
  <footer>curricula-opus · ${level}</footer>
</body>
</html>`;
}

function generateCurriculumIndex(levels: Array<{ level: string; moduleCount: number }>, langPair: string): string {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Ukrainian for English Speakers | Curriculum</title>
  <style>
    :root { --primary: #1a5fb4; --bg: #fafafa; --card-bg: #fff; --text: #1e1e1e; --text-muted: #5e5e5e; --border: #e0e0e0; }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; }
    header { background: linear-gradient(135deg, #1a5fb4, #613583); color: white; padding: 4rem 2rem; text-align: center; }
    header h1 { font-size: 2.5rem; margin-bottom: 0.5rem; }
    header p { opacity: 0.9; font-size: 1.125rem; }
    main { max-width: 700px; margin: 0 auto; padding: 2rem; }
    .level-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; }
    .level-card { background: var(--card-bg); border: 2px solid var(--border); border-radius: 16px; padding: 2rem; text-align: center; text-decoration: none; color: inherit; transition: all 0.2s; }
    .level-card:hover { border-color: var(--primary); transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.1); }
    .level-card h2 { font-size: 2rem; color: var(--primary); margin-bottom: 0.5rem; }
    .level-card p { color: var(--text-muted); }
    footer { text-align: center; padding: 2rem; color: var(--text-muted); }
  </style>
</head>
<body>
  <header>
    <h1>🇺🇦 Ukrainian</h1>
    <p>for English Speakers</p>
  </header>
  <main>
    <div class="level-grid">
      ${levels.map(l => `
      <a href="${l.level.toLowerCase()}/index.html" class="level-card">
        <h2>${l.level}</h2>
        <p>${l.moduleCount} modules</p>
      </a>`).join('')}
    </div>
  </main>
  <footer>curricula-opus</footer>
</body>
</html>`;
}

// Generate root index (all curricula)
function generateRootIndex(curricula: { langPair: string; name: string; levels: { level: string; count: number }[] }[]): string {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Curricula Opus</title>
  <style>
    :root { --primary: #1a5fb4; --bg: #fafafa; --card-bg: #fff; --text: #1e1e1e; --text-muted: #5e5e5e; --border: #e0e0e0; }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; }
    header { background: linear-gradient(135deg, #1a5fb4, #613583); color: white; padding: 4rem 2rem; text-align: center; }
    header h1 { font-size: 2.5rem; margin-bottom: 0.5rem; }
    header p { opacity: 0.9; font-size: 1.125rem; }
    main { max-width: 700px; margin: 0 auto; padding: 2rem; }
    .curriculum-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; }
    .curriculum-card { background: var(--card-bg); border: 2px solid var(--border); border-radius: 16px; padding: 2rem; text-decoration: none; color: inherit; transition: all 0.2s; }
    .curriculum-card:hover { border-color: var(--primary); transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.1); }
    .curriculum-card h2 { font-size: 1.5rem; color: var(--primary); margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.5rem; }
    .curriculum-card p { color: var(--text-muted); }
    .badge { background: #e8f4fd; color: var(--primary); padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem; }
    footer { text-align: center; padding: 2rem; color: var(--text-muted); }
    footer a { color: var(--primary); }
  </style>
</head>
<body>
  <header>
    <h1>Curricula Opus</h1>
    <p>Open Language Learning Curricula</p>
  </header>
  <main>
    <div class="curriculum-grid">
      ${curricula.map(c => `<a href="${c.langPair}/index.html" class="curriculum-card">
        <h2>${c.name}</h2>
        <p>For English Speakers</p>
        <p style="margin-top: 1rem;">${c.levels.map(l => `<span class="badge">${l.level}</span> ${l.count} modules`).join(' ')}</p>
      </a>`).join('\n      ')}
    </div>
  </main>
  <footer>
    <p>Open source curriculum - <a href="https://github.com/krisztiankoos/curricula-opus">GitHub</a></p>
  </footer>
</body>
</html>`;
}

// ============================================================================
// MAIN
// ============================================================================

interface ModuleInfo {
  num: number;
  level: string;
  title: string;
  subtitle?: string;
  phase: string;
  duration?: number;
  parsed: ParsedModule;
  vibeJSON: any;
}

async function main() {
  const args = process.argv.slice(2);
  const targetLangPair = args[0];
  const targetModule = args[1] ? parseInt(args[1], 10) : null;

  console.log('\n🚀 Curricula-Opus Generator\n');
  console.log('Source: curriculum/[lang]/modules/*.md');
  console.log('Output: output/json/ + output/html/\n');

  const langPairs = targetLangPair
    ? [targetLangPair]
    : (await readdir(CURRICULUM_DIR)).filter(f => f.startsWith('l'));

  // Collect info for root index
  const allCurricula: { langPair: string; name: string; levels: { level: string; count: number }[] }[] = [];

  for (const langPair of langPairs) {
    console.log(`📚 Processing ${langPair}...`);

    const modulesDir = join(CURRICULUM_DIR, langPair, 'modules');
    if (!existsSync(modulesDir)) {
      console.log(`  ⚠ No modules directory, skipping...`);
      continue;
    }

    const mdFiles = (await readdir(modulesDir))
      .filter(f => f.startsWith('module-') && f.endsWith('.md'))
      .sort();

    // First pass: parse all modules and collect info
    const modules: ModuleInfo[] = [];

    for (const mdFile of mdFiles) {
      const moduleNum = parseInt(mdFile.match(/module-(\d+)/)?.[1] || '0', 10);
      if (targetModule && moduleNum !== targetModule) continue;

      try {
        const mdPath = join(modulesDir, mdFile);
        const mdContent = await readFile(mdPath, 'utf-8');
        const parsed = parseModule(mdContent);
        const vibeJSON = generateVibeJSON(parsed, langPair);

        modules.push({
          num: moduleNum,
          level: parsed.frontmatter.level,
          title: parsed.frontmatter.title,
          subtitle: parsed.frontmatter.subtitle,
          phase: parsed.frontmatter.phase,
          duration: parsed.frontmatter.duration,
          parsed,
          vibeJSON,
        });
      } catch (error) {
        console.error(`  ⚠ Error parsing ${mdFile}:`, error);
      }
    }

    // Group modules by level
    const modulesByLevel = new Map<string, ModuleInfo[]>();
    for (const mod of modules) {
      const levelMods = modulesByLevel.get(mod.level) || [];
      levelMods.push(mod);
      modulesByLevel.set(mod.level, levelMods);
    }

    // Second pass: generate files with navigation
    for (const [level, levelModules] of modulesByLevel) {
      const levelLower = level.toLowerCase();
      levelModules.sort((a, b) => a.num - b.num);

      console.log(`\n  📁 Level ${level} (${levelModules.length} modules)`);

      for (let i = 0; i < levelModules.length; i++) {
        const mod = levelModules[i];
        const prevMod = i > 0 ? levelModules[i - 1] : undefined;
        const nextMod = i < levelModules.length - 1 ? levelModules[i + 1] : undefined;

        console.log(`    📦 Module ${padNumber(mod.num)}: ${mod.title}`);

        // Generate Vibe JSON
        await writeJSON(
          join(OUTPUT_DIR, 'json', langPair, levelLower, `module-${padNumber(mod.num)}.json`),
          mod.vibeJSON
        );

        // Generate HTML with navigation
        const nav: NavInfo = {
          prevModule: prevMod ? { num: prevMod.num, title: prevMod.title } : undefined,
          nextModule: nextMod ? { num: nextMod.num, title: nextMod.title } : undefined,
          level,
          langPair,
        };
        const html = generateHTML(mod.vibeJSON, nav);
        await writeHTML(
          join(OUTPUT_DIR, 'html', langPair, levelLower, `module-${padNumber(mod.num)}.html`),
          html
        );
      }

      // Generate level index
      const levelIndex = generateLevelIndex(
        levelModules.map(m => ({ num: m.num, title: m.title, subtitle: m.subtitle, phase: m.phase, duration: m.duration })),
        level,
        langPair
      );
      await writeHTML(join(OUTPUT_DIR, 'html', langPair, levelLower, 'index.html'), levelIndex);
    }

    // Generate curriculum index
    const levels = Array.from(modulesByLevel.entries())
      .map(([level, mods]) => ({ level, moduleCount: mods.length }))
      .sort((a, b) => a.level.localeCompare(b.level));

    if (levels.length > 0) {
      const curriculumIndex = generateCurriculumIndex(levels, langPair);
      await writeHTML(join(OUTPUT_DIR, 'html', langPair, 'index.html'), curriculumIndex);

      // Collect for root index
      const langName = langPair === 'l2-uk-en' ? 'Ukrainian' : langPair;
      allCurricula.push({
        langPair,
        name: langName,
        levels: levels.map(l => ({ level: l.level, count: l.moduleCount }))
      });
    }
  }

  // Generate root index
  if (allCurricula.length > 0) {
    const rootIndex = generateRootIndex(allCurricula);
    await writeHTML(join(OUTPUT_DIR, 'html', 'index.html'), rootIndex);
    console.log(`  ✓ /output/html/index.html`);
  }

  console.log('\n✅ Generation complete!\n');
}

main().catch(console.error);
