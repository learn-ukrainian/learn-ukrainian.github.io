# Plan Review: sounds-letters-and-hello

**Track:** a1 | **Sequence:** 1 | **Version:** 1.6.2 | **Lifecycle:** locked
**Verdict:** NEEDS FIXES (MEDIUM only; CRITICAL gates clean)
**Authority:** `docs/l2-uk-en/state-standard-2024-mapping.yaml` — A1 §4.1 (phonetics: alphabet §4.1.1, soft_sign §4.1.3, vowels/consonants §4.1.4, stress §4.1.5, euphony §4.1.7); A1 §4.2.4.2 (imperative — 2nd person only at A1).

## Rule Compliance
| Check | Status | Details |
|-------|--------|---------|
| word_target | PASS | Plan: 1200 = Config A1: 1200 (`scripts/audit/config.py:666`) |
| section_budgets | PASS | Sum = 300+250+250+250+150 = 1200 (exact match, 0% deviation) |
| required_fields | PASS | All present: module, level, sequence, slug, version, title, subtitle, focus, pedagogy, word_target, objectives, content_outline, vocabulary_hints, activity_hints, grammar, register |
| version_string | PASS | `version: 1.6.2` parses as string per YAML (3-component dotted form) |
| no Latin in Cyrillic | PASS | Latin-in-Cyrillic homoglyph scan clean (per locked review_notes); confirmed by manual reading |

## State Standard Alignment
| Grammar Topic | In Standard? | Standard Level | Plan Level | Status |
|--------------|-------------|----------------|------------|--------|
| Alphabet (33 letters / 38 sounds split) | YES (§4.1.1) | A1 | A1 | PASS |
| Голосні/приголосні | YES (§4.1.4) | A1 | A1 | PASS |
| Soft sign (Ь) | YES (§4.1.3) | A1 | A1 | PASS (light intro, deep dive in M3) |
| Stress (наголос) | YES (§4.1.5) | A1 | A1 | PASS (light intro, deep dive in M4) |
| Euphony (у/в, і/й) | YES (§4.1.7) | A1 | A1 | PASS |
| Iotated vowels (Я Ю Є Ї) — light intro | Implicit (§4.1.4) | A1 | A1 | PASS (deep dive in M2) |
| Прочитаймо (1pl perfective imperative) | NO at A1 | A2 (§4.2.3.2 1pl `читаймо`) | A1 | **MEDIUM** — see issues |

## Grammar Verification (Textbook RAG)
| Concept | Textbook Source | Correct? | Notes |
|---------|----------------|----------|-------|
| «Звуки чуємо й вимовляємо, а букви бачимо й пишемо» | Заболотний 5 кл. с.83 (cited in plan) | YES | Canonical pedagogical formula; matches NUS practice |
| 33 letters / 38 sounds | Заболотний 5 кл. с.83 | YES | Standard A1 framing |
| 10 vowel letters / 6 vowel sounds | Standard NUS framing | YES | Letters: А О У Е И І Я Ю Є Ї → sounds: [а о у е и і] |
| Ь — no sound, softens preceding consonant | Захарійчук 1 кл. с.13–15 | YES | Confirmed standard pedagogy |
| Щ = [шч] always | Standard | YES | Correct |
| Ґ = [g] vs Г = [ɦ] | Standard | YES | Fix in v1.5.1 removed "uniquely Ukrainian" overstatement — correctly resolved |

## Vocabulary Verification (VESUM)
| Word | VESUM | Notes |
|------|-------|-------|
| ирій (key word for И) | FOUND (noun, 2 matches) | Real Ukrainian word (mythological paradise), but **LOW**: very rare for A1 — most NUS bukvars use `іній` or `Україна`/`лина` |
| ґудзик (key word for Ґ) | FOUND | OK |
| їжак (Ї) | FOUND | OK |
| юшка (Ю) | FOUND | OK |
| Прочитаймо (1pl imp) | NOT FOUND as form; `читаймо` confirmed as 1pl imperative of `читати` | Morphologically valid but A2-scope per State Standard §4.2.3.2 |
| мама / молоко / тато / око / дім / ніс / сон | FOUND (all) | OK |
| Greetings as chunks: Добрий день / Доброго ранку / Добрий вечір / До побачення / На все добре | Components verified; chunks treated as multi-word units — OK |
| Радий/Рада тебе бачити | Gender pair correct; both forms confirmed in VESUM as adj `радий` (m/f) | OK — pedagogically appropriate for first gender exposure |

## Issues Found

### CRITICAL (must fix before build)
None.

### HIGH (should fix before build)
None.

### MEDIUM (fix if possible)
1. **`Прочитаймо «Привіт» по літерах»** (content_outline[3].points[3]) — 1pl perfective imperative. Per State Standard 2024 §4.2.3.2, A1 imperative scope is **2nd person only**; 1pl forms (`читаймо`, `прочитаймо`) belong to A2. The plan uses this in author/teacher meta-language ("let's read") rather than as taught grammar, but the writer may render it in module prose and inadvertently model an A2 form before the learner has seen any imperative paradigm. Suggested fix: replace with a 2nd-person framing such as `Прочитай «Привіт» по літерах` (2sg imperative) or move the verb out of the meta-instruction.
2. **`ирій` as key word for И** in vocabulary_hints (recommended). Word exists in VESUM but is poetic/mythological and extremely low-frequency. Most NUS-track A1 bukvars pair И with `іній`, `лина`, `Україна`, or even no key word (И is rarely word-initial). Suggested fix: replace with `іній` (frost — high-frequency, concrete, fits the literacy alphabet pattern).

### LOW (informational)
1. The `pronunciation_videos.vowels.О` entry is `null`. The module teaches all six vowel sounds; the missing О video is the only gap among the basics. Note for future fix or local recording.
2. Plan teaches all 33 letters in vocabulary_hints (33 alphabet entries) — high count is intentional per `letter_module: true` flag and `#1550` plan_fix. This is appropriate but means activity-count gates should be calibrated separately (already handled in `scripts/audit/config.py` per the letter-module exception class).
3. Grammar item "Привітання як неподільні лексичні чанки" overlaps with the soft-sign / iotated material that gets a full module in M3. Acceptable as light intro per phase staging.

## Suggested Fixes
```yaml
# content_outline[3].points[3] — replace `Прочитаймо` with 2sg form
- 'Прочитай «Привіт» по літерах — твій перший звуковий аналіз: П [п] приголосний + р [р] приголосний + и [и] голосний + в [в] приголосний + і [і] голосний + т [т] приголосний...'

# vocabulary_hints.recommended (in the 33-letter alphabet block)
# old:
- word: И
  key_word: ирій
# new:
- word: И
  key_word: іній
```

## Verdict
Plan is structurally sound and well-grounded in NUS textbook authorities. Two MEDIUM linguistic issues (out-of-scope 1pl imperative and obscure key word for И). Recommend **NEEDS_FIX** before next build — both are 1-line YAML edits, not pedagogical rewrites.
