# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-060
level: HIST
sequence: 60
slug: andrusivske-peremyrya
version: '2.0'
title: 'Андрусівське перемир''я: Поділ України'
subtitle: 'The Truce of Andrusovo: The Partition of Ukraine'
focus: history
pedagogy: CBI
phase: HIST.6 [Khmelnytsky & Cossack State]
word_target: 5000
objectives:
- Учень може пояснити умови Андрусівського перемир'я 1667 року
- Учень може проаналізувати наслідки поділу України по Дніпру
- Учень може оцінити роль Ордіна-Нащокіна в дипломатичній грі
sources:
- name: Andrusovo Treaty - Encyclopedia of Ukraine
  url: https://www.encyclopediaofukraine.com/display.asp?linkpath=pages%5CA%5CN%5CAndrusovoTreatyof1667.htm
  type: reference
  notes: Academic summary
- name: Text of the Treaty
  url: http://litopys.org.ua/
  type: primary
  notes: Original articles
content_outline:
- section: 'Вступ: Ніч дипломатії в Андрусові'
  points:
  - The exhaustion of Poland and Muscovy by 1667 — Poland's 'Rokosz Lubomirskiego' and Muscovy's Copper Riot created mutual
    desperation
  - The secret negotiations without Ukrainian representatives — [!context] Cossack envoys were physically barred from the
    meeting hall, highlighting the 'separate peace' nature
  words: 600
- section: 'Архітектор поділу: Афанасій Ордин-Нащокін'
  points:
  - The figure of the Muscovite diplomat — [!history-bite] Known as 'father of Russian diplomacy' but for Ukraine he was the
    'architect of the split'
  - 'Strategy: divide and rule — Convinced Poles that ''unruly Cossacks'' were a mutual threat to be tamed jointly'
  - Use of gifts and bribes — Corruption of Polish commissioners to secure favorable terms
  words: 600
- section: 'Умови договору: Геополітична ампутація'
  points:
  - The border along the Dnipro river — Left Bank + Sivershchyna + Smolensk to Moscow; Right Bank + Belarus to Poland
  - The fate of Kyiv ('rule of two years') — Formally leased until 1669, but became a permanent occupation (broken promise)
  - The status of Zaporizhzhia (condominium) — Joint Polish-Muscovite control to use Cossacks against Tatars; [!decolonization]
    'Little Russian Ukraine' treated as object, not subject
  words: 600
- section: 'Реакція України: Шок і гнів'
  points:
  - Reaction of Doroshenko and Briukhovetsky — Jan 1668 councils in Chyhyryn and Hadiach rejected both monarchs; Doroshenko
    wrote 'we cannot trust...'
  - 'The murder of Briukhovetsky by the mob — June 1668 at Opishnya: torn apart by Cossacks for his ''Moscow policy'''
  - The feeling of betrayal by both 'protectors' — [!quote] Samovydets chronicle describes Cossacks 'beating their hats on
    the ground' in despair
  words: 600
- section: 'Соціальні наслідки: Життя на розломі'
  points:
  - Economic collapse and disruption of trade — Dnipro transformed from a trade artery into a 'border of enmity'
  - Forced migrations ('The Great Drive') — Start of Right Bank depopulation; appearance of the term «тогобочні» (people from
    the other side)
  - Religious intolerance on both banks — Catholic expansion on Right Bank vs. Muscovite absorption of Kyiv Metropoly on Left
    Bank
  words: 600
- section: Чому світ промовчав?
  points:
  - The international context (wars in Europe) — [!context] Louis XIV's War of Devolution (1667-68) and Anglo-Dutch wars distracted
    the West
  - Why a weak Ukraine was beneficial to neighbors — A divided buffer state was easier to manipulate than a strong Cossack
    Hetmanate
  words: 600
- section: 'Первинні джерела: Текст договору'
  points:
  - Analysis of the articles of the truce — Article 3 specifically excludes Cossacks from protection; use of term «свавільні»
    (unruly) to delegitimize them
  words: 600
- section: Деколонізаційний погляд
  points:
  - Debunking the myth of 'stabilization' — [!myth-buster] 1654 'reunification' myth exploded by 1667 betrayal; Moscow willingly
    returned 'reunited' lands to Poland
  - Andrusovo as a crime against statehood — An international conspiracy of two empires to dismember a third nation; triggered
    the 'Ruin'
  words: 800
vocabulary_hints:
  required:
  - перемир'я (truce) — often framed by Ukrainians as «Андрусівська змова» (Andrusovo Conspiracy)
  - демаркація (demarcation) — establishing the Dnipro border
  - кондомініум (condominium) — joint control over Zaporizhzhia
  - розкол (split/schism) — political and social division of the Hetmanate
  - сепаратний (separate) — сепаратний мир (separate peace) concluded behind ally's back
  - статус-кво (status quo) — attempt to freeze the conflict
  - депортація (deportation) — forced movement of populations
  - біженці (refugees) — fleeing the 'Ruin'
  - змова (conspiracy) — secret agreement against Ukraine
  - руйнація (ruin/destruction) — the period triggered by this treaty
  recommended:
  - тогобочні (those from the other side) — [!culture] term for Ukrainians across the river
  - свавільні (unruly/arbitrary) — imperial label for Cossacks in the treaty
  - ампутація (amputation) — metaphor for the territorial loss
activity_hints:
- type: reading
  focus: Analysis of the Andrusovo treaty text
- type: essay-response
  focus: The tragedy of the partition of Ukraine
- type: comparative-study
  focus: Zboriv vs. Andrusovo
- type: critical-analysis
  focus: 'Спростування міфів: Myths about the truce'
  items: 4
persona:
  voice: Senior Professor of History
  role: Border Commissioner
grammar:
- 'Diplomatic terminology: truce, demarcation'
- Conditional sentences in historical context
register: публіцистичний
prerequisites:
- ruina-ii
connects_to:
- ivan-sirko

```

---

## PART 1: Deep Research

Research **Андрусівське перемир'я: Поділ України** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Андрусівське перемир'я: Поділ України

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Андрусівське перемир'я: Поділ України"
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
