import { render, screen, within } from '@testing-library/react';
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
                status: 'active',
              },
            ],
          },
        ]}
      />,
    );

    const link = screen.getByRole('link', { name: /Звуки, літери та привіт/ });
    expect(link).toHaveAttribute('href', '/a1/sounds-letters-and-hello/');
    // Status chrome must not become a separate named control inside the link.
    expect(within(link).queryByRole('img')).toBeNull();
  });
});
