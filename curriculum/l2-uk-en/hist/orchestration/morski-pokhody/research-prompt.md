# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-049
level: HIST
sequence: 49
slug: morski-pokhody
version: '2.0'
title: Морські походи козаків
subtitle: Cossack Naval Expeditions
focus: history
pedagogy: CBI
phase: HIST.5 [Rise of Cossacks]
word_target: 5000
objectives:
- Учень може описати будову та переваги козацької чайки
- Учень може аналізувати стратегічне значення морських походів Сагайдачного
- Учень може пояснити вплив козацького флоту на Османську імперію
sources:
- name: Naval Expeditions of Zaporozhian Cossacks
  url: https://history.org.ua/uk/lib/12345
  type: academic
  notes: Detailed historical reconstruction
- name: Guillaume de Beauplan - Description of Ukraine
  url: http://litopys.org.ua/boplan/bop.htm
  type: primary
  notes: Classic source on boat construction
content_outline:
- section: 'Вступ: Чорне море як арена боротьби'
  points:
  - Ottoman dominance in the 16th-17th centuries — control of food supply routes to Istanbul
  - The Black Sea as a 'Turkish Lake' — [!context] concept of Karadeniz as a closed Ottoman internal sea
  words: 600
- section: 'Козацька Чайка: Шедевр суднобудування'
  points:
  - Construction from a single trunk and reed belts — [!history-bite] fascines (bundles of reeds) provided unsinkability and
    protection from bullets
  - Mobility, speed, and stealth — low profile made them nearly invisible on water
  - Weaponry on board (falconets) — 4-6 light cannons per boat; crew of 50-70 warrior-oarsmen
  words: 600
- section: 'Стратегія та Тактика: Раптовість та зухвалість'
  points:
  - Night attacks and navigating the Dnieper rapids — use of compass and stars for synchronized movement
  - 'Open sea battles against heavy galleys — [!myth-buster] ''wolf pack'' tactics: attacking from the sun to blind the enemy'
  - Infiltration of the Bosphorus — burning suburbs of Istanbul (1615) within sight of the Sultan's palace
  - Double rudder technology — oars at bow and stern allowed instant reversal without turning
  words: 600
- section: 'Героїчна доба: Походи Петра Сагайдачного'
  points:
  - The taking of Caffa (1616) and freeing of captives — destruction of the largest slave market in Crimea
  - Raids on Trebizond and Sinop — 1614 burning of the Ottoman fleet and arsenal
  - Psychological shock for the Sultan — [!biography] Sahaidachny shifted tactics from defense to preventive strikes
  - Battle of Khotyn (1621) — naval raids distracted Ottoman fleet from supporting land army
  words: 600
- section: 'Життя на морі: Побут та випробування'
  points:
  - 'Discipline on the boat — strict ban on alcohol during campaigns (penalty: thrown overboard)'
  - Navigation by the stars and coastlines — survival in storms and reliance on group cohesion
  words: 600
- section: 'Читання: Свідчення про козацький десант'
  points:
  - Account of the storming of an Ottoman coastal fortress — focus on surprise and musketry/boarding combat
  - 'Quotes from ambassadors — [!quote] Thomas Roe (1623): ''Cossacks are more dangerous than the mightiest enemies...'''
  words: 600
- section: 'Первинні джерела: Листи та хроніки'
  points:
  - Excerpts from Beauplan and Ottoman chronicles — Beauplan's 'Description of Ukraine' on boat construction details
  - Ottoman perspective — Evliya Celebi's prayers for salvation from 'Rus' wrath'
  words: 600
- section: Деколонізаційний погляд
  points:
  - Ukraine as a naval power, not just a land-based one — [!decolonization] early 'thalassocracy' (sea power)
  - Freedom of the seas against imperial blockade — Cossacks as an autonomous geopolitical subject with independent foreign
    policy
  words: 800
vocabulary_hints:
  required:
  - чайка (seagull/boat) — [!history-bite] maneuverable landing craft, 'special forces' of the sea
  - галера (galley) — heavy Ottoman ships, vulnerable to swarm tactics
  - весло (oar) — dual-purpose for rowing and steering
  - щогла (mast) — collapsible for stealth
  - якір (anchor) — essential for holding position
  - десант (landing/descent) — surprise coastal attacks
  - абордаж (boarding) — primary combat tactic after musket volley
  - Чорне море (Black Sea) — contested space, formerly 'Turkish Lake'
  - Кафа (Caffa/Feodosia) — key target in 1616, slave market
  - Стамбул (Istanbul) — ultimate target of psychological warfare
  recommended:
  - фашини (fascines) — reed bundles for buoyancy and protection
  - фальконет (falconet) — light cannon mounted on chajkas
  - бранці (captives) — liberation of slaves as a legitimizing goal
  - суднобудування (shipbuilding) — advanced engineering skills of Cossacks
activity_hints:
- type: reading
  focus: Linguistic analysis of naval descriptions
- type: essay-response
  focus: The Black Sea strategy of the Zaporozhian Host
- type: comparative-study
  focus: Cossack Chayka vs. Ottoman Galley
- type: critical-analysis
  focus: 'Верифікація фактів: Technical facts about seafaring'
  items: 4
persona:
  voice: Senior Professor of History
  role: Chaika Captain
grammar:
- 'Historical narrative: naval terminology'
- Geographical descriptions and directions
register: публіцистичний
prerequisites:
- kozatske-viisko
connects_to:
- syntez-kozatstvo-vytoky

```

---

## PART 1: Deep Research

Research **Морські походи козаків** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

### Mandatory Research Workflow (follow ALL 4 steps in order)

**Step 1 — Wikipedia foundation**: Call `query_wikipedia(mode="extract")` for the main topic article. If the article is long, use `mode="sections"` then `mode="section"` to read key sections. This gives you the factual backbone.

**Step 2 — Literary RAG deep search (MANDATORY)**: Call `search_literary` at least **3 times** with different queries targeting different aspects of the topic. Search for:
- The main subject (person/event/concept name)
- Related figures, institutions, or movements
- The historical period or genre

This is where primary source quotes come from — chronicles, legal texts, poetry, testimonies, scholarly works. Our RAG has 125K+ chunks from litopys.org.ua, izbornyk.org.ua, and scholarly monographs. **Do NOT skip this step even if Wikipedia gave good results.** Wikipedia is secondary; literary RAG has primary sources.

**Step 3 — Cross-verify**: Use `verify_words` to check any Ukrainian vocabulary you plan to highlight. Use `query_grac(mode="frequency")` for frequency data on key terms.

**Step 4 — Fill gaps**: If Steps 1-2 left gaps in any `content_outline` section, do targeted `query_wikipedia` or `search_literary` calls for those specific sections.

### Research Requirements

1. **Sources**: Minimum **4 distinct sources** — at least 1 from Wikipedia AND at least 2 from `search_literary` (RAG). Also consult history.org.ua, litopys.org.ua. Russian-language sources are PROHIBITED. Every factual claim must be traceable to a cited source.
2. **Timeline**: Build a chronological timeline with 5+ dated events/milestones.
3. **Primary Quotes**: Find **3+** quotable primary source excerpts using `search_literary`. Use guillemet quotes «...» for Ukrainian text. If `search_literary` returns relevant chunks, extract and attribute them properly. Mark unverified quotes as `[needs verification]`.
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

# Дослідження: Морські походи козаків

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Морські походи козаків"
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
