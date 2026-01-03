# Context: Grammar Validation Testing (Issue #352)

**Agent:** C1-c (Claude Sonnet - New Session)
**Date:** 2026-01-02
**Priority:** P1 - Validation before production use
**Issue:** #352 - Grammar Validation System Refactor

---

## Your Mission

Test the new `--validate-grammar` flag implementation to verify it's production-ready.

**CRITICAL:** You don't have a GEMINI_API_KEY, so you'll use **manual validation** - reading Ukrainian text and checking grammar using your own Ukrainian language knowledge.

---

## What Was Built (Issue #352)

Antigravity Opus implemented a refactor that:
1. Removed complex grammar queue generation system (3 scripts, 964 lines deleted)
2. Added `--validate-grammar` opt-in flag to audit script
3. Uses Gemini API directly with existing prompt
4. Gracefully skips if GEMINI_API_KEY not set

**Implementation commits:**
- 932fda3c - Removed queue generation
- 2ef8b996 - Added --validate-grammar flag

---

## Your Testing Approach

Since you don't have an API key, you'll test by:

1. **Code Review** - Read the implementation, check error handling, verify graceful degradation
2. **Manual Grammar Validation** - Read 15-20 Ukrainian sentences from curriculum modules and validate grammar using your corpus:
   - Check for Russianisms (кушать → їсти)
   - Check for calques ("робити сенс" → "мати сенс")
   - Check for surzhyk (mixed Ukrainian-Russian)
   - Verify case agreement
   - Verify aspect usage
   - Check word order naturalness

3. **Prompt Quality Review** - Evaluate the Ukrainian grammar validator prompt for completeness

---

## Test Plan Location

**READ THIS FIRST:** `/Users/krisztiankoos/projects/learn-ukrainian/docs/dev/GRAMMAR_VALIDATE_TESTING.md`

This contains 10 comprehensive tests:
- Tests 1-3: CLI functionality (help, default behavior, graceful degradation)
- Tests 4-7: Manual grammar validation (read A1/B1/B2 modules, validate with your knowledge)
- Tests 8-9: Code review (error handling, implementation quality)
- Test 10: Prompt quality assessment

---

## How Manual Validation Works

**Example workflow for Test 4:**

1. Read a module:
```bash
cat curriculum/l2-uk-en/b1/01-how-to-talk-about-grammar.md
```

2. Extract 5-10 Ukrainian sentences from the content

3. For each sentence, use your Ukrainian grammar knowledge to check:
   - ✅ Is this grammatically correct standard Ukrainian?
   - ❌ Are there Russianisms? (e.g., "кушать" instead of "їсти")
   - ❌ Are there calques? (e.g., "робити сенс" instead of "мати сенс")
   - ❌ Is case agreement correct?
   - ❌ Is aspect usage correct?
   - ❌ Is word order natural?

4. Document findings in your test report

**You are the LLM validator** - use your internal Ukrainian knowledge corpus to check grammar, exactly as the Gemini API would.

---

## Pedagogical Context (IMPORTANT)

**A1 modules** (scaffolding, mixed English/Ukrainian):
- May have intentional simplifications
- Transliteration expected
- Some "errors" are pedagogical choices
- Grade leniently

**B1+ modules** (97-100% immersed Ukrainian):
- Should be near-perfect Ukrainian
- No Russianisms acceptable
- No calques acceptable
- Grade strictly

**When in doubt** - flag for review rather than false positive.

---

## Deliverable

Create: `docs/dev/GRAMMAR_VALIDATE_TEST_REPORT.md`

**Template:**
```markdown
# Grammar Validation Test Report

**Date:** 2026-01-02
**Tester:** C1-c (Claude Sonnet)
**Issue:** #352

## Test Results Summary

| Test | Description | Result | Notes |
|------|-------------|--------|-------|
| 1 | Help text | PASS/FAIL | ... |
| 2 | Default behavior | PASS/FAIL | ... |
| 3 | No API key | PASS/FAIL | ... |
| 4 | Manual validation (B1) | PASS/FAIL | ... |
| 5 | Manual validation (A1) | PASS/FAIL | ... |
| 6 | Manual validation (B1 immersed) | PASS/FAIL | ... |
| 7 | Manual validation (B2 history) | PASS/FAIL | ... |
| 8 | Error handling review | PASS/FAIL | ... |
| 9 | Implementation quality | PASS/FAIL | ... |
| 10 | Prompt quality | PASS/FAIL | ... |

**Overall:** ☐ All tests pass / ☐ Issues found

## Grammar Issues Discovered

[List any real grammar issues found in modules during manual validation]

**Example:**
- **M01 Line 45:** "Я маю книгу мій друг" → Should be "моєму другу" (dative case)
- **B2-M75 Line 102:** "робити сенс" → Calque, should be "мати сенс"

## Code Quality Assessment

[Your review of the implementation from Tests 8-9]

## Recommendations

- [ ] Implementation ready for production use
- [ ] Documentation complete and accurate
- [ ] Prompt quality acceptable
- [ ] Error handling robust

## Next Steps

[What should be done based on test results]
```

---

## Context Files to Read

**Before starting:**
1. `docs/dev/GRAMMAR_VALIDATE_TESTING.md` - Your test plan (mandatory)
2. `scripts/audit/ukrainian_grammar_validator_prompt.md` - The validation prompt
3. `CLAUDE.md` - Project instructions

**For manual validation:**
4. `curriculum/l2-uk-en/a1/01-*.md` - A1 module sample
5. `curriculum/l2-uk-en/b1/01-*.md` - B1 module sample
6. `curriculum/l2-uk-en/b1/06-*.md` - B1 immersed module sample
7. `curriculum/l2-uk-en/b2/75-*.md` - B2 historical module sample

**For code review:**
8. `scripts/audit_module.py` - Implementation (grep for "validate_grammar_with_llm")

---

## Success Criteria

✅ You've completed the test if:
1. All 10 tests executed and documented
2. Test report created with Pass/Fail for each
3. Any grammar issues found are documented with module + line number
4. Code quality assessed (error handling, graceful degradation)
5. Clear recommendation on production readiness

---

## Commands You'll Need

```bash
# Test 1: Help text
.venv/bin/python scripts/audit_module.py --help

# Test 2: Default behavior
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/01-*.md

# Test 3: With flag, no API key
unset GEMINI_API_KEY
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/01-*.md --validate-grammar

# Tests 4-7: Read modules
cat curriculum/l2-uk-en/b1/01-*.md
cat curriculum/l2-uk-en/a1/01-*.md
cat curriculum/l2-uk-en/b1/06-*.md
cat curriculum/l2-uk-en/b2/75-*.md

# Test 8-9: Code review
grep -A 50 "def validate_grammar_with_llm" scripts/audit_module.py

# Test 10: Prompt review
cat scripts/audit/ukrainian_grammar_validator_prompt.md
```

---

## Important Notes

1. **No API key** - You're the validator, use your Ukrainian knowledge
2. **False positives OK for A1** - Pedagogical simplifications are intentional
3. **Strict for B1+** - 97-100% immersed content should be perfect Ukrainian
4. **Document everything** - Grammar issues, code quality, recommendations
5. **Be thorough** - This gates production use

---

## Questions?

Read the test plan first: `docs/dev/GRAMMAR_VALIDATE_TESTING.md`

**Ready to begin?** Start with Test 1 and work systematically through all 10 tests.
