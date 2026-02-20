Now I have all the context I need. Let me compile my full adversarial review.

---

## Phase 9: Adversarial QA Review — description-adverbs

### Issues Found

**Issue 1 — CRITICAL: Conjugation error «живіш»**
- **File:** `description-adverbs.md`, line 308
- **Text:** «Ти живіш спокійно, а я живу активно.»
- **Problem:** «живіш» is not a valid Ukrainian conjugation. The verb «жити» conjugates: я живу, ти живеш, він/вона живе. The correct 2nd person singular is «живеш».
- **Severity:** Critical — teaches an incorrect form to A1 learners.

**Issue 2 — CRITICAL: Conjugation error «п'ю» (wrong person)**
- **File:** `description-adverbs.md`, line 346
- **Text:** «Він снідає повільно і п'ю каву.»
- **Problem:** «п'ю» is 1st person singular ("I drink"). The subject is «він» (he), requiring 3rd person singular «п'є».
- **Severity:** Critical — introduces a basic conjugation error in a reading passage beginners will model.

**Issue 3 — IPA ERROR: «легко» transcribed with [h] instead of [x]**
- **File:** `description-adverbs.md`, line 92
- **Text:** `[ˈlɛhkɔ]`
- **Problem:** Ukrainian /ɦ/ devoices to [x] (voiceless velar fricative) before voiceless /k/, neutralizing with /x/ (= "х"). The transcription uses [h] (voiceless glottal), which is incorrect. Should be `[ˈlɛxkɔ]`.

**Issue 4 — IPA ERROR: «довго» transcribed with [h] instead of [ɦ]**
- **File:** `description-adverbs.md`, line 307
- **Text:** `[ˈdɔu̯hɔ]`
- **Problem:** Ukrainian "г" is /ɦ/ (voiced glottal fricative). In "довго", the г is between voiced sounds ([u̯] and [ɔ]), so it stays voiced [ɦ]. The transcription uses [h] (voiceless glottal). Should be `[ˈdɔu̯ɦɔ]`.

**Issue 5 — Misleading section header "Хто vs Як"**
- **File:** `description-adverbs.md`, line 46
- **Text:** `### Візуальна схема: Хто vs Як`
- **Problem:** The section contrasts «Який?» (What kind?) with «Як?» (How?). The header says «Хто» (Who?), which is unrelated. Should be «Який vs Як» to match the content and the table below it.

**Issue 6 — Numbered list skips #15**
- **File:** `description-adverbs.md`, lines 394–396
- **Text:** `14. Ми працюємо **активно**.` then `16. Ми бігаємо **вранці**.`
- **Problem:** Number 15 is missing from the reading practice list. Jumps 14 → 16.

**Issue 7 — Activity uses untaught vocabulary «гучний/гучно»**
- **File:** `description-adverbs.yaml`, lines 39–41
- **Text:** `"Музика гучна. Вона грає {{answer}}."` with answer "гучно" and options `["гучно", "гучна", "гучний", "гучне"]`
- **Problem:** The module teaches «голосний → голосно» (line 85–87) as the word for "loud". The activity tests «гучний → гучно», which is a synonym but is never introduced in the prose. A1 learners will encounter an untaught word in an exercise. Should use «голосний/голосно» for consistency.

**Issue 8 — Vocabulary YAML: wrong root format + missing IPA**
- **File:** `description-adverbs.yaml` (vocabulary)
- **Problem:** All other vocabulary files in the project use a bare list at root with `ipa` fields. This file uses an `items:` dictionary wrapper and has no IPA transcriptions. Non-standard format.

---

### Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/description-adverbs.md
---OLD---
### Візуальна схема: Хто vs Як
---NEW---
### Візуальна схема: Який vs Як
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/description-adverbs.md
---OLD---
*   **легкий** (easy/light) → **легко** [ˈlɛhkɔ] (easily)
---NEW---
*   **легкий** (easy/light) → **легко** [ˈlɛxkɔ] (easily)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/description-adverbs.md
---OLD---
Я люблю спати **довго** [ˈdɔu̯hɔ] (long/late).
---NEW---
Я люблю спати **довго** [ˈdɔu̯ɦɔ] (long/late).
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/description-adverbs.md
---OLD---
Ти живіш спокійно, а я живу активно.
---NEW---
Ти живеш спокійно, а я живу активно.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/description-adverbs.md
---OLD---
Він снідає **повільно** і п'ю каву.
---NEW---
Він снідає **повільно** і п'є каву.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/description-adverbs.md
---OLD---
14. Ми працюємо **активно**.
16. Ми бігаємо **вранці**.
17. Вони живуть **спокійно**.
18. Я читаю **уважно**.
---NEW---
14. Ми працюємо **активно**.
15. Ми бігаємо **вранці**.
16. Вони живуть **спокійно**.
17. Я читаю **уважно**.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/description-adverbs.yaml
---OLD---
    - sentence: "Музика гучна. Вона грає {{answer}}."
      answer: "гучно"
      options: ["гучно", "гучна", "гучний", "гучне"]
---NEW---
    - sentence: "Музика голосна. Вона грає {{answer}}."
      answer: "голосно"
      options: ["голосно", "голосна", "голосний", "голосне"]
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/vocabulary/description-adverbs.yaml
---OLD---
items:
  - lemma: "добре"
    translation: "well"
    pos: "adverb"
    notes: "Irregular adverb from 'добрий' (good)"
  - lemma: "погано"
    translation: "badly/poorly"
    pos: "adverb"
    example: "Я погано чую. (I hear poorly.)"
  - lemma: "швидко"
    translation: "quickly/fast"
    pos: "adverb"
    example: "Він бігає швидко."
  - lemma: "повільно"
    translation: "slowly"
    pos: "adverb"
    example: "Говоріть повільно, будь ласка."
  - lemma: "завжди"
    translation: "always"
    pos: "adverb"
    notes: "Stress on the second syllable: zav-ZHDY"
  - lemma: "часто"
    translation: "often"
    pos: "adverb"
  - lemma: "іноді"
    translation: "sometimes"
    pos: "adverb"
  - lemma: "ніколи"
    translation: "never"
    pos: "adverb"
    notes: "Requires 'не' before the verb"
  - lemma: "голосно"
    translation: "loudly"
    pos: "adverb"
  - lemma: "тихо"
    translation: "quietly"
    pos: "adverb"
  - lemma: "рідко"
    translation: "rarely"
    pos: "adverb"
  - lemma: "зазвичай"
    translation: "usually"
    pos: "adverb"
  - lemma: "легко"
    translation: "easily"
    pos: "adverb"
  - lemma: "важко"
    translation: "hard/with difficulty"
    pos: "adverb"
    example: "Мені важко це робити."
  - lemma: "дуже"
    translation: "very/really"
    pos: "adverb"
    notes: "Always placed BEFORE the word it modifies"
  - lemma: "активно"
    translation: "actively"
    pos: "adverb"
  - lemma: "рано"
    translation: "early"
    pos: "adverb"
  - lemma: "пізно"
    translation: "late"
    pos: "adverb"
  - lemma: "спокійно"
    translation: "calmly"
    pos: "adverb"
  - lemma: "уважно"
    translation: "attentively/carefully"
    pos: "adverb"
---NEW---
- ipa: '[ˈdɔbrɛ]'
  lemma: добре
  pos: adverb
  translation: well
  notes: "Irregular adverb from 'добрий' (good)"
- ipa: '[ˈpɔɦɑnɔ]'
  lemma: погано
  pos: adverb
  translation: badly/poorly
  example: "Я погано чую. (I hear poorly.)"
- ipa: '[ˈʃʋɪdkɔ]'
  lemma: швидко
  pos: adverb
  translation: quickly/fast
  example: "Він бігає швидко."
- ipa: '[pɔˈʋʲilʲnɔ]'
  lemma: повільно
  pos: adverb
  translation: slowly
  example: "Говоріть повільно, будь ласка."
- ipa: '[zɑu̯ˈʒdɪ]'
  lemma: завжди
  pos: adverb
  translation: always
  notes: "Stress on the second syllable"
- ipa: '[ˈt͡ʃɑstɔ]'
  lemma: часто
  pos: adverb
  translation: often
- ipa: '[ˈinɔdʲi]'
  lemma: іноді
  pos: adverb
  translation: sometimes
- ipa: '[nʲiˈkɔlɪ]'
  lemma: ніколи
  pos: adverb
  translation: never
  notes: "Requires 'не' before the verb"
- ipa: '[ˈɦɔlɔsnɔ]'
  lemma: голосно
  pos: adverb
  translation: loudly
- ipa: '[ˈtɪxɔ]'
  lemma: тихо
  pos: adverb
  translation: quietly
- ipa: '[ˈrʲidkɔ]'
  lemma: рідко
  pos: adverb
  translation: rarely
- ipa: '[zɑzʋɪˈt͡ʃɑj]'
  lemma: зазвичай
  pos: adverb
  translation: usually
- ipa: '[ˈlɛxkɔ]'
  lemma: легко
  pos: adverb
  translation: easily
- ipa: '[ˈʋɑʃkɔ]'
  lemma: важко
  pos: adverb
  translation: hard/with difficulty
  example: "Мені важко це робити."
- ipa: '[ˈduʒɛ]'
  lemma: дуже
  pos: adverb
  translation: very/really
  notes: "Always placed BEFORE the word it modifies"
- ipa: '[ɑkˈtɪu̯nɔ]'
  lemma: активно
  pos: adverb
  translation: actively
- ipa: '[ˈrɑnɔ]'
  lemma: рано
  pos: adverb
  translation: early
- ipa: '[ˈpʲiznɔ]'
  lemma: пізно
  pos: adverb
  translation: late
- ipa: '[spɔˈkʲijnɔ]'
  lemma: спокійно
  pos: adverb
  translation: calmly
- ipa: '[uˈʋɑʒnɔ]'
  lemma: уважно
  pos: adverb
  translation: attentively/carefully
===FIX_END===

---

### Review Summary

| Category | Issues | Severity |
|----------|--------|----------|
| Conjugation errors | 2 (живіш, п'ю) | Critical |
| IPA errors | 2 (легко [h→x], довго [h→ɦ]) | Moderate |
| Misleading header | 1 (Хто → Який) | Moderate |
| Numbering bug | 1 (skip #15) | Minor |
| Untaught vocab in activity | 1 (гучний → голосний) | Moderate |
| Vocabulary YAML format | 1 (wrapper + missing IPA) | Moderate |
| Russianisms | 0 | Clean |
| Russian characters | 0 | Clean |
| LLM artifacts | 0 | Clean |
| Plan compliance | Full | Pass |
| Factual accuracy | Verified | Pass |

**Green Team review correctly caught issues #1 and #2.** Issues #3–#8 are new findings from this adversarial pass.

All issues are fixable with the blocks above. After applying these 8 fixes, the module is pedagogically solid, linguistically accurate, and well-structured for A1 learners.

===VERDICT===
APPROVE
===END_VERDICT===