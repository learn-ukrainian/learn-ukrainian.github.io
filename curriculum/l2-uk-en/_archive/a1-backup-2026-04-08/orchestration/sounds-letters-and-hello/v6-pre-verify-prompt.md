<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 1: Sounds, Letters, and Hello (A1, A1.1 [Sounds, Letters, and First Contact])

## Plan vocabulary to verify

- звук (sound)
- літера (letter)
- голосний (vowel sound)
- приголосний (consonant sound)
- привіт (hi, informal)
- як справи (how are you)
- добре (fine, good)
- чудово (great, wonderful)
- мама (mother)
- молоко (milk)
- нормально (okay)
- тато (father)
- око (eye)
- дім (house)
- ніс (nose)
- сон (dream)

## Sections to research

- **Звуки і літери (Sounds and Letters)**: Golden rule from Заболотний Grade 5 p.83: 'Звуки ми чуємо й вимовляємо, а букви бачимо й пишемо.' We hear and pronounce sounds (звуки). We see and write letters (літери). These are NOT the same thing. A letter is a symbol on paper. A sound is what your mouth produces. This distinction is the foundation of Ukrainian phonetics — Ukrainian teachers drill it from Grade 1.; Ukrainian has 33 letters (літери) but 38 sounds (звуків). Why the mismatch? Some letters represent two sounds (Я, Ю, Є, Ї in certain positions). One letter (Ь) makes no sound at all — it only softens the consonant before it. Litvinova Grade 5 p.130 asks: 'Чи можна говорити «голосна літера»?' Answer: no! Sounds are голосні or приголосні, not letters. Letters only represent sounds.; The Ukrainian alphabet (абетка/алфавіт): all 33 letters in order. Each letter has a name. Unlike English, Ukrainian spelling is highly phonetic — what you see is (mostly) what you hear. No silent letters, no surprise pronunciations. Once you know the sounds, you can read any word.
- **Голосні звуки (Vowel Sounds)**: Большакова Grade 1 p.24 teaches vowels through a poem: 'Голосні почуєш в пісні, і у темному у лісі, і коли дивуєшся, і коли милуєшся. Легко вимовляються, весело співаються!' Голосні (vowels) are made with voice only — air flows freely through the mouth with no obstruction. You can sing them. You can shout them across a field.; 6 vowel sounds: [а], [о], [у], [е], [и], [і]. But 10 vowel letters: А, О, У, Е, И, І, Я, Ю, Є, Ї. The extra four (Я, Ю, Є, Ї) are 'iotated' — they can represent two sounds. Full details in M02. For now: every Ukrainian word has at least one vowel sound. Vowels are the heart of every syllable.; Захарійчук Grade 1 p.13 notation: vowel sounds are marked [•] in sound models. Practice hearing vowels: мА-мА (two [а]), мО-лО-кО (three [о]), У-ля (one [у]). Anna Ohoiko video for each vowel letter — watch, listen, repeat.
- **Приголосні звуки (Consonant Sounds)**: Большакова Grade 1 p.24: 'Приголосні деренчать і тихенько шелестять, голосно свистять і шиплять.' Приголосні (consonants) are made with voice + noise or noise only. Your lips, teeth, or tongue create an obstruction. You cannot sing a pure consonant — try singing [к] or [п].; 32 consonant sounds from 22 consonant letters. Some consonants come in pairs: тверді (hard) and м'які (soft). Захарійчук Grade 1 p.15: hard sounds marked [–], soft sounds marked [=]. This hard/soft distinction doesn't exist in English — it's uniquely Slavic.; Consonant letters to meet through Anna Ohoiko videos: М, Н, С, К, Л, Р, Б, В, Д, П, Т, Г, Ґ, З, Ж, Ш, Х, Й, Ч, Щ, Ц, Ф. Each video shows the letter, demonstrates the sound, and gives example words. Special: Ґ is uniquely Ukrainian. Щ always = two sounds [шч]. Ь (м'який знак) makes no sound — it softens the consonant before it.
- **Привіт! (Hello!)**: Your first Ukrainian conversation. Following Anna Ohoiko ULP Episode 1. Привіт! — Hi! (informal, for friends, family, peers). Як справи? — How are you? Answers: Добре (fine). Чудово (great). Нормально (okay). А у тебе? — And you?; Рада тебе бачити! (female speaker) / Радий тебе бачити! (male speaker) — Glad to see you! Ukrainian has gendered forms — women say рада, men say радий. This is your first encounter with grammatical gender. It will become a major topic starting M08.; Let's read Привіт letter by letter — your first sound analysis (звуковий аналіз): П [п] приголосний + р [р] приголосний + и [и] голосний + в [в] приголосний + і [і] голосний + т [т] приголосний. Two голосні, four приголосні. Every type of sound you learned in this module appears in this one word.
- **Підсумок (Summary)**: Self-check questions: How many letters in the Ukrainian alphabet? (33) How many sounds? (38) Why are they different? What are голосні? What are приголосні? Can you say 'голосна літера'? (No — sounds are голосні, not letters!) What does Привіт mean? How do you answer Як справи?

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

Call `query_cefr_level` on 5-10 key vocabulary words to confirm they match the target level (A1).

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
