# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-057
level: A2
sequence: 57
slug: education-learning
version: '2.0'
title: Education and Learning
subtitle: School and University
focus: vocabulary
pedagogy: PPP
phase: A2.5 [Vocabulary Expansion]
word_target: 2000
objectives:
- Learner can describe their studies
- Learner can use 'вчитися' and 'вивчати' correctly
- Learner can talk about school/university subjects
- Learner can discuss exams and grades
content_outline:
- section: Вступ (Introduction)
  words: 275
  points:
  - 'Cultural hook: Knowledge Day (День знань) on September 1st; describe the ''First Bell'' (Перший дзвоник) traditions,
    including students in vyshyvankas and the ceremony of a senior carrying a first-grader.'
  - 'Contextual overview of the education system; high-frequency collocations for starting and finishing studies: «ходити
    до школи», «закінчити школу», and «вступати до університету».'
- section: 'Лексика: Навчальні предмети та речі (Vocabulary: Subjects and Supplies)'
  words: 400
  points:
  - 'Alignment with State Standard §3.7: categorize school subjects (математика, історія, фізика) and basic school supplies
    (канцелярські товари) such as «зошит», «ручка», and «підручник».'
  - Describing interests and preferences using collocations like «улюблений предмет» and «профільний предмет»; building on
    a2-09 Dative Case structures (e.g., «Мені подобається історія»).
- section: 'Граматика: Дієслова навчання (Grammar: Learning Verbs)'
  words: 550
  points:
  - High-value distinction between transitive «вивчати» (requires a direct object/subject) and intransitive/reflexive «вчитися»
    (process, location, or manner); provide a clear comparison table.
  - 'Learner error correction: address the common confusion between «Я вивчаю в школі» (Wrong) vs «Я вчуся в школі» (Correct)
    and «Я вчуся математику» (Wrong) vs «Я вивчаю математику» (Correct).'
  - Integration of «навчати» (to teach/instruct) to align with State Standard action requirements for acquiring knowledge;
    drill with basic sentence transformations.
- section: Академічне життя (Academic Life)
  words: 325
  points:
  - 'Prepositional patterns in education: drill the distinction between «в/у» for institutions (в школі, в університеті) vs
    «на» for events/subdivisions (на уроці, на лекції, на факультеті).'
  - 'University terminology and roles: describe the interaction between «студент» and «викладач»; introduce academic milestones
    like «семінар», «залік» (credit), and «курсова робота» (course paper).'
- section: Оцінювання та іспити (Assessment and Exams)
  words: 325
  points:
  - 'Cultural hook: the Ukrainian 12-point grading system; explain the scale (10-12 High, 7-9 Sufficient, etc.) and use realistic
    grade examples in dialogues (e.g., «Я отримав 11 балів»).'
  - 'Exam collocations and learner error: correct the literal translation of ''take an exam'' as «брати іспит» (Wrong). Use
    «складати іспит» (process) and «скласти іспит» (pass/result).'
- section: Підсумок (Summary)
  words: 125
  points:
  - Synthesis of school vs. university vocabulary; final review of the «вчитися» vs «вивчати» distinction through a summarized
    checklist.
  - 'Personal application: learners describe their own educational background or current learning goals using the correct
    verbs and cultural context provided in the module.'
vocabulary_hints:
  required:
  - школа (school) — ходити до школи, закінчити школу, середня школа, у школі; high-frequency core noun
  - університет (university) — вступати до університету, навчатися в університеті, державний університет; high-frequency core
    noun
  - 'вчитися (to study) — intransitive (process/location); вчитися в школі/університеті, вчитися старанно, вчитися на відмінно;
    note: never takes a direct object'
  - 'вивчати (to learn) — transitive (+ object); вивчати українську мову, вивчати історію, вивчати нові слова; note: always
    requires an object in the accusative case'
  - предмет (subject) — шкільний предмет, улюблений предмет, профільний предмет; refers to academic disciplines
  - іспит (exam) — складати іспит (take/attempt), скласти іспит (pass), провалити іспит (fail), випускний іспит
  - оцінка (grade) — 12-бальна система (12-point scale); гарна оцінка, висока оцінка, отримувати оцінки
  - студент (student) — academic life context; masculine/feminine forms (студент/студентка)
  recommended:
  - викладач (lecturer) — university context; distinct from 'вчитель' (school teacher)
  - 'лекція (lecture) — usage: на лекції (requires preposition «на»)'
  - залік (credit/test) — university context; distinct from «іспит» as a pass/fail assessment
  - диплом (diploma) — graduation context; захищати диплом (defend a thesis)
  - стипендія (scholarship) — financial aid context; отримувати стипендію
  - курсова (course paper) — university project context; писати курсову роботу
  - підручник (textbook) — навчатися за підручником; core school supply
  - зошит (notebook) — писати в зошиті; core school supply
activity_hints:
- type: match-up
  focus: Education vocabulary
  items: 30
- type: fill-in
  focus: Complete academic sentences
  items: 20
- type: cloze
  focus: University conversation
  items: 10
- type: quiz
  focus: Describe your studies
  items: 8
connects_to:
- a2-58 (Shopping and Services)
prerequisites:
- a2-56 (Hobbies and Leisure)
persona:
  voice: Encouraging Cultural Guide
  role: School Principal
grammar:
- Education verbs (вчитися, вивчати, навчати)
- School subjects vocabulary
- Grades, exams, and academic terms
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

Research **Education and Learning** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Education and Learning

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
