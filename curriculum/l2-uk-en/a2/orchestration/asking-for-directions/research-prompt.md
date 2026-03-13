# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-069
level: A2
sequence: 69
slug: asking-for-directions
version: '2.0'
title: Asking for Directions
subtitle: Getting Around Town
focus: practical
pedagogy: PPP
phase: A2.6 [Practical]
word_target: 2000
objectives:
- Learner can ask for directions to landmarks
- Learner can understand complex route descriptions
- Learner can use public transport vocabulary
- Learner can describe their location
content_outline:
- section: Вступ (Introduction)
  words: 275
  points:
  - 'Introduction to the urban environment and basic navigation — §3.5: Середовище перебування (місто чи село). Focus on essential
    direction adverbs: прямо, ліворуч, праворуч.'
  - 'The Persona Hook: A lost tourist in Odesa. Set the scene where navigating the city requires not just a map, but a sense
    of humor and local communication styles.'
- section: Презентація (Presentation)
  words: 625
  points:
  - 'The Core Motion Distinction — §3.6: йти (foot) vs. їхати (vehicle). Focus on the primary A2 stumbling block: learner
    error ''Я йду в Київ'' (meaning walking) vs. correct ''Я їду в Київ'' (taking transport).'
  - 'Conjugation of Motion Verbs — §4.2.3.1: дієвідмінювання дієслів у теперішньому часі (іду, ідеш vs. їду, їдеш). Highlight
    the phonetic similarity between ''іду'' and ''їду'' and how to distinguish them in speech.'
  - 'Unidirectional vs. Habitual Motion — addressing the learner error of using unidirectional forms for repeated actions.
    Error: ''Я йду в школу кожен день'' vs. correction: ''Я хожу в школу кожен день''.'
  - 'Prefix Nuances: по- (start) vs. при- (arrival). Drill the distinction to avoid errors like ''Він приїхав у магазин''
    when the subject has only just departed. Correction: ''Він поїхав у магазин''.'
- section: Культурний контекст (Cultural Context)
  words: 425
  points:
  - 'Odesa Style Navigation: Discuss the classic trope of answering a question with a question (''А вам це точно треба?'')
    and the tendency for simple directions to turn into long, winding stories.'
  - 'Landmarks over Distances: In Ukrainian culture, directions are relative. Drill the use of landmarks (''біля аптеки'',
    ''перед пам''ятником'') instead of strict meters or cardinal directions. Note that ''йти прямо'' is often a relative suggestion.'
- section: Практика та діалоги (Practice and Dialogues)
  words: 400
  points:
  - 'Navigating to Odesa Icons: Creating dialogues centered on finding the Opera House, Pryvoz market, or Deribasivska street.
    Practice the sequence: Excuse me -> How to get to... -> Landmark confirmation.'
  - 'Transport Vocabulary in Action: Using specific local transport terms (трамвай, маршрутка). Practice phrases like ''їхати
    автобусом'' or ''сісти на трамвай'' and identifying the correct ''зупинка'' (stop).'
- section: Підсумок та розповідь (Summary and Narrative)
  words: 275
  points:
  - 'The Navigation Story: A humorous Odesa narrative based on a classic anecdote (e.g., a tourist asking for directions to
    a street they are already standing on). Focus on the distinction between foot and vehicle movement.'
  - 'Final Synthesis: Review of §3.5 and §3.6 competencies. Reinforce the distinction between ''йти'' and ''їхати'' as the
    module''s primary grammar takeaway.'
vocabulary_hints:
  required:
  - 'йти (to go on foot) — High Freq (Code 4 0011); collocations: йти пішки, йти прямо, йти до...'
  - 'їхати (to go by transport) — Very High Freq (Code 6 1111); collocations: їхати автобусом, їхати на роботу, їхати в центр'
  - 'повертати (to turn) — Medium-High Freq (Code 3 0001); collocations: повертати праворуч/ліворуч, повертати за ріг'
  - 'зупинка (stop) — High Freq; collocations: автобусна зупинка, кінцева зупинка'
  - прямо (straight) — Basic direction; note its relative usage in Odesa/Ukrainian context
  - ліворуч (to the left) — Basic direction adverb
  - праворуч (to the right) — Basic direction adverb
  - маршрутка (minibus) — Essential Ukrainian transport context
  - трамвай (tram) — Culturally significant in Odesa navigation
  - 'автобус (bus) — High Freq; collocations: автобусна зупинка'
  - метро (metro) — use with їхати (їхати на метро)
  recommended:
  - пересадка (transfer) — useful for complex public transport directions
  - вихід (exit) — essential for transport/metro navigation
  - платформа (platform) — train/metro context
  - квиток (ticket) — buying tickets for transport
  - розклад (schedule) — checking transport times
  - біля (near) — essential for landmark navigation (e.g., біля аптеки)
  - перед (in front of) — landmark navigation (e.g., перед пам'ятником)
  - повз (past) — preposition of movement (e.g., йти повз театр)
  - через (through/across) — preposition of movement (e.g., їхати через міст)
  - маршрут (route) — context of planning a trip or following directions
activity_hints:
- type: match-up
  focus: Transport vocabulary
  items: 25
- type: fill-in
  focus: Ask about transport
  items: 20
- type: quiz
  focus: Describe your location
  items: 10
connects_to:
- a2-70 (Social Media Ukrainian)
prerequisites:
- a2-68 (Giving Directions)
persona:
  voice: Encouraging Cultural Guide
  role: Lost Tourist in Odesa
grammar:
- Verbs of motion (йти, їхати, ходити, їздити)
- Prepositions of movement (до, повз, через)
- Imperative for directions
register: розмовний
immersion: 75-90% Ukrainian

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

Research **Asking for Directions** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Asking for Directions

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
