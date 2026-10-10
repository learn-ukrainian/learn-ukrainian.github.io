// @vitest-environment node
/** Render the production route with body-free synthetic content collections. */
import { experimental_AstroContainer as AstroContainer } from 'astro/container';
import { getContainerRenderer } from '@astrojs/react/container-renderer';
import { loadRenderers } from 'astro:container';
import { createHash } from 'node:crypto';
import { mkdirSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { Window } from 'happy-dom';
import { describe, expect, it, vi } from 'vitest';
import Route from '../../src/pages/[...slug].astro';
import arc from '../../src/data/arc-a1.json';

// Only collection I/O is synthetic. Route guards, generated JSON and HTML are production code.
vi.mock('astro:content', () => ({
  getCollection: async () => [],
  render: async () => ({ Content: undefined }),
}));

async function renderPage(kind: string, slug?: string) {
  const renderers = await loadRenderers([getContainerRenderer()]);
  const container = await AstroContainer.create({ renderers });
  const id = slug ? `a1/${slug}/index` : 'a1/index';
  return container.renderToString(Route, {
    props: {
      kind: slug ? 'doc' : 'landingDoc',
      entry: { id, data: { title: slug ?? 'A1', arc_kind: kind, arc_level: 'a1', arc_slug: slug } },
    },
    request: new Request(`https://example.org/${slug ? `a1/${slug}/` : 'a1/'}`),
  });
}

function preserveRender(name: string, html: string) {
  if (!process.env.ARC_RENDER_REPORT_DIR) return;
  const root = resolve(process.env.ARC_RENDER_REPORT_DIR);
  mkdirSync(root, { recursive: true });
  writeFileSync(resolve(root, `${name}.html`), html);
  console.log(`${name}.html sha256=${createHash('sha256').update(html).digest('hex')}`);
}

describe('production arc route rendering', () => {
  it.each(['special-signs', 'stress-and-melody'])('renders the recorded retired notice for %s', async (slug) => {
    const html = await renderPage('retired', slug);
    const window = new Window();
    const doc = new window.DOMParser().parseFromString(html, 'text/html');
    const notice = doc.querySelector('[data-arc-state="retired"]');
    expect(notice?.querySelector('h1')?.textContent).toBe('Retired');
    expect(notice?.querySelector('p')?.textContent).toBe('This module has been retired from the current course sequence.');
    expect(notice?.querySelector('a')?.getAttribute('href')).toBe('/a1/');
    expect(doc.querySelector('[data-state="plan_reviewed"]')).toBeNull();
    expect(doc.querySelector('[data-state="built"]')).toBeNull();
    preserveRender(slug, html);
  });

  it('refuses an unrecorded retired slug instead of rendering a notice', async () => {
    await expect(renderPage('retired', 'unrecorded-synthetic-route')).rejects.toThrow(
      'retired arc page names unrecorded arc_slug "unrecorded-synthetic-route"',
    );
  });

  it('refuses an active slug presented as retired', async () => {
    await expect(renderPage('retired', 'intro')).rejects.toThrow('unrecorded arc_slug "intro"');
  });

  it('renders all 55 active landing positions as planned', async () => {
    const html = await renderPage('landing');
    expect(arc.positions).toHaveLength(55);
    expect(html.match(/data-state="planned"/g)).toHaveLength(55);
    expect(html).not.toContain('data-arc-state="retired"');
    preserveRender('a1', html);
  });

  it.each(arc.positions.slice(0, 10).map(({ slug }) => slug))('renders current active module %s as planned', async (slug) => {
    const html = await renderPage('module', slug);
    expect(html).toContain('data-state="planned"');
    expect(html).not.toContain('data-arc-state="retired"');
    expect(html).not.toContain('data-state="plan_reviewed"');
    preserveRender(slug, html);
  });
});
