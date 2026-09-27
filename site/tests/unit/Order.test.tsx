import { describe, test, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Order from '@site/src/components/Order';

// Order shuffles the available lines on mount (seeded, so SSR/client match).
// Lines move by click, not drag, so the full check flow is testable here.

function availableTiles(container: HTMLElement) {
  const box = container.querySelector('[data-activity="order-available"]');
  if (!box) throw new Error('order-available not found');
  return [...box.querySelectorAll<HTMLButtonElement>('button')];
}

function selectedTiles(container: HTMLElement) {
  const box = container.querySelector('[data-activity="order-selected"]');
  if (!box) throw new Error('order-selected not found');
  return [...box.querySelectorAll<HTMLButtonElement>('button')];
}

function findAvailableByText(container: HTMLElement, text: string) {
  const btn = availableTiles(container).find((b) => b.textContent?.trim().endsWith(text));
  if (!btn) throw new Error(`available line "${text}" not found`);
  return btn;
}

function checkButton(container: HTMLElement) {
  return [...container.querySelectorAll<HTMLButtonElement>('button')].find(
    (b) => b.textContent?.trim() === 'Check' || b.textContent?.trim() === 'Перевірити',
  );
}

function feedback(container: HTMLElement) {
  return container.querySelector('[data-activity="order-feedback"]');
}

describe('Order', () => {
  beforeEach(() => {
    document.documentElement.dataset.chromeLocale = 'en';
  });

  const items = ['First', 'Second', 'Third'];
  const correct_order = [0, 1, 2];

  test('wraps everything in an order activity container', () => {
    const { container } = render(<Order items={items} correct_order={correct_order} />);
    expect(container.querySelector('[data-activity="order"]')).toBeInTheDocument();
  });

  test('renders every line as an available tile before ordering', () => {
    const { container } = render(<Order items={items} correct_order={correct_order} />);
    expect(availableTiles(container)).toHaveLength(3);
    expect(selectedTiles(container)).toHaveLength(0);
  });

  test('Check is disabled until every line has been placed', () => {
    const { container } = render(<Order items={items} correct_order={correct_order} />);
    expect(checkButton(container)).toBeDisabled();
  });

  test('clicking an available line moves it into the selected zone', async () => {
    const user = userEvent.setup();
    const { container } = render(<Order items={items} correct_order={correct_order} />);

    await user.click(findAvailableByText(container, 'First'));

    expect(selectedTiles(container)).toHaveLength(1);
    expect(availableTiles(container)).toHaveLength(2);
  });

  test('placing lines in the correct order and checking shows correct feedback with the explanation', async () => {
    const user = userEvent.setup();
    const { container } = render(
      <Order items={items} correct_order={correct_order} explanation="Chronological order." />,
    );

    for (const text of ['First', 'Second', 'Third']) {
      await user.click(findAvailableByText(container, text));
    }
    await user.click(checkButton(container)!);

    const fb = feedback(container);
    expect(fb).toBeInTheDocument();
    expect(fb).toHaveAttribute('data-correct', 'true');
    expect(fb).toHaveAttribute('role', 'status');
    expect(fb).toHaveAttribute('aria-live', 'polite');
    expect(container.querySelector('[data-activity="order-explanation"]')?.textContent).toBe(
      'Chronological order.',
    );
  });

  test('placing lines out of order and checking shows incorrect feedback with the explanation', async () => {
    const user = userEvent.setup();
    const { container } = render(
      <Order items={items} correct_order={correct_order} explanation="Chronological order." />,
    );

    for (const text of ['Third', 'Second', 'First']) {
      await user.click(findAvailableByText(container, text));
    }
    await user.click(checkButton(container)!);

    const fb = feedback(container);
    expect(fb).toHaveAttribute('data-correct', 'false');
    expect(container.querySelector('[data-activity="order-explanation"]')?.textContent).toBe(
      'Chronological order.',
    );
  });

  test('without explanation, no explanation element renders (V7 fallback)', async () => {
    const user = userEvent.setup();
    const { container } = render(<Order items={items} correct_order={correct_order} />);

    for (const text of ['First', 'Second', 'Third']) {
      await user.click(findAvailableByText(container, text));
    }
    await user.click(checkButton(container)!);

    expect(container.querySelector('[data-activity="order-explanation"]')).not.toBeInTheDocument();
    // #8889 A1-P3 finding 5: matches main exactly — no live region without explanation.
    const fb = feedback(container);
    expect(fb).not.toHaveAttribute('role');
    expect(fb).not.toHaveAttribute('aria-live');
  });

  test('renders instruction text when provided', () => {
    render(<Order items={items} correct_order={correct_order} instruction="Put the events in order" />);
    expect(screen.getByText('Put the events in order')).toBeInTheDocument();
  });
});
