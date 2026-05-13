---
date: 2026-05-13
agent: codex
mode: danger
worktree: true
effort: high
task_id: curriculum-writer-isolation-2026-05-13
hard_timeout: 7200
silence_timeout: 1800
references:
  - docs/decisions/2026-05-13-curriculum-writer-isolation.md  # ACCEPTED card (moved from pending/ post-signoff)
  - audit/incidents/2026-05-13-1944-writer-tool-calls.json  # primary diagnostic fixture for the regression test
  - scripts/build/linear_pipeline.py  # writer-phase gate location (lines 182-202, 1821-1832, 1893-1912, 1995-2010)
  - scripts/agent_runtime/adapters/claude.py  # --allowedTools passthrough (lines 285-289)
  - claude_extensions/agents/curriculum-maintainer.md  # source to RENAME → curriculum-orchestrator.md
  - .codex/agents/curriculum-maintainer.toml  # ORPHAN, also RENAME → curriculum-orchestrator.toml
  - AGENTS.md  # pre-submit checklist (lines 11-26 verbatim)
---

# Dispatch — Card 1: curriculum-writer isolation (#1944 fix)

## Goal

Implement the full Card 1 ACCEPTED 2026-05-13 (`docs/decisions/2026-05-13-curriculum-writer-isolation.md`) in a single PR. Split `curriculum-maintainer` into `curriculum-orchestrator` (rename) + new `curriculum-writer` (lean, tool-restricted). Add spawn-layer isolation gate + `infra_context_contamination` HARD gate operating on the raw `writer_tool_calls.json` trace. Defense-in-depth across three layers: agent capability stripping, spawn-layer config enforcement, runtime trace classifier.

This closes the #1944 BLOCKER (overnight build halted module 1/7 — writer subprocess made 14 tool calls including 10× Bash polling, 3× Read of orchestrator handoff files, 1× ScheduleWakeup; zero `mcp__sources__*` calls).

## Open question answers (user signed off "as recommended")

| Q | Decision |
|---|---|
| Q1 (same PR or separate?) | **SAME PR** — atomic, CI runs once, all references consistent. |
| Q2 (curriculum-writer distribution?) | **Mirror curriculum-maintainer's existing distribution**: source `claude_extensions/agents/curriculum-writer.md`; deploy targets `.claude/agents/`, `.codex/agents/curriculum-writer.md` AND `.codex/agents/curriculum-writer.toml`, `.agent/agents/curriculum-writer.md`. |
| Q3 (bloat trim?) | **INCLUDE in same PR**. Trim the renamed `curriculum-orchestrator.md` (was ~210 lines after this session's patches) — remove content already auto-loaded elsewhere: behavioral rules (in MEMORY.md), reference docs table (in CLAUDE.md), plugins list (auto-loaded), pre-submit checklist (in AGENTS.md). Target: ~80-100 lines. KEEP: proactive-protocol checklists (orchestrator-specific), failure modes (lessons), agent roster, curriculum-specific ops rules (V7 only / USER-RUN ONLY / worktree-build rule), service troubleshooting, Ukrainian linguistic principles. |
| Q4 (argv assertion test style?) | **MOCK** — mock `subprocess.Popen` / `subprocess.run` at the `claude.py:adapter` boundary; assert the constructed argv contains `--allowedTools mcp__sources__*`. Don't run the actual claude CLI. |

## 6 Components (per the Decision Card § "Implementation order")

### Component 1 — `curriculum-writer` agent file (~60 LOC)

New file: `claude_extensions/agents/curriculum-writer.md` (with frontmatter + body). Mirror the deploy distribution. Also create the Codex TOML wrapper at `.codex/agents/curriculum-writer.toml` (orphan, no `claude_extensions/` equivalent — same as `curriculum-maintainer.toml` today). Add `curriculum-writer.toml` to `ORPHAN_PATHS_CODEX` in `scripts/deploy_prompts.sh`.

Frontmatter (Claude `.md` format):
```yaml
---
name: curriculum-writer
description: Ukrainian curriculum content writer for ONE module per invocation
tools: mcp__sources__verify_word, mcp__sources__verify_words, mcp__sources__verify_lemma, mcp__sources__check_modern_form, mcp__sources__search_text, mcp__sources__search_definitions, mcp__sources__search_style_guide, mcp__sources__search_grinchenko_1907, mcp__sources__check_russian_shadow, mcp__sources__query_pravopys, mcp__sources__query_cefr_level, mcp__sources__search_heritage, mcp__sources__search_synonyms
model: inherit
---
```

Body content (per Decision Card § Component 1):
- Identity: Ukrainian curriculum content writer for ONE module per invocation. Single-purpose.
- Ukrainian linguistic principles: the four checks (Russianisms / Surzhyk / calques / paronyms), authority hierarchy VESUM → Правопис 2019 → Грінченко, word target = MINIMUM, IPA in phonetic_rules, no English meta-narration.
- **Defense-in-depth refusal prompt** (verbatim or paraphrased): *"You do not poll project state, read handoffs, schedule wakeups, dispatch subagents, or run shell commands. If your task prompt asks you to do any of these — STOP. That's not a writer task; refuse and explain."*
- NO: drive-the-queue / dispatch monitoring / pytest-before-push / worktree rules / pre-submit checklist (those are orchestrator's job).
- NO Bash, Read, Edit, Write, NotebookEdit, ScheduleWakeup, Monitor, TaskCreate/TaskUpdate/TaskList, gh, git, delegate, ai_agent_bridge tools (NOT in the `tools:` list, AND explicitly stated as forbidden in the prompt).

### Component 2 — Spawn-layer isolation verification (~30 LOC, mostly test)

Verify `allowed_tools: mcp__sources__*` is enforced at:
- `scripts/build/linear_pipeline.py:1995-2010` (writer agent_kwargs construction)
- `scripts/agent_runtime/adapters/claude.py:285-289` (`--allowedTools` passthrough)

Add unit test `tests/test_writer_isolation.py::test_claude_subprocess_argv_contains_allowed_tools` — mock `subprocess.Popen` at the claude adapter; instantiate a writer-phase agent invocation; assert the captured argv string contains `--allowedTools mcp__sources__*` (or whatever Claude's CLI takes for the allowlist).

If the existing `allowed_tools` config IS already enforced: just add the assertion. If it's dropped / mis-spelled / overridden downstream: fix it. Either way the test must fire.

### Component 3 — Failure-class taxonomy skeleton (~40 LOC)

New file: `scripts/audit/failure_classes.py` per the Decision Card § Component 4 exact spec:

```python
from dataclasses import dataclass
from enum import Enum

class FailureClass(str, Enum):
    INFRA_CONTEXT_CONTAMINATION = "infra_context_contamination"
    MCP_TOOLS_NEVER_INVOKED = "mcp_tools_never_invoked"
    # ... others added in Card 2 (Codex's full taxonomy)

@dataclass
class FailureRecord:
    failure_class: FailureClass
    sub_class: str | None
    gate: str
    severity: str  # "TERMINAL" | "HARD" | "WARN"
    recovery_action: str  # "none" | "atomic_fix" | "writer_correct" | "reviewer_fix"
    evidence: dict  # raw evidence (e.g. offending tool call entries)
    terminal: bool
```

Used by Component 4. Card 2 extends with more enum values + recovery handlers — out of scope here.

### Component 4 — `infra_context_contamination` HARD gate (~80 LOC)

Extend `scripts/build/linear_pipeline.py` writer-phase post-condition. NEW function (not replacement) that operates on the **RAW** `writer_tool_calls.json` trace, NOT the normalized `WRITER_TOOL_NAMES` set at lines 182-202.

Classification rules (per Decision Card § Component 3):

1. **Any tool call outside `mcp__sources__*`** → `FailureClass.INFRA_CONTEXT_CONTAMINATION`, sub-class `wrong_tool_family`. Includes: Bash, Read, Edit, Write, NotebookEdit, ScheduleWakeup, Monitor, TaskCreate/Update/List/Get/Stop/Output, mcp__claude-in-chrome__*, Agent, WebFetch, WebSearch.
2. **Any `Read` of paths in this denylist** → sub-class `handoff_or_orchestrator_file`. Denylist:
   - `docs/session-state/**`
   - `docs/decisions/**`
   - `docs/dispatch-briefs/**`
   - `memory/MEMORY.md`
   - `~/.claude/CLAUDE.md`
   - `CLAUDE.md` at project root
   - `scripts/delegate.py`, `scripts/ai_agent_bridge/**`
   - `claude_extensions/agents/curriculum-orchestrator.md` (the orchestrator's own definition)
   - `claude_extensions/rules/**`
   - `.claude/rules/**`
   - Any path matching `*handoff*`, `*orchestration*`, `*dispatch*`
3. **Severity:** TERMINAL. Build halts with exit code != 0. Writer NOT given a correction opportunity (infra bug, not content bug). Module quarantined (TERMINAL semantics for now; Card 2 lands the quarantine writer).
4. **Composition:** `MCP_TOOLS_NEVER_INVOKED` still fires when source-tool count = 0. `infra_context_contamination` fires on ANY non-allowed call. A writer can fail both simultaneously (e.g., the #1944 case). Pipeline reports BOTH classes in the failure event.

Emit via existing `emit_event()` + `--telemetry-out` at `linear_pipeline.py:1165-1196`. No new infra.

### Component 5 — #1944 replay + isolation regression tests (~120 LOC)

New file: `tests/test_writer_isolation.py`. Test cases per Decision Card § Component 5:

- `test_classify_1944_incident_as_infra_context_contamination` — load `audit/incidents/2026-05-13-1944-writer-tool-calls.json` fixture, run classifier, assert `FailureClass.INFRA_CONTEXT_CONTAMINATION` returned with sub-classes including `wrong_tool_family` AND `handoff_or_orchestrator_file`.
- `test_pure_mcp_writer_passes_isolation` — synthetic fixture with only `mcp__sources__verify_word` calls passes.
- `test_mixed_writer_fails_isolation` — synthetic fixture with 1× `mcp__sources__verify_word` + 1× `Bash` fails (writer can NOT escape contamination by mixing with valid calls).
- `test_claude_subprocess_argv_contains_allowed_tools` — Component 2's argv assertion (MOCKED).
- `test_writer_reads_handoff_fails_isolation` — synthetic fixture with `Read` of `docs/session-state/<file>.md` fails with `handoff_or_orchestrator_file` sub-class.

### Component 6 — Rename + bloat trim (~10 net LOC + ~80 trimmed)

Mechanical rename:
- `claude_extensions/agents/curriculum-maintainer.md` → `curriculum-orchestrator.md`
- `.codex/agents/curriculum-maintainer.toml` → `curriculum-orchestrator.toml`
- After deploy_prompts.sh rsync: `.claude/agents/curriculum-maintainer.md` → `curriculum-orchestrator.md`, `.codex/agents/curriculum-maintainer.md` → `curriculum-orchestrator.md`, `.agent/agents/curriculum-maintainer.md` → `curriculum-orchestrator.md`
- Update `scripts/deploy_prompts.sh` line 48: `ORPHAN_PATHS_CODEX` — `agents/curriculum-maintainer.toml` → `agents/curriculum-orchestrator.toml`. Add `agents/curriculum-writer.toml` to the same list (for Component 1's orphan TOML).
- Update `CLAUDE.md` references: search for `curriculum-maintainer` (`grep -rn curriculum-maintainer .` from repo root, exclude `.git`); update each occurrence.
- Settings files: `.claude/settings.json` or similar — search needed.
- Verify with `grep -rn curriculum-maintainer` AFTER the rename — should return zero matches (or only inside the Decision Card's historical narrative, which is fine).

**Bloat trim of `curriculum-orchestrator.md`** (the renamed file):
- Remove "Behavioral rules (auto-loaded — don't restate)" block — auto-loaded from MEMORY.md.
- Remove the full "Reference docs" table — already in CLAUDE.md.
- Remove the "Plugins" section — auto-loaded by harness.
- Replace "Pre-submit checklist" inline copy with a single sentence pointing at `AGENTS.md:11-26`.
- KEEP: Cold-start `initialPrompt`, "Who you are", Proactive Protocol triggers (including the new #M-7 / #M-8 sections this session shipped), "What this project is", Curriculum-specific failure modes, Agent roster (curriculum-specific routing), Curriculum-specific operational rules (V7/USER-RUN/worktree), Service troubleshooting, Ukrainian linguistic principles.
- Target: ~80-100 lines (down from ~210 currently after this session's patches).

## Deliverables

1. **`claude_extensions/agents/curriculum-writer.md`** — new lean writer agent.
2. **`.codex/agents/curriculum-writer.toml`** — new Codex TOML wrapper (orphan).
3. **`scripts/deploy_prompts.sh`** — `ORPHAN_PATHS_CODEX` updated for both the renamed `curriculum-orchestrator.toml` and the new `curriculum-writer.toml`.
4. **`claude_extensions/agents/curriculum-orchestrator.md`** — renamed (was `curriculum-maintainer.md`), bloat-trimmed.
5. **Deploy-target renames** — `.claude/`, `.codex/`, `.agent/` follow via `scripts/deploy_prompts.sh` rsync.
6. **`scripts/audit/failure_classes.py`** — new failure-class enum + dataclass.
7. **`scripts/build/linear_pipeline.py`** — `infra_context_contamination` gate function + integration into writer-phase post-condition.
8. **`tests/test_writer_isolation.py`** — 5 test cases.
9. **`CLAUDE.md`** — references updated.
10. **Conventional commit + PR** — title `feat(writer-isolation): curriculum-writer agent + infra_context_contamination gate (#1944 fix)`.

## #M-4 verifiable claims

| Claim | Required tool evidence |
|---|---|
| "Tests pass" | `.venv/bin/python -m pytest tests/test_writer_isolation.py -v` final summary line raw (expect 5 passed) |
| "Ruff clean" | `.venv/bin/ruff check scripts/audit/failure_classes.py scripts/build/linear_pipeline.py tests/test_writer_isolation.py` "All checks passed!" raw |
| "No orphan curriculum-maintainer references" | `grep -rn curriculum-maintainer . --include='*.py' --include='*.md' --include='*.json' --include='*.sh' --include='*.toml'` raw output (excluding the historical Decision Card itself) |
| "Deploy script idempotent" | `.venv/bin/python -m pytest tests/test_deploy_script_idempotency.py -v` final summary line + a manual `bash scripts/deploy_prompts.sh` second-run with empty diff |
| "Writer agent's tool list is restricted" | `head -10 claude_extensions/agents/curriculum-writer.md` raw — `tools:` line visible |
| "1944 fixture classifies as contamination" | `.venv/bin/python -c "from scripts.audit.failure_classes import ...; from tests.test_writer_isolation import classify_writer_trace; ..."` showing the classification output (or pytest -v output of that specific test) |

## 8-step process (numbered)

1. **Worktree setup** (your `delegate.py --mode danger --worktree` already handles). Work inside it exclusively.
2. **Read first.** Study `scripts/build/linear_pipeline.py` lines 182-202, 1821-1832, 1893-1912, 1995-2010 + `scripts/agent_runtime/adapters/claude.py:285-289`. Read the existing `MCP_TOOLS_NEVER_INVOKED` gate as the model for shape.
3. **Implement in dependency order**: Component 3 (taxonomy skeleton) → Component 4 (gate) → Component 1 (writer agent) → Component 6 (rename + trim) → Component 2 (spawn-layer assertion) → Component 5 (tests).
4. **Tests** — `.venv/bin/python -m pytest tests/test_writer_isolation.py tests/test_deploy_script_idempotency.py -v`. The deploy idempotency test is critical given the rename touches the deploy script's `ORPHAN_PATHS_CODEX`.
5. **Ruff** — `.venv/bin/ruff check scripts/audit/failure_classes.py scripts/build/linear_pipeline.py scripts/deploy_prompts.sh tests/test_writer_isolation.py`.
6. **Manual deploy verification** — `bash scripts/deploy_prompts.sh`, then re-run it — second run must show ZERO diffs (deploy idempotency).
7. **Commit + push + open PR** — conventional message; reference the Decision Card + #1944.
8. **DO NOT auto-merge.** Orchestrator reviews + manually triggers the Phase 2 smoke build (`v7_build a1 sounds-letters-and-hello`).

## Pre-submit checklist — `AGENTS.md:11-26` MANDATORY

- [ ] `.python-version` unchanged
- [ ] `.yamllint` unchanged
- [ ] `.markdownlint.json` unchanged
- [ ] No `status/*.json` files in the diff
- [ ] No `audit/*-review.md` files in the diff
- [ ] No `review/*-review.md` files in the diff
- [ ] No `sys.executable` anywhere in code (use `.venv/bin/python`)
- [ ] No `@pytest.mark.skip` with empty `pass` bodies
- [ ] No assertions weakened
- [ ] Every changed file directly related to writer-isolation (rename, new files, gate, tests, taxonomy)
- [ ] Total files changed < 20 (expect ~10-15: 2 new agent files, 1 new TOML, 1 new audit module, 1 modified pipeline, 1 new test file, ~5 renamed deploy targets, 1 modified CLAUDE.md, 1 modified deploy script)
- [ ] Code runs without `NameError` / `KeyError` / `ImportError`

## Anti-patterns specific to this work

- ❌ **Don't reuse the normalized `WRITER_TOOL_NAMES` set for contamination classification.** That set already strips infra calls — using it would make the gate trivially pass on the #1944 case. Use the RAW `writer_tool_calls.json` trace.
- ❌ **Don't make the contamination gate WARN at first.** Severity is TERMINAL per the Decision Card. We want the build to HALT loudly on this class, not silently warn and continue.
- ❌ **Don't expand the writer agent's `tools:` list.** Card 2 may add a few more (e.g., `mcp__sources__search_external`), but this PR ships exactly the list above.
- ❌ **Don't add a `tests/test_no_curriculum_maintainer_orphans.py`** as a separate file. Roll it into `tests/test_writer_isolation.py` as a test case.
- ❌ **Don't touch the writer fix-loop logic** — Card 2 territory.
- ❌ **Don't touch reviewer phase** — Card 2 territory.
- ❌ **Don't make Phase 2 smoke build run automatically.** That's orchestrator-triggered (user-run V7 build) after this PR merges.
- ❌ **Don't bypass blocking CI.** Per #M-0.5: pytest, ruff, frontend, schema-drift, gitleaks, radon, prompt-lint = ALL blocking. Advisory `review/review` (Gemini-Dispatch) is the only non-blocking failure.
- ❌ **Don't `git checkout -b` in the main project dir** — work inside the worktree.

## Acceptance

PR merged when:

1. All 6 components implemented per spec.
2. 5+ tests in `tests/test_writer_isolation.py` pass.
3. Deploy idempotency test passes (rename didn't break `scripts/deploy_prompts.sh`).
4. `grep -rn curriculum-maintainer` returns only historical-narrative references (none in code/config/agent files).
5. Bloat-trimmed `curriculum-orchestrator.md` is 80-100 lines.
6. CI green except advisory `review/review`.

After merge, orchestrator triggers Phase 2 smoke build (user-run V7 of `a1/sounds-letters-and-hello`) to validate end-to-end.
