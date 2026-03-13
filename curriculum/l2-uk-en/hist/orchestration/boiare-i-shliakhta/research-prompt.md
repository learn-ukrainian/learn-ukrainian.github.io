# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: hist-025
level: HIST
sequence: 25
slug: boiare-i-shliakhta
version: '2.0'
title: 'Бояри та шляхта: Соціальна еліта'
subtitle: Лицарська честь та політична суб'єктність
focus: history
pedagogy: CBI
phase: B2.3a [Українська історія]
word_target: 5000
objectives:
- Учень може пояснити різницю між боярством та шляхтою
- Учень розуміє процеси формування привілейованих верств
- Учень може аналізувати вплив права на українську аристократію
content_outline:
- section: Вступ
  points:
  - Поняття "аристократія" в українському контексті — від грец. aristos (найкращий) + kratos (влада); еволюція від варязьких
    дружинників до землевласників
  - Різниця між боярами та дружиною — бояри як родова еліта з вотчиною (прив'язка до землі) на відміну від служилої знаті;
    [!context] про походження терміну «шляхта» від нім. slahta (рід)
  words: 850
- section: Читання
  points:
  - Феномен боярської олігархії в Галичині — унікальний період 1340–1349 рр., коли Дмитро Дедько правив як «староста та управитель»;
    [!history-bite] про силу галицьких бояр
  - '"Золота вольність" шляхти та коріння демократії — право на rokosz (опір королю) та обмеження королівської влади як фундамент
    політичної культури'
  - 'Економічна база: Фільварки та аграрна держава — орієнтація на експорт зерна в Європу через Гданськ; шляхтич як воїн-підприємець'
  - 'Каста магнатів: Володарі України — «королев''ята» (Острозькі, Вишневецькі) з приватними арміями та замками як держави
    в державі'
  - Трансформація у шляхетський стан — юридичне оформлення прав через Литовські Статути (1529, 1566) та Єдлінський привілей
    (1430); [!myth-buster] про концепцію Gente Ruthenus, natione Polonus
  - Полонізація та збереження ідентичності — прагматичні мотиви (доступ до сенату, судів) vs. збереження «руської віри»; поступовість
    процесу
  words: 850
- section: Первинні джерела
  points:
  - Грамота короля Сигізмунда ІІ Августа (1569) — гарантія мовних прав та принцип «рівні до рівних, вільні до вільних» як
    основа унії
  - Свідчення літописця про Боярську раду — Галицько-Волинський літопис про свавілля бояр («не почавивши бджіл, меду не їсти»);
    [!quote] з першоджерела
  words: 850
- section: Деколонізаційний погляд
  points:
  - Спростування міфу про "відсутність власної еліти" — [!decolonization] протиставлення імперського міфу про «націю попів
    та хлопів» реальності європейської інтегрованості української шляхти
  - Шляхта як носій української політичної культури — культура договору і закону на противагу московській культурі підданства
    і самодержавства
  words: 850
- section: Підсумок — Еліта вільної України
  points:
  - 'Еволюція еліти — термінологічний перехід: бояри -> зем''яни -> шляхта'
  - Юридичні гарантії — верховенство Статуту (закону) над волею монарха
  - Лицарська культура — [!culture] геральдична спадщина (герби Леліва, Абданк) та тяглість елітарної культури до козацької
    старшини
  words: 850
- section: Потрібно більше практики?
  points:
  - Додаткові ресурси
  words: 750
vocabulary_hints:
  required:
  - 'шляхта (nobility) — ключовий термін; collocations: українська шляхта, права шляхти'
  - 'боярин (boyar) — історичний попередник шляхтича; collocations: галицькі бояри'
  - 'привілей (privilege) — юридичний документ; collocations: королівський привілей, підтвердити привілеї'
  - 'сейм (diet/parliament) — орган станового представництва; collocations: вальний сейм'
  - 'статут (statute) — збірник законів; collocations: Литовський Статут'
  - 'вольність (liberty) — політична свобода; collocations: золота вольність, шляхетські вольності'
  - 'магнат (magnate) — великий землевласник; collocations: магнатські роди'
  - 'фільварок (manor farm) — господарська одиниця; collocations: заснувати фільварок'
  recommended:
  - 'олігархія (oligarchy) — форма правління; collocations: боярська олігархія'
  - 'автономія (autonomy) — самоврядування; collocations: зберегти автономію'
  - 'інкорпорація (incorporation) — включення до складу; collocations: акт інкорпорації'
  - 'ієрархія (hierarchy) — соціальна структура; collocations: станова ієрархія'
activity_hints:
- type: reading
  focus: Первинні джерела
  items: 4
- type: essay-response
  focus: Критичний аналіз
- type: critical-analysis
  focus: Аналіз причинно-наслідкових зв'язків між подіями
  items: 3
- type: critical-analysis
  focus: Критична оцінка історичних тверджень та міфів
  items: 5
persona:
  voice: Senior Professor of History
  role: Council Lord
grammar:
- Social terminology
- Formal address forms
prerequisites:
- galytsko-volynska-derzhava
connects_to:
- kinets-halytsko-volyni

```

---

## PART 1: Deep Research

Research **Бояри та шляхта: Соціальна еліта** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Бояри та шляхта: Соціальна еліта

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — Phase D verifies prose against this -->
```yaml
subject: "Бояри та шляхта: Соціальна еліта"
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
