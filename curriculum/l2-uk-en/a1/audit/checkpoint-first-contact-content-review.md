# Content Review: checkpoint-first-contact
**Track:** a1 | **Sequence:** 14
**Mode:** core
**Tier:** 1-beginner
**Pipeline:** PASS (words: 1179 raw/1338 section-sum, target: 1200)
**Verdict:** B

## Plan Adherence

The plan and content are significantly misaligned due to a stale plan that references forbidden grammar:

| Plan Objective | Status | Notes |
|----------------|--------|-------|
| Demonstrate Cyrillic reading fluency | COVERED | Section 1 covers И vs I, minimal pairs, reading without transliteration |
| Identify noun gender by word ending | COVERED | Section 1 covers gender rules, exceptions (тато) |
| Conjugate First Conjugation verbs correctly | SKIPPED (correctly) | Plan objective contradicts sequence constraints (verbs FORBIDDEN until M15). Content correctly omits this. |
| Form questions and negative statements | COVERED | Section 2 covers Хто/Що/Де, Так/Ні, negation with не |

**Section alignment:**
- Plan section "Навичка 2: Дієслова та Питання" was correctly reinterpreted as "Прикметники та Питання" in content
- Plan section "Інтеграційне завдання" (180 words) was replaced with "Підсумок" (150 words) -- acceptable for a checkpoint
- All 5 meta outline sections present and covered

**Vocabulary coverage:** Only 10/20 vocabulary items appear in content+activities. The 10 missing items are primarily verbs (читати, писати, говорити, знати, розуміти, питати, відповідати, перевіряти) which the module correctly cannot use per sequence constraints. This is a plan defect, not a content defect.

## Linguistic Accuracy

All 124 Ukrainian words verified against VESUM (100% pass rate). No ghost words, no Russianisms, no Russian characters detected.

Specific checks:
- **київський** -- verified, correct adjective form
- **олівець** -- verified, correct noun
- **вулиця** -- verified, correct noun
- **Stress marks** -- consistently applied using combining acute accent (correct typography)
- **Euphony** -- no obvious violations found
- **No IPA or Latin transliteration** -- clean

Minor note: The word **ки́ївський** has the stress on the first syllable, which is correct (ки́їв -> ки́ївський).

## Pedagogical Quality

**Lesson arc:** WELCOME (warm greeting from hostel host) -> PREVIEW (what we'll review) -> PRESENT (rules + examples) -> PRACTICE (tables, examples, dialogues) -> CELEBRATE (summary with self-check) -- follows the beginner arc well.

**Strengths:**
- Clear progression from reading -> gender -> adjectives -> questions -> cultural application
- Tables used effectively for vocabulary presentation and dialogue examples
- Ukrainian sentences kept short (under 10 words) with immediate English translations
- The И vs I minimal pair explanation is concrete and memorable
- Cultural cafe section integrates grammar (nominal sentences) with real-world context
- Self-check questions in summary are well-targeted

**Weaknesses:**
- The Ukrainian immersion sentences at the start of each section follow a repetitive pattern: "Це дуже [adjective]." / "Це [noun]." This creates a mechanical feel. The template says to vary immersion patterns, but these are quite samey.
- Cognitive load is well-managed but the adjective agreement section moves quickly from singular to plural with only one example table.

**"Would I Continue?" Test:** 4/5
- Overwhelmed? No -- pacing is comfortable
- Instructions clear? Yes -- always knew what to do
- Quick wins? Yes -- early recognition of И/I distinction
- Ukrainian scary? No -- English scaffolding present throughout
- Come back tomorrow? Mostly yes, but the Модель/Практика/Самоперевірка sub-structure creates slight confusion (H3 headings in Ukrainian without explanation of what these subsections mean)

## Activities Quality

**8 activities total** across 7 types (true-false, group-sort, match-up x2, anagram, quiz x2, fill-in). Good variety.

**Schema compliance:** All activities use allowed types. No forbidden types. Bare list at root (correct).

**Item counts:**
| Activity | Type | Items | Min | Status |
|----------|------|-------|-----|--------|
| True or False | true-false | 8 | 8 | PASS |
| Sort Nouns by Gender | group-sort | 8 | 8 | PASS |
| Match the Phrase | match-up | 9 | 8 | PASS |
| Unscramble | anagram | 8 | 8 | PASS |
| Adjective Agreement Quiz | quiz | 8 | 8 | PASS |
| Complete the Sentence | fill-in | 8 | 8 | PASS |
| Grammar Review Quiz | quiz | 8 | 8 | PASS |
| Match Plurals and Concepts | match-up | 9 | 8 | PASS |

**Quality issues:**
- MEDIUM: True-false item 2 says "The Ukrainian letter И sounds exactly like English H." This conflates the visual appearance issue (Н looks like H) with the sound issue (И sounds like short i). The statement is false, but the explanation ("It looks like an H but sounds like the short 'i' in 'bit'") conflates И with Н. И does NOT look like H -- that is Н. The item should be rewritten.
- LOW: Match-up 1 pair "Це велика кава" -> "This is big coffee" -- "big coffee" is unnatural in English. "Large coffee" would be more idiomatic, though this is minor for A1.
- LOW: Anagram items use lowercase for scrambled but uppercase/lowercase inconsistently for answers (mostly lowercase, which is fine).

**Language testing vs content testing:** Activities appropriately test language skills (gender identification, adjective agreement, question formation) rather than content recall. Passes rule 10.

## Engagement

4 callout boxes across 4 different types:
1. `[!note]` -- explains why reviewing patterns matters (line 27)
2. `[!warning]` -- И vs I visual trap (line 58)
3. `[!tip]` -- intonation for yes/no questions (line 115)
4. `[!culture]` -- Смачного etiquette (line 149)

Exceeds minimum of 2 for A1. Good distribution across sections.

**Tables:** 6 tables used for vocabulary, gender rules, adjective agreement, questions, dialogues, and cafe phrases. Excellent visual organization.

## LLM Fingerprint

- No "In this lesson, we will..." opener -- clean
- No repetitive transitions detected
- The Ukrainian immersion sentences use "Це" heavily ("Це дуже важливо", "Це перевірка", "Це дуже корисно", "Це короткі речення", "Це дуже цікаво") -- borderline repetitive but acceptable since "Це" is the primary available sentence structure at this level
- "Let's" appears 8 times across the module -- slightly mechanical but acceptable for a beginner review lesson
- No grandiose openers or purple prose

## Issues Found

### CRITICAL
None.

### HIGH
1. **Plan-content misalignment on verb objective** -- Plan objective #3 ("Conjugate First Conjugation verbs correctly") is impossible to deliver given sequence constraints. Content correctly skips it, but the plan needs updating. This is a plan defect, not a content defect.
2. **Vocabulary disconnect** -- 8/20 vocabulary items are verbs that cannot be used in content or meaningfully practiced in activities (since verb conjugation is forbidden). The vocabulary YAML includes читати, писати, говорити, знати, розуміти, питати, відповідати, перевіряти -- none appear in the lesson content. Plan vocabulary_hints need revision.

### MEDIUM
3. **True-false item #2 confuses И and Н** -- Statement: "The Ukrainian letter И sounds exactly like English H." The explanation says "It looks like an H" but that describes Н, not И. И looks like a backwards N, not like H.
4. **Immersion below target** -- 14.8% Ukrainian vs 25-40% target. The audit exempts checkpoints from the immersion gate, but the content could benefit from more Ukrainian integration, particularly in the cultural section.
5. **H3 subsection labels unexplained** -- Sections use "Модель (Model)", "Практика (Practice)", "Самоперевірка (Self-Check)" as H3 headings without explaining this TTT structure to the learner.

### LOW
6. **"Big coffee" translation** -- "Це велика кава" translated as "This is big coffee" in match-up activity. "Large coffee" is more natural in English.
7. **Repetitive "Це" pattern** -- Ukrainian immersion sentences rely heavily on "Це [X]" structure. Could vary with "Ось" (here is), "А тепер" (and now), etc.

## Grade Justification

**Grade: B** -- Good module with minor issues.

The content successfully navigates a difficult situation: a stale plan that requires verb conjugation in a module where verbs are forbidden. The content writer correctly prioritized sequence constraints over plan objectives, producing a coherent checkpoint that reviews reading, gender, adjective agreement, questions, and cultural context.

The main issues are upstream (plan needs updating, vocabulary hints include unusable verbs) rather than content-quality problems. The one genuine content issue is the confusing true-false item about И/Н. Linguistic accuracy is perfect (124/124 VESUM). Pedagogical structure is solid with good use of tables, callout boxes, and progressive difficulty. Activities are well-designed with appropriate variety and difficulty.

Deductions from A:
- -0.5: Vocabulary disconnect (plan defect bleeding into content metrics)
- -0.25: True-false item error
- -0.25: Low immersion (mitigated by checkpoint exemption)
