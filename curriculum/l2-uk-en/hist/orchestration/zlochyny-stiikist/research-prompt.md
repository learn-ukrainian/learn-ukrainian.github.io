# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-139
level: HIST
sequence: 139
slug: zlochyny-stiikist
version: '2.0'
title: Злочини і стійкість
subtitle: Crimes and Resilience
focus: history
pedagogy: CBI
phase: HIST.13 [Russian Aggression]
word_target: 5000
objectives:
- Учень може описати воєнні злочини Росії в Україні
- Учень може пояснити концепцію стійкості українського суспільства
- Учень може проаналізувати хронологію звільнень українських територій
- Учень може оцінити міжнародну правову відповідь на злочини
content_outline:
- section: 'Вступ: Злочин та відплата'
  points:
  - Воєнні злочини як стратегія — не ексцеси виконавців, а державна політика терору та залякування
  - Буча, Маріуполь, Ірпінь — символи трагедії, що змінили світове сприйняття війни та пришвидшили постачання зброї
  - 'Україна вистояла — феномен опору «другій армії світу»; cultural hook: [!history-bite] «Київ за три дні» vs реальність
    Гааги'
  words: 850
- section: Воєнні злочини
  points:
  - 'Буча: розстріли цивільних — систематичні вбивства за списками та катівні (наприклад, табір «Променистий»); [!myth-buster]
    супутникові знімки Maxar спростовують фейк про «постановку»'
  - 'Маріуполь: облога та руйнування — авіаудар по Драмтеатру 16 березня, гуманітарна катастрофа, знищення 90% житлового фонду'
  - Удари по інфраструктурі — тактика «випаленої землі» та спроба заморозити українців взимку
  - Депортація дітей — примусове вивезення та зміна ідентичності; [!context] роль «фільтраційних таборів»
  - Ордер на арешт Путіна — історичне рішення МКС 17 березня 2023 року щодо відповідальності за депортацію дітей
  words: 850
- section: Стійкість (Stiikist)
  points:
  - Що таке стійкість — здатність суспільства функціонувати та відновлюватися під час екзистенційної загрози
  - Блекаути та виживання — генератори бізнесу та феномен «Пунктів незламності» ([!culture]); [!quote] гасло «Світло переможе
    темряву»
  - Волонтерський рух — горизонтальні зв'язки, збори на «Байрактари» та супутники (фонд Притули)
  - Культура опору — гумор як зброя (меми про «бавовну», «тракторні війська») та пісні («Ой у лузі червона калина»)
  words: 850
- section: Первинні джерела
  points:
  - Свідчення з Бучі — історії вижилих про окупацію (матеріали «Слідство.Інфо» та Радіо Свобода)
  - Фото- та відеодокази — роботи Євгена Малолетки з обложеного Маріуполя (World Press Photo)
  - Документи МКС — заява прокурора Каріма Хана про обґрунтовані підозри щодо Путіна та Львової-Бєлової
  words: 850
- section: Деколонізаційний погляд
  points:
  - 'Російський наратив: «фейки» — заперечення злочинів як типова імперська стратегія дегуманізації жертви'
  - 'Реальність: задокументовані злочини — геноцидний характер війни (стаття Тімоті Снайдера), знищення еліти та культури'
  - Правосуддя як деколонізація — [!decolonization] Гаага як визнання української суб'єктності та злочинності російських імперських
    практик
  words: 850
- section: 'Підсумок: Звільнення'
  points:
  - 'Харківщина: вересень 2022 — блискавичний прорив (Балаклійсько-Куп''янська операція) та захоплення техніки («російський
    ленд-ліз»)'
  - 'Херсон: листопад 2022 — звільнення єдиного окупованого обласного центру; [!history-bite] «кавун звільнення» як символ
    надії'
  - Шлях до перемоги — злочини не зламали волю, а зміцнили вимогу справедливості
  words: 750
vocabulary_hints:
  required:
  - злочин (crime) — воєнний злочин, злочин проти людяності, фіксація злочинів
  - стійкість (resilience) — національна стійкість, проявляти стійкість, феномен стійкості
  - звільнення (liberation) — звільнення територій, деокупація міст, радість звільнення
  - жертви (victims) — цивільні жертви, вшанування пам'яті жертв, ексгумація тіл
  - докази (evidence) — збирати докази, неспростовні докази, передавати докази в суд
  - правосуддя (justice) — міжнародне правосуддя, відновити справедливість, невідворотність покарання
  - депортація (deportation) — примусова депортація дітей, незаконне переміщення, повернення депортованих
  - окупація (occupation) — тимчасова окупація, життя в окупації, звільнення з-під окупації
  recommended:
  - МКС (ICC) — Міжнародний кримінальний суд, Гаазький трибунал, Римський статут
  - трибунал (tribunal) — спеціальний трибунал, трибунал для агресора, створити трибунал
  - блекаут (blackout) — аварійні відключення, пережити блекаут, енергетичний терор
  - волонтер (volunteer) — волонтерський рух, допомога волонтерів, донатити на ЗСУ
  - свідчення (testimony) — свідчення очевидців, фіксувати свідчення, давати свідчення
  - відновлення (recovery) — відновлення інфраструктури, план відновлення, відбудова України
activity_hints:
- type: reading
  focus: Свідчення вижилих з Бучі
  source: Усна історія
  items: 4
- type: essay-response
  focus: Як Україна демонструє стійкість під час війни?
connects_to:
- hist-138 (Міжнародна підтримка)
- 'hist-140 (Синтез: Війна за існування)'
prerequisites:
- hist-136 (Воєнна економіка)
persona:
  voice: Senior Professor of History
  role: Human Rights Lawyer
grammar:
- Минулий та теперішній час
- Юридична та емоційна лексика
- Пасивні конструкції
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Злочини і стійкість** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Злочини і стійкість

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Злочини і стійкість"
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
