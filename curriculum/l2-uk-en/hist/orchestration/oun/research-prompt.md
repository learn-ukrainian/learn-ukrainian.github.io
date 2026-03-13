# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-100
level: HIST
sequence: 100
slug: oun
version: '2.0'
title: 'ОУН: Формування'
subtitle: 'OUN: The Formation of Ukrainian Nationalism'
focus: history
pedagogy: CBI
phase: HIST.10 [Soviet Terror]
word_target: 5000
objectives:
- Учень може описати створення та ідеологію ОУН
- Учень може пояснити історичний контекст українського націоналізму
- Учень може проаналізувати діяльність ОУН у міжвоєнний період
- Учень може оцінити суперечливу спадщину організації
content_outline:
- section: 'Вступ: Народження націоналізму'
  points:
  - '1929: створення ОУН у Відні — 28 січня – 3 лютого, об''єднання УВО та молодіжних груп; engagement hook: [!context] failure
    of 1917-1921 left Ukrainians stateless and divided'
  - 'Контекст: поразка визвольних змагань — травма втрати державності, розчарування в демократичних методах і Лізі Націй (яка
    легітимізувала окупацію Галичини)'
  - Чому радикальний націоналізм? — відповідь на окупацію та репресії, потреба в безкомпромісній силі, що не йде на угоди
    з окупантами
  words: 850
- section: Витоки та ідеологія
  points:
  - 'УВО: попередник ОУН — створена 1920 Євгеном Коновальцем як військове ядро, перехід до політичної боротьби'
  - 'Євген Коновалець: засновник — колишній командир Січових Стрільців, авторитет, що об''єднав ветеранів і молодь; include
    quote: «Самостійність і державність нація зможе осягнути революційним шляхом...»'
  - Ідеологія інтегрального націоналізму — «Нація понад усе», волюнтаризм (воля до життя), «творче насильство», відмова від
    соціалізму та лібералізму
  - 'Дмитро Донцов та його вплив — праця «Націоналізм» (1926) як «біблія» молоді; engagement hook: [!quote] Донцов про безкомпромісову
    боротьбу з Росією'
  words: 850
- section: Діяльність у 1930-х
  points:
  - Підпільна боротьба в Галичині — контекст польської політики «пацифікації» (1930) та радикалізація руху у відповідь на
    репресії
  - 'Терористичні акції: полеміка — атентати як акти відплати: Майлов (1933) за Голодомор, Пєрацький (1934) за Пацифікацію;
    engagement hook: [!myth-buster] not blind terror but targeted revenge'
  - Вбивство Коновальця 1938 — Роттердам, агент НКВС Павло Судоплатов, коробка цукерок з вибухівкою — «подарунок з України»
  - 'Розкол: ОУН-М та ОУН-Б — 1940 рік, конфлікт поколінь і тактик: революціонери «Краю» (Бандера) vs помірковані емігранти
    «Пенсії» (Мельник)'
  - 'Степан Бандера та Андрій Мельник — Варшавський (1935) та Львівський (1936) процеси зробили Бандеру символом незламності;
    engagement hook: [!history-bite] refusal to speak Polish in court («Український суд, на українській землі»)'
  words: 850
- section: Первинні джерела
  points:
  - 'Програмові документи ОУН — Декалог (1929), 12 прикмет, 44 правила життя; мета — УССД (Українська Самостійна Соборна Держава);
    engagement hook: [!source] Декалог як моральний кодекс'
  - Листи та спогади учасників — листування Коновальця, спогади про підпілля та конспірацію
  - Польські та радянські звіти — погляд окупаційної влади на «бандитизм» та «тероризм»
  words: 850
- section: Деколонізаційний погляд
  points:
  - 'Радянський та польський наративи: «фашисти» — таврування борців за незалежність, міф про «німецьких маріонеток» та «банду
    терористів»; engagement hook: [!decolonization] soviet propaganda vs reality'
  - 'Контекст: боротьба проти двох імперій — польського шовінізму та радянського тоталітаризму (Голодомор, репресії)'
  - 'Сучасні дискусії та переосмислення — ОУН як суб''єктна гра (agency) в умовах бездержавності; contested terms: тероризм
    vs національно-визвольна боротьба'
  words: 850
- section: 'Підсумок: До Другої світової'
  points:
  - ОУН напередодні війни — Карпатська Україна (1939) як перший бойовий досвід (Карпатська Січ)
  - Надії на німецьку підтримку — тактика «ворог мого ворога» проти СРСР і Польщі, частково ілюзорні сподівання
  - 'Трагічні наслідки — розкол 1940 року ослабив рух перед великою війною, але показав наявність різних візій боротьби; engagement
    hook: [!reflection] tragedy of the 1940 split'
  words: 750
vocabulary_hints:
  required:
  - 'націоналізм (nationalism) — інтегральний, радикальний, український; collocations: ідеологія націоналізму, дух націоналізму'
  - підпілля (underground) — піти в підпілля, діяльність підпілля, керівник підпілля
  - ідеологія (ideology) — українського націоналізму, вплив Донцова, формування ідеології
  - організація (organization) — ОУН (Організація Українських Націоналістів), розбудова організації, член організації
  - визвольний рух (liberation movement) — національно-визвольні змагання, учасник визвольного руху
  - 'терор (terror) — індивідуальний терор (як тактика), червоний терор (більшовицький); learner error: terror vs terrorism
    vs political assassination'
  - розкол (split) — розкол в ОУН, поділ на фракції, трагічний розкол
  - провідник (leader) — Провідник ОУН, Євген Коновалець, Степан Бандера, Провід українських націоналістів (ПУН)
  recommended:
  - радикальний (radical) — радикалізація молоді, радикальні методи боротьби
  - інтегральний (integral) — інтегральний націоналізм (ідеологія Донцова)
  - атентат (assassination) — політичне вбивство, акт відплати (not just 'terror'), виконавець атентату
  - конспірація (conspiracy) — правила конспірації, глибока конспірація, жити в конспірації
  - еміграція (emigration) — політична еміграція, провід в еміграції
  - маніфест (manifesto) — ідеологічний маніфест, програмові документи
  - пацифікація (pacification) — польська каральна акція, політика пацифікації, відповідь на пацифікацію
activity_hints:
- type: reading
  focus: Програмові документи ОУН
  source: Архівні матеріали
  items: 4
- type: critical-analysis
  focus: 'Спростування міфів: Міфи про ОУН'
  items: 5
- type: essay-response
  focus: Як історичний контекст вплинув на радикалізацію українського націоналізму?
connects_to:
- hist-104 (Карпатська Україна)
- hist-107 (УПА)
prerequisites:
- 'hist-102 (Голодомор: пам''ять)'
persona:
  voice: Senior Professor of History
  role: Political Analyst
grammar:
- Минулий час в історичному наративі
- Політична та ідеологічна лексика
- Складнопідрядні речення
register: публіцистичний

```

---

## PART 1: Deep Research

Research **ОУН: Формування** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: ОУН: Формування

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "ОУН: Формування"
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
