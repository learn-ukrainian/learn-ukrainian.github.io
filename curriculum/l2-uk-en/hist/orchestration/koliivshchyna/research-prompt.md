# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-071
level: HIST
sequence: 71
slug: koliivshchyna
version: '2.0'
title: 'Коліївщина: Гайдамацький дух'
subtitle: 'Koliivshchyna: The Haidamaka Spirit'
focus: history
pedagogy: CBI
phase: B2.3b [Українська історія]
word_target: 5000
objectives:
- Учень може пояснити причини Коліївщини
- Учень може охарактеризувати роль Максима Залізняка та Івана Гонти
- Учень може проаналізувати значення Уманської різні
- Учень може оцінити вплив повстання на історію України
content_outline:
- section: 'Вступ: Пролог у сакральному Холодному Яру'
  points:
  - Холодний Яр як символ козацького духу — [!context] «місце сили» українського опору, зв'язок з холодноярцями 1920-х
  - Географія та стратегічне значення лісів Правобережжя — Мотронинський монастир на місці скіфського городища
  - 'Чому 1768 рік став переломним — Травень 1768: початок збору повстанців'
  words: 250
- section: 'Соціально-економічне тло: Анатомія колоніального гніту на Правобережжі'
  points:
  - Польська шляхта та кріпосницький гніт — панщина 5-6 днів, «Золотий спокій» шляхти коштом селян
  - Релігійні утиски православних — [!history-bite] Барська конфедерація (лютий 1768) оголосила захист католицизму метою
  - Економічна експлуатація селянства
  - Конфедерати vs дисиденти
  words: 250
- section: 'Духовний провід: Мелхіседек Значко-Яворський та роль Мотронинського монастиря'
  points:
  - Мотронинський монастир як духовний центр — штаб і притулок повстанців
  - Легенда про освячення ножів — [!myth-buster] Мелхіседек ймовірно не освячував особисто (був у від'їзді), але міф сакралізував
    війну
  - Роль православного духовенства — чутки про «Золоту грамоту» Катерини II
  words: 250
- section: 'Життя та побут гайдамаки: Лицарі вільного лісового братства'
  points:
  - Хто ставав гайдамакою — соціальний портрет — селяни-втікачі, запорозька сірома, міщани, дрібне духовенство
  - Організація загонів та командування — відновлення полково-сотенного устрою Гетьманщини
  - Повсякденне життя у таборах — сувора дисципліна, заборона алкоголю в походах
  - Гайдамацький кодекс честі
  words: 250
- section: 'Максим Залізняк: Запорозький гарт та народний провідник повстання'
  points:
  - Біографія до повстання — [!biography] послушник -> запорожець -> отаман; родом з Чигиринщини (с. Івківці)
  - 'Військовий талант та харизма — 26 травня (6 червня) 1768: вихід із Холодного Яру'
  - Союз із Запорозькою Січчю
  words: 250
- section: 'Читання: Трагічні хроніки Уманської облоги та штурму'
  points:
  - 'Хронологія подій червня 1768 — 10 (21) червня: взяття Умані'
  - Роль Івана Гонти — зрада чи повстання? — [!analysis] «Гонта — не зрадник, а мученик, що обрав свій народ»
  - Уманська різня — факти vs пропаганда — термін Rzeź humańska vs Взяття Умані
  words: 250
- section: 'Кодня: Голгофа гайдамаччини та механізм державного терору'
  points:
  - Російсько-польська змова проти повстанців — арешт лідерів 27 червня (8 липня) 1768 підступно генералом Кречетніковим
  - Масові страти та катування — [!fact] понад 3000 страчених; «Коднянська книга»
  - Доля Залізняка та Гонти — Гонта страчений у липні 1768 (шкіру здерто), Залізняк засланий у Нерчинськ (листопад 1768)
  words: 250
- section: 'Коліївщина у філософському вимірі: Свобода, Жертовність та Справедливість'
  points:
  - Народне право на повстання — концепт «люди довгої волі»
  - Етичні дилеми насильства — жорстокість як відповідь на системне насильство
  - Пам'ять vs помста
  words: 250
- section: 'Повсякдення гайдамацького табору: Від світанку до сутінків у лісах'
  points:
  - Матеріальна культура повстанців
  - Їжа, одяг, зброя — куліш, дичина; списи, «колії» (ножі), шаблі
  - Пісні біля вогнища — «Гей, літав орел, літав сизий...»
  words: 250
- section: 'Гайдамаччина в мистецтві: Живопис та Скульптура як пам''ять нації'
  points:
  - Картини Тараса Шевченка — ілюстрації Сластіона до поеми «Гайдамаки»
  - Пам'ятники Залізнякові та Гонті — в Умані та Холодному Яру
  words: 250
- section: 'Народний епос про гайдамаків: Кобзарські думи та сила живого слова'
  points:
  - Думи про гайдамаків — «Максим козак Залізняк»
  - Усна традиція збереження пам'яті — фольклор як єдине правдиве джерело в умовах цензури
  words: 250
- section: 'Деколонізаційний погляд: Міфи імперій та справжня українська реальність'
  points:
  - Польська історіографія — «різня» та «бунт» — Bunt / Rozruchy
  - Російська історіографія — «розбійники» — [!decolonization] імперія використала гайдамаків, а потім знищила
  - Українська деколонізація — національно-визвольний рух — відновлення державності
  words: 250
- section: 'Мова повстання: Лексика як дзеркало ідеології та світогляду месників'
  points:
  - Гайдамацька термінологія — Віра, Правда, Воля
  - 'Ключові слова: коліївщина, гайдамака, різун — соціально-економічні терміни: «ляхи», «орендарі»'
  words: 250
- section: 'Гайдамацькі пісні: Жива історія у звуках, словах та героїчних образах'
  points:
  - Аналіз пісенних текстів — «Да лине чутка по всім світі»
  - Музична традиція
  words: 250
- section: Балтський інцидент та його масштабне геополітичне відлуння у Європі
  points:
  - Міжнародний контекст повстання — перехід кордону в Балту (Османська імперія)
  - Реакція європейських держав — формальний привід для російсько-турецької війни 1768–1774
  words: 250
- section: 'Спадщина в кінематографі: Від німого кіно до сучасної драми'
  points:
  - Фільми про гайдамаків — фільм «Коліївщина» (1933) як радянська агітка
  - Сучасні екранізації — потреба в сучасному осмисленні
  words: 250
- section: Первинні джерела та їх критичний лінгвістичний аналіз для сучасних дослідників
  points:
  - Польські хроніки та їх упередженість — мемуари учасників, необхідність читати «між рядків»
  - Народні перекази та фольклор
  - Сучасні археологічні знахідки — «Уманський літопис»
  words: 250
- section: 'Сучасні паралелі: Коліївщина та екзистенційні виклики XXI століття для України'
  points:
  - 'Боротьба за свободу як константа історії — тяглість боротьби: Гайдамаччина -> УНР -> Сучасна війна'
  - Уроки для сучасності — небезпека надії на «союзників» (російська гібридна тактика)
  words: 250
- section: Підсумок
  points:
  - Значення Коліївщини для національної свідомості
  - Від повстання до символу
  words: 500
vocabulary_hints:
  required:
  - 'гайдамака (haidamak rebel) — козак-повстанець; collocations: загін гайдамаків, гайдамацький рух'
  - коліївщина (Koliivshchyna uprising) — національно-визвольне повстання 1768 року
  - 'різня (massacre) — Уманська різня; context: трагічні події'
  - кріпацтво (serfdom) — посилення кріпацтва як причина повстання
  - 'повстання (uprising) — collocations: вибухнуло повстання, придушити повстання'
  - 'шляхта (Polish nobility) — context: польська шляхта, маєтки шляхти'
  - православ'я (Orthodoxy) — захист православної віри
  - гніт (oppression) — соціальний та релігійний гніт
  recommended:
  - 'загін (detachment) — collocations: гайдамацький загін'
  - отаман (ataman/leader) — Максим Залізняк, Іван Гонта
  - освячення (consecration) — освячення ножів (легенда)
  - страта (execution) — масові страти в Кодні
  - мученик (martyr) — Гонта як мученик за народ
  - сірома (poor Cossacks) — соціальна база повстання
  - ляхи (Poles - historical/derogatory) — historical term used in sources
  - катування (torture) — жорстокі катування учасників
activity_hints:
- type: reading
  focus: Первинні джерела про Уманську облогу
  items: 4
- type: essay-response
  focus: Етична оцінка насильства у визвольній боротьбі
- type: comparative-study
  focus: Польська vs українська інтерпретація подій
- type: critical-analysis
  focus: 'Аналіз: Хронологія подій 1768 року'
  items: 3
persona:
  voice: Senior Professor of History
  role: Haidamaka Leader
grammar:
- Історичний наратив
- Емоційно забарвлена лексика
register: публіцистичний
prerequisites:
- danylo-apostol
connects_to:
- opryshky

```

---

## PART 1: Deep Research

Research **Коліївщина: Гайдамацький дух** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Коліївщина: Гайдамацький дух

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Коліївщина: Гайдамацький дух"
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
