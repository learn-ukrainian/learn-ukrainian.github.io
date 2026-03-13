# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b1-057
level: B1
sequence: 57
slug: word-formation-modifiers
version: '2.0'
title: Словотвір прикметників та прислівників
subtitle: Adjective & Adverb Word Formation
focus: grammar
pedagogy: PPP
phase: B1.7 [Word Formation and Lexicology]
word_target: 4000
objectives:
- Learner can form adjectives using productive Ukrainian suffixes
- Learner can use adjective prefixes for negation and intensity
- Learner can form adverbs from adjectives and nouns
- Learner can analyze word formation of unknown modifiers
content_outline:
- section: 'Вступ: Від іменника до прикметника (Introduction: From Noun to Adjective)'
  words: 500
  points:
  - 'State Standard §4.3.6-7: adjective and adverb formation'
  - How productive word formation expands descriptive vocabulary exponentially
  - 'Preview: suffixation as the primary mechanism for both adjectives and adverbs'
- section: Суфіксальний словотвір прикметників (Adjective Suffixation)
  words: 800
  points:
  - 'Relational adjectives: -н- (книжний), -ськ- (київський, козацький), -ів-/-їв- (батьківський)'
  - 'Qualitative adjectives: -ист- (барвистий), -уват- (синюватий), -еньк- (маленький)'
  - 'Material adjectives: -ян- (дерев''яний), -ов- (шовковий)'
  - 'From verbs: -овит- (працьовитий), -лив- (дбайливий), -н- (написаний — not just participle!)'
  - 'Key alternations in formation: к→ч (козак→козацький), г→ж (Прага→празький)'
- section: Префіксальний словотвір прикметників (Adjective Prefixation)
  words: 700
  points:
  - 'Negation: не- (неможливий, незалежний) — most productive'
  - 'Intensity: пре- (прекрасний), над- (надзвичайний), за- (завеликий)'
  - 'Composition: prefix+suffix simultaneously: без-+(-н-) (безмежний), між-+(-н-) (міжнародний)'
  - 'Cultural note: незалежний (independent) — from залежний, the most important не- word in modern Ukraine'
- section: Складні прикметники (Compound Adjectives)
  words: 600
  points:
  - 'Equal components: жовто-блакитний, сільськогосподарський'
  - 'Subordinate: давньоруський, давньоукраїнський'
  - 'Hyphenation rules: colors (жовто-гарячий), cardinal directions (південно-західний)'
  - 'From numerals: стодесятий, двадцятирічний'
- section: Словотвір прислівників (Adverb Word Formation)
  words: 800
  points:
  - 'From adjectives: -о/-е (добре, гарно, швидко) — most productive pattern'
  - 'From adjectives: -и (по-українськи, по-новому) — manner adverbs'
  - 'From nouns: вранці (від ранок), взимку (від зима), угорі (від гора)'
  - 'Prefix adverbs: на- (надворі, нагорі), по- (повсюди, помалу)'
  - 'Compound adverbs: мимохідь, мимоволі, спохвату'
  - 'Learner error: по-українськи vs *по українському'
- section: 'Практика: Словотвірний аналіз (Practice: Word Formation Analysis)'
  words: 600
  points:
  - Decompose adjectives/adverbs into morphemes
  - Form adjectives from nouns using correct suffix
  - Form adverbs from adjectives
  - 'Reading: spot word formation patterns in authentic text'
  - 'Creative: describe a scene using maximum derived vocabulary'
vocabulary_hints:
  required:
  - словотвір (word formation) — словотвір прикметників; core term
  - прикметник (adjective) — якісний/відносний прикметник
  - прислівник (adverb) — прислівник способу дії, часу, місця
  - суфікс (suffix) — словотвірний суфікс прикметника
  - якісний (qualitative) — якісний прикметник (describes quality)
  - відносний (relational) — відносний прикметник (describes relation/material)
  recommended:
  - складний (compound) — складний прикметник; compound adjective
  - ступінь (degree) — ступінь порівняння
  - продуктивний (productive) — продуктивна модель словотвору
  - чергування (alternation) — к→ч, г→ж in adjective formation
  - дефіс (hyphen) — через дефіс; hyphenation rules
activity_hints:
- type: fill-in
  focus: Form adjectives from nouns/verbs
  items: 20
- type: quiz
  focus: Identify formation type of adjective
  items: 12
- type: fill-in
  focus: Form adverbs from adjectives
  items: 15
- type: match-up
  focus: Match suffix to meaning (relational, qualitative, material)
  items: 12
connects_to:
- 'b1-58 (Synonymy: Thinking Verbs)'
prerequisites:
- 'b1-56 (Word Formation: Nouns)'
persona:
  voice: Senior Language & Culture Specialist
  role: Linguistic Researcher
grammar:
- Adjective suffixation (-н-, -ськ-, -ів-, -ист-, -уват-, -еньк-)
- Adjective prefixation (не-, пре-, над-, за-, без-)
- Compound adjectives (складні прикметники)
- Adverb formation (-о/-е, -и, prefix patterns)
register: нейтральний
immersion: 75-100% Ukrainian

```

**Level constraints quick-ref:**

```
# B1 Quick Reference

> This file supplements the build prompt. Do NOT repeat targets already injected
> via `4000`, `Full Ukrainian immersion. Grammar explained IN Ukrainian. English only for disambiguation of false friends. Sentences max 30 words.`, etc.

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

Research **Словотвір прикметників та прислівників** for the **B1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Словотвір прикметників та прислівників

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
