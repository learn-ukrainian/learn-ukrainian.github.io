# Review-Content-Scoring Prompt v4.1 (Deep Review)

```yaml
---
name: review-content-v4
description: Deep content review with thorough linguistic verification
version: '4.1'
category: quality
dependencies: audit_module.py
changelog: v4.1 - Deep review first, scoring second. No shortcuts.
---
```

---

## CRITICAL: DEEP REVIEW IS MANDATORY

**This is not a template-filling exercise. You must actually read and verify every word.**

Before you write ANY report or score, you MUST:

1. **Read every line** of the lesson content (`.md` file)
2. **Read every activity item** in the activities file (`.yaml`)
3. **Verify every Ukrainian sentence** is grammatically correct and natural
4. **Check every linguistic claim** (grammar rules, aspectual pairs, etc.) is accurate
5. **Identify real issues** — not template categories

**If you skip this, the review is worthless.**

---

## STEP 1: LOAD ALL CONTENT

Read these files in full (not skimming):

```
curriculum/l2-uk-en/{level}/{slug}.md           # Full lesson content
curriculum/l2-uk-en/{level}/activities/{slug}.yaml   # All activities
curriculum/l2-uk-en/{level}/vocabulary/{slug}.yaml   # Vocabulary (if exists)
```

**Do not proceed until you have read every line.**

---

## STEP 2: DEEP UKRAINIAN VERIFICATION

**You are a native Ukrainian speaker. Every Ukrainian word is your responsibility.**

### For Lesson Content (.md):

Go through the file section by section. For each Ukrainian sentence:

- Is the grammar correct? (cases, verb forms, agreement)
- Does it sound natural? (not robotic, not calqued from English)
- Are there Russianisms? (see list below)
- Is the vocabulary appropriate for the level?

### For Activities (.yaml):

Check EVERY item:

- **quiz**: Is each question grammatically correct? Are all options valid Ukrainian? Is exactly one answer correct?
- **fill-in**: Is the sentence correct with the answer filled in? Are distractors plausible?
- **match-up**: Are all pairs correct? No duplicates?
- **true-false**: Are the true statements actually true? Are false statements clearly false?
- **unjumble**: Does the answer form a correct, natural sentence?
- **cloze**: Is the target word appropriate? Is the sentence natural?
- **error-correction**: Is the "error" actually an error? Is the correction correct?
- **mark-the-words**: Are the target words correctly identified?
- **group-sort**: Are items correctly categorized?

### For Grammar Modules:

Verify all linguistic claims:

- **Aspectual pairs**: Both verbs must share the same core meaning, differing only in aspect
  - ✅ казати/сказати (say/said)
  - ✅ читати/прочитати (read/finished reading)
  - ❌ говорити/сказати (speak vs say — different meanings)
  - ❌ шукати/знайти (search vs find — different meanings)
- **Case rules**: Verify examples match stated rules
- **Verb conjugations**: Check all forms are correct

---

## STEP 3: DOCUMENT REAL ISSUES

As you read, note every issue you find. Be specific:

```markdown
## Issues Found

### Line 45: Incorrect aspectual pair
**Original:** говорити/сказати as aspectual pair
**Problem:** These have different core meanings (speak vs say)
**Fix:** Replace with казати/сказати, add note about говорити/сказати difference

### Activity 7, Item 3: Grammar error
**Original:** Він написав довгого листа
**Problem:** "лист" is inanimate, accusative = nominative
**Fix:** Він написав довгий лист

### Line 89: Unnatural phrasing
**Original:** Це є дуже важливо
**Problem:** Calque from English "This is very important"
**Fix:** Це дуже важливо
```

---

## STEP 4: AUTO-FAIL CHECKLIST

### Russianisms (Auto-fail)

| ❌ Wrong | ✅ Correct |
|----------|-----------|
| кушать | їсти |
| приймати участь | брати участь |
| самий кращий | найкращий |
| слідуючий | наступний |
| на протязі | протягом |
| любий (any) | будь-який |
| отвічати | відповідати |

### Calques (Auto-fail)

| ❌ Wrong | ✅ Correct |
|----------|-----------|
| робити сенс | мати сенс |
| брати місце | відбуватися |
| це є | це (usually) |
| мати місце | відбуватися |

### Activity Errors (Auto-fail)

- Wrong answer marked as correct
- Multiple valid answers but only one accepted
- Grammatically incorrect sentences
- Duplicate items
- Broken YAML structure

---

## STEP 5: APPLY FIXES

**Fix issues as you find them.** Don't just report — fix.

### Fix Immediately:
- Grammar errors
- Russianisms
- Incorrect linguistic claims
- Activity errors
- Typos

### Ask Before Fixing:
- Rewriting >50% of content
- Changing pedagogical approach
- Removing entire sections

---

## STEP 6: WRITE REPORT

**Only after completing deep review**, write the report.

### Save Location
```
curriculum/l2-uk-en/{level}/review/{slug}-review.md
```

### Report Format

```markdown
# Review: {Module Title}

**Level:** {level} | **Module:** {num}
**Status:** ✅ PASS / ❌ FAIL
**Reviewed:** {date}

## Issues Found and Fixed

{List each issue with location, problem, and fix applied}

## Issues Requiring Manual Review

{Any issues you couldn't fix automatically}

## Verification Summary

- Lines read: {X}
- Activity items checked: {X}
- Ukrainian sentences verified: {X}
- Issues found: {X}
- Issues fixed: {X}

## Recommendation

{PASS/FAIL with brief explanation}
```

**Note:** The old 12-dimension scoring system is deprecated. Focus on finding and fixing real issues, not filling out score tables.

---

## STEP 7: RUN AUDIT

After fixes, verify the module still passes technical audit:

```bash
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/{level}/{slug}.md
```

---

## Usage

```
/review-content-v4 [LEVEL] [NUM]        # Single module (recommended)
/review-content-v4 [LEVEL]              # All modules in level
/review-content-v4 [LEVEL] [START-END]  # Range
```

### Module Slug Lookup

1. Read `curriculum/l2-uk-en/curriculum.yaml`
2. Find level section
3. Module N = index N-1 in modules list

---

## Tier-Specific Guidance

For level-specific expectations, read the appropriate tier file:

| Level | Tier File |
|-------|-----------|
| A1, A2 | `claude_extensions/commands/review-tiers/tier-1-beginner.md` |
| B1, B2 Core | `claude_extensions/commands/review-tiers/tier-2-core.md` |
| B2-HIST, C1-BIO, LIT | `claude_extensions/commands/review-tiers/tier-3-seminar.md` |
| C1, C2 | `claude_extensions/commands/review-tiers/tier-4-advanced.md` |

These provide additional context on tone, pacing, and level-appropriate complexity. But the core requirement remains: **read everything, verify everything, fix everything.**

---

## Persona

> Embody the Ukrainian linguist & historian. See `claude_extensions/skills/_shared/persona.md`

**IPA RULE:** All phonetics MUST use IPA (no Latin transliteration).
**PYTHON:** Use `.venv/bin/python` only.
**WORKFLOW:** This is for manual review AFTER audit_module.py passes.
