## Linguistic Scan
No linguistic errors found in terms of Russianisms, Surzhyk, or calques. All vocabulary is perfectly attested in Ukrainian. However, there is a critical phonetic/orthographic error regarding the dash rule, which is documented in the findings below.

## Exercise Check
- `<!-- INJECT_ACTIVITY: fill-in-self-intro -->`: Placed correctly after "Мене звати...".
- `<!-- INJECT_ACTIVITY: quiz-register-choice -->`: Placed incorrectly after "Це...". The "Це..." section focuses on "What is this/Who is this" and does not teach registers. It should be moved after the "Особові займенники" section, which actually teaches formal vs. informal pronouns.
- `<!-- INJECT_ACTIVITY: match-up-gendered-professions -->`: Placed correctly after "Я — студент".
- `<!-- INJECT_ACTIVITY: fill-in-dialogue-final -->`: Placed correctly after "Звідки?".
- Total markers: 4 (matches plan exactly).

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 10/10 | Word budget exceeded (1725 words vs 1200 target). All `content_outline` points covered perfectly. Dialogues match the plan exactly. |
| 2. Linguistic accuracy | 8/10 | The text claims the dash is "completely silent when speaking... without any extra pause," which contradicts the phonetic rule that the dash represents a logical pause. |
| 3. Pedagogical quality | 8/10 | The module teaches that a dash is used to replace "to be" (Я — студент), but then immediately presents 7 examples without dashes ("Він студент"). The summary includes "Хто ви?" which was not taught and is pragmatically abrupt. |
| 4. Vocabulary coverage | 10/10 | All required vocabulary is integrated seamlessly into contextual sentences and dialogues. Recommended vocabulary is also heavily utilized. |
| 5. Exercise quality | 9/10 | The `quiz-register-choice` activity is placed directly after the "Це..." section, which does not cover formal/informal registers. |
| 6. Engagement & tone | 9/10 | Excellent teacher persona and cultural notes, but the conclusion uses banned corporate/gamified language ("You now possess the core tools..."). |
| 7. Structural integrity | 10/10 | Clean markdown, clear H2 headers matching the outline exactly. Word count is strong. |
| 8. Cultural accuracy | 10/10 | Explains the cultural context of handshakes, eye contact, and the literal translation of "мене звати" effectively. |
| 9. Dialogue & conversation quality | 10/10 | The dialogues are contextualized beautifully (hostel vs conference) and flow naturally for A1 learners. |

## Findings

[Linguistic accuracy] [Critical]
Location: Section "Я — студент (I am a student)" — `The dash (—) replaces the missing verb "to be" in writing, but it is completely silent when speaking. When reading the sentence **Я — лікар** out loud, simply say the two words naturally without any extra pause.`
Issue: The text provides a factually incorrect phonetic rule. In Ukrainian, a dash between a subject and a nominal predicate explicitly represents a logical intonational pause. Instructing learners to "simply say the two words naturally without any extra pause" contradicts the orthographic reason for the dash's existence.
Fix: Update the tip to explain that a slight pause can be made where the dash is.

[Pedagogical quality] [Major]
Location: Section "Я — студент (I am a student)" — `**Він студент.** (He is a student.) vs **Вона студентка.**`
Issue: The text establishes the rule that a long dash marks the spot of the missing verb, but then lists 7 consecutive examples of professions and nationalities without the dash, directly contradicting its own stated rule and confusing learners.
Fix: Add the dash to all profession and nationality examples to maintain consistency with the section's rule.

[Exercise quality] [Major]
Location: Section "Це... (This is...)" — `<!-- INJECT_ACTIVITY: quiz-register-choice -->`
Issue: The activity `quiz-register-choice` tests formal vs informal register, but it is placed after a section about pointing at objects/people ("Who is this/What is this"), which has nothing to do with registers.
Fix: Move the activity marker to immediately after the "Особові займенники" section, where formal and informal pronouns (ти vs ви) are actually taught.

[Pedagogical quality] [Major]
Location: Section "Підсумок — Summary" — `- **Хто ви? — Я — вчителька.** (Who are you? — I am a teacher.)`
Issue: The summary includes the question "Хто ви?", which was never taught in the module. Furthermore, asking "Хто ви?" as a standalone question to find out someone's profession is pragmatically abrupt ("Who are you?") in Ukrainian.
Fix: Replace the question with a simple declarative statement taught in the text.

[Engagement & tone] [Minor]
Location: Section "Підсумок — Summary" — `You now possess the core tools to introduce yourself...`
Issue: The text uses banned corporate/gamified language ("You now possess...").
Fix: Reword to a more natural teacher phrase ("You are now ready to...").

## Verdict: REVISE
The module is incredibly strong, exceeding word counts and integrating cultural notes effectively. However, the contradiction regarding the dash rule (teaching it, then ignoring it in 7 examples) and the factually incorrect phonetic claim about the dash must be fixed. There are also minor structural fixes required for exercise placement.

<fixes>
- find: |-
    The dash (—) replaces the missing verb "to be" in writing, but it is completely silent when speaking. When reading the sentence **Я — лікар** out loud, simply say the two words naturally without any extra pause.
  replace: |-
    The dash (—) replaces the missing verb "to be" in writing. When reading the sentence **Я — лікар** out loud, you can either say the two words naturally or make a very slight pause where the dash is.
- find: |-
    **Він студент.** (He is a student.) vs **Вона студентка.** (She is a student.)
    **Він лікар.** (He is a doctor.) vs **Вона лікарка.** (She is a doctor.)
    **Він вчитель.** (He is a teacher.) vs **Вона вчителька.** (She is a teacher.)
    **Він програміст.** (He is a programmer.) vs **Вона програмістка.** (She is a programmer.)
  replace: |-
    **Він — студент.** (He is a student.) vs **Вона — студентка.** (She is a student.)
    **Він — лікар.** (He is a doctor.) vs **Вона — лікарка.** (She is a doctor.)
    **Він — вчитель.** (He is a teacher.) vs **Вона — вчителька.** (She is a teacher.)
    **Він — програміст.** (He is a programmer.) vs **Вона — програмістка.** (She is a programmer.)
- find: |-
    **Він українець.** (He is a Ukrainian.) vs **Вона українка.** (She is a Ukrainian.)
    **Він американець.** (He is an American.) vs **Вона американка.** (She is an American.)
    **Він канадієць.** (He is a Canadian.) vs **Вона канадка.** (She is a Canadian.)
  replace: |-
    **Він — українець.** (He is a Ukrainian.) vs **Вона — українка.** (She is a Ukrainian.)
    **Він — американець.** (He is an American.) vs **Вона — американка.** (She is an American.)
    **Він — канадієць.** (He is a Canadian.) vs **Вона — канадка.** (She is a Canadian.)
- find: |-
    This construction is the fastest way to build your vocabulary. You point, you ask, you identify.

    <!-- INJECT_ACTIVITY: quiz-register-choice -->

    ## Особові займенники (Personal Pronouns)
  replace: |-
    This construction is the fastest way to build your vocabulary. You point, you ask, you identify.

    ## Особові займенники (Personal Pronouns)
- find: |-
    When writing a formal letter or email to one specific person, you capitalize it as **Ви** to show high respect. These pronouns drive the rest of the sentence.

    ## Я — студент (I am a student)
  replace: |-
    When writing a formal letter or email to one specific person, you capitalize it as **Ви** to show high respect. These pronouns drive the rest of the sentence.

    <!-- INJECT_ACTIVITY: quiz-register-choice -->

    ## Я — студент (I am a student)
- find: |-
    You now possess the core tools to introduce yourself, identify the world around you, and engage in a first conversation. You can navigate formal and informal encounters with confidence. Use this checklist to verify your understanding of the foundational patterns:
  replace: |-
    You are now ready to introduce yourself, identify the world around you, and engage in a first conversation. You can navigate formal and informal encounters with confidence. Use this checklist to verify your understanding of the foundational patterns:
- find: |-
    - **Хто ви? — Я — вчителька.** (Who are you? — I am a teacher.)
  replace: |-
    - **Вона — вчителька.** (She is a teacher.)
</fixes>
