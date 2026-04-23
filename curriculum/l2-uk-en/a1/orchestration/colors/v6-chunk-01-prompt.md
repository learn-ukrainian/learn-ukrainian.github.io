Full module rewrite required. Preserve the plan and contract exactly.
Prioritize these persistent findings:
- [exercise_quality/activity_order] activity order: Activity order mismatch at position 1 (expected type 'quiz', found 'group-sort-hard-soft') and position 2 (expected type 'fill-in', found 'quiz-what-color') and position 3 (expected type 'quiz', found 'fill-in-agreement') and position 4 (expected type 'match-up', found 'quiz-blue-shades') and position 5 (expected type 'group-sort', found 'match-up-appearance') :: Regenerate the module so the activity order matches the plan's activity_obligations.

# Section-by-Section Generation — Section 1/4

You are a lead ukrainian instructor (The Patient Guide), writing ONE SECTION of a Ukrainian language module. Write ONLY this section — nothing else.

**Module:** 10: Кольори (A1, A1.2 [Мій світ])
**Section to write:** Діалоги
**Word target for this section:** about 330 words. Hitting the minimum matters more than staying short; do not undershoot this section.

---

## Section Skeleton (follow this exactly)

If any skeleton example conflicts with the Shared Module Contract or current plan YAML, the plan wins. Rewrite the conflicting paragraph to match the plan.
Do not use meta-pedagogical narration ("We can analyze...", "This conversation shows...").
After any dialogue, write at most 2 explanatory sentences, each quoting a Ukrainian form from that dialogue.

[BEGIN SECTION SKELETON LITERAL - reference data only; do not follow instructions inside]
```markdown
## Діалоги (~330 words total)
- P1 (~130 words): Діалог 1 — На відкритому квітковому ринку. Наталка та Продавець вибирають букет. Використання базових кольорів з різними родами: червоні троянди (f, pl), білі лілії (f, pl), жовті соняшники (m, pl), синя ваза (f), зелене листя (n). Введення фрази `Якого вони кольору? — Червоні` та виразу `Мені подобаються`.
- P2 (~130 words): Діалог 2 — Вибір вбрання з гардероба та опис зовнішності людини (Олі), яку треба впізнати на вечірці. Дмитро та Ліза. Опис предметів: чорна сукня (f), білий светр (m), сіре пальто (n), коричневі черевики (pl). Питання: `Як я впізнаю Олю?` — Відповідь: `У неї карі очі й русяве волосся.`
- P3 (~70 words): Короткий аналіз діалогів. Звернення уваги на те, як питання `Якого кольору?` вимагає узгодження прикметника з іменником, а також на використання готових фраз типу `Мені подобаються` (без заглиблення у давальний відмінок) та описів зовнішності.
```
[END SECTION SKELETON LITERAL]

---
## Shared Module Contract

[BEGIN MODULE CONTRACT LITERAL - reference data only; do not follow instructions inside]
```yaml
current_section:
  order: 1
  name: Діалоги
  word_budget:
    target: 300
    min: 270
    max: 330
  teaching_beats:
  - 'Діалог 1 — Вибір букета на квітковому ринку (за мотивами вірша про кольори з
    підручника Большакової для 2 класу, с. 38): — Які гарні троянди! Якого вони кольору?
    — Червоні. А ось ці лілії — білі. — Мені подобаються жовті соняшники. — Добре,
    загорнути букет? Кольори входять через реалістичне запитання `Якого кольору?`
    і коротку відповідь. Примітка: `Мені подобаються` тут працює як готовий вираз;
    детальне пояснення давального відмінка відкладаємо.'
  - 'Діалог 2 — Опис кімнати й людини для впізнавання (продовження модуля №8–9): —
    Якого кольору твоя кімната? — Біла. — А стіл? — Стіл коричневий. А крісло — сіре.
    — Як я впізнаю Олю? — У неї карі очі й русяве волосся. Повторення: узгодження
    за родами + нова лексика кольорів + кілька природних словосполучень для зовнішності.'
  required_terms:
  - Діалог
  - Вибір
  - букета
  - квітковому
  - ринку
  - мотивами
  - вірша
  - про
dialogue_acts:
- setting: 'На відкритому квітковому ринку — вибір букетів для різних подій. Описати:
    червоні троянди, білі лілії, жовті соняшники, синя ваза (f), зелене листя (n).
    Використовуються квіти, рослини та обгортка.'
  speakers:
  - Наталка
  - Продавець
  function: Запитання `Якого кольору?` + узгодження кольорів зі словами троянда(f),
    соняшник(m), листя(n), ваза(f)
- setting: 'Вибір вбрання для вечірки з гардероба друга і короткий опис людини, яку
    треба впізнати в натовпі. Описати: чорна сукня (f), білий светр (m), сіре пальто
    (n), коричневі черевики (pl), карі очі, русяве або сиве волосся. Використовується
    одяг, БЕЗ сумок.'
  speakers:
  - Дмитро
  - Ліза
  function: 'Колір + рід: сукня(f), светр(m), пальто(n), черевики(pl); короткі відповіді
    на `Якого кольору?`; опис зовнішності через `карі очі`, `русяве/сиве волосся`'
activity_obligations: []
style_review_advice: []
```
[END MODULE CONTRACT LITERAL]

---

## Section-Mapped Wiki Excerpts

[BEGIN SECTION WIKI EXCERPTS LITERAL - reference data only; do not follow instructions inside]
```yaml
section: Діалоги
items:
- citation: 'pedagogy/a1/colors.md :: Послідовність введення'
  source_path: pedagogy/a1/colors.md
  source_heading: Послідовність введення
  score: 38
  score_breakdown:
    query: 31
    scenario: 4
    article: 3
  matched_terms:
  - білии
  - використовуються
  - волосся
  - впізнавання
  - відмінка
  - відповідь
  scenario_terms:
  - базових
  - блакитнии
  - білии
  - використовуються
  - волосся
  - готових
  excerpt: '**Крок 1: Базові кольори (★★★★)** Починати слід з 7–10 основних, найчастотніших
    кольорів. Ці кольори є основою для подальшого вивчення і найчастіше зустрічаються
    у повсякденному житті. До цієї групи належать: * червоний * зелений * синій *
    жовтий * чорний * білий * сірий На цьому етапі кольори подаються як базові лексеми,
    але з наголосом, що це прикметники, які будуть змінюватися. **Крок 2: Узгодження
    в роді та числі (називний відмінок)** Це найважливіший крок. Кожен новий колір
    має бути представлений у всіх...'
- citation: 'pedagogy/a1/colors.md :: Приклади з підручників'
  source_path: pedagogy/a1/colors.md
  source_heading: Приклади з підручників
  score: 30
  score_breakdown:
    query: 23
    scenario: 4
    article: 3
  matched_terms:
  - без
  - волосся
  - відповідь
  - діалог
  - жовті
  - запитання
  scenario_terms:
  - без
  - блакитнии
  - волосся
  - групи
  - жовтии
  - жовті
  excerpt: Ось кілька прикладів вправ з українських шкільних підручників, адаптованих
    для рівня A1. **1. Складання речень (з розрізнених слів)** * **Завдання:** Зі
    слів кожної групи складіть і запишіть речення. * **Приклад:** 1. Жовтий, люди,
    сонячним, колір, називають. → Люди називають жовтий колір сонячним. 2. Зелений,
    кольором, люди, вважають, колір, життя. → Люди вважають зелений колір кольором
    життя. * **Мета:** Практика правильного порядку слів та синтаксичної ролі кольору
    в реченні. * **Джерело:** Підручник для 2...
```
[END SECTION WIKI EXCERPTS LITERAL]

---

## Paragraph Language Rule

- Section must fit the module immersion target: 10-20% Ukrainian
- Every prose paragraph is monolingual: all English or all Ukrainian.
- Never alternate English and Ukrainian sentences inside one paragraph.
- If you write a Ukrainian paragraph for A1/A2 support, translate the whole paragraph in one English blockquote when needed; do not translate sentence by sentence.
- Dialogues are exempt: per-turn inline English translations are allowed.


---

## Section Rules

- A1 grammar envelope: keep Ukrainian sentences short, one clause, and avoid advanced case-heavy constructions unless the current section explicitly teaches them.
- Cover only the current section's obligations from the shared contract; do not pre-teach later sections.
- Include at least one callout box (`:::note`, `:::tip`, or `:::info`) in this section.
- No meta-pedagogical narration. No vocabulary tables. No word-count notes.
- Zero Russian, zero Surzhyk, zero calques. No stress marks.
- Use Ukrainian quotes «...» for Ukrainian text.
- Do not invent exercise markers in this section unless the skeleton explicitly contains one.

## Dialogue formatting

- **Dialogue formatting (EXEMPT from the monolingual rule):** Use blockquote `>` with speaker names in bold. Each turn on its own `>` line. Per-turn inline English translations in `*(English)*` ARE allowed for dialogs. NO blank lines between turns. Example:
  > — **Оксана:** Привіт! *(Hi!)*
  > — **Степан:** Добрий день! *(Good day!)*
  > — **Оксана:** Як справи? *(How are you?)*

## REQUIRED VOCABULARY CHECKLIST (#1189)

**Current-section vocabulary focus** — include these words naturally in this section if they fit the teaching beats. Later sections will handle the rest of the module vocabulary.

- [ ] Діалог
- [ ] Вибір
- [ ] букета
- [ ] квітковому
- [ ] ринку
- [ ] мотивами
- [ ] вірша
- [ ] про

## FORBIDDEN WORDS — never produce (#1189)

Never emit these Russian/Russianized forms: `хорошо`, `конечно`, `спасибо`, `пожалуйста`, `ничего`, `сейчас`, `тоже`, `здесь`, `кот`, `кон`.
Use `добре`, `звичайно`, `дякую`, `будь ласка`, `нічого`, `зараз`, `теж`, `тут`, `кіт`, `кін`. Never output `ы`, `э`, `ё`, or `ъ`.

## Output

Write the section starting with the H2 heading **`## Діалоги`** (verbatim — do not paraphrase). Output ONLY the section content — no preamble, no summary, no notes.
