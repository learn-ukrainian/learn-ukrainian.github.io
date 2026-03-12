# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-028
level: A2
sequence: 28
slug: complete-imperative
version: '2.0'
title: Complete Imperative
subtitle: Let It Be! (3rd Person)
focus: grammar
pedagogy: PPP
phase: A2.2
word_target: 2000
objectives:
- Learner can form 3rd person commands using хай/нехай
- Learner can make toasts and wishes
- Learner can relay indirect commands
- Learner can use the full range of imperative forms
sources:
- name: Ukrainian State Standard 2024 - Imperative
  url: https://mon.gov.ua/
  type: reference
  notes: Complete imperative mood requirements for A2
- name: Grammar of Ukrainian Language - Verb Moods
  url: https://uk.wikipedia.org/wiki/Наказовий_спосіб
  type: reference
  notes: Detailed rules for all persons in imperative
content_outline:
- section: 'Вступ: Воля та соціальний клей (Introduction: Willpower and Social Glue)'
  words: 325
  points:
  - Concept of willpower in language and why the imperative is not always a 'command' — contrast with English 'Please' dependency
  - 'Cultural hook: Wishes like «Нехай щастить!» or «Хай щастить!» function as social glue rather than commands, emphasizing
    shared hopes for success'
  - 'Introduction to the persona: Carpathian Rescue Lead using imperative for both safety and camaraderie'
- section: 'Граматична база: Усі особи наказового способу (Grammar Base: All Persons of Imperative)'
  words: 500
  points:
  - Review of 2nd person (ти/ви) forms and introduction to the 'Let's' form (-мо/-імо suffix) — e.g., ході́мо, робі́мо
  - 'State Standard 2024 (§4.2.3.2) requirements: Formation of 3rd person singular and plural using particles хай / нехай'
  - 'State Standard examples with IPA: мрі́яти (мрій, мрі́йте, хай мрі́є), каза́ти (кажи́, кажі́ть, хай ка́же), пи́ти (пий,
    пи́йте, хай п’є)'
  - 'Formation nuances: explaining why хай/нехай uses the regular 3rd person present/future form (хай він чита́є) unlike the
    special stems of the 2nd person'
- section: Виклики та пастки для учня (Challenges and Learner Traps)
  words: 400
  points:
  - 'The ''Negative'' Trap: Explicitly correcting the assumption that ''нехай'' is the negative of ''хай'' — drill their interchangeability'
  - 'Implicit ''Let''s'': Correcting the common error where English speakers try to use the infinitive with a ''let''s'' equivalent
    instead of the -мо/-імо suffix'
  - 'Negative Imperatives: Correct placement of ''не'' in 3rd person (хай не читає) and 1st person plural (не ходімо);
    note that нехай/хай is a 3rd-person particle and cannot combine with 1st-person -мо forms'
- section: 'Культурний контекст: Ритуал тостів (Cultural Context: Ritual of Toasts)'
  words: 400
  points:
  - 'The ritual of «Будьмо!»: historical significance as a call to collective presence and survival, not just a drinking phrase'
  - 'The Third Toast Protocol: Tradition of dedicating the third toast «за любов» or «за жінок» — cultural note: men traditionally
    stand as a sign of respect'
  - 'Formulating wishes with the verb «бажати» (to wish) — practice with Genitive case: «бажаю щастя», «бажаю успіхів»'
- section: 'Практичне застосування: Борщ та координація (Practical Application: Borscht and Coordination)'
  words: 375
  points:
  - 'Borscht recipe practice: contrasting 2nd person commands (додайте) with collective suggestions (додаймо) during the cooking
    process'
  - 'Team coordination dialogue: mixing ''Do this'' (2nd person), ''Let him do that'' (3rd person), and ''Let''s do this''
    (1st person plural)'
  - 'Vocabulary hook: incorporating common collocations like «ходімо в гості» and «нехай буде» (let it be)'
vocabulary_hints:
  required:
  - 'хай (let) — high frequency particle for 3rd person; collocations: хай живе (long live), хай щастить (good luck); IPA:
    [xɑi̯]'
  - 'нехай (let) — high frequency (formal/lit) particle for 3rd person; interchangeable with хай; collocation: нехай буде
    (let it be); IPA: [neˈxɑi̯]'
  - 'бу́дьмо (cheers/let us be) — standard drinking toast; centuries-old call to collective presence; IPA: [ˈbudʲmo]'
  - 'бажа́ти (to wish) — takes Genitive case; collocations: бажаю щастя (I wish happiness), бажаю успіхів (I wish success);
    IPA: [bɐˈʒɑte]'
  - 'ході́мо (let''s go) — 1st person plural imperative of йти/ходити; collocations: ходімо разом, ходімо в гості; IPA: [xoˈdʲimo]'
  recommended:
  - 'мрі́яти (to dream) — imperative: мрій/мрійте/нехай мріє; State Standard example; IPA: [ˈmrijɐte]'
  - 'каза́ти (to say) — imperative: кажи/кажіть/нехай каже; State Standard example; IPA: [kɐˈzɑte]'
  - 'пи́ти (to drink) — imperative: пий/пийте/нехай п''є; State Standard example; IPA: [ˈpɪte]'
persona:
  voice: Encouraging Cultural Guide
  role: Carpathian Rescue Lead
module_type: grammar
immersion: 60-75% Ukrainian
prerequisites:
- if-i-were
connects_to:
- smart-shopping
grammar:
- Воля та соціальний клей
- Усі особи наказового способу
- Виклики та пастки для учня
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

Research **Complete Imperative** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Complete Imperative

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
