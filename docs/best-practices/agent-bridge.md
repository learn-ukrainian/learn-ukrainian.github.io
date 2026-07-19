# Agent Bridge — Channel Communication

> **Fleet roles:** operator doctrine and living scorecard live in
> [`fleet-shared-doctrine.md`](fleet-shared-doctrine.md) and
> [`fleet-role-scorecard.md`](fleet-role-scorecard.md). Machine routing remains
> `agents_extensions/shared/rules/model-assignment.md` (takes precedence on conflict).

The agent bridge is how Claude, AGY, and Codex (and you, the
human) communicate across invocations. The new **channel bridge**
(added in #1190) replaces the old 1:1 `ask-*` pattern with topic-
scoped channels, pinned context, and character-budget history
truncation — the token waste from re-explaining project setup on
every delegation drops from ~15KB to ~6KB per post.

> **Current tooling note.** Use `.venv/bin/python
> scripts/ai_agent_bridge/__main__.py ...` for bridge commands. Do not use
> bare `ab ...` examples; `ab` resolves to ApacheBench on the user's machine.
> Gemini CLI and Gemini Code Assist are unsupported. Use AGY for
> Gemini-family work.

## Mental model

A **channel** is a topic — `pipeline`, `content`, `architecture`,
`reviews`, `shared`. Each channel has:

- A **pinned context** file at `docs/agent-channels/{channel}/context.md`
  that holds stable project state (rules, conventions, file paths).
  Auto-prepended to every post.
- A **message history** in SQLite (`channel_messages` table). Replies
  link to parents via `parent_id`; all messages in a thread share a
  `thread_id`.
- An **include chain** — channel A can include channel B, so posts
  to A also carry B's pinned context. The `shared` channel is
  typically included by everything.
- A **subscribers** list — the default recipients for broadcast posts.

A **post** is a message from one agent to zero or more others. It
captures, at post-time:

- The sha256 of every context.md file seen
- A snapshot of the Monitor API project state (`/api/state/summary`)
- The assembled prompt with history truncated to a character budget
- A delivery row per recipient (separate from the message — delivery
  is an outbound state machine, replies are new messages with parent_id)

A **reply** is just a new post with `parent_id` set. Replies inherit
the thread_id and get `round_index = parent.round_index + 1`.

## Discussion vs execution

`.venv/bin/python scripts/ai_agent_bridge/__main__.py discuss` is
deliberation, not implementation. The bridge invokes
participants in read-only mode, passes the `AB_DISCUSS_READONLY=1`
contract through the adapter layer, and fails the round if the git
working tree changes while participants are running. A failed round
posts a loud system warning into the thread before returning non-zero,
including `READ_ONLY_VIOLATION: <agent>` for the agent family that must
be treated as the write source. Filesystem writes during discussion are
a hard stop; dispatch the work as a separate `scripts/delegate.py dispatch`
brief.

`.venv/bin/python scripts/ai_agent_bridge/__main__.py post` creates channel
messages and delivery rows. Its default
delivery mode is read-only, and the inbox worker applies the same
discussion read-only adapter contract to those default deliveries. Use
write-capable modes only when the post is explicitly an execution
request. Implementation work that needs file edits, commits, pushes, or
a PR should normally go through `scripts/delegate.py dispatch` or
`.venv/bin/python scripts/ai_agent_bridge/__main__.py dispatch-fix`, not
through discussion.

Current adapter policy for discussion calls:

- Codex: `read-only` maps to `codex exec -s read-only`.
- AGY: discussion calls route through the AGY adapter. Direct `agy --model`
  uses display labels such as `Gemini 3.1 Pro (High)`; bridge/runtime calls
  may pass slugs such as `gemini-3.1-pro-high` for adapter mapping.
- Claude: discussion calls restrict built-in tools to read/list/search
  tools. They do not use Claude plan mode because discussion replies are
  comments, not implementation plans; the restricted tool list plus the
  bridge's git mutation guard enforce the read-only contract.
- Post-round guard: if the working tree differs after a round, the
  bridge posts a `⚠️ READ-ONLY DISCUSSION VIOLATION` system message and
  returns non-zero without accepting that round's agent replies.

## CLI quick reference

```bash
# Channel management
.venv/bin/python scripts/ai_agent_bridge/__main__.py channel new pipeline --include shared --agents claude,agy,codex
.venv/bin/python scripts/ai_agent_bridge/__main__.py channel list
.venv/bin/python scripts/ai_agent_bridge/__main__.py channel info pipeline
.venv/bin/python scripts/ai_agent_bridge/__main__.py channel context pipeline --edit
.venv/bin/python scripts/ai_agent_bridge/__main__.py channel tail pipeline -n 20
.venv/bin/python scripts/ai_agent_bridge/__main__.py channel tail pipeline --thread ABC

# Posting (short + long form)
.venv/bin/python scripts/ai_agent_bridge/__main__.py p pipeline agy "quick question about X"
.venv/bin/python scripts/ai_agent_bridge/__main__.py post pipeline "full form with --to options" --to agy,codex
.venv/bin/python scripts/ai_agent_bridge/__main__.py post pipeline "reply" --parent MESSAGE_ID

# Multi-agent discussion (B.4)
.venv/bin/python scripts/ai_agent_bridge/__main__.py discuss architecture "should we refactor X?" --with claude,agy,codex --max-rounds 2
```

## Desktop Participation

Desktop participation is currently an MVP flat-string identity, not the
full Multi-UI identity model. The bridge accepts `codex-desktop` and
`claude-desktop` as post authors and delivery targets, but it does not
spawn them as subprocesses. Their registry entries have
`cli_available=False`, so Desktop participation is human-invoked from
the Desktop session.

Orchestrator dispatch to Codex Desktop:

```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py post desktop-tasks "<brief>" --to codex-desktop --from-agent claude
```

Codex Desktop watches the task channel from its own session:

```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py channel tail desktop-tasks --follow
```

Codex Desktop can also pull its pending inbox:

```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py inbox show codex-desktop
```

### Explicit ack: `.venv/bin/python scripts/ai_agent_bridge/__main__.py inbox ack <delivery_id>`

When an external worker processes a delivery without going through
`.venv/bin/python scripts/ai_agent_bridge/__main__.py inbox run`, ack it explicitly:

```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py inbox ack <delivery_id> [--error "processed by <thing>"]
```

Without an explicit ack, deliveries stay `pending` forever and the inbox
warning recurs. Bridge discussion acks its own deliveries on round convergence
automatically, so no manual intervention is needed for that path.

Codex Desktop posts replies with its own sender identity:

```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py post desktop-tasks "<status>" --from-agent codex-desktop
```

Limitation: this MVP stores a flat sender/recipient string. The pending
Multi-UI ADR remains the future design for 4-tuple identity
(`agent_family`, `ui_surface`, `client_id`, `instance_id`), claims,
SSE replay, and attachments.

## Dispatch wrappers

Use these wrappers when the task needs the project-standard model/mode
assignment enforced by tooling instead of memory.

`.venv/bin/python scripts/ai_agent_bridge/__main__.py dispatch-fix <issue-or-task-id> [--brief-file PATH]` dispatches a
Codex worktree implementation run for "fix this and ship a PR" tasks.
It hardcodes `scripts/delegate.py dispatch --agent codex --mode danger
--worktree --base origin/main --effort high`, and every generated
brief includes the commit, push, and PR checklist. If `--brief-file`
is omitted, the wrapper builds `/tmp/dispatch-fix-<task-id>.md` from
`gh issue view <issue> --json title,body`.

`.venv/bin/python scripts/ai_agent_bridge/__main__.py review-pr <PR> [--reviewer auto|codex|glm|claude]`
is the **canonical formal PR review entry** (Sol fleet-comms Phase 0–3):

- **Pointer-only** prompt (PR URL + checklist + mandatory read-only contract).
- Hard size caps — refuse fat pasted diffs/inventory YAML.
- Default `--reviewer auto` → **Codex sealed `--review --pr`** (#5285 isolation).
- Claude dark + local: `--reviewer glm` or `--reviewer auto --no-claude-available`
  (GLM-5.2 is **LOCAL-ONLY** / China egress — never CI).
- Do **not** identify the reviewer as “Hermes”; record model + family + harness.

Formal reviews stay thin in both directions (Phase 4–5). Do not paste a review
body over 4 KiB or attach evidence over 64 KiB to an `ask-*` review job; the
bridge rejects it and points to `review-pr <N>`. Prefer a PR target over a
manual review ask.

**Phase 5 fail-closed (#5486):** if an `ask-* --review` payload looks like a
**formal CF PR review** (GitHub PR URL / `PR #N` / cross-family formal wording)
and has **no** sealed `review_pr` / `review_branch` target, the bridge **refuses**
with `formal_pr_review_requires_review_pr`. Use `review-pr <N>` then
`publish-review-verdict`. Curriculum content reviews that use `--review` without
a PR URL still work. Emergency escape only:
`BRIDGE_ALLOW_LEGACY_REVIEW_ASK=1`.

**Phase 4 residual (#5485):** migrate runbooks and dispatch briefs that still say
`ask-agy --review` / `ask-codex --review` for PR gates to `review-pr` +
`publish-review-verdict`. `scripts/audit/llm_reviewer_dispatch.py` content-review
routes remain `ask-* --review` (module QG, not PR CF).

After a reviewer writes a short verdict or findings JSON, publish exactly one
PR comment without relaying the full body through the orchestrator:

```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py publish-review-verdict \
  --pr 5458 --verdict-file /tmp/review-verdict.txt \
  --model gpt-5.6-terra --family openai --harness codex
```

The comment contains only `VERDICT`, the PR head SHA, and reviewer provenance.
The command prints a ≤2 KiB status summary; use `--findings-json` for a JSON
file with a top-level `verdict`, and `--dry-run` to verify the payload locally.

`.venv/bin/python scripts/ai_agent_bridge/__main__.py review-deep <PR-or-path> [--effort xhigh]` dispatches an
adversarial Claude review run. It hardcodes `--agent claude --mode
read-only --model claude-opus-4-7 --effort xhigh` unless an explicit
effort override is passed, then builds a review prompt from either
`gh pr view` plus `gh pr diff` or the target file/directory contents.
Use it for blocking logic/security/test review, not for stylistic
preferences. Prefer `review-pr` for ordinary formal CF review.

### Worktree cleanup (post-merge painpoint)

After a PR merges, do **not** leave dispatch worktrees forever:

```bash
# Safe default (dry-run):
.venv/bin/python scripts/orchestration/reap_worktrees.py

# Recommended post-merge cleanup (MERGED/CLOSED + dirty auto preserve-then-reap):
.venv/bin/python scripts/orchestration/reap_worktrees.py --apply --merged
```

`--merged` enables `--safe-only`, auto preserve-then-reap for dirty MERGED/CLOSED
trees, and branch prune. Open PRs are never reaped just because HEAD matches
`origin/<branch>`.

### Hermes / DeepSeek isolation (Sol #213 class)

`ask-hermes` is tool-capable. It **must not** inherit the operator primary
checkout as `cwd`. Review-class asks always:

1. run under a **neutral temp scratch** (or sealed snapshot for Codex path);
2. prepend the **READ-ONLY REVIEW CONTRACT**;
3. enforce content/attachment size caps.

Escape hatch `BRIDGE_ALLOW_PRIMARY_HERMES=1` is **non-review only** and
logged. A red-team test proves a hostile hermes that only attacks `cwd`
cannot change primary `HEAD`/`status`.

Both wrappers support `--dry-run`, which writes the prompt and a
`batch_state/tasks/<task-id>.json` preview without launching the
delegate worker.

## Silence-timeout vs hard-timeout

`scripts/delegate.py dispatch` has two watchdogs with different jobs.
`--hard-timeout` is the absolute wall-clock fallback for the worker.
`--silence-timeout` is narrower: it kills the agent CLI when no watchdog
activity arrives within the configured window, then marks the task
`status="timeout"`.

Watchdog activity includes stdout/stderr lines, liveness-file mtime
updates, and process-tree CPU/disk activity. This keeps quiet but active
build/test/enrich subprocess phases alive while still killing fully idle
poll-loop hangs before the hard timeout.

The default silence timeout is 3600 seconds. Do not lower it merely
because wrapper stdout is expected to be quiet; that recreates the
stdout-only false-kill shape from #3875. Use a shorter value only for a
known protocol where all legitimate work emits frequent watchdog
activity.

Use `--silence-timeout 0` only when the hard timeout alone is acceptable
and you have another way to detect parked sessions.

## When to use channels vs `ask-*`

| Situation | Use |
| --- | --- |
| One-off question, no history needed | `.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-agy ...` / `ask-claude` / `ask-codex` |
| Sustained discussion on a topic | `.venv/bin/python scripts/ai_agent_bridge/__main__.py post` to a channel |
| Need a 2-3 agent debate on a design | `.venv/bin/python scripts/ai_agent_bridge/__main__.py discuss` |
| Sharing context across many delegations | Pin it in `docs/agent-channels/{topic}/context.md` |
| Formal PR review (CF gate) | `.venv/bin/python scripts/ai_agent_bridge/__main__.py review-pr <N>` |
| Code review discussion (non-gate) | `.venv/bin/python scripts/ai_agent_bridge/__main__.py post reviews ...` |
| Want the post visible in the dashboard | Channels only (the legacy `messages` table has its own UI) |

## The hygiene rule

**Nothing commits or merges without adversarial review from another
agent.** Per channel conventions:

1. Write code → stage with `git add`
2. `git diff --cached > /tmp/diff.txt`
3. `.venv/bin/python scripts/ai_agent_bridge/__main__.py post reviews "Review request for #NNN" --to agy`
4. Apply feedback or argue back in writing
5. Commit only after the review is CLEAN or BLOCKING is resolved
6. Commit message includes `Reviewed-By: AGY Gemini 3.1 Pro (High) (task-id)` trailer

This rule is non-negotiable. Bypassing it was the #1 reason review
quality degraded on earlier commits.

## Spawned-agent env hygiene

The agent runtime does not pass the orchestrator's full `os.environ` to
spawned CLIs. `scripts/agent_runtime/env_sanitize.py` builds a narrow
environment for each process:

- Common runtime variables survive only from the safe allowlist:
  `PATH`, `HOME`, `TMPDIR`, `LANG`, `USER`, `LOGNAME`, `LC_*`,
  `AB_*`, and `LU_*`. `USER` and `LOGNAME` are identity variables, not
  secrets, and are intentionally allowed for subprocesses that need the
  local account context.
- Variables with secret-shaped names are dropped, including names that
  contain `TOKEN`, `SECRET`, `PASSWORD`, `PASSWD`, `PRIVATE`,
  `CREDENTIAL`, `API_KEY`, `ACCESS_KEY`, `AUTH`, or `COOKIE`.
- Variables with known secret-shaped values are dropped, including
  GitHub, OpenAI-style `sk-`, Slack `xox-`, Hugging Face `hf_`, npm,
  AWS access-key, and Google `AIza` patterns.
- Provider credentials pass through only to that provider: Gemini sees
  Gemini/Google keys, Claude sees Anthropic/Claude keys, and Codex sees
  OpenAI/Codex keys. Cross-provider keys stay absent. `GITHUB_TOKEN`
  is never passed through directly; `delegate.py` resolves it once from
  the environment or `~/.bash_secrets` and exposes it as `GH_TOKEN` only
  for Codex, Claude, and bridge subprocesses so authenticated `gh`
  commands work without sourcing shell secrets. Gemini subprocesses do
  not receive `GH_TOKEN`.
- Gemini also receives `GEMINI_AUTH_MODE` because it is runtime mode
  selection, not a credential; secret-shaped values are still rejected.

For #1754, Claude Pro/Max OAuth on macOS has one extra gotcha: the
Claude CLI reads OAuth tokens from the macOS keychain, and the keychain
lookup depends on the local user identity. A stripped environment like
`env -i HOME=$HOME PATH=$PATH claude -p "say PONG"` can report `Not
logged in`, while adding `USER=$USER` lets the same CLI find the
keychain entry. `LOGNAME` is allowed as defense in depth for libraries
that prefer it. This does not replace the provider-specific token
allowlist; `ANTHROPIC_API_KEY` and `CLAUDE_API_KEY` still pass only to
Claude for API-key users.

Adapters should put per-call environment values in
`InvocationPlan.env_overrides`; the runner applies overrides, sanitizes,
then applies explicit `InvocationPlan.env_unsets`. The merge guard runs
after sanitization so its `gh`/`git` shims still receive the final `PATH`
and can stamp `AGENT_NO_MERGE`, `AGENT_REAL_GH`, and `AGENT_REAL_GIT`.

## Context file conventions

`docs/agent-channels/{channel}/context.md` should contain:

- **Stable** project knowledge: conventions, file layouts, non-negotiables
- **Reference** data that doesn't change per-commit: auth rules, API surfaces
- **Clarifying** context the agents need but you don't want to re-type

It should NOT contain:

- **Volatile** state (current sprint, recent commits) — that comes from
  the Monitor API snapshot automatically
- **Secrets** — context.md is git-tracked
- **Per-conversation** details — those belong in the post itself

Revisions to `context.md` are tracked via sha256 — every message
stores which revision it saw, so you can replay a conversation
deterministically even if the context drifts later.

## Token savings (measured on the #1190 review trail)

The channel bridge was built over four phases (B.1–B.4) with six
adversarial review rounds handed to Gemini. The review briefs were
written by hand against explicit AC lists — no bulk context paste —
which means the numbers below under-sell the savings for typical
"please review this diff" delegations that normally repeat 10–35KB
of project rules each time.

**Measured brief sizes (chars sent from claude → gemini, excluding
the ~10KB project-rules wrapper the legacy bridge prepends):**

| Review round            | Task ID               | Brief size |
| ----------------------- | --------------------- | ---------: |
| B.3 r1 (initial)        | `bridge-b3-review`    |      6,621 |
| B.3 r2 (3 new blockers) | `bridge-b3-review-r2` |      5,304 |
| B.3 r3 (backslash bug)  | `bridge-b3-review-r3` |      2,683 |
| B.3 r4 (CLEAN)          | `bridge-b3-review-r4` |      2,121 |
| B.4 r1 (4 blockers)     | `bridge-b4-review`    |      4,827 |
| B.4 r2 (MINOR)          | `bridge-b4-review-r2` |      3,915 |
| **Total**               |                       | **25,471** |

Every brief in that table would have been ~12KB larger had I
followed the old convention (manually re-pasting the rules/history
that channels would otherwise pin). Six rounds × ~12KB = **~72KB
of repeated context avoided** on this one issue alone — and the
savings grow roughly linearly with round count.

**Compound wins on multi-round debates:** the same trick applies to
`.venv/bin/python scripts/ai_agent_bridge/__main__.py discuss` round 2+. When an agent is handed their own prior
response via `_channels.build_agent_prompt` it doesn't need to be
re-typed. The B.2 prompt assembler caps history at 5KB (configurable
via `DEFAULT_MAX_HISTORY_CHARS`), so even a 4-round, 4-agent
discussion stays inside a ~12KB budget per call instead of exploding
to 40–60KB of copy-pasted transcript.

**Tradeoff:** the first round of any new channel pays a small
one-time cost — the pinned `context.md` + the Monitor API snapshot
are concatenated into the prompt even if the agent doesn't strictly
need them. For drive-by one-shots, the legacy `ask-*` commands are
still cheaper. `ask-*` commands infer `--from` from wrapper environment
such as `CLAUDE_AGENT_NAME`, `CODEX_SESSION`, or `GEMINI_SESSION`; pass
`--from` explicitly when running them from a plain shell. Use channels
when the conversation will have at least two turns.

## Web dashboard

`dashboards/channels.html` — read-only monitor plus post form,
localhost only. Shows:

- All channels with message counts + pending deliveries + last activity
- Per-channel message feed (auto-refresh every 5s)
- Context preview with sha256 short-hash
- Post form for dropping messages in from the browser

Served by `scripts/api/main.py` at `http://localhost:8765`. The
browser POST endpoint is `/api/comms/channels/{name}/post` — user-only,
gated by localhost binding. Agents still post via CLI.

`dashboards/comms.html` is the legacy operational dashboard for live
activity, DM-style broker messages, zombie detection, and batch progress.
Its hot message endpoints are bounded by server-side `limit` defaults
and keyset cursors; keep client polling paced so heavy views refresh no
more often than every 30 seconds.

## Broker storage hygiene

SQLite remains the broker store for the localhost-only bridge. The
performance bottleneck in the comms dashboard was unindexed scans plus
unbounded result sets, not the engine. Keep the broker in WAL mode so
readers can continue while a writer commits:

```bash
sqlite3 .mcp/servers/message-broker/messages.db 'PRAGMA journal_mode'
```

Expected output is `wal`. Bridge connections also use
`PRAGMA busy_timeout=5000`, `PRAGMA cache_size=-20000` (about 20 MB),
and `PRAGMA temp_store=MEMORY` for local dashboard queries.

Run retention explicitly; the API server must not delete broker history
on startup:

```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py cleanup --older-than 30d --dry-run
.venv/bin/python scripts/ai_agent_bridge/__main__.py cleanup --older-than 30d
```

Recommended schedule: run the dry-run weekly, then run the cleanup if
the counts look reasonable. Cleanup deletes acknowledged legacy
messages and terminal channel deliveries/messages older than the
threshold, then runs `VACUUM` to reclaim disk space.

## API endpoints (for scripts + dashboards)

Read-only:
- `GET /api/comms/channels` — list all channels
- `GET /api/comms/channels/{name}` — channel metadata + context preview
- `GET /api/comms/channels/{name}/messages?tail=N` — recent messages
- `GET /api/comms/channels/{name}/threads/{thread_id}` — full thread
- `GET /api/comms/channels/{name}/deliveries?status=pending` — routing state

Write (user-only, localhost-gated):
- `POST /api/comms/channels/{name}/post` — drop a new post

## When channels drift

If `context.md` for a channel goes stale (the rules no longer match
reality), fix it immediately:

```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py channel context pipeline --edit
```

This bumps the sha256, and the next post will record the new rev.
Older messages still have their original `context_rev_*` values for
deterministic replay — the update doesn't retroactively rewrite
history.

## Wake integration (C.3)

The inbox worker now supports a simple filesystem wake hint at
`.agent/wake/{agent}`. Whenever `_channels.post()` commits delivery
rows for one or more recipients, it replaces each recipient's wake
file atomically. That write is best-effort only: a wake-file failure
does not roll back the message or delivery insert.

Who writes:

- `scripts/ai_agent_bridge/_channels.py` after a successful post commit

Who reads:

- Any external watcher you configure locally
- `.venv/bin/python scripts/ai_agent_bridge/__main__.py sync` if you prefer manual draining instead of OS integration

Recommended mental model:

- The SQLite `deliveries` table is the source of truth
- Wake files are only a nudge to run `.venv/bin/python scripts/ai_agent_bridge/__main__.py inbox run <agent>`
- Missing a wake is safe because the work is still pending in SQLite

Example launchd `.plist` (`docs/examples/learn-ukrainian.codex-inbox.plist`):

> <?xml version="1.0" encoding="UTF-8"?>
> <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
> "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
> <plist version="1.0">
> <dict>
>   <key>Label</key>
>   <string>learn-ukrainian.codex-inbox</string>
>   <key>ProgramArguments</key>
>   <array>
>     <string>/Users/your-user/projects/learn-ukrainian/.venv/bin/python</string>
>     <string>/Users/your-user/projects/learn-ukrainian/scripts/ai_agent_bridge/__main__.py</string>
>     <string>inbox</string>
>     <string>run</string>
>     <string>codex</string>
>     <string>--until-idle</string>
>   </array>
>   <key>WatchPaths</key>
>   <array>
>     <string>/Users/your-user/projects/learn-ukrainian/.agent/wake/codex</string>
>   </array>
> </dict>
> </plist>

Example systemd units (documented only, not tested here):

```ini
# ~/.config/systemd/user/learn-ukrainian-codex-inbox.path
[Path]
PathChanged=%h/projects/learn-ukrainian/.agent/wake/codex

# ~/.config/systemd/user/learn-ukrainian-codex-inbox.service
[Service]
Type=oneshot
WorkingDirectory=%h/projects/learn-ukrainian
ExecStart=%h/projects/learn-ukrainian/.venv/bin/python scripts/ai_agent_bridge/__main__.py inbox run codex --until-idle
```

If you do not want OS-level watchers, use the manual fallback:

```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py sync claude
.venv/bin/python scripts/ai_agent_bridge/__main__.py sync --all
```

That path reads the same `deliveries` queue and drains it on demand.

## See also

- Issue #1190 — the channel bridge spec and implementation history
- `scripts/ai_agent_bridge/_channels.py` — storage primitives
- `scripts/ai_agent_bridge/_channels_cli.py` — CLI commands
- `scripts/api/comms_router.py` — HTTP endpoints
- `docs/MONITOR-API.md` — the Monitor API used for volatile state snapshots
