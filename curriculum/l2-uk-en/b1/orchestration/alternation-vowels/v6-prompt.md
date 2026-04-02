<correction_directive>
CRITICAL: Your previous attempt failed the following checks. Write the module FROM SCRATCH. All original constraints still apply.

- FIX: Missing section heading: 'Підсумок: правила i практика'
- FIX: Russian characters found: ё
- NOTE: Missing 2/14 required vocab: нуль звука (zero sound — absence of a vowel in an alternation), шиплячий (hushing consonant — ж, ч, ш, дж)
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

Write the full prose content for module **8: Чергування голосних** (B1, B1.2 [Morphophonemics & Noun Subclasses]).

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
module: b1-008
level: B1
sequence: 8
slug: alternation-vowels
version: '3.0'
title: "Чергування голосних"
subtitle: "Коли о та е стають i — і коли зникають зовсім"
focus: grammar
pedagogy: PPP
phase: "B1.2 [Morphophonemics & Noun Subclasses]"
word_target: 4000
objectives:
- "Learner can predict when [о] or [е] in a root will become [i]
  in a different word form, using the open/closed syllable rule
  (рік — року, сіль — солі, двір — двори)"
- "Learner can identify and produce the [о]/[е] to zero alternation
  in noun and adjective paradigms (учень — учня, вітер — вітру,
  день — дня)"
- "Learner can explain the connection between наголос shift
  and vowel alternation in verb pairs (летіти — літати,
  нести — ніс)"
- "Learner can apply these rules to spell unfamiliar words correctly,
  recognizing that the alternation is a defining feature of Ukrainian
  phonology that distinguishes it from other Slavic languages"
dialogue_situations:
- setting: 'A Ukrainian teacher explaining to students why certain words change their
    vowels — using examples from a grocery list: Я купив коня (m, horse), але: коні
    (pl). Вона живе в селі (n), але: село. Він поставив стіл (m), але: на столі.'
  speakers:
  - Вчитель
  - Студенти
  motivation: 'Vowel alternation о/е→і: кінь→коня, село→селі, стіл→столі'
content_outline:
- section: "Що таке чергування голосних?"
  words: 550
  points:
  - "Bridge from M01 (metalanguage-phonetics): learners already know
    голосний, приголосний, наголос, відкритий/закритий склад.
    This module shows how these concepts drive systematic spelling changes.
    Key definition from Авраменко Grade 5 p.111:
    'Iноді, коли утворюємо нове слово або його форму, звук може
    змінюватися на інший: сіль — соляний, солі; корінь — кореня.
    Це мовне явище називають чергуванням звуків.'"
  - "Why this matters: чергування голосних is a defining feature of
    Ukrainian that distinguishes it from Russian and Polish.
    Glazova Grade 10 p.103: 'Таке чергування характерне для
    української мови й вирізняє її серед інших східнослов'янських мов.'
    Learners who master this rule unlock correct spelling of thousands
    of Ukrainian words."
  - "Overview of the three main types covered in this module:
    1. [о], [е] чергуються з [i] (the open/closed syllable rule)
    2. [о], [е] чергуються з нулем звука (fleeting vowels)
    3. [о] чергується з [е] after шиплячі та [й]
    Each type has its own logic; this section previews all three."
- section: "Чергування [о], [е] з [i]"
  words: 900
  points:
  - "The core rule from Заболотний Grade 5 p.113-114:
    When a syllable changes from open to closed (or vice versa),
    [о] or [е] in the root may alternate with [i].
    Open syllable (ends in vowel): дво-ри, ко-ні, ро-ку.
    Closed syllable (ends in consonant): двір, кінь, рік.
    Pattern: [о]/[е] in open syllable <-> [i] in closed syllable."
  - "Systematic examples organized by part of speech:
    Nouns: стіл — столу, двір — двору, сіль — солі,
    віз — воза, ніс — носа, рік — року, річ — речі.
    Adjectives: осінній — осени, вечірній — вечора.
    Verbs: несті — ніс, везті — віз.
    Glazova Grade 10 p.103: 'шко-ла — шкіл; дво-ри — двір;
    по-со-ли — сіль; у мо[йе]му — у мо[йі]м.'"
  - "Exceptions and special cases:
    Not every closed syllable triggers the change.
    Borrowed words typically do not alternate: мотор — мотору
    (not *мотіру). Some native words have fossilized forms.
    Practice: learners predict the nominative from an oblique case form
    and vice versa."
  - "Reading practice: short passage using words with [о]/[е] ~ [i]
    alternation in natural context (e.g., describing a Ukrainian village:
    двір, стіл, піч, вікна, ріг, etc.). Learners identify all
    alternating pairs in the text."
- section: "Чергування [о], [е] з нулем звука"
  words: 650
  points:
  - "Definition from Заболотний Grade 5 p.114:
    In some words, [о] or [е] disappears entirely when the word form
    changes. This is called 'чергування з нулем звука' or 'біглі
    голосні'. The vowel is present in one form but absent in another."
  - "Common patterns:
    Masculine nouns: учень — учня, день — дня, вітер — вітру,
    камінь — каменя, хлопець — хлопця, пень — пня.
    The vowel [е] or [о] in the last syllable of the nominative
    disappears in oblique cases when the ending is added.
    Suffixes: -ець/-ця (молодець — молодця),
    -ок/-ка (замок — замка, гурток — гуртка),
    -ень/-ня (корінь — кореня)."
  - "How to recognize fleeting vowels vs. stable vowels:
    If removing the vowel creates an impossible consonant cluster,
    the vowel may be stable (but not always — Ukrainian tolerates
    clusters like -дня, -тру). Practice with minimal pairs:
    сон — сну (fleeting) vs. стон — стону (stable)."
- section: "Чергування [о] з [е] після шиплячих та [й]"
  words: 550
  points:
  - "Rule from Заболотний Grade 7 p.56:
    After [ж], [ч], [ш], [дж], [й]:
    — write е before м'який приголосний or before syllables with [е], [и]:
    вечеря, вишень, джерело, женити.
    — write о before твердий приголосний or before syllables with [а], [о], [у]:
    бджола, будиночок, пшоно, знайомий."
  - "Exceptions to memorize: чепурний, шепіт, жебоніти, щедрий,
    черствий, чекати (е despite the rule), and чоло, бджола (о despite
    the rule). These are listed explicitly in Заболотний Grade 7 p.56."
  - "Practice: learners apply the rule to fill in missing letters
    in words after шиплячі. Contrast with Russian where this distinction
    does not exist — Ukrainian learners must develop sensitivity to
    the following consonant's hardness/softness."
- section: "Чергування голосних у дієслівних коренях"
  words: 550
  points:
  - "From Заболотний Grade 5 p.113, вправа 275:
    Verb root alternations driven by stress and suffix:
    летіти — літати, котити — катати, терти — стирати.
    Pattern: [е] ~ [i] ~ [и] depending on stress position and
    suffix (-а-, -и-, -іти-)."
  - "Extended examples from Заболотний Grade 5 p.114, вправа 276:
    захопити — хапати ([о] ~ [а]),
    сплести — сплітати ([е] ~ [i]),
    завмерти — завмирати ([е] ~ [и]),
    заберу — забирати ([е] ~ [и]).
    The alternation is predictable: before stressed -а- suffix,
    the root vowel changes."
  - "Connecting to A2 knowledge: learners already know these verbs
    from everyday use. Now they see the system. This transforms
    memorized pairs into a productive rule."
- section: "Чергування i наголос: як вони пов'язані"
  words: 500
  points:
  - "Key insight: наголос (stress) drives many vowel alternations.
    When stress shifts away from a root vowel, the vowel may change:
    рік (stress on [i]) — років (stress on [i] in suffix, root has [о]).
    Авраменко Grade 5 p.111: the alternation often reveals
    the original vowel that existed before the shift to [i]."
  - "Practice: given a word with [i] in a closed syllable,
    learners find the form with [о] or [е] by changing the word form.
    This is exactly the spelling strategy taught in Ukrainian schools:
    Литвінова Grade 5 p.118: 'Якщо під час зміни слова сумнівний
    звук чергується з [i] в закритому складі — пишемо и: осені (бо
    осінь).'"
  - "Summary table: all three alternation types with examples,
    triggers, and exceptions — a reference card learners can use."
- section: "Підсумок: правила i практика"
  words: 300
  points:
  - "Complete alternation summary with decision flowchart:
    Step 1: Is the syllable open or closed? -> [о]/[е] ~ [i]
    Step 2: Does the vowel disappear? -> fleeting vowel
    Step 3: Is it after a шиплячий? -> [о] ~ [е] rule
    Step 4: Is it a verb root with suffix change? -> verb alternation."
  - "Self-check in Ukrainian: Дайте відповіді на запитання:
    1. Чому в слові 'двір' пишемо i, а в слові 'двори' — о?
    2. Яке чергування відбувається у словах 'день — дня'?
    3. Після яких приголосних чергуються [о] з [е]?
    4. Запишіть три пари слів із чергуванням [о] ~ [i]."
  - "Preview of next module: Чергування приголосних (іменники) —
    consonant alternations in noun paradigms, building on the same
    morphophonemic logic."
vocabulary_hints:
  required:
  - "чергування (alternation — systematic sound change between word forms)"
  - "голосний (vowel — sound produced without obstruction)"
  - "відкритий склад (open syllable — ending in a vowel sound)"
  - "закритий склад (closed syllable — ending in a consonant sound)"
  - "корінь (root — the core meaning-bearing part of a word)"
  - "наголос (stress — emphasized pronunciation of a syllable)"
  - "біглий голосний (fleeting vowel — vowel that disappears in some forms)"
  - "нуль звука (zero sound — absence of a vowel in an alternation)"
  - "суфікс (suffix — morpheme added after the root)"
  - "закінчення (ending — inflectional morpheme at the end of a word)"
  - "шиплячий (hushing consonant — ж, ч, ш, дж)"
  - "орфограма (orthographic rule — a spelling pattern requiring a rule)"
  - "відмінок (grammatical case)"
  - "форма слова (word form — a specific inflected variant of a word)"
  recommended:
  - "милозвучність (euphony — pleasant sound quality of speech)"
  - "ненаголошений (unstressed — syllable without stress)"
  - "відкритий (open — ending in a vowel)"
  - "закритий (closed — ending in a consonant)"
  - "морфонологія (morphophonology — study of sound alternations in morphology)"
  - "твердий (hard — non-palatalized consonant)"
  - "м'який (soft — palatalized consonant)"
  - "спільнокореневий (cognate — sharing the same root)"
  - "правопис (orthography — correct spelling rules)"
  - "перевірне слово (checking word — word used to verify spelling)"
activity_hints:
- type: quiz
  focus: "Identify which vowel alternation type is present in word pairs
    (e.g., рік-року = [о]~[i]; день-дня = fleeting vowel)"
  items: 8
- type: fill-in
  focus: "Complete word forms by applying the open/closed syllable rule
    (e.g., двір — двор___, стіл — стол___)"
  items: 8
- type: match-up
  focus: "Match nominative forms with their oblique case counterparts
    (e.g., рік <-> року, кінь <-> коня, день <-> дня)"
  items: 8
- type: group-sort
  focus: "Sort word pairs into categories: [о]~[i] alternation,
    [е]~[i] alternation, fleeting vowel, no alternation"
  items: 10
- type: error-correction
  focus: "Find and fix vowel spelling errors in sentences caused by
    incorrect application of alternation rules"
  items: 6
connects_to:
- "b1-001 (metalanguage-phonetics — foundation: наголос, склад, голосний)"
- "b1-009 (alternation-consonants-nouns — consonant alternations in nouns)"
- "b1-011 (simplification-consonants — another morphophonemic process)"
prerequisites:
- "A2 completion (learner knows basic noun declension and verb conjugation)"
- "b1-001 (metalanguage-phonetics — наголос, відкритий/закритий склад)"
grammar:
- "Чергування [о], [е] з [i] — the open/closed syllable rule"
- "Чергування [о], [е] з нулем звука — fleeting vowels (біглі голосні)"
- "Чергування [о] з [е] after шиплячі та [й]"
- "Vowel alternations in verb roots driven by stress and suffix"
- "Connection between наголос shift and vowel alternation"
- "Spelling verification strategy: finding the перевірне слово"
register: академічний
references:
- title: "Авраменко Grade 5, p.111-113"
  notes: "Core чергування голосних chapter: definition, examples with
    сіль-соляний, корінь-кореня, systematic presentation of patterns."
- title: "Заболотний Grade 5, p.113-115"
  notes: "Чергування голосних звуків (section 27): verb pairs
    летіти-літати, practice exercises with open/closed syllable analysis."
- title: "Литвінова Grade 5, p.118"
  notes: "Правопис ненаголошених [е] та [и]: verification strategy
    using word form changes, connection to чергування з [i]."
- title: "Глазова Grade 10, p.103"
  notes: "Mature presentation: [о],[е]~[i] as a defining feature of
    Ukrainian, systematic examples шко-ла — шкіл, дво-ри — двір."
- title: "Заболотний Grade 7, p.55-56"
  notes: "Чергування [о] з [е] після шиплячих: rule formulation,
    exceptions, practice exercises."

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
- Confirmed: чергування, голосний, корінь, наголос, суфікс, закінчення, шиплячий, орфограма, відмінок, милозвучність, ненаголошений, відкритий, закритий, морфонологія, твердий, м'який, спільнокореневий, правопис.
- Not found: відкритий склад, закритий склад, біглий голосний, нуль звука, форма слова, перевірне слово (These are common multi-word linguistic terms; components like "склад", "голосний", "форма", "слово", "перевірне" are all individually verified).

## Textbook Excerpts
### Section: Що таке чергування голосних?
> "Іноді, коли утворюємо нове слово або його форму, звук може змінюватися на інший: сіль — соляний, солі; корінь — кореня. Це мовне явище називають чергуванням звуків."
> Source: Avramenko, Grade 5

### Section: Чергування [о], [е] з [і]
> "Голосні звуки [о], [е] (у відкритих складах) часто чергуються з [і] (у закритих складах): шко-ла — шкіл; дво-ри — двір; по-со-ли — сіль; у мо[йе]му — у мо[йі]м."
> Source: Glazova, Grade 10

### Section: Чергування [о], [е] з нулем звука
> "Чергування [о], [е] з нулем звука (випадання): садок – садка, вітер – вітру."
> Source: Zabolotnyi, Grade 10

### Section: Чергування [о] з [е] після шиплячих та [й]
> "Після ж, ч, ш, щ, дж, й перед м’яким приголосним, а також перед складами з е та и пишемо е: вечеря, вишень, джерело, женити. Перед твердим приголосним, а також перед складами з а, о, у пишемо о: бджола, будиночок, пшоно, знайомий."
> Source: Karaman, Grade 10

### Section: Чергування голосних у дієслівних коренях
> "Чергування відбуваються у дієслівних коренях: схопити — хапати ([о]-[а]), летіти — літати ([е]-[і]), стерти — стирати ([е]-[и])."
> Source: Avramenko, Grade 5

## Grammar Rules
- [о], [е] — [і] в закритих складах: Правопис §9 — "У сучасній українській мові звуки о, е у відкритих складах чергуються з і в закритих складах".
- [е] — [о] після шиплячих: Правопис §10 — "Після ж, ч, ш, шч, дж, й перед м’яким приголосним... пишемо е... перед твердим приголосним... пишемо о".
- Дієслівні чергування: Правопис §11 — "Чергування О — А... Е — І... Е (випадний) — И".

## Calque Warnings
- біглий голосний: OK/Term — Pravopys uses "випадний е" (§11), but "біглі голосні" is used in textbooks (Zabolotnyi 10). I will use "випадний" as the primary term.
- у якості: Calque — Correct: "як".
- приймати участь: Calque — Correct: "брати участь".
- на протязі: Calque — Correct: "протягом" (time) or "на протягу" (wind).

## CEFR Check
- чергування: B2 — Necessary linguistic term for this module.
- голосний: B1 — OK.
- наголос: B1 — OK.
- корінь: B1 — OK.
- відмінок: A1 — OK.
- правопис: B1 — OK (implied from derivatives).
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
# Verified Knowledge Packet: Чергування голосних
**Module:** alternation-vowels | **Phase:** B1.2 [Morphophonemics & Noun Subclasses]
**Textbook grades searched:** 1, 2, 3, 5

---

## Що таке чергування голосних?

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 116
> **Score:** 0.50
>
> 113
> 27. ЧЕРГУВАННЯ ГОЛОСНИХ ЗВУКІВ
> Про те, як під час творення слів чи зміни форми слів  
> замість одного голосного з’являється інший
> ПРИГАДАЙМО. 1. Що таке суфікс слова? 2. Який склад називають від-
> критим? 
> 275.	А.  Прочитайте пари дієслів. 
> лет¾ти – літати    терти – стирати    котити – катати
> Б.  Якими звуками різняться корені слів у кожній парі?
> В.  Простежте, чи залежить чергування в цих словах від місця наго­
> лосу та суфікса.
> Іноді під час творення слова чи зміни його форми замість 
> одного звука з’являється інший. НАПРИКЛАД: друг – дружити; 
> стіл – стола. Таку зміну звуків називають чергуванням.
> В українській мові можливі чергування і голосних, і 
> приголосних звуків.
> Звуки, які 
> чергуємо
> Приклади 
> [о] – [і]
> [е] – [і]
> кінь – коня, вільний – воля, колесо – коліс 
> Примітка.

> **Source:** avramenko, Grade 5
> **Section:** Сторінка 111
> **Score:** 0.33
>
> 111
>  § 48–49.  Чергування  голосних  звуків
> 1.	Прочитайте речення та виконайте завдання.
> Кінь міг літати.
> Коні можуть летіти.
> А. Простежте за голосними в коренях слів.
> Б. Чи помітили ви якусь закономірність?
> § 48–49.  ЧЕРГУВАННЯ  ГОЛОСНИХ  ЗВУКІВ
> Іноді, коли утворюємо нове слово або його форму, звук може змінюва-
> тися на інший: сіль — соляний, солі; корінь — кореня.

> **Source:** avramenko, Grade 5
> **Section:** Сторінка 115
> **Score:** 0.25
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

## Чергування [о], [е] з [i]

> **Source:** kravcova, Grade 2
> **Section:** Сторінка 45
> **Score:** 0.25
>
> 45
> На подвір’ячку, під в’язом,
> вся зібралася сім’я:
> відпочить, побути разом
> та послухать солов’я.
> 	
> 	
> 	
> Надія Красоткіна
> 2.	 Випиши слова, у яких є апостроф.
> 163. 1.	 Користуючись словами для довідки, доповни речення.
> 1.  Тіло риб покриває луска, а тіло птахів — ...  . 
> 2. В’юн — риба, а м’ята — ... . 3. Пір’їна легка, а камінь ... . 
> 4. Найбільше багатство — ... . 5. Тато, мама і я — дружна ... . 
> 6. П’ятий день тижня — ... .
> Слова для довідки: п’ятниця, здоров’я, рослина, пір’я, 
> важкий, сім’я. 
> 2. Спиши відновлені речення.
> 164. 1.	 Прочитай вірш. Як ти гадаєш, про що говоритиме сім’я?
> 165. 1.	 За допомогою алфавіту утвори слово. Підказка: записуй 
> букви в тому порядку, що й числа.
> 15
> 1
> 17
> ’
> 33
> 18
> 11
> 14
> 2.	 Пригадай, коли ми ставимо апостроф. 
> Крок 1.

## Чергування [о], [е] з нулем звука

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 120
> **Score:** 0.33
>
> 117
> 284.	Доберіть до поданих слів їхні форми або спільнокореневі слова із 
> чергуванням приголосних. Запишіть слова групами. Вимовте звуки, які 
> чергуємо, та підкресліть букви на позначення 
> цих звуків.
> ЗРАЗОК. Книга – книзі, книжечка. 
> Забігати – забіжу.
> Берег, перемога, серветка, горох, 
> тихо, заходити, їздити­. 
> 285.	ЧОМУ ТАК? Поясніть, чому подані в парах слова вважаємо спіль-
> нокореневими, хоча в їхніх коренях немає спільних звуків.
> 1. Річний – у році. 2. Нога – ніжка.
> 286.	Простежте, чи відбувається чергування голосних або приголос­
> них звуків під час зміни форми назви вашого населеного пункту, мікро-
> району, вулиці, назви річки, озера тощо у вашій місцевості. Поділіться 
> своїми спостереженнями. 
> 287.	І. Прочитайте гумореску Грицька Бойка.

## Чергування [о] з [е] після шиплячих та [й]

> **Source:** bolshakova, Grade 2
> **Section:** Сторінка 48
> **Score:** 0.50
>
> 48
> ПЕрЕнос сЛІв З ь І ьо
> Прочитай слова. До якого слова немає малюнка? Чим схожі 
> слова? Чим відрізняються? Спиши. Познач м’які приголосні 
> звуки знаком 
> .  
> галка — галька 
> лан — лань
> мілка — мі лька
> Спиши. Відшукай слова зі знаком м’якшення. Познач м’який 
> приголосний перед знаком м’якшення знаком 
> .
> У метелика біленькі крильця. Василько сів на маленький 
> стільчик. Вітерець підняв легеньку пір’їнку. Сіренький заєць 
> їсть морквинку.  
> Не відривай букву ь від попередньої букви, 
> коли переносиш слово з рядка в рядок. 
> Наприклад: кіль-це, паль-ці, апель-син.
> Поділи слова для переносу.
> Зразок. Кіль-це, … .
> Зразок.

> **Source:** bolshakova, Grade 1
> **Section:** Сторінка 41
> **Score:** 0.25
>
> 41
> Знайди слово до схеми.
> 	
> щука	
> дощик	
> щастя	
> щедро
> 	
> щавель	
> кущик	
> щасливий	
> щедрість
> 	 щебетати	
> плащик	
> щастить	
> щедрий
> 
> Вірш. Рима
> ЯК ЖУРАВЕЛЬ ЗБИРАВ ЩАВЕЛЬ 
> На болоті журавель
> Цілий день збирав щавель.
> Назбирав собі на борщ,
> Та якраз впе-рі-щив дощ,
> І щавель знесла водиця, —
> Без борщу лишилась птиця.
> З того часу журавель
> Сировим жує щавель.
> 	
> Михайло Стельмах
> 
> Скоромовка
> Борщик у горщику,
> Щавель у борщику.
> А до борщу — 
> Ще й по лящу.
> 1
> 2
> 3
> Щ щ
> 	
> ща	
> що	
> щу	
> щи
> 	
> щі	
> ще	
> ащ	
> ощ
> 	
> ущ	
> ищ	
> іщ	
> ещ

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 177
> **Score:** 0.50
>
> 177
> Фонетика. Графіка. Орфоепія. Орфографія. Милозвучність української мови
> Чергування прийменників З — ЗІ — ІЗ
> З
> ІЗ
> ЗІ
> перед словом, яке почи-
> нається з  голосного:
> з однокласницями;
> з Одеси
> між приголосними:
> Максим 
> із Семеном 
> перед словом, 
> яке починається 
> сполученням 
> приголосних 
> (особливо 
> з  початковими 
> літерами 
> з, с, ш, щ):
> зі мною; 
> зі святом;
> зі швидкістю
> перед словом, яке почи-
> нається з  приголосного 
> (крім свистячих і  ши-
> плячих), якщо утворена 
> сполука є  нескладною 
> для вимови:
> з нагоди святкування
> після голосного 
> перед  наступними 
> свистячими і  ши-
> плячими (літери з, 
> ц, с, ч, ш, щ):
> із цими 
> новинами
> Вправа 290
> 1.

## Чергування голосних у дієслівних коренях

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 116
> **Score:** 0.33
>
> 113
> 27. ЧЕРГУВАННЯ ГОЛОСНИХ ЗВУКІВ
> Про те, як під час творення слів чи зміни форми слів  
> замість одного голосного з’являється інший
> ПРИГАДАЙМО. 1. Що таке суфікс слова? 2. Який склад називають від-
> критим? 
> 275.	А.  Прочитайте пари дієслів. 
> лет¾ти – літати    терти – стирати    котити – катати
> Б.  Якими звуками різняться корені слів у кожній парі?
> В.  Простежте, чи залежить чергування в цих словах від місця наго­
> лосу та суфікса.
> Іноді під час творення слова чи зміни його форми замість 
> одного звука з’являється інший. НАПРИКЛАД: друг – дружити; 
> стіл – стола. Таку зміну звуків називають чергуванням.
> В українській мові можливі чергування і голосних, і 
> приголосних звуків.
> Звуки, які 
> чергуємо
> Приклади 
> [о] – [і]
> [е] – [і]
> кінь – коня, вільний – воля, колесо – коліс 
> Примітка.

> **Source:** avramenko, Grade 5
> **Section:** Сторінка 111
> **Score:** 0.50
>
> 111
>  § 48–49.  Чергування  голосних  звуків
> 1.	Прочитайте речення та виконайте завдання.
> Кінь міг літати.
> Коні можуть летіти.
> А. Простежте за голосними в коренях слів.
> Б. Чи помітили ви якусь закономірність?
> § 48–49.  ЧЕРГУВАННЯ  ГОЛОСНИХ  ЗВУКІВ
> Іноді, коли утворюємо нове слово або його форму, звук може змінюва-
> тися на інший: сіль — соляний, солі; корінь — кореня.

## Чергування i наголос: як вони пов'язані

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 120
> **Score:** 0.33
>
> 117
> 284.	Доберіть до поданих слів їхні форми або спільнокореневі слова із 
> чергуванням приголосних. Запишіть слова групами. Вимовте звук

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Що таке чергування голосних?` (~550 words)
- `## Чергування [о], [е] з [i]` (~900 words)
- `## Чергування [о], [е] з нулем звука` (~650 words)
- `## Чергування [о] з [е] після шиплячих та [й]` (~550 words)
- `## Чергування голосних у дієслівних коренях` (~550 words)
- `## Чергування i наголос: як вони пов'язані` (~500 words)
- `## Підсумок: правила i практика` (~300 words)
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
  1. **A Ukrainian teacher explaining to students why certain words change their vowels — using examples from a grocery list: Я купив коня (m, horse), але: коні (pl). Вона живе в селі (n), але: село. Він поставив стіл (m), але: на столі.**
     Speakers: Вчитель, Студенти
     Why: Vowel alternation о/е→і: кінь→коня, село→селі, стіл→столі

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

**Required:** чергування (alternation — systematic sound change between word forms), голосний (vowel — sound produced without obstruction), відкритий склад (open syllable — ending in a vowel sound), закритий склад (closed syllable — ending in a consonant sound), корінь (root — the core meaning-bearing part of a word), наголос (stress — emphasized pronunciation of a syllable), біглий голосний (fleeting vowel — vowel that disappears in some forms), нуль звука (zero sound — absence of a vowel in an alternation), суфікс (suffix — morpheme added after the root), закінчення (ending — inflectional morpheme at the end of a word), шиплячий (hushing consonant — ж, ч, ш, дж), орфограма (orthographic rule — a spelling pattern requiring a rule), відмінок (grammatical case), форма слова (word form — a specific inflected variant of a word)
**Recommended:** милозвучність (euphony — pleasant sound quality of speech), ненаголошений (unstressed — syllable without stress), відкритий (open — ending in a vowel), закритий (closed — ending in a consonant), морфонологія (morphophonology — study of sound alternations in morphology), твердий (hard — non-palatalized consonant), м'який (soft — palatalized consonant), спільнокореневий (cognate — sharing the same root), правопис (orthography — correct spelling rules), перевірне слово (checking word — word used to verify spelling)

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
## Що таке чергування голосних? (~600 words total)
- P1 (~120 words): [Introduction connecting back to B1-M01. Recall the basic phonetics: vowels (голосні), consonants (приголосні), and the architecture of syllables (відкритий/закритий склад). Define 'чергування' as a systematic replacement of one sound with another during word formation or inflection, using the foundational example from Avramenko: сіль — солі, кінь — коня.]
- P2 (~130 words): [Linguistic context: Why this matters. Explain that vowel alternation is the 'DNA' of the Ukrainian language, distinguishing it from Russian and Polish. Use Glazova’s insight that this is a defining feature of the language's melody (милозвучність). Explain that for a learner, mastering this isn't just about 'rules' but about unlocking the ability to recognize roots across different cases.]
- P3 (~120 words): [Dialogue: Вчитель та Студенти. The teacher uses a grocery list to demonstrate. 'Я купив коня' (m, horse), but pointing at a field: 'Там коні' (pl). 'Він поставив стіл' (m), but 'Книжка на столі'. The students notice the o/i shift and ask why. Teacher introduces the concept of syllable 'breathing' (open vs closed).]
- P4 (~130 words): [Categorization: Preview the three main types covered in the module. 1. The O/E to I shift in closed syllables. 2. Fleeting vowels (біглі голосні) that vanish into thin air. 3. The O/E alternation after hushing consonants (шиплячі). Emphasize that each has a logic tied to the history of the language.]
- P5 (~100 words): [Motivation and Strategy. Explain that while these look like 'exceptions' to English speakers, they are the 'standard' in Ukrainian. Advise the learner to stop thinking of 'стіл' as the 'real' word and 'стола' as a 'change', but rather to see the root {ст-л-} as a flexible unit that adapts to its environment.]

## Чергування [о], [е] з [i] (~1000 words total)
- P1 (~150 words): [The Core Rule: Open vs. Closed Syllables. Deep dive into Zabolotnyi’s rule: [о] or [е] in an open syllable (ending in a vowel) typically changes to [i] when the syllable becomes closed (ending in a consonant). Define 'closed' visually: the consonant 'locks' the vowel in. Examples: ко-ня (open) vs. кінь (closed); сто-ли (open) vs. стіл (closed).]
- P2 (~150 words): [The 'Backwards' Logic. Explain that we often see [i] in the dictionary form (Nominative) because it's a closed one-syllable word. But the 'original' vowel reveals itself in the Genitive or Locative. Examples: двір (Nom, closed) -> дво-ру (Gen, open); ніс -> но-са; рік -> ро-ку. This is the 'detective work' of Ukrainian morphology.]
- P3 (~130 words): [Alternation in Nouns: Masculine vs. Feminine. Show how the rule applies regardless of gender. Masc: віз — воза, поріг — порога. Fem: ніч — ночі, річ — речі, сіль — солі. Note that the [i] appears in the closed syllable of the Nominative singular for these feminine 3rd declension nouns.]
- P4 (~120 words): [Alternation in Adjectives and Verbs. Demonstrate that this isn't just for nouns. Adjectives: осінній (from осінь/осені), вечірній (from вечір/вечора). Verbs: нести (open) vs. ніс (closed/past masc); везти (open) vs. віз (closed/past masc). Explain that the [i] acts as a marker of the closed syllable in the past tense.]
- P5 (~130 words): [Exceptions and Loanwords. Crucial distinction: Borrowed words usually don't play by these rules. Explain why we say 'мотор — мотору' and not 'мотір'. Discuss 'автомобіль', 'коридор', and 'бетон'. If the word feels 'modern' or 'international', the [о] stays stable. Mention a few native exceptions like 'слон — слона' (no alternation because of historical vowel length).]
- P6 (~150 words): [Reading Passage: 'Наше село'. A descriptive text about a Ukrainian homestead. Use words: двір, стіл, піч, поріг, кінь, коні, стола, печі. The text describes a scene where a horse (кінь) stands near the threshold (поріг), and bread is on the table (стіл). Contextualizes the grammar within a narrative arc.]
- Exercise (~70 words): [Match-up activity. Match 8 Nominative forms (кінь, стіл, рік, ніч, сіль, віз, двір, річ) with their Genitive counterparts (коня, стола, року, ночі, солі, воза, двору, речі).]
- Exercise (~100 words): [Fill-in activity. Learners provide the missing vowel (o, e, or i) based on syllable structure. Items: 1. П_д_л (Nom) -> По-до-лу (Gen). 2. В_ч_р (Nom) -> Ве-чо-ра (Gen). 3. К_р_нь (Nom) -> Ко-ре-ня (Gen). 8 items total.]

## Чергування [о], [е] з нулем звука (~720 words total)
- P1 (~140 words): [Definition of 'Fleeting Vowels' (біглі голосні). Based on Zabolotnyi Grade 5: explain that [о] and [е] sometimes disappear entirely. Use the 'breathing' metaphor again—sometimes the word 'exhales' and the vowel drops to make the word shorter when an ending is added. Example: учень (vowel present) vs. учня (vowel gone).]
- P2 (~150 words): [The Masculine Noun Pattern. Focus on common words: день — дня, вітер — вітру, камінь — каменя, хлопець — хлопця. Explain that these vowels usually sit in the final syllable of the Nominative. When the Genitive/Dative/etc. endings are attached, the vowel is no longer needed to 'support' the final consonant, so it vanishes.]
- P3 (~130 words): [Suffix Analysis: -ець, -ок, -ень. Identify these as the 'danger zones' for fleeting vowels. -ець: молодець -> молодця, українець -> українця. -ок: замок -> замка, подарунок -> подарунка. -ень: корінь -> кореня, півень -> півня. This helps learners predict the drop based on the suffix shape.]
- P4 (~150 words): [Stable Vowels vs. Fleeting Vowels. How to tell them apart? Compare 'сон' (sleep) -> 'сну' (fleeting) with 'стон' (moan) -> 'стону' (stable). Explain that there isn't always a visual cue, but listening to the rhythm helps. If the vowel is 'weak' and unstressed in the Nominative, it's a candidate for disappearing.]
- P5 (~150 words): [Dialogue: At the University. A student looking for a classmate. 'Де цей хлопець?' (Nom). 'Я не бачу цього хлопця' (Gen). 'Йому, цьому хлопцеві, треба зателефонувати' (Dat). The dialogue naturally cycles through the forms, highlighting the missing 'е' in every form except the Nominative.]

## Чергування [о] з [е] після шиплячих та [й] (~600 words total)
- P1 (~150 words): [The Hushing Consonant Rule. Reference Zabolotnyi Grade 7. After [ж, ч, ш, дж] and [й], the choice between 'о' and 'е' is not random. It depends on the 'hardness' or 'softness' of the following environment. Introduce the concept of the 'following syllable check'.]
- P2 (~150 words): [Trigger 1: Use 'е' before soft consonants or syllables with 'е' or 'и'. Examples: вечеря (followed by 'е'), вишень (followed by soft 'н'), джерело (followed by 'е'). This creates a 'soft-harmony' in the word. Contrast with Trigger 2: Use 'о' before hard consonants or syllables with 'а, о, у'. Examples: бджола (followed by 'а'), знайомий (followed by 'и'—explain the exception here), будиночок.]
- P3 (~150 words): [Comparison with Russian. Explain that in Russian, the letter 'ё' often masks these distinctions. In Ukrainian, the distinction is audible and orthographically required. 'Пшоно' (hard environment) vs. 'пшениця' (soft environment). This builds phonetic sensitivity.]
- P4 (~150 words): [The 'Memory List' of Exceptions. List and explain the words that defy the rule: чепурний, шепіт, жебоніти, щедрий, чекати (all use 'е' despite hard neighbors) and чоло, бджола (use 'о' despite soft neighbors). Give a short mnemonic sentence including these: 'Щедрий шепіт бджоли біля чола'.]

## Чергування голосних у дієслівних коренях (~600 words total)
- P1 (~150 words): [Verb Root Alternations. Connect to A2 knowledge of Aspect pairs. Explain that in verbs, vowel change is often used to distinguish between 'doing' (Imperfective) and 'done' (Perfective). Use Zabolotnyi’s example: летіти (to fly) vs. літати (to be flying/habitual). The 'е' changes to 'і' based on the suffix '-а-'.]
- P2 (~150 words): [The E-I-Y Pattern. Show the three-way shift: терти (to rub) -> стирати (to erase) -> витирати. Root: {тер/тир/тір}. Explain that the vowel 'и' appears when the root is followed by the suffix '-а-'. Other examples: заберу -> забирати, завмерти -> завмирати. This is a crucial tool for building Perfective/Imperfective pairs.]
- P3 (~150 words): [The O-A Pattern. Discuss the [о] ~ [а] shift. котити (to roll) -> катати, схопити (to grab) -> хапати, ломити -> ламати. Rule: [о] changes to [а] before the stressed suffix '-а-'. This is a very common 'B1' level verb pattern that allows learners to 'guess' the imperfective form of many verbs.]
- P4 (~150 words): [Historical context: Why do verbs do this? Briefly mention that in ancient times, vowel length mattered. Today, those length differences have turned into different vowels. This gives the learner a sense that the language is an evolving system, not just a list of random hurdles.]

## Чергування i наголос: як вони пов'язані (~550 words total)
- P1 (~150 words): [Stress as the Engine. Explain that vowel alternation isn't just about syllables, it's about the energy of the word. When the stress (наголос) moves, the vowels often shift to compensate. Example: рíк (stress on root) -> рокíв (stress moves to ending, root vowel 'relaxes' back to 'о').]
- P2 (~150 words): [The 'Checking Word' Strategy (перевірне слово). Teach the learner the primary school method for spelling: if you aren't sure if it's 'е' or 'и', try to find a form where that vowel alternates with 'і' in a closed syllable. Example: 'осені' (is it 'е' or 'и'?) -> 'осінь' (closed syllable has 'і'). Therefore, we write 'е'.]
- P3 (~150 words): [Summary Table Presentation. Create a mental map of the 'Decision Card'. If Syllable is Closed -> check for 'і'. If Vowel vanishes -> check for fleeting vowel. If stress moves -> check for o/e return. This section acts as the 'cheat sheet' for the entire 4000-word module.]
- Exercise (~100 words): [Error-correction activity. Provide 6 sentences with common alternation 'mistakes' (e.g., 'Я не бачив свово коня' -> 'коня' is correct, but what if they wrote 'кіня'?). Focus on 'мотір' vs 'мотор' and 'хлóпеця' vs 'хлопця'.]

## Підсумок — Summary (~330 words)
- P1 (~150 words): [Recap of the three pillars: 1. Syllable structure (Open/Closed) governs the O/E-I shift. 2. Inflectional needs govern the fleeting vowels (біглі голосні) like in 'день-дня'. 3. Consonant hardness/softness governs the O-E shift after hushing sounds. Emphasize that these aren't just for spelling, but for the 'soul' of the Ukrainian sound system.]
- P2 (~180 words): [Self-check questions:
    1. Чому в слові 'двір' пишемо i, а в слові 'двори' — о? (Відповідь: бо склад стає відкритим).
    2. Яке чергування відбувається у словах 'день — дня'? (Відповідь: чергування [е] з нулем звука).
    3. Після яких приголосних чергуються [о] з [е]? (Відповідь: після шиплячих ж, ч, ш, дж та й).
    4. Як перевірити написання слова 'осені'? (Відповідь: змінити слово так, щоб склад став закритим — 'осінь').
    Preview: In the next module, we will apply this same morphophonemic logic to consonants, seeing how 'рука' becomes 'на руці'.]

Grand total: ~4400 words
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
