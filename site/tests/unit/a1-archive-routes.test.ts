import { describe, expect, it } from 'vitest';
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
