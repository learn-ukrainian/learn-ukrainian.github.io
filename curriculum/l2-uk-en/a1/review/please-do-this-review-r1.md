## Linguistic Scan
2 linguistic errors found (calques): "Добрий ранок" (instead of "Доброго ранку") and "Відкрий двері" (instead of "Відчини двері").

## Exercise Check
- `<!-- INJECT_ACTIVITY: group-sort-imperative-register -->` - Matches plan hint 3. Placed correctly after the register explanation.
- `<!-- INJECT_ACTIVITY: fill-in-imperative-formation -->` - Matches plan hint 1. Placed correctly after the formation explanation.
- `<!-- INJECT_ACTIVITY: quiz-polite-choice -->` - Matches plan hint 2. Placed correctly after the formation explanation.
- `<!-- INJECT_ACTIVITY: fill-in-contextual-names -->` - Matches plan hint 4. Placed correctly at the end of the summary.

All 4 markers are correctly placed and map perfectly to the plan's `activity_hints`.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | Covers all required points, but the recommended vocabulary word `показати` is missing from the prose entirely. |
| 2. Linguistic accuracy | 8/10 | Contains two common calques: `Добрий ранок` (should be "Доброго ранку") and `Відкрий двері` (should be "Відчини двері"). |
| 3. Pedagogical quality | 6/10 | The rules for forming the imperative for Group I and II verbs are factually inaccurate and contradict the examples provided. "писати" does not form "пиши" by simply removing "-ти" and adding "-й". Reflexive verbs ("дивитися" -> "дивись") are completely ignored in the Group II rule. |
| 4. Vocabulary coverage | 9/10 | All required vocabulary is used naturally, but the recommended word `показати` was omitted. |
| 5. Exercise quality | 10/10 | All exercises map perfectly to the plan and are placed correctly after the corresponding concepts. |
| 6. Engagement & tone | 10/10 | Tone is warm and encouraging, using natural classroom and daily-life situations without generic filler. |
| 7. Structural integrity | 10/10 | Word count is 1525 (exceeds 1200 target). All headers and sections are correctly structured. |
| 8. Cultural accuracy | 10/10 | Uses appropriate and natural Ukrainian settings, names, and communicative norms. |
| 9. Dialogue & conversation quality | 10/10 | Dialogues are natural, correctly formatted, and effectively demonstrate the difference in register (ти vs ви). |

## Findings
[2. Linguistic accuracy] [critical]
Location: `> **Вчитель:** Добрий ранок! **Відкрийте підручники, будь ласка. Читайте текст.** *(Good morning! Open the textbooks, please. Read the text.)*`
Issue: "Добрий ранок" is a calque. The standard Ukrainian greeting is "Доброго ранку".
Fix: Change to "Доброго ранку!".

[2. Linguistic accuracy] [critical]
Location: `> **Тренер:** **Натягни сітку! Поклади рушники на лавку! Відкрий двері!** *(Tighten the net! Put the towels on the bench! Open the doors!)*`
Issue: "Відкрий двері" is a calque from Russian. In Ukrainian, doors and windows are opened with the verb "відчиняти", not "відкривати".
Fix: Change to "Відчини двері!".

[3. Pedagogical quality] [critical]
Location: `For many common verbs belonging to Group I that end in **-ати**, the rule is wonderfully simple. You remove the **-ти** ending to find the stem, and then you add the letter **-й**. This creates a crisp, one- or two-syllable command.`
Issue: This rule is factually incorrect for verbs like "писати" which form "пиши" (by adding "-и" to the present tense stem "пиш-"), not "писай". The stated rule contradicts the example ("писати -> пиши") given immediately below it.
Fix: Update the rule explanation to accurately reflect both patterns (adding "-й" or "-и" depending on the stem).

[3. Pedagogical quality] [critical]
Location: `For verbs in Group II, which often end in **-ити**, the process is slightly different. Instead of adding a completely new sound, you usually drop the final infinitive ending and are left with a stem ending in **-и**. The stress often plays a key role here, landing clearly on that final vowel to give the command its punchy rhythm.`
Issue: This rule ("drop the final infinitive ending") does not account for reflexive verbs like "дивитися" (which becomes "дивись", not "диви"). The explanation is incomplete and misleading.
Fix: Update the explanation to note that the ending is replaced with "-и", and for reflexive verbs it becomes "-ись".

## Verdict: REVISE
The module requires revision due to critical factual errors in the grammar explanations for imperative formation, which contradict the provided examples. Additionally, two common calques need to be corrected to ensure linguistic accuracy.

<fixes>
- find: "> **Вчитель:** Добрий ранок! **Відкрийте підручники, будь ласка. Читайте текст.** *(Good morning! Open the textbooks, please. Read the text.)*"
  replace: "> **Вчитель:** Доброго ранку! **Відкрийте підручники, будь ласка. Читайте текст.** *(Good morning! Open the textbooks, please. Read the text.)*"
- find: "> **Тренер:** **Натягни сітку! Поклади рушники на лавку! Відкрий двері!** *(Tighten the net! Put the towels on the bench! Open the doors!)*"
  replace: "> **Тренер:** **Натягни сітку! Поклади рушники на лавку! Відчини двері!** *(Tighten the net! Put the towels on the bench! Open the doors!)*"
- find: "For many common verbs belonging to Group I that end in **-ати**, the rule is wonderfully simple. You remove the **-ти** ending to find the stem, and then you add the letter **-й**. This creates a crisp, one- or two-syllable command."
  replace: "For many common verbs belonging to Group I that end in **-ати**, the pattern is wonderfully simple. You remove the **-ти** ending and add the letter **-й**. For verbs that change their stem in the present tense, you usually add **-и**."
- find: "For verbs in Group II, which often end in **-ити**, the process is slightly different. Instead of adding a completely new sound, you usually drop the final infinitive ending and are left with a stem ending in **-и**. The stress often plays a key role here, landing clearly on that final vowel to give the command its punchy rhythm."
  replace: "For verbs in Group II, which often end in **-ити**, the process is slightly different. You usually replace the final infinitive ending with **-и**. For reflexive verbs, the ending becomes **-ись**. The stress often plays a key role here, landing clearly on that final vowel to give the command its punchy rhythm."
</fixes>
