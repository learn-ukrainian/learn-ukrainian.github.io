# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: bio-107
level: BIO
sequence: 107
slug: berta-rapoport
version: '2.0'
title: 'Берта Рапопорт: Лікарка і громадська діячка'
focus: biography
phase: BIO
word_target: 5000
objectives:
- 'Analyze the life and legacy of берта рапопорт: лікарка і громадська діячка'
- Evaluate the contributions of жінка, що лікувала і надихала
- Trace the career and influence of повернення з небуття
sources:
- name: Берта Рапопорт (Wikipedia UA)
  url: https://uk.wikipedia.org/wiki/Рапопорт_Берта_Ісаківна
  type: primary
  notes: Biography of the pioneering woman doctor and activist
- name: Одеська медична спадщина
  url: https://omu.odessa.ua/
  type: reference
  notes: Historical medical archives of Odesa
content_outline:
- section: Вступ — Жінка, що лікувала і надихала
  points:
  - Одна з перших жінок-лікарів в Україні
  - Громадська діячка та феміністка
  - Боротьба за права жінок у медицині
  words: 850
- section: Походження та освіта (1860-ті–1880-ті)
  points:
  - Єврейська родина в Одесі
  - Прагнення до освіти попри перешкоди
  - Навчання за кордоном (Швейцарія)
  - Здобуття медичного диплома
  words: 850
- section: Медична практика (1880-ті–1900-ті)
  points:
  - Повернення до Одеси
  - Робота в лікарнях та приватна практика
  - Спеціалізація в гінекології
  - Допомога бідним верствам населення
  words: 850
- section: Громадська діяльність (1890-ті–1910-ті)
  points:
  - Участь у жіночому русі
  - Боротьба за доступ жінок до освіти
  - Благодійність та соціальна робота
  - Публіцистична діяльність
  words: 850
- section: Революційні роки (1917-1920-ті)
  points:
  - Продовження роботи під час хаосу
  - Ставлення до революційних змін
  - Останні роки життя
  - Смерть та забуття в радянський час
  words: 850
- section: Спадщина — Повернення з небуття
  points:
  - Дослідження істориків
  - Внесок у розвиток жіночої медицини
  - Роль у феміністичному русі
  - Приклад для сучасних жінок-лікарів
  words: 750
vocabulary_hints:
  required:
  - лікарка (woman doctor)
  - медична освіта (medical education)
  - гінекологія (gynecology)
  - феміністка (feminist)
  - громадська діячка (public activist)
  - благодійність (charity)
  - жіночий рух (women's movement)
  - дискримінація (discrimination)
  - емансипація (emancipation)
  - соціальна робота (social work)
  recommended:
  - акушерство (obstetrics)
  - приватна практика (private practice)
  - медична етика (medical ethics)
  - просвітництво (enlightenment)
  - рівноправність (equal rights)
activity_hints:
- type: reading
  focus: Жінки в медицині XIX-XX ст.
  source: Historical medical sources
  items: 3 passages
- type: essay-response
  focus: Які перешкоди долали перші жінки-лікарі?
  output: Analytical essay
connects_to:
- bio-33
- bio-61
prerequisites:
- bio-59
persona:
  voice: Senior Biographer
  role: Chief Physician
module_type: biography
immersion: 100% Ukrainian

```

---

## PART 1: Deep Research

Research **Берта Рапопорт: Лікарка і громадська діячка** for the **bio** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Берта Рапопорт: Лікарка і громадська діячка

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — Phase D verifies prose against this -->
```yaml
subject: "Берта Рапопорт: Лікарка і громадська діячка"
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
