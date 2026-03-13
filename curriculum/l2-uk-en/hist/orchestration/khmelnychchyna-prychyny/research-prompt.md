# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-051
level: HIST
sequence: 51
slug: khmelnychchyna-prychyny
version: '2.0'
title: 'Хмельниччина I: причини та початок'
subtitle: 'The Khmelnytsky Uprising: Causes and Outbreak'
focus: history
pedagogy: CBI
phase: HIST.5 [Rise of Cossacks]
word_target: 5000
objectives:
- Учень може пояснити соціальні та релігійні причини повстання
- Учень може аналізувати особисту трагедію Хмельницького як каталізатор подій
- Учень може описати перші перемоги 1648 року (Жовті Води, Корсунь)
sources:
- name: History of Ukraine-Rus
  url: http://litopys.org.ua/hrushrus/iur.htm
  type: reference
  notes: Classic historical account
- name: The Khmelnytsky Uprising
  url: https://encyclopediaofukraine.com
  type: academic
  notes: Modern analysis
content_outline:
- section: 'Вступ: На порозі великих змін'
  points:
  - The atmosphere in Ukraine in the mid-17th century — demographic boom and colonization of the 'Wild Fields' creating a
    passionate free population
  - Accumulated tensions and grievances — the 'Golden Peace' (1638-1648) as an illusion or 'calm before the storm'
  - '— include hook: [!context] World context 1648: End of Thirty Years'' War in Europe vs. start of Khmelnychchyna; global
    ''General Crisis'''
  - '— include hook: [!history-bite] Khmelnytsky was ~52 years old, a mature leader, not a young revolutionary'
  words: 700
- section: 'Соціально-економічні причини: Земля і воля'
  points:
  - Enserfment of peasants (pansshchyna) — reached 3-5 days a week on the Right Bank
  - Restrictions on Cossack rights and registry — Ordination of 1638 limited registry to 6,000, turning others into serfs
  - Economic exploitation by magnates — 'leaseholders' (orendatori) controlling church rites; lack of legal protection (sva-villia)
  - '— include hook: [!history-bite] Taxes on everything, even church rites (baptisms, funerals)'
  words: 700
- section: Релігійні та національне гноблення
  points:
  - The Union of Brest and religious conflict — split society; Orthodox 'disuniats' often outlawed
  - Discrimination against the Orthodox Church — banned from guilds and magistrates
  - Polonization of the Ukrainian elite — Vyshnevetsky/Ostrozky families converting to Catholicism, leaving the people 'headless'
    until Cossacks took the lead
  - '— include hook: [!culture] Baroque consciousness: religion was identity; changing faith equaled betrayal'
  words: 700
- section: Політична криза Речі Посполитої
  points:
  - Weakness of royal power vs. magnate anarchy — King Wladyslaw IV wanted war with Turkey to strengthen power vs Sejm
  - Failed attempts at reform by Wladyslaw IV — secret talks with Cossacks (1646) promised rights, then betrayed
  - The 'Golden Peace' period (1638-1648) — described in Polish historiography as 'Złoty spokój', in Ukrainian as 'decade
    of heavies oppression'
  - '— include hook: [!myth-buster] Myth of ''Strong Poland''; reality was ''Noble Anarchy'' where the King couldn''t punish
    even one noble (Chaplynsky)'
  - '— include quote: King Wladyslaw IV allegedly saying ''You have a saber at your side'' (ius resistendi)'
  words: 700
- section: 'Первинні джерела: Скарги та універсали'
  points:
  - Excerpts from contemporary chronicles describing oppression — Litopys Samovydtsia on treating Cossacks 'worse than Turkish
    slaves'
  - Early letters of Khmelnytsky stating grievances — focus on personal tragedy (Subotiv raid) resonating with general discontent
    ('match in a powder keg')
  - '— include quote: Khmelnytsky''s Universals (''...intolerable wrongs to our people...'')'
  words: 700
- section: 'Деколонізаційний погляд: Не бунт, а революція'
  points:
  - 'Reframing the conflict: National Liberation War vs. Civil War — organized campaign with diplomacy (Crimea alliance) and
    state-building goals, not a chaotic peasant riot (Jacquerie)'
  - Debunking myths about 'reunification' desires — 1654 thesis back-projected to 1648; Khmelnytsky sought allies everywhere
    (Turkey, Crimea, Sweden) for survival
  - '— include hook: [!decolonization] Imperial framing vs. Ukrainian reality of statehood'
  words: 700
- section: Читання
  points:
  - Intro to reading tasks — adapted excerpt from Khmelnytsky's letter or Litopys Samovydtsia analyzing vocabulary of oppression
    (kryvda, volnosti)
  words: 800
vocabulary_hints:
  required:
  - повстання (uprising/rebellion) — often paired with 'національно-визвольне' (national liberation)
  - 'гніт (oppression) — collocations: соціальний, національний, релігійний'
  - унія (Union) — refers specifically to the Union of Brest (1596)
  - шляхта (nobility) — the ruling class in the Polish-Lithuanian Commonwealth
  - реєстр (registry) — list of official Cossacks; limiting it was a major cause of war
  - універсал (universal) — manifesto or decree by the Hetman
  - союз (alliance) — e.g., with Crimean Khanate (військово-політичний союз)
  - засідка (ambush) — military tactic used in early battles
  - перемога (victory) — e.g., at Zhovti Vody and Korsun
  - 'воля (freedom/will) — dual meaning: liberty vs. willpower; core Cossack value'
  recommended:
  - кріпацтво (serfdom) — essential term for the social cause
  - панщина (corvée) — labor obligation to the lord
  - свавілля (arbitrariness) — lack of rule of law; impunity of magnates
  - дизуніти (disuniats) — derogatory term for Orthodox believers who rejected the Union
  - посполиті (commoners) — term for peasants/townspeople vs. Cossacks/Nobles
activity_hints:
- type: reading
  focus: Linguistic analysis of 17th-century documents
- type: essay-response
  focus: Causes of the uprising
- type: comparative-study
  focus: Polish vs. Cossack perspective
- type: critical-analysis
  focus: 'Верифікація фактів: Facts about the battles'
  items: 4
persona:
  voice: Senior Professor of History
  role: Registered Cossack
grammar:
- 'Historical narrative: cause and effect'
- Military and political terminology
register: публіцистичний
prerequisites:
- syntez-kozatstvo-vytoky
connects_to:
- bohdan-khmelnytskyi

```

---

## PART 1: Deep Research

Research **Хмельниччина I: причини та початок** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Хмельниччина I: причини та початок

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Хмельниччина I: причини та початок"
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
