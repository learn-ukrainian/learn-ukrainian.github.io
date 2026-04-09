<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 61: Слова і відмінки (A2, A2.9 [Metalanguage Bridge & Foundation])

## Plan vocabulary to verify

- іменник (noun)
- прикметник (adjective)
- дієслово (verb)
- займенник (pronoun)
- числівник (numeral)
- прислівник (adverb)
- прийменник (preposition)
- сполучник (conjunction)
- називний відмінок (nominative case)
- родовий відмінок (genitive case)
- рід (gender, grammatical)
- однина (singular)
- множина (plural)
- чоловічий рід (masculine gender)
- жіночий рід (feminine gender)
- середній рід (neuter gender)
- частина мови (part of speech)

## Sections to research

- **Частини мови: що це за слово? (Parts of Speech: What Kind of Word Is This?)**: Re-labeling known concepts: the learner already uses nouns, verbs, adjectives — now they learn what Ukrainian teachers call them. Method: Grade 3-4 textbook excerpts showing how Ukrainian children learn these terms.; Іменник (noun) — назва предмета: хто? що? — мама, стіл, радість. Прикметник (adjective) — ознака предмета: який? яка? яке? — великий, гарна, синє. Дієслово (verb) — дія предмета: що робити? що зробити? — читати, написати.; Займенник (pronoun) — замість іменника: хто? що? — я, ти, він, хтось. Числівник (numeral) — кількість або порядок: скільки? який? — п'ять, третій.
- **Сім відмінків: питання та назви (Seven Cases: Questions and Names)**: The complete case system with Ukrainian names and questions: Називний (Nominative) — хто? що? Родовий (Genitive) — кого? чого? Давальний (Dative) — кому? чому? Знахідний (Accusative) — кого? що? Орудний (Instrumental) — ким? чим? Місцевий (Locative) — на кому? на чому? Кличний (Vocative) — direct address.; Mnemonic strategy: Ukrainian schoolchildren learn "Не Роби Дурниць, Знай, Орудуй Місцем, Кличний!" — or the learner can create their own.; Practice: given a sentence, identify which відмінок each noun is in, using the question method (задати питання).
- **Рід і число: чоловічий, жіночий, середній (Gender and Number)**: Three genders: чоловічий рід (masculine), жіночий рід (feminine), середній рід (neuter). How to determine gender by ending: consonant → ч.р., -а/-я → ж.р., -о/-е → с.р.; Two numbers: однина (singular), множина (plural). How textbooks teach this: Один — однина. Багато — множина.; Combining terms: identify a word fully — іменник, жіночий рід, множина, родовий відмінок (e.g., книг = noun, feminine, plural, genitive).
- **Читаємо граматику українською (Reading Grammar in Ukrainian)**: Reading exercise: a Grade 4 textbook page explaining a simple grammar rule entirely in Ukrainian. Learner answers comprehension questions about the rule.; Building confidence: the learner realizes they can already understand Ukrainian grammar explanations. This is the bridge to B1, where grammar will increasingly be taught in Ukrainian.; Quick reference card: all terms introduced in this module, organized as a study aid the learner can return to.

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
