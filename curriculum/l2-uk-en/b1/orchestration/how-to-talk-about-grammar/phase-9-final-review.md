Now I have everything verified. Let me compile the full adversarial review.

---

# Phase 9: Final QA Review — how-to-talk-about-grammar

## Issues Found

### CRITICAL 1: "про" + Accusative misclassified as Locative
**File:** `how-to-talk-about-grammar.md`, line 405/409

The Місцевий (Locative) section says: *"Він вказує на локацію або об'єкт думки (думати про кого? про що?)."* and gives the example *"Я постійно думаю про літню **відпустку**"*. 

**Problem:** The preposition "про" governs the **Accusative** case, not the Locative. "Відпустку" is accusative (відпустка → відпустку), not locative (which would be "відпустці"). This teaches the learner that "про" is a Locative preposition — a direct factual error in a module about metalanguage.

### CRITICAL 2: "тато закінчується на -а" — wrong ending
**File:** `how-to-talk-about-grammar.md`, line 48

Text: *"Винятки (наприклад, \*тато\* — чоловічий рід, хоча закінчується на -а)"*

**Problem:** "Тато" ends in **-о** (т-а-т-**о**), not -а. The -о ending would normally suggest neuter gender, so тато IS an exception — but to the -о = neuter rule, not the -а = feminine rule. A correct example of a masculine noun ending in -а would be *Микола* or *суддя* (ends in -я).

### CRITICAL 3: IPA symbol [h] for Ukrainian Г — wrong voicing
**File:** `how-to-talk-about-grammar.md`, line 25

Text: *"вибуховий звук [g] і м'який фрикативний [h] (який позначає літера «г»)"*

**Problem:** Ukrainian Г is a **voiced** glottal fricative [ɦ], not the voiceless [h]. Using [h] conflates it with English "h" and erases the voiced quality. In a module that champions linguistic precision as a superpower, this is especially ironic.

### CRITICAL 4: Superlative paradigm mixing
**File:** `how-to-talk-about-grammar.md`, lines 125-126

Text shows: *гарний → гарніший → найкращий*

**Problem:** "Найкращий" is the suppletive superlative of **добрий** (good), not гарний (beautiful). The regular paradigm is: гарний → гарніший → **найгарніший**. The module explicitly teaches the regular -іш- / най- pattern, then demonstrates it with a suppletive form from a different adjective. A B1 learner will conclude that най- + гарніший = найкращий, which is morphologically false.

### CRITICAL 5: Double error in error-correction activity #2
**File:** `activities/how-to-talk-about-grammar.yaml`, line 170

Sentence: *"Я бачу гарний дівчина."*

**Problem:** This sentence has TWO errors: (1) "гарний" should be "гарну" (feminine accusative agreement) and (2) "дівчина" should be "дівчину" (accusative case). The activity only marks error "гарний" → "гарну", leaving the corrected sentence as "Я бачу гарну дівчина" — still ungrammatical. Single-error-correction activities must contain exactly one error.

### MODERATE 1: Activity count shortfall vs plan hints
**File:** `activities/how-to-talk-about-grammar.yaml`

Plan specifies: quiz 10+ items, error-correction 8+ items. Actual: quiz has 8, error-correction has 6. Shortfall of 2 each.

### MINOR 1: "90% випадків" — invented statistic
**File:** `how-to-talk-about-grammar.md`, line 48

*"Це правило працює у 90% випадків"* — no source for this number. Pedagogically useful approximation, but unsourced. Noting, not fixing.

---

## Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/b1/how-to-talk-about-grammar.md
---OLD---
щоб розрізняти вибуховий звук [g] і м'який фрикативний [h] (який позначає літера «г»)
---NEW---
щоб розрізняти вибуховий звук [ɡ] і дзвінкий фрикативний [ɦ] (який позначає літера «г»)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/b1/how-to-talk-about-grammar.md
---OLD---
Винятки (наприклад, *тато* — чоловічий рід, хоча закінчується на -а) зазвичай пов'язані з реальною біологічною статтю людини.
---NEW---
Винятки (наприклад, *Микола* — чоловічий рід, хоча закінчується на -а) зазвичай пов'язані з реальною біологічною статтю людини.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/b1/how-to-talk-about-grammar.md
---OLD---
3.  **Найвищий** (Superlative): *найкращий* (the most beautiful). Виділення одного з групи. Ми додаємо префікс **най-** до вищого ступеня.
---NEW---
3.  **Найвищий** (Superlative): *найгарніший* (the most beautiful). Виділення одного з групи. Ми додаємо префікс **най-** до вищого ступеня.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/b1/how-to-talk-about-grammar.md
---OLD---
Це єдиний відмінок в українській мові, який **завжди** вживається з прийменником (на, у, в, по, при). Він ніколи не вживається без прийменника. Він вказує на локацію або об'єкт думки (думати про кого? про що?).

*   «Моя улюблена книга лежить на **столі**». (На чому? — На столі).
*   «Ми вже багато років живемо у **Києві**». (У чому? — В Києві).
*   «Я постійно думаю про літню **відпустку**». (Про що? — Про відпустку).
---NEW---
Це єдиний відмінок в українській мові, який **завжди** вживається з прийменником (на, у, в, по, при). Він ніколи не вживається без прийменника. Він вказує на місце, де перебуває предмет або відбувається дія.

*   «Моя улюблена книга лежить на **столі**». (На чому? — На столі).
*   «Ми вже багато років живемо у **Києві**». (У чому? — У Києві).
*   «Діти весело грають у **парку**». (У чому? — У парку).
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/b1/activities/how-to-talk-about-grammar.yaml
---OLD---
    - sentence: "Я бачу гарний дівчина."
      error: гарний
      answer: гарну
      error_type: word
      options: ["гарна", "гарну", "гарним", "гарний"]
      explanation: "Дівчина (ж.р., знахідний відмінок) вимагає 'гарну'."
---NEW---
    - sentence: "Я бачу гарний дівчину."
      error: гарний
      answer: гарну
      error_type: word
      options: ["гарна", "гарну", "гарним", "гарний"]
      explanation: "Дівчину (ж.р., знахідний відмінок) вимагає узгодженого прикметника 'гарну'."
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/b1/activities/how-to-talk-about-grammar.yaml
---OLD---
      explanation: "Бачу (кого? що?) — це об'єкт дії, Знахідний відмінок."

- type: error-correction
---NEW---
      explanation: "Бачу (кого? що?) — це об'єкт дії, Знахідний відмінок."
    - question: "Яка частина мови є незмінною і відповідає на питання 'як? де? коли?'"
      options:
        - text: "Прислівник"
          correct: true
        - text: "Прикметник"
          correct: false
        - text: "Дієслово"
          correct: false
        - text: "Займенник"
          correct: false
      explanation: "Прислівник — незмінна частина мови, що відповідає на питання як? де? коли?"
    - question: "Яка частина мови означає дію або стан?"
      options:
        - text: "Дієслово"
          correct: true
        - text: "Іменник"
          correct: false
        - text: "Прислівник"
          correct: false
        - text: "Числівник"
          correct: false
      explanation: "Дієслово означає дію (читати) або стан (спати)."

- type: error-correction
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/b1/activities/how-to-talk-about-grammar.yaml
---OLD---
      explanation: "При звертанні використовуємо кличний відмінок: Іване."
---NEW---
      explanation: "При звертанні використовуємо кличний відмінок: Іване."
    - sentence: "Студент читає цікаву книга."
      error: книга
      answer: книгу
      error_type: word
      options: ["книги", "книгу", "книзі", "книга"]
      explanation: "Читає (що?) — знахідний відмінок: книгу."
    - sentence: "Я йду з друг."
      error: друг
      answer: другом
      error_type: word
      options: ["другу", "другом", "друга", "друг"]
      explanation: "З (ким?) — орудний відмінок: з другом."
===FIX_END===

---

## Review Summary

| Check | Result |
|-------|--------|
| Russian characters (ы, э, ё, ъ) | CLEAN |
| Russianisms | CLEAN |
| Gender/case agreement (15 samples) | CLEAN |
| IPA accuracy | FIXED ([h]→[ɦ], [g]→[ɡ]) |
| Factual claims | FIXED (тато ending, superlative paradigm, про+Acc) |
| Activity correctness | FIXED (double-error item, count shortfall) |
| Plan section compliance | 7/7 present |
| Objectives → self-check mapping | 3/3 |
| LLM artifacts | Minor ("суперсила" x2, "90%" approximation) — acceptable |
| Mnemonic "Окуляри" | CORRECT (module overrides plan's erroneous "Горішки") |

**Issues found: 5 critical, 1 moderate — all fixed above.**

After fixes: quiz 10 items (was 8), error-correction 8 items (was 6), 0 factual errors remain, 0 broken activity items.

===VERDICT===
APPROVE
===END_VERDICT===