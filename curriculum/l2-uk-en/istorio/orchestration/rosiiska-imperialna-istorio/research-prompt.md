# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: istorio-003
level: ISTORIO
sequence: 3
slug: rosiiska-imperialna-istorio
version: '1.0'
title: Російська імперіальна історіографія
focus: history
pedagogy: seminar
word_target: 5000
objectives:
- Analyze the causes and consequences of російська імперіальна історіографія
- Evaluate the historical significance of імперська історіографія як зброя
- Trace the development of критичний аналіз і деконструкція
sources:
- name: Михайло Погодін (Вікіпедія)
  url: https://uk.wikipedia.org/wiki/Погодін_Михайло_Петрович
  type: reference
  notes: Creator of "Pogodin theory" denying Ukrainian distinctiveness
- name: Теорія Погодіна
  url: https://uk.wikipedia.org/wiki/Теорія_Погодіна
  type: reference
  notes: The theory itself explained
- name: Малоросійство
  url: https://uk.wikipedia.org/wiki/Малоросійство
  type: reference
  notes: «Little Russia» ideology analysis
- name: Serhii Plokhy - Lost Kingdom
  url: https://www.huri.harvard.edu/publications/lost-kingdom-the-quest-for-empire-and-the-making-of-the-russian-nation
  type: secondary
  notes: Modern analysis of Russian imperial nationalism
content_outline:
- section: Вступ — Імперська історіографія як зброя
  points:
  - Історія як інструмент легітимації імперії
  - Чому Росія потребувала «привласнити» українську історію
  - Київ як «колиска» — чия саме?
  words: 700
- section: Карамзін і початок імперського наративу
  points:
  - «Історія держави Російської» (1816-1829)
  - Київська Русь як «початок Росії»
  - Нема окремих українців — є «малороси»
  - Вплив на російську свідомість
  words: 700
- section: Теорія Погодіна
  points:
  - Михайло Погодін (1800-1875)
  - Суть теорії — українці «прийшли» після монголів
  - «Справжні» кияни пішли на північ → москвичі
  - Наукова критика теорії (Грушевський, Антонович)
  - Чому теорія досі популярна в Росії
  words: 700
- section: Концепція "Малоросії"
  points:
  - Термін «Малоросія» — походження та еволюція
  - Від географії до ідеології
  - «Малорос» як неповноцінний росіянин
  - Культурна асиміляція як мета
  words: 700
- section: Радянська версія імперського наративу
  points:
  - «Возз'єднання» 1654 — офіційний міф
  - «Братні народи» — ієрархія братів
  - Табуйовані теми — Голодомор, репресії, ОУН
  - Продовження царської схеми у новій формі
  words: 700
- section: Сучасна російська історіографія
  points:
  - Путінські історичні есе (2021)
  - «Один народ» — заперечення українців
  - Історія як виправдання війни
  - Від Погодіна до Путіна — безперервність
  words: 700
- section: Критичний аналіз і деконструкція
  points:
  - Як розпізнати імперський наратив
  - Ключові маркери пропаганди
  - Українська відповідь
  words: 800
vocabulary_hints:
  required:
  - історія (history)
  - подія (event)
  - джерело (source)
  - аналіз (analysis)
  recommended:
  - контекст (context)
  - інтерпретація (interpretation)
  - наслідки (consequences)
vocabulary:
- імперський наратив
- Малоросія / малорос
- возз'єднання
- привласнення
- легітимація
- асиміляція
- теорія Погодіна
- колиска
- братні народи
- один народ
- спадкоємність
- історична пам'ять
- фальсифікація
- деконструкція
- ідеологія
activity_hints:
- type: reading
  focus: Первинні джерела
  items: 4
- type: essay-response
  focus: Критичний аналіз
- type: true-false
  focus: Факти та інтерпретації
  items: 10
activities:
- type: reading
  focus: Excerpt from Putin's 2021 essay "On the Historical Unity of Russians and Ukrainians"
- type: critical-analysis
  focus: Identify 5 markers of imperial narrative in a Russian textbook excerpt
- type: comparative-study
  focus: Same event (1654) in Ukrainian vs Russian textbook
- type: essay-response
  focus: Чому теорія Погодіна є науково неспроможною?
persona:
  voice: Academic Historiographer
  role: Empire Studies Critic
prerequisites:
- ukrainska-istoriohrafichna-tradytsiia
connects_to:
- radyanska-istorio

```

---

## PART 1: Deep Research

Research **Російська імперіальна історіографія** for the **istorio** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Російська імперіальна історіографія

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — Phase D verifies prose against this -->
```yaml
subject: "Російська імперіальна історіографія"
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
