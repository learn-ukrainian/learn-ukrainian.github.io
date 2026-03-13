# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-121
level: HIST
sequence: 121
slug: nezalezhnist-1991
version: '2.0'
title: 'Україна 1991-2004: Становлення'
subtitle: 'Ukraine 1991-2004: Formation of a State'
focus: history
pedagogy: CBI
phase: HIST.12 [Independence & Modern Era]
word_target: 5000
objectives:
- Учень може описати проголошення незалежності 1991 року
- Учень може пояснити економічні та політичні виклики раннього періоду
- Учень може проаналізувати формування олігархічної системи
- Учень може оцінити президентство Кравчука та Кучми
content_outline:
- section: 'Вступ: Народження держави'
  points:
  - '24 серпня 1991: Акт проголошення незалежності — include quote ''Виходячи із смертельної небезпеки...''; author Levko
    Lukyanenko; text written by Levko Lukyanenko; atmosphere of euphoria and anxiety'
  - '1 грудня 1991: референдум — 90.32% support shock to Moscow; voted YES even in Crimea and Donbas; legal dissolution of
    USSR; Ukraine as subject of international law'
  - 'Що означала незалежність для українців — Legal dissolution of USSR; Ukraine as subject of international law; cultural
    hook: atmosphere of euphoria and anxiety; [!quote] — Цитата з Акту проголошення незалежності про «смертельну небезпеку»'
  words: 850
- section: Перші роки (1991-1994)
  points:
  - 'Леонід Кравчук: перший президент — Ideologue turned statesman; policy of ''between raindrops'' (між крапельками); avoided
    civil conflict but stalled reforms; former CPU ideologue; «Маємо те, що маємо» — phrase symbolizing the era of uncertainty'
  - Будапештський меморандум — 5 Dec 1994; Assurances (запевнення) vs Guarantees; pressure from US/Russia; Ukraine had 3rd
    largest nuclear arsenal
  - 'Ядерне роззброєння — Ukraine had 3rd largest arsenal; traded for paper promises; analyze text: «respect sovereignty»
    vs «defend»'
  - Економічна криза та гіперінфляція — 10,000% inflation in 1993; 'Kravchuchka' (cart) as symbol of survival; Coupons/Karbonavtsi
    era; prices changed daily; salaries in millions of coupons; [!history-bite] — Про «кравчучку» як символ епохи виживання
  words: 850
- section: Ера Кучми (1994-2004)
  points:
  - Конституція 1996 року — 28 June 1996 'Constitutional Night'; result of fierce political struggle vs 'gifted' myth; adopted
    in one night (27-28 June) under threat of parliament dissolution; [!myth-buster] — Constitution was not «gifted», result
    of struggle
  - 'Грошова реформа: гривня — Sept 1996; Viktor Yushchenko (NBU); exchange 100,000:1; stabilization of economy; 1 USD = 1.76
    UAH at launch'
  - Формування олігархічної системи — Red directors privatizing assets using Soviet connections; rise of Donetsk and Dnipro
    clans; [!decolonization] — «Red directors» became first oligarchs using Soviet ties; direct legacy of Soviet nomenklatura
  - Авторитарні тенденції — 'Multi-vector' foreign policy (maneuvering between West/Russia); strong presidential power; [!context]
    — «Multi-vector» policy as sitting on two chairs
  - «Касетний скандал» та «Україна без Кучми» — Nov 2000; Gongadze case; Melnychenko tapes; first mass protests; crackdown
    9 March 2001; rehearsal for Orange Revolution
  words: 850
- section: Первинні джерела
  points:
  - Акт проголошення незалежності — focus on right to self-determination and 'mortal danger' justification; key document
  - 'Будапештський меморандум — analyze text: ''respect sovereignty'' vs ''defend'''
  - 'Промови політиків — Kravchuk inaugural (building state); Chornovil (alternative democratic path); Chornovil: alternative
    democratic path not chosen'
  words: 850
- section: Деколонізаційний погляд
  points:
  - 'Радянська спадщина в економіці — Lack of closed production cycles; vulnerability to Moscow blackmail (gas wars); imperial
    myth: economy unviable without Russia; reality: collapse caused by dependency on Soviet model'
  - Пострадянські еліти — Nomenklatura remained in power; no lustration (unlike Baltics); 'Sovok' management style; lack of
    lustration conserved «sovok» management
  - Незавершеність — Formal vs Mental independence; cultural space dominated by Russia until 2014; formal independence did
    not mean mental independence
  words: 850
- section: 'Підсумок: До Помаранчевої революції'
  points:
  - 'Досягнення та невдачі — State institutions/Currency/Army established vs Corruption/Poverty; success: state institutions,
    currency, army established; failure: corruption, oligarchy, poverty'
  - 'Суспільство готове до змін — Cultural hook: Song ''Razom nas bahato''; civil society awakening; [!culture] — Song «Razom
    nas bahato» as anthem of awakening; civil society outgrew the state'
  - '2004: точка перелому — Falsified elections as trigger; society outgrew the authoritarian state; falsified elections as
    trigger for explosion of accumulated discontent'
  words: 750
vocabulary_hints:
  required:
  - незалежність (independence) — проголошення незалежності, здобуття незалежності, відновлення незалежності
  - референдум (referendum) — всеукраїнський референдум, провести референдум
  - конституція (constitution) — прийняти конституцію, гарант конституції, конституційна ніч
  - президент (president) — інавгурація президента, повноваження президента
  - олігарх (oligarch) — олігархічний клан, вплив олігархів, червоні директори
  - приватизація (privatization) — ваучерна приватизація, незаконна приватизація
  - гіперінфляція (hyperinflation) — галопуюча інфляція, знецінення грошей
  - реформа (reform) — грошова реформа, земельна реформа
  recommended:
  - меморандум (memorandum) — підписати меморандум, порушити меморандум
  - роззброєння (disarmament) — ядерне роззброєння, відмова від зброї
  - корупція (corruption) — боротьба з корупцією, корупційні схеми
  - авторитаризм (authoritarianism) — посилення авторитаризму, авторитарний режим
  - опозиція (opposition) — політична опозиція, об'єднана опозиція
  - громадянське суспільство (civil society) — розвиток громадянського суспільства, зрілість суспільства
  - багатовекторність (multi-vector policy) — політика багатовекторності, сидіти на двох стільцях
  - кравчучка (kravchuchka) — символ епохи виживання, епоха кравчучок
activity_hints:
- type: reading
  focus: Акт проголошення незалежності
  source: Офіційні документи
  items: 4
- type: essay-response
  focus: Чому незалежність 1991 року не принесла швидкого добробуту?
connects_to:
- hist-123 (Помаранчева революція)
- hist-125 (Мовна політика)
prerequisites:
- hist-119 (Шлях до незалежності)
persona:
  voice: Senior Professor of History
  role: Parliamentary Deputy
grammar:
- Минулий час в історичному наративі
- Політична та економічна лексика
- Складнопідрядні речення
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Україна 1991-2004: Становлення** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Україна 1991-2004: Становлення

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Україна 1991-2004: Становлення"
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
