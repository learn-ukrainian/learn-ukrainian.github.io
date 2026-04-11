import { describe, test, expect } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import WatchAndRepeat from '@site/src/components/WatchAndRepeat';

// WatchAndRepeat is a lazy YouTube player:
//  - Starts with a thumbnail button per item (no iframe in the DOM)
//  - Clicking play swaps the thumbnail for an <iframe>
//  - Prev/Next nav buttons move between items and reset the player
//  - Items without a parseable video show "Video unavailable"
//
// We DO NOT test the iframe itself — that requires real YouTube.
// We test the surrounding state machine and the progress indicator.

// ── helpers ──────────────────────────────────────────────────────────────────

function container(root: HTMLElement) {
  return root.querySelector('[data-activity="watch-and-repeat"]') as HTMLElement;
}

function prevBtn(root: HTMLElement) {
  return root.querySelector('[data-activity="war-prev"]') as HTMLButtonElement;
}

function nextBtn(root: HTMLElement) {
  return root.querySelector('[data-activity="war-next"]') as HTMLButtonElement;
}

function thumbnailBtn(root: HTMLElement) {
  return root.querySelector('[data-activity="war-thumbnail"]') as HTMLButtonElement | null;
}

function videoWrapper(root: HTMLElement) {
  return root.querySelector('[data-activity="war-video"]');
}

// ── WatchAndRepeat ────────────────────────────────────────────────────────────

describe('WatchAndRepeat initial render', () => {
  const items = [
    { video: 'https://www.youtube.com/watch?v=aaaaaaaaaaa', letter: 'А', note: 'vowel' },
    { video: 'https://youtu.be/bbbbbbbbbbb', letter: 'Б' },
    { video: 'https://www.youtube.com/embed/ccccccccccc', word: 'слово' },
  ];

  test('wraps everything in a watch-and-repeat container', () => {
    const { container: root } = render(<WatchAndRepeat items={items} />);
    expect(container(root)).toBeInTheDocument();
  });

  test('exposes the total item count via data-total', () => {
    const { container: root } = render(<WatchAndRepeat items={items} />);
    expect(container(root).getAttribute('data-total')).toBe('3');
  });

  test('starts at index 0', () => {
    const { container: root } = render(<WatchAndRepeat items={items} />);
    expect(container(root).getAttribute('data-current-index')).toBe('0');
  });

  test('progress indicator shows "1 / 3" initially', () => {
    const { container: root } = render(<WatchAndRepeat items={items} />);
    const progress = root.querySelector('[data-activity="war-progress"]');
    expect(progress?.textContent).toContain('1 / 3');
  });

  test('initial render shows a thumbnail button (iframe not loaded yet)', () => {
    const { container: root } = render(<WatchAndRepeat items={items} />);
    expect(thumbnailBtn(root)).toBeInTheDocument();
    expect(videoWrapper(root)).toBeNull();
    expect(root.querySelector('iframe')).toBeNull();
  });

  test('renders the letter when the item has one', () => {
    const { container: root } = render(<WatchAndRepeat items={items} />);
    expect(root.textContent).toContain('А');
  });

  test('renders the note when present', () => {
    const { container: root } = render(<WatchAndRepeat items={items} />);
    expect(root.textContent).toContain('vowel');
  });

  test('Previous button is disabled at index 0', () => {
    const { container: root } = render(<WatchAndRepeat items={items} />);
    expect(prevBtn(root)).toBeDisabled();
  });

  test('Next button is enabled when not at the last item', () => {
    const { container: root } = render(<WatchAndRepeat items={items} />);
    expect(nextBtn(root)).toBeEnabled();
  });

  test('renders the default Ukrainian header when isUkrainian omitted (defaults to true)', () => {
    render(<WatchAndRepeat items={items} />);
    expect(screen.getByText('Дивись і повторюй')).toBeInTheDocument();
  });

  test('renders the English header when isUkrainian=false', () => {
    render(<WatchAndRepeat items={items} isUkrainian={false} />);
    expect(screen.getByText('Watch and Repeat')).toBeInTheDocument();
  });

  test('renders a custom title when provided', () => {
    render(<WatchAndRepeat items={items} title="My Custom Title" />);
    expect(screen.getByText('My Custom Title')).toBeInTheDocument();
  });
});

describe('WatchAndRepeat play button interaction', () => {
  const items = [{ video: 'https://www.youtube.com/watch?v=abcdefghij1', letter: 'А' }];

  test('clicking the thumbnail swaps it for the iframe wrapper', async () => {
    const user = userEvent.setup();
    const { container: root } = render(<WatchAndRepeat items={items} />);

    expect(thumbnailBtn(root)).toBeInTheDocument();
    expect(videoWrapper(root)).toBeNull();

    await user.click(thumbnailBtn(root)!);

    expect(thumbnailBtn(root)).toBeNull();
    expect(videoWrapper(root)).toBeInTheDocument();
  });

  test('the iframe src is the YouTube embed URL with the correct video id', async () => {
    const user = userEvent.setup();
    const { container: root } = render(<WatchAndRepeat items={items} />);

    await user.click(thumbnailBtn(root)!);

    const iframe = root.querySelector('iframe') as HTMLIFrameElement;
    expect(iframe).toBeInTheDocument();
    expect(iframe.src).toContain('youtube.com/embed/abcdefghij1');
  });

  test('play button carries an aria-label', () => {
    const { container: root } = render(<WatchAndRepeat items={items} />);
    expect(thumbnailBtn(root)?.getAttribute('aria-label')).toBeTruthy();
  });
});

describe('WatchAndRepeat navigation', () => {
  const items = [
    { video: 'https://www.youtube.com/watch?v=aaaaaaaaaaa', letter: 'А' },
    { video: 'https://www.youtube.com/watch?v=bbbbbbbbbbb', letter: 'Б' },
    { video: 'https://www.youtube.com/watch?v=ccccccccccc', letter: 'В' },
  ];

  test('clicking Next advances to the second item', async () => {
    const user = userEvent.setup();
    const { container: root } = render(<WatchAndRepeat items={items} />);

    await user.click(nextBtn(root));

    expect(container(root).getAttribute('data-current-index')).toBe('1');
    expect(root.textContent).toContain('Б');
  });

  test('progress indicator updates after Next', async () => {
    const user = userEvent.setup();
    const { container: root } = render(<WatchAndRepeat items={items} />);

    await user.click(nextBtn(root));

    expect(root.querySelector('[data-activity="war-progress"]')?.textContent).toContain('2 / 3');
  });

  test('clicking Previous moves back', async () => {
    const user = userEvent.setup();
    const { container: root } = render(<WatchAndRepeat items={items} />);

    await user.click(nextBtn(root));
    await user.click(nextBtn(root));
    expect(container(root).getAttribute('data-current-index')).toBe('2');

    await user.click(prevBtn(root));
    expect(container(root).getAttribute('data-current-index')).toBe('1');
  });

  test('Previous is disabled at the first item and Next is disabled at the last', async () => {
    const user = userEvent.setup();
    const { container: root } = render(<WatchAndRepeat items={items} />);

    // Advance to the last item
    await user.click(nextBtn(root));
    await user.click(nextBtn(root));

    expect(nextBtn(root)).toBeDisabled();
    expect(prevBtn(root)).toBeEnabled();
  });

  test('switching items resets the playing state (thumbnail shows again)', async () => {
    const user = userEvent.setup();
    const { container: root } = render(<WatchAndRepeat items={items} />);

    await user.click(thumbnailBtn(root)!);
    expect(videoWrapper(root)).toBeInTheDocument();

    await user.click(nextBtn(root));

    // Thumbnail is back, iframe is gone
    expect(thumbnailBtn(root)).toBeInTheDocument();
    expect(videoWrapper(root)).toBeNull();
  });

  test('uses Ukrainian button labels when isUkrainian is true (default)', () => {
    const { container: root } = render(<WatchAndRepeat items={items} />);
    expect(prevBtn(root).textContent?.trim()).toBe('← Назад');
    expect(nextBtn(root).textContent?.trim()).toBe('Далі →');
  });

  test('uses English button labels when isUkrainian is false', () => {
    const { container: root } = render(<WatchAndRepeat items={items} isUkrainian={false} />);
    expect(prevBtn(root).textContent?.trim()).toBe('← Back');
    expect(nextBtn(root).textContent?.trim()).toBe('Next →');
  });
});

describe('WatchAndRepeat edge cases', () => {
  test('returns null when items is an empty array', () => {
    const { container: root } = render(<WatchAndRepeat items={[]} />);
    expect(root.firstChild).toBeNull();
  });

  test('returns null when items is undefined', () => {
    // @ts-expect-error — runtime null-safe path
    const { container: root } = render(<WatchAndRepeat items={undefined} />);
    expect(root.firstChild).toBeNull();
  });

  test('shows "Video unavailable" when URL has no parseable YouTube ID', () => {
    const items = [{ video: 'https://example.com/not-a-youtube-url', letter: 'А' }];
    const { container: root } = render(<WatchAndRepeat items={items} />);
    expect(root.textContent).toContain('Video unavailable');
    expect(thumbnailBtn(root)).toBeNull();
  });

  test('renders word instead of letter when letter is absent', () => {
    const items = [{ video: 'https://www.youtube.com/watch?v=aaaaaaaaaaa', word: 'мама' }];
    const { container: root } = render(<WatchAndRepeat items={items} />);
    expect(root.textContent).toContain('мама');
  });

  test('prefers letter over word when both are present', () => {
    const items = [{ video: 'https://www.youtube.com/watch?v=aaaaaaaaaaa', letter: 'А', word: 'ignore' }];
    const { container: root } = render(<WatchAndRepeat items={items} />);
    // Word is hidden by the `!item.letter` guard
    expect(root.querySelector('[class*="warLetterDisplay"]')).toBeInTheDocument();
    expect(root.querySelector('[class*="warWordDisplay"]')).toBeNull();
  });

  test('parses the /embed/ URL format correctly', async () => {
    const user = userEvent.setup();
    const items = [{ video: 'https://www.youtube.com/embed/embedVidId1' }];
    const { container: root } = render(<WatchAndRepeat items={items} />);

    await user.click(thumbnailBtn(root)!);

    const iframe = root.querySelector('iframe') as HTMLIFrameElement;
    expect(iframe.src).toContain('youtube.com/embed/embedVidId1');
  });

  test('parses the short youtu.be URL format correctly', async () => {
    const user = userEvent.setup();
    const items = [{ video: 'https://youtu.be/shortUrlId0' }];
    const { container: root } = render(<WatchAndRepeat items={items} />);

    await user.click(thumbnailBtn(root)!);

    const iframe = root.querySelector('iframe') as HTMLIFrameElement;
    expect(iframe.src).toContain('youtube.com/embed/shortUrlId0');
  });
});
