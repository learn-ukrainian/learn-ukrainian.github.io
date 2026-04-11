## Linguistic Scan
No linguistic errors found.

## Exercise Check
The plan lists 4 activities: `fill-in`, `quiz`, `group-sort`, and `error-correction`. All 4 markers are present. However, `<!-- INJECT_ACTIVITY: group-sort -->` is placed directly after Part 1. The `group-sort` activity asks learners to sort verb forms, including the imperative. Imperative is not taught until Part 2. Placing an exercise that tests imperative before Part 2 violates the pedagogical progression. The marker should be moved to after Part 2.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 10/10 | Covers all requested sections and grammar rules. All required vocabulary ("контрольна точка", "помилка", "наказовий спосіб", etc.) is integrated naturally. Self-assessment questions are present. |
| 2. Linguistic accuracy | 10/10 | Excellent grammar explanations. Effectively explains the nuance of perfective/imperfective aspect. Correctly points out and corrects common Russianisms (e.g., "на автобусі" vs "автобусом", "давай підемо" vs "ходімо"). |
| 3. Pedagogical quality | 9/10 | Clear examples and strong PPP flow. However, the `group-sort` exercise is placed before its required concept (imperative) is taught. |
| 4. Vocabulary coverage | 10/10 | Incorporates all required words in a meaningful context. |
| 5. Exercise quality | 8/10 | The `group-sort` marker is misplaced (appears after Part 1, but tests imperative which is in Part 2). |
| 6. Engagement & tone | 10/10 | The teacher persona is encouraging and provides excellent, culturally grounded context without excessive gamification. |
| 7. Structural integrity | 8/10 | The conclusion contains a dangling/incomplete sentence: `If you can answer "так" (yes) to all of them, ` which abruptly stops before the bulleted list. |
| 8. Cultural accuracy | 10/10 | Excellent contrast with English and Russian constructions. Explains authentic Ukrainian properly. |
| 9. Dialogue & conversation quality | 8/10 | In the second dialogue, Iryna says she is going to the Carpathians with Andriy ("ми поїдемо"), but then says "Ідіть до лісу обережно" (You go to the forest carefully). This is a logical contradiction; she should use the 1st person plural ("Будьмо обережні" or "Ходімо") since she is part of the group. |

## Findings
[Pedagogical quality] [major]
Location: `*   **Вони житимуть у Києві.** (They will live in Kyiv.)\n\n<!-- INJECT_ACTIVITY: group-sort -->\n\n## Частина 2: Дієслова руху та наказовий спосіб (Part 2: Motion Verbs and Imperatives)`
Issue: The `group-sort` activity tests the imperative mood, but is placed before the imperative is taught in Part 2.
Fix: Move `<!-- INJECT_ACTIVITY: group-sort -->` to after Part 2.

[Structural integrity] [major]
Location: `Ask yourself the following questions. If you can answer "так" (yes) to all of them, \n\n*   Чи можу я обрати правильний вид дієслова у минулому часі?`
Issue: Dangling/incomplete English sentence at the end of the text.
Fix: Complete the sentence with `you are ready for A2.7!`.

[Dialogue & conversation quality] [major]
Location: `> **Ірина:** Зрозуміла. Ідіть до лісу обережно. Друзі, будьмо готові! *(Understood. Go to the forest carefully. Friends, let's be ready!)*`
Issue: Iryna says "Ідіть" (2nd person plural imperative, meaning "You go") to her friends, but she is going on the trip with them. This breaks the logic of the dialogue.
Fix: Change "Ідіть до лісу обережно" to "Будьмо обережні в лісі" (Let's be careful in the forest) to match her inclusion in the group.

## Verdict: REVISE
The module contains excellent explanations and a strong pedagogical flow, but a dangling sentence, a logical contradiction in the dialogue, and a misplaced exercise marker require a targeted revision.

<fixes>
- find: "*   **Вони житимуть у Києві.** (They will live in Kyiv.)\n\n<!-- INJECT_ACTIVITY: group-sort -->\n\n## Частина 2: Дієслова руху та наказовий спосіб"
  replace: "*   **Вони житимуть у Києві.** (They will live in Kyiv.)\n\n## Частина 2: Дієслова руху та наказовий спосіб"
- find: "*   **Друже, будь обережним!** (Friend, be careful!)\n\n<!-- INJECT_ACTIVITY: fill-in -->\n\n## Частина 3: Комплексні завдання"
  replace: "*   **Друже, будь обережним!** (Friend, be careful!)\n\n<!-- INJECT_ACTIVITY: fill-in -->\n\n<!-- INJECT_ACTIVITY: group-sort -->\n\n## Частина 3: Комплексні завдання"
- find: "Ask yourself the following questions. If you can answer \"так\" (yes) to all of them, \n\n*   Чи можу я обрати"
  replace: "Ask yourself the following questions. If you can answer \"так\" (yes) to all of them, you are ready for A2.7!\n\n*   Чи можу я обрати"
- find: "> **Ірина:** Зрозуміла. Ідіть до лісу обережно. Друзі, будьмо готові! *(Understood. Go to the forest carefully. Friends, let's be ready!)*"
  replace: "> **Ірина:** Зрозуміла. Будьмо обережні в лісі. Друзі, будьмо готові! *(Understood. Let's be careful in the forest. Friends, let's be ready!)*"
</fixes>
