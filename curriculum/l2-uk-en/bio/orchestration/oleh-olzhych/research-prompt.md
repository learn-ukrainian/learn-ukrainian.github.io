# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: bio-179
level: BIO
sequence: 179
slug: oleh-olzhych
version: '2.0'
title: 'Олег Ольжич: Камінь з Божої пращі'
focus: biography
pedagogy: immersion
phase: BIO
word_target: 5000
objectives:
- Проаналізувати поєднання наукової, поетичної та політичної діяльності Олега Ольжича
- Дослідити археологічні досягнення Ольжича у контексті тяглості української цивілізації
- Оцінити моральний вибір інтелектуала між безпекою еміграції та підпільною боротьбою
sources:
- name: Олег Ольжич (Wikipedia UA)
  url: https://uk.wikipedia.org/wiki/Олег_Ольжич
  type: primary
  notes: Біографія, наукова та політична діяльність, загибель у Заксенгаузені
- name: Заксенгаузен (концтабір)
  url: https://uk.wikipedia.org/wiki/Заксенгаузен_(концтабір)
  type: reference
  notes: Місце загибелі
content_outline:
- section: Вступ — Інтелектуал, який обрав смерть
  points:
  - Ольжич як унікальний тип — вчений-археолог світового рівня, поет і підпільник
  - Син Олександра Олеся — спадкоємність поетичних поколінь
  - Загибель під тортурами в Заксенгаузені — ціна відмови від колаборації
  - Псевдонім «Ольжич» — від княгині Ольги, державність у крові
  words: 850
- section: Житомир, Київ, Прага (1907-1929)
  points:
  - Народження в Житомирі у родині поета Олександра Олеся та вчительки Віри Свадковської
  - Дитинство в Києві на вулиці Антоновича, трудова школа в Пущі-Водиці
  - Еміграція з матір'ю до Берліна (1922), зустріч з батьком після трьох років розлуки
  - Прага — матуральні курси, Карлов університет, Український вільний університет
  - Член Пласту, вірш «Пластовий капелюх»
  words: 850
- section: Археолог європейського масштабу (1929-1938)
  points:
  - Дисертація «Неолітична мальована кераміка Галичини» (1930)
  - Трипільська культура — розкопки на Тернопільщині, шість типів кераміки
  - Міжнародний конгрес у Лондоні, Американська школа доісторичних досліджень
  - Співпраця з Гарвардським університетом, експедиції до Югославії
  - Археологія як доказ тяглості української цивілізації
  - Спроба створення Українського наукового інституту в Америці
  words: 900
- section: Поезія вежі та ріні
  points:
  - «Рінь» (1935) — дебютна збірка, стоїчна героїка
  - «Вежі» (1940) — символ незламності, вертикаль духу
  - Вплив Празької школи, але окремий голос — аскетичний, мужній
  - Теми честі, жертви, обов'язку — поезія як етичний кодекс
  - «Підзамче» (1946) — посмертна збірка, видана в діаспорі
  words: 800
- section: ОУН та підпільна боротьба (1929-1944)
  points:
  - Вступ до ОУН (1929), культурно-освітня референтура ПУН (1937)
  - Карпатська Україна — арешт угорцями, визволення після листа вчених
  - Розкол ОУН — залишився з Мельником, але підтримував контакти з Бандерою та Шухевичем
  - Київ 1941 — організація Української Національної Ради
  - Голова ПУН (січень 1944) після арешту Мельника
  - Одруження з Калиною Білецькою (1943), народження сина Олега після смерті батька
  words: 850
- section: Заксенгаузен та безсмертя (1944 — сьогодення)
  points:
  - Арешт гестапо у Львові 25 травня 1944 на вулиці Личаківській
  - Целленбау — блок для особливо важливих в'язнів
  - Загибель під час допиту в ніч проти 10 червня 1944, гестапівська трійка
  - Символічна могила — від Ольшанського цвинтаря у Празі до Лук'янівського у Києві (2017)
  - Фільм-трилогія «Я камінь з Божої пращі», Шевченківська премія (2002)
  - Вулиці, бібліотеки, пам'ятники — вшанування інтелектуала, який не зрадив
  words: 750
vocabulary_hints:
  required:
  - археолог (archaeologist)
  - підпільник (underground fighter)
  - концтабір (concentration camp)
  - катування (torture)
  - колаборація (collaboration)
  - неоліт (Neolithic)
  - кераміка (ceramics)
  - стоїцизм (stoicism)
  - державотворення (state-building)
  - жертовність (self-sacrifice)
  recommended:
  - Заксенгаузен (Sachsenhausen)
  - Празька школа (Prague School)
  - трипільська культура (Trypillia culture)
  - ПУН (Leadership of Ukrainian Nationalists)
  - Целленбау (Zellenbau — special prison block)
activity_hints:
- type: reading
  focus: Поезія та біографія інтелектуала-підпільника
  source: Вірші та біографічні матеріали
  items: 3 passages
- type: essay-response
  focus: Як поєднувалися наука, поезія та політична боротьба в житті Ольжича?
  output: Біографічне есе
connects_to:
- bio-95 (Євген Коновалець)
- bio-118 (Олена Теліга)
- bio-123 (Богдан-Ігор Антонич)
- bio-92 (Микола Зеров)
prerequisites:
- bio-95 (Євген Коновалець)
persona:
  voice: Senior Historian
  role: Resistance Intellectual Specialist
module_type: biography
immersion: 100% Ukrainian

```

---

## Downstream Audit Gates (know these BEFORE you start)

Phase B content must pass these gates — plan your research accordingly:
- **Word count**: minimum **5000** words
- **Colonial framing**: plan decolonized framing NOW so Phase B doesn't default to Soviet tropes
- **Engagement callouts**: map 6+ hooks to specific sections during research
- **Duplicate headers**: ensure outline section names don't share keywords

---

## PART 1: Deep Research

Research **Олег Ольжич: Камінь з Божої пращі** for the **bio** track. Produce structured research notes that will drive content writing in Phase B.

### Your RAG Tools

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

### Research Workflow (minimize tool round-trips)

> **Performance rule**: Each tool call forces context re-processing. Batch your calls. Do NOT add narration between tool calls ("I will now search...") — output ONLY the tool call block. Fewer turns = faster completion.

**Batch 1 — Initial sweep (call ALL of these in ONE turn):**
- `query_wikipedia(query="Олег Ольжич: Камінь з Божої пращі", mode="extract")` — factual backbone
- `search_literary(query="Олег Ольжич: Камінь з Божої пращі")` — primary source excerpts
- `verify_words(words=[...])` — check vocabulary_hints from plan

**Batch 2 — Targeted follow-up (1-2 calls MAX):**
Based on Batch 1 results, fill gaps with ONE of:
- `search_literary` with a different query if primary quotes are missing
- `query_wikipedia` for a related article if key context is missing
- Skip this batch entirely if Batch 1 covered everything

**That's it. 2 batches, not 4 sequential steps.** Quality comes from thinking, not from more tool calls.

### Research Requirements

1. **Sources**: Minimum **3 distinct sources** — at least 1 from Wikipedia AND at least 1 from `search_literary` (RAG). Russian-language sources are PROHIBITED. Every factual claim must be traceable to a cited source.
2. **Timeline**: Build a chronological timeline with 5+ dated events/milestones.
3. **Primary Quotes**: Find **3+** quotable primary source excerpts using `search_literary`. Use guillemet quotes «...» for Ukrainian text. If `search_literary` returns relevant chunks, extract and attribute them properly. Mark unverified quotes as `[needs verification]`.
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

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

### Output Block 1: Research Notes

===RESEARCH_START===

# Дослідження: Олег Ольжич: Камінь з Божої пращі

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Олег Ольжич: Камінь з Божої пращі"
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
