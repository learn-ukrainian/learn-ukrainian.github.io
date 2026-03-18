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



**NOTE: 2 inline fix(es) from the review have ALREADY been applied to the files. Do NOT re-apply those fixes. Read the CURRENT file contents carefully — they reflect the post-fix state. Only fix issues that are still present in the current files.**

## Review Findings (targeted fix required)

**CONSTRAINTS:**
- Fix ONLY the issues listed below
- Do NOT rewrite surrounding text
- Preserve word count and structure
- Only modify these sections: Line 113, Section "Диграфи ДЖ, ДЗ", Line 65, Section "Африкати, Щ та Ф"

### Finding 1: Wrong Stress — цві́ркун (STRESS_MISMATCH)
**Location**: Line 65, Section "Африкати, Щ та Ф"
**Problem**: Standard Ukrainian stress is цвірку́н (stress on final syllable), not цві́ркун. Confirmed by D.0 stress verification pipeline (2.7M forms).
**Required Fix**: Replace `**цві́ркун**` with `**цвірку́н**`
**Severity**: HIGH

### Finding 2: Verb in Pre-Verb Module — цо́кає (MORPHOLOGICAL_VIOLATION)
**Location**: Line 65, Section "Африкати, Щ та Ф"
**Problem**: цо́кає is verb:imperf:pres:s:3 per VESUM. Module M4 is pre-verb (verbs forbidden before M15). While this appears inside a cultural riddle quote, it still introduces a conjugated verb form that hasn't been taught.
**Required Fix**: Rephrase to avoid the verb form. Use: «Не годи́нник, а цо́к-цо́к-цо́к.» — onomatopoeia instead of verb, preserving the Ц focus and riddle spirit.
**Severity**: HIGH

### Finding 3: Verb in Pre-Verb Module — дзвони́ти (MORPHOLOGICAL_VIOLATION)
**Location**: Line 113, Section "Диграфи ДЖ, ДЗ"
**Problem**: дзвони́ти is verb:imperf:inf per VESUM. Explicitly teaching a verb derivation (noun → verb) is grammar scope creep for M4.
**Required Fix**: Remove the verb derivation. Replace with a cultural detail that keeps the ДЗ focus: "The word дзвін is everywhere in Ukrainian life — from church towers to phone calls."
**Severity**: HIGH

### Finding 4: D.0 Pre-Screen Dismissals
**Severity**: HIGH

---

## Critical Issues Found

### Issue 1: Wrong Stress — цві́ркун (STRESS_MISMATCH)
- **Location**: Line 65, Section "Африкати, Щ та Ф"
- **Original**: 「The answer is **цві́ркун** (cricket)!」
- **Problem**: Standard Ukrainian stress is цвірку́н (stress on final syllable), not цві́ркун. Confirmed by D.0 stress verification pipeline (2.7M forms).
- **Fix**: Replace `**цві́ркун**` with `**цвірку́н**`

### Issue 2: Verb in Pre-Verb Module — цо́кає (MORPHOLOGICAL_VIOLATION)
- **Location**: Line 65, Section "Африкати, Щ та Ф"
- **Original**: 「«Не годи́нник, а цо́кає.»」
- **Problem**: цо́кає is verb:imperf:pres:s:3 per VESUM. Module M4 is pre-verb (verbs forbidden before M15). While this appears inside a cultural riddle quote, it still introduces a conjugated verb form that hasn't been taught.
- **Fix**: Rephrase to avoid the verb form. Use: «Не годи́нник, а цо́к-цо́к-цо́к.» — onomatopoeia instead of verb, preserving the Ц focus and riddle spirit.

### Issue 3: Verb in Pre-Verb Module — дзвони́ти (MORPHOLOGICAL_VIOLATION)
- **Location**: Line 113, Section "Диграфи ДЖ, ДЗ"
- **Original**: 「The word дзвін also gives Ukrainian the verb **дзвони́ти** (to ring, to call).」
- **Problem**: дзвони́ти is verb:imperf:inf per VESUM. Explicitly teaching a verb derivation (noun → verb) is grammar scope creep for M4.
- **Fix**: Remove the verb derivation. Replace with a cultural detail that keeps the ДЗ focus: "The word дзвін is everywhere in Ukrainian life — from church towers to phone calls."

### Issue 4: D.0 Pre-Screen Dismissals
- **[MORPHOLOGICAL_VIOLATION] Дя́кую (line 130)**: DISMISSED — properly framed as fixed survival phrase (line 127): 「These are fixed phrases — you will learn how they work grammatically later.」 Standard A1 pedagogy.
- **[MORPHOLOGICAL_VIOLATION] Будь (line 131)**: DISMISSED — same framing, same justification.
- **[STRESS_UNKNOWN] Дя́кую (line 130)**: DISMISSED — VESUM finds lowercase дякую (lemma: дякувати, verb:imperf:pres:s:1). Capitalization caused lookup miss.
- **[ACTIVITY_VESUM_FAIL] (activities)**: DISMISSED — activity has `vesum_exempt: true` with note: "Distractors include intentional misspellings (мясо, мьясо...) to test apostrophe knowledge." These are deliberately invalid forms in a quiz about correct spelling.

---

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 65 | 「**цві́ркун**」 | 「**цвірку́н**」 | Stress |
| 65 | 「а цо́кає」 | 「а цо́к-цо́к-цо́к」 | Scope (verb in M4) |
| 113 | 「the verb **дзвони́ти** (to ring, to call)」 | (remove verb derivation) | Scope (verb in M4) |

---

## Fix Plan to Reach 9/10 (REQUIRED — score < 9.0)

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. Line 65: Change `**цві́ркун**` → `**цвірку́н**` — wrong stress mark
2. Line 65: Change `«Не годи́нник, а цо́кає.»` → `«Не годи́нник, а цо́к-цо́к-цо́к.»` — removes verb from pre-verb module while keeping Ц focus
3. Line 113: Remove verb дзвони́ти derivation. Replace: "The word дзвін also gives Ukrainian the verb **дзвони́ти** (to ring, to call)." → "The word **дзвін** is everywhere in Ukrainian life — from church towers to phone calls."

**Expected score after fix:** 9/10

### Language: 8/10 → 9/10
**What to fix:** Fixes 1-3 above also resolve the Language dimension issues (stress error, scope violations).

**Expected score after fix:** 9/10

### LLM Fingerprint: 8/10 → 8/10
**Observation only (no fix required for pass):** Example formatting is consistent across sections (bold + parenthetical + dash + context note). This is functional formatting for an alphabet module, not a fingerprint concern worth fixing. No action needed.

### Projected Overall After Fixes
```
(9×1.5 + 9×1.1 + 9×1.2 + 8×1.3 + 9×1.3 + 8×1.0 + 9×1.5) / 8.9
= (13.5 + 9.9 + 10.8 + 10.4 + 11.7 + 8.0 + 13.5) / 8.9
= 77.8 / 8.9 = 8.7/10 → PASS (no auto-fail dimensions)
```

---

## Audit Failures (from automated re-audit)

```
⚠️  Outline compliance: 0 errors, 1 warnings
⚠️ [EXTRA_SECTION_IN_MARKDOWN] Section 'Підсумок — Summary' found in markdown but not in outline.
--- STRICT GATES (Level A1) ---
❌ [REVIEW_VERDICT_FAIL] Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
❌ AUDIT FAILED. Correct errors before proceeding.
Critical Failures:
• Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/completing-the-alphabet-audit.log for details)
⚠️  RAG verification found unverified words (see audit report)
--- STATUS JSON GATE BLOCKERS ---
GATE BLOCKER: Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
--- VESUM WORD VERIFICATION FAILURES ---
These words were NOT found in the VESUM morphological dictionary.
Check if they are valid Ukrainian forms. Fix misspellings or Russianisms.
  ❌ `ДЖ` (source: prose)
  ❌ `ДЗ` (source: prose)
  ❌ `ець` (source: prose)
  ❌ `иця` (source: prose)
  ❌ `М'Я` (source: prose)
```

---

## File Contents (for reference)

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/completing-the-alphabet.md`

```markdown
## Вступ — Introduction

Welcome to your final alphabet lesson! Here is how far you have come:

*   **Module 1** — You got the map: the Cyrillic code and how Ukrainian writing works.
*   **Module 2** — You mastered all ten vowels.
*   **Module 3** — You learned every consonant.
*   **Module 4 (today)** — The final pieces of the puzzle!

Today, we are placing those final pieces: the special modifiers (like the soft sign **Ь** and the apostrophe), the affricates (**Ц**, **Ч**, **Щ**), the unique digraphs (**ДЖ**, **ДЗ**), and the rare letter **Ф**. After completing this module, you will be able to read absolutely ANY Ukrainian word you see. Think about that for a moment — the entire Ukrainian language is about to open up to you! This is a huge milestone. Let's finish what we started!

## М'який знак — The Soft Sign

### Літера Ь
[Anna Ohoiko — Ukrainian Lessons — Ь](https://www.youtube.com/watch?v=cJlal8XKBxo)

Meet the soft sign, or **м'який знак**. The letter **Ь** is unique because it has no sound of its own at all. Its only job is to soften, or palatalize, the consonant that comes immediately before it. When you see **Ь**, you need to place your tongue closer to the roof of your mouth as you say the preceding consonant, making it sound "soft" and light.

Here is the pattern you need to know: **Ь** appears after consonants at the very end of a word, or sometimes before another consonant in the middle of a word. It will never appear at the start of a word, and it will never appear after a vowel.

Let's look at some common words where **Ь** does its magic:
*   **сі́ль** (salt) — Notice how the **Л** is soft at the end. This is a common everyday kitchen word.
*   **де́нь** (day) — This is a top 50 word! You will hear it in phrases like «До́брий де́нь!»
*   **Льві́в** (Lviv) — Here, **Ь** softens the **Л** right before the consonant **В**.
*   **мі́дь** (copper) — The **Д** becomes soft.
*   **о́сінь** (autumn) — A beautiful word for the season, ending softly.
*   **ми́ть** (moment) — Here, **Ь** softens the **Т** at the end. A fleeting instant!
*   **ті́нь** (shadow) — Here, **Ь** softens the **Н** at the end, just like in де́нь and кі́нь.

> [!tip] The Soft Sign Changes Everything
> The soft sign isn't just an accent; it can change the entire meaning of a word! Take a look at this minimal pair:
> *   **кі́н** (a stake in a game) — Hard **Н**.
> *   **кі́нь** (horse) — Soft **Н**.
> Adding **Ь** changes the preceding consonant's quality, creating a completely different word!

## Апостроф — The Apostrophe

You might be used to seeing an apostrophe as just a punctuation mark in English, but in Ukrainian, the apostrophe is a crucial part of spelling and pronunciation. The apostrophe separates a consonant from a following iotated vowel (**Я**, **Ю**, **Є**, **Ї**). Its job is preserving the **Й**-sound of the iotated vowel that would otherwise be absorbed into softening the consonant.

The rule is quite strict: the apostrophe appears after the consonants **Б**, **П**, **В**, **М**, **Ф**, **Р** before the vowels **Я**, **Ю**, **Є**, **Ї**.

Without the apostrophe, a combination like **М** + **Я** would mean "soft **М** + **А**". But with the apostrophe, **М'Я** means "hard **М** + **Й** + **А**". The apostrophe is NOT optional; it tells you exactly how to say the word!

Let's practice reading some common words with an apostrophe:
*   **м'я́со** (meat) — Hard **М**, followed by the **Й** sound, then **А**.
*   **п'я́ть** (five) — A very common number. Hard **П**, then **Й** sound.
*   **сім'я́** (family) — An incredibly high-frequency word you will use often.
*   **м'я́ч** (ball) — A common word from children's vocabulary.
*   **об'є́кт** (object) — Here, the apostrophe separates the prefix from the root.

> [!challenge] Can you spot the difference?
> Listen closely when native speakers say words like **м'я́со**. You will hear a distinct little break or a clear **Й** sound right where the apostrophe sits. Try saying it aloud yourself: hard **М**, then **Я**. You are doing great!

## Африкати, Щ та Ф — Affricates, Щ, and Ф

### Літера Ц
[Anna Ohoiko — Ukrainian Lessons — Ц](https://www.youtube.com/watch?v=u44eCjR2Oz8)

The letter **Ц** is a true affricate. This means it is the sounds **Т** and **С** fused together into one single sound, just like the English 'ts' in the word 'cats'. It is a sharp, crisp sound.
*   **цу́кор** (sugar) — An everyday kitchen word.
*   **цибу́ля** (onion) — Another common food item.
The **Ц** sound is also very common in Ukrainian word endings, like -ець or -иця.

> [!did-you-know] Загадка з Ц
> Here is a classic Ukrainian riddle: «Не годи́нник, а цо́к-цо́к-цо́к.» (Not a clock, but tick-tick-tick.) Can you guess? The answer is **цвірку́н** (cricket)! Riddles like these are used in Ukrainian schools to practice the Ц sound.

### Літера Ч
[Anna Ohoiko — Ukrainian Lessons — Ч](https://www.youtube.com/watch?v=UsJkbdsY2RA)

The letter **Ч** is another true affricate. It sounds exactly like the English 'ch' in 'church'. It is a very frequent letter in Ukrainian.
*   **ча́с** (time/hour) — A top 100 word you will need often.
*   **черепа́ха** (turtle) — A fun word from children's literature!
*   **ча́й** (tea) — A high-frequency drink.

### Літера Щ
[Anna Ohoiko — Ukrainian Lessons — Щ](https://www.youtube.com/watch?v=QmBLieIuf6Q)

Now for a big secret: **Щ** is NOT an affricate! Instead, it represents TWO separate sounds: **Ш** + **Ч**. It is a consonant cluster written as one convenient letter. You need to pronounce both sounds clearly, one after the other.
*   **що́** (what) — This word appears in almost every conversation!
*   **ще́** (still/more) — Very useful for asking for more tea!
*   **ща́стя** (happiness) — A beautiful, high-frequency word.

### Літера Ф
[Anna Ohoiko — Ukrainian Lessons — Ф](https://www.youtube.com/watch?v=haHRsFFZRQI)

The letter **Ф** sounds just like the English 'f'. It is actually quite rare in native Ukrainian words! It appears mostly in borrowings from other languages. It is the voiceless partner of the letter **В**.
*   **фа́кт** (fact) — An easy internationalism.
*   **фо́то** (photo) — Another familiar borrowed word.

> [!practice] Reading Practice
> Read these short dialogues out loud:
> > **(На кухні)**
> > — Це цу́кор?
> > — Та́к, це цу́кор.
>
> > **(Вдома)**
> > — Це ча́й?
> > — Ні́, це ка́ва.

## Диграфи ДЖ, ДЗ — Digraphs

Sometimes, Ukrainian uses two letters to represent one single sound. These are called digraphs. These are single phonemes written with two characters, and you should always read them as one smooth sound, not two separate ones.

The first digraph is **ДЖ**. This sounds just like the English 'j' in 'jungle'. It is the voiced partner of the letter **Ч**. Let's look at some examples:
*   **джерело́** (spring/source) — A beautiful nature word.
*   **бджола́** (bee) — Another great nature vocabulary word.

The second digraph is **ДЗ**. This sound has no direct English equivalent! You have to buzz it together as one sound. It is the voiced partner of the letter **Ц**. This sound is distinctly Ukrainian — a hallmark of authentic Ukrainian phonology.
*   **дзві́н** (bell) — A very important cultural word. Church bells are a big part of Ukrainian history.
*   **дзе́ркало** (mirror) — An everyday object you will find in any home.

> [!culture] Дзвін — The Sound of Ukraine
> Church bells (**дзві́н**) have deep cultural significance in Ukraine. The word **дзвін** is everywhere in Ukrainian life — from church towers to phone calls. The **ДЗ** sound is distinctly Ukrainian — you will not find it in many other languages. When you hear that buzzing **ДЗ**, you are hearing something uniquely Ukrainian!

> [!note] One Sound, Not Two
> Remember, when you see **ДЖ** or **ДЗ**, do not split them up! Treat them as a single sound block.

## Весь алфавіт! — The Full Alphabet Mastered

Congratulations! You have learned the complete 33-letter Ukrainian alphabet: **А Б В Г Ґ Д Е Є Ж З И І Ї Й К Л М Н О П Р С Т У Ф Х Ц Ч Ш Щ Ь Ю Я**. Plus, you know the digraphs **ДЖ**, **ДЗ** and the apostrophe.

### Full-Alphabet Reading Challenge
Let's put everything together. Try to read this short paragraph. It uses all the letter types you have learned — vowels, consonants, the soft sign, the apostrophe, affricates, and digraphs:
*   «Ту́т м'я́со, ри́ба, цу́кор і ча́й. Моя́ сім'я́ — це вели́ке ща́стя!»
*   «До́брий де́нь, Украї́но! Де́ дзві́н і бджола́?»

Now you can also read these essential survival phrases using the full alphabet. These are fixed phrases — you will learn how they work grammatically later. For now, just practice reading them aloud:
*   **До́брий де́нь!** (Good day!)
*   **Я́к спра́ви?** (How are you?)
*   **Дя́кую!** (Thank you!)
*   **Будь ла́ска!** (Please!)
*   **Хто́ це́?** (Who is this?)
*   **Що́ це́?** (What is this?)
*   **До поба́чення!** (Goodbye!)

Take a moment for a huge celebration: you can now decode any Ukrainian word you encounter. The reading skills you have built from Module 1 to Module 4 are the foundation for reading, writing, and speaking Ukrainian!

## Підсумок — Summary

You did it! You have mastered the final pieces of the Ukrainian alphabet. Let's do a quick recap:
*   The soft sign (**Ь**) softens consonants.
*   The apostrophe preserves the **Й**-sound before iotated vowels.
*   **Ц** and **Ч** are crisp affricates.
*   **Щ** is a **Ш** + **Ч** cluster.
*   **ДЖ** and **ДЗ** are unique digraphs.
*   **Ф** is a rare letter found mostly in borrowed words.

**Self-check time:**
*   What does **Ь** do to the letter before it?
*   When do you use an apostrophe in Ukrainian?
*   What two sounds does the letter **Щ** represent?
*   Can you read any Ukrainian word now? (Hint: The answer is yes!)

Next up in Module 5, we will look at syllables and word division. Get ready!
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/completing-the-alphabet.yaml`

```yaml
- type: watch-and-repeat
  title: "Watch and Repeat: New Letters and Sounds"
  instruction: "Watch each video by Anna Ohoiko. Listen carefully, then repeat the sound and example word aloud."
  items:
    - letter: "Ь"
      word: "сіль"
      video: "https://www.youtube.com/watch?v=cJlal8XKBxo"
      note: "The soft sign has no sound of its own — it softens the consonant before it."
    - letter: "Ц"
      word: "цукор"
      video: "https://www.youtube.com/watch?v=u44eCjR2Oz8"
      note: "Like the 'ts' in English 'cats'. A crisp affricate."
    - letter: "Ч"
      word: "час"
      video: "https://www.youtube.com/watch?v=UsJkbdsY2RA"
      note: "Like the 'ch' in English 'church'."
    - letter: "Щ"
      word: "що"
      video: "https://www.youtube.com/watch?v=QmBLieIuf6Q"
      note: "Two sounds fused together: Ш + Ч. Pronounce both clearly."
    - letter: "Ф"
      word: "факт"
      video: "https://www.youtube.com/watch?v=haHRsFFZRQI"
      note: "Like English 'f'. Rare in native Ukrainian words — mostly in borrowings."
    - letter: "Ґ"
      word: "ґанок"
      video: "https://www.youtube.com/watch?v=gNjHqjTW9WQ"
      note: "A hard 'g' sound, different from Г. Review from previous modules."
    - letter: "Apostrophe"
      word: "м'ясо"
      video: "https://www.youtube.com/watch?v=ksXIXj7CXwc"
      note: "The apostrophe separates a consonant from an iotated vowel, preserving the Й-sound. (Overview video — no dedicated apostrophe video available.)"
    - letter: "ДЖ"
      word: "джерело"
      video: "https://www.youtube.com/watch?v=ksXIXj7CXwc"
      note: "A digraph — two letters, one sound. Like English 'j' in 'jungle'. (Overview video — no dedicated ДЖ video available.)"
    - letter: "ДЗ"
      word: "дзвін"
      video: "https://www.youtube.com/watch?v=ksXIXj7CXwc"
      note: "A digraph — two letters, one sound. No English equivalent. Buzz it together. (Overview video — no dedicated ДЗ video available.)"
    - letter: "Ь"
      word: "день"
      video: "https://www.youtube.com/watch?v=cJlal8XKBxo"
      note: "Practice the soft sign again — compare день (soft Н) with ден (hard Н)."

- type: classify
  title: "Which Consonant Is Softened?"
  instruction: "Look at each word containing the soft sign (Ь). Drag it to the correct category based on which consonant is softened."
  categories:
    - label: "Soft Н"
      symbol_hint: "consonant"
      items: ["день", "кінь", "осінь", "тінь"]
    - label: "Soft Л"
      symbol_hint: "consonant"
      items: ["сіль", "Львів"]
    - label: "Soft Д"
      symbol_hint: "consonant"
      items: ["мідь"]
    - label: "Soft Т"
      symbol_hint: "consonant"
      items: ["мить"]

- type: image-to-letter
  title: "What Letter Does It Start With?"
  instruction: "Look at the picture. Which Ukrainian letter does this word begin with?"
  items:
    - emoji: "🧂"
      answer: "Ц"
      distractors: ["Ч", "С"]
      note: "цукор (sugar) starts with Ц"
    - emoji: "🕐"
      answer: "Ч"
      distractors: ["Ц", "Щ"]
      note: "час (time) starts with Ч"
    - emoji: "🐝"
      answer: "Б"
      distractors: ["Д", "Ж"]
      note: "бджола (bee) starts with Б"
    - emoji: "🐢"
      answer: "Ч"
      distractors: ["Ц", "Ш"]
      note: "черепаха (turtle) starts with Ч"
    - emoji: "🪞"
      answer: "Д"
      distractors: ["З", "Ж"]
      note: "дзеркало (mirror) starts with Д (part of digraph ДЗ)"
    - emoji: "🏔️"
      answer: "Д"
      distractors: ["Ж", "Г"]
      note: "джерело (spring) starts with Д (part of digraph ДЖ)"
    - emoji: "📸"
      answer: "Ф"
      distractors: ["В", "П"]
      note: "фото (photo) starts with Ф"
    - emoji: "🐴"
      answer: "К"
      distractors: ["Ч", "Н"]
      note: "кінь (horse) starts with К"

- type: quiz
  title: "Apostrophe Rules"
  instruction: "Choose the correct answer about how the apostrophe works in Ukrainian."
  vesum_exempt: true
  notes: "Distractors include intentional misspellings (мясо, мьясо, пять, пьять, сімя, сімья, обєкт, обьєкт) to test apostrophe knowledge. These are deliberately invalid forms."
  items:
    - question: "Which spelling is correct for the word meaning 'meat'?"
      options:
        - text: "м'ясо"
          correct: true
        - text: "мясо"
          correct: false
        - text: "мьясо"
          correct: false
        - text: "м ясо"
          correct: false
      explanation: "The apostrophe separates М from the iotated vowel Я, preserving the Й-sound."
    - question: "Which spelling is correct for the word meaning 'five'?"
      options:
        - text: "п'ять"
          correct: true
        - text: "пять"
          correct: false
        - text: "пьять"
          correct: false
        - text: "п ять"
          correct: false
      explanation: "After П, the apostrophe keeps the Й-sound in Я."
    - question: "Which spelling is correct for the word meaning 'family'?"
      options:
        - text: "сім'я"
          correct: true
        - text: "сімя"
          correct: false
        - text: "сімья"
          correct: false
        - text: "сім я"
          correct: false
      explanation: "The apostrophe after М preserves the Й-sound in Я."
    - question: "Which spelling is correct for the word meaning 'ball'?"
      options:
        - text: "м'яч"
          correct: true
        - text: "мяч"
          correct: false
        - text: "мьяч"
          correct: false
        - text: "м яч"
          correct: false
      explanation: "The apostrophe separates М from Я, keeping the Й-sound."
    - question: "Which spelling is correct for the word meaning 'object'?"
      options:
        - text: "об'єкт"
          correct: true
        - text: "обєкт"
          correct: false
        - text: "обьєкт"
          correct: false
        - text: "об єкт"
          correct: false
      explanation: "The apostrophe after Б separates it from the iotated vowel Є."
    - question: "After which group of consonants does the apostrophe appear?"
      options:
        - text: "Б, П, В, М, Ф, Р"
          correct: true
        - text: "Т, Д, Н, Л, С, З"
          correct: false
        - text: "К, Г, Х, Ж, Ш, Щ"
          correct: false
        - text: "All consonants"
          correct: false
      explanation: "The apostrophe appears only after Б, П, В, М, Ф, Р before iotated vowels."
    - question: "What does the apostrophe preserve in pronunciation?"
      options:
        - text: "The Й-sound of the following vowel"
          correct: true
        - text: "The hardness of the vowel"
          correct: false
        - text: "A pause between syllables"
          correct: false
        - text: "The stress on the vowel"
          correct: false
      explanation: "Without the apostrophe, the Й-sound would be absorbed into softening the consonant."
    - question: "Which word does NOT need an apostrophe?"
      options:
        - text: "цукор"
          correct: true
        - text: "м'ясо"
          correct: false
        - text: "п'ять"
          correct: false
        - text: "сім'я"
          correct: false
      explanation: "Цукор has no combination of Б/П/В/М/Ф/Р + iotated vowel, so no apostrophe is needed."
    - question: "Before which vowels does the apostrophe appear?"
      options:
        - text: "Я, Ю, Є, Ї"
          correct: true
        - text: "А, О, У, Е, И"
          correct: false
        - text: "І, И, Е, А"
          correct: false
        - text: "All vowels"
          correct: false
      explanation: "The apostrophe appears before iotated vowels only: Я, Ю, Є, Ї."
    - question: "In the word м'ясо, what does the apostrophe tell you about the М?"
      options:
        - text: "М stays hard, followed by Й + А"
          correct: true
        - text: "М becomes soft, followed by А"
          correct: false
        - text: "М is silent"
          correct: false
        - text: "М changes to a different sound"
          correct: false
      explanation: "The apostrophe means the consonant stays hard and the iotated vowel keeps its full Й + vowel sound."

- type: classify
  title: "Sort by Sound Type"
  instruction: "Sort these letters into the correct category based on what kind of sound they represent."
  categories:
    - label: "Affricate (two sounds fused into one)"
      symbol_hint: "consonant"
      items: ["Ц", "Ч"]
    - label: "Consonant cluster written as one letter"
      symbol_hint: "consonant"
      items: ["Щ"]
    - label: "Digraph (two letters = one sound)"
      symbol_hint: "consonant"
      items: ["ДЖ", "ДЗ"]
    - label: "Modifier (no sound of its own)"
      symbol_hint: "modifier"
      items: ["Ь", "Апостроф"]
    - label: "Simple consonant (single sound)"
      symbol_hint: "consonant"
      items: ["Ф"]

- type: fill-in
  title: "Complete the Phrase"
  instruction: "Choose the correct word to complete each phrase. These are survival phrases using the full alphabet."
  items:
    - sentence: "_____ день!"
      answer: "Добрий"
      options: ["Добрий", "Добре", "Доброго", "Добра"]
      explanation: "Добрий день! means Good day! — a standard Ukrainian greeting."
    - sentence: "Як _____?"
      answer: "справи"
      options: ["справи", "справа", "справ", "справу"]
      explanation: "Як справи? means How are you? — a common follow-up greeting."
    - sentence: "Хто _____?"
      answer: "це"
      options: ["це", "то", "тут", "там"]
      explanation: "Хто це? means Who is this?"
    - sentence: "Що _____?"
      answer: "це"
      options: ["це", "то", "тут", "там"]
      explanation: "Що це? means What is this?"
    - sentence: "До _____!"
      answer: "побачення"
      options: ["побачення", "зустрічі", "завтра", "вечора"]
      explanation: "До побачення! means Goodbye!"
    - sentence: "Це _____, а не кава."
      answer: "чай"
      options: ["чай", "час", "цукор", "щастя"]
      explanation: "Чай means tea — from the lesson dialogue."
    - sentence: "Моя _____ — це велике щастя!"
      answer: "сім'я"
      options: ["сім'я", "сіль", "осінь", "цибуля"]
      explanation: "Сім'я means family — practises reading the apostrophe from the lesson."
    - sentence: "Де _____ і бджола?"
      answer: "дзвін"
      options: ["дзвін", "дзеркало", "джерело", "день"]
      explanation: "Дзвін means bell — practises reading the ДЗ digraph from the lesson."

- type: match-up
  title: "Match the Phrase to Its Meaning"
  instruction: "Match each Ukrainian survival phrase to its English meaning."
  pairs:
    - left: "Добрий день!"
      right: "Good day!"
    - left: "Як справи?"
      right: "How are you?"
    - left: "Хто це?"
      right: "Who is this?"
    - left: "Що це?"
      right: "What is this?"
    - left: "До побачення!"
      right: "Goodbye!"
    - left: "Так"
      right: "Yes"
    - left: "Ні"
      right: "No"
    - left: "Це чай"
      right: "This is tea"
    - left: "Дякую!"
      right: "Thank you!"
    - left: "Будь ласка!"
      right: "Please!"
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/completing-the-alphabet.yaml`

```yaml
items:
  - lemma: "сіль"
    translation: "salt"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates Ь softening Л. Everyday kitchen word."
  - lemma: "день"
    translation: "day"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates Ь softening Н. Top 50 word. Used in Добрий день!"
  - lemma: "Львів"
    translation: "Lviv"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates Ь before consonant В. Major Ukrainian city."
  - lemma: "мідь"
    translation: "copper"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates Ь softening Д."
  - lemma: "осінь"
    translation: "autumn"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates Ь softening Н. Seasonal vocabulary."
  - lemma: "кінь"
    translation: "horse"
    pos: "noun"
    gender: "m"
    notes: "Minimal pair with кін (stake). Shows how Ь changes meaning."
  - lemma: "мить"
    translation: "moment; instant"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates Ь softening Т. Used in classify activity."
  - lemma: "тінь"
    translation: "shadow"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates Ь softening Н. Used in classify activity."
  - lemma: "м'ясо"
    translation: "meat"
    pos: "noun"
    gender: "n"
    notes: "Demonstrates apostrophe separating М from Я."
  - lemma: "п'ять"
    translation: "five"
    pos: "numeral"
    notes: "Demonstrates apostrophe after П before Я."
  - lemma: "сім'я"
    translation: "family"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates apostrophe. High-frequency word."
  - lemma: "м'яч"
    translation: "ball"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates apostrophe. Common children's vocabulary."
  - lemma: "цукор"
    translation: "sugar"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates Ц affricate. Everyday kitchen word."
  - lemma: "цибуля"
    translation: "onion"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates Ц. Common food vocabulary."
  - lemma: "час"
    translation: "time; hour"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates Ч affricate. Top 100 word."
  - lemma: "черепаха"
    translation: "turtle"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates Ч. Fun children's vocabulary word."
  - lemma: "чай"
    translation: "tea"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates Ч. High-frequency drink word."
  - lemma: "що"
    translation: "what"
    pos: "pronoun"
    notes: "Demonstrates Щ (Ш+Ч cluster). Top 10 word. Interrogative pronoun in 'Що це?'"
  - lemma: "щастя"
    translation: "happiness"
    pos: "noun"
    gender: "n"
    notes: "Demonstrates Щ. High-frequency word."
  - lemma: "факт"
    translation: "fact"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates Ф. Internationalism — easy to remember."
  - lemma: "джерело"
    translation: "spring; source"
    pos: "noun"
    gender: "n"
    notes: "Demonstrates ДЖ digraph. Nature vocabulary."
  - lemma: "дзвін"
    translation: "bell"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates ДЗ digraph. Culturally significant — church bells."
  - lemma: "об'єкт"
    translation: "object"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates apostrophe after Б before Є. Prefix-root separation."
  - lemma: "фото"
    translation: "photo"
    pos: "noun"
    gender: "n"
    notes: "Demonstrates Ф. Indeclinable borrowed word."
  - lemma: "ще"
    translation: "still; more"
    pos: "adverb"
    notes: "Demonstrates Щ. High-frequency adverb."
  - lemma: "бджола"
    translation: "bee"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates ДЖ digraph. Nature vocabulary."
  - lemma: "дзеркало"
    translation: "mirror"
    pos: "noun"
    gender: "n"
    notes: "Demonstrates ДЗ digraph. Everyday object."
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
- Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/completing-the-alphabet.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/completing-the-alphabet.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/completing-the-alphabet.yaml`

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
