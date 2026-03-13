# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-064
level: HIST
sequence: 64
slug: ivan-mazepa-kultura
version: '2.0'
title: 'Іван Мазепа II: освіта і культура'
focus: history
pedagogy: CBI
phase: B2.3b [Українська історія]
word_target: 5000
objectives:
- Учень може описати культурну спадщину Івана Мазепи
- Учень може пояснити особливості мазепинського бароко
- Учень може охарактеризувати роль Києво-Могилянської академії в культурному відродженні
- Учень може аналізувати Мазепу як мецената та покровителя мистецтв
content_outline:
- section: 'Вступ: Золота доба українського духу'
  points:
  - 'Епоха Мазепи як культурний ренесанс українського народу — термін «Мазепинська доба» як синонім розквіту (1687–1709);
    [!context]: синонім найвищого розквіту українського бароко'
  - Поєднання європейських традицій та української ідентичності — освіта гетьмана в Девентері та знання 8 мов; навчання в
    Києво-Могилянському та єзуїтському колегіумах
  - Меценатство гетьмана як основа культурного відродження — інвестиції понад 1 мільйон дукатів у культуру та церкву; дані
    Бендерської комісії 1709 р.
  words: 450
- section: 'Києво-Могилянська академія: Афіни на Дніпрі'
  points:
  - Розширення та збагачення академії за підтримки Мазепи — будівництво нового кам'яного корпусу (Бурси) та Братського собору
  - Підготовка українських інтелектуальних еліт для держави та церкви — випускники формували еліту Східної Європи
  - 'Впровадження західноєвропейських освітніх програм та методів — [!history-bite]: неофіційна назва «Могило-Мазепинська
    академія»; титул ставив гетьмана в один ряд із засновником Петром Могилою'
  - Роль академії у формуванні національної свідомості — отримання офіційного статусу академії у 1701 році; підтверджено царською
    грамотою
  words: 450
- section: 'Мазепинське бароко: Архітектура національної величі'
  points:
  - 'Характерні риси мазепинського стилю в архітектурі — [!culture]: «гра світла» на білих стінах, грушоподібні бані, пишний
    декор; відсутність зовнішніх розписів'
  - Побудова та відновлення храмів за гетьманський кошт — Чернігівський колегіум, Троїцький собор, Мгарський монастир; Вознесенський
    собор (Переяслав)
  - Успенський собор Києво-Печерської лаври як вершина епохи — відновлення давньоруських святинь
  - 'Синтез візантійських, західноєвропейських та українських традицій — втрачені шедеври: Військовий Микільський та Богоявленський
    собори (знищені більшовиками)'
  words: 450
- section: 'Література і друк: Мазепинське слово як національна зброя'
  points:
  - Розвиток друкарської справи та видавництва книг — розкішні видання з гравюрами («Антимінс», «Євангеліє»)
  - Створення літературних творів, панегіриків та хронік — трагікомедія Феофана Прокоповича «Володимир» (1705); алегоричне
    прославлення Мазепи в образі князя Володимира
  - 'Використання літератури для утвердження державної ідеології — include quote: «Всіх славеноруських стран князь і повелитель...»;
    посвята від Феофана Прокоповича'
  - Роль українських письменників у формуванні політичного дискурсу — Пилип Орлик, Стефан Яворський
  words: 450
- section: Мистецтво гравюри та символіка влади
  points:
  - Розквіт української гравюри як мистецької форми — київська школа (І. Щирський, Л. Тарасевич)
  - Використання символів влади та національних емблем — герб «Курч» в архітектурному декорі
  - 'Поширення портретів гетьмана та ілюстрацій церковних книг — [!analysis]: гравюра І. Мигури «Мазепа серед своїх добрих
    справ» (1706); гетьман в оточенні збудованих церков та алегоричних фігур (Мудрість, Слава, Віра)'
  words: 450
- section: Українська барокова музика та хоровий спів
  points:
  - Розвиток партесного багатоголосся в церковній музиці — вплив «Граматики мусикійської» Миколи Дилецького
  - Підтримка хорових капел та музичних шкіл — емоційність і динамічність барокової естетики
  - Формування української барокової музичної традиції — Глухів як майбутній музичний центр
  words: 450
- section: Театральне мистецтво та шкільна драма
  points:
  - Розвиток театру при Києво-Могилянській академії — дидактична та пропагандистська функція театру
  - Шкільна драма як засіб виховання та національної освіти — постановки на історичні та релігійні теми
  - Поєднання релігійних та світських тем у виставах — використання інтермедій живою народною мовою; гумористичні сценки між
    актами серйозних драм
  words: 450
- section: 'Первинні джерела: Свідчення величі та щедрості'
  points:
  - Документи про вклади та дарування Мазепи церквам і монастирям — універсали та вкладні грамоти; приклад Густинського та
    Мгарського монастирів
  - Літописні згадки про культурні досягнення епохи — панегіричні вірші та посвяти
  - 'Архітектурні пам''ятки як матеріальні свідчення меценатства — include quote: «Же през шаблю маєм права» (з думи Мазепи);
    повна цитата: «А за волю, хоч умріте...»'
  words: 450
- section: 'Деколонізаційний погляд: Відновлення правди про мецената'
  points:
  - 'Спростування російських міфів про Мазепу як «зрадника» — [!myth-buster]: Мазепа-будівничий vs Мазепа-Юда; замовчування
    будівництва понад 40 храмів'
  - 'Відновлення історичної правди про культурні досягнення гетьмана — парадокс: анафема лунала в церквах, збудованих гетьманом'
  - Мазепа як символ української незалежності та європейського вибору — культура як державна політика
  - Сучасне переосмислення мазепинської спадщини — повернення імені в назви вулиць та установ
  words: 450
- section: Підсумок
  points:
  - Культурна спадщина Мазепи як основа української національної ідентичності — «кам'яний літопис», що пережив руїну
  - Мазепинське бароко як символ української європейської орієнтації — доказ приналежності до європейського культурного простору
  words: 450
- section: Читання
  points:
  - Додаткові матеріали про культурні досягнення епохи Мазепи — уривок про диспут в Академії або опис собору
  words: 500
vocabulary_hints:
  required:
  - меценат (patron) — Мазепа як «превеликий ктитор» і меценат; витрати понад 1 млн дукатів
  - бароко (baroque) — мазепинське бароко, українське бароко, козацьке бароко; «гра світла»
  - гравюра (engraving) — мідьорит, панегірична гравюра, школа гравюри; «Мазепа серед добрих справ»
  - партесний спів (polyphonic chant) — багатоголосся, церковний хор
  - панегірик (panegyric) — хвалебний вірш, присвята гетьману; Феофан Прокопович
  - друкарня (printing house) — Лаврська друкарня, видання книг
  - шкільна драма (school drama) — шкільний театр, інтермедія; «Володимир»
  - багатоголосся (polyphony) — партесний концерт, музична гармонія
  recommended:
  - іконостас (iconostasis) — різьблений іконостас, бароковий іконостас
  - культурне відродження (cultural renaissance) — золота доба, розквіт культури; Мазепинська доба
  - архітектурний стиль (architectural style) — особливості стилю, національний стиль
  - літописець (chronicler) — козацький літописець, Самійло Величко
activity_hints:
- type: reading
  focus: Cultural achievements of Mazepa's era
  items: 1
- type: essay-response
  focus: Decolonizing the narrative about Mazepa
  items: 1
- type: critical-analysis
  focus: 'Критичний аналіз послідовності: Major cultural projects during Mazepa''s rule'
  items: 1
- type: critical-analysis
  focus: 'Критична оцінка: Baroque architecture and art'
  items: 1
persona:
  voice: Senior Professor of History
  role: Baroque Architect
grammar:
- Історичний наратив
- Культурна термінологія
register: публіцистичний
prerequisites:
- ivan-mazepa-derzhavnyk
connects_to:
- kost-hordiyenko-sich

```

---

## PART 1: Deep Research

Research **Іван Мазепа II: освіта і культура** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Іван Мазепа II: освіта і культура

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Іван Мазепа II: освіта і культура"
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
