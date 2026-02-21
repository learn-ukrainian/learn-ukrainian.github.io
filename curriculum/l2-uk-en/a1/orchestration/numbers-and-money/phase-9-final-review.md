Now I have all the data I need for a thorough adversarial review.

---

## Phase 9: Final QA Review — numbers-and-money

### Issues Found

**Issue 1 (Pedagogical — SIGNIFICANT): Misleading "16" explanation**
- **Location**: `numbers-and-money.md` line 85
- **Text**: `(Notice: the 'т' from 'шість' drops out for easier pronunciation)`
- **Problem**: This is factually misleading. The word is spelled **шістнадцять** — the letter **т IS present** in writing. What drops from the spelling is the **soft sign ь** (шість → шіст-). In pronunciation, the cluster -стн- simplifies and the т becomes silent, but the text implies it disappears entirely, which will cause learners to misspell the word as *шіснадцять.
- **Severity**: High — directly causes spelling errors.

**Issue 2 (IPA inconsistency): п'ять transcription**
- **Location**: `numbers-and-money.md` line 59
- **Text**: `[pjatʲ]` uses plain `a`
- **Problem**: Every other transcription in the module uses `ɑ` for Ukrainian а (e.g., п'ятнадцять [pjɑtˈnɑdt͡sʲɑtʲ], п'ятдесят [pjɑtdɛˈsʲɑt]). This is an internal inconsistency.

**Issue 3 (Pedagogical): Table headers break Zone abstraction**
- **Location**: `numbers-and-money.md` lines 233-237
- **Text**: Column header `Відмінок` with raw values `Nominative Sg`, `Nominative Pl`, `Genitive Pl`
- **Problem**: The module beautifully introduces "Zone 1/2/3" to shield A1 learners from Latin grammar terminology. The summary table then reverts to raw `Nominative Sg/Pl`, `Genitive Pl` without Zone labels, breaking the scaffolding. The Green Team review also flagged this.

**Issue 4 (Vocab IPA — ERROR): коштувати stress wrong**
- **Location**: `vocabulary/numbers-and-money.yaml` line 49
- **Text**: `'[ˈkɔʃtuʋɑtɪ]'` — stress on first syllable
- **Problem**: The stress in коштува́ти falls on the penultimate syllable -ва-: `[kɔʃtuˈʋɑtɪ]`. This is an incorrect stress placement.

**Issue 5 (Vocab IPA inconsistency): здача vowels**
- **Location**: `vocabulary/numbers-and-money.yaml` line 65
- **Text**: `'[ˈzdat͡ʃa]'` — uses plain `a`
- **Problem**: Should use `ɑ` for consistency with the module: `[ˈzdɑt͡ʃɑ]`. The prose at line 334 correctly uses `[ˈzdɑt͡ʃɑ]`.

**Minor notes (not fixing — follow project conventions):**
- `[!observe]` callout: used in 83+ A1 files — this is a valid project convention, not an error. The Green Team review was wrong about this.
- Unjumble without punctuation: all A1 unjumble activities omit punctuation. "Ні дякую я зі своїм" follows convention.
- No Russianisms detected. No Russian characters. No forward grammar references beyond scope. All factual claims verified (1996 currency introduction, 2004 ₴ symbol adoption, proverb is authentic). No LLM purple prose beyond tolerance.

---

### Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/numbers-and-money.md
---OLD---
*   **16 — шістнадцять** [ʃisˈnɑdt͡sʲɑtʲ] (Notice: the 'т' from 'шість' drops out for easier pronunciation)
---NEW---
*   **16 — шістнадцять** [ʃisˈnɑdt͡sʲɑtʲ] (Notice: the soft sign 'ь' from 'шість' drops in spelling; the 'т' is written but often silent in speech)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/numbers-and-money.md
---OLD---
*   **5 — п'ять** [pjatʲ]. Це п'ять.
---NEW---
*   **5 — п'ять** [pjɑtʲ]. Це п'ять.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/numbers-and-money.md
---OLD---
| Number (End digit) | Form of "One/Two" | Відмінок | Приклад (Гривня) | Приклад (Копійка) |
| :--- | :--- | :--- | :--- | :--- |
| **1** (1, 21, 31...) | одна | Nominative Sg | **21 гривня** | **1 копійка** |
| **2, 3, 4** (22, 33...) | два/дві | Nominative Pl | **22 гривні** | **2 копійки** |
| **5, 6... 9, 0** (also 11-19) | п'ять, шість... | Genitive Pl | **25 гривень** | **5 копійок** |
---NEW---
| Number (End digit) | Form of "One/Two" | Zone / Відмінок | Приклад (Гривня) | Приклад (Копійка) |
| :--- | :--- | :--- | :--- | :--- |
| **1** (1, 21, 31...) | одна | Zone 1 (Називний однини) | **21 гривня** | **1 копійка** |
| **2, 3, 4** (22, 33...) | два/дві | Zone 2 (Називний множини) | **22 гривні** | **2 копійки** |
| **5, 6... 9, 0** (also 11-19) | п'ять, шість... | Zone 3 (Родовий множини) | **25 гривень** | **5 копійок** |
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/vocabulary/numbers-and-money.yaml
---OLD---
- ipa: '[ˈkɔʃtuʋɑtɪ]'
  lemma: коштувати
---NEW---
- ipa: '[kɔʃtuˈʋɑtɪ]'
  lemma: коштувати
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/vocabulary/numbers-and-money.yaml
---OLD---
- ipa: '[ˈzdat͡ʃa]'
  lemma: здача
---NEW---
- ipa: '[ˈzdɑt͡ʃɑ]'
  lemma: здача
===FIX_END===

---

### Review Summary

| Check | Result |
|-------|--------|
| Russianisms | CLEAN |
| Russian characters (ы, э, ё, ъ) | CLEAN |
| IPA accuracy (ʋ for В, tie bars) | 1 inconsistency fixed (п'ять) |
| Gender/case agreement | CORRECT throughout |
| Plan compliance (sections) | All 4 sections present |
| Plan compliance (vocabulary) | All 8 required + 6 recommended covered |
| Plan compliance (objectives) | All 4 mapped to self-check questions |
| Activity correctness | All answers verified correct |
| Unjumble word arrays | All words present in answers |
| Fill-in grammaticality | All produce grammatical sentences |
| Factual accuracy | All claims verified (dates, etymology, proverb) |
| LLM artifacts | None beyond tolerance |
| Word target (2000) | Met |

===VERDICT===
APPROVE
===END_VERDICT===