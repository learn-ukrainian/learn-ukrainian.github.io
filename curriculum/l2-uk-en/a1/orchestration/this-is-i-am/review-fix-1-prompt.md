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



**NOTE: 3 inline fix(es) from the review have ALREADY been applied to the files. Do NOT re-apply those fixes. Read the CURRENT file contents carefully — they reflect the post-fix state. Only fix issues that are still present in the current files.**

## Plan Adherence Issues (Deterministic — MUST FIX)

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥15 items
  - Actual: Activity has 6 items
  - Fix: Add 9 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥15 items
  - Actual: Activity has 6 items
  - Fix: Add 9 more items to 'fill-in' activity


---

## Review Findings (targeted fix required)

**CONSTRAINTS:**
- Fix ONLY the issues listed below
- Do NOT rewrite surrounding text
- Preserve word count and structure
- Only modify these sections: Activities file, all 3 activities (lines 1, 30, 95), Line 19 / Section "Вступ: Хто це? Що це? (Introduction: Who is this? What is this?)", Line 45 / Section "Презентація: Особові займенники (Presentation: Personal Pronouns)", Lines 120-129 / Section "Продакшн: Хто я і Хто ви? (Production: Who am I and Who are you?)"

### Finding 1: Missing "Давай на ти?" Ukrainian phrase (MEDIUM)
**Location**: Line 45 / Section "Презентація: Особові займенники (Presentation: Personal Pronouns)"
**Problem**: The plan explicitly includes the phrase "Давай на ти?" as a teachable expression for the Bruderschaft/register-shift concept. The content describes the concept entirely in English without giving learners the actual Ukrainian words they would hear or use. This is a missed vocabulary opportunity — learners will encounter this phrase in real life.
**Required Fix**: Add the Ukrainian phrase **"Давай на ти?"** (Shall we use ти?) after "A person might smile and suggest switching to the informal register" — e.g., "A person might smile and say **«Давай на ти?»** (Shall we switch to ти?)."
**Severity**: HIGH

### Finding 2: Activity type monotony — all fill-in (MEDIUM)
**Location**: Activities file, all 3 activities (lines 1, 30, 95)
**Problem**: All 27 activity items are fill-in type. While this matches the plan's activity_hints (which specify fill-in for all three), it creates a monotonous practice experience. No match-up for pronoun↔gender pairing, no quiz for хто/що distinction, no ordering activity for dialogue reconstruction.
**Required Fix**: This is a plan-level issue. For a future plan revision, suggest replacing one fill-in with a match-up (matching nouns to correct pronouns він/вона/воно) or a quiz (хто vs що scenarios).
**Severity**: HIGH

### Finding 3: Folk riddle attribution (LOW)
**Location**: Line 19 / Section "Вступ: Хто це? Що це? (Introduction: Who is this? What is this?)"
**Problem**: The research notes give a different example for this folk pattern: *«Хто це? — Мій друг. Що це? — Мій підручник.»* The content's version (「Хто це? — Це мій брат. Що це? — Це моя книга.」) appears to be a generated paraphrase presented as authentic tradition. The structural pattern is genuine, but the specific example should match research or be presented as "following the pattern of" rather than "mirrors."
**Required Fix**: Change wording from "mirrors the folk riddles" to "follows the same pattern as traditional Ukrainian question games" — or use the research notes' example.
**Severity**: HIGH

### Finding 4: Passive extended dialogue (LOW)
**Location**: Lines 120-129 / Section "Продакшн: Хто я і Хто ви? (Production: Who am I and Who are you?)"
**Problem**: The extended roleplay dialogue is a fully completed conversation the learner reads passively. In a Production section, the learner should be constructing responses, not observing a pre-built dialogue. This is a presentation choice — the dialogue itself is well-constructed (「Вони мої друзі. Ми всі тут.」 nicely demonstrates plural pronouns + zero copula), but it would be stronger as a gapped exercise.
**Required Fix**: Add a brief prompt before the dialogue: "Try to predict each answer before reading it" — or convert 2-3 responses to blanks for the learner to fill.
**Severity**: HIGH

---

## Critical Issues Found

### Issue 1: Missing "Давай на ти?" Ukrainian phrase (MEDIUM)
- **Location**: Line 45 / Section "Презентація: Особові займенники (Presentation: Personal Pronouns)"
- **Original**: "A person might smile and suggest switching to the informal register."
- **Problem**: The plan explicitly includes the phrase "Давай на ти?" as a teachable expression for the Bruderschaft/register-shift concept. The content describes the concept entirely in English without giving learners the actual Ukrainian words they would hear or use. This is a missed vocabulary opportunity — learners will encounter this phrase in real life.
- **Fix**: Add the Ukrainian phrase **"Давай на ти?"** (Shall we use ти?) after "A person might smile and suggest switching to the informal register" — e.g., "A person might smile and say **«Давай на ти?»** (Shall we switch to ти?)."

### Issue 2: Activity type monotony — all fill-in (MEDIUM)
- **Location**: Activities file, all 3 activities (lines 1, 30, 95)
- **Problem**: All 27 activity items are fill-in type. While this matches the plan's activity_hints (which specify fill-in for all three), it creates a monotonous practice experience. No match-up for pronoun↔gender pairing, no quiz for хто/що distinction, no ordering activity for dialogue reconstruction.
- **Fix**: This is a plan-level issue. For a future plan revision, suggest replacing one fill-in with a match-up (matching nouns to correct pronouns він/вона/воно) or a quiz (хто vs що scenarios).

### Issue 3: Folk riddle attribution (LOW)
- **Location**: Line 19 / Section "Вступ: Хто це? Що це? (Introduction: Who is this? What is this?)"
- **Original**: "It mirrors the folk riddles of Ukrainian children's tradition: *«Хто це? — Це мій брат. Що це? — Це моя книга.»*"
- **Problem**: The research notes give a different example for this folk pattern: *«Хто це? — Мій друг. Що це? — Мій підручник.»* The content's version (「Хто це? — Це мій брат. Що це? — Це моя книга.」) appears to be a generated paraphrase presented as authentic tradition. The structural pattern is genuine, but the specific example should match research or be presented as "following the pattern of" rather than "mirrors."
- **Fix**: Change wording from "mirrors the folk riddles" to "follows the same pattern as traditional Ukrainian question games" — or use the research notes' example.

### Issue 4: Passive extended dialogue (LOW)
- **Location**: Lines 120-129 / Section "Продакшн: Хто я і Хто ви? (Production: Who am I and Who are you?)"
- **Problem**: The extended roleplay dialogue is a fully completed conversation the learner reads passively. In a Production section, the learner should be constructing responses, not observing a pre-built dialogue. This is a presentation choice — the dialogue itself is well-constructed (「Вони мої друзі. Ми всі тут.」 nicely demonstrates plural pronouns + zero copula), but it would be stronger as a gapped exercise.
- **Fix**: Add a brief prompt before the dialogue: "Try to predict each answer before reading it" — or convert 2-3 responses to blanks for the learner to fill.

---

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| — | No Ukrainian language errors found | — | — |

All Ukrainian sentences verified via VESUM batch check. Grammar is correct throughout. Gender agreement, pronoun selection, and zero copula patterns are all accurate.

---

## Fix Plan to Reach 9/10 (REQUIRED — score is 8.3)

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Line 45: Add **«Давай на ти?»** as a taught Ukrainian phrase — currently the register shift concept is described only in English
2. Lines 120-129: Add a learner engagement prompt before the extended dialogue (e.g., "Try to predict each answer before reading it")

**Expected score after fix:** 9/10

### Pedagogy: 8/10 → 9/10
**What to fix:**
1. Same as Experience fix #1 — teaching the actual Ukrainian phrase improves pedagogical value
2. Line 19: Soften folk riddle attribution from "mirrors the folk riddles" to "follows the same pattern as traditional Ukrainian question games"

**Expected score after fix:** 9/10

### Activities: 7/10 → 8/10
**What to fix:**
1. This is plan-constrained (plan specifies all fill-in). No content-level fix possible without plan revision. Recommend plan revision to add one match-up activity in future.

**Expected score after fix:** 8/10 (plan-constrained ceiling)

### Projected Overall After Fixes
```
(9×1.5 + 9×1.1 + 9×1.2 + 8×1.3 + 9×1.3 + 8×1.0 + 9×1.5) / 8.9
= (13.5 + 9.9 + 10.8 + 10.4 + 11.7 + 8.0 + 13.5) / 8.9
= 77.8 / 8.9 = 8.7/10
```

---

## Audit Failures (from automated re-audit)

```
⚠️ HYDRATION NOTE: Outline sums to 1350, exceeding word_target 1200
Робота над помилками та практика (Error Correction and Practice)       260 /  200  ✅ (+60)
--- STRICT GATES (Level A1) ---
📚 PEDAGOGICAL VIOLATIONS FOUND:
📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
→ 1 violations (minor)
⚠️  [SCORE_DRIFT_OUTLIER] Review mean score (8.3) is a 2σ outlier above track average (7.2 ± 0.4). This may indicate rubber-stamping. Re-examine scores critically.
⚠️  RAG verification found unverified words (see audit report)
--- VESUM WORD VERIFICATION FAILURES ---
These words were NOT found in the VESUM morphological dictionary.
Check if they are valid Ukrainian forms. Fix misspellings or Russianisms.
  ❌ `Анна` (source: prose)
  ❌ `Марк` (source: prose)
  ❌ `Ірина` (source: prose)
```

---

## File Contents (for reference)

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/this-is-i-am.md`

```markdown
## Вступ: Хто це? Що це? (Introduction: Who is this? What is this?)

Welcome back! So far, you have mastered reading the Ukrainian alphabet and understanding the beautiful three-gender system of our nouns. You already know quite a few words for people, animals, and everyday objects. But language is all about connection and communication. Today, we are taking a massive leap forward. We are going to start building actual sentences to talk about who we are and what is around us. 

When you look at the world around you, your first instinct is to identify things. Children learn their first words by pointing and asking what things are. In Ukrainian, this foundational skill is incredibly straightforward and built on a very simple pattern. We use the demonstrative word **це** (this is) to point out anything or anyone. Let's look at some simple identification sentences following the Ukrainian State Standard:

* **Це Ірина.** (This is Iryna.)
* **Це підручник.** (This is a textbook.)
* **Це новий телевізор.** (This is a new television.)

Notice how easy that is! You just say **це** and add the noun. But how do we ask the questions to get these answers? Ukrainian makes a strict distinction between people and things, between the living and the inanimate. 

When you want to identify a person, you use the question word **хто** (who). 
* **Хто це?** (Who is this?)

When you are identifying an object, an animal, or a concept, you use the question word **що** (what).
* **Що це?** (What is this?)

This pattern focus—identifying people with **хто** versus objects with **що** using the demonstrative **це**—is your absolute foundation. It follows the same pattern as traditional Ukrainian question games: *«Хто це? — Це мій брат. Що це? — Це моя книга.»*

But what if you want to introduce yourself? Naming yourself in Ukrainian uses a special, fixed phrase. While in English you say "My name is", the Ukrainian concept of naming is slightly different. We say:
* **Мене звати...** (They call me... / My name is...)

For example, **Мене звати Іван** means "My name is Ivan". This is a crucial precursor to identity statements. In every formal introduction, in schools and offices, the formula **Мене звати...** is expected. Practice saying it right now with your own name!

## Презентація: Особові займенники (Presentation: Personal Pronouns)

Now that we can point to things and ask what they are, we need to talk about the people around us. To do this, we need personal pronouns—those handy little words like "I", "you", and "they" that replace names. The introduction of personal pronouns aligns perfectly with our learning goals, so let's meet your new best friends. 

Here is the complete list of Ukrainian personal pronouns:
* **я** (I)
* **ти** (you — informal, singular)
* **він** (he)
* **вона** (she)
* **воно** (it)
* **ми** (we)
* **ви** (you — formal, or plural)
* **вони** (they)

The most important cultural lesson here is the difference between **ти** and **ви**. In English, we use "you" for everyone: your best friend, your boss, your dog, or a stranger on the bus. Ukrainian, like many European languages, maintains a strict formal versus informal register, known as the T-V distinction.

> [!cultural]
> The **ви** Safety Net is your golden rule as a learner. Starting with **ви** is absolutely mandatory for strangers, elders, officials, and anyone you do not know personally in Ukrainian culture. It shows respect and cultural awareness. If you walk into a cafe or stop someone on the street, you must use **ви**. 

So, when do you use **ти**? The pronoun **ти** is reserved for close friends, family members, children, and animals. Moving from the formal **ви** to the informal **ти** is a meaningful social milestone. This 'Vi' to 'Ty' transition is a conscious choice, often initiated by the older or more senior person. In social settings, this shift might even be celebrated with a toast, a concept historically known as 'Bruderschaft' (brotherhood). A person might smile and say **«Давай на ти?»** (Shall we switch to ти?) — suggesting the shift to the informal register.

This is a wonderful moment—it means you have been accepted as a friend! However, a very common learner error is the Register Mix-up. Because English speakers lack the T-V distinction, they often accidentally use **ти** with officials, teachers, or elders. This can sound overly familiar or slightly rude. Always remember: when in doubt, rely on the **ви** Safety Net!

## Граматика: Секрет нульової зв'язки (Grammar: The Zero Copula Secret)

Are you ready for the best news you will hear all day? When it comes to saying who or what you are, Ukrainian grammar is actually much easier than English! 

In English, to make a simple sentence, you absolutely need a verb. You say "I **am** a student", "She **is** a teacher", or "They **are** here". The verb "to be" (am, is, are) acts as a bridge connecting the subject to the description. 

In Ukrainian, we have a magical rule for the present tense called the Zero Copula rule. The Zero Copula Secret means that when you are making a simple identification statement (Subject + Predicate), you simply drop the verb "to be" entirely! You just place the subject pronoun right next to the noun. 

Let's look at visualizing the gap. Imagine a silent, invisible link between the words, using the 'Ø' or '—' symbol to map the sentence:
* English: I (am) a student.
* Ukrainian: **Я [Ø] студент.** (for a male student)
* Ukrainian: **Я [Ø] студентка.** (for a female student)

Look how beautifully efficient that is! You do not need to memorize complicated conjugations of the verb "to be" for every pronoun. You just state the pronoun and the fact.
* **Він [Ø] вчитель.** (He is a teacher.)
* **Вона [Ø] вчителька.** (She is a teacher.)
* **Ми [Ø] студенти.** (We are students.)

A very common learner error here is the "Phantom 'Is'". Because the English brain desperately wants to put a verb in the middle of the sentence, students suffer from interference from English, causing them to insert the word **є** (is/am/are) unnecessarily. They might try to say *\*Я є студент*. 

Here is the critical note on **є**. While the linking verb **є** does exist in the Ukrainian dictionary, it is rarely used in simple identification sentences in modern speech. We only use it when we want to emphasize existence (like "Yes, I *do* exist!") or in specific philosophical contexts. For everyday communication, naming yourself, or identifying your profession, the Zero Copula is the only correct and natural way. 

To say "I am Ukrainian", a man simply says **Я українець**, and a woman says **Я українка**. Notice how the noun itself changes to match your gender? This is why the gender rules you learned previously are so vital! And to say someone is over here, you can simply use the particle **ось**: 
* **Ось він!** (Here he is!)
* **Ось вона!** (Here she is!)

No verbs required. Just pure, simple, direct connection.

## Робота над помилками та практика (Error Correction and Practice)

Let's tackle a very tricky obstacle that almost every English speaker faces: The 'It' Trap. 

In English, if you point to a table, a lamp, or a book, you use the pronoun "it". You say, "Where is the book? It is here." The pronoun "it" is the universal label for all inanimate objects. 

Because of this, learners often fall into the 'It' Trap by using the Ukrainian pronoun **воно** (it) for all inanimate objects (tables, lamps, phones) instead of using the proper gendered pronouns. Remember what you learned about grammatical gender? Everything in Ukrainian has a gender! 

If a noun is masculine, like **стіл** (table), you must replace it with **він** (he). If a noun is feminine, like **книга** (book), you must replace it with **вона** (she). The pronoun **воно** is strictly reserved ONLY for grammatically neuter nouns, like **вікно** (window) or **яблуко** (apple). 

Let's do a quick drill: replacing nouns with correct gendered pronouns to reinforce that everything in Ukrainian has gender.
* **Стіл** (table, masculine) -> **він**
* **Книга** (book, feminine) -> **вона**
* **Місто** (city, neuter) -> **воно**
* **Дім** (house, masculine) -> **він**

Now, let's practice some transformation drills. We are going to convert our simple **це** (this is) sentences into Zero Copula pronoun sentences. This noun-to-pronoun mapping will train your brain to assign gender automatically.
* Identifying: **Це Іван.** -> Describing: **Він студент.** 
* Identifying: **Це Ірина.** -> Describing: **Вона студентка.**
* Identifying: **Це мій тато.** -> Describing: **Він вчитель.**

See the pattern? You establish the identity first, and then you follow up with a beautiful, verb-free sentence using the correct gendered pronoun.

## Продакшн: Хто я і Хто ви? (Production: Who am I and Who are you?)

It is time to put everything together! Your task: self-introduction using zero copula patterns for your name, role, and nationality. 

Imagine you are at an international language meetup in Kyiv. You step up to the group and introduce yourself using exactly what we learned today. 
* **Привіт! Мене звати Марк. Я українець. Я студент.** 
* **Привіт! Мене звати Анна. Я українка. Я студентка.** 

Notice the confidence in these statements. You did not need a single verb! 

Now, let's roleplay. Imagine you are meeting a stranger at a passport control desk. The officer is an official, so you must use the **ви** Safety Net. The officer might ask:
* **Ви студент?** (Are you a student?)
And you can answer:
* **Так, я студент.** (Yes, I am a student.)

But what if you are at a cafe, meeting a peer of your own age? You can use the informal register and identify others in the room. You point to a friend and say:
* **Це мій брат. Він тут. Він студент.** 

Let's look at an extended roleplay to see all these pieces working together. Try to predict each answer before reading it!

> — **Привіт! Хто це?** (Hi! Who is this?)
> — **Це мій брат. Він студент.** (This is my brother. He is a student.)
> — **А що це?** (And what is this?)
> — **Це моя нова книга.** (This is my new book.)
> — **Дуже добре! Ви вчитель?** (Very good! Are you a teacher?)
> — **Ні, я студент. Я українець.** (No, I am a student. I am Ukrainian.)
> — **А вона? Вона студентка?** (And she? Is she a student?)
> — **Ні, вона вчителька. Вона українка.** (No, she is a teacher. She is Ukrainian.)
> — **А хто вони?** (And who are they?)
> — **Вони мої друзі. Ми всі тут.** (They are my friends. We are all here.)

In summary: reviewing the simple Subject + Predicate identification structure is the key. The foundation for A1.1 communication is built on these two pillars: knowing your pronouns (and choosing between **ти** and **ви**) and trusting the Zero Copula to make your sentences clean and natural. You are no longer just pointing at things; you are now actively participating in conversations!

## Підсумок — Summary

Today, we unlocked the secret to forming simple, natural Ukrainian sentences. You learned the fundamental question words **хто** (for people) and **що** (for objects) to identify the world around you using the demonstrative **це**. 

You also met the eight personal pronouns: **я**, **ти**, **він**, **вона**, **воно**, **ми**, **ви**, and **вони**. Most importantly, you learned the cultural weight behind the T-V distinction, knowing always to use the **ви** Safety Net with strangers and elders, and waiting for the joyful moment to switch to the informal **ти**. Finally, you mastered the Zero Copula Secret, realizing that you can drop the verb "to be" completely to say **Я студент** naturally and correctly. 

**Self-Check Questions:**
1. What is the difference between asking **Хто це?** and **Що це?**
2. Why is it a mistake to use **ти** with a shop assistant you just met?
3. If you want to say "I am a student," why is saying *\*Я є студент* unnatural?
4. If you are talking about a feminine object like **кава** (coffee), which pronoun do you use instead of the English "it"?

> [!tip]
> Practice saying these sentences aloud:
> * **Мене звати Анна. Я студентка. Я тут.**
> * **Це мій брат. Він студент. Він там.**
> * **Хто це? Це мій тато. Він вчитель.**
> * **Що це? Це моя нова книга.**
> * **Ми українці. Ви студенти. Вони тут.**
> * **Це новий телефон. Він там.**
> * **Це моя кава. Вона дуже смачна.**
> * **Ти мій найкращий друг.**
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/this-is-i-am.yaml`

```yaml
- type: fill-in
  title: "Introduce Yourself"
  instruction: "Complete each self-introduction sentence by choosing the correct word."
  items:
    - sentence: "___ звати Іван."
      answer: "Мене"
      options: ["Мене", "Моя", "Мій", "Це"]
      explanation: "Мене звати... is the fixed phrase for 'My name is...' in Ukrainian."
    - sentence: "Мене звати Анна. Я ___."
      answer: "студентка"
      options: ["студентка", "студент", "вчитель", "українець"]
      explanation: "Анна is a woman, so the feminine form студентка is correct."
    - sentence: "Мене звати Марк. Я ___."
      answer: "українець"
      options: ["українець", "українка", "студентка", "вчителька"]
      explanation: "Марк is a man, so the masculine nationality form українець is correct."
    - sentence: "Привіт! Мене ___ Ірина."
      answer: "звати"
      options: ["звати", "це", "тут", "ось"]
      explanation: "Мене звати... is the standard way to say 'My name is...' in Ukrainian."
    - sentence: "Я студент. Я ___."
      answer: "тут"
      options: ["тут", "це", "хто", "що"]
      explanation: "Я тут means 'I am here' — using the zero copula, no verb needed."
    - sentence: "Мене звати Оксана. Я ___."
      answer: "українка"
      options: ["українка", "українець", "студент", "вчитель"]
      explanation: "Оксана is a woman, so the feminine form українка is correct."

- type: fill-in
  title: "Complete Sentences with Pronouns"
  instruction: "Choose the correct Ukrainian pronoun to complete each sentence."
  items:
    - sentence: "___ студент."
      answer: "Я"
      options: ["Я", "Це", "Він", "Хто"]
      explanation: "Я студент means 'I am a student' — zero copula, no verb needed."
    - sentence: "___ вчителька."
      answer: "Вона"
      options: ["Вона", "Він", "Воно", "Вони"]
      explanation: "Вчителька is feminine, so the pronoun must be вона (she)."
    - sentence: "___ студенти."
      answer: "Ми"
      options: ["Ми", "Я", "Він", "Вона"]
      explanation: "Студенти is plural, and ми means 'we'."
    - sentence: "___ вчитель."
      answer: "Він"
      options: ["Він", "Вона", "Воно", "Ми"]
      explanation: "Вчитель is masculine, so the pronoun is він (he)."
    - sentence: "Книга — ___ нова."
      answer: "вона"
      options: ["вона", "він", "воно", "вони"]
      explanation: "Книга is a feminine noun, so we replace it with вона (she), not воно (it)."
    - sentence: "Стіл — ___ тут."
      answer: "він"
      options: ["він", "вона", "воно", "вони"]
      explanation: "Стіл is a masculine noun, so we replace it with він (he), not воно."
    - sentence: "Вікно — ___ там."
      answer: "воно"
      options: ["воно", "він", "вона", "вони"]
      explanation: "Вікно is a neuter noun, so воно is the correct pronoun."
    - sentence: "___ мої друзі."
      answer: "Вони"
      options: ["Вони", "Ми", "Він", "Вона"]
      explanation: "Друзі is plural, and вони means 'they'."
    - sentence: "___ це?"
      answer: "Хто"
      options: ["Хто", "Що", "Де", "Так"]
      explanation: "Use хто (who) when asking about a person."
    - sentence: "___ це? — Це підручник."
      answer: "Що"
      options: ["Що", "Хто", "Де", "Ось"]
      explanation: "Use що (what) when asking about an object, not a person."
    - sentence: "Дім — ___ там."
      answer: "він"
      options: ["він", "вона", "воно", "вони"]
      explanation: "Дім is a masculine noun, so we use він."
    - sentence: "___ студент?"
      answer: "Ви"
      options: ["Ви", "Я", "Він", "Це"]
      explanation: "Ви студент? means 'Are you a student?' using the formal/polite register."
    - sentence: "___ мій брат."
      answer: "Це"
      options: ["Це", "Він", "Вона", "Хто"]
      explanation: "Це мій брат means 'This is my brother' — using це for identification."
    - sentence: "Місто — ___ тут."
      answer: "воно"
      options: ["воно", "він", "вона", "ми"]
      explanation: "Місто is a neuter noun, so the correct pronoun is воно."
    - sentence: "___ українці."
      answer: "Ми"
      options: ["Ми", "Я", "Він", "Вона"]
      explanation: "Ми українці means 'We are Ukrainians' — plural subject needs ми."

- type: fill-in
  title: "Meeting Someone New"
  instruction: "You are at passport control. Complete the dialogue with the correct word."
  items:
    - sentence: "Привіт! ___ це?"
      answer: "Хто"
      options: ["Хто", "Що", "Де", "Так"]
      explanation: "When asking about a person, use хто (who)."
    - sentence: "Це мій брат. ___ студент."
      answer: "Він"
      options: ["Він", "Вона", "Воно", "Це"]
      explanation: "Брат is masculine, so we use він to say 'He is a student.'"
    - sentence: "___ вчитель? — Ні, я студент."
      answer: "Ви"
      options: ["Ви", "Ти", "Він", "Вони"]
      explanation: "At passport control, you must use the formal ви with strangers."
    - sentence: "А ___? Вона студентка?"
      answer: "вона"
      options: ["вона", "він", "воно", "ти"]
      explanation: "Asking about a woman — use вона (she)."
    - sentence: "Ні, вона ___."
      answer: "вчителька"
      options: ["вчителька", "вчитель", "студент", "українець"]
      explanation: "She is a teacher — the feminine form вчителька is needed."
    - sentence: "___ мої друзі. Ми всі тут."
      answer: "Вони"
      options: ["Вони", "Він", "Вона", "Ви"]
      explanation: "Вони мої друзі means 'They are my friends' — plural needs вони."
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/this-is-i-am.yaml`

```yaml
items:
  - lemma: "це"
    translation: "this is"
    pos: "particle"
    notes: "Demonstrative word used for identification"
    usage: "Це Ірина. Це підручник."
  - lemma: "я"
    translation: "I"
    pos: "pronoun"
    usage: "Я студент. Я тут."
  - lemma: "ти"
    translation: "you (informal)"
    pos: "pronoun"
    notes: "Used with close friends, family, children"
    usage: "Ти студент?"
  - lemma: "він"
    translation: "he"
    pos: "pronoun"
    notes: "Also replaces masculine nouns (стіл -> він)"
    usage: "Він студент. Він тут."
  - lemma: "вона"
    translation: "she"
    pos: "pronoun"
    notes: "Also replaces feminine nouns (книга -> вона)"
    usage: "Вона вчителька."
  - lemma: "воно"
    translation: "it"
    pos: "pronoun"
    notes: "Only for neuter nouns (вікно -> воно). Do not use for all objects!"
    usage: "Вікно — воно там."
  - lemma: "ми"
    translation: "we"
    pos: "pronoun"
    usage: "Ми студенти. Ми тут."
  - lemma: "ви"
    translation: "you (formal/plural)"
    pos: "pronoun"
    notes: "Mandatory with strangers, elders, officials"
    usage: "Ви студент?"
  - lemma: "вони"
    translation: "they"
    pos: "pronoun"
    usage: "Вони мої друзі."
  - lemma: "хто"
    translation: "who"
    pos: "pronoun"
    notes: "Used to ask about people"
    usage: "Хто це? — Це мій брат."
  - lemma: "що"
    translation: "what"
    pos: "pronoun"
    notes: "Used to ask about objects and concepts"
    usage: "Що це? — Це книга."
  - lemma: "студент"
    translation: "student (male)"
    pos: "noun"
    gender: "m"
    usage: "Я студент."
  - lemma: "студентка"
    translation: "student (female)"
    pos: "noun"
    gender: "f"
    usage: "Вона студентка."
  - lemma: "вчитель"
    translation: "teacher (male)"
    pos: "noun"
    gender: "m"
    usage: "Він вчитель."
  - lemma: "вчителька"
    translation: "teacher (female)"
    pos: "noun"
    gender: "f"
    usage: "Вона вчителька."
  - lemma: "українець"
    translation: "Ukrainian (male)"
    pos: "noun"
    gender: "m"
    usage: "Я українець."
  - lemma: "українка"
    translation: "Ukrainian (female)"
    pos: "noun"
    gender: "f"
    usage: "Я українка."
  - lemma: "ось"
    translation: "here (is), over here"
    pos: "particle"
    usage: "Ось він! Ось вона!"
  - lemma: "звати"
    translation: "to call, to name"
    pos: "verb"
    aspect: "imperfective"
    notes: "Used in the fixed phrase 'Мене звати...'"
    usage: "Мене звати Іван."
  - lemma: "привіт"
    translation: "hello, hi"
    pos: "noun"
    gender: "m"
    notes: "Informal greeting"
    usage: "Привіт! Мене звати Анна."
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
- Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/this-is-i-am.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/this-is-i-am.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/this-is-i-am.yaml`

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
