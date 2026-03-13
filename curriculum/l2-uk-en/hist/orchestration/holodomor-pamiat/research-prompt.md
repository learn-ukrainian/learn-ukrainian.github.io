# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-102
level: HIST
sequence: 102
slug: holodomor-pamiat
version: '2.0'
title: 'Голодомор: Пам''ять та визнання'
subtitle: 'Holodomor: Memory and Recognition'
focus: history
pedagogy: CBI
phase: HIST.10 [Soviet Period & Tragedies]
word_target: 5000
objectives:
- Учень може описати історію боротьби за визнання Голодомору
- Учень може пояснити роль Гарета Джонса та інших свідків
- Учень може проаналізувати механізми радянського заперечення
- Учень може оцінити значення міжнародного визнання геноциду
content_outline:
- section: 'Вступ: Злочин без кари'
  points:
  - 'Радянське замовчування Голодомору — фальсифікація метричних книг (причина смерті: «старість», «виснаження»), табу на
    слово «голод» як антирадянська агітація'
  - Чому світ не знав? — політика realpolitik Заходу (Франція, США) та визнання СРСР США у 1933 році попри звіти дипломатів
  - 'Роль пам''яті у відновленні справедливості — hook: [!history-bite] Рафаель Лемкін розробляв концепцію геноциду саме на
    українському досвіді, виділяючи 4 складові (розум/інтелігенція, душа/церква, тіло/селянство, розпорошення)'
  words: 850
- section: Свідки та журналісти
  points:
  - 'Гарет Джонс: валлієць, який сказав правду — подорож пішки селами Харківщини у березні 1933-го, прес-конференція у Берліні;
    щоденникові записи «Всі опухлі від голоду»'
  - 'Волтер Дюранті: пропаганда замість правди — hook: [!myth-buster] Пулітцерівська премія 1932 року за брехливі репортажі
    в NYT («Russians are hungry but not starving», 31.03.1933) досі не відкликана; цинічне «You can''t make an omelet without
    breaking eggs»'
  - Маргарет Барбер, Малкольм Маггерідж (Manchester Guardian) — репортажі дипломатичною поштою, визначення голоду як «війни
    режиму проти селянства»
  - Радянська дезінформація — організація показових турів («потьомкінські села») для іноземців, заперечення фактів на офіційному
    рівні
  words: 850
- section: Боротьба за визнання
  points:
  - 'Діаспора та збереження пам''яті — hook: [!context] роль UCCA та діаспори у збереженні свідчень, доки в Україні тема була
    заборонена'
  - Комісія Конгресу США (1980-ті) — Комісія Джеймса Мейса (1985–1988) та збір тисяч свідчень (Oral History Project) як юридична
    база
  - Проголошення незалежності та відкриття архівів — оприлюднення документів про «чорні дошки» та директиви Сталіна/Молотова,
    що доводять умисел
  - Закон України про Голодомор (28 листопада 2006) — офіційна кваліфікація як геноцид та криміналізація публічного заперечення
  - Міжнародне визнання — хвиля рішень парламентів ЄС (Німеччина, Франція, Італія, 2022–2024) на тлі сучасної війни
  words: 850
- section: Первинні джерела
  points:
  - 'Статті Гарета Джонса — hook: [!quote] «Я пройшов через села... Скрізь я чув стогін: У нас немає хліба, ми помираємо!»
    (з статті «Famine Rules Russia» / «Good-bye Russia»)'
  - Свідчення вцілілих — щоденники селян (напр. вчителя Олексія Наливайка) та листи іноземних інженерів (Джеррі Берман)
  - Резолюції про визнання геноциду — Естонія (1993, перша у світі), Канада (2003), США (2018)
  words: 850
- section: Деколонізаційний погляд
  points:
  - 'Голодомор як геноцид: юридичні аргументи — відповідність Конвенції ООН 1948 року (умисне створення умов для фізичного
    знищення групи)'
  - Російське заперечення сьогодні — знищення пам'ятників Голодомору на окупованих територіях (Маріуполь, Луганщина) як доказ
    спадковості злочину
  - 'Пам''ять vs. пропаганда — hook: [!decolonization] концепція Джеймса Мейса про «постгеноцидне суспільство» та травму національної
    душі; русифікація вимерлих сіл переселенцями з Росії'
  words: 850
- section: 'Підсумок: Чому це важливо'
  points:
  - 'День пам''яті жертв Голодомору — hook: [!culture] традиція «Запали свічку» (4-та субота листопада), ініційована Джеймсом
    Мейсом як акт національного єднання живих і мертвих'
  - Музеї та меморіали — Національний музей Голодомору-геноциду в Києві як місце пам'яті та освіти
  - 'Уроки для майбутнього — непокаране зло повертається: зв''язок між відсутністю «Нюрнберга» над комунізмом та сучасною
    агресією РФ'
  words: 750
vocabulary_hints:
  required:
  - Голодомор (Holodomor) — Голодомор-геноцид, жертви Голодомору, штучний голод
  - геноцид (genocide) — Конвенція ООН, визнання геноцидом, Рафаель Лемкін, ознаки геноциду
  - визнання (recognition) — міжнародне визнання, боротьба за визнання, дипломатичне визнання
  - замовчування (silencing) — радянське замовчування, стіна мовчання, змова мовчання
  - свідок (witness) — живі свідки, свідчення очевидців, збирати свідчення
  - пам'ять (memory) — національна пам'ять, збереження пам'яті, День пам'яті жертв Голодомору, місця пам'яті
  - меморіал (memorial) — відкриття меморіалу, місце пам'яті, Національний музей
  - заперечення (denial) — кримінальна відповідальність за заперечення, російська пропаганда, політика заперечення
  recommended:
  - комісія (commission) — Комісія Конгресу США, Комісія Джеймса Мейса, висновки комісії
  - резолюція (resolution) — ухвалити резолюцію, парламентська резолюція, проект резолюції
  - архів (archive) — розсекречення архівів, архівні документи (чорні дошки), доступ до архівів
  - дезінформація (disinformation) — кампанія дезінформації, Волтер Дюранті, радянська пропаганда
  - жертва (victim) — вшанування жертв, мільйони жертв, невинні жертви
  - справедливість (justice) — відновлення історичної справедливості, злочин без кари
activity_hints:
- type: reading
  focus: Статті Гарета Джонса
  source: Архівні матеріали
  items: 4
- type: critical-analysis
  focus: 'Спростування міфів: Факти та міфи про Голодомор'
  items: 5
- type: essay-response
  focus: Чому міжнародне визнання Голодомору геноцидом важливе для України?
connects_to:
- hist-118 (Діаспора)
- 'hist-108 (Синтез: Трагедії XX століття)'
prerequisites:
- 'hist-101 (Голодомор: Механізм)'
persona:
  voice: Senior Professor of History
  role: Memorial Keeper
grammar:
- Минулий та теперішній час у наративі пам'яті
- Пасивні конструкції для опису злочинів
- Юридична та мемориальна лексика
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Голодомор: Пам'ять та визнання** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Голодомор: Пам'ять та визнання

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Голодомор: Пам'ять та визнання"
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
