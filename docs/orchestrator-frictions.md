# Orchestrator frictions — detail + autopsies

Long-form for rules listed terse in `claude_extensions/agents/curriculum-orchestrator.md`. Add new entries here; keep the skill cheatsheet short.

## Routing autopsies

### Why "code edit, any size → codex" matters

The friction: "small inline edits" (1-line bug fixes, 1-line test relaxations) accumulate to large Claude weekly burn. On 2026-05-24 the orchestrator burned multiple turns of Claude quota on:
- A 2-line cursor adapter fix in `scripts/agent_runtime/adapters/cursor.py:97`.
- A 2-line CodeQL suppression-comment placement fix in `scripts/build/linear_pipeline.py:5888`.
- A 1-line test label relaxation in `tests/build/test_writer_pre_emit_checklist.py`.

Each individually was "too small to bother dispatching." Together they consumed more quota than a single codex dispatch would have, AND took multiple turns + multiple verification cycles. Codex with reset compute can handle each in 3-5 min wall, zero Claude burn.

The exception "≤5 LOC fixing CI you just caused" applies ONLY when reverting an immediate self-introduced break — not as a general license for "this one is small."

### Why claude-tools writer is forbidden during quota constraint

V7 module builds with `--writer claude-tools` consume the SAME Claude weekly quota as the orchestrator. During a quota-constraint signal from the user (e.g. "7% left"), claude-tools writer puts the orchestrator + builder in the same lane competing for the same budget. Cursor-tools (composer-2.5) and codex-tools both go to different lanes.

agy = claude-sonnet (per user direction 2026-05-24). agy is NOT a fallback during Claude-constraint — it pulls from the same lane.

## Adapter-bug autopsies

### 2026-05-24 — cursor adapter `-p -` argv bug

Symptom: cursor dispatches classified as `rate_limited` ~168s in, `returncode=0`, `response_chars=0`.

Root cause: `scripts/agent_runtime/adapters/cursor.py:97` (pre-PR-#2258) built argv as `[cursor_bin, "-p", "-", ...]`. cursor-agent's `-p` is a boolean print-mode toggle, NOT a flag that takes an argument. The bare `-` after it is parsed as the POSITIONAL `prompt` argument — value = the single-character string `"-"`. The real 14KB prompt sat unread on stdin while cursor processed `-` as the actual prompt. Output was empty; the empty thinking trace happened to contain tokens matched by `_RATE_LIMIT_RE` (false positive).

Why CI passed it: `tests/agent_runtime/adapters/test_cursor_adapter.py:34` asserted `assert "-" in plan.cmd` — the test enshrined the bug as a feature.

Fix: PR #2258 drops `-` from argv, flips the broken assertion, adds regression test `test_cursor_adapter_no_literal_dash_argument_anywhere` covering all 3 modes.

Lesson encoded: "ADAPTER-BUG FIX DISCIPLINE" rule — fix adapter + FLIP the enshrining test (don't just add a new test next to the wrong one) + autopsy in commit message.

Investigation took 4 user prompts because the orchestrator initially accepted "rate_limited" as canonical. User said "i see no limit problems at composer" — that pushed the orchestrator to verify. Lesson encoded: "VERIFY BEFORE ACCEPTING ADAPTER LABEL" rule.

## Monitoring autopsies

### 2026-05-24 — passive Monitor missed 3 silent-exit dispatches

Setup: 2 gemini dispatches (PR #2256 fixups, Option C gate) + 1 codex dispatch (PR #2256 review) fired with `Monitor` tool tailing `batch_state/tasks/logs/<task>.{stdout,stderr}.log` filtered by keyword grep.

Outcome: All 3 dispatches completed cleanly. None of the keyword filters matched (gemini CLI writes almost nothing to stdout; codex writes nothing visible at clean exit). Monitor was silent. Orchestrator did not notice completion. User had to ask "any update?" to get a status check.

Root cause: `batch_state/tasks/logs/*.{stdout,stderr}.log` capture the dispatch CLI's stdout/stderr, NOT the agent's reasoning/tool stream. The agent writes its real activity to:
- codex → `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` (or scoped `CODEX_HOME/sessions/...`)
- cursor → `~/.cursor/chats/<hash>/`
- gemini → `~/.gemini/history/<task-name>/`

The CLI launcher mostly forwards stdin to the agent and waits for exit. Nothing matches typical "completion" keywords.

Lesson encoded: "ACTIVE WATCH — SAME TURN AS FIRE" rule with explicit signal-source-by-agent table. Plus MEMORY.md #M-8 updated.

## Status-report autopsies

### 2026-05-24 — repeated "I'll do X" without doing X

Pattern: orchestrator sent multi-paragraph status updates restating "the plan" and "what I'll do next" instead of acting. User asked "any update?" twice in a session where the orchestrator had been active.

Lesson encoded: "STATUS REPORTS" rule — ≤5 lines, past + present + next verb, no future-tense plans without immediate action.

## Repeated-attempt autopsies

### 2026-05-23 — m20 prompt-rewrite loop

Pattern: m20 a1/my-morning attempts #5 and #6 both failed at writer phase with the SAME root cause (writer ignoring `#R-TEXTBOOK-30W` Step A, citing Grade 4 anchors not in plan). Orchestrator rewrote the rule TWICE in one overnight session without changing the underlying behavior, instead of switching tactics.

Smoking gun (found 2026-05-24 via writer-prompt audit dispatched to codex):
- `linear-write.md:455` — `**1. Textbook grounding: \`mcp__sources__search_text\` for each \`plan_references\` entry, then \`mcp__sources__get_chunk_context\` for quotes.**` — tells the writer to call `search_text` FIRST for each plan ref, directly contradicting `#R-TEXTBOOK-30W` Step A which says "use chunk_id directly from notes."
- `linear-write.md:193` — allows Knowledge Packet anchors (which can be Grade 4) to become `resources.yaml` textbook entries.
- `linear_pipeline.py:504-526` (resources.yaml schema) — permissive, doesn't enforce plan-reference membership pre-emit.

Lesson encoded: "REPEATED-ATTEMPT LOOP" rule — N≥3 same-failure-mode attempts triggers Option B audit, not another rewrite.

## Persistence autopsies

### 2026-05-24 — wrote lesson only to MEMORY.md, user pushed back

The orchestrator updated `memory/MEMORY.md` #M-8 with the dispatch-monitoring lesson but didn't update the curriculum-orchestrator skill. User pointed out the skill is canonical; MEMORY.md is per-session memory. Lesson belongs in both.

Lesson encoded: "PERSISTENCE — WRITE TWICE" rule + reference to `./scripts/deploy_prompts.sh` (the deploy from `claude_extensions/` to `.claude/`).
