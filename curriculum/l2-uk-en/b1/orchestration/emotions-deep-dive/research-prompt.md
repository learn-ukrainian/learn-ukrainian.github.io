# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b1-075
level: B1
sequence: 75
slug: emotions-deep-dive
version: '2.0'
title: 'Емоції: глибоке занурення'
subtitle: 'Emotions: Deep Dive'
focus: vocabulary
pedagogy: PPP
phase: B1.6 [Vocabulary Expansion II]
word_target: 4000
objectives:
- Learner can use 30 emotional vocabulary words in context
- Learner can distinguish between synonymous emotion words
- Learner can form natural collocations with emotional vocabulary
- Learner can express nuanced emotional states
content_outline:
- section: Вступ (Introduction)
  words: 400
  points:
  - Introduce the 'Psychotherapist' persona who guides the learner through the inner landscape of emotions; introduce the
    cultural hook of Cordocentrism (heart-centered worldview) based on Skovoroda and Yurkevych.
  - 'Thematic framing: ''Listen to your heart'' (Слухай своє серце) as a gateway to discussing feelings, character traits,
    and relationships as mandated by State Standard §3.'
- section: Лексико-граматичні нюанси (Lexico-Grammatical Nuances)
  words: 1000
  points:
  - Contrast the Dative Experiencer structure (Мені сумно, Тобі радісно) with the Nominative Agent structure (Я сумую, Ти
    радієш); model the shift from simple verb structures to complex state descriptions.
  - 'Integrate State Standard §4.2.2 requirements: Genitive of cause (стрибати з радості, почервоніти від сорому) and Instrumental
    of object (захоплюватися музикою/мистецтвом).'
  - 'Intensity and Nuance: Distinguish between the ''General Sadness'' (сум), the ''Poetic Yearning'' (туга), and the ''Total
    Despair'' (розпач/відчай).'
- section: Тексти та культурний контекст (Texts and Cultural Context)
  words: 1200
  points:
  - Reading analysis of high-frequency emotional states (радість, захоплення, тривога); integrate modern context for 'тривога'
    (air raid sirens/anxiety) vs historical 'бити на сполох'.
  - Introduce 'Зажура' (Zazhura) as a uniquely Ukrainian poetic state of 'sweet sadness' or connection to memory often found
    in folklore, contrasting it with clinical states.
  - Analyze authentic expressions of 'щира радість' and 'праведний гнів' in narrative texts to build stylistic awareness.
- section: Комунікативна практика (Communicative Practice)
  words: 1000
  points:
  - 'Focus on correcting common learner calques: drill the replacement of ''Я відчуваю себе добре'' (Eng/Rus influence) with
    the correct ''Я почуваюся добре'' (reflexive verb + adverb).'
  - 'Register and nuance drill: distinguish between ''хвилюватися'' (common anxiety/nervousness) and ''переживати'' (deep
    suffering or survival contexts like ''пережити війну'').'
  - 'Precision in preference: move learners beyond overusing ''Я люблю'' for everything to using ''Мені подобається'' for
    mild affinity and ''Я в захваті від...'' for strong admiration.'
- section: Рефлексія та висновки (Reflection and Conclusions)
  words: 400
  points:
  - 'Final production task in persona: respond to deep analytical questions such as ''Чому ви це відчуваєте?'' and ''Що приховує
    ваш гнів?'' using new collocations.'
  - 'Summary of emotional intelligence in Ukrainian: recap of collocations (світлий смуток, не приховувати захоплення) and
    the Cordocentric perspective.'
vocabulary_hints:
  required:
  - радість (joy) — щира/непідробна радість, стрибати з радості, сльози радості; High frequency/Corpora
  - смуток (sadness) — глибокий смуток, смуток охопив, розвіяти смуток, світлий смуток; Lit/Formal frequency
  - тривога (anxiety/alarm) — відчувати тривогу, бити на сполох, повітряна тривога, тривога наростає; High frequency in modern
    context
  - захоплення (admiration/excitement) — викликати захоплення, дивитися із захопленням, щире захоплення, не приховувати захоплення;
    High frequency spoken
  - розчарування (disappointment) — гірке розчарування, спіткало розчарування, глибоке розчарування
  - гнів (anger) — праведний гнів, приборкати гнів, спалах гніву, гнів палає
  - страх (fear) — відчувати страх, долати страх, заціпеніти від страху
  - відчувати (to feel) — відчувати підтримку, відчувати страх, відчувати натхнення; very high frequency
  - почуватися (to feel state) — я почуваюся добре/кепсько/бадьоро; crucial reflexive usage
  recommended:
  - туга (yearning/angst) — poetic yearning or existential angst; higher register than 'сум'
  - розпач (despair) — extreme hopelessness; synonym to 'відчай'
  - ностальгія (nostalgia) — related to 'світлий смуток' (light sadness)
  - натхнення (inspiration) — відчувати натхнення, шукати натхнення
  - заздрість (envy) — чорна/біла заздрість; note the idiomatic color usage
  - сором (shame) — почервоніти від сорому, згорати від сорому; Genitive of cause
activity_hints:
- type: match-up
  focus: Match emotions to descriptions
  items: 25
- type: fill-in
  focus: Express emotional states
  items: 20
- type: match-up
  focus: Emotional expressions
  items: 15
- type: fill-in
  focus: Describe emotional experiences
  items: 10
connects_to:
- b1-76 (Стосунки та зв'язки)
prerequisites:
- b1-74 (Здоров'я та самопочуття)
persona:
  voice: Senior Language & Culture Specialist
  role: Psychotherapist
grammar:
- Emotional vocabulary collocations
- Register differences in emotional expression
- Intensity modifiers with emotions
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

Research **Емоції: глибоке занурення** for the **B1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Емоції: глибоке занурення

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
