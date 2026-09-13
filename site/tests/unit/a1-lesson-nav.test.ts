import { describe, expect, it } from 'vitest';

import {
  a1AdjacentHrefs,
  isUpgradedLesson,
  isUpgradedModuleLanding,
  lessonNumberFromDoc,
  moduleSlugFromDoc,
  resolveNavHref,
} from '../../src/lib/a1-lesson-nav';

describe('a1 lesson nav', () => {
  it('treats a1/{slug} with lessons as a module landing', () => {
    expect(isUpgradedModuleLanding('a1/things-have-gender', [{ n: 1 }])).toBe(true);
    expect(isUpgradedModuleLanding('a1/things-have-gender/index', [{ n: 1 }])).toBe(true);
    expect(isUpgradedModuleLanding('a1/things-have-gender/1', [{ n: 1 }])).toBe(false);
    expect(isUpgradedModuleLanding('a1-v1/things-have-gender', [{ n: 1 }])).toBe(false);
    expect(isUpgradedModuleLanding('a1/things-have-gender', undefined)).toBe(false);
  });

  it('treats a1/{slug}/{n} as a nested lesson', () => {
    expect(isUpgradedLesson('a1/things-have-gender/1')).toBe(true);
    expect(isUpgradedLesson('a1/things-have-gender/1.mdx')).toBe(true);
    expect(isUpgradedLesson('a1/things-have-gender')).toBe(false);
    expect(isUpgradedLesson('a1-v1/things-have-gender')).toBe(false);
  });

  it('reads module slug and lesson numbers', () => {
    expect(moduleSlugFromDoc('a1/things-have-gender/2')).toBe('things-have-gender');
    expect(lessonNumberFromDoc('a1/things-have-gender/2')).toBe('02');
    expect(lessonNumberFromDoc('a1/things-have-gender')).toBeUndefined();
  });

  it('does not double-prefix absolute prev/next paths', () => {
    expect(resolveNavHref('/a1/things-have-gender/2/', 'a1')).toBe('/a1/things-have-gender/2/');
    expect(resolveNavHref('/a1/things-have-gender/2', 'a1')).toBe('/a1/things-have-gender/2/');
    expect(resolveNavHref('things-have-gender/2', 'a1')).toBe('/a1/things-have-gender/2/');
  });

  it('chains prev/next across two upgraded modules', () => {
    const docs = [
      { id: 'a1/things-have-gender', lessons: [{ n: 1 }], order: 8 },
      { id: 'a1/things-have-gender/1', order: 1 },
      { id: 'a1/things-have-gender/2', order: 2 },
      { id: 'a1/things-have-gender/3', order: 3 },
      { id: 'a1/what-is-it-like', lessons: [{ n: 1 }], order: 9 },
      { id: 'a1/what-is-it-like/1', order: 1 },
    ];
    expect(a1AdjacentHrefs('a1/things-have-gender/1', docs)).toEqual({
      prev: '/a1/things-have-gender/',
      next: '/a1/things-have-gender/2/',
    });
    expect(a1AdjacentHrefs('a1/things-have-gender/3', docs)).toEqual({
      prev: '/a1/things-have-gender/2/',
      next: '/a1/what-is-it-like/',
    });
    expect(a1AdjacentHrefs('a1/what-is-it-like', docs)).toEqual({
      prev: '/a1/things-have-gender/3/',
      next: '/a1/what-is-it-like/1/',
    });
  });
});
