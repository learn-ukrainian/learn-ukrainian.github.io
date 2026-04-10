# Plan Review Prompt — Core Levels (A1-C2)

You are reviewing a Ukrainian language course plan YAML file for core levels (A1, A2, B1, B2, C1, C2, B2-PRO, C1-PRO). Your job is to find errors, weaknesses, and gaps BEFORE content is built from this plan.

## Authority Sources

You have THREE authority sources. Use ALL of them:

1. **State Standard 2024** — Read `docs/l2-uk-en/state-standard-2024-mapping.yaml` with the Read tool. This is the Ukrainian government's official CEFR-mapped curriculum. Cross-reference the plan's grammar topics against the level's prescribed scope.

2. **Ukrainian textbooks (RAG)** — Use `mcp__sources__search_text` to verify grammar rules, pedagogical approaches, and vocabulary. The RAG contains 70+ Ukrainian school textbooks (grades 1-11) covering all grammar concepts in Ukrainian. Search in Ukrainian (e.g., "знахідний відмінок" not "accusative case").

3. **VESUM + GRAC** — Use `mcp__sources__verify_word` for vocabulary existence, `mcp__sources__query_grac` for frequency, `mcp__sources__query_r2u` for Russicism checks.

## Input

Read the plan YAML file, then systematically check every item below.

## Word Targets (from config.py)

**NEVER lower these. If the plan has a different value, flag as CRITICAL.**

| Track | target_words |
|-------|-------------|
| A1 | 1200 |
| A1-checkpoint | 1000 |
| A2 | 2000 |
| A2-checkpoint | 1500 |
| B1 | 4000 |
| B1-checkpoint | 4000 |
| B2, B2-checkpoint, B2-capstone | 4000 |
| C1, C1-checkpoint | 4000 |
| C2 | 5000 |
| C2-checkpoint | 4000 |

---

## Checks

### 1. RULE COMPLIANCE (blockers — any failure = plan REJECTED)

Flag as **CRITICAL**.

- [ ] **word_target matches config** — See table above.
- [ ] **Section budgets sum correctly** — Sum all section `words:` values. Must be within +/-10% of `word_target`.
- [ ] **No section >10% under its budget** — Each section's word count should not be more than 10% below its stated target.
- [ ] **Required fields present** — module, level, sequence, slug, version, title, subtitle, focus, pedagogy, word_target, objectives, content_outline, vocabulary_hints, activity_hints, persona, grammar, register.
- [ ] **Version is a string** — `version: '2.0'` not `version: 2.0`.

### 2. STATE STANDARD ALIGNMENT (MANDATORY)

**You MUST read `docs/l2-uk-en/state-standard-2024-mapping.yaml` with the Read tool before proceeding.**

Find the section for this plan's level (a1, a2, b1, b2, c1, c2). Then check:

- [ ] **Grammar scope appropriate for level** — Every grammar topic in the plan's `grammar:` field must appear in the State Standard's scope for this level. If a topic belongs to a higher level, flag as **HIGH** (e.g., Genitive plural at A1 when Standard puts it at A2).
- [ ] **Grammar not missing from plan** — If the plan's `content_outline` teaches grammar that isn't listed in the plan's `grammar:` field, flag as **MEDIUM**.
- [ ] **Thematic catalogue match** — The module's topic should fit within the Standard's thematic catalogue for this level.

### 3. GRAMMAR VERIFICATION (use textbook RAG)

For each grammar concept in the plan's `grammar:` field and `content_outline` points:

- [ ] **Search textbooks** — Use `mcp__sources__search_text` with the grammar concept in Ukrainian (e.g., for "Accusative case" search "знахідний відмінок", for "verb conjugation" search "дієвідмінювання"). Verify:
  - The rule is stated correctly in the plan
  - The examples given are accurate
  - The pedagogical approach aligns with how Ukrainian textbooks teach it
- [ ] **Flag incorrect rules** as **CRITICAL**
- [ ] **Flag imprecise explanations** as **MEDIUM** (e.g., oversimplifying a rule that has important exceptions)

### 4. VOCABULARY VERIFICATION (use VESUM + GRAC)

For every word in `vocabulary_hints.required` and `vocabulary_hints.recommended`:

- [ ] **VESUM check** — Use `mcp__sources__verify_word` for each Ukrainian word. Empty result = ghost word. Flag as **CRITICAL**.
- [ ] **Russicism check** — For words that might be shared with Russian, use `mcp__sources__query_r2u` to check. Flag as **HIGH**. Skip for clearly Ukrainian words.
- [ ] **Frequency check** — Use `mcp__sources__query_grac` (mode: frequency) on required vocabulary. Words with IPM < 1.0 may be too rare for the stated level. Flag as **LOW**.
- [ ] **Gender/case accuracy** — If vocab hints include example phrases with case forms, verify forms are correct. Use `mcp__sources__query_ulif` when in doubt.

### 5. YAML QUALITY

- [ ] **No YAML syntax issues** — Strings with colons, quotes, or special characters must be properly quoted.
- [ ] **No Latin characters in Ukrainian text** — Check for Latin lookalikes (a/a, o/o, c/c, i/i, e/e).
- [ ] **Prerequisites are valid** — Listed prerequisites should exist and be sequentially earlier. No self-references.

### 6. PEDAGOGICAL QUALITY

- [ ] **Objectives are testable** — Each objective describes something the learner CAN DO (not "understand" or "learn about").
- [ ] **Content outline matches objectives** — Every objective addressed by at least one section.
- [ ] **Logical progression** — Sections build on each other.
- [ ] **Activity hints achievable** — Types appropriate for level and content.

### 7. DECODABILITY (Cyrillic modules M1-M4 only)

Only for slugs containing "cyrillic-code":

- [ ] **All required vocab is decodable** — Words use ONLY letters from this module + prior modules.
- [ ] **Example phrases are decodable** — Reading exercises use only known letters.

### 8. CONTENT ACCURACY

- [ ] **Grammar rules cited correctly** — Verify against textbooks using `mcp__sources__search_text` (search in Ukrainian).
- [ ] **Cultural claims accurate** — Verify via `mcp__sources__query_wikipedia`.
- [ ] **No false Russicism claims** — If the plan claims a word is Russian/Surzhyk, verify with `mcp__sources__verify_word` and `mcp__sources__query_r2u`. False Russicism claims are **HIGH**.

---

## Output Format

```markdown
# Plan Review: {slug}

**Track:** {track} | **Sequence:** {sequence} | **Version:** {version}
**Verdict:** PASS / FAIL / NEEDS FIXES

## Rule Compliance
| Check | Status | Details |
|-------|--------|---------|
| word_target | PASS/FAIL | Plan: X, Config: Y |
| section_budgets | PASS/FAIL | Sum = X vs target Y (+/-Z%) |
| required_fields | PASS/FAIL | Missing: ... |
| version_string | PASS/FAIL | ... |

## State Standard Alignment
| Grammar Topic | In Standard? | Standard Level | Plan Level | Status |
|--------------|-------------|----------------|------------|--------|
| ... | YES/NO | ... | ... | PASS/FAIL |

## Grammar Verification (Textbook RAG)
| Concept | Textbook Source | Correct? | Notes |
|---------|----------------|----------|-------|
| ... | Grade X, author, chunk ID | YES/NO | ... |

## Vocabulary Verification
| Word | VESUM | Frequency (IPM) | Issues |
|------|-------|-----------------|--------|
| ... | OK/FAIL | ... | ... |

## Issues Found

### CRITICAL (must fix before build)
1. ...

### HIGH (should fix before build)
1. ...

### MEDIUM (fix if possible)
1. ...

### LOW (informational)
1. ...

## Suggested Fixes
[Concrete YAML edits with old/new]
```

---

## Batch Execution

Iterate over plan files:

```
for each plan in plans/{track}/*.yaml:
    run plan-review with plan_path and track
    save output to audit/{slug}-plan-review.md
```

### Efficiency Notes

- **Read State Standard ONCE** per batch (it's the same file for all plans in a level)
- **Prioritize CRITICAL**: If a CRITICAL issue is found, still complete the review but mark verdict as FAIL immediately
- **Search textbooks in Ukrainian**: "називний відмінок" not "nominative case", "теперішній час" not "present tense"
