## Linguistic Scan
- Factually wrong rule claim in the first section: `At the start of a sentence, we look only at the first letter of the next word. If the next word starts with a vowel, we use «в». If it starts with a consonant, we use «у»...` This is too absolute; sentence-initial `у/в` is a norm with variation, not a one-choice binary rule.
- Factually wrong rule claim in the third section: `Найбезпечніший варіант після коми — завжди «і»... Це помилка...` This is false as stated; school-textbook norms allow `й` after a pause before a vowel.
- Overstated status claim in the opening: `It is not just an optional style choice; it is a strict grammar rule.` This misframes милозвучність as rigid mechanics rather than a pronunciation/usage norm.

## Exercise Check
Four markers are present, and they are placed after the relevant teaching blocks:
`match-up` after `У чи в?`
`error-correction` after `З, із чи зі?`
`fill-in` after `І чи й?`
`quiz` after `Все разом`

They match the four `activity_hints` in the plan and are evenly distributed. No exercise-placement issues found.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | All four planned H2 sections are present in order; section pacing is close to plan (~660/~660/~550/~330 vs 600/600/500/300), and all four planned activity types appear as markers. |
| 2. Linguistic accuracy | 5/10 | Two categorical rule claims are wrong as written: `If the next word starts with a vowel, we use «в». If it starts with a consonant, we use «у»` and `Найбезпечніший варіант після коми — завжди «і» ... Це помилка`. Local textbook corpus explicitly allows variation at sentence start and gives `Й` after a pause before a vowel. |
| 3. Pedagogical quality | 6/10 | The module has a usable PPP spine (dialogue -> explanation -> activity markers), but it repeatedly turns flexible euphony norms into hard prohibitions, which will teach learners to “correct” acceptable forms. |
| 4. Vocabulary coverage | 10/10 | All required plan vocabulary is introduced in context: `милозвучність`, `евфонія`, `чергування`, `голосний`, `приголосний`, `збіг`, `прийменник`, `сполучник`, `вживати`, `складний`. |
| 5. Exercise quality | 10/10 | All four plan hint types are represented by markers and placed after the relevant teaching sections. |
| 6. Engagement & tone | 8/10 | The teacher voice is clear and energetic, but `Your tongue will thank you, and you will immediately sound like a native speaker` overpromises and reads less like classroom guidance. |
| 7. Structural integrity | 10/10 | All planned headings are present, markdown is clean, and the pipeline word count is 2790, well above the 2000 target. |
| 8. Cultural accuracy | 10/10 | Fully Ukrainian-centered; no Russian comparison frame and no cultural distortion. |
| 9. Dialogue & conversation quality | 9/10 | The opening dialogue uses named speakers, a real trip-planning situation, and multiple target alternations in context. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `At the start of a sentence, we look only at the first letter of the next word. If the next word starts with a vowel, we use «в». If it starts with a consonant, we use «у» to create a smooth sound transition.`  
Issue: This teaches sentence-initial `у/в` as an absolute binary rule. School-textbook norms treat these as strong tendencies, not an invariant one-choice rule in every context.  
Fix: Reword this paragraph as a preference/norm: `в` is common before vowels, `у` is common before consonants, but the choice is not purely mechanical.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `Найбезпечніший варіант після коми — завжди «і»... Це помилка... Правильно: «Вона заспівала, і усі заплакали».`  
Issue: This falsely teaches that `й` after a comma before a vowel is wrong. Textbook norms explicitly allow `й` after a pause before a vowel.  
Fix: Replace the passage with wording that says `і` is common after a pause, but `й` before a vowel is also possible when it sounds natural.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `It is not just an optional style choice; it is a strict grammar rule.`  
Issue: This frames милозвучність as rigid mechanics instead of a pronunciation/usage norm and encourages overcorrection.  
Fix: Replace `strict grammar rule` with wording that presents it as an important norm of standard usage.

[ENGAGEMENT & TONE] [SEVERITY: minor]  
Location: `Always say «у вікно» and «у Львові». Your tongue will thank you, and you will immediately sound like a native speaker.`  
Issue: The line overpromises outcome and slips into marketing-style reassurance.  
Fix: Replace it with a concrete pronunciation benefit instead of a native-speaker promise.

## Verdict: REVISE
REVISE. The module is structurally strong and well-scaffolded, but it contains critical factual inaccuracies about `у/в` and `і/й`. A language module that teaches acceptable forms as mistakes cannot pass.

<fixes>
- find: |-
    It is not just an optional style choice; it is a strict grammar rule.
  replace: |-
    It is not just a style preference; it is an important pronunciation norm in standard Ukrainian, but speakers still choose the variant that sounds smoother in context.

- find: |-
    However, real speech is a **складний** (complex, compound) flow of words. What happens at the beginning of a sentence? At the start of a sentence, we look only at the first letter of the next word. If the next word starts with a vowel, we use «в». If it starts with a consonant, we use «у» to create a smooth sound transition.
  replace: |-
    However, real speech is a **складний** (complex, compound) flow of words. What happens at the beginning of a sentence? At the start of a sentence, speakers usually choose the variant that sounds smoother with the next word. Before a vowel, «в» is common: «В Україні». Before a consonant, «у» is common: «У лісі». These are strong preferences, not a mechanical rule for every context.

- find: |-
    When building complex sentences, pay close attention to commas. A comma represents a natural pause that completely resets the phonetic context, so you only look at the sound *after* the comma to know which word to **вживати** (to use, to apply).

    Після коми ми робимо паузу, тому попередній звук не має значення. Найбезпечніший варіант після коми — завжди «і»: «Він прийшов, і ми поїхали». Іноді студенти бачать наступний голосний і пишуть «й»: «Вона заспівала, й усі заплакали». Це помилка, бо після паузи звук «й» губиться. Правильно: «Вона заспівала, і усі заплакали».

    > *After a comma we make a pause, so the previous sound doesn't matter. The safest option after a comma is always «і»: "He arrived, and we left". Sometimes students see the next vowel and write «й»: "She started singing, and everyone started crying". This is a mistake, because after a pause the «й» sound gets lost. Correct: "She started singing, and everyone started crying" (with і).*
  replace: |-
    When building complex sentences, pay close attention to commas. A comma creates a pause, so the choice after it is often guided by what sounds smoother in the next phrase, not by a rigid ban on one form.

    Після коми ми робимо паузу, тому попередній звук часто відступає на другий план. Після паузи дуже часто вживають «і»: «Він прийшов, і ми поїхали». Але форма «й» перед голосним теж можлива, якщо вона звучить природно: «Вона заспівала, й усі заплакали». Обидва варіанти трапляються в нормативному мовленні, тож тут важливо не перетворювати милозвучність на жорстку механічну схему.

    > *After a comma we make a pause, so the previous sound is often less important. After a pause, «і» is very common: "He arrived, and we left". But «й» before a vowel is also possible if it sounds natural: "She started singing, and everyone started crying". Both forms occur in standard usage, so euphony should not be turned into a rigid mechanical rule.*

- find: |-
    Always say «у вікно» and «у Львові». Your tongue will thank you, and you will immediately sound like a native speaker.
  replace: |-
    In standard usage, «у вікно» and «у Львові» sound more natural and are easier to pronounce clearly.
</fixes>