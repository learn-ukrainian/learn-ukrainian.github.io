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



**NOTE: 5 inline fix(es) from the review have ALREADY been applied to the files. Do NOT re-apply those fixes. Read the CURRENT file contents carefully — they reflect the post-fix state. Only fix issues that are still present in the current files.**

## Review Findings (targeted fix required)

**CONSTRAINTS:**
- Fix ONLY the issues listed below
- Do NOT rewrite surrounding text
- Preserve word count and structure
- Only modify these sections: Activities file, line 263, Entire module — all sections, Line 43 in section "Типи складів — Syllable Types", Section "Практика — Practice" (lines 73-96), Vocabulary YAML — items "книга", "звук", "буква", "слово", "тут", Whole module

### Finding 1: Zero Engagement Boxes (Audit-Blocking)
**Location**: Entire module — all sections
**Problem**: The module contains 0 callout boxes. Minimum for A1 is 1, and the richness audit expects engagement: 2. This is the primary cause of the audit FAIL (richness 53% < 60% threshold). The research notes specifically recommended a callout for ї as a vowel and suggested using the скоромовка «На дворі трава, на траві дрова» as a cultural hook. Neither was implemented.
**Required Fix**: Add at minimum:
**Severity**: HIGH

### Finding 2: True-False Instruction in Ukrainian (A1 Violation)
**Location**: Activities file, line 263
**Problem**: This instruction is entirely in Ukrainian. At A1 M05, activity instructions must be in English. The learner cannot yet parse a Ukrainian imperative sentence. All other activity instructions in this file are in English.
**Required Fix**: Replace with English: "Decide whether each statement is true or false."
**Severity**: HIGH

### Finding 3: Untranslated "острів" in Content
**Location**: Line 43 in section "Типи складів — Syllable Types"
**Problem**: The word "острів" (island) appears as a syllable division example but is never translated. Every other Ukrainian example word in the module includes its English meaning ("the word for milk: **молоко**", "the word for sister: **сестра**", etc.). An A1 learner encountering an untranslated word will be confused. The word is also not in the vocabulary YAML.
**Required Fix**: Change to "Another example is the word for island: **о-стрів**."
**Severity**: HIGH

### Finding 4: Five Vocabulary Items Not Used in Prose
**Location**: Vocabulary YAML — items "книга", "звук", "буква", "слово", "тут"
**Problem**: These 5 vocabulary items are defined in the vocabulary YAML but never appear in the content markdown. Vocabulary should be introduced in context within the prose. Of these, "буква" (letter) and "звук" (sound) are highly relevant metalinguistic terms that should be woven into section "Що таке склад? — What Is a Syllable?" or "Типи складів — Syllable Types".
**Required Fix**: Either (a) integrate these words into the prose with translations, or (b) remove from vocabulary YAML if they're not pedagogically essential. Recommendation: add "буква" and "звук" as metalinguistic terms in the prose (they are fundamental to discussing syllables). "Книга" could appear as a syllable example (кни-га, 2 syllables). "Тут" and "слово" can remain in vocab as passive recognition items with their `example` sentences serving as introduction.
**Severity**: HIGH

### Finding 5: Practice Section Repeats Without Adding Value
**Location**: Section "Практика — Practice" (lines 73-96)
**Problem**: This section re-uses the exact same words (молоко, автобус, сестра, бібліотека, університет) that were already fully worked through in sections "Що таке склад? — What Is a Syllable?" and "Типи складів — Syllable Types". No new words are introduced. A practice section should test with fresh examples to verify transfer of learning, not re-drill familiar words.
**Required Fix**: Replace at least 2-3 examples with fresh words from the vocabulary (e.g., книга → кни-га, мама → ма-ма) to test whether the learner can apply the rules independently.
**Severity**: HIGH

### Finding 6: Missing Examples Count (Richness Gap)
**Location**: Whole module
**Problem**: Richness audit shows examples: 4/8. The module needs more formatted example blocks. While Ukrainian examples exist inline, they aren't structured as dedicated example blocks that the richness scanner can detect.
**Required Fix**: Add `[!example]` callout boxes around key demonstration sets (e.g., the open vs closed syllable examples in section "Типи складів — Syllable Types", the word division rules in section "Правила переносу — Word Division Rules").
**Severity**: HIGH

---

## Critical Issues Found

### Issue 1: Zero Engagement Boxes (Audit-Blocking)
- **Location**: Entire module — all sections
- **Problem**: The module contains 0 callout boxes. Minimum for A1 is 1, and the richness audit expects engagement: 2. This is the primary cause of the audit FAIL (richness 53% < 60% threshold). The research notes specifically recommended a callout for ї as a vowel and suggested using the скоромовка «На дворі трава, на траві дрова» as a cultural hook. Neither was implemented.
- **Fix**: Add at minimum:
  - A `[!tip]` box in section "Що таке склад? — What Is a Syllable?" about ї always being its own syllable (line 19 area)
  - A `[!cultural-note]` box in section "Практика — Practice" with the скоромовка clapping exercise
  - A `[!tip]` box in section "Правила переносу — Word Division Rules" summarizing the "never split" rules as a quick reference

### Issue 2: True-False Instruction in Ukrainian (A1 Violation)
- **Location**: Activities file, line 263
- **Original**: 「Визначте, чи твердження правильне.」
- **Problem**: This instruction is entirely in Ukrainian. At A1 M05, activity instructions must be in English. The learner cannot yet parse a Ukrainian imperative sentence. All other activity instructions in this file are in English.
- **Fix**: Replace with English: "Decide whether each statement is true or false."

### Issue 3: Untranslated "острів" in Content
- **Location**: Line 43 in section "Типи складів — Syllable Types"
- **Original**: 「Another example is **о-стрів**.」
- **Problem**: The word "острів" (island) appears as a syllable division example but is never translated. Every other Ukrainian example word in the module includes its English meaning ("the word for milk: **молоко**", "the word for sister: **сестра**", etc.). An A1 learner encountering an untranslated word will be confused. The word is also not in the vocabulary YAML.
- **Fix**: Change to "Another example is the word for island: **о-стрів**."

### Issue 4: Five Vocabulary Items Not Used in Prose
- **Location**: Vocabulary YAML — items "книга", "звук", "буква", "слово", "тут"
- **Problem**: These 5 vocabulary items are defined in the vocabulary YAML but never appear in the content markdown. Vocabulary should be introduced in context within the prose. Of these, "буква" (letter) and "звук" (sound) are highly relevant metalinguistic terms that should be woven into section "Що таке склад? — What Is a Syllable?" or "Типи складів — Syllable Types".
- **Fix**: Either (a) integrate these words into the prose with translations, or (b) remove from vocabulary YAML if they're not pedagogically essential. Recommendation: add "буква" and "звук" as metalinguistic terms in the prose (they are fundamental to discussing syllables). "Книга" could appear as a syllable example (кни-га, 2 syllables). "Тут" and "слово" can remain in vocab as passive recognition items with their `example` sentences serving as introduction.

### Issue 5: Practice Section Repeats Without Adding Value
- **Location**: Section "Практика — Practice" (lines 73-96)
- **Problem**: This section re-uses the exact same words (молоко, автобус, сестра, бібліотека, університет) that were already fully worked through in sections "Що таке склад? — What Is a Syllable?" and "Типи складів — Syllable Types". No new words are introduced. A practice section should test with fresh examples to verify transfer of learning, not re-drill familiar words.
- **Fix**: Replace at least 2-3 examples with fresh words from the vocabulary (e.g., книга → кни-га, мама → ма-ма) to test whether the learner can apply the rules independently.

### Issue 6: Missing Examples Count (Richness Gap)
- **Location**: Whole module
- **Problem**: Richness audit shows examples: 4/8. The module needs more formatted example blocks. While Ukrainian examples exist inline, they aren't structured as dedicated example blocks that the richness scanner can detect.
- **Fix**: Add `[!example]` callout boxes around key demonstration sets (e.g., the open vs closed syllable examples in section "Типи складів — Syllable Types", the word division rules in section "Правила переносу — Word Division Rules").

---

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 43 | 「Another example is **о-стрів**.」 | Another example is the word for island: **о-стрів**. | Missing translation |
| 263 (activities) | 「Визначте, чи твердження правильне.」 | Decide whether each statement is true or false. | A1 language violation |

---

## Fix Plan to Reach 9/10 (REQUIRED since score < 9.0)

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Add 3 callout boxes (see Issue 1) — `[!tip]` for ї vowel rule, `[!cultural-note]` for скоромовка, `[!tip]` for word division summary
2. Add an `[!example]` box in section "Типи складів — Syllable Types" for open vs closed comparison

**Expected score after fix:** 9/10

### Language: 8/10 → 9/10
**What to fix:**
1. Line 43: Add translation for острів (see Issue 3)

**Expected score after fix:** 9/10

### Pedagogy: 8/10 → 9/10
**What to fix:**
1. Integrate missing vocab words (буква, звук, книга) into prose (see Issue 4)
2. Add fresh examples to section "Практика — Practice" (see Issue 5)

**Expected score after fix:** 9/10

### Activities: 8/10 → 9/10
**What to fix:**
1. Line 263: Change true-false instruction to English (see Issue 2)
2. Consider adding a word-division focused activity (the fill-in tests syllable division, but a dedicated exercise on the "cannot split" rules would strengthen coverage)

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.1 + 9×1.2 + 9×1.3 + 9×1.3 + 8×1.0 + 9×1.5) / 8.9
= (13.5 + 9.9 + 10.8 + 11.7 + 11.7 + 8 + 13.5) / 8.9
= 79.1 / 8.9 = 8.9/10
```

---

## Audit Failures (from automated re-audit)

```
⚠️ HYDRATION NOTE: Outline sums to 1300, exceeding word_target 1200
--- STRICT GATES (Level A1) ---
❌ [REVIEW_VERDICT_FAIL] Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
⚠️  [UNIFORM_HIGH_SCORES] All 7 dimension scores are uniformly high (mean=8.1, stdev=0.38). Each dimension should be evaluated independently — genuinely different aspects rarely score identically.
❌ AUDIT FAILED. Correct errors before proceeding.
Critical Failures:
• Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/syllables-and-word-division-audit.log for details)
⚠️  RAG verification found unverified words (see audit report)
--- STATUS JSON GATE BLOCKERS ---
GATE BLOCKER: Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
--- VESUM WORD VERIFICATION FAILURES ---
These words were NOT found in the VESUM morphological dictionary.
Check if they are valid Ukrainian forms. Fix misspellings or Russianisms.
  ❌ `блі` (source: prose)
  ❌ `Бі` (source: prose)
  ❌ `вер` (source: prose)
  ❌ `дж` (source: prose)
  ❌ `дз` (source: prose)
  ❌ `ка` (source: prose)
  ❌ `ль` (source: prose)
  ❌ `стр` (source: prose)
```

---

## File Contents (for reference)

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/syllables-and-word-division.md`

```markdown
## Що таке склад? — What Is a Syllable?

Welcome back! You have mastered the Ukrainian alphabet, and you are doing an incredible job. Now that you know all the letters and the sounds they make, you are ready for the next big step: building words. Just like a house is built brick by brick, words are built piece by piece. In Ukrainian, these pieces are called syllables. Learning how syllables work will transform the way you read and speak. It makes long words feel much less intimidating.

So, what exactly is a syllable? You can think of a syllable, or **склад**, as a single beat of rhythm in a word. If you clap your hands while saying a word, each clap represents one syllable.

Here is the golden rule of Ukrainian syllables, and it is beautifully simple: the vowel is the absolute core of the syllable. In fact, every single vowel creates exactly one syllable. This means that if you want to know how many syllables a word has, you do not need to guess. All you have to do is count the vowels! This metalinguistic term for vowel is **голосний**. Every **голосний** creates a new beat.

Let’s look at some examples to see this in action.

Take the word for milk: **молоко**.
Look at the vowels: **о**, **о**, **о**. That is three vowels.
Because there are three vowels, there are exactly three syllables: **мо-ло-ко**.

What about a short word like the word for cat? «Це кіт.»
There is only one vowel: **і**. Therefore, it has only one syllable: **кіт**. One clap, one syllable.

Now let’s look at a very important word: **Україна**.
Let’s count the vowels: **у**, **а**, **ї**, **а**. That makes four vowels. So, the word has four syllables: **у-кра-ї-на**. Notice that the letter **ї** is a full vowel, and it creates its own syllable.

> [!tip] **ї is always a vowel!**
> The letter **ї** always counts as its own syllable. Do not confuse it with **й**, which is a consonant. Whenever you see **ї**, add one more clap!

This might feel a little different from your English syllable intuition. In English, syllable boundaries can sometimes feel flexible or depend on spelling rules that do not match the sounds. In Ukrainian, syllable boundaries follow very clear, consistent phonetic rules. Once you learn to spot the vowels, you will never struggle to break down a long word. You just find the vowels, count them, and clap it out.

## Типи складів — Syllable Types

Now that you know how to count syllables, let's talk about the different shapes they can take. Syllables come in two main types: open and closed.

An open syllable is one that ends in a vowel. The air flows freely out of your mouth without being stopped by a consonant. This is the absolute default and the most common type of syllable in the Ukrainian language. When you listen to native speakers, the language sounds so melodic and flowing largely because it is packed with open syllables. Examples of open syllables are **ма-** and **но-**.

Look at the word for tree: **дерево**.
If we break it down, we get **де-ре-во**. Every single syllable ends in a vowel. They are all open syllables.

Look at the word for street: **вулиця**.
Broken down, it is **ву-ли-ця**. Again, all open syllables! The word flows beautifully.

A closed syllable, on the other hand, ends in a consonant (**приголосний**). The flow of air is stopped or restricted at the end of the beat. Closed syllables usually occur at the very end of a word, like in **там**.

For example, let's look at the word for bus: **автобус**.
It breaks down into **ав-то-бус**. The final syllable, **бус**, ends in the consonant **с**, so it is a closed syllable. Another example is the word for cat, **кіт**, which is a single closed syllable. Closed syllables also happen in the middle of a word when a sonorant consonant (like **й**, **в**, **р**, **л**, **м**, **н**) comes before another consonant, as in the word **чай-ка**.

What happens when you have a bunch of consonants clustered together? This brings us to consonant clusters. In spoken Ukrainian, phonetic syllables follow a rule called maximal onset. This means consonants prefer to group together at the beginning of the next syllable rather than closing the previous one.

Take the word for sister: **сестра**.
Phonetically, you split it as **се-стра**. The cluster **стр** jumps to the second syllable, leaving the first syllable open. Another example is the word for island: **о-стрів**.

While written orthographic hyphenation (**перенос**) is a bit more flexible—the official Pravopys rules allow you to write **се-стра**, **сес-тра**, or even **сест-ра**—as a learner, you should focus on the phonetic boundaries first. Always try to keep syllables open when you speak.

## Правила переносу — Word Division Rules

Speaking of writing, let's dive into the rules of word division, or **перенос**. When you are writing in Ukrainian—whether you are carefully writing in a copybook or typing up a document to be printed—you will often reach the end of a line before you finish a word. You need to know exactly where you are allowed to hyphenate and break the word. Correct word division matters a great deal in Ukrainian handwriting and printing; it shows that you truly understand the structure of the language.

While spoken syllables focus on keeping things open, written word division has its own specific set of rules. Here is what you need to know.

First, let's look at what you absolutely cannot split. You cannot leave a single letter alone on a line, and you cannot carry a single letter over to the next line. Even if that single letter is a full syllable, it must stay attached to the rest of the word. For example, the word **Україна** has the syllables **у-кра-ї-на**. However, you cannot write «У-країна». The single letter **У** is not allowed to stand alone.

You also cannot split the digraphs **дж** and **дз** when they represent a single sound. For example, in the word **ґудзик**, the **дз** makes one sound. You must divide it as **ґу-дзик**. You cannot write «ґуд-зик».

> [!tip] **Quick reference — what you can never split:**
> - A single letter from the rest of the word (❌ У-країна)
> - The digraphs **дж** / **дз** when they make one sound (❌ ґуд-зик)
> - The soft sign **ь** from its consonant (❌ пал-ьці)
> - The apostrophe group from the consonant before it (❌ сім-'я)

There are a couple of special characters that love to stick to their friends. You cannot separate the soft sign (**ь**) from the preceding consonant. It modifies the consonant before it, so they are an inseparable pair. In the word **пальці**, the correct split is **паль-ці**. You cannot write «пал-ьці».

Similarly, you cannot separate the apostrophe group from the consonant before it. The apostrophe stays with the preceding consonant. Take the word **сім'я**. The correct division is **сі-м'я**. You must never write «сім-'я».

So, where can you split? You can split between two consonants. For example, in a word like **сільський**, you can split it as **сіль-ський**. Notice how the **ль** stays together because of the soft sign rule, and you split between the two consonant groups. You can also easily split between a vowel and a consonant, which is the most natural place. For instance, **молоко** easily divides as **мо-ло-ко**.

A common learner error is applying English hyphenation habits to Ukrainian words. English rules are often based on root words or prefixes in ways that Ukrainian does not follow. Let's drill with some longer problem words.

Look at the word for library: **бібліотека**.
It has five syllables: **бі-блі-о-те-ка**. It can be divided at any of those dashes, but remember, you cannot leave the single letter **о** on a line by itself!

Look at the word for university: **університет**.
It also has five syllables: **у-ні-вер-си-тет**. Just like before, the **у** cannot be left alone on a line.

Mastering these rules of word division will make your written Ukrainian look elegant and perfectly natural.

## Практика — Practice

> [!cultural-note] **Clap it out — like Ukrainian kids do!**
> In Ukrainian schools, children clap their hands to count syllables. Try this скоромовка (tongue twister): «На дворі трава, на траві дрова.» Clap each syllable: **На-дво-рі / тра-ва / на-тра-ві / дро-ва** — eight claps! This is how native speakers learn syllable rhythm.

You have learned so much! Now it is time to put your new knowledge into practice. The best way to get comfortable with syllables and word division is to actively work with them. Let's do some syllable counting drills.

Look at the word **молоко**. Count the vowels: **о**, **о**, **о**. That is three vowels, which means three syllables. The boundaries are **мо-ло-ко**.

Look at the word **автобус**. Count the vowels: **а**, **о**, **у**. Three vowels, three syllables. The boundaries are **ав-то-бус**.

Look at the word **сестра**. Count the vowels: **е**, **а**. Two vowels, two syllables. Phonetically, the boundary is **се-стра**.

Now, let's try some word division exercises for writing. Imagine you are reaching the end of a line in your notebook. Where would you mark the correct division points in these multi-syllable words?

For the word **бібліотека**, you can divide it as **бі-блі-о-те-ка**, but remember not to leave the **о** alone if you divide it there.

For the word **університет**, you can divide it as **у-ні-вер-си-тет**, but the **у** must stay with the rest of the word if it is at the start of the line.

Finally, practice reading multi-syllable words aloud. This is a fantastic way to build your reading fluency. Start by reading the word slowly, syllable-by-syllable.

«Бі... блі... о... те... ка.»
«У... ні... вер... си... тет.»

Once you feel comfortable, speed it up and read the word at full speed. «Це бібліотека.» «Це університет.»

This step-by-step approach will make even the longest Ukrainian words feel easy and manageable. You are doing great!

## Підсумок — Summary

Let's quickly review what we have covered today. You learned that every vowel creates one syllable, so counting syllables simply means counting the vowels. You discovered that open syllables end in a vowel and are the most common type in Ukrainian, while closed syllables end in a consonant. We also explored consonant cluster split rules, where spoken syllables prefer to stay open (like **се-стра**). Finally, you learned the strict word division rules for writing.

**Self-check:**
- How many syllables in **Україна**?
- What is an open syllable?
- Where do you split a consonant cluster phonetically?

In our next module, M6, we will build on this rhythm by exploring stress and intonation. Keep up the excellent work!
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/syllables-and-word-division.yaml`

```yaml
- type: quiz
  title: Count the Syllables
  instruction: 'Remember: count the vowels to find the number of syllables.'
  items:
  - question: How many syllables does the word молоко have?
    options:
    - text: '2'
      correct: false
    - text: '3'
      correct: true
    - text: '4'
      correct: false
    - text: '1'
      correct: false
    explanation: 'молоко has three vowels (о, о, о), so it has three syllables: мо-ло-ко.'
  - question: How many syllables does the word кіт have?
    options:
    - text: '2'
      correct: false
    - text: '3'
      correct: false
    - text: '1'
      correct: true
    - text: '4'
      correct: false
    explanation: кіт has one vowel (і), so it has one syllable.
  - question: How many syllables does the word Україна have?
    options:
    - text: '3'
      correct: false
    - text: '5'
      correct: false
    - text: '2'
      correct: false
    - text: '4'
      correct: true
    explanation: 'Україна has four vowels (у, а, ї, а), so it has four syllables:
      у-кра-ї-на.'
  - question: How many syllables does the word дерево have?
    options:
    - text: '3'
      correct: true
    - text: '2'
      correct: false
    - text: '4'
      correct: false
    - text: '1'
      correct: false
    explanation: 'дерево has three vowels (е, е, о), so it has three syllables: де-ре-во.'
  - question: How many syllables does the word бібліотека have?
    options:
    - text: '3'
      correct: false
    - text: '4'
      correct: false
    - text: '5'
      correct: true
    - text: '6'
      correct: false
    explanation: 'бібліотека has five vowels (і, і, о, е, а), so it has five syllables:
      бі-блі-о-те-ка.'
  - question: How many syllables does the word автобус have?
    options:
    - text: '2'
      correct: false
    - text: '4'
      correct: false
    - text: '1'
      correct: false
    - text: '3'
      correct: true
    explanation: 'автобус has three vowels (а, о, у), so it has three syllables: ав-то-бус.'
  - question: How many syllables does the word вулиця have?
    options:
    - text: '3'
      correct: true
    - text: '2'
      correct: false
    - text: '4'
      correct: false
    - text: '1'
      correct: false
    explanation: 'вулиця has three vowels (у, и, я), so it has three syllables: ву-ли-ця.'
  - question: How many syllables does the word університет have?
    options:
    - text: '4'
      correct: false
    - text: '3'
      correct: false
    - text: '5'
      correct: true
    - text: '6'
      correct: false
    explanation: 'університет has five vowels (у, і, е, и, е), so it has five syllables:
      у-ні-вер-си-тет.'
  - question: How many syllables does the word сестра have?
    options:
    - text: '1'
      correct: false
    - text: '3'
      correct: false
    - text: '2'
      correct: true
    - text: '4'
      correct: false
    explanation: 'сестра has two vowels (е, а), so it has two syllables: се-стра.'
  - question: How many syllables does the word мама have?
    options:
    - text: '1'
      correct: false
    - text: '2'
      correct: true
    - text: '3'
      correct: false
    - text: '4'
      correct: false
    explanation: 'мама has two vowels (а, а), so it has two syllables: ма-ма.'
- type: fill-in
  title: Mark the Correct Word Division
  instruction: Choose the correct way to divide each word into syllables.
  items:
  - sentence: молоко = ___
    answer: мо-ло-ко
    options:
    - мо-ло-ко
    - мол-ок-о
    - мол-о-ко
    - м-оло-ко
    explanation: Each syllable starts with a consonant and ends with a vowel (open
      syllables).
  - sentence: дерево = ___
    answer: де-ре-во
    options:
    - де-ре-во
    - дер-ев-о
    - дере-во
    - д-ере-во
    explanation: 'All three syllables are open, ending in vowels: де-ре-во.'
  - sentence: вулиця = ___
    answer: ву-ли-ця
    options:
    - ву-ли-ця
    - вул-и-ця
    - вули-ця
    - в-ули-ця
    explanation: 'Three open syllables: ву-ли-ця.'
  - sentence: автобус = ___
    answer: ав-то-бус
    options:
    - ав-то-бус
    - а-вто-бус
    - авт-об-ус
    - авто-бус
    explanation: The first syllable ав is closed (ends in consonant в), то is open,
      бус is closed.
  - sentence: сестра = ___
    answer: се-стра
    options:
    - се-стра
    - сес-тра
    - сест-ра
    - с-естра
    explanation: 'Phonetically, consonant clusters go to the next syllable: се-стра.'
  - sentence: Україна = ___
    answer: у-кра-ї-на
    options:
    - у-кра-ї-на
    - ук-ра-ї-на
    - у-кра-їна
    - укра-ї-на
    explanation: 'Four syllables, one per vowel: у-кра-ї-на.'
  - sentence: бібліотека = ___
    answer: бі-блі-о-те-ка
    options:
    - бі-блі-о-те-ка
    - біб-лі-о-те-ка
    - бібліо-те-ка
    - бі-бліо-тека
    explanation: 'Five syllables, one per vowel: бі-блі-о-те-ка.'
  - sentence: університет = ___
    answer: у-ні-вер-си-тет
    options:
    - у-ні-вер-си-тет
    - ун-ів-ер-си-тет
    - уні-вер-си-тет
    - у-нівер-ситет
    explanation: 'Five syllables: у-ні-вер-си-тет.'
- type: group-sort
  title: Open or Closed Syllables?
  instruction: Sort these syllables into the correct group. Open syllables end in
    a vowel. Closed syllables end in a consonant.
  groups:
  - name: Open syllables (end in a vowel)
    items:
    - мо
    - ло
    - ко
    - де
    - ре
    - во
    - ву
  - name: Closed syllables (end in a consonant)
    items:
    - кіт
    - там
    - бус
    - тет
    - вер
    - ав
- type: match-up
  title: Match the Word to Its Syllable Count
  instruction: Match each Ukrainian word to the correct number of syllables.
  pairs:
  - left: кіт
    right: 1 syllable
  - left: мама
    right: 2 syllables
  - left: молоко
    right: 3 syllables
  - left: Україна
    right: 4 syllables
  - left: бібліотека
    right: 5 syllables
  - left: сестра
    right: 2 syllables
  - left: дерево
    right: 3 syllables
  - left: автобус
    right: 3 syllables
  - left: університет
    right: 5 syllables
  - left: вулиця
    right: 3 syllables
- type: true-false
  title: True or False? Test Your Syllable Knowledge
  items:
  - statement: Every vowel in a Ukrainian word creates one syllable.
    correct: true
    explanation: 'This is the golden rule: count the vowels to count the syllables.'
  - statement: The word кіт has two syllables.
    correct: false
    explanation: кіт has only one vowel (і), so it has one syllable.
  - statement: An open syllable ends in a vowel.
    correct: true
    explanation: Open syllables end in a vowel, like мо, ло, ко.
  - statement: A closed syllable ends in a vowel.
    correct: false
    explanation: A closed syllable ends in a consonant, like кіт or там.
  - statement: The word молоко has all open syllables.
    correct: true
    explanation: мо-ло-ко — each syllable ends in the vowel о.
  - statement: You can leave a single letter alone on a line when dividing a word
      for writing.
    correct: false
    explanation: A single letter cannot stand alone on a line, even if it is a full
      syllable.
  - statement: The letters дж can be split between lines when they represent one sound.
    correct: false
    explanation: When дж represents a single sound, it must stay together.
  - statement: The soft sign (ь) can be separated from the consonant before it.
    correct: false
    explanation: The soft sign always stays with the preceding consonant, like паль-ці.
  instruction: Decide whether each statement is true or false.
- type: anagram
  title: Unscramble the Word
  instruction: Rearrange the letters to form the correct Ukrainian word from the lesson.
  items:
  - scrambled: к і т
    answer: кіт
  - scrambled: м а м а
    answer: мама
  - scrambled: о к о л о м
    answer: молоко
  - scrambled: о в е д е р
    answer: дерево
  - scrambled: а р т с е с
    answer: сестра
  - scrambled: д а л к с
    answer: склад

```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/syllables-and-word-division.yaml`

```yaml
items:
  - lemma: "склад"
    translation: "syllable"
    pos: "noun"
    gender: "m"
    notes: "Metalinguistic term. A single beat of rhythm in a word."
    usage: "Count the склади in this word."
  - lemma: "голосний"
    translation: "vowel"
    pos: "adj"
    notes: "Metalinguistic term. Every голосний creates one syllable."
  - lemma: "приголосний"
    translation: "consonant"
    pos: "adj"
    notes: "Metalinguistic term. Consonant clusters follow specific split rules."
  - lemma: "перенос"
    translation: "word division / hyphenation"
    pos: "noun"
    gender: "m"
    notes: "Metalinguistic term for the rules of splitting a word at the end of a line."
  - lemma: "молоко"
    translation: "milk"
    pos: "noun"
    gender: "n"
    notes: "Three open syllables: мо-ло-ко."
    example: "Це молоко."
  - lemma: "Україна"
    translation: "Ukraine"
    pos: "noun"
    gender: "f"
    notes: "Four syllables: у-кра-ї-на. The letter ї creates its own syllable."
    example: "Це Україна."
  - lemma: "сестра"
    translation: "sister"
    pos: "noun"
    gender: "f"
    notes: "Consonant cluster split: се-стра."
    example: "Це сестра."
  - lemma: "дерево"
    translation: "tree"
    pos: "noun"
    gender: "n"
    notes: "Three open syllables: де-ре-во."
    example: "Це дерево."
  - lemma: "вулиця"
    translation: "street"
    pos: "noun"
    gender: "f"
    notes: "Three open syllables: ву-ли-ця."
    example: "Це вулиця."
  - lemma: "автобус"
    translation: "bus"
    pos: "noun"
    gender: "m"
    notes: "Three syllables with closed final syllable: ав-то-бус."
    example: "Це автобус."
  - lemma: "бібліотека"
    translation: "library"
    pos: "noun"
    gender: "f"
    notes: "Five syllables: бі-блі-о-те-ка."
    example: "Це бібліотека."
  - lemma: "університет"
    translation: "university"
    pos: "noun"
    gender: "m"
    notes: "Five syllables: у-ні-вер-си-тет."
    example: "Це університет."
  - lemma: "буква"
    translation: "letter (of the alphabet)"
    pos: "noun"
    gender: "f"
    example: "Це буква."
  - lemma: "звук"
    translation: "sound"
    pos: "noun"
    gender: "m"
    example: "Це звук."
  - lemma: "слово"
    translation: "word"
    pos: "noun"
    gender: "n"
    example: "Це слово."
  - lemma: "кіт"
    translation: "cat"
    pos: "noun"
    gender: "m"
    notes: "One syllable, one vowel."
    example: "Це кіт."
  - lemma: "мама"
    translation: "mom"
    pos: "noun"
    gender: "f"
    notes: "Two open syllables: ма-ма."
    example: "Це мама."
  - lemma: "там"
    translation: "there"
    pos: "adv"
    notes: "One closed syllable."
    example: "Мама там."
  - lemma: "тут"
    translation: "here"
    pos: "adv"
    notes: "One closed syllable."
    example: "Кіт тут."
  - lemma: "книга"
    translation: "book"
    pos: "noun"
    gender: "f"
    notes: "Two syllables: кни-га."
    example: "Це книга."
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
- Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/syllables-and-word-division.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/syllables-and-word-division.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/syllables-and-word-division.yaml`

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
