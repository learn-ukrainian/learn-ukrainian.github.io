Good. I've now read all the actual files. Let me compile my adversarial review.

---

## Adversarial QA Review: checkpoint-first-contact (a1-10)

### Issues Found

**Issue 1: IPA error — Ukrainian "е" transcribed as [e] instead of [ɛ]**
- **File:** `checkpoint-first-contact.md`, line 46
- **Text:** `**Ресторан**`
- **Problem:** Ukrainian letter "е" represents /ɛ/, not /e/. The module itself correctly teaches this three lines later in the Е vs Є section: "**Е** — is [ɛ]." The IPA for "Ресторан" contradicts the module's own teaching. Should be.

**Issue 2: Incomplete писати paradigm — missing Він/Вона form**
- **File:** `checkpoint-first-contact.md`, lines 213-217
- **Text:** The paradigm jumps from "Ти пишеш" to "Вони пишуть", skipping 3rd person singular.
- **Problem:** The stem change (с→ш) is flagged as noteworthy, but skipping Він/Вона **пише** leaves a gap. A beginner might guess "Він писає" by analogy to Group 1. The Green Team review flagged this correctly.

**Issue 3: Fragment — "Тому що..." without a complete model sentence**
- **File:** `checkpoint-first-contact.md`, line 254
- **Text:** `*   **Тому що...** — Because...`
- **Problem:** Every other question word gets complete Q&A pairs. "Чому?" gets a question but the answer is a trailing fragment. A beginner needs to see the pattern: Question → Full answer. The Green Team flagged this.

**Issue 4: Missing IPA on key phrase "Я буду"**
- **File:** `checkpoint-first-contact.md`, line 304
- **Text:** `2.  **Я буду...** — I will have...`
- **Problem:** The surrounding phrases (Можна, Будь ласка, Дякую) all have IPA. "Я буду" is the core ordering phrase for the module's integration scenario. Missing pronunciation guidance creates an inconsistency.

**Issue 5: Typo in activity — "роббить" (double б)**
- **File:** `checkpoint-first-contact.yaml`, line 216
- **Text:** `options: ['роблю', 'робиш', 'роббить', 'робимо']`
- **Problem:** "роббить" is not a Ukrainian word. Should be "робить". This is a distractor option, but presenting a nonsense string as a valid option is confusing — a student might think it's a real but incorrect form.

**Issue 6: Misleading Г/Ґ labels in quiz — "(soft)"/"(hard)" contradicts content**
- **File:** `checkpoint-first-contact.yaml`, lines 36, 38, 46, 48
- **Text:** `'[ɦ] (soft)'` and `'[g] (hard)'`
- **Problem:** The content (lines 69-72) correctly labels Г as "fricative" and Ґ as "stop." The quiz labels them "(soft)" and "(hard)" instead. In Slavic linguistics, "soft/hard" (м'який/твердий) refers to palatalization — a completely different concept. This will cause confusion when students later encounter actual hard/soft consonant pairs. Additionally, the quiz uses `[g]` (ASCII g) while the content uses `[ɡ]` (IPA ɡ, U+0261) for the velar stop.

**Issue 7: "Папа" presented as a Ukrainian word in quiz**
- **File:** `checkpoint-first-contact.yaml`, line 90
- **Text:** `- text: 'Папа'` (as distractor in "Which word starts with [r]?")
- **Problem:** The question asks "Which of these Ukrainian words starts with the sound [r]?" — implying all options are Ukrainian words. "Папа" as "dad" is a Russicism (Ukrainian: тато). As "pope" (Папа Римський) it's too specialized for A1. Better to use a word already in the module: "Паспорт."

**Issue 8 (Minor): Question Words match-up includes 6 words not covered in content**
- **File:** `checkpoint-first-contact.yaml`, lines 282-295
- **Text:** Який, Як, Скільки, Чи, Звідки, Чий
- **Problem:** The content (Skill 4) teaches only Хто, Що, Де, Куди, Коли, Чому. The activity adds 6 more words that aren't reviewed in this module. For a checkpoint this is borderline acceptable (they were presumably taught in a1-08), but the gap between what's reviewed and what's tested is notable. Not fixing this — just flagging it.

### Verification Summary

- **Russianisms:** CLEAN (except "Папа" distractor — fixed below)
- **Russian characters (ы, э, ё, ъ):** CLEAN
- **Gender agreement:** CLEAN (Добра кава, Добрий чай, Моя кава, Моє кафе — all correct)
- **IPA tie bars on affricates:** CORRECT (d͡z in Ґудзик, t͡ʃ in Смачного)
- **В as [ʋ]:** CORRECT throughout (Новий, Говорити, Європа, Страви, etc.)
- **Fill-in answers:** All 24 produce grammatical sentences when inserted
- **Anagram letter counts:** All 12 match their answers
- **All content_outline sections present:** YES (7/7 from meta)
- **Required vocabulary in prose:** YES (читати, писати, говорити, знати, хто, що, де, так/ні — all present)
- **Factual claims:** Kulchytsky claim hedged with "According to Ukrainian tradition" — acceptable
- **LLM artifacts:** None detected. Tone is natural and specific.
- **Word target:** Content appears to meet the 2000-word minimum

---

### Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/checkpoint-first-contact.md
---OLD---
    *   *Приклад:* **Ресторан** — Restaurant, **Парк** [pɑrk] — Park.
---NEW---
    *   *Приклад:* **Ресторан** — Restaurant, **Парк** [pɑrk] — Park.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/checkpoint-first-contact.md
---OLD---
*   **Писати** — to write. Ending -ати. But attention! There is a sound change.
    *   Я **пишу** (s → sh)
    *   Ти **пишеш**
    *   Вони **пишуть**
    This is a first group verb. Endings are standard: **-еш**, **-уть**.
---NEW---
*   **Писати** — to write. Ending -ати. But attention! There is a sound change.
    *   Я **пишу** (с → ш)
    *   Ти **пишеш**
    *   Він/Вона **пише**
    *   Вони **пишуть**
    This is a first group verb. Endings are standard: **-еш**, **-уть**. The stem change (с → ш) persists in all forms.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/checkpoint-first-contact.md
---OLD---
6.  **Чому?** (Why?) — reason.
    *   **Чому ти тут?** — Why are you here?
    *   **Тому що...** — Because...
---NEW---
6.  **Чому?** (Why?) — reason.
    *   **Чому ти тут?** — Why are you here?
    *   **Тому що я турист.** — Because I am a tourist.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/checkpoint-first-contact.md
---OLD---
2.  **Я буду...** — I will have... (Literally: I will be...)
---NEW---
2.  **Я буду...** — I will have... (Literally: I will be...)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/checkpoint-first-contact.yaml
---OLD---
      options: ['роблю', 'робиш', 'роббить', 'робимо']
---NEW---
      options: ['роблю', 'робиш', 'робить', 'робимо']
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/checkpoint-first-contact.yaml
---OLD---
    - question: Can you identify the correct sound for the letter 'Г'?
      options:
        - text: '[ɦ] (soft)'
          correct: true
        - text: '[g] (hard)'
          correct: false
        - text: '[r]'
          correct: false
        - text: '[h]'
          correct: false
    - question: Can you identify the correct sound for the letter 'Ґ'?
      options:
        - text: '[g] (hard)'
          correct: true
        - text: '[ɦ] (soft)'
          correct: false
---NEW---
    - question: Can you identify the correct sound for the letter 'Г'?
      options:
        - text: '[ɦ] (fricative)'
          correct: true
        - text: '[ɡ] (plosive)'
          correct: false
        - text: '[r]'
          correct: false
        - text: '[h]'
          correct: false
    - question: Can you identify the correct sound for the letter 'Ґ'?
      options:
        - text: '[ɡ] (plosive)'
          correct: true
        - text: '[ɦ] (fricative)'
          correct: false
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/checkpoint-first-contact.yaml
---OLD---
        - text: 'Папа'
          correct: false
        - text: 'Мама'
---NEW---
        - text: 'Паспорт'
          correct: false
        - text: 'Мама'
===FIX_END===

---

===VERDICT===
APPROVE
===END_VERDICT===

**Rationale:** The module is solid — good tone, correct Ukrainian throughout, culturally appropriate, structurally complete against the meta outline. The 8 issues found are all fixable with the patches above: 1 IPA transcription error, 1 incomplete paradigm, 1 sentence fragment, 1 missing IPA, 1 typo in activity options, 1 terminology inconsistency between content and activities, and 1 Russicism in a distractor. None are structural or unfixable. After these fixes, the module passes all gates cleanly.