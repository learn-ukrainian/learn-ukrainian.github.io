import { describe, test, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import PhraseTable from '@site/src/components/PhraseTable';

describe('PhraseTable', () => {
  const groups = [
    {
      label: 'Привітання',
      phrases: [
        { phrase: 'Добрий день' },
        { phrase: 'Привіт', context: 'неформальне', emoji: '👋' },
      ],
    },
    {
      function: 'Прощання',
      phrases: [
        { phrase: 'До побачення' },
      ],
    },
  ];

  test('renders title, instruction, and phrase groups', () => {
    const { container } = render(
      <PhraseTable
        title="Корисні фрази"
        instruction="Прочитайте фрази"
        groups={groups}
      />
    );

    expect(screen.getByText('Корисні фрази')).toBeInTheDocument();
    expect(screen.getByText('Прочитайте фрази')).toBeInTheDocument();
    expect(screen.getByText('Привітання')).toBeInTheDocument();
    expect(screen.getByText('Добрий день')).toBeInTheDocument();
    expect(screen.getByText('Привіт')).toBeInTheDocument();
    expect(screen.getByText('неформальне')).toBeInTheDocument();
    expect(screen.getByText('👋')).toBeInTheDocument();
    expect(screen.getByText('Прощання')).toBeInTheDocument();
    expect(screen.getByText('До побачення')).toBeInTheDocument();
  });

  test('returns null when groups is empty', () => {
    const { container } = render(<PhraseTable groups={[]} />);
    expect(container.firstChild).toBeNull();
  });
});
