/**
 * Markdown utilities with Showdown extensions
 *
 * Handles:
 * - Standard markdown conversion
 * - Callout blocks: > [!answer], > [!explanation], > [!alt]
 * - Answer hiding with toggle buttons
 */

import * as showdown from 'showdown';

// =============================================================================
// Callout Block Types
// =============================================================================

export type CalloutType = 'answer' | 'explanation' | 'alt' | 'note' | 'tip' | 'warning';

export interface CalloutBlock {
  type: CalloutType;
  content: string;
}

// =============================================================================
// Showdown Extensions
// =============================================================================

/**
 * Extension to parse callout blocks like > [!answer] content
 * Converts them to semantic HTML that can be styled/hidden
 * Handles both start-of-line and indented callouts (under list items)
 */
const calloutExtension: showdown.ShowdownExtension = {
  type: 'lang',
  regex: /^(\s*)>\s*\[!(\w+)\]\s*(.+)$/gm,
  replace: (match: string, indent: string, type: string, content: string) => {
    const calloutType = type.toLowerCase() as CalloutType;
    // Process inline markdown (bold, italic) in content
    let html = content.trim()
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>');
    return `${indent}<div class="callout callout-${calloutType}" data-callout="${calloutType}">${html}</div>`;
  }
};

/**
 * Extension to handle answer blocks with toggle functionality
 * Groups consecutive callouts into hideable sections
 */
const answerBlockExtension: showdown.ShowdownExtension = {
  type: 'output',
  filter: (text: string) => {
    let answerCount = 0;

    // Find consecutive answer + explanation callouts and wrap them
    text = text.replace(
      /(<div class="callout callout-answer"[^>]*>[\s\S]*?<\/div>)(\s*<div class="callout callout-(?:explanation|alt)"[^>]*>[\s\S]*?<\/div>)*/g,
      (match) => {
        const id = `ans-${answerCount++}`;
        return `<button class="show-answer-btn" onclick="toggleAnswer('${id}', this)">Показати відповідь</button><div class="answer-block" id="${id}">${match}</div>`;
      }
    );

    return text;
  }
};

/**
 * Extension to handle legacy answer formats for backward compatibility
 * Converts old formats to new callout format during parsing
 */
const legacyAnswerExtension: showdown.ShowdownExtension = {
  type: 'lang',
  filter: (text: string) => {
    // Pattern 1: **Відповідь:** answer
    text = text.replace(
      /\*\*(?:Відповідь|Відповіді|Answer|Answers?):\*\*\s*(.+?)(?:\n|$)/gi,
      '> [!answer] $1\n'
    );

    // Pattern 2: → ✅ **Правда.** explanation
    text = text.replace(
      /→\s*✅\s*\*\*Правда\.\*\*\s*(.+?)(?:\n|$)/g,
      '> [!answer] true\n> [!explanation] $1\n'
    );

    // Pattern 3: → ❌ **Міф.** explanation
    text = text.replace(
      /→\s*❌\s*\*\*Міф\.\*\*\s*(.+?)(?:\n|$)/g,
      '> [!answer] false\n> [!explanation] $1\n'
    );

    // Pattern 4: → **answer** (bold answer)
    text = text.replace(
      /→\s*\*\*(.+?)\*\*\s*(?:\n|$)/g,
      '> [!answer] $1\n'
    );

    // Pattern 5: → answer (explanation) - arrow with parenthetical
    text = text.replace(
      /→\s*(.+?)\s*\((.+?)\)\s*(?:\n|$)/g,
      '> [!answer] $1\n> [!explanation] $2\n'
    );

    // Pattern 6: → answer (simple arrow, no parens)
    // Only match if not already converted and not starting with emoji
    text = text.replace(
      /^(\s*)→\s*([^✅❌\*\n][^\n]*?)$/gm,
      '$1> [!answer] $2'
    );

    return text;
  }
};

// =============================================================================
// Markdown Converter
// =============================================================================

export interface MarkdownConverterOptions {
  /**
   * Enable legacy answer format conversion
   * When true, old formats (→, **Відповідь:**) are converted to callouts
   */
  convertLegacyAnswers?: boolean;

  /**
   * Enable answer hiding with toggle buttons
   * When true, answer callouts are wrapped in hideable blocks
   */
  hideAnswers?: boolean;

  /**
   * Enable table support
   */
  tables?: boolean;
}

const defaultOptions: MarkdownConverterOptions = {
  convertLegacyAnswers: false,  // Disabled: all modules now use native > [!answer] syntax
  hideAnswers: true,
  tables: true,
};

/**
 * Create a configured Showdown converter
 */
export function createMarkdownConverter(options: MarkdownConverterOptions = {}): showdown.Converter {
  const opts = { ...defaultOptions, ...options };

  const extensions: showdown.ShowdownExtension[] = [
    calloutExtension,
  ];

  if (opts.convertLegacyAnswers) {
    extensions.unshift(legacyAnswerExtension); // Run first
  }

  if (opts.hideAnswers) {
    extensions.push(answerBlockExtension); // Run last (on output)
  }

  const converter = new showdown.Converter({
    tables: opts.tables,
    strikethrough: true,
    simpleLineBreaks: true,
    extensions,
  });

  return converter;
}

/**
 * Convert markdown to HTML with answer handling
 */
export function markdownToHtml(markdown: string, options?: MarkdownConverterOptions): string {
  const converter = createMarkdownConverter(options);
  return converter.makeHtml(markdown);
}

// =============================================================================
// Answer Parsing Utilities
// =============================================================================

/**
 * Parse callout blocks from markdown text
 * Returns array of callout blocks found
 */
export function parseCallouts(markdown: string): CalloutBlock[] {
  const callouts: CalloutBlock[] = [];
  // Allow optional leading whitespace for indented callouts (under list items)
  const regex = /^\s*>\s*\[!(\w+)\]\s*(.+)$/gm;

  let match;
  while ((match = regex.exec(markdown)) !== null) {
    callouts.push({
      type: match[1].toLowerCase() as CalloutType,
      content: match[2].trim(),
    });
  }

  return callouts;
}

/**
 * Extract answer and explanation from a block of text
 */
export function extractAnswer(text: string): { answer: string; explanation?: string; alternatives?: string[] } {
  const callouts = parseCallouts(text);

  const answerCallout = callouts.find(c => c.type === 'answer');
  const explanationCallout = callouts.find(c => c.type === 'explanation');
  const altCallouts = callouts.filter(c => c.type === 'alt');

  return {
    answer: answerCallout?.content || '',
    explanation: explanationCallout?.content,
    alternatives: altCallouts.length > 0 ? altCallouts.map(c => c.content) : undefined,
  };
}

/**
 * Check if text contains answer callouts
 */
export function hasAnswers(text: string): boolean {
  return />\s*\[!answer\]/i.test(text);
}

// =============================================================================
// CSS for Callouts and Answer Hiding
// =============================================================================

export const calloutStyles = `
/* Callout blocks */
.callout {
  padding: 0.5rem 1rem;
  margin: 0.25rem 0;
  border-radius: 4px;
}

.callout-answer {
  background: #e8f8f0;
  border-left: 3px solid var(--success, #26a269);
  color: var(--text, #1e1e1e);
}

.callout-explanation {
  background: #e8f4fd;
  border-left: 3px solid var(--primary, #1a5fb4);
  color: var(--text-muted, #5e5e5e);
  font-style: italic;
}

.callout-alt {
  background: #f5f5f5;
  border-left: 3px solid var(--border, #e0e0e0);
  color: var(--text-muted, #5e5e5e);
}

/* Answer hiding */
.answer-block {
  display: none;
}

.answer-block.show {
  display: block;
}

.show-answer-btn {
  background: #f0f0f0;
  border: 1px solid var(--border, #e0e0e0);
  border-radius: 6px;
  padding: 0.25rem 0.75rem;
  font-size: 0.8rem;
  cursor: pointer;
  color: var(--text-muted, #5e5e5e);
  margin: 0.25rem 0;
}

.show-answer-btn:hover {
  background: #e5e5e5;
}

.show-answer-btn.revealed {
  background: #e8f8f0;
  border-color: var(--success, #26a269);
  color: var(--success, #26a269);
}
`;

export const answerToggleScript = `
function toggleAnswer(id, btn) {
  const el = document.getElementById(id);
  if (!el) return;
  const show = !el.classList.contains('show');
  if (show) {
    el.classList.add('show');
    btn.textContent = 'Сховати відповідь';
    btn.classList.add('revealed');
  } else {
    el.classList.remove('show');
    btn.textContent = 'Показати відповідь';
    btn.classList.remove('revealed');
  }
}
`;
