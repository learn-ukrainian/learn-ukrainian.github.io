# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: hist-013
level: HIST
sequence: 13
slug: ruska-pravda
version: '2.0'
title: 'Руська Правда: Перший законодавчий кодекс'
focus: history
pedagogy: CBI
phase: HIST.1 [Kyivan Rus]
word_target: 5000
objectives:
- Understand the structure of Ruska Pravda
- Analyze the social hierarchy of Rus
- Discuss the concept of justice in Kyivan Rus
sources:
- name: Руська Правда (Вікіпедія)
  url: https://uk.wikipedia.org/wiki/Руська_Правда
  type: reference
  notes: Overview of the legal code
- name: Текст Руської Правди
  url: https://litopys.org.ua/oldukr2/oldukr51.htm
  type: primary
  notes: Original text with translation
- name: Правда Ярослава (Коротка редакція)
  url: https://uk.wikipedia.org/wiki/Правда_Ярослава
  type: reference
  notes: First version of the code
content_outline:
- section: Вступ
  points:
  - Історичне значення — перехід від звичаєвого права (помсти) до державного законодавства (штрафів)
  - Контекст появи кодексу — договір з варязькими найманцями (1016/1019) для уникнення конфліктів
  words: 450
- section: Правда Ярослава (1016–1036)
  points:
  - Історичне тло — [!context] Кодекс з'явився не від «хорошого життя», а як компроміс у боротьбі за престол
  - Основні положення (віра vs помста) — обмеження кола месників (брат за брата); штраф 40 гривень, якщо немає месника
  - Еволюція закону — від «Правди Ярослава» до «Уставу Мономаха» (1113)
  words: 450
- section: Правда Ярославичів та соціальна структура
  points:
  - Скасування кровної помсти — 1072 р. у Вишгороді, остаточна заміна на штрафи в казну
  - Соціальна ієрархія (віра 80/40/5) — [!history-bite] Життя «огнищанина» (80 грн) vs смерда (5 грн); 5 грн = ціна 16 коней
  - Статус закупів і холопів — холопи (повна несвобода), закупи (боргова кабала з правом викупу)
  - Майнові права — захист меж, знаків власності; штрафи за переорювання межі
  words: 450
- section: Первинні джерела
  points:
  - 'Документ 1: Уривок з Руської Правди — include quote from [Літопис руський] про кровну помсту та її заміну'
  - 'Документ 2: Стаття про побиття — пріоритет честі: виривання бороди (12 грн) дорожче за відрубаний палець (3 грн)'
  - Лінгвістичний аналіз — терміни «вервь» (громада), «видок» (очевидець)
  words: 450
- section: Деколонізаційний погляд
  points:
  - Міф про "російське право" — [!myth-buster] Імперська крадіжка назви «Русская Правда» (з двома «с») vs оригінальна «Руська»
  - Мовні ознаки (протоукраїнські риси) — [!culture] повноголосся (голова, бородома), закінчення -ові/-еві, кличний відмінок
  - Європейський контекст — гуманність (відсутність смертної кари) на відміну від візантійської та московської традицій
  words: 450
- section: 'Читання: Ярослав Мудрий — законодавець'
  points:
  - Роль особистості — Ярослав як «Руський Юстиніан», будівничий держави через право
  - Захист торгівлі — особливий статус і захист для «гостя» (купця)
  - Розбудова держави — заміна племінної помсти на державний суд і віру (штраф)
  words: 450
- section: Соціальні ліфти та Економіка
  points:
  - Мобільність суспільства — закуп міг викупитися; вільний міг стати холопом через злочин або борги
  - Економічне регулювання (борги, власність) — Устав Мономаха про різи (відсотки); гривня як валюта
  - 'Археологічні підтвердження (гривні, печатки) — [!fact] Штрафи були величезними: 40–80 гривень — це статок цілого села'
  words: 450
- section: Порівняльний аналіз правових систем
  points:
  - Візантія та Германські правди — паралелі із Салічною правдою (Lex Salica) франків
  - Велика хартія вольностей — спільна європейська логіка обмеження свавілля
  - Контраст із Московським правом (Домострой) — [!context] «Божий суд» (ордалії) в Русі vs тортури і смертна кара в Московщині
    (Судебник 1497)
  words: 450
- section: Жінки, Суд та Мова
  points:
  - Правосуб'єктність жінки — високі штрафи за образу жінки; майнові права вдів
  - Судовий процес (свідки, ордалії) — змагальний процес («гоніння сліду»), випробування залізом або водою
  - Мовні особливості тексту — жива народна мова Русі-України як основа документа
  words: 450
- section: Спадщина та Сучасність
  points:
  - 'Литовський Статут і козацьке право — прямі спадкоємці: збереження термінології та гуманності'
  - Сучасна правова свідомість — Україна як спадкоємиця європейської правової традиції, а не ординської деспотії
  - Уроки для сьогодення — [!decolonization] «Руська Правда» не має нічого спільного з «Домостроєм»
  words: 450
- section: 'Повсякденне правосуддя: Казуси'
  points:
  - Справа про борт — штраф 12 гривень за знищення вуликів (мед і віск як стратегічний експорт)
  - Справа про позику — розстрочка, якщо товар втрачено через стихію; рабство, якщо пропив
  - Роль громади — «вервь» несла колективну відповідальність («дика віра») за вбивство на її території
  words: 500
vocabulary_hints:
  required:
  - право (law) — перехід від звичаєвого права
  - закон (statute) — писаний закон князя
  - віра (wergild) — грошовий штраф за вбивство
  - кровна помста (blood feud) — архаїчний звичай, скасований Ярославичами
  - смерд (smerd - peasant) — вільний селянин-общинник, штраф 5 гривень
  - холоп (kholop - slave) — повна несвобода, об'єкт власності
  - закуп (zakup - debt bondsman) — боргова кабала з правом викупу
  - боярин (boyar) — представник еліти, «огнищанин»
  - дружина (druzhina) — військова еліта князя
  - судочинство (judiciary) — змагальний процес
  - звід (svod - legal procedure) — процедура пошуку краденого
  - спадкування (inheritance) — права дітей і вдів
  recommended:
  - рядович (riadovych) — залежна людина за договором («рядом»)
  - челядь (household slaves) — домашні раби
  - ордалія (ordeal) — «Божий суд», випробування залізом/водою
  - гоніння сліду (pursuit of trail) — розшук злочинця
  - присяга (oath) — «рота», клятва на суді
  - Просторова редакція (Expanded edition) — пізніша, детальніша версія кодексу
activity_hints:
- type: reading
  focus: Excerpts from Ruska Pravda with translation
  source: Provide in module
- type: comparative-study
  focus: Punishments for crimes against different social classes
  output: Table of wergild amounts
- type: essay-response
  focus: Що Руська Правда розповідає про суспільство Київської Русі?
- type: essay-response
  focus: Чи була Руська Правда справедливою для всіх верств населення?
connects_to:
- hist-14 (St. Sophia — cultural context)
- hist-18 (People of Rus — social life)
- 'hist-20 (Synthesis: Kyivan Rus)'
prerequisites:
- hist-12 (Yaroslav the Wise)
persona:
  voice: Senior Professor of History
  role: Prince's Judge
grammar:
- Legal terminology
- Conditional sentences
module_type: history
immersion: 100% Ukrainian

```

---

## PART 1: Deep Research

Research **Руська Правда: Перший законодавчий кодекс** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Руська Правда: Перший законодавчий кодекс

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — Phase D verifies prose against this -->
```yaml
subject: "Руська Правда: Перший законодавчий кодекс"
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
