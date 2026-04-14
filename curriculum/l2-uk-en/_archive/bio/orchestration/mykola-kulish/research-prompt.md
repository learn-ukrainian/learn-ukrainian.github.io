# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: bio-098
level: BIO
sequence: 98
slug: mykola-kulish
version: '2.0'
title: 'Микола Куліш: Геній українського театру'
focus: biography
phase: BIO
word_target: 5000
objectives:
- Дізнатися про життя та творчість Миколи Куліша
- Проаналізувати його найважливіші п'єси
- Зрозуміти значення Куліша для українського театру
- Осмислити трагедію Розстріляного відродження
sources:
- name: Микола Куліш (Енциклопедія історії України)
  url: https://esu.com.ua/article-7980
  type: primary
  notes: Академічна біографія
- name: Куліш М. П'єси
  type: primary
  notes: Збірка драматичних творів
- name: Жулинський М. Микола Куліш
  type: reference
  notes: Монографія про творчість
content_outline:
- section: Вступ — Найбільший драматург XX століття
  points:
  - Куліш як геній українського театру
  - Доля митця в тоталітарній системі
  - Його місце в Розстріляному відродженні
  words: 700
- section: Ранні роки та освіта
  points:
  - Дитинство на Херсонщині (Чаплинка, 1892)
  - Освіта та перші літературні спроби
  - Участь у визвольних змаганнях (1917-1920)
  words: 700
- section: Становлення драматурга
  points:
  - «97» — перша велика п'єса (1924)
  - Співпраця з театром «Березіль»
  - Творчий тандем із Лесем Курбасом
  words: 700
- section: Великі п'єси
  points:
  - «Комуна в степах» (1925)
  - «Народний Малахій» (1927)
  - «Мина Мазайло» (1929) — сатира на русифікацію
  - «Патетична соната» (1929)
  - «Маклена Граса» (1933)
  words: 700
- section: Художній світ Куліша
  points:
  - Експресіонізм та модернізм
  - Мовне питання у творчості
  - Сатира та трагедія
  - Український характер у п'єсах
  words: 700
- section: Переслідування та загибель
  points:
  - Критика та цькування (початок 1930-х)
  - Арешт 1934 року
  - Соловки
  - Розстріл у Сандармосі (3 листопада 1937)
  words: 700
- section: Спадщина та реабілітація
  points:
  - Реабілітація (1957)
  - Повернення на сцену
  - Куліш у сучасному театрі
  - Значення для української культури
  words: 800
vocabulary_hints:
  required:
  - драматург (playwright)
  - п'єса (play)
  - театр «Березіль» (Berezil Theatre)
  - режисер (director)
  - експресіонізм (expressionism)
  - Розстріляне відродження (Executed Renaissance)
  - русифікація (Russification)
  - реабілітація (rehabilitation)
  - Соловки (Solovki)
  - Сандармох (Sandarmokh)
  recommended:
  - модернізм (modernism)
  - сатира (satire)
  - абсурд (absurd)
  - тоталітаризм (totalitarianism)
activity_hints:
- type: reading
  focus: Фрагменти п'єси «Мина Мазайло»
  source: Первинне джерело
  items: 3 passages
- type: essay-response
  focus: Мовне питання у творчості Куліша
  output: Аргументований есей
- type: critical-analysis
  focus: Порівняння долі Куліша та Курбаса
connects_to:
- bio/les-kurbas
- bio/mykola-khvylovyi
prerequisites:
- hist/rozstriliane-vidrodzennia
- hist/mekhanizm-teroru
persona:
  voice: Senior Biographer
  role: Social Satirist
module_type: biography
immersion: 100% Ukrainian
notes: 'Mykola Kulish is considered the greatest Ukrainian playwright of the 20th century.

  His plays combined modernist techniques with deep exploration of Ukrainian identity

  and the absurdities of Soviet reality. "Myna Mazailo" brilliantly satirized

  linguistic assimilation. His partnership with director Les Kurbas created

  legendary theatrical productions. Both were arrested in 1934 and executed on

  the same day (November 3, 1937) in the Sandarmokh mass execution.

  '

```

---

## PART 1: Deep Research

Research **Микола Куліш: Геній українського театру** for the **bio** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Микола Куліш: Геній українського театру

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — Phase D verifies prose against this -->
```yaml
subject: "Микола Куліш: Геній українського театру"
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
