import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, test } from 'vitest';

import {
  getTeacherLessonVirtualDeck,
  getTeacherTableVirtualDeck,
  TEACHER_CURATED_MEMBERSHIP_SOURCES,
} from '../../src/lib/lexicon/custom-decks';

const membershipPath = resolve(
  __dirname,
  '../../src/data/lexicon-teacher-curated-membership.json',
);

type MembershipFile = {
  members: Array<{ lemma: string; sources?: string[] }>;
};

describe('getTeacherLessonVirtualDeck membership sources (#6544)', () => {
  const membership = JSON.parse(readFileSync(membershipPath, 'utf8')) as MembershipFile;

  test('pins the real curated-membership source vocabulary', () => {
    const observed = new Set(
      membership.members.flatMap((member) => member.sources ?? []),
    );

    expect([...TEACHER_CURATED_MEMBERSHIP_SOURCES].sort()).toEqual(
      ['homework', 'teacher_inventory'],
    );
    for (const source of TEACHER_CURATED_MEMBERSHIP_SOURCES) {
      expect(observed.has(source)).toBe(true);
    }
    // Dead filter names from the pre-#6544 path — must not reappear as the
    // membership vocabulary, or the next rename will need an explicit update.
    expect(observed.has('teacher_lesson')).toBe(false);
    expect(observed.has('private_teacher_lesson')).toBe(false);
  });

  test('filters entries with the live source tags instead of the dead ones', () => {
    const filtered = getTeacherLessonVirtualDeck(membership.members);
    const expectedLemmas = membership.members
      .filter((member) =>
        member.sources?.some((source) =>
          (TEACHER_CURATED_MEMBERSHIP_SOURCES as readonly string[]).includes(source),
        ),
      )
      .map((member) => member.lemma);

    expect(filtered.lemma_keys.length).toBeGreaterThan(0);
    expect(filtered.lemma_keys).toEqual(expectedLemmas);
    expect(filtered.lemma_keys.length).toBe(membership.members.length);

    const deadOnly = getTeacherLessonVirtualDeck([
      { lemma: 'ghost', sources: ['teacher_lesson', 'private_teacher_lesson'] },
      { lemma: 'жива', sources: ['teacher_inventory'] },
      { lemma: 'дзвінок', sources: ['homework'] },
    ]);
    expect(deadOnly.lemma_keys).toEqual(['жива', 'дзвінок']);
  });
});

describe('getTeacherTableVirtualDeck weekly source boundary (#4387)', () => {
  test("uses the committed public, lemma-only Dev's example deck payload", () => {
    const deck = getTeacherTableVirtualDeck();

    expect(deck).toMatchObject({
      id: 'virtual_teacher_table',
      title: "Dev's example deck",
      titleUk: 'Приклад розробника',
      description: "Shared example from the developer's classroom list.",
    });
    expect(deck.cloze_items).toBeUndefined();

    // Current teacher table: 1095 data rows → 1077 unique UK.
    expect(deck.lemma_keys.length).toBe(1077);
    expect(deck.lemma_keys.some((key) => /\s/.test(key))).toBe(true);
    expect(deck.lemma_keys[0]).toBe('Справедливий');
  });
});
