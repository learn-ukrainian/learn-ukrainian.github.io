# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: hist-014
level: HIST
sequence: 14
slug: sofiya-kyivska
version: '2.0'
title: Софія Київська та культурний розквіт
focus: history
pedagogy: seminar
phase: HIST.1 [Kyivan Rus]
word_target: 5000
objectives:
- Understand significance of St Sophia
- Analyze mosaics and frescoes
- Discuss cultural blooming of Kyivan Rus
sources:
- name: Софійський собор (Київ) (Вікіпедія)
  url: https://uk.wikipedia.org/wiki/Софійський_собор_(Київ)
  type: reference
  notes: UNESCO World Heritage site
- name: Національний заповідник "Софія Київська"
  url: https://uk.wikipedia.org/wiki/Національний_заповідник_«Софія_Київська»
  type: reference
  notes: Museum complex
- name: Мозаїки Софії Київської
  url: https://uk.wikipedia.org/wiki/Мозаїки_Софійського_собору_в_Києві
  type: reference
  notes: Art analysis
content_outline:
- section: Вступ
  points:
  - Символ мудрості та могутності — «Діамант у короні» Ярослава; місце коронацій, судів та поховань еліти
  - 'Державний статус — не просто церква, а «головний офіс» Русі-України; engagement hook: [!history-bite]'
  words: 450
- section: 'Архітектура собору: Візантійський канон та київська сміливість'
  points:
  - 'Історичне тло: Майстри та замисел — грецькі архітектори з Константинополя та місцеві учні; дискусія про дату заснування
    (1011 vs 1037)'
  - 'Конструктивні особливості — 13 куполів (Христос і 12 апостолів) та пірамідальна композиція; деколонізаційний аспект:
    унікальний київський стиль, відсутній у тогочасній Росії (Заліссі)'
  - 'Техніка мурування: Opus Mixtum — «смугаста» кладка з каменю та плінфи на рожевому розчині (цем''янці); engagement hook:
    [!context]'
  words: 450
- section: 'Мозаїки та фрески: Біблія у кольорі'
  points:
  - Світлоносна Мозаїка — смальта (177 відтінків), мерехтіння світла; Оранта «Нерушима стіна» — легенда про стійкість Києва
  - 'Живописні Фрески — унікальні світські сюжети на стінах храму: полювання на вепра, скоморохи, іподром Константинополя
    (сходи на хори)'
  words: 450
- section: 'Графіті Софії: Голоси киян XI-XIII століть'
  points:
  - 'Про що писали кияни? — «Середньовічний Facebook»: скарги, молитви, прокляття, любовні зізнання та політичні новини; engagement
    hook: [!culture]'
  - 'Мовний аспект — жива староукраїнська мова (риси: «Володимир», «Олекса», «помагай»), відмінна від церковнослов''янської
    книжної'
  words: 450
- section: 'Культурний розквіт: "Афіни Сходу"'
  points:
  - Скрипторій та Бібліотека
  - Літературна школа
  words: 450
- section: Читання
  points:
  - Інтелектуальний центр Русі — Іларіон Київський та його «Слово про Закон і Благодать» як маніфест політичної суверенності
    від Візантії
  words: 450
- section: Первинні джерела
  points:
  - 'Документ 1: «Повість минулих літ» про заснування Софії (1037 р.) — цитата про «писців многих» та переклади книг'
  - 'Документ 2: Графіті про смерть Ярослава Мудрого (1054 р.) — титулування князя «царем» (рівним імператору); engagement
    hook: [!source]'
  words: 450
- section: Таємниця саркофага Ярослава Мудрого
  points:
  - Історія відкриттів — 6-тонний саркофаг, зникнення кісток Ярослава (версія про вивезення до США)
  - 'Сучасні дослідження (2009) — виявлення лише жіночого скелета (Інгегерда?) та радянської газети; engagement hook: [!mystery]'
  words: 450
- section: 'Дзвіниця: Голос Києва'
  points:
  - 'Історична доля: Від занепаду до відродження — роль гетьмана Івана Мазепи у відбудові; стиль козацького бароко (бірюзово-білий);
    engagement hook: [!myth-buster]'
  words: 450
- section: Деколонізаційний погляд
  points:
  - Міфи та реальність — спростування імперського міфу про «спільну колиску»; Софія як доказ європейської суб'єктності Києва
  - 'Сучасна Україна — повернення справжніх титулів (каган, цар) замість нав''язаних пізніше «князів»; engagement hook: [!decolonization]'
  words: 450
- section: Потрібно більше практики?
  points:
  - 🔄 Інтеграція знань — порівняння мозаїк Софії та Равенни
  - Реальне застосування — віртуальний тур заповідником
  - 🌐 Онлайн-ресурси — сайт «Софія Київська» та база графіті
  words: 500
vocabulary_hints:
  required:
  - собор (cathedral) — головний храм міста, символ віри
  - мозаїка (mosaic) — мистецтво зі смальти, вічна техніка
  - фреска (fresco) — розпис по вологій штукатурці
  - Оранта (Oranta) — «Нерушима стіна», захисниця Києва
  - купол (dome) — баня, символ неба (13 куполів Софії)
  - неф (nave) — частина внутрішнього простору храму
  - візантійський (Byzantine) — стиль Константинополя, канон
  - бароко (Baroque) — козацьке бароко, стиль Мазепи
  - графіті (graffiti) — видряпані написи, жива історія
  - митрополит (metropolitan) — голова церкви, Петро Могила
  - літописання (chronicle writing) — фіксація історії, скрипторій
  - іконопис (icon painting) — канонічне зображення святих
  recommended:
  - хрестово-купольний (cross-domed) — тип храму, архітектурна схема
  - Нерушима стіна (Unbreakable Wall) — епітет Оранти, символ стійкості
  - смальта (smalto) — кольорове скло для мозаїк
  - заповідник (reserve/sanctuary) — охоронна зона, музейний комплекс
  - юрисдикція (jurisdiction) — церковна влада, підпорядкування
activity_hints:
- type: critical-analysis
  focus: Analyze St. Sophia mosaics and frescoes (Visual analysis)
  items: 8-10 images
- type: reading
  focus: Excerpt from "Slovo pro zakon i blahodat"
  source: Provide in module
- type: comparative-study
  focus: Original 11th century vs modern appearance
  output: Visual comparison
- type: essay-response
  focus: Чому Софія Київська є символом України?
connects_to:
- hist-16 (Kyivan Rus culture)
- 'hist-20 (Synthesis: Kyivan Rus)'
prerequisites:
- hist-12 (Yaroslav the Wise)
- hist-11 (Volodymyr and Baptism)
persona:
  voice: Senior Professor of History
  role: Cathedral Mosaicist
grammar:
- Historical narrative
module_type: history
immersion: 100% Ukrainian

```

---

## PART 1: Deep Research

Research **Софія Київська та культурний розквіт** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Софія Київська та культурний розквіт

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — Phase D verifies prose against this -->
```yaml
subject: "Софія Київська та культурний розквіт"
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
