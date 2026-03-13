# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-129
level: HIST
sequence: 129
slug: tomos
version: '2.0'
title: 'Томос: Духовна незалежність'
subtitle: 'Tomos: Spiritual Independence'
focus: history
pedagogy: CBI
phase: HIST.12 [Independence & Modern Era]
word_target: 5000
objectives:
- Учень може описати історію боротьби за церковну незалежність
- Учень може пояснити значення Томосу про автокефалію
- Учень може проаналізувати роль церкви в українській ідентичності
- Учень може оцінити геополітичне значення Томосу
content_outline:
- section: 'Вступ: Церква та держава'
  points:
  - 'Чому церковна незалежність важлива — концепція «Незалежна держава — незалежна церква»; релігія як стовп національної
    ідентичності; engage hook: [!context] про автокефалію — повна адміністративна незалежність, аналог державного суверенітету'
  - '1686: підпорядкування Москві — корінь проблеми; початок русифікації літургії та освіти (Києво-Могилянська академія) —
    незаконна анексія Київської митрополії, що належала Константинополю'
  - Шлях до Томосу — спроби 1917-1921 (Липківський, УАПЦ), 1942, 1990-ті та їх жорстоке придушення Москвою — історична тяглість
    боротьби за автокефалію
  words: 850
- section: Історія українського православ'я
  points:
  - 'Київська митрополія — заснована 988 р., є Матір''ю для московського православ''я; engage hook: [!myth-buster] про «добровільне
    приєднання» 1686 року — Москва отримала автокефалію лише у 1448 році (самопроголошення), а визнання — у 1589'
  - Підпорядкування Московському патріархату — хабар патріарху Діонісію IV (соболі та золото); порушення умови поминання Вселенського
    патріарха як першого
  - Розкол після 1991 — звернення Філарета (Денисенка) про автокефалію, відмова Москви та накладення анафеми — використання
    церковних канонів як політичної зброї
  - УПЦ КП, УАПЦ, УПЦ МП — УПЦ КП як невизнана але патріотична vs УПЦ МП як інструмент «русского міра» — просування ідеї «триєдиного
    народу»
  words: 850
- section: Здобуття Томосу (2018-2019)
  points:
  - Звернення Порошенка до Варфоломія — квітень 2018, єдність влади та церкви; протидія Росії (дипломатія, кібератаки групи
    Fancy Bear, тиск на ієрархів)
  - 'Об''єднавчий собор 15 грудня 2018 — Софія Київська; розпуск УПЦ КП та УАПЦ; участь двох ієрархів УПЦ МП (Симеон, Олександр);
    engage hook: [!history-bite] про напругу очікування — закриті двері Софії'
  - Митрополит Епіфаній — обрання молодого предстоятеля без радянського минулого (КДБ); знання грецької мови, що полегшує
    комунікацію з Фанаром
  - Вручення Томосу 6 січня 2019 — Фанарі, церква Св. Георгія; перша офіційна молитва українською мовою на цьому рівні — співслужіння
    Варфоломія та Епіфанія
  - Реакція Москви — заперечення, невизнання, ярлик «Стамбульська парафія» — розрив євхаристійного спілкування Москви з Константинополем
    (самоізоляція РПЦ)
  words: 850
- section: Первинні джерела
  points:
  - 'Текст Томосу — визнання автокефальної церкви «духовною донькою»; обмеження діаспори; engage hook: [!quote] з Томосу про
    самоврядність — «визнаємо та проголошуємо встановлену... Автокефальну Церкву»'
  - Виступи патріарха Варфоломія — метафора про «зиму схизми» та відновлення справедливості — «дощ ізоляції припинився, і
    квіт надії з'явився»
  - Документи Собору — Статут ПЦУ за грецькою демократичною традицією — відмінність від авторитарної моделі РПЦ
  words: 850
- section: Деколонізаційний погляд
  points:
  - 'Російський наратив: «розкол» — маніпуляція страхом «безблагодатності»; engage hook: [!decolonization] про термін «розкол»
    (raskol) як інструмент контролю — тавро для тих, хто прагне незалежності'
  - 'Реальність: духовна деколонізація — Москва сама була в розколі 141 рік (1448-1589); Томос як відновлення історичної справедливості,
    а не створення нового'
  - Церква як інструмент імперії — міф про «триєдиний народ», заперечення української мови в літургії — концепція «канонічної
    території» як виправдання агресії
  words: 850
- section: 'Підсумок: Після Томосу'
  points:
  - Перехід парафій — хвилі 2019 (~500 громад) та 2022 років (>1000 громад); зміна юрисдикції як свідомий вибір громад (голосування)
  - Війна та церква — втрата легітимності УПЦ МП через колабораціонізм та благословення війни патріархом Кирилом; Собор у
    Феофанії (2022) як спроба мімікрії «незалежності»
  - 'Значення для ідентичності — капеланство, волонтерство; перехід на новоюліанський календар (Різдво 25 грудня) як цивілізаційний
    вибір «Геть від Москви»; engage hook: [!culture] про календар — синхронізація з Європою'
  words: 750
vocabulary_hints:
  required:
  - 'Томос (Tomos) — патріарша грамота про автокефалію; collocations: надання Томосу, отримання Томосу, підписання Томосу'
  - 'автокефалія (autocephaly) — повна адміністративна незалежність церкви; collocations: надати автокефалію, визнати автокефалію'
  - 'церква (church) — як інституція та спільнота вірян; collocations: помісна церква, єдина церква'
  - патріарх (patriarch) — титул глави помісної церкви (Варфоломій, Філарет, Кирило); Вселенський патріарх
  - митрополит (metropolitan) — титул глави ПЦУ (Епіфаній); Митрополит Київський і всієї України
  - 'собор (council) — зібрання єпископів (Об''єднавчий собор); collocations: скликати собор, провести собор'
  - православ'я (Orthodoxy) — східна гілка християнства; українське православ'я
  - незалежність (independence) — у контексті духовної свободи від Москви; духовна незалежність
  recommended:
  - парафія (parish) — церковна громада; перехід парафій, релігійна громада
  - єпископ (bishop) — вищий священнослужитель; участь єпископів
  - канонічний (canonical) — такий, що відповідає церковним законам; канонічна територія, канонічна церква
  - духовенство (clergy) — сукупність священнослужителів; українське духовенство
  - розкол (schism) — церковне розділення; імперський штамп, подолання розколу
  - деколонізація (decolonization) — звільнення від імперського впливу в церкві; духовна деколонізація
  - схизма (schism) — церковний розкол (термін Варфоломія); зима схизми
  - предстоятель (primate) — глава помісної церкви; обрання предстоятеля
activity_hints:
- type: reading
  focus: Текст Томосу
  source: Церковні документи
  items: 4
- type: critical-analysis
  focus: 'Верифікація фактів: Факти про автокефалію'
  items: 5
- type: essay-response
  focus: Чому отримання Томосу називають духовною незалежністю?
connects_to:
- hist-125 (Мовна політика)
- hist-127 (Революція Гідності) [контекст]
prerequisites:
- hist-123 (Україна 2014-2019)
persona:
  voice: Senior Professor of History
  role: Ecclesiastical Scholar
grammar:
- Минулий час в історичному наративі
- Церковна та релігійна лексика
- Складнопідрядні речення
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Томос: Духовна незалежність** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Томос: Духовна незалежність

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Томос: Духовна незалежність"
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
