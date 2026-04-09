<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 69: Фінал A2 (A2, A2.10 [Refinement and Graduation])

## Plan vocabulary to verify

- прибуття (arrival)
- вокзал (train station)
- квиток (ticket)
- ринок (market)
- замовити (to order)
- порадити (to recommend)
- будівля (building)
- враження (impression)
- підсумок (summary)
- вітаємо (congratulations)
- маршрутка (minibus)
- прогулянка (walk, stroll)
- дізнатися (to find out, to learn)
- готовий (ready)

## Sections to research

- **Ранок: прибуття та орієнтація (Morning: Arrival and Orientation)**: Scenario: the learner arrives in Lviv by train. Tasks: buy a transit ticket, ask for directions to the hotel, check in at the hotel (give name, passport, ask about room).; Dialogues integrating: Locative (у Львові, на вокзалі), Accusative (купити квиток), Genitive (немає вільних кімнат), formal imperative (Покажіть, будь ласка, паспорт).; Cultural note: how to navigate a Ukrainian city — маршрутка, трамвай, таксі, пішки.
- **День: ринок, кав'ярня, прогулянка (Day: Market, Cafe, Walk)**: At the market: buy food, discuss quantities and prices (numeral agreement: два кілограми яблук, п'ять помідорів), compare products (Ці яблука солодші за ті).; At a cafe: order food and drinks, discuss preferences (Я волію каву з молоком. А що ви порадите?), deal with a small problem (Вибачте, я замовляв борщ, а не суп).; Walking around: describe what you see using all cases naturally, ask locals about sights (Що це за будівля? Коли її збудували?).
- **Вечір: друзі, розмови, плани (Evening: Friends, Conversations, Plans)**: Meeting Ukrainian friends: discuss your day using past tense and aspect (Сьогодні я побачив/побачила стільки цікавого!). Share opinions (На мою думку, Львів — найгарніше місто).; Extended conversation: discuss favorite places, compare Lviv with your home city, talk about Ukrainian traditions (Я дізнався/ дізналася про Івана Купала — це так цікаво!).; Making future plans: discuss what to do tomorrow using future tense and щоб/якщо (Якщо буде гарна погода, поїдемо у Карпати. Я хочу поїхати, щоб побачити гори).
- **Підсумок: від A2 до B1 (Summary: From A2 to B1)**: Reflection: what the learner can now do — a summary of all A2 competencies expressed as "Я можу..." statements. Connect to CEFR A2 can-do descriptors.; What changes in B1: more Ukrainian in explanations (metalanguage bridge is complete), longer texts, more nuanced grammar (participles, complex aspect, passive), richer vocabulary.; Encouragement and celebration: completing A2 is a major milestone. The learner can handle everyday situations in Ukraine. Вітаємо! Ви готові до рівня B1!

## Instructions

Complete ALL of the following verification tasks. Each task MUST include at least one tool call.

### Task 1: Verify ALL vocabulary words exist in VESUM

Call `verify_words` with EVERY word from the plan vocabulary above. Batch them (10-15 per call).

Report:
- ✅ Words confirmed in VESUM
- ❌ Words NOT in VESUM (these must not be used in the module)

### Task 2: Verify grammar rules

For any grammar rules mentioned in the plan, call `query_pravopys` to confirm the official 2019 rule.

Report the Правопис section number and key rule text.

### Task 3: Check for calques

Call `search_style_guide` for any phrases in the plan that might be calques. Check at least 3 phrases.

Report any calques found with the correct Ukrainian alternative.

### Task 4: Verify CEFR appropriateness

Call `query_cefr_level` on 5-10 key vocabulary words to confirm they match the target level (A2).

Report any words above the target level.

## Output format

Output your findings in this exact format:

<verification>
## VESUM Verification
- Confirmed: [list of verified words]
- Not found: [list of words to avoid]

## Grammar Rules
- [rule]: Правопис §[number] — [key text]

## Calque Warnings
- [phrase]: [calque or OK] — [correct form if calque]

## CEFR Check
- [word]: [level] — [OK or above target]
</verification>
