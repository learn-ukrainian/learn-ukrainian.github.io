# Dispatch brief — Writer prompt: ULP S1 baseline + resource-search obligation + dialogue-gloss reconciliation

**Agent**: codex
**Mode**: danger
**Effort**: xhigh
**Branch base**: `origin/main` (`faeed6dd38`)
**Task ID**: `writer-prompt-ulp-and-resource-search-2026-05-25`

## Why this is on codex headless

PR #2275 (worktree symlinks) merged at `faeed6dd38` and unblocks the headless dispatch lane (`.venv` is now symlinked into dispatch worktrees). Writer-prompt engineering is mechanical-with-judgment scope — exactly codex's sweet spot. Codex UI session stays warm for the m20 anchor REBUILD that follows this PR.

## Context — Phase 3 m20 build failed

Issue #2288 captured the failure: a1/m20 anchor build hit `module_failed phase=python_qg reason="resources_search_attempted: passed=false, search_attempt_count=0"`. Manual inspection of the failed artifact also surfaced:

- Vocab 20 vs required 25-40
- Word count 1155 vs 1200 minimum
- Only 3 combining acute marks (stress marks essentially absent vs ULP Practice 3 "every multi-syllable UK term")
- EN-first reflexive-verb framing: "A reflexive verb in Ukrainian is built from..."
- Conflicting dialogue-gloss instruction in writer prompt vs ULP Practice 4
- ULP 7-practices content not present in rendered writer prompt at all

These are SYSTEMIC (writer prompt + gate), not m20-specific. Fix them and m20 rebuilds clean. This PR is the prerequisite to Phase 3 retry.

## Root-cause map (already traced — confirm + fix)

### Bug 1 — `{IMMERSION_RULE}` resolver doesn't emit ULP content

- Placeholder lives at `scripts/build/phases/linear-write.md:223`
- Resolver: `scripts/config.py::get_immersion_rule()` line 790 → calls `_structural_immersion_rule()` line 566
- Current rule output: structural targets (min_uk_dialogue_lines, min_vocab_entries) + language roles
- **Missing**: the ULP 7-practices content from `docs/best-practices/ulp-presentation-pattern.md` (~3-4 KB) for letter modules + mid-S1 A1

### Bug 2 — Conflicting dialogue-gloss instruction

- `scripts/build/phases/linear-write.md:246`: "Each Ukrainian dialogue line needs an inline English gloss within 8 tokens (or the DialogueBox `en` prop). Do not put all translations in a block-bottom gloss."
- Conflicts directly with ULP Practice 4: "Dialogues are presented in pure Ukrainian (no inline English in the dialogue itself). The breakdown / explanation comes AFTER the dialogue, separately."
- The `<DialogueBox en="...">` form is fine (renders side-by-side, satisfies Practice 2). The "inline English gloss within 8 tokens INSIDE the line" form is the ULP violation. Reconcile.

### Bug 3 — Missing resource-search obligation in linear-write.md

- `linear-write-grok.md:270-310` has the full `resources_search_attempted` directive ("If the search returns nothing usable, that is acceptable — but the search attempt MUST be recorded in the writer telemetry. The deterministic gate fails the build if the writer skipped the search entirely.")
- `linear-write.md` (claude-tools default) does NOT carry this obligation — hence `search_attempt_count=0` on the m20 build
- Gate code: `scripts/build/linear_pipeline.py::_resources_search_attempted_gate` line 7893, wired at lines 5809-5810

## Verifiable claims preamble (#M-4)

Every claim in the PR description and commit body MUST be tool-backed. Quote raw outputs.

| Claim | Required evidence |
|---|---|
| "Immersion rule now emits ULP content for letter modules" | Test asserting `get_immersion_rule("a1", 4)` and `get_immersion_rule("a1", 20)` contain the ULP 7-practices keywords (em-dash, stress, UK-first, named persona); `get_immersion_rule("c1", 50)` does NOT contain them |
| "Rendered prompt size stays under 130 KB ceiling" | Test asserting `render_writer_prompt('a1', 'sounds-letters-and-hello')` and other letter-module fixtures stay ≤ 130 KB |
| "Dialogue-gloss conflict resolved" | Diff of `linear-write.md:246` showing the new instruction; test asserting the writer-prompt rendered against an A1 plan does NOT instruct "inline English gloss within 8 tokens" |
| "Resource-search obligation present in linear-write.md" | Diff showing the obligation copied from linear-write-grok.md; grep confirming `resources_search_attempted` appears in linear-write.md |
| "pytest green" | Final summary line raw |
| "ruff clean" | Final summary line raw |

## Steps (numbered, do in order)

1. **Worktree**: `git worktree add -B fix/writer-prompt-ulp-and-resource-search .worktrees/fix/writer-prompt-ulp-and-resource-search origin/main && cd .worktrees/fix/writer-prompt-ulp-and-resource-search`

2. **Read the SSOT** at `docs/best-practices/ulp-presentation-pattern.md` (the 7 Ohoiko practices — lines 17-150). This is what the immersion rule should emit verbatim or compactly for A1 mid-S1.

3. **Implement ULP-rule injection in `scripts/config.py`**:
   - Add a new function `_ulp_practices_rule(track: str, module_num: int) -> str` that returns the compact 7-practices content (target ~3-4 KB rendered) when `track == "a1" and module_num <= 25`, else returns `""`. Use the SSOT's "What this changes about the writer prompt" section (lines 137-150) as the canonical compact form.
   - Extend `get_immersion_rule(track, module_num, learner_state)` to APPEND `_ulp_practices_rule(track, module_num)` to the existing structural rule output when non-empty.
   - Do NOT use a separate placeholder — fold into the existing `{IMMERSION_RULE}` substitution. Minimal blast radius.
   - Optionally add a tighter trigger (`level=="a1" and sequence <= 40`) so a1 m41-m55 also get ULP S2 step-change content; defer S2 specifics if it expands scope.

4. **Reconcile dialogue-gloss instruction in `scripts/build/phases/linear-write.md:246`**:
   - Remove the "inline English gloss within 8 tokens" requirement.
   - Replace with: "Use `<DialogueBox uk='...' en='...'>` to render dialogues with side-by-side translation (this satisfies Practice 2 + Practice 4 of ULP for A1, and the `l2_exposure_floor` gate. Em-dash bare lines without `en` prop fail the gate.)"
   - Keep the existing "em-dash-only dialogue under `## Діалоги` is invisible to `l2_exposure_floor`" rule.

5. **Add resource-search obligation to `scripts/build/phases/linear-write.md`**:
   - Copy the relevant directive from `linear-write-grok.md:270-310` (the multi-paragraph block about search obligation + resources.yaml schema + omit-vs-empty pattern).
   - Place it in linear-write.md in the same structural position (probably near the §"Resources tab" section if one exists, else near the Tab 4 instructions).
   - Verify the obligation explicitly says: "If you cannot find usable resources, you MUST still record the search attempt in writer telemetry. Skipping the search fails the `resources_search_attempted` gate."

6. **Add tests** in a new file or extend an existing one:
   - `tests/test_immersion_rule_ulp.py` (or extend `tests/test_immersion_band.py` if it exists):
     - Test A: `get_immersion_rule("a1", 4)` returns string containing "em-dash" OR "side-by-side" OR "stress marks" OR "named persona" (any 2 of the 7-practices keywords)
     - Test B: `get_immersion_rule("a1", 20)` returns the same ULP content
     - Test C: `get_immersion_rule("a1", 50)` returns ONLY structural rule (no ULP content)
     - Test D: `get_immersion_rule("c1", 5)` returns ONLY structural rule
   - `tests/test_writer_prompt_render_size.py` (or extend existing):
     - Test E: rendered prompt for `a1/sounds-letters-and-hello` (m01, letter module) stays ≤ 130 KB
     - Test F: rendered prompt for `a1/my-morning` (m20, mid-S1) stays ≤ 130 KB
     - Test G: rendered prompt for `c1/<sample>` stays ≤ 130 KB
   - `tests/test_writer_prompt_no_inline_gloss_8_tokens.py` (new, small):
     - Test H: rendered prompt for `a1/my-morning` does NOT contain "inline English gloss within 8 tokens"
     - Test I: rendered prompt for `a1/my-morning` contains the `DialogueBox` side-by-side directive
   - `tests/test_writer_prompt_resource_search_obligation.py` (new, small):
     - Test J: rendered prompt for `a1/my-morning` contains `resources_search_attempted` mention
     - Test K: rendered prompt for `c1/<sample>` contains the same

7. **Run tests + lint**:
   ```bash
   # venv symlinked per #2275 (Phase 2 prerequisite, merged at faeed6dd38)
   .venv/bin/python -m pytest tests/test_immersion_rule_ulp.py tests/test_writer_prompt_render_size.py tests/test_writer_prompt_no_inline_gloss_8_tokens.py tests/test_writer_prompt_resource_search_obligation.py -q
   .venv/bin/python -m pytest tests/ -k "immersion or writer_prompt or pipeline" -q
   .venv/bin/ruff check scripts tests
   ```
   ALL must be green. Quote raw outputs.

8. **Smoke test the rendered prompt manually**:
   - Render `a1/my-morning` writer prompt to a tmpfile
   - `grep -c "em-dash\|stress mark\|UK-first\|named persona"` should be ≥ 4
   - `grep "inline English gloss within 8 tokens"` should return nothing
   - `grep "resources_search_attempted\|search.*MUST be recorded"` should return ≥ 1 hit
   - Quote raw outputs in PR body.

9. **Commit + push + PR**:
   - Title: `fix(writer-prompt): ULP S1 baseline injection + resource-search obligation + dialogue-gloss reconciliation`
   - Body: cite issue #2288 + #2278 (the ULP-conditional-injection follow-up filed this morning); include the verifiable-claims table with raw evidence per row; reference m20 anchor retry as the consumer.
   - `git push -u origin fix/writer-prompt-ulp-and-resource-search`
   - `gh pr create --title "..." --body @PR_BODY.md`
   - DO NOT auto-merge.

## Hard constraints

- **Do NOT increase the writer prompt above 130 KB rendered.** The earlier attempt (commented out per session-state) was reverted because it hit 137 KB. The ULP compact form must keep total ≤ 130 KB. If the compact ULP content threatens the ceiling, scope it harder (only `letter_module:true` plans, not `sequence <= 25`).
- **Do NOT touch the `l2_exposure_floor` gate** — the gate is correct; only the writer-prompt instruction conflicts with it. Reconcile at the prompt layer, not the gate layer.
- **Do NOT touch `m20`'s plan YAML** — m20's plan is correct; the writer prompt failing to enforce ULP is the bug.
- **Do NOT change `_resources_search_attempted_gate`** — the gate is correct; the writer prompt is silently failing it because the obligation isn't in linear-write.md.
- **Do NOT close issue #2288 in this PR** — close it in the m20 retry PR after the anchor ships clean.

## Stop conditions

1. Adding the ULP compact content pushes the rendered prompt above 130 KB even for the smallest plan → narrow the trigger (letter_module:true only), re-test, surface if still over.
2. Tests for prompt-size pass for plans without the ULP trigger but fail for plans with it → the compact ULP content is too large; trim it further. Acceptable trim: drop S1→S6 progression detail (keep only S1 baseline 7-practices), keep stress + em-dash + named-persona + dialogue rules.
3. Adding the resource-search obligation breaks an unrelated test (e.g., writer-prompt structured-COT count test) → diagnose, don't force-push.
4. ULP rule emitted at unexpected modules (b1, c1, etc.) → trigger logic is wrong; fix.

## Estimated cost

- Wall clock: 1-2 hours (read + 3 file edits + 4 small test files + run gates + PR)
- Codex weekly: minimal (single dispatch, xhigh effort)

## After this PR merges

Codex UI does:
1. `cd ~/.codex/worktrees/3a9a/learn-ukrainian` (or wherever the m20 Phase 3 worktree lives)
2. `git pull` (gets the new writer-prompt fix)
3. Re-run the build: `.venv/bin/python -u scripts/build/v7_build.py a1 my-morning --worktree --no-resume`
4. The writer will now follow ULP + search resources + use DialogueBox correctly; gates should pass; the §4 ten-check should clear.
5. Open the m20 anchor PR per the original Phase 3 brief.

## Output format

PR body MUST include:
- Verifiable claims table with raw evidence per row
- `git diff --stat` showing all changed files
- Smoke-test grep outputs from Step 8
- Reference to issue #2288 ("addresses by..."); reference #2278 ("implements the ULP-conditional-injection")
- Note: "Do not close #2288 — the m20 anchor PR will close it after the anchor ships clean from a clean writer-prompt foundation."
