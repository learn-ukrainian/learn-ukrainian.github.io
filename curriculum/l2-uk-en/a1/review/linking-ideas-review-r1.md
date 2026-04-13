## Linguistic Scan
No linguistic errors found.

## Exercise Check
Markers present: `fill-in-because`, `quiz-conjunction-choice`, `fill-in-all-conjunctions`, `group-sort-conjunction-roles`. Total count matches the 4 `activity_hints`, and the IDs broadly map to the plan.

Placement issue: `<!-- INJECT_ACTIVITY: fill-in-all-conjunctions -->` appears only after the summary, even though the relevant teaching for `і, а, але` is in `Сполучники` and `бо/тому що` is taught in the next section. Practice is back-loaded instead of following the teaching sequence.

The YAML exercise bodies are not shown here, so distractor quality and answer-index distribution cannot be verified from this prompt alone.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | All planned H2 sections are present and the required conjunctions are covered, but the section pacing is far off the 300-word plan budgets: `Діалоги` ~422 words, `Сполучники` ~563, `Бо і тому що` ~488, `Підсумок` ~367. `Сполучники` also spends a full subsection on `або/чи`, which is outside the stated grammar focus. |
| 2. Linguistic accuracy | 10/10 | I did not find a substantiated Russianism, Surzhyk form, calque, paronym error, wrong gender/case, or false grammar claim in the Ukrainian text. VESUM/textbook spot checks did not contradict the module’s Ukrainian forms. |
| 3. Pedagogical quality | 6/10 | The module has a PPP-like flow (`Діалоги` → explanation → practice markers), but much of the English exposition is bloated and low-yield: “These small words are the grammatical glue of the language.”, “This immediately elevates Ukrainian speech from beginner phrasing into authentic communication.” Core practice is also delayed. |
| 4. Vocabulary coverage | 9/10 | All required vocabulary from the plan appears naturally in prose: `і`, `та`, `а`, `але`, `бо`, `тому що`. Recommended items are also partly integrated (`теж`, `або`, `чи`, `тому`). |
| 5. Exercise quality | 6/10 | The module includes the expected 4 markers, but they are clustered late: two appear only after `Бо і тому що`, and two more after the summary. The broad all-conjunction practice marker is not placed right after the conjunction teaching it is meant to reinforce. |
| 6. Engagement & tone | 5/10 | The tone is readable, but several lines are empty hype rather than instruction: “These small words are the grammatical glue of the language.”, “This immediately elevates Ukrainian speech…”, “Mastering them early on is a major step toward natural, confident, and fluent communication…” |
| 7. Structural integrity | 10/10 | All planned H2 headings are present and in order, markdown is clean, and the pipeline word count is 1973, which is above the 1200 target. |
| 8. Cultural accuracy | 10/10 | The module presents Ukrainian on its own terms and does not rely on Russian-centric framing or dubious cultural claims. |
| 9. Dialogue & conversation quality | 8/10 | The dialogues use named speakers and multi-turn exchanges in plausible situations: vacation planning, cafe choice, daily routine, missed call. They are functional and more natural than drill-only textbook exchanges. |

## Findings
[PLAN ADHERENCE / PEDAGOGY] [SEVERITY: major]  
Location: `Сполучники (Conjunctions)` and overall section pacing — e.g. “When you want to present an alternative or a choice, use **або** (or) in regular statements, or **чи** (or) when asking a direct question).”  
Issue: The module substantially overruns the plan’s 300-word section budgets, and `Сполучники` spends valuable space on `або/чи`, which is outside the module’s stated grammar core (`і/та`, `а`, `але`, `бо`, `тому що`).  
Fix: Trim the English meta-exposition, remove the `або/чи` subsection, and compress long explanatory paragraphs so the section stays focused on the planned conjunction set.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: `<!-- INJECT_ACTIVITY: fill-in-all-conjunctions -->` appears only at the end of the summary.  
Issue: The first broad practice on `і, а, але, бо` comes too late. Learners finish the explanation sections before getting the planned whole-system fill-in exercise.  
Fix: Move `fill-in-all-conjunctions` to the end of `Сполучники`, before `## Бо і тому що (Because)`.

[ENGAGEMENT & TONE] [SEVERITY: major]  
Location: `Діалоги` / `Підсумок` — “These small words are the grammatical glue of the language.”; “This immediately elevates Ukrainian speech from beginner phrasing into authentic communication.”; “Mastering them early on is a major step toward natural, confident, and fluent communication with native speakers.”  
Issue: These lines add word count and hype but little instructional value. They make the module feel padded, which also worsens the section-budget miss.  
Fix: Delete these filler paragraphs/sentences and keep only the lines that introduce, exemplify, or clarify the target conjunctions.

## Verdict: REVISE
Zero critical linguistic errors, but there are clear plan/pedagogy/exercise-placement problems, and multiple dimensions score below 9. This is fixable with deterministic trims and marker relocation rather than a full rewrite.

<fixes>
- find: |
    Communication is all about connecting your thoughts. Instead of speaking in short, isolated, and choppy sentences, native Ukrainian speakers use small connecting words to build flowing, expressive speech. These small words are the grammatical glue of the language. They help you compare different ideas, add new information seamlessly, and explain your specific reasons without needing to start a completely new sentence every single time.
  replace: ""
- find: |
    Without the connecting words **а**, **бо**, **але**, and **і**, their conversation would sound like a machine reading a dry list of facts. These connectors provide the entire logical structure to their debate, allowing them to contrast the mountains with the sea, and to explain exactly why they want coffee instead of tea.
  replace: ""
- find: |
    A simple question about someone's daily routine becomes a fluid, natural conversation when you apply these tools.
  replace: ""
- find: |
    By using these basic connectors, Denys and Maksym easily explain the sequence of events, present unexpected problems like an unanswered phone, and offer clear reasons for their actions. This immediately elevates Ukrainian speech from beginner phrasing into authentic communication.
  replace: ""
- find: |
    What exactly are these connecting words? The Ukrainian grammatical term is **сполучник** (conjunction). This important word comes from the verb **сполучити** (to connect or to join). A **сполучник** does exactly what its name implies: it connects individual words, short phrases, or whole sentences to create a unified, logical thought.
  replace: |
    The Ukrainian grammatical term is **сполучник** (conjunction): it connects words, phrases, or whole sentences.
- find: |
    Consider the difference in conversational flow when you speak without them compared to when you use them properly.
  replace: ""
- find: |
    When thoughts are disconnected, they feel abrupt and incomplete, making it difficult for the listener to follow your logic.
  replace: ""
- find: |
    In Ukrainian schools (typically around Grade 4 and 5), students learn about coordinating conjunctions, known formally as **сполучники сурядності**. These specific conjunctions connect equal, balanced parts of a sentence. The most basic of these are **і** and **та**, which both mean "and" and are used to simply add information together. The word **та** is a very common synonym for **і**, appearing frequently in both classic literature and everyday written text.
  replace: |
    These are **сполучники сурядності**: **і** and **та** add information.
- find: |
    When you want to present an alternative or a choice, use **або** (or) in regular statements, or **чи** (or) when asking a direct question.

    * Ти хочеш чай **чи** каву? *(Do you want tea or coffee?)*
    * Я з'їм яблуко **або** грушу. *(I will eat an apple or a pear.)*
    * Ми підемо в кіно **чи** в театр? *(Are we going to the cinema or to the theater?)*
    * Він купить книгу **або** журнал. *(He will buy a book or a magazine.)*
  replace: ""
- find: |
    When you need to show a contrast or a switch in topic, you use the conjunction **а**. This word translates to "and" or "but" depending on the specific context, and it is used to softly compare two different things or actions. English speakers often make the mistake of using **і** when they should use **а**. Remember: **і** is for addition, while **а** is for contrast.
  replace: |
    Use **а** for a softer contrast or switch in topic.
- find: |
    For a stronger, more direct contrast, Ukrainian uses **але** (but). This word introduces an opposition, a strict contradiction, or an unexpected result. It feels heavier than the soft contrast of **а**.
  replace: |
    Use **але** for stronger contrast.
- find: |
    Answering the question **Чому?** (Why?) is a fundamental conversational skill. Ukrainians explain their reasons using two primary conjunctions: **бо** and **тому що**. Both words mean "because" and they are used continuously to build logical explanations and justify actions.
  replace: |
    **Бо** and **тому що** both answer **Чому?** (Why?).
- find: |
    While both options are perfectly correct, they possess slightly different rhythms. The word **бо** is short, energetic, and extremely common in spoken language. It provides a quick and natural way to justify an action immediately. It is critical to note that **бо** is standard, proper Ukrainian, not informal slang. You will hear it constantly in daily life across all regions of Ukraine.
  replace: |
    **Бо** is short, very common in speech, and fully standard Ukrainian.
- find: |
    The phrase **тому що** is slightly longer and feels a bit more formal, making it very common in writing, academic literature, and news broadcasts. However, people also use it freely and naturally in everyday conversation.
  replace: |
    **Тому що** is a longer neutral option used in both writing and speech.
- find: |
    If you want to reverse the logic entirely and state the result instead of the reason, you can use the linking word **тому** (therefore / that is why).

    * Я хворий, **тому** я не йду. *(I am sick, therefore I am not going.)*
    * Йде дощ, **тому** ми сидимо вдома. *(It is raining, that is why we are sitting at home.)*
    * Телефон новий, **тому** він дорогий. *(The phone is new, therefore it is expensive.)*
  replace: ""
- find: |
    Understanding exactly how to link your ideas transforms your Ukrainian from a series of disconnected, rigid words into a flowing, highly logical language. These basic conjunctions allow you to express complex thoughts, highlight comparisons, and explain your reasons clearly. Mastering them early on is a major step toward natural, confident, and fluent communication with native speakers.
  replace: ""
- find: |
    * День сонячний, **але** дуже холодний. *(The day is sunny, but very cold.)*

    ## Бо і тому що (Because)
  replace: |
    * День сонячний, **але** дуже холодний. *(The day is sunny, but very cold.)*

    <!-- INJECT_ACTIVITY: fill-in-all-conjunctions -->

    ## Бо і тому що (Because)
- find: |
    <!-- INJECT_ACTIVITY: fill-in-all-conjunctions -->
  replace: ""
</fixes>