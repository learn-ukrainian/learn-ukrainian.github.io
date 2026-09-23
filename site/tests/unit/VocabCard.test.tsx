import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import VocabCard from '@site/src/components/VocabCard';

describe('VocabCard', () => {
  it('renders taught forms compactly under lemma when forms prop is provided', () => {
    render(
      <VocabCard
        words={[
          {
            word: 'брат',
            forms: ['бра́та', 'бра́тові'],
            examples: [],
          },
        ]}
      />,
    );

    expect(screen.getByText('брат')).toBeInTheDocument();
    expect(screen.getByText('бра́та, бра́тові')).toBeInTheDocument();
  });

  it('renders without forms line when forms prop is absent or empty', () => {
    const { container } = render(
      <VocabCard
        words={[
          {
            word: 'сестра',
            examples: ['Це моя сестра.'],
          },
        ]}
      />,
    );

    expect(screen.getByText('сестра')).toBeInTheDocument();
    expect(screen.getByText('Це моя сестра.')).toBeInTheDocument();
    expect(container.querySelector('.vocabCardForms')).toBeNull();
  });
});
