import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { evaluate } from '@mdx-js/mdx';
import * as runtime from 'react/jsx-runtime';
import { archiveBookmarkPaths } from '../../src/lib/a1-archive-routes';

describe('A1 archive bookmarks', () => {
  const archive = { id: 'a1-v1/things-have-gender.mdx', data: {} };
  it('serves the unchanged archive for an existing bookmark', () => {
    expect(archiveBookmarkPaths([archive])).toEqual([{ slug: 'a1/things-have-gender', entry: archive }]);
  });
  it('lets a published canonical landing win', () => {
    expect(archiveBookmarkPaths([archive, { id: 'a1/things-have-gender/index.mdx', data: {} }])).toEqual([]);
  });
  it('keeps fallback while a replacement is draft', () => {
    expect(archiveBookmarkPaths([archive, { id: 'a1/things-have-gender/index', data: { draft: true } }])).toHaveLength(1);
  });
  it('does not publish draft archives, nested pages, or archive landing as bookmarks', () => {
    expect(archiveBookmarkPaths([
      { ...archive, data: { draft: true } },
      { id: 'a1-v1/index.mdx', data: {} },
      { id: 'a1-v1/module/1.mdx', data: {} },
    ])).toEqual([]);
  });
});

describe('canonical A1 landing', () => {
  it.each([{ modules: [] }, { modules: [{ unit: 'Published modules', items: [{
    num: 1, slug: 'example', title: 'Example', status: 'active',
    lessons: [{ n: 1, title: 'Lesson', minutes: 5, href: '/a1/example/1/' }],
  }] }] }])('renders the published lesson modules with their actual count: %j', async ({ modules }) => {
    const source = readFileSync(new URL('../../src/content/docs/a1/index.mdx', import.meta.url), 'utf8')
      .replace(/^---\n[\s\S]*?\n---\n/, '')
      .replace("import LevelLanding from '@site/src/components/LevelLanding';",
        'export const LevelLanding = (props) => props;');
    const compiled = await evaluate(source, runtime);
    const tree = compiled.default({ modules });
    const landing = tree.props.children.find(child => child?.type === compiled.LevelLanding);
    expect(landing.props.modules).toEqual(modules);
    expect(landing.props.moduleCount).toBe(modules.reduce((total, group) => total + group.items.length, 0));
  });
});
