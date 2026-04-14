# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: bio-044
level: BIO
sequence: 44
slug: ivan-nechuy-levytskyi
version: '2.0'
title: 'Іван Нечуй-Левицький: Майстер українського реалізму'
focus: biography
phase: BIO
word_target: 5000
objectives:
- 'Analyze the life and legacy of іван нечуй-левицький: майстер українського реалізму'
- Evaluate the contributions of великий оповідач
- Trace the career and influence of останні роки та спадщина
sources:
- name: Іван Нечуй-Левицький (Wikipedia UA)
  url: https://uk.wikipedia.org/wiki/Іван_Нечуй-Левицький
  type: primary
  notes: Biography, works, literary significance
- name: Кайдашева сім'я
  url: https://uk.wikipedia.org/wiki/Кайдашева_сім%27я
  type: reference
  notes: His most famous novel
- name: Микола Джеря
  url: https://uk.wikipedia.org/wiki/Микола_Джеря
  type: reference
  notes: Novel about serfdom and industrialization
- name: Український реалізм
  url: https://uk.wikipedia.org/wiki/Реалізм_(література)
  type: reference
  notes: Literary movement context
- name: UkrLib - Нечуй-Левицький
  url: https://www.ukrlib.com.ua/bio/printit.php?tid=1646
  type: reference
  notes: Full texts and analysis
content_outline:
- section: Вступ — Великий оповідач
  points:
  - Нечуй-Левицький як вершина українського реалізму
  - Його унікальний "візуальний" стиль
  - Значення для становлення літературної мови
  words: 700
- section: Походження та освіта
  points:
  - Народження в родині священика (1838)
  - Навчання в Київській духовній академії
  - Вплив Шевченка та народницьких ідей
  - Перші літературні спроби
  words: 700
- section: Учительська кар'єра
  points:
  - Викладання в різних містах України
  - Спостереження за життям різних верств
  - Збирання матеріалу для творів
  - Конфлікти з цензурою
  words: 700
- section: '"Кайдашева сім''я" — шедевр реалізму'
  points:
  - Історія створення (1878)
  - Родинний конфлікт як дзеркало суспільства
  - Образи Кайдашихи, Мотрі, Омелька
  - '"Війна за грушу" — символ дрібних чвар'
  - Гумор і трагізм поєднані
  words: 700
- section: '"Микола Джеря" та соціальна критика'
  points:
  - Тема кріпацтва та втечі
  - Індустріалізація в українській літературі
  - Образ "нового українського героя"
  - Порівняння села та міста
  words: 700
- section: Мовна революція
  points:
  - Автентична народна мова в літературі
  - Діалектизми Київщини
  - Лайка як літературний прийом
  - Полеміка про мовні норми
  - Конфлікт із Грінченком
  words: 700
- section: Останні роки та спадщина
  points:
  - Життя під час революції 1917
  - Смерть від голоду в 1918 році
  - Трагічна іронія долі письменника
  - Вплив на українську літературу XX століття
  words: 800
vocabulary_hints:
  required:
  - реалізм (realism)
  - оповідач (narrator/storyteller)
  - кріпацтво (serfdom)
  - селянство (peasantry)
  - родинний конфлікт (family conflict)
  - діалектизм (dialectism)
  - просторіччя (colloquial speech)
  - візуальний стиль (visual style)
  - народницький (populist)
  - етнографічний (ethnographic)
  recommended:
  - дрібні чвари (petty quarrels)
  - сільський побут (village life)
  - соціальна критика (social criticism)
  - натуралізм (naturalism)
  - мовна полеміка (language polemic)
activity_hints:
- type: reading
  focus: Excerpts from "Кайдашева сім'я" and "Микола Джеря"
  source: UkrLib
  items: 4 passages
- type: essay-response
  focus: Why is "Кайдашева сім'я" still relevant today?
  output: Social analysis with modern parallels
- type: critical-analysis
  focus: Compare Nechuy-Levytsky with European realists (Zola, Dickens)
  output: Comparative literature analysis
connects_to:
- lit-26 through lit-30 (Literary analysis of Nechuy's works)
- bio-47 (Marko Vovchok - contemporary)
- bio-31 (Olha Kobylianska - later realist)
prerequisites:
- bio-102 (Kvitka-Osnovianenko - predecessor)
- bio-28 (Ivan Franko - contemporary)
- Understanding of literary realism
persona:
  voice: Senior Biographer
  role: Ethnographic Observer
module_type: biography
immersion: 100% Ukrainian

```

---

## PART 1: Deep Research

Research **Іван Нечуй-Левицький: Майстер українського реалізму** for the **bio** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Іван Нечуй-Левицький: Майстер українського реалізму

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — Phase D verifies prose against this -->
```yaml
subject: "Іван Нечуй-Левицький: Майстер українського реалізму"
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
