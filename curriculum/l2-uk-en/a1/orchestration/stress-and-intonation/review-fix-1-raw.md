✅ Message sent to Gemini (ID: 26371) [auto-acked: self-addressed]

🚀 Invoking Gemini to process message #26371...
📨 Message #26371
   From: gemini → To: gemini
   Type: query
   Task: stress-and-intonation-review-fix-1
   Time: 2026-03-17T15:58:22.818598+00:00

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
- Only modify these sections: Section "Інтонація — Intonation", Section "Наголос — Stress", `[!note] Stress mark reminder`, Section "Рухомий наголос — Mobile Stress", Section "Типові наголоси — Common Stress Patterns"

### Finding 1: Grammar Scope Violation (Verbs in A1 M6)
**Location**: Section "Рухомий наголос — Mobile Stress"
**Problem**: The text uses verbs to explain mobile stress: `Take **писа́ти** (to write): ... **пишу́** ... **пи́шеш**`. Module 6 is pre-verb; verbs are explicitly forbidden before M15.
**Required Fix**: Replace the verb example with a simple noun that changes stress in the plural, such as `сестра́` -> `се́стри`.
**Severity**: HIGH

### Finding 2: Colonial Framing in Vowel Note
**Location**: Section "Наголос — Stress", `[!note] Stress mark reminder`
**Problem**: The text states: `"There is no vowel reduction like in English or Russian."` Defining Ukrainian phonetics by what it *doesn't* share with Russian is a violation of the colonial framing rule.
**Required Fix**: Remove the reference to Russian. Just compare it to English.
**Severity**: HIGH

### Finding 3: Unnecessary Stress Mark on Monosyllabic Word
**Location**: Section "Інтонація — Intonation"
**Problem**: The text includes a stress mark on a single-syllable word: `> **Де́ кафе́?** ↗↘`. Monosyllabic words do not take stress marks in standard Ukrainian orthography unless for specific semantic contrast.
**Required Fix**: Remove the accent mark from `Де`: `> **Де кафе́?** ↗↘`.
**Severity**: HIGH

### Finding 4: Richness Gap (Missing Tables)
**Location**: Section "Типові наголоси — Common Stress Patterns"
**Problem**: The module has a 54% richness score, specifically missing tables (0/2 target). The bulleted lists of stress patterns are perfectly suited for a summary table to improve visual engagement.
**Required Fix**: Convert the bulleted lists of first-syllable, last-syllable, and penultimate stress into a single Markdown table.
**Severity**: HIGH

---

## Critical Issues Found

### Issue 1: Grammar Scope Violation (Verbs in A1 M6)
**Location**: Section "Рухомий наголос — Mobile Stress"
**Problem**: The text uses verbs to explain mobile stress: `Take **писа́ти** (to write): ... **пишу́** ... **пи́шеш**`. Module 6 is pre-verb; verbs are explicitly forbidden before M15.
**Fix**: Replace the verb example with a simple noun that changes stress in the plural, such as `сестра́` -> `се́стри`.

### Issue 2: Colonial Framing in Vowel Note
**Location**: Section "Наголос — Stress", `[!note] Stress mark reminder`
**Problem**: The text states: `"There is no vowel reduction like in English or Russian."` Defining Ukrainian phonetics by what it *doesn't* share with Russian is a violation of the colonial framing rule.
**Fix**: Remove the reference to Russian. Just compare it to English.

### Issue 3: Unnecessary Stress Mark on Monosyllabic Word
**Location**: Section "Інтонація — Intonation"
**Problem**: The text includes a stress mark on a single-syllable word: `> **Де́ кафе́?** ↗↘`. Monosyllabic words do not take stress marks in standard Ukrainian orthography unless for specific semantic contrast.
**Fix**: Remove the accent mark from `Де`: `> **Де кафе́?** ↗↘`.

### Issue 4: Richness Gap (Missing Tables)
**Location**: Section "Типові наголоси — Common Stress Patterns"
**Problem**: The module has a 54% richness score, specifically missing tables (0/2 target). The bulleted lists of stress patterns are perfectly suited for a summary table to improve visual engagement.
**Fix**: Convert the bulleted lists of first-syllable, last-syllable, and penultimate stress into a single Markdown table.

---

## Ukrainian Language Issues
- The use of `Де́` with an acute accent is non-standard for a single-syllable word.
- The use of syllables like `-да` or `во-` in the Activity YAML options triggers VESUM errors. While factually clear to a human, it breaks the automated validation pipeline.

---

## Fix Plan to Reach PASS
1. Replace the `писа́ти` verb example with the noun `сестра́`/`се́стри` in both the prose and the "Stress Minimal Pairs" activity.
2. Remove the phrase "or Russian" from the vowel reduction `[!note]`.
3. Change `**Де́ кафе́?**` to `**Де кафе́?**`.
4. Convert the lists in "Типові наголоси" into a Markdown table to meet structural richness requirements.
5. In the activities YAML, reformat syllables in the options (e.g., change "Last syllable (-да)" to "Last syllable") to avoid isolated Cyrillic characters that cause VESUM scanner failures.

---

## Audit Failures (from automated re-audit)

```
⚠️ HYDRATION NOTE: Outline sums to 1300, exceeding word_target 1200
--- STRICT GATES (Level A1) ---
Pedagogy     ❌ 4 violations
📚 PEDAGOGICAL VIOLATIONS FOUND:
📝 RECOMMENDATION: UPDATE (patch fixes) (severity 30/100)
→ 4 violations (moderate)
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/stress-and-intonation-audit.log for details)
⚠️  RAG verification found unverified words (see audit report)
--- VESUM WORD VERIFICATION FAILURES ---
These words were NOT found in the VESUM morphological dictionary.
Check if they are valid Ukrainian forms. Fix misspellings or Russianisms.
  ❌ `да` (source: prose)
  ❌ `ка` (source: prose)
  ❌ `шко` (source: prose)
```

---

## File Contents

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/stress-and-intonation.md`

```markdown
You've learned all the letters of the Ukrainian alphabet, and you can break words into syllables. Now it's time to discover the **music** of Ukrainian — where to place the beat in a word, and how your voice rises and falls in a sentence.

By the end of this module, you'll be able to spot the stressed syllable in common words, understand why stress matters so much in Ukrainian, and use the right melody for statements, questions, and exclamations.

## Наголос — Stress

Every Ukrainian word has one syllable that you say a little louder and longer than the others. This emphasis is called **наго́лос** (stress). In English, you already do this naturally — think of the difference between *REcord* (a noun) and *reCORD* (a verb). Ukrainian works the same way, but with an important twist.

In some languages, stress follows a predictable pattern. Polish puts the stress on the second-to-last syllable, almost without exception. French stresses the final syllable. Ukrainian has no such rule. Stress in Ukrainian is **free** — it can land on any syllable of the word. There is no shortcut, no formula. You simply learn the stress for each word when you learn the word itself.

Why does this matter? Because in Ukrainian, stress can change the meaning of a word entirely. Look at these two words — they are spelled with the exact same letters:

- **за́мок** — a castle
- **замо́к** — a lock

Same spelling, completely different meanings. Here's another pair:

- **му́ка** — torment, suffering
- **мука́** — flour

<!-- adapted from: Avramenko, Grade 5, p.88 — замок minimal pair exercise -->

If you stress the wrong syllable, you might say «flour» when you mean «torment» — or talk about a lock when you mean a castle! These word pairs are called **minimal pairs** — words that differ only in stress placement.

[!tip] **How to read stress marks**
In Ukrainian dictionaries and textbooks, stress is shown with an accent mark (´) over the stressed vowel: **вода́**, **мо́лодь**, **за́мок**. Whenever you look up a new word, pay attention to this little mark — it tells you exactly where to place the beat.

Here's your most important strategy as a learner: when you encounter a new Ukrainian word, **always check where the stress falls**. Don't guess from the spelling — Ukrainian spelling does not reveal the stress. Look it up in a dictionary, practice reading the dictionary entry with its stress mark, listen to it, and say it out loud a few times.

<!-- adapted from: Vashulenko, Grade 2, p.16 — "Щоб запам'ятати наголос у слові, правильно проговори його кілька разів." -->

[!note] **Stress mark reminder**
You already know that Ukrainian vowels are always pronounced clearly and fully, whether stressed or not. There is no vowel reduction like there is in English. But the stressed vowel is still louder and slightly longer — that's how a listener knows which syllable carries the **наго́лос**.

## Типові наголоси — Common Stress Patterns

While there is no single rule for Ukrainian stress, you'll start to notice tendencies as your vocabulary grows. Let's look at three common patterns.

**First-syllable stress** appears in many basic, everyday words — especially short family and household words you already know:

- **ма́ма** — mom
- **та́то** — dad
- **ха́та** — house
- **ка́ва** — coffee
- **до́брий** — good

You've been saying **ма́ма** and **та́то** since your very first module. The stress sits right on the first syllable — nice and comfortable.

**Last-syllable stress** is common in longer words and some verb forms:

- **молоко́** — milk
- **далеко́** — far
- **вода́** — water
- **мука́** — flour
- **говорю́** — I speak

Notice how all four words end with the stress on the very last syllable. This pattern is especially frequent in three-syllable words.

**Penultimate stress** (second-to-last syllable) shows up frequently in two- and three-syllable words:

- **шко́ла** — school
- **кни́жка** — book
- **доро́га** — road

Here's the tricky part: the same ending can carry different stress. Both **кни́га** (book) and **вода́** (water) end in **-а**, but the stress falls on different syllables. Both **шко́ла** and **далеко́** have an **о**, but the stress is in different places. This is why you cannot predict stress from spelling alone — you must learn it word by word.

[!practice] **Quick check**
Look at these words you already know. Can you feel where the stress falls?
- **мо́локо** — no! It's **молоко́** (last syllable)
- **ка́ва** — yes! First syllable
- **шко́ла** — yes! First syllable (penultimate in two syllables)

## Рухомий наголос — Mobile Stress

Here's something fascinating about Ukrainian stress — it doesn't just vary between different words. It can actually **move within the same word** when the word changes form. This is called **mobile stress**.

You haven't learned word forms yet (that's coming soon with cases and verb conjugation), but let's preview this concept so you're prepared.

Take the word **рука́** (hand, arm). When you use it in a different form, the stress shifts:

- **рука́** — hand (basic form)
- **ру́ки** — hands (plural form)

The stress jumped from the last syllable to the first! The word didn't change much in its letters, but the beat moved.

The same thing happens with other everyday words. Take **сестра́** (sister):

- **сестра́** — sister (one)
- **се́стри** — sisters (more than one)

The stress jumped from the last syllable to the first! You'll see these mobile stress patterns often as you learn more words.

[!tip] **Don't worry — awareness is the goal**
You don't need to memorize all stress shifts right now. When you start learning cases and verb conjugation in future modules, you'll practice these patterns step by step. For now, just know that stress can move — and that's completely normal in Ukrainian.

The best way to internalize mobile stress patterns is by **listening to native speakers**. Pay attention to how they pronounce words in different forms. Your ear will start picking up the patterns naturally, even before you learn the grammar rules. Every time you hear a word like **вода́**, try repeating it out loud: **вода́**. Then later, when you hear **во́ди** (of water), notice how the stress shifted. This kind of active listening is your secret weapon.

[!culture] **Ukrainian castles**
Remember **за́мок** (castle)? Ukraine has stunning medieval castles — the fortress at Кам'яне́ць-Поді́льський and the Оле́ський за́мок are among the most famous. When Ukrainians talk about their castles, they always say **за́мок** with stress on the first syllable. If they mean the lock on their door, it's **замо́к** — stress on the last syllable.

## Інтонація — Intonation

Now let's move from individual words to whole sentences. **Інтона́ція** (intonation) is the melody of a sentence — how your pitch rises and falls as you speak.

Ukrainian has four basic intonation patterns that you'll use every **день** (day). Let's explore them using one simple phrase: **Це кафе́** (This is a café).

**Declarative (statement):** Your pitch gently falls at the end of the sentence.

> **Це кафе́.** ↘

You're simply stating a fact — that's a café. Your voice goes down at the end, like a calm landing. This is the same pattern you use in English for statements.

**Question with a question word:** Your pitch rises on the question word, then falls.

> **Де кафе́?** ↗↘

The word **де** (where) gets a little lift, and then your voice settles down. The **пита́ння** (question) word carries the main energy.

**Yes/no question (without a question word):** Your pitch rises sharply at the end.

> **Це кафе́?** ↗

This is the trickiest pattern for English speakers! In English, most questions rise at the end. In Ukrainian, only yes/no questions do this. The **відпо́відь** (answer) to this kind of question is **так** or **ні**.

**Exclamatory:** Your voice rises with strong emphasis.

> **Це кафе́!** ↗!

You're surprised or excited — maybe you've found your favorite café! The pitch rises with energy and emotion.

[!warning] **Common English-speaker mistake**
English speakers tend to raise their pitch at the end of *all* questions. In Ukrainian, only yes/no questions rise at the end. When you use a question word like **де** or **що**, the pitch rises on that word and then **falls**. Practice this contrast — it makes a big difference in how natural you sound.

Let's practice all four patterns with another sentence. Try reading each one out loud, paying attention to your pitch:

> **Це шко́ла.** ↘ (statement: This is a school.)
> **Де шко́ла?** ↗↘ (question with question word: Where is the school?)
> **Це шко́ла?** ↗ (yes/no question: Is this a school?)
> **Це шко́ла!** ↗! (exclamation: This is a school! / What a school!)

<!-- adapted from: Vashulenko, Grade 2, p.108-116 — intonation of different sentence types -->

And one more set with a word you know well — try saying «**до́брий ра́нок**» (good morning) as:

> **До́брий ра́нок.** ↘ (a calm greeting)
> **До́брий ра́нок?** ↗ (is it really a good morning?)
> **До́брий ра́нок!** ↗! (an enthusiastic greeting)

[!practice] **Contrast drill**
Read this phrase three ways. Feel how your voice changes each time:
1. **Це молоко́.** ↘ — You're pointing at milk on the table.
2. **Це молоко́?** ↗ — You're not sure if it's milk.
3. **Це молоко́!** ↗! — You're excited to see milk!

## Практика — Practice

You've learned a lot! Let's put it all together with some practice.

**Stress placement:** Read each word out loud and tap the table on the stressed syllable:

- **вода́** (tap on -да́)
- **шко́ла** (tap on шко́-)
- **молоко́** (tap on -ко́)
- **до́брий** (tap on до́-)
- **далеко́** (tap on -ко́)
- **рука́** (tap on -ка́)

**Minimal pairs:** Say both words in each pair. Can you hear the difference?

- **за́мок** (castle) — **замо́к** (lock)
- **му́ка** (torment) — **мука́** (flour)

**Intonation reading:** Read each sentence with the correct melody:

> **Це вода́.** ↘
> **Де вода́?** ↗↘
> **Це вода́?** ↗
> **Це вода́!** ↗!

Great job making it through all these exercises! Remember, you don't need to be perfect right away. Every time you practice, your ear and your voice get a little bit better.

## Підсумок — Summary

You've just unlocked the music of Ukrainian! Here's what you now know:

- Ukrainian **наго́лос** (stress) is **free** — it can fall on any syllable — and **mobile** — it can shift when a word changes form.
- Stress changes meaning: **за́мок** (castle) vs **замо́к** (lock).
- Ukrainian vowels stay clear and pure whether stressed or not — no mumbling!
- **Інтона́ція** (intonation) gives sentences their melody: pitch falls for statements ↘, rises at the end for yes/no questions ↗, and rises on the question word for wh-questions ↗↘.

**Self-check — test yourself:**

1. Where is the stress in **вода́**? (Answer: last syllable)
2. What happens to vowel quality when a vowel is unstressed? (Answer: nothing — Ukrainian vowels stay clear)
3. How does **Це кафе́?** ↗ differ from **Де кафе́?** ↗↘?

**Coming up next:** In Module 7, you'll learn your first greetings and basic phrases — **до́брий день**, **як спра́ви**, and more. The stress and intonation skills you've built here will help you sound natural from your very first conversation!
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/stress-and-intonation.yaml`

```yaml
- type: quiz
  title: Where Does the Stress Fall?
  instruction: Choose the syllable that carries the stress in each word.
  items:
  - question: Where is the stress in the word вода (water)?
    options:
    - text: First syllable (во-)
      correct: false
    - text: Last syllable (-да)
      correct: true
    - text: Both syllables equally
      correct: false
    - text: Ukrainian words have no stress
      correct: false
    explanation: 'Вода has last-syllable stress: вода́.'
  - question: Where is the stress in the word мама (mom)?
    options:
    - text: First syllable (ма-)
      correct: true
    - text: Last syllable (-ма)
      correct: false
    - text: Both syllables equally
      correct: false
    - text: It changes every time
      correct: false
    explanation: 'Мама has first-syllable stress: ма́ма.'
  - question: Where is the stress in the word молоко (milk)?
    options:
    - text: First syllable (мо-)
      correct: false
    - text: Second syllable (-ло-)
      correct: false
    - text: Last syllable (-ко)
      correct: true
    - text: Second and third equally
      correct: false
    explanation: 'Молоко has last-syllable stress: молоко́.'
  - question: Where is the stress in the word школа (school)?
    options:
    - text: First syllable (шко-)
      correct: true
    - text: Last syllable (-ла)
      correct: false
    - text: Both syllables equally
      correct: false
    - text: There is no stress
      correct: false
    explanation: 'Школа has first-syllable stress (penultimate): шко́ла.'
  - question: Where is the stress in the word далеко (far)?
    options:
    - text: First syllable (да-)
      correct: false
    - text: Second syllable (-ле-)
      correct: false
    - text: Last syllable (-ко)
      correct: true
    - text: First and last equally
      correct: false
    explanation: 'Далеко has last-syllable stress: далеко́.'
  - question: Where is the stress in the word добрий (good)?
    options:
    - text: First syllable (до-)
      correct: true
    - text: Last syllable (-рий)
      correct: false
    - text: Both syllables
      correct: false
    - text: No stress in this word
      correct: false
    explanation: 'Добрий has first-syllable stress: до́брий.'
  - question: Where is the stress in the word книжка (book)?
    options:
    - text: Last syllable (-ка)
      correct: false
    - text: First syllable (кни-)
      correct: true
    - text: Both syllables equally
      correct: false
    - text: The middle sound -ж-
      correct: false
    explanation: 'Книжка has first-syllable stress: кни́жка.'
  - question: Where is the stress in the word рука (hand)?
    options:
    - text: First syllable (ру-)
      correct: false
    - text: Last syllable (-ка)
      correct: true
    - text: Both equally
      correct: false
    - text: It has no stress
      correct: false
    explanation: 'Рука has last-syllable stress: рука́.'
  - question: Where is the stress in the word дорога (road)?
    options:
    - text: First syllable (до-)
      correct: false
    - text: Second syllable (-ро-)
      correct: true
    - text: Last syllable (-га)
      correct: false
    - text: First and second equally
      correct: false
    explanation: 'Дорога has penultimate stress: доро́га.'
  - question: Where is the stress in the word кава (coffee)?
    options:
    - text: First syllable (ка-)
      correct: true
    - text: Last syllable (-ва)
      correct: false
    - text: Both equally
      correct: false
    - text: No stress in short words
      correct: false
    explanation: 'Кава has first-syllable stress: ка́ва.'
  - question: Where is the stress in the word хата (house)?
    options:
    - text: Last syllable (-та)
      correct: false
    - text: First syllable (ха-)
      correct: true
    - text: Both syllables
      correct: false
    - text: It depends on the sentence
      correct: false
    explanation: 'Хата has first-syllable stress: ха́та.'
  - question: Where is the stress in the word тато (dad)?
    options:
    - text: First syllable (та-)
      correct: true
    - text: Last syllable (-то)
      correct: false
    - text: Both equally
      correct: false
    - text: No fixed stress
      correct: false
    explanation: 'Тато has first-syllable stress: та́то.'
- type: match-up
  title: Stress Minimal Pairs
  instruction: Match each stressed word to its correct English meaning. Pay attention
    to where the stress falls!
  pairs:
  - left: за́мок (stress on ЗА-)
    right: castle
  - left: замо́к (stress on -МОК)
    right: lock
  - left: му́ка (stress on МУ-)
    right: torment
  - left: мука́ (stress on -КА)
    right: flour
  - left: рука́ (stress on -КА)
    right: hand (singular)
  - left: ру́ки (stress on РУ-)
    right: hands (plural)
  - left: писа́ти (stress on -СА-)
    right: to write
  - left: пишу́ (stress on -ШУ)
    right: I write
- type: true-false
  title: Stress and Intonation Facts
  instruction: Decide whether each statement about Ukrainian stress and intonation
    is true or false.
  items:
  - statement: In Ukrainian, stress always falls on the first syllable of a word.
    correct: false
    explanation: Ukrainian stress is free — it can fall on any syllable. There is
      no fixed rule.
  - statement: The words за́мок (castle) and замо́к (lock) are spelled with the same
      letters but have different stress.
    correct: true
    explanation: These are stress minimal pairs — same spelling, different stress,
      different meaning.
  - statement: When you say a yes/no question in Ukrainian, your pitch rises at the
      end.
    correct: true
    explanation: Yes/no questions (without a question word) use rising intonation
      at the end.
  - statement: When you ask a question with де (where), your pitch rises at the end
      of the sentence.
    correct: false
    explanation: With a question word like де, the pitch rises on the question word
      and then falls.
  - statement: Ukrainian stress can move to a different syllable when a word changes
      form.
    correct: true
    explanation: This is called mobile stress. For example, рука́ becomes ру́ки in
      the plural.
  - statement: In a Ukrainian statement, your pitch rises at the end of the sentence.
    correct: false
    explanation: In statements, pitch gently falls at the end — like a calm landing.
  - statement: Unstressed Ukrainian vowels become unclear and mumbled, like in English.
    correct: false
    explanation: Ukrainian vowels stay clear and pure whether stressed or not — there
      is no vowel reduction.
  - statement: You can always predict Ukrainian stress from the spelling of a word.
    correct: false
    explanation: You cannot predict stress from spelling. Words like кни́га and вода́
      both end in -а but have different stress.
- type: fill-in
  title: Choose the Correct Stress
  instruction: Select the word with the stress mark on the correct syllable.
  items:
  - sentence: The word for 'water' with correct stress is ___.
    answer: вода́
    options:
    - во́да
    - вода́
    - вод́а
    - вода
    explanation: 'Вода has stress on the last syllable: вода́.'
  - sentence: The word for 'castle' with correct stress is ___.
    answer: за́мок
    options:
    - за́мок
    - замо́к
    - замоќ
    - замок
    explanation: Castle is за́мок with stress on the first syllable. Замо́к means
      lock.
  - sentence: The word for 'lock' with correct stress is ___.
    answer: замо́к
    options:
    - за́мок
    - замо́к
    - замоќ
    - замок
    explanation: Lock is замо́к with stress on the last syllable. За́мок means castle.
  - sentence: The word for 'milk' with correct stress is ___.
    answer: молоко́
    options:
    - мо́локо
    - моло́ко
    - молоко́
    - молоко
    explanation: 'Молоко has stress on the last syllable: молоко́.'
  - sentence: The word for 'school' with correct stress is ___.
    answer: шко́ла
    options:
    - шко́ла
    - школа́
    - школ́а
    - школа
    explanation: 'Школа has stress on the first syllable: шко́ла.'
  - sentence: The word for 'flour' with correct stress is ___.
    answer: мука́
    options:
    - му́ка
    - мука́
    - муќа
    - мука
    explanation: Flour is мука́ with stress on the last syllable. Му́ка means torment.
  - sentence: The word for 'coffee' with correct stress is ___.
    answer: ка́ва
    options:
    - ка́ва
    - кава́
    - кав́а
    - кава
    explanation: 'Кава has stress on the first syllable: ка́ва.'
  - sentence: The word for 'good' with correct stress is ___.
    answer: до́брий
    options:
    - до́брий
    - добри́й
    - добрий́
    - добрий
    explanation: 'Добрий has stress on the first syllable: до́брий.'
  - sentence: The word for 'far' with correct stress is ___.
    answer: далеко́
    options:
    - да́леко
    - дале́ко
    - далеко́
    - далеко
    explanation: 'Далеко has stress on the last syllable: далеко́.'
  - sentence: The word for 'road' with correct stress is ___.
    answer: доро́га
    options:
    - до́рога
    - доро́га
    - дорога́
    - дорога
    explanation: 'Дорога has stress on the second syllable: доро́га.'
- type: group-sort
  title: Sort Words by Stress Position
  instruction: Sort these words into groups based on which syllable carries the stress.
  groups:
  - name: First-syllable stress
    items:
    - ма́ма
    - та́то
    - ха́та
    - ка́ва
    - до́брий
  - name: Last-syllable stress
    items:
    - вода́
    - молоко́
    - далеко́
    - рука́
    - мука́
- type: quiz
  title: Intonation Patterns
  instruction: Choose the correct intonation pattern for each sentence type.
  items:
  - question: You say 'Це кафе.' as a simple statement. What does your pitch do?
    options:
    - text: Rises at the end
      correct: false
    - text: Falls at the end
      correct: true
    - text: Stays flat
      correct: false
    - text: Rises then falls then rises
      correct: false
    explanation: Statements use falling intonation at the end.
  - question: You ask 'Це кафе?' (Is this a cafe?) — a yes/no question. What does
      your pitch do?
    options:
    - text: Falls at the end
      correct: false
    - text: Stays flat
      correct: false
    - text: Rises sharply at the end
      correct: true
    - text: Falls then rises then falls
      correct: false
    explanation: Yes/no questions (without a question word) rise at the end.
  - question: You ask 'Де кафе?' (Where is the cafe?) with a question word. What does
      your pitch do?
    options:
    - text: Rises at the end
      correct: false
    - text: Rises on де, then falls
      correct: true
    - text: Falls the whole time
      correct: false
    - text: Stays flat throughout
      correct: false
    explanation: Questions with a question word rise on the question word, then fall.
  - question: You exclaim 'Це кафе!' with excitement. What does your pitch do?
    options:
    - text: Falls at the end
      correct: false
    - text: Stays flat
      correct: false
    - text: Falls then rises
      correct: false
    - text: Rises with strong emphasis
      correct: true
    explanation: Exclamations use rising pitch with energy and emphasis.
  - question: How is the intonation of 'Це школа?' different from 'Де школа?'
    options:
    - text: They use the same intonation
      correct: false
    - text: '''Це школа?'' rises at the end; ''Де школа?'' rises on де then falls'
      correct: true
    - text: '''Це школа?'' falls at the end; ''Де школа?'' rises at the end'
      correct: false
    - text: Both fall at the end
      correct: false
    explanation: Yes/no questions rise at the end. Questions with a question word
      rise on the question word and then fall.
  - question: An English speaker raises their pitch at the end of every question.
      Is this correct for Ukrainian?
    options:
    - text: Yes, Ukrainian works the same as English
      correct: false
    - text: No — only yes/no questions rise at the end in Ukrainian
      correct: true
    - text: No — Ukrainian questions always fall
      correct: false
    - text: No — Ukrainian has no intonation patterns
      correct: false
    explanation: In Ukrainian, only yes/no questions rise at the end. Questions with
      a question word rise on the question word then fall.
- type: anagram
  title: Unscramble the Word
  instruction: Rearrange the letters to form a Ukrainian word from this lesson.
  items:
  - scrambled: о д а в
    answer: вода
  - scrambled: о к о л о м
    answer: молоко
  - scrambled: а л о к ш
    answer: школа
  - scrambled: а к у р
    answer: рука
  - scrambled: а г о р о д
    answer: дорога
  - scrambled: а в а к
    answer: кава

```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/stress-and-intonation.yaml`

```yaml
items:
  - lemma: "замок"
    translation: "castle (за́мок) / lock (замо́к)"
    pos: "noun"
    gender: "m"
    notes: "Stress minimal pair — different stress changes meaning entirely"
    usage: "за́мок = castle, замо́к = lock"
  - lemma: "вода"
    translation: "water"
    pos: "noun"
    gender: "f"
    notes: "Last-syllable stress: вода́"
    example: "Це вода́."
  - lemma: "рука"
    translation: "hand, arm"
    pos: "noun"
    gender: "f"
    notes: "Mobile stress: рука́ (singular) → ру́ки (plural)"
  - lemma: "писати"
    translation: "to write"
    pos: "verb"
    aspect: "imperfective"
    notes: "Mobile stress: писа́ти → пишу́ → пи́шеш"
  - lemma: "школа"
    translation: "school"
    pos: "noun"
    gender: "f"
    notes: "Penultimate stress: шко́ла"
  - lemma: "молоко"
    translation: "milk"
    pos: "noun"
    gender: "n"
    notes: "Last-syllable stress: молоко́"
  - lemma: "добрий"
    translation: "good"
    pos: "adjective"
    notes: "First-syllable stress: до́брий"
    example: "До́брий день."
  - lemma: "далеко"
    translation: "far"
    pos: "adverb"
    notes: "Last-syllable stress: далеко́"
  - lemma: "наголос"
    translation: "stress, accent"
    pos: "noun"
    gender: "m"
    notes: "Metalinguistic term for word stress"
  - lemma: "інтонація"
    translation: "intonation"
    pos: "noun"
    gender: "f"
    notes: "Metalinguistic term for sentence melody"
  - lemma: "питання"
    translation: "question"
    pos: "noun"
    gender: "n"
    notes: "High-frequency word"
  - lemma: "відповідь"
    translation: "answer"
    pos: "noun"
    gender: "f"
    notes: "High-frequency word"
  - lemma: "мука"
    translation: "flour (мука́) / torment (му́ка)"
    pos: "noun"
    gender: "f"
    notes: "Stress minimal pair — different stress changes meaning"
  - lemma: "мама"
    translation: "mom"
    pos: "noun"
    gender: "f"
    notes: "First-syllable stress: ма́ма"
  - lemma: "тато"
    translation: "dad"
    pos: "noun"
    gender: "m"
    notes: "First-syllable stress: та́то"
  - lemma: "хата"
    translation: "house"
    pos: "noun"
    gender: "f"
    notes: "First-syllable stress: ха́та"
  - lemma: "кава"
    translation: "coffee"
    pos: "noun"
    gender: "f"
    notes: "First-syllable stress: ка́ва"
  - lemma: "книжка"
    translation: "book"
    pos: "noun"
    gender: "f"
    notes: "First-syllable stress: кни́жка"
  - lemma: "дорога"
    translation: "road"
    pos: "noun"
    gender: "f"
    notes: "Penultimate stress: доро́га"
  - lemma: "кафе"
    translation: "cafe"
    pos: "noun"
    gender: "n"
    notes: "Used in intonation examples: Це кафе́."
```

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
  [gemini] attempt 1/5, model=gemini-3.1-pro-preview, prompt=36125 chars: You are Gemini, participating in a collaboration with Claude. This is a message from Claude to you:  --- # Gemini Review Fix: Targeted Repair via FIND/REPLACE  > **You are an expert Ukrainian language...
```

  [watchdog] Output resumed after 296s stall
===SECTION_FIX_START===
FILE: curriculum/l2-uk-en/a1/stress-and-intonation.md
FIND:
**First-syllable stress** appears in many basic, everyday words — especially short family and household words you already know:

- **ма́ма** — mom
- **та́то** — dad
- **ха́та** — house
- **ка́ва** — coffee
- **до́брий** — good

You've been saying **ма́ма** and **та́то** since your very first module. The stress sits right on the first syllable — nice and comfortable.

**Last-syllable stress** is common in longer words and some verb forms:

- **молоко́** — milk
- **далеко́** — far
- **вода́** — water
- **мука́** — flour
- **говорю́** — I speak

Notice how all four words end with the stress on the very last syllable. This pattern is especially frequent in three-syllable words.

**Penultimate stress** (second-to-last syllable) shows up frequently in two- and three-syllable words:

- **шко́ла** — school
- **кни́жка** — book
- **доро́га** — road

Here's the tricky part: the same ending can carry different stress.
REPLACE:
| Pattern | Description | Examples |
| :--- | :--- | :--- |
| **First-syllable stress** | Common in basic, everyday words | **ма́ма** (mom), **та́то** (dad), **ха́та** (house), **ка́ва** (coffee), **до́брий** (good) |
| **Last-syllable stress** | Common in longer words | **молоко́** (milk), **далеко́** (far), **вода́** (water), **мука́** (flour) |
| **Penultimate stress** | Frequent in two- and three-syllable words | **шко́ла** (school), **кни́жка** (book), **доро́га** (road) |

You've been saying **ма́ма** and **та́то** since your very first module. The stress sits right on the first syllable — nice and comfortable. Notice how words like **молоко́** and **вода́** end with the stress on the very last syllable. This pattern is especially frequent in three-syllable words.

Here's the tricky part: the same ending can carry different stress.
---
FILE: curriculum/l2-uk-en/a1/activities/stress-and-intonation.yaml
FIND:
  - question: Where is the stress in the word вода (water)?
    options:
    - text: First syllable (во-)
      correct: false
    - text: Last syllable (-да)
      correct: true
    - text: Both syllables equally
      correct: false
    - text: Ukrainian words have no stress
      correct: false
    explanation: 'Вода has last-syllable stress: вода́.'
  - question: Where is the stress in the word мама (mom)?
    options:
    - text: First syllable (ма-)
      correct: true
    - text: Last syllable (-ма)
      correct: false
    - text: Both syllables equally
      correct: false
    - text: It changes every time
      correct: false
    explanation: 'Мама has first-syllable stress: ма́ма.'
  - question: Where is the stress in the word молоко (milk)?
    options:
    - text: First syllable (мо-)
      correct: false
    - text: Second syllable (-ло-)
      correct: false
    - text: Last syllable (-ко)
      correct: true
    - text: Second and third equally
      correct: false
    explanation: 'Молоко has last-syllable stress: молоко́.'
  - question: Where is the stress in the word школа (school)?
    options:
    - text: First syllable (шко-)
      correct: true
    - text: Last syllable (-ла)
      correct: false
    - text: Both syllables equally
      correct: false
    - text: There is no stress
      correct: false
    explanation: 'Школа has first-syllable stress (penultimate): шко́ла.'
  - question: Where is the stress in the word далеко (far)?
    options:
    - text: First syllable (да-)
      correct: false
    - text: Second syllable (-ле-)
      correct: false
    - text: Last syllable (-ко)
      correct: true
    - text: First and last equally
      correct: false
    explanation: 'Далеко has last-syllable stress: далеко́.'
  - question: Where is the stress in the word добрий (good)?
    options:
    - text: First syllable (до-)
      correct: true
    - text: Last syllable (-рий)
      correct: false
    - text: Both syllables
      correct: false
    - text: No stress in this word
      correct: false
    explanation: 'Добрий has first-syllable stress: до́брий.'
  - question: Where is the stress in the word книжка (book)?
    options:
    - text: Last syllable (-ка)
      correct: false
    - text: First syllable (кни-)
      correct: true
    - text: Both syllables equally
      correct: false
    - text: The middle sound -ж-
      correct: false
    explanation: 'Книжка has first-syllable stress: кни́жка.'
  - question: Where is the stress in the word рука (hand)?
    options:
    - text: First syllable (ру-)
      correct: false
    - text: Last syllable (-ка)
      correct: true
    - text: Both equally
      correct: false
    - text: It has no stress
      correct: false
    explanation: 'Рука has last-syllable stress: рука́.'
  - question: Where is the stress in the word дорога (road)?
    options:
    - text: First syllable (до-)
      correct: false
    - text: Second syllable (-ро-)
      correct: true
    - text: Last syllable (-га)
      correct: false
    - text: First and second equally
      correct: false
    explanation: 'Дорога has penultimate stress: доро́га.'
  - question: Where is the stress in the word кава (coffee)?
    options:
    - text: First syllable (ка-)
      correct: true
    - text: Last syllable (-ва)
      correct: false
    - text: Both equally
      correct: false
    - text: No stress in short words
      correct: false
    explanation: 'Кава has first-syllable stress: ка́ва.'
  - question: Where is the stress in the word хата (house)?
    options:
    - text: Last syllable (-та)
      correct: false
    - text: First syllable (ха-)
      correct: true
    - text: Both syllables
      correct: false
    - text: It depends on the sentence
      correct: false
    explanation: 'Хата has first-syllable stress: ха́та.'
  - question: Where is the stress in the word тато (dad)?
    options:
    - text: First syllable (та-)
      correct: true
    - text: Last syllable (-то)
      correct: false
    - text: Both equally
      correct: false
    - text: No fixed stress
      correct: false
    explanation: 'Тато has first-syllable stress: та́то.'
REPLACE:
  - question: Where is the stress in the word вода (water)?
    options:
    - text: First syllable
      correct: false
    - text: Last syllable
      correct: true
    - text: Both syllables equally
      correct: false
    - text: Ukrainian words have no stress
      correct: false
    explanation: 'Вода has last-syllable stress: вода́.'
  - question: Where is the stress in the word мама (mom)?
    options:
    - text: First syllable
      correct: true
    - text: Last syllable
      correct: false
    - text: Both syllables equally
      correct: false
    - text: It changes every time
      correct: false
    explanation: 'Мама has first-syllable stress: ма́ма.'
  - question: Where is the stress in the word молоко (milk)?
    options:
    - text: First syllable
      correct: false
    - text: Second syllable
      correct: false
    - text: Last syllable
      correct: true
    - text: Second and third equally
      correct: false
    explanation: 'Молоко has last-syllable stress: молоко́.'
  - question: Where is the stress in the word школа (school)?
    options:
    - text: First syllable
      correct: true
    - text: Last syllable
      correct: false
    - text: Both syllables equally
      correct: false
    - text: There is no stress
      correct: false
    explanation: 'Школа has first-syllable stress (penultimate): шко́ла.'
  - question: Where is the stress in the word далеко (far)?
    options:
    - text: First syllable
      correct: false
    - text: Second syllable
      correct: false
    - text: Last syllable
      correct: true
    - text: First and last equally
      correct: false
    explanation: 'Далеко has last-syllable stress: далеко́.'
  - question: Where is the stress in the word добрий (good)?
    options:
    - text: First syllable
      correct: true
    - text: Last syllable
      correct: false
    - text: Both syllables
      correct: false
    - text: No stress in this word
      correct: false
    explanation: 'Добрий has first-syllable stress: до́брий.'
  - question: Where is the stress in the word книжка (book)?
    options:
    - text: Last syllable
      correct: false
    - text: First syllable
      correct: true
    - text: Both syllables equally
      correct: false
    - text: The middle sound -ж-
      correct: false
    explanation: 'Книжка has first-syllable stress: кни́жка.'
  - question: Where is the stress in the word рука (hand)?
    options:
    - text: First syllable
      correct: false
    - text: Last syllable
      correct: true
    - text: Both equally
      correct: false
    - text: It has no stress
      correct: false
    explanation: 'Рука has last-syllable stress: рука́.'
  - question: Where is the stress in the word дорога (road)?
    options:
    - text: First syllable
      correct: false
    - text: Second syllable
      correct: true
    - text: Last syllable
      correct: false
    - text: First and second equally
      correct: false
    explanation: 'Дорога has penultimate stress: доро́га.'
  - question: Where is the stress in the word кава (coffee)?
    options:
    - text: First syllable
      correct: true
    - text: Last syllable
      correct: false
    - text: Both equally
      correct: false
    - text: No stress in short words
      correct: false
    explanation: 'Кава has first-syllable stress: ка́ва.'
  - question: Where is the stress in the word хата (house)?
    options:
    - text: Last syllable
      correct: false
    - text: First syllable
      correct: true
    - text: Both syllables
      correct: false
    - text: It depends on the sentence
      correct: false
    explanation: 'Хата has first-syllable stress: ха́та.'
  - question: Where is the stress in the word тато (dad)?
    options:
    - text: First syllable
      correct: true
    - text: Last syllable
      correct: false
    - text: Both equally
      correct: false
    - text: No fixed stress
      correct: false
    explanation: 'Тато has first-syllable stress: та́то.'
---
FILE: curriculum/l2-uk-en/a1/activities/stress-and-intonation.yaml
FIND:
  - left: писа́ти (stress on -СА-)
    right: to write
  - left: пишу́ (stress on -ШУ)
    right: I write
REPLACE:
  - left: сестра́ (stress on -РА)
    right: sister
  - left: се́стри (stress on СЕС-)
    right: sisters
---
FILE: curriculum/l2-uk-en/a1/vocabulary/stress-and-intonation.yaml
FIND:
  - lemma: "писати"
    translation: "to write"
    pos: "verb"
    aspect: "imperfective"
    notes: "Mobile stress: писа́ти → пишу́ → пи́шеш"
REPLACE:
  - lemma: "сестра"
    translation: "sister"
    pos: "noun"
    gender: "f"
    notes: "Mobile stress: сестра́ → се́стри"
===SECTION_FIX_END===

===FRICTION_START===
**Phase**: Gemini Review Fix
**Step**: Executing FIND/REPLACE fixes from Claude's review plan
**Friction Type**: TEXT_NOT_FOUND
**Raw Error**: Finding 2 ("or Russian") and Finding 3 ("Де́") from the Review Plan were not present in the provided file contents. Similarly, the prose reference to "писа́ти" in Finding 1 was already absent (replaced by "сестра́") in the provided markdown file.
**Self-Correction**: I skipped Findings 2 and 3 and only applied the "писа́ти" replacement to the activities and vocabulary where it was still present.
**Proposed Tooling Fix**: N/A
===FRICTION_END===
```


────────────────────────────────────────
✅ Gemini finished (11424 chars)
✅ Message sent to Claude (ID: 26372)
✓ Message 26372 acknowledged
   Auto-acknowledged reply #26372 (stdout delivery — no inbox accumulation)
   📎 Review posted as new issue #958 (1 part)
✓ Message 26371 acknowledged
