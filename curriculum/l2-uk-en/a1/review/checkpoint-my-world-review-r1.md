## Linguistic Scan
No Russianisms, Surzhyk, calques, or paronym errors found in the Ukrainian examples I spot-checked. VESUM spot checks were clean for the relevant words, and there are no Russian characters (`ы`, `э`, `ё`, `ъ`) in the module.

Problems found:
- In **Що ми знаємо?** the claim **“The final letter always reveals the answer.”** is grammatically inaccurate. For A1 you can teach endings as a strong cue, but not as an absolute rule.
- In **Підсумок — Summary** the claim **“with a simple vowel change at the end of the word”** is grammatically inaccurate. Ukrainian plurals are not reducible to one simple vowel swap.

## Exercise Check
- Marker inventory matches the 4 `activity_hints`: `group-sort-vocabulary`, `quiz-gender-agreement`, `quiz-singular-plural`, `fill-in-shopping-dialogue`.
- Marker placement is broadly correct:
  - `group-sort-vocabulary` comes after the review/self-check section.
  - `quiz-gender-agreement` and `quiz-singular-plural` come after the grammar summary they are meant to test.
  - `fill-in-shopping-dialogue` comes after the dialogue.
- No inline exercise-logic errors are visible here because the actual YAML exercise content is not shown.
- Coverage count is correct: 4 planned activities, 4 markers present.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | The module keeps the planned H2 structure, but the reading section adds off-plan metalanguage: **“The first part is the зачin… основна частина… кінцівка”** even though the plan reference says **“No new material — review and integration of A1.2 phase.”** Also the planned cultural object `намисто` never appears in the prose. |
| 2. Linguistic accuracy | 7/10 | No Russianisms/Surzhyk/calques found, but two grammar claims are inaccurate: **“The final letter always reveals the answer.”** and **“with a simple vowel change at the end of the word.”** |
| 3. Pedagogical quality | 6/10 | There is too much English meta-explanation around the reading: **“Reading practice serves a specific purpose…”** and **“Breaking down the text's structure…”** spend many words on theory instead of directly reviewing A1.2 forms through guided practice. |
| 4. Vocabulary coverage | 7/10 | The prose uses planned cultural vocabulary like **вишиванка**, **глечик**, and **писанки**, but the planned item `намисто` is absent. |
| 5. Exercise quality | 9/10 | All 4 planned exercise markers are present and placed after relevant teaching sections: `group-sort-vocabulary`, `quiz-gender-agreement`, `quiz-singular-plural`, `fill-in-shopping-dialogue`. |
| 6. Engagement & tone | 7/10 | The teacher voice is mostly calm and usable, but generic framing like **“Reading practice serves a specific purpose in your language development”** adds padding without much learner value. |
| 7. Structural integrity | 10/10 | All planned sections are present and ordered correctly, markdown is clean, and the pipeline word count is **1492**, safely above the **1200** target. |
| 8. Cultural accuracy | 9/10 | The module is grounded in specifically Ukrainian content: **ярмарок**, **вишиванка**, **глечик**, **писанки**. It avoids Russia-centric framing. |
| 9. Dialogue & conversation quality | 8/10 | The dialogue has named speakers and a concrete market situation, and it combines demonstratives, prices, and plurals through lines like **“Скільки вона коштує?”** and **“Я беру три.”** |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: **Що ми знаємо?** — “**The final letter always reveals the answer.**”  
Issue: This teaches an absolute grammar rule that is false. Endings are a strong beginner cue, but not an infallible test of noun gender.  
Fix: Change **“always”** to a qualified formulation such as **“usually”** and restrict it to basic A1 patterns.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: **Підсумок — Summary** — “**with a simple vowel change at the end of the word**”  
Issue: This teaches the wrong idea about plural formation. Ukrainian plurals are not just a simple final-vowel swap.  
Fix: Rephrase this as changing the noun ending and then matching it with plural adjective forms.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: **Читання (Reading Practice)** — “**Reading practice serves a specific purpose in your language development…**” and “**The first part is the зачин… основна частина… кінцівка**”  
Issue: The section spends too much time on English composition theory and introduces off-plan discourse metalanguage, even though the plan says this checkpoint should be **review and integration of A1.2** with **no new material**.  
Fix: Replace the long meta-explanation with a short guided prompt that points learners to the actual target forms in the reading: possessives, adjective agreement, demonstratives, numbers, and plurals.

[VOCABULARY COVERAGE] [SEVERITY: major]  
Location: **Діалог (Connected Dialogue)** — “**They stop to look at a вишиванка…, a глечик…, and several писанки…**”  
Issue: The plan’s dialogue situation explicitly includes **намисто**, but `намисто` is missing from the prose. I searched for `намисто` and found 0 occurrences.  
Fix: Add **намисто** to the market-stall item set in the dialogue setup or dialogue lines.

[PLAN ADHERENCE] [SEVERITY: minor]  
Location: **Підсумок — Summary** — “**The upcoming module phase will introduce you to verbs.**”  
Issue: The plan explicitly names the handoff as **“Next: A1.3 — Actions”**, but the summary never states that label. I searched for `A1.3` and found 0 occurrences.  
Fix: Name the next phase explicitly as **A1.3 — Actions**.

## Verdict: REVISE
Critical factual grammar errors are present, and there is major plan/pedagogy drift in the reading section. This does not require a full rebuild: the module structure, activity markers, and most Ukrainian examples are salvageable with targeted edits.

<fixes>
- find: |
    The final letter always reveals the answer.
  replace: |
    For many basic nouns at this level, the final letter usually reveals the answer.
- find: |
    Reading practice serves a specific purpose in your language development: it shifts your focus from a simple back-and-forth dialogue to a sustained monologue. When you read a continuous text, you train your brain to follow the flow of Ukrainian thought over multiple sentences. You will read a short text describing a room. This paragraph utilizes only known vocabulary from previous modules, ensuring that you can focus entirely on the structure and grammar without being distracted by any new words. Read the following text aloud to practice your pronunciation and rhythm.
  replace: |
    Read this short room description aloud. It reviews familiar A1.2 vocabulary and lets you focus on possessives, adjective agreement, demonstratives, numbers, and plurals.
- find: |
    Breaking down the text's structure reveals how Ukrainians build a simple narrative. The Ukrainian school model teaches a straightforward three-part format for any description or story. The first part is the **зачин** (introduction). Here, it is the simple statement **Це моя кімната** (This is my room), which sets the topic. The second part is the **основна частина** (main body). In our text, this consists of listing objects, their colors, and using demonstratives to point them out. You see sentences like **Стіни білі** (The walls are white) and **Мій стіл великий і новий** (My table is big and new) fleshing out the details. The final part is the **кінцівка** (conclusion). The text wraps up with a summarizing feeling: **Я люблю свою кімнату** (I love my room). Relying on this structure helps you organize your own thoughts when speaking or writing in Ukrainian.

    :::note
    **The Power of Three**
    The **зачин**, **основна частина**, and **кінцівка** structure is taught to every Ukrainian schoolchild. Using this simple three-part formula makes your spoken and written Ukrainian sound naturally organized.
    :::
  replace: |
    Read the text again and notice how it reviews A1.2 patterns. **моя кімната** shows a possessive, **великий і новий** shows adjective agreement, **ця/та/це/те** review demonstratives, and **три книги** plus **ці книги** review numbers and plurals. Use the text as a model and describe your own room in 4-5 short sentences.
- find: |
    They stop to look at a **вишиванка** (embroidered shirt), a **глечик** (jug), and several **писанки** (decorated eggs).
  replace: |
    They stop to look at a **вишиванка** (embroidered shirt), a **глечик** (jug), a **намисто** (necklace), and several **писанки** (decorated eggs).
- find: |
    You can also talk about groups of things using the plural form, effortlessly turning a single item into many with a simple vowel change at the end of the word.
  replace: |
    You can also talk about groups of things using the plural form, often changing the noun ending and then matching it with a plural adjective.
- find: |
    Now that you can name and describe the "things" in your world, the next step is learning how to talk about "actions." The upcoming module phase will introduce you to verbs.
  replace: |
    Now that you can name and describe the "things" in your world, the next step is A1.3 — Actions, where you learn how to talk about what you do. The upcoming module phase will introduce you to verbs.
</fixes>