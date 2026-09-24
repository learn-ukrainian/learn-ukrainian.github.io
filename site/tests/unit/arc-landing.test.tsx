import { render, screen, within } from '@testing-library/react';
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import ArcLanding from '@site/src/components/ArcLanding';
import ArcModule from '@site/src/components/ArcModule';
import { groupByPhase, type ArcData, type ArcPosition } from '@site/src/lib/arc';
import { formatArcScopeCount, formatLessonCount } from '@site/src/lib/i18n/chrome';

const here = dirname(fileURLToPath(import.meta.url));
const src = (path: string) => resolve(here, '../../src', path);

function position(overrides: Partial<ArcPosition>): ArcPosition {
  return {
    position: 1,
    slug: 'alpha',
    phase: 'A1.1',
    title_uk: null,
    title_en: 'Alpha',
    job: 'Say hello',
    skills: [],
    is_checkpoint: false,
    est_lessons: 3,
    lessons: null,
    built_lessons: [],
    lesson_numbers: [],
    lesson_titles: [],
    scope: null,
    state: 'planned',
    previous_edition_href: '/a1-v1/alpha/',
    ...overrides,
  };
}

describe('formatLessonCount (numeral agreement)', () => {
  it.each([
    [0, '0 уроків', '0 lessons'],
    [1, '1 урок', '1 lesson'],
    [2, '2 уроки', '2 lessons'],
    [4, '4 уроки', '4 lessons'],
    [5, '5 уроків', '5 lessons'],
    [11, '11 уроків', '11 lessons'],
    [21, '21 урок', '21 lessons'],
    [22, '22 уроки', '22 lessons'],
    [25, '25 уроків', '25 lessons'],
    [101, '101 урок', '101 lessons'],
  ])('n = %i', (n, uk, en) => {
    expect(formatLessonCount(n)).toEqual({ uk, en });
  });
});

describe('formatArcScopeCount (numeral agreement)', () => {
  it.each([
    [0, '0 літер', '0 letters'],
    [1, '1 літера', '1 letter'],
    [2, '2 літери', '2 letters'],
    [4, '4 літери', '4 letters'],
    [5, '5 літер', '5 letters'],
    [11, '11 літер', '11 letters'],
    [21, '21 літера', '21 letters'],
    [22, '22 літери', '22 letters'],
    [25, '25 літер', '25 letters'],
  ])('letters n = %i', (n, uk, en) => {
    expect(formatArcScopeCount('letters', n)).toEqual({ uk, en });
  });

  it.each([
    [0, '0 граматичних тем', '0 grammar points'],
    [1, '1 граматична тема', '1 grammar point'],
    [2, '2 граматичні теми', '2 grammar points'],
    [4, '4 граматичні теми', '4 grammar points'],
    [5, '5 граматичних тем', '5 grammar points'],
    [11, '11 граматичних тем', '11 grammar points'],
    [21, '21 граматична тема', '21 grammar points'],
    [22, '22 граматичні теми', '22 grammar points'],
    [25, '25 граматичних тем', '25 grammar points'],
  ])('grammarPoints n = %i', (n, uk, en) => {
    expect(formatArcScopeCount('grammarPoints', n)).toEqual({ uk, en });
  });

  it.each([
    [0, '0 базових слів', '0 core words'],
    [1, '1 базове слово', '1 core word'],
    [2, '2 базові слова', '2 core words'],
    [4, '4 базові слова', '4 core words'],
    [5, '5 базових слів', '5 core words'],
    [11, '11 базових слів', '11 core words'],
    [21, '21 базове слово', '21 core words'],
    [22, '22 базові слова', '22 core words'],
    [25, '25 базових слів', '25 core words'],
  ])('coreLemmas n = %i', (n, uk, en) => {
    expect(formatArcScopeCount('coreLemmas', n)).toEqual({ uk, en });
  });
});

describe('groupByPhase', () => {
  it('keeps arc order inside and between phases', () => {
    const groups = groupByPhase([
      position({ position: 1, slug: 'a', phase: 'A1.1' }),
      position({ position: 2, slug: 'b', phase: 'A1.1' }),
      position({ position: 3, slug: 'c', phase: 'A1.2' }),
    ]);
    expect(groups.map((g) => [g.phase, g.items.map((i) => i.slug)])).toEqual([
      ['A1.1', ['a', 'b']],
      ['A1.2', ['c']],
    ]);
  });
});

describe('ArcLanding', () => {
  const positions = [
    position({ position: 1, slug: 'alpha', title_uk: 'Звуки', lessons: 3, state: 'plan_reviewed' }),
    position({ position: 2, slug: 'beta', title_en: 'Beta path', phase: 'A1.2' }),
    position({ position: 3, slug: 'checkpoint-one', title_en: 'Checkpoint one', phase: 'A1.2', is_checkpoint: true }),
  ];

  it('lists positions by phase with links, titles, counts and states', () => {
    const { container } = render(<ArcLanding level="a1" positions={positions} previousEditionHref="/a1-v1/" />);

    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('A1');
    expect(screen.getByText('A1.1')).toBeTruthy();
    expect(screen.getByText('A1.2')).toBeTruthy();
    expect(screen.getAllByRole('link', { name: /Previous A1|Попередня A1/ })).toHaveLength(1);

    const alpha = screen.getByRole('link', { name: /Звуки/ });
    expect(alpha.getAttribute('href')).toBe('/a1/alpha/');
    expect(within(alpha).getByText('3 lessons')).toBeTruthy();
    expect(alpha.querySelector('[data-state="plan_reviewed"]')).toBeTruthy();

    const beta = screen.getByRole('link', { name: /Beta path/ });
    expect(beta.getAttribute('href')).toBe('/a1/beta/');
    expect(beta.querySelector('[data-state="planned"]')).toBeTruthy();
    expect(within(beta).queryByText(/lesson/)).toBeNull();
    expect(container.querySelectorAll('a[href^="/a1/"]')).toHaveLength(3);
  });

  it('marks checkpoints and omits the previous-edition link when none is given', () => {
    render(<ArcLanding level="a1" positions={positions} />);
    expect(within(screen.getByRole('link', { name: /Checkpoint one/ })).getAllByText('Checkpoint').length).toBeGreaterThan(0);
    expect(screen.queryByRole('link', { name: /Previous A1/ })).toBeNull();
  });
});

describe('ArcModule', () => {
  it('shows the job and planned state for an unbuilt position, with no lessons', () => {
    const { container } = render(<ArcModule level="a1" position={position({})} />);
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('Alpha');
    expect(screen.getByText('Say hello')).toBeTruthy();
    expect(container.querySelector('[data-state="planned"]')).toBeTruthy();
    expect(container.querySelector('ol')).toBeNull();
    expect(screen.getByRole('link', { name: /Previous A1|Попередня A1/ }).getAttribute('href')).toBe('/a1-v1/alpha/');
  });

  it('links only the built lessons and shows the scope counts', () => {
    render(
      <ArcModule
        level="a1"
        position={position({
          title_uk: 'Звуки',
          state: 'plan_reviewed',
          lessons: 2,
          built_lessons: [1],
          lesson_numbers: [1, 2],
          lesson_titles: ['Перший', 'Другий'],
          scope: { letters: 13, grammar_points: 2, core_lemmas: 30 },
        })}
      />,
    );
    expect(screen.getByRole('link', { name: 'Перший' }).getAttribute('href')).toBe('/a1/alpha/1/');
    expect(screen.queryByRole('link', { name: 'Другий' })).toBeNull();
    expect(screen.getByText('Другий')).toBeTruthy();
    expect(screen.getByText('13 letters')).toBeTruthy();
    expect(screen.getByText('13 літер')).toBeTruthy();
    expect(screen.getByText('2 grammar points')).toBeTruthy();
    expect(screen.getByText('2 граматичні теми')).toBeTruthy();
    expect(screen.getByText('30 core words')).toBeTruthy();
    expect(screen.getByText('30 базових слів')).toBeTruthy();
  });
});

describe('lesson links', () => {
  it('link each lesson by its own number, not by list position', () => {
    render(
      <ArcModule
        level="a1"
        position={position({
          state: 'plan_reviewed',
          lessons: 2,
          built_lessons: [7],
          lesson_numbers: [7, 8],
          lesson_titles: ['Сьомий', 'Восьмий'],
        })}
      />,
    );
    expect(screen.getByRole('link', { name: 'Сьомий' }).getAttribute('href')).toBe('/a1/alpha/7/');
    expect(screen.queryByRole('link', { name: 'Восьмий' })).toBeNull();
  });
});

describe('templates hold no typed strings', () => {
  it.each(['components/ArcLanding.tsx', 'components/ArcModule.tsx'])('%s has no Cyrillic', (file) => {
    expect(readFileSync(src(file), 'utf8')).not.toMatch(/[Ѐ-ӿ]/);
  });

  it.each(['components/ArcLanding.tsx', 'components/ArcModule.tsx'])('%s takes chrome only through keys', (file) => {
    expect(readFileSync(src(file), 'utf8')).not.toMatch(/<ChromeDual\s+en="/);
  });
});

describe('generated arc pages', () => {
  const data = JSON.parse(readFileSync(src('data/arc-a1.json'), 'utf8')) as ArcData;

  it('has a module page for every position and a landing', () => {
    expect(data.positions).toHaveLength(55);
    const landing = readFileSync(src('content/docs/a1/index.mdx'), 'utf8');
    expect(landing).toContain('arc_kind: landing');
    for (const p of data.positions) {
      const page = readFileSync(src(`content/docs/a1/${p.slug}/index.mdx`), 'utf8');
      expect(page).toContain('arc_kind: module');
      expect(page).toContain(`arc_slug: ${p.slug}`);
    }
  });
});
