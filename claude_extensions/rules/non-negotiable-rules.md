# NON-NEGOTIABLE RULES

All rules are hard requirements. Partial compliance = failure.

<critical>

## Quick Reference

| When... | Do this |
|---|---|
| Building content | Check `config.py` target_words FIRST — never hardcode from memory |
| Module under word target | Expand content to meet target. Never lower the target |
| Audit gate shows ❌ | Fix it. ALL gates must be GREEN or the module fails |
| Fixing a module | Reviewer provides `<fixes>` — apply deterministically (rule 4) |
| Reviewing content | Cite SPECIFIC examples from the text, or the review is invalid (rule 6) |
| Plan can't be met | STOP building. Report to user. Propose new plan version (rule 7) |
| Review verdict REVISE | Reviewer outputs `<fixes>` find/replace pairs → pipeline applies them (rule 4) |
| Creating JSONL/data | Add ingestion flag + update tracking doc in SAME commit (rule 11) |

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
```

**Word targets by level** (from `config.py` v2026-03-05 — if stale, re-read config.py):

| Level | Config Key | target_words |
|---|---|---|
| A1 | A1 | 1200 |
| A1-checkpoint | A1-checkpoint | 1000 |
| A2 | A2 | 2000 |
| A2-checkpoint | A2-checkpoint | 1500 |
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

**Priority:** Total word count first → fix sections >10% under → don't worry about over-target sections.

---

## 4. Review + Fix Loop (V6 Pipeline)

V6 uses **reviewer-as-fixer**: Gemini reviews, finds issues, outputs `<fixes>` with exact find/replace pairs. Pipeline applies them deterministically — no LLM regeneration, no rewriting from scratch.

**Flow:**
1. Writer generates content → ENRICH adds tabs/словнік → REVIEW
2. If REVISE: reviewer outputs `<fixes>` → pipeline applies find/replace → re-ENRICH → re-REVIEW
3. Max 2 fix rounds. Score should go UP (9.0→9.4→9.7), never down.
4. If still failing after 2 rounds → problem is in the PROMPT or PLAN, not the content.

**Critical:** Reviewer sees PROSE ONLY (enrichment stripped before review). Deterministic word count injected into review prompt. Reviewer must NOT estimate word count — use the injected number.

**Never rewrite from scratch.** Gemini proved: "FROM SCRATCH" rewrites degrade content (9.6→9.2→8.4). PATCH fixes only what's broken.

---

## 5. Quality Standards

| Requirement | Threshold |
|---|---|
| Review score | 9+/10 target (8+ minimum PASS) |
| Russian ghost words | Zero (кот → кіт, хорошо → добре) |
| Dialogues | Natural situations from textbooks — not invented. Someone searches for keys, not interrogation. |
| Vocabulary | All words VESUM-verified. Writer generates словнік YAML with contextual translations. |
| Plans | Must have `references` (textbook + ULP links). No plan ships without references. |
| Stress marks | Added by deterministic annotator AFTER review, not by writer. |

Rewrite any text that fails naturalness. No robotic or disconnected prose.

---

## 6. LLM Self-Validation — Cite Evidence or It's Invalid

Reviews must cite SPECIFIC examples from the actual content.

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

**When build can't meet plan:** STOP → report "Plan requires X but Y isn't achievable because Z" → propose new plan version → user approves → backup old plan as `.bak` → write new version with bumped `version` field.

**Never** silently modify plan files, lower word_target to match output, or skip the backup step.

**Exception**: The pipeline may auto-fix plan `vocabulary_hints` entries that fail VESUM verification. Changes are version-bumped and logged in `plan_fixes`. Content outline, objectives, and word targets remain immutable.

---

## 8. Batch Fixes Within Module

When fixing a module, diagnose ALL issues first, fix ALL at once, verify ONCE.

**Wrong** (O(3N) tokens):
```
Read → Fix A → Audit → Read → Fix B → Audit → Read → Fix C → Audit
```

**Correct** (O(3) tokens):
```
1. DIAGNOSE: Read review findings + audit results
2. EXECUTE: Apply ALL fixes in ONE pass
3. VERIFY: Re-enrich + re-review ONCE
```

---

## 9. Activities Test LANGUAGE, Not Content

Activities practice Ukrainian language skills, not subject knowledge.

### 9a. Content-heavy modules (HIST, BIO, ISTORIO, LIT, RUTH, OES)

**Golden Rule:** Can the learner answer without reading the Ukrainian text? If YES → rewrite it.

| Pattern | Verdict |
|---|---|
| "У якому році..." (dates) | ❌ Tests content recall |
| "Хто був..." (names) | ❌ Tests content recall |
| "Згідно з текстом, як автор..." | ✅ Tests comprehension |
| "У тексті модуля автор характеризує..." | ✅ Tests comprehension |

### 9b. ZNO-format activities (EXEMPT from 9a)

ZNO activities test language mechanics directly — наголос, фонетика, орфографія, морфологія. These are standalone language skill tests exempt from 9a.

---

## 10. Complete The Work — No Tech Debt

Every operation must be finished end-to-end in the same commit:

| When you... | You MUST also... |
|---|---|
| Create JSONL data | Add ingestion flag to script + update `DICTIONARY-PIPELINE-STATUS.md` |
| Write plans | Add references (textbook + ULP links) to every plan |
| Build a module | Verify MDX renders correctly (not empty, has all tabs) |
| Fix a bug | Write a test that catches the same bug |
| Close a GH issue | Verify ALL acceptance criteria, not just "most" |

"For now", "batch job for later", "flag for human" = failure. If it needs doing, do it NOW.

---

## Enforcement

Negotiating requirements down, skipping audit gates, producing under-length modules, shipping without references, leaving incomplete work, or giving up before PASS = task failure.
