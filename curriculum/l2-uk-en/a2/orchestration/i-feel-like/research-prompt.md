# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-035
level: A2
sequence: 35
slug: i-feel-like
version: '2.0'
title: I Feel Like...
subtitle: Physical and Emotional States
focus: vocabulary
pedagogy: PPP
phase: A2.2
word_target: 2000
objectives:
- Learner can describe physical states (hot, cold, painful)
- Learner can describe emotional states (sad, happy, bored)
- Learner can ask others about their feelings
- Learner can distinguish between personal traits and temporary states
sources:
- name: Ukrainian State Standard 2024 - States and Emotions
  url: https://mon.gov.ua/
  type: reference
  notes: Standards for expressing subjective physical and mental states at A2
- name: Psychology of Language - Slavic Subjective Dative
  url: https://uk.wikipedia.org/wiki/Безособові_речення
  type: reference
  notes: Syntax of impersonal sentences for expressing feelings
content_outline:
- section: Вступ (Introduction)
  words: 325
  points:
  - 'The difference between ''Who I am'' and ''How I feel'' — explicit contrast table: ''Я холодний'' (I am a cold person)
    vs ''Мені холодно'' (I feel cold); focus on fixing the Nominative subject error.'
  - 'Grammatical foundation: The Dative logic according to State Standard §4.2.2.3 for subjective states and impersonal constructions
    (Мені не спиться, Нам весело).'
- section: Презентація (Presentation)
  words: 625
  points:
  - 'Physical States: жарко, холодно, боляче — frequent adverbs; distinguish between personal traits and temporary states;
    warning on the sexual connotation of ''Я гарячий''.'
  - 'Emotional States: сумно, весело, нудно — high frequency list; collocations like ''мені стало сумно'' to show transition
    of state.'
  - 'Psychological Reflexives: Я хвилююся, я боюся, я тішуся — contrast structure: ''я боюся'' (Nominative subject) vs ''мені
    страшно'' (Dative state experiencer).'
  - 'Semantic distinction: Радий (Situational gladness, gendered: радий/рада) vs Щасливий (Deep/permanent feeling) vs Мені
    весело (Adverbial state).'
- section: Культурний контекст (Cultural Context)
  words: 325
  points:
  - Meteosensitivity (Метеозалежність) — explaining how complaints about 'magnetic storms' (магнітні бурі) serve as a social
    bonding mechanism in Ukraine.
  - 'Folk wisdom: Analysis of the proverb ''Ломить руки, або коліна – буде погоди переміна'' to illustrate the cultural connection
    between physical sensation and nature.'
- section: Практика та вправи (Practice and Exercises)
  words: 400
  points:
  - 'Dative conversion drills: mapping Nominative to Dative (я→мені, ти→тобі, він→йому, вона→їй); correcting the common error
    ''Вона сумно'' to ''Їй сумно''.'
  - 'Adjective vs Adverb contrast: Drills to prevent ''Мені холодний'' (Adj) by contrasting it with correct ''Мені холодно''
    (Adv) for feeling/state.'
- section: Діалоги та підсумок (Dialogues and Summary)
  words: 325
  points:
  - 'Dialogue scenarios: comforting a friend who feels unwell or complaining about the weather; using ''мені...'' to express
    spontaneous physical needs or feelings.'
  - 'Final summary: Recap of the Dative experiencer pattern and the list of core adverbs for physical and emotional states.'
vocabulary_hints:
  required:
  - 'мені (to me) — Dative case marker for subjective states; Very High Frequency (Rank #51); anchor for the experiencer construction'
  - 'холодно (cold/coldly) — High Frequency; ''мені холодно'' (I feel cold), ''надворі холодно'' (outside); antonym: жарко'
  - 'жарко (hot/hotly) — High Frequency; ''мені жарко'' (I feel hot); learner warning: avoid ''я гарячий'' for bodily temperature'
  - 'сумно (sad/sadly) — High Frequency; ''мені сумно'' (I feel sad); collocation: ''стало сумно'' (became sad)'
  - весело (fun/merrily) — High Frequency; 'нам весело' (we are having fun), 'проводити час весело' (enjoyable time)
  - боляче (painfully/hurts) — Medium Frequency; 'мені боляче' (it hurts me), 'робити боляче' (to inflict pain)
  recommended:
  - радий (glad) — Short adjective, agrees with gender (я радий/рада); situational usage
  - щасливий (happy) — Long adjective describing a permanent trait or profound state
  - нудно (boring/bored) — 'мені нудно' (I am bored); distinct from 'нудний' (boring person/thing)
  - метеозалежність (meteosensitivity) — Cultural term for physical reactions to weather changes
  - магнітні бурі (magnetic storms) — Specific cultural hook for explaining fatigue or headaches
persona:
  voice: Encouraging Cultural Guide
  role: Melancholy Poet
module_type: vocabulary
immersion: 60-75% Ukrainian
prerequisites:
- i-think-that
connects_to:
- in-order-to
grammar:
- Вступ
- Презентація
- Культурний контекст
register: розмовний
activity_hints:
- type: match-up
  focus: Match words to definitions
  items: 12
- type: fill-in
  focus: Complete sentences with vocabulary
  items: 8
- type: group-sort
  focus: Sort by category
  items: 10
- type: quiz
  focus: Choose correct word for context
  items: 10
- type: fill-in
  focus: Use words in sentences
  items: 6
- type: essay-response
  focus: Write using domain vocabulary

```

**Level constraints quick-ref:**

```
# A2 Quick Reference

> This file supplements the build prompt. Do NOT repeat targets already injected
> via `2000`, `TARGET: 55-75% Ukrainian.
LANGUAGE ROLES:
- PRIMARY: Ukrainian for all content — dialogues, examples, section intros, cultural context.
- ENGLISH: Only for abstract grammar concepts that need explicit explanation.
- STRUCTURAL RULE: Each sentence is 100% Ukrainian OR 100% English. Dialogues, examples, section intros all stay Ukrainian-only.
A2 register. Concrete everyday vocabulary. No literary language, no metaphors. Ukrainian sentences max 15 words. Max 2 clauses. All cases allowed. Simple subordinate clauses only. Aspect pairs introduced. No participles.`, ``, etc.

## Grammar Scope

**Allowed:** All 7 cases. Simple subordinate clauses (який/що/коли). Aspect pairs introduced.
Max 15 words per Ukrainian sentence. Max 2 clauses per sentence.

**Forbidden:** Participles. Complex subordinate clauses.

## Immersion Strategy (A2)

A2 uses graduated immersion (50-90%) across three bands:

| Band | Modules | Target | English used for |
|------|---------|--------|-----------------|
| Core grammar | M01-20 | 45-65% | Grammar theory (cases, aspect) |
| Applied grammar | M21-50 | 55-75% | Abstract concepts only |
| Consolidation | M51-70 | 70-90% | Vocabulary tables only |

**Critical rule:** NEVER mix languages within a sentence at A2.
Each sentence is 100% Ukrainian OR 100% English.
Ukrainian paragraph first, then English translation paragraph below if needed.

## A2-Specific Writing Notes

- No Latin transliteration — stress marks (´) only
- No IPA or phonetic brackets
- Register: A2 only. Concrete everyday vocabulary (їсти, ходити, купувати)
- No literary/poetic language, no abstract nouns (почуття, відчуття, стан, сутність)
- No metaphors or figurative speech
- Grammar terms in Ukrainian introduced where relevant (відмінок, називний, etc.)

```

Read the State Standard compliance mapping (small file — read this FIRST):

```
docs/l2-uk-en/state-standard-2024-mapping.yaml
```

The full State Standard 2024 is at `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt` (431KB, ~6000 lines). **Do NOT read the entire file.** Instead:
1. Check the mapping file for the relevant `A2` section — find the grammar topic that matches your module
2. Use the `lines: [start, end]` coordinates to read ONLY that section from the full Standard
3. If no mapping entry exists for this topic, search by §number or keyword as fallback
4. If still no match, say so honestly — do NOT fabricate a §reference

---

## PART 1: Lightweight Research

Research **I Feel Like...** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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
- **Word count**: minimum **2000** words — allocate outline sections accordingly
- **Colonial framing**: plan decolonized framing NOW so Phase B doesn't default to Russian comparisons
- **Russianisms**: ensure vocabulary_hints and examples avoid banned words (кушати→їсти, получати→отримувати)
- **Duplicate headers**: ensure outline section names don't share keywords

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

### Output Block 1: Research Notes

```
===RESEARCH_START===

# Дослідження: I Feel Like...

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
