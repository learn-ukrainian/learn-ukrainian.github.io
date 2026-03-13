# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-094
level: HIST
sequence: 94
slug: symon-petliura-revolution
version: '2.0'
title: 'Симон Петлюра: Головний отаман'
subtitle: 'Symon Petliura: The Supreme Commander'
focus: history
pedagogy: CBI
phase: HIST.9 [WWI & Revolution]
word_target: 5000
objectives:
- Учень може описати життя та діяльність Симона Петлюри
- Учень може пояснити роль Петлюри в Українській революції
- Учень може проаналізувати контроверсійні питання навколо Петлюри
- Учень може оцінити значення Петлюри для української державності
content_outline:
- section: 'Вступ: Символ боротьби'
  points:
  - Хто такий Симон Петлюра — (1879–1926), походив із полтавських міщан козацького роду — народжений 10 (22) травня 1879 року
    в Полтаві
  - Головний отаман армії УНР — не був професійним військовим, здобув авторитет харизмою та вірою — очолив антигетьманське
    повстання в листопаді 1918 року
  - Чому його пам'ятають — [!myth-buster] радянське кліше «бандита» проти реальності інтелектуала та державника — термін «петлюрівці»
    використовувався ворогами до 1940-х років
  words: 850
- section: Шлях до влади
  points:
  - Молодість та журналістика — [!context] редактор «Украинской Жизни» у Москві, формував ідею окремішності українців — вступ
    до Революційної української партії (РУП) у 1900 році
  - Участь у Центральній Раді — конфлікт реаліста-державника з пацифістом Винниченком — Петлюра виступав за створення власної
    армії, наперекір соціалістам-утопістам
  - Військовий міністр — створення армії з нуля (Гайдамацький кіш) в умовах війни — голова УГВК (червень 1917), Генеральний
    секретар військових справ
  - Голова Директорії — фактичний одноосібний лідер з травня 1919 року — обраний головою 9 травня 1919 року
  words: 850
- section: Війна за незалежність
  points:
  - 'Боротьба на кількох фронтах — [!history-bite] «Трикутник смерті» 1919 року: більшовики, білі, поляки та тиф — ситуація
    на Поділлі, коли армія була затиснута з усіх боків'
  - 'Союз з Польщею (1920) — Варшавський договір: важкий компроміс (Галичина) заради порятунку Великої України — підписано
    21 квітня 1920 року (союз Пілсудський-Петлюра)'
  - Київська операція — спільний парад 7 травня 1920 року, коротка надія перед «дивом на Віслі» — звільнення Києва об'єднаними
    військами
  - Поразка та еміграція — відступ за Збруч, інтернування, продовження боротьби в екзилі — листопад 1920 року, перехід на
    територію Польщі
  - Зимовий похід армії УНР — партизанська тактика в тилу ворога — спроба зберегти ядро армії для майбутньої боротьби
  words: 850
- section: Первинні джерела
  points:
  - 'Накази та звернення Петлюри — [!quote] Наказ № 131 проти погромів: «Кара на смерть погромникам» — виданий 26 серпня 1919
    року, вимагав розстрілу провокаторів'
  - 'Листування — листи до дружини свідчать про глибоку віру в перемогу навіть у безвиході — цитата: «Ми не можемо перестати
    боротися, бо це значить зрадити націю»'
  - Спогади соратників — аскетизм, відсутність прагнення матеріальних благ — жив у вагоні потяга, постійно перебував на фронті
  words: 850
- section: Деколонізаційний погляд
  points:
  - 'Радянський наратив: «петлюрівщина» — [!decolonization] термін-тавро для дегуманізації всього українського руху опору
    — аналог сучасного «бандерівці», створений Москвою'
  - 'Контроверсії: єврейські погроми — [!myth-buster] роль «чорних сотень» та провокаторів; Міністерство єврейських справ
    УНР — унікальна інституція в світовій практиці'
  - 'Реальність: складна постать складної епохи — лідер нації без держави, змушений обирати між поганим і найгіршим — державник,
    що будував інституції під вогнем'
  words: 850
- section: 'Підсумок: Париж, 1926'
  points:
  - Вбивство в Парижі — спецоперація ДПУ для ліквідації небезпечного лідера еміграції — 25 травня 1926 року, вбитий агентом
    Самуїлом Шварцбардом
  - Суд над Шварцбардом — перетворення суду над вбивцею на суд над жертвою за гроші Москви — радянські агенти фінансували
    захист і фабрикували свідчення
  - Петлюра в українській пам'яті — [!culture] похорон як маніфестація нескореності; символ боротьби — тисячі українців на
    похороні в Парижі
  words: 750
vocabulary_hints:
  required:
  - отаман (ataman) — Головний отаман військ УНР; очолив повстання
  - Директорія (Directory) — голова Директорії (фактично одноосібний лідер)
  - армія (army) — Армія УНР, розбудова збройних сил; Гайдамацький кіш
  - незалежність (independence) — війна за незалежність; символ боротьби
  - боротьба (struggle) — символ національно-визвольної боротьби; продовження боротьби в екзилі
  - еміграція (emigration) — політична еміграція, уряд в екзилі; лідер еміграції
  - союз (alliance) — військово-політичний союз із Польщею; Варшавський договір
  - вбивство (assassination) — політичне вбивство агентом спецслужб; вбитий 25 травня 1926
  recommended:
  - журналіст (journalist) — публіцистична діяльність, редактор журналу «Украинская Жизнь»
  - військовий міністр (war minister) — генеральний секретар військових справ; голова УГВК
  - операція (operation) — Київська операція 1920 року; спецоперація ДПУ
  - поразка (defeat) — причини поразки визвольних змагань; Трикутник смерті
  - погром (pogrom) — боротьба з єврейськими погромами, Наказ № 131; смертна кара погромникам
  - суд (trial) — судовий процес над Шварцбардом; суд над жертвою
activity_hints:
- type: reading
  focus: Звернення Петлюри до армії
  source: Архівні документи
  items: 4
- type: essay-response
  focus: Чому постать Петлюри залишається контроверсійною?
connects_to:
- hist-95 (Більшовицько-українська війна)
- hist-97 (Кінець визвольних змагань)
prerequisites:
- hist-93 (Директорія УНР)
persona:
  voice: Senior Professor of History
  role: Chief of Staff
grammar:
- Минулий час у біографічному наративі
- Військова та політична лексика
- Складнопідрядні речення
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Симон Петлюра: Головний отаман** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Симон Петлюра: Головний отаман

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Симон Петлюра: Головний отаман"
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
