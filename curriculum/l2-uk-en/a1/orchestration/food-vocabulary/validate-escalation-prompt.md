        # Escalation Fix — validate

        You are an expert Ukrainian language editor. The previous agent could not fix
        these audit violations. Fix them precisely.

        ## Audit Errors

        ```
        Auditing: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/food-vocabulary.md
Mode: content-only (activities deferred)
Saving log to: curriculum/l2-uk-en/a1/audit/food-vocabulary-audit.log


========================================
Error: No YAML frontmatter found (checked embedded and sidecar).

Critical Failures:
  • No YAML frontmatter found

❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/food-vocabulary-audit.log for details)

Running RAG word verification...
Verifying: food-vocabulary.md
  VESUM misses: 2 — querying RAG...
[embed] Loading BGE-M3 from BAAI/bge-m3...

Fetching 30 files:   0%|          | 0/30 [00:00<?, ?it/s]
Fetching 30 files: 100%|██████████| 30/30 [00:00<00:00, 40149.69it/s]
[embed] BGE-M3 loaded.
You're using a XLMRobertaTokenizerFast tokenizer. Please note that with a fast tokenizer, using the `__call__` method is faster than using a method to encode the text followed by a call to the `pad` method to get a padded encoding.
  Words: 79 | VESUM: 77 (97.5%) | RAG: 2 | Not found: 0
  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/food-vocabulary-rag-audit.md
✅ RAG verification: all words verified

No status JSON produced by audit
VESUM: 77/79 (97%) verified
⚠️ VESUM not found (2): ий, ій
        ```

        ## Current Content of Affected Section(s)

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
«**Хліб — це життя́.**» (Bread is life.)

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
* **Борщ украї́нський** (Ukrainian borscht)
* **М'я́со з карто́плею** (Meat with potato)
* **Сві́жі фру́кти** (Fresh fruits)
* **Ка́ва з молоко́м** (Coffee with milk)
* **Я́блучний сік** (Apple juice)

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

# Підсумок
You have done a fantastic job today! Let's recap what we have covered. You learned essential vocabulary for both food (**ї́жа**) and drinks (**напо́ї**), including cultural staples like **борщ**, **хліб**, **паляни́ця**, and **компо́т**. You also learned how to identify the gender of these food items so you can pair them correctly with adjectives like **сві́жий** (fresh) and **гаря́чий** (hot). Finally, we practiced crucial survival phrases for expressing your tastes: **Мені́ подо́бається...**, **Я люблю́...**, and **Я не їм...**.

**Self-Check Questions:**
1. How do you say "I want water" using the correct Accusative ending?
2. What are three common Ukrainian drinks?
3. How do you politely tell a host "I don't eat meat"?
4. What is the cultural significance of the word **паляни́ця**?

        ## File Path

        `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/food-vocabulary.md`

        ## Instructions

        1. Fix ONLY the violations listed above
        2. For euphony (в/у, і/й): apply Ukrainian euphony rules strictly
        3. Do NOT add or remove content — only fix the specific violations
        4. Preserve all markdown formatting, headers, and structure

        ## Output Format (MANDATORY)

        Output ONLY the fixed section(s) between delimiters:

        ```
        ===SECTION_FIX_START===
        ## {section title}
        {fixed section content}
        ===SECTION_FIX_END===
        ```

        If multiple sections need fixing, output each in its own delimiter block.
        Do NOT output anything else — no explanations, no commentary.
