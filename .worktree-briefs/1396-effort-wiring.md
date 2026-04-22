# Brief: wire `--effort` through delegate.py + Claude/Codex adapters (#1396)

**Task ID:** `claude-1396-effort-wiring`
**Worktree:** `.worktrees/claude-1396-effort-wiring`
**Branch:** `claude-1396-effort-wiring`
**Mode:** `--mode danger` (worktree-isolated, commits + push allowed)
**Issue:** https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1396

## Context

`scripts/delegate.py dispatch` has no `--effort` flag. Headless Claude dispatches run at the CLI default (currently `high` per 1.117). MEMORY says Opus 4.7 at `high` underperforms — use `xhigh` for content/review work. Wiring this lets us dispatch at the correct effort level.

**Codex reviewed the plan (msg #416 on bridge, also in comment on #1396) and approved with three required changes** — implement against the revised AC set below, NOT the original. All ACs are restated here so you don't need to re-read the issue.

## Worktree setup (mandatory — `.claude/rules/delegate-must-use-worktree.md`)

```bash
git worktree add -b claude-1396-effort-wiring .worktrees/claude-1396-effort-wiring
cd .worktrees/claude-1396-effort-wiring
```

Do NOT branch in the main checkout.

## Revised ACs (Codex-approved)

### AC1 — `delegate.py dispatch --effort <level>`

Add optional `--effort` to the dispatch subparser. Choices: `low | medium | high | xhigh | max`. Default: `None`.

### AC2 — First-class `effort` kwarg (NOT tool_config)

Thread `effort: str | None` as a **first-class kwarg** through:
- `delegate.py` dispatch → `_run_worker`
- `scripts/agent_runtime/runner.py:invoke()` signature
- BOTH `build_invocation(...)` call sites in runner.py (currently line 540 and line 874)
- `scripts/agent_runtime/adapters/base.py:AgentAdapter.build_invocation` protocol signature

Update the base.py docstring to document `effort` as cross-agent invocation semantics, peer of `model`. DO NOT stuff it into `tool_config` dict — `tool_config` is adapter-specific/MCP-ish and `effort` is not adapter-specific.

### AC3 — ClaudeAdapter with version gate

In `scripts/agent_runtime/adapters/claude.py:ClaudeAdapter.build_invocation`:

1. Accept `effort` kwarg
2. When `effort` is non-None, check the `cmd_prefix` supports `--effort` via a new function in `scripts/utils/claude_version.py`
3. If supported: append `--effort <level>` to cmd (near existing `--model` append at line 142–143)
4. If NOT supported: log a warning via module-level `logging` (not stderr print), proceed without the flag. **Do not hard-fail.**

Add to `scripts/utils/claude_version.py`:
```python
def supports_effort(cmd_prefix: Sequence[str] | str) -> bool:
    """Return True iff Claude Code at cmd_prefix supports --effort.

    --effort was available in Claude Code 2.1.98+ (verified against
    2.1.117 --help output on 2026-04-22). Gates on same min version
    as the exclude-dynamic-system-prompt-sections feature for
    simplicity; if this turns out to be wrong, split the constant.
    """
    # Reuse the probing machinery; same min version.
    return supports_exclude_dynamic_system_prompt_sections(cmd_prefix)
```

If you prefer a cleaner factoring (separate `_MIN_EFFORT_VERSION` constant + factor the probe logic into a generic `_supports_feature(min_version, prefix)` helper), that's an acceptable nice-to-have. Keep the existing function signature stable for back-compat.

### AC4 — CodexAdapter per-invocation override

In `scripts/agent_runtime/adapters/codex.py:CodexAdapter.build_invocation`:
1. Accept `effort` kwarg
2. When non-None, append `-c model_reasoning_effort=<level>` to the cmd list (matches existing per-invocation `-c` handling pattern at `adapters/codex.py:175`)
3. When None, fall through to `~/.codex/config.toml` default (currently `high`)

### AC5 — Unit tests for argv construction + propagation

File: `tests/test_agent_runtime.py` (add; do NOT create a new test file unless the existing one is over 1500 LOC).

Required tests:
1. `delegate.py dispatch --effort xhigh` parses correctly (use argparse `parse_args()` directly, no subprocess)
2. `_run_worker` receives effort and forwards to `runner.invoke()`
3. `runner.invoke(effort="xhigh", ...)` forwards to `adapter.build_invocation(effort="xhigh", ...)`
4. `ClaudeAdapter.build_invocation(effort="xhigh", ...)` with mocked `supports_effort` returning True → emits `--effort xhigh` in `plan.cmd`
5. `ClaudeAdapter.build_invocation(effort="xhigh", ...)` with mocked `supports_effort` returning False → does NOT emit the flag, logs a warning
6. `CodexAdapter.build_invocation(effort="xhigh", ...)` → emits `-c model_reasoning_effort=xhigh` in `plan.cmd`
7. `GeminiAdapter.build_invocation(effort="xhigh", ...)` → does NOT crash, logs debug, no flag in cmd

Mock the `supports_effort` version probe so tests don't actually run `claude --version`. Pattern: existing tests already model mocking subprocess calls — follow that shape.

Log inspection of real worker runs is NOT sufficient per Codex review — these unit tests are the primary validation.

### AC6 — `--help` output

`delegate.py dispatch --help` lists `--effort` with:
- accepted values
- note that Codex uses `~/.codex/config.toml` default when omitted (currently `high`)
- note that Claude uses CLI default when omitted (currently `high` for Opus/Sonnet 4.6+ per CC 1.117)
- note that Gemini effort is not yet wired (`gemini-cli` does not expose the flag)

### AC7 — Update `.claude/rules/delegate-must-use-worktree.md`

Add a `--effort xhigh` example to the mandatory dispatch wording:

```
git worktree add -b <task-branch-name> .worktrees/<task-name>
cd .worktrees/<task-name>
# For dispatches that warrant peak Opus 4.7:
#   .venv/bin/python scripts/delegate.py dispatch \
#       --agent claude --effort xhigh --model claude-opus-4-7 ...
```

### AC8 — Persist effort in task-state JSON

In `scripts/delegate.py` `_write_state_atomic` callsites (and any state-building code around `delegate.py:437`), include `effort` in the state dict alongside `model`. This is for debuggability and postmortems — not a hard contract, but Codex flagged it as useful.

### AC9 — GeminiAdapter accepts effort

`scripts/agent_runtime/adapters/gemini.py`:
1. Accept `effort` kwarg in `build_invocation`
2. When non-None, log at DEBUG level: `"gemini effort '{level}' not yet wired through CLI — using adapter default"`. Reference issue #1396 follow-up in the log message.
3. Do NOT crash, do NOT append anything to cmd

### AC10 — File follow-up issue for Gemini

After PR merges (or at the same time), file a follow-up issue titled like "Wire `--effort` for Gemini once gemini-cli exposes the flag" referencing #1396. Link back from #1396 before closing.

## Validation

After all ACs, run:
```bash
.venv/bin/python -m pytest tests/test_agent_runtime.py -x -v 2>&1 | tail -40
```

All new tests pass + no existing tests regress.

Then live smoke (optional, for your confidence):
```bash
.venv/bin/python scripts/delegate.py dispatch \
  --agent claude --task-id smoke-effort-claude \
  --prompt "echo 'hello at xhigh'" --effort xhigh --hard-timeout 60
# Check the worker log contains '--effort xhigh' in the invocation
```

## Adversarial review before merge

```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-codex \
  "Adversarial review of implementation for #1396. Read the diff against main." \
  --task-id issue-1396-impl
```

Address findings or justify-ignore each. Document on #1396.

## Deliverables

1. Commits on branch `claude-1396-effort-wiring`:
   - `feat(delegate): wire --effort through to Claude + Codex adapters (#1396)`
   - `test(agent_runtime): effort-arg argv construction + propagation (#1396)`
   - `docs(rules): delegate brief template example for --effort (#1396)`
2. PR from `claude-1396-effort-wiring` → `main`, titled `feat: --effort wiring for claude/codex dispatch (#1396)`
3. Codex adversarial review results on #1396
4. Follow-up issue filed for Gemini (AC10), link on #1396
5. Close #1396 when PR merges and all ACs green

## What NOT to do

- Do NOT put `effort` in `tool_config` dict — first-class kwarg only (Codex requirement)
- Do NOT hard-fail when Claude version doesn't support `--effort` — warn + proceed (Codex requirement)
- Do NOT ship without unit tests for argv propagation (Codex requirement — stronger than original AC5)
- Do NOT modify `ai_agent_bridge` — separate surface, out of scope
- Do NOT change Codex config.toml default or mutate global Claude settings
- Do NOT branch in the main checkout

## Files you'll touch

- `scripts/delegate.py`
- `scripts/agent_runtime/runner.py`
- `scripts/agent_runtime/adapters/base.py`
- `scripts/agent_runtime/adapters/claude.py`
- `scripts/agent_runtime/adapters/codex.py`
- `scripts/agent_runtime/adapters/gemini.py`
- `scripts/utils/claude_version.py`
- `tests/test_agent_runtime.py`
- `.claude/rules/delegate-must-use-worktree.md`

## Time estimate

45–90 min. If you're past 90 min and still iterating on AC5 tests, post progress on #1396 and ask for guidance.
