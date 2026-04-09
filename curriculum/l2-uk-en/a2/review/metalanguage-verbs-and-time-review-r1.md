黎thought
CRITICAL INSTRUCTION 1: Prioritize specific tools over generic ones. Use MCP tools for linguistic verification rather than making assumptions.
CRITICAL INSTRUCTION 2: Related tools for checking language/style: `mcp_rag_search_style_guide`, `mcp_rag_search_text`, `mcp_rag_search_definitions`, `mcp_rag_query_pravopys`, `mcp_rag_verify_words`. I will use `mcp_rag_search_style_guide` to check potential Russianisms and `mcp_rag_search_text` to verify textbook grammar.

So textbooks use "незмінна частина мови". My suspicion of "незмінювана" was wrong, "незмінна" is entirely correct and standard in school textbooks.
"незмінна частина мови" is used in Grade 7 Zabolotnyi, Grade 4 Zahariychuk, etc.

Let's check "відношення дії до нашої реальності" (relation of action to our reality).
In Ukrainian grammar, it's often "відношення дії до дійсності". So it's acceptable.

Let's check "Давайте" rule from the plan:
"Here is a critical decolonization rule for authentic Ukrainian phrasing. Never use the Russian calque "давайте" to form group commands. "
Content says: "Замість «давайте підемо», ми завжди кажемо коротко «ходімо». Замість «давайте працювати», ми чудово кажемо «працюймо»."
This is 100% correct.

Wait, check "відношення" vs "ставлення" in the style guide. I'll search `mcp_rag_search_style_guide` for `відношення`.
黎thought
CRITICAL INSTRUCTION 1: Use specific tools. I'm verifying style with `mcp_rag_search_style_guide`.
CRITICAL INSTRUCTION 2: Related tools: `mcp_rag_verify_words`, `mcp_rag_search_text`. I will use `mcp_rag_search_text` if needed to verify "ставлення".

Wait, actually, I remember Антоненко-Давидович writes about "Відношення і ставлення". Let's search `ставлення`.
Let's check "дієвідміна" rules in the text.
"Перша дієвідміна (first conjugation) має голосні літери «е» або «є» у закінченнях. Наприклад: «ти пиш-е-ш», «він чита-є», «ми зна-є-мо». Друга дієвідміна (second conjugation) має голосні літери «и» або «ї» у закінченнях. Наприклад: «ти говор-и-ш», «вона сто-ї-ть», «ми мовч-и-мо»."
"Також можна дивитися на форму третьої особи множини. Перша дієвідміна завжди закінчується на «-уть» або «-ють» (вони пишуть, вони читають). Друга дієвідміна закінчується на «-ать» або «-ять» (вони кричать, вони говорять)."
Wait! Let's check "ми мовч-и-мо" and "вони кричать".
Is "мовчати" 2nd conjugation?
я мовчу
ти мовчиш
він мовчить
ми мовчимо
ви мовчите
вони мовчать. Yes, it's 2nd conjugation.

Is "кричати" 2nd conjugation?
я кричу
ти кричиш
він кричить
ми кричимо
ви кричите
вони кричать. Yes, it's 2nd conjugation.

Wait, look at this phrase from the generated content:
`"ч. Р.", "ж. Р.", "с. Р."`
The capital R. Is it ever written with a capital R in dictionaries?
Let's check Goroh or other dictionaries.
`ч. р.` is the standard abbreviation. `р.` stands for `рід`. Why would it be capitalized?
Let me check Goroh abbreviations. I'll search `mcp_rag_search_text` for abbreviations in dictionaries.
黎thought
CRITICAL INSTRUCTION 1: Use specific tools. I will not use shell tools since I have MCP tools.
CRITICAL INSTRUCTION 2: Related tools: `mcp_rag_verify_words`, `mcp_rag_search_text`, `mcp_rag_search_definitions`.

Okay, so it should be lowercase `ч. р.` and `ж. р.`. Capitalizing it is a typographical error.
In the generated content:
`**ч. Р.** | чоловічий рід`
`**ж. Р.** | жіночий рід`
`**с. Р.** | середній рід`
And: `книга (ім., ж. Р., одн.)`

Let's check vocabulary and plan adherence.
Required vocabulary:
- дієслово (verb) - Yes
- час (tense, time) - Yes
- вид (aspect) - Yes
- доконаний (perfective) - Yes
- недоконаний (imperfective) - Yes
- спосіб (mood, manner) - Yes
- дієвідміна (conjugation class) - Yes
- особа (person, grammatical) - Yes
- прислівник (adverb) - Yes
- словник (dictionary) - Yes

Recommended vocabulary:
- дійсний спосіб - Yes
- наказовий спосіб - Yes
- умовний спосіб - Yes
- скорочення - Yes

Check sections and word counts:
Plan:
1. Дієслово: категорії та терміни (600 words). Content covers tense, aspect, mood.
2. Дієвідміна та особа (450 words). Content covers conjugation, person, number, and morph analysis.
3. Словникова грамотність: читаємо словник (550 words). Content has dialogue, table of abbreviations.
4. Прислівник: види та приклади (400 words). Content covers adverbs of place, time, manner.

Let's check the dialogue:
```markdown
> — **Марк:** Вибачте, я зараз дивлюся у **словник** *(dictionary)* Goroh.pp.ua. Тут є нове слово «бачити». Але що означають ці маленькі букви поруч: «недок.» і «дієсл.»? *(Excuse me, I am looking in the dictionary Goroh.pp.ua right now. Here is the new word "бачити". But what do these small letters nearby mean: "недок." and "дієсл."?)*
> — **Вчителька:** Це дуже гарне і важливе питання! *(This is a very good and important question!)* Це спеціальні граматичні **скорочення** *(abbreviations)*. Словники завжди використовують такий короткий код, щоб зекономити місце. *(Dictionaries always use such a short code to save space.)*
> — **Марк:** Тобто це граматика? *(So this is grammar?)*
> — **Вчителька:** Так, це ключова граматична інформація. *(Yes, this is key grammatical information.)* Слово «дієсл.» означає дієслово. А «недок.» означає недоконаний вид. Коли ви самостійно читаєте словник, ви повинні розуміти цей код. *(The word "дієсл." means verb. And "недок." means imperfective aspect. When you independently read a dictionary, you must understand this code.)*
```
Dialogue looks good. Fulfills the plan: "situation: A student trying to look up a word in an online dictionary...".
But wait, what about the FIRST dialogue situation from the plan?
Plan dialogue_situations:
1. situation: "A student asking the teacher to explain verb aspect terminology..."
Functions: "asking about grammar concepts", "understanding Ukrainian terminology"...
Did the content include this dialogue? Let me search the content. I do not see a dialogue about verb aspect terminology! The only dialogue is the one about reading the dictionary (Goroh.pp.ua).
Wait! The plan specifies TWO dialogue situations:
1. "A student asking the teacher to explain verb aspect terminology..."
2. "A student trying to look up a word in an online dictionary..."
The generated content only has the SECOND dialogue. The first dialogue is MISSING. This is a deduction for Dimension 1 (Plan adherence) and Dimension 9 (Dialogue & conversation quality).
Let me double check the generated content.
"## Дієслово: категорії та терміни" - no dialogue here.
"## Дієвідміна та особа" - no dialogue here.
"## Словникова грамотність: читаємо словник (~550 words)" - dialogue present.
So Dialogue 1 is missing! I must add it to findings.

What about "Словникова грамотність: читаємо словник (~550 words)"? The heading itself contains "(~550 words)" in the text! This is a meta-commentary artifact!
`## Словникова грамотність: читаємо словник (~550 words)`
The plan section title is `Словникова грамотність: читаємо словник (Dictionary Literacy: Reading a Dictionary)`. The writer included `(~550 words)` from the prompt's instruction or internal planning into the actual H2 header!
Wait, in the plan it says:
`section: 'Словникова грамотність: читаємо словник (Dictionary Literacy: Reading a Dictionary)'`
And `words: 550`
So the AI put `(~550 words)` into the header. This is a Structural Integrity deduction and needs a fix.

Wait, check the first heading in the content:
`## Дієслово: категорії та терміни`
Second:
`## Дієвідміна та особа`
Third:
`## Словникова грамотність: читаємо словник (~550 words)`
Fourth:
`## Прислівник: види та приклади`
Fifth:
`## Підсумок`

So the translation in the header for the first two sections was dropped, but for the third it kept the word count? No, the plan says:
`section: 'Дієслово: категорії та терміни (The Verb: Categories and Terms)'`
The content just used `## Дієслово: категорії та терміни`. Which is fine, they are not supposed to put English in the header if they can avoid it, but adding `(~550 words)` is an error.

Let's check the activities.
Plan activity_hints:
1. match-up (focus: Match verb category terms to their definitions, items: 8)
2. quiz (focus: Read a dictionary entry and answer questions..., items: 8)
3. group-sort (focus: Sort verb forms by час, items: 8)
4. fill-in (focus: Complete sentences about verbs using Ukrainian metalanguage terms, items: 8)

Content markers:
1. `<!-- INJECT_ACTIVITY: match-up-verb-terms -->` (After Спосіб)
2. `<!-- INJECT_ACTIVITY: group-sort-verb-tense -->` (After Дієвідміна)
3. `<!-- INJECT_ACTIVITY: quiz-quiz-dictionary-literacy -->` (After Словник)
4. `<!-- INJECT_ACTIVITY: fill-in-fill-in-metalanguage -->` (After Прислівник)

The order of markers:
- match-up is placed after "Дієслово: категорії та терміни".
- group-sort is placed after "Дієвідміна та особа".
- quiz is placed after "Словникова грамотність...".
- fill-in is placed after "Прислівник...".

Wait, does the group-sort marker `group-sort-verb-tense` match the teaching?
The group-sort focus is "Sort verb forms by час (минулий, теперішній, майбутній)".
The concept of "час" is taught in the FIRST section ("Дієслово: категорії та терміни"), but the group-sort marker is placed at the end of the SECOND section ("Дієвідміна та особа").
Wait, the first section introduces час, вид, спосіб. The match-up activity tests terms. Then the second section teaches дієвідміна and особа, but the activity after it is sorting by tense (group-sort-verb-tense).
Actually, the second section ends with morphological analysis which includes determining tense, but placing the tense sorting there is a bit delayed. However, it's not a severe error.

Let's check the exercise type naming: `quiz-quiz-dictionary-literacy` and `fill-in-fill-in-metalanguage`. It duplicated the activity type in the ID. This is acceptable, the build pipeline will handle the ID.

Is there any linguistic error?
"наші улюблені інструменти для щоденного планування свого життя" - calque? "щоденне планування свого життя" is okay.
"Цей тип пояснює нам, «як» саме ми робимо певну дію." - okay.

Wait, check "Ця категорія логічно показує, як саме дієслово змінюється."
"Ця категорія реальності називається дійсний спосіб (indicative mood). Якщо дія повністю реальна, вона завжди має минулий, теперішній або майбутній час." - technically true.
"Друга і мабуть найважливіша категорія — це вид. Це фундаментальна різниця у всіх слов'янських мовах."

Wait, look at this: "Друга дієвідміна закінчується на «-ать» або «-ять» (вони кричать, вони говорять)."
Actually, the 3rd person plural for 2nd conjugation is `-ать` / `-ять`.
But earlier it says: "Друга дієвідміна (second conjugation) має голосні літери «и» або «ї» у закінченнях. Наприклад: «ти говор-и-ш», «вона сто-ї-ть», «ми мовч-и-мо»."
Is "мовчимо" correctly divided? "мовч-и-мо". Yes. "сто-ї-ть". Yes. "говор-и-ш". Yes.

Wait, look at the vocabulary:
"Слово «дієсл.» означає дієслово."
"А «недок.» означає недоконаний вид."

Check abbreviations capital letters:
```markdown
| **ч. Р.** | чоловічий рід | *masculine gender* |
| **ж. Р.** | жіночий рід | *feminine gender* |
| **с. Р.** | середній рід | *neuter gender* |
```
And:
```markdown
Перший приклад — це слово «книга». У словнику ми бачимо такий запис: **книга** (ім., ж. Р., одн.). Що це означає для нас? Ми відразу розуміємо, що це іменник жіночого роду в однині.
```
And in the summary:
```markdown
6. **ч.р.** — чоловічий рід *(masculine gender)*
7. **ж.р.** — жіночий рід *(feminine gender)*
8. **с.р.** — середній рід *(neuter gender)*
```
In the summary, it correctly uses lowercase `ч.р.`, `ж.р.`, `с.р.`! But in the table and text, it uses `ч. Р.`. This is inconsistent and a typographical error. I will fix it.

Let's check another thing: "Ви, мабуть, помітили, що дієслова мають різні закінчення в теперішньому часі. Чому ми кажемо «ти пишеш», але при цьому кажемо «ти говориш»?"
Perfect Ukrainian.

Let's check "Коли ми говоримо про себе, ми використовуємо першу особу (first person). Це займенники «я» (I) та «ми» (we). Коли ми говоримо з кимось прямо, це друга особа (second person)."
"прямо" here might be a calque of "напрямую" / "говорить прямо с кем-то". "Звертаємося до когось безпосередньо" is better. "Говоримо з кимось прямо" is understandable but slightly colloquial. It's minor, I'll leave it.

Check English text:
"Welcome to the language of the classroom."
"Why is this so important for us right now?"
"You will see grammatical terms instead of English explanations. Knowing these terms is the key to independent learning."
"Only verbs that state real facts have tenses."
"Let's closely compare two past tense verbs you already know well."
"Here is a critical decolonization rule for authentic Ukrainian phrasing. Never use the Russian calque "давайте" to form group commands."

This is all acceptable metalanguage and instructions, conforming to "teacher persona". It uses English to frame important concepts, which is fine for A2.

Wait! The plan specifies TWO dialogue situations:
1. `situation: "A student asking the teacher to explain verb aspect terminology — Що означає 'доконаний вид'? Як визначити дієвідміну? Teacher uses familiar verbs as examples"`
2. `situation: "A student trying to look up a word in an online dictionary — reading the entry aloud and asking a classmate what the abbreviations mean"`

The generated content completely missed the FIRST dialogue.
I must deduct points for Plan Adherence and add a finding. Since I cannot generate a full dialogue in `<fixes>` because I must use deterministic find/replace for small fixes, I'll provide an `insert_after` to insert the missing dialogue, or if it's too large, I'll just formulate a targeted fix for it.
Wait! I can write a dialogue and insert it using `insert_after`? No, the instructions say "For word count issues: add content as a new insert_after: entry instead of find/replace". A missing dialogue can be added using `insert_before` or `insert_after`?
Actually, the instructions say:
"For word count issues: add content as a new insert_after: entry instead of find/replace"
But wait, if I add a whole dialogue, I can just use a `find`/`replace` to replace a paragraph with the paragraph + dialogue.
Let's see where the first dialogue belongs.
"A student asking the teacher to explain verb aspect terminology..."
It fits perfectly in the "Дієслово: категорії та терміни" section, right before the aspect explanation or after it.
Let's insert it before the aspect explanation:
"Друга і мабуть найважливіша категорія — це вид. Це фундаментальна різниця у всіх слов'янських мовах. Вид показує, як саме протікає наша дія."
I will replace this with:
```yaml
- find: "Друга і мабуть найважливіша категорія — це вид. Це фундаментальна різниця у всіх слов'янських мовах. Вид показує, як саме протікає наша дія."
  replace: "> — **Емма:** Вибачте, я часто бачу в підручнику термін «доконаний вид». Що це означає? *(Excuse me, I often see the term "perfective aspect" in the textbook. What does this mean?)*\n> — **Вчитель:** Це чудове запитання. Вид показує, як саме протікає дія: чи це довгий процес, чи швидкий результат. *(This is an excellent question. Aspect shows exactly how an action flows: whether it is a long process or a quick result.)*\n> — **Емма:** Тобто це різниця між «робити» і «зробити»? *(So it's the difference between "to do" and "to have done"?)*\n> — **Вчитель:** Саме так! Ви вже знаєте ці слова, тепер ми просто даємо їм офіційні назви. *(Exactly! You already know these words, now we are just giving them official names.)*\n\nДруга і мабуть найважливіша категорія — це вид. Це фундаментальна різниця у всіх слов'янських мовах. Вид показує, як саме протікає наша дія."
```
This is a perfect fix for the missing dialogue.

Let's check the second dialogue. The plan says:
"A student trying to look up a word in an online dictionary — reading the entry aloud and asking a classmate what the abbreviations mean"
The generated content:
"Марк: Вибачте, я зараз дивлюся у словник (dictionary) Goroh.pp.ua... Вчителька: Це дуже гарне..."
It uses "Марк" and "Вчителька" (Teacher). But the plan says "asking a classmate"! This is a slight deviation from the plan, but acceptable. I won't penalize it heavily, but I can change "Вчителька" to "Анна" (classmate) in the replace if I want. Wait, the generated text says "Вчителька:" which is fine, teacher is okay. I will leave it to avoid unnecessary fixes, but it is a minor plan deviation.

Let's check "умовний спосіб (conditional — label only: читав би. Production is B1; here we learn the term so learners can read grammar references)."
Generated content:
"Третій тип — це умовний спосіб (conditional mood). Він показує наші мрії або цікаві гіпотетичні ситуації. Наприклад: «Я б пішов у кіно сьогодні ввечері»."
It includes the label and an example, which matches the plan. Production is not taught. Good.

What about "знайти шість ключових категорій"?
"Крок перший: яка це частина мови (part of speech)? Це дієслово..."
This perfectly matches the morph analysis.

Are there any formatting artifacts?
`## Словникова грамотність: читаємо словник (~550 words)`
I will fix this:
```yaml
- find: "## Словникова грамотність: читаємо словник (~550 words)"
  replace: "## Словникова грамотність: читаємо словник"
```

Let's check `ч. Р.` vs `ч. р.`
```yaml
- find: "| **ч. Р.** | чоловічий рід | *masculine gender* |"
  replace: "| **ч. р.** | чоловічий рід | *masculine gender* |"
- find: "| **ж. Р.** | жіночий рід | *feminine gender* |"
  replace: "| **ж. р.** | жіночий рід | *feminine gender* |"
- find: "| **с. Р.** | середній рід | *neuter gender* |"
  replace: "| **с. р.** | середній рід | *neuter gender* |"
- find: "**книга** (ім., ж. Р., одн.)"
  replace: "**книга** (ім., ж. р., одн.)"
```
Wait, let's search the text to ensure there are no other instances of `Р.`
"Якщо ви знаєте, що нове слово має позначку «ж. Р.», ви точно знаєте, що треба сказати «гарна», а не «гарний»."
```yaml
- find: "позначку «ж. Р.»"
  replace: "позначку «ж. р.»"
```

Let's check the Russianisms again.
Is "улоговина" in the generated text? No, that was in the textbook chunk.
"Слово «купував» — це минулий час, недоконаний вид. Це означає, що ви просто ходили по магазину і дуже довго вибирали речі." -> "довго вибирали речі" is correct.
"Слово «купив» — це минулий час, доконаний вид. Це означає конкретний результат: ви вже дали гроші касиру і взяли свій товар." -> correct.
"відношення дії до нашої реальності" - checked, it's correct terminology.
"Друга велика і популярна група — це прислівник часу" -> "популярна" is slightly colloquial but fine.

Are there any other errors?
"Ми використовуємо його кожного дня для наказів, прохань або корисних порад." -> "кожного дня" vs "щодня". Both are fine.
"Але найголовніше правило — ми знаємо, що це дієслово ніколи не має форм теперішнього часу!" -> True, perfective verbs do not have present tense in Ukrainian.
"Ви не можете сказати «я зроблю це зараз», якщо ви маєте на увазі процес, який зараз триває. Форма «я зроблю» — це вже проста форма майбутнього часу." -> Excellent explanation.

Wait, check the table of verbs in "Дієвідміна та особа":
| Число | 1-ша особа | 2-га особа | 3-тя особа |
| :--- | :--- | :--- | :--- |
| **Однина** | я | ти | він, вона, воно |
| **Множина** | ми | ви | вони |
This is correct.

Let's review the score.
1. Plan adherence:
- Missing first dialogue situation from the plan. Deduct 2 points. Score: 8/10.
Evidence: The plan required two dialogues, including one where a student asks the teacher about verb aspect ("Що означає 'доконаний вид'?"). This dialogue is entirely absent from the content.

2. Linguistic accuracy:
- Typographical error in dictionary abbreviations: capitalized `Р.` in `ч. Р.`, `ж. Р.`, `с. Р.`. In Ukrainian dictionary abbreviations, gender is written in lowercase (`ч. р.`, `ж. р.`, `с. р.`). As seen in the summary list at the end of the module which uses `ч.р.`. Deduct 1 point. Score: 9/10.
Evidence: `**ч. Р.** | чоловічий рід`, `книга (ім., ж. Р., одн.)`, `позначку «ж. Р.»`.

3. Pedagogical quality:
- Good teacher persona, clear explanations, good comparisons (купував vs купив). Validated "давайте" translation. The morphological analysis steps are excellent. Score: 10/10.
Evidence: The step-by-step breakdown of the word "читаємо" is a perfect pedagogical tool for applying the taught categories.

4. Vocabulary coverage:
- All required vocabulary covered. Recommended vocabulary covered. Score: 10/10.
Evidence: All terms (дієслово, час, вид, доконаний, недоконаний, спосіб, дієвідміна, особа, прислівник, словник) are clearly introduced and bolded.

5. Exercise quality:
- Markers are present, but `group-sort-verb-tense` is placed after the "Дієвідміна та особа" section instead of the section that actually teaches tenses ("Дієслово: категорії та терміни"). Score: 9/10.
Evidence: `<!-- INJECT_ACTIVITY: group-sort-verb-tense -->` is at the end of section 2, not section 1 where tense is taught. However, it's not a critical failure as section 2 discusses morphological analysis which includes tense.

6. Engagement & tone:
- Good tone, supportive teacher. "Welcome to the language of the classroom." Score: 10/10.
Evidence: The tone is encouraging but focuses on substantial language learning goals.

7. Structural integrity:
- The writer included the word count target from the plan directly into the H2 header. Deduct 2 points. Score: 8/10.
Evidence: The heading reads `## Словникова грамотність: читаємо словник (~550 words)` instead of just the title.

8. Cultural accuracy:
- Good explanation of "давайте" calque. Score: 10/10.
Evidence: Explicitly addresses the decolonization rule regarding the Russian calque "давайте" and provides correct Ukrainian synthetic forms (ходімо, працюймо).

9. Dialogue & conversation quality:
- The dialogue about dictionary abbreviations is good, but the plan requested it to be with a "classmate", and the generated content uses "Вчителька". Also, the first dialogue is missing entirely (penalized in Adherence). The one dialogue present is a bit teacher-student transactional. Score: 9/10.
Evidence: Dialogue uses "Вчителька" instead of a classmate as requested in the plan, but the flow is natural.

Let's summarize the findings:
1. [Dimension 1] [MAJOR]
Location: Section `## Дієслово: категорії та терміни`
Issue: The plan required a dialogue situation where a student asks the teacher about verb aspect terminology ("Що означає 'доконаний вид'?"). This dialogue is completely missing.
Fix: Insert the missing dialogue before the explanation of "вид".

2. [Dimension 7] [MAJOR]
Location: `## Словникова грамотність: читаємо словник (~550 words)`
Issue: The writer leaked the word count target from the prompt into the actual H2 header.
Fix: Remove the `(~550 words)` artifact from the header.

3. [Dimension 2] [CRITICAL]
Location: `| **ч. Р.** | чоловічий рід |`, `**книга** (ім., ж. Р., одн.)`, `позначку «ж. Р.»`
Issue: Typographical error in dictionary abbreviations. "Рід" in abbreviations must be lowercase (`ч. р.`, `ж. р.`, `с. р.`), not capitalized `Р.`. This is a factual error in teaching dictionary literacy.
Fix: Change `ч. Р.` to `ч. р.` and similarly for all instances.

Are there any other errors?
Let's check the dialogue injection again.
```yaml
- find: "Друга і мабуть найважливіша категорія — це вид. Це фундаментальна різниця у всіх слов'янських мовах. Вид показує, як саме протікає наша дія."
  replace: "> — **Емма:** Вибачте, я часто бачу в підручнику термін «доконаний вид». Що це означає? *(Excuse me, I often see the term "perfective aspect" in the textbook. What does this mean?)*\n> — **Вчителька:** Це чудове запитання! Вид показує, як саме протікає дія: чи це довгий процес, чи швидкий результат. *(This is an excellent question! Aspect shows exactly how an action flows: whether it is a long process or a quick result.)*\n> — **Емма:** Тобто це різниця між «робити» і «зробити»? *(So it's the difference between "to do" and "to have done"?)*\n> — **Вчителька:** Саме так! Ви вже чудово знаєте ці слова, тепер ми просто даємо їм офіційні назви. *(Exactly! You already know these words perfectly well, now we are just giving them official names.)*\n\nДруга і мабуть найважливіша категорія — це вид. Це фундаментальна різниця у всіх слов'янських мовах. Вид показує, як саме протікає наша дія."
```
Wait, the prompt says "The find string MUST be an EXACT copy-paste from the module content".
Yes, I will copy-paste EXACTLY:
```yaml
- find: "Друга і мабуть найважливіша категорія — це вид. Це фундаментальна різниця у всіх слов'янських мовах. Вид показує, як саме протікає наша дія."
  replace: "> — **Емма:** Вибачте, я часто бачу в підручниках термін «доконаний вид». Що це означає? *(Excuse me, I often see the term "perfective aspect" in textbooks. What does this mean?)*\n> — **Вчителька:** Це чудове запитання! Вид показує, як саме протікає дія: чи це довгий процес, чи швидкий результат. *(This is an excellent question! Aspect shows exactly how an action flows: whether it is a long process or a quick result.)*\n> — **Емма:** Тобто це різниця між «робити» і «зробити»? *(So it's the difference between "to do" and "to have done"?)*\n> — **Вчителька:** Саме так! Ви вже чудово знаєте ці слова, тепер ми просто даємо їм офіційні граматичні назви. *(Exactly! You already know these words perfectly well, now we are just giving them official grammatical names.)*\n\nДруга і мабуть найважливіша категорія — це вид. Це фундаментальна різниця у всіх слов'янських мовах. Вид показує, як саме протікає наша дія."
```

Let's double check all exact instances of `Р.`:
```markdown
| **ч. Р.** | чоловічий рід | *masculine gender* |
| **ж. Р.** | жіночий рід | *feminine gender* |
| **с. Р.** | середній рід | *neuter gender* |
```
```yaml
- find: "| **ч. Р.** | чоловічий рід | *masculine gender* |\n| **ж. Р.** | жіночий рід | *feminine gender* |\n| **с. Р.** | середній рід | *neuter gender* |"
  replace: "| **ч. р.** | чоловічий рід | *masculine gender* |\n| **ж. р.** | жіночий рід | *feminine gender* |\n| **с. р.** | середній рід | *neuter gender* |"
```
Wait, does it have `| :--- | :--- | :--- |` before it? Yes, but I can match just the rows.
Let's see:
```yaml
- find: "| **ч. Р.** | чоловічий рід | *masculine gender* |\n| **ж. Р.** | жіночий рід | *feminine gender* |\n| **с. Р.** | середній рід | *neuter gender* |"
  replace: "| **ч. р.** | чоловічий рід | *masculine gender* |\n| **ж. р.** | жіночий рід | *feminine gender* |\n| **с. р.** | середній рід | *neuter gender* |"
```
Also:
```markdown
Перший приклад — це слово «книга». У словнику ми бачимо такий запис: **книга** (ім., ж. Р., одн.). Що це означає для нас?
```
```yaml
- find: "**книга** (ім., ж. Р., одн.)"
  replace: "**книга** (ім., ж. р., одн.)"
```
Also:
```markdown
Вивчіть ці скорочення напам'ять. Вони — ваш надійний ключ до успішного самостійного навчання. Коли ви знаєте, що нове слово має позначку «ж. Р.», ви точно знаєте, що треба сказати «гарна», а не «гарний».
```
```yaml
- find: "позначку «ж. Р.»"
  replace: "позначку «ж. р.»"
```

Let's check the marker placement. I noted that `group-sort-verb-tense` is after "Дієвідміна та особа" instead of after "Дієслово: категорії та терміни".
Is there another marker that was placed after section 1? `match-up-verb-terms`.
Yes, section 1 has `match-up-verb-terms`. Section 2 has `group-sort-verb-tense`.
If section 1 teaches tense, aspect, mood, and section 2 teaches conjugation and person, the activities are match-up (terms) and group-sort (tenses). Placing one after section 1 and one after section 2 ensures they are spread out. The second section ends with a morphological analysis that covers tense ("Крок другий: який це час? Це теперішній час..."), so it's a perfectly logical place for an activity about tense. I won't flag this as an error.

Let's check if the vocabulary table is missing.
"Note: Vocabulary tables (словник), video embeds, and external resource links are added by a downstream ENRICH step — do NOT penalize their absence or quality." - Checked.

Check English/metalanguage rules.
"Welcome to the language of the classroom."
"Why is this so important for us right now?"
"You will see grammatical terms instead of English explanations. Knowing these terms is the key to independent learning."
"Only verbs that state real facts have tenses."
"Let's closely compare two past tense verbs you already know well."
"Here is a critical decolonization rule for authentic Ukrainian phrasing. Never use the Russian calque "давайте" to form group commands."
Are there more than 100 words of English theory without a Ukrainian example?
No, these are short 1-2 sentence injections in a sea of Ukrainian text. This is fully compliant.

Check the exercise counts from the plan.
Plan:
match-up: 8
quiz: 8
group-sort: 8
fill-in: 8
Total: 32 items. The markers are all present. This is correct.

Let's write out the review.
I don't need any more tools, I have confirmed the rules and findings. I will structure the response exactly as required.

Are there any other Russianisms?
"фінальний результат" - acceptable in Ukrainian, though "кінцевий результат" is more native. Let's check `фінальний` in VESUM. It is in VESUM, and "фінальний" is widely used.
"довгий процес" - correct.
"протікає дія" - "протікати" is often a calque when used for processes (instead of liquids). Better is "відбувається дія" or "перебіг дії".
Let's check Антоненко-Давидович for "протікати".
黎thought
CRITICAL INSTRUCTION 1: Specific tools: `mcp_rag_search_definitions` to check "протікати".
CRITICAL INSTRUCTION 2: Related tools: `mcp_rag_search_definitions`, `mcp_rag_search_text`. I will use `mcp_rag_search_definitions` to see if "протікати" is used for actions.
黎thought
CRITICAL INSTRUCTION 1: Specific tools: `mcp_rag_search_definitions`. It returned no results, maybe because of conjugation or imperfective/perfective pair. Let's try `перебігати` or `протікати` in RAG. Actually, "дія протікає" is a common calque for "протекает" (processes). In Ukrainian, time or processes "минають", "тривають", "відбуваються". Let's check `mcp_rag_search_text` for "дія триває" vs "дія протікає".
黎thought
CRITICAL INSTRUCTION 1: Specific tools prioritize over generic ones. I am checking the usage of "протікати".
CRITICAL INSTRUCTION 2: Related tools for checking word usage/collocations: `mcp_rag_query_grac`, `mcp_rag_search_text`, `mcp_rag_search_style_guide`. `mcp_rag_search_text` shows textbook usage.

I see that "дія протікає" was NOT found in grammar contexts, only "річка протікає". The textbooks say: "дія відбувається".
So "дія протікає" is a calque from Russian "действие протекает". This is a Major Linguistic error.
Let's add a fix for it.
"Вид показує, як саме протікає наша дія."
"Вид показує, як саме протікає дія: чи це довгий процес..."
I will change it to "відбувається наша дія" and "відбувається дія".
Wait, the sentence in the text:
"Вид показує, як саме протікає наша дія."
I will replace it with:
```yaml
- find: "Вид показує, як саме протікає наша дія."
  replace: "Вид показує, як саме відбувається наша дія."
```
Is there another instance? I'll just change the one instance and my injected dialogue will also use "відбувається".
Wait, the injected dialogue will replace that exact sentence, so I will just write the injected dialogue correctly:
"Вид показує, як саме відбувається дія: чи це довгий процес, чи швидкий результат."

Let's double check if there's any other "протікає" in the text.
No.

I have enough findings. The score for Linguistic Accuracy will drop to 8/10 because of the capital "Р" and the calque "протікає дія".
The score for Plan Adherence is 8/10 because of the missing dialogue.
The score for Structural Integrity is 8/10 because of the word count artifact.

Final Scores:
1. Plan adherence: 8/10 (Missing dialogue 1)
2. Linguistic accuracy: 8/10 (Capital "Р" in dictionary abbreviations, calque "протікає наша дія")
3. Pedagogical quality: 10/10
4. Vocabulary coverage: 10/10
5. Exercise quality: 9/10 (Sort by tense placed after Section 2 instead of Section 1, but acceptable)
6. Engagement & tone: 10/10
7. Structural integrity: 8/10 (Word count artifact in header)
8. Cultural accuracy: 10/10
9. Dialogue & conversation quality: 8/10 (First dialogue missing, second dialogue altered "classmate" to "teacher")

Wait, "Антоненко-Давидович" has a specific entry on "протікати". Actually, many style guides say "протікати" is only for liquids. Processes "перебігають", "відбуваються", "минають", "тривають".
I'll add the finding.

I am ready to output the review.## Linguistic Scan
2 linguistic errors found:
1. **Calque**: "протікає наша дія" — "протікати" is used for liquids (rivers, pipes) in Ukrainian. Processes and actions "відбуваються", "тривають", or "перебігають". This is a calque from Russian "протекает действие". 
2. **Typographical/Factual Error**: Capitalizing the abbreviation for "рід" as `Р.` (`ч. Р.`, `ж. Р.`, `с. Р.`). Standard dictionary abbreviations in Ukrainian use lowercase (`ч. р.`, `ж. р.`, `с. р.`).

## Exercise Check
All four `<!-- INJECT_ACTIVITY: {id} -->` markers are present and correspond to the plan's `activity_hints`.
- `match-up-verb-terms` is present after the first section.
- `group-sort-verb-tense` is present after the second section. While tenses are taught in section 1, the morphological analysis in section 2 relies on identifying tenses, so this placement is acceptable.
- `quiz-quiz-dictionary-literacy` is present after the dictionary section.
- `fill-in-fill-in-metalanguage` is present after the adverbs section.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | The plan required two distinct dialogue situations. The second dialogue (about dictionary lookup) is present, but the first dialogue ("A student asking the teacher to explain verb aspect terminology") is entirely missing. |
| 2. Linguistic accuracy | 8/10 | The content incorrectly capitalizes the abbreviation for "рід" (`ч. Р.`) which is a factual error for dictionary literacy. It also uses the calque "протікає наша дія" instead of "відбувається наша дія". |
| 3. Pedagogical quality | 10/10 | Excellent pedagogical flow. The step-by-step morphological analysis of the word "читаємо" is a brilliant practical application of the concepts taught. |
| 4. Vocabulary coverage | 10/10 | All required and recommended vocabulary terms are naturally integrated and bolded throughout the text. |
| 5. Exercise quality | 9/10 | All planned activities are present and test the appropriate language skills. `group-sort-verb-tense` is placed after section 2, which is slightly delayed but still works well as a capstone to the morphological analysis. |
| 6. Engagement & tone | 10/10 | The teacher persona is encouraging and substantial without resorting to empty filler ("Welcome to the language of the classroom"). |
| 7. Structural integrity | 8/10 | The writer mistakenly included the prompt's word count target directly into the H2 header: `## Словникова грамотність: читаємо словник (~550 words)`. |
| 8. Cultural accuracy | 10/10 | Successfully addresses the decolonization rule regarding the Russian calque "давайте", providing authentic Ukrainian synthetic alternatives ("ходімо", "працюймо"). |
| 9. Dialogue & conversation quality | 8/10 | The provided dialogue flows naturally, but it alters the plan's instruction from "asking a classmate" to "Вчителька". Furthermore, the missing first dialogue significantly reduces the conversational density of the module. |

## Findings

[1. Plan adherence] [MAJOR]
Location: Section `## Дієслово: категорії та терміни`
Issue: The plan explicitly requires a dialogue where a student asks the teacher to explain verb aspect terminology (e.g., "Що означає 'доконаний вид'?"). This dialogue is missing from the module.
Fix: Insert the missing dialogue right before the explanation of "вид".

[2. Linguistic accuracy] [CRITICAL]
Location: `Вид показує, як саме протікає наша дія.`
Issue: Calque. In Ukrainian, actions do not "протікають" (flow like water); they "відбуваються" (happen/occur). This is a direct calque from Russian "протекает действие".
Fix: Change "протікає" to "відбувається" (this will be handled simultaneously with the dialogue insertion fix).

[7. Structural integrity] [MAJOR]
Location: `## Словникова грамотність: читаємо словник (~550 words)`
Issue: A prompt artifact/meta-commentary was leaked directly into the H2 header.
Fix: Remove `(~550 words)` from the header.

[2. Linguistic accuracy] [CRITICAL]
Location: `| **ч. Р.** | чоловічий рід |`, `**книга** (ім., ж. Р., одн.)`, `позначку «ж. Р.»`
Issue: Typographical error in teaching dictionary literacy. In Ukrainian dictionaries, the abbreviation for "рід" is always lowercase (`р.`), not capitalized.
Fix: Replace `Р.` with `р.` in all dictionary abbreviations.

## Verdict: REVISE
The module has excellent pedagogical structure and tone, but the missing dialogue, the word-count artifact in the header, and the factual errors regarding dictionary abbreviations must be fixed before publishing.

<fixes>
- find: "Друга і мабуть найважливіша категорія — це вид. Це фундаментальна різниця у всіх слов'янських мовах. Вид показує, як саме протікає наша дія."
  replace: "> — **Емма:** Вибачте, я часто бачу в підручниках термін «доконаний вид». Що це означає? *(Excuse me, I often see the term "perfective aspect" in textbooks. What does this mean?)*\n> — **Вчителька:** Це чудове запитання! Вид показує, як саме відбувається дія: чи це довгий процес, чи швидкий результат. *(This is an excellent question! Aspect shows exactly how an action occurs: whether it is a long process or a quick result.)*\n> — **Емма:** Тобто це різниця між «робити» і «зробити»? *(So it's the difference between "to do" and "to have done"?)*\n> — **Вчителька:** Саме так! Ви вже чудово знаєте ці слова, тепер ми просто даємо їм офіційні граматичні назви. *(Exactly! You already know these words perfectly well, now we are just giving them official grammatical names.)*\n\nДруга і мабуть найважливіша категорія — це вид. Це фундаментальна різниця у всіх слов'янських мовах. Вид показує, як саме відбувається наша дія."
- find: "## Словникова грамотність: читаємо словник (~550 words)"
  replace: "## Словникова грамотність: читаємо словник"
- find: "| **ч. Р.** | чоловічий рід | *masculine gender* |\n| **ж. Р.** | жіночий рід | *feminine gender* |\n| **с. Р.** | середній рід | *neuter gender* |"
  replace: "| **ч. р.** | чоловічий рід | *masculine gender* |\n| **ж. р.** | жіночий рід | *feminine gender* |\n| **с. р.** | середній рід | *neuter gender* |"
- find: "**книга** (ім., ж. Р., одн.)"
  replace: "**книга** (ім., ж. р., одн.)"
- find: "позначку «ж. Р.»"
  replace: "позначку «ж. р.»"
</fixes>
