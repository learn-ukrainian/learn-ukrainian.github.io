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

## Review Findings (targeted fix required)

**CONSTRAINTS:**
- Fix ONLY the issues listed below
- Do NOT rewrite surrounding text
- Preserve word count and structure
- Only modify these sections: Line 72, Section "Інтонація — Intonation", Whole module

### Finding 1: Wrong Stress on відповідь (HIGH — Linguistic Accuracy)
**Location**: Line 72, Section "Інтонація — Intonation"
**Problem**: The stress mark is placed on the second syllable (відпо́відь). The correct stress is on the first syllable: **ві́дповідь**. Confirmed by pre-screen D.0 STRESS_MISMATCH and ukrainian-word-stress dictionary.
**Required Fix**: Replace `**відпо́відь**` with `**ві́дповідь**`
**Severity**: HIGH

### Finding 2: Zero Engagement Boxes (MEDIUM — Experience Quality / Richness)
**Location**: Whole module
**Problem**: Audit gate requires minimum 1 engagement box for A1. The richness score shows `engagement: 0/2`. The замок/castle cultural hook from research notes (Кам'янець-Подільський, Олеський замок) and the textbook poem reference are natural candidates for callout boxes.
**Required Fix**: Add at least 2 callout boxes: (1) a `[!did-you-know]` after line 11 about Ukrainian castles tying зАмок to real geography, (2) a `[!tip]` in the intonation section about the yes/no question pitch pattern being the #1 mistake for English speakers.
**Severity**: HIGH

### Finding 3: Pre-Screen Stress Findings — Dismissals
**Severity**: HIGH

---

## Critical Issues Found

### Issue 1: Wrong Stress on відповідь (HIGH — Linguistic Accuracy)
- **Location**: Line 72, Section "Інтонація — Intonation"
- **Original**: 「When you are giving a simple **відпо́відь** (answer) or stating a clear fact, your pitch smoothly falls at the end of the sentence.」
- **Problem**: The stress mark is placed on the second syllable (відпо́відь). The correct stress is on the first syllable: **ві́дповідь**. Confirmed by pre-screen D.0 STRESS_MISMATCH and ukrainian-word-stress dictionary.
- **Fix**: Replace `**відпо́відь**` with `**ві́дповідь**`

### Issue 2: Zero Engagement Boxes (MEDIUM — Experience Quality / Richness)
- **Location**: Whole module
- **Original**: No `[!tip]`, `[!example]`, `[!cultural-note]`, `[!did-you-know]`, or similar callout boxes anywhere in the module.
- **Problem**: Audit gate requires minimum 1 engagement box for A1. The richness score shows `engagement: 0/2`. The замок/castle cultural hook from research notes (Кам'янець-Подільський, Олеський замок) and the textbook poem reference are natural candidates for callout boxes.
- **Fix**: Add at least 2 callout boxes: (1) a `[!did-you-know]` after line 11 about Ukrainian castles tying зАмок to real geography, (2) a `[!tip]` in the intonation section about the yes/no question pitch pattern being the #1 mistake for English speakers.

### Issue 3: Pre-Screen Stress Findings — Dismissals
- **[STRESS_UNKNOWN] за́мок, му́ка** (INFO): DISMISSED — Both are valid VESUM entries with homograph stress pairs. Not found in the stress dictionary because the dictionary may not index homographs separately, but the content usage is correct.
- **[STRESS_MISMATCH] пла́кати → плака́ти** (HIGH): DISMISSED — Line 110 presents a valid minimal pair: пла́кати (verb "to cry," VESUM lemma: плакати verb:imperf:inf) vs плака́ти (noun plural "posters," VESUM lemma: плакат noun:inanim:p:v_naz). Both stresses are correct for their respective words. The scanner flagged only the first occurrence without recognizing the pair context.

---

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 72 | 「**відпо́відь**」 | 「**ві́дповідь**」 | Stress error |

---

## Fix Plan to Reach 9/10 (REQUIRED — score is 8.1)

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. Line 72: Change 「**відпо́відь**」 → 「**ві́дповідь**」 — confirmed stress error

**Expected score after fix:** 9/10

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Add a `> [!did-you-know]` callout after line 11, using the castle cultural hook: зАмок connects to real Ukrainian castles like Кам'янець-Подільський.
2. Add a `> [!tip]` callout in section "Інтонація — Intonation" after line 81, highlighting that yes/no question intonation is the #1 English-speaker mistake.
3. Add a warm "You can now..." celebration before line 127's next-module preview.

**Expected score after fix:** 9/10

### Language: 8/10 → 9/10
**What to fix:**
1. Fix the відповідь stress error (same as Linguistic Accuracy fix above).

**Expected score after fix:** 9/10

### Pedagogy: 8/10 → 9/10
**What to fix:**
1. Adding the engagement boxes above addresses the pedagogical gap.

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.1 + 9×1.2 + 9×1.3 + 8×1.3 + 8×1.0 + 9×1.5) / 8.9
= (13.5 + 9.9 + 10.8 + 11.7 + 10.4 + 8.0 + 13.5) / 8.9
= 77.8 / 8.9 = 8.7/10
```

---

## Audit Failures (from automated re-audit)

```
⚠️ HYDRATION NOTE: Outline sums to 1300, exceeding word_target 1200
--- STRICT GATES (Level A1) ---
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/stress-and-intonation-audit.log for details)
--- VESUM WORD VERIFICATION FAILURES ---
These words were NOT found in the VESUM morphological dictionary.
Check if they are valid Ukrainian forms. Fix misspellings or Russianisms.
  ❌ `шко` (source: prose)
```

---

## File Contents (for reference)

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/stress-and-intonation.md`

```markdown
## Наголос — Stress

Welcome to the music of Ukrainian! When we talk about pronunciation and making your Ukrainian sound natural, one of the most important concepts to master is **на́голос** (stress or accent). In some languages, word stress is perfectly predictable and follows a strict geographic pattern. For example, if you have studied French, you know the stress almost always falls on the very last syllable. If you have learned Polish, it reliably lands on the penultimate (second-to-last) syllable. Because of this, learners from these backgrounds often try to force Ukrainian words into the same comfortable boxes.

However, Ukrainian is entirely different. Ukrainian stress is what linguists call "free." This means the **на́голос** can fall on literally any syllable of a content word—the beginning, the middle, or the end. There is no single fixed rule or mathematical formula that tells you where the stress goes just by looking at the written letters. (Note: tiny grammatical words, like short prepositions or conjunctions, typically lack stress entirely and just merge phonetically with the next word in the sentence).

Why does this free stress matter so much? Because in Ukrainian, stress changes meaning! The position of the stress carries a heavy functional load, meaning two words can be spelled exactly the same but mean completely different things depending solely on which syllable you emphasize. Let's look at some classic minimal pairs that demonstrate the functional load of stress:
- **за́мок** (castle) vs **замо́к** (lock)
- **му́ка** (torment) vs **мука́** (flour)

Imagine the confusion if you say **замо́к** when you mean to say **за́мок**! You might lead someone to believe you visited a beautiful ancient lock in the Carpathian mountains, rather than a historic stone castle. Stress is not just a stylistic decoration; it is a core part of the vocabulary.

> [!did-you-know]
> The word **за́мок** (castle) connects to real Ukrainian geography! Ukraine has stunning historic castles — like the fortress at **Кам'яне́ць-Поді́льський** and the Renaissance **Оле́ський за́мок** in western Ukraine. When you learn this word, you are learning a piece of Ukrainian landscape.

Because you cannot guess the stress from the spelling alone, how do you know where it goes? In Ukrainian dictionaries, textbooks, and throughout our learning materials, you will see how stress is clearly marked: we use the acute accent (´) placed directly over the stressed vowel. This small mark is your visual guide to the word's melody. Practicing reading dictionary entries early on will help you train your eye to catch these marks immediately. Also, remember our rule of vowel purity from previous lessons: all vowels stay pure and clear, but the stressed vowel is always pronounced with the most energy and slightly longer duration.

As your dedicated learner strategy, remember this golden rule: when encountering a new word, always check the stress placement immediately. Guessing from spelling will often be wrong, and unlearning a bad habit is much harder than learning it right the first time.
<!-- adapted from: Vashulenko, Grade 3 -->

## Типові наголоси — Common Stress Patterns

Even though Ukrainian stress is completely free, you will naturally start to notice some common stress patterns as you build your vocabulary. Recognizing these patterns won't give you a perfect rule, but it will help you feel the rhythm of the language. Let's explore where the **на́голос** typically lands in some of our everyday words.

**First-syllable stress:**
Many basic family, home, and household words have their stress placed firmly on the very first syllable. This creates a strong, clear start to the word. For example:
- **ма́ма** (mom)
- **та́то** (dad)
- **ха́та** (house)
- **ка́ва** (coffee)

You also already know the word **до́брий** (good), which has first-syllable stress, just like in our everyday greeting «**до́брий** день».

**Last-syllable stress:**
It is also very common, especially in longer words, to find the stress resting on the final syllable. This gives the word a rising, energetic finish. Common examples include:
- **молоко́** (milk)
- **Украї́на** (Ukraine)

*(Note: Be careful with the word **дале́ко** meaning "far". Many beginners mistakenly put the stress on the last syllable due to outside influences, but in Ukrainian, it actually belongs in the penultimate group!)*

**Penultimate (second-to-last) stress:**
This pattern is extremely frequent in two- and three-syllable words. You will hear it constantly in daily conversation, giving words a balanced, rolling feel:
- **шко́ла** (school)
- **кни́жка** (book)
- **доро́га** (road)
- **дале́ко** (far)

Despite seeing these patterns, remember our core principle: there is absolutely no fixed rule! You might look at two words and notice that **кни́жка** and **вода́** both end with the identical letter **а**. However, they have completely different stress patterns. The word **кни́жка** is stressed on the first syllable, while **вода́** (water) is stressed on the very last. The same ending can have a different stress, which reinforces our strategy: stress must be learned per word, every single time. It is like learning the spelling of the word—you cannot know it without checking!

## Рухомий наголос — Mobile Stress

Not only is Ukrainian stress free, but it is also highly mobile. "Mobile stress" means that the **на́голос** can actually move from one syllable to another within the very same word! This happens when we use different grammatical forms of the word in a sentence.

How exactly does this happen? The stress shifts in declension—when the word form changes its ending to show a different grammatical role. A perfect example of this mobility is the word for "hand" or "arm." In its basic dictionary form (the nominative singular), the stress sits at the very end:
- **рука́** (hand)

But when we talk about multiple hands (the nominative or accusative plural), the stress dramatically moves to the beginning of the word:
- **ру́ки** (hands)

(Note: in the genitive singular, which means "of a hand", the form is **руки́**—and here the stress stays right on the end! You can see how the stress dances around the word based on its job in the sentence.)

We also regularly see stress shifts in number. Noun stress can shift between singular and plural forms. Look at our common word for water:
- **вода́** (water, singular)
- **во́ди** (waters, plural)

This is strictly a preview note. Mobile stress will matter much more later in your journey when you are learning noun cases and verb conjugation in detail. For now, simple awareness is the goal. You do not need to memorize all these shifting rules today. Simply understanding that the stress can move will save you a lot of confusion later.

As a practical tip, reading dictionary marks is helpful, but listening closely to native speakers is the absolute best way to internalize these mobile stress patterns. Let the melody of the language wash over you, and soon your ears will naturally expect the stress to land in the right place.

## Інтонація — Intonation

Now that we deeply understand word stress, let's look at the broader melody of an entire sentence: your **інтона́ція** (intonation). The way your pitch rises and falls tells the listener exactly what you are doing—whether you are making a simple statement, asking a **пита́ння** (question), or expressing a burst of surprise. Let's break down the basic intonation patterns.

**Declarative intonation (Statements):**
When you are giving a simple **ві́дповідь** (answer) or stating a clear fact, your pitch smoothly falls at the end of the sentence. It has a calming, downward contour that signals you have finished speaking.
> «Це кафе.» (pitch drops down gently on «фе»)

**Interrogative with a question word:**
If you use a specific question word (like where, who, or what), your pitch rises on that specific question word, and then gently falls for the rest of the sentence. This creates a small hill at the start of your question.
> «Де́ кафе?» (pitch rises noticeably on «Де» and falls on «фе»)

**Yes/no questions (without a question word):**
This is where English speakers often make their biggest mistake! In English, we usually raise our pitch at the very end of a yes/no question. In Ukrainian, the pitch rises sharply on the stressed syllable of the key word you are asking about, and then it immediately falls. It is not a simple terminal rise like English!
> «Це ма́ма?» (pitch rises sharply on «ма́», then falls down on the second «ма»)

> [!tip]
> **The #1 mistake for English speakers:** In English, you raise your pitch at the very end of a yes/no question. In Ukrainian, the pitch rises sharply on the stressed syllable of the key word, then immediately falls. Practice this difference — it is one of the fastest ways to sound more natural!

**Exclamatory intonation:**
When you are expressing strong surprise, sudden excitement, or powerful emotion, you use a sharp pitch rise with heavy emphasis across the entire sentence.
> «Це кафе!» (sharp rise with very strong vocal energy)

Let's do a contrast drill right now. Practicing similar sentences with all four intonation patterns is the best way to train your voice to hit the right notes:
- **Statement:** «Це ма́ма.» (Downward finish)
- **Yes/No Question:** «Це ма́ма?» (Rise sharply on the first «ма» and fall on the second)
- **Question Word:** «Де́ ма́ма?» (Rise on «Де» and fall on the rest)
- **Exclamation:** «Це ма́ма!» (Sharp rise with strong emotional emphasis)

## Практика — Practice

Let's put all of this musical theory into practice! Pronunciation is a physical skill, so please make sure to read these exercises out loud to train your mouth and your ears.

**Stress placement drills:**
Identify which syllable carries the stress in these common words. Read them aloud, slightly exaggerating the stressed vowel to build your muscle memory:
- **до́брий** (first syllable)
- **дале́ко** (second syllable)
- **молоко́** (last syllable)
- **шко́ла** (first syllable)
- **вода́** (last syllable)

**Minimal pairs practice:**
Distinguish words that differ only in stress. Pay close attention to how the meaning shifts instantly when you move the emphasis!
- **за́мок** (castle) ↔ **замо́к** (lock)
- **му́ка** (torment) ↔ **мука́** (flour)
- **бра́ти** (brothers) ↔ **брати́** (to take)
- **пла́кати** (to cry) ↔ **плака́ти** (posters)

**Intonation reading exercises:**
Try reading the exact same sentence as a statement, a yes/no question, and an exclamation. Feel how your throat and pitch change with each variation:
1. «Це шко́ла.» (Smoothly falling pitch, very relaxed)
2. «Це шко́ла?» (Sharp rise on the stressed syllable of «шко́ла», then a quick fall)
3. «Це шко́ла!» (Loud, energetic rise across the whole word)

## Підсумок — Summary

Let's recap what we have successfully covered today. Ukrainian stress is "free" (meaning it can fall anywhere) and "mobile" (meaning it can shift when words change form). We remembered our rule of vowel purity under stress, keeping sounds clear and unreduced. We explored how to use specific rising and falling intonation contours for different types of questions, and we saw exactly how stress minimal pairs can completely change a word's meaning.

**Self-check:**
- Where exactly is the stress in the word **вода́**?
- What happens to vowel quality when a syllable is unstressed?
- How does yes/no question intonation fundamentally differ from a simple statement?

You can now identify stress in common Ukrainian words, read stress marks in dictionaries, and use the right intonation for statements, questions, and exclamations. That is real progress — добре!

Next up in Module 7: we will apply all these phonetic rules and musical patterns to real conversations as we dive into learning essential greetings and basic phrases!
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/stress-and-intonation.yaml`

```yaml
- type: quiz
  title: Stress Placement
  instruction: Identify which syllable carries the stress in these Ukrainian words.
  items:
  - question: Where does the stress fall in the word мама?
    options:
    - text: First syllable (МА-ма)
      correct: true
    - text: Second syllable (ма-МА)
      correct: false
    - text: Both syllables equally
      correct: false
    - text: No stress at all
      correct: false
    explanation: The word мама has first-syllable stress — it is one of the most common
      household words with this pattern.
  - question: Where does the stress fall in the word молоко?
    options:
    - text: First syllable (МО-ло-ко)
      correct: false
    - text: Second syllable (мо-ЛО-ко)
      correct: false
    - text: Third syllable (мо-ло-КО)
      correct: true
    - text: First and third equally
      correct: false
    explanation: Молоко has last-syllable stress — the emphasis falls on the final
      КО.
  - question: Where does the stress fall in the word школа?
    options:
    - text: First syllable (ШКО-ла)
      correct: true
    - text: Second syllable (шко-ЛА)
      correct: false
    - text: Both syllables equally
      correct: false
    - text: No fixed stress
      correct: false
    explanation: Школа has first-syllable (penultimate) stress — ШКО-ла.
  - question: Where does the stress fall in the word вода?
    options:
    - text: First syllable (ВО-да)
      correct: false
    - text: Second syllable (во-ДА)
      correct: true
    - text: Both syllables equally
      correct: false
    - text: It changes every time
      correct: false
    explanation: Вода has last-syllable stress — во-ДА.
  - question: Where does the stress fall in the word далеко?
    options:
    - text: First syllable (ДА-ле-ко)
      correct: false
    - text: Second syllable (да-ЛЕ-ко)
      correct: true
    - text: Third syllable (да-ле-КО)
      correct: false
    - text: First and third equally
      correct: false
    explanation: Далеко has penultimate stress — да-ЛЕ-ко. Many beginners mistakenly
      put the stress on the last syllable.
  - question: Where does the stress fall in the word добрий?
    options:
    - text: First syllable (ДО-брий)
      correct: true
    - text: Second syllable (до-БРИЙ)
      correct: false
    - text: Both syllables equally
      correct: false
    - text: No stress
      correct: false
    explanation: Добрий has first-syllable stress — ДО-брий, as in the greeting добрий
      день.
  - question: Where does the stress fall in the word книжка?
    options:
    - text: First syllable (КНИЖ-ка)
      correct: true
    - text: Second syllable (книж-КА)
      correct: false
    - text: Both syllables equally
      correct: false
    - text: It depends on the sentence
      correct: false
    explanation: Книжка has first-syllable stress — КНИЖ-ка.
  - question: Where does the stress fall in the word дорога?
    options:
    - text: First syllable (ДО-ро-га)
      correct: false
    - text: Second syllable (до-РО-га)
      correct: true
    - text: Third syllable (до-ро-ГА)
      correct: false
    - text: First and second equally
      correct: false
    explanation: Дорога has penultimate stress — до-РО-га.
  - question: Where does the stress fall in the word кава?
    options:
    - text: First syllable (КА-ва)
      correct: true
    - text: Second syllable (ка-ВА)
      correct: false
    - text: Both syllables equally
      correct: false
    - text: No fixed stress
      correct: false
    explanation: Кава has first-syllable stress — КА-ва.
  - question: Where does the stress fall in the word хата?
    options:
    - text: First syllable (ХА-та)
      correct: true
    - text: Second syllable (ха-ТА)
      correct: false
    - text: Both syllables equally
      correct: false
    - text: No fixed stress
      correct: false
    explanation: Хата has first-syllable stress — ХА-та.
  - question: Where does the stress fall in the word рука?
    options:
    - text: First syllable (РУ-ка)
      correct: false
    - text: Second syllable (ру-КА)
      correct: true
    - text: Both syllables equally
      correct: false
    - text: It changes depending on usage
      correct: false
    explanation: In its basic form, рука has last-syllable stress — ру-КА. But remember,
      in the plural руки the stress moves!
  - question: Where does the stress fall in the word Україна?
    options:
    - text: First syllable
      correct: false
    - text: Second syllable
      correct: false
    - text: Third syllable (Укра-Ї-на)
      correct: true
    - text: Fourth syllable
      correct: false
    explanation: Україна has stress on the third syllable — У-кра-Ї-на.
- type: match-up
  title: Stress Minimal Pairs
  instruction: Match each stressed word to its correct English meaning.
  pairs:
  - left: замок (stress on ЗА-)
    right: castle
  - left: замок (stress on -МОК)
    right: lock
  - left: мука (stress on МУ-)
    right: torment
  - left: мука (stress on -КА)
    right: flour
  - left: брати (stress on БРА-)
    right: brothers
  - left: брати (stress on -ТИ)
    right: to take
  - left: рука (stress on -КА)
    right: hand
  - left: руки (stress on РУ-)
    right: hands
- type: true-false
  title: Intonation and Stress Facts
  instruction: Decide whether each statement about Ukrainian stress and intonation
    is true or false.
  items:
  - statement: In Ukrainian, stress always falls on the second-to-last syllable, just
      like in Polish.
    correct: false
    explanation: Ukrainian stress is free — it can fall on any syllable. Polish has
      fixed penultimate stress, but Ukrainian does not.
  - statement: Two Ukrainian words spelled the same way can have different meanings
      depending on which syllable is stressed.
    correct: true
    explanation: This is exactly how stress minimal pairs work — for example, замок
      means castle or lock depending on the stress.
  - statement: When asking a yes/no question in Ukrainian, your pitch should rise
      at the very end of the sentence, just like in English.
    correct: false
    explanation: In Ukrainian yes/no questions, the pitch rises sharply on the stressed
      syllable of the key word, then falls. It is not a simple terminal rise.
  - statement: In a Ukrainian statement, the pitch falls at the end of the sentence.
    correct: true
    explanation: Declarative intonation in Ukrainian uses a falling pitch at the end,
      signaling that the speaker has finished.
  - statement: Ukrainian stress can move to a different syllable when a word changes
      its grammatical form.
    correct: true
    explanation: This is called mobile stress. For example, рука (stress on -КА) becomes
      руки (stress on РУ-) in the plural.
  - statement: The acute accent mark in Ukrainian dictionaries shows which vowel is
      stressed.
    correct: true
    explanation: The accent mark (like in вода) is placed over the stressed vowel
      to help learners identify the correct pronunciation.
  - statement: When using a question word like Де, the pitch stays flat throughout
      the entire sentence.
    correct: false
    explanation: With a question word, the pitch rises on the question word itself
      and then falls for the rest of the sentence.
  - statement: The words книжка and вода both end with the letter а, so they must
      have the same stress pattern.
    correct: false
    explanation: Having the same ending does not guarantee the same stress. Книжка
      is stressed on the first syllable, while вода is stressed on the last.
- type: fill-in
  title: Complete the Stress Rule
  instruction: Choose the correct word or phrase to complete each statement about
    Ukrainian stress and intonation.
  items:
  - sentence: Ukrainian stress is called ___ — it can fall on any syllable.
    answer: free
    options:
    - free
    - fixed
    - final
    - penultimate
    explanation: Ukrainian stress is free, meaning there is no single rule for where
      it falls.
  - sentence: The word замок means 'castle' when the stress is on the ___ syllable.
    answer: first
    options:
    - first
    - second
    - third
    - last
    explanation: ЗА-мок (first syllable) = castle; за-МОК (second syllable) = lock.
  - sentence: The word замок means 'lock' when the stress is on the ___ syllable.
    answer: second
    options:
    - first
    - second
    - third
    - last
    explanation: За-МОК (second syllable) = lock; ЗА-мок (first syllable) = castle.
  - sentence: When stress moves between forms of the same word (like рука → руки),
      this is called ___ stress.
    answer: mobile
    options:
    - mobile
    - fixed
    - final
    - invisible
    explanation: Mobile stress means the stress shifts to a different syllable when
      the word changes grammatical form.
  - sentence: In a Ukrainian statement like 'Це кафе', the pitch ___ at the end.
    answer: falls
    options:
    - falls
    - rises
    - stays flat
    - disappears
    explanation: Declarative intonation uses a falling pitch at the end of the sentence.
  - sentence: In a Ukrainian yes/no question, the pitch rises sharply on the ___ of
      the key word.
    answer: stressed syllable
    options:
    - stressed syllable
    - first syllable
    - last syllable
    - last word
    explanation: Ukrainian yes/no questions feature a sharp pitch rise on the stressed
      syllable of the key word, then a fall.
  - sentence: The word мама has stress on the ___ syllable.
    answer: first
    options:
    - first
    - second
    - third
    - last
    explanation: МА-ма — stress on the first syllable, common in basic family words.
  - sentence: The word молоко has stress on the ___ syllable.
    answer: third
    options:
    - first
    - second
    - third
    - none
    explanation: Мо-ло-КО — stress on the third (last) syllable.
  - sentence: In Ukrainian dictionaries, stress is marked with a(n) ___ over the stressed
      vowel.
    answer: acute accent
    options:
    - acute accent
    - circle
    - underline
    - bold dot
    explanation: The acute accent mark (like the mark in вода) is placed directly
      over the stressed vowel.
  - sentence: Words like мама, тато, хата, and кава all share stress on the ___ syllable.
    answer: first
    options:
    - first
    - second
    - last
    - middle
    explanation: These common family and household words all have first-syllable stress.
- type: group-sort
  title: Sort by Stress Position
  instruction: Sort these Ukrainian words into groups based on which syllable carries
    the stress.
  groups:
  - name: First-syllable stress
    items:
    - мама
    - тато
    - хата
    - кава
    - добрий
  - name: Penultimate (middle) stress
    items:
    - школа
    - книжка
    - дорога
    - далеко
  - name: Last-syllable stress
    items:
    - молоко
    - вода
    - рука
- type: anagram
  title: Unscramble the Word
  instruction: Rearrange the letters to form a Ukrainian word from this lesson. All
    letters are space-separated.
  items:
  - scrambled: о л о м о к
    answer: молоко
  - scrambled: а к у р
    answer: рука
  - scrambled: а д о в
    answer: вода
  - scrambled: а л о к ш
    answer: школа
  - scrambled: а к в а
    answer: кава
  - scrambled: а г о р о д
    answer: дорога
  - scrambled: а м а м
    answer: мама
  - scrambled: о т а т
    answer: тато

```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/stress-and-intonation.yaml`

```yaml
items:
  - lemma: "замок"
    translation: "castle (when stressed ЗА-мок) / lock (when stressed за-МОК)"
    pos: "noun"
    gender: "m"
    notes: "Stress minimal pair — meaning changes entirely based on stress placement."
    usage: "за-мок vs. замо-к"
    example: "Це старий замок."
  - lemma: "вода"
    translation: "water"
    pos: "noun"
    gender: "f"
    notes: "Last-syllable stress (во-ДА). Mobile stress in plural: во-ДИ."
    usage: "пити воду, холодна вода"
  - lemma: "рука"
    translation: "hand, arm"
    pos: "noun"
    gender: "f"
    notes: "Mobile stress: ру-КА (singular) → РУ-ки (plural)."
  - lemma: "добрий"
    translation: "good"
    pos: "adj"
    notes: "First-syllable stress (ДО-брий)."
    usage: "добрий день"
  - lemma: "школа"
    translation: "school"
    pos: "noun"
    gender: "f"
    notes: "Penultimate stress (ШКО-ла)."
  - lemma: "молоко"
    translation: "milk"
    pos: "noun"
    gender: "n"
    notes: "Last-syllable stress (мо-ло-КО)."
  - lemma: "мука"
    translation: "torment (when stressed МУ-ка) / flour (when stressed му-КА)"
    pos: "noun"
    gender: "f"
    notes: "Stress minimal pair like замок."
  - lemma: "мама"
    translation: "mom"
    pos: "noun"
    gender: "f"
    notes: "First-syllable stress (МА-ма)."
  - lemma: "тато"
    translation: "dad"
    pos: "noun"
    gender: "m"
    notes: "First-syllable stress (ТА-то)."
  - lemma: "хата"
    translation: "house (traditional Ukrainian home)"
    pos: "noun"
    gender: "f"
    notes: "First-syllable stress (ХА-та)."
  - lemma: "кава"
    translation: "coffee"
    pos: "noun"
    gender: "f"
    notes: "First-syllable stress (КА-ва)."
  - lemma: "книжка"
    translation: "book"
    pos: "noun"
    gender: "f"
    notes: "First-syllable stress (КНИЖ-ка)."
  - lemma: "дорога"
    translation: "road"
    pos: "noun"
    gender: "f"
    notes: "Penultimate stress (до-РО-га)."
  - lemma: "далеко"
    translation: "far"
    pos: "adv"
    notes: "Penultimate stress (да-ЛЕ-ко). Common learner error to stress the last syllable."
  - lemma: "наголос"
    translation: "stress, accent (linguistic term)"
    pos: "noun"
    gender: "m"
    notes: "Metalinguistic term for word stress."
  - lemma: "інтонація"
    translation: "intonation"
    pos: "noun"
    gender: "f"
    notes: "Metalinguistic term for sentence melody."
  - lemma: "питання"
    translation: "question"
    pos: "noun"
    gender: "n"
    notes: "High-frequency word used in intonation section."
  - lemma: "відповідь"
    translation: "answer"
    pos: "noun"
    gender: "f"
    notes: "High-frequency word paired with питання."
  - lemma: "кафе"
    translation: "cafe"
    pos: "noun"
    gender: "n"
    notes: "Used in intonation examples throughout the lesson."
  - lemma: "голос"
    translation: "voice"
    pos: "noun"
    gender: "m"
    notes: "Related to наголос; root word for stress concept."
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
- Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/stress-and-intonation.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/stress-and-intonation.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/stress-and-intonation.yaml`

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
