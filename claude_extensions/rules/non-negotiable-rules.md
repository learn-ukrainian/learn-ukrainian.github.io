# NON-NEGOTIABLE RULES

All rules are hard requirements. Partial compliance = failure.

<critical>

## Quick Reference

| When... | Do this |
|---|---|
| Building content | Check `config.py` target_words FIRST — never hardcode from memory |
| Module under word target | Expand content to meet target. Never lower the target |
| Audit gate shows ❌ | Fix it. ALL gates must be GREEN or the module fails |
| Fixing a module | Batch ALL fixes in ONE pass, run ONE audit at end (rule 9) |
| Reviewing content | Cite SPECIFIC examples from the text, or the review is invalid (rule 6) |
| Plan can't be met | STOP building. Report to user. Propose new plan version (rule 7) |
| Review phase (v4) / Phase D (v3) | Loop: Review → Fix → Review → Fix until ALL gates PASS (rule 4) |

</critical>

---

## 1. Word Count Targets (Source of Truth: `config.py`)

<critical>

Expand content to meet targets. Never lower targets to match content.

**Always check config.py before generating content_outline or word budgets:**

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from audit.config import LEVEL_CONFIG
print(LEVEL_CONFIG['{LEVEL}']['target_words'])
"

# Or use the validation script
.venv/bin/python scripts/validate_plan_config.py {level}
```

**Word targets by level** (from `config.py` v2026-02-15 — if stale, re-read config.py):

| Level | Config Key | target_words |
|---|---|---|
| A1 | A1 | 2000 |
| A1-checkpoint | A1-checkpoint | 1500 |
| A2 | A2 | 3000 |
| A2-checkpoint | A2-checkpoint | 2500 |
| B1 | B1-grammar/vocab/cultural | 4000 |
| B1-checkpoint | B1-checkpoint | 4000 |
| B2 | B2 | 4000 |
| B2-checkpoint | B2-checkpoint | 4000 |
| B2-capstone | B2-capstone | 4000 |
| C1 | C1 | 4000 |
| C1-checkpoint | C1-checkpoint | 4000 |
| C2 | C2 | 5000 |
| C2-checkpoint | C2-checkpoint | 4000 |
| HIST | history | 5000 |
| ISTORIO | istorio | 5000 |
| BIO | biography | 5000 |
| LIT | LIT | 5000 |
| OES | OES | 5000 |
| RUTH | RUTH | 5000 |

> **B2-capstone**: Raised from legacy 2714 to 4000 (2026-03). Module content needs expansion.

**Lesson learned:** In January 2026, 270 ISTORIO plans were generated with 3500 words instead of 4000 because an agent hardcoded values from memory instead of reading config.py.

</critical>

---

## 2. Audit Gates — ALL Must Pass

ALL gates must be GREEN (✅) or the module FAILS.

| Gate | Requirement |
|---|---|
| Words | ≥ target from config.py |
| Activities | ≥ minimum count for level |
| Unique_types | Sufficient variety |
| Engagement | ≥ minimum engagement boxes for level |
| Vocab | ≥ minimum vocabulary for level |
| Naturalness | ≥ 8/10 |

Fix every failing gate. No exceptions, no "good enough."

---

## 3. Section-Level Word Targets (Flexible Guidance)

Section targets are guidance, not hard limits.

**Hard requirements:**
1. **Total word count** ≥ `word_target`
2. Each section within **±10% tolerance** of its target

**Flexible:** Redistribute words between sections freely. One section 20% over is fine if no section is >10% under.

```
Section A: 900 / 800 ✅ (+12.5% over — OK)
Section B: 500 / 600 ❌ (-16.7% under — expand to ≥540)
TOTAL: 1400 / 1400 ✅
```

**Priority:** Total word count first → fix sections >10% under → don't worry about over-target sections.

---

## 4. Review Loop (Review → Fix → Pass)

The review phase (v4 `review` / v3 `D`) loops until ALL gates PASS: Review → Fix → Review → Fix.

- Loop until ALL gates show ✅
- Fix every violation completely
- Rebuild sections if needed (>3 violations in one section)
- Do not stop at "most gates pass" or give up after 1-2 iterations

---

## 5. Quality Standards

| Requirement | Threshold |
|---|---|
| Naturalness score | 8+/10 minimum (9-10 preferred) |
| Russian ghost words | Zero (кот → кіт, хорошо → добре) |
| Engagement boxes | B2: 6+, C1: 7+ |
| Example sentences | B2: 28+, C1: 30+ |

Rewrite any text that fails naturalness. No robotic or disconnected prose.

---

## 6. LLM Self-Validation — Cite Evidence or It's Invalid

Reviews in `{slug}-llm-review.md` must cite SPECIFIC examples from the actual content.

**FAKE review (invalid):**

```markdown
| **Ukrainian Grammar** | ✅ PASS | High-style analytical register with historical terms. |
```

**HONEST review (required):**

```markdown
| **Ukrainian Grammar** | ✅ PASS | Case endings correct (e.g., "Данилом Галицьким" — instrumental). Verb aspects: "зумів об'єднати" (pf), "прагнула" (impf). No Russianisms found. |
```

Every review must: read the actual content first, verify grammar with real examples, list specific vocabulary found, check factual accuracy with concrete evidence. A review without evidence is a failed review.

---

## 7. Plan Versioning (Architecture v2.1)

Plans in `plans/` are the source of truth. They require user approval to change.

> `plans/{level}/{slug}.yaml` → VERSIONED (immutable without approval)
> `{level}/meta/{slug}.yaml` → MUTABLE build config
> `{level}/status/{slug}.json` → AUTO-GENERATED audit cache

**When build can't meet plan:** STOP → report "Plan requires X but Y isn't achievable because Z" → propose new plan version → user approves → backup old plan as `.bak` → write new version with bumped `version` field.

**Never** silently modify plan files, lower word_target to match output, or skip the backup step.

**This is mutiny:**

```yaml
# Plan says word_target: 4000, you wrote 3500, then changed plan to:
word_target: 3500  # ← FORBIDDEN
# Correct: ADD 500 more words to match plan
```

---

## 8. Meta.yaml Is Build Config, Not Planning

Meta.yaml = mutable build config. Plans = immutable source of truth.

| File | Contains | Mutability |
|---|---|---|
| `meta/{slug}.yaml` | naturalness score/status, version, build timestamps | Mutable |
| `plans/{level}/{slug}.yaml` | content_outline, word_target, objectives, vocabulary_hints, activity_hints | Immutable (user approval required) |

Update meta after naturalness evaluation or successful build. Never add planning data to meta.

---

## 9. Batch Fixes Within Module

When fixing a module, diagnose ALL issues first, fix ALL at once, audit ONCE.

**Wrong** (O(3N) tokens):
```
Read → Fix A → Audit → Read → Fix B → Audit → Read → Fix C → Audit
```

**Correct** (O(3) tokens):
```
1. DIAGNOSE: Read all 4 files (meta, md, activities, vocab) + run ONE audit
2. EXECUTE: Fix ALL issues in ONE pass (order: meta → vocab → activities → markdown)
3. VERIFY: Run ONE final audit
```

Fixes are interdependent (adding vocab → expanding sections → new activities). Batch fixing catches interaction bugs. This is mandatory for all review-phase work.

---

## 10. Activities Test LANGUAGE, Not Content

Activities practice Ukrainian language skills, not subject knowledge.

### 10a. Content-heavy modules (HIST, BIO, ISTORIO, LIT, RUTH, OES)

**Golden Rule:** Can the learner answer without reading the Ukrainian text? If YES → rewrite it.

| Pattern | Verdict |
|---|---|
| "У якому році..." (dates) | ❌ Tests content recall |
| "Хто був..." (names) | ❌ Tests content recall |
| "Згідно з текстом, як автор..." | ✅ Tests comprehension |
| "У тексті модуля автор характеризує..." | ✅ Tests comprehension |

### 10b. ZNO-format activities (EXEMPT from 10a)

ZNO activities (`zno_row_select`, `zno_sentence_select`, `zno_error_find`, `zno_fill_ending`) test language mechanics directly — наголос, фонетика, орфографія, морфологія. These are standalone language skill tests exempt from 10a. Source: `osyvokon/zno` (MIT license). Applies to both `l2-uk-en` and `l2-uk-direct` (A2+).

---

## Enforcement

Negotiating requirements down, skipping audit gates, producing under-length modules, or giving up before PASS = task failure.
