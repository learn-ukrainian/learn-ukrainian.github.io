<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 67: Дієприкметниковий зворот (B1, B1.6 [Participles & Gerunds])

## Plan vocabulary to verify

- дієприкметниковий зворот (participle phrase)
- означуване слово (modified word — the noun the participle refers to)
- означення (attribute — syntactic role of the participle phrase)
- відокремлення (setting off — punctuation with commas)
- постпозиція (postposition — phrase after the noun)
- препозиція (preposition — phrase before the noun)
- підрядне речення (subordinate clause)
- залежні слова (dependent words)
- пунктограма (punctuation rule)
- обставинне значення (adverbial shade — causal/conditional)
- трансформація (transformation — converting between structures)
- стилістика (stylistics — choice between phrase and clause)

## Sections to research

- **Що таке дієприкметниковий зворот?**: Definition from Литвінова Grade 7 p.82: дієприкметник із залежними словами утворює дієприкметниковий зворот. It functions as an extended означення (attribute) in the sentence. Фільм, знятий в Україні, отримав найвищу нагороду. Here 'знятий в Україні' is the зворот: знятий (дієприкметник) + в Україні (залежні слова).; Comparison: одиничний дієприкметник vs зворот: Ми подивились обговорюваний фільм. (single participle — no commas) Фільм, знятий в Україні, отримав нагороду. (phrase — commas) The зворот carries more information and behaves differently in punctuation.; Syntactic role: the entire зворот is an означення (attribute). It answers the question який? яка? яке? які? about the noun. Книга (яка?), прочитана всіма учнями, лежала на столі.
- **Правила відокремлення**: Core rule from Авраменко Grade 7 p.104-108: AFTER the noun (постпозиція): COMMAS required. Фільм, знятий в Україні, отримав нагороду. Стіна, побілена вапном, сяяла чистотою. Земля, припорошена першим снігом, нагадує білий килим. BEFORE the noun (препозиція): NO commas. Знятий в Україні фільм отримав нагороду. Побілена вапном стіна сяяла чистотою. Припорошена першим снігом земля нагадує білий килим.; Special case: participle phrase refers to a personal pronoun — ALWAYS set off by commas regardless of position: Стомлений дорогою, я заснув одразу. Я, стомлений дорогою, заснув одразу. Both require commas because the означуване слово is я (pronoun).; From Заболотний Grade 8 p.205: participle phrases that also carry обставинне значення (причини, умови) are always set off: Схвильований новиною, батько негайно зателефонував. (The phrase explains WHY the father called — causal shade.)
- **Трансформація: зворот ↔ підрядне речення**: Every дієприкметниковий зворот can be restated as a subordinate clause with який/яка/яке/які: Книга, прочитана всіма учнями, лежала на столі. → Книга, яку прочитали всі учні, лежала на столі. Збудований у XVIII столітті палац зберігся до сьогодні. → Палац, який збудували у XVIII столітті, зберігся до сьогодні.; When to prefer which form: Дієприкметниковий зворот: more concise, literary, formal. Підрядне з який: more natural in speech, easier to parse. Ukrainian stylistic preference: підрядне з який is generally more natural. Дієприкметникові звороти are a feature of written/literary Ukrainian.; Practice: transform 8 sentences both ways (зворот → clause and clause → зворот). Learners note which version sounds more natural.
- **Складні випадки та помилки**: Multiple participle phrases in one sentence: Доповідь, написана студентом, перевірена професором, була відмінна. (two postposed phrases — both get commas) Написана студентом i перевірена професором доповідь була відмінна. (two preposed phrases joined by i — no commas needed); Common errors: 1. Forgetting commas after a postposed phrase that is not at end of sentence. 2. Adding commas to a preposed phrase (wrong: *Знятий в Україні, фільм...). 3. Dangling participle: the participle must refer to the noun it modifies. *Прочитана всіма, бібліотекар забрала книгу. (wrong referent) → Прочитану всіма книгу бібліотекар забрала.; Overuse warning: stacking participle phrases creates heavy, bureaucratic prose. Prefer variety: mix звороти with який-clauses and simple sentences.
- **Читання та практика**: Reading passage: a news report or article using participle phrases naturally. Learners identify all звороти, mark commas, determine whether each could be converted to a який-clause.; Error-correction passage: a text with deliberate punctuation errors in participle phrases. Learners fix all errors and explain the rules.; Production: learners rewrite 5 simple sentences using participle phrases to make them more concise: Міст, який збудували минулого року, з'єднує два береги. → Збудований минулого року міст з'єднує два береги.
- **Підсумок та перехід до M60**: Summary: дієприкметниковий зворот = дієприкметник + залежні слова. Після означуваного слова → коми. Перед означуваним словом → без ком. Після займенника → завжди коми. Трансформація ↔ підрядне з який. Self-check: Я правильно ставлю коми ✓/✗, Я можу перетворити зворот на підрядне речення ✓/✗.; Preview: M60 — Короткі прикметники. A different morphological form: зелен, молод, потрібен — expressive and poetic.

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
