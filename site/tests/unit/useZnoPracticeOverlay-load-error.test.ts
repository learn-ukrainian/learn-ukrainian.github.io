/**
 * #7673 CF: a rejected `loadZnoDeck` chunk download must not leave the ZNO
 * overlay stuck on "loading" forever. Isolated from useZnoPracticeOverlay.test.ts
 * because it mocks loadZnoDeck module-wide (vi.mock is hoisted); the happy-path
 * test needs the real dynamic-import loader.
 */
import { afterEach, describe, expect, test, vi } from 'vitest';
import { act, renderHook, waitFor } from '@testing-library/react';

vi.mock('@site/src/components/ZnoPractice', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@site/src/components/ZnoPractice')>();
  return {
    ...actual,
    loadZnoDeck: vi.fn(() => Promise.reject(new Error('chunk load failed'))),
  };
});

import { loadZnoDeck } from '@site/src/components/ZnoPractice';
import { useZnoPracticeOverlay } from '@site/src/components/useZnoPracticeOverlay';

describe('useZnoPracticeOverlay — rejected chunk download (#7673 CF)', () => {
  afterEach(() => {
    vi.mocked(loadZnoDeck).mockClear();
  });

  test('surfaces a retryable error instead of leaving the overlay stuck loading', async () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
    const { result } = renderHook(() => useZnoPracticeOverlay());

    act(() => {
      result.current.setActiveZnoDeckId('zno-stress');
    });
    expect(result.current.activeZnoDeckLoading).toBe(true);
    expect(result.current.activeZnoDeckError).toBe(false);

    await waitFor(() => expect(result.current.activeZnoDeckError).toBe(true));
    // The stuck-loading bug: activeZnoDeckLoading must flip false once the
    // rejection is handled, not stay true forever.
    expect(result.current.activeZnoDeckLoading).toBe(false);
    expect(result.current.activeZnoDeck).toBeNull();

    // Backing out of the overlay clears the error.
    act(() => {
      result.current.setActiveZnoDeckId(null);
    });
    expect(result.current.activeZnoDeckError).toBe(false);
    expect(result.current.activeZnoDeckLoading).toBe(false);

    consoleError.mockRestore();
  });

  test('retryActiveZnoDeck re-invokes the loader for the same deck', async () => {
    vi.spyOn(console, 'error').mockImplementation(() => {});
    const { result } = renderHook(() => useZnoPracticeOverlay());

    act(() => {
      result.current.setActiveZnoDeckId('zno-stress');
    });
    await waitFor(() => expect(result.current.activeZnoDeckError).toBe(true));
    expect(loadZnoDeck).toHaveBeenCalledTimes(1);

    act(() => {
      result.current.retryActiveZnoDeck();
    });
    expect(result.current.activeZnoDeckLoading).toBe(true);
    await waitFor(() => expect(result.current.activeZnoDeckError).toBe(true));
    expect(loadZnoDeck).toHaveBeenCalledTimes(2);
  });
});
