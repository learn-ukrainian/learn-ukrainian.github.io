# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-076
level: A2
sequence: 76
slug: a2-final-exam
version: '2.0'
title: A2 Final Exam
subtitle: Level Completion
focus: checkpoint
pedagogy: TTT
phase: A2.6 [Practical]
word_target: 2000
objectives:
- Learner can demonstrate A2 level proficiency
- Learner can solve practical problems in Ukrainian
- Learner can understand main points of complex texts
- Learner is ready for B1 level
content_outline:
- section: 'Вступ: Огляд іспиту (Overview / Огляд)'
  words: 300
  points:
  - Exam format overview referencing the modern Ukrainian 12-point grading system
    (where 12 is A+) vs the legacy 5-point Soviet scale still expected by some foreigners
  - Introduction to the University ECTS 100-point scale context often used for final
    certifications
  - 'Alignment with State Standard §3.7: demonstrate communicative competence in the
    ''learning'' domain, specifically actions related to gaining knowledge (вчити,
    вивчати, вчитися)'
- section: 'Навичка 1: Майстерність відмінків (Case System Mastery)'
  words: 433
  points:
  - 'Advanced review of case government focusing on exam-related verbs: ''відповідати
    на питання'' (verb + Accusative) vs ''відповідати студенту/викладачу'' (verb +
    Dative)'
  - 'Practice exercises addressing the common learner error: confusion between the
    noun phrase ''відповідь на питання'' (Acc) and the verbal construction'
  - Drills on correct case usage for 'готуватися до іспиту' (Genitive) and 'цікавитися
    результатом' (Instrumental)
- section: 'Навичка 2: Вид дієслова — Процес чи результат? (Verb Aspect)'
  words: 467
  points:
  - 'Explicit contrast between process (процес) and result (результат): ''я складав
    іспит'' (I was taking/trying) vs ''я склав іспит'' (I passed/completed)'
  - 'Correction of the frequent learner error: defaulting to imperfective ''Я складав''
    when a completed result like ''Я склав'' is required for successful certification'
  - 'Sentence transformation drills: changing descriptions of study habits (imperfective)
    into exam results (perfective)'
- section: 'Навичка 3: Навігація до екзаменаційного центру (Navigation)'
  words: 367
  points:
  - 'Practical application: ''Finding your way to the exam center'', integrating navigation
    vocabulary (ліворуч, праворуч, прямувати) with the academic theme'
  - Simulated dialogue for arriving at the ZNO (Зовнішнє незалежне оцінювання) or
    NMT (Національний мультипредметний тест) testing site
  - Giving and following directions within a university campus or school building
    context
- section: 'Інтеграційне завдання: Культура іспитів (Integration Challenge)'
  words: 433
  points:
  - Combined skills dialogue practising 'скласти іспит' (to pass/compose) as the preferred
    formal form; note that 'здати іспит' is also widely attested in Ukrainian (GRAC
    corpus) and is not a Russicism per se, but 'скласти' is considered more stylistically
    precise
  - 'Cultural deep dive: The role of ZNO/NMT as a modern standard fighting corruption
    in the Ukrainian education system'
  - 'Final simulation: Receiving results and discussing ''висока оцінка'' vs ''провалити
    іспит'' using appropriate register'
vocabulary_hints:
  required:
  - 'іспит (exam) — collocations: скласти іспит (pass), провалити іспит (fail), готуватися
    до іспиту (prepare for); High frequency academic/general'
  - 'завдання (task) — collocations: тестове завдання, виконати завдання, складне
    завдання'
  - 'відповідь (answer) — collocations: правильна відповідь, дати відповідь, шукати
    відповідь; note case government (на + Acc)'
  - 'результат (result) — collocations: гарний результат, отримати результат, чекати
    на результат; High frequency general'
  - 'рівень (level) — collocations: рівень знань, підвищити рівень, досягти рівня;
    High frequency general'
  - 'оцінка (grade) — collocations: висока оцінка, отримати оцінку, система оцінювання;
    Medium frequency education'
  - 'готовий (ready) — usage: бути готовим до випробувань'
  - 'успішно (successfully) — collocation: успішно скласти, успішно завершити'
  recommended:
  - 'розуміння (comprehension) — usage: рівень розуміння тексту'
  - 'навички (skills) — usage: мовні навички, практичні навички'
  - 'досягнення (achievement) — usage: вагомі досягнення в навчанні'
  - 'сертифікат (certificate) — usage: отримати сертифікат А2'
  - складати/скласти (to pass/compose) — preferred formal form; also 'здавати/здати'
    is standard Ukrainian (GRAC-attested)
activity_hints:
- type: quiz
  focus: Comprehensive A2 grammar test
  items: 30
- type: quiz
  focus: A2 vocabulary mastery
  items: 15
- type: quiz
  focus: A2 practical scenarios
  items: 10
connects_to:
- b1-01 (How to Talk About Grammar)
prerequisites:
- a2-75 (Introduction to Gerunds)
- a2-72 (Online Services)
- a2-60 (Checkpoint — Full Grammar)
persona:
  voice: Encouraging Cultural Guide
  role: University Dean
grammar:
- Comprehensive A2 grammar review (all cases)
- Verb aspect mastery
- Complex sentence structures
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

Research **A2 Final Exam** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: A2 Final Exam

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
