<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 59: Місця і розташування (B1, B1.5 [Case Nuances & Prepositions])

## Plan vocabulary to verify

- місцевість (locality/area — a geographic area)
- околиця (outskirts — the edge of a settlement)
- передмістя (suburb — area around a city, невідм. pl)
- площа (square — public urban space)
- набережна (embankment/waterfront — street along a river)
- узбережжя (coast/shoreline — land along the sea)
- заповідник (nature reserve — protected natural area)
- краєвид (landscape/view — scenery)
- пам'ятка (landmark/monument — notable place or structure)
- рівнина (plain — flat terrain)
- височина (highland/upland — elevated terrain)
- острів (island — land surrounded by water)
- провулок (lane/alley — small street)
- розташування (location — where something is situated)
- орієнтир (landmark/reference point — for navigation)
- низовина (lowland — low-lying terrain)
- півострів (peninsula — land surrounded by water on three sides)
- гірський (mountainous — adjective from гора)
- долина (valley — low area between mountains)
- містечко (small town — diminutive of місто)
- район (district — administrative area)
- берег (bank/shore — edge of water)

## Sections to research

- **Географічна лексика: рельєф і ландшафт**: Landforms and terrain — systematic vocabulary (grounded in Заболотний Grade 5 p.69 thematic grouping): рівнина (plain), височина (highland/upland), низовина (lowland), гора (mountain, pl гори), пагорб (hill), долина (valley), яр (ravine), степ (steppe). Ukraine-specific: Карпати (Carpathians), Кримські гори (Crimean mountains), Подільська височина (Podolian Upland).; Water features: річка (river), озеро (lake), море (sea), узбережжя (coast/shore), набережна (embankment/waterfront), острів (island), півострів (peninsula). Ukrainian rivers: Дніпро, Дністер, Південний Буг, Десна. Lakes: Світязь, Синевир.; Settlements and urban features: місто (city), село (village), містечко (small town), передмістя (suburb, невідм. pl), околиця (outskirts), район (district), площа (square), вулиця (street), провулок (lane/alley), набережна (embankment street — also a noun).
- **Місцевий відмінок: де?**: Locative case for location (Заболотний Grade 6 p.55 — місцевий відмінок): The locative answers де? (where?) and is ALWAYS used with a preposition. Two main prepositions: у/в (in/at) and на (on/at). Rule for cities: у Києві, у Львові, в Одесі, у Харкові, в Ужгороді. But: на Хрещатику (streets with specific names take на).; У vs на for geographic locations — rules and patterns: у + enclosed spaces: у місті, у селі, у парку, у заповіднику, у долині. на + open spaces, surfaces, events: на площі, на вулиці, на узбережжі, на острові, на горі, на рівнині. Special: на Україні is INCORRECT — в Україні (the old form на Україні was a Russianized colonial usage; modern standard: в Україні).; Locative endings review in geographic context: Masculine: -і/-ї (у Києві, у заповіднику, на острові). Exception: -у in a few words (на лугу). Feminine: -і (у долині, на площі, в Одесі, на вулиці). Neuter: -і (у місті, у селі, на морі, на узбережжі). Plural: -ах/-ях (у Карпатах, у горах, на вулицях).
- **Родовий відмінок: звідки? і куди?**: Genitive for origin — з/із + родовий відмінок (Заболотний Grade 6 p.47): з Києва (from Kyiv), з Львова (from Lviv), з Одеси (from Odesa), з Харкова (from Kharkiv), із Закарпаття (from Transcarpathia), з України (from Ukraine). Question word: звідки? (from where?).; Genitive in geographic descriptions — possession and relation: центр міста (centre of the city, gen), узбережжя моря (coast of the sea, gen), долина Дністра (valley of the Dniester, gen), вершина гори (peak of the mountain, gen), набережна Дніпра (embankment of the Dnipro, gen).; Direction — до + genitive vs у/на + accusative: до Києва / у Київ (to Kyiv — до emphasizes direction, у/на emphasizes destination). до моря / на море (to the sea). до лісу / у ліс (to/into the forest). Both are correct; register and emphasis differ. Practice: Ми їдемо до Львова. = Ми їдемо у Львів.
- **Підсумок: описуємо місця**: Model city description — structured text about a Ukrainian city (following composition model from Заболотний Grade 7 p.248): Зачин (where is it, brief introduction). Основна частина: geography (на березі чого?), landmarks (що варто побачити?), atmosphere (яке місто?). Кінцівка (why visit?). Example: Чернівці — місто на Буковині, у передгір'ї Карпат...; Case summary table for geographic nouns: Київ — у Києві (loc), з Києва (gen), до Києва (gen), у Київ (acc). Одеса — в Одесі (loc), з Одеси (gen), до Одеси (gen), в Одесу (acc). Карпати — у Карпатах (loc pl), з Карпат (gen pl), до Карпат (gen pl). Закарпаття — на Закарпатті (loc), із Закарпаття (gen).; Vocabulary summary by category: рельєф (рівнина, височина, низовина, гора, долина), водойми (річка, озеро, море, узбережжя), поселення (місто, село, передмістя, околиця), міські об'єкти (площа, вулиця, провулок, набережна), природа (заповідник, ліс, парк, краєвид, пам'ятка).

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
