# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-112
level: HIST
sequence: 112
slug: krym-1954
version: '2.0'
title: 'Крим 1954: Передача УРСР'
subtitle: 'Crimea 1954: Transfer to Ukraine'
focus: history
pedagogy: CBI
phase: HIST.11 [Post-War Soviet Ukraine]
word_target: 5000
objectives:
- Учень може описати обставини передачі Криму 1954 року
- Учень може пояснити радянські та пострадянські інтерпретації
- Учень може проаналізувати юридичні аспекти передачі
- Учень може оцінити значення цієї події для сучасності
content_outline:
- section: 'Вступ: «Подарунок» чи рішення?'
  points:
  - '19 лютого 1954: дата передачі — Указ Президії Верховної Ради СРСР № 129/2; date: 19.02.1954'
  - 'Російський міф про «подарунок Хрущова» — спростування: рішення було колегіальним (Маленков, Ворошилов) та економічно
    вимушеним; hook: [!myth-buster]'
  - Чому це питання актуальне сьогодні — Путін використовує міф про «незаконність» для виправдання анексії 2014 року
  words: 850
- section: 'Контекст: Крим до 1954 року'
  points:
  - 'Депортація кримських татар 1944 року — 18-20 травня, виселення ~200 тис. корінного населення; hook: [!context]'
  - Крим як «спустошена земля» — економічна руїна, врожайність садів на рівні 1913 року, зернових — мізерні 3,9 ц/га, критичний
    брак води
  - 'Економічні зв''язки з Україною — територіальна близькість та залежність від материкових ресурсів; note: провал переселенців
    з РРФСР, які не вміли господарювати в горах'
  - Північно-Кримський канал — початок масштабного проєкту зрошення степу, реалізованого силами УРСР (запуск 1961, але планування
    пов'язане з передачею)
  words: 850
- section: 'Передача: як це відбулося'
  points:
  - 'Ініціатива та прийняття рішення — візит Хрущова у вересні 1953, скарги російських переселенців, терміновий виліт до Києва
    вмовляти українське керівництво (Кириченка); hook: [!history-bite]'
  - Указ Президії Верховної Ради СРСР — підписано 19.02.1954, затверджено законом 26.04.1954
  - 'Офіційне обґрунтування: економічна доцільність — цитата: «Враховуючи спільність економіки, територіальну близькість і
    тісні господарські й культурні зв''язки...»'
  - Процедура за радянським законодавством — повна відповідність Конституції СРСР 1936 року (згода РРФСР 5 лютого і УРСР 13
    лютого)
  - Реакція в УРСР та РРФСР — для України це був «хомут» і обов'язок відбудови, а не нагорода
  words: 850
- section: Первинні джерела
  points:
  - Текст указу 1954 року — аналіз офіційного формулювання без згадки про «300-річчя» Переяславської ради (згадувалося лише
    ритуально в інших документах)
  - 'Протоколи засідань — документи Президій РРФСР (5 лютого) та УРСР (13 лютого); hook: [!source]'
  - Радянська преса того часу — газета «Кримська правда» про «радість возз'єднання» та плани на «води Дніпра»
  words: 850
- section: Деколонізаційний погляд
  points:
  - 'Російська міфологія «подарунка» — деконструкція наративу про «волюнтаризм» та «п''яного Хрущова»; myth: «Крим — ісконно
    русская зємля»'
  - Юридична легітимність передачі — протидія сучасному російському правовому нігілізму та спробам скасувати акти заднім числом
  - 'Крим і кримські татари: забутий народ — передача відбулася без урахування думки киримли (спецпоселенців), але це не змінило
    їхній статус; hook: [!decolonization]'
  words: 850
- section: 'Підсумок: Від 1954 до 2014'
  points:
  - Крим у незалежній Україні — інфраструктурний розквіт, курорти, «Артек», побудовані за українські кошти
  - Автономна Республіка Крим — референдум 1 грудня 1991 (54% підтримки незалежності в Криму)
  - 'Російська анексія 2014: псевдоісторичні аргументи — ігнорування 60 років української праці та інвестицій; hook: [!culture]'
  words: 750
vocabulary_hints:
  required:
  - передача (transfer) — передача області, акт передачі, законність передачі
  - указ (decree) — підписати указ, згідно з указом, текст указу
  - президія (presidium) — Президія Верховної Ради, засідання президії
  - автономія (autonomy) — кримська автономія, статус автономії, відновити автономію
  - депортація (deportation) — наслідки депортації, сталінська депортація, жертви депортації
  - анексія (annexation) — незаконна анексія, спроба анексії, виправдання анексії
  - юридичний (legal) — юридична підстава, юридичний аспект, юридична сила
  - законодавство (legislation) — чинне законодавство, порушення законодавства, згідно із законодавством
  recommended:
  - доцільність (expediency) — економічна доцільність, політична доцільність
  - легітимність (legitimacy) — сумнівна легітимність, визнавати легітимність
  - референдум (referendum) — всеукраїнський референдум, результати референдуму, провести референдум
  - суверенітет (sovereignty) — державний суверенітет, повага до суверенітету
  - територія (territory) — територіальна цілісність, на території, прилегла територія
  - пропаганда (propaganda) — ворожа пропаганда, міфи пропаганди, жертва пропаганди
activity_hints:
- type: reading
  focus: Указ 1954 року про передачу Криму
  source: Архівні документи
  items: 4
- type: critical-analysis
  focus: 'Спростування міфів: Міфи про «подарунок» Криму'
  items: 5
- type: essay-response
  focus: Чому російська міфологія про «подарунок» Криму — це пропаганда?
connects_to:
- 'hist-115 (Кримські татари: повернення)'
- hist-131 (Крим 2014)
prerequisites:
- hist-113 (Десталінізація)
persona:
  voice: Senior Professor of History
  role: Hydrological Engineer
grammar:
- Минулий час в історичному наративі
- Юридична та політична лексика
- Непряма мова для передачі аргументів
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Крим 1954: Передача УРСР** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Крим 1954: Передача УРСР

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Крим 1954: Передача УРСР"
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
