# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-138
level: HIST
sequence: 138
slug: mizhnarodna-pidtrymka
version: '2.0'
title: Міжнародна підтримка
subtitle: International Support for Ukraine
focus: history
pedagogy: CBI
phase: HIST.13 [Russian Aggression]
word_target: 5000
objectives:
- Учень може описати форми міжнародної підтримки України
- Учень може пояснити роль різних країн та організацій
- Учень може проаналізувати санкції проти Росії
- Учень може оцінити значення міжнародної солідарності
content_outline:
- section: 'Вступ: Україна не сама'
  points:
  - '24 лютого 2022: світ реагує — безпрецедентна консолідація на відміну від «глибокого занепокоєння» 2014 року — географія
    підтримки від США/ЄС до Японії, Австралії та Нової Зеландії'
  - Від слів до дій — феномен «народної дипломатії» (прапори на будинках) та миттєва реакція урядів
  - Чому підтримка України важлива для світу — [!context] порівняння з самотністю УНР у 1917-1921 роках — контраст «самотність
    на полі бою» проти «глобальної коаліції»
  words: 850
- section: Військова допомога
  points:
  - 'США: найбільший донор — Закон про ленд-ліз (9.05.2022) та візит Байдена до Києва (20.02.2023) під звуки повітряної тривоги'
  - 'Великобританія: перші поставки — лідерство у наданні NLAW та підготовці військових (етап «партизанської війни»)'
  - Європейський Союз та його країни — надання статусу кандидата (23.06.2022) як геополітичний сигнал
  - 'Еволюція: від касок до танків — [!history-bite] етапи: «партизанський» (Javelin/NLAW) → «артилерійський» (M777/CAESAR)
    → «HIMARS-ефект» («літо, яке змінить правила гри») → «бронетанковий» (Leopard/Abrams) → авіаційний (F-16)'
  words: 850
- section: Санкції та економічний тиск
  points:
  - Заморожування активів — блокування ~300 млрд доларів резервів ЦБ РФ
  - Відключення від SWIFT — фінансова ізоляція російських банків
  - Енергетичні санкції — ембарго на нафту (з грудня 2022) та цінова стеля ($60), відмова Європи від російського газу як поворотний
    момент
  - Персональні санкції — удар по олігархах та пропагандистах (арешт яхт і вілл)
  - Ефективність санкцій — [!myth-buster] ефект «накопичувальної отрути» проти міфу про недієвість (санкції не діють миттєво,
    але руйнують довгостроково)
  words: 850
- section: Первинні джерела
  points:
  - 'Промови світових лідерів — [!quote] Зеленський у Конгресі США (21.12.2022): «Ваші гроші – це не благодійність. Це інвестиція
    у глобальну безпеку...»'
  - 'Резолюції ООН — документ A/RES/ES-11/1: 141 країна «ЗА» проти 5 країн-ізгоїв (РФ, Білорусь, Сирія, КНДР, Еритрея)'
  - Статистика допомоги — формат «Рамштайн» (з 26.04.2022) як механізм синхронізації оборони 50+ країн («синхронізація годинників»)
  words: 850
- section: Деколонізаційний погляд
  points:
  - Чому Захід так довго ігнорував Росію — [!decolonization] політика «Wandel durch Handel», страх розпаду імперії та віра
    в міф про «другу армію світу»
  - Уроки для світової безпеки — кінець «Westsplaining» і визнання суб'єктності Східної Європи (голос України, Польщі, Балтії
    став визначальним)
  - Україна як форпост демократії — руйнування міфу про «Київ за 3 дні» та російського міфу про «штучну державу»
  words: 850
- section: 'Підсумок: Довга перспектива'
  points:
  - Перспектива членства в ЄС та НАТО — [!reflection] трансформація НАТО через досвід України (приклад Фінляндії/Швеції);
    Україна як суб'єкт, що змінює Альянс
  - План відбудови України — конференція в Лугано, модернізація замість простого ремонту («план Маршалла 2.0»)
  - 'Глобальний південь: неоднозначна позиція — боротьба за нейтральні країни в ООН'
  words: 750
vocabulary_hints:
  required:
  - 'підтримка (support) — collocations: міжнародна, військова, безпрецедентна'
  - 'допомога (aid) — context: інвестиція в безпеку, а не благодійність (Ze quote)'
  - 'санкції (sanctions) — collocations: персональні, секторальні, пакет санкцій, ефект накопичувальної отрути'
  - 'союзник (ally) — context: антипутінська коаліція, Рамштайн'
  - 'донор (donor) — context: найбільший донор безпеки (США)'
  - 'резолюція (resolution) — collocations: ухвалити резолюцію, Генасамблея ООН (141 країна ЗА)'
  - 'солідарність (solidarity) — context: глобальна солідарність з Україною, народна дипломатія'
  - 'відбудова (reconstruction) — collocations: план відбудови, післявоєнна модернізація, план Маршалла 2.0'
  recommended:
  - 'заморожування (freezing) — context: заморожування активів РФ (резервів ЦБ)'
  - 'активи (assets) — context: суверенні активи, конфіскація'
  - 'членство (membership) — collocations: статус кандидата, вступ до ЄС'
  - 'форпост (outpost) — context: форпост демократії на сході'
  - 'дипломатія (diplomacy) — collocations: народна дипломатія, візит лідера'
  - 'коаліція (coalition) — context: танкова коаліція, авіаційна коаліція, Рамштайн'
  - 'суб''єктність (subjectivity/agency) — context: Україна довела свою суб''єктність'
  - 'ізоляція (isolation) — context: міжнародна ізоляція РФ'
activity_hints:
- type: reading
  focus: Промови світових лідерів про Україну
  source: Офіційні джерела
  items: 4
- type: essay-response
  focus: Чому підтримка України — це захист демократії у світі?
connects_to:
- hist-139 (Злочини і стійкість)
- 'hist-140 (Синтез: Війна)'
prerequisites:
- hist-137 (Громадянське суспільство)
persona:
  voice: Senior Professor of History
  role: Foreign Affairs Minister
grammar:
- Теперішній та минулий час
- Дипломатична та економічна лексика
- Складнопідрядні речення
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Міжнародна підтримка** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Міжнародна підтримка

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Міжнародна підтримка"
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
