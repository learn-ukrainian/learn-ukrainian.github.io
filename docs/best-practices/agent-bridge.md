# Agent Bridge — Channel Communication

The agent bridge is how Claude, Gemini, and Codex (and you, the
human) communicate across invocations. The new **channel bridge**
(added in #1190) replaces the old 1:1 `ask-*` pattern with topic-
scoped channels, pinned context, and character-budget history
truncation — the token waste from re-explaining project setup on
every delegation drops from ~15KB to ~6KB per post.

> **Note on the legacy `ask-*` commands.** They still work and are
> the simplest way to fire a one-shot delegation with no history
> tracking. They're **not deprecated** and won't be. Channels are
> the right primitive for sustained, topic-scoped conversations;
> `ask-*` is the right primitive for one-off questions. Use both.

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

`ab discuss` is deliberation, not implementation. The bridge invokes
participants in read-only mode, passes the `AB_DISCUSS_READONLY=1`
contract through the adapter layer, and fails the round if the git
working tree changes while participants are running. A failed round
posts a loud system warning into the thread before returning non-zero.

`ab post` creates channel messages and delivery rows. Its default
delivery mode is read-only, and the inbox worker applies the same
discussion read-only adapter contract to those default deliveries. Use
write-capable modes only when the post is explicitly an execution
request. Implementation work that needs file edits, commits, pushes, or
a PR should normally go through `delegate.py dispatch` or
`ab dispatch-fix`, not through discussion.

Current adapter policy for discussion calls:

- Codex: `read-only` maps to `codex exec -s read-only`.
- Gemini: discussion calls add `--approval-mode plan`; plain read-only
  CLI defaults were not enough in trusted workspaces.
- Claude: discussion calls add `--permission-mode plan` and restrict
  built-in tools to read/list/search tools.

## CLI quick reference

```bash
# Channel management
ab channel new pipeline --include shared --agents claude,gemini,codex
ab channel list
ab channel info pipeline
ab channel context pipeline --edit     # opens $EDITOR on context.md
ab channel tail pipeline -n 20         # last 20 messages
ab channel tail pipeline --thread ABC  # full thread

# Posting (short + long form)
ab p pipeline gemini "quick question about X"
ab post pipeline "full form with --to options" --to gemini,codex
ab post pipeline "reply" --parent MESSAGE_ID

# Multi-agent discussion (B.4)
ab discuss architecture "should we refactor X?" --with claude,gemini,codex --max-rounds 2
```

## Dispatch wrappers

Use these wrappers when the task needs the project-standard model/mode
assignment enforced by tooling instead of memory.

`ab dispatch-fix <issue-or-task-id> [--brief-file PATH]` dispatches a
Codex worktree implementation run for "fix this and ship a PR" tasks.
It hardcodes `delegate.py dispatch --agent codex --mode danger
--worktree --base origin/main --effort high`, and every generated
brief includes the commit, push, and PR checklist. If `--brief-file`
is omitted, the wrapper builds `/tmp/dispatch-fix-<task-id>.md` from
`gh issue view <issue> --json title,body`.

`ab review-deep <PR-or-path> [--effort xhigh]` dispatches an
adversarial Claude review run. It hardcodes `--agent claude --mode
read-only --model claude-opus-4-7 --effort xhigh` unless an explicit
effort override is passed, then builds a review prompt from either
`gh pr view` plus `gh pr diff` or the target file/directory contents.
Use it for blocking logic/security/test review, not for stylistic
preferences.

Both wrappers support `--dry-run`, which writes the prompt and a
`batch_state/tasks/<task-id>.json` preview without launching the
delegate worker.

## Silence-timeout vs hard-timeout

`delegate.py dispatch` has two watchdogs with different jobs.
`--hard-timeout` is the absolute wall-clock fallback for the worker.
`--silence-timeout` is narrower: it kills the agent CLI when no stdout
line arrives within the configured window, then marks the task
`status="timeout"`.

The default silence timeout is 1800 seconds. This is intentionally
longer than the old 600-second watchdog because substantive Codex
dispatches can be quiet for more than 10 minutes during thinking
phases, multi-file refactors, or long test runs. The #1725
`1725-verbatim-quoting` dispatch was killed after 12 minutes of stdout
silence with most work already complete and the last phase still
salvageable; that is the failure mode this default avoids.

Use `--silence-timeout 600` when you want the tighter 10-minute
operator watchdog. OAuth or CLI hangs should still show up within
minutes, while the hard timeout remains the final wall-clock cap.
Use `--silence-timeout 0` only when stdout silence is expected and the
hard timeout alone is acceptable.

## When to use channels vs `ask-*`

| Situation | Use |
| --- | --- |
| One-off question, no history needed | `ask-claude/gemini/codex` |
| Sustained discussion on a topic | `ab post` to a channel |
| Need a 2-3 agent debate on a design | `ab discuss` |
| Sharing context across many delegations | Pin it in `docs/agent-channels/{topic}/context.md` |
| Code review with adversarial feedback | `ab post reviews ...` |
| Want the post visible in the dashboard | Channels only (the legacy `messages` table has its own UI) |

## The hygiene rule

**Nothing commits or merges without adversarial review from another
agent.** Per channel conventions:

1. Write code → stage with `git add`
2. `git diff --cached > /tmp/diff.txt`
3. `ab post reviews "Review request for #NNN" --to gemini` (or ask-gemini with the diff attached)
4. Apply feedback or argue back in writing
5. Commit only after the review is CLEAN or BLOCKING is resolved
6. Commit message includes `Reviewed-By: gemini-3.1-pro-preview (task-id)` trailer

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
`ab discuss` round 2+. When an agent is handed their own prior
response via `_channels.build_agent_prompt` it doesn't need to be
re-typed. The B.2 prompt assembler caps history at 5KB (configurable
via `DEFAULT_MAX_HISTORY_CHARS`), so even a 4-round, 4-agent
discussion stays inside a ~12KB budget per call instead of exploding
to 40–60KB of copy-pasted transcript.

**Tradeoff:** the first round of any new channel pays a small
one-time cost — the pinned `context.md` + the Monitor API snapshot
are concatenated into the prompt even if the agent doesn't strictly
need them. For drive-by one-shots, the legacy `ask-*` commands are
still cheaper. Use channels when the conversation will have at
least two turns.

## Web dashboard

`playgrounds/channels.html` — read-only monitor plus post form,
localhost only. Shows:

- All channels with message counts + pending deliveries + last activity
- Per-channel message feed (auto-refresh every 5s)
- Context preview with sha256 short-hash
- Post form for dropping messages in from the browser

Served by `scripts/api/main.py` at `http://localhost:8765`. The
browser POST endpoint is `/api/comms/channels/{name}/post` — user-only,
gated by localhost binding. Agents still post via CLI.

`playgrounds/comms.html` is the legacy operational dashboard for live
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
ab channel context pipeline --edit
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
- `ab sync` if you prefer manual draining instead of OS integration

Recommended mental model:

- The SQLite `deliveries` table is the source of truth
- Wake files are only a nudge to run `ab inbox run <agent>`
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
ab sync claude
ab sync --all
```

That path reads the same `deliveries` queue and drains it on demand.

## See also

- Issue #1190 — the channel bridge spec and implementation history
- `scripts/ai_agent_bridge/_channels.py` — storage primitives
- `scripts/ai_agent_bridge/_channels_cli.py` — CLI commands
- `scripts/api/comms_router.py` — HTTP endpoints
- `docs/MONITOR-API.md` — the Monitor API used for volatile state snapshots
