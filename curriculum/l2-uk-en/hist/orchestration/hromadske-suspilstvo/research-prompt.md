# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-137
level: HIST
sequence: 137
slug: hromadske-suspilstvo
version: '2.0'
title: Громадянське суспільство у війні
subtitle: Civil Society in Wartime
focus: history
pedagogy: CBI
phase: HIST.13 [Russian Aggression]
word_target: 5000
objectives:
- Учень може описати роль громадянського суспільства під час повномасштабного вторгнення
- Учень може пояснити діяльність волонтерських організацій
- Учень може проаналізувати трансформацію українського суспільства у війні
- Учень може обговорити взаємодію держави та громадянського суспільства
content_outline:
- section: 'Вступ: Нація, яка згуртувалася'
  points:
  - '24 лютого 2022: перший шок та реакція — черги до військкоматів і центрів здачі крові замість паніки; момент істини для
    суспільства — перехід до «мережі довіри»'
  - Чому українське суспільство виявилося сильним — [!myth-buster] імперський міф про українців як «анархічну націю» проти
    реальності високої самоорганізації (горизонтальні зв'язки)
  - 'Історичні корені громадянської активності — традиція віче, братств, Майданів як тренування навичок; date: Листопад 2013
    (Революція Гідності) — Євромайдан SOS'
  words: 850
- section: Волонтерський рух
  points:
  - 'Допомога армії: Come Back Alive, Повернись живим — [!history-bite] еволюція від бронежилетів до ліцензії на зброю; date:
    Травень 2014 (заснування фонду) — Тарас Чмут як лідер компетентної допомоги'
  - 'Гуманітарна допомога: евакуація, їжа, притулок — феномен переходу від «гуманітарки» до закупівлі високоточної зброї (супутник
    ICEYE, дрони Magura); кампанія «Народний Байрактар» (Фонд Притули)'
  - 'Медична допомога: волонтери-медики — батальйон «Госпітальєри» та Яна Зінкевич; евакуація з 2014 року'
  - 'IT-армія та інформаційний фронт — date: 26 лютого 2022 (створення IT Army); кібервійна цивільних фахівців — атаки на
    інфраструктуру ворога через Telegram-координацію'
  - Волонтери за кордоном — світова підтримка та роль діаспори у лобіюванні зброї
  words: 850
- section: Громадські організації
  points:
  - 'Правозахисні організації: документування злочинів — Центр Громадянських Свобод, Олександра Матвійчук; ініціатива «Трибунал
    для Путіна»'
  - 'Культурні ініціативи: збереження спадщини — [!context] Нобелівська премія миру 2022 як визнання суб''єктності; «культурний
    десант», евакуація експонатів'
  - Допомога переселенцям — організації, що виникли «знизу» (наприклад, «СпівДія»); інтеграція ВПО
  - Відбудова громад — місцеві ініціативи відновлення житла та інфраструктури
  words: 850
- section: Первинні джерела
  points:
  - Свідчення волонтерів — історії звичайних людей (бариста, бізнесмен), що змінили професію заради перемоги
  - Звіти громадських організацій — прозорість звітів як основа суспільної довіри
  - 'Соціологічні дослідження — 81% довіри до волонтерів (2023), вище ніж до церкви; source: ISNASU/Rating'
  - '[!quote] Валерій Залужний про «родинний зв''язок» армії та волонтерів як запоруку незламності — «У нашій єдності — сила
    й незламність української нації»'
  words: 850
- section: Держава і суспільство
  points:
  - Координація зусиль — [!decolonization] Україна (держава-партнер, Дія) проти Росії (держава-каратель, іноагенти); нагороди
    «Золоте серце»
  - Проблеми та виклики — бюрократія, спроби регулювання волонтерства, емоційне вигорання активістів; тиск силовиків (поодинокі
    випадки)
  - Майбутнє громадянського суспільства — роль як запобіжника авторитаризму у післявоєнний період
  words: 850
- section: 'Підсумок: Сила спільноти'
  points:
  - 'Українська модель стійкості — метафора «Бджолиний рій»: децентралізована координація без єдиного центру'
  - Уроки для світу — демократія як відповідальність громадян за фізичне виживання держави
  - Громадянське суспільство як фундамент демократії — [!culture] волонтерство як новий «суспільний стан» (social estate)
    сучасної України — подібно до козацтва
  words: 750
vocabulary_hints:
  required:
  - 'громадянське суспільство (civil society) — колокація: розвинене громадянське суспільство; не плутати з населенням'
  - 'волонтер (volunteer) — колокація: волонтерський рух, стати волонтером; 81% довіри'
  - благодійність (charity) — World Giving Index 2023 (Україна — 2 місце у світі)
  - мобілізація (mobilization) — не лише військова, а й суспільна/ресурсна; тотальна мобілізація
  - 'солідарність (solidarity) — колокація: соціальна солідарність, міжнародна солідарність'
  - координація (coordination) — горизонтальні зв'язки, мережева структура
  - 'ініціатива (initiative) — колокація: громадська ініціатива, низова ініціатива'
  - 'стійкість (resilience) — синонім: резильєнтність; здатність відновлюватися після шоку'
  recommended:
  - 'пожертва (donation) — синонім: донат (сленг); регулярний донат'
  - евакуація (evacuation) — медична евакуація (медевак)
  - 'переселенець (internally displaced person) — абревіатура: ВПО (внутрішньо переміщена особа)'
  - правозахисник (human rights defender) — документування воєнних злочинів
  - документування (documentation) — збір доказів для трибуналу
  - відбудова (reconstruction) — відбудова громад, відновлення інфраструктури
  - 'активіст (activist) — contested term: рушійна сила vs «грантоїд» (російський наратив)'
  - 'забезпечення (provision) — термін: забезпечення війська (замість «допомога»)'
activity_hints:
- type: reading
  focus: Свідчення українських волонтерів
  source: Сучасні медіа
  items: 4
- type: essay-response
  focus: Як громадянське суспільство допомагає Україні вистояти у війні?
connects_to:
- hist-138 (Міжнародна підтримка)
- 'hist-140 (Синтез: Війна за існування)'
prerequisites:
- hist-136 (Воєнна економіка)
persona:
  voice: Senior Professor of History
  role: Volunteer Coordinator
grammar:
- Теперішній час для опису актуальних процесів
- Минулий час для нещодавніх подій
- Соціологічна лексика
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Громадянське суспільство у війні** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Громадянське суспільство у війні

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Громадянське суспільство у війні"
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
