# Grok session canary + diary dual-write policy

## Problem

Grok auto-compacts at **85%** of the model context window by default (~**400k** tokens on large Grok coding windows). Compact is **lossy for working memory**. Disk session logs and stream dual-writes survive; the model’s live context is summarized.

Ending a session *only because compact fired* is too early if recall is still sharp. Ending *only after* compact when dual-write is stale is too late. **Measured rot** is the end signal.

## Policy

**Operator is not the recovery driver.** Agents own compact recovery
(score → auto-hydrate on PASS). Do not ask the human whether to restart,
hydrate, or re-load the diary. Restart only when FAIL-HANDOFF ends the seat
(or the operator deliberately starts a new session).

| Signal | Meaning |
| --- | --- |
| Auto-compact | **Re-score** canary → on PASS **auto-hydrate + RE-GROUND** (not blind continue) |
| Canary **PASS** | Durable **anchors** OK only — **not** proof mid-flight working memory survived |
| Canary **&lt; 8/10** (`pass-ratio` 0.8) | **FAIL-HANDOFF** → auto **STATE AT HANDBACK** on diary + stream note → close stream → `/quit` |
| Compact count / “compactions remaining” | **Not** an end criterion |
| First compact | **Not** required before you may end; **not** a reason to delay a clean end |

### Working-set honesty (canary is not full memory)

Promote load-bearing mid-flight facts **before** compact risk (~60–70% context or after each batch):

```bash
.venv/bin/python -m scripts.session_canary.grok_lane stamp --epic <epic> \
  --title "pre-compact promote" \
  --bullet "what just finished" \
  --next "concrete next action" \
  --workset "open blocker / phase receipt path / pilot clone path"
```

Mintable sections: **## Next Drive**, **## Active Working Set**, **## Hands-off**.

After every compact (including when canary still PASSes):

1. Score from memory → auto-hydrate capsule (includes **RE-GROUND CHECKLIST** footer)
2. Re-read Next Drive + Active Working Set
3. Open the active phase receipt named there
4. If open task is missing from dual-write → **STOP inventing** — stamp or hand off

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

Canary mint pulls bullets from headings matching **Next Drive** / **Active Working Set** /
**Hands-off** (see `scripts/session_canary/grok_lane.py`). Prefer:

```markdown
## Next Drive
1. Concrete next action
2. Another action

## Active Working Set
- Load-bearing mid-flight facts (paths, PR numbers, open blockers)

## Hands-off
- Foreign lanes
- Primary checkout product writes
```

### No secrets

Never put API keys, private teacher PII, or private-repo secrets in the diary.

### CLI

```bash
# Post-compact (automatic): score FROM MEMORY — PASS auto-prints hydrate capsule
.venv/bin/python -m scripts.session_canary.grok_lane score \
  --epic harness --answers .claude/harness-epic/canary/answers.json \
  --context-tokens 250000
# Optional: --no-hydrate to skip; --hydrate-write for canary/hydrate.md receipt
# Standalone hydrate only if you need a re-print:
#   .venv/bin/python -m scripts.session_canary.grok_lane hydrate --epic harness

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
START  → start-grok.sh --epic <name> claims stream lease via common supervisor
         → load diary + stream → mint canary
DRIVE  → stamp diary after each batch
         at ~60–70% context OR after auto-compact → score from memory
         PASS → auto-hydrate printed by score; continue (no operator prompt)
         FAIL → STATE AT HANDBACK + close stream + quit
END    → handback while PASS (optional) before forced compact
```

The launcher owns lease open/close for Grok. The cold-start prompt explicitly tells the model not to open or resume the lease itself.

## SSOT

| Store | Role |
| --- | --- |
| Session stream (`epic:N`) | Primary typed continuity |
| INTERIM / CLAUDE / CODEX driver handoff | Dual-write **diary** board |
| Canary probe | Rot measurement only (not the board) |

## Related

- `scripts/session_canary/diary.py` — stamp / handback / hydrate capsule helpers
- `docs/runbooks/epic-stream-handoff.md` — cross-agent stream claim
- `scripts/context_canary.py` — shared mint/score engine
- `docs/best-practices/codex-thread-handoff.md` — strict rollover canary
- `start-grok.sh --epic <name>` — cold-start injects lane protocol pointer
