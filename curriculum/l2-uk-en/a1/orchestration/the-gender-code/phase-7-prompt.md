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

1. **Plan** (source of truth): `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/the-gender-code.yaml`
2. **Meta** (build config): `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/meta/the-gender-code.yaml`
3. **Content** (the lesson): `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-gender-code.md`
4. **Activities**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/the-gender-code.yaml`
5. **Vocabulary**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/the-gender-code.yaml`
6. **Review** (Green Team review from Phase 6): `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/review/the-gender-code-review.md`
7. **Phase 6b fix log** (if exists): `curriculum/l2-uk-en/a1/orchestration/the-gender-code/phase-6b-fixes.md`

**Do not proceed until you have read every line of every file.**

## Module Context

```
Track:        a1
Level:        A1
Module:       #3
Slug:         the-gender-code
Title:        The Gender Code
Word target:  934
```

---

## Step 1: Run Fresh Audit

**NEVER trust cached reports. Run fresh:**

```bash
scripts/audit_module.sh /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-gender-code.md
```

Record the exit code, all gate statuses, word count, activity count, vocabulary count.

---

## Step 2: Plan Compliance

Check against `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/the-gender-code.yaml`:

### 2a: Content outline
For EACH section in `content_outline`: grep for corresponding H2 heading in content.

### 2b: Required vocabulary
For EACH word in `vocabulary_hints.required`: grep in content AND vocabulary file.

### 2c: Objectives
Check that self-check questions in content map to plan objectives.

---

## Step 3: Adversarial Content Review

Read `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-gender-code.md` in FULL. Check for:

### 3a: Russianisms (auto-fail)
```bash
grep -inP 'кушати|получати|приймати участь|слідуючий|любий\b|дякуючи' /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-gender-code.md
grep -inP 'кушати|получати|приймати участь|слідуючий|любий\b|дякуючи' /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/the-gender-code.yaml
```

### 3b: Russian characters (auto-fail)
```bash
grep -nP '[ыэёъ]' /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-gender-code.md
grep -nP '[ыэёъ]' /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/the-gender-code.yaml
```

### 3c: IPA errors (AUTOMATED — mandatory)

**Run the IPA linter. Do NOT use manual grep for IPA checks.**

```bash
.venv/bin/python scripts/lint_ipa.py /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-gender-code.md
```

If issues found, auto-fix:
```bash
.venv/bin/python scripts/lint_ipa.py /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-gender-code.md --fix
```

**What it catches (8 rules):**
- IPA-001: /ʊ/ → /u/ (Ukrainian has no lax vowel)
- IPA-002: /ɫ/ → /l/ (no dark L)
- IPA-003: tʃ → t͡ʃ (ч needs tie-bar)
- IPA-004: dʒ → d͡ʒ (дж needs tie-bar)
- IPA-005: /w/ → /ʋ/ (В is labiodental, inside IPA brackets)
- IPA-006: /v/ → /ʋ/ (same, inside IPA brackets)
- IPA-007: ts → t͡s (ц needs tie-bar, context-aware)
- IPA-008: dz → d͡z (дз needs tie-bar, context-aware)

**After fixing, re-lint to confirm clean:**
```bash
.venv/bin/python scripts/lint_ipa.py /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-gender-code.md
```

### 3d: Inline IPA (B1+ only)
For B1 and above: IPA belongs ONLY in vocabulary YAML, not inline in content.
```bash
grep -nP '\[/[^]]+/\]|(?<!\[)/[а-яіїєґА-ЯІЇЄҐ][^/]*/(?!\])' /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-gender-code.md
```
If found and track is B1+: move to vocabulary, remove from content.

### 3e: English leakage
```bash
grep -inP '\b(the|is|are|was|were|has|have|this|that|with|from|for|and|but|not|can|will)\b' /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-gender-code.md
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
.venv/bin/python scripts/calc_immersion.py /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-gender-code.md
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

Read `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/the-gender-code.yaml` in FULL.

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
- Check schema at `schemas/activities-a1.schema.json` for track-specific rules

---

## Step 5: Phase 6b Fix Verification

Read `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/review/the-gender-code-review.md`. For EACH issue in "Critical Issues Found" or "Fix Plan":

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
.venv/bin/python scripts/generate_mdx.py l2-uk-en a1 3
```

---

## Step 8: Re-Run Audit

```bash
scripts/audit_module.sh /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-gender-code.md
```

Confirm all gates pass after fixes. Max 2 fix-audit loops.

---

## Step 9: Tier-Specific Checks

# Tier 1: Beginner Levels (A1/A2)

> **Target:** A1 and A2 modules
> **Pedagogy:** PPP (Present-Practice-Produce)
> **Immersion:** 10-90% Ukrainian (scaffolded with English, graduated by band)
> **Experience Goal:** Safe, encouraging tutoring — learner feels supported, not overwhelmed

---

## LESSON EXPERIENCE AUDIT (Tier 1 Adaptation)

> **Key Question:** "Does this feel like a patient, encouraging tutor?"
>
> At A1/A2, learners are fragile. They need:
> - Clear, simple explanations in English
> - Gentle introduction of Ukrainian
> - Lots of encouragement
> - Predictable structure (safety)
> - Quick wins (dopamine hits)

### The "Would I Continue?" Test

**Read the module as a nervous beginner.** Ask:

| Question | Pass | Fail |
|----------|------|------|
| Did I feel overwhelmed? | No, pacing was comfortable | Too much too fast |
| Were instructions clear? | Always knew what to do | Confused about expectations |
| Did I get quick wins? | Early successes, manageable chunks | Long slog before any reward |
| Was Ukrainian scary? | Introduced gently, with support | Thrown into deep end |
| Would I come back tomorrow? | Yes, felt encouraging | No, felt discouraging |

**Scoring:**
- 5/5 Pass → Lesson Quality 10/10
- 4/5 Pass → Lesson Quality 9/10
- 3/5 Pass → Lesson Quality 8/10
- 2/5 Pass → Lesson Quality 7/10
- 0-1/5 Pass → Lesson Quality ≤6/10

### Lesson Arc (Beginner Adaptation)

**Beginner modules need simpler arc:**

```
WELCOME → PREVIEW → PRESENT → PRACTICE → CELEBRATE
```

| Element | What to Look For | Red Flag |
|---------|------------------|----------|
| **WELCOME** | Warm greeting, context setting | Cold start, no orientation |
| **PREVIEW** | "Today you'll learn to..." (sets expectations) | Jumps straight into content |
| **PRESENT** | Clear explanation with examples, visual aids | Wall of text, no examples |
| **PRACTICE** | Guided → supported → independent progression | Too hard too fast |
| **CELEBRATE** | "You can now...", encouragement, progress marker | Abrupt ending |

### Pacing for Beginners

**Cognitive load is critical at A1/A2:**

| Metric | A+ Standard | Fail |
|--------|-------------|------|
| New words per section | ≤5-7 | >10 new words without practice |
| Concepts before practice | ≤2 concepts | >3 concepts before any exercise |
| English support | Present when needed | Missing when learner would struggle |
| Visual aids | Tables, charts for grammar | Prose-only explanations |

### Emotional Safety Mapping

**Required emotional beats for beginners:**

```
😊 Welcomed → 🤔 Curious but safe → 💪 Small win → 😊 Encouraged → 🎯 Progress visible
```

**Required moments:**
- ≥1 **Welcome/orientation** (you're in the right place)
- ≥1 **Curiosity trigger** (but gentle, not overwhelming)
- ≥2 **Quick wins** (you got this!)
- ≥1 **Encouragement** (don't worry, this is normal)
- ≥1 **Progress marker** (look how far you've come)

### Weak Moment Categories (Beginner-Specific)

| Category | Pattern | Example | Required Fix |
|----------|---------|---------|--------------|
| **OVERWHELMING_INTRO** | Too much Ukrainian too fast | First paragraph all Ukrainian | Add English scaffolding |
| **NO_QUICK_WIN** | Long content before any practice | 500 words before first activity | Add mini-exercise earlier |
| **MISSING_ENGLISH** | Learner left to guess meaning | Ukrainian without translation | Add translation/gloss |
| **SCARY_GRAMMAR** | Complex terminology for beginners | "Accusative case" without explanation | Simplify or explain term |
| **NO_ENCOURAGEMENT** | Flat, mechanical instruction | "Now do exercise 2" | Add "Great! Now let's..." |
| **TOO_MUCH_AT_ONCE** | >3 concepts before practice | 5 verb forms in one section | Split into smaller chunks |
| **MISSING_PREVIEW** | No "today you'll learn" | Jumps into content | Add learning objectives |
| **ABRUPT_END** | No celebration of progress | Module just stops | Add "You can now..." summary |

### A+ Beginner Lesson Checklist

| Criterion | A+ Standard | B Standard | C or Below |
|-----------|-------------|------------|------------|
| **Opening** | Warm welcome, clear preview | Basic intro | Cold start |
| **English Support** | Present throughout, scaffolded reduction | Present but inconsistent | Missing when needed |
| **Visual Aids** | Tables, charts, clear formatting | Some visual organization | Walls of text |
| **Pacing** | Small chunks, frequent practice | Reasonable chunks | Overwhelming sections |
| **Quick Wins** | Multiple small successes | At least one | None until end |
| **Encouragement** | Regular positive reinforcement | Some encouragement | None |
| **Closing** | Progress celebration, preview of next | Summarizes content | Abrupt end |
| **Overall Feel** | "I can do this!" | "I learned something" | "This is too hard" |

---

## Dimension Rubrics (Tier 1 Adaptations)

### Immersion Targets (A1/A2)

| Level | Target Range | Notes |
|-------|--------------|-------|
| A1.1 | 20-40% | Heavy English support |
| A1.2 | 40-60% | Increasing Ukrainian |
| A1.3 | 60-80% | Scaffolded transition |
| A2 M01-20 | 50-60% | Core grammar — English for theory |
| A2 M21-50 | 60-75% | Applied grammar — English only for abstract concepts |
| A2 M51-70 | 75-90% | Consolidation — near-full Ukrainian |

### Language Quality (Beginner Adaptation)

**Ukrainian must be:**
- Simple vocabulary (high-frequency words)
- Short sentences
- Clear pronunciation guidance (IPA)
- Consistent grammar patterns (no exceptions early)

**English must be:**
- B1-level readability (accessible to non-native English speakers too)
- Contractions allowed ("you'll", "don't")
- Encouraging tone

### Activity Quality (Beginner Gates)

| Metric | A1/A2 Threshold |
|--------|-----------------|
| Naturalness | ≥5.0 (functional is OK) |
| Difficulty | appropriate (not too_hard) |
| Distractor quality | ≥3.0 (obvious wrong answers OK) |
| Variety | ≥40% (repetition aids learning) |
| Item count | Per level requirements |

### Richness (Beginner Adaptation)

**At A1/A2, richness means:**
- Clear examples (not creative prose)
- Visual organization
- Cultural context that's relatable
- Named Ukrainian references (but simple ones)

**Richness score minimums:**
- A1: 70%
- A2: 75%

### Humanity & Warmth (Beginner Critical)

**Higher thresholds for beginners:**

| Marker | Minimum Count |
|--------|---------------|
| Direct address (you, ви) | ≥15 |
| Encouragement phrases | ≥3 |
| "Don't worry" moments | ≥2 |
| "You can now..." validation | ≥2 |

**Warmth is CRITICAL at beginner level. <3 markers → COLD_PEDAGOGY → Auto-fail**

### LLM Fingerprint (Beginner)

**More lenient than higher levels, but still check:**
- ❌ "In this lesson, we will explore..." (generic AI opening)
- ❌ "It is important to note..." (formal AI voice)
- ✅ "Today you'll learn..." (friendly tutor voice)
- ✅ "Let's start with..." (encouraging, guiding)

**Threshold:** 2+ patterns → flag, but not auto-fail unless egregious

---

## Beginner-Specific Quality Markers

### Good Beginner Module Signs

- Starts with "Привіт!" or similar warm greeting
- Learning objectives clearly stated in English
- New vocabulary introduced 3-5 words at a time
- Grammar tables are clean and visual
- Each section has practice before moving on
- Regular encouragement ("Great!", "You've got this!")
- Ends with "You can now..." celebration
- Preview of what's next

### Red Flags (Beginner)

- ❌ Opens with grammar terminology
- ❌ >10 new words without practice
- ❌ No English for first 200 words
- ❌ "This is easy" (patronizing)
- ❌ Complex sentence structures in Ukrainian
- ❌ No visual aids for grammar
- ❌ Testing before teaching
- ❌ Abrupt ending without encouragement

---

## Lecture Quality → Lesson Quality Translation

For A1/A2, "Lecture Quality" is renamed to "Lesson Quality" because:
- These aren't lectures, they're guided lessons
- Focus is on tutoring, not presenting
- Goal is safety and encouragement, not intellectual engagement

**Lesson Quality Rubric (Tier 1):**

| Score | Description | Action |
|-------|-------------|--------|
| 10 | Exceptional — feels like a caring tutor | None |
| 9 | Excellent — encouraging throughout | Light polish |
| 8 | Good — solid but could be warmer | Add encouragement |
| 7 | Adequate — functional but cold | Significant warmth injection |
| 6 | Weak — feels like a textbook | Rewrite for warmth |
| ≤5 | Poor — discouraging or overwhelming | Full rewrite |


---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded.

```
===FINAL_REVIEW_START===
# Final Review: the-gender-code

**Track:** a1 | **Module:** #3
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
| IPA lint (8 rules) | CLEAN/FIXED | {lint_ipa.py output: X issues, Y fixed} |
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
