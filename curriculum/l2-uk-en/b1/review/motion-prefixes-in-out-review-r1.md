## Linguistic Scan
Two instances of grammatical calques (Russianisms) found related to prepositions of purpose with verbs of motion:
- «за гарячим горнятком лате» (influenced by Russian "за кофе"). Standard Ukrainian uses «по» + Accusative for purpose of movement: «по гаряче горнятко лате» or «випити гаряче горнятко лате».
- «за вітамінами» (influenced by Russian "за витаминами"). Standard Ukrainian uses: «по вітаміни».

All other vocabulary (including "парковка", "доставка", "собака", "бариста") exists in modern dictionaries/VESUM and is used correctly here. Gender and case assignments are fully correct.

## Exercise Check
The generated text includes 8 `<!-- INJECT_ACTIVITY: -->` markers, but the plan only contains `activity_hints` for 6 activities. The writer inserted two unauthorized markers (`match-up-match-idiomatic-and-literal-phrases-with` and `free-write-describe-a-morning-routine-using-imperfective-verbs`) which break the strict 1:1 mapping required by the pipeline. 

The remaining 6 markers are placed well and match the focus of the plan.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | Missed the explicit error correction examples (`*Зайшов у друга`, `*Вийшов від магазину`) in Section 5, substituting them with a general warning. Added unauthorized activity markers. All required/recommended vocabulary used. |
| 2. Linguistic accuracy | 9/10 | Excellent paradigms and explanations. Deducted slightly for the two calques («за вітамінами», «за гарячим горнятком») which mimic Russian purpose-of-motion patterns. |
| 3. Pedagogical quality | 10/10 | Superb "PPP" flow. The spatial dilemmas in Section 4 (parking lot, grocery store, rain shelter) are phenomenal examples of contextualized grammar teaching. |
| 4. Vocabulary coverage | 10/10 | Perfectly integrated all 12 required and 10 recommended verbs/nouns naturally into stories, dialogues, and explanations. |
| 5. Exercise quality | 8/10 | Generated 8 markers for a 6-activity plan. The extra markers (`match-up-match-idiomatic-and-literal-phrases-with` and `free-write-describe-a-morning-routine-using-imperfective-verbs`) break pipeline integrity. |
| 6. Engagement & tone | 10/10 | Masterful tone. Very encouraging but substantial. "Ваша мовна «дверна ручка»" is a brilliant metaphor. |
| 7. Structural integrity | 9/10 | Exceeds the 4000-word target significantly (5292 words) adding rich depth. Clean markdown. Deducted for duplicating the exact same cultural explanation of "вийти заміж" in both Section 3 and Section 5. |
| 8. Cultural accuracy | 10/10 | The explanation of «вийти заміж» (going to live behind the husband's family) is a beautiful decolonized historical touch that anchors the grammar in culture. |
| 9. Dialogue & conversation quality | 10/10 | The phone dialogue between the secretary and Maksym perfectly demonstrates a natural, practical chain of motion verbs without feeling forced. |

## Findings

[1. Plan adherence] [Major]
Location: Section 5 ("Практика: за- і ви- в повсякденному житті"), last paragraph.
Issue: The plan required specific error correction examples: `*Зайшов у друга (wrong — should be до друга). *Вийшов від магазину (wrong — should be з магазину). *Забіг у пошту (should be до пошти or на пошту)`. The writer omitted these and instead copied the "вийти заміж" explanation from Section 3.
Fix: Replace the duplicated "вийти заміж" text with the required error examples.

[2. Linguistic accuracy] [Critical]
Location: Section 1, «Метушливий ранок у Львові» - "А потім він заходить (enters / goes into) до своєї улюбленої кав’ярні за гарячим горнятком лате."
Issue: "за чимось" with verbs of motion is a Russianism ("идти за кофе"). The Ukrainian norm is "по щось" (по каву, по воду).
Fix: Change to "по гаряче горнятко лате".

[2. Linguistic accuracy] [Critical]
Location: Section 5, Dialogue - "Потім я ще на одну хвилину забіжу (will pop into) в сусідню аптеку за вітамінами."
Issue: "за вітамінами" is a Russianism ("за витаминами"). Ukrainian norm is "по вітаміни".
Fix: Change to "по вітаміни".

[5. Exercise quality] [Critical]
Location: Throughout the module.
Issue: The writer injected 8 activity markers, but the plan only supports 6. The extra markers (`match-up-match-idiomatic-and-literal-phrases-with` and `free-write-describe-a-morning-routine-using-imperfective-verbs`) will cause pipeline failures.
Fix: Delete the two unauthorized `<!-- INJECT_ACTIVITY: -->` markers.

## Verdict: REVISE
The module is outstanding in its pedagogical depth, vocabulary integration, and tone, functioning perfectly as a B1 theory module. However, the presence of two grammatical calques, the missing error correction examples from the plan, and the pipeline-breaking extra activity markers require deterministic fixes before the module can be safely published.

<fixes>
- find: "А потім він **заходить** *(enters / goes into)* до своєї улюбленої кав’ярні за гарячим горнятком лате."
  replace: "А потім він **заходить** *(enters / goes into)* до своєї улюбленої кав’ярні по гаряче горнятко лате."
- find: "Потім я ще на одну хвилину **забіжу** *(will pop into)* в сусідню аптеку за вітамінами."
  replace: "Потім я ще на одну хвилину **забіжу** *(will pop into)* в сусідню аптеку по вітаміни."
- find: |
    Тому граматично правильно казати тільки «Вийди **з** *(from/out of)* кімнати». Також завжди пам'ятайте, що відомий вираз **вийти заміж** *(to get married)* використовується виключно для жінок, адже історично це означало «вийти жити за родину чоловіка». Для чоловіка ми традиційно використовуємо зовсім інше дієслово — **одружитися** *(to marry)*. Завжди будьте дуже уважні з прийменниками простору: ми заходимо **в** новий магазин або **до** старого друга, але завжди виходимо з великого магазину.
  replace: |
    Тому граматично правильно казати тільки «Вийди **з** *(from/out of)* кімнати». Завжди будьте дуже уважні з типовими помилками у прийменниках простору: не можна казати «*Зайшов у друга» (правильно — **до друга**), або «*Вийшов від магазину» (правильно — **з магазину**), чи «*Забіг у пошту» (правильно — **до пошти** або **на пошту**).
- find: |
    <!-- INJECT_ACTIVITY: match-up-match-idiomatic-and-literal-phrases-with -->

    Рух може бути не лише самостійним
  replace: |
    Рух може бути не лише самостійним
- find: |
    <!-- INJECT_ACTIVITY: free-write-describe-a-morning-routine-using-imperfective-verbs -->

    ## За- чи ви-? Пари протилежностей
  replace: |
    ## За- чи ви-? Пари протилежностей
</fixes>
