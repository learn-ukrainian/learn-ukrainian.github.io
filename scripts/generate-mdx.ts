#!/usr/bin/env npx ts-node
/**
 * MDX Generator for Docusaurus (With Activity Parsing)
 * 
 * Converts curriculum markdown modules to MDX format for Docusaurus.
 * Parses activity sections and converts them to React components.
 * 
 * Usage:
 *   npx ts-node scripts/generate-mdx.ts [langPair] [level] [moduleNum]
 */

import * as fs from 'fs/promises';
import * as path from 'path';
import * as yaml from 'js-yaml';

const CURRICULUM_DIR = path.join(__dirname, '..', 'curriculum');
const DOCUSAURUS_DIR = path.join(__dirname, '..', 'docusaurus', 'docs');

// ============================================================================
// UTILITIES
// ============================================================================

async function ensureDir(dirPath: string): Promise<void> {
    await fs.mkdir(dirPath, { recursive: true });
}

function escapeJsxString(text: string): string {
    if (!text) return '';
    // Escape for template literal usage: `${...}`
    // We need to escape backticks and ${} sequences
    return text
        .replace(/\\/g, '\\\\')
        .replace(/`/g, '\\`')
        .replace(/\$\{/g, '\\${');
}

function wrapForJsx(text: string): string {
    // Wrap in backticks for JSX expression
    return '{`' + escapeJsxString(text) + '`}';
}

// ============================================================================
// FRONTMATTER PARSER
// ============================================================================

function parseFrontmatter(content: string): { frontmatter: any; body: string } {
    const lines = content.split('\n');
    if (lines[0] !== '---') {
        return { frontmatter: {}, body: content };
    }

    let endIndex = -1;
    for (let i = 1; i < lines.length; i++) {
        if (lines[i] === '---') {
            endIndex = i;
            break;
        }
    }

    if (endIndex === -1) {
        return { frontmatter: {}, body: content };
    }

    const yamlContent = lines.slice(1, endIndex).join('\n');
    const body = lines.slice(endIndex + 1).join('\n');

    try {
        const frontmatter = yaml.load(yamlContent) as any;
        return { frontmatter: frontmatter || {}, body };
    } catch (e) {
        return { frontmatter: {}, body: content };
    }
}

// ============================================================================
// ACTIVITY PARSERS
// ============================================================================

interface ParsedQuizQuestion {
    question: string;
    options: string[];
    correctIndex: number;
    explanation: string;
}

interface ParsedMatchPair {
    left: string;
    right: string;
}

function parseQuizActivity(activityContent: string): ParsedQuizQuestion[] {
    const questions: ParsedQuizQuestion[] = [];

    // Split by numbered questions
    const questionBlocks = activityContent.split(/\n\d+\.\s+/).filter(Boolean);

    for (const block of questionBlocks) {
        const lines = block.trim().split('\n');
        if (lines.length < 2) continue;

        const question = lines[0].replace(/\*\*/g, '').trim();
        const options: string[] = [];
        let correctIndex = 0;
        let explanation = '';

        for (let i = 1; i < lines.length; i++) {
            const line = lines[i].trim();

            if (line.startsWith('- [x]')) {
                correctIndex = options.length;
                options.push(line.replace('- [x]', '').trim());
            } else if (line.startsWith('- [ ]')) {
                options.push(line.replace('- [ ]', '').trim());
            } else if (line.startsWith('>')) {
                explanation = line.replace(/^>\s*/, '').trim();
            }
        }

        if (question && options.length > 0) {
            questions.push({ question, options, correctIndex, explanation });
        }
    }

    return questions;
}

function parseMatchUpActivity(activityContent: string): ParsedMatchPair[] {
    const pairs: ParsedMatchPair[] = [];

    // Find the table
    const tableMatch = activityContent.match(/\|[^\n]+\|\n\|[-\s|]+\|\n((?:\|[^\n]+\|\n?)+)/);
    if (!tableMatch) return pairs;

    const rows = tableMatch[1].trim().split('\n');
    for (const row of rows) {
        const cells = row.split('|').filter(c => c.trim());
        if (cells.length >= 2) {
            pairs.push({
                left: cells[0].trim(),
                right: cells[1].trim()
            });
        }
    }

    return pairs;
}

interface ParsedFillInItem {
    prompt: string;
    answer: string;
    options: string[];
}

function parseFillInActivity(activityContent: string): ParsedFillInItem[] {
    const items: ParsedFillInItem[] = [];

    // Split by numbered items
    const itemBlocks = activityContent.split(/\n\d+\.\s+/).filter(Boolean);

    for (const block of itemBlocks) {
        const lines = block.trim().split('\n');
        if (lines.length < 2) continue;

        const prompt = lines[0].trim();
        let answer = '';
        let options: string[] = [];

        for (const line of lines.slice(1)) {
            const trimmed = line.trim();
            if (trimmed.startsWith('> [!answer]')) {
                answer = trimmed.replace('> [!answer]', '').trim();
            } else if (trimmed.startsWith('> [!options]')) {
                options = trimmed.replace('> [!options]', '').split('|').map(o => o.trim());
            }
        }

        if (prompt && answer) {
            items.push({ prompt, answer, options });
        }
    }

    return items;
}

interface ParsedGroupSort {
    groups: { [key: string]: string[] };
}

function parseGroupSortActivity(activityContent: string): ParsedGroupSort {
    const groups: { [key: string]: string[] } = {};

    // Split by ### headers
    const groupBlocks = activityContent.split(/\n###\s+/).filter(Boolean);

    for (const block of groupBlocks) {
        const lines = block.trim().split('\n');
        if (lines.length < 2) continue;

        const groupName = lines[0].trim();
        const items: string[] = [];

        for (const line of lines.slice(1)) {
            const trimmed = line.trim();
            if (trimmed.startsWith('-')) {
                items.push(trimmed.replace(/^-\s*/, '').trim());
            }
        }

        if (groupName && items.length > 0) {
            groups[groupName] = items;
        }
    }

    return { groups };
}

interface ParsedAnagramItem {
    scrambled: string;
    answer: string;
    hint: string;
}

function parseAnagramActivity(activityContent: string): ParsedAnagramItem[] {
    const items: ParsedAnagramItem[] = [];

    const itemBlocks = activityContent.split(/\n\d+\.\s+/).filter(Boolean);

    for (const block of itemBlocks) {
        const lines = block.trim().split('\n');
        if (lines.length < 2) continue;

        const scrambled = lines[0].trim();
        let answer = '';
        let hint = '';

        for (const line of lines.slice(1)) {
            const trimmed = line.trim();
            if (trimmed.startsWith('> [!answer]')) {
                answer = trimmed.replace('> [!answer]', '').trim();
            } else if (trimmed.startsWith('> (')) {
                hint = trimmed.replace('> (', '').replace(')', '').trim();
            }
        }

        if (scrambled && answer) {
            items.push({ scrambled, answer, hint });
        }
    }

    return items;
}

interface ParsedUnjumbleItem {
    words: string;
    answer: string;
    hint: string;
}

function parseUnjumbleActivity(activityContent: string): ParsedUnjumbleItem[] {
    const items: ParsedUnjumbleItem[] = [];

    const itemBlocks = activityContent.split(/\n\d+\.\s+/).filter(Boolean);

    for (const block of itemBlocks) {
        const lines = block.trim().split('\n');
        if (lines.length < 2) continue;

        const words = lines[0].trim();
        let answer = '';
        let hint = '';

        for (const line of lines.slice(1)) {
            const trimmed = line.trim();
            if (trimmed.startsWith('> [!answer]')) {
                answer = trimmed.replace('> [!answer]', '').trim();
            } else if (trimmed.startsWith('> (')) {
                hint = trimmed.replace('> (', '').replace(')', '').trim();
            }
        }

        if (words && answer) {
            items.push({ words, answer, hint });
        }
    }

    return items;
}

interface ParsedTrueFalseItem {
    statement: string;
    isTrue: boolean;
    explanation: string;
}

function parseTrueFalseActivity(activityContent: string): ParsedTrueFalseItem[] {
    const items: ParsedTrueFalseItem[] = [];

    // Split by checkbox items: - [x] or - [ ]
    const lines = activityContent.split('\n');
    let currentItem: Partial<ParsedTrueFalseItem> | null = null;

    for (const line of lines) {
        const trimmed = line.trim();

        if (trimmed.startsWith('- [x]')) {
            // Save previous item if exists
            if (currentItem && currentItem.statement) {
                items.push(currentItem as ParsedTrueFalseItem);
            }
            currentItem = {
                statement: trimmed.replace('- [x]', '').trim(),
                isTrue: true,
                explanation: ''
            };
        } else if (trimmed.startsWith('- [ ]')) {
            // Save previous item if exists
            if (currentItem && currentItem.statement) {
                items.push(currentItem as ParsedTrueFalseItem);
            }
            currentItem = {
                statement: trimmed.replace('- [ ]', '').trim(),
                isTrue: false,
                explanation: ''
            };
        } else if (trimmed.startsWith('>') && currentItem) {
            // This is an explanation for the current item
            const explanation = trimmed.replace(/^>\s*/, '').trim();
            if (explanation) {
                currentItem.explanation = (currentItem.explanation ? currentItem.explanation + ' ' : '') + explanation;
            }
        }
    }

    // Don't forget the last item
    if (currentItem && currentItem.statement) {
        items.push(currentItem as ParsedTrueFalseItem);
    }

    return items;
}

// ============================================================================
// ACTIVITY TO JSX CONVERTERS
// ============================================================================

function quizToJsx(questions: ParsedQuizQuestion[], title: string): string {
    if (questions.length === 0) return '';

    const questionsJsx = questions.map(q => {
        const optionsStr = q.options.map(o => '`' + escapeJsxString(o) + '`').join(', ');
        return `  <QuizQuestion
    question=${wrapForJsx(q.question)}
    options={[${optionsStr}]}
    correctIndex={${q.correctIndex}}
    explanation=${wrapForJsx(q.explanation)}
  />`;
    }).join('\n');

    return `### ${title}

<Quiz>
${questionsJsx}
</Quiz>`;
}

function matchUpToJsx(pairs: ParsedMatchPair[], title: string): string {
    if (pairs.length === 0) return '';

    const pairsStr = pairs.map(p =>
        `  { left: \`${escapeJsxString(p.left)}\`, right: \`${escapeJsxString(p.right)}\` }`
    ).join(',\n');

    return `### ${title}

<MatchUp pairs={[
${pairsStr}
]} />`;
}

function fillInToJsx(items: ParsedFillInItem[], title: string): string {
    if (items.length === 0) return '';

    const itemsJsx = items.map(item => {
        const optionsStr = item.options.map(o => '`' + escapeJsxString(o) + '`').join(', ');
        return `  <FillInQuestion
    sentence=${wrapForJsx(item.prompt)}
    answer=${wrapForJsx(item.answer)}
    options={[${optionsStr}]}
  />`;
    }).join('\n');

    return `### ${title}

<FillIn>
${itemsJsx}
</FillIn>`;
}

function groupSortToJsx(data: ParsedGroupSort, title: string): string {
    if (Object.keys(data.groups).length === 0) return '';

    return `### ${title}

<GroupSort groups={${JSON.stringify(data.groups, null, 2)}} />`;
}

function anagramToJsx(items: ParsedAnagramItem[], title: string): string {
    if (items.length === 0) return '';

    const itemsJsx = items.map(item => `  <AnagramQuestion
    scrambled=${wrapForJsx(item.scrambled)}
    answer=${wrapForJsx(item.answer)}
    hint=${wrapForJsx(item.hint)}
  />`).join('\n');

    return `### ${title}

<Anagram>
${itemsJsx}
</Anagram>`;
}

function unjumbleToJsx(items: ParsedUnjumbleItem[], title: string): string {
    if (items.length === 0) return '';

    const itemsJsx = items.map(item => `  <UnjumbleQuestion
    words=${wrapForJsx(item.words)}
    answer=${wrapForJsx(item.answer)}
    hint=${wrapForJsx(item.hint)}
  />`).join('\n');

    return `### ${title}

<Unjumble>
${itemsJsx}
</Unjumble>`;
}

function trueFalseToJsx(items: ParsedTrueFalseItem[], title: string): string {
    if (items.length === 0) return '';

    const itemsJsx = items.map(item => `  <TrueFalseQuestion
    statement=${wrapForJsx(item.statement)}
    isTrue={${item.isTrue}}
    explanation=${wrapForJsx(item.explanation)}
  />`).join('\n');

    return `### ${title}

<TrueFalse>
${itemsJsx}
</TrueFalse>`;
}

// ============================================================================
// MAIN ACTIVITY PROCESSOR
// ============================================================================

function processActivities(body: string): { mainContent: string; activitiesJsx: string } {
    // Find Activities section
    const activitiesMatch = body.match(/# Activities\n([\s\S]*?)(?=\n# Vocabulary|\n---\n# Vocabulary|$)/);

    if (!activitiesMatch) {
        return { mainContent: body, activitiesJsx: '' };
    }

    const activitiesSection = activitiesMatch[1];

    // Remove activities from main content
    const mainContent = body.replace(/# Activities\n[\s\S]*?(?=\n# Vocabulary|\n---\n# Vocabulary|$)/, '');

    // Parse individual activities
    const activityBlocks = activitiesSection.split(/\n## /).filter(Boolean);

    let activitiesJsx = '## 🎮 Activities\n\n';

    for (const block of activityBlocks) {
        const typeMatch = block.match(/^(\w[\w-]*?):\s*(.+?)(?:\n|$)/);
        if (!typeMatch) continue;

        const activityType = typeMatch[1].toLowerCase();
        const title = typeMatch[2].trim();
        const content = block.substring(typeMatch[0].length);

        let jsx = '';

        switch (activityType) {
            case 'quiz':
                const questions = parseQuizActivity(content);
                jsx = quizToJsx(questions, title);
                break;
            case 'match-up':
                const pairs = parseMatchUpActivity(content);
                jsx = matchUpToJsx(pairs, title);
                break;
            case 'fill-in':
                const fillItems = parseFillInActivity(content);
                jsx = fillInToJsx(fillItems, title);
                break;
            case 'group-sort':
                const groupData = parseGroupSortActivity(content);
                jsx = groupSortToJsx(groupData, title);
                break;
            case 'anagram':
                const anagramItems = parseAnagramActivity(content);
                jsx = anagramToJsx(anagramItems, title);
                break;
            case 'unjumble':
                const unjumbleItems = parseUnjumbleActivity(content);
                jsx = unjumbleToJsx(unjumbleItems, title);
                break;
            case 'true-false':
                const trueFalseItems = parseTrueFalseActivity(content);
                jsx = trueFalseToJsx(trueFalseItems, title);
                break;
            default:
                // Keep as markdown for unsupported types
                jsx = `### ${title}\n\n${content}`;
        }

        activitiesJsx += jsx + '\n\n';
    }

    return { mainContent, activitiesJsx };
}

// ============================================================================
// CONTENT CONVERTERS  
// ============================================================================

function convertCalloutsToAdmonitions(content: string): string {
    // For now, don't convert callouts - the blockquote format works fine
    // Converting to admonitions requires careful block parsing to add closing :::
    // which is complex with multi-line callouts
    return content;
}

// ============================================================================
// MDX GENERATOR
// ============================================================================

async function generateMdx(
    modulePath: string,
    level: string,
    moduleNum: number
): Promise<string> {
    const content = await fs.readFile(modulePath, 'utf-8');
    const { frontmatter: fm, body } = parseFrontmatter(content);

    // Build imports - only include if activities exist
    const imports = `import Quiz, { QuizQuestion } from '@site/src/components/Quiz';
import FillIn, { FillInQuestion } from '@site/src/components/FillIn';
import MatchUp from '@site/src/components/MatchUp';
import TrueFalse, { TrueFalseQuestion } from '@site/src/components/TrueFalse';
import Anagram, { AnagramQuestion } from '@site/src/components/Anagram';
import Unjumble, { UnjumbleQuestion } from '@site/src/components/Unjumble';
import GroupSort from '@site/src/components/GroupSort';
`;

    // Build frontmatter
    const frontmatter = `---
sidebar_position: ${moduleNum}
sidebar_label: "${String(moduleNum).padStart(2, '0')}. ${escapeJsxString(fm.title || 'Untitled')}"
title: "${escapeJsxString(fm.title || 'Untitled')}"
description: "${escapeJsxString(fm.subtitle || '')}"
---
`;

    // Process activities - extract and convert to JSX
    const { mainContent, activitiesJsx } = processActivities(body);

    // Convert callouts
    let processedContent = convertCalloutsToAdmonitions(mainContent);

    // Remove the duplicate H1 title (already in frontmatter)
    processedContent = processedContent.replace(/^#\s+[^\n]+\n/, '');

    // Combine all - don't add duplicate title, source MD has it
    const mdx = `${frontmatter}
${imports}

${processedContent}

---

${activitiesJsx}
`;

    return mdx;
}

// ============================================================================
// MAIN
// ============================================================================

async function main() {
    const args = process.argv.slice(2);
    const langPair = args[0] || 'l2-uk-en';
    const targetLevel = args[1]?.toLowerCase();
    const targetModule = args[2] ? parseInt(args[2]) : undefined;

    console.log('\n🚀 MDX Generator for Docusaurus\n');
    console.log(`Source: curriculum/${langPair}/`);
    console.log(`Output: docusaurus/docs/\n`);

    const curriculumPath = path.join(CURRICULUM_DIR, langPair);
    const levels = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2'];

    for (const level of levels) {
        if (targetLevel && level !== targetLevel) continue;

        const levelPath = path.join(curriculumPath, level);

        try {
            await fs.access(levelPath);
        } catch {
            continue;
        }

        const files = await fs.readdir(levelPath);
        const moduleFiles = files.filter(f => f.startsWith('module-') && f.endsWith('.md'));

        if (moduleFiles.length === 0) continue;

        console.log(`📁 Level ${level.toUpperCase()} (${moduleFiles.length} modules)`);

        const outputDir = path.join(DOCUSAURUS_DIR, level);
        await ensureDir(outputDir);

        // NOTE: Not creating index.md - sidebar uses generated-index for landing pages

        for (const file of moduleFiles) {
            const moduleNum = parseInt(file.replace('module-', '').replace('.md', ''));

            if (targetModule !== undefined && moduleNum !== targetModule) continue;

            const modulePath = path.join(levelPath, file);

            try {
                const mdx = await generateMdx(modulePath, level, moduleNum);
                const outputFile = path.join(outputDir, `module-${String(moduleNum).padStart(2, '0')}.mdx`);
                await fs.writeFile(outputFile, mdx);
                console.log(`  ✓ Module ${String(moduleNum).padStart(2, '0')}`);
            } catch (error) {
                console.error(`  ✗ Module ${String(moduleNum).padStart(2, '0')}: ${error}`);
            }
        }
    }

    console.log('\n✅ MDX generation complete!\n');
}

function getLevelName(level: string): string {
    const names: Record<string, string> = {
        'a1': 'Beginner Ukrainian',
        'a2': 'Elementary Ukrainian',
        'b1': 'Intermediate Ukrainian',
        'b2': 'Upper-Intermediate Ukrainian',
        'c1': 'Advanced Ukrainian',
        'c2': 'Mastery Ukrainian',
    };
    return names[level] || level.toUpperCase();
}

main().catch(console.error);
