## Linguistic Scan
Found 1 critical linguistic error:
- "біль горла", "біль спини", "біль голови" are unnatural phrasing used to force the Genitive case. In Ukrainian, physical pain location is expressed with the Locative case: "біль у горлі", "біль у спині". Teaching these unnatural calques as a core grammatical pattern is a critical linguistic and pedagogical error.

## Exercise Check
- All four `<!-- INJECT_ACTIVITY: ... -->` markers are present.
- They perfectly match the plan's `activity_hints` in both type and focus.
- The markers correctly test what was just taught (market dialogue, complaints, remedies, consolidation).
- Markers 3 and 4 are clustered together at the end of Section 3, which is logically acceptable given it is a consolidation section, but slightly reduces pacing.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | Missed specific outline phrases: `нормально`, `Як давно?`, `Чи є алергія на ліки?`, `дбати про здоров'я`, and `з ринку`. |
| 2. Linguistic accuracy | 6/10 | Critical error: Forces unnatural phrasing ("біль горла", "біль спини") to teach Genitive case, contradicting standard Ukrainian usage ("біль у горлі"). |
| 3. Pedagogical quality | 6/10 | Teaches a factually incorrect linguistic pattern by inventing unnatural Genitive pain examples instead of using valid Locative constructions. |
| 4. Vocabulary coverage | 10/10 | All required and recommended words (ринок, кілограм, пляшка, здоров'я, помідор, etc.) are included and used naturally. |
| 5. Exercise quality | 10/10 | Exercise markers perfectly match the plan's hints and logically test the relevant grammatical skills in context. |
| 6. Engagement & tone | 9/10 | Engaging dialogues and culturally relevant market interactions. Tone is instructional, concrete, and natural. |
| 7. Structural integrity | 7/10 | The deterministic word count (3131 words) vastly overshoots the target budget (2000 words). |
| 8. Cultural accuracy | 10/10 | Excellent depiction of Ukrainian markets (tasting food, buying "десяток яєць") and authentic pharmacy etiquette. |
| 9. Dialogue & conversation quality | 10/10 | Dialogues are realistic, culturally appropriate, and effectively demonstrate the target grammar in multi-turn exchanges. |

## Findings
[1. Plan adherence] [Major]
Location: Section 1 ("If a price seems high, it is **дорого** (expensive), but a good deal is **дешево** (cheap).")
Issue: Missing the requested vocabulary point `нормально` for price expressions.
Fix: Add `нормально` to the explanation and examples.

[1. Plan adherence] [Major]
Location: Section 2 (Doctor's questions in the dialogue and explanation)
Issue: Missing the doctor's questions `Як давно?` and `Чи є алергія на ліки?` from the plan.
Fix: Insert these questions into the doctor-patient dialogue.

[1. Plan adherence] [Major]
Location: Section 3 ("The Genitive case is also essential for describing healthy habits and daily dietary choices.")
Issue: Missing the phrase `дбати про здоров'я` from the everyday health phrases point.
Fix: Add the phrase to the healthy habits introduction.

[1. Plan adherence] [Major]
Location: Section 3 consolidation ("Finally, you use it to show purpose, origin, or a specific remedy: ефективні ліки від кашлю...")
Issue: Missing the consolidation example `з ринку` requested by the plan.
Fix: Include `з ринку` in the consolidation examples.

[2. Linguistic accuracy] [Critical]
Location: Section 2 ("When describing pain, you will often name body parts... У мене сильний біль горла... Лікар оглядає пацієнта через постійний біль спини...")
Issue: The text actively teaches an unnatural grammatical calque ("біль горла", "біль спини") to force the Genitive case. In Ukrainian, physical pain location requires the Locative case ("біль у горлі", "біль у спині").
Fix: Rewrite the paragraph to teach other valid Genitive medical structures (like "напад кашлю", "симптом хвороби") and "немає болю" instead of forced body part Genitives.

[7. Structural integrity] [Major]
Location: Entire document
Issue: The generated word count (3131 words) is significantly outside the target range of 2000 words.
Fix: Update the word_target in metadata to match the actual length, or manually trim the content.

## Verdict: REVISE
The module contains a critical linguistic and pedagogical error by explicitly teaching unnatural Ukrainian constructions ("біль горла", "біль спини") to satisfy a grammatical constraint. It also missed several specific phrases mandated by the plan outline and significantly overshot the word count. It must be revised to correct the false grammatical teachings and integrate the missing points.

<fixes>
- find: "If a price seems high, it is **дорого** (expensive), but a good deal is **дешево** (cheap)."
  replace: "If a price seems high, it is **дорого** (expensive), a fair price is **нормально** (normal/fine), and a good deal is **дешево** (cheap)."
- find: "На цьому ринку дуже **дешево** купувати овочі (it is very cheap to buy vegetables at this market)."
  replace: "На цьому ринку дуже **дешево** купувати овочі (it is very cheap to buy vegetables at this market).\nЦіна на ці помідори — це цілком **нормально** (the price for these tomatoes is normal)."
- find: "> — **Лікар:** Зрозуміло. А чи є у вас висока температура? *(Understood. And do you have a high fever?)*\n> — **Пацієнт:** Ні, температури **немає**, але я відчуваю слабкість. *(No, there is no fever, but I feel weakness.)*"
  replace: "> — **Лікар:** Зрозуміло. **Як давно** це почалося? А чи є у вас висока температура? *(Understood. How long ago did this start? And do you have a high fever?)*\n> — **Пацієнт:** Ні, температури **немає**, але я відчуваю слабкість. *(No, there is no fever, but I feel weakness.)*\n> — **Лікар:** **Чи є алергія на ліки**? *(Do you have an allergy to medicine?)*\n> — **Пацієнт:** Ні, немає. *(No, I don't.)*"
- find: "The Genitive case is also essential for describing healthy habits and daily dietary choices. The preposition **для** (for) shows purpose, while **без** (without) shows absence."
  replace: "The Genitive case is also essential for describing healthy habits, such as when you want to **дбати про здоров'я** (take care of health). The preposition **для** (for) shows purpose, while **без** (without) shows absence."
- find: "Finally, you use it to show purpose, origin, or a specific remedy: ефективні **ліки від кашлю** (effective medicine for a cough)."
  replace: "Finally, you use it to show purpose, origin, or a specific remedy: свіжі фрукти **з ринку** (fresh fruits from the market) or ефективні **ліки від кашлю** (effective medicine for a cough)."
- find: "When describing pain, you will often name body parts. If you are pointing out where it hurts, you might use constructions that require the Genitive. For example, saying \"pain of the throat\" uses the Genitive form of **горло** (throat) — **горла**. The word **спина** (back) becomes **спини**, and **голова** (head) becomes **голови**. Doctors also use formal medical phrases like **біль у ділянці серця** (pain in the heart area), where **серце** (heart) is in the Genitive: **серця**. Conversely, if you want to report that a pain has stopped, you use **немає** with the Genitive of **біль** (pain) — **немає болю** (no pain).\n\n**Читаємо українською:**\nУ мене сильний біль **горла** (I have a strong pain of the throat). Лікар оглядає пацієнта через постійний біль **спини** (The doctor examines the patient because of constant back pain). Чи є у вас біль у ділянці **серця**? (Do you have pain in the heart area?). Після таблетки у мене більше **немає болю** (After the pill I have no more pain). Вона часто скаржиться на біль **голови** (She often complains about pain of the head)."
  replace: "When describing your condition, you might use phrases where one noun describes another, requiring the Genitive case. For example, **напад кашлю** (an attack of coughing), where **кашель** (cough) is in the Genitive: **кашлю**. Doctors use formal medical phrases like **біль у ділянці серця** (pain in the heart area), where **серце** (heart) is in the Genitive: **серця**. Conversely, if you want to report that a pain has stopped, you use **немає** with the Genitive of **біль** (pain) — **немає болю** (no pain), or **немає симптомів** (no symptoms).\n\n**Читаємо українською:**\nУ нього вночі був сильний напад **кашлю** (He had a strong attack of coughing at night). Лікар оглядає пацієнта через симптоми **хвороби** (The doctor examines the patient because of symptoms of the illness). Чи є у вас біль у ділянці **серця**? (Do you have pain in the heart area?). Після таблетки у мене більше **немає болю** (After the pill I have no more pain). Вона каже, що у неї **немає симптомів** (She says that she has no symptoms)."
</fixes>
