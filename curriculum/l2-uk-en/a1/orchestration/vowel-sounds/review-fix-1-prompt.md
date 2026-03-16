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



**NOTE: 10 inline fix(es) from the review have ALREADY been applied to the files. Do NOT re-apply those fixes. Read the CURRENT file contents carefully — they reflect the post-fix state. Only fix issues that are still present in the current files.**

## Plan Adherence Issues (Deterministic — MUST FIX)

- **[HIGH] MISSING_STRUCTURAL_ELEMENT** in `Вступ — Introduction`
  - Expected: Plan point requires visual element: Review: M1 gave you the alphabet map and 10 practice letters. Today: the vowel system — 10 letters t
  - Actual: Section contains only prose — no table or bulleted list found
  - Fix: Add a markdown table or bulleted list to section 'Вступ — Introduction'

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:classify`
  - Expected: Plan requires ≥10 items
  - Actual: Activity has 8 items
  - Fix: Add 2 more items to 'classify' activity


---

## Critical Issues Found

### Issue 1: Non-Existent Distractor Words in Quiz (HIGH)
- **Location**: Activities file, lines 151, 162, 164 — quiz "The И vs І Distinction"
- **Original**: Distractors include "сар" (line 151), "сєр" (line 162), "сйр" (line 164)
- **Problem**: All three are VESUM-confirmed non-existent Ukrainian word forms. A1 learners seeing these as answer options may internalize them as real words. "сйр" is particularly bad — Й cannot follow a consonant in this position in Ukrainian orthography.
- **Fix**: Replace with real Ukrainian words that demonstrate vowel contrasts:
  - "сар" → "сур" (still non-standard) → better: "сор" (rubbish) — real word demonstrating О
  - "сєр" → "сер" — but this is also not standard. Better: replace entire distractor set with real minimal-pair words like "сон" (sleep), "сік" (juice), "сук" (bough)
  - "сйр" → "сюр" (surrealism, colloquial) — or simply "сік" (juice)

### Issue 2: Richness Gate Failure (HIGH)
- **Location**: Entire module — audit shows richness at 47% vs 95% threshold
- **Problem**: Missing engagement elements across multiple dimensions:
  - engagement: 3/5 (need 2 more `[!tip]`/`[!note]`/`[!practice]` boxes)
  - cultural: 0/3 (need 3 `[!culture]` or `[!did-you-know]` callouts)
  - examples: 0/24 (structural gap — inline examples exist but not in counted format)
  - dialogues: 2/4 (need 2 more dialogue blocks)
  - proverbs: 0/1 (need 1 proverb or saying)
  - tables: 0/2 (need 2 comparison/reference tables)
- **Fix**: See Fix Plan below for specific additions.

### Issue 3: LLM Filler in Section "Голосні в словах" (MEDIUM)
- **Location**: Line 84, section "Голосні в словах"
- **Original**: 「Great job so far! You have learned a lot of new sounds today, and you are doing exceptionally well.」
- **Problem**: Pure cheerleading with zero educational content. This is 19 words of filler before the section's actual teaching begins. At A1 some encouragement is fine, but this sentence teaches nothing.
- **Fix**: Combine encouragement with a teaching hook: "Great work on vowels and stress! Now let's put everything together by reading real Ukrainian words and sentences."

### Issue 4: LLM Filler in Section "Голосні в словах" (MEDIUM)
- **Location**: Line 103, section "Голосні в словах"
- **Original**: 「Every single syllable you count is a massive step forward in your language learning journey.」
- **Problem**: Generic AI motivational prose. "Language learning journey" is a classic LLM cliché. This sentence adds no teaching value.
- **Fix**: Replace with a practical pointer: "Counting syllables helps you read new words confidently — you will use this skill in every module."

### Issue 5: "лук (bow)" Translation (LOW)
- **Location**: Line 24, section "Шість основних голосних — Six Base Vowels"
- **Original**: 「Слова́ (Words): **тут** (here), **лук** (bow), **ву́хо** (ear).」
- **Problem**: "лук" primarily means "onion" in everyday Ukrainian. "Bow" (weapon) is a secondary meaning. For A1, "onion" is more useful everyday vocabulary.
- **Fix**: Change to **лук** (onion).

---

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Activities:151 | сар | сон (sleep) | Non-existent word |
| Activities:162 | сєр | сік (juice) | Non-existent word |
| Activities:164 | сйр | сор (rubbish) | Non-existent word |
| 24 | лук (bow) | лук (onion) | Translation |

---

## Fix Plan to Reach 9/10 (REQUIRED — score < 9.0)

### Activities: 7/10 → 9/10
**What to fix:**
1. Activities line 151: Change distractor "сар" → "сон" (real word, demonstrates О)
2. Activities line 162: Change distractor "сєр" → "сік" (real word, demonstrates І)
3. Activities line 164: Change distractor "сйр" → "сор" (real word, demonstrates О)

**Expected score after fix:** 9/10

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Section "Шість основних голосних": Add a comparison TABLE showing all 6 base vowels with their sounds and example words (fills tables gap)
2. Section "Йотовані голосні": Add a summary TABLE showing all 4 iotated vowels with their й+vowel breakdown
3. Section "Вступ — Introduction": Add a `[!did-you-know]` about Ukrainian having one of the most phonetic spelling systems in Europe (fills cultural gap)
4. Section "Наголос — Word Stress": Add a `[!culture]` about how наголос patterns differ by region
5. Section "Голосні в словах": Add 2 more short dialogue lines for reading practice (fills dialogues gap)
6. Section "Підсумок — Summary": Add a Ukrainian saying/proverb that uses many vowels as a practice sentence (fills proverbs gap)
7. Add 2 more engagement boxes (`[!practice]` or `[!tip]`) across sections

**Expected score after fix:** 9/10

### Pedagogy: 8/10 → 9/10
**What to fix:**
1. Line 40: Add 2-3 more И vs І minimal pairs beyond сир/сір (e.g., бити/біти, вити/віти)
2. Section "Голосні в словах": Organize reading words by vowel focus as plan specifies

**Expected score after fix:** 9/10

### LLM Fingerprint: 8/10 → 9/10
**What to fix:**
1. Line 84: Replace pure cheerleading with teaching-integrated encouragement
2. Line 103: Replace "language learning journey" cliché with practical advice
3. Line 4: "heartbeat of every Ukrainian word" — consider a more natural metaphor

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.1 + 9×1.2 + 9×1.3 + 9×1.3 + 9×1.0 + 9×1.5) / 8.9
= (13.5 + 9.9 + 10.8 + 11.7 + 11.7 + 9.0 + 13.5) / 8.9
= 80.1 / 8.9 = 9.0/10
```

---

## Audit Failures (from automated re-audit)

```
--- STRICT GATES (Level A1) ---
Pedagogy     ❌ 1 violations
📚 PEDAGOGICAL VIOLATIONS FOUND:
📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
→ 1 violations (minor)
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/vowel-sounds-audit.log for details)
⚠️  RAG verification found unverified words (see audit report)
--- VESUM WORD VERIFICATION FAILURES ---
These words were NOT found in the VESUM morphological dictionary.
Check if they are valid Ukrainian forms. Fix misspellings or Russianisms.
  ❌ `Європа` (source: prose)
```

---

## File Contents (for reference)

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vowel-sounds.md`

```markdown
## Вступ — Introduction
Приві́т (Hello) back! You are doing very well. У пе́ршому мо́дулі (In Module 1), you learned the alphabet map and your first 10 practice letters. Сього́дні (Today), we are focusing on the beautiful vowel system. 

The Ukrainian alphabet has exactly 10 vowel letters, and they carry every Ukrainian word forward. Why do vowels matter so much? Because every single syllable has exactly one vowel. If you count the vowels in a word, you know exactly how many syllables that word has. Це ду́же про́сто!

This means reading Ukrainian is incredibly logical. By the end of this module, you will be able to pronounce all 10 vowel letters confidently and read many new words. Let's get started!

## Шість основних голосних — Six Base Vowels
В украї́нській мо́ві шість голосних зву́ків (There are six base vowel sounds in Ukrainian). Let's look at each one carefully and listen to how they sound. 

> [!did-you-know] Цікавий факт (Fun Fact)
> Ukrainian has one of the most phonetic spelling systems in Europe. Each letter almost always represents the same sound — what you see is what you say! This makes reading much easier once you learn the vowels. 

### Літера А
The letter **А** sounds open, very much like the 'a' in the English word 'father'. It is a strong, clear sound that never reduces or changes.
При́клади (Examples): **ма́ма** (mom), **ка́ша** (porridge), **са́ло** (lard).

### Літера О
The letter **О** is well-rounded, like the 'o' in 'more'. Here is a critical rule: it stays **О** even when it is unstressed. It never becomes a lazy "uh" sound. Keep your lips rounded!
При́клади (Examples): **о́ко** (eye), **молоко́** (milk), **село́** (village).

> [!note] Примітка: Чистота звуку (Note: Sound Purity)
> Remember that the **О** sound must remain clear and distinct, no matter its position in the word.

### Літера У
The letter **У** sounds just like the 'oo' in 'moon'. It is a deep, resonant sound.
Слова́ (Words): **тут** (here), **лук** (onion), **ву́хо** (ear).

### Літера Е
The letter **Е** sounds like the 'e' in 'set'. It is NOT like the English 'ee'. Notice the new consonants **Д**, **В**, and **Р** in these examples — your focus should be entirely on producing a clear vowel sound.
При́клади (Examples): **не́бо** (sky), **село́** (village), **день** (day).

### Літера И
The letter **И** is uniquely Ukrainian. There is no exact English equivalent for this sound. Keep your jaw relaxed, and your tongue lower than for the letter **І**. It sounds somewhat like the 'i' in 'sit', but deeper and further back in the mouth.
Пра́ктика (Practice): **ри́ба** (fish), **сир** (cheese), **син** (son).

### Літера І
The letter **І** sounds like the 'ee' in 'see'. It is much brighter and higher than **И**. When you say it, your mouth should be smiling.
При́клади (Examples): **ліс** (forest), **кіт** (cat), **сік** (juice).

> [!practice] Practice: The И vs І Distinction
> The distinction between **И** and **І** is the hardest vowel contrast for English speakers to master. Let's drill with minimal pairs. Say them out loud and feel your jaw position change as you say these!
> * **сир** (cheese) vs **сір** (grey)
> * **бити** (to beat) vs **біти** (to whiten)
> * **вити** (to howl) vs **віти** (to wind)

## Наголос — Word Stress

| Голосна | Sound | Example |
|---------|-------|---------|
| **А** | 'a' in 'father' | ма́ма |
| **О** | 'o' in 'more' | о́ко |
| **У** | 'oo' in 'moon' | тут |
| **Е** | 'e' in 'set' | не́бо |
| **И** | deeper 'i' in 'sit' | ри́ба |
| **І** | 'ee' in 'see' | кіт |

Every Ukrainian word has exactly one stressed syllable. This is called **наголос** (word stress). The stressed vowel is pronounced louder and slightly longer than the others. But here is the most important part: its quality does NOT change at all.

> [!tip] The Golden Rule of Ukrainian Vowels
> Ukrainian vowels stay pure in any position — whether they are stressed or unstressed. English speakers naturally swallow unstressed vowels into a weak "uh" sound (called a schwa). You must fight this instinct! Every vowel deserves to be heard clearly.

Let's look closely at the word **молоко́** (milk). The stress is on the very last syllable, but all three **О**'s sound exactly the same. Compare this to the English word 'photograph', where the 'o' vowels shift and change depending on the stress. In Ukrainian, you must keep every vowel clear and pure. Take your time when reading to pronounce every letter!

## Йотовані голосні — Iotated Vowels
Now let's meet the four iotated vowels: **Я**, **Ю**, **Є**, and **Ї**. Think of them as special "double-duty" vowels. At the start of a word, or immediately after another vowel, they represent TWO distinct sounds: the **Й** (y-sound) plus a base vowel. 

### Літера Я
**Я** makes the sounds й+а.
* At the start of a word, you hear both sounds clearly: **я́блуко** (apple)
* After another vowel, it remains two sounds: **моя́** (my, feminine)
* After a consonant, it softens that consonant. Compare **ма́ти** (mother) vs **м'я́ти** (to crumple) — notice how the apostrophe is used to preserve the **Й** sound!

### Літера Ю
**Ю** makes the sounds й+у.
* At the start of a word, it is two sounds: **юна́к** (young man), **ю́шка** (broth)
* After a consonant, it softens it. For example, in **лю́ди** (people), the **Л** becomes a soft sound.

### Літера Є
**Є** makes the sounds й+е.
* At the start of a word: **Євро́па** (Europe)
* After another vowel, you hear both sounds: **моє́** (my, neuter)

> [!myth-buster] Міф (Myth-buster)
> Some learners think iotated vowels are entirely new sounds. They are not! They are just combinations of the familiar **Й** and the base vowels you already know.

### Літера Ї
**Ї** is very special: it ALWAYS makes two sounds (й+і) and it never softens a preceding consonant. You will always pronounce it as a strong, clear combination.
Слова́ (Words): **їжа́к** (hedgehog), **ї́жа** (food), **Украї́на** (Ukraine).

> [!culture] Cultural Note: The Letter Ї
> The letter **Ї** is unique to the Ukrainian alphabet. It has become a powerful symbol of Ukrainian identity, culture, and resistance. You will see it proudly displayed all over the country.

### Напівголосний Й — The Semi-Vowel Й
**Й** is a semi-vowel. It makes a short, consonant-like "y" sound, very similar to the English word "yes" or "boy". It never forms a syllable on its own.
При́клади (Examples): **край** (edge/land), **йо́гурт** (yogurt).

## Голосні в словах — Vowels in Words
Great work on vowels and stress! Now let's put everything together by reading real Ukrainian words and short sentences. Do not worry about the consonants you have not officially learned yet. Just focus entirely on making those vowel sounds pure, clear, and distinct.

Read these short sentences out loud. Take a deep breath and give every single vowel its full value:

> **(Вдома / At Home)**
> — Це я́блуко.
> — Це моє́ село́.
> — Це ма́ма і та́то.
> — Де мій кіт?

Now, let's do a quick count-the-vowels exercise to find the exact number of syllables. This is a very useful trick for beginners. Remember the golden rule: one vowel always equals one syllable! Let's count them together right now:

* **молоко́** (3 vowels = 3 syllables)
* **Украї́на** (4 vowels = 4 syllables)
* **кіт** (1 vowel = 1 syllable)
* **яйце́** (2 vowels = 2 syllables)
* **о́ко** (2 vowels = 2 syllables)
* **ву́хо** (2 vowels = 2 syllables)

Take your time reading these aloud. Don't rush through them! Counting syllables helps you read new words confidently — you will use this skill in every module. You are already reading real Ukrainian sentences, and that is a truly wonderful achievement. Keep practicing!

> [!culture] Культурна нотатка (Culture Note)
> Ukrainian vowel purity is something Ukrainians are proud of. The clear, musical quality of Ukrainian vowels is one reason the language is often called one of the most melodic in the world.

> [!tip] Приказка (Saying)
> Try reading this Ukrainian saying aloud, focusing on making every vowel pure: **Око за око, зуб за зуб** (An eye for an eye, a tooth for a tooth). Count the vowels: 8 vowels, 8 syllables!

## Підсумок — Summary
You have made excellent progress today. You now know all 10 vowel letters: the 6 base vowels (**А**, **О**, **У**, **Е**, **И**, **І**), the 4 iotated vowels (**Я**, **Ю**, **Є**, **Ї**), plus the semi-vowel **Й**. Це вели́ке дося́гнення!

Always remember the Golden Rule: Ukrainian vowels stay pure. Never swallow or reduce them, no matter where the stress falls in the word. Your goal is clarity.

Let's do a quick self-check to see what you remember:
1. Can you pronounce all 6 base vowels clearly out loud?
2. What two sounds does **Я** make at the start of a word?
3. Can you hear and feel the difference between **И** and **І**?

Don't worry if you need a little more practice; you will hear and use these vowels in every single lesson from now on. In Module 3, we will master the consonant system, exploring voiced and voiceless pairs, sonorants, and the difference between hard and soft sounds. Keep up the fantastic work!
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/vowel-sounds.yaml`

```yaml
- type: watch-and-repeat
  title: "Pronounce the Vowels"
  instruction: "Watch the video to hear the correct pronunciation, then repeat the letter out loud."
  items:
    - letter: "А"
      word: "мама"
      video: "https://www.youtube.com/watch?v=hvB3VpcR3ZE"
    - letter: "О"
      word: "око"
      video: "https://www.youtube.com/watch?v=gJFxRIPRZbI"
    - letter: "У"
      word: "вухо"
      video: "https://www.youtube.com/watch?v=VB1O6PmtYRU"
    - letter: "Е"
      word: "небо"
      video: "https://www.youtube.com/watch?v=KFlsroBW0dk"
    - letter: "И"
      word: "риба"
      video: "https://www.youtube.com/watch?v=W-1rCu0indE"
    - letter: "І"
      word: "кіт"
      video: "https://www.youtube.com/watch?v=Z9TH0H4ShGo"
    - letter: "Я"
      word: "яблуко"
      video: "https://www.youtube.com/watch?v=yhSAf41LX8I"
    - letter: "Ю"
      word: "юнак"
      video: "https://www.youtube.com/watch?v=9JdIBYCTWGw"
    - letter: "Є"
      word: "Європа"
      video: "https://www.youtube.com/watch?v=O0bwRyyBQSc"
    - letter: "Ї"
      word: "їжак"
      video: "https://www.youtube.com/watch?v=UcjdjQXhAY8"

- type: classify
  title: "Base vs. Iotated Vowels"
  instruction: "Sort the vowel letters into the correct category."
  categories:
    - label: "Base Vowels"
      symbol_hint: "vowel"
      items:
        - "А"
        - "О"
        - "У"
        - "Е"
        - "И"
        - "І"
    - label: "Iotated Vowels"
      symbol_hint: "vowel"
      items:
        - "Я"
        - "Ю"
        - "Є"
        - "Ї"

- type: image-to-letter
  title: "First Letter Match"
  instruction: "Look at the emoji and select the vowel letter the Ukrainian word starts with."
  items:
    - emoji: "🍎"
      answer: "Я"
      distractors:
        - "А"
        - "Е"
        - "Ю"
      note: "яблуко"
    - emoji: "🦔"
      answer: "Ї"
      distractors:
        - "І"
        - "И"
        - "Є"
      note: "їжак"
    - emoji: "👁️"
      answer: "О"
      distractors:
        - "А"
        - "У"
        - "Е"
      note: "око"
    - emoji: "🥚"
      answer: "Я"
      distractors:
        - "Ю"
        - "Є"
        - "Ї"
      note: "яйце"
    - emoji: "🇺🇦"
      answer: "У"
      distractors:
        - "О"
        - "А"
        - "І"
      note: "Україна"
    - emoji: "👦"
      answer: "Ю"
      distractors:
        - "У"
        - "Я"
        - "Є"
      note: "юнак"
    - emoji: "🇪🇺"
      answer: "Є"
      distractors:
        - "Е"
        - "Ї"
        - "Я"
      note: "Європа"
    - emoji: "🍲"
      answer: "Ї"
      distractors:
        - "І"
        - "И"
        - "Є"
      note: "їжа"

- type: quiz
  title: "The И vs І Distinction"
  instruction: "Test your understanding of the difference between the letters И and І."
  items:
    - question: "Which letter sounds bright and high, similar to the 'ee' in the English word 'see'?"
      explanation: "І is pronounced like 'ee'."
      options:
        - text: "І"
          correct: true
        - text: "И"
          correct: false
        - text: "Е"
          correct: false
        - text: "Ї"
          correct: false
    - question: "Which letter has no exact English equivalent and sounds deeper, somewhat like the 'i' in 'sit'?"
      explanation: "И is the unique, deeper Ukrainian vowel."
      options:
        - text: "И"
          correct: true
        - text: "І"
          correct: false
        - text: "Й"
          correct: false
        - text: "У"
          correct: false
    - question: "Which word means cheese and uses the deeper vowel sound?"
      explanation: "Сир means cheese and uses the letter И."
      options:
        - text: "сир"
          correct: true
        - text: "сір"
          correct: false
        - text: "сон"
          correct: false
        - text: "сур"
          correct: false
    - question: "Which word means grey and uses the brighter vowel sound?"
      explanation: "Сір means grey and uses the letter І."
      options:
        - text: "сір"
          correct: true
        - text: "сир"
          correct: false
        - text: "сік"
          correct: false
        - text: "сор"
          correct: false
    - question: "Look at the word кіт (cat). Which vowel sound does it contain?"
      explanation: "Кіт contains the bright І sound."
      options:
        - text: "The bright 'ee' sound (І)"
          correct: true
        - text: "The deep 'i' sound (И)"
          correct: false
        - text: "The rounded 'o' sound (О)"
          correct: false
        - text: "The open 'a' sound (А)"
          correct: false
    - question: "Look at the word риба (fish). Which vowel is the first one?"
      explanation: "Риба uses the deeper И."
      options:
        - text: "И"
          correct: true
        - text: "І"
          correct: false
        - text: "Ї"
          correct: false
        - text: "Й"
          correct: false
    - question: "When pronouncing І, your mouth should be doing what?"
      explanation: "І is bright and high, so your mouth should be smiling."
      options:
        - text: "Smiling"
          correct: true
        - text: "Relaxed and open"
          correct: false
        - text: "Rounded like a circle"
          correct: false
        - text: "Closed completely"
          correct: false
    - question: "When pronouncing И, your jaw and tongue should be..."
      explanation: "For И, keep your jaw relaxed and your tongue lower than for І."
      options:
        - text: "Relaxed and lower"
          correct: true
        - text: "High and tight"
          correct: false
        - text: "Rounded and pushed forward"
          correct: false
        - text: "Touching your teeth"
          correct: false
    - question: "Look at the word син (son). Does it use И or І?"
      explanation: "Син uses the letter И."
      options:
        - text: "И"
          correct: true
        - text: "І"
          correct: false
        - text: "Ї"
          correct: false
        - text: "Є"
          correct: false
    - question: "Look at the word ліс (forest). Which vowel is in the middle?"
      explanation: "Ліс uses the bright І."
      options:
        - text: "І"
          correct: true
        - text: "И"
          correct: false
        - text: "Е"
          correct: false
        - text: "Ї"
          correct: false

- type: classify
  title: "Iotated Vowels: One Sound or Two?"
  instruction: "Sort the words based on whether the iotated vowel makes one sound (softening the consonant) or two sounds (Й + vowel)."
  categories:
    - label: "Two Sounds (Й + vowel)"
      symbol_hint: "vowel"
      items:
        - "яблуко"
        - "юнак"
        - "моя"
        - "моє"
        - "їжак"
        - "Європа"
        - "Україна"
    - label: "One Sound (Softens consonant)"
      symbol_hint: "consonant"
      items:
        - "люди"

- type: fill-in
  title: "Count the Syllables"
  instruction: "Remember the Golden Rule: one vowel equals one syllable! Select the correct number of syllables for each word."
  items:
    - sentence: "The word молоко has ___ syllables."
      answer: "3"
      options:
        - "1"
        - "2"
        - "3"
        - "4"
    - sentence: "The word кіт has ___ syllable."
      answer: "1"
      options:
        - "1"
        - "2"
        - "3"
        - "4"
    - sentence: "The word око has ___ syllables."
      answer: "2"
      options:
        - "1"
        - "2"
        - "3"
        - "4"
    - sentence: "The word Україна has ___ syllables."
      answer: "4"
      options:
        - "2"
        - "3"
        - "4"
        - "5"
    - sentence: "The word яйце has ___ syllables."
      answer: "2"
      options:
        - "1"
        - "2"
        - "3"
        - "4"
    - sentence: "The word вухо has ___ syllables."
      answer: "2"
      options:
        - "1"
        - "2"
        - "3"
        - "4"
    - sentence: "The word яблуко has ___ syllables."
      answer: "3"
      options:
        - "1"
        - "2"
        - "3"
        - "4"
    - sentence: "The word сир has ___ syllable."
      answer: "1"
      options:
        - "1"
        - "2"
        - "3"
        - "4"

- type: true-false
  title: "Vowel Rules: True or False?"
  instruction: "Test your knowledge of Ukrainian vowel rules."
  items:
    - statement: "In Ukrainian, unstressed vowels change their sound and become weak."
      correct: false
      explanation: "False! The Golden Rule is that Ukrainian vowels stay pure, whether stressed or unstressed."
    - statement: "Every Ukrainian word has exactly one stressed syllable."
      correct: true
      explanation: "True. One syllable is always pronounced louder and slightly longer."
    - statement: "The letter О should sound like an 'uh' if it is not stressed."
      correct: false
      explanation: "False. The letter О always stays well-rounded and pure, never reducing to 'uh'."
    - statement: "The letter Й is a semi-vowel and never forms a syllable on its own."
      correct: true
      explanation: "True. It makes a short consonant-like sound, similar to 'y' in 'yes'."
    - statement: "The iotated vowel Ї always represents two sounds (й+і)."
      correct: true
      explanation: "True. Ї is special and never softens a consonant; it always makes two sounds."
    - statement: "The letter А is an iotated vowel."
      correct: false
      explanation: "False. А is one of the six base vowels."
    - statement: "The number of syllables in a Ukrainian word is equal to the number of vowels."
      correct: true
      explanation: "True. Every syllable contains exactly one vowel."
    - statement: "The letter Е sounds exactly like the English 'ee'."
      correct: false
      explanation: "False. Е sounds like the 'e' in 'set', while І sounds like the English 'ee'."

- type: match-up
  title: "Vocabulary Match"
  instruction: "Match the Ukrainian words with their English translations."
  pairs:
    - left: "яблуко"
      right: "apple"
    - left: "риба"
      right: "fish"
    - left: "молоко"
      right: "milk"
    - left: "село"
      right: "village"
    - left: "їжак"
      right: "hedgehog"
    - left: "юнак"
      right: "young man"
    - left: "край"
      right: "edge/land"
    - left: "небо"
      right: "sky"
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/vowel-sounds.yaml`

```yaml
items:
  - lemma: "яблуко"
    translation: "apple"
    pos: "noun"
    notes: "Starts with iotated Я (й+а)"
  - lemma: "риба"
    translation: "fish"
    pos: "noun"
    notes: "Uses the deep И sound"
  - lemma: "село"
    translation: "village"
    pos: "noun"
  - lemma: "Україна"
    translation: "Ukraine"
    pos: "noun"
    notes: "Contains the special letter Ї"
  - lemma: "їжак"
    translation: "hedgehog"
    pos: "noun"
  - lemma: "юнак"
    translation: "young man"
    pos: "noun"
  - lemma: "край"
    translation: "edge/land"
    pos: "noun"
    notes: "Ends with the semi-vowel Й"
  - lemma: "день"
    translation: "day"
    pos: "noun"
  - lemma: "син"
    translation: "son"
    pos: "noun"
  - lemma: "моя"
    translation: "my (feminine)"
    pos: "pronoun"
  - lemma: "вухо"
    translation: "ear"
    pos: "noun"
  - lemma: "їжа"
    translation: "food"
    pos: "noun"
  - lemma: "моє"
    translation: "my (neuter)"
    pos: "pronoun"
  - lemma: "яйце"
    translation: "egg"
    pos: "noun"
  - lemma: "юшка"
    translation: "soup/broth"
    pos: "noun"
  - lemma: "каша"
    translation: "porridge"
    pos: "noun"
  - lemma: "небо"
    translation: "sky"
    pos: "noun"
  - lemma: "сир"
    translation: "cheese"
    pos: "noun"
  - lemma: "молоко"
    translation: "milk"
    pos: "noun"
    notes: "3 syllables, all Оs sound identical"
  - lemma: "кіт"
    translation: "cat"
    pos: "noun"
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
- Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vowel-sounds.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/vowel-sounds.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/vowel-sounds.yaml`

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
