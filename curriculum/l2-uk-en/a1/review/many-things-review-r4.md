## Linguistic Scan
No linguistic errors found.

## Exercise Check
All 4 planned markers are present and placed after the relevant teaching sections: `group-sort-singular-plural`, `fill-in-make-it-plural`, and `quiz-choose-correct-plural` follow `## Один → бага́то`, and `fill-in-adjective-agreement` follows `## Прикме́тники у множині́`. Marker count matches the 4 `activity_hints`, and no marker-level logic problems are visible.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | The planned grammar/content points are covered with direct examples like `"стіл → столи"`, `"книга → книги"`, `"вікно → вікна"`, and `"**ці** means \"these\" and **ті** means \"those\""`, with textbook citations included. But the pipeline word count is 986/1200, and searched prose shows no `сумки`, `лампи`, `дзеркала`, or `речі`. |
| 2. Linguistic accuracy | 10/10 | Core Ukrainian forms are correct throughout: `"стілець → стільці"`, `"великий стіл → великі столи"`, `"чисте вікно → чисті вікна"`. No Russian letters `ы`, `э`, `ё`, `ъ` appear. |
| 3. Pedagogical quality | 9/10 | The module follows a clean presentation-to-rule-to-practice flow: dialogues first, then `"Один → бага́то"`, then `"Прикме́тники у множині́"`, then review/self-check. Each grammar point has multiple examples. |
| 4. Vocabulary coverage | 7/10 | All required vocabulary is present, including `"столи"`, `"книги"`, `"вікна"`, `"стільці"`, `"ці"`, `"ті"`, `"мої́ нові книги"`, and `"які"`. But recommended `сумки`, `лампи`, `дзеркала`, and `речі` do not occur in the prose. |
| 5. Exercise quality | 9/10 | The four markers align with the plan’s four activity hints and are placed after the relevant teaching sections. The singular/plural markers follow the plural explanation, and the adjective-agreement marker follows the adjective section. |
| 6. Engagement & tone | 9/10 | The tone is teacherly and mostly substantive, with practical prompts like `"Look around your own room or classroom..."`. It is a bit functional, but not padded or gamified. |
| 7. Structural integrity | 5/10 | All required H2 sections are present and ordered correctly, but the pipeline note gives 986 words, below the 1200 target. Section balance is also short versus the 300-word outline in three sections: approx. 258 words in `Один → бага́то`, 216 in `Прикме́тники у множині́`, and 248 in `Підсумок`. |
| 8. Cultural accuracy | 10/10 | Ukrainian is presented on its own terms, with no Russian-centered framing or cultural distortion. |
| 9. Dialogue & conversation quality | 7/10 | The classroom dialogue works, but the shop exchange is thin: `"Так! Які ручки? Черво́ні чи си́ні? ... Скі́льки? ... Три зошити."` It stays grammatical, but it reads like a drill rather than a natural multi-turn interaction. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: module-wide — `## Один → бага́то (Singular → Plural)`, `## Прикме́тники у множині́ (Adjectives in Plural)`, `## Підсумок — Summary`  
Issue: The module underfills the plan’s 1200-word target; the pipeline note gives 986 words, and three of the four planned 300-word sections are noticeably short.  
Fix: Add about 220 words of contextualized plural practice across the prose so the module reaches target length while reinforcing the taught patterns.

[VOCABULARY COVERAGE] [SEVERITY: major]  
Location: module-wide; searched prose contains no `сумки`, `лампи`, `дзеркала`, `речі`  
Issue: Four recommended plan words never appear in running prose, so learners miss contextual exposure to a large part of the recommended vocabulary set.  
Fix: Add a short room-description/practice paragraph that uses `лампи`, `сумки`, `дзеркала`, and `речі` with plural nouns, adjectives, and demonstratives.

[DIALOGUE & CONVERSATION QUALITY] [SEVERITY: major]  
Location: shop dialogue — `> **Продаве́ць:** Так! Які ручки? Черво́ні чи си́ні? ... > **Студент:** Три зошити.`  
Issue: The exchange is too transactional and gives the learner mostly one-word turns; it does not sound like a natural A1 conversation.  
Fix: Replace it with a slightly fuller shop exchange that keeps the same grammar target but adds a complete request, confirmation, and closing.

## Verdict: REVISE
No critical language errors were found, but the module misses the 1200-word target, leaves four recommended plan words unused, and includes one dialogue block that is below the dialogue-quality bar.

<fixes>
- find: |
    > **Студе́нт:** До́брий день! У вас є ручки? *(Good afternoon! Do you have pens?)*
    > **Продаве́ць:** Так! Які ручки? Черво́ні чи си́ні? *(Yes! What kind of pens? Red or blue?)*
    > **Студент:** Сині. І ще зо́шити, будь ла́ска. *(Blue. And also notebooks, please.)*
    > **Продавець:** Скі́льки? *(How many?)*
    > **Студент:** Три зошити. *(Three notebooks.)*
    > **Продавець:** Ось, будь ласка. *(Here you go.)*
  replace: |
    > **Студе́нт:** До́брий день! У вас є ручки? *(Good afternoon! Do you have pens?)*
    > **Продаве́ць:** Так, є. Які ручки вам потрібні: червоні чи сині? *(Yes, we do. Which pens do you need: red or blue?)*
    > **Студент:** Сині, будь ласка. І ще три зошити. *(Blue ones, please. And three notebooks as well.)*
    > **Продавець:** Добре. Ось сині ручки і три зошити. Ще щось? *(All right. Here are blue pens and three notebooks. Anything else?)*
    > **Студент:** Ні, дякую. *(No, thank you.)*
    > **Продавець:** Будь ласка. *(You’re welcome.)*
- insert_after: "That is why pairs like **стіл — столи**, **книга — книги**, and **річ — ре́чі** are worth practicing aloud."
  content: "Try four more everyday pairs from the same room: **одна лампа — лампи**, **одна сумка — сумки**, **одне дзеркало — дзеркала**, **одна річ — речі**. Then turn them into short sentences: **На столі лежать сумки. Біля дошки стоять лампи. На стіні є дзеркала. Тут мої речі.** This keeps the new plural forms tied to real objects instead of isolated word lists. It also prepares you to answer simple questions such as **Що тут є?** and **Які це речі?** with full plural phrases. If you study with a partner, one person can name a singular noun and the other gives the plural and adds an adjective: **нова сумка — нові сумки**, **велике дзеркало — великі дзеркала**."
- insert_after: "If you can confidently apply the correct plural endings to both nouns and their descriptive adjectives, you are thoroughly prepared to start handling more complex environments and larger groups of objects in the upcoming lessons."
  content: "One last mini-task: imagine you are helping a teacher tidy the room after class. Say three full sentences: **Ці лампи старі, але чисті. Ті сумки нові. Мої речі тут, а ті дзеркала там.** Then ask a classmate **Які це речі?** and answer with a full phrase such as **Ці речі мої** or **Ті дзеркала великі й чисті**. You can also answer **Які лампи?** with **Ці лампи великі й нові**. This short production step makes you combine noun plurals, adjective plurals, and demonstratives without relying on translation first."
</fixes>