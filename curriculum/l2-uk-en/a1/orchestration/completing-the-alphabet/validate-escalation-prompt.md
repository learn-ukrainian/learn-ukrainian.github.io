        # Escalation Fix — validate

        You are an expert Ukrainian language editor. The previous agent could not fix
        these audit violations. Fix them precisely.

        ## Audit Errors

        ```
          ✨ Purity violations found: 1
     ❌ [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'in module...'.

--- STRICT GATES (Level A1) ---
Persona      ✅ Persona Defined
Words        ✅ 1664/1200 (raw: 1820)
Activities   ⏳ Deferred (content-only audit)
Density      ⏳ Deferred (content-only audit)
Unique_types ⏳ Deferred (content-only audit)
Priority     ⏳ Deferred (content-only audit)
Engagement   ✅ 7/3
Audio        ℹ️ No audio
Vocab        ⏳ Deferred (content-only audit)
Structure    ✅ Valid Structure
Lint         ✅ Clean Format
Pedagogy     ❌ 2 violations
Content_heavy ⏳ Deferred (content-only audit)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ⏳ Deferred (content-only audit)
Research     ✅ Content aligned with research
Immersion    🇺🇦 9.7% (target 5-15% (M04))

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [GRAMMAR] Instrumental case used at A1: 'перед апострофом'
     → FIX: Instrumental case not allowed until A2 (M36+). Restructure sentence.
  [GRAMMAR] Subordinate clause marker at A1: 'є, що п'
     → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'in module...'.
     → FIX: Vary sentence structure.


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
   → 3 violations (minor)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/completing-the-alphabet-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/completing-the-alphabet.json

❌ AUDIT FAILED. Correct errors before proceeding.

❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/completing-the-alphabet-audit.log for details)

Running RAG word verification...
Verifying: completing-the-alphabet.md
  VESUM misses: 6 — querying RAG...
[embed] Loading BGE-M3 from BAAI/bge-m3...

Fetching 30 files:   0%|          | 0/30 [00:00<?, ?it/s]
Fetching 30 files: 100%|██████████| 30/30 [00:00<00:00, 74631.74it/s]
[embed] BGE-M3 loaded.
You're using a XLMRobertaTokenizerFast tokenizer. Please note that with a fast tokenizer, using the `__call__` method is faster than using a method to encode the text followed by a call to the `pad` method to get a padded encoding.
  Words: 68 | VESUM: 62 (91.2%) | RAG: 4 | Not found: 2
  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/completing-the-alphabet-rag-audit.md
⚠️  RAG verification found unverified words (see audit report)

Prose-relevant failures:
  lesson: 1664/1200 (raw: 1820) | pedagogy: 2 violations
VESUM: 62/68 (91%) verified
⚠️ VESUM not found (5): ДЖ, ДЗ, ець, иця, шо
        ```

        ## Current Content of Affected Section(s)

        - **кінь** — horse (the **Н** is soft)
- **кін** — a stake in a game (the **Н** is hard)

One tiny letter makes a completely different word. That's the power of **Ь**! Don't skip it when you read — it matters.

<!-- adapted from: Bolshakova, Grade 2, p. 43 -->

> [!practice] Try it yourself
> Say **день** out loud. Now say **ден** (without softening). Feel how your tongue position changes? That difference is what **Ь** creates.

## Апостроф — The Apostrophe

### Why Ukrainian Needs It

Remember the iotated vowels from Module 2? **Я**, **Ю**, **Є**, **Ї** each contain a hidden **Й**-sound. The apostrophe (**'**) keeps that **Й**-sound alive.

Without an apostrophe, a consonant followed by **Я** would simply mean "soft consonant + А." But sometimes you need "hard consonant + Й + А" — and that's exactly what the apostrophe signals.

Here's the key comparison:

- Without apostrophe: М + Я = soft **М** + **А** sound
- With apostrophe: М **'** Я = hard **М** + **Й** + **А** sound

The apostrophe is NOT optional. It changes how the word sounds and what it means.

<!-- adapted from: Bolshakova, Grade 2, p. 57 -->

### Words with the Apostrophe

- **м'ясо** — meat (hard **М**, then **Й** + **А**)
- **п'ять** — five (hard **П**, then **Й** + **А**)
- **сім'я** — family (hard **М**, then **Й** + **А**)
- **м'яч** — ball (hard **М**, then **Й** + **А**)
- **об'єкт** — object (hard **Б**, then **Й** + **Е**)

> [!note] The Apostrophe Rule
> The apostrophe appears after the consonants **Б**, **П**, **В**, **М**, **Ф**, **Р** — and only before the iotated vowels **Я**, **Ю**, **Є**, **Ї**. If you see one of these consonants followed by a iotated vowel, expect an apostrophe.

<!-- adapted from: Kravtsova, Grade 2, p. 44 -->

### Seeing It in Context

Look at these words your **сім'я** might use in the kitchen:

- **М'ясо** тут. — The meat is here.
- **П'ять**? — Five?
- Це моя **сім'я**. — This is my family.

> [!tip] Quick memory trick
> The apostrophe looks like a tiny separator — and that's exactly what it does! It separates the consonant from the iotated vowel, keeping them independent.

Notice how the Grade 2 textbook (Bolshakova) explains it: «Апостроф — це знак **'**. Він показує, що приголосний звук перед апострофом твердий, а букви я, ю, є позначають два звуки.» The consonant stays hard, and the vowel letter keeps its two sounds.

## Африкати, Щ та Ф — Affricates, Щ, and Ф

### Ц — Like «ts» in «cats»

**Ц** is a true affricate: two sounds — **Т** and **С** — fused into one. If you can say the English word "cats," you already know this sound. Just take the "ts" at the end and put it at the beginning of a word.

📹 *Watch Anna Ohoiko demonstrate Ц:*
[Anna Ohoiko — Ukrainian Lessons — Ц](https://www.youtube.com/watch?v=u44eCjR2Oz8)

Words with **Ц**:

- **цукор** — sugar
- **цибуля** — onion

You'll see **Ц** often in word endings like **-ець** and **-иця**. For now, just get comfortable with the sound at the start of words.

> [!culture] Kitchen words
> Notice that **цукор** and **цибуля** are both kitchen words. When you're cooking, you're practicing Ukrainian phonology!

### Ч — Like «ch» in «church»

**Ч** is another affricate, and you already know the sound — it's like English "ch" in "church." This letter is very frequent in Ukrainian.

📹 *Watch Anna Ohoiko demonstrate Ч:*
[Anna Ohoiko — Ukrainian Lessons — Ч](https://www.youtube.com/watch?v=UsJkbdsY2RA)

Words with **Ч**:

- **час** — time, hour
- **чай** — tea
- **черепаха** — turtle

**Час** is a top-100 Ukrainian word. You'll hear it and read it constantly.

### Щ — Two Sounds in One Letter

Here's a surprise: **Щ** is NOT a single sound. It represents TWO sounds: **Ш** + **Ч** — a consonant cluster written as one letter. When you say **Щ**, start with **Ш** and let it flow into **Ч**.

📹 *Watch Anna Ohoiko demonstrate Щ:*
[Anna Ohoiko — Ukrainian Lessons — Щ](https://www.youtube.com/watch?v=QmBLieIuf6Q)

Words with **Щ**:

- **що** — what (you'll use this in almost every conversation!)
- **ще** — still, more
- **щастя** — happiness

> [!warning] Common mistake
> Don't pronounce **що** as «шо»! Standard Ukrainian **що** has both sounds: **Ш** + **Ч**. Saying just **Ш** is a colloquial shortcut — in writing and careful speech, always use the full **Щ** sound.

### Ф — The Rare Letter

**Ф** sounds just like English "f" — no surprise there. But here's an interesting fact: **Ф** is rare in native Ukrainian words. Most words with **Ф** are borrowings from other languages.

📹 *Watch Anna Ohoiko demonstrate Ф:*
[Anna Ohoiko — Ukrainian Lessons — Ф](https://www.youtube.com/watch?v=haHRsFFZRQI)

Words with **Ф**:

- **факт** — fact (an internationalism — similar in many languages)
- **фото** — photo

You won't see **Ф** as often as **Ч** or **Ц**, but when you do, you already know exactly how to pronounce it.

## Диграфи ДЖ, ДЗ — Digraphs

Some Ukrainian sounds need two letters to write. These are **digraphs** — two letters that represent a single sound. Don't read them as separate letters!

### ДЖ — Like «j» in «jungle»

**ДЖ** is one sound, not **Д** + **Ж**. It's the voiced partner of **Ч** — just like "j" in the English word "jungle."

Words with **ДЖ**:

- **джерело** — spring, source (imagine a natural spring in the mountains)
- **бджола** — bee

> [!tip] How to know it's one sound
> If **ДЖ** appears within the same syllable, it's one sound. In **джерело**, the **ДЖ** starts the word together — one sound. In **бджола**, the **ДЖ** is also one sound within the syllable.

### ДЗ — Uniquely Ukrainian

**ДЗ** is the voiced partner of **Ц**. There's no exact English equivalent — it's like a voiced "ts." This sound is uniquely Ukrainian.

📹 *Watch Anna Ohoiko demonstrate Ґ (and hear about the voiced/voiceless pairs):*
[Anna Ohoiko — Ukrainian Lessons — Ґ](https://www.youtube.com/watch?v=gNjHqjTW9WQ)

Words with **ДЗ**:

- **дзвін** — bell (think of Ukrainian church bells ringing — a beautiful cultural image)
- **дзеркало** — mirror

> [!culture] The sound of Ukraine
> The word **дзвін** captures something deeply Ukrainian — the sound of church bells across villages and cities. This digraph **ДЗ** is a distinctive feature of Ukrainian phonology.

## Весь алфавіт! — The Full Alphabet Mastered

You did it! Here is the complete 33-letter Ukrainian alphabet, plus the digraphs and apostrophe:

**А Б В Г Ґ Д Е Є Ж З И І Ї Й К Л М Н О П Р С Т У Ф Х Ц Ч Ш Щ Ь Ю Я**

Plus the digraphs **ДЖ** and **ДЗ**, and the apostrophe **'**.

### Reading Challenge

Try reading this paragraph out loud. It uses vowels, consonants, the soft sign, the apostrophe, affricates, and digraphs — everything you've learned:

> **Добрий день! Моя сім'я тут. М'ясо, сіль, цукор, чай — це наша їжа. Я бачу бджолу. Дзвін! Що це? Це щастя!**

You can decode every word. Every single one!

### Survival Phrases

Now that you can read the full alphabet, here are five phrases you'll use again and again:

- **Добрий день!** — Good day!
- **Як справи?** — How are you?
- **Дякую!** — Thank you!
- **Будь ласка!** — Please! / You're welcome!
- **До побачення!** — Goodbye!

Read them out loud. Notice the soft sign in **день**, the affricate in **Дякую**, the **Щ** cluster in **справи**... You're reading real Ukrainian!

> [!challenge] Full alphabet celebration
> Go back to Module 1 and look at the alphabet chart. Every letter that once looked unfamiliar — you now know what it sounds like, how it behaves, and where to find it in real words. That is a real achievement. You're ready for everything that comes next.

## Підсумок — Summary

You've completed the Ukrainian alphabet! Here's what you learned today:

- **Ь** (soft sign) softens the consonant before it — it has no sound of its own
- The **apostrophe** (**'**) separates a consonant from a iotated vowel, preserving the **Й**-sound
- **Ц** and **Ч** are affricates (fused sounds: Т+С and Т+Ш respectively)
- **Щ** represents two sounds: **Ш** + **Ч** — written as one letter
- **ДЖ** and **ДЗ** are digraphs — two letters, one sound each
- **Ф** is rare in native Ukrainian words — mostly found in borrowings

> [!practice] Self-check
> Ask yourself these questions:
> 1. What does **Ь** do to the consonant before it?
> 2. When do you write an apostrophe?
> 3. What two sounds does **Щ** represent?
> 4. Can you read any Ukrainian word now?
>
> If you answered "yes" to all four — you're absolutely ready for Module 5!

**Coming next:** Module 5 — Syllables and Word Division. You'll learn how Ukrainian words break into syllables, the difference between open and closed syllables, and the rules for dividing words.

        ## File Path

        `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/completing-the-alphabet.md`

        ## Instructions

        1. Fix ONLY the violations listed above
        2. For euphony (в/у, і/й): apply Ukrainian euphony rules strictly
        3. Do NOT add or remove content — only fix the specific violations
        4. Preserve all markdown formatting, headers, and structure

        ## Output Format (MANDATORY)

        Output ONLY the fixed section(s) between delimiters:

        ```
        ===SECTION_FIX_START===
        ## {section title}
        {fixed section content}
        ===SECTION_FIX_END===
        ```

        If multiple sections need fixing, output each in its own delimiter block.
        Do NOT output anything else — no explanations, no commentary.
