The `KeyError: 'section'` crash is fixed — the audit now runs to completion. The remaining failures (Pedagogy, Immersion) are pre-existing issues unrelated to the original crash.

===REVIEW_START===

## Fix Applied

**Root cause:** `curriculum/l2-uk-en/a1/meta/food-vocabulary.yaml` had `content_outline` entries using `title:` key instead of the required `section:` key, causing `KeyError: 'section'` in `outline_compliance.py:298`.

**Fix:** Replaced the entire `content_outline` block in meta yaml, changing `title:` to `section:` and aligning section names with the plan (`plans/a1/food-vocabulary.yaml`). Removed stale `slug:` fields that don't belong in the outline entries.

**VESUM misses (no fix needed):**
- `Анна`, `Марія`, `Олена`, `Олено`, `Іван` — proper names, expected misses
- `Кушати` — intentionally cited as a Russianism example (line 127, warning box)
- `борща`, `сока`, `сіка`, `чая` — intentional wrong-answer distractors in quiz activities

**Audit result after fix:** No more crash. Audit runs fully. Remaining failures (`Pedagogy ❌` with 16 violations, `Immersion ❌` at 32.5%) are pre-existing content quality issues, not related to the reported crash.

===REVIEW_END===