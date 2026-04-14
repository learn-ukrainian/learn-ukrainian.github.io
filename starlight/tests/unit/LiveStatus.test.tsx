import { render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import LiveStatus, { deriveLiveStatus } from '@site/src/components/LiveStatus';

describe('deriveLiveStatus', () => {
  it('prioritizes audit failure over a shippable flag', () => {
    // Gemini review #1228: shippable=true must NOT shadow a failed audit.
    expect(deriveLiveStatus({
      shippable: true,
      phases: { publish: { status: 'complete' } },
      audit: { status: 'fail', word_count: 120, word_target: 150, blocking_issues: ['x'] },
    }, 'done')).toEqual({
      kind: 'failing',
      title: '120/150 words',
    });
  });

  it('marks audit=pass + publish=complete + shippable=true as passing', () => {
    expect(deriveLiveStatus({
      shippable: true,
      phases: { publish: { status: 'complete' } },
      audit: { status: 'pass', word_count: 140, word_target: 150, blocking_issues: [] },
    }, 'done')).toEqual({
      kind: 'passing',
      title: '140/150 words',
    });
  });

  it('marks audit=pass + publish=complete as passing even when shippable is false', () => {
    // Common case on A1: audit passes but the pipeline has not yet flagged
    // the module as shippable. We still want the green badge.
    expect(deriveLiveStatus({
      shippable: false,
      phases: { publish: { status: 'complete' } },
      audit: { status: 'pass', word_count: 140, word_target: 150, blocking_issues: [] },
    }, 'done')).toEqual({
      kind: 'passing',
      title: '140/150 words',
    });
  });

  it('marks blocking issues as failing even with audit=pass', () => {
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

  it('marks incomplete publish phases as building (even when shippable=true)', () => {
    expect(deriveLiveStatus({
      shippable: true,
      audit: { status: 'pass', word_count: 140, word_target: 150, blocking_issues: [] },
      phases: { publish: { status: 'running' } },
    }, 'done')).toEqual({
      kind: 'building',
      title: '140/150 words',
    });
  });

  it('treats unknown publish state as building (API returned sparse payload)', () => {
    // When the API responds with no phase info, we can't confirm a completed
    // deploy — surface that as "building" rather than the stale fallback.
    expect(deriveLiveStatus({}, 'active')).toEqual({
      kind: 'building',
      title: '0/0 words',
    });
  });
});

describe('LiveStatus', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
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
      expect(screen.getByRole('img', { name: 'Module passing audit' })).toHaveTextContent('\u2705');
    });
    expect(screen.getByTitle('512/600 words')).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8765/api/state/module/a1/24',
      expect.objectContaining({ signal: expect.any(AbortSignal) }),
    );
  });

  it('does not setState when unmounted between fetch() and json()', async () => {
    let resolveJson: ((value: unknown) => void) | undefined;
    const jsonPromise = new Promise<unknown>((r) => { resolveJson = r; });
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => jsonPromise,
    });
    vi.stubGlobal('fetch', fetchMock);

    const { unmount, container } = render(
      <LiveStatus track="a1" num={24} fallback="done" />,
    );
    // Let fetch() resolve; the microtask queue reaches the `await response.json()` boundary.
    await Promise.resolve();
    unmount();
    // Unmount aborted the controller; now deliver the JSON payload.
    resolveJson?.({
      shippable: true,
      phases: { publish: { status: 'complete' } },
      audit: { status: 'pass', word_count: 1, word_target: 1, blocking_issues: [] },
    });
    await Promise.resolve();
    // Badge must not have updated — container is empty after unmount.
    expect(container.innerHTML).toBe('');
  });

  it('skips the fetch in a production bundle without PUBLIC_MONITOR_API_BASE', async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);
    // In tests `import.meta.env.DEV` is true by default; override for this case.
    vi.stubEnv('DEV', false);
    vi.stubEnv('PUBLIC_MONITOR_API_BASE', '');

    const { container } = render(<LiveStatus track="a1" num={24} fallback="done" />);

    expect(fetchMock).not.toHaveBeenCalled();
    // Fallback icon is rendered; no title (we never saw audit data).
    expect(container).toHaveTextContent('\u2705');
    expect(container.querySelector('[title]')).toBeNull();
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
