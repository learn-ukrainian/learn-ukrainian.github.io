import { describe, test, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import PickSyllables from '@site/src/components/PickSyllables';

function optionButtons(container: HTMLElement) {
  const box = container.querySelector('[data-activity="pick-syllables-options"]');
  if (!box) throw new Error('pick-syllables-options not found');
  return [...box.querySelectorAll<HTMLButtonElement>('button')];
}

function feedback(container: HTMLElement) {
  return container.querySelector('[data-activity="pick-syllables-feedback"]');
}

describe('PickSyllables', () => {
  const syllables = ['кіт', 'со-ба-ка', 'дім', 'ма-ши-на'];
  // "closed" (закриті) syllables end in a consonant: кіт, дім
  const correctIndices = [0, 2];

  test('wraps everything in a pick-syllables activity container', () => {
    const { container } = render(
      <PickSyllables syllables={syllables} correctIndices={correctIndices} category="закриті" />,
    );
    expect(container.querySelector('[data-activity="pick-syllables"]')).toBeInTheDocument();
  });

  test('renders one button per syllable', () => {
    const { container } = render(
      <PickSyllables syllables={syllables} correctIndices={correctIndices} category="закриті" />,
    );
    expect(optionButtons(container)).toHaveLength(4);
  });

  test('no feedback before checking', () => {
    const { container } = render(
      <PickSyllables syllables={syllables} correctIndices={correctIndices} category="закриті" />,
    );
    expect(feedback(container)).not.toBeInTheDocument();
  });

  test('Check is disabled until at least one syllable is picked', () => {
    const { container } = render(
      <PickSyllables syllables={syllables} correctIndices={correctIndices} category="закриті" />,
    );
    const check = [...container.querySelectorAll<HTMLButtonElement>('button')].find(
      (b) => b.textContent?.trim() === 'Перевірити',
    );
    expect(check).toBeDisabled();
  });

  test('picking exactly the correct set and checking shows correct feedback with the explanation', async () => {
    const user = userEvent.setup();
    const { container } = render(
      <PickSyllables
        syllables={syllables}
        correctIndices={correctIndices}
        category="закриті"
        explanation="Закритий склад закінчується на приголосний."
      />,
    );

    await user.click(optionButtons(container)[0]); // кіт
    await user.click(optionButtons(container)[2]); // дім
    await user.click(screen.getByText('Перевірити'));

    const fb = feedback(container);
    expect(fb).toBeInTheDocument();
    expect(fb).toHaveAttribute('data-correct', 'true');
    // `explanation` is pre-existing (not new in #8889 A1-P3): no live-region
    // announcement is added here, matching main exactly (finding 5).
    expect(fb).not.toHaveAttribute('role');
    expect(fb).not.toHaveAttribute('aria-live');
    expect(container.querySelector('[data-activity="pick-syllables-explanation"]')?.textContent).toBe(
      'Закритий склад закінчується на приголосний.',
    );
  });

  test('picking the wrong set and checking shows incorrect feedback with the explanation', async () => {
    const user = userEvent.setup();
    const { container } = render(
      <PickSyllables
        syllables={syllables}
        correctIndices={correctIndices}
        category="закриті"
        explanation="Закритий склад закінчується на приголосний."
      />,
    );

    await user.click(optionButtons(container)[1]); // со-ба-ка (wrong)
    await user.click(screen.getByText('Перевірити'));

    const fb = feedback(container);
    expect(fb).toHaveAttribute('data-correct', 'false');
    expect(container.querySelector('[data-activity="pick-syllables-explanation"]')?.textContent).toBe(
      'Закритий склад закінчується на приголосний.',
    );
  });

  test('without explanation, no explanation element renders (V7 fallback)', async () => {
    const user = userEvent.setup();
    const { container } = render(
      <PickSyllables syllables={syllables} correctIndices={correctIndices} category="закриті" />,
    );

    await user.click(optionButtons(container)[0]);
    await user.click(screen.getByText('Перевірити'));

    expect(container.querySelector('[data-activity="pick-syllables-explanation"]')).not.toBeInTheDocument();
  });

  test('renders instruction when provided', () => {
    render(
      <PickSyllables
        syllables={syllables}
        correctIndices={correctIndices}
        category="закриті"
        instruction="Виберіть закриті склади"
      />,
    );
    expect(screen.getByText('Виберіть закриті склади')).toBeInTheDocument();
  });
});
