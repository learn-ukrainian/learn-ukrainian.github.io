✅ Message sent to Gemini (ID: 26671) [auto-acked: self-addressed]

🚀 Invoking Gemini to process message #26671...
📨 Message #26671
   From: gemini → To: gemini
   Type: query
   Task: demonstratives-this-that-review-fix-1
   Time: 2026-03-18T05:57:50.298739+00:00

============================================================

# Gemini Review Fix: Targeted Repair via FIND/REPLACE

> **You are an expert Ukrainian language editor applying targeted fixes.**
> You have NO tools — output FIND/REPLACE pairs only.
> The build system will apply your fixes programmatically.

---

## Editing Principles

- **IMPROVE, don't destroy.** Every rewrite should teach MORE than the original.
- **PRESERVE the author's intent.** Rewrite poorly explained content to explain it well — don't delete it.
- **MATCH the surrounding voice.** Your fixes should read like the original author wrote them on a better day.
- Only DELETE truly empty sentences (pure cheerleading with zero information).

---

## Fix Plan (from review)

## Review Findings (targeted fix required)

**CONSTRAINTS:**
- Fix ONLY the issues listed below
- Do NOT rewrite surrounding text
- Preserve word count and structure
- Only modify these sections: Section "Цей vs Той у контексті (This vs That in context)" -> "Try it yourself" callout, Section "Цей vs Той у контексті (This vs That in context)" -> Conversational Distance, Section "Цей vs Той у контексті (This vs That in context)" -> Spatial Distance, Section "Цей vs Той у контексті (This vs That in context)" -> Spatial Distance -> (У кімнаті / In the room)

### Finding 1: Grammatical Invalidity (Macaronic Phrasing)
**Location**: Section "Цей vs Той у контексті (This vs That in context)" -> "Try it yourself" callout
**Problem**: "...your Ukrainian is becoming more natural with **кожний** новий крок (every new step)!" Using a Ukrainian noun phrase in the nominative case directly after an English preposition ("with") is linguistically invalid and sets a bad precedent.
**Required Fix**: Rewrite into two distinct sentences, keeping the Ukrainian grammatically intact: "...becoming more natural. **Кожний** новий крок — це успіх (Every new step is a success)!"
**Severity**: HIGH

### Finding 2: Scope Violation - Accusative Case
**Location**: Section "Цей vs Той у контексті (This vs That in context)" -> Spatial Distance -> (У кімнаті / In the room)
**Problem**: The sentence "Я люблю **цю** кімнату!" uses the accusative case. For beginners who have only learned the nominative (цей/ця/це), seeing "цю" and "кімнату" is confusing and violates the A1 constraints (accusative is not taught until M25).
**Required Fix**: Change to a nominative construction: "**Ця** кімната дуже гарна!"
**Severity**: HIGH

### Finding 3: Scope Violation - Past Tense
**Location**: Section "Цей vs Той у контексті (This vs That in context)" -> Conversational Distance
**Problem**: "Ми говорили про **інший** будинок." uses the past tense verb "говорили" and the prepositional object "про інший будинок", which are out of scope for early A1 modules.
**Required Fix**: Change to a simpler structure that avoids the past tense entirely: "А **інший** будинок? **Той** будинок старий."
**Severity**: HIGH

### Finding 4: Scope Violation - Locative Case Headers
**Location**: Section "Цей vs Той у контексті (This vs That in context)" -> Spatial Distance
**Problem**: Dialogue headers use the locative case with prepositions: "> **(У кімнаті / In the room)**" and "> **(На ринку / At the market)**". This exposes learners to noun mutations ('кімната' -> 'кімнаті', 'ринок' -> 'ринку') before cases are formally taught.
**Required Fix**: Simplify to nominative labels: "> **(Кімната / Room)**" and "> **(Ринок / Market)**".
**Severity**: HIGH

---

## Plan Adherence Issues (Deterministic — MUST FIX)

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:quiz`
  - Expected: Plan requires ≥12 items
  - Actual: Activity has 6 items
  - Fix: Add 6 more items to 'quiz' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:match-up`
  - Expected: Plan requires ≥10 items
  - Actual: Activity has 6 items
  - Fix: Add 4 more items to 'match-up' activity


---

## Critical Issues Found

### Issue 1: Grammatical Invalidity (Macaronic Phrasing)
**Location**: Section "Цей vs Той у контексті (This vs That in context)" -> "Try it yourself" callout
**Problem**: "...your Ukrainian is becoming more natural with **кожний** новий крок (every new step)!" Using a Ukrainian noun phrase in the nominative case directly after an English preposition ("with") is linguistically invalid and sets a bad precedent.
**Fix**: Rewrite into two distinct sentences, keeping the Ukrainian grammatically intact: "...becoming more natural. **Кожний** новий крок — це успіх (Every new step is a success)!"

### Issue 2: Scope Violation - Accusative Case
**Location**: Section "Цей vs Той у контексті (This vs That in context)" -> Spatial Distance -> (У кімнаті / In the room)
**Problem**: The sentence "Я люблю **цю** кімнату!" uses the accusative case. For beginners who have only learned the nominative (цей/ця/це), seeing "цю" and "кімнату" is confusing and violates the A1 constraints (accusative is not taught until M25).
**Fix**: Change to a nominative construction: "**Ця** кімната дуже гарна!"

### Issue 3: Scope Violation - Past Tense
**Location**: Section "Цей vs Той у контексті (This vs That in context)" -> Conversational Distance
**Problem**: "Ми говорили про **інший** будинок." uses the past tense verb "говорили" and the prepositional object "про інший будинок", which are out of scope for early A1 modules.
**Fix**: Change to a simpler structure that avoids the past tense entirely: "А **інший** будинок? **Той** будинок старий."

### Issue 4: Scope Violation - Locative Case Headers
**Location**: Section "Цей vs Той у контексті (This vs That in context)" -> Spatial Distance
**Problem**: Dialogue headers use the locative case with prepositions: "> **(У кімнаті / In the room)**" and "> **(На ринку / At the market)**". This exposes learners to noun mutations ('кімната' -> 'кімнаті', 'ринок' -> 'ринку') before cases are formally taught.
**Fix**: Simplify to nominative labels: "> **(Кімната / Room)**" and "> **(Ринок / Market)**".

---

## Ukrainian Language Issues

- "with **кожний** новий крок" — Ungrammatical mixing of languages avoiding proper declension.
- "Я люблю **цю** кімнату!" — Unexplained accusative case usage.
- "Ми говорили про **інший** будинок." — Unexplained past tense and prepositional case.
- "У кімнаті", "На ринку" — Unexplained locative case usage.

---

## Fix Plan to Reach 9.0+

1. Replace "Я люблю цю кімнату!" with a nominative sentence like "Ця кімната дуже гарна!".
2. Replace the past-tense "Ми говорили про інший будинок." with a simpler transition like "А інший будинок?".
3. Change the location headers "(У кімнаті...)" and "(На ринку...)" to nominative "(Кімната...)", "(Ринок...)".
4. Fix the "Try it yourself" callout text to avoid mixing the English preposition "with" with Ukrainian nominative phrases.

---

## Audit Failures (from automated re-audit)

```
Error: No YAML frontmatter found (checked embedded and sidecar).
Critical Failures:
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/demonstratives-this-that-audit.log for details)
```

---

## File Contents

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/demonstratives-this-that.md`

```markdown
# Demonstratives — The Grammar of This and That

Welcome back! You've been building your Ukrainian toolkit steadily — you can talk about yourself, describe things, and say what belongs to whom. Now you're going to learn how to point things out: **this** book right here, **that** building over there. These little words — **вказівні займенники** (demonstrative pronouns) — pop up constantly in everyday Ukrainian.

By the end of this module, you'll be able to:
- Say "this" and "that" for masculine, feminine, and neuter nouns
- Use the plural forms "these" and "those"
- Tell apart **це** as "this is..." from **це** as "this (thing)"
- Navigate the tricky double life of **та** (both "that" and "and")

You already know how **мій/моя/моє** change to match gender — **цей/ця/це** work the same way. This is going to feel familiar. Let's go!

## Цей/ця/це (This)

In English, "this" never changes — this book, this street, this city. Ukrainian is different. The word for "this" must match the gender of the noun it describes, just like your possessive pronouns **мій/моя/моє** from the previous module.

Here's the pattern:

| Gender | This | Example |
|--------|------|---------|
| Masculine (він) | **цей** | **цей хлопець** — this guy |
| Feminine (вона) | **ця** | **ця книга** — this book |
| Neuter (воно) | **це** | **це місто** — this city |

Notice how this mirrors what you already know:

| | Possessive | Demonstrative |
|--|-----------|---------------|
| Masculine | мій | цей |
| Feminine | моя | ця |
| Neuter | моє | це |

The agreement rule is the same — look at the noun's gender, then pick the matching form. You've done this before with adjectives and possessives, so you're already ahead!

- **Цей стілець** новий. — This chair is new.
- **Ця вулиця** гарна. — This street is nice.
- **Це озеро** велике. — This lake is big.
- **Цей будинок** старий. — This building is old.
- **Ця дівчина** — студентка. — This girl is a student.

[!tip] **Gender shortcut**
If you remember the gender of a noun from its ending, you already know which demonstrative to use: consonant ending → **цей**, -а/-я ending → **ця**, -о/-е ending → **це**.

### The Two Lives of Це

Here's a critical distinction. You've been using **це** since your very first modules — in sentences like **Це кіт** (This is a cat). That **це** is a copula — it means "this is." But now you're meeting **це** as a demonstrative pronoun modifying a neuter noun.

Compare these two sentences carefully:

- **Це кафе.** — This is a café. (What is it? → It's a café.)
- **Це кафе** гарне. — This café is nice. (Which café? → This one.)

In the first sentence, **це** stands alone — it's the subject, pointing at something and identifying it. In the second, **це** sits before **кафе** and describes which café you mean — it's working as a demonstrative, and the sentence continues with an adjective.

Here's how to tell them apart:

- **Це** + noun + period = copula ("This is a...")
- **Це** + noun + continues = demonstrative ("This particular...")

> **(У кафе / At a café)**
>
> — Це кафе?
> — Так, це кафе. Це кафе дуже гарне!
> — А це місто велике?
> — Так. Це місто — Львів.

[!warning] **Common mistake**
Don't use **це** for all genders! English speakers often say *це хлопець* instead of **цей хлопець**, because English "this" never changes. Always check the noun's gender first.

## Ці (These)

When a noun is plural, all three gender forms collapse into one: **ці** (these). No matter whether the singular was **цей**, **ця**, or **це** — the plural is always **ці**.

| Singular | Plural |
|----------|--------|
| **цей** стілець (this chair) | **ці** стільці (these chairs) |
| **ця** книга (this book) | **ці** книги (these books) |
| **це** місто (this city) | **ці** міста (these cities) |

This is actually good news — one form for all plurals! Here are some examples:

- **Ці** студенти говорять добре. — These students speak well.
- **Ці** будинки нові. — These buildings are new.
- **Ці** вулиці гарні. — These streets are nice.
- **Ці** озера великі. — These lakes are big.

[!warning] **Watch out for number mismatch**
A common beginner error is using a singular demonstrative with a plural noun: *цей книги* instead of **ці книги**. Your strategy: if you see -и, -і, or -а on the noun (plural endings), you need **ці** — no exceptions.

Think of it this way: singular nouns get a gender-specific form (**цей/ця/це**), but plural nouns all share one form (**ці**). Simple!

## Той/та/те/ті (That/Those)

Now let's look across the room. When something is farther away, Ukrainian uses a separate set of demonstratives: **той/та/те/ті** (that/those).

The gender agreement works exactly the same way:

| Gender | That | Example |
|--------|------|---------|
| Masculine | **той** | **той будинок** — that building |
| Feminine | **та** | **та вулиця** — that street |
| Neuter | **те** | **те озеро** — that lake |
| Plural | **ті** | **ті люди** — those people |

- **Той** стілець старий. — That chair is old.
- **Та** дівчина — моя подруга. — That girl is my friend.
- **Те** місто далеко. — That city is far.
- **Ті** книги цікаві. — Those books are interesting.
- **Той** хлопець — студент. — That guy is a student.

Here's the full picture — both sets side by side:

| | This (close) | That (far) |
|--|-------------|------------|
| Masculine | **цей** | **той** |
| Feminine | **ця** | **та** |
| Neuter | **це** | **те** |
| Plural | **ці** | **ті** |

[!note] **Pattern recognition**
Notice how the "that" forms are shorter and simpler: **той, та, те, ті** — all start with **т** and are just one syllable. The "this" forms **цей, ця, це, ці** all start with **ц**. This makes them easy to keep apart.

### The Double Life of Та

Here's something tricky. The word **та** has two completely different jobs in Ukrainian:

1. **та** = "that" (feminine demonstrative) — **Та дівчина** гарна.
2. **та** = "and" (conjunction, like **і**) — Хлопець **та** дівчина.

Sometimes both appear in the same sentence:

- **Та** дівчина **та** її подруга тут. — That girl and her friend are here.

The first **та** means "that" (it comes before a noun and describes it). The second **та** means "and" (it connects two things). Context makes it clear — if **та** sits right before a noun and acts like "which one?", it's a demonstrative. If it connects two nouns or phrases, it's a conjunction.

[!tip] **Quick test for та**
Can you replace **та** with **і** (and)? If yes, it's a conjunction. If no, it's a demonstrative.
- Та дівчина → *і дівчина*? No → demonstrative ✓
- Дівчина та хлопець → дівчина і хлопець? Yes → conjunction ✓

## Цей vs Той у контексті (This vs That in context)

The core difference between **цей** and **той** is distance — physical or conversational.

### Spatial Distance

When you're pointing at things, **цей** means "here, close to me" and **той** means "over there, farther away." Imagine you're at a market:

> **(На ринку / At the market)**
>
> — Я хочу **цей** торт. *(pointing at the one nearby)*
> — **Цей** торт? Він дуже смачний!
> — А **той** торт великий? *(pointing at one farther away)*
> — **Той**? Так, він великий і дорогий.

> **(У кімнаті / In the room)**
>
> — **Цей** стілець зручний.
> — А **той** стілець?
> — **Той** старий, але добрий.
> — Я люблю **цю** кімнату!

In each case, **цей/ця/це** refers to what's near the speaker, and **той/та/те** refers to what's farther away. This is natural and intuitive — just like pointing and saying "this one... no, that one!"

### Conversational Distance

Beyond physical space, **цей** and **той** also work for conversational reference. When you just mentioned something, use **цей** (this, the one I just said). When referring back to something mentioned earlier, use **той** (that, the one from before):

- Я бачу **такий** великий будинок! **Цей** будинок новий. — I see such a big building! This building is new. *(just mentioned)*
- Ми говорили про **інший** будинок. **Той** будинок старий. — We were talking about a different building. That building is old. *(mentioned earlier)*

[!practice] **Try it yourself**
Look around the room you're in right now. Pick three objects and describe each one: **цей/ця/це ___** for things within arm's reach, and **той/та/те ___** for things across the room. Say each phrase out loud — your Ukrainian is becoming more natural with **кожний** новий крок (every new step)!

## Практика (Practice)

Time to put everything together! You've learned eight demonstrative forms and the key distinctions between them. Let's practice.

### Gender Agreement Drill

Choose the correct demonstrative for each noun:

- ___ книга (this) → **ця** книга (feminine)
- ___ будинок (that) → **той** будинок (masculine)
- ___ озеро (this) → **це** озеро (neuter)
- ___ стільці (these) → **ці** стільці (plural)
- ___ вулиця (that) → **та** вулиця (feminine)
- ___ торт (this) → **цей** торт (masculine)

### Proximity Contrast

Pair up items by distance:

- **Цей** стілець новий, а **той** стілець старий.
- **Ця** книга цікава, а **та** книга нудна.
- **Це** кафе гарне, а **те** кафе маленьке.
- **Ці** будинки нові, а **ті** будинки старі.

[!challenge] **Spot the demonstrative!**
Read this mini-text and identify each demonstrative — is it "this/these" or "that/those"?

Цей хлопець — мій друг. Він любить ці книги. Та дівчина — його подруга. Вона сама читає ті книги. Це місто гарне!

*(Answer: цей = this, ці = these, та = that, ті = those, це = this)*

# Підсумок
Great work! You can now point out anything in Ukrainian — near or far, singular or plural. Here's what you've mastered:

- **Цей/ця/це** for "this" (matching gender) and **ці** for "these"
- **Той/та/те** for "that" (matching gender) and **ті** for "those"
- The difference between **це** as a copula ("This is...") and **це** as a demonstrative ("This thing...")
- How to tell **та** the demonstrative from **та** the conjunction
- Using proximity to choose between **цей** and **той**

**Self-check — can you do these?**

1. Your friend points at a building far away and asks what it is. How do you say "That building is old"?
2. You're holding a book. How do you say "This book is interesting"?
3. Someone says **«Та дівчина та її подруга»** — which **та** means "that" and which means "and"?
4. You see several nice streets. How do you say "These streets are nice"?

*(Answers: 1. Той будинок старий. 2. Ця книга цікава. 3. First та = "that," second та = "and." 4. Ці вулиці гарні.)*

You're ready for the next module, where you'll learn numbers and money — and you'll use **ці** and **ті** to point at the things you're counting! Keep going — you're doing wonderfully.
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/demonstratives-this-that.yaml`

```yaml
- type: fill-in
  title: "Choose the Correct Demonstrative"
  instruction: "Fill in the blank with the correct demonstrative pronoun (this/that/these/those)."
  items:
    - sentence: "___ книга цікава."
      answer: "Ця"
      options: ["Ця", "Цей", "Це", "Ці"]
      explanation: "Книга is feminine, so it takes ця (this)."
    - sentence: "___ будинок старий."
      answer: "Цей"
      options: ["Цей", "Ця", "Це", "Ці"]
      explanation: "Будинок is masculine, so it takes цей (this)."
    - sentence: "___ озеро велике."
      answer: "Це"
      options: ["Це", "Цей", "Ця", "Ці"]
      explanation: "Озеро is neuter, so it takes це (this)."
    - sentence: "___ студенти говорять добре."
      answer: "Ці"
      options: ["Ці", "Цей", "Ця", "Це"]
      explanation: "Студенти is plural, so it takes ці (these)."
    - sentence: "___ вулиця гарна."
      answer: "Та"
      options: ["Та", "Той", "Те", "Ті"]
      explanation: "Вулиця is feminine, so it takes та (that)."
    - sentence: "___ стілець зручний."
      answer: "Той"
      options: ["Той", "Та", "Те", "Ті"]
      explanation: "Стілець is masculine, so it takes той (that)."
    - sentence: "___ місто далеко."
      answer: "Те"
      options: ["Те", "Той", "Та", "Ті"]
      explanation: "Місто is neuter, so it takes те (that)."
    - sentence: "___ книги цікаві."
      answer: "Ті"
      options: ["Ті", "Той", "Та", "Те"]
      explanation: "Книги is plural, so it takes ті (those)."
    - sentence: "___ торт смачний."
      answer: "Цей"
      options: ["Цей", "Ця", "Це", "Ці"]
      explanation: "Торт is masculine, so it takes цей (this)."
    - sentence: "___ дівчина — студентка."
      answer: "Ця"
      options: ["Ця", "Цей", "Це", "Ці"]
      explanation: "Дівчина is feminine, so it takes ця (this)."

- type: quiz
  title: "Gender Agreement with Demonstratives"
  instruction: "Choose the correct answer for each question."
  items:
    - question: "Which demonstrative do you use with книга (this)?"
      options:
        - text: "ця"
          correct: true
        - text: "цей"
          correct: false
        - text: "це"
          correct: false
        - text: "ці"
          correct: false
      explanation: "Книга is feminine, so it takes ця."
    - question: "Which demonstrative do you use with будинок (that)?"
      options:
        - text: "той"
          correct: true
        - text: "та"
          correct: false
        - text: "те"
          correct: false
        - text: "ті"
          correct: false
      explanation: "Будинок is masculine, so it takes той."
    - question: "Which demonstrative do you use with озеро (this)?"
      options:
        - text: "це"
          correct: true
        - text: "цей"
          correct: false
        - text: "ця"
          correct: false
        - text: "ці"
          correct: false
      explanation: "Озеро is neuter, so it takes це."
    - question: "Which demonstrative do you use with стільці (these)?"
      options:
        - text: "ці"
          correct: true
        - text: "цей"
          correct: false
        - text: "ця"
          correct: false
        - text: "це"
          correct: false
      explanation: "Стільці is plural, so it takes ці — one form for all plural nouns."
    - question: "Which demonstrative do you use with вулиця (that)?"
      options:
        - text: "та"
          correct: true
        - text: "той"
          correct: false
        - text: "те"
          correct: false
        - text: "ті"
          correct: false
      explanation: "Вулиця is feminine, so it takes та."
    - question: "Which demonstrative do you use with місто (that)?"
      options:
        - text: "те"
          correct: true
        - text: "той"
          correct: false
        - text: "та"
          correct: false
        - text: "ті"
          correct: false
      explanation: "Місто is neuter, so it takes те."
    - question: "What is the plural form of цей, ця, and це?"
      options:
        - text: "ці"
          correct: true
        - text: "ті"
          correct: false
        - text: "ця"
          correct: false
        - text: "це"
          correct: false
      explanation: "All three singular forms (цей, ця, це) merge into one plural: ці."
    - question: "Which demonstrative do you use with хлопець (this)?"
      options:
        - text: "цей"
          correct: true
        - text: "ця"
          correct: false
        - text: "це"
          correct: false
        - text: "ці"
          correct: false
      explanation: "Хлопець is masculine, so it takes цей."
    - question: "All 'this/these' forms in Ukrainian start with which letter?"
      options:
        - text: "ц"
          correct: true
        - text: "т"
          correct: false
        - text: "в"
          correct: false
        - text: "м"
          correct: false
      explanation: "Цей, ця, це, ці — all start with ц. The 'that/those' forms start with т."
    - question: "All 'that/those' forms in Ukrainian start with which letter?"
      options:
        - text: "т"
          correct: true
        - text: "ц"
          correct: false
        - text: "д"
          correct: false
        - text: "с"
          correct: false
      explanation: "Той, та, те, ті — all start with т."
    - question: "Which demonstrative do you use with кафе (this)?"
      options:
        - text: "це"
          correct: true
        - text: "цей"
          correct: false
        - text: "ця"
          correct: false
        - text: "ці"
          correct: false
      explanation: "Кафе is neuter, so it takes це."
    - question: "Which demonstrative do you use with торт (that)?"
      options:
        - text: "той"
          correct: true
        - text: "та"
          correct: false
        - text: "те"
          correct: false
        - text: "ті"
          correct: false
      explanation: "Торт is masculine (consonant ending), so it takes той."

- type: match-up
  title: "Match Demonstrative Phrases to English"
  instruction: "Match each Ukrainian phrase with its English translation."
  pairs:
    - left: "цей хлопець"
      right: "this guy"
    - left: "ця книга"
      right: "this book"
    - left: "це місто"
      right: "this city"
    - left: "ці студенти"
      right: "these students"
    - left: "той будинок"
      right: "that building"
    - left: "та вулиця"
      right: "that street"
    - left: "те озеро"
      right: "that lake"
    - left: "ті люди"
      right: "those people"
    - left: "цей стілець"
      right: "this chair"
    - left: "ця дівчина"
      right: "this girl"

- type: group-sort
  title: "Sort Nouns by Gender"
  instruction: "Sort these nouns into groups based on which demonstrative form they take."
  groups:
    - name: "Masculine (цей / той)"
      items:
        - "будинок"
        - "хлопець"
        - "стілець"
        - "торт"
    - name: "Feminine (ця / та)"
      items:
        - "книга"
        - "вулиця"
        - "дівчина"
        - "подруга"
    - name: "Neuter (це / те)"
      items:
        - "місто"
        - "озеро"
        - "кафе"
    - name: "Plural (ці / ті)"
      items:
        - "студенти"
        - "книги"
        - "будинки"

- type: true-false
  title: "True or False?"
  instruction: "Decide whether each statement is true or false."
  items:
    - statement: "The Ukrainian word for 'this' changes depending on the noun's gender."
      correct: true
      explanation: "Correct — цей (masculine), ця (feminine), це (neuter)."
    - statement: "Ці is the plural form for all genders — masculine, feminine, and neuter."
      correct: true
      explanation: "All three singular forms collapse into one plural: ці."
    - statement: "The word та always means 'that' in Ukrainian."
      correct: false
      explanation: "Та can also mean 'and' (like і). Test it: can you replace та with і? If yes, it means 'and.'"
    - statement: "In the sentence 'Це кафе.' (with nothing after), це works as a demonstrative pronoun meaning 'this cafe.'"
      correct: false
      explanation: "When це stands alone before a noun, it works as a copula meaning 'This is a cafe.'"
    - statement: "Цей is the correct demonstrative for the noun книга."
      correct: false
      explanation: "Книга is feminine, so it takes ця, not цей."
    - statement: "Той, та, те, ті are used for things that are farther away from the speaker."
      correct: true
      explanation: "The 'that/those' set is for distant objects, like English 'that over there.'"
    - statement: "You can replace та with і to check if та means 'and.'"
      correct: true
      explanation: "If the sentence still makes sense with і, then та is a conjunction meaning 'and.'"
    - statement: "The plural of той, та, and те is ті."
      correct: true
      explanation: "Just like цей/ця/це become ці, the forms той/та/те become ті in the plural."

- type: unjumble
  title: "Put the Words in Order"
  instruction: "Arrange the words to form a correct Ukrainian sentence."
  items:
    - words: ["книга", "Ця", "цікава"]
      answer: "Ця книга цікава"
    - words: ["старий", "будинок", "Той"]
      answer: "Той будинок старий"
    - words: ["нові", "будинки", "Ці"]
      answer: "Ці будинки нові"
    - words: ["велике", "Це", "озеро"]
      answer: "Це озеро велике"
    - words: ["гарна", "вулиця", "Та"]
      answer: "Та вулиця гарна"
    - words: ["цікаві", "книги", "Ті"]
      answer: "Ті книги цікаві"

- type: quiz
  title: "This or That? Proximity and Ambiguity"
  instruction: "Choose the correct answer."
  items:
    - question: "You're holding a book and want to say 'this book.' Which is correct?"
      options:
        - text: "ця книга"
          correct: true
        - text: "цей книга"
          correct: false
        - text: "це книга"
          correct: false
        - text: "ці книга"
          correct: false
      explanation: "Книга is feminine, so 'this book' is ця книга."
    - question: "You see a building across the street. How do you say 'that building'?"
      options:
        - text: "той будинок"
          correct: true
        - text: "та будинок"
          correct: false
        - text: "те будинок"
          correct: false
        - text: "ті будинок"
          correct: false
      explanation: "Будинок is masculine, so 'that building' is той будинок."
    - question: "In 'Та дівчина та її подруга,' which та means 'and'?"
      options:
        - text: "The second та"
          correct: true
        - text: "The first та"
          correct: false
        - text: "Both"
          correct: false
        - text: "Neither"
          correct: false
      explanation: "The first та describes дівчина (that girl). The second та connects two people (and her friend)."
    - question: "What does це mean in 'Це кафе.' (with nothing after)?"
      options:
        - text: "This is (copula)"
          correct: true
        - text: "This (demonstrative)"
          correct: false
        - text: "That"
          correct: false
        - text: "These"
          correct: false
      explanation: "When це + noun + period, it is a copula: 'This is a cafe.'"
    - question: "What does це mean in 'Це кафе гарне.'?"
      options:
        - text: "This (demonstrative)"
          correct: true
        - text: "This is (copula)"
          correct: false
        - text: "That"
          correct: false
        - text: "A"
          correct: false
      explanation: "When це + noun + continues, it is a demonstrative: 'This cafe is nice.'"
    - question: "How do you say 'these lakes' in Ukrainian?"
      options:
        - text: "ці озера"
          correct: true
        - text: "це озера"
          correct: false
        - text: "цей озера"
          correct: false
        - text: "ця озера"
          correct: false
      explanation: "Озера is plural, so it takes ці — the one plural form for all genders."

- type: match-up
  title: "This vs That — Proximity Pairs"
  instruction: "Match each 'this' phrase with its 'that' equivalent."
  pairs:
    - left: "цей стілець"
      right: "той стілець"
    - left: "ця вулиця"
      right: "та вулиця"
    - left: "це озеро"
      right: "те озеро"
    - left: "ці будинки"
      right: "ті будинки"
    - left: "цей торт"
      right: "той торт"
    - left: "ця книга"
      right: "та книга"
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/demonstratives-this-that.yaml`

```yaml
items:
  - lemma: "цей"
    translation: "this (masculine)"
    pos: "pronoun"
    usage: "цей хлопець, цей будинок"
    notes: "Used with masculine nouns. Part of the demonstrative set цей/ця/це/ці."
  - lemma: "ця"
    translation: "this (feminine)"
    pos: "pronoun"
    usage: "ця дівчина, ця книга"
    notes: "Used with feminine nouns."
  - lemma: "це"
    translation: "this (neuter); this is"
    pos: "pronoun"
    usage: "це місто, це озеро"
    notes: "Double function: demonstrative (це місто гарне = this city is nice) and copula (Це місто = This is a city)."
  - lemma: "ці"
    translation: "these"
    pos: "pronoun"
    usage: "ці книги, ці студенти"
    notes: "Plural form for all genders — цей, ця, це all become ці."
  - lemma: "той"
    translation: "that (masculine)"
    pos: "pronoun"
    usage: "той будинок, той стілець"
    notes: "Used with masculine nouns for distant objects."
  - lemma: "та"
    translation: "that (feminine); and"
    pos: "pronoun"
    usage: "та вулиця, та дівчина"
    notes: "Also functions as conjunction meaning 'and' (like і). Context determines meaning."
  - lemma: "те"
    translation: "that (neuter)"
    pos: "pronoun"
    usage: "те озеро, те місто"
    notes: "Used with neuter nouns for distant objects."
  - lemma: "ті"
    translation: "those"
    pos: "pronoun"
    usage: "ті люди, ті міста"
    notes: "Plural form for all genders — той, та, те all become ті."
  - lemma: "будинок"
    translation: "building, house"
    pos: "noun"
    gender: "m"
    usage: "цей будинок, той будинок"
  - lemma: "вулиця"
    translation: "street"
    pos: "noun"
    gender: "f"
    usage: "ця вулиця, та вулиця"
  - lemma: "озеро"
    translation: "lake"
    pos: "noun"
    gender: "n"
    usage: "це озеро, те озеро"
  - lemma: "стілець"
    translation: "chair"
    pos: "noun"
    gender: "m"
    usage: "цей стілець, той стілець"
  - lemma: "такий"
    translation: "such, so"
    pos: "adjective"
    usage: "такий великий, такий цікавий"
    notes: "Related demonstrative — agrees in gender like adjectives."
  - lemma: "інший"
    translation: "other, different"
    pos: "adjective"
    usage: "інший будинок, інша вулиця"
    notes: "Used to contrast with demonstratives: цей vs інший."
  - lemma: "кожний"
    translation: "every, each"
    pos: "adjective"
    usage: "кожний студент, кожна книга"
  - lemma: "сам"
    translation: "oneself, (by) oneself"
    pos: "pronoun"
    usage: "сам бачив, сама знає"
    notes: "Emphatic pronoun; agrees in gender."
  - lemma: "книга"
    translation: "book"
    pos: "noun"
    gender: "f"
    usage: "ця книга, та книга"
  - lemma: "місто"
    translation: "city, town"
    pos: "noun"
    gender: "n"
    usage: "це місто, те місто"
  - lemma: "торт"
    translation: "cake"
    pos: "noun"
    gender: "m"
    usage: "цей торт, той торт"
  - lemma: "кафе"
    translation: "cafe"
    pos: "noun"
    gender: "n"
    usage: "це кафе, те кафе"
    notes: "Indeclinable neuter noun (borrowed word)."
```

---

## Friction Constraints (Past Review Findings — DO NOT reintroduce)

FRICTION CONSTRAINTS (from past build reviews — DO NOT repeat these errors):
- [GLOBAL] сес-тра is a VALID word division per Правопис 2019 §49. Do NOT mark it as an error. Phonetic syllabification (се-стра) and typographic word division (сес-тра) follow different rules — both are correct in their respective contexts.
- [GLOBAL] Ukrainian textbooks teach a hands-on-EARS test for voicing (закрий долонями вуха), NOT a hand-on-throat test. The hand-on-throat test is a valid phonetics technique but must NOT be attributed to Ukrainian textbooks. Source: Кравцова 2019, Grade 2, p.39.
- [GLOBAL] Do NOT invent Ukrainian words for minimal pairs. "Сір" is NOT a word meaning "grey" — the correct form is "сірий". Use verified minimal pairs only: кит/кіт, бити/біти, лис/ліс.

---

## Instructions

**CRITICAL: Fix ALL issues. Partial fixes are REJECTED. Count your fixes — if you missed one, go back.**

1. For EVERY issue in the Fix Plan AND audit failures, locate the exact text in the file contents above
2. Output a FIND/REPLACE pair with the exact text and the corrected version
3. Prioritize: **audit gate failures first**, then review issues
4. Only fix issues documented above — no silent extra changes
5. Maximum **15 FIND/REPLACE pairs** total

---

## Fix Rules

- Only fix issues documented in the Fix Plan or audit failures above
- You MAY add new activities or modify existing ones if the Fix Plan explicitly requests it
- Do NOT add new prose sections unless the Fix Plan explicitly requests it
- If nothing needs fixing, output an empty fix block
- FIND text must match the file contents EXACTLY (copy-paste from above)

---

## Output Format

You MUST use these exact delimiters:

```
===SECTION_FIX_START===
FILE: [filename]
FIND:
[exact text from the file — must match character-for-character]
REPLACE:
[corrected text]
---
FILE: [filename]
FIND:
[exact text]
REPLACE:
[corrected text]
---
[... more pairs, max 15 ...]
===SECTION_FIX_END===
```

If no fixes are needed:

```
===SECTION_FIX_START===
(No fixes needed — all issues resolved)
===SECTION_FIX_END===
```

After the fix block, output a friction report:

```
===FRICTION_START===
**Phase**: Gemini Review Fix
**Step**: {what you were doing}
**Friction Type**: NONE | TEXT_NOT_FOUND | ...
**Raw Error**: {actual issue or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if applicable, or "N/A"}
===FRICTION_END===
```

---

## Boundaries

- Do NOT write a review — that was already done
- Do NOT output ===REVIEW_START=== or ===FACTUAL_REVIEW_START=== blocks
- Do NOT use Edit tool or any other tool — you have NO tool access
- Output ONLY FIND/REPLACE pairs within the delimiters above
- Maximum 15 FIND/REPLACE pairs


============================================================
📎 Attached Data:
{"to_model": "gemini-3.1-pro-preview"}

🤖 Processing with Gemini (gemini-3.1-pro-preview) [sync, 15 min timeout]...
  [gemini] attempt 1/5, model=gemini-3.1-pro-preview, prompt=37213 chars: You are Gemini, participating in a collaboration with Claude. This is a message from Claude to you:  --- # Gemini Review Fix: Targeted Repair via FIND/REPLACE  > **You are an expert Ukrainian language...
```
===SECTION_FIX_START===
FILE: curriculum/l2-uk-en/a1/demonstratives-this-that.md
FIND:
# Demonstratives — The Grammar of This and That
REPLACE:
---
title: Demonstratives — The Grammar of This and That
---

# Demonstratives — The Grammar of This and That
---
FILE: curriculum/l2-uk-en/a1/demonstratives-this-that.md
FIND:
> **(На ринку / At the market)**
REPLACE:
> **(Ринок / Market)**
---
FILE: curriculum/l2-uk-en/a1/demonstratives-this-that.md
FIND:
> **(У кімнаті / In the room)**
>
> — **Цей** стілець зручний.
> — А **той** стілець?
> — **Той** старий, але добрий.
> — Я люблю **цю** кімнату!
REPLACE:
> **(Кімната / Room)**
>
> — **Цей** стілець зручний.
> — А **той** стілець?
> — **Той** старий, але добрий.
> — **Ця** кімната дуже гарна!
---
FILE: curriculum/l2-uk-en/a1/demonstratives-this-that.md
FIND:
- Ми говорили про **інший** будинок. **Той** будинок старий. — We were talking about a different building. That building is old. *(mentioned earlier)*
REPLACE:
- А **інший** будинок? **Той** будинок старий. — And the other building? That building is old. *(mentioned earlier)*
---
FILE: curriculum/l2-uk-en/a1/demonstratives-this-that.md
FIND:
Say each phrase out loud — your Ukrainian is becoming more natural with **кожний** новий крок (every new step)!
REPLACE:
Say each phrase out loud — your Ukrainian is becoming more natural. **Кожний** новий крок — це успіх (Every new step is a success)!
---
FILE: curriculum/l2-uk-en/a1/activities/demonstratives-this-that.yaml
FIND:
    - question: "How do you say 'these lakes' in Ukrainian?"
      options:
        - text: "ці озера"
          correct: true
        - text: "це озера"
          correct: false
        - text: "цей озера"
          correct: false
        - text: "ця озера"
          correct: false
      explanation: "Озера is plural, so it takes ці — the one plural form for all genders."
REPLACE:
    - question: "How do you say 'these lakes' in Ukrainian?"
      options:
        - text: "ці озера"
          correct: true
        - text: "це озера"
          correct: false
        - text: "цей озера"
          correct: false
        - text: "ця озера"
          correct: false
      explanation: "Озера is plural, so it takes ці — the one plural form for all genders."
    - question: "If you want to say 'that chair' (far away), which is correct?"
      options:
        - text: "той стілець"
          correct: true
        - text: "цей стілець"
          correct: false
        - text: "та стілець"
          correct: false
        - text: "те стілець"
          correct: false
      explanation: "Стілець is masculine, and for a far object we use той."
    - question: "Which demonstrative means 'those' for all plural nouns?"
      options:
        - text: "ті"
          correct: true
        - text: "ці"
          correct: false
        - text: "та"
          correct: false
        - text: "те"
          correct: false
      explanation: "Ті is the plural form of той/та/те, meaning 'those'."
    - question: "How do you say 'this city'?"
      options:
        - text: "це місто"
          correct: true
        - text: "те місто"
          correct: false
        - text: "ця місто"
          correct: false
        - text: "цей місто"
          correct: false
      explanation: "Місто is neuter, so 'this city' is це місто."
    - question: "If your friend mentions a book and you want to refer back to 'that book', you say:"
      options:
        - text: "та книга"
          correct: true
        - text: "ця книга"
          correct: false
        - text: "ті книга"
          correct: false
        - text: "те книга"
          correct: false
      explanation: "Книга is feminine, and 'that' (previously mentioned/distant) is та."
    - question: "Which demonstrative means 'these' for all plural nouns?"
      options:
        - text: "ці"
          correct: true
        - text: "ті"
          correct: false
        - text: "ця"
          correct: false
        - text: "це"
          correct: false
      explanation: "Ці is the plural form of цей/ця/це, meaning 'these'."
    - question: "To say 'this guy is my friend', you start with:"
      options:
        - text: "Цей хлопець"
          correct: true
        - text: "Той хлопець"
          correct: false
        - text: "Ця хлопець"
          correct: false
        - text: "Це хлопець"
          correct: false
      explanation: "Хлопець is masculine and 'this' is цей."
---
FILE: curriculum/l2-uk-en/a1/activities/demonstratives-this-that.yaml
FIND:
- type: match-up
  title: "This vs That — Proximity Pairs"
  instruction: "Match each 'this' phrase with its 'that' equivalent."
  pairs:
    - left: "цей стілець"
      right: "той стілець"
    - left: "ця вулиця"
      right: "та вулиця"
    - left: "це озеро"
      right: "те озеро"
    - left: "ці будинки"
      right: "ті будинки"
    - left: "цей торт"
      right: "той торт"
    - left: "ця книга"
      right: "та книга"
REPLACE:
- type: match-up
  title: "This vs That — Proximity Pairs"
  instruction: "Match each 'this' phrase with its 'that' equivalent."
  pairs:
    - left: "цей стілець"
      right: "той стілець"
    - left: "ця вулиця"
      right: "та вулиця"
    - left: "це озеро"
      right: "те озеро"
    - left: "ці будинки"
      right: "ті будинки"
    - left: "цей торт"
      right: "той торт"
    - left: "ця книга"
      right: "та книга"
    - left: "це місто"
      right: "те місто"
    - left: "ці студенти"
      right: "ті студенти"
    - left: "цей будинок"
      right: "той будинок"
    - left: "ця дівчина"
      right: "та дівчина"
===SECTION_FIX_END===

===FRICTION_START===
**Phase**: Gemini Review Fix
**Step**: Executing requested FIND/REPLACE changes
**Friction Type**: NONE
**Raw Error**: None
**Self-Correction**: N/A
**Proposed Tooling Fix**: N/A
===FRICTION_END===
```


────────────────────────────────────────
✅ Gemini finished (5845 chars)
✅ Message sent to Claude (ID: 26672)
✓ Message 26672 acknowledged
   Auto-acknowledged reply #26672 (stdout delivery — no inbox accumulation)
   ℹ️  No issue number in task_id 'demonstratives-this-that-review-fix-1' — skipping GH posting (review saved to orchestration/)
✓ Message 26671 acknowledged
