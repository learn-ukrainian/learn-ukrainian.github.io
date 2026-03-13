# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-062
level: A2
sequence: 62
slug: practical-warm-up
version: '2.0'
title: Practical Warm-up
subtitle: Getting Ready for Action
focus: practical
pedagogy: PPP
phase: A2.6 [Practical]
word_target: 2000
objectives:
- Learner can understand main ideas in text
- Learner can answer questions about a text
- Learner can identify key vocabulary in context
- Learner can synthesize information
content_outline:
- section: 'Вступ (Introduction: Setting the Stage)'
  words: 275
  points:
  - 'Orientation to practical A2.6 competencies: setting expectations for understanding short texts (30-50 words) and monologues
    as per State Standard §1.1.1.2.'
  - 'Overview of the module''s mission: bridging theoretical knowledge with real-world application, focusing on strategies
    for understanding separate phrases and dialogue replies.'
- section: 'Навички читання: Скарби Книжкового Форуму (Reading Skills: Book Forum Treasures)'
  words: 475
  points:
  - 'Application of reading strategies (§1.2.1.4): skimming (оглядове читання) for main ideas and scanning (пошукове читання)
    for specific facts like names or dates.'
  - 'Cultural Hook: The Lviv Book Forum. Practice browsing book blurbs in a bookstore (книгарня) to identify the ''головна
    ідея'' without needing to know every individual word.'
  - 'Keyword identification: Extracting ''ключові слова'' from posters and public announcements to grasp the context of major
    cultural events.'
- section: 'Слухання та Говоріння: Активне сприйняття (Listening & Speaking: Active Perception)'
  words: 500
  points:
  - 'Listening for gist and factual information (§1.1.1.2): extracting simple data from clear, structured speech and responding
    with short, appropriate dialogue replies.'
  - 'Learner Error Clinic: Distinguishing between ''чути'' (passive physical hearing) and ''слухати'' (active, intentional
    listening). Drill: ''Я не слухав тебе уважно'' vs. ''Я не чув твого голосу''.'
  - 'Interactive exercise: Simulating a morning show dialogue where learners must identify specific facts and names mentioned
    by the host.'
- section: 'Письмо: Радіодиктант національної єдності (Writing: Radio Dictation of National Unity)'
  words: 475
  points:
  - 'Cultural Hook: The tradition of the Radio Dictation of National Unity held on Ukrainian Language Day. Discussion of how
    it unites Ukrainians worldwide through a shared writing task.'
  - 'Writing practice (§1.3.1.1): Transferring information from a heard text into simple written phrases. Focus on clarity
    and factual accuracy over complex syntax.'
  - 'Learner Error Clinic: ''питання'' (general issue/topic) vs. ''запитання'' (specific inquiry requiring an answer). Practice:
    ''важливе питання'' vs. ''ставити запитання вчителеві''.'
- section: Інтеграція та Підсумок (Integration & Summary)
  words: 275
  points:
  - 'Integration Task: A simulated mini-dictation based on the National Unity Day concept, requiring learners to listen, write,
    and then answer questions about the text.'
  - 'Synthesis of A2 skills: Reviewing strategies for skimming/scanning and active listening before progressing to high-stakes
    scenarios like medical care (Module A2-59).'
vocabulary_hints:
  required:
  - текст (text) — читати текст, розуміти текст, писати текст; high frequency in educational settings
  - питання (issue/question) — важливе питання, вирішити питання; refers to a topic or problem, not a specific inquiry
  - запитання (question to ask) — ставити запитання, відповідати на запитання; used for inquiries requiring a response
  - відповідь (answer) — правильна відповідь, дати відповідь; essential for dialogue interaction
  - розуміти (to understand) — я розумію, ти розумієш?; core verb for expressing comprehension
  - читати (to read) — читати книгу, оглядове читання; linked to the high value of reading culture in Ukraine
  - слухати (to listen) — слухати уважно, слухати музику; active process, often confused with the passive 'чути'
  - головний (main) — головна ідея, головний герой, головна інформація
  - деталь (detail) — шукати деталі, важлива деталь; used in scanning exercises
  recommended:
  - ідея (idea) — головна ідея; useful for summarizing skimming tasks
  - інформація (information) — шукати інформацію, передавати інформацію
  - ключовий (key) — ключове слово (keyword), ключова фраза
  - стратегія (strategy) — стратегія читання, стратегія слухання; academic/practical register
activity_hints:
- type: reading
  focus: Understand main ideas
  items: 15
- type: quiz
  focus: Listen for key information
  items: 10
- type: fill-in
  focus: Vocabulary in context
  items: 15
- type: quiz
  focus: Answer questions orally
  items: 10
connects_to:
- a2-59 (Medical Care)
prerequisites:
- a2-61 (Practical Intro)
persona:
  voice: Encouraging Cultural Guide
  role: Morning Show Host
grammar:
- Reading comprehension strategies
- Listening for gist and detail
- Vocabulary activation in context
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

Research **Practical Warm-up** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Practical Warm-up

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
