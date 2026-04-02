<correction_directive>
CRITICAL: Your previous attempt failed the following checks. Write the module FROM SCRATCH. All original constraints still apply.

- FIX: Missing section heading: 'Підсумок та перехід до M22'
- NOTE: Plan expects 5 exercise(s) but content has 0 placeholders
</correction_directive>

LEARNINGS FROM PAST BUILDS (same error patterns seen before):
- [GLOBAL] сес-тра is a VALID word division per Правопис 2019 §49. Do NOT mark it as an error. Phonetic syllabification (се-стра) and typographic word division (сес-тра) follow different rules — both are correct in their respective contexts.
- [GLOBAL] Ukrainian textbooks teach a hands-on-EARS test for voicing (закрий долонями вуха), NOT a hand-on-throat test. The hand-on-throat test is a valid phonetics technique but must NOT be attributed to Ukrainian textbooks. Source: Кравцова 2019, Grade 2, p.39.
- [GLOBAL] Do NOT invent Ukrainian words for minimal pairs. "Сір" is NOT a word meaning "grey" — the correct form is "сірий". Use verified minimal pairs only: кит/кіт, бити/біти, лис/ліс.
- [GLOBAL] NEVER frame Ukrainian as "lacking" or "missing" letters that Russian has. Ukrainian has its own 33-letter alphabet — it is complete. Do NOT write "Ukrainian lacks Ъ, Ы, Э" or "Ukrainian doesn't have these Russian letters." Instead, highlight what Ukrainian HAS: Ґ, Є, Ї, І are unique to Ukrainian. Present Ukrainian on its own terms.
- [GLOBAL] NO LLM filler phrases. Do NOT write: "Let us start with...", "Numbers unlock the real Ukraine", "You now possess a complete...", "It is incredibly versatile", "one of the most rewarding skills". Start sections with a dialogue, a question, or a concrete example — never with a generic motivational opener. If a sentence could appear in any language course about any topic, delete it.
- [GLOBAL] Every exercise item must test something EXPLICITLY taught in the preceding prose. If an exercise tests the collocation "малювати картину", the prose must contain "малювати картину" as a taught example. Do NOT test collocations, vocabulary, or patterns that the learner has to infer — test what was taught.
- [GLOBAL] Quiz correct answers must be RANDOMIZED across positions. Do NOT place the correct answer at index 0 for all items. Distribute correct answers roughly evenly across all positions (0, 1, 2) to prevent pattern-guessing.
- [GLOBAL] Do NOT use spatial metaphors for abstract grammatical requirements. Example: "на" with musical instruments is NOT "on top of" — it is an abstract grammatical requirement that must be memorized. Misleading mnemonics cause incorrect generalizations. If a rule must simply be memorized, say so directly.
- [GLOBAL] Memorized chunks are allowed before their grammar is formally taught. Natural Ukrainian expressions (Мені подобається, У мене є, Мене звати, Як справи?, Звідки ти?, Скільки коштує?, Мені ... років) can appear in ANY module as memorized chunks, even if the underlying grammar (dative, genitive, etc.) is not taught until later. This mirrors how Ukrainian children and L2 learners naturally acquire language. Do NOT flag these as forward-references. DO flag premature drilling of case paradigms, untaught vocabulary words, and grammar analysis before its module.
- [GLOBAL] Inline activity markers (<!-- INJECT_ACTIVITY: ... -->) must ONLY appear AFTER all concepts they test have been taught. If an activity tests both soft signs and apostrophes, it must appear after BOTH sections, not after the first one. This is critical in Ukrainian where apostrophe rules (б,п,в,м,ф,р + я,ю,є,ї) appear constantly — placing an apostrophe exercise before the apostrophe section teaches wrong sequencing. Rule: scan each activity's items and verify every tested concept has a preceding H2 section that teaches it.



---

## Your Writing Identity

**You are: Experienced Ukrainian Language Instructor.** Your persona is *The Cultural Guide*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **21: Віддієслівні іменники** (B1, B1.3 [Verbs]).

**Target: 4000–6000 words** of prose (Ukrainian examples count toward word total, headings and exercise placeholders do not).

---

## Step 1: Pacing Plan (output this FIRST)

Before writing any content, output a `<pacing_plan>` block. Evaluate each section from the plan and commit to a word budget. This prevents frontloading early sections and rushing later ones.

```
<pacing_plan>
Section 1 "Title": ~XXX words — [1-sentence content focus]
Section 2 "Title": ~XXX words — [1-sentence content focus]
...
Summary: ~150 words
Total: 4000+ words
</pacing_plan>
```

Then begin writing the module content. Follow your own pacing plan — each section must hit its word budget (±10%).

---

## 9 Hard Rules

1. **IMMERSION TARGET: 40-60% Ukrainian** — this is the percentage of Ukrainian text in your output. The audit will REJECT the module if immersion is outside this range. For A1 early modules, the learner cannot read Cyrillic — English must dominate. For A2+, Ukrainian must carry a significant share — add Ukrainian Reading Practice blocks, dialogues, and example paragraphs to reach the target. Too little Ukrainian fails audit just as much as too much.
2. **EVERY plan point MUST appear in your output.** The plan's `content_outline` lists specific points for each section. You MUST cover ALL of them — every textbook reference, every notation, every example. If the plan says "Захарійчук Grade 1: [•] for vowels, [–] for consonants", you MUST include that notation. Skipping plan points is the #1 reason modules get rejected. Before submitting, mentally check each plan point against your output.
3. **NO IPA, NO Latin transliteration** — never write [mɑmɑ], (khlib), or phonetic brackets. Describe sounds by comparison: "Х sounds like «ch» in Scottish «loch»."
4. **NO "In this lesson we will..."** — never use formulaic openers. Start with a dialogue, a question, or a situation.
5. **Ukrainian quotes: «...»** for Ukrainian text. Use regular quotes "..." for English metalanguage (e.g., "like the 'a' in 'father'").
6. **Place exercise markers only** — do NOT write exercises directly. Place `<!-- INJECT_ACTIVITY: {id} -->` markers where exercises should appear. A separate pipeline step generates the actual exercises from the plan's activity_hints.
7. **NO meta-commentary or vocabulary tables** — do NOT add "Content notes:", word count summaries, self-audit sections, or vocabulary/словник tables at the end. A downstream tool generates vocabulary tables automatically. Just write the module content and stop.
8. **Hit the word target** — you MUST write 4000–6000 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.
9. **NO archaic, obsolete, or rare words** — use only modern standard Ukrainian. Do not use words marked as archaic (застаріле) or dialectal in dictionaries. Example: use «кін» not «кон», use «пом'якшені» not «м'якшені». When in doubt, choose the common modern form. Your pre-training contains Russian-influenced archaic forms — verify unfamiliar words.
10. **EVERY module MUST end with `## Підсумок`** — this is the last H2 section before the file ends. It contains a self-check recap. If you forget this section, the audit REJECTS the module and you waste a retry. Write it LAST, after all other sections.

**Note:** Do NOT add stress marks (´) to any Ukrainian word — a deterministic tool handles this after you write.

## Exercise Placement — Markers Only

**Do NOT write exercises directly.** A separate pipeline step (ACTIVITIES) generates all exercises from the plan's `activity_hints`. Your job is to place markers showing WHERE exercises belong.

### How It Works

1. Read the plan's `activity_hints` — each entry has an `id`, `type`, and `focus`
2. After the relevant teaching section, place an injection marker
3. The ACTIVITIES step reads your prose + the plan hints and generates complete exercises

### Marker Format

Place markers after key teaching sections. Each marker corresponds to ONE `activity_hints` entry from the plan:

```
<!-- INJECT_ACTIVITY: quiz-sounds-vs-letters -->
```

Rules:
- Use the EXACT `id` from the plan's `activity_hints` — do not invent new IDs
- Place the marker right after the prose that teaches the concept the exercise tests
- Spread markers evenly throughout the module — never cluster them
- If the plan has 4 activity hints, you should place 4 markers in your prose

### Example

If the plan says:
```yaml
activity_hints:
  - id: quiz-sounds-vs-letters
    type: quiz
    focus: "Distinguish звук from літера"
  - id: match-false-friends
    type: match-up
    focus: "Match false friend Cyrillic letters to real sounds"
```

Your prose should contain (after the relevant sections):
```
[...prose about sounds and letters...]

<!-- INJECT_ACTIVITY: quiz-sounds-vs-letters -->

[...prose about false friend letters...]

<!-- INJECT_ACTIVITY: match-false-friends -->
```

### What NOT to Do

- Do NOT write `:::quiz`, `:::fill-in`, `:::match-up`, or any DSL exercise blocks
- Do NOT write exercise questions, answers, or options — the ACTIVITIES step handles all of this
- Do NOT invent marker IDs — use only IDs from the plan's `activity_hints`

---

## Plan

<plan_content>
module: b1-021
level: B1
sequence: 21
slug: verbal-nouns
version: '3.0'
title: "Віддієслівні іменники"
subtitle: "Читання, бачення, відкриття — як дієслова стають іменниками"
focus: grammar
pedagogy: PPP
phase: "B1.3 [Verbs]"
word_target: 4000
objectives:
- "Learner can form віддієслівні іменники using productive suffixes
  -ння, -ття, -іння and understands the formation rules"
- "Learner can distinguish between суфіксальний and безафіксний ways
  of forming nouns from verbs (читання vs пошук)"
- "Learner can correctly spell іменники with -ння, -ття, -іння
  (подвоєння: читання, знання; -ття: відкриття, забуття)"
- "Learner can use віддієслівні іменники in formal and academic register
  instead of verbose verb constructions (здійснювати перевірку → перевірка)"
- "Learner can identify the register difference: віддієслівні іменники
  on -ння/-ття are bookish/formal, while безафіксні are neutral"
dialogue_situations:
- setting: 'At a Ukrainian IT company — discussing project processes: Тестування (n,
    testing) триватиме два дні. Після написання (n, writing) коду — перевірка. Навчання
    (n, training) нових працівників — наш пріоритет. Читання (n, reading) документації
    обов''язкове.'
  speakers:
  - Менеджер проєкту
  - Розробник (developer)
  motivation: 'Verbal nouns: тестування, написання, навчання, читання — -ння/-ття
    formations'
content_outline:
- section: "Що таке віддієслівні іменники?"
  words: 550
  points:
  - "Definition from Вашуленко Grade 3 p.107:
    Iменники можуть утворюватися від дієслів i називати дії:
    зустріч, плавання. They name the ACTION itself as a thing.
    читати → читання (the act of reading)
    бачити → бачення (the act of seeing, also: vision)
    відкрити → відкриття (discovery, opening)"
  - "Why this matters at B1: віддієслівні іменники are essential for
    academic and formal Ukrainian. They allow learners to nominalize
    actions: замість 'ми досліджували' → 'наше дослідження показало'.
    This is the language of news, science, and official documents."
  - "Categories: іменники що називають дію (процес) vs результат:
    навчання = process of learning AND the education itself.
    відкриття = process of opening AND the discovery made.
    Context determines which meaning applies."
- section: "Суфікс -ння (-ання, -яння) — найпродуктивніший"
  words: 700
  points:
  - "Formation rule: основа інфінітива + -ння.
    читати → читання, писати → писання, малювати → малювання,
    вивчати → вивчання (process) vs вивчення (result — see below).
    From Заболотний Grade 7 p.136: віддієслівні іменники на -ння, -ття
    є продуктивними в офіційно-діловому, науковому та
    публіцистичному стилях."
  - "Spelling rule: подвоєння н → -нн-:
    The суфікс is -нн- + закінчення -я, giving -ння.
    знати → знання [знан':а], читати → читання [читан':а].
    This подвоєння is consistent across all -ння forms.
    From Голуб Grade 6 p.107: суфікси -инн(я), -інн(я), -енн(я)."
  - "Variant: -іння from II дієвідміна verbs:
    говорити → говоріння, ходити → ходіння, бачити → бачення.
    The голосний before -ння depends on the дієвідміна:
    I: -а- → -ання (читання), -ува- → -ування (малювання).
    II: -и- → -іння (ходіння) or -ення (бачення).
    Some verbs have parallel forms: вивчання / вивчення (process / result)."
  - "Practice: form -ння nouns from 10-12 common verbs, noting which
    дієвідміна determines the vowel. Check against VESUM for edge cases."
- section: "Суфікс -ття та безафіксний спосіб"
  words: 650
  points:
  - "Formation with -ття: from verbs with stems ending in consonant clusters:
    відкрити → відкриття, забути → забуття, життя ← жити.
    пізнати → пізнання, but здобути → здобуття.
    Заболотний Grade 7 p.136: становлення, забуття — книжне забарвлення."
  - "Безафіксний спосіб (zero derivation) from Литвінова Grade 6 p.83:
    пошукати → пошук, підписати → підпис, раній → рань.
    'Нові слова можна утворити також усіканням частин слова
    (префіксів i суфіксів). Цей спосіб словотворення має назву
    безафіксний.' Many common words are formed this way:
    біг (← бігти), хід (← ходити), лет (← летіти),
    спів (← співати), крик (← кричати)."
  - "Register difference:
    -ння/-ття forms are bookish/formal: дослідження, навчання, спілкування.
    Безафіксні forms are neutral/colloquial: біг, хід, крик, спів.
    Compare: вивчення цього питання (formal) vs пошук відповіді (neutral).
    Learners practise choosing the right register for context."
- section: "Віддієслівні іменники у реченні"
  words: 600
  points:
  - "Syntactic roles: віддієслівні іменники function as regular nouns —
    they decline, take adjectives, and serve as subjects/objects.
    Вивчення мови потребує часу. (subject)
    Я люблю читання. (object)
    Після закінчення курсу... (after preposition)
    They require the same case government as their source verb:
    досліджувати проблему (Зн.) → дослідження проблеми (Р.)."
  - "Noun phrase expansion:
    навчання → навчання дітей → навчання дітей у школі
    The verbal noun heads a phrase that mirrors the verb's arguments:
    вчити дітей у школі → навчання дітей у школі.
    This is how Ukrainian builds complex academic phrases."
  - "Avoiding overuse — a style concern:
    Too many -ння forms make text heavy and bureaucratic.
    *Здійснення забезпечення виконання... — мовний канцелярит.
    Better: Забезпечити виконання... (use verb when possible).
    Антоненко-Давидович principle: use nouns for concepts, verbs for actions."
- section: "Практика: від дієслова до іменника"
  words: 550
  points:
  - "Exercise block 1 — Formation:
    Given 12-15 verbs, form the віддієслівний іменник:
    говорити → говоріння, створити → створення, жити → життя,
    будувати → будування/будівництво, мислити → мислення.
    Some verbs have two forms: note the semantic difference."
  - "Exercise block 2 — In context:
    Replace verbose constructions with віддієслівні іменники:
    'Коли ми вивчали цю тему...' → 'Під час вивчення цієї теми...'
    'Те, що він приїхав, здивувало нас' → 'Його приїзд здивував нас.'
    6-8 transformations from colloquial to formal register."
  - "Exercise block 3 — Register identification:
    Given pairs (читання / крик, дослідження / пошук, спілкування / розмова),
    label each as formal or neutral. Place them in appropriate sentences:
    наукове _____ (дослідження) vs щоденний _____ (пошук)."
- section: "Читання: віддієслівні іменники у новинах"
  words: 600
  points:
  - "A short Ukrainian news article (adapted B1 level) using multiple
    віддієслівні іменники naturally: будівництво, забезпечення,
    відновлення, виробництво, навчання, дослідження.
    Topic: education or technology in Ukraine."
  - "Comprehension tasks that test LANGUAGE, not content:
    — Знайдіть у тексті всі віддієслівні іменники.
    — Від яких дієслів вони утворені?
    — Яким способом утворено: суфіксальним чи безафіксним?
    — Замініть два віддієслівні іменники на дієслівні конструкції."
  - "Production: learners write 3-4 sentences about their city/country
    using at least 3 віддієслівні іменники. Model:
    Будівництво нових шкіл — це важливе завдання.
    Навчання української мови потребує практики.
    Відкриття нового музею відбудеться наступного місяця."
- section: "Підсумок та перехід до M22"
  words: 350
  points:
  - "Summary: віддієслівні іменники — іменники, утворені від дієслів,
    що називають дії як предмети. Суфікси -ння, -ття, -іння.
    Безафіксний спосіб. Регістрові відмінності.
    Self-check: Я можу утворити іменник від дієслова ✓/✗,
    Я знаю правопис -ння, -ття ✓/✗,
    Я можу перетворити дієслівну конструкцію на іменникову ✓/✗."
  - "Preview: M22 — Зворотні дієслова. The -ся/-сь suffix that turns
    transitive verbs reflexive: мити → митися, бачити → бачитися.
    This is another productive way Ukrainian modifies verb meaning."
vocabulary_hints:
  required:
  - "віддієслівний іменник (verbal noun — noun derived from a verb)"
  - "читання (reading — verbal noun from читати)"
  - "бачення (vision, seeing — verbal noun from бачити)"
  - "відкриття (discovery, opening — verbal noun from відкрити)"
  - "навчання (learning, education — verbal noun from навчати)"
  - "дослідження (research, study — verbal noun from досліджувати)"
  - "знання (knowledge — verbal noun from знати)"
  - "спілкування (communication — verbal noun from спілкуватися)"
  - "створення (creation — verbal noun from створити)"
  - "забуття (oblivion, forgetting — verbal noun from забути)"
  - "пошук (search — zero-derivation from пошукати)"
  - "підпис (signature — zero-derivation from підписати)"
  - "суфіксальний (suffixal — word formation method)"
  - "безафіксний (zero-derivation — word formation without affixes)"
  recommended:
  - "становлення (formation, establishment — bookish)"
  - "будівництво (construction — from будувати)"
  - "виробництво (production, manufacturing)"
  - "забезпечення (provision, ensuring)"
  - "відновлення (restoration, renewal)"
  - "мислення (thinking, thought process)"
  - "приїзд (arrival — zero-derivation from приїхати)"
  - "канцелярит (bureaucratese — overuse of nominal style)"
  - "продуктивний (productive — in word formation sense)"
  - "основа інфінітива (infinitive stem — base for formation)"
activity_hints:
- type: fill-in
  focus: "Form the correct віддієслівний іменник from a given verb in sentence context"
  items: 10
- type: match-up
  focus: "Match verbs to their derived nouns (читати→читання, відкрити→відкриття, бігти→біг)"
  items: 10
- type: group-sort
  focus: "Sort verbal nouns by formation type: суфіксальний (-ння/-ття) vs безафіксний"
  items: 10
- type: sentence-builder
  focus: "Transform verb phrases into nominal phrases (Ми вивчали → Вивчення...)"
  items: 6
- type: quiz
  focus: "Identify register: which verbal noun is formal vs neutral? Choose appropriate form for context"
  items: 8
connects_to:
- "b1-020 (Наказовий спосіб — verb mood mastery, now verb-to-noun transition)"
- "b1-022 (Зворотні дієслова — another verb modification: -ся/-сь)"
- "b1-024 (Творення дієслів — completes the verb formation picture)"
- "b1-044 (Творення назв осіб i місць — extends noun word formation)"
prerequisites:
- "b1-020 (Imperative nuances — completes mood system before word formation)"
grammar:
- "Суфіксальне творення: -ння (читання), -ття (відкриття), -іння (ходіння), -ення (бачення)"
- "Безафіксний спосіб: пошук, підпис, біг, хід, крик, спів"
- "Подвоєння in -ння forms: читання [читан':а], знання [знан':а]"
- "Register: -ння/-ття = bookish/formal; безафіксні = neutral"
- "Case government transfer: досліджувати проблему → дослідження проблеми"
- "Avoiding канцелярит: verbs for actions, nouns for concepts"
register: академічний
references:
- title: "Вашуленко Grade 3, p.107"
  notes: "Iменники утворюються від дієслів i називають дії: зустріч, плавання.
    Basic introduction to verbal noun concept."
- title: "Голуб Grade 6, p.107"
  notes: "Написання іменників із суфіксами -инн(я), -інн(я), -енн(я), -ен(я).
    Spelling rules table with examples."
- title: "Литвінова Grade 6, p.83"
  notes: "Безафіксний спосіб словотворення: пошук ← пошукати, підпис ← підписати.
    Definition and examples of zero derivation."
- title: "Заболотний Grade 7, p.136"
  notes: "Віддієслівні іменники на -ння, -ття: становлення, забуття.
    Книжне забарвлення; продуктивні в офіційно-діловому i науковому стилях."

</plan_content>

---

## Pre-Verified Facts (from MCP tools — use these, do NOT guess)

A verification step already called VESUM, textbooks, Правопис, and style guide tools. The results below are GROUND TRUTH. Use them:
- If a word is marked ❌ NOT IN VESUM — do NOT use it
- If a textbook excerpt is provided — use that pedagogy
- If a calque is flagged — use the correct alternative
- If CEFR says a word is above target — find a simpler synonym

You do NOT need to call tools yourself — the facts are already verified.

<pre_verified_facts>
## VESUM Verification
- Confirmed: [віддієслівний, іменник, читання, бачення, відкриття, навчання, дослідження, знання, спілкування, створення, забуття, пошук, підпис, суфіксальний, безафіксний, становлення, будівництво, виробництво, забезпечення, відновлення, мислення, приїзд, канцелярит, продуктивний, основа, інфінітив]
- Not found: [None]

## Textbook Excerpts
### Section: Що таке віддієслівні іменники?
> Iменники можуть утворюватися від дієслів i називати дії: зустріч, плавання.
> Source: Вашуленко, Grade 3 (Reflected in content outline)

### Section: Суфікс -ння (-ання, -яння) — найпродуктивніший
> Суфікси -інн(я), -енн(я) вживаємо в іменниках середнього роду... утворених від дієслів із кінцевим голосним основи и або і: бурити — буріння, ходити — ходіння.
> Source: Golub, Grade 6, p. 107

### Section: Суфікс -ття та безафіксний спосіб
> Нові слова можна утворити також усіканням частин слова (префіксів і суфіксів... Цей спосіб словотворення має назву безафіксний. У такий спосіб утворено багато іменників від дієслів... наприклад: підпис ← підписати.
> Source: Litvinova, Grade 6, p. 83

### Section: Віддієслівні іменники у реченні
> До книжного забарвлення належать ті [іменники], які утворюють загальні й абстрактні назви, назви опредметнених дій. Це віддієслівні іменники на -ння, -ття: становлення, забуття. Ці суфікси є продуктивними в офіційно-діловому, науковому та публіцистичному стилях.
> Source: Karaman, Grade 10, p. 136

## Grammar Rules
- [Написання -нн- в іменниках середнього роду]: Правопис §32.5 — Суфікси -нн-(я) / -інн-(я), -анн-(я) (-янн-(я) пишемо з двома буквами н. Варіант -інн-(я) для дієслів на -и/-і (ходіння), -анн-(я) для дієслів на -а (гукання), -енн-(я) при наголосі на корені (звернення).

## Calque Warnings
- [Приймати участь]: CALQUE — CORRECT: **брати участь**.
- [Приймати рішення]: CALQUE (often) — CORRECT: **ухвалювати рішення** or **приймати рішення** (depending on context, but 'ухвалювати' is more formal). Style guide ad-172 recommends 'ухвалювати пропозицію'.
- [Нагромадження віддієслівних іменників]: STYLE ERROR (Канцелярит) — Антоненко-Давидович ad-120: Overuse makes text sound unnatural ("не по-українському"). Use verbs where possible.

## CEFR Check
- навчання: B1 — OK
- дослідження: B1 — OK
- спілкування: B1 — OK
- бачення: B1 — OK
- вивчення: B1 — OK
- відновити (відновлення): B2 — Acceptable for B1 context (high frequency in news).
</pre_verified_facts>


## Knowledge Packet (textbook excerpts from RAG)

**MANDATORY — this is your primary source.** The knowledge packet contains real Ukrainian textbook excerpts. Your content MUST use the terminology, notation, and pedagogical approach from these excerpts.

**Hard rules for the knowledge packet:**
1. **Use Ukrainian terminology from the packet, not English linguistics.** If the textbook says «складоподіл», you write «складоподіл» — never CVCCV or "syllable division rules" paraphrased from English phonology. If it says «відкритий склад», you write «відкритий склад» — never "open syllable type."
2. **Adopt the textbook's teaching sequence.** If the packet shows: sound model → syllable → word → sentence, follow that progression. Do not rearrange or substitute your own.
3. **Include specific examples from the packet.** If the textbook uses «ка-ша», «мо-ло-ко» to teach syllable division, use those same words (and add more). Authentic examples beat invented ones.
4. **Your pre-training is contaminated by Russian and English linguistics.** When the packet contradicts your instinct, the packet wins. Ukrainian has its own phonetic categories (голосний/приголосний, дзвінкий/глухий, м'який/твердий) that do not map 1:1 to English or Russian. Use the Ukrainian categories.
5. **Before submitting, verify:** For every linguistic term you used, check — does it appear in the knowledge packet or plan? If you used a term that's NOT in the packet (e.g., "CVCCV", "onset", "coda"), replace it with the Ukrainian equivalent from the packet.

<knowledge_packet>
# Verified Knowledge Packet: Віддієслівні іменники
**Module:** verbal-nouns | **Phase:** B1.3 [Verbs]
**Textbook grades searched:** 1, 2, 3, 5

---

## Що таке віддієслівні іменники?

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 109
> **Score:** 0.50
>
> Навчаюся розпізнавати іменники, які називають  
> ознаки і дії
> 	
>   Складіть і запишіть речення із трьома утвореними іменниками 
> (на вибір).
> Іменники можуть утворюватися від прикметників і називати 
> ознаки: блакить, краса. Іменники можуть утворюватися 
> від дієслів і називати дії: зустріч, плавання.
> сміливий — сміливість
> мужній — мужність 
> радіти — радість
> читати — читання
> Досліди, яке сло-
> во з пари слів є 
> іменником.
> Я — дослідник
> Я — дослідниця
> молодий
> молодість
> гра
> гравець
> грає
> швидкий
> ?
> ?
> ?
> бігає
> чемний
> ?
> ?
> ?
> читає
> щирий
> ?
> ?
> ?
> співає
> Який?  
> Що?  
> Що  
> робить?  
> Що?  
> Хто?  
> 	 	
> 19   Доберіть спільнокореневі іменники до прикметників і дієслів. 
> Запишіть їх. 
> 	 	
> 20   Поєднай частини приказок і запиши їх. Підкресли іменники.
> 109
> 18   Прочитай пари слів і порівняй їх.

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 116
> **Score:** 0.33
>
> 116
> Досліди, чи всі іменни-
> ки можуть мати фор-
> му однини і множини.
> Я — дослідник
> Я — дослідниця
> Спостерігаю за іменниками, які вживаються тільки  
> в однині або тільки у множині
> 6   Прочитай слова і порівняй їх. 
> 	
>   Визначте число виділених іменників. Зробіть висновок, у якій 
> числовій формі вживаються ці іменники.
> дружба
> птаство
> дітвора
> сани
> окуляри
> двері
> Поясни, що спільне є між цими словами, а що — відмінне.
> Чи можна утворити форму множини від іменників у лівому 
> стовпчику?
> Чи можна утворити форму однини від іменників у правому 
> стовпчику?
> Зроби висновок про особливості вживання деяких іменників.
> Деякі іменники можуть уживатися тільки в однині: 
> дитинство, листя, молодь.
> Деякі іменники можуть уживатися тільки у множині: 
> радощі, іменини, ворота.
> 	 	
> 7   Прочитайте.

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 146
> **Score:** 0.25
>
> 146
> Зв’язок дієслова з іменником 
> Навчаюся встановлювати зв’язок дієслова  
> з іменником у реченні
> 46
> 1   Прочитай і порівняй. До яких частин мови належать виділені слова?
> Приліт птахів.
> Що називають виділені слова?
> На які питання вони відповідають?
> До якої частини мови вони  
> належать?
> Птахи прилітають.
> Досліди, як відріз-
> нити дієслово від 
> іменника.
> Я — дослідник
> Я — дослідниця
> Дієслова в реченні зв’язані з іменниками.
> 	 	
> 2   Прочитайте текст. Доберіть до нього заголовок. 
> Швидко настає вечір у густому лісі. 
> Темні тіні лягають під деревами. По-
> чорніли густі ялини. Сіло за деревами 
> вечірнє сонце. У лісі запахло смолою і 
> сосновою глицею.
> Ще не сплять усі птахи. Ось на стовбурі дерева сидить 
> дятел. Навколо нього крутяться прудкі синиці.

## Суфікс -ння (-ання, -яння) — найпродуктивніший

> **Source:** ponomarova, Grade 3
> **Section:** Сторінка 55
> **Score:** 0.25
>
> 55
> 2. Спиши повідомлення Читалочки. Підкресли службові
> слова.  Знайди слова  з  префіксами  й  познач  їх.
> Префікс — це частина слова. Його пишемо разом
> зі словом.
> Службові слова пишемо окремо від інших слів.
> У Кам’янці-Подільському побудований найви-
> щий міст в Україні — «Стрімка лань». З мосту
> безстрашні сміливці стрибають на канатах униз.
> 4. Скористайся порадою Ґаджика і запиши сполучення слів 
> без дужок.
> Між службовим і наступним словом можна встави-
> ти ще одне слово. Наприклад: за дерево — за високе
> дерево; без хліба — без чорного хліба.
> 3. Ґаджик  хоче  навчити  тебе  розрізняти  префікси  і  служ-
> бові  слова.  Прочитай  його  пораду.
> (за) писати (на) дошці 
>       (в) ходити (в) будинок
> (до) нести (до) дверей 
>       (за) ховатись (за) штору
> 5.

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 65
> **Score:** 0.33
>
> 65
> Частини основи — префікс, корінь, суфікс —  на письмі 
> позначаються так: 
> підводн ий  .
> 	 	
> 3   Запишіть слова, позначте за-
> кінчення та основу. 
> Вода, водний, підводний.
> Лікарня, вечірній, прихід, баранчик, 
> житловий, жартівник, премудрий,  прадід.
> Живе один батько, 
> тисячі синів має,
> усім шапки справляє,
> а сам не має.
> 	
>   У словах відгадки визнач закінчення та основу.
> 	
>   Склади і запиши з цими словами речення.
> 4   Запиши слова, познач у них закінчення та 
> основу. 
> Визнач спільну частину основи у записаних  словах.  
> Це — корінь.
> Визнач частину основи перед коренем. Це — префікс.
> Визнач частину основи між коренем і закінченням.

## Суфікс -ття та безафіксний спосіб

## Віддієслівні іменники у реченні

> **Source:** vashulenko, Grade 2
> **Section:** Сторінка 104
> **Score:** 0.50
>
> НАВЧАЮСЯ РОЗПІЗНАВАТИ РЕЧЕННЯ 
> ЗА ЙОГО ОСНОВНИМИ ОЗНАКАМИ
> Я — учителька
> Прочитай і розкажи 
> ; у класі.
> 1
> розпізнаЮ 
> складаю
> Я — учитель
> РЄчєння виражає закінчену думку.
> Слова в реченні зв'язані між собою за змістом.
> і[ Прочитай текст. Кінець кожного 
> речення позначай зниженням 
> голосу і паузою. Полічи кількість 
> речень.
> Щодня ти ходиш до школи. 
> У школі тебе навчають учителі. 
> Вони хочуть, щоб діти вчилися 
> з цікавістю. Твій обов’язок —
> добре вчитися.
> • Запиши друге речення. Поясни думку, висловлену в цьому 
> реченні.
> 2| Поєднайте в речення сполучення слів обох колонок. 
> Запишіть утворені речення.
> На уроці математики 
> Учні записали 
> Учителька пояснювала
> у зошит умову задачі. 
> способи читання прикладів. 
> учні розв’язували приклади.
> 104^

## Практика: від дієслова до іменника

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 109
> **Score:** 0.50
>
> Навчаюся розпізнавати іменники, які називають  
> ознаки і дії
> 	
>   Складіть і запишіть речення із трьома утвореними іменниками 
> (на вибір).
> Іменники можуть утворюватися від прикметників і називати 
> ознаки: блакить, краса. Іменники можуть утворюватися 
> від дієслів і називати дії: зустріч, плавання.
> сміливий — сміливість
> мужній — мужність 
> радіти — радість
> читати — читання
> Досліди, яке сло-
> во з пари слів є 
> іменником.
> Я — дослідник
> Я — дослідниця
> молодий
> молодість
> гра
> гравець
> грає
> швидкий
> ?
> ?
> ?
> бігає
> чемний
> ?
> ?
> ?
> читає
> щирий
> ?
> ?
> ?
> співає
> Який?  
> Що?  
> Що  
> робить?  
> Що?  
> Хто?  
> 	 	
> 19   Доберіть спільнокореневі іменники до прикметників і дієслів. 
> Запишіть їх. 
> 	 	
> 20   Поєднай частини приказок і запиши їх. Підкресли іменники.
> 109
> 18   Прочитай пари слів і порівняй їх.

> **Source:** kravcova, Grade 2
> **Section:** Сторінка 87
> **Score:** 0.33
>
> 87
> 312. Утвори прислів’я. 
> 313. 1.	 Вибери навчальний предмет. 
> 2.	 Напиши чотири дієслова, які означають навчальні дії.
> 314. До поданих іменників добери дієслова за зразком та 
> запиши утворені пари.
> 315. 1.	 Прочитай прислів’я та поясни їх зміст.
> Не говори, що знаєш, але знай, що говориш. Сказав, як 
> сокирою одрубав. Що вимовиш язиком, то не витягнеш і волом.
> 2.	 Спиши. Підкресли дієслова.
> 2 учиться — 4 пригодиться. 3 завжди 1 Потрібно
> Зразок. Радість — радіти.
> радість	
> 	
> 	
> сум	 	
> 	
> тривога
> співчуття	 	
> 	
> жаль		
> 	
> обурення
> гордість	 	
> 	
> повага	
> 	
> заздрість
> 316. 1.	 Прочитай вірш.

> **Source:** vashulenko, Grade 2
> **Section:** Сторінка 80
> **Score:** 0.50
>
> НАВЧАЮСЯ СКЛАДАТИ РЕЧЕННЯ 
> З ДІЄСЛОВАМИ
> Прочитайте речення. Простежте, 
> які різні дії означає слово іде.
> складаю
> Іде катер. Іде поїзд. Іде зима. Іде час. Іде концерт.
> • Замініть у кожному реченні слово іде дієсловом, близьким 
> за значенням. Скористайтеся довідкою. Запишіть речення
> за зразком.
> Іде катер. 
> Пливе катер.
> ? годинник
> Довідка
> Відбувається, їде, минає, пливе, настає.
> б| Розглянь малюнки. Напиши, хто як пересувається,
> використавши дієслова з довідки.
> На які питання 
> відповідають 
> дієслова?
> Дові

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Що таке віддієслівні іменники?` (~550 words)
- `## Суфікс -ння (-ання, -яння) — найпродуктивніший` (~700 words)
- `## Суфікс -ття та безафіксний спосіб` (~650 words)
- `## Віддієслівні іменники у реченні` (~600 words)
- `## Практика: від дієслова до іменника` (~550 words)
- `## Читання: віддієслівні іменники у новинах` (~600 words)
- `## Підсумок та перехід до M22` (~350 words)
- `## Підсумок` (~150 words)

Each section should follow the word budget specified. The total must reach 4000 words minimum.

---

## Content Rules

Full Ukrainian immersion. Grammar explained IN Ukrainian. English only for disambiguation of false friends. Sentences max 30 words.

GRAMMAR RULES:
- Max 30 words per Ukrainian sentence
- Max 4 clauses per sentence
- All grammar constructions allowed
- Participles allowed
- Complex subordinate clauses allowed

### Pedagogy
- Start each section with a real situation or dialogue (PPP: Present → Practice → Produce)
- Every grammar rule needs 3+ Ukrainian examples with English translations
- Teach through PATTERNS, not rules: show examples first, then name the pattern
- Cultural context where relevant — this is Ukrainian, not generic L2
- Use vocabulary from the plan's vocabulary_hints. Function words (pronouns, conjunctions) are always allowed.

### Ukrainian Language Quality
- **Zero Russian**: No ы, э, ё, ъ. No Russian words (кот→кіт, хорошо→добре, конечно→звичайно)
- **Zero Surzhyk**: No шо→що, чо→чому, тіпа→типу
- **Zero calques**: No приймати душ→брати душ, приймати рішення→ухвалювати рішення
- **Zero paronyms**: тактична≠тактовна, ефектний≠ефективний — use the right word, not a similar-sounding one
- **Natural Ukrainian**: Write how a Ukrainian teacher would explain this to a student. Not robotic, not textbook-dry, not overly casual.

**Authority hierarchy (if uncertain about a word, check in this order):**
VESUM (does word exist?) → Правопис 2019 (spelling) → Горох (stress) → Антоненко-Давидович (style) → Грінченко (etymology).

**Online fallbacks:** VESUM: vesum.com.ua | Правопис: 2019.pravopys.net | Горох: goroh.pp.ua | Антоненко-Давидович: ukrlib.com.ua/books/printit.php?tid=4002 | Грінченко: hrinchenko.com | Словник.ua: slovnyk.me

### Writing Quality
- Every paragraph: ONE clear point, logical flow to the next
- Vary sentence length (short for emphasis, medium for explanation, long for examples)
- Use callout boxes (:::tip, :::caution, :::note) — at least 3 per module (mnemonics, common mistakes, cultural notes). Space them throughout the module, not clustered.
- **Dialogue formatting** — use blockquote `>` with speaker names in bold. Each turn on its own line. At A1 level, add English translation in italics after each line so learners understand what is being said. At A2, translate only new vocabulary. At B1+, no dialogue translations. Example:

> **Оленка:** Привіт! Як справи? *(Hi! How are you?)*
> **Тарас:** Добре, дякую! А у тебе? *(Good, thanks! And you?)*
> **Оленка:** Теж добре! *(Also good!)*

Without speaker names, the reader cannot tell who is speaking. NEVER use anonymous em dashes (`— text`). After each dialogue, briefly explain the key phrases and patterns the learner just saw.
- **Dialogues must sound like real people talking.** Test: would two Ukrainians actually say this to each other? If the dialogue sounds like a textbook drill ("Це кінь? — Так, це кінь."), rewrite it. Good dialogues have context, reactions, and personality:

  BAD (interrogation): "Це сім'я? — Так, це сім'я. — А де м'ясо? — М'ясо там."
  GOOD (natural): "Це твоя сім'я на фото? — Так! Нас п'ять. — А що ви їсте? М'ясо? — Так, дуже смачне!"

  BAD (labeling objects): "Це дуб. — А там коза. — Ні, це коса."
  GOOD (real reaction): "Дивись, який великий дуб! — Так, старий. А під ним — коза! — Смішна коза."

  Use the knowledge packet's textbook excerpts for dialogue patterns. Adapt real situations, don't invent drills.
- **DIALOGUE VARIETY — CRITICAL.** Each module MUST have DIFFERENT dialogue situations from other modules. Before writing any dialogue, check: have previous modules used this setting? If yes, pick a different one.

  BANNED recurring settings (already used in M01-M09): describing a room (кімната), looking at a table/bed/lamp, generic greetings with no context, labeling objects.

  REQUIRED: Every dialogue must have a SPECIFIC REAL-WORLD SITUATION that motivates the grammar being taught. The situation must be different from all other modules.

  **Module-specific dialogue settings (from plan):**
  1. **At a Ukrainian IT company — discussing project processes: Тестування (n, testing) триватиме два дні. Після написання (n, writing) коду — перевірка. Навчання (n, training) нових працівників — наш пріоритет. Читання (n, reading) документації обов'язкове.**
     Speakers: Менеджер проєкту, Розробник (developer)
     Why: Verbal nouns: тестування, написання, навчання, читання — -ння/-ття formations

  Use these settings. Do NOT substitute with a room description or generic greeting.
- **Tone: direct, clear, no filler.** State facts and teach. Don't praise the language ("beautiful", "wonderful", "unique melody"), don't praise the learner ("great job", "you've mastered"), don't narrate what you're doing ("In this section we will", "Now let's look at"). Just teach. Example:

  BAD: "The Ukrainian language has a wonderfully consistent and beautiful phonetic system."
  GOOD: "Ukrainian spelling is highly phonetic — what you see is what you hear."
- **Never guess about Ukrainian.** If you are unsure about a word, grammatical form, or phonetic rule — flag it with `<!-- VERIFY: word/claim -->`. Never invent or describe vaguely to hide uncertainty.

### Forbidden Tropes

If you write any of these patterns, the module will be rejected in review:

- **The Cheerleader:** "Great job!", "Don't worry, it's easy!", "You're doing amazing!", "Good news!" — respect the learner's intelligence; stay professional.
- **The Announcer:** "In this section, we will explore...", "Now let's dive into...", "Let's take a look at...", "To summarize what we learned..." — never use formulaic transitions. Just teach the concept directly.
- **The Translator:** "The Ukrainian word for 'cat' is 'кіт'." — instead, present naturally: "A domestic cat is a **кіт**."
- **The Wall of Text:** 3+ paragraphs of English theory without a single Ukrainian example — every concept must be anchored in immediate Ukrainian examples.
- **The Filler:** "This is a very important concept that you will use frequently in your daily life." — empty sentences that add words but not meaning. Every sentence must teach something.



### Vocabulary

**Required:** віддієслівний іменник (verbal noun — noun derived from a verb), читання (reading — verbal noun from читати), бачення (vision, seeing — verbal noun from бачити), відкриття (discovery, opening — verbal noun from відкрити), навчання (learning, education — verbal noun from навчати), дослідження (research, study — verbal noun from досліджувати), знання (knowledge — verbal noun from знати), спілкування (communication — verbal noun from спілкуватися), створення (creation — verbal noun from створити), забуття (oblivion, forgetting — verbal noun from забути), пошук (search — zero-derivation from пошукати), підпис (signature — zero-derivation from підписати), суфіксальний (suffixal — word formation method), безафіксний (zero-derivation — word formation without affixes)
**Recommended:** становлення (formation, establishment — bookish), будівництво (construction — from будувати), виробництво (production, manufacturing), забезпечення (provision, ensuring), відновлення (restoration, renewal), мислення (thinking, thought process), приїзд (arrival — zero-derivation from приїхати), канцелярит (bureaucratese — overuse of nominal style), продуктивний (productive — in word formation sense), основа інфінітива (infinitive stem — base for formation)

### Pronunciation Videos

**Do NOT embed YouTube videos in your prose.** A downstream ENRICH tool automatically places pronunciation videos from the plan. If you embed `<YouTubeVideo>` components, they will be duplicated. Simply reference the videos' existence when relevant (e.g., "Watch the pronunciation video for this letter") but do NOT insert `<YouTubeVideo>` tags.

Available videos (for reference only — ENRICH handles placement):


---

### Style Reference (match this tone and structure)

Дієприкметники — це особлива форма дієслова, яка поєднує ознаки дієслова та прикметника. Вони відповідають на питання «який?» і змінюються за родами, числами та відмінками, як звичайні прикметники.

Порівняйте:
- **написаний лист** (a written letter) — пасивний дієприкметник
- **зігрітий чай** (warmed tea) — пасивний дієприкметник

:::tip
В українській мові активні дієприкметники теперішнього часу (на -учий/-ючий) вважаються стилістично небажаними. Замість «працюючий лікар» краще сказати «лікар, який працює».
:::

*Note: Grammar explained IN Ukrainian using Ukrainian linguistic terms. English appears only in parenthetical translations for disambiguation. Callout boxes in Ukrainian.*



---

## Skeleton — Follow This Structure Exactly

A detailed paragraph-level skeleton was generated for this module. You MUST follow it precisely:
- Write every paragraph listed, in the order listed
- Hit each paragraph's word budget (+-10%)
- Place exercises exactly where the skeleton says
- Use the specific examples named in the skeleton
- Do NOT skip paragraphs, reorder sections, or add unplanned content

The skeleton replaces Step 1 (Pacing Plan) — do NOT output a <pacing_plan> block. Start writing immediately from the first section.

<skeleton>
## Що таке віддієслівні іменники? (~600 words total)
- P1 (~130 words): Introduction to the concept of nominalization. Explain how verbs (actions) can be transformed into nouns (things). Use Vashulenko Grade 3 examples: "зустріч" from "зустріти" and "плавання" from "плавати". Contrast the question "Що робити?" (to read) with "Що?" (reading).
- P2 (~150 words): Pedagogical rationale for B1 learners. Explain that verbal nouns are the backbone of academic, scientific, and formal Ukrainian. Illustrate how shifting from "Ми досліджували це питання" (active) to "Наше дослідження цього питання" (nominalized) changes the tone from personal to professional.
- P3 (~140 words): Semantic distinction between process and result. Use "навчання" as a prime example: it describes both the act of learning (процес) and the educational system/result (результат). Provide another example with "відкриття" (the act of opening vs. a scientific discovery).
- Dialogue (~110 words): Setting: A Ukrainian IT company during a sprint planning session. A Project Manager and a Developer discuss tasks. Use nouns: "тестування" (testing), "написання" (writing), "навчання" (training), and "читання" (reading). 
- P4 (~70 words): Transition to the mechanics of word formation. Briefly list the two main paths: suffixal (-ння, -ття, -іння) and zero-derivation (безафіксний спосіб).

## Суфікс -ння (-ання, -іння) — найпродуктивніший (~770 words total)
- P1 (~150 words): The primary rule for formation: Infinitive stem + -ння. Provide examples based on first conjugation verbs: "читати" → "читання", "писати" → "писання", "малювати" → "малювання". Explain the "основа інфінітива" concept clearly.
- P2 (~160 words): Orthography and Phonetics. Focus on the gemination (подвоєння) of the letter 'н'. Explain that the suffix is actually -нн- plus the ending -я. Provide the phonetic transcription [читан':а] and [знан':а] to help B1 students internalize the long soft consonant sound.
- P3 (~180 words): Vowel variations based on verb conjugation classes. Class I verbs usually yield -ання (спостерігати → спостереження - wait, contrast with -ування). Focus on II conjugation verbs producing -іння: "говорити" → "говоріння", "ходити" → "ходіння". Explain the shift to -ення for verbs like "бачити" → "бачення" and "створити" → "створення".
- P4 (~140 words): Semantic nuances between -ання (process focus) and -ення (result focus). Use the pair "вивчання" (the ongoing process of studying) vs. "вивчення" (the mastered result/completed study). Reference Zabolotnyi Grade 7 on the bookish nature of these forms.
- Exercise: Match-up activity. Match 10 verbs to their derived -ння nouns. Items include: вивчати, готувати, мислити, розуміти, бачити, будувати, спілкуватися, знати, писати, створювати.

## Суфікс -ття та безафіксний спосіб (~720 words total)
- P1 (~170 words): Suffixal formation with -ття. Explain that this suffix is common for verbs where the stem ends in certain consonant clusters or monosyllabic roots. Examples: "відкрити" → "відкриття", "забути" → "забуття", "жити" → "життя", "здобути" → "здобуття".
- P2 (~180 words): Zero-derivation (безафіксний спосіб). Introduce the concept from Lytvinova Grade 6: forming a noun by removing the verb suffix and/or prefix. Examples: "пошукати" → "пошук", "підписати" → "підпис", "бігти" → "біг", "хід" (← ходити), "спів" (← співати).
- P3 (~160 words): Register and Stylistic differences. Explain that -ння/-ття forms sound formal, academic, or "bookish" (книжне забарвлення). Contrast them with zero-derivation forms which are neutral or colloquial. Example: "дослідження" (academic study) vs. "пошук" (everyday search).
- Exercise: Group-sort activity. Categorize 10 verbal nouns by formation type: Suffixal (-ння/-ття) vs. Zero-derivation. Items: відкриття, біг, навчання, підпис, крик, знання, хід, спілкування, спів, приїзд.
- P4 (~110 words): Contextual choice. Explain how a native speaker chooses between "розмова" (zero-derivation, neutral) and "спілкування" (suffixal, more abstract/formal) depending on whether they are chatting with a friend or discussing communication in a lecture.

## Віддієслівні іменники у реченні (~660 words total)
- P1 (~170 words): Syntactic flexibility. Explain that these nouns function like any other noun: they decline through 7 cases, take adjectives ("глибоке дослідження"), and can be subjects or objects. Mention usage after prepositions: "Після закінчення курсу..." or "Перед початком зустрічі...".
- P2 (~190 words): Case government transfer (керування). This is critical: transitive verbs that take the Accusative case ("досліджувати проблему" - Зн.) transform into nouns that take the Genitive case ("дослідження проблеми" - Р.). Provide 3 examples: "читати книгу" → "читання книги", "вивчати мову" → "вивчення мови", "будувати дім" → "будівництво дому".
- P3 (~180 words): Style warning: Avoiding "Kantselyaryt" (канцелярит). Advise against overusing -ння forms which make text heavy and bureaucratic. Contrast the "dead" sentence "Здійснення забезпечення виконання плану..." with the "living" verb-based "Забезпечити виконання плану". Reference Antonenko-Davydovych's advice: use nouns for concepts, but stick to verbs for actions.
- Exercise: Sentence-builder activity. Transform 6 verb-heavy sentences into nominal phrases. Example: "Ми довго вивчали цю тему" → "Тривале вивчення цієї теми...". Items focus on changing case from Accusative to Genitive.

## Практика: від дієслова до іменника (~600 words total)
- Exercise 1: Fill-in-the-blanks. 10 items. Form the correct verbal noun from the bracketed verb to complete the sentence. Contexts: business, technology, and daily life. Examples: (створити) → створення нових робочих місць; (відпочивати) → активне відпочивання.
- Exercise 2: Register Transformation. 8 items. Rephrase colloquial sentences into formal "news" style using verbal nouns. Example: "Він приїхав учора, і ми були раді" → "Його вчорашній приїзд нас порадував".
- Exercise 3: Register/Context Quiz. 8 items. Choose the most appropriate verbal noun for a given sentence based on register. Example: [крик / волання] — "У лісі було чути ____ дитини." vs "Це ____ про допомогу було почуте всіма." (nuancing neutral vs formal/emotive).

## Читання: віддієслівні іменники у новинах (~660 words total)
- Reading Text (~320 words): A simulated Ukrainian news article about "Цифровізація освіти в Україні" (Digitalization of Education in Ukraine). Use a high density of verbal nouns: будівництво (infrastructure), забезпечення (provision), відновлення (restoration), навчання (learning), впровадження (implementation), дослідження (research).
- P1 (~160 words): Linguistic analysis of the text. Walk the student through identifying 5-6 key nouns from the text and tracing them back to their source verbs (e.g., "відновлення" from "відновити"). 
- Exercise (~100 words): Comprehension and grammar tasks. 1) Find 3 nouns with -ння and 2 with -ття. 2) Identify the source verbs. 3) Replace "забезпечення шкіл" with a phrase using the verb "забезпечувати".
- P2 (~80 words): Creative Writing prompt. Ask the learner to write 4 sentences about a project in their city or their own study progress using at least 3 verbal nouns from the module.

## Підсумок (~400 words)
- P1 (~180 words): Comprehensive recap. Summarize that verbal nouns describe an action as an object. Recall the main suffixes (-ння, -ття, -іння) and the importance of gemination (подвоєння). Remind the learner about the register gap between -ння forms and zero-derivation nouns like "біг" or "пошук".
- Self-check (~140 words):
  - Q: Як утворити іменник від дієслова "читати"?
  - A: Читання (основа чита- + -ння).
  - Q: Який відмінок зазвичай вживається після віддієслівного іменника?
  - A: Родовий відмінок (Genitive): вивчення (чого?) мови.
  - Q: Чим відрізняються "спілкування" та "розмова"?
  - A: "Спілкування" — офіційне/книжне; "розмова" — нейтральне/розмовне.
  - Q: Чи є подвоєння у слові "знання"?
  - A: Так, усі іменники на -ння мають подвоєння [н':].
- P2 (~80 words): Transition to M22. Introduce the next topic: Reflexive verbs (-ся/-сь). Explain that just as we can turn verbs into nouns, we can change a verb's direction toward the subject (мити → митися).

Grand total: ~4410 words
</skeleton>

## Output Format

Write in Markdown. Use:
- `## Section Title` for main sections
- `### Subsection` for subsections within a section
- `**bold**` for Ukrainian words being taught — EVERY bold Ukrainian word MUST have an English translation on first use, either in parentheses `**слово** (translation)` or inline `**слово** means "translation"`. No exceptions.
- Tables for paradigms (conjugation, declension)
- `:::tip` / `:::caution` / `:::note` for callout boxes
- `<!-- INJECT_ACTIVITY: {id} -->` for exercise placement (markers only — do NOT write exercise content)

Do NOT write MDX component syntax, JSON, or DSL exercise blocks (:::quiz, etc.). Plain Markdown with injection markers.

Begin writing now. Start with the first section heading.
