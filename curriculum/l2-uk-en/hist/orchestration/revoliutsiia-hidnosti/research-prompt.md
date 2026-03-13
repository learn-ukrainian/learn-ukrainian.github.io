# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: hist-126
level: HIST
sequence: 126
slug: revoliutsiia-hidnosti
version: '2.0'
title: 'Революція Гідності: Євромайдан'
subtitle: 'The Revolution of Dignity: Euromaidan'
focus: history
pedagogy: CBI
phase: HIST.13 [Russian Aggression]
word_target: 5000
objectives:
- Учень може описати причини та хронологію Революції Гідності
- 'Учень може пояснити ключові події: побиття студентів, закони 16 січня, розстріли на Інститутській'
- Учень може проаналізувати роль громадянського суспільства в революції
- Учень може оцінити значення Небесної Сотні для української ідентичності
content_outline:
- section: 'Вступ: Чому «Гідність»?'
  points:
  - '21 листопада 2013: відмова від асоціації з ЄС — уряд Азарова призупиняє підготовку; перший пост Мустафи Найєма як каталізатор'
  - 'Перший Майдан: студенти та європейські прапори — романтичний етап: лекції на відкритому повітрі, пісні, відсутність партійної
    символіки'
  - Чому революція отримала назву «Гідність» — захист права на вибір і честі проти грубої сили; [!context] про символізм дати
    21 листопада (співпадіння з Помаранчевою революцією)
  words: 850
- section: Хронологія подій
  points:
  - Побиття студентів 30 листопада — «Звіряче побиття» «Беркутом» як точка неповернення; include quote зі щоденника або посту
    тієї ночі («Київ, вставай!»)
  - Мільйонний марш 1 грудня — реакція суспільства на насилля; захоплення КМДА та Будинку профспілок; [!history-bite] про
    «Набат» Михайлівського монастиря
  - 'Закони 16 січня: «диктаторські закони» — ручне голосування у ВР, обмеження прав (заборона касок/масок), що призвело до
    ескалації'
  - 'Грушевського та перші жертви — «Вогнехреща» (19-22 січня); перші загиблі: Нігоян, Жизневський, Вербицький'
  - '18-20 лютого: розстріли на Інститутській — «Кривавий четвер», масові вбивства неозброєних протестувальників; [!myth-buster]
    про «печиво Нуланд» та «американські гроші» проти волонтерської самоорганізації'
  - Втеча Януковича — постанова ВР про самоусунення президента; втеча до Росії як акт зради
  words: 850
- section: Небесна Сотня
  points:
  - 'Хто вони: герої революції — люди різного віку (17–83) та професій; свідома пожертва життям (дерев''яні щити проти куль)'
  - Сергій Нігоян — перший загиблий — [!biography] вірменин з Дніпропетровщини, який читав Шевченка (символ політичної нації)
  - Вшанування пам'яті — пісня «Пливе кача по Тисині» як реквієм революції
  - Небесна Сотня як символ — сакралізація жертви заради майбутнього
  words: 850
- section: Первинні джерела
  points:
  - Відеозаписи подій на Майдані — стріми Spilno.tv та Громадського, які дивилися мільйони
  - 'Свідчення учасників — include quote: «Ми вийшли не за Європу, ми вийшли за гідність...»'
  - Журналістські розслідування — документування злочинів режиму проти людяності
  words: 850
- section: Деколонізаційний погляд
  points:
  - 'Російський наратив: «державний переворот» — міф про «путч» та «радикалів» для виправдання агресії'
  - 'Реальність: народне повстання за гідність — [!decolonization] відмова від терміну «пострадянський простір» на користь
    європейської ідентичності'
  - Євромайдан як антиколоніальна революція — завершення радянського періоду («Ленінопад» 8 грудня); суб'єктність народу як
    джерела влади
  words: 850
- section: 'Підсумок: Наслідки революції'
  points:
  - Перемога і початок війни — Росія скористалася тимчасовим ослабленням влади для окупації Криму
  - Україна на шляху до Європи — народження потужного волонтерського руху та громадянського суспільства
  - Спадщина Майдану — перехід російськомовних на українську як акт політичного самовизначення
  words: 750
vocabulary_hints:
  required:
  - гідність (dignity) — Революція Гідності, захищати гідність
  - Майдан (Maidan) — вийти на Майдан, Євромайдан
  - революція (revolution) — мирний протест, Революція Гідності vs державний переворот
  - протест (protest) — мирний протест, учасники протесту
  - Небесна Сотня (Heavenly Hundred) — герої Небесної Сотні, вшанування пам'яті
  - свобода (freedom) — ціна свободи, боротьба за свободу
  - демократія (democracy) — демократичні цінності, захист демократії
  - євроінтеграція (European integration) — курс на євроінтеграцію, Угода про асоціацію
  recommended:
  - беркут (Berkut) — жорстокість «Беркуту», розгін студентів
  - барикади (barricades) — будувати барикади, стояти на барикадах
  - автомайдан (Automaidan) — колона Автомайдану
  - тітушки (titushky) — найманці влади, провокатори
  - самооборона (self-defense) — загони самооборони Майдану
  - люстрація (lustration) — вимога люстрації влади
activity_hints:
- type: reading
  focus: Свідчення учасників Майдану
  source: Усна історія
  items: 4
- type: essay-response
  focus: Чому Революцію 2014 року називають «Революцією Гідності»?
connects_to:
- hist-128 (Анексія Криму)
- hist-131 (Війна на Донбасі 2014-2022)
prerequisites:
- 'hist-124 (Епоха Януковича: Реванш)'
persona:
  voice: Senior Professor of History
  role: Maidan Medic
grammar:
- Минулий час у хронологічному наративі
- Політична та соціальна лексика
- Складнопідрядні речення
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Революція Гідності: Євромайдан** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

### Your RAG Tools (USE THEM)

You have access to Ukrainian language tools via MCP. **Use them during research.**

| Tool | When to use | Example |
|------|-------------|---------|
| `query_wikipedia` mode=`extract` | Get full article text (50K chars) for deep research | `query_wikipedia("Богдан Хмельницький", mode="extract")` |
| `query_wikipedia` mode=`sections` | See article structure before diving in | `query_wikipedia("Запорізька Січ", mode="sections")` |
| `query_wikipedia` mode=`section` | Read a specific section by index | `query_wikipedia("Запорізька Січ", mode="section", section=3)` |
| `query_wikipedia` mode=`search` | Find the right article title | `query_wikipedia("Переяславська рада", mode="search")` |
| `search_literary` | Find primary source excerpts (chronicles, poetry, legal texts) | `search_literary("Хмельницький", genre="chronicle")` |
| `verify_word` / `verify_words` | Check Ukrainian words exist in VESUM dictionary | `verify_words(["гетьман", "козацтво"])` |
| `query_grac` | Check word frequency in Ukrainian corpus | `query_grac("упокорення", mode="frequency")` |

**Workflow**: Search Wikipedia FIRST for factual foundation → search literary RAG for primary quotes → verify vocabulary with VESUM.

### Research Requirements

1. **Sources**: Use `query_wikipedia` (mode=`extract`) for Ukrainian Wikipedia articles. Also consult history.org.ua, litopys.org.ua. Use `search_literary` for primary source excerpts. Russian-language sources are PROHIBITED.
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
6. **Section-Mapped Content**: Structure notes with headings that match the `content_outline` sections from the plan. This makes Phase B content writing mechanical.

### Research Output Cap
Keep research notes under **4000 words** (seminar tracks need depth for historiographical mapping).
Focus on density: Key Facts Ledger, timeline, primary quotes, section-mapped notes.

If this topic involves contested narratives (Ukrainian vs. Russian/Soviet/Polish historiography), include a Contested Terms Table:

```markdown
## Contested Terms

| Concept | Imperial framing | Ukrainian (decolonized) framing |
|---------|-----------------|-------------------------------|
| ...     | ...             | ...                           |
```

---

## Downstream Audit Gates (Phase B content will be checked for)

Plan your research and outline knowing that Phase B content must pass these gates:
- **Word count**: minimum **5000** words — allocate outline sections accordingly
- **Colonial framing**: plan decolonized framing NOW so Phase B doesn't default to Russian comparisons
- **Engagement callouts**: map 6+ hooks to specific sections during research (not as afterthought patches)
- **Duplicate headers**: ensure outline section names don't share keywords

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

### Output Block 1: Research Notes

```
===RESEARCH_START===

# Дослідження: Революція Гідності: Євромайдан

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — Phase D verifies prose against this -->
```yaml
subject: "Революція Гідності: Євромайдан"
vital_status: "deceased" # or "alive"
dates:
  birth: "YYYY-MM-DD"    # or approximate: "~YYYY"
  death: "YYYY-MM-DD"    # omit if alive
  key_events:
    - year: YYYY
      event: "Event description (Ukrainian)"
    - year: YYYY
      event: "Event description"
primary_quotes:
  - text: "Exact Ukrainian quote"
    source: "Source name, year"
    attribution: "Who said/wrote it"
  - text: "..."
    source: "..."
    attribution: "..."
forbidden_claims:
  - "Common myth or Russian propaganda claim to avoid"
  - "..."
```

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

## Відеоресурси
(Якщо під час дослідження ви натрапили на релевантні відеоматеріали — документальні фільми, архівні записи, інтерв'ю — зазначте їх тут. НЕ шукайте відео спеціально — це робить фаза discover. Максимум 3 записи.)
- {Канал — Назва — URL — Короткий опис релевантності}
- (нічого не знайдено)

## Section-Mapped Research Notes

### {Section 1 from content_outline}
Key facts, dates, sources for this section...

### {Section 2 from content_outline}
...

===RESEARCH_END===
```

## Friction Report (MANDATORY)

After both output blocks, include:

```
===FRICTION_START===
**Phase**: Phase A: Research + Meta (Seminar)
**Step**: {what you were doing when friction occurred, or "Full Phase A"}
**Friction Type**: NONE | TOKEN_LIMIT_TRUNCATION | TOOL_REDUNDANCY | SOURCE_NOT_FOUND | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===
```

---

## Boundaries

- Do NOT write lesson content — only research notes
- Do NOT generate activities or vocabulary
- Do NOT skip any section from the plan's content_outline
- Do NOT use Russian-language sources
- Do NOT fabricate quotes or dates — if unsure, mark as "[needs verification]"
- Do NOT reference persona names or voice instructions — persona is assigned at content generation time
- Do NOT request skills, delegate to Claude, or skip this phase
