# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-059
level: A2
sequence: 59
slug: sports-fitness
version: '2.0'
title: Sports and Fitness
subtitle: Active Lifestyle
focus: vocabulary
pedagogy: PPP
phase: A2.5 [Vocabulary Expansion]
word_target: 2000
objectives:
- Learner can talk about sports and fitness
- Learner can use 'грати в' and 'займатися' correctly
- Learner can describe a sports event
- Learner can discuss healthy habits
content_outline:
- section: Вступ (Introduction)
  words: 300
  points:
  - 'Introduction to leisure and sports in Ukraine based on State Standard §3.4; Cultural hook: ''Football is King'' and the
    legendary status of Andriy Shevchenko as a national hero.'
  - Discussion of the cultural staple phrase «Вболівати за Динамо» (to root for Dynamo) to introduce the concept of sports
    fanship and national identity.
- section: Спортивні споруди та види спорту (Sports Facilities and Types of Sports)
  words: 475
  points:
  - 'Vocabulary expansion following State Standard §3.4 requirements: learning names of sports venues like стадіон (stadium),
    басейн (pool), корт (court), and ковзанка (skating rink).'
  - Cultural focus on boxing legends (Klitschko brothers, Oleksandr Usyk) to introduce individual sports and provide context
    for the verb «займатися боксом».
  - Distinction between team sports (football, basketball) and individual fitness activities (running, swimming, yoga).
- section: 'Граматика: Керування дієслів (Grammar: Verb Government)'
  words: 625
  points:
  - 'Strict binary focus on verb government: Team/Ball Games = «грати в/у» + Accusative case; Individual/Fitness = «займатися»
    + Instrumental case (State Standard §4.2.2.5).'
  - 'Correction of common learner error: explain that unlike English ''play football'', Ukrainian requires the preposition
    ''у/в'' (грати у футбол vs грати футбол).'
  - 'Reflexive verb government drill: addressing the mismatch where learners use Nominative after «займатися» instead of the
    required Instrumental (займатися спортом).'
  - 'Semantic nuance check: Distinguishing between «грати» (to play a sport/instrument) and «гратися» (to play with toys/child''s
    play) to ensure age-appropriate register.'
- section: Практика та діалоги (Practice and Dialogues)
  words: 400
  points:
  - Interactive dialogues about sports preferences and rooting for teams using the phrase «вболівати за» + Accusative.
  - Guided practice describing fitness routines and visits to the 'спортзал' (gym) and 'тренування' (training), reinforcing
    the 'займатися' + Instrumental pattern.
  - Sentence construction exercises using famous Ukrainian athletes (Usyk, Shevchenko) as mnemonic anchors for grammar rules.
- section: Здоровий спосіб життя та підсумок (Healthy Lifestyle and Summary)
  words: 200
  points:
  - Discussion of healthy habits and physical activity as part of daily life.
  - Summary of key collocations and a final check on the Accusative vs. Instrumental distinction in sports contexts.
vocabulary_hints:
  required:
  - спорт (sport) — займатися спортом (to do sports); very high frequency A2 core
  - грати (to play) — грати у футбол, грати в теніс; requires preposition 'в/у' + Accusative
  - займатися (to practice/do) — займатися плаванням, займатися боксом; requires Instrumental case
  - футбол (football) — грати у футбол, дивитися футбол, вболівати за футбольну команду
  - команда (team) — грати в команді, улюблена команда; high frequency
  - стадіон (stadium) — ходити на стадіон, тренуватися на стадіоні; State Standard §3.4
  - басейн (pool) — ходити в басейн, плавати в басейні; State Standard §3.4
  - спортзал (gym) — тренування в спортзалі, ходити в спортзал; modern usage
  - матч (match) — футбольний матч, дивитися матч
  - вболівати (to root/cheer) — вболівати за команду, вболівальник (fan)
  recommended:
  - баскетбол (basketball) — грати в баскетбол
  - бокс (boxing) — займатися боксом; cultural link to Usyk/Klitschko
  - плавання (swimming) — займатися плаванням
  - біг (running) — займатися бігом
  - йога (yoga) — займатися йогою
  - ковзанка (skating rink) — кататися на ковзанці; State Standard §3.4
  - змагання (competition) — брати участь у змаганнях
  - тренер (coach) — слухати тренера
  - вигравати (to win) — наша команда виграла
  - програвати (to lose) — не хотіти програвати
activity_hints:
- type: match-up
  focus: Sports vocabulary
  items: 30
- type: match-up
  focus: Match verbs to sports
  items: 20
- type: fill-in
  focus: Complete sports sentences
  items: 15
- type: quiz
  focus: Describe your fitness routine
  items: 8
connects_to:
- a2-60 (Checkpoint — Full Grammar)
- a2-56 (Hobbies and Leisure)
prerequisites:
- a2-58 (Shopping and Services)
persona:
  voice: Encouraging Cultural Guide
  role: Olympic Trainer
grammar:
- Sports verbs (грати в, займатися)
- Accusative vs instrumental in sports contexts
- Describing events (match, game, competition)
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

Research **Sports and Fitness** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Sports and Fitness

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
