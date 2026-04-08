<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 3: Дієслова ходять парами (A2, A2.1 [Foundation and Aspect Introduction])

## Plan vocabulary to verify

- пара (pair)
- префікс (prefix)
- суфікс (suffix)
- корінь (root)
- читати / прочитати (to read)
- писати / написати (to write)
- брати / взяти (to take)
- говорити / сказати (to speak / to say)
- утворювати (to form)
- словник (dictionary)
- запам'ятовувати (to memorize)
- базовий (basic)

## Sections to research

- **Чому дієслова потрібно вчити парами? (Why Verbs Must Be Learned in Pairs)**: Reinforce the idea that aspect is fundamental. Learning a verb without its partner is like learning only half a word.; Introduce the standard notation: imperfective / perfective (e.g., робити / зробити).; Using a dictionary: how to find aspectual pairs in online or paper dictionaries.
- **Спосіб 1: Додавання префікса (Method 1: Adding a Prefix)**: The most common way to form a perfective verb: add a prefix to the imperfective base. The prefix often adds a specific meaning, but for now, we focus on its role in creating a perfective verb.; Core examples: писати / **на**писати; читати / **про**читати; робити / **з**робити; бачити / **по**бачити; готувати / **при**готувати.; Practice: given an imperfective verb, learner adds the correct prefix to make it perfective.
- **Спосіб 2: Зміна в корені або суфіксі (Method 2: Change in the Root or Suffix)**: The 'imperfectivization' pattern: a complex perfective verb (often with a prefix) gets an '-ува-' or '-юва-' suffix to become imperfective.; This is a more advanced concept, so we introduce it with simple pairs: відповідати / відповісти; вирішувати / вирішити; запитувати / запитати.; Show the vowel change that often accompanies this: 'о' -> 'а' (допомогти / допомагати).
- **Спосіб 3: Зовсім інші слова (суплетивізм) (Method 3: Completely Different Words - Suppletion)**: Some of the most common verbs have suppletive pairs that must be memorized.; Essential pairs: брати / взяти (to take); говорити / сказати (to say/tell); ловити / піймати (to catch); класти / покласти (to put).; Note: шукати (to search) and знайти (to find) are often presented together, but they are different actions, not a true aspect pair. The perfective of шукати is пошукати or відшукати.

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
