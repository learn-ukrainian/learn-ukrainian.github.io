# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-063
level: HIST
sequence: 63
slug: ivan-mazepa-derzhavnyk
version: '2.0'
title: 'Іван Мазепа I: Державник'
subtitle: 'Ivan Mazepa I: The Statesman'
focus: history
pedagogy: CBI
phase: HIST.7 [Mazepa & End of Hetmanate]
word_target: 5000
objectives:
- Учень може описати шлях Івана Мазепи до гетьманства
- Учень може пояснити значення Коломацьких статей
- Учень може проаналізувати внутрішню політику Мазепи
- Учень може оцінити його як державного діяча
content_outline:
- section: 'Вступ: Найвідоміший гетьман'
  points:
  - Чому Мазепа — центральна постать української історії — 22 роки правління (найдовше в історії), пережив 4 королів, 3 султанів
    і 2 царів
  - Від анафеми до національного героя — трансформація образу від барокового панегірика до «проклятого» в церквах РІ
  - 'Три частини історії Мазепи — етапи: служба (до 1687), розбудова (1687-1708), повстання (1708-1709)'
  words: 700
- section: Шлях до влади
  points:
  - 'Походження та освіта — шляхтич з Київщини; освіта: Києво-Могилянська колегія, Варшавський єзуїтський колегіум, Європа
    (артилерія); [!context]'
  - Служба при різних гетьманах — дипломат Дорошенка (місія до Туреччини), перехід до Самойловича (вихователь дітей)
  - Інтриги та вибори 1687 року — роль Голіцина та козацької старшини у Коломацькому перевороті
  - 'Коломацькі статті: компроміс з Москвою — тиск Москви: заборона дипломатії, московські залоги в містах'
  words: 700
- section: Гетьман-будівничий (1687-1708)
  points:
  - Зміцнення гетьманської влади — стабілізація соціального устрою, підтримка старшини (але й захист посполитих)
  - 'Економічний розвиток — розвиток промисловості: селітра, гути, папірні'
  - 'Культурне меценатство: мазепинське бароко — [!culture] понад 40 церков (Братський, Микільський собори), Чернігівський
    колегіум'
  - Відносини з козацькою старшиною — формування нової еліти, вірної гетьману
  - Балансування між Москвою та автономією — участь у Азовських походах Петра І, возз'єднання Правобережжя (1704)
  words: 700
- section: Читання
  points:
  - Аналіз Коломацьких статей — [!quote] документ про обмеження прав Гетьманщини та заборону «голосів» проти єдності
  - Меценатство Мазепи — надання статусу академії Києво-Могилянському колегіуму (1701)
  words: 700
- section: Первинні джерела
  points:
  - Коломацькі статті — уривки про «з'єднання народів» та «неразорванное согласие»
  - Листування Мазепи — [!biography] листи до Мотрі Кочубеївни як доказ емоційної глибини
  - Свідчення сучасників — Дума «Всі покою щиро прагнуть» як політичний маніфест єдності
  words: 700
- section: Деколонізаційний погляд
  points:
  - 'Міф: «Зрадник» як російський наратив — [!myth-buster] анафема як політичний акт Петра І (знята у 2018)'
  - 'Реальність: Державник, який шукав найкращого для України — прагматик, що намагався зберегти автономію дипломатією'
  - Мазепа в українській та російській пам'яті — «зрада» vs «порушення васальної угоди сюзереном» (Жовквівська нарада 1706)
  words: 700
- section: 'Підсумок: Гетьман на роздоріжжі'
  points:
  - Досягнення державника — створення економічної та культурної бази для незалежності
  - 'Дилема: лояльність чи незалежність — [!reflection] вибір між клятвою царю (який її порушив) та порятунком Батьківщини
    («Україна гине»)'
  - До Полтави — перехід до союзу зі Швецією як вимушений крок
  words: 800
vocabulary_hints:
  required:
  - гетьман (hetman) — гетьманська булава, вибори гетьмана
  - державник (statesman) — мудрий державник, далекоглядний політик
  - меценат (patron) — щедрий меценат, церковне меценатство
  - бароко (baroque) — мазепинське бароко, розквіт стилю
  - автономія (autonomy) — збереження автономії, обмеження прав
  - старшина (starshyna/elite) — козацька старшина, генеральна старшина
  - статті (articles/agreements) — Коломацькі статті, підписання статей
  - дипломатія (diplomacy) — гнучка дипломатія, таємні переговори
  recommended:
  - інтрига (intrigue) — політичні інтриги, жертвою інтриг
  - компроміс (compromise) — вимушений компроміс, шукати компроміс
  - лояльність (loyalty) — демонструвати лояльність, сумніви у лояльності
  - протекторат (protectorate) — зміна протекторату, під протекторатом
  - універсал (universal/decree) — видавати універсали, гетьманський універсал
  - канцелярія (chancellery) — військова канцелярія, писар канцелярії
activity_hints:
- type: reading
  focus: Коломацькі статті
  source: Архівні документи
  items: 4
- type: essay-response
  focus: Як Мазепа зміцнював гетьманську владу?
connects_to:
- 'hist-64 (Іван Мазепа II: Культура)'
- 'hist-66 (Іван Мазепа III: Полтава)'
prerequisites:
- 'hist-62 (Синтез: Козацька революція)'
persona:
  voice: Senior Professor of History
  role: Chancellor
grammar:
- Минулий час в історичному наративі
- Політична та адміністративна лексика
- Складнопідрядні речення
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Іван Мазепа I: Державник** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Іван Мазепа I: Державник

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Іван Мазепа I: Державник"
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
