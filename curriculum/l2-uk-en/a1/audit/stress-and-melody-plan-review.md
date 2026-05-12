# Plan Review: stress-and-melody

**Track:** a1 | **Sequence:** 4 | **Version:** 1.2.1 | **Lifecycle:** locked
**Verdict:** PASS (one MEDIUM about a pedagogical exception that author acknowledges)
**Authority:** `docs/l2-uk-en/state-standard-2024-mapping.yaml` — A1 §4.1.5 (stress), §4.1.8 (intonation).

## Rule Compliance
| Check | Status | Details |
|-------|--------|---------|
| word_target | PASS | Plan: 1200 = Config A1: 1200 |
| section_budgets | PASS | Sum = 350+300+300+250 = 1200 (exact match) |
| required_fields | PASS | All present |
| version_string | PASS | `version: 1.2.1` |
| no Latin in Cyrillic | PASS | Scan clean (v1.2.1 stripped U+0301 stress marks per pipeline policy) |

## State Standard Alignment
| Grammar Topic | In Standard? | Standard Level | Plan Level | Status |
|--------------|-------------|----------------|------------|--------|
| Free / mobile stress | YES (§4.1.5) | A1 | A1 | PASS |
| Intonation contours (declarative ↘, yes/no Q ↗, exclamation ↘↘, WH-Q ↘) | YES (§4.1.8) | A1 | A1 | PASS |
| Stress-pair meaning distinction (замок/замок) | NUS pedagogy (Заболотний 5 кл. с.73) | A1 | A1 | PASS |
| Numerals одинадцять / чотирнадцять (stress on -на-) | A1 stress-load (commonly taught early) | A1 | A1 | PASS — but the numbers themselves are A1 vocab introduced later; recommended-tier here, which is fine |

## Grammar Verification (Textbook RAG)
| Concept | Textbook Source | Correct? | Notes |
|---------|----------------|----------|-------|
| Stress is free and mobile in Ukrainian | Заболотний 5 кл. с.73 (cited) | YES | Standard A1 framing |
| Sentence types by purpose: розповідні / питальні / спонукальні / окличні | Авраменко 5 кл. с.19 (cited) | YES | Correct |
| WH-questions take falling intonation (Що це? ↘) vs yes/no questions take rising (Це метро? ↗) | Standard | YES | Internal contradiction from prior version (питальна ↗ overstatement) was correctly fixed in v1.2.0 — plan now consistent |
| `Як справи? ↘` (WH-Q rule) with author-note about conversational rising contour | Author-note in content_outline[2].points[2] | YES | Defensible compromise — author transparently flags conversational vs normative; writer gets clear instruction to teach normative ↘ |
| Homograph stress pairs: замок/замок, атлас/атлас, орган/орган, сім'я/сім'я | Common stress-pair pedagogy | YES | All four pairs are real Ukrainian stress homographs |

## Vocabulary Verification (VESUM)
| Word | VESUM | Notes |
|------|-------|-------|
| наголос | FOUND | OK |
| замок | FOUND (both stress variants) | OK — meaning by stress is correct |
| атлас | FOUND | OK |
| орган | FOUND | OK |
| кава / вода / столиця / ранок / метро / фотографія | All FOUND | OK |
| одинадцять / чотирнадцять | FOUND | OK — stress on -на- is correct (validated by Pravopys/goroh) |

## Issues Found

### CRITICAL (must fix before build)
None.

### HIGH (should fix before build)
None.

### MEDIUM (fix if possible)
1. **`Як справи? ↘` author-note exception** (content_outline[2].points[2]). The plan acknowledges that conversational Ukrainian typically uses rising intonation for `Як справи?` (phatic function) but mandates the normative falling contour to consolidate the WH-question rule. This is a defensible pedagogical compromise — but the build writer may emit audio/synthesis with the wrong contour if the TTS layer defaults to rising for the `?` punctuation. Suggested fix: add an explicit `intonation_override` directive in the section's points so the audio-generation step (when added) can respect the author's intent. Note: not a blocker — current text-only build is fine, but flag for next-gen TTS phase.

### LOW (informational)
1. The `мука / мука` (flour/torment) homograph pair was correctly dropped from vocabulary_hints in v1.2.0 with a writer-note explaining that the modern standard for "flour" is `борошно` (cited in content_outline[0].points[1]). This is excellent attention to dialectal/standard register distinction.
2. The stress-transfer fill-in activity drills classic R-L1 transfer errors (новий/новий, старий/старий, plural mobile stress, fem -ія names). Strong adversarial-learning coverage.

## Suggested Fixes
None blocking; the MEDIUM is a forward-looking note about TTS, not a current-build issue.

## Verdict
PASS. The plan is rigorous: clear intonation rules, explicit numeric stress targets, well-curated stress-pair drills, and transparent author-notes about pedagogical exceptions. The v1.2.0 review-and-lock cycle cleaned up the internal contradiction about WH-questions and the disputed `мука` pair. Recommend **LOCK_NOW**.
