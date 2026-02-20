## Adversarial QA Review — `past-passive-participles` (b2 #2)

### Issues Found

---

**Issue 1 — Typo (Critical)**
File: content, essay section
> «але **наній** видно сліди»

`наній` is a typographic merge of `на ній`. Existing review confirmed this.

---

**Issue 2 — Aspect mismatch in alternation table: "Губити" (Critical)**
File: content, §"Таблиця чергувань"
> `| Гу**б**ити | **б** → **бл** | Гу**бл**ений | Гублений час ніколи не повертається. |`

`Губити` is **imperfective**. Past passive participles are canonically formed from perfective verbs. `Гублений` from `губити` is a marginal, archaïc form. Should be perfective `Загубити → Загублений`.

---

**Issue 3 — Aspect mismatch in alternation table: "Ловити" (Critical)**
File: content, §"Таблиця чергувань"
> `| Ло**в**ити | **в** → **вл** | Вло**вл**ений |`

Infinitive `Ловити` is imperfective; the participle shown `Вловлений` comes from `Вловити` (perfective). The table shows two different verbs in the same row. Infinitive must be `Вловити`.

---

**Issue 4 — Scope violation: "вирішено" in content essay prompt (High)**
File: content, §"Есе: Етика реставрації"
> «Використайте слова: *відновлений, збережений, втрачений, пошкоджений, **вирішено**, залишений*»

The module SCOPE comment explicitly excludes «Безособові форми на -но/-то → b2-03». `Вирішено` is exactly such a form. Requiring students to use it in this module's essay is a forward-reference teaching trap. Must be removed from the required-words list.

---

**Issue 5 — Same scope violation in activities YAML essay-response prompt (High)**
File: activities YAML, essay-response item
Same `вирішено` appears in the YAML `prompt:` field. Must be removed there too.

---

**Issue 6 — Match-up activity: imperfective "писати" paired with perfective participle "написаний" (Medium)**
File: activities YAML, match-up "Від дієслова до дієприкметника"
> `left: писати / right: написаний`

The module prose itself demonstrates `писати → писаний` (the imperfective base form). Pairing `писати` with `написаний` (from `написати`, perfective) creates inconsistency and teaches students an incorrect derivation chain.

---

**Issue 7 — Match-up activity: imperfective "робити" paired with perfective participle "зроблений" (Medium)**
File: activities YAML, same match-up
> `left: робити / right: зроблений`

`Робити` is imperfective; `зроблений` derives from `зробити` (perfective). Same problem as Issue 6.

---

**Issue 8 — "Обернутий" presented as secondary form when it is the standard form (Minor)**
File: content, §"Рідкісні та 'хитрі' форми"
> «Але **Обернути** → **обернений** (тут уже -ен-).»

`Обернутий` is the standard form for `обернути` (a regular -нути verb). `Обернений` exists in literary usage but is the minority form. The text implies `обернений` is the expected/primary form, which would mislead students.

---

**Issue 9 — Inaccurate English gloss for "Як пити дати" (Minor)**
File: content, §"Дієслова з коренем -ня-" tip box
> «(Meaning: It's as easy as giving someone a drink, **very likely to happen**)»

"Very likely" implies probability; the idiom `як пити дати` expresses **certainty** ("it will definitely happen", "as sure as anything"). "Likely" is the wrong register.

---

**Minor observation (no fix required):** The group-sort activity names the first bucket "Суфікс -аний" but includes `відреставрований` which ends in `-ований`. The module prose does subsume `-ований` under the `-ний` family, so this is a pedagogical simplification — not wrong, but worth noting for a future revision.

---

===FIX_START===
FILE: curriculum/l2-uk-en/b2/past-passive-participles.md
---OLD---
але наній видно сліди
---NEW---
але на ній видно сліди
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/b2/past-passive-participles.md
---OLD---
| Гу**б**ити | **б** → **бл** | Гу**бл**ений | Гублений час ніколи не повертається. |
---NEW---
| Загу**б**ити | **б** → **бл** | Загу**бл**ений | Загублений час ніколи не повертається. |
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/b2/past-passive-participles.md
---OLD---
| Ло**в**ити | **в** → **вл** | Вло**вл**ений | Вловлений момент щастя застиг на фотографії. |
---NEW---
| Вло**в**ити | **в** → **вл** | Вло**вл**ений | Вловлений момент щастя застиг на фотографії. |
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/b2/past-passive-participles.md
---OLD---
Використайте слова: *відновлений, збережений, втрачений, пошкоджений, вирішено, залишений*.
---NEW---
Використайте слова: *відновлений, збережений, втрачений, пошкоджений, залишений*.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/b2/past-passive-participles.md
---OLD---
- Але **Обернути** → **обернений** (тут уже -ен-).
---NEW---
- **Обернути** → здебільшого **обернутий** (як і *повернутий*), рідше **обернений** (з суф. -ен-).
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/b2/past-passive-participles.md
---OLD---
«Як **пити** дати» (Meaning: It's as easy as giving someone a drink, very likely to happen).
---NEW---
«Як **пити** дати» (Meaning: It will definitely happen — "as sure as anything"; expresses certainty, not mere probability).
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/b2/activities/past-passive-participles.yaml
---OLD---
  - left: писати
    right: написаний
---NEW---
  - left: написати
    right: написаний
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/b2/activities/past-passive-participles.yaml
---OLD---
  - left: робити
    right: зроблений
---NEW---
  - left: зробити
    right: зроблений
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/b2/activities/past-passive-participles.yaml
---OLD---
    слова: відновлений, збережений, втрачений, пошкоджений, вирішено.'
---NEW---
    слова: відновлений, збережений, втрачений, пошкоджений, залишений.'
===FIX_END===

===VERDICT===
APPROVE
===END_VERDICT===