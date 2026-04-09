<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 54: Emergencies (A1, A1.8 [Past, Future, Graduation])

## Plan vocabulary to verify

- допомога (help, f)
- допоможіть (help! — imperative)
- швидка (ambulance, f — short for швидка допомога)
- поліція (police, f)
- лікарня (hospital, f)
- аварія (accident, f)
- загубити (to lose)
- викликати (to call/summon)
- пожежа (fire, f)
- порятунок (rescue, m)
- паспорт (passport, m)
- адреса (address, f)
- номер (number, m)
- алергія (allergy, f)
- форма (form/document, f)
- будинок (building, m)

## Sections to research

- **Dialogues**: Dialogue 1 — Calling 112: — Служба порятунку, слухаю вас. — Допоможіть! Тут аварія! Людина не рухається! — Де ви? — На вулиці Хрещатик, біля метро Майдан Незалежності. — Зрозуміло. Швидка вже їде. Як вас звати? — Мене звати Адам. Мій номер — нуль дев'яносто три... — Дякую. Залишайтеся на місці. Emergency call: location + problem + personal info.; Dialogue 2 — Lost documents: — Вибачте, де тут поліція? — Поліція? Прямо і наліво. — Дякую! (at the station) Добрий день. Я загубив паспорт. — Де ви його загубили? — Я не знаю. Може, в метро. — Як ваше прізвище? — Сміт. Адам Сміт. — Ваш номер телефону? — Нуль дев'яносто три, п'ятсот двадцять один... — Добре. Заповніть цю форму, будь ласка. Police station: reporting a lost document.
- **Екстрені ситуації (Emergencies)**: Emergency number: 112 (один один два) — works everywhere in Ukraine. Key phrases (learn as chunks!): Допоможіть! (Help! — formal/plural imperative) Викличте швидку! (Call an ambulance!) Викличте поліцію! (Call the police!) Тут аварія! (There's an accident here!) Тут пожежа! (There's a fire here!) Людині погано! (Someone is feeling bad!) Мені потрібна допомога! (I need help!); Giving your location: Де ви? — Where are you? Я на вулиці... (I'm on ... street.) Я біля... (I'm near...) Я в метро... (I'm in the metro...) Адреса: вулиця Хрещатик, будинок десять. (Address: Khreshchatyk street, building 10.) Use places vocabulary from A1.5 (біля, навпроти, поруч).
- **Допомога (Getting Help)**: At the hospital / лікарня: Мені потрібен лікар. (I need a doctor.) У мене болить... (My ... hurts — from M53.) У мене алергія на... (I'm allergic to...) Я не розумію. Повторіть, будь ласка. (I don't understand. Please repeat.) Ви говорите англійською? (Do you speak English?); Personal information for emergencies: Мене звати... (My name is...) Моє прізвище... (My surname is...) Мій номер телефону... (My phone number is...) Я з [country]. (I'm from [country].) Мій паспорт... / Я загубив/загубила паспорт. (My passport... / I lost my passport.) Мій готель — ... (My hotel is...) All review from previous modules — applied to a critical situation.
- **Summary**: Emergency survival kit: 112 — universal emergency number. Допоможіть! (Help!) Викличте швидку / поліцію! Тут аварія / пожежа! Location: Я на вулиці... Я біля... At hospital: У мене болить... Мені потрібен лікар. At police: Я загубив/загубила [document]. Personal info: ім'я, прізвище, номер телефону, країна, адреса. Self-check: Practice a 112 call — state the problem, give your location, give your name.

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

Call `query_cefr_level` on 5-10 key vocabulary words to confirm they match the target level (A1).

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
