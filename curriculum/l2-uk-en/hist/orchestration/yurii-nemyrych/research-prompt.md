# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-057
level: HIST
sequence: 57
slug: yurii-nemyrych
version: '2.0'
title: 'Юрій Немирич: Гадяцька угода'
subtitle: 'Yurii Nemyrych: The Treaty of Hadiach'
focus: history
pedagogy: CBI
phase: HIST.6 [Khmelnytsky & Cossack State]
word_target: 5000
objectives:
- Учень може пояснити суть проекту 'Великого Князівства Руського'
- Учень може проаналізувати причини провалу Гадяцької угоди
- Учень може оцінити роль Юрія Немирича як інтелектуала в політиці
sources:
- name: The Treaty of Hadiach - Encyclopedia of Ukraine
  url: https://www.encyclopediaofukraine.com/display.asp?linkpath=pages%5CH%5CA%5CHadiachTreatyof.htm
  type: reference
  notes: Academic summary
- name: Yurii Nemyrych's Speech
  url: http://litopys.org.ua/
  type: primary
  notes: Original text of the speech
content_outline:
- section: Вступ
  points:
  - 'Nemyrych as a unique figure: intellectual and politician — the ''brain'' behind the break with Moscow and turn to Europe'
  - 'The crisis after Khmelnytsky''s death — seeking new allies amidst the collapse of the 1654 protectorate; cultural hook:
    [!context] The concept of the ''Commonwealth of Three Nations'' (Rzeczpospolita Trojga Narodów)'
  words: 500
- section: 'Юрій Немирич: Портрет інтелектуала'
  points:
  - Education in Europe (Leiden, Oxford, Paris) — 1630–1634; studying at Sorbonne and Cambridge, arguably the most educated
    man in Ukraine
  - 'Protestant faith (Arianism) and tolerance — conversion to Orthodoxy in 1657 for political legitimacy; cultural hook:
    [!biography] ''The Ukrainian Machiavelli'' or ''Protestant Humanist'' — how European education shaped his statecraft'
  - Political career in the Commonwealth — author of 'Discursus de bello Moscovitico' (1632)
  words: 500
- section: 'Гадяцька угода 1658: Проект трьох народів'
  points:
  - The concept of the Grand Duchy of Rus' — signed Sept 16, 1658; defining the state as a third equal partner alongside Poland
    and Lithuania
  - 'Equality of rights: religion, language, administration — Nemyrych becomes Chancellor; own treasury, mint, and tribunal'
  - 'The vision of a federal state — army of 30k registered Cossacks + 10k mercenaries; cultural hook: [!myth-buster] The
    ''Polish Intrigue'' myth vs. Reality: A sovereign Ukrainian project for a federal Europe'
  words: 500
- section: Освіта і культура в проекті Немирича
  points:
  - Plans for two academies (universities) — elevating Kyiv-Mohyla to university status (equal to Krakow) + a second new academy
  - Freedom of the press and schools — establishing printing presses and gymnasiums 'as many as needed'
  - 'Intellectual foundation for the state — cultural hook: [!culture] Education as a prerequisite for statehood in Nemyrych''s
    vision'
  words: 500
- section: 'Конотопська битва: Тріумф зброї'
  points:
  - The war with Muscovy (1658-1659) — Moscow's reaction to Hadiach as 'treason'
  - 'Victory at Konotop as a defense of the Treaty — June 28-29, 1659; defeat of Trubetskoy''s army; cultural hook: [!history-bite]
    ''The flower of Muscovite cavalry perished in one day'' — Tsar Alexei Mikhailovich preparing to flee Moscow'
  - Vyhovsky's military leadership — coalition warfare (Cossacks + Tatars)
  words: 500
- section: 'Крах великої ідеї: Чому не вийшло?'
  points:
  - Internal opposition (Pushkar, Barabash) — social divide between the 'aristocratic' project and the egalitarian masses
  - Muscovite propaganda and incitement of the masses — early 'hybrid war' tactics using populism and money
  - The tragic death of Nemyrych — murdered in September 1659 near Svydivets; likely by pro-Moscow instigation
  words: 500
- section: Читання
  points:
  - Analysis of the Hadiach Treaty text — focusing on the articles establishing the Grand Duchy of Rus'
  words: 500
- section: Первинні джерела
  points:
  - Analysis of Nemyrych's speech to the Sejm — 'Manifestation' (April 23, 1659); justifying the break with Moscow
  - 'include quote: «Ми, як вільні до вільних і рівні до рівних, повертаємось» — the motto of the union'
  words: 500
- section: Деколонізаційний погляд
  points:
  - Hadiach as an alternative to Pereiaslav — European legal tradition vs. Asian despotism
  - 'The myth of ''inevitable unity'' with Russia — cultural hook: [!decolonization] Dismantling the Soviet label of Nemyrych
    as a ''traitor'' and ''Polish lord'''
  words: 500
- section: Підсумок
  points:
  - Final evaluation of the project — 'The Grand Illusion' but a precursor to Pylyp Orlyk's Constitution
  words: 500
vocabulary_hints:
  required:
  - федерація (federation) — as opposed to unitary empire or protectorate
  - канцлер (chancellor) — Nemyrych's title in the Grand Duchy of Rus'
  - шляхта (nobility) — the political nation of the Commonwealth
  - сенат (senate) — the upper house of the parliament where Rus' was to be represented
  - академія (academy) — status of a university (Kyiv-Mohyla)
  - триєдина держава (triune state) — Res Publica of Three Nations
  - аріанин (Arian) — Nemyrych's original Protestant confession
  - унія (union) — specifically the Union of Hadiach (1658)
  - розкол (schism/split) — social division exploited by Moscow
  - Руїна (The Ruin) — the period of chaos following the failure of Hadiach
  recommended:
  - протекторат (protectorate) — the failed status under Moscow (1654)
  - маніфестація (manifestation) — public declaration/speech
  - ратифікація (ratification) — approval of the treaty by the Sejm
  - деспотія (despotism) — Nemyrych's characterization of Muscovite rule
activity_hints:
- type: reading
  focus: Analysis of the Hadiach Treaty text
- type: essay-response
  focus: Why the European choice failed in the 17th century
- type: comparative-study
  focus: Pereiaslav vs. Hadiach models
- type: critical-analysis
  focus: 'Верифікація фактів: Facts about the Grand Duchy of Rus'''
  items: 4
persona:
  voice: Senior Professor of History
  role: Protestant Noble
grammar:
- 'Political terminology: federation vs. protectorate'
- 'Historical conditionals: ''what if'' scenarios'
register: публіцистичний
prerequisites:
- pereyaslavska-uhoda
connects_to:
- ruina-i

```

---

## PART 1: Deep Research

Research **Юрій Немирич: Гадяцька угода** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Юрій Немирич: Гадяцька угода

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Юрій Немирич: Гадяцька угода"
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
