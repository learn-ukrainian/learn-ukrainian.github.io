# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-055
level: A2
sequence: 55
slug: technology-media
version: '2.0'
title: Technology and Media
subtitle: Digital World
focus: vocabulary
pedagogy: PPP
phase: A2.5 [Vocabulary Expansion]
word_target: 2000
objectives:
- Learner can talk about computers and phones
- Learner can describe internet activities
- Learner can use social media vocabulary
- Learner can discuss technology in daily life
content_outline:
- section: 'Вступ: Україна як IT-хаб (Introduction: Ukraine as an IT Hub)'
  words: 325
  points:
  - Introduction to Ukraine's digital landscape, highlighting the 'IT Nation' context with major hubs in Kyiv, Lviv, and Kharkiv.
  - 'Overview of basic terminology: the ubiquity of ''смартфон'' alongside the traditional ''телефон'' in daily communication.'
  - 'Aligning with State Standard §3.4: Discussing the role of the internet, press, and social media as essential components
    of modern leisure and daily life.'
- section: Цифровий словник та культура (Digital Vocabulary and Culture)
  words: 475
  points:
  - 'Essential hardware: ''комп''ютер'', ''ноутбук'', ''планшет'', and the importance of ''смартфон'' in the ''State in a
    smartphone'' philosophy.'
  - 'The ''Diia'' (Дія) phenomenon: Explaining how Ukraine became the first country to equate digital and physical passports,
    using it as a prime example for ''мобільний додаток''.'
  - 'Internet basics: ''вебсайт'', ''посилання'', and ''пароль''. Highlighting the importance of a ''надійний пароль'' (reliable
    password) in a digital-first society.'
- section: Граматичні пастки та вибір слів (Grammatical Traps and Word Choice)
  words: 400
  points:
  - 'Addressing the common prepositional error: Correcting the English calque ''на інтернеті'' to the proper Locative form
    ''в інтернеті''.'
  - 'Standard vs. Colloquial: Guiding learners to prefer ''завантажити'' (download) over the colloquial/Russian-influenced
    ''скачати''.'
  - 'Case governance with tech brands: Mastering the Locative case for search engines — ''шукати в ґуґлі'' (declined) vs.
    ''шукати в Google'' (original).'
  - 'Directional verbs: Distinguishing between ''завантажити'' (download) and the actions of ''викласти'' or ''опублікувати''
    (upload/post).'
- section: 'Практика: Життя в мережі (Practice: Life Online)'
  words: 475
  points:
  - 'Remote work dialogues: Using collocations like ''надіслати посилання'' and ''перейти за посиланням'' in a professional
    context, building on a2-49 (Work and Professions).'
  - 'The Digital Grandma scenario: A narrative about teaching an older relative to use ''Дія'' for state services, practicing
    ''встановити додаток'' and ''ввести пароль''.'
  - 'Social media storytelling: Describing the process of becoming a blogger, using ''соціальна мережа'', ''підписка'', and
    ''оновлення''.'
- section: Підсумок та поради (Summary and Tips)
  words: 325
  points:
  - Review of key tech collocations and their frequency, emphasizing the transition to more advanced social media topics in
    a2-67.
  - 'Final check on register: ensuring the use of ''розмовний'' (conversational) style for digital interactions.'
  - 'Self-reflection: Learners describe their most-used ''додатки'' and digital habits in Ukrainian.'
vocabulary_hints:
  required:
  - комп'ютер (computer) — High frequency; essential office/home equipment
  - телефон (phone) — High frequency; used interchangeably with 'смартфон' in modern contexts
  - 'інтернет (internet) — High frequency; collocations: ''в інтернеті'' (Locative), ''доступ до інтернету'', ''безлімітний
    інтернет'''
  - 'сайт (website) — High frequency; collocations: ''вебсайт'', ''офіційний сайт'', ''зайти на сайт'''
  - пошта (email) — Essential for 'remote work' contexts
  - 'завантажити (to download) — Standard Ukrainian; prefer over ''скачати''. Collocations: ''завантажити файл'', ''завантажити
    додаток'''
  - відправити (to send) — Basic verb for digital communication (emails, messages)
  - 'шукати (to search) — Key collocation: ''шукати в ґуґлі'' (Locative) or ''шукати в Google'''
  recommended:
  - 'додаток (app) — High frequency (tech context); collocations: ''мобільний додаток'', ''встановити додаток''. Cultural
    hook: ''Дія'''
  - 'пароль (password) — Medium frequency; collocations: ''ввести пароль'', ''забути пароль'', ''надійний пароль'''
  - акаунт (account) — Common loanword in digital contexts
  - оновлення (update) — Essential for describing software/app maintenance
  - підписка (subscription) — Relevant for social media and media services
  - 'мережа (network) — High frequency; collocations: ''соціальна мережа'', ''у мережі'' (online), ''немає мережі'''
  - 'посилання (link) — Medium frequency; collocations: ''активне посилання'', ''надіслати посилання'', ''перейти за посиланням'''
activity_hints:
- type: match-up
  focus: Technology terms
  items: 30
- type: match-up
  focus: Match actions to devices
  items: 20
- type: fill-in
  focus: Complete tech descriptions
  items: 15
- type: cloze
  focus: Tech support conversation
  items: 8
connects_to:
- a2-56 (Hobbies and Leisure)
- a2-70 (Social Media Ukrainian)
prerequisites:
- a2-54 (Work and Professions)
persona:
  voice: Encouraging Cultural Guide
  role: Tech Blogger
grammar:
- Technology verbs (завантажити, відправити)
- Internet vocabulary
- Social media and digital terms
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

Research **Technology and Media** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Technology and Media

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
