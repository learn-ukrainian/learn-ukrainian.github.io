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

async function parseMarkdown(source: string) {
  const processor = unified().use(remarkParse).use(remarkDirective).use(remarkAdmonitions);
  const tree = processor.parse(source);
  return processor.run(tree);
}

interface DirectiveNode {
  type?: string;
  name?: string;
  children?: unknown[];
  attributes?: Record<string, string | null> | null;
}

function collectTextDirectives(node: unknown, acc: DirectiveNode[] = []): DirectiveNode[] {
  if (!node || typeof node !== 'object') return acc;

  const candidate = node as DirectiveNode;
  if (candidate.type === 'textDirective') acc.push(candidate);

  const children = candidate.children;
  if (Array.isArray(children)) {
    for (const child of children) collectTextDirectives(child, acc);
  }

  return acc;
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

  it('keeps mm:ss and h:mm:ss timecodes as literal text', async () => {
    const html = await renderMarkdown('від 28:57 до 32:47, а «Два кольори» — від 1:03:15 до 1:07:29');

    expect(html).toContain('28:57');
    expect(html).toContain('32:47');
    expect(html).toContain('1:03:15');
    expect(html).toContain('1:07:29');

    expect(html).not.toContain('<div></div>');
    expect(html).not.toContain('</p><p>');
    expect(html).toContain('<p>від 28:57 до 32:47, а «Два кольори» — від 1:03:15 до 1:07:29</p>');
  });

  it('keeps numeric directive-like suffixes literal after formatted text', async () => {
    const html = await renderMarkdown('**1**:03');

    expect(html).toContain('<p><strong>1</strong>:03</p>');
    expect(html).not.toContain('<div></div>');
  });

  it('keeps standalone numeric directive-like text literal', async () => {
    const html = await renderMarkdown('word :57');

    expect(html).toContain('<p>word :57</p>');
    expect(html).not.toContain('<div></div>');
  });

  it('preserves explicit numeric text directive labels and attributes', async () => {
    const labeled = await parseMarkdown('x 2:123[label]');
    const labeledDirectives = collectTextDirectives(labeled);
    const labeledDirective = labeledDirectives.find((node) => node.name === '123');

    expect(labeledDirective).toBeDefined();
    expect((labeledDirective?.children ?? []).length).toBeGreaterThan(0);

    const attributed = await parseMarkdown('x 2:123{key=value}');
    const attributedDirective = collectTextDirectives(attributed).find((node) => node.name === '123');

    expect(attributedDirective).toBeDefined();
    expect(attributedDirective?.attributes).toBeDefined();
    expect(Object.keys(attributedDirective?.attributes ?? {}).length).toBeGreaterThan(0);
  });
});
