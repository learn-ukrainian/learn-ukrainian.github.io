# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b1-069
level: B1
sequence: 69
slug: describing-changes
version: '2.0'
title: Опис змін
subtitle: Describing Changes
focus: vocabulary
pedagogy: PPP
phase: B1.5 [Vocabulary Expansion I]
word_target: 4000
objectives:
- Learner can use 25 verbs and expressions for describing changes
- Learner can distinguish between gradual and sudden change vocabulary
- Learner can form natural collocations with change-related adverbs
- Learner can narrate transformations over time
content_outline:
- section: 'Вступ: Мова динаміки (Introduction: The Language of Dynamics)'
  words: 400
  points:
  - 'Introduction to the Climate Scientist persona: setting a professional tone for describing environmental and social shifts
    according to State Standard §3.14.'
  - Distinguishing between dynamic processes (*процес*) and static results (*результат*) in Ukrainian descriptive grammar.
  - 'Temporal perspectives: defining the scale of change from gradual (*поступово*) to sudden (*різко*) or rapid (*стрімко*).'
- section: Презентація та граматичні нюанси (Presentation and Grammatical Nuances)
  words: 1000
  points:
  - 'Lexical groups for change: Motion, State, Quantity, Quality, and Abstract concepts as mandated by Standard §3.6.'
  - 'Comparison of adverbs: using *більш сучасно* or *менш холодно* to describe shifting states (State Standard §4.3.2).'
  - 'Learner Error Focus 1: Distinguishing *рости* (physical growth of plants/children) from *зростати* (abstract/statistical
    growth like *економіка зростає*).'
  - 'Learner Error Focus 2: Transitive *змінювати* (active agent) vs reflexive *змінюватися* (intransitive state); drill correct
    Accusative governance *змінювати план* vs incorrect *змінювати до плану*.'
  - 'Collocations with speed adverbs: *стрімко зростати*, *поступово змінюватися*, *різко падати*.'
- section: 'Читання: Клімат та трансформація міст (Reading: Climate and City Transformation)'
  words: 1000
  points:
  - 'Climate Scientist Report: analytical text on environmental trends using *температура підвищується/знижується* and *клімат
    змінюється*.'
  - 'Cultural Hook: The transformation of Kyiv into a ''UNESCO City of Music'' (2025) as a context for verbs of improvement
    (*покращуватися*, *розвиватися*).'
  - 'Social Context: De-russification and street renaming as an active process of *змінювати назви*, contrasting with how
    the urban landscape *змінюється* (passive/state).'
- section: 'Діалоги: Від прогнозів до цифровізації (Dialogues: From Forecasts to Digitalization)'
  words: 800
  points:
  - 'Formal workplace dialogue: negotiating project changes and adjustments using transitive verbs and Accusative case.'
  - 'Informal weather discussion: practicing the distinction between *погода змінюється* (intransitive) and *вітер змінює
    напрямок* (transitive).'
  - 'Digital State Discussion: Cultural hook on how the ''Diia'' ecosystem *стрімко розвивається*, transforming bureaucratic
    processes into digital services.'
- section: Виробництво та підсумок (Production and Summary)
  words: 800
  points:
  - 'Guided production: learners describe a significant change in their hometown or professional field using at least 10 verbs/adverbs
    from the required list.'
  - 'Refining nuances: choosing between *поступово*, *різко*, and *стрімко* to accurately convey the speed of transformation.'
  - Final recap of case governance (*перетворюватися на...*) and the contrast between physical and abstract growth verbs.
vocabulary_hints:
  required:
  - зростати (to grow/increase) — *попит/економіка/ціни/напруга зростають*; high frequency in news/econ; contrast with physical
    *рости*
  - зменшуватися (to decrease) — *кількість/відстань/ризик зменшується*; common for gradual reduction
  - змінюватися (to change [itself]) — *погода/ситуація/часи змінюються*; intransitive/reflexive; contrast with transitive
    *змінювати*
  - 'змінювати (to change [something]) — *змінювати план/назву/пароль*; transitive, requires Accusative; error: do not use
    ''до'''
  - перетворюватися на (to transform into) — *місто перетворюється на культурний хаб*; requires Accusative governance
  - підвищуватися (to rise/increase) — *температура/рівень/тиск підвищується*; specific to measurements and scales
  - знижуватися (to lower/decline) — *температура/ціни/рівень знижується*; antonym to *підвищуватися*
  - поступово (gradually) — *поступово змінюватися/звикати/відновлюватися*; high frequency for steady processes
  - різко (sharply/suddenly) — *різко змінитися/впасти/піднятися*; indicates a sudden break in trend
  recommended:
  - стрімко (rapidly) — *стрімко розвиватися/зростати/падати*; used for digitalization (Diia) and fast economic shifts
  - значно (significantly) — *значно впливати/змінити/покращити*; adds emphasis to the scale of change
  - падати (to fall) — *курс валют/ціни/температура падає*; common for rapid or negative trends
  - ставати (to become) — *ставати кращим/гіршим/доступнішим*; used with comparative adjectives/adverbs
  - покращуватися (to improve) — *ситуація/здоров'я/якість покращується*; reflexive form for positive change
  - погіршуватися (to worsen) — *зір/погода/відносини погіршуються*; reflexive form for negative change
activity_hints:
- type: match-up
  focus: Verb + adverb combinations
  items: 25
- type: fill-in
  focus: Describe changes in context
  items: 20
- type: fill-in
  focus: Rephrase change descriptions
  items: 15
- type: fill-in
  focus: Narrate trends
  items: 10
connects_to:
- b1-70 (Медіа та новини)
prerequisites:
- 'b1-68 (Дискурсивні маркери II: складна організація)'
persona:
  voice: Senior Language & Culture Specialist
  role: Climate Scientist
grammar:
- Verb collocations for describing change
- Adverbs of manner with change verbs
- Temporal expressions for change processes
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

Research **Опис змін** for the **B1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Опис змін

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
