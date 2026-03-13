# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-053
level: HIST
sequence: 53
slug: bitva-pid-zhovtymy-vodamy
version: '2.0'
title: Битва під Жовтими Водами
subtitle: The Battle of Zhovti Vody
focus: history
pedagogy: CBI
phase: HIST.6 [Khmelnytsky & Cossack State]
word_target: 5000
objectives:
- Учень може описати стратегію Хмельницького у битві під Жовтими Водами
- Учень може пояснити роль реєстрових козаків у перемозі
- Учень може проаналізувати значення цієї битви для подальшого ходу повстання
sources:
- name: History of Ukraine-Rus
  url: http://litopys.org.ua/hrushrus/iur.htm
  type: reference
  notes: Detailed reconstruction of the battle
- name: Military Art of Ukraine
  url: https://history.org.ua
  type: secondary
  notes: Tactical analysis
content_outline:
- section: 'Вступ: Перший грім'
  points:
  - The strategic situation in spring 1648 — 21 April 1648 departure; tension in the steppe
  - Potocki's plan to split forces — Mykola Potocki's fatal underestimation of 'Khmel'; sending son Stefan ahead while main
    forces lagged
  words: 550
- section: 'Сили сторін: Давид проти Голіафа?'
  points:
  - Structure of the Polish vanguard (Stefan Potocki) — 2500 registered Cossacks, 1500 soldiers; mix of elite hussars and
    dragoons
  - Cossack-Tatar coalition forces — 4000 cavalry of Tugay Bey providing crucial mobility and blockade capability
  - Armament and morale comparison — Polish artillery advantage vs Cossack 'shanets' (earthworks) tactics; [!myth-buster]
    professional armies colliding, not a 'mob of peasants'
  words: 550
- section: 'Початок битви: Блокада табору'
  points:
  - Establishing the camp at Zhovti Vody — 29 April 1648; Stefan Potocki digs in at the tract
  - First skirmishes and tactical stalemate — Failed first assault leads to positional warfare (29 April - 2 May)
  - The role of Tugay Bey's cavalry — Cutting off water and supply lines; psychological pressure of 'The Horde is here'
  words: 550
- section: 'Переломний момент: Бунт на Дніпрі'
  points:
  - The register Cossacks' journey down the Dnieper — Flotilla movement intended to reinforce Potocki turned into a trap
  - The uprising at Kamianyi Zaton — 3-4 May; execution of loyalist colonels (Barabash, Karaimovych) who refused to join
  - Killing of Barabash and joining Khmelnytsky — [!history-bite] Destruction of Polish symbols (kleinods) before swearing
    allegiance; doubling Khmelnytsky's forces
  words: 550
- section: 'Розгром: Княжі Байраки'
  points:
  - The failed attempt to break out — 14 May negotiations fail over surrender of artillery; 16 May night 'hollow camp' retreat
    attempt
  - Total destruction of the Polish vanguard — [!context] Kniazhi Bairaky terrain trap (ravines/forest) prevented hussar deployment;
    16 May final rout
  - Death of Stefan Potocki — Wounded in battle, captured by Tatars, died of gangrene 19 May; symbol of the fall of noble
    pride
  words: 550
- section: 'Читання: Опис битви в літописі'
  points:
  - Excerpt from the Eyewitness Chronicle — [!quote] «Хмельницький... не ожидаючи на Запорожжє...» (analysis of archaic vs
    modern narrative)
  words: 550
- section: 'Первинні джерела: Листи про поразку'
  points:
  - 'Potocki''s last letter to his father — [!source] Reconstruction of emotional state: from arrogance to despair; the ''father''s
    pride'' narrative'
  words: 550
- section: Деколонізаційний погляд
  points:
  - Debunking the myth of 'accidental victory' — [!decolonization] Khmelnytsky as a calculated strategist, not a chaotic rebel
    leader
  - Cossack military art vs. feudal arrogance — Synthesis of European infantry tactics and Steppe maneuverability vs rigid
    Polish doctrine
  words: 550
- section: Європа у 1648 році
  points:
  - Treaty of Westphalia and the end of the 30 Years' War — Redrawing the map of Europe; synchronicity of events
  - The Crisis of the 17th Century (Fronde, English Revolution) — Global context of upheaval and state-building
  - Ukraine entering the European stage — The 'Cossack Revolution' as a new geopolitical player disrupting the balance of
    power
  words: 600
vocabulary_hints:
  required:
  - 'авангард (війська, польський) — передова частина армії; collocations: розбити авангард, вислати авангард'
  - 'облога (табору, тривала) — оточення війська; collocations: взяти в облогу, прорвати облогу'
  - 'переправа (через Дніпро, важка) — подолання водної перешкоди; collocations: захопити переправу'
  - 'клейноди (військові, втопити) — символи влади (булава, прапор); context: знищення клейнодів як акт непокори'
  - 'реєстровці (козаки, перехід на бік) — козаки на службі короля; key concept: зміна лояльності'
  - 'зрада (полковників, національна) — порушення вірності; learner error: treason vs betrayal nuance'
  - 'капітуляція (умови, відмова) — припинення опору; collocations: підписати капітуляцію, ганебна капітуляція'
  - 'тріумф (військовий, несподіваний) — видатна перемога; collocations: святкувати тріумф'
  - байрак (урочище, княжий) — яр, порослий лісом; geographical term crucial for the battle map
  - 'шанець (земляний, окопатися) — польове укріплення; collocations: будувати шанці'
  recommended:
  - урочище (Жовті Води) — natural boundary/tract; specific to Ukrainian geography
  - 'гармати (артилерія) — cannons; context: Polish advantage neutralized'
  - оточення (потрапити в) — encirclement; tactical situation
  - засідка (влаштувати) — ambush; Cossack tactic at Kniazhi Bairaky
  - шляхта (польська, пихата) — nobility; social class context
activity_hints:
- type: reading
  focus: Analysis of historical texts
- type: essay-response
  focus: The role of intelligence and diplomacy in victory
- type: comparative-study
  focus: Polish vs. Cossack camp fortifications
- type: critical-analysis
  focus: 'Спростування міфів: Myths about the battle'
  items: 4
persona:
  voice: Senior Professor of History
  role: Cossack Colonel
grammar:
- 'Military narrative: descriptions of maneuvers'
- Cause and effect in historical context
register: публіцистичний
prerequisites:
- bohdan-khmelnytskyi
connects_to:
- zborivska-bila-tserkva

```

---

## PART 1: Deep Research

Research **Битва під Жовтими Водами** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Битва під Жовтими Водами

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Битва під Жовтими Водами"
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
