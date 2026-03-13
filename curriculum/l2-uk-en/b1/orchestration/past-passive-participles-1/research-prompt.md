# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b1-046
level: B1
sequence: 46
slug: past-passive-participles-1
version: '2.0'
title: Пасивні дієприкметники минулого часу I
subtitle: Past Passive Participles I (-ний/-тий)
focus: grammar
pedagogy: TTT
phase: B1.4a [Participles]
word_target: 4000
objectives:
- Learner can form past passive participles using -ний/-тий suffixes
- Learner can agree participles with nouns in gender, number, and case
- Learner can use passive participles attributively and predicatively
- Learner can explain suffix selection rules
content_outline:
- section: Вступ та вступний тест (Introduction and Entry Test)
  words: 500
  points:
  - Introduction to passive participles aligned with State Standard §4.2.3.1, defining them as verbal forms with adjectival
    properties (verbal adjectives).
  - 'Concept of ''passive'' meaning: focusing on the object being acted upon rather than the actor (Agent).'
  - Assessment of prior knowledge from b1-44 (Active Participles) to establish the transition from active to passive voice.
- section: 'Творення: Логіка суфіксів та Чергування (Formation: Suffix Logic and Alternations)'
  words: 950
  points:
  - 'Suffix selection logic: -ний (most common), -ений (stems ending in consonants), and -ти (monosyllabic stems + vowels
    like ''мити'' -> ''митий'').'
  - 'The Music of Language: Detailed focus on Euphony and Alternation patterns including [д//дж] (садити -> саджений) and
    [с//ш] (носити -> ношений).'
  - A decision tree approach for learners to choose the correct suffix based on the verb stem structure.
- section: Граматичне узгодження та типові помилки (Grammatical Agreement and Common Errors)
  words: 850
  points:
  - Agreement patterns in gender, number, and case with the noun; addressing the 'Agreement Failure' error (e.g., correcting
    'Лист написана' to 'Лист написаний').
  - 'The ''-мий'' Trap (Russian Interference): Explicitly debunking forms like ''любимий'' or ''відомий'' as passive participles,
    replacing them with ''улюблений'' or specific adjectives.'
  - Drills for identifying transitive verbs suitable for passive formation, avoiding reflexive participle errors like 'читаючася'.
- section: 'Синтаксис: Дієприкметниковий зворот та Агентність (Syntax: Participle Phrases and Agency)'
  words: 850
  points:
  - Introduction to the Participle Phrase (дієприкметниковий зворот) per State Standard §4.4.2 using examples like 'екскурсія,
    організована для учасників'.
  - 'The ''Agency Rule'' in spoken Ukrainian: Why ''Я написав'' is more natural than ''Книга написана мною'' and when to use
    passive for describing states.'
  - Word order effects in sentences with participles to shift focus toward the result or the object.
- section: 'Культурний контекст: Феномен «-но/-то» (Cultural Context: The ''-no/-to'' Phenomenon)'
  words: 550
  points:
  - The unique Ukrainian impersonal forms on -но/-то (зроблено, написано) as a derivative of passive participles that emphasize
    result without an agent.
  - 'Formal register focus: Utilizing ''виконаний'' in official contexts (виконане завдання, виконаний план, виконана обіцянка).'
  - Contrast between written/formal frequency of participles and their reduced usage in conversational 'immersion' Ukrainian.
- section: Підсумок та практичні поради (Summary and Practical Tips)
  words: 300
  points:
  - Practical memorization hacks for verb stems and the most high-frequency participles (зроблений, відкритий, закритий).
  - 'Final self-check checklist: Suffix check, Alternation check, Agreement check.'
vocabulary_hints:
  required:
  - написаний (written) — написана книга, написаний лист, написана картина; High frequency
  - прочитаний (read) — прочитана стаття, прочитане повідомлення; High frequency
  - зроблений (done/made) — зроблена робота, зроблений вибір, зроблено в Україні; Very High frequency
  - відкритий (opened) — відкриті двері, відкрите питання, відкритий урок; Very High frequency
  - закритий (closed) — закрите вікно, закрита тема, закритий клуб; Very High frequency
  - пасивний (passive) — граматичний термін
  - дієприкметник (participle) — граматичний термін
  - узгодження (agreement) — граматичний термін
  recommended:
  - виконаний (executed/fulfilled) — виконане завдання, виконаний план, виконана обіцянка; Formal register
  - улюблений (favorite) — often confused with 'любимий' (error); use for preference
  - саджений (planted) — example of [д//дж] alternation
  - ношений (worn) — example of [с//ш] alternation
  - перехідне дієслово (transitive verb) — context for formation
  - дієприкметниковий зворот (participle phrase) — syntactic construction
activity_hints:
- type: fill-in
  focus: Verb to passive participle
  items: 25
- type: fill-in
  focus: Complete with correct form
  items: 20
- type: fill-in
  focus: Match participle to noun
  items: 15
- type: error-correction
  focus: Fix agreement errors
  items: 10
connects_to:
- b1-47 (Past Passive Participles 2)
prerequisites:
- b1-45 (Активні дієприкметники та їхній стиль)
persona:
  voice: Senior Language & Culture Specialist
  role: Museum Archivist
grammar:
- Пасивні дієприкметники минулого часу
- Суфікси -ний/-тий selection
- Узгодження з іменником
register: розмовний

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

Research **Пасивні дієприкметники минулого часу I** for the **B1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Пасивні дієприкметники минулого часу I

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
