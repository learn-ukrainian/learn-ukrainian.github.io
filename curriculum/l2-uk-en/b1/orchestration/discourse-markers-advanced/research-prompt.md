# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b1-068
level: B1
sequence: 68
slug: discourse-markers-advanced
version: '2.0'
title: 'Дискурсивні маркери II: складна організація'
subtitle: 'Discourse Markers II: Advanced Text Organization'
focus: vocabulary
pedagogy: PPP
phase: B1.5 [Vocabulary Expansion I]
word_target: 4000
objectives:
- Learner can use 25 advanced discourse markers to organize complex arguments
- Learner can sequence ideas using ordinal markers
- Learner can express addition, contrast, and conclusion in academic writing
- Learner can structure extended discourse effectively
content_outline:
- section: Вступ (Introduction)
  words: 500
  points:
  - Align text organization strategies with State Standard §4.4.2/§4.5.1 regarding advanced 'вставні слова' (inserted words)
    and the transition from simple B1 connectors to complex argument structures.
  - 'Cultural hook: The Kyiv-Mohyla Academy rhetoric tradition (17th-18th c.), where masters like Hryhorii Skovoroda and Theophan
    Prokopovych taught transitional logic and clear speech as essential signs of intellectual wisdom.'
- section: Презентація лексики (Vocabulary Presentation)
  words: 1000
  points:
  - 'Categorize 25+ markers into six functional clusters: Sequencing (по-перше), Addition (крім того, передусім), Contrast
    (проте, з одного боку... з іншого боку), Clarification (загалом), Result (таким чином), and Conclusion (отже, нарешті).'
  - 'Focus on frequency-informed collocations and paired usage: Drill ''по-перше, хочу зазначити'' and ''підсумовуючи результати'',
    while emphasizing the mandatory pair ''з одного боку... з іншого боку'' to avoid broken logic.'
  - 'Visualize decision logic using a flowchart approach: Training students to select markers based on intent (Adding? → крім
    того; Contrasting? → проте; Concluding? → отже).'
- section: Граматика та вживання (Grammar and Usage)
  words: 1000
  points:
  - 'Register differentiation: Clearly separate formal/academic markers (отже, таким чином, підсумовуючи) from conversational
    discourse markers (ну, знаєш, до речі, словом).'
  - 'Learner error clinic: Addressing punctuation omission with comma-placement drills after markers (e.g., ''По-перше, я
    не знав'') and correcting the semantic confusion between temporal ''нарешті'' and spatial ''накінець''.'
  - 'De-Russification focus: Identifying and replacing common calques like ''во-пєрвих'' with ''по-перше'' and surzhyk ''короче''
    with professional alternatives like ''словом'' or ''підсумовуючи''.'
- section: Аналіз та читання (Analysis and Reading)
  words: 1000
  points:
  - 'Reading: ''How to Win a Debate'' — an analytical article framed around conference presentations and parliamentary debate
    traditions (viche), using authority markers like ''шановне товариство'' and ''дозвольте зауважити''.'
  - 'Modeling persuasive structure: Analyzing how to move from simple sentences to organized, authoritative discourse using
    the ''Keynote Speaker'' persona.'
- section: Практика та підсумок (Practice and Summary)
  words: 500
  points:
  - 'Production Task: Delivering a structured argument in the ''Keynote Speaker'' voice, modeling authority and logical flow
    through a recap of the 25 target markers.'
  - 'Self-correction workshop: Identifying register mismatches and broken pairs in peer arguments, bridging directly to the
    descriptive organization required for b1-58 (Describing Changes).'
vocabulary_hints:
  required:
  - по-перше (firstly) — по-перше, хочу зазначити; High frequency academic starter
  - по-друге (secondly) — по-друге, варто наголосити; Sequencing marker
  - нарешті (finally) — нарешті ми дійшли згоди; і, нарешті, останній пункт; High frequency; temporal focus
  - підсумовуючи (summarizing) — підсумовуючи вищесказане; підсумовуючи результати; Academic/Formal register
  - таким чином (thus) — таким чином, ми бачимо; діяти таким чином; High frequency formal result marker
  - особливо (especially) — used for emphasizing key points within complex arguments
  - передусім (above all) — передусім потрібно; це стосується передусім; Medium frequency emphasis marker
  - загалом (in general) — загалом кажучи; загалом це вірно; High frequency clarification/generalization
  recommended:
  - насамкінець (in conclusion) — formal academic closing marker
  - головне (the main thing) — signals priority within a hierarchical argument
  - з одного боку (on one hand) — paired with з іншого боку; mandatory logical pair
  - з іншого боку (on the other hand) — paired with з одного боку; contrast marker
  - проте (however) — contrastive discourse marker; formal register
  - отже (so/therefore) — concluding marker for logical derivation
  - крім того (besides/furthermore) — additive marker for expanding complex texts
  - словом (in a word) — conversational/semi-formal summary marker to replace 'короче'
activity_hints:
- type: true-false
  focus: Structure arguments with markers
  items: 20
- type: fill-in
  focus: Complete academic texts
  items: 20
- type: fill-in
  focus: Write structured essays
  items: 15
- type: fill-in
  focus: Improve text organization
  items: 15
connects_to:
- b1-69 (Опис змін)
prerequisites:
- 'b1-67 (Дискурсивні маркери: базові конектори)'
persona:
  voice: Senior Language & Culture Specialist
  role: Keynote Speaker
grammar:
- Advanced discourse markers for text organization
- Academic and formal connectors
- Structuring arguments and conclusions
register: розмовний

```

**Level constraints quick-ref:**

```
# B1 Quick Reference

> This file supplements the build prompt. Do NOT repeat targets already injected
> via `4000`, `Full Ukrainian immersion. Grammar explained IN Ukrainian. English only for disambiguation of false friends. Sentences max 30 words.`, etc.

## Grammar Scope

**Allowed:** All grammar constructions. Participles. Complex subordinate clauses.
Max 30 words per Ukrainian sentence. Max 4 clauses.

## Immersion Strategy (B1)

| Phase | Modules | Immersion | Notes |
|-------|---------|-----------|-------|
| B1.0 (Bridge) | M01-05 | Mixed | Teach grammar metalanguage; English scaffolding for abstract concepts |
| B1.1+ (Core) | M06-92 | **100%** | Full Ukrainian. English ONLY in vocabulary table translations |

**B1.0 Bridge modules:** English grammar term explanations allowed as transition from A2.

**B1.1+ Hard rule:** No English in prose, titles, callouts, or explanations.
No English in parentheses to clarify Ukrainian concepts:
- Wrong: **поки** — дія на тлі іншої дії (While she was cooking...)
- Right: **поки** — дія на тлі іншої дії, тобто одночасні процеси

## B1-Specific Writing Notes

- Content quality: equal treatment for all items in a category (same depth, same format)
- Example variety: mix standalone, table, inline, dialogue — no 5+ consecutive examples in same format
- Tables must have narrative context (2+ sentences before and after)
- Parallel sections use identical internal structure

```

Read the State Standard compliance mapping (small file — read this FIRST):

```
docs/l2-uk-en/state-standard-2024-mapping.yaml
```

The full State Standard 2024 is at `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt` (431KB, ~6000 lines). **Do NOT read the entire file.** Instead:
1. Check the mapping file for the relevant `B1` section — find the grammar topic that matches your module
2. Use the `lines: [start, end]` coordinates to read ONLY that section from the full Standard
3. If no mapping entry exists for this topic, search by §number or keyword as fallback
4. If still no match, say so honestly — do NOT fabricate a §reference

---

## PART 1: Lightweight Research

Research **Дискурсивні маркери II: складна організація** for the **B1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

### Your RAG Tools

| Tool | When to use |
|------|-------------|
| `search_text` | Find how this topic is taught in Ukrainian textbooks |
| `verify_words` | Check vocabulary exists in VESUM dictionary |
| `query_grac` mode=`frequency` | Get word frequency data |
| `query_wikipedia` mode=`summary` | Quick fact-check for cultural hooks |

### Research Requirements

1. **State Standard Reference**: Look up the §section in `state-standard-2024-mapping.yaml`, then read ONLY that section from `UKRAINIAN-STATE-STANDARD-2024.txt`. Quote the relevant requirement.
2. **Vocabulary Frequency**: Use `query_grac` (mode=`frequency`) for key vocabulary items. Do NOT rely on memory alone.
3. **Cultural Hook**: Use `query_wikipedia` to find 1-2 verified cultural facts to anchor the lesson.
4. **Cross-References**: Note which modules this builds on and prepares for (check the plan's `connects_to` field).
5. **Common Errors**: Identify 2-3 common learner mistakes for this grammar point/topic.

### Decolonized Framing

When researching, frame Ukrainian independently — **never as a derivative or variant of Russian:**
- Describe Ukrainian features positively ("Ukrainian has...", "Ukrainian uses...")
- Do NOT use Russian as the baseline for comparisons ("Unlike Russian...", "Different from Russian...")
- If comparing language systems is useful, use non-Russian languages (Polish, Portuguese, etc.)
- Note how topics have been historically misframed by Russian/Soviet sources and provide the Ukrainian-centric perspective

### Research Output Cap
Keep research notes under **1500 words**. Focus on density: facts, dates, quotes, tables — not prose.

### Additional for Core B (B1.6+, B2, C1, C2, PRO)

- Domain-specific vocabulary collocations from professional glossaries (PRO tracks)
- Stylistic/dialectal features from academic sources (C2)
- Register distinctions (formal vs. informal usage)

## Downstream Audit Gates (Phase B content will be checked for)

Plan your outline knowing that Phase B content must pass these gates:
- **Word count**: minimum **4000** words — allocate outline sections accordingly
- **Colonial framing**: plan decolonized framing NOW so Phase B doesn't default to Russian comparisons
- **Russianisms**: ensure vocabulary_hints and examples avoid banned words (кушати→їсти, получати→отримувати)
- **Duplicate headers**: ensure outline section names don't share keywords

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

### Output Block 1: Research Notes

```
===RESEARCH_START===

# Дослідження: Дискурсивні маркери II: складна організація

## State Standard Reference
§{section_number}: "{quoted requirement}"
Alignment: {how this module addresses the standard}

## Vocabulary Frequency
| Word | Frequency / Source | Key collocations |
|------|-------------------|------------------|
| ...  | ...               | ...              |

## Cultural Hooks
1. {Verified fact with source}
2. {Verified fact with source}

## Common Learner Errors
1. {Error pattern} → {Correct form} — {Why it happens}
2. ...

## Cross-References
- Builds on: {module slugs}
- Prepares for: {module slugs}

## Multimedia Resources
(If you naturally encountered relevant Ukrainian-language YouTube videos or audio resources during your web research, note them here. Do NOT search specifically for videos — the discover phase handles that. Maximum 3 entries.)
- {Channel — Title — URL — 1-sentence relevance note}
- (none encountered)

## Notes for Content Writing
- {Any additional observations for Phase B}

===RESEARCH_END===
```

## Friction Report (MANDATORY)

After both output blocks, include:

```
===FRICTION_START===
**Phase**: Phase A: Meta + Research (Core)
**Step**: {what you were doing when friction occurred, or "Full Phase A"}
**Friction Type**: NONE | TOKEN_LIMIT_TRUNCATION | TOOL_REDUNDANCY | STATE_STANDARD_NOT_FOUND | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===
```

---

## Boundaries

- Do NOT write lesson content — only research notes
- Do NOT generate activities or vocabulary
- Do NOT fabricate State Standard references — if you can't find the exact §, say so
- Do NOT reference persona names or voice instructions — persona is assigned at content generation time
- Do NOT request skills, delegate to Claude, or skip this phase
