# Grok session canary + diary dual-write policy

## Problem

Grok auto-compacts at **85%** of the model context window by default (~**400k** tokens on large Grok coding windows). Compact is **lossy for working memory**. Disk session logs and stream dual-writes survive; the model’s live context is summarized.

Ending a session *only because compact fired* is too early if recall is still sharp. Ending *only after* compact when dual-write is stale is too late. **Measured rot** is the end signal.

## Policy

| Signal | Meaning |
| --- | --- |
| Auto-compact | **Re-score** canary; keep driving only if PASS |
| Canary **&lt; 8/10** (`pass-ratio` 0.8) | **FAIL-HANDOFF** → auto **STATE AT HANDBACK** on diary + stream note → close stream → `/quit` |
| Compact count / “compactions remaining” | **Not** an end criterion |
| First compact | **Not** required before you may end; **not** a reason to delay a clean end |

Production **thread rollover** still uses strict **10/10** via `scripts/context_canary.py mint --snapshot` (separate protocol).

## Handoff = DIARY (required)

The dual-write board under `.claude/<epic>-epic/*-DRIVER-HANDOFF.md` is a **diary**, not a one-shot close note.

| When | Action |
| --- | --- |
| After each batch (merge, issue close, dispatch, advisor, block) | `stamp` |
| After canary score PASS | auto stamp with `canary PASS … @ ~N tok` |
| After canary FAIL or clean close | `handback` / auto FAIL template |
| Cold-start | **Read diary + stream first**, then `mint` |

### Mintable sections (keep short)

Canary mint pulls bullets from headings matching **Next Drive** / **Hands-off** (see `scripts/session_canary/grok_lane.py`). Prefer:

```markdown
## Next Drive
1. Concrete next action
2. Another action

## Hands-off
- Foreign lanes
- Primary checkout product writes
```

### No secrets

Never put API keys, private teacher PII, or private-repo secrets in the diary.

### CLI

```bash
# Mid-batch diary stamp + refresh Next Drive
.venv/bin/python -m scripts.session_canary.grok_lane stamp --epic harness \
  --title "merged continuity PRs" \
  --bullet "#5532 MERGED" --bullet "#5533 MERGED" \
  --next "Dispatch Terra B1" --next "Start Grok PR-C"

# Clean close while canary still PASS
.venv/bin/python -m scripts.session_canary.grok_lane handback --epic harness \
  --reason "clean end" \
  --canary-line "canary PASS 10/10 @ ~200k tok" \
  --next "Resume Wave 1 B1" \
  --pin "Sol SHIP memo binding" \
  --open-pr "none"

# FAIL-HANDOFF is automatic on score rc 2; optional overrides:
.venv/bin/python -m scripts.session_canary.grok_lane score \
  --epic harness --answers .claude/harness-epic/canary/answers.json \
  --context-tokens 250000 \
  --next-drive "Load STATE AT HANDBACK; mint; resume B1" \
  --open-prs "PR #N still open"
```

Implementation: `scripts/session_canary/diary.py`.

## Operator config (recommended)

In `~/.grok/config.toml`:

```toml
[session]
auto_compact_threshold_percent = 95
```

Default `85` leaves little runway for a deliberate close after the banner.

## CLI (canary)

```bash
# Cold-start (after stream open + diary load)
.venv/bin/python -m scripts.session_canary.grok_lane mint --epic atlas --stream epic:4387
.venv/bin/python -m scripts.session_canary.grok_lane questions --epic atlas

# Mid-session / post-compact (answers FROM MEMORY — do not re-open probe.json)
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
START  → open stream lease → load diary + stream → mint canary
DRIVE  → stamp diary after each batch
         at ~60–70% context OR after auto-compact → score from memory
         PASS → diary canary line; continue
         FAIL → STATE AT HANDBACK + close stream + quit
END    → handback while PASS (optional) before forced compact
```

## SSOT

| Store | Role |
| --- | --- |
| Session stream (`epic:N`) | Primary typed continuity |
| INTERIM / CLAUDE / CODEX driver handoff | Dual-write **diary** board |
| Canary probe | Rot measurement only (not the board) |

## Related

- `scripts/session_canary/diary.py` — stamp / handback helpers
- `docs/runbooks/epic-stream-handoff.md` — cross-agent stream claim
- `scripts/context_canary.py` — shared mint/score engine
- `docs/best-practices/codex-thread-handoff.md` — strict rollover canary
- `start-grok.sh --epic <name>` — cold-start injects lane protocol pointer
