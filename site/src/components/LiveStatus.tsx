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

const STATUS_LABELS: Record<LiveStatusKind, string> = {
  done: 'Module done',
  active: 'Module in progress',
  todo: 'Module not started',
  locked: 'Module locked',
  passing: 'Module passing audit',
  failing: 'Module failing audit',
  stale: 'Module audit stale',
  building: 'Module building',
};

export function deriveLiveStatus(
  data: ModuleStateResponse,
  fallback: FallbackStatus,
): ResolvedStatus {
  const audit = data.audit ?? {};
  const blockingIssues = Array.isArray(audit.blocking_issues) ? audit.blocking_issues : [];

  // Order matters: real failures > staleness > deploy-in-progress > green states.
  // Gemini review #1228: `shippable` must NOT shadow a failed/incomplete publish
  // phase, and `audit.status === 'pass'` should surface as green even when
  // the module is not yet flagged shippable by the pipeline.
  let kind: LiveStatusKind = fallback;
  if (audit.status === 'fail' || blockingIssues.length > 0) {
    kind = 'failing';
  } else if (audit.status === 'stale') {
    kind = 'stale';
  } else if (data.phases?.publish && data.phases.publish.status !== 'complete') {
    // Only assert "building" when the payload actually includes a publish
    // phase. Otherwise a sparse response (no `phases` key at all) would
    // shadow the audit.pass / shippable checks below and mis-render a
    // freshly-audited module as "building". (Gemini review #1228.)
    kind = 'building';
  } else if (data.shippable === true || audit.status === 'pass') {
    kind = 'passing';
  }

  const wordCount = typeof audit.word_count === 'number' ? audit.word_count : 0;
  const wordTarget = typeof audit.word_target === 'number' ? audit.word_target : 0;

  return {
    kind,
    title: `${wordCount}/${wordTarget} words`,
  };
}

function getMonitorApiBase(): string | null {
  const configuredBase = import.meta.env.PUBLIC_MONITOR_API_BASE;
  if (configuredBase) return String(configuredBase).replace(/\/+$/, '');
  // Dev-only fallback: never hit localhost from a production bundle,
  // which would trigger mixed-content blocks (HTTPS→HTTP) and CORS noise
  // in every visitor's console. In prod without config, disable the fetch
  // and let the frontmatter-derived fallback stay visible.
  if (import.meta.env.DEV) return DEFAULT_MONITOR_API_BASE;
  return null;
}

export default function LiveStatus({
  track,
  num,
  fallback = 'todo',
}: LiveStatusProps) {
  const [resolvedStatus, setResolvedStatus] = useState<ResolvedStatus>({ kind: fallback });

  useEffect(() => {
    const base = getMonitorApiBase();
    // Prod without PUBLIC_MONITOR_API_BASE: keep the frontmatter fallback,
    // don't fire a cross-origin request to localhost (mixed-content / CORS).
    if (base === null) {
      return;
    }

    const controller = new AbortController();

    void (async () => {
      try {
        const response = await fetch(
          `${base}/api/state/module/${track}/${num}`,
          { signal: controller.signal },
        );

        if (!response.ok) {
          return;
        }

        const payload = await response.json() as ModuleStateResponse;
        // Guard against setState-after-unmount: json() can resolve after
        // the effect's cleanup fires, and AbortError is only raised by
        // fetch(), not by response.json().
        if (controller.signal.aborted) {
          return;
        }
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

  return (
    <span
      role="img"
      aria-label={STATUS_LABELS[resolvedStatus.kind]}
      title={resolvedStatus.title}
    >
      {STATUS_ICONS[resolvedStatus.kind]}
    </span>
  );
}
