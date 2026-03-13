# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-054
level: A2
sequence: 54
slug: work-professions
version: '2.0'
title: Work and Professions
subtitle: Jobs and Careers
focus: vocabulary
pedagogy: PPP
phase: A2.5 [Vocabulary Expansion]
word_target: 2000
objectives:
- Learner can name common professions
- Learner can describe their job
- Learner can talk about workplace activities
- Learner can use instrumental case for jobs
content_outline:
- section: 'Вступ: Світ роботи (Introduction: World of Work)'
  words: 300
  points:
  - 'Modern Ukrainian job market overview: focus on the IT sector prominence where «програміст» is a key cultural figure associated
    with «віддалено» (remote work) and «гнучкий графік» (flexible schedule).'
  - 'High-frequency workplace collocations: introduce «шукати роботу», «місце роботи», and contrasting descriptions like «важка
    робота» vs. «цікава робота».'
- section: Назви професій та гендер (Profession Names and Gender)
  words: 400
  points:
  - 'Common professions vocabulary: ensure gender balance (лікар/лікарка, вчитель/вчителька) and note that while spoken language
    prefers feminine forms, official titles in formal documents often remain masculine.'
  - 'Cultural hook — Teacher''s Day: The first Sunday of October celebration where «вчитель» is honored with high social respect,
    emphasizing their role as a mentor/guide.'
  - 'Educational titles: Introduce academic roles like «професор» and «доцент», which are highly respected and used as formal
    titles in Ukrainian society.'
- section: 'Граматика: Орудний відмінок (Grammar: Instrumental Case)'
  words: 550
  points:
  - 'State Standard §4.2.2.5.1 alignment: teaching the use of Instrumental without a preposition to characterize a person
    by profession (e.g., «Олег буде програмувальником», «Микола хоче стати викладачем»).'
  - 'The logic of Instrumental: explain that the case represents the ''Role/Function'' — you are using your profession as
    a tool to function in society.'
  - 'Verb triggers: reinforce that verbs like «працювати», «бути», and «стати» always trigger the Instrumental case when describing
    jobs.'
  - 'Learner error — ''To Be'' omission: contrast the Nominative used in the present tense («Я — лікар») with the mandatory
    Instrumental used in past/future («Я був лікарем», «Я буду лікарем»).'
- section: Діловий етикет та звертання (Business Etiquette and Address)
  words: 375
  points:
  - 'Formal address in the workplace: emphasize the use of «Пан/Пані» + First Name or Surname, contrasting it with the informal
    Western ''first-name basis'' approach.'
  - 'Professional relationships: distinguish between «колега» (colleague) and friend; drill collocations like «шановний колега»
    and «порада колеги» for formal registers.'
- section: 'Практика: Співбесіда та обов''язки (Practice: Interview and Duties)'
  words: 375
  points:
  - 'Job interview preparation: introduction to «співбесіда» and «резюме» as a bridge to module a2-64, focusing on describing
    basic duties.'
  - 'Correction of learner errors: focus on ending mismatches between masculine (-ом/-ем) and feminine (-ою/-ею) Instrumental
    endings (e.g., «вона працює секретаркою» not «секретаром»).'
  - 'Collocations for responsibilities: drill verbs governing specific roles like «викликати лікаря», «записатися до лікаря»,
    and «бути класним керівником».'
vocabulary_hints:
  required:
  - 'робота (work/job) — high frequency; collocations: шукати роботу, графік роботи, місце роботи, важка/цікава робота'
  - 'професія (profession) — State Standard: характеристика особи за професією; за професією'
  - лікар (doctor) — сімейний лікар (family doctor), головний лікар, викликати лікаря, записатися до лікаря
  - вчитель (teacher) — вчитель історії, класний керівник, День вчителя (cultural respect context)
  - інженер (engineer) — головний інженер, працювати інженером, інженер-програміст
  - офіс (office) — працювати в офісі, опен-спейс
  - зарплата (salary) — висока/низька зарплата, отримувати зарплату
  - колега (colleague) — шановний колега (formal), мої колеги, порада колеги
  recommended:
  - програміст (programmer) — modern cultural hook; працювати віддалено (remote), гнучкий графік
  - бухгалтер (accountant) — головний бухгалтер
  - резюме (resume/CV) — писати резюме, додавати до резюме
  - співбесіда (interview) — проходити співбесіду, запросити на співбесіду
  - керівник (manager/head) — класний керівник (homeroom teacher), безпосередній керівник
  - підлеглий (subordinate) — мати підлеглих, спілкування з підлеглими
  - лікарка (female doctor) — standard feminine form for gender balance
  - вчителька (female teacher) — standard feminine form for gender balance
activity_hints:
- type: match-up
  focus: Professions and workplace
  items: 30
- type: fill-in
  focus: Complete work descriptions
  items: 20
- type: cloze
  focus: Job interview
  items: 10
- type: quiz
  focus: Describe your work
  items: 8
connects_to:
- a2-55 (Technology and Media)
- a2-67 (Scheduling Interviews)
prerequisites:
- a2-53 (Emotions and Personality)
persona:
  voice: Encouraging Cultural Guide
  role: Career Counselor
grammar:
- Instrumental with professions (працювати лікарем)
- Workplace vocabulary
- Describing duties and responsibilities
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

Research **Work and Professions** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Work and Professions

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
