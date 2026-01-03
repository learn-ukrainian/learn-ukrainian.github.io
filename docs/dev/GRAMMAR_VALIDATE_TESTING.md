# Task: Test --validate-grammar Flag Implementation

**Issue:** Verify #352 implementation of `--validate-grammar` flag works correctly

**Your task:** Test the new opt-in grammar validation feature using manual validation (no API key available - use your own Ukrainian grammar knowledge).

---

## Background

Issue #352 implemented a new `--validate-grammar` flag for the audit script that:
- Uses Gemini API for Ukrainian grammar validation
- Is **opt-in** (requires explicit flag)
- Gracefully skips if `GEMINI_API_KEY` not set
- Uses existing prompt: `scripts/audit/ukrainian_grammar_validator_prompt.md`

**Commits:**
- 932fda3c - Removed queue generation
- 2ef8b996 - Added --validate-grammar flag

---

## Test Plan

### Test 1: Verify Flag Exists and Help Text

**Command:**
```bash
.venv/bin/python scripts/audit_module.py --help
```

**Expected:**
- Should show `--validate-grammar` option in help text
- Description should mention it's optional and requires GEMINI_API_KEY

**Result:** ☐ Pass / ☐ Fail

---

### Test 2: Run Without Flag (Default Behavior)

**Command:**
```bash
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/01-*.md
```

**Expected:**
- Audit runs normally
- No grammar validation performed
- No mention of GEMINI_API_KEY
- Audit completes successfully

**Result:** ☐ Pass / ☐ Fail

---

### Test 3: Run With Flag, No API Key Set

**Command:**
```bash
unset GEMINI_API_KEY
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/01-*.md --validate-grammar
```

**Expected:**
- Audit runs normally
- Warning message: "⚠️ GEMINI_API_KEY not set. Skipping LLM grammar validation."
- Helpful message: "Set: export GEMINI_API_KEY='your-key'"
- Audit continues and completes (graceful degradation)

**Result:** ☐ Pass / ☐ Fail

---

### Test 4: Manual Grammar Validation (No API Key)

**Since no API key available, manually validate grammar using your Ukrainian knowledge:**

**Read modules and validate:**
```bash
# Read B1 module
cat curriculum/l2-uk-en/b1/01-*.md
```

**Manual validation checklist:**
- ☐ Check for Russianisms (кушать → їсти, кушать)
- ☐ Check for calques ("робити сенс" → "мати сенс")
- ☐ Check for surzhyk (mixed Ukrainian-Russian)
- ☐ Verify case agreement
- ☐ Verify aspect usage
- ☐ Check word order naturalness

**Result:** ☐ Pass / ☐ Fail

**Notes:** Document any real grammar issues found.

---

### Test 5: Manual Validation - A1 Module

**Read and manually validate A1 module:**
```bash
cat curriculum/l2-uk-en/a1/01-*.md
```

**Check:**
- ☐ A1 modules may have pedagogical simplifications (intentional)
- ☐ Mixed Ukrainian/English/transliteration (expected at A1)
- ☐ Core Ukrainian grammar should still be correct
- ☐ Document if simplified forms are pedagogically appropriate

**Result:** ☐ Pass / ☐ Fail

---

### Test 6: Manual Validation - B1 Immersed Module

**Read and manually validate B1 module:**
```bash
cat curriculum/l2-uk-en/b1/06-*.md
```

**Check:**
- ☐ 97%+ Ukrainian immersion
- ☐ Advanced grammar structures (aspect, complex sentences)
- ☐ Verify grammar accuracy
- ☐ Check for common errors (Russianisms, calques)

**Sample sentences to validate:**
- Extract 5-10 complex Ukrainian sentences
- Manually check each for grammatical correctness
- Document findings

**Result:** ☐ Pass / ☐ Fail

---

### Test 7: Manual Validation - B2 Historical Module

**Read and manually validate B2 historical module:**
```bash
cat curriculum/l2-uk-en/b2/75-*.md
```

**Check:**
- ☐ Advanced Ukrainian (historical narrative)
- ☐ Literary constructions
- ☐ Historical terminology accuracy
- ☐ Complex syntax correctness

**Sample sentences to validate:**
- Extract 5-10 historical narrative sentences
- Check for accuracy and naturalness
- Verify terminology is standard Ukrainian (not Russian loans)

**Result:** ☐ Pass / ☐ Fail

---

### Test 8: Code Review - Error Handling

**Review the implementation for error handling:**
```bash
# Read the validate_grammar_with_llm function
grep -A 50 "def validate_grammar_with_llm" scripts/audit_module.py
```

**Check:**
- ☐ Graceful handling when API key not set
- ☐ Try/except blocks for API errors
- ☐ Clear error messages
- ☐ Function returns empty list on error (doesn't crash)
- ☐ Proper import error handling

**Result:** ☐ Pass / ☐ Fail

---

### Test 9: Code Review - Implementation Quality

**Review the implementation:**
```bash
# Read entire validate_grammar_with_llm function
head -150 scripts/audit_module.py | tail -100
```

**Check:**
- ☐ Clean code structure
- ☐ Proper documentation/comments
- ☐ Follows project patterns
- ☐ Uses existing prompt correctly
- ☐ Returns data in expected format

**Result:** ☐ Pass / ☐ Fail

---

### Test 10: Validate Prompt Quality

**Read the prompt:**
```bash
cat scripts/audit/ukrainian_grammar_validator_prompt.md
```

**Check:**
- ☐ Prompt includes Russianism detection
- ☐ Prompt includes calque detection
- ☐ Prompt includes surzhyk detection
- ☐ Prompt considers pedagogical context (A1 vs B2)
- ☐ Prompt asks for JSON output
- ☐ Prompt is clear and well-structured

**Result:** ☐ Pass / ☐ Fail

---

## Implementation Review

### Code Quality Check

**Read the implementation:**
```bash
# View the --validate-grammar implementation
head -100 scripts/audit_module.py
```

**Verify:**
- ☐ Flag properly added to argument parser
- ☐ Graceful handling when GEMINI_API_KEY not set
- ☐ Proper error handling for API calls
- ☐ Clear user messages
- ☐ Integration with existing audit flow

**Result:** ☐ Pass / ☐ Fail

---

## Deliverable

### Test Report

Create: `docs/dev/GRAMMAR_VALIDATE_TEST_REPORT.md`

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
| 4 | With API key | PASS/FAIL | ... |
| 5 | A1 module | PASS/FAIL | ... |
| 6 | B1 module | PASS/FAIL | ... |
| 7 | B2 module | PASS/FAIL | ... |
| 8 | Invalid key | PASS/FAIL | ... |
| 9 | Performance | PASS/FAIL | ... |
| 10 | Prompt quality | PASS/FAIL | ... |

**Overall:** ☐ All tests pass / ☐ Issues found

## Issues Found

[List any bugs, errors, or unexpected behavior]

## Grammar Issues Discovered

[List any real grammar issues found in modules during testing]

## Recommendations

- [ ] Implementation ready for production use
- [ ] Documentation complete and accurate
- [ ] Prompt quality acceptable
- [ ] Error handling robust
- [ ] Performance acceptable

## Next Steps

[What should be done based on test results]
```

---

## Context Files

**Read these:**
- `/Users/krisztiankoos/projects/learn-ukrainian/CLAUDE.md` - Project instructions
- `/Users/krisztiankoos/projects/learn-ukrainian/scripts/audit/ukrainian_grammar_validator_prompt.md` - Validation prompt

**Commits to review:**
```bash
git show 932fda3c --stat
git show 2ef8b996 --stat
git show 2ef8b996:scripts/audit_module.py | head -100
```

---

## Important Notes

1. **No API Key:** Manual validation using your Ukrainian grammar knowledge
2. **False positives:** Some "errors" may be pedagogically intentional (especially A1)
3. **Focus on code review:** Since we can't test API integration, focus on implementation quality
4. **Manual grammar check:** Validate 15-20 sample sentences across A1/B1/B2 levels

---

## Issue Reference

**GitHub:** #352 - Grammar Validation System Refactor
**Implementation:** 2ef8b996
**Prompt location:** `scripts/audit/ukrainian_grammar_validator_prompt.md`

---

**Ready to begin?** Start with Test 1 and work through systematically.
