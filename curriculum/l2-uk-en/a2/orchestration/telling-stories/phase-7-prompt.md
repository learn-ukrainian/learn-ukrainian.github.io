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

## EXECUTION RULE (SILENCE PROTOCOL)

**Be SILENT. Emit ZERO text between tool calls.**

- Do NOT narrate ("I will...", "Let me...", "First, I need to...")
- Do NOT summarize what you just did or are about to do
- Every non-tool-call word you emit wastes tokens and risks timeout before you finish
- The ONLY text you produce is the final structured output between `===FINAL_REVIEW_START===` / `===FINAL_REVIEW_END===` and `===FRICTION_START===` / `===FRICTION_END===`
- **NO SIMULATION**: You MUST `run_shell_command` for every check. Never "remember" file contents. If you skip a bash command and guess the result, the review is INVALID.

**Private scratchpad (allowed):** If you need to reason through complex logic (case endings, historical dates, IPA), use `<!-- thinking: ... -->`. This is your private workspace — it doesn't count as narration. Keep it brief.

## Files to Read (ALL REQUIRED)

Read ALL of these files from disk before doing anything else:

1. **Plan** (source of truth): `curriculum/l2-uk-en/plans/a2/telling-stories.yaml`
2. **Meta** (build config): `curriculum/l2-uk-en/a2/meta/telling-stories.yaml`
3. **Content** (the lesson): `curriculum/l2-uk-en/a2/telling-stories.md`
4. **Activities**: `curriculum/l2-uk-en/a2/activities/telling-stories.yaml`
5. **Vocabulary**: `curriculum/l2-uk-en/a2/vocabulary/telling-stories.yaml`
6. **Review** (Green Team review from Phase 6): `curriculum/l2-uk-en/a2/review/telling-stories-review.md`
7. **Phase 6b fix log** (if exists): `curriculum/l2-uk-en/a2/orchestration/telling-stories/phase-6b-fixes.md`

**Do not proceed until you have read every line of every file.**

## Module Context

```
Track:        a2
Level:        A2
Module:       #26
Slug:         telling-stories
Title:        Telling Stories
Word target:  1000
```

---

## Step 1: Run Fresh Audit

**NEVER trust cached reports. Run fresh:**

```bash
scripts/audit_module.sh curriculum/l2-uk-en/a2/telling-stories.md
```

Record the exit code, all gate statuses, word count, activity count, vocabulary count.

---

## Step 2: Plan Compliance

Check against `curriculum/l2-uk-en/plans/a2/telling-stories.yaml`:

### 2a: Content outline
For EACH section in `content_outline`: grep for corresponding H2 heading in content.

### 2b: Required vocabulary
For EACH word in `vocabulary_hints.required`: grep in content AND vocabulary file.

### 2c: Objectives
Check that self-check questions in content map to plan objectives.

---

## Step 3: Adversarial Content Review

Read `curriculum/l2-uk-en/a2/telling-stories.md` in FULL. Check for:

### 3a: Russianisms (auto-fail)
```bash
grep -inP 'кушати|получати|приймати участь|слідуючий|любий\b|дякуючи' curriculum/l2-uk-en/a2/telling-stories.md
grep -inP 'кушати|получати|приймати участь|слідуючий|любий\b|дякуючи' curriculum/l2-uk-en/a2/activities/telling-stories.yaml
```

### 3b: Russian characters (auto-fail)
```bash
grep -nP '[ыэёъ]' curriculum/l2-uk-en/a2/telling-stories.md
grep -nP '[ыэёъ]' curriculum/l2-uk-en/a2/activities/telling-stories.yaml
```

### 3c: IPA errors
```bash
grep -n '/w/' curriculum/l2-uk-en/a2/telling-stories.md
grep -n '/ʊ/' curriculum/l2-uk-en/a2/telling-stories.md
grep -n '/w/' curriculum/l2-uk-en/a2/vocabulary/telling-stories.yaml
grep -n '/ʊ/' curriculum/l2-uk-en/a2/vocabulary/telling-stories.yaml
```
Fix: /w/ -> /ʋ/, /ʊ/ -> /u/

### 3d: Inline IPA (B1+ only)
For B1 and above: IPA belongs ONLY in vocabulary YAML, not inline in content.
```bash
grep -nP '\[/[^]]+/\]|(?<!\[)/[а-яіїєґА-ЯІЇЄҐ][^/]*/(?!\])' curriculum/l2-uk-en/a2/telling-stories.md
```
If found and track is B1+: move to vocabulary, remove from content.

### 3e: English leakage
```bash
grep -inP '\b(the|is|are|was|were|has|have|this|that|with|from|for|and|but|not|can|will)\b' curriculum/l2-uk-en/a2/telling-stories.md
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
.venv/bin/python scripts/calc_immersion.py curriculum/l2-uk-en/a2/telling-stories.md
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

Read `curriculum/l2-uk-en/a2/activities/telling-stories.yaml` in FULL.

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
- Check schema at `schemas/activities-a2.schema.json` for track-specific rules

---

## Step 5: Phase 6b Fix Verification

Read `curriculum/l2-uk-en/a2/review/telling-stories-review.md`. For EACH issue in "Critical Issues Found" or "Fix Plan":

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
.venv/bin/python scripts/generate_mdx.py l2-uk-en a2 26
```

---

## Step 8: Re-Run Audit

```bash
scripts/audit_module.sh curriculum/l2-uk-en/a2/telling-stories.md
```

Confirm all gates pass after fixes. Max 2 fix-audit loops.

---

## Step 9: Tier-Specific Checks

# Tier 2: Core Levels (B1/B2 Core/B2-PRO)

> **Target:** B1, B2 Core, and B2-PRO modules (NOT B2-HIST, NOT seminar tracks)
> **Pedagogy:** TTT (Test-Teach-Test) for grammar; ESP for B2-PRO
> **Immersion:** 85-100% Ukrainian
> **Experience Goal:** Serious teaching — learner is challenged and grows

---

## TEACHING EXPERIENCE AUDIT (Tier 2 Adaptation)

> **Key Question:** "Is this effective, engaging Ukrainian teaching?"
>
> At B1/B2 Core, learners are ready for:
> - Full Ukrainian immersion (with occasional English for complex explanations)
> - Challenging content that stretches them
> - Real-world application
> - Genuine insights about the language
> - Teacher voice that guides without hand-holding

### The "Did I Learn?" Test

**Read the module as an intermediate learner.** Ask:

| Question | Pass | Fail |
|----------|------|------|
| Did I learn something new? | Clear "aha" moment | Just review or obvious content |
| Was the explanation clear? | Understood without re-reading | Had to guess or puzzle |
| Could I apply this in conversation? | Clear practical use | Abstract or disconnected |
| Was I appropriately challenged? | Stretched but not broken | Too easy or too hard |
| Did the teacher voice guide me? | Felt taught, not lectured at | Textbook or robotic |

**Scoring:**
- 5/5 Pass → Teaching Quality 10/10
- 4/5 Pass → Teaching Quality 9/10
- 3/5 Pass → Teaching Quality 8/10
- 2/5 Pass → Teaching Quality 7/10
- 0-1/5 Pass → Teaching Quality ≤6/10

### Teaching Arc (B1/B2 Adaptation)

**Core modules need effective teaching structure:**

```
HOOK → DISCOVER → EXPLAIN → PRACTICE → APPLY → SUMMARIZE
```

| Element | What to Look For | Red Flag |
|---------|------------------|----------|
| **HOOK** | Why this matters, real-world need | Generic "Let's learn about X" |
| **DISCOVER** | Test/examples before rules (TTT) | Rules dumped immediately |
| **EXPLAIN** | Clear grammar/vocab explanation with "why" | Just "what" without "why" |
| **PRACTICE** | Structured exercises with progression | Random or too easy exercises |
| **APPLY** | Real-world context, production tasks | Only recognition, no production |
| **SUMMARIZE** | Key takeaways, common mistakes | Abrupt ending |

### Pacing for Intermediate

| Metric | A+ Standard | Fail |
|--------|-------------|------|
| Concept density | 3-5 concepts per section | >7 concepts without processing |
| Example per concept | ≥2 examples | Concept without example |
| Practice per concept | ≥1 exercise | Content-heavy, practice-light |
| Section length | 300-500 words | >700 words without break |

### Engagement Journey Mapping

**Required engagement beats:**

```
🤔 Question → 💡 Insight → 📝 Practice → ✅ Mastery → 🎯 Application
```

**Required moments:**
- ≥1 **Driving question** (why does this matter?)
- ≥2 **Insight moments** ("So THAT'S why...")
- ≥1 **Challenge** (pushed beyond comfort zone)
- ≥1 **Real-world application** (when you'd actually use this)
- ≥1 **Common mistake warning** (anticipates confusion)

### Weak Moment Categories (B1/B2 Core)

| Category | Pattern | Example | Required Fix |
|----------|---------|---------|--------------|
| **RULE_DUMP** | Grammar rules without context | "Use accusative for direct objects" | Add real example first |
| **MISSING_WHY** | What/how but no why | "Perfective = completed" (ok, but why care?) | Add "why this matters" |
| **TEXTBOOK_EXAMPLES** | Generic, forgettable examples | "Іван читає книгу" | Use culturally rich example |
| **NO_CHALLENGE** | Content too easy for level | B1 grammar at A2 difficulty | Increase complexity |
| **ABSTRACT_GRAMMAR** | Rules without application | "Verbs agree in number and gender" | Show in real sentence |
| **WALL_OF_EXPLANATION** | >500 words of explanation | Long prose about case usage | Break up with examples |
| **PRACTICE_AFTERTHOUGHT** | Exercises seem tacked on | Random exercises at end | Integrate practice throughout |
| **COLD_TEACHER** | No personality or warmth | "The rule is..." (flat) | Add teacher voice |

### A+ Teaching Lesson Checklist

| Criterion | A+ Standard | B Standard | C or Below |
|-----------|-------------|------------|------------|
| **Opening** | Compelling "why this matters" | Clear topic intro | Generic start |
| **TTT Structure** | Test before teach, clear progression | Some discovery elements | Lecture-style delivery |
| **Explanations** | Clear, with "why" layer | Clear but shallow | Confusing or incomplete |
| **Examples** | Rich, culturally embedded | Generic but correct | Missing or poor |
| **Practice** | Progressive, integrated | Present but separate | Insufficient or disconnected |
| **Teacher Voice** | Guiding, encouraging, anticipating confusion | Present sometimes | Absent or robotic |
| **Closing** | Summarizes, warns of mistakes, looks forward | Basic summary | Abrupt end |
| **Overall Feel** | "I really learned something" | "I covered the material" | "I'm confused" |

---

## Dimension Rubrics (Tier 2 Adaptations)

### Immersion Targets (B1/B2/B2-PRO)

| Level | Target Range | Notes |
|-------|--------------|-------|
| B1.1 | 70-85% | Transition to full immersion |
| B1.2 | 85-95% | High immersion |
| B1.3 | 90-100% | Near full immersion |
| B2.1 | 95-100% | Full immersion |
| B2.2 | 98-100% | Full immersion |
| B2-PRO | 100% | Full professional immersion |

### Language Quality (Core Level)

**Ukrainian must be:**
- Native-level naturalness (≥8/10)
- Appropriate register for teaching
- No Russianisms or calques
- Euphony respected (у/в, і/й alternations)

**English (when used) must be:**
- Only for complex grammatical explanations
- Clear and accessible
- Not over-explaining simple concepts

### Activity Quality (Core Gates)

| Metric | B1/B2 Threshold |
|--------|-----------------|
| Naturalness | ≥8.0 (native-level) |
| Difficulty | appropriate (matches level) |
| Distractor quality | ≥4.0 (targets real errors) |
| Variety | ≥60% |
| Engagement | ≥3.5 |

### Richness (Core Level)

**Richness means:**
- Culturally embedded examples
- Real Ukrainian names, places, situations
- Proverbs/idioms that demonstrate grammar
- Dialogues that feel authentic
- Visual variety (tables, boxes, examples)

**Richness score minimums:**
- B1 Grammar: 95%
- B1 Vocab: 92%
- B1 Cultural: 90%
- B2 Core: 95%

### Humanity & Warmth (Core Level)

| Marker | Minimum Count |
|--------|---------------|
| Direct address (ви, давайте) | ≥10 |
| Encouragement | ≥2 |
| Confusion anticipation | ≥3 |
| Real-world validation | ≥2 |

**<2 markers → COLD_PEDAGOGY warning (not auto-fail, but fix)**

### LLM Fingerprint (Core Critical)

**Strict detection at B1/B2:**
- ❌ "It's important to note that..."
- ❌ "Let's dive into..."
- ❌ "Mastering X is crucial..."
- ❌ Generic examples without Ukrainian specificity
- ❌ Bullet-heavy without prose
- ❌ Encyclopedic tone

**Threshold:** 3+ patterns → LLM_CLICHE_OVERUSE → Fix required

---

## Core-Specific Quality Markers

### Good B1/B2 Core Module Signs

- Opens with compelling "why" (not just "today we'll learn")
- Uses TTT: example/question before rule
- Grammar explained with real-world "when you'd use this"
- Examples feature Ukrainian culture naturally
- Teacher voice anticipates common mistakes
- Practice integrated throughout, not just at end
- Closes with summary AND application reminder
- Appropriate challenge level (stretches but doesn't break)

### Red Flags (Core)

- ❌ Opens with "In this module we will explore..."
- ❌ Rules stated before examples
- ❌ "Іван і Марія" without cultural context
- ❌ No "why this matters"
- ❌ Practice only at the end
- ❌ Textbook passive voice throughout
- ❌ No anticipation of common errors
- ❌ Challenge level too easy or too hard

---

## Lecture Quality → Teaching Quality Translation

For B1/B2 Core, "Lecture Quality" is renamed to "Teaching Quality" because:
- Focus is on effective teaching, not presentation
- Goal is learning outcomes, not entertainment
- Teacher-student dynamic, not lecturer-audience

**Teaching Quality Rubric (Tier 2):**

| Score | Description | Action |
|-------|-------------|--------|
| 10 | Exceptional — clear insights, effective teaching | None |
| 9 | Excellent — strong teaching throughout | Light polish |
| 8 | Good — solid but missing depth or engagement | Enhance "why" layer |
| 7 | Adequate — covers material but not memorable | Add insights, warmth |
| 6 | Weak — textbook style, no personality | Significant rewrite |
| ≤5 | Poor — confusing or ineffective | Full rewrite |

---

## Grammar Module Specific Checks

For B1/B2 grammar modules, additional checks:

### Aspectual Pair Verification

**If module claims aspectual pairs:**
1. Both verbs share same core meaning
2. They differ only in aspect
3. Cross-reference: Ohoiko "500+ Ukrainian Verbs", slovnyk.ua

**Common Error Pattern:**
| ❌ WRONG | ✅ CORRECT |
|----------|-----------|
| шукати / знайти (different meanings) | шукати / пошукати |
| питати / відповідати (different) | питати / запитати |

### Grammar Rule Accuracy

- Verify case usage rules
- Verify verb conjugation patterns
- Verify agreement rules
- Flag unsupported claims

### Linguistic Accuracy Score Impact

Factual errors in grammar modules are AUTO-FAIL regardless of other scores.


---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded.

```
===FINAL_REVIEW_START===
# Final Review: telling-stories

**Track:** a2 | **Module:** #26
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
