# 2026-05-26 — Writer-prompt three small additions (Gemini)

> Dispatch target: `gemini-3.1-pro-preview`, `--mode danger`, `--worktree` (auto-derived path).
> Base: `origin/main` (currently `8331966935`, post PR #2305).

## Why this exists

The m20 anchor build #4 surfaced three small writer-side failures. Each is addressable with a focused writer-prompt addition. Full context: `docs/session-state/2026-05-26-overnight-pt2-m20-build-4-failed-near-publish.md` §"Three failing gates" + `docs/session-state/2026-05-26-session-close-pt3-direction-update.md` §"3 small writer-prompt additions".

## What to add

Three additions to `scripts/build/phases/linear-write.md`. ONLY this file. Other prompts (e.g. `linear-write-grok.md`) stay untouched unless the addition is structurally identical AND the prompt has a clearly mirrored section — if so, mirror; if not, scope to `linear-write.md` only.

### 1. INJECT_ACTIVITY parity check — add to PRE-EMIT HARD STOP block

Build #4 emitted `<INJECT_ACTIVITY id="act-5"/>` inline in `module.md` but did NOT include an `act-5` activity in `activities.yaml`. Result: `inject_activity_ids` HARD-failed.

Locate the existing PRE-EMIT HARD STOP block introduced in PR #2297. Add ONE new bullet to its checklist:

> Every `INJECT_ACTIVITY id=<X>` reference in `module.md` MUST have a corresponding activity with id `<X>` in `activities.yaml`. The build hard-fails on dangling references via the `inject_activity_ids` gate. Before emitting, count your `INJECT_ACTIVITY` markers in `module.md` and confirm each id is defined in `activities.yaml`.

Match the existing bullet style + indentation of the surrounding PRE-EMIT block. If the block uses checkbox syntax or numbered items, mirror it.

### 2. Diglossia guidance for `шо`

Build #4's roommate dialogue used `шо` — natural for the colloquial register. The user clarified in the Pt 3 handoff that `шо` is acceptable inside dialogue contexts and SHOULD be modelled there as a teaching opportunity for the literary↔colloquial pair, but never in teacher-voice narration.

Add ONE line under the existing dialogue-style guidance section:

> `шо` is acceptable inside dialogue blocks (`<DialogueBox>` or `>` blockquotes) when the register is colloquial; never in teacher-voice narration. When you use it, mention the literary↔colloquial pair (`що` literary vs `шо` colloquial) in the vocabulary section so learners know when each is appropriate.

NOTE: a parallel PR is removing `\bшо\b` from `surzhyk_clean` HARD-fail patterns and replacing with a WARN-only `register_consistency` linter. Do NOT make any code changes to `linear_pipeline.py` in THIS dispatch — leave the gate work entirely to the parallel dispatch. You are only writing prose into the writer prompt.

### 3. Tool-citation honesty reinforcement

Build #4 cited `query_pravopys` inside `<plan_reasoning>` but did not actually call it (`tool_theatre_violations=["query_pravopys"]`). The existing rule `#R-CITE-HONEST` says "Every tool name you cite inside `<plan_reasoning>` MUST correspond to an actual tool call" — the writer ignored it.

Two paths; pick BOTH if both apply, else just the first:

**Path A — writer-side reinforcement (do this)**: locate the `#R-CITE-HONEST` rule. Strengthen the language so the consequence is explicit and immediate. Add a line like:

> If you have written a tool name inside `<plan_reasoning>` without making the corresponding tool call in this turn, STOP. Either make the call now, or remove the citation. The pipeline tracks `tool_theatre_violations` and a non-zero count fails the build before publish.

**Path B — code enforcement**: scope-limited; do NOT do this in this dispatch. The Pt 3 handoff notes "may need pipeline-side enforcement: reject builds with any tool_theatre violation upstream of the writer's `<end_gate>`". That is a separate code change with its own gate-wiring implications. If the writer-side reinforcement alone fixes the next build, Path B is unnecessary. Leave Path B for a future dispatch if the writer keeps slipping.

## Required dispatch-brief preamble (#M-4 deterministic-over-hallucination)

Verifiable claims in your work + the tools that produce evidence:

| Claim | Tool / command (capture raw output, quote in PR body) |
|---|---|
| "PRE-EMIT HARD STOP block has the new bullet" | `git diff origin/main -- scripts/build/phases/linear-write.md` — quote the relevant hunk. |
| "Dialogue guidance has the diglossia one-liner" | Same `git diff` hunk. |
| "`#R-CITE-HONEST` strengthened" | Same `git diff` hunk. |
| "Tests pass" | `.venv/bin/python -m pytest tests/ -q --timeout=180` final summary line, OR if no test references `linear-write.md` directly, just `tests/test_writer_prompt_linting.py` and equivalents. Quote raw. |
| "Ruff clean" | `.venv/bin/ruff check scripts/build/phases/` (if applicable — markdown files aren't ruff-checked, so this may be skipped). |
| "Lint-prompts CI gate passes locally" | The repo has a Lint Prompts gate. Run `.venv/bin/python scripts/audit/lint_prompts.py` (or equivalent — search for the prompt-lint entry point). Quote the final pass line. |
| "Commit landed" | `git log -1 --oneline` raw |
| "PR opened" | `gh pr view <N> --json url` raw URL line |

## Numbered dispatch steps

1. `git worktree add` — auto via `--worktree`; cwd will be `.worktrees/dispatch/gemini/writer-prompt-deltas-2026-05-26/`. Confirm `git rev-parse HEAD` is at `origin/main` head.
2. **File work**:
   - Read `scripts/build/phases/linear-write.md` in full first. Identify (a) the PRE-EMIT HARD STOP block, (b) the dialogue-style guidance, (c) the `#R-CITE-HONEST` rule. Confirm locations via `rg`.
   - Add the three deltas, each minimally invasive and consistent with surrounding style.
3. **Tests**:
   - Run the prompt-lint scan: locate via `rg -l 'lint.*prompt' scripts/audit/ ci/ .github/`.
   - Run the broader test suite touching writer-prompt expectations: `.venv/bin/python -m pytest tests/ -k "writer_prompt or linear_write or prompt_lint" -v` (or similar — adjust to what exists).
   - Full sweep: `.venv/bin/python -m pytest tests/ -q --timeout=180`.
4. **Ruff** (skips for markdown but runs for any Python files you touched, which should be none).
5. **Commit** message: `feat(writer-prompt): INJECT_ACTIVITY parity + diglossia + cite-honesty (m20 #4 follow-up)`. Body: explain each of the three additions, link to this brief, link to the Pt 3 handoff.
6. **Push** via `git push -u origin <branch>` — branch will be `dispatch/gemini/writer-prompt-deltas-2026-05-26`.
7. **Open PR** with deterministic-evidence body.
8. **DO NOT AUTO-MERGE.** Wait for human review.

## Out of scope

- NO code changes to `linear_pipeline.py` or any gate logic. Writer-prompt prose ONLY.
- NO additions to other writer prompts (`linear-write-grok.md`, etc.) unless the additions naturally mirror identical pre-existing sections — if you find mirror sections AND the additions fit verbatim, mirror; otherwise scope to `linear-write.md`.
- NO module rebuild / no curriculum artifact changes.
- NO m20 re-fire — that's a separate task waiting on this AND the parallel surzhyk-reclassify PR.

## Acceptance criteria

- PR opens with all blocking CI green.
- The diff is small (likely < 50 lines of writer-prompt text changes across 3 sections).
- PR body quotes raw tool outputs per the #M-4 preamble.
- No unrelated edits.
