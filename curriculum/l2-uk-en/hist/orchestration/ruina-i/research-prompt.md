# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: hist-058
level: HIST
sequence: 58
slug: ruina-i
version: '2.0'
title: 'Руїна I: Виговщина і розкол'
subtitle: 'The Ruin I: Vyhovsky and the Split'
focus: history
pedagogy: CBI
phase: HIST.6 [Khmelnytsky & Cossack State]
word_target: 5000
objectives:
- Учень може пояснити причини громадянської війни (Руїни)
- Учень може проаналізувати наслідки Конотопської битви
- Учень може оцінити роль Чорної ради 1663 року в розколі України
sources:
- name: The Ruin - Encyclopedia of Ukraine
  url: https://www.encyclopediaofukraine.com/display.asp?linkpath=pages%5CR%5CU%5CRuin.htm
  type: reference
  notes: Overview of the period
- name: Chronicle of Eyewitness
  url: http://litopys.org.ua/samovyd/sam.htm
  type: primary
  notes: Primary source for the period
content_outline:
- section: 'Вступ: Епоха великих надій і розчарувань'
  points:
  - Definition of 'The Ruin' (1657-1687) — term coined by Cossack chronicler Samiilo Velychko to describe the devastation
  - The vacuum of power after Khmelnytsky — [!context] Ruin as state collapse due to internal strife plus external intervention
  words: 600
- section: 'Гетьман Іван Виговський: Курс на Європу'
  points:
  - Vyhovsky's biography and political program — General Chancellor, intellectual, architect of the Hadiach Union; [!myth-buster]
    not a 'Polish lackey' but a statist
  - The suppression of the Pushkar uprising — first act of civil war, inspired and financed by Moscow (Pushkar and Barabash)
  - 'Foreign policy: balancing between Moscow and Warsaw — seeking equal status for Ukraine in Europe'
  words: 600
- section: Гадяцька унія і війна з Москвою
  points:
  - The failure of the alliance with Moscow — violation of Pereyaslav articles by the Tsar
  - The signing of the Treaty of Hadiach (brief recap) — Grand Duchy of Rus as 3rd member of Commonwealth with own army, treasury,
    and coin
  - The start of the Muscovite-Ukrainian war — Moscow declares Vyhovsky a traitor; open military aggression
  words: 600
- section: 'Конотопська битва 1659: Втрачена перемога'
  points:
  - The siege of Konotop by Trubetskoy — heroic defense by Colonel Hulyanytsky
  - 'Tactics of the battle: deceptive retreat — luring Muscovites into the marshy Sosnivka river valley'
  - 'The defeat of the Muscovite cavalry and its consequences — Solovyov quote: ''flower of Moscow cavalry perished''; [!history-bite]
    Tsar Alexei Mikhailovich in mourning, preparing to evacuate Moscow'
  words: 600
- section: Падіння Виговського і початок хаосу
  points:
  - The uprising of Ivan Sirko in Zaporizhzhia — forced Tatar allies to return to Crimea, weakening Vyhovsky
  - The election of Yurii Khmelnytsky — [!decolonization] Vyhovsky lost the information war to populist demagoguery about
    'Polish serfdom'
  - The Chudniv campaign and the split of the state — cementing the division into Left and Right Banks
  words: 600
- section: 'Чорна рада 1663: Тріумф охлократії'
  points:
  - The struggle for power on the Left Bank — vacuum filled by populism
  - Somko vs. Briukhovetsky — [!culture] Panteleimon Kulish's novel 'Chorna rada' depicts this conflict between elite statist
    (Somko) and demagogue (Briukhovetsky)
  - The 'Black Council' in Nizhyn and its tragic outcome — 1663; participation of 'chern' (commoners); execution of Somko
    and Zolota
  words: 600
- section: 'Первинні джерела: Літопис Самовидця'
  points:
  - Reading excerpts about the Black Council — eyewitness account (likely Roman Rakushka-Romanovsky)
  - Contrast between mob chaos and state order — criticism of both 'chern' for anarchy and 'starshyna' for pride
  words: 600
- section: Деколонізаційний погляд
  points:
  - 'The myth of ''civil war'' vs. foreign intervention — Moscow''s hybrid war tactics: financing opposition to destabilize
    the Hetmanate'
  - Moscow's role in deepening the split — [!quote] irony of Briukhovetsky promising rights but bringing Muscovite voyevodas
  words: 800
vocabulary_hints:
  required:
  - руїна (ruin) — capitalized when referring to the period; synonym for devastation
  - розкол (split/schism) — often used for the division of the Hetmanate
  - чорна рада (Black Council) — council where commoners (chern) participated; symbol of mob rule
  - охлократія (ochlocracy) — mob rule; negative term for the events of 1663
  - міжусобиця (internecine strife) — civil conflict within the state
  - булава (bulava/mace) — symbol of Hetman's power; 'zrekatysia bulavy' (to resign)
  - промосковський (pro-Moscow) — political orientation of the Left Bank elite
  - пропольський (pro-Polish) — political orientation often ascribed to Vyhovsky
  - лівобережжя (Left Bank) — sphere of Moscow's influence
  - правобережжя (Right Bank) — sphere of Poland's influence
  recommended:
  - наказний гетьман (acting hetman) — temporary title held by Vyhovsky initially
  - воєвода (voyevoda) — Muscovite military governor installed in Ukrainian cities
  - зрадник (traitor) — label used by Moscow propaganda against Vyhovsky
activity_hints:
- type: reading
  focus: Analysis of the Black Council description
- type: essay-response
  focus: 'Causes of the Ruin: internal or external?'
- type: comparative-study
  focus: Vyhovsky vs. Briukhovetsky policies
- type: critical-analysis
  focus: 'Верифікація фактів: Facts about Konotop and Nizhyn'
  items: 4
persona:
  voice: Senior Professor of History
  role: Mercenary Captain
grammar:
- 'Historical narrative: description of chaos'
- 'Political terminology: factions and parties'
register: публіцистичний
prerequisites:
- yurii-nemyrych
connects_to:
- ruina-ii

```

---

## PART 1: Deep Research

Research **Руїна I: Виговщина і розкол** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Руїна I: Виговщина і розкол

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — Phase D verifies prose against this -->
```yaml
subject: "Руїна I: Виговщина і розкол"
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
