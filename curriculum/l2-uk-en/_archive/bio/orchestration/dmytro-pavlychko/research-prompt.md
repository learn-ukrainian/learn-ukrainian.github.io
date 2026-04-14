# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: bio-137
level: BIO
sequence: 137
slug: dmytro-pavlychko
version: '2.0'
title: 'Дмитро Павличко: Поет і дипломат'
focus: biography
phase: BIO
word_target: 5000
objectives:
- 'Analyze the life and legacy of дмитро павличко: поет і дипломат'
- Evaluate the contributions of два кольори однієї душі
- Trace the career and influence of голос україни
sources:
- name: Дмитро Павличко (Wikipedia UA)
  url: https://uk.wikipedia.org/wiki/Павличко_Дмитро_Васильович
  type: primary
  notes: Biography of the poet, translator, and diplomat
- name: Національна спілка письменників України
  url: https://nspu.org.ua/
  type: reference
  notes: Literary biography and works
content_outline:
- section: Вступ — Два кольори однієї душі
  points:
  - Поет, перекладач, політик, дипломат
  - Автор легендарної пісні «Два кольори»
  - Життя між поезією та політикою
  words: 850
- section: Юність і формування (1929-1953)
  points:
  - Народження на Івано-Франківщині
  - Важке повоєнне дитинство
  - Навчання у Львівському університеті
  - Перші вірші та публікації
  words: 850
- section: Поетичний шлях (1953-1970)
  points:
  - Входження в літературу
  - Збірки «Любов і ненависть», «Правда кличе»
  - Пісня «Два кольори» (1965)
  - Шістдесятництво та його межі
  words: 850
- section: Перекладацька діяльність (1960-ті–1990-ті)
  points:
  - Переклади Шекспіра
  - Переклади світової поезії
  - Роль перекладу у збереженні мови
  - Визнання як перекладача
  words: 850
- section: Політик і дипломат (1988-2000-ні)
  points:
  - Участь у Народному Русі
  - Співавтор Акту незалежності
  - Посол України в Польщі та Словаччині
  - Політичні позиції та суперечки
  words: 850
- section: Спадщина — Голос України
  points:
  - Вплив на українську поезію
  - «Два кольори» як другий гімн
  - Пізня творчість
  - Місце в історії літератури
  words: 750
vocabulary_hints:
  required:
  - поет (poet)
  - перекладач (translator)
  - дипломат (diplomat)
  - пісня (song)
  - символіка (symbolism)
  - шістдесятництво (Sixtiers movement)
  - Народний Рух (People's Movement)
  - посол (ambassador)
  - літературна спадщина (literary legacy)
  - ліричний (lyrical)
  recommended:
  - патріотизм (patriotism)
  - поетика (poetics)
  - романтизм (romanticism)
  - політична поезія (political poetry)
  - національна свідомість (national consciousness)
activity_hints:
- type: reading
  focus: Українська поезія XX ст.
  source: Literary sources
  items: 3 passages
- type: essay-response
  focus: Як поезія може впливати на політичні зміни?
  output: Analytical essay
connects_to:
- bio-74
- bio-79
prerequisites:
- bio-72
persona:
  voice: Senior Biographer
  role: Poet Diplomat
module_type: biography
immersion: 100% Ukrainian

```

---

## PART 1: Deep Research

Research **Дмитро Павличко: Поет і дипломат** for the **bio** track. Produce structured research notes that will drive content writing in Phase B.

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

### Mandatory Research Workflow (follow ALL 4 steps in order)

**Step 1 — Wikipedia foundation**: Call `query_wikipedia(mode="extract")` for the main topic article. If the article is long, use `mode="sections"` then `mode="section"` to read key sections. This gives you the factual backbone.

**Step 2 — Literary RAG deep search (MANDATORY)**: Call `search_literary` at least **3 times** with different queries targeting different aspects of the topic. Search for:
- The main subject (person/event/concept name)
- Related figures, institutions, or movements
- The historical period or genre

This is where primary source quotes come from — chronicles, legal texts, poetry, testimonies, scholarly works. Our RAG has 125K+ chunks from litopys.org.ua, izbornyk.org.ua, and scholarly monographs. **Do NOT skip this step even if Wikipedia gave good results.** Wikipedia is secondary; literary RAG has primary sources.

**Step 3 — Cross-verify**: Use `verify_words` to check any Ukrainian vocabulary you plan to highlight. Use `query_grac(mode="frequency")` for frequency data on key terms.

**Step 4 — Fill gaps**: If Steps 1-2 left gaps in any `content_outline` section, do targeted `query_wikipedia` or `search_literary` calls for those specific sections.

### Research Requirements

1. **Sources**: Minimum **4 distinct sources** — at least 1 from Wikipedia AND at least 2 from `search_literary` (RAG). Also consult history.org.ua, litopys.org.ua. Russian-language sources are PROHIBITED. Every factual claim must be traceable to a cited source.
2. **Timeline**: Build a chronological timeline with 5+ dated events/milestones.
3. **Primary Quotes**: Find **3+** quotable primary source excerpts using `search_literary`. Use guillemet quotes «...» for Ukrainian text. If `search_literary` returns relevant chunks, extract and attribute them properly. Mark unverified quotes as `[needs verification]`.
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

# Дослідження: Дмитро Павличко: Поет і дипломат

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Дмитро Павличко: Поет і дипломат"
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
