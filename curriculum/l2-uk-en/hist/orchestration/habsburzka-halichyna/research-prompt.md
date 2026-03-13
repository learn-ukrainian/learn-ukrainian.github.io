# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-076
level: HIST
sequence: 76
slug: habsburzka-halichyna
version: '2.0'
title: Габсбурзька Галичина
subtitle: 'Habsburg Galicia: The Ukrainian Piedmont 1772-1918'
focus: history
pedagogy: CBI
phase: HIST.8 [Imperial Era]
word_target: 5000
objectives:
- Учень може описати історію Галичини під владою Габсбургів
- Учень може пояснити концепцію «Українського П'ємонту»
- Учень може порівняти становище українців в Австрії та Росії
- Учень може проаналізувати розвиток національного руху в Галичині
content_outline:
- section: 'Вступ: Дві долі українського народу'
  points:
  - 'Поділи Польщі та приєднання Галичини до Австрії — розрив українських земель між двома імперіями (1772, 1793, 1795); contested
    term: «Galicia» vs «Małopolska Wschodnia»'
  - 'Чому Габсбурги створили умови для відродження — прагматичне використання українців як противаги польській шляхті; [!myth-buster]
    про «доброго цісаря»; concept: «Tiroler des Ostens» (Tyroleans of the East)'
  - 'Концепція «Українського П''ємонту» — регіон як політична лабораторія та лідер національного об''єднання (за М. Грушевським);
    contrast: legal struggle vs underground resistance in Russia'
  words: 850
- section: Початок австрійського правління (1772-1848)
  points:
  - 'Йосифінські реформи — релігійна емансипація (1774), «Барбареум» та заборона принизливої назви «уніати»; date: 1784 (Studium
    Ruthenum) and renewal of Lviv University'
  - Греко-католицька церква як охоронець ідентичності — формування освіченої еліти («попівська нація») на противагу полонізованій
    шляхті
  - 'Руська трійця та культурне пробудження — «Русалка Дністрова» (1837) та впровадження живої народної мови; [!history-bite]
    про церковну цензуру (local authorities, not Vienna); quote: Markiyan Shashkevych on «pure Rus language»'
  - 'Головна Руська Рада 1848 року — «Весна народів», вимога поділу Галичини та перша поява синьо-жовтого прапора на ратуші;
    date: May 1848; key demand: administrative separation from Polish West Galicia'
  words: 850
- section: Національний рух (1848-1914)
  points:
  - 'Москвофіли vs. народовці — орієнтація на Росію (субсидії, «язичіє») проти єдності з Наддніпрянщиною; [!history-bite]
    про штучну мову москвофілів (example: «извѣстны суть»)'
  - 'Товариство «Просвіта» — боротьба з неписьменністю (1868) та економічний самозахист («Свій до свого по своє»); network:
    reading rooms (chytalni) and cooperatives'
  - 'Наукове товариство імені Шевченка — створення неофіційної Академії наук (1873/1892) та роль Грушевського; output: hundreds
    of volumes of «Zapysky NTSh»'
  - 'Політичні партії та виборча боротьба — від РУРП (1890) до УНДП (1899); перехід від культурництва до реальної політики;
    key figures: Ivan Franko, Mykhailo Pavlyk'
  - 'Конфлікт з поляками — боротьба за університет та виборчу реформу; вбивство намісника Потоцького (1908); actor: student
    Myroslav Sichynsky'
  words: 850
- section: Первинні джерела
  points:
  - Документи Головної Руської Ради — [!quote] з Маніфесту 1848 про єдність 15-мільйонного народу («Ми Русини Галицькі...»)
  - 'Статути українських організацій — структура громадянського суспільства («Січ», «Сокіл»); comparison: building a «state
    within a state»'
  - Преса того часу — роль газет «Зоря Галицька», «Діло» та «Батьківщина» у формуванні політичної культури vs censorship in
    Russian Empire
  words: 850
- section: Деколонізаційний погляд
  points:
  - 'Австрія vs. Росія: порівняння колоніальних політик — Валуєвський циркуляр проти кафедр в університетах та місць у парламенті;
    contrast: 1863/1876 bans vs 1868 Prosvita founding'
  - 'Чому Галичина стала осередком національного руху — «вікно можливостей» через австрійсько-польське протистояння; strategy:
    loyalty to Habsburgs as «lesser evil»'
  - 'Межі австрійського «лібералізму» — Галичина як «Golomeria und Hungerland», бідність та соціальний гніт; economic reality:
    poorest province of the empire'
  words: 850
- section: 'Підсумок: Спадщина Габсбургів'
  points:
  - 'Перша світова війна та кінець імперії — Талергоф і крах ілюзій щодо лояльності; tragedy: internment of Russophiles and
    Ukrainophiles'
  - 'Галицька ідентичність у XX столітті — дисциплінованість, правова культура та здатність до самоорганізації; legacy: foundation
    for ZUNR (1918)'
  - 'Сучасна пам''ять про Австрію — [!reflection] чи відбулася б незалежність без галицького досвіду парламентаризму? synthesis:
    political maturity gained in the «laboratory»'
  words: 750
vocabulary_hints:
  required:
  - 'Галичина (Galicia) — Східна Галичина (етнічно українська), королівство Галичини та Володимирії; contested term: Małopolska
    Wschodnia (Polish view)'
  - 'автономія (autonomy) — широка культурна автономія, боротьба за політичну автономію; context: cultural vs political autonomy'
  - 'П''ємонт (Piedmont) — Український П''ємонт (політичний центр відродження); metaphor: region leading national unification'
  - 'національний рух (national movement) — модерний національний рух, політизація руху; dates: 1848-1914'
  - 'відродження (revival) — національне відродження, культурне пробудження; stages: cultural (Rusalka) -> political (RURP)'
  - 'греко-католицький (Greek-Catholic) — греко-католицька церква, священники як інтелігенція; term: Uniate (derogatory) vs
    Greek-Catholic (official)'
  - 'москвофіл (Russophile) — старорусини, орієнтація на Російську імперію; synonym: Starorusyny; language: yazychie'
  - 'народовець (populist/ukrainophile) — українофіли, єдність з Великою Україною; orientation: Kyiv'
  recommended:
  - 'реформа (reform) — йосифінські реформи, виборча реформа; specific: Josephine reforms (1770s-80s)'
  - 'сейм (sejm/parliament) — Галицький крайовий сейм, посол до сейму; institution: local parliament in Lviv'
  - 'намісник (viceroy) — австрійський намісник, вбивство намісника; figure: Andrzej Potocki (assassinated 1908)'
  - 'консерватор (conservative) — українські консерватори, лояльність до корони; context: loyalism to Kaiser'
  - 'товариство (society) — таємне товариство, наукове товариство, «Просвіта»; examples: Prosvita, Sokil, Sich'
  - 'конституція (constitution) — конституційні свободи, парламентська боротьба; impact: legal framework for struggle'
activity_hints:
- type: reading
  focus: Документи Головної Руської Ради
  source: Архівні документи
  items: 4
- type: critical-analysis
  focus: 'Критична оцінка: Порівняння Австрії та Росії'
  items: 5
- type: essay-response
  focus: Чому Галичина стала «Українським П'ємонтом»?
connects_to:
- hist-85 (Франко, Леся, Грінченко)
- hist-88 (Перша світова)
prerequisites:
- hist-75 (Україна в Російській імперії)
persona:
  voice: Senior Professor of History
  role: Diet Deputy
grammar:
- Минулий час в історичному наративі
- Порівняльні конструкції
- Адміністративна лексика
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Габсбурзька Галичина** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Габсбурзька Галичина

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Габсбурзька Галичина"
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
