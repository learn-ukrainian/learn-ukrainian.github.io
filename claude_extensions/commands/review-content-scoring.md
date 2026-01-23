# Review-Content-Scoring Prompt: 0-10 Quality Rubric (Post-Audit)

**MANDATE:** Evaluate module for educational quality, coherence, soundness. Immediately fix to 10/10 scores.

**IPA RULE:** All phonetics MUST use IPA (no Latin transliteration). IPA is sole standard.

**PYTHON ONLY:** Use `.venv/bin/python` (never `python3`).

**CRITICAL WORKFLOW NOTE:** This is for **manual quality review AFTER audit_module.py passes**. audit_module.py validates structure (word counts, activity counts, richness metrics, immersion %). This focuses on pedagogical quality.

**Skill Metadata:**

```yaml
---
name: review-content-scoring
description: 0-10 scoring rubric for content quality review after audit passes
version: '2.0'
category: quality
dependencies: audit_module.py
---
```

## Critical Sections Index (DO NOT SKIP)

1. Template Compliance (auto-fail if violated)
2. Activity Quality (auto-fail for structure/wrong answers)
3. Richness Red Flags (auto-fail for AI slop)
4. Red Flags (multiple auto-fails)
5. Content Richness (B1+ critical)
6. Humanity & Flow Audit
7. Dryness Flags (rewrite if 2+)
8. Human Warmth Checklist (<2 markers = fail)
9. LLM Fingerprint Detection (B1+ critical)

**CHECKPOINT:** Evaluate ALL 9 sections.

## Module Number to Slug Lookup

**CRITICAL:** Before reviewing, determine the exact module slug from the curriculum.yaml manifest.

1. **Locate Manifest:** `curriculum/l2-uk-en/curriculum.yaml`
2. **Find Level Section:** Look for the `[LEVEL]:` entry (e.g., `b2-hist:`)
3. **Get Slug by Index:** Modules are 1-indexed. For module number N, take the (N-1)th item in the `modules:` list.
4. **Example for B2-HIST Module 1:**
   ```
   b2-hist:
     type: track
     modules:
       - trypillian-civilization  # [1] Index 0
       - scythians-sarmatians     # [2] Index 1
   ```
   Module 1 = `trypillian-civilization`
5. **File Path:** `curriculum/l2-uk-en/{level}/{slug}.md`

**If number > module count:** Return error "Module {num} not found in {level} (max {count})".

## Usage

```
/review-content-scoring [LEVEL]              # Review all in level
/review-content-scoring [LEVEL] [MODULE_NUM] # Single module
/review-content-scoring [LEVEL] [START-END]  # Range
```

## Batch Mode (Multiple Modules)

Use subagents for each module (fresh context per module to avoid exhaustion).

## Single Module Mode

### Extract Content

- Lesson content: Everything before ## Activities (include summaries, examples, boxes; exclude activities/vocab sidecars)
- Metadata: Title, level, module num, topic

### Locate Activities (YAML-Mandatory)

**Logic:**

- Check for `activities/{slug}.yaml`.
- Scan Markdown for forbidden headers: ## quiz, ## match-up, etc.
- **Duplicate Activities:** YAML exists + headers exist → ⚠️ DUPLICATE (Safe fix: Remove inline, keep vocab)
- **Legacy:** Only headers → "Migrate to YAML" (blocking)
- **Correct:** Only YAML → ✅ Proceed
- **Missing:** Neither → ❌ Fail

**YAML Schema:** See docs/ACTIVITY-YAML-REFERENCE.md for 12+ types (quiz, match-up, etc.).

### Evaluate Quality

**Step 0: Template Compliance (Auto-fail if violated)**
Verify against level template (e.g., B1 uses b1-grammar-module-template.md).

- Sections match?
- Word count meets min (core prose)?
- Activity/vocab counts ok?
- Pedagogy matches?
- Focus-area (architect skill) met?
- Ukrainian validation: Словник.UA, Грінченка, Антоненко-Давидович (no Russisms/Surzhik/calques).

**Score each dimension 0-10 (see Scoring Philosophy below):**

1. **Coherence (0-10):** Logical flow, transitions, progressive difficulty, consistent terminology.
2. **Relevance (0-10):** Alignment with module goals, curriculum plan, level targets.
3. **Educational (0-10):** Clear explanations, useful examples, learning effectiveness.
4. **Language (0-10):** Ukrainian quality, absence of Russianisms/calques, euphony, naturalness.
5. **Pedagogy (0-10):** Teaching approach, scaffolding, level-appropriateness, TTT/CBI/PPP alignment.
6. **Immersion (0-10):** Ukrainian-to-English ratio, appropriate scaffolding for level.
7. **Activities (0-10):** Quality, density, variety, correct answers, format compliance.
8. **Richness (0-10):** Examples, engagement boxes, cultural references, proverbs, dialogues, visuals.
9. **Humanity (0-10):** Teacher voice, direct address, encouragement, warmth, real-world validation.
10. **LLM Fingerprint (0-10):** AI-generated patterns vs. authentic human writing.

**Activity Quality Sub-Checks (Critical for Dimension 7):**

- **Structural Integrity (Auto-fail):** No duplicates/mixed types/broken YAML. Item count matches level (MODULE-RICHNESS-GUIDELINES-v2.md).
- **Correctness + Naturalness (1-10 Scale):** Grammar/linguistic accuracy, Ukrainian authenticity.
  - 1-3: FAIL (English syntax, calques, formality)
  - 4-7: NEEDS FIXES (Stilted, pronoun overuse)
  - 8-10: PASS (Idiomatic, stylistic, cultural)
  - Level Gate: A1-A2 ≥5; B1+ ≥8.
  - Auto-fail: Wrong answer, multiple valid not accepted, Russisms, naturalness <8 for B1+.
- **Difficulty Calibration:** Tests taught material, activity type fits goal, clear instructions.
- **Distractor Quality:** Plausible but wrong, same word class.
- **Engagement:** Cultural relevance, interest.
- **Variety & Repetition:** Diverse patterns, no mechanical repetition.
- **External Resources:** Relevant, valid, level-appropriate.

**CEFR Quality Gates (ALL Levels):**

- Naturalness avg ≥5.0 (but B1+ ≥8.0)
- Difficulty inappropriate ≤0%
- Engagement avg ≥3.5
- Distractor quality avg ≥4.2
- Variety avg ≥65%

**Activity Red Flags (Auto-fail):**

- Structure: Duplicates, wrong format, < min items.
- Correctness: Wrong answer, multiple valid not accepted.
- Linguistic: Russisms, errors in correct answer.
- Difficulty: Untaught, wrong level.
- Distractors: Nonsense (1), spoiler hints.
- Naturalness: 1 for B2+.
- Variety: <40%.
- Resources: Broken URLs, irrelevant.

11. **Red Flags (Auto-fail):** Forced mixing, undefined terms, false friends, Russisms/Surzhik, inline activities.

12. **Content Richness Quality (B1+ Critical):**
    - 12a. Engagement: Boring? No hooks/metaphors?
    - 12b. Variety: Unique sentence starters (<50% repeat).
    - 12c. Emotional Hooks: Metaphors, scenarios, questions (≥1/section).
    - 12d. Cultural Depth: ≥1 named place/food/cultural ref; real Ukrainian scenarios.
    - 12e. Proverbs/Idioms (Grammar Modules): ≥1 demonstrating grammar.
    - Score per section 0-4: 0=Rewrite, 1-3=Enrich, 4=Pass.

13. **Humanity & Flow Audit:**
    - 13a. Cohesion: Logical paragraphs, transitional phrases.
    - 13b. Naturalness: Clear teacher voice, euphony (no vowel clashes).
    - 13c. Cognitive Load: Dense terms with explanations.
    - 13d. Sentence Variety: Mix lengths.
    - 13e. Figurative Language: Idioms/metaphors for B1+.
    - 13f. Readability: Natural contractions, simple English.
    - 13g. Cultural Authenticity: Ukrainian reality, not translated.
    - 13h. "Aha!" Moments: Discovery insights.
    - 13i. Accessibility: Inclusive, no stereotypes.

14. **Dryness Flags (Rewrite if 2+):**
    - TEXTBOOK_VOICE: No questions/hooks in 300+ words.
    - ROBOTIC_TRANSITIONS: No phrases between paragraphs.
    - REPETITIVE: Same pattern 5+ times.
    - GENERIC_EXAMPLES: No named people/places.
    - LIST_DUMP: Explanations as lists.
    - NO_CULTURAL_ANCHOR: Grammar without Ukrainian context.
    - ENGAGEMENT_BOX_FILLER: Boxes just restate.
    - WALL_OF_TEXT: >500 words without boxes/dialogue (except history/bio/lit).
    - EUPHONY_VIOLATION: >3 errors (u/v alternations).
    - Note: A1/A2 focus on scaffolding; richness for B1+.

## Scoring Philosophy

- **0-4 FAIL** (fix immediately)
- **5-6 FAIL** (below standard, fix)
- **7-8 INSUFFICIENT** (improve to 9+)
- **9-10 PASS** (acceptable)

**ONLY 9-10 IS ACCEPTABLE. Everything below requires fixes.**

**Justification Rule:**

- ≥8: Explain why not higher
- ≤6: Explain weaknesses
- 7: Explain both good and missing

## Dimension Rubrics (0-10 Scale)

### 1. Coherence

- 0-4: FAIL - Incoherent (missing sections, jumps)
- 5-6: FAIL - Basic (present, awkward transitions)
- 7-8: INSUFFICIENT - Clear (logical, smooth)
- 9-10: PASS - Seamless (perfect flow)

### 2. Relevance

- 0-4: FAIL - Off-topic (wrong focus)
- 5-6: FAIL - Loose (tangents)
- 7-8: INSUFFICIENT - Focused (serves goals)
- 9-10: PASS - Laser-focused

### 3. Educational

- 0-4: FAIL - Confusing/wrong
- 5-6: FAIL - Adequate, uninspiring
- 7-8: INSUFFICIENT - Clear/helpful
- 9-10: PASS - Outstanding ("aha" moments)

### 4. Language

- 0-4: FAIL - Major errors (Russianisms, calques)
- 5-6: FAIL - Functional, unnatural
- 7-8: INSUFFICIENT - Natural, good euphony
- 9-10: PASS - Native-level, elegant

### 5. Pedagogy

- 0-4: FAIL - Broken (wrong approach)
- 5-6: FAIL - Basic (template loose)
- 7-8: INSUFFICIENT - Solid (proper TTT/CBI)
- 9-10: PASS - Exemplary (innovative)

### 6. Immersion

- 0-4: FAIL - Wrong level
- 5-6: FAIL - Slightly off
- 7-8: INSUFFICIENT - Hits target
- 9-10: PASS - Optimal

**Ranges:** A1.1: 20-40%; A1.2: 40-60%; A1.3: 60-80%; A2: 40-70%; B1.1: 70-85%; B1.2+: 85-100%; B2+: 98-100%

### 7. Activities

- 0-4: FAIL - Broken (wrong answers, format)
- 5-6: FAIL - Functional (low density/variety)
- 7-8: INSUFFICIENT - Solid (good count/variety)
- 9-10: PASS - Outstanding (high density, creative)

### 8. Richness

**Min scores:** Grammar 95%, Vocab 92%, Cultural 90%, History 95%, Integration 88%

- 0-4: FAIL - Below min
- 5-6: FAIL - Meets min, thin
- 7-8: INSUFFICIENT - Above min, solid
- 9-10: PASS - Rich/varied (15%+ above)

### 9. Humanity

**Thresholds:** Direct Address ≥10, Encouragement ≥1, Anticipation ≥2, Validation ≥1

- 0-4: FAIL - Robotic
- 5-6: FAIL - Occasional warmth
- 7-8: INSUFFICIENT - Warm teacher voice
- 9-10: PASS - Exceptional warmth

### 10. LLM Fingerprint

- 0-4: FAIL - AI slop (multiple patterns)
- 5-6: FAIL - Some patterns
- 7-8: INSUFFICIENT - Minimal patterns
- 9-10: PASS - Human mastery

**Sub-dimensions:** AI clichés, false specificity, certainty overload, anecdotal absence, predictability, emotional flatness, voice inconsistency, shallow explanation, decorative culture.

## Section 15: LLM Fingerprint Detection

- 15a. Overused Phrases: Flag 3+ clichés → **LLM_CLICHE_OVERUSE**
- 15b. False Specificity: <3 Ukrainian refs → **FALSE_SPECIFICITY**
- 15c. Certainty Overload: >5 absolutes → **OVERCONFIDENCE**
- 15d. Anecdotal Absence: No narratives → **NO_NARRATIVE_VOICE**
- 15e. Predictability: No surprises → **PREDICTABLE_PEDAGOGY**
- 15f. Emotional Flatness: <1 marker/100 words → **EMOTIONAL_FLATNESS**
- 15g. Voice Consistency: Shifts >2 → **INCONSISTENT_VOICE**
- 15h. Shallow Explanation: No "why" → **MISSING_WHY_LAYER**
- 15i. Decorative Culture: Random facts → **DECORATIVE_CULTURE**

## Section 16: Human Warmth Checklist

- 16a. Direct Address: "you" (ти/ви), "we" (ми)
- 16b. Encouragement: ≥1 phrase ("You've got this!")
- 16c. Anticipates Confusion: ≥2 ("you might think...")
- 16d. Real-World Validation: ≥1 ("you'll be able to...")

**Fail:** <2 markers → **COLD_PEDAGOGY**

## Section 17: Richness Red Flags (AUTO-FAIL)

- 17a. ChatGPT Voice: "Welcome... we'll explore..." → Auto-fail
- 17b. Bullet Barrage: >50% bullets → Auto-fail
- 17c. Wikipedia Tone: Encyclopedic → Auto-fail
- 17d. Box Faker: >50% boxes restate → Auto-fail

## Section 18: Fix Strategies

1. Sensory Detail: Generic → Vivid
2. Name Everything: Vague → Specific
3. "Why" Layer: Shallow → Deep
4. Certainty: Absolute → Nuanced
5. Story: Factual → Narrative

## Section 19: Overall Score Calculation

**Weighted:**

```
Overall = (Coherence × 1.0 + Relevance × 1.0 + Educational × 1.2 + Language × 1.1 + Pedagogy × 1.2 + Immersion × 0.8 + Activities × 1.3 + Richness × 0.9 + Humanity × 0.8 + LLM × 1.1) / 10.4
```

**Round:** Nearest 0.5.

## Section 20: Final Report Format

```markdown
## Module [NUM]: [Title]

**Template:** [template] | **Compliance:** ✅ PASS / ❌ FAIL
**Overall Score:** [X/10] ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ (show X stars)
**Status:** ✅ PASS / ❌ FAIL
**AI Detection Flags:** [None / List]

### Scores Breakdown

- **Coherence:** X/10 - [Desc + justification if ≥8/≤6]
  ... (all dimensions)

### Strengths

- [3-5 specific]

### Issues

- [All issues]

### Examples

> [Strong] - Strength: [Why]
> [Weak] - Weakness: [Why]

### Recommendation

[✅ PASS / ❌ FAIL] - [Summary]

### Action Items

[List fixes or "None"]
```

## Calibration Examples

**6/10:** Scores 6.2, repetition, generic.
**8/10:** Scores 8.3, strong but gaps.
**10/10:** Scores 10.0, reference quality.

## Common Mistakes

- Anchoring to 10/10
- Ignoring issues
- Not using low scores
- Missing justifications
- Inconsistent standards
- False equivalence

**High scores earned, not given. Recalibrate if mostly 9-10s.**
