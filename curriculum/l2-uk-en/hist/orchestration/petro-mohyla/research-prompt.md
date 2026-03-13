# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: hist-035
level: HIST
sequence: 35
slug: petro-mohyla
version: '2.0'
title: 'Петро Могила: Реформатор церкви'
subtitle: 'Petro Mohyla: The Church Reformer'
focus: history
pedagogy: CBI
phase: HIST.4 [Lithuanian-Polish Era]
word_target: 5000
objectives:
- Understand the significance of Petro Mohyla's educational reforms
- Analyze the impact of the Kyiv-Mohyla Academy on Ukrainian culture
- Discuss the 'Mohylian Era' in Ukrainian history
- Use religious and educational terminology of the 17th century
sources:
- name: Історія України-Руси
  url: http://litopys.org.ua/hrushrus/iur.htm
  type: secondary
- name: Petro Mohyla (Encyclopedia of Ukraine)
  url: http://www.encyclopediaofukraine.com/display.asp?linkpath=pages%5CM%5CO%5CMohylaPetro.htm
  type: reference
content_outline:
- section: Вступ
  points:
  - Crisis of Orthodoxy post-Union — 1596 Union aftermath, hierarchy unrecognized, churches seized
  - 'Need for new strategy — beyond survival: modernization and intellectual defense'
  words: 550
- section: Шлях до митри
  points:
  - Moldovan origins — son of hospodar Simeon Mohyla
  - Western education — Lviv Brotherhood School, Zamość Academy, possibly Paris (Sorbonne)
  - 'Military service — 1620-1621 Cecora and Khotyn battles; [!history-bite]: Mohyla was a soldier before becoming a monk,
    bringing military discipline to the church'
  - Tonsure at Lavra — 1627 elected archimandrite, start of publishing activity
  words: 550
- section: Заснування Академії
  points:
  - Merger of schools (1632) — Lavra School (1631) + Brotherhood School = Kyiv-Mohyla Collegium
  - Latin curriculum for Orthodox defense — adopting Jesuit methods (language, rhetoric) to defeat the enemy with their own
    weapons
  - Resistance from traditionalists — conservative Cossacks and clergy feared 'Latinization'
  - 'Role of ''spudei'' (students) — forming a new national elite; [!myth-buster]: Myth: Mohyla ''Catholicized'' education.
    Reality: He used Latin tools for Orthodox defense.'
  words: 550
- section: Реформатор церкви
  points:
  - Legalization of hierarchy (1632/1633) — 'Articles of Pacification' from King Władysław IV; consecration in Lviv
  - 'Rebuilding St. Sophia and Desyatynna — 1633 restoration of Sophia (Octaviano Mancini), 1635 excavations of Desyatynna;
    [!context]: Parallel with Counter-Reformation — education + discipline + dogma'
  - Liturgical reforms (Trebnyk) — 1646 'Euchologion', unification of rites, pastor's manual
  - Discipline and education of clergy — strict requirements for priests to be educated
  words: 550
- section: Спадщина Могили
  points:
  - Kyiv as the 'New Jerusalem' — theological concept of Kyiv as a sacred center
  - 'Baroque culture — [!culture]: ''Mohylian'' or ''Cossack'' Baroque style blending European splendor with local tradition'
  - Lasting impact on Ukrainian identity — integration into European cultural space
  words: 550
- section: Читання
  points:
  - Primary sources assignment — excerpts from 'Trebnyk' Preface or 'Testament'
  words: 550
- section: Первинні джерела
  points:
  - Testament of Mohyla — moral and educational instructions
  - Inscription on Desyatynna — finding Rus' roots for legitimacy
  - 'Linguistic analysis — [!quote]: ''Гарно й почесно бути свічкою... але свічка має світити'' (Trebnyk, 1646) — metaphor
    of active service'
  words: 550
- section: Деколонізаційний погляд
  points:
  - 'Myth of Latinization — [!decolonization]: Imperial historiography portrayed pre-Moscow Orthodoxy as ''corrupted''; reality:
    peak intellectual sovereignty'
  - Intellectual sovereignty — Kyiv exported scholars to Moscow, not vice versa
  - Summary of achievements — standardized dogma ('Confession of Faith', 1640), recognized by all patriarchs
  - Reflection on 'Western tools for Eastern faith' — agency in self-reform without waiting for Moscow or Constantinople
  words: 550
- section: Потрібно більше практики?
  points:
  - Engagement — reflective questions on Mohyla's strategy
  words: 600
vocabulary_hints:
  required:
  - митрополит (Metropolitan) — титул глави церкви
  - академія (Academy) — Києво-Могилянська академія
  - реформа (reform) — церковна реформа, освітня реформа
  - колегіум (collegium) — за зразком єзуїтських колегіумів
  - полеміка (polemics) — релігійна полеміка
  - православ'я (Orthodoxy) — захист православ'я
  - унія (Union) — Берестейська унія 1596
  - руїна (ruin) — відбудова з руїн (rebuilding from ruins)
  - канонізація (canonization) — Петро Могила канонізований у 1996
  - друкарня (printing press) — Лаврська друкарня
  recommended:
  - спудей (student) — студент академії (archaic)
  - риторика (rhetoric) — мистецтво красномовства
  - латина (Latin) — мова науки
  - бароко (Baroque) — українське бароко, козацьке бароко
  - меценат (patron) — меценат освіти і культури
activity_hints:
- type: critical-analysis
  focus: 'Верифікація фактів: facts'
  items: 4
persona:
  voice: Senior Professor of History
  role: Academy Professor
grammar:
- Latinisms in Ukrainian language
- Rhetorical style of Baroque
- Passive voice in historical narrative
prerequisites:
- pravoslavna-tserkva-17
connects_to:
- bratstva-i-osvita

```

---

## PART 1: Deep Research

Research **Петро Могила: Реформатор церкви** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Петро Могила: Реформатор церкви

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — Phase D verifies prose against this -->
```yaml
subject: "Петро Могила: Реформатор церкви"
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
