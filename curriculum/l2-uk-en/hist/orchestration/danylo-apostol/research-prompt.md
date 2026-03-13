# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-070
level: HIST
sequence: 70
slug: danylo-apostol
version: '2.0'
title: Данило Апостол та Кирило Розумовський
subtitle: 'The Last Hetmans: Apostol and Rozumovsky'
focus: history
pedagogy: CBI
phase: B2.3b [Українська історія]
word_target: 5000
objectives:
- Учень може порівняти правління Данила Апостола та Кирила Розумовського
- Учень може пояснити причини ліквідації гетьманства
- Учень може охарактеризувати культурний розвиток Глухова
- Учень може проаналізувати Рішительні пункти
content_outline:
- section: 'Вступ: Між молотом і ковадлом'
  points:
  - 'Гетьманщина у XVIII столітті між Російською та Османською імперіями — контекст геополітичного тиску після Полтави 1709
    року; hook: [!context] про державні інституції Гетьманщини'
  - Скорочення автономії козацької держави — перехід від протекторату до прямого управління (Перша Малоросійська колегія 1722-1727)
  - Два гетьмани як символи різних стратегій виживання — Апостол (стара козацька еліта, юридичний опір) vs Розумовський (нова
    аристократія, культурна інтеграція)
  words: 700
- section: 'Читання: Епоха Данила Апостола'
  points:
  - Обрання Данила Апостола гетьманом 1727 року — Глухівська рада, 73-річний досвідчений політик, відновлення гетьманства
    через турецьку загрозу
  - 'Його політика збереження козацьких вольностей — петиція до Петра II про відновлення статей Богдана Хмельницького; hook:
    [!myth-buster] про активність «старого» гетьмана'
  - Рішительні пункти як спроба законодавчого закріплення автономії — 1728 рік, односторонній указ імперії замість двостороннього
    договору, обмеження дипломатії та фінансів
  - Боротьба за економічні інтереси Гетьманщини — «Генеральне слідство про маєтності» (1729-1731) для повернення державних
    земель, боротьба з корупцією
  words: 700
- section: 'Економіка та суспільство: Стабільність і криза'
  points:
  - Економічний розвиток Гетьманщини за часів Апостола — формування першого чіткого державного бюджету, захист від російських
    митників
  - Соціальна структура та розшарування козацтва — перетворення козацької старшини на дворянство, відрив від рядового козацтва
  - 'Торгівля та ремесла в містах — відновлення експорту (зерно, шкіра) через Вроцлав/Гданськ всупереч імперським заборонам;
    hook: [!history-bite]'
  - Наростання соціальних протиріч — захоплення земель старшиною та російськими дворянами, початок закріпачення селян
  words: 700
- section: 'Епоха Розумовського: Європейська мрія'
  points:
  - Кирило Розумовський як останній гетьман України — обрання 1750 року (заочно), брат фаворита імператриці, спроба модернізації
    за європейським зразком
  - Його європейська освіта та придворне життя — реформи 1760-1763 років (судова, військова, проект університету в Батурині)
  - 'Глухів як культурна столиця Гетьманщини — італійська опера, французькі парки, палаци («маленький Петербург»); hook: [!culture]'
  - Розквіт барокової культури та архітектури — «Золота осінь» Гетьманщини, спроба зробити гетьманство спадковим (петиція
    1763 року)
  words: 700
- section: 'Первинні джерела: Голоси епохи'
  points:
  - Фрагменти з Рішительних пунктів — цитати про контроль над військом та фінансами («в каком состоянии та артиллерия ныне
    есть...»)
  - 'Документи про ліквідацію гетьманства — інструкція Катерини II («щоб час і назва гетьманів зникли»); hook: [!quote]'
  - Листування гетьманів з царським двором — риторика прохання про «права і вольності» vs імперські накази
  words: 700
- section: 'Деколонізаційний погляд: Дві стратегії виживання'
  points:
  - Апостол та Розумовський як різні моделі відповіді на імперський тиск — консервація старих прав vs модернізація еліти
  - Спроби збереження автономії через законодавство vs культурну інтеграцію — чому обидві стратегії зазнали краху перед абсолютизмом
  - 'Наслідки втрати державності для українського народу — перетворення «Гетьманщини» на «Малоросію», ліквідація інституцій;
    hook: [!decolonization]'
  words: 700
- section: 'Підсумок: Захід сонця'
  points:
  - Ліквідація Гетьманщини Катериною II 1764 року — примусова відставка Розумовського, створення Другої Малоросійської колегії
    (Румянцев)
  - Причини та наслідки втрати української автономії — страх імперії перед окремішністю, уніфікація управління
  - Доля козацької старшини після знищення гетьманства — інтеграція в російське дворянство, втрата політичної суб'єктності
  - Історичні уроки для сучасності — автономія без незалежності неможлива, культурний розквіт без війська крихкий
  words: 800
vocabulary_hints:
  required:
  - 'гетьман (hetman) — collocations: обрати гетьмана, останній гетьман, влада гетьмана'
  - 'автономія (autonomy) — collocations: обмеження автономії, збереження автономії, втрата автономії'
  - 'козацтво (Cossackdom) — collocations: рядове козацтво, права козацтва'
  - 'старшина (Cossack elite) — collocations: генеральна старшина, козацька старшина, корупція старшини'
  - 'вольності (liberties) — collocations: козацькі вольності, права і вольності, захист вольностей'
  - 'ліквідація (liquidation) — collocations: ліквідація гетьманства, ліквідація устрою, остаточна ліквідація'
  - 'бароко (baroque) — collocations: українське бароко, козацьке бароко, культура бароко'
  - 'імперія (empire) — collocations: Російська імперія, тиск імперії, політика імперії'
  recommended:
  - 'протиріччя (contradiction) — collocations: соціальні протиріччя, внутрішні протиріччя'
  - 'розшарування (stratification) — collocations: майнове розшарування, соціальне розшарування'
  - 'інтеграція (integration) — collocations: культурна інтеграція, імперська інтеграція'
  - 'законодавство (legislation) — collocations: імперське законодавство, кодифікація законодавства'
activity_hints:
- type: reading
  focus: Фрагменти з Рішительних пунктів
  items: 4
- type: essay-response
  focus: Порівняння двох гетьманів
- type: critical-analysis
  focus: 'Критичний аналіз послідовності: Період від обрання Апостола до ліквідації гетьманства (1727-1764)'
  items: 3
- type: critical-analysis
  focus: 'Верифікація фактів: Факти про правління двох гетьманів'
  items: 5
persona:
  voice: Senior Professor of History
  role: Hetman's Treasurer
grammar:
- Історичний наратив
- Пасивний стан в історичному тексті
register: публіцистичний
prerequisites:
- pavlo-polubotok
connects_to:
- koliivshchyna

```

---

## PART 1: Deep Research

Research **Данило Апостол та Кирило Розумовський** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Данило Апостол та Кирило Розумовський

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Данило Апостол та Кирило Розумовський"
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
