# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-055
level: HIST
sequence: 55
slug: kozatska-derzhava
version: '2.0'
title: 'Хмельниччина: Козацька держава'
subtitle: 'The Cossack State: Structure and Administration of the Hetmanate'
focus: history
pedagogy: CBI
phase: HIST.6 [Khmelnytsky & Cossack State]
word_target: 5000
objectives:
- Учень може описати полково-сотенний устрій Гетьманщини
- Учень може пояснити функції Генеральної старшини
- Учень може проаналізувати значення Чигирина як політичного центру
sources:
- name: History of Ukraine-Rus
  url: http://litopys.org.ua/hrushrus/iur.htm
  type: reference
  notes: Analysis of the Hetmanate structure
- name: The Cossack Myth
  url: https://history.org.ua
  type: reference
  notes: State-building and identity
content_outline:
- section: 'Вступ: Народилася Гетьманщина'
  points:
  - The challenge of state-building after victories — після перемог 1648 року постало питання організації влади на визволених
    землях
  - 'Cossack democracy vs. European legal standards — еволюція від «козацьких вольностей» до ідеї суверенної «держави руського
    народу»; cultural hook: [!context] — Швидкість трансформації повстання у повноцінну державу'
  words: 600
- section: 'Структура влади: Гетьман та Генеральна старшина'
  points:
  - The role of the Hetman as head of state — поєднання військової, адміністративної та судової влади, фактично монархічні
    повноваження
  - 'Functions of the General Staff (Scribe, Quartermaster, Judge, Treasurer) — Генеральний писар (Іван Виговський) як голова
    МЗС; cultural hook: [!history-bite] — Генеральна старшина як прообраз сучасного Кабінету Міністрів'
  words: 600
- section: 'Адміністративний устрій: Полково-сотенна система'
  points:
  - Merging military and territorial structures — ліквідація воєводств, запровадження полків як адміністративних одиниць
  - 'Role of colonels and centurions in local governance — ієрархія: Гетьман -> Полковник -> Сотник -> Отаман; cultural hook:
    [!decolonization] — Порівняння устрою з римськими муніципалітетами, а не «анархією»'
  words: 600
- section: 'Чигирин: Серце козацької держави'
  points:
  - Chyhyryn as a European capital — резиденція, архів та скарбниця, попри дерев'яну забудову
  - 'Diplomatic etiquette and foreign embassies — прийом послів з Венеції, Москви, Туреччини, Швеції; cultural hook: [!quote]
    — Альберто Віміна про дипломатичний рух у Чигирині'
  words: 600
- section: 'Економіка та право: Скарбниця та суди'
  points:
  - Creation of a national financial system — податки (мито, оренда шинків) йдуть до Військового скарбу, а не королю
  - 'Cossack justice and the Lithuanian Statute — поєднання звичаєвого права («як здавна бувало») та писаного права; cultural
    hook: [!myth-buster] — Спростування міфу про «беззаконня»'
  words: 600
- section: Читання
  points:
  - Analysis of state documents — аналіз мови та змісту Універсалу Богдана Хмельницького (1650) про захист прав міщан
  words: 600
- section: Первинні джерела
  points:
  - 'Alberto Vimina''s notes on Chyhyryn — «Реляція про походження і звичаї козаків»: погляд іноземця на освіченість та любов
    до свободи'
  words: 600
- section: 'Деколонізаційний погляд: Державність проти анархії'
  points:
  - Debunking imperial myths of 'Cossack chaos' — протиставлення імперського міфу про «селян-втікачів» реальності модерної
    держави
  - 'The Hetmanate as a mature political project — наявність території, влади, війська, податків та дипломатії; cultural hook:
    [!analysis] — Чому імперії вигідно зображати козаків як «розбійників»'
  words: 800
vocabulary_hints:
  required:
  - 'гетьманат (Hetmanate) — держава; collocations: Козацький гетьманат, устрій гетьманату'
  - 'булава (mace) — символ влади; collocations: гетьманська булава, отримати булаву'
  - 'канцелярська (chancellery) — official language; collocations: мова документів, генеральна канцелярія'
  - 'полковник (colonel) — head of regiment/territory; collocations: чернігівський полковник, влада полковника'
  - 'сотник (centurion) — head of hundred/district; collocations: сотенний устрій, наказ сотника'
  - 'скарбниця (treasury) — finances; collocations: Військова скарбниця, поповнення скарбниці'
  - 'універсал (universal) — decree; collocations: видати універсал, універсали Хмельницького'
  - 'клейноди (regalia) — state symbols; collocations: військові клейноди, втрата клейнодів'
  - 'підскарбій (treasurer) — finance minister; collocations: генеральний підскарбій, звіт підскарбія'
  - 'обозний (quartermaster) — logistics/artillery; collocations: генеральний обозний, відати артилерією'
  recommended:
  - 'автономія (autonomy) — самоврядування; collocations: політична автономія, широка автономія'
  - 'дипломатія (diplomacy) — international relations; collocations: козацька дипломатія, гнучка дипломатія'
  - 'суверенітет (sovereignty) — незалежність; collocations: державний суверенітет, боротьба за суверенітет'
activity_hints:
- type: reading
  focus: Administrative documents and chronicles
- type: essay-response
  focus: Continuity of state-building traditions
- type: critical-analysis
  focus: 'Спростування міфів: Myths about the Hetmanate governance'
  items: 4
- type: comparative-study
  focus: Cossack vs. Polish administrative models
persona:
  voice: Senior Professor of History
  role: Regimental Chancellor
grammar:
- 'Institutional register: administrative terms'
- Passive voice in official descriptions
register: публіцистичний
prerequisites:
- zborivska-bila-tserkva
connects_to:
- pereyaslavska-uhoda

```

---

## PART 1: Deep Research

Research **Хмельниччина: Козацька держава** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Хмельниччина: Козацька держава

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Хмельниччина: Козацька держава"
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
