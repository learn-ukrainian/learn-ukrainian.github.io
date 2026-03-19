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

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥20 items
  - Actual: Activity has 8 items
  - Fix: Add 12 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥20 items
  - Actual: Activity has 6 items
  - Fix: Add 14 more items to 'fill-in' activity


---

## Review Findings (targeted fix required)

**CONSTRAINTS:**
- Fix ONLY the issues listed below
- Do NOT rewrite surrounding text
- Preserve word count and structure
- Only modify these sections: Line 101 / Section "Практика та підсумок (Practice and Summary)", Line 86 / Section "Лексика та культурний контекст (Vocabulary and Culture)", Lines 1-7 / Section "Вступ (Introduction)" and Lines 90-126 / Section "Практика та підсумок (Practice and Summary)", Whole module, Whole module / All sections

### Finding 1: Stress Error — те́бе → тебе́
**Location**: Line 101 / Section "Практика та підсумок (Practice and Summary)"
**Problem**: Wrong stress placement. VESUM confirms тебе is a form of ти (pronoun, genitive/accusative). The stress falls on the second syllable: тебе́, not те́бе. Pre-screen D.0 correctly flagged this.
**Required Fix**: Replace `те́бе` with `тебе́`
**Severity**: HIGH

### Finding 2: Zero Engagement Boxes
**Location**: Whole module / All sections
**Problem**: The module uses italicized headers (*Learner Error Warning: Aspect Conflict*, *FYI: The Synthetic Future*, *Learner Error: "Next" Time Expressions*, *Expressing Intentions and Ukrainian Caution*) instead of proper Markdown callout boxes. These don't render as engagement elements and fail the richness gate. Pre-audit shows 0 engagement boxes (minimum 1 for A1). The richness score is 54% (threshold 60%) with gaps in `engagement: 0/2` and `video_embeds: 0/2`.
**Required Fix**: Convert italicized headers to proper callout boxes: `> [!warning]` for learner errors, `> [!tip]` for FYI, `> [!culture]` for the proverb section.
**Severity**: HIGH

### Finding 3: Missing Warmth Markers — Cold Pedagogy Risk
**Location**: Lines 1-7 / Section "Вступ (Introduction)" and Lines 90-126 / Section "Практика та підсумок (Practice and Summary)"
**Problem**: Beginner safety requires ≥3 encouragement phrases, ≥2 "Don't worry" moments, ≥2 "You can now..." validation markers. Module has ~1 encouragement phrase ("Great job" at the very end) and 0 "You can now..." markers. The "Would I Continue?" test fails on quick wins (no practice before line 92) and encouragement (almost none throughout).
**Required Fix**: Add "Привіт!" opening, add 2-3 encouragement phrases between sections, convert self-check questions into a "You can now..." celebration list.
**Severity**: HIGH

### Finding 4: Imperative кажи́ in Proverb (Pre-Screen Confirmation)
**Location**: Line 86 / Section "Лексика та культурний контекст (Vocabulary and Culture)"
**Problem**: Pre-screen flagged imperative кажи́ (VESUM: verb:imperf:impr:s:2) — imperatives not taught until M47. However, this is a **fixed proverb expression**, not productive grammar. The learner is not being asked to form imperatives — they're encountering a cultural set phrase. **DISMISS as LOW severity** — the proverb should stay, but add a brief English note that this is a fixed expression.
**Required Fix**: Add "(this is a fixed expression — you don't need to learn the verb form yet)" after the translation.
**Severity**: HIGH

### Finding 5: Immersion Below Target
**Location**: Whole module
**Problem**: Module is heavily English-dominant. Ukrainian appears mainly in isolated bold examples and the dialogue block (lines 106-119). The prose sections "Вступ (Introduction)" and "Лексика та культурний контекст (Vocabulary and Culture)" are almost entirely English with Ukrainian words sprinkled in bold.
**Required Fix**: Add Ukrainian reading practice blocks after sections "Презентація граматики (Grammar Presentation)" and "Лексика та культурний контекст (Vocabulary and Culture)" — 3-5 Ukrainian sentences each with translations, practicing the буду + infinitive pattern in context.
**Severity**: HIGH

---

## Critical Issues Found

### Issue 1: Stress Error — те́бе → тебе́
- **Location**: Line 101 / Section "Практика та підсумок (Practice and Summary)"
- **Original**: 「Які́ у те́бе пла́ни на ве́чір?」
- **Problem**: Wrong stress placement. VESUM confirms тебе is a form of ти (pronoun, genitive/accusative). The stress falls on the second syllable: тебе́, not те́бе. Pre-screen D.0 correctly flagged this.
- **Fix**: Replace `те́бе` with `тебе́`

### Issue 2: Zero Engagement Boxes
- **Location**: Whole module / All sections
- **Original**: N/A — no `[!tip]`, `[!example]`, `[!cultural-note]`, `[!did-you-know]` callout boxes exist anywhere in the content.
- **Problem**: The module uses italicized headers (*Learner Error Warning: Aspect Conflict*, *FYI: The Synthetic Future*, *Learner Error: "Next" Time Expressions*, *Expressing Intentions and Ukrainian Caution*) instead of proper Markdown callout boxes. These don't render as engagement elements and fail the richness gate. Pre-audit shows 0 engagement boxes (minimum 1 for A1). The richness score is 54% (threshold 60%) with gaps in `engagement: 0/2` and `video_embeds: 0/2`.
- **Fix**: Convert italicized headers to proper callout boxes: `> [!warning]` for learner errors, `> [!tip]` for FYI, `> [!culture]` for the proverb section.

### Issue 3: Missing Warmth Markers — Cold Pedagogy Risk
- **Location**: Lines 1-7 / Section "Вступ (Introduction)" and Lines 90-126 / Section "Практика та підсумок (Practice and Summary)"
- **Original**: The module opens with "Welcome back to your Ukrainian journey!" (no Ukrainian greeting) and ends with "Great job expanding your timeline—the future looks bright!" (single encouragement, no progress celebration list).
- **Problem**: Beginner safety requires ≥3 encouragement phrases, ≥2 "Don't worry" moments, ≥2 "You can now..." validation markers. Module has ~1 encouragement phrase ("Great job" at the very end) and 0 "You can now..." markers. The "Would I Continue?" test fails on quick wins (no practice before line 92) and encouragement (almost none throughout).
- **Fix**: Add "Привіт!" opening, add 2-3 encouragement phrases between sections, convert self-check questions into a "You can now..." celebration list.

### Issue 4: Imperative кажи́ in Proverb (Pre-Screen Confirmation)
- **Location**: Line 86 / Section "Лексика та культурний контекст (Vocabulary and Culture)"
- **Original**: 「Не кажи́ "гоп", по́ки не переско́чиш」
- **Problem**: Pre-screen flagged imperative кажи́ (VESUM: verb:imperf:impr:s:2) — imperatives not taught until M47. However, this is a **fixed proverb expression**, not productive grammar. The learner is not being asked to form imperatives — they're encountering a cultural set phrase. **DISMISS as LOW severity** — the proverb should stay, but add a brief English note that this is a fixed expression.
- **Fix**: Add "(this is a fixed expression — you don't need to learn the verb form yet)" after the translation.

### Issue 5: Immersion Below Target
- **Location**: Whole module
- **Original**: Pre-audit shows 11.0% immersion (target for M37 is 30-55% per A1 band "Modules 21+")
- **Problem**: Module is heavily English-dominant. Ukrainian appears mainly in isolated bold examples and the dialogue block (lines 106-119). The prose sections "Вступ (Introduction)" and "Лексика та культурний контекст (Vocabulary and Culture)" are almost entirely English with Ukrainian words sprinkled in bold.
- **Fix**: Add Ukrainian reading practice blocks after sections "Презентація граматики (Grammar Presentation)" and "Лексика та культурний контекст (Vocabulary and Culture)" — 3-5 Ukrainian sentences each with translations, practicing the буду + infinitive pattern in context.

---

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 101 | 「те́бе」 | тебе́ | Stress error |
| 86 | 「кажи́」(in proverb) | Keep — fixed expression, add English note | Scope (LOW — dismiss) |

---

## Fix Plan to Reach 9/10 (REQUIRED — score is 7.7)

### Experience Quality: 7/10 → 9/10
**What to fix:**
1. Line 1: Add "Привіт! 👋" before the section header or as first line of content — warm Ukrainian greeting.
2. Lines 29, 40, 59, 71: Convert italicized headers to proper callout boxes (`> [!warning]`, `> [!tip]`, `> [!culture]`). This fixes both engagement (0→4) and richness gaps.
3. Line 126: Expand ending into a "You can now..." celebration list with 3-4 specific achievements.
4. Add 2 encouragement phrases between sections (e.g., after the conjugation table: "You've just mastered the full буду conjugation — that's a huge step!")

**Expected score after fix:** 9/10

### Beginner Safety: 7/10 → 9/10
**What to fix:**
1. Add a mini-practice prompt after section "Презентація граматики (Grammar Presentation)" (~line 38) — "Try forming a sentence: Я буду ___. Pick any verb you know!"
2. Add 2 "don't worry" moments — e.g., after aspect warning (line 38): "Don't worry — at this stage, all the verbs we use are imperfective, so this rule is easy to follow."
3. Section "Практика та підсумок (Practice and Summary)": Convert self-check questions into a progress celebration.

**Expected score after fix:** 9/10

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. Line 101: Change 「те́бе」 → тебе́.

**Expected score after fix:** 9/10

### LLM Fingerprint: 8/10 → 9/10
**What to fix:**
1. Convert all italicized section sub-headers (*Learner Error Warning*, *FYI*, etc.) to proper callout boxes — removes the non-standard formatting pattern.

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 8×1.1 + 8×1.2 + 8×1.3 + 9×1.3 + 9×1.0 + 9×1.5) / 8.9
= (13.5 + 8.8 + 9.6 + 10.4 + 11.7 + 9.0 + 13.5) / 8.9
= 76.5 / 8.9 = 8.6/10
```

---

## Audit Failures (from automated re-audit)

```
--- STRICT GATES (Level A1) ---
Pedagogy     ❌ 3 violations
📚 PEDAGOGICAL VIOLATIONS FOUND:
📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
→ 3 violations (minor)
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/tomorrow-future-tense-audit.log for details)
--- VESUM WORD VERIFICATION FAILURES ---
These words were NOT found in the VESUM morphological dictionary.
Check if they are valid Ukrainian forms. Fix misspellings or Russianisms.
  ❌ `Захарійчук` (source: prose)
```

---

## File Contents (for reference)

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/tomorrow-future-tense.md`

```markdown
## Вступ (Introduction)

Привіт! Welcome back to your Ukrainian journey! So far, we have spent our time exploring the present moment, asking what we are doing right now. In our previous module, *Yesterday - Past Tense*, we learned how to look backward on the timeline and talk about what has already happened. Now, we are going to look forward. We will learn how to talk about what we will do, where we will go, and what will happen **за́втра** (tomorrow).

Understanding this timeline is crucial for having meaningful conversations. You already know how to say "I am reading" or "I read yesterday." By the end of this lesson, you will be able to confidently say "I will read tomorrow." This opens up a whole new world of planning, hoping, and dreaming in Ukrainian. You will be able to share your schedule, organize meetings, and tell your friends what you are excited about doing.

In Ukrainian culture, looking toward the future often carries a deep sense of optimism and resilience. You will frequently hear the inspiring phrase **«За́втра бу́де нови́й день»** (Tomorrow will be a new day). This isn't just a simple statement about the calendar; it is a powerful expression of hope and strength. Even when times are difficult, there is a strong cultural belief that tomorrow brings a fresh start and new possibilities. By learning to use the future tense, you are not just learning a set of grammatical rules—you are learning to express this exact same hope and looking forward to the exciting plans you **бу́деш** (will) make. Let's get started and look at what the future holds!

## Презентація граматики (Grammar Presentation)

To talk about the future in Ukrainian, we use a simple two-part structure, often called the compound future tense. This is the most common way to express future actions, and it is very similar to how you say "I will work" in English. 

According to the official Ukrainian language standards, this form is straightforward: we take a special helper verb and pair it with the dictionary form (the infinitive) of the main action verb. 

**Compound Future Formula:** 
**бу́ду** (helper verb) + **роби́ти** (infinitive verb)

The helper verb we use is a form of "to be." It changes depending on who is doing the action, while the second verb always stays exactly the same. Let's look at how to conjugate this helper verb for all persons.

| Pronoun | Helper Verb | Main Verb | English |
|---|---|---|---|
| **я** | **бу́ду** | **чита́ти** | I will read |
| **ти** | **бу́деш** | **чита́ти** | you will read |
| **він/вона́/воно́** | **бу́де** | **чита́ти** | he/she/it will read |
| **ми** | **бу́демо** | **чита́ти** | we will read |
| **ви** | **бу́дете** | **чита́ти** | you (plural/formal) will read |
| **вони́** | **бу́дуть** | **чита́ти** | they will read |

> [!warning] Learner Error: Aspect Conflict

There is one critical rule you must remember when building these sentences: the helper verb **бу́ду** can *only* be used with imperfective verbs. These are the regular verbs we have been learning so far—verbs that focus on the process of an action, not its completion. 

Because English "will read" doesn't specify if the action is complete or ongoing, many learners try to combine **бу́ду** with perfective (completed action) verbs. This is a common error and is incorrect in Ukrainian.

*   ✅ Correct: **я бу́ду чита́ти** (I will be reading / I will read)
*   ❌ Incorrect: ~~я бу́ду прочита́ти~~

The word **бу́ду** acts like a strict grammatical marker telling us an ongoing or repeated action is going to happen.

Don't worry — at this stage, all the verbs we use are imperfective, so this rule is easy to follow. You will learn perfective verbs later, and by then, this pattern will feel natural.

You have just mastered the full **бу́ду** conjugation — that is a huge step! Try forming a sentence right now: **Я бу́ду ___.** Pick any verb you know!

> **📖 Читаємо українською (Reading Practice)**
>
> **Я бу́ду чита́ти кни́гу за́втра.** — I will read a book tomorrow.
> **Ти бу́деш працюва́ти вра́нці.** — You will work in the morning.
> **Він бу́де готува́ти ве́черю.** — He will cook dinner.
> **Ми бу́демо диви́тися фі́льм.** — We will watch a movie.
> **Вони́ бу́дуть гуля́ти в па́рку.** — They will walk in the park.

> [!tip] FYI: The Synthetic Future

As you read authentic Ukrainian texts, listen to music, or read the news, you might notice another way to express the future tense. This is called the synthetic future tense, where the helper verb is attached directly to the end of the infinitive as a single word. 

For example, instead of **бу́ду працюва́ти** (I will work), you might see **працюва́тиму**. Instead of **бу́деш працюва́ти** (you will work), you might see **працюва́тимеш**. 

At this stage, you do not need to memorize how to form this single-word future tense. The two-part compound future (**бу́ду** + infinitive) is completely natural, correct, and all you need for daily communication. Just keep this synthetic form in mind so you can recognize it when you encounter it!
<!-- adapted from: Grade 4 textbook -->

## Лексика та культурний контекст (Vocabulary and Culture)

To make your future plans clear, you need the right time markers. The most important word is, of course, **за́втра** (tomorrow). You can also look slightly further ahead with **післяза́втра** (the day after tomorrow), or talk about things happening **ско́ро** (soon). 

When we talk about our schedules, we usually specify the time of day. In Ukrainian, these expressions are used constantly and form very natural chunks of speech:

*   **за́втра вра́нці** — tomorrow morning
*   **за́втра вде́нь** — tomorrow afternoon
*   **за́втра вве́чері** — tomorrow evening

These chunks appear constantly in everyday speech. Notice how Ukrainians build their daily schedule around them:

*   **За́втра вра́нці я бу́ду пи́ти ка́ву.** — Tomorrow morning I will drink coffee.
*   **За́втра вде́нь ми бу́демо працюва́ти.** — Tomorrow afternoon we will work.
*   **За́втра вве́чері вони́ бу́дуть диви́тися фі́льм.** — Tomorrow evening they will watch a movie.

You can also combine these with **ско́ро** (soon) and **по́тім** (then, afterwards) to create natural sequences:

*   **Ско́ро я бу́ду вчи́ти но́ві слова́.** — Soon I will study new words.
*   **Спочатку́ я бу́ду чита́ти, а по́тім бу́ду писа́ти.** — First I will read, and then I will write.

> [!warning] Learner Error: "Next" Time Expressions

When we want to talk about **насту́пний** (next) week or year, we run into a small difference between English and Ukrainian. In English, we just say "next week." But in Ukrainian, time expressions that answer the question "when?" often require a special ending called the Genitive case. 

You should avoid translating "next week" directly word-for-word into the Nominative case. Instead, memorize these very common phrases where the endings change to **-ого** and **-я** or **-у**:

*   **насту́пного ти́жня** — next week
*   **насту́пного ро́ку** — next year
*   **насту́пного ра́зу** — next time

Do not say ~~насту́пний ти́ждень~~ when you mean "I will do it next week." Always use the modified phrase **насту́пного ти́жня**.

> [!culture] Expressing Intentions and Ukrainian Caution

When you have a **план** (plan), how certain are you that it will happen? The verbs you choose signal your confidence. 

If you use the future tense with **бу́ду**, you are expressing strong confidence. It means the event is scheduled and definite. 

*   **Я бу́ду там за́втра.** — I will be there tomorrow. (100% certainty)

However, if you are just thinking about what you would like to do, or if you are preparing for something that isn't fully confirmed, you should use verbs of intention: **хоті́ти** (to want) or **збира́тися** (to be going to / to get ready).

*   **Я хо́чу сказа́ти...** — I want to say...
*   **Я збира́юся ї́хати додо́му.** — I am going to go home. (My intention)

If you are thinking about bigger, more distant aspirations, you can use the verb **мрі́яти** (to dream).

Compare these three levels of certainty side by side:

*   **Я бу́ду вчи́ти украї́нську за́втра.** — I will study Ukrainian tomorrow. (definite)
*   **Я збира́юся вчи́ти украї́нську за́втра.** — I am going to study Ukrainian tomorrow. (intention)
*   **Я хо́чу вчи́ти украї́нську за́втра.** — I want to study Ukrainian tomorrow. (wish)

> **📖 Читаємо українською (Reading Practice)**
>
> **За́втра вра́нці я бу́ду пи́ти ка́ву.** — Tomorrow morning I will drink coffee.
> **Насту́пного ти́жня ми бу́демо відпочива́ти.** — Next week we will rest.
> **Вона́ збира́ється ї́хати в село́.** — She is going to travel to the village.
> **Я хо́чу вчи́ти украї́нську ско́ро.** — I want to study Ukrainian soon.
> **Вони́ планува́тимуть по́дорож.** — They will plan a trip.

You are doing great — you already know how to express time, certainty, and intention in Ukrainian. That is real progress!

Culturally, Ukrainians are often a bit cautious when making grand, absolute plans for the future. There is a famous proverb that perfectly captures this feeling: **«Не кажи́ "гоп", по́ки не переско́чиш»** (Don't say 'hop' until you've jumped). 

This proverb (a fixed expression — you don't need to learn the verb form кажи yet) advises against celebrating a plan before it is actually completed. Because of this slight cultural superstition, it is very common to hear people soften their future statements. Instead of a hard "I will," many people prefer to use **сподіва́тися** (to hope) or **планува́ти** (to plan). If you ask someone when they will finish a task, they might tell you they will do it **пізні́ше** (later) rather than giving an exact time. It shows that while you have a wonderful idea, you also respect that the future is never entirely in your control.

Here is how these softened statements sound in practice:

*   **Я сподіва́юся, що за́втра бу́де га́рна пого́да.** — I hope that tomorrow the weather will be nice.
*   **Ми плану́ємо ї́хати в село́ насту́пного ти́жня.** — We plan to travel to the village next week.
*   **Вона́ сподіва́ється ско́ро ві́дпочити.** — She hopes to rest soon.

## Практика та підсумок (Practice and Summary)

Now it is time to put your new skills to work! As an event planner for your own life, you will frequently need to discuss your schedule. When asking others about their schedules, the most common questions revolve around the weekend or the evening.

Try using these common combinations in your daily conversations:
*   **ма́ти пла́ни** — to have plans
*   **склада́ти план** — to make a plan
*   **пла́ни на майбу́тнє** — plans for the future

Here is how you might practice asking and answering these questions:

*   **— Які́ у тебе́ пла́ни на ве́чір?** (What are your plans for the evening?)
*   **— Я бу́ду чита́ти кни́гу, а по́тім бу́ду спа́ти.** (I will read a book, and then I will sleep.)

*   **— Що ти бу́деш роби́ти за́втра вра́нці?** (What will you do tomorrow morning?)
*   **— За́втра вра́нці я бу́ду пи́ти ка́ву і слу́хати му́зику.** (Tomorrow morning I will drink coffee and listen to music.)

*   **— Ви бу́дете працюва́ти насту́пного ти́жня?** (Will you work next week?)
*   **— Ні, насту́пного ти́жня я бу́ду відпочива́ти.** (No, next week I will rest.)

Let's look at a realistic dialogue. Imagine you are acting as an event planner, coordinating with a friend about the upcoming week. Notice how they use the correct forms of the helper verb and the proper time expressions.

> — Приві́т! Ти ма́єш пла́ни на вихідні́?
> (Hi! Do you have plans for the weekend?)
>
> — Приві́т! Так, я збира́юся ї́хати в село́. А ти?
> (Hi! Yes, I am going to travel to the village. And you?)
>
> — Я бу́ду працюва́ти. Але́ насту́пного ти́жня я хо́чу відпочива́ти.
> (I will work. But next week I want to rest.)
>
> — Це до́брий план. Що ти бу́деш роби́ти за́втра вве́чері?
> (That is a good plan. What will you do tomorrow evening?)
>
> — За́втра вве́чері я бу́ду готува́ти суп, а по́тім ми бу́демо диви́тися фі́льм.
> (Tomorrow evening I will cook soup, and then we will watch a movie.)
>
> — Чудо́во! Я сподіва́юся, за́втра бу́де га́рний день!
> (Wonderful! I hope tomorrow will be a nice day!)
>
> — Я то́ж! За́втра бу́де нови́й день.
> (Me too! Tomorrow will be a new day.)

Now try building your own sentences! Use the formula **pronoun + бу́ду/бу́деш/бу́де... + infinitive** and add a time marker. For example: **Я бу́ду гуля́ти за́втра вве́чері.** (I will walk tomorrow evening.)

**Self-Check Questions:**
1. Can you conjugate the helper verb **бу́ду** for all pronouns (я, ти, він, ми, ви, вони)?
2. Do you use perfective or imperfective verbs with **бу́ду**?
3. How do you correctly say "tomorrow morning" and "next week" in Ukrainian?

**You can now:**
- ✅ Form the compound future tense with **бу́ду** + infinitive for all persons
- ✅ Use time expressions like **за́втра вра́нці** and **насту́пного ти́жня** correctly
- ✅ Express plans with different levels of certainty (**бу́ду** vs **збира́юся** vs **хо́чу**)
- ✅ Sound culturally natural when discussing future plans

In just one module, you have gained the ability to talk about tomorrow, next week, and all your future dreams. You can confidently use the **бу́ду** forms, avoiding common pitfalls, and you know how to sound culturally natural. Чудо́во! (Wonderful!) — the future looks bright!

## Summary

This module introduced the **compound future tense** in Ukrainian. The formula is simple: a conjugated form of **бу́ти** (бу́ду, бу́деш, бу́де, бу́демо, бу́дете, бу́дуть) + an **imperfective infinitive**. You learned essential time markers — **за́втра** (tomorrow), **ско́ро** (soon), **насту́пного ти́жня** (next week) — and how to express different levels of certainty: **бу́ду** for confident plans, **збира́юся** for intentions, and **хо́чу** for wishes. Remember: don't worry if it feels like a lot — you already have all the tools you need to talk about your future in Ukrainian!
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/tomorrow-future-tense.yaml`

```yaml
- type: fill-in
  title: "Complete the Future Tense"
  instruction: "Choose the correct form of the helper verb to complete each future tense sentence."
  items:
    - sentence: "Я ___ читати книгу завтра."
      answer: "буду"
      options: ["буду", "будеш", "буде", "будемо"]
      explanation: "With я (I), the helper verb is буду."
    - sentence: "Ти ___ працювати завтра вранці."
      answer: "будеш"
      options: ["буду", "будеш", "буде", "будуть"]
      explanation: "With ти (you), the helper verb is будеш."
    - sentence: "Він ___ готувати суп ввечері."
      answer: "буде"
      options: ["буду", "будеш", "буде", "будемо"]
      explanation: "With він (he), the helper verb is буде."
    - sentence: "Ми ___ дивитися фільм потім."
      answer: "будемо"
      options: ["буду", "будеш", "будемо", "будуть"]
      explanation: "With ми (we), the helper verb is будемо."
    - sentence: "Ви ___ відпочивати наступного тижня."
      answer: "будете"
      options: ["будемо", "будете", "будуть", "буде"]
      explanation: "With ви (you plural/formal), the helper verb is будете."
    - sentence: "Вони ___ слухати музику скоро."
      answer: "будуть"
      options: ["буде", "будемо", "будете", "будуть"]
      explanation: "With вони (they), the helper verb is будуть."
    - sentence: "Вона ___ писати пізніше."
      answer: "буде"
      options: ["буду", "будеш", "буде", "будуть"]
      explanation: "With вона (she), the helper verb is буде."
    - sentence: "Я ___ гуляти завтра вдень."
      answer: "буду"
      options: ["буду", "будеш", "будемо", "будуть"]
      explanation: "With я (I), the helper verb is буду."
    - sentence: "Ти ___ дивитися фільм ввечері."
      answer: "будеш"
      options: ["буду", "будеш", "буде", "будемо"]
      explanation: "With ти (you), the helper verb is будеш."
    - sentence: "Вони ___ відпочивати наступного тижня."
      answer: "будуть"
      options: ["буде", "будемо", "будете", "будуть"]
      explanation: "With вони (they), the helper verb is будуть."
    - sentence: "Ми ___ слухати музику завтра вранці."
      answer: "будемо"
      options: ["буду", "будеш", "будемо", "будуть"]
      explanation: "With ми (we), the helper verb is будемо."
    - sentence: "Він ___ працювати пізніше."
      answer: "буде"
      options: ["буду", "будеш", "буде", "будемо"]
      explanation: "With він (he), the helper verb is буде."
    - sentence: "Ви ___ готувати вечерю скоро."
      answer: "будете"
      options: ["будемо", "будете", "будуть", "буде"]
      explanation: "With ви (you plural/formal), the helper verb is будете."
    - sentence: "Вона ___ їхати в село післязавтра."
      answer: "буде"
      options: ["буду", "будеш", "буде", "будуть"]
      explanation: "With вона (she), the helper verb is буде."
    - sentence: "Я ___ спати рано завтра."
      answer: "буду"
      options: ["буду", "будеш", "буде", "будемо"]
      explanation: "With я (I), the helper verb is буду."
    - sentence: "Ти ___ малювати завтра вдень."
      answer: "будеш"
      options: ["буду", "будеш", "будемо", "будуть"]
      explanation: "With ти (you), the helper verb is будеш."
    - sentence: "Вони ___ готувати суп разом."
      answer: "будуть"
      options: ["буде", "будемо", "будете", "будуть"]
      explanation: "With вони (they), the helper verb is будуть."
    - sentence: "Ми ___ гуляти в парку скоро."
      answer: "будемо"
      options: ["буду", "будеш", "будемо", "будуть"]
      explanation: "With ми (we), the helper verb is будемо."
    - sentence: "Ви ___ читати книгу наступного тижня."
      answer: "будете"
      options: ["будемо", "будете", "будуть", "буде"]
      explanation: "With ви (you plural/formal), the helper verb is будете."
    - sentence: "Воно ___ починатися скоро."
      answer: "буде"
      options: ["буду", "будеш", "буде", "будуть"]
      explanation: "With воно (it), the helper verb is буде."

- type: quiz
  title: "Future Tense Knowledge Check"
  instruction: "Choose the correct answer for each question about the Ukrainian future tense."
  items:
    - question: "Which two parts make up the compound future tense in Ukrainian?"
      options:
        - text: "a form of бути + infinitive verb"
          correct: true
        - text: "a form of мати + past tense verb"
          correct: false
        - text: "a pronoun + present tense verb"
          correct: false
        - text: "a form of хотіти + infinitive verb"
          correct: false
      explanation: "The compound future uses a conjugated form of бути (буду, будеш, etc.) plus the infinitive of the main verb."
    - question: "What does завтра вранці mean?"
      options:
        - text: "tomorrow morning"
          correct: true
        - text: "tomorrow evening"
          correct: false
        - text: "yesterday morning"
          correct: false
        - text: "today morning"
          correct: false
      explanation: "Завтра means tomorrow and вранці means in the morning."
    - question: "How do you correctly say 'next week' in Ukrainian?"
      options:
        - text: "наступного тижня"
          correct: true
        - text: "наступний тиждень"
          correct: false
        - text: "наступне тижня"
          correct: false
        - text: "наступна тиждень"
          correct: false
      explanation: "Time expressions with наступний require the Genitive case — наступного тижня, not the Nominative."
    - question: "Which sentence is CORRECT?"
      options:
        - text: "Я буду читати."
          correct: true
        - text: "Я буду прочитати."
          correct: false
        - text: "Я будеш читати."
          correct: false
        - text: "Я будемо читати."
          correct: false
      explanation: "Буду can only be used with imperfective verbs (читати), not perfective (прочитати). And я takes буду, not будеш or будемо."
    - question: "What does the proverb 'Не кажи гоп, поки не перескочиш' teach?"
      options:
        - text: "Do not celebrate before you have actually succeeded"
          correct: true
        - text: "Always plan your future carefully"
          correct: false
        - text: "Tomorrow is always better than today"
          correct: false
        - text: "Jump as high as you can"
          correct: false
      explanation: "This proverb warns against celebrating success before it actually happens — a cultural note about Ukrainian caution with future plans."
    - question: "Which verb expresses intention rather than certainty about the future?"
      options:
        - text: "збиратися"
          correct: true
        - text: "буду"
          correct: false
        - text: "завтра"
          correct: false
        - text: "потім"
          correct: false
      explanation: "Збиратися (to be going to) expresses intention, while буду + infinitive expresses confident certainty."

- type: match-up
  title: "Match Pronouns to Helper Verbs"
  instruction: "Match each pronoun with the correct future tense helper verb."
  pairs:
    - left: "я"
      right: "буду"
    - left: "ти"
      right: "будеш"
    - left: "він/вона"
      right: "буде"
    - left: "ми"
      right: "будемо"
    - left: "ви"
      right: "будете"
    - left: "вони"
      right: "будуть"

- type: true-false
  title: "True or False? Future Tense Facts"
  instruction: "Decide whether each statement about the Ukrainian future tense is true or false."
  items:
    - statement: "The compound future tense uses a form of бути plus an infinitive verb."
      correct: true
      explanation: "Correct! The formula is буду/будеш/буде/будемо/будете/будуть + infinitive."
    - statement: "You can use буду with perfective verbs like прочитати."
      correct: false
      explanation: "Буду can only be used with imperfective verbs (читати, not прочитати)."
    - statement: "Завтра ввечері means 'tomorrow evening.'"
      correct: true
      explanation: "Завтра means tomorrow and ввечері means in the evening."
    - statement: "To say 'next week,' you should say наступний тиждень."
      correct: false
      explanation: "Time expressions answering 'when?' require the Genitive case: наступного тижня."
    - statement: "Збиратися expresses a definite, certain plan."
      correct: false
      explanation: "Збиратися expresses intention, not certainty. For certainty, use буду + infinitive."
    - statement: "The helper verb changes depending on the subject, but the main verb stays the same."
      correct: true
      explanation: "The helper verb conjugates (буду, будеш, буде, etc.) while the infinitive remains unchanged."
    - statement: "Післязавтра means 'the day after tomorrow.'"
      correct: true
      explanation: "Correct! Після means after and завтра means tomorrow."
    - statement: "Скоро means 'yesterday.'"
      correct: false
      explanation: "Скоро means 'soon.' Yesterday is вчора."

- type: unjumble
  title: "Put the Words in Order"
  instruction: "Arrange the words to form a correct Ukrainian future tense sentence."
  items:
    - words: ["буду", "Я", "читати", "завтра"]
      answer: "Я буду читати завтра"
    - words: ["будемо", "Ми", "дивитися", "фільм"]
      answer: "Ми будемо дивитися фільм"
    - words: ["будеш", "Ти", "працювати", "вранці"]
      answer: "Ти будеш працювати вранці"
    - words: ["буде", "Вона", "готувати", "суп"]
      answer: "Вона буде готувати суп"
    - words: ["будуть", "Вони", "гуляти", "ввечері"]
      answer: "Вони будуть гуляти ввечері"
    - words: ["будете", "Ви", "відпочивати", "скоро"]
      answer: "Ви будете відпочивати скоро"

- type: group-sort
  title: "Sort the Time Expressions"
  instruction: "Sort these Ukrainian words into the correct category."
  groups:
    - name: "Future time markers"
      items: ["завтра", "скоро", "потім", "пізніше", "післязавтра"]
    - name: "Parts of day"
      items: ["вранці", "вдень", "ввечері"]
    - name: "Verbs of intention (not certainty)"
      items: ["хотіти", "збиратися", "мріяти", "планувати"]

- type: fill-in
  title: "Choose the Right Infinitive"
  instruction: "Complete each sentence by choosing the correct infinitive verb."
  items:
    - sentence: "Завтра вранці я буду ___ книгу."
      answer: "читати"
      options: ["читати", "слухати", "гуляти", "спати"]
      explanation: "Читати книгу means to read a book."
    - sentence: "Ми будемо ___ фільм ввечері."
      answer: "дивитися"
      options: ["дивитися", "слухати", "писати", "готувати"]
      explanation: "Дивитися фільм means to watch a movie."
    - sentence: "Вона буде ___ суп на вечерю."
      answer: "готувати"
      options: ["готувати", "читати", "писати", "малювати"]
      explanation: "Готувати суп means to cook/prepare soup."
    - sentence: "Ти будеш ___ музику потім."
      answer: "слухати"
      options: ["слухати", "читати", "робити", "бігати"]
      explanation: "Слухати музику means to listen to music."
    - sentence: "Вони будуть ___ в село наступного тижня."
      answer: "їхати"
      options: ["їхати", "спати", "малювати", "писати"]
      explanation: "Їхати в село means to travel/go to the village."
    - sentence: "Я збираюся ___ завтра."
      answer: "відпочивати"
      options: ["відпочивати", "працювати", "готувати", "бігати"]
      explanation: "Збираюся відпочивати means I am going to rest."
    - sentence: "Він буде ___ листа пізніше."
      answer: "писати"
      options: ["писати", "читати", "слухати", "гуляти"]
      explanation: "Писати листа means to write a letter."
    - sentence: "Ми будемо ___ каву завтра вранці."
      answer: "пити"
      options: ["пити", "їсти", "готувати", "читати"]
      explanation: "Пити каву means to drink coffee."
    - sentence: "Вони будуть ___ в парку ввечері."
      answer: "гуляти"
      options: ["гуляти", "спати", "писати", "читати"]
      explanation: "Гуляти в парку means to walk in the park."
    - sentence: "Ти будеш ___ завтра вдень."
      answer: "працювати"
      options: ["працювати", "спати", "мріяти", "гуляти"]
      explanation: "Працювати means to work."
    - sentence: "Вона буде ___ рано ввечері."
      answer: "спати"
      options: ["спати", "писати", "бігати", "малювати"]
      explanation: "Спати means to sleep."
    - sentence: "Я буду ___ вечерю скоро."
      answer: "готувати"
      options: ["готувати", "дивитися", "слухати", "писати"]
      explanation: "Готувати вечерю means to cook dinner."
    - sentence: "Ви будете ___ картину наступного тижня."
      answer: "малювати"
      options: ["малювати", "читати", "слухати", "готувати"]
      explanation: "Малювати картину means to paint a picture."
    - sentence: "Ми будемо ___ українську щодня."
      answer: "вчити"
      options: ["вчити", "писати", "готувати", "слухати"]
      explanation: "Вчити українську means to study Ukrainian."
    - sentence: "Він буде ___ вранці завтра."
      answer: "бігати"
      options: ["бігати", "спати", "читати", "малювати"]
      explanation: "Бігати means to run/jog."
    - sentence: "Ти будеш ___ подарунок скоро."
      answer: "робити"
      options: ["робити", "читати", "гуляти", "спати"]
      explanation: "Робити подарунок means to make a gift."
    - sentence: "Вони будуть ___ пісню разом."
      answer: "співати"
      options: ["співати", "писати", "читати", "готувати"]
      explanation: "Співати пісню means to sing a song."
    - sentence: "Я хочу ___ нову книгу."
      answer: "читати"
      options: ["читати", "готувати", "малювати", "бігати"]
      explanation: "Хочу читати means I want to read."
    - sentence: "Вона буде ___ подругу завтра."
      answer: "чекати"
      options: ["чекати", "писати", "гуляти", "спати"]
      explanation: "Чекати подругу means to wait for a friend."
    - sentence: "Ви будете ___ план на вечір."
      answer: "складати"
      options: ["складати", "читати", "бігати", "спати"]
      explanation: "Складати план means to make a plan."
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/tomorrow-future-tense.yaml`

```yaml
items:
  - lemma: "завтра"
    translation: "tomorrow"
    pos: "adverb"
    usage: "завтра вранці, завтра вдень, завтра ввечері"
    notes: "High frequency — top 100 word"
  - lemma: "бути"
    translation: "to be (future helper verb)"
    pos: "verb"
    aspect: "imperfective"
    usage: "буду, будеш, буде, будемо, будете, будуть"
    notes: "Conjugated forms serve as the helper verb in compound future tense"
  - lemma: "наступний"
    translation: "next"
    pos: "adjective"
    gender: "m"
    usage: "наступного тижня, наступного року, наступного разу"
    notes: "Requires Genitive case in time expressions"
  - lemma: "план"
    translation: "plan"
    pos: "noun"
    gender: "m"
    usage: "мати плани, складати план, плани на майбутнє"
  - lemma: "хотіти"
    translation: "to want"
    pos: "verb"
    aspect: "imperfective"
    usage: "хочу знати, хочу сказати"
    notes: "Expresses intention, not certainty"
  - lemma: "збиратися"
    translation: "to be going to, to intend"
    pos: "verb"
    aspect: "imperfective"
    usage: "збираюся їхати, збираюся вчити"
    notes: "Expresses intention; also збиратися додому = to get ready to go home"
  - lemma: "скоро"
    translation: "soon"
    pos: "adverb"
    usage: "скоро буду, дуже скоро"
  - lemma: "потім"
    translation: "then, afterwards"
    pos: "adverb"
    usage: "а потім, потім скажу"
    notes: "Used to sequence future actions"
  - lemma: "тиждень"
    translation: "week"
    pos: "noun"
    gender: "m"
    usage: "наступного тижня"
  - lemma: "рік"
    translation: "year"
    pos: "noun"
    gender: "m"
    usage: "наступного року"
  - lemma: "сподіватися"
    translation: "to hope"
    pos: "verb"
    aspect: "imperfective"
    usage: "сподіваюся, що все буде добре"
  - lemma: "мріяти"
    translation: "to dream"
    pos: "verb"
    aspect: "imperfective"
    usage: "мріяти про відпустку"
  - lemma: "планувати"
    translation: "to plan"
    pos: "verb"
    aspect: "imperfective"
    usage: "планувати час, планувати подорож"
  - lemma: "пізніше"
    translation: "later"
    pos: "adverb"
    usage: "трохи пізніше"
  - lemma: "післязавтра"
    translation: "the day after tomorrow"
    pos: "adverb"
    usage: "післязавтра буде свято"
  - lemma: "майбутнє"
    translation: "future"
    pos: "noun"
    gender: "n"
    usage: "плани на майбутнє"
  - lemma: "вечір"
    translation: "evening"
    pos: "noun"
    gender: "m"
    usage: "плани на вечір, завтра ввечері"
  - lemma: "працювати"
    translation: "to work"
    pos: "verb"
    aspect: "imperfective"
    usage: "буду працювати, працювати завтра"
  - lemma: "відпочивати"
    translation: "to rest"
    pos: "verb"
    aspect: "imperfective"
    usage: "буду відпочивати, відпочивати на вихідних"
  - lemma: "готувати"
    translation: "to cook, to prepare"
    pos: "verb"
    aspect: "imperfective"
    usage: "буду готувати суп"
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
- Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/tomorrow-future-tense.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/tomorrow-future-tense.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/tomorrow-future-tense.yaml`

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
