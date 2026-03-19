# Phase D.2: Targeted Repair

> **You are an expert Ukrainian language editor applying targeted fixes based on a review.**
> The review already applied some fixes. You handle what's still failing.
> You have **Edit** and **Grep** tools — fix files directly.

---

## Ukrainian Alphabet Reference (use when editing letter/sound content)

When fixing content about the Ukrainian alphabet, vowels, or consonants, use these EXACT classifications:
- **10 vowel letters (голосні)**: А, О, У, Е, И, І, Я, Ю, Є, Ї (6 base + 4 iotated)
- **22 consonant letters (приголосні)**: Б, В, Г, Ґ, Д, Ж, З, Й, К, Л, М, Н, П, Р, С, Т, Ф, Х, Ц, Ч, Ш, Щ
- **1 modifier**: Ь (soft sign)
- Common confusions: В is a CONSONANT, І is a VOWEL, Й is a CONSONANT

---

## Editing Principles

- **IMPROVE, don't destroy.** Every rewrite should teach MORE than the original, not less.
- **PRESERVE the author's intent.** If a paragraph explains something poorly, rewrite it to explain it well — don't delete it.
- **MATCH the surrounding voice.** Your rewrite should read like the original author wrote it on a better day.
- Only DELETE truly empty sentences (pure cheerleading with zero information that cannot be salvaged). This should be rare.

---

## Fix Plan (from Phase D.1 review)



**NOTE: 6 inline fix(es) from the review have ALREADY been applied to the files. Do NOT re-apply those fixes. Read the CURRENT file contents carefully — they reflect the post-fix state. Only fix issues that are still present in the current files.**

## Review Findings (targeted fix required)

**CONSTRAINTS:**
- Fix ONLY the issues listed below
- Do NOT rewrite surrounding text
- Preserve word count and structure
- Only modify these sections: Across all sections, Activities file, line 280, Line 61 / Section "Навичка 2: Повсякденне життя (Skill 2: Daily Life)", Lines 12 and 16 / Sections quote block and "Огляд (Overview)", Lines 72, 76, 77, 146 / Section "Навичка 2: Повсякденне життя (Skill 2: Daily Life)" and "Підсумок", Section "Огляд (Overview)" / Module structure

### Finding 1: Ungrammatical Ukrainian — "дуже вранці"
**Location**: Line 61 / Section "Навичка 2: Повсякденне життя (Skill 2: Daily Life)"
**Problem**: "Дуже" is an intensifier that modifies adjectives and qualitative adverbs (дуже швидко, дуже добре), NOT temporal adverbs like "вранці" (in the morning). The English translation says "very early in the morning," confirming the intended meaning requires "рано" (early). "Дуже вранці" is ungrammatical in Ukrainian.
**Required Fix**: Change to **Я встаю́ ду́же ра́но вра́нці.** — I get up very early in the morning.
**Severity**: HIGH

### Finding 2: Double Stress Marks on коштувати/коштує
**Location**: Lines 72, 76, 77, 146 / Section "Навичка 2: Повсякденне життя (Skill 2: Daily Life)" and "Підсумок"
**Problem**: Ukrainian words have exactly ONE stress mark. "Коштувати" has stress on -ва-: коштува́ти. "Коштує" has stress on -ту-: кошту́є. The spurious stress on the first syllable (ко́-) is wrong in all 4 occurrences.
**Required Fix**: Remove first stress mark → кошту́є, коштува́ти
**Severity**: HIGH

### Finding 3: Missing TTT Initial Test Phase
**Location**: Section "Огляд (Overview)" / Module structure
**Problem**: The plan specifies `pedagogy: TTT` and the research notes (line 63) explicitly state "start with a brief self-assessment task (Test), then teach gaps (Teach), then apply (Test again)." The module claims TTT but implements Teach→Practice→Review instead. There is no initial diagnostic test where the learner discovers their own gaps before the review begins. The self-check questions at lines 144-147 serve as a final test, but no initial test exists.
**Required Fix**: Add a brief 5-question diagnostic mini-quiz at the end of the Overview section (before "Навичка 1"). Frame it: "Before we review, let's see what you remember! Try these without looking back at your notes." This creates the genuine TTT arc.
**Severity**: HIGH

### Finding 4: Structural Monotony — "Let's" Overuse
**Location**: Across all sections
**Problem**: Nearly every paragraph/sub-section opens with "Let's [verb]." This is classic LLM structural monotony — a real tutor would vary their transitions.
**Required Fix**: Vary openers: "Time to look at...", "Now for...", "Your next skill:", "Here's where X meets Y:", "Ready for...?" etc. At least 50% of "Let's" openers should be replaced.
**Severity**: HIGH

### Finding 5: Comparative Form Scope Creep in Activity
**Location**: Activities file, line 280
**Problem**: "Холодніше" is a comparative form of "холодно." Comparatives are not taught at A1 and a checkpoint must NOT introduce new grammar. The learner must answer based on context clues, but the form itself is scope creep.
**Required Fix**: Replace with: "Часто йде дощ, стає холодно?" or rephrase to "Часто йде дощ і дуже холодно?"
**Severity**: HIGH

### Finding 6: Repeated Phrase in Opening
**Location**: Lines 12 and 16 / Sections quote block and "Огляд (Overview)"
**Problem**: Verbatim repetition of the same praise phrase within 4 lines. Reads like copy-paste.
**Required Fix**: Change line 12 to: "You've come a long way in your Ukrainian journey!" or another distinct encouragement.
**Severity**: HIGH

---

## Critical Issues Found

### Issue 1: Ungrammatical Ukrainian — "дуже вранці"
- **Location**: Line 61 / Section "Навичка 2: Повсякденне життя (Skill 2: Daily Life)"
- **Original**: 「Я встаю́ ду́же вра́нці.」
- **Problem**: "Дуже" is an intensifier that modifies adjectives and qualitative adverbs (дуже швидко, дуже добре), NOT temporal adverbs like "вранці" (in the morning). The English translation says "very early in the morning," confirming the intended meaning requires "рано" (early). "Дуже вранці" is ungrammatical in Ukrainian.
- **Fix**: Change to **Я встаю́ ду́же ра́но вра́нці.** — I get up very early in the morning.

### Issue 2: Double Stress Marks on коштувати/коштує
- **Location**: Lines 72, 76, 77, 146 / Section "Навичка 2: Повсякденне життя (Skill 2: Daily Life)" and "Підсумок"
- **Original**: 「ко́шту́є」 and 「ко́штува́ти」
- **Problem**: Ukrainian words have exactly ONE stress mark. "Коштувати" has stress on -ва-: коштува́ти. "Коштує" has stress on -ту-: кошту́є. The spurious stress on the first syllable (ко́-) is wrong in all 4 occurrences.
- **Fix**: Remove first stress mark → кошту́є, коштува́ти

### Issue 3: Missing TTT Initial Test Phase
- **Location**: Section "Огляд (Overview)" / Module structure
- **Original**: 「This is a Test-Teach-Test checkpoint.」 (line 16)
- **Problem**: The plan specifies `pedagogy: TTT` and the research notes (line 63) explicitly state "start with a brief self-assessment task (Test), then teach gaps (Teach), then apply (Test again)." The module claims TTT but implements Teach→Practice→Review instead. There is no initial diagnostic test where the learner discovers their own gaps before the review begins. The self-check questions at lines 144-147 serve as a final test, but no initial test exists.
- **Fix**: Add a brief 5-question diagnostic mini-quiz at the end of the Overview section (before "Навичка 1"). Frame it: "Before we review, let's see what you remember! Try these without looking back at your notes." This creates the genuine TTT arc.

### Issue 4: Structural Monotony — "Let's" Overuse
- **Location**: Across all sections
- **Original**: 12+ paragraphs beginning with "Let's" — e.g., 「Let's start our review」 (line 24), 「let's do a past tense review」 (line 26), 「let's do an analytical future review」 (line 38), 「let's review direction expressions」 (line 46), 「let's review your daily routine vocabulary」 (line 57), 「Let's move on to food and drink vocabulary recall.」 (line 67), 「let's review weather expressions」 (line 96), 「let's connect these concepts」 (line 104), 「Let's build a connected narrative.」 (line 113)
- **Problem**: Nearly every paragraph/sub-section opens with "Let's [verb]." This is classic LLM structural monotony — a real tutor would vary their transitions.
- **Fix**: Vary openers: "Time to look at...", "Now for...", "Your next skill:", "Here's where X meets Y:", "Ready for...?" etc. At least 50% of "Let's" openers should be replaced.

### Issue 5: Comparative Form Scope Creep in Activity
- **Location**: Activities file, line 280
- **Original**: 「Часто йде дощ, стає холодніше?」
- **Problem**: "Холодніше" is a comparative form of "холодно." Comparatives are not taught at A1 and a checkpoint must NOT introduce new grammar. The learner must answer based on context clues, but the form itself is scope creep.
- **Fix**: Replace with: "Часто йде дощ, стає холодно?" or rephrase to "Часто йде дощ і дуже холодно?"

### Issue 6: Repeated Phrase in Opening
- **Location**: Lines 12 and 16 / Sections quote block and "Огляд (Overview)"
- **Original**: 「You have accomplished an incredible amount in your journey!」 (line 12) and 「You have accomplished an incredible amount in the past few lessons.」 (line 16)
- **Problem**: Verbatim repetition of the same praise phrase within 4 lines. Reads like copy-paste.
- **Fix**: Change line 12 to: "You've come a long way in your Ukrainian journey!" or another distinct encouragement.

---

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 61 | 「Я встаю́ ду́же вра́нці.」 | Я встаю́ ду́же ра́но вра́нці. | Grammar — "дуже" cannot modify "вранці" |
| 72 | 「ко́штува́ти」 | коштува́ти | Stress — single stress only |
| 72 | 「ко́шту́є」 (in Скі́льки ко́шту́є?) | кошту́є | Stress — single stress only |
| 76 | 「Скі́льки ко́шту́є суп?」 | Скі́льки кошту́є суп? | Stress — single stress only |
| 77 | 「Він ко́шту́є дві́сті гри́вень.」 | Він кошту́є дві́сті гри́вень. | Stress — single stress only |
| 146 | 「Скі́льки ко́шту́є обід?」 | Скі́льки кошту́є обід? | Stress — single stress only |

---

## Fix Plan to Reach 9/10 (REQUIRED)

### Language: 7/10 → 9/10
**What to fix:**
1. Line 61: Change 「Я встаю́ ду́же вра́нці.」 → "Я встаю́ ду́же ра́но вра́нці." — fixes ungrammatical modifier
2. Lines 72, 76, 77, 146: Remove spurious first stress from all коштувати/коштує instances — fixes double-stress error
**Expected score after fix:** 9/10

### LLM Fingerprint: 7/10 → 8/10
**What to fix:**
1. Replace 6+ of the 12 "Let's" openers with varied transitions
2. Line 12: Change opening encouragement to differ from line 16
**Expected score after fix:** 8/10

### Pedagogy: 7/10 → 9/10
**What to fix:**
1. Add a 5-question diagnostic mini-quiz after the "Огляд (Overview)" section to implement the TTT initial Test phase
2. Trim re-explanations in section "Навичка 1: Часові форми (Skill 1: Tenses)" (lines 26-27) to brief reminders rather than full re-teaching
**Expected score after fix:** 9/10

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. Same as Language fixes — the grammar error and stress errors are the only linguistic accuracy issues
**Expected score after fix:** 9/10

### Richness gaps (from audit):
- **engagement: 2/3** → Add 1 more engagement callout (e.g., a [!tip] in section "Навичка 3: Опис та погода (Skill 3: Description & Weather)" about how Ukrainians associate seasons with foods)
- **activity_types: 1/8** → This is a checkpoint with a single comprehensive quiz per plan. The plan only specifies `type: quiz`. This gap is inherent to the checkpoint design. Consider adding a `fill-in` activity for the integration tasks if the pipeline allows.

### Projected Overall After Fixes
```
(9×1.5 + 9×1.1 + 9×1.2 + 8×1.3 + 9×1.3 + 8×1.0 + 9×1.5) / 8.9
= (13.5 + 9.9 + 10.8 + 10.4 + 11.7 + 8.0 + 13.5) / 8.9
= 77.8 / 8.9
= 8.7/10
```

---

## Audit Failures (from automated re-audit)

```
✨ Purity violations found: 1
❌ [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'how do...'.
--- STRICT GATES (Level A1) ---
Immersion    🇺🇦 16.4% (checkpoint - no gate)
📚 PEDAGOGICAL VIOLATIONS FOUND:
[ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'how do...'.
📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
→ 2 violations (minor)
❌ [REVIEW_VERDICT_FAIL] Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
❌ AUDIT FAILED. Correct errors before proceeding.
Critical Failures:
• Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/checkpoint-daily-life-audit.log for details)
⚠️  RAG verification found unverified words (see audit report)
--- STATUS JSON GATE BLOCKERS ---
GATE BLOCKER: Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
```

---

## File Contents (for reference)

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/checkpoint-daily-life.md`

```markdown
<!-- SCOPE
Covers: Review and synthesis of a1-36, a1-37, a1-38, a1-39, a1-40, a1-42, a1-43
Not covered:
  - New grammar or vocabulary
  - Can and Know How → a1-45
-->

# Checkpoint: Daily Life

> **Чому це важливо?**
>
> You've come a long way in your Ukrainian journey! You can now talk about what you did, what you will do, what you eat, and what the weather is like. You have learned how to describe your actions and confidently navigate everyday situations. Now it is time to bring all those skills together and celebrate your progress!

## Огляд (Overview)

Welcome to your very first major checkpoint! You have accomplished an incredible amount in the past few lessons. This is a Test-Teach-Test checkpoint. Its primary purpose is testing the consolidation of everything you have learned in the A1.4 phase. We are going to look closely at your understanding of past and future tenses, your daily routine, food and shopping vocabulary, and weather expressions. 

The goal of this module is not to learn brand new grammar rules. Instead, this is a self-assessment orientation. It is all about identifying your strengths and catching any weaknesses in your tense usage, daily life vocabulary, and practical communication scenarios. By the end of this checkpoint, you will know exactly what you have mastered and what you might need to review before moving on. 

This is a safe space to practice. Do not worry about making mistakes. Mistakes are proof that you are trying and learning! We will go through each skill step-by-step. You will see brief reminders of the rules, look at some common errors, and then apply your knowledge to real-life situations. Grab a notebook, read the Ukrainian examples aloud, and see how much you can understand! Your journey so far has been amazing, and this is your chance to shine.

### Quick Diagnostic: What Do You Remember?

Before we review, try these five questions without looking back at your notes. Be honest with yourself — this is just for you!

1. How do you say "I worked yesterday" if you are a man? *(Hint: which verb ending?)*
2. How do you form the future tense in Ukrainian? *(Hint: which helper verb?)*
3. What is the Ukrainian word for "usually"?
4. How do you ask "How much does it cost?"
5. How do you say "Yesterday it was cold" in Ukrainian? *(Hint: what word do you add for past weather?)*

If you answered all five easily — excellent, this checkpoint will be a breeze! If some felt tricky, pay extra attention to those sections below. That is exactly what this review is for.

## Навичка 1: Часові форми (Skill 1: Tenses)

Time to review the most powerful tool in your grammar toolbox: the tenses. You have learned how to talk about actions that already happened and actions that will happen later.

### Model:

First, a past tense refresher. The past tense in Ukrainian is remarkably simple because it uses a predictable suffix pattern (for example, **працював**, **працювала**, **працювало**, and **працювали**). However, the absolute key rule is gender agreement in the past tense. The verb ending must perfectly match the gender of the subject performing the action.

> [!warning] Обережно!
> A frequent learner error is using the wrong gender suffix. English has no gender agreement for verbs, so it is easy to forget! If you are a man, you must never say **Він ходи́ла**. The correct form is always **Він ходи́в**. If you are a woman, you must use **Вона́ ходи́ла**.

Here is the past tense pattern with the verb **працюва́ти** (to work):

- **Я працюва́в вчо́ра.** — I worked yesterday. *(чол. / masc.)*
- **Я працюва́ла вчо́ра.** — I worked yesterday. *(жін. / fem.)*
- **Воно́ працюва́ло до́бре.** — It worked well. *(серед. / neut.)*
- **Ми працюва́ли ра́зом.** — We worked together. *(множ. / pl.)*

Now for the analytical future. When you want to talk about your plans, you use the helper verb **бу́ти** (to be) plus the infinitive form of your main verb. For example, **Я бу́ду чита́ти** (I will read) or **Ми бу́демо гуля́ти** (We will walk).

> [!tip] Important!
> Watch out for common errors: omitting the helper verb **бу́ду** entirely, or using the wrong infinitive form. The main verb must stay in its original dictionary form!

- **За́втра я бу́ду відпочива́ти вдо́ма.** — Tomorrow I will rest at home.
- **Вони́ бу́дуть сні́дати пі́зно.** — They will have breakfast late.

### Practice:

Your next challenge: direction expressions. You know the three-question paradigm: **Куди́?** (Where to?), **Зві́дки?** (Where from?), and **Де?** (Where at?). The integration of spatial grammar with tense usage is crucial for telling stories about your day. Each question triggers a different case form.

- **Де ти був вчо́ра?** — Where were you yesterday?
- **Я був у вели́кому магази́ні.** — I was at a big store.
- **Куди́ ти пі́деш за́втра?** — Where will you go tomorrow?
- **Я піду́ до рестора́ну.** — I will go to the restaurant.
- **Зві́дки вона́ йшла?** — Where was she coming from?
- **Вона́ йшла зі шко́ли.** — She was coming from school.

### Self-Check

Can you confidently form past tense verbs with correct gender endings? Can you build a future tense sentence with **бу́ду** + infinitive? Do you know which question word — **Де?**, **Куди́?**, or **Зві́дки?** — to use for location, direction, and origin?

## Навичка 2: Повсякденне життя (Skill 2: Daily Life)

Now that we have reviewed the tenses, it is time to revisit your daily routine vocabulary and sequence. You have learned the essential verbs to describe a typical day: **встава́ти** (to get up), **сні́дати** (to have breakfast), **обідати** (to have lunch), **вече́ряти** (to have dinner), and **ляга́ти спа́ти** (to go to sleep).

### Model:

Telling what you do and when is a vital conversational skill. To make your sentences flow naturally, you can add frequency adverbs like **зазвича́й** (usually), **ча́сто** (often), **і́ноді** (sometimes), and **рі́дко** (rarely).

- **Я встаю́ ду́же ра́но вра́нці.** — I get up very early in the morning.
- **Я зазвича́й обідаю вдо́ма.** — I usually have lunch at home.
- **Він ча́сто сні́дає пі́зно.** — He often has breakfast late.
- **Ми і́ноді готу́ємо ра́зом.** — We sometimes cook together.
- **Я рі́дко ляга́ю спа́ти ра́но.** — I rarely go to sleep early.

Now for food and drink vocabulary recall. Ordering food and expressing preferences should feel familiar now. You can easily name common items and order a meal in a cafe.

> [!culture] Культура
> In Ukraine, the rhythm of meals is a bit different. A typical **ра́нок** (morning) starts with a light breakfast. The lunch is usually the largest, warmest meal of the day, often featuring a hot soup. The **вече́ря** (dinner) is usually smaller and lighter.

### Practice:

Ready to test your shopping dialogue skills? You have learned the crucial question **Скі́льки кошту́є?** (How much does it cost?) and the verb **коштува́ти** (to cost). You also know quantity expressions and polite request patterns to use at the market or in a bakery.

> — **Добри́день. Я хо́чу купи́ти хліб.** — Good afternoon. I want to buy bread.
> — **Будь ла́ска. Що ще?** — Please. What else?
> — **Я хо́чу молоко́. Скі́льки кошту́є суп?** — I want milk. How much does soup cost?
> — **Він кошту́є дві́сті гри́вень.** — It costs two hundred hryvnias.
> — **До́бре.** — Good.

You can confidently use the verb **купува́ти** (to buy) to describe your shopping habits.

- **Я ча́сто купу́ю сві́жі овочі.** — I often buy fresh vegetables.
- **Вона́ бу́де купува́ти ка́ву.** — She will buy coffee.

### Self-Check

Can you describe your daily routine from morning to evening using the correct verbs? Can you add frequency adverbs to say how often you do things? Could you order food and ask prices at a Ukrainian market?

## Навичка 3: Опис та погода (Skill 3: Description & Weather)

To make your stories more colorful and precise, you need adverbs of manner. You know words like **до́бре** (well/good), **пога́но** (badly), **шви́дко** (fast), **пові́льно** (slowly), **ти́хо** (quietly), and **го́лосно** (loudly). Modifying verbs to describe how actions are performed makes your Ukrainian sound much more natural and expressive.

### Model:

- **Мій брат чита́є ду́же шви́дко.** — My brother reads very fast.
- **Студе́нти слу́хають викладача́ ти́хо.** — The students listen to the teacher quietly.
- **Ти гово́риш украї́нською до́бре.** — You speak Ukrainian well.

> [!did-you-know] Цікавий факт!
> The word **до́бре** is everywhere in daily Ukrainian conversations. It translates to "well" or "good," but it is also the most common way to say "okay," "agreed," or "fine" when making plans with friends!

Now we turn to weather expressions. In Ukrainian, we use impersonal constructions for weather description. This means you do not use a "dummy subject" like "it" in English. You simply state the condition directly using words like **тепло́** (warm), **хо́лодно** (cold), **со́нячно** (sunny), or **хма́рно** (cloudy).

- **Сього́дні на ву́лиці ду́же тепло́.** — Today it is very warm outside.
- **Вчора́ було́ ду́же хо́лодно.** — Yesterday was very cold.
- **За́втра бу́де тро́хи хма́рно.** — Tomorrow will be a bit cloudy.

Notice the time markers: for the past tense we add **було́**, and for the future tense we add **бу́де**.

> [!tip] Порада
> Ukrainians love connecting seasons to food! **Влі́тку** is the time for fresh berries and cherries, **восени́** brings apples and pumpkins, and **взи́мку** everyone craves hot **борщ**.

### Practice:

Here is where seasons meet weather. You can use your seasonal vocabulary to make general statements about the climate in Ukraine or your home country.

- **Взи́мку зазвича́й ду́же хо́лодно.** — In winter it is usually very cold.
- **Влі́тку ча́сто ду́же тепло́.** — In summer it is often very warm.
- **Восени́ ча́сто йде дощ.** — In autumn it often rains.
- **Навесні́ пого́да ду́же га́рна.** — In spring the weather is very beautiful.

### Self-Check

Can you describe the weather today, yesterday, and tomorrow using the correct time markers? Can you name the four seasons and associate typical weather with each one?

## Інтеграційне завдання (Integration Task)

This is where everything comes together in a practical way! Time to build a connected narrative. We will combine your past tense, daily routine, and food vocabulary into a single story.

Your first integration task: describe your yesterday. Imagine you are writing a diary entry or telling a friend about your day. Watch how the sentences logically flow into each other to create a timeline of events.

- **Вчора́ я встав о сьо́мій годи́ні.** — Yesterday I got up at seven o'clock.
- **Вра́нці було́ ду́же хо́лодно і хма́рно.** — In the morning it was very cold and cloudy.
- **Я сні́дав ка́шу і пив чай.** — I had porridge for breakfast and drank tea.
- **По́тім я пішо́в на робо́ту.** — Then I went to work.
- **В обід я їв смачни́й борщ.** — At lunch I ate delicious borscht.
- **Уве́чері я купува́в хліб у магази́ні.** — In the evening I was buying bread at the store.

If you are a woman, remember to change all those past tense verb endings: **вста́ла**, **сні́дала**, **пішла́**, **ї́ла**, and **купува́ла**. 

Now, your second integration task: describe your tomorrow. This time you will use the future tense, shopping vocabulary, and weather phrases in a connected narrative. This shows how you can plan your daily life.

- **За́втра я бу́ду готува́ти вече́рю.** — Tomorrow I will cook dinner.
- **Я піду́ в вели́кий магази́н.** — I will go to a big store.
- **Я бу́ду купува́ти сві́жі овочі.** — I will be buying fresh vegetables.
- **За́втра бу́де ду́же тепло́ і со́нячно.** — Tomorrow will be very warm and sunny.
- **Я бу́ду гуля́ти в мі́сті.** — I will walk in the city.

By practicing these short paragraphs, you are training your brain to think in complete Ukrainian sentences rather than translating word by word. You are truly ready to tell your own stories and share your daily life!

---

# Підсумок

You have successfully completed this checkpoint review! You should feel incredibly proud of your progress. You can now confidently navigate past and future tenses, describe your daily habits, and handle common situations like shopping or talking about the weather. This is exactly what you need for daily life in Ukrainian.

Take a moment to answer these self-check questions. If you can answer them easily, you are completely ready to dive into the next set of modules!

1. Як розповісти про минуле? (How to talk about the past?) — **Вчора́ я чита́в кни́гу.** (Yesterday I read a book - masc.) / **Вчора́ я чита́ла кни́гу.** (Yesterday I read a book - fem.)
2. Яке слово правильне для майбутнього? (Which word is correct for the future?) — I will eat breakfast. / **Я бу́ду сні́дати.**
3. Як запитати про ціну? (How to ask about the price?) — How much does lunch cost? / **Скі́льки кошту́є обід?**
4. Як описати погоду? (How to describe the weather?) — Today is warm. / **Сього́дні тепло́.**

Great job, celebrate your hard work, and keep up the fantastic learning!

---
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/checkpoint-daily-life.yaml`

```yaml
- type: quiz
  title: 'A1.4 Checkpoint: Daily Life Comprehensive Review'
  instruction: 'This checkpoint quiz tests everything you learned in the A1.4 phase: past and future tenses, daily routine, food, shopping, weather, and adverbs. Each question combines skills from multiple lessons. Choose the best answer.'
  items:
    - question: 'A man is describing his yesterday. Which sentence is correct?'
      options:
        - text: "Я працювала вчора."
          correct: false
        - text: "Я працював вчора."
          correct: true
        - text: "Я працювало вчора."
          correct: false
        - text: "Я буду працювати вчора."
          correct: false
      explanation: "A masculine speaker uses the -в ending in past tense: працював. The -ла ending is feminine, and буду + infinitive is future tense — it cannot combine with вчора (yesterday)."
    - question: 'A woman wants to say she cooked dinner yesterday. Which is correct?'
      options:
        - text: "Я готував вечерю вчора."
          correct: false
        - text: "Я буду готувати вечерю."
          correct: false
        - text: "Я готувала вечерю вчора."
          correct: true
        - text: "Я готувало вечерю вчора."
          correct: false
      explanation: "A feminine speaker uses the -ла ending: готувала. The -в ending is masculine, -ло is neuter, and буду готувати is future — wrong with вчора."
    - question: 'Which sentence correctly uses the future tense?'
      options:
        - text: "Завтра я снідав рано."
          correct: false
        - text: "Завтра я снідала рано."
          correct: false
        - text: "Завтра я буду снідати рано."
          correct: true
        - text: "Завтра я снідати рано."
          correct: false
      explanation: "Future tense requires буду + infinitive: буду снідати. Снідав/снідала are past tense forms, and the infinitive alone cannot be the main verb."
    - question: 'Someone asks you about your plans. Fill in the blank: Завтра ми ___ гуляти в місті.'
      options:
        - text: "гуляли"
          correct: false
        - text: "будемо"
          correct: true
        - text: "буду"
          correct: false
        - text: "гуляв"
          correct: false
      explanation: "With ми (we), the correct helper verb is будемо. Буду is for я only. Гуляли and гуляв are past tense forms."
    - question: 'Which question asks WHERE someone went (direction)?'
      options:
        - text: "Де ти був?"
          correct: false
        - text: "Звідки ти йшов?"
          correct: false
        - text: "Куди ти пішов?"
          correct: true
        - text: "Коли ти пішов?"
          correct: false
      explanation: "Куди means 'where to' (direction). Де means 'where at' (location), звідки means 'where from' (origin), and коли means 'when' (time)."
    - question: 'Your friend asks where you were yesterday. Which answer combines location and past tense correctly?'
      options:
        - text: "Я буду в магазині."
          correct: false
        - text: "Я був у магазині."
          correct: true
        - text: "Я був до магазину."
          correct: false
        - text: "Я буду в магазин."
          correct: false
      explanation: "Де? (where at) requires the locative case: у магазині. Був is past tense of бути. До магазину answers куди (direction), not де (location)."
    - question: 'Which pair correctly shows a past action and a future plan?'
      options:
        - text: "Вчора я читав. Завтра я читав."
          correct: false
        - text: "Вчора я буду читати. Завтра я читав."
          correct: false
        - text: "Вчора я читав. Завтра я буду читати."
          correct: true
        - text: "Вчора я буду читати. Завтра я буду читати."
          correct: false
      explanation: "Past tense (читав) goes with вчора (yesterday), and future tense (буду читати) goes with завтра (tomorrow). You cannot mix them the other way."
    - question: 'They (вони) will have breakfast late tomorrow. Choose the correct sentence.'
      options:
        - text: "Вони будемо снідати пізно."
          correct: false
        - text: "Вони будуть снідати пізно."
          correct: true
        - text: "Вони буду снідати пізно."
          correct: false
        - text: "Вони снідали пізно завтра."
          correct: false
      explanation: "With вони (they), the helper verb is будуть. Будемо is for ми, буду is for я, and снідали is past tense which cannot be used with завтра."
    - question: 'What does the sentence mean: Я зазвичай обідаю вдома?'
      options:
        - text: "I rarely have lunch at home."
          correct: false
        - text: "I usually have lunch at home."
          correct: true
        - text: "I sometimes have lunch at home."
          correct: false
        - text: "I never have lunch at home."
          correct: false
      explanation: "Зазвичай means 'usually.' Обідаю means 'I have lunch' and вдома means 'at home.' The sentence describes a regular daily habit."
    - question: 'Which frequency adverb means the OPPOSITE of часто?'
      options:
        - text: "зазвичай"
          correct: false
        - text: "іноді"
          correct: false
        - text: "рідко"
          correct: true
        - text: "завтра"
          correct: false
      explanation: "Рідко (rarely) is the opposite of часто (often). Зазвичай means 'usually,' іноді means 'sometimes,' and завтра is a time word, not a frequency adverb."
    - question: 'Put the daily routine in the correct time order. Which comes FIRST?'
      options:
        - text: "обідати"
          correct: false
        - text: "вечеряти"
          correct: false
        - text: "вставати"
          correct: true
        - text: "лягати спати"
          correct: false
      explanation: "Вставати (to get up) is the first action of the day. The typical order is: вставати → снідати → обідати → вечеряти → лягати спати."
    - question: 'A woman is telling her friend about her morning routine in past tense. Which is correct?'
      options:
        - text: "Вранці я встав і снідала."
          correct: false
        - text: "Вранці я встала і снідав."
          correct: false
        - text: "Вранці я встала і снідала."
          correct: true
        - text: "Вранці я встало і снідало."
          correct: false
      explanation: "Both verbs must agree with the feminine speaker: встала (got up) and снідала (had breakfast). You cannot mix masculine -в with feminine -ла."
    - question: 'Which sentence correctly combines a daily routine verb with a frequency adverb?'
      options:
        - text: "Він часто вечеряє пізно."
          correct: true
        - text: "Він часто вечеряти пізно."
          correct: false
        - text: "Він часто вечеряв пізно."
          correct: false
        - text: "Він часто будемо вечеряти."
          correct: false
      explanation: "For habitual actions in present tense, use the conjugated form: вечеряє (he has dinner). Вечеряти is the infinitive, вечеряв is past tense, and будемо is the wrong person (ми, not він)."
    - question: 'You want to buy bread at a store. How do you say it?'
      options:
        - text: "Я хочу коштувати хліб."
          correct: false
        - text: "Я хочу купити хліб."
          correct: true
        - text: "Я хочу готувати хліб."
          correct: false
        - text: "Я хочу снідати хліб."
          correct: false
      explanation: "Купити means 'to buy.' Коштувати means 'to cost' (not 'to buy'), готувати means 'to cook,' and снідати means 'to have breakfast.'"
    - question: 'How do you ask the price of soup?'
      options:
        - text: "Де коштує суп?"
          correct: false
        - text: "Куди коштує суп?"
          correct: false
        - text: "Скільки коштує суп?"
          correct: true
        - text: "Коли коштує суп?"
          correct: false
      explanation: "Скільки коштує? means 'How much does it cost?' Де means 'where,' куди means 'where to,' and коли means 'when' — none of these work with price."
    - question: 'Which sentence correctly describes a past shopping trip with food vocabulary?'
      options:
        - text: "Вчора я купував свіжі овочі в магазині."
          correct: true
        - text: "Вчора я буду купувати свіжі овочі."
          correct: false
        - text: "Завтра я купував свіжі овочі."
          correct: false
        - text: "Вчора я купувати свіжі овочі."
          correct: false
      explanation: "Вчора (yesterday) requires past tense: купував. Буду купувати is future tense, and the bare infinitive купувати cannot serve as the main verb in a sentence."
    - question: 'Which food item would you most likely order as a hot first course at a Ukrainian lunch?'
      options:
        - text: "каша"
          correct: false
        - text: "хліб"
          correct: false
        - text: "борщ"
          correct: true
        - text: "кава"
          correct: false
      explanation: "Борщ is the classic Ukrainian hot soup, typically served as the first course at lunch. Каша is porridge (breakfast), хліб is bread (side), and кава is coffee (drink)."
    - question: 'She will buy coffee and milk tomorrow. Choose the correct sentence.'
      options:
        - text: "Вона будемо купувати каву і молоко завтра."
          correct: false
        - text: "Вона буде купувати каву і молоко завтра."
          correct: true
        - text: "Вона буду купувати каву і молоко завтра."
          correct: false
        - text: "Вона купувала каву і молоко завтра."
          correct: false
      explanation: "With вона (she), the helper verb is буде. Будемо is for ми, буду is for я, and купувала is past tense — wrong with завтра (tomorrow)."
    - question: 'A man had porridge for breakfast and drank tea. Which sentence is correct?'
      options:
        - text: "Я снідала кашу і пила чай."
          correct: false
        - text: "Я снідав кашу і пив чай."
          correct: true
        - text: "Я снідав кашу і пила чай."
          correct: false
        - text: "Я снідало кашу і пило чай."
          correct: false
      explanation: "A masculine speaker must use -в endings for BOTH verbs: снідав (had breakfast) and пив (drank). Mixing -в and -ла within the same sentence is a gender agreement error."
    - question: 'What does добре mean when your friend suggests a plan and you reply with it?'
      options:
        - text: "goodbye"
          correct: false
        - text: "slowly"
          correct: false
        - text: "okay / agreed"
          correct: true
        - text: "badly"
          correct: false
      explanation: "Добре literally means 'well/good' but is commonly used as 'okay' or 'agreed' when responding to plans or suggestions in daily conversation."
    - question: 'Which adverb describes HOW someone reads? Мій брат читає дуже ___.'
      options:
        - text: "вчора"
          correct: false
        - text: "швидко"
          correct: true
        - text: "завтра"
          correct: false
        - text: "часто"
          correct: false
      explanation: "Швидко (fast/quickly) describes the manner of reading. Вчора and завтра are time words, and часто (often) describes frequency, not manner."
    - question: 'Which pair of adverbs are opposites?'
      options:
        - text: "добре — часто"
          correct: false
        - text: "швидко — повільно"
          correct: true
        - text: "тихо — добре"
          correct: false
        - text: "голосно — швидко"
          correct: false
      explanation: "Швидко (fast) and повільно (slowly) are opposites describing manner. Тихо (quietly) pairs with голосно (loudly), and добре (well) pairs with погано (badly)."
    - question: 'How do you say "Today it is warm and sunny" in Ukrainian?'
      options:
        - text: "Сьогодні тепло і сонячно."
          correct: true
        - text: "Сьогодні холодно і хмарно."
          correct: false
        - text: "Вчора було тепло і сонячно."
          correct: false
        - text: "Завтра буде тепло і сонячно."
          correct: false
      explanation: "Сьогодні (today) with no було/буде means present tense. Тепло = warm, сонячно = sunny. The other options are about yesterday or tomorrow."
    - question: 'Yesterday it was very cold. Which sentence is correct?'
      options:
        - text: "Вчора буде дуже холодно."
          correct: false
        - text: "Вчора дуже холодно."
          correct: false
        - text: "Вчора було дуже холодно."
          correct: true
        - text: "Завтра було дуже холодно."
          correct: false
      explanation: "Past weather requires було: вчора було холодно. Without було, the sentence sounds like present tense. Буде is future tense. Завтра (tomorrow) cannot take було (past)."
    - question: 'Tomorrow it will be cloudy. Choose the correct weather expression.'
      options:
        - text: "Завтра було хмарно."
          correct: false
        - text: "Завтра хмарно."
          correct: false
        - text: "Завтра буде хмарно."
          correct: true
        - text: "Вчора буде хмарно."
          correct: false
      explanation: "Future weather requires буде: завтра буде хмарно. Було is for past tense, and вчора (yesterday) cannot combine with буде (will be)."
    - question: 'Which season matches this description: Часто йде дощ і стає холодно?'
      options:
        - text: "влітку"
          correct: false
        - text: "взимку"
          correct: false
        - text: "восени"
          correct: true
        - text: "навесні"
          correct: false
      explanation: "Восени (in autumn) is when it often rains (часто йде дощ) and gets colder. Влітку (summer) is warm, взимку (winter) is snow, and навесні (spring) is getting warmer."
    - question: 'Which sentence integrates a season, weather, and a frequency adverb correctly?'
      options:
        - text: "Влітку зазвичай дуже тепло."
          correct: true
        - text: "Влітку зазвичай дуже холодно."
          correct: false
        - text: "Взимку часто дуже тепло."
          correct: false
        - text: "Навесні рідко погода."
          correct: false
      explanation: "Влітку (in summer) + зазвичай (usually) + тепло (warm) makes sense. Winter is cold not warm, and навесні рідко погода is grammatically incomplete."
    - question: 'Read this mini-story and answer: Вчора я встав рано. Вранці було холодно і хмарно. Я снідав кашу. What did the speaker do FIRST?'
      options:
        - text: "снідав кашу"
          correct: false
        - text: "встав рано"
          correct: true
        - text: "було холодно"
          correct: false
        - text: "пішов на роботу"
          correct: false
      explanation: "The speaker first встав рано (got up early), then noticed the weather, then снідав кашу (had porridge). Пішов на роботу is not mentioned in this excerpt."
    - question: 'A woman is planning her tomorrow: shopping, cooking, and a walk. Which set of sentences is ALL correct?'
      options:
        - text: "Я буду купувати овочі. Я буду готувати вечерю. Я буду гуляти."
          correct: true
        - text: "Я будемо купувати овочі. Я буду готувати вечерю. Я буду гуляти."
          correct: false
        - text: "Я буду купувати овочі. Я готувала вечерю. Я буду гуляти."
          correct: false
        - text: "Я буду купувати овочі. Я буду готувати вечерю. Я гуляла."
          correct: false
      explanation: "All three future plans need буду + infinitive with я. Будемо is for ми, not я. Готувала and гуляла are past tense — they break the future narrative."
    - question: 'Read the full scenario: Вчора було сонячно. Я пішла до ресторану і їла борщ. Завтра буде холодно. Я буду готувати вдома. Which statement about the speaker is TRUE?'
      options:
        - text: "The speaker is male and ate at home yesterday."
          correct: false
        - text: "The speaker is female, ate out yesterday, and will cook at home tomorrow."
          correct: true
        - text: "The speaker is female and will go to a restaurant tomorrow."
          correct: false
        - text: "The speaker is male and will cook at a restaurant tomorrow."
          correct: false
      explanation: "Пішла and їла use -ла endings (feminine speaker). She went to a restaurant yesterday (пішла до ресторану). Tomorrow she will cook at home (буду готувати вдома), not go out."
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/checkpoint-daily-life.yaml`

```yaml
items:
  - lemma: "вчора"
    translation: "yesterday"
    pos: "adverb"
    usage: "Temporal anchor for past tense narration."
    example: "Вчора я працював."
  - lemma: "завтра"
    translation: "tomorrow"
    pos: "adverb"
    usage: "Temporal anchor for future tense narration."
    example: "Завтра я буду снідати рано."
  - lemma: "ранок"
    translation: "morning"
    pos: "noun"
    gender: "m"
    usage: "Daily routine time marker; the adverbial form вранці means 'in the morning.'"
    example: "Вранці було холодно."
  - lemma: "обід"
    translation: "lunch"
    pos: "noun"
    gender: "m"
    usage: "The main midday meal in Ukrainian culture; verb form обідати."
    example: "Я зазвичай обідаю вдома."
  - lemma: "вечеря"
    translation: "dinner"
    pos: "noun"
    gender: "f"
    usage: "Evening meal, usually lighter; verb form вечеряти."
    example: "Завтра я буду готувати вечерю."
  - lemma: "купувати"
    translation: "to buy"
    pos: "verb"
    aspect: "imperfective"
    usage: "Shopping context; used with products and stores."
    example: "Я часто купую свіжі овочі."
  - lemma: "коштувати"
    translation: "to cost"
    pos: "verb"
    aspect: "imperfective"
    usage: "Used in the key phrase Скільки коштує? (How much does it cost?)"
    example: "Скільки коштує суп?"
  - lemma: "тепло"
    translation: "warm"
    pos: "adverb"
    usage: "Impersonal weather expression; no subject needed."
    example: "Сьогодні дуже тепло."
  - lemma: "холодно"
    translation: "cold"
    pos: "adverb"
    usage: "Impersonal weather expression; pairs with було/буде for past/future."
    example: "Вчора було дуже холодно."
  - lemma: "добре"
    translation: "well; good; okay"
    pos: "adverb"
    usage: "Adverb of manner and conversational response meaning 'agreed.'"
    example: "Ти говориш українською добре."
  - lemma: "зазвичай"
    translation: "usually"
    pos: "adverb"
    usage: "Frequency adverb for habitual actions in daily routine."
    example: "Я зазвичай обідаю вдома."
  - lemma: "іноді"
    translation: "sometimes"
    pos: "adverb"
    usage: "Frequency adverb for occasional actions."
    example: "Ми іноді готуємо разом."
  - lemma: "часто"
    translation: "often"
    pos: "adverb"
    usage: "High-frequency adverb for habits; opposite of рідко."
    example: "Він часто снідає пізно."
  - lemma: "рідко"
    translation: "rarely"
    pos: "adverb"
    usage: "Frequency adverb; opposite of часто."
    example: "Я рідко лягаю спати рано."
  - lemma: "погода"
    translation: "weather"
    pos: "noun"
    gender: "f"
    usage: "Used with adjectives for weather descriptions."
    example: "Навесні погода дуже гарна."
  - lemma: "сьогодні"
    translation: "today"
    pos: "adverb"
    usage: "Present-tense time marker for weather and daily events."
    example: "Сьогодні на вулиці дуже тепло."
  - lemma: "швидко"
    translation: "fast; quickly"
    pos: "adverb"
    usage: "Adverb of manner; opposite of повільно."
    example: "Мій брат читає дуже швидко."
  - lemma: "готувати"
    translation: "to cook; to prepare"
    pos: "verb"
    aspect: "imperfective"
    usage: "Daily routine and food context."
    example: "Завтра я буду готувати вечерю."
  - lemma: "хмарно"
    translation: "cloudy"
    pos: "adverb"
    usage: "Impersonal weather expression."
    example: "Завтра буде трохи хмарно."
  - lemma: "сонячно"
    translation: "sunny"
    pos: "adverb"
    usage: "Impersonal weather expression."
    example: "Завтра буде дуже тепло і сонячно."
```

---

## Instructions

1. For each issue in the Fix Plan or audit failures, use **Grep** to verify the exact text exists in the file
2. Use the **Edit** tool to fix each issue directly in the file
3. Only fix issues documented above — no silent extra changes
4. Prioritize: audit gate failures first, then review issues

---

## How to Fix

Use the Edit tool for each fix. The workflow for each issue:

1. **Grep** the file to confirm the text exists and is unique
2. **Edit** the file: provide `old_string` (exact text from file) and `new_string` (corrected text)
3. Move to next issue

File paths:
- Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/checkpoint-daily-life.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/checkpoint-daily-life.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/checkpoint-daily-life.yaml`

## Fix Rules

- Only fix issues documented in the Fix Plan or audit failures above
- You MAY add new activities or modify existing ones if the Fix Plan explicitly requests it
- Do NOT add new prose sections or vocabulary items unless the Fix Plan explicitly requests it
- Maximum **20 edits** total (prioritize the most impactful fixes)
- If nothing needs fixing, state that clearly

---

## Friction Report (MANDATORY)

After all fixes, output:

```
===FRICTION_START===
**Phase**: Phase D.2: Targeted Repair
**Step**: {what you were doing when friction occurred, or "Full Phase D.2"}
**Friction Type**: NONE | EDIT_FAILED | TEXT_NOT_FOUND | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===
```

---

## Boundaries

- Do NOT write a review — that was already done in Phase D.1
- Do NOT output ===REVIEW_START=== blocks
- Do NOT output FIND/REPLACE blocks — use the Edit tool instead
- You MAY add/modify activities if the Fix Plan requests it
- Do NOT make cosmetic changes beyond what the review flagged
