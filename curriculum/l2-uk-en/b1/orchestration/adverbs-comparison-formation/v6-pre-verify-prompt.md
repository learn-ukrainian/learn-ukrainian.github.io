<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 37: Ступені порівняння та творення прислівників (B1, B1.4 [Degrees of Comparison & Word Formation])

## Plan vocabulary to verify

- прислівник (adverb — invariable part of speech)
- творення (formation — the process of creating new words)
- суфіксальний (suffixal — formed by adding a suffix)
- префіксальний (prefixal — formed by adding a prefix)
- суфіксально-префіксальний (prefixal-suffixal — formed by both)
- складання (compounding — joining two stems)
- незмінний (invariable — does not decline or conjugate)
- швидше (faster — adverb comparative of швидко)
- тихіше (more quietly — adverb comparative of тихо)
- якісний прикметник (qualitative adjective — source for comparable adverbs)
- по-українськи (in the Ukrainian way — prefixal-suffixal adverb)
- мимоволі (involuntarily — compound adverb)
- самохіть (of one's own will — compound adverb)
- праворуч (to the right — compound adverb)
- помалу (slowly, gradually — prefixed adverb, no hyphen)

## Sections to research

- **Як утворюються прислівники?**: Main formation patterns from Литвінова Grade 7 p.143: 1. Суфіксальний: від прикметників суфіксами -о, -е швидкий → швидко, тихий → тихо, гарячий → гаряче. 2. Префіксально-суфіксальний: по- + прикметник + -ому/-ськи/-и по-доброму, по-українськи, по-козацьки, по-новому. 3. Від іменників: зранку (ранок), вночі (ніч), додому (дім). 4. Складання: мимоволі, самохіть, праворуч.; State Standard §4.3.7 context: adverb formation from adjectives using -о, -е (добре, гарно) is a core B1 competency. Learners must recognize the formation pattern and produce adverbs fluently from any якісний прикметник.; Spelling rules for по- adverbs: по-українськи, по-братерськи, по-доброму, по-новому — always hyphenated. But: помалу, потроху, позавчора — no hyphen (these are prefix formations, not the по-...-ому pattern). Rule from Правопис 2019: по- with adverbs in -ому, -ему, -ськи, -зьки, -цьки = hyphen.
- **Ступені порівняння прислівників**: Only adverbs formed from якісні прикметники with -о, -е can form degrees of comparison (Заболотний Grade 7 p.151). Cannot: adverbs with prefixes пре-, над-, за-, супер- (превисоко, надшвидко — already express extreme degree).; Simple comparative from Литвінова Grade 7 p.141: суфікс -іш(е): тихо-тихіше, повільно-повільніше. суфікс -ш(е): швидко-швидше, довго-довше. With alternations: дорого-дорожче ([г]+[ш]=[жч]), вузько-вужче, високо-вище ([с]+[ш]=[шч]).; Simple superlative: най- + comparative. найтихіше, найшвидше, найдорожче. Intensified: щонайшвидше, якнайтихіше.
- **Прислівник vs прикметник: паралельні форми**: Critical distinction: adjective comparatives end in -ший (-ша, -ше, -ші), adverb comparatives end in -ше (-іше, -че). тихіший (adj., declines) vs тихіше (adv., invariable). Вона тихіша за нього (adj.). Вона говорить тихіше за нього (adv.).; Suppletive adverb forms (review from b1-040): добре → краще → найкраще погано → гірше → найгірше багато → більше → найбільше мало → менше → найменше; Practice: sentences where learners must choose adjective or adverb comparative/superlative. Distinguish modifying a noun vs modifying a verb.
- **Прислівники без ступенів порівняння**: From Заболотний Grade 7 p.151: Adverbs with пре-, над-, за-, супер- (превисоко, надшвидко). Adverbs of manner not from якісні прикметники (пішки, навмисно). Adverbs of time and place (вчора, тут, завжди). Adverbs formed with по-...-ськи (по-українськи).; Practice: sort a list of 15 adverbs into 'can form comparison' and 'cannot form comparison,' explaining why.
- **Прислівники в контексті**: Reading practice: a sports commentary or competition report using adverb comparatives and superlatives extensively. 'Спортсменка пробігла швидше за суперницю. Вона стрибнула найвище серед усіх учасниць. Тренувалася найбільше.'; Dialogue practice: two friends comparing how they do things — 'Хто швидше читає? Хто краще готує? Хто найчастіше подорожує?' Using чим...тим with adverbs: Чим більше читаєш, тим краще пишеш.; Self-check: form all comparison forms for 8 adverbs, including at least 2 suppletive and 2 with consonant alternations.
- **Типові помилки з прислівниками**: Error catalogue from Авраменко Grade 7 p.140: 1. *більш швидше (mixing forms). 2. *по українськи (missing hyphen). 3. *самий добре (Russicism — correct: найкраще). 4. *тихо → *тихше (wrong suffix — correct: тихіше). 5. Confusing -ше (adverb) with -ший (adjective): *Він біжить швидший.; Diagnostic exercise: 8 sentences with adverb errors. Learners identify and correct each, classifying by error type.
- **Підсумок**: Reference table: adjective comparison vs adverb comparison side by side (Заболотний Grade 8 p.28 format). Formation methods: суфіксальний, пр.-суф., складання. Comparison: проста (-іше/-ше), складена (більш/менш), найвищий (най-).; Summary decision tree: Is the word modifying a verb/adjective/adverb? → use adverb form (-ше/-іше). Is it modifying a noun? → use adjective form (-ший). Visual diagram showing the parallel tracks.; Preview: word formation — next modules explore how Ukrainian builds new adjectives (b1-042) and nouns (b1-043) from existing words. The formation patterns learned here (суфіксальний, префіксальний) apply to all word classes.

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

Call `query_cefr_level` on 5-10 key vocabulary words to confirm they match the target level (B1).

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
