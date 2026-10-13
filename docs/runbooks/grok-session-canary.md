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
auto_compact_threshold_percent = 85
```

Operator 2026-09-21: keep the product default of 85%. Do not raise it.

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
  --model grok-4.7

.venv/bin/python -m scripts.session_canary.grok_lane status --epic atlas
.venv/bin/python -m scripts.session_canary.grok_lane protocol --epic atlas
```

Artifacts live under gitignored `.claude/<epic>-epic/canary/`.

## Lifecycle

```
START  → start-grok-driver.sh --epic <name> claims stream lease via common supervisor
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

## Native driver safety hooks

`npm run agents:deploy` overlays `agents_extensions/grok/hooks/driver.json`
onto `.grok/hooks/driver.json`, compares that file on subsequent deployment,
and preserves unrelated `.grok` configuration. The two native `PreToolUse`
matcher groups reuse the write-worker guard selection and native tool aliases,
without reviewer restrictions or a Stop hook. The bridge supplies the shared
guards with `tool_name` and `tool_input`, rejects malformed event envelopes and
truncated inputs, rejects missing shell commands and non-object inputs,
and retains the publishing guard's input rewrite.

`start-grok-driver.sh` binds a fresh native session UUID with `--session-id`
and forces `--no-leader`, keeping hook binding in the launcher process tree.
The binding activates guards for every conversation and native subagent in
that launcher process tree, including `/new`, `/resume` and `/fork`; the event
session ID does not select enforcement. The launcher identity must still be
`grok` / `grok-tui`. Interactive launches clear the three driver binding
variables. Native Grok fleet workers/reviewers and acpx Grok discussions/sealed
reviews scrub all inherited `LU_GROK_*` variables through their invocation
plans. Commands resolve the
shared project interpreter and this launcher's tracked guard sources. Native
aliases are anchored so `todo_write` does not trigger file-write guards.

Native driver forwarded arguments (after `--`) are denied by default. The
allowlist, checked against the installed `grok --help`, contains only these
exact, valueless flags:

| Flags | Rationale |
| --- | --- |
| `--debug` | Enables diagnostic logging without selecting a project or session. |
| `--fullscreen`, `--minimal`, `--no-alt-screen` | Changes terminal presentation only. |
| `--disable-web-search`, `--no-subagents` | Removes tool capabilities without changing their execution site. |

Value spellings, positional prompts, subcommands, unknown flags and every
other option are refused with the option name and reason, without echoing values
or positional text into diagnostics. In particular,
`--cwd`, `-w`/`--worktree`, `--worktree-ref`/`--ref`, session/replay options,
agent definitions and leader options cannot redirect a session after its
project passed preflight. Model and effort remain launcher options before the
separator. Interactive forwarding is unchanged.

Native driver usage is `start-grok-driver.sh [OPTIONS] [-- PROVIDER_ARGS ...]`;
there is no positional prompt. The launcher changes to its own checkout before
the final exec (and in dry-run), refusing if it cannot enter that directory.
Invocation from an unrelated directory or a linked worktree therefore keeps
the session in the checkout whose hooks were inspected.

Before deployment or inspection, native drivers refuse these environment
overrides, including explicitly empty values:

| Variables | Context affected |
| --- | --- |
| `GROK_CONFIG`, `GROK_CONFIG_PATH` | Inline or file config overlays. |
| `GROK_HOME`, `GROK_WORKSPACE_ROOT` | Config home or workspace root. |
| `GROK_FOLDER_TRUST`, `GROK_LEADER_SOCKET` | Folder trust or leader selection. |
| `GROK_MANAGED_CONFIG_URL` | Managed config source. |
| `GROK_CLAUDE_HOOKS_ENABLED`, `GROK_CURSOR_HOOKS_ENABLED`, `GROK_CODEX_HOOKS_ENABLED` | Compatibility hook sources. |
| `GROK_CAMPAIGNS`, `GROK_CAMPAIGNS_OVERRIDE` | Remote config patches. |
| `__GROK_HOOKS_MASK___` | Reserved internal hook marker, conservatively refused. |

This refusal keeps ambient overrides from selecting a different hook context
for the running session. Diagnostics name only the variable, never its value;
unset the named variable before retrying. The list was checked against the
installed client's help, embedded configuration documentation and hook symbols. Interactive
launches retain their environment behavior.

Before launching a native driver, the launcher deploys agent extensions,
refuses a failed deployment, then requires `projectRoot` from
`grok inspect --json` to be an absolute path resolving to the launcher's source
checkout, `projectTrusted: true`, both discovered `pre_tool_use` matchers from the
project profile, and byte equality between the deployed profile and its source.
It refuses launch with the missing condition and remedy; it never grants
folder trust. Deployment refuses symlinked `.grok` or `.grok/hooks` targets.
A missing executable project interpreter or any driver bridge exception denies
with exit 2. Shell inputs require a command and all guarded inputs require an
object; tool `workdir` takes precedence over the session `cwd`.

Worker and reviewer profiles retain their existing behavior except for two
explicit bridge changes: truncated inputs now deny, and native envelopes with
only `hookEventName` are accepted alongside the legacy event-name field.

Discovery can be verified with `grok inspect --json` in an isolated deployed
checkout. Residual: live firing in a real launcher-bound driver session has
not yet been observed. The accountable driver owns that observation before
claiming runtime certification; stop if the installed client cannot execute
project hooks, and do not patch the client.
Residual: native `apply_patch` and `features.write_file` are not covered by
the current matcher groups; the accountable driver owns that coverage gap.

## Related

- `scripts/session_canary/diary.py` — stamp / handback / hydrate capsule helpers
- `docs/runbooks/epic-stream-handoff.md` — cross-agent stream claim
- `scripts/context_canary.py` — shared mint/score engine
- `docs/best-practices/codex-thread-handoff.md` — strict rollover canary
- `start-grok-driver.sh --epic <name>` — core injects the lane protocol pointer
