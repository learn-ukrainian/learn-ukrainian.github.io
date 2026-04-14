<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 53: Health (A1, A1.8 [Past, Future, Graduation])

## Plan vocabulary to verify

- голова (head, f)
- горло (throat, n)
- живіт (stomach, m)
- рука (hand/arm, f)
- нога (leg/foot, f)
- {'болить (hurts — chunk': 'у мене болить)'}
- лікар (doctor, m)
- аптека (pharmacy, f)
- спина (back, f)
- око (eye, n)
- вухо (ear, n)
- зуб (tooth, m)
- ніс (nose, m)
- температура (fever/temperature, f)
- кашель (cough, m)
- нежить (runny nose, f)
- таблетка (pill, f)
- хворий (sick, adj)

## Sections to research

- **Dialogues**: Dialogue 1 — At the doctor's: — Що у вас болить? — У мене болить голова і горло. — Давно? — З учора. І в мене температура. — Ви кашляєте? — Так, трохи. І в мене нежить. — Зрозуміло. Це застуда. Я випишу ліки. Відпочивайте! — Дякую, лікарю! Doctor visit: symptoms + basic diagnosis.; Dialogue 2 — At the pharmacy: — Добрий день! У мене болить голова. Дайте, будь ласка, таблетки. — Від головного болю? — Так. І від кашлю, будь ласка. — Ось, будь ласка. Ще щось? — А є щось від нежиті? — Так, ось краплі. — Дякую! Скільки це коштує? Pharmacy: asking for medicine using known polite forms.
- **Тіло (The Body)**: Essential body parts (Grade 1-2 textbooks: частини тіла): голова (head, f), горло (throat, n), спина (back, f), живіт (stomach, m), рука (hand/arm, f), нога (leg/foot, f), око (eye, n), вухо (ear, n), зуб (tooth, m), ніс (nose, m). Note: рука = whole arm including hand. нога = whole leg including foot. These are the most useful for A1 — not an anatomy lesson.; Body part gender matters for adjectives (review from M09): велике око (big eye — neuter), великий ніс (big nose — masc), велика рука (big hand — fem). But at A1, focus on recognition — you'll use these mainly with болить.
- **У мене болить... (It Hurts...)**: The magic phrase: У мене болить + body part. У мене болить голова. (I have a headache. — literally 'at me hurts head') У мене болить живіт. (My stomach hurts.) У мене болить горло. (My throat hurts.) У мене болить спина. (My back hurts.) У мене болить зуб. (I have a toothache.) Learn this as a CHUNK — don't analyze the grammar (that's dative, A2+).; Common symptoms (as chunks): У мене температура. (I have a fever.) У мене кашель. (I have a cough.) У мене нежить. (I have a runny nose.) Мені холодно. (I'm cold.) Мені погано. (I feel bad.) Я хворий/хвора. (I'm sick. — masc/fem) Note: 'У мене болять зуби' (teeth hurt — plural form болять). Just recognize it.
- **Summary**: Health toolkit: Body parts: голова, горло, живіт, спина, рука, нога, око, вухо, зуб, ніс. Symptoms: У мене болить [body part]. У мене температура/кашель/нежить. State: Я хворий/хвора. Мені погано. At the doctor: Що у вас болить? — У мене болить... At the pharmacy: Дайте таблетки від [symptom], будь ласка. від головного болю (for headache), від кашлю (for cough), від нежиті (for runny nose). Self-check: How do you say 'My throat hurts and I have a fever'?

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
