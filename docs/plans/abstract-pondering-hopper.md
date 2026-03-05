# Plan: Integrate Content Quality Review into Pipeline + Plan Auto-Fix

**Issue:** #730, #731
**Why:** The manual `/content-review` skill catches issues the pipeline misses (untranslated non-decodable phrases, weak pedagogical examples, plan bugs). Automating these checks prevents recurring quality issues and removes manual review bottlenecks.

---

## Approach: Hybrid Deterministic + Enhanced Prompts

**No new LLM pass.** Instead:
1. Add deterministic checks to `_deterministic_screen()` — catches 70% of content review issues at zero cost
2. Inject findings into existing Gemini Pass 1/2 prompts (already flows via `{DETERMINISTIC_ISSUES}`)
3. Add plan auto-fix as a post-review deterministic step

This adds ~100ms per build, not 2-5 minutes for another LLM call.

---

## Step 1: New file `scripts/audit/checks/content_quality.py`

Deterministic content quality checks:

| Check | Function | Scope | Severity |
|-------|----------|-------|----------|
| Untranslated non-decodable Ukrainian | `check_untranslated_non_decodable()` | A1 M1-M6 | MEDIUM |
| Wall of text (>300 words no break) | `check_wall_of_text()` | All | MEDIUM |
| Engagement box count | `check_engagement_boxes()` | All | MEDIUM |
| Repetitive transitions | `check_repetitive_transitions()` | All | LOW |
| Plan section coverage | `check_plan_section_coverage()` | All | MEDIUM |
| Activity answer VESUM check | `check_activity_answers_vesum()` | All | HIGH |

**Key: `check_untranslated_non_decodable()`**
- Get cumulative charset for module number (from `pipeline_lib.get_decodable_charset()`)
- Find Ukrainian words (regex `[\u0400-\u04ff]+`) in prose
- Skip: vocabulary tables, `> [!` callout labels, text inside `(translation)` parentheses, heading text
- Flag words with letters outside charset that lack an English translation in parens after them

## Step 2: Integrate into `_deterministic_screen()` (build_module.py ~line 3038)

After step 6 (VESUM verification), add step 7: content quality checks. Results go into `result.deterministic_issues` which already flows into review prompts.

## Step 3: Expand `_scan_llm_filler()` (~line 2641)

Add patterns:
- `r"In this (?:lesson|module|section), we will (?:explore|learn|discover)"`
- Repetitive transition detection (3+ sections starting same way)

## Step 4: New file `scripts/plan_autofix.py`

**`auto_fix_plan(plan_path, issues, vesum_data) -> (n_fixes, changelog)`**

Auto-fixable plan issues:
- Vocabulary hint words failing VESUM → remove or annotate
- Duplicate/identical "minimal pairs" → flag (can't auto-fix pedagogical choice)
- Missing pronunciation video URLs → flag

Version bumping: `'4.0' → '4.0.1'`, `'4.0.1' → '4.0.2'`

Add `plan_fixes` changelog to plan YAML:
```yaml
plan_fixes:
  - version: '4.0.1'
    date: '2026-03-05'
    changes:
      - "Removed VESUM-unverified word 'xyz' from vocabulary_hints.required"
```

**Scope limit:** Auto-fix ONLY touches `vocabulary_hints` and adds metadata. Never modifies `content_outline`, `objectives`, `word_target`, or `grammar` — those still need user approval.

## Step 5: Integrate plan auto-fix into review phase (build_module.py ~line 5092)

After `_run_deterministic_fixes(ctx)` (line 5092), before post-review audit:

```python
# 10.5 Plan auto-fix
from plan_autofix import auto_fix_plan
n_plan_fixes, plan_changelog = auto_fix_plan(ctx.paths["plan"], screen.deterministic_issues, screen.vesum_not_found)
if n_plan_fixes:
    log(f"  review: Plan auto-fix: {n_plan_fixes} fix(es)")
```

## Step 6: Update Rule 7 in non-negotiable-rules.md

Add exception:
> **Exception**: The pipeline may auto-fix plan `vocabulary_hints` entries that fail VESUM verification. Changes are version-bumped and logged in `plan_fixes`. Content outline, objectives, and word targets remain immutable.

## Step 7: Log in completion report

Expand `write_completion_report_v2()` to include plan fix changelog if present.

---

## Files to modify

| File | Change |
|------|--------|
| `scripts/audit/checks/content_quality.py` | **NEW** — 6 deterministic checks |
| `scripts/plan_autofix.py` | **NEW** — plan auto-fix with version bumping |
| `scripts/build_module.py` | Integrate checks into `_deterministic_screen()`, add plan auto-fix call |
| `scripts/pipeline_lib.py` | Expand completion report |
| `claude_extensions/rules/non-negotiable-rules.md` | Update Rule 7 exception |

## Verification

1. Run `build_module.py a1 2 --review` — should detect untranslated non-decodable phrases deterministically
2. Run `build_module.py a1 1 --review` — should pass clean (M1 was already fixed)
3. Check that plan auto-fix bumps version and logs changes
4. Verify no false positives on vocabulary tables, callout boxes, or translation parentheses
