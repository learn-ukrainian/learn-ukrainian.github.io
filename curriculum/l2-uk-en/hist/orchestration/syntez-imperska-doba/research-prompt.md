# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-086
level: HIST
sequence: 86
slug: syntez-imperska-doba
version: '2.0'
title: 'Синтез: Імперська доба'
subtitle: 'Synthesis: The Imperial Era'
focus: history
pedagogy: CBI
phase: HIST.8 [Imperial Era]
word_target: 5000
objectives:
- Учень може синтезувати знання про Україну в імперську добу
- Учень може пояснити механізми колоніального панування
- Учень може проаналізувати форми спротиву імперії
- Учень може оцінити наслідки імперської доби для сучасності
content_outline:
- section: 'Вступ: Два імперії'
  points:
  - Російська та Австро-Угорська імперії — контраст між централізованою самодержавною Росією та конституційною «клаптиковою»
    Австрією (з 1867) — початок політичного осмислення з 1840-х (Кирило-Мефодіївське братство)
  - 'Поділ українських земель — 90% території під Романовими (Наддніпрянщина), 10% під Габсбургами (Галичина, Буковина, Закарпаття);
    engagement hook: [!context] — Карта поділу: контраст політичного життя'
  - Чому імперська доба важлива — період формування модерної нації та «Австрійського П'ємонту», що врятував ідентичність від
    повного знищення — вплив «Весни народів» 1848 року
  words: 850
- section: Механізми панування
  points:
  - 'Мовні заборони — Валуєвський циркуляр (1863) та Емський указ (1876) як інструменти державного лінгвоциду; engagement
    hook: [!history-bite] — «Заборона на ноти»: страх перед музичним «сепаратизмом»'
  - Економічна експлуатація — перетворення України на сировинний придаток (76% цукру, 71% вугілля імперії) без розвитку інфраструктури
    для людей — видобуток вугілля на Донбасі зріс у 100 разів (1861–1900)
  - Кріпацтво та його наслідки — скасування 1848 (Австрія) та 1861 (Росія), але збереження економічної залежності та бідності
    села
  - «Малоросійська» ідентичність — насадження комплексу меншовартості та асиміляція еліт (приклад Гоголя vs приклад Шевченка)
    — імперський міф про «триєдиний руський народ»
  words: 850
- section: Форми спротиву
  points:
  - Шевченко та пробудження — «Кобзар» як політичний маніфест («І мертвим, і живим...») проти малоросійства
  - Громади та Драгоманова — діяльність у Києві, Харкові, Одесі; журнал «Основа»; європеїзація українського руху
  - 'Галичина як П''ємонт — створення «Просвіти» (1868) та НТШ, роль греко-католицької церкви; engagement hook: [!myth-buster]
    — Міф про «відстале селянство» vs реальність масового руху читалень'
  - Від культурного до політичного — Кирило-Мефодіївське братство (1840-ві) -> Братство тарасівців (1891) -> РУРП (1890) ->
    «Самостійна Україна» Міхновського (1900) — поява перших політичних партій
  words: 850
- section: Первинні джерела в синтезі
  points:
  - Порівняння імперських політик — цинізм Валуєва («не было, нет и быть не может») vs прагматизм австрійських дозволів
  - Голоси опору — критика федералізму Франком («над нами як нацією була б висипана могила») та листи Драгоманова
  - 'Документи епохи — тексти Емського указу про заборону нот і театру; engagement hook: [!quote] — Орест Новицький (цензор):
    «Освічені малороси... вважають свою говірку зіпсованою російською»'
  words: 850
- section: Деколонізаційний погляд
  points:
  - 'Імперський наратив: «один народ» — міф про «возз''єднання» та «триєдиний руський народ» як виправдання окупації'
  - 'Реальність: колоніалізм — експлуатація ресурсів (Донбас, Південь) на користь метрополії, а не «модернізація» — лінгвоцид
    як державна політика'
  - 'Імперська спадщина сьогодні — термін «Новоросія» як спроба стерти пам''ять про козацький Степ; engagement hook: [!decolonization]
    — Термін «Південь Росії» (Новоросія) як стирання історичної пам''яті'
  words: 850
- section: 'Підсумок: До революції'
  points:
  - Підготовка до 1917 — формування політичної еліти (Грушевський, Винниченко) та мережі організацій («Просвіти»)
  - Роль Першої світової — крах імперій як вікно можливостей для державної незалежності
  - 'Від імперії до нації — метафора «алмазу під тиском»: репресії загартували рух опору; engagement hook: [!legacy] — Чому
    1917 рік не виник на порожньому місці'
  words: 750
vocabulary_hints:
  required:
  - синтез (synthesis) — історичний синтез, синтез культур, синтез ідей
  - імперія (empire) — Російська імперія, Австро-Угорська імперія, крах імперій, «клаптикова імперія»
  - колоніалізм (colonialism) — внутрішній колоніалізм, колоніальна політика, сировинний придаток
  - спротив (resistance) — культурний спротив, збройний спротив, рух опору, форми спротиву
  - пробудження (awakening) — національне пробудження, весна народів, політичне осмислення
  - заборона (ban) — Емський указ, Валуєвський циркуляр, заборона друку, заборона сцени
  - експлуатація (exploitation) — економічна експлуатація, експлуатація ресурсів, соціальна експлуатація
  - ідентичність (identity) — національна ідентичність, малоросійська ідентичність, збереження ідентичності
  recommended:
  - кріпацтво (serfdom) — скасування кріпацтва (1861), кріпосне право, залишки кріпацтва
  - русифікація (Russification) — політика русифікації, тотальна русифікація, зросійщення
  - автономія (autonomy) — культурна автономія, вимога автономії, політична автономія
  - інтелігенція (intelligentsia) — українська інтелігенція, свідома інтелігенція, еліта
  - нація (nation) — політична нація, формування нації, модерна нація
  - революція (revolution) — назрівання революції, революційні події, переддень революції
activity_hints:
- type: reading
  focus: Порівняльний аналіз імперських політик
  source: Історичні документи
  items: 4
- type: essay-response
  focus: Як імперська доба вплинула на формування української нації?
connects_to:
- hist-87 (Грушевський)
- hist-88 (Перша світова)
prerequisites:
- hist-85 (Франко, Леся, Грінченко)
persona:
  voice: Senior Professor of History
  role: Historical Sociologist
grammar:
- Аналітичний стиль
- Причинно-наслідкові конструкції
- Складнопідрядні речення
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Синтез: Імперська доба** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Синтез: Імперська доба

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Синтез: Імперська доба"
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
