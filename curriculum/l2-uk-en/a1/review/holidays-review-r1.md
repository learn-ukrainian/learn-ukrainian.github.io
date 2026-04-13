## Linguistic Scan
No Russianisms, Surzhyk, paronym errors, or forbidden Russian letters were found in the Ukrainian text I checked.

Issues found:
- The grammar note in the `:::caution` block teaches the wrong capitalization rule: `**День Незалежності** has both words capitalized because it is a major state holiday...`. Ukrainian orthography does not use “major holiday” as the rule.
- The cultural-history sentence `However, in 2023, Ukraine officially moved the date to December 25.` is factually inaccurate as written: it conflates the 2017 public-holiday change with the 2023 church-calendar shift.
- The Independence Day prose presents `салют` / fireworks as a normal present-day practice in Ukraine, which is outdated for contemporary Ukraine.

## Exercise Check
Found 4 markers:
- `quiz-which-holiday`
- `quiz-match-date`
- `group-sort-traditions`
- `fill-in-greetings`

Checks:
- Marker IDs match the 4 `activity_hints` in the plan.
- `quiz-match-date`, `group-sort-traditions`, and `fill-in-greetings` are placed after the relevant teaching.
- `quiz-which-holiday` is misplaced: it appears before `Новий рік` is taught, but the plan’s focus explicitly gives `Різдво / Великдень / Новий рік` as the answer set.
- Marker count is correct, but the first marker should be moved later so the learner has seen all target holidays before the quiz is injected.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | The structure follows the plan, but the Christmas Eve dialogue situation is not fully realized. The plan calls for a family + foreign guest scene explaining `кутя, борщ, вареники, риба, узвар`; in the module `узвар`, `вареники`, and `риба` do not appear at all, and the only `борщ` appears later in `борщ з м'ясом` as a grammar example. |
| 2. Linguistic accuracy | 7/10 | No Russianisms/Surzhyk found, but the note `**День Незалежності** has both words capitalized because it is a major state holiday` teaches the wrong orthographic rule. |
| 3. Pedagogical quality | 7/10 | The module has a usable presentation flow, but the `quiz-which-holiday` marker comes before `Новий рік` is introduced, so the learner may be tested on an option not yet taught. |
| 4. Vocabulary coverage | 7/10 | Required vocabulary is mostly present, but the planned Christmas-dinner vocabulary is underdelivered: `узвар`, `вареники`, and `риба` are absent from the prose, and `борщ` is not taught in the holiday scene. |
| 5. Exercise quality | 7/10 | The marker inventory matches the plan, but `<!-- INJECT_ACTIVITY: quiz-which-holiday -->` is placed before the New Year subsection even though the plan says the quiz should distinguish `Різдво / Великдень / Новий рік`. |
| 6. Engagement & tone | 7/10 | There are useful cultural details (`Свята вечеря`, `писанки`, `вишиванка`), but the key Christmas scene is less vivid than the plan’s guest-at-table situation and reads more like explanation than lived interaction. |
| 7. Structural integrity | 9/10 | All planned H2 sections are present and ordered correctly; markdown is clean; pipeline word count is 1713, which is above the 1200 target. |
| 8. Cultural accuracy | 5/10 | `However, in 2023, Ukraine officially moved the date to December 25` is historically imprecise, and the present-tense Independence Day material normalizes `салют` / fireworks in a way that is outdated for contemporary Ukraine. |
| 9. Dialogue & conversation quality | 6/10 | Named speakers help, but the strongest planned scene is missing; the Christmas material does not use the intended foreign-guest dinner setup and loses a more natural cultural conversation opportunity. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: `> **Олена:** Що ми готуємо на Святвечір?... > **Мама:** Звичайно, кутя — перша страва.` and `На столі стоять дванадцять страв...`  
Issue: The plan requires a Ukrainian family + foreign guest Christmas Eve dialogue explaining the 12 dishes, with `кутя, борщ, вареники, риба, узвар`. The module uses a simpler mother-daughter exchange and omits most of the planned dish vocabulary.  
Fix: Replace the mini-dialogue and follow-up paragraph with a guest/family exchange that explicitly names `борщ, вареники, риба, узвар` and ties them to `Свята вечеря`.

[CULTURAL ACCURACY] [SEVERITY: critical]  
Location: `However, in 2023, Ukraine officially moved the date to December 25.`  
Issue: This is historically inaccurate as written. December 25 became an official public holiday in 2017; 2023 refers to the major church-calendar shift and the removal of January 7 from the state-holiday list.  
Fix: Replace the paragraph with a precise explanation that distinguishes 2017 and 2023.

[CULTURAL ACCURACY] [SEVERITY: critical]  
Location: `> **Сара:** Ввечері — салют і святковий вечір з друзями.` and `Увечері люди дивляться яскравий салют.`  
Issue: The module presents fireworks as a normal present-day Independence Day practice. That is outdated for contemporary Ukraine and should not be taught as a default current custom.  
Fix: Replace `салют` examples with concerts, walks, public celebrations, or festive programs.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `Remember that Ukrainian capitalizes the first word of holidays. For example, **День Незалежності** has both words capitalized because it is a major state holiday...`  
Issue: This teaches the wrong rule. The reason is not “major state holiday”; Ukrainian capitalization depends on the formal naming rule for holiday names, and official names like `День Незалежності України` are a special case.  
Fix: Replace the note with a correct orthography explanation.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: `<!-- INJECT_ACTIVITY: quiz-which-holiday -->` before `## Державні свята (National Holidays)`  
Issue: The plan’s `which holiday?` quiz includes `Новий рік`, but this marker appears before the New Year subsection is taught.  
Fix: Move `quiz-which-holiday` to after the New Year material and before the date-matching quiz.

## Verdict: REVISE
REVISE. The module is structurally usable, but it contains critical factual/orthographic issues and one major exercise-ordering problem. The problems are fixable with deterministic replacements; this is not a full-rebuild case.

<fixes>
- find: |-
    The winter cycle centers around **Різдво**. Historically, under Russian and Soviet influence, many Ukrainians celebrated on January 7. However, in 2023, Ukraine officially moved the date to December 25. This decision aligns the country with Europe and the majority of the Christian world, marking a major cultural shift away from the Russian Orthodox calendar.
  replace: |-
    The winter cycle centers around **Різдво**. For many years, Ukrainians celebrated Christmas on both December 25 and January 7, depending on church calendar and family tradition. In 2017, December 25 became an official public holiday, and in 2023 major Ukrainian churches adopted the revised calendar for fixed feasts. This shift is part of Ukraine's broader effort to live by its own traditions and institutions.
- find: |-
    > **Олена:** Що ми готуємо на Святвечір? *(What are we preparing for Christmas Eve?)*
    > **Мама:** Ми готуємо дванадцять страв. *(We are preparing twelve dishes.)*
    > **Олена:** А кутя є? *(And is there kutia?)*
    > **Мама:** Звичайно, кутя — перша страва. *(Of course, kutia is the first dish.)*
  replace: |-
    > **Іноземний гість:** Що ви готуєте на Святвечір? *(What are you preparing for Christmas Eve?)*
    > **Українська родина:** Ми готуємо дванадцять пісних страв. *(We are preparing twelve meatless dishes.)*
    > **Іноземний гість:** Які саме? *(Which ones exactly?)*
    > **Українська родина:** Кутю, борщ, вареники, рибу й узвар. *(Kutia, borshch, varenyky, fish, and uzvar.)*
    > **Іноземний гість:** Яка страва головна? *(Which dish is the main one?)*
    > **Українська родина:** Кутя — головна страва Святого вечора. *(Kutia is the main dish of Holy Supper.)*
- find: |-
    На столі стоять дванадцять страв. Вони дуже смачні і традиційні. Головна страва — це кутя. Ми дуже любимо це свято.
    > *There are twelve dishes on the table. They are very tasty and traditional. The main dish is kutia. We really love this holiday.*
  replace: |-
    На столі стоять дванадцять пісних страв: кутя, борщ, вареники, риба й узвар. Це традиційні страви Святого вечора, а кутя — головна страва.
    > *There are twelve meatless dishes on the table: kutia, borshch, varenyky, fish, and uzvar. These are traditional foods of Holy Supper, and kutia is the main dish.*
- find: |-
    > **Сара:** Ввечері — салют і святковий вечір з друзями. *(In the evening — fireworks and a festive evening with friends.)*
  replace: |-
    > **Сара:** Ввечері — концерт і святковий вечір з друзями. *(In the evening — a concert and a festive evening with friends.)*
- find: |-
    This conversation introduces the core noun **свято** (holiday). The phrase **державне свято** means state holiday. During these events, a **парад** (parade) takes place, a **концерт** (concert) provides music, and a **салют** (fireworks) lights up the sky. The greeting **З Днем Незалежності!** is standard for August 24. It is frequently paired with the national salute **Слава Україні!** (Glory to Ukraine!).
  replace: |-
    This conversation introduces the core noun **свято** (holiday). The phrase **державне свято** means state holiday. During these events, a **парад** (parade) takes place, a **концерт** (concert) provides music, and people gather for festive public events in the evening. The greeting **З Днем Незалежності!** is standard for August 24. It is frequently paired with the national salute **Слава Україні!** (Glory to Ukraine!).
- find: |-
    У серпні ми святкуємо День Незалежності. На вулиці проходить великий парад. Ми бачимо сині і жовті прапори. Увечері люди дивляться яскравий салют. Усі гордо кажуть: «Слава Україні!». 
    > *In August we celebrate Independence Day. A big parade takes place on the street. We see blue and yellow flags. In the evening people watch bright fireworks. Everyone proudly says: "Glory to Ukraine!".*
  replace: |-
    У серпні ми святкуємо День Незалежності. На вулиці проходить великий парад. Ми бачимо сині і жовті прапори. Увечері люди слухають концерт і гуляють містом. Усі гордо кажуть: «Слава Україні!». 
    > *In August we celebrate Independence Day. A big parade takes place on the street. We see blue and yellow flags. In the evening people listen to a concert and walk around the city. Everyone proudly says: "Glory to Ukraine!".*
- find: "<!-- INJECT_ACTIVITY: quiz-which-holiday -->"
  replace: ""
- find: "<!-- INJECT_ACTIVITY: quiz-match-date -->"
  replace: |-
    <!-- INJECT_ACTIVITY: quiz-which-holiday -->
    <!-- INJECT_ACTIVITY: quiz-match-date -->
- find: |-
    Remember that Ukrainian capitalizes the first word of holidays. For example, **День Незалежності** has both words capitalized because it is a major state holiday, but **Новий рік** only has the first word capitalized. Religious holidays like **Різдво** and **Великдень** are always capitalized.
  replace: |-
    Remember that Ukrainian holiday names normally capitalize the first word and any proper names: **Новий рік**, **Великдень**, **Різдво**. In the official holiday names **День Незалежності України**, **День Конституції України**, and **День Соборності України**, all words are capitalized.
</fixes>