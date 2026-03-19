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

## Review Findings (targeted fix required)

**CONSTRAINTS:**
- Fix ONLY the issues listed below
- Do NOT rewrite surrounding text
- Preserve word count and structure
- Only modify these sections: Activities file, line 175-176, Activities file, line 195, Entire module, Line 84, Section "Кількість та одиниці (Quantities and Units)", Section "У магазині (In the Store)", Vocabulary file

### Finding 1: Missing Plan Point — "Дайте, будь ласка..." (MEDIUM-HIGH)
**Location**: Section "У магазині (In the Store)"
**Problem**: The plan explicitly requires three polite request patterns: "Дайте, будь ласка... (Give me, please...). Я хочу купити... (I want to buy...). Можна...? (May I...?)." The content only covers "Я хочу купити..." and "Item + будь ласка." The imperative formula "Дайте, будь ласка" is entirely absent. The plan's `grammar` field also lists "Shopping imperative phrases (Дайте, будь ласка)" as a grammar point. The summary on line 158 even claims 「You explored polite request patterns like **Хліб, будь ласка** and **Я хочу купити**」 — inadvertently confirming the gap.
**Required Fix**: Add "Дайте, будь ласка..." as a third polite request formula in section "У магазині", with 2-3 examples (Дайте хліб, будь ласка. Дайте воду, будь ласка.). Also add "Можна мило, будь ласка?" to the same section. Research notes say to treat "Дайте, будь ласка" as a frozen chunk, not a productive imperative.
**Severity**: HIGH

### Finding 2: Grammatical Terminology Inconsistency (MEDIUM)
**Location**: Line 84, Section "Кількість та одиниці (Quantities and Units)"
**Problem**: Line 18 correctly describes the 2-4 pattern for гривні as "Nominative plural" but line 84 calls the identical pattern for пачки/пляшки "Genitive singular form." While the forms are homonymous for -а/-я feminines, using two different case labels for the same numerical agreement rule within one module is confusing for A1 learners. Modern Ukrainian grammar describes 2-4 agreement as Nominative plural. Calling it "Genitive singular" follows the Russian grammatical tradition.
**Required Fix**: Change to "Nominative plural ending **-и**" for consistency with line 18 and Ukrainian grammatical tradition.
**Severity**: HIGH

### Finding 3: Activity Error — Unjumble Missing Comma (MEDIUM)
**Location**: Activities file, line 195
**Problem**: The content teaches 「Хліб, будь ласка.」 (line 33) with a comma. The unjumble answer omits the comma, teaching incorrect punctuation. In Ukrainian, "будь ласка" is separated by a comma when it follows the item.
**Required Fix**: Change answer to "Хліб, будь ласка"
**Severity**: HIGH

### Finding 4: Activity Error — Match-up Nonsense Pairing (MEDIUM)
**Location**: Activities file, line 175-176
**Problem**: The activity instruction says "Match each product with the unit of measurement typically used when buying it." "будь ласка (by item)" is not a unit of measurement. This is confusing and breaks the activity's internal logic. Хліб is typically sold by штука or as a whole item.
**Required Fix**: Change to `right: "штука"` — штука is already taught in the module as a unit (line 72).
**Severity**: HIGH

### Finding 5: Low Immersion (17.7% vs 20% minimum) (LOW-MEDIUM)
**Location**: Entire module
**Problem**: Pre-computed immersion is 17.7%, below the 20% floor. Module 40 is in the 21+ band. The English prose dominates even in sections where more Ukrainian examples could be woven in.
**Required Fix**: Add 2-3 more Ukrainian example sentences in sections "Засоби гігієни" and "У магазині" to nudge immersion above 20%. For example, add a short dialogue asking for зубна паста at an аптека.
**Severity**: HIGH

### Finding 6: Missing Vocabulary Items in YAML (LOW)
**Location**: Vocabulary file
**Problem**: зубна паста (toothpaste) and туалетний папір (toilet paper) are taught in section "Засоби гігієни" (lines 107, 110) but absent from the vocabulary YAML. These are useful survival vocabulary words.
**Required Fix**: Add both to the vocabulary YAML.
**Severity**: HIGH

---

## Critical Issues Found

### Issue 1: Missing Plan Point — "Дайте, будь ласка..." (MEDIUM-HIGH)
- **Location**: Section "У магазині (In the Store)"
- **Problem**: The plan explicitly requires three polite request patterns: "Дайте, будь ласка... (Give me, please...). Я хочу купити... (I want to buy...). Можна...? (May I...?)." The content only covers "Я хочу купити..." and "Item + будь ласка." The imperative formula "Дайте, будь ласка" is entirely absent. The plan's `grammar` field also lists "Shopping imperative phrases (Дайте, будь ласка)" as a grammar point. The summary on line 158 even claims 「You explored polite request patterns like **Хліб, будь ласка** and **Я хочу купити**」 — inadvertently confirming the gap.
- **Fix**: Add "Дайте, будь ласка..." as a third polite request formula in section "У магазині", with 2-3 examples (Дайте хліб, будь ласка. Дайте воду, будь ласка.). Also add "Можна мило, будь ласка?" to the same section. Research notes say to treat "Дайте, будь ласка" as a frozen chunk, not a productive imperative.

### Issue 2: Grammatical Terminology Inconsistency (MEDIUM)
- **Location**: Line 84, Section "Кількість та одиниці (Quantities and Units)"
- **Original**: 「The feminine words **пачка** and **пляшка** change their ending to **-и** (Genitive singular form).」
- **Problem**: Line 18 correctly describes the 2-4 pattern for гривні as "Nominative plural" but line 84 calls the identical pattern for пачки/пляшки "Genitive singular form." While the forms are homonymous for -а/-я feminines, using two different case labels for the same numerical agreement rule within one module is confusing for A1 learners. Modern Ukrainian grammar describes 2-4 agreement as Nominative plural. Calling it "Genitive singular" follows the Russian grammatical tradition.
- **Fix**: Change to "Nominative plural ending **-и**" for consistency with line 18 and Ukrainian grammatical tradition.

### Issue 3: Activity Error — Unjumble Missing Comma (MEDIUM)
- **Location**: Activities file, line 195
- **Original**: 「answer: "Хліб будь ласка"」
- **Problem**: The content teaches 「Хліб, будь ласка.」 (line 33) with a comma. The unjumble answer omits the comma, teaching incorrect punctuation. In Ukrainian, "будь ласка" is separated by a comma when it follows the item.
- **Fix**: Change answer to "Хліб, будь ласка"

### Issue 4: Activity Error — Match-up Nonsense Pairing (MEDIUM)
- **Location**: Activities file, line 175-176
- **Original**: 「right: "будь ласка (by item)"」 for хліб
- **Problem**: The activity instruction says "Match each product with the unit of measurement typically used when buying it." "будь ласка (by item)" is not a unit of measurement. This is confusing and breaks the activity's internal logic. Хліб is typically sold by штука or as a whole item.
- **Fix**: Change to `right: "штука"` — штука is already taught in the module as a unit (line 72).

### Issue 5: Low Immersion (17.7% vs 20% minimum) (LOW-MEDIUM)
- **Location**: Entire module
- **Problem**: Pre-computed immersion is 17.7%, below the 20% floor. Module 40 is in the 21+ band. The English prose dominates even in sections where more Ukrainian examples could be woven in.
- **Fix**: Add 2-3 more Ukrainian example sentences in sections "Засоби гігієни" and "У магазині" to nudge immersion above 20%. For example, add a short dialogue asking for зубна паста at an аптека.

### Issue 6: Missing Vocabulary Items in YAML (LOW)
- **Location**: Vocabulary file
- **Problem**: зубна паста (toothpaste) and туалетний папір (toilet paper) are taught in section "Засоби гігієни" (lines 107, 110) but absent from the vocabulary YAML. These are useful survival vocabulary words.
- **Fix**: Add both to the vocabulary YAML.

---

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 84 | 「The feminine words **пачка** and **пляшка** change their ending to **-и** (Genitive singular form).」 | "The feminine words **пачка** and **пляшка** change their ending to **-и** (Nominative plural)." | Grammar terminology |
| Act. 195 | 「answer: "Хліб будь ласка"」 | answer: "Хліб, будь ласка" | Punctuation |

---

## Fix Plan to Reach 9/10 (REQUIRED — current 7.7/10)

### Pedagogy: 7/10 → 9/10
**What to fix:**
1. Section "У магазині": Add "Дайте, будь ласка..." as a polite request pattern with 2-3 examples, and add "Можна...?" with 1-2 examples. This closes the biggest plan gap. (~60 words)
2. Move or duplicate "Можна платити карткою?" context into section "У магазині" so all three request patterns are taught together before practice.

### Activities: 7/10 → 9/10
**What to fix:**
1. Activity line 195: Fix unjumble answer from "Хліб будь ласка" to "Хліб, будь ласка"
2. Activity line 175-176: Change match-up pair for хліб from "будь ласка (by item)" to "штука"

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. Line 84: Change "(Genitive singular form)" to "(Nominative plural)" for consistency with line 18 and Ukrainian grammatical tradition.

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Line 1: Add a warm opening with "Привіт!" and a brief learning preview before diving into content.
2. Add one more engagement box (e.g., a [!tip] or [!did-you-know] about market culture in section "Практика").

### Projected Overall After Fixes
```
Experience 9×1.5 + Language 8×1.1 + Pedagogy 9×1.2 + Activities 9×1.3 +
Beginner Safety 9×1.3 + LLM 8×1.0 + Linguistic Accuracy 9×1.5
= 13.5 + 8.8 + 10.8 + 11.7 + 11.7 + 8.0 + 13.5 = 78.0 / 8.9 = 8.8/10
```

---

## Audit Failures (from automated re-audit)

```
⚠️ HYDRATION NOTE: Outline sums to 1300, exceeding word_target 1200
--- STRICT GATES (Level A1) ---
❌ [REVIEW_VERDICT_FAIL] Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
❌ AUDIT FAILED. Correct errors before proceeding.
Critical Failures:
• Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/shopping-and-market-audit.log for details)
⚠️  RAG verification found unverified words (see audit report)
--- STATUS JSON GATE BLOCKERS ---
GATE BLOCKER: Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
--- VESUM WORD VERIFICATION FAILURES ---
These words were NOT found in the VESUM morphological dictionary.
Check if they are valid Ukrainian forms. Fix misspellings or Russianisms.
  ❌ `ень` (source: prose)
```

---

## File Contents (for reference)

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/shopping-and-market.md`

```markdown
Today, we are going to connect your vocabulary with something very practical: shopping in Ukraine. Whether you are at a modern supermarket or a lively outdoor bazaar, you will need to know how to ask about prices. Let's start with the most important question for any shopper.

## Скільки коштує? (How much?)

When you want to know the price of something, you use the verb **коштувати** (to cost). It is an imperfective verb that you will hear every day. To ask "How much does it cost?", we say **Скільки коштує?**.

If you are pointing at something specific, you can add the word **це** (this):
- **Скільки це коштує?** (How much does this cost?)
- **Скільки коштує яблуко?** (How much does the apple cost?)
- **Скільки коштує вода?** (How much does the water cost?)

The verb **коштувати** is in the present tense form for "it" (**коштує**), because the item you are buying is the subject of the sentence.

Now, let's talk about money. The currency of Ukraine is the **гривня** (hryvnia). As we learned before when talking about numbers, the form of the word **гривня** changes depending on the number that comes before it. This is a very common pattern in Ukrainian, and it is a great time for a quick review of number-noun agreement!

Here is how we count our money:
- **одна гривня** (one hryvnia) — ends in **-я**
- **дві гривні** (two hryvnias) — numbers 2, 3, and 4 take the Nominative plural, ending in **-і**
- **п'ять гривень** (five hryvnias) — numbers 5 and above take the Genitive plural, ending in **-ень**

When the seller answers your question about the price, they will use the same verb **коштувати** and then give you the amount. You can also produce full price sentences yourself. For example:
- **Це коштує двадцять гривень.** (This costs twenty hryvnias.)
- **Борщ коштує сімдесят гривень.** (The borscht costs seventy hryvnias.)
- **Кава коштує тридцять дві гривні.** (The coffee costs thirty-two hryvnias.)

You just state the item, use the verb **коштує**, and add the number and the correct form of **гривня**. Take a moment to practice saying these prices out loud.

## У магазині (In the Store)

In Ukrainian, a store or shop is called a **магазин**. To say "in the store", you use the Locative case: **у магазині**. Let's learn the polite request patterns you need to get what you want.

When you are ready to order or ask for an item, it is polite to use specific shopping formulas. One useful approach is to simply name the item and add please.
- **Хліб, будь ласка.** (Bread, please.)
- **Молоко, будь ласка.** (Milk, please.)

Another very common phrase uses the perfective verb **купити** (to buy). You can say:
- **Я хочу купити сир.** (I want to buy cheese.)
- **Я хочу купити яблуко.** (I want to buy an apple.)

You can also use the imperative formula **Дайте, будь ласка** (Give me, please). This is a fixed shopping phrase — just add the item you want:
- **Дайте хліб, будь ласка.** (Give me bread, please.)
- **Дайте воду, будь ласка.** (Give me water, please.)
- **Дайте два кілограми яблук, будь ласка.** (Give me two kilograms of apples, please.)

And when you want to ask permission, use **Можна...?** (May I...? / Can I...?):
- **Можна воду?** (Can I have water?)
- **Можна мило, будь ласка?** (Can I have soap, please?)

Sometimes you want to politely request an item without a verb. In this case, just ask for the item directly:
- **Каву, будь ласка.** (A coffee, please.)

Before you ask for the price, you might need to check if the store actually has the item in stock. English speakers often make a small mistake here by trying to use the verb "to have" (like "Do you have apples?"). However, in a Ukrainian **магазин**, we do not ask if the person "has" the item. Instead, we ask if the item "exists" there.

To check availability, we ask **Є...?** (Is there...?) or **У вас є...?** (Do you have...?, literally: Is there by you...?).
- **У вас є молоко?** (Do you have milk?)
- **Так, є.** (Yes, we do.)
- **Ні, немає.** (No, we don't.)

Let's look at the basic shopping dialogue structure. A complete transaction flow usually goes like this: greeting → asking for item → asking price → paying → thanking.

> — **Добрий день!** (Good afternoon!)
> — **Добрий день.** (Good afternoon.)
> — **У вас є вода?** (Do you have water?)
> — **Так, є.** (Yes, we do.)
> — **Добре. Скільки коштує?** (Good. How much does it cost?)
> — **Двадцять гривень.** (Twenty hryvnias.)
> — **Дякую.** (Thank you.)
> — **Будь ласка.** (You're welcome.)

This exchange will work perfectly in any **магазин**.

## Кількість та одиниці (Quantities and Units)

You rarely just buy "water" or "sugar"—you buy a bottle of water or a packet of sugar. Learning how to express quantities and units is essential for your everyday life in Ukraine. Let's look at the most common units of measurement and their typical products.

Here are the key containers and measurements you will use:
- **кілограм** (kilogram) — a masculine noun, used for fruits, vegetables, and meat.
- **літр** (litre) — a masculine noun, used for liquids like milk or juice.
- **пачка** (packet / pack) — a feminine noun, used for dry goods like tea, sugar, or butter.
- **пляшка** (bottle) — a feminine noun, used for drinks.
- **штука** (piece / item) — a feminine noun, used when counting individual items.

When you use these words, the product that comes after them must be in the Genitive case. This creates the meaning of "a bottle *of* water" or "a packet *of* sugar." You have already practiced the formulaic Genitive case for absence, and the endings here are exactly the same!

Let's see the Genitive with quantities in action:
- **кілограм яблук** (a kilogram of apples)
- **літр молока** (a litre of milk)
- **пачка цукру** (a packet of sugar)
- **пляшка води** (a bottle of water)

But what if you need more than one kilogram or more than one bottle? You will need to combine numbers with these units. The rules for number-noun case agreement patterns are the same as we saw with the currency!

For numbers 2, 3, and 4, the masculine words **кілограм** and **літр** take the Nominative plural ending **-и** (or **-і**). The feminine words **пачка** and **пляшка** change their ending to **-и** (Nominative plural).
- **два кілограми** (two kilograms)
- **три літри** (three litres)
- **дві пляшки** (two bottles)

For numbers 5 and above, the units go into the Genitive plural:
- **п'ять кілограмів** (five kilograms)
- **вісім літрів** (eight litres)
- **десять пляшок** (ten bottles)

So, if you want to buy two bottles of water, you combine all these rules into one polite request:
- **Я хочу купити дві пляшки води.** (I want to buy two bottles of water.)


> [!note]
> In Ukraine, you will often be asked if you need a bag (**пакет**). It is very common to bring your own reusable bag to the supermarket!

## Засоби гігієни (Hygiene Products)

You will also need to buy everyday essentials. Let's build your vocabulary for essential hygiene products.

Here are the basic items you might look for:
- **мило** (soap) — a neuter noun. For example: **Я хочу купити мило.** (I want to buy soap.)
- **зубна паста** (toothpaste) — a feminine phrase.
- **шампунь** (shampoo) — a masculine noun! Be careful with this one. Because it ends in a soft sign, learners often think it is feminine, but it is actually masculine.
- **рушник** (towel) — a masculine noun. In Ukraine, embroidered towels hold special cultural meaning, but you also need a regular one for the bathroom.
- **туалетний папір** (toilet paper) — a masculine phrase.

When you need to find these items, you will combine your location vocabulary with your shopping skills. The best way to ask where to buy items is to use the phrase **Де можна купити...?** (Where can one buy...?).

- **Де можна купити шампунь?** (Where can I buy shampoo?)
- **Де можна купити зубну пасту?** (Where can I buy toothpaste?)

You can also simply ask where a specific shop is located. Remember that a pharmacy is called an **аптека**.
- **Де тут аптека?** (Where is the pharmacy here?)
- **Де тут магазин?** (Where is the store here?)
- **Аптека поруч.** (The pharmacy is nearby.)

## Практика (Practice)

It is time to put everything together! Reading about shopping is helpful, but speaking the phrases out loud is how you truly learn. We will practice some shopping role-play dialogues to complete a transaction from greeting to payment.

Let's look at a transaction at the outdoor market. The Ukrainian word for market is **ринок**. Notice the preposition switch here: while we say **у магазині** (in the store), we say **на ринку** (at the market).

> — **Добрий ранок!** (Good morning!)
> — **Добрий ранок! Що ви хочете купити?** (Good morning! What do you want to buy?)
> — **Я хочу купити кілограм яблук.** (I want to buy a kilogram of apples.)
> — **Будь ласка. Що ще?** (Here you go. What else?)
> — **Більше нічого. Скільки це коштує?** (Nothing else. How much does this cost?)
> — **Це коштує сорок гривень.** (This costs forty hryvnias.)

Now let's review a slightly different scenario. You are in a modern **магазин** and you want to pay with a bank card (**картка**). You can use the phrase **карткою** to mean "by card." You will also hear the word **решта** (change).

> — **Добрий день.** (Good afternoon.)
> — **Добрий день. У вас є шампунь?** (Good afternoon. Do you have shampoo?)
> — **Так, є. Ось тут.** (Yes, we do. Right here.)
> — **Дякую. Скільки він коштує?** (Thank you. How much does it cost?)
> — **Сто п'ятдесят гривень.** (One hundred fifty hryvnias.)
> — **Можна платити карткою?** (Can I pay by card?)
> — **Так, звичайно.** (Yes, of course.)

Let's do some rapid price asking and answering drills. Imagine you are pointing at different items. Read the question and the answer aloud:
- **Скільки коштує пачка чаю? — Це коштує шістдесят гривень.**
- **Скільки коштує літр молока? — Це коштує тридцять п'ять гривень.**
- **Скільки коштує мило? — Це коштує двадцять одну гривню.**

Finally, let's practice quantity expressions by building a simple shopping list. Say these out loud to order specific amounts with correct case forms:
- **дві пляшки води** (two bottles of water)
- **три кілограми м'яса** (three kilograms of meat)
- **одна пачка цукру** (one packet of sugar)

By practicing these phrases, you will feel confident and prepared the next time you go shopping!

# Підсумок
You have done an amazing job today! Shopping is one of the most essential survival skills in any language, and you now have the tools you need. You learned how to ask for prices using **Скільки коштує?** and how to correctly agree your numbers with the word **гривня**. You explored polite request patterns like **Хліб, будь ласка** and **Я хочу купити**, and you know how to check for availability with **Є...?**.

We also covered important containers and units, such as **кілограм**, **літр**, **пляшка**, and **пачка**, along with the hygiene essentials like **мило** and **шампунь**. Remember the contrast between the locations: **у магазині** versus **на ринку**.

Take a moment to check your understanding with these self-check questions:
1. How do you ask "How much does this cost?" in Ukrainian?
2. What happens to the word **гривня** after the numbers 2 and 5?
3. How do you say "I want to buy a bottle of water"?
4. Is the word **шампунь** masculine, feminine, or neuter?

Keep practicing these phrases, and soon buying your daily groceries will feel completely natural!
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/shopping-and-market.yaml`

```yaml
- type: fill-in
  title: "Complete the Shopping Dialogue"
  instruction: "Fill in the blank with the correct Ukrainian word or phrase to complete each shopping sentence."
  items:
    - sentence: "___ коштує яблуко?"
      answer: "Скільки"
      options: ["Скільки", "Де", "Що", "Як"]
      explanation: "To ask the price, we use Скільки коштує? (How much does it cost?)"
    - sentence: "Це коштує двадцять ___."
      answer: "гривень"
      options: ["гривень", "гривня", "гривні", "гривню"]
      explanation: "After numbers 5 and above, we use the Genitive plural form гривень."
    - sentence: "Я хочу ___ сир."
      answer: "купити"
      options: ["купити", "коштувати", "платити", "дякувати"]
      explanation: "Купити (to buy) is the correct verb for purchasing items."
    - sentence: "Хліб, ___ ласка."
      answer: "будь"
      options: ["будь", "дуже", "як", "де"]
      explanation: "Будь ласка means please — a polite way to request an item."
    - sentence: "У вас ___ молоко?"
      answer: "є"
      options: ["є", "має", "був", "тут"]
      explanation: "To check availability in a store, we ask У вас є...? (Do you have...?)"
    - sentence: "Де ___ купити шампунь?"
      answer: "можна"
      options: ["можна", "треба", "хочу", "будь"]
      explanation: "Де можна купити...? means Where can one buy...?"
    - sentence: "___ коштує тридцять дві гривні."
      answer: "Кава"
      options: ["Кава", "Каву", "Кави", "Каві"]
      explanation: "The item being priced is the subject of the sentence and takes Nominative case."
    - sentence: "Можна платити ___?"
      answer: "карткою"
      options: ["карткою", "картка", "картки", "картку"]
      explanation: "Карткою (by card) uses the Instrumental case to express the means of payment."
    - sentence: "Дві ___ води, будь ласка."
      answer: "пляшки"
      options: ["пляшки", "пляшка", "пляшок", "пляшку"]
      explanation: "After the number 2, feminine nouns take the form пляшки."
    - sentence: "Ні, ___."
      answer: "немає"
      options: ["немає", "нічого", "ніде", "ніколи"]
      explanation: "Немає means there is none — the standard response when an item is unavailable."

- type: quiz
  title: "Quantities and Case Forms"
  instruction: "Choose the correct answer for each question about Ukrainian shopping expressions."
  items:
    - question: "Which unit of measurement would you use when buying apples by weight?"
      options:
        - text: "кілограм"
          correct: true
        - text: "літр"
          correct: false
        - text: "пляшка"
          correct: false
        - text: "пачка"
          correct: false
      explanation: "Кілограм (kilogram) is used for fruits, vegetables, and meat sold by weight."
    - question: "What is the correct form after the number 5: п'ять ___?"
      options:
        - text: "гривень"
          correct: true
        - text: "гривня"
          correct: false
        - text: "гривні"
          correct: false
        - text: "гривню"
          correct: false
      explanation: "Numbers 5 and above take Genitive plural: п'ять гривень."
    - question: "Which is the correct way to say 'a bottle of water'?"
      options:
        - text: "пляшка води"
          correct: true
        - text: "пляшка вода"
          correct: false
        - text: "пляшка воду"
          correct: false
        - text: "пляшку води"
          correct: false
      explanation: "After a unit of measurement, the product takes Genitive case: води (from вода)."
    - question: "What is the gender of the word шампунь (shampoo)?"
      options:
        - text: "masculine"
          correct: true
        - text: "feminine"
          correct: false
        - text: "neuter"
          correct: false
        - text: "plural"
          correct: false
      explanation: "Despite ending in a soft sign, шампунь is masculine — a common learner trap."
    - question: "How do you say 'a packet of sugar' in Ukrainian?"
      options:
        - text: "пачка цукру"
          correct: true
        - text: "пачка цукор"
          correct: false
        - text: "пачки цукру"
          correct: false
        - text: "пачку цукор"
          correct: false
      explanation: "The product after a unit takes Genitive case: цукру (from цукор)."
    - question: "What is the correct form: дві ___?"
      options:
        - text: "гривні"
          correct: true
        - text: "гривень"
          correct: false
        - text: "гривня"
          correct: false
        - text: "гривню"
          correct: false
      explanation: "Numbers 2, 3, and 4 take Nominative plural: дві гривні."
    - question: "Which unit would you use for buying milk?"
      options:
        - text: "літр"
          correct: true
        - text: "кілограм"
          correct: false
        - text: "штука"
          correct: false
        - text: "пачка"
          correct: false
      explanation: "Літр (litre) is the standard unit for liquids like milk and juice."
    - question: "What does the phrase 'на ринку' mean?"
      options:
        - text: "at the market"
          correct: true
        - text: "in the store"
          correct: false
        - text: "at the pharmacy"
          correct: false
        - text: "at the cafe"
          correct: false
      explanation: "На ринку means at the market. Note: we say на ринку (not у ринку)."
    - question: "How do you say 'two kilograms' in Ukrainian?"
      options:
        - text: "два кілограми"
          correct: true
        - text: "два кілограмів"
          correct: false
        - text: "два кілограм"
          correct: false
        - text: "два кілограму"
          correct: false
      explanation: "Numbers 2-4 take Nominative plural: два кілограми."
    - question: "What does 'решта' mean in a shopping context?"
      options:
        - text: "change (money back)"
          correct: true
        - text: "receipt"
          correct: false
        - text: "bag"
          correct: false
        - text: "discount"
          correct: false
      explanation: "Решта means change — the money returned after paying."

- type: match-up
  title: "Match Product to Unit"
  instruction: "Match each product with the unit of measurement typically used when buying it."
  pairs:
    - left: "яблука"
      right: "кілограм"
    - left: "молоко"
      right: "літр"
    - left: "цукор"
      right: "пачка"
    - left: "вода"
      right: "пляшка"
    - left: "мило"
      right: "штука"
    - left: "хліб"
      right: "штука"
    - left: "сир"
      right: "кілограм"
    - left: "чай"
      right: "пачка"
    - left: "кава"
      right: "пачка"
    - left: "м'ясо"
      right: "кілограм"

- type: unjumble
  title: "Build Shopping Sentences"
  instruction: "Arrange the words to form a correct Ukrainian shopping sentence."
  items:
    - words: ["коштує", "Скільки", "яблуко"]
      answer: "Скільки коштує яблуко"
    - words: ["купити", "хочу", "Я", "сир"]
      answer: "Я хочу купити сир"
    - words: ["будь", "Хліб", "ласка"]
      answer: "Хліб, будь ласка"
    - words: ["є", "вас", "У", "молоко"]
      answer: "У вас є молоко"
    - words: ["коштує", "двадцять", "Це", "гривень"]
      answer: "Це коштує двадцять гривень"
    - words: ["купити", "можна", "Де", "шампунь"]
      answer: "Де можна купити шампунь"
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/shopping-and-market.yaml`

```yaml
items:
  - lemma: "коштувати"
    translation: "to cost"
    pos: "verb"
    aspect: "imperfective"
    usage: "Скільки коштує?"
  - lemma: "купити"
    translation: "to buy"
    pos: "verb"
    aspect: "perfective"
    usage: "Я хочу купити сир."
  - lemma: "гривня"
    translation: "hryvnia (Ukrainian currency)"
    pos: "noun"
    gender: "f"
    notes: "одна гривня, дві гривні, п'ять гривень"
  - lemma: "кілограм"
    translation: "kilogram"
    pos: "noun"
    gender: "m"
    usage: "кілограм яблук"
  - lemma: "літр"
    translation: "litre"
    pos: "noun"
    gender: "m"
    usage: "літр молока"
  - lemma: "пачка"
    translation: "packet, pack"
    pos: "noun"
    gender: "f"
    usage: "пачка цукру"
  - lemma: "пляшка"
    translation: "bottle"
    pos: "noun"
    gender: "f"
    usage: "пляшка води"
  - lemma: "штука"
    translation: "piece, item"
    pos: "noun"
    gender: "f"
    usage: "три штуки"
  - lemma: "магазин"
    translation: "store, shop"
    pos: "noun"
    gender: "m"
    usage: "у магазині"
  - lemma: "ринок"
    translation: "market"
    pos: "noun"
    gender: "m"
    usage: "на ринку"
  - lemma: "мило"
    translation: "soap"
    pos: "noun"
    gender: "n"
    usage: "купити мило"
  - lemma: "шампунь"
    translation: "shampoo"
    pos: "noun"
    gender: "m"
    notes: "Masculine despite soft sign ending"
  - lemma: "рушник"
    translation: "towel"
    pos: "noun"
    gender: "m"
    notes: "Embroidered towels hold cultural significance in Ukraine"
  - lemma: "решта"
    translation: "change (money returned)"
    pos: "noun"
    gender: "f"
    usage: "Ваша решта."
  - lemma: "картка"
    translation: "card (bank card)"
    pos: "noun"
    gender: "f"
    usage: "платити карткою"
  - lemma: "скільки"
    translation: "how much, how many"
    pos: "adverb"
    usage: "Скільки коштує?"
  - lemma: "платити"
    translation: "to pay"
    pos: "verb"
    aspect: "imperfective"
    usage: "Можна платити карткою?"
  - lemma: "аптека"
    translation: "pharmacy"
    pos: "noun"
    gender: "f"
    usage: "Де тут аптека?"
  - lemma: "немає"
    translation: "there is no, there are no"
    pos: "particle"
    usage: "Ні, немає."
  - lemma: "можна"
    translation: "one can, it is possible"
    pos: "particle"
    usage: "Де можна купити...?"
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
- Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/shopping-and-market.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/shopping-and-market.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/shopping-and-market.yaml`

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
