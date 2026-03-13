# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-107
level: HIST
sequence: 107
slug: upa
version: '2.0'
title: 'УПА: Збройний опір'
subtitle: 'UPA: The Armed Resistance'
focus: history
pedagogy: CBI
phase: HIST.10 [WWII & Soviet Terror]
word_target: 5000
objectives:
- Учень може описати створення та діяльність УПА
- Учень може пояснити концепцію «війни на два фронти»
- Учень може проаналізувати контроверсійні аспекти історії УПА
- Учень може оцінити роль УПА в боротьбі за незалежність
content_outline:
- section: 'Вступ: Війна на два фронти'
  points:
  - '1942: створення УПА — 14 жовтня (символічна дата), наказ ч. 1/47, Поліська Січ як предтеча'
  - Проти нацистів і більшовиків — концепція «Між двома вогнями», єдина армія проти двох тоталітарних імперій без зовнішньої
    допомоги
  - 'Чому збройний опір — стратегічна мета: не стати розмінною монетою після війни; hook: [!context] про унікальність ситуації
    (воювали проти двох імперій одночасно)'
  words: 850
- section: Створення та організація
  points:
  - ОУН та шлях до УПА — роль ОУН(б) у формуванні єдиної структури восени 1942; інтеграція загонів; Поліська Січ (Бульба-Боровець)
    як попередниця
  - 'Командири: Шухевич, Клячківський — Дмитро Клячківський (Клим Савур) на Волині, Роман Шухевич (Тарас Чупринка) як творець
    регулярної структури з січня 1944'
  - 'Структура та організація — УПА-Північ, УПА-Захід, УПА-Південь; «лісові брати» мали власну валюту (бофони) та шпиталі
    (Червоний Хрест УПА); hook: [!history-bite] про підпільну державу'
  - 'Ідеологія та цілі — Присяга воїна УПА: «боротись за повне визволення» (червень 1943); листівки до народів Кавказу та
    Азії («Чому ти стріляєш в брата?»)'
  words: 850
- section: Бойовий шлях
  points:
  - 'Боротьба з німцями — Весна 1943, Колківська республіка (держава без німців), порятунок «остарбайтерів»; статистика: >12
    тис. вбитих окупантів; hook: [!myth-buster] про співпрацю з нацистами'
  - Боротьба з радянською владою — Бій під Гурбами (квітень 1944) — найбільша відкрита битва (5 тис. проти 30 тис. НКВС);
    перехід до тактики малих груп (криївки)
  - 'Волинська трагедія — липень 1943 (апогей), складний етнічний конфлікт, жертви серед цивільних з обох сторін; контекст:
    пацифікація 1930-х та німецькі провокації'
  - Операція «Вісла» — 28 квітня 1947, депортація 140 тис. українців з Закерзоння, спроба УПА захистити населення (2 тис.
    проти 20 тис. польських військ)
  - Опір до 1950-х років — останній бій групи «Петра» (1960) на Тернопільщині, арешт Василя Кука (1954)
  words: 850
- section: Первинні джерела
  points:
  - Документи УПА — Накази ГВШ, звіти про бої, дереворити Ніла Хасевича як візуальна пропаганда, що обійшла світ
  - 'Спогади учасників — багатотомний «Літопис УПА», щоденники командирів; hook: [!quote] з Декалогу («Здобудеш Українську
    Державу, або згинеш у боротьбі за неї»)'
  - Радянські документи — звіти спецгруп НКВС про боротьбу з «бандитизмом»; використання провокаторів, перевдягнених в упівців
  words: 850
- section: Деколонізаційний погляд
  points:
  - 'Радянський наратив: «бандерівці» — міф про «німецьких посіпак» vs. реальність пакту Молотова-Ріббентропа (СРСР як союзник
    Гітлера); hook: [!decolonization] про термінологію'
  - Контроверсії та складна правда — Нюрнберзький процес не визнав УПА злочинною; порівняння з ірландським (IRA) чи польським
    (AK) підпіллям
  - УПА в сучасній пам'яті — визнання борцями за незалежність на рівні держави; спростування імперських міфів про «банди»
  words: 850
- section: 'Підсумок: Спадщина'
  points:
  - Загибель Шухевича (1950) — бій у Білогорщі 5 березня, символ незламності («Мертві сорому не мають»); не здався живим
  - Визнання УПА — реабілітація учасників, спростування радянських міфів; кінець організованого опору в 1954
  - 'УПА та сучасна війна — спадкоємність традицій: «Слава Україні! Героям Слава!», червоно-чорний прапор у ЗСУ як символ
    боротьби до перемоги; hook: [!reflection] про спадок'
  words: 750
vocabulary_hints:
  required:
  - 'УПА (UPA) — Ukrainian Insurgent Army, key term; date: 14.10.1942'
  - повстанці (insurgents) — often referred to as «лісові брати» (forest brothers); not «бандити»
  - опір (resistance) — збройний опір (armed resistance) against occupiers; рух опору (resistance movement)
  - 'партизани (partisans) — note: in Soviet context «партизани» were enemies (Red partisans), UPA were «повстанці»'
  - 'окупація (occupation) — подвійна окупація (double occupation: Nazi and Soviet); німецька/радянська окупація'
  - незалежність (independence) — здобути незалежність (to gain independence); боротьба за незалежність
  - командир (commander) — Головнокомандувач (Commander-in-Chief) Роман Шухевич
  - підпілля (underground) — піти в підпілля (to go underground); українське підпілля
  recommended:
  - бункер (bunker) — also криївка (hideout), essential for survival in 1944-1950s
  - криївка (hideout) — secret underground shelter masked in forests or houses; жити в криївці
  - диверсія (sabotage) — акти саботажу (acts of sabotage) against German administration
  - пропаганда (propaganda) — ворожа пропаганда (enemy propaganda) vs. повстанські листівки
  - репресії (repressions) — масові репресії НКВС (mass NKVD repressions); каральні акції
  - депортація (deportation) — примусове виселення (forced eviction), e.g., Operation Vistula (1947)
  - бофони (bofons) — повстанські гроші (insurgent currency); бойовий фонд
  - присяга (oath) — скласти присягу (to take an oath); текст присяги
  - етнічний конфлікт (ethnic conflict) — vs. «різанина» (massacre); Волинська трагедія
activity_hints:
- type: reading
  focus: Документи та спогади учасників УПА
  source: Архівні матеріали
  items: 4
- type: essay-response
  focus: Чому історія УПА залишається контроверсійною?
connects_to:
- hist-107 (Завершення війни)
- hist-109 (Депортації)
prerequisites:
- hist-105 (ОУН)
persona:
  voice: Senior Professor of History
  role: Bunker Commander
grammar:
- Минулий час у воєнному наративі
- Військова лексика
- Пасивні конструкції
register: публіцистичний

```

---

## PART 1: Deep Research

Research **УПА: Збройний опір** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: УПА: Збройний опір

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "УПА: Збройний опір"
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
