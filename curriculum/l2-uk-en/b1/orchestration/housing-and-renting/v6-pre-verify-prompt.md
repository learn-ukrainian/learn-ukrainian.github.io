<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 29: Житло і оренда (B1, B1.2 [Verb System])

## Plan vocabulary to verify

- квартира (apartment)
- оренда (rent/rental)
- орендар (tenant)
- орендодавець (landlord)
- договір оренди (lease agreement)
- завдаток (deposit)
- комунальні послуги (utilities)
- опалення (heating)
- вмебльована (furnished)
- поверх (floor/storey)
- площа (area/square footage)
- ремонт (renovation/repair)
- гуртожиток (dormitory)
- водопостачання (water supply)
- електрика (electricity)
- цвіль (mould)
- ліфт (elevator)
- протікати (to leak)
- полагодити (to fix/repair)
- під ключ (turnkey — ready to move in)
- окремо (separately — for utilities)

## Sections to research

- **Опис житла**: Types of housing: квартира, будинок, приватний будинок, гуртожиток, однокімнатна/двокімнатна/трикімнатна квартира. Rooms: вітальня, спальня, кухня, ванна кімната, туалет, коридор, балкон, комора, підвал, горище.; Describing features using case constructions: Р.в.: квартира площею сорок квадратних метрів. Ор.в.: кімната з великим вікном, квартира з меблями (вмебльована). М.в.: на першому/другому/п'ятому поверсі, у новому будинку. Зн.в.: вікна виходять на подвір'я/на вулицю.; Furniture and appliances: меблі (pl.), шафа, ліжко, стіл, крісло, диван, плита, холодильник, пральна машина, посудомийка. Practice: describe your ideal apartment using 10+ case constructions.
- **Оголошення про оренду**: Reading real-format Ukrainian rental ads: 'Здається 2к квартира, 55 кв.м, 3/9 поверх, євроремонт, вмебльована, поруч метро. 12 000 грн/міс + комунальні.' Abbreviation key: к = кімнатна, кв.м = квадратних метрів, 3/9 = третій поверх із дев'яти, грн/міс = гривень на місяць.; Responding to ads: Добрий день, я телефоную щодо оголошення про оренду квартири. Чи вона ще вільна? Коли можна подивитися? Скільки коштує оренда? Чи входять комунальні у вартість?; Practice: read 3 rental ads, extract key information, write a response message for the one you prefer.
- **Переговори про оренду**: Key rental vocabulary: оренда (rent), орендар (tenant), орендодавець (landlord), договір оренди (lease agreement), завдаток (deposit), комунальні послуги (utilities), опалення (heating), водопостачання (water supply), електрика (electricity), інтернет, сміття (garbage).; Negotiation dialogue: 'Яка вартість оренди на місяць?' 'Дванадцять тисяч гривень. Комунальні окремо.' 'Який завдаток?' 'Одна місячна оплата.' 'На який термін?' 'Мінімум на рік. Можна продовжити.' Using temporal prepositions (на рік, на місяць) and quantity expressions.; Rights and rules: Хто оплачує ремонт? Чи можна з тваринами? Чи можна замінити меблі? Як повідомити про виїзд? Practice: role-play a lease negotiation using formal register.
- **Проблеми з житлом**: Common problems and complaints: Протікає кран/дах. Не працює опалення/гаряча вода. Зламалася пральна машина. Не працює ліфт. У кімнаті цвіль (mould). Сусіди шумлять. Using reflexive and passive constructions from earlier modules.; Requesting repairs: 'Добрий день, хочу повідомити, що в квартирі не працює опалення. Прошу надіслати майстра якнайшвидше. Дякую.' Using formal register with vocative (Шановний орендодавцю!) and purpose constructions (для ремонту, щоб полагодити).; Emergency contacts: In urgent cases: Аварійна служба (f, emergency service), сантехнік (m, plumber), електрик (m, electrician), служба газу (f, gas service). 'Терміново потрібен сантехнік — протікає труба у ванній.' Integration with dative (мені потрібен) and cause prepositions (через аварію).
- **Практика: пошук квартири**: Extended role play: the full process from ad to lease. 1. Read three ads, compare (using ступені порівняння from Phase 5). 2. Call the landlord (using vocative, formal register). 3. Visit and describe the apartment (using cases for features). 4. Negotiate terms (using quantity expressions and temporal preps). 5. Report a problem after moving in (using cause/purpose preps).; Integrated grammar checklist: did you use... Р.в. (площею, без меблів, близько ста метрів)? Д.в. (мені потрібна, орендарю)? Ор.в. (з балконом, за адресою)? Кл.в. (Шановний пане)? порівняння (ця квартира більша, але дорожча)? числівники (на третьому поверсі, двадцять п'ять тисяч)? займенники (якась квартира, нічого підходящого, кожен варіант)?
- **Підсумок**: Key housing vocabulary organized by category: types, rooms, furniture, rental terms, problems. Grammar integration: all Phase 6 cases and prepositions in action.; Cultural note: Ukrainian rental culture differs from Western norms. Оренда is often informal (без договору, through знайомі). Terms like євроремонт (European-style renovation), під ключ (turnkey), і меблі, і техніка (furnished + appliances) reflect local market language. Understanding these terms is essential for real-life housing searches on Ukrainian platforms like OLX.; Preview: контрольна робота 6 — comprehensive review of Phase 6.

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
