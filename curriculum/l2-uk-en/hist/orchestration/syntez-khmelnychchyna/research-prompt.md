# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-062
level: HIST
sequence: 62
slug: syntez-khmelnychchyna
version: '2.0'
title: 'Синтез: Козацька революція'
focus: history
pedagogy: CBI
phase: HIST.6 [Khmelnytsky & Cossack State]
word_target: 5000
objectives:
- 'Analyze the causes and consequences of синтез: козацька революція'
- Evaluate the historical significance of вибух, що змінив усе
- Trace the development of деколонізаційний погляд
content_outline:
- section: 'Вступ: Вибух, що змінив усе'
  points:
  - The definition of the Khmelnytsky Uprising as a revolution — change of social order, not just a rebellion; [!context]
    — Хмельниччина відбувалася одночасно з Англійською революцією Кромвеля (1640-1660)
  - 'The scale of changes: social, political, geopolitical — emergence of a new player on the European map; parallels with
    Westphalian Peace (1648)'
  words: 700
- section: 'Причини революції: Чому вибухнуло?'
  points:
  - 'Social oppression (serfdom) — [!quote] — Гійом ле Вассер де Боплан про гноблення селян: «Вони живуть у гіршому рабстві,
    ніж галерники»'
  - Religious discrimination (Uniate Church) — friction from Union of Brest; Ordinance of 1638 liquidating Cossack rights
  - Political lack of rights for Cossacks — attempt to turn Cossacks into peasants; «Золотий спокій» was an illusion
  - Personal tragedy of Khmelnytsky — raid on Subotiv as the spark
  words: 700
- section: 'Етапи боротьби: Від тріумфу до компромісу'
  points:
  - Initial victories (Yellow Waters, Korsun) — spring-autumn 1648; Battle of Pyliavtsi
  - The Treaty of Zboriv (1649) and statehood — recognition of autonomy; Register set at 40,000
  - Defeats (Berestechko) and the Treaty of Bila Tserkva — June 1651; betrayal by Tatars; Register reduced to 20,000; [!history-bite]
    — Битва під Берестечком була однією з найбільших битв Європи XVII ст. (до 300 тис. учасників)
  - The Pereiaslav Council (1654) and the alliance with Moscow — military alliance against three fronts; choice of «lesser
    evil»
  - The death of Khmelnytsky and the start of the Ruin — 1657; struggle for power begins
  words: 700
- section: 'Соціальні трансформації: Народження нації'
  points:
  - 'Liquidation of serfdom — de facto freedom on controlled territories; [!culture] — «Покозачення»: масовий перехід селян
    у козацький стан як спосіб здобути свободу'
  - Formation of the Cossack starshyna as a new elite — merger of former nobility and meritorious Cossacks
  - The role of the Orthodox Church — increased influence and consolidation
  words: 700
- section: 'Читання: Аналіз історичних документів'
  points:
  - Analysis of the Zboriv Treaty — defined three voivodeships (Kyiv, Chernihiv, Bratslav); amnesty and expulsion of Jesuits/Jews
  - Analysis of the March Articles — 11 (or 23) points; rights to foreign policy (except Poland/Turkey); confederative model
    or protectorate
  words: 700
- section: Первинні джерела
  points:
  - 'Eyewitness accounts (Paul of Aleppo, etc.) — [!quote] — Павло Алеппський: «Ми помітили в цьому благословенному народі
    набожність, богобоязливість і благочестя»; notes on high literacy rate'
  - Khmelnytsky's universals — instrument of executive power; calls to uprising and protection decrees
  words: 700
- section: Деколонізаційний погляд
  points:
  - 'Debunking the myth of ''reunification'' — [!myth-buster] — Міф про «возз''єднання»: Переяславська рада була військовим
    союзом, а не злиттям держав; Soviet concept of «вікове прагнення»'
  - Ukraine as a subject of international law — independent diplomatic relations (Turkey, Sweden)
  - The European context of the revolution — betrayal by Moscow in Vilna Truce (1656); pragmatism over «brotherhood»
  - 'Legacy: The birth of the modern Ukrainian state tradition — idea of Cossack statehood persisted until late 18th century'
  words: 800
vocabulary_hints:
  required:
  - історія (history) — [!collocation] творити історію; переписувати історію
  - держава (state) — [!collocation] будувати державу; козацька держава; суверенна держава
  - народ (people) — [!collocation] український народ; воля народу; Paul of Aleppo quote regarding «благословенний народ»
  - влада (power) — [!collocation] гетьманська влада; виконавча влада; боротьба за владу
  - період (period) — [!collocation] період Руїни; перехідний період
  - подія (event) — [!collocation] історична подія; трагічні події
  - джерело (source) — [!collocation] первинне джерело; історичні джерела; згідно з джерелами
  - спадщина (heritage) — [!collocation] козацька спадщина; культурна спадщина
  recommended:
  - аналіз (analysis) — [!collocation] критичний аналіз; аналіз договору
  - контекст (context) — [!collocation] європейський контекст; історичний контекст
  - вплив (influence) — [!collocation] вплив церкви; політичний вплив
  - наслідки (consequences) — [!collocation] далекосяжні наслідки; трагічні наслідки
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
prerequisites: '[]'
persona:
  voice: Senior Professor of History
  role: Military Chronicler
learning_outcomes: '[]'
connects_to:
- ivan-mazepa-derzhavnyk

```

---

## PART 1: Deep Research

Research **Синтез: Козацька революція** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Синтез: Козацька революція

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Синтез: Козацька революція"
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
