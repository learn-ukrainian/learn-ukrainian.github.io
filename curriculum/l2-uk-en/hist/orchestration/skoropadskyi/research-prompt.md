# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-091
level: HIST
sequence: 91
slug: skoropadskyi
version: '2.0'
title: 'Павло Скоропадський: Гетьманат'
subtitle: 'Pavlo Skoropadskyi: The Hetmanate'
focus: history
pedagogy: CBI
phase: HIST.9 [WWI & Revolution]
word_target: 5000
objectives:
- Учень може описати прихід до влади Павла Скоропадського
- Учень може пояснити політику та реформи Гетьманату
- Учень може проаналізувати суперечливу оцінку режиму Скоропадського
- Учень може оцінити культурні та освітні досягнення Гетьманату
content_outline:
- section: 'Вступ: Консервативна альтернатива'
  points:
  - '''29 квітня 1918: державний переворот'' — [!history-bite] «Гетьман із цирку» (З''їзд хліборобів у цирку Крутікова); 29
    квітня як унікальний день проголошення монархічного устрою у ХХ столітті'
  - Хто такий Павло Скоропадський — бойовий генерал, аристократ, нащадок брата гетьмана Івана Скоропадського; легітимність
    через історичну традицію, а не революційний популізм
  - Чому «Гетьманат» — «консервативна революція» проти соціалістичного хаосу Центральної Ради; зміна форми правління як відповідь
    на кризу
  words: 850
- section: Прихід до влади
  points:
  - Німецька окупація та криза УНР — [!context] «Втома від анархії» (селяни-власники підтримали генерала через неспроможність
    Ради забезпечити порядок); німці підтримали переворот post factum
  - З'їзд хліборобів — відбувся 29 квітня 1918 року в Києві у цирку Крутікова; безкровна зміна влади
  - Проголошення Української Держави — відновлення права приватної власності як фундаменту цивілізації (антитеза більшовизму)
  - Відносини з німцями — [!myth-buster] «Маріонетка німців?» (використання німецької сили як парасольки для розбудови інституцій;
    часто діяв всупереч німецьким інтересам, наприклад, у кримському питанні)
  words: 850
- section: Політика Гетьманату
  points:
  - Консервативний курс — опора на заможне селянство та відновлення приватної власності; ухвалено близько 400 законів за 7,5
    місяців
  - Земельне питання — скасування соціалізації землі; конфлікт між селянами та великими землевласниками
  - 'Українізація чи русифікація? — залучення старих фахівців (часто російськомовних) для ефективності апарату; цитата Дмитра
    Донцова: «На Україні будують Росію»; конфлікт з національно свідомими українцями'
  - '«Культурні досягнення: академія, університети» — [!culture] «Українізація зверху» (заснування УАН, Національної бібліотеки,
    Державного українського архіву, Українського театру драми і опери, 150 гімназій за 7,5 місяців)'
  - Падіння Гетьманату (грудень 1918) — Грамота про федерацію з Росією (14 листопада) як фатальний крок під тиском Антанти;
    антигетьманське повстання Директорії
  words: 850
- section: Первинні джерела
  points:
  - Грамота про Українську Державу — [!quote] «Цією грамотою я оголошую себе Гетьманом всієї України... Права приватної власності...
    відновлюються»
  - Документи Гетьманату — ухвалено близько 400 законів за 7,5 місяців (шалений темп законодавчої роботи)
  - 'Спогади Скоропадського — писані в еміграції; розчарування «вузьким українством» соціалістів; цитата: «Я хотів Україну,
    не ворожу Великоросії, а братню...» (ілюстрація складної ідентичності)'
  words: 850
- section: Деколонізаційний погляд
  points:
  - '«Суперечливі оцінки: «зрадник» чи «державник»?» — [!decolonization] переосмислення: від радянського таврування «білогвардієць»
    до визнання ефективності державного менеджменту'
  - Гетьманат у контексті революції — доказ, що український рух не був монолітно лівим/соціалістичним; спроба побудови модерної
    держави з традиційним укладом
  - Спадщина та уроки — інституційна пам'ять (Академія наук існує досі); ідея сильної правої держави
  words: 850
- section: 'Підсумок: Доля Скоропадського'
  points:
  - Еміграція та життя в Німеччині — Ванзеє, створення Гетьманського руху; спроби об'єднати українську діаспору
  - Загибель у 1945 році — смертельне поранення під час бомбардування союзників на станції Меттен (квітень 1945)
  - Оцінка сьогодні — символічний кінець епохи та постать, що об'єднує історію з сучасністю
  words: 750
vocabulary_hints:
  required:
  - гетьман (hetman) — оголошую себе Гетьманом всієї України; нащадок гетьманського роду; Гетьман Скоропадський
  - гетьманат (hetmanate) — Українська Держава (Гетьманат); період Гетьманату; політика Гетьманату
  - переворот (coup) — державний переворот 29 квітня; безкровний переворот; здійснити переворот
  - держава (state) — Українська Держава; розбудова держави; будувати державу
  - консерватизм (conservatism) — здоровий консерватизм; консервативна революція; консервативний уряд
  - реформа (reform) — земельна реформа; адміністративна реформа; проводити реформи
  - окупація (occupation) — німецька окупація; австро-німецькі війська; за підтримки окупаційної влади
  - еміграція (emigration) — політична еміграція; життя в еміграції; померти в еміграції
  recommended:
  - хлібороб (farmer) — З'їзд хліборобів; вільне козацтво; заможні хлібороби
  - грамота (decree) — Грамота до всього українського народу; видання грамоти; текст грамоти
  - академія (academy) — Українська академія наук (УАН); заснування академії; перший президент академії
  - університет (university) — відкриття нових університетів (Кам'янець-Подільський, Київ); державні університети
  - автономія (autonomy) — культурна автономія; широка автономія; межі автономії
  - реставрація (restoration) — реставрація порядку; реставрація приватної власності; реставрація монархії
activity_hints:
- type: reading
  focus: Грамота про Українську Державу
  source: Архівні документи
  items: 4
- type: critical-analysis
  focus: 'Верифікація фактів: Факти про Гетьманат'
  items: 5
- type: essay-response
  focus: Чи був Гетьманат Скоропадського українською державою?
connects_to:
- hist-93 (ЗУНР)
- hist-93 (Директорія УНР)
prerequisites:
- hist-91 (Центральна Рада)
persona:
  voice: Senior Professor of History
  role: Diplomat of the Ukrainian State
grammar:
- Минулий час в історичному наративі
- Політична та адміністративна лексика
- Складнопідрядні речення
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Павло Скоропадський: Гетьманат** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Павло Скоропадський: Гетьманат

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Павло Скоропадський: Гетьманат"
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
