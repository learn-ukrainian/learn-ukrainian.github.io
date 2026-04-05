# Bug Autopsy: Wiki Review Loop Stuck at 8/10

**Date:** 2026-04-05
**Issue:** #1150
**Symptom:** Wiki compiler could not push `a2/genitive-intro` from 8/10 to 9/10 target.

## What Broke

The wiki review loop couldn't converge to 9/10. The test article `a2/genitive-intro` received valid fixes from Gemini (8.8/10 with 6 fixes that would push it to 9+), but the loop either exited prematurely or exhausted rounds without improvement.

## Why — Three Interacting Bugs

### Bug 1: Decimal score regex can't match `8.8/10`
The regex `(\d+)\s*/\s*10` only matches integer scores. When Gemini returned "**Overall: 8.8/10**", the primary match failed. The fallback took the last integer `/10` match from dimension scores (e.g., "Actionable: 9/10" → score=9), causing the loop to think the article had already passed.

### Bug 2: Final re-review sends stale article text
The "final" re-review reused the `review_prompt` variable from the last loop iteration, which contained the **pre-fix** article text embedded in the prompt string. Despite reading the updated file, the fresh text was never injected into the prompt. Gemini reviewed the OLD article.

### Bug 3: Final re-review never applies its fixes
The final scoring pass (after the main loop) parsed the score and saved the review, but never applied the `<fixes>` block from that review. Known improvements were left on the table.

## Fix

1. **Decimal regex**: `(\d+(?:\.\d+)?)` with `float()` parsing
2. **Fresh prompt per round**: Extracted `_build_review_prompt()` function, called with current article text every round (including the final)
3. **Apply final fixes**: The final re-review now extracts and applies its fixes too

Also refactored into three clean helper functions:
- `_parse_review_score()` — handles all score formats
- `_build_review_prompt()` — builds prompt with current article text
- `_extract_and_apply_fixes()` — extract + apply in one call

## Prevention

- 13 new unit tests covering: decimal scores, integer scores, variant labels, fallback parsing, fix extraction, code fence handling, prompt template echo filtering
- The `_parse_review_score()` function is independently testable — score parsing can never silently regress
