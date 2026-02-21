## Adversarial QA Review: being-and-becoming (a2-06)

Word count: 3278 (target: 3000) — PASS.
Russianisms scan: CLEAN.
Russian characters (ы, э, ё, ъ): CLEAN.
Plan sections: All 4 present (Вступ, Презентація, Практика, Діалоги) — PASS.
Activity variety: 12 types — PASS.

---

### Issues Found

**Issue 1: Dialogue 1 gender agreement error** (content:387)
`**Марина:** (сміється) Так, вгадала.`
Oleg asks "Ти дизайнерка?" — he is the one guessing. Marina's confirmation should agree with *his* gender: "вгадав" (masculine past tense), not "вгадала." As written, "вгадала" means "(I) guessed" which is nonsensical in this context.

**Issue 2: History section title capitalization** (content:274)
`Він **був Великим князем Київським**.`
Per Ukrainian orthographic rules, ranks/titles are lowercase in running text: великий князь, гетьман, президент. The same file correctly lowercases "гетьманом" for Khmelnytskyi. This is an inconsistency.

**Issue 3: Unjumble 5 — capitalization mismatch + missing comma** (activities:261-262)
- words: `['Ми', ... 'я', 'що']` → answer: `'Я впевнений що ми будемо дуже хорошими колегами'`
- "Ми" is capitalized in words but lowercase in answer; "я" is lowercase in words but capitalized in answer. This creates a confusing word bank where "Ми" appears to be the sentence opener.
- Ukrainian grammar requires a comma before "що" in subordinate clauses: "Я впевнений**,** що..."
- **Fix approach**: Replace with simpler sentence to avoid both issues.

**Issue 4: Cloze activity — 8 orphaned blanks** (activities:443-466)
The passage contains only `{{1}}` through `{{6}}`, but 14 blanks are defined. Blanks 7–14 (жінкою, дизайнеркою, успішною, колегою, студенткою, подругою, сестрою, мамою) are never referenced in the passage. These are dead data that will cause rendering bugs or silent failures.

**Issue 5: Vocabulary IPA inconsistency** (vocabulary:91)
`волонтер` has IPA `"vɔlɔnˈtɛr"` using /v/. All other entries use /ʋ/ for Ukrainian "в" (фахівець → `fɑxiˈʋɛt͡sʲ`, працювати → `prɑt͡sʲuˈʋɑtɪ`, тестувальник → `tɛstuˈʋɑlʲnɪk`). Ukrainian "в" before a vowel is labiodental approximant /ʋ/, not labiodental fricative /v/.

**Issue 6: Vocabulary duplicate entries** (vocabulary:5-12, 21-24, 29-32)
Three terms appear twice with only capitalization difference: називний/Називний, орудний/Орудний, множина/Множина. Builder artifact — removing duplicates.

---

### Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a2/being-and-becoming.md
---OLD---
**Марина:** (сміється) Так, вгадала. Я **працюю графічною дизайнеркою**. Малюю логотипи. А ти?
---NEW---
**Марина:** (сміється) Так, вгадав. Я **працюю графічною дизайнеркою**. Малюю логотипи. А ти?
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/being-and-becoming.md
---OLD---
Він **був Великим князем Київським**. Він охрестив Русь у 988 році. Він був могутнім правителем і мудрим політиком.
---NEW---
Він **був великим князем київським**. Він охрестив Русь у 988 році. Він був могутнім правителем і мудрим політиком.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/activities/being-and-becoming.yaml
---OLD---
    - words: ['Ми', 'колегами', 'будемо', 'дуже', 'хорошими', 'впевнений', 'я', 'що']
      answer: 'Я впевнений що ми будемо дуже хорошими колегами'
---NEW---
    - words: ['Ми', 'будемо', 'дуже', 'хорошими', 'колегами', 'обов'язково']
      answer: 'Ми обов'язково будемо дуже хорошими колегами'
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/activities/being-and-becoming.yaml
---OLD---
    - id: 6
      answer: 'творчою'
      options: ['творчою', 'творча', 'творчій', 'творчу']
    - id: 7
      answer: 'жінкою'
      options: ['жінкою', 'жінка', 'жінки', 'жінку']
    - id: 8
      answer: 'дизайнеркою'
      options: ['дизайнеркою', 'дизайнерка', 'дизайнерки', 'дизайнерку']
    - id: 9
      answer: 'успішною'
      options: ['успішною', 'успішна', 'успішній', 'успішну']
    - id: 10
      answer: 'колегою'
      options: ['колегою', 'колега', 'колеги', 'колегу']
    - id: 11
      answer: 'студенткою'
      options: ['студенткою', 'студентка', 'студентки', 'студентку']
    - id: 12
      answer: 'подругою'
      options: ['подругою', 'подруга', 'подруги', 'подругу']
    - id: 13
      answer: 'сестрою'
      options: ['сестрою', 'сестра', 'сестри', 'сестру']
    - id: 14
      answer: 'мамою'
      options: ['мамою', 'мама', 'мами', 'маму']
---NEW---
    - id: 6
      answer: 'творчою'
      options: ['творчою', 'творча', 'творчій', 'творчу']
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/vocabulary/being-and-becoming.yaml
---OLD---
- term: називний
  ipa: "nɑzɪu̯ˈnɪj"
  translation: "Nominative"
  pos: adjective
- term: Називний
  ipa: "nɑzɪu̯ˈnɪj"
  translation: "Nominative"
  pos: adjective
---NEW---
- term: називний
  ipa: "nɑzɪu̯ˈnɪj"
  translation: "Nominative"
  pos: adjective
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/vocabulary/being-and-becoming.yaml
---OLD---
- term: орудний
  ipa: "ɔˈrudnɪj"
  translation: "Instrumental"
  pos: adjective
- term: Орудний
  ipa: "ɔˈrudnɪj"
  translation: "Instrumental"
  pos: adjective
---NEW---
- term: орудний
  ipa: "ɔˈrudnɪj"
  translation: "Instrumental"
  pos: adjective
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/vocabulary/being-and-becoming.yaml
---OLD---
- term: множина
  ipa: "mnɔʒɪˈnɑ"
  translation: "plural"
  pos: noun
- term: Множина
  ipa: "mnɔʒɪˈnɑ"
  translation: "plural"
  pos: noun
---NEW---
- term: множина
  ipa: "mnɔʒɪˈnɑ"
  translation: "plural"
  pos: noun
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/vocabulary/being-and-becoming.yaml
---OLD---
- term: волонтер
  ipa: "vɔlɔnˈtɛr"
  translation: "volunteer"
  pos: noun
---NEW---
- term: волонтер
  ipa: "ʋɔlɔnˈtɛr"
  translation: "volunteer"
  pos: noun
===FIX_END===

---

### Observations (not requiring fixes)

**Plan vocabulary gap**: The plan's `vocabulary_hints.required` lists ставати, служити, залишатися, виявитися, здаватися — all absent from content. The meta correctly narrows scope to 3 core verbs (бути, стати, працювати), which is appropriate for A2. This is a plan-meta alignment issue, not a content defect.

**"Я є студент" (content:23)**: Uses explicit copula for pedagogical contrast with past/future forms. Slightly unnatural for spoken Ukrainian but justified — the module addresses Zero Copula at line 116.

**учитель/вчитель inconsistency**: Content uses "вчитель" throughout; activities use "учитель" in some places. Both forms are valid per 2019 orthography (учитель = formal, вчитель = colloquial). Not an error, but worth noting for future consistency passes.

### Strengths

- The **Costume Analogy** and **Nominative Trap** are genuinely excellent pedagogical devices — memorable and accurate.
- The **"як" debunking** is thorough and correctly addresses the #1 L1 interference error for English/German speakers.
- **Feminitives section** is factually correct (2019 orthography, not "new" but restored tradition) and culturally well-calibrated.
- **Historical figures** are factually accurate: Zelenskyy 2019 ✓, Khmelnytskyi 1648 & 5-hryvnia note ✓, Skovoroda epitaph ✓, Krushelnytska & Madama Butterfly ✓.
- No LLM artifacts detected: no purple prose openers, no "Це не просто X, а Y" pattern, no invented statistics.

---

===VERDICT===
APPROVE
===END_VERDICT===