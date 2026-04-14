import { useEffect, useState } from 'react';

type FallbackStatus = 'done' | 'active' | 'todo' | 'locked';
type LiveStatusKind = FallbackStatus | 'passing' | 'failing' | 'stale' | 'building';

type LiveStatusProps = {
  track: string;
  num: number;
  fallback?: FallbackStatus;
};

type ModuleStateResponse = {
  shippable?: boolean;
  phases?: {
    publish?: {
      status?: string;
    };
  };
  audit?: {
    status?: string;
    word_count?: number;
    word_target?: number;
    blocking_issues?: unknown[];
  };
};

type ResolvedStatus = {
  kind: LiveStatusKind;
  title?: string;
};

const DEFAULT_MONITOR_API_BASE = 'http://localhost:8765';

const STATUS_ICONS: Record<LiveStatusKind, string> = {
  done: '\u2705',
  active: '\u25B6\uFE0F',
  todo: '',
  locked: '\uD83D\uDD12',
  passing: '\u2705',
  failing: '\u274C',
  stale: '\uD83D\uDD04',
  building: '\u23F3',
};

export function deriveLiveStatus(
  data: ModuleStateResponse,
  fallback: FallbackStatus,
): ResolvedStatus {
  const audit = data.audit ?? {};
  const blockingIssues = Array.isArray(audit.blocking_issues) ? audit.blocking_issues : [];

  let kind: LiveStatusKind = fallback;
  if (data.shippable === true) {
    kind = 'passing';
  } else if (audit.status === 'fail' || blockingIssues.length > 0) {
    kind = 'failing';
  } else if (audit.status === 'stale') {
    kind = 'stale';
  } else if (data.phases?.publish?.status !== 'complete') {
    kind = 'building';
  }

  const wordCount = typeof audit.word_count === 'number' ? audit.word_count : 0;
  const wordTarget = typeof audit.word_target === 'number' ? audit.word_target : 0;

  return {
    kind,
    title: `${wordCount}/${wordTarget} words`,
  };
}

function getMonitorApiBase(): string {
  const configuredBase = import.meta.env.PUBLIC_MONITOR_API_BASE;
  return (configuredBase || DEFAULT_MONITOR_API_BASE).replace(/\/+$/, '');
}

export default function LiveStatus({
  track,
  num,
  fallback = 'todo',
}: LiveStatusProps) {
  const [resolvedStatus, setResolvedStatus] = useState<ResolvedStatus>({ kind: fallback });

  useEffect(() => {
    const controller = new AbortController();

    void (async () => {
      try {
        const response = await fetch(
          `${getMonitorApiBase()}/api/state/module/${track}/${num}`,
          { signal: controller.signal },
        );

        if (!response.ok) {
          return;
        }

        const payload = await response.json() as ModuleStateResponse;
        setResolvedStatus(deriveLiveStatus(payload, fallback));
      } catch (error) {
        if (error instanceof Error && error.name === 'AbortError') {
          return;
        }
      }
    })();

    return () => {
      controller.abort();
    };
  }, [fallback, num, track]);

  return <span title={resolvedStatus.title}>{STATUS_ICONS[resolvedStatus.kind]}</span>;
}
