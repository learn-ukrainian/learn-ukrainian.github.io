<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 8: Вид і заперечення (B1, B1.0 [Baselines & Aspect Mastery])

## Plan vocabulary to verify

- заперечення
- загальне заперечення
- очікуване завершення
- ще
- факт
- очікування
- прагматика
- обговорювати
- обговорити
- вирішувати
- вирішити
- відповідати
- відповісти
- домити
- дочитати
- доробити
- нейтральний
- незавершений
- намір

## Sections to research

- **Тест: що ви заперечуєте?**: Diagnostic: 10 sentence pairs with negation — learners choose the natural option. Examples: — Ти читав цю книжку? — Ні, (не читав / ще не прочитав). [Both are valid — but they mean different things. Which fits the context?] — Ти написав звіт? — (Не писав / Ще не написав). — Чому ти не їв? / Чому ти ще не поїв?; Self-assessment: learners notice that both options often 'work' grammatically, but the MEANING shifts. This module teaches how to control that shift intentionally.; Key concept: negation + aspect = TWO different speech acts. Не + недоконаний: 'This activity didn't happen. I'm stating a fact.' Ще не + доконаний: 'This result hasn't been achieved yet, but it's expected.' The speaker's attitude toward the action (neutral fact vs pending expectation) determines the aspect.
- **Не + недоконаний: загальне заперечення**: Core pattern: не + недоконаний вид = the action is denied as a general fact (Заболотний Grade 7 p.57). Я не читав цю книжку. (Never read it — factual.) Вона не телефонувала. (She didn't call — no call occurred.) Ми не обговорювали це питання. (We didn't discuss it — the topic wasn't raised.) Він не вчив українську. (He didn't study Ukrainian — general statement.); In present tense: not doing something now/generally. Я не розумію. (I don't understand — ongoing state.) Він не працює сьогодні. (He's not working today.) Вона не їсть м'ясо. (She doesn't eat meat — general habit.) All naturally imperfective because the present tense itself is imperfective.; In questions: Ти не бачив моїх ключів? (general — have you seen my keys at all?) Ви не знаєте, де бібліотека? (polite question — impf natural). Чому ви не відповідали на листи? (why didn't you respond — general non-occurrence).
- **Ще не + доконаний: очікуване завершення**: Core pattern: ще не + доконаний вид = expected result has not been achieved YET (Литвінова Grade 7 p.38). Я ще не прочитав цю книжку. (I haven't read it yet — but I intend to / I'm expected to.) Вона ще не зателефонувала. (She hasn't called yet — but she's supposed to.) Ми ще не вирішили. (We haven't decided yet — decision pending.); The word ще is the key signal: it marks the expectation that the action WILL eventually be completed. Without ще, perfective negation is rare and marked: Він не прочитав книжку (unusual — implies specific failure). With ще: Він ще не прочитав книжку (natural — pending completion).; In future: Я ще не зроблю це до п'ятниці. (I won't have done it by Friday — result pending.) Вона ще не закінчить до вечора. (She won't have finished by evening.) These express incomplete progress toward an expected endpoint.
- **Підсумок: заперечення як прагматичний вибір**: Synthesis: negation + aspect is about the speaker's ATTITUDE, not about objective reality. The same factual situation (no letter was written) can be expressed as не писав (neutral fact) or ще не написав (pending expectation). The speaker CHOOSES how to frame the non-occurrence.; Extended dialogue practice: learners roleplay a scenario where a boss asks about project progress. Employee uses не + impf for tasks they weren't assigned (Ні, я не працював над цим — це не моє завдання) and ще не + pf for tasks in progress (Ще не закінчив, але закінчу до п'ятниці). The aspect reveals the employee's relationship to each task.; Common errors: *Я ще не читав цю книжку (mixing ще не with impf — awkward; choose either не читав or ще не прочитав). *Він не написав лист (without ще, perfective negation sounds like accusation or complaint — unnatural for neutral statement). Over-using ще не — not every negation implies pending completion.

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
