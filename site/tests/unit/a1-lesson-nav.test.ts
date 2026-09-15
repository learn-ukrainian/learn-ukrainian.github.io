import { describe, expect, it } from 'vitest';

import {
  a1AdjacentHrefs,
  isUpgradedLesson,
  isUpgradedModuleLanding,
  lessonNumberFromDoc,
  moduleSlugFromDoc,
  resolveNavHref,
  withManifestCopy,
} from '../../src/lib/a1-lesson-nav';

describe('a1 lesson nav', () => {
  it('treats a1/{slug} with lessons as a module landing', () => {
    expect(isUpgradedModuleLanding('a1/things-have-gender', [{ n: 1 }])).toBe(true);
    expect(isUpgradedModuleLanding('a1/things-have-gender/index', [{ n: 1 }])).toBe(true);
    expect(isUpgradedModuleLanding('a1/things-have-gender/1', [{ n: 1 }])).toBe(false);
    expect(isUpgradedModuleLanding('a1-v1/things-have-gender', [{ n: 1 }])).toBe(false);
    expect(isUpgradedModuleLanding('a1/things-have-gender', undefined)).toBe(false);
  });

  it('keeps bilingual title and taglines when a module unlocks', () => {
    const item = {
      num: 4,
      slug: 'stress-and-melody',
      title: 'Наголос і мелодика',
      titleEn: 'Stress & Melody',
      sub: 'Наголос змінює значення, інтонація змінює намір',
      subEn: 'Stress changes meaning, intonation changes intent',
    };
    const card = withManifestCopy(item, {
      title: 'Наголос і мелодика',
      sidebar: { order: 4 },
      lessons: [{ n: 1, title: 'Lesson', minutes: 60, href: '/a1/stress-and-melody/1/' }],
    });
    expect(card.titleEn).toBe('Stress & Melody');
    expect(card.sub).toBe('Наголос змінює значення, інтонація змінює намір');
    expect(card.subEn).toBe('Stress changes meaning, intonation changes intent');
    expect(card.status).toBe('active');
    // Type-level: withManifestCopy must carry a concrete lessons type (not
    // `unknown`) so callers can pass the result straight into LevelLanding.
    const [lesson] = card.lessons;
    expect(lesson.n).toBe(1);
    expect(lesson.href).toBe('/a1/stress-and-melody/1/');
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
