<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 32: Подорож Україною (B1, B1.3 [Motion Verb Universe])

## Plan vocabulary to verify

- подорож (journey/trip)
- мандрівка (travel/journey — slightly more literary)
- подорожувати (to travel)
- мандрувати (to travel/wander)
- квиток (ticket)
- зворотний квиток (return ticket)
- розклад руху (schedule/timetable)
- вокзал (station)
- платформа (platform)
- перон (platform — for trains)
- зупинка (stop — bus/tram)
- маршрут (route)
- пересадка (transfer/connection)
- дістатися (to get to / to reach)
- маршрутка (minibus — common Ukrainian transport)
- купе (compartment — on a train)
- плацкарт (open sleeping car)
- провідник (conductor — on a train)
- пасажир (passenger)
- рейс (route/flight/service)
- затримка (delay)
- пам'ятка (landmark/monument)
- екскурсія (excursion/guided tour)
- готель (hotel)
- хостел (hostel)

## Sections to research

- **Подорож починається: планування та транспорт**: Bridge from M27-M35: this module is the communicative capstone of the Motion Verb Universe. Learners apply ALL motion verb knowledge — base pairs, 10 prefixes, figurative uses — to real travel scenarios in Ukraine.; Transport vocabulary: потяг/поїзд (train), автобус (bus), маршрутка (minibus), літак (plane), пором (ferry), таксі (taxi), метро (metro), тролейбус, трамвай. Купе, плацкарт, сидячий вагон. Квиток, зворотний квиток (return ticket), разовий квиток. Розклад руху (schedule), платформа/перон, зал очікування.; Instrumental case with geography — the Ukrainian way: подорож Україною (traveling through Ukraine — Ор.в.), їхати Закарпаттям (traveling through Zakarpattia), мандрувати Карпатами (hiking the Carpathians). This is a distinctive Ukrainian construction: the instrumental expresses the route/area of travel. From Кравцова Grade 3 p.83: dialogue at the bus station about buying tickets — natural model for travel communication.
- **На вокзалі та в аеропорту**: Train station dialogue: Buying a ticket: 'Скільки коштує квиток до Львова?' 'Один квиток у купейний вагон, будь ласка.' 'О котрій відходить поїзд?' 'Поїзд відходить о двадцять першій.' 'З якої платформи?' 'З третьої платформи.' Learners practice with 8-10 exchanges.; Airport dialogue: 'Де реєстрація на рейс до Відня?' 'Ваші речі для здачі в багаж?' 'О котрій посадка?' 'Посадка починається о чотирнадцятій тридцять.' 'Рейс затримується на годину.' Motion verbs in context: виліт (departure), приліт (arrival), вилетіти, прилетіти, пересісти (transfer).; Decolonization note: use відходити/відправлятися for trains carefully — native Ukrainian prefers відходити or виїжджати. Автобус виїжджає (NOT *відправляється).
- **Маршрут: від Києва до Карпат**: Model travel narrative (250-300 words): a journey from Kyiv to the Carpathians by train and bus, using all prefix groups: Виїхали з Києва ввечері (ви-). Поїзд відійшов від перону (від-). Проїхали Вінницю, Хмельницький (про-). Переїхали через міст (пере-). Приїхали до Iвано-Франківська вранці (при-). Пересіли на автобус. Доїхали до Яремче (до-). Зайшли до готелю (за-). Вийшли на прогулянку (ви-). Обійшли центр містечка (об-). Підійшли до водоспаду Пробій (під-).; Ukrainian landmarks as travel destinations: Київ (Хрещатик, Софійський собор, Лавра). Львів (площа Ринок, Високий Замок, кав'ярні). Одеса (Потьомкінські сходи, Дерибасівська, море). Карпати (Говерла, Яремче, Буковель). Чернігів, Кам'янець-Подільський, Ужгород.; Learners see how motion verbs + spatial prepositions + landmarks create vivid Ukrainian travel narratives. 8-10 sentences modeling different routes.
- **Орієнтування в місті: як дістатися?**: Asking for directions: 'Як дістатися до центру?' 'Як доїхати до вокзалу?' 'Де найближча зупинка метро?' 'Скільки їхати до аеропорту?' Giving directions: 'Пройдіть прямо, поверніть ліворуч, перейдіть дорогу, i побачите музей навпроти.'; Navigation vocabulary: прямо (straight), ліворуч (left), праворуч (right), на розі (at the corner), на перехресті (at the intersection), повернути (to turn), зупинка (stop), станція (station), квартал (block), провулок (lane/alley).; Practice: learners give directions from one landmark to another using motion verbs and spatial prepositions from M27. 6-8 direction-giving exchanges.
- **Подорожні історії: розповідь про поїздку**: Connected discourse model: a complete travel story (200-250 words) using past tense, motion verbs with prefixes, spatial prepositions, and transport vocabulary. Multiple paragraphs showing text coherence.; Story structure: Paragraph 1: Planning (куди, як, коли). Paragraph 2: Journey (виїхали, проїхали, доїхали). Paragraph 3: Destination (прийшли, обійшли, зайшли). Paragraph 4: Return (поїхали назад, повернулися). Learners see how motion verbs create narrative structure.; Production task: learners write their own travel story about a real or imagined trip in Ukraine, using at least 10 different motion verbs with prefixes, 5 spatial prepositions, and 5 transport terms.

## Instructions

Complete ALL of the following verification tasks. Each task MUST include at least one tool call.

### Task 1: Verify ALL vocabulary words exist in VESUM

Call `verify_words` with EVERY word from the plan vocabulary above. Batch them (10-15 per call).

Report:
- ✅ Words confirmed in VESUM
- ❌ Words NOT in VESUM (these must not be used in the module)

### Task 2: Search textbooks for each section topic

For each section title above, call `search_text` with the Ukrainian keywords.

Report the most relevant textbook excerpt for each section (author, grade, key quote).

### Task 3: Verify grammar rules

For any grammar rules mentioned in the plan, call `query_pravopys` to confirm the official 2019 rule.

Report the Правопис section number and key rule text.

### Task 4: Check for calques

Call `search_style_guide` for any phrases in the plan that might be calques. Check at least 3 phrases.

Report any calques found with the correct Ukrainian alternative.

### Task 5: Verify CEFR appropriateness

Call `query_cefr_level` on 5-10 key vocabulary words to confirm they match the target level (B1).

Report any words above the target level.

## Output format

Output your findings in this exact format:

<verification>
## VESUM Verification
- Confirmed: [list of verified words]
- Not found: [list of words to avoid]

## Textbook Excerpts
### Section: [title]
> [relevant textbook quote]
> Source: [author, grade]

### Section: [title]
> [relevant textbook quote]
> Source: [author, grade]

## Grammar Rules
- [rule]: Правопис §[number] — [key text]

## Calque Warnings
- [phrase]: [calque or OK] — [correct form if calque]

## CEFR Check
- [word]: [level] — [OK or above target]
</verification>
