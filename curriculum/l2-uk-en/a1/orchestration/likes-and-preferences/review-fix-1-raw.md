✅ Message sent to Gemini (ID: 26645) [auto-acked: self-addressed]

🚀 Invoking Gemini to process message #26645...
📨 Message #26645
   From: gemini → To: gemini
   Type: query
   Task: likes-and-preferences-review-fix-1
   Time: 2026-03-18T04:57:34.215049+00:00

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
- Only modify these sections: Section `Мені подобається (I like)`, Section `Порівняння (Comparing likes)` and Vocabulary list, Section `Практика (Practice)`, Section `Я хочу (I want)`

### Finding 1: Calque / Incorrect Semantic Usage ("найкращий" instead of "улюблений")
**Location**: Section `Порівняння (Comparing likes)` and Vocabulary list
**Problem**: The content teaches `найкращий` (best) to mean "favourite" (e.g., "Мій найкращий колір — синій", "Яка твоя найкраща музика?"). This is a literal English translation. In Ukrainian, "улюблений" must be used for personal preferences. "Найкращий" means objectively the best.
**Required Fix**: Replace all instances of `найкращий` used for personal preference with `улюблений`, including the vocabulary list and the summary.
**Severity**: HIGH

### Finding 2: Service Context Register Error (Anglicism)
**Location**: Section `Практика (Practice)`
**Problem**: The café dialogue uses the direct translation "Що ви хочете?" ("Добрий день! Що ви хочете?"). This violates the A1 guidance, which flags this as an Anglicism/register mismatch in hospitality contexts and requires "Що бажаєте?".
**Required Fix**: Change "Що ви хочете?" to "Що бажаєте?" or "Що будете замовляти?" in the café dialogue.
**Severity**: HIGH

### Finding 3: Unnatural Dialogue Phrasing
**Location**: Section `Я хочу (I want)`
**Problem**: The café dialogue ends with "Добре! Смачний торт і кава." This sounds highly unnatural, like a literal translation of "Good! Tasty cake and coffee." A native speaker handing over food would use "ось" (here is).
**Required Fix**: Change to "Добре! Ось кава і смачний торт."
**Severity**: HIGH

### Finding 4: Typographical Word Split Causing False VESUM Error
**Location**: Section `Мені подобається (I like)`
**Problem**: The text bolds only the suffix of the word: `подобає**ться**`. This breaks markdown parsing and causes the audit script (VESUM) to fail on the isolated chunk `ться`.
**Required Fix**: Move the markdown bolding to encompass the entire word: `**подобається**` or remove the bolding entirely.
**Severity**: HIGH

---

## Plan Adherence Issues (Deterministic — MUST FIX)

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:quiz`
  - Expected: Plan requires ≥10 items
  - Actual: Activity has 6 items
  - Fix: Add 4 more items to 'quiz' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥8 items
  - Actual: Activity has 6 items
  - Fix: Add 2 more items to 'fill-in' activity


---

## Critical Issues Found

### Issue 1: Calque / Incorrect Semantic Usage ("найкращий" instead of "улюблений")
**Location**: Section `Порівняння (Comparing likes)` and Vocabulary list
**Problem**: The content teaches `найкращий` (best) to mean "favourite" (e.g., "Мій найкращий колір — синій", "Яка твоя найкраща музика?"). This is a literal English translation. In Ukrainian, "улюблений" must be used for personal preferences. "Найкращий" means objectively the best.
**Fix**: Replace all instances of `найкращий` used for personal preference with `улюблений`, including the vocabulary list and the summary.

### Issue 2: Service Context Register Error (Anglicism)
**Location**: Section `Практика (Practice)`
**Problem**: The café dialogue uses the direct translation "Що ви хочете?" ("Добрий день! Що ви хочете?"). This violates the A1 guidance, which flags this as an Anglicism/register mismatch in hospitality contexts and requires "Що бажаєте?".
**Fix**: Change "Що ви хочете?" to "Що бажаєте?" or "Що будете замовляти?" in the café dialogue.

### Issue 3: Unnatural Dialogue Phrasing
**Location**: Section `Я хочу (I want)`
**Problem**: The café dialogue ends with "Добре! Смачний торт і кава." This sounds highly unnatural, like a literal translation of "Good! Tasty cake and coffee." A native speaker handing over food would use "ось" (here is).
**Fix**: Change to "Добре! Ось кава і смачний торт."

### Issue 4: Typographical Word Split Causing False VESUM Error
**Location**: Section `Мені подобається (I like)`
**Problem**: The text bolds only the suffix of the word: `подобає**ться**`. This breaks markdown parsing and causes the audit script (VESUM) to fail on the isolated chunk `ться`. 
**Fix**: Move the markdown bolding to encompass the entire word: `**подобається**` or remove the bolding entirely.

---

## Ukrainian Language Issues

- `Я хочу слухати разом!` (Section: Порівняння): While understandable at A1, this is slightly unnatural as "слухати" usually demands a direct object (e.g., "слухати її разом" or "послухати разом").
- The pre-screen flagged `Мені`, `Тобі`, `каву`, etc. as `[MORPHOLOGICAL_VIOLATION]`. However, these are false positives for this specific module, as the curriculum plan authorizes teaching these as lexical chunks before formal case instruction.

---

## Fix Plan to Reach PASS

1. Replace all mentions of `найкращий` with `улюблений` when discussing favourites in the prose, examples, summary, and vocabulary list.
2. Correct the café register by replacing `Що ви хочете?` with `Що бажаєте?`.
3. Rewrite the unnatural `Смачний торт і кава` line in the café dialogue to use `ось`.
4. Fix the markdown bolding on `подобається` to prevent morphological scanner failures.

---

## Audit Failures (from automated re-audit)

```
⚠️ HYDRATION NOTE: Outline sums to 1300, exceeding word_target 1200
✨ Prose quality violations found: 1
❌ [INLINE_ENGLISH_IN_PROSE] Inline English translations in B1+ prose (3 occurrences): (Comparing likes), (Dative construction), (Nominative subject) — breaks immersion target
--- STRICT GATES (Level A1) ---
Pedagogy     ❌ 5 violations
📚 PEDAGOGICAL VIOLATIONS FOUND:
📝 RECOMMENDATION: UPDATE (patch fixes) (severity 50/100)
→ Revision recommended (severity 50/100)
→ 9 violations (significant)
→ 3 grammar-level violations (fundamental)
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/likes-and-preferences-audit.log for details)
⚠️  RAG verification found unverified words (see audit report)
--- VESUM WORD VERIFICATION FAILURES ---
These words were NOT found in the VESUM morphological dictionary.
Check if they are valid Ukrainian forms. Fix misspellings or Russianisms.
  ❌ `бл` (source: prose)
  ❌ `ться` (source: prose)
```

---

## File Contents

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/likes-and-preferences.md`

```markdown
You already know how to talk about what things are, describe them, ask questions, and say what you do. Now it's time for something personal — talking about what you **like**, what you **love**, and what you **want**. These are some of the most useful sentences in any language, and Ukrainian has its own elegant way of expressing them.

By the end of this module, you'll be able to say what appeals to you, tell someone what you love, express what you want, and ask others about their preferences — all in natural, everyday Ukrainian.

## Мені подобається (I like)

Here's something that surprises many English speakers: in Ukrainian, you don't "like" things the way you do in English. Instead of "I like coffee," Ukrainian says something closer to "Coffee is pleasing **to me**." The thing you like is actually the subject of the sentence!

The construction works like this: **Dative pronoun + подобається + what you like**. The word **подобається** means "is pleasing" or "appeals to." You don't need to worry about conjugating it for different people — it stays the same because it agrees with the thing that's liked, not with you.

Here are the Dative forms of the personal pronouns you already know:

| Pronoun | English meaning | Example |
|---------|-----------------|---------|
| я | "to me" | Мені подобається кава. |
| ти | "to you" | Тобі подобається музика. |
| він | "to him" | Йому подобається читати. |
| вона | "to her" | Їй подобається парк. |
| ми | "to us" | Нам подобається борщ. |
| ви | "to you" | Вам подобається книга? |
| вони | "to them" | Їм подобається школа. |

Don't try to memorize these as grammar rules — just learn them as fixed chunks, the way you'd learn a phrase like "excuse me." You'll meet the Dative case formally later. For now, just think "to me," "to you," and so on.

> [!tip] **Quick Win**
> You can already say what is pleasing! Just pick a word you know and put it before **подобається**: **Чай подобається.** — Tea is pleasing. Try it with any noun you've learned!

Now, what happens when more than one thing is pleasing? The verb changes to match:

- Кава **подобається**. — Coffee is pleasing. *(one thing)*
- Квіти **подобаються**. — Flowers are pleasing. *(many things)*

Notice the difference: **подобається** (singular) vs **подобаються** (plural). The verb agrees with what is liked.

You can also use this construction with verbs in the infinitive form — to say an action is pleasing:

- Читати подобається. — Reading is pleasing.
- Гуляти подобається? — Is walking pleasing?
- Співати подобається. — Singing is pleasing.

> [!warning] **Common Mistake**
> English speakers often try to say ~~"Я подобаюся кава"~~ — mapping "I like coffee" word for word. This is wrong! In Ukrainian, YOU are in the Dative case (which means "to me"), and the COFFEE is the subject: **Мені подобається кава.**

<!-- adapted from: Vashulenko, Grade 3, p.5 — "Що я люблю" theme -->

## Я люблю (I love)

While **подобається** describes something that appeals to you, **люблю** is stronger and more personal. It means "I love" or "I really enjoy." And unlike **подобається**, here YOU are the subject — just like in English.

The verb **любити** belongs to the Second Conjugation. Here is the full present-tense pattern:

| Person | Singular | Plural |
|--------|----------|--------|
| 1st | я **люблю** | ми **любимо** |
| 2nd | ти **любиш** | ви **любите** |
| 3rd | він/вона **любить** | вони **люблять** |

Notice how the first person singular (**люблю**) and third person plural (**люблять**) both have **-бл-** instead of **-б-**. This is a consonant change you've seen before with Second Conjugation verbs.

After **люблю**, the object takes the Accusative form. You'll study Accusative case formally in a later module. For inanimate masculine objects, the form looks exactly like the Nominative:

- Я люблю чай. — I love tea. *(чай)*
- Він любить борщ. — He loves borshch. *(борщ)*
- Ми любимо парк. — We love the park. *(парк)*
- Вони люблять торт. — They love cake. *(торт)*

You can also use **любити** with infinitives, just like **подобається**:

- Я люблю читати. — I love reading.
- Вона любить співати. — She loves singing.
- Ми любимо гуляти. — We love walking.

> [!note] **подобається vs люблю — What's the Difference?**
> Think of it this way: **подобається** is about a reaction — something appeals to you. **Люблю** is about a feeling — you actively love or enjoy something.
>
> - Цей парк подобається. — This park is appealing. *(reaction)*
> - Я люблю цей парк. — I love this park. *(feeling)*
>
> Both are natural. Use **подобається** when you discover something pleasant. Use **люблю** for things you know you love.

## Я хочу (I want)

The verb **хотіти** (to want) is one of the most useful verbs in Ukrainian. It belongs to the First Conjugation, with a simple consonant change where **т** becomes **ч**. It's very common, so you'll memorize its pattern quickly through use.

| Person | Singular | Plural |
|--------|----------|--------|
| 1st | я **хочу** | ми **хочемо** |
| 2nd | ти **хочеш** | ви **хочете** |
| 3rd | він/вона **хоче** | вони **хочуть** |

You can use **хочу** in two ways. First, with an infinitive — to say what you want **to do**:

- Я хочу їсти. — I want to eat.
- Я хочу піти. — I want to go.
- Вона хоче читати. — She wants to read.
- Ми хочемо гуляти. — We want to walk.

Second, with a noun — to say what you want **to have**. Just like with **любити**, the noun takes the Accusative form:

- Я хочу каву. — I want coffee.
- Ти хочеш чай? — Do you want tea?
- Він хоче борщ. — He wants borshch.
- Вони хочуть квиток. — They want a ticket.

> [!tip] **Three Constructions, Three Patterns**
> Here's your cheat sheet:
>
> | Construction | Structure | Example |
> |-------------|-----------|---------|
> | подобається | Dative + подобається + Nominative/infinitive | Мені подобається кава. |
> | люблю | Subject + люблю + Accusative/infinitive | Я люблю каву. |
> | хочу | Subject + хочу + Accusative/infinitive | Я хочу каву. |
>
> Notice: with **люблю** and **хочу**, YOU are the subject. With **подобається**, the THING you like is the subject.

How is **хочу** different from the other two? It's about desire or intention, not preference:

- Мені подобається кава. — I like coffee. *(general preference)*
- Я люблю каву. — I love coffee. *(strong, lasting feeling)*
- Я хочу каву. — I want coffee. *(right now, please!)*

> **(Кафе / Café)**
>
> — Привіт! Ви хочете каву?
> — Так, я хочу каву. Дякую!
> — А торт? Тобі подобається торт?
> — Так, дуже! Я люблю торт.
> — Добре! Ось кава і смачний торт.

## Порівняння (Comparing likes)

Now you have three powerful tools for talking about preferences. Let's use them in conversations! When you want to ask someone about their preferences, here are the key questions:

- Тобі подобається музика? — Do you like music?
- Ти любиш читати? — Do you love reading?
- Ви хочете каву? — Do you want coffee?
- А ти? — And you? *(informal)*
- А вам? — And you? *(formal)*

Notice that **тобі** and **ти** are both "you," but they appear in different constructions. With **подобається**, you use the Dative form **тобі** (to you). With **любиш** and **хочеш**, you use the Nominative **ти** because you are the subject of those verbs. This is the key structural difference between the three patterns.

These questions are your gateway to real conversations. Let's see them in action. Each dialogue below uses all three constructions in a natural setting — pay attention to which form of "you" appears in each sentence:

> **(Парк / Park)**
>
> — Мені подобається цей парк. А тобі?
> — Так, мені також подобається. Тут дуже гарно.
> — Ти любиш гуляти?
> — Так, я люблю гуляти. А ти?
> — Я також! Мені подобається гуляти разом.

In this dialogue, the first speaker uses **мені подобається** (Dative construction) to say the park appeals to them, then switches to **ти любиш** (Nominative subject) to ask about an activity. Both are natural ways to talk about liking things — the choice depends on whether you're describing a reaction or asking about a habit.

> **(Школа / School)**
>
> — Тобі подобається ця книга?
> — Ні, вона нудна. Я люблю цікаві книги.
> — А який фільм тобі подобається?
> — Мені подобаються цікаві фільми.

Here, the response **вона нудна** (it is boring) uses a short adjective sentence — a very common way to give opinions in Ukrainian. Notice also that the last line uses **подобаються** (plural) because **фільми** (films) is plural.

Notice how **цікавий** (interesting) and **нудний** (boring) help you express opinions. And the word **улюблений** (favourite) is perfect for talking about top preferences:

- Моя улюблена книга — це... — My favourite book is...
- Мій улюблений колір — синій. — My favourite colour is blue.
- Яка твоя улюблена музика? — What is your favourite music?

> [!culture] **What Ukrainians Love**
> Ukrainians love to share food and drinks with friends and family. A host will often ask **«Ви хочете чай чи каву?»** (Do you want tea or coffee?) rather than just asking what you like in general. **Борщ**, **вареники**, and **чай** are everyday favourites. Ukrainian culture is warm and hospitable. The Ukrainian proverb says: **«На колір і смак товариш не всяк»** — roughly, "Tastes differ" or "To each their own." This means everyone has their own unique taste and style. In Ukraine, people value these personal differences in food, music, and art.

Here's a longer dialogue that puts everything together. Try reading it through once, then go back and identify which of the three constructions each speaker uses:

> **(Дім / Home)**
>
> — Що ти любиш робити?
> — Я люблю читати і слухати музику.
> — Цікаво! А яка музика тобі подобається?
> — Мені подобається українська музика. А тобі?
> — Мені також! Я хочу слухати разом!
> — Добре! Ходімо!

## Практика (Practice)

Let's practise choosing the right construction. Remember:

- **Подобається** — something appeals to you (Dative + подобається)
- **Люблю** — you love or enjoy something (Subject + люблю)
- **Хочу** — you want something right now (Subject + хочу)

Try filling in the blanks in these mini-conversations:

- — ___ подобається кава? — Так, ___ подобається.  *(Answer: Тобі... мені)*
- — Ти ___ читати? — Так, я ___ читати.  *(Answer: любиш... люблю)*
- — Ви ___ чай? — Так, ми ___ чай.  *(Answer: хочете... хочемо)*

> [!practice] **Your Turn**
> Think about your own preferences. Can you say three things you like using each construction?
>
> 1. Мені подобається ___. *(something that appeals to you)*
> 2. Я люблю ___. *(something you love)*
> 3. Я хочу ___. *(something you want right now)*
>
> Now try asking a friend: **А тобі? Що ти любиш?**

Here's one final dialogue to bring it all together:

> **(Кафе / Café)**
>
> — Добрий день! Що бажаєте?
> — Я хочу каву, будь ласка. А ти?
> — Мені подобається чай. Я хочу чай.
> — Ви хочете торт? Він дуже смачний!
> — Так! Ми любимо смачний торт!

# Підсумок
Great job! You've learned three essential ways to talk about your preferences in Ukrainian. Let's celebrate what you can now do:

You can say what appeals to you with **мені подобається** — using the Dative construction where the thing you like is the subject. You can express love and enjoyment with **я люблю** — where you are the subject and the object takes the Accusative form. And you can express what you want right now with **я хочу** — followed by an infinitive or an Accusative noun.

You've also learned all seven Dative pronoun forms (**мені, тобі, йому, їй, нам, вам, їм**), how to use adjectives like **цікавий**, **нудний**, **смачний**, and **улюблений** to express opinions, and how to ask others about their preferences with **А тобі? Ти любиш...? Ви хочете...?**

**Self-check — can you do these?**

1. Say "I like music" using **подобається**.
2. Say "She loves coffee" using **любити**.
3. Say "We want to walk" using **хотіти**.
4. Ask someone "Do you like this book?" using **подобається**.

If you can do all four, you're ready to move on to the next module, where you'll learn about possessive pronouns — **mine**, **yours**, and more!
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/likes-and-preferences.yaml`

```yaml
- type: quiz
  title: "Which Construction?"
  instruction: "Choose the correct construction for each situation."
  items:
    - question: "You discover a beautiful park and want to say it appeals to you. Which construction do you use?"
      options:
        - text: "Мені подобається цей парк."
          correct: true
        - text: "Я люблю цей парк."
          correct: false
        - text: "Я хочу цей парк."
          correct: false
        - text: "Мені люблю цей парк."
          correct: false
      explanation: "When something appeals to you (a reaction), use the Dative + подобається construction."
    - question: "You want to tell someone that you love reading as a habit. Which sentence is correct?"
      options:
        - text: "Мені подобається читати."
          correct: false
        - text: "Я люблю читати."
          correct: true
        - text: "Я хочу читати."
          correct: false
        - text: "Читати люблю мені."
          correct: false
      explanation: "For a strong, lasting feeling about something you enjoy, use Я люблю + infinitive."
    - question: "You are at a cafe and want coffee right now. What do you say?"
      options:
        - text: "Мені подобається кава."
          correct: false
        - text: "Я люблю каву."
          correct: false
        - text: "Я хочу каву."
          correct: true
        - text: "Каву подобається."
          correct: false
      explanation: "For an immediate desire, use Я хочу + noun (Accusative)."
    - question: "In the sentence 'Мені подобається кава', what is the subject?"
      options:
        - text: "Мені"
          correct: false
        - text: "кава"
          correct: true
        - text: "подобається"
          correct: false
        - text: "There is no subject"
          correct: false
      explanation: "In the подобається construction, the thing that is pleasing (кава) is the subject."
    - question: "Which is the correct Dative form for 'to her'?"
      options:
        - text: "йому"
          correct: false
        - text: "їй"
          correct: true
        - text: "їм"
          correct: false
        - text: "вам"
          correct: false
      explanation: "Їй is the Dative form of вона (she), meaning 'to her'."
    - question: "What happens to подобається when you like multiple things?"
      options:
        - text: "It stays подобається"
          correct: false
        - text: "It changes to подобаються"
          correct: true
        - text: "It changes to подобаюся"
          correct: false
        - text: "It changes to подобатися"
          correct: false
      explanation: "With plural subjects, the verb becomes подобаються (plural agreement)."
    - question: "Which sentence correctly uses люблю with the right verb form?"
      options:
        - text: "Вони люблять борщ."
          correct: true
        - text: "Вони любить борщ."
          correct: false
        - text: "Вони любимо борщ."
          correct: false
        - text: "Вони люблю борщ."
          correct: false
      explanation: "Вони (they) takes люблять — the third person plural form of любити."
    - question: "How do you say 'She wants to eat' in Ukrainian?"
      options:
        - text: "Вона хочу їсти."
          correct: false
        - text: "Вона хоче їсти."
          correct: true
        - text: "Вона хочемо їсти."
          correct: false
        - text: "Їй хоче їсти."
          correct: false
      explanation: "Вона (she) takes хоче — the third person singular of хотіти."
    - question: "Which construction makes YOU the subject of the sentence?"
      options:
        - text: "Мені подобається"
          correct: false
        - text: "Я люблю"
          correct: true
        - text: "Both make you the subject"
          correct: false
        - text: "Neither makes you the subject"
          correct: false
      explanation: "With люблю and хочу, YOU (я) are the subject. With подобається, the THING you like is the subject."
    - question: "What is the difference between подобається and люблю?"
      options:
        - text: "подобається is a reaction, люблю is a strong feeling"
          correct: true
        - text: "They mean exactly the same thing"
          correct: false
        - text: "подобається is formal, люблю is informal"
          correct: false
        - text: "подобається is for people, люблю is for things"
          correct: false
      explanation: "Подобається describes a reaction (something appeals to you), while люблю expresses an active, lasting feeling."

- type: fill-in
  title: "Complete the Sentence"
  instruction: "Choose the correct word to complete each sentence about preferences."
  items:
    - sentence: "___ подобається музика."
      answer: "Мені"
      options: ["Мені", "Я", "Мене", "Моя"]
      explanation: "The подобається construction uses the Dative form: Мені (to me)."
    - sentence: "Ти ___ читати."
      answer: "любиш"
      options: ["любиш", "люблю", "любить", "люблять"]
      explanation: "Ти (you, singular) takes любиш — the second person singular form."
    - sentence: "Ми ___ каву."
      answer: "хочемо"
      options: ["хочемо", "хочу", "хочуть", "хоче"]
      explanation: "Ми (we) takes хочемо — the first person plural form of хотіти."
    - sentence: "___ подобається цей парк."
      answer: "Тобі"
      options: ["Тобі", "Ти", "Тебе", "Твій"]
      explanation: "With подобається, use the Dative form: Тобі (to you)."
    - sentence: "Вона ___ співати."
      answer: "любить"
      options: ["любить", "люблю", "любиш", "любимо"]
      explanation: "Вона (she) takes любить — the third person singular of любити."
    - sentence: "Вони ___ борщ."
      answer: "хочуть"
      options: ["хочуть", "хочу", "хоче", "хочемо"]
      explanation: "Вони (they) takes хочуть — the third person plural of хотіти."
    - sentence: "___ подобається гуляти."
      answer: "Нам"
      options: ["Нам", "Ми", "Нас", "Наш"]
      explanation: "With подобається, use the Dative form: Нам (to us)."
    - sentence: "Він ___ торт."
      answer: "любить"
      options: ["любить", "люблю", "любиш", "люблять"]
      explanation: "Він (he) takes любить — the third person singular of любити."

- type: match-up
  title: "Match Construction to Meaning"
  instruction: "Match each Ukrainian sentence to its English meaning."
  pairs:
    - left: "Мені подобається кава."
      right: "Coffee appeals to me."
    - left: "Я люблю каву."
      right: "I love coffee."
    - left: "Я хочу каву."
      right: "I want coffee."
    - left: "Тобі подобається музика?"
      right: "Does music appeal to you?"
    - left: "Ти любиш читати?"
      right: "Do you love reading?"
    - left: "Ви хочете чай?"
      right: "Do you want tea?"
    - left: "Їй подобається парк."
      right: "The park appeals to her."
    - left: "Він любить борщ."
      right: "He loves borshch."
    - left: "Ми хочемо гуляти."
      right: "We want to walk."
    - left: "Їм подобаються квіти."
      right: "Flowers appeal to them."

- type: unjumble
  title: "Put the Words in Order"
  instruction: "Arrange the words to form a correct Ukrainian sentence."
  items:
    - words: ["подобається", "Мені", "кава"]
      answer: "Мені подобається кава."
    - words: ["люблю", "читати", "Я"]
      answer: "Я люблю читати."
    - words: ["хочу", "Я", "їсти"]
      answer: "Я хочу їсти."
    - words: ["подобається", "Тобі", "музика", "?"]
      answer: "Тобі подобається музика?"
    - words: ["любить", "Вона", "співати"]
      answer: "Вона любить співати."
    - words: ["хочете", "Ви", "чай", "?"]
      answer: "Ви хочете чай?"

- type: true-false
  title: "True or False?"
  instruction: "Decide whether each statement about Ukrainian preference constructions is true or false."
  items:
    - statement: "In the sentence 'Мені подобається кава', the word кава is the subject."
      correct: true
      explanation: "Correct! With подобається, the thing that is pleasing (кава) is the grammatical subject."
    - statement: "The Dative form of я is мене."
      correct: false
      explanation: "The Dative form of я is мені (to me). Мене is the Accusative/Genitive form."
    - statement: "Любити is a Second Conjugation verb."
      correct: true
      explanation: "Correct! Любити follows the Second Conjugation pattern: люблю, любиш, любить..."
    - statement: "You can use подобається with an infinitive, for example: Читати подобається."
      correct: true
      explanation: "Correct! Подобається works with both nouns and infinitives."
    - statement: "The verb хотіти follows a regular First Conjugation pattern."
      correct: false
      explanation: "Хотіти is irregular — it doesn't follow standard First or Second Conjugation patterns neatly."
    - statement: "When you like multiple things, подобається changes to подобаються."
      correct: true
      explanation: "Correct! Подобається (singular) becomes подобаються (plural) to agree with a plural subject."
    - statement: "In 'Я люблю каву', the word я is in the Dative case."
      correct: false
      explanation: "With люблю, я is the Nominative subject — YOU are the one loving. Dative is used with подобається."
    - statement: "Хочу can be followed by either an infinitive or a noun."
      correct: true
      explanation: "Correct! Я хочу їсти (infinitive) and Я хочу каву (noun) are both valid."

- type: group-sort
  title: "Sort by Construction"
  instruction: "Sort each sentence into the correct construction group."
  groups:
    - name: "подобається (Dative construction)"
      items:
        - "Мені подобається чай."
        - "Тобі подобається парк?"
        - "Їй подобається музика."
        - "Нам подобається гуляти."
    - name: "люблю (I love/enjoy)"
      items:
        - "Я люблю читати."
        - "Вона любить співати."
        - "Ми любимо борщ."
        - "Вони люблять торт."
    - name: "хочу (I want)"
      items:
        - "Я хочу каву."
        - "Він хоче їсти."
        - "Ви хочете чай?"
        - "Ми хочемо гуляти."

- type: quiz
  title: "Dative Pronouns"
  instruction: "Choose the correct Dative pronoun for each sentence."
  items:
    - question: "Which Dative pronoun completes '___ подобається борщ'? (to him)"
      options:
        - text: "Йому"
          correct: true
        - text: "Він"
          correct: false
        - text: "Його"
          correct: false
        - text: "Їй"
          correct: false
      explanation: "Йому is the Dative form of він (he), meaning 'to him'."
    - question: "Which Dative pronoun means 'to them'?"
      options:
        - text: "Нам"
          correct: false
        - text: "Вам"
          correct: false
        - text: "Їм"
          correct: true
        - text: "Їй"
          correct: false
      explanation: "Їм is the Dative form of вони (they), meaning 'to them'."
    - question: "Which Dative pronoun completes '___ подобається книга'? (to us)"
      options:
        - text: "Нам"
          correct: true
        - text: "Ми"
          correct: false
        - text: "Нас"
          correct: false
        - text: "Вам"
          correct: false
      explanation: "Нам is the Dative form of ми (we), meaning 'to us'."
    - question: "'___ подобається школа.' Fill in with 'to you' (formal)."
      options:
        - text: "Тобі"
          correct: false
        - text: "Вам"
          correct: true
        - text: "Ви"
          correct: false
        - text: "Вас"
          correct: false
      explanation: "Вам is the formal Dative form, meaning 'to you (formal/plural)'."
    - question: "Which pair shows the correct Dative forms for 'to me' and 'to you' (informal)?"
      options:
        - text: "мені / тобі"
          correct: true
        - text: "я / ти"
          correct: false
        - text: "мене / тебе"
          correct: false
        - text: "мій / твій"
          correct: false
      explanation: "Мені (to me) and тобі (to you) are the Dative forms of я and ти."
    - question: "Which Dative pronoun completes '___ подобається торт'? (to her)"
      options:
        - text: "Йому"
          correct: false
        - text: "Їм"
          correct: false
        - text: "Їй"
          correct: true
        - text: "Вам"
          correct: false
      explanation: "Їй is the Dative form of вона (she), meaning 'to her'."

- type: fill-in
  title: "Verb Conjugation Practice"
  instruction: "Choose the correct verb form for each sentence."
  items:
    - sentence: "Я ___ каву."
      answer: "люблю"
      options: ["люблю", "любиш", "любить", "люблять"]
      explanation: "Я (I) takes люблю — the first person singular of любити."
    - sentence: "Ми ___ гуляти."
      answer: "любимо"
      options: ["любимо", "люблю", "любиш", "люблять"]
      explanation: "Ми (we) takes любимо — the first person plural of любити."
    - sentence: "Ти ___ чай?"
      answer: "хочеш"
      options: ["хочеш", "хочу", "хоче", "хочуть"]
      explanation: "Ти (you) takes хочеш — the second person singular of хотіти."
    - sentence: "Вони ___ торт."
      answer: "люблять"
      options: ["люблять", "люблю", "любить", "любимо"]
      explanation: "Вони (they) takes люблять — the third person plural of любити."
    - sentence: "Він ___ їсти."
      answer: "хоче"
      options: ["хоче", "хочу", "хочеш", "хочемо"]
      explanation: "Він (he) takes хоче — the third person singular of хотіти."
    - sentence: "Ви ___ читати?"
      answer: "любите"
      options: ["любите", "люблю", "любиш", "любимо"]
      explanation: "Ви (you, formal/plural) takes любите — the second person plural of любити."
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/likes-and-preferences.yaml`

```yaml
items:
  - lemma: "подобатися"
    translation: "to like, to appeal to"
    pos: "verb"
    aspect: "imperfective"
    notes: "Dative construction: Мені подобається кава"
    usage: "Мені подобається музика."
  - lemma: "любити"
    translation: "to love, to enjoy"
    pos: "verb"
    aspect: "imperfective"
    notes: "Second Conjugation; consonant change б→бл in люблю/люблять"
    usage: "Я люблю читати."
  - lemma: "хотіти"
    translation: "to want"
    pos: "verb"
    aspect: "imperfective"
    notes: "Irregular conjugation: хочу, хочеш, хоче, хочемо, хочете, хочуть"
    usage: "Я хочу каву."
  - lemma: "кава"
    translation: "coffee"
    pos: "noun"
    gender: "f"
    usage: "Мені подобається кава."
  - lemma: "музика"
    translation: "music"
    pos: "noun"
    gender: "f"
    usage: "Тобі подобається музика?"
  - lemma: "читати"
    translation: "to read"
    pos: "verb"
    aspect: "imperfective"
    usage: "Я люблю читати."
  - lemma: "їсти"
    translation: "to eat"
    pos: "verb"
    aspect: "imperfective"
    usage: "Я хочу їсти."
  - lemma: "піти"
    translation: "to go (on foot, perfective)"
    pos: "verb"
    aspect: "perfective"
    usage: "Я хочу піти."
  - lemma: "цікавий"
    translation: "interesting"
    pos: "adjective"
    usage: "Мені подобаються цікаві книги."
  - lemma: "нудний"
    translation: "boring"
    pos: "adjective"
    usage: "Ця книга нудна."
  - lemma: "смачний"
    translation: "tasty, delicious"
    pos: "adjective"
    usage: "Торт дуже смачний!"
  - lemma: "улюблений"
    translation: "favourite"
    pos: "adjective"
    notes: "Used to express top preferences"
    usage: "Мій улюблений колір — синій."
  - lemma: "гуляти"
    translation: "to walk, to stroll"
    pos: "verb"
    aspect: "imperfective"
    usage: "Ми любимо гуляти."
  - lemma: "співати"
    translation: "to sing"
    pos: "verb"
    aspect: "imperfective"
    usage: "Вона любить співати."
  - lemma: "чай"
    translation: "tea"
    pos: "noun"
    gender: "m"
    usage: "Ти хочеш чай?"
  - lemma: "борщ"
    translation: "borshch (beet soup)"
    pos: "noun"
    gender: "m"
    usage: "Він любить борщ."
  - lemma: "торт"
    translation: "cake"
    pos: "noun"
    gender: "m"
    usage: "Ми любимо смачний торт!"
  - lemma: "парк"
    translation: "park"
    pos: "noun"
    gender: "m"
    usage: "Мені подобається цей парк."
  - lemma: "книга"
    translation: "book"
    pos: "noun"
    gender: "f"
    usage: "Тобі подобається ця книга?"
  - lemma: "слухати"
    translation: "to listen"
    pos: "verb"
    aspect: "imperfective"
    usage: "Я люблю слухати музику."
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
  [gemini] attempt 1/5, model=gemini-3.1-pro-preview, prompt=39736 chars: You are Gemini, participating in a collaboration with Claude. This is a message from Claude to you:  --- # Gemini Review Fix: Targeted Repair via FIND/REPLACE  > **You are an expert Ukrainian language...
```

  [watchdog] Output resumed after 170s stall
===SECTION_FIX_START===
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/likes-and-preferences.md
FIND:
Notice how the first person singular (**люблю**) and third person plural (**люблять**) both have **-бл-** instead of **-б-**. This is a consonant change you've seen before with Second Conjugation verbs.
REPLACE:
Notice how the first person singular (**люблю**) and third person plural (**люблять**) both have an inserted **л** after the **б**. This is a consonant change you've seen before with Second Conjugation verbs.
---
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/likes-and-preferences.md
FIND:
## Порівняння (Comparing likes)
REPLACE:
## Порівняння
---
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/likes-and-preferences.md
FIND:
In this dialogue, the first speaker uses **мені подобається** (Dative construction) to say the park appeals to them, then switches to **ти любиш** (Nominative subject) to ask about an activity. Both are natural ways to talk about liking things — the choice depends on whether you're describing a reaction or asking about a habit.
REPLACE:
In this dialogue, the first speaker uses **мені подобається** to say the park appeals to them, then switches to **ти любиш** to ask about an activity. Both are natural ways to talk about liking things — the choice depends on whether you're describing a reaction or asking about a habit.
---
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/likes-and-preferences.md
FIND:
> — Мені також! Я хочу слухати разом!
REPLACE:
> — Мені також! Я хочу послухати разом!
---
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/likes-and-preferences.yaml
FIND:
    - question: "Which Dative pronoun completes '___ подобається торт'? (to her)"
      options:
        - text: "Йому"
          correct: false
        - text: "Їм"
          correct: false
        - text: "Їй"
          correct: true
        - text: "Вам"
          correct: false
      explanation: "Їй is the Dative form of вона (she), meaning 'to her'."

- type: fill-in
REPLACE:
    - question: "Which Dative pronoun completes '___ подобається торт'? (to her)"
      options:
        - text: "Йому"
          correct: false
        - text: "Їм"
          correct: false
        - text: "Їй"
          correct: true
        - text: "Вам"
          correct: false
      explanation: "Їй is the Dative form of вона (she), meaning 'to her'."
    - question: "What is the Dative form of 'я' (I)?"
      options:
        - text: "мені"
          correct: true
        - text: "мене"
          correct: false
        - text: "моя"
          correct: false
        - text: "мій"
          correct: false
      explanation: "The Dative form of я is мені."
    - question: "What is the Dative form of 'ти' (you, informal)?"
      options:
        - text: "тобі"
          correct: true
        - text: "тебе"
          correct: false
        - text: "твоя"
          correct: false
        - text: "твій"
          correct: false
      explanation: "The Dative form of ти is тобі."
    - question: "Which pronoun completes the sentence: '___ подобається чай'? (We like tea)"
      options:
        - text: "Нам"
          correct: true
        - text: "Ми"
          correct: false
        - text: "Вам"
          correct: false
        - text: "Їм"
          correct: false
      explanation: "For 'we like' using подобається, use the Dative form Нам."
    - question: "Which pronoun completes the sentence: '___ подобається музика'? (He likes music)"
      options:
        - text: "Йому"
          correct: true
        - text: "Він"
          correct: false
        - text: "Їй"
          correct: false
        - text: "Його"
          correct: false
      explanation: "For 'he likes' using подобається, use the Dative form Йому."

- type: fill-in
---
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/likes-and-preferences.yaml
FIND:
    - sentence: "Ви ___ читати?"
      answer: "любите"
      options: ["любите", "люблю", "любиш", "любимо"]
      explanation: "Ви (you, formal/plural) takes любите — the second person plural of любити."
REPLACE:
    - sentence: "Ви ___ читати?"
      answer: "любите"
      options: ["любите", "люблю", "любиш", "любимо"]
      explanation: "Ви (you, formal/plural) takes любите — the second person plural of любити."
    - sentence: "Я ___ читати."
      answer: "хочу"
      options: ["хочу", "хочеш", "хоче", "хочемо"]
      explanation: "Я (I) takes хочу — the first person singular of хотіти."
    - sentence: "Вони ___ співати."
      answer: "хочуть"
      options: ["хочуть", "хочу", "хоче", "хочемо"]
      explanation: "Вони (they) takes хочуть — the third person plural of хотіти."
===SECTION_FIX_END===

===FRICTION_START===
**Phase**: Gemini Review Fix
**Step**: Applying FIND/REPLACE fixes based on review and audit failures
**Friction Type**: TEXT_NOT_FOUND
**Raw Error**: Issues 1, 2, 3, and 4 (concerning "найкращий", "Що ви хочете?", "Смачний торт і кава", and "подобає**ться**") were not found in the provided file contents. It appears they were already fixed prior to this step.
**Self-Correction**: Skipped applying FIND/REPLACE for those specific issues to prevent the pipeline from failing due to text not found errors. Focused on the remaining active Audit Failures (undercounts, inline English, and the `бл` morphological violation) and the unnatural phrasing of "слухати разом".
**Proposed Tooling Fix**: N/A
===FRICTION_END===


────────────────────────────────────────
✅ Gemini finished (5605 chars)
✅ Message sent to Claude (ID: 26646)
✓ Message 26646 acknowledged
   Auto-acknowledged reply #26646 (stdout delivery — no inbox accumulation)
   ℹ️  No issue number in task_id 'likes-and-preferences-review-fix-1' — skipping GH posting (review saved to orchestration/)
✓ Message 26645 acknowledged
