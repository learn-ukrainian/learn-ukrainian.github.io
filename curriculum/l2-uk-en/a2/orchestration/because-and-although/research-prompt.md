# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-032
level: A2
sequence: 32
slug: because-and-although
version: '2.0'
title: Because and Although
subtitle: Linking Ideas Logically
focus: grammar
pedagogy: PPP
phase: A2.2
word_target: 2000
objectives:
- Learner can connect ideas using causal conjunctions
- Learner can express contrast using 'хоча' and 'але'
- Learner can build complex sentences
- Learner can explain reasons and consequences
sources:
- name: Ukrainian State Standard 2024 - Conjunctions
  url: https://mon.gov.ua/
  type: reference
  notes: Functional logic and conjunction requirements for A2
- name: Syntax of Modern Ukrainian - Complex Sentences
  url: https://uk.wikipedia.org/wiki/Складне_речення
  type: reference
  notes: Rules for causal and concessive clauses
content_outline:
- section: Вступ (Introduction)
  words: 300
  points:
  - Connecting simple ideas into complex logical structures — alignment with Ukrainian State Standard §4.4.2 (lines 1403-1416)
    for causal and adversarial sentences
  - 'Cultural anchor: Introducing the folk wisdom ''І трясця не бере без причини'' (Even the fever doesn''t strike without
    a reason) to illustrate that every result has a cause'
- section: 'Презентація: Чому та Як (Presentation: Why and How)'
  words: 550
  points:
  - 'Register Hierarchy: Clearly distinguish between neutral ''тому що'', casual/spoken ''бо'', and formal/written ''оскільки''
    — provide examples for each context'
  - 'Word Order Constraint: Fix the learner error of starting sentences with ''Because...'' (unnatural inversion) by drilling
    the preference for main clause first: ''Я не прийшов, тому що хворів'''
  - 'The Mandatory Comma: Addressing ''Comma Phobia'' by drilling the comma as an inseparable part of the conjunction ('',
    тому що'', '', бо'', '', оскільки'', '', але'')'
- section: 'Презентація: Всупереч обставинам (Presentation: Despite the Circumstances)'
  words: 425
  points:
  - Concession with 'хоча' (although) vs contrast with 'але' (but) — building sentences with counter-expectations (e.g., 'Хоча
    це дорого, я це куплю')
  - 'Attribution Accuracy: Positive ''завдяки'' (thanks to) vs Negative/Neutral ''через'' (due to/because of) — warning against
    the sarcastic or illiterate use of ''завдяки'' for negative events'
- section: 'Практика: Логічне обґрунтування (Practice: Logical Justification)'
  words: 425
  points:
  - 'Correction Drills: Identifying and fixing the use of ''через'' for positive outcomes (e.g., ''Я склав іспит через вчителя''
    -> ''Я склав іспит завдяки вчителю'')'
  - 'Argumentation practice: Re-phrasing casual explanations using ''бо'' into formal statements using ''оскільки'' for different
    social settings'
- section: Продукція та Діалоги (Production and Dialogues)
  words: 300
  points:
  - 'Investigative Journalist Roleplay: Interviewing a partner about a surprising result or event, requiring the use of ''через
    затори'' vs ''завдяки зусиллям'''
  - 'Logical Synthesis: Summarizing the transition from A1 simple sentences to A2 connected speech, emphasizing the ''glue''
    provided by logical conjunctions'
vocabulary_hints:
  required:
  - тому що (because) — Це сталося, тому що...; high frequency, neutral register
  - бо (because/for) — Я їм, бо голодний; high frequency, casual/spoken register
  - через (because of/due to) — Через погоду, через помилку; preposition for negative or neutral causes
  - завдяки (thanks to) — Завдяки тобі, завдяки допомозі; preposition strictly for positive causes
  - хоча (although) — Хоча я втомився, я піду; introduces counter-expectation/concession
  - але (but) — Standard adversarial conjunction (State Standard §4.4.2 requirement)
  recommended:
  - оскільки (since/as) — Оскільки ви тут...; formal/written register, often used in professional contexts
  - 'причина (reason) — Key noun for logic; idiomatic: ''без причини'' (folk wisdom)'
  - наслідок (consequence/result) — Useful for explaining the logical outcome of an action
persona:
  voice: Encouraging Cultural Guide
  role: Investigative Journalist
module_type: grammar
immersion: 60-75% Ukrainian
prerequisites:
- telling-stories
connects_to:
- she-said-that
grammar:
- Вступ
- Чому та Як
- Всупереч обставинам
register: розмовний
activity_hints:
- type: quiz
  focus: Identify correct forms
  items: 10
- type: fill-in
  focus: Complete with correct grammar
  items: 8
- type: match-up
  focus: Match forms to categories
  items: 10
- type: error-correction
  focus: Find and fix errors
  items: 6
- type: group-sort
  focus: Classify by grammatical feature
  items: 8
- type: essay-response
  focus: Write using target structures

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

Research **Because and Although** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Because and Although

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
