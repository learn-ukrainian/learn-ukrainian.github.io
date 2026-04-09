<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 27: Вид у наказовому способі (B1, B1.0 [Baselines & Aspect Mastery])

## Plan vocabulary to verify

- наказовий спосіб
- заборона
- застереження
- дозвіл
- прохання
- порада
- інструкція
- ввічливий
- категоричний
- відкривати
- відкрити
- закривати
- закрити
- торкатися
- запізнюватися
- забувати
- забути
- починати
- почати

## Sections to research

- **Тест: який наказ звучить природно?**: Diagnostic: 10 imperative pairs — learners choose the more natural option. Examples: (Відкрий / Відкривай) вікно, будь ласка — тут душно. Не (відкрий / відкривай) вікно — надворі холодно. (Запиши / Записуй) мій номер телефону. Не (запиши / записуй) нічого — я все скажу усно.; Self-assessment: pattern recognition. Most learners will notice: positive = usually pf, negative = usually impf. But WHY? This module explains the logic behind what intuition already senses.; Key insight framed: The imperative is where aspect choice is MOST meaningful in everyday speech. Відкрий! (do it — specific result) vs Відкривай! (go ahead, start doing it — process/permission). Не відкривай! (don't do it — general prohibition) vs Не відкрий! (very rare — be careful not to accidentally open).
- **Позитивний наказ: доконаний чи недоконаний?**: Perfective positive imperative — the default for commands (Заболотний Grade 7 p.84): Specific result requested: Напиши лист! (write and finish it). Відчини двері! (open them — result: doors open). Прочитай цю статтю! (read it through — result: you'll know the content). Sequential instructions: Спочатку помий руки. Потім наріж хліб. Візьми тарілку.; Imperfective positive imperative — invitation, permission, process: General invitation: Заходьте! Сідайте! (come in, sit down — welcoming, not commanding). Permission to begin/continue: Починайте! Читайте далі! Ongoing/repeated action: Пишіть акуратно. Говоріть повільніше. Process focus: Слухай уважно. (listen — ongoing attention, not a one-time act).; Politeness scale: imperfective imperatives often feel SOFTER than perfective. Допоможіть, будь ласка (impf — general request for help). Допоможіть мені перенести цю валізу (pf context — specific action). Розкажіть про себе (impf — open invitation). Розкажіть, що сталося (pf context — specific request for info). The aspect shifts the pragmatic force.
- **Негативний наказ: чому майже завжди недоконаний?**: The negative imperative rule (Литвінова Grade 7 p.84): Не + недоконаний вид is the standard form for prohibitions and warnings. Не відкривай вікно! (don't open it — general prohibition). Не торкайся! (don't touch — warning). Не запізнюйся! (don't be late — general advice). Не хвилюйся! (don't worry — reassurance).; WHY imperfective? A prohibition targets the ACTION ITSELF — it says 'this activity is forbidden.' Imperfective captures the activity as a whole (process, general category). Perfective captures a specific completed result — which makes less sense to prohibit (you can't 'un-complete' something).; Rare не + доконаний вид: warning against accidental result. Не впади! (careful not to fall! — accidental event). Не загуби ключі! (don't lose the keys — accidental result to prevent). Не забудь! (don't forget — accidental lapse). These are not prohibitions — they are WARNINGS about possible unwanted outcomes. The speaker doesn't forbid an action; they warn about a potential accidental result.
- **Підсумок: вид як прагматичний вибір**: Synthesis table: Positive imperative — pf (specific command/result), impf (invitation/permission/process). Negative imperative — impf (prohibition/advice), pf (warning against accidental result). The choice is PRAGMATIC — it depends on what the speaker wants to communicate, not on a mechanical rule.; Situational practice: learners roleplay 4 scenarios using both aspects in imperatives. A) Cooking: give step-by-step instructions (pf) + general food safety rules (impf). B) Doctor's advice: specific instructions (pf: випийте цей чай) + general prohibitions (impf: не пийте холодну воду). C) Tourist guide: invitations (impf: дивіться! фотографуйте!) + specific instructions (pf: зверніть увагу на цю фреску). D) Parent: commands (pf: прибери кімнату) + warnings (pf: не забудь ключі) + general rules (impf: не запізнюйся).; Common errors: *Не відкрий вікно! (wrong — general prohibition = impf: не відкривай). *Заходь, будь ласка! Сідь! (pf for invitation feels abrupt — impf Заходьте! Сідайте! is warmer). *Не забувай ключі! (overly general for a specific warning — pf Не забудь ключі! is better).

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
