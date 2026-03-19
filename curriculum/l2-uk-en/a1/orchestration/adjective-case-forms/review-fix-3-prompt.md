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



**NOTE: 10 inline fix(es) from the review have ALREADY been applied to the files. Do NOT re-apply those fixes. Read the CURRENT file contents carefully — they reflect the post-fix state. Only fix issues that are still present in the current files.**

## Plan Adherence Issues (Deterministic — MUST FIX)

- **[HIGH] VOCAB_NOT_IN_CONTENT** in `vocabulary`
  - Expected: Required word 'красивий' must appear in content
  - Actual: Word not found (after stress-mark normalization)
  - Fix: Add 'красивий' to an appropriate section in the content


---

## Review Findings (targeted fix required)

**CONSTRAINTS:**
- Fix ONLY the issues listed below
- Do NOT rewrite surrounding text
- Preserve word count and structure
- Only modify these sections: Entire module, especially Section "Прикметник у Знахідному (Adj in Accusative)", Line 144, Line 4, Section "Прикметник у Знахідному (Adj in Accusative)", Line 89, Section "Порівняння форм (Comparing forms)", Lines 6, 48, 58, 81 — four instances of "Let us", Lines 6, 48, 81, 101, 128

### Finding 1: Factual Error — Incorrect Ending Identification (HIGH)
**Location**: Line 89, Section "Порівняння форм (Comparing forms)"
**Problem**: This is factually wrong within the module's own scope. The ending **-ій** is taught in this very module as the **feminine Locative** marker (у новій, у старій, в українській). Telling learners "-ій = masculine Nominative" will directly contradict what they learned 30 lines earlier. The ending -ій on adjectives is ambiguous between masculine Nominative (синій) and feminine Locative (новій), and should NOT be presented as a definitive case marker.
**Required Fix**: Remove "-ій" from this claim, or rewrite to acknowledge the ambiguity: "When you hear the ending **-ий**, you know it's likely a masculine Nominative form."
**Severity**: HIGH

### Finding 2: LLM Filler — "beautiful" Overuse (MEDIUM)
**Location**: Lines 6, 48, 81, 101, 128
**Problem**: "beautiful" is used 6 times as a filler adjective applied to grammar concepts (endings, examples, process). This is unnatural — no human tutor calls adjective endings "beautiful" three times. This is a clear LLM fingerprint.
**Required Fix**: Remove or replace with varied, natural alternatives. E.g., "these endings" (no adjective needed), "helpful examples", "natural part of the process".
**Severity**: HIGH

### Finding 3: Missing Learning Objectives Preview (MEDIUM)
**Location**: Line 4, Section "Прикметник у Знахідному (Adj in Accusative)"
**Problem**: The module opens with a warm welcome but never states "Today you'll learn to..." — a required element for beginner safety (PREVIEW in the beginner lesson arc). The learner doesn't know what to expect.
**Required Fix**: Add a clear preview after the opening sentence: "Today you'll learn how adjectives change their endings in two important cases — the Accusative (for direct objects) and the Locative (for locations)."
**Severity**: HIGH

### Finding 4: Overly Formal English — "Let us" (LOW)
**Location**: Lines 6, 48, 58, 81 — four instances of "Let us"
**Problem**: A1 guidelines say contractions are allowed and encouraged for warmth. "Let us" is stilted and formal — a patient tutor would say "Let's".
**Required Fix**: Replace all "Let us" with "Let's".
**Severity**: HIGH

### Finding 5: Підсумок as H1 Instead of H2 (LOW)
**Location**: Line 144
**Problem**: All other sections use H2 (`##`). The summary uses H1 (`#`), breaking structural consistency. This may cause rendering issues on the Starlight site.
**Required Fix**: Change to `## Підсумок`.
**Severity**: HIGH

### Finding 6: Missing Fashion Advisor Persona (MEDIUM)
**Location**: Entire module, especially Section "Прикметник у Знахідному (Adj in Accusative)"
**Problem**: Plan persona is "Fashion Advisor". Research notes explicitly suggest clothing examples (красивий светр, нову сукню, у модному магазині). The content mentions "fashion advisor hats" once in line 4 and then uses zero clothing/fashion vocabulary. This is a missed plan directive.
**Required Fix**: Replace 2-3 generic examples with fashion-themed ones. E.g., in the Accusative section: "Я купую нову сукню" (I'm buying a new dress), "Я бачу красивий светр" (I see a beautiful sweater).
**Severity**: HIGH

---

## Critical Issues Found

### Issue 1: Factual Error — Incorrect Ending Identification (HIGH)
- **Location**: Line 89, Section "Порівняння форм (Comparing forms)"
- **Original**: 「When you hear the ending -ий or -ій, you immediately know you are dealing with a masculine subject in the Nominative case.」
- **Problem**: This is factually wrong within the module's own scope. The ending **-ій** is taught in this very module as the **feminine Locative** marker (у новій, у старій, в українській). Telling learners "-ій = masculine Nominative" will directly contradict what they learned 30 lines earlier. The ending -ій on adjectives is ambiguous between masculine Nominative (синій) and feminine Locative (новій), and should NOT be presented as a definitive case marker.
- **Fix**: Remove "-ій" from this claim, or rewrite to acknowledge the ambiguity: "When you hear the ending **-ий**, you know it's likely a masculine Nominative form."

### Issue 2: LLM Filler — "beautiful" Overuse (MEDIUM)
- **Location**: Lines 6, 48, 81, 101, 128
- **Original**: 「To truly master these beautiful endings, it is incredibly helpful to see them side-by-side.」 (line 81) / 「Practice is the secret to making these beautiful endings flow naturally in your conversation.」 (line 128) / 「Learning a new language is a journey full of trial and error, and making mistakes is a beautiful part of the process!」 (line 101)
- **Problem**: "beautiful" is used 6 times as a filler adjective applied to grammar concepts (endings, examples, process). This is unnatural — no human tutor calls adjective endings "beautiful" three times. This is a clear LLM fingerprint.
- **Fix**: Remove or replace with varied, natural alternatives. E.g., "these endings" (no adjective needed), "helpful examples", "natural part of the process".

### Issue 3: Missing Learning Objectives Preview (MEDIUM)
- **Location**: Line 4, Section "Прикметник у Знахідному (Adj in Accusative)"
- **Problem**: The module opens with a warm welcome but never states "Today you'll learn to..." — a required element for beginner safety (PREVIEW in the beginner lesson arc). The learner doesn't know what to expect.
- **Fix**: Add a clear preview after the opening sentence: "Today you'll learn how adjectives change their endings in two important cases — the Accusative (for direct objects) and the Locative (for locations)."

### Issue 4: Overly Formal English — "Let us" (LOW)
- **Location**: Lines 6, 48, 58, 81 — four instances of "Let us"
- **Problem**: A1 guidelines say contractions are allowed and encouraged for warmth. "Let us" is stilted and formal — a patient tutor would say "Let's".
- **Fix**: Replace all "Let us" with "Let's".

### Issue 5: Підсумок as H1 Instead of H2 (LOW)
- **Location**: Line 144
- **Original**: `# Підсумок`
- **Problem**: All other sections use H2 (`##`). The summary uses H1 (`#`), breaking structural consistency. This may cause rendering issues on the Starlight site.
- **Fix**: Change to `## Підсумок`.

### Issue 6: Missing Fashion Advisor Persona (MEDIUM)
- **Location**: Entire module, especially Section "Прикметник у Знахідному (Adj in Accusative)"
- **Problem**: Plan persona is "Fashion Advisor". Research notes explicitly suggest clothing examples (красивий светр, нову сукню, у модному магазині). The content mentions "fashion advisor hats" once in line 4 and then uses zero clothing/fashion vocabulary. This is a missed plan directive.
- **Fix**: Replace 2-3 generic examples with fashion-themed ones. E.g., in the Accusative section: "Я купую нову сукню" (I'm buying a new dress), "Я бачу красивий светр" (I see a beautiful sweater).

---

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 89 | 「When you hear the ending -ий or -ій, you immediately know you are dealing with a masculine subject in the Nominative case.」 | "When you hear the ending **-ий**, it often signals a masculine Nominative form. But remember — **-ій** can be either masculine Nominative (синій) or feminine Locative (новій)!" | Factual Error |

---

## Fix Plan to Reach 9/10 (REQUIRED — score < 9.0)

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. Line 89: Correct the false claim that "-ій" = masculine Nominative. Rewrite to acknowledge that -ій is ambiguous (masc Nom for soft-group vs fem Locative).

**Expected score after fix:** 9/10

### LLM Fingerprint: 7/10 → 8/10
**What to fix:**
1. Remove 4 of 6 uses of "beautiful" as filler (lines 48, 81, 101, 128). Keep it only where it refers to actual beauty (line 6 "beautiful item", line 97 "beautiful city" = красиве місто).
2. Replace 「You have done an absolutely phenomenal job today!」 (line 145) with a warmer, more natural closing.
3. Replace 「The case system is the heartbeat of Ukrainian grammar」 (line 4) with something concrete.

**Expected score after fix:** 8/10

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Add learning objectives preview after opening sentence.
2. Replace "Let us" with "Let's" (4 instances).
3. Fix `# Підсумок` to `## Підсумок`.

**Expected score after fix:** 9/10

### Pedagogy: 8/10 → 9/10
**What to fix:**
1. Add 2-3 fashion/clothing examples to fulfill the Fashion Advisor persona.
2. Consider adding the Ukrainian riddle from research notes as a cultural hook.

**Expected score after fix:** 9/10

### Projected Overall After Fixes
(9×1.5 + 8×1.1 + 9×1.2 + 9×1.3 + 8×1.3 + 8×1.0 + 9×1.5) / 8.9
= (13.5 + 8.8 + 10.8 + 11.7 + 10.4 + 8.0 + 13.5) / 8.9
= 76.7 / 8.9 = **8.6/10**

---

## Audit Failures (from automated re-audit)

```
Типові помилки (Common errors)                275 /  175  ✅ (+100)
--- STRICT GATES (Level A1) ---
Pedagogy     ❌ 1 violations
📚 PEDAGOGICAL VIOLATIONS FOUND:
📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
→ 2 violations (minor)
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/adjective-case-forms-audit.log for details)
⚠️  RAG verification found unverified words (see audit report)
--- VESUM WORD VERIFICATION FAILURES ---
These words were NOT found in the VESUM morphological dictionary.
Check if they are valid Ukrainian forms. Fix misspellings or Russianisms.
  ❌ `ий` (source: prose)
  ❌ `ьому` (source: prose)
  ❌ `ій` (source: prose)
```

---

## File Contents (for reference)

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/adjective-case-forms.md`

```markdown
<!-- adapted from: Avramenko, Grade 6 -->
## Прикметник у Знахідному (Adj in Accusative)

Welcome back! It is so wonderful to see you continuing your journey with the Ukrainian language. Today, we are going to put on our fashion advisor hats and learn how to describe things in action. When you go shopping, order food, or talk about what you see around you, you need adjectives. You already know that adjectives match the gender of the noun they describe. Now, we are going to see what happens to these descriptive words when the noun goes into a different grammatical case. The case system is central to Ukrainian grammar, and mastering it gives you real freedom to express yourself. **Today you'll learn** how adjectives change their endings in two important cases — the Accusative (for direct objects) and the Locative (for locations).

Let's start with the Accusative case, which we use for the direct object of a sentence. Imagine you are pointing out a new film you want to watch or a beautiful item you want to buy. The great news here is that for inanimate masculine and neuter nouns, the adjective does not change at all! The Accusative form is exactly the same as the Nominative form.

> - **новий фільм** — **Я дивлюся новий фільм.** (I am watching a new film.)
> - **нове кафе** — **Я бачу нове кафе.** (I see a new cafe.)
> - **великий парк** — **Я люблю великий парк.** (I love the big park.)
> - **красивий светр** — **Я бачу красивий светр.** (I see a beautiful sweater.)

This means that half of your work is already done! When you talk about non-living masculine or neuter objects, you can simply use the dictionary form of the adjective.

> [!tip]
> Think of inanimate masculine and neuter adjectives as "lazy" in the Accusative case. They just sit there in their dictionary form, relaxing, while the feminine adjectives do all the work!

However, feminine nouns are a bit more dynamic. When a feminine noun goes into the Accusative case, its adjective must match it. The typical ending **-а** transforms into **-у**. 

> - **нова сукня** → **Я купую нову сукню.** (I am buying a new dress.)
> - **смачна кава** → **Я п'ю смачну каву.** (I am drinking tasty coffee.)
> - **красива дівчина** → **Я бачу красиву дівчину.** (I see a beautiful girl.)
> - **маленька проблема** → **Я маю маленьку проблему.** (I have a small problem.)

Now, we must pay attention to a critical distinction: living versus non-living. For masculine animate nouns (living people or animals), the Accusative form actually borrows the ending from the Genitive case. This means the adjective takes the ending **-ого**. This rule is incredibly important because the living status of the noun determines the adjective form completely. It might feel strange at first to ask if a noun is alive before you describe it, but this becomes second nature very quickly. You are basically showing respect to living beings by giving them a special grammatical form!

> - **новий студент** → **Я бачу нового студента.** (I see a new student.)
> - **молодий чоловік** → **Я знаю молодого чоловіка.** (I know a young man.)
> - **старий кіт** → **Я годую старого кота.** (I feed the old cat.)


By keeping this simple animate versus inanimate rule in mind, you will always know exactly how to style your adjectives in the Accusative case.

> 🎬 **Діалог: У модному магазині**
>
> — **Добрий день! Я шукаю нову сукню.** (Good day! I am looking for a new dress.)
> — **У нас є красива нова сукня.** (We have a beautiful new dress.)
> — **А є красивий светр?** (And is there a beautiful sweater?)
> — **Так, ось великий український светр.** (Yes, here is a big Ukrainian sweater.)
> — **Добре, я беру нову сукню. Дякую!** (Good, I am taking the new dress. Thank you!)
> — **Будь ласка! Гарного дня!** (You are welcome! Have a good day!)


## Прикметник у Місцевому (Adj in Locative)

Now that we know how to interact with objects directly, let's talk about where things are. As your trusty language guide, I want you to feel perfectly comfortable navigating the city and describing your surroundings. The Locative case is our go-to tool for location, and of course, our adjectives must dress the part.

When we talk about locations that are masculine or neuter nouns, the adjective takes a very distinct and elegant ending. We add **-ому** or sometimes **-ьому** to the stem of the word. Let's look at some examples of how this transforms our sentences. Imagine you are sharing your travel stories with a friend. You want to describe the exact feel of the places you visited.

> - **новий** → **у новому місті** (in a new city)
> - **великий** → **у великому парку** (in a big park)
> - **синій** → **на синьому морі** (on the blue sea)
> - **старий** → **у старому будинку** (in an old building)
> - **дорогий** → **у дорогому ресторані** (in an expensive restaurant)
> - **модний** → **у модному магазині** (in a fashionable store)

A very typical error that English speakers make is to leave the adjective in the Nominative case while changing the noun. It is very tempting to use an unchanged adjective because it feels like English, where adjectives never change. However, in Ukrainian, they must always travel together! The adjective must wear the Locative ending to match its noun.

Let's turn our attention to the feminine nouns in the Locative case. Feminine adjectives are quite consistent and elegant here. They take the ending **-ій**. Let's explore some helpful phrases you might use while exploring.

> - **нова** → **у новій книзі** (in a new book)
> - **велика** → **на великій площі** (on a big square)
> - **стара** → **у старій церкві** (in an old church)
> - **важлива** → **у важливій справі** (in an important matter)
> - **українська** → **в українській школі** (in a Ukrainian school)


You might remember that feminine nouns sometimes have a consonant mutation in the Locative case (like the shift from **площа** to **площі** or **церква** to **церкві**). The fantastic news is that this change in the noun's stem does not affect the adjective's ending at all! The adjective confidently keeps its **-ій** ending no matter what the noun is doing. This stability is your best friend when you are speaking on the fly.

> 🎬 **Діалог: Старий готель**
> 
> — **Добрий вечір! Ми в старому готелі?** (Good evening! Are we in an old hotel?)
> — **Так, ми зараз у старому готелі.** (Yes, we are in an old hotel right now.)
> — **Цей готель на великій площі?** (Is this hotel on a big square?)
> — **Ні, він на маленькій вулиці.** (No, it is on a small street.)
> — **Тут є гарний новий ресторан?** (Is there a beautiful new restaurant here?)
> — **Так, у новому ресторані дуже смачно.** (Yes, it is very tasty in the new restaurant.)


## Порівняння форм (Comparing forms)

To truly master these endings, it is incredibly helpful to see them side-by-side. By comparing the Nominative, Accusative, and Locative forms directly, you can train your brain to recognize the patterns instantly. Let's do a parallel comparison using the word for «new» across all three genders. This visualization will help anchor the grammar rules in your visual memory.

| Стать (Gender) | Називний (Nom) | Знахідний (Acc) | Місцевий (Loc) |
|---|---|---|---|
| Чоловічий (Masc) | **новий** | **новий** / **нового** | **новому** |
| Жіночий (Fem) | **нова** | **нову** | **новій** |
| Середній (Neut) | **нове** | **нове** | **новому** |

Take a close look at this table. You can use this as your ultimate reference guide. Recognizing endings as markers of a specific case is a powerful strategy for understanding spoken Ukrainian. When you hear the ending **-ий**, you know it is likely a masculine Nominative form. Be careful with **-ій** though — it can be either masculine Nominative (like **синій**) or feminine Locative (like **у новій книзі**). Context will tell you which! If you catch the sound of **-у** on an adjective, your brain should automatically register that it is a feminine object in the Accusative case. 

Similarly, the deep **-ому** ending is your clear signal for a masculine or neuter location in the Locative case, while the soft **-ій** is your marker for a feminine location.

> - **Називний**: **Цей популярний фільм цікавий.** (This popular film is interesting.)
> - **Знахідний**: **Я дивлюся популярний фільм.** (I am watching a popular film.)
> - **Місцевий**: **Я у популярному кафе.** (I am in a popular cafe.)

A great strategy for memorization is to practice these as sets. Pick an adjective and noun pair, like **красиве місто** (beautiful city), and run it through the three forms aloud. This will build muscle memory and make the transitions feel perfectly natural when you are speaking.

## Типові помилки (Common errors)

Learning a new language is a journey full of trial and error, and making mistakes is a natural part of the process! As your tutor, I want to highlight a few common traps so you can step right over them.

The most frequent hurdle is the «frozen adjective» mistake. Because English adjectives never change their form, it is very easy to remember to change the noun but forget about its descriptive partner. For example, always pair an accusative adjective with an accusative noun, like **велику книгу** or the correct **красиву книгу**. To avoid this, try to visualize the adjective and the noun holding hands. Your core strategy must be: if the noun changes, the adjective changes too!

> - ✅ **Я п'ю велику каву.** (Correct)
> - ✅ **Я п'ю смачну каву.** (Correct)

Another tricky spot involves the living masculine nouns. It is very important to use the correct endings, choosing forms such as **молодого студента** or the correct **нового студента**. Because English does not treat living and non-living objects differently in grammar, this rule requires a little extra attention.

> - ✅ **Я бачу старого чоловіка.** (Correct)
> - ✅ **Я бачу молодого чоловіка.** (Correct)


Just remember your golden rule: a living masculine noun demands the Genitive ending **-ого** when it is the direct object!

> 🎬 **Діалог: Хороший студент**
> 
> — **Я бачу нового студента.** (I see a new student.)
> — **Він хороший студент?** (Is he a good student?)
> — **Так, він дуже хороший студент.** (Yes, he is a very good student.)
> — **Він зараз читає нову книгу?** (Is he reading a new book now?)
> — **Так, він читає українську книгу.** (Yes, he is reading a Ukrainian book.)
> — **Він читає в новому парку.** (He is reading in a new park.)


## Практика (Practice)

You've absorbed some great grammar today! Now it's time to put these concepts into action. Practice is the secret to making these endings flow naturally in your conversation. We will start with some transformation exercises where you can apply the correct adjective forms in the Accusative and Locative cases.

First, try transforming these Nominative phrases into the Locative case. Think about the gender and apply your new endings!

> - **велике місто** → **у великому місті**
> - **стара вулиця** → **на старій вулиці**
> - **дорогий готель** → **у дорогому готелі**

Next, let's work on some contextual tasks. Imagine you are ordering food or pointing out people. Complete the sentences with the correct adjective forms. Pay close attention to whether the masculine nouns are alive or not!

> - **Я п'ю смачну каву.** (I am drinking tasty coffee.)
> - **Він знає цікавого чоловіка.** (He knows an interesting man.)
> - **Ми читаємо нову книгу.** (We are reading a new book.)

These exercises in recognizing the case by the adjective's ending will dramatically improve your listening skills. Keep practicing these parallel transformations, and soon you will be describing the world around you with absolute confidence and style!

## Підсумок
Great work today! We have explored how adjectives adapt and change to match their nouns in the Accusative and Locative cases. You learned that inanimate masculine and neuter adjectives look just like the Nominative in the Accusative, while feminine adjectives take the lovely **-у** ending. You also discovered that animate masculine nouns borrow the **-ого** ending. 

In the Locative case, you mastered the rich **-ому** ending for masculine and neuter locations, and the elegant **-ій** ending for feminine places. You are now equipped to navigate the city, describe what you see, and order your favorite things!

**Self-Check Questions:**
1. What is the Accusative feminine ending for an adjective?
2. How do you say "in a new city" using the Locative case?
3. What is the critical rule for masculine animate nouns in the Accusative case?
4. How do you avoid the «frozen adjective» error?
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/adjective-case-forms.yaml`

```yaml
- type: fill-in
  title: "Choose the Correct Adjective Form"
  instruction: "Pick the right form of the adjective to complete each sentence. Pay attention to the case and gender of the noun."
  items:
    - sentence: "Я читаю ___ книгу."
      answer: "нову"
      options: ["нову", "нова", "новій", "нового"]
      explanation: "Книга is feminine. In the Accusative case, feminine adjectives change -а to -у."
    - sentence: "Я дивлюся ___ фільм."
      answer: "цікавий"
      options: ["цікавий", "цікавого", "цікаву", "цікавому"]
      explanation: "Фільм is masculine inanimate. In the Accusative, the adjective stays the same as the Nominative."
    - sentence: "Ми у ___ парку."
      answer: "великому"
      options: ["великому", "великий", "великій", "велику"]
      explanation: "Парк is masculine. In the Locative case, masculine adjectives take the ending -ому."
    - sentence: "Вона у ___ школі."
      answer: "українській"
      options: ["українській", "українську", "українська", "українському"]
      explanation: "Школа is feminine. In the Locative case, feminine adjectives take the ending -ій."
    - sentence: "Він бачить ___ студента."
      answer: "молодого"
      options: ["молодого", "молодий", "молоду", "молодому"]
      explanation: "Студент is masculine animate. In the Accusative, animate masculine adjectives take -ого (same as Genitive)."
    - sentence: "Я п'ю ___ каву."
      answer: "смачну"
      options: ["смачну", "смачний", "смачному", "смачна"]
      explanation: "Кава is feminine. In the Accusative case, the adjective changes to -у."
    - sentence: "Вони у ___ ресторані."
      answer: "дорогому"
      options: ["дорогому", "дорогий", "дорогій", "дорогу"]
      explanation: "Ресторан is masculine. In the Locative case, masculine adjectives take -ому."
    - sentence: "Я бачу ___ кафе."
      answer: "нове"
      options: ["нове", "нового", "нову", "новому"]
      explanation: "Кафе is neuter inanimate. In the Accusative, neuter adjectives stay the same as the Nominative."
    - sentence: "Книга на ___ площі."
      answer: "великій"
      options: ["великій", "великому", "велику", "великий"]
      explanation: "Площа is feminine. In the Locative case, feminine adjectives take the ending -ій."
    - sentence: "Я годую ___ кота."
      answer: "старого"
      options: ["старого", "старий", "стару", "старому"]
      explanation: "Кіт is masculine animate. In the Accusative, animate masculine adjectives take -ого."
    - sentence: "Він у ___ готелі."
      answer: "старому"
      options: ["старому", "старій", "старий", "стару"]
      explanation: "Готель is masculine. In the Locative case, masculine adjectives take the ending -ому."
    - sentence: "Ми маємо ___ проблему."
      answer: "маленьку"
      options: ["маленьку", "маленький", "маленькій", "маленька"]
      explanation: "Проблема is feminine. In the Accusative case, feminine adjectives change to -у."

- type: quiz
  title: "Identify the Case"
  instruction: "Look at the adjective form and decide which case it belongs to."
  items:
    - question: "Which case is the adjective in: 'у новому місті'?"
      options:
        - text: "Locative"
          correct: true
        - text: "Accusative"
          correct: false
        - text: "Nominative"
          correct: false
        - text: "Genitive"
          correct: false
      explanation: "The ending -ому on новому signals the Locative case for masculine/neuter adjectives."
    - question: "Which case is the adjective in: 'Я читаю нову книгу'?"
      options:
        - text: "Accusative"
          correct: true
        - text: "Nominative"
          correct: false
        - text: "Locative"
          correct: false
        - text: "Genitive"
          correct: false
      explanation: "The ending -у on нову signals the Accusative case for feminine adjectives."
    - question: "Which case is the adjective in: 'Я бачу нового студента'?"
      options:
        - text: "Accusative"
          correct: true
        - text: "Genitive"
          correct: false
        - text: "Locative"
          correct: false
        - text: "Nominative"
          correct: false
      explanation: "Студент is masculine animate. In the Accusative, the adjective borrows the Genitive ending -ого."
    - question: "Which case is the adjective in: 'у старій церкві'?"
      options:
        - text: "Locative"
          correct: true
        - text: "Accusative"
          correct: false
        - text: "Nominative"
          correct: false
        - text: "Genitive"
          correct: false
      explanation: "The ending -ій on старій signals the Locative case for feminine adjectives."
    - question: "Which case is the adjective in: 'Це великий парк'?"
      options:
        - text: "Nominative"
          correct: true
        - text: "Accusative"
          correct: false
        - text: "Locative"
          correct: false
        - text: "Genitive"
          correct: false
      explanation: "The ending -ий is the dictionary form — Nominative case for masculine adjectives."
    - question: "Which case is the adjective in: 'Я люблю великий парк'?"
      options:
        - text: "Accusative"
          correct: true
        - text: "Nominative"
          correct: false
        - text: "Locative"
          correct: false
        - text: "Genitive"
          correct: false
      explanation: "Парк is masculine inanimate. In the Accusative, the adjective looks the same as the Nominative, but the case is Accusative because парк is the direct object."
    - question: "What ending does a masculine/neuter adjective take in the Locative case?"
      options:
        - text: "-ому"
          correct: true
        - text: "-у"
          correct: false
        - text: "-ого"
          correct: false
        - text: "-ій"
          correct: false
      explanation: "Masculine and neuter adjectives take -ому (or -ьому) in the Locative case."
    - question: "What ending does a feminine adjective take in the Accusative case?"
      options:
        - text: "-у"
          correct: true
        - text: "-ій"
          correct: false
        - text: "-ому"
          correct: false
        - text: "-ого"
          correct: false
      explanation: "Feminine adjectives change from -а to -у in the Accusative case."
    - question: "Why does 'нового студента' use -ого instead of -ий in the Accusative?"
      options:
        - text: "Because студент is masculine animate (a living person)"
          correct: true
        - text: "Because студент is a neuter noun"
          correct: false
        - text: "Because it is in the Locative case"
          correct: false
        - text: "Because студент is feminine"
          correct: false
      explanation: "Masculine animate nouns use the Genitive ending (-ого) in the Accusative case. Living beings get a special form!"
    - question: "Which adjective form is correct for 'I see a beautiful city' (Я бачу ___ місто)?"
      options:
        - text: "красиве"
          correct: true
        - text: "красивого"
          correct: false
        - text: "красиву"
          correct: false
        - text: "красивому"
          correct: false
      explanation: "Місто is neuter inanimate. In the Accusative, neuter adjectives keep the Nominative form: красиве."

- type: match-up
  title: "Match the Adjective Form to Its Case"
  instruction: "Connect each adjective form with its grammatical case."
  pairs:
    - left: "нову (книгу)"
      right: "Accusative feminine"
    - left: "новому (місті)"
      right: "Locative masculine/neuter"
    - left: "нового (студента)"
      right: "Accusative masculine animate"
    - left: "новій (школі)"
      right: "Locative feminine"
    - left: "новий (фільм)"
      right: "Nominative/Accusative masculine inanimate"
    - left: "нове (кафе)"
      right: "Nominative/Accusative neuter"
    - left: "великому (парку)"
      right: "Locative masculine"
    - left: "старій (церкві)"
      right: "Locative feminine"
    - left: "смачну (каву)"
      right: "Accusative feminine"
    - left: "молодого (чоловіка)"
      right: "Accusative masculine animate"

- type: true-false
  title: "True or False? Check Adjective-Noun Agreement"
  instruction: "Decide if the adjective form correctly matches the noun in the given sentence."
  items:
    - statement: "In 'Я читаю нову книгу', the adjective нову is correct for the Accusative feminine."
      correct: true
      explanation: "Correct! Feminine adjectives change -а to -у in the Accusative case."
    - statement: "In the Accusative case, masculine inanimate adjectives change their ending."
      correct: false
      explanation: "False! Masculine inanimate adjectives stay in their Nominative (dictionary) form in the Accusative."
    - statement: "The phrase 'у великий парку' uses the correct Locative adjective form."
      correct: false
      explanation: "False! In the Locative, masculine adjectives must take -ому: у великому парку."
    - statement: "Animate masculine nouns use the Genitive adjective ending (-ого) in the Accusative case."
      correct: true
      explanation: "Correct! For living masculine nouns, the Accusative borrows the Genitive form: нового студента."
    - statement: "The phrase 'у новій книзі' correctly uses the Locative feminine adjective form."
      correct: true
      explanation: "Correct! Feminine adjectives take -ій in the Locative case."
    - statement: "Neuter adjectives change their ending in the Accusative case for inanimate nouns."
      correct: false
      explanation: "False! Like masculine inanimate, neuter adjectives keep their Nominative form in the Accusative: нове кафе."
    - statement: "The ending -ому on an adjective tells you the noun is in the Locative case."
      correct: true
      explanation: "Correct! The -ому ending is the clear Locative marker for masculine and neuter adjectives."
    - statement: "In 'Я бачу старий чоловіка', the adjective form старий is correct."
      correct: false
      explanation: "False! Чоловік is masculine animate. The Accusative requires the Genitive form: старого чоловіка."
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/adjective-case-forms.yaml`

```yaml
items:
  - lemma: "новий"
    translation: "new"
    pos: "adjective"
    notes: "Paradigm adjective for case practice. Forms: новий (Nom), нову (Acc fem), нового (Acc anim), новому (Loc m/n), новій (Loc f)"
    usage: "Я дивлюся новий фільм."
  - lemma: "великий"
    translation: "big, large"
    pos: "adjective"
    notes: "High frequency. Forms: великий, велику, великому, великій"
    usage: "Ми у великому парку."
  - lemma: "маленький"
    translation: "small, little"
    pos: "adjective"
    notes: "Contrast with великий. Forms: маленький, маленьку, маленькій"
    usage: "Я маю маленьку проблему."
  - lemma: "красивий"
    translation: "beautiful"
    pos: "adjective"
    notes: "High frequency. Forms: красивий, красиву, красивому"
    usage: "Я бачу красиву дівчину."
  - lemma: "старий"
    translation: "old"
    pos: "adjective"
    notes: "Locative context. Forms: старий, старого, стару, старому, старій"
    usage: "Ми у старому будинку."
  - lemma: "цікавий"
    translation: "interesting"
    pos: "adjective"
    notes: "Accusative context. Forms: цікавий, цікавого, цікаву, цікавому"
    usage: "Він знає цікавий факт."
  - lemma: "смачний"
    translation: "tasty, delicious"
    pos: "adjective"
    notes: "Food context. Forms: смачний, смачну, смачному"
    usage: "Я п'ю смачну каву."
  - lemma: "дорогий"
    translation: "expensive; dear"
    pos: "adjective"
    notes: "Price context. Forms: дорогий, дорогого, дорогу, дорогому, дорогій"
    usage: "Ми у дорогому ресторані."
  - lemma: "український"
    translation: "Ukrainian"
    pos: "adjective"
    notes: "Cultural adjective. Forms: український, українську, українському, українській"
    usage: "Він читає українську книгу."
  - lemma: "молодий"
    translation: "young"
    pos: "adjective"
    notes: "Animate Accusative context. Forms: молодий, молодого, молоду"
    usage: "Я бачу молодого чоловіка."
  - lemma: "важливий"
    translation: "important"
    pos: "adjective"
    notes: "Abstract context. Forms: важливий, важливу, важливому, важливій"
    usage: "Це важливий документ."
  - lemma: "популярний"
    translation: "popular"
    pos: "adjective"
    notes: "Locative context. Forms: популярний, популярну, популярному"
    usage: "Я у популярному кафе."
  - lemma: "фільм"
    translation: "film, movie"
    pos: "noun"
    gender: "m"
    usage: "Я дивлюся новий фільм."
  - lemma: "книга"
    translation: "book"
    pos: "noun"
    gender: "f"
    usage: "Я читаю нову книгу."
  - lemma: "кава"
    translation: "coffee"
    pos: "noun"
    gender: "f"
    usage: "Я п'ю смачну каву."
  - lemma: "місто"
    translation: "city"
    pos: "noun"
    gender: "n"
    usage: "Ми у великому місті."
  - lemma: "парк"
    translation: "park"
    pos: "noun"
    gender: "m"
    usage: "Я люблю великий парк."
  - lemma: "студент"
    translation: "student"
    pos: "noun"
    gender: "m"
    notes: "Masculine animate — uses Genitive form in Accusative"
    usage: "Я бачу нового студента."
  - lemma: "ресторан"
    translation: "restaurant"
    pos: "noun"
    gender: "m"
    usage: "Ми у дорогому ресторані."
  - lemma: "церква"
    translation: "church"
    pos: "noun"
    gender: "f"
    notes: "Consonant mutation in Locative: церква → церкві"
    usage: "Ми у старій церкві."
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
- Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/adjective-case-forms.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/adjective-case-forms.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/adjective-case-forms.yaml`

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
