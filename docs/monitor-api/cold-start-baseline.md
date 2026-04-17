# Monitor API Cold-Start Baseline

Measurement log for GH #1309. Each run appends a new entry.
Compare successive runs to confirm each P0/P1 change reduces cost.

Run: `.venv/bin/python scripts/measure_cold_start.py --label "<label>"`

What "cold start" means here: a fresh agent session hitting the API to
orient itself, plus all repo files it has to read because the API does
not yet cover them. Each `(API call + file read)` pair is a separate
tool call with its own context cost.

---

## baseline-pre-caching — 2026-04-17 (first measurement, #1309)

### Observation: `/api/orient` is hanging

First live measurement caught `/api/orient` in a wedged state. Other
endpoints (`/api/health`, `/api/config`, `/api/state/summary`) responded
in 2-3 ms, but `/api/orient` failed to respond inside a 60 s timeout.
`gh issue list` ran standalone in ~2 s, so the hang is not the shellout
itself — it is the composed async handler that lacks caching and
failure-isolation.

This is the live reproduction of the review BLOCKER:

> `/api/orient` shells out to `git` and `gh issue list` on every call,
> with no endpoint-level cache. That is a latency/reliability problem.
> Fix caching, freshness metadata, and failure isolation before
> inventing more aggregation.

### Numbers (hang case)

- **Tool calls**: 1 API call + 8 file reads = **9 total**
- **Bytes**: 0 API (timeout) + 75,107 files = **75,107 total**
- **Est. input tokens**: ~18,776 (chars/4 heuristic)
- **API latency**: 30–60 s (timed out in both curl and urllib)

### API calls

| URL | Status | Bytes | Elapsed | Error |
|---|---|---|---|---|
| `http://localhost:8765/api/orient` | — | 0 | >30 s | TimeoutError |

### Manual file reads (NOT covered by API)

| Path | Exists | Bytes |
|---|---|---|
| `CLAUDE.md` | ✅ | 6,388 |
| `claude_extensions/rules/critical-rules.md` | ✅ | 1,339 |
| `claude_extensions/rules/non-negotiable-rules.md` | ✅ | 7,511 |
| `claude_extensions/rules/workflow.md` | ✅ | 4,138 |
| `docs/best-practices/agent-cooperation.md` | ✅ | 9,160 |
| `docs/session-state/current.md` | ✅ | 7,206 |
| `docs/WORKSTREAMS.md` | ✅ | 7,131 |
| `docs/MONITOR-API.md` | ✅ | 32,234 |
| **Total files** | | **75,107 b** |

### Baseline targets for the fix

- `/api/orient` unchanged-state: ≤ 1 call, < 100 bytes (304 or empty delta), < 200 ms.
- `/api/orient` changed-state: ≤ 3 calls, < 1000 input tokens, < 500 ms.
- File reads eliminated by P1 endpoints: rules (3 files → `/api/rules`), session (1 → `/api/session/current`), at least 4 of 8 total.

---

## post-onboarding — 2026-04-17 (P0+P1+P2+P3 + agent rules updated, #1309)

Measured via in-process FastAPI ``TestClient`` so the numbers reflect
the shipped code, not whatever happens to be running on localhost.

### Fresh-boot (no local cache yet)

| URL | Status | Bytes | Notes |
|---|---|---|---|
| `GET /api/state/manifest` | 200 | 778 | < 2 KB target ✓ |
| `GET /api/rules?format=markdown` | 200 | 14,305 | 3 rule files merged, ETag set |
| `GET /api/session/current` | 200 | 7,404 | current.md + 3 recent handoffs, ETag set |
| **Total API bytes** | | **22,487** | |

### Warm-cache re-entry (rules + session unchanged)

| URL | Status | Bytes | Notes |
|---|---|---|---|
| `GET /api/state/manifest` | 200 | 778 | always fetched — this IS the staleness check |
| `GET /api/rules?format=markdown` + `If-None-Match` | **304** | **0** | client reuses `.agent/cache/monitor/rules.body` |
| `GET /api/session/current` + `If-None-Match` | **304** | **0** | client reuses `.agent/cache/monitor/session.body` |
| **Total API bytes** | | **778** | |

### Delta vs. the first-measurement baseline

- **Tool calls**: 9 (1 API + 8 files, pre-P0) → 3 API (manifest + rules + session), no rule/session file reads required.
- **Payload bytes**: ~75,107 file bytes + 1 hung API call (pre-P0) → 22,487 API bytes fresh / **778 warm-cache**.
- **Input-token estimate (bytes/4)**: ~18,776 → ~5,620 fresh, ~195 warm-cache.
- **Reliability**: wedged `/api/orient` (pre-P0) → bounded by per-section hard timeout + failure isolation + `?fresh=true` bypass (P0).

The residual file reads per `MANUAL_FILE_READS` in
`scripts/measure_cold_start.py` are `CLAUDE.md` (loaded automatically
by the Claude harness; not a cold-start cost the harness can skip)
and `docs/WORKSTREAMS.md` (read on demand, not every session).
Onboarding docs now direct all three agents (Claude, Gemini, Codex)
to call the API first and only fall back to direct file reads when
the API server is unreachable.

---
