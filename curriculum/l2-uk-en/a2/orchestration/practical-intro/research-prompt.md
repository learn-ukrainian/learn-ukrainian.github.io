# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-061
level: A2
sequence: 61
slug: practical-intro
version: '2.0'
title: Practical Intro
subtitle: Real World Ukrainian
focus: practical
pedagogy: PPP
phase: A2.6 [Practical]
word_target: 2000
objectives:
- Learner can identify all 7 cases in context
- Learner can choose correct verb aspect
- Learner can fix common grammar mistakes
- Learner can build complex sentences
content_outline:
- section: 'Вступ: Від теорії до практики (Introduction: From Theory to Practice)'
  words: 300
  points:
  - Bridge from A2 grammar to functional usage (State Standard §4.2.2 alignment) — focus on applying norms in spontaneous
    speech
  - 'Cultural hook: Surzhyk as a transitional stage — viewing ''mistakes'' as stepping stones for speakers switching to Ukrainian;
    the concept of ''trying'' as a value'
- section: Сім відмінків у дії (The 7 Cases in Action)
  words: 525
  points:
  - Functional overview of all 7 cases (State Standard §4.2.2) — choosing cases based on communicative purpose rather than
    memorized paradigms
  - 'The Vocative case (Кличний) as a cultural marker of respect: contrasting casual ''Юра'' with formal ''Пане Юрію'' or
    ''Олено'' — etiquette rules for addressing different social roles'
  - 'Common case confusion: Drill the Genitive vs. Accusative distinction for negation (я не бачу книгу [Acc] vs. книги [Gen])'
- section: Вид дієслова в контексті (Verb Aspect in Context)
  words: 425
  points:
  - Differentiating aspect pairs (State Standard §4.2.3.1) — Perfective (result) vs. Imperfective (process/habit) in narrative
    storytelling
  - 'Learner error alert: The ''Perfective Present'' trap — explaining why ''я напишу'' equals future result, while ''я пишу''
    describes the current moment; practice with 5 minimal pairs'
  - 'Motion verb nuances: Revisiting ''йти'' vs. ''їхати'' — vehicle vs. foot travel in real-world scenarios'
- section: Складні речення та пояснення (Complex Sentences and Reasoning)
  words: 425
  points:
  - Constructing complex sentences using conjunctions 'тому що', 'бо' (reason), 'щоб' (purpose), and 'якщо' (condition) per
    State Standard §4.4.2
  - Moving beyond simple SVO structures — building multi-clause sentences to express logic and situational conditions in professional
    and personal contexts
- section: Типові помилки та інтеграція (Common Mistakes and Integration)
  words: 325
  points:
  - 'Diagnostic drill: Identifying and fixing common errors in case selection and aspect usage in a mixed-input text'
  - 'Scenario: Integration challenge — writing a formal/semi-formal message to a boss or friend (applying cases, aspect, and
    complex sentence connectors for reasoning)'
vocabulary_hints:
  required:
  - 'речення (sentence) — High frequency; collocations: скласти речення, просте/складне речення, член речення'
  - 'слово (word) — Very High frequency; collocations: нове слово, значення слова, іншомовне слово, чесне слово'
  - 'граматика (grammar) — collocations: вивчати граматику, правила граматики, граматична помилка'
  - 'правило (rule) — High frequency; collocations: запам''ятати правило, за правилом, виняток з правила'
  - 'помилка (mistake) — High frequency; collocations: зробити помилку, виправити помилку, груба/типова помилка'
  - 'правильно (correctly) — usage: як правильно сказати?; register: neutral/formal'
  - 'неправильно (incorrectly) — context: це граматично неправильно; register: neutral/formal'
  - 'контекст (context) — collocations: у контексті, зрозуміти з контексту, залежить від контексту'
  recommended:
  - 'відмінок (case) — metalanguage; context: визначити відмінок'
  - 'вид (aspect) — metalanguage; context: доконаний/недоконаний вид'
  - 'сполучник (conjunction) — context: поєднати частини речення'
  - 'порядок (order) — collocations: порядок слів'
activity_hints:
- type: fill-in
  focus: Case selection in context
  items: 20
- type: error-correction
  focus: Fix grammar mistakes
  items: 20
- type: unjumble
  focus: Build complex sentences
  items: 15
- type: quiz
  focus: Grammar rules review
  items: 15
connects_to:
- a2-62 (Practical Warm-up)
prerequisites:
- a2-60 (Checkpoint — Full Grammar)
persona:
  voice: Encouraging Cultural Guide
  role: Camp Counselor
grammar:
- Case system review in practical contexts
- Verb aspect review for real situations
- Sentence structure and common errors
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

Research **Practical Intro** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Practical Intro

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
