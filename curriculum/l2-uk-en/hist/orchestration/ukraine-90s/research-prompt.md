# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-122
level: HIST
sequence: 122
slug: ukraine-90s
version: '2.0'
title: 'Україна 1990-х: Кучма та олігархи'
subtitle: 'Ukraine in the 1990s: Kuchma and the Oligarchs'
focus: history
pedagogy: CBI
phase: HIST.12 [Independence & Modern Era]
word_target: 5000
objectives:
- Учень може описати економічну та політичну ситуацію 1990-х років
- Учень може пояснити формування олігархічної системи
- Учень може проаналізувати президентство Кучми
- Учень може оцінити виклики молодої держави
content_outline:
- section: 'Вступ: Народження держави'
  points:
  - '1991: Україна незалежна — період ейфорії, що змінився шоком від економічного розвалу'
  - Виклики нової держави — втрата ядерної зброї (Будапештський меморандум 1994) та відсутність економічної стратегії
  - Від Кравчука до Кучми — вибори 1994 року як перша мирна передача влади; перемога Кучми на проросійських гаслах
  words: 850
- section: Економічна криза
  points:
  - 'Гіперінфляція — світовий рекорд 1993 року (понад 10000%) та повне знецінення заощаджень; cultural hook: «кравчучка» як
    символ виживання [!history-bite]'
  - Приватизація та «прихватизація» — ваучерна схема, де директори скуповували активи за безцінь [!myth-buster]
  - 'Народження олігархів — парадокс «червоних директорів»: як номенклатура стала капіталістами [!context]'
  - Донецький та дніпропетровський клани — формування груп впливу (Лазаренко, Тимошенко, Ахметов) навколо енергетики та металургії
  words: 850
- section: Президентство Кучми
  points:
  - Вибори 1994 та 1999 років — технологія «червоної загрози» (Кучма проти Симоненка) та використання адмінресурсу
  - Авторитарні тенденції — Конституція 1996 року як компроміс, що посилив президентську владу; багатовекторність як пастка
    [!decolonization]
  - Касетний скандал — оприлюднення записів Мельниченка Олександром Морозом (листопад 2000)
  - Справа Гонгадзе — вбивство журналіста (вересень 2000) як точка неповернення для легітимності влади
  - «Україна без Кучми» — перші масові протести (грудень 2000 – березень 2001), розгін 9 березня
  words: 850
- section: Первинні джерела
  points:
  - Касети Мельниченка — аналіз змісту погроз та стилю спілкування влади [!quote]
  - Журналістські розслідування — Георгій Гонгадзе та «Українська правда» як нові медіа
  - Свідчення політиків — реакція влади на звинувачення (заперечення, тиск на слідство)
  words: 850
- section: Деколонізаційний погляд
  points:
  - Олігархія vs. демократія — порівняння з люстрацією в країнах Балтії та Польщі; чому Україна тупцювала на місці
  - Роль Росії в 1990-х — енергетичний шантаж («газові війни»), Чорноморський флот та кримський сепаратизм (Мєшков)
  - Втрачені можливості — домінування російського культурного продукту vs феномен «Території А» [!culture]
  words: 850
- section: 'Підсумок: До Помаранчевої революції'
  points:
  - Підсумки 1990-х — ізоляція Кучми на Заході та дрейф у бік Росії
  - Формування опозиції — відставка Ющенка (2001) та створення блоку «Наша Україна»
  - Шлях до 2004 року — суспільство навчилося протестувати, а влада — фальсифікувати вибори
  words: 750
vocabulary_hints:
  required:
  - 'олігарх (oligarch) — кланово-олігархічна система; learner error: плутати з просто «багата людина» (бізнесмен)'
  - приватизація (privatization) — ваучерна приватизація, незаконна приватизація («прихватизація»)
  - інфляція (inflation) — гіперінфляція, галопуюча інфляція, індекс інфляції
  - корупція (corruption) — боротьба з корупцією, політична корупція, рівень корупції
  - демократія (democracy) — розбудова демократії, загроза демократії
  - клан (clan) — олігархічний клан, донецький клан, дніпропетровський клан
  - скандал (scandal) — касетний скандал, політичний скандал, корупційний скандал
  - журналіст (journalist) — опозиційний журналіст, свобода слова, переслідування журналістів
  recommended:
  - авторитаризм (authoritarianism) — посилення авторитаризму, авторитарний режим
  - бізнес (business) — тіньовий бізнес, малий та середній бізнес
  - опозиція (opposition) — демократична опозиція, об'єднана опозиція
  - вибори (elections) — фальсифікація виборів, президентські перегони
  - референдум (referendum) — всеукраїнський референдум
  - медіа (media) — незалежні медіа, контроль над медіа, цензура
activity_hints:
- type: reading
  focus: Журналістські розслідування 1990-х
  source: Медіа-архіви
  items: 4
- type: critical-analysis
  focus: 'Верифікація фактів: Факти про 1990-ті'
  items: 5
- type: essay-response
  focus: Як формування олігархії вплинуло на розвиток України?
connects_to:
- hist-123 (Помаранчева революція)
- 'hist-124 (Епоха Януковича: Реванш)'
prerequisites:
- hist-120 (Незалежність 1991)
persona:
  voice: Senior Professor of History
  role: Economic Reformer
grammar:
- Минулий час в історичному наративі
- Економічна та політична лексика
- Складнопідрядні речення
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Україна 1990-х: Кучма та олігархи** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Україна 1990-х: Кучма та олігархи

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Україна 1990-х: Кучма та олігархи"
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
