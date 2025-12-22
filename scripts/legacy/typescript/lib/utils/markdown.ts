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

export type CalloutType = 'answer' | 'explanation' | 'alt' | 'note' | 'tip' | 'warning' | 'options' | 'option' | 'observe';

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
    const html = content.trim()
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>');
    return `${indent}<div class="callout callout-${calloutType}" data-callout="${calloutType}">${html}</div>`;
  }
};

/**
 * Extension to convert [🔊](audio_id) to Forvo buttons
 * Tries to find preceding **Word** to use as search term.
 * If not found, uses the ID suffix (e.g. "boryspil") which Forvo search might handle.
 */
const audioLinkExtension: showdown.ShowdownExtension = {
  type: 'lang',
  filter: (text: string) => {
    // 1. Match: **Word** [🔊](audio_id)
    text = text.replace(
      /\*\*([^*]+)\*\*\s*\[🔊\]\(audio_[^)]+\)/g,
      (match, word) => {
        // Keep the bold word, add the button
        return `<strong>${word}</strong> <button class="audio-btn" onclick="openForvo('${word}')" title="Listen on Forvo">🔊</button>`;
      }
    );

    // 2. Match remaining orphan [🔊](audio_id) (fallback)
    text = text.replace(
      /\[🔊\]\(audio_([a-zA-Z0-9_]+)\)/g,
      (match, idSuffix) => {
        const fallback = idSuffix.replace(/_/g, ' ');
        return `<button class="audio-btn" onclick="openForvo('${fallback}')" title="Listen on Forvo (Search)">🔊</button>`;
      }
    );

    return text;
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
    audioLinkExtension,
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
  const lines = markdown.split('\n');

  let currentBlock: { type: CalloutType; content: string[] } | null = null;

  // Regex to detect start of a callout: > [!type] content?
  // We need to match the type and optional initial content
  const startRegex = /^\s*(?:>|-|\*)\s*\[!(\w+)\](?:\s+(.+))?$/;
  // Regex to detect continuation lines: > content
  const continuationRegex = /^\s*(?:>|-|\*)\s*(.*?)$/;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const startMatch = line.match(startRegex);

    if (startMatch) {
      // If we were parsing a block, save it
      if (currentBlock) {
        callouts.push({
          type: currentBlock.type,
          content: currentBlock.content.join('\n').trim()
        });
      }

      // Start new block
      const type = startMatch[1].toLowerCase() as CalloutType;
      const initialContent = startMatch[2] ? [startMatch[2]] : [];
      currentBlock = { type, content: initialContent };
      continue;
    }

    // Check for continuation if we are in a block
    if (currentBlock) {
      const contMatch = line.match(continuationRegex);
      if (contMatch) {
        // It's a quoted line. Is it a new callout? No, we checked startRegex first.
        // Check if it's just an empty quote line or content
        const content = contMatch[1];
        // If it looks like a new list item or something that breaks headers, maybe stop?
        // But for now, assume all contiguous > lines belong to the block.
        currentBlock.content.push(content);
      } else {
        // Non-quoted line breaks the block
        callouts.push({
          type: currentBlock.type,
          content: currentBlock.content.join('\n').trim()
        });
        currentBlock = null;
      }
    }
  }

  // Push final block
  if (currentBlock) {
    callouts.push({
      type: currentBlock.type,
      content: currentBlock.content.join('\n').trim()
    });
  }

  return callouts;
}




/**
 * Extract answer and explanation from a block of text
 */
export function extractAnswer(text: string): {
  answer: string;
  explanation?: string;
  alternatives?: string[];
  options?: string[];
} {
  const callouts = parseCallouts(text);

  const answerCallout = callouts.find(c => c.type === 'answer');
  const explanationCallout = callouts.find(c => c.type === 'explanation');
  const altCallouts = callouts.filter(c => c.type === 'alt');
  const optionsCallout = callouts.find(c => c.type === 'options' || (c as any).type === 'option'); // Handle both singular and plural

  let options: string[] | undefined;
  if (optionsCallout) {
    // Split by commas, pipe, or newlines
    options = optionsCallout.content.split(/[,|\n]/).map(o => o.trim()).filter(o => o.length > 0);
  }

  return {
    answer: answerCallout?.content || '',
    explanation: explanationCallout?.content,
    alternatives: altCallouts.length > 0 ? altCallouts.map(c => c.content) : undefined,
    options,
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

.callout-observe {
  background: #fff8e6;
  border-left: 3px solid #f5a623;
  padding: 1rem;
  margin: 1rem 0;
}

.callout-observe::before {
  content: '🔎 ';
  font-size: 1.1em;
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
