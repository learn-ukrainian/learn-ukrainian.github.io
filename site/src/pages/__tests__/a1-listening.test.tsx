import { describe, it, expect } from 'vitest';
import { render, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Quiz from '../../components/Quiz';

describe('A1 listening quiz media', () => {
  it('plays each item’s pack video beside its options and keeps the correct key', async () => {
    const user = userEvent.setup();
    // Inspect the real iframe URL without loading a third-party page in the test DOM.
    const settings = (window as unknown as { happyDOM: { settings: { disableIframePageLoading: boolean } } }).happyDOM.settings;
    const previous = settings.disableIframePageLoading;
    settings.disableIframePageLoading = true;
    const urls = [
      'https://www.youtube.com/watch?v=g4Bh-lqzd48',
      'https://www.youtube.com/watch?v=BhASNxitC1A',
    ];
    const { container } = render(<Quiz questions={urls.map((url, index) => ({
      question: 'Listen and choose.',
      options: [{ text: 'First', correct: index === 0 }, { text: 'Second', correct: index === 1 }],
      host: { kind: 'video', url, label: 'Ukrainian Lessons Podcast' },
    }))} />);
    const items = container.querySelectorAll<HTMLElement>('[data-activity="quiz-question"]');
    expect(items).toHaveLength(2);
    for (let i = 0; i < items.length; i++) {
      const media = items[i].querySelector<HTMLElement>('[data-activity="listening-host"]')!;
      expect(media.querySelector('img')?.getAttribute('src')).toContain(urls[i].split('v=')[1]);
      const options = items[i].querySelector<HTMLElement>('[data-activity="quiz-options"]')!;
      expect(media.compareDocumentPosition(options) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
      await user.click(within(media).getByRole('button'));
      expect(media.querySelector('iframe')?.getAttribute('src')).toContain(urls[i].split('v=')[1]);
      await user.click(within(options).getByRole('button', { name: i === 0 ? 'First' : 'Second' }));
      expect(items[i].querySelector('[data-activity="quiz-feedback"]')?.getAttribute('data-correct')).toBe('true');
    }
    settings.disableIframePageLoading = previous;
  });

  it('links a podcast without inventing an embed or speech', () => {
    const url = 'https://www.ukrainianlessons.com/episode1/';
    const { container } = render(<Quiz questions={[{
      question: 'Listen and choose.',
      options: [{ text: 'First', correct: true }, { text: 'Second', correct: false }],
      host: { kind: 'video', url, label: 'Ukrainian Lessons Podcast' },
    }]} />);
    expect(within(container).getByRole('link').getAttribute('href')).toBe(url);
    expect(container.querySelector('iframe')).toBeNull();
  });

  it('leaves ordinary quiz items playable without a media host', () => {
    const { container } = render(<Quiz questions={[{
      question: 'Choose.', options: [{ text: 'First', correct: true }, { text: 'Second', correct: false }],
    }]} />);
    expect(container.querySelector('[data-activity="listening-host"]')).toBeNull();
    expect(within(container).getAllByRole('button').length).toBeGreaterThanOrEqual(2);
  });
});
