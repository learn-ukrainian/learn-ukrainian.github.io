## Linguistic Scan
- **Critical:** In `Планування`, the grammar note is incomplete: `"Notice the vowel ending change for feminine days. The days **середа**, **п'ятниця**, and **субота** change..."` omits **неділя → неділю**, even though the module immediately teaches `**в неділю**`.

## Exercise Check
- Marker inventory matches the 3 plan hints: `fill-in-schedule-time`, `match-invitations`, `fill-in-weekly-plan`.
- Placement is correct: the schedule/time marker comes after day/time + future teaching, the invitation marker comes after invitation phrases, and the weekly-plan marker comes after the `Мій тиждень` model/template.
- No inline DSL exercise blocks appear in the module.
- No marker-placement issues found. Actual YAML distractor logic is not visible here, so only marker alignment can be checked.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All planned H2 sections are present and the required vocabulary appears in prose, but the planned reference `State Standard 2024, §4.2.4.1` is not cited anywhere in the module (`0` matches for `State Standard` / `§4.2.4.1`). |
| 2. Linguistic accuracy | 8/10 | No Russianisms/Surzhyk/paronym issues surfaced in the prose, but the grammar note on feminine day forms is inaccurate by omission: it lists `середа`, `п'ятниця`, `субота` and leaves out `неділя → неділю`. |
| 3. Pedagogical quality | 8/10 | The module has many examples and follows dialogue → explanation → practice, but the opening English exposition is filler-heavy: `"Arranging a weekend get-together..."` delays instruction without adding much linguistic value. |
| 4. Vocabulary coverage | 9/10 | Required vocabulary is present in prose (`план`, `тиждень`, `вільний/вільна`, `зустріч`, `відпочивати`, `прибирати`, `вечірка`), and recommended items like `зустрінемося`, `з задоволенням`, `на жаль`, `допізна`, `звичайно`, `квартира`, `кіно`, `вчити` are also used. |
| 5. Exercise quality | 9/10 | Three markers are present and aligned to the taught material; `match-invitations` is placed directly after invitation language, and `fill-in-weekly-plan` follows the weekly-plan model. No visible exercise-logic errors in the prose. |
| 6. Engagement & tone | 7/10 | The tone is teacherly, but several passages are generic filler, especially the first paragraph under `Dialogues` and reflective lines like `"The ability to structure your time and share your schedule is a major milestone in communication."` |
| 7. Structural integrity | 10/10 | `Dialogues`, `Планування (Planning)`, `Мій тиждень (My Week)`, and `Summary` all appear in the planned order; the module is cleanly formatted and the pipeline word count is 1705, above the 1200 target. |
| 8. Cultural accuracy | 9/10 | No Russian-centric framing or cultural inaccuracies. The scenarios are ordinary Ukrainian-learning contexts and stay decolonized. |
| 9. Dialogue & conversation quality | 7/10 | Dialogue 1 is usable, but Dialogue 2 has a speaker-turn coherence error: after `Віктор: Так, багато!`, the line `Антон: У понеділок я буду працювати допізна.` breaks the expected flow of Viktor listing his week. |

## Findings
[DIMENSION] [SEVERITY: critical]  
Location: `Планування` note — `"Notice the vowel ending change for feminine days. The days **середа**, **п'ятниця**, and **субота** change their final **-а** or **-я** to **-у** or **-ю**."`  
Issue: The grammar explanation omits **неділя → неділю**, so the rule is incomplete and misleading.  
Fix: Add `**неділя**` to the list of feminine day names that change to `-ю`.

[DIMENSION] [SEVERITY: major]  
Location: `Dialogues` second dialogue — `"> **Антон:** У понеділок я буду працювати допізна."`  
Issue: The speaker label breaks the dialogue logic. Viktor is the one answering about his week, so this line should remain with Viktor.  
Fix: Change the speaker label from `Антон` to `Віктор`.

[DIMENSION] [SEVERITY: major]  
Location: `Summary` opener — `"The core grammatical formula for scheduling in this module is extremely reliable: Day + time + буду + infinitive."`  
Issue: The plan includes `State Standard 2024, §4.2.4.1`, but the module never cites or integrates that reference.  
Fix: Append a short sentence tying the scheduling focus to `State Standard 2024, §4.2.4.1`.

[DIMENSION] [SEVERITY: major]  
Location: first paragraph under `## Dialogues` — `"Arranging a weekend get-together with friends is a perfect way to practice discussing the future..."`  
Issue: The opening is verbose filler. It spends too many English words on generic framing before getting to the teachable language.  
Fix: Replace it with a shorter, more specific introduction that points directly to future tense, timing, and invitations.

## Verdict: REVISE
REVISE because the module has fixable findings, including one grammar-note inaccuracy and one dialogue-coherence error. It also misses a planned reference and has noticeable filler, so several dimensions fall below the PASS threshold.

<fixes>
- find: "Notice the vowel ending change for feminine days. The days **середа**, **п'ятниця**, and **субота** change their final **-а** or **-я** to **-у** or **-ю**. Masculine days like **понеділок** remain unchanged."
  replace: "Notice the vowel ending change for feminine days. The days **середа**, **п'ятниця**, **субота**, and **неділя** change their final **-а** or **-я** to **-у** or **-ю**. Masculine days like **понеділок** remain unchanged."
- find: "> **Антон:** У понеділок я буду працювати допізна. *(On Monday, I will work until late.)*"
  replace: "> **Віктор:** У понеділок я буду працювати допізна. *(On Monday, I will work until late.)*"
- find: "The core grammatical formula for scheduling in this module is extremely reliable: Day + time + буду + infinitive."
  replace: "The core grammatical formula for scheduling in this module is extremely reliable: Day + time + буду + infinitive. This scheduling focus aligns with **State Standard 2024, §4.2.4.1**."
- find: "Arranging a weekend get-together with friends is a perfect way to practice discussing the future. In Ukrainian, expressing a **план** (plan) is a practical skill you use every single day. When organizing your time, you will often need to state what you are doing, when you are doing it, and ask others if they are **вільний** (free). Read this group chat where three friends are trying to align their weekend schedules and find time to relax together."
  replace: "Weekend plans are a natural context for the future tense. In this dialogue, three friends share a **план**, ask when something will happen, and invite each other out."
</fixes>