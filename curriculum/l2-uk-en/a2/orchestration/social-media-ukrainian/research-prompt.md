# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-070
level: A2
sequence: 70
slug: social-media-ukrainian
version: '2.0'
title: Social Media Ukrainian
subtitle: Digital Life
focus: practical
pedagogy: PPP
phase: A2.6 [Practical]
word_target: 2000
objectives:
- Learner can navigate Ukrainian social media interfaces
- Learner can write comments and posts
- Learner can understand digital slang
- Learner can manage profile settings
content_outline:
- section: Вступ (Introduction)
  words: 300
  points:
  - 'Alignment with State Standard §3.4: Navigating social networks (соціальні мережі) as a core leisure and information competency.'
  - 'The Telegram Phenomenon: Explaining why Telegram is the primary news source for 75% of Ukrainians and used daily by 90%;
    mention its role for air raid alerts and official government updates.'
  - 'Instagram as a Business Ecosystem: How Instagram often replaces traditional websites for Ukrainian micro-businesses;
    introduce the essential business phrase ''Пишіть у дірект'' (Write to DM).'
- section: Презентація (Presentation)
  words: 525
  points:
  - 'Core UI Vocabulary and False Friends: Distinguishing between ''сторінка'' (profile/page) and ''сайт'' (website); warn
    against the common error of calling a social media profile a ''сайт''.'
  - 'Navigating the Interface: Key UI elements like ''кнопка «Стежити»'' (Follow button), ''іконка серця'' (heart icon), and
    ''стрічка'' (feed).'
  - 'Grammar of Subscription: Drill the use of ''підписатися на...'' + Accusative case; contrast masculine inanimate ''на
    канал'' (no change) with feminine ''на сторінку'' (ending change to -у) to address common learner errors.'
  - 'Slang vs. Purism: Presenting standard slang like ''лайк'' alongside cultural/purist alternatives like ''вподобайка''
    (like) and ''світлина'' (photo) for stylistic depth.'
- section: Практика (Practice)
  words: 400
  points:
  - 'Digital Action Verbs: Drilling the conjugation and usage of ''постити'', ''лайкати'', and ''репостити'' in casual registers.'
  - 'Sharing and Posting: Practical application of ''поширити допис'' (share a post) versus ''поділитися з друзями'' (share
    with friends); practice phrases like ''знімати сторіз'' and ''кидати в сторіз''.'
  - 'Correcting Case Errors: Exercises focused on correctly using the Accusative case for subscription targets and the Prepositional
    case for platform locations (''в інстаграмі'', ''в телеграмі'').'
- section: Діалоги та Взаємодія (Dialogues & Interaction)
  words: 400
  points:
  - 'Telegram Register: Contextual dialogues for messaging friends versus interacting with official news channels and alerts.'
  - 'The Instagram Shopping Experience: A dialogue between a customer and a shop owner using ''Яка ціна?'', ''Пишіть у дірект'',
    and ''скиньте посилання''.'
  - 'Managing Engagement: Interacting with ''підписники'' (followers) in comments; discussing ''кількість підписників'' and
    ''накрутка''.'
- section: Розповідь та Підсумок (Narrative & Summary)
  words: 375
  points:
  - 'Narrative: A ''Day in Digital Ukraine'' — checking Telegram for news/alerts in the morning, posting a ''світлина'' to
    Instagram, and interacting with the community.'
  - 'Refining Digital Style: Summary of when to use casual slang (''лайк'') versus more formal or poetic terms (''вподобайка'',
    ''світлина'') to sound more natural.'
  - 'State Standard Check: Final review of competencies for managing profile settings and understanding digital notifications
    (''сповіщення'').'
vocabulary_hints:
  required:
  - 'лайк (like) — ставити лайк, збирати лайки; very high frequency internet slang; alt: вподобайка'
  - пост (post) — писати пост, новий пост, опублікувати пост; refers to any feed content
  - сторіз (stories) — знімати сторіз, кидати в сторіз, дивитися сторіз; dominates daily social media usage
  - підписник (follower) — мої підписники, кількість підписників; key term for influencer/business culture
  - підписатися (to subscribe/follow) — підписатися на канал, підписатися на сторінку; MUST use Accusative case
  - сторінка (page/profile) — твоя сторінка в інстаграмі; contrast with 'сайт' (false friend)
  - поширити (to share) — поширити допис; standard UI term for 'Share' action
  - дірект (direct/DM) — пишіть у дірект; essential for Ukrainian Instagram business communication
  recommended:
  - вподобайка (like) — purist alternative to 'лайк' increasingly seen in localized interfaces
  - світлина (photo) — poetic and elegant alternative to 'фото' or 'пост'
  - стрічка (feed) — гортати стрічку; the main social media feed
  - сповіщення (notification) — вмикати сповіщення; essential for app settings and Telegram alerts
  - посилання (link) — скинути посилання; standard for sharing web content
  - накрутка (boosting/faking) — накрутка підписників; buying fake engagement
  - 'профіль (profile) — learner error: often confused with ''сторінка'''
activity_hints:
- type: match-up
  focus: Social media vocabulary
  items: 25
- type: fill-in
  focus: Complete social media texts
  items: 15
- type: cloze
  focus: Write posts and comments
  items: 10
- type: match-up
  focus: Match actions to icons
  items: 15
connects_to:
- a2-71 (Texting and Messaging)
prerequisites:
- a2-69 (Asking for Directions)
- a2-55 (Technology and Media)
persona:
  voice: Encouraging Cultural Guide
  role: Community Manager
grammar:
- Internet slang (лайк, пост, сторіз)
- Verbs for digital actions (постити, лайкати)
- Commenting and messaging etiquette
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

Research **Social Media Ukrainian** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Social Media Ukrainian

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
