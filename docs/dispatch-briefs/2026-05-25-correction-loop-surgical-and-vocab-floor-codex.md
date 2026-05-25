# Dispatch brief — Correction loop: surgical per-gate prompts + deterministic vocab_floor path

**Agent**: codex
**Mode**: danger
**Effort**: xhigh
**Branch base**: `origin/main` (`0b54dcd6cc`)
**Task ID**: `correction-loop-surgical-and-vocab-floor-2026-05-25`

## Why this is on cold headless

Codex UI is hot on m20 retries + b1 backfill (parallel UI threads). This work is methodical multi-file engineering on the correction loop — pipeline plumbing, not interactive judgment. Cold headless's sweet spot.

PR #2289 fixed the writer prompt. m20 retries (#2294) now expose a deeper gap: the **correction loop itself**. Two failure modes:

1. **Writer regresses passing gates during correction** — `vesum_verified` was green, correction fixed `word_count`, fabricated `що́стій` in the rewrite, `previously_passed_regression` caught it but only as terminal failure. The patch-bound instruction "do not regenerate" is in the prompt but the writer ignores it.

2. **`vocabulary.yaml` has no correction path at all** — `linear-writer-correction.md:20-22` explicitly says vocab/activities/resources are NOT patched in this correction pass. Writer produces 20 lemmas on first pass, correction loop can never fix it. Vocab count stuck under floor with no recovery.

## Hard scope (READ THIS FIRST)

This PR does TWO targeted fixes and NOTHING ELSE:

1. **Per-gate surgical correction instructions** in `scripts/build/phases/linear-writer-correction.md` — for each fixable gate (`word_count`, `vesum_verified`, `engagement_floor`, `russianisms_strict`, `l2_exposure_floor`), embed gate-specific surgical guidance instead of generic "fix the gate".

2. **Deterministic vocab_floor correction path** in `scripts/build/linear_pipeline.py` — when the vocab count gate fails (vocab.yaml has < per-level floor), deterministically pad from `plan.vocabulary_hints.recommended` (no LLM). Pure code; cannot regress; cannot hallucinate.

OUT-OF-SCOPE (do NOT touch in this PR):
- Diff-only correction architecture (separate larger PR, file as follow-up issue)
- Adding correction paths for activities.yaml / resources.yaml
- Refactoring the gate code itself
- Bridge/adversarial review (NO `ab ask-gemini` — see "Hard constraints" below)

## Context — read first

- `gh issue view 2294` — the m20 retry blocker that motivates this PR
- `scripts/build/phases/linear-writer-correction.md` (75 lines — read the whole thing)
- `scripts/build/linear_pipeline.py` ADR-008 correction surface:
  - `_render_writer_correction_prompt` ~line 3983
  - `_run_python_qg_correction_attempts` ~line 4308
  - `correction_terminal` annotation ~line 4336
  - `previously_passed_regression` gate
- `docs/decisions/2026-04-28-targeted-gate-correction-paths.md` — ADR-008 itself, the architecture you're extending
- `curriculum/l2-uk-en/plans/a1/my-morning.yaml` — has `vocabulary_hints.required` (7) + `vocabulary_hints.recommended` (8) = pad source

## The bugs concretely

### Bug 1 — Writer regression during correction

m20 retry 2 (`a1-my-morning-20260525-210047`): correction round fixed `word_count`, fabricated `що́стій` (should be `шо́стій`) on line 13 of module.md while rewriting the dialogue. The prompt says "Modify in place via append/insert. Never re-author or regenerate" but the writer ignored it. Either the prompt is too weak or the writer is treating "patch" too liberally.

### Bug 2 — Vocab count has no correction path

`linear-writer-correction.md:20-22` excludes vocabulary.yaml from the correction pass. First-pass writer produces 20 lemmas (under the 25 floor for A1). The correction loop can fix module.md issues but cannot touch vocabulary.yaml. So vocab undershoot persists across all correction rounds. Need either:
- (a) Add an LLM correction round for vocabulary.yaml — risky, same hallucination class
- (b) **PREFERRED**: deterministic post-process. When `vocab_count` gate fails AND `plan.vocabulary_hints.recommended` has unused lemmas, pad vocabulary.yaml from that list until floor is met. No LLM. Cannot regress. Cannot hallucinate.

## Verifiable claims preamble (#M-4)

| Claim | Required evidence |
|---|---|
| "Per-gate surgical correction added for N gates" | Diff of `linear-writer-correction.md` showing per-gate sections; test that renders prompt against fixture failures for each gate |
| "Vocab_floor deterministic correction works" | Test that calls the new pad function on a fixture with vocab.yaml=20 and plan with 8 recommended lemmas → returns vocab.yaml=25 (or whatever floor is) |
| "Pad function uses plan.recommended only, never hallucinates" | Test that asserts every added lemma is in `plan.vocabulary_hints.recommended` |
| "Hard fail when pad source exhausted" | Test that calls pad with vocab.yaml=20 + plan with only 3 recommended → returns vocab.yaml=23, gate still fails, error message points to "plan recommends insufficient" |
| "Writer regression prevention" | Test or assertion that correction output cannot replace a specific known-good substring (token-level diff check) |
| "pytest green" | Final summary raw |
| "ruff clean" | Final summary raw |

## Steps (numbered, do in order)

1. **Worktree**: `git worktree add -B fix/correction-loop-surgical-and-vocab-floor .worktrees/fix/correction-loop-surgical-and-vocab-floor origin/main && cd .worktrees/fix/correction-loop-surgical-and-vocab-floor`

2. **Read ADR-008** at `docs/decisions/2026-04-28-targeted-gate-correction-paths.md`. Understand the per-gate correction-handler registry pattern. The vocab_floor path is a NEW correction handler in that registry.

3. **Strengthen `scripts/build/phases/linear-writer-correction.md` with per-gate surgical sections**:

   Replace the generic `## Gate Feedback {CORRECTION_SECTION}` with a per-gate block. New structure:

   ```markdown
   ## Gate Feedback

   {CORRECTION_SECTION}

   ## Surgical instructions for this gate

   {GATE_SPECIFIC_INSTRUCTIONS}
   ```

   The `{GATE_SPECIFIC_INSTRUCTIONS}` is a NEW substitution rendered by `_render_writer_correction_prompt`. Per-gate content:

   - **`vesum_verified`**: "The following tokens FAILED VESUM verification: {missing_tokens}. For EACH offending token, find the smallest fix (likely a typo, wrong stress mark, or missing/extra character) and replace that EXACT token. Do NOT modify any other word in the prose. Do NOT change any prose that does not contain the offending token. If you cannot determine the correct form, leave the token as-is with a `<!-- VERIFY -->` HTML comment immediately after."

   - **`word_count`**: "Current: {current_count} words. Target: {target_min}-{target_max}. Delta to floor: {delta} words. Append a NEW short section (2-3 sentences) or extend the existing 'Підсумок' / final section with {delta}+10 words. Do NOT modify the existing prose, vocab, or dialogues. ONLY append."

   - **`engagement_floor`**: "Current: {current_callouts} callouts. Target: ≥{min_callouts}. Insert a `:::tip` or `:::note` block at the end of the lesson body with a content-anchored mnemonic or cultural note. Do NOT modify existing prose."

   - **`russianisms_strict`**: "The following spans matched Russianism patterns: {findings}. Replace EXACTLY these spans with the suggested Ukrainian alternatives or rephrasings. Do NOT modify any other prose."

   - **`l2_exposure_floor`**: "Current: {current_exposure} UK example surfaces. Target: ≥{min_exposure}. Add {delta}+2 NEW gate-countable Ukrainian example bullets or table rows. Do NOT modify existing examples."

   - **Default (fallback)**: keep the existing generic patch-bound instruction.

   Also strengthen the "Hard constraint — patch-bounded" section with explicit token-level language: "**Do NOT replace any word that is not explicitly listed in the gate feedback above.** If the gate names 5 offending tokens, modify exactly 5 tokens. The rest of the prose stays byte-for-byte identical."

4. **Implement `{GATE_SPECIFIC_INSTRUCTIONS}` rendering** in `scripts/build/linear_pipeline.py::_render_writer_correction_prompt`:
   - Add a per-gate handler dict that maps gate_id → instruction-template-renderer
   - Renderer takes the gate's diagnostic payload (missing tokens, current count, etc.) and produces the surgical instruction text
   - Fall back to generic "fix this gate" text for gates without a specific handler

5. **Implement vocab_floor deterministic correction path** in `scripts/build/linear_pipeline.py`:
   - Add a new ADR-008 correction handler `_correct_vocab_floor(plan, vocab_yaml, gate_payload)`
   - Reads `plan.vocabulary_hints.recommended` (and optionally `required` for additional candidates)
   - Filters out lemmas already in `vocab_yaml`
   - Pads vocab_yaml with the next N lemmas from the candidate list until floor is met or list exhausted
   - Returns updated vocab_yaml + a small diagnostic (added_count, exhausted: bool)
   - NO LLM call. NO MCP. Pure deterministic.
   - Register the handler in the per-gate correction-handler registry so the correction loop dispatches to it when `vocab_count` (or whatever the gate is named) fails.

6. **Add tests** in `tests/test_correction_loop_surgical.py` (new):
   - Test A: render correction prompt for vesum_verified failure → output contains "tokens FAILED VESUM verification" + specific token list + "Do NOT modify any other word"
   - Test B: render correction prompt for word_count failure → output contains current count, delta, "ONLY append"
   - Test C: render correction prompt for an UN-handled gate → output falls back to generic patch-bound text (no crash)

   In `tests/test_vocab_floor_correction.py` (new):
   - Test D: vocab.yaml has 20 lemmas, plan.recommended has 8 unused → pad to 25, returns 5 added lemmas all from plan.recommended
   - Test E: vocab.yaml has 20 lemmas, plan.recommended has only 3 unused → returns 23, exhausted=True
   - Test F: every padded lemma must be in plan.recommended (anti-hallucination assertion)
   - Test G: vocab.yaml already at floor → no-op, added_count=0

   In `tests/test_correction_no_regression.py` (new, optional, can defer if scope creeps):
   - Test H: simulate a correction round where the writer's response replaces a token NOT in the gate feedback → assert the validator rejects it (this requires a small new check in the correction-response validator; defer if too much)

7. **Run tests + lint**:
   ```bash
   # venv symlinked per #2275 (Phase 2 prerequisite)
   .venv/bin/python -m pytest tests/test_correction_loop_surgical.py tests/test_vocab_floor_correction.py -q
   .venv/bin/python -m pytest tests/ -k "correction or vocab_floor or python_qg" -q
   .venv/bin/ruff check scripts tests
   ```
   ALL must be green. Quote raw outputs.

8. **Commit + push + PR**:
   - Title: `fix(correction-loop): surgical per-gate prompts + deterministic vocab_floor correction path`
   - Body MUST include: verifiable-claims table with raw evidence; reference issue #2294; explicit note that this does NOT implement diff-only correction (that's a separate larger PR).
   - `git push -u origin fix/correction-loop-surgical-and-vocab-floor`
   - `gh pr create --title "..." --body @PR_BODY.md`
   - DO NOT auto-merge.

## Hard constraints

- **NO `ab ask-gemini` or `ab discuss` calls during this dispatch.** PR #2289 hit a 30-min silence timeout waiting on an adversarial review that never returned. Do the work, ship the PR, let orchestrator review post-merge. If you want adversarial review, note it in the PR body as a manual follow-up step; do not invoke from within the dispatch.
- **NO scope creep into diff-only correction architecture.** That's a separate ~300-LOC PR with parser + conflict resolution + partial-apply handling. This PR is NOT that. If you start drafting that work, STOP and file a follow-up issue.
- **NO modification to activities.yaml or resources.yaml correction paths.** Only module.md prompt strengthening + vocabulary.yaml deterministic path.
- **NO new MCP tool requirements.** The deterministic vocab_floor correction is pure Python; no `mcp__sources__*` calls.
- **Do NOT touch the gate code itself.** `vocab_count` / `vesum_verified` / etc. stay as-is. We're improving the CORRECTION layer, not the GATE layer.

## Stop conditions

1. The correction-handler registry shape in linear_pipeline.py doesn't accommodate a new vocab_floor handler cleanly → diagnose, propose minimal refactor, file as a separate issue if it's >50 LOC of pipeline code.
2. Tests for the new vocab_floor path break existing pipeline tests → find the conflict, don't force-push.
3. `{GATE_SPECIFIC_INSTRUCTIONS}` substitution renders incorrectly for an existing gate I didn't enumerate → fall back to generic, file follow-up.

## Estimated cost

- Wall clock: 1-2 hours (read + 2 file edits + 3 test files + run gates + PR)
- Codex weekly: minimal (single dispatch, xhigh effort, no parallel work)

## After this PR merges

Codex UI re-fires m20 retry from his existing worktree:
1. `cd ~/.codex/worktrees/3a9a/learn-ukrainian/.worktrees/dispatch/codex/a1-m20-anchor-2026-05-26`
2. `git pull` (gets surgical correction + vocab_floor path)
3. `.venv/bin/python -u scripts/build/v7_build.py a1 my-morning --worktree --no-resume`
4. Writer's first pass produces 20 vocab → vocab_floor handler pads to 25-27 from plan.recommended → vocab gate passes.
5. Writer's word_count + vesum_verified failures (if any) get per-gate surgical fix instructions → minimal token-level fix without regression.
6. Module reaches module_done. §4 ten-check + ULP fidelity run. Anchor PR opens.

If still failing after this PR, the next escalation is the diff-only correction architecture (separate PR, larger scope).

## Output format

PR body MUST include:
- Verifiable claims table with raw evidence per row
- `git diff --stat` showing all changed files
- Reference: addresses part of #2294 (the correction loop + vocab gap); does NOT close #2294 fully (vesum hallucination may still recur if writer ignores the surgical instructions)
- Note: "Do not close #2294 in this PR — the m20 anchor PR will close it after the rebuilt module ships clean."
- Explicit "diff-only correction is a follow-up" line so the next orchestrator session knows what's next.
