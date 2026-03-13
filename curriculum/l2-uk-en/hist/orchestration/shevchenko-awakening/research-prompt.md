# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-081
level: HIST
sequence: 81
slug: shevchenko-awakening
version: '2.0'
title: Шевченко і пробудження
subtitle: Shevchenko and the National Awakening
focus: history
pedagogy: CBI
phase: HIST.8 [Imperial Era]
word_target: 5000
objectives:
- Учень може описати життєвий шлях Тараса Шевченка
- Учень може пояснити роль Шевченка в українському національному пробудженні
- 'Учень може проаналізувати ключові твори: «Заповіт», «Кавказ»'
- Учень може оцінити вплив Шевченка на формування української ідентичності
content_outline:
- section: 'Вступ: Від кріпака до пророка'
  points:
  - Народження в кріпацтві (1814) — 9 березня, с. Моринці, родина кріпаків Енгельгардта; сирота з 11 років
  - Шевченко як національний символ — [!myth-buster] руйнування стереотипу «старого діда в шапці», образ молодого успішного
    художника-денді, душі компанії до арешту
  - Чому його називають пророком — слова, що справджувалися (крах імперії, відродження України); феномен «Пророка» у формуванні
    модерної нації
  words: 850
- section: Життєвий шлях
  points:
  - Дитинство в кріпацтві — сирота, школа у дяка, служба «козачком» у пана Енгельгардта (подорожі до Вільна, Петербурга)
  - Викуп з неволі (1838) — [!context] «краудфандинг» еліти (Жуковський, Брюллов, Венеціанов) через лотерею; ціна свободи
    2500 рублів (еквівалент 45 кг срібла)
  - Навчання в Академії мистецтв — учень Карла Брюллова, успішна кар'єра художника, академік гравюри
  - «Кобзар» (1840) — вихід першого видання (8 творів), миттєва слава; перехід від фольклоризму до національного маніфесту
  - Кирило-Мефодіївське братство — 1846 рік, радикальне крило, ідея слов'янської федерації з центром у Києві; збірка «Три
    літа»
  - 'Арешт і заслання (1847-1857) — резолюція Миколи І: «під найсуворіший нагляд із забороною писати й малювати», Орська фортеця,
    Новопетровське укріплення, Аральська експедиція'
  - Останні роки — повернення, звання академіка гравюри, арешт 1859 року, смерть 10 березня 1861 року за день до дня народження
  words: 850
- section: Ключові твори
  points:
  - '«Заповіт»: національна молитва — написаний у Переяславі (1845) під час хвороби, програма дій («Кайдани порвіте»); став
    неофіційним гімном'
  - '«Кавказ»: антиколоніальна поема — [!decolonization] присвята Якову де Бальмену, солідарність поневолених народів («Не
    нам на прю з тобою стати!»), образ Прометея'
  - '«Сон»: критика імперії — політична сатира («У кожного своя доле...»), гротескні образи «ведмедя» Петра І та «чаплі» Катерини
    ІІ'
  - Мова та стиль Шевченка — синтез фольклорної пісенності, біблійної патетики та політичної гостроти; створення літературної
    мови
  words: 850
- section: Первинні джерела
  points:
  - Уривки з «Кобзаря» — [!quote] «Борітеся — поборете! Вам Бог помагає!», «В своїй хаті своя й правда, і сила, і воля»
  - Щоденник Шевченка — [!quote] записи про огиду до солдафонщини та муштри; писаний російською для інтелігенції, але демонструє
    європейський рівень мислення
  - Листування — лист до брата Микити із закликом не цуратися рідної мови («Не цурайся, брате...»)
  words: 850
- section: Деколонізаційний погляд
  points:
  - 'Імперський наратив: «регіональний поет» — зведення до етнографічного курйозу («малоросійський поет»), намагання маргіналізувати
    вплив'
  - 'Реальність: творець нації — [!history-bite] формування ідеї державної самостійності, чітке розмежування «ми» (Україна)
    і «вони» (імперія)'
  - Шевченко проти імперії — слово як зброя, якої імперія боялася більше за повстання (суворість вироку)
  words: 850
- section: 'Підсумок: Культ Шевченка'
  points:
  - Смерть і поховання (1861) — похорон у Петербурзі, перепоховання 22 травня на Чернечій горі в Каневі, виконання «Заповіту»
    студентами
  - 'Шевченко в радянський час — спотворення образу: атеїст, революціонер-демократ, «селянський поет», замовчування націоналізму'
  - 'Шевченко сьогодні — [!culture] символ боротьби: на Майдані, у шоломі й бронежилеті (2022); рекордсмен за кількістю пам''ятників
    у світі; «Кобзар» поруч з Євангелієм у хаті'
  words: 750
vocabulary_hints:
  required:
  - кріпак (serf) — народитися кріпаком, викуп з кріпацтва, доля кріпака
  - поет (poet) — більше ніж поет, національний пророк, народний поет
  - пробудження (awakening) — національне пробудження, зростання свідомості
  - Кобзар (Kobzar) — назва збірки (1840), статус поета, символ українства
  - заслання (exile) — десятирічне заслання, заборона писати й малювати, солдатчина
  - пророк (prophet) — слова, що справджуються; батько нації; феномен пророцтва
  - нація (nation) — творець модерної української нації, ідея державної самостійності
  - творчість (creative work) — заборона творчості, малярська творчість, літературна спадщина
  recommended:
  - викуп (ransom) — ціна волі (2500 рублів), лотерея, краудфандинг еліти
  - братство (brotherhood) — Кирило-Мефодіївське товариство, ідеї федерації
  - імперія (empire) — тюрма народів, критика самодержавства, російський імперіалізм
  - воля (freedom) — свята воля, боротьба за волю, «В своїй хаті своя правда...»
  - поема (poem) — сатирична поема «Сон», поема-послання, антиколоніальна поема «Кавказ»
  - могила (grave) — «Як умру, то поховайте...», Чернеча гора, національна святиня
activity_hints:
- type: reading
  focus: Уривки з творів Шевченка
  source: Кобзар
  items: 4
- type: essay-response
  focus: Чому Шевченка називають творцем української нації?
connects_to:
- hist-82 (Валуєвський та Емський укази)
- hist-84 (Михайло Драгоманов)
prerequisites:
- hist-80 (Кирило-Мефодіївське братство)
persona:
  voice: Senior Professor of History
  role: Brotherhood Member
grammar:
- Минулий час у біографічному наративі
- Цитати та пряма мова
- Дієприкметникові звороти
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Шевченко і пробудження** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Шевченко і пробудження

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Шевченко і пробудження"
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
