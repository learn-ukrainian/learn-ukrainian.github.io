# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-080
level: HIST
sequence: 80
slug: kyrylo-mefodiivtsi
version: '2.0'
title: Кирило-Мефодіївське братство
subtitle: The Cyril and Methodius Brotherhood
focus: history
pedagogy: CBI
phase: HIST.8 [Imperial Era]
word_target: 5000
objectives:
- Учень може описати цілі та програму Кирило-Мефодіївського братства
- Учень може пояснити роль Шевченка, Костомарова та Куліша
- Учень може проаналізувати «Книги буття українського народу»
- Учень може оцінити значення братства для національного руху
content_outline:
- section: 'Вступ: Таємне товариство'
  points:
  - '1845-1847: два роки, що змінили історію — грудень 1845 – березень 1847 (всього 14 місяців існування); контекст: Київ
    як провінційне місто, що стає інтелектуальним центром'
  - Київ як центр українського відродження — Університет Св. Володимира як інтелектуальний хаб; вплив європейського романтизму
    та ідей національного відродження
  - 'Чому таємне? Умови для діяльності — жорстка цензура, поліцейський нагляд, збори на квартирах (зокрема у М. Гулака) —
    [!history-bite]: 12 членів налякали Імперію так, що розслідуванням керував особисто цар Микола I'
  words: 850
- section: Засновники та учасники
  points:
  - 'Микола Костомаров: історик та ідеолог — «мозок» організації, автор «Книг буття»; арештований за кілька днів до весілля
    з Аліною Крагельською (вони одружилися лише через 28 років) — [!biography]'
  - 'Пантелеймон Куліш: письменник та просвітитель — «аристократ духу», більш помірковані погляди; майбутній автор «Чорної
    ради»'
  - 'Тарас Шевченко: поет та пророк — «голос» і «душа», вступив у квітні 1846, його поезія («Сон», «Кавказ») стала каталізатором
    радикалізації'
  - Інші члени братства — Микола Гулак (юрист, найрадикальніший після Шевченка, відмовився давати свідчення); Василь Білозерський
  words: 850
- section: Ідеологія та програма
  points:
  - '«Книги буття українського народу» — структура: Створення світу -> гріхопадіння (монархія) -> воскресіння України; біблійний
    стиль, наслідування А. Міцкевича'
  - Панславізм vs. українська ідентичність — [!context] «Весна народів» 1848; конфедерація рівних республік (як США), де Росія
    — лише одна з частин, а Україна — центр (Київ)
  - Федерація слов'янських народів — Україна, Польща, Росія, Чехія, Сербія; столиця федерації в Києві, скасування царату
  - Скасування кріпацтва та рівність — ліквідація станів, соціальна справедливість, загальна освіта для всіх верств
  - Просвітницька місія — християнська мораль як основа політики; ідеалізація Запорозької Січі як демократичного взірця
  words: 850
- section: Первинні джерела
  points:
  - 'Фрагменти «Книг буття» — include quote: «І встане Україна із своєї могили, і знову озветься до всіх братів своїх слов’ян...»
    — [!quote]'
  - Вірші Шевченка того періоду — «Сон», «Кавказ», «І мертвим, і живим...» («В своїй хаті своя й правда, і сила, і воля»)
    як неофіційна програма
  - Поліцейські звіти та протоколи — донос студента Олексія Петрова (лютий 1847); матеріали ІІІ відділення Власної Його Імператорської
    Величності канцелярії
  words: 850
- section: Деколонізаційний погляд
  points:
  - 'Імперський наратив: «українофільство» як загроза — [!myth-buster]: міф про «безневинних мрійників» vs реальна загроза
    ідеології «Православіє, Самодержавіє, Народність»'
  - 'Реальність: мирний культурний рух — перше політичне формулювання України як окремої нації з власною історією та місією'
  - Чому імперія так боялася братства — страх перед республіканізмом; «Книги буття» чітко відокремлюють українців (демократів)
    від росіян (схильних до рабства)
  words: 850
- section: 'Підсумок: Розгром та спадщина'
  points:
  - Арешти та покарання — березень-квітень 1847; Гулак (3 роки у Шліссельбурзі), Костомаров (Саратов), Куліш (Тула)
  - Заслання Шевченка — солдати з забороною писати й малювати; особиста помста царя Миколи I за поему «Сон» — [!legacy]
  - Вплив на наступні покоління — перехід від культурництва до політики; ідеї лягли в основу діяльності «Громад» 1860-90-х
    років
  words: 750
vocabulary_hints:
  required:
  - братство (brotherhood) — Кирило-Мефодіївське братство, члени братства
  - таємне товариство (secret society) — діяти як таємне товариство, розкриття товариства
  - ідеологія (ideology) — політична ідеологія, формування ідеології братчиків
  - 'панславізм (Pan-Slavism) — ідеї панславізму, слов''янська єдність; learner error: плутати український демократичний панславізм
    з російським імперським'
  - федерація (federation) — слов'янська федерація, республіканська федерація, конфедерація
  - просвітництво (enlightenment) — ідеї просвітництва, поширення освіти
  - арешт (arrest) — масові арешти, уникнути арешту, арешт напередодні весілля
  - заслання (exile) — відправити на заслання, роки заслання, солдатчина
  recommended:
  - маніфест (manifesto) — програмний маніфест, «Книги буття» як маніфест
  - рівність (equality) — соціальна рівність, рівність народів, скасування станів
  - свобода (freedom) — політична свобода, свобода слова, особиста воля
  - донос (denunciation) — написати донос, стати жертвою доносу студента Петрова
  - репресії (repressions) — імперські репресії, жорстокі вироки
  - пророк (prophet) — національний пророк (Шевченко), пророчі слова
  - самодержавство (autocracy) — повалення самодержавства, критика царату
  - жандарм (gendarme) — ІІІ відділення, слідство жандармів
activity_hints:
- type: reading
  focus: Фрагменти «Книг буття українського народу»
  source: Архівні документи
  items: 4
- type: critical-analysis
  focus: 'Спростування міфів: Міфи про братство'
  items: 5
- type: essay-response
  focus: Чому імперія так жорстоко покарала мирних просвітників?
connects_to:
- 'hist-81 (Шевченко: Пробудження)'
- hist-83 (Громадівський рух)
prerequisites:
- hist-79 (Кріпацтво на Півдні)
persona:
  voice: Senior Professor of History
  role: Bratstvo Conspirator
grammar:
- Минулий час в історичному наративі
- Політична та філософська лексика
- Непряма мова для передачі ідей
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Кирило-Мефодіївське братство** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Кирило-Мефодіївське братство

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Кирило-Мефодіївське братство"
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
