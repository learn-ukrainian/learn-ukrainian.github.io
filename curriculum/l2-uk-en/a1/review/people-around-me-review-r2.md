## Linguistic Scan
No linguistic errors found.

## Exercise Check
Found 4 markers: `group-sort-animate-inanimate`, `fill-in-accusative-forms`, `quiz-choose-correct-accusative`, `fill-in-dialogue-completion`.

They are placed after the relevant teaching sections and match the 4 `activity_hints` by type/focus. The markers are reasonably spread through the module, and there are no inline DSL exercises here, so no downstream answer-key logic errors are visible in the prose.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | Core objectives are covered, and all required verbs appear, but the wedding-photo outline drops planned nouns (`дядько`, `тітка`, `наречений` search = 0 in the generated content), and the listed references (`ULP Season 1, Episode 33`, `Grade 4`, `Заболотний`) are never cited. |
| 2. Linguistic accuracy | 10/10 | No Russianisms, Surzhyk, calques, bad case endings, or factual grammar errors found in the Ukrainian text. |
| 3. Pedagogical quality | 7/10 | The lesson has a usable presentation-to-explanation-to-practice flow, but it spends too many words on English metalanguage; e.g. the paragraph beginning “Notice how the nouns for family members change their endings...” is much longer than the concept requires before the first activity. |
| 4. Vocabulary coverage | 9/10 | All required verbs from the plan appear in prose (`бачити`, `знати`, `любити`, `чекати`, `шукати`), and recommended items such as `сусід`, `колега`, `викладач`, `вчитель`, `лікар`, `продавець`, `покупець` are included. |
| 5. Exercise quality | 9/10 | Four markers appear and align with the four `activity_hints`: group sort after `Кого?`, fill-in and quiz after `Знахідний відмінок — живе`, and dialogue completion after `Підсумок`. |
| 6. Engagement & tone | 7/10 | The teacher voice is steady, but some sentences are generic filler rather than instruction, e.g. “This is a fundamental pattern you will use...” and “Seeing them together makes the grammatical difference perfectly clear.” |
| 7. Structural integrity | 10/10 | All planned H2 headings are present and ordered correctly, markdown is clean, and the pipeline word count is 1734, safely above the 1200 target. |
| 8. Cultural accuracy | 9/10 | The module presents Ukrainian on its own terms and avoids Russian-centered framing. |
| 9. Dialogue & conversation quality | 8/10 | Named speakers and concrete situations help, especially the wedding-photo setup, but the exchanges are brief and heavily form-driven. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: `Let us look at a natural conversation. Two friends are looking at wedding photos and identifying people in them.` and the dialogue that follows  
Issue: The plan’s wedding-photo situation explicitly includes `дядько`, `тітка`, and `наречений`, but those nouns never appear in the generated module. That narrows the planned coverage of “people around me” in the flagship dialogue.  
Fix: Extend the first dialogue so the photo scene also names the uncle, aunt, and groom in Ukrainian.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `In Ukrainian schools, children learn this grammar by memorizing the double question «Бачу кого? що?» (I see whom? what?).`  
Issue: The plan lists two references, but the prose never cites them. `ULP`, `Episode 33`, `Заболотний`, and `Grade 4` do not appear anywhere in the module.  
Fix: Add one explicit sentence here tying the explanation to the Grade 4 textbook approach and `ULP Season 1, Episode 33`.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `Notice how the nouns for family members change their endings in this dialogue...`  
Issue: This explanation is too long for an A1 point the dialogue already demonstrates. It adds English exposition instead of moving quickly to pattern recognition and practice.  
Fix: Compress the paragraph to a short pattern-focused explanation.

[ENGAGEMENT & TONE] [SEVERITY: minor]  
Location: `In this workplace setting, we observe the same grammatical pattern applied to professions and names...`  
Issue: The paragraph is padded with generic explanatory prose and repeats points the learner already saw in the dialogue.  
Fix: Replace it with a tighter paragraph that names the three useful forms and stops.

## Verdict: REVISE
REVISE — there are no Ukrainian-language errors, but multiple major findings remain in plan adherence and pedagogy, and several dimensions fall below 9.

<fixes>
- find: |
    > **Друг:** **А хто це?** *(And who is this?)*
    > **Наречена:** **Це мій брат. Ти знаєш мого брата?** *(This is my brother. Do you know my brother?)*
    > **Друг:** **Ні, я не знаю твого брата.** *(No, I do not know your brother.)*
    > **Наречена:** **Ходімо, я тебе познайомлю!** *(Let's go, I will introduce you!)*
  replace: |
    > **Друг:** **А хто це?** *(And who is this?)*
    > **Наречена:** **Це мій брат. Ти знаєш мого брата?** *(This is my brother. Do you know my brother?)*
    > **Друг:** **Ні, я не знаю твого брата. А кого ще ти тут бачиш?** *(No, I do not know your brother. And who else do you see here?)*
    > **Наречена:** **Я бачу мого дядька і тітку. А там ти бачиш нареченого. Ходімо, я тебе познайомлю!** *(I see my uncle and aunt. And there you can see the groom. Let's go, I will introduce you!)*

- find: |
    In Ukrainian schools, children learn this grammar by memorizing the double question «Бачу кого? що?» (I see whom? what?).
  replace: |
    In Ukrainian schools, children learn this grammar by memorizing the double question «Бачу кого? що?» (I see whom? what?). This follows the Grade 4 textbook approach listed in the plan, and the same core pattern appears in ULP Season 1, Episode 33.

- find: |
    Notice how the nouns for family members change their endings in this dialogue. In the dictionary, these nouns are **мама**, **тато**, and **брат**. However, when they become the object of the verb **бачити** (to see) or **знати** (to know), their endings must change. The noun **мама** becomes **маму**, **тато** becomes **тата**, and **брат** becomes **брата**. We call this the animate accusative form, and it is specifically used for living beings like people and animals. This is a fundamental pattern you will use when talking about your family and friends in Ukrainian.
  replace: |
    Notice the endings: **мама** → **маму**, **тато** → **тата**, **брат** → **брата**. These are animate accusative forms used for people, so the dialogue immediately shows the core pattern you need for family and friends.

- find: |
    In this workplace setting, we observe the same grammatical pattern applied to professions and names. The noun for a female teacher is **вчителька** (teacher, f), but here it changes to **вчительку**. The name **Олена** becomes **Олену**. The noun for a male doctor is **лікар** (doctor, m), but it transforms into **лікаря**. When the first colleague says she is waiting for him, she uses the verb **чекати** (to wait for). Just like seeing or knowing someone, waiting for a person requires this specific object form. You will use these animate accusative forms constantly when interacting with people around you, whether speaking to a **колега** (colleague, m/f), a **викладач** (lecturer, m), a **продавець** (seller, m), or a **покупець** (buyer, m) in a shop.
  replace: |
    This dialogue adds three useful patterns: **вчителька** → **вчительку**, **Олена** → **Олену**, and **лікар** → **лікаря**. It also shows **чекати** with a person as the object, so the same animate object forms keep appearing with people around you.
</fixes>