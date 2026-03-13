# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: hist-022
level: HIST
sequence: 22
slug: mykhailo-chernigivskyi
version: '2.0'
title: 'Михайло Чернігівський: Опір Орді'
focus: history
pedagogy: CBI
phase: HIST.3 [Mongol Era & Galicia-Volhynia]
word_target: 5000
objectives:
- 'Analyze the causes and consequences of михайло чернігівський: опір орді'
- Evaluate the historical significance of вступ
- Trace the development of потрібно більше практики?
content_outline:
- section: Вступ
  points:
  - 'Постать Михайла Всеволодовича у контексті ХІІІ століття — [!context] релігія і політика були нероздільні: відмова від
    обряду була політичним бунтом; Чернігівське князівство як один з найпотужніших центрів Русі'
  - Символізм мученицької смерті для української ідентичності — відмова визнати повну духовну владу загарбника (зміна світогляду
    через ритуали очищення)
  words: 1000
- section: 'Читання: Життя та опір Михайла Чернігівського'
  points:
  - 'Княжіння в Чернігові та боротьба за Київ — хронологія: 1238–1239 (перше княжіння), 1241–1243 (друге княжіння); конфлікти
    і союзи з Данилом Галицьким'
  - Подорож до Орди та відмова від язичницьких обрядів — 1246 рік; вимога Батия пройти між вогнями («очищення від злих намірів»)
    і вклонитися зображенню Чінгісхана
  - 'Смерть Михайла та боярина Федора як акт політичного протесту — [!history-bite] Михайло був одним з небагатьох (на відміну
    від Невського), хто обрав смерть замість приниження; дата страти: 20 вересня 1246 року'
  - Канонізація та вшанування пам'яті в Україні — офіційна канонізація 1547 року; святий Чернігівської землі, а не загальноросійський
    (деколонізація)
  words: 1000
- section: Первинні джерела
  points:
  - 'Аналіз літописних розповідей про загибель князя — Галицько-Волинський літопис (Іпатський список); цитата: «Тобі, царю,
    поклонюся, бо Бог доручив тобі царство... а тому, чому ці кланяються, не поклонюся»'
  - 'Житійні тексти як історичне джерело — «Сказання про вбивство в Орді...» як літературний твір, що акцентує на духовному
    подвигу; [!quote] слова Федора: «Не погуби душі, а тіла не бійся»'
  words: 1000
- section: Деколонізаційний погляд
  points:
  - Міф про 'покірну Русь' та реальність князівського спротиву — [!myth-buster] розвінчання радянського наративу про суцільну
    покору в період 'іга'; українські князі (Михайло, Данило) чинили опір
  - Порівняння стратегій Михайла Чернігівського та московських князів — [!decolonization] контраст з Олександром Невським
    (колаборація/виживання) проти Михайла (гідність/смерть); дві різні політичні культури
  words: 1000
- section: Потрібно більше практики?
  points:
  - Додаткові матеріали про опір українських князів ординському пануванню — [!culture] ікони та церква Михайла і Федора у
    Чернігові як елементи сакральної спадщини
  - 'Порівняння різних стратегій виживання під монгольською владою — тема есе: «Ціна компромісу: Михайло Чернігівський проти
    Олександра Невського»'
  words: 1000
vocabulary_hints:
  required:
  - Михайло Всеволодович (Mykhailo Vsevolodovych) — князь Чернігівський і Київський (титулатура)
  - Чернігівське князівство (Chernihiv Principality) — один з найпотужніших центрів Русі
  - Орда (Horde) — Золота Орда, ставка хана Батия
  - язичницькі обряди (pagan rituals) — пройти крізь вогонь, вклонитися кущу/сонцю/ідолам
  - мученицька смерть (martyrdom) — прийняти мученицький вінець (collocation)
  - боярин Федор (boyar Fedir) — вірний соратник, розділив долю князя
  - канонізація (canonization) — визнання святим, церковне вшанування
  - політичний протест (political protest) — відмова від покори як акт суверенності
  recommended:
  - літопис (chronicle) — Галицько-Волинський, Іпатський
  - житіє (hagiography) — житійна література, сказання
  - князівський спротив (princely resistance) — антонім до колаборації
  - релігійна стійкість (religious steadfastness) — не зрадити віру
activity_hints:
- type: reading
  title: Подорож Михайла до Орди та його рішення
- type: essay-response
  prompt: Чому Михайло Чернігівський відмовився виконати язичницькі обряди?
- type: critical-analysis
  focus: 'Критичний аналіз послідовності: '
  items: 3
- type: critical-analysis
  focus: 'Критична оцінка: '
  items: 4
prerequisites: '[]'
persona:
  voice: Senior Professor of History
  role: Orthodox Bishop
learning_outcomes: '[]'
connects_to:
- danylo-halytskyi

```

---

## PART 1: Deep Research

Research **Михайло Чернігівський: Опір Орді** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

### Your RAG Tools (USE THEM)

You have access to Ukrainian language tools via MCP. **Use them during research.**

| Tool | When to use | Example |
|------|-------------|---------|
| `query_wikipedia` mode=`extract` | Get full article text (50K chars) for deep research | `query_wikipedia("Богдан Хмельницький", mode="extract")` |
| `query_wikipedia` mode=`sections` | See article structure before diving in | `query_wikipedia("Запорізька Січ", mode="sections")` |
| `query_wikipedia` mode=`section` | Read a specific section by index | `query_wikipedia("Запорізька Січ", mode="section", section=3)` |
| `query_wikipedia` mode=`search` | Find the right article title | `query_wikipedia("Переяславська рада", mode="search")` |
| `search_literary` | Find primary source excerpts (chronicles, poetry, legal texts) | `search_literary("Хмельницький", genre="chronicle")` |
| `verify_word` / `verify_words` | Check Ukrainian words exist in VESUM dictionary | `verify_words(["гетьман", "козацтво"])` |
| `query_grac` | Check word frequency in Ukrainian corpus | `query_grac("упокорення", mode="frequency")` |

**Workflow**: Search Wikipedia FIRST for factual foundation → search literary RAG for primary quotes → verify vocabulary with VESUM.

### Research Requirements

1. **Sources**: Use `query_wikipedia` (mode=`extract`) for Ukrainian Wikipedia articles. Also consult history.org.ua, litopys.org.ua. Use `search_literary` for primary source excerpts. Russian-language sources are PROHIBITED.
2. **Timeline**: Build a chronological timeline with 5+ dated events/milestones.
3. **Primary Quotes**: Find 2+ quotable primary source excerpts (original Ukrainian text preferred).
4. **Engagement Hooks**: Identify 6+ engagement hooks mapped to specific content sections:
   - `[!myth-buster]` — Decolonization: correct imperial/Soviet myths
   - `[!history-bite]` — Surprising or lesser-known facts
   - `[!context]` — Broader historical/cultural context
   - `[!quote]` — Primary source citations
   - `[!decolonization]` — Ukraine-centric reframing
   - `[!culture]` — Cultural significance
5. **Decolonization Angle**: Identify how this topic has been distorted by imperial/Soviet historiography and what the Ukrainian-centric framing should be.
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
- **Colonial framing**: plan decolonized framing NOW so Phase B doesn't default to Russian comparisons
- **Engagement callouts**: map 6+ hooks to specific sections during research (not as afterthought patches)
- **Duplicate headers**: ensure outline section names don't share keywords

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

### Output Block 1: Research Notes

```
===RESEARCH_START===

# Дослідження: Михайло Чернігівський: Опір Орді

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — Phase D verifies prose against this -->
```yaml
subject: "Михайло Чернігівський: Опір Орді"
vital_status: "deceased" # or "alive"
dates:
  birth: "YYYY-MM-DD"    # or approximate: "~YYYY"
  death: "YYYY-MM-DD"    # omit if alive
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
- Section "{section_name}": [!hook_type] — description
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
```

## Friction Report (MANDATORY)

After both output blocks, include:

```
===FRICTION_START===
**Phase**: Phase A: Research + Meta (Seminar)
**Step**: {what you were doing when friction occurred, or "Full Phase A"}
**Friction Type**: NONE | TOKEN_LIMIT_TRUNCATION | TOOL_REDUNDANCY | SOURCE_NOT_FOUND | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===
```

---

## Boundaries

- Do NOT write lesson content — only research notes
- Do NOT generate activities or vocabulary
- Do NOT skip any section from the plan's content_outline
- Do NOT use Russian-language sources
- Do NOT fabricate quotes or dates — if unsure, mark as "[needs verification]"
- Do NOT reference persona names or voice instructions — persona is assigned at content generation time
- Do NOT request skills, delegate to Claude, or skip this phase
