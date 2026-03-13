# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: hist-017
level: HIST
sequence: 17
slug: kniazivski-usobiytsi
version: '2.0'
title: Княжі усобиці та роздроблення
focus: history
pedagogy: CBI
phase: HIST.1 [Kyivan Rus]
word_target: 5000
objectives:
- Understand the causes of Kyivan Rus fragmentation
- Analyze the decisions of the Liubech Congress
- Discuss the impact of Polovtsian threat on unity
sources:
- name: Роздроблення Київської Русі (Вікіпедія)
  url: https://uk.wikipedia.org/wiki/Роздроблення_Київської_Русі
  type: reference
  notes: Overview of fragmentation
- name: Любецький з'їзд (Вікіпедія)
  url: https://uk.wikipedia.org/wiki/Любецький_з%27їзд
  type: reference
  notes: Congress that formalized division
- name: Повість минулих літ
  url: https://litopys.org.ua/pvl/pvl.htm
  type: primary
  notes: Chronicle accounts
content_outline:
- section: Розминка
  points:
  - Defining sovereignty vs suzerainty — Київський князь як сюзерен (перший серед рівних), а не абсолютний монарх
  - The map of 1054 vs 1132 — [!context] comparison of 'monolithic' 1054 map vs 'patchwork puzzle' of 1132
  words: 550
- section: 'Читання: Тріумвірат Ярославичів'
  points:
  - The will of Yaroslav the Wise — attempt to create a system of checks and balances; rota system breakdown
  - Battle of Alta (1068) — [!history-bite] citizens expelled Izyaslav not for tyranny but for failure to protect; first major
    defeat by Polovtsians
  - Kyiv Uprising — Vseslav Polotsky released from prison ('поруба') and elected by community; precedent of 'viche' power
  words: 550
- section: Любецький з'їзд (1097)
  points:
  - Every man holds his own fatherland — «Кожен хай держить отчину свою»; shift from rota system to hereditary patrimony
  - The blinding of Vasylko — [!myth-buster] 'Unity' oath immediately followed by brutal realpolitik violation; shock to society
  - Consequences of the Congress — legalization of political fragmentation (federalization)
  words: 550
- section: Володимир Мономах
  points:
  - Crusades against Polovtsians — successful campaigns of 1103 and 1111; securing the borders
  - Monomakh's Reforms (Statute) — social compromise after 1113 uprising; limiting interest rates ('різи') and protecting
    debtors ('закупи')
  - Instruction (Povchannia) — [!quote] «Не проминіть ніколи людину, не привітавши її...»; image of ideal Christian ruler-humanist
  words: 550
- section: Соціальна структура та Економіка
  points:
  - Economic causes of fragmentation — [!decolonization] growth of regional capitals (Chernihiv, Halych) made them independent
    of Kyiv
  - Boyars, Druzhina, Smerds — distinction between free peasants (smerds) and debt-dependent (zakupy)
  - Urban growth — Kyiv remains largest (50k pop), but regional centers rise; craft and trade expansion
  words: 550
- section: Культура та Церква
  points:
  - Architecture (St. Michael's) — built by Sviatopolk II (1108-1113); 'shimmering painting' mosaics
  - Chronicle writing (Nestor) — Nestor the Chronicler as ideologue of Rus unity (PVL 1113)
  - Church as unifying force — Kyiv Metropoly remained the only structure uniting all lands
  words: 550
- section: Первинні джерела
  points:
  - 'Extract from the Primary Chronicle on Liubech — include quote: «Пощо ми губимо Руськую землю, самі проти себе зваду маючи?»'
  - 'Extract from Monomakh''s Instruction — focus on moral guidelines: do not kill, honor guests, do not be lazy'
  words: 550
- section: Деколонізаційний погляд
  points:
  - Reframing Fragmentation as Decentralization — [!perspective] not 'collapse' but evolution into confederation
  - European parallels — comparison with Holy Roman Empire or France; standard feudal stage
  - Myth of 'Feudal Disunity' — debunking Soviet/Imperial myth of 'disaster' leading to Moscow's rise; debunking 'Joint Cradle'
    myth
  words: 550
- section: Підсумок
  points:
  - Legacy of the era — unity requires high political culture; internal contradictions laid groundwork for vulnerability to
    Mongols
  words: 600
vocabulary_hints:
  required:
  - усобиця (internecine war) — князівські усобиці, припинити усобиці
  - роздроблення (fragmentation) — феодальне роздроблення, політична децентралізація
  - лествичне право (rota system) — принцип сеньйорату, спадкування за старшинством
  - престолонаслідування (succession) — порядок престолонаслідування, криза престолонаслідування
  - отчина (patrimony) — володіти отчиною, батьківська спадщина
  - з'їзд (congress) — князівський з'їзд, Любецький з'їзд
  - боярин (boyar) — впливові бояри, боярська рада
  - князівство (principality) — удільне князівство, Київське князівство
  - половці (Polovtsians) — половецька загроза, походи на половців
  - єдність (unity) — збереження єдності, ідея єдності Русі
  - центральна влада (central authority) — послаблення центральної влади
  - місцева еліта (local elite) — зростання впливу місцевої еліти
  recommended:
  - засліплення (blinding) — політичне засліплення, жорстока розправа
  - номінальний (nominal) — номінальний правитель, номінальна влада
  - союз (alliance) — укласти союз, військовий союз
  - культурний розквіт (cultural flourishing) — епоха культурного розквіту регіонів
activity_hints:
- type: reading
  focus: Chronicle account of Liubech Congress
  source: Provide in module
- type: comparative-study
  focus: Unified Rus vs fragmented Rus
  output: Two-column analysis
- type: essay-response
  focus: Чи було роздроблення неминучим?
connects_to:
- hist-21 (Mongol invasion)
- hist-23 (Danylo of Halych)
- 'hist-20 (Synthesis: Kyivan Rus)'
prerequisites:
- hist-12 (Yaroslav the Wise)
- hist-15 (Volodymyr Monomakh)
persona:
  voice: Senior Professor of History
  role: Dynastic Chronicler
grammar:
- Past tense narrative
- Political and military terminology
immersion: 100% Ukrainian

```

---

## PART 1: Deep Research

Research **Княжі усобиці та роздроблення** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Княжі усобиці та роздроблення

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — Phase D verifies prose against this -->
```yaml
subject: "Княжі усобиці та роздроблення"
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
