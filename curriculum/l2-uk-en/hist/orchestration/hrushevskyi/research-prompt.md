# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: hist-087
level: HIST
sequence: 87
slug: hrushevskyi
version: '2.0'
title: Михайло Грушевський
subtitle: 'Mykhailo Hrushevsky: Father of Ukrainian Historiography'
focus: history
pedagogy: CBI
phase: HIST.9 [WWI & Revolution]
word_target: 5000
objectives:
- Учень може описати життя та діяльність Михайла Грушевського
- Учень може пояснити його концепцію «Історії України-Руси»
- Учень може проаналізувати його роль як голови Центральної Ради
- Учень може оцінити значення Грушевського для української історіографії
content_outline:
- section: 'Вступ: Людина-епоха'
  points:
  - Чому Грушевський — найважливіший український історик — творець «паспорта» українського народу, наукової історії
  - Науковець, який став президентом — поєднання ролей національного пророка XIX ст. і державного будівничого XX ст.
  - 'Трагічна доля в радянські часи — повернення в 1924 році як свідома жертва заради науки; engagement hook: [!history-bite]
    про географію життя (Холм, Кавказ, Київ, Львів, Кисловодськ)'
  words: 850
- section: Біографія та наукова кар'єра
  points:
  - Ранні роки та освіта — вплив Володимира Антоновича та київської школи
  - 'Львівський період: професор, керівник НТШ — «золота доба» (1894–1914), перетворення НТШ на де-факто Академію наук; engagement
    hook: [!context] про професорство у 28 років'
  - «Історія України-Руси» — монументальна праця — 10 томів у 13 книгах, писалася все життя
  - Деконструкція російської імперської схеми — зміщення фокусу з історії держави на історію народу
  words: 850
- section: Політична діяльність
  points:
  - Революція 1917 року — обрання головою Центральної Ради заочно (березень 1917)
  - 'Голова Центральної Ради — легітимізація УНР; engagement hook: [!myth-buster] про «романтика, який не вмів керувати»'
  - Проголошення УНР — еволюція поглядів від автономії до незалежності (IV Універсал)
  - Еміграція та повернення — Прага, Відень, Женева (1919–1924) та фатальне рішення повернутися в СРСР
  - 'Радянський період: тиск та загибель — арешт 1931 року, смерть у Кисловодську 1934 року (медичний терор)'
  words: 850
- section: Первинні джерела
  points:
  - Фрагменти «Історії України-Руси» — аналіз стилю та аргументації
  - Промови Грушевського в Центральній Раді — риторика державотворення
  - 'Листи та щоденники — листи до доньки Катерини як свідчення людяності; engagement hook: [!quote] зі статті 1904 року «Звичайна
    схема...»'
  words: 850
- section: Деколонізаційний погляд
  points:
  - Схема Грушевського проти схеми Карамзіна — «коперніканський переворот» в історії Східної Європи
  - 'Україна як окремий історичний суб''єкт — спадкоємність: Київська Русь -> Галицько-Волинська держава -> Козаччина -> УНР'
  - 'Чому Росія досі атакує Грушевського — боротьба за київську спадщину; engagement hook: [!decolonization] про термін «Україна-Русь»'
  words: 850
- section: 'Підсумок: Незнищенна спадщина'
  points:
  - 'Грушевський на сторінці гривні — символізм 50 гривень; engagement hook: [!symbolism]'
  - Сучасна історіографія та його вплив — цитата «Біда України в тому, що нею керують ті, кому вона не потрібна»
  - Грушевський і війна 2022 року — історична схема як зброя проти російських псевдоісторичних наративів
  words: 750
vocabulary_hints:
  required:
  - історіографія (historiography) — батько української історіографії
  - історик (historian) — видатний, авторитетний
  - наукова школа (academic school) — київська історична школа, школа Антоновича
  - концепція (concept) — схема історії, народницька концепція
  - деконструкція (deconstruction) — імперського наративу, міфів
  - Центральна Рада (Central Rada) — голова ЦР, парламент
  - голова (chairman) — обраний головою
  - праця (work/opus) — фундаментальна, багатотомна
  recommended:
  - методологія (methodology) — наукова, позитивістська
  - джерело (source) — першоджерело, аналіз джерел
  - архів (archive) — робота в архівах
  - репресії (repressions) — радянські, переслідування
  - реабілітація (rehabilitation) — посмертна, наукова
  - спадщина (legacy) — незнищенна, інтелектуальна
activity_hints:
- type: reading
  focus: Фрагменти «Історії України-Руси»
  source: Наукові тексти
  items: 4
- type: critical-analysis
  focus: 'Спростування міфів: Міфи про Грушевського'
  items: 5
- type: essay-response
  focus: Чому концепція Грушевського досі важлива для української ідентичності?
connects_to:
- hist-90 (Центральна Рада)
- 'hist-98 (Розстріляне відродження: Постаті)'
prerequisites:
- 'hist-86 (Синтез: Імперська доба)'
persona:
  voice: Senior Professor of History
  role: Academic Historian
grammar:
- Минулий час в біографічному наративі
- Наукова термінологія
- Непряма мова для передачі ідей
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Михайло Грушевський** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Михайло Грушевський

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — Phase D verifies prose against this -->
```yaml
subject: "Михайло Грушевський"
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
