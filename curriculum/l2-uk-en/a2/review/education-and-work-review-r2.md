## Linguistic Scan
No linguistic errors found.

## Exercise Check
Markers found: `fill-in-complete-sentences-about-education-and-work-using`, `true-false-culture-complex`, `match-up-match-education-career-situations-to-appropriate-responses-using-complex-sentences`, `quiz-choose-the-correct-complex-sentence-type-for-work-education-scenarios`.

All 4 expected activity types from the plan are present. Placement is sensible: the fill-in comes after education, the true/false after work, the match-up after future/conditional work, and the quiz closes the module. No exercise-logic issues are detectable from the markers alone.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All three planned sections are present and the required/recommended vocabulary is covered, but the listed references were not integrated: search returned 0 hits for `Заболотний`, `ULP`, and `Ukrainian Lessons`. |
| 2. Linguistic accuracy | 10/10 | No confirmed Russianisms, Surzhyk, calques, paronym errors, or bad case forms. VESUM checks passed for borderline items such as `виш`, `випускаються`, `архітекторкою`, `директоркою`, and `допуст`. |
| 3. Pedagogical quality | 8/10 | The target structures get many examples, but `### Читаємо українською (Reading Practice)` is only a recap: `Ми використовуємо «тому що»...`, `Ми кажемо «щоб»...` instead of fresh contextualized reading input. |
| 4. Vocabulary coverage | 10/10 | All required words appear in prose, and the recommended items also appear: `факультет`, `зарплата`, `співбесіда`, `керівник`, `магістратура`. |
| 5. Exercise quality | 9/10 | The four marker types match the four `activity_hints` and are distributed through the module rather than clustered at the end. |
| 6. Engagement & tone | 9/10 | The tone stays teacherly and avoids gamified fluff; lines like `Тепер подивімося...` fit the brief well. |
| 7. Structural integrity | 10/10 | All planned H2 headings are present and ordered, inject markers are intact, and the pipeline word count is 2765, which is above the 2000 target. |
| 8. Cultural accuracy | 8/10 | The module stays Ukrainian-centered, but the English gloss `A modern school is often called a gymnasium or a lyceum.` overgeneralizes the school taxonomy. |
| 9. Dialogue & conversation quality | 8/10 | Named speakers and relevant situations are present, but `Діалог: Нові знайомі` is mostly an interview: `А яку спеціальність ти обрав?` / `Чому саме цю професію?` |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: `Коли ми говоримо про вибір професії, ми часто пояснюємо причину наших рішень.`  
Issue: The plan lists two references, but the module never cites either of them; search confirmed 0 occurrences of `Заболотний`, `ULP`, and `Ukrainian Lessons`.  
Fix: Add one short natural citation sentence that names `§28 у Заболотного` and `Ukrainian Lessons`.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `### Читаємо українською (Reading Practice)` — `Складні речення допомагають нам дуже детально пояснювати свої думки...`  
Issue: The section is labeled as reading practice but only restates grammar labels; learners do not get a fresh connected text to read.  
Fix: Replace the recap with a short mini-text that uses `тому що`, `щоб`, `який`, `якщо`, and `хоча` in context.

[CULTURAL ACCURACY] [SEVERITY: major]  
Location: English translation block in the first section — `A modern school is often called a gymnasium or a lyceum.`  
Issue: This adds a broader factual claim than the Ukrainian text and misrepresents the taxonomy of Ukrainian secondary schools.  
Fix: Replace it with `Among secondary schools in Ukraine, there are regular schools, gymnasiums, and lyceums.`

[DIALOGUE & CONVERSATION QUALITY] [SEVERITY: major]  
Location: `### Діалог: Нові знайомі`  
Issue: The exchange is mostly one speaker questioning the other, so it sounds transactional rather than like two new acquaintances naturally sharing information.  
Fix: Rewrite the dialogue so both speakers volunteer information, react to each other, and still model the target structures.

## Verdict: REVISE
The Ukrainian itself is clean, but there are four nontrivial issues: missing plan references, a weak pseudo-reading section, one factual overreach in the English gloss, and a stiff interview-style dialogue. Because these findings lower multiple dimensions below 9, this cannot pass as-is.

<fixes>
- find: "Коли ми говоримо про вибір професії, ми часто пояснюємо причину наших рішень."
  replace: "Коли ми говоримо про вибір професії, ми часто пояснюємо причину наших рішень. Такі моделі складних речень докладно пояснює §28 у Заболотного, а розмовну лексику про роботу добре доповнює матеріал Ukrainian Lessons."

- find: "A modern school is often called a gymnasium or a lyceum."
  replace: "Among secondary schools in Ukraine, there are regular schools, gymnasiums, and lyceums."

- find: |
    ### Читаємо українською (Reading Practice)

    Складні речення допомагають поєднувати прості ідеї й точніше висловлюватися про навчання та роботу.

    Складні речення допомагають нам дуже детально пояснювати свої думки. Ми використовуємо «тому що» для пояснення причини. Ми кажемо «щоб», коли говоримо про нашу життєву мету. Слово «який» чудово допомагає описувати компанію або нову професію. За допомогою «якщо» ми будуємо амбітні плани на майбутнє. А слово «хоча» яскраво показує контраст між фактами. Тепер ви можете точніше розповідати про навчання й кар'єру українською мовою.
  replace: |
    ### Читаємо українською (Reading Practice)

    Марія навчається в університеті, який готує майбутніх перекладачів. Вона обрала цю спеціальність, тому що любить мови і хоче працювати з міжнародними клієнтами. Щоб отримати добру роботу, Марія щодня читає професійні тексти українською. Якщо вона успішно складе всі іспити, то подасть документи на стажування. Хоча навчання забирає багато часу, Марія не шкодує про свій вибір.

- find: |
    > — **Анна:** Привіт, Богдане! Розкажи, де ти навчався? *(Hi, Bohdan! Tell me, where did you study?)*
    > — **Богдан:** Привіт! Я закінчив Київський національний університет. *(Hi! I graduated from Kyiv National University.)*
    > — **Анна:** О, це відомий виш! А яку спеціальність ти обрав? *(Oh, that's a famous university! And what specialty did you choose?)*
    > — **Богдан:** Я навчався на економіста. А ти? *(I studied to be an economist. And you?)*
    > — **Анна:** Я вивчала право. Я вступила до університету, тому що завжди хотіла стати юристом. *(I studied law. I entered the university because I always wanted to become a lawyer.)*
    > — **Богдан:** Чому саме цю професію? *(Why exactly this profession?)*
    > — **Анна:** Я обрала її, щоб допомагати людям. А ти чому став економістом? *(I chose it in order to help people. And why did you become an economist?)*
    > — **Богдан:** Предмет, який мені найбільше подобався у школі, — це математика. Тому я пішов на економічний факультет. *(The subject I liked the most in school was math. That's why I went to the economics faculty.)*
    > — **Анна:** Це логічно. Тобі подобається твоя теперішня робота? *(That's logical. Do you like your current job?)*
    > — **Богдан:** Так, компанія, де я працюю, дуже сучасна. *(Yes, the company where I work is very modern.)*
  replace: |
    > — **Анна:** Привіт, Богдане! Рада знайомству. Я щойно закінчила університет і шукаю першу роботу. *(Hi, Bohdan! Nice to meet you. I have just finished university and am looking for my first job.)*
    > — **Богдан:** Привіт! А я вже рік працюю в компанії, де займаюся фінансами. *(Hi! I have already been working for a year at a company where I deal with finance.)*
    > — **Анна:** Цікаво. А що ти вивчав? *(Interesting. And what did you study?)* 
    > — **Богдан:** Я навчався на економіста, тому що в школі найбільше любив математику. *(I studied to become an economist because in school I liked math the most.)*
    > — **Анна:** А я вивчала право, тому що хотіла допомагати людям. Якщо все піде добре, наступного місяця піду на співбесіду в юридичну фірму. *(And I studied law because I wanted to help people. If everything goes well, next month I will go to an interview at a law firm.)*
    > — **Богдан:** Це звучить серйозно. У якому університеті ти навчалася? *(That sounds serious. Which university did you study at?)* 
    > — **Анна:** У Київському національному університеті, який має сильний юридичний факультет. Я багато вчилася, щоб добре скласти іспити. *(At Kyiv National University, which has a strong law faculty. I studied a lot to do well on my exams.)*
    > — **Богдан:** Якщо хочеш, я можу розповісти, як проходила моя перша співбесіда. *(If you want, I can tell you how my first interview went.)*
    > — **Анна:** Було б чудово, дякую! *(That would be great, thank you!)*
</fixes>