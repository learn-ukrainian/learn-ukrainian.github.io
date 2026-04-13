## Linguistic Scan
- `Використовуйте складену форму тільки тоді, коли проста форма звучить дивно або важко вимовляється.` This teaches a false rule: school grammar treats `більш/менш + adjective` as a standard parallel form, not only a pronunciation fallback.
- `Пам'ятайте, що для опису краси обличчя ми можемо сказати «гарніший».` This wrongly narrows `гарніший`; dictionary/textbook evidence allows broader aesthetic comparison (`гарніший рюкзак`, `гарніший краєвид`, `гарніше обличчя`).

## Exercise Check
All 5 planned `INJECT_ACTIVITY` markers are present and placed after the relevant teaching blocks:
`fill-in-comparative`, `true-false-constructions`, `match-up-match-adjective-to-its-superlative-form`, `quiz-irregular-forms-choose-the-correct-suppletive-form`, `error-correction-double-comparisons-find-and-fix-wrong-comparative-and-superlative-forms-e-g`.

No placement problems found. No inline DSL exercise logic was available to audit.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | All four planned H2 sections appear in order; the module covers `ніж/за/від`, suppletive forms, adverb comparatives, the phone-store dialogue, and the modifiers `набагато/трохи/значно`. |
| 2. Linguistic accuracy | 6/10 | Two wrong rules are taught: `Використовуйте складену форму тільки тоді...` falsely restricts the compound comparative, and `для опису краси обличчя... «гарніший»` falsely narrows the adjective’s usage. |
| 3. Pedagogical quality | 7/10 | PPP skeleton is visible via dialogue → explanation → activity markers, but long English theory blocks such as `In the Ukrainian language, we have a simple form...` and `The simple form of the superlative degree...` interrupt the Ukrainian teaching flow. |
| 4. Vocabulary coverage | 9/10 | All required plan words are used in prose, and recommended `набагато`, `трохи`, `значно` appear naturally in context. |
| 5. Exercise quality | 9/10 | Marker coverage matches all 5 `activity_hints`, and each marker comes after the relevant teaching section. |
| 6. Engagement & tone | 9/10 | The phone-store scenario and city-comparison reading keep the module concrete and learner-facing rather than abstract. |
| 7. Structural integrity | 10/10 | All expected sections are present, markers are clean, and the pipeline count is 2178 words, above the 2000-word target. |
| 8. Cultural accuracy | 6/10 | `Така граматична конструкція є типовою для російської мови... Чиста українська мова...` and `A critical difference between Ukrainian and Russian... Pure Ukrainian...` define Ukrainian through Russian and use purity framing. |
| 9. Dialogue & conversation quality | 9/10 | Dialogues use named speakers and plausible situations; the phone-store exchange is especially usable for learners. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `Використовуйте складену форму тільки тоді, коли проста форма звучить дивно або важко вимовляється.`  
Issue: This teaches the compound comparative as a fallback only. Textbook grammar presents simple and compound forms as parallel normative options.  
Fix: Replace the sentence with a rule that says the compound form is also standard and is chosen by style/context.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `Пам'ятайте, що для опису краси обличчя ми можемо сказати «гарніший». Але слово «кращий» є стандартним для будь-якого загального порівняння.`  
Issue: This falsely limits `гарніший` to facial beauty. Reference evidence attests broader aesthetic use.  
Fix: Rephrase to contrast `гарніший` for aesthetic beauty with `кращий` for general quality.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `> *In the Ukrainian language, we have a simple form for comparison...*` and `> *The simple form of the superlative degree is formed very easily...*`  
Issue: These long English theory blocks interrupt the module’s Ukrainian-first teaching flow and spend word budget on repetition instead of practice.  
Fix: Replace them with short reinforcement notes tied to the Ukrainian examples.

[CULTURAL ACCURACY] [SEVERITY: major]  
Location: `Така граматична конструкція є типовою для російської мови... Чиста українська мова...` and `A critical difference between Ukrainian and Russian is how the superlative is formed... Pure Ukrainian exclusively uses...`  
Issue: The explanation is Russian-centered and uses `чиста/pure Ukrainian` framing instead of teaching the standard Ukrainian norm directly.  
Fix: Rephrase both passages in neutral normative terms without purity language.

## Verdict: REVISE
REVISE because the module contains critical linguistic findings that teach wrong rules, and dimensions 2, 3, and 8 fall below 9.

<fixes>
- find: "Використовуйте складену форму тільки тоді, коли проста форма звучить дивно або важко вимовляється."
  replace: "Складена форма теж нормативна; вживайте її, коли вона краще пасує до стилю або контексту, а не лише тоді, коли проста форма незручна."

- find: "Пам'ятайте, що для опису краси обличчя ми можемо сказати «гарніший». Але слово «кращий» є стандартним для будь-якого загального порівняння."
  replace: "Пам'ятайте, що «гарніший» уживаємо, коли порівнюємо зовнішню красу або естетичне враження: гарніший краєвид, гарніший будинок, гарніше обличчя. Але слово «кращий» уживаємо для загальної оцінки якості."

- find: |
    > *In the Ukrainian language, we have a simple form for comparison. This is the most natural way. To form this, we add special suffixes to the adjective stem. We use the suffixes "-ший" or "-іший". For example, the word "солодкий" changes and sounds like "солодший" (sweeter). Another example is the word "теплий". We add a suffix and have the word "тепліший". The word "дешевий" turns into "дешевший". This simple form often sounds in conversations and literature. Ukrainians really love to use these short words. They make our language fast and melodic.*
  replace: |
    > *Повторіть моделі вголос: солодкий → солодший, теплий → тепліший, дешевий → дешевший. Так ви швидше відчуєте, як працює проста форма вищого ступеня.*

- find: |
    > *The simple form of the superlative degree is formed very easily. We only need a special prefix. We take an adjective in the comparative degree and add the prefix "най-". For example, to the word **солодший** (sweeter) we add the prefix and get "найсолодший". The word "тепліший" turns into "найтепліший". And a **цікавіший** (more interesting) text quickly becomes "найцікавішим". This simple form is the most popular in the language. You will hear it every day. People love to use this short form because it sounds natural.*
  replace: |
    > *Повторіть моделі вголос: солодший → найсолодший, тепліший → найтепліший, цікавіший → найцікавіший. Так легше побачити, що найвищий ступінь утворюємо від форми вищого ступеня.*

- find: |
    Тут є одна дуже важлива деталь. Деякі люди роблять помилку, коли порівнюють предмети. Вони використовують родовий відмінок без прийменників. Наприклад, можна почути таку фразу: «сталь міцніше міді». Це неправильно. Така граматична конструкція є типовою для російської мови. Вона не є природною для української. Українська мова має власні правила. Чиста українська мова вимагає використання слів «за», «від» або «ніж». Правильно говорити: «сталь міцніша за мідь». Завжди звертайте увагу на ці слова. Уникайте прямого копіювання граматики з інших мов.
  replace: |
    Тут є одна дуже важлива деталь. Деякі люди роблять помилку, коли порівнюють предмети. Вони використовують родовий відмінок без прийменника: «сталь міцніше міді». У стандартній українській мові краще вживати нормативні конструкції зі словами «за», «від» або «ніж»: «сталь міцніша за мідь», «сталь міцніша від міді», «сталь міцніша, ніж мідь». Завжди звертайте увагу на ці слова й на правильний відмінок після них.

- find: |
    > *There is one very important detail here. Some people make a mistake when comparing objects. They use the Genitive case without prepositions. For example, you can hear the phrase: "сталь міцніше міді". This is incorrect. Such a grammatical construction is typical for the Russian language. It is not natural for Ukrainian. The Ukrainian language has its own rules. Pure Ukrainian language requires the use of the words "за", "від", or "ніж". It is correct to say: "сталь міцніша за мідь". Always pay attention to these words. Avoid direct copying of grammar from other languages.*
  replace: |
    > *There is one important detail here. In standard Ukrainian, comparisons are normally built with **за**, **від**, or **ніж**: "сталь міцніша за мідь", "сталь міцніша від міді", "сталь міцніша, ніж мідь". Avoid the bare Genitive pattern in this topic.*

- find: |
    :::info
    **Grammar box**
    A critical difference between Ukrainian and Russian is how the superlative is formed. You might hear some people use the word **самий** before an adjective to create a superlative (e.g., *самий великий*, *самий кращий*). This is a direct Russianism and a major grammatical error in standard Ukrainian. Pure Ukrainian exclusively uses the **най-** prefix for the simple form, or **найбільш** for the compound form (**найбільший**, **найкращий**, **найбільш цікавий**). Never use "самий" to mean "the most".
    :::
  replace: |
    :::info
    **Grammar box**
    In standard Ukrainian, the usual superlative is formed with the prefix **най-** (**найбільший**, **найкращий**) or, in compound forms, with **найбільш/найменш** + adjective (**найбільш цікавий**). Forms like *самий великий* or *самий кращий* are nonstandard in this meaning, so prefer the regular superlative forms instead.
    :::
</fixes>