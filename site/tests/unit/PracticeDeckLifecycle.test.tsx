import '@testing-library/jest-dom/vitest';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { act, cleanup, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LexiconPractice from '@site/src/components/LexiconPractice';
import { loadState, type PracticeDeckData } from '@site/src/lib/lexicon/srs';
import { buildFixturePayloads } from '../helpers/teacher-deck-fixture';

const initialDeck: PracticeDeckData = {
  deckVersion: 'lifecycle-fixture',
  level: 'A1',
  lexemes: [],
  index: [],
  cloze: [],
};

function jsonResponse(body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });
}

function fixtureFetch({ holdLexemes = false } = {}) {
  const pending: Array<() => void> = [];
  const requested: string[] = [];
  const { deck, cloze } = buildFixturePayloads();
  const fetch = vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
    const url = String(input);
    requested.push(url);
    if (url.endsWith('/daily-pool.json')) return jsonResponse([]);
    if (url.endsWith('/practice-deck.teacher.json')) return jsonResponse(deck);
    if (url.endsWith('/practice-cloze.teacher.json')) return jsonResponse(cloze);
    if (/practice-lexemes\.[ABC][12]\.json$/.test(url)) {
      if (holdLexemes) {
        return new Promise<Response>((resolve) => {
          pending.push(() => resolve(jsonResponse({ lexemes: [] })));
        });
      }
      return jsonResponse({ lexemes: [] });
    }
    return new Response(null, { status: 404 });
  });
  return { fetch, requested, release: () => pending.splice(0).forEach((resolve) => resolve()) };
}

beforeEach(() => {
  localStorage.clear();
  loadState(localStorage);
  document.documentElement.dataset.chromeLocale = 'en';
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('practice deck loading and switching', () => {
  test.each(['en', 'uk'] as const)('switches to curated and back using local responses in %s', async (locale) => {
    document.documentElement.dataset.chromeLocale = locale;
    const { requested } = fixtureFetch();
    const user = userEvent.setup();
    render(<LexiconPractice initialDeck={initialDeck} />);
    await screen.findByTestId('practice-daily-deck-title');

    await user.click(screen.getByTestId('practice-active-deck-chip'));
    await user.click(screen.getByTestId('practice-deck-option-virtual_teacher_lesson'));
    const curated = await screen.findByTestId('practice-daily-deck-title');
    expect(curated.querySelector('[data-loc="en"]')).toHaveTextContent('Words of the day — Curated Deck');
    expect(curated.querySelector('[data-loc="uk"]')).toHaveTextContent('Слова дня — Відібрана добірка');
    expect(screen.queryByTestId('practice-daily-deck-loading')).not.toBeInTheDocument();
    expect(requested).toContain('/lexicon/search-shards.json');
    expect(requested).toContain('/lexicon/search-index.json');

    await user.click(screen.getByTestId('practice-active-deck-chip'));
    await user.click(screen.getByTestId('practice-deck-option-all'));
    const all = await screen.findByTestId('practice-daily-deck-title');
    expect(all).not.toHaveTextContent('Curated Deck');
    expect(all).not.toHaveTextContent('Відібрана добірка');
    expect(requested.filter((url) => url.endsWith('/daily-pool.json'))).toHaveLength(1);
  });

  test('ignores a late curated response after switching back to All Words', async () => {
    const { release } = fixtureFetch({ holdLexemes: true });
    const user = userEvent.setup();
    render(<LexiconPractice initialDeck={initialDeck} />);
    await screen.findByTestId('practice-daily-deck-title');

    await user.click(screen.getByTestId('practice-active-deck-chip'));
    await user.click(screen.getByTestId('practice-deck-option-virtual_teacher_lesson'));
    expect(screen.getByTestId('practice-daily-deck-loading')).toHaveTextContent('Curated Deck');
    await user.click(screen.getByTestId('practice-active-deck-chip'));
    await user.click(screen.getByTestId('practice-deck-option-all'));
    const all = await screen.findByTestId('practice-daily-deck-title');
    expect(all).not.toHaveTextContent('Curated Deck');
    expect(screen.getByTestId('practice-daily-empty')).toBeInTheDocument();

    await act(async () => { release(); });
    expect(screen.getByTestId('practice-daily-deck-title')).toBe(all);
    expect(screen.getByTestId('practice-daily-empty')).toBeInTheDocument();
    expect(within(screen.getByTestId('practice-daily-deck')).queryAllByRole('listitem', { hidden: true })).toHaveLength(0);
    expect(screen.getByTestId('practice-active-deck-chip')).toHaveTextContent('All Words (A1)');
    expect(screen.queryByTestId('practice-daily-deck-loading')).not.toBeInTheDocument();
  });

  test('loads the artifact deck and returns to curated without retaining the artifact view', async () => {
    fixtureFetch();
    const user = userEvent.setup();
    render(<LexiconPractice initialDeck={initialDeck} />);
    await user.click(screen.getByTestId('practice-active-deck-chip'));
    await user.click(screen.getByTestId('practice-deck-option-virtual_teacher_table'));
    expect(await screen.findByTestId('teacher-deck-start')).toBeInTheDocument();
    const artifact = screen.getByTestId('teacher-deck-practice');

    await user.click(within(artifact).getByTestId('practice-active-deck-chip'));
    await user.click(screen.getByTestId('practice-deck-option-virtual_teacher_lesson'));
    expect(await screen.findByTestId('practice-daily-deck-title')).toHaveTextContent('Curated Deck');
    expect(screen.queryByTestId('teacher-deck-practice')).not.toBeInTheDocument();
  });
});
