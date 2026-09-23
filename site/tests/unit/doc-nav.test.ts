import { describe, expect, it } from 'vitest';

import { lessonRoute, resolveNavHref } from '../../src/lib/doc-nav';

describe('resolveNavHref', () => {
  it('does not double-prefix absolute prev/next paths', () => {
    expect(resolveNavHref('/a1/things-have-gender/2/', 'a1')).toBe('/a1/things-have-gender/2/');
    expect(resolveNavHref('/a1/things-have-gender/2', 'a1')).toBe('/a1/things-have-gender/2/');
    expect(resolveNavHref('things-have-gender/2', 'a1')).toBe('/a1/things-have-gender/2/');
    expect(resolveNavHref('  ', 'a1')).toBe('/a1/');
  });
});

describe('lessonRoute', () => {
  it('reads module and lesson number from a1/<module>/<n>', () => {
    expect(lessonRoute('a1/things-have-gender/2', 'a1')).toEqual({ module: 'things-have-gender', n: 2 });
    expect(lessonRoute('a1/things-have-gender/12.mdx', 'a1')).toEqual({ module: 'things-have-gender', n: 12 });
  });

  it('rejects module pages, other tracks and non-numeric leaves', () => {
    expect(lessonRoute('a1/things-have-gender', 'a1')).toBeUndefined();
    expect(lessonRoute('a1/things-have-gender/index', 'a1')).toBeUndefined();
    expect(lessonRoute('a1-v1/things-have-gender/1', 'a1')).toBeUndefined();
    expect(lessonRoute('a1/things-have-gender/intro', 'a1')).toBeUndefined();
  });
});
