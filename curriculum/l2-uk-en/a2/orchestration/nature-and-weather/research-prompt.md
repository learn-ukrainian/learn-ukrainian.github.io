# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-052
level: A2
sequence: 52
slug: nature-and-weather
version: '2.0'
title: Nature and Weather
subtitle: The World Around Us
focus: vocabulary
pedagogy: PPP
phase: A2.5 [Vocabulary Expansion]
word_target: 2000
objectives:
- Learner can describe weather conditions in detail
- Learner can talk about seasons and climate
- Learner can describe landscapes
- Learner can discuss nature and environment
content_outline:
- section: 'Вступ: Природа України (Introduction: Ukraine''s Nature)'
  words: 300
  points:
  - 'Geographical overview of Ukraine as per Standard §3.13: contrasting the diverse landscapes of the Carpathian mountains
    (Карпати) and the southern steppes (степи).'
  - Introduction to the 'Carpathian Forester' persona and the transition from A1 basic nouns to A2 detailed nature descriptions
    and personal states.
- section: 'Лексика: Ландшафти та легенди (Vocabulary: Landscapes and Legends)'
  words: 600
  points:
  - 'High-frequency nature vocabulary (гора, ліс, річка, озеро) enriched with A2 collocations: ''густий ліс'', ''швидка річка'',
    and ''вершина гори'' (§3.13).'
  - 'Cultural Hook: The legend of Lake Nesamovyte (Озеро Несамовите); teaching ''буря'' (storm) and ''град'' (hail) through
    the folk belief that disturbing the water triggers dangerous mountain weather.'
  - 'Flora and Fauna (§3.13): Introducing common plants and domestic animals (свійські тварини) within the context of their
    natural Ukrainian habitats.'
- section: 'Граматика: Погода та стани (Grammar: Weather and States)'
  words: 575
  points:
  - 'Dative Case for States (§4.2.2.3): Mastering ''Мені холодно/тепло/жарко'' and correcting the pervasive learner error
    ''Я холодний'' (I am a cold person/corpse).'
  - 'Idiomatic Weather Verbs: Correcting the literal ''Це є дощ'' with the correct verb phrases ''Йде дощ'', ''Падає сніг'',
    or the synthetic verb ''Дощить''.'
  - 'Grammar Contrast: Explicitly distinguishing between Adjectives (Який день? Холодний) for noun modification and Adverbs
    (Як надворі? Холодно) for impersonal weather descriptions.'
  - 'Visualizing Impersonal Constructions: Construction of a comparative table mapping English personal subjects to Ukrainian
    Dative structures for weather and physical feelings.'
- section: 'Практика: Прогноз та розмови (Practice: Forecast and Dialogues)'
  words: 325
  points:
  - 'Mountain Survival Dialogue: Using weather vocabulary to discuss unpredictable conditions through the idiom ''Сім погод
    надворі''.'
  - 'Communicative Task: Describing a favorite landscape using expanded adjectives and dative-state constructions to express
    comfort or discomfort (e.g., ''Біля річки мені прохолодно'').'
  - 'Weather Forecasting: Roleplay practicing ''прогноз погоди'' and ''сонячна погода'' in a realistic conversational or broadcast
    register.'
- section: Підсумок (Summary)
  words: 200
  points:
  - Review of essential nature collocations and the functional shift from Nominative labels to Dative case descriptions of
    states (§4.2.2.3).
  - 'Self-Correction Check: Distinguishing between descriptive nature adjectives and impersonal weather adverbs to avoid common
    A2 errors.'
vocabulary_hints:
  required:
  - погода (weather) — гарна/погана погода, прогноз погоди, сонячна погода (High frequency)
  - дощ (rain) — йде дощ, сильний дощ, під дощем, мокнути під дощем (High frequency)
  - сніг (snow) — падає сніг, білий сніг, багато снігу (High frequency)
  - ліс (forest) — густий ліс, у лісі, лісова стежка (High frequency)
  - гора (mountain) — висока гора, у горах, вершина гори, Карпатські гори (High frequency)
  - річка (river) — швидка річка, на березі річки, купатися в річці (Med-High frequency)
  - клімат (climate) — континентальний клімат, зміни клімату
  - природа (nature) — дика природа, на лоні природи
  recommended:
  - озеро (lake) — Озеро Несамовите, чисте озеро; cultural hook for storms
  - град (hail) — сильний град, град у горах; associated with Lake Nesamovyte legend
  - туман (fog) — густий туман, у тумані
  - степ (steppe) — широкий степ, у степу; key geographical contrast (§3.13)
  - довкілля (environment) — охорона довкілля, навколишнє довкілля
  - тварина (animal) — свійська тварина, дика тварина (§3.13)
activity_hints:
- type: match-up
  focus: Nature and weather words
  items: 35
- type: match-up
  focus: Match weather to descriptions
  items: 20
- type: fill-in
  focus: Complete nature descriptions
  items: 15
- type: quiz
  focus: Describe weather and landscapes
  items: 8
connects_to:
- a2-53 (Emotions and Personality)
prerequisites:
- a1-29 (Weather and Nature)
- a2-51 (Home and Furniture)
persona:
  voice: Encouraging Cultural Guide
  role: Carpathian Forester
grammar:
- Weather expressions (холодно, тепло, вітряно)
- Nature vocabulary
- Seasons and describing landscapes
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

Research **Nature and Weather** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Nature and Weather

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
