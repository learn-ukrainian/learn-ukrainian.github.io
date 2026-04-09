黎thought
CRITICAL INSTRUCTION 1: Use the most specific tool for the task. We are running MCP queries to verify linguistic claims.
CRITICAL INSTRUCTION 2: Related tools include `mcp_rag_query_r2u`, `mcp_rag_search_definitions`. Since Antonenko-Davydovych doesn't specifically ban "давайте" under that exact search, I don't need to flag it.

Wait, let's look at another part:
"Давайте послухаємо розмову двох друзів."
"Давайте послухаємо коротку розмову двох друзів."
It's fine.

What about "вирішують проблему"? "Вони показують конкретні завершені дії, які вирішують проблему." ("розв'язують проблему" is preferred, but "вирішують проблему" is acceptable enough, let me check R2U).
Let's check `mcp_rag_query_r2u` for "решать проблему".
黎thought
CRITICAL INSTRUCTION 1: Use specific tools. The previous tools gave me the information needed.
CRITICAL INSTRUCTION 2: Related tools include `mcp_rag_query_r2u`. I don't need any more tools.

Let's review the word "вокзал":
"Ви довго подорожуєте потягом і прибуваєте на великий вокзал. Слово «вокзал» є в багатьох мовах, але українська мова має своє унікальне історичне слово — двірець (station). Це слово особливо популярне в західних регіонах України."
This is factually correct and very nice culturally.

"Якщо подорож змогла вам сподобатися (to like)"
"Якщо подорож змогла вам сподобатися" — this phrasing "змогла вам сподобатися" is a bit awkward. "If the trip was able to be liked by you". A better phrasing would be: "Якщо подорож вам сподобалася". But it's not grammatically incorrect, just slightly awkward. Let's see if I should fix it.
"Після детальної розповіді про події ми часто хочемо поділитися своїми позитивними емоціями. Якщо подорож змогла вам сподобатися (to like), як правильно сказати про це українською?"
I will flag it as a minor issue: Awkward phrasing.
Let's fix it:
`find: "Якщо подорож змогла вам сподобатися (to like), як правильно сказати про це українською?"`
`replace: "Якщо подорож вам дуже сподобалася (to like), як правильно сказати про це українською?"`

Wait, another issue: "If a woman says "I went to the cinema," she must say «я ходила в кіно», never «я ходив»."
The text says "If a woman says "I went to the cinema," she must say «я ходила в кіно», never «я ходив»."
This is perfectly correct.

Let's review "Літак летить дві години" from the plan. Section 2 didn't mention it. Is it a big deal? The plan says:
`Motion verbs in context: Ми поїдемо потягом до Львова (pf. — specific trip). Зазвичай ми їздимо туди влітку (impf. — habitual). Літак летить дві години (unidirectional — in progress).`
The text says:
`For the actual journey to your destination, we use unidirectional perfective verbs. Ви кажете: «Я поїду (will go by vehicle) до міста» або «Я полечу (will fly) за кордон». Ці слова показують конкретний рух в одному напрямку. However, for general movement around the destination once you arrive, we use the compound future with multidirectional verbs. Наприклад: «Там я буду їздити (will ride around) на екскурсії».`
It completely missed "Літак летить дві години" (unidirectional in progress, imperfective). This is a minor omission, but plan adherence covers it. I'll just deduct a point for Plan adherence, but the major plan issues are the missing prepositions and time connectors, which I've fixed.

What about "доїхати"?
Section 3 plan: `Contrast: їздив (was there, round-trip completed) vs. поїхав (departed, left). Я їздив до Києва (I went to Kyiv and came back) vs. Він поїхав до Києва (He left for Kyiv — may still be there).`
The text has:
`The verb «їхати» is imperfective and means "to be going in one direction," but its partner «їздити» (imperfective, multidirectional) is uniquely used in the past tense to describe a fully completed round trip. Марко каже: «Я їздив (went and came back) до Одеси». Ми чітко розуміємо, що він уже повернувся додому. This is a very crucial distinction in Ukrainian. Ви можете сказати інакше: «Мій брат поїхав (left) до Києва». Це означає, що ваш брат покинув дім. Він усе ще перебуває в Києві. Або ви просто фокусуєтесь на факті його від'їзду. The perfective verb «поїхати» focuses entirely on the departure, not the return.`

Wait, Section 1: "Раптом я з жахом зрозумів, що загубив мій квиток!"
"мій квиток" vs "свій квиток". "загубив свій квиток" is much more natural in Ukrainian (possessive reflexive pronoun is preferred over "мій" when referring to the subject's own object).
I'll flag this as a Major issue (pedagogical/naturalness) to enforce good grammar habits.
`find: "Раптом я з жахом зрозумів, що загубив мій квиток!"`
`replace: "Раптом я з жахом зрозумів, що загубив свій квиток!"`
Also:
`find: "Нарешті я знайшов його в кишені моєї куртки."`
`replace: "Нарешті я знайшов його в кишені своєї куртки."`

Are there any formatting issues?
"Слово «потім» показує чітку хронологічну послідовність дій."
"Слово «раптом» — це завжди великий сюрприз."

Let's do a final review of the fixes:
```yaml
<fixes>
- find: "Ось кілька дуже важливих слів для розповіді: **спочатку** (at first), **потім** (then), **раптом** (suddenly), та **нарешті** (finally). Слово «спочатку» дає ідеальний старт вашій історії."
  replace: "Ось кілька дуже важливих слів для розповіді: **спочатку** (at first), **потім** (then), **після цього** (after that), **тим часом** (meanwhile), **у цей момент** (at that moment), **раптом** (suddenly), та **нарешті** (finally). Слово «спочатку» дає ідеальний старт вашій історії."
- find: "Раптом я з жахом зрозумів, що загубив мій квиток! Я швидко почав шукати його скрізь. Нарешті я знайшов його в кишені моєї куртки."
  replace: "Раптом я з жахом зрозумів, що загубив свій квиток! Я швидко почав шукати його скрізь. Нарешті я знайшов його в кишені своєї куртки."
- find: "Notice how incredibly stable the -в sound is for masculine verbs in Ukrainian. Even for verbs with challenging consonant stems like **міг** (could), **ніс** (carried), or **біг** (ran), Ukrainian stubbornly maintains its unique phonetic pattern compared to neighboring languages."
  replace: "Notice that most verbs use the **-в** sound for masculine forms. However, some verbs with consonant stems, like **міг** (could from *могти*), **ніс** (carried from *нести*), or **біг** (ran from *бігти*), do not have this suffix in the masculine form."
- find: "Але ми використовуємо прийменник «на» зі знахідним відмінком для відкритих просторів чи подій. Наприклад: на море, на фестиваль, на концерт."
  replace: "Але ми використовуємо прийменник «на» зі знахідним відмінком для відкритих просторів чи подій. Наприклад: на море, на фестиваль, на концерт. Щоб сказати, звідки ви приїхали, використовуйте прийменник «з» або «зі» з родовим відмінком: прилетіти з Києва, повернутися зі Львова."
- find: "Якщо подорож змогла вам сподобатися (to like), як правильно сказати про це українською?"
  replace: "Якщо подорож вам дуже сподобалася (to like), як правильно сказати про це українською?"
- find: "You use this specific construction with the dative case pronoun («мені») and the neuter past tense form of the verb. Після цієї фрази ви можете легко додати інфінітив або звичайний іменник: «Мені сподобалося гуляти по місту» або «Мені дуже сподобалося це старе місто»."
  replace: "You use this specific construction with the dative case pronoun («мені») and the past tense verb. Якщо ви додаєте інфінітив, дієслово завжди має середній рід: «Мені сподобалося гуляти по місту». Якщо ви додаєте іменник, дієслово узгоджується з його родом: «Мені сподобалося місто» (neuter), «Мені сподобався музей» (masculine), або «Мені сподобалася вулиця» (feminine)."
- find: "Це було справді !"
  replace: "Це було справді неймовірно!"
- find: "Це слова **спочатку** (at first), **потім** (then), **раптом** (suddenly), **нарешті** (finally)."
  replace: "Це слова **спочатку** (at first), **потім** (then), **після цього** (after that), **тим часом** (meanwhile), **раптом** (suddenly), **нарешті** (finally)."
</fixes>
```

Let's double-check the Summary fix.
"Це слова **спочатку** (at first), **потім** (then), **після цього** (after that), **тим часом** (meanwhile), **раптом** (suddenly), **нарешті** (finally)."
Wait, earlier I added "у цей момент" to the main text, but omitted it in the summary fix. Let's include it:
```yaml
- find: "Це слова **спочатку** (at first), **потім** (then), **раптом** (suddenly), **нарешті** (finally)."
  replace: "Це слова **спочатку** (at first), **потім** (then), **після цього** (after that), **тим часом** (meanwhile), **у цей момент** (at that moment), **раптом** (suddenly), **нарешті** (finally)."
```

Let's ensure the `find` string for the missing word is exact.
Original: `Це було справді !`
Wait, does it have a trailing space before `!`? In the raw content: `Це було справді !` Yes.
Let's check:
"Це було справді !"
I'll replace it with "Це було справді неймовірно!"

Wait, what about the summary missing the explanation of the newly added prepositions `з` and `зі`? The original summary says:
`Ми використовуємо **з** (from) або **зі** плюс родовий відмінок для старту. Наприклад: «зі Львова».`
So the summary ALREADY has the explanation of `з`/`зі`!
"Ми використовуємо з (from) або зі плюс родовий відмінок для старту. Наприклад: «зі Львова»."
But Section 2 MISSES it! This means the summary introduces something not explicitly taught in Section 2, further justifying my fix in Section 2. My fix adding `з` to Section 2 aligns it with the summary.

Let's double check my fix for the verb conjugation rule in past tense.
`Notice that most verbs use the **-в** sound for masculine forms. However, some verbs with consonant stems, like **міг** (could from *могти*), **ніс** (carried from *нести*), or **біг** (ran from *бігти*), do not have this suffix in the masculine form.`
Wait, "Notice that most verbs use the **-в** sound for masculine forms. However, some verbs with consonant stems, like **міг** (could from *могти*), **ніс** (carried from *нести*), or **біг** (ran from *бігти*), do not have this suffix in the masculine form." is exactly what it should be. The original was stating they DO have the `-в` sound and maintain it. That was incredibly wrong. Good catch.

Wait, are there any Russianisms?
`путешествіє` is explicitly used as a negative example: `Ніколи не використовуйте російське слово «путешествіє».` This is allowed.
`білет` is also used as a negative example: `Please note that the authentic Ukrainian word is «квиток», which helps us avoid the common Russianism «білет».`
`забронюю хатинку` - correct.
`купувати квитки` - correct.
`розповідати / розповісти` - correct.
`декорації` - correct.
`оленя` - correct.

Is there any missing plan vocabulary?
`подорож` - used
`розповідати / розповісти` - used
`трапитися` - used
`квиток` - used
`потяг` - used
`вокзал` - used
`зупинитися` - used
`доїхати` - used
`сподобатися` - used
`враження` - used
`спочатку, потім, нарешті, тим часом` - "тим часом" was missed, I've added it.
`сувенір` - Not used! The word "сувенір" is in the plan's recommended vocabulary (`сувенір (souvenir)`) and in the plan's section 3 sample narrative (`купили сувеніри`). The text dialogue and narrative omit it.
Section 3 text dialogue: `Ми багато ходили на пляж і просто дивилися на море. Це був чудовий відпочинок!`
I can add it:
`find: "Ми багато ходили на **пляж** (beach) і просто дивилися на **море** (sea). Це був чудовий відпочинок!"`
`replace: "Ми багато ходили на **пляж** (beach), купували **сувеніри** (souvenirs) і просто дивилися на **море** (sea). Це був чудовий відпочинок!"`
Let's add this fix as well to improve plan adherence.

Wait, the prompt says "recommended: сувенір".
Let's modify the fix:
```yaml
- find: "Ми багато ходили на **пляж** (beach) і просто дивилися на **море** (sea). Це був чудовий відпочинок! *(We went to the beach a lot and just looked at the sea. It was a wonderful vacation!)*"
  replace: "Ми багато ходили на **пляж** (beach), купували **сувеніри** (souvenirs) і просто дивилися на **море** (sea). Це був чудовий відпочинок! *(We went to the beach a lot, bought souvenirs and just looked at the sea. It was a wonderful vacation!)*"
```
Wait, I shouldn't mess with the translated English text if I can avoid it, but it's part of the dialogue block and the English translation must match.
I'll just find a simpler place to insert it.
Section 3: `«Ходити по місту» is a long process — you walk around and explore without a specific, immediate final destination. Therefore, we use the multidirectional imperfective verb.`
Or in Section 3 narrative example:
`Вдень ми дуже багато **ходили** (walked) по місту, а ввечері ми **відвідали** (visited) оперу`
Let's use the model answer in Section 4:
`Там ми **залишили** [Perfective, completed event] усі свої важкі речі. Наступного дня ми **пішли** [Perfective, one-time departure on foot] високо в гори.`
Actually, it's a recommended word, so it's not critical, but missing it is a minor deduction. I'll just note it in findings and add the fix to Section 3 narrative example.
`find: "Вдень ми дуже багато **ходили** (walked) по місту, а ввечері ми **відвідали** (visited) оперу".`
`replace: "Вдень ми дуже багато **ходили** (walked) по місту, купували **сувеніри** (souvenirs), а ввечері ми **відвідали** (visited) оперу".`

Let's format the final response.

## Linguistic Scan
No linguistic errors found in general Ukrainian usage, but there is a critical grammatical explanation error regarding the past tense of verbs like "міг" and "ніс".

## Exercise Check
- `<!-- INJECT_ACTIVITY: quiz-aspect-choice -->` appears at the end of Section 1 (tests aspect choice).
- `<!-- INJECT_ACTIVITY: match-up-travel-verbs -->` appears at the end of Section 2 (tests motion verbs).
- `<!-- INJECT_ACTIVITY: fill-in-travel-narrative -->` appears at the end of Section 3 (tests narrative verbs/aspects).
- `<!-- INJECT_ACTIVITY: error-correction-travel -->` appears at the end of Section 4 (tests common mistakes).
All markers match the plan's activity hints and are evenly distributed.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | Missed some time connectors ("після цього", "тим часом", "у цей момент") and the preposition "з + Gen" in Section 2 (though it appears in the summary). Missed the recommended word "сувенір". |
| 2. Linguistic accuracy | 5/10 | Critical error in phonetic/grammatical explanation: Claims verbs like "міг, ніс, біг" have a "-в" suffix. In reality, they drop this suffix in the masculine past tense form. Also, awkward use of possessive pronoun "мій квиток" instead of "свій квиток". |
| 3. Pedagogical quality | 6/10 | Critical error: Teaches that for "Мені сподобалося [Noun]" the verb always stays neuter, giving the misleading rule "Після цієї фрази ви можете легко додати інфінітив або звичайний іменник: «Мені дуже сподобалося це старе місто»", without explaining gender agreement for nouns. |
| 4. Vocabulary coverage | 9/10 | Good coverage overall, but missed the recommended word "сувенір" in the narrative sections. |
| 5. Exercise quality | 10/10 | Markers are placed well and match the plan's activity hints. |
| 6. Engagement & tone | 9/10 | Warm, encouraging, and natural teacher persona without excessive fluff. |
| 7. Structural integrity | 9/10 | Missing word in the model answer block ("Це було справді !"). Word count is solid (2745 words). |
| 8. Cultural accuracy | 10/10 | Excellent points about "двірець" vs "вокзал" and the importance of using Ukrainian city names like Київ instead of Russian variants. |
| 9. Dialogue & conversation quality | 9/10 | Dialogues are natural and incorporate the targeted grammar structures well. |

## Findings
[1. Plan adherence] [Major]
Location: `Ось кілька дуже важливих слів для розповіді: спочатку (at first), потім (then), раптом (suddenly), та нарешті (finally).`
Issue: Several time connectors required by the plan (після цього, тим часом, у цей момент) are completely missing from the explanation.
Fix: Add the missing connectors to the list.

[1. Plan adherence] [Minor]
Location: `Вдень ми дуже багато ходили (walked) по місту, а ввечері ми відвідали (visited) оперу.`
Issue: The recommended vocabulary word "сувенір" is missing from the entire text.
Fix: Add "купували сувеніри" to the example sentence.

[1. Plan adherence] [Major]
Location: `Але ми використовуємо прийменник «на» зі знахідним відмінком для відкритих просторів чи подій. Наприклад: на море, на фестиваль, на концерт.`
Issue: The preposition "з/зі + Gen" (from a place) was required by the plan but omitted from the explanation in Section 2.
Fix: Add an explanation for "з/зі" + Genitive.

[2. Linguistic accuracy] [Critical]
Location: `Notice how incredibly stable the -в sound is for masculine verbs in Ukrainian. Even for verbs with challenging consonant stems like міг (could), ніс (carried), or біг (ran), Ukrainian stubbornly maintains its unique phonetic pattern compared to neighboring languages.`
Issue: Factually incorrect. The masculine past tense of verbs like "міг", "ніс", "біг" is formed by dropping the "-в" suffix, not maintaining it.
Fix: Correct the rule to state that these verbs do NOT have the suffix in the masculine form.

[2. Linguistic accuracy] [Major]
Location: `Раптом я з жахом зрозумів, що загубив мій квиток! Я швидко почав шукати його скрізь. Нарешті я знайшов його в кишені моєї куртки.`
Issue: Unnatural use of possessive pronouns. In Ukrainian, it's more natural to use "свій" instead of "мій" when the object belongs to the subject.
Fix: Replace "мій/моєї" with "свій/своєї".

[3. Pedagogical quality] [Critical]
Location: `You use this specific construction with the dative case pronoun («мені») and the neuter past tense form of the verb. Після цієї фрази ви можете легко додати інфінітив або звичайний іменник: «Мені сподобалося гуляти по місту» або «Мені дуже сподобалося це старе місто».`
Issue: The rule is misleading. It implies the verb is ALWAYS neuter when followed by a noun, failing to explain that the verb must agree in gender with the noun (e.g., "Мені сподобався музей").
Fix: Clarify that the neuter is for infinitives, and the verb must agree with the noun's gender if a noun is used.

[6. Engagement & tone] [Minor]
Location: `Якщо подорож змогла вам сподобатися (to like), як правильно сказати про це українською?`
Issue: The phrasing "змогла вам сподобатися" is awkward and feels like an unnatural calque of "was able to be liked".
Fix: Change to "Якщо подорож вам дуже сподобалася".

[7. Structural integrity] [Critical]
Location: `Раптом ми побачили [Perfective, sudden event] великого оленя біля дерева. Це було справді !`
Issue: A word is missing at the end of the sentence before the exclamation mark.
Fix: Add "неймовірно" before the exclamation mark.

[1. Plan adherence] [Minor]
Location: `Це слова спочатку (at first), потім (then), раптом (suddenly), нарешті (finally).`
Issue: The summary misses the newly added time connectors.
Fix: Update the summary to include the missing time connectors.

## Verdict: REVISE
The module covers the topic well and has excellent cultural notes, but it contains two critical grammatical/phonetic errors: claiming verbs like "міг" and "ніс" maintain the "-в" suffix, and providing a misleading rule about gender agreement for "Мені сподобалося + noun". These issues, along with missing plan connectors and a structural typo, require revision.

I am ready to output.
## Linguistic Scan
No linguistic errors found in general Ukrainian usage (the module successfully avoids common Russianisms and Surzhyk), but there is a critical grammatical explanation error regarding the past tense of verbs like "міг" and "ніс".

## Exercise Check
- `<!-- INJECT_ACTIVITY: quiz-aspect-choice -->` appears at the end of Section 1 (tests aspect choice).
- `<!-- INJECT_ACTIVITY: match-up-travel-verbs -->` appears at the end of Section 2 (tests motion verbs).
- `<!-- INJECT_ACTIVITY: fill-in-travel-narrative -->` appears at the end of Section 3 (tests narrative verbs/aspects).
- `<!-- INJECT_ACTIVITY: error-correction-travel -->` appears at the end of Section 4 (tests common mistakes).
All markers match the plan's activity hints and are evenly distributed across the sections.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | Missed some time connectors required by the plan ("після цього", "тим часом", "у цей момент") and the preposition "з + Gen" in Section 2. Missed the recommended word "сувенір". |
| 2. Linguistic accuracy | 5/10 | Critical error in phonetic/grammatical explanation: Claims verbs like "міг, ніс, біг" have a "-в" suffix ("Even for verbs with challenging consonant stems like міг (could), ніс (carried), or біг (ran), Ukrainian stubbornly maintains its unique phonetic pattern"). In reality, they drop this suffix in the masculine past tense form. Also, awkward use of possessive pronoun "мій квиток" instead of the natural "свій квиток". |
| 3. Pedagogical quality | 6/10 | Critical error: Teaches that for "Мені сподобалося [Noun]" the verb always stays neuter, giving the misleading rule "Після цієї фрази ви можете легко додати інфінітив або звичайний іменник: «Мені дуже сподобалося це старе місто»", without explaining gender agreement for nouns of other genders. |
| 4. Vocabulary coverage | 9/10 | Good coverage overall, but missed the recommended word "сувенір" in the narrative sections. |
| 5. Exercise quality | 10/10 | Markers are placed well and match the plan's activity hints. |
| 6. Engagement & tone | 9/10 | Warm, encouraging, and natural teacher persona without excessive fluff. |
| 7. Structural integrity | 9/10 | Missing word in the model answer block ("Це було справді !"). Word count is solid (2745 words). |
| 8. Cultural accuracy | 10/10 | Excellent points about "двірець" vs "вокзал" and the importance of using Ukrainian city names like Київ instead of Russian variants. |
| 9. Dialogue & conversation quality | 9/10 | Dialogues are natural and incorporate the targeted grammar structures well. |

## Findings
[1. Plan adherence] [Major]
Location: `Ось кілька дуже важливих слів для розповіді: **спочатку** (at first), **потім** (then), **раптом** (suddenly), та **нарешті** (finally).`
Issue: Several time connectors required by the plan (після цього, тим часом, у цей момент) are missing from the explanation.
Fix: Add the missing connectors to the list.

[1. Plan adherence] [Major]
Location: `Але ми використовуємо прийменник «на» зі знахідним відмінком для відкритих просторів чи подій. Наприклад: на море, на фестиваль, на концерт.`
Issue: The preposition "з/зі + Gen" (from a place) was required by the plan but omitted from the explanation in Section 2.
Fix: Add an explanation for "з/зі" + Genitive.

[1. Plan adherence] [Minor]
Location: `Вдень ми дуже багато **ходили** (walked) по місту, а ввечері ми **відвідали** (visited) оперу.`
Issue: The recommended vocabulary word "сувенір" is missing from the entire text.
Fix: Add "купували сувеніри" to the example sentence.

[2. Linguistic accuracy] [Critical]
Location: `Notice how incredibly stable the -в sound is for masculine verbs in Ukrainian. Even for verbs with challenging consonant stems like **міг** (could), **ніс** (carried), or **біг** (ran), Ukrainian stubbornly maintains its unique phonetic pattern compared to neighboring languages.`
Issue: Factually incorrect. The masculine past tense of verbs like "міг", "ніс", "біг" is formed by dropping the "-в" suffix, not maintaining it.
Fix: Correct the rule to state that these verbs do NOT have the suffix in the masculine form.

[2. Linguistic accuracy] [Major]
Location: `Раптом я з жахом зрозумів, що загубив мій квиток! Я швидко почав шукати його скрізь. Нарешті я знайшов його в кишені моєї куртки.`
Issue: Unnatural use of possessive pronouns. In Ukrainian, it's more natural to use "свій" instead of "мій" when the object belongs to the subject.
Fix: Replace "мій/моєї" with "свій/своєї".

[3. Pedagogical quality] [Critical]
Location: `You use this specific construction with the dative case pronoun («мені») and the neuter past tense form of the verb. Після цієї фрази ви можете легко додати інфінітив або звичайний іменник: «Мені сподобалося гуляти по місту» або «Мені дуже сподобалося це старе місто».`
Issue: The rule is misleading. It implies the verb is ALWAYS neuter when followed by a noun, failing to explain that the verb must agree in gender with the noun (e.g., "Мені сподобався музей").
Fix: Clarify that the neuter is for infinitives, and the verb must agree with the noun's gender if a noun is used.

[6. Engagement & tone] [Minor]
Location: `Якщо подорож змогла вам **сподобатися** (to like), як правильно сказати про це українською?`
Issue: The phrasing "змогла вам сподобатися" is awkward and feels like an unnatural calque of "was able to be liked".
Fix: Change to "Якщо подорож вам дуже сподобалася".

[7. Structural integrity] [Critical]
Location: `Це було справді !`
Issue: A word is missing at the end of the sentence before the exclamation mark.
Fix: Add "неймовірно" before the exclamation mark.

[1. Plan adherence] [Minor]
Location: `Це слова **спочатку** (at first), **потім** (then), **раптом** (suddenly), **нарешті** (finally).`
Issue: The summary misses the newly added time connectors.
Fix: Update the summary to include the missing time connectors.

## Verdict: REVISE
The module covers the topic well and has excellent cultural notes, but it contains two critical grammatical/phonetic errors: claiming verbs like "міг" and "ніс" maintain the "-в" suffix, and providing a misleading rule about gender agreement for "Мені сподобалося + noun". These issues, along with missing plan connectors and a structural typo, require revision.

<fixes>
- find: "Ось кілька дуже важливих слів для розповіді: **спочатку** (at first), **потім** (then), **раптом** (suddenly), та **нарешті** (finally). Слово «спочатку» дає ідеальний старт вашій історії."
  replace: "Ось кілька дуже важливих слів для розповіді: **спочатку** (at first), **потім** (then), **після цього** (after that), **тим часом** (meanwhile), **у цей момент** (at that moment), **раптом** (suddenly), та **нарешті** (finally). Слово «спочатку» дає ідеальний старт вашій історії."
- find: "Раптом я з жахом зрозумів, що загубив мій квиток! Я швидко почав шукати його скрізь. Нарешті я знайшов його в кишені моєї куртки."
  replace: "Раптом я з жахом зрозумів, що загубив свій квиток! Я швидко почав шукати його скрізь. Нарешті я знайшов його в кишені своєї куртки."
- find: "Notice how incredibly stable the -в sound is for masculine verbs in Ukrainian. Even for verbs with challenging consonant stems like **міг** (could), **ніс** (carried), or **біг** (ran), Ukrainian stubbornly maintains its unique phonetic pattern compared to neighboring languages."
  replace: "Notice that most verbs use the **-в** sound for masculine forms. However, some verbs with consonant stems, like **міг** (could from *могти*), **ніс** (carried from *нести*), or **біг** (ran from *бігти*), do not have this suffix in the masculine form."
- find: "Але ми використовуємо прийменник «на» зі знахідним відмінком для відкритих просторів чи подій. Наприклад: на море, на фестиваль, на концерт."
  replace: "Але ми використовуємо прийменник «на» зі знахідним відмінком для відкритих просторів чи подій. Наприклад: на море, на фестиваль, на концерт. Щоб сказати, звідки ви приїхали, використовуйте прийменник «з» або «зі» з родовим відмінком: прилетіти з Києва, повернутися зі Львова."
- find: "Вдень ми дуже багато **ходили** (walked) по місту, а ввечері ми **відвідали** (visited) оперу"
  replace: "Вдень ми дуже багато **ходили** (walked) по місту, купували **сувеніри** (souvenirs), а ввечері ми **відвідали** (visited) оперу"
- find: "Якщо подорож змогла вам **сподобатися** (to like), як правильно сказати про це українською?"
  replace: "Якщо подорож вам дуже **сподобалася** (to like), як правильно сказати про це українською?"
- find: "You use this specific construction with the dative case pronoun («мені») and the neuter past tense form of the verb. Після цієї фрази ви можете легко додати інфінітив або звичайний іменник: «Мені сподобалося гуляти по місту» або «Мені дуже сподобалося це старе місто»."
  replace: "You use this specific construction with the dative case pronoun («мені») and the past tense verb. Якщо ви додаєте інфінітив, дієслово завжди має середній рід: «Мені сподобалося гуляти по місту». Якщо ви додаєте іменник, дієслово узгоджується з його родом: «Мені сподобалося місто» (neuter), «Мені сподобався музей» (masculine), або «Мені сподобалася вулиця» (feminine)."
- find: "Це було справді !"
  replace: "Це було справді неймовірно!"
- find: "Це слова **спочатку** (at first), **потім** (then), **раптом** (suddenly), **нарешті** (finally)."
  replace: "Це слова **спочатку** (at first), **потім** (then), **після цього** (after that), **тим часом** (meanwhile), **у цей момент** (at that moment), **раптом** (suddenly), **нарешті** (finally)."
</fixes>
