<correction_directive>
CRITICAL: Your previous attempt failed the following checks. Write the module FROM SCRATCH. All original constraints still apply.

- FIX: Missing section heading: 'Підсумок: таблиця чергувань'
- NOTE: Missing 3/14 required vocab: тверда група (hard group — nouns with hard stem-final consonant), м'яка група (soft group — nouns with soft stem-final consonant), мішана група (mixed group — nouns with шиплячий stem-final)
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

Write the full prose content for module **5: Чергування приголосних (іменники)** (B1, B1.1 [Baselines & Morphophonemics]).

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
10. **EVERY module MUST end with `## Підсумок — Summary`** — this is the last H2 section before the file ends. It contains a self-check recap. If you forget this section, the audit REJECTS the module and you waste a retry. Write it LAST, after all other sections.

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
module: b1-005
level: B1
sequence: 5
slug: alternation-consonants-nouns
version: '3.0'
title: "Чергування приголосних (іменники)"
subtitle: "Друг — друже — друзі: як змінюються приголосні в іменниках"
focus: grammar
pedagogy: PPP
phase: "B1.1 [Baselines & Morphophonemics]"
word_target: 4000
objectives:
  - "Learner can predict and produce the first palatalization [г/к/х] -> [ж/ч/ш] in
    кличний відмінок and word formation (друг — друже, козак — козаче, пастух — пастуше)"
  - "Learner can predict and produce the second palatalization [г/к/х] -> [з'/ц'/с']
    in давальний and місцевий відмінки (нога — на нозі, рука — на руці, Ольга — Ользі)"
  - "Learner can identify which case or word-formation context triggers which alternation
    type (first vs. second palatalization)"
  - "Learner can apply consonant alternation rules to unfamiliar nouns and proper
    names, avoiding common errors in case forms"
dialogue_situations:
  - setting: 'At a Львівська книгарня (f, Lviv bookshop) — discussing authors and
      book titles, noticing consonant changes: книга→у книжці (г→ж), рука→у руці (к→ц),
      друг→друже (г→ж, vocative), вухо→у вусі (х→с).'
    speakers:
      - Книгар (bookseller)
      - Покупець
    motivation: 'Consonant alternation in nouns: г→ж, к→ц, х→с in locative and vocative'
content_outline:
  - section: "Що таке чергування приголосних?"
    words: 500
    points:
      - "Bridge from M08 (alternation-vowels): learners now understand that sounds
        change systematically in Ukrainian word forms. Vowel alternations affect the
        root vowel; consonant alternations affect the final consonant of the root
        or stem. Авраменко Grade 5 p.114: 'Найпоширенішими є такі чергування приголосних:
        [г] — [з] — [ж], [к] — [ц] — [ч], [х] — [с] — [ш].'"
      - "The three-way pattern: each задньоязиковий consonant [г], [к], [х] has TWO
        possible alternation targets depending on the phonetic environment. This module
        teaches learners to predict which one appears where. The system is regular
        and productive."
      - "Historical context (brief): these alternations trace back to давньоукраїнська
        мова and the effect of front vowels on back consonants. Understanding the
        history is optional but helps learners see the logic, not just memorize."
  - section: "Перша палаталізація: [г/к/х] -> [ж/ч/ш]"
    words: 750
    points:
      - "The pattern from Заболотний Grade 5 p.116 (section 28): [г] -> [ж]: друг
        — дружити, нога — ніжка, ворог — вороже [к] -> [ч]: рука — ручка, молоко —
        молочний, козак — козаче [х] -> [ш]: кожух — кожушок, вухо — вушко, пастух
        — пастуше This alternation appears in word formation (suffixes -к-, -н-) and
        in кличний відмінок."
      - "Кличний відмінок with first palatalization (Глазова Grade 10 p.209): друг
        — друже, козак — козаче, чоловік — чоловіче, хлопець — хлопче (also [ц'] ->
        [ч]), юнак — юначе, вітязь — вітязю (м'яка група — no alternation). Rule:
        II відміна, тверда група, закінчення -е triggers the alternation. М'яка група
        takes -ю with no alternation."
      - "Word formation with first palatalization: нога — ніжка — ніженька, рука —
        ручка — рученька, книга — книжка — книжковий, молоко — молочний — молочар.
        Adjective suffixes -н-, -ськ- also trigger it: Прага — празький, Норвегія
        — норвезький."
      - "Reading practice: Ukrainian folk sayings and прислів'я that use кличний відмінок
        naturally. Learners identify the alternation in each: 'Терпи, козаче, отаманом
        будеш' (козак -> козаче)."
  - section: "Друга палаталізація: [г/к/х] -> [з'/ц'/с']"
    words: 750
    points:
      - "The pattern from Авраменко Grade 5 p.114: [г] -> [з']: нога — на нозі, Ольга
        — Ользі, дорога — на дорозі [к] -> [ц']: рука — на руці, ріка — на ріці, дочка
        — дочці [х] -> [с']: муха — мусі, свекруха — свекрусі, стріха — на стрісі
        This alternation appears in давальний and місцевий однини of I відміна (feminine
        nouns ending in -а/-я)."
      - "Why давальний and місцевий? The endings -i trigger this alternation before
        them. Compare: нога: Н.в. нога, Р.в. ноги, Д.в. нозі, Зн.в. ногу, Ор.в. ногою,
        М.в. (на) нозі, Кл.в. ного! The alternation ONLY appears before -i in Д.в.
        and М.в."
      - "Proper names follow the same pattern: Ольга — Ользі, Палажка — Палажці, Одарка
        — Одарці. Geographic names: Прага — у Празі, Рига — у Ризі, Америка — в Америці
        (but: Африка — в Африці). Practice: learners decline proper names in давальний
        and місцевий."
      - "Common errors to avoid: Mixing up the two palatalizations: *на нозі is correct
        (second), but *на ножі would be wrong (that is first palatalization, wrong
        context). The кличний uses first ([ж/ч/ш]), while давальний/місцевий use second
        ([з'/ц'/с'])."
  - section: "Чергування [ц'] -> [ч] та інші"
    words: 500
    points:
      - "From Глазова Grade 10 p.209: хлопець — хлопче, швець — шевче, молодець —
        молодче. The soft [ц'] alternates with [ч] in кличний відмінок. This is a
        separate alternation from the [к]->[ч] pattern."
      - "Minor alternations in nouns: [с] -> [ш]: колесо — на колішні (rare, mostly
        in fixed forms) [з] -> [ж]: князь — княже (кличний відмінок) These are less
        productive but appear in common words."
      - "Practice: learners build a complete table of alternation types, contexts,
        and examples. The table becomes a reference for future modules on verb alternations
        (M10)."
  - section: "Чергування у відмінюванні іменників II відміни"
    words: 550
    points:
      - "Systematic view: how consonant alternations interact with the full declension
        paradigm of II відміна masculine nouns. Using друг as a model: Н.в. друг,
        Р.в. друга, Д.в. другу/другові, Зн.в. друга, Ор.в. другом, М.в. (на) другу/другові,
        Кл.в. друже. Only the кличний shows alternation in masculine nouns."
      - "Comparison with I відміна feminine nouns: нога: alternation in Д.в. (нозі)
        and М.в. (на нозі). This contrast helps learners predict WHERE to expect the
        change: masculine nouns — кличний; feminine nouns — давальний/місцевий."
      - "Литвінова Grade 6 p.159: закінчення іменників II відміни в кличному відмінку
        однини — systematic table of endings by group (тверда, м'яка, мішана) with
        alternation rules."
  - section: "Чергування у власних назвах і географічних іменах"
    words: 500
    points:
      - "Ukrainian place names and personal names follow the same rules: Прага — у
        Празі, Рига — у Ризі, Одарка — Одарці. But some foreign names resist alternation:
        Пенелопа — Пенелопі (no alternation — foreign name). Learners need to know
        which names follow Ukrainian patterns."
      - "Cultural context: кличний відмінок in everyday Ukrainian. Addressing people:
        Олеже! Марічко! Iгоре! Тарасе! Understanding alternation = correct forms of
        address. Common mistakes by L2 speakers: *Олего! (wrong — should be Олеже)."
      - "Practice: learners write short dialogues using кличний відмінок with proper
        names, applying the correct alternation."
  - section: "Підсумок: таблиця чергувань"
    words: 450
    points:
      - "Complete reference table: | Consonant | First (Кл.в., word formation) | Second
        (Д.в./М.в.) | | [г] | [ж] | [з'] | | [к] | [ч] | [ц'] | | [х] | [ш] | [с']
        | | [ц'] | [ч] (Кл.в. only) | — |"
      - "Self-check in Ukrainian: Дайте відповіді на запитання: 1. Які приголосні
        чергуються у кличному відмінку слова 'друг'? 2. Яке чергування відбувається
        у слові 'на нозі'? 3. Утворіть кличний відмінок: козак, юнак, хлопець. 4.
        Поставте у давальний відмінок: Ольга, книга, рука."
      - "Preview of next module: Чергування приголосних (дієслова) — the same consonants
        alternate in verb conjugation, but with different triggers and patterns."
vocabulary_hints:
  required:
    - "чергування (alternation — systematic sound change between forms)"
    - "приголосний (consonant — sound made with obstruction)"
    - "палаталізація (palatalization — softening of a consonant)"
    - "кличний відмінок (vocative case — used for direct address)"
    - "давальний відмінок (dative case)"
    - "місцевий відмінок (locative case)"
    - "задньоязиковий (velar — consonant formed at the back of the mouth)"
    - "відміна (declension class — noun classification by ending pattern)"
    - "тверда група (hard group — nouns with hard stem-final consonant)"
    - "м'яка група (soft group — nouns with soft stem-final consonant)"
    - "мішана група (mixed group — nouns with шиплячий stem-final)"
    - "закінчення (ending — inflectional morpheme)"
    - "звертання (form of address — using кличний відмінок)"
    - "корінь (root — core morpheme of a word)"
  recommended:
    - "шиплячий (hushing consonant — ж, ч, ш, дж)"
    - "свистячий (sibilant — з, ц, с, дз)"
    - "словотворення (word formation — creating new words from roots)"
    - "прислів'я (proverb — traditional folk saying)"
    - "орфограма (orthographic rule — spelling pattern)"
    - "спільнокореневий (cognate — sharing the same root)"
    - "однина (singular number)"
    - "множина (plural number)"
    - "продуктивний (productive — pattern applicable to new words)"
    - "непродуктивний (unproductive — pattern limited to existing words)"
activity_hints:
  - type: quiz
    focus: "Identify which palatalization type is present: first ([ж/ч/ш]) or second
      ([з'/ц'/с']), given a word pair (друг-друже vs. нога-нозі)"
    items: 8
  - type: fill-in
    focus: "Write the correct кличний відмінок form of masculine nouns (e.g., козак
      -> козач___, друг -> друж___)"
    items: 8
  - type: fill-in
    focus: "Write the correct давальний/місцевий form of feminine nouns (e.g., нога
      -> на ноз___, рука -> руц___)"
    items: 6
  - type: match-up
    focus: "Match base forms with their alternated case forms (e.g., Ольга <-> Ользі,
      козак <-> козаче)"
    items: 8
  - type: error-correction
    focus: "Find and fix consonant alternation errors in sentences (e.g., *на ножі
      -> на нозі, *козаже -> козаче)"
    items: 6
connects_to:
  - "b1-008 (alternation-vowels — vowel alternations as the first morphophonemic rule)"
  - "b1-010 (alternation-consonants-verbs — same consonants alternate in verbs)"
  - "b1-012 (noun-subclasses-masculine — declension of -ар/-яр/-ин nouns)"
prerequisites:
  - "A2 completion (learner knows noun declension basics, all 7 cases)"
  - "b1-001 (metalanguage-phonetics — приголосний classification)"
  - "b1-008 (alternation-vowels — concept of чергування)"
grammar:
  - "First palatalization: [г/к/х] -> [ж/ч/ш] in кличний and word formation"
  - "Second palatalization: [г/к/х] -> [з'/ц'/с'] in давальний/місцевий"
  - "Alternation [ц'] -> [ч] in кличний відмінок"
  - "Interaction of alternations with declension paradigms (I and II відміна)"
  - "Application to proper names and geographic names"
register: академічний
references:
  - title: "Авраменко Grade 5, p.114-115"
    notes: "Чергування приголосних звуків (section 50): three-way pattern [г]-[з]-[ж],
      [к]-[ц]-[ч], [х]-[с]-[ш] with examples and exercises."
  - title: "Заболотний Grade 5, p.116-119"
    notes: "Чергування приголосних звуків (section 28): systematic presentation with
      друг-друзі-дружити, молоко-молоці-молочний."
  - title: "Глазова Grade 10, p.209"
    notes: "Особливості кличного відмінка: complete table of consonant alternations
      before -е in кличний, including [ц']->[ч]."
  - title: "Литвінова Grade 6, p.159"
    notes: "Закінчення іменників II відміни в кличному відмінку однини: systematic
      by group (тверда, м'яка, мішана)."
  - title: "Авраменко Grade 10, p.175"
    notes: "Особливості кличного відмінка: dialogue-based presentation, Валеріє vs.
      Валерію gender distinction."

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
- Confirmed: чергування, приголосний, палаталізація, відмінок, група, закінчення, звертання, корінь, шиплячий, свистячий, словотворення, прислів'я, орфограма, спільнокореневий, однина, множина, продуктивний, непродуктивний, кличний, місцевий, давальний, мішаний, твердий, м'який.
- Not found: [None - all core terms and their components are confirmed.]

## Textbook Excerpts
### Section: Що таке чергування приголосних?
> "Найпоширенішими є такі чергування приголосних: [г] — [з] — [ж], [к] — [ц] — [ч], [х] — [с] — [ш]."
> Source: Авраменко, Grade 5, p. 114

### Section: Перша палаталізація: [г/к/х] -> [ж/ч/ш]
> "Чергування приголосних у кличному відмінку (г-ж, к-ч, х-ш: друг-друже, вовк-вовче) є наслідком праслов'янської першої палаталізації."
> Source: Глазова, Grade 10, §26

### Section: Друга палаталізація: [г/к/х] -> [з'/ц'/с']
> "Чергування приголосних у Дав. і Місц. відмінках (результат другої палаталізації): рука — руці, нога — нозі. Це жива норма сучасної української мови."
> Source: Глазова, Grade 10, §26

## Grammar Rules
- [Consonant Alternation in Nouns]: Правопис § 18 (Suffixal Changes) — Confirms changes like "козак — козацький" and "Прага — празький".
- [Verb Alternation Baseline]: Правопис § 16 — Confirms related alternations [т/ч], [з/ж], [с/ш] in verb forms, providing a system-wide context.
- [Vocative Case Rules]: Правопис § 87, § 91 (per general grammatical sources confirmed in grep) — Triggers [г/к/х] -> [ж/ч/ш] (друже, козаче, пастуше) and [ц'] -> [ч] (хлопче).

## Calque Warnings
- [чергування приголосних]: OK — Standard linguistic term.
- [кличний відмінок]: OK — Standard linguistic term (formerly dismissed as "form" in Soviet eras).
- [палаталізація]: OK — International linguistic term used in Ukrainian textbooks.

## CEFR Check
- чергування: B1 — Technical linguistic term for this level.
- приголосний: A1/A2 — Basic grammatical term.
- рука, нога, вухо: A1 — Core vocabulary used as mnemonic.
- Ольга, книга: A1 — Core nouns used as examples.
- кличний відмінок: B1 — Formal introduction of case name and systematic rules.
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
# Verified Knowledge Packet: Чергування приголосних (іменники)
**Module:** alternation-consonants-nouns | **Phase:** B1.1 [Baselines & Morphophonemics]
**Textbook grades searched:** 1, 2, 3, 5

---

## Що таке чергування приголосних?

*No textbook results found for: Що таке чергування приголосних задньоязиковий давньоукраїнська мова*

## Перша палаталізація: [г/к/х] -> [ж/ч/ш]

*No textbook results found for: Перша палаталізація Заболотний друг дружити нога ніжка ворог вороже рука ручка*

## Друга палаталізація: [г/к/х] -> [з'/ц'/с']

*No textbook results found for: Друга палаталізація з' ц' с' Авраменко нога на нозі Ольга Ользі дорога*

## Чергування [ц'] -> [ч] та інші

*No textbook results found for: Чергування ц' та інші Глазова хлопець хлопче швець шевче молодець молодче*

## Чергування у відмінюванні іменників II відміни

*No textbook results found for: Чергування у відмінюванні іменників відміни відміна друг друга другу другові Зн Ор нога*

## Чергування у власних назвах і географічних іменах

*No textbook results found for: Чергування у власних назвах і географічних іменах Прага у Празі Рига у Ризі Одарка Одарці Пенелопа Пенелопі кличний відмінок*

## Підсумок: таблиця чергувань

*No textbook results found for: Підсумок таблиця чергувань Кл з' ц' с' Дайте відповіді на запитання Які приголосні чергуються у кличному відмінку слова 'друг' Яке чергування відбувається у слові 'на нозі' Утворіть кличний відмінок*

## Grammar Reference

*No grammar results for: кличний з' ц' с' давальний місцевий кличний відмінок відміна*


## МійКлас Theory (miyklas.com.ua)

*Ukrainian school curriculum theory — use this terminology and teaching approach.*

### Приголосні м'які й тверді, дзвінкі й глухі
> **Source:** МійКлас — [Приголосні м'які й тверді, дзвінкі й глухі](https://www.miyklas.com.ua/p/ukrainska-mova/5-klas/fonetika-grafika-orfoepiia-orfografiia-14565/prigolosni-m-iaki-i-tverdi-dzvinki-i-glukhi-vimova-prigolosnikh-g-i-g-40885)

### Теорія:

*www.ua.pistacja.tv*  
Приголосні звуки – це звуки, що творяться за допомогою голосу й шуму або лише шуму. При їх вимові струмінь видихуваного повітря натрапляє на різні перепони органів мовлення \(язик, зуби, губи\), унаслідок чого виникають шуми, які є основою саме приголосних звуків.
Зверни увагу\!
Тверді і м’які приголосні — це різні звуки, для позначення яких на письмі використовують ті самі літери: \[лин\] лин – \[л'ін'\] лінь.
Напівпом'якшені звуки — це **відтінки **твердих звуків: \[в’інок\] вінок — \[виниекнути\] виникнути.
В українській мові є такі м’які приголосні: \[д'\], \[т'\], \[з'\], \[с'\], \[ц'\], \[л'\], \[н'\], \[дз'\], \[р'\].
 
Запам'ятати ці приголосні  можна, вивчивши таку фразу: «Де Ти З'їСи Ці ЛиНи, аДЗуР».

Звук \[й\] завжди м’який.

### Вимова приголосних звуків. Уподібнення приголосних
> **Source:** МійКлас — [Вимова приголосних звуків. Уподібнення приголосних](https://www.miyklas.com.ua/p/ukrainska-mova/5-klas/fonetika-grafika-orfoepiia-orfografiia-14565/vimova-prigolosnikh-zvukiv-upodibnennia-prigolosnikh-zvukiv-42793)

### Теорія:

*www.ua.pistacja.tv*  
Вимова приголосних звуків
Для української мови характерна  **виразна** вимова приголосних звуків, зокрема дзвінких. Вони завжди вимовляються **чітко**. Особливо в кінці складу та слова й перед голосними: стежка \[сте́жка\],  виріб \[ви́р'іб\], дружина \[дружи́на\]. Але бувають випадки, коли звуки важко відрізнити один від одного.
Що таке уподібнення приголосних і коли воно відбувається
У процесі мовлення один приголосний стає схожий за звучанням на інший, тобто зазнає впливу сусіднього звуку. Таке явище називається уподібненням.
Приклад:
Слово боротьба пишемо з літерою т \(боротися\), а вимовляємо й чуємо \[бород'ба́\], бо глухий \[т'\] уподібнився під впливом дзвінкого \[б\] до  \[д'\].
Зверни увагу\!
Сумнівний приголосний можна легко перевірити.

### Спрощення в групах приголосних
> **Source:** МійКлас — [Спрощення в групах приголосних](https://www.miyklas.com.ua/p/ukrainska-mova/5-klas/fonetika-grafika-orfoepiia-orfografiia-14565/sproshchennia-v-grupakh-prigolosnikh-41974)

### Теорія:

*www.ua.pistacja.tv*  
При вiдмiнюваннi слова або його твореннi інколи виникає важкий для вимови збiг приголосних звукiв. Тому в процесi мовлення один із таких приголосних випадає, тобто вiдбувається спрощення \(правило «третього зайвого»\). Зазвичай спрощені звуки не пишемо.
Спрощення приголосних відбувається в таких **групах** приголосних:
- \[ждн\], \[здн\] → \[жн\], \[зн\] \(випадає д\): проїздити – проїзний, тиждень – тижня;
  
- \[зкн\], \[скн\] → \[зн\], \[сн\] \(випадає к\): брязкіт — брязнути, тріск — тріснути, писк — писнути \(рідше — пискнути\);
  
- \[стл\], \[стн\] → \[сл\], \[сн\] \(випадає т\): щастя — щасливий, прихвостень — прихвосня, перстень — персня;
  
- \[рнц\] → \[нц\] \(випадає р\): чернець — ченці;
  
- \[рдц\] → \[рц\] \(випадає д\): сердець — серце;
...

---
**Total textbook excerpts found:** 1
**Grades searched:** 1, 2, 3, 5
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Що таке чергування приголосних?` (~500 words)
- `## Перша палаталізація: [г/к/х] -> [ж/ч/ш]` (~750 words)
- `## Друга палаталізація: [г/к/х] -> [з'/ц'/с']` (~750 words)
- `## Чергування [ц'] -> [ч] та інші` (~500 words)
- `## Чергування у відмінюванні іменників II відміни` (~550 words)
- `## Чергування у власних назвах і географічних іменах` (~500 words)
- `## Підсумок: таблиця чергувань` (~450 words)

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
  1. **At a Львівська книгарня (f, Lviv bookshop) — discussing authors and book titles, noticing consonant changes: книга→у книжці (г→ж), рука→у руці (к→ц), друг→друже (г→ж, vocative), вухо→у вусі (х→с).**
     Speakers: Книгар (bookseller), Покупець
     Why: Consonant alternation in nouns: г→ж, к→ц, х→с in locative and vocative

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

**Required:** чергування (alternation — systematic sound change between forms), приголосний (consonant — sound made with obstruction), палаталізація (palatalization — softening of a consonant), кличний відмінок (vocative case — used for direct address), давальний відмінок (dative case), місцевий відмінок (locative case), задньоязиковий (velar — consonant formed at the back of the mouth), відміна (declension class — noun classification by ending pattern), тверда група (hard group — nouns with hard stem-final consonant), м'яка група (soft group — nouns with soft stem-final consonant), мішана група (mixed group — nouns with шиплячий stem-final), закінчення (ending — inflectional morpheme), звертання (form of address — using кличний відмінок), корінь (root — core morpheme of a word)
**Recommended:** шиплячий (hushing consonant — ж, ч, ш, дж), свистячий (sibilant — з, ц, с, дз), словотворення (word formation — creating new words from roots), прислів'я (proverb — traditional folk saying), орфограма (orthographic rule — spelling pattern), спільнокореневий (cognate — sharing the same root), однина (singular number), множина (plural number), продуктивний (productive — pattern applicable to new words), непродуктивний (unproductive — pattern limited to existing words)

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
## Що таке чергування приголосних? (~550 words total)
- P1 (~150 words): [Establish a bridge from M08 (vowel alternations), explaining that while vowel changes often happen in the root, consonant alternations typically affect the final sound of the root/stem. Introduce the term 'чергування' as a systematic, predictable shift that occurs during declension or word formation.]
- P2 (~150 words): [Introduce the core "three-way pattern" defined in Avramenko Grade 5: the velar group (задньоязикові) [г], [к], [х] each have two potential alternation targets. Contrast the hard starting points with their soft or hushing results (г — з — ж, к — ц — ч, х — с — ш) to give learners a map of the entire module.]
- P3 (~150 words): [Explain the phonetic mechanism: why these sounds change. Discuss the role of historical "front vowels" (like the modern 'i' or the vocative 'e') in pulling the back-of-the-mouth velars forward, transforming them into sibilants or hushing sounds. Use the analogy of "lazy speech" or "tongue efficiency."]
- P4 (~100 words): [Briefly touch upon the historical context of Proto-Slavic and Old East Slavic (давньоукраїнська мова), explaining that these aren't "irregularities" but are the very fossils of the language's evolution that make Ukrainian melodic and easy to pronounce.]

## Перша палаталізація: [г/к/х] -> [ж/ч/ш] (~825 words total)
- P1 (~150 words): [Deep dive into the [г/к/х] -> [ж/ч/ш] pattern. Explain that this is triggered by the vocative ending -e and certain word-formation suffixes. Provide immediate primary examples: друг (base) -> друже (vocative), рука (base) -> ручка (diminutive).]
- P2 (~150 words): [Focus on the Vocative Case (кличний відмінок) for masculine nouns. Detail the rule from Glazova Grade 10: 2nd declension, hard group, ending in -e. List transformations: ворог — вороже, козак — козаче, пастух — пастуше, чоловік — чоловіче, юнак — юначе.]
- P3 (~150 words): [Discuss Word Formation (словотворення). Explain how suffixes like -к-, -н-, and -еньк- trigger the same shift. Provide examples: нога — ніжка — ніженька, рука — рученька, книга — книжка — книжковий, молоко — молочний.]
- P4 (~125 words): [Extend the rule to adjectives and place-name-based suffixes like -ськ-. Show how the hushing sound is often assimilated or preserved: Прага — празький, Норвегія — норвезький, Лейпциг — лейпцизький.]
- P5 (~150 words): [Reading Practice: Introduce authentic Ukrainian folk proverbs and sayings that utilize the vocative case naturally. Focus on "Терпи, козаче, отаманом будеш" and explain the kozak -> kozache shift in the context of historical address.]
- Exercise: [Fill-in, focus on writing the correct кличний відмінок form of masculine nouns (e.g., козак -> козаче, друг -> друже), 8 items] (~100 words in items/instructions)

## Друга палаталізація: [г/к/х] -> [з'/ц'/с'] (~925 words total)
- P1 (~150 words): [Introduce the second pattern: [г] -> [з'], [к] -> [ц'], [х] -> [с']. Emphasize that these are "soft" (палаталізовані) sounds, not hushing ones. Use Avramenko's examples: нога — на нозі, рука — на руці, муха — на мусі.]
- P2 (~150 words): [The Trigger: The ending -i. Explain that this alternation is strictly limited to the Dative and Locative singular cases of the 1st declension (mostly feminine nouns ending in -a). Contrast this with the Vocative trigger (-e) to help learners categorize the two types.]
- P3 (~150 words): [Case Comparison: Walk through a partial declension of 'нога' to show where the change *doesn't* happen (ноги, ногу, ногою) versus where it *does* (нозі, на нозі). This visualization reinforces that -i is the catalyst.]
- P4 (~150 words): [Proper Names: Apply the rule to names. Show how Olga becomes Olzi and Odarka becomes Odartsi. Explain that this is vital for correct syntax in sentences like "Я дав книжку Ользі" or "Ми були в гостях у Одарки."]
- P5 (~125 words): [Common Pitfalls: Warn against mixing the two palatalizations. Explain why "*на ножі" is a mistake for "on the leg" (it uses the 1st palatalization incorrectly) while "на нозі" is correct. Contrast "книжці" (locative) with "книже" (hypothetical vocative vs actual diminutive "книжка").]
- Exercise: [Quiz, focus on identifying which palatalization type is present: first or second, given a word pair (друг-друже vs. нога-нозі), 8 items] (~100 words)
- Exercise: [Fill-in, focus on writing the correct давальний/місцевий form of feminine nouns (e.g., нога -> на нозі, рука -> руці), 6 items] (~100 words)

## Чергування [ц'] -> [ч] та інші (~550 words total)
- P1 (~150 words): [Focus on the special alternation [ц'] -> [ч] in the Vocative case, as seen in Glazova Grade 10. List high-frequency examples: хлопець — хлопче, молодець — молодче, швець — шевче. Explain that the soft [ц'] of the stem yields to the hushing [ч] before the -e ending.]
- P2 (~150 words): [Address "Minor" but important alternations. Mention [з] -> [ж] in the Vocative: князь — княже. Briefly touch on [с] -> [ш] in rare forms like колесо — на колішні, clarifying that while less productive, these are essential for high-level literacy.]
- P3 (~150 words): [Systematic Synthesis: Combine all the bits into a "Master Logic." Explain how a learner can look at any noun ending in a velar or [ц'] and instantly predict its Vocative, Dative, and Locative forms based on the tables provided.]
- Exercise: [Match-up, focus on matching base forms with their alternated case forms (e.g., Ольга <-> Ользі, козак <-> козаче), 8 items] (~100 words)

## Чергування у відмінюванні іменників II відміни (~600 words total)
- P1 (~150 words): [Examine the 2nd Declension (masculine) paradigm as a whole. Use 'друг' as the model. Show that throughout the entire singular and plural declension, *only* the Vocative singular triggers the alternation. This simplifies the rule for masculine nouns.]
- P2 (~150 words): [Contrast with 1st Declension (feminine/mixed). Highlight that feminine nouns have a "Dative/Locative" pocket for alternations, whereas masculine nouns have a "Vocative" pocket. This contrast is the key to avoiding cross-gender errors.]
- P3 (~150 words): [Group Classification: Revisit the "Hard, Soft, Mixed" groups from Lytvynova Grade 6. Explain how 'тверда група' nouns are the primary candidates for these velar alternations, while 'м'яка група' (ending in -ю in Vocative) usually avoids them (e.g., вітязь — вітязю).]
- Exercise: [Error-correction, focus on finding and fixing consonant alternation errors in sentences (e.g., *на ножі -> на нозі, *козаже -> козаче), 6 items] (~150 words)

## Чергування у власних назвах і географічних іменах (~550 words total)
- P1 (~150 words): [Geography Focus: Practice with place names. Explain why we say "у Празі" (Prague), "у Ризі" (Riga), and "в Америці" (America). Note the exception for some foreign names like "Пенелопа — Пенелопі" where the sound remains unchanged to preserve the original name's phonetics.]
- P2 (~150 words): [Cultural Context - Forms of Address: Explain why correct alternation is a sign of respect and native-level fluency in Ukraine. Discuss the social awkwardness of using the nominative or an incorrect vocative (e.g., calling someone "*Олего" instead of "Олеже!").]
- P3 (~150 words): [Common Proper Names: Provide a reference list of common names that undergo change: Марічка — Марічці, Галинка — Галинці, Олег — Олеже, Ігор — Ігорю (contrast with no change).]
- Dialogue (~100 words): [At a Львівська книгарня (Lviv bookshop). A customer asks for a book ("книга") and the bookseller says it's in a specific "книжці" (г->ж). They discuss the author ("Ользі") and use the vocative "друже" to address each other politely.]

## Підсумок — Summary (~500 words)
- P1 (~100 words): [Recap the three-way velar pattern and the two main types of palatalization. Emphasize that [г/к/х] are the "unstable" sounds that love to shift when they meet the vowels -e or -i.]
- P2 (~100 words): [Complete Reference Table:
| Base Consonant | First Palatalization (Кл.в., word formation) | Second Palatalization (Д.в./М.в.) |
| :--- | :--- | :--- |
| [г] | [ж] (друже) | [з'] (нозі) |
| [к] | [ч] (козаче) | [ц'] (руці) |
| [х] | [ш] (пастуше) | [с'] (мусі) |
| [ц'] | [ч] (хлопче - Кл.в. only) | — |]
- P3 (~300 words): [Self-check Questions:
1. Які приголосні чергуються у кличному відмінку слова 'друг'? (г -> ж)
2. Яке чергування відбувається у слові 'на нозі' і чому? (г -> з', друга палаталізація перед -і в місцевому відмінку)
3. Утворіть кличний відмінок від слів: козак, юнак, хлопець. (козаче, юначе, хлопче)
4. Поставте у давальний відмінок: Ольга, книга, рука. (Ользі, книзі, руці)
5. Чому ми кажемо "у Празі", але "у Пенелопі"? (Географічні назви зазвичай чергуються, але деякі запозичені власні назви зберігають основу для впізнаваності.)]

Grand total: ~4500 words
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
