        # Escalation Fix — validate

        You are an expert Ukrainian language editor. The previous agent could not fix
        these audit violations. Fix them precisely.

        ## Audit Errors

        ```
        ========================================
  📋 Loaded Plan from: plans/a1/stress-and-intonation.yaml
  📋 Loaded Metadata from YAML sidecar

📋 Auditing: A1 M06 — Stress and Intonation
   File: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/stress-and-intonation.md | Target: 1200 words
  📋 Required activity types from meta: match-up, quiz, true-false
  ⏳ Content-only audit: activities/vocab gates DEFERRED
  📋 Template: docs/l2-uk-en/templates/a1-module-template.md (pedagogy: PPP)
  ⚠️  Outline compliance: 0 errors, 2 warnings
     ⚠️ [EXTRA_SECTION_IN_MARKDOWN] Section 'Activities — Вправи' found in markdown but not in outline.
     ⚠️ [EXTRA_SECTION_IN_MARKDOWN] Section 'Словник — Vocabulary' found in markdown but not in outline.

  ⚠️ HYDRATION NOTE: Outline sums to 1300, exceeding word_target 1200
     Additional 100 words (allowed for content depth)

  📊 Section Word Analysis:
     Наголос — Stress                           433 /  350  ✅ (+83)
     Типові наголоси — Common Stress Patterns   261 /  250  ✅ (+11)
     Рухомий наголос — Mobile Stress            248 /  250  ✅ (-2)
     Інтонація — Intonation                     337 /  250  ✅ (+87)
     Практика — Practice                        141 /  100  ✅ (+41)
     Підсумок — Summary                         128 /  100  ✅ (+28)
     ─────────────────────────────────────────────────────────────────
     TOTAL                                     1548 / 1300  ✅ (+248)

--- STRICT GATES (Level A1) ---
Persona      ✅ Persona Defined
Words        ✅ 1425/1200 (raw: 1819)
Activities   ⏳ Deferred (content-only audit)
Density      ⏳ Deferred (content-only audit)
Unique_types ⏳ Deferred (content-only audit)
Priority     ⏳ Deferred (content-only audit)
Engagement   ✅ 2/2
Audio        ℹ️ No audio
Vocab        ⏳ Deferred (content-only audit)
Structure    ✅ Valid Structure
Lint         ✅ Clean Format
Pedagogy     ✅ Level-appropriate
Content_heavy ⏳ Deferred (content-only audit)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ✅ 10/10 (High)
Activity_quality ⏳ Deferred (content-only audit)
Research     ⚠️ Refresh recommended: Research has 2+ cultural hooks but content has no cultural section
Immersion    🇺🇦 6.3% (target 5-15% (M06))

Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/stress-and-intonation-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/stress-and-intonation.json

❌ AUDIT FAILED. Correct errors before proceeding.

❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/stress-and-intonation-audit.log for details)

Running RAG word verification...
Verifying: stress-and-intonation.md
  Words: 42 | VESUM: 42 (100.0%) | RAG: 0 | Not found: 0
  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/stress-and-intonation-rag-audit.md
✅ RAG verification: all words verified

VESUM: 60/60 (100%) verified
        ```

        ## Current Content of Affected Section(s)

        ## Наголос — Stress

Welcome! You have already mastered the Ukrainian alphabet and learned how to build syllables. Now, we are adding the most important element that brings these syllables to life: the **на́голос** (stress or accent). Think of stress as the heartbeat of a word. It tells you exactly which syllable to emphasize by making it sound longer, louder, and clearer than the others.

The free and mobile stress concept is crucial to understand right from the start. Unlike Polish, where stress almost always lands predictably on the penultimate (second-to-last) syllable, or French, where it usually hits the final syllable, Ukrainian has free and mobile stress. This means the stress can fall on absolutely any syllable of a content word. There is no single fixed rule you can rely on to guess where the emphasis belongs every time. Note that clitics like short prepositions and conjunctions typically lack stress entirely, but any main content word carries its own unique rhythm.

You might be wondering why this matters so much. In Ukrainian, stress changes meaning completely! Look at this famous minimal pair to see how it works:
- **за́мок** (castle) [ZA-mok] - stress on the first syllable
- **замо́к** (lock) [za-MOK] - stress on the second syllable

Both of these words share the exact same letters. But if you visit western Ukraine and ask to see a lock, people might point you to a beautiful medieval fortress! Another classic example of minimal pairs that demonstrate the functional load of stress is **му́ка** (torment) [MU-ka] and **мука́** (flour) [mu-KA]. The emphasis is literally part of the word's definition.

> [!warning] Stress Changes Meaning
> In Ukrainian, stress is not just for rhythm—it is functional! Always check the stress of a new word because a wrong emphasis can lead to a misunderstanding, like confusing a medieval **за́мок** [ZA-mok] with a door **замо́к** [za-MOK].

When you look up a new word, pay attention to how stress is marked in dictionaries and textbooks: you will see the acute accent (´) placed directly over the stressed vowel. This little mark is your best friend. For example, if you look up the word for «water», you will see it written as **вода́**, showing you that the final syllable gets the emphasis. We will practice reading dictionary entries like this throughout the course.

Your core learner strategy is simple: when encountering a new word, always check stress placement immediately. Guessing from spelling will often be wrong, and unlearning a bad habit is much harder than learning it correctly the first time. Keep your eyes open for the acute accent!

## Типові наголоси — Common Stress Patterns

Even though Ukrainian stress is beautifully free, you will start to notice certain common patterns as you learn more vocabulary. Let's explore some of the typical places the **на́голос** likes to hide, using basic words you might already recognize from your earlier lessons.

First, we frequently see first-syllable stress. Try saying these out loud, putting all your energy into the first vowel:
- **ма́ма** (mom)
- **та́то** (dad)
- **ха́та** (house)
- **ка́ва** (coffee)

This pattern is incredibly common in basic family and household words. Great job! Next, let's look at last-syllable stress. Give these words a try, holding that final vowel just a fraction of a second longer:
- **молоко́** (milk)
- **вода́** (water)

While some of these might surprise you, last-syllable stress is very common in many core words. (Note: standard dictionaries often list **Украї́на** with penultimate stress, which is the most common form).

We also see a lot of penultimate stress, where the emphasis lands firmly on the second-to-last syllable. Think of words like:
- **шко́ла** (school)
- **кни́жка** (book)
- **доро́га** (road)
- **дале́ко** (far)

This is highly frequent in two- and three-syllable words. As you can see, the melody of the language is incredibly varied!

However, remember the most important takeaway: there is no fixed rule. The exact same ending can have a completely different stress. For instance, compare **кни́жка** and **вода́**. They both have an **-а** ending, but the stress behaves differently. This proves why stress must be learned per word as you expand your vocabulary.

## Рухомий наголос — Mobile Stress

As you continue your language journey, you will discover another fascinating feature of the **на́голос**: it can move! We call this mobile stress.

Sometimes, stress shifts in declension. When a word changes its grammatical role in a sentence, the emphasis might jump to a completely different syllable. Let's look at the word for «hand» or «arm». In its basic dictionary form (nominative singular), we say **рука́**. But when we talk about two hands (nominative and accusative plural), the stress leaps backward: **ру́ки**. The stress moves when the word form changes! (As a quick note, if you need the genitive singular form, it remains **руки́** — the stress stays right where it was).

You will also see how stress shifts in number. A noun's stress can shift between singular and plural forms. Take **вода́** (water) in the singular. When we refer to plural «waters», it becomes **во́ди**. This is just a preview — we will dive into the details in later modules.

Right now, your only goal is awareness. Mobile stress will matter more when learning grammar patterns. For instance, many Ukrainian words shift their emphasis when they change their form or number. We will explore these patterns together in later modules!

A practical tip for you: listening to native speakers is the best way to internalize stress patterns. Do not stress over the stress! Just keep your ears open, enjoy the melody, and let your brain absorb the rhythms naturally as you hear more Ukrainian.

## Інтонація — Intonation

Now that we understand the heartbeat of individual words, let's look at the beautiful melody of entire sentences: **інтона́ція** (intonation). Just like the **на́голос** affects a single word, your **інтона́ція** can completely change the meaning of your **ві́дповідь** (answer) or your **пита́ння** (question).

First, we have declarative intonation. When you are making a simple statement, your pitch falls gracefully at the end of the sentence. Imagine a smooth downward contour as you speak:
> **Це кафе́.** (This is a café.)

Your voice starts steady and drops on the final word, signaling that your thought is complete.

Next, consider the interrogative with a question word. When you ask a question using specific words like «where», «who», or «what», your pitch rises on the question word itself, and then falls toward the end of the sentence. Listen to the melody:
> **Де́ кафе́?** (Where is the café?)

The word **Де** gets the highest pitch, and then your voice relaxes.

What about yes/no questions (without a question word)? This is where English and Ukrainian differ significantly. In English, your voice often just goes up at the very end of the phrase. However, in Ukrainian, your pitch rises sharply on the stressed syllable of the key word you are asking about, and then falls. It is not a simple terminal rise like English!
> **Це ма́ма?** (Is this mom?)

Your pitch rises sharply on **МА** and falls immediately on **ма**.

> [!tip] Yes/No Questions
> Unlike English, which often uses a gentle rise at the very end of a sentence, Ukrainian yes/no questions peak sharply on the stressed syllable of the focus word and then fall: **Це ма́ма?** (Rise on **ма**, fall on **ма**).

Finally, we have exclamatory intonation. When you want to express surprise, joy, or excitement, use a sharp rise with strong emphasis on the most important word:
> **Це кафе́!** (This is a café!)

To truly master this, try a contrast drill! Spend a few minutes practicing the exact same sentence with all four intonation patterns aloud.

## Практика — Practice

Let's put everything we have learned today into action with real conversations. You are doing fantastic, so take a deep breath and try these exercises out loud! Pay close attention to the **на́голос** and your **інтона́ція**.

> **(Вдома / At home)**
> — Приві́т! Це ма́ма?
> — Ні, це та́то.
> — А ма́ма тут?
> — Так, ма́ма тут.

> **(На вулиці / On the street)**
> — Це за́мок?
> — Ні. Це шко́ла.
> — А за́мок дале́ко?
> — Так, за́мок дале́ко.

> **(У кафе / In the café)**
> — Це кафе́?
> — Так, це кафе́!
> — Вода́ тут?
> — Ні, вода́ там.

> **(На кухні / In the kitchen)**
> — Молоко́ тут?
> — Так, молоко́ тут.
> — А ка́ва?
> — Ка́ва там.

These short conversations give you perfect practice for yes/no question intonation and recognizing stress in everyday situations. Keep practicing these melodies, and your Ukrainian will sound incredibly natural.

## Activities — Вправи

Now it is time to put your new knowledge of stress and intonation into practice! In the activities below, you will practice identifying the stressed syllable in everyday words, distinguishing between different stress minimal pairs, and recognizing the sharp rise and fall of yes/no question intonation. Remember, there is no single fixed rule for Ukrainian stress, so building your awareness through active practice is essential. Take your time, say the words out loud, and focus on the natural rhythm and beautiful melody of the Ukrainian language.

Try to answer these questions based on the vocabulary we learned:
- **Хто** це? (Who is this?) — Це ма́ма.
- **Що** це? (What is this?) — Це **кни́жка**.
- Це **замо́к**? (Is this a lock?) — Ні, це **за́мок**!
- Це **мука́**? (Is this flour?) — Так, це **мука́**.

You can also practice the melody of the language by reading these short sentences:
1. Де **кни́жка**? — **Кни́жка** тут.
2. **Хто** там? — Та́то там.
3. **Що** там? — **Ка́ва** там.

Focus on how your voice moves. Is it a statement with a falling pitch, or a question with a sharp rise on the focus word? Constant practice is the key to mastering the heartbeat and melody of Ukrainian!

## Словник — Vocabulary

All new words from this module are listed in the vocabulary section. Practice their stress and meaning to build a solid foundation.

## Підсумок — Summary

Let's do a quick recap of what we covered today. You learned that Ukrainian stress is free and mobile, meaning it can land on any syllable and shift when words change form. We saw how vowel purity is strictly maintained under stress. You also learned to use a rising intonation for questions, which differs from English, and you explored how stress minimal pairs can change a word's meaning entirely!

Time for a quick self-check before we finish:
1. Where is the stress in **вода́**?
2. What happens to vowel quality when unstressed? (It stays pure!)
3. How does question intonation differ from a basic statement?

If you feel confident with these answers, you are perfectly ready for the next step. Next: M7 — greetings and basic phrases. Excellent work!

        ## File Path

        `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/stress-and-intonation.md`

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
