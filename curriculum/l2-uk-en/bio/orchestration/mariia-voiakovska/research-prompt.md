# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: bio-068
level: BIO
sequence: 68
slug: mariia-voiakovska
version: '2.0'
title: 'Марія Вояковська: Революціонерка'
focus: biography
phase: BIO
word_target: 5000
objectives:
- 'Analyze the life and legacy of марія вояковська: революціонерка'
- Evaluate the contributions of у тіні великого чоловіка
- Trace the career and influence of останні роки та пам'ять
sources:
- name: Марія Вояківська (Wikipedia UA)
  url: https://uk.wikipedia.org/wiki/Марія_Вояківська
  type: primary
  notes: Біографія, громадська діяльність, шлюб з Грушевським
- name: Михайло Грушевський
  url: https://uk.wikipedia.org/wiki/Михайло_Грушевський
  type: reference
  notes: Чоловік — перший президент УНР
- name: Жіночий рух в Україні
  url: https://uk.wikipedia.org/wiki/Жіночий_рух_в_Україні
  type: reference
  notes: Контекст фемінізму кінця XIX — початку XX ст.
content_outline:
- section: Вступ — У тіні великого чоловіка
  points:
  - Марія Вояковська — дружина Михайла Грушевського
  - Власний внесок у жіночий рух та освіту
  - Життя як партнерство рівних інтелектуалів
  words: 850
- section: Ранні роки та освіта (1868-1895)
  points:
  - Народження у Відні в родині галицьких емігрантів
  - Освіта в австрійських гімназіях
  - Формування феміністичних поглядів
  - Участь у жіночих організаціях Львова
  words: 850
- section: Шлюб та партнерство (1896-1917)
  points:
  - Знайомство з Михайлом Грушевським у Львові
  - Шлюб у 1896 році
  - Роль у Науковому товаристві імені Шевченка
  - Перекладацька та редакторська діяльність
  words: 850
- section: Київ та Українська революція (1917-1924)
  points:
  - Переїзд до Києва разом із чоловіком
  - Підтримка Української Центральної Ради
  - Еміграція до Відня та Праги
  - Повернення до Радянської України
  words: 850
- section: Радянські роки та репресії (1924-1948)
  points:
  - Життя під наглядом НКВС
  - Смерть Михайла Грушевського у 1934 році
  - Арешт та заслання доньки Катерини
  - Виживання у важкі часи
  words: 850
- section: Останні роки та пам'ять
  points:
  - Смерть у 1948 році
  - Тривале забуття в радянські часи
  - Повернення імені в незалежній Україні
  - Марія Вояковська як приклад жінки-інтелектуалки
  words: 750
vocabulary_hints:
  required:
  - феміністка (feminist)
  - освітянка (educator)
  - перекладач (translator)
  - партнерство (partnership)
  - емансипація (emancipation)
  - інтелігенція (intelligentsia)
  - революція (revolution)
  - еміграція (emigration)
  - репресії (repressions)
  - спадщина (legacy)
  recommended:
  - рівноправність (equality)
  - суфражизм (suffragism)
  - салон (salon)
  - меценатство (patronage)
  - заслання (exile)
activity_hints:
- type: reading
  focus: Листування та спогади сучасників
  source: Архівні матеріали
  items: 3 passages
- type: essay-response
  focus: Яка роль дружин видатних діячів у історії?
  output: Reflective essay
connects_to:
- bio-25-nataliya-kobrynska
- bio-24-olena-pchilka
prerequisites:
- bio-35-mykhailo-hrushevskyi-biography
persona:
  voice: Senior Biographer
  role: Schoolteacher
module_type: biography
immersion: 100% Ukrainian

```

---

## PART 1: Deep Research

Research **Марія Вояковська: Революціонерка** for the **bio** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Марія Вояковська: Революціонерка

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — Phase D verifies prose against this -->
```yaml
subject: "Марія Вояковська: Революціонерка"
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
