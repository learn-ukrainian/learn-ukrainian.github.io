<correction_directive>
CRITICAL: Your previous attempt failed the following checks. Write the module FROM SCRATCH. All original constraints still apply.

- FIX: Missing section heading: 'Підсумок: таблиця дієслівних чергувань'
- NOTE: Missing 2/14 required vocab: задньоязиковий (velar — consonant formed at back of mouth: г, к, х), палаталізація (palatalization — softening of consonant)
- NOTE: Plan expects 6 exercise(s) but content has 0 placeholders
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

Write the full prose content for module **10: Чергування приголосних (дієслова)** (B1, B1.2 [Morphophonemics & Noun Subclasses]).

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
module: b1-010
level: B1
sequence: 10
slug: alternation-consonants-verbs
version: '3.0'
title: "Чергування приголосних (дієслова)"
subtitle: "Сидіти — сиджу, плакати — плачу: приголосні в дієсловах"
focus: grammar
pedagogy: PPP
phase: "B1.2 [Morphophonemics & Noun Subclasses]"
word_target: 4000
objectives:
- "Learner can predict and produce consonant alternations in
  the 1st person singular (я-form) of II дієвідміна verbs:
  [д]->[дж], [т]->[ч], [з]->[ж], [с]->[ш], [ст]->[шч(щ)]
  (водити — воджу, крутити — кручу, носити — ношу)"
- "Learner can predict consonant alternations when forming
  imperfective verbs with suffixes -ати/-увати:
  зарядити — заряджати, погасити — погашати"
- "Learner can produce the губний + [л] alternation in
  1st person singular: робити — роблю, купити — куплю,
  ловити — ловлю"
- "Learner can conjugate common II дієвідміна verbs correctly
  across all persons, recognizing that alternation occurs ONLY
  in the 1st person singular"
dialogue_situations:
- setting: 'Cooking competition on Ukrainian TV — the host narrates actions with consonant
    changes: Я ходжу (д→дж) по кухні. Він просить (с→с), але: прошу (с→ш). Вона возить
    (з→з), але: я вожу (з→ж).'
  speakers:
  - Ведучий (host)
  - Учасники змагання
  motivation: 'Consonant alternation in verbs: ходити→ходжу, просити→прошу, возити→вожу'
content_outline:
- section: "Від іменників до дієслів"
  words: 500
  points:
  - "Bridge from M09 (alternation-consonants-nouns): the same
    consonants [г/к/х] that alternate in nouns also alternate in verbs,
    but the triggers are different. In nouns: case endings.
    In verbs: conjugation (especially 1st person singular).
    Заболотний Grade 7 p.52: 'Закономірними для української мови
    стали чергування приголосних звуків, що відбулися перед
    давнім суфіксом j.'"
  - "Why the 1st person singular? Historically, the -у/-ю ending
    of the 1st person contained a [й] sound that triggered
    palatalization of the preceding consonant. This is why
    the alternation appears ONLY in я-forms, not in ти-, він-forms.
    Modern result: сидіти — сиджу (я), сидиш (ти), сидить (він)."
  - "Overview of the three alternation groups in this module:
    1. Задньоязикові: [г]->[ж], [к]->[ч], [х]->[ш] (same as nouns)
    2. Зубні/свистячі: [д]->[дж], [т]->[ч], [з]->[ж], [с]->[ш]
    3. Губні + [л]: [б]->[бл], [п]->[пл], [в]->[вл], [м]->[мл], [ф]->[фл]"
- section: "Чергування зубних i свистячих: [д]->[дж], [т]->[ч], [з]->[ж], [с]->[ш]"
  words: 800
  points:
  - "From Глазова Grade 10 p.107:
    [д] -> [дж]: водити — воджу, сидіти — сиджу, ходити — ходжу,
    родити — роджу, будити — буджу, садити — саджу.
    [т] -> [ч]: крутити — кручу, летіти — лечу, світити — свічу,
    платити — плачу (note: плакати — плачу is [к]->[ч], different!).
    [з] -> [ж]: возити — вожу, морозити — морожу, гасити — гашу.
    [с] -> [ш]: носити — ношу, просити — прошу, косити — кошу,
    місити — мішу."
  - "Compound alternations:
    [зд] -> [ждж]: їздити — їжджу, бороздити — борожджу.
    [ст] -> [шч] (written as щ): мостити — мощу, простити — прощу,
    чистити — чищу, пустити — пущу.
    These are regular extensions of the basic alternations."
  - "Practice conjugation: learners conjugate 8-10 common verbs
    in теперішній час, all persons. Key insight: the alternation
    ONLY affects я-form. Compare:
    я воджу, ти водиш, він водить, ми водимо, ви водите, вони водять.
    Pattern: alternation in 1st sg., base consonant everywhere else."
  - "Common errors: mixing up [д]->[дж] with [д]->[ж] (the correct
    alternation is [д]->[дж] with the affricate, not simple [ж]).
    Writing *сижу instead of сиджу. The дж is one sound, one letter
    combination."
- section: "Чергування задньоязикових у дієсловах: [г]->[ж], [к]->[ч], [х]->[ш]"
  words: 600
  points:
  - "Same consonants as in nouns, same targets:
    [к] -> [ч]: плакати — плачу, тикати — тичу, пекти — печу.
    [г] -> [ж]: могти — можу, берегти — бережу, стригти — стрижу.
    [х] -> [ш]: колихати — колишу, махати — машу.
    These verbs belong to I дієвідміна (unlike the зубні group above)."
  - "Comparison with noun alternations from M09:
    Noun: друг -> друже (кличний) — same [г]->[ж].
    Verb: берегти -> бережу (1st sg.) — same [г]->[ж].
    The consonant change is identical; only the trigger differs
    (case ending vs. verb person ending)."
  - "Practice: learners identify whether a given alternation
    ([г]->[ж], [к]->[ч]) comes from a noun or verb context,
    reinforcing the shared phonological system."
- section: "Чергування губних + [л]: робити — роблю"
  words: 600
  points:
  - "From Заболотний Grade 7 p.52:
    [б] -> [бл']: робити — роблю, любити — люблю, губити — гублю.
    [п] -> [пл']: ліпити — ліплю, купити — куплю, сипати — сиплю.
    [в] -> [вл']: ловити — ловлю, ставити — ставлю, правити — правлю.
    [м] -> [мл']: дрімати — дрімлю, ломити — ломлю.
    [ф] -> [фл']: графити — графлю (rare)."
  - "This alternation is unique: instead of replacing the consonant,
    it INSERTS [л'] after the губний. The labial consonant stays,
    but gains a lateral partner. This is why it only affects
    1st person singular — the historical [й] caused [л'] insertion."
  - "Practice: learners conjugate common verbs with губні stems
    across all persons, confirming that [л'] appears only in я-form:
    я ловлю, ти ловиш, він ловить, ми ловимо..."
- section: "Чергування при утворенні недоконаних дієслів"
  words: 550
  points:
  - "From Глазова Grade 10 p.107:
    When forming imperfective verbs with -ати/-увати from perfective
    stems, the same alternations apply:
    [д] -> [дж]: зарядити — заряджати, засудити — засуджувати.
    [з] -> [ж]: знизити — знижати, знижувати.
    [с] -> [ш]: погасити — погашати, погашувати.
    [т] -> [ч]: скоротити — скорочувати, збагатити — збагачувати."
  - "Why this matters for word formation:
    When learners encounter an unfamiliar imperfective verb with
    [ж], [ч], [ш], or [дж] in the root, they can reconstruct the
    perfective stem: прощати <- простити ([ст]->[шч(щ)]).
    This is a powerful decoding strategy for reading."
  - "Practice: given perfective verbs, learners form the imperfective
    with -ати/-увати, applying the correct consonant alternation."
- section: "Повна парадигма: від інфінітива до всіх форм"
  words: 550
  points:
  - "Bringing it all together: complete conjugation of representative
    verbs showing where alternation does and does not occur.
    водити: воджу, водиш, водить, водимо, водите, водять;
    водив, водила, водило, водили; водитиму; водь! водіть!
    Alternation ONLY in теперішній час, 1st person singular."
  - "Contrast with наказовий спосіб (imperative):
    No consonant alternation in imperatives: носи! просіть! сидь!
    (not *нош!, *прош!, *сидж!). This confirms the alternation
    is specific to the 1-st person present/future context."
  - "Decision flowchart for learners:
    1. Is the verb II дієвідміна? -> check for [д/т/з/с/б/п/в/м]
    2. Is it 1st person singular? -> apply alternation
    3. Is it any other form? -> use the base consonant
    4. Are you forming imperfective with -ати/-увати? -> apply alternation"
- section: "Підсумок: таблиця дієслівних чергувань"
  words: 400
  points:
  - "Complete reference table:
    | Base | Alternation | Examples |
    | [д] | [дж] | водити-воджу, сидіти-сиджу |
    | [т] | [ч] | крутити-кручу, летіти-лечу |
    | [з] | [ж] | возити-вожу, морозити-морожу |
    | [с] | [ш] | носити-ношу, просити-прошу |
    | [зд]| [ждж]| їздити-їжджу |
    | [ст]| [шч(щ)]| простити-прощу, чистити-чищу |
    | [б] | [бл'] | робити-роблю, любити-люблю |
    | [п] | [пл'] | купити-куплю, ліпити-ліплю |
    | [в] | [вл'] | ловити-ловлю, ставити-ставлю |
    | [м] | [мл'] | ломити-ломлю |"
  - "Self-check: Дайте відповіді на запитання:
    1. Яке чергування відбувається у формі 'я сиджу'?
    2. Чому в дієслові 'роблю' з'являється звук [л']?
    3. Провідмінюйте дієслово 'просити' в теперішньому часі.
    4. Утворіть недоконаний вид: простити, зарядити, знизити."
  - "Preview: Спрощення приголосних (M11) — when consonant clusters
    simplify by dropping a sound entirely."
vocabulary_hints:
  required:
  - "чергування (alternation — systematic sound change)"
  - "дієслово (verb)"
  - "дієвідміна (conjugation class — verb classification)"
  - "особа (grammatical person — я/ти/він)"
  - "теперішній час (present tense)"
  - "інфінітив (infinitive — base verb form)"
  - "зубний (dental — consonant formed at the teeth: д, т)"
  - "свистячий (sibilant — whistling consonant: з, с, ц, дз)"
  - "губний (labial — consonant formed with lips: б, п, в, м, ф)"
  - "задньоязиковий (velar — consonant formed at back of mouth: г, к, х)"
  - "доконаний вид (perfective aspect)"
  - "недоконаний вид (imperfective aspect)"
  - "парадигма (paradigm — full set of inflected forms)"
  - "палаталізація (palatalization — softening of consonant)"
  recommended:
  - "африката (affricate — compound sound: дж, дз)"
  - "наказовий спосіб (imperative mood)"
  - "провідмінювати (to conjugate/decline through all forms)"
  - "основа (stem — word minus its ending)"
  - "суфікс (suffix)"
  - "словотворення (word formation)"
  - "продуктивний (productive — applicable to new words)"
  - "вимова (pronunciation)"
  - "закономірність (regularity — systematic pattern)"
activity_hints:
- type: fill-in
  focus: "Write the correct 1st person singular form of II дієвідміна
    verbs (e.g., сидіти -> я сидж___, носити -> я нош___)"
  items: 10
- type: quiz
  focus: "Identify which alternation type applies to a given verb:
    зубний, задньоязиковий, or губний + [л]"
  items: 8
- type: match-up
  focus: "Match infinitive forms with their 1st person singular
    (e.g., водити <-> воджу, купити <-> куплю)"
  items: 10
- type: group-sort
  focus: "Sort verbs by alternation type: [д]->[дж], [т]->[ч],
    [з]->[ж], [с]->[ш], губний+[л]"
  items: 10
- type: fill-in
  focus: "Form imperfective verbs with -ати/-увати from perfective
    stems (e.g., простити -> прощ___ти, знизити -> знижув___ти)"
  items: 6
- type: error-correction
  focus: "Find and fix conjugation errors in sentences
    (e.g., *я сижу -> я сиджу, *я робю -> я роблю)"
  items: 6
connects_to:
- "b1-009 (alternation-consonants-nouns — same consonants, noun context)"
- "b1-008 (alternation-vowels — vowel alternations in verb roots)"
- "b1-011 (simplification-consonants — consonant cluster simplification)"
prerequisites:
- "A2 completion (learner can conjugate basic verbs in present tense)"
- "b1-009 (alternation-consonants-nouns — first/second palatalization concept)"
grammar:
- "Зубні/свистячі alternations: [д]->[дж], [т]->[ч], [з]->[ж], [с]->[ш]"
- "Compound alternations: [зд]->[ждж], [ст]->[шч(щ)]"
- "Задньоязикові alternations in verbs: [г]->[ж], [к]->[ч], [х]->[ш]"
- "Губні + [л'] insertion: [б]->[бл'], [п]->[пл'], [в]->[вл'], [м]->[мл']"
- "Alternation in imperfective formation with -ати/-увати"
- "Alternation scope: 1st person singular only in conjugation"
register: академічний
references:
- title: "Глазова Grade 10, p.107"
  notes: "Complete table of verb consonant alternations: зубні,
    задньоязикові, compound groups with examples."
- title: "Заболотний Grade 7, p.52"
  notes: "Historical explanation: alternations before давній суфікс j,
    full list including губні + [л'] insertion."
- title: "Авраменко Grade 5, p.114-115"
  notes: "Чергування приголосних звуків: exercises with verb forms
    in прислів'я context."
- title: "Заболотний Grade 5, p.116-119"
  notes: "Чергування приголосних (section 28): systematic presentation
    with cross-references to чергування голосних."

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
- Confirmed: [чергування, дієслово, дієвідміна, особа, теперішній, час, інфінітив, зубний, свистячий, губний, задньоязиковий, доконаний, вид, недоконаний, парадигма, палаталізація, африката, наказовий, спосіб, провідмінювати, основа, суфікс, словотворення, продуктивний, вимова, закономірність]
- Not found: [None - all individual words and terms confirmed]

## Textbook Excerpts
### Section: Від іменників до дієслів
> Закономірними для української мови стали чергування приголосних звуків, що відбулися перед давнім суфіксом j: [д] — [дж], [т] — [ч], [з] — [ж], [с] — [ш], а також [к] — [ч], [х] — [ш], [г] — [ж], [ст] — [шч](щ) в основах дієслів.
> Source: Karaman, Grade 10

### Section: Чергування зубних i свистячих
> В особових формах дієслів теперішнього і майбутнього часу чергуються приголосні: [д] — [дж] (водити — воджу), [т] — [ч] (крутити — кручу), [з] — [ж] (возити — вожу), [с] — [ш] (носити — ношу).
> Source: Glazova, Grade 10

### Section: Чергування задньоязикових у дієсловах
> [г] — [ж]: берегти – бережу; [к] — [ч]: пекти – печу; [х] — [ш]: колихати – колишу.
> Source: Zabolotnyi, Grade 5

### Section: Чергування губних + [л]: робити — роблю
> [б] — [бл], [п] — [пл], [в] — [вл], [м] — [мл], [ф] — [фл]: робити — роблю, ліпити — ліплю, ловити — ловлю, відломити — відломлю, графити — графлю.
> Source: Karaman, Grade 10

### Section: Чергування при утворенні недоконаних дієслів
> У неозначеній формі дієслів перед суфіксами -ати-, -увати- чергуються: [д] — [дж] (зарядити — заряджати), [з] — [ж] (знизити — знижати, знижувати), [с] — [ш] (погасити — погашати).
> Source: Glazova, Grade 10

## Grammar Rules
- [Чергування зубних та свистячих]: Правопис §16 — Відбувається у першій особі однини дієслів теперішнього часу й майбутнього часу доконаного виду та в пасивних дієприкметниках перед суфіксом -ен-.
- [Чергування губних]: Правопис §17 — Звук Л у названих звукосполученнях м’який: у першій особі однини та третій особі множини теперішнього часу і майбутнього часу доконаного виду.

## Calque Warnings
- наказовий спосіб: OK — Antoniuko-Davydovych confirms usage for 1st person plural (читаймо) vs Russian descriptive constructions.
- теперішній час: OK — Antoniuko-Davydovych discusses "зараз/тепер" nuances but confirms the term.

## CEFR Check
- чергування: B2 — OK (Linguistic metalanguage for B1 module title)
- дієвідміна: B2 — OK (Core grammar term for B1)
- словотворення: B1 — OK
- парадигма: Not in PULS — OK (Academic term)
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
# Verified Knowledge Packet: Чергування приголосних (дієслова)
**Module:** alternation-consonants-verbs | **Phase:** B1.2 [Morphophonemics & Noun Subclasses]
**Textbook grades searched:** 1, 2, 3, 5

---

## Від іменників до дієслів

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 123
> **Score:** 0.50
>
> 123
> Фонетика. Графіка. Орфоепія. Орфографія.  Приголосні дзвінкі та глухі
> Звуки [в], [м], [н], [л], [р], відповідні їм м’які приголосні та  звук 
> [й] не належать ні до дзвінких, ні до глухих.  У цих звуках голос 
> переважає над шумом.  Їх називають сонорними (запам’ятати їх 
> можна у  слові ­МіНеРаЛоВиЙ).
> Через особливості вимови звуки [з], [ц], [с], [дз] називають 
> свистячими (бо їх звучання схоже на  свист), а  [ж], [ч], [ш], [дж] 
> шиплячими (бо їх вимовляємо шипінням).  Окремо виділяють 
> губні звуки [б], [п], [в], [м], [ф].

## Чергування зубних i свистячих: [д]->[дж], [т]->[ч], [з]->[ж], [с]->[ш]

> **Source:** kravtsova, Grade 3
> **Section:** Сторінка 8
> **Score:** 0.50
>
> 8
> ПРАВИЛЬНА ВИМОВА СЛІВ 
> ЗІ ЗВУКАМИ [ДЗ], [ДЗ´], [ДЖ]
> 15.
> 1.	 Утворіть пари слів: що робити? — що роблю?
> Сидіти — 		
> 	
> Будити —	 	
> Радити — 	
> Ходити — 		
> 	
> Водити — 	 	
> Садити —
> Зразок. Їздити — їжджу.
> 2.	 Пригадайте, як переносити слова зі звуками [дз], [дз[ ,]׳дж].
> 	
> 	
> поса-джені	 	
> за-дзвенів
> 	
> 	
> посадже-ні	 	
> задзве-нів
> 3.	 Запишіть утворені слова, поділивши їх для переносу. Пере-
> вірте роботу одні в одних. 
> 16.
> 1.	 Прочитай і відгадай загадку. 
> Живим зерном народжений, 
> живу я на землі. 
> Щодня рум’яним сонечком 
> я сходжу на столі.
> 2.	 Як ти розумієш словосполучення рум’яним сонечком?
> 3.	 Виконай завдання на вибір.
> 	 Спиши загадку. Підкресли слова, у яких звуків менше, ніж букв. 
> 	 Випиши виділені слова, поділивши їх для переносу різними 
> способами.

> **Source:** vashulenko, Grade 2
> **Section:** Сторінка 24
> **Score:** 0.25
>
> НАВЧАЮСЯ ПРАВИЛЬНО ПЕРЕНОСИТИ СЛОВА
> Пригадай і розкажи 
> у класі.
> 1
> ДЗ
> ДЖ
> вихо-джу 
> по-дзвонив
> Я — учитель
> Звуки [дж], [дз], [дз'] позначаються на письмі 
> буквосполученнями дж, дз. Під час переносу слів 
> буквосполучення дж, дз розривати не можна.
> Придумайте мелодію і проспівайте пісню. 
> Ходжу, ходжу по садочку, 
> по зеленім барвіночку.
> Ходжу, ходжу та й думаю, 
> як на світі жити маю.
> ходжу 
> приходжу 
> переходжу 
> заходжу
> ■_____ _____ л
> • Запишіть і поділіть для переносу слова.
> 8| Відгадай загадку. Випиши слова з 
> дз і поділи їх для переносу.
> Він мелодію зіграє, 
> як будильник продзвенить.

## Чергування задньоязикових у дієсловах: [г]->[ж], [к]->[ч], [х]->[ш]

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 34
> **Score:** 0.25
>
> 34
> 11
> Види речень за метою  
> висловлювання та інтонацією
> Розпізнаю види речень за метою висловлювання  
> та інтонацією
> Пригадай, які є види речень. Поєднай правильно. 
> Кожен народ плекає свою рідну мову.
> Чи добре ти володієш  
> українською мовою?
>  Ніколи не цурайся рідного слова.
> спонукати, закликати
> повідомити, розповісти
> запитати
> Плекати — дбайливо доглядати, піклуватися. 
> Цуратися — триматися осторонь, уникати, від-
> мовлятися.
> Чуєш, друже мій, розмови?
> З вітром листя гомонить,
> з сонцем — ниви і діброви,
> із озерами — блакить.
> Розмовляють доли, води…
> Стань, послухай, роздивись.
> Мову рідної природи
> розуміти серцем вчись.
> 1   Прочитай виразно вірш Оксани Сенатович.
>   Знайди в тексті розповідні, питальні і спонукальні речення.

## Чергування губних + [л]: робити — роблю

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 87
> **Score:** 0.50
>
> 8   Утворіть і запишіть слова за допомогою префіксів роз-, без-.
> 	 	
> 9   Відгадай слова і запиши їх. 
> безділля
> за
> велике
> праця
> краща
> маленька
> 	 	
>   Випиши з тексту слова із префіксами. Познач їх.
> 	 	
>   Розкажи, якою ти уявляєш зиму з цього тексту.
> 	 	
>   Склади і запиши речення з утвореними 
> словами.
> —	 Я так люблю зиму! Мені подобається …
> —	 А мені зовсім не подобається, коли зима …
> Продовжте розмову.
> Хвилинка спілкування
> мова
> гадка
> нести
> бити
> казати
> хмарний
> водний
> рідний
> ділля
> соння
> роз-
> без-
>  Префікс від слова безхмарний,
>  корінь від слова перелісок, 
>  закінчення від слова білий.
> Префікс від слова безсоння, 
> корінь від слова крило, 
> закінчення від слова тихий.
> Префікс від слова розмова, 
> корінь від слова дума, 
> закінчення від слова сад.
> Прочитай  
> приховане 
> прислів’я.

## Чергування при утворенні недоконаних дієслів

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
> Довідка
> Повзає, літає, плаває, стрибає, бігає.
> Хвилинка спілкування
> і
> — Як ти думаєш, як правильно сказати: 
> собака прибіг чи собака прибігла?
> — Я думаю, що можна вживати обидва 
> речення.
> — Давай перевіримо за словником. 
> Продовжте розмову.

> **Source:** avramenko, Grade 5
> **Section:** Сторінка 115
> **Score:** 0.33
>
> 115
>  § 50.  Чергування  приголосних  звуків
> 3. Прочитайте вислови та виконайте завдання.
> 1. Що на (думка), те й на (язик). 2. Терпи, (козак), отаманом будеш. 
> 3. Живемо, як горох при (дорога): хто не йде, той скубне. 4. Не шукай гри-
> бів у ведмежому (барліг). 5. Коли не знаєш дороги, не (виїхати) із дому 
> (Нар. тв.). 
> А. Перепишіть речення, ставлячи в потрібну форму слова, що в дужках. 
> Б. Підкресліть букви, що позначають звуки, які чергуються.

## Повна парадигма: від інфінітива до всіх форм

> **Source:** bolshakova, Grade 2
> **Section:** Сторінка 87
> **Score:** 0.25
>
> 87
> Поясни значення слів. Що в них спільне? Чи можна їх назвати 
> словами-родичами? А спільнокореневими чи спорідненими?
> сад
> садити
> садовий
> садівник
> ліс
> пролісок
> лісний
> лісник
>  
> Визнач корінь у словах. Чому ці слова споріднені? Запиши їх. 
> Склади речення з трьома словами на вибір.
> Дуб, дубок, дубовий листок, 
> дубняк (ліс).
> Вишня, вишенька, вишневий 
> листок, вишник (сад).
>  
> Вилучи «зайве» слово. Спиши. Познач корінь.
> 1. Риба, рибка, рибалка, рити, рибалити, риб’ячий.
> 2. Вода, водичка, водити, водний.
> 3. Сніг, сніжок, сніп, сніговий, снігур, сніговик.
>  
> Інструкція 
> Інструкція — це вказівки, як виконувати що-небудь.
> • Установи послідовність дій.

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 276
> **Score:** 0.50
>
> 276
> Складні випадки наголошування
> СКЛАДНІ ВИПАДКИ НАГОЛОШУВАННЯ
> А
> алфаві т
> аркушик
> Б
> багаторазо вий
> бе шкет
> близьки й
> болоти стий
> боро давка
> босо ніж
> боя знь
> бурштино вий
> В
> вантажі вка
> весня ни й
> ви года (користь)
> виго да (зручність)
> видання
> вимо га
> ви падок
> виразний
> ви сіти
> виши ваний
> відвезти 
> відвести 
> ві дгомін
> віднести 
> ві рші
> віршови й
> Г
> гальмо , гальма
> глядач
> гороши на
> граблі 
> Д
> дано
> де щиця
> джерело 
> дичавіти
> добу ток
> довезти 
> довести 
> дові дник
> донести 
> до нька
> дочка
> дро ва
> Е
> експе рт
> Ж
> жалюзі 
> З
> завдання
> завезти 
> завести 
> завжди 
> завчасу 
> загадка
> закінчи ти
> закладка (у книзі)
> залиши ти
> занести 
> застібка
> зви сока

## Підсумок: таблиця дієслівних чергувань

> **Source:** bolshakova, Grade 2
> **Section:** Сторінка 66
> **Score:** 0.25
>
> 66
> При переносі слова з рядка в рядок не розривай букво- 
>  сполучення дж, дз, які позначають один звук [дж], [дз], [д

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Від іменників до дієслів` (~500 words)
- `## Чергування зубних i свистячих: [д]->[дж], [т]->[ч], [з]->[ж], [с]->[ш]` (~800 words)
- `## Чергування задньоязикових у дієсловах: [г]->[ж], [к]->[ч], [х]->[ш]` (~600 words)
- `## Чергування губних + [л]: робити — роблю` (~600 words)
- `## Чергування при утворенні недоконаних дієслів` (~550 words)
- `## Повна парадигма: від інфінітива до всіх форм` (~550 words)
- `## Підсумок: таблиця дієслівних чергувань` (~400 words)
- `## Підсумок — Summary` (~150 words)

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
  1. **Cooking competition on Ukrainian TV — the host narrates actions with consonant changes: Я ходжу (д→дж) по кухні. Він просить (с→с), але: прошу (с→ш). Вона возить (з→з), але: я вожу (з→ж).**
     Speakers: Ведучий (host), Учасники змагання
     Why: Consonant alternation in verbs: ходити→ходжу, просити→прошу, возити→вожу

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

**Required:** чергування (alternation — systematic sound change), дієслово (verb), дієвідміна (conjugation class — verb classification), особа (grammatical person — я/ти/він), теперішній час (present tense), інфінітив (infinitive — base verb form), зубний (dental — consonant formed at the teeth: д, т), свистячий (sibilant — whistling consonant: з, с, ц, дз), губний (labial — consonant formed with lips: б, п, в, м, ф), задньоязиковий (velar — consonant formed at back of mouth: г, к, х), доконаний вид (perfective aspect), недоконаний вид (imperfective aspect), парадигма (paradigm — full set of inflected forms), палаталізація (palatalization — softening of consonant)
**Recommended:** африката (affricate — compound sound: дж, дз), наказовий спосіб (imperative mood), провідмінювати (to conjugate/decline through all forms), основа (stem — word minus its ending), суфікс (suffix), словотворення (word formation), продуктивний (productive — applicable to new words), вимова (pronunciation), закономірність (regularity — systematic pattern)

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
## Від іменників до дієслів (~550 words total)
- P1 (~110 words): [Transition from M09 (Nouns) to Verbs. Explain that while the consonant targets [г/к/х] are the same, the context is entirely different. Nouns alternate due to case endings (друг — друже), whereas verbs alternate due to conjugation, primarily the 1st person singular (я). Introduce the term "чергування приголосних у дієсловах".]
- P2 (~130 words): [Historical context based on Zabolotnyi Grade 7. Explain the "Yod" ([j]) suffix that existed in Old East Slavic verb endings for the 1st person singular. This invisible trigger caused the palatalization of the preceding consonant. This explains why the change is restricted to the "я" form and doesn't spread to "ти" or "він" forms in Modern Ukrainian.]
- Dialogue (~120 words): [Cooking competition setting. Ведучий (host) narrates: "Я ходжу (д→дж) між столами і бачу, як ви працюєте. Я прошу (с→ш) вас бути уважними. Кожен робить (б) свій шедевр, але я люблю (б→бл) лише гострі страви!" Motivation: show alternations in natural speech.]
- P3 (~100 words): [Classification overview. Introduce the three primary groups we will study: 1. Dental/Sibilants (зубні/свистячі), 2. Velars (задньоязикові), and 3. Labials with inserted 'л' (губні + л). Mention that Group 1 is the most common in II-conjugation.]
- P4 (~90 words): [Importance of this module for B1 learners. Explain that these alternations are productive and regular; mastering them prevents "robotic" or incorrect speech (like saying *я сижу* or *я робю*) and helps in recognizing root meanings across different verb forms.]

## Чергування зубних i свистячих: [д]->[дж], [т]->[ч], [з]->[ж], [с]->[ш] (~880 words total)
- P1 (~140 words): [Focus on the [д] -> [дж] alternation. Explain the importance of the affricate sound [дж] (not a simple [ж]). Examples: водити — воджу, сидіти — сиджу, ходити — ходжу, радити — раджу. Highlight the spelling rule: 'дж' is written with two letters but represents one sound.]
- P2 (~130 words): [Focus on the [т] -> [ч] alternation. Examples: крутити — кручу, летіти — лечу, світити — свічу, платити — плачу. Contrast this specifically with the [к]->[ч] alternation (плакати — плачу) to show that different stems can result in the same 'я' form.]
- P3 (~120 words): [Focus on sibilants: [з] -> [ж] and [с] -> [ш]. Examples: возити — вожу, морозити — морожу, гасити — гашу, просити — прошу, носити — ношу. Explain that these are very frequent in daily communication.]
- Exercise: [match-up, Match infinitive forms with their 1st person singular, 10 items. Includes: будити, косити, світити, возити, садити, крутити, летіти, просити, сидіти, ходити.]
- P4 (~140 words): [Compound alternations: [зд] -> [ждж] and [ст] -> [щ] (which is phonetic [шч]). Examples: їздити — їжджу, бороздити — борожджу, чистити — чищу, пустити — пущу, простити — прощу. Explain that 'щ' is a shorthand for the sh-ch alternation.]
- P5 (~110 words): [The "1st Person Only" rule. Contrast the 'я' form with the rest of the paradigm using 'водити'. Show that from 'ти' to 'вони', the base consonant [д] returns: я воджу, ти водиш, він водить... Highlight the visual break in the conjugation table.]
- Exercise: [fill-in, Write the correct 1st person singular form of II дієвідміна verbs, 10 items. Focus: [д/т/з/с/ст/зд] endings.]
- P6 (~120 words): [Common errors and Orthography. Warn against Russian influence (e.g., *сижу instead of сиджу). Explain that in Ukrainian, the distinction between [дж] and [ж] is phonemically significant for meaning and grammatical correctness.]

## Чергування задньоязикових у дієсловах: [г]->[ж], [к]->[ч], [х]->[ш] (~660 words total)
- P1 (~120 words): [Reviewing the velar triplets [г, к, х]. Explain that these alternations occur primarily in I-conjugation verbs (unlike the previous group). Mention that the targets [ж, ч, ш] are the same as in noun palatalization (M09).]
- P2 (~110 words): [The [к] -> [ч] alternation. Examples: пекти — печу, плакати — плачу, кликати — кличу, тикати — тичу. Explain how the infinitive stem helps identify the alternation pattern.]
- P3 (~110 words): [The [г] -> [ж] alternation. Examples: берегти — бережу, могти — можу, стригти — стрижу, застерегти — застережу. Note that 'можу' is one of the most common verbs in the language.]
- P4 (~100 words): [The [х] -> [ш] alternation. Examples: колихати — колишу, махати — машу, дихати — дишу (poetic/standard). Note that these are less common but follow the same logic as 'муха — мусі'.]
- Exercise: [group-sort, Sort verbs by alternation type: [г]->[ж], [к]->[ч], [х]->[ш], 10 items.]
- P5 (~130 words): [Comparison Table: Noun vs Verb context. Compare 'друг -> друже' and 'берег -> на березі' with 'берегти -> бережу'. Show that while the sounds are shared, the "trigger" for the learner's brain must switch from "Which case?" to "Which person?".]

## Чергування губних + [л]: робити — роблю (~660 words total)
- P1 (~130 words): [Introduction to Labials ([б, п, в, м, ф]). Explain that unlike other groups where a sound is replaced, here a sound is INSERTED. This is called "L-epenthesis" (епентетичне л). The labial consonant remains, but gains a lateral partner.]
- P2 (~120 words): [Focus on [б] -> [бл] and [п] -> [пл]. Examples: робити — роблю, любити — люблю, купити — куплю, ліпити — ліплю. Point out that this only happens in the 'я' form: я люблю — ти любиш.]
- P3 (~110 words): [Focus on [в] -> [вл] and [м] -> [мл]. Examples: ловити — ловлю, ставити — ставлю, дрімати — дрімлю, знайомити — знайомлю. Explain the phonetic ease of transitioning from a labial to a softened 'л'.]
- P4 (~90 words): [The rare [ф] -> [фл]. Example: графити — графлю (to rule/draw lines). Mention that while rare, it proves the rule that ALL labials trigger this insertion in the 1st person singular.]
- Exercise: [error-correction, Find and fix conjugation errors in sentences, 6 items. Focus: *я робю, *я купю, *я любу.]
- P5 (~110 words): [Visualizing the insertion. Use a diagram-like explanation: Stem [люб-] + Ending [-ю] -> [люб'ю] -> [люблю]. Explain that the 'л' acts as a buffer created by the historical 'yod'.]

## Чергування при утворенні недоконаних дієслів (~600 words total)
- P1 (~120 words): [Introduction to Aspectual Derivation. Explain that alternations don't just happen in conjugation; they are central to creating imperfective verbs from perfective ones using the suffixes -ати or -увати.]
- P2 (~140 words): [Systematic mapping of derivation alternations. Examples based on Glazova Grade 10: [д] -> [дж] (зарядити — заряджати, засудити — засуджувати), [т] -> [ч] (скоротити — скорочувати, збагатити — збагачувати).]
- P3 (~120 words): [Dealing with Sibilants in derivation: [з] -> [ж] (знизити — знижувати) and [с] -> [ш] (погасити — погашати). Contrast these with their conjugation counterparts to show the consistency of the phonological system.]
- Exercise: [fill-in, Form imperfective verbs with -ати/-увати from perfective stems, 6 items. Includes: простити, зарядити, скоротити, знизити, засудити, погасити.]
- P4 (~120 words): [Decoding Strategy for Reading. Teach learners how to "reverse" an alternation to find the root. If they see 'запрошувати', they should look for the dental [с] in the perfective root 'просити'. This builds lexical intuition.]

## Повна парадигма: від інфінітива до всіх форм (~600 words total)
- P1 (~150 words): [The Full Picture: Present Tense. Provide the complete conjugation table for 'водити' and 'любити'. Reinforce the "Alternation Island": 1st sg is changed, 2nd sg, 3rd sg, 1st pl, 2nd pl, and 3rd pl all use the base consonant stem.]
- P2 (~130 words): [Contrasting with the Imperative Mood (наказовий спосіб). Based on the plan, explain that imperatives do NOT trigger alternation: 'носи!', 'просіть!', 'сидь!'. Explain that the lack of the specific historical [j] trigger in imperatives means the consonant stays "hard" or base.]
- P3 (~120 words): [The Past Tense check. Show that 'водив', 'водила', 'водили' keep the base consonant. Explain that alternation is a feature of the PRESENT/FUTURE system (and derivation), not the past tense.]
- P4 (~100 words): [The "Decision Flowchart" for the learner: 1. Is it a verb? 2. Is it 1st person singular or an imperfective derivative? 3. Identify the stem-final consonant. 4. Apply the corresponding group rule.]
- Exercise: [quiz, Identify which alternation type applies to a given verb or if it occurs in a specific form, 8 items.]

## Підсумок — Summary (~410 words total)
- P1 (~260 words): [Complete Reference Table. Provide a clear, clean Markdown table summarizing: Base sound, Alternation sound, and Examples (водити-воджу, летіти-лечу, возити-вожу, носити-ношу, їздити-їжджу, простити-прощу, робити-роблю, купити-куплю, ловити-ловлю, дрімати-дрімлю). This serves as the "cheat sheet" for the module.]
- P2 (~150 words): [Self-check Questions & Answers based on the plan:
    1. Яке чергування відбувається у формі 'я сиджу'? (Відповідь: [д] -> [дж]).
    2. Чому в дієслові 'роблю' з'являється звук [л']? (Відповідь: Через губний приголосний [б] перед давнім суфіксом).
    3. Провідмінюйте дієслово 'просити' в теперішньому часі. (я прошу, ти просиш, він просить...).
    4. Утворіть недоконаний вид: простити (прощати), зарядити (заряджати), знизити (знижувати).]

Grand total: ~4360 words
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
