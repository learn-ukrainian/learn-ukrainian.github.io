import { describe, expect, test, beforeEach } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import {
  chromeFacingBilingual,
  readChromeLocale,
  useActivityIsUkrainian,
} from '../../src/lib/i18n/useChromeLocale';
import Unjumble from '../../src/components/Unjumble';
import ErrorCorrection from '../../src/components/ErrorCorrection';
import userEvent from '@testing-library/user-event';

function Probe() {
  const uk = useActivityIsUkrainian(false);
  return <span>{uk ? 'uk-chrome' : 'en-chrome'}</span>;
}

describe('useChromeLocale / activity chrome', () => {
  beforeEach(() => {
    document.documentElement.dataset.chromeLocale = 'en';
  });

  test('readChromeLocale follows data-chrome-locale', () => {
    document.documentElement.dataset.chromeLocale = 'uk';
    expect(readChromeLocale()).toBe('uk');
  });

  test('activity chrome follows toggle even when baked isUkrainian=false', async () => {
    const { rerender } = render(<Probe />);
    expect(screen.getByText('en-chrome')).toBeInTheDocument();
    act(() => {
      document.documentElement.dataset.chromeLocale = 'uk';
    });
    rerender(<Probe />);
    // MutationObserver may need a tick
    await act(async () => {
      await Promise.resolve();
    });
    expect(screen.getByText('uk-chrome')).toBeInTheDocument();
  });

  test('chromeFacingBilingual picks the locale side', () => {
    const s = 'Складіть слово. — Build the word.';
    expect(chromeFacingBilingual(s, 'uk')).toBe('Складіть слово.');
    expect(chromeFacingBilingual(s, 'en')).toBe('Build the word.');
  });
});

describe('ErrorCorrection choice chips', () => {
  beforeEach(() => {
    document.documentElement.dataset.chromeLocale = 'en';
  });

  test('after finding the error, shows option chips when options are provided', async () => {
    const user = userEvent.setup();
    render(
      <ErrorCorrection
        items={[
          {
            sentence: 'Сього́дні га́рний ден.',
            errorWord: 'ден',
            correctForm: 'день',
            options: ['день', 'ден', 'дєнь'],
            explanation: 'soft sign',
          },
        ]}
      />
    );
    await user.click(screen.getByRole('button', { name: /Click to flag "ден"/i }));
    expect(screen.getByText(/Step 2/i)).toBeInTheDocument();
    const chips = document.querySelectorAll('[data-activity="error-correction-fix-chip"]');
    // The spotted error `ден` is not offered again (#8237).
    expect([...chips].map((el) => el.textContent).sort()).toEqual(['день', 'дєнь']);
    expect(chips).toHaveLength(2);
    expect(screen.queryByRole('button', { name: /Show correction/i })).not.toBeInTheDocument();
  });
});
