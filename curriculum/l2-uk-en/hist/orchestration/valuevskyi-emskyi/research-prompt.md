# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-082
level: HIST
sequence: 82
slug: valuevskyi-emskyi
version: '2.0'
title: Валуєвський циркуляр та Емський указ
subtitle: The Valuev Circular and Ems Decree
focus: history
pedagogy: CBI
phase: HIST.8 [Imperial Era]
word_target: 5000
objectives:
- Учень може описати заборони української мови в XIX столітті
- Учень може пояснити зміст Валуєвського циркуляра та Емського указу
- Учень може проаналізувати наслідки мовних заборон
- Учень може оцінити ці заборони як форму культурного геноциду
content_outline:
- section: 'Вступ: Мова як загроза імперії'
  points:
  - 'Чому імперія боялась української мови — страх «польської інтриги» та сепаратизму як загрози єдності; cultural hook: страх
    перед перекладом Євангелія Пилипом Морачевським [!context]'
  - 'Контекст: польське повстання 1863 — Січневе повстання (січень 1863) як безпосередній каталізатор репресій проти українства'
  - 'Політика «немає окремої мови» — імперська логіка, що українці є частиною російського народу; learner error: плутати «руський»
    (стародавній) і «російський» (імперський)'
  words: 850
- section: Валуєвський циркуляр (1863)
  points:
  - Міністр Валуєв — Петро Валуєв, автор таємного циркуляра від 18 (30) липня 1863 року
  - «Малоруської мови не було, нема і бути не може» — ключова цитата, що офіційно заперечує існування мови [!quote]
  - 'Заборона друку — наукових, релігійних і навчальних книг; content note: художня література («красне письменство») формально
    дозволялась, але цензурувалась'
  - 'Наслідки для української літератури — зупинка розвитку освіти, науки та церковного життя українською мовою; мета: звести
    мову до «домашнього вжитку»'
  words: 850
- section: Емський указ (1876)
  points:
  - 'Посилення репресій — указ підписаний Олександром II 18 (30) травня 1876 року у німецькому місті Бад-Емс; history-bite:
    підписано під час відпочинку царя на курорті [!history-bite]'
  - 'Зміст указу: заборона театру, пісень, освіти — тотальна заборона сценічних вистав, публічних читань та текстів до нот'
  - Заборона ввозу книг — повна блокада літератури з-за кордону (удар по галицьких виданнях і роботі Драгоманова)
  - Наслідки для культури — вимога використовувати російський правопис («ярижку») для історичних пам'яток, заборона «кулішівки»
  - 'Спротив: Галичина як центр — «Галицький П''ємонт»: переміщення видавничої діяльності до Львова та Женеви (Драгоманов)'
  words: 850
- section: Первинні джерела
  points:
  - 'Текст циркуляра — аналіз оригіналу: «пропуск же книг... приостановить» [!source]'
  - 'Текст указу — аналіз оригіналу: «Не допускать ввоза... воспретить сценические представления» [!source]'
  - Реакція українських діячів — діяльність Михайла Юзефовича («Юзефович-Іскаріот») як ініціатора репресій та його меморандум
    1875 року
  words: 850
- section: Деколонізаційний погляд
  points:
  - 'Імперський наратив: «один народ» — міф про українську мову як «зіпсоване наріччя» або «польську інтригу» [!myth-buster]'
  - 'Реальність: лінгвоцид — свідома державна політика знищення мови для унеможливлення націєтворення; contested term: «малоруське
    наріччя» vs українська мова'
  - Сучасні паралелі — тяглість російської політики знищення української ідентичності (від Валуєва до сучасної війни)
  words: 850
- section: 'Підсумок: Наслідки заборон'
  points:
  - Скасування (1905) — Маніфест громадянських свобод 17 жовтня 1905 року фактично зняв заборони
  - Довготривалі наслідки — формування комплексу меншовартості («мужицька мова») та гальмування освіти
  - 'Мова як поле битви — радикалізація українського руху: перехід від культурництва до політичних вимог; cultural hook: Львів
    як центр відродження [!culture]'
  words: 750
vocabulary_hints:
  required:
  - циркуляр (circular) — таємний Валуєвський циркуляр, видати циркуляр
  - указ (decree) — Емський указ Олександра II, підписати указ
  - заборона (ban) — тотальна заборона друку, мовні заборони, заборона ввозу
  - мова (language) — українська мова, «малоруське наріччя» (імперський термін), окрема мова
  - друк (print) — заборона друку, друкувати книги, друковане слово
  - цензура (censorship) — жорстка цензура, цензурні обмеження, заборона сценічних вистав
  - імперія (empire) — Російська імперія, політика імперії, імперська логіка
  - репресії (repressions) — посилення репресій, політичні репресії, лінгвоцид
  recommended:
  - театр (theater) — заборона театру, сценічні вистави, український театр
  - освіта (education) — народна освіта, підручники, навчальні книги
  - література (literature) — художня література («красне письменство»), наукова література
  - культура (culture) — українська культура, культурний розвиток, культурний спротив
  - лінгвоцид (linguicide) — акт лінгвоциду, свідома політика лінгвоциду
  - спротив (resistance) — культурний спротив, національний рух, «Галицький П'ємонт»
activity_hints:
- type: reading
  focus: Тексти Валуєвського циркуляра та Емського указу
  source: Архівні документи
  items: 4
- type: critical-analysis
  focus: 'Верифікація фактів: Факти про мовні заборони'
  items: 5
- type: essay-response
  focus: Чому заборони української мови можна вважати культурним геноцидом?
connects_to:
- hist-84 (Михайло Драгоманов)
- hist-84 (Громади)
prerequisites:
- hist-81 (Шевченко)
persona:
  voice: Senior Professor of History
  role: Secret Publisher
grammar:
- Минулий час в історичному наративі
- Юридична та офіційна лексика
- Пасивні конструкції
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Валуєвський циркуляр та Емський указ** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Валуєвський циркуляр та Емський указ

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Валуєвський циркуляр та Емський указ"
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
