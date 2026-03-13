# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-134
level: HIST
sequence: 134
slug: bucha-irpin
version: '2.0'
title: 'Буча та Ірпінь: Злочини'
subtitle: 'Bucha and Irpin: War Crimes'
focus: history
pedagogy: CBI
phase: HIST.13 [Russian Aggression]
word_target: 5000
objectives:
- Учень може описати події російської окупації Бучі та Ірпеня
- Учень може проаналізувати докази воєнних злочинів
- Учень може пояснити міжнародну реакцію та правові наслідки
- Учень може обговорити тему воєнних злочинів відповідною лексикою
content_outline:
- section: 'Вступ: Лютий-березень 2022'
  points:
  - 'Контекст: перші дні повномасштабного вторгнення (24 лютого) — десант у Гостомелі (аеропорт «Антонов») та спроба «бліцкригу»'
  - Наступ на Київ через північні передмістя — річка Ірпінь як природний бар'єр; підрив мостів у Романівці (єдиний шлях евакуації)
    та Стоянці
  - '33 дні окупації — Буча та Ірпінь як «щит» Києва; engagement hook: [!context] про стратегічне значення передмість для
    оборони столиці'
  words: 850
- section: Хроніка окупації
  points:
  - 'Захоплення Бучі та Ірпеня російськими військами — знищення колони «Росгвардії» на вул. Вокзальній (27 лютого); engagement
    hook: [!history-bite] про героїзм ТрО та ЗСУ vs міф «Привида Києва»'
  - 'Життя під окупацією: страх і виживання — відсутність світла, газу, води; життя у підвалах, польові кухні у дворах під
    обстрілами'
  - Масові страти цивільних на вулиці Яблунській — «Вулиця смерті» як штаб окупантів (64-та ОМСБр, псковські десантники);
    «білі пов'язки» як мітка ворога
  - Відступ російських військ (кінець березня) — втеча окупантів під тиском ЗСУ (31 березня); залишення замінованих територій
  words: 850
- section: Виявлення злочинів
  points:
  - Перші фото та відео звільнених міст — шок 1-2 квітня, коли світ та журналісти (AFP, Reuters) побачили тіла на вулицях
  - 'Міжнародна реакція на докази масових убивств — візити світових лідерів; engagement hook: [!quote] Анатолій Федорук: «Ми
    не встигали ховати людей»'
  - 'Робота слідчих: ексгумації та ідентифікація — братська могила (траншея) біля церкви Андрія Первозванного'
  - Кількість жертв та характер злочинів — понад 1400 загиблих у районі (501 у Бучі), зв'язані руки, сліди тортур
  words: 850
- section: Первинні джерела
  points:
  - Свідчення вцілілих мешканців Бучі — проєкт «The Ukrainians», історії про «тишу як загрозу» (цитата Наташі Александрової
    про погляд крізь людей)
  - Звіти міжнародних місій (ООН, ОБСЄ) — підтвердження системності терору (Human Rights Watch); ідентифікація підрозділів
  - 'Супутникові знімки Maxar — engagement hook: [!myth-buster] спростування російського фейку про «постановку» (докази, що
    тіла лежали тижнями)'
  words: 850
- section: Міжнародне правосуддя
  points:
  - Розслідування Міжнародного кримінального суду — візит прокурора Каріма Хана, кваліфікація подій як воєнних злочинів
  - Ордер на арешт Путіна — Буча як частина доказової бази в контексті ширшого геноциду та депортації
  - Українські суди над злочинцями — ідентифікація конкретних виконавців (псковські десантники, «кадирівці», 64-та бригада)
  - 'Порівняльний контекст — engagement hook: [!decolonization] реакція світу на Бучу (онлайн-свідчення) vs Голодомор (інформаційна
    ізоляція)'
  words: 850
- section: Пам'ять і спротив
  points:
  - Меморіалізація жертв — «Стіна пам'яті» біля церкви Андрія Первозванного, нові меморіали на місцях розстрілів
  - Буча як символ російської жорстокості — та Ірпінь як «Місто-Герой», що не пропустив ворога (лінія фронту через місто)
  - 'Відбудова громад — відновлення вулиці Вокзальної, мурали Бенксі; engagement hook: [!culture] мистецтво на руїнах як символ
    стійкості та відродження'
  words: 750
vocabulary_hints:
  required:
  - 'воєнний злочин (war crime) — часто вживається у множині «воєнні злочини РФ»; collocations: скоювати, розслідувати, документувати'
  - 'окупація (occupation) — collocations: тимчасова окупація, пережити окупацію, звільнення з окупації'
  - 'страта (execution) — context: масові страти на вул. Яблунській; synonym: розстріл; collocations: позасудові страти'
  - 'жертва (victim) — collocations: жертви агресії, цивільні жертви, кількість жертв'
  - 'свідчення (testimony) — collocations: свідчення очевидців, збирати свідчення, фіксувати свідчення'
  - 'розслідування (investigation) — collocations: міжнародне розслідування, проводити розслідування, незалежне розслідування'
  - 'ексгумація (exhumation) — context: ексгумація тіл з братських могил для ідентифікації'
  - 'геноцид (genocide) — context: ознаки геноциду українського народу; collocations: визнати геноцидом'
  recommended:
  - 'масове поховання (mass grave) — context: братська могила біля церкви; synonym: братська могила'
  - 'катування (torture) — collocations: сліди катувань, піддавати катуванням, катівня (torture chamber)'
  - 'мародерство (looting) — context: викрадення побутової техніки окупантами; collocations: займатися мародерством'
  - 'депортація (deportation) — context: примусова депортація мешканців до Білорусі/РФ'
  - 'трибунал (tribunal) — context: спеціальний трибунал для керівництва РФ за злочин агресії'
  - 'репарації (reparations) — context: виплата репарацій за завдані збитки та руйнування'
activity_hints:
- type: reading
  focus: Свідчення очевидців подій у Бучі
  source: Українські медіа, ООН
  items: 4
- type: essay-response
  focus: Чому документування злочинів важливе для майбутнього правосуддя?
connects_to:
- hist-135 (Каховська ГЕС)
- hist-139 (Злочини і стійкість)
prerequisites:
- hist-132 (Повномасштабне вторгнення)
- hist-133 (Маріуполь та Азовсталь)
persona:
  voice: Senior Professor of History
  role: Forensic Investigator
grammar:
- Минулий час у документальному наративі
- Пасивний стан для опису злочинів
- Юридична лексика
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Буча та Ірпінь: Злочини** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Буча та Ірпінь: Злочини

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Буча та Ірпінь: Злочини"
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
