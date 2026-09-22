import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LexiconPractice from '@site/src/components/LexiconPractice';
import { dateSeed } from '@site/src/lib/lexicon/daily';
import {
  writePracticeSessionSnapshot,
  type PracticeDeckData,
  type PracticeLexeme,
  type PracticeSessionSnapshot,
} from '@site/src/lib/lexicon/srs';

function makeLexeme(
  lemmaId: string,
  lemma: string,
  gloss: string,
  cefr: 'A1' | 'A2' | 'B1',
): PracticeLexeme {
  return {
    lemmaId,
    lemma,
    lemmaPlain: lemma,
    gloss,
    ipa: null,
    paradigm: {
      cases: {
        nominative: { singular: lemma },
      },
    },
    cefr,
    pos: 'noun',
    heritage: 'native',
    severity: 'standard',
  };
}

function makeA1Deck(): PracticeDeckData {
  const item = makeLexeme('knyha', 'книга', 'book', 'A1');
  return {
    deckVersion: 'test-a1',
    level: 'A1',
    lexemes: [item],
    index: [
      {
        lemmaId: item.lemmaId,
        lemma: item.lemma,
        cefr: 'A1',
        modes: ['flashcards', 'choice', 'matching'],
        hasCloze: false,
        clozeIds: [],
        newOrder: 0,
      },
    ],
    cloze: [],
    stress: [],
    classify: [],
    paradigm: [],
    synonym: [],
    paronym: [],
    heritage: [],
  };
}

describe('Mobile Mixed Mode Transition (Issue #8382)', () => {
  let scrollIntoViewMock: ReturnType<typeof vi.fn>;
  const originalInnerWidth = window.innerWidth;
  const originalMatchMedia = window.matchMedia;

  beforeEach(() => {
    localStorage.clear();
    delete document.documentElement.dataset.chromeLocale;
    document.documentElement.lang = 'en';

    scrollIntoViewMock = vi.fn();
    Element.prototype.scrollIntoView = scrollIntoViewMock as unknown as typeof Element.prototype.scrollIntoView;

    vi.spyOn(globalThis, 'fetch').mockImplementation(async () =>
      new Response(JSON.stringify([]), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );
  });

  afterEach(() => {
    delete document.documentElement.dataset.chromeLocale;
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: originalInnerWidth,
    });
    window.matchMedia = originalMatchMedia;
    vi.restoreAllMocks();
  });

  describe('AC-01: Direct session initiation on Mixed mode click', () => {
    test('Tapping Mixed mode card immediately transitions to active practice session', async () => {
      const user = userEvent.setup();
      const { container } = render(
        <LexiconPractice initialDeck={makeA1Deck()} deckLevel="A1" />,
      );

      // Verify initially idle with dashboard
      expect(screen.getByTestId('practice-dashboard-session')).toBeInTheDocument();
      expect(screen.queryByTestId('practice-stage-shell')).not.toBeInTheDocument();

      const mixedModeBtn = container.querySelector<HTMLButtonElement>('button[data-mode="mixed"]');
      expect(mixedModeBtn).toBeInTheDocument();

      await user.click(mixedModeBtn!);

      // Immediately transitions to active session
      await waitFor(() => {
        expect(screen.getByTestId('practice-stage-shell')).toBeInTheDocument();
      });
      expect(screen.getByTestId('practice-session-progress')).toBeInTheDocument();
      expect(screen.queryByTestId('practice-dashboard-session')).not.toBeInTheDocument();
    });

    test('Tapping Mixed mode resumes existing resumable session snapshot', async () => {
      const user = userEvent.setup();
      const existingSnapshot: PracticeSessionSnapshot = {
        sessionSeed: 12345,
        history: [],
        budget: 20,
        completed: 2,
        modeFilter: 'mixed',
        level: 'A1',
        deckId: 'all',
        dateSeed: dateSeed(new Date()),
        startedAt: Date.now() - 1000,
        extensionUsed: 0,
        sessionNewIntroduced: 0,
        plannedReviews: 5,
        plannedNew: 5,
        plannedTotal: 10,
        reviewsCompleted: 2,
        unresolvedCardKeys: [],
      };
      writePracticeSessionSnapshot('mixed', existingSnapshot);

      const { container } = render(
        <LexiconPractice initialDeck={makeA1Deck()} deckLevel="A1" />,
      );

      const mixedModeBtn = container.querySelector<HTMLButtonElement>('button[data-mode="mixed"]');
      expect(mixedModeBtn).toBeInTheDocument();

      await user.click(mixedModeBtn!);

      await waitFor(() => {
        expect(screen.getByTestId('practice-stage-shell')).toBeInTheDocument();
      });
      // Progress reflects resumed session (2 completed)
      expect(screen.getByTestId('practice-session-progress')).toHaveTextContent(/2/);
    });
  });

  describe('AC-02: Viewport auto-scroll on mobile viewports', () => {
    test('Scrolls smoothly to stage shell on mobile viewport (<= 820px)', async () => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 390, // iPhone 14
      });
      window.matchMedia = vi.fn().mockImplementation((query: string) => ({
        matches: query.includes('max-width: 820px'),
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      }));

      const user = userEvent.setup();
      const { container } = render(
        <LexiconPractice initialDeck={makeA1Deck()} deckLevel="A1" />,
      );

      const mixedModeBtn = container.querySelector<HTMLButtonElement>('button[data-mode="mixed"]');
      await user.click(mixedModeBtn!);

      await waitFor(() => {
        expect(scrollIntoViewMock).toHaveBeenCalledWith({
          behavior: 'smooth',
          block: 'start',
        });
      });
    });

    test('Honors prefers-reduced-motion: reduce with auto behavior on mobile', async () => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 412, // Pixel 7
      });
      window.matchMedia = vi.fn().mockImplementation((query: string) => ({
        matches: query.includes('max-width: 820px') || query.includes('prefers-reduced-motion'),
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      }));

      const user = userEvent.setup();
      const { container } = render(
        <LexiconPractice initialDeck={makeA1Deck()} deckLevel="A1" />,
      );

      const mixedModeBtn = container.querySelector<HTMLButtonElement>('button[data-mode="mixed"]');
      await user.click(mixedModeBtn!);

      await waitFor(() => {
        expect(scrollIntoViewMock).toHaveBeenCalledWith({
          behavior: 'instant',
          block: 'start',
        });
      });
    });

    test('Non-goal: Desktop viewport does NOT auto-scroll', async () => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1200, // Desktop
      });
      window.matchMedia = vi.fn().mockImplementation((query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      }));

      const user = userEvent.setup();
      const { container } = render(
        <LexiconPractice initialDeck={makeA1Deck()} deckLevel="A1" />,
      );

      const mixedModeBtn = container.querySelector<HTMLButtonElement>('button[data-mode="mixed"]');
      await user.click(mixedModeBtn!);

      await waitFor(() => {
        expect(screen.getByTestId('practice-stage-shell')).toBeInTheDocument();
      });
      expect(scrollIntoViewMock).not.toHaveBeenCalled();
    });
  });

  describe('Stop policy: Daily deck visibility and re-roll when idle', () => {
    test('Daily deck hero card and re-roll button remain visible and functional in idle state', async () => {
      const user = userEvent.setup();
      render(<LexiconPractice initialDeck={makeA1Deck()} deckLevel="A1" />);

      // Hero card is present on idle once snapshot loads
      await waitFor(() => {
        expect(screen.getByTestId('practice-daily-deck')).toBeInTheDocument();
      });
      const rerollBtn = screen.getByTestId('practice-daily-reroll');
      expect(rerollBtn).toBeInTheDocument();

      // Clicking re-roll does not start session, remains idle
      await user.click(rerollBtn);
      expect(screen.getByTestId('practice-daily-deck')).toBeInTheDocument();
      expect(screen.queryByTestId('practice-stage-shell')).not.toBeInTheDocument();
    });
  });
});
