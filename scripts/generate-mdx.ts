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

/**
 * Extract instruction blockquote from activity content.
 * Instructions are lines starting with `> ` at the beginning of the content.
 * Returns { instruction, contentWithoutInstruction }
 */
function extractInstruction(content: string): { instruction: string; content: string } {
    const lines = content.split('\n');
    const instructionLines: string[] = [];
    let contentStartIndex = 0;

    // Find instruction lines at the start (blockquotes starting with >)
    for (let i = 0; i < lines.length; i++) {
        const trimmed = lines[i].trim();
        if (trimmed.startsWith('>') && !trimmed.startsWith('> [!')) {
            // It's an instruction blockquote (not a callout like > [!answer])
            // Remove the > prefix and trim
            instructionLines.push(trimmed.replace(/^>\s*/, '').trim());
            contentStartIndex = i + 1;
        } else if (trimmed === '') {
            // Skip empty lines at the start
            contentStartIndex = i + 1;
        } else {
            // Found non-instruction content
            break;
        }
    }

    const instruction = instructionLines.join(' ').trim();
    const remainingContent = lines.slice(contentStartIndex).join('\n');

    return { instruction, content: remainingContent };
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

    // Detect format: numbered (1. Question) vs nested list (- Question with indented options) vs --- separated
    const hasNumberedFormat = lines.some(l => /^\d+\.\s+/.test(l.trim()));
    const hasSeparatorFormat = activityContent.includes('\n---\n');

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
    } else if (hasSeparatorFormat) {
        // --- separated format: Question text followed by - [ ]/- [x] options, separated by ---
        const questionBlocks = activityContent.split(/\n---\n/).filter(Boolean);
        for (const block of questionBlocks) {
            const blockLines = block.trim().split('\n');
            if (blockLines.length < 2) continue;

            // Find question text (lines before the first - [ ] or - [x])
            let questionLines: string[] = [];
            let optionStartIndex = 0;
            for (let i = 0; i < blockLines.length; i++) {
                const trimmed = blockLines[i].trim();
                if (trimmed.startsWith('- [')) {
                    optionStartIndex = i;
                    break;
                }
                if (trimmed && !trimmed.startsWith('>')) {
                    questionLines.push(trimmed);
                }
            }

            const question = questionLines.join(' ').replace(/\*\*/g, '').trim();
            const options: string[] = [];
            let correctIndex = 0;
            let explanation = '';

            for (let i = optionStartIndex; i < blockLines.length; i++) {
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

    // Try list format: - left | right  OR  - left :: right
    for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith('-')) {
            const content = trimmed.replace(/^-\s*/, '');
            // Try :: separator first, then | separator
            let parts: string[] = [];
            if (content.includes('::')) {
                parts = content.split('::').map(p => p.trim());
            } else if (content.includes('|')) {
                parts = content.split('|').map(p => p.trim());
            }
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
        let nextIsAnswer = false;
        let nextIsOptions = false;

        for (const line of lines.slice(1)) {
            const trimmed = line.trim();

            // Check for inline format: > [!answer] value or multi-line format: > [!answer]\n> value
            if (trimmed.startsWith('> [!answer]')) {
                const inlineValue = trimmed.replace('> [!answer]', '').trim();
                if (inlineValue) {
                    answer = inlineValue;
                } else {
                    nextIsAnswer = true;
                }
            } else if (trimmed.startsWith('> [!options]')) {
                const inlineValue = trimmed.replace('> [!options]', '').trim();
                if (inlineValue) {
                    // Handle pipe-separated or comma-separated
                    options = inlineValue.includes('|')
                        ? inlineValue.split('|').map(o => o.trim())
                        : inlineValue.split(',').map(o => o.trim());
                } else {
                    nextIsOptions = true;
                }
            } else if (trimmed.startsWith('>') && (nextIsAnswer || nextIsOptions)) {
                const value = trimmed.replace(/^>\s*/, '').trim();
                if (nextIsAnswer && value) {
                    answer = value;
                    nextIsAnswer = false;
                } else if (nextIsOptions && value) {
                    options = value.includes('|')
                        ? value.split('|').map(o => o.trim())
                        : value.split(',').map(o => o.trim());
                    nextIsOptions = false;
                }
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

        const scrambled = lines[0].trim().replace(/^\d+\.\s*/, '');
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
    const lines = activityContent.trim().split('\n');

    // Detect format: numbered (1. words) vs list (- words)
    const hasNumberedFormat = lines.some(l => /^\d+\.\s+/.test(l.trim()));

    if (hasNumberedFormat) {
        // Numbered format
        const itemBlocks = activityContent.split(/\n\d+\.\s+/).filter(Boolean);
        for (const block of itemBlocks) {
            const blockLines = block.trim().split('\n');
            if (blockLines.length < 2) continue;

            const words = blockLines[0].trim().replace(/^\d+\.\s*/, '');
            let answer = '';
            let hint = '';
            let nextIsAnswer = false;

            for (const line of blockLines.slice(1)) {
                const trimmed = line.trim();
                if (trimmed.startsWith('> [!answer]')) {
                    const inlineValue = trimmed.replace('> [!answer]', '').trim();
                    if (inlineValue) {
                        answer = inlineValue;
                    } else {
                        nextIsAnswer = true;
                    }
                } else if (trimmed.startsWith('>') && nextIsAnswer) {
                    answer = trimmed.replace(/^>\s*/, '').trim();
                    nextIsAnswer = false;
                } else if (trimmed.startsWith('> (')) {
                    hint = trimmed.replace('> (', '').replace(')', '').trim();
                }
            }

            if (words && answer) {
                items.push({ words, answer, hint });
            }
        }
    } else {
        // List format: - words | to | reorder
        let currentWords = '';
        let currentAnswer = '';
        let currentHint = '';
        let nextIsAnswer = false;

        for (const line of lines) {
            const trimmed = line.trim();

            if (trimmed.startsWith('-') && !trimmed.startsWith('> [!')) {
                // Save previous item if exists
                if (currentWords && currentAnswer) {
                    items.push({ words: currentWords, answer: currentAnswer, hint: currentHint });
                }
                currentWords = trimmed.replace(/^-\s*/, '').trim();
                currentAnswer = '';
                currentHint = '';
                nextIsAnswer = false;
            } else if (trimmed.startsWith('> [!answer]')) {
                const inlineValue = trimmed.replace('> [!answer]', '').trim();
                if (inlineValue) {
                    currentAnswer = inlineValue;
                } else {
                    nextIsAnswer = true;
                }
            } else if (trimmed.startsWith('>') && nextIsAnswer) {
                currentAnswer = trimmed.replace(/^>\s*/, '').trim();
                nextIsAnswer = false;
            } else if (trimmed.startsWith('> (')) {
                currentHint = trimmed.replace('> (', '').replace(')', '').trim();
            }
        }

        // Don't forget the last item
        if (currentWords && currentAnswer) {
            items.push({ words: currentWords, answer: currentAnswer, hint: currentHint });
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
    const lines = activityContent.trim().split('\n');

    // Detect format: numbered (1. sentence) vs list format (- sentence)
    const hasNumberedFormat = lines.some(l => /^\d+\.\s+/.test(l.trim()));

    if (hasNumberedFormat) {
        // Numbered format
        const itemBlocks = activityContent.split(/\n\d+\.\s+/).filter(Boolean);

        for (const block of itemBlocks) {
            const blockLines = block.trim().split('\n');
            if (blockLines.length < 2) continue;

            const sentence = blockLines[0].trim();
            let error = '';
            let answer = '';
            let options: string[] = [];
            let explanation = '';

            for (const line of blockLines.slice(1)) {
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
    } else {
        // List format: - sentence followed by multi-line callouts
        let currentSentence = '';
        let error = '';
        let answer = '';
        let options: string[] = [];
        let explanation = '';
        let nextIsAnswer = false;
        let nextIsExplanation = false;
        let nextIsError = false;
        let nextIsOptions = false;

        for (const line of lines) {
            const trimmed = line.trim();

            // New list item (sentence) - starts with - but not > [!
            if (trimmed.startsWith('-') && !trimmed.startsWith('> [!')) {
                // Save previous item if exists
                if (currentSentence && answer) {
                    items.push({ sentence: currentSentence, error, answer, options, explanation });
                }
                currentSentence = trimmed.replace(/^-\s*/, '').trim();
                error = '';
                answer = '';
                options = [];
                explanation = '';
                nextIsAnswer = false;
                nextIsExplanation = false;
                nextIsError = false;
                nextIsOptions = false;
            } else if (trimmed.startsWith('> [!error]')) {
                const inlineValue = trimmed.replace('> [!error]', '').trim();
                if (inlineValue) {
                    error = inlineValue;
                } else {
                    nextIsError = true;
                }
            } else if (trimmed.startsWith('> [!answer]')) {
                const inlineValue = trimmed.replace('> [!answer]', '').trim();
                if (inlineValue) {
                    answer = inlineValue;
                } else {
                    nextIsAnswer = true;
                }
            } else if (trimmed.startsWith('> [!options]')) {
                const inlineValue = trimmed.replace('> [!options]', '').trim();
                if (inlineValue) {
                    options = inlineValue.split('|').map(o => o.trim());
                } else {
                    nextIsOptions = true;
                }
            } else if (trimmed.startsWith('> [!explanation]')) {
                const inlineValue = trimmed.replace('> [!explanation]', '').trim();
                if (inlineValue) {
                    explanation = inlineValue;
                } else {
                    nextIsExplanation = true;
                }
            } else if (trimmed.startsWith('>')) {
                const value = trimmed.replace(/^>\s*/, '').trim();
                if (nextIsAnswer) {
                    answer = value;
                    nextIsAnswer = false;
                } else if (nextIsExplanation) {
                    explanation = value;
                    nextIsExplanation = false;
                } else if (nextIsError) {
                    error = value;
                    nextIsError = false;
                } else if (nextIsOptions) {
                    options = value.split('|').map(o => o.trim());
                    nextIsOptions = false;
                }
            }
        }

        // Don't forget last item
        if (currentSentence && answer) {
            items.push({ sentence: currentSentence, error, answer, options, explanation });
        }
    }

    return items;
}

function parseSelectActivity(activityContent: string): ParsedSelectQuestion[] {
    const questions: ParsedSelectQuestion[] = [];
    const lines = activityContent.trim().split('\n');

    // Detect format: numbered (1. Question) vs simple flat list
    const hasNumberedFormat = lines.some(l => /^\d+\.\s+/.test(l.trim()));

    if (hasNumberedFormat) {
        // Numbered format
        const questionBlocks = activityContent.split(/\n\d+\.\s+/).filter(Boolean);
        for (const block of questionBlocks) {
            const blockLines = block.trim().split('\n');
            if (blockLines.length < 2) continue;

            const question = blockLines[0].replace(/\*\*/g, '').trim();
            const options: string[] = [];
            const correctAnswers: string[] = [];
            let explanation = '';

            for (let i = 1; i < blockLines.length; i++) {
                const line = blockLines[i].trim();
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
    } else {
        // Simple flat format: Question text followed by - [x]/- [ ] options
        let question = '';
        const options: string[] = [];
        const correctAnswers: string[] = [];
        let explanation = '';

        for (const line of lines) {
            const trimmed = line.trim();

            if (trimmed.startsWith('- [x]')) {
                const option = trimmed.replace('- [x]', '').trim();
                options.push(option);
                correctAnswers.push(option);
            } else if (trimmed.startsWith('- [ ]')) {
                options.push(trimmed.replace('- [ ]', '').trim());
            } else if (trimmed.startsWith('>')) {
                explanation = trimmed.replace(/^>\s*/, '').trim();
            } else if (trimmed && !trimmed.startsWith('-')) {
                // First non-empty, non-checkbox line is the question
                if (!question) {
                    question = trimmed;
                }
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
    const lines = activityContent.trim().split('\n');

    // Detect format: numbered (1. Question) vs nested list (- Question with indented options) vs --- separated
    const hasNumberedFormat = lines.some(l => /^\d+\.\s+/.test(l.trim()));
    const hasSeparatorFormat = activityContent.includes('\n---\n');

    if (hasNumberedFormat) {
        // Numbered format
        const questionBlocks = activityContent.split(/\n\d+\.\s+/).filter(Boolean);
        for (const block of questionBlocks) {
            const blockLines = block.trim().split('\n');
            if (blockLines.length < 2) continue;

            const prompt = blockLines[0].replace(/\*\*/g, '').trim();
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

            if (prompt && options.length > 0) {
                questions.push({ prompt, options, correctIndex, explanation });
            }
        }
    } else if (hasSeparatorFormat) {
        // --- separated format: Prompt text followed by - [ ]/- [x] options, separated by ---
        const questionBlocks = activityContent.split(/\n---\n/).filter(Boolean);
        for (const block of questionBlocks) {
            const blockLines = block.trim().split('\n');
            if (blockLines.length < 2) continue;

            // Find prompt text (lines before the first - [ ] or - [x])
            let promptLines: string[] = [];
            let optionStartIndex = 0;
            for (let i = 0; i < blockLines.length; i++) {
                const trimmed = blockLines[i].trim();
                if (trimmed.startsWith('- [')) {
                    optionStartIndex = i;
                    break;
                }
                if (trimmed && !trimmed.startsWith('>')) {
                    promptLines.push(trimmed);
                }
            }

            const prompt = promptLines.join(' ').replace(/\*\*/g, '').trim();
            const options: string[] = [];
            let correctIndex = 0;
            let explanation = '';

            for (let i = optionStartIndex; i < blockLines.length; i++) {
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

            if (prompt && options.length > 0) {
                questions.push({ prompt, options, correctIndex, explanation });
            }
        }
    } else {
        // Nested list format: - Prompt followed by indented - [x]/- [ ] options
        let currentQuestion: Partial<ParsedTranslateQuestion> | null = null;

        for (const line of lines) {
            const trimmed = line.trim();

            // Check for parent list item (prompt) - starts with - but NOT - [ ] or - [x]
            if (/^-\s+(?!\[[ x]\])/.test(trimmed)) {
                // Save previous question if exists
                if (currentQuestion && currentQuestion.prompt && currentQuestion.options && currentQuestion.options.length > 0) {
                    questions.push(currentQuestion as ParsedTranslateQuestion);
                }
                currentQuestion = {
                    prompt: trimmed.replace(/^-\s+/, '').trim(),
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
        if (currentQuestion && currentQuestion.prompt && currentQuestion.options && currentQuestion.options.length > 0) {
            questions.push(currentQuestion as ParsedTranslateQuestion);
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

    // First, try format with speaker labels: - А: Text or - A: Text
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

    // If no lines with speaker labels found, try speakerless format
    if (lines.length === 0) {
        for (const line of activityContent.split('\n')) {
            const trimmed = line.trim();
            // Skip answer blocks and empty lines
            if (trimmed.startsWith('>') || trimmed === '' || trimmed === '---') continue;
            // Match simple format: - Text (without speaker label)
            if (trimmed.startsWith('-')) {
                const text = trimmed.replace(/^-\s*/, '').trim();
                if (text) {
                    lines.push({
                        speaker: '', // No speaker label
                        text: text
                    });
                }
            }
        }
    }

    return lines;
}

function parseMarkTheWordsActivity(activityContent: string): ParsedMarkTheWordsData {
    const lines = activityContent.trim().split('\n');
    let instruction = '';
    let textParts: string[] = [];
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
            // Check for new format: [word](correct) or [word](wrong)
            const newFormatMatches = trimmed.match(/\[([^\]]+)\]\((correct|wrong)\)/g);
            if (newFormatMatches && newFormatMatches.length > 0) {
                textParts.push(trimmed);
                // Extract only words marked as correct
                for (const match of newFormatMatches) {
                    const wordMatch = match.match(/\[([^\]]+)\]\((correct|wrong)\)/);
                    if (wordMatch && wordMatch[2] === 'correct') {
                        correctWords.push(wordMatch[1]);
                    }
                }
            } else {
                // Check for old format: [bracketed] words without (correct)/(wrong)
                const oldFormatMatches = trimmed.match(/\[([^\]]+)\]/g);
                if (oldFormatMatches && oldFormatMatches.length > 0) {
                    textParts.push(trimmed);
                    // Extract bracketed words (all are correct in old format)
                    for (const match of oldFormatMatches) {
                        correctWords.push(match.slice(1, -1)); // Remove brackets
                    }
                } else if (textParts.length === 0) {
                    // If no brackets and no text yet, this is the instruction
                    instruction = trimmed;
                }
            }
        }
    }

    // Combine all text parts
    let text = textParts.join(' ');

    // Remove [word](correct) and [word](wrong) markers, keeping just the word
    text = text.replace(/\[([^\]]+)\]\((correct|wrong)\)/g, '$1');
    // Also handle old format: remove just the brackets
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
        // Extract correct answer from options
        const answer = q.options[q.correctIndex] || q.options[0];
        const optionsStr = q.options.map(o => '`' + escapeJsxString(o) + '`').join(', ');
        return `  <TranslateItem
    source=${wrapForJsx(q.prompt)}
    answer=${wrapForJsx(answer)}
    options={[${optionsStr}]}
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

    // Add index property to each blank (0-based, corresponds to [___:N] where N is 1-based)
    const blanksWithIndex = data.blanks.map((blank, idx) => ({
        index: idx,
        options: blank.options,
        answer: blank.answer
    }));
    const blanksJson = JSON.stringify(blanksWithIndex, null, 2);

    return `### ${title}

<Cloze>
  <ClozePassage
    text=${wrapForJsx(data.passage)}
    blanks={${blanksJson}}
  />
</Cloze>`;
}

function dialogueReorderToJsx(lines: ParsedDialogueLine[], title: string): string {
    if (lines.length === 0) return '';

    // Rename 'text' to 'line' to match component's expected interface
    const linesForComponent = lines.map(l => ({
        speaker: l.speaker,
        line: l.text
    }));
    const linesJson = JSON.stringify(linesForComponent, null, 2);

    return `### ${title}

<DialogueReorder>
  <DialogueReorderActivity lines={${linesJson}} />
</DialogueReorder>`;
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
    // Find Activities section (stops at Vocabulary, Summary, or end of file)
    const activitiesMatch = body.match(/# Activities\n([\s\S]*?)(?=\n# (?:Vocabulary|Словник|Summary|Підсумок)|\n---\n# |$)/);

    if (!activitiesMatch) {
        return { mainContent: body, activitiesJsx: '' };
    }

    const activitiesSection = activitiesMatch[1];

    // Remove activities from main content
    const mainContent = body.replace(/# Activities\n[\s\S]*?(?=\n# (?:Vocabulary|Словник|Summary|Підсумок)|\n---\n# |$)/, '');

    // Parse individual activities
    const activityBlocks = activitiesSection.split(/\n## /).filter(Boolean);

    let activitiesJsx = '';

    for (const block of activityBlocks) {
        const typeMatch = block.match(/^(\w[\w-]*?):\s*(.+?)(?:\n|$)/);
        if (!typeMatch) continue;

        const activityType = typeMatch[1].toLowerCase();
        const title = typeMatch[2].trim();
        const rawContent = block.substring(typeMatch[0].length);

        // Extract instruction from content (blockquote at the start)
        const { instruction, content } = extractInstruction(rawContent);
        const instructionLine = instruction ? `\n\n*${instruction}*\n` : '';

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

        // Insert instruction after the title line (### Title)
        if (instructionLine && jsx.startsWith('###')) {
            const titleEndIndex = jsx.indexOf('\n');
            if (titleEndIndex !== -1) {
                jsx = jsx.slice(0, titleEndIndex) + instructionLine + jsx.slice(titleEndIndex);
            }
        }

        activitiesJsx += jsx + '\n\n';
    }

    return { mainContent, activitiesJsx };
}

// ============================================================================
// SECTION EXTRACTOR
// ============================================================================

interface ExtractedSections {
    lesson: string;      // Main lesson content (grammar, dialogues, examples)
    vocabulary: string;  // # Vocabulary section
    summary: string;     // # Summary or # Підсумок section
    resources: string;   // > [!resources] callout
}

/**
 * Extract and separate content into logical sections for reordering.
 * Layout order: Lesson → Resources → Summary → Activities → Vocabulary
 */
function extractSections(content: string): ExtractedSections {
    let vocabulary = '';
    let summary = '';
    let resources = '';
    const lessonParts: string[] = [];

    // Split content by H1 headers, keeping the headers
    const sections = content.split(/(?=^# )/m).filter(s => s.trim());

    for (const section of sections) {
        const headerMatch = section.match(/^# (.+?)(?:\n|$)/);
        if (!headerMatch) {
            lessonParts.push(section);
            continue;
        }

        const headerName = headerMatch[1].trim().toLowerCase();

        if (headerName === 'vocabulary' || headerName === 'словник') {
            vocabulary = section.trim();
        } else if (headerName === 'summary' || headerName === 'підсумок') {
            summary = section.trim();
        } else {
            // Everything else is lesson content (Grammar, Examples, Dialogues, etc.)
            lessonParts.push(section);
        }
    }

    let lesson = lessonParts.join('\n\n');

    // Extract Resources callout from lesson content
    const resourcesMatch = lesson.match(/(^>\s*\[!resources\][^\n]*\n(?:>.*\n)*)/m);
    if (resourcesMatch) {
        const resourceContent = resourcesMatch[1]
            .split('\n')
            .map(line => line.replace(/^>\s?/, ''))
            .join('\n')
            .replace(/^\[!resources\]\s*/, '')
            .trim();
        resources = `## 🎧 External Resources\n\n${resourceContent}`;
        lesson = lesson.replace(resourcesMatch[1], '');
    }

    // Clean up lesson content (remove extra blank lines)
    lesson = lesson.replace(/\n{3,}/g, '\n\n').trim();

    return { lesson, vocabulary, summary, resources };
}

// ============================================================================
// CONTENT CONVERTERS
// ============================================================================

// Map custom callout types to Docusaurus admonition types and styles
const CALLOUT_MAP: Record<string, { type: string; icon?: string; title?: string }> = {
    // Standard Docusaurus types
    'tip': { type: 'tip' },
    'note': { type: 'note' },
    'warning': { type: 'warning' },
    'important': { type: 'warning' },
    'caution': { type: 'caution' },
    'info': { type: 'info' },
    // Custom curriculum types mapped to appropriate styles
    'observe': { type: 'tip', icon: '🔍', title: 'Pattern Discovery' },
    'resources': { type: 'info', icon: '🎧', title: 'External Resources' },
    'example': { type: 'info', icon: '📝', title: 'Example' },
    'conversation': { type: 'note', icon: '💬', title: 'Conversation' },
    'summary': { type: 'note', icon: '📋', title: 'Summary' },
};

function convertCalloutsToAdmonitions(content: string): string {
    // Convert GitHub-style callouts [!tip], [!note], etc to Docusaurus admonitions
    // Handles multi-line blockquote callouts properly

    const lines = content.split('\n');
    const result: string[] = [];
    let i = 0;

    // Build regex from all known callout types
    const calloutTypes = Object.keys(CALLOUT_MAP).join('|');
    const calloutRegex = new RegExp(`^>\\s*\\[!(${calloutTypes})\\](.*)$`, 'i');

    while (i < lines.length) {
        const line = lines[i];

        // Check for callout start: > [!type] or > [!type] Title
        const calloutMatch = line.match(calloutRegex);

        if (calloutMatch) {
            const rawType = calloutMatch[1].toLowerCase();
            const titlePart = calloutMatch[2].trim();
            const mapping = CALLOUT_MAP[rawType] || { type: 'note' };

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

            // Build the Docusaurus admonition with optional custom title
            const customTitle = mapping.title && !titlePart ? `[${mapping.icon || ''} ${mapping.title}]` : '';
            if (customTitle) {
                result.push(`:::${mapping.type}${customTitle}`);
            } else {
                result.push(`:::${mapping.type}`);
            }
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
import Cloze, { ClozePassage } from '@site/src/components/Cloze';
import DialogueReorder, { DialogueReorderActivity } from '@site/src/components/DialogueReorder';
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

    // Process activities - convert to JSX components inline
    const { mainContent, activitiesJsx } = processActivities(body);

    // Convert callouts to Docusaurus admonitions
    let processedContent = convertCalloutsToAdmonitions(mainContent);

    // Process dialogue sections to add line breaks between turns
    processedContent = processDialogues(processedContent);

    // Remove the duplicate H1 title (already in frontmatter)
    processedContent = processedContent.replace(/^#\s+[^\n]+\n/, '');

    // Convert Summary and Vocabulary H1 to H2 for right-side TOC visibility
    processedContent = processedContent.replace(/^# (Summary|Підсумок)/gm, '## 📋 $1');
    processedContent = processedContent.replace(/^# (Vocabulary|Словник)/gm, '## 📚 $1');

    // Build MDX - exact MD order, activities JSX replaces # Activities section
    const mdxParts = [
        frontmatter,
        imports,
        '',
        processedContent,
    ];

    // Add Activities JSX (replaces removed # Activities section)
    if (activitiesJsx.trim()) {
        mdxParts.push('---', '', '## 🎯 Activities', '', activitiesJsx);
    }

    return mdxParts.join('\n');
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
    const levels = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2', 'lit'];

    for (const level of levels) {
        if (targetLevel && level !== targetLevel) continue;

        const levelPath = path.join(curriculumPath, level);

        try {
            await fs.access(levelPath);
        } catch {
            continue;
        }

        const files = await fs.readdir(levelPath);
        // Support multiple naming patterns:
        // - module-NN.md (A1, A2, B1)
        // - NN-slug.md (B2)
        // - module-LIT-NNN.md (LIT)
        const moduleFiles = files.filter(f => {
            if (!f.endsWith('.md')) return false;
            if (f.startsWith('module-')) return true;
            if (/^\d{2}-/.test(f)) return true; // NN-slug.md pattern
            return false;
        });

        if (moduleFiles.length === 0) continue;

        console.log(`📁 Level ${level.toUpperCase()} (${moduleFiles.length} modules)`);

        const outputDir = path.join(DOCUSAURUS_DIR, level);
        await ensureDir(outputDir);

        // NOTE: Not creating index.md - sidebar uses generated-index for landing pages

        for (const file of moduleFiles) {
            // Extract module number from different patterns
            let moduleNum: number;
            if (file.startsWith('module-LIT-')) {
                // module-LIT-001.md -> 1
                moduleNum = parseInt(file.replace('module-LIT-', '').replace('.md', ''));
            } else if (file.startsWith('module-')) {
                // module-01.md -> 1
                moduleNum = parseInt(file.replace('module-', '').replace('.md', ''));
            } else {
                // 01-slug.md -> 1
                moduleNum = parseInt(file.split('-')[0]);
            }

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
        'lit': 'Ukrainian Literature & Classics',
    };
    return names[level] || level.toUpperCase();
}

main().catch(console.error);
