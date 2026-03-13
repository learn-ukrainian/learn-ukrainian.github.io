# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-118
level: HIST
sequence: 118
slug: diaspora
version: '2.0'
title: 'Діаспора: Ковчег держави'
subtitle: 'The Diaspora: Ark of the Nation'
focus: history
pedagogy: CBI
phase: HIST.11 [Post-War Soviet Ukraine]
word_target: 5000
objectives:
- Учень може описати хвилі української еміграції XX століття
- Учень може оцінити роль діаспори у збереженні української ідентичності
- Учень може проаналізувати внесок діаспори в боротьбу за незалежність
- Учень може пояснити зв'язок діаспори із сучасною Україною
content_outline:
- section: 'Вступ: Чому українці покидали батьківщину'
  points:
  - 'Три великі хвилі еміграції — економічна (земля), політична (поразка), біженська (війна) — відмінність української діаспори:
    сильна політична складова («альтернативна Україна»)'
  - Політичні та економічні причини — «ми виїхали, щоб Україна жила» (політична місія) — місія збереження легітимності влади
    та культури
  - Збереження нації поза Україною — [!decolonization] Радянська пропаганда називала емігрантів «зрадниками», тоді як вони
    були «хранителями» державності (Ковчег)
  words: 700
- section: Перша хвиля (1880-1914)
  points:
  - Економічна еміграція до Америки та Канади — [!history-bite] Іван Пилипів та Василь Єлиняк (1891); везли зерно, змінюючи
    аграрну карту Канади
  - Формування українських громад — «люди ангельські, всі дуже інтелігентні» (Павлина Геникова, 1898) — роль греко-католицьких
    священиків як лідерів
  - Церква як центр громадського життя — будівництво церков та читалень «Просвіти» — «ми будували Україну на чужині»
  words: 700
- section: Друга хвиля (1920-1939)
  points:
  - Політична еміграція після поразки УНР — «інтелектуальна еміграція» військових та еліти — центри у Варшаві, Празі, Парижі
  - Уряд УНР в екзилі — Тарнів (Польща), Париж; легітимний спадкоємець державності (1917-1992) — збереження державних атрибутів
  - Наукові та культурні інституції — [!context] Українська Господарська Академія (Подєбради), «український Оксфорд» у Празі
    — розвиток науки без радянської цензури
  words: 700
- section: Третя хвиля (ДіПі, 1945-1950)
  points:
  - Переміщені особи після Другої світової — близько 200 тисяч українців; відмова від «радянської родіни» (страх репресій)
  - Табори ДіПі в Німеччині та Австрії — [!myth-buster] «держави в мініатюрі» з театрами, школами та газетами (МУР — Мистецький
    український рух)
  - 'Розселення у світі: США, Канада, Австралія — масовий переїзд після закриття таборів у 1950-х — формування потужних громад'
  - Створення нових інституцій — Світовий Конгрес Вільних Українців (СКВУ, 1967) — консолідація політичних сил
  words: 700
- section: Первинні джерела
  points:
  - Спогади емігрантів — Іван Багряний («Тигролови»), Улас Самчук («Планета Ді-Пі») — фіксація досвіду таборового життя
  - Документи українських організацій — акт передачі клейнодів УНР президенту Кравчуку (22 серпня 1992) — символ спадкоємності
  - Діаспорна преса — газети «Свобода», «Українська думка» — хроніка життя громади
  words: 700
- section: Внесок діаспори
  points:
  - Збереження мови та культури — Енциклопедія українознавства (ЕУ), пам'ятники Шевченку (Вашингтон) — фінансова підтримка
    культури
  - Лобіювання визнання Голодомору — Комісія Мейса; Тиждень поневолених народів (Captive Nations Week) у США
  - Підтримка незалежності 1991 року — [!quote] Микола Плав'юк про спадкоємність УНР, а не УРСР — тиск на західні уряди
  - Допомога у війні 2022 року — глобальна мережа підтримки, лобізм зброї та санкцій — діаспора як «голос України» у світі
  words: 700
- section: 'Підсумок: Діаспора сьогодні'
  points:
  - Четверта хвиля (після 2022) — статус «тимчасового захисту» vs класична еміграція — надія на повернення
  - Зв'язок з Україною в цифрову епоху — [!reflection] зміна поняття ностальгії та асиміляції через інтернет — миттєвий зв'язок
  - Майбутнє діаспори — глобальне українство як мережа, а не географічне розпорошення — концепція «Global Ukraine»
  words: 800
vocabulary_hints:
  required:
  - 'діаспора (diaspora) — «Ковчег держави», західна діаспора; collocation: українська діаспора'
  - 'еміграція (emigration) — хвилі еміграції (waves of emigration), трудова/політична еміграція; context: вимушена еміграція'
  - 'імміграція (immigration) — країна поселення (host country); context: імміграційні квоти'
  - 'громада (community) — церковна громада, українська громада; collocation: згуртування громади'
  - 'біженець (refugee) — статус біженця (refugee status), політичний біженець; context: воєнні біженці'
  - 'переміщена особа (displaced person) — табори ДіПі (DP camps), «скитальці»; context: таборове життя'
  - 'екзиль (exile) — уряд в екзилі (government in exile), література в екзилі; context: жити в екзилі'
  - 'асиміляція (assimilation) — збереження ідентичності (preserving identity), загроза асиміляції; context: мовна асиміляція'
  recommended:
  - 'репатріація (repatriation) — примусова репатріація (forced repatriation) до СРСР; context: уникнути репатріації'
  - 'лобіювання (lobbying) — політичний лобізм, українське лобі; context: лобіювання інтересів'
  - 'культурна спадщина (cultural heritage) — збереження спадщини; context: передача спадщини'
  - 'ідентичність (identity) — національна ідентичність; context: втрата ідентичності'
  - 'інтеграція (integration) — інтеграція в суспільство; context: успішна інтеграція'
  - 'двомовність (bilingualism) — українські суботні школи; context: збереження мови'
activity_hints:
- type: reading
  focus: Спогади українських емігрантів
  source: Усна історія
  items: 4
- type: essay-response
  focus: Яку роль відіграла діаспора у збереженні української ідентичності?
connects_to:
- hist-119 (Шлях до незалежності)
- 'hist-102 (Голодомор: Пам''ять)'
prerequisites:
- hist-117 (Чорнобиль)
persona:
  voice: Senior Professor of History
  role: Cultural Archivist
grammar:
- Минулий час в історичному наративі
- Теперішній час для опису сучасного стану
- Географічні назви та їх відмінювання
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Діаспора: Ковчег держави** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Діаспора: Ковчег держави

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Діаспора: Ковчег держави"
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
