# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-073
level: A2
sequence: 73
slug: participles-passive
version: '2.0'
title: Passive Participles
subtitle: Past Passive Participles as Adjectives (-ний/-тий)
focus: grammar
pedagogy: PPP
phase: A2.7
word_target: 2000
objectives:
- Learner can recognize and form past passive participles (-ний/-тий)
- Learner can use participles with correct gender/number/case agreement
- Learner can distinguish participles from regular adjectives
- Learner can identify the active participle ban in standard Ukrainian
sources:
- name: Ukrainian State Standard 2024 - Participles
  url: https://mon.gov.ua/
  type: reference
  notes: '§4.2.3.1: participles required at A2 level'
content_outline:
- section: 'Вступ: Дієприкметники навколо нас (Introduction: Participles Around Us)'
  words: 300
  points:
  - 'Alignment with State Standard 2024: Scaffolding B1 morphological concepts (§4.2.3.1) through the lens of A2 adjectival
    declension (§4.2.1.2) for practical communication.'
  - 'Passive encounter in daily life: explaining why learners find participles in signs, labels, and instructions before they
    master the generative grammar.'
  - 'Functional goal: prioritizing the recognition of high-frequency adjectival participles (open, closed, busy) over complex
    grammatical transformation.'
- section: Утворення дієприкметників (Participle Formation)
  words: 475
  points:
  - Formation patterns using -ний and -тий suffixes from perfective verb stems (зробити → зроблений, відкрити → відкритий,
    написати → написаний).
  - 'Stem changes: consonant mutations before -ний (підготувати → підготовлений, побудувати → побудований); recognizing patterns.'
  - 'High-utility lexical set: essential daily words — зайнятий (busy/occupied), зламаний (broken), забутий (forgotten), підготовлений
    (prepared).'
- section: Узгодження як прикметник (Agreement Like Adjectives)
  words: 400
  points:
  - 'Agreement rules: treating participles as adjectives in gender, number, and case (написаний лист-m, написана книга-f,
    написане слово-n, написані листи-pl).'
  - 'Learner error prevention: focusing on Agreement Mismatch (двері відкритий → двері відкриті, since двері is plural).'
  - 'Case forms: declining participles in oblique cases — written exercises with Gen, Dat, Inst forms (зламаного ліфта, зайнятому
    студенту).'
- section: Дієприкметник у контексті (Participles in Context)
  words: 400
  points:
  - 'Attributive position: написаний лист (a written letter) — participle before or after noun.'
  - 'Predicative position: Лист написаний (The letter is written) — participle as predicate with бути (Лист був написаний,
    Лист буде написаний).'
  - 'Proverbs and fixed expressions: «Дарованому коню в зуби не заглядають» — how participles decline in proverbs.'
  - 'Contrast with active voice: «Лист написаний мамою» (passive) vs «Мама написала лист» (active) — recognition, not active
    production of passive voice.'
- section: Помилки та заборони (Errors and Restrictions)
  words: 225
  points:
  - 'The Active Participle Ban: in standard Ukrainian, -ючий/-ачий forms are NOT used (*читаючий хлопець is a Russian/English
    calque); use relative clauses instead: «хлопець, який читає».'
  - 'Common errors: confusing adjectives and participles; knowing when a word is "really" a participle vs a lexicalized adjective
    (відомий, знайомий).'
- section: Практика (Practice)
  words: 200
  points:
  - Form participles from given verbs; complete sentences with correct agreement.
  - 'Reading comprehension: identify participles in a short text and determine their function (attributive/predicative).'
  - 'Transition to next module: recognize -но/-то forms on signs → impersonal-passive.'
vocabulary_hints:
  required:
  - зроблений (made/done) — зроблена робота, зроблений вибір; from зробити
  - відкритий (open) — відкриті двері, відкритий урок; from відкрити
  - закритий (closed) — закритий магазин, закриті очі; from закрити
  - написаний (written) — написаний лист, написана книга; from написати
  - зайнятий (busy/occupied) — зайняте місце, він зайнятий; from зайняти
  - зламаний (broken) — зламаний ліфт, зламана рука; from зламати
  - забутий (forgotten) — забутий пароль, забуті речі; from забути
  - побудований (built) — побудований будинок, побудована школа; from побудувати
  recommended:
  - підготовлений (prepared) — підготовлений до іспиту; from підготувати
  - відомий (known/famous) — lexicalized participle; відома актриса
  - знайомий (familiar/acquaintance) — lexicalized participle; знайома людина
  - втрачений (lost) — втрачений час, втрачена можливість; from втратити
  - куплений (bought) — куплений квиток; from купити
  - отриманий (received) — отриманий лист; from отримати
activity_hints:
- type: fill-in
  focus: Form participles from verbs
  items: 20
- type: fill-in
  focus: Agreement (gender/number/case matching)
  items: 15
- type: quiz
  focus: Participle vs regular adjective identification
  items: 12
- type: match-up
  focus: Verb to participle pairs
  items: 15
connects_to:
- a2-74 (Impersonal Passive Forms)
prerequisites:
- a2-72 (Online Services)
persona:
  voice: Encouraging Cultural Guide
  role: Copy Editor
grammar:
- past passive participles (-ний/-тий forms)
- participle agreement (gender, number, case)
- attributive vs predicative usage
- active participle restriction
bridge_to: B1
module_type: grammar
immersion: 75-90% Ukrainian
register: розмовний

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

Research **Passive Participles** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Passive Participles

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
