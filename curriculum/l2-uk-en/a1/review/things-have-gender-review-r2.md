## Linguistic Scan
No linguistic errors found.

Spot checks passed: VESUM confirmed the key noun set used here (`кіт`, `акваріум`, `рибка`, `черепаха`, `кошеня`, `фото`, `стілець`, `крісло`, `дзеркало`, etc.), and there are no Russian-only letters (`ы`, `э`, `ё`, `ъ`) in the module text or activity YAML.

## Exercise Check
Prose has 4 exercise markers, which matches the 4 `activity_hints` in the plan.

Resolved correctly:
- `quiz-pronoun-test`
- `fill-in-possessive`
- `quiz-gender-endings`

Placement is good for those 3 markers: each appears after the relevant explanation.

Problem:
- The prose contains `<!-- INJECT_ACTIVITY: group-sort-objects -->` after the object-by-gender section, which is the correct place for the planned sorting task.
- But the activity YAML has no matching `id: group-sort-objects` and no `type: group-sort` at all.
- So the planned 12-item gender-sorting exercise is missing at publish time.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 5/10 | The plan’s dialogue situation says pet shop, “Use animals and pet items to demonstrate він/вона/воно — not room furniture,” but the lesson opens with `"це моя кімната"` and `"Що у тебе є в сумці?"`. The planned references are also not integrated: `Пономарова`, `Вашуленко`, and `ULP` occur 0 times in the prose. |
| 2. Linguistic accuracy | 10/10 | No Russianisms, Surzhyk, calques, paronym errors, or wrong Ukrainian forms found. Core nouns were VESUM-verified; no Russian-only letters appear. |
| 3. Pedagogical quality | 6/10 | The core explanation is too abstract for A1: `"permanent grammatical categories"`, `"fixed part of its identity"`, `"dictates how the word interacts..."`. The lesson teaches the right facts, but too much English metalanguage sits between the examples and the practice. |
| 4. Vocabulary coverage | 10/10 | All required vocabulary appears naturally in prose (`стіл`, `книга`, `вікно`, `кімната`, `ліжко`, `стілець`, `лампа`, `телефон`, `комп'ютер`, `він/вона/воно`), and all recommended items also appear (`зошит`, `ручка`, `сумка`, `крісло`, `дзеркало`, `ключ`, `фото`, `стіна`). |
| 5. Exercise quality | 4/10 | The 8-item pronoun quiz, 8-item possessive fill-in, and 6-item endings quiz match the plan. But the planned 12-item `group-sort` is missing: the prose has `<!-- INJECT_ACTIVITY: group-sort-objects -->`, while the YAML has no matching ID and no `type: group-sort`. |
| 6. Engagement & tone | 6/10 | The teaching voice is not wrong, but it becomes lecture-heavy: `"critical pattern emerging"`, `"first direct encounter"`, `"dictates how the word interacts..."`. It reads more like commentary on grammar than an A1 lesson. |
| 7. Structural integrity | 9/10 | All four H2 sections are present and ordered correctly. Pipeline word count is 1274, so it clears the 1200 target. The only structural blemish is the unresolved group-sort injection point. |
| 8. Cultural accuracy | 10/10 | Ukrainian is presented on its own terms, with no Russian-centered framing or cultural distortion. |
| 9. Dialogue & conversation quality | 6/10 | Named speakers are used correctly, but the dialogues are thin and mostly demonstrative. `"це моя кімната"` / `"Що у тебе є в сумці?"` are functional examples, not the richer pet-shop interaction the plan asked for. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: `## Діалоги (Dialogues)` — `"Read this short video-call dialogue..."` and the room scene `"це моя кімната" ... "моє вікно нове"`  
Issue: The plan’s dialogue situation explicitly requires a pet-shop scene with `кіт`, `рибка`, `кошеня`, `акваріум`, `черепаха` and says “not room furniture.” The module instead opens with a room tour and only mentions pet-shop nouns later in exposition.  
Fix: Replace the opening room dialogue with a pet-shop dialogue that demonstrates `він / вона / воно` directly.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: `<!-- INJECT_ACTIVITY: group-sort-objects -->`  
Issue: The prose expects a group-sort activity after the object vocabulary section, but the activity YAML has no matching `id: group-sort-objects` and no `type: group-sort`. The planned 12-item sorting task is therefore missing.  
Fix: Replace the unresolved marker with a standard group-sort injection hint that specifies sorting 12 objects into masculine/feminine/neuter groups.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `## Він, вона, воно` — `"The Ukrainian language divides all nouns into three permanent grammatical categories..."` and `## Підсумок — Summary` — `"Whenever you encounter a new noun in Ukrainian, determining its gender is essential because it dictates how the word interacts..."`  
Issue: These passages are too abstract and English-heavy for A1. They also omit the planned textbook/ULP anchoring from Пономарова, Вашуленко, and the earlier possessive pattern from family/ULP Episode 6.  
Fix: Replace both passages with shorter rule-first wording, explicit textbook anchoring, and concrete repetition of `він / вона / воно` and `мій / моя / моє`.

## Verdict: REVISE
REVISE. There are no Ukrainian-language errors, but there are major plan/exercise/pedagogy failures: the opening dialogue ignores the required pet-shop setup, the planned `group-sort` activity is missing at injection time, and the core explanation is too abstract for A1 while omitting the planned reference anchoring. Multiple scored dimensions are below 9, so this cannot pass.

<fixes>
- find: |
    Ukrainian nouns have grammatical gender. Read this short video-call dialogue and notice how the word for "my" changes: **моя кімната**, **мій стіл**, **моє ліжко**.

    > **Марія:** Привіт! Дивись, це моя кімната. *(Hi! Look, this is my room.)*
    > **Оленка:** О, яка гарна лампа! А це твій стіл? *(Oh, what a nice lamp! And is that your table?)*
    > **Марія:** Так, це мій стіл. А ось моє ліжко. *(Yes, this is my table. And here is my bed.)*
    > **Оленка:** Бачу. А вікно теж нове? *(I see. Is the window new too?)*
    > **Марія:** Так, моє вікно нове. *(Yes, my window is new.)*

    If you look closely at this exchange, you will notice a critical pattern emerging. The word for "my" changes depending on the object it describes. When talking about the room, Марія says **моя кімната** (my room). When mentioning the table, she uses **мій стіл** (my table). And when pointing out the bed and the window, she switches to **моє ліжко** (my bed) and **моє вікно** (my window). This shifting pattern is your first direct encounter with Ukrainian gender agreement.
  replace: |
    Ukrainian nouns have grammatical gender. Read this short pet-shop dialogue and notice how **він**, **вона**, and **воно** help you test noun gender.

    > **Марія:** Дивись, який гарний кіт! Він спить у кошику. *(Look, what a nice cat! He is sleeping in a basket.)*
    > **Оленка:** А рибка? Вона в акваріумі. *(And the fish? She is in the aquarium.)*
    > **Марія:** Так. А це черепаха. Вона біля дзеркала. *(Yes. And this is a turtle. She is near the mirror.)*
    > **Оленка:** О, а кошеня маленьке! Воно теж гарне. *(Oh, and the kitten is small! It is nice too.)*

    In this dialogue, the pronouns show gender directly: **кіт — він**, **рибка — вона**, **черепаха — вона**, **кошеня — воно**. The same idea works with objects too: **акваріум — він**, **дзеркало — воно**.
- find: |
    The Ukrainian language divides all nouns into three permanent grammatical categories: **чоловічий рід** (masculine gender), **жіночий рід** (feminine gender), and **середній рід** (neuter gender). You cannot change a word's gender; it is a fixed part of its identity. To identify which category a word belongs to, Ukrainian students learn a simple test using pronouns. Imagine visiting a pet shop. If you look at a sleeping male **кіт** (cat) or a large **акваріум** (aquarium), you can point to them and say **він** (he). If you watch a swimming **рибка** (fish) or a resting **черепаха** (turtle), you can replace those words with **вона** (she). Finally, if you see a tiny **кошеня** (kitten), you would refer to it as **воно** (it).

    Building on this pronoun concept, the most practical tool for identifying gender is the "My" test. Instead of just replacing the noun, you pair it with a possessive pronoun. If you can naturally say **мій** (my, masculine) with the object, it is a "he-word." If **моя** (my, feminine) sounds right, it is a "she-word." If it requires **моє** (my, neuter), it is an "it-word." Apply this to the room vocabulary we saw earlier. You can say **мій стіл** (my table), which confirms the word is masculine. When you say **моя книга** (my book), you confirm it is feminine. Finally, saying **моє вікно** (my window) proves that the word is neuter.
  replace: |
    Grade 3 Ukrainian textbooks teach this with a simple test: add **він**, **вона**, or **воно** to the noun. That gives you three genders: **чоловічий рід** (masculine), **жіночий рід** (feminine), and **середній рід** (neuter). In the pet shop scene, **кіт** and **акваріум** take **він**, **рибка** and **черепаха** take **вона**, and **кошеня** takes **воно**.

    You can check the same idea with **мій / моя / моє**. Say **мій стіл**, **моя книга**, and **моє вікно**. If **мій** fits, the noun is masculine. If **моя** fits, it is feminine. If **моє** fits, it is neuter. This follows the textbook pattern from Пономарова (p.86) and the endings overview in Вашуленко (p.112).
- find: "<!-- INJECT_ACTIVITY: group-sort-objects -->"
  replace: "<!-- INJECT_ACTIVITY: group-sort, Sort 12 objects into masculine (він), feminine (вона), and neuter (воно) groups -->"
- find: |
    Whenever you encounter a new noun in Ukrainian, determining its gender is essential because it dictates how the word interacts with adjectives and pronouns. You can master this process by following three reliable steps. First, replace the noun with the core pronouns **він** (he), **вона** (she), or **воно** (it) to see which one fits naturally. Second, look closely at the word's final letter. A consonant almost always indicates masculine, an **-а** or **-я** ending points to feminine, and an **-о** or **-е** signals neuter. Third, test the word using the possessive pronoun series: **мій** (my, m), **моя** (my, f), or **моє** (my, n). Remember, gender is a permanent trait that commands agreement across the entire sentence.

    Run a quick self-check using the vocabulary from this lesson. What gender is the word **стіл**? It is masculine because you can say **він**, it ends in a consonant, and it pairs with the pronoun to become **мій стіл**. What gender is **книга**? It is feminine because you can replace it with **вона**, it ends in the vowel **-а**, and you say **моя книга**. What about **вікно**? It is clearly neuter because you refer to it as **воно**, it ends in **-о**, and it becomes **моє вікно**. Finally, try translating this thought: Say "I have a chair" in Ukrainian. You simply use the familiar structure and state **У мене є стілець**.
  replace: |
    Use three quick checks when you meet a new noun. First, try **він**, **вона**, or **воно**. Second, look at the ending: a consonant usually means masculine, **-а / -я** usually means feminine, and **-о / -е** usually means neuter. Third, say **мій / моя / моє** with the noun and listen for the form that sounds right.

    Try it once more: **стіл — він — мій стіл**; **книга — вона — моя книга**; **вікно — воно — моє вікно**. Then make your own sentence with **У мене є**, the same pattern you met earlier with family vocabulary and hear again in Ukrainian Lessons Episode 6: **У мене є стілець**.
</fixes>