import { describe, expect, it } from 'vitest';

import {
  isUpgradedLesson,
  isUpgradedModuleLanding,
  lessonNumberFromDoc,
  moduleSlugFromDoc,
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
});
