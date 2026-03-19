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



**NOTE: 9 inline fix(es) from the review have ALREADY been applied to the files. Do NOT re-apply those fixes. Read the CURRENT file contents carefully — they reflect the post-fix state. Only fix issues that are still present in the current files.**

## Review Findings (targeted fix required)

**CONSTRAINTS:**
- Fix ONLY the issues listed below
- Do NOT rewrite surrounding text
- Preserve word count and structure
- Only modify these sections: Lines 121-122, Lines 138-141, Lines 15, 40, 47, 76, Lines 34, 40, 51, Lines 40, 80, 132

### Finding 1: Morphological Scope Violations — Imperatives in Ukrainian Instructions (HIGH)
**Location**: Lines 15, 40, 47, 76
**Problem**: Imperatives (Зверніть, Пам'ятайте, Подивіться, перевіряйте) not taught until M47. The research notes explicitly state: "No imperative verbs in instructions — use English." These Ukrainian imperative sentences are unparseable for M21 learners.
**Required Fix**: Replace all Ukrainian imperative instructions with English. E.g., line 15 → "Notice the endings." / line 40 → "Remember this, and your Ukrainian will be natural!" / line 47 → "Watch this video about demonstrative pronouns. It helps you understand the topic better!" / line 76 → "Always check the gender of the noun. If the word is feminine, we say «ця» or «та»."
**Severity**: HIGH

### Finding 2: Non-Nominative Cases in Ukrainian Instructional Prose (HIGH)
**Location**: Lines 34, 40, 51
**Problem**: At M21, only nominative case is available. Genitive (середнього, роду), accusative (різницю), instrumental (простішою, природною), and dative (множині) appear in Ukrainian instructional prose that learners are expected to read.
**Required Fix**: Move these instructional sentences to English. E.g., line 34 → "But when we point to a specific neuter noun..." / line 51 → "In the plural, Ukrainian becomes simpler!"
**Severity**: HIGH

### Finding 3: Non-Present Tenses in Ukrainian Prose (MEDIUM)
**Location**: Lines 40, 80, 132
**Problem**: Only present tense available before M36. Future (буде) and past (навчилися, вивчили) appear in Ukrainian instructional prose.
**Required Fix**: Replace with English or present tense. E.g., line 80 → "We now know how to point to objects nearby." / line 132 → "You've learned a lot today!"
**Severity**: HIGH

### Finding 4: "Remember to use:" Formatting Artifact (LOW)
**Location**: Lines 121-122
**Problem**: "Remember to use:" is an unusual prompt-like prefix. The plan specifies "Дайте мені цей торт" but the content uses "Цей торт, будь ла́ска" with this odd framing. "Дайте мені" is imperative so shouldn't be in Ukrainian either, but the example should flow naturally.
**Required Fix**: Remove "Remember to use:" prefix. Present as: `*   **Цей торт, будь ла́ска.** — This cake here, please.`
**Severity**: HIGH

### Finding 5: Practice Section Reveals Answers Inline (MEDIUM)
**Location**: Lines 138-141
**Problem**: The fill-in-the-blank exercise shows the answer immediately after each blank: "_____ **хло́пець** (masculine) → **цей хло́пець**". This removes the pedagogical challenge — the learner reads the answer without attempting it.
**Required Fix**: Present blanks without answers, then provide answers in a separate collapsed/spoiler section, or simply remove the answers and let the activities YAML handle interactive practice.
**Severity**: HIGH

---

## Critical Issues Found

### Issue 1: Morphological Scope Violations — Imperatives in Ukrainian Instructions (HIGH)
- **Location**: Lines 15, 40, 47, 76
- **Original**: 「Зверніть увагу на закінчення.」 (line 15), 「Пам'ятайте про це, і ваша мова буде природною!」 (line 40), 「Подивіться відео про вказівні займенники. Це допомагає краще розуміти тему!」 (line 47), 「Завжди перевіряйте рід іменника. Якщо слово жіночого роду, кажемо «ця» або «та».」 (line 76)
- **Problem**: Imperatives (Зверніть, Пам'ятайте, Подивіться, перевіряйте) not taught until M47. The research notes explicitly state: "No imperative verbs in instructions — use English." These Ukrainian imperative sentences are unparseable for M21 learners.
- **Fix**: Replace all Ukrainian imperative instructions with English. E.g., line 15 → "Notice the endings." / line 40 → "Remember this, and your Ukrainian will be natural!" / line 47 → "Watch this video about demonstrative pronouns. It helps you understand the topic better!" / line 76 → "Always check the gender of the noun. If the word is feminine, we say «ця» or «та»."

### Issue 2: Non-Nominative Cases in Ukrainian Instructional Prose (HIGH)
- **Location**: Lines 34, 40, 51
- **Original**: 「Але коли ми вказуємо на конкретний предмет середнього роду」 (line 34 — genitive середнього роду), 「Бачите різницю?」 (line 40 — accusative різницю), 「У множині українська мова стає простішою!」 (line 51 — instrumental простішою, dative множині)
- **Problem**: At M21, only nominative case is available. Genitive (середнього, роду), accusative (різницю), instrumental (простішою, природною), and dative (множині) appear in Ukrainian instructional prose that learners are expected to read.
- **Fix**: Move these instructional sentences to English. E.g., line 34 → "But when we point to a specific neuter noun..." / line 51 → "In the plural, Ukrainian becomes simpler!"

### Issue 3: Non-Present Tenses in Ukrainian Prose (MEDIUM)
- **Location**: Lines 40, 80, 132
- **Original**: 「Пам'ятайте про це, і ваша мова буде природною!」 (line 40 — future буде), 「Ми навчилися вказувати на предмети поруч.」 (line 80 — past навчилися), 「Ви сьогодні багато вивчили!」 (line 132 — past вивчили)
- **Problem**: Only present tense available before M36. Future (буде) and past (навчилися, вивчили) appear in Ukrainian instructional prose.
- **Fix**: Replace with English or present tense. E.g., line 80 → "We now know how to point to objects nearby." / line 132 → "You've learned a lot today!"

### Issue 4: "Remember to use:" Formatting Artifact (LOW)
- **Location**: Lines 121-122
- **Original**: 「Remember to use: Цей торт, будь ла́ска.」
- **Problem**: "Remember to use:" is an unusual prompt-like prefix. The plan specifies "Дайте мені цей торт" but the content uses "Цей торт, будь ла́ска" with this odd framing. "Дайте мені" is imperative so shouldn't be in Ukrainian either, but the example should flow naturally.
- **Fix**: Remove "Remember to use:" prefix. Present as: `*   **Цей торт, будь ла́ска.** — This cake here, please.`

### Issue 5: Practice Section Reveals Answers Inline (MEDIUM)
- **Location**: Lines 138-141
- **Problem**: The fill-in-the-blank exercise shows the answer immediately after each blank: "_____ **хло́пець** (masculine) → **цей хло́пець**". This removes the pedagogical challenge — the learner reads the answer without attempting it.
- **Fix**: Present blanks without answers, then provide answers in a separate collapsed/spoiler section, or simply remove the answers and let the activities YAML handle interactive practice.

---

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 15 | 「Зверніть увагу на закінчення.」 | "Notice the endings." (English) | Scope — imperative |
| 34 | 「на конкретний предмет середнього роду」 | "a specific neuter noun" (English) | Scope — genitive |
| 40 | 「Бачите різницю?」 | "Can you see the difference?" (English) | Scope — accusative |
| 40 | 「Пам'ятайте про це, і ваша мова буде природною!」 | "Remember this, and your Ukrainian will sound natural!" (English) | Scope — imperative + future + instrumental |
| 47 | 「Подивіться відео про вказівні займенники. Це допомагає краще розуміти тему!」 | "Watch this video about demonstrative pronouns. It helps you understand the topic better!" (English) | Scope — imperative + accusative |
| 51 | 「У множині українська мова стає простішою!」 | "In the plural, Ukrainian becomes simpler!" (English) | Scope — dative + instrumental |
| 76 | 「Завжди перевіряйте рід іменника. Якщо слово жіночого роду, кажемо «ця» або «та».」 | "Always check the gender of the noun. If the word is feminine, we say «ця» or «та»." (English) | Scope — imperative |
| 80 | 「Ми навчилися вказувати на предмети поруч.」 | "We've learned to point to nearby objects." (English) | Scope — past tense |
| 132 | 「Ви сьогодні багато вивчили!」 | "You've learned a lot today!" (English) | Scope — past tense |

---

## Fix Plan to Reach 9/10 (REQUIRED if score < 9.0)

### Language: 6/10 → 9/10
**What to fix:**
1. Lines 15, 40, 47, 76: Replace ALL Ukrainian imperative instructions with English equivalents (4 locations)
2. Lines 34, 40, 51: Replace Ukrainian sentences containing non-nominative cases with English (3 locations)
3. Lines 40, 80, 132: Replace Ukrainian past/future tense in instructional prose with English (3 locations)
4. Lines 42, 71: Video titles contain УКРАЇ́НСЬКОЮ (instrumental) — these are external titles, acceptable to keep as-is (DISMISS)

**Expected score after fix:** 9/10

### Linguistic Accuracy: 6/10 → 9/10
**What to fix:**
Same fixes as Language above — the morphological violations are the only accuracy issue. Grammar explanations themselves are correct. Example Ukrainian sentences (цей хлопець, ця вулиця, etc.) are all properly formed nominative phrases — the violations are exclusively in instructional/meta prose.

**Expected score after fix:** 9/10

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Lines 121-122: Remove "Remember to use:" prefix
2. Lines 138-141: Remove inline answers from practice blanks, or restructure as "try first, then check"

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.1 + 8×1.2 + 8×1.3 + 8×1.3 + 8×1.0 + 9×1.5) / 8.9
= (13.5 + 9.9 + 9.6 + 10.4 + 10.4 + 8.0 + 13.5) / 8.9
= 75.3 / 8.9 = 8.5/10
```

---

## Audit Failures (from automated re-audit)

```
⚠️ HYDRATION NOTE: Outline sums to 1452, exceeding word_target 1200
❌ Missing required activity types from meta.yaml: classify
--- STRICT GATES (Level A1) ---
❌ AUDIT FAILED. Correct errors before proceeding.
Critical Failures:
• Missing required activity types: classify
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/demonstratives-this-that-audit.log for details)
⚠️  RAG verification found unverified words (see audit report)
--- STATUS JSON GATE BLOCKERS ---
GATE BLOCKER: Missing required activity types: classify
--- VESUM WORD VERIFICATION FAILURES ---
These words were NOT found in the VESUM morphological dictionary.
Check if they are valid Ukrainian forms. Fix misspellings or Russianisms.
  ❌ `Пам` (source: prose)
  ❌ `ятайте` (source: prose)
  ❌ `єкти` (source: prose)
  ❌ `єктів` (source: prose)
```

---

## File Contents (for reference)

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/demonstratives-this-that.md`

```markdown
## Вступ: Як вказувати на предмети? (Introduction: How to point to objects?)

Привіт! Вітаю! (Hello! Greetings!) Ви вже знаєте, як сказати "my" (**мій**), "your" (**твій**), and other possessives. Now, let's take the next natural step. Як вказувати на предмети? How do you say "this house" or "that street"? In Ukrainian, just like with possessive pronouns, our demonstrative pronouns — the pointing words — need to match the gender of the noun they describe.

## Цей/ця/це: Вказуємо на близькі об’єкти (This: Pointing to Near Objects)

Let's start with the word for "this" when something is close to you. Because Ukrainian has three genders for singular nouns, we have three different words for "this". They work exactly like the **мій** / **моя** / **моє** pattern you already know and love!

Here is how we match "this" to masculine, feminine, and neuter nouns:

*   **цей** — this (masculine)
*   **ця** — this (feminine)
*   **це** — this (neuter)

Let's see them in action with some examples. Notice the endings!

*   **цей хло́пець** — this guy (masculine)
*   **цей буди́нок** — this building (masculine)
*   **ця ді́вчи́на** — this girl (feminine)
*   **ця ву́лиця** — this street (feminine)
*   **це мі́сто** — this city (neuter)
*   **це о́зеро** — this lake (neuter)

When you look at **цей**, **ця**, and **це**, you might notice that **це** looks very familiar. You have actually been using **це** since your very first lessons! But there is a critical contrast for beginners that we need to clear up right now.

Є велика різниця між **це** as a linking word (a copula) meaning "This is" and **це** as a demonstrative pointing word meaning "this specific neuter noun".

Коли ми кажемо «Це...» (This is...), форма не змінюється, no matter what noun follows it. It acts like an equal sign.

*   **Це мі́сто.** — This is a city.
*   **Це кафе́.** — This is a cafe.
*   **Це стіле́ць.** — This is a chair. (Even though chair is masculine!)

But when we point to a specific neuter noun, it means "this specific thing". In this case, it must match the neuter gender.

*   **Це мі́сто — старе́.** — This city is old.
*   **Це кафе́ — га́рне.** — This cafe is nice.
*   **Це о́зеро — вели́ке.** — This lake is big.

Бачите різницю? **Це кафе** (This is a cafe) is a full sentence. **Це кафе** (this specific cafe) inside a sentence like **Це кафе га́рне** is just a descriptive phrase. Пам’ятайте про це, і ваша мова буде природною!

> [!video] THIS, THAT, THESE, THOSE - ВКАЗІВНІ ЗАЙМЕННИКИ (УКРАЇ́НСЬКОЮ) | УРОК 22
> https://www.youtube.com/watch?v=XXalk_gwWXE


> [!info] 🎬 Відео
Watch this video about demonstrative pronouns. It helps you understand the topic better!

## Ці: Вказуємо на багато об’єктів (These: Pointing to Many Objects)

Now you can point to a single object. But what if there are many? Perhaps you are holding two books or looking at a group of students. In the plural, Ukrainian becomes simpler!

No need to think about gender anymore. For all plural nouns, we use a single, universal word for "these": **ці**.

Let's look at the transformation from singular to plural. Notice how every single gender collapses into the exact same plural form:

*   **цей** → **ці** (masculine singular to plural)
*   **ця** → **ці** (feminine singular to plural)
*   **це** → **ці** (neuter singular to plural)

Ось реальні приклади:

*   **ці книжки́** — these books
*   **ці студе́нти** — these students
*   **ці мі́ста** — these cities

This is a huge relief, right? However, there is one very common mistake that English speakers make. Because English sometimes uses "this" in ways that can feel plural or collective, learners sometimes try to mix a singular pointing word with a plural noun.

For example, a learner might say **цей книжки** instead of **ці книжки**. This sounds very jarring to a Ukrainian ear! The best prevention strategy is to always check the noun first. If the noun is plural, immediately lock in **ці**. Do not even think about the gender. Plural means **ці**, end of story. This simple habit will save you from the most common beginner trap.

> [!video] УРОК 32. ВКАЗІВНІ ЗАЙМЕННИКИ THIS THAT THESE THOSE (ПОЯСНЕННЯ УКРАЇ́НСЬКОЮ)
> https://www.youtube.com/watch?v=Ng0Lt33xBIk


> [!tip] 💡 Порада
Always check the gender of the noun. If the word is feminine, we say «ця» or «та».

## Той/та/те/ті: Вказуємо на далекі об’єкти (That/Those: Pointing to Distant Objects)

We've learned to point to nearby objects. But what if the object is far away? In English, you say "that" or "those". In Ukrainian, we use a different set of demonstrative pronouns to indicate distance.

Just like with the "this" group, the "that" group must agree with the gender and number of the noun it describes. The pattern will look very familiar to you by now:

*   **той** — that (masculine)
*   **та** — that (feminine)
*   **те** — that (neuter)
*   **ті** — those (plural for all genders)

Let's pair these up with some of our vocabulary words to see how they sound:

*   **той буди́нок** — that building
*   **та ву́лиця** — that street
*   **те о́зеро** — that lake
*   **ті лю́ди** — those people

As you practice these, you will quickly get the hang of matching the vowel sounds. But there is a very important detail to pay attention to regarding the feminine form **та**.

You might recall that Ukrainian has a few words for "and" (**і**, **й**, and **та**). Because the feminine demonstrative pronoun **та** (that) looks and sounds exactly the same as the conjunction **та** (and), you might run into sentences where the same word appears twice, doing two completely different jobs!

Let's look at a context resolution example:

*   **Та ді́вчи́на та її по́друга.** — That girl and her friend.

In this sentence, the first **та** is pointing at the girl ("that girl"), while the second **та** is simply connecting the two people ("and"). How do you tell the difference? Context is everything. A demonstrative pronoun will always sit directly in front of the noun it modifies, acting as a pointer. A conjunction will sit right between two nouns or phrases, linking them together. When you read or listen to Ukrainian, your brain will naturally learn to separate these two functions based on their position in the sentence.


> [!note] 🏺 Культура
У магазині українці часто кажуть «цей» або «той». Це допомагає швидко отримати товар.

## Цей vs Той у контексті (This vs That in context)

Now we have all the pieces of the puzzle: the close group (**цей** / **ця** / **це** / **ці**) and the distant group (**той** / **та** / **те** / **ті**). How do we choose between them in real life? The choice usually comes down to spatial distance or textual distance.

Просторова дистанція — це відстань у просторі. We use **цей** for something right here, and **той** for something over there. Уявіть, що ви в кімнаті, де є два стільці.

*   **цей стіле́ць** — this chair (the one you are close to)
*   **той стіле́ць** — that chair (the one across the room)

This proximity contrast is incredibly useful in a store or a cafe. Imagine you are ordering a dessert. You might point to the display case and say:

*   **Цей торт, будь ла́ска.** — This cake here, please.
*   **Той торт, будь ла́ска.** — That cake there, please.

It is also common to use words like **такий** (such) or **і́нший** (other) when comparing things in space. For example, **цей буди́нок нови́й, а той — і́нший** (this building is new, and that one is different).

Крім фізичного простору, ми використовуємо ці слова у розмові. When you are referring to something that was just said right now, you use **цей**. When you refer to something mentioned earlier, you use **той**. Every student (**ко́жний студе́нт**) learns this through practice.

For example, if you are telling a story and introduce a new fact, you might say **це пра́вда** (this is true). But if you are reminding someone of a rule from last week, you would point back to it as "that rule". You will soon find yourself using these words naturally in your own dialogues, and you will feel proud when you catch yourself doing it yourself (**сам** / **сама**)!

## Практика: Тренуємо вказівні займенники (Practice: Drilling Demonstrative Pronouns)

You've learned a lot today! The best way to lock in these grammar rules is to practice classifying nouns into the correct demonstrative groups.

When you see a new noun, your first reflex should be to check its gender. Is it masculine, feminine, neuter, or plural? Once you know that, choosing the right pointing word is easy.

Let's do some exercises to choose the correct demonstrative pronoun according to the gender and number of the noun. Try to fill in the blanks with the correct form of "this" (**цей**, **ця**, **це**, **ці**):

*   _____ **хло́пець** (masculine) → **цей хло́пець**
*   _____ **ву́лиця** (feminine) → **ця ву́лиця**
*   _____ **о́зеро** (neuter) → **це о́зеро**
*   _____ **книжки́** (plural) → **ці книжки́**

Now, let's practice the spatial distance contrast. Imagine you are comparing an object close to you with an object far away. Sort these pairs into the "here" group and the "there" group:

*   **цей стіле́ць** (here) vs **той стіле́ць** (there)
*   **ця ді́вчи́на** (here) vs **та ді́вчи́на** (there)
*   **це мі́сто** (here) vs **те мі́сто** (there)
*   **ці лю́ди** (here) vs **ті лю́ди** (there)

Remember to read these pairs out loud. Speaking the contrast between the near and far words will help train your ear to expect the correct vowel sounds.

## Підсумок: Що ми вивчили сьогодні? (Summary: What did we learn today?)
Let's recap what we have covered today. You now have the power to point out exactly what you want to talk about, whether it is right in front of you or across the room!

We learned that demonstrative pronouns must agree with the gender and number of the noun they modify. For objects close to you, we use the **цей** / **ця** / **це** / **ці** family. For objects further away, we use the distant group: **той** / **та** / **те** / **ті**. We also explored the critical difference between **це** as an unchanging linking word ("This is...") and **це** as a gender-matching pointing word ("This lake..."). Finally, we looked at how **та** can mean either "that" (feminine) or "and", depending on the context.

Here are a few self-check questions to test your understanding before you move on:

1.  Which form of "this" do you use for a plural noun?
2.  How do you say "that building" (masculine) in Ukrainian?
3.  What is the difference between "Це стілець" and "Цей стілець"?
4.  Why is it incorrect to say "цей студенти"?

Чудова робота! Ви будуєте міцний фундамент.

```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/demonstratives-this-that.yaml`

```yaml
- type: fill-in
  title: "Choose the Correct Demonstrative Pronoun"
  instruction: "Fill in the blank with the correct form of 'this' or 'that' based on the gender and number of the noun."
  items:
    - sentence: "_____ хлопець читає книгу."
      answer: "цей"
      options: ["цей", "ця", "це", "ці"]
      explanation: "Хлопець is masculine, so we use цей (this, masculine)."
    - sentence: "_____ дівчина — моя сестра."
      answer: "ця"
      options: ["цей", "ця", "це", "ці"]
      explanation: "Дівчина is feminine, so we use ця (this, feminine)."
    - sentence: "_____ озеро — велике."
      answer: "це"
      options: ["цей", "ця", "це", "ці"]
      explanation: "Озеро is neuter, so we use це (this, neuter)."
    - sentence: "_____ студенти — нові."
      answer: "ці"
      options: ["цей", "ця", "це", "ці"]
      explanation: "Студенти is plural, so we use ці (these)."
    - sentence: "_____ будинок — старий."
      answer: "той"
      options: ["той", "та", "те", "ті"]
      explanation: "Будинок is masculine, so we use той (that, masculine)."
    - sentence: "_____ вулиця — гарна."
      answer: "та"
      options: ["той", "та", "те", "ті"]
      explanation: "Вулиця is feminine, so we use та (that, feminine)."
    - sentence: "_____ місто — нове."
      answer: "те"
      options: ["той", "та", "те", "ті"]
      explanation: "Місто is neuter, so we use те (that, neuter)."
    - sentence: "_____ люди — мої друзі."
      answer: "ті"
      options: ["той", "та", "те", "ті"]
      explanation: "Люди is plural, so we use ті (those)."
    - sentence: "_____ книга — цікава."
      answer: "ця"
      options: ["цей", "ця", "це", "ці"]
      explanation: "Книга is feminine, so we use ця (this, feminine)."
    - sentence: "_____ стілець — новий."
      answer: "цей"
      options: ["цей", "ця", "це", "ці"]
      explanation: "Стілець is masculine, so we use цей (this, masculine)."

- type: quiz
  title: "Demonstrative Pronoun Agreement"
  instruction: "Choose the correct answer for each question about Ukrainian demonstrative pronouns."
  items:
    - question: "Which demonstrative pronoun do you use with a masculine noun to say 'this'?"
      options:
        - text: "цей"
          correct: true
        - text: "ця"
          correct: false
        - text: "це"
          correct: false
        - text: "ці"
          correct: false
      explanation: "Цей is the masculine singular form of 'this' — цей хлопець, цей будинок."
    - question: "Which demonstrative pronoun do you use with a feminine noun to say 'that'?"
      options:
        - text: "той"
          correct: false
        - text: "та"
          correct: true
        - text: "те"
          correct: false
        - text: "ті"
          correct: false
      explanation: "Та is the feminine singular form of 'that' — та вулиця, та дівчина."
    - question: "How do you say 'this city' in Ukrainian? (місто is neuter)"
      options:
        - text: "цей місто"
          correct: false
        - text: "ця місто"
          correct: false
        - text: "це місто"
          correct: true
        - text: "ці місто"
          correct: false
      explanation: "Місто is neuter, so we use це — це місто."
    - question: "How do you say 'those people' in Ukrainian?"
      options:
        - text: "той люди"
          correct: false
        - text: "та люди"
          correct: false
        - text: "те люди"
          correct: false
        - text: "ті люди"
          correct: true
      explanation: "Люди is plural, so we use ті (those) — gender does not matter in plural."
    - question: "What is special about the word ці?"
      options:
        - text: "It is used only for feminine nouns"
          correct: false
        - text: "It is the plural form for all genders"
          correct: true
        - text: "It means 'that' for neuter nouns"
          correct: false
        - text: "It is used only for masculine nouns"
          correct: false
      explanation: "Ці is the universal plural form — цей, ця, and це all become ці in the plural."
    - question: "Which sentence uses це as a linking word meaning 'This is...'?"
      options:
        - text: "Це місто — старе."
          correct: false
        - text: "Це стілець."
          correct: true
        - text: "Це озеро — велике."
          correct: false
        - text: "Це село — гарне."
          correct: false
      explanation: "'Це стілець' means 'This is a chair' — це acts as a linking word, not a gender-matching pronoun. Стілець is masculine, but це does not change."
    - question: "Why is 'цей книжки' incorrect?"
      options:
        - text: "Книжки is feminine, so it needs ця"
          correct: false
        - text: "Книжки is plural, so it needs ці"
          correct: true
        - text: "Книжки is neuter, so it needs це"
          correct: false
        - text: "Цей is not a real Ukrainian word"
          correct: false
      explanation: "Книжки is the plural form of книжка. All plural nouns use ці, regardless of gender."
    - question: "How do you say 'that chair' in Ukrainian? (стілець is masculine)"
      options:
        - text: "та стілець"
          correct: false
        - text: "те стілець"
          correct: false
        - text: "той стілець"
          correct: true
        - text: "ті стілець"
          correct: false
      explanation: "Стілець is masculine, so we use той — той стілець."
    - question: "In the sentence 'Та дівчина та її подруга', what does the first та mean?"
      options:
        - text: "and"
          correct: false
        - text: "that (feminine)"
          correct: true
        - text: "this (feminine)"
          correct: false
        - text: "those"
          correct: false
      explanation: "The first та is a demonstrative pronoun meaning 'that girl'. The second та is the conjunction 'and'."
    - question: "Which form means 'that' for a neuter noun?"
      options:
        - text: "той"
          correct: false
        - text: "та"
          correct: false
        - text: "те"
          correct: true
        - text: "ті"
          correct: false
      explanation: "Те is the neuter singular form of 'that' — те озеро, те місто."
    - question: "You are in a cafe and want to point at a cake right in front of you. What do you say?"
      options:
        - text: "Той торт, будь ласка."
          correct: false
        - text: "Цей торт, будь ласка."
          correct: true
        - text: "Ті торт, будь ласка."
          correct: false
        - text: "Ця торт, будь ласка."
          correct: false
      explanation: "The cake is close to you, so use цей (this). Торт is masculine — цей торт."
    - question: "How do you say 'these books' in Ukrainian?"
      options:
        - text: "ця книжки"
          correct: false
        - text: "цей книжки"
          correct: false
        - text: "це книжки"
          correct: false
        - text: "ці книжки"
          correct: true
      explanation: "Книжки is plural, so we always use ці — ці книжки."

- type: match-up
  title: "Match the Demonstrative to Its Noun"
  instruction: "Match each noun with the correct demonstrative pronoun for 'this'."
  pairs:
    - left: "хлопець (guy)"
      right: "цей"
    - left: "дівчина (girl)"
      right: "ця"
    - left: "місто (city)"
      right: "це"
    - left: "книжки (books)"
      right: "ці"
    - left: "будинок (building)"
      right: "цей"
    - left: "вулиця (street)"
      right: "ця"
    - left: "озеро (lake)"
      right: "це"
    - left: "студенти (students)"
      right: "ці"
    - left: "стілець (chair)"
      right: "цей"
    - left: "школа (school)"
      right: "ця"

- type: group-sort
  title: "Sort by Gender Group"
  instruction: "Sort these nouns into the correct demonstrative group. Which pronoun — цей, ця, це, or ці — goes with each noun?"
  groups:
    - name: "цей (masculine)"
      items: ["будинок", "хлопець", "стілець"]
    - name: "ця (feminine)"
      items: ["вулиця", "дівчина", "школа"]
    - name: "це (neuter)"
      items: ["місто", "озеро", "село"]
    - name: "ці (plural)"
      items: ["книжки", "студенти", "люди"]
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/demonstratives-this-that.yaml`

```yaml
items:
  - lemma: "цей"
    translation: "this (masculine)"
    pos: "pronoun"
    gender: "m"
    usage: "цей хлопець, цей будинок"
    notes: "Demonstrative pronoun, agrees with masculine nouns"
  - lemma: "ця"
    translation: "this (feminine)"
    pos: "pronoun"
    gender: "f"
    usage: "ця дівчина, ця книга"
    notes: "Feminine form of цей"
  - lemma: "це"
    translation: "this (neuter); this is"
    pos: "pronoun"
    gender: "n"
    usage: "це місто, це озеро"
    notes: "Also used as a linking word (copula) meaning 'this is' — Це кафе."
  - lemma: "ці"
    translation: "these (all genders)"
    pos: "pronoun"
    usage: "ці книжки, ці студенти, ці міста"
    notes: "Universal plural form — no gender distinction"
  - lemma: "той"
    translation: "that (masculine)"
    pos: "pronoun"
    gender: "m"
    usage: "той будинок, той стілець"
    notes: "Distant demonstrative, masculine"
  - lemma: "та"
    translation: "that (feminine)"
    pos: "pronoun"
    gender: "f"
    usage: "та вулиця, та дівчина"
    notes: "Same form as conjunction та (and) — context resolves the ambiguity"
  - lemma: "те"
    translation: "that (neuter)"
    pos: "pronoun"
    gender: "n"
    usage: "те озеро, те місто"
    notes: "Distant demonstrative, neuter"
  - lemma: "ті"
    translation: "those (all genders)"
    pos: "pronoun"
    usage: "ті люди, ті міста"
    notes: "Universal plural distant form"
  - lemma: "будинок"
    translation: "building, house"
    pos: "noun"
    gender: "m"
    usage: "цей будинок, той будинок"
  - lemma: "вулиця"
    translation: "street"
    pos: "noun"
    gender: "f"
    usage: "ця вулиця, та вулиця"
  - lemma: "озеро"
    translation: "lake"
    pos: "noun"
    gender: "n"
    usage: "це озеро, те озеро"
  - lemma: "стілець"
    translation: "chair"
    pos: "noun"
    gender: "m"
    usage: "цей стілець, той стілець"
    notes: "Used in proximity contrast examples"
  - lemma: "такий"
    translation: "such, so"
    pos: "pronoun"
    usage: "такий великий, такий цікавий"
    notes: "Related demonstrative, agrees with noun gender"
  - lemma: "інший"
    translation: "other, different"
    pos: "adjective"
    usage: "інший будинок, інша вулиця"
    notes: "Used when contrasting objects"
  - lemma: "кожний"
    translation: "every, each"
    pos: "pronoun"
    usage: "кожний студент, кожна книга"
    notes: "Universal pronoun, agrees with noun gender"
  - lemma: "сам"
    translation: "oneself, self"
    pos: "pronoun"
    usage: "сам бачив, сама знає"
    notes: "Emphatic pronoun, masculine form; feminine is сама"
  - lemma: "хлопець"
    translation: "guy, young man"
    pos: "noun"
    gender: "m"
    usage: "цей хлопець"
  - lemma: "дівчина"
    translation: "girl, young woman"
    pos: "noun"
    gender: "f"
    usage: "ця дівчина, та дівчина"
  - lemma: "місто"
    translation: "city, town"
    pos: "noun"
    gender: "n"
    usage: "це місто, те місто"
  - lemma: "торт"
    translation: "cake"
    pos: "noun"
    gender: "m"
    usage: "цей торт, той торт"
    notes: "Used in cafe/shop proximity contrast scenarios"
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
- Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/demonstratives-this-that.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/demonstratives-this-that.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/demonstratives-this-that.yaml`

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
