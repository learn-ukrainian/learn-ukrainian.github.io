        # Escalation Fix — validate

        You are an expert Ukrainian language editor. The previous agent could not fix
        these audit violations. Fix them precisely.

        ## Audit Errors

        ```
          📊 Section Word Analysis:
     Вступ (Introduction)                                        296 /  250  ✅ (+46)
     Погода та безособові форми (Weather & Impersonal Forms)     414 /  300  ✅ (+114)
     Пори року та природа (Seasons & Nature)                     342 /  325  ✅ (+17)
     Складні речення та прогноз (Complex Sentences & Forecast)   418 /  325  ✅ (+93)
     ──────────────────────────────────────────────────────────────────────────────────
     TOTAL                                                      1470 / 1200  ✅ (+270)

📚 IMMERSION TOO LOW (13.0% vs 20-35% target)
   FIX: Convert simple explanations to Ukrainian
   FIX: Add more Ukrainian narratives/dialogues
   FIX: Use Ukrainian for engagement boxes (💡🎬🌍)

--- STRICT GATES (Level A1) ---
Persona      ✅ Persona Defined
Words        ✅ 1575/1200 (raw: 1606)
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
Immersion    ❌ 13.0% LOW (target 20-35% (M43))

📝 RECOMMENDATION: UPDATE (patch fixes) (severity 10/100)
   → Immersion 7% off target (minor)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/weather-and-nature-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/weather-and-nature.json

❌ AUDIT FAILED. Correct errors before proceeding.

❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/weather-and-nature-audit.log for details)

Running RAG word verification...
Verifying: weather-and-nature.md
  VESUM misses: 1 — querying RAG...
[embed] Loading BGE-M3 from BAAI/bge-m3...

Fetching 30 files:   0%|          | 0/30 [00:00<?, ?it/s]
Fetching 30 files: 100%|██████████| 30/30 [00:00<00:00, 52648.17it/s]
[embed] BGE-M3 loaded.
You're using a XLMRobertaTokenizerFast tokenizer. Please note that with a fast tokenizer, using the `__call__` method is faster than using a method to encode the text followed by a call to the `pad` method to get a padded encoding.
  Words: 82 | VESUM: 81 (98.8%) | RAG: 1 | Not found: 0
  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/weather-and-nature-rag-audit.md
✅ RAG verification: all words verified

Prose-relevant failures:
  lesson: 1575/1200 (raw: 1606) | immersion: 13.0% LOW (target 20-35% (M43))
VESUM: 91/92 (99%) verified
        ```

        ## Current Content of Affected Section(s)

        ## Вступ (Introduction)

Приві́т! Welcome to navigating the great outdoors and mastering one of the most essential, universal topics in the Ukrainian language: the weather (**пого́да**). 

Whether you are waiting for a morning bus in **Киї́в**, ordering a fresh coffee in **Львів**, or planning an ambitious hike up into the **го́ри** (mountains), knowing how to talk about the weather is your ultimate key to small talk. In Ukraine, the climate is not just a passive background detail; it is an active part of daily life and conversation. 

We experience four very distinct, beautiful seasons (**весна́**, **лі́то**, **о́сінь**, **зима́**). Each brings its own unique character, its own vocabulary, and its own challenges. Being able to discuss the changing conditions means you can easily connect with anyone, anywhere. It shows that you are paying attention to the world around you.

Before we dive into the grammar, let me share a special cultural hook with you. Have you ever heard of «Ба́бине лі́то»? In English, this is often called Indian Summer. It is a brief, unseasonably warm, and dry period that usually arrives on the border between September and October. Historically, this time was incredibly important for the agricultural cycle. It was the final window of opportunity for farmers to gather the last of the harvest, pick apples, and prepare their homes before the hard winter set in. In Ukrainian folklore, «Ба́бине лі́то» is associated with a magical calm, golden sunlight, and the delicate spiderwebs that float through the autumn air. It is a beautiful moment of pause in nature.

Mastering these concepts allows you to describe these seasonal changes, talk about the rain, the sun, and the wind, and build sentences that explain your plans. Let's explore the natural world!

## Погода та безособові форми (Weather & Impersonal Forms)

When you look out the window, how do you describe what you see? In English, we rely heavily on the dummy subject "it" to talk about the weather. We say, "It is cold," or "It is raining." However, Ukrainian grammar takes a much more direct and elegant approach. We use impersonal forms.

For the state of nature and temperature, we simply use adverbs. There is no need for a subject at all. The weather just *is*. Let’s look at the core adverbs you need to know:

- **Тепло́.** (It is warm.)
- **Хо́лодно.** (It is cold.)
- **Спекотно.** (It is hot.)
- **Прохоло́дно.** (It is cool.)

A very common mistake for English speakers is to translate literally and say «Це хо́лодно». You must avoid this! If you say «Це хо́лодно», a Ukrainian will assume you are touching a physical object, like a cold glass of water or a metal pole. When you are talking about the environment, the atmosphere, or the weather outside, you must drop the «це» entirely and simply say: **Хо́лодно.**

`Сього́дні ду́же хо́лодно.` (It is very cold today.)
`На ву́лиці тепло́.` (It is warm outside.)
`За́втра бу́де спекотно.` (Tomorrow it will be hot.)
`Восени́ прохоло́дно.` (In autumn it is cool.)

Now, let us talk about precipitation. How do we say that it is raining or snowing? Ukrainian uses a very poetic and idiomatic construction based on verbs of motion. The rain and the snow literally "walk" or "go".

- **Йде дощ.** (It is raining. Literally: Rain goes.)
- **Йде сніг.** (It is snowing. Literally: Snow goes.)

You must use the verb **іти́** (to go). A common error is to say «дощ ро́бить» (rain makes or rain does). Please remember that the verb **роби́ти** implies conscious work or creation, like building a house or making dinner. The rain does not work a shift at a factory; it moves, it falls, it "goes". Let’s practice this:

`Йде си́льний дощ.` (Heavy rain is falling.)
`Взи́мку йде сніг.` (It snows in winter.)
`Світи́ть яскра́ве со́нце.` (The bright sun is shining.)
`Сього́дні си́льний ві́тер.` (There is a strong wind today.)

Also, if the sun is out, we simply say **Світи́ть со́нце**. This makes your language sound incredibly natural and observant. 

*To hear these phrases and adverbs in action, check out this video lesson:*
🎥 [ULP 1-16 | Talking about weather in Ukrainian](https://www.youtube.com/watch?v=ycCrSrHCezQ)

## Пори року та природа (Seasons & Nature)

Now that we know how to describe the weather, we need to know *when* and *where* it is happening. Ukraine is famous for its rich natural landscapes and its distinct four seasons. 

The foundation of discussing nature is knowing the nouns for the seasons themselves:

- **зима́** (winter)
- **весна́** (spring)
- **лі́то** (summer)
- **о́сінь** (autumn)

When we want to say that something happens *in* or *during* a season, we do not simply use a preposition with these nouns. Instead, Ukrainian grammar provides specific temporal adverbs for this exact purpose. You must learn these by heart, paying very close attention to the phonetics and the stress marks.

- **взи́мку** (in winter)
- **навесні́** (in spring)
- **влі́тку** (in summer)
- **восени́** (in autumn)

Please be extremely careful: avoid literal translations like «у весні́» or «в весні́». This sounds unnatural to a native speaker. Always use the proper adverb **навесні́**, and notice how the stress falls heavily on the very last syllable. Similarly, with **восени́**, the stress is firmly on the first «о».

Next, let’s explore the natural world around us. The Ukrainian State Standard highlights several key geographical features that are essential for planning your outdoor adventures:

- **ліс** (forest)
- **о́зеро** (lake)
- **рі́чка** (river)
- **го́ри** (mountains)
- **мо́ре** (sea)

Let’s combine our new seasons, natural locations, and weather adverbs to describe typical conditions across the country:

`Влі́тку на мо́рі ду́же спекотно.` (In summer, it is very hot at the sea.)
`Взи́мку в го́рах бага́то сні́гу.` (In winter, there is a lot of snow in the mountains.)
`Навесні́ бі́ля річки́ та на о́зері тепло́.` (In spring, it is warm near the river and at the lake.)
`Восени́ у лі́сі прохоло́дно, там га́рна приро́да.` (In autumn, it is cool in the forest, the nature is beautiful there.)

Notice the prepositions we use: **на мо́рі**, **в го́рах**, and **у лі́сі**. By practicing these combinations, your Ukrainian will become rich, descriptive, and perfectly suited for any conversation about nature.

## Складні речення та прогноз (Complex Sentences & Forecast)

When you are trying to organize a weekend picnic, the weather directly dictates your schedule. To express this in Ukrainian, we need to build clear, consecutive sentences. Connecting simple ideas allows you to logically express your plans.

We will use simple, consecutive sentences to explain our plans depending on the weather conditions. The structure is straightforward: state the weather, and then state your action in a new sentence.

`Сього́дні хо́лодно. Ми не гуля́ємо.` (Today it is cold. We are not walking.)
`Йде си́льний дощ. Я не ї́ду в го́ри.` (Heavy rain is falling. I am not going to the mountains.)
`Сього́дні тепло́. Вони́ йдуть у ліс.` (It is warm today. They are going to the forest.)

Notice how simple, consecutive sentences create a seamless logical connection. This is a very powerful tool for everyday conversation and explaining your daily routine.

To know what plans to make, you must first check the weather forecast, or **прогно́з**. Let’s look at a realistic dialogue between two friends discussing their plans for the weekend. Notice how they ask questions and use common collocations like «га́рний прогно́з» (good forecast) or «пога́ний прогно́з» (bad forecast).

> — Приві́т! Яка сього́дні пого́да?
> — (Hi! What is the weather like today?)
> — Сього́дні пога́на пого́да. Вели́ка хма́ра і си́льний ві́тер.
> — (Today is bad weather. A big cloud and a strong wind.)
> — А що там за прогно́зом на за́втра? Чи бу́де дощ?
> — (And what is in the forecast for tomorrow? Will there be rain?)
> — Ні, за́втра бу́де со́нце і ду́же тепло́.
> — (No, tomorrow there will be sun and it will be very warm.)
> — Чудо́во! Бу́де га́рний прогно́з. Тоді́ ми ї́демо на о́зеро!
> — (Wonderful! There will be a good forecast. Then we are going to the lake!)

In this dialogue, the phrase **що там за прогно́зом?** (what is in the forecast?) is an incredibly authentic way to ask about future conditions. We also see the word **хма́ра** (cloud) and **ві́тер** (wind) being used to describe the current state. Master these questions, and you will never be caught in the rain without an umbrella!

*For more listening practice on forecasts, try this short lesson:*
🎥 [FMU 1-28 | How to talk about the weather in Ukrainian](https://www.youtube.com/watch?v=6MRrGpcGEp4)

> [!tip]
> Always remember to drop the dummy subject "it" when talking about weather in Ukrainian!

# Підсумок
Excellent work! You have successfully mastered one of the most common and vital topics in the Ukrainian language. You are now fully prepared to discuss the weather, the changing seasons, and the beautiful nature of Ukraine. 

You know how to avoid the trap of saying «це хо́лодно» and instead use the elegant impersonal adverbs like **хо́лодно**, **тепло́**, **спекотно**, and **прохоло́дно**. You also understand the logic that rain and snow "walk" (**йде дощ**, **йде сніг**), and you can use the temporal adverbs for seasons (**взи́мку**, **навесні́**, **влі́тку**, **восени́**) with perfect rhythm and stress. 

Take a moment to review what you have learned and test your knowledge before moving on to the activities. Ask yourself the following self-check questions:
- How do you say "It is cold outside" without using the dummy subject "it"?
- Why is it incorrect to say «дощ ро́бить», and what is the correct verb to use for precipitation?
- What is the difference between **весна́** and **навесні́**?
- How do you connect ideas about weather and plans using simple sentences?



        ## File Path

        `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/weather-and-nature.md`

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
