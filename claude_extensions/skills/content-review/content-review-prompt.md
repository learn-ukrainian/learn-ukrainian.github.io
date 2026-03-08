# Content Quality Review Prompt (Claude + RAG)

You are reviewing a BUILT Ukrainian language course module. The module has already passed pipeline audit gates (word count, activity count, VESUM coverage). Your job is to find quality issues the pipeline CANNOT catch: pedagogical quality, plan adherence, linguistic accuracy, content coherence, and engagement.

## Input

You will be given the module slug and track. Read these files:

1. **Content markdown** (`{track}/{slug}.md`) -- the main lesson content
2. **Activities YAML** (`{track}/activities/{slug}.yaml`) -- interactive exercises
3. **Plan YAML** (`plans/{track}/{slug}.yaml`) -- what SHOULD have been built
4. **Meta YAML** (`{track}/meta/{slug}.yaml`) -- build metadata
5. **Vocabulary YAML** (`{track}/vocabulary/{slug}.yaml`) -- if it exists

All paths relative to `curriculum/l2-uk-en/`.

## Track Detection

Same as plan-review: determine mode from track (core / history / biography / literary / oes-ruth). This affects which checks apply.

## Review-Tier Selection

Select the appropriate review tier based on level:

| Level | Tier | Reference |
|-------|------|-----------|
| A1, A2 | Tier 1 (Beginner) | See `../plan-review/review-tiers/tier-1-beginner.md` |
| B1, B2 | Tier 2 (Core) | See `../plan-review/review-tiers/tier-2-core.md` |
| HIST, BIO, ISTORIO, LIT, OES, RUTH | Tier 3 (Seminar) | See `../plan-review/review-tiers/tier-3-seminar.md` |
| C1, C2 | Tier 4 (Advanced) | See `../plan-review/review-tiers/tier-4-advanced.md` |

Read the tier file and apply its rubrics alongside the checks below.

---

## Checks (ALL tracks)

### 1. PLAN ADHERENCE

Compare the built content against the plan YAML:

- [ ] **Objectives covered** -- Every plan objective addressed by the content. List each objective and note which section covers it. Flag missing objectives as **CRITICAL**.
- [ ] **Vocabulary present** -- Every `vocabulary_hints.required` word appears in the markdown prose AND in the vocabulary YAML (if it exists). Flag missing required words as **HIGH**.
- [ ] **Content outline followed** -- Each plan section's `points` are addressed in the corresponding content section. Flag skipped points as **MEDIUM**.
- [ ] **Section structure matches** -- Content sections align with plan's `content_outline` sections. Flag missing/extra sections as **MEDIUM**.
- [ ] **Cultural hooks present** -- Any cultural hooks mentioned in the plan appear in the content. Flag missing hooks as **LOW**.

### 2. LINGUISTIC ACCURACY (use RAG tools)

- [ ] **Russianisms scan** -- Read through all Ukrainian text in the module. Flag any Russian-specific vocabulary or grammar. Use `mcp__rag__verify_word` for suspicious words and `mcp__rag__query_r2u` for words that might have Ukrainian alternatives.
- [ ] **Grammar correctness** -- Check case endings, verb conjugations, gender agreement in Ukrainian examples. Use `mcp__rag__query_ulif` for morphological verification when in doubt.
- [ ] **Ghost word check** -- Verify any Ukrainian word you haven't seen before with `mcp__rag__verify_word`. Focus on words in example sentences, vocabulary tables, and activities.
- [ ] **Stress marks** -- If the module uses stress marks, verify they're on the correct syllable. Use `mcp__rag__query_grac` (mode: concordance) to check stress patterns.
- [ ] **False friend claims** -- If the module claims a word is a "false friend" or Russicism, verify the claim. False Russicism claims are **HIGH** severity.

### 3. PEDAGOGICAL QUALITY

Apply the appropriate tier rubric, then also check:

- [ ] **Lesson arc** -- Does the module follow a natural progression? (intro -> present -> practice -> consolidate -> summarize)
- [ ] **Cognitive load** -- Are new concepts introduced at an appropriate pace? Too many new words/concepts per section?
- [ ] **Examples before rules** -- Good pedagogy shows examples first, then derives rules. Flag "rule first, examples later" as **LOW**.
- [ ] **Practice opportunities** -- Sufficient practice after each new concept? Flag long stretches of exposition without practice as **MEDIUM**.
- [ ] **Warmth and encouragement** (A1/A2 especially) -- Feels like a supportive tutor, not a textbook? Apply tier-1 emotional safety mapping for beginners.

### 4. ACTIVITIES QUALITY

Read the activities YAML and check:

- [ ] **Schema compliance** -- Each activity matches its type's schema. Check required fields (type, title, items/pairs, correct answers). Read `docs/ACTIVITY-YAML-REFERENCE.md` for schema details if needed.
- [ ] **Language testing, not content testing** -- Can the learner answer without reading the Ukrainian text? If YES, the activity tests content recall, not language. Flag as **HIGH** (Rule 10a). Exempt: ZNO-format activities.
- [ ] **Correct answers are correct** -- Verify that marked correct answers are actually correct Ukrainian. Use `mcp__rag__verify_word` for any suspicious answer.
- [ ] **Distractors are plausible** -- Wrong answers should be plausible but clearly wrong. Not absurd, not trick questions.
- [ ] **Variety** -- Check activity type distribution. Flag if >50% are the same type as **LOW**.
- [ ] **Decodability** (Cyrillic modules only) -- Activity items use only letters from the cumulative charset.

### 5. ENGAGEMENT & FORMATTING

- [ ] **Engagement boxes** -- Count callout boxes (> [!cultural], > [!myth-buster], > [!tip], > [!warning], etc.). Minimum: A1/A2 = 3+, B1/B2 = 6+, C1+ = 7+. Flag as **MEDIUM** if under.
- [ ] **Tables** -- Grammar explanations should use tables, not prose. Flag prose-only grammar as **LOW**.
- [ ] **Wall of text** -- Flag any section >300 words without a table, list, callout box, or heading break as **MEDIUM**.
- [ ] **Videos embedded** -- If the plan references pronunciation videos, are they embedded as markdown links in the content? Flag missing embeds as **MEDIUM**.

### 6. LLM FINGERPRINT

- [ ] **Generic AI openings** -- Flag "In this lesson, we will explore..." or "It is important to note..." patterns. These should be rewritten to conversational tone.
- [ ] **Repetitive transitions** -- Flag if multiple sections start with the same pattern (e.g., "Now let's look at...").
- [ ] **Word salad** -- Flag sentences that randomly mix Ukrainian and English within the same clause or string unrelated ideas together.

---

## Mode-Specific Checks

### CORE MODE (A1-C2)

- [ ] **Immersion ratio appropriate** -- Estimate Ukrainian vs English word ratio. Compare against tier targets (A1.1: 20-40%, A2: 50-75%, B1+: 75%+).
- [ ] **Grammar accuracy** -- Verify grammar explanations against textbooks using `mcp__rag__search_text`. Flag incorrect rules as **CRITICAL**.

### HISTORY/BIO/ISTORIO MODE

- [ ] **Factual accuracy** -- Spot-check 3-5 factual claims using `mcp__rag__query_wikipedia`. Flag errors as **HIGH**.
- [ ] **Decolonization stance** -- Ukrainian agency centered, not passive objects of Russian/Soviet history. Flag imperial framing as **HIGH**.
- [ ] **Analytical, not encyclopedic** -- Content drives analysis and critical thinking, not just narrates facts. Flag purely descriptive sections as **MEDIUM**.

### LITERARY MODE (LIT, LIT-*)

- [ ] **Textual evidence** -- Literary analysis cites specific passages, not vague generalizations. Flag unsupported claims as **MEDIUM**.
- [ ] **Author/work accuracy** -- Verify key claims about literary works using `mcp__rag__search_literary` or `mcp__rag__query_wikipedia`.

### OES/RUTH MODE

- [ ] **Primary source accuracy** -- Verify text dating, genre, linguistic features using `mcp__rag__search_literary` with period filter.
- [ ] **Not anachronistic** -- No modern features projected onto historical texts.

---

## Output Format

```markdown
# Content Review: {slug}

**Track:** {track} | **Sequence:** {sequence}
**Mode:** core / history / biography / literary / oes-ruth
**Tier:** 1-beginner / 2-core / 3-seminar / 4-advanced
**Pipeline:** PASS (words: X, target: Y)
**Verdict:** A / B / C / F

## Plan Adherence
| Objective | Covered? | Section | Notes |
|-----------|----------|---------|-------|
| ... | YES/NO | ... | ... |

### Vocabulary Coverage
| Required Word | In Prose? | In Vocab YAML? | In Activities? |
|--------------|-----------|----------------|----------------|
| ... | YES/NO | YES/NO | YES/NO |

## Linguistic Accuracy
| Issue | Severity | Location | Details |
|-------|----------|----------|---------|
| ... | CRITICAL/HIGH/MEDIUM/LOW | Section X, line Y | ... |

## Pedagogical Quality
**Lesson Quality Score:** X/10
**Tier Rubric Results:** [from tier file]

## Activities Quality
| Activity | Type | Issues |
|----------|------|--------|
| ... | ... | ... |

## Engagement
| Metric | Count | Minimum | Status |
|--------|-------|---------|--------|
| Callout boxes | X | Y | PASS/FAIL |
| Tables | X | -- | -- |
| Videos embedded | X/Y | -- | PASS/FAIL |

## Issues Found

### CRITICAL (blocks deployment)
1. ...

### HIGH (should fix before deployment)
1. ...

### MEDIUM (fix if possible)
1. ...

### LOW (informational)
1. ...

## Grade Justification

[1-3 sentences explaining the overall grade]
```

### Grading Scale

| Grade | Meaning | Action |
|-------|---------|--------|
| **A** | Excellent -- ready for deployment | No fixes needed |
| **B** | Good -- minor issues only | Optional polish |
| **C** | Adequate -- has issues that should be fixed | Fix HIGH issues, rebuild if needed |
| **F** | Fails -- CRITICAL issues found | Must fix and rebuild |

**Auto-fail triggers (immediate F):**
- Any CRITICAL issue
- Missing >2 plan objectives
- >3 Russianisms or ghost words
- Lesson Quality Score <= 5
