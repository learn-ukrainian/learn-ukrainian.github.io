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



**NOTE: 8 inline fix(es) from the review have ALREADY been applied to the files. Do NOT re-apply those fixes. Read the CURRENT file contents carefully — they reflect the post-fix state. Only fix issues that are still present in the current files.**

## Plan Adherence Issues (Deterministic — MUST FIX)

- **[HIGH] VOCAB_NOT_IN_CONTENT** in `vocabulary`
  - Expected: Required word 'писати' must appear in content
  - Actual: Word not found (after stress-mark normalization)
  - Fix: Add 'писати' to an appropriate section in the content


---

## Review Findings (targeted fix required)

**CONSTRAINTS:**
- Fix ONLY the issues listed below
- Do NOT rewrite surrounding text
- Preserve word count and structure
- Only modify these sections: Entire module / Plan vocabulary_hints.required, Line 134 / Section "Практика — Practice", Line 140 / Section "Підсумок — Summary", Line 18 / Section "Наголос — Stress", Line 61 / Section "Рухомий наголос — Mobile Stress", Lines 134, 136 / Sections "Практика — Practice" and "Підсумок — Summary"

### Finding 1: Russicism "дом" (CRITICAL)
**Location**: Line 134 / Section "Практика — Practice"
**Problem**: "дом" is Russian. VESUM confirms: NOT FOUND. Ukrainian is "дім" (VESUM: noun:inanim:m:v_naz). This is a textbook Russicism.
**Required Fix**: Replace with "Наш дім — це ха́та." (Note: "дім" has stress on its only syllable so no stress mark needed, OR write "наш дім" without acute accent since it's monosyllabic.)
**Severity**: HIGH

### Finding 2: Verb Scope Violation — Reading Passage (CRITICAL)
**Location**: Line 134 / Section "Практика — Practice"
**Problem**: M6 is a pre-verb module. Verbs are forbidden before M15. This passage uses 8 distinct conjugated verbs: звуть, живу́, пра́цює, лю́бить, чита́є, п'є́мо, їмо́, лю́блю. A learner at this stage has NEVER seen verb conjugation.
**Required Fix**: Rewrite the entire reading passage using only Це + noun, location phrases, and noun phrases that learners have actually encountered. Example: "Приві́т! Це Оле́на. Оле́на — в Украї́ні. Тут ма́ма, та́то і сестра́. Ма́ма — в шко́лі. Та́то і ка́ва — тут. Сестра́ і кни́жка — там. Наш дім — це ха́та. Ха́та дале́ко від шко́ли. Молоко́ і хліб — тут. Вода́ тут, а ка́ва там."
**Severity**: HIGH

### Finding 3: Verb on Line 18 (HIGH)
**Location**: Line 18 / Section "Наголос — Stress"
**Problem**: пра́цює is a conjugated verb in a pre-verb module. Additionally, the stress is WRONG: should be працю́є (stress on -ю́-), not пра́цює.
**Required Fix**: Replace with a noun example: "**хліб** (bread), **мі́сто** (city), or **доро́га** (road)"
**Severity**: HIGH

### Finding 4: Wrong Stress — Олена́ (HIGH)
**Location**: Lines 134, 136 / Sections "Практика — Practice" and "Підсумок — Summary"
**Problem**: The standard stress for the name Олена is Оле́на (second syllable), not Олена́ (last syllable). Line 136 even explicitly teaches this wrong stress as a pedagogical example.
**Required Fix**: Replace all instances of Олена́ with Оле́на. Fix line 136 to say "**Оле́на** has penultimate stress."
**Severity**: HIGH

### Finding 5: Wrong Stress — п'є́мо and лю́блю (HIGH)
**Location**: Line 134 / Section "Практика — Practice"
**Problem**: Correct stress is п'ємо́ (last syllable) and люблю́ (last syllable). These verbs also shouldn't be here at all (Issue 2), but the stress is independently wrong.
**Required Fix**: If verbs remain (they shouldn't), correct to п'ємо́ and люблю́.
**Severity**: HIGH

### Finding 6: Phantom Summary Claim — Vowel Purity (MEDIUM)
**Location**: Line 140 / Section "Підсумок — Summary"
**Problem**: Vowel purity/quality was never discussed in ANY section of this module. The summary fabricates a teaching point. Self-check question 2 (line 144) also asks about vowel quality.
**Required Fix**: Remove the vowel purity claim. Replace with something actually taught, e.g., "We saw how the same word can have different stress patterns depending on its form — like рука́ becoming ру́ки." Replace self-check question 2 with "Can stress move when a word changes form? Give an example."
**Severity**: HIGH

### Finding 7: Missing Required Vocabulary — писати and добрий (MEDIUM)
**Location**: Entire module / Plan vocabulary_hints.required
**Problem**: Plan requires писати (to write, mobile stress писа́ти → пишу́ → пи́шеш) and добрий (good, first-syllable stress, collocation: добрий день). Neither appears in the prose. до́бре (line 30) is the adverb form, not the adjective. Note: писати is a verb and thus cannot appear in pre-verb M6 — this is a plan conflict.
**Required Fix**: For добрий: Add "**до́брий** (good) — as in **до́брий день** (good day)" to the first-syllable stress examples in section "Типові наголоси — Common Stress Patterns". For писати: This is a plan defect — a verb cannot appear in pre-verb M6. Flag for plan version bump: remove писати from required vocab or move to recommended.
**Severity**: HIGH

### Finding 8: се́стри Stress — Pre-Screen Dismissal (INFO)
**Location**: Line 61 / Section "Рухомий наголос — Mobile Stress"
**Problem**: Pre-screen D.0 #12 flags се́стри as wrong, suggesting сестри́. However, VESUM confirms сестри is nominative plural of сестра (noun:anim:p:v_naz). The nominative plural stress IS се́стри. The genitive singular is сестри́. In context, "sisters" = nom.pl. = се́стри. **Pre-screen is WRONG. Dismiss.**
**Required Fix**: None needed.
**Severity**: HIGH

---

## Critical Issues Found

### Issue 1: Russicism "дом" (CRITICAL)
- **Location**: Line 134 / Section "Практика — Practice"
- **Original**: 「Наш до́м — це ха́та.」
- **Problem**: "дом" is Russian. VESUM confirms: NOT FOUND. Ukrainian is "дім" (VESUM: noun:inanim:m:v_naz). This is a textbook Russicism.
- **Fix**: Replace with "Наш дім — це ха́та." (Note: "дім" has stress on its only syllable so no stress mark needed, OR write "наш дім" without acute accent since it's monosyllabic.)

### Issue 2: Verb Scope Violation — Reading Passage (CRITICAL)
- **Location**: Line 134 / Section "Практика — Practice"
- **Original**: 「Мене́ звуть Олена́. Я живу́ в Украї́ні...Ма́ма пра́цює в шко́лі. Та́то лю́бить ка́ву. Сестра́ чита́є кни́жку...Ми п'є́мо молоко́ і їмо́ хліб...Я лю́блю свою́ роди́ну!」
- **Problem**: M6 is a pre-verb module. Verbs are forbidden before M15. This passage uses 8 distinct conjugated verbs: звуть, живу́, пра́цює, лю́бить, чита́є, п'є́мо, їмо́, лю́блю. A learner at this stage has NEVER seen verb conjugation.
- **Fix**: Rewrite the entire reading passage using only Це + noun, location phrases, and noun phrases that learners have actually encountered. Example: "Приві́т! Це Оле́на. Оле́на — в Украї́ні. Тут ма́ма, та́то і сестра́. Ма́ма — в шко́лі. Та́то і ка́ва — тут. Сестра́ і кни́жка — там. Наш дім — це ха́та. Ха́та дале́ко від шко́ли. Молоко́ і хліб — тут. Вода́ тут, а ка́ва там."

### Issue 3: Verb on Line 18 (HIGH)
- **Location**: Line 18 / Section "Наголос — Stress"
- **Original**: 「whether it is **хліб** (bread), **місто** (city), or **пра́цює** (works)」
- **Problem**: пра́цює is a conjugated verb in a pre-verb module. Additionally, the stress is WRONG: should be працю́є (stress on -ю́-), not пра́цює.
- **Fix**: Replace with a noun example: "**хліб** (bread), **мі́сто** (city), or **доро́га** (road)"

### Issue 4: Wrong Stress — Олена́ (HIGH)
- **Location**: Lines 134, 136 / Sections "Практика — Practice" and "Підсумок — Summary"
- **Original**: 「Олена́」 and 「**Олена́** has last-syllable stress」
- **Problem**: The standard stress for the name Олена is Оле́на (second syllable), not Олена́ (last syllable). Line 136 even explicitly teaches this wrong stress as a pedagogical example.
- **Fix**: Replace all instances of Олена́ with Оле́на. Fix line 136 to say "**Оле́на** has penultimate stress."

### Issue 5: Wrong Stress — п'є́мо and лю́блю (HIGH)
- **Location**: Line 134 / Section "Практика — Practice"
- **Original**: 「п'є́мо」 and 「лю́блю」
- **Problem**: Correct stress is п'ємо́ (last syllable) and люблю́ (last syllable). These verbs also shouldn't be here at all (Issue 2), but the stress is independently wrong.
- **Fix**: If verbs remain (they shouldn't), correct to п'ємо́ and люблю́.

### Issue 6: Phantom Summary Claim — Vowel Purity (MEDIUM)
- **Location**: Line 140 / Section "Підсумок — Summary"
- **Original**: 「We saw how vowel purity is strictly maintained under stress.」
- **Problem**: Vowel purity/quality was never discussed in ANY section of this module. The summary fabricates a teaching point. Self-check question 2 (line 144) also asks about vowel quality.
- **Fix**: Remove the vowel purity claim. Replace with something actually taught, e.g., "We saw how the same word can have different stress patterns depending on its form — like рука́ becoming ру́ки." Replace self-check question 2 with "Can stress move when a word changes form? Give an example."

### Issue 7: Missing Required Vocabulary — писати and добрий (MEDIUM)
- **Location**: Entire module / Plan vocabulary_hints.required
- **Problem**: Plan requires писати (to write, mobile stress писа́ти → пишу́ → пи́шеш) and добрий (good, first-syllable stress, collocation: добрий день). Neither appears in the prose. до́бре (line 30) is the adverb form, not the adjective. Note: писати is a verb and thus cannot appear in pre-verb M6 — this is a plan conflict.
- **Fix**: For добрий: Add "**до́брий** (good) — as in **до́брий день** (good day)" to the first-syllable stress examples in section "Типові наголоси — Common Stress Patterns". For писати: This is a plan defect — a verb cannot appear in pre-verb M6. Flag for plan version bump: remove писати from required vocab or move to recommended.

### Issue 8: се́стри Stress — Pre-Screen Dismissal (INFO)
- **Location**: Line 61 / Section "Рухомий наголос — Mobile Stress"
- **Original**: 「**сестра́** (sister) → **се́стри** (sisters)」
- **Problem**: Pre-screen D.0 #12 flags се́стри as wrong, suggesting сестри́. However, VESUM confirms сестри is nominative plural of сестра (noun:anim:p:v_naz). The nominative plural stress IS се́стри. The genitive singular is сестри́. In context, "sisters" = nom.pl. = се́стри. **Pre-screen is WRONG. Dismiss.**
- **Fix**: None needed.

---

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 134 | 「до́м」 | дім | Russicism |
| 18 | 「пра́цює」 | працю́є (but remove — verb scope) | Stress + Scope |
| 134 | 「пра́цює」 | працю́є (but remove — verb scope) | Stress + Scope |
| 134 | 「Олена́」 | Оле́на | Stress |
| 134 | 「п'є́мо」 | п'ємо́ (but remove — verb scope) | Stress + Scope |
| 134 | 「лю́блю」 | люблю́ (but remove — verb scope) | Stress + Scope |
| 134 | 「звуть」 | remove — verb scope | Scope |
| 134 | 「живу́」 | remove — verb scope | Scope |
| 134 | 「лю́бить」 | remove — verb scope | Scope |
| 134 | 「чита́є」 | remove — verb scope | Scope |
| 134 | 「їмо́」 | remove — verb scope | Scope |

---

## Fix Plan to Reach 9/10 (REQUIRED — score is 6.1)

### Linguistic Accuracy: 4/10 → 9/10
**What to fix:**
1. Line 134: Replace entire reading passage with verb-free version (removes 8 verb violations, Russicism дом, 4 stress errors in one fix)
2. Line 18: Replace 「пра́цює」 with a noun example like доро́га
3. Line 136: Fix 「Олена́」 to Оле́на and correct the pedagogical claim
4. Line 140: Remove phantom vowel purity claim
5. Lines 143-144: Fix self-check question 2 about vowel quality

**Expected score after fix:** 9/10

### Language: 5/10 → 9/10
**What to fix:**
1. All fixes from Linguistic Accuracy above eliminate the Russicism and stress errors
2. Replace "incredibly" (lines 30, 44, 130) with varied vocabulary
3. Add до́брий to section "Типові наголоси — Common Stress Patterns" (missing required vocab)

**Expected score after fix:** 9/10

### Beginner Safety: 5/10 → 9/10
**What to fix:**
1. Rewrite line 134 reading passage to use only Це + noun, location adverbs, and noun phrases — structures the learner has already seen
2. All verb scope violations resolved by this rewrite

**Expected score after fix:** 9/10

### LLM Fingerprint: 7/10 → 8/10
**What to fix:**
1. Line 50: Rewrite 「As you continue your language journey」 — flagged LLM filler
2. Vary "incredibly" (3 uses) and "beautiful/beautifully" (3 uses)

**Expected score after fix:** 8/10

### Projected Overall After Fixes
```
Experience: 8×1.5 + Language: 9×1.1 + Pedagogy: 9×1.2 + Activities: 8×1.3 +
Beginner Safety: 9×1.3 + LLM: 8×1.0 + Linguistic Accuracy: 9×1.5
= 12.0 + 9.9 + 10.8 + 10.4 + 11.7 + 8.0 + 13.5 = 76.3 / 8.9 = 8.6/10
```

---

## Audit Failures (from automated re-audit)

```
⚠️ HYDRATION NOTE: Outline sums to 1300, exceeding word_target 1200
--- STRICT GATES (Level A1) ---
Pedagogy     ❌ 1 violations
📚 PEDAGOGICAL VIOLATIONS FOUND:
📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
→ 1 violations (minor)
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/stress-and-intonation-audit.log for details)
⚠️  RAG verification found unverified words (see audit report)
--- VESUM WORD VERIFICATION FAILURES ---
These words were NOT found in the VESUM morphological dictionary.
Check if they are valid Ukrainian forms. Fix misspellings or Russianisms.
  ❌ `дом` (source: prose)
```

---

## File Contents (for reference)

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/stress-and-intonation.md`

```markdown
## Наголос — Stress

Welcome! You have already mastered the Ukrainian alphabet and learned how to build syllables. Now, we are adding the most important element that brings these syllables to life: the **на́голос** (stress or accent). Think of stress as the heartbeat of a word. It tells you exactly which syllable to emphasize by making it sound longer, louder, and clearer than the others.

The free and mobile stress concept is crucial to understand right from the start. Unlike Polish, where stress almost always lands predictably on the penultimate (second-to-last) syllable, or French, where it usually hits the final syllable, Ukrainian has free and mobile stress. This means the stress can fall on absolutely any syllable of a content word. There is no single fixed rule you can rely on to guess where the emphasis belongs every time. Note that clitics like short prepositions and conjunctions typically lack stress entirely, but any main content word carries its own unique rhythm.

You might be wondering why this matters so much. In Ukrainian, stress changes meaning completely! Look at this famous minimal pair to see how it works:
- **за́мок** (castle) [ZA-mok] - stress on the first syllable
- **замо́к** (lock) [za-MOK] - stress on the second syllable

Both of these words share the exact same letters. But if you visit western Ukraine and ask to see a lock, people might point you to a medieval fortress! Another classic example of minimal pairs that demonstrate the functional load of stress is **му́ка** (torment) [MU-ka] and **мука́** (flour) [mu-KA]. The emphasis is literally part of the word's definition.

> [!warning] Stress Changes Meaning
> In Ukrainian, stress is not just for rhythm—it is functional! Always check the stress of a new word because a wrong emphasis can lead to a misunderstanding, like confusing a medieval **за́мок** [ZA-mok] with a door **замо́к** [za-MOK].

When you look up a new word, pay attention to how stress is marked in dictionaries and textbooks: you will see the acute accent (´) placed directly over the stressed vowel. This little mark is your best friend. For example, if you look up the word for «water», you will see it written as **вода́**, showing you that the final syllable gets the emphasis. We will practice reading dictionary entries like this throughout the course.

Your core learner strategy is simple: when encountering a new word — whether it is **хліб** (bread), **мі́сто** (city), or **доро́га** (road) — always check stress placement immediately. Guessing from spelling will often be wrong, and unlearning a bad habit is much harder than learning it correctly the first time. Keep your eyes open for the acute accent!

## Типові наголоси — Common Stress Patterns

Even though Ukrainian stress is wonderfully free, you will start to notice certain common patterns as you learn more vocabulary. Let's explore some of the typical places the **на́голос** likes to hide, using basic words you might already recognize from your earlier lessons.

First, we frequently see first-syllable stress. Try saying these out loud, putting all your energy into the first vowel:
- **ма́ма** (mom)
- **та́то** (dad)
- **ха́та** (house)
- **ка́ва** (coffee)

This pattern is very common in basic family and household words. You will also find it in **ді́ти** (children), **бра́те** (brother, vocative), **до́бре** (well/good), and **до́брий** (good) — as in the greeting **до́брий день** (good day). Great job! Next, let's look at last-syllable stress. Give these words a try, holding that final vowel just a fraction of a second longer:
- **молоко́** (milk)
- **вода́** (water)

While some of these might surprise you, last-syllable stress is very common in many core words. You will also hear it in words like **сестра́** (sister), **нога́** (leg), and **голова́** (head). (Note: standard dictionaries often list **Украї́на** with penultimate stress, which is the most common form).

We also see a lot of penultimate stress, where the emphasis lands firmly on the second-to-last syllable. Think of words like:
- **шко́ла** (school)
- **кни́жка** (book)
- **доро́га** (road)
- **дале́ко** (far)
- **пита́ння** (question)
- **ві́дповідь** (answer)

This is highly frequent in two- and three-syllable words. As you can see, the melody of the language is wonderfully varied!

However, remember the most important takeaway: there is no fixed rule. The exact same ending can have a completely different stress. For instance, compare **кни́жка** and **вода́**. They both have an **-а** ending, but the stress behaves differently. This proves why stress must be learned per word as you expand your vocabulary.

## Рухомий наголос — Mobile Stress

Here is another key feature of the **на́голос**: it can move! We call this mobile stress.

Sometimes, stress shifts in declension. When a word changes its grammatical role in a sentence, the emphasis might jump to a completely different syllable. Let's look at the word for «hand» or «arm». In its basic dictionary form (nominative singular), we say **рука́**. But when we talk about two hands (nominative and accusative plural), the stress leaps backward: **ру́ки**. The stress moves when the word form changes! (As a quick note, if you need the genitive singular form, it remains **руки́** — the stress stays right where it was).

You will also see how stress shifts in number. A noun's stress can shift between singular and plural forms. Take **вода́** (water) in the singular. When we refer to plural «waters», it becomes **во́ди**. This is just a preview — we will dive into the details in later modules.

Right now, your only goal is awareness. Mobile stress will matter more when learning grammar patterns. For instance, many Ukrainian words shift their emphasis when they change their form or number. We will explore these patterns together in later modules!

Here are a few more examples of mobile stress to listen for:
- **нога́** (leg) → **но́ги** (legs)
- **голова́** (head) → **го́лови** (heads)
- **сестра́** (sister) → **се́стри** (sisters)
- **писа́ти** (to write) — even verbs have mobile stress: the emphasis shifts across different forms of this word, which we will explore when we learn verbs later

A practical tip for you: listening to native speakers is the best way to internalize stress patterns. Do not stress over the stress! Just keep your ears open, enjoy the rhythm, and let your brain absorb the patterns naturally as you hear more Ukrainian.

## Інтонація — Intonation

Now that we understand the heartbeat of individual words, let's look at the melody of entire sentences: **інтона́ція** (intonation). Just like the **на́голос** affects a single word, your **інтона́ція** can completely change the meaning of your **ві́дповідь** (answer) or your **пита́ння** (question).

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

To truly master this, try a contrast drill! Spend a few minutes practicing the exact same sentence with all four intonation patterns aloud:

> **Це кафе́.** — statement (pitch falls)
> **Де кафе́?** — question with question word (rise on **Де**, then fall)
> **Це кафе́?** — yes/no question (sharp rise on **фе**, then fall)
> **Це кафе́!** — exclamation (sharp rise with emphasis)

Here are more sentences to practice your intonation with:
> **Та́то тут.** / **Та́то тут?** / **Та́то тут!**
> **Ма́ма вдо́ма.** / **Ма́ма вдо́ма?** / **Ма́ма вдо́ма!**
> **Кни́жка там.** / **Кни́жка там?** / **Кни́жка там!**

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

These short conversations give you perfect practice for yes/no question intonation and recognizing stress in everyday situations. Keep practicing these melodies, and your Ukrainian will sound natural and confident.

Now try reading this short passage aloud. Focus on the stress marks and intonation:

> Приві́т! Це Оле́на. Оле́на — в Украї́ні. Тут ма́ма, та́то і сестра́. Ма́ма — в шко́лі. Та́то і ка́ва — тут. Сестра́ і кни́жка — там. Наш дім — це ха́та. Ха́та дале́ко від шко́ли. Молоко́ і хліб — тут. Вода́ тут, а ка́ва там. Це роди́на!

Pay attention to how the stress jumps around — **Оле́на** has penultimate stress, **ма́ма** has first-syllable stress, and **роди́на** has penultimate stress. This is the natural rhythm of Ukrainian!

## Підсумок — Summary

Let's do a quick recap of what we covered today. You learned that Ukrainian stress is free and mobile, meaning it can land on any syllable and shift when words change form. You also learned to use a rising intonation for questions, which differs from English, and you explored how stress minimal pairs can change a word's meaning entirely!

Time for a quick self-check before we finish:
1. Where is the stress in **вода́**?
2. Can stress move when a word changes form? Give an example!
3. How does question intonation differ from a basic statement?

If you feel confident with these answers, you are perfectly ready for the next step. Next: M7 — greetings and basic phrases. Excellent work!
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/stress-and-intonation.yaml`

```yaml
- type: quiz
  title: "Stress Placement"
  instruction: "Identify which syllable carries the stress in each Ukrainian word."
  items:
    - question: "Which syllable is stressed in the word вода́ (water)?"
      options:
        - text: "First syllable (во-)"
          correct: false
        - text: "Second syllable (-да)"
          correct: true
        - text: "Both syllables equally"
          correct: false
        - text: "Neither — it has no stress"
          correct: false
      explanation: "Вода́ has last-syllable stress — the emphasis falls on -да."
    - question: "Which syllable is stressed in the word ма́ма (mom)?"
      options:
        - text: "First syllable (ма-)"
          correct: true
        - text: "Second syllable (-ма)"
          correct: false
        - text: "Both syllables equally"
          correct: false
        - text: "It depends on the sentence"
          correct: false
      explanation: "Ма́ма has first-syllable stress — the emphasis falls on the first ма-."
    - question: "Which syllable is stressed in the word молоко́ (milk)?"
      options:
        - text: "First syllable (мо-)"
          correct: false
        - text: "Second syllable (-ло-)"
          correct: false
        - text: "Third syllable (-ко)"
          correct: true
        - text: "All syllables equally"
          correct: false
      explanation: "Молоко́ has last-syllable stress — the emphasis falls on -ко."
    - question: "Which syllable is stressed in the word шко́ла (school)?"
      options:
        - text: "First syllable (шко-)"
          correct: true
        - text: "Second syllable (-ла)"
          correct: false
        - text: "Both syllables equally"
          correct: false
        - text: "It changes depending on context"
          correct: false
      explanation: "Шко́ла has first-syllable stress — the emphasis falls on шко-."
    - question: "The words за́мок and замо́к have the same letters but different stress. What does за́мок (first-syllable stress) mean?"
      options:
        - text: "lock"
          correct: false
        - text: "castle"
          correct: true
        - text: "key"
          correct: false
        - text: "door"
          correct: false
      explanation: "За́мок with first-syllable stress means 'castle'. Замо́к with last-syllable stress means 'lock'."
    - question: "What does замо́к (last-syllable stress) mean?"
      options:
        - text: "castle"
          correct: false
        - text: "fortress"
          correct: false
        - text: "lock"
          correct: true
        - text: "gate"
          correct: false
      explanation: "Замо́к with last-syllable stress means 'lock'. За́мок with first-syllable stress means 'castle'."
    - question: "Which syllable is stressed in the word сестра́ (sister)?"
      options:
        - text: "First syllable (сес-)"
          correct: false
        - text: "Second syllable (-тра)"
          correct: true
        - text: "Both syllables equally"
          correct: false
        - text: "Neither — short words have no stress"
          correct: false
      explanation: "Сестра́ has last-syllable stress — the emphasis falls on -тра."
    - question: "Which syllable is stressed in the word кни́жка (book)?"
      options:
        - text: "First syllable (книж-)"
          correct: true
        - text: "Second syllable (-ка)"
          correct: false
        - text: "Both syllables equally"
          correct: false
        - text: "It depends on the sentence"
          correct: false
      explanation: "Кни́жка has first-syllable stress — the emphasis falls on книж-."
    - question: "Which syllable is stressed in the word дале́ко (far)?"
      options:
        - text: "First syllable (да-)"
          correct: false
        - text: "Second syllable (-ле-)"
          correct: true
        - text: "Third syllable (-ко)"
          correct: false
        - text: "All syllables equally"
          correct: false
      explanation: "Дале́ко has penultimate (second-to-last) stress — the emphasis falls on -ле-."
    - question: "Which syllable is stressed in the word голова́ (head)?"
      options:
        - text: "First syllable (го-)"
          correct: false
        - text: "Second syllable (-ло-)"
          correct: false
        - text: "Third syllable (-ва)"
          correct: true
        - text: "First and third equally"
          correct: false
      explanation: "Голова́ has last-syllable stress — the emphasis falls on -ва."
    - question: "Which statement about Ukrainian stress is true?"
      options:
        - text: "Stress always falls on the first syllable"
          correct: false
        - text: "Stress always falls on the last syllable"
          correct: false
        - text: "Stress always falls on the second-to-last syllable"
          correct: false
        - text: "Stress can fall on any syllable — it is free"
          correct: true
      explanation: "Ukrainian has free stress — it can fall on any syllable, unlike Polish (penultimate) or French (final)."
    - question: "What happens to the stress when рука́ (hand) becomes ру́ки (hands)?"
      options:
        - text: "The stress stays on the same syllable"
          correct: false
        - text: "The stress moves to a different syllable"
          correct: true
        - text: "The word loses its stress entirely"
          correct: false
        - text: "Both syllables become equally stressed"
          correct: false
      explanation: "Ukrainian has mobile stress — рука́ (stress on -ка) shifts to ру́ки (stress on ру-) in the plural."

- type: match-up
  title: "Stress and Meaning"
  instruction: "Match each stressed word to its English meaning. Pay attention to where the stress falls!"
  pairs:
    - left: "за́мок (stress on ЗА-)"
      right: "castle"
    - left: "замо́к (stress on -МОК)"
      right: "lock"
    - left: "му́ка (stress on МУ-)"
      right: "torment"
    - left: "мука́ (stress on -КА)"
      right: "flour"
    - left: "вода́"
      right: "water"
    - left: "ма́ма"
      right: "mom"
    - left: "шко́ла"
      right: "school"
    - left: "молоко́"
      right: "milk"

- type: true-false
  title: "Intonation Patterns"
  instruction: "Decide whether each statement about Ukrainian intonation and stress is true or false."
  items:
    - statement: "In Ukrainian statements, the pitch falls at the end of the sentence."
      correct: true
      explanation: "Correct! Declarative sentences have a falling pitch contour at the end."
    - statement: "Ukrainian yes/no questions use a simple rise at the very end, just like English."
      correct: false
      explanation: "Ukrainian yes/no questions rise sharply on the stressed syllable of the key word, then fall — not a simple terminal rise like English."
    - statement: "In questions with a question word (like Де?), the pitch rises on the question word itself."
      correct: true
      explanation: "Correct! In questions like Де кафе?, the highest pitch is on the question word Де, then the voice relaxes."
    - statement: "Ukrainian stress always falls on the first syllable of every word."
      correct: false
      explanation: "Ukrainian stress is free — it can fall on any syllable. Compare ма́ма (first) with вода́ (last)."
    - statement: "The words за́мок (castle) and замо́к (lock) have the same letters but different stress."
      correct: true
      explanation: "Correct! These are stress minimal pairs — same letters, different stress, different meaning."
    - statement: "Ukrainian exclamatory sentences use a sharp rise with strong emphasis on the key word."
      correct: true
      explanation: "Correct! Exclamations like Це кафе́! use a sharp rise with emphasis to express surprise or excitement."
    - statement: 'In the yes/no question "Це ма́ма?", the pitch rises on the stressed syllable of ма́ма and then falls.'
      correct: true
      explanation: "Correct! The pitch rises sharply on МА and falls immediately — this is the Ukrainian yes/no question pattern."
    - statement: "Ukrainian stress is fixed and predictable, like stress in Polish."
      correct: false
      explanation: "Ukrainian stress is free and mobile — it can fall on any syllable and can shift when a word changes form. Polish stress is nearly always on the penultimate syllable."

- type: fill-in
  title: "Mark the Stress"
  instruction: "Choose the word form with the correct stress mark."
  items:
    - sentence: "The word for 'water' with correct stress is ___."
      answer: "вода́"
      options: ["во́да", "вода́", "во́да́", "вода"]
      explanation: "Вода́ — stress falls on the last syllable."
    - sentence: "The word for 'school' with correct stress is ___."
      answer: "шко́ла"
      options: ["шко́ла", "школа́", "шко́ла́", "школа"]
      explanation: "Шко́ла — stress falls on the first syllable."
    - sentence: "The word for 'milk' with correct stress is ___."
      answer: "молоко́"
      options: ["мо́локо", "моло́ко", "молоко́", "молоко"]
      explanation: "Молоко́ — stress falls on the last (third) syllable."
    - sentence: "The word for 'mom' with correct stress is ___."
      answer: "ма́ма"
      options: ["ма́ма", "мама́", "ма́ма́", "мама"]
      explanation: "Ма́ма — stress falls on the first syllable."
    - sentence: "The word for 'castle' with correct stress is ___."
      answer: "за́мок"
      options: ["за́мок", "замо́к", "за́мо́к", "замок"]
      explanation: "За́мок (castle) has first-syllable stress. Замо́к (lock) has last-syllable stress."
    - sentence: "The word for 'lock' with correct stress is ___."
      answer: "замо́к"
      options: ["за́мок", "замо́к", "за́мо́к", "замок"]
      explanation: "Замо́к (lock) has last-syllable stress. За́мок (castle) has first-syllable stress."
    - sentence: "The word for 'sister' with correct stress is ___."
      answer: "сестра́"
      options: ["се́стра", "сестра́", "се́стра́", "сестра"]
      explanation: "Сестра́ — stress falls on the last syllable."
    - sentence: "The word for 'far' with correct stress is ___."
      answer: "дале́ко"
      options: ["да́леко", "дале́ко", "далеко́", "далеко"]
      explanation: "Дале́ко — stress falls on the second (penultimate) syllable."
    - sentence: "The word for 'head' with correct stress is ___."
      answer: "голова́"
      options: ["го́лова", "голо́ва", "голова́", "голова"]
      explanation: "Голова́ — stress falls on the last (third) syllable."
    - sentence: "The word for 'road' with correct stress is ___."
      answer: "доро́га"
      options: ["до́рога", "доро́га", "дорога́", "дорога"]
      explanation: "Доро́га — stress falls on the second (penultimate) syllable."
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/stress-and-intonation.yaml`

```yaml
items:
  - lemma: "замок"
    translation: "castle (за́мок) / lock (замо́к)"
    pos: "noun"
    gender: "m"
    notes: "Stress minimal pair — same letters, different stress, different meaning."
    usage: "за́мок = castle, замо́к = lock"
  - lemma: "вода"
    translation: "water"
    pos: "noun"
    gender: "f"
    notes: "Last-syllable stress вода́. Mobile stress in plural: во́ди."
    example: "Вода́ тут."
  - lemma: "рука"
    translation: "hand, arm"
    pos: "noun"
    gender: "f"
    notes: "Mobile stress: рука́ (singular) → ру́ки (plural)."
    example: "Це рука́."
  - lemma: "писати"
    translation: "to write"
    pos: "verb"
    aspect: "imperfective"
    notes: "Mobile stress in conjugation: писа́ти → пишу́ → пи́шеш."
  - lemma: "школа"
    translation: "school"
    pos: "noun"
    gender: "f"
    notes: "Penultimate stress: шко́ла."
    example: "Це шко́ла."
  - lemma: "молоко"
    translation: "milk"
    pos: "noun"
    gender: "n"
    notes: "Last-syllable stress: молоко́."
    example: "Молоко́ тут."
  - lemma: "добрий"
    translation: "good"
    pos: "adj"
    notes: "First-syllable stress: до́брий. Common in greetings: до́брий день."
    usage: "до́брий день = good day/hello"
  - lemma: "далеко"
    translation: "far"
    pos: "adv"
    notes: "Penultimate stress: дале́ко."
    example: "За́мок дале́ко."
  - lemma: "наголос"
    translation: "stress, accent (linguistic term)"
    pos: "noun"
    gender: "m"
    notes: "Metalinguistic term. На́голос — stress on the first syllable."
  - lemma: "інтонація"
    translation: "intonation"
    pos: "noun"
    gender: "f"
    notes: "Metalinguistic term. Інтона́ція — penultimate stress."
  - lemma: "питання"
    translation: "question"
    pos: "noun"
    gender: "n"
    notes: "Penultimate stress: пита́ння."
    example: "Це пита́ння."
  - lemma: "відповідь"
    translation: "answer"
    pos: "noun"
    gender: "f"
    notes: "First-syllable stress: ві́дповідь."
    example: "Це ві́дповідь."
  - lemma: "мама"
    translation: "mom"
    pos: "noun"
    gender: "f"
    notes: "First-syllable stress: ма́ма."
    example: "Це ма́ма."
  - lemma: "тато"
    translation: "dad"
    pos: "noun"
    gender: "m"
    notes: "First-syllable stress: та́то."
    example: "Та́то тут."
  - lemma: "хата"
    translation: "house, home (traditional)"
    pos: "noun"
    gender: "f"
    notes: "First-syllable stress: ха́та."
    example: "Це ха́та."
  - lemma: "кава"
    translation: "coffee"
    pos: "noun"
    gender: "f"
    notes: "First-syllable stress: ка́ва."
    example: "Ка́ва там."
  - lemma: "сестра"
    translation: "sister"
    pos: "noun"
    gender: "f"
    notes: "Last-syllable stress: сестра́. Mobile stress in plural: се́стри."
  - lemma: "кафе"
    translation: "cafe"
    pos: "noun"
    gender: "n"
    notes: "Last-syllable stress: кафе́. Indeclinable noun."
    example: "Це кафе́."
  - lemma: "книжка"
    translation: "book"
    pos: "noun"
    gender: "f"
    notes: "First-syllable stress: кни́жка."
    example: "Кни́жка там."
  - lemma: "дорога"
    translation: "road"
    pos: "noun"
    gender: "f"
    notes: "Penultimate stress: доро́га."
    example: "Це доро́га."
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
