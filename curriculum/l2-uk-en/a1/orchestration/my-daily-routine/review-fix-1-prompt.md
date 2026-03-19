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

## Plan Adherence Issues (Deterministic — MUST FIX)

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:quiz`
  - Expected: Plan requires ≥20 items
  - Actual: Activity has 8 items
  - Fix: Add 12 more items to 'quiz' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥20 items
  - Actual: Activity has 8 items
  - Fix: Add 12 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥20 items
  - Actual: Activity has 6 items
  - Fix: Add 14 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:match-up`
  - Expected: Plan requires ≥15 items
  - Actual: Activity has 8 items
  - Fix: Add 7 more items to 'match-up' activity


---

## Review Findings (targeted fix required)

**CONSTRAINTS:**
- Fix ONLY the issues listed below
- Do NOT rewrite surrounding text
- Preserve word count and structure
- Only modify these sections: Activities file, all activity blocks, Activities file, line 163, Activities file, lines 16-26 (Q2) and lines 38-48 (Q4), Entire content file, Section "Вступ (Introduction)", lines 3-22

### Finding 1: Activities — Severely Under Plan Item Counts (HIGH)
**Location**: Activities file, all activity blocks
**Problem**: Plan specifies quiz=20, fill-in=20, match-up=15, fill-in=6 (total 61 items). Actual delivery: quiz=8, fill-in=8, match-up=8, fill-in=6 (total 30 items). This is only 49% of planned activities.
**Required Fix**: Content rebuild needed for activities. Cannot be patched with FIND/REPLACE — requires generating 31 additional activity items.
**Severity**: HIGH

### Finding 2: Zero Engagement Boxes (HIGH)
**Location**: Entire content file
**Problem**: Audit reports 0 engagement boxes. The single callout on line 50 uses `[!cultural-note]` which is not a standard engagement box type (should be `[!culture-note]`). Richness gap shows `engagement: 0/2`. Module needs at least 2 engagement boxes.
**Required Fix**: Change `[!cultural-note]` to `[!culture-note]` and add at least one more engagement callout (e.g., `[!did-you-know]` about the proverb "Хто рано встає, тому Бог дає" in section "Вступ (Introduction)", or a `[!tip]` about the -ся/-сь mnemonic in section "Презентація (Presentation)").
**Severity**: HIGH

### Finding 3: Immersion Below Target (MEDIUM)
**Location**: Entire content file
**Problem**: Immersion at 13.9%, but Module 38 is in the "Modules 21+" band requiring 30-55% Ukrainian. The content is overwhelmingly English prose with Ukrainian examples interspersed. Ukrainian text appears almost exclusively in bold example sentences.
**Required Fix**: Add Ukrainian reading practice blocks after each section. Convert some English explanations to Ukrainian with parenthetical translations. Add Ukrainian mini-dialogues.
**Severity**: HIGH

### Finding 4: Activities Test Content Not Language (MEDIUM)
**Location**: Activities file, lines 16-26 (Q2) and lines 38-48 (Q4)
**Problem**: Q2 ("What is the correct order for these morning activities?") tests content recall of a morning sequence, not language skill. Q4 ("Which Ukrainian meal is traditionally the main, most substantial meal of the day?") tests cultural knowledge, not Ukrainian language. Per Rule 10a: "Can the learner answer without reading the Ukrainian text? If YES → rewrite."
**Required Fix**: Rewrite Q2 to test sequencing adverb usage (e.g., "Which word means 'then' in a sequence?"). Rewrite Q4 to test vocabulary in context (e.g., "Complete: О першій годині я ___.").
**Severity**: HIGH

### Finding 5: Missing Learning Objectives Preview (MEDIUM)
**Location**: Section "Вступ (Introduction)", lines 3-22
**Problem**: No explicit "Today you'll learn to..." preview. The intro jumps into content about daily routine concepts. Beginner modules need clear expectation-setting.
**Required Fix**: Add a brief learning objectives block after line 5, e.g., "In this lesson, you'll learn to: conjugate reflexive verbs, describe your morning and evening routine, use sequence words (спочатку, потім, нарешті), and tell time with о + Locative case."
**Severity**: HIGH

### Finding 6: Activity Explanation Contains Non-Word (LOW)
**Location**: Activities file, line 163
**Problem**: Explanation text "вмиваєть+ся" contains the token "вмиваєть" which is not a real Ukrainian word form (VESUM confirms NOT FOUND). While pedagogically this is showing a morpheme boundary, the scanner flags it.
**Required Fix**: Rewrite explanation to avoid the broken token: "Вона вмивається — the він/вона/воно form ends in -ться (consonant cluster), so the reflexive particle is -ся."
**Severity**: HIGH

---

## Critical Issues Found

### Issue 1: Activities — Severely Under Plan Item Counts (HIGH)
- **Location**: Activities file, all activity blocks
- **Problem**: Plan specifies quiz=20, fill-in=20, match-up=15, fill-in=6 (total 61 items). Actual delivery: quiz=8, fill-in=8, match-up=8, fill-in=6 (total 30 items). This is only 49% of planned activities.
- **Fix**: Content rebuild needed for activities. Cannot be patched with FIND/REPLACE — requires generating 31 additional activity items.

### Issue 2: Zero Engagement Boxes (HIGH)
- **Location**: Entire content file
- **Problem**: Audit reports 0 engagement boxes. The single callout on line 50 uses `[!cultural-note]` which is not a standard engagement box type (should be `[!culture-note]`). Richness gap shows `engagement: 0/2`. Module needs at least 2 engagement boxes.
- **Fix**: Change `[!cultural-note]` to `[!culture-note]` and add at least one more engagement callout (e.g., `[!did-you-know]` about the proverb "Хто рано встає, тому Бог дає" in section "Вступ (Introduction)", or a `[!tip]` about the -ся/-сь mnemonic in section "Презентація (Presentation)").

### Issue 3: Immersion Below Target (MEDIUM)
- **Location**: Entire content file
- **Problem**: Immersion at 13.9%, but Module 38 is in the "Modules 21+" band requiring 30-55% Ukrainian. The content is overwhelmingly English prose with Ukrainian examples interspersed. Ukrainian text appears almost exclusively in bold example sentences.
- **Fix**: Add Ukrainian reading practice blocks after each section. Convert some English explanations to Ukrainian with parenthetical translations. Add Ukrainian mini-dialogues.

### Issue 4: Activities Test Content Not Language (MEDIUM)
- **Location**: Activities file, lines 16-26 (Q2) and lines 38-48 (Q4)
- **Problem**: Q2 ("What is the correct order for these morning activities?") tests content recall of a morning sequence, not language skill. Q4 ("Which Ukrainian meal is traditionally the main, most substantial meal of the day?") tests cultural knowledge, not Ukrainian language. Per Rule 10a: "Can the learner answer without reading the Ukrainian text? If YES → rewrite."
- **Fix**: Rewrite Q2 to test sequencing adverb usage (e.g., "Which word means 'then' in a sequence?"). Rewrite Q4 to test vocabulary in context (e.g., "Complete: О першій годині я ___.").

### Issue 5: Missing Learning Objectives Preview (MEDIUM)
- **Location**: Section "Вступ (Introduction)", lines 3-22
- **Problem**: No explicit "Today you'll learn to..." preview. The intro jumps into content about daily routine concepts. Beginner modules need clear expectation-setting.
- **Fix**: Add a brief learning objectives block after line 5, e.g., "In this lesson, you'll learn to: conjugate reflexive verbs, describe your morning and evening routine, use sequence words (спочатку, потім, нарешті), and tell time with о + Locative case."

### Issue 6: Activity Explanation Contains Non-Word (LOW)
- **Location**: Activities file, line 163
- **Problem**: Explanation text "вмиваєть+ся" contains the token "вмиваєть" which is not a real Ukrainian word form (VESUM confirms NOT FOUND). While pedagogically this is showing a morpheme boundary, the scanner flags it.
- **Fix**: Rewrite explanation to avoid the broken token: "Вона вмивається — the він/вона/воно form ends in -ться (consonant cluster), so the reflexive particle is -ся."

---

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Act:163 | 「вмиваєть+ся」 | "вмивається — the -ться ending uses -ся after consonant" | Non-word form |

No Russianisms, calques, or grammar scope violations found. All Ukrainian verb forms verified against VESUM. The -ся/-сь conjugation paradigm for дивитися is correct (colloquial register forms дивлюсь, дивимось, дивитесь confirmed in VESUM alongside standard forms дивлюся, дивимося, дивитеся).

---

## Fix Plan to Reach 9/10 (REQUIRED — score is 7.6)

### Activities: 6/10 → 8/10
**What to fix:**
1. **Rebuild activities** with full item counts: quiz=20, fill-in=20, match-up=15, fill-in=6. This requires a pipeline rebuild (`--restart-from activities`), not manual patching.
2. Rewrite Q2 and Q4 to test language skills, not content recall.
3. Fix line 163 explanation to avoid "вмиваєть" token.

**Expected score after fix:** 8/10

### Experience Quality: 7/10 → 9/10
**What to fix:**
1. Add learning objectives preview after line 5 in section "Вступ (Introduction)".
2. Fix callout type: `[!cultural-note]` → `[!culture-note]` on line 50.
3. Add at least 1 more engagement callout — suggest `[!did-you-know]` with the proverb "Хто рано встає, тому Бог дає" in section "Вступ (Introduction)".
4. Add a "You can now..." celebration block in section "Продукування та Підсумок (Production and Summary)" before the final sentence.

**Expected score after fix:** 9/10

### LLM Fingerprint: 7/10 → 8/10
**What to fix:**
1. Vary section openings — currently 3 sections start with declarative English "we" statements.
2. Mix example formats — add a table for the дивитися conjugation instead of bullet list, use inline examples in some places.

**Expected score after fix:** 8/10

### Immersion: 13.9% → 25%+ (supports Experience and Language scores)
**What to fix:**
1. Add Ukrainian reading practice blocks (5-8 sentences) after sections "Презентація (Presentation)" and "Практика (Practice)".
2. Convert some English framing sentences to Ukrainian with translations.
3. Add the proverb "Хто рано встає, тому Бог дає" as an authentic Ukrainian text element.

**Expected impact:** Immersion should rise to ~25-30%, closer to the 30% minimum.

### Projected Overall After Fixes
```
(9×1.5 + 8×1.1 + 8×1.2 + 8×1.3 + 8×1.3 + 8×1.0 + 9×1.5) / 8.9
= (13.5 + 8.8 + 9.6 + 10.4 + 10.4 + 8.0 + 13.5) / 8.9
= 74.2 / 8.9
= 8.3/10
```

Note: Reaching 9.0 overall requires activity rebuild (pipeline) + immersion expansion, which are substantial content changes best handled by a pipeline rebuild (`--restart-from content`).

---

## Audit Failures (from automated re-audit)

```
❌ Structure check failed: Missing '## Summary'
📚 IMMERSION TOO LOW (14.8% vs 20-35% target)
--- STRICT GATES (Level A1) ---
Structure    ❌ Missing '## Summary'
Immersion    ❌ 14.8% LOW (target 20-35% (M38))
📝 RECOMMENDATION: UPDATE (patch fixes) (severity 30/100)
→ Structure issue: Missing '## Summary'
❌ AUDIT FAILED. Correct errors before proceeding.
Critical Failures:
• Structure: Missing '## Summary'
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/my-daily-routine-audit.log for details)
⚠️  RAG verification found unverified words (see audit report)
--- STATUS JSON GATE BLOCKERS ---
GATE BLOCKER: Structure: Missing '## Summary'
--- VESUM WORD VERIFICATION FAILURES ---
These words were NOT found in the VESUM morphological dictionary.
Check if they are valid Ukrainian forms. Fix misspellings or Russianisms.
  ❌ `сь` (source: prose)
  ❌ `ть` (source: prose)
```

---

## File Contents (for reference)

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/my-daily-routine.md`

```markdown
<!-- adapted from: Заболотний, Grade 6 -->

## Вступ (Introduction)

Welcome back to our language journey! Today, we are taking a significant step into the practical heart of the Ukrainian language. We are going to explore your daily routine, which is known in Ukrainian as **щоденний побут** (daily routine) or your everyday routine (**повсякденний побут**).

**In this lesson, you will learn to:**
- Conjugate common reflexive verbs (-ся / -сь)
- Describe your morning, daytime, and evening routine
- Use sequence words: **спочатку** (first), **потім** (then), **нарешті** (finally)
- Tell time correctly using **о** + Locative case (о сьомій годині)

We all have things that we do every single day, and learning how to describe them is incredibly empowering. It allows you to share your world, your habits, and your schedule with native speakers in a completely natural way.

> [!did-you-know] Хто рано встає, тому Бог дає
> This beloved Ukrainian proverb means "He who rises early, God provides for." It's the Ukrainian equivalent of "The early bird catches the worm" — and it perfectly sets the stage for today's lesson about daily routines!

To structure our conversation effectively, we first need to understand the conceptual split between the two main types of days you experience. The first is a busy **робочий день** (working day). This is the time filled with schedules, commuting, professional tasks, or academic classes. The second is a relaxing **вихідний день** (day off). On these days, the rhythm of life changes completely. The expectations are different, and the vocabulary you use will reflect that shift in pace and energy. 

When we talk about our routine, setting the scene is absolutely essential. We do this by discussing the start and end of activities, or the **початок і кінець дня** (start and end of the day). A day doesn't just happen all at once; it unfolds logically from morning until night. To establish a logical flow for your narrative, we use chronological markers. These are specific words that tell your listener how often something happens or when an event takes place. 

For instance, the word **щодня** means "every day." It is the perfect word to use for unbroken, reliable habits.
*   **Я щодня працюю.** — I work every day.
*   **Вона щодня читає.** — She reads every day.

When you travel to Ukraine or speak with Ukrainian friends, they will often ask you about your day. Being able to confidently say "I work every day" or "I rest on the weekend" builds an immediate connection. Let's look at a short example of a morning chat:

> — **Привіт! Як твій типовий день?** (Hi! How is your typical day?)
> — **Привіт! Мій робочий день дуже активний. Я щодня працюю.** (Hi! My working day is very active. I work every day.)
> — **А твій вихідний день?** (And your day off?)
> — **Вихідний день — це час для сім'ї. Я зазвичай відпочиваю.** (The day off is time for family. I usually rest.)

By mastering these concepts, you are not just memorizing vocabulary; you are learning how to build a clear, chronological story of your life. Let's dive deeper into the core verbs that make this storytelling possible!

## Презентація (Presentation)

At the core of your daily routine are the actions you perform on yourself. In Ukrainian grammar, we express these personal, self-directed actions using reflexive verbs. These are verbs that end with the special reflexive particle **-ся** or **-сь**. You have briefly met them before, but today we focus on how they define your daily hygiene and morning tasks.

Two of the most crucial verbs for the start of your day are **прокидатися** (to wake up) and **вмиватися** (to wash oneself). Let's explicitly address a very common learner error right now. English speakers often want to use the transitive verb **мити** (to wash) for everything, whether it is a plate, a car, or their own face. However, in Ukrainian, there is a strict grammatical and logical difference based on whether the action has an external object.

**The Washing Rule:**
*   **Я мию руки.** — I am washing my hands. (Transitive: you are washing a specific, separate object).
*   **Я вмиваюся.** — I am washing my face / washing up. (Reflexive: you are performing the general action of morning hygiene on yourself).

You must not say *"я мию"* when you mean washing your face in the morning. Always use **вмиватися**. Another vital reflexive verb is **одягатися** (to dress oneself). Just like washing, dressing is an action directed completely at yourself.

Now, let's look at the morphological focus of these verbs, using the Class II verb **дивитися** (to watch/look) as our primary model. The rule for adding the reflexive particle is beautifully musical and based entirely on the letter that comes right before it: you use **-сь** after vowels, and **-ся** after consonants.

**Conjugation Pattern: дивитися (to watch)**
*   **Я дивлюсь** — I watch (the ending -ю is a vowel, so we add **-сь**)
*   **Ти дивишся** — You watch (the ending -ш is a consonant, so we add **-ся**)
*   **Він/вона/воно дивиться** — He/she/it watches (consonant -ть, so **-ся**)
*   **Ми дивимось** — We watch (vowel -о, so **-сь**)
*   **Ви дивитесь** — You (plural/formal) watch (vowel -е, so **-сь**)
*   **Вони дивляться** — They watch (consonant -ть, so **-ся**)

This exact same rule applies to **одягатися**. Try it out: **я одягаюсь**, **ти одягаєшся**, **він одягається**. See how perfectly the **-ся** and **-сь** forms balance the sound of the word? This is Ukrainian euphony in action.

Beyond hygiene, your day is anchored by food. The three essential verbs for meals are **снідати** (to have breakfast), **обідати** (to have lunch), and **вечеряти** (to have dinner).

> [!culture-note] The Ukrainian Lunch
> This brings us to a fascinating cultural hook: the Ukrainian **обід** (lunch). In Western cultures, lunch might be a quick, light sandwich grabbed on the go. In Ukraine, **обід** is traditionally the main, most substantial meal of the day, occurring between 13:00 and 14:00. It typically involves a first course (like borsch or a rich soup) and a second course (meat or fish with a heavy side dish). Because it is such a heavy, important meal, the **обідня перерва** (lunch break) is a deeply respected time in schools, factories, and offices. People need a proper **обідня перерва** to enjoy this feast! So when you say **я обідаю**, you are talking about a serious, sit-down meal, not a quick snack.

## Практика (Practice)

Once you have finished your morning routine, it is time to leave the house. Here we encounter an important rule about daily commute and motion in Ukrainian. English relies heavily on the single, flexible verb "to go," but Ukrainian demands precise information about your method of transport.

You must distinguish between walking and riding as part of your daily sequence. If your daily commute involves traveling by foot, you use the verb **йти**. If your commute requires a bus, metro, tram, or car, you must use the verb **їхати**.
*   **Я йду на роботу.** — I am going to work (on foot).
*   **Я їду на роботу.** — I am going to work (by transport).

This is a critical part of your routine narrative. Using the wrong verb will confuse a native speaker, as they will picture you walking ten kilometers on the highway!

Next, let's fix a common time and case error. When English speakers want to schedule a routine task, they often translate "at seven o'clock" word-for-word, creating the incorrect phrase *"в сьому годину"* (using the preposition "в" plus the Accusative case). You must avoid this! The correct pattern for scheduling time in Ukrainian uses the preposition **о** (or **об** before a vowel) followed by the Locative case. Let's drill the correct Locative pattern for scheduling routine tasks:

*   **о сьомій годині** — at seven o'clock
*   **о восьмій годині** — at eight o'clock
*   **о дев'ятій годині** — at nine o'clock

To build a truly complex description of a day, you need frequency and sequence adverbs. We use the high-frequency word **зазвичай** (usually) to establish that a behavior is a habit. Then, we use sequence markers to logically connect the events. The three most important markers are **спочатку** (first), **потім** (then), and **нарешті** (finally). Sometimes, you can also use **після цього** (after that).

Look at how integrating these markers brings a routine to life in a fluid sequence:
*   **Спочатку я прокидаюся о сьомій годині.** — First, I wake up at seven o'clock.
*   **Потім я вмиваюся і снідаю.** — Then, I wash my face and have breakfast.
*   **Після цього я їду на роботу.** — After that, I go to work.
*   **Нарешті я обідаю.** — Finally, I have lunch.

Let's look at a complete morning sequence in a dialogue format to see how everything works together:

> — **Коли ти прокидаєшся?** (When do you wake up?)
> — **Я зазвичай прокидаюся о сьомій годині.** (I usually wake up at seven o'clock.)
> — **Що ти робиш потім?** (What do you do then?)
> — **Потім я вмиваюся і снідаю.** (Then I wash up and have breakfast.)
> — **Куди ти йдеш після цього?** (Where do you go after that?)
> — **Я їду на роботу. Я маю довгий робочий день.** (I go to work. I have a long working day.)

These adverbs are the essential building blocks of a great narrative.

## Продукування та Підсумок (Production and Summary)

As the busy **робочий день** comes to an end, we slowly transition into the evening. Returning home in Ukraine comes with a very specific and beloved cultural habit: the immediate change into **домашній одяг** (home clothes). 

This is a highly significant evening transition. For Ukrainians, changing clothes is not just about physical comfort; it represents the psychological boundary between the chaotic public world and the private, clean sanctuary of the home. The moment you cross the threshold of your apartment, you take off your street clothes and immediately put on your **домашній одяг**. It is a clear signal to your brain that the active day is officially over. Once you are wearing your **домашній одяг**, you are free to relax, **вечеряти** (have dinner), and perhaps **дивитися** (watch) a good movie or read a book.

For many people, the evening routine is the most peaceful part of the day. You leave the stress of the city completely behind. Imagine this relaxing sequence:
*   **Я повертаюся додому.** — I return home.
*   **Я одягаю домашній одяг.** — I put on home clothes.
*   **Я вечеряю.** — I have dinner.
*   **Я дивлюсь цікавий фільм.** — I watch an interesting film.

The final, definitive step of our daily sequence is sleep. We use the phrase **лягати спати** (to go to bed, literally "to lie down to sleep"). It is the perfect, quiet end to a long day.
*   **Нарешті я лягаю спати о десятій годині.** — Finally, I go to bed at ten o'clock.

Now, it is time for your synthesis task. You have all the grammatical and vocabulary tools needed to describe your own daily routine. I want you to practice contrasting a busy working day with a peaceful day off. Pay extremely close attention to your reflexive verb agreement (always remember the difference between **-ся** and **-сь**!) and your temporal markers like **о сьомій годині**.

Use these self-check questions to guide your production:
1. When do you usually wake up? (Practice using **зазвичай** and **прокидатися**).
2. What are the sequence markers you use in the morning? (**спочатку**, **потім**).
3. Do you walk or take transport to work? (**йти** vs **їхати**).
4. When is your **обідня перерва**?
5. Do you change into **домашній одяг** when you arrive home?
6. At what time do you **лягати спати**?

**🎯 You can now:**
- Describe your morning routine using reflexive verbs (прокидатися, вмиватися, одягатися)
- Talk about meals (снідати, обідати, вечеряти)
- Say what time things happen (о сьомій годині)
- Connect events into a story using спочатку → потім → нарешті
- Contrast a робочий день with a вихідний день

By mastering these patterns, you can confidently narrate the beautiful rhythm of your life in natural, fluent Ukrainian. Great job today, and see you in the next lesson!
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/my-daily-routine.yaml`

```yaml
- type: quiz
  title: "Daily Routine Knowledge Check"
  instruction: "Choose the correct answer for each question about daily routines in Ukrainian."
  items:
    - question: "Which verb means 'to wake up' in Ukrainian?"
      options:
        - text: "прокидатися"
          correct: true
        - text: "лягати"
          correct: false
        - text: "вмиватися"
          correct: false
        - text: "одягатися"
          correct: false
      explanation: "Прокидатися means to wake up. Лягати means to lie down, вмиватися means to wash up, одягатися means to get dressed."
    - question: "What is the correct order for these morning activities?"
      options:
        - text: "прокидатися, вмиватися, снідати"
          correct: true
        - text: "снідати, прокидатися, вмиватися"
          correct: false
        - text: "вмиватися, снідати, прокидатися"
          correct: false
        - text: "снідати, вмиватися, прокидатися"
          correct: false
      explanation: "A typical morning follows this order: wake up (прокидатися), wash up (вмиватися), then have breakfast (снідати)."
    - question: "If you travel to work by bus, which verb do you use?"
      options:
        - text: "їхати"
          correct: true
        - text: "йти"
          correct: false
        - text: "лягати"
          correct: false
        - text: "дивитися"
          correct: false
      explanation: "Їхати is used when traveling by transport (bus, car, metro). Йти means going on foot."
    - question: "Which Ukrainian meal is traditionally the main, most substantial meal of the day?"
      options:
        - text: "обід"
          correct: true
        - text: "сніданок"
          correct: false
        - text: "вечеря"
          correct: false
        - text: "перерва"
          correct: false
      explanation: "In Ukrainian culture, обід (lunch, around 13:00-14:00) is the biggest meal, typically with a first course and second course."
    - question: "What does the word зазвичай mean?"
      options:
        - text: "usually"
          correct: true
        - text: "always"
          correct: false
        - text: "never"
          correct: false
        - text: "sometimes"
          correct: false
      explanation: "Зазвичай means usually — it describes a regular habit, like я зазвичай прокидаюся о сьомій годині."
    - question: "What is the correct way to say 'at seven o'clock' in Ukrainian?"
      options:
        - text: "о сьомій годині"
          correct: true
        - text: "в сьому годину"
          correct: false
        - text: "на сьомій годині"
          correct: false
        - text: "до сьомої години"
          correct: false
      explanation: "Time expressions use о (or об before a vowel) + Locative case: о сьомій годині."
    - question: "What does домашній одяг mean?"
      options:
        - text: "home clothes"
          correct: true
        - text: "work uniform"
          correct: false
        - text: "street clothes"
          correct: false
        - text: "sports clothes"
          correct: false
      explanation: "Домашній одяг means home clothes — Ukrainians change into them immediately upon returning home."
    - question: "Which word means 'first' when listing the order of daily events?"
      options:
        - text: "спочатку"
          correct: true
        - text: "потім"
          correct: false
        - text: "нарешті"
          correct: false
        - text: "щодня"
          correct: false
      explanation: "Спочатку means first (in a sequence). Потім means then, нарешті means finally, щодня means every day."

- type: fill-in
  title: "Complete the Routine"
  instruction: "Choose the correct word to complete each sentence about daily activities."
  items:
    - sentence: "Я ___ о сьомій годині."
      answer: "прокидаюся"
      options: ["прокидаюся", "лягаю", "обідаю", "вечеряю"]
      explanation: "Прокидаюся (I wake up) fits the morning time — о сьомій годині (at seven o'clock)."
    - sentence: "___ я вмиваюся і снідаю."
      answer: "Потім"
      options: ["Потім", "Нарешті", "Щодня", "Додому"]
      explanation: "Потім (then) is the sequence marker that connects the next step after waking up."
    - sentence: "Я ___ на роботу автобусом."
      answer: "їду"
      options: ["їду", "йду", "лягаю", "дивлюсь"]
      explanation: "Їду (by transport) is correct because the sentence mentions автобусом (by bus)."
    - sentence: "Увечері я ___ цікавий фільм."
      answer: "дивлюсь"
      options: ["дивлюсь", "вмиваюся", "снідаю", "працюю"]
      explanation: "Дивлюсь (I watch) is the correct reflexive verb for watching a film."
    - sentence: "___ я лягаю спати о десятій годині."
      answer: "Нарешті"
      options: ["Нарешті", "Спочатку", "Потім", "Зазвичай"]
      explanation: "Нарешті (finally) marks the last event in the daily sequence — going to bed."
    - sentence: "Я ___ працюю з дев'ятої до п'ятої."
      answer: "щодня"
      options: ["щодня", "нарешті", "спочатку", "потім"]
      explanation: "Щодня (every day) is a frequency marker describing a regular habit."
    - sentence: "Я повертаюся ___ і одягаю домашній одяг."
      answer: "додому"
      options: ["додому", "на роботу", "спочатку", "нарешті"]
      explanation: "Додому means homeward/home. After work, you return home (повертатися додому)."
    - sentence: "О першій годині я маю обідню ___."
      answer: "перерву"
      options: ["перерву", "годину", "вечерю", "роботу"]
      explanation: "Обідня перерва (lunch break) — перерву is the Accusative form of перерва."

- type: match-up
  title: "Match Activities to Times of Day"
  instruction: "Match each daily activity to when it typically happens."
  pairs:
    - left: "прокидатися"
      right: "morning — wake up"
    - left: "вмиватися"
      right: "morning — wash up"
    - left: "снідати"
      right: "morning — have breakfast"
    - left: "їхати на роботу"
      right: "morning — commute"
    - left: "обідати"
      right: "afternoon — have lunch"
    - left: "повертатися додому"
      right: "evening — come home"
    - left: "вечеряти"
      right: "evening — have dinner"
    - left: "лягати спати"
      right: "night — go to bed"

- type: fill-in
  title: "Describe Your Typical Day"
  instruction: "Choose the correct reflexive verb form to complete each sentence."
  items:
    - sentence: "Ти ___ о восьмій годині?"
      answer: "прокидаєшся"
      options: ["прокидаєшся", "прокидаюся", "прокидається", "прокидатися"]
      explanation: "Ти прокидаєшся — the ти form uses -ся after the consonant ш."
    - sentence: "Вона ___ і снідає."
      answer: "вмивається"
      options: ["вмивається", "вмиваюся", "вмиватися", "вмиваєшся"]
      explanation: "Вона вмивається — the він/вона/воно form ends in -ться, where the reflexive particle -ся follows the consonant т."
    - sentence: "Я ___ і йду на роботу."
      answer: "одягаюсь"
      options: ["одягаюсь", "одягаєшся", "одягається", "одягатися"]
      explanation: "Я одягаюсь — the я form uses -сь after the vowel ю."
    - sentence: "Він ___ телевізор увечері."
      answer: "дивиться"
      options: ["дивиться", "дивлюсь", "дивишся", "дивитися"]
      explanation: "Він дивиться — the він form uses -ся after the consonant т."
    - sentence: "Ми ___ о шостій годині."
      answer: "прокидаємось"
      options: ["прокидаємось", "прокидаюся", "прокидаєшся", "прокидається"]
      explanation: "Ми прокидаємось — the ми form uses -сь after the vowel о."
    - sentence: "Вони ___ після вечері."
      answer: "одягаються"
      options: ["одягаються", "одягаюсь", "одягаєшся", "одягається"]
      explanation: "Вони одягаються — the вони form uses -ся after the consonant т."
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/my-daily-routine.yaml`

```yaml
items:
  - lemma: "прокидатися"
    translation: "to wake up"
    pos: "verb"
    aspect: "imperfective"
    usage: "Я прокидаюся о сьомій годині."
  - lemma: "вмиватися"
    translation: "to wash oneself (face/body)"
    pos: "verb"
    aspect: "imperfective"
    notes: "Reflexive — for morning hygiene. Use мити for washing objects (мити руки)."
  - lemma: "одягатися"
    translation: "to dress oneself, to get dressed"
    pos: "verb"
    aspect: "imperfective"
    usage: "Я швидко одягаюсь."
  - lemma: "снідати"
    translation: "to have breakfast"
    pos: "verb"
    aspect: "imperfective"
  - lemma: "обідати"
    translation: "to have lunch"
    pos: "verb"
    aspect: "imperfective"
    notes: "In Ukraine, обід is the main meal of the day (13:00-14:00)."
  - lemma: "вечеряти"
    translation: "to have dinner"
    pos: "verb"
    aspect: "imperfective"
  - lemma: "дивитися"
    translation: "to watch, to look"
    pos: "verb"
    aspect: "imperfective"
    notes: "Class II reflexive verb. Model for -ся/-сь conjugation."
  - lemma: "лягати"
    translation: "to lie down"
    pos: "verb"
    aspect: "imperfective"
    usage: "Я лягаю спати о десятій годині."
  - lemma: "йти"
    translation: "to go (on foot)"
    pos: "verb"
    aspect: "imperfective"
    notes: "Use for walking. Contrast with їхати (by transport)."
  - lemma: "їхати"
    translation: "to go (by transport)"
    pos: "verb"
    aspect: "imperfective"
    notes: "Use for bus, car, metro, tram. Contrast with йти (on foot)."
  - lemma: "повертатися"
    translation: "to return"
    pos: "verb"
    aspect: "imperfective"
    usage: "Я повертаюся додому."
  - lemma: "працювати"
    translation: "to work"
    pos: "verb"
    aspect: "imperfective"
  - lemma: "відпочивати"
    translation: "to rest"
    pos: "verb"
    aspect: "imperfective"
  - lemma: "зазвичай"
    translation: "usually"
    pos: "adverb"
    usage: "Я зазвичай прокидаюся о сьомій годині."
  - lemma: "спочатку"
    translation: "first, at first"
    pos: "adverb"
    notes: "Sequence marker — begins a series of events."
  - lemma: "потім"
    translation: "then, afterwards"
    pos: "adverb"
    notes: "Sequence marker — connects the next event."
  - lemma: "нарешті"
    translation: "finally"
    pos: "adverb"
    notes: "Sequence marker — marks the last event."
  - lemma: "щодня"
    translation: "every day"
    pos: "adverb"
    notes: "Frequency marker for daily habits."
  - lemma: "перерва"
    translation: "break"
    pos: "noun"
    gender: "f"
    usage: "обідня перерва — lunch break"
  - lemma: "одяг"
    translation: "clothes, clothing"
    pos: "noun"
    gender: "m"
    usage: "домашній одяг — home clothes"
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
- Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/my-daily-routine.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/my-daily-routine.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/my-daily-routine.yaml`

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
