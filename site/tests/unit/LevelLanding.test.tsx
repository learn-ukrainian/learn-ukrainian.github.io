import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { render, screen, within } from '@testing-library/react';
import yaml from 'js-yaml';
import { describe, expect, it } from 'vitest';
import LevelLanding from '@site/src/components/LevelLanding';

describe('LevelLanding module cards', () => {
  it('renders available modules as real links (role=link + href)', () => {
    // Use a non-A1 level so LiveStatus is not mounted; the link contract is
    // the same for every track that uses ModuleCard (#6712).
    render(
      <LevelLanding
        level="A2"
        modules={[
          {
            unit: 'Unit 1',
            items: [
              {
                num: 1,
                slug: 'sounds-letters-and-hello',
                title: 'Звуки, літери та привіт',
                sub: 'First module',
                status: 'active',
              },
              {
                num: 2,
                slug: 'reading-ukrainian',
                title: 'Читаємо українською',
                status: 'done',
              },
              {
                num: 3,
                slug: 'not-ready-yet',
                title: 'Ще не готово',
                status: 'locked',
              },
            ],
          },
        ]}
      />,
    );

    const active = screen.getByRole('link', { name: /Звуки, літери та привіт/ });
    expect(active.tagName).toBe('A');
    expect(active).toHaveAttribute('href', '/a2/sounds-letters-and-hello/');

    const done = screen.getByRole('link', { name: /Читаємо українською/ });
    expect(done).toHaveAttribute('href', '/a2/reading-ukrainian/');

    expect(screen.queryByRole('link', { name: /Ще не готово/ })).toBeNull();
    expect(screen.getByText('Ще не готово')).toBeInTheDocument();
  });

  it('keeps A1 module rows as links whose accessible name is the title', () => {
    render(
      <LevelLanding
        level="A1"
        modules={[
          {
            unit: 'A1.1',
            items: [
              {
                num: 1,
                slug: 'sounds-letters-and-hello',
                title: 'Звуки, літери та привіт',
                titleEn: 'Sounds, Letters & Hello',
                sub: '33 літери, 38 звуків, Привіт!',
                subEn: '33 letters, 38 sounds, Hello!',
                status: 'active',
              },
            ],
          },
        ]}
      />,
    );

    const link = screen.getByRole('link', { name: /Звуки, літери та привіт/ });
    expect(link).toHaveAttribute('href', '/a1/sounds-letters-and-hello/');
    expect(screen.getByText(/Sounds, Letters & Hello/)).toBeInTheDocument();
    expect(screen.getByText('33 літери, 38 звуків, Привіт!')).toBeInTheDocument();
    expect(screen.getByText('33 letters, 38 sounds, Hello!')).toBeInTheDocument();
    // Status chrome must not become a separate named control inside the link.
    expect(within(link).queryByRole('img')).toBeNull();
  });
});

// #9754: feed the real committed landing files (not hand-written props) through the real component.
const readRepoFile = (relative: string) => readFileSync(resolve(__dirname, '../../..', relative), 'utf8');
const manifest = yaml.load(readRepoFile('curriculum/l2-uk-en/curriculum.yaml')) as {
  levels: Record<string, { modules: string[] }>;
};

function landingInput(track: string) {
  const mdx = readRepoFile(`site/src/content/docs/${track}/index.mdx`);
  const moduleCount = Number(/\bmoduleCount=\{(\d+)\}/.exec(mdx)![1]);
  const items = [...mdx.matchAll(/\{ num: (\d+), slug: "([^"]+)", title: "((?:[^"\\]|\\.)*)".*?status: "(\w+)" \}/g)].map(
    ([, num, slug, title, status]) => ({
      num: Number(num),
      slug,
      title: JSON.parse(`"${title}"`) as string,
      status: status as 'active' | 'done' | 'locked',
    }),
  );
  return { moduleCount, items };
}

describe('LevelLanding rendered from the committed track landings', () => {
  const tracks = [
    { track: 'c1', level: 'C1' },
    { track: 'bio', level: 'BIO' },
    { track: 'folk', level: 'FOLK' },
  ];

  for (const { track, level } of tracks) {
    it(`${track} landing shows the manifest module count`, () => {
      const { moduleCount, items } = landingInput(track);
      render(<LevelLanding level={level} moduleCount={moduleCount} modules={[{ unit: 'All', items }]} />);

      const expected = manifest.levels[track].modules.length;
      // Hero stat is "<emoji> {count} <modules label>": the count is the span's own text, the label a child.
      expect(screen.getByText(new RegExp(`^\\s*\\p{Extended_Pictographic}\\s*${expected}\\s*$`, 'u'))).toBeInTheDocument();
      expect(items).toHaveLength(expected);
    });
  }

  for (const track of ['bio', 'folk']) {
    it(`${track} landing keeps available modules as real links`, () => {
      const { moduleCount, items } = landingInput(track);
      render(<LevelLanding level={track.toUpperCase()} moduleCount={moduleCount} modules={[{ unit: 'All', items }]} />);

      const available = items.filter((item) => item.status !== 'locked');
      expect(available.length).toBeGreaterThan(0);
      for (const item of available) {
        expect(screen.getByRole('link', { name: new RegExp(item.title.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')) }))
          .toHaveAttribute('href', `/${track}/${item.slug}/`);
      }
      expect(screen.getAllByRole('link')).toHaveLength(available.length);
    });
  }
});
