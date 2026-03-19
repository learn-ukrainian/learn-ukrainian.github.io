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



**NOTE: 4 inline fix(es) from the review have ALREADY been applied to the files. Do NOT re-apply those fixes. Read the CURRENT file contents carefully — they reflect the post-fix state. Only fix issues that are still present in the current files.**

## Plan Adherence Issues (Deterministic — MUST FIX)

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥30 items
  - Actual: Activity has 8 items
  - Fix: Add 22 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥30 items
  - Actual: Activity has 8 items
  - Fix: Add 22 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥20 items
  - Actual: Activity has 8 items
  - Fix: Add 12 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥20 items
  - Actual: Activity has 8 items
  - Fix: Add 12 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:match-up`
  - Expected: Plan requires ≥18 items
  - Actual: Activity has 9 items
  - Fix: Add 9 more items to 'match-up' activity


---

## Review Findings (targeted fix required)

**CONSTRAINTS:**
- Fix ONLY the issues listed below
- Do NOT rewrite surrounding text
- Preserve word count and structure
- Only modify these sections: Entire module, Entire module — all sections, Line 170, Section "Культурний аспект та підсумок (Cultural Insight and Summary)", Lines 153, 156, 160, 162 — Section "Практика (Practice)"

### Finding 1: Missing Full Ukrainian Proverb (HIGH — Plan Adherence)
**Location**: Line 170, Section "Культурний аспект та підсумок (Cultural Insight and Summary)"
**Problem**: The plan requires the proverb "Птицю пізнати по пір'ю, а людину по мові" to be presented in full Ukrainian. The content lists individual words in nominative case and gives only an English translation. The learner never encounters the actual proverb. The nominative forms (Птиця, пір'я, людина, мова) misrepresent the proverb, which uses accusative and other cases (Птицю, пір'ю, людину, мові).
**Required Fix**: Replace the passage to include the full Ukrainian proverb with bolded text, followed by a word-by-word gloss and the English translation.
**Severity**: HIGH

### Finding 2: Scope Creep — Non-First-Conjugation Verbs in Dialogue (MEDIUM)
**Location**: Lines 153, 156, 160, 162 — Section "Практика (Practice)"
**Problem**: "робити" is Second Conjugation (робиш, роблять — not the -ю/-єш/-є pattern taught), and "їхати" is irregular (їду — not the standard ending). A learner may try to apply the First Conjugation pattern to these verbs. No note or caveat is provided.
**Required Fix**: Add a brief `[!tip]` after the dialogue noting that "робити" and "їхати" follow different patterns that will be taught in the next module (The Living Verb II).
**Severity**: HIGH

### Finding 3: Low Immersion (MEDIUM — Below Audit Target)
**Location**: Entire module — all sections
**Problem**: Immersion is 12.1% vs the 15-25% target for this module position. The module is heavily English-dominant, particularly in sections "Вступ (Introduction)" (lines 3-9: ~250 words of pure English) and "Культурний аспект та підсумок (Cultural Insight and Summary)" (lines 168-184: mostly English).
**Required Fix**: Add a short Ukrainian Reading Practice block after the Презентація section with 4-5 simple sentences using taught verbs, with translations. Convert some English explanation in the summary section to Ukrainian sentences with glosses.
**Severity**: HIGH

### Finding 4: Missing Video Embeds (LOW — Richness Gap)
**Location**: Entire module
**Problem**: Richness audit shows video_embeds: 0/2. No pronunciation or conjugation demonstration videos are embedded.
**Required Fix**: Add 2 video embed placeholders — one for conjugation pattern demonstration in "Презентація (Presentation)", one for pronunciation of key verbs in "Практика (Practice)".
**Severity**: HIGH

---

## Critical Issues Found

### Issue 1: Missing Full Ukrainian Proverb (HIGH — Plan Adherence)
- **Location**: Line 170, Section "Культурний аспект та підсумок (Cultural Insight and Summary)"
- **Original**: 「There is a profound and wonderful Ukrainian proverb about these words: **Птиця** (bird), **пір'я** (feathers), **людина** (person), and **мова** (speech). The proverb translates to "A bird is known by its feathers, a person by their speech."」
- **Problem**: The plan requires the proverb "Птицю пізнати по пір'ю, а людину по мові" to be presented in full Ukrainian. The content lists individual words in nominative case and gives only an English translation. The learner never encounters the actual proverb. The nominative forms (Птиця, пір'я, людина, мова) misrepresent the proverb, which uses accusative and other cases (Птицю, пір'ю, людину, мові).
- **Fix**: Replace the passage to include the full Ukrainian proverb with bolded text, followed by a word-by-word gloss and the English translation.

### Issue 2: Scope Creep — Non-First-Conjugation Verbs in Dialogue (MEDIUM)
- **Location**: Lines 153, 156, 160, 162 — Section "Практика (Practice)"
- **Original**: 「Привіт, Іване! Що ти робиш зараз? Ти працюєш?」 and 「Ви студенти. Ви багато працюєте. А ваші друзі? Що роблять вони?」 and 「Я зараз чекаю на автобус. Я їду в магазин.」
- **Problem**: "робити" is Second Conjugation (робиш, роблять — not the -ю/-єш/-є pattern taught), and "їхати" is irregular (їду — not the standard ending). A learner may try to apply the First Conjugation pattern to these verbs. No note or caveat is provided.
- **Fix**: Add a brief `[!tip]` after the dialogue noting that "робити" and "їхати" follow different patterns that will be taught in the next module (The Living Verb II).

### Issue 3: Low Immersion (MEDIUM — Below Audit Target)
- **Location**: Entire module — all sections
- **Problem**: Immersion is 12.1% vs the 15-25% target for this module position. The module is heavily English-dominant, particularly in sections "Вступ (Introduction)" (lines 3-9: ~250 words of pure English) and "Культурний аспект та підсумок (Cultural Insight and Summary)" (lines 168-184: mostly English).
- **Fix**: Add a short Ukrainian Reading Practice block after the Презентація section with 4-5 simple sentences using taught verbs, with translations. Convert some English explanation in the summary section to Ukrainian sentences with glosses.

### Issue 4: Missing Video Embeds (LOW — Richness Gap)
- **Location**: Entire module
- **Problem**: Richness audit shows video_embeds: 0/2. No pronunciation or conjugation demonstration videos are embedded.
- **Fix**: Add 2 video embed placeholders — one for conjugation pattern demonstration in "Презентація (Presentation)", one for pronunciation of key verbs in "Практика (Practice)".

---

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 170 | Individual nominative words: Птиця, пір'я, людина, мова | Full proverb: 「Птицю пізнати по пір'ю, а людину по мові」 | Missing content |
| 153, 160 | робиш, роблять (no scope note) | Add note: these are II conjugation, covered later | Scope |
| 162 | їду (no scope note) | Add note: їхати is irregular, covered later | Scope |

---

## Fix Plan to Reach 9/10 (REQUIRED — score is 8.3)

### Language: 8/10 → 9/10
**What to fix:**
1. Line 170: Replace nominative word list with full Ukrainian proverb: **Птицю пізнати по пір'ю, а людину по мові** — bolded, with word-by-word gloss. This fulfills the plan requirement and gives the learner a real Ukrainian cultural artifact.

**Expected score after fix:** 9/10

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. After line 164: Add a `[!tip]` noting that "робити" and "їхати" follow different patterns (Coming in The Living Verb II). This prevents confusion without requiring a full explanation.
2. Between sections "Презентація" and "Практика": Add a Ukrainian Reading Practice block (4-5 sentences using taught verbs only) to boost immersion from 12.1% toward 15%.

**Expected score after fix:** 9/10

### Pedagogy: 8/10 → 9/10
**What to fix:**
1. Address -яти gap: Add one -яти example verb (e.g., гуляти) to the Презентація paradigm area, or add a brief note that -яти verbs follow the same pattern, to honor the subtitle's promise.

**Expected score after fix:** 9/10

### Activities: 8/10 → 9/10
**What to fix:**
1. No critical fixes needed — the 7 activity types provide good variety. The fill-in count deviation was acknowledged by the builder. Items are all correct.

**Expected score after fix:** 8/10 (no change — acceptable)

### Projected Overall After Fixes
```
(9×1.5 + 9×1.1 + 9×1.2 + 8×1.3 + 9×1.3 + 8×1.0 + 9×1.5) / 8.9
= (13.5 + 9.9 + 10.8 + 10.4 + 11.7 + 8.0 + 13.5) / 8.9
= 77.8 / 8.9
= 8.74/10
```

---

## Audit Failures (from automated re-audit)

```
> Conjugate First Conjugation Verbs: 8 items (min 6)
✨ Prose quality violations found: 1
❌ [GLOSSARY_LIST_IN_PROSE] Glossary-style list (5 items) in narrative prose starting: '**Я читаю книгу.** — I read a book.' — vocab tables belong in vocabulary YAML
--- STRICT GATES (Level A1) ---
Pedagogy     ❌ 2 violations
📚 PEDAGOGICAL VIOLATIONS FOUND:
📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
→ 2 violations (minor)
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/the-living-verb-i-audit.log for details)
⚠️  RAG verification found unverified words (see audit report)
--- VESUM WORD VERIFICATION FAILURES ---
These words were NOT found in the VESUM morphological dictionary.
Check if they are valid Ukrainian forms. Fix misspellings or Russianisms.
  ❌ `Анна` (source: prose)
  ❌ `Анно` (source: prose)
  ❌ `ати` (source: prose)
  ❌ `Міні-розповідь` (source: prose)
  ❌ `працюваю` (source: prose)
  ❌ `ю` (source: prose)
  ❌ `юва` (source: prose)
  ❌ `ювати` (source: prose)
  ❌ `ють` (source: prose)
  ❌ `яти` (source: prose)
  ❌ `ємо` (source: prose)
  ❌ `єте` (source: prose)
  ❌ `єш` (source: prose)
  ❌ `Іване` (source: prose)
```

---

## File Contents (for reference)

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-living-verb-i.md`

```markdown
## Вступ (Introduction)

So far on your Ukrainian journey, you have done a fantastic job mapping out your world. You have learned how to name the objects around you, describe what they look like, and state simple facts using "this is" structures. But a language isn't just a static painting; it is a vibrant, moving picture. Today, we are taking a massive leap forward. We are shifting our focus from static descriptions to dynamic action. It is time to transition from simply pointing and saying "this is a book" to confidently stating "I read a book."

This brings us to the beating heart of Ukrainian communication: the verb. Verbs are the engines of your sentences. They give life to your thoughts and allow you to interact with the world in real time. Without them, we can only point at things or describe states of being. With them, we can tell stories, share our daily experiences, and truly connect with people. Today, we are going to unlock the most common action words in the language.

To appreciate the importance of our first verbs, let's step back in time. In 1574, Ivan Fedorov printed the *Apostol* in Lviv, which became the very first printed book in Ukraine. This momentous historical event established a deep-rooted tradition of literacy, education, and learning across the country. The action of reading—**читати**—has been central to Ukrainian culture for centuries. When you learn to say "I read" in Ukrainian, you are participating in a tradition that stretches back hundreds of years. The word **читати** literally helped build Ukrainian literate culture, and today, it will help build your foundational conversational skills.

Our focus now turns to the present tense of what we call the First Conjugation. In alignment with the Ukrainian State Standard, this is your primary introduction to the indicative mood. This simply means a group of verbs that follow a very specific, highly predictable pattern when they change to match the person doing the action (like "I read", "you read", "we read"). We will start with high-frequency, everyday examples. You will learn exactly how to use **читати** (to read) and **працювати** (to work) to talk about what you are actively doing right now. By the end of this module, you will be able to describe your daily activities and finally start bringing your Ukrainian sentences to life. Let's get started!

## Презентація (Presentation)

Let's look at how Ukrainian verbs actually work in practice. Unlike English, where the verb often stays exactly the same ("I read, you read, we read") and you must rely on a pronoun to know who is acting, Ukrainian verbs change their endings to show exactly who is doing the action. This changing of endings is called conjugation.

Today, we are mastering the First Conjugation. These verbs typically end in **-ати** or **-яти** in their dictionary form (the infinitive, like "to read"). The magic happens when we remove that **-ти** ending to find the verb's stem, and then add a new ending that acts like a built-in pronoun.

Let's take our historical verb, **читати** (to read). If we drop the **-ти**, we are left with the stem: **чита-**. Now, let's look at the pattern of endings we add to this stem.

| Person | Ending | Ukrainian | English |
| :--- | :--- | :--- | :--- |
| Я (I) | **-ю** | **Я читаю** | I read |
| Ти (You, informal) | **-єш** | **Ти читаєш** | You read |
| Він / Вона / Воно | **-є** | **Він читає** | He/She/It reads |
| Ми (We) | **-ємо** | **Ми читаємо** | We read |
| Ви (You, formal/plural) | **-єте** | **Ви читаєте** | You read |
| Вони (They) | **-ють** | **Вони читають** | They read |

Notice how the ending clearly points to the person? Because the ending itself tells us who is acting, Ukrainian has a fantastic "pro-drop" feature. This means the pronouns (I, you, he, we) are entirely optional! You don't need to explicitly say **Я читаю**; you can simply say **Читаю**. The **-ю** ending already means "I". While English requires the pronoun, dropping it in Ukrainian sounds incredibly natural and fluent.

Let's talk about what these present tense verbs actually mean. In Ukrainian, present tense verbs describe an ongoing process or a habitual action. This concept is known as the Imperfective Aspect. When you say **Читаю**, it can mean "I am reading right now" (the ongoing process) or "I read regularly" (the habit). You don't need a complex, separate grammar structure for "I am reading"; the simple present tense beautifully covers both scenarios!

This pattern is a universal key. It applies to hundreds of verbs. Let's apply it to another essential State Standard example: **знати** (to know).

| Ukrainian | English |
| :--- | :--- |
| **я знаю** | I know |
| **ти знаєш** | you know |
| **він/вона/воно знає** | he/she/it knows |
| **ми знаємо** | we know |
| **ви знаєте** | you know |
| **вони знають** | they know |

See? The exact same endings! You just attach **-ю, -єш, -є, -ємо, -єте, -ють** to the stem.

Now, let's look at a slight visual variation. Some very common verbs, like **працювати** (to work), look a bit different. Notice the **-ювати** ending. When we conjugate these, the **-юва-** part contracts into a simple **-ю-** before we add the ending for "I".

| Ukrainian | English |
| :--- | :--- |
| **Я працюю** | I work |
| **Ти працюєш** | You work |
| **Він працює** | He works |
| **Ми працюємо** | We work |
| **Ви працюєте** | You work |
| **Вони працюють** | They work |

Do not fall into the trap of saying ~~працюваю~~! Always remember to compress the stem. The endings themselves, however, remain completely regular. This predictable system will allow you to quickly expand your vocabulary.

### Everyday Action Phrases

Let's apply these verbs to describe a typical daily routine. You can use these phrases to narrate your own life right now. Here are high-frequency combinations you can start using immediately:

| Action Phrase | Meaning |
| :--- | :--- |
| **читати новини** | to read the news |
| **читати вголос** | to read aloud |
| **гарно писати** | to write well |
| **знати правду** | to know the truth |
| **не знати** | to not know |
| **працювати вдома** | to work at home |
| **працювати багато** | to work a lot |
| **слухати** | to listen |
| **слухати уважно** | to listen carefully |
| **питати про це** | to ask about this |
| **грати в ігри** | to play games |
| **добре грати** | to play well |
| **чекати на автобус** | to wait for the bus |
| **чекати на відповідь** | to wait for an answer |
| **думати про це** | to think about this |
| **думати багато** | to think a lot |
| **розуміти все** | to understand everything |
| **вивчати текст** | to study the text |
| **вивчати слова** | to study words |
| **відпочивати влітку** | to rest in summer |

Notice how you can simply drop the **Я** after establishing who is acting. This is how Ukrainians naturally speak! Practice narrating your own actions as you do them. As you send a text, think: **пишу повідомлення**. While putting on headphones, think: **я слухаю**. Once you sit on the sofa, think: **відпочиваю**.

## Практика (Practice)

### Читання (Reading Practice)

Before we drill, let's read a few sentences using what you just learned. Try reading the Ukrainian first, then check the English:

**Я читаю книгу.** — I read a book.
**Ти знаєш багато.** — You know a lot.
**Він працює вдома.** — He works at home.
**Ми слухаємо радіо.** — We listen to the radio.
**Вони вивчають слова.** — They study words.

Now that we have the key, it is time to use it. A very common habit for English speakers is "Infinitive Abuse." Because "to read" and "I read" look so similar in English, learners often try to say ~~Я читати книгу~~ (literally "I to read a book"). Let's break this habit immediately. The infinitive is just the name of the action; it cannot perform the action.

Let's drill replacing the static infinitive with the active, conjugated form. Pay attention to how the endings immediately bring the sentence to life.

| Infinitive | Meaning | Action | Meaning |
| :--- | :--- | :--- | :--- |
| **читати** | to read | **Я читаю** | I read |
| **писати** | to write | **Він пише** | He writes (note the shift: с → ш) |
| **слухати** | to listen | **Ми слухаємо** | We listen |
| **питати** | to ask | **Вони питають** | They ask |
| **грати** | to play | **Ти граєш** | You play |

> [!tip] Професійна порада (Pro Tip)
> Dropping the pronoun when the context is clear makes your Ukrainian sound much more natural and fluent. Don't be afraid to just say the verb!

Next, let's tackle "Pronoun Overuse." In English, we must say "I work. I listen. I read." Doing this in Ukrainian sounds overly repetitive and robotic: ~~Я працюю. Я слухаю. Я читаю.~~ Since the endings hold all the necessary information, let's practice stripping away the **Я** to achieve a smooth, native-like flow. Try reading these out loud, embracing the missing pronoun:

| Short Form | Meaning |
| :--- | :--- |
| **Працюю.** | I work. |
| **Слухаю.** | I listen. |
| **Знаю.** | I know. |
| **Думаю.** | I think. |
| **Розумію.** | I understand. |

Doesn't that feel faster and more authentic?

Now let's build full sentences. We will use the Subject-Verb-Object (SVO) order, which is identical to English structure. To keep things incredibly simple, we will use inanimate objects (things, not people) that are masculine or neuter. For these specific words, the form stays exactly the same whether it is the subject or the object. Let's introduce a few new items to interact with: **журнал** (magazine), **лист** (letter), **радіо** (radio), and **повідомлення** (message).

| Ukrainian | English |
| :--- | :--- |
| **Я читаю журнал.** | I read a magazine. |
| **Ти пишеш лист.** | You write a letter. |
| **Він слухає радіо.** | He listens to the radio. |
| **Ми пишемо повідомлення.** | We write a message. |

### Міні-розповідь (Mini-Story)
Let's see these verbs in action in a short text.

| Українською (In Ukrainian) | Англійською (In English) |
| :--- | :--- |
| **Я студент. Я багато вивчаю.** | I am a student. I study a lot. |
| **Я багато читаю і гарно пишу.** | I read a lot and write well. |
| **Ввечері я відпочиваю.** | In the evening, I rest. |
| **Я слухаю радіо.** | I listen to the radio. |
| **Мій друг також вивчає текст.** | My friend also studies the text. |
| **Він читає новини.** | He reads the news. |
| **Ми знаємо багато слів.** | We know a lot of words. |
| **Ми розуміємо все.** | We understand everything. |
| **Ти граєш у ігри?** | Do you play games? |
| **Ти чекаєш на автобус?** | Are you waiting for the bus? |
| **Так, я чекаю.** | Yes, I wait. |
| **Ти думаєш багато?** | Do you think a lot? |
| **Я завжди думаю.** | I always think. |
| **Ми працюємо і відпочиваємо.** | We work and rest. |
| **Вони також працюють.** | They also work. |
| **Я слухаю радіо щодня.** | I listen to the radio every day. |
| **Ти слухаєш уважно.** | You listen carefully. |
| **Він питає про це.** | He asks about this. |
| **Ми відповідаємо.** | We answer. |

### Діалог: Що ти робиш сьогодні? (Dialogue: What are you doing today?)
Let's look at a conversation between two friends, Anna and Ivan. They are discussing their daily activities.

> **Анна:** Привіт, Іване! Що ти робиш зараз? Ти працюєш?
> **Іван:** Привіт, Анно! Ні, я зараз не працюю. Я відпочиваю. Я слухаю радіо і читаю журнал.
> **Анна:** Що ти читаєш? Це цікавий журнал?
> **Іван:** Так, я читаю новини. Я багато читаю. А ти? Що ти робиш сьогодні? Ти багато граєш?
> **Анна:** Ні, я не граю сьогодні. Я багато вивчаю. Я читаю текст і пишу нові слова. Я вже багато знаю і розумію.
> **Іван:** Ти молодець! Ти гарно пишеш і добре розумієш. Твій брат також вивчає текст?
> **Анна:** Так, мій брат вивчає текст. Він зараз слухає подкаст і думає про це. Ми працюємо дуже багато.
> **Іван:** Ви студенти. Ви багато працюєте. А ваші друзі? Що роблять вони?
> **Анна:** Вони також працюють. Вони читають, пишуть і слухають. Ми всі вивчаємо текст.
> **Іван:** Добре. Я зараз чекаю на автобус. Я їду в магазин.
> **Анна:** Добре, Іване.
> **Іван:** Добре, Анно!

> [!tip] Зверніть увагу (Heads Up)
> In this dialogue, you saw the verbs **робити** (to do/make) and **їхати** (to go/ride). These are common verbs, but they follow *different* conjugation patterns — not the First Conjugation you learned today. For now, treat **Що ти робиш?** and **Я їду** as useful fixed phrases. You will learn their full patterns in the next module, The Living Verb II!

## Культурний аспект та підсумок (Cultural Insight and Summary)

> 🌍 **Культура (Culture): Мова — це важливо**
>
> There is a wonderful Ukrainian proverb that captures the spirit of what you are learning: **Птицю пізнати по пір'ю, а людину — по мові.** (*Ptytsiú piznáty po pir'iú, a liudýnu — po móvi.*) — "A bird is known by its feathers, and a person by their speech." **Мова — це дуже важливо.** (Language is very important.) In Ukrainian culture, the way you speak reflects who you are and your character. Taking the time to learn the proper verb endings instead of just using the infinitive shows respect for the language and its people. It shows that you are actively paying attention to the intricate, beautiful "feathers" — **пір'я** — of Ukrainian grammar.

You have just acquired a grammatical "Master Key." The First Conjugation pattern you learned today—the reliable **-ю, -єш, -є, -ємо, -єте, -ють** endings—unlocks the vast majority of everyday Ukrainian verbs. By simply swapping out the stem, you can suddenly talk about thinking (**думати**), understanding (**розуміти**), playing (**грати**), studying (**вивчати**), and countless other actions. It is a highly efficient system that rewards your learning effort immediately.

Today marks a major milestone in your language journey. You have transitioned from the English instructional scaffolding—learning how the language works from the outside—to initial Ukrainian immersion through direct action statements. You are no longer just statically observing the world; you are acting within it. You can confidently declare **Я знаю** (I know) instead of just pointing at a dictionary.

As you move forward, remember to bravely drop those pronouns when the context is clear. Embrace the rhythmic flow of the verb endings. They are the pulse of the Ukrainian sentence.

Let's do a quick self-check to ensure you are completely ready for the next step:
1. Can you confidently conjugate the verb **читати** for "I", "you (informal)", and "we"?
2. What happens to the stem of the verb **працювати** when we conjugate it in the present tense? Do we say ~~працюваю~~ or **працюю**?
3. Why is it considered completely natural to drop the pronoun **Я** and simply say **Слухаю**?
4. How would you natively say "I write a message" using the pro-drop feature we practiced?

If you can confidently answer these questions, you have successfully mastered the living verb! Keep practicing your daily routines by narrating your actions, and we will see you in the next lesson.

# Summary
You learned the First Conjugation for verbs ending in -ати. You can now talk about what you read, write, know, and listen to!
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/the-living-verb-i.yaml`

```yaml
- type: fill-in
  title: "Conjugate First Conjugation Verbs"
  instruction: "Choose the correct present tense form of the verb to complete the sentence."
  items:
    - sentence: "Я ___ книгу. (читати)"
      answer: "читаю"
      options: ["читаю", "читаєш", "читає", "читати"]
      explanation: "The ending -ю shows the action is done by Я (I)."
    - sentence: "Ти ___ лист. (писати)"
      answer: "пишеш"
      options: ["пишу", "пишеш", "пише", "писати"]
      explanation: "For Ти (you informal), the ending is -еш. Note the stem change with писати."
    - sentence: "Він ___ радіо. (слухати)"
      answer: "слухає"
      options: ["слухаю", "слухаєш", "слухає", "слухати"]
      explanation: "For він/вона/воно (he/she/it), the ending is -є."
    - sentence: "Ми ___ вдома. (працювати)"
      answer: "працюємо"
      options: ["працюю", "працюємо", "працюєте", "працювати"]
      explanation: "For Ми (we), the ending is -ємо. Remember the stem contracts from -ювати to -ю-."
    - sentence: "Ви ___ багато. (думати)"
      answer: "думаєте"
      options: ["думаю", "думаємо", "думаєте", "думати"]
      explanation: "For Ви (you formal/plural), the ending is -єте."
    - sentence: "Вони ___ все. (розуміти)"
      answer: "розуміють"
      options: ["розумію", "розуміє", "розуміємо", "розуміють"]
      explanation: "For Вони (they), the ending is -ють."
    - sentence: "Я ___ правду. (знати)"
      answer: "знаю"
      options: ["знаю", "знаєш", "знає", "знати"]
      explanation: "For Я (I), the ending is -ю attached to the stem зна-."
    - sentence: "Ти ___ в ігри. (грати)"
      answer: "граєш"
      options: ["граю", "граєш", "грає", "грати"]
      explanation: "For Ти (you informal), the ending is -єш."

- type: fill-in
  title: "Complete with the Correct Verb Form"
  instruction: "Read the context and choose the correct verb form to fill in the blank."
  items:
    - sentence: "Мій друг ___ текст."
      answer: "вивчає"
      options: ["вивчаю", "вивчаєш", "вивчає", "вивчати"]
      explanation: "Мій друг is third person singular (він), so the ending is -є."
    - sentence: "Ми ___ новини щодня."
      answer: "читаємо"
      options: ["читаю", "читаємо", "читаєте", "читають"]
      explanation: "Ми (we) takes the ending -ємо."
    - sentence: "Вони ___ уважно."
      answer: "слухають"
      options: ["слухаю", "слухає", "слухаємо", "слухають"]
      explanation: "Вони (they) takes the ending -ють."
    - sentence: "Я ___ на автобус."
      answer: "чекаю"
      options: ["чекаю", "чекаєш", "чекає", "чекати"]
      explanation: "Я (I) takes the ending -ю."
    - sentence: "Ти ___ про це."
      answer: "питаєш"
      options: ["питаю", "питаєш", "питає", "питати"]
      explanation: "Ти (you informal) takes the ending -єш."
    - sentence: "Ввечері я ___."
      answer: "відпочиваю"
      options: ["відпочиваю", "відпочиває", "відпочиваємо", "відпочивати"]
      explanation: "Я (I) takes the ending -ю."
    - sentence: "Ви ___ дуже багато."
      answer: "працюєте"
      options: ["працюю", "працюємо", "працюєте", "працюють"]
      explanation: "Ви (you formal/plural) takes the ending -єте."
    - sentence: "Він ___ повідомлення."
      answer: "пише"
      options: ["пишу", "пишеш", "пише", "пишуть"]
      explanation: "Він (he) takes the ending -е. Note the stem change with писати."

- type: match-up
  title: "Match the Pronoun to the Verb Form"
  instruction: "Match each pronoun with the correct conjugated form of the verb."
  pairs:
    - left: "Я + читати"
      right: "читаю"
    - left: "Ти + знати"
      right: "знаєш"
    - left: "Він + слухати"
      right: "слухає"
    - left: "Ми + працювати"
      right: "працюємо"
    - left: "Ви + грати"
      right: "граєте"
    - left: "Вони + думати"
      right: "думають"
    - left: "Я + вивчати"
      right: "вивчаю"
    - left: "Ти + чекати"
      right: "чекаєш"
    - left: "Він + писати"
      right: "пише"

- type: quiz
  title: "Understanding First Conjugation"
  instruction: "Choose the correct answer about Ukrainian verb conjugation."
  items:
    - question: "What is the correct 'I' form of працювати?"
      options:
        - text: "працюю"
          correct: true
        - text: "працюваю"
          correct: false
        - text: "працювати"
          correct: false
        - text: "працюєш"
          correct: false
      explanation: "The stem contracts from -ювати to -ю- before adding the ending. Працюваю is a common mistake."
    - question: "Why can you say 'Читаю' without the pronoun Я?"
      options:
        - text: "The verb ending -ю already shows who is doing the action"
          correct: true
        - text: "It is considered rude to use pronouns in Ukrainian"
          correct: false
        - text: "Ukrainian does not have pronouns"
          correct: false
        - text: "You must always include the pronoun"
          correct: false
      explanation: "Ukrainian is a pro-drop language. The ending itself acts like a built-in pronoun, so Я is optional."
    - question: "What ending do you add for 'they' (вони) in the First Conjugation?"
      options:
        - text: "-ють"
          correct: true
        - text: "-ємо"
          correct: false
        - text: "-єте"
          correct: false
        - text: "-ю"
          correct: false
      explanation: "Вони takes the ending -ють (e.g., вони читають, вони знають)."
    - question: "Which sentence is correct?"
      options:
        - text: "Я читаю журнал."
          correct: true
        - text: "Я читати журнал."
          correct: false
        - text: "Я читає журнал."
          correct: false
        - text: "Я читаємо журнал."
          correct: false
      explanation: "You must conjugate the verb. Я читати is 'infinitive abuse' — a common English-speaker mistake."
    - question: "What does the present tense cover in Ukrainian?"
      options:
        - text: "Both ongoing actions and habitual actions"
          correct: true
        - text: "Only actions happening right now"
          correct: false
        - text: "Only habitual or regular actions"
          correct: false
        - text: "Only future actions"
          correct: false
      explanation: "Читаю can mean both 'I am reading right now' and 'I read regularly'. One form covers both."
    - question: "What is the correct 'we' form of знати?"
      options:
        - text: "знаємо"
          correct: true
        - text: "знаю"
          correct: false
        - text: "знаєте"
          correct: false
        - text: "знають"
          correct: false
      explanation: "Ми (we) takes the ending -ємо, so it is знаємо."

- type: true-false
  title: "True or False? Verb Conjugation Facts"
  instruction: "Decide whether each statement about Ukrainian verbs is true or false."
  items:
    - statement: "In Ukrainian, you must always say the pronoun before the verb, just like in English."
      correct: false
      explanation: "Ukrainian is a pro-drop language. The verb ending shows who is acting, so pronouns are optional."
    - statement: "The First Conjugation endings are -ю, -єш, -є, -ємо, -єте, -ють."
      correct: true
      explanation: "These are the standard endings for First Conjugation (-ати) verbs in the present tense."
    - statement: "The correct 'I' form of працювати is працюваю."
      correct: false
      explanation: "The stem contracts. The correct form is працюю, not працюваю."
    - statement: "Читаю can mean both 'I read regularly' and 'I am reading right now'."
      correct: true
      explanation: "The Ukrainian present tense covers both ongoing and habitual actions."
    - statement: "To conjugate a First Conjugation verb, you remove -ти and add the personal ending."
      correct: true
      explanation: "You find the stem by removing -ти (e.g., чита- from читати), then add the ending."
    - statement: "Saying 'Я читати книгу' is correct Ukrainian."
      correct: false
      explanation: "This is 'infinitive abuse'. You must conjugate the verb: Я читаю книгу."

- type: unjumble
  title: "Build the Sentence"
  instruction: "Arrange the words to form a correct Ukrainian sentence."
  items:
    - words: ["читаю", "Я", "журнал"]
      answer: "Я читаю журнал"
    - words: ["лист", "пишеш", "Ти"]
      answer: "Ти пишеш лист"
    - words: ["радіо", "слухає", "Він"]
      answer: "Він слухає радіо"
    - words: ["працюємо", "Ми", "вдома"]
      answer: "Ми працюємо вдома"
    - words: ["багато", "Вони", "читають"]
      answer: "Вони читають багато"
    - words: ["повідомлення", "пишемо", "Ми"]
      answer: "Ми пишемо повідомлення"

- type: group-sort
  title: "Sort the Verb Forms"
  instruction: "Sort each conjugated verb form into the correct pronoun group."
  groups:
    - name: "Я (I)"
      items: ["читаю", "знаю", "працюю"]
    - name: "Ти (you)"
      items: ["читаєш", "знаєш", "граєш"]
    - name: "Він/Вона (he/she)"
      items: ["слухає", "думає", "вивчає"]
    - name: "Вони (they)"
      items: ["працюють", "чекають", "розуміють"]
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/the-living-verb-i.yaml`

```yaml
items:
  - lemma: "читати"
    translation: "to read"
    pos: "verb"
    aspect: "imperfective"
    usage: "читати книгу, читати новини, читати вголос"
    example: "Я читаю журнал."
  - lemma: "писати"
    translation: "to write"
    pos: "verb"
    aspect: "imperfective"
    usage: "писати лист, писати повідомлення, гарно писати"
    notes: "Stem changes in conjugation: пис- becomes пиш- (я пишу, він пише)"
    example: "Ти пишеш лист."
  - lemma: "знати"
    translation: "to know"
    pos: "verb"
    aspect: "imperfective"
    usage: "знати все, знати правду, не знати"
    example: "Ми знаємо багато слів."
  - lemma: "працювати"
    translation: "to work"
    pos: "verb"
    aspect: "imperfective"
    usage: "працювати вдома, працювати багато"
    notes: "Stem contracts: -ювати becomes -ю- (працюю, NOT працюваю)"
    example: "Ми працюємо дуже багато."
  - lemma: "слухати"
    translation: "to listen"
    pos: "verb"
    aspect: "imperfective"
    usage: "слухати музику, слухати уважно, слухати радіо"
    example: "Він слухає радіо."
  - lemma: "питати"
    translation: "to ask"
    pos: "verb"
    aspect: "imperfective"
    usage: "питати про це"
    example: "Він питає про це."
  - lemma: "грати"
    translation: "to play"
    pos: "verb"
    aspect: "imperfective"
    usage: "грати в ігри, добре грати"
    example: "Ти граєш у ігри?"
  - lemma: "чекати"
    translation: "to wait"
    pos: "verb"
    aspect: "imperfective"
    usage: "чекати на автобус, чекати на відповідь"
    example: "Я чекаю на автобус."
  - lemma: "думати"
    translation: "to think"
    pos: "verb"
    aspect: "imperfective"
    usage: "думати про це, думати багато"
    example: "Я завжди думаю."
  - lemma: "розуміти"
    translation: "to understand"
    pos: "verb"
    aspect: "imperfective"
    usage: "розуміти все, не розуміти"
    example: "Ми розуміємо все."
  - lemma: "вивчати"
    translation: "to study"
    pos: "verb"
    aspect: "imperfective"
    usage: "вивчати мову, вивчати текст, вивчати слова"
    example: "Мій друг також вивчає текст."
  - lemma: "відпочивати"
    translation: "to rest"
    pos: "verb"
    aspect: "imperfective"
    usage: "відпочивати вдома, відпочивати влітку"
    example: "Ввечері я відпочиваю."
  - lemma: "відповідати"
    translation: "to answer"
    pos: "verb"
    aspect: "imperfective"
    usage: "відповідати на питання"
    example: "Ми відповідаємо."
  - lemma: "журнал"
    translation: "magazine"
    pos: "noun"
    gender: "m"
    example: "Я читаю журнал."
  - lemma: "лист"
    translation: "letter"
    pos: "noun"
    gender: "m"
    example: "Ти пишеш лист."
  - lemma: "радіо"
    translation: "radio"
    pos: "noun"
    gender: "n"
    notes: "Indeclinable noun — the form never changes"
    example: "Він слухає радіо."
  - lemma: "повідомлення"
    translation: "message"
    pos: "noun"
    gender: "n"
    example: "Ми пишемо повідомлення."
  - lemma: "новини"
    translation: "news"
    pos: "noun"
    notes: "Typically used in plural"
    example: "Він читає новини."
  - lemma: "автобус"
    translation: "bus"
    pos: "noun"
    gender: "m"
    example: "Я чекаю на автобус."
  - lemma: "текст"
    translation: "text"
    pos: "noun"
    gender: "m"
    example: "Мій друг вивчає текст."
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
- Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-living-verb-i.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/the-living-verb-i.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/the-living-verb-i.yaml`

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
