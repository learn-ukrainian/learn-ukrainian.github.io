# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-131
level: HIST
sequence: 131
slug: viyna-donbas
version: '2.0'
title: Війна на Донбасі 2014-2022
subtitle: The War in Donbas 2014-2022
focus: history
pedagogy: CBI
phase: HIST.13 [Russian Aggression]
word_target: 5000
objectives:
- Учень може описати початок та перебіг війни на Донбасі
- Учень може пояснити роль Росії в конфлікті
- Учень може проаналізувати ключові битви та події
- Учень може оцінити наслідки війни для України
content_outline:
- section: 'Вступ: «Русская весна»'
  points:
  - 'Квітень 2014: захоплення Донецька та Луганська — 12 квітня група Гіркіна захоплює Слов''янськ; початок силового сценарію;
    вторгнення диверсійних груп ГРУ РФ'
  - Російські «зелені чоловічки» — тактика захоплення адмінбудівель спецназом РФ без розпізнавальних знаків; координація ГРУ;
    застосування кримського сценарію
  - Проголошення «ДНР» та «ЛНР» — штучні утворення; референдуми «під дулами автоматів» без списків виборців і спостерігачів
  - 'cultural hook: [!myth-buster] — «Русская весна» не була стихійним повстанням шахтарів, а спланованою операцією спецслужб
    РФ (кейс Гіркіна)'
  words: 850
- section: Війна 2014-2015
  points:
  - 'Слов''янськ: Стрілков/Гіркін — звільнення міста 5 липня 2014 року; переломний момент; відхід бойовиків у Донецьк'
  - Збиття MH17 — 17 липня 2014, 298 загиблих; [!context] момент істини для світу, докази російського «Бука» з Курської бригади
    (розслідування JIT)
  - 'Іловайськ: трагедія — серпень 2014, пряме вторгнення регулярної армії РФ; розстріл «зеленого коридору»; найбільші одномоментні
    втрати ЗСУ'
  - 'Донецький аеропорт: «кіборги» — оборона 242 (244) дні; [!history-bite] фраза «Кіборги вистояли, не витримав бетон»; вежа
    впала 13 січня 2015'
  - Дебальцеве — січень-лютий 2015, масштабний танковий наступ РФ (буряти) перед Мінськом-2
  words: 850
- section: Мінські угоди (2014-2022)
  points:
  - Мінськ-1 та Мінськ-2 — вересень 2014 та 12 лютого 2015; спроби зупинити наступ РФ; пункти про припинення вогню та контроль
    над кордоном
  - Чому угоди не працювали — [!analysis] Росія заперечувала участь («нас там немає») і використовувала час для підготовки
    до великої війни
  - «Заморожений конфлікт» — позиційна війна 2015-2022; постійні порушення тиші, снайперський вогонь
  - Обстріли та жертви — понад 14 тисяч загиблих (військові та цивільні) до 2022 року
  words: 850
- section: Первинні джерела
  points:
  - Свідчення учасників — спогади про Іловайськ (солдат батальйону «Донбас» про розстріл КамАЗу з пораненими)
  - Журналістські розслідування MH17 — Bellingcat та JIT доводять провину РФ
  - Відеодокази російської присутності — полонені десантники з Костроми («заблукали») у серпні 2014
  - include quote from [Pavlo Novitsky] — [!quote] захисник ДАП про колядування на вежі у -24°C
  words: 850
- section: Деколонізаційний погляд
  points:
  - 'Російський наратив: «громадянська війна» — [!decolonization] спростування міфу Civil War; термінологія Russo-Ukrainian
    War; конфлікт інспірований РФ'
  - 'Реальність: російська агресія — ініціатори громадяни РФ (Гіркін, Бородай, Моторола), зброя (Т-72Б3) та фінансування з
    бюджету РФ'
  - «ДНР»/«ЛНР» як маріонетки — окупаційні адміністрації; ватажки (Захарченко, Плотницький) призначалися та ліквідовувалися
    Кремлем
  words: 850
- section: 'Підсумок: До повномасштабного вторгнення'
  points:
  - 8 років війни — адаптація суспільства до війни «десь там»; стримування агресора
  - Втрати та біженці — мільйони ВПО (внутрішньо переміщених осіб); втрата домівок
  - Шлях до 24 лютого 2022 — роздача паспортів РФ в ОРДЛО; визнання «незалежності» псевдореспублік 21 лютого як привід для
    вторгнення
  words: 750
vocabulary_hints:
  required:
  - 'війна (war) — російсько-українська війна (Russo-Ukrainian War); learner error: civil war'
  - окупація (occupation) — тимчасова окупація (temporary occupation); окупаційна адміністрація
  - агресія (aggression) — збройна агресія РФ (armed aggression of RF); акт агресії
  - 'сепаратисти (separatists) — usage note: better use «колаборанти» or «бойовики» (militants); російські найманці'
  - добровольці (volunteers) — добровольчі батальйони (volunteer battalions); піти добровольцем
  - кіборги (cyborgs) — захисники ДАП (defenders of DAP); символ стійкості
  - Мінські угоди (Minsk agreements) — порушення угод (violation of agreements); підписання угод
  - АТО (ATO) — Антитерористична операція (Anti-Terrorist Operation); зона АТО
  - зелений коридор (green corridor) — розстріл зеленого коридору (shooting of the green corridor); пастка
  recommended:
  - обстріл (shelling) — артилерійський обстріл (artillery shelling); мінометний обстріл
  - фронт (front) — лінія фронту (front line); лінія розмежування
  - біженці (refugees) — внутрішньо переміщені особи (IDPs); вимушені переселенці
  - перемир'я (ceasefire) — режим тиші (silence regime); порушення перемир'я
  - санкції (sanctions) — міжнародні санкції (international sanctions); запровадження санкцій
  - гібридна війна (hybrid warfare) — інформаційна війна (information war); пропаганда
  - диверсанти (saboteurs) — російські диверсійні групи (Russian sabotage groups); ДРГ
activity_hints:
- type: reading
  focus: Свідчення захисників Донецького аеропорту
  source: Усна історія
  items: 4
- type: essay-response
  focus: Чому Мінські угоди не зупинили війну?
connects_to:
- hist-132 (Повномасштабне вторгнення)
- hist-134 (Маріуполь)
prerequisites:
- hist-128 (Анексія Криму)
persona:
  voice: Senior Professor of History
  role: Combat Medic
grammar:
- Минулий час у воєнному наративі
- Військова та політична лексика
- Складнопідрядні речення
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Війна на Донбасі 2014-2022** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Війна на Донбасі 2014-2022

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Війна на Донбасі 2014-2022"
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
