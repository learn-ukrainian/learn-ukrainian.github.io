# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-048
level: HIST
sequence: 48
slug: kozatske-viisko
version: '2.0'
title: Козацьке військо та озброєння
subtitle: Cossack Army and Weaponry
focus: history
pedagogy: CBI
phase: HIST.5 [Rise of Cossacks]
word_target: 5000
objectives:
- Учень може описати структуру та ієрархію козацького війська
- Учень може аналізувати типи озброєння та їхнє походження
- Учень може пояснити тактичні переваги козацької піхоти та кавалерії
sources:
- name: Military Art of Ukrainian Cossacks
  url: https://resource.history.org.ua/item/0002345
  type: academic
  notes: Detailed analysis of tactics
- name: Cossack Weaponry - Museum Project
  url: https://warmuseum.kyiv.ua
  type: reference
  notes: Visual and technical details
content_outline:
- section: 'Вступ: Феномен козацького війська'
  points:
  - Universal military service and democracy — concept of 'Лицарський люд' (Knightly people) and distinct social status
  - International reputation of Cossack mercenaries — valued from France (Dunkirk) to Persia; [!history-bite] about Thirty
    Years' War participation
  words: 600
- section: 'Структура та Ієрархія: Від коша до полку'
  points:
  - The role of the Hetman and General Staff — Oboznyi (logistics), Suddia (justice), Pysar (intelligence/records), Osavuly
    (aides), Khorunzhyi (flag-bearer)
  - Territorial and functional divisions — [!context] Administrative division of Hetmanate (regiments/hundreds) duplicated
    military structure; state as 'military camp'
  - Discipline and military code — strict alcohol ban during campaigns; death penalty for disobedience
  words: 600
- section: 'Озброєння: Шабля, самопал та гармата'
  points:
  - 'Individual weaponry: fire and steel — priority of firearms (muskets/samopaly); 3-rank volley fire tactic (fire-pass-load)'
  - The cult of the sabre (shablya) — [!myth-buster] Sabre as 'weapon of last resort' or cavalry, while infantry relied on
    fire; curved eastern type
  - 'Artillery: mobility and psychological impact — light field falconets transported on wagons; high status of artillery
    masters'
  words: 600
- section: 'Тактика бою: Козацький табір та розвідка'
  points:
  - The 'tabor' as a defensive fort — [!decolonization] Wagenburg (moving fortress of chained wagons) as prototype of modern
    armored units
  - 'Cossack ''plastuny'' (scouts) — special operations skills: underwater breathing (reeds), camouflage in steppe'
  - Siege warfare and river raids — use of 'chaika' boats for sea raids (e.g., Kafa); engineering skills (mining, earthworks)
  words: 600
- section: 'Символіка та Клейноди: Знаки влади'
  points:
  - Bulava, bunchuk, and seals — Bulava (Hetman), Bunchuk (horse tail command symbol), Seal ('Knight with Musket')
  - The sacred meaning of the banner (khoruhva) — [!culture] Loss of khoruhva equated to defeat/shame; Crimson banner with
    Archangel Michael
  words: 600
- section: 'Читання: Опис козацького вишколу'
  points:
  - Account of a foreign observer on Cossack training — Guillaume Le Vasseur de Beauplan on endurance, orientation, and gunpowder
    making
  words: 600
- section: 'Первинні джерела: Голоси епохи'
  points:
  - Analysis of official documents and letters — Khmelnytskyi's diplomatic correspondence vs Cossack chronicles (Hrabianka/Velychko)
  words: 600
- section: Деколонізаційний погляд
  points:
  - Cossacks as a modern professional army, not a 'rabble' — debunking 'anarchy/bandit' myths; 'Christian Republic' concept
  - Influence on European military science — adoption of Cossack infantry tactics and light cavalry models by Europe
  - Ukraine's military subjectivity — [!perspective] 'Antemurale Christianitatis' (Bulwark of Christianity); recognized by
    European monarchs and Pope
  words: 800
vocabulary_hints:
  required:
  - булава (mace/baton) — символ влади гетьмана; вручалася на раді
  - пернач (mace with flanges) — символ влади полковника
  - самопал (musket/firearm) — основна зброя козацької піхоти; 'козак з самопалом'
  - шабля (sabre) — символічна зброя; 'козацька шабля', 'гостра шабля'
  - гармата (cannon) — 'козацька артилерія', 'влучити з гармати'
  - полк (regiment) — адміністративно-військова одиниця; 'Київський полк'
  - сотня (company/hundred) — підрозділ полку; 'козацька сотня'
  - кіш (encampment/command) — 'Запорозький Кіш', центр управління
  - обоз (baggage train) — 'військовий обоз', логістика
  - хоругва (banner) — 'військова хоругва', символ честі
  recommended:
  - клейноди (regalia) — символи влади (булава, бунчук, печатка)
  - реєстровець (registered Cossack) — професійний військовий на службі
  - пластун (scout) — козацький розвідник
  - чайка (boat) — бойовий човен для морських походів
  - табір (camp/wagon fort) — 'рухома фортеця', тактичний прийом
  - курінь (battalion/barracks) — військова одиниця на Січі
  - довбиш (drummer) — відповідальний за литаври і скликання ради
activity_hints:
- type: reading
  focus: Primary sources on military structure
- type: essay-response
  focus: Cossack military ethics and modern parallels
- type: comparative-study
  focus: Cossack vs Western European military organization
- type: critical-analysis
  focus: 'Верифікація фактів: Facts about weaponry and ranks'
  items: 4
persona:
  voice: Senior Professor of History
  role: Artillery Master
grammar:
- Military terminology and formations
- Historical narrative register
register: публіцистичний
prerequisites:
- kozatska-kultura
connects_to:
- morski-pokhody

```

---

## PART 1: Deep Research

Research **Козацьке військо та озброєння** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Козацьке військо та озброєння

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Козацьке військо та озброєння"
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
