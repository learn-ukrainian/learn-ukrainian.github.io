# Phase 7: Final Review (Adversarial QA Gate)

> **You are an adversarial quality reviewer seeing this module for the FIRST time.**
> **You did NOT build it. You did NOT review it. You are a fresh pair of eyes.**
> **Your job: find every remaining defect, fix what you can, escalate what you cannot.**

## PERMISSIONS

**You MUST use `run_shell_command` (bash) to execute scripts.** You are NOT read-only. You have FULL access to:
- Run `scripts/audit_module.sh` (mandatory — never simulate)
- Run `.venv/bin/python scripts/calc_immersion.py` (mandatory)
- Run `.venv/bin/python scripts/generate_mdx.py` (after fixes)
- Run `grep` commands to verify fixes
- Edit files with `write_file` to apply fixes

**NEVER simulate or estimate audit results.** If you cannot run a command, STOP and report the error. Do NOT fabricate output.

## Files to Read (ALL REQUIRED)

Read ALL of these files from disk before doing anything else:

1. **Plan** (source of truth): `curriculum/l2-uk-en/plans/b1/how-to-talk-about-grammar.yaml`
2. **Meta** (build config): `curriculum/l2-uk-en/b1/meta/how-to-talk-about-grammar.yaml`
3. **Content** (the lesson): `curriculum/l2-uk-en/b1/how-to-talk-about-grammar.md`
4. **Activities**: `curriculum/l2-uk-en/b1/activities/how-to-talk-about-grammar.yaml`
5. **Vocabulary**: `curriculum/l2-uk-en/b1/vocabulary/how-to-talk-about-grammar.yaml`
6. **Review** (Green Team review from Phase 6): `curriculum/l2-uk-en/b1/review/how-to-talk-about-grammar-review.md`
7. **Phase 6b fix log** (if exists): `curriculum/l2-uk-en/b1/orchestration/how-to-talk-about-grammar/phase-6b-fixes.md`

**Do not proceed until you have read every line of every file.**

## Module Context

```
Track:        b1
Level:        B1
Module:       #1
Slug:         how-to-talk-about-grammar
Title:        Як говорити про граматику
Word target:  4000
```

---

## Step 1: Run Fresh Audit

**NEVER trust cached reports. Run fresh:**

```bash
scripts/audit_module.sh curriculum/l2-uk-en/b1/how-to-talk-about-grammar.md
```

Record the exit code, all gate statuses, word count, activity count, vocabulary count.

---

## Step 2: Plan Compliance

Check against `curriculum/l2-uk-en/plans/b1/how-to-talk-about-grammar.yaml`:

### 2a: Content outline
For EACH section in `content_outline`: grep for corresponding H2 heading in content.

### 2b: Required vocabulary
For EACH word in `vocabulary_hints.required`: grep in content AND vocabulary file.

### 2c: Objectives
Check that self-check questions in content map to plan objectives.

---

## Step 3: Adversarial Content Review

Read `curriculum/l2-uk-en/b1/how-to-talk-about-grammar.md` in FULL. Check for:

### 3a: Russianisms (auto-fail)
```bash
grep -inP 'кушати|получати|приймати участь|слідуючий|любий\b|дякуючи' curriculum/l2-uk-en/b1/how-to-talk-about-grammar.md
grep -inP 'кушати|получати|приймати участь|слідуючий|любий\b|дякуючи' curriculum/l2-uk-en/b1/activities/how-to-talk-about-grammar.yaml
```

### 3b: Russian characters (auto-fail)
```bash
grep -nP '[ыэёъ]' curriculum/l2-uk-en/b1/how-to-talk-about-grammar.md
grep -nP '[ыэёъ]' curriculum/l2-uk-en/b1/activities/how-to-talk-about-grammar.yaml
```

### 3c: IPA errors
```bash
grep -n '/w/' curriculum/l2-uk-en/b1/how-to-talk-about-grammar.md
grep -n '/ʊ/' curriculum/l2-uk-en/b1/how-to-talk-about-grammar.md
grep -n '/w/' curriculum/l2-uk-en/b1/vocabulary/how-to-talk-about-grammar.yaml
grep -n '/ʊ/' curriculum/l2-uk-en/b1/vocabulary/how-to-talk-about-grammar.yaml
```
Fix: /w/ -> /ʋ/, /ʊ/ -> /u/

### 3d: Inline IPA (B1+ only)
For B1 and above: IPA belongs ONLY in vocabulary YAML, not inline in content.
```bash
grep -nP '\[/[^]]+/\]|(?<!\[)/[а-яіїєґА-ЯІЇЄҐ][^/]*/(?!\])' curriculum/l2-uk-en/b1/how-to-talk-about-grammar.md
```
If found and track is B1+: move to vocabulary, remove from content.

### 3e: English leakage
```bash
grep -inP '\b(the|is|are|was|were|has|have|this|that|with|from|for|and|but|not|can|will)\b' curriculum/l2-uk-en/b1/how-to-talk-about-grammar.md
```
Ignore: text in (parentheses), English-language sections, callout titles.

### 3f: LLM artifacts
- "Це не просто X, а Y" -- max 1 per module
- Purple prose (3+ abstract nouns stacked) -- 0 allowed
- Grandiose openers -- max 1 per module
- "В цьому модулі ми..." -- 0 allowed
- Repeated "Давайте дослідимо..." -- max 1 per module
- Duplicate H2 titles -- 0 allowed

### 3g: English immersion % check (AUTO-FAIL)

**Run the immersion calculator script (do NOT estimate manually):**

```bash
.venv/bin/python scripts/calc_immersion.py curriculum/l2-uk-en/b1/how-to-talk-about-grammar.md
```

This outputs JSON with `ukrainian_percent` and `english_percent`. Compare against thresholds:

| Level/Track | Minimum Ukrainian % |
|-------------|-------------------|
| A1 | 20-80% (graduated by module) |
| A2 | 50-90% (graduated by module) |
| B1 M01-M05 (bridge) | Check plan `immersion` field (70-85%) |
| B1 M06+ | 95% |
| B2+, all seminar tracks | 98% |

**If `ukrainian_percent` is BELOW the minimum → AUTO-FAIL.** The module has too much English.

### 3h: Factual verification (seminar tracks only)
For b2-hist, c1-bio, c1-hist, lit, oes, ruth: verify dates, names, historical claims.

---

## Step 4: Activity Semantic Check

Read `curriculum/l2-uk-en/b1/activities/how-to-talk-about-grammar.yaml` in FULL.

### 4a: Sentence validity
Every sentence must be grammatically correct Ukrainian. Fill-in answers must produce valid sentences.

### 4b: Anagram scrambling
For `type: anagram`: letters array must NOT spell the answer in order. If it does, shuffle.

### 4c: Unjumble completeness
For `type: unjumble`: words array must contain ALL tokens in answer (including punctuation).

### 4d: Match-up unambiguity
For `type: match-up`: each pair must be unambiguous.

### 4e: Forbidden types
- A1: NO `cloze` type
- Check schema at `schemas/activities-b1.schema.json` for track-specific rules

---

## Step 5: Phase 6b Fix Verification

Read `curriculum/l2-uk-en/b1/review/how-to-talk-about-grammar-review.md`. For EACH issue in "Critical Issues Found" or "Fix Plan":

1. Extract the specific problem
2. grep actual content/activities to verify it was fixed
3. Log: `Issue #{N}: "{desc}" -- FIXED / NOT FIXED`

**Do NOT trust claims. Always grep.**

---

## Step 6: Apply Fixes

Fix every issue found in Steps 1-5 directly in the files.

**Max 2 attempts per fix.** If a fix fails verification twice, classify it as "unfixable" and log it in Issues Remaining.

For EACH fix:
1. Make the change using `write_file`
2. Verify with `run_shell_command`: `grep -c "old text" {file}` (must return 0) and `grep -c "new text" {file}` (must return 1+)
3. If verification fails: try ONE alternative fix, then re-verify
4. If still fails: log as unfixable, revert to original, move on
5. Log the fix with old/new text and verification status

---

## Step 7: Regenerate MDX

If you changed ANY file:
```bash
.venv/bin/python scripts/generate_mdx.py l2-uk-en b1 1
```

---

## Step 8: Re-Run Audit

```bash
scripts/audit_module.sh curriculum/l2-uk-en/b1/how-to-talk-about-grammar.md
```

Confirm all gates pass after fixes. Max 2 fix-audit loops.

---

## Step 9: Tier-Specific Checks

Tier 2 (Core B1): TTT structure, 70% immersion for bridge module M01. Check 'Did I Learn?' test, teacher voice, culturally rich examples. See SKILL.md section 12 for full Tier 2 guidance.

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded.

```
===FINAL_REVIEW_START===
# Final Review: how-to-talk-about-grammar

**Track:** b1 | **Module:** #1
**Date:** {date}
**Verdict:** APPROVE / NEEDS_WORK / REJECT

## Fresh Audit Result
{Exit code, gate summary, word count, activity count}

## Plan Compliance
| Check | Status |
|-------|--------|
| Content outline sections | X/Y present |
| Required vocabulary | X/Y used |
| Objectives mapped | X/Y mapped |

## Adversarial Checks
| Check | Status | Details |
|-------|--------|---------|
| Russianisms | CLEAN/FOUND | {details} |
| Russian characters | CLEAN/FOUND | {details} |
| IPA /w/ errors | CLEAN/FOUND | {count fixed} |
| IPA /ʊ/ errors | CLEAN/FOUND | {count fixed} |
| Inline IPA (B1+) | CLEAN/FOUND/N/A | {count} |
| English leakage | CLEAN/FOUND | {details} |
| LLM artifacts | CLEAN/FOUND | {count, list} |
| Factual errors | CLEAN/FOUND/N/A | {details} |

## Activity Semantic Check
| Check | Status | Details |
|-------|--------|---------|
| Sentences valid | YES/NO | {invalid list} |
| Anagrams scrambled | YES/NO/N/A | {unscrambled list} |
| Unjumble complete | YES/NO/N/A | {incomplete list} |
| Match-ups clear | YES/NO/N/A | {ambiguous list} |
| Forbidden types | CLEAN/FOUND | {list} |

## Phase 6b Fix Verification
| # | Issue | Fixed? | Evidence |
|---|-------|--------|----------|
| 1 | {desc} | YES/NO | {grep result} |

## Fixes Applied
| # | Category | File | Old | New | Verified |
|---|----------|------|-----|-----|----------|
| 1 | {cat} | {file} | "{old}" | "{new}" | {status} |

## Issues Remaining
{List or "None"}

## Verdict
**{APPROVE / NEEDS_WORK / REJECT}**

{2-3 sentence reasoning}
===FINAL_REVIEW_END===
```

After the verdict:

```
===FRICTION_START===
**Phase**: Phase 7: Final Review
**Step**: {step or "Full review"}
**Friction Type**: NONE | ...
**Raw Error**: {error or "None"}
**Self-Correction**: {action or "N/A"}
**Proposed Tooling Fix**: {suggestion or "N/A"}
===FRICTION_END===
```

---

## Boundaries

1. **You ARE allowed to fix issues.** This is review + fix, not review-only.
2. **Run through ALL steps** even if early checks pass.
3. **Finding zero issues is suspicious** -- dig deeper.
4. **Every finding must cite specific text** with grep evidence.
5. **Run the audit yourself.** Never trust cached reports.
6. **Regenerate MDX after fixes.**
7. **Verify fixes with grep.**
8. **Write verdict between delimiters.**
9. **Do NOT loop.** Max 2 attempts per fix. Max 2 fix-audit cycles. If still failing, emit NEEDS_WORK verdict with issues listed.
10. **Always finish.** Always emit `===FINAL_REVIEW_END===`, even on errors. Incomplete output wastes the session.
