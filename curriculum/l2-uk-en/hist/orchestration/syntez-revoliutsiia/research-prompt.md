# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-097
level: HIST
sequence: 97
slug: syntez-revoliutsiia
version: '2.0'
title: 'Синтез: Українська революція'
subtitle: 'Synthesis: The Ukrainian Revolution'
focus: history
pedagogy: CBI
phase: HIST.9 [WWI & Revolution]
word_target: 5000
objectives:
- Учень може синтезувати знання про Українську революцію 1917-1921
- Учень може пояснити причини поразки визвольних змагань
- Учень може проаналізувати досягнення та помилки
- Учень може оцінити спадщину революції для сучасності
content_outline:
- section: 'Вступ: Втрачена незалежність'
  points:
  - '1917-1921: чотири роки боротьби — це не був «хаос», а відчайдушна спроба побудувати дім під час землетрусу; key dates:
    17 березня 1917 (УЦР) — листопад 1921 (Другий Зимовий похід)'
  - Чому важлива революція — вперше за століття Україна заявила про себе як суб'єкт, а не об'єкт історії
  - 'Уроки для сьогодення — головний урок: єдність еліти та нації важливіша за ідеологічні розбіжності; [!history-bite] «Читати
    з бромом» (Винниченко) — цитата з «Відродження нації» про розпач від внутрішніх чвар'
  words: 850
- section: Етапи революції
  points:
  - 'Центральна Рада (березень 1917 — квітень 1918) — Романтики (Грушевський, Винниченко); акцент на автономії та культурі;
    помилка: запізніле створення армії; [!context] Три кольори революції: соціалістична, консервативна, республіканська'
  - 'Гетьманат (29 квітня — 14 грудня 1918) — Прагматики (Скоропадський); акцент на порядку та власності; відкриття Академії
    наук; помилка: залежність від німців та відчуження селянства'
  - 'Директорія (грудень 1918 — 1920) — Воїни (Петлюра); повстання проти Гетьмана; війна на кілька фронтів; гірка іронія:
    «У вагоні Директорія, під вагоном територія»'
  - ЗУНР та Акт Злуки — висока організація (УГА); Злука 22 січня 1919 як символічна вершина революції — об'єднання Наддніпрянщини
    та Галичини
  words: 850
- section: Причини поразки
  points:
  - 'Внутрішні конфлікти — соціалісти ненавиділи консерваторів; галичани не завжди розуміли наддніпрянців; reference: Липинський
    «Листи до братів-хліборобів» про брак власної держави'
  - Соціальні проблеми — селяни хотіли землі негайно; більшовицький популізм (обіцянки всього) проти легальних реформ УНР
  - 'Зовнішні вороги — «Чотирикутник смерті»: Червона Росія, Біла Росія (Денікін), Польща, Румунія/Антанта; [!myth-buster]
    Міф про «Громадянську війну» — це була Українсько-російська війна'
  - Слабкість армії — брак зброї та амуніції; епідемія тифу («Тіфозна зима»), що викосила ряди УГА
  - Чому більшовики перемогли — тотальна мобілізація, терор та необмежений популізм; [!analysis] Отаманщина як прокляття (отамани
    Зелений, Ангел)
  words: 850
- section: Первинні джерела в синтезі
  points:
  - Порівняння урядів — Універсали УЦР (поетичні, декларативні) vs Грамоти Скоропадського (сухі, наказові)
  - 'Документи епохи — IV Універсал (незалежність 22 січня 1918): «Однині Українська Народна Республіка стає самостійною...»
    та Акт Злуки (єдність)'
  - Спогади учасників — Винниченко («Відродження нації» — самовиправдання) vs Скоропадський («Спогади» — погляд аристократа);
    include quote from Винниченко
  words: 850
- section: Деколонізаційний погляд
  points:
  - 'Радянський наратив: «буржуазія» — трактування національної війни як класової боротьби; міф про Петлюру-погромника vs
    реальність його наказів проти погромів'
  - 'Реальність: національно-визвольний рух — повноцінний процес державотворення, знищений зовнішньою агресією; [!decolonization]
    Термінологія має значення (не «банди», а повстанські загони; не «петлюрівці», а Армія УНР)'
  - 'Революція в українській пам''яті — тяглість: уряд в екзилі передав клейноди Україні у 1992 році (Плав''юк — Кравчуку)'
  words: 850
- section: 'Підсумок: Спадщина'
  points:
  - Що залишилось — державні символи (Тризуб, Гімн, Прапор) та кордони (Берестейський мир)
  - Від 1921 до 1991 — Герої Крут, Базар та Зимові походи як міф, на якому виросло покоління УПА і шістдесятників
  - Революція та сучасна Україна — сучасна війна як продовження боротьби 1917-1921; [!legacy] Без 1917 року не було б 1991
    — УРСР мусила зберігати атрибути державності через силу спротиву УНР
  words: 750
vocabulary_hints:
  required:
  - синтез (synthesis) — історичний синтез, узагальнення подій
  - революція (revolution) — Українська революція 1917–1921, доба визвольних змагань
  - незалежність (independence) — проголошена IV Універсалом, відновлена у 1991
  - 'поразка (defeat) — причини поразки: внутрішні чвари та зовнішня агресія'
  - боротьба (struggle) — визвольна боротьба за державність, збройний опір
  - визвольні змагання (liberation struggle) — термін замість імперського «Громадянська війна»
  - уряд (government) — УЦР, Гетьманат, Директорія, екзильний уряд
  - армія (army) — Армія УНР, УГА (Українська Галицька Армія), повстанські загони
  recommended:
  - конфлікт (conflict) — внутрішній соціальний та національний конфлікт
  - більшовики (Bolsheviks) — червона загроза, популізм, російська окупація
  - інтервенція (intervention) — військова агресія Росії, «Чотирикутник смерті»
  - еміграція (emigration) — політична еміграція, уряд в екзилі (exile)
  - спадщина (legacy) — символи (Тризуб), ідея державності, історична тяглість
  - пам'ять (memory) — історична пам'ять, політика пам'яті, герої Крут
activity_hints:
- type: reading
  focus: Порівняльний аналіз урядів революції
  source: Історичні документи
  items: 4
- type: essay-response
  focus: Чому Українська революція 1917-1921 зазнала поразки?
connects_to:
- hist-99 (Радянська Україна)
- hist-100 (Механізм терору)
prerequisites:
- hist-97 (Кінець визвольних змагань)
persona:
  voice: Senior Professor of History
  role: Archive Keeper
grammar:
- Аналітичний стиль
- Причинно-наслідкові конструкції
- Складнопідрядні речення
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Синтез: Українська революція** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Синтез: Українська революція

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Синтез: Українська революція"
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
