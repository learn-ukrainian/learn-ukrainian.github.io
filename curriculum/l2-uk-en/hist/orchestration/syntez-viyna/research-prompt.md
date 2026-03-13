# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-140
level: HIST
sequence: 140
slug: syntez-viyna
version: '2.0'
title: 'Синтез: Війна за існування'
subtitle: 'Synthesis: War for Existence'
focus: history
pedagogy: CBI
phase: HIST.13 [Full-Scale War]
word_target: 5000
objectives:
- Учень може синтезувати знання про російсько-українську війну 2014-2024
- Учень може пояснити причини та цілі російської агресії
- Учень може проаналізувати чинники українського спротиву
- Учень може оцінити глобальне значення війни
content_outline:
- section: 'Вступ: Війна за майбутнє'
  points:
  - '2014-2024: десятиліття війни — кульмінація багатовікових намагань Росії знищити українську незалежність; engagement hook:
    [!context] про столітнє протистояння як екзистенційну боротьбу, що почалася задовго до 2014'
  - 'Від Криму до повномасштабного вторгнення — трансформація гібридної агресії у тотальну війну на знищення; key date: 20
    лютого 2014 (початок агресії)'
  - 'Чому ця війна змінює світ — зіткнення цивілізацій: демократія проти тиранії; include concept: Україна як щит Європи'
  words: 850
- section: Етапи війни
  points:
  - 'Анексія Криму (2014) — початок агресії 20 лютого 2014 року, «зелені чоловічки» та імітація референдуму; contested term:
    «воссоединение» vs «тимчасова окупація»'
  - 'Війна на Донбасі (2014-2022) — оголошення АТО 14 квітня 2014 року, Мінські угоди як спроба заморозити конфлікт; contrast:
    АТО/ООС vs повномасштабна війна'
  - 'Повномасштабне вторгнення (2022) — спроба бліцкригу «Київ за три дні» та героїчна оборона столиці, Чернігова, Маріуполя;
    date: 24 лютого 2022'
  - 'Оборона та контрнаступ — звільнення Півночі (квітень 2022), блискавичний Харківський контрнаступ (вересень 2022) та звільнення
    Херсона (11 листопада 2022); engagement hook: [!history-bite] про Харківську операцію як зразок оперативного мистецтва'
  words: 850
- section: Причини та мотиви
  points:
  - 'Імперська ідеологія Росії — невизнання суб''єктності України та прагнення відновити «імперську велич»; source concept:
    «рашизм» (NISS)'
  - '«Русский мир» та неоколоніалізм — використання мови та культури як зброї; engagement hook: [!myth-buster] про міф «захист
    російськомовних» як прикриття для етноциду'
  - 'Страх перед українською демократією — успішна європейська Україна як екзистенційна загроза для авторитарного режиму Путіна;
    destroys myth: «один народ»'
  - 'Геополітичні розрахунки Кремля — намагання змінити світовий порядок силою; goal: знищення української державності'
  words: 850
- section: Чинники спротиву
  points:
  - 'Українська ідентичність та нація — усвідомлення себе окремою політичною нацією, вільною від імперського диктату; include
    quote (Valerii Zaluzhnyi): «Ми не маємо права перекласти цю війну на наших дітей»'
  - 'Реформи армії після 2014 — впровадження понад 300 стандартів НАТО, створення професійного сержантського корпусу та ССО;
    fact: бойовий досвід АТО/ООС'
  - 'Громадянське суспільство — феномен волонтерства (від шкарпеток до супутників); engagement hook: [!culture] про горизонтальні
    зв''язки та самоорганізацію'
  - 'Міжнародна підтримка — коаліція «Рамштайн», санкції та постачання зброї; context: ленд-ліз та західна артилерія'
  words: 850
- section: Деколонізаційний погляд
  points:
  - 'Російський наратив: «денацифікація» — прикриття для етноциду та знищення української державності; contested term: «громадянська
    війна» vs «війна за незалежність»'
  - 'Реальність: колоніальна війна — метрополія намагається силою утримати колишню колонію; engagement hook: [!decolonization]
    про тисячолітню державницьку традицію vs «штучну державу»'
  - 'Геноцидний характер агресії — депортація дітей, масові вбивства (Буча, Ізюм), стирання культурної ідентичності; include
    quote (Lina Kostenko): «І жах, і кров... маленьке сіре чоловіче накоїло чорної біди»'
  words: 850
- section: 'Підсумок: Глобальне значення'
  points:
  - 'Україна та світовий порядок — крах міфу про «другу армію світу» та оновлення системи безпеки; analysis: кінець епохи
    безкарності'
  - Від жертви до суб'єкта історії — Україна як щит Європи та вільний суб'єкт міжнародної політики
  - 'Майбутнє: перемога та відбудова — кінець епохи безкарності для диктаторів; engagement hook: [!perspective] про перемогу
    як ренесанс демократичних цінностей'
  words: 750
vocabulary_hints:
  required:
  - 'синтез (synthesis) — історичний синтез, синтез фактів; context: узагальнення подій війни'
  - 'агресія (aggression) — російська збройна агресія, акт агресії, гібридна агресія; collocation: стримувати агресію'
  - 'спротив (resistance) — чинити спротив, рух опору, народний спротив; context: тотальний спротив окупантам'
  - 'вторгнення (invasion) — повномасштабне вторгнення, початок вторгнення; date: 24.02.2022'
  - 'окупація (occupation) — тимчасова окупація, режим окупації, деокупація територій; contested term: «визволення» (RU propaganda)'
  - 'анексія (annexation) — незаконна анексія Криму, спроба анексії; legal status: нікчемна з точки зору права'
  - 'геноцид (genocide) — ознаки геноциду, визнання геноцидом; examples: Буча, Маріуполь'
  - 'ідентичність (identity) — національна ідентичність, збереження ідентичності; context: війна за ідентичність'
  recommended:
  - 'контрнаступ (counteroffensive) — успішний контрнаступ, звільнення територій; examples: Харківський, Херсонський'
  - деокупація (de-occupation) — процес деокупації, життя після деокупації; administrative challenge
  - санкції (sanctions) — міжнародні санкції, санкційний тиск, пакет санкцій; economic impact
  - зброя (weapons) — постачання зброї, сучасна зброя, західна зброя; military aid
  - стійкість (resilience) — національна стійкість, символ стійкості, психологічна стійкість
  - перемога (victory) — шлях до перемоги, день перемоги, віра в перемогу
activity_hints:
- type: reading
  focus: Порівняльний аналіз етапів війни
  source: Аналітичні матеріали
  items: 4
- type: essay-response
  focus: Чому Україна чинить спротив російській агресії?
connects_to:
- hist-139 (Шлях до перемоги)
- hist-140 (Підсумок курсу)
prerequisites:
- hist-139 (Злочини і стійкість)
persona:
  voice: Senior Professor of History
  role: Military Historian
grammar:
- Аналітичний стиль
- Причинно-наслідкові конструкції
- Складнопідрядні речення
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Синтез: Війна за існування** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Синтез: Війна за існування

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Синтез: Війна за існування"
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
