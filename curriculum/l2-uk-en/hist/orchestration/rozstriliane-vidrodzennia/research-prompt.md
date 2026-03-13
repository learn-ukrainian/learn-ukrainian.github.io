# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-098
level: HIST
sequence: 98
slug: rozstriliane-vidrodzennia
version: '2.0'
title: 'Розстріляне відродження: Постаті'
subtitle: 'The Executed Renaissance: Key Figures'
focus: history
pedagogy: CBI
phase: HIST.10 [WWII & Soviet Terror]
word_target: 5000
objectives:
- Учень може описати ключові постаті Розстріляного відродження
- Учень може пояснити концепцію «Геть від Москви» та «психологічної Європи»
- Учень може проаналізувати культурне значення будинку «Слово»
- Учень може оцінити трагічну долю покоління 1920-х років
content_outline:
- section: 'Вступ: Покоління мрійників'
  points:
  - '1920-ті: культурний ренесанс — політика «українізації» як вікно можливостей для розвитку; заснування «Гарту» (1923)'
  - 'Хто такі «розстріляні» — масштаб явища: література, театр (Курбас), живопис (Бойчук), наука; інтеграція в європейський
    контекст'
  - Чому їх знищили — трагедія покоління, яке повірило у можливість української культури в межах соціалізму; превентивний
    удар імперії
  - 'Engagement Hook: [!context] — Термін «Розстріляне відродження» виник не в Україні, а в еміграції (Лавріненко/Ґедройць,
    1959 антологія)'
  words: 850
- section: Ключові постаті
  points:
  - 'Микола Хвильовий: «Геть від Москви» — концепція «психологічної Європи» та орієнтація на «фаустівську людину»; самогубство
    13.05.1933'
  - 'Микола Зеров: неокласики — гасло «Ad fontes!» (до джерел) та висока елітарна культура проти масовізму; переклади античної
    літератури'
  - 'Лесь Курбас: театр «Березіль» — перетворення театру з етнографічного на європейський модерний (експресіонізм, конструктивізм)'
  - 'Михайло Бойчук: монументальний живопис — школа «бойчукізму», синтез візантійського мистецтва (неовізантизм) та українського
    примітиву'
  - 'Інші жертви: Семенко, Куліш, Яловий — арешт Ялового як сигнал для самогубства Хвильового'
  - 'Engagement Hook: [!quote] — «Геть від Москви! Дайош Європу!» (М. Хвильовий) — гасло, яке стало вироком'
  words: 850
- section: Будинок «Слово»
  points:
  - Колективний дім письменників — Харків, вул. Культури 9, форма літери «С» (збудований 1929), ідея комфорту для творчості
  - Хто там жив — кооператив літераторів, де мешкала еліта нації; початок арештів (справа СВУ)
  - Арешти та знищення — із 66 квартир репресій не зазнали мешканці лише кількох
  - Символ культурного геноциду — атмосфера жаху та нічні «чорні воронки» з 1933 року
  - 'Engagement Hook: [!history-bite] — Харків''яни називали цей будинок «БПУ» — «Будинок Попереднього Ув''язнення»'
  - 'Engagement Hook: [!myth-buster] — Міф про розкішне життя письменників vs реальність пастки з прослуховуванням'
  words: 850
- section: Первинні джерела
  points:
  - 'Твори Хвильового — памфлети, які ставили питання руба: Україна чи Малоросія?'
  - Листи та щоденники — свідчення про атмосферу та внутрішній стан митців; очікування арешту
  - Фотографії та документи НКВД — розстрільні списки за підписом Сталіна, ретушовані фото ВАПЛІТЕ (зникнення облич)
  words: 850
- section: Деколонізаційний погляд
  points:
  - 'Радянський наратив: «буржуазні націоналісти» — ярлик для будь-якого прояву української суб''єктності та культурної окремішності'
  - 'Реальність: цілеспрямоване знищення еліти — превентивний удар імперії проти модерної нації, що могла конкурувати з російською'
  - Культурний геноцид як частина Голодомору — знищення носіїв культури паралельно з фізичним знищенням селянства
  - 'Engagement Hook: [!decolonization] — Радянська влада нищила не «шпигунів», а творців нації-конкурента'
  words: 850
- section: 'Підсумок: Сандармох і пам''ять'
  points:
  - 'Місце розстрілів: Сандармох — урочище в Карелії, 27 жовтня – 4 листопада 1937 (до 20-річчя Жовтневої революції)'
  - Відновлення пам'яті після 1991 — роль Юрія Дмитрієва у віднайденні поховань (1997); нині політв'язень РФ
  - Спадщина Розстріляного відродження — повернення імен як повернення суб'єктності; «Соловецький етап»
  - 'Engagement Hook: [!culture] — «Список Сандармоху» (1111 осіб, 287 українців) — цвіт нації, знищений капітаном Матвєєвим'
  words: 750
vocabulary_hints:
  required:
  - відродження (renaissance) — розстріляне відродження, культурне відродження, українське відродження
  - репресії (repressions) — сталінські репресії, жертва репресій, масові репресії 1930-х
  - письменник (writer) — українські письменники, спілка письменників, арештований письменник
  - митець (artist) — репресовані митці, творчість митця, доля митця
  - розстріл (execution) — масові розстріли, розстрільні списки, стаття розстрілу, розстріл в урочищі
  - НКВД (NKVD) — органи НКВД, агенти НКВД, допити в НКВД, кат НКВД
  - культура (culture) — українська культура, розвиток культури, нищення культури, європейська культура
  - геноцид (genocide) — культурний геноцид, політика геноциду, визнання геноциду
  recommended:
  - неокласики (neoclassicists) — група неокласиків, київські неокласики, лідер неокласиків
  - авангард (avant-garde) — мистецький авангард, європейський авангард, український авангард
  - театр (theater) — театр «Березіль», реформа театру, курбасівський театр
  - живопис (painting) — монументальний живопис, школа бойчукістів, український живопис
  - Сандармох (Sandarmokh) — урочище Сандармох, розстріли в Сандармоху, список Сандармоху
  - реабілітація (rehabilitation) — посмертна реабілітація, процес реабілітації, юридична реабілітація
activity_hints:
- type: reading
  focus: Уривки з творів Хвильового
  source: Літературні твори
  items: 4
- type: essay-response
  focus: Чому радянська влада знищила покоління українських митців 1920-х років?
connects_to:
- hist-102 (Голодомор)
- hist-115 (Шістдесятники)
prerequisites:
- hist-100 (Механізм терору)
persona:
  voice: Senior Professor of History
  role: Avant-garde Director
grammar:
- Минулий час у біографічному наративі
- Літературна та мистецька лексика
- Пасивні конструкції
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Розстріляне відродження: Постаті** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Розстріляне відродження: Постаті

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Розстріляне відродження: Постаті"
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
