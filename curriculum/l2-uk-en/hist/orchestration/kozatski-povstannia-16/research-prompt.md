# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: hist-044
level: HIST
sequence: 44
slug: kozatski-povstannia-16
version: '2.0'
title: Козацькі повстання XVI століття
subtitle: The First Great Clashes for Rights and Freedoms
focus: history
pedagogy: CBI
phase: HIST.5 [Rise of Cossacks]
word_target: 5000
objectives:
- Learner can identify the causes and consequences of the Kosynskyi and Nalyvaiko uprisings
- Learner can analyze the social and religious motivations behind the first cossack wars
- Learner can understand the significance of these uprisings for the formation of national identity
content_outline:
- section: Вступ
  points:
  - 'The accumulation of social tension in the late 16th century — context of the ''Great Border'' (Великий Кордон) where
    cossacks were the only defense against Tatars; cultural hook: [!context]'
  - The conflict between 'registrove' and 'neregistrove' cossackdom — impact of the 1590 Seim Constitution 'Order regarding
    Nizovtsi' (Порядок щодо низовців)
  words: 700
- section: Повстання Криштофа Косинського (1591–1593)
  points:
  - 'Causes: Private conflict vs. social grievance — dispute over Rokytne estate with Janusz Ostrozkyi escalating into social
    explosion; engagement hook: [!history-bite]'
  - 'Course of events: Battle of Piatka — decisive role of Ostrozkyi''s artillery and the capture of Bila Tserkva (symbolic
    destruction of debt documents)'
  - Consequences and the role of the Ostrozkyi princes — suppression of the first attempt at independent political force;
    Kosynskyi's death in Cherkasy
  words: 700
- section: Повстання Северина Наливайка (1594–1596)
  points:
  - 'Scale and geography: From Podillia to Belarus — capture of Bratslav and proclamation of a ''free cossack city'''
  - The union of registered and non-registered cossacks — alliance with Hryhorii Loboda (registered) and Matvii Shaula (Zaporozhians)
  - The tragic finale at Solonytsia — the betrayal by registered cossacks and Zholkevskyi's broken promise of amnesty
  - 'Political program of Nalyvaiko — the idea of a separate ''Appanage Principality'' (Удільне князівство) between Dnister
    and Dnipro; engagement hook: [!myth-buster]'
  words: 700
- section: Читання
  points:
  - Analysis of the 'Seim Constitutions' regarding cossacks — 1593 'punishment without trial' and 1596 declaration of cossacks
    as 'hostes patriae' (enemies of the fatherland)
  - Accounts of Stanislav Zholkevskyi — justification of cruelty as 'state necessity' against 'swawolnicy' (unruly ones)
  words: 700
- section: Соціальний та Релігійний Вимір боротьби
  points:
  - 'The struggle for rights and ''volnosti'' — demand for noble status (shliakhta rights: court, land ownership, tax exemption)'
  - 'The religious factor: Defense of Orthodoxy — context of the Union of Brest (1596) turning cossacks into the ''Sword of
    Orthodoxy''; engagement hook: [!culture]'
  words: 700
- section: Первинні джерела та свідчення очевидців
  points:
  - Excerpts from the accounts of contemporaries (Bielski, Heidenstein) — Bielski's description of the Battle of Piatka; mention
    of Erich Lassota's visit
  - 'Letter of Nalyvaiko to the King — diplomatic rhetoric offering service in exchange for autonomy; engagement hook: [!quote]'
  words: 700
- section: Деколонізаційний погляд на історію повстань
  points:
  - 'Reconceptualizing ''rebellion'' as ''liberation war'' — reframing ''bunt chłopstwa'' (peasant riot) as a state-building
    effort by a new political elite; engagement hook: [!decolonization]'
  - The myth of 'peasant riots' vs. professional military struggle — evidence of organized artillery, intelligence, and diplomacy
  words: 800
vocabulary_hints:
  required:
  - повстання (uprising) — козацьке повстання, придушення повстання
  - реєстр (registry) — реєстрове козацтво, викреслити з реєстру
  - шляхта (nobility) — права шляхти, конфлікт зі шляхтою
  - унія (union) — Берестейська унія, релігійна унія
  - свавілля (arbitrariness/unruliness) — польський термін 'swawola', козацьке свавілля
  - облога (siege) — облога табору, тривала облога
  - зрада (betrayal/treason) — зрада старшини, звинувачення у зраді
  - угода (agreement) — порушення угоди, підписання угоди
  recommended:
  - артилерія (artillery) — використання артилерії
  - автономія (autonomy) — вимога автономії
  - амністія (amnesty) — обіцянка амністії
  - вимоги (demands) — політичні вимоги
activity_hints:
- type: reading
  focus: Contemporary accounts of the Solonytsia massacre
- type: essay-response
  focus: The evolution of cossack demands from private grievances to national rights
- type: comparative-study
  focus: 'Kosynskyi vs Nalyvaiko: Leadership styles and goals'
- type: critical-analysis
  focus: Analyzing the reasons for the failure of early uprisings
persona:
  voice: Senior Professor of History
  role: Kyiv-Mohyla Academy Historian
grammar:
- 'Historical narrative: complex sentences with causal links'
- Conditionals in historical analysis (якби... то...)
register: публіцистичний
prerequisites:
- dmytro-vyshnevetskyi
connects_to:
- petro-sahaidachnyi

```

---

## PART 1: Deep Research

Research **Козацькі повстання XVI століття** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Козацькі повстання XVI століття

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — Phase D verifies prose against this -->
```yaml
subject: "Козацькі повстання XVI століття"
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
