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
    const lines = activityContent.trim().split('\n');

    // Detect format: numbered (1. Question) vs nested list (- Question with indented options)
    const hasNumberedFormat = lines.some(l => /^\d+\.\s+/.test(l.trim()));

    if (hasNumberedFormat) {
        // Original numbered format
        const questionBlocks = activityContent.split(/\n\d+\.\s+/).filter(Boolean);
        for (const block of questionBlocks) {
            const blockLines = block.trim().split('\n');
            if (blockLines.length < 2) continue;

            const question = blockLines[0].replace(/\*\*/g, '').trim();
            const options: string[] = [];
            let correctIndex = 0;
            let explanation = '';

            for (let i = 1; i < blockLines.length; i++) {
                const line = blockLines[i].trim();
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
    } else {
        // Nested list format: - Question followed by indented - [x]/- [ ] options
        let currentQuestion: Partial<ParsedQuizQuestion> | null = null;

        for (const line of lines) {
            const trimmed = line.trim();

            // Check for parent list item (question) - starts with - but NOT - [ ] or - [x]
            if (/^-\s+(?!\[[ x]\])/.test(trimmed)) {
                // Save previous question if exists
                if (currentQuestion && currentQuestion.question && currentQuestion.options && currentQuestion.options.length > 0) {
                    questions.push(currentQuestion as ParsedQuizQuestion);
                }
                currentQuestion = {
                    question: trimmed.replace(/^-\s+/, '').trim(),
                    options: [],
                    correctIndex: 0,
                    explanation: ''
                };
            } else if (/^\s*-\s*\[x\]/.test(line) && currentQuestion) {
                // Correct option (indented)
                currentQuestion.correctIndex = currentQuestion.options!.length;
                currentQuestion.options!.push(line.replace(/^\s*-\s*\[x\]\s*/, '').trim());
            } else if (/^\s*-\s*\[ \]/.test(line) && currentQuestion) {
                // Wrong option (indented)
                currentQuestion.options!.push(line.replace(/^\s*-\s*\[ \]\s*/, '').trim());
            } else if (trimmed.startsWith('>') && currentQuestion) {
                currentQuestion.explanation = trimmed.replace(/^>\s*/, '').trim();
            }
        }

        // Don't forget the last question
        if (currentQuestion && currentQuestion.question && currentQuestion.options && currentQuestion.options.length > 0) {
            questions.push(currentQuestion as ParsedQuizQuestion);
        }
    }

    return questions;
}

function parseMatchUpActivity(activityContent: string): ParsedMatchPair[] {
    const pairs: ParsedMatchPair[] = [];
    const lines = activityContent.trim().split('\n');

    // Try table format first
    const tableMatch = activityContent.match(/\|[^\n]+\|\n\|[-\s|]+\|\n((?:\|[^\n]+\|\n?)+)/);
    if (tableMatch) {
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
        if (pairs.length > 0) return pairs;
    }

    // Try list format: - left | right
    for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith('-') && trimmed.includes('|')) {
            const content = trimmed.replace(/^-\s*/, '');
            const parts = content.split('|').map(p => p.trim());
            if (parts.length >= 2) {
                pairs.push({
                    left: parts[0],
                    right: parts[1]
                });
            }
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
    const lines = activityContent.trim().split('\n');

    // First try: table-based format (A2+)
    // | Item | Category |
    // | футбол | Командні |
    const tableRows = activityContent.match(/^\|[^|]+\|[^|]+\|$/gm);
    if (tableRows && tableRows.length > 1) {
        for (const row of tableRows) {
            if (row.includes('---')) continue;
            const cols = row.split('|').map(c => c.trim()).filter(Boolean);
            if (cols.length >= 2) {
                const item = cols[0];
                const category = cols[1];
                if (category.toLowerCase() === 'category' ||
                    category.toLowerCase() === 'group' ||
                    category.toLowerCase() === 'категорія') continue;

                if (!groups[category]) {
                    groups[category] = [];
                }
                groups[category].push(item);
            }
        }
        if (Object.keys(groups).length > 0) {
            return { groups };
        }
    }

    // Second try: Categories line + "- item: Category" format (B1+)
    // Categories: Cat1, Cat2, Cat3
    // - item1: Cat1
    // - item2: Cat2
    for (const line of lines) {
        const trimmed = line.trim();
        // Match: - item: Category
        if (trimmed.startsWith('-') && trimmed.includes(':')) {
            const content = trimmed.replace(/^-\s*/, '');
            const lastColonIndex = content.lastIndexOf(':');
            if (lastColonIndex > 0) {
                const item = content.substring(0, lastColonIndex).trim();
                const category = content.substring(lastColonIndex + 1).trim();
                if (item && category) {
                    if (!groups[category]) {
                        groups[category] = [];
                    }
                    groups[category].push(item);
                }
            }
        }
    }
    if (Object.keys(groups).length > 0) {
        return { groups };
    }

    // Third try: ### header format (A1)
    // ### Group Name
    // - item1
    // - item2
    const groupBlocks = activityContent.split(/\n###\s+/).filter(Boolean);

    for (const block of groupBlocks) {
        const blockLines = block.trim().split('\n');
        if (blockLines.length < 2) continue;

        const groupName = blockLines[0].trim();
        const items: string[] = [];

        for (const line of blockLines.slice(1)) {
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

interface ParsedErrorCorrectionItem {
    sentence: string;
    error: string;
    answer: string;
    options: string[];
    explanation: string;
}

interface ParsedSelectQuestion {
    question: string;
    options: string[];
    correctAnswers: string[];
    explanation: string;
}

interface ParsedTranslateQuestion {
    prompt: string;
    options: string[];
    correctIndex: number;
    explanation: string;
}

interface ParsedClozeData {
    passage: string;
    blanks: { options: string[]; answer: string }[];
}

interface ParsedDialogueLine {
    speaker: string;
    text: string;
}

interface ParsedMarkTheWordsData {
    instruction: string;
    text: string;
    correctWords: string[];
}

function parseTrueFalseActivity(activityContent: string): ParsedTrueFalseItem[] {
    const items: ParsedTrueFalseItem[] = [];
    const lines = activityContent.split('\n');

    // Detect format:
    // Format A (simple): - [x] Statement or - [ ] Statement
    // Format B (nested): - Statement followed by indented - [x] Правда / - [ ] Міф
    const hasNestedFormat = lines.some(l => /^\s+-\s*\[[ x]\]\s*(Правда|Міф|True|False)/i.test(l));

    if (hasNestedFormat) {
        // Nested format: - Statement with indented answer options
        let currentStatement = '';
        let isTrue = false;
        let explanation = '';

        for (const line of lines) {
            const trimmed = line.trim();

            // Check for parent list item (statement) - starts with - but NOT - [ ] or - [x]
            if (/^-\s+(?!\[[ x]\])/.test(trimmed)) {
                // Save previous item if exists
                if (currentStatement) {
                    items.push({ statement: currentStatement, isTrue, explanation });
                }
                currentStatement = trimmed.replace(/^-\s+/, '').trim();
                isTrue = false;
                explanation = '';
            } else if (/^\s*-\s*\[x\]\s*(Правда|True)/i.test(line)) {
                // Checked "True/Правда" - statement is true
                isTrue = true;
            } else if (/^\s*-\s*\[x\]\s*(Міф|False)/i.test(line)) {
                // Checked "False/Myth" - statement is false
                isTrue = false;
            } else if (trimmed.startsWith('>') && currentStatement) {
                const exp = trimmed.replace(/^>\s*/, '').trim();
                if (exp) explanation = (explanation ? explanation + ' ' : '') + exp;
            }
        }

        // Don't forget the last item
        if (currentStatement) {
            items.push({ statement: currentStatement, isTrue, explanation });
        }
    } else {
        // Simple format: - [x] Statement (true) or - [ ] Statement (false)
        let currentItem: Partial<ParsedTrueFalseItem> | null = null;

        for (const line of lines) {
            const trimmed = line.trim();

            if (trimmed.startsWith('- [x]')) {
                if (currentItem && currentItem.statement) {
                    items.push(currentItem as ParsedTrueFalseItem);
                }
                currentItem = {
                    statement: trimmed.replace('- [x]', '').trim(),
                    isTrue: true,
                    explanation: ''
                };
            } else if (trimmed.startsWith('- [ ]')) {
                if (currentItem && currentItem.statement) {
                    items.push(currentItem as ParsedTrueFalseItem);
                }
                currentItem = {
                    statement: trimmed.replace('- [ ]', '').trim(),
                    isTrue: false,
                    explanation: ''
                };
            } else if (trimmed.startsWith('>') && currentItem) {
                const explanation = trimmed.replace(/^>\s*/, '').trim();
                if (explanation) {
                    currentItem.explanation = (currentItem.explanation ? currentItem.explanation + ' ' : '') + explanation;
                }
            }
        }

        if (currentItem && currentItem.statement) {
            items.push(currentItem as ParsedTrueFalseItem);
        }
    }

    return items;
}

function parseErrorCorrectionActivity(activityContent: string): ParsedErrorCorrectionItem[] {
    const items: ParsedErrorCorrectionItem[] = [];
    const itemBlocks = activityContent.split(/\n\d+\.\s+/).filter(Boolean);

    for (const block of itemBlocks) {
        const lines = block.trim().split('\n');
        if (lines.length < 2) continue;

        const sentence = lines[0].trim();
        let error = '';
        let answer = '';
        let options: string[] = [];
        let explanation = '';

        for (const line of lines.slice(1)) {
            const trimmed = line.trim();
            if (trimmed.startsWith('> [!error]')) {
                error = trimmed.replace('> [!error]', '').trim();
            } else if (trimmed.startsWith('> [!answer]')) {
                answer = trimmed.replace('> [!answer]', '').trim();
            } else if (trimmed.startsWith('> [!options]')) {
                options = trimmed.replace('> [!options]', '').split('|').map(o => o.trim());
            } else if (trimmed.startsWith('> [!explanation]')) {
                explanation = trimmed.replace('> [!explanation]', '').trim();
            }
        }

        if (sentence && answer) {
            items.push({ sentence, error, answer, options, explanation });
        }
    }

    return items;
}

function parseSelectActivity(activityContent: string): ParsedSelectQuestion[] {
    const questions: ParsedSelectQuestion[] = [];
    const questionBlocks = activityContent.split(/\n\d+\.\s+/).filter(Boolean);

    for (const block of questionBlocks) {
        const lines = block.trim().split('\n');
        if (lines.length < 2) continue;

        const question = lines[0].replace(/\*\*/g, '').trim();
        const options: string[] = [];
        const correctAnswers: string[] = [];
        let explanation = '';

        for (let i = 1; i < lines.length; i++) {
            const line = lines[i].trim();

            if (line.startsWith('- [x]')) {
                const option = line.replace('- [x]', '').trim();
                options.push(option);
                correctAnswers.push(option);
            } else if (line.startsWith('- [ ]')) {
                options.push(line.replace('- [ ]', '').trim());
            } else if (line.startsWith('>')) {
                explanation = line.replace(/^>\s*/, '').trim();
            }
        }

        if (question && options.length > 0) {
            questions.push({ question, options, correctAnswers, explanation });
        }
    }

    return questions;
}

function parseTranslateActivity(activityContent: string): ParsedTranslateQuestion[] {
    const questions: ParsedTranslateQuestion[] = [];
    const questionBlocks = activityContent.split(/\n\d+\.\s+/).filter(Boolean);

    for (const block of questionBlocks) {
        const lines = block.trim().split('\n');
        if (lines.length < 2) continue;

        const prompt = lines[0].replace(/\*\*/g, '').trim();
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

        if (prompt && options.length > 0) {
            questions.push({ prompt, options, correctIndex, explanation });
        }
    }

    return questions;
}

function parseClozeActivity(activityContent: string): ParsedClozeData {
    const lines = activityContent.trim().split('\n');
    let passage = '';
    const blanks: { options: string[]; answer: string }[] = [];

    // Find the passage (lines before numbered items)
    let i = 0;
    while (i < lines.length && !lines[i].match(/^\d+\.\s+/)) {
        if (lines[i].trim() && !lines[i].startsWith('>')) {
            passage += (passage ? '\n' : '') + lines[i].trim();
        }
        i++;
    }

    // Parse numbered items for options and answers
    const itemBlocks = activityContent.split(/\n\d+\.\s+/).filter(Boolean);
    for (const block of itemBlocks) {
        const blockLines = block.trim().split('\n');
        if (blockLines.length === 0) continue;

        // First line is options (pipe-separated)
        const optionsLine = blockLines[0].trim();
        if (!optionsLine.includes('|')) continue;

        const options = optionsLine.split('|').map(o => o.trim());
        let answer = '';

        for (const line of blockLines.slice(1)) {
            const trimmed = line.trim();
            if (trimmed.startsWith('> [!answer]')) {
                answer = trimmed.replace('> [!answer]', '').trim();
            }
        }

        if (options.length > 0 && answer) {
            blanks.push({ options, answer });
        }
    }

    return { passage, blanks };
}

function parseDialogueReorderActivity(activityContent: string): ParsedDialogueLine[] {
    const lines: ParsedDialogueLine[] = [];

    for (const line of activityContent.split('\n')) {
        const trimmed = line.trim();
        // Match format: - А: Text or - A: Text
        const match = trimmed.match(/^-\s*([^:]+):\s*(.+)$/);
        if (match) {
            lines.push({
                speaker: match[1].trim(),
                text: match[2].trim()
            });
        }
    }

    return lines;
}

function parseMarkTheWordsActivity(activityContent: string): ParsedMarkTheWordsData {
    const lines = activityContent.trim().split('\n');
    let instruction = '';
    let text = '';
    const correctWords: string[] = [];

    for (const line of lines) {
        const trimmed = line.trim();
        // Skip horizontal rules and empty lines
        if (trimmed === '---' || trimmed === '') continue;
        // Skip stage indicators
        if (trimmed.startsWith('stage:')) continue;
        // Skip "Correct words:" lines (alternative format)
        if (trimmed.toLowerCase().startsWith('correct words:')) continue;

        if (trimmed.startsWith('>') && !instruction) {
            instruction = trimmed.replace(/^>\s*/, '').trim();
        } else if (trimmed && !trimmed.startsWith('>')) {
            // Check if this line has [bracketed] words - this is the text to mark
            const matches = trimmed.match(/\[([^\]]+)\]/g);
            if (matches && matches.length > 0) {
                text = trimmed;
                // Extract bracketed words
                for (const match of matches) {
                    correctWords.push(match.slice(1, -1)); // Remove brackets
                }
            } else if (!text) {
                // If no brackets and no text yet, this is the instruction
                instruction = trimmed;
            }
        }
    }

    // Remove brackets from text for display
    text = text.replace(/\[([^\]]+)\]/g, '$1');

    return { instruction, text, correctWords };
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

function errorCorrectionToJsx(items: ParsedErrorCorrectionItem[], title: string): string {
    if (items.length === 0) return '';

    const itemsJsx = items.map(item => {
        const optionsStr = item.options.map(o => '`' + escapeJsxString(o) + '`').join(', ');
        return `  <ErrorCorrectionItem
    sentence=${wrapForJsx(item.sentence)}
    error=${wrapForJsx(item.error)}
    answer=${wrapForJsx(item.answer)}
    options={[${optionsStr}]}
    explanation=${wrapForJsx(item.explanation)}
  />`;
    }).join('\n');

    return `### ${title}

<ErrorCorrection>
${itemsJsx}
</ErrorCorrection>`;
}

function selectToJsx(questions: ParsedSelectQuestion[], title: string): string {
    if (questions.length === 0) return '';

    const questionsJsx = questions.map(q => {
        const optionsStr = q.options.map(o => '`' + escapeJsxString(o) + '`').join(', ');
        const correctStr = q.correctAnswers.map(a => '`' + escapeJsxString(a) + '`').join(', ');
        return `  <SelectQuestion
    question=${wrapForJsx(q.question)}
    options={[${optionsStr}]}
    correctAnswers={[${correctStr}]}
    explanation=${wrapForJsx(q.explanation)}
  />`;
    }).join('\n');

    return `### ${title}

<Select>
${questionsJsx}
</Select>`;
}

function translateToJsx(questions: ParsedTranslateQuestion[], title: string): string {
    if (questions.length === 0) return '';

    const questionsJsx = questions.map(q => {
        const optionsStr = q.options.map(o => '`' + escapeJsxString(o) + '`').join(', ');
        return `  <TranslateItem
    prompt=${wrapForJsx(q.prompt)}
    options={[${optionsStr}]}
    correctIndex={${q.correctIndex}}
    explanation=${wrapForJsx(q.explanation)}
  />`;
    }).join('\n');

    return `### ${title}

<Translate>
${questionsJsx}
</Translate>`;
}

function clozeToJsx(data: ParsedClozeData, title: string): string {
    if (!data.passage || data.blanks.length === 0) return '';

    const blanksJson = JSON.stringify(data.blanks, null, 2);

    return `### ${title}

<Cloze
  passage=${wrapForJsx(data.passage)}
  blanks={${blanksJson}}
/>`;
}

function dialogueReorderToJsx(lines: ParsedDialogueLine[], title: string): string {
    if (lines.length === 0) return '';

    const linesJson = JSON.stringify(lines, null, 2);

    return `### ${title}

<DialogueReorder lines={${linesJson}} />`;
}

function markTheWordsToJsx(data: ParsedMarkTheWordsData, title: string): string {
    if (!data.text) return '';

    const wordsStr = data.correctWords.map(w => '`' + escapeJsxString(w) + '`').join(', ');

    // Include instruction as a paragraph if present
    const instructionParagraph = data.instruction ? `\n\n${data.instruction}\n` : '';

    return `### ${title}${instructionParagraph}

<MarkTheWords>
  <MarkTheWordsActivity
    text=${wrapForJsx(data.text)}
    correctWords={[${wordsStr}]}
  />
</MarkTheWords>`;
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
            case 'error-correction':
                const errorItems = parseErrorCorrectionActivity(content);
                jsx = errorCorrectionToJsx(errorItems, title);
                break;
            case 'select':
                const selectQuestions = parseSelectActivity(content);
                jsx = selectToJsx(selectQuestions, title);
                break;
            case 'translate':
                const translateQuestions = parseTranslateActivity(content);
                jsx = translateToJsx(translateQuestions, title);
                break;
            case 'cloze':
                const clozeData = parseClozeActivity(content);
                jsx = clozeToJsx(clozeData, title);
                break;
            case 'dialogue-reorder':
                const dialogueLines = parseDialogueReorderActivity(content);
                jsx = dialogueReorderToJsx(dialogueLines, title);
                break;
            case 'mark-the-words':
                const markData = parseMarkTheWordsActivity(content);
                jsx = markTheWordsToJsx(markData, title);
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
    // Convert GitHub-style callouts [!tip], [!note], etc to Docusaurus admonitions
    // Handles multi-line blockquote callouts properly

    const lines = content.split('\n');
    const result: string[] = [];
    let i = 0;

    while (i < lines.length) {
        const line = lines[i];

        // Check for callout start: > [!type] or > [!type] Title
        const calloutMatch = line.match(/^>\s*\[!(tip|note|warning|important|caution)\](.*)$/i);

        if (calloutMatch) {
            const type = calloutMatch[1].toLowerCase();
            const titlePart = calloutMatch[2].trim();

            // Start collecting callout content
            const calloutLines: string[] = [];

            // If there's content on the same line as the callout type
            if (titlePart) {
                calloutLines.push(titlePart);
            }

            i++;

            // Collect all subsequent blockquote lines as callout content
            while (i < lines.length && lines[i].startsWith('>')) {
                // Remove the > prefix and trim
                const contentLine = lines[i].replace(/^>\s?/, '');
                calloutLines.push(contentLine);
                i++;
            }

            // Build the Docusaurus admonition
            result.push(`:::${type}`);
            for (const cl of calloutLines) {
                result.push(cl);
            }
            result.push(':::');
            result.push(''); // Add blank line after admonition
        } else {
            result.push(line);
            i++;
        }
    }

    return result.join('\n');
}

/**
 * Process dialogue sections to ensure proper line breaks between turns.
 * Finds ## Dialogue: sections and adds blank lines between consecutive 
 * lines that start with **Name:** format.
 */
function processDialogues(content: string): string {
    // Find dialogue sections (## Dialogue: ... until next ## or end)
    const dialogueSectionRegex = /(## Dialogue:[^\n]*\n)([\s\S]*?)(?=\n## |\n# |\n---\n|$)/g;

    return content.replace(dialogueSectionRegex, (match, header, dialogueBody) => {
        // Split dialogue body into lines
        const lines = dialogueBody.split('\n');
        const processedLines: string[] = [];

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            const prevLine = i > 0 ? lines[i - 1] : '';

            // If current line starts with **Name:** and previous line also did,
            // add a blank line before (unless there's already one)
            if (/^\*\*[^*]+:\*\*/.test(line.trim())) {
                if (/^\*\*[^*]+:\*\*/.test(prevLine.trim())) {
                    processedLines.push('');  // Add blank line
                }
            }
            processedLines.push(line);
        }

        return header + processedLines.join('\n');
    });
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
import ErrorCorrection, { ErrorCorrectionItem } from '@site/src/components/ErrorCorrection';
import Select, { SelectQuestion } from '@site/src/components/Select';
import Translate, { TranslateItem } from '@site/src/components/Translate';
import Cloze from '@site/src/components/Cloze';
import DialogueReorder from '@site/src/components/DialogueReorder';
import MarkTheWords, { MarkTheWordsActivity } from '@site/src/components/MarkTheWords';
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

    // Process dialogue sections to add line breaks between turns
    processedContent = processDialogues(processedContent);

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
