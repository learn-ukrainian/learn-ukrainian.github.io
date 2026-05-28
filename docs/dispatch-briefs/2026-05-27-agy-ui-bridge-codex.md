# 2026-05-27 — Antigravity UI bridge: `ab send-agy-ui` (Codex)

> Dispatch target: `codex --mode danger --worktree`, model `gpt-5.5` (default), effort `xhigh`.
> Base: `origin/main` (currently `ceae5df9ff`, post PR #2357).
> Tracking: bridge target #2 from Pt 3 handoff direction update; reactivated 2026-05-27 by user.

## Why this exists

We have `ab send-codex-ui --thread <UUID>` (in `scripts/ai_agent_bridge/_ui_codex.py`) that lets us drive the running Codex Desktop UI by injecting prompts into its on-disk thread state via `codex exec resume <UUID> --json -`. This is the high-leverage orchestration primitive: a long-running thread accumulates context across many turns (m20 rounds #4-#12 all ran in one codex thread), the bridge subprocess buffers stdout until `task_complete`, and we get a structured JSON result we can parse.

We need the SAME pattern for Antigravity (`agy` CLI), so we can drive gemini-3.1-pro through the Antigravity UI thread the way we drive codex. The empirical writer comparison for the A1 m20 anchor (per `docs/decisions/2026-05-06-writer-selection-codex-gpt55.md`) requires both codex AND gemini implementations, and we want the SAME quality of orchestration on the gemini side.

User direction 2026-05-27: bio research scale-up is delayed until this ships. With +10K Google credits we don't have a quota constraint on gemini-side empirical runs; the missing piece is the orchestration plumbing.

## What to build

Add a `send-agy-ui` subcommand to the bridge analogous to `send-codex-ui`. Same shape:

```bash
ab send-agy-ui --thread <CONVERSATION-ID> "your message"
ab send-agy-ui --thread <CONVERSATION-ID> --from-file relay.md
ab send-agy-ui --thread <CONVERSATION-ID> --cwd ~/some/worktree --from-file relay.md --timeout 5400 --json
```

Returns a JSON object with `bridge_id`, `thread_id`, `exit_code`, `final_message`, `duration_s`, `session_file`, `event_count`.

## How agy supports this

The `agy` CLI (`/Users/krisztiankoos/.local/bin/agy`) exposes:

```
agy --print "<prompt>"          # -p / --print: one-shot non-interactive prompt
agy --continue                  # -c: continue most recent conversation
agy --conversation <ID>         # resume a previous conversation by ID
agy --dangerously-skip-permissions  # auto-approve tool calls (analogue of codex --mode danger)
agy --print-timeout 5m          # timeout for --print wait
agy --add-dir <PATH>            # add directory to workspace (repeatable)
```

Combining `--conversation <ID>` + `--print "<msg>"` should be the **agy equivalent of `codex exec resume <UUID> --json -`** — it resumes a specific conversation and prints the model's response non-interactively.

Verify this empirically as Step 1 of your work. If `agy --conversation <ID> --print "<msg>"` exists and emits JSON-or-parseable output, the adapter is essentially a mirror of `_ui_codex.py` with the right command flags. If agy doesn't support resume-print combo, fall back to: spawn `agy --conversation <ID>`, feed the prompt on stdin if supported, parse stdout until idle.

## Where to find the analog

Read `scripts/ai_agent_bridge/_ui_codex.py` end-to-end (279 lines). The structure:

1. `find_session_file(thread_id)` — locates the session JSONL on disk under `~/.codex/sessions/YYYY/MM/DD/rollout-<ts>-<uuid>.jsonl`.
2. `_extract_final_message(events)` — walks the JSON event stream and picks the last `agent_message`-type item.
3. `send(thread_id, message, cwd, timeout_s, from_file, prefix_bridge_id)` — the core entry point. Spawns `codex exec resume <UUID> --json -`, feeds the prompt on stdin (prefixed with `Bridge-ID: <id>` for correlation), reads stdout JSON events, parses, returns structured result.
4. `argparse` wiring in `_cli.py` (search for `send-codex-ui` subparser around line 782-820).

Build `scripts/ai_agent_bridge/_ui_agy.py` with the same shape, swapping:

- `codex exec resume <UUID> --json -` → the agy resume invocation you verified in Step 1.
- `~/.codex/sessions/...` → wherever agy stores conversation state. Find this by running `agy --conversation foo --print "hi"` once and observing what files get touched (`find ~ -newer /tmp/marker -type f 2>/dev/null` after a `touch /tmp/marker` snapshot).
- JSON event parser → adapt to whatever agy emits. If agy doesn't emit JSON events natively (it might just print final text), the parser becomes "read until subprocess exits, treat stdout as final_message."
- `_extract_final_message` → trivial if agy is one-shot text output; same shape as codex if agy emits a structured stream.

Wire it into `_cli.py` analogous to lines 782-820 (subparser setup) and 921 (dispatch handler). Match argument names exactly: `--thread`, `--from-file`, `--cwd`, `--timeout`, `--json`. Allow `--thread` to be optional or accept a sentinel for "start new conversation."

## Numbered execution steps

1. `git worktree add ~/projects/.worktrees/dispatch/codex/agy-ui-bridge-2026-05-27 -b codex/agy-ui-bridge-2026-05-27 origin/main` from `/Users/krisztiankoos/projects/learn-ukrainian`. CD into the worktree.
2. **Empirical investigation (Step 1 above).** Run `agy --conversation <FRESH-ID> --print "hello"` (or `agy --print "hello"` then `agy --continue --print "follow up"`) and observe the output stream. Find where conversation state is persisted on disk. Document findings inline in the new `_ui_agy.py` docstring (mirroring the `_ui_codex.py` 2026-05-25 probe section).
3. Read `scripts/ai_agent_bridge/_ui_codex.py` end-to-end. Read `scripts/ai_agent_bridge/_cli.py` lines 780-925 for the `send-codex-ui` wiring.
4. **Build `scripts/ai_agent_bridge/_ui_agy.py`** mirroring `_ui_codex.py` shape: docstring with empirical findings + `find_session_file` + `_extract_final_message` + `send` function + `main` argparse handler. Target size ~250-350 LOC. Keep the public `send(...)` signature identical to `_ui_codex.send(...)` so callers can swap one for the other.
5. **Wire into `_cli.py`**: add a `send-agy-ui` subparser around line 820 (after `send-codex-ui`); add a dispatch branch around line 925 (after `send-codex-ui`).
6. **Tests**: add `tests/ai_agent_bridge/test_ui_agy.py` covering: (a) `find_session_file` happy path + missing-file, (b) `_extract_final_message` with synthetic event stream, (c) `send()` with subprocess mocked to return a known event stream, (d) `send()` timeout behavior. Mirror existing patterns from `tests/ai_agent_bridge/test_ui_codex*.py` if any exist; otherwise model after a sibling adapter test like `tests/test_agent_runtime_adapters_codex.py`.
7. **Lint + tests**: `.venv/bin/ruff check scripts/ai_agent_bridge/_ui_agy.py scripts/ai_agent_bridge/_cli.py tests/ai_agent_bridge/test_ui_agy.py` then `.venv/bin/python -m pytest tests/ai_agent_bridge/ -q --no-header`. Quote raw final lines in the PR body.
8. **Smoke test against a real agy session**: run `ab send-agy-ui --thread <ID> --from-file /tmp/agy-smoke.md --timeout 600 --json`, capture the JSON output, paste in the PR body. (You may need to start a fresh agy conversation first to have a valid ID.)
9. **Commit** with conventional message: `feat(bridge): agy UI relay (ab send-agy-ui) mirroring send-codex-ui`. Include `X-Agent: codex/agy-ui-bridge-2026-05-27` trailer.
10. **Push** via `git push -u origin codex/agy-ui-bridge-2026-05-27` then `gh pr create` with title `feat(bridge): ab send-agy-ui — drive Antigravity UI thread analogous to send-codex-ui`. Body must include: (a) the empirical investigation findings (where agy stores conversation state, what command resumes a conversation), (b) per-test pass summary, (c) smoke-test JSON output. Tag the PR with `bridge` if such a label exists.
11. **DO NOT auto-merge.** Leave for orchestrator review.

## Anti-fabrication contract (#M-4)

Every claim in your PR body MUST be tool-backed:

| Claim | Required evidence |
|---|---|
| "agy supports `--conversation <ID> --print <msg>`" | The `agy --help` output + actual successful invocation showing it works |
| "agy stores conversation state at PATH" | `ls -la PATH/` raw output AFTER creating a conversation |
| "Tests pass" | `pytest tests/ai_agent_bridge/ -q --no-header` final line raw |
| "Lint clean" | `ruff check` final line raw |
| "Smoke test succeeded" | The actual JSON returned by `ab send-agy-ui ...` |

If `agy --conversation <ID> --print <msg>` does NOT work as documented, STOP and surface in the PR body with the actual error output. Do not invent a workaround silently.

## Out of scope

- Do NOT modify the existing `_ui_codex.py` or `send-codex-ui` subcommand.
- Do NOT modify `delegate.py dispatch --agent agy` (that's the dispatch lane, independent of the bridge UI lane).
- Do NOT touch other writers/bridges (claude, cursor, gemini-cli direct).
- Do NOT auto-merge.

## On unexpected blockers

- If `agy --conversation` and `agy --print` cannot be combined: document in PR body, propose alternative (e.g. `agy --conversation <ID>` then stdin feed if supported), implement only if straightforward.
- If agy conversation state is in-process-only (not on-disk): the bridge can still work by orchestrating fresh `agy --print` sessions per call, but acknowledge in the PR that conversation continuity isn't supported and recommend a follow-up.
- If smoke test fails because no fresh agy session can be started: skip step 8, mark as follow-up, ship the code with tests only.
