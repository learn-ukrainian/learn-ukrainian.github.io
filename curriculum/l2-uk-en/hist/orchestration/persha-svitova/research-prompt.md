# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-088
level: HIST
sequence: 88
slug: persha-svitova
version: '2.0'
title: 'Перша світова війна: Брат проти брата'
subtitle: 'World War I: Brother Against Brother'
focus: history
pedagogy: CBI
phase: HIST.9 [WWI & Revolution]
word_target: 5000
objectives:
- Учень може описати участь українців у Першій світовій війні
- Учень може пояснити трагедію розділеного народу
- Учень може проаналізувати історію Легіону УСС
- Учень може оцінити вплив війни на національний рух
content_outline:
- section: 'Вступ: Розділений народ'
  points:
  - '1914: початок катастрофи — 1 серпня 1914 року як початок глобального конфлікту, що перетворив українські землі на головний
    театр бойових дій Східного фронту'
  - 'Українці в двох арміях — загальна статистика: понад 4.5 млн українців (4 млн у російській, 250-500 тис. у австро-угорській
    арміях); cultural hook: [!context] карта фронту через серце України'
  - Чому «брат проти брата» — річка Збруч як кордон не між державами, а між розділеними частинами одного народу
  words: 850
- section: Українці в російській армії
  points:
  - Мобілізація Наддніпрянщини — кожен 3-4 солдат Південно-Західного фронту був українцем
  - 'Масштаб участі: мільйони — 18% населення імперії дали до 30% солдатів; history bite: [!history-bite] статистика участі'
  - 'Галицький фронт: трагедія — українці-наддніпрянці змушені руйнувати артилерією українські міста (Львів, Тернопіль)'
  - Ставлення імперії до українців — недовіра до «мазепинців», репресії в окупованій Галичині (Генерал-губернаторство Бобринського,
    висилка Грушевського)
  words: 850
- section: Українці в австро-угорській армії
  points:
  - 'Галичина та Буковина — феномен добровольчого руху: 28 тисяч бажаючих, з яких відібрали лише 2.5 тисячі «цвіту нації»
    (інтелігенція, пластуни)'
  - 'Українські Січові Стрільці (УСС) — створені 6 серпня 1914 року, перша національна військова формація з 1709 року; myth
    buster: [!myth-buster] не «австрійські найманці», а «зародки національної армії»'
  - Битва під Маківкою — квітень-травень 1915 року, героїчна оборона проти російських військ; згадати також трагедію на горі
    Лисоня (вересень 1916)
  - Культура та ідеологія УСС — «армія, що співає», оркестр УСС, читання книг в окопах
  - Вплив на майбутню незалежність — формування кадрового резерву для майбутньої Галицької Армії
  words: 850
- section: Первинні джерела
  points:
  - Спогади січових стрільців — цитати С. Ріпецького або невідомих стрільців про бої на Лисоні
  - 'Стрілецькі пісні — «Ой у лузі червона калина» як символ епохи; cultural hook: [!culture]'
  - 'Фронтові листи — свідчення про «братання» та усвідомлення трагедії війни; include quote: [!quote] лист про зустріч з
    українцем по той бік фронту'
  words: 850
- section: Деколонізаційний погляд
  points:
  - 'Імперська війна — український погляд — війна не як «тріумф зброї», а як гуманітарна катастрофа українців; decolonization
    hook: [!decolonization]'
  - Чому війна прискорила національний рух — трансформація українців з пасивного «населення» в активних суб'єктів історії
    зі зброєю в руках
  - Крах імперій як можливість — виснаження Росії та Австро-Угорщини відкрило «вікно можливостей» для державотворення
  words: 850
- section: 'Підсумок: До революції'
  points:
  - Наслідки війни для України — ~1.5 млн загиблих та померлих, руїна, біженці
  - Від війни до революції 1917 — досвід 1914-1916 років як фундамент для подій 1917 року
  - Спадщина УСС — героїчний міф, що надихав наступні покоління борців за незалежність
  words: 750
vocabulary_hints:
  required:
  - війна (war) — Перша світова війна (WWI), громадянська війна (civil war), окопна війна (trench warfare)
  - армія (army) — служити в армії (serve in the army), регулярна армія (regular army)
  - фронт (front) — Східний фронт (Eastern Front), лінія фронту (front line), піти на фронт (go to the front)
  - мобілізація (mobilization) — загальна мобілізація (general mobilization), уникнути мобілізації (avoid mobilization)
  - січові стрільці (Sich Riflemen) — Легіон Українських Січових Стрільців (Legion of USS), усуси (colloquial for USS members)
  - битва (battle) — кривава битва (bloody battle), програти битву (lose a battle)
  - імперія (empire) — Російська імперія (Russian Empire), Австро-Угорська імперія (Austro-Hungarian Empire), розпад імперії
    (collapse of the empire)
  - крах (collapse) — крах імперій (collapse of empires), економічний крах (economic collapse)
  recommended:
  - окоп (trench) — сидіти в окопах (sit in trenches), окопна правда (trench truth)
  - артилерія (artillery) — важка артилерія (heavy artillery), артилерійський обстріл (artillery shelling)
  - наступ (offensive) — Брусиловський прорив (Brusilov Offensive), перейти в наступ (go on the offensive)
  - відступ (retreat) — тактичний відступ (tactical retreat), хаотичний відступ (chaotic retreat)
  - полон (captivity) — потрапити в полон (be taken prisoner/captive), військовополонений (prisoner of war)
  - легіон (legion) — формування легіону (formation of the legion), добровольчий легіон (volunteer legion)
activity_hints:
- type: reading
  focus: Спогади січових стрільців
  source: Архівні матеріали
  items: 4
- type: essay-response
  focus: Чому Перша світова війна стала каталізатором українського національного руху?
connects_to:
- hist-89 (Революція 1917)
- hist-91 (Центральна Рада)
prerequisites:
- hist-87 (Грушевський)
persona:
  voice: Senior Professor of History
  role: Sich Rifleman
grammar:
- Минулий час у воєнному наративі
- Військова лексика
- Пасивні конструкції
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Перша світова війна: Брат проти брата** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Перша світова війна: Брат проти брата

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Перша світова війна: Брат проти брата"
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
