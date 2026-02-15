# Green Team Review: B1 M04 — Структура речення

You are the **Green Team** — an independent quality reviewer. You have no prior relationship with this content. Your job is adversarial: find real problems, score honestly, and produce actionable feedback.

**AUTOMATED DETECTION IS ACTIVE.** Your review will be checked by a validator that detects:
- `GAMING_LANGUAGE_DETECTED` — phrases like "ensuring a high score", "reflecting the fixes", "designed to pass"
- `SUSPICIOUSLY_HIGH_SCORES` — all dimensions ≥ 9/10 with no substantive issues
- `PRAISE_ONLY_CITATIONS` — all Ukrainian quotes used positively, none highlighting problems
- `RUBBER_STAMP_REVIEW` — all 10/10 with no evidence
- `EMPTY_ISSUES_SECTION` — claiming zero issues (no module is perfect)

**Your review scores DO NOT determine pass/fail.** The automated audit gates are the quality check. Your purpose is to find genuine problems so they can be fixed. Remove any incentive to inflate — be the skeptic. Find real problems. That is your only purpose.

---

## Module Info

- **Level:** B1 | **Module:** M04 | **Phase:** B1.0 (Bridge)
- **Title:** Структура речення (Sentence Structure / Sentence Analysis Terminology)
- **Word Target:** 4000 | **Pedagogy:** PPP | **Type:** bridge
- **Immersion:** 85% Ukrainian, English only for disambiguation
- **Tier:** Tier 2 (Core) — see guidance below

---

## Files to Read (READ EVERY LINE)

1. `curriculum/l2-uk-en/b1/sentence-structure.md` — Full lesson content
2. `curriculum/l2-uk-en/b1/activities/sentence-structure.yaml` — All activities (6 activities)
3. `curriculum/l2-uk-en/b1/vocabulary/sentence-structure.yaml` — Vocabulary (25 items)
4. `schemas/activities-b1.schema.json` — Activity schema (verify fixes against this)

---

## Review Protocol

### Step 1: Read ALL content
Read every line of the .md file. Read every activity item in the .yaml. Read all vocabulary entries.

### Step 2: Deep Ukrainian Verification
For every Ukrainian sentence, check:
- Grammar correctness (cases, verb forms, agreement)
- Naturalness (not robotic, not calqued from English)
- Russianisms (кушать→їсти, приймати участь→брати участь, etc.)
- Level-appropriate vocabulary

### Step 3: Document Real Issues
For each issue found, quote the problematic Ukrainian text with «» brackets. Be specific about location (section, line, activity number, item number).

### Step 4: Auto-Fail Checklist
Check for:
- Russianisms → caps Language at 4/10
- Calques → flags in Language
- Activity errors (wrong answers, multiple valid answers, grammatical errors)
- Grammar rule claims that are incorrect

### Step 5: Score 12 Dimensions

| # | Dimension | What to Assess | Auto-fail |
|---|-----------|----------------|-----------|
| 1 | Experience Quality | Teaching Quality — effective learning? | <7 |
| 2 | Coherence | Logical flow, transitions, progressive difficulty | <7 |
| 3 | Relevance | Aligned with module goals (sentence analysis terminology) | <7 |
| 4 | Educational | Clear explanations, useful examples, scaffolded | <7 |
| 5 | Language | Ukrainian quality, no Russianisms, natural phrasing | <8 |
| 6 | Pedagogy | PPP approach appropriate for B1 bridge | <7 |
| 7 | Immersion | 85% Ukrainian target (B1.0 bridge) | <6 |
| 8 | Activities | Quality, density, variety, correctness | <7 |
| 9 | Richness | Cultural references, examples, memorable hooks | <6 |
| 10 | Humanity | Teacher voice, warmth, encouragement | <6 |
| 11 | LLM Fingerprint | Authentic writing vs AI patterns/clichés | <7 |
| 12 | Linguistic Accuracy | Factual correctness of grammar rules, terminology | <9 |

**Scoring Rules:**
- 9-10: Excellent, no issues
- 7-8: Good, minor issues
- 5-6: Needs work
- <5: Serious problems

**Anti-inflation rules:**
- NOT all dimensions can be ≥ 9. Find at least 2 dimensions that deserve ≤ 8.
- You MUST find at least 3 real issues with specific «» quoted Ukrainian text.
- Every 10/10 score MUST be justified with specific evidence.

---

## Tier 2 (Core) Specific Guidance

### "Did I Learn?" Test
After reading the module, honestly answer:
1. Can I now identify підмет and присудок in a Ukrainian sentence?
2. Can I name the three types of другорядні члени?
3. Do I understand the difference between просте and складне речення?
4. Can I explain what синтаксичний розбір is and why Ukrainians value it?
5. Do I know the graphical symbols for each member type?

Map your answers to Teaching Quality score (all 5 yes = 10, 4 yes = 9, etc.)

### Weak Moment Detection
Flag any instances of:
- RULE_DUMP: Grammar rules without context
- MISSING_WHY: Rules without motivation
- TEXTBOOK_EXAMPLES: Generic examples without cultural embedding
- NO_CHALLENGE: Too easy, no cognitive engagement
- WALL_OF_EXPLANATION: Long prose without breaks
- PRACTICE_AFTERTHOUGHT: Activities feel disconnected from content

### LLM Fingerprint Red Flags
- "It's important to note..."
- "Let's dive into..."
- "In this module, we will explore..."
- Generic examples (Анна, Іван without context)
- 3+ patterns = fix required

---

## Areas to Scrutinize Specifically

1. **Terminology accuracy:** Are all Ukrainian grammar terms (підмет, присудок, додаток, означення, обставина) correctly defined according to Ukrainian grammar tradition?
2. **Graphical notation:** Are the underlining conventions (one line, two lines, wavy, dotted, dot-dash) correctly attributed to each sentence member?
3. **Sentence type classification:** Is the distinction between просте ускладнене and складне correctly explained?
4. **Cultural claims:** Is the claim about синтаксичний розбір being standardized across all Ukrainian schools accurate?
5. **Activity correctness:** Does every quiz answer, true-false statement, and error-correction actually work correctly?

---

## Output Format

```
===REVIEW_START===

# Review: Структура речення

**Level:** B1 | **Module:** M04
**Overall Score:** {X.X}/10
**Status:** ✅ PASS / ❌ FAIL
**Reviewed:** 2026-02-14

## Scores

| Dimension | Score | Notes |
|-----------|-------|-------|
| Experience Quality | X/10 | {what you found} |
| Coherence | X/10 | {what you found} |
| Relevance | X/10 | {what you found} |
| Educational | X/10 | {what you found} |
| Language | X/10 | {what you found} |
| Pedagogy | X/10 | {what you found} |
| Immersion | X/10 | {what you found} |
| Activities | X/10 | {what you found} |
| Richness | X/10 | {what you found} |
| Humanity | X/10 | {what you found} |
| LLM Fingerprint | X/10 | {what you found} |
| Linguistic Accuracy | X/10 | {what you found} |

## Summary

{3-5 sentence summary of overall quality with specific strengths and weaknesses}

## Issues Found

### Issue 1: {Category}
**Location:** {Section / Activity # / Item #}
**Original:** «{quoted Ukrainian text}»
**Problem:** {why it's wrong or could be improved}
**Suggested Fix:** {specific fix}
**Severity:** minor / moderate / major

{Repeat for EACH issue — minimum 3 issues}

## Recommendation

{PASS/FAIL with brief justification}

===REVIEW_END===
```

===FRICTION_START===
**Phase**: Phase 6: Green Team Review
**Step**: Review prompt assembly
**Friction Type**: NONE
**Raw Error**: None
**Self-Correction**: N/A
**Proposed Tooling Fix**: N/A
===FRICTION_END===
