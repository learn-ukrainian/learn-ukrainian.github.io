# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: hist-052
level: HIST
sequence: 52
slug: bohdan-khmelnytskyi
version: '2.0'
title: 'Богдан Хмельницький: Постать в історії'
subtitle: 'Bohdan Khmelnytsky: A Figure in History'
focus: biography
pedagogy: CBI
phase: HIST.5 [Rise of Cossacks]
word_target: 5000
objectives:
- Учень може описати життєвий шлях Богдана Хмельницького
- Учень може проаналізувати роль особистості в історії
- Учень може оцінити внесок гетьмана у розбудову держави
sources:
- name: History of Ukraine-Rus
  url: http://litopys.org.ua/hrushrus/iur.htm
  type: reference
  notes: Classic historical account
- name: The Khmelnytsky Uprising
  url: https://encyclopediaofukraine.com
  type: secondary
  notes: Modern analysis
content_outline:
- section: 'Вступ: Батько нації чи суперечлива фігура?'
  points:
  - Khmelnytsky's place in Ukrainian historical memory — from 'Moses' in Cossack chronicles to 'traitor' in Shevchenko's early
    works
  - 'Different interpretations of his legacy — comparison to Oliver Cromwell (revolutionary dictator) and George Washington
    (founding father); cultural hook: [!context] — Хмельницький як ''український Кромвель'''
  words: 600
- section: 'Ранні роки: Освіта і служба'
  points:
  - 'Education at Lviv Jesuit College — rhetoric and knowledge of Latin; cultural hook: [!history-bite] — Хмельницький знав
    латину та цитував римських класиків'
  - Battle of Cecora and Turkish captivity — death of father Mykhailo, 2 years in Istanbul, learning Turkish and Tatar
  - Service as a registered Cossack — Smolensk War (1632-1634), golden saber for bravery, maritime campaigns
  words: 600
- section: Особиста драма як іскра повстання
  points:
  - The Subotiv conflict with Czaplinski — raid in 1647, loss of property, abduction of Motrona, beating of son
  - 'Failure of the Polish legal system — King Vladyslav IV''s advice ''You have a saber at your side''; cultural hook: [!myth-buster]
    — Міф про те, що повстання планувалося роками (це був спонтанний вибух через особисту кривду)'
  - Flight to the Sich — December 1647, election as Hetman in January 1648
  words: 600
- section: Геній дипломатії та війни
  points:
  - 'Alliance with the Crimean Khanate — Tuhay-Bey brotherhood, neutralizing Polish cavalry advantage; cultural hook: [!military]
    — Використання татарської кінноти як вирішального фактору'
  - Victories at Zhovti Vody, Korsun, Pyliavtsi — strategy of ambushes and psychological pressure ('pylyavchyky')
  - Entry into Kyiv — February 1649, triumphant reception as 'liberator of the Rus people'
  words: 600
- section: Будівничий держави
  points:
  - Creation of the Hetmanate's administrative system — division into regiments (polky) and hundreds (sotni) combining military
    and civil power
  - Social and economic reforms — de facto abolition of serfdom, 'Cossackization' of peasants, independent treasury
  - 'Chyhyryn as a diplomatic center — receiving ambassadors from Austria, Turkey, Moscow, Sweden; cultural hook: [!fact]
    — За Хмельницького Київ був духовним центром, а Чигирин — політичною столицею'
  words: 600
- section: 'Первинні джерела: Листи та промови'
  points:
  - Excerpts from letters to European monarchs — letter to Swedish King Charles X Gustav (1656) about honest alliances
  - 'Speech to the Polish commissioners — Kyiv (Feb 1649) to Adam Kysil: ''I am the sole autocrat of Rus...''; include quote:
    «Виб''ю з лядської неволі руський народ увесь!»'
  words: 600
- section: 'Деколонізаційний погляд: Лідер, а не васал'
  points:
  - 'Debunking the myth of ''reunification'' — Pereyaslav (1654) as a military alliance (ad hoc), not a merger; cultural hook:
    [!decolonization] — Спростування радянського терміну ''возз''єднання'''
  - Khmelnytsky as a sovereign ruler — independent foreign policy (Sweden/Transylvania 1656) despite Moscow's objections
  words: 600
- section: Читання
  points:
  - Intro to reading tasks
  words: 800
vocabulary_hints:
  required:
  - 'гетьман (Hetman) — leader of the Cossack state; collocations: обрати гетьмана, гетьманська булава'
  - державотворення (state-building) — process of creating state institutions
  - дипломатія (diplomacy) — skill in managing international relations
  - 'союз (alliance) — military or political agreement; collocations: укласти союз, військовий союз'
  - 'універсал (universal) — official decree of the Hetman; collocations: видати універсал'
  - полк (regiment) — administrative-territorial unit of the Hetmanate
  - сотня (company/hundred) — subdivision of a regiment
  - булава (mace) — symbol of Hetman's power
  - 'автономія (autonomy) — self-government rights; collocations: широка автономія'
  - суверенітет (sovereignty) — supreme authority of the state
  recommended:
  - шляхта (nobility) — privileged class in Poland-Lithuania
  - реєстрове козацтво (Registered Cossacks) — Cossacks in official military service
  - 'повстання (uprising) — armed resistance; collocations: національно-визвольне повстання'
  - протекторат (protectorate) — relationship of protection and partial control
activity_hints:
- type: reading
  focus: Analysis of Khmelnytsky's universals
- type: essay-response
  focus: Evaluation of his political decisions
- type: comparative-study
  focus: Khmelnytsky vs. Cromwell
- type: critical-analysis
  focus: 'Спростування міфів: Myths and facts'
  items: 4
persona:
  voice: Senior Professor of History
  role: Hetman
grammar:
- Biographical narrative structure
- Verbs of political action
register: публіцистичний
prerequisites:
- khmelnychchyna-prychyny
connects_to:
- bitva-pid-zhovtymy-vodamy

```

---

## PART 1: Deep Research

Research **Богдан Хмельницький: Постать в історії** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Богдан Хмельницький: Постать в історії

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — Phase D verifies prose against this -->
```yaml
subject: "Богдан Хмельницький: Постать в історії"
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
