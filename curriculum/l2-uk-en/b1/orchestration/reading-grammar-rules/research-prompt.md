# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b1-003
level: B1
sequence: 3
slug: reading-grammar-rules
version: '2.0'
title: Читаємо граматичні правила
subtitle: Understanding grammar explanations in Ukrainian
focus: integration
pedagogy: PPP
phase: B1.0 Bridge
word_target: 4000
objectives:
- Learner can understand standard grammar explanation patterns
- Learner can follow Ukrainian grammar instructions
- Learner can identify word formation components
- Learner can recognize activity instruction verbs
- Learner can understand analytical terminology
- Learner can distinguish language styles and registers
sources:
- name: Ukrainian Grammar Textbooks
  url: https://mon.gov.ua/
  type: reference
  notes: Standard patterns used in Ukrainian grammar instruction
- name: Ukrainian Language Teaching Resources
  url: https://osvita.ua/
  type: reference
  notes: Common instructional language in educational materials
content_outline:
- section: 'Вступ: Розуміння освітнього процесу (Introduction: Understanding Educational Process)'
  words: 600
  points:
  - 'Importance of mastering instructional language for educational integration — aligns with State Standard §3.8: Organization
    of educational process (understanding lectures, seminars, and exams)'
  - 'Framing the shift to full immersion by decoding textbook structures: why recognizing visual patterns (bold text, tables,
    arrows) is the first step in comprehension'
  - Preparation for navigating B1-level materials where instructions are exclusively in Ukrainian
- section: Шаблони граматичних пояснень (Grammar Explanation Patterns)
  words: 850
  points:
  - 'High-frequency academic patterns: «X використовується, коли...» and «X означає...» — mapping typical definitions in standard
    textbooks'
  - 'Collocation focus: «часто використовується», «як правило використовується», «це не означає, що...»'
  - 'Visual literacy: Decoding the ''Grammar Box'' — identifying ''Rule'', ''Example'', and ''Exception'' layout patterns
    without needing translation'
  - 'Grammar-specific frequency: mastering the term «виняток» (exception) to navigate rules — highlighting the common learner
    error of using the Russian calque «виключення»'
- section: Словник інструкцій та дієслова завдань (Instruction Vocabulary and Activity Verbs)
  words: 900
  points:
  - 'Instructional commands: «порівняйте», «зверніть увагу», «виберіть», «знайдіть», «доповніть» — mapping the 80% rule: identifying
    the verb is 80% of understanding the task'
  - 'Common learner error: confusing «підкресліть» (underline) with «креслити» (draw/draft) — minimal pair drills to ensure
    task compliance'
  - 'The transition from general tasks to morphological ones: understanding «утворіть» (form/derive) vs «зробіть» (do/make)
    — referencing State Standard §4.3.4 on deriving nouns from verbs (читати – читання)'
  - 'Logical connectors in instructions: «наприклад», «тобто», «отже», «на відміну від»'
- section: Аналітична термінологія та контекст (Analytical Terminology and Context)
  words: 700
  points:
  - 'Mastering academic terminology: «контекст», «маркер», «частота», «аспектуальна пара» — building on b1-01 and b1-02 terminology'
  - 'Contextual clues: «зрозуміти з контексту», «широкий контекст» — strategies for dealing with unknown words in grammar
    rules'
  - 'Learner error warning: avoiding calques in grammar discussion — explicitly drilling «брати участь» (to participate) instead
    of the incorrect «приймати участь»'
- section: Стилістика та історія граматики (Stylistics and Grammar History)
  words: 650
  points:
  - 'Cultural hook: Meletius Smotrytsky (1619) — the author of ''Hrammatika Slavenska'' who established the terminology we
    use today (відмінок, дієслово) and separated the Locative case'
  - 'Distinguishing registers: «розмовна мова» vs «літературна мова» — aligns with State Standard §4.5.1 Stylistics'
  - 'Cultural hook: Ivan Ohiienko (Metropolitan Ilarion) and his ''Native Language Duties'' — the struggle for linguistic
    purity and standard language norms'
  - 'Word structure terms: «корінь», «префікс», «суфікс», «закінчення» — understanding the ''building blocks'' of Ukrainian
    words'
- section: Практика та підсумок (Practice and Summary)
  words: 300
  points:
  - 'Authentic text analysis: identifying instructions and explanation patterns in a sample text from a Ukrainian MON-approved
    textbook'
  - 'Readiness check: ensuring the learner can correctly identify 90% of task verbs to prepare for M04 Sentence Structure'
vocabulary_hints:
  required:
  - маркер (marker) — Analytical term
  recommended:
  - частота (frequency) — Academic usage
  - аспектуальна пара (aspectual pair) — Grammar-specific term
  - літературна мова (literary language) — Related to Ohiienko's standardization
  - розмовна мова (colloquial language) — Stylistic marker
  - відмінювання (declension/conjugation) — Smotrytsky's legacy
  - утворіть (form/derive) — Morphological instruction
activity_hints:
- type: mark-the-words
  focus: Find instruction patterns in grammar text
  items: 10+
- type: true-false
  focus: Statements about grammar patterns
  items: 10+
- type: fill-in
  focus: Complete grammar explanation passages
  items: 8+
- type: match-up
  focus: Activity instruction verb → example activity (виберіть → quiz question)
  items: 10+
- type: quiz
  focus: Identify analytical terms in grammar explanations (контекст, маркер, частота)
  items: 8+
- type: error-correction
  focus: Correct misused style/register terms in grammar explanations
  items: 6+
connects_to:
- b1-04 (Sentence structure)
- b1-05 (Metalanguage checkpoint)
prerequisites:
- b1-01 (Basic grammar terminology)
- b1-02 (Verb terminology)
persona:
  voice: Senior Language & Culture Specialist
  role: Law Student
grammar:
- Grammar explanation patterns
- Instruction vocabulary
- Word formation terms
module_type: bridge
immersion: 70-85% Ukrainian
register: нейтральний

```

**Level constraints quick-ref:**

```
# B1 Quick Reference

> This file supplements the build prompt. Do NOT repeat targets already injected
> via `4000`, `Bridge modules: teach grammar metalanguage. English scaffolding for abstract concepts. Parenthetical equivalents for new terms. Sentences max 30 words.`, etc.

## Grammar Scope

**Allowed:** All grammar constructions. Participles. Complex subordinate clauses.
Max 30 words per Ukrainian sentence. Max 4 clauses.

## Immersion Strategy (B1)

| Phase | Modules | Immersion | Notes |
|-------|---------|-----------|-------|
| B1.0 (Bridge) | M01-05 | Mixed | Teach grammar metalanguage; English scaffolding for abstract concepts |
| B1.1+ (Core) | M06-92 | **100%** | Full Ukrainian. English ONLY in vocabulary table translations |

**B1.0 Bridge modules:** English grammar term explanations allowed as transition from A2.

**B1.1+ Hard rule:** No English in prose, titles, callouts, or explanations.
No English in parentheses to clarify Ukrainian concepts:
- Wrong: **поки** — дія на тлі іншої дії (While she was cooking...)
- Right: **поки** — дія на тлі іншої дії, тобто одночасні процеси

## B1-Specific Writing Notes

- Content quality: equal treatment for all items in a category (same depth, same format)
- Example variety: mix standalone, table, inline, dialogue — no 5+ consecutive examples in same format
- Tables must have narrative context (2+ sentences before and after)
- Parallel sections use identical internal structure

```

Read the State Standard compliance mapping (small file — read this FIRST):

```
docs/l2-uk-en/state-standard-2024-mapping.yaml
```

The full State Standard 2024 is at `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt` (431KB, ~6000 lines). **Do NOT read the entire file.** Instead:
1. Check the mapping file for the relevant `B1` section — find the grammar topic that matches your module
2. Use the `lines: [start, end]` coordinates to read ONLY that section from the full Standard
3. If no mapping entry exists for this topic, search by §number or keyword as fallback
4. If still no match, say so honestly — do NOT fabricate a §reference

---

## PART 1: Lightweight Research

Research **Читаємо граматичні правила** for the **B1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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
- **Word count**: minimum **4000** words — allocate outline sections accordingly
- **Colonial framing**: plan decolonized framing NOW so Phase B doesn't default to Russian comparisons
- **Russianisms**: ensure vocabulary_hints and examples avoid banned words (кушати→їсти, получати→отримувати)
- **Duplicate headers**: ensure outline section names don't share keywords

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

### Output Block 1: Research Notes

```
===RESEARCH_START===

# Дослідження: Читаємо граматичні правила

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
