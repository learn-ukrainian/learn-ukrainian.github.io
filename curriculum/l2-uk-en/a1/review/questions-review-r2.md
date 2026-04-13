## Linguistic Scan
- **Question Words**: `"The word **що** only asks for identification."` is a factual grammar error. S.U.M.-11 defines **що** as a question word for a thing, phenomenon, or action, so this sentence teaches a false restriction.

## Exercise Check
Markers found: `quiz-question-word-choice`, `match-question-answer`, `fill-in-negation-transform`, `quiz-double-negation`.

Placement is correct: the two question markers come after `Пита́льні слова́`, and the two negation markers come after `Запере́чення`. The IDs match all four `activity_hints` from the plan. No inline DSL exercises are present here, so there is no exercise logic to audit beyond marker placement.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All planned sections and all 4 activity markers are present, but the plan references are not cited anywhere in the prose (`Варзацька`, `ULP`, `Episode 35` = 0 hits), and the final self-check drops the plan’s explicit `Я не... / Ніхто не...` production task. |
| 2. Linguistic accuracy | 7/10 | In `Пита́льні слова́`, the module says: `"The word **що** only asks for identification."` That is false; S.U.M.-11 defines **що** as asking about a thing, phenomenon, or action. |
| 3. Pedagogical quality | 7/10 | The section first says `"these question words take the very first position"` but later teaches `"Ти де живеш?"` as acceptable, so the rule is presented too rigidly and then immediately softened. |
| 4. Vocabulary coverage | 10/10 | All required plan words are present in context, and recommended items such as `ніхто`, `нічого`, `ніколи`, `жити`, `розуміти`, and `тому що` are also represented naturally. |
| 5. Exercise quality | 10/10 | The marker inventory matches the plan exactly, and each marker comes after the concept it is meant to test. |
| 6. Engagement & tone | 7/10 | `"You now possess a complete set of question words..."` slips into the gamified/corporate tone the rubric explicitly warns against. |
| 7. Structural integrity | 10/10 | All planned H2 sections are present and ordered correctly, and the pipeline word count is 1630, safely above target. |
| 8. Cultural accuracy | 10/10 | No Russian-comparison framing or cultural inaccuracies found. |
| 9. Dialogue & conversation quality | 7/10 | The Marco/Anna dialogue is one-sided: Marco asks 4 questions and Anna asks 0, so it reads like an interview rather than a natural exchange. |

## Findings
[Linguistic accuracy] [SEVERITY: critical]  
Location: `The word **що** only asks for identification.`  
Issue: This teaches a false rule. **Що** does not only identify objects; it also asks about actions and events, which the module itself already shows in `Що ти ро́биш?`.  
Fix: Replace the paragraph so **що** is explained as a general question word, and reserve **який** for quality/type.

[Pedagogical quality] [SEVERITY: major]  
Location: `In a typical sentence, these question words take the very first position.` and later `Ти де живеш?`  
Issue: The rule is stated too absolutely, then contradicted a few lines later. That is avoidable learner confusion.  
Fix: Change the first sentence to `In neutral questions, these words usually come first.`

[Dialogue & conversation quality] [SEVERITY: major]  
Location:  
`> **Марко́:** Хто ти?`  
`> **А́нна:** Я студе́нтка.`  
`> **Марко:** Що ти вивча́єш?`  
`> **Анна:** Я вивча́ю украї́нську.`  
`> **Марко:** Де ти живе́ш?`  
`> **Анна:** Я живу́ в Ки́єві.`  
`> **Марко:** Ко́ли ти працю́єш?`  
`> **Анна:** Вра́нці.`  
Issue: One speaker asks four straight questions and the other never asks anything back. This is textbook interrogation, not conversation.  
Fix: Rewrite the exchange so Anna also asks at least one or two return questions.

[Plan adherence] [SEVERITY: major]  
Location: module body; searched for `Варзацька`, `ULP`, and `Episode 35` and found 0 occurrences.  
Issue: The plan’s reference sources are not cited or integrated anywhere in the prose.  
Fix: Add one short note in the question section tying the explanation to `Варзацька Grade 4, p.41` and `ULP Season 1, Episode 35`.

[Plan adherence] [SEVERITY: major]  
Location: `2.  Change the positive statement "Я бачу все" (I see everything) into a negative statement meaning "I see nothing" using the double negation rule.`  
Issue: The summary practice no longer matches the plan’s explicit self-check pattern `Я не... / Ніхто не...`; learners only produce one negative form.  
Fix: Replace this item with a prompt that requires both a simple negative sentence and a `Ніхто не...` sentence.

[Engagement & tone] [SEVERITY: minor]  
Location: `You now possess a complete set of question words to navigate daily situations, gather facts, and build relationships.`  
Issue: This is gamified/corporate phrasing, not teacherly explanation.  
Fix: Replace it with a neutral summary sentence about what the learner practiced.

## Verdict: REVISE
REVISE. The module has a critical factual grammar error about **що**, plus multiple major quality issues in pedagogy, dialogue naturalness, and plan adherence. It is not a rebuild, but it should not ship as written.

<fixes>
- find: |
    To gather information effectively, you need a core set of linguistic tools. Ukrainian relies on seven essential question words: **хто** (who), **що** (what), **де** (where), **куди** (where to), **коли** (when), **чому** (why), and **як** (how). In a typical sentence, these question words take the very first position.
  replace: |
    To gather information effectively, you need a core set of linguistic tools. Ukrainian relies on seven essential question words: **хто** (who), **що** (what), **де** (where), **куди** (where to), **коли** (when), **чому** (why), and **як** (how). In neutral questions, these words usually come first.

- find: |
    The distinction between **хто** (who) and **що** (what) is strictly tied to animacy. You must use **хто** when asking about people or animals, and **що** when asking about inanimate objects or abstract concepts. English speakers frequently use "what" to ask for a description or specification, such as "What color is it?" or "What kind of car is it?". You cannot do this in Ukrainian. The word **що** only asks for identification. If you point to a vehicle and ask **Що це?** (What is this?), the answer is simply "A car." To ask for a description, you must use the word **яки́й** (what kind / which). This clear separation prevents confusion and guarantees that you receive the specific information you want.
  replace: |
    The distinction between **хто** (who) and **що** (what) is important, but **що** does more than ask for identification. Use **хто** for a person or another animate being. Use **що** for a thing, an event, or an action: **Що це?** (What is this?) and **Що ти ро́биш?** (What are you doing?). When you ask about a quality or type, Ukrainian usually uses **яки́й**: **Яки́й це колір?** (What color is it?) or **Яка це маши́на?** (What kind of car is it?).

- find: |
    > **Марко́:** Хто ти? *(Who are you?)*
    > **А́нна:** Я студе́нтка. *(I am a student.)*
    > **Марко:** Що ти вивча́єш? *(What do you study?)*
    > **Анна:** Я вивча́ю украї́нську. *(I study Ukrainian.)*
    > **Марко:** Де ти живе́ш? *(Where do you live?)*
    > **Анна:** Я живу́ в Ки́єві. *(I live in Kyiv.)*
    > **Марко:** Ко́ли ти працю́єш? *(When do you work?)*
    > **Анна:** Вра́нці. *(In the morning.)*
  replace: |
    > **Марко́:** Хто ти? *(Who are you?)*
    > **А́нна:** Я А́нна, студе́нтка. А ти? *(I am Anna, a student. And you?)*
    > **Марко:** Я Марко. Що ти вивча́єш? *(I am Marko. What do you study?)*
    > **Анна:** Я вивча́ю украї́нську. А де ти живе́ш? *(I study Ukrainian. And where do you live?)*
    > **Марко:** Я живу́ в Ки́єві. А ти? *(I live in Kyiv. And you?)*
    > **Анна:** Теж у Ки́єві. Ко́ли ти працю́єш? *(Also in Kyiv. When do you work?)*
    > **Марко:** Вра́нці. *(In the morning.)*

- insert_after: |
    Both variations mean exactly the same thing. The first option, with the question word at the front, is the most neutral and common pattern.
  text: |
    A similar presentation of question words and yes/no intonation appears in **Варзацька Grade 4, p.41** and **ULP Season 1, Episode 35**, the two references named in the plan.

- find: |
    This module provided the essential tools for extracting information and expressing negative statements. You now possess a complete set of question words to navigate daily situations, gather facts, and build relationships.
  replace: |
    This module introduced the main question words and the basic negation patterns you need for everyday A1 communication.

- find: |
    2.  Change the positive statement "Я бачу все" (I see everything) into a negative statement meaning "I see nothing" using the double negation rule.
  replace: |
    2.  Write two negative sentences: one with **не** (**Я не знаю.**) and one with **Ніхто не...** (**Ніхто не знає.**).
</fixes>