# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-071
level: A2
sequence: 71
slug: texting-messaging
version: '2.0'
title: Texting and Messaging
subtitle: Chatting with Friends
focus: practical
pedagogy: PPP
phase: A2.6 [Practical]
word_target: 2000
objectives:
- Learner can send and receive text messages
- Learner can use common abbreviations
- Learner can understand informal chat language
- Learner can arrange meetings via text
content_outline:
- section: Вступ (Introduction)
  words: 325
  points:
  - 'Digital etiquette in Ukraine: the ''Don''t Call'' rule (Краще напиши) and the phenomenon of ''telefonophobia''—intrusive
    calls vs. the courtesy of texting first.'
  - The dominance of Telegram in Ukrainian life (81% usage for communication); its role as the de facto standard for personal
    messages, news consumption, and work.
- section: Презентація (Presentation)
  words: 475
  points:
  - 'Distinguishing digital verbs: ''писати'' (to write/text) vs. ''дзвонити'' (to call)—emphasizing ''Напиши мені'' as the
    standard phrase for inviting messaging.'
  - 'Core texting abbreviations: ''прив'' (hi), ''дяк'' (thanks), and ''норм'' (fine); addressing the Russianism error ''спс''
    and replacing it with the authentic ''дяк'' or ''дякую''.'
  - Introducing 'бдлск' (будь ласка) as a high-frequency functional abbreviation for polite requests in informal chats.
- section: Практика (Practice)
  words: 400
  points:
  - 'Drilling the Vocative case in digital communication: reinforcing that names require the vocative even in informal chats
    (e.g., ''Привіт, Андрію''); correcting the common error of dropping the vocative due to perceived informality.'
  - 'Functional phrases for media sharing: ''надіслати фото'', ''скинути файл'', and ''отримати повідомлення''—standard collocations
    aligned with State Standard §3.4.'
- section: Діалоги (Dialogues)
  words: 400
  points:
  - 'The polarizing culture of ''голосове'' (voice messages): vocabulary for sending/receiving audio clips and navigating
    the social etiquette of voice-messaging.'
  - 'Sticker culture in Ukraine: using meme-based packs featuring historical figures like Shevchenko or heroes like Patron
    the Dog; the collocation ''кинути стікер'' for reactive messaging.'
- section: Розповідь (Narrative)
  words: 275
  points:
  - 'A narrative journey through a typical Telegram feed: checking a news channel, responding to a friend using abbreviations,
    and forwarding (''пересилати'') an interesting link.'
- section: Підсумок (Summary)
  words: 125
  points:
  - 'Summary of digital competencies: recap of abbreviations, vocative usage in chats, and navigating the messaging landscape.'
  - Self-check on 'писати' vs 'дзвонити' usage and distinguishing between close-friend slang and general informal language.
vocabulary_hints:
  required:
  - повідомлення (message) — надіслати ~, отримати ~, голосове ~; high frequency standard term
  - надіслати (to send) — ~ фото, ~ файл, ~ смайлик; standard verb for digital actions
  - отримати (to receive) — standard pair with надіслати for messages and media
  - прив (hi) — standalone greeting for close friends; informal abbreviation
  - дяк (thanks) — informal; explicitly use instead of Russian 'спс' to maintain Ukrainian identity
  - чат (chat) — груповий ~, створити ~; essential for Telegram/Viber context
  - смайлик (emoji) — надіслати ~; common informal term for emoticons
  - голосове (voice message) — huge part of Ukrainian culture; often polarizing (love/hate)
  recommended:
  - норм (fine/okay) — high frequency reply to 'Як ти?' in chats
  - прикольно (cool) — common reaction to stories or funny messages
  - круто (awesome) — high-intensity positive reaction
  - стікер (sticker) — набір стікерів, кинути ~; cultural phenomenon (Patron, Shevchenko stickers)
  - пересилати (to forward) — to forward a message to another chat or channel
  - 'видалити (to delete) — digital hygiene: delete for everyone vs just for me'
  - бдлск (please) — abbreviation of 'будь ласка'; common in informal typing
activity_hints:
- type: match-up
  focus: Texting vocabulary
  items: 25
- type: fill-in
  focus: Complete text messages
  items: 15
- type: cloze
  focus: Write text conversations
  items: 10
- type: match-up
  focus: Match abbreviations to meanings
  items: 15
connects_to:
- a2-72 (Online Services)
prerequisites:
- a2-70 (Social Media Ukrainian)
persona:
  voice: Encouraging Cultural Guide
  role: Digital Native
grammar:
- Text abbreviations (прив, дяк, норм)
- Informal syntax in chats
- Polite vs informal messaging
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

Research **Texting and Messaging** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Texting and Messaging

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
