# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: bio-090
level: BIO
sequence: 90
slug: oleksandr-arkhypenko
version: '2.0'
title: 'Олександр Архипенко: Скульптор авангарду'
focus: biography
phase: BIO
word_target: 5000
objectives:
- 'Analyze the life and legacy of олександр архипенко: скульптор авангарду'
- Evaluate the contributions of революціонер у скульптурі
- Trace the career and influence of спадщина та вплив
sources:
- name: Олександр Архипенко (Wikipedia UA)
  url: https://uk.wikipedia.org/wiki/Архипенко_Олександр_Порфирович
  type: primary
  notes: Біографія, творчий шлях, інновації
- name: Archipenko Foundation
  url: https://www.archipenko.org
  type: reference
  notes: Каталог творів та біографічні матеріали
- name: MoMA Collection
  url: https://www.moma.org/artists/229
  type: reference
  notes: Роботи в колекції Музею сучасного мистецтва
content_outline:
- section: Вступ — Революціонер у скульптурі
  points:
  - Архипенко як один із найвидатніших скульпторів XX століття
  - Новаторство у тривимірному мистецтві
  - Українське коріння та світова слава
  words: 850
- section: Київські роки (1887-1908)
  points:
  - Народження в родині інженера
  - Навчання в Київській художній школі
  - Вплив української народної творчості
  - Рішення продовжити освіту в Європі
  words: 850
- section: Паризький період (1908-1921)
  points:
  - Прибуття до Парижа та інтеграція в авангард
  - Знайомство з Пікассо, Браком, Модільяні
  - Розвиток кубістичної скульптури
  - Винахід «скульптоживопису» та порожнечі як форми
  words: 850
- section: Берлінський період (1921-1923)
  points:
  - Переїзд до Берліна
  - Викладання та відкриття власної школи
  - Виставки та визнання в Німеччині
  - Вплив німецького експресіонізму
  words: 850
- section: Американський період (1923-1964)
  points:
  - Еміграція до США
  - Викладання в провідних університетах
  - Експерименти з новими матеріалами
  - Створення «Архипеньо» — світлових скульптур
  words: 850
- section: Спадщина та вплив
  points:
  - Роль у розвитку абстрактної скульптури
  - Теоретичні праці про мистецтво
  - Вплив на подальші покоління скульпторів
  - Повернення імені в Україну
  words: 750
vocabulary_hints:
  required:
  - скульптура (sculpture)
  - авангард (avant-garde)
  - кубізм (cubism)
  - порожнеча (void/negative space)
  - тривимірний (three-dimensional)
  - форма (form)
  - простір (space)
  - абстракція (abstraction)
  - новаторство (innovation)
  - скульптоживопис (sculpto-painting)
  recommended:
  - експресіонізм (expressionism)
  - пластика (plastic arts)
  - матеріал (material)
  - композиція (composition)
  - виставка (exhibition)
activity_hints:
- type: reading
  focus: Мистецька біографія
  source: Уривки з теоретичних праць та каталогів
  items: 3 passages
- type: essay-response
  focus: Як порожнеча може бути елементом скульптури?
  output: Мистецтвознавче есе
connects_to:
- bio-50 (Олександр Богомазов)
- bio-57 (Лесь Курбас)
- bio-66 (Катерина Білокур)
prerequisites:
- bio-45 (Казимир Малевич)
persona:
  voice: Senior Biographer
  role: Cubist Sculptor
module_type: biography
immersion: 100% Ukrainian

```

---

## PART 1: Deep Research

Research **Олександр Архипенко: Скульптор авангарду** for the **bio** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Олександр Архипенко: Скульптор авангарду

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — Phase D verifies prose against this -->
```yaml
subject: "Олександр Архипенко: Скульптор авангарду"
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
