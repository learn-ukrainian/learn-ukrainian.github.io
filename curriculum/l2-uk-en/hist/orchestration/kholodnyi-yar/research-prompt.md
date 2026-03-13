# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-096
level: HIST
sequence: 96
slug: kholodnyi-yar
version: '2.0'
title: 'Холодний Яр: Останній опір'
subtitle: 'Kholodny Yar: The Last Resistance'
focus: history
pedagogy: CBI
phase: HIST.9 [WWI & Revolution]
word_target: 5000
objectives:
- Учень може описати повстанський рух Холодного Яру
- Учень може пояснити причини та характер повстання
- Учень може проаналізувати роль Юрія Горліса-Горського
- Учень може оцінити значення Холодного Яру для національної пам'яті
content_outline:
- section: 'Вступ: Республіка в лісах'
  points:
  - 'Холодний Яр: географія та символіка — ландшафт як природна фортеця (яри довжиною 250 км, реліктовий ліс, підземні ходи);
    Мотронинський монастир як духовний і організаційний центр'
  - 'Селянське повстання чи національний рух? — відмінність від стихійного бунту: організована структура та підпорядкування
    УНР; держава в державі з адміністрацією та судом'
  - Чому Холодний Яр став легендою — гасло «Воля України або смерть!» на чорному прапорі; спадкоємність від гайдамаччини (Коліївщини
    1768 року, освячення ножів)
  words: 850
- section: Витоки повстання
  points:
  - 'Контекст: поразка УНР — 1919-1920 роки, втрата централізованого контролю, перехід до партизанської боротьби; learner
    error: громадянська війна vs російсько-українська війна'
  - 'Більшовицька окупація та терор — політика «воєнного комунізму», продрозкладка (грабунок селян), звірства ЧК, наруга над
    церквою; learner error: комунізм = лише ідеологія (тут це окупаційний режим)'
  - 'Селяни беруть зброю — соціальна база: заможні селяни-власники, колишні солдати Першої світової, інтелігенція (вчителі)
    — рух середнього класу проти люмпенізації'
  - 'Формування повстанських загонів — роль братів Чучупаків (Василь — Головний отаман); перший загін охорони монастиря (1918,
    22 особи на прохання ігумені); engagement hook: [!history-bite] про Мотронинський монастир як центр гайдамаччини'
  words: 850
- section: Повстанська республіка (1919-1922)
  points:
  - 'Організація та командири — Василь Чучупак (загинув 18 березня 1920), Чорний Ворон (Іван Чорновус/Микола Скляр); чітка
    ієрархія: полки, сотні, штаб інформаційного бюро; engagement hook: [!myth-buster] про організованість vs хаос'
  - Юрій Горліс-Горський та Юрій Тютюнник — Горліс-Горський як осавул і хроніст; роль Тютюнника у координації (Зимовий похід)
  - Бойові операції та тактика — рейди, засідки, тактика «бий і тікай», розвідка та підтримка місцевого населення (15 тисяч
    повстанців у пік розквіту)
  - «Зелена армія» та зв'язок з УНР — ідентифікація себе як частини регулярної армії УНР, а не анархістів чи «бандитів»; відозва
    «Брати селяни і козаки» (4 червня 1919)
  - Придушення повстання — спецоперація ЧК «Заповіт» (29 вересня 1922, арешт отаманів у Звенигородці через фальшивий з'їзд);
    останній бій у Лук'янівській в'язниці (9 лютого 1923)
  words: 850
- section: Первинні джерела
  points:
  - '«Холодний Яр» Юрія Горліса-Горського — «холодноярська біблія», жива мова діалогів, опис психології повстанців; include
    quote: «Нам потрібний не мрійний пав''ячий хвіст, а вовчі зуби»'
  - Спогади учасників — свідчення вцілілих (наприклад, Михайла Дорошенка); важливість усної історії та збереження пам'яті
    про «лісову державу»
  - 'Більшовицькі документи про «бандитизм» — доповідні ЧК про неможливість ліквідації руху («бандитизм неліквідований»);
    include quote: «Коли я впаду... мою кров вип''є рідна земля»'
  words: 850
- section: Деколонізаційний погляд
  points:
  - 'Радянський міф про «куркулів та бандитів» — конструювання образу ворога; підміна понять (національно-визвольний рух ->
    бандитизм); engagement hook: [!decolonization] про термінологію (бандити vs повстанці)'
  - 'Реальність: національно-визвольний рух — масова підтримка, державницька ідеологія, не класова боротьба (села повставали
    цілком проти окупації)'
  - 'Холодний Яр та УПА: паралелі — тяглість традиції опору; ті самі методи, ворог та ідея; діти холодноярців в УПА'
  words: 850
- section: 'Підсумок: Пам''ять та відродження'
  points:
  - Заборонена пам'ять за радянських часів — знищення могил, закриття монастиря, табу на тему; самвидав книги Горліса-Горського
  - Відродження після 1991 року — роман Василя Шкляра «Чорний Ворон» як культурний феномен; відновлення вшанувань та реабілітація
    отаманів
  - 'Холодний Яр як символ спротиву — 93-тя ОМБр «Холодний Яр» ЗСУ; сучасна війна як продовження боротьби 1920-х; engagement
    hook: [!culture] про 93-тю бригаду'
  words: 750
vocabulary_hints:
  required:
  - повстання (uprising) — збройне повстання, селянське повстання, вибухнуло повстання
  - повстанці (insurgents) — холодноярські повстанці, загони повстанців, армія повстанців
  - опір (resistance) — чинити опір, збройний опір, рух опору, останній опір
  - партизани (partisans) — партизанська війна, лісові партизани, партизанська тактика
  - командир (commander) — командир полку, талановитий командир, наказ командира
  - загін (detachment) — повстанський загін, озброєний загін, сформувати загін
  - окупація (occupation) — більшовицька окупація, режим окупації, боротьба з окупацією
  - придушення (suppression) — жорстоке придушення, придушення повстання, операція з придушення
  recommended:
  - засідка (ambush) — влаштувати засідку, потрапити в засідку, несподівана засідка
  - рейд (raid) — кінний рейд, бойовий рейд по тилах ворога, Зимовий похід
  - підпілля (underground) — піти в підпілля, діяти в підпіллі, українське підпілля
  - отаман (otaman/leader) — Головний отаман, виборний отаман, славетний отаман
  - терор (terror) — червоний терор, політика терору, жертви терору
  - легенда (legend) — жива легенда, легендарний отаман, народна легенда
  - гайдамаки (haidamaky) — нащадки гайдамаків, нові гайдамаки, полк гайдамаків
  - монастир (monastery) — Мотронинський монастир, оборона монастиря, стіни монастиря
  - яр (ravine) — система ярів, сховатися в яру, лісовий яр
  - чекісти (chekists) — агенти ЧК, бій з чекістами, підступність чекістів
activity_hints:
- type: reading
  focus: Фрагменти книги «Холодний Яр»
  source: Юрій Горліс-Горський
  items: 4
- type: critical-analysis
  focus: 'Спростування міфів: Міфи та правда про Холодний Яр'
  items: 5
- type: essay-response
  focus: Чому більшовики називали повстанців «бандитами»?
connects_to:
- hist-98 (Українізація)
- hist-107 (УПА)
prerequisites:
- hist-96 (Голод 1921-1923)
persona:
  voice: Senior Professor of History
  role: Forest Partisan
grammar:
- Минулий час у воєнному наративі
- Військова та повстанська лексика
- Складнопідрядні речення
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Холодний Яр: Останній опір** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Холодний Яр: Останній опір

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Холодний Яр: Останній опір"
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
