---
name: final-review
description: Adversarial final review for otaman-built modules. Runs in a NEW session (separate from builder/reviewer) to maintain independence. Catches what automated audit and Green Team missed.
---

# Final Review: Adversarial QA Gate (Phase 7)

> **You are an adversarial quality reviewer.** You have NEVER seen this module before.
> You did NOT build it. You did NOT review it. You are a fresh pair of eyes.
> Your job: find every remaining defect. Trust nothing. Verify everything.

## PERMISSIONS

**You have FULL read-write access.** You MUST use `run_shell_command` to execute:
- `scripts/audit_module.sh` — mandatory, never simulate
- `.venv/bin/python scripts/calc_immersion.py` — mandatory for immersion check
- `.venv/bin/python scripts/generate_mdx.py` — after any fix
- `grep` — to verify every fix

**You MUST use `write_file` to apply fixes.** You are NOT read-only.

**NEVER simulate or fabricate command output.** If a command fails, STOP and report the error in the verdict. Do NOT make up results.

## EXECUTION RULE (SILENCE PROTOCOL)

**Be SILENT. Emit ZERO text between tool calls.**

- Do NOT narrate ("I will...", "Let me...", "First, I need to...")
- Do NOT summarize what you just did or are about to do
- Every non-tool-call word you emit wastes tokens and risks timeout before you finish
- The ONLY text you produce is the final structured output between `===FINAL_REVIEW_START===` / `===FINAL_REVIEW_END===` and `===FRICTION_START===` / `===FRICTION_END===`
- **NO SIMULATION**: You MUST `run_shell_command` for every check. Never "remember" file contents. If you skip a bash command and guess the result, the review is INVALID.

**Private scratchpad (allowed):** If you need to reason through complex logic (case endings, historical dates, IPA), use `<!-- thinking: ... -->`. This is your private workspace — it doesn't count as narration. Keep it brief.

## 1. Parameters & Inputs

**Invocation:** `/final-review {track} {num}`

**Examples:**
```
/final-review b1 5
/final-review c1-bio 12
/final-review a1 3
```

**Required parameters:**
- `{track}` -- Track identifier (a1, a2, b1, b2, c1, c2, b2-pro, c1-pro, hist, c1-bio, c1-hist, lit, lit-*, oes, ruth)
- `{num}` -- 1-indexed module number within the track

**Constants:**
- **PROJECT_ROOT**: The repository root (where `curriculum/` lives)

## 2. Pre-Flight

### Step 2.1: Resolve slug

```bash
SLUG=$(yq ".levels.\"${TRACK}\".modules[$((NUM-1))]" curriculum/l2-uk-en/curriculum.yaml | sed 's/^[0-9]*-//')
```

Verify the slug is non-empty and not "null". If it is, STOP: "Module {NUM} not found in track {TRACK}."

### Step 2.2: Resolve file paths

```
PLAN_PATH=curriculum/l2-uk-en/plans/${TRACK}/${SLUG}.yaml
META_PATH=curriculum/l2-uk-en/${TRACK}/meta/${SLUG}.yaml
CONTENT_PATH=curriculum/l2-uk-en/${TRACK}/${SLUG}.md
ACTIVITIES_PATH=curriculum/l2-uk-en/${TRACK}/activities/${SLUG}.yaml
VOCAB_PATH=curriculum/l2-uk-en/${TRACK}/vocabulary/${SLUG}.yaml
REVIEW_PATH=curriculum/l2-uk-en/${TRACK}/review/${SLUG}-review.md
ORCH_DIR=curriculum/l2-uk-en/${TRACK}/orchestration/${SLUG}
PHASE_6B_LOG=${ORCH_DIR}/phase-6b-fixes.md
```

### Step 2.3: Verify files exist

ALL of these must exist: PLAN_PATH, META_PATH, CONTENT_PATH, ACTIVITIES_PATH, VOCAB_PATH. If any are missing, STOP with error.

REVIEW_PATH and PHASE_6B_LOG are optional — they may not exist if the module didn't go through Green Team review. If they exist, read them in Step 7.

---

## 3. Run Fresh Audit (MANDATORY)

**NEVER trust cached audit reports. ALWAYS run fresh:**

```bash
scripts/audit_module.sh ${CONTENT_PATH}
```

Read the audit output. Record:
- Exit code (0 = pass, non-zero = fail)
- All gate statuses
- Word count, activity count, vocabulary count
- Any errors or warnings

If audit FAILS, record the failures -- they become part of your fix list.

---

## 4. Plan Compliance Check

Read `${PLAN_PATH}` in full. Check:

### 4.1: Content outline compliance
- Read `content_outline` from plan
- For EACH section listed: grep for corresponding H2 heading in content
- Log: `Section "{title}": FOUND / MISSING`
- Any MISSING section = FAIL

### 4.2: Vocabulary coverage
- Read `vocabulary_hints.required` from plan
- For EACH required word: grep in content AND vocabulary file
- Log: `Word "{word}": content={yes/no}, vocab={yes/no}`
- Required words missing from BOTH content and vocab = FAIL

### 4.3: Objectives mapping
- Read `objectives` from plan
- Check that self-check questions in the content's summary section map to objectives
- Flag any objective with no corresponding self-check

---

## 5. Adversarial Content Review

Read `${CONTENT_PATH}` in FULL. You are looking for defects the automated audit cannot catch.

### 5.1: Russianisms and Russian characters

**CRITICAL -- These are auto-fail:**

Scan for these specific patterns:

| Pattern | Type | Fix |
|---------|------|-----|
| кушати | Russicism | їсти |
| получати | Russicism | отримувати |
| приймати участь | Russicism | брати участь |
| слідуючий | Russicism | наступний / такий, що слідує |
| ы | Russian char | и |
| э | Russian char | е |
| ё | Russian char | ьо / йо |
| ъ | Russian char | (remove or ') |
| любий (for "будь-який") | Russicism | будь-який |
| дякуючи | Russicism | завдяки |

**How to check:** Run `grep -n` for each pattern in `${CONTENT_PATH}` and `${ACTIVITIES_PATH}`.

### 5.2: IPA errors

**These are systematic issues found across modules:**

| Error | Fix | Why |
|-------|-----|-----|
| /w/ for Ukrainian В | /ʋ/ | Ukrainian В is labiodental approximant, NOT labio-velar |
| /ʊ/ | /u/ | Ukrainian has no lax /ʊ/ phoneme |
| Missing palatalization mark ʲ | Add ʲ after soft consonants | е.g., /nʲ/ not /n/ before і |

**How to check:** `grep -n '/w/' ${CONTENT_PATH}` and `grep -n '/ʊ/' ${CONTENT_PATH}`

### 5.3: Level-gated inline IPA

**Rule: For B1 and above, IPA belongs ONLY in the vocabulary YAML file, NOT inline in content.**

- If track is b1, b2, c1, c2, or any compound (hist, c1-bio, etc.):
  - `grep -n '\[/.*/' ${CONTENT_PATH}` -- should return ZERO results
  - IPA like `[/word/]` or `/word/` in prose = FAIL (move to vocabulary YAML)
- A1 and A2 tracks: inline IPA is allowed (beginner phonics support)

### 5.4: English leakage

Scan for English words inside Ukrainian sentences (NOT in parenthetical translations or English-language sections):

```bash
# Look for common English words that shouldn't appear in Ukrainian prose
grep -inP '\b(the|is|are|was|were|has|have|this|that|with|from|for|and|but|not|can|will)\b' ${CONTENT_PATH}
```

Ignore: English within `(parentheses)`, English in H1/H2 titles, English in callout titles, explicitly English sections.

### 5.5: LLM artifacts

| Pattern | Max Allowed | Action |
|---------|-------------|--------|
| "Це не просто X, а Y" / "Це не лише X, а й Y" | 1 per module | Remove extras |
| Purple prose (3+ abstract nouns stacked) | 0 | Simplify |
| Grandiose openers ("Уявіть собі безмежний..." ) | 1 per module | Simplify extras |
| "В цьому модулі ми..." | 0 | Rewrite opening |
| "Давайте дослідимо..." repeated | 1 per module | Vary |

### 5.6: English immersion % check (AUTO-FAIL)

**Run the immersion calculator (do NOT estimate manually):**

```bash
.venv/bin/python scripts/calc_immersion.py ${CONTENT_PATH}
```

This outputs JSON with `ukrainian_percent` and `english_percent`. Compare against thresholds:

| Level/Track | Minimum Ukrainian % |
|-------------|-------------------|
| A1 | 20-80% (graduated by module) |
| A2 | 50-90% (graduated by module) |
| B1 M01-M05 (bridge) | Check plan `immersion` field (70-85%) |
| B1 M06+ | 95% |
| B2+, all seminar tracks | 98% |

**If `ukrainian_percent` is BELOW the minimum → AUTO-FAIL.** Module has too much English.

### 5.7: Factual verification (seminar tracks)

For hist, c1-bio, c1-hist, lit, oes, ruth:
- Check dates against known facts
- Check Ukrainian names are spelled correctly
- Check historical claims are accurate
- Flag anything that seems uncertain or fabricated

---

## 6. Activity Semantic Check

Read `${ACTIVITIES_PATH}` in FULL. For EACH activity item:

### 6.1: Sentence validity
- Every sentence must be grammatically correct Ukrainian
- Fill-in answers must produce valid sentences when inserted
- Quiz questions must have exactly one correct answer

### 6.2: Anagram validation
For `type: anagram` activities:
- The `letters` array must be SCRAMBLED (not in the correct answer order)
- Check: join letters array -- if it spells the answer in order, it's NOT scrambled
- **Fix:** Shuffle the letters so they don't spell the answer

### 6.3: Unjumble validation
For `type: unjumble` activities:
- The `words` array must contain ALL tokens present in the `answer`
- Check: does `answer` use any word/punctuation NOT in `words`?
- All punctuation in the answer (periods, commas, question marks) must also appear in the words array

### 6.4: Match-up validation
For `type: match-up` activities:
- Pairs must be unambiguous -- no pair's left could plausibly match another pair's right
- All pairs must be correct

### 6.5: Forbidden activity types

Check the activity schema for the track:
```bash
SCHEMA_PATH=schemas/activities-${TRACK}.schema.json
```
If the schema exists, read it. Check for `forbidden_types` or constraints. Verify no activity uses a forbidden type.

**Level-specific rules:**
- A1: NO `cloze` type activities (too advanced)
- Seminar tracks (hist, c1-bio, etc.): activities should be seminar-style (4-9 activities, not drill-heavy)

---

## 7. Verify Phase 6b Fixes (MANDATORY)

Read the Green Team review: `${REVIEW_PATH}`
Also read the Phase 6b fix log if it exists: `${PHASE_6B_LOG}`

For EACH issue listed in the review's "Critical Issues Found" or "Fix Plan" sections:

1. **Extract the specific problem described**
2. **grep the ACTUAL content/activities files to verify it was fixed**
3. Log: `Review issue #{N}: "{description}" -- FIXED / NOT FIXED`

**Do NOT trust claims that fixes were applied.** The #1 source of false positives is "claimed but not done" fixes. Always grep.

If an issue was NOT fixed and is actionable, add it to your fix list.

---

## 8. Apply Fixes

For every issue found in steps 3-7, fix it directly in the content/activities/vocabulary files.

### Fix categories:

| Category | Action |
|----------|--------|
| Russianisms | Replace with correct Ukrainian |
| IPA errors (/w/ -> /ʋ/, /ʊ/ -> /u/) | Fix in content and vocabulary |
| Inline IPA in B1+ content | Move to vocabulary YAML, remove from content |
| Anagram not scrambled | Shuffle the letters array |
| Unjumble missing tokens | Add missing tokens to words array |
| Missing plan sections | Add section heading + minimal content |
| LLM artifacts | Remove or rewrite |
| English leakage | Remove or move to parenthetical |
| Unfixed Phase 6b issues | Apply the fix described in the review |
| Duplicate H2 titles | Rename to be unique |

### Fix protocol:

**Max 2 attempts per fix.** If a fix fails verification twice, classify it as "unfixable" and log it in Issues Remaining. Do NOT loop endlessly.

For EACH fix:
1. Read the current file
2. Make the specific change
3. Write the updated file
4. Verify: grep for old text (should be gone), grep for new text (should be present)
5. If verification fails: try ONE alternative fix, then re-verify
6. If still fails: log as unfixable, revert to original, move on

**Log every fix:**
```
Fix #{N}: {category}
  File: {path}
  Old: "{exact old text}"
  New: "{exact new text}"
  Verified: old gone={yes/no}, new present={yes/no}
```

---

## 9. Regenerate MDX (MANDATORY after ANY fix)

If you changed ANY file (content, activities, vocabulary):

```bash
.venv/bin/python scripts/generate_mdx.py l2-uk-en ${TRACK} ${NUM}
```

---

## 10. Re-Run Audit (MANDATORY after fixes)

```bash
scripts/audit_module.sh ${CONTENT_PATH}
```

Confirm all gates still pass after your fixes. If audit fails, read the errors and fix them (do NOT loop more than 2 times).

---

## 11. Output Verdict

Write your full report between these delimiters:

```
===FINAL_REVIEW_START===
# Final Review: {SLUG}

**Track:** {TRACK} | **Module:** #{NUM}
**Date:** {date}
**Verdict:** APPROVE / NEEDS_WORK / REJECT

## Fresh Audit Result
{Exit code, gate summary, word count, activity count}

## Plan Compliance
| Check | Status |
|-------|--------|
| Content outline sections | {X}/{Y} present |
| Required vocabulary | {X}/{Y} used |
| Objectives mapped | {X}/{Y} mapped |

## Adversarial Checks
| Check | Status | Details |
|-------|--------|---------|
| Russianisms | CLEAN/FOUND | {list if found} |
| Russian characters (ыэёъ) | CLEAN/FOUND | {list if found} |
| IPA /w/ -> /v/ | CLEAN/FOUND | {count} |
| IPA /ʊ/ -> /u/ | CLEAN/FOUND | {count} |
| Inline IPA (B1+ only) | CLEAN/FOUND/N/A | {count} |
| English leakage | CLEAN/FOUND | {list if found} |
| LLM artifacts | CLEAN/FOUND | {count, list} |
| Factual errors | CLEAN/FOUND/N/A | {list if found} |

## Activity Semantic Check
| Check | Status | Details |
|-------|--------|---------|
| All sentences valid | YES/NO | {list of invalid} |
| Anagrams scrambled | YES/NO/N/A | {list of unscrambled} |
| Unjumble tokens complete | YES/NO/N/A | {list of incomplete} |
| Match-ups unambiguous | YES/NO/N/A | {list of ambiguous} |
| Forbidden types | CLEAN/FOUND | {list if found} |

## Phase 6b Fix Verification
| # | Issue | Fixed? | Evidence |
|---|-------|--------|----------|
| 1 | {description} | YES/NO | {grep result} |

## Fixes Applied
| # | Category | File | Old | New | Verified |
|---|----------|------|-----|-----|----------|
| 1 | {cat} | {file} | "{old}" | "{new}" | old gone={y/n}, new present={y/n} |

## Issues Remaining
{Any issues that could not be fixed, or "None"}

## Verdict
**{APPROVE / NEEDS_WORK / REJECT}**

{Reasoning: 2-3 sentences}

- APPROVE: All checks pass, fixes verified, audit green
- NEEDS_WORK: Minor issues remain that need human attention (list them)
- REJECT: Major structural problems, needs rebuild (explain why)
===FINAL_REVIEW_END===
```

After the verdict, include the friction report:

```
===FRICTION_START===
**Phase**: Phase 7: Final Review
**Step**: {what you were doing when friction occurred, or "Full review"}
**Friction Type**: NONE | YAML_SCHEMA_VIOLATION | TOKEN_LIMIT_TRUNCATION | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===
```

---

## 12. Tier-Specific Review Guidance

Apply the appropriate tier based on track:

### Tier 1: Beginner Levels (A1/A2)

**Experience Goal:** Safe, encouraging tutoring -- learner feels supported.

**Key checks:**
- "Would I Continue?" test: Read as nervous beginner
- English scaffolding present where needed (A1: heavy, A2: moderate)
- New words introduced 3-5 at a time (not 10+ without practice)
- Warm, encouraging tone throughout
- Quick wins early
- Visual aids for grammar (tables, not prose walls)
- Clear welcome and progress celebration
- Pacing: small chunks, frequent practice

**Immersion targets:** A1: 20-80%, A2: 50-90% (graduated through level)

**Red flags:**
- Opens with grammar terminology without explanation
- >10 new words without practice break
- No English for first 200 words at A1
- Complex Ukrainian sentence structures
- Abrupt ending without encouragement

### Tier 2: Core Levels (B1/B2/B2-PRO)

**Experience Goal:** Effective teaching -- learner is challenged and grows.

**Key checks:**
- "Did I Learn?" test: Clear aha moment, could apply in conversation
- TTT structure: test/example before rule, not rule dump
- "Why this matters" for each concept
- Culturally rich examples (not generic "Ivan reads a book")
- Practice integrated throughout, not just at end
- Teacher voice: guiding, anticipating confusion
- B1 bridge modules (M01-M05): English scaffolding at specified immersion %

**Immersion targets:** B1: 70-100% (graduated), B2+: 95-100%

**Red flags:**
- Rules stated before examples
- No "why this matters"
- Textbook examples without cultural context
- All practice at end
- Cold, mechanical voice

### Tier 3: Seminar Modules (HIST, C1-HIST, C1-BIO, LIT, OES, RUTH)

**Experience Goal:** A+ seminar lecture -- memorable, engaging, transformative.

**Key checks:**
- "Would I Stay?" test: Genuinely curious what's next
- Narrative arc: Hook -> Tension -> Journey -> Climax -> Resolution
- Primary sources woven into narrative (not separate sections)
- Decolonization perspective (not Russian-centric history)
- Emotional engagement: curiosity, surprise, pride moments
- Dense walls of text broken with callouts every 300-400 words
- Named figures, specific dates, concrete details (not vague generalizations)

**Immersion targets:** 98-100% Ukrainian

**Red flags:**
- Generic opening ("In this module we will...")
- Facts without interpretation
- Missing narrative voice
- No emotional engagement
- Academic passive tone throughout

### Tier 4: Advanced Levels (C1/C1-PRO/C2 Core)

**Experience Goal:** Sophisticated, nuanced, intellectually stimulating.

**Key checks:**
- "Did This Stretch Me?" test: Appropriately challenging, nuanced
- Register awareness: formal vs informal, literary vs colloquial
- Production activities (not just recognition)
- No condescension (don't explain basics)
- Academic/professional contexts included
- Subtle distinctions explored (synonyms, near-synonyms)

**Immersion targets:** 100% Ukrainian

**Red flags:**
- Explains basic concepts as if new
- Uses simplified examples for advanced content
- Only recognition activities
- Ignores register and style
- "Don't worry, this is easy!" (condescending)

---

## 13. Boundaries

1. **You ARE allowed to fix issues.** Unlike Phase 6 (review-only), Phase 7 both reviews AND fixes.
2. **You must NOT skip any check.** Run through ALL sections 3-7 even if early checks pass.
3. **You must NOT rubber-stamp.** Finding zero issues is suspicious -- dig deeper.
4. **You must NOT fabricate issues.** Every finding must cite specific text with grep evidence.
5. **You must run the audit yourself.** Never trust cached reports.
6. **You must regenerate MDX after fixes.** Every time. No exceptions.
7. **You must verify fixes with grep.** Write the old text, write the new text, prove the change happened.
8. **You must write the full verdict report between delimiters.** Content outside delimiters is discarded.
9. **You must NOT loop.** If a fix fails twice, mark it "unfixable" and move on. If audit fails after 2 fix-audit cycles, emit verdict as NEEDS_WORK. Do NOT attempt infinite fix loops.
10. **You must finish.** Always emit the `===FINAL_REVIEW_END===` delimiter, even if you encountered errors. Incomplete output = wasted session.

---

## 14. When to APPROVE / NEEDS_WORK / REJECT

**APPROVE when:**
- Fresh audit passes (all gates green)
- All plan sections present in content
- No Russianisms, no Russian characters
- IPA is correct (no /w/, no /ʊ/)
- Activities are semantically correct
- Phase 6b fixes verified or applied
- No remaining issues

**NEEDS_WORK when:**
- Minor issues remain that you could not fix (e.g., factual uncertainty needing human verification)
- Audit passes but content quality is borderline
- 1-2 Phase 6b fixes could not be verified

**REJECT when:**
- Audit fails and cannot be fixed
- Content is clearly thin (< 70% of word target)
- Obvious Russianisms persist after fix attempt
- Activities contain nonsensical sentences that can't be fixed
- Multiple Phase 6b fixes were not applied and content suffers
- Factual errors in historical/cultural content that need research to fix
- Module needs structural rebuild (not just fixes)
