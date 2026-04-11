<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 61: Порядкові числівники і відмінки (B1, B1.5 [Case Nuances & Prepositions])

## Plan vocabulary to verify

- порядковий числівник (ordinal numeral — перший, другий, третій)
- дата (date — uses ordinal in Р.в.)
- котра година (what time is it)
- поверх (floor/storey)
- століття (century)
- половина (half — о пів на п'яту)
- хвилина (minute)
- рік (year — року in Р.в.)
- складений числівник (compound numeral — двадцять п'ятий)
- вдруге (for the second time — adverb)
- утретє (for the third time — adverb)
- в першу чергу (first of all)
- двадцять перше століття (twenty-first century)

## Sections to research

- **Відмінювання порядкових числівників**: From Литвінова Grade 6 p.237: Ordinal numerals decline like adjectives. Твердий тип: перший, другий, четвертий, п'ятий, шостий... М'який тип: третій, третя, третє, треті. Full paradigm for перший (m/f/n/pl) and третій (m/f/n/pl).; Agreement: ordinal + noun must agree in gender, number, case. перший урок (m. Н.в.), першу книжку (f. Зн.в.), першого вересня (n. Р.в.), перших учнів (pl. Р.в.). Practice: decline 'п'ятий клас' through all 7 cases.; Compound ordinals (Заболотний Grade 6 p.179): ONLY the last word declines: двадцять третій день → двадцять третього дня → двадцять третьому дню. Practice: decline 'сто п'ятнадцята сторінка' through all cases.
- **Дати**: Saying 'today is': Сьогодні + ordinal in Н.в. + month in Р.в.: Сьогодні п'яте березня. Сьогодні тридцять перше грудня. Note: the ordinal is NEUTER (число = neuter noun implied).; Saying 'on a date': ordinal in Р.в. + month in Р.в.: п'ятого березня, тридцять першого грудня. Він народився п'ятнадцятого вересня тисяча дев'ятсот дев'яностого року. Year: тисяча дев'ятсот дев'яностого року (only last word declines).; Writing dates with digits: 15 березня 2024 року. With ordinal ending: 15-го березня, 1-ша сторінка, 5-й клас. But dates in calendar format: 15.03.2024 (no ending). Hyphen rules: the ordinal suffix attaches with a hyphen after digits (5-й, 10-та, 3-тє), but NOT after Roman numerals: ХХІ століття (no hyphen).
- **Час**: From Авраменко Grade 11 p.42: Full hours: о першій годині, о другій, о третій, о п'ятій. Note: годині is in М.в. (о + М.в.). Half hours: о пів на п'яту (at half past four — lit. 'half toward fifth').; Minutes past: десять хвилин на п'яту (4:10 — 'ten minutes toward fifth'). Minutes to: за десять хвилин п'ята (4:50 — 'in ten minutes, the fifth'). NOT *без десяти п'ять (Russicism from без десяти пять). Correct: за десять хвилин п'ята or чотири п'ятдесят.; Formal vs colloquial time: Formal: п'ятнадцять хвилин на четверту (3:15). Colloquial: три п'ятнадцять. Both are correct; formal uses ordinals, colloquial uses cardinals. In writing, digital format (15:30) doesn't use ordinals.
- **Поверхи, номери, порядок**: Floors: на першому поверсі (М.в.), з другого поверху (Р.в.), на п'ятий поверх (Зн.в. — direction). Маршрути: автобус номер сьомий, тролейбус п'ятнадцятий. Addresses: будинок третій, квартира п'ята, кабінет двісті десятий.; Order: перший раз, вдруге (adverb — for the second time), утретє, вчетверте. В першу чергу (first of all). Centuries: у двадцять першому столітті (М.в.), двадцяте століття (Н.в.). По-перше, по-друге, по-третє (firstly, secondly — ordinal adverbs for listing).; Ordinals in document titles and official contexts: стаття перша, пункт третій, параграф п'ятий, розділ восьмий. From Авраменко Grade 7 p.63: numeral usage in formal/official register.
- **Порядкові числівники в контексті**: Reading passage: a schedule/invitation containing multiple dates, times, floor numbers, and ordinals. Learners extract information and answer questions requiring correct ordinal declension. 'Зустріч відбудеться п'ятнадцятого березня о третій годині на четвертому поверсі, у кімнаті двісті двадцять п'ятій.'; Dialogue: making an appointment — agreeing on date, time, location. 'Коли вам зручно? Може, двадцять першого? О котрій годині? О пів на другу? Добре, на якому поверсі ваш офіс?'; Self-check: dates of major Ukrainian historical events: 24 серпня 1991 (День Незалежності), 28 червня 1996 (Конституція). Write in full word form with correct cases.
- **Підсумок**: Key patterns: ordinals decline like adjectives; compound ordinals — only last word declines; dates in Р.в.; clock time uses ordinals in М.в.; NOT *без десяти → за десять хвилин.; Self-check: 1. Decline двадцять п'ятий through all cases. 2. Write today's date in full words (both 'today is' and 'on the date'). 3. Express times 3:15, 7:30, 11:45 in Ukrainian. 4. Say your address with floor and apartment number. 5. Name three centuries in М.в. (у ... столітті).; Preview: кількісні вирази — agreement between quantity words and nouns.

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

Call `query_cefr_level` on 5-10 key vocabulary words to confirm they match the target level (B1).

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
