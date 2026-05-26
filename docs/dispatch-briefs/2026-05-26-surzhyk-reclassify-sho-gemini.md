# 2026-05-26 — Reclassify `шо` from surzhyk to register-consistency warning (Gemini)

> Dispatch target: `gemini-3.1-pro-preview`, `--mode danger`, `--worktree` (auto-derived path).
> Base: `origin/main` (currently `8331966935`, post PR #2305).

## Why this exists

The m20 anchor build #4 hard-failed on `surzhyk_clean` because the writer emitted `шо` in a roommate dialogue. The user corrected this in two passes:

1. **First pass**: `шо` is not surzhyk — Antonenko-Davydovych has no entry for it; Russian has `что`/`[што]`, NOT `шо`; the form is a native Ukrainian phonetic reduction of `що`, widespread in colloquial speech across all regions including monolingual Ukrainian-speaking ones.
2. **Second pass**: the diglossia is a TEACHING TARGET — learners benefit from knowing the literary↔colloquial pair (`що` vs `шо`) and when each is appropriate. The pipeline should facilitate teaching it, not suppress one side.

Full context: `docs/session-state/2026-05-26-session-close-pt3-direction-update.md` §"Correction to Pt 2".

## What to do

Two related edits, ONE PR:

### 1. Remove `\bшо\b` from `surzhyk_clean` hard-fail patterns

File: `scripts/build/linear_pipeline.py`. Locate `QUALITY_FIELD_PATTERNS["surzhyk_clean"]` (currently around line 540). Delete the `r"\bшо\b"` entry. The other patterns (`канєшно`, `счас`, `нє`) stay — they ARE surzhyk.

Add a comment in the source explaining the reclassification, referencing this brief and the Pt 3 handoff, so a future reader doesn't re-add the pattern thinking it was a mistake.

### 2. Add a `register_consistency` WARN-only linter

NEW gate function in `scripts/build/linear_pipeline.py` (place near the other quality field checks). Purpose: WARN (never HARD-fail) when `шо` appears outside an appropriate colloquial context in A1-B2 modules. Exempt contexts:

- Inside a `<DialogueBox>` JSX component block (Tab 1 dialogues — colloquial register is correct there).
- Inside a markdown blockquote (lines starting with `>` — quoted speech / dialogue rendering).
- Inside fenced code blocks (would be inside code, not learner-facing prose).
- In modules at levels C1, C2, PRO (advanced learners are expected to handle register sensitivity without scaffolding).

Behaviour:

- Gate name: `register_consistency`.
- Verdict: `WARN` when violations exist, `PASS` when none.
- Severity: `WARN` (NEVER `HARD`).
- Payload: `{"passed": True/False per WARN semantics consistent with neighbouring gates, "verdict": "WARN"/"PASS", "severity": "WARN", "violations": [{"form": "шо", "line": <n>, "context": <short snippet>}], "violation_count": N, "scope_level": <level>}`. Match the shape neighbouring gates return — read 2-3 existing gates first and mirror conventions.

The gate must be wired into the gate registry so it shows up in `python_qg.json` alongside the other gates, with `WARN` severity so it never blocks publish.

### 3. Writer prompt addition (small)

File: `scripts/build/phases/linear-write.md`. ONE LINE under existing dialogue-style guidance: `\`шо\` is acceptable inside dialogue blocks (\`<DialogueBox>\` or \`>\` blockquotes) when the register is colloquial; never in teacher-voice narration. Mention the literary↔colloquial pair in vocab when the module surfaces it.`

This tells the writer the gate is now WARN, not HARD, AND when each form is appropriate. Without this nudge the writer may still avoid `шо` everywhere to be safe.

### 4. Tests

- Update tests that currently expect `surzhyk_clean` to HARD-fail on `шо`. Search: `rg -n 'шо' tests/` — find every fixture / assertion. Remove the assertion that `шо` triggers `surzhyk_clean` (if any test pins it explicitly). Keep tests for `канєшно`/`счас`/`нє`.
- Add new tests for `register_consistency`:
  - `шо` inside `<DialogueBox>` block → PASS (no violations).
  - `шо` inside a `>` blockquote → PASS (no violations).
  - `шо` in teacher-voice paragraph at level A1 → WARN with violation count 1.
  - `шо` in teacher-voice paragraph at level C1 → PASS (out of scope).
  - Multiple `шо` instances mixed (some in dialogue, some not) → WARN with only the out-of-context ones counted.
  - Module with only `що` → PASS.

Mirror the existing test-file conventions. Place tests in `tests/test_register_consistency_gate.py` (new file) OR extend an existing file if you find a clear sibling.

## Required dispatch-brief preamble (#M-4 deterministic-over-hallucination)

Verifiable claims in your work + the tools that produce evidence:

| Claim | Tool / command (capture raw output, quote in PR body) |
|---|---|
| "Tests pass" | `.venv/bin/python -m pytest tests/test_<x>.py -v` final summary line (`N passed in M.MMs`) |
| "Ruff clean" | `.venv/bin/ruff check scripts/build/linear_pipeline.py tests/...` (`All checks passed!` or zero-error count) |
| "шо is not in Antonenko-Davydovych" | `mcp__sources__search_style_guide(query="шо")` returning zero hits, AND `mcp__sources__search_text(query="шо", source_file="antonenko-davydovych-yak-my-hovorymo")` returning zero hits. Quote both raw. |
| "VESUM accepts both forms" | `mcp__sources__verify_words(words=["що", "шо"])` both `is_valid: True`. Quote raw. |
| "Commit landed" | `git log -1 --oneline` raw |
| "PR opened" | `gh pr view <N> --json url` raw URL line |

Do NOT claim "I verified X" without a tool-output line in the PR body for that exact claim. Mirrors MEMORY #M-4.

## Numbered dispatch steps (DISPATCH-BRIEF CHECKLIST)

1. `git worktree add` — runtime does this automatically with `--worktree`; the working dir will be `.worktrees/dispatch/gemini/surzhyk-reclassify-sho-2026-05-26/`. Confirm via `pwd` and `git rev-parse HEAD` (should be at `origin/main` HEAD).
2. **File work**:
   - Edit `scripts/build/linear_pipeline.py`:
     - Remove `r"\bшо\b"` from `QUALITY_FIELD_PATTERNS["surzhyk_clean"]`. Add explanatory comment.
     - Add new `_register_consistency_gate(module_text, plan, module_dir)` function (or equivalent — match how neighbouring single-field WARN gates are structured).
     - Wire the new gate into the gate-registration list (find the spot where other gates are listed in the gate-recording loop; look for `record("surzhyk_clean", ...)` and add `record("register_consistency", ...)` near it).
   - Edit `scripts/build/phases/linear-write.md` with the one-line writer guidance.
   - Update existing tests + add new tests per §4 above.
3. **Tests**: `.venv/bin/python -m pytest tests/test_register_consistency_gate.py tests/test_<other_touched_test_files>.py -v` until all green. Then a broader sweep: `.venv/bin/python -m pytest tests/ -q --timeout=180` to catch unintended breakage. Quote the final summary line in the PR body.
4. **Ruff**: `.venv/bin/ruff check scripts/build/linear_pipeline.py tests/test_register_consistency_gate.py` etc. Quote raw.
5. **Commit** with conventional-commits message: `feat(register-consistency): reclassify шо from surzhyk hard-fail to WARN-only linter (#2294)`. Include a body that explains the user's two-pass linguistic correction and references this brief + the Pt 3 handoff.
6. **Push** via `git push -u origin <branch>` — the conventional branch name auto-derived by the runtime is `dispatch/gemini/surzhyk-reclassify-sho-2026-05-26`.
7. **Open PR** via `gh pr create --title ... --body ...` with the deterministic-evidence body (tool outputs + test pass summary).
8. **DO NOT AUTO-MERGE.** Leave for human review. `AGENT_NO_MERGE=1` is set by default by the dispatcher; respect it.

## Out of scope (do NOT do these)

- Do NOT change the OTHER surzhyk patterns (`канєшно`, `счас`, `нє`). They ARE surzhyk per the canonical heritage-defense literature.
- Do NOT add `register_consistency` checks for other forms (e.g. `що б`/`щоб` confusion). Single-form scope this round.
- Do NOT re-fire m20 — that is a separate task waiting on this + the parallel writer-prompt PR landing.
- Do NOT touch any module artifacts under `curriculum/`. Code + tests + writer-prompt + one writer-side nudge only.

## Acceptance criteria

- PR opens with all blocking CI green (pytest, ruff, gitleaks, frontend, MDX parity, schema drift).
- A build that currently hard-fails on `surzhyk_clean` because of `шо` would now pass `surzhyk_clean` and produce a `register_consistency` WARN entry in `python_qg.json` (verify by manually constructing a fixture module or by re-running on the m20 build #4 artifact directory if practical).
- PR body cites raw tool outputs for every verifiable claim per the #M-4 preamble above.
