# Batch Review Summary: A1 M7–M10

**Date:** 2026-03-05
**Modules reviewed:** 4 (M7 the-gender-code, M8 this-is-i-am, M9 the-cyrillic-code-iv, M10 syllables-and-transfer)

---

## Results Table

| # | Slug | Prompt Review | Content Grade | Critical | High | Medium | Low | Fixed? |
|---|------|--------------|---------------|----------|------|--------|-----|--------|
| 7 | the-gender-code | NEEDS_WORK (TIER_GUIDANCE broken) | B | 0 | 1 | 1 | 2 | YES (собака gender) |
| 8 | this-is-i-am | NEEDS_WORK (IPA false positive) | B | 0 | 1 | 2 | 1 | YES (locative removal) |
| 9 | the-cyrillic-code-iv | NEEDS_WORK (empty fix prompts) | C | 2 | 1 | 1 | 0 | YES (alphabet + Й + юшка) |
| 10 | syllables-and-transfer | GOOD | B | 0 | 1 | 0 | 2 | YES (переніс→перенос) |

---

## Content Fixes Applied

All HIGH+ issues were fixed during this review session:

1. **M7 собака gender** — Prose claimed "Masculine by default" but VESUM/SUM list feminine as standard. Fixed to feminine.
2. **M8 "на роботі" locative** — Violated nominative-only constraint. Replaced with nominative examples.
3. **M9 garbled alphabet** — Multiple uppercase/lowercase swaps in full alphabet listing (У в→В в, Із з→З з, etc.). Fixed.
4. **M9 Й classified as vowel** — Contradicted its own teaching (line 175 says consonant). Fixed to consonant.
5. **M9 юшка "fish soup"** — Too narrow; standard meaning is "broth/soup". Fixed.
6. **M10 переніс ghost noun** — "переніс" is past tense of перенести, not a noun. Correct noun is "перенос". Fixed all 4 occurrences.

---

## Cross-Module Patterns

### Pattern 1: TIER_GUIDANCE placeholder broken (3+ modules)
- **Scope:** All modules built with v4 pipeline
- **Root cause:** `REVIEW_TIERS_DIR` in `pipeline_lib.py` pointed to deleted path `claude_extensions/commands/review-tiers/`
- **Fix applied:** Updated path to `claude_extensions/skills/plan-review/review-tiers/` in `pipeline_lib.py`
- **Category:** Auto-fixed (template-level)

### Pattern 2: IPA scanner false positive on [Ø] (M8)
- **Root cause:** Python `\w` matches Unicode Ø, so `[Ø]` triggered IPA_BANNED regex
- **Fix applied:** Added `_IPA_WHITELIST = {"[Ø]"}` in `build_module.py`
- **Category:** Auto-fixed (tooling bug)

### Pattern 3: Empty fix prompts ("Fix 0 issues") (M9, M10)
- **Root cause:** Deterministic issues resolved but audit still failing on non-deterministic gate. Fix prompt builder had no issues to list.
- **Fix status:** Previously fixed with ultra-fallback that dumps raw audit tail
- **Category:** Already fixed (tooling bug)

### Pattern 4: VESUM rejects hyphenated syllable breakdowns (M10)
- **Root cause:** VESUM verifier sends "ав-то-бус" as-is; VESUM doesn't recognize hyphenated forms
- **Proposed fix:** Strip hyphens before VESUM lookup: `"ав-то-бус" → "автобус"` → PASS
- **Category:** Needs implementation (tooling improvement)

### Pattern 5: Pipeline doesn't save Gemini outputs to orchestration dir
- **Root cause:** Content and activities outputs went to temp files only
- **Fix applied:** Added `phase-2-output-{N}.md` and `phase-C-output-*.yaml` saving to orch dir in `pipeline_lib.py` and `build_module.py`
- **Category:** Auto-fixed (traceability improvement)

---

## Template/Tooling Fixes Applied This Session

| Fix | File | Type |
|-----|------|------|
| TIER_GUIDANCE path | `scripts/pipeline_lib.py` | Path fix |
| IPA whitelist for [Ø] | `scripts/build_module.py` | Regex fix |
| Content-review accepted by review gate | `scripts/audit/checks/review_validation.py` | Gate expansion |
| Orchestration output saving | `scripts/pipeline_lib.py`, `scripts/build_module.py` | Traceability |

## Modules Needing Rebuild

None — all content fixes were applied directly. All 4 modules pass audit.

## Open Improvements (Not Blocking)

1. **VESUM hyphen stripping** — Would eliminate false positives for syllable-teaching modules
2. **M7 tatою discussion** — Uses non-existent form to negate it (pedagogically valid but could confuse). LOW priority.
3. **M8 "давай" imperative** — Taught as memorized phrase, not grammar. Acceptable.
