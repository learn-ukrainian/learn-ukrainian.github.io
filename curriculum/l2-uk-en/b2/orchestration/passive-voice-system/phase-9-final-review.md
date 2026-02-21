## Adversarial QA Review — passive-voice-system (b2-01)

---

### Issues Found

**ISSUE 1 — Typo: "неповорокою" (non-word)**
File: `passive-voice-system.md`, myth-buster callout
> "Надмірний пасив робить мову важкою, **неповорокою** і бюрократичною."

"Неповорока" is not a Ukrainian word. The correct instrumental adjective is "неповороткою" (від "неповороткий" — clumsy/unwieldy). Severity: medium.

---

**ISSUE 2 — Typo: "Настапаючий" (garbled example)**
File: `passive-voice-system.md`, Form 1 section, "Типова помилка: Активні дієприкметники"
> "❌ *Настапаючий рік* — калька."

Missing "у": should be "Наступаючий" (the Russianism being demonstrated as wrong). Severity: medium.

---

**ISSUE 3 — Nonsensical header: "Офіційний орудний діяча"**
File: `passive-voice-system.md`, Form 3 section
> "### Критична помилка: Офіційний орудний діяча"

"Офіційний" (official) makes no grammatical sense as a modifier for "орудний" here. The section is about prohibiting a human agent in the instrumental case with -ся constructions. Confirmed from Green Review. Severity: high.

---

**ISSUE 4 — Activity contradiction: "Лист написаний братом" marked `correct: false`**
File: `passive-voice-system.yaml`, `select` activity, question 5

The activity marks "Лист написаний братом" as INCORRECT. But the module's own prose uses the identical construction as a **positive example**:

> "*«Цей лист **написаний** ще моїм дідом.»* (Лист зберігає тепло рук діда)."

Passive participle (-ний/-тий) + human agent in instrumental IS standard Ukrainian grammar for Form 1. Marking it wrong contradicts the content and teaches students incorrect Ukrainian. `min_correct: 3` must become `min_correct: 4` since all four options are then valid. Severity: **critical**.

---

**ISSUE 5 — Group-sort: "Вікно розбили хулігани" misclassified as Form 4**
File: `passive-voice-system.yaml`, `group-sort` activity, Form 4 group

The sentence "Вікно **розбили** хулігани" has an **explicit grammatical subject** "хулігани" (nominative plural). Form 4 passive is defined in the module as constructions WITHOUT an explicit subject ("ми беремо дієслово у 3-й особі множини і свідомо прибираємо займенник *вони*"). All other Form 4 items in the group correctly omit the subject. This example is an active two-part sentence with inverted word order, not Form 4 passive. Severity: high.

---

**ISSUE 6 — Fill-in explanation uses "короткі прикметники" (Russian grammar term)**
File: `passive-voice-system.yaml`, `fill-in` activity, item 9
> "У побуті ми часто використовуємо **короткі прикметники** або прості ствердження стану."

"Короткі прикметники" (short-form adjectives) is a Russian grammatical category (краткие прилагательные: "готов," "добр"). Ukrainian does not have this form — "готовий" is the only standard form. Importing this Russian term into the metalanguage is inaccurate. Severity: medium.

---

**ISSUE 7 — LLM: "гімн результату"** (confirmed from Green Review)
File: `passive-voice-system.md`, Form 1 section
> "Пасивний дієприкметник — це **гімн результату**."

Hyperbolic LLM prose. Fix: "фіксація результату."

---

**ISSUE 8 — LLM: "фонетична магія"** (confirmed from Green Review)
File: `passive-voice-system.md`, Form 1 section
> "Тут відбувається **фонетична магія**: чергування..."

Fix: "Тут відбувається **фонетичне чергування**:"

---

**ISSUE 9 — LLM: "уявний експеримент"** (confirmed from Green Review)
File: `passive-voice-system.md`, "Вибір форми пасиву за контекстом" section
> "Давайте проведемо **уявний експеримент**."

Fix: "Розглянемо це на практиці."

---

### Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/b2/passive-voice-system.md
---OLD---
> **Реальність:** Надмірний пасив робить мову важкою, неповорокою і бюрократичною. Сучасний стиль прагне до чіткості.
---NEW---
> **Реальність:** Надмірний пасив робить мову важкою, неповороткою і бюрократичною. Сучасний стиль прагне до чіткості.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/b2/passive-voice-system.md
---OLD---
*   ❌ *Настапаючий рік* — калька.
---NEW---
*   ❌ *Наступаючий рік* — калька.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/b2/passive-voice-system.md
---OLD---
### Критична помилка: Офіційний орудний діяча
---NEW---
### Критична помилка: Виконавець в орудному відмінку
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/b2/passive-voice-system.md
---OLD---
Пасивний дієприкметник — це гімн результату.
---NEW---
Пасивний дієприкметник — це фіксація результату.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/b2/passive-voice-system.md
---OLD---
Тут відбувається фонетична магія: чергування, з'являється додатковий звук **-л-** для милозвучності.
---NEW---
Тут відбувається фонетичне чергування: з'являється додатковий звук **-л-** для милозвучності.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/b2/passive-voice-system.md
---OLD---
Давайте проведемо уявний експеримент. Ми досліджуємо старовинну хату-мазанку.
---NEW---
Розглянемо це на практиці. Ми досліджуємо старовинну хату-мазанку.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/b2/activities/passive-voice-system.yaml
---OLD---
    - question: "Оберіть речення, де правильно вжито пасивний дієприкметник."
      options:
        - text: "Двері зачинені."
          correct: true
        - text: "Двері зачинені вітром."
          correct: true
        - text: "Лист написаний чорнилом."
          correct: true
        - text: "Лист написаний братом."
          correct: false
      min_correct: 3
---NEW---
    - question: "Оберіть речення, де правильно вжито пасивний дієприкметник."
      options:
        - text: "Двері зачинені."
          correct: true
        - text: "Двері зачинені вітром."
          correct: true
        - text: "Лист написаний чорнилом."
          correct: true
        - text: "Лист написаний братом."
          correct: true
      min_correct: 4
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/b2/activities/passive-voice-system.yaml
---OLD---
        - "Вікно **розбили** хулігани."
---NEW---
        - "Вікно **розбили** випадково."
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/b2/activities/passive-voice-system.yaml
---OLD---
      explanation: "У побуті ми часто використовуємо короткі прикметники або прості ствердження стану."
---NEW---
      explanation: "У побуті ми часто використовуємо прикметники або прості ствердження стану."
===FIX_END===

===VERDICT===
APPROVE
===END_VERDICT===