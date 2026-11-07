# Plan Review: checkpoint-first-contact

**Track:** a1 | **Sequence:** 7 | **Version:** 1.2.1 | **Lifecycle:** locked
**Verdict:** NEEDS FIXES (one MEDIUM about checkpoint word_target inconsistency across A1)
**Authority:** `docs/l2-uk-en/state-standard-2024-mapping.yaml` — A1 review module (no new grammar). Cross-references all phonetics/morphology rules taught in M1–M6.

## Rule Compliance
| Check | Status | Details |
|-------|--------|---------|
| word_target | **MEDIUM** | Plan: 1200; **skill prompt table** says `A1-checkpoint: 1000`; **actual config** says `A1-checkpoint: 1000` (`scripts/audit/config.py:719-720`), BUT current `get_word_target` lookup uses `focus` key (plan focus is `review`, not `checkpoint`), so config falls back to A1=1200. So plan-vs-config matches **as configured**, but plan-vs-policy-intent does not. See cross-cutting in summary. |
| section_budgets | PASS | Sum = 200+250+200+400+150 = 1200 (exact match) |
| required_fields | PASS | All present |
| version_string | PASS | `version: '1.2.1'` (explicit string) |
| no Latin in Cyrillic | PASS | Scan clean (v1.2.1 removed 6 Latin tokens flagged in cross-agent review per #1392 D1/D7) |

## State Standard Alignment
| Grammar Topic | In Standard? | Standard Level | Plan Level | Status |
|--------------|-------------|----------------|------------|--------|
| New grammar | N/A — review module | — | — | PASS — "Нової граматики немає" explicit |
| Recap of: Це + іменник, nullsubject (Я — студент), у мене є, мій/моя/моє, як тебе/вас звати, звідки + country | All previously introduced in M1–M6 | A1 | A1 review | PASS |

## Grammar Verification (Textbook RAG)
| Concept | Source | Correct? | Notes |
|---------|--------|----------|-------|
| Bundling 6 key constructions for synthesis | ULP Ep.10 (cited) | YES | Anna's Episode 10 is the canonical review-of-1-9 episode and the plan correctly anchors here |
| Author-note enumerating 6 forbidden Surzhyk/calque forms (`папа`, `фамілія`, `Моє ім'я є...`, `Я є студент`, `Я маю 25 років`, `Здрастуйте/Пока`) | Wiki "Типові помилки L2" (cited) | YES | All 6 are real L2 issues at this level |
| Two-speaker dialogue at language-meetup setting (ти-register) | Pragmatic alignment | YES | Setting reframed in v1.2.0 from formal conference to peer-meetup so ти-register and family-topic content cohere |

## Vocabulary Verification (VESUM)
| Word | VESUM | Notes |
|------|-------|-------|
| Required: "All vocabulary from №1–6 is recycled" | Inherits all M1–M6 vocab | OK |
| Recommended: ім'я, прізвище, знайомство, професія, національність, походження, Вітаю, Дуже приємно, Мені теж, тато | All FOUND | OK |
| Russianism counter-pairs in fill-in: Здрастуйте, папа, Моє ім'я є Іван, Я є студент, Я маю 25 років, фамілія, Пока | **папа FOUND, фамілія FOUND (both are valid Ukrainian words but used differently)**; others NOT FOUND | See HIGH |

## Issues Found

### CRITICAL (must fix before build)
None.

### HIGH (should fix before build)
1. **`Мій {тато|папа} — інженер.`** (activity_hints[3].items[1]). `папа` IS in VESUM (2 matches, no restrictive tags), and the **my-family plan (M6) v1.4.0 explicitly dropped this exact pair from its Surzhyk drill** after Codex AC-3 adversarial review, citing "VESUM lists `папа` without restrictive tags, so framing it as a dictionary-backed error would be overreach." Including it here as a "wrong" form contradicts the M6 audit conclusion and inverts the team's own discipline. Suggested fix: remove this row OR reframe as a register preference (тато is more common in colloquial register), matching M6's framing. Items count drops from 7 to 6 (still meets minimum).
2. **`Як твоє {прізвище|фамілія}?`** (activity_hints[3].items[5]). `фамілія` IS in VESUM but means "family" (archaic, low-frequency in modern usage). Calling someone's surname `фамілія` IS Russian-influenced (Russian фамилия = surname), so this Surzhyk flag IS defensible — but the author-note should clarify "фамілія exists but means «family» archaically; for surname use `прізвище`." Current framing risks teaching that the word doesn't exist at all.

### MEDIUM (fix if possible)
1. **word_target mismatch with skill policy.** Per the plan-review skill prompt table, A1-checkpoint target is 1000, but the plan has 1200. The actual `scripts/audit/config.py` enforces 1000 only when `focus: checkpoint` is set; since this plan has `focus: review`, the audit currently accepts 1200. The inconsistency is curriculum-wide (5 of 8 A1 checkpoints use 1200, 3 use 1000 — see Suggested Fixes). This is a **cross-cutting policy decision**, not a single-plan defect.

### LOW (informational)
1. Plan correctly notes the deliberate omission of wiki row 8 (`Я із Росії`) from the drill — sensitive contextual call to avoid teaching that pattern as an item, even as a negative example. Good editorial judgment.
2. The author-note in Діалог section (forbidden Surzhyk + ти-register consistency) is excellent writer guardrails.
3. v1.2.1 cleanup of 6 Latin tokens (per AC-3) is a sign of good adversarial-review hygiene.

## Suggested Fixes

```yaml
# activity_hints[3].items — remove the тато/папа row; clarify прізвище/фамілія
items:
  - '{Добрий день|Здрастуйте}! Мене звати Оксана.'
  - '{Мене звати Іван|Моє ім''я є Іван}.'
  - Я {студент|є студент}.
  - '{Мені 25 років|Я маю 25 років}.'
  - Як твоє {прізвище|фамілія}?  # keep — defensible Surzhyk pattern
  - — Дякую! — Будь ласка. — {До побачення|Пока}!
# (6 items, matches min_items_per_activity)

# vocabulary_hints.recommended — adjust author-note framing for тато
# old:
- тато (dad — standard; NOT the Russianism `папа`)
# new:
- тато (dad — preferred colloquial register; `папа` is also Ukrainian but more child-register / familial)

# CROSS-CUTTING: word_target — see summary roll-up; recommend curriculum-wide audit decision before this single plan changes.
```

## Verdict
NEEDS_FIX. One HIGH item (`тато/папа` Surzhyk-pair contradiction with M6's documented discipline) must be resolved before re-build to keep editorial line consistent. The MEDIUM word_target issue is curriculum-wide policy, not a single-plan blocker — flag in summary for orchestrator decision. Once `тато/папа` is removed and `фамілія` framing is clarified, plan is build-ready.
