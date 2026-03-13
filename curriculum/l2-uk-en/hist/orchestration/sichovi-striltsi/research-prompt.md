# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: hist-089
level: HIST
sequence: 89
slug: sichovi-striltsi
version: '2.0'
title: Українські січові стрільці
subtitle: The Ukrainian Sich Riflemen
focus: history
pedagogy: CBI
phase: HIST.9 [WWI & Revolution]
word_target: 5000
objectives:
- Учень може описати створення та бойовий шлях УСС
- Учень може пояснити роль УСС в українському національному відродженні
- Учень може проаналізувати культурну спадщину січових стрільців
- Учень може оцінити значення УСС для майбутньої боротьби за незалежність
content_outline:
- section: 'Вступ: Патріоти, воїни, просвітники'
  points:
  - '1914: початок Першої світової — контекст трагедії розділеного народу (3.5 млн в армії РФ vs 250 тис. в австрійській)'
  - 'Чому українці пішли воювати — маніфест Головної Української Ради (6 серпня 1914); мета: інтернаціоналізація українського
    питання'
  - УСС як національне формування — феномен «армії поетів та професорів»; високий освітній ценз добровольців; include engagement
    hook [!history-bite] about 28k volunteers vs 2.5k allowed
  words: 850
- section: Створення легіону
  points:
  - Галицькі студенти та «Сокіл» — роль парамілітарних організацій («Січ», «Пласт») як бази для війська; include engagement
    hook [!context]
  - Формування Легіону УСС (1914) — жорсткий відбір у Львові та Стрию; недовіра австрійського командування
  - Організація та командування — перший комендант Михайло Галущинський; роль Вільгельма Габсбурга (Василя Вишиваного)
  - Символіка та присяга — шапки-«мазепинки», синьо-жовті відзнаки; таємна присяга на вірність Україні (Стрий, 3 вересня 1914);
    include Quote 1 (Oath)
  words: 850
- section: Бойовий шлях
  points:
  - Карпатський фронт — перший бій на Ужоцькому перевалі (25 вересня 1914); «війна в снігу» та оборона переходів
  - Битва під Маківкою (1915) — 29 квітня – 4 травня; зупинка наступу генерала Брусилова; психологічний злам (перемога над
    регулярною російською армією); include engagement hook [!military]
  - Битва на горі Лисоня — серпень-вересень 1916; блокування наступу на Бережани; трагічні втрати (>70%)
  - Втрати та героїзм — відновлення складу (Гуцульська сотня); міф про «австрійських найманців» (include engagement hook [!myth-buster])
  - УСС у 1917-1918 роках — перехід до Листопадового чину; ядро Української Галицької Армії (УГА)
  words: 850
- section: Первинні джерела
  points:
  - Спогади січових стрільців — Михайло Галущинський «Мої спомини»; щоденники рядових бійців
  - Стрілецькі пісні — творчість Романа Купчинського, Левка Лепкого, Михайла Гайворонського; «Чуєш, брате мій» як реквієм
  - Фотографії та документи — феномен «Пресової кватири» (мистецтво в окопах); виставки та видавництво листівок; include engagement
    hook [!culture]
  words: 850
- section: Деколонізаційний погляд
  points:
  - 'Імперський наратив: «зрадники» — радянські міфи про «австрійських найманців» та «буржуазних націоналістів»'
  - 'Реальність: борці за волю — концепція «українського П''ємонту»; використання геополітичного конфлікту імперій для відновлення
    державності'
  - УСС в українській пам'яті — просвітницька місія на Волині (відкриття ~100 шкіл, навчання історії та мови на підросійських
    землях)
  words: 850
- section: 'Підсумок: Культурна спадщина'
  points:
  - 'Стрілецькі пісні: «Ой у лузі червона калина» — шлях від гімну 1914 року до світового символу спротиву 2022 (Андрій Хливнюк,
    Pink Floyd); include engagement hook [!legacy]'
  - 'УСС та ЗУНР — безперервність боротьби: УСС -> УГА -> УВО -> ОУН -> УПА'
  - Вплив на наступні покоління — романтизація визвольних змагань як фундамент національної ідентичності
  words: 750
vocabulary_hints:
  required:
  - січові стрільці (Sich Riflemen) — often abbreviated as УСС
  - 'легіон (legion) — collocations: формування легіону, вступ до легіону'
  - 'фронт (front) — collocations: Карпатський фронт, на фронті'
  - 'битва (battle) — collocations: кривава битва, вирішальна битва'
  - 'присяга (oath) — collocations: скласти присягу, вірність присязі'
  - 'воїн (warrior) — context: high register compared to солдат'
  - 'патріот (patriot) — context: volunteer motivation'
  - 'командир (commander) — synonym: комендант, сотник'
  recommended:
  - 'окоп (trench) — collocations: сидіти в окопах, окопна війна'
  - 'артилерія (artillery) — context: heavy shelling at Lysonia'
  - 'кулемет (machine gun) — context: WWI technology'
  - 'наступ (offensive) — collocations: зупинити наступ, російський наступ'
  - 'полон (captivity) — collocations: потрапити в полон'
  - 'героїзм (heroism) — collocations: виявити героїзм'
  - 'доброволець (volunteer) — context: 28,000 volunteers'
  - 'сотня (company) — context: historical military unit (approx. 100-200 men)'
  - 'вишкіл (military training) — context: Plast/Sokil preparation'
  - 'просвітництво (enlightenment) — context: cultural mission in Volhynia'
  - 'спадщина (legacy) — collocations: культурна спадщина, історична спадщина'
activity_hints:
- type: reading
  focus: Спогади січових стрільців
  source: Архівні матеріали
  items: 4
- type: essay-response
  focus: Яку роль відіграли УСС в українському національному відродженні?
connects_to:
- hist-90 (Революція 1917)
- hist-93 (ЗУНР)
prerequisites:
- hist-88 (Перша світова війна)
persona:
  voice: Senior Professor of History
  role: USS Legionnaire
grammar:
- Минулий час у воєнному наративі
- Військова лексика
- Пасивні конструкції
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Українські січові стрільці** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

### Your RAG Tools (USE THEM)

You have access to Ukrainian language tools via MCP. **Use them during research.**

| Tool | When to use | Example |
|------|-------------|---------|
| `query_wikipedia` mode=`extract` | Get full article text (50K chars) for deep research | `query_wikipedia("Богдан Хмельницький", mode="extract")` |
| `query_wikipedia` mode=`sections` | See article structure before diving in | `query_wikipedia("Запорізька Січ", mode="sections")` |
| `query_wikipedia` mode=`section` | Read a specific section by index | `query_wikipedia("Запорізька Січ", mode="section", section=3)` |
| `query_wikipedia` mode=`search` | Find the right article title | `query_wikipedia("Переяславська рада", mode="search")` |
| `search_literary` | Find primary source excerpts (chronicles, poetry, legal texts) | `search_literary("Хмельницький", genre="chronicle")` |
| `verify_word` / `verify_words` | Check Ukrainian words exist in VESUM dictionary | `verify_words(["гетьман", "козацтво"])` |
| `query_grac` | Check word frequency in Ukrainian corpus | `query_grac("упокорення", mode="frequency")` |

**Workflow**: Search Wikipedia FIRST for factual foundation → search literary RAG for primary quotes → verify vocabulary with VESUM.

### Research Requirements

1. **Sources**: Use `query_wikipedia` (mode=`extract`) for Ukrainian Wikipedia articles. Also consult history.org.ua, litopys.org.ua. Use `search_literary` for primary source excerpts. Russian-language sources are PROHIBITED.
2. **Timeline**: Build a chronological timeline with 5+ dated events/milestones.
3. **Primary Quotes**: Find 2+ quotable primary source excerpts (original Ukrainian text preferred).
4. **Engagement Hooks**: Identify 6+ engagement hooks mapped to specific content sections:
   - `[!myth-buster]` — Decolonization: correct imperial/Soviet myths
   - `[!history-bite]` — Surprising or lesser-known facts
   - `[!context]` — Broader historical/cultural context
   - `[!quote]` — Primary source citations
   - `[!decolonization]` — Ukraine-centric reframing
   - `[!culture]` — Cultural significance
5. **Decolonization Angle**: Identify how this topic has been distorted by imperial/Soviet historiography and what the Ukrainian-centric framing should be.
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
- **Colonial framing**: plan decolonized framing NOW so Phase B doesn't default to Russian comparisons
- **Engagement callouts**: map 6+ hooks to specific sections during research (not as afterthought patches)
- **Duplicate headers**: ensure outline section names don't share keywords

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

### Output Block 1: Research Notes

```
===RESEARCH_START===

# Дослідження: Українські січові стрільці

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — Phase D verifies prose against this -->
```yaml
subject: "Українські січові стрільці"
vital_status: "deceased" # or "alive"
dates:
  birth: "YYYY-MM-DD"    # or approximate: "~YYYY"
  death: "YYYY-MM-DD"    # omit if alive
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
- Section "{section_name}": [!hook_type] — description
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
```

## Friction Report (MANDATORY)

After both output blocks, include:

```
===FRICTION_START===
**Phase**: Phase A: Research + Meta (Seminar)
**Step**: {what you were doing when friction occurred, or "Full Phase A"}
**Friction Type**: NONE | TOKEN_LIMIT_TRUNCATION | TOOL_REDUNDANCY | SOURCE_NOT_FOUND | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===
```

---

## Boundaries

- Do NOT write lesson content — only research notes
- Do NOT generate activities or vocabulary
- Do NOT skip any section from the plan's content_outline
- Do NOT use Russian-language sources
- Do NOT fabricate quotes or dates — if unsure, mark as "[needs verification]"
- Do NOT reference persona names or voice instructions — persona is assigned at content generation time
- Do NOT request skills, delegate to Claude, or skip this phase
