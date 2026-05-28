# 2026-05-27 — Path B: writer-prompt prose floor + wiki-coverage rendering hint (Gemini)

> Dispatch target: `gemini --mode danger --worktree`, model `gemini-3.1-pro-preview`.
> Base: `origin/main` (currently `20ab69072d`, post PR #2371).
> Tracking: Pt 10 handoff — Phase 2a re-fire (worktree 185032) validated all hardening but failed word_count alone (1058 < 1104 min, 4.1% under) due to structural-density shift after PR #2366's `#R-CLEAN-TABLES` rule pushed content into tables/callouts/dialogue boxes that the gate doesn't count.

## Why this exists

Phase 2a re-fire under the fully hardened pipeline (PRs #2366, #2367, #2370, #2371 all in) produced a nearly-shippable lesson:
- 6/7 step-5 vocabulary integrated (up from 1/7 in Pt 9 refire — `wiki_coverage_required_items` block works)
- Step-4 content (дивлюся conjugation + л insertion) covered
- All hardening gates pass: chunk_context_for_all_refs, published_quote_for_publishable_refs, textbook_quote_fidelity, register_consistency, formatting_standards, vesum_verified, every russianism/surzhyk/calque/paronym gate, engagement_floor, l2_exposure_floor, component_props, activity_schema, plan_reference_match, citations_resolve, ai_slop_clean.
- Zero tool theatre violations.

**Single failing gate: `word_count`.** 1058 prose words vs 1104 minimum (target 1200, 8% tolerance below). Raw `wc -w` on the file is 1335 — the gap is structural: writer placed content density into tables, callouts, and dialogue boxes the gate doesn't count, especially after `#R-CLEAN-TABLES` (PR #2366) shifted authoring toward clean structural elements.

Section breakdown per gate (prose only, gate's count):
- Діалоги: 324 ✓ (270-330)
- Дієслова на -ся: 203 ✗ (under 270 by 67)
- Мій ранок: 243 ✗ (under 270 by 27)
- Підсумок: 104 ✗ (under 270 by 166)

Also missing: `вода` (water) is the single step-5 vocab item the writer skipped despite the `wiki_coverage_required_items` block listing it.

## What to build

### Part A — strengthen per-section prose floor in `scripts/build/phases/linear-write.md`

Find the section that discusses word budgets / per-section minimums (probably near the existing `#R-` rules cluster around line 290+, or in a "Word budget" / "Section budget" subsection). The existing language allows the writer to interpret the budget as TOTAL section including tables.

Add or modify language. Suggested wording (adjust to fit existing prose):

> **Prose words only — section budget.** Per-section word budgets (270-330 each for A1) count PROSE only. Callouts (`:::tip`, `:::caution`), dialogue boxes (`<DialogueBox ...>`), table cells, model-sentence bullets, and code/MDX comments do NOT count toward the per-section budget. The `plan_sections` and `word_count` gates count prose explanatory text only — structural elements are *bonus content density*, not budget.
>
> If your section relies on a table or callout for the teaching, you must STILL include ≥270 words of explanatory prose AROUND the structure. A heading + one paragraph + a 6-row table + one callout is NOT 270 prose words — it is probably 80-120 prose words plus structural fill.
>
> Reach the prose floor BEFORE you optimize for clean structure. A clean structure on top of thin prose fails `word_count` and `plan_sections.word_budgets` both.

Add as a new `#R-PROSE-FLOOR-A1` rule (or fold into existing word-budget rule if one exists). Keep tight — 4-6 lines of directive prose.

### Part B — enhance `_render_wiki_coverage_required_items` in `scripts/build/prompt_builder.py`

The function added in PR #2371 renders the per-obligation breakdown. Currently it lists items but doesn't tell the writer how to demonstrate coverage. The Pt 10 refire missed `вода` despite it being in the list — writer probably included it in a vocab table but no prose model sentence used it.

Modify the rendering to include this hint at the TOP of the rendered block:

> **Coverage rule for each item below**: every listed vocabulary word and example MUST appear at least once in `module.md` PROSE — in a model sentence, a definition with usage, or a teaching paragraph. A vocab table entry alone is NOT coverage. The gate verifies item-by-item in normalized module text; a word that exists only inside a table cell or a dialogue box will count for that structural element's vocabulary but will not satisfy the wiki_coverage obligation.

This nudges the writer to demonstrate each item in prose, which also helps Part A (boosts prose word count) and addresses the `вода` miss specifically.

### Part C — tests

1. Update or add prompt-pinning test in `tests/test_writer_prompt_*.py` (find the appropriate one — there are several from PR #2366) covering `#R-PROSE-FLOOR-A1` or whatever rule ID you use. Anchor on key phrases like "Prose words only", "structural elements are *bonus content density*", "Reach the prose floor BEFORE you optimize".
2. Update or extend `tests/audit/test_wiki_coverage_normalize.py` (or wherever the prompt_builder render is tested) — add an assertion that the rendered block contains the coverage rule hint phrase ("vocab table entry alone is NOT coverage" or similar).
3. Run the full prompt-related test suite to ensure no regressions: `.venv/bin/pytest tests/test_writer_prompt_*.py tests/audit/test_wiki_coverage*.py tests/build/test_linear_pipeline.py -q --no-header`.

## Anti-fabrication contract (#M-4)

| Claim | Required evidence in PR body |
|---|---|
| "Prose floor rule added with anchor phrases" | `grep -n "Prose words only\|prose floor\|structural elements" scripts/build/phases/linear-write.md` raw output |
| "Rendering hint added" | `grep -A 3 "vocab table entry alone\|MUST appear" scripts/build/prompt_builder.py` raw |
| "Prompt-pinning test covers the new rule" | Test names from `pytest tests/test_writer_prompt_*.py --collect-only` listing |
| "Tests pass" | `.venv/bin/pytest tests/test_writer_prompt_*.py tests/audit/test_wiki_coverage*.py tests/build/test_linear_pipeline.py -q --no-header` final summary |
| "Lint clean" | `.venv/bin/ruff check scripts/build/ tests/` final line |
| "PR opened" | `gh pr view --json url` raw URL line |

## Numbered execution steps

1. **Worktree**. You start in `.worktrees/dispatch/gemini/path-b-writer-prompt-section-floor-2026-05-27/`. Verify with `pwd` and `git branch --show-current`. `git fetch origin main && git log --oneline -3` — confirm PR #2371 is in your base.

2. **Survey**:
   - Read `scripts/build/phases/linear-write.md` lines 280-330 (the rule cluster + Tone/Immersion section).
   - Read `scripts/build/prompt_builder.py` — find `_render_wiki_coverage_required_items` (added by PR #2371).
   - Skim `tests/test_writer_prompt_v7_register_rules.py` for the existing test shape — match it for the new rule.

3. **Implement Part A** — add `#R-PROSE-FLOOR-A1` rule (or named what fits existing naming). Keep terse.

4. **Implement Part B** — modify `_render_wiki_coverage_required_items` to prepend the coverage-rule hint.

5. **Implement Part C** — tests (1 new prompt-pinning test, 1 prompt_builder render test, full suite green).

6. **Run tests**: `.venv/bin/pytest tests/test_writer_prompt_*.py tests/audit/test_wiki_coverage*.py tests/build/test_linear_pipeline.py -q --no-header`. Capture final line.

7. **Run lint**: `.venv/bin/ruff check scripts/build/ tests/`. Capture final line.

8. **Commit conventional**:
   ```
   feat(writer-prompt): per-section prose floor + wiki_coverage prose-demonstration hint

   Resolves the structural-density shift caught by Pt 10 Phase 2a refire
   (worktree 185032): writer placed content into tables/callouts/dialogue
   boxes per #R-CLEAN-TABLES (PR #2366), gate counts prose only, gap of
   45 words triggered word_count failure on otherwise-clean output.

   Two surgical changes:
   - #R-PROSE-FLOOR-A1 (linear-write.md): explicit per-section prose
     minimum, structural elements are bonus not budget. Writer must
     reach floor BEFORE optimizing structure.
   - prompt_builder.py: render of wiki_coverage_required_items prepends
     coverage rule "vocab table entry alone is NOT coverage" — every
     listed item must appear in prose at least once. Addresses the
     `вода` miss in Pt 10 refire.

   Tests cover the rule anchor + the render hint.

   X-Agent: gemini/path-b-writer-prompt-section-floor-2026-05-27
   ```

9. **Push + PR**: `git push -u origin gemini/path-b-writer-prompt-section-floor-2026-05-27` then `gh pr create` with title `feat(writer-prompt): per-section prose floor + wiki_coverage prose-demonstration hint`. PR body must include the raw test + lint outputs + Pt 10 context (link to worktree 185032 word_count failure).

10. **DO NOT auto-merge**. Orchestrator review required.

## Scope guardrails

- **DO NOT** modify gate logic. word_count and plan_sections gates are working; they correctly identified the prose gap.
- **DO NOT** modify the existing 6 `#R-` rules from PR #2366. Only add the new rule.
- **DO NOT** touch reviewer rubric `linear-review-dim.md`.
- **DO NOT** touch curriculum/ or m20 module artifacts.
- **DO NOT** add more than what the brief specifies. If you spot an adjacent improvement (e.g. another writer-prompt clarity gap), file a follow-up issue.

## On unexpected blockers

- If `#R-PROSE-FLOOR-A1` overlaps with an existing rule about word counts, fold the new language into the existing rule rather than creating a duplicate. Note the choice in PR body.
- If `_render_wiki_coverage_required_items` doesn't exist at the expected path (PR #2371 may have placed it elsewhere), `git grep -n "_render_wiki_coverage_required_items"` and follow.
- If the prompt is rendered via templating (Jinja, etc.) rather than direct string concat, modify the template properly — don't band-aid via string replacement.
