# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-053
level: A2
sequence: 53
slug: emotions-personality
version: '2.0'
title: Emotions and Personality
subtitle: Describing People
focus: vocabulary
pedagogy: PPP
phase: A2.5 [Vocabulary Expansion]
word_target: 2000
objectives:
- Learner can describe personality traits
- Learner can describe emotional states
- Learner can characterize people
- Learner can express feelings
content_outline:
- section: 'Вступ: Кордоцентризм та світ емоцій (Introduction: Cordocentrism and the World of Emotions)'
  words: 325
  points:
  - 'Introduce the ''Philosophy of the Heart'' (Cordocentrism) as a cultural foundation: explaining how Ukrainians feel emotions
    ''на душі'' (on the soul) rather than just thinking them.'
  - 'Visual mapping of core emotions using emojis to introduce high-frequency adjectives: радість (joy), сум (sadness), злість
    (anger), and their corresponding state adverbs (весело, сумно, зло).'
  - 'Cultural inquiry: Teaching the phrase ''Що у тебе на душі?'' as a deep alternative to ''Як справи?'', emphasizing the
    value of ''щирість'' (sincerity) in personal interaction.'
- section: 'Граматика: Стани та якості за стандартами (Grammar: States and Qualities per Standards)'
  words: 575
  points:
  - '§4.2.2.3 Dative for emotional states: Explicit contrast between permanent quality (Я веселий — I am a cheerful person)
    and fleeting state (Мені весело — I am having fun right now).'
  - 'Addressing common learner error: The tendency to use Nominative for states (e.g., ''Я нудний'' instead of the correct
    ''Мені нудно''). Provide 5 minimal pairs for correction.'
  - '§3.1 Gender agreement in character traits: Drilling the shift from masculine to feminine (Він добрий vs. Вона добра)
    to prevent the error of using masculine defaults for female subjects.'
  - 'The ''False Friend'' alert: Clarifying that ''симпатичний'' refers to being good-looking or pleasant, not ''sympathetic''
    in the English sense of being compassionate.'
- section: Лексика та Портрет особистості (Vocabulary and Personality Portrait)
  words: 475
  points:
  - 'Analysis of high-frequency adjectives with research-backed collocations: ''добре серце'' (kind heart), ''злі язики''
    (gossips), and ''розумний вибір'' (smart choice).'
  - 'National character traits: Defining ''гостинність'' (hospitality) and ''щирість'' (sincerity) as key positive values,
    contrasted with being a ''замкнена людина'' (closed/unsociable person).'
  - 'Proverb analysis: ''Не по одежині судять, а по розуму'' (Judge not by clothes, but by mind) — reading task focusing on
    the cultural priority of wisdom and intellect.'
- section: 'Практика: Опис характеру та стану (Practice: Describing Character and State)'
  words: 400
  points:
  - 'Guided dialogues: Role-playing a ''Drama Teacher'' persona where students must express their feelings using Dative +
    Adverb constructions in response to ''Що на душі?''.'
  - 'Professional context bridge: Identifying traits like ''працьовитий'' (hardworking) and ''терплячий'' (patient) as preparation
    for workplace vocabulary in module A2-49.'
  - 'Personality Matching: Exercises mapping character descriptions to specific behaviors (e.g., ''Він завжди ділиться'' ->
    ''Він щедрий'').'
- section: 'Підсумок: Від серця до розуму (Summary: From Heart to Mind)'
  words: 225
  points:
  - 'Consolidation of syntactic logic: Reinforcing the distinction between ''Who I am'' (Adjective) and ''How I feel'' (Dative
    + Adverb).'
  - Final review of the frequency-based vocabulary table, ensuring mastery of soft-stem agreement and the 'симпатичний' false
    friend distinction.
vocabulary_hints:
  required:
  - добрий (kind) — добра людина, добре серце (kind heart), добра воля (goodwill); High frequency (Top 500)
  - злий (angry/evil) — злий собака, злий жарт (cruel joke), злі язики (gossips/evil tongues), на зло (out of spite)
  - щасливий (happy) — щаслива дорога (bon voyage), щасливий випадок (lucky chance), щасливе дитинство
  - сумний (sad) — сумна пісня, сумний погляд (sad look), сумна звістка (sad news)
  - розумний (smart) — розумна голова (smart person), розумна дитина, розумний вибір
  - веселий (cheerful) — веселі свята, весела вдача (cheerful nature), весела компанія (fun company)
  - спокійний (calm) — спокійне життя, спокійний голос, спокійної ночі (good night)
  - нервовий (nervous) — нервова система, нервовий тік, нервова робота (stressful job)
  recommended:
  - щирий (sincere) — щира розмова, щира правда; Key cultural value
  - гостинний (hospitable) — гостинний господар; National trait
  - замкнений (closed/unsociable) — замкнена людина; Opposite of 'щирий'
  - 'симпатичний (nice/good-looking) — симпатичне обличчя; Note: Not ''sympathetic'''
  - щедрий (generous) — щедра душа
  - скупий (stingy) — скупий на слова (sparing with words)
  - чесний (honest)
  - лінивий (lazy)
  - працьовитий (hardworking)
  - терплячий (patient)
activity_hints:
- type: match-up
  focus: Emotions and personality
  items: 30
- type: match-up
  focus: Match traits to descriptions
  items: 20
- type: fill-in
  focus: Complete character descriptions
  items: 15
- type: quiz
  focus: Describe people you know
  items: 8
connects_to:
- a2-54 (Work and Professions)
prerequisites:
- a1-26 (Describing Things - Adjectives)
- a2-52 (Nature and Weather)
persona:
  voice: Encouraging Cultural Guide
  role: Drama Teacher
grammar:
- Adjectives of personality (добрий, злий)
- Describing feelings (мені сумно)
- Dative for emotional states
register: розмовний
immersion: 60-75% Ukrainian

```

**Level constraints quick-ref:**

```
# A2 Quick Reference

> This file supplements the build prompt. Do NOT repeat targets already injected
> via `2000`, `TARGET: 70-90% Ukrainian.
LANGUAGE ROLES:
- PRIMARY: Ukrainian for everything.
- ENGLISH: Only in vocabulary tables and one-line grammar notes where absolutely necessary.
- STRUCTURAL RULE: Each sentence is 100% Ukrainian OR 100% English.
A2 register. Concrete everyday vocabulary. No literary language, no metaphors. Near-full Ukrainian immersion. Ukrainian sentences max 15 words. Max 2 clauses. All cases allowed. Simple subordinate clauses only. Full aspect pairs. No participles.`, ``, etc.

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

Research **Emotions and Personality** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Emotions and Personality

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
