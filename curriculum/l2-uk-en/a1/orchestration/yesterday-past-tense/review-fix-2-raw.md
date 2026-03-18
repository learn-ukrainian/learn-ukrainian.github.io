✅ Message sent to Gemini (ID: 26514) [auto-acked: self-addressed]

🚀 Invoking Gemini to process message #26514...
📨 Message #26514
   From: gemini → To: gemini
   Type: query
   Task: yesterday-past-tense-review-fix-2
   Time: 2026-03-18T00:00:26.087624+00:00

============================================================

# Gemini Review Fix: Targeted Repair via FIND/REPLACE

> **You are an expert Ukrainian language editor applying targeted fixes.**
> You have NO tools — output FIND/REPLACE pairs only.
> The build system will apply your fixes programmatically.

---

## Editing Principles

- **IMPROVE, don't destroy.** Every rewrite should teach MORE than the original.
- **PRESERVE the author's intent.** Rewrite poorly explained content to explain it well — don't delete it.
- **MATCH the surrounding voice.** Your fixes should read like the original author wrote them on a better day.
- Only DELETE truly empty sentences (pure cheerleading with zero information).

---

## Fix Plan (from review)

## Review Findings (targeted fix required)

**CONSTRAINTS:**
- Fix ONLY the issues listed below
- Do NOT rewrite surrounding text
- Preserve word count and structure
- Only modify these sections: "Основи минулого часу" and "Підсумок: Мій день", "Складні випадки та практика", Activities > "Change the Verb to Past Tense"

### Finding 1: Anglicism / English Calque in Impersonal Sentence
**Location**: Activities > "Change the Verb to Past Tense"
**Problem**: `- sentence: "Воно ___ цікаво."` with `explanation: "Воно (it/neuter) takes the neuter ending -ло: було."` Using "Воно" as a dummy subject is a direct calque from English ("It was interesting"). True Ukrainian impersonal sentences drop the subject: "Було цікаво." The text gets this right (`- **Було цікаво!**`), but the activity explicitly drills the error.
**Required Fix**: Remove "Воно" from the activity sentence and update the explanation to mention impersonal sentences.
**Severity**: HIGH

### Finding 2: Euphony (Чергування у/в) Violations
**Location**: "Основи минулого часу" and "Підсумок: Мій день"
**Problem**: The module repeatedly uses `у офісі` before a vowel: `A woman says: **Я працювала у офісі.**` According to Ukrainian euphony rules, `в` is strictly preferred before words starting with a vowel to avoid hiatus, especially when the preceding word also ends in a vowel (`працювала в офісі`).
**Required Fix**: Replace all instances of `у офісі` with `в офісі`.
**Severity**: HIGH

### Finding 3: Inaccurate Morphological Breakdown of Reflexives
**Location**: "Складні випадки та практика"
**Problem**: `The particle stays attached — it just shifts from **-ся** to **-лася** in the feminine form.` This is linguistically false. The reflexive particle is simply `-ся`. The feminine gender ending is `-ла`. The particle does not "shift"; it is appended (`-ла` + `-ся`). Activity 2 compounds this with: `Asking a man, so use masculine -ся: ти дивився.` There is no "masculine -ся".
**Required Fix**: Correct the explanation to state that the `-ся` particle is added *after* the gender ending (`-в`, `-ла`, `-ло`, `-ли`).
**Severity**: HIGH

### Finding 4: Inaccurate Root Identification
**Location**: "Складні випадки та практика"
**Problem**: `The root shortens from **їст-** to **ї-**...` This is morphologically incorrect. The historical root is `їд-`, and `-ти` is the infinitive suffix. Calling `їст-` the root is factually wrong and confusing for future verb conjugations.
**Required Fix**: Rephrase to avoid mislabeling the root: "The infinitive ends in **-сти**, but the past tense uses the short stem **ї-**."
**Severity**: HIGH

---

## Plan Adherence Issues (Deterministic — MUST FIX)

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥25 items
  - Actual: Activity has 12 items
  - Fix: Add 13 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥25 items
  - Actual: Activity has 10 items
  - Fix: Add 15 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥25 items
  - Actual: Activity has 6 items
  - Fix: Add 19 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥20 items
  - Actual: Activity has 12 items
  - Fix: Add 8 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥20 items
  - Actual: Activity has 10 items
  - Fix: Add 10 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥20 items
  - Actual: Activity has 6 items
  - Fix: Add 14 more items to 'fill-in' activity


---

## Critical Issues Found

### Issue 1: Anglicism / English Calque in Impersonal Sentence
**Location**: Activities > "Change the Verb to Past Tense"
**Problem**: `- sentence: "Воно ___ цікаво."` with `explanation: "Воно (it/neuter) takes the neuter ending -ло: було."` Using "Воно" as a dummy subject is a direct calque from English ("It was interesting"). True Ukrainian impersonal sentences drop the subject: "Було цікаво." The text gets this right (`- **Було цікаво!**`), but the activity explicitly drills the error.
**Fix**: Remove "Воно" from the activity sentence and update the explanation to mention impersonal sentences.

### Issue 2: Euphony (Чергування у/в) Violations
**Location**: "Основи минулого часу" and "Підсумок: Мій день"
**Problem**: The module repeatedly uses `у офісі` before a vowel: `A woman says: **Я працювала у офісі.**` According to Ukrainian euphony rules, `в` is strictly preferred before words starting with a vowel to avoid hiatus, especially when the preceding word also ends in a vowel (`працювала в офісі`).
**Fix**: Replace all instances of `у офісі` with `в офісі`.

### Issue 3: Inaccurate Morphological Breakdown of Reflexives
**Location**: "Складні випадки та практика"
**Problem**: `The particle stays attached — it just shifts from **-ся** to **-лася** in the feminine form.` This is linguistically false. The reflexive particle is simply `-ся`. The feminine gender ending is `-ла`. The particle does not "shift"; it is appended (`-ла` + `-ся`). Activity 2 compounds this with: `Asking a man, so use masculine -ся: ти дивився.` There is no "masculine -ся".
**Fix**: Correct the explanation to state that the `-ся` particle is added *after* the gender ending (`-в`, `-ла`, `-ло`, `-ли`).

### Issue 4: Inaccurate Root Identification
**Location**: "Складні випадки та практика"
**Problem**: `The root shortens from **їст-** to **ї-**...` This is morphologically incorrect. The historical root is `їд-`, and `-ти` is the infinitive suffix. Calling `їст-` the root is factually wrong and confusing for future verb conjugations.
**Fix**: Rephrase to avoid mislabeling the root: "The infinitive ends in **-сти**, but the past tense uses the short stem **ї-**."

---

## Ukrainian Language Issues
- `Воно було цікаво` (Direct English Calque)
- `працював у офісі` / `працювала у офісі` (Euphony / hiatus rule violation)

---

## Fix Plan to Reach 9.5+
1. Fix the English calque in Activity 1 by removing the dummy subject "Воно".
2. Correct all instances of "у офісі" to "в офісі" to respect Ukrainian euphony rules.
3. Rewrite the reflexive verb explanation to accurately reflect that `-ся` attaches *after* the gender ending.
4. Correct the explanation of the verb "їсти" so it does not falsely claim the root is "їст-".
5. Ignore the deterministic pre-screen errors regarding agreement (line 45 and 79), as the text (`вона спала, вони спали` and `вона була / воно було`) is grammatically correct. The scanner triggered false positives on adjacent tokens.

---

## Audit Failures (from automated re-audit)

```
⚠️  English hints in A2+ activities: 2
🔴 [ENGLISH_HINTS_IN_ACTIVITY] Choose the Correct Gender Form
⚠️ [ENGLISH_HINTS_IN_ACTIVITY] What Did You Do Yesterday?
--- STRICT GATES (Level A1) ---
Pedagogy     ❌ 2 violations
📚 PEDAGOGICAL VIOLATIONS FOUND:
📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
→ 2 violations (minor)
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/yesterday-past-tense-audit.log for details)
⚠️  RAG verification found unverified words (see audit report)
--- VESUM WORD VERIFICATION FAILURES ---
These words were NOT found in the VESUM morphological dictionary.
Check if they are valid Ukrainian forms. Fix misspellings or Russianisms.
  ❌ `Захарійчук` (source: prose)
  ❌ `ЗУНР` (source: prose)
  ❌ `Кравцова` (source: prose)
  ❌ `лася` (source: prose)
  ❌ `ли` (source: prose)
  ❌ `ло` (source: prose)
  ❌ `Львові` (source: prose)
  ❌ `Федоров` (source: prose)
  ❌ `ї` (source: prose)
  ❌ `їст` (source: prose)
  ❌ `їстив` (source: prose)
```

---

## File Contents

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/yesterday-past-tense.md`

```markdown
## Вступ: Що було вчора? (Introduction: What Happened Yesterday?)

You already know how to talk about what's happening right now — **Я читаю книгу**, **Він працює**. But what about yesterday? What happened last week? What did you do this morning? You're about to unlock the past tense, and it's actually simpler than you might expect. Ukrainian past tense is much easier than the present tense because it does not change based on the person speaking.

Here's a taste. On February 15, 1574, the first printer published the famous book in the city of Lviv. In Ukrainian:

- **Друкар надрукував «Апостол» у місті Львів.**

That word **надрукував** is past tense. It describes an action that is already complete. By the end of this module, you'll be forming past tense verbs yourself and confidently telling stories about **вчора** (yesterday), sharing your experiences, and talking about history.

### Time expressions for the past

Before diving into verb forms, you need the time words that signal past events. Ukrainian uses the adjective **минулий** (last, past) in the genitive case — and importantly, *without* any preposition:

- **вчора** — yesterday
- **вчора зранку** — yesterday morning
- **вчора ввечері** — yesterday evening
- **минулого тижня** — last week
- **минулого місяця** — last month
- **минулого року** — last year
- **раніше** — earlier, before

> [!warning] No preposition needed!
> English says "last week," and some learners want to add **в**: ~~в минулому тижні~~. The correct form is simply **минулого тижня** — genitive case, no preposition. The same pattern works for **минулого місяця** (last month).

With just **вчора** and a few past tense verbs, you can talk about your whole day. Let's learn how to form those verbs!

## Основи минулого часу (Grammar: Past Tense Formation)

Great news — Ukrainian past tense is simpler than present tense! In the present tense, you conjugate for six different persons (я, ти, він, ми, ви, вони), which means learning many different endings. In the past tense, you only match **gender** and **number**. There are absolutely no person endings to worry about. This makes speaking about the past very quick to learn and use in daily life.

### The formula

Take the infinitive, remove the infinitive suffix, and add one of four endings:

| Gender/Number | Ending | читати | робити |
|---|---|---|---|
| він (he) | ends in **в** | читав | робив |
| вона (she) | ends in **ла** | читала | робила |
| воно (it) | ends in **ло** | читало | робило |
| вони (they) | ends in **ли** | читали | робили |

Four endings — that's it! Here are more examples with verbs you know:

- **пити** → він **пив**, вона **пила**, вони **пили**
- **спати** → він **спав**, вона **спала**, вони **спали**
- **працювати** → він **працював**, вона **працювала**

> [!tip] Quick pattern
> **Masculine** ends with the letter **в** (after the stem vowel).
> **Feminine** always ends with **ла**. **Neuter** always ends with **ло**. **Plural** always ends with **ли**.
> Just change the vowel before the last letter — easy!

### Gender agreement matters

Here's the biggest difference from English: your past tense form depends on YOUR gender. In English, "I worked" is the same for everyone. In Ukrainian:

- A man says: **Я працював в офісі.**
- A woman says: **Я працювала в офісі.**

The same applies when talking to someone using **ти**:

- To a man: **Ти читав книгу?**
- To a woman: **Ти читала книгу?**

> [!warning] Common mistake
> If you're a woman, don't say ~~Я писав~~. The correct form is **Я писала**. Always match the verb ending to the speaker's gender when using **я** or **ти**.

### Don't add бути!

English speakers sometimes want to translate "I was working" by adding **бути** (to be) before the verb. Don't do this!

- ✅ **Я працював.** — I was working. / I worked.
- ❌ ~~Я був працював.~~ — This is wrong!

Ukrainian imperfective past covers both English simple past ("I worked") and past progressive ("I was working"). One form does the work of two — that's a win for you!

The verb **бути** does have its own past tense forms, and they're very useful on their own:

- він **був** / вона **була** / воно **було** / вони **були**

Use these to say where you were or how something was:

- **Я був удома.** — I was at home. (man speaking)
- **Я була на роботі.** — I was at work. (woman speaking)
- **Було цікаво!** — It was interesting!

## Складні випадки та практика (Irregular Verbs and Practice)

Most verbs follow the pattern you just learned. But a few very common verbs have irregular past forms. Don't worry — there are only a handful, and you'll memorize them quickly with practice.

### Їсти (to eat) — short stem

The verb **їсти** doesn't follow the regular pattern. Instead of adding a regular ending, the past tense uses a short stem:

- він **їв** / вона **їла** / воно **їло** / вони **їли**

The infinitive ends in **-сти**, but the past tense uses the short stem! Examples in context:

- **Він їв яблуко.** — He ate an apple.
- **Вона їла кашу зранку.** — She ate porridge in the morning.
- **Ми їли обід у ресторані.** — We ate lunch at a restaurant.

### Йти (to go) — suppletive forms

The verb **йти** (to go on foot, one direction) has completely different past tense forms:

- він **ішов** / вона **ішла** / вони **ішли**

Compare this with **ходити** (to go regularly, or there and back):

- він **ходив** / вона **ходила** / вони **ходили**

For now, remember this simple distinction:
- **ішов/ішла** = was going somewhere (one trip)
- **ходив/ходила** = went somewhere (and came back)

- **Він ішов додому.** — He was going home.
- **Вона ходила в магазин.** — She went to the store.

### Practice: masculine vs. feminine

Let's drill the gender pairs. Notice the pattern:

- він **пив** / вона **пила**
- він **дивився** / вона **дивилася**
- він **ішов** / вона **ішла**
- він **був** / вона **була**
- він **спав** / вона **спала**

Notice that **дивитися** keeps its reflexive particle in the past tense. The particle is added after the gender ending: he watched is **дивився**, she watched is **дивилася**.

> [!culture] Two February 15ths
> February 15 is a remarkable date in Ukrainian history. In 1574, the first book was printed. And in 1919, the new republic passed a law making Ukrainian the state language: **Республіка прийняла закон про державну мову.** Two past tense sentences — two turning points in Ukrainian culture.

Now let's see past tense in a real conversation:

> **(У кафе / At a café)**
>
> — Привіт! Що ти робив вчора?
> — Hello! What did you do yesterday?
>
> — Вчора я читав книгу вдома.
> — Yesterday I read a book at home.
>
> — А я ходила в музей. Було цікаво!
> — And I went to the museum. It was interesting!
>
> — Ти їла там?
> — Did you eat there?
>
> — Ні, я пила тільки каву.
> — No, I only drank coffee.

> **(На роботі / At work)**
>
> — Що ти робила ввечері?
> — What did you do in the evening?
>
> — Я дивилася серіал. А ти?
> — I watched a TV series. And you?
>
> — Я спав. Я був дуже втомлений.
> — I slept. I was very tired.

## Підсумок: Мій день (Summary and Production)

You've made great progress! You can now describe your entire yesterday. Here's a sample:

- **Вчора зранку я робив каву.** — Yesterday morning I made coffee.
- **Потім я ходила в магазин.** — Then I went to the store.
- **Я ішов додому.** — I was going home.
- **Ввечері я дивився фільм.** — In the evening I watched a movie.

> [!practice] Your turn!
> Try building your own story about yesterday. Use these question-and-answer patterns:
> - **Що ти робив/робила вчора?** — What did you do yesterday?
> - **Де ти був/була?** — Where were you?
> - **Що ти їв/їла?** — What did you eat?

### Quick reference: gender endings

Remember — match the verb to the subject's gender:

| Subject | -в | -ла | -ло | -ли |
|---|---|---|---|---|
| він / я (♂) | **був** | — | — | — |
| вона / я (♀) | — | **була** | — | — |
| воно | — | — | **було** | — |
| вони / ми | — | — | — | **були** |

### Self-check

Before moving on, make sure you can:

1. Form the past tense of any regular verb (remove the infinitive suffix, add the correct past ending)
2. Choose the correct gender ending for **я** and **ти** based on the speaker's gender
3. Use **був/була/було/були** to say where you were
4. Handle irregular forms: **їв/їла** and **ішов/ішла**
5. Use time expressions **вчора**, **минулого тижня**, **раніше** — without adding a preposition

> [!tip] Ukrainian proverb
> **Що було, те минуло.** — What was, has passed. A perfect summary of the past tense — and great folk wisdom!

You can now talk about yesterday, last week, and even events from centuries ago. In the next module, you'll learn how to talk about **tomorrow** — the future tense!

<!-- adapted from textbook sources -->
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/yesterday-past-tense.yaml`

```yaml
- type: fill-in
  title: "Change the Verb to Past Tense"
  instruction: "Each sentence needs a past tense verb. Choose the correct form."
  items:
    - sentence: "Вчора він ___ книгу."
      answer: "читав"
      options: ["читав", "читати", "читає", "читала"]
      explanation: "Він (he) takes the masculine ending -в: читав."
    - sentence: "Вона ___ каву зранку."
      answer: "пила"
      options: ["пив", "пила", "пити", "п'є"]
      explanation: "Вона (she) takes the feminine ending -ла: пила."
    - sentence: "Вони ___ обід у ресторані."
      answer: "їли"
      options: ["їсти", "їв", "їла", "їли"]
      explanation: "Вони (they) takes the plural ending -ли: їли."
    - sentence: "Він ___ в офісі."
      answer: "працював"
      options: ["працювати", "працює", "працював", "працювала"]
      explanation: "Він takes the masculine ending -в: працював."
    - sentence: "Вона ___ додому."
      answer: "ішла"
      options: ["ішла", "ішов", "йти", "іде"]
      explanation: "Вона takes the feminine form: ішла."
    - sentence: "Він ___ довго."
      answer: "спав"
      options: ["спати", "спав", "спала", "спить"]
      explanation: "Він takes the masculine ending -в: спав."
    - sentence: "Вони ___ фільм ввечері."
      answer: "дивилися"
      options: ["дивитися", "дивився", "дивилася", "дивилися"]
      explanation: "Вони takes the plural form: дивилися."
    - sentence: "Вчора ___ цікаво."
      answer: "було"
      options: ["був", "була", "було", "бути"]
      explanation: "Impersonal sentences use the neuter verb form: вчора було."
    - sentence: "Він ___ яблуко."
      answer: "їв"
      options: ["їсти", "їв", "їла", "їли"]
      explanation: "Він takes the irregular masculine form: їв."
    - sentence: "Вона ___ листа."
      answer: "писала"
      options: ["писати", "писав", "писала", "пише"]
      explanation: "Вона takes the feminine ending -ла: писала."
    - sentence: "Він ___ в магазин."
      answer: "ходив"
      options: ["ходити", "ходив", "ходила", "ходить"]
      explanation: "Він takes the masculine ending -в: ходив."
    - sentence: "Вона ___ уроки."
      answer: "робила"
      options: ["робити", "робив", "робила", "робить"]
      explanation: "Вона takes the feminine ending -ла: робила."
    - sentence: "Він ___ довго."
      answer: "думав"
      options: ["думати", "думав", "думала", "думають"]
      explanation: "Він takes the masculine ending: думав."
    - sentence: "Вона ___ пісню."
      answer: "співала"
      options: ["співав", "співати", "співала", "співає"]
      explanation: "Вона takes the feminine ending: співала."
    - sentence: "Вони ___ швидко."
      answer: "бігли"
      options: ["біг", "бігла", "бігли", "бігати"]
      explanation: "Вони takes the plural ending: бігли."
    - sentence: "Він ___ питання."
      answer: "розумів"
      options: ["розумів", "розуміла", "розуміти", "розуміє"]
      explanation: "Він takes the masculine ending: розумів."
    - sentence: "Вона ___ текст."
      answer: "знала"
      options: ["знав", "знати", "знає", "знала"]
      explanation: "Вона takes the feminine ending: знала."
    - sentence: "Вони ___ вдома."
      answer: "сиділи"
      options: ["сидів", "сиділа", "сиділи", "сидіти"]
      explanation: "Вони takes the plural ending: сиділи."
    - sentence: "Він ___ лист."
      answer: "відправив"
      options: ["відправила", "відправити", "відправив", "відправляє"]
      explanation: "Він takes the masculine ending: відправив."
    - sentence: "Вона ___ вікно."
      answer: "відкрила"
      options: ["відкрив", "відкрила", "відкрили", "відкрити"]
      explanation: "Вона takes the feminine ending: відкрила."
    - sentence: "Вони ___ музику."
      answer: "слухали"
      options: ["слухав", "слухати", "слухала", "слухали"]
      explanation: "Вони takes the plural ending: слухали."
    - sentence: "Він ___ відпочивати."
      answer: "хотів"
      options: ["хотів", "хотіла", "хотіли", "хотіти"]
      explanation: "Він takes the masculine ending: хотів."
    - sentence: "Вона ___ слова."
      answer: "повторювала"
      options: ["повторював", "повторювала", "повторювати", "повторює"]
      explanation: "Вона takes the feminine ending: повторювала."
    - sentence: "Вони ___ правило."
      answer: "вивчали"
      options: ["вивчав", "вивчала", "вивчати", "вивчали"]
      explanation: "Вони takes the plural ending: вивчали."
    - sentence: "Він ___ правду."
      answer: "говорив"
      options: ["говорив", "говорила", "говорили", "говорити"]
      explanation: "Він takes the masculine ending: говорив."
- type: fill-in
  title: "Choose the Correct Gender Form"
  instruction: "The subject tells you the gender. Pick the past tense form that matches."
  items:
    - sentence: "Я ___ книгу. (female speaker)"
      answer: "читала"
      options: ["читав", "читала", "читало", "читали"]
      explanation: "A female speaker uses the feminine ending -ла: я читала."
    - sentence: "Я ___ удома. (male speaker)"
      answer: "був"
      options: ["був", "була", "було", "були"]
      explanation: "A male speaker uses the masculine form: я був."
    - sentence: "Ти ___ на роботі? (asking a woman)"
      answer: "була"
      options: ["був", "була", "було", "були"]
      explanation: "Asking a woman, so use feminine -ла: ти була."
    - sentence: "Я ___ каву. (male speaker)"
      answer: "пив"
      options: ["пив", "пила", "пило", "пили"]
      explanation: "A male speaker uses the masculine form: я пив."
    - sentence: "Ти ___ фільм? (asking a man)"
      answer: "дивився"
      options: ["дивився", "дивилася", "дивилося", "дивилися"]
      explanation: "Asking a man, so use the masculine form: ти дивився."
    - sentence: "Я ___ в офісі. (female speaker)"
      answer: "працювала"
      options: ["працював", "працювала", "працювало", "працювали"]
      explanation: "A female speaker uses the feminine ending -ла: я працювала."
    - sentence: "Ти ___ вчора? (asking a man)"
      answer: "спав"
      options: ["спав", "спала", "спало", "спали"]
      explanation: "Asking a man, so use masculine -в: ти спав."
    - sentence: "Я ___ в музей. (female speaker)"
      answer: "ходила"
      options: ["ходив", "ходила", "ходило", "ходили"]
      explanation: "A female speaker uses the feminine ending -ла: я ходила."
    - sentence: "Ти ___ листа? (asking a woman)"
      answer: "писала"
      options: ["писав", "писала", "писало", "писали"]
      explanation: "Asking a woman, so use feminine -ла: ти писала."
    - sentence: "Я ___ серіал. (male speaker)"
      answer: "дивився"
      options: ["дивився", "дивилася", "дивилося", "дивилися"]
      explanation: "A male speaker uses the masculine form: я дивився."
    - sentence: "Ти ___ довго? (asking a woman)"
      answer: "думала"
      options: ["думав", "думала", "думало", "думали"]
      explanation: "Asking a woman, use feminine: ти думала."
    - sentence: "Я ___ вікно. (female speaker)"
      answer: "відкрила"
      options: ["відкрив", "відкрила", "відкрило", "відкрили"]
      explanation: "A female speaker uses feminine: я відкрила."
    - sentence: "Ти ___ вдома? (asking a man)"
      answer: "сидів"
      options: ["сидів", "сиділа", "сиділо", "сиділи"]
      explanation: "Asking a man, use masculine: ти сидів."
    - sentence: "Я ___ питання. (male speaker)"
      answer: "розумів"
      options: ["розумів", "розуміла", "розуміло", "розуміли"]
      explanation: "A male speaker uses masculine: я розумів."
    - sentence: "Ти ___ пісню? (asking a woman)"
      answer: "співала"
      options: ["співав", "співала", "співало", "співали"]
      explanation: "Asking a woman, use feminine: ти співала."
    - sentence: "Я ___ швидко. (female speaker)"
      answer: "бігла"
      options: ["біг", "бігла", "бігло", "бігли"]
      explanation: "A female speaker uses feminine: я бігла."
    - sentence: "Ти ___ слова? (asking a man)"
      answer: "повторював"
      options: ["повторював", "повторювала", "повторювало", "повторювали"]
      explanation: "Asking a man, use masculine: ти повторював."
    - sentence: "Я ___ відпочивати. (male speaker)"
      answer: "хотів"
      options: ["хотів", "хотіла", "хотіло", "хотіли"]
      explanation: "A male speaker uses masculine: я хотів."
    - sentence: "Ти ___ правило? (asking a woman)"
      answer: "вивчала"
      options: ["вивчав", "вивчала", "вивчало", "вивчали"]
      explanation: "Asking a woman, use feminine: ти вивчала."
    - sentence: "Я ___ текст. (female speaker)"
      answer: "знала"
      options: ["знав", "знала", "знало", "знали"]
      explanation: "A female speaker uses feminine: я знала."
    - sentence: "Ти ___ лист? (asking a man)"
      answer: "відправив"
      options: ["відправив", "відправила", "відправило", "відправили"]
      explanation: "Asking a man, use masculine: ти відправив."
    - sentence: "Я ___ правду. (male speaker)"
      answer: "говорив"
      options: ["говорив", "говорила", "говорило", "говорили"]
      explanation: "A male speaker uses masculine: я говорив."
    - sentence: "Ти ___ роботу? (asking a woman)"
      answer: "почала"
      options: ["почав", "почала", "почало", "почали"]
      explanation: "Asking a woman, use feminine: ти почала."
    - sentence: "Я ___ проект. (female speaker)"
      answer: "закінчила"
      options: ["закінчив", "закінчила", "закінчило", "закінчили"]
      explanation: "A female speaker uses feminine: я закінчила."
    - sentence: "Ти ___ довго? (asking a man)"
      answer: "чекав"
      options: ["чекав", "чекала", "чекало", "чекали"]
      explanation: "Asking a man, use masculine: ти чекав."
- type: fill-in
  title: "What Did You Do Yesterday?"
  instruction: "Complete the sentences about yesterday using the correct past tense form."
  items:
    - sentence: "Вчора зранку я ___ каву. (male speaker)"
      answer: "пив"
      options: ["пив", "пила", "пити", "п'є"]
      explanation: "A male speaker talking about yesterday morning: я пив каву."
    - sentence: "Вчора ввечері вона ___ серіал."
      answer: "дивилася"
      options: ["дивився", "дивилася", "дивитися", "дивиться"]
      explanation: "Вона takes the feminine reflexive form: дивилася."
    - sentence: "Минулого тижня ми ___ в ресторані."
      answer: "їли"
      options: ["їсти", "їв", "їла", "їли"]
      explanation: "Ми (we) takes the plural ending -ли: їли."
    - sentence: "Вчора він ___ на роботу."
      answer: "ходив"
      options: ["ходив", "ходила", "ходити", "ходить"]
      explanation: "Він takes the masculine ending -в: ходив."
    - sentence: "Що ти ___ вчора? (asking a woman)"
      answer: "робила"
      options: ["робив", "робила", "робити", "робить"]
      explanation: "Asking a woman, so use feminine -ла: що ти робила?"
    - sentence: "Вчора ___ дуже цікаво!"
      answer: "було"
      options: ["був", "була", "було", "були"]
      explanation: "Impersonal sentences use neuter було: вчора було цікаво."
    - sentence: "Вчора я ___ лист. (male speaker)"
      answer: "писав"
      options: ["писати", "писав", "писала", "пише"]
      explanation: "A male speaker talking about yesterday uses masculine: писав."
    - sentence: "Вчора вона ___ пісню."
      answer: "співала"
      options: ["співати", "співав", "співала", "співає"]
      explanation: "Вона takes feminine: співала."
    - sentence: "Вчора ми ___ вдома."
      answer: "сиділи"
      options: ["сидіти", "сидів", "сиділа", "сиділи"]
      explanation: "Ми takes plural: сиділи."
    - sentence: "Що ти ___ вчора? (asking a man)"
      answer: "робив"
      options: ["робити", "робив", "робила", "робить"]
      explanation: "Asking a man, use masculine: робив."
    - sentence: "Вчора я ___ відпочивати. (female speaker)"
      answer: "хотіла"
      options: ["хотіти", "хотів", "хотіла", "хотіли"]
      explanation: "A female speaker uses feminine: хотіла."
    - sentence: "Вчора вони ___ правило."
      answer: "вивчали"
      options: ["вивчати", "вивчав", "вивчала", "вивчали"]
      explanation: "Вони takes plural: вивчали."
    - sentence: "Вчора він ___ вікно."
      answer: "відкрив"
      options: ["відкрити", "відкрив", "відкрила", "відкрили"]
      explanation: "Він takes masculine: відкрив."
    - sentence: "Вчора я ___ текст. (male speaker)"
      answer: "читав"
      options: ["читати", "читав", "читала", "читають"]
      explanation: "A male speaker uses masculine: читав."
    - sentence: "Вчора вона ___ правду."
      answer: "говорила"
      options: ["говорити", "говорив", "говорила", "говорили"]
      explanation: "Вона takes feminine: говорила."
    - sentence: "Вчора ми ___ роботу."
      answer: "почали"
      options: ["почати", "почав", "почала", "почали"]
      explanation: "Ми takes plural: почали."
    - sentence: "Що ти ___ вчора? (asking a woman)"
      answer: "думала"
      options: ["думати", "думав", "думала", "думають"]
      explanation: "Asking a woman, use feminine: думала."
    - sentence: "Вчора я ___ проект. (female speaker)"
      answer: "закінчила"
      options: ["закінчити", "закінчив", "закінчила", "закінчили"]
      explanation: "A female speaker uses feminine: закінчила."
    - sentence: "Вчора вони ___ швидко."
      answer: "бігли"
      options: ["бігти", "біг", "бігла", "бігли"]
      explanation: "Вони takes plural: бігли."
    - sentence: "Вчора він ___ питання."
      answer: "розумів"
      options: ["розуміти", "розумів", "розуміла", "розуміють"]
      explanation: "Він takes masculine: розумів."
    - sentence: "Вчора я ___ слова. (male speaker)"
      answer: "повторював"
      options: ["повторювати", "повторював", "повторювала", "повторюють"]
      explanation: "A male speaker uses masculine: повторював."
    - sentence: "Вчора вона ___ нове слово."
      answer: "знала"
      options: ["знати", "знала", "знав", "знають"]
      explanation: "Вона takes feminine: знала."
    - sentence: "Вчора ми ___ музику."
      answer: "слухали"
      options: ["слухати", "слухав", "слухала", "слухали"]
      explanation: "Ми takes plural: слухали."
    - sentence: "Вчора він ___ довго."
      answer: "спав"
      options: ["спати", "спав", "спала", "спить"]
      explanation: "Він takes masculine: спав."
    - sentence: "Вчора я ___ в магазин. (female speaker)"
      answer: "ходила"
      options: ["ходити", "ходив", "ходила", "ходить"]
      explanation: "A female speaker uses feminine: ходила."
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/yesterday-past-tense.yaml`

```yaml
items:
  - lemma: "вчора"
    translation: "yesterday"
    pos: "adverb"
    usage: "вчора зранку, вчора ввечері"
    notes: "High-frequency time adverb for past events"
  - lemma: "бути"
    translation: "to be"
    pos: "verb"
    aspect: "imperfective"
    usage: "був удома, була на роботі, було цікаво"
    notes: "Irregular past forms: був/була/було/були"
  - lemma: "робити"
    translation: "to do, to make"
    pos: "verb"
    aspect: "imperfective"
    usage: "робити каву, робити уроки, що ти робив?"
  - lemma: "їсти"
    translation: "to eat"
    pos: "verb"
    aspect: "imperfective"
    usage: "їв обід, вона їла яблуко"
    notes: "Irregular past: їв/їла/їло/їли (uses short stem)"
  - lemma: "пити"
    translation: "to drink"
    pos: "verb"
    aspect: "imperfective"
    usage: "пив воду, вона пила чай"
  - lemma: "читати"
    translation: "to read"
    pos: "verb"
    aspect: "imperfective"
    usage: "читав книгу, читала новини"
  - lemma: "дивитися"
    translation: "to watch"
    pos: "verb"
    aspect: "imperfective"
    usage: "дивився фільм, дивилася серіал"
    notes: "Reflexive -ся stays in past tense: дивився/дивилася"
  - lemma: "ходити"
    translation: "to go (regularly, there and back)"
    pos: "verb"
    aspect: "imperfective"
    usage: "ходила в магазин, ходив на роботу"
    notes: "Contrast with йти (one direction): ходив = went and came back"
  - lemma: "минулий"
    translation: "last, past"
    pos: "adjective"
    usage: "минулого тижня, минулого місяця"
    notes: "Used in genitive without preposition (no 'в'!)"
  - lemma: "раніше"
    translation: "earlier, before"
    pos: "adverb"
    usage: "раніше я працював тут"
  - lemma: "тиждень"
    translation: "week"
    pos: "noun"
    gender: "m"
    usage: "минулого тижня"
  - lemma: "місяць"
    translation: "month"
    pos: "noun"
    gender: "m"
    usage: "минулого місяця"
  - lemma: "спати"
    translation: "to sleep"
    pos: "verb"
    aspect: "imperfective"
    usage: "спав довго, вона спала"
  - lemma: "працювати"
    translation: "to work"
    pos: "verb"
    aspect: "imperfective"
    usage: "працював в офісі, вона працювала"
  - lemma: "йти"
    translation: "to go (on foot, one direction)"
    pos: "verb"
    aspect: "imperfective"
    usage: "ішов додому"
    notes: "Suppletive past forms: ішов/ішла/ішли"
  - lemma: "писати"
    translation: "to write"
    pos: "verb"
    aspect: "imperfective"
    usage: "писав листа, писала"
  - lemma: "зранку"
    translation: "in the morning"
    pos: "adverb"
    usage: "вчора зранку"
  - lemma: "ввечері"
    translation: "in the evening"
    pos: "adverb"
    usage: "вчора ввечері"
  - lemma: "удома"
    translation: "at home"
    pos: "adverb"
    usage: "був удома, працювала удома"
  - lemma: "надрукувати"
    translation: "to print, to publish"
    pos: "verb"
    aspect: "perfective"
    usage: "надрукував книгу"
    notes: "Used in cultural context: Іван Федоров надрукував Апостол (1574)"
```

---

## Friction Constraints (Past Review Findings — DO NOT reintroduce)

FRICTION CONSTRAINTS (from past build reviews — DO NOT repeat these errors):
- [GLOBAL] сес-тра is a VALID word division per Правопис 2019 §49. Do NOT mark it as an error. Phonetic syllabification (се-стра) and typographic word division (сес-тра) follow different rules — both are correct in their respective contexts.
- [GLOBAL] Ukrainian textbooks teach a hands-on-EARS test for voicing (закрий долонями вуха), NOT a hand-on-throat test. The hand-on-throat test is a valid phonetics technique but must NOT be attributed to Ukrainian textbooks. Source: Кравцова 2019, Grade 2, p.39.
- [GLOBAL] Do NOT invent Ukrainian words for minimal pairs. "Сір" is NOT a word meaning "grey" — the correct form is "сірий". Use verified minimal pairs only: кит/кіт, бити/біти, лис/ліс.

---

## Instructions

**CRITICAL: Fix ALL issues. Partial fixes are REJECTED. Count your fixes — if you missed one, go back.**

1. For EVERY issue in the Fix Plan AND audit failures, locate the exact text in the file contents above
2. Output a FIND/REPLACE pair with the exact text and the corrected version
3. Prioritize: **audit gate failures first**, then review issues
4. Only fix issues documented above — no silent extra changes
5. Maximum **15 FIND/REPLACE pairs** total

---

## Fix Rules

- Only fix issues documented in the Fix Plan or audit failures above
- You MAY add new activities or modify existing ones if the Fix Plan explicitly requests it
- Do NOT add new prose sections unless the Fix Plan explicitly requests it
- If nothing needs fixing, output an empty fix block
- FIND text must match the file contents EXACTLY (copy-paste from above)

---

## Output Format

You MUST use these exact delimiters:

```
===SECTION_FIX_START===
FILE: [filename]
FIND:
[exact text from the file — must match character-for-character]
REPLACE:
[corrected text]
---
FILE: [filename]
FIND:
[exact text]
REPLACE:
[corrected text]
---
[... more pairs, max 15 ...]
===SECTION_FIX_END===
```

If no fixes are needed:

```
===SECTION_FIX_START===
(No fixes needed — all issues resolved)
===SECTION_FIX_END===
```

After the fix block, output a friction report:

```
===FRICTION_START===
**Phase**: Gemini Review Fix
**Step**: {what you were doing}
**Friction Type**: NONE | TEXT_NOT_FOUND | ...
**Raw Error**: {actual issue or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if applicable, or "N/A"}
===FRICTION_END===
```

---

## Boundaries

- Do NOT write a review — that was already done
- Do NOT output ===REVIEW_START=== or ===FACTUAL_REVIEW_START=== blocks
- Do NOT use Edit tool or any other tool — you have NO tool access
- Output ONLY FIND/REPLACE pairs within the delimiters above
- Maximum 15 FIND/REPLACE pairs


============================================================
📎 Attached Data:
{"to_model": "gemini-3.1-pro-preview"}

🤖 Processing with Gemini (gemini-3.1-pro-preview) [sync, 15 min timeout]...
  [gemini] attempt 1/5, model=gemini-3.1-pro-preview, prompt=38942 chars: You are Gemini, participating in a collaboration with Claude. This is a message from Claude to you:  --- # Gemini Review Fix: Targeted Repair via FIND/REPLACE  > **You are an expert Ukrainian language...
```

  [watchdog] Output resumed after 139s stall
===SECTION_FIX_START===
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/yesterday-past-tense.md
FIND:
The infinitive ends in **-сти**, but the past tense uses the short stem! Examples in context:
REPLACE:
The infinitive ends in **-сти**, but the past tense uses the short stem **ї-**! Examples in context:
---
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/yesterday-past-tense.yaml
FIND:
- type: fill-in
  title: "Choose the Correct Gender Form"
  instruction: "The subject tells you the gender. Pick the past tense form that matches."
  items:
    - sentence: "Я ___ книгу. (female speaker)"
      answer: "читала"
      options: ["читав", "читала", "читало", "читали"]
      explanation: "A female speaker uses the feminine ending -ла: я читала."
    - sentence: "Я ___ удома. (male speaker)"
      answer: "був"
      options: ["був", "була", "було", "були"]
      explanation: "A male speaker uses the masculine form: я був."
    - sentence: "Ти ___ на роботі? (asking a woman)"
      answer: "була"
      options: ["був", "була", "було", "були"]
      explanation: "Asking a woman, so use feminine -ла: ти була."
    - sentence: "Я ___ каву. (male speaker)"
      answer: "пив"
      options: ["пив", "пила", "пило", "пили"]
      explanation: "A male speaker uses the masculine form: я пив."
    - sentence: "Ти ___ фільм? (asking a man)"
      answer: "дивився"
      options: ["дивився", "дивилася", "дивилося", "дивилися"]
      explanation: "Asking a man, so use the masculine form: ти дивився."
    - sentence: "Я ___ в офісі. (female speaker)"
      answer: "працювала"
      options: ["працював", "працювала", "працювало", "працювали"]
      explanation: "A female speaker uses the feminine ending -ла: я працювала."
    - sentence: "Ти ___ вчора? (asking a man)"
      answer: "спав"
      options: ["спав", "спала", "спало", "спали"]
      explanation: "Asking a man, so use masculine -в: ти спав."
    - sentence: "Я ___ в музей. (female speaker)"
      answer: "ходила"
      options: ["ходив", "ходила", "ходило", "ходили"]
      explanation: "A female speaker uses the feminine ending -ла: я ходила."
    - sentence: "Ти ___ листа? (asking a woman)"
      answer: "писала"
      options: ["писав", "писала", "писало", "писали"]
      explanation: "Asking a woman, so use feminine -ла: ти писала."
    - sentence: "Я ___ серіал. (male speaker)"
      answer: "дивився"
      options: ["дивився", "дивилася", "дивилося", "дивилися"]
      explanation: "A male speaker uses the masculine form: я дивився."
    - sentence: "Ти ___ довго? (asking a woman)"
      answer: "думала"
      options: ["думав", "думала", "думало", "думали"]
      explanation: "Asking a woman, use feminine: ти думала."
    - sentence: "Я ___ вікно. (female speaker)"
      answer: "відкрила"
      options: ["відкрив", "відкрила", "відкрило", "відкрили"]
      explanation: "A female speaker uses feminine: я відкрила."
    - sentence: "Ти ___ вдома? (asking a man)"
      answer: "сидів"
      options: ["сидів", "сиділа", "сиділо", "сиділи"]
      explanation: "Asking a man, use masculine: ти сидів."
    - sentence: "Я ___ питання. (male speaker)"
      answer: "розумів"
      options: ["розумів", "розуміла", "розуміло", "розуміли"]
      explanation: "A male speaker uses masculine: я розумів."
    - sentence: "Ти ___ пісню? (asking a woman)"
      answer: "співала"
      options: ["співав", "співала", "співало", "співали"]
      explanation: "Asking a woman, use feminine: ти співала."
    - sentence: "Я ___ швидко. (female speaker)"
      answer: "бігла"
      options: ["біг", "бігла", "бігло", "бігли"]
      explanation: "A female speaker uses feminine: я бігла."
    - sentence: "Ти ___ слова? (asking a man)"
      answer: "повторював"
      options: ["повторював", "повторювала", "повторювало", "повторювали"]
      explanation: "Asking a man, use masculine: ти повторював."
    - sentence: "Я ___ відпочивати. (male speaker)"
      answer: "хотів"
      options: ["хотів", "хотіла", "хотіло", "хотіли"]
      explanation: "A male speaker uses masculine: я хотів."
    - sentence: "Ти ___ правило? (asking a woman)"
      answer: "вивчала"
      options: ["вивчав", "вивчала", "вивчало", "вивчали"]
      explanation: "Asking a woman, use feminine: ти вивчала."
    - sentence: "Я ___ текст. (female speaker)"
      answer: "знала"
      options: ["знав", "знала", "знало", "знали"]
      explanation: "A female speaker uses feminine: я знала."
    - sentence: "Ти ___ лист? (asking a man)"
      answer: "відправив"
      options: ["відправив", "відправила", "відправило", "відправили"]
      explanation: "Asking a man, use masculine: ти відправив."
    - sentence: "Я ___ правду. (male speaker)"
      answer: "говорив"
      options: ["говорив", "говорила", "говорило", "говорили"]
      explanation: "A male speaker uses masculine: я говорив."
    - sentence: "Ти ___ роботу? (asking a woman)"
      answer: "почала"
      options: ["почав", "почала", "почало", "почали"]
      explanation: "Asking a woman, use feminine: ти почала."
    - sentence: "Я ___ проект. (female speaker)"
      answer: "закінчила"
      options: ["закінчив", "закінчила", "закінчило", "закінчили"]
      explanation: "A female speaker uses feminine: я закінчила."
    - sentence: "Ти ___ довго? (asking a man)"
      answer: "чекав"
      options: ["чекав", "чекала", "чекало", "чекали"]
      explanation: "Asking a man, use masculine: ти чекав."
REPLACE:
- type: fill-in
  title: "Choose the Correct Gender Form"
  instruction: "The subject tells you the gender. Pick the past tense form that matches."
  items:
    - sentence: "Я ___ книгу. (каже жінка)"
      answer: "читала"
      options: ["читав", "читала", "читало", "читали"]
      explanation: "A female speaker uses the feminine ending -ла: я читала."
    - sentence: "Я ___ удома. (каже чоловік)"
      answer: "був"
      options: ["був", "була", "було", "були"]
      explanation: "A male speaker uses the masculine form: я був."
    - sentence: "Ти ___ на роботі? (запитуємо жінку)"
      answer: "була"
      options: ["був", "була", "було", "були"]
      explanation: "Asking a woman, so use feminine -ла: ти була."
    - sentence: "Я ___ каву. (каже чоловік)"
      answer: "пив"
      options: ["пив", "пила", "пило", "пили"]
      explanation: "A male speaker uses the masculine form: я пив."
    - sentence: "Ти ___ фільм? (запитуємо чоловіка)"
      answer: "дивився"
      options: ["дивився", "дивилася", "дивилося", "дивилися"]
      explanation: "Asking a man, so use the masculine form: ти дивився."
    - sentence: "Я ___ в офісі. (каже жінка)"
      answer: "працювала"
      options: ["працював", "працювала", "працювало", "працювали"]
      explanation: "A female speaker uses the feminine ending -ла: я працювала."
    - sentence: "Ти ___ вчора? (запитуємо чоловіка)"
      answer: "спав"
      options: ["спав", "спала", "спало", "спали"]
      explanation: "Asking a man, so use masculine -в: ти спав."
    - sentence: "Я ___ в музей. (каже жінка)"
      answer: "ходила"
      options: ["ходив", "ходила", "ходило", "ходили"]
      explanation: "A female speaker uses the feminine ending -ла: я ходила."
    - sentence: "Ти ___ листа? (запитуємо жінку)"
      answer: "писала"
      options: ["писав", "писала", "писало", "писали"]
      explanation: "Asking a woman, so use feminine -ла: ти писала."
    - sentence: "Я ___ серіал. (каже чоловік)"
      answer: "дивився"
      options: ["дивився", "дивилася", "дивилося", "дивилися"]
      explanation: "A male speaker uses the masculine form: я дивився."
    - sentence: "Ти ___ довго? (запитуємо жінку)"
      answer: "думала"
      options: ["думав", "думала", "думало", "думали"]
      explanation: "Asking a woman, use feminine: ти думала."
    - sentence: "Я ___ вікно. (каже жінка)"
      answer: "відкрила"
      options: ["відкрив", "відкрила", "відкрило", "відкрили"]
      explanation: "A female speaker uses feminine: я відкрила."
    - sentence: "Ти ___ вдома? (запитуємо чоловіка)"
      answer: "сидів"
      options: ["сидів", "сиділа", "сиділо", "сиділи"]
      explanation: "Asking a man, use masculine: ти сидів."
    - sentence: "Я ___ питання. (каже чоловік)"
      answer: "розумів"
      options: ["розумів", "розуміла", "розуміло", "розуміли"]
      explanation: "A male speaker uses masculine: я розумів."
    - sentence: "Ти ___ пісню? (запитуємо жінку)"
      answer: "співала"
      options: ["співав", "співала", "співало", "співали"]
      explanation: "Asking a woman, use feminine: ти співала."
    - sentence: "Я ___ швидко. (каже жінка)"
      answer: "бігла"
      options: ["біг", "бігла", "бігло", "бігли"]
      explanation: "A female speaker uses feminine: я бігла."
    - sentence: "Ти ___ слова? (запитуємо чоловіка)"
      answer: "повторював"
      options: ["повторював", "повторювала", "повторювало", "повторювали"]
      explanation: "Asking a man, use masculine: ти повторював."
    - sentence: "Я ___ відпочивати. (каже чоловік)"
      answer: "хотів"
      options: ["хотів", "хотіла", "хотіло", "хотіли"]
      explanation: "A male speaker uses masculine: я хотів."
    - sentence: "Ти ___ правило? (запитуємо жінку)"
      answer: "вивчала"
      options: ["вивчав", "вивчала", "вивчало", "вивчали"]
      explanation: "Asking a woman, use feminine: ти вивчала."
    - sentence: "Я ___ текст. (каже жінка)"
      answer: "знала"
      options: ["знав", "знала", "знало", "знали"]
      explanation: "A female speaker uses feminine: я знала."
    - sentence: "Ти ___ лист? (запитуємо чоловіка)"
      answer: "відправив"
      options: ["відправив", "відправила", "відправило", "відправили"]
      explanation: "Asking a man, use masculine: ти відправив."
    - sentence: "Я ___ правду. (каже чоловік)"
      answer: "говорив"
      options: ["говорив", "говорила", "говорило", "говорили"]
      explanation: "A male speaker uses masculine: я говорив."
    - sentence: "Ти ___ роботу? (запитуємо жінку)"
      answer: "почала"
      options: ["почав", "почала", "почало", "почали"]
      explanation: "Asking a woman, use feminine: ти почала."
    - sentence: "Я ___ проект. (каже жінка)"
      answer: "закінчила"
      options: ["закінчив", "закінчила", "закінчило", "закінчили"]
      explanation: "A female speaker uses feminine: я закінчила."
    - sentence: "Ти ___ довго? (запитуємо чоловіка)"
      answer: "чекав"
      options: ["чекав", "чекала", "чекало", "чекали"]
      explanation: "Asking a man, use masculine: ти чекав."
---
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/yesterday-past-tense.yaml
FIND:
- type: fill-in
  title: "What Did You Do Yesterday?"
  instruction: "Complete the sentences about yesterday using the correct past tense form."
  items:
    - sentence: "Вчора зранку я ___ каву. (male speaker)"
      answer: "пив"
      options: ["пив", "пила", "пити", "п'є"]
      explanation: "A male speaker talking about yesterday morning: я пив каву."
    - sentence: "Вчора ввечері вона ___ серіал."
      answer: "дивилася"
      options: ["дивився", "дивилася", "дивитися", "дивиться"]
      explanation: "Вона takes the feminine reflexive form: дивилася."
    - sentence: "Минулого тижня ми ___ в ресторані."
      answer: "їли"
      options: ["їсти", "їв", "їла", "їли"]
      explanation: "Ми (we) takes the plural ending -ли: їли."
    - sentence: "Вчора він ___ на роботу."
      answer: "ходив"
      options: ["ходив", "ходила", "ходити", "ходить"]
      explanation: "Він takes the masculine ending -в: ходив."
    - sentence: "Що ти ___ вчора? (asking a woman)"
      answer: "робила"
      options: ["робив", "робила", "робити", "робить"]
      explanation: "Asking a woman, so use feminine -ла: що ти робила?"
    - sentence: "Вчора ___ дуже цікаво!"
      answer: "було"
      options: ["був", "була", "було", "були"]
      explanation: "Impersonal sentences use neuter було: вчора було цікаво."
    - sentence: "Вчора я ___ лист. (male speaker)"
      answer: "писав"
      options: ["писати", "писав", "писала", "пише"]
      explanation: "A male speaker talking about yesterday uses masculine: писав."
    - sentence: "Вчора вона ___ пісню."
      answer: "співала"
      options: ["співати", "співав", "співала", "співає"]
      explanation: "Вона takes feminine: співала."
    - sentence: "Вчора ми ___ вдома."
      answer: "сиділи"
      options: ["сидіти", "сидів", "сиділа", "сиділи"]
      explanation: "Ми takes plural: сиділи."
    - sentence: "Що ти ___ вчора? (asking a man)"
      answer: "робив"
      options: ["робити", "робив", "робила", "робить"]
      explanation: "Asking a man, use masculine: робив."
    - sentence: "Вчора я ___ відпочивати. (female speaker)"
      answer: "хотіла"
      options: ["хотіти", "хотів", "хотіла", "хотіли"]
      explanation: "A female speaker uses feminine: хотіла."
    - sentence: "Вчора вони ___ правило."
      answer: "вивчали"
      options: ["вивчати", "вивчав", "вивчала", "вивчали"]
      explanation: "Вони takes plural: вивчали."
    - sentence: "Вчора він ___ вікно."
      answer: "відкрив"
      options: ["відкрити", "відкрив", "відкрила", "відкрили"]
      explanation: "Він takes masculine: відкрив."
    - sentence: "Вчора я ___ текст. (male speaker)"
      answer: "читав"
      options: ["читати", "читав", "читала", "читають"]
      explanation: "A male speaker uses masculine: читав."
    - sentence: "Вчора вона ___ правду."
      answer: "говорила"
      options: ["говорити", "говорив", "говорила", "говорили"]
      explanation: "Вона takes feminine: говорила."
    - sentence: "Вчора ми ___ роботу."
      answer: "почали"
      options: ["почати", "почав", "почала", "почали"]
      explanation: "Ми takes plural: почали."
    - sentence: "Що ти ___ вчора? (asking a woman)"
      answer: "думала"
      options: ["думати", "думав", "думала", "думають"]
      explanation: "Asking a woman, use feminine: думала."
    - sentence: "Вчора я ___ проект. (female speaker)"
      answer: "закінчила"
      options: ["закінчити", "закінчив", "закінчила", "закінчили"]
      explanation: "A female speaker uses feminine: закінчила."
    - sentence: "Вчора вони ___ швидко."
      answer: "бігли"
      options: ["бігти", "біг", "бігла", "бігли"]
      explanation: "Вони takes plural: бігли."
    - sentence: "Вчора він ___ питання."
      answer: "розумів"
      options: ["розуміти", "розумів", "розуміла", "розуміють"]
      explanation: "Він takes masculine: розумів."
    - sentence: "Вчора я ___ слова. (male speaker)"
      answer: "повторював"
      options: ["повторювати", "повторював", "повторювала", "повторюють"]
      explanation: "A male speaker uses masculine: повторював."
    - sentence: "Вчора вона ___ нове слово."
      answer: "знала"
      options: ["знати", "знала", "знав", "знають"]
      explanation: "Вона takes feminine: знала."
    - sentence: "Вчора ми ___ музику."
      answer: "слухали"
      options: ["слухати", "слухав", "слухала", "слухали"]
      explanation: "Ми takes plural: слухали."
    - sentence: "Вчора він ___ довго."
      answer: "спав"
      options: ["спати", "спав", "спала", "спить"]
      explanation: "Він takes masculine: спав."
    - sentence: "Вчора я ___ в магазин. (female speaker)"
      answer: "ходила"
      options: ["ходити", "ходив", "ходила", "ходить"]
      explanation: "A female speaker uses feminine: ходила."
REPLACE:
- type: fill-in
  title: "What Did You Do Yesterday?"
  instruction: "Complete the sentences about yesterday using the correct past tense form."
  items:
    - sentence: "Вчора зранку я ___ каву. (каже чоловік)"
      answer: "пив"
      options: ["пив", "пила", "пити", "п'є"]
      explanation: "A male speaker talking about yesterday morning: я пив каву."
    - sentence: "Вчора ввечері вона ___ серіал."
      answer: "дивилася"
      options: ["дивився", "дивилася", "дивитися", "дивиться"]
      explanation: "Вона takes the feminine reflexive form: дивилася."
    - sentence: "Минулого тижня ми ___ в ресторані."
      answer: "їли"
      options: ["їсти", "їв", "їла", "їли"]
      explanation: "Ми (we) takes the plural ending -ли: їли."
    - sentence: "Вчора він ___ на роботу."
      answer: "ходив"
      options: ["ходив", "ходила", "ходити", "ходить"]
      explanation: "Він takes the masculine ending -в: ходив."
    - sentence: "Що ти ___ вчора? (запитуємо жінку)"
      answer: "робила"
      options: ["робив", "робила", "робити", "робить"]
      explanation: "Asking a woman, so use feminine -ла: що ти робила?"
    - sentence: "Вчора ___ дуже цікаво!"
      answer: "було"
      options: ["був", "була", "було", "були"]
      explanation: "Impersonal sentences use neuter було: вчора було цікаво."
    - sentence: "Вчора я ___ лист. (каже чоловік)"
      answer: "писав"
      options: ["писати", "писав", "писала", "пише"]
      explanation: "A male speaker talking about yesterday uses masculine: писав."
    - sentence: "Вчора вона ___ пісню."
      answer: "співала"
      options: ["співати", "співав", "співала", "співає"]
      explanation: "Вона takes feminine: співала."
    - sentence: "Вчора ми ___ вдома."
      answer: "сиділи"
      options: ["сидіти", "сидів", "сиділа", "сиділи"]
      explanation: "Ми takes plural: сиділи."
    - sentence: "Що ти ___ вчора? (запитуємо чоловіка)"
      answer: "робив"
      options: ["робити", "робив", "робила", "робить"]
      explanation: "Asking a man, use masculine: робив."
    - sentence: "Вчора я ___ відпочивати. (каже жінка)"
      answer: "хотіла"
      options: ["хотіти", "хотів", "хотіла", "хотіли"]
      explanation: "A female speaker uses feminine: хотіла."
    - sentence: "Вчора вони ___ правило."
      answer: "вивчали"
      options: ["вивчати", "вивчав", "вивчала", "вивчали"]
      explanation: "Вони takes plural: вивчали."
    - sentence: "Вчора він ___ вікно."
      answer: "відкрив"
      options: ["відкрити", "відкрив", "відкрила", "відкрили"]
      explanation: "Він takes masculine: відкрив."
    - sentence: "Вчора я ___ текст. (каже чоловік)"
      answer: "читав"
      options: ["читати", "читав", "читала", "читають"]
      explanation: "A male speaker uses masculine: читав."
    - sentence: "Вчора вона ___ правду."
      answer: "говорила"
      options: ["говорити", "говорив", "говорила", "говорили"]
      explanation: "Вона takes feminine: говорила."
    - sentence: "Вчора ми ___ роботу."
      answer: "почали"
      options: ["почати", "почав", "почала", "почали"]
      explanation: "Ми takes plural: почали."
    - sentence: "Що ти ___ вчора? (запитуємо жінку)"
      answer: "думала"
      options: ["думати", "думав", "думала", "думають"]
      explanation: "Asking a woman, use feminine: думала."
    - sentence: "Вчора я ___ проект. (каже жінка)"
      answer: "закінчила"
      options: ["закінчити", "закінчив", "закінчила", "закінчили"]
      explanation: "A female speaker uses feminine: закінчила."
    - sentence: "Вчора вони ___ швидко."
      answer: "бігли"
      options: ["бігти", "біг", "бігла", "бігли"]
      explanation: "Вони takes plural: бігли."
    - sentence: "Вчора він ___ питання."
      answer: "розумів"
      options: ["розуміти", "розумів", "розуміла", "розуміють"]
      explanation: "Він takes masculine: розумів."
    - sentence: "Вчора я ___ слова. (каже чоловік)"
      answer: "повторював"
      options: ["повторювати", "повторював", "повторювала", "повторюють"]
      explanation: "A male speaker uses masculine: повторював."
    - sentence: "Вчора вона ___ нове слово."
      answer: "знала"
      options: ["знати", "знала", "знав", "знають"]
      explanation: "Вона takes feminine: знала."
    - sentence: "Вчора ми ___ музику."
      answer: "слухали"
      options: ["слухати", "слухав", "слухала", "слухали"]
      explanation: "Ми takes plural: слухали."
    - sentence: "Вчора він ___ довго."
      answer: "спав"
      options: ["спати", "спав", "спала", "спить"]
      explanation: "Він takes masculine: спав."
    - sentence: "Вчора я ___ в магазин. (каже жінка)"
      answer: "ходила"
      options: ["ходити", "ходив", "ходила", "ходить"]
      explanation: "A female speaker uses feminine: ходила."
===SECTION_FIX_END===

===FRICTION_START===
**Phase**: Gemini Review Fix
**Step**: Applying FIND/REPLACE fixes from review plan.
**Friction Type**: TEXT_NOT_FOUND
**Raw Error**: Almost all Review Findings and Audit Failures were for text that NO LONGER EXISTS in the provided markdown/yaml files. The provided text has already resolved the "Воно" calque, the "у офісі" euphony violation, the inaccurate morphological breakdown, and the missing activity items. The VESUM word validation errors referenced words (like ЗУНР, Захарійчук, їстив) that did not exist in the source files.
**Self-Correction**: I only applied fixes for issues that were actually present in the text: adding the missing "ї-" stem to the grammar explanation and translating the English metalanguage hints in activities 2 and 3 to clear the deterministic A2+ audit error.
**Proposed Tooling Fix**: The review system seems to be passing stale audit logs or old module snapshots to the targeted fix phase, leading to mismatches between requested fixes and current file contents. 
===FRICTION_END===
```


────────────────────────────────────────
✅ Gemini finished (21352 chars)
✅ Message sent to Claude (ID: 26516)
✓ Message 26516 acknowledged
   Auto-acknowledged reply #26516 (stdout delivery — no inbox accumulation)
   ℹ️  No issue number in task_id 'yesterday-past-tense-review-fix-2' — skipping GH posting (review saved to orchestration/)
✓ Message 26514 acknowledged
