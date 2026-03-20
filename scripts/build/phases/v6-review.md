# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** {MODULE_NUM}: {TOPIC_TITLE} ({LEVEL}, {PHASE})
**Writer:** {WRITER_MODEL}
**Word target:** {WORD_TARGET}

## Plan (source of truth)

{PLAN_CONTENT}

## Generated Content

{GENERATED_CONTENT}

---

## Review Protocol

### Step 1: Inventory all Ukrainian text

Before scoring, list EVERY Ukrainian word, phrase, and sentence in the content. For each:
- Verify spelling (no Russian characters ы, э, ё, ъ)
- Check gender assignment if applicable
- Flag any Russianisms, Surzhyk, or calques

### Step 2: Inventory all exercises

List every exercise block (:::quiz, :::fill-in, :::match-up, :::group-sort, :::true-false).
For each exercise, check:
- Are the YAML keys valid? (no stray quotes, proper structure)
- Is the content pedagogically correct? (right answers actually right, distractors plausible)
- Can a learner actually complete this exercise? (sufficient context for fill-in, logical groupings)
- Does the exercise test what the module just taught? (not content recall, but language skill)

### Step 3: Score on 10 dimensions

Rate each dimension 1-10 with SPECIFIC evidence (cite line/paragraph).

| # | Dimension | Weight | What to check |
|---|-----------|--------|---------------|
| 1 | **Plan adherence** | 15% | Every content_outline point covered? Section word budgets respected (±10%)? All plan references used? |
| 2 | **Linguistic accuracy** | 15% | All Ukrainian correct? Stress marks present and correct? No Russianisms/Surzhyk/calques? Correct phonetic descriptions? |
| 3 | **Pedagogical quality** | 15% | PPP (Present→Practice→Produce) applied? Textbook pedagogy used (Большакова, Захарійчук)? Grammar scope respected (no A2 in A1)? |
| 4 | **Vocabulary coverage** | 10% | All required vocab from plan used naturally in prose? Recommended vocab included? New words introduced in context, not as lists? |
| 5 | **Exercise quality** | 10% | Exercises test the right skills? Placed after relevant teaching? Real content (not "?" placeholders)? Correct YAML syntax? Sufficient items per plan? |
| 6 | **Engagement & tone** | 10% | Interesting for teens/adults? Authoritative but warm (like a skilled teacher)? No LLM filler ("Good news!", "Don't panic!", "Fun fact!")? Cultural hooks? |
| 7 | **Structural integrity** | 5% | All H2 headings from plan present? Word count in range? No duplicate sections? No meta-commentary? Clean markdown? |
| 8 | **Cultural accuracy** | 5% | Decolonized (Ukrainian on its own terms, never "like Russian but...")? Factually correct claims about Ukrainian? Respectful representation? |
| 9 | **Dialogue & conversation quality** | 10% | Dialogues natural and culturally appropriate? Real situations, real responses? Speaker roles clear? Not stilted or textbook-robotic? |
| 10 | **Vocabulary table & resources** | 5% | Словник section present with all taught words? Pronunciation videos referenced? External resources linked? |

### Step 4: Calculate weighted score

Multiply each dimension score by its weight. Sum to get final score.

### Step 5: List findings

For every issue found, provide:
```
[DIMENSION] [SEVERITY: critical/major/minor]
Location: [specific section/paragraph/line]
Issue: [what's wrong]
Fix: [exactly how to fix it]
```

Critical = module cannot ship. Major = quality below standard. Minor = polish item.

### Step 6: Verdict

- **PASS** (≥8.0, zero critical) — ready for stress annotation and publishing
- **REVISE** (6.0-7.9 or has majors) — fix findings and re-review
- **REJECT** (<6.0 or has criticals) — fundamental rewrite needed

---

## Output Format

```
## Inventory
### Ukrainian text: [count] words verified
### Exercises: [count] found, [issues]

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | X/10 | [specific evidence] |
| ... | ... | ... |
| **Weighted total** | **X.X/10** | |

## Findings
[list all findings with dimension/severity/location/issue/fix]

## Verdict: PASS / REVISE / REJECT
[justification]
```
