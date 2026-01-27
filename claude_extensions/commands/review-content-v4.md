# Review-Content-Scoring Prompt v4.0 (Modular Tier System)

```yaml
---
name: review-content-v4
description: 0-10 scoring rubric with tier-specific experience assessment
version: '4.0'
category: quality
dependencies: audit_module.py
changelog: v4.0 - Modular tier architecture for all levels
---
```

---

## STEP 1: DETECT TIER AND READ TIER FILE

**CRITICAL: Before reviewing, determine tier and read the tier-specific file.**

### Tier Detection

| Level | Tier | File to Read |
|-------|------|--------------|
| A1, A2 | Tier 1 (Beginner) | `claude_extensions/commands/review-tiers/tier-1-beginner.md` |
| B1, B2 Core, B2-PRO | Tier 2 (Core) | `claude_extensions/commands/review-tiers/tier-2-core.md` |
| B2-HIST, C1-HIST, C1-BIO, LIT | Tier 3 (Seminar) | `claude_extensions/commands/review-tiers/tier-3-seminar.md` |
| C1 Core, C1-PRO, C2 | Tier 4 (Advanced) | `claude_extensions/commands/review-tiers/tier-4-advanced.md` |

**Read the tier file NOW before continuing.**

---

## STEP 2: MANDATORY OUTPUT FORMAT

### File Naming
```
{slug}-review.md
```

### Save Location
```
curriculum/l2-uk-en/{level}/review/{slug}-review.md
```

### Header Format (COPY EXACTLY)
```markdown
# Module {NUM}: {Ukrainian Title}

**Template:** {template-name}.md | **Compliance:** ✅ PASS / ❌ FAIL
**Overall Score:** {X.X}/10
**Status:** ✅ PASS / ❌ FAIL
**Generated:** {YYYY-MM-DD HH:MM:SS}
**Reviewer:** Claude
**Tier:** {1-4} ({Beginner/Core/Seminar/Advanced})

## Scores Breakdown

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Experience Quality** | X/10 | {note} ← TOP PRIORITY |
| Coherence | X/10 | {note} |
| Relevance | X/10 | {note} |
| Educational | X/10 | {note} |
| Language | X/10 | {note} |
| Pedagogy | X/10 | {note} |
| Immersion | X/10 | {note} |
| Activities | X/10 | {note} |
| Richness | X/10 | {note} |
| Humanity | X/10 | {note} |
| LLM Fingerprint | X/10 | {note} |
| Linguistic Accuracy | X/10 | {note} |
```

**Note:** "Experience Quality" adapts per tier:
- Tier 1: Lesson Quality (tutoring experience)
- Tier 2: Teaching Quality (learning effectiveness)
- Tier 3: Lecture Quality (seminar engagement)
- Tier 4: Learning Quality (intellectual depth)

---

## STEP 3: EXECUTE TIER-SPECIFIC EXPERIENCE AUDIT

**Follow the tier file you read in Step 1.** Each tier has:
- Tier-specific "Would I...?" test
- Appropriate arc structure for level
- Pacing requirements
- Emotional/intellectual journey mapping
- Weak moment categories
- A+ checklist

**This is TOP PRIORITY. Do this FIRST.**

---

## STEP 4: SCORE ALL 12 DIMENSIONS

### Dimension List (All Tiers)

1. **Experience Quality (0-10):** Tier-specific assessment (see tier file)
2. **Coherence (0-10):** Logical flow, transitions, progressive difficulty
3. **Relevance (0-10):** Alignment with module goals, curriculum plan
4. **Educational (0-10):** Clear explanations, useful examples
5. **Language (0-10):** Ukrainian quality, no Russianisms, euphony
6. **Pedagogy (0-10):** Teaching approach, scaffolding, level-appropriateness
7. **Immersion (0-10):** Ukrainian-to-English ratio per level
8. **Activities (0-10):** Quality, density, variety, correctness
9. **Richness (0-10):** Examples, engagement, cultural references
10. **Humanity (0-10):** Teacher voice, warmth (tier-adjusted thresholds)
11. **LLM Fingerprint (0-10):** AI patterns vs. authentic writing
12. **Linguistic Accuracy (0-10):** Factual correctness (AUTO-FAIL if wrong)

### Scoring Philosophy

- **0-6 FAIL** (fix immediately)
- **7-8 INSUFFICIENT** (improve to 9+)
- **9-10 PASS** (acceptable)

**ONLY 9-10 IS ACCEPTABLE.**

### Overall Score Calculation

```
Overall = (Experience × 1.5 + Coherence × 1.0 + Relevance × 1.0 + Educational × 1.2 +
          Language × 1.1 + Pedagogy × 1.2 + Immersion × 0.8 + Activities × 1.3 +
          Richness × 0.9 + Humanity × 0.8 + LLM × 1.1 + Linguistic_Accuracy × 1.5) / 13.4
```

---

## STEP 5: CHECK SHARED QUALITY GATES

### Auto-fail Russianisms

| ❌ Wrong | ✅ Correct |
|----------|-----------|
| кушать | їсти |
| приймати участь | брати участь |
| самий кращий | найкращий |
| слідуючий | наступний |
| на протязі | протягом |

### Auto-fail Calques

| ❌ Wrong | ✅ Correct |
|----------|-----------|
| робити сенс | мати сенс |
| брати місце | відбуватися |

### Activity Structure (All Tiers)

- ❌ Duplicate items
- ❌ Wrong format/broken YAML
- ❌ Wrong answer marked correct
- ❌ Multiple valid answers but only one accepted
- ❌ Russianisms in content

### Linguistic Accuracy (Grammar Modules)

For aspectual pairs, verify:
1. Both verbs share same core meaning
2. Differ only in aspect
3. Cross-reference: Ohoiko "500+ Ukrainian Verbs", slovnyk.ua

**Common Error:** шукати/знайти is NOT a pair (different meanings). Correct: шукати/пошукати.

---

## STEP 6: APPLY FIXES

### Safe Fixes (Apply Immediately)

**Category 1: Structure** — Remove duplicates, fix typos, fix tables, fix euphony
**Category 2: Language** — Replace Russianisms, fix calques, fix grammar errors
**Category 6: Warmth** — Add direct address, encouragement (tier-adjusted)
**Category 7: AI Slop** — Remove LLM clichés, break bullet barrages
**Category 8: Accuracy** — Correct factual errors immediately

### Risky Fixes (User Approval)

- Rewriting >50% content
- Changing pedagogical approach
- Removing sections

---

## STEP 7: GENERATE REPORT

### Required Sections

```markdown
## Experience Analysis (Tier {N})

**Arc:** {element ✅/❌} → {element ✅/❌} → ...
**Emotional/Intellectual Beats:** {count per category}
**Pacing Issues:** {list}

## Weak Moments & Rewrites

### Weak Moment 1: {Category}
**Location:** Line {X}
**Original:** > {text}
**Problem:** {why}
**Rewrite:** > {fixed}

## Linguistic Accuracy Issues

- {issue} → {fix} — {source}

## Strengths

- {3-5 specific strengths}

## Issues

- {all issues by category}

## Recommendation

{✅ PASS / ❌ FAIL} — {summary}

## Action Items

1. {fix} — ✅ APPLIED / ⏳ MANUAL
```

---

## Usage

```
/review-content-v4 [LEVEL]              # All modules in level
/review-content-v4 [LEVEL] [NUM]        # Single module
/review-content-v4 [LEVEL] [START-END]  # Range
```

### Module Slug Lookup

1. Read `curriculum/l2-uk-en/curriculum.yaml`
2. Find level section
3. Module N = index N-1 in modules list
4. File: `curriculum/l2-uk-en/{level}/{slug}.md`

---

## Batch Mode

For multiple modules, spawn subagents:
```
For each module:
  Task agent → "/review-content-v4 {level} {num}"
  Wait → Log result → Continue (fresh context)
```

---

## Persona

> Embody the Ukrainian linguist & historian. See `claude_extensions/skills/_shared/persona.md`

**IPA RULE:** All phonetics MUST use IPA (no Latin transliteration).
**PYTHON:** Use `.venv/bin/python` only.
**WORKFLOW:** This is for manual review AFTER audit_module.py passes.
