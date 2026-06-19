import { describe, expect, it } from 'vitest';
import rehypeStringify from 'rehype-stringify';
import remarkDirective from 'remark-directive';
import remarkParse from 'remark-parse';
import remarkRehype from 'remark-rehype';
import { unified } from 'unified';

import remarkAdmonitions from '../../plugins/remark-admonitions.mjs';

async function renderMarkdown(source: string): Promise<string> {
  const file = await unified()
    .use(remarkParse)
    .use(remarkDirective)
    .use(remarkAdmonitions)
    .use(remarkRehype)
    .use(rehypeStringify)
    .process(source);

  return String(file);
}

describe('remark admonitions', () => {
  it('renders a labelled info directive as an aside with title and markdown body', async () => {
    const html = await renderMarkdown(':::info[Title]\nBody with **bold**.\n:::\n');

    expect(html).toContain('<aside class="admonition admonition-info">');
    expect(html).toContain('<p class="admonition-title">Title</p>');
    expect(html).toContain('<p>Body with <strong>bold</strong>.</p>');
    expect(html).not.toContain(':::info');
  });

  it('renders a plain tip directive with the default Ukrainian title (#M-13)', async () => {
    const html = await renderMarkdown('::::tip\nKeep going.\n::::\n');

    expect(html).toContain('<aside class="admonition admonition-tip">');
    expect(html).toContain('<p class="admonition-title">Порада</p>');
    expect(html).toContain('<p>Keep going.</p>');
    expect(html).not.toContain('::::tip');
  });
});
