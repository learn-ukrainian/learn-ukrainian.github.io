/**
 * Markdown utilities for legacy TypeScript activity parsers.
 *
 * Showdown was removed (CVE-2026-59710 / CVE-2026-59711; no patched npm
 * release — vulnerable range is <=2.1.0). HTML conversion is unsupported;
 * callout / answer *parsing* helpers below remain pure string utilities.
 */

// =============================================================================
// Callout Block Types
// =============================================================================

export type CalloutType = 'answer' | 'explanation' | 'alt' | 'note' | 'tip' | 'warning' | 'options' | 'option' | 'observe';

export interface CalloutBlock {
  type: CalloutType;
  content: string;
}

// =============================================================================
// Markdown Converter (removed)
// =============================================================================

export interface MarkdownConverterOptions {
  convertLegacyAnswers?: boolean;
  hideAnswers?: boolean;
  tables?: boolean;
}

/**
 * @deprecated Showdown removed for XSS CVEs with no upstream patch.
 * Site content uses Astro / @astrojs/markdown-remark instead.
 */
export function createMarkdownConverter(_options: MarkdownConverterOptions = {}): never {
  throw new Error(
    "createMarkdownConverter is unavailable: showdown was removed " +
      "(CVE-2026-59710 / CVE-2026-59711; no fixed npm release). " +
      "Use the site markdown pipeline."
  );
}

/**
 * @deprecated See createMarkdownConverter.
 */
export function markdownToHtml(_markdown: string, _options?: MarkdownConverterOptions): never {
  return createMarkdownConverter();
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
