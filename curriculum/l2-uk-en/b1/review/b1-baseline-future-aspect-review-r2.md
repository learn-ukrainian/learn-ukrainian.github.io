## Linguistic Scan
No linguistic errors found regarding Russianisms, Surzhyk, Calques, or Paronyms.

## Exercise Check
Found 7 `INJECT_ACTIVITY` markers, but the plan only dictates 6. 
The extra marker `<!-- INJECT_ACTIVITY: fill-in-simple-future -->` in Section 2 is redundant, does not map to a hint, and risks breaking pipeline validation. It must be removed.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | The module covers all required sections, but missed the "Practice table with 5 verb pairs for full conjugation" in the "Дієвідмінювання у майбутньому часі" section, and skipped the "dialogue between two friends planning a trip" in the "Складена форма" section. |
| 2. Linguistic accuracy | 7/10 | A critical error exists in explaining the synthetic future formation: the text instructs learners to take the full infinitive and add "-тиму" (which would produce "працюватитиму"), contradicting its own claim that the ending starts with "м". |
| 3. Pedagogical quality | 9/10 | The explanation of why perfective verbs lack a present tense is excellent and intuitive. However, the contradictory rule for forming the synthetic future creates severe pedagogical confusion. |
| 4. Vocabulary coverage | 10/10 | All required vocabulary is seamlessly integrated into the prose in a natural way. |
| 5. Exercise quality | 8/10 | The writer included an extra `fill-in-simple-future` marker not requested by the plan's `activity_hints`, causing a mismatch. |
| 6. Engagement & tone | 10/10 | The tone is warm, encouraging, and uses excellent metaphors (like the bridge metaphor for aspect) without relying on gamified corporate filler. |
| 7. Structural integrity | 10/10 | All Markdown headings match the plan exactly. The word count (4759) well exceeds the 4000-word target. |
| 8. Cultural accuracy | 10/10 | Demonstrates deep understanding of Ukrainian worldview (the focus on result vs process). Authentic examples (Kharkiv university, Taras Shevchenko park). |
| 9. Dialogue & conversation quality | 9/10 | Dialogues are natural and multi-turn, though one required dialogue was omitted. |

## Findings
[1. Plan adherence] [major]
Location: Section "Дієвідмінювання у майбутньому часі", end of the third paragraph: "Проста форма майбутнього часу працює за ідентичними правилами."
Issue: The plan explicitly requires a "Practice table with 5 verb pairs for full conjugation", but the writer only provided inline paragraphs with scattered examples.
Fix: Add a Markdown table with the conjugation of 5 verb pairs at the end of the paragraph about simple future rules.

[1. Plan adherence] [major]
Location: Section "Складена (аналітична) форма майбутнього часу", end of the section: "Ви будете гарантовано чути конструкції на зразок «я буду робити» чи «ми будемо чекати» скрізь."
Issue: The plan requires a "Reading practice: dialogue between two friends planning a trip, using all three future forms." The writer used the main `dialogue_situations` (charity concert) here but completely omitted the required trip planning dialogue.
Fix: Insert the missing dialogue between two friends planning a trip right before the final summary paragraph of this section.

[2. Linguistic accuracy] [critical]
Location: Section "Складна (синтетична) форма майбутнього часу": "Ось повна і незмінна схема для всіх дієслів: я -тиму (I will), ти -тимеш (you will)..."
Issue: The text tells learners to take the full infinitive (e.g., "працювати") and add "-тиму". This is linguistically incorrect and would result in "працюватитиму". The correct endings to add to the full infinitive start with "м" (-му, -меш, etc.), which the text ironically states in the preceding sentence.
Fix: Change "-тиму", "-тимеш", etc. to "-му", "-меш", "-ме", "-мемо", "-мете", "-муть" so it correctly attaches to the full infinitive.

[5. Exercise quality] [minor]
Location: Section "Проста форма майбутнього часу", at the very end.
Issue: The writer inserted an unauthorized `<!-- INJECT_ACTIVITY: fill-in-simple-future -->` marker that does not exist in the plan's `activity_hints`.
Fix: Delete the extra marker.

## Verdict: REVISE
The module is rich, engaging, and well-written, but it contains a critical linguistic rule error regarding the synthetic future formation that will thoroughly confuse learners. It also missed two explicit plan requirements (a practice table and a specific dialogue). Applying the fixes below will bring it into full compliance.

<fixes>
- find: "Ці закінчення завжди починаються з літери «м». Ось повна і незмінна схема для всіх дієслів: я -тиму (I will), ти -тимеш (you will), він, вона, воно -тиме (he/she/it will). У множині ми продовжуємо додавати ці закінчення: ми -тимемо (we will), ви -тимете (you [pl] will), вони -тимуть (they will)."
  replace: "Ці закінчення завжди починаються з літери «м». Ось повна і незмінна схема для всіх дієслів: я -му (I will), ти -меш (you will), він, вона, воно -ме (he/she/it will). У множині ми продовжуємо додавати ці закінчення: ми -мемо (we will), ви -мете (you [pl] will), вони -муть (they will)."
- find: "Проста форма майбутнього часу працює за ідентичними правилами."
  replace: "Проста форма майбутнього часу працює за ідентичними правилами.\n\nОсь таблиця для порівняння п'яти корисних видових пар у першій особі однини (я):\n\n| Інфінітив (док. / недок.) | Проста (доконана) | Складна (недоконана) | Складена (недоконана) |\n|---|---|---|---|\n| принести / носити | я принесу | я носитиму | я буду носити |\n| прочитати / читати | я прочитаю | я читатиму | я буду читати |\n| зробити / робити | я зроблю | я робитиму | я буду робити |\n| посидіти / сидіти | я посиджу | я сидітиму | я буду сидіти |\n| запросити / просити | я запрошу | я проситиму | я буду просити |"
- find: "Ви будете гарантовано чути конструкції на зразок «я буду робити» чи «ми будемо чекати» скрізь."
  replace: "Прочитайте ще один короткий діалог про подорож, де друзі вільно поєднують усі три форми. Зверніть увагу, чому вони обирають кожну з них:\n> — **Максим:** Куди ми поїдемо (проста) у відпустку? Я буду шукати (складена) готелі.\n> — **Оксана:** Я перевірю (проста) ціни на літаки. Ми відпочиватимемо (складна) на морі цілий тиждень!\n\nВи будете гарантовано чути конструкції на зразок «я буду робити» чи «ми будемо чекати» скрізь."
- find: "<!-- INJECT_ACTIVITY: fill-in-simple-future -->\n\n## Складна (синтетична) форма майбутнього часу"
  replace: "## Складна (синтетична) форма майбутнього часу"
</fixes>
