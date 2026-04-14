<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 16: Verbs Group I (A1, A1.3 [Actions])

## Plan vocabulary to verify

- читати (to read)
- знати (to know)
- працювати (to work)
- слухати (to listen)
- гуляти (to walk)
- готувати (to cook)
- робити (to do — Group II, preview as chunk)
- вивчати (to study/learn)
- малювати (to draw)
- грати (to play)
- вечеря (dinner, f)
- музика (music — review from M15)

## Sections to research

- **Діалоги (Dialogues)**: Dialogue 1 — What do you do? (ULP Ep22 pattern): — Що ти робиш? — Я читаю книгу. А ти? — Я слухаю музику. — А що робить Олена? — Вона готує вечерю. All three persons (я/ти/він,вона) emerge naturally.; Dialogue 2 — At work/school: — Де ти працюєш? — Я працюю в офісі. А ти? — Я не працюю, я навчаюся. — Ти знаєш українську? — Так, я вивчаю! Group I verbs in practical context.
- **Перша дієвідміна (Group I Verbs)**: Варзацька Grade 4 p.129: verb conjugation table (теперішній час). Group I verbs have infinitive in -ати (or -увати, -яти): читати → я читаю, ти читаєш, він/вона читає ми читаємо, ви читаєте, вони читають. Pattern: stem + -ю, -єш, -є, -ємо, -єте, -ють.; Six essential Group I verbs: читати (to read): читаю, читаєш, читає... знати (to know): знаю, знаєш, знає... працювати (to work): працюю, працюєш, працює... слухати (to listen): слухаю, слухаєш, слухає... гуляти (to walk): гуляю, гуляєш, гуляє... готувати (to cook): готую, готуєш, готує...
- **Я, ти, він/вона (Persons)**: Focus on the three most-used forms: Я читаю (I read) — ending -ю Ти читаєш (You read) — ending -єш Він/вона читає (He/she reads) — ending -є These three cover 90% of A1 conversations. Plural forms for recognition: ми читаємо, ви читаєте, вони читають.; Building sentences with known vocabulary: Я читаю нову книгу. (M08 noun + M09 adjective + M16 verb) Ти знаєш цю пісню? (M12 demonstrative + M16 verb) Вона слухає українську музику. (M16 verb + adjective + noun) Note: the object may change form (книгу, пісню) — learn as chunks for now.
- **Підсумок — Summary**: Group I conjugation pattern: я -ю, ти -єш, він/вона -є, ми -ємо, ви -єте, вони -ють. Works for: читати, знати, працювати, слухати, гуляти, готувати. Self-check: Conjugate 'слухати' for я, ти, він/вона. Say what you do (Я читаю...), ask what someone does (Що ти робиш?).

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
