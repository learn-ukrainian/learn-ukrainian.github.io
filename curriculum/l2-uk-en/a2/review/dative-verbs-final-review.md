Good. The Grep confirms zero of the 9 missing required plan verbs appear in the prose. Now let me compile my full adversarial review.

---

## Deep Adversarial Review: dative-verbs (a2-03)

### Issues Found

---

**Issue 1: Error-correction activity — double error (CRITICAL)**
- **File:** `activities/dative-verbs.yaml`, line 185
- **Text:** `'Я дуже дякують тебе за подарунок.'`
- **Problem:** Subject "Я" requires "дякую" (1sg), not "дякують" (3pl). The intended *sole* error is "тебе" → "тобі", but the verb agreement bug creates a second, unintended error. A learner doing error-correction should find ONE error, not two. The Green Team flagged this identically.
- **Fix:** Change "дякують" → "дякую".

**Issue 2: Concept Before Use — співчувати in group-sort (CRITICAL)**
- **File:** `activities/dative-verbs.yaml`, line 104
- **Text:** `'співчувати'` listed in the Dative group
- **Problem:** "Співчувати" is never introduced, defined, or used in the lesson text. Learners cannot sort a word they've never seen. Plan `vocabulary_hints.required` includes it, but the prose never teaches it.
- **Fix:** Replace with "вірити" (taught in Group 1, §Вірити vs. Довіряти).

**Issue 3: Concept Before Use — личити in fill-in "Закінчення іменників" (CRITICAL)**
- **File:** `activities/dative-verbs.yaml`, line 172
- **Text:** `'Ця сукня дуже личить подруз___.'`
- **Problem:** "Личити" is never taught. The activity uses untaught vocabulary to test Dative endings. The г→з alternation is the pedagogical value here — keep it, but swap the verb.
- **Fix:** Replace with a sentence using "допомагати" that preserves the подруга→подрузі alternation.

**Issue 4: Concept Before Use — личити in fill-in "Займенники" (CRITICAL)**
- **File:** `activities/dative-verbs.yaml`, line 322
- **Text:** `'Це Олена. ___ дуже личить ця сукня.'`
- **Problem:** Same as above — "личити" untaught.
- **Fix:** Replace with "подобатися" (taught in Group 3).

**Issue 5: Unjumble capitalization mismatch (MEDIUM)**
- **File:** `activities/dative-verbs.yaml`, lines 226-227
- **Words array:** `['заважає', 'Музика', 'спати', 'нашим', 'сусідам', 'гучна']`
- **Answer:** `'Гучна музика заважає нашим сусідам спати'`
- **Problem:** Capital letter in the words array signals the sentence-initial word. `'Музика'` is capitalized (suggesting it starts the sentence), but the answer starts with `'Гучна'` (which is lowercase in the array). Learner will misidentify the first word.
- **Fix:** Swap caps: `'Гучна'` (capital) and `'музика'` (lowercase).

**Issue 6: IPA — missing tie bars on affricates (MEDIUM)**
- **File:** `vocabulary/dative-verbs.yaml`
- цукор: `[ˈt͡sukɔr]` → should be `[ˈt͡sukɔr]` (ц = /t͡s/)
- офіціант: `[ɔfʲit͡sʲiˈjɑnt]` → should be `[ɔfʲit͡sʲiˈjɑnt]` (ц = /t͡s/)
- щиро: `[ˈʃt͡ʃɪrɔ]` → should be `[ˈʃt͡ʃɪrɔ]` (щ contains /t͡ʃ/)

**Issue 7: Plan vocabulary compliance — 9 required verbs missing (MAJOR, cannot patch)**
- **File:** `dative-verbs.md` (entire module)
- **Missing from plan `vocabulary_hints.required`:** вибачати, пробачати, заздрити, симпатизувати, співчувати, личити, підходити, вистачати, бракувати
- **Root cause:** The meta `content_outline` (build instruction) never included a section for these emotional/state verbs. The plan-to-meta translation dropped them. The prose was built from the meta, so the verbs were never written.
- **Impact:** These verbs represent ~50% of the plan's required vocabulary. This is a rebuild-level issue, not a patch.
- **Note:** "Вибачте мені" appears in Dialogue 3 (line 496) as an incidental usage, but "вибачати" is never formally presented as a dative verb.

**Issue 8: Minor inconsistency — учителю vs вчителеві (COSMETIC, no fix needed)**
- Line 118 uses «Студенти дякують **учителю**.» (short Dative -у form)
- Drill 6 item 2 uses «Вона дякує **вчителеві**.» (long Dative -еві form)
- The module teaches -ові/-еві as preferred. Using -у before the drill that explains the preference is borderline — it could confuse or it could preview the distinction. Not blocking.

### Russianisms Check
- No instances of кушати, получати, приймати участь, слідуючий. Clean.
- "Тратить" in the proverb (line 521) is legitimate Ukrainian, not a Russicism.

### Russian Characters Check (ы, э, ё, ъ)
- None found. Clean.

### LLM Artifact Check
- No purple prose or grandiose openers
- No "Це не просто X, а Y" pattern
- No false statistics or invented percentages
- No folk etymology presented as fact
- The "bossy driver" analogy is original and pedagogically effective

### Factual Accuracy
- Toloka tradition: accurately described
- Volunteering since 2014/2022: accurate
- "Красно дякую" etymology: correct (красно = beautifully)
- Hand-on-heart gesture: legitimate cultural observation
- Proverb «Хто людям допомагає, той тратить час не марно»: authentic Ukrainian saying

---

## Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a2/activities/dative-verbs.yaml
---OLD---
    - sentence: 'Я дуже дякують тебе за подарунок.'
      error: 'тебе'
      answer: 'тобі'
      options: ['тобі', 'ти', 'тобою', 'вас']
      explanation: 'Дієслово "дякувати" вимагає Давального відмінка (Кому?), а не Знахідного.'
---NEW---
    - sentence: 'Я дуже дякую тебе за подарунок.'
      error: 'тебе'
      answer: 'тобі'
      options: ['тобі', 'ти', 'тобою', 'вас']
      explanation: 'Дієслово "дякувати" вимагає Давального відмінка (Кому?), а не Знахідного.'
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/activities/dative-verbs.yaml
---OLD---
    - name: 'Давальний (Кому?)'
      items:
        - 'допомагати'
        - 'дякувати'
        - 'заважати'
        - 'довіряти'
        - 'співчувати'
        - 'подобатися'
---NEW---
    - name: 'Давальний (Кому?)'
      items:
        - 'допомагати'
        - 'дякувати'
        - 'заважати'
        - 'довіряти'
        - 'вірити'
        - 'подобатися'
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/activities/dative-verbs.yaml
---OLD---
    - sentence: 'Ця сукня дуже личить подруз___.'
      answer: 'подрузі'
      options: ['подрузі', 'подругу', 'подруга', 'подругою']
      explanation: 'Подруга (жіночий рід) у Давальному відмінку має закінчення -і (г змінюється на з).'
---NEW---
    - sentence: 'Ми часто допомагаємо подруз___ з уроками.'
      answer: 'подрузі'
      options: ['подрузі', 'подругу', 'подруга', 'подругою']
      explanation: 'Подруга (жіночий рід) у Давальному відмінку має закінчення -і (г змінюється на з).'
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/activities/dative-verbs.yaml
---OLD---
    - sentence: 'Це Олена. ___ дуже личить ця сукня.'
      answer: 'Їй'
      options: ['Їй', 'Вона', 'Її', 'Нею']
      explanation: 'Олена (вона) -> Їй.'
---NEW---
    - sentence: 'Це Олена. ___ дуже подобається ця книга.'
      answer: 'Їй'
      options: ['Їй', 'Вона', 'Її', 'Нею']
      explanation: 'Олена (вона) -> Їй.'
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/activities/dative-verbs.yaml
---OLD---
    - words: ['заважає', 'Музика', 'спати', 'нашим', 'сусідам', 'гучна']
      answer: 'Гучна музика заважає нашим сусідам спати'
---NEW---
    - words: ['заважає', 'музика', 'спати', 'нашим', 'сусідам', 'Гучна']
      answer: 'Гучна музика заважає нашим сусідам спати'
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/vocabulary/dative-verbs.yaml
---OLD---
    ipa: [ˈt͡sukɔr]
---NEW---
    ipa: [ˈt͡sukɔr]
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/vocabulary/dative-verbs.yaml
---OLD---
    ipa: [ɔfʲit͡sʲiˈjɑnt]
---NEW---
    ipa: [ɔfʲit͡sʲiˈjɑnt]
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/vocabulary/dative-verbs.yaml
---OLD---
    ipa: [ˈʃt͡ʃɪrɔ]
---NEW---
    ipa: [ˈʃt͡ʃɪrɔ]
===FIX_END===

---

## Verdict

The module is tonally excellent, pedagogically sound for its covered verbs, culturally rich, and safe for A2 learners. The 8 fixes above resolve all activity-level errors (double error in error-correction, 3 Concept Before Use violations, 1 unjumble capitalization bug, 3 IPA tie bars).

**Remaining issue that cannot be patched:** The plan's `vocabulary_hints.required` lists 9 verbs (вибачати, пробачати, заздрити, симпатизувати, співчувати, личити, підходити, вистачати, бракувати) that are absent from the prose. This is a plan-to-meta translation gap — the meta `content_outline` never included a section for these verbs, so the builder never wrote them. Fixing this requires adding ~500 words of new content (a "Group 4: Emotional & State Verbs" section), which is a rebuild, not a patch. The automated audit passes because word count meets target; the gap is in plan vocabulary coverage.

===VERDICT===
NEEDS_WORK
===END_VERDICT===