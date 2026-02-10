# Phase 0: Deep Research (Seminar Track)

> **You are Gemini, executing Phase 0 of an orchestrated rebuild.**
> **Your ONLY task: Research the topic and produce structured notes.**

## Your Input

Read the plan file to understand what this module covers:

```
---
module: c1-bio-001
level: C1-BIO
sequence: 1
slug: knyahynia-olha
version: '2.0'
title: 'Княгиня Ольга: Дипломатія та реформи'
word_target: 4300
content_outline:
- section: "Вступ — Мудра володарка Києва"
  words: 600
  points:
  - Ольга як символ державної мудрості
  - Поєднання язичницької сили та християнського вибору
  - Роль у зміцненні внутрішнього ладу
- section: Життєпис
  words: 1600
  points:
  - Походження (легенди про Псков та болгарське коріння)
  - Шлюб з Ігорем
  - Трагедія 945 р. та помста древлянам
  - Регентство при Святославі
- section: Історичний контекст
  words: 600
  points:
  - Стан Русі в середині X ст.
  - Стосунки з Візантією та Священною Римською імперією
- section: Внесок
  words: 400
  points:
  - Податкова реформа (устави, уроки, погости)
  - Встановлення перших державних кордонів
- section: Останні роки
  words: 400
  points:
  - Дипломатична місія до Константинополя 957 р.
  - Прийняття християнства
  - Смерть та канонізація
- section: Спадщина
  words: 400
  points:
  - Ольга як "передвісниця" Хрещення Русі
  - Образ у літописах та мистецтві
- section: Підсумок
  words: 300
  points:
  - Ольга як архітекторка регулярної держави
focus: biography
pedagogy: seminar
prerequisites:
- c1-bio-01 (Олег Віщий)
- b2-hist knyahynia-olha module
connects_to:
- c1-bio-03 (Святослав Хоробрий)
- b2-hist hrystyianstvo module
objectives:
- Проаналізувати адміністративні реформи Ольги
- Оцінити дипломатичні успіхи у відносинах з Візантією
- Дослідити причини та наслідки прийняття християнства
grammar:
- Архаїзми в літописному контексті
- Офіційний регістр (опис реформ)
module_type: biography
sources:
- name: Княгиня Ольга (Wikipedia UA)
  url: "https://uk.wikipedia.org/wiki/Княгиня_Ольга"
  type: primary
  notes: Основне джерело фактів
- name: Повість минулих літ
  url: "http://izbornyk.org.ua/"
  type: primary
  notes: Літописні легенди
immersion: 100% Ukrainian
phase: C1-BIO
vocabulary_hints:
  required:
  - регент (regent)
  - погост (pohost - administrative center)
  - урок (urok - fixed tax)
activity_hints:
- type: reading
  focus: Аналіз літописної розповіді про помсту
  source: Повість минулих літ (адаптовано)
- type: critical-analysis
  focus: Сутність податкової реформи
```

Read the current meta file for content_outline structure:

```
---
module: c1-bio-001
level: C1-BIO
slug: knyahynia-olha
version: '2.0'
id: c1-bio-001
title: "Княгиня Ольга: Архітекторка державної волі"
naturalness:
  score: 10
  status: PASS
duration: 120
transliteration: none
tags:
- history
- biography
- politics
- diplomacy
- Kievan-Rus
content_outline:
- section: "Вступ: Мудра володарка Києва"
  words: 600
  points:
  - "Ольга як символ державної мудрості та незламності"
  - "Перехід від епохи завоювань до епохи впорядкування"
  - "Роль у зміцненні внутрішнього ладу"
- section: "Життєпис: Від таємниць походження до регентства"
  words: 1600
  points:
  - "Походження (легенди про Псков, болгарське коріння та скандинавський слід)"
  - "Шлюб з Ігорем та входження у владну еліту"
  - "Трагедія 945 р. та приборкання древлян: політика через ритуал"
  - "Регентство при Святославі: втримання імперії Рюриковичів"
- section: "Історичний контекст: Русь на роздоріжжі X століття"
  words: 600
  points:
  - "Геополітична ситуація: Хазарський каганат, Візантія та Європа"
  - "Внутрішні виклики: сепаратизм племен та потреба в центрі"
- section: "Внесок: Перша реформаторка Східної Європи"
  words: 400
  points:
  - "Податкова реформа: устави, уроки та система погостів"
  - "Встановлення перших державних кордонів та адміністративних одиниць"
- section: "Дипломатія та віра: Місія до Константинополя"
  words: 400
  points:
  - "Візит 957 р.: етикет, хрещення та державний престиж"
  - "Стосунки з Оттоном I та баланс між Сходом і Заходом"
- section: "Спадщина: Світло після темряви"
  words: 400
  points:
  - "Ольга як передвісниця Хрещення Русі"
  - "Образ у літописах та мистецтві"
  - "Канонізація та тяглість державної традиції"
- section: "Порівняльний аналіз: Моделі управління (Ігор та Ольга)"
  words: 300
  points:
  - "Зіставлення експансивної та інституційної моделей"
  - "Перехід від вождівства до регулярної держави"
- section: "Критичне мислення"
  words: 200
  points:
  - "Питання для глибокого аналізу реформ та дипломатії"
- section: "Есе"
  words: 500
  points:
  - "Тема та вимоги до аналітичного есе про деколонізацію простору"
- section: "Зразок відповіді"
  words: 400
  points:
  - "Приклад есе високого рівня для аналізу"
- section: "Підсумок: Засновниця регулярної держави"
  words: 300
  points:
  - "Ольга як архітекторка правового поля України-Руси"
  - "Урок політичного реалізму та візіонерства"
word_target: 5000
vital_status: deceased
build:
  last_modified: '2026-02-05T15:30:00Z'

```

## Your Task

Research **Княгиня Ольга: Дипломатія та реформи** for the **c1-bio** track. Produce structured research notes that will drive content writing in later phases.

### Research Requirements

1. **Sources**: Find 3+ Ukrainian-language academic sources (esu.com.ua, history.org.ua, uk.wikipedia.org, litopys.org.ua). Russian-language sources are PROHIBITED.
2. **Timeline**: Build a chronological timeline with 5+ dated events/milestones.
3. **Primary Quotes**: Find 2+ quotable primary source excerpts (original Ukrainian text preferred).
4. **Engagement Hooks**: Identify 6+ engagement hooks mapped to specific content sections:
   - `[!myth-buster]` — Decolonization: correct imperial/Soviet myths
   - `[!history-bite]` — Surprising or lesser-known facts
   - `[!context]` — Broader historical/cultural context
   - `[!quote]` — Primary source citations
   - `[!decolonization]` — Ukraine-centric reframing
   - `[!culture]` — Cultural significance
5. **Decolonization Angle**: Identify how this topic has been distorted by imperial/Soviet historiography and what the Ukrainian-centric framing should be.
6. **Section-Mapped Content**: Structure notes with headings that match the `content_outline` sections from the meta file. This makes content writing mechanical.

### Contested Terms (if applicable)

If this topic involves contested narratives (Ukrainian vs. Russian/Soviet/Polish historiography), create a Contested Terms Table:

```markdown
## Contested Terms

| Concept | Enemy/Imperial framing | Ukrainian (decolonized) framing |
|---------|----------------------|-------------------------------|
| ...     | ...                  | ...                           |
```

## Output Format

Return your research as structured markdown. Use these exact section headers:

```
===RESEARCH_START===

# Дослідження: Княгиня Ольга: Дипломатія та реформи

## Використані джерела
1. [Source name](URL) — brief description
2. ...
3. ...

## Хронологія
- {date}: {event}
- ...

## Ключові факти та цитати
- ...

## Engagement Hooks (mapped to sections)
- Section "{section_name}": [!hook_type] — description
- ...

## Деколонізаційний контекст
- Imperial/Soviet myth: ...
- Ukrainian reality: ...

## Contested Terms (if applicable)
| Concept | Imperial framing | Ukrainian framing |
|---------|-----------------|-------------------|
| ...     | ...             | ...               |

## Section-Mapped Research Notes

### {Section 1 from content_outline}
Key facts, dates, sources for this section...

### {Section 2 from content_outline}
...

===RESEARCH_END===
```

## Boundaries

- Do NOT write lesson content — only research notes
- Do NOT generate activities or vocabulary
- Do NOT skip any section from the content_outline
- Do NOT use Russian-language sources
- Do NOT fabricate quotes or dates — if unsure, mark as "[needs verification]"
- Do NOT request skills, delegate to Claude, or skip this phase
