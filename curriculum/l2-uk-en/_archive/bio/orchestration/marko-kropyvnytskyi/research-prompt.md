# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: bio-045
level: BIO
sequence: 45
slug: marko-kropyvnytskyi
version: '2.0'
title: 'Марко Кропивницький: Корифей театру'
focus: biography
phase: BIO
word_target: 5000
objectives:
- 'Analyze the life and legacy of марко кропивницький: корифей театру'
- Evaluate the contributions of батько українського театру
- Trace the career and influence of останні роки та спадщина (1900-1910)
sources:
- name: Марко Кропивницький (Wikipedia UA)
  url: https://uk.wikipedia.org/wiki/Марко_Кропивницький
  type: primary
  notes: Біографія, театральна та літературна діяльність
- name: Театр корифеїв
  url: https://uk.wikipedia.org/wiki/Театр_корифеїв
  type: reference
  notes: Український театр XIX століття
- name: Українська драматургія XIX століття
  url: https://uk.wikipedia.org/wiki/Українська_драматургія
  type: reference
  notes: Контекст розвитку театру
content_outline:
- section: Вступ — Батько українського театру
  points:
  - Марко Кропивницький — засновник професійного українського театру
  - Актор, режисер, драматург і композитор в одній особі
  - Творець національної театральної школи
  words: 850
- section: Ранні роки та освіта (1840-1865)
  points:
  - Народження в селі Бережувата на Херсонщині
  - Навчання в Єлисаветградській гімназії
  - Перші театральні враження та аматорські вистави
  - Формування національної свідомості
  words: 850
- section: Початок театральної кар'єри (1865-1882)
  points:
  - Організація аматорських труп
  - Перші драматичні твори
  - Знайомство з Михайлом Старицьким
  - Боротьба з цензурою Емського указу
  words: 850
- section: Створення професійного театру (1882-1900)
  points:
  - Заснування першої професійної української трупи (1882)
  - Постановка «Наталки Полтавки» та «Назара Стодолі»
  - Виховання акторів — Заньковецька, Садовський, Саксаганський
  - Гастролі імперією та успіх у глядачів
  words: 850
- section: Драматургія та музика
  points:
  - П'єси «Дай серцю волю, заведе в неволю», «Глитай, або ж Павук»
  - Оперети та музичні комедії
  - Народні пісні та хорові обробки
  - Етнографічний реалізм як метод
  words: 850
- section: Останні роки та спадщина (1900-1910)
  points:
  - Продовження театральної діяльності до останніх днів
  - Смерть у 1910 році
  - Вплив на розвиток українського театру XX століття
  - Кропивницький як символ національного відродження
  words: 750
vocabulary_hints:
  required:
  - корифей (coryphaeus, leading figure)
  - трупа (theater company)
  - драматург (playwright)
  - режисер (director)
  - актор (actor)
  - вистава (performance)
  - репертуар (repertoire)
  - цензура (censorship)
  - етнографізм (ethnographism)
  - антреприза (theatrical enterprise)
  recommended:
  - оперета (operetta)
  - декорація (stage design)
  - гастролі (tour)
  - бенефіс (benefit performance)
  - амплуа (character type)
activity_hints:
- type: reading
  focus: Уривки з п'єс та спогади сучасників
  source: Оригінальні твори та мемуари
  items: 3 passages
- type: essay-response
  focus: Чому Кропивницького називають батьком українського театру?
  output: Historical analysis
connects_to:
- bio-26-mariya-zankovetska
- bio-57-les-kurbas
prerequisites:
- bio-46-ivan-kotliarevskyi
persona:
  voice: Senior Biographer
  role: Troupe Manager
module_type: biography
immersion: 100% Ukrainian

```

---

## PART 1: Deep Research

Research **Марко Кропивницький: Корифей театру** for the **bio** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Марко Кропивницький: Корифей театру

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — Phase D verifies prose against this -->
```yaml
subject: "Марко Кропивницький: Корифей театру"
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
