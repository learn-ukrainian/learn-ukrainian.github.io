# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: bio-157
level: BIO
sequence: 157
slug: oksana-zabuzhko
version: '2.0'
title: 'Оксана Забужко: Інтелектуал і феміністка'
focus: biography
phase: BIO
word_target: 5000
objectives:
- 'Analyze the life and legacy of оксана забужко: інтелектуал і феміністка'
- Evaluate the contributions of голос українського інтелектуалізму
- Trace the career and influence of громадська позиція та сучасність
sources:
- name: Оксана Забужко (Wikipedia UA)
  url: https://uk.wikipedia.org/wiki/Забужко_Оксана_Стефанівна
  type: primary
  notes: Біографія, літературна діяльність, філософія
- name: Офіційний сайт Оксани Забужко
  url: https://zabuzhko.com
  type: reference
  notes: Бібліографія та есеїстика
- name: PEN Ukraine
  url: https://pen.org.ua
  type: reference
  notes: Громадська позиція та правозахисна діяльність
content_outline:
- section: Вступ — Голос українського інтелектуалізму
  points:
  - Забужко як найвпливовіша українська письменниця сучасності
  - Поєднання літератури, філософії та публіцистики
  - Роль у формуванні постколоніального дискурсу
  words: 850
- section: Ранні роки та формування (1960-1987)
  points:
  - Народження в Луцьку в родині інтелігентів
  - Батько — дисидент та дослідник Лесі Українки
  - Навчання філософії в Київському університеті
  - Перші поетичні збірки
  words: 850
- section: «Польові дослідження з українського сексу» (1996)
  points:
  - Революційність роману для української літератури
  - Тема травми та постколоніальної ідентичності
  - Фемінізм та сексуальність у літературі
  - Міжнародний успіх та переклади
  words: 850
- section: «Музей покинутих секретів» (2009)
  points:
  - Епічний роман про українську історію XX століття
  - Тема УПА та замовчуваної пам'яті
  - Складна наративна структура
  - Літературна премія Анджелуса
  words: 850
- section: Філософія та есеїстика
  points:
  - Дисертація про естетику Шевченка
  - Есеї про українську ідентичність
  - «Notre Dame d'Ukraine» — дослідження Лесі Українки
  - Публічний інтелектуал та коментатор
  words: 850
- section: Громадська позиція та сучасність
  points:
  - Роль під час Революції гідності
  - Коментування російсько-української війни
  - Виступи на міжнародних форумах
  - Вплив на сучасну українську культуру
  words: 750
vocabulary_hints:
  required:
  - постколоніалізм (postcolonialism)
  - фемінізм (feminism)
  - інтелектуал (intellectual)
  - есеїстика (essay writing)
  - наратив (narrative)
  - ідентичність (identity)
  - травма (trauma)
  - дискурс (discourse)
  - деколонізація (decolonization)
  - публіцистика (opinion journalism)
  recommended:
  - сексуальність (sexuality)
  - пам'ять (memory)
  - УПА (UPA)
  - естетика (aesthetics)
  - міжнародне визнання (international recognition)
activity_hints:
- type: reading
  focus: Літературна творчість
  source: Уривки з романів та есеїв
  items: 3 passages
- type: essay-response
  focus: Як література допомагає опрацювати колективну травму?
  output: Аналітичне есе
connects_to:
- bio-84 (Галина Пагутяк)
- bio-85 (Марія Матіос)
- bio-94 (Софія Андрухович)
prerequisites:
- bio-40 (Леся Українка)
- bio-74 (Ліна Костенко)
persona:
  voice: Senior Biographer
  role: Public Intellectual
module_type: biography
immersion: 100% Ukrainian

```

---

## PART 1: Deep Research

Research **Оксана Забужко: Інтелектуал і феміністка** for the **bio** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Оксана Забужко: Інтелектуал і феміністка

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Оксана Забужко: Інтелектуал і феміністка"
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
