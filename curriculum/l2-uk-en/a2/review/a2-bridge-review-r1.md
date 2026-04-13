## Linguistic Scan
- `Кличний відмінок ми використовуємо тільки для звертання до людей.` / `the **кличний** (vocative) for addressing people` is too narrow. School-textbook usage includes direct address to personified/non-human nouns too (`Дніпре`, `Україно`), so this teaches an incorrect restriction.
- `When a syllable ends in a consonant and has no vowel after it, it is considered closed, and the historical root sound appears as an «і».` overstates the `о/е ~ і` alternation as if every closed syllable triggers it. Textbook evidence says this is not every closed syllable, but historically new closed syllables in many lexical patterns.
- `Equally important are the consonant alternations, specifically a historical process known as the first palatalization.` is incorrect for the examples `нога -> нозі`, `рука -> руці`, `муха -> мусі`. Those illustrate the alternations `г/з, к/ц, х/с` before `-і`, not first palatalization.
- `To achieve this, it uses a strict system of euphonic alternations. This is a fundamental phonetic law, not merely an optional stylistic choice. Ukrainian forces these changes...` and `If you see two consonants, put the vowel «у» between them. If you see a vowel, use the consonant «в».` are too absolute. This misdescribes euphony as mechanical and exceptionless.

## Exercise Check
- Found 4 markers total, matching the 4 `activity_hints` in the plan.
- Placement is correct: `quiz-case-identification` follows the cases section, `fill-in-phonological-alternations` follows phonology, and the two euphony markers follow the euphony section.
- IDs align semantically with the plan foci and expected item counts.
- No inline DSL exercises are present, so exercise logic beyond marker placement cannot be audited from the prose alone.
- No exercise-placement issues found.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | All four planned H2 sections are present and ordered correctly; section sizes stay within the allowed +10% range (`~660/~770/~440/~330` vs `600/700/400/300`). The planned phonology content is covered, but one covered point is taught inaccurately: `г/з, к/ц, х/с` is mislabeled as `the first palatalization`. |
| 2. Linguistic accuracy | 5/10 | Multiple factual teaching errors: `Кличний відмінок ми використовуємо тільки для звертання до людей`; `When a syllable ends in a consonant... the historical root sound appears as an «і»`; `specifically a historical process known as the first palatalization`; `strict system of euphonic alternations... Ukrainian forces these changes`. |
| 3. Pedagogical quality | 6/10 | The PPP skeleton is there (dialogue -> explanation -> activity markers), but the module teaches unsafe rules in core A2 bridge content, especially in phonology and euphony. A learner who memorizes these explanations will internalize wrong generalizations. |
| 4. Vocabulary coverage | 9/10 | All required plan words appear naturally in prose: `відмінок`, `називний`, `знахідний`, `місцевий`, `кличний`, `чергування`, `голосний`, `приголосний`, `наголос`. Recommended words such as `милозвучність`, `система`, `правило` also appear in context. |
| 5. Exercise quality | 9/10 | The four exercise markers are present, correctly placed after the relevant teaching, and match the plan’s types/foci (`quiz`, `fill-in`, `match-up`, `error-correction`). No marker clustering at the end. |
| 6. Engagement & tone | 6/10 | The rubric-penalized hype language appears repeatedly: `Welcome to the next stage of your journey!`, `significant leap forward`, `These three new cases will unlock your ability...`. This reads generic rather than like a concrete teacher. |
| 7. Structural integrity | 10/10 | Clean markdown, all planned sections present, markers intact, and the deterministic pipeline word count is `2695`, which is above the `2000` target. |
| 8. Cultural accuracy | 6/10 | The `Decolonization Note` centers Russian: `Unlike in Russian, where the vocative has largely disappeared...`. The rubric explicitly prefers presenting Ukrainian on its own terms, not through Russian comparison. |
| 9. Dialogue & conversation quality | 9/10 | The opening uses named speakers in a real A2 scenario and naturally surfaces all four A1 cases: `Я — новий студент`, `вивчаю українську мову`, `в Києві`, `Оксано`. |

## Findings
[Linguistic accuracy] [SEVERITY: critical]  
Location: `Кличний відмінок ми використовуємо тільки для звертання до людей.` and `the **кличний** (vocative) for addressing people.`  
Issue: This incorrectly teaches that the vocative is only for people. Standard usage also includes direct address to personified/non-human nouns.  
Fix: Change both statements to “direct address / прямого звертання, most often with people,” not “only for people.”

[Linguistic accuracy] [SEVERITY: critical]  
Location: `When a syllable ends in a consonant and has no vowel after it, it is considered closed, and the historical root sound appears as an «і».`  
Issue: This presents the `о/е ~ і` alternation as universal for closed syllables. Textbook evidence says it is limited to historically new closed syllables and many lexical patterns, not every closed syllable.  
Fix: Rewrite this as a limited historical pattern in many words, not a blanket rule.

[Linguistic accuracy] [SEVERITY: critical]  
Location: `Equally important are the consonant alternations, specifically a historical process known as the first palatalization.`  
Issue: The examples `нога -> нозі`, `рука -> руці`, `муха -> мусі` are not “first palatalization.” The label is wrong.  
Fix: Remove that label and name the actual alternations `г/з, к/ц, х/с` before `-і`.

[Linguistic accuracy] [SEVERITY: critical]  
Location: `it uses a strict system of euphonic alternations... Ukrainian forces these changes...` and `If you see two consonants, put the vowel «у» between them. If you see a vowel, use the consonant «в».`  
Issue: This teaches euphony as exceptionless and mechanical. That is misleading; these are strong norms/tendencies, not a rigid algorithm for every sentence.  
Fix: Soften the wording to “common patterns / useful guideline” and explicitly note acceptable variation.

[Cultural accuracy] [SEVERITY: major]  
Location: `**Decolonization Note** — ... Unlike in Russian, where the vocative has largely disappeared...`  
Issue: The note frames Ukrainian through Russian comparison instead of presenting Ukrainian on its own terms.  
Fix: Replace it with a positive usage note about how vocative functions in Ukrainian.

[Engagement & tone] [SEVERITY: major]  
Location: `Welcome to the next stage of your journey!`, `significant leap forward`, `These three new cases will unlock your ability...`  
Issue: This is generic journey/unlock language the rubric explicitly penalizes. It adds hype instead of instruction.  
Fix: Replace with a calmer teacher voice that states concretely what A2 adds.

## Verdict: REVISE
REVISE. The module is structurally solid and the activity markers are well placed, but it contains multiple critical factual-teaching errors in vocative usage, phonology, and euphony. Several dimensions are below 9, and the severity gate is failed.

<fixes>
- find: |
    We start with the **називний** (nominative) case. This is the basic dictionary form of a word. It answers the fundamental questions "who?" or "what?" and always acts as the main subject of the sentence performing the action. In stark contrast, the **кличний** (vocative) case does not answer any questions at all. It is used exclusively when you are addressing someone directly by their name or title, like saying "Оксанко", "друже", or "тату".

    Словникова форма слова завжди стоїть у називному відмінку. Цей відмінок називає предмет або особу. Кличний відмінок ми використовуємо тільки для звертання до людей.

    > *The dictionary form of a word always stands in the Nominative case. This case names an object or a person. We use the Vocative case only for addressing people.*
  replace: |
    We start with the **називний** (nominative) case. This is the basic dictionary form of a word. It answers the fundamental questions "who?" or "what?" and always acts as the main subject of the sentence performing the action. In stark contrast, the **кличний** (vocative) case does not answer any questions at all. It is used for direct address, most often when you are speaking to a person by name or title, like saying "Оксанко", "друже", or "тату".

    Словникова форма слова завжди стоїть у називному відмінку. Цей відмінок називає предмет або особу. Кличний відмінок ми використовуємо для прямого звертання, найчастіше до людини.

    > *The dictionary form of a word always stands in the Nominative case. This case names an object or a person. We use the Vocative case for direct address, most often when speaking to a person.*
- find: |
    :::info
    **Decolonization Note** — The Vocative case is a living, active, and absolutely essential feature of the Ukrainian language. Unlike in Russian, where the vocative has largely disappeared from modern speech, omitting it in Ukrainian instantly sounds unnatural to native speakers. Always use it when addressing someone to sound natural and respectful.
    :::
  replace: |
    :::info
    **Usage Note** — The Vocative case is a living, active feature of Ukrainian. Using it in direct address makes speech sound natural and respectful.
    :::
- find: |
    One of the most famous phonetic rules in Ukrainian is the alternation of the vowels «о» and «е» with the vowel «і». This happens because of a historical phenomenon known as the "closed syllable" rule. When a syllable ends in a consonant and has no vowel after it, it is considered closed, and the historical root sound appears as an «і». However, the moment you add a grammatical ending that starts with a vowel, the syllable opens up, and the hidden «о» or «е» reappears. This is why the names of many Ukrainian cities and common objects look different on a map compared to how they sound when you talk about moving to or from them.
  replace: |
    One of the most famous phonetic rules in Ukrainian is the alternation of the vowels «о» and «е» with the vowel «і». This is connected with a historical sound change that appears in many words, especially in historically new closed syllables. In such patterns, a form with «і» can alternate with a form where «о» or «е» reappears after a vowel-initial ending. This is why forms like «стіл/стола» or «Київ/Києва» look different across related grammatical forms.
- find: |
    Equally important are the consonant alternations, specifically a historical process known as the first palatalization.
  replace: |
    Equally important are the consonant alternations. In these noun forms, Ukrainian shows the alternations «г/з», «к/ц», and «х/с» before the ending «і».
- find: |
    Have you ever noticed how smoothly Ukrainian flows when spoken? This natural quality is known as **милозвучність** (euphony). The language actively avoids awkward clusters of sounds, preferring a steady balance between a **голосний** (vowel) and a **приголосний** (consonant). To achieve this, it uses a strict system of euphonic alternations. This is a fundamental phonetic law, not merely an optional stylistic choice. Ukrainian forces these changes to protect its melody. For example, a Ukrainian says «був у школі» to break up three consonants.
  replace: |
    Have you ever noticed how smoothly Ukrainian flows when spoken? This natural quality is known as **милозвучність** (euphony). The language often avoids awkward clusters of sounds and uses euphonic alternations that help speech flow more naturally. These are strong tendencies and common literary norms, but more than one option may be acceptable in some contexts. For example, a speaker may say «був у школі» to break up three consonants.
- find: |
    :::info
    **Grammar box**
    Always look at the letter *before* and the letter *after* the preposition. Your goal is to alternate vowel-consonant-vowel-consonant. If you see two consonants, put the vowel «у» between them. If you see a vowel, use the consonant «в».
    :::
  replace: |
    :::info
    **Grammar box**
    Look at the sounds before and after the preposition. As a first guideline, «у» often helps between consonants, while «в» often fits next to a vowel. These are useful tendencies for learners, not a mechanical rule for every sentence.
    :::
- find: |
    In the A2 level curriculum, three new and incredibly useful cases are waiting for you. You will soon master the Genitive case, which indicates absence, possession, or quantity when counting objects. You will also learn the Dative case to seamlessly express the recipient or the final destination of an action. Finally, you will explore the Instrumental case, which shows the tool you use to do something or the companion you are spending time with. These three new cases will unlock your ability to express much more complex and nuanced ideas in Ukrainian. You will master them step by step over the coming modules!
  replace: |
    In the A2 level curriculum, three new and very useful cases are waiting for you. You will soon master the Genitive case, which indicates absence, possession, or quantity when counting objects. You will also learn the Dative case to express the recipient or the final destination of an action. Finally, you will explore the Instrumental case, which shows the tool you use to do something or the companion you are spending time with. These three new cases will let you express more complex and nuanced ideas in Ukrainian. You will master them step by step over the coming modules.
- find: |
    Welcome to the next stage of your journey! The A2 curriculum is designed to be a significant leap forward in your functional fluency. In the previous level, you focused on surviving everyday situations with simple statements. A2 transitions you from merely stating facts to expressing complex ideas. You will learn how to connect thoughts, describe ongoing situations, and tell detailed stories. 

    Рівень А2 — це великий крок уперед. Ти більше не будеш говорити тільки короткими реченнями. Тепер ти зможеш розповідати цілі історії та пояснювати свої думки. Це час, коли українська мова стає твоїм справжнім інструментом.

    > *Level A2 is a big step forward. You will no longer speak only in short sentences. Now you will be able to tell whole stories and explain your thoughts. This is the time when the Ukrainian language becomes your true tool.*
  replace: |
    We are now beginning A2. In the previous level, you focused on simple everyday situations and short statements. At this level, you will begin connecting ideas, describing situations in more detail, and telling longer stories.

    Рівень А2 починається з повторення й упорядкування того, що ти вже знаєш. Ти будеш не тільки будувати короткі речення, а й поєднувати думки, докладніше описувати ситуації та розповідати довші історії.

    > *A2 begins with a review and organization of what you already know. You will not only build short sentences, but also connect ideas, describe situations in more detail, and tell longer stories.*
- find: |
    You also learned the **місцевий** (locative) for locations and the **кличний** (vocative) for addressing people. In A2, we will conquer the Genitive, Dative, and Instrumental cases. However, the most significant milestone is your introduction to verbal aspect.
  replace: |
    You also learned the **місцевий** (locative) for locations and the **кличний** (vocative) for direct address. In A2, we will conquer the Genitive, Dative, and Instrumental cases. However, the most significant milestone is your introduction to verbal aspect.
</fixes>