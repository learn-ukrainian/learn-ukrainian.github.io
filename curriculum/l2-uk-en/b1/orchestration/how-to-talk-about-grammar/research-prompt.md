# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b1-001
level: B1
sequence: 1
slug: how-to-talk-about-grammar
version: '3.0'
title: Як говорити про граматику
subtitle: Learning grammar terminology in Ukrainian
focus: integration
pedagogy: PPP
phase: B1.0 Bridge
word_target: 4000
objectives:
- Learner can identify parts of speech using Ukrainian terminology
- Learner can name all seven grammatical cases in Ukrainian
- Learner can describe basic sentence elements using Ukrainian terms
sources:
- name: Ukrainian State Standard 2024 - Grammar Terminology
  url: https://mon.gov.ua/
  type: reference
  notes: Official metalanguage terms for Ukrainian grammar education
- name: Ukrainian Grammar (Wikipedia)
  url: https://uk.wikipedia.org/wiki/Граматика_української_мови
  type: reference
  notes: Overview of Ukrainian grammatical terminology
content_outline:
- section: 'Вступ: Сила метамови (Introduction: The Power of Metalanguage)'
  words: 500
  points:
  - English scaffolding (bridge module) explaining the transition to 70-85% immersion and why learning grammar in Ukrainian
    is essential for B1+ success.
  - 'The ''Linguistics Professor'' persona introduction: grammar as a powerful tool for decolonization and precision, not
    just a set of rules.'
  - 'Historical Hook: Meletiy Smotrytskyi and his ''Grammar'' (1619). Discuss how his terminology established the foundation
    for modern Ukrainian linguistic systematicity.'
  - 'Alignment with State Standard §4.2.1: Defining ''метамова'' (metalanguage) and ''термін'' (term) as prerequisites for
    morphological competence.'
- section: Самостійні частини мови (Independent Parts of Speech)
  words: 1000
  points:
  - 'Comprehensive breakdown of the six independent categories: іменник, дієслово, прикметник, прислівник, займенник, числівник.'
  - Each category features an H3 with definition, questions (Хто? Що? Що робити?), and frequency-based collocations like 'рід
    іменника' or 'час дієслова'.
  - 'Linguistic Depth: Explicit instruction on ''вид дієслова'' (aspect) and ''відміна іменника'' (declension group) as required
    for B1 state standards.'
  - 'Addressing Learner Error (Gender): Clarifying that ''рід іменника'' is determined by word endings (стіл - він, шафа -
    вона), not the physical sex of the object.'
- section: Службові частини мови та культурна лінза (Service Parts of Speech and Cultural Lens)
  words: 600
  points:
  - Functional roles of сполучник (conjunction), прийменник (preposition), частка (particle), and вигук (interjection) in
    sentence construction.
  - 'Cultural Hook: The letter ''Ґ'' as a symbol of systematicity. Discuss its repression in 1933 and restoration in the 1990s
    as part of returning historical truth to grammar.'
  - Distinction between 'просте речення' (simple sentence) and 'складне речення' (complex sentence) using service words as
    structural glue.
- section: 'Сім ключів: Відмінки та їхні ролі (Seven Keys: Cases and Their Roles)'
  words: 1000
  points:
  - Detailed presentation of all 7 cases (називний, родовий, давальний, знахідний, орудний, місцевий, кличний) with questions
    and primary semantic roles.
  - 'Mnemonic Aid: Integration of ''На Різдво Дід Загубив Горішки Між Ковбасками'' for memorizing the standard Ukrainian case
    order.'
  - 'Addressing Learner Error (Accusative vs Genitive): Specific drill on ''Бачу брата'' (Acc) vs ''Немає брата'' (Gen) to
    clear confusion with animate nouns.'
  - 'The Vocative Mandate: Emphasizing the cultural importance of ''кличний відмінок'' (e.g., ''Привіт, Андрію!'') as a marker
    of authentic Ukrainian address.'
- section: Граматичні категорії та будова слова (Grammatical Categories and Word Structure)
  words: 600
  points:
  - 'Morphemics breakdown: identification of ''корінь'' (root), ''префікс'' (prefix), ''суфікс'' (suffix), and ''закінчення''
    (ending) for vocabulary decoding.'
  - 'Overview of categories: рід (gender), число (number), особа (person), час (tense), and вид (aspect) with 2+ examples
    for each.'
  - 'Syntactic Roles: Introduction to ''підмет'' (subject), ''присудок'' (predicate), ''додаток'' (object), ''означення''
    (attribute), and ''обставина'' (adverbial) in Ukrainian.'
- section: Практика та підсумок (Practice and Summary)
  words: 300
  points:
  - 'Teacher-student dialogue simulation: ''Яка це частина мови?'' and ''У якому відмінку це слово?'' to normalize classroom
    metalanguage.'
  - Recognition drill using authentic quotes from Shevchenko or Lesya Ukrainka to identify parts of speech and case forms
    in context.
  - Self-assessment checklist for M02 readiness, ensuring the learner can name all 7 cases and 10 parts of speech without
    English prompts.
vocabulary_hints:
  required:
  - іменник (noun) — рід іменника (gender of a noun), відміна іменника (declension of a noun); High frequency.
  - дієслово (verb) — час дієслова (verb tense), вид дієслова (verb aspect); High frequency.
  - відмінок (case) — називний відмінок (nominative case), відмінювання (declension); Essential terminology.
  - прикметник (adjective) — узгодження з іменником (agreement with noun).
  - прислівник (adverb) — незмінна частина мови (invariable part of speech).
  - займенник (pronoun) — особовий займенник (personal pronoun).
  - числівник (numeral) — кількісний та порядковий (cardinal and ordinal).
  - називний відмінок (nominative case) — Хто? Що?
  - родовий відмінок (genitive case) — Кого? Чого?
  - давальний відмінок (dative case) — Кому? Чому?
  - знахідний відмінок (accusative case) — Кого? Що?
  - орудний відмінок (instrumental case) — Ким? Чим?
  - місцевий відмінок (locative case) — На кому? На чому?
  - кличний відмінок (vocative case) — Звертання (addressing someone).
  recommended:
  - речення (sentence) — просте речення (simple sentence), складати речення (to form a sentence).
  - правило (rule) — граматичне правило (grammar rule), за правилом (according to the rule).
  - приклад (example) — наводити приклад (to provide an example).
  - метамова (metalanguage) — термінологічний апарат (terminological apparatus).
  - підмет (subject) — головний член речення (main member of the sentence).
  - присудок (predicate) — що робить підмет? (what the subject does).
  - сполучник (conjunction) — єднальний сполучник (connecting conjunction).
  - прийменник (preposition) — уживання з відмінками (usage with cases).
  - частка (particle) — модальна частка (modal particle).
  - вигук (interjection) — емоційне забарвлення (emotional coloring).
activity_hints:
- type: match-up
  focus: Ukrainian term → English equivalent
  items: 12+
- type: quiz
  focus: Identify part of speech by Ukrainian name
  items: 10+
- type: fill-in
  focus: Complete sentences about grammar using Ukrainian terms
  items: 8+
- type: error-correction
  focus: Fix common metalanguage mistakes
  items: 8+
connects_to:
- b1-02 (Verb-specific terminology)
- b1-03 (Reading grammar rules)
- b1-05 (Metalanguage checkpoint)
prerequisites:
- A2 completion required
- Familiarity with all 7 cases (conceptually)
- Basic understanding of grammar concepts
persona:
  voice: Senior Language & Culture Specialist
  role: Linguistics Professor
grammar:
- Parts of speech names in Ukrainian
- Case names in Ukrainian
- Basic sentence structure terms
immersion: 70-85% Ukrainian
module_type: bridge
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

Research **Як говорити про граматику** for the **B1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Як говорити про граматику

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
