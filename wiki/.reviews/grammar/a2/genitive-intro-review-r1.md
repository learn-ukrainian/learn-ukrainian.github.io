✅ Message sent to Gemini (ID: 28071) [auto-acked: self-addressed]

🚀 Invoking Gemini to process message #28071...
📨 Message #28071
   From: gemini → To: gemini
   Type: query
   Task: wiki-review-a2-genitive-intro-r1
   Time: 2026-04-05T18:47:46.571567+00:00

============================================================

You are a HARSH adversarial reviewer of a grammar brief for the Ukrainian language curriculum wiki. Your job is to find problems, not praise.

Track: a2, Slug: genitive-intro, Round: 1

## Review Rubric (score EACH dimension 1-10, then average)

1. **Factual accuracy** — every claim must have evidence from sources. Vague or unsourced claims → deduct points.
2. **Ukrainian language quality** — check for Russianisms (кон→кін), surzhyk (шо→що), calques (приймати душ→брати душ). Even ONE Russianism = max 7/10.
3. **Decolonization** — is Ukrainian presented on its own terms? Any 'like Russian but...' framing = max 6/10.
4. **Completeness** — does it cover ALL aspects a module writer needs? Missing sections or shallow treatment → deduct.
5. **Actionable guidance** — can a writer actually USE this? Generic advice like 'teach it well' = max 5/10. Must have specific examples, sequences, exercises.

## Rules
- Score each dimension separately, then give weighted average.
- Be honest. If the article is excellent, say so. 10/10 IS possible.
- 9/10 = excellent with minor issues. 8/10 = good. 7/10 = needs work.
- Output a <fixes> block ONLY if there are real issues to fix. If the article is clean, output <fixes></fixes> (empty) and the review stops.
- Do NOT invent problems. Fabricated issues waste rebuild cycles.

## Output format

Dimension scores:
1. Factual: X/10 — [evidence]
2. Language: X/10 — [evidence]
3. Decolonization: X/10 — [evidence]
4. Completeness: X/10 — [evidence]
5. Actionable: X/10 — [evidence]

**Overall: X/10**

<fixes>
old: exact text to find in the article
new: replacement text
---
old: another exact find
new: another replacement
</fixes>

## Article to review

# Граматика A2: У мене немає...

<!-- wiki-meta
slug: genitive-intro
domain: grammar/a2
tracks: [a2, b1]
sources: [no-source]
compiled: 2026-04-05
-->

## Як це пояснюють у школі (How Schools Teach This)

The concept of using the genitive case for negation is fundamental and introduced early in Ukrainian schools, typically around Grade 5, once students have a firm grasp of the nominative case and basic sentence structure. The topic is almost always presented as a direct contrast to possession.

**Progression:**

1.  **Possession (Nominative Case):** The curriculum first establishes the structure `У мене є...` + **Nominative** (`хто? що?`).
    *   *Example (Заболотний, 5 клас):* У мене є **брат**. У подруги є **книга**.

2.  **Absence/Negation (Genitive Case):** Immediately after, the negative form is introduced using the impersonal verb `немає` (a contraction of `не має`), which obligatorily requires the object to be in the **Genitive** case (`кого? чого?`).
    *   *Example (Заболотний, 5 клас):* У мене немає **брата**. У подруги немає **книги**.

**Terminology:**

*   **Називний відмінок (Nominative Case):** Used for the subject and with `є`.
*   **Родовий відмінок (Genitive Case):** The "go-to" case for absence, negation, and quantity. It answers the questions `кого?` (whom?) and `чого?` (what?).
*   **Заперечення (Negation):** The key concept linking `немає` to the genitive case.

Ukrainian textbooks like those by Avramenko and Zabolotnyi emphasize rote memorization of this `немає + Genitive` pairing. They use simple substitution drills and question-answer pairs (`У тебе є собака?` — `Ні, у мене немає собаки.`) to solidify the pattern before introducing complex endings. The focus is on the functional use of the case to express absence.

## Повна парадигма (Full Paradigm)

The genitive case is used to show the absence of an object when using `немає`. All nouns, pronouns, and adjectives modifying them must be in the genitive case.

### I. Nouns (Іменники)

The endings depend on the noun's gender and declension.

**Masculine (Чоловічий рід)**
This is the most complex gender in the genitive, with two possible endings for inanimate nouns: **-а/-я** and **-у/-ю**. The choice is lexical and often a point of difficulty. (See Decolonization Notes for the key difference from Russian).

| Nominative | Genitive (-а/-я) - *Concrete* | Genitive (-у/-ю) - *Abstract/Mass* | Example Sentence |
| :--- | :--- | :--- | :--- |
| стіл | **стола** | | У мене немає **стола**. |
| брат | **брата** | | У неї немає **брата**. |
| трамвай | **трамвая** | | Тут немає **трамвая**. |
| комп'ютер | **комп'ютера** | | У нас немає **комп'ютера**. |
| --- | --- | --- | --- |
| цукор | | **цукру** | У каві немає **цукру**. |
| простір | | **простору** | У кімнаті немає **простору**. |
| біль | | **болю** | Я не відчуваю **болю**. |
| час | | **часу** | На це немає **часу**. |
| телефон | **телефона** | **телефону** (both used) | У мене немає **телефону**. |

**Feminine (Жіночий рід)**
Much more regular than masculine.

| Nominative | Genitive | Example Sentence |
| :--- | :--- | :--- |
| мама | **мами** | **Мами** немає вдома. |
| книга | **книги** | У мене немає цієї **книги**. |
| пісня | **пісні** | Я не знаю цієї **пісні**. |
| ніч | **ночі** | Він не спить до **ночі**. |
| сіль | **солі** | У супі немає **солі**. |

**Neuter (Середній рід)**

| Nominative | Genitive | Example Sentence |
| :--- | :--- | :--- |
| вікно | **вікна** | У кімнаті немає **вікна**. |
| сонце | **сонця** | Сьогодні на небі немає **сонця**. |
| море | **моря** | Поблизу немає **моря**. |
| ім'я | **імені** | Його **імені** немає у списку. |

**Plural (Множина)**
The genitive plural is used to express the absence of multiple items.

| Nominative Plural | Genitive Plural | Example Sentence |
| :--- | :--- | :--- |
| столи | **столів** | У класі немає **столів**. |
| книги | **книг** | На полиці немає **книг**. |
| вікна | **вікон** | У будинку немає **вікон**. |
| друзі | **друзів** | У мене немає **друзів** у цьому місті. |
| місця | **місць** | У театрі немає вільних **місць**. |

### II. Adjectives & Pronouns

These must also be in the genitive case, agreeing in gender and number with the noun they modify.

| Gender / Number | Nominative Adjective | Genitive Adjective | Nominative Pronoun | Genitive Pronoun | Example Sentence |
|:--- |:--- |:--- |:--- |:--- |:--- |
| Masculine | новий | **нового** | цей | **цього** | У мене немає **нового/цього** стола. |
| Feminine | нова | **нової** | ця | **цієї** | У мене немає **нової/цієї** книги. |
| Neuter | нове | **нового** | це | **цього** | У мене немає **нового/цього** вікна. |
| Plural | нові | **нових** | ці | **цих** | У мене немає **нових/цих** друзів. |

## Частотність і пріоритети (Frequency & Priorities)

At the A2 level, the priority is mastering the core function: expressing the absence of everyday objects.

1.  **Highest Priority:** `немає` + **singular nouns**.
    *   **Feminine `-и/-і`:** `води`, `кави`, `роботи`, `машини`, `гривні`. This is the most common and regular pattern.
    *   **Masculine `-а/-я` (concrete):** `брата`, `друга`, `кота`, `комп'ютера`.
    *   **Masculine `-у/-ю` (abstract/mass):** `часу`, `цукру`, `інтернету`, ` настрою`. The word `часу` is critically important: `Немає часу` (There's no time).
    *   **Neuter `-а/-я`:** `молока`, `пива`, `вина`, `місця`.

2.  **Second Priority:** `немає` + **personal pronouns**.
    *   `Мене/тебе/його/її/нас/вас/їх немає...` (I'm/you're/he's/she's/we're/you're/they're not...). This is extremely common for indicating someone is not present. Example: `Його немає вдома` (He is not at home).

3.  **Third Priority:** `немає` + **adjective + noun**.
    *   Focus on simple, common adjectives: `доброго настрою`, `гарячої води`, `вільного часу`, `жодного уявлення` (no idea).

The genitive plural (`-ів`, `-ів`, empty ending) can wait until B1, except for very high-frequency phrases like `немає проблем`.

## Типові помилки L2 (Common L2 Errors)

1.  **Using Nominative/Accusative:** The most common error is transferring the English structure "I don't have a book" directly.
    *   *Error:* `У мене немає *книга*` (Nominative) or `... *книгу*` (Accusative).
    *   *Correction:* `У мене немає **книги**` (Genitive).
    *   **Prevention:** Drill the `немає + Genitive` rule as an unbreakable pair. Contrast it directly with `є + Nominative`.

2.  **Masculine `-а` vs. `-у` Confusion:** English speakers struggle with the `‑а/‑я` vs. `‑у/‑ю` distinction for masculine nouns because it lacks a clear, simple rule. They often default to `-а`.
    *   *Error:* `У мене немає *часа*`.
    *   *Correction:* `У мене немає **часу**`.
    *   **Prevention:** Teach the most frequent `-у` nouns (`часу`, `цукру`, `інтернету`, `простору`, `дощу`, `снігу`) as lexical items. Explain the general (but not perfect) rule: `-а/я` for countable, defined objects; `-у/ю` for mass nouns, abstract concepts, places, feelings.

3.  **Adjective Agreement Failure:** Forgetting to put the adjective in the genitive.
    *   *Error:* `У мене немає *гаряча* води`.
    *   *Correction:* `У мене немає **гарячої** води`.
    *   **Prevention:** Teach adjective-noun pairs as chunks (`вільний час` -> `немає вільного часу`).

## Деколонізаційні застереження (Decolonization Notes)

Teaching the Ukrainian genitive as a "variant of Russian" is a critical pedagogical error. They are distinct systems.

1.  **The `-а`/`-у` Distinction IS UKRAINIAN:** The most significant difference is the masculine genitive singular.
    *   **Ukrainian:** Maintains the historical Proto-Slavic distinction between the genitive (for animate/concrete nouns, `-а`) and the partitive (for mass/abstract nouns, `-у`). This makes the `-у` ending extremely common and productive. (`немає сиру`, `немає звуку`).
    *   **Russian:** Has largely lost the productive partitive `-у` ending in the modern standard language, leveling it in favor of `-а` for most nouns (`нет сыра`, `нет звука`). The `-у` ending remains only in a few specific contexts (e.g., `стакан чаю`).
    *   **Teaching Trap:** Presenting the Ukrainian `-у` ending as a rare exception. It is not. It is a core feature of the language's grammar. The writer should provide *many* examples of `немає + ...-у`.

2.  **Pronominal Forms:** Personal pronoun forms can differ.
    *   *He/Him:* Ukrainian `його` vs. Russian `его` (pronounced `yevo`).
    *   *She/Her:* Ukrainian `її` vs. Russian `её` (pronounced `yeyo`).
    *   *They/Them:* Ukrainian `їх` vs. Russian `их`.
    *   Using Russian forms is a common sign of Surzhyk and should be corrected.

3.  **Vocabulary:** Avoid using Russian loanwords when a native Ukrainian equivalent exists. Example: `немає грошей` (Ukrainian) not `*нєт дєнєг*`.

## Природні приклади (Natural Examples)

1.  У мене немає **часу** на це. (I don't have time for this.)
2.  Вибачте, у нас немає **вільних місць**. (Sorry, we don't have any free tables/seats.)
3.  У холодильнику немає **молока**. (There's no milk in the fridge.)
4.  Чому сьогодні немає **гарячої води**? (Why is there no hot water today?)
5.  У мене немає **жодного уявлення**, де він. (I have no idea where he is.)
6.  **Тараса** сьогодні немає на роботі. (Taras isn't at work today.)
7.  У цій каві зовсім немає **цукру**. (There's no sugar at all in this coffee.)
8.  Без **тебе** немає **сенсу**. (Without you, there is no meaning/point.)
9.  На жаль, **квитків** уже немає. (Unfortunately, there are no more tickets.)
10. У мене немає **готівки**, тільки картка. (I don't have cash, only a card.)
11. Якщо немає **питань**, тоді все. (If there are no questions, then that's all.)
12. У дитини ще немає **імені**. (The baby doesn't have a name yet.)
13. Влітку тут немає **снігу**. (There is no snow here in the summer.)

## Зв'язки з іншими темами (Connections)

*   **Prerequisite:** **Possession (`У мене є...`)**. This topic is the logical "other side of the coin" to expressing possession with the nominative case.
*   **Foundation for Genitive Case:** Mastering `немає` provides the first, highest-frequency context for the genitive case. This builds a strong foundation for later topics that also require the genitive:
    *   **Quantities:** `багато/мало/кілька` + Genitive Plural (`багато друзів`).
    *   **Numbers:** `два/три/чотири` + Genitive Singular (`два столи`); `п'ять` and more + Genitive Plural (`п'ять столів`).
    *   **Prepositions:** `без`, `для`, `від`, `до`, `біля` + Genitive (`без цукру`, `для мами`).
*   **Foundation for Other Negation:** The concept of using a different case for negation extends to other verbs, such as `не знати`, `не бачити`, `не хотіти` + Genitive (though accusative is also possible and increasingly common in modern speech). `Немає` is the strictest.

## Пов'язані статті (Related Articles)

*   `grammar/a1/possession-ye`
*   `grammar/b1/genitive-quantity`
*   `grammar/b1/genitive-prepositions`
*   `vocabulary/a2/common-foods`
*   `vocabulary/a2/daily-routines`


============================================================
📎 Attached Data:
{"to_model": "gemini-3.1-pro-preview"}

🤖 Processing with Gemini (gemini-3.1-pro-preview) [sync, 30 min timeout]...
  [gemini] attempt 1/5, model=gemini-3.1-pro-preview, prompt=13743 chars: You are Gemini, participating in a collaboration with Claude. This is a message from Claude to you:  --- You are a HARSH adversarial reviewer of a grammar brief for the Ukrainian language curriculum w...
Dimension scores:
1. Factual: 7/10 — The article erroneously lists genitive plural endings as `(-ів, -ів, empty ending)`, missing `-їв` and `-ей`. Additionally, claiming `немає` is simply a "contraction" of `не має` ignores the critical functional difference in modern grammar where impersonal `немає` demands the Genitive case, while the personal verb `не має` functions differently.
2. Language: 6/10 — Contains a blatant English calque: `У мене немає жодного уявлення` is a literal translation of "I have no idea", which is unnatural in Ukrainian (native speakers use `я гадки не маю` or similar verbs, not `немає + noun`). Also, giving `телефона` as an equal variant to `телефону` for the device contradicts standard dictionaries like ULIF.
3. Decolonization: 4/10 — Fails the core rubric instruction ("Any 'like Russian but...' framing = max 6/10"). An entire section is dedicated to contrasting Ukrainian with Russian endings and warning L2 English learners not to use Russian pronouns (`его`, `их`) or slang (`нєт дєнєг`). This assumes the learner's baseline is Russian, centering the imperial language instead of teaching Ukrainian on its own terms.
4. Completeness: 8/10 — Covers the major paradigms well, but completely misses "Double Negation" (`нікого немає`, `нічого немає`), which is a critical and high-frequency Genitive pairing that must be taught at the A2 level.
5. Actionable: 8/10 — Provides solid priority levels and L2 error prevention tips. However, it lacks specific guidance to drill double negation structures alongside the standard nouns and pronouns.

**Overall: 6.6/10**

<fixes>
old: Immediately after, the negative form is introduced using the impersonal verb `немає` (a contraction of `не має`), which obligatorily requires the object to be in the **Genitive** case (`кого? чого?`).
new: Immediately after, the negative form is introduced using the impersonal predicate `немає` (historically a contraction of `не має`, but functioning as an independent impersonal word), which obligatorily requires the object to be in the **Genitive** case (`кого? чого?`).
---
old: | телефон | **телефона** | **телефону** (both used) | У мене немає **телефону**. |
new: | телефон | | **телефону** | У мене немає **телефону**. |
---
old: 2.  **Second Priority:** `немає` + **personal pronouns**.
    *   `Мене/тебе/його/її/нас/вас/їх немає...` (I'm/you're/he's/she's/we're/you're/they're not...). This is extremely common for indicating someone is not present. Example: `Його немає вдома` (He is not at home).

3.  **Third Priority:** `немає` + **adjective + noun**.
    *   Focus on simple, common adjectives: `доброго настрою`, `гарячої води`, `вільного часу`, `жодного уявлення` (no idea).
new: 2.  **Second Priority:** `немає` + **personal pronouns** and **double negation**.
    *   **Pronouns:** `Мене/тебе/його/її/нас/вас/їх немає...` (I'm/you're/he's/she's/we're/you're/they're not...). This is extremely common for indicating someone is not present. Example: `Його немає вдома` (He is not at home).
    *   **Double Negation:** `Нічого немає` (There is nothing / I have nothing) and `Нікого немає` (There is no one). This is a critical A2 concept.

3.  **Third Priority:** `немає` + **adjective + noun**.
    *   Focus on simple, common adjectives: `доброго настрою`, `гарячої води`, `вільного часу`, `жодного бажання` (no desire at all).
---
old: 5.  У мене немає **жодного уявлення**, де він. (I have no idea where he is.)
new: 5.  У мене немає **жодного бажання** туди йти. (I have no desire at all to go there.)
---
old: The genitive plural (`-ів`, `-ів`, empty ending) can wait until B1, except for very high-frequency phrases like `немає проблем`.
new: The genitive plural (`-ів`, `-їв`, empty ending, `-ей`) can wait until B1, except for very high-frequency phrases like `немає проблем`.
---
old: ## Деколонізаційні застереження (Decolonization Notes)

Teaching the Ukrainian genitive as a "variant of Russian" is a critical pedagogical error. They are distinct systems.

1.  **The `-а`/`-у` Distinction IS UKRAINIAN:** The most significant difference is the masculine genitive singular.
    *   **Ukrainian:** Maintains the historical Proto-Slavic distinction between the genitive (for animate/concrete nouns, `-а`) and the partitive (for mass/abstract nouns, `-у`). This makes the `-у` ending extremely common and productive. (`немає сиру`, `немає звуку`).
    *   **Russian:** Has largely lost the productive partitive `-у` ending in the modern standard language, leveling it in favor of `-а` for most nouns (`нет сыра`, `нет звука`). The `-у` ending remains only in a few specific contexts (e.g., `стакан чаю`).
    *   **Teaching Trap:** Presenting the Ukrainian `-у` ending as a rare exception. It is not. It is a core feature of the language's grammar. The writer should provide *many* examples of `немає + ...-у`.

2.  **Pronominal Forms:** Personal pronoun forms can differ.
    *   *He/Him:* Ukrainian `його` vs. Russian `его` (pronounced `yevo`).
    *   *She/Her:* Ukrainian `її` vs. Russian `её` (pronounced `yeyo`).
    *   *They/Them:* Ukrainian `їх` vs. Russian `их`.
    *   Using Russian forms is a common sign of Surzhyk and should be corrected.

3.  **Vocabulary:** Avoid using Russian loanwords when a native Ukrainian equivalent exists. Example: `немає грошей` (Ukrainian) not `*нєт дєнєг*`.
new: ## Деколонізаційні застереження (Decolonization Notes)

Teaching the Ukrainian genitive must be done on its own terms, without treating its complex endings as "exceptions" to some generalized Slavic rule.

1.  **The `-у` Ending is Core, Not an Exception:** The masculine genitive singular `-у/-ю` ending is highly productive in Ukrainian for abstract concepts, mass nouns, feelings, and spaces (`немає сиру`, `немає звуку`, `немає простору`). 
    *   **Teaching Trap:** Do not frame `-у` as a "special partitive" exception. It is an equal half of the masculine genitive system. The writer should provide *many* equal examples of `немає + ...-у` alongside `-а` nouns.

2.  **Avoid False Friends in Genitive:** Ensure that words expressing absence don't accidentally rely on borrowed mental models.
    *   Use native Ukrainian collocations for absence, rather than calquing English idioms (e.g., avoiding "немає жодного уявлення" for "have no idea", as Ukrainian prefers different verbs for this entirely, like "гадки не маю").

3.  **No Contrastive Instruction:** Do not warn L2 English learners against Russian pronoun forms or Russian slang. This curriculum is for English speakers learning Ukrainian from scratch; comparing Ukrainian to Russian only centers the imperial language and pollutes their learning environment. Teach Ukrainian on its own native foundation.
</fixes>


────────────────────────────────────────
✅ Gemini finished (6731 chars)
✅ Message sent to Claude (ID: 28072)
✓ Message 28072 acknowledged
   Auto-acknowledged reply #28072 (stdout delivery — no inbox accumulation)
   ℹ️  No issue number in task_id 'wiki-review-a2-genitive-intro-r1' — skipping GH posting (review saved to orchestration/)
✓ Message 28071 acknowledged
