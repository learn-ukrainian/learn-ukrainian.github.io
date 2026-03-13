# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-093
level: HIST
sequence: 93
slug: dyrektoriia
version: '2.0'
title: Директорія УНР
subtitle: The Directory of the Ukrainian People's Republic 1918-1920
focus: history
pedagogy: CBI
phase: HIST.9 [WWI & Revolution]
word_target: 5000
objectives:
- Учень може описати створення та діяльність Директорії УНР
- Учень може пояснити політичні конфлікти всередині Директорії
- Учень може проаналізувати причини поразки Директорії
- Учень може оцінити роль Симона Петлюри та Володимира Винниченка
content_outline:
- section: 'Вступ: Падіння Гетьманату'
  points:
  - 'Контекст: кінець німецької окупації — листопад 1918, втрата зовнішньої підтримки Скоропадського після поразки Німеччини'
  - Повстання проти Скоропадського — центр у Білій Церкві, Січові Стрільці як рушійна сила; [!context] об'єднання полярних
    сил (соціалістів і націоналістів) проти Гетьмана
  - Створення Директорії (листопад 1918) — таємне засідання 13-14 листопада, перемога під Мотовилівкою відкриває шлях на Київ
  words: 850
- section: Структура та лідери
  points:
  - П'ятеро членів Директорії — Винниченко, Петлюра, Швець, Андрієвський, Макаренко (колективне керівництво)
  - 'Володимир Винниченко: соціаліст — доктринер, прагнення «радянської платформи без більшовиків»; [!history-bite] «Винниченко
    пише, Петлюра воює»'
  - 'Симон Петлюра: військовий лідер — прагматик-державник, розуміння неминучості війни з Москвою'
  - Внутрішні конфлікти та відставка Винниченка — лютий 1919, провал спроб домовитися з більшовиками, перехід влади до Петлюри
  words: 850
- section: Боротьба на кілька фронтів
  points:
  - Війна з більшовиками — оголошення війни 16 січня 1919, втрата Києва в лютому, наступ Червоної армії з півночі та сходу
  - Конфлікт із Західноукраїнською Народною Республікою — Акт Злуки (22.01.1919) як символічний тріумф, але складність військової
    співпраці (Петрушевич vs Петлюра)
  - Денікін та білогвардійці — наступ з півдня за «Єдину неділиму Росію», «Київська катастрофа» (серпень 1919)
  - Польські інтервенти — Варшавський договір як вимушений крок відчаю для порятунку державності
  - Зимовий похід армії УНР — 6 грудня 1919 – 6 травня 1920, перехід до партизанської тактики; [!history-bite] «Трикутник
    смерті» (більшовики, білі, поляки + тиф)
  words: 850
- section: Первинні джерела
  points:
  - Універсали Директорії — Декларація 26 грудня 1918; [!quote] про права лише для «трудових класів» (лівий популізм)
  - Спогади Винниченка — «Відродження нації», спроба виправдання та звинувачення опонентів
  - Військові документи — Накази Петлюри про покарання за погроми (напр. Наказ № 131)
  words: 850
- section: Деколонізаційний погляд
  points:
  - 'Міф: «Петлюрівщина» як радянський термін — синонім бандитизму та анархії в імперському наративі'
  - 'Реальність: Боротьба за незалежність — легітимний уряд, визнаний де-факто; [!decolonization] термін «Громадянська війна»
    є фальшивим, це була російсько-українська війна'
  - Погроми та їх контекст — [!myth-buster] вбивство Петлюри Шварцбардом як спецоперація ОДПУ, реальні винуватці погромів
    (денікінці, будьоннівці, отамани)
  words: 850
- section: 'Підсумок: Спадщина Директорії'
  points:
  - Причини поразки — внутрішні чвари, відсутність сильної армії, байдужість Антанти, переважаючі сили ворогів
  - Еміграція та уряд в екзилі — збереження юридичної спадкоємності влади до 1992 року (передача клейнодів Кравчуку)
  - 'Директорія в національній пам''яті — урок: демократія без сильної армії неможлива'
  words: 750
vocabulary_hints:
  required:
  - директорія (directorate) — тимчасовий революційний орган, згодом верховна влада
  - універсал (universal/decree) — законодавчий акт, декларація
  - 'отаман (otaman/chieftain) — військовий ватажок; learner error: плутати з козацькими гетьманами (тут інший контекст)'
  - повстання (uprising) — протигетьманське повстання
  - інтервенція (intervention) — більшовицька/польська військова інтервенція
  - еміграція (emigration) — політична еміграція уряду УНР
  - уряд (government) — уряд в екзилі (government in exile)
  - армія (army) — Дієва армія УНР
  recommended:
  - соціалізм (socialism) — домінування лівих партій у Директорії
  - республіка (republic) — відновлення УНР
  - коаліція (coalition) — вимушені та тимчасові союзи
  - фронт (front) — боротьба на кілька фронтів
  - відступ (retreat) — стратегічний відступ, Зимовий похід
  - перемир'я (armistice) — спроби перемир'я з більшовиками
  - зимовий похід (winter campaign) — Перший Зимовий похід (героїчна сторінка)
  - трикутник смерті (triangle of death) — стратегічна пастка 1919 року
  - акт злуки (act of unification) — об'єднання УНР і ЗУНР
activity_hints:
- type: reading
  focus: Універсали Директорії
  source: Архівні документи
  items: 4
- type: essay-response
  focus: Які внутрішні та зовнішні причини призвели до поразки Директорії?
connects_to:
- hist-94 (Симон Петлюра)
- hist-95 (Більшовицько-українська війна)
prerequisites:
- hist-91 (Скоропадський)
- hist-92 (ЗУНР)
persona:
  voice: Senior Professor of History
  role: Diplomatic Envoy
grammar:
- Минулий час у політичному наративі
- Пасивні конструкції для опису подій
- Офіційна лексика
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Директорія УНР** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Директорія УНР

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Директорія УНР"
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
