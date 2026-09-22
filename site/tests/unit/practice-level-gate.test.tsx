import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LexiconPractice from '@site/src/components/LexiconPractice';
import {
  LEARNER_LEVEL_STORAGE_KEY,
  calculateModeLevelRequirement,
  isCefrAtLeast,
} from '@site/src/lib/lexicon/levels';
import type { PracticeDeckData, PracticeLexeme } from '@site/src/lib/lexicon/srs';

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
    forms: { nominative: lemma, accusative: lemma, locative: lemma },
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

function makeA2Deck(): PracticeDeckData {
  const item = makeLexeme('bihate', 'бігати', 'to run', 'A2');
  return {
    deckVersion: 'test-a2',
    level: 'A2',
    lexemes: [item],
    index: [
      {
        lemmaId: item.lemmaId,
        lemma: item.lemma,
        cefr: 'A2',
        modes: ['flashcards', 'paronym', 'heritage'],
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
    paronym: [
      {
        paronymId: 'par-1',
        lemmaId: item.lemmaId,
        srsKey: 'bihate:paronym',
        lemma: 'бігати',
        confusable: 'бігти',
        distinction_gloss_uk: 'бігати регулярно, бігти зараз',
        frameIndex: 1,
        cefr: 'A2',
        prompt: 'Вранці він ___ у парку.',
        answer: 'бігає',
        options: [{ label: 'бігає' }, { label: 'біжить' }],
      },
    ],
    heritage: [
      {
        heritageId: 'her-1',
        lemmaId: item.lemmaId,
        srsKey: 'bihate:heritage',
        kind: 'lexical',
        severity: 'russianism',
        prompt: 'Оберіть питоме слово',
        answer: 'бігати',
        calque: 'стартувати',
        options: [{ label: 'бігати' }, { label: 'стартувати' }],
      },
    ],
  };
}

function makeB1Deck(): PracticeDeckData {
  const item = makeLexeme('vidtinok', 'відтінок', 'shade', 'B1');
  return {
    deckVersion: 'test-b1',
    level: 'B1',
    lexemes: [item],
    index: [
      {
        lemmaId: item.lemmaId,
        lemma: item.lemma,
        cefr: 'B1',
        modes: ['flashcards', 'paronym', 'heritage'],
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
    paronym: [
      {
        paronymId: 'par-b1',
        lemmaId: item.lemmaId,
        srsKey: 'vidtinok:paronym',
        lemma: 'відтінок',
        confusable: 'натяк',
        distinction_gloss_uk: 'відтінок кольору',
        frameIndex: 1,
        cefr: 'B1',
        prompt: 'Це тонкий ___ кольору.',
        answer: 'відтінок',
        options: [{ label: 'відтінок' }, { label: 'натяк' }],
      },
    ],
    heritage: [
      {
        heritageId: 'her-b1',
        lemmaId: item.lemmaId,
        srsKey: 'vidtinok:heritage',
        kind: 'lexical',
        severity: 'russianism',
        prompt: 'Оберіть питоме слово',
        answer: 'відтінок',
        calque: 'нюанс',
        options: [{ label: 'відтінок' }, { label: 'нюанс' }],
      },
    ],
  };
}

describe('Practice Level Gate (Issue #8380)', () => {
  beforeEach(() => {
    localStorage.clear();
    delete document.documentElement.dataset.chromeLocale;
    document.documentElement.lang = 'en';
    vi.spyOn(globalThis, 'fetch').mockImplementation(async () =>
      new Response(JSON.stringify([]), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );
  });

  afterEach(() => {
    delete document.documentElement.dataset.chromeLocale;
    vi.restoreAllMocks();
  });

  describe('AC-03: State calculation & isCefrAtLeast', () => {
    test('isCefrAtLeast compares CEFR hierarchy correctly', () => {
      expect(isCefrAtLeast('A1', 'A2')).toBe(false);
      expect(isCefrAtLeast('A2', 'A2')).toBe(true);
      expect(isCefrAtLeast('B1', 'A2')).toBe(true);
      expect(isCefrAtLeast('B2', 'A2')).toBe(true);
      expect(isCefrAtLeast('C1', 'A2')).toBe(true);
      expect(isCefrAtLeast('C2', 'A2')).toBe(true);
      expect(isCefrAtLeast(null, 'A2')).toBe(false);
      expect(isCefrAtLeast('invalid', 'A2')).toBe(false);
    });

    test('calculateModeLevelRequirement gates paronyms at A1 with 0 items', () => {
      const req = calculateModeLevelRequirement('paronym', 'A1', 0);
      expect(req.isGated).toBe(true);
      expect(req.minLevel).toBe('A2');
      expect(req.badgeText).toBe('A2+');
      expect(req.feedback?.en).toBe(
        'Paronyms are available starting at A2 level — switch level to practice',
      );
      expect(req.feedback?.uk).toBe(
        'Пароніми доступні з рівня A2 — змініть рівень для тренування',
      );
      expect(req.tooltip?.en).toBe(req.feedback?.en);
      expect(req.tooltip?.uk).toBe(req.feedback?.uk);
      expect(req.note?.uk).toBe('Доступно з рівня A2');
      expect(req.note?.en).toBe('Available from A2 level');
    });

    test('calculateModeLevelRequirement gates heritage at A1 with 0 items', () => {
      const req = calculateModeLevelRequirement('heritage', 'A1', 0);
      expect(req.isGated).toBe(true);
      expect(req.minLevel).toBe('A2');
      expect(req.badgeText).toBe('A2+');
      expect(req.feedback?.en).toBe(
        'Heritage exercises are available starting at A2 level — switch level to practice',
      );
      expect(req.feedback?.uk).toBe(
        'Питома лексика доступна з рівня A2 — змініть рівень для тренування',
      );
      expect(req.tooltip?.en).toBe(req.feedback?.en);
      expect(req.tooltip?.uk).toBe(req.feedback?.uk);
      expect(req.note?.uk).toBe('Доступно з рівня A2');
      expect(req.note?.en).toBe('Available from A2 level');
    });

    test('calculateModeLevelRequirement does not gate paronyms or heritage at A2 or B1 (Stop Policy)', () => {
      // At A2 with items
      expect(calculateModeLevelRequirement('paronym', 'A2', 17).isGated).toBe(false);
      expect(calculateModeLevelRequirement('heritage', 'A2', 44).isGated).toBe(false);

      // At A2 even with 0 items, level requirement is satisfied
      expect(calculateModeLevelRequirement('paronym', 'A2', 0).isGated).toBe(false);
      expect(calculateModeLevelRequirement('heritage', 'A2', 0).isGated).toBe(false);

      // At B1 with items
      expect(calculateModeLevelRequirement('paronym', 'B1', 69).isGated).toBe(false);
      expect(calculateModeLevelRequirement('heritage', 'B1', 265).isGated).toBe(false);
    });

    test('calculateModeLevelRequirement does not gate modes without level minimum', () => {
      expect(calculateModeLevelRequirement('flashcards', 'A1', 0).isGated).toBe(false);
      expect(calculateModeLevelRequirement('matching', 'A1', 0).isGated).toBe(false);
      expect(calculateModeLevelRequirement('choice', 'A1', 0).isGated).toBe(false);
      expect(calculateModeLevelRequirement('mixed', 'A1', 0).isGated).toBe(false);
    });
  });

  describe('AC-01 & AC-02: Level-gate badge, tooltip, and click feedback in UI', () => {
    test('A1 shows A2+ level requirement badge and tooltip on Paronyms and Heritage cards (AC-01, EN)', () => {
      localStorage.setItem(LEARNER_LEVEL_STORAGE_KEY, 'A1');
      document.documentElement.lang = 'en';
      const { container } = render(
        <LexiconPractice initialDeck={makeA1Deck()} deckLevel="A1" />,
      );

      // Paronym card
      const paronymBadge = screen.getByTestId('practice-mode-level-badge-paronym');
      expect(paronymBadge).toBeInTheDocument();
      expect(paronymBadge).toHaveTextContent('A2+');

      const paronymCard = container.querySelector<HTMLButtonElement>('[data-mode="paronym"]');
      expect(paronymCard).toBeInTheDocument();
      expect(paronymCard).toHaveAttribute('data-level-gated', 'true');
      expect(paronymCard).toHaveAttribute(
        'title',
        'Paronyms are available starting at A2 level — switch level to practice',
      );

      // Heritage card
      const heritageBadge = screen.getByTestId('practice-mode-level-badge-heritage');
      expect(heritageBadge).toBeInTheDocument();
      expect(heritageBadge).toHaveTextContent('A2+');

      const heritageCard = container.querySelector<HTMLButtonElement>('[data-mode="heritage"]');
      expect(heritageCard).toBeInTheDocument();
      expect(heritageCard).toHaveAttribute('data-level-gated', 'true');
      expect(heritageCard).toHaveAttribute(
        'title',
        'Heritage exercises are available starting at A2 level — switch level to practice',
      );
    });

    test('A1 shows Ukrainian tooltip when document lang is uk (AC-01, UK)', () => {
      localStorage.setItem(LEARNER_LEVEL_STORAGE_KEY, 'A1');
      document.documentElement.dataset.chromeLocale = 'uk';
      const { container } = render(
        <LexiconPractice initialDeck={makeA1Deck()} deckLevel="A1" />,
      );

      const paronymCard = container.querySelector<HTMLButtonElement>('[data-mode="paronym"]');
      expect(paronymCard).toHaveAttribute(
        'title',
        'Пароніми доступні з рівня A2 — змініть рівень для тренування',
      );

      const heritageCard = container.querySelector<HTMLButtonElement>('[data-mode="heritage"]');
      expect(heritageCard).toHaveAttribute(
        'title',
        'Питома лексика доступна з рівня A2 — змініть рівень для тренування',
      );
    });

    test('Clicking Paronyms at A1 displays feedback prompting learner to switch level (AC-02)', async () => {
      const user = userEvent.setup();
      localStorage.setItem(LEARNER_LEVEL_STORAGE_KEY, 'A1');
      const { container } = render(
        <LexiconPractice initialDeck={makeA1Deck()} deckLevel="A1" />,
      );

      const paronymCard = container.querySelector<HTMLButtonElement>('[data-mode="paronym"]');
      expect(paronymCard).toBeInTheDocument();

      await user.click(paronymCard!);

      const statusEl = container.querySelector('.lexicon-practice-status');
      expect(statusEl).toBeInTheDocument();
      expect(statusEl).toHaveTextContent(
        'Пароніми доступні з рівня A2 — змініть рівень для тренування',
      );
      expect(statusEl).toHaveTextContent(
        'Paronyms are available starting at A2 level — switch level to practice',
      );
      expect(screen.queryByTestId('practice-session-progress')).not.toBeInTheDocument();
    });

    test('Clicking Heritage at A1 displays feedback prompting learner to switch level (AC-02)', async () => {
      const user = userEvent.setup();
      localStorage.setItem(LEARNER_LEVEL_STORAGE_KEY, 'A1');
      const { container } = render(
        <LexiconPractice initialDeck={makeA1Deck()} deckLevel="A1" />,
      );

      const heritageCard = container.querySelector<HTMLButtonElement>('[data-mode="heritage"]');
      expect(heritageCard).toBeInTheDocument();

      await user.click(heritageCard!);

      const statusEl = container.querySelector('.lexicon-practice-status');
      expect(statusEl).toBeInTheDocument();
      expect(statusEl).toHaveTextContent(
        'Питома лексика доступна з рівня A2 — змініть рівень для тренування',
      );
      expect(statusEl).toHaveTextContent(
        'Heritage exercises are available starting at A2 level — switch level to practice',
      );
      expect(screen.queryByTestId('practice-session-progress')).not.toBeInTheDocument();
    });

    test('A2 and B1 levels do not show level-gate badges and tiles are enabled (Stop Policy & Denominator)', () => {
      // A2 Level
      localStorage.setItem(LEARNER_LEVEL_STORAGE_KEY, 'A2');
      const { container: containerA2, unmount: unmountA2 } = render(
        <LexiconPractice initialDeck={makeA2Deck()} deckLevel="A2" />,
      );

      expect(screen.queryByTestId('practice-mode-level-badge-paronym')).not.toBeInTheDocument();
      expect(screen.queryByTestId('practice-mode-level-badge-heritage')).not.toBeInTheDocument();

      const paronymA2 = containerA2.querySelector<HTMLButtonElement>('[data-mode="paronym"]');
      expect(paronymA2).not.toHaveAttribute('data-level-gated');
      expect(paronymA2).not.toBeDisabled();

      const heritageA2 = containerA2.querySelector<HTMLButtonElement>('[data-mode="heritage"]');
      expect(heritageA2).not.toHaveAttribute('data-level-gated');
      expect(heritageA2).not.toBeDisabled();

      unmountA2();

      // B1 Level
      localStorage.setItem(LEARNER_LEVEL_STORAGE_KEY, 'B1');
      const { container: containerB1 } = render(
        <LexiconPractice initialDeck={makeB1Deck()} deckLevel="B1" />,
      );

      expect(screen.queryByTestId('practice-mode-level-badge-paronym')).not.toBeInTheDocument();
      expect(screen.queryByTestId('practice-mode-level-badge-heritage')).not.toBeInTheDocument();

      const paronymB1 = containerB1.querySelector<HTMLButtonElement>('[data-mode="paronym"]');
      expect(paronymB1).not.toHaveAttribute('data-level-gated');
      expect(paronymB1).not.toBeDisabled();

      const heritageB1 = containerB1.querySelector<HTMLButtonElement>('[data-mode="heritage"]');
      expect(heritageB1).not.toHaveAttribute('data-level-gated');
      expect(heritageB1).not.toBeDisabled();
    });

    test('Live region element is persistently mounted in the DOM with aria-live="polite"', () => {
      localStorage.setItem(LEARNER_LEVEL_STORAGE_KEY, 'A1');
      const { container } = render(
        <LexiconPractice initialDeck={makeA1Deck()} deckLevel="A1" />,
      );

      const statusEl = container.querySelector('.lexicon-practice-status');
      expect(statusEl).toBeInTheDocument();
      expect(statusEl).toHaveAttribute('aria-live', 'polite');
      expect(statusEl).toHaveTextContent('');
    });

    test('Keyboard activation (Enter) triggers feedback announcement in the live region', async () => {
      const user = userEvent.setup();
      localStorage.setItem(LEARNER_LEVEL_STORAGE_KEY, 'A1');
      const { container } = render(
        <LexiconPractice initialDeck={makeA1Deck()} deckLevel="A1" />,
      );

      const paronymCard = container.querySelector<HTMLButtonElement>('[data-mode="paronym"]');
      expect(paronymCard).toBeInTheDocument();

      paronymCard!.focus();
      expect(paronymCard).toHaveFocus();
      await user.keyboard('{Enter}');

      const statusEl = container.querySelector('.lexicon-practice-status');
      expect(statusEl).toBeInTheDocument();
      expect(statusEl).toHaveTextContent(
        'Paronyms are available starting at A2 level — switch level to practice',
      );
    });

    test('Switching levels after clicking level-gated card clears stale feedback message', async () => {
      const user = userEvent.setup();
      localStorage.setItem(LEARNER_LEVEL_STORAGE_KEY, 'A1');
      const { container } = render(
        <LexiconPractice initialDeck={makeA1Deck()} deckLevel="A1" />,
      );

      const paronymCard = container.querySelector<HTMLButtonElement>('[data-mode="paronym"]');
      await user.click(paronymCard!);

      const statusEl = container.querySelector('.lexicon-practice-status');
      expect(statusEl).toHaveTextContent(
        'Paronyms are available starting at A2 level — switch level to practice',
      );

      // Switch level to A2
      const a2Btn = screen.getByRole('button', { name: 'A2' });
      await user.click(a2Btn);

      expect(statusEl).toHaveTextContent('');
    });
  });
});
