        # Escalation Fix — validate

        You are an expert Ukrainian language editor. The previous agent could not fix
        these audit violations. Fix them precisely.

        ## Audit Errors

        ```
             Практика (Practice)                     203 /  150  ✅ (+53)
     ──────────────────────────────────────────────────────────────
     TOTAL                                  1805 / 1200  ✅ (+605)

--- STRICT GATES (Level A1) ---
Persona      ✅ Persona Defined
Words        ✅ 2006/1200 (raw: 2092)
Activities   ⏳ Deferred (content-only audit)
Density      ⏳ Deferred (content-only audit)
Unique_types ⏳ Deferred (content-only audit)
Priority     ⏳ Deferred (content-only audit)
Engagement   ✅ 1/1
Audio        ℹ️ No audio
Vocab        ⏳ Deferred (content-only audit)
Structure    ✅ Valid Structure
Lint         ✅ Clean Format
Pedagogy     ✅ Level-appropriate
Content_heavy ⏳ Deferred (content-only audit)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ⏳ Deferred (content-only audit)
Research     ⚠️ Refresh recommended: Research has 2+ cultural hooks but content has no cultural section
Immersion    ⚠️ 13.5% (target 15-30%, within tolerance (M32))

📋 TEMPLATE COMPLIANCE VIOLATIONS FOUND:
  🔴 [MISSING_REQUIRED_SECTION] Missing required section 'Warm-up' per template 'a1-module-template.md'
     → FIX: Add '## Warm-up' section as specified in docs/l2-uk-en/templates/a1-module-template.md.md
  🔴 [MISSING_REQUIRED_SECTION] Missing required section 'Presentation' per template 'a1-module-template.md'
     → FIX: Add '## Presentation' section as specified in docs/l2-uk-en/templates/a1-module-template.md.md


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
   → 2 violations (minor)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/genitive-prepositions-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/genitive-prepositions.json

❌ AUDIT FAILED. Correct errors before proceeding.

Critical Failures:
  • 2 Critical Template Violations

❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/genitive-prepositions-audit.log for details)

Running RAG word verification...
Verifying: genitive-prepositions.md
  VESUM misses: 6 — querying RAG...
[embed] Loading BGE-M3 from BAAI/bge-m3...

Fetching 30 files:   0%|          | 0/30 [00:00<?, ?it/s]
Fetching 30 files: 100%|██████████| 30/30 [00:00<00:00, 188649.36it/s]
[embed] BGE-M3 loaded.
You're using a XLMRobertaTokenizerFast tokenizer. Please note that with a fast tokenizer, using the `__call__` method is faster than using a method to encode the text followed by a call to the `pad` method to get a padded encoding.
  Words: 88 | VESUM: 82 (93.2%) | RAG: 3 | Not found: 3
  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/genitive-prepositions-rag-audit.md
⚠️  RAG verification found unverified words (see audit report)

VESUM: 82/88 (93%) verified
⚠️ VESUM not found (6): зв, льв, Львові, св, Хрещатик, Шевченка
        ```

        ## Current Content of Affected Section(s)

          focus: Select appropriate preposition for given location
  items: 10
- type: match-up
  focus: Match place to correct preposition phrase
  items: 10
- type: true-false
  focus: Evaluate location statements for correctness
  items: 8
connects_to:
- a1-33 (Adjective Case Forms)
prerequisites:
- a1-31 (The Genitive I: Absence)
persona:
  voice: Patient Supportive Tutor
  role: City Cartographer
grammar:
- Locative prepositions (в/у, на)
- Euphonic в/у alternation
- Біля/навпроти + Genitive
register: розмовний
duration: "45 min"
transliteration: no
tags:
- grammar
- cases
- locative
- genitive
- prepositions
naturalness:
  status: PASS
  score: 10/10
  notes: Good text.
---

## В/У + Місцевий (In + Locative)

Welcome back! So far, you have learned how to talk about the absence of things using the Genitive case. Now it is time to step out into the world and learn how to navigate a Ukrainian city. When you want to talk about where something is located, you will often use prepositions. The most common preposition for being inside an enclosed space is **в** or **у** (meaning "in" or "at"), followed by a noun in the Locative case.

You already know that the Locative case is used to show location. For most nouns, you simply change the final vowel to **-і**. Let's look at some high-frequency collocations for buildings, cities, and countries where we use the "in" meaning. Notice how the endings change to show that we are talking about a location.

*   **магазин** (store) → **в магазині** (in the store)
*   **школа** (school) → **у школі** (in the school)
*   **місто** (city) → **у місті** (in the city)
*   **Україна** (Ukraine) → **в Україні** (in Ukraine)

You might be wondering: why do we sometimes use **в** and sometimes **у**? This brings us to a beautiful feature of the Ukrainian language known as *милозвучність* (euphony, or musicality). Ukrainian speakers naturally alternate between **в** and **у** to avoid clunky consonant clusters and to make the language flow smoothly like a song. 

Here are the basic euphony rules you need to know:
1.  **Use «у» between two consonants.** If the previous word ends in a consonant, and the next word starts with a consonant, use **у** to create a bridge.
2.  **Use «у» before clusters starting with в, ф, льв, зв, св.** Even if the previous word ends in a vowel, these heavy clusters demand the softer **у**. A very common learner error is saying «в Львові» — this is incredibly hard to pronounce! You must always say **у Львові** (in Lviv).
3.  **Use «в» between vowels.** If the previous word ends in a vowel and the next word starts with a vowel, use **в**.
4.  **Use «в» at the beginning of a sentence before a vowel.**

> [!tip] 
> Remember that **в** and **у** mean the exact same thing! The choice between them is only about making the sentence easier to pronounce.

Let's look at these euphony rules in action with some practical examples. Pay close attention to the letters immediately before and after the preposition.

*   Він був **у** школі. (He was in the school. — *consonant before, consonant after*)
*   Вона **в** автобусі. (She is in the bus. — *vowel before, vowel after*)
*   Вона **у** Львові. (She is in Lviv. — *before the льв- cluster*)

Finally, as a quick review, remember that some consonants undergo a special alternation when they take the Locative **-і** ending. This is a very old linguistic rule that makes the words easier to say. If a word ends in **г**, **к**, or **х**, these consonants will change to **з**, **ц**, or **с** right before the **-і** ending. 

Here are the consonant alternations you need to practice. Read them aloud and notice how the sound changes in the back of your mouth.

| Nominative (Base) | Locative (Location) | Rule |
| :--- | :--- | :--- |
| **нога** (leg) | **на нозі** (on the leg) | **г** → **з** |
| **рука** (hand) | **у руці** (in the hand) | **к** → **ц** |
| **вухо** (ear) | **у вусі** (in the ear) | **х** → **с** |

Always keep an ear out for these euphony rules and alternations. They are not just grammar chores; they are the secret to sounding truly authentic and natural when speaking Ukrainian.

## На + Місцевий (On + Locative)

While **в/у** means "in" or "inside", the preposition **на** translates to "on". We use **на** followed by the Locative case when we want to talk about location on a surface, physical contact, or open spaces. 

Think of physical objects resting on top of other objects. Just like in English, you wouldn't say your cup is "in" the table; you say it is "on" the table. 

*   **стіл** (table) → **на столі** (on the table)
*   **стіна** (wall) → **на стіні** (on the wall)
*   **підлога** (floor) → **на підлозі** (on the floor — *notice the г → з alternation!*)
*   **вулиця** (street) → **на вулиці** (on the street / outside)

However, Ukrainian uses **на** for more than just physical surfaces. There is a very important social and activity exception where **на** replaces **в/у**. We use **на** for events, processes, and certain institutions. When you go to a concert, you are participating in an event, not just entering a box. Therefore, you are "on" the concert.

Here are the most common examples of this social/activity exception. You should memorize these as fixed phrases.

*   **на концерті** (at the concert)
*   **на роботі** (at work)
*   **на пошті** (at the post office — *institutional usage*)
*   **на уроці** (at the lesson / in class)

A great way to understand this distinction is to look at contrast pairs. Sometimes, you can use both **в** and **на** with similar places, but the meaning or the tradition changes completely. 

For example, when you are talking about rooms in a house, you generally use **в** (inside the room). But there is a massive traditional exception: the kitchen! Historically, cooking areas were open hearths or separate utility spaces, not enclosed rooms in the same way a bedroom is. Because of this linguistic remnant, Ukrainians always say **на кухні** (on the kitchen).

Let's compare these contrast pairs to see the difference clearly:

*   **в кімнаті** (inside a room) vs **на кухні** (in the kitchen)
*   **в театрі** (inside the theatre building) vs **на виставі** (at the theatre performance)
*   **в університеті** (inside the university) vs **на лекції** (at the lecture)

As an English speaker, you might be tempted to default to **в** for everything because "in" feels so universal. Be careful! Saying *в пошті* instead of **на пошті** is a very common beginner mistake. Always ask yourself: is this a physical box I am standing inside, or is this an event, an institution, or a surface?

## Біля/Поруч/Між (Near/Next to/Between)

Now that we know how to say we are "in" or "on" something, how do we describe where buildings are relative to each other? For this, we need prepositions of proximity and orientation.

The most important preposition for giving directions is **біля** (near, close to). Unlike **в** and **на** which take the Locative case, the preposition **біля** takes the Genitive case. This is a very high-frequency pattern, so you will use it constantly when navigating a city.

To form the Genitive case for most masculine and neuter nouns, you add **-а** or **-я**. For feminine nouns, you change the ending to **-и** or **-і**. Let's look at how we use **біля** to describe where things are.

*   **біля школи** (near the school)
*   **біля парку** (near the park)
*   **біля магазину** (near the store)
*   **біля зупинки** (near the bus stop)

When you want to say that something is directly across the street or facing another building, you use the orientation preposition **навпроти** (opposite). Just like **біля**, the preposition **навпроти** also requires the Genitive case. This is incredibly useful for city orientation tasks.

*   **навпроти банку** (opposite the bank)
*   **навпроти аптеки** (opposite the pharmacy)
*   **навпроти пошти** (opposite the post office)

While **біля** and **навпроти** use the Genitive case, there are other useful location prepositions that use a completely different case called the Instrumental. We will learn the full rules for the Instrumental case later, but for now, you can learn these two expressions as formulaic chunks or fixed phrases. 

These preview chunks are fantastic for expanding your descriptive abilities right now.

*   **поруч з** + Instrumental (next to / right alongside)
*   **між** + Instrumental (between)

You will hear these words often when native speakers give detailed directions. If you want to say that something is very distant, you can use the distance expression **далеко від** (far from), which again uses the Genitive case. If it is very close, you can say **близько від** (close to). 

By mastering just **біля** and **навпроти**, you can already guide someone through a basic city block!

## Де знаходиться...? (Where is...?)

To give directions, you first have to know how to ask for them! Up until now, you might have used the simple word **де** (where) to ask about locations, for example: «Де мама?» (Where is mom?). 

However, when we are talking about buildings, landmarks, or formal locations on a map, it is much more natural and polite to use the formal location verb **знаходиться** (is located). This is a formal alternative to simply using the verb "to be". It makes your Ukrainian sound polished and respectful, especially when talking to strangers on the street.

Let's look at how to ask these location questions properly:

*   **Де знаходиться пошта?** (Where is the post office located?)
*   **Де знаходиться найближча аптека?** (Where is the nearest pharmacy located?)
*   **Вибачте, де знаходиться магазин?** (Excuse me, where is the store located?)

When answering these questions with full sentences, you will combine the verb **знаходиться** with the prepositions and case forms you have just learned. You can use **на вулиці** to give the street name, or **біля** to give a nearby landmark.

Here are some complete, realistic answers you might hear or give:

*   **Пошта знаходиться на вулиці Хрещатик.** (The post office is located on Khreshchatyk street.)
*   **Аптека знаходиться біля метро.** (The pharmacy is located near the subway.)
*   **Школа знаходиться навпроти парку.** (The school is located opposite the park.)

To make your learning more authentic, let's use some real cultural context. When giving directions in Kyiv, the capital of Ukraine, locals frequently use major landmarks as reference points:

*   **Хрещатик** (Khreshchatyk — the main street)
*   **Майдан** (Maidan — Independence Square)
*   **Золоті Ворота** (Golden Gate — historical monument)

If you visit Kyiv, you will constantly hear directions anchored to these specific spots:

*   Кафе знаходиться **на вулиці Хрещатик**.
*   Магазин знаходиться **біля Майдану**.
*   Театр знаходиться **поруч з** метро Золоті Ворота.

Using the verb **знаходиться** along with your new prepositions will make you sound like a confident, capable traveler!

## Практика (Practice)

Let's put everything you have learned together! When you describe where objects are in a room, or where buildings are in a city, you will often need to use multiple prepositions in connected speech. This location description drill will train your brain to switch between cases smoothly.

Read this short description of a neighborhood and notice the bolded prepositions and case endings:

> Моя хата знаходиться **на вулиці** Франка. Вона **біля парку**. **Навпроти хати** є великий магазин. **В магазині** є молоко, хліб і м'ясо. Аптека знаходиться **далеко від** школи, але **близько від** пошти. Я зараз **на кухні**, а мій кіт спить **на підлозі**.

Now, let's look at a realistic dialogue. Imagine a tourist asking for directions in the city center. Notice how they use the formal verb to ask, and how the local uses landmarks and prepositions to answer.

> — Вибачте, **де знаходиться** пошта?
> — Пошта знаходиться **на вулиці** Шевченка.
> — Це **далеко**?
> — Ні, це **близько**. Вона **біля банку**, **навпроти кафе**.
> — Дуже дякую!
> — Будь ласка.

Read this dialogue aloud a few times. Try replacing the words for "post office" and "bank" with other vocabulary words like **школа** and **аптека**. Practicing these formulaic chunks will help you build muscle memory for navigating any Ukrainian street.

# Підсумок
You have done an amazing job today! You have unlocked the ability to navigate a city and describe locations using prepositions. You learned that **в/у** means "in" and requires the euphony rule to sound musical. You learned that **на** means "on" but is also used for events and institutions like **на пошті** and **на уроці**. Finally, you mastered the Genitive prepositions **біля** (near) and **навпроти** (opposite), and how to ask for directions using **Де знаходиться...?**.

Take a moment to review your knowledge with these self-check questions:

1.  Why do we say **у Львові** instead of **в Львові**? What rule are we following?
2.  How do you say "in the kitchen" in Ukrainian, and why is it an exception?
3.  If a store is near a school, what preposition and case do you use to describe its location?
4.  Translate this sentence into Ukrainian: "Where is the pharmacy located? It is opposite the post office."

Keep practicing, and soon you will be giving directions like a local!

        ## File Path

        `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/genitive-prepositions.md`

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
