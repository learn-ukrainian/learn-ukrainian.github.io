## Linguistic Scan
- No Russianisms, Surzhyk, calques, paronym misuse, or forbidden Russian characters found.
- Factual grammar claim is too absolute: `This change is not an optional stylistic choice; Ukrainians always use the vocative case when addressing someone directly.` Standard Ukrainian strongly prefers the vocative here, but the textbook evidence provided by the repo describes recommended/preferred usage, not an exception-free `always`.
- Factual grammar claim is incorrect: `You must always use the vocative case for both the title and the person's name.` This is wrong for `пані`, which stays unchanged: `пані Оксано`.

## Exercise Check
- 4 markers are present, which matches the 4 `activity_hints` in the plan.
- `fill-in-dialogue-completion` appears after `## Діалоги`, which is the right placement.
- `quiz-vocative-choice` appears after `## Кличний відмінок`, which is the right placement.
- `group-sort-endings` and `fill-in-vocative-forms` appear after `## Закінчення кличного`, which is the right placement.
- Marker spread is acceptable for this module shape, and the marker types/focus align with the plan.
- No exercise-logic errors are visible in the prose itself; the actual injected YAML exercise content is not shown here.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | All planned H2 sections are present: `Діалоги`, `Кличний відмінок`, `Закінчення кличного`, `Підсумок — Summary`. Required plan vocabulary is covered in prose: `друг`, `подруга`, `брат`, `сестра`, `пан`, `пані`. |
| 2. Linguistic accuracy | 7/10 | Two explanatory claims are inaccurate: `Ukrainians always use the vocative case when addressing someone directly` and `You must always use the vocative case for both the title and the person's name.` |
| 3. Pedagogical quality | 8/10 | The module has clear examples, but the `Діалоги` section opens with a long English scene-setter before the learner sees any Ukrainian dialogue: `Imagine you are at a busy, loud birthday party... instantly makes you sound like a native speaker.` |
| 4. Vocabulary coverage | 9/10 | Required vocabulary is used naturally, and recommended items also appear: `синку`, `дочко`, `козак`, `вчитель`, `бабуся`, `дідусь`. |
| 5. Exercise quality | 9/10 | Marker inventory is complete and correctly placed after teaching sections; the module includes one marker per planned activity hint. |
| 6. Engagement & tone | 9/10 | The teacher voice is warm and concrete, with usable examples like `Мамо, де мій телефон?` and `Добрий день, пане Іване!`. |
| 7. Structural integrity | 10/10 | All four planned sections are present and ordered correctly, and the pipeline word count is `1536`, which is above the `1200` target. |
| 8. Cultural accuracy | 9/10 | The lesson presents Ukrainian on its own terms and does not frame it through Russian. The only cultural-language issue is the overabsolute rule wording already noted in linguistic accuracy. |
| 9. Dialogue & conversation quality | 9/10 | Dialogues use named speakers, real situations, and multi-turn exchanges: meeting a friend, looking for a phone, asking about keys. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `## Кличний відмінок` — `This change is not an optional stylistic choice; Ukrainians always use the vocative case when addressing someone directly.`  
Issue: This teaches an overabsolute rule. Standard Ukrainian strongly prefers the vocative in direct address, but `always` is too categorical.  
Fix: Replace `Ukrainians always use` with wording about standard/preferred usage.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `## Кличний відмінок` — `You must always use the vocative case for both the title and the person's name. This double change shows high respect and deep cultural awareness.`  
Issue: This is factually wrong for `пані`, which does not change in the examples given (`пані Оксано`).  
Fix: State that `пан` changes to `пане`, while `пані` stays unchanged and only the name changes.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `## Діалоги` — `Imagine you are at a busy, loud birthday party... This subtle change is a fundamental part of everyday communication, and it instantly makes you sound like a native speaker.`  
Issue: The section delays the first Ukrainian input with a long English lead-in, which weakens PPP pacing for A1.  
Fix: Replace the opening paragraph with a short setup that gets to the Ukrainian examples immediately.

## Verdict: REVISE
REVISE — there are two critical factual inaccuracies in the grammar explanation and one major A1 pedagogy issue. Dimensions 2 and 3 fall below the PASS gate.

<fixes>
- find: |-
    Imagine you are at a busy, loud birthday party. The music is playing, people are dancing, and your friends are talking in every corner of the large room. You are holding a plate of cake and you want to offer a piece to your friend who is standing far away. Or perhaps you need to ask your mom where she put the extra gifts. In English, you simply shout their name: "Olena!" or "Mom!". But to get someone's attention naturally in Ukrainian, you cannot just use their name in its basic dictionary form. You have to change the ending of the word. This subtle change is a fundamental part of everyday communication, and it instantly makes you sound like a native speaker. The party environment is the perfect place to see this grammar in action. You will hear different names and relationships, and every single one changes.
  replace: |-
    At a birthday party, you often need to call someone across the room: **Олено! Тарасе! Мамо! Бабусю!** In Ukrainian, direct address usually changes the ending of the name or family word. Listen for these forms in the dialogues below.
- find: |-
    The Ukrainian language has a special grammatical case dedicated entirely to calling someone or getting their attention. It is called the **кличний відмінок** (vocative case). In English, you just use the person's name exactly as it is: "Olena, come here!" In Ukrainian, the name actively changes its form: **Олено, ходи сюди!** This change is not an optional stylistic choice; Ukrainians always use the vocative case when addressing someone directly. In fact, in Ukrainian elementary schools, fourth-grade students learn a specific helper word to remember this case: **Кл. (!)**. The exclamation mark is a visual cue that reminds you: you are calling someone, you are getting their attention, so the word ending must change.
  replace: |-
    Ukrainian has a special grammatical case for calling someone or getting their attention: the **кличний відмінок** (vocative case). In standard Ukrainian, direct address normally uses this form: **Олено, ходи сюди!** In school grammar, this case is often remembered with the helper **Кл. (!)** — the exclamation mark signals that you are calling someone, so the ending changes.
- find: |-
    You must always use the vocative case for both the title and the person's name. This double change shows high respect and deep cultural awareness.
  replace: |-
    Use the vocative form in the name. With **пан**, the title also changes (**пане Іване**), but **пані** stays unchanged (**пані Оксано**).
</fixes>