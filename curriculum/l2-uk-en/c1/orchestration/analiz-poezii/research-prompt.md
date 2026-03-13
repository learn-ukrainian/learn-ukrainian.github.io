# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: c1-065
level: C1
sequence: 65
slug: analiz-poezii
version: '2.0'
title: Аналіз поезії
subtitle: Analysis of Poetry
content_outline:
- section: 'Вступ: Основи української версифікації (Introduction: Foundations of Ukrainian Versification)'
  words: 600
  points:
  - 'Introduction to §1.1.2.1.1: Analyzing detailed poetic texts as a specific genre, distinguishing between ''вірш'' (poem/work)
    and ''строфа'' (stanza) to fix the common learner error of confusing verse with poem.'
  - Overview of 'силабо-тонічна версифікація' (syllabo-tonic versification) and the fundamental difference between fixed meter
    and natural rhythm in the Ukrainian language.
  - 'Linguistic note on stress patterns in Ukrainian poetry: why reading poetry requires feeling the ''ритмічна схема'' (ta-TA-ta-TA)
    rather than treating it as tonic verse.'
- section: 'Архітектура вірша: Стопа та метр (Poem Architecture: Foot and Meter)'
  words: 1000
  points:
  - 'Defining the ''віршова стопа'' (poetic foot) and the binary meters: ямб (iamb) and хорей (trochee).'
  - 'Mnemonic drill for rising and falling rhythms: Ямб — ''Я йду'' (rising, ta-DA) vs. Хорей — ''Холод'' (falling, DA-ta)
    to address the ''rising/falling'' confusion found in research.'
  - 'Analysis of binary meters in classical texts: Shevchenko''s use of meter vs. Franko''s rhythmic variations, including
    ternary meters (дактиль, амфібрахій, анапест).'
  - Drill on identifying 'чотиристопний ямб' vs. 'п’ятистопний ямб' in canonical Ukrainian lyrics.
- section: 'Строфіка та римування: Від катрена до сонета (Strophic Structure and Rhyming: From Quatrain to Sonnet)'
  words: 800
  points:
  - 'Types of rhyming patterns: парна (AABB), перехресна (ABAB), and кільцева (ABBA), with a focus on ''багата рима'' (rich
    rhyme).'
  - Distinguishing between 'чоловіча рима' (masculine) and 'жіноча рима' (feminine) based on stress position at the line end.
  - 'Cultural Hook: Mykola Zerov and the ''Неокласики'' (Neoclassicists) — the sonnet as an ideal of classical form and Zerov''s
    mastery of the ''сонетна форма''.'
  - Lina Kostenko's use of complex strophic structures to convey historical and philosophical depths, demonstrating high-level
    stylistic variation.
- section: Звукопис та художня майстерність (Soundscapes and Artistic Mastery)
  words: 800
  points:
  - 'Integration of State Standard §4.4.3: Analyzing stylistic devices such as алітерація (alliteration), асонанс (assonance),
    and звуконаслідування (onomatopoeia).'
  - 'Contrastive analysis of soundscapes: comparing the traditional melodicism of Lesia Ukrainka with the modernist experimentation
    of Mykhail Semenko (Futurism) and Bohdan-Ihor Antonych.'
  - The role of 'верлібр' (free verse) in modern Ukrainian poetry as a departure from traditional syllabo-tonic constraints
    while maintaining phonetic richness.
- section: 'Практикум: Філологічний аналіз тексту (Workshop: Philological Analysis of Text)'
  words: 800
  points:
  - 'Step-by-step methodology for a comprehensive philological analysis: from identifying meter and rhyme to decoding metaphors
    and epithets (§4.4.2).'
  - 'Analysis of a selected poem by Lesia Ukrainka: identifying strophic structure, meter, and the ''звукова алітерація''
    that creates its unique mood.'
  - 'Production task: Written analysis of a contemporary poem (e.g., Lina Kostenko) applying correct terminology and avoiding
    the ''verse/poem'' terminological trap.'
focus: literature
pedagogy: Literary Analysis
objectives:
- Learner can identify poetic meters (ямб, хорей, дактиль).
- Learner can analyze rhyme schemes and strophic structures.
- Learner can conduct a comprehensive philological analysis of a poem.
grammar:
- Poetic syntax and rhythm
- Stylistic devices in verse
phase: C1.5 [Stylistics & Rhetoric]
persona:
  voice: Senior Specialist
  role: Літературний критик
word_target: 4000
vocabulary_hints:
  required:
  - 'версифікація (versification) — Academic register; collocations: ''силабо-тонічна версифікація'', ''системи версифікації''.'
  - 'рима (rhyme) — Medium frequency; collocations: ''парна/перехресна/кільцева рима'', ''чоловіча/жіноча рима'', ''багата
    рима''.'
  - стопа (poetic foot) — Specific literary term; 'віршова стопа', 'двоскладова стопа', 'трискладова стопа'.
  - ямб (iamb) — Rising rhythm (ta-DA); 'чотиристопний ямб', 'п’ятистопний ямб'.
  - хорей (trochee) — Falling rhythm (DA-ta); 'народний хорей', 'ритм хорея'.
  - алітерація (alliteration) — 'звукова алітерація', 'прийом алітерації'; repetition of consonants for stylistic effect.
  - строфа (stanza) — Critical term; distinguish from 'вірш' (the poem as a whole).
  recommended:
  - асонанс (assonance) — Repetition of vowel sounds; creates internal melody.
  - сонет (sonnet) — 14-line form; associated with Mykola Zerov and Neoclassicists.
  - верлібр (free verse) — Poem without traditional meter or rhyme.
  - звуконаслідування (onomatopoeia) — State Standard term for phonetic imitation of natural sounds.
  - ритмомелодика (rhythm-melodics) — Complex interaction of rhythm and sound in a poem.
prerequisites:
- literaturoznavcha-terminolohiia
connects_to:
- review-c1-5
register: літературний
activity_hints:
- type: match-up
  focus: Match Стопа та метр examples to categories
  items: 12
- type: group-sort
  focus: Classify by Від катрена до сонета
  items: 12
- type: fill-in
  focus: Rewrite in target register
  items: 10
- type: quiz
  focus: Identify stylistic devices in context
  items: 12
- type: error-correction
  focus: Fix register-inappropriate language
  items: 8
- type: essay-response
  focus: Produce text in specified style

```

**Level constraints quick-ref:**

```
# C1 Quick Reference

> This file supplements the build prompt. Do NOT repeat targets already injected
> via `4000`, `Full Ukrainian immersion. No English except technical terminology. Sentences max 35 words.`, etc.

## Grammar Scope

No grammar restrictions. Full literary Ukrainian. No sentence length limit.

## Immersion (100% Ukrainian)

Full Ukrainian immersion. All content — grammar explanations, narratives, dialogues,
cultural content, analyses, literary critiques, activity instructions, tips — in Ukrainian.

English ONLY in vocabulary table translations (YAML).

No Language Link boxes at C1 — students learned all grammar terminology by B1.

## Module Types

| Type | Modules | Focus |
|------|---------|-------|
| Academic | M01-19 | Academic foundation |
| Professional | M21-34 | Professional communication |
| Stylistics | M36-55 | Stylistics & sociolinguistics |
| Folk Culture | M56-85 | Folk culture & arts |
| Literature | M86-105 | Literary analysis |
| Checkpoint | M20,35,55,85,105,106 | Review + assessment |

> Biography content is in separate **BIO** track.

## Content-Heavy Modules (Folk/Literature M56+)

**Golden Rule:** "Can the learner answer without reading the Ukrainian text?"
- If YES → rewrite (tests content recall, not language)
- If NO → keep (tests Ukrainian comprehension)

Forbidden activity patterns: "У якому році...", "Хто був...", "Що символізує..." (without text reference)
Required patterns: "Згідно з текстом...", "У тексті модуля автор...", "Яку стилістичну функцію..."

```

Read the State Standard compliance mapping (small file — read this FIRST):

```
docs/l2-uk-en/state-standard-2024-mapping.yaml
```

The full State Standard 2024 is at `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt` (431KB, ~6000 lines). **Do NOT read the entire file.** Instead:
1. Check the mapping file for the relevant `C1` section — find the grammar topic that matches your module
2. Use the `lines: [start, end]` coordinates to read ONLY that section from the full Standard
3. If no mapping entry exists for this topic, search by §number or keyword as fallback
4. If still no match, say so honestly — do NOT fabricate a §reference

---

## PART 1: Lightweight Research

Research **Аналіз поезії** for the **C1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Аналіз поезії

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
