## Linguistic Scan
No linguistic errors found.

## Exercise Check
Three activity markers are present: `match-hobbies-verbs`, `fill-in-prepositions-activities`, and `fill-in-invitations-frequency`. That matches the plan’s three `activity_hints`, and each marker appears after the relevant teaching material. No exercise-logic errors are visible in the prose-only module.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | All planned H2 sections are present, and the hobby/frequency/invitation content is broadly covered. But the objective “Combine all A1.4 skills: time + day + weather + activities” is not realized: searches for `погода`, `сонячно`, `дощ`, `холодно`, `тепло`, `вітер`, and `сніг` returned 0 occurrences in the module. Section pacing is also far off the 300-word plan budget: roughly 484 / 564 / 468 / 364 words by section. |
| 2. Linguistic accuracy | 9/10 | The Ukrainian forms themselves are solid: `Вітю`, `ходімо`, `двічі на тиждень`, `грати на гітарі`, `ходити на концерт`, `ніколи не працюю`. No Russian letters or obvious Russianisms/surzhyk/calques found. |
| 3. Pedagogical quality | 6/10 | There are enough examples, but too much English meta-explanation crowds out the target language. The caution box says `You have to say "I never *do not* work"`, which is a misleading way to explain Ukrainian double negation. |
| 4. Vocabulary coverage | 10/10 | All required vocabulary appears naturally in prose: `вихідні`, `спорт`, `футбол`, `кіно`, `часто`, `іноді`, `рідко`, `ходімо`. Recommended words are also integrated: `завжди`, `зазвичай`, `ніколи`, `театр`, `концерт`, `музей`, `давай`, `раз`. |
| 5. Exercise quality | 9/10 | The marker count matches the plan exactly, and placement is sensible: hobbies markers after the hobbies section, invitation/frequency marker after frequency teaching. No visible mismatch between marker purpose and taught material. |
| 6. Engagement & tone | 6/10 | The lesson repeatedly pads itself with filler/hype instead of teaching: `This is the perfect moment`, `powerful invitation word`, `incredibly useful`, `most natural and authentic`, `much more natural and authentic`. This inflates word count without adding instructional value. |
| 7. Structural integrity | 9/10 | Clean markdown, all required H2s are present and ordered correctly, markers are intact, and the pipeline word count is 1738, safely above target. |
| 8. Cultural accuracy | 9/10 | The `Будинок культури` note is plausible and culturally grounded. The module presents Ukrainian on its own terms and avoids “like Russian” framing. |
| 9. Dialogue & conversation quality | 7/10 | Dialogue 1 is natural and useful. Dialogue 2 is mostly an interview (`Ти любиш спорт?`, `Як часто?`, `А ще?`) and does not realize the plan’s bulletin-board motivation ending in a shared invitation (`Часто ходиш? Іноді. Ходімо разом!`). |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: plan objective `Combine all A1.4 skills: time + day + weather + activities`; module text contains time/day/activity examples but no weather-linked example.  
Issue: One explicit plan objective is missing.  
Fix: Add at least one short weather + activity example, e.g. `Сьогодні тепло. Ходімо в парк у суботу!` / `Сьогодні холодно. Я читаю вдома.`

[ENGAGEMENT & TONE] [SEVERITY: major]  
Location: opening and explanation prose such as `This is the perfect moment for them to talk about what they do for fun and make plans.`, `powerful invitation word`, `incredibly useful`, `most natural and authentic`.  
Issue: The module is heavily padded with English filler, which pushes all four sections well past the plan’s 300-word budget and weakens pacing.  
Fix: Replace hype and scene-setting with shorter teacherly explanations that keep the Ukrainian examples but cut redundant English prose.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `You have to say "I never *do not* work" («Я ніколи не працюю»).`  
Issue: This is a misleading explanation of double negation and can confuse learners about what the Ukrainian sentence means.  
Fix: Replace it with a precise rule: `In Ukrainian, ніколи is used together with не: «Я ніколи не працюю».`

[DIALOGUE & CONVERSATION QUALITY] [SEVERITY: major]  
Location: second dialogue: `Оленка: ... Як часто? ... А ще?` / `Вітя: ... Іноді слухаю музику і малюю.`  
Issue: The exchange stays one-sided and does not land on the shared invitation promised by the plan’s bulletin-board situation.  
Fix: Add a closing invitation line, e.g. `Ходімо разом на концерт у суботу! — Давай!`

## Verdict: REVISE
The module is linguistically safe, but it misses a stated plan objective, overuses filler to the point that every section blows past its target budget, and contains one genuinely misleading grammar explanation. That is a `REVISE`, not a `PASS`.

<fixes>
- find: |
    Community centers and public bulletin boards are common places to find out about local events, clubs, and activities in Ukraine. Imagine **Вітя** (Vitya) and **Оленка** (Olenka) standing in front of a colorful bulletin board at their local cultural center. They are reading posters about upcoming concerts, sports teams, and art classes. This is the perfect moment for them to talk about what they do for fun and make plans. In Ukrainian, when we want to ask someone about their hobbies or weekend plans, we use specific conversational patterns. Let's listen to how Вітя and Оленка discuss their free time.
  replace: |
    At a community-center bulletin board, **Вітя** (Vitya) and **Оленка** (Olenka) talk about their hobbies and make a weekend plan. This gives us a simple model for asking about free time and inviting someone to an activity.

- find: |
    Notice how Вітя asks «Що ти робиш у вихідні?» (What do you do on the weekend?). The word **вихідні** (weekend) is always plural in Ukrainian. Olenka replies with «Зазвичай я гуляю і читаю» (Usually I walk and read), using the adverb **зазвичай** (usually) to describe her habit. When Вітя wants to invite her out, he uses the powerful invitation word **ходімо** (let's go!). He says «Ходімо в кіно в суботу!» (Let's go to the cinema on Saturday!). This pattern is very natural: you state the invitation, the place, and then the day. Finally, they confirm the time using the question «О котрій?» (At what time?) and the answer «О п'ятій» (At five).
  replace: |
    Notice the core pattern here: «Що ти робиш у вихідні?», «Ходімо в кіно в суботу!», and «О котрій? — О п'ятій». To connect this module to earlier A1.4 material, you can also combine activities with weather: **Сьогодні тепло. Ходімо в парк у суботу!** *(It is warm today. Let's go to the park on Saturday!)* **Сьогодні холодно. Я читаю вдома.** *(It is cold today. I read at home.)*

- insert_after: |
    > **Вітя:** **Іноді** слухаю музику і малюю. *(Sometimes I listen to music and draw.)*
  replace: |
    > **Оленка:** Клас! **Ходімо разом** на **концерт** у суботу! *(Great! Let's go to a concert together on Saturday!)*
    > **Вітя:** **Давай!** *(Let's!)*

- find: |
    To start a conversation about hobbies, you can ask a very direct and polite question: «Що ти любиш робити у вільний час?» (What do you like to do in your free time?). We already know the verb «любити» (to love, to like). When we want to talk about our hobbies, we simply use «Я люблю» (I like) followed by the dictionary form (infinitive) of an action verb. For example, if your hobby is reading, you say «Я люблю читати» (I like to read). If you enjoy relaxing, you can say «Я люблю відпочивати» (I like to rest). This structure expands on what we learned previously and is the easiest way to express your interests.
  replace: |
    To talk about hobbies, ask: «Що ти любиш робити у вільний час?» (What do you like to do in your free time?). The basic pattern is **Я люблю + infinitive**: «Я люблю читати» (I like to read), «Я люблю відпочивати» (I like to rest).

- find: |
    When we talk about playing sports or games, Ukrainian uses a very specific pattern. We take the verb «грати» (to play), add the preposition «у» or «в» (in/at), and then name the sport. Unlike English, which just says "play football", Ukrainian requires this preposition. It literally translates to "play in football".
  replace: |
    To talk about sports, use **грати у / в + sport**: «Я граю у футбол», «Він грає у баскетбол», «Ми граємо у теніс».

- find: |
    However, if your hobby is playing a musical instrument, the pattern changes completely! Instead of the preposition «у» or «в», Ukrainian uses the preposition «на» (on) for instruments. You are literally saying that you "play on" the guitar or piano. This is a strict rule in Ukrainian. We play «у» sports, but we play «на» instruments. Think of your hands resting on the instrument to make music.
  replace: |
    For musical instruments, use **грати на + instrument**: «Я граю на гітарі», «Вона грає на піаніно», «Ти граєш на скрипці?»

- find: |
    Once you know someone's hobbies, the next logical question is to ask about their routine. You can ask «Як часто?» (How often?). To answer this, we need a special group of words called frequency adverbs. These words tell us how regularly an action happens.
  replace: |
    To ask about routine, say «Як часто?» (How often?). The answer usually uses a frequency adverb.

- find: |
    English speakers often make a mistake with the word **ніколи** (never). In English, we say "I never work", using only one negative word. In Ukrainian, you must use a double negative! You have to say "I never *do not* work" («Я ніколи не працюю»). If you forget the «не», the sentence will sound completely broken to a native speaker.
  replace: |
    English speakers often miss the extra **не** here. In Ukrainian, **ніколи** is used together with **не**: «Я ніколи не працюю». Without **не**, the sentence is ungrammatical.

- find: |
    In this module, we expanded our ability to communicate about free time and entertainment. You learned how to state your hobbies clearly using the pattern «Я люблю» followed by an infinitive action verb. We also discovered that Ukrainian uses very specific prepositions for playing. Remember the rule: you use «у» or «в» for sports («Я граю у футбол», «Я граю в баскетбол»), but you must use «на» for musical instruments («Я граю на гітарі», «Я граю на піаніно»). Knowing this difference makes your Ukrainian sound much more natural and authentic.
  replace: |
    In this module, you learned how to talk about free time with **Я люблю + infinitive**, **грати у / в + sport**, and **грати на + instrument**. These patterns let you describe hobbies clearly and naturally.
</fixes>