## Linguistic Scan
No Russianisms, Surzhyk, calques, paronym mistakes, or banned Russian characters (`ы`, `э`, `ё`, `ъ`) found.

Critical grammar error found:
- In `## Підсумок — Summary`, the module teaches only `-а → -у` for feminine accusative: `| Жіночий (Feminine) | **-а** → **-у** (**каву**) | **-а** → **-у** (**маму**) |` and then says `The feminine noun always changes its ending from **-а** to **-у**, regardless of animacy.` This is factually wrong as written, because the module itself already taught the feminine `-я → -ю` pattern earlier (`**Олена** → **Олену**`).

## Exercise Check
Marker inventory is complete and matches the 4 `activity_hints`:
- `group-sort-animate-inanimate` appears after `## Кого?`
- `fill-in-accusative-forms` appears after `## Знахідний відмінок — живе`
- `quiz-choose-correct-accusative` appears after `## Знахідний відмінок — живе`
- `fill-in-dialogue-completion` appears after `## Підсумок — Summary`

No visible marker-ID mismatch. No visible exercise-logic error can be confirmed from the module body alone because the YAML exercise content is not shown here.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All four planned H2 sections are present and ordered correctly, but the plan references are not integrated: `ULP Season 1, Episode 33` and `Заболотний` both have 0 occurrences in the content, and recommended vocab `покупець` also has 0 occurrences. |
| 2. Linguistic accuracy | 6/10 | The summary row `| Жіночий (Feminine) | **-а** → **-у** (**каву**) | **-а** → **-у** (**маму**) |` plus `The feminine noun always changes its ending from **-а** to **-у**` overstates the rule and contradicts the earlier correct example `**Олена** → **Олену**`. |
| 3. Pedagogical quality | 7/10 | The module has many examples, but it opens with generic English exposition before getting to the pattern: `We interact with people every day in our lives...` instead of leading with the target form immediately. |
| 4. Vocabulary coverage | 8/10 | Required verbs are all used in prose (`бачити`, `знати`, `любити`, `чекати`, `шукати`), and most recommended nouns appear, but `покупець` is absent from the prose. |
| 5. Exercise quality | 9/10 | The 4 expected markers are present and placed after relevant teaching sections, especially the form-focused markers after `## Знахідний відмінок — живе`. |
| 6. Engagement & tone | 7/10 | Some teacher voice is fine, but filler lines like `This structural difference is absolutely essential for natural Ukrainian speech.` add emphasis more than information. |
| 7. Structural integrity | 8/10 | Headings are complete and the pipeline word count is above target, but the module ends with a broken line: `These simple checks confirm that `. |
| 8. Cultural accuracy | 9/10 | No Russia-centric framing or cultural misinformation detected. |
| 9. Dialogue & conversation quality | 8/10 | Dialogues have named speakers and plausible contexts, but the second dialogue is short and mostly prompt-response (`Ти знаєш нашу вчительку? ... А нового лікаря?`). |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `## Підсумок — Summary` — `| Жіночий (Feminine) | **-а** → **-у** (**каву**) | **-а** → **-у** (**маму**) |` and `The feminine noun always changes its ending from **-а** to **-у**, regardless of animacy.`  
Issue: The module teaches an incomplete feminine accusative rule and omits the already-taught `-я → -ю` pattern.  
Fix: Update the summary row and explanatory sentence to include both `-а → -у` and `-я → -ю`.

[PLAN ADHERENCE] [SEVERITY: minor]  
Location: whole module; searched strings `ULP Season 1, Episode 33` and `Заболотний` both return 0 occurrences.  
Issue: The plan references are provided but never integrated into the prose.  
Fix: Add one brief sentence tying the school-style `бачу кого? що?` explanation to the Grade 4 textbook framing and mention Episode 33 as a spoken reference.

[VOCABULARY COVERAGE] [SEVERITY: minor]  
Location: whole module; searched string `покупець` returns 0 occurrences.  
Issue: One recommended vocabulary item from the plan is absent from the prose.  
Fix: Add `покупець` to the professions/people-around-you sentence in the workplace explanation.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `## Діалоги (Dialogues)` — `We interact with people every day in our lives...`  
Issue: The section starts with broad English explanation instead of immediately modeling the target accusative pattern. For A1 PPP, this is slower and less concrete than necessary.  
Fix: Replace the opener with a short pattern-led introduction using Ukrainian examples such as `Я бачу маму`, `я знаю Олену`, `я шукаю друга`.

[ENGAGEMENT & TONE] [SEVERITY: minor]  
Location: `## Знахідний відмінок — живе` — `This structural difference is absolutely essential for natural Ukrainian speech.`  
Issue: This is generic emphasis rather than new information.  
Fix: Replace it with a shorter sentence that restates the actual learner takeaway.

[STRUCTURAL INTEGRITY] [SEVERITY: major]  
Location: end of `## Підсумок — Summary` — `These simple checks confirm that `  
Issue: The module ends with a dangling incomplete sentence immediately before the final activity marker.  
Fix: Complete the sentence or remove it.

## Verdict: REVISE
REVISE because there is a critical grammar overgeneralization in the summary, plus a dangling final sentence and several quality misses. Multiple dimensions are below 9, and the critical linguistic finding alone blocks PASS.

<fixes>
- find: |
    We interact with people every day in our lives. When we talk about the people around us—identifying family members, mentioning a **друг** (friend, m) or **подруга** (friend, f), or interacting with professionals—we often use them as the direct object of our sentences. In Ukrainian, this means applying the accusative case for people. This module explores how to correctly refer to people when you see, know, or look for them.
  replace: |
    We often talk about people as direct objects: **Я бачу маму**, **я знаю Олену**, **я шукаю друга**. In Ukrainian, that means using the accusative case for people.

- find: |
    :::note
    In Ukrainian, it is very common to refer to professionals by their titles rather than their names. Discussing a **лікар** (doctor, f) or **вчитель** (teacher) in the accusative case is a standard way to talk about the people who help you in your daily life.
    :::
  replace: |
    :::note
    In Ukrainian, it is very common to refer to professionals by their titles rather than their names. You can hear this pattern in **ULP Season 1, Episode 33**, and the school-style question **«бачу кого? що?»** matches the Grade 4 textbook approach noted in the plan.
    :::

- find: |
    You will use these animate accusative forms constantly when interacting with people around you, whether speaking to a **колега** (colleague, m/f), a **викладач** (lecturer, m), or a **продавець** (seller, m) in a shop.
  replace: |
    You will use these animate accusative forms constantly when interacting with people around you, whether speaking to a **колега** (colleague, m/f), a **викладач** (lecturer, m), a **продавець** (seller, m), or a **покупець** (buyer, m) in a shop.

- find: "| Жіночий (Feminine) | **-а** → **-у** (**каву**) | **-а** → **-у** (**маму**) |"
  replace: "| Жіночий (Feminine) | **-а/-я** → **-у/-ю** | **-а/-я** → **-у/-ю** |"

- find: "The feminine noun always changes its ending from **-а** to **-у**, regardless of animacy."
  replace: "The feminine noun follows the usual accusative pattern shown here: **-а** → **-у** and **-я** → **-ю**, regardless of animacy."

- find: "This structural difference is absolutely essential for natural Ukrainian speech. Whenever you interact with people or talk about the individuals in your daily life, you must apply this animate accusative pattern to ensure your sentences are correct."
  replace: "This is the key contrast to remember: inanimate masculine nouns stay the same, but animate masculine nouns take the genitive-shaped form."

- find: "These simple checks confirm that "
  replace: "These simple checks confirm that the core pattern is clear: **кого?** triggers animate forms such as **маму** and **брата**."
</fixes>