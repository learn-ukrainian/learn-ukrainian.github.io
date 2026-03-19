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



**NOTE: 6 inline fix(es) from the review have ALREADY been applied to the files. Do NOT re-apply those fixes. Read the CURRENT file contents carefully — they reflect the post-fix state. Only fix issues that are still present in the current files.**

## Review Findings (targeted fix required)

**CONSTRAINTS:**
- Fix ONLY the issues listed below
- Do NOT rewrite surrounding text
- Preserve word count and structure
- Only modify these sections: Activities YAML, line 215, Activities YAML, line 217, Entire content — richness gap: engagement 0/2, Line 164, Line 86, Section "Паляниця (The Shibboleth Bread)", Lines 139-145, Section "Практика (Practice)"

### Finding 1: Unjumble Activity — Missing Comma in "Будь ласка чай"
**Location**: Activities YAML, line 215
**Problem**: Ukrainian orthography requires a comma after "Будь ласка" when it precedes a request. The correct sentence is "Будь ласка, чай." The unjumble teaches incorrect punctuation.
**Required Fix**: Change answer to `"Будь ласка, чай"` and add comma to the `words` array or restructure.
**Severity**: HIGH

### Finding 2: Unjumble Activity — Missing Dash in "Моя улюблена їжа каша"
**Location**: Activities YAML, line 217
**Problem**: This sentence requires a dash (—) between їжа and каша: "Моя улюблена їжа — каша." Without it, the sentence is grammatically malformed. The content itself on line 159 correctly writes 「**Моя́ улю́блена ї́жа — гаря́ча ка́ша!**」 with the dash.
**Required Fix**: Change answer to `"Моя улюблена їжа — каша"` and add dash to `words` array.
**Severity**: HIGH

### Finding 3: Wrong Proverb — Plan Says «Хліб — усьому голова» but Content Uses «Хліб — це життя́»
**Location**: Line 86, Section "Паляниця (The Shibboleth Bread)"
**Problem**: The plan explicitly specifies the connection to the proverb «Хліб — усьому голова» (Bread is the head of everything). This is the canonical, widely-known Ukrainian proverb. The content substitutes a different, less authoritative phrase. The research notes also list «Хліб — усьому голова» as the target proverb.
**Required Fix**: Replace with «Хліб — усьому голова.» (Bread is the head of everything.)
**Severity**: HIGH

### Finding 4: Zero Engagement Boxes (Audit Gate Failure)
**Location**: Entire content — richness gap: engagement 0/2
**Problem**: The audit shows 0 engagement boxes. There is one `[!cultural-note]` callout (line 90) but the richness metric counts engagement-type boxes (did-you-know, fun-fact, tip, etc.) and requires at least 2. This is a failing audit gate.
**Required Fix**: Add at least 2 engagement callouts. Suggestions: (1) A `[!did-you-know]` about компот tradition in Section "Напої (Drinks)", (2) A `[!tip]` about remembering noun genders by their endings in Section "Їжа (Food)".
**Severity**: HIGH

### Finding 5: Menu Reading Missing Prices (Plan Deviation)
**Location**: Lines 139-145, Section "Практика (Practice)"
**Problem**: The plan specifies "Recognizing food words in authentic format **with prices**" but the menu preview has no prices. This is a plan adherence gap — prices make the menu feel authentic and introduce number practice.
**Required Fix**: Add Ukrainian hryvnia prices to each menu item (e.g., **Борщ украї́нський — 95 грн**).
**Severity**: HIGH

### Finding 6: H1 Heading for Підсумок Instead of H2
**Location**: Line 164
**Problem**: All content sections should use H2 (`##`). The summary uses H1, which breaks the heading hierarchy and may cause rendering issues.
**Required Fix**: Change `# Підсумок` to `## Підсумок`
**Severity**: HIGH

---

## Critical Issues Found

### Issue 1: Unjumble Activity — Missing Comma in "Будь ласка чай"
- **Location**: Activities YAML, line 215
- **Original**: Answer is `"Будь ласка чай"`
- **Problem**: Ukrainian orthography requires a comma after "Будь ласка" when it precedes a request. The correct sentence is "Будь ласка, чай." The unjumble teaches incorrect punctuation.
- **Fix**: Change answer to `"Будь ласка, чай"` and add comma to the `words` array or restructure.

### Issue 2: Unjumble Activity — Missing Dash in "Моя улюблена їжа каша"
- **Location**: Activities YAML, line 217
- **Original**: Answer is `"Моя улюблена їжа каша"`
- **Problem**: This sentence requires a dash (—) between їжа and каша: "Моя улюблена їжа — каша." Without it, the sentence is grammatically malformed. The content itself on line 159 correctly writes 「**Моя́ улю́блена ї́жа — гаря́ча ка́ша!**」 with the dash.
- **Fix**: Change answer to `"Моя улюблена їжа — каша"` and add dash to `words` array.

### Issue 3: Wrong Proverb — Plan Says «Хліб — усьому голова» but Content Uses «Хліб — це життя́»
- **Location**: Line 86, Section "Паляниця (The Shibboleth Bread)"
- **Original**: 「«**Хліб — це життя́.**» (Bread is life.)」
- **Problem**: The plan explicitly specifies the connection to the proverb «Хліб — усьому голова» (Bread is the head of everything). This is the canonical, widely-known Ukrainian proverb. The content substitutes a different, less authoritative phrase. The research notes also list «Хліб — усьому голова» as the target proverb.
- **Fix**: Replace with «Хліб — усьому голова.» (Bread is the head of everything.)

### Issue 4: Zero Engagement Boxes (Audit Gate Failure)
- **Location**: Entire content — richness gap: engagement 0/2
- **Problem**: The audit shows 0 engagement boxes. There is one `[!cultural-note]` callout (line 90) but the richness metric counts engagement-type boxes (did-you-know, fun-fact, tip, etc.) and requires at least 2. This is a failing audit gate.
- **Fix**: Add at least 2 engagement callouts. Suggestions: (1) A `[!did-you-know]` about компот tradition in Section "Напої (Drinks)", (2) A `[!tip]` about remembering noun genders by their endings in Section "Їжа (Food)".

### Issue 5: Menu Reading Missing Prices (Plan Deviation)
- **Location**: Lines 139-145, Section "Практика (Practice)"
- **Problem**: The plan specifies "Recognizing food words in authentic format **with prices**" but the menu preview has no prices. This is a plan adherence gap — prices make the menu feel authentic and introduce number practice.
- **Fix**: Add Ukrainian hryvnia prices to each menu item (e.g., **Борщ украї́нський — 95 грн**).

### Issue 6: H1 Heading for Підсумок Instead of H2
- **Location**: Line 164
- **Original**: 「# Підсумок」
- **Problem**: All content sections should use H2 (`##`). The summary uses H1, which breaks the heading hierarchy and may cause rendering issues.
- **Fix**: Change `# Підсумок` to `## Підсумок`

---

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 86 | 「Хліб — це життя́.」 | «Хліб — усьому голова.» | Plan deviation (wrong proverb) |
| Act:215 | "Будь ласка чай" | "Будь ласка, чай" | Punctuation (missing comma) |
| Act:217 | "Моя улюблена їжа каша" | "Моя улюблена їжа — каша" | Punctuation (missing dash) |

---

## Fix Plan to Reach 9/10 (REQUIRED if score < 9.0)

### Activities: 7/10 → 9/10
**What to fix:**
1. Activities YAML line 215: Fix unjumble answer "Будь ласка чай" → "Будь ласка, чай" (add comma to words array)
2. Activities YAML line 217: Fix unjumble answer "Моя улюблена їжа каша" → "Моя улюблена їжа — каша" (add dash to words array)
3. Quiz item line 89-98: Question "What is the cultural significance of паляниця?" tests content recall, not language. Replace with a language-focused question (e.g., "Which adjective form matches the feminine noun каша?" or add a second fill-in exercise).

**Expected score after fix:** 9/10

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Line 3: Add explicit learning preview after the welcome — "Today you'll learn to name common foods and drinks, describe them with adjectives, and express your food preferences."
2. Line 164: Change `# Підсумок` to `## Підсумок`
3. Add 1-2 encouragement markers between sections (e.g., after Section "Їжа (Food)": "Great start! You already know 11 food words.")

**Expected score after fix:** 9/10

### Pedagogy: 8/10 → 9/10
**What to fix:**
1. Lines 139-145: Add prices to menu items per plan (e.g., "Борщ украї́нський — 95 грн")
2. Add engagement boxes: [!did-you-know] about компот in Section "Напої (Drinks)", [!tip] about gender endings in Section "Їжа (Food)"

**Expected score after fix:** 9/10

### Language: 8/10 → 9/10
**What to fix:**
1. Line 86: Replace 「«**Хліб — це життя́.**» (Bread is life.)」 with «**Хліб — усьому голова́.**» (Bread is the head of everything.) — the canonical proverb per plan and research notes.

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.1 + 9×1.2 + 9×1.3 + 9×1.3 + 8×1.0 + 9×1.5) / 8.9
= (13.5 + 9.9 + 10.8 + 11.7 + 11.7 + 8.0 + 13.5) / 8.9
= 79.1 / 8.9 = 8.9/10
```

---

## Audit Failures (from automated re-audit)

```
✨ Prose quality violations found: 1
❌ [INLINE_ENGLISH_IN_PROSE] Inline English translations in B1+ prose (5 occurrences): (Ukrainian borscht), (Meat with potato), (Fresh fruits) — breaks immersion target
📚 IMMERSION TOO LOW (15.6% vs 20-35% target)
--- STRICT GATES (Level A1) ---
Pedagogy     ❌ 1 violations
Immersion    ❌ 15.6% LOW (target 20-35% (M39))
📚 PEDAGOGICAL VIOLATIONS FOUND:
📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
→ 2 violations (minor)
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/food-vocabulary-audit.log for details)
--- VESUM WORD VERIFICATION FAILURES ---
These words were NOT found in the VESUM morphological dictionary.
Check if they are valid Ukrainian forms. Fix misspellings or Russianisms.
  ❌ `ий` (source: prose)
  ❌ `ій` (source: prose)
```

---

## File Contents (for reference)

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/food-vocabulary.md`

```markdown
## Їжа (Food)

Welcome back! Today we are diving into one of the most exciting and delicious topics in any language: food. Whether you are planning a trip to Ukraine, preparing to visit a Ukrainian restaurant, or just want to describe your daily meals, knowing how to talk about food is essential.

In Ukrainian, the word for food is **ї́жа**. Let's start by looking at some basic food categories. To make it easier for you to remember, we can group them logically. First, we have our staples and main dishes:
* **хліб** — bread
* **суп** — soup
* **борщ** — borscht (the iconic Ukrainian beet soup)
* **ка́ша** — porridge

Then, we have our proteins and other hearty foods:
* **м'я́со** — meat
* **ри́ба** — fish
* **сир** — cheese

And of course, we need our fresh produce:
* **о́вочі** — vegetables
* **фру́кти** — fruits
* **я́блуко** — apple
* **карто́пля** — potato

You already know that Ukrainian nouns have gender, and food words are no exception. Remembering the gender of your food is very important because you want your adjectives to agree with them! Let's organize these delicious items by gender:

**Masculine Nouns** (often end in a consonant):
* **хліб**
* **суп**
* **борщ**
* **сир**

**Feminine Nouns** (often end in **-а** or **-я**):
* **ка́ша**
* **ри́ба**
* **карто́пля**

**Neuter Nouns** (often end in **-о** or **-е**):
* **м'я́со**
* **я́блуко**
* **молоко́** (milk)

> [!tip] Як запам'ятати рід (How to Remember Gender)
> Look at the ending! Consonant → masculine, **-а/-я** → feminine, **-о/-е** → neuter. This pattern works for most food words.

When we describe our food, the adjectives change their endings to match these genders. Let's look at some common collocations (words that frequently go together) to build natural-sounding descriptions:
* **сві́жий хліб** — fresh bread (masculine adjective **сві́жий** for masculine **хліб**)
* **смачни́й борщ** — tasty borscht
* **дома́шній суп** — homemade soup
* **гаря́ча ка́ша** — hot porridge (feminine adjective **гаря́ча** for feminine **ка́ша**)
* **сві́же м'я́со** — fresh meat (neuter adjective **сві́же** for neuter **м'я́со**)

Notice how the endings change? **-ий** / **-ій** for masculine, **-а** / **-я** for feminine, and **-е** / **-о** for neuter. This is exactly what you practiced in earlier lessons, now applied to your dinner plate!

## Напої (Drinks)

Now that we have our food sorted out, we need something to drink! The Ukrainian word for drinks or beverages is **напо́ї**. Let's look at the most common ones you will encounter.
* **вода́** — water (feminine)
* **чай** — tea (masculine)
* **ка́ва** — coffee (feminine)
* **сік** — juice (masculine)
* **молоко́** — milk (neuter)
* **компо́т** — compote (a traditional sweet drink made from boiled fruit, masculine)

> [!did-you-know] Компо́т — не сік!
> Компот is not juice — it's a uniquely Ukrainian tradition of boiling seasonal fruits (cherries, plums, apples) in water to make a sweet drink. Every Ukrainian grandmother has her own recipe!

Just like with food, we use adjectives to describe our drinks, and gender agreement applies here too. Here are some typical combinations you will hear and use:
* **гаря́ча ка́ва** — hot coffee
* **холо́дна вода́** — cold water
* **апельси́новий сік** — orange juice

When you want to order a drink, you will use the verb **хоті́ти** (to want). Remember the Accusative case from our previous lessons? When you want something, that object is the direct receiver of your action. For masculine inanimate nouns and neuter nouns, the word stays exactly the same as its base form. For feminine nouns ending in **-а**, the ending changes to **-у**. For example:
* **Я хо́чу сік.** — I want juice. (masculine, stays the same)
* **Я хо́чу ка́ву.** — I want coffee. (**ка́ва** becomes **ка́ву**)
* **Я хо́чу чай.** — I want tea.
* **Я хо́чу воду́.** — I want water.

If you are at a café and want to be polite, you can use **Будь ла́ска** (please). For example, you can order by saying:
* **Будь ла́ска, чай і молоко́.** — Please, tea and milk.

Ukrainian culture has distinct regional preferences when it comes to hot drinks. Tea is incredibly popular throughout the country. You will often be offered traditional combinations, especially in colder months or if you have a cold. On the other hand, western Ukraine, particularly the city of Lviv, is famous for its coffee culture.

* **чай і мед** — tea and honey
* **чай і лимо́н** — tea and lemon
* **Льві́вська ка́ва** — Lviv coffee (legendary, often brewed in a special little pot over hot sand)

## Паляниця (The Shibboleth Bread)

You cannot talk about Ukrainian food without talking about bread. Let's take a cultural sidebar to look at a very specific and famous type of bread: **паляни́ця**.

**Паляни́ця** is a traditional round wheat bread baked in an oven. However, its significance goes far beyond the kitchen. In 2022, this simple word became a famous linguistic shibboleth — a test used to identify someone's origins based on their pronunciation. The specific sequence of sounds in **па-ля-ни-ця** is quite difficult for native Russian speakers to reproduce correctly, particularly the soft **-ля-** and the soft **-ця** at the end. For Ukrainians, saying **паляни́ця** is effortless, making it a powerful symbol of identity.

Bread, or **хліб**, has always held a sacred status in Ukrainian traditions. It is deeply respected and is never carelessly thrown away. This reverence is perfectly captured in a simple phrase:
«**Хліб — усьому́ голова́.**» (Bread is the head of everything.)

You will also see this respect in the traditional hospitality greeting known as **хліб-сіль** (bread and salt). When welcoming important guests, Ukrainians present them with a round loaf of bread resting on an embroidered towel, with a small dish of salt on top. The guest breaks off a piece of bread, dips it in the salt, and eats it as a sign of accepted hospitality and friendship.

> [!cultural-note] Українська гостинність (Ukrainian Hospitality)
> In Ukraine, offering food is the ultimate sign of care. If you visit a Ukrainian home, expect to be fed well! It is polite to try a little bit of everything offered to you.

## Мені подобається / Я не їм (Preferences)

Now we need to talk about your personal tastes. How do you express what you like or dislike? How do you explain dietary restrictions?

To say that you like a certain food, you can use the construction you learned earlier: **Мені́ подо́бається** (literally: "to me is pleasing"). You just add the food word in its normal dictionary form right after it.
* **Мені́ подо́бається борщ.** — I like borscht.
* **Мені́ подо́бається ка́ша.** — I like porridge.
* **Мені́ подо́бається украї́нський хліб.** — I like Ukrainian bread.

You can also use the verb **люби́ти** (to love or like strongly). With **люби́ти**, you must use the Accusative case for the food item:
* **Я люблю́ ка́ву з молоко́м.** — I love coffee with milk.
* **Я люблю́ сві́жі о́вочі.** — I love fresh vegetables.

But what if you don't like something, or simply don't eat it? To express dislikes or dietary restrictions, you will use negation with the verb **ї́сти** (to eat) or **пи́ти** (to drink). Just add **не** before the verb.
* **Я не їм м'я́со.** — I don't eat meat. (This is your go-to phrase if you are vegetarian!)
* **Я не п'ю ка́ву.** — I don't drink coffee.
* **Я не їм ри́бу.** — I don't eat fish.

Sometimes, avoiding a food isn't about preference, but health. If you have dietary needs, here are some incredibly practical survival phrases to memorize:
* **У мене́ алергі́я на горі́хи.** — I have an allergy to nuts.
* **У мене́ алергі́я на молоко́.** — I have an allergy to milk.
* **Я не мо́жу ї́сти глютен.** — I cannot eat gluten.

These phrases will ensure you can safely navigate any dinner invitation or restaurant menu!

## Практика (Practice)

It is time to put your new vocabulary to the test! Let's do some quick drills to build your automatic recall of these food terms.

**Categorization Drill: Їжа vs Напої**
Can you mentally sort these words into food or drinks?
**борщ, вода́, сир, сік, ка́ша, чай, м'я́со, компо́т**
* **Ї́жа**: борщ, сир, ка́ша, м'я́со
* **Напо́ї**: вода́, сік, чай, компо́т

**Gender Sorting & Adjective Matching Drill**
Let's practice matching adjectives to nouns based on gender. Try to connect the correct adjective form (hot) with the drink:
* m: **гаря́чий**
* f: **гаря́ча**
* n: **гаря́че**

1. ___ ка́ва (f.) → **гаря́ча ка́ва**
2. ___ чай (m.) → **гаря́чий чай**
3. ___ молоко́ (n.) → **гаря́че молоко́**

**Menu Reading Preview**
Imagine you are sitting in a cozy café in Kyiv. You open the menu, and you see these simple items. Can you recognize them?
* **Борщ украї́нський** — 95 грн (Ukrainian borscht)
* **М'я́со з карто́плею** — 145 грн (Meat with potato)
* **Сві́жі фру́кти** — 75 грн (Fresh fruits)
* **Ка́ва з молоко́м** — 55 грн (Coffee with milk)
* **Я́блучний сік** — 45 грн (Apple juice)

By simply looking for the root words you learned today, you can already navigate a basic Ukrainian menu!

**Preference Dialogues**
Let's look at how a conversation about food tastes might flow. Read this mini-dialogue out loud to practice:

> — **Що ти лю́биш ї́сти?**
> — What do you like to eat?
> — **Мені́ подо́бається борщ і хліб. А ти?**
> — I like borscht and bread. And you?
> — **Я люблю́ о́вочі, але́ я не їм м'я́со.**
> — I love vegetables, but I don't eat meat.
> — **Яка твоя́ улю́блена ї́жа?**
> — What is your favorite food?
> — **Моя́ улю́блена ї́жа — гаря́ча ка́ша!**
> — My favorite food is hot porridge!

Practice these questions with a friend or language partner. Ask them: «**Що ти лю́биш ї́сти?**»

## Підсумок
You have done a fantastic job today! Let's recap what we have covered. You learned essential vocabulary for both food (**ї́жа**) and drinks (**напо́ї**), including cultural staples like **борщ**, **хліб**, **паляни́ця**, and **компо́т**. You also learned how to identify the gender of these food items so you can pair them correctly with adjectives like **сві́жий** (fresh) and **гаря́чий** (hot). Finally, we practiced crucial survival phrases for expressing your tastes: **Мені́ подо́бається...**, **Я люблю́...**, and **Я не їм...**.

**Self-Check Questions:**
1. How do you say "I want water" using the correct Accusative ending?
2. What are three common Ukrainian drinks?
3. How do you politely tell a host "I don't eat meat"?
4. What is the cultural significance of the word **паляни́ця**?
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/food-vocabulary.yaml`

```yaml
- type: match-up
  title: "Match the Food Word to Its English Meaning"
  instruction: "Match each Ukrainian food or drink word on the left with its English translation on the right."
  pairs:
    - left: "хліб"
      right: "bread"
    - left: "борщ"
      right: "borscht"
    - left: "каша"
      right: "porridge"
    - left: "риба"
      right: "fish"
    - left: "сир"
      right: "cheese"
    - left: "вода"
      right: "water"
    - left: "кава"
      right: "coffee"
    - left: "сік"
      right: "juice"
    - left: "молоко"
      right: "milk"
    - left: "компот"
      right: "compote"
    - left: "овочі"
      right: "vegetables"
    - left: "фрукти"
      right: "fruits"

- type: quiz
  title: "Food and Drink Knowledge Check"
  instruction: "Choose the correct answer for each question."
  items:
    - question: "How do you say 'I want coffee' in Ukrainian, with the correct Accusative ending?"
      options:
        - text: "Я хочу каву"
          correct: true
        - text: "Я хочу кава"
          correct: false
        - text: "Я хочу кави"
          correct: false
        - text: "Я хочу каві"
          correct: false
      explanation: "Кава is feminine ending in -а, so in the Accusative it becomes каву."
    - question: "Which of these is a drink (напій), not a food?"
      options:
        - text: "компот"
          correct: true
        - text: "борщ"
          correct: false
        - text: "каша"
          correct: false
        - text: "картопля"
          correct: false
      explanation: "Компот is a traditional Ukrainian sweet drink made from boiled fruit."
    - question: "What gender is the word молоко?"
      options:
        - text: "neuter"
          correct: true
        - text: "masculine"
          correct: false
        - text: "feminine"
          correct: false
        - text: "plural"
          correct: false
      explanation: "Молоко ends in -о, which is a typical neuter ending."
    - question: "How do you say 'I don't eat meat' in Ukrainian?"
      options:
        - text: "Я не їм м'ясо"
          correct: true
        - text: "Я не їсти м'ясо"
          correct: false
        - text: "Я не люблю м'ясо"
          correct: false
        - text: "Я не хочу м'ясо"
          correct: false
      explanation: "'Я не їм м'ясо' uses the correct first-person form of їсти with negation."
    - question: "Which adjective form correctly matches the masculine noun хліб?"
      options:
        - text: "свіжий хліб"
          correct: true
        - text: "свіжа хліб"
          correct: false
        - text: "свіже хліб"
          correct: false
        - text: "свіжі хліб"
          correct: false
      explanation: "Хліб is masculine, so the adjective takes the masculine ending -ий: свіжий."
    - question: "What is the cultural significance of паляниця?"
      options:
        - text: "It became a linguistic shibboleth in 2022"
          correct: true
        - text: "It is the name of a traditional Ukrainian dance"
          correct: false
        - text: "It is the oldest Ukrainian recipe"
          correct: false
        - text: "It is a type of Ukrainian cheese"
          correct: false
      explanation: "Паляниця is a round wheat bread whose pronunciation became a famous identity test in 2022."
    - question: "Which construction expresses 'I like' in Ukrainian?"
      options:
        - text: "Мені подобається"
          correct: true
        - text: "Я подобається"
          correct: false
        - text: "Мене подобається"
          correct: false
        - text: "Мій подобається"
          correct: false
      explanation: "'Мені подобається' literally means 'to me is pleasing' — the Dative construction."
    - question: "What does 'Я хочу воду' mean?"
      options:
        - text: "I want water"
          correct: true
        - text: "I drink water"
          correct: false
        - text: "I like water"
          correct: false
        - text: "I have water"
          correct: false
      explanation: "Хочу means 'I want,' and воду is the Accusative form of вода."
    - question: "Which drink is Lviv especially famous for?"
      options:
        - text: "кава"
          correct: true
        - text: "чай"
          correct: false
        - text: "компот"
          correct: false
        - text: "сік"
          correct: false
      explanation: "Lviv is legendary for its coffee culture — Львівська кава is brewed over hot sand."
    - question: "How do you say 'I have an allergy to nuts' in Ukrainian?"
      options:
        - text: "У мене алергія на горіхи"
          correct: true
        - text: "Я алергія на горіхи"
          correct: false
        - text: "Мені алергія на горіхи"
          correct: false
        - text: "У мене горіхи алергія"
          correct: false
      explanation: "'У мене алергія на...' is the standard Ukrainian pattern for expressing allergies."

- type: fill-in
  title: "Complete the Food Sentence"
  instruction: "Choose the correct word to fill in the blank."
  items:
    - sentence: "Мені подобається ___ ."
      answer: "борщ"
      options: ["борщ", "борщу", "борщем", "борщі"]
      explanation: "After 'подобається' the noun stays in the Nominative case: борщ."
    - sentence: "Я хочу ___ ."
      answer: "каву"
      options: ["каву", "кава", "каві", "кавою"]
      explanation: "Хотіти takes the Accusative. Feminine кава becomes каву."
    - sentence: "Я не п'ю ___ ."
      answer: "молоко"
      options: ["молоко", "молока", "молоку", "молоком"]
      explanation: "Молоко is neuter. Neuter nouns in the Accusative stay the same as Nominative."
    - sentence: "Я люблю ___ овочі."
      answer: "свіжі"
      options: ["свіжі", "свіжий", "свіжа", "свіже"]
      explanation: "Овочі is plural, so the adjective takes the plural form: свіжі."
    - sentence: "Будь ласка, ___ і молоко."
      answer: "чай"
      options: ["чай", "чаю", "чаєм", "чаї"]
      explanation: "Чай is masculine. When listing items in a request, use the Nominative form."
    - sentence: "Я не їм ___ ."
      answer: "рибу"
      options: ["рибу", "риба", "рибі", "рибою"]
      explanation: "Їсти takes the Accusative. Feminine риба becomes рибу."
    - sentence: "___ каша — мій улюблений сніданок."
      answer: "Гаряча"
      options: ["Гаряча", "Гарячий", "Гаряче", "Гарячі"]
      explanation: "Каша is feminine, so the adjective takes the feminine form: гаряча."
    - sentence: "Моя улюблена їжа — ___ борщ."
      answer: "смачний"
      options: ["смачний", "смачна", "смачне", "смачні"]
      explanation: "Борщ is masculine, so the adjective takes the masculine form: смачний."

- type: group-sort
  title: "Sort into Food or Drinks"
  instruction: "Drag each word into the correct category."
  groups:
    - name: "Їжа (Food)"
      items: ["хліб", "борщ", "каша", "м'ясо", "риба", "сир"]
    - name: "Напої (Drinks)"
      items: ["вода", "чай", "кава", "сік", "молоко", "компот"]

- type: group-sort
  title: "Sort Food by Gender"
  instruction: "Sort these food and drink words by their grammatical gender."
  groups:
    - name: "Masculine"
      items: ["хліб", "суп", "борщ", "сир", "чай", "сік"]
    - name: "Feminine"
      items: ["каша", "риба", "картопля", "вода", "кава"]
    - name: "Neuter"
      items: ["м'ясо", "яблуко", "молоко"]

- type: unjumble
  title: "Put the Words in Order"
  instruction: "Arrange the words to form a correct Ukrainian sentence."
  items:
    - words: ["подобається", "Мені", "борщ"]
      answer: "Мені подобається борщ"
    - words: ["хочу", "Я", "каву"]
      answer: "Я хочу каву"
    - words: ["не", "Я", "м'ясо", "їм"]
      answer: "Я не їм м'ясо"
    - words: ["люблю", "Я", "овочі", "свіжі"]
      answer: "Я люблю свіжі овочі"
    - words: ["ласка,", "чай", "Будь"]
      answer: "Будь ласка, чай"
    - words: ["улюблена", "їжа", "—", "каша", "Моя"]
      answer: "Моя улюблена їжа — каша"

- type: true-false
  title: "True or False?"
  instruction: "Decide whether each statement is true or false."
  items:
    - statement: "The word борщ is a masculine noun in Ukrainian."
      correct: true
      explanation: "Борщ ends in a consonant, which is typical for masculine nouns."
    - statement: "To say 'I want coffee,' you say 'Я хочу кава.'"
      correct: false
      explanation: "Feminine nouns ending in -а change to -у in the Accusative: Я хочу каву."
    - statement: "Молоко is a feminine noun."
      correct: false
      explanation: "Молоко ends in -о, making it neuter."
    - statement: "Паляниця is a traditional round wheat bread."
      correct: true
      explanation: "Паляниця is indeed a traditional Ukrainian round wheat bread baked in an oven."
    - statement: "The phrase 'Мені подобається' literally means 'I like.'"
      correct: false
      explanation: "It literally means 'to me is pleasing' — it uses a Dative construction, not a direct 'I like' pattern."
    - statement: "To express an allergy in Ukrainian, you say 'У мене алергія на...'."
      correct: true
      explanation: "This is the standard Ukrainian pattern for stating allergies."
    - statement: "The adjective свіжий becomes свіже when describing молоко."
      correct: true
      explanation: "Молоко is neuter, so the adjective takes the neuter ending -е: свіже молоко."
    - statement: "Компот is a carbonated soft drink."
      correct: false
      explanation: "Компот is a traditional Ukrainian sweet drink made by boiling fruit in water — it is not carbonated."
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/food-vocabulary.yaml`

```yaml
items:
  - lemma: "їжа"
    translation: "food"
    pos: "noun"
    gender: "f"
    usage: "General word for food"
    example: "Моя улюблена їжа — борщ."
  - lemma: "хліб"
    translation: "bread"
    pos: "noun"
    gender: "m"
    usage: "Sacred symbol in Ukrainian culture"
    example: "Свіжий хліб дуже смачний."
  - lemma: "борщ"
    translation: "borscht"
    pos: "noun"
    gender: "m"
    usage: "National dish of Ukraine"
    example: "Смачний борщ на обід."
  - lemma: "м'ясо"
    translation: "meat"
    pos: "noun"
    gender: "n"
    usage: "Я не їм м'ясо (vegetarian phrase)"
    example: "Свіже м'ясо на ринку."
  - lemma: "овочі"
    translation: "vegetables"
    pos: "noun"
    notes: "plural noun (singular: овоч)"
    example: "Я люблю свіжі овочі."
  - lemma: "фрукти"
    translation: "fruits"
    pos: "noun"
    notes: "plural noun (singular: фрукт)"
    example: "Свіжі фрукти на столі."
  - lemma: "вода"
    translation: "water"
    pos: "noun"
    gender: "f"
    usage: "Accusative: воду"
    example: "Я хочу воду."
  - lemma: "кава"
    translation: "coffee"
    pos: "noun"
    gender: "f"
    usage: "Accusative: каву"
    example: "Я люблю каву з молоком."
  - lemma: "чай"
    translation: "tea"
    pos: "noun"
    gender: "m"
    usage: "Very popular across Ukraine"
    example: "Будь ласка, чай і молоко."
  - lemma: "молоко"
    translation: "milk"
    pos: "noun"
    gender: "n"
    example: "Гаряче молоко на вечір."
  - lemma: "сік"
    translation: "juice"
    pos: "noun"
    gender: "m"
    example: "Апельсиновий сік, будь ласка."
  - lemma: "суп"
    translation: "soup"
    pos: "noun"
    gender: "m"
    example: "Домашній суп дуже смачний."
  - lemma: "паляниця"
    translation: "palianytsia (round wheat bread)"
    pos: "noun"
    gender: "f"
    notes: "Cultural shibboleth since 2022"
    example: "Паляниця — традиційний хліб."
  - lemma: "каша"
    translation: "porridge"
    pos: "noun"
    gender: "f"
    usage: "Traditional Ukrainian breakfast"
    example: "Гаряча каша на сніданок."
  - lemma: "компот"
    translation: "compote (sweet fruit drink)"
    pos: "noun"
    gender: "m"
    example: "Солодкий компот з фруктів."
  - lemma: "риба"
    translation: "fish"
    pos: "noun"
    gender: "f"
    example: "Я не їм рибу."
  - lemma: "сир"
    translation: "cheese"
    pos: "noun"
    gender: "m"
    notes: "Not to confuse with Russian сыр"
    example: "Свіжий сир на сніданок."
  - lemma: "яблуко"
    translation: "apple"
    pos: "noun"
    gender: "n"
    example: "Свіже яблуко дуже смачне."
  - lemma: "картопля"
    translation: "potato"
    pos: "noun"
    gender: "f"
    example: "М'ясо з картоплею."
  - lemma: "напій"
    translation: "drink, beverage"
    pos: "noun"
    gender: "m"
    notes: "Plural: напої"
    example: "Який напій ти хочеш?"
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
- Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/food-vocabulary.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/food-vocabulary.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/food-vocabulary.yaml`

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
