# Review-Content-Core-A Prompt (Deep Review for Mixed-Language Modules)

```yaml
---
name: review-content-core-a
description: Deep content review adapted for A1/A2/B1.0 mixed-language modules
version: '1.0'
category: quality
dependencies: audit_module.py
changelog: v1.0 - Initial Core A review prompt (adapted from review-content-v4)
---
```

---

## CRITICAL: DEEP REVIEW IS MANDATORY

**This is not a template-filling exercise. You must actually read and verify every word.**

Before you write ANY report or score, you MUST:

1. **Read every line** of the lesson content (`.md` file)
2. **Read every activity item** in the activities file (`.yaml`)
3. **Verify every Ukrainian sentence** is grammatically correct and natural
4. **Verify every English sentence** is B1-readable and encouraging
5. **Check every IPA transcription** for correct stress and segments
6. **Verify grammar claims** against State Standard 2024 §reference
7. **Identify real issues** — not template categories

**If you skip this, the review is worthless.**

---

## STEP 1: LOAD ALL CONTENT

Read these files in full (not skimming):

```
curriculum/l2-uk-en/{level}/{slug}.md                # Full lesson content
curriculum/l2-uk-en/{level}/activities/{slug}.yaml    # All activities
curriculum/l2-uk-en/{level}/vocabulary/{slug}.yaml    # Vocabulary (if exists)
curriculum/l2-uk-en/{level}/audit/{slug}-research.md  # Research note (if exists)
schemas/activities-{level}.schema.json                # Activity schema (REQUIRED)
claude_extensions/commands/review-tiers/tier-1-beginner.md  # Tier 1 quality bar
```

> **SCHEMA AWARENESS IS MANDATORY.**
> Before suggesting ANY fix to activity YAML, verify the fix is valid against the schema.
> Key constraints:
> - Most activity types use `additionalProperties: false` — unlisted fields cause audit failure
> - A1 allows `anagram` (M01-10 only), A2 introduces `error-correction`
> - **NEVER suggest adding fields that don't exist in the schema**

**Do not proceed until you have read every line.**

---

## STEP 2: DEEP VERIFICATION

### Ukrainian Sentences

Go through the file section by section. For each Ukrainian sentence:

- Is the grammar correct? (cases, verb forms, agreement)
- Does it sound natural? (not robotic, not calqued from English)
- Are there Russianisms? (see checklist below)
- Is the vocabulary appropriate for the level?
- Is sentence length appropriate? (A2: max 15 words)

### English Sentences

For each English sentence:

- Is it B1-readable? (accessible to non-native English speakers)
- Is it warm and encouraging? (tutor voice, not textbook)
- Does it over-explain simple concepts?
- Does it under-explain complex concepts?

### IPA Transcriptions

**Every phonetic transcription must be checked:**

- Stress placement correct? (Ukrainian stress is unpredictable)
- All segments accurate? (no English approximations)
- Consistent format across module?
- Common errors to watch: теорія → /teoˈr⁠ija/ (not /ˈteor⁠ija/)

### State Standard Compliance

If the module teaches grammar:

- Does the grammar explanation match `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt` §section?
- Are exceptions mentioned where the standard requires them?
- Is the level placement correct per the standard?

### Activities

Check EVERY item:

- **quiz**: Each question grammatically correct? All options valid Ukrainian? Exactly one correct answer?
- **fill-in**: Sentence correct with answer inserted? Distractors plausible?
- **match-up**: All pairs correct? No duplicates?
- **true-false**: True statements actually true? False statements clearly false?
- **unjumble**: Answer forms a correct, natural sentence?
- **cloze**: Target word appropriate? Sentence natural?
- **mark-the-words**: Target words correctly identified?
- **group-sort**: Items correctly categorized?
- **anagram** (A1 M01-10 only): Solution is correct? Hint clear?
- **error-correction** (A2+): Error is actually an error? Correction is correct?

---

## STEP 3: DOCUMENT REAL ISSUES

As you read, note every issue you find. Be specific:

```markdown
## Issues Found

### Line 45: IPA stress error
**Original:** /ˈdjatel/ for "дятел"
**Problem:** Stress should be on second syllable
**Fix:** /djaˈtel/

### Line 78: Missing English support
**Original:** Complex grammar point explained only in Ukrainian
**Problem:** At A1 M08, learner needs English for this
**Fix:** Add English explanation before Ukrainian example

### Activity 3, Item 5: Grammar error
**Original:** Він їде на автобус
**Problem:** Movement toward = preposition + accusative, but "автобус" needs "на автобусі" (locative) for being on transport
**Fix:** Він їде автобусом / Він сідає на автобус
```

---

## STEP 4: AUTO-FAIL CHECKLIST

### Russianisms (Auto-fail)

| Wrong | Correct |
|-------|---------|
| кушать | їсти |
| приймати участь | брати участь |
| самий кращий | найкращий |
| слідуючий | наступний |
| на протязі | протягом |
| любий (any) | будь-який |
| отвічати | відповідати |
| вообще | взагалі |
| получати | отримувати |
| відноситися | ставитися |

### Calques (Auto-fail)

| Wrong | Correct |
|-------|---------|
| робити сенс | мати сенс |
| брати місце | відбуватися |
| це є | це (usually) |
| мати місце | відбуватися |

### IPA Errors (Auto-fail for vocabulary)

- Wrong stress placement
- English approximations instead of Ukrainian phonemes
- Missing or incorrect palatalization markers
- Inconsistent transcription format

### L1/L2 Balance Errors (Auto-fail)

Check the immersion ratio against targets:

| Level/Phase | Ukrainian Target | Red Flag |
|-------------|-----------------|----------|
| A1 M01-05 | 10-15% | >25% Ukrainian without support |
| A1 M06-10 | 15-25% | >35% or <10% |
| A1 M11-20 | 25-35% | >45% or <15% |
| A1 M21-44 | 35-40% | >50% or <25% |
| A2 M01-25 | 40-60% | >75% or <30% |
| A2 M26-55 | 50-70% | >80% or <40% |
| A2 M56-70 | 60-75% | >85% or <50% |
| B1 M01-05 | ~50% | >70% or <30% |

**If balance is significantly off target, flag immediately.**

### Beginner Safety Failures (Auto-fail)

From `tier-1-beginner.md` — the "Would I Continue?" test:

| Question | Auto-fail if... |
|----------|----------------|
| Did I feel overwhelmed? | Too much too fast, no scaffolding |
| Were instructions clear? | Confused about what to do |
| Did I get quick wins? | Long slog before any reward |
| Was Ukrainian scary? | Thrown into deep end |
| Would I come back tomorrow? | Felt discouraging |

**≤1/5 Pass on this test → Lesson Quality auto-fail**

Required emotional beats:
- ≥1 Welcome/orientation
- ≥1 Curiosity trigger
- ≥2 Quick wins
- ≥1 Encouragement
- ≥1 Progress marker

**<3 emotional beat markers → COLD_PEDAGOGY → Auto-fail**

### State Standard Violations (Auto-fail for grammar modules)

- Grammar rule stated that contradicts the State Standard
- Case usage explained incorrectly
- Verb aspect rules inaccurate
- Level placement wrong (e.g., B1 grammar taught at A1)

### Activity Errors (Auto-fail)

- Wrong answer marked as correct
- Multiple valid answers but only one accepted
- Grammatically incorrect sentences
- Duplicate items
- Broken YAML structure
- Items don't validate against schema

---

## STEP 5: APPLY FIXES

**Fix issues as you find them.** Don't just report — fix.

### Fix Immediately:
- Grammar errors (Ukrainian and English)
- Russianisms and calques
- IPA transcription errors
- Activity errors
- Typos
- Missing emotional beats (add encouragement)

### Ask Before Fixing:
- Rewriting >50% of content
- Changing pedagogical approach
- Removing entire sections
- Changing L1/L2 balance significantly

---

## STEP 6: SCORE DIMENSIONS (Based on Deep Review)

**Only after completing Steps 1-5**, score each dimension based on what you actually found.

### The 12 Dimensions

| # | Dimension | What to Assess | Auto-fail |
|---|-----------|----------------|-----------|
| 1 | **Lesson Quality** | "Would I Continue?" test — warm, clear, encouraging? | <7 |
| 2 | **Coherence** | Logical flow, transitions, progressive difficulty | <7 |
| 3 | **Relevance** | Aligned with module goals, curriculum plan | <7 |
| 4 | **Educational** | Clear explanations, useful examples, scaffolded | <7 |
| 5 | **Language** | Ukrainian quality (natural, no Russianisms) AND English quality (B1-readable, warm) | <8 |
| 6 | **Pedagogy** | PPP (A1/A2) or metalanguage bridge (B1.0) appropriate, scaffolded correctly | <7 |
| 7 | **L1/L2 Balance** | Ukrainian-to-English ratio matches level targets (graduated) | <6 |
| 8 | **Activities** | Correctness, minimal but accurate, schema-valid | <7 |
| 9 | **Richness** | Cultural hooks, visual aids, memorable moments | <6 |
| 10 | **Beginner Safety** | Emotional beats, encouragement, "Would I Continue?" | <7 |
| 11 | **LLM Fingerprint** | Authentic tutor voice vs AI patterns/cliches | <7 |
| 12 | **Linguistic Accuracy** | State Standard compliance, grammar correctness, IPA accuracy | <9 |

### Scoring Rules

- **9-10**: Excellent, no issues found in this dimension
- **7-8**: Good, minor issues found
- **5-6**: Needs work, multiple issues
- **<5**: Serious problems, major rewrite needed

**IMPORTANT:** Scores must reflect what you actually found during deep review.

### Lesson Quality Rubric (Tier 1)

| Score | Description |
|-------|-------------|
| 10 | Exceptional — feels like a caring tutor |
| 9 | Excellent — encouraging throughout |
| 8 | Good — solid but could be warmer |
| 7 | Adequate — functional but cold |
| 6 | Weak — feels like a textbook |
| ≤5 | Poor — discouraging or overwhelming |

### Overall Score

```
Overall = (Lesson_Quality × 1.5 + Coherence × 1.0 + Relevance × 1.0 + Educational × 1.2 +
          Language × 1.1 + Pedagogy × 1.2 + L1L2_Balance × 1.0 + Activities × 1.3 +
          Richness × 0.9 + Beginner_Safety × 1.3 + LLM × 1.0 + Linguistic_Accuracy × 1.5) / 14.0
```

**Pass threshold: 8.5+ overall, no dimension below its auto-fail threshold**

---

## STEP 7: WRITE REPORT

### Save Location
```
curriculum/l2-uk-en/{level}/review/{slug}-review.md
```

### Report Format

```markdown
# Review: {Module Title}

**Level:** {level} | **Module:** {num}
**Overall Score:** {X.X}/10
**Status:** PASS / FAIL
**Reviewed:** {date}
**Review Prompt:** review-content-core-a v1.0

## Scores Breakdown

| Dimension | Score | Notes |
|-----------|-------|-------|
| Lesson Quality | X/10 | {what you found} |
| Coherence | X/10 | {what you found} |
| Relevance | X/10 | {what you found} |
| Educational | X/10 | {what you found} |
| Language | X/10 | {what you found} |
| Pedagogy | X/10 | {what you found} |
| L1/L2 Balance | X/10 | {actual ratio vs target} |
| Activities | X/10 | {what you found} |
| Richness | X/10 | {what you found} |
| Beginner Safety | X/10 | {"Would I Continue?" result} |
| LLM Fingerprint | X/10 | {what you found} |
| Linguistic Accuracy | X/10 | {State Standard compliance} |

## L1/L2 Balance Analysis

- **Target immersion:** {X-Y%} Ukrainian
- **Actual immersion:** ~{Z%} Ukrainian
- **Assessment:** {on target / too much English / too much Ukrainian}

## IPA Verification

- Transcriptions checked: {X}
- Errors found: {X}
- All corrected: {yes/no}

## State Standard Check

- Grammar point: {description}
- Standard reference: §{X.X.X}
- Compliance: {compliant / violation found}

## Beginner Safety Audit

"Would I Continue?" Test:
- Overwhelmed? {Pass/Fail}
- Instructions clear? {Pass/Fail}
- Quick wins? {Pass/Fail}
- Ukrainian scary? {Pass/Fail}
- Come back tomorrow? {Pass/Fail}
- **Result:** {X}/5

Emotional beats found: {count}
- Welcome: {yes/no}
- Curiosity: {yes/no}
- Quick wins: {count}
- Encouragement: {count}
- Progress marker: {yes/no}

## Issues Found and Fixed

### Issue 1: {Category}
**Location:** Line X / Activity Y, Item Z
**Original:** {text}
**Problem:** {why it's wrong}
**Fix:** {what you changed}
**Status:** Fixed / Manual

{Repeat for each issue}

## Verification Summary

- Lines read: {X}
- Activity items checked: {X}
- Ukrainian sentences verified: {X}
- English sentences verified: {X}
- IPA transcriptions verified: {X}
- Issues found: {X}
- Issues fixed: {X}

## Recommendation

{PASS / FAIL} — {brief explanation linking to specific findings}
```

---

## STEP 7.5: SET NATURALNESS SCORE IN META

After completing your deep review, update the meta file:

```yaml
naturalness:
  score: {your_score}    # 1-10 based on Language dimension
  status: PASS           # PASS if score >= 8, FAIL if < 8
```

This unblocks the audit's naturalness gate.

---

## STEP 8: RUN AUDIT

After fixes, verify the module still passes technical audit:

```bash
scripts/audit_module.sh curriculum/l2-uk-en/{level}/{slug}.md
```

---

## Usage

```
/review-content-core-a [LEVEL] [NUM]        # Single module (recommended)
/review-content-core-a [LEVEL]              # All modules in level
/review-content-core-a [LEVEL] [START-END]  # Range
```

### Module Slug Lookup

1. Read `curriculum/l2-uk-en/curriculum.yaml`
2. Find level section
3. Module N = index N-1 in modules list

---

## Tier-Specific Guidance

**All Core A modules use:**
- `claude_extensions/commands/review-tiers/tier-1-beginner.md`

This includes the "Would I Continue?" test, emotional safety mapping, pacing checks, and beginner-specific quality markers.

---

## How This Differs from review-content-v4

| Aspect | Core A (this prompt) | v4 (Core B / Seminar) |
|--------|---------------------|----------------------|
| **Dimensions** | 12 (no Propaganda, no Semantic Nuance) | 14 (all dimensions) |
| **Added: L1/L2 Balance** | Checks graduated immersion ratio | "Immersion" (binary) |
| **Added: Beginner Safety** | "Would I Continue?" + emotional beats | Not present |
| **Added: IPA Verification** | Every transcription checked | Vocabulary IPA only |
| **Added: State Standard** | Grammar compliance §reference | Added (grammar modules) |
| **Dropped: Propaganda Filter** | Not relevant at A1-A2 | Required for HIST/BIO |
| **Dropped: Semantic Nuance** | Not relevant at beginner level | Required at C1+ |
| **LLM Fingerprint** | Lenient (tutor voice patterns OK) | Strict detection |
| **Activity focus** | Correctness over quantity | Correctness + density |
| **Tier reference** | tier-1-beginner.md | tier-2/3/4 per level |

---

## Persona

> Embody the Ukrainian linguist & teacher. See `claude_extensions/skills/_shared/persona.md`

**IPA RULE:** All phonetics MUST use IPA (no Latin transliteration).
**PYTHON:** Use `.venv/bin/python` only.
**WORKFLOW:** This is for manual review AFTER audit_module.py passes.
