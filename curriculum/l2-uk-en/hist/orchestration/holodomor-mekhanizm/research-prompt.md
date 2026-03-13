# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-101
level: HIST
sequence: 101
slug: holodomor-mekhanizm
version: '2.0'
title: 'Голодомор I: Механізм'
subtitle: 'Holodomor I: Mechanism'
focus: history
pedagogy: seminar
phase: HIST.10
word_target: 5000
objectives:
- Learner understands the legal and economic mechanisms of Holodomor
- Learner can analyze official vs. survivor discourse
- Learner can apply decolonial lens to Soviet history
sources:
- name: Національний музей Голодомору-геноциду
  url: https://holodomormuseum.org.ua/
  type: reference
- name: 'Енциклопедія історії України: Голодомор'
  url: http://resource.history.org.ua/cgi-bin/eiu/history.exe
  type: secondary
- name: Джеймс Мейс. Повість про двох журналістів
  url: https://day.kyiv.ua/
  type: secondary
- name: 'Енн Епплбом. Червоний голод: Війна Сталіна проти України'
  url: https://www.anneapplebaum.com/
  type: secondary
- name: 'Тімоті Снайдер. Криваві землі: Європа між Гітлером і Сталіним'
  url: https://timothysnyder.org/
  type: secondary
content_outline:
- section: Вступ
  points:
  - Context of 1930s — Stalin's modernization of the empire at the expense of the village; Ukraine seen as both breadbasket
    and existential threat (national movement)
  - 'Social engineering — Transforming independent owners into dependent state workers (kolkhozniks); Stalin''s letter (11.08.1932)
    on ''losing Ukraine'' — quote: «Якщо не візьмемося нині за виправлення становища в Україні, Україну можемо втратити»'
  words: 600
- section: Читання
  points:
  - CBI approach — Analysis of how dehumanizing language prepared the ground for mass murder; if the enemy is a 'class element',
    destruction is justified
  - 'Language of violence — Official terms: ''elements'', ''saboteurs'', ''petliurites'' («петлюрівські недобитки»), ''idlers''
    («лежні»); cultural hook: ''kurkul'' as a political label, not economic status [!context]'
  words: 600
- section: Колективізація та опір селянства
  points:
  - Traditional village storm — The village as the center of Ukrainian identity, incompatible with Soviet unification and
    totalitarian control
  - Peasant resistance — 'Babski bunty' (women's revolts) and over 4000 mass uprisings in 1930 involving 1.2 million peasants
    [!myth-buster] — forced regime into tactical retreat ('Dizziness from Success', March 1930)
  - Dekulakization — Systematic destruction of the village elite (best farmers) to break resistance; 'rozcurkulennia' as economic
    and physical liquidation
  words: 600
- section: Закон про п'ять колосків та Чорні дошки
  points:
  - 'Law of Five Ears — Decree of 07.08.1932: death penalty for ''theft'' of collective property (even a handful of grain);
    ''socialist property'' declared «священна і недоторканна» (sacred and inviolable) [!history-bite]'
  - Black Boards mechanism — Specific repression against resistant villages (e.g., Liutenka, Kamiani Potoky, Pisky); total
    blockade, removal of ALL food and goods, ban on trade — introduced Nov-Dec 1932
  words: 600
- section: Терор голодом як інструмент упокорення
  points:
  - Red broom — 'Buksyrni bryhady' (towing brigades) using probes to search houses for hidden food; confiscation of meat,
    potatoes, and beans as 'natural fines' (натуральні штрафи)
  - Blockade of borders — Directive of Jan 22, 1933 banning exit from UkrSSR and Kuban; troops guarding borders to create
    a ghetto [!decolonization]
  words: 600
- section: Первинні джерела
  points:
  - Survivor testimonies — Diaries of Nestor Bilous ('«Люди мруть з голоду…»') and Oleksandra Radchenko ('...horror of swollen
    children') [!quote]
  - Secret circulars — Stalin's correspondence revealing intent; proof that famine was not a harvest failure but a punitive
    operation
  words: 600
- section: Деколонізаційний погляд
  points:
  - Imperial crime — Moscow used Ukrainian resources for industrialization while destroying the carriers of Ukrainian identity;
    comparison to other colonial resource extractions [!analysis]
  - Russification — Organized resettlement of Russians (echelons in 1933) into emptied Ukrainian villages in Donbas and South;
    changing ethnic composition
  words: 600
- section: Спадщина
  points:
  - Transgenerational trauma — Fear of hunger, habit of hoarding food, deep distrust of authority, 'do not stick out' («не
    висовуйся») mentality
  - Memory as force — Recognition of Holodomor as genocide restores Ukrainian agency; 'Candle in the Window' tradition as
    a symbol of resilience
  words: 800
vocabulary_hints:
  required:
  - 'окупація (occupation) — collocations: радянська окупація, режим окупації'
  - 'геноцид (genocide) — usage: визнання Голодомору геноцидом; crime against humanity'
  - 'розкуркулення (dekulakization) — context: знищення господара, репресивний захід'
  - 'колективізація (collectivization) — collocations: примусова колективізація, суцільна колективізація; ''Dizziness from
    Success'' article'
  - 'чорна дошка (black board) — context: режим чорних дощок, занесення на чорну дошку (death sentence for a village)'
  recommended:
  - саботаж (sabotage) — Soviet propaganda term for resistance
  - 'тоталітаризм (totalitarianism) — context: сталінський тоталітаризм, контроль над особою'
  - хлібозаготівля (grain procurement) — official term covering the confiscation of grain; unrealistic plans
  - продрозкладка (prodrazverstka/food apportionment) — historical antecedent to 1930s policies
  - 'куркуль (kulak/fist) — political label for independent farmers; learner error: confused with ''rich person'''
  - Закон про п'ять колосків (Law of Five Ears) — decree of 7.08.1932, death penalty for food
  - натуральні штрафи (fines in kind) — confiscation of meat/potatoes when grain was missing
  - червона мітла (red broom) — search brigades using probes to find food
activity_hints:
- type: reading
  focus: Historical documents
- type: critical-analysis
  focus: Propaganda vs Evidence
- type: essay-response
  focus: Genocide mechanism
persona:
  voice: Senior Professor of History
  role: Village Elder
grammar:
- Historical narrative register
- Passive voice (-no, -to) in documentation
- Hypothetical structures in trauma narratives
prerequisites:
- oun
connects_to:
- holodomor-pamiat

```

---

## PART 1: Deep Research

Research **Голодомор I: Механізм** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Голодомор I: Механізм

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Голодомор I: Механізм"
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
