import { beforeEach, describe, expect, test } from 'vitest';
import { act, render, renderHook, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ErrorCorrectionPractice, {
  nextDueErrorCorrectionItem,
  type ErrorCorrectionDrill,
} from '@site/src/components/ErrorCorrectionPractice';
import {
  loadErrorCorrectionDeck,
  useErrorCorrectionPracticeOverlay,
} from '@site/src/components/useErrorCorrectionPracticeOverlay';
import { SRS_STORAGE_KEY, cardKey, loadState, rateCard } from '@site/src/lib/lexicon/srs';

const mockDrills: ErrorCorrectionDrill[] = [
  {
    id: 'err_0001',
    sentence: 'Уважно прочитайте: «україномовний» — тут допущено помилку.',
    errorWord: 'україномовний',
    correctForm: 'українськомовний',
    options: [
      'україномовний',
      'україномовний (розм.)',
      'українськомовний',
      'українськомовний (застаріле)',
    ],
    explanation: 'Правильно вживати «українськомовний» замість помилкового «україномовний».',
    isUkrainian: true,
    source: 'Textbook Gr 11 (avramenko)',
  },
  {
    id: 'err_0002',
    sentence: 'Уважно прочитайте: «природній» — тут допущено помилку.',
    errorWord: 'природній',
    correctForm: 'природний',
    options: [
      'природний',
      'природний (застаріле)',
      'природній',
      'природній (розм.)',
    ],
    explanation: 'Правильно вживати «природний» замість помилкового «природній».',
    isUkrainian: true,
    source: 'Textbook Gr 11 (avramenko)',
  },
];

describe('ErrorCorrectionPractice', () => {
  beforeEach(() => {
    localStorage.clear();
    loadState(localStorage);
  });

  test('loads production error-correction dataset with valid schema and non-empty drills', async () => {
    const drills = await loadErrorCorrectionDeck();
    expect(drills.length).toBe(278);
    for (const drill of drills) {
      expect(drill.id).toMatch(/^err_\d{4}$/);
      expect(drill.sentence.length).toBeGreaterThan(0);
      expect(drill.errorWord.length).toBeGreaterThan(0);
      expect(drill.correctForm.length).toBeGreaterThan(0);
      expect(drill.options.length).toBeGreaterThanOrEqual(2);
      expect(drill.options).toContain(drill.correctForm);
      expect(drill.sentence).toContain(drill.errorWord);
    }
  });

  test('nextDueErrorCorrectionItem prioritizes due cards over future cards', () => {
    rateCard('err_0001', 'choice', 'good', new Date(Date.now() + 86400000));
    rateCard('err_0002', 'choice', 'again', new Date(Date.now() - 1000));

    const next = nextDueErrorCorrectionItem(mockDrills, null);
    expect(next?.id).toBe('err_0002');
  });

  test('renders error correction drill, allows identifying error word and rating SRS', async () => {
    const user = userEvent.setup();
    render(<ErrorCorrectionPractice items={mockDrills} onBackToDecks={() => {}} chromeLocale="uk" />);

    expect(screen.getByTestId('drill-source-badge')).toHaveTextContent('📚 Textbook Gr 11 (avramenko)');
    expect(screen.getByTestId('drill-counter-badge')).toHaveTextContent('Виконано: 0 (правильно: 0)');

    // Step 1: Click the erroneous word
    const errorSpan = screen.getByText('україномовний');
    await user.click(errorSpan);

    // Step 2: Options appear; click the correct replacement
    const correctBtn = screen.getByRole('button', { name: 'українськомовний' });
    await user.click(correctBtn);

    // Feedback and next button appear
    expect(screen.getByText(/Правильно вживати «українськомовний»/)).toBeInTheDocument();
    expect(screen.getByTestId('error-correction-next-btn')).toBeInTheDocument();

    // SRS card is recorded
    expect(localStorage.getItem(SRS_STORAGE_KEY)).not.toBeNull();
    expect(loadState().cards.has(cardKey('err_0001', 'choice'))).toBe(true);

    // Click Next advances to the next drill
    await user.click(screen.getByTestId('error-correction-next-btn'));
    expect(screen.getByText('природній')).toBeInTheDocument();
    expect(screen.getByTestId('drill-counter-badge')).toHaveTextContent('Виконано: 1 (правильно: 1)');
  });

  test('useErrorCorrectionPracticeOverlay manages state transitions', async () => {
    const { result } = renderHook(() => useErrorCorrectionPracticeOverlay());
    expect(result.current.activeCulturePractice).toBe(false);
    expect(result.current.cultureDrills).toBeNull();

    act(() => {
      result.current.setActiveCulturePractice(true);
    });

    await waitFor(() => expect(result.current.cultureDrills).not.toBeNull());
    expect(result.current.cultureDrills?.length).toBe(278);
    expect(result.current.cultureLoading).toBe(false);

    act(() => {
      result.current.setActiveCulturePractice(false);
    });
    expect(result.current.activeCulturePractice).toBe(false);
  });
});
