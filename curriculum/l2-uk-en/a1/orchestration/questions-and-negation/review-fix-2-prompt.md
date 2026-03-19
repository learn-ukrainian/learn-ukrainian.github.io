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

## Plan Adherence Issues (Deterministic — MUST FIX)

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥15 items
  - Actual: Activity has 8 items
  - Fix: Add 7 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥15 items
  - Actual: Activity has 10 items
  - Fix: Add 5 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥15 items
  - Actual: Activity has 8 items
  - Fix: Add 7 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥15 items
  - Actual: Activity has 8 items
  - Fix: Add 7 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥20 items
  - Actual: Activity has 8 items
  - Fix: Add 12 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥20 items
  - Actual: Activity has 10 items
  - Fix: Add 10 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥20 items
  - Actual: Activity has 8 items
  - Fix: Add 12 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥20 items
  - Actual: Activity has 8 items
  - Fix: Add 12 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥15 items
  - Actual: Activity has 8 items
  - Fix: Add 7 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥15 items
  - Actual: Activity has 10 items
  - Fix: Add 5 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥15 items
  - Actual: Activity has 8 items
  - Fix: Add 7 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥15 items
  - Actual: Activity has 8 items
  - Fix: Add 7 more items to 'fill-in' activity


---

## Review Findings (targeted fix required)

**CONSTRAINTS:**
- Fix ONLY the issues listed below
- Do NOT rewrite surrounding text
- Preserve word count and structure
- Only modify these sections: Activities file, all activities, Line 150, Line 174, Section "Культурний контекст та ALF (Cultural Context and ALF)", Line 181, Section "З'єднуємо слова та ідеї (Connecting Words and Ideas)", entire section, Vocabulary file lists іноді but it never appears in the content prose

### Finding 1: Missing Plan Content — тому що / бо (HIGH)
**Location**: Section "З'єднуємо слова та ідеї (Connecting Words and Ideas)", entire section
**Problem**: Plan explicitly requires "Causal clauses with тому що / бо (because)" with examples: "Я не йду, тому що я хворий. Він не прийшов, бо холодно." None of this appears anywhere in the content. The section only covers і/й, а, але — omitting the entire causal conjunction subsection. Worse, the summary on line 181 claims 「joining sentences with **але** or **тому що** can instantly elevate your fluency」 — presenting тому що as if it had been taught.
**Required Fix**: Add a subsection after the і/а/але block covering тому що (formal) and бо (colloquial) with 3-4 example sentences. Remove "тому що" from the summary or keep it only after the content actually teaches it.
**Severity**: HIGH

### Finding 2: Wrong ALF Quote (MEDIUM)
**Location**: Line 174, Section "Культурний контекст та ALF (Cultural Context and ALF)"
**Problem**: Plan specifies "Ти не любиш котів? Ти просто не вмієш їх готувати!" which demonstrates BOTH negation AND a rhetorical question — perfectly tying together the module's two core topics. The replacement quote only shows negation with і, missing the question component entirely. The replacement may also be fabricated — this isn't a well-known ALF line.
**Required Fix**: Replace with the plan's ALF quote which is pedagogically superior for this module's scope.
**Severity**: HIGH

### Finding 3: Missing Vocabulary — іноді (MEDIUM)
**Location**: Vocabulary file lists іноді but it never appears in the content prose
**Problem**: Vocabulary item is taught nowhere. Plan objective says "Learner can explain frequency adverbs (завжди, часто, іноді, ніколи)" — іноді is not demonstrated at all.
**Required Fix**: Add іноді to the frequency adverb examples in section "Продукція: Комунікативні сценарії" alongside завжди, часто, ніколи.
**Severity**: HIGH

### Finding 4: Activity Item Shortfall (MEDIUM)
**Location**: Activities file, all activities
**Problem**: Plan specifies 58 items total (15+20+15+8). Only 34 delivered (8+10+8+8). Activities 1-3 are roughly half the specified count. Additionally, Activity 1 "Form Questions with чи" has all 8 items with the same answer ("Чи") — after the first 2 items, the learner is just repeating without thinking.
**Required Fix**: Expand activities 1-3 to match plan counts. For Activity 1, add items where the answer is NOT чи (e.g., question words) to create actual discrimination.
**Severity**: HIGH

### Finding 5: Section Title Mismatch (LOW)
**Location**: Line 150
**Problem**: Plan says "З'єднуємо речення (Joining Sentences)" but content has "З'єднуємо слова та ідеї (Connecting Words and Ideas)". Minor but should match plan.
**Required Fix**: Rename to match plan.
**Severity**: HIGH

### Finding 6: Misleading Summary (MEDIUM)
**Location**: Line 181
**Problem**: The summary claims тому що was covered, but it was never taught in the module. This misleads the learner into thinking they learned something they didn't.
**Required Fix**: Either add тому що content (Issue 1 fix) or remove the reference from the summary.
**Severity**: HIGH

---

## Critical Issues Found

### Issue 1: Missing Plan Content — тому що / бо (HIGH)
- **Location**: Section "З'єднуємо слова та ідеї (Connecting Words and Ideas)", entire section
- **Problem**: Plan explicitly requires "Causal clauses with тому що / бо (because)" with examples: "Я не йду, тому що я хворий. Він не прийшов, бо холодно." None of this appears anywhere in the content. The section only covers і/й, а, але — omitting the entire causal conjunction subsection. Worse, the summary on line 181 claims 「joining sentences with **але** or **тому що** can instantly elevate your fluency」 — presenting тому що as if it had been taught.
- **Fix**: Add a subsection after the і/а/але block covering тому що (formal) and бо (colloquial) with 3-4 example sentences. Remove "тому що" from the summary or keep it only after the content actually teaches it.

### Issue 2: Wrong ALF Quote (MEDIUM)
- **Location**: Line 174, Section "Культурний контекст та ALF (Cultural Context and ALF)"
- **Original**: 「Я не людина, і я не кіт!」
- **Problem**: Plan specifies "Ти не любиш котів? Ти просто не вмієш їх готувати!" which demonstrates BOTH negation AND a rhetorical question — perfectly tying together the module's two core topics. The replacement quote only shows negation with і, missing the question component entirely. The replacement may also be fabricated — this isn't a well-known ALF line.
- **Fix**: Replace with the plan's ALF quote which is pedagogically superior for this module's scope.

### Issue 3: Missing Vocabulary — іноді (MEDIUM)
- **Location**: Vocabulary file lists іноді but it never appears in the content prose
- **Problem**: Vocabulary item is taught nowhere. Plan objective says "Learner can explain frequency adverbs (завжди, часто, іноді, ніколи)" — іноді is not demonstrated at all.
- **Fix**: Add іноді to the frequency adverb examples in section "Продукція: Комунікативні сценарії" alongside завжди, часто, ніколи.

### Issue 4: Activity Item Shortfall (MEDIUM)
- **Location**: Activities file, all activities
- **Problem**: Plan specifies 58 items total (15+20+15+8). Only 34 delivered (8+10+8+8). Activities 1-3 are roughly half the specified count. Additionally, Activity 1 "Form Questions with чи" has all 8 items with the same answer ("Чи") — after the first 2 items, the learner is just repeating without thinking.
- **Fix**: Expand activities 1-3 to match plan counts. For Activity 1, add items where the answer is NOT чи (e.g., question words) to create actual discrimination.

### Issue 5: Section Title Mismatch (LOW)
- **Location**: Line 150
- **Problem**: Plan says "З'єднуємо речення (Joining Sentences)" but content has "З'єднуємо слова та ідеї (Connecting Words and Ideas)". Minor but should match plan.
- **Fix**: Rename to match plan.

### Issue 6: Misleading Summary (MEDIUM)
- **Location**: Line 181
- **Original**: 「joining sentences with **але** or **тому що** can instantly elevate your fluency」
- **Problem**: The summary claims тому що was covered, but it was never taught in the module. This misleads the learner into thinking they learned something they didn't.
- **Fix**: Either add тому що content (Issue 1 fix) or remove the reference from the summary.

---

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 70 | 「Робиш ти працюєш тут?」 | Ти робиш працювати тут? (or another realistic error) | Unrealistic error example |
| 174 | 「Я не людина, і я не кіт!」 | Ти не любиш котів? Ти просто не вмієш їх готувати! | Wrong cultural reference |

---

## Fix Plan to Reach 9/10 (REQUIRED — score is 8.0)

### Pedagogy: 7/10 → 9/10
**What to fix:**
1. Section "З'єднуємо слова та ідеї": Add тому що / бо subsection with 3-4 examples (e.g., "Я не йду, тому що я хворий.", "Він не працює, бо він студент.") — covers missing plan point
2. Line 174: Replace ALF quote with plan's "Ти не любиш котів? Ти просто не вмієш їх готувати!" — demonstrates both negation + question
3. Add іноді to frequency adverb examples in section "Продукція: Комунікативні сценарії" (e.g., "Я іноді читаю, але я ніколи не граю.")
4. Line 181: Fix summary to accurately reflect taught material

**Expected score after fix:** 9/10

### Activities: 7/10 → 9/10
**What to fix:**
1. Expand Activity 1 from 8→15 items, ensuring at least 3-4 items have answers other than "Чи" (mix in question words as distractors where the correct answer varies)
2. Expand Activity 2 from 10→20 items covering all question words including чому and скільки more
3. Expand Activity 3 from 8→15 items, adding double negation (ніколи не) items and тому що/бо sentences
4. Consider adding one non-fill-in activity type for variety

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 8×1.1 + 9×1.2 + 9×1.3 + 9×1.3 + 8×1.0 + 9×1.5) / 8.9
= (13.5 + 8.8 + 10.8 + 11.7 + 11.7 + 8.0 + 13.5) / 8.9
= 78.0 / 8.9 = 8.8/10
```

---

## Audit Failures (from automated re-audit)

```
⚠️ HYDRATION NOTE: Outline sums to 1400, exceeding word_target 1200
🎭 Content gaming violations found: 1
⚠️ [VOCAB_NOT_IN_CONTENT] Only 11/20 (55%) vocabulary words appear in content+activities. Missing: а, але, звідки, коли, куди, не, чи, чому (+1 more)
--- STRICT GATES (Level A1) ---
Pedagogy     ❌ 6 violations
📚 PEDAGOGICAL VIOLATIONS FOUND:
[VOCAB_NOT_IN_CONTENT] Only 11/20 (55%) vocabulary words appear in content+activities. Missing: а, але, звідки, коли, куди, не, чи, чому (+1 more)
→ FIX: Integrate missing vocabulary words into the prose or activities. Each vocab word should appear at least once in context.
📝 RECOMMENDATION: UPDATE (patch fixes) (severity 50/100)
→ Revision recommended (severity 50/100)
→ 7 violations (significant)
→ 6 grammar-level violations (fundamental)
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/questions-and-negation-audit.log for details)
⚠️  RAG verification found unverified words (see audit report)
--- VESUM WORD VERIFICATION FAILURES ---
These words were NOT found in the VESUM morphological dictionary.
Check if they are valid Ukrainian forms. Fix misspellings or Russianisms.
  ❌ `шо` (source: prose)
```

---

## File Contents (for reference)

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/questions-and-negation.md`

```markdown
## Вступ: Основи заперечення та інтонації (Introduction: Basics of Negation and Intonation)

Welcome back! Today we are exploring a fundamental milestone in your Ukrainian journey: asking questions and saying no. You already know how to make basic statements and describe what you or others are doing. Now, we will unlock the power to seek information and express negation.

One of the most beautifully simple aspects of Ukrainian syntax is that we do not use auxiliary verbs to form questions or negatives. In English, you are used to the «do/does» trap: «Do you know?» or «He does not know.» In Ukrainian, this complication simply does not exist! We directly transform a statement into a question, or we simply place a short negative particle before the verb.

Let's start with saying «not». To make any sentence negative in Ukrainian, you just put the particle **не** right before the verb or the word you are negating. It is incredibly straightforward.

However, many learners fall into a common phonetic and functional trap: confusing **не** (not) with **ні** (no). These are two essential words, but they serve different roles. You use **ні** as a standalone answer meaning «no». You use **не** to negate the verb inside the sentence. Often, you will use them together!

*   **Ні, я не знаю.** (No, I don't know.)
*   **Ні, він не працює.** (No, he does not work.)

Another crucial element of asking questions is visualizing the voice. When you ask a simple yes/no question without a question word, your intonation does all the heavy lifting. We use a sharp pitch rise (↗) on the focus word of the question to make it clear we are asking something, not just stating a fact. Contrast this with the natural falling tone (↘) we use at the end of negative statements.

*   **Ти знаєш? ↗** (Do you know?)
*   **Я не знаю. ↘** (I don't know.)

By mastering this rising intonation and the simple **не** particle, you are already halfway to having full conversations!

## Презентація: Питальні конструкції (Presentation: Interrogative Structures)

Now that we understand the basics of intonation and negation, let's look at the standard ways to build interrogative structures.

When you want to ask a direct yes/no question clearly and politely, Ukrainian uses the special question particle **чи**. You can think of **чи** as a clear signal flag at the beginning of a sentence that announces, «A question is coming!» Using **чи** is a marker of politeness, emphasis, or a slightly more formal register. It is especially useful when you want to make absolutely sure you are understood.

*   **Чи ви розумієте?** (Do you understand?)
*   **Чи це твій стіл?** (Is this your table?)
*   **Чи це кава?** (Is this coffee?)

While **чи** is fantastic for clarity, there is a very common spoken alternative: using rising intonation alone. Dropping the **чи** is standard in casual, everyday conversation with friends and family. However, without the particle, you absolutely must use that sharp pitch rise (↗) on the focus word, otherwise, it will just sound like a flat statement.

*   **Ви розумієте? ↗** (Do you understand?)
*   **Ти читаєш? ↗** (Are you reading?)

Beyond simple yes/no questions, you will need a comprehensive set of interrogative words to gather specific information. These words are the keys to having meaningful exchanges. Let's look at the core question words you need to know right now, aligned with the State Standard:

*   **Що** — What — **Що це?** — What is this?
*   **Хто** — Who — **Хто там?** — Who is there?
*   **Де** — Where — **Де ти?** — Where are you?
*   **Коли** — When — **Коли ти вдома?** — When are you at home?
*   **Куди** — Where to — **Куди ви їдете?** — Where are you going to?
*   **Звідки** — From where — **Звідки ти?** — Where are you from?
*   **Як** — How — **Як справи?** — How are things?

A quick cultural note: while **що** is the standard, correct form for «what», you will hear the ubiquitous spoken variant **шо** everywhere in casual settings. It is completely normal, but you should stick to writing **що**.

Finally, let's practice the answering patterns. When someone asks you a question, you can confirm with **так** (yes) or negate with **ні** (no). It is very natural to repeat the verb in your answer.

*   **Чи ти працюєш?** (Do you work?)
*   **Так, я працюю.** (Yes, I work.)
*   **Ні, я не працюю.** (No, I don't work.)

## Практика: Тренування заперечень та запитань (Practice: Drilling Negation and Questions)

Let's put this theory into practice. The best way to build your syntactic intuition is through sentence transformation drills. We are going to take simple positive statements, turn them into negative statements, and finally transform them into interrogative forms. Notice how the word order remains largely exactly the same!

**Transformation Pattern 1: Knowing**
*   **Ти знаєш.** (You know.)
*   **Ти не знаєш.** (You do not know.)
*   **Чи ти знаєш?** (Do you know?)

**Transformation Pattern 2: Reading**
*   **Вона читає.** (She reads.)
*   **Вона не читає.** (She does not read.)
*   **Чи вона читає?** (Does she read?)

Now, let's enter the error correction lab. When English speakers first start asking questions in Ukrainian, they often try to force English grammar rules where they do not belong. Remember the «do/does» trap? Let's fix some common English-transfer errors.

Imagine a learner wants to ask «Do you work here?». They might try to say something like: «Робиш ти працюєш тут?» This is completely wrong because they are trying to translate «do» literally. The correct, elegant Ukrainian way is simply:
*   **Чи ти працюєш тут?** (Do you work here?)

Another common mistake is using flat intonation patterns. If you say «Ти працюєш тут ↘» with a falling tone, people will think you are just making an observation. You must lift your voice: **Ти працюєш тут? ↗**

> 💡 **Корисні фрази для практики — Useful phrases for practice**
> Read these out loud to practice your intonation and rhythm. Notice the negative particle **не** and the question particle **чи**.
>
> **Вдома (At home):**
> — Де ти? Ти вдома?
> — Так, я вдома. А ти де?
> — Я не вдома. Я працюю.
> — Що це? Це чай?
> — Ні, це не чай. Це вода. Я не люблю чай.
> — Чи ти читаєш?
> — Ні, я не читаю. Я працюю.
>
> **На вулиці (On the street):**
> — Хто це? Це твій брат?
> — Ні, це не мій брат. Це мій друг.
> — Куди ви йдете? Ви йдете в парк?
> — Ні, ми не йдемо в парк. Ми йдемо в місто.
> — Хто ви? Ви студент?
> — Так, я студент. А ви хто?
> — Я не студент. Я турист.
> — Де тут кав'ярня?
> — Кав'ярня там.

Finally, let's do a mental matching exercise to pair question words with situational answers. This helps cement the meaning of words like **хто**, **що**, **де**, and **куди**.
*   Answer: **Я вдома.** — I am at home. Question: **Де?** — Where?
*   Answer: **Це мій брат.** — This is my brother. Question: **Хто це?** — Who is this?
*   Answer: **Я їду в місто.** — I am going to the city. Question: **Куди?** — Where to?
*   Answer: **Це книга.** — This is a book. Question: **Що це?** — What is this?

> [!example] Listening Comprehension
> Watch this video to hear Olha use question words like **що** and the negation **не** naturally while talking about food.
> <iframe width="560" height="315" src="https://www.youtube.com/embed/QE9JOcQfLE0" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

## Продукція: Комунікативні сценарії (Production: Communicative Scenarios)

It is time to step out into the real world and use your new skills in communicative scenarios. Imagine you are walking into a bustling Ukrainian café. You need to ask questions about the menu, check for availability, and ask about prices. The vocabulary you have learned so far is perfect for this.

Here are some essential questions for the Café Scenario:
*   **Де кава?** (Where is the coffee?)
*   **Скільки це коштує?** (How much does this cost?)
*   **Чи є цукор?** (Is there sugar?)
*   **Що ви любите?** (What do you like?)

Notice how we use the new question word **скільки** (how much / how many). It is incredibly useful whenever you are shopping or ordering food.

Next, let's try a roleplay exercise: «The Investigative Journalist». Imagine you are a reporter trying to uncover basic facts about a mysterious new person. You can use your checklist of question words to interview them. You could ask:
*   **Хто ви?** (Who are you?)
*   **Звідки ви?** (Where are you from?)
*   **Де ви працюєте?** (Where do you work?)
*   **Чому ви тут?** (Why are you here?)

When answering these investigative questions, you will often need to use negative responses combined with frequency adverbs. Ukrainian uses a wonderful double negation structure when you want to say you «never» do something. You combine **ніколи** (never) with the negative particle **не**.

*   **Ні, я ніколи не читаю.** (No, I never read.)
*   **Я ніколи не працюю там.** (I never work there.)

You can also use other frequency words like **завжди** (always) and **часто** (often) to contrast with your negative statements.

*   **Я часто читаю, але я ніколи не граю.** (I often read, but I never play.)
*   **Він завжди тут.** (He is always here.)
*   **Я іноді працюю тут.** (I sometimes work here.)

Practicing these scenarios will make your conversational skills feel much more authentic and spontaneous!

> 🎬 **Міні-діалог (Mini-dialogue)**
>
> — Привіт! Як справи?
> — Привіт! Добре. А ти як?
> — Теж добре. Ти працюєш тут?
> — Ні, я не працюю тут. Я студент. А ти?
> — Я працюю. Це мій стіл.
> — Добре, дякую! Де кава?
> — Кава там.
> — Що це? Це чай?
> — Ні, це не чай. Це вода.

## З'єднуємо речення (Joining Sentences)

Asking questions and giving short answers is great, but to truly sound fluent, you need to start connecting your thoughts together. We can link simple ideas into more expressive pairs using basic conjunctions. This allows you to build a flow and connect related actions. This is perfectly aligned with the State Standard expectations for this early level.

Let's look at the core conjunctions: **і / й** (and), **а** (and/but - indicating contrast), and **але** (but). The pattern is beautifully simple. You can use them to join two words, or you can start a new sentence with them to connect it to the previous thought. The word order inside each of your simple sentences does not change at all. You just use the connector to bridge the gap!

*   **Тут є кава і чай.** (There is coffee and tea here.)
*   **Це мій брат. А хто це?** (This is my brother. And who is this?)
*   **Я читаю. Але я не граю.** (I read. But I do not play.)

We also need to emphasize the difference between **і** and **а**. Use **і** when you are just adding things together without any contrast. Use **а** when you are contrasting two different things or asking a follow-up question about a different subject. The word **але** is a stronger contrast, like "but" in English.

*   **Він тут. І вона тут.** (He is here. And she is here.)
*   **Він тут. А де вона?** (He is here. And where is she?)
*   **Він тут. Але вона не тут.** (He is here. But she is not here.)

By linking your words and sentences with these simple conjunctions, your Ukrainian immediately becomes richer, more mature, and much more natural for native speakers to listen to.

We also need to learn how to explain the reason for something. Ukrainian uses **тому що** (because — neutral/formal) and **бо** (because — colloquial). The pattern is the same: your sentence stays the same, you just connect it to the reason.

*   **Я не йду, тому що я хворий.** (I'm not going because I'm sick.)
*   **Він не працює, бо він студент.** (He doesn't work because he is a student.)
*   **Я вдома, тому що я не працюю.** (I'm at home because I'm not working.)
*   **Вона не читає, бо вона працює.** (She doesn't read because she is working.)

Use **тому що** in writing and formal speech. Use **бо** with friends and family — it is shorter and very natural.

## Культурний контекст та ALF (Cultural Context and ALF)

Understanding when to use different question forms is an important part of Ukrainian social etiquette. Register nuances matter. When you are speaking with older individuals, teachers, or in a professional environment, using the formal **чи** is highly recommended. It shows respect and ensures your standard, polite tone is clearly understood. However, if you are grabbing coffee with friends or chatting at a casual gathering, dropping the **чи** and relying entirely on your conversational intonation-only questions is exactly what native speakers do.

To truly appreciate Ukrainian rhetorical intonation and our touch of humor, we have to look at pop culture. The television show ALF was famously dubbed into Ukrainian in the 1990s, and its brilliant translation is still culturally iconic today. There is a legendary style that perfectly demonstrates simple negation:

*   **Ти не любиш котів? Ти просто не вмієш їх готувати!** (You don't like cats? You just don't know how to cook them!)

This iconic line perfectly demonstrates both a negative question and a negative statement in one humorous exchange, tying together everything you have learned in this module.

# Підсумок
You have done a phenomenal job tackling questions and negation! This module has equipped you with some of the most powerful tools for everyday communication. You have learned that Ukrainian avoids the complicated English «do/does» auxiliary system, relying instead on simple intonation and straightforward particles.

We explored how to form polite, formal questions using **чи**, and how to ask casual questions using just a sharp rising pitch. You mastered the essential difference between the negative particle **не** inside a sentence and the standalone answer **ні**. We also covered the critical question words—like **що**, **хто**, **де**, and **коли**—and saw how joining sentences with **але**, **тому що**, and **бо** can instantly elevate your fluency.

**Self-Check Questions:**
1. Where do you place the negative particle **не** in a Ukrainian sentence?
2. What is the difference between **не** and **ні**?
3. How do you turn a statement into a casual question without using **чи**?
4. What is the difference between the conjunctions **і**, **а**, and **але**?

Keep practicing these patterns, and you will find yourself navigating conversations with increasing confidence!
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/questions-and-negation.yaml`

```yaml
- type: fill-in
  title: "Form Questions with чи"
  instruction: "Add the correct question particle or word to form a proper yes/no question."
  items:
    - sentence: "___ ти працюєш тут?"
      answer: "Чи"
      options: ["Чи", "Що", "Де", "Як"]
      explanation: "Чи is the question particle used to form polite yes/no questions."
    - sentence: "___ це твій стіл?"
      answer: "Чи"
      options: ["Чи", "Хто", "Куди", "Коли"]
      explanation: "Чи marks a yes/no question — here asking whether this is your table."
    - sentence: "___ ви розумієте?"
      answer: "Чи"
      options: ["Чи", "Що", "Де", "Чому"]
      explanation: "Чи ви розумієте? is the polite way to ask Do you understand?"
    - sentence: "___ вона читає?"
      answer: "Чи"
      options: ["Чи", "Як", "Куди", "Скільки"]
      explanation: "Чи turns a statement (Вона читає) into a polite yes/no question."
    - sentence: "___ це кава?"
      answer: "Чи"
      options: ["Чи", "Хто", "Звідки", "Коли"]
      explanation: "Чи це кава? asks Is this coffee? — a standard yes/no question."
    - sentence: "___ є цукор?"
      answer: "Чи"
      options: ["Чи", "Де", "Що", "Як"]
      explanation: "Чи є цукор? asks Is there sugar? — using чи for a polite question."
    - sentence: "___ він знає?"
      answer: "Чи"
      options: ["Чи", "Хто", "Куди", "Скільки"]
      explanation: "Чи він знає? is the formal way to ask Does he know?"
    - sentence: "___ ти любиш каву?"
      answer: "Чи"
      options: ["Чи", "Що", "Де", "Коли"]
      explanation: "Чи ти любиш каву? politely asks Do you like coffee?"
    - sentence: "___ це? — Це мій стіл."
      answer: "Що"
      options: ["Що", "Чи", "Де", "Як"]
      explanation: "Що це? asks What is this? — not a yes/no question, so чи is wrong here."
    - sentence: "___ ви їдете? — Ми їдемо в місто."
      answer: "Куди"
      options: ["Куди", "Чи", "Що", "Хто"]
      explanation: "Куди asks where to — this needs a question word, not the yes/no particle чи."
    - sentence: "___ він студент?"
      answer: "Чи"
      options: ["Чи", "Хто", "Де", "Куди"]
      explanation: "Чи він студент? is a polite yes/no question — Is he a student?"
    - sentence: "___ там? — Там мій друг."
      answer: "Хто"
      options: ["Хто", "Чи", "Що", "Де"]
      explanation: "Хто там? asks Who is there? — a question word, not a yes/no particle."
    - sentence: "___ ви розумієте мене?"
      answer: "Чи"
      options: ["Чи", "Як", "Що", "Хто"]
      explanation: "Чи ви розумієте мене? politely asks Do you understand me?"
    - sentence: "___ ти? — Я вдома."
      answer: "Де"
      options: ["Де", "Чи", "Що", "Коли"]
      explanation: "Де ти? asks Where are you? — the answer gives a location, so we need де."
    - sentence: "___ вона вдома?"
      answer: "Чи"
      options: ["Чи", "Де", "Хто", "Що"]
      explanation: "Чи вона вдома? asks Is she at home? — a yes/no question using чи."

- type: fill-in
  title: "Complete with Question Words"
  instruction: "Choose the correct question word to complete each sentence."
  items:
    - sentence: "___ це? — Це книга."
      answer: "Що"
      options: ["Що", "Хто", "Де", "Куди"]
      explanation: "Що means what — Що це? asks What is this?"
    - sentence: "___ там? — Там мій брат."
      answer: "Хто"
      options: ["Хто", "Що", "Коли", "Як"]
      explanation: "Хто means who — Хто там? asks Who is there?"
    - sentence: "___ ти? — Я вдома."
      answer: "Де"
      options: ["Де", "Хто", "Що", "Куди"]
      explanation: "Де means where — the answer Я вдома (I am at home) tells location."
    - sentence: "___ ти вдома? — Я завжди вдома."
      answer: "Коли"
      options: ["Коли", "Де", "Куди", "Як"]
      explanation: "Коли means when — the answer uses завжди (always), indicating time."
    - sentence: "___ ви їдете? — Ми їдемо в місто."
      answer: "Куди"
      options: ["Куди", "Де", "Звідки", "Коли"]
      explanation: "Куди means where to — asking about a destination."
    - sentence: "___ ти? — Я з Києва."
      answer: "Звідки"
      options: ["Звідки", "Куди", "Де", "Коли"]
      explanation: "Звідки means from where — asking about origin."
    - sentence: "___ справи? — Добре, дякую."
      answer: "Як"
      options: ["Як", "Що", "Хто", "Де"]
      explanation: "Як means how — Як справи? is How are things?"
    - sentence: "___ це коштує? — Це коштує багато."
      answer: "Скільки"
      options: ["Скільки", "Що", "Як", "Де"]
      explanation: "Скільки means how much — asking about price or quantity."
    - sentence: "___ ви тут? — Я студент."
      answer: "Чому"
      options: ["Чому", "Як", "Де", "Хто"]
      explanation: "Чому means why — asking the reason for being here."
    - sentence: "___ це? — Це мій друг."
      answer: "Хто"
      options: ["Хто", "Що", "Де", "Куди"]
      explanation: "Хто це? asks Who is this? — the answer identifies a person."
    - sentence: "___ ви працюєте? — Я працюю в місті."
      answer: "Де"
      options: ["Де", "Куди", "Коли", "Хто"]
      explanation: "Де asks where — the answer tells a location (в місті)."
    - sentence: "___ це коштує? — Це коштує мало."
      answer: "Скільки"
      options: ["Скільки", "Що", "Де", "Як"]
      explanation: "Скільки means how much — asking about price."
    - sentence: "___ ти не працюєш? — Я студент."
      answer: "Чому"
      options: ["Чому", "Де", "Коли", "Хто"]
      explanation: "Чому means why — asking the reason."
    - sentence: "___ вона? — Вона вдома."
      answer: "Де"
      options: ["Де", "Хто", "Що", "Куди"]
      explanation: "Де means where — the answer Вона вдома tells location."
    - sentence: "___ ви їдете? — Ми їдемо в парк."
      answer: "Куди"
      options: ["Куди", "Де", "Звідки", "Як"]
      explanation: "Куди asks where to — asking about destination."
    - sentence: "___ він? — Він з Києва."
      answer: "Звідки"
      options: ["Звідки", "Де", "Куди", "Коли"]
      explanation: "Звідки means from where — asking about origin."
    - sentence: "___ ти робиш? — Я читаю."
      answer: "Що"
      options: ["Що", "Хто", "Де", "Як"]
      explanation: "Що means what — Що ти робиш? asks What are you doing?"
    - sentence: "___ це? — Це вода."
      answer: "Що"
      options: ["Що", "Хто", "Де", "Скільки"]
      explanation: "Що це? asks What is this? — the answer identifies a thing (вода)."
    - sentence: "___ ви? — Я турист."
      answer: "Хто"
      options: ["Хто", "Де", "Звідки", "Куди"]
      explanation: "Хто ви? asks Who are you? — asking about identity."
    - sentence: "___ ти вдома? — Я завжди вдома ввечері."
      answer: "Коли"
      options: ["Коли", "Де", "Як", "Чому"]
      explanation: "Коли means when — the answer tells time (завжди ввечері — always in the evening)."

- type: fill-in
  title: "Make Sentences Negative"
  instruction: "Choose the correct negative word to complete each sentence."
  items:
    - sentence: "Я ___ знаю."
      answer: "не"
      options: ["не", "ні", "так", "чи"]
      explanation: "Не is the negation particle placed before the verb: Я не знаю (I don't know)."
    - sentence: "___, я ___ працюю."
      answer: "не"
      options: ["не", "ні", "так", "чи"]
      explanation: "Ні is the standalone no, but не goes before the verb: Ні, я не працюю."
    - sentence: "Вона ___ читає."
      answer: "не"
      options: ["не", "ні", "так", "але"]
      explanation: "Не goes directly before the verb: Вона не читає (She does not read)."
    - sentence: "Це ___ чай. Це вода."
      answer: "не"
      options: ["не", "ні", "так", "чи"]
      explanation: "Не negates the noun here: Це не чай (This is not tea)."
    - sentence: "Він ___ студент. Він турист."
      answer: "не"
      options: ["не", "ні", "але", "так"]
      explanation: "Не negates the word that follows: Він не студент (He is not a student)."
    - sentence: "Я ніколи ___ граю."
      answer: "не"
      options: ["не", "ні", "так", "чи"]
      explanation: "Double negation is required: ніколи + не. Я ніколи не граю (I never play)."
    - sentence: "Ми ___ йдемо в парк."
      answer: "не"
      options: ["не", "ні", "так", "але"]
      explanation: "Не before the verb: Ми не йдемо в парк (We are not going to the park)."
    - sentence: "___, дякую. Я ___ хочу."
      answer: "не"
      options: ["не", "ні", "так", "чи"]
      explanation: "Ні starts the refusal, then не negates the verb: Ні, дякую. Я не хочу."
    - sentence: "Вона ніколи ___ працює тут."
      answer: "не"
      options: ["не", "ні", "так", "але"]
      explanation: "Double negation: ніколи + не. Вона ніколи не працює тут (She never works here)."
    - sentence: "Я ___ йду, тому що я хворий."
      answer: "не"
      options: ["не", "ні", "так", "чи"]
      explanation: "Не negates the verb: Я не йду (I'm not going) — тому що gives the reason."
    - sentence: "Він ___ читає, бо він працює."
      answer: "не"
      options: ["не", "ні", "але", "так"]
      explanation: "Не before the verb: Він не читає (He doesn't read) — бо explains why."
    - sentence: "Це ___ мій стіл. Це його стіл."
      answer: "не"
      options: ["не", "ні", "так", "чи"]
      explanation: "Не negates the possessive: Це не мій стіл (This is not my table)."
    - sentence: "Я ніколи ___ їду в місто."
      answer: "не"
      options: ["не", "ні", "так", "але"]
      explanation: "Double negation is required: ніколи + не. Я ніколи не їду в місто (I never go to the city)."
    - sentence: "Ми ___ студенти. Ми туристи."
      answer: "не"
      options: ["не", "ні", "але", "так"]
      explanation: "Не negates the noun: Ми не студенти (We are not students)."
    - sentence: "Вона ___ вдома, бо вона працює."
      answer: "не"
      options: ["не", "ні", "так", "чи"]
      explanation: "Не negates the location: Вона не вдома (She is not at home) — бо gives the reason."

- type: fill-in
  title: "Question-Answer Pairs"
  instruction: "Choose the correct response to each question."
  items:
    - sentence: "Чи ти працюєш? — ___, я працюю."
      answer: "Так"
      options: ["Так", "Ні", "Не", "Чи"]
      explanation: "Так means yes — confirming that you work."
    - sentence: "Чи це кава? — ___, це не кава. Це чай."
      answer: "Ні"
      options: ["Ні", "Так", "Не", "Але"]
      explanation: "Ні means no — denying that it is coffee."
    - sentence: "Де ти? — Я ___."
      answer: "вдома"
      options: ["вдома", "завжди", "часто", "ніколи"]
      explanation: "Де asks where — вдома (at home) answers the location."
    - sentence: "Хто це? — Це мій ___."
      answer: "брат"
      options: ["брат", "парк", "стіл", "місто"]
      explanation: "Хто asks who — брат (brother) is a person, matching the question."
    - sentence: "Що це? — Це ___."
      answer: "книга"
      options: ["книга", "друг", "студент", "турист"]
      explanation: "Що asks what — книга (book) is a thing, not a person."
    - sentence: "Чи ти читаєш? — Ні, я ___ читаю."
      answer: "не"
      options: ["не", "ні", "так", "завжди"]
      explanation: "After ні, use не before the verb to negate: я не читаю."
    - sentence: "Як справи? — ___, дякую."
      answer: "Добре"
      options: ["Добре", "Ні", "Не", "Чи"]
      explanation: "Добре (good/fine) is the standard reply to Як справи?"
    - sentence: "Куди ви їдете? — Ми їдемо в ___."
      answer: "місто"
      options: ["місто", "завжди", "часто", "ніколи"]
      explanation: "Куди asks where to — місто (city) is a destination."
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/questions-and-negation.yaml`

```yaml
items:
  - lemma: "чи"
    translation: "question particle (marks yes/no questions)"
    pos: "particle"
    usage: "Чи ти працюєш? Чи це кава?"
    notes: "Polite/formal question marker; can be omitted in casual speech"
  - lemma: "що"
    translation: "what"
    pos: "pronoun"
    usage: "Що це? Що ти робиш?"
    notes: "Spoken variant шо is common but not standard in writing"
  - lemma: "хто"
    translation: "who"
    pos: "pronoun"
    usage: "Хто це? Хто там?"
  - lemma: "де"
    translation: "where"
    pos: "adverb"
    usage: "Де ти? Де кава?"
  - lemma: "коли"
    translation: "when"
    pos: "adverb"
    usage: "Коли сніданок? Коли ти вдома?"
  - lemma: "куди"
    translation: "where to"
    pos: "adverb"
    usage: "Куди ви їдете?"
  - lemma: "звідки"
    translation: "from where"
    pos: "adverb"
    usage: "Звідки ти?"
  - lemma: "чому"
    translation: "why"
    pos: "adverb"
    usage: "Чому ти тут? Чому ні?"
  - lemma: "як"
    translation: "how"
    pos: "adverb"
    usage: "Як справи? Як це?"
  - lemma: "скільки"
    translation: "how much / how many"
    pos: "adverb"
    usage: "Скільки це коштує?"
  - lemma: "не"
    translation: "not (negation particle)"
    pos: "particle"
    usage: "Я не знаю. Він не працює."
    notes: "Always placed directly before the word being negated"
  - lemma: "ні"
    translation: "no"
    pos: "particle"
    usage: "Ні, дякую. Ні, я не хочу."
    notes: "Standalone answer; do not confuse with не (negation inside sentence)"
  - lemma: "так"
    translation: "yes"
    pos: "adverb"
    usage: "Так, я працюю. Так, звичайно."
  - lemma: "завжди"
    translation: "always"
    pos: "adverb"
    usage: "Я завжди тут."
  - lemma: "часто"
    translation: "often"
    pos: "adverb"
    usage: "Я часто читаю."
  - lemma: "іноді"
    translation: "sometimes"
    pos: "adverb"
    usage: "Я іноді граю."
  - lemma: "ніколи"
    translation: "never"
    pos: "adverb"
    usage: "Я ніколи не читаю."
    notes: "Requires double negation: ніколи + не"
  - lemma: "але"
    translation: "but"
    pos: "conjunction"
    usage: "Я читаю, але я не граю."
  - lemma: "і"
    translation: "and"
    pos: "conjunction"
    usage: "Тут є кава і чай."
    notes: "Use й after vowels for euphony"
  - lemma: "а"
    translation: "and/but (contrast)"
    pos: "conjunction"
    usage: "Це мій брат. А хто це?"
    notes: "Indicates contrast or shift of subject, unlike і which just adds"
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
- Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/questions-and-negation.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/questions-and-negation.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/questions-and-negation.yaml`

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
