<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 4: Яка вона людина? Описуємо людей навколо нас (A2, A2.1 [Foundation and Aspect Introduction])

## Plan vocabulary to verify

- людина (person, human being)
- стосунок (relationship)
- характер (character, personality)
- зовнішність (appearance)
- привітний (friendly, welcoming)
- щирий (sincere, genuine)
- працьовитий (hardworking)
- терплячий (patient)
- сусід (neighbor)
- описувати (to describe)
- впертий (stubborn, persistent)
- чуйний (responsive, caring)
- наполегливий (persistent, determined)
- родич (relative)
- знайомий (acquaintance)

## Sections to research

- **Зовнішність: як виглядає людина? (Appearance: What Does a Person Look Like?)**: Core appearance vocabulary: високий/низький, худий/повний, молодий/старий, темноволосий/світловолосий, кароокий/блакитноокий.; Describing with мати and з + instrumental (preview): Вона має карі очі / Вона з карими очима. Note: instrumental is previewed here but formally taught later in A2.4.; Practice describing people from photos or illustrations — building multi-adjective descriptions. Agreement: високий чоловік, висока жінка.
- **Характер: яка вона людина? (Character: What Kind of Person Is She?)**: Positive traits: привітний, щирий, чуйний, добрий, веселий, розумний, працьовитий, терплячий, відповідальний, наполегливий.; Challenging traits (not just "negative"): впертий, сумний, ледачий, серйозний, тихий. Ukrainian perspective — впертий can be positive (persistent, principled).; Sentence patterns for describing character: Він дуже добрий. Вона — щира людина. Мій брат — працьовитий і відповідальний.
- **Люди навколо нас: родичі, друзі, знайомі (People Around Us)**: Relationship vocabulary: родич, мати/батько, брат/сестра, дідусь/бабуся, дядько/тітка, друг/подруга, товариш, сусід/сусідка, колега, знайомий.; Talking about relationships: Ми дружимо вже п'ять років. Вона — моя найкраща подруга. Він мій сусід — живе поруч.; Describing how someone acts toward you: Вона мені довіряє. Він мене поважає. Вони нам допомагають.
- **Описуємо людину цілком (Describing a Person Fully)**: Combining appearance + character + relationship in a short paragraph: Мій друг Андрій — високий хлопець із карими очима. Він дуже веселий і щирий. Ми познайомилися в університеті.; Practice: learner describes 2-3 people they know using the full pattern (who they are, what they look like, what their character is).; Cultural note: Ukrainians often describe people through their actions and character more than physical appearance — "Добра людина" is a powerful compliment.

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

Call `query_cefr_level` on 5-10 key vocabulary words to confirm they match the target level (A2).

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
