# Grok session canary + auto-compact policy

## Problem

Grok auto-compacts at **85%** of the model context window by default (~**400k** tokens on large Grok coding windows). Compact is **lossy for working memory**. Disk session logs and stream dual-writes survive; the model’s live context is summarized.

Ending a session *only because compact fired* is too early if recall is still sharp. Ending *only after* compact when dual-write is stale is too late. **Measured rot** is the end signal.

## Policy

| Signal | Meaning |
| --- | --- |
| Auto-compact | **Re-score** canary; keep driving only if PASS |
| Canary **&lt; 8/10** (`pass-ratio` 0.8) | **FAIL-HANDOFF** → dual-write STATE AT HANDBACK, close stream, `/quit` |
| Compact count / “compactions remaining” | **Not** an end criterion |
| First compact | **Not** required before you may end; **not** a reason to delay a clean end |

Production **thread rollover** still uses strict **10/10** via `scripts/context_canary.py mint --snapshot` (separate protocol).

## Operator config (recommended)

In `~/.grok/config.toml`:

```toml
[session]
auto_compact_threshold_percent = 95
```

Default `85` leaves little runway for a deliberate close after the banner.

## CLI

```bash
# Cold-start (after stream open + handoff load)
.venv/bin/python -m scripts.session_canary.grok_lane mint --epic atlas --stream epic:4387
.venv/bin/python -m scripts.session_canary.grok_lane questions --epic atlas

# Mid-session / post-compact (answers FROM MEMORY — do not re-open probe.json)
# Write .claude/atlas-epic/canary/answers.json as {"anchor-id": "your recall", ...}
.venv/bin/python -m scripts.session_canary.grok_lane score \
  --epic atlas \
  --answers .claude/atlas-epic/canary/answers.json \
  --context-tokens 250000 \
  --model grok-4.5

.venv/bin/python -m scripts.session_canary.grok_lane status --epic atlas
.venv/bin/python -m scripts.session_canary.grok_lane protocol --epic atlas
```

Artifacts live under gitignored `.claude/<epic>-epic/canary/`.

## Lifecycle

```
START  → open stream lease → dual-write handoff → mint canary
DRIVE  → dual-write after each batch
         at ~60–70% context OR after auto-compact → score from memory
         FAIL → STATE AT HANDBACK + close stream + quit
END    → optional clean close while canary still PASS (before forced compact if possible)
```

## SSOT

| Store | Role |
| --- | --- |
| Session stream (`epic:N`) | Primary typed continuity |
| INTERIM / CLAUDE driver handoff | Dual-write board |
| Canary probe | Rot measurement only (not the board) |

## Related

- `scripts/context_canary.py` — shared mint/score engine
- `docs/best-practices/codex-thread-handoff.md` — strict rollover canary
- `start-grok.sh --epic <name>` — cold-start injects lane protocol pointer
