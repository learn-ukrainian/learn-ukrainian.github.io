## Adversarial QA Review: the-dative-ii-nouns (A2-02)

---

### Issues Found

**CRITICAL — Subject-Verb Agreement (3 instances in activities)**

1. `fill-in "Жіночий рід: магія чергування"` — `"Я даруємо квіти (подруга)."` — "Я" (1st sg) paired with "даруємо" (1st pl). Teaching material with a basic A1 conjugation error poisons the learner's pattern formation. Fix: change subject to "Ми" (we) to match the verb.

2. `fill-in "Множина: щедрість для всіх"` — `"Я даруємо радість (люди)."` — Same error. Fix: "Ми даруємо".

3. `cloze passage "День народження"` — `"Я даруємо {{2}} книгу"` — Same error inside a passage the student reads as model text. Especially harmful in a cloze where students absorb the sentence frame. Fix: "Я дарую".

**CRITICAL — Typo in match-up**

4. `match-up` — `"Читат казку"` — missing infinitive suffix "-и". Fix: "Читати казку".

**CRITICAL — Broken cloze: orphaned blanks 9–14**

5. `cloze "День народження"` — The passage contains only `{{1}}` through `{{8}}`, but the `blanks` array has 14 entries. Blanks 9–14 reference `{{9}}`–`{{14}}` that do not exist in the passage text. These are inanswerable ghost slots that will either crash the activity engine or confuse students. Fix: delete blanks 9–14.

**IMPORTANT — Factually misleading pedagogical note (K→Ts section)**

6. `main content, К→Ц section` — "If you go to the pharmacy, you are approaching the **аптеці** (though 'approaching' uses Dative only in specific contexts, usually it's used with Locative 'in the pharmacy', but the form is the same!)."

"Я йду до аптеки" uses **Genitive** after "до", not Dative. "Я підходжу до аптеки" also Genitive. There is no normal construction where "approaching a pharmacy" uses Dative in Ukrainian. The parenthetical tries to walk it back but the opening claim is wrong and will leave students with a false rule. Fix: replace the pharmacy claim with a factually correct note about Dative/Locative homophony.

**IMPORTANT — Morphology question with phrase option (select activity)**

7. `select "Як змінити слово 'Ольга' у Давальному відмінку?"` — Option `"Дати Ользі"` is marked `correct: true`. The question asks *how to change the word* (morphological form), not for a sample usage phrase. Mixing a phrase with bare forms in a morphology question is pedagogically unsound and the `min_correct: 2` forces students to select the phrase as a required answer. Fix: replace "Дати Ользі" with a wrong form (e.g., "Олзі" — missing soft sign) and set `min_correct: 1`.

**IMPORTANT — Wrong gloss for «іменинник»**

8. `main content, "Хто такий іменинник?" section` — `називається **іменинник** (birthday/name day person)`. "Іменинник" is specifically the *name day celebrant*, not a birthday person. Birthday person is "іменинець" or just described via "день народження". The gloss conflates two distinct celebrations. Fix: "(name day celebrant)".

**MINOR — Capitalization inconsistency in unjumble**

9. `unjumble` — words array contains `"Студентові"` (capital S) but the answer is `"Цьому молодому студентові вже виповнилося двадцять років"` where "студентові" is mid-sentence (lowercase). Fix: lowercase in words array.

---

===FIX_START===
FILE: curriculum/l2-uk-en/a2/activities/the-dative-ii-nouns.yaml
---OLD---
    - sentence: "Я даруємо квіти (подруга)."
      answer: "подрузі"
---NEW---
    - sentence: "Ми даруємо квіти (подруга)."
      answer: "подрузі"
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/activities/the-dative-ii-nouns.yaml
---OLD---
    - sentence: "Я даруємо радість (люди)."
      answer: "людям"
---NEW---
    - sentence: "Ми даруємо радість (люди)."
      answer: "людям"
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/activities/the-dative-ii-nouns.yaml
---OLD---
  passage: "Сьогодні у мого брата свято. {{1}} двадцять років. Ми готуємо подарунки. Я даруємо {{2}} книгу, тому що він любить читати. Мама дарує {{3}} новий телефон. Тато обіцяв купити {{4}} машину, але пізніше. Ми запросили гостей. Я телефоную {{5}}, щоб вони прийшли вчасно. Ми раді {{6}}. Ми пропонуємо {{7}} чай і торт. Свято дуже подобається {{8}}."
---NEW---
  passage: "Сьогодні у мого брата свято. {{1}} двадцять років. Ми готуємо подарунки. Я дарую {{2}} книгу, тому що він любить читати. Мама дарує {{3}} новий телефон. Тато обіцяв купити {{4}} машину, але пізніше. Ми запросили гостей. Я телефоную {{5}}, щоб вони прийшли вчасно. Ми раді {{6}}. Ми пропонуємо {{7}} чай і торт. Свято дуже подобається {{8}}."
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/activities/the-dative-ii-nouns.yaml
---OLD---
    - left: "Читат казку"
---NEW---
    - left: "Читати казку"
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/activities/the-dative-ii-nouns.yaml
---OLD---
    - id: 8
      answer: "брату"
      options: ["брату", "брат", "брата", "братом"]
    - id: 9
      answer: "сестрі"
      options: ["сестрі", "сестру", "сестра", "сестрою"]
    - id: 10
      answer: "мамі"
      options: ["мамі", "маму", "мама", "мамою"]
    - id: 11
      answer: "татові"
      options: ["татові", "тата", "тато", "татом"]
    - id: 12
      answer: "подрузі"
      options: ["подрузі", "подругу", "подруга", "подругою"]
    - id: 13
      answer: "дівчині"
      options: ["дівчині", "дівчину", "дівчина", "дівчиною"]
    - id: 14
      answer: "колезі"
      options: ["колезі", "колегу", "колега", "колегою"]
---NEW---
    - id: 8
      answer: "брату"
      options: ["брату", "брат", "брата", "братом"]
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/activities/the-dative-ii-nouns.yaml
---OLD---
    - question: "Як змінити слово 'Ольга' у Давальному відмінку?"
      options:
        - text: "Ользі"
          correct: true
        - text: "Ольгі"
          correct: false
        - text: "Дати Ользі"
          correct: true
        - text: "Бачити Ольгу"
          correct: false
      min_correct: 2
---NEW---
    - question: "Як змінити слово 'Ольга' у Давальному відмінку?"
      options:
        - text: "Ользі"
          correct: true
        - text: "Ольгі"
          correct: false
        - text: "Олзі"
          correct: false
        - text: "Бачити Ольгу"
          correct: false
      min_correct: 1
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/activities/the-dative-ii-nouns.yaml
---OLD---
    - words: ["років", "двадцять", "Студентові", "Цьому", "молодому", "вже", "виповнилося"]
---NEW---
    - words: ["років", "двадцять", "студентові", "Цьому", "молодому", "вже", "виповнилося"]
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/the-dative-ii-nouns.md
---OLD---
If you give flowers to your daughter, you give them **доньці**. If you go to the pharmacy, you are approaching the **аптеці** (though "approaching" uses Dative only in specific contexts, usually it's used with Locative "in the pharmacy", but the form is the same!).
---NEW---
If you give flowers to your daughter, you give them **доньці**. If you address a parcel to the pharmacy, you write **аптеці** — Dative at work. Important note: the Dative form **аптеці** looks identical to the Locative «в аптеці» (in the pharmacy). This is expected — Ukrainian feminine nouns ending in **-ка** use the same **-і** ending for both Dative (*кому?*) and Locative (*де?*). The verb and context tell you which case you are dealing with.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/the-dative-ii-nouns.md
---OLD---
називається **іменинник** (birthday/name day person).
---NEW---
називається **іменинник** (name day celebrant).
===FIX_END===

---

===VERDICT===
APPROVE
===END_VERDICT===

**Rationale:** All blocking issues are fixable and fixed above — the three subject-verb agreement errors (critical A1-level errors in model text), the typo, the orphaned cloze blanks (would break the activity engine), the factually wrong Dative/pharmacy claim, and the structurally broken select question. After applying these fixes no remaining issues block release. Word count is well above target, all plan sections are present, objectives map to self-check questions, Ukrainian cultural content (odd-numbered flowers, taboo gifts, name day customs) is accurate and well-integrated, and there are no Russianisms or Russian characters.