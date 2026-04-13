## Linguistic Scan
No Russianisms, Surzhyk, calques, or Russian-only characters (`ы`, `э`, `ё`, `ъ`) found in the provided text.

- Factual grammar error: Section `Моделі дієвідмінювання: казати, пити, боротися` says `боротися` “features a stem change from «от» to «ор».” That is not the correct description of this verb’s present-tense pattern and misteaches the model.
- Factual phonetics error: The same section says `-ться` “always sounds like a long soft sound” and `-шся` “sounds like ... "сся"`. Standard school-textbook treatment is more precise: `-ться` is pronounced `[ц':а]`, and `-шся` is pronounced `[с':а]`.

## Exercise Check
Markers present: `group-sort`, `fill-in`, `quiz`, `match-up`, `unjumble`.

All 5 plan hints have a corresponding marker, and each marker appears after the relevant teaching section. Distribution is acceptable: one after section 1, one after section 2, one after section 3, and two after section 4 where the preposition/case material is taught. No inline DSL exercise blocks are present here, so there is no exercise-answer logic to audit in this content dump.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 10/10 | All four planned H2 sections are present and in the planned order; the module covers motion pairs, conjugation/perfective partners, the three verb models, and motion + prepositions/cases. The plan references are cited explicitly: `Заболотний Grade 6, §39-41` and `Ohoiko, *Verbs of Motion with Prefixes* (2024)`. |
| 2. Linguistic accuracy | 6/10 | Section 3 incorrectly says `боротися` “features a stem change from «от» to «ор»,” and the pronunciation note for `-ться/-шся` is factually wrong/imprecise for a teaching module. |
| 3. Pedagogical quality | 7/10 | The overall PPP flow is good, but the lesson teaches two unsafe rules in a core grammar section: the false `от → ор` explanation for `боротися` and the wrong/imprecise pronunciation rule for reflexive endings. |
| 4. Vocabulary coverage | 10/10 | Required vocabulary is integrated into prose, not dumped as a list: `іти / ходити`, `їхати / їздити`, `летіти / літати`, `піти`, `поїхати`, `казати / кажу`, `пити / п'ю`, `боротися / борюся`, `напрямок`, `рух`. Recommended items also appear: `чергування`, `односпрямований`, `різноспрямований`, `звідки`. |
| 5. Exercise quality | 10/10 | All 5 planned activity types are represented by markers, and each is placed after the relevant teaching content. No inline exercise logic is present here to contradict the prose. |
| 6. Engagement & tone | 9/10 | The module uses concrete travel/daily-life scenarios and mostly keeps a teacherly, explanatory tone. The only notable drag is one awkward exchange in the opening dialogue. |
| 7. Structural integrity | 10/10 | Clean markdown structure, all planned sections present, no stray formatting artifacts beyond expected injection markers, and pipeline word count is `2907`, which is above the `2000` target. |
| 8. Cultural accuracy | 10/10 | The module treats Ukrainian as its own system, uses Ukrainian places/examples naturally (`Київ`, `Львів`, `Україна`), and avoids Russian-centric framing. |
| 9. Dialogue & conversation quality | 8/10 | The module includes multi-turn dialogues, but the airport dialogue ends with a non-answer: `А батьки вже вдома?` is answered with `Так, ми пішли з квартири...`, which shifts subject and breaks coherence. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `Моделі дієвідмінювання: казати, пити, боротися` — `The verb **боротися / борюся** (to fight/struggle — reflexive model) is an excellent example of a complex reflexive verb because it also features a stem change from «от» to «ор».`  
Issue: This is the wrong grammatical explanation for `боротися`. It misdescribes the verb’s present-tense model and teaches a false alternation.  
Fix: Replace that sentence with a correct description of `боротися` as a first-conjugation reflexive model and anchor it in the actual paradigm `борюся, борешся, бореться, боремося, боретеся, борються`.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `Моделі дієвідмінювання: казати, пити, боротися` — `Комбінації «-ться» і «-шся» мають особливу вимову...` and the English gloss `The letter combination "-ться" always sounds like a long soft sound...`  
Issue: The phonetic explanation is not accurate enough for teaching. Standard school treatment is specific: `-ться` is pronounced `[ц':а]`, and `-шся` is pronounced `[с':а]`.  
Fix: Replace the vague explanation with the precise pronunciation rule in both the Ukrainian text and the English gloss.

[DIALOGUE & CONVERSATION QUALITY] [SEVERITY: major]  
Location: `Три пари дієслів руху` — `> — **Друг:** Класно! А батьки вже вдома?` / `> — **Пасажир:** Так, ми пішли з квартири о третій годині, а вони залишилися.`  
Issue: The answer does not directly answer the question and shifts from `батьки` to `ми`, which makes the exchange sound broken.  
Fix: Make the reply explicitly answer that the parents are already home, then keep the motion-verb example.

## Verdict: REVISE
REVISE. The module has two critical language-teaching errors in the grammar section and one major dialogue-coherence issue. That blocks PASS even though plan coverage, vocabulary coverage, structure, and exercise-marker placement are strong.

<fixes>
- find: "The verb **боротися / борюся** (to fight/struggle — reflexive model) is an excellent example of a complex reflexive verb because it also features a stem change from «от» to «ор»."
  replace: "The verb **боротися / борюся** (to fight/struggle — reflexive model) is an excellent example of a reflexive verb of the first conjugation. Learn its present-tense pattern as **борюся, борешся, бореться, боремося, боретеся, борються**."

- find: "Зверніть особливу увагу на вимову цих слів! Комбінації «-ться» і «-шся» мають особливу вимову, тому ці форми варто слухати й повторювати як готові моделі. Це допоможе зробити ваше мовлення більш природним."
  replace: "Зверніть особливу увагу на вимову цих слів! У дієсловах 3-ї особи «-ться» вимовляємо як [ц':а], а у формах 2-ї особи «-шся» — як [с':а]. Тому ці форми варто слухати й повторювати як готові моделі."

- find: "Pay special attention to the pronunciation of these words! The letter combination \"-ться\" always sounds like a long soft sound. The letter combination \"-шся\" also has its own special pronunciation and sounds like a long soft sound \"сся\". This is a very important phonetic rule of the Ukrainian language that makes your speech more natural."
  replace: "Pay special attention to the pronunciation of these words! In standard pronunciation, \"-ться\" is pronounced [ц':а], and \"-шся\" is pronounced [с':а]. This is a useful rule to practice aloud with full verb forms."

- find: "> — **Пасажир:** Так, ми пішли з квартири о третій годині, а вони залишилися. *(Yes, we left the apartment at three o'clock, and they stayed.)*"
  replace: "> — **Пасажир:** Так, вони вже вдома. Ми пішли з квартири о третій годині, а вони залишилися вдома. *(Yes, they are already at home. We left the apartment at three o'clock, and they stayed home.)*"
</fixes>