        # Escalation Fix — validate

        You are an expert Ukrainian language editor. The previous agent could not fix
        these audit violations. Fix them precisely.

        ## Audit Errors

        ```
        📋 Auditing: A1 M04 — Completing the Alphabet
   File: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/completing-the-alphabet.md | Target: 1200 words
  📋 Required activity types from meta: classify, fill-in, image-to-letter, match-up, quiz, watch-and-repeat
  ⏳ Content-only audit: activities/vocab gates DEFERRED
  📋 Template: docs/l2-uk-en/templates/a1-module-template.md (pedagogy: PPP)
  ⚠️  Outline compliance: 0 errors, 1 warnings
     ⚠️ [EXTRA_SECTION_IN_MARKDOWN] Section 'Підсумок — Summary' found in markdown but not in outline.

  📊 Section Word Analysis:
     Вступ — Introduction                         122 /  100  ✅ (+22)
     М'який знак — The Soft Sign                  235 /  250  ✅ (-15)
     Апостроф — The Apostrophe                    210 /  250  ⚠️ (-40)
     Африкати та Ф — Affricates and Ф             327 /  300  ✅ (+27)
     Диграфи ДЖ, ДЗ — Digraphs                    167 /  150  ✅ (+17)
     Весь алфавіт! — The Full Alphabet Mastered   241 /  150  ✅ (+91)
     ───────────────────────────────────────────────────────────────────
     TOTAL                                       1302 / 1200  ✅ (+102)

--- STRICT GATES (Level A1) ---
Persona      ✅ Persona Defined
Words        ✅ 1517/1200 (raw: 1599)
Activities   ⏳ Deferred (content-only audit)
Density      ⏳ Deferred (content-only audit)
Unique_types ⏳ Deferred (content-only audit)
Priority     ⏳ Deferred (content-only audit)
Engagement   ✅ 5/3
Audio        ℹ️ No audio
Vocab        ⏳ Deferred (content-only audit)
Structure    ✅ Valid Structure
Lint         ✅ Clean Format
Pedagogy     ✅ Level-appropriate
Content_heavy ⏳ Deferred (content-only audit)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ⏳ Deferred (content-only audit)
Research     ✅ Content aligned with research
Immersion    🇺🇦 9.5% (target 5-15% (M04))

Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/completing-the-alphabet-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/completing-the-alphabet.json

✅ AUDIT PASSED.

✅ AUDIT PASSED

Running RAG word verification...
Verifying: completing-the-alphabet.md
  VESUM misses: 7 — querying RAG...
[embed] Loading BGE-M3 from BAAI/bge-m3...

Fetching 30 files:   0%|          | 0/30 [00:00<?, ?it/s]
Fetching 30 files: 100%|██████████| 30/30 [00:00<00:00, 79588.31it/s]
[embed] BGE-M3 loaded.
You're using a XLMRobertaTokenizerFast tokenizer. Please note that with a fast tokenizer, using the `__call__` method is faster than using a method to encode the text followed by a call to the `pad` method to get a padded encoding.
  Words: 62 | VESUM: 55 (88.7%) | RAG: 4 | Not found: 3
  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/completing-the-alphabet-rag-audit.md
⚠️  RAG verification found unverified words (see audit report)

VESUM: 55/62 (89%) verified
⚠️ VESUM not found (6): ДЖ, ДЗ, ець, иця, М'Я, шо
        ```

        ## Current Content of Affected Section(s)

        The letter **Ь** is unique in the Ukrainian alphabet — it has no sound of its own. Instead, it softens the consonant that comes before it. When you see **Ь** after a consonant, place your tongue a little closer to the roof of your mouth as you say that consonant. The result is a palatalized sound — lighter and gentler than the hard version.

### Літера Ь

<YouTube url="https://www.youtube.com/watch?v=cJlal8XKBxo" title="Anna Ohoiko — Ukrainian Lessons — Ь" />

Here are everyday words with **Ь**:

- **сіль** (salt) — the **Л** before **Ь** is soft
- **день** (day) — the **Н** before **Ь** is soft
- **Льві́в** (Lviv) — **Ь** appears before another consonant
- **мідь** (copper) — the **Д** before **Ь** is soft
- **о́сінь** (autumn) — the **Н** before **Ь** is soft
- **кінь** (horse) — the **Н** before **Ь** is soft

> [!tip] **Pattern**
> **Ь** appears after consonants at the end of a word (**сіль**, **день**) or before another consonant (**Льві́в**). It never appears at the start of a word, and never after a vowel.

Notice how **Ь** changes meaning. Compare these two words:

- **кінь** — horse
- **кін** — a stake in a game

The same letters, but **Ь** softens the final **Н**, creating an entirely different word. Your ears will learn to hear this difference with practice — don't worry if it takes time.

Here's a short exchange using your new words:

> — Добрий **день**!
> — Добрий **день**!
> — **Сіль** тут?
> — Так, **сіль** тут.

<!-- adapted from: Bolshakova, Grade 2 -->

## Апостроф — The Apostrophe

Remember from Module 2 that the iotated vowels **Я**, **Ю**, **Є**, **Ї** can represent two sounds — a **Й**-glide plus a vowel. The apostrophe (**'**) is a small but powerful mark that keeps this **Й**-sound alive.

When a consonant is followed directly by an iotated vowel, Ukrainian normally softens that consonant and absorbs the **Й**-glide. The apostrophe prevents this. It tells you: «Keep the consonant hard. Let the iotated vowel keep its full two-sound value.»

Here are key words with the apostrophe:

- **м'я́со** (meat) — hard **М** + **Й** + **А**
- **п'ять** (five) — hard **П** + **Й** + **А**
- **сім'я́** (family) — hard **М** + **Й** + **А**
- **м'яч** (ball) — hard **М** + **Й** + **А**
- **об'є́кт** (object) — hard **Б** + **Й** + **Е**

> [!warning] **The Apostrophe Rule**
> The apostrophe appears after **Б**, **П**, **В**, **М**, **Ф**, **Р** before **Я**, **Ю**, **Є**, **Ї**. It is never optional — without it, the word is spelled incorrectly and sounds different.

Think of it this way: without the apostrophe, **М** + **Я** would mean «soft М + А». With the apostrophe, **М'Я** means «hard М + Й + А». The apostrophe preserves the **Й**-sound you learned in Module 2.

Practice reading with your new words:

> — Це **м'я́со**?
> — Так, це **м'я́со**.
> — А це **сіль**?
> — Ні, це **цу́кор**.

<!-- adapted from: Bolshakova, Grade 2 -->

## Африкати, Щ та Ф — Affricates, Щ, and Ф

Now for some sounds that might be more familiar than you expect.

### Літера Ц

<YouTube url="https://www.youtube.com/watch?v=u44eCjR2Oz8" title="Anna Ohoiko — Ukrainian Lessons — Ц" />

**Ц** is a true affricate — the sounds **Т** and **С** fused into one. You already make this sound in English: think of the «ts» at the end of «cats» or «bits». In Ukrainian, this sound can appear anywhere in a word, including the very beginning.

- **цу́кор** (sugar) — an everyday kitchen word
- **цибу́ля** (onion) — another kitchen staple

You'll also find **Ц** in common word endings like **-ець** and **-иця**.

### Літера Ч

<YouTube url="https://www.youtube.com/watch?v=UsJkbdsY2RA" title="Anna Ohoiko — Ukrainian Lessons — Ч" />

**Ч** is another affricate, like the «ch» in English «church». It's one of the most frequent consonants in Ukrainian.

- **час** (time, hour) — a top-100 Ukrainian word
- **черепа́ха** (turtle) — a favourite in children's stories
- **чай** (tea) — you'll hear this one every day

Try this quick exchange:

> — **Що** це?
> — Це **чай**.
> — А це?
> — Це **цу́кор**.

### Літера Щ

<YouTube url="https://www.youtube.com/watch?v=QmBLieIuf6Q" title="Anna Ohoiko — Ukrainian Lessons — Щ" />

**Щ** looks like it should be a single sound, but it's actually a consonant cluster — two sounds, **Ш** + **Ч**, written as one letter. Say «fresh cheese» quickly — that «sh-ch» at the boundary is close to Ukrainian **Щ**.

- **що** (what) — one of the top 10 most common Ukrainian words
- **ще** (still, more)
- **ща́стя** (happiness)

> [!note] **Common Learner Mistake**
> Many learners pronounce **що** as «шо», dropping the **Ч** part. Remember: **Щ** = **Ш** + **Ч**, not just **Ш**. Keep both sounds!

### Літера Ф

<YouTube url="https://www.youtube.com/watch?v=haHRsFFZRQI" title="Anna Ohoiko — Ukrainian Lessons — Ф" />

**Ф** sounds just like English «f». It's rare in native Ukrainian words — you'll mostly find it in borrowings from other languages.

- **факт** (fact) — a familiar internationalism
- **фо́то** (photo)

**Ф** is the voiceless partner of **В**, just as **П** is the voiceless partner of **Б**.

## Диграфи ДЖ, ДЗ — Digraphs

Ukrainian has two digraphs — combinations where two letters on the page represent a single sound.

**ДЖ** sounds like the English «j» in «jungle» or «g» in «gem». It's the voiced partner of **Ч**.

- **джерело́** (spring, source) — a beautiful word for a natural spring
- **бджола́** (bee) — notice the **ДЖ** hiding inside the word

**ДЗ** has no English equivalent. It's the voiced partner of **Ц** — imagine adding voice to that «ts» sound you just learned.

- **дзвін** (bell) — Ukrainian church bells have a distinctive ring; this word is the root of **дзвіно́к** (a bell, a ring)
- **дзе́ркало** (mirror)

> [!culture] **A Uniquely Ukrainian Sound**
> The digraph **ДЗ** is a marker of authentic Ukrainian phonology. When you say **дзвін** or **дзе́ркало**, you're producing a sound that belongs to this language alone.

> [!warning] **Don't Split the Digraph**
> When you see **ДЖ** or **ДЗ**, read them as one sound. Don't read **дзвін** as «Д + З + він» — it's one smooth sound at the start.

A quick practice:

> — **Що** це?
> — Це **дзе́ркало**.
> — А це?
> — Це **м'яч**.

## Весь алфавіт! — The Full Alphabet Mastered

You did it! Here is the complete 33-letter Ukrainian alphabet:

**А Б В Г Ґ Д Е Є Ж З И І Ї Й К Л М Н О П Р С Т У Ф Х Ц Ч Ш Щ Ь Ю Я**

Plus the two digraphs **ДЖ** and **ДЗ**, and the apostrophe **'**. That's your complete toolkit for reading Ukrainian.

### Літера Ґ

<YouTube url="https://www.youtube.com/watch?v=gNjHqjTW9WQ" title="Anna Ohoiko — Ukrainian Lessons — Ґ" />

Recall the plosive «g» sound of **Ґ** from Module 3 — as in **ґа́нок** (porch). It's the rarest letter in the alphabet, but uniquely Ukrainian.

### Reading Challenge

Try reading these sentences aloud. They use vowels, consonants, the soft sign, an apostrophe, affricates, and digraphs:

- **Моя́ сім'я́ тут.** (My family is here.)
- **Ма́ма, та́то і кіт.** (Mom, dad, and the cat.)
- **Сіль, цу́кор, чай.** (Salt, sugar, tea.)
- **Бджола́ тут!** (A bee is here!)
- **Що це? Це дзе́ркало.** (What is this? This is a mirror.)

### Survival Phrases

These phrases use your full alphabet. Read them aloud — you have all the tools you need:

- **До́брий день!** — Good day!
- **Як спра́ви?** — How are you?
- **Спаси́бі!** — Thanks!
- **Будь ла́ска!** — **Please / You're welcome!** (Note that this is a fixed phrase.)
- **До поба́чення!** — Goodbye!

You can now decode any Ukrainian word you encounter. The reading skills from Modules 1 through 4 are the foundation for everything that follows. Be proud of how far you've come!

## Підсумок — Summary

Congratulations — you've completed the alphabet! Here's what you learned:

- **Ь** (soft sign) softens the consonant before it, with no sound of its own
- The **apostrophe** preserves the **Й**-sound before iotated vowels (**Я**, **Ю**, **Є**, **Ї**)
- **Ц** and **Ч** are affricates — fused sounds
- **Щ** is a consonant cluster: **Ш** + **Ч**
- **ДЖ** and **ДЗ** are digraphs — two letters, one sound each
- **Ф** is rare in native words, common in borrowings

**Self-check — ask yourself:**

1. What does **Ь** do to the consonant before it?
2. When do you write an apostrophe?
3. What two sounds does **Щ** represent?
4. Can you read any Ukrainian word now?

If you answered yes to question 4, you're ready for the next step. Our next session, Module 5, will explore syllables and word division — how Ukrainian words break into pieces for reading and writing.

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
