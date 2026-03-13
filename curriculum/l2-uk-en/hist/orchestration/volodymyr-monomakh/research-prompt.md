# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: hist-015
level: HIST
sequence: 15
slug: volodymyr-monomakh
version: '2.0'
title: Володимир Мономах
subtitle: The Last Great Prince of United Rus
focus: history
pedagogy: seminar
phase: HIST.2 [Kyivan Rus]
word_target: 5000
objectives:
- Учень може проаналізувати правління Володимира Мономаха та його вплив на єдність Русі
- Учень може пояснити значення «Повчання дітям» як унікального літературного та філософського твору
- Учень може оцінити роль Любецького з'їзду в історії Русі
- Учень може порівняти внутрішню і зовнішню політику Мономаха з іншими князями доби
sources:
- name: Володимир Мономах (Вікіпедія)
  url: https://uk.wikipedia.org/wiki/Володимир_Мономах
  type: reference
- name: Повчання Володимира Мономаха (Електронні Літописи)
  url: https://litopys.org.ua/pvl/pvl21.htm
  type: primary
content_outline:
- section: Вступ
  points:
  - 'Значення постаті Володимира Мономаха — символ мудрості та єдності, «останній великий князь» об''єднаної Русі; hook: [!context]
    про його популярність серед киян'
  words: 300
- section: 'Читання: Момент істини в Києві'
  points:
  - 'Повстання 1113 року — причини: спекуляції сіллю та лихварство; hook: [!history-bite] про початок з єврейського погрому
    та легітимний вибір віча'
  words: 300
- section: 'Хронологія: Шлях до великого княжіння'
  points:
  - 'Військова кампанія 1111 року — Хрестовий похід у степ (битва при Сальниці); ключові дати: 1053 (народження), 1094-1113
    (оборона Переяслава)'
  words: 300
- section: 'Глибоке занурення: Династична криза 1093-1113 років: Шлях крізь темряву'
  points:
  - Трагедія на Стугні — та шок від осліплення Василька Теребовлянського (порушення клятви); роль Мономаха як арбітра та миротворця
  words: 300
- section: 'Аналіз: Любецький з''їзд 1097 року: Мистецтво компромісу'
  points:
  - 'Принцип вотчини — «Кождо да держить отчину свою» задля об''єднання проти половців; hook: [!quote] «Нащо губимо Руськую
    землю...»'
  words: 300
- section: 'Внутрішня політика: Великий реформатор та Законодавець'
  points:
  - Устав 1113 року — обмеження різу (відсотка) до 50%, захист банкрутів та «закупів»; запобігання соціальному вибуху
  words: 300
- section: 'Культура: Культурний ренесанс епохи Мономаха'
  points:
  - Архітектура та літописання — редакція «Повісті минулих літ» (Сильвестр, 1116), будівництво церков та мосту через Дніпро
  words: 300
- section: 'Глибоке занурення: «Повчання дітям»: Літературний шедевр епохи'
  points:
  - 'Моральні настанови — відповідальність, гуманізм («не вбивайте ні правого, ні винного»), освіта; hook: [!myth-buster]
    перша світська автобіографія'
  words: 300
- section: 'Розмова: Родина Мономаха: Династія великих справ та європейські зв''язки'
  points:
  - 'Гіта Вессекська — донька короля Гарольда (загинув при Гастінгсі 1066); династичні шлюби з Швецією, Візантією, Угорщиною;
    hook: [!context]'
  words: 300
- section: 'Сьогодення: Економічне життя та Побут Русі'
  points:
  - Життя міст — Київ як європейський мегаполіс (50 тис.), експорт хутра/воску, імпорт вина/зброї; гривня як срібний зливок
  words: 300
- section: 'Погляд: Військове мистецтво та Озброєння'
  points:
  - Озброєння дружини — перехід до активних превентивних ударів; шоломи типу «Чорна могила», мигдалевидні щити, шаблі
  words: 300
- section: 'Первинні джерела: Голоси вічності'
  points:
  - Аналіз уривків — Лаврентіївський літопис про битву на Сальниці; легенда про допомогу ангелів
  words: 300
- section: 'Деколонізаційний погляд: Мономах — наш, а не їхній'
  points:
  - 'Спростування міфу про Шапку Мономаха — це тюбетейка XIV ст. (дар хана Узбека); hook: [!decolonization] про московське
    привласнення спадщини'
  words: 300
- section: Підсумкове есе
  points:
  - Завдання для есе
  words: 300
- section: Оцінювання есе
  points:
  - Модельна відповідь та рубрика
  words: 300
- section: 'Погляд: Потрібно більше практики?'
  points:
  - Додаткові ресурси
  words: 500
vocabulary_hints:
  required:
  - великий князь (grand prince) — титул правителя Києва
  - отчина (patrimony, hereditary domain) — принцип «кожен хай держить отчину свою»
  - половці (Polovtsians, Cumans) — кочовий народ, основний ворог Русі
  - з'їзд (congress, assembly) — Любецький з'їзд князів
  - усобиця (internecine strife) — братовбивчі війни за владу
  - устав (statute, charter) — законодавчий акт, Устав Володимира Мономаха
  - лихварство (usury) — надання грошей у борг під високий відсоток
  - боржник (debtor) — захист прав боржників у «Уставі»
  - повчання (instruction, teaching) — літературний жанр, «Повчання дітям»
  - настанова (admonition, precept) — моральна порада
  - працелюбність (diligence, industriousness) — ключова чеснота за Мономахом
  - шапка Мономаха (Monomakh's Cap) — імперський міф, фальсифікат XIV ст.
  - єдність (unity) — головна політична мета князя
  - роздроблення (fragmentation) — феодальна роздробленість Русі
  - степ (steppe) — зона кочовиків, походів
  - полководець (military commander) — Мономах провів 83 великі походи
  - засліплення (blinding) — жорстоке покарання (Василько Теребовлянський)
  - Любеч (Liubech) — місце з'їзду 1097 року
  - Теrebovlia (Terebovlia) — князівство Василька
  - Візантія (Byzantium) — батьківщина матері Мономаха
  recommended:
  - автобіографія (autobiography) — жанрова особливість «Повчання»
  - гуманізм (humanism) — ставлення до людського життя
  - етика (ethics) — християнська етика правителя
  - династичний шлюб (dynastic marriage) — інструмент зовнішньої політики
  - літопис (chronicle) — джерело історичних знань
activity_hints:
- type: reading
  focus: Уривок з «Повчання дітям» про працелюбність
- type: essay-response
  focus: Чому «Повчання дітям» є унікальним для середньовічної Європи?
- type: comparative-study
  focus: Любецький з'їзд vs Віче
  output: Comparison table
- type: critical-analysis
  focus: Аналіз 'Повчання дітям' як історичного джерела
  questions: 3+
connects_to:
- 'hist-16: Культура Київської Русі'
- 'hist-17: Княжі усобиці'
prerequisites:
- 'hist-12: Ярослав Мудрий'
- 'hist-13: Руська Правда'
persona:
  voice: Senior Professor of History
  role: Prince's Tutor
grammar:
- 'Історичний наратив: минулий час доконаного виду'
- Складні речення з підрядними причини та наслідку
- Вживання дієприкметників у публіцистичному стилі
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Володимир Мономах** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Володимир Мономах

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — Phase D verifies prose against this -->
```yaml
subject: "Володимир Мономах"
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
