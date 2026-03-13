# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-066
level: A2
sequence: 66
slug: scheduling-appointments
version: '2.0'
title: Scheduling Appointments
subtitle: Making and Changing Plans
focus: practical
pedagogy: PPP
phase: A2.6 [Practical]
word_target: 2000
objectives:
- Learner can make an appointment by phone
- Learner can reschedule or cancel a meeting
- Learner can understand appointment details
- Learner can use polite phrases for scheduling
content_outline:
- section: Вступ (Introduction)
  words: 300
  points:
  - 'The ''Academic Quarter'' hook: Cultural norms of social lateness (5-10 minutes) vs. strict business and medical punctuality
    in Ukraine.'
  - 'The Messenger Revolution: Explaining the dominance of Viber, Telegram, and WhatsApp for booking appointments over traditional
    voice calls; ''Check your Viber'' as a standard confirmation phrase.'
  - 'Clock Systems: Distinguishing the 24-hour clock for official schedules (15:00) vs. the 12-hour clock for colloquial speech
    (третя година дня).'
- section: Презентація (Presentation)
  words: 550
  points:
  - 'Service vs. Social: Distinguish «записатися на...» (booking a service/appointment) from «домовитися про зустріч» (arranging
    a hangout/meeting).'
  - 'Collocations for booking: записатися на прийом (doctor), записатися на стрижку (haircut), записатися на манікюр.'
  - 'The ''Half Past'' Logic: Explaining the linguistic structure of ''half on the next hour'' (e.g., «пів на четверту» is
    3:30, not 4:30) to prevent common chronological errors.'
  - 'Polite Phone Etiquette: Standard phrases for opening and closing a scheduling call or message.'
- section: Практика (Practice)
  words: 425
  points:
  - 'Time Prepositions Drill: Distinguishing «о котрій?» (at what time? - Locative) vs. «на котру?» (for what time/deadline?
    - Accusative) with specific correction for common errors like ''Я прийду на п''яту'' when meaning ''at 5:00''.'
  - 'App Interface Immersion: Using realistic Ukrainian terms found in booking apps (календар, вільне місце, підтвердити,
    деталі запису).'
  - 'Verb Contrast: Drill distinguishing «зустріти» (to meet/greet someone arriving) from «зустрітися з» (to meet with someone
    for an appointment).'
- section: Діалоги (Dialogues)
  words: 400
  points:
  - 'Formal Scenario: Scheduling a doctor''s appointment (записатися до лікаря) using strict 24-hour time and checking availability
    («вільні місця»).'
  - 'Informal Scenario: Rescheduling a coffee meetup via messenger, using «перенести» and discussing the ''academic quarter''
    for arrival time.'
  - 'State Standard §1.1.2.1.1 practice: Producing and understanding messages for changing or canceling meeting times.'
- section: Розповідь (Narrative)
  words: 225
  points:
  - 'Narrative arc involving a character navigating multiple appointments: booking a haircut, confirming via Viber, and having
    to reschedule a business meeting («перенести на іншу годину»).'
  - Integrating 'half past' logic within the story to test comprehension of 3:30 vs 4:30.
- section: Підсумок (Summary)
  words: 100
  points:
  - Review of key collocations and the locative vs. accusative time distinction.
  - Self-assessment checklist for State Standard §1.1.2.1.1 competencies (inviting, changing, canceling).
vocabulary_hints:
  required:
  - записатися (to book/sign up) — записатися на прийом (appointment), записатися до лікаря (to the doctor); implies a formal
    service context
  - 'зустріч (meeting) — призначити зустріч (schedule), перенести зустріч (reschedule), скасувати зустріч (cancel); note learner
    error: зустріти vs зустрітися з'
  - вільний (free/available) — ви вільні? (are you free?), вільне місце (free spot/slot), вільний час (free time)
  - зайнятий (busy) — я зайнятий, лінія зайнята; used for both people and phone lines
  - перенести (to move/reschedule) — перенести на завтра, перенести на іншу годину; high frequency in administrative contexts
  - скасувати (to cancel) — скасувати запис, скасувати зустріч
  - підтвердити (to confirm) — підтвердити запис, повідомлення для підтвердження
  - о котрій? (at what time?) — uses Locative case (о п'ятій); used for specific point in time
  - на котру? (for what time?) — uses Accusative case (на п'яту); used for booking slots or deadlines
  recommended:
  - прийом (appointment/reception) — бути на прийомі, години прийому
  - пів на... (half past...) — e.g., пів на четверту (3:30); requires Genitive of the next hour's ordinal
  - нагадування (reminder) — отримати нагадування в Телеграмі
  - запізнення (lateness) — без запізнень (without delay), невелике запізнення
  - раніше / пізніше (earlier / later)
  - домовитися (to arrange/agree) — домовитися про зустріч, домовитися про час
activity_hints:
- type: match-up
  focus: Phone appointment calls
  items: 25
- type: quiz
  focus: Schedule and reschedule
  items: 10
connects_to:
- a2-67 (Scheduling Interviews)
- a2-59 (Medical Care)
prerequisites:
- a2-65 (Rental Accommodation)
persona:
  voice: Encouraging Cultural Guide
  role: Administrative Assistant
grammar:
- Making appointments (записатися на)
- Rescheduling and canceling
- Polite phone etiquette
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

Research **Scheduling Appointments** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Scheduling Appointments

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
