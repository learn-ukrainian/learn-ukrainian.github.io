<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 36: Гарний - кращий (суплетивні форми) (B1, B1.4 [Degrees of Comparison & Word Formation])

## Plan vocabulary to verify

- суплетивний (suppletive — formed from a different root)
- кращий (better — suppletive comparative of гарний)
- гірший (worse — suppletive comparative of поганий)
- більший (bigger — suppletive comparative of великий)
- менший (smaller — suppletive comparative of малий)
- найкращий (best — suppletive superlative of гарний)
- найгірший (worst — suppletive superlative of поганий)
- краще (better — adverb, suppletive comparative of добре)
- гірше (worse — adverb, suppletive comparative of погано)
- більше (more — adverb, suppletive comparative of багато)
- менше (less — adverb, suppletive comparative of мало)
- гарніший (more handsome — regular comparative, physical appearance only)
- нерегулярний (irregular — synonym for suppletive forms)
- корінь (root — the core morpheme of a word)

## Sections to research

- **Що таке суплетивні форми?**: Definition: суплетивізм (suppletion) is when a grammatical form is built from a completely different root than the base word. In English: good-better, bad-worse. In Ukrainian: гарний-кращий, поганий-гірший. The root changes entirely, unlike regular formation where only suffixes change.; Why suppletion exists: these are the most commonly used adjectives in any language. High frequency → more likely to preserve ancient irregular forms. Ukrainian inherited these from Proto-Slavic, and they are stable — every native speaker uses them without thinking.; Comparison with regular formation: Regular: сильний → сильніший (same root сильн-). Suppletive: гарний → кращий (different root крат-/красн-). The learner needs to memorize these — no rule predicts them.
- **Чотири основні суплетивні пари**: гарний (good/beautiful) → кращий → найкращий Note: гарніший also exists but means 'more beautiful/handsome' (physical appearance). кращий means 'better' (general quality). Ця книжка краща за ту. Він гарніший за брата (more handsome).; поганий (bad) → гірший → найгірший No alternative regular form (*поганіший is not standard). Ситуація стає гіршою. Це найгірший варіант.; великий (big/great) → більший → найбільший Note: великий also has regular form великіший (rare, dialectal). більший is standard. Це більша кімната. Найбільше місто України.
- **Напівсуплетивні форми**: Some adjectives undergo such heavy consonant changes that they feel nearly suppletive, even though the root is technically preserved: високий → вищий (not *високіший) низький → нижчий широкий → ширший вузький → вужчий легкий → легший довгий → довший дорогий → дорожчий товстий → товщий; These are NOT true suppletive forms (the root is recognizable), but learners often struggle with them because the changes are dramatic. Systematic review: base form → comparative → superlative for each.; Practice passage: a market scene where a buyer compares products, using both suppletive and near-suppletive forms naturally. 'Ці яблука більші, але ті дешевші. А які найкращі?'
- **Суплетивні прислівники**: Parallel adverb forms follow the same suppletive roots: добре (well) → краще → найкраще погано (badly) → гірше → найгірше багато (much) → більше → найбільше мало (little) → менше → найменше; Note the -е ending for adverb comparatives vs -ий for adjective comparatives: кращий (adj.) vs краще (adv.). Він кращий студент. Він вчиться краще. більший (adj.) vs більше (adv.). Більша кімната. Читай більше.; Common expressions with suppletive adverbs: Краще пізно, ніж ніколи. Чим менше знаєш, тим краще спиш. Practice: sentences where learners choose adjective or adverb form.
- **Типові помилки та розмовна практика**: Error 1: using regular forms instead of suppletive (*поганіший → гірший, *маленькіший → менший). Error 2: confusing adjective and adverb forms (*Він вчиться кращий → Він вчиться краще). Error 3: Russicism самий + superlative (*самий кращий → найкращий).; Dialogue practice: two friends planning a vacation, comparing options. They use suppletive forms throughout: 'Цей готель кращий, але дорожчий. А менший готель ближчий до моря. Яке найкраще рішення? Може, краще поїхати в наймолодше місто?'; Self-assessment: translate 10 comparison sentences from English to Ukrainian, requiring suppletive forms. Then peer-check.
- **Суплетивні форми у відмінках**: Declension practice for suppletive comparatives — these decline like regular adjectives but learners need explicit drill because the stems are unfamiliar: Н. кращий / краща / краще / кращі, Р. кращого / кращої / кращого / кращих, Д. кращому / кращій / кращому / кращим. Same paradigm for гірший, більший, менший.; Contextual sentences requiring declined suppletive forms in oblique cases (Заболотний Grade 8 p.18): Я задоволений кращим результатом (Ор.в.). Ми розмовляли про гіршу ситуацію (Зн.в.). У меншій кімнаті (М.в.) холодніше.
- **Підсумок**: Complete reference table: гарний — кращий — найкращий (добре — краще — найкраще) поганий — гірший — найгірший (погано — гірше — найгірше) великий — більший — найбільший (багато — більше — найбільше) малий — менший — найменший (мало — менше — найменше); Decision flowchart: Is it one of the 4 core pairs? → suppletive. Is it високий/низький/широкий/вузький/легкий/довгий/дорогий/товстий? → near-suppletive with consonant change. Otherwise → regular (-іш-/-ш-). This visual helps learners systematize their knowledge.; Preview: next module extends comparison to прислівники — how adverbs form ступені порівняння systematically, including the suppletive adverb forms reviewed here.

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
