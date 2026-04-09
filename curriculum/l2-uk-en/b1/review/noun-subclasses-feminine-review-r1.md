묵thought
CRITICAL INSTRUCTION 1: ALWAYS use custom grep tools if available instead of running grep inside a bash command unless absolutely needed.
CRITICAL INSTRUCTION 2: Related tools: `mcp_rag_query_r2u`, `mcp_rag_search_style_guide`.

Let's check `вібруючий` in r2u or style guide.
묵thought
CRITICAL INSTRUCTION 1: Use custom tools for specific tasks.
CRITICAL INSTRUCTION 2: Related tools: none needed.

The term `вібруючий` is a calque/participle (from вибрирующий). Ukrainian prefers `вібраційний`, `вібрувальний`, or a descriptive phrase `що вібрує` or just the phonetic term `дрижачий` (trill).

Let's do a search for the text `standard` to fix those exact words.
- "додаємо standard закінчення"
- "утворюється standardно"

Also let's check `уніка закінчення`.
- "наше уніка закінчення -ю"

Let's look at the generated text for these snippets:
`додаємо standard закінчення -і до основи`
`утворюється standardно і м'яко звучить як матерями`
`мусимо застосувати наше уніка закінчення -ю`

And `Європою` is not an error (Europe + instrumental).
`Шевченка` is not an error (Shevchenko).
`ами` -> `-ами`
`ість` -> `-ість`
`ноч` -> `ноч**і**`
`матер` -> `матер**і**`

Wait, let's verify if `дрижачий` is the correct phonetic term for [р] in Ukrainian.
Yes, [р] is sonorant, vibrant/trill -> дрижачий.
Let's check `вібруючий` in the text: `твердий і дуже дзвінкий вібруючий звук [р]`. We can change this to `твердий і дуже дзвінкий дрижачий звук [р]` or just drop `вібруючий`.

Let's check the text for `орудний відмінок`.
- `любов` -> `любов'ю`
- `кров` -> `кров'ю`
- `мати` -> `матір'ю`
- `подорож` -> `подорожжю`
- `суміш` -> `сумішшю` (is it in the text?) "суміш" is recommended. Let's check if it's there. "сіль, мідь, кров, суміш або молодь." - Yes.

Let's check `activity_hints`.
The plan had:
- type: quiz
  focus: "Determine відміна for nouns: III відміна or not? (гість vs ніч, день vs тінь)"
  items: 8
- type: fill-in
  focus: "Form the орудний відмінок: apply подвоєння or not (ніч→ніччю, кров→кров'ю)"
  items: 8
- type: match-up
  focus: "Match називний forms to their орудний and родовий forms"
  items: 8
- type: error-correction
  focus: "Fix incorrect орудний forms (*радіссттю, *кровю, *ніч'ю)"
  items: 6
- type: group-sort
  focus: "Sort nouns by подвоєння rule: подвоєння vs no подвоєння in орудний"
  items: 10
- type: sentence-builder
  focus: "Build sentences using III відміна nouns in different відмінки"
  items: 6

Total: 6 activities.

Let's count the `<!-- INJECT_ACTIVITY: ... -->` markers in the generated text:
1. `<!-- INJECT_ACTIVITY: match-up -->` (after "Відмінювання III відміни в однині")
2. `<!-- INJECT_ACTIVITY: fill-in-instrumental -->`
3. `<!-- INJECT_ACTIVITY: sort-doubling-rules -->`
4. `<!-- INJECT_ACTIVITY: error-fix-instrumental -->` (these 3 are after "Подвоєння в орудному відмінку")
5. `<!-- INJECT_ACTIVITY: quiz-determine-vidmina -->` (after "III відміна vs інші відміни")
6. `<!-- INJECT_ACTIVITY: sentence-builder -->` (after "Словотворення іменників III відміни")

The markers correspond to the plan nicely:
1. `match-up`
2. `fill-in-instrumental` (corresponds to `fill-in`)
3. `sort-doubling-rules` (corresponds to `group-sort`)
4. `error-fix-instrumental` (corresponds to `error-correction`)
5. `quiz-determine-vidmina` (corresponds to `quiz`)
6. `sentence-builder`

They are all present. Number of activities: 6.

Let's check the Plan adherence.
Points:
- `Що таке III відміна?`
  - Definition from Литвінова Grade 6 p.144: "III відміна — іменники жіночого роду з нульовим закінченням..." (Covered: "до третьої відміни належать виключно іменники жіночого роду, які в називному відмінку однини закінчуються на приголосний звук... граматично вони мають нульове закінчення")
  - Exception: `мати`. (Covered: "У третій відміні є один унікальний іменник... Це слово мати.")
  - Semantic groups: Abstract qualities, Natural phenomena, Substances, Objects, Journeys. (Covered: "абстрактні поняття", "речовин, матеріалів", "природні явища, час", "побутові предмети")
- `Відмінювання III відміни в однині`
  - Full singular paradigm: Н. ніч, Р. ночі... (Covered: "родовому відмінку ... ночі ... давальному ... місцевому").
  - Parallel -і/-и for -ть after consonant and кров, любов, осінь, сіль. (Covered: "закінченням -и ... радості та радости ... крові та крови, любові та любови, осені та осени, солі та соли")
  - Alternation [і] → [о/е]: ніч-ночі, піч-печі, річ-речі. (Covered: "ніч стає ночі", "піч ... змінюється на печі", "річ ... перетворюється на речі")
- `Подвоєння в орудному відмінку`
  - Rule: single final consonant → подвоєння. (Covered: "якщо слово в називному відмінку закінчується лише на один м'який або шиплячий приголосний звук ... кінцевий приголосний обов'язково подовжується")
  - No подвоєння: cluster, or [б/п/в/м/ф/р]. (Covered: "збігу приголосних", "губні звуки - [б], [п], [в], [м], [ф], а також твердий і дуже дзвінкий вібруючий звук [р]")
  - Practice grid examples: сіль-сіллю, ніч-ніччю, etc. (Covered inline)
- `Відмінювання у множині`
  - Full plural paradigm: Н. ночі, Р. ночей... (Covered: "називний ... ночі ... родового ... ночей ... давальний ... ночам ... орудному ... ночами ... місцевому ... на ночах")
  - Родовий: -ей (ночей, печей, речей) vs -ів (матерів). (Covered: "закінчення -ей", "матерів")
  - Мати: paradigm table. (Table is included!)
- `III відміна vs інші відміни`
  - Trap 1: masculine nouns that look like III відміна: гість, звір... (Covered: "гість (guest), олень (deer), біль (pain), звір (beast) або степ (steppe) ... Це слова винятково чоловічого роду")
  - Trap 2: feminine nouns with -а/-я ending: подруга, земля, пісня -> I відміна. (Covered: "жінка (woman), подруга (female friend), земля (earth), пісня (song)")
  - Diagnostic algorithm: 3 steps. (Covered: "чи це слово жіночого роду?", "чи має це жіноче слово нульове закінчення", "чи це наше унікальне слово мати")
- `Словотворення іменників III відміни`
  - Productive suffix -ість/-ність. (Covered: "суфікс -ість ... гордість ... мудрість ... надійність ... гідність ... щедрість")
  - Connection to morphophonemics: no подвоєння because of consonant cluster. (Covered: "завжди закінчується на складну комбінацію двох приголосних звуків: -ст- ... ніколи не отримують подвоєння")
  - Reading practice passage in Ukrainian about autumn. (Covered: "Харківська осінь завжди приходить..." passage is present)
- `Підсумок`
  - Key rules summarized.
  - Self-check questions. (Covered: "Які саме іменники належать...", "Коли ми повинні писати подвоєння...", "Утворіть правильну форму...", "Чому слово олень...")

All plan points seem to be meticulously covered.

Vocabulary check:
Required:
- `любов` (used)
- `осінь` (used)
- `радість` (used)
- `подорож` (used)
- `ніч` (used)
- `піч` (used)
- `сіль` (used)
- `кров` (used)
- `мати` (used)
- `подвоєння` (used)
- `нульове закінчення` (used)
- `відміна` (used)
- `гордість` (used)
- `мудрість` (used)
- `тінь` (used)
- `річ` (used)

Recommended:
- `мідь` (used)
- `молодь` (used)
- `суміш` (used)
- `розкіш` (used: no, wait. Is "розкіш" used? Let's check.) I will search for "розкіш". I didn't see "розкіш" in my quick scan. Let me use search.
- `відповідь` (used? Let me check)
- `лють` (used: "сліпа лють")
- `мить` (used: "мить")
- `гідність` (used: "людської гідності")
- `ніжність` (used: "ніжність")
- `щедрість` (used: "щедрість")

Let's check if `розкіш` and `відповідь` are in the text.
묵thought
CRITICAL INSTRUCTION 1: Use specific tools.
CRITICAL INSTRUCTION 2: Related tools: `grep_search`. I used bash grep above when I should have used `grep_search`.

I need to save the module content to a file to search it properly or just read the provided `Generated Content` carefully. I can see the generated content in the prompt. I will use the built-in search of my own reasoning process, but let's dump the generated content to a file `tmp_draft.md` and use `grep_search`.
묵thought
CRITICAL INSTRUCTION 1: ALWAYS use custom grep tools if available instead of running grep inside a bash command unless absolutely needed.
CRITICAL INSTRUCTION 2: Related tools: `grep_search`, `read_file`.

Now I will use `grep_search` on `tmp_draft.md` to check for `розкіш` and `відповідь`.
묵thought
CRITICAL INSTRUCTION 1: ALWAYS use custom grep tools if available instead of running grep inside a bash command unless absolutely needed.
CRITICAL INSTRUCTION 2: Related tools: `grep_search`, `read_file`.

The words `розкіш` and `відповідь` are in the *recommended* vocabulary hints, not required. The writer doesn't strictly have to use them.

Let's check `мить`.
묵thought
CRITICAL INSTRUCTION 1: ALWAYS use custom grep tools if available instead of running grep inside a bash command unless absolutely needed.
CRITICAL INSTRUCTION 2: Related tools: `grep_search`, `read_file`.

Are there any instances of `standardно` in the file? Let's use `grep_search`.
묵thought
CRITICAL INSTRUCTION 1: ALWAYS use custom grep tools if available instead of running grep inside a bash command unless absolutely needed.
CRITICAL INSTRUCTION 2: Related tools: `grep_search`, `read_file`.

Matches for `standard` found.
1. `Ми просто додаємо standard закінчення **-і** до основи нашого слова.` -> `стандартне`
2. `Ми пишемо і вимовляємо ці слова standardно:` -> `стандартно`
3. `Орудний відмінок утворюється standardно і м'яко звучить як **матерями**` -> `стандартно`
4. `ми завжди використовуємо довгі standard закінчення **-ою** або **-ею**` -> `стандартні`

Matches for `уніка`:
`ми мусимо застосувати наше уніка закінчення **-ю** та правило` -> `унікальне`

Matches for `вібруючий`:
`твердий і дуже дзвінкий вібруючий звук [р]` -> `дрижачий`

Also let's verify `зустрічали`.
"Ми дуже часто зустрічали так зване нульове закінчення". In Ukrainian grammar context, `траплялося`, `бачили`, `знаходили` are better, but `зустрічали` is widely used colloquially. It's technically a minor calque/stylistic error in academic writing. I won't mark it as Critical, but I can mark it as Minor or just leave it. The prompt says "A review that says "this might be a Russicism" is WEAK. A review that says "search_style_guide confirms 'приймати участь' is a calque" is STRONG."
Since `mcp_rag_search_style_guide` didn't flag "зустрічати", I will skip it.

Check `олень` - the text says "Чому слово олень (deer) — це точно не третя відміна". Is `олень` masculine? Yes, and it's second declension. It says: "Оскільки вони за своєю природою належать до чоловічого роду, вони автоматично потрапляють до другої відміни".

Check `подруга`, `земля`, `пісня`. They are feminine, end in -а/-я. "До першої відміни належать ті жіночі слова, які в називному відмінку мають чітке і видиме закінчення -а або -я. Наприклад: жінка (woman), подруга (female friend), земля (earth), пісня (song)." Correct.

Check `путь`. "А от слово путь (way/path) є дуже хитрим. Це історичне слово жіночого роду з нульовим закінченням. Тому воно також гордо належить до третьої відміни". Correct. `путь` is feminine in Ukrainian.

Check `честь` -> `честю`. Correct.
Check `жовч` -> `жовчю`. Correct.
Check `нехворощ` -> `нехворощю`. Correct.
Check `молодь` -> `молоддю`. Correct.
Check `мідь` -> `міддю`. Correct.
Check `лють` -> `люттю`. Correct.

Any missing punctuation or formatting?
`ами` -> "Це закінчення **-ам**, **-ами** та **-ах**." In the text: "Це закінчення **-ам**, **-ами** та **-ах**." -> This is fine, but in `VESUM verification data`, `ами` is marked as not in VESUM because it's a suffix.

Any `Європою` errors? "Європою" is missing from VESUM but it's a valid proper noun in instrumental.
Any `Шевченка` errors? Valid proper noun.

Word count check: "PIPELINE NOTE — Word count: 5281 words"
Plan word target: 4000. It's well above the target. Score 10/10 for structural integrity.

Let's review the pedagogical quality.
- Very clear explanations.
- Dialogue situation is present but wait...
Let's check the dialogue:
`> — Лікар: Ця ніч (night) у нашій лікарні...`
Is it a valid dialogue? Yes, section "Словотворення іменників III відміни" starts with a dialogue. Wait, the plan says:
`dialogue_situations: - setting: 'At a нічна зміна...' speakers: Медсестра, Лікар.`
The generated dialogue matches the plan exactly.

Tone: Tone is encouraging, appropriate.

Dimensions and Scores:
1. **Plan adherence**: 10/10. All plan points, sections, and vocabulary (required and recommended) are covered.
2. **Linguistic accuracy**: 8/10. Identified the use of English words (`standard`, `standardно`) and incomplete words (`уніка`) which are artifacts. Also the active participle `вібруючий` instead of the correct phonetic term `дрижачий`.
3. **Pedagogical quality**: 10/10. Good PPP flow, clear grammar rules with contextual examples, diagnostic algorithm.
4. **Vocabulary coverage**: 10/10. All required and most recommended words are beautifully woven into the text.
5. **Exercise quality**: 10/10. All 6 activity markers are present in the correct places, matching the plan hints.
6. **Engagement & tone**: 10/10. Natural teacher tone, encouraging without being overly gamified.
7. **Structural integrity**: 10/10. H2 headers match the plan. Word count is 5281 (above 4000 target).
8. **Cultural accuracy**: 10/10. Highlights the difference between Ukrainian phonetic doubling and Russian soft sign. Culturally authentic context (Kharkiv hospital, Shevchenko park).
9. **Dialogue & conversation quality**: 10/10. Natural hospital dialogue incorporating III declension nouns seamlessly.

Findings:
1. `Linguistic accuracy` [Critical] (Wait, are untranslated English words Critical or Major? They are factual errors in the target language text. Let's call it Critical as it ruins the Ukrainian sentence).
2. `Linguistic accuracy` [Critical] (Phonetic term error: `вібруючий` instead of `дрижачий`).

Let's format the findings carefully.
Finding 1:
```
[2. Linguistic accuracy] [Critical]
Location: Відмінювання у множині
Issue: English word "standard" used instead of Ukrainian "стандартне"
Fix: `додаємо standard закінчення` -> `додаємо стандартне закінчення`
```
Wait, there are 4 instances of `standard`. I'll create a finding for each or group them.
Group them in one finding, but in `<fixes>` add all of them.

Finding 2:
```
[2. Linguistic accuracy] [Critical]
Location: Відмінювання у множині
Issue: English word mixed with Ukrainian suffix "standardно" instead of "стандартно"
Fix: `утворюється standardно і м'яко` -> `утворюється стандартно і м'яко`
```

Finding 3:
```
[2. Linguistic accuracy] [Critical]
Location: Відмінювання у множині
Issue: English word mixed with Ukrainian suffix "standardно" instead of "стандартно"
Fix: `ці слова standardно:` -> `ці слова стандартно:`
```

Finding 4:
```
[2. Linguistic accuracy] [Critical]
Location: III відміна vs інші відміни
Issue: English word "standard" used instead of Ukrainian "стандартні"
Fix: `довгі standard закінчення` -> `довгі стандартні закінчення`
```

Finding 5:
```
[2. Linguistic accuracy] [Critical]
Location: III відміна vs інші відміни
Issue: Truncated word "уніка" instead of "унікальне"
Fix: `наше уніка закінчення` -> `наше унікальне закінчення`
```

Finding 6:
```
[2. Linguistic accuracy] [Critical]
Location: Подвоєння в орудному відмінку
Issue: Inaccurate phonetic terminology and calque. In Ukrainian phonetics, the [р] sound is classified as "дрижачий" (trill), not "вібруючий" (which is an active participle and a Russianism calqued from вибрирующий).
Fix: `дзвінкий вібруючий звук [р]` -> `дзвінкий дрижачий звук [р]`
```

Wait, are there any other errors?
Let's check the text: "називний — це печі" -> correct. "мишей" -> correct.
"радості та радости", "крові та крови" -> correct orthography.

Let's check the dialogue:
`> — **Лікар:** Ця **ніч** *(night)* у нашій лікарні точно буде дуже довгою і складною. Як минула ваша **подорож** *(journey)* до роботи через усе місто?`
`> — **Медсестра:** Насправді, досить спокійно. На вулицях зараз панує абсолютна **тиша** *(silence)*, хоча надворі вже досить холодно.`
`> — **Лікар:** Розумію вас. Перейдемо до справ: нам терміново потрібна морська **сіль** *(salt)* для спеціального фізіологічного розчину. Де вона лежить?`
`> — **Медсестра:** Не хвилюйтеся, я вже все підготувала заздалегідь. І я також увімкнула електричну **піч** *(oven)* для швидкої стерилізації всіх хірургічних інструментів.`
`> — **Лікар:** Дуже вам дякую за оперативність. Працювати цією темною **ніччю** *(by night)* буде значно легше і приємніше з вашою професійною допомогою.`

The dialogue is flawless.

Is there anything else?
Let's look at `Орудний відмінок утворюється standardно і м'яко звучить як **матерями**` -> `Орудний відмінок утворюється стандартно і м'яко звучить як **матерями**`
`Ми пишемо і вимовляємо ці слова standardно: **ночами**` -> `Ми пишемо і вимовляємо ці слова стандартно: **ночами**`
`Ми просто додаємо standard закінчення **-і**` -> `Ми просто додаємо стандартне закінчення **-і**`
`завжди використовуємо довгі standard закінчення **-ою**` -> `завжди використовуємо довгі стандартні закінчення **-ою**`
`мусимо застосувати наше уніка закінчення **-ю**` -> `мусимо застосувати наше унікальне закінчення **-ю**`
`твердий і дуже дзвінкий вібруючий звук [р]` -> `твердий і дуже дзвінкий дрижачий звук [р]`

The exact text for `вібруючий`:
"а також твердий і дуже дзвінкий вібруючий звук [р]."
Replace with:
"а також твердий і дуже дзвінкий дрижачий звук [р]."

Exact text for `standard`:
1. "Ми просто додаємо standard закінчення **-і** до основи нашого слова."
Replace with: "Ми просто додаємо стандартне закінчення **-і** до основи нашого слова."

2. "Ми пишемо і вимовляємо ці слова standardно: **ночами**"
Replace with: "Ми пишемо і вимовляємо ці слова стандартно: **ночами**"

3. "Орудний відмінок утворюється standardно і м'яко звучить як **матерями**"
Replace with: "Орудний відмінок утворюється стандартно і м'яко звучить як **матерями**"

4. "завжди використовуємо довгі standard закінчення **-ою** або **-ею**"
Replace with: "завжди використовуємо довгі стандартні закінчення **-ою** або **-ею**"

Exact text for `уніка`:
1. "ми мусимо застосувати наше уніка закінчення **-ю** та правило"
Replace with: "ми мусимо застосувати наше унікальне закінчення **-ю** та правило"

Let's double check if there are other occurrences. No, `grep_search` found exactly 4 matches for `standard`.
And I saw `уніка` when reading.

Let's quickly check `ість` in the generated text:
`Багато з них продуктивно утворюються за допомогою суфікса **-ість**.` -> correct.
`Але цей неймовірно популярний суфікс **-ість** має один` -> correct.

Let's check `матер` and `ноч`:
`| **Н.** | *хто? що?* | ноч**і** | матер**і** |`
`| **Р.** | *кого? чого?* | ноч**ей** | матер**ів** |`
`| **Д.** | *кому? чому?* | ноч**ам** | матер**ям** |`
This is why VESUM reported `матер` and `ноч` as missing: the bolding splits the words into `ноч` and `**і**`. This is standard Markdown formatting for tables showing stems and endings. Not a linguistic error.

Let's formulate the response.

## Linguistic Scan
Errors found:
1. English word "standard" left in the text multiple times (`standard закінчення`, `standardно`, `standard закінчення`).
2. Truncated word `уніка` instead of `унікальне`.
3. Russianism/calque and incorrect phonetic terminology: `вібруючий` sound [р] instead of the correct Ukrainian phonetic term `дрижачий`.

## Exercise Check
All exercise markers are present, logically placed, and match the plan's `activity_hints`.
1. `<!-- INJECT_ACTIVITY: match-up -->` - After singular declension
2. `<!-- INJECT_ACTIVITY: fill-in-instrumental -->` - After instrumental case
3. `<!-- INJECT_ACTIVITY: sort-doubling-rules -->` - After instrumental case
4. `<!-- INJECT_ACTIVITY: error-fix-instrumental -->` - After instrumental case
5. `<!-- INJECT_ACTIVITY: quiz-determine-vidmina -->` - After declension comparison
6. `<!-- INJECT_ACTIVITY: sentence-builder -->` - After word formation

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 10/10 | All sections from the outline are present with excellent detail. All semantic groups, paradigms (including the exception "мати"), and spelling rules are taught exactly as outlined. |
| 2. Linguistic accuracy | 8/10 | Several critical transcription/generation artifacts found: English words left in the text ("standard", "standardно") and truncated words ("уніка закінчення"). Also, an incorrect phonetic term "вібруючий звук [р]" is used instead of the standard Ukrainian "дрижачий звук [р]". |
| 3. Pedagogical quality | 10/10 | Superb PPP flow. The module starts with clear definitions, connects to previously learned topics (vowel alternation [і] → [о/е]), and presents the diagnostic algorithm logically. |
| 4. Vocabulary coverage | 10/10 | All required vocabulary is used in context (любов, осінь, радість, подорож, ніч, піч, сіль, кров, мати, etc.). |
| 5. Exercise quality | 10/10 | All 6 planned activities are injected in the correct places, immediately after the relevant teaching sections. |
| 6. Engagement & tone | 10/10 | Excellent teacher persona. The text feels natural, encouraging, and informative without filler ("Це фундаментальна і питома фонетична особливість нашої мови"). |
| 7. Structural integrity | 10/10 | Word count is 5281 (exceeds the 4000 target). All markdown headers match the plan flawlessly. |
| 8. Cultural accuracy | 10/10 | Brilliant decolonization point on the difference between Ukrainian phonetic consonant doubling and the Russian orthographic soft sign. |
| 9. Dialogue & conversation quality | 10/10 | The dialogue is a realistic hospital setting ("нічна зміна") that perfectly incorporates target vocabulary (ніч, подорож, тиша, сіль, піч). |

## Findings
[2. Linguistic accuracy] [Critical]
Location: Відмінювання у множині
Issue: English word "standard" used instead of the Ukrainian adjective "стандартне".
Fix: Change `standard закінчення` to `стандартне закінчення`.

[2. Linguistic accuracy] [Critical]
Location: Відмінювання у множині
Issue: English word mixed with a Ukrainian suffix ("standardно").
Fix: Change `standardно` to `стандартно`.

[2. Linguistic accuracy] [Critical]
Location: III відміна vs інші відміни
Issue: English word "standard" used instead of "стандартні".
Fix: Change `довгі standard закінчення` to `довгі стандартні закінчення`.

[2. Linguistic accuracy] [Critical]
Location: III відміна vs інші відміни
Issue: Truncated word "уніка" used instead of the correct adjective "унікальне".
Fix: Change `уніка закінчення` to `унікальне закінчення`.

[2. Linguistic accuracy] [Critical]
Location: Подвоєння в орудному відмінку
Issue: Inaccurate phonetic terminology and calque. In Ukrainian phonetics, the [р] sound is classified as "дрижачий" (trill), not "вібруючий" (which is an active participle and a Russianism calqued from "вибрирующий").
Fix: Change `вібруючий звук` to `дрижачий звук`.

## Verdict: REVISE
The module content is structurally, pedagogically, and culturally phenomenal. However, the presence of English words ("standard"), truncation artifacts ("уніка"), and an incorrect phonetic term ("вібруючий") requires a mandatory revision to ensure linguistic accuracy before publishing.

<fixes>
- find: "додаємо standard закінчення"
  replace: "додаємо стандартне закінчення"
- find: "ці слова standardно:"
  replace: "ці слова стандартно:"
- find: "утворюється standardно і м'яко"
  replace: "утворюється стандартно і м'яко"
- find: "довгі standard закінчення"
  replace: "довгі стандартні закінчення"
- find: "наше уніка закінчення"
  replace: "наше унікальне закінчення"
- find: "дзвінкий вібруючий звук"
  replace: "дзвінкий дрижачий звук"
</fixes>

Let's double check the exact matches.
1. "додаємо standard закінчення" -> `Ми просто додаємо standard закінчення **-і** до основи нашого слова.` matches `додаємо standard закінчення`.
2. "ці слова standardно:" -> `Ми пишемо і вимовляємо ці слова standardно: **ночами**` matches `ці слова standardно:`.
3. "утворюється standardно і м'яко" -> `Орудний відмінок утворюється standardно і м'яко звучить як **матерями**` matches `утворюється standardно і м'яко`.
4. "довгі standard закінчення" -> `ми завжди використовуємо довгі standard закінчення **-ою** або **-ею**` matches `довгі standard закінчення`.
5. "наше уніка закінчення" -> `ми мусимо застосувати наше уніка закінчення **-ю** та правило` matches `наше уніка закінчення`.
6. "дзвінкий вібруючий звук" -> `а також твердий і дуже дзвінкий вібруючий звук [р].` matches `дзвінкий вібруючий звук`.

Wait, finding 1: "додаємо standard закінчення **-і**" -> maybe better to use more context just in case.
"Ми просто додаємо standard закінчення" -> "Ми просто додаємо стандартне закінчення"
"вимовляємо ці слова standardно:" -> "вимовляємо ці слова стандартно:"
"відмінок утворюється standardно і м'яко" -> "відмінок утворюється стандартно і м'яко"
"використовуємо довгі standard закінчення" -> "використовуємо довгі стандартні закінчення"
"застосувати наше уніка закінчення" -> "застосувати наше унікальне закінчення"
"дуже дзвінкий вібруючий звук" -> "дуже дзвінкий дрижачий звук"

This looks extremely solid. All fixes correspond EXACTLY to what's in the generated text. I will output exactly as instructed.## Linguistic Scan
Errors found:
1. English word "standard" left in the text multiple times (`standard закінчення`, `standardно`).
2. Truncated word `уніка` instead of `унікальне`.
3. Russianism/calque and incorrect phonetic terminology: `вібруючий` sound [р] instead of the correct Ukrainian phonetic term `дрижачий`.

## Exercise Check
All exercise markers are present, logically placed, and match the plan's `activity_hints`.
1. `<!-- INJECT_ACTIVITY: match-up -->` - After singular declension
2. `<!-- INJECT_ACTIVITY: fill-in-instrumental -->` - After instrumental case
3. `<!-- INJECT_ACTIVITY: sort-doubling-rules -->` - After instrumental case
4. `<!-- INJECT_ACTIVITY: error-fix-instrumental -->` - After instrumental case
5. `<!-- INJECT_ACTIVITY: quiz-determine-vidmina -->` - After declension comparison
6. `<!-- INJECT_ACTIVITY: sentence-builder -->` - After word formation

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 10/10 | All sections from the outline are present with excellent detail. All semantic groups, paradigms (including the exception "мати"), and spelling rules are taught exactly as outlined. |
| 2. Linguistic accuracy | 8/10 | Several critical transcription/generation artifacts found: English words left in the text ("Ми просто додаємо standard закінчення", "Орудний відмінок утворюється standardно") and truncated words ("мусимо застосувати наше уніка закінчення"). Also, an incorrect phonetic term is used: "дзвінкий вібруючий звук [р]" instead of the standard Ukrainian "дрижачий звук [р]". |
| 3. Pedagogical quality | 10/10 | Superb PPP flow. The module starts with clear definitions, connects to previously learned topics (vowel alternation [і] → [о/е]), and presents the diagnostic algorithm logically. |
| 4. Vocabulary coverage | 10/10 | All required vocabulary is used in context (любов, осінь, радість, подорож, ніч, піч, сіль, кров, мати, etc.). |
| 5. Exercise quality | 10/10 | All 6 planned activities are injected in the correct places, immediately after the relevant teaching sections. |
| 6. Engagement & tone | 10/10 | Excellent teacher persona. The text feels natural, encouraging, and informative without filler ("Це фундаментальна і питома фонетична особливість нашої мови"). |
| 7. Structural integrity | 10/10 | Word count is 5281 (exceeds the 4000 target). All markdown headers match the plan flawlessly. |
| 8. Cultural accuracy | 10/10 | Brilliant decolonization point on the difference between Ukrainian phonetic consonant doubling and the Russian orthographic soft sign. |
| 9. Dialogue & conversation quality | 10/10 | The dialogue is a realistic hospital setting ("нічна зміна") that perfectly incorporates target vocabulary (ніч, подорож, тиша, сіль, піч). |

## Findings
[2. Linguistic accuracy] [Critical]
Location: Відмінювання у множині
Issue: English word "standard" used instead of the Ukrainian adjective "стандартне".
Fix: Change `додаємо standard закінчення` to `додаємо стандартне закінчення`.

[2. Linguistic accuracy] [Critical]
Location: Відмінювання у множині
Issue: English word mixed with a Ukrainian suffix ("standardно").
Fix: Change `ці слова standardно:` to `ці слова стандартно:` and `утворюється standardно і м'яко` to `утворюється стандартно і м'яко`.

[2. Linguistic accuracy] [Critical]
Location: III відміна vs інші відміни
Issue: English word "standard" used instead of "стандартні".
Fix: Change `довгі standard закінчення` to `довгі стандартні закінчення`.

[2. Linguistic accuracy] [Critical]
Location: III відміна vs інші відміни
Issue: Truncated word "уніка" used instead of the correct adjective "унікальне".
Fix: Change `наше уніка закінчення` to `наше унікальне закінчення`.

[2. Linguistic accuracy] [Critical]
Location: Подвоєння в орудному відмінку
Issue: Inaccurate phonetic terminology and calque. In Ukrainian phonetics, the [р] sound is classified as "дрижачий" (trill), not "вібруючий" (which is an active participle and a Russianism calqued from "вибрирующий").
Fix: Change `дзвінкий вібруючий звук` to `дзвінкий дрижачий звук`.

## Verdict: REVISE
The module content is structurally, pedagogically, and culturally phenomenal. However, the presence of English words ("standard"), truncation artifacts ("уніка"), and an incorrect phonetic term ("вібруючий") requires a mandatory revision to ensure linguistic accuracy before publishing.

<fixes>
- find: "додаємо standard закінчення"
  replace: "додаємо стандартне закінчення"
- find: "ці слова standardно:"
  replace: "ці слова стандартно:"
- find: "утворюється standardно і м'яко"
  replace: "утворюється стандартно і м'яко"
- find: "довгі standard закінчення"
  replace: "довгі стандартні закінчення"
- find: "наше уніка закінчення"
  replace: "наше унікальне закінчення"
- find: "дзвінкий вібруючий звук"
  replace: "дзвінкий дрижачий звук"
</fixes>
