# Retrieval Diagnosis — a1/sounds-letters-and-hello

## Summary
- Concepts present in 40 returned chunks: 6 / 10
- Concepts absent from 40 but present in full corpus: 3 / 10
- Concepts absent from full corpus entirely: 1 / 10

## Verdict
retrieval_bottleneck

## Per-concept table
| Concept | In returned 40? | In full corpus? | Sample grade(s) |
|---|---|---|---|
| syllable_count_rule | yes | yes | 2 |
| larynx_touch_exercise | no | yes | 5 |
| final_voicing | yes | yes | 3 |
| v_to_w_rule | no | yes | 3, 4, 5, 5, 5 |
| yi_letter_two_sounds | yes | yes | 2 |
| ya_yu_ye_dual | yes | yes | 2 |
| milozvuchnist | no | yes | 4, 5, 5, 5, 5 |
| g_ge_history | no | no | — |
| sound_before_letter | yes | yes | 2 |
| vowel_consonant_definition | yes | yes | 2, 1 |

## Recommendation
- Proceed with the retrieval bakeoff issue; the corpus already contains the missing concepts, but the A1 playback did not surface them.
- Retrieval misses: larynx_touch_exercise, v_to_w_rule, milozvuchnist.

## Notes
- Playback returned 40 chunk(s); the script logs the actual count instead of assuming 41.
- Added concept variants after inspecting actual chunk wording:
- syllable_count_rule: у слові стільки складів, скільки голосних звуків, стільки складів, скільки голосних
- larynx_touch_exercise: покладіть пальці на гортань, поклади пальці на гортань, відчули напруження голосових зв'язок
- final_voicing: вимовляються дзвінко, не можна оглушувати, вимовляємо чітко, дзвінкі приголосні звуки в кінці слова і складу
- v_to_w_rule: звук [в] треба вимовляти ніби короткий голосний [ў], у кінці слова: лев [леў], був [буў], у кінці слова, перед приголосним
- yi_letter_two_sounds: буква ї завжди позначає два звуки
- ya_yu_ye_dual: букви я, ю, є позначають, після приголосних букви я, ю, є позначають один звук, позначають два звуки: [йа], [йу], [йе]
- milozvuchnist: милозвучність української мови, забезпечує милозвучність мови, уникаємо збігу голосних або приголосних, чергування у-в та і-й
- g_ge_history: у правописі 1933 року, літеру ґ було вилучено, літеру ґ було повернуто, повернули літеру ґ
- sound_before_letter: букви — це умовні знаки, які позначають звуки мови, букви ми бачимо, читаємо і пишемо, звуки ми чуємо, звуки вимовляємо, букви бачимо
- vowel_consonant_definition: голосні звуки утворюються за допомогою голосу, приголосні звуки утворюються за допомогою голосу та шуму, голос і шум
