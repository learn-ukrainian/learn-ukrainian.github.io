# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-074
level: HIST
sequence: 74
slug: kinets-hetmanshchyny
version: '2.0'
title: Кінець Гетьманщини
subtitle: The End of the Hetmanate
focus: history
pedagogy: CBI
phase: B2.3b [Українська історія]
word_target: 5000
objectives:
- Учень може описати процес ліквідації Гетьманщини
- Учень може проаналізувати наслідки знищення Січі
- Учень може пояснити причини запровадження кріпацтва
- Учень може оцінити роль Катерини II в українській історії
content_outline:
- section: Вступ
  points:
  - Контекст занепаду автономії Гетьманщини у XVIII столітті — «Золота осінь» Кирила Розумовського та спроби реформ (судова,
    військова, Батуринський університет)
  - Російська імперська політика централізації влади — епоха «освіченого абсолютизму», де Гетьманщина була аномалією
  - Значення ліквідації гетьманства для української історії — інсценізована «Глухівська рада» 1764 року та примусова відставка
    Розумовського
  words: 850
- section: Читання
  points:
  - 'Скасування гетьманства Катериною II у 1764 році — створення Другої Малоросійської колегії на чолі з П. Румянцевим; cultural
    hook: інструкція про стирання пам''яті про гетьманів'
  - Знищення Запорізької Січі у 1775 році — напад військ генерала Текелія після війни з Туреччиною; арешт Петра Калнишевського
    (Соловецький монастир)
  - Запровадження кріпацтва на українських землях — указ 1783 року, що завершив 300 років козацької свободи
  - Ліквідація козацьких привілеїв та автономії — перетворення полків на гусарські (1765), скасування полкового устрою на
    Гетьманщині (1781)
  - Російська колонізація та русифікація українських земель — бренд «Новоросія» на козацьких землях, роздача земель російським
    дворянам та іноземцям
  - Політика асиміляції української еліти — надання прав російського дворянства в обмін на лояльність («Малоросійське дворянство»)
  - Економічні наслідки інкорпорації до Російської імперії — Румянцевський опис (1765–1769) як підготовка до тотального оподаткування
  - Культурний занепад та втрата національних інституцій — заміна козацького судочинства та адміністрації намісництвами
  words: 850
- section: Деколонізаційний погляд
  points:
  - Ліквідація Гетьманщини як акт колонізації — використання термінів «анексія» та «інкорпорація» замість «об'єднання»
  - Спростування російських наративів про «об'єднання братніх народів» — [!myth-buster] міф про «Дике Поле» та «цивілізаційну
    місію» імперії
  - Наслідки втрати державності для української нації — перетворення політичної нації на етнографічну масу («земляцтво»)
  words: 850
- section: Первинні джерела
  points:
  - 'Укази Катерини II про скасування гетьманства — Маніфест 1775 року: «Самое названіе Запорожскихъ Козаковъ... на вѣчныя
    времена истребить»'
  - Свідчення сучасників про руйнування Січі — [!quote] спогади Микити Коржа про сльози козаків, що брали рідну землю в чоботи
  - Документи про впровадження кріпацтва — юридичне закріпачення селян Лівобережжя та Слобожанщини (1783)
  - 'Листи та спогади українських козаків про трагедію — [!quote] «Історія Русів»: «Рум''янцівська колегія увійшла... як паморозь
    на руно»'
  words: 850
- section: Підсумок
  points:
  - Ліквідація Гетьманщини як кінець української державності — цивілізаційна катастрофа, втрата політичного класу та війська
  - Початок нового періоду колонізації та русифікації — [!history-bite] початок «довгого XIX століття» бездержавності, що
    тривало до 1917 року
  words: 850
- section: Потрібно більше практики?
  points:
  - Додаткові матеріали для поглибленого вивчення теми
  words: 750
vocabulary_hints:
  required:
  - ліквідація (liquidation) — ліквідація Запорізької Січі (1775), ліквідація автономії
  - кріпацтво (serfdom) — запровадження кріпацтва (1783), кріпацька неволя
  - скасування (abolition) — скасування гетьманства, скасування полкового устрою
  - централізація (centralization) — імперська централізація, уніфікація управління
  - асиміляція (assimilation) — асиміляція козацької старшини, політика асиміляції
  - русифікація (Russification) — русифікація адміністрації, заборона мови
  - автономія (autonomy) — втрата автономії, залишки автономії
  - колонізація (colonization) — колонізація Півдня України, імперська колонізація
  recommended:
  - інкорпорація (incorporation) — інкорпорація до складу імперії
  - занепад (decline) — занепад культури, політичний занепад
  - привілеї (privileges) — козацькі привілеї, дворянські привілеї
  - козацька старшина (Cossack officers) — лояльність старшини, перетворення на дворянство
activity_hints:
- type: reading
  focus: The destruction of Ukrainian statehood
  items: 1
- type: essay-response
  focus: Decolonizing the Russian imperial narrative
  items: 1
- type: critical-analysis
  focus: 'Критичний аналіз послідовності: Key events leading to the end of the Hetmanate'
  items: 1
- type: critical-analysis
  focus: 'Критична оцінка: Consequences of Russian centralization'
  items: 1
persona:
  voice: Senior Professor of History
  role: General Pysar
grammar:
- Пасивні конструкції
- Історична термінологія
register: публіцистичний
prerequisites:
- petro-kalnyshevskyi
connects_to:
- rosiiska-imperiia-ukraina

```

---

## PART 1: Deep Research

Research **Кінець Гетьманщини** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

### Your RAG Tools (USE THEM)

You have access to Ukrainian language tools via MCP. **Use them during research.**

| Tool | When to use | Args |
|------|-------------|------|
| `query_wikipedia` | Get full article text (50K chars) for deep research | `query`, `mode="extract"` |
| `query_wikipedia` | See article structure before diving in | `query`, `mode="sections"` |
| `query_wikipedia` | Read a specific section by index | `query`, `mode="section"`, `section=N` |
| `query_wikipedia` | Find the right article title | `query`, `mode="search"` |
| `search_literary` | Find primary source excerpts (chronicles, poetry, legal texts, testimonies) | `query`, `genre` (optional) |
| `verify_words` | Check Ukrainian words exist in VESUM dictionary | `words` (list of strings) |
| `query_grac` | Check word frequency in Ukrainian corpus | `query`, `mode="frequency"` |

> **Important**: Invoke these tools using your standard tool-calling interface. Do NOT write Python code.

**Workflow**: Search Wikipedia FIRST for factual foundation → search literary RAG for primary quotes → verify vocabulary with VESUM.

### Research Requirements

1. **Sources**: Use `query_wikipedia` (mode=`extract`) for Ukrainian Wikipedia articles. Also consult history.org.ua, litopys.org.ua. Use `search_literary` for primary source excerpts. Russian-language sources are PROHIBITED.
2. **Timeline**: Build a chronological timeline with 5+ dated events/milestones.
3. **Primary Quotes**: Find 2+ quotable primary source excerpts (original Ukrainian text preferred).
4. **Engagement Hooks**: Research and expand upon any hooks already suggested in the `content_outline`, and add new ones to reach a minimum of 6 total hooks mapped to specific content sections:
   - `[!myth-buster]` — Decolonization: correct imperial/Soviet myths
   - `[!history-bite]` — Surprising or lesser-known facts
   - `[!context]` — Broader historical/cultural context
   - `[!quote]` — Primary source citations
   - `[!decolonization]` — Ukraine-centric reframing
   - `[!culture]` — Cultural significance
5. **Decolonization Angle**: Identify how this topic has been distorted by imperial/Soviet historiography (e.g., erasure of identity, stripping of local agency, Soviet tropes) and define the Ukrainian-centric framing (centering local agency, restoring historical truth, using accurate terminology).
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
- **Colonial framing**: plan decolonized framing NOW so Phase B doesn't default to Soviet tropes (e.g., erasure of victim identity), imperial terminology, or Moscow-centric timelines
- **Engagement callouts**: map 6+ hooks to specific sections during research (not as afterthought patches)
- **Duplicate headers**: ensure outline section names don't share keywords

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

### Output Block 1: Research Notes

===RESEARCH_START===

# Дослідження: Кінець Гетьманщини

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Кінець Гетьманщини"
type: "event" # "event", "biography", or "phenomenon"
vital_status: "living" # ONLY for biography: "living" or "deceased" (omit for events)
dates:
  start: "YYYY-MM-DD" # Event start OR biography birth (approximate: "~YYYY")
  end: "YYYY-MM-DD"   # Event end OR biography death (omit if living/ongoing)
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
- Section "{section_name}": [!hook_type] — {raw research fact/data to be used for this hook in Phase B}
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

## Friction Report (MANDATORY)

After Output Block 1, include the Friction Report:

===FRICTION_START===
**Phase**: Phase A: Research + Meta (Seminar)
**Step**: {what you were doing when friction occurred, or "Full Phase A"}
**Friction Type**: NONE | TOKEN_LIMIT_TRUNCATION | TOOL_REDUNDANCY | SOURCE_NOT_FOUND | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===

---

## Boundaries

- Do NOT write lesson content — only research notes
- Do NOT generate activities or vocabulary
- Do NOT skip any section from the plan's content_outline
- Do NOT use Russian-language sources
- Do NOT fabricate quotes or dates — if unsure, mark as "[needs verification]"
- Do NOT reference persona names or voice instructions — persona is assigned at content generation time
- Do NOT request skills, delegate to Claude, or skip this phase
