# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-043
level: HIST
sequence: 43
slug: dmytro-vyshnevetskyi
version: '2.0'
title: 'Дмитро Вишневецький: Перший кошовий'
subtitle: The Legendary Founder of the First Sich
focus: history
pedagogy: CBI
phase: HIST.5 [Rise of Cossacks]
word_target: 5000
objectives:
- Learner can describe the role of Dmytro Vyshnevetskyi in the founding of the first Sich
- Learner can analyze the geopolitical significance of the Khortytsia fortress
- Learner can understand the legendary status of Baida in Ukrainian folklore
content_outline:
- section: Вступ
  points:
  - 'The transition from princes to cossack leaders — Vyshnevetskyi as the ''last knight'' of the princely era and ''first
    knight'' of the Cossack era; cultural hook: the synthesis of old aristocracy and new steppe tactics'
  - Dmytro Vyshnevetskyi as a figure of the frontier — living on the border of settled Rzeczpospolita and nomadic Wild Fields;
    [!history-bite] he was an elite magnate, debunking the myth that all Cossacks were runaway serfs
  words: 700
- section: 'Шлях князя: Від Волині до Степу'
  points:
  - Origins and noble status — born ~1517 in Vyshnivets, Volhynia, of the Gedyminovych lineage
  - Early military experience — Starosta of Kaniv and Cherkasy (1550-1553), the frontline defense against Tatar raids
  - Diplomatic maneuvers — realizing passive castle defense was insufficient, shifting to active steppe tactics to intercept
    raiders
  words: 700
- section: Заснування Малої Хортиці
  points:
  - Strategic necessity of the 1550s — establishing a base in 1556 on Mala Khortytsia island to control river crossings; [!context]
    why Khortytsia was the ideal 'Dnipro castle'
  - Life in the first fortress — not just a camp, but a fortress with earthworks and wooden log structures
  - Historical legacy — the first precedent of a permanent Cossack garrison beyond the rapids
  words: 700
- section: Читання
  points:
  - Analysis of folk ballads and primary accounts — specifically 'Song of Baida' and Marcin Bielski's chronicle; [!culture]
    connecting Baida's image to the 'kharakternyk' archetype
  words: 700
- section: Геополітика і Дипломатія
  points:
  - Relations with Poland, Lithuania, and Moscow — the 'Moscow episode' (1558-1561) as a pragmatic resource grab for the anti-Crimean
    war; [!myth-buster] Vyshnevetskyi was an ally, not a servant, and left when priorities shifted
  - The anti-Tatar coalition strategy — attempts to unite Poland, Lithuania, Moscow, and potentially Moldova against the Ottoman
    threat
  words: 700
- section: Первинні джерела
  points:
  - Chronicle accounts of Vyshnevetskyi's death — Marcin Bielski's detailed description of his execution in Istanbul (1563)
    by hanging from a rib; [!quote] French ambassador's account confirming the legend
  - Ballad of Baida — symbolism of refusing the Sultan's daughter/faith as an affirmation of Christian knightly honor
  words: 700
- section: Деколонізаційний погляд
  points:
  - Vyshnevetskyi as an independent actor — acting as a sovereign who sent ambassadors and built fortresses; [!decolonization]
    treating him as a geopolitical player, not a vassal
  - The myth of Moscow's protectorate — refuting the Soviet narrative of 'eternal attraction' to Russia; it was a situational
    alliance broken by Vyshnevetskyi
  words: 800
vocabulary_hints:
  required:
  - історія (history) — козацька історія, історія України, сторінки історії
  - держава (state) — будувати державу, інтереси держави, захист держави
  - народ (people) — український народ, пам'ять народу, воля народу
  - влада (power) — князівська влада, військова влада, боротьба за владу
  - період (period) — період Руїни, княжий період, історичний період
  - подія (event) — історична подія, трагічна подія, важлива подія
  - джерело (source) — першоджерело, історичне джерело, надійне джерело
  - спадщина (heritage) — культурна спадщина, козацька спадщина, історична спадщина
  recommended:
  - аналіз (analysis) — критичний аналіз, аналіз джерел, глибокий аналіз
  - контекст (context) — історичний контекст, політичний контекст, культурний контекст
  - вплив (influence) — політичний вплив, культурний вплив, вплив на події
  - наслідки (consequences) — політичні наслідки, історичні наслідки, непередбачувані наслідки
activity_hints:
- type: reading
  focus: 'Ballad of Baida: Analysis of folk imagery'
- type: essay-response
  focus: Vyshnevetskyi as the bridge between Rus princes and Cossack hetmans
- type: comparative-study
  focus: Vyshnevetskyi vs later Cossack leaders
- type: critical-analysis
  focus: Analyzing primary source accounts of his martyrdom
persona:
  voice: Senior Professor of History
  role: Fortress Builder
grammar:
- 'Historical narrative: past perfective'
- Passive voice in historical descriptions
register: публіцистичний
prerequisites:
- zaporizka-sich
connects_to:
- kozatski-povstannia-16

```

---

## PART 1: Deep Research

Research **Дмитро Вишневецький: Перший кошовий** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Дмитро Вишневецький: Перший кошовий

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Дмитро Вишневецький: Перший кошовий"
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
