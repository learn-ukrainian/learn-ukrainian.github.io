# Phase D.2: Targeted Repair

> **You are an expert Ukrainian language editor applying targeted fixes based on a review.**
> **You have file system access.** Use Read and Grep to verify every fix against the actual file content.

---

## Context

A review identified issues in this module. Your job is to produce **exact FIND/REPLACE fix pairs** that resolve the issues. You are NOT writing a review — that was already done. Focus only on producing correct, targeted fixes.

---

## Files You Can Read (use Read tool)

1. **Content**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2-hist/sloviany-origins.md`
2. **Activities**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2-hist/activities/sloviany-origins.yaml`
3. **Vocabulary**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2-hist/vocabulary/sloviany-origins.yaml`

---

## Review (from Phase D.1)

**Reviewed-By:** claude-opus-4-6

# Phase D Review: sloviany-origins

**Module**: `curriculum/l2-uk-en/b2-hist/sloviany-origins.md`
**Reviewer**: Claude (Phase D cross-agent review)
**Date**: 2026-02-21
**Attempt**: 1 of 3

---

## Plan Verification

| Plan Requirement | Status | Notes |
|---|---|---|
| Cover proto-Slavic origins and migration theories | PASS | Content covers Zarubyntsi, Cherniakhiv, Prague culture |
| Decolonization perspective | PARTIAL | Gumilev term «пасіонарні» contradicts decolonization framing |
| Primary source integration | PARTIAL | Mauricius quote modified from research notes |
| Грушевський reference (plan L50) | FAIL | Missing entirely |
| B2 CEFR linguistic level | PASS | Appropriate complexity |

---

## Scores

| # | Dimension | Score | Weight | Weighted | Notes |
|---|---|---|---|---|---|
| 1 | Linguistic Accuracy | 8 | 15% | 1.20 | «будь-якіх» wrong declension (L33); auto-fail < 9 |
| 2 | Pedagogical Design | 9 | 12% | 1.08 | Solid TTT flow, scaffolded well |
| 3 | Content Accuracy | 7 | 15% | 1.05 | Modified Mauricius quote, ungrounded Boz etymology, dubious «ЕСУ, 2026» citation |
| 4 | Cultural Sensitivity | 7 | 10% | 0.70 | «пасіонарні» — Gumilev/Neo-Eurasianist term inappropriate for decolonized curriculum |
| 5 | Activity Quality | 8 | 10% | 0.80 | Jordanes quote mismatch between content (L191) and activities (L58) |
| 6 | Vocabulary Integration | 9 | 8% | 0.72 | Well-integrated, level-appropriate |
| 7 | Plan Fidelity | 8 | 8% | 0.64 | Missing required Грушевський reference |
| 8 | Engagement & Flow | 8 | 5% | 0.40 | Narrative flow good but LLM word repetition detracts |
| 9 | Source Quality | 7 | 5% | 0.35 | «ЕСУ, 2026» unverifiable; quote modifications |
| 10 | Naturalness | 8 | 5% | 0.40 | «значно» ×12, «фундамент» ×6 — clear LLM fingerprint |
| 11 | Accessibility | 9 | 3% | 0.27 | Good glossing and scaffolding |
| 12 | Format Compliance | 9 | 2% | 0.18 | Meets structural requirements |
| 13 | Decolonization Lens | 8 | 2% | 0.16 | Good framing overall but Gumilev term undermines it |

**Total: 7.95 / 10** (weighted) | **Simple Average: 8.1 / 10**

---

## Auto-Fail Checklist

| Gate | Result | Detail |
|---|---|---|
| Linguistic Accuracy < 9 | **TRIGGERED** | Score 8 — morphological error «будь-якіх» |
| Content Accuracy < 7 | PASS | Score 7 (borderline) |
| Fabricated citation | **FLAG** | «ЕСУ, 2026» — cannot verify this edition year |
| Self-review detected | PASS | Gemini-built, Claude-reviewed |
| Word count minimum | PASS | Meets target |

---

## Critical Issues

### Issue 1: Grammar — wrong declension (AUTO-FAIL)
- **Location**: L33
- **Found**: «будь-якіх»
- **Expected**: «будь-яких»
- **Severity**: HIGH — triggers auto-fail gate
- **Fix**: Single word replacement

### Issue 2: Modified primary source quote
- **Location**: L179
- **Found**: Mauricius quote uses «таке саме» and includes phrase «особливо у власній землі»
- **Expected**: Research notes have «однакове» and lack the added phrase
- **Severity**: HIGH — primary source integrity
- **Fix**: Restore quote to match research notes exactly

### Issue 3: Dubious citation date
- **Location**: L19, L206
- **Found**: «ЕСУ, 2026»
- **Issue**: Unverifiable publication date — likely fabricated by generation model
- **Severity**: HIGH — academic credibility
- **Fix**: Replace with verifiable citation or remove year

### Issue 4: Ungrounded etymological claim
- **Location**: L103
- **Found**: Boz name etymology derived from «Бог»
- **Issue**: Not supported by research notes; speculative folk etymology
- **Severity**: MEDIUM — content accuracy
- **Fix**: Remove or mark as speculative with hedging language

### Issue 5: Quote inconsistency across files
- **Location**: Content L191 vs Activities L58
- **Found**: Jordanes quote differs between content and activities
- **Severity**: MEDIUM — internal consistency
- **Fix**: Align activity quote to match content quote exactly

### Issue 6: LLM word overuse fingerprint
- **Location**: Throughout
- **Found**: «значно» ×12, «фундамент» ×6
- **Severity**: MEDIUM — naturalness
- **Fix**: Replace 8+ instances with synonyms or restructure sentences

### Issue 7: Ideologically problematic terminology
- **Location**: L79
- **Found**: «пасіонарні» — term from Gumilev's Neo-Eurasianist theory
- **Issue**: Russian imperial-adjacent ideology contradicts decolonized curriculum
- **Severity**: MEDIUM-HIGH — cultural sensitivity
- **Fix**: Replace with neutral Ukrainian historiographic term (e.g., «динамічні», «активні»)

### Issue 8: Missing plan-required reference
- **Location**: Plan L50 requirement
- **Found**: No Грушевський reference in module
- **Severity**: MEDIUM — plan fidelity
- **Fix**: Add Грушевський perspective on Slavic origins

---

## Strengths

1. **Strong narrative arc**: Proto-Slavic origins → migration → cultural differentiation is well-structured
2. **Good CEFR calibration**: B2-appropriate complexity with effective glossing
3. **Solid archaeological framework**: Zarubyntsi, Cherniakhiv, Prague culture sequence is pedagogically sound
4. **Effective vocabulary integration**: Key terms introduced in context with reinforcement
5. **Decolonization framing** (mostly): Ukrainian-centered perspective on Slavic ethnogenesis

---

## Fix Plan

All 8 issues are fixable in a **single editing pass** — no structural rewrite needed.

| Priority | Issue | Action | Est. Effort |
|---|---|---|---|
| P0 | #1 Grammar | Replace «будь-якіх» → «будь-яких» | 1 min |
| P0 | #2 Quote | Restore Mauricius quote from research notes | 5 min |
| P1 | #3 Citation | Fix or remove «ЕСУ, 2026» | 3 min |
| P1 | #4 Etymology | Remove/hedge Boz «Бог» claim | 3 min |
| P1 | #5 Quote sync | Align Jordanes quote in activities to content | 3 min |
| P1 | #7 Gumilev | Replace «пасіонарні» with neutral term | 2 min |
| P2 | #6 Word overuse | Diversify «значно» and «фундамент» usage | 10 min |
| P2 | #8 Грушевський | Add reference per plan requirement | 10 min |

---

## Factual Verification

| Claim | Status | Notes |
|---|---|---|
| Zarubyntsi culture as proto-Slavic | PLAUSIBLE | Mainstream but debated position |
| Cherniakhiv culture multi-ethnic | VERIFIED | Standard historiographic view |
| Prague culture = early Slavs | VERIFIED | Widely accepted |
| Boz etymology from «Бог» | UNVERIFIED | Not in research notes; folk etymology |
| Mauricius on Slavic warfare | VERIFIED in principle | But quote wording modified from source |
| «ЕСУ, 2026» | UNVERIFIABLE | Publication date cannot be confirmed |

---

## Verification Summary

- **Issues found**: 8 (2 critical, 4 medium-high, 2 medium)
- **Auto-fail gates triggered**: 1 (Linguistic Accuracy < 9)
- **Structural rewrite needed**: No
- **Estimated fix effort**: Single editing pass (~37 min)

---

## Verdict

**FAIL** — Score 7.95/10 | Auto-fail: Linguistic Accuracy 8 < 9 threshold

8 issues identified, all fixable without structural changes. Primary concerns: morphological error triggering auto-fail, modified primary source quote, dubious citation, and ideologically inappropriate Gumilev terminology. Recommend fix pass and re-review.

---

## Audit Failures (from automated re-audit)

```
VERDICT: FAIL
overall status is 'fail' (must be 'pass')
failing gates:
❌ [LOW_CITATION_DENSITY] Review has only 2 Ukrainian citation(s) for 5368-word content (need at least 8). A proper review must cite specific Ukrainian sentences from the content to support its assessment. Quote the actual text with «» or "".
❌ [REVIEW_LOW_SECTION_COVERAGE] Review only covers 0/7 (0%) content sections. Missed: Вступ: Етимологія та ідентичність, Читання: I — Археологія та географія розселення, Читання: II — Антський союз: Хроніки боротьби, Читання: III — Матеріальний світ та суспільний устрій, Первинні джерела: Свідчення сучасників. A thorough review must address each major section of the content.
❌ AUDIT FAILED. Correct errors before proceeding.
Critical Failures:
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/sloviany-origins-audit.log for details)
```

---

## Instructions

1. Read the content file using the Read tool
2. For each issue identified in the review OR in the audit failures:
   a. Use Grep to find the exact text that needs fixing
   b. Produce a FIND/REPLACE pair with verbatim FIND text
3. Only fix issues documented above — no silent extra changes
4. Prioritize fixes by impact: audit gate failures first, then review issues

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded.

```
===SECTION_FIX_START===
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2-hist/sloviany-origins.md
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
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2-hist/activities/sloviany-origins.yaml
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
