<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 52: My Story (A1, A1.8 [Past, Future, Graduation])

## Plan vocabulary to verify

- народитися (to be born)
- жити (to live)
- вчитися (to study)
- переїхати (to move)
- зараз (now)
- раніше (before/earlier)
- далі (further/next)
- розповідати (to tell/narrate)
- подорожувати (to travel)
- закінчити (to finish/graduate)
- дитинство (childhood, n)
- університет (university, m)
- програміст (programmer, m)
- успіх (success, m)
- мрія (dream, f)
- батьки (parents, pl)

## Sections to research

- **Dialogues**: Dialogue 1 — Getting to know someone deeply: — Розкажи про себе! — Я народився в Канаді, у Торонто. — А зараз ти живеш тут? — Так, зараз я живу в Києві. — Чому ти переїхав? — Я хотів вивчати українську. Мої бабуся і дідусь з України. — А що ти будеш робити далі? — Я буду працювати тут і вчити мову. — Чудово! Успіхів тобі! All three tenses in one conversation.; Dialogue 2 — Anna's story: — Я народилася у Львові. Там я вчилася в школі. — Потім я переїхала в Київ і закінчила університет. — Зараз я працюю вчителькою і живу в центрі міста. — А що далі? — Я буду подорожувати! Я хочу побачити Японію. — І ти будеш вчити японську? — Може! Але спочатку — українська для тебе! Past → present → future flow.
- **Три часи разом (Three Tenses Together)**: Life story structure: PAST (минулий час): Я народився/народилася в... Я жив/жила в... Я вчився/вчилася... Я працював/працювала... PRESENT (теперішній час): Зараз я живу в... Я працюю... Я вивчаю... Я люблю... FUTURE (майбутній час): Я буду працювати... Я буду вивчати... Я буду жити...; Signal words that mark tense shifts: Past: раніше (before), у дитинстві (in childhood), коли я був/була маленьким/маленькою (when I was little). Present: зараз (now), сьогодні (today), цього року (this year). Future: потім (then), далі (further), наступного року (next year). These words help the listener know which tense is coming.
- **Моя історія (My Story)**: Model story — Taras's life: Я народився в Одесі у тисяча дев'ятсот дев'яносто п'ятому році. Я жив там з батьками і сестрою. Я ходив у школу і любив математику. Потім я переїхав у Київ і вчився в університеті. Зараз я живу в Києві. Я працюю програмістом. Я люблю свою роботу. У вільний час я граю у футбол і читаю книжки. Далі я буду подорожувати. Я буду вивчати англійську. І я буду жити в Києві — це моє місто! Past (народився, жив, ходив) → Present (живу, працюю) → Future (буду подорожувати).; Your turn — tell YOUR story: Start: Я народився/народилася в [city/country]. Past: Я жив/жила... Я вчився/вчилася... Я працював/працювала... Present: Зараз я живу... Я працюю... Я вивчаю українську, тому що... Future: Я буду... Я хочу... Use at least 3 past verbs, 3 present verbs, and 3 future constructions.
- **Summary**: Three tenses — one story: Past: -в/-ла/-ло/-ли (gender endings). Я народився. Я жила. Present: person endings. Я живу. Ти працюєш. Вона вивчає. Future: буду + infinitive. Я буду працювати. Вона буде жити. Signal words: раніше → past, зараз → present, далі → future. Life story vocabulary: народитися (to be born), жити (to live), вчитися (to study), переїхати (to move), подорожувати (to travel). Self-check: Write your life story in 8-10 sentences using all three tenses.

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
