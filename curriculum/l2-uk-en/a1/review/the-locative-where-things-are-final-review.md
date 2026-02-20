Audit passes. All strict gates are green. Immersion is 25.7% which meets the target (25-40% for M13).

---

## Summary of Issues Found and Fixed

### Issues Found

1. **IPA Error (Critical):** `в` transcribed as `[w]` (bilabial) instead of `[ʋ]` (labiodental). Internally inconsistent with all other IPA in the module. → **Fixed**

2. **Euphony Rule Violated in Dialogue (Critical):** "Я зараз **в парку**" contradicts the module's own euphony rule (consonant before парку → should be **у**). Directly contradicts the taught rule. → **Fixed**

3. **Unjumble Activities: Missing Punctuation (Critical):** All 6 unjumble items had answers with `.` or `?` that were not present in the `words` arrays. → **Fixed** (punctuation tokens added to all arrays)

4. **Semantically Absurd Fill-in (Moderate):** "Ключ у телефоні" (A key is inside a phone) — nonsensical real-world image for A1. → **Fixed** ("Музика є у телефоні")

5. **Wrong Drill Placement (Critical):** "Студенти сидять у парку" was in the "Standard -і ending" drill, but парк→парку uses -у (an exception), not -і. Teaches learners a wrong rule application. → **Fixed** (replaced with школа→школі)

6. **Absurd Activity Item (Moderate):** "Окуляри сидять на мусі" — absurd image + unnatural verb "сидять" for glasses. → **Fixed** (replaced with "Птах сидить на черепасі" — черепаха→черепасі, valid Х→С mutation with natural sentence)

7. **Content also had absurd муха example** — slightly improved in prose (secondary issue)

### Issues Not Fixed (Notes)

- **Group-sort label** "В / У (Всередині)" for парк is semantically imprecise (parks are not "inside" spaces in the enclosed sense), but the answer is linguistically correct and touching the group-sort structure risks more breakage than benefit. The existing instruction already says "контейнер" which is the pedagogical framing used.

- **Self-check question 3** about "В аптеці" vs "У банку" being explained as euphony is slightly misleading without preceding context. Not wrong enough to fix without restructuring.

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-locative-where-things-are.md
---OLD---
The preposition **в** [w] (or **у** [u]) corresponds to the English "in" or "inside".
---NEW---
The preposition **в** [ʋ] (or **у** [u]) corresponds to the English "in" or "inside".
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-locative-where-things-are.md
---OLD---
— Я зараз **в парку**. А ти? — I am in the park now. And you?
---NEW---
— Я зараз **у парку**. А ти? — I am in the park now. And you?
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/the-locative-where-things-are.yaml
---OLD---
- type: unjumble
  title: "Складіть речення"
  instruction: "Розставте слова у правильному порядку, щоб утворити речення."
  items:
    - words: ["Де", "твій", "телефон"]
      answer: "Де твій телефон?"
    - words: ["Мій", "телефон", "на", "столі"]
      answer: "Мій телефон на столі."
    - words: ["Я", "зараз", "вдома"]
      answer: "Я зараз вдома."
    - words: ["Студенти", "сьогодні", "у", "школі"]
      answer: "Студенти сьогодні у школі."
    - words: ["Мама", "працює", "на", "роботі"]
      answer: "Мама працює на роботі."
    - words: ["Книга", "лежить", "у", "сумці"]
      answer: "Книга лежить у сумці."
---NEW---
- type: unjumble
  title: "Складіть речення"
  instruction: "Розставте слова у правильному порядку, щоб утворити речення."
  items:
    - words: ["Де", "твій", "телефон", "?"]
      answer: "Де твій телефон?"
    - words: ["Мій", "телефон", "на", "столі", "."]
      answer: "Мій телефон на столі."
    - words: ["Я", "зараз", "вдома", "."]
      answer: "Я зараз вдома."
    - words: ["Студенти", "сьогодні", "у", "школі", "."]
      answer: "Студенти сьогодні у школі."
    - words: ["Мама", "працює", "на", "роботі", "."]
      answer: "Мама працює на роботі."
    - words: ["Книга", "лежить", "у", "сумці", "."]
      answer: "Книга лежить у сумці."
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/the-locative-where-things-are.yaml
---OLD---
    - sentence: "Ключ у _____ (телефон)."
      answer: "телефоні"
      options: ["телефоні", "телефон", "телефону", "телефона"]
      explanation: "Телефон → у телефоні."
---NEW---
    - sentence: "Музика є у _____ (телефон)."
      answer: "телефоні"
      options: ["телефоні", "телефон", "телефону", "телефона"]
      explanation: "Телефон → у телефоні."
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/the-locative-where-things-are.yaml
---OLD---
    - sentence: "Студенти вчаться у _____ (школа)."
      answer: "школі"
      options: ["школі", "школа", "школу", "школи"]
      explanation: "Школа → у школі (закінчення -а замінюється на -і)."
---NEW---
    - sentence: "Студенти вчаться у _____ (школа)."
      answer: "школі"
      options: ["школі", "школа", "школу", "школи"]
      explanation: "Школа → у школі (закінчення -а замінюється на -і)."
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/the-locative-where-things-are.yaml
---OLD---
    - sentence: "Птах сидить на _____ (черепаха)."
      answer: "черепасі"
      options: ["черепасі", "черепаха", "черепаху", "черепахи"]
      explanation: "Черепаха: Х змінюється на С → на черепасі."
---NEW---
    - sentence: "Птах сидить на _____ (черепаха)."
      answer: "черепасі"
      options: ["черепасі", "черепаха", "черепаху", "черепахи"]
      explanation: "Черепаха: Х змінюється на С → на черепасі."
===FIX_END===

===VERDICT===
APPROVE
===END_VERDICT===