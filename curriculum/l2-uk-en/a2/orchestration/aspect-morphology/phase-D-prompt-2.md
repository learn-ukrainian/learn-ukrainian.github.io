# Phase D.2: Targeted Repair

> **You are an expert Ukrainian language editor applying targeted fixes based on a review.**
> **You have file system access.** Use Read and Grep to verify every fix against the actual file content.

---

## Editing Principles

- **IMPROVE, don't destroy.** Every rewrite should teach MORE than the original, not less.
- **PRESERVE the author's intent.** If a paragraph explains something poorly, rewrite it to explain it well — don't delete it.
- **MATCH the surrounding voice.** Your rewrite should read like the original author wrote it on a better day.
- Only DELETE truly empty sentences (pure cheerleading with zero information that cannot be salvaged). This should be rare.

---

## Track Calibration

# Track Calibration: A2

## Bilingual Scope
A2 uses 3-band GRADUATED immersion — targets increase by module band:
- Band 1 (M01-20): 50-60% Ukrainian — Core grammar, English for theory
- Band 2 (M21-50): 60-75% Ukrainian — Applied grammar, English only for abstracts
- Band 3 (M51-70): 75-90% Ukrainian — Consolidation, near-full immersion

English explanations with Ukrainian examples and increasing Ukrainian prose
sections is CORRECT pedagogy. Do NOT flag bilingual content as LANGUAGE_BLENDER
when it falls within the module's immersion band.
Flag: Sections that exceed the module's immersion maximum.
Flag: Modules that fall below their minimum immersion target.

## Russicism Lookup (A2-specific)
All A1 Russicisms plus:
- приймати участь → брати участь (to participate)
- самий кращий → найкращий (the best — Russian superlative calque)
- на то, що → на те, що (Russian calque)
- відноситися → стосуватися / ставитися (to relate to)
- слідуючий → наступний (next — Russian calque)
- скучати → сумувати / нудьгувати (to miss/be bored)
- нравитися → подобатися (to like)

## Anglicism Lookup (A2-specific)
- "робити рішення" → "приймати рішення" (make a decision)
- "брати місце" → "відбуватися" (take place)
- "робити сенс" → "мати сенс" (make sense)

## LLM Filler Sensitivity
Stricter than A1. Motivational padding should be minimal.
Flag: Repeated "Let's explore/discover" patterns, generic AI transitions.
Do NOT flag: Brief warm-ups at section starts if they contain a teaching hook.

## Content Focus
Transitional level — grammar explanations getting longer, vocabulary richer.
Focus on: Russianisms, calques, correct case usage in examples, factual accuracy.


---

## Files You Can Read (use Read tool)

1. **Content**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/aspect-morphology.md`
2. **Activities**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/activities/aspect-morphology.yaml`
3. **Vocabulary**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/vocabulary/aspect-morphology.yaml`

---

## Review (from Phase D.1)

**IMPORTANT: The D.1 review verdict was PASS. Fix ONLY the audit failures listed below. Do NOT fix review suggestions — they are informational only.**

(Review omitted — verdict was PASS)


---

## Audit Failures (from automated re-audit)

```
VERDICT: FAIL
overall status is 'fail' (must be 'pass')
failing gates:
lesson: 3722/3000 (raw: 3953) | pedagogy: 1 violations
📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
→ 2 violations (minor)
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/aspect-morphology-audit.log for details)
```

---

## Instructions

1. Read the content file using the Read tool
2. For each issue identified in the review OR in the audit failures:
   a. Use Grep to find the exact text that needs fixing
   b. Produce a FIND/REPLACE pair with verbatim FIND text
3. Only fix issues documented above — no silent extra changes
4. Prioritize fixes by impact: audit gate failures first, then review issues
5. For Russianisms: replace with the standard Ukrainian form from the calibration table

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded.

```
===SECTION_FIX_START===
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/aspect-morphology.md
---
FIND:
exact text to replace (full sentence or paragraph, verbatim from the file)
REPLACE:
corrected replacement text
---
FIND:
next problematic text
REPLACE:
corrected replacement
---
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/activities/aspect-morphology.yaml
---
FIND:
exact activity text to replace
REPLACE:
corrected activity text
---
===SECTION_FIX_END===
```

## Fix Rules

- **FIND text must be verbatim** from the file — use Grep to verify before including
- Only fix issues documented in the review or audit failures above
- You MAY add new activities or modify existing ones if the review's Fix Plan explicitly requests it
- Do NOT add new prose sections or vocabulary items unless the review's Fix Plan explicitly requests it
- Maximum **20 FIND/REPLACE pairs** total (prioritize the most impactful fixes)
- Each FILE: line starts a new sub-block for that file
- If nothing needs fixing, output:
  ```
  ===SECTION_FIX_START===
  ===SECTION_FIX_END===
  ```

---

## Friction Report (MANDATORY)

After the fix block, include:

```
===FRICTION_START===
**Phase**: Phase D.2: Targeted Repair
**Step**: {what you were doing when friction occurred, or "Full Phase D.2"}
**Friction Type**: NONE | FIND_TEXT_MISMATCH | FILE_NOT_FOUND | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===
```

---

## Boundaries

- Do NOT write a review — that was already done in Phase D.1
- Do NOT output ===REVIEW_START=== blocks
- Do NOT modify files directly — only output fix blocks
- You MAY add/modify activities if the review's Fix Plan requests it (use FIND/REPLACE on the YAML file)
- Do NOT make cosmetic changes beyond what the review flagged
