# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: bio-003
level: BIO
sequence: 3
slug: volodymyr-velykii
version: '2.0'
title: 'Володимир Великий: Хреститель Русі'
focus: biography
pedagogy: CBI
phase: BIO
word_target: 5000
objectives:
- Analyze the geopolitical significance of the Christianization of Rus
- Evaluate the state-building reforms of Volodymyr the Great (administrative, financial, symbolic)
- Discuss the legacy of the Trident and the first currency in modern Ukrainian identity
sources:
- name: Володимир Святославич (Wikipedia UA)
  url: https://uk.wikipedia.org/wiki/Володимир_Святославич
  type: primary
  notes: Biography, Christianization, reign
- name: Хрещення Русі (Wikipedia UA)
  url: https://uk.wikipedia.org/wiki/Хрещення_Русі
  type: primary
  notes: Process and significance of Christianization
- name: Вибір віри
  url: https://uk.wikipedia.org/wiki/Вибір_віри
  type: reference
  notes: Legend of choosing religion
content_outline:
- section: 'Вступ: Архітектор цивілізаційного коду'
  points:
  - Трансформація Володимира як ключова точка розлому історії — зміна вектору розвитку Східної Європи на 1000 років
  - Місце в українському державотворенні та європейському контексті — вибір християнства як вибір цивілізації (писемність,
    кам'яне будівництво)
  - Проблема джерел та 'легендарний' фільтр — ідеалізація в 'Повісті минулих літ' vs реальний жорсткий політик; [!decolonization]
    Пам'ятник у Москві як крадіжка історії
  words: 450
- section: 'Походження: Від ''робичича'' до великого стратега'
  points:
  - Статус 'робичича' (сина ключниці Малуші) як виклик і стимул — [!history-bite] порівняння з байстрюками Європи (Вільгельм
    Завойовник)
  - Виховання під наглядом воєводи Добрині — жорстка школа виживання та військової справи
  - 'Новгородський період: перша школа управління — тісні зв''язки зі Скандинавією та варязьким світом'
  words: 450
- section: 'Боротьба за престол: Кривава усобиця Рюриковичів'
  points:
  - Загибель Святослава та початок війни між братами — Ярополк (Київ) vs Олег (Древляни) vs Володимир (Новгород)
  - Втеча до Скандинавії та збір варязького війська — повернення з найманцями для реваншу
  - Захоплення Полоцька (трагедія Рогнеди) та штурм Києва — відмова «не хочу роззути робичича» та брутальна помста
  words: 450
- section: 'Язичницька реформа: Спроба створення державної віри'
  points:
  - 'Київський пантеон 980 року: політичний підтекст ієрархії богів — [!context] штучний конструкт для об''єднання племен'
  - 'Перун як патрон княжої влади — спроба централізації: один князь — один головний бог'
  - Криза ідеології та провал людських жертвоприношень — варяги Федір і Іван як свідчення тупикового шляху
  words: 450
- section: 'Геополітичний вибір: Тендер світових релігій'
  points:
  - 'Легенда про випробування вір: аналіз прагматичних факторів — мусульмани (вина), юдеї (землі), німці (піст)'
  - Чому було відкинуто іслам, юдаїзм та західне християнство — загроза від Степу та Хозарського каганату
  - 'Візантійський вектор: естетика, право та імперський статус — модель «цезаропапізму» (імператор вище патріарха)'
  words: 450
- section: 'Корсунь та Хрещення: Дипломатія примусу до рівності'
  points:
  - Облога Корсуня (Херсонеса) як інструмент тиску на Візантію — імператор Василій II потребував допомоги проти заколотників
  - 'Шлюб з Анною Порфірородною: вхід до світової еліти — [!myth-buster] це була прагматична умова, а не добровільне просвітлення'
  - 'Події 988 року: повалення ідолів та хрещення киян — «хто не з’явиться завтра на ріці... мені той противником буде»'
  words: 450
- section: 'Державне будівництво: Змієві вали та власний карб'
  points:
  - 'Змієві Вали: стратегічне значення та технологія будівництва — «Велика українська стіна» довжиною бл. 1000 км проти печенігів'
  - 'Карбування златників і срібників: акт фінансового суверенітету — копіювання візантійських зразків, але з власним портретом'
  - 'Тризуб Володимира: народження державного символу — [!culture] напис «Володимир на столі, а се його срібло»'
  words: 450
- section: 'Культурна революція: Десятинна церква та освіта еліт'
  points:
  - 'Будівництво Десятинної церкви: архітектурний та фінансовий центр — 989–996 рр., майстри з Візантії, десятина доходів'
  - 'Заснування шкіл: ''навчання книжне'' як деколонізація неписьменності — примусове навчання дітей бояр (кадровий резерв)'
  - Початок літописання та візантійський культурний трансфер — впровадження кириличної писемності
  words: 450
- section: 'Трансформація особистості: Від деспота до милосердного батька'
  points:
  - 'Зміна стилю правління: соціальна опіка та милосердя — роздача їжі бідним, бенкети для дружини'
  - Образ 'Красного Сонечка' у народній пам'яті — літописний топос «вовк став ягням»
  - Спроба скасувати смертну кару — конфлікт «Боюсь гріха» vs позиція єпископів про покарання розбійників
  words: 450
- section: 'Спадщина: Деколонізація образу та тяглість Тризуба'
  points:
  - Спростування імперських міфів про спадковість Москви — [!myth-buster] Володимир правив у Києві, коли Москви не існувало
  - Володимир як символ європейського вибору України — династичні шлюби дітей (NB: епітет «Тесть Європи» належить Ярославу Мудрому, не Володимиру)
  - Канонізація та тяглість ідеї української державності — Тризуб як спадок Київської Русі в сучасній Україні
  words: 450
- section: 'Підсумок: Візіонер руської ойкумени'
  points:
  - Квінтесенція правління Володимира Великого — перетворення конгломерату племен на централізовану імперію
  - Урок політичного візіонерства для сучасності — створення ідеологічного фундаменту, що тримає ідентичність досі
  words: 500
vocabulary_hints:
  required:
  - хрещення (baptism/Christianization) — прийняття християнства, акт хрещення
  - язичництво (paganism) — язичницька реформа, криза язичництва
  - хреститель (baptizer) — Володимир Хреститель, рівноапостольний князь
  - рівноапостольний (equal-to-the-apostles) — святий рівноапостольний князь
  - пантеон (pantheon) — язичницький пантеон, ієрархія богів
  - ідол (idol) — повалення ідолів, Перун
  - десятина (tithe) — Десятинна церква, віддавати десятину
  - усобиця (internecine war) — князівська усобиця, боротьба за владу
  - порфірородна (born in the purple) — Анна Порфірородна, візантійська принцеса
  - Корсунь (Chersonesus) — похід на Корсунь, облога міста
  recommended:
  - клятва (oath) — порушення клятви, вірність
  - святиня (shrine) — християнська святиня, будівництво храмів
  - монастир (monastery) — заснування монастирів
  - єпископ (bishop) — порада єпископів, церковна ієрархія
  - грамота (charter/literacy) — навчання грамоти, книжне вчення
activity_hints:
- type: reading
  focus: Chronicle account of the choice of faith
  source: Повість минулих літ (adapted)
  items: 3 passages
- type: essay-response
  focus: Why did Volodymyr choose Byzantine Christianity?
  output: Analysis with historical and pragmatic factors
- type: critical-analysis
  focus: Evaluate the methods of Christianization
  output: Balanced assessment with sources
connects_to:
- bio-04 (Yaroslav Mudryi - son, continued church building)
- bio-05 (Anna Yaroslavna - granddaughter)
- bio-08 (Iov Boretskyi - Orthodox church defense)
prerequisites:
- bio-01 (Knyahynia Olha - grandmother, first Christian)
- bio-02 (Kniaz Sviatoslav - father)
persona:
  voice: Senior Biographer
  role: Grand Prince
grammar:
- Historical narrative register
module_type: biography
immersion: 100% Ukrainian

```

---

## PART 1: Deep Research

Research **Володимир Великий: Хреститель Русі** for the **bio** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Володимир Великий: Хреститель Русі

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — Phase D verifies prose against this -->
```yaml
subject: "Володимир Великий: Хреститель Русі"
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
