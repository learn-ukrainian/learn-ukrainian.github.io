# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-120
level: HIST
sequence: 120
slug: rukh
version: '2.0'
title: 'Рух: Народний рух України'
subtitle: 'Rukh: The People''s Movement of Ukraine'
focus: history
pedagogy: CBI
phase: HIST.12 [Independence & Modern Era]
word_target: 5000
objectives:
- Учень може описати створення та діяльність Народного руху України
- Учень може пояснити роль Руху у здобутті незалежності
- Учень може проаналізувати програму та ідеологію руху
- 'Учень може оцінити внесок лідерів Руху: Чорновіл, Драч, Павличко'
content_outline:
- section: 'Вступ: Перебудова в Україні'
  points:
  - '1985-1989: гласність і перебудова — політика, що відкрила шлюзи правди про репресії та Голодомор'
  - 'Чому виник Рух — невдоволення «заповідником застою» Щербицького та екологічний фактор (Чорнобиль, «Зелений світ»); cultural
    hook: мобілізація через екологічні ініціативи'
  - 'Від культурного до політичного — ініціатива Спілки письменників переросла у вимогу суверенітету; engagement hook: [!context]
    про газету «Літературна Україна» як парадоксальний рупор революції в умовах інформаційної блокади'
  words: 850
- section: Створення Руху (1989)
  points:
  - 'Установчий з''їзд у Києві — 8-10 вересня 1989, КПІ, 1109 делегатів, ейфорія та перше масове використання синьо-жовтих
    прапорів; cultural hook: присутність гостей з литовського «Саюдіс» та польської «Солідарності»'
  - 'Лідери: В''ячеслав Чорновіл — представник радикального крила, виступав за дефедералізацію СРСР; Михайло Горинь — голова
    Секретаріату'
  - 'Іван Драч та Дмитро Павличко — поети на чолі політики; engagement hook: [!culture] про унікальність українського досвіду,
    де митці очолили націю (Drach quote: «Хто сумнівом битий, той не може вести»)'
  - Програма Руху — еволюція від «Народний рух України за перебудову» та федералізму (1989) до повної державної незалежності
    (1990)
  words: 850
- section: Діяльність Руху (1989-1991)
  points:
  - 'Живий ланцюг: 21 січня 1990 — символ єднання ЗУНР і УНР, організаційний тріумф; engagement hook: [!history-bite] про
    масштаб акції (0.5-3 млн учасників, 600-700 км)'
  - Вибори 1990 року — перемога Демократичного блоку в Галичині та Києві, створення опозиційної «Народної Ради» (Ігор Юхновський)
    проти комуністичної «Групи 239»
  - 'Боротьба за незалежність — тиск на Верховну Раду для прийняття Декларації про суверенітет (16.07.1990); include quote:
    В. Чорновіл «Над Україною нависає зловісна двоголова тінь російського імперіалізму»'
  - Референдум 1 грудня 1991 — активна агітація «ТАК», Чорновіл (23%) переміг у трьох західних областях
  - Рух після незалежності — трансформація з широкого фронту в політичну партію, розколи через амбіції («де два українці,
    там три гетьмани»)
  words: 850
- section: Первинні джерела
  points:
  - 'Програмні документи Руху — «Відозва до усіх людей доброї волі» (права нацменшин) та еволюція статуту; include quote:
    Іван Драч «Народний рух — це форма самоорганізації народу»'
  - 'Виступи лідерів — промови Драча та Чорновола; engagement hook: [!quote] Чорновіл про мову та державність («Допустити
    дві державні мови... значить, зруйнувати державу»)'
  - Фото- та відеоматеріали — море людей біля Софії Київської, синьо-жовті прапори, обличчя «Живого ланцюга»
  words: 850
- section: Деколонізаційний погляд
  points:
  - 'Радянський наратив: «націоналісти» — таврування рухівців як «екстремістів» та «бандерівців», робота КДБ на розкол; engagement
    hook: [!myth-buster] про поміркованість першої програми та міф про «екстремістів»'
  - 'Реальність: демократичний рух — інструмент повернення суб''єктності та відновлення природного стану речей (державності)'
  - Рух як антиколоніальна сила — класичний національно-визвольний рух, адаптований до умов пізнього тоталітаризму, що об'єднав
    різні етноси («За нашу і вашу свободу» — євреї, кримські татари)
  words: 850
- section: 'Підсумок: Спадщина Руху'
  points:
  - 'Внесок у незалежність — підготовка суспільства і кадрів, без яких 1991 рік міг би мати інший сценарій; engagement hook:
    [!decolonization] про трансформацію радянської республіки в державу'
  - Доля лідерів — загадкова загибель Чорновола (1999), подальша діяльність Драча і Павличка
  - 'Рух у сучасній пам''яті — еталон демократичної партії романтичного періоду та уроки єдності; include quote: В. Чорновіл
    «Україна розпочинається з тебе»'
  words: 750
vocabulary_hints:
  required:
  - рух (movement) — Народний рух України, національно-визвольний рух, рухівці
  - незалежність (independence) — Акт проголошення незалежності, здобуття незалежності, повна державна незалежність
  - перебудова (perestroika) — Народний рух за перебудову, епоха перебудови, політика перебудови
  - демократія (democracy) — демократичні перетворення, Демократичний блок, мітингова демократія
  - референдум (referendum) — Всеукраїнський референдум 1 грудня, результати референдуму
  - партія (party) — політична партія, комуністична партія, багатопартійна система
  - з'їзд (congress) — Установчий з'їзд, делегати з'їзду, ІІ Всеукраїнські збори
  - програма (program) — програма Руху, програмні документи, проєкт програми
  recommended:
  - гласність (glasnost) — політика гласності, епоха гласності, рупор гласності
  - опозиція (opposition) — легальна опозиція, опозиційна Народна Рада, конструктивна опозиція
  - мітинг (rally) — багатотисячний мітинг, мітингова демократія, несанкціонований мітинг
  - самовизначення (self-determination) — право на самовизначення, національне самовизначення
  - суверенітет (sovereignty) — державний суверенітет, Декларація про суверенітет
  - декларація (declaration) — Декларація про державний суверенітет України, ухвалення декларації
  - ланцюг (chain) — живий ланцюг, ланцюг єднання
  - спілка (union) — Спілка письменників України, професійна спілка
activity_hints:
- type: reading
  focus: Програма Руху та виступи лідерів
  source: Архівні документи
  items: 4
- type: critical-analysis
  focus: 'Верифікація фактів: Факти про Рух'
  items: 5
- type: essay-response
  focus: Яку роль відіграв Рух у здобутті незалежності України?
connects_to:
- hist-119 (Ланцюг єднання)
- hist-120 (Незалежність 1991)
prerequisites:
- hist-117 (Шістдесятники)
persona:
  voice: Senior Professor of History
  role: Civic Organizer
grammar:
- Минулий час в історичному наративі
- Політична лексика
- Складнопідрядні речення
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Рух: Народний рух України** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Рух: Народний рух України

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Рух: Народний рух України"
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
