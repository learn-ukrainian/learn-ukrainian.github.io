import { render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import LiveStatus, { deriveLiveStatus } from '@site/src/components/LiveStatus';

describe('deriveLiveStatus', () => {
  it('marks shippable modules as passing', () => {
    expect(deriveLiveStatus({
      shippable: true,
      phases: { publish: { status: 'pending' } },
      audit: { status: 'fail', word_count: 120, word_target: 150, blocking_issues: ['x'] },
    }, 'done')).toEqual({
      kind: 'passing',
      title: '120/150 words',
    });
  });

  it('marks audit failures and blocking issues as failing', () => {
    expect(deriveLiveStatus({
      audit: { status: 'pass', word_count: 140, word_target: 150, blocking_issues: ['gate'] },
      phases: { publish: { status: 'complete' } },
    }, 'done')).toEqual({
      kind: 'failing',
      title: '140/150 words',
    });
  });

  it('marks stale audits as stale', () => {
    expect(deriveLiveStatus({
      audit: { status: 'stale', word_count: 140, word_target: 150, blocking_issues: [] },
      phases: { publish: { status: 'complete' } },
    }, 'active')).toEqual({
      kind: 'stale',
      title: '140/150 words',
    });
  });

  it('marks incomplete publish phases as building', () => {
    expect(deriveLiveStatus({
      audit: { status: 'pass', word_count: 140, word_target: 150, blocking_issues: [] },
      phases: { publish: { status: 'running' } },
    }, 'done')).toEqual({
      kind: 'building',
      title: '140/150 words',
    });
  });
});

describe('LiveStatus', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('fetches live state and renders the derived icon with word count hover text', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        shippable: true,
        phases: { publish: { status: 'complete' } },
        audit: { status: 'pass', word_count: 512, word_target: 600, blocking_issues: [] },
      }),
    });
    vi.stubGlobal('fetch', fetchMock);

    render(<LiveStatus track="a1" num={24} fallback="done" />);

    await waitFor(() => {
      expect(screen.getByTitle('512/600 words')).toHaveTextContent('\u2705');
    });
    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8765/api/state/module/a1/24',
      expect.objectContaining({ signal: expect.any(AbortSignal) }),
    );
  });

  it('falls back silently when the fetch fails', async () => {
    const fetchMock = vi.fn().mockRejectedValue(new Error('offline'));
    vi.stubGlobal('fetch', fetchMock);

    const { container } = render(<LiveStatus track="a1" num={13} fallback="active" />);

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(1);
    });
    expect(container).toHaveTextContent('\u25B6\uFE0F');
    expect(container.querySelector('[title]')).toBeNull();
  });

  it('aborts the in-flight request on unmount', () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({}),
    });
    vi.stubGlobal('fetch', fetchMock);

    const { unmount } = render(<LiveStatus track="a1" num={24} fallback="done" />);
    const signal = fetchMock.mock.calls[0]?.[1]?.signal as AbortSignal;

    expect(signal.aborted).toBe(false);
    unmount();
    expect(signal.aborted).toBe(true);
  });
});
