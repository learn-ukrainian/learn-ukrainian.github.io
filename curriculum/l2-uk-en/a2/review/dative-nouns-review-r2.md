## Linguistic Scan
No Russianisms, surzhyk, calques, paronyms, or forbidden Russian characters (`ы`, `э`, `ё`, `ъ`) found.

[CRITICAL] Masculine dative ending selection is taught inaccurately in the masculine section. The module says: “Always look at the last letter of the dictionary form. Hard consonants get **-ові**, soft and hissing consonants get **-еві**, and vowels get **-єві**.” The school-textbook pattern is group/stem-based, not a simple last-letter rule.

## Exercise Check
Searched the embedded content: 5 `<!-- INJECT_ACTIVITY:` markers, 0 inline `:::quiz` blocks, 0 inline `:::fill-in` blocks.

Marker inventory and placement are correct:
- `fill-in-dative-masculine` appears after the masculine section.
- `quiz-feminine-alternation` appears after the feminine section.
- `group-sort-dative-gender` appears after the neuter section.
- `match-up-verb-phrases` and `unjumble-dative-syntax` appear after the sentence/syntax section.

Marker IDs align with the 5 plan `activity_hints`. No exercise-marker issues found in the visible content. Actual YAML distractor logic is not visible here, so only placement/alignment can be assessed.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 10/10 | All planned sections appear in order, the post-office dialogue is present, the genitive contrast is present, and plan vocabulary/references are integrated in prose: “друга відміна,” “чергування,” “одержувач,” `немовляті`, plus citations of “Заболотний,” “Глазова,” and “Кравцова.” |
| 2. Linguistic accuracy | 7/10 | Critical grammar-teaching error: “Always look at the last letter of the dictionary form. Hard consonants get **-ові**...” This is not the textbook rule for choosing `-ові/-еві/-єві`. |
| 3. Pedagogical quality | 8/10 | Example density is strong, but the masculine explanation teaches the wrong heuristic in the core rule box, which is high-impact for learners. |
| 4. Vocabulary coverage | 10/10 | Required vocabulary is used naturally across the prose: `студентові`, `сестрі`, `другові`, `подарувати`, `показати`, `написати`, `розповісти`, `пояснити`, `відповісти`, `закінчення`; recommended items also appear. |
| 5. Exercise quality | 9/10 | All 5 planned activity types have corresponding markers and each marker follows the relevant teaching section. |
| 6. Engagement & tone | 9/10 | The voice is teacherly and clear: “Let us look at...,” “Now that you know...,” with substantial example support rather than empty celebration. |
| 7. Structural integrity | 10/10 | Clean H2 structure, correct section order, no stray artifacts, and pipeline word count is 2761, which is above target. |
| 8. Cultural accuracy | 10/10 | No Russian-centric framing, no colonial comparison language, and no cultural inaccuracies surfaced. |
| 9. Dialogue & conversation quality | 6/10 | The only dialogue is very thin and label-like: “Кому вони?” / “Студентові Петренку — підручник. Сестрі Олені — листівка...” It reads more like a case drill than a natural exchange. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: “How do we choose between the different endings in the first group? ... Always look at the last letter of the dictionary form. Hard consonants get **-ові**, soft and hissing consonants get **-еві**, and vowels get **-єві**.”  
Issue: This teaches the choice of `-ові/-еві/-єві` by the last letter of the dictionary form, which is inaccurate and overgeneralized. The school-textbook rule is based on stem/group type, with `-єві` after a vowel/apostrophe and `-еві` for soft/mixed stems after a consonant.  
Fix: Replace the explanation and grammar box with a stem/group-based rule.

[DIALOGUE & CONVERSATION QUALITY] [SEVERITY: major]  
Location: “— **Працівник пошти:** Кому вони? ... — **Відправник:** Студентові Петренку — підручник. Сестрі Олені — листівка. А дитині — іграшка.”  
Issue: The dialogue is too compressed and transactional; the reply is a list of labels rather than a natural postal interaction.  
Fix: Replace it with a slightly fuller multi-turn exchange that keeps the same dative targets but sounds like spoken language.

## Verdict: REVISE
REVISE. There is one critical grammar-teaching error in the masculine ending rule, and the dialogue quality is below ship standard. Dimensions 2, 3, and 9 are below 9, and the critical error requires deterministic fixes.

<fixes>
- find: |-
    How do we choose between the different endings in the first group? The choice depends on the final consonant of the noun stem. If the noun ends in a hard consonant, we use the **-ові** ending. For instance, the word for friend becomes **другові**, and the word for son becomes **синові**. If the noun ends in a soft consonant or a hissing sound, we use the **-еві** ending. The word for teacher becomes **вчителеві**, and the word for comrade becomes **товаришеві**. Finally, if the noun stem ends in a vowel, we use the **-єві** ending. The name Andriy becomes **Андрієві**.
  replace: |-
    How do we choose between the different endings in the first group? The choice depends on the stem type, not simply on the last letter of the dictionary form. Hard-group masculine nouns usually take the **-ові** ending, for example **другові** and **синові**. Soft-group and mixed-group nouns after a consonant usually take **-еві**, for example **вчителеві**, **товаришеві**, and **лікареві**. After a vowel or an apostrophe, nouns usually take **-єві**, for example **Андрієві**.
- find: |-
    :::info
    **Grammar box**
    Always look at the last letter of the dictionary form. Hard consonants get **-ові**, soft and hissing consonants get **-еві**, and vowels get **-єві**.
    :::
  replace: |-
    :::info
    **Grammar box**
    Do not rely only on the last letter of the dictionary form. Use the stem type: hard-group masculine nouns usually take **-ові**, soft-group and mixed-group nouns after a consonant usually take **-еві**, and forms after a vowel or apostrophe usually take **-єві**.
    :::
- find: |-
    > — **Відправник:** Доброго дня. Я хочу відправити ці пакунки. *(Good day. I want to send these packages.)*
    > — **Працівник пошти:** Кому вони? *(Who are they for?)*
    > — **Відправник:** Студентові Петренку — підручник. Сестрі Олені — листівка. А дитині — іграшка. *(To student Petrenko — a textbook. To sister Olena — a postcard. And to the child — a toy.)*
  replace: |-
    > — **Відправник:** Доброго дня. Я хочу відправити три пакунки. *(Good day. I want to send three packages.)*
    > — **Працівник пошти:** Добре. Кому вони призначені? *(All right. Who are they addressed to?)*
    > — **Відправник:** Підручник — студентові Петренку, листівка — сестрі Олені, а іграшка — дитині. *(A textbook is for student Petrenko, a postcard is for sister Olena, and a toy is for the child.)*
    > — **Працівник пошти:** Чудово, зараз усе оформимо. *(Great, I’ll process everything now.)*
</fixes>