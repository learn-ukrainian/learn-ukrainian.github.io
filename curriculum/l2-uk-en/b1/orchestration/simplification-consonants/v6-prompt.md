<correction_directive>
CRITICAL: Your previous attempt failed the following checks. Write the module FROM SCRATCH. All original constraints still apply.

- FIX: Missing section heading: 'Підсумок i практика'
- NOTE: Missing 2/14 required vocab: закріплений (fixed — reflected in standard spelling), морфонологія (morphophonology — sound changes in morphology)
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

Write the full prose content for module **11: Спрощення приголосних** (B1, B1.2 [Morphophonemics & Noun Subclasses]).

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
module: b1-011
level: B1
sequence: 11
slug: simplification-consonants
version: '3.0'
title: "Спрощення приголосних"
subtitle: "Щастя — щасливий: коли приголосний випадає"
focus: grammar
pedagogy: PPP
phase: "B1.2 [Morphophonemics & Noun Subclasses]"
word_target: 4000
objectives:
- "Learner can identify consonant simplification in Ukrainian words
  and explain WHY the consonant drops: a cluster of three consonants
  simplifies to two for ease of pronunciation (милозвучність)"
- "Learner can apply spelling rules for simplification that is
  закріплене на письмі (reflected in writing): тижневий (not *тижденевий),
  щасливий (not *щастливий), корисний (not *користний)"
- "Learner can identify exceptions where simplification occurs in speech
  but NOT in writing: шістнадцять, зап'ястний, контрастний"
- "Learner can distinguish simplification from чергування (alternation):
  simplification = consonant DROPS; alternation = consonant CHANGES"
dialogue_situations:
- setting: 'Dictation exercise in a Дніпро classroom — the teacher reads words aloud
    and students discuss which letters disappear: серце (not серДце), тижневий (not
    тижДневий), чесний (not чесТний), щасливий (not щасТливий).'
  speakers:
  - Вчитель
  - Студенти
  motivation: 'Consonant simplification: серДце→серце, чесТний→чесний, щасТливий→щасливий'
content_outline:
- section: "Що таке спрощення?"
  words: 600
  points:
  - "Bridge from M08-M10: learners now understand чергування —
    sounds that CHANGE to other sounds. Спрощення is different:
    a sound DISAPPEARS entirely from a consonant cluster.
    Литвінова Grade 5 p.180: 'Одним із засобів милозвучності
    української мови є спрощення приголосних. Якщо в процесі
    словотворення виникає група з трьох приголосних, один із них
    може випадати.'"
  - "Demonstration from Литвінова Grade 5 p.180, вправа 296:
    проїЗД + Н = проїЗДНий -> проїзний. The [д] drops because
    the cluster [здн] is awkward to pronounce. Ukrainian prefers
    two-consonant clusters over three-consonant ones."
  - "Key distinction: чергування = sound A becomes sound B;
    спрощення = sound A disappears. Both are morphophonemic
    processes, but they work differently.
    чергування: друг -> друже ([г] -> [ж])
    спрощення: щастя -> щасливий ([т] drops)"
- section: "Спрощення, закріплене на письмі"
  words: 850
  points:
  - "Complete table from Заболотний Grade 5 p.110:
    [ждн] -> [жн]: тиждень — тижневий
    [здн] -> [зн]: проїзд — проїзний, виїзд — виїзний
    [стл] -> [сл]: щастя — щасливий, лестощі — улесливий
    [стн] -> [сн]: радість — радісний, якість — якісний,
    честь — чесний, користь — корисний, вість — вісник
    [скн] -> [сн]: бризки — бризнути, тиск — тиснути
    [слн] -> [сн]: масло — масний"
  - "From Литвінова Grade 5 p.181: additional examples organized
    by cluster type. Emphasis: in these words, the simplified
    consonant is NOT written. You write тижневий, not *тижд­невий.
    The spelling reflects the pronunciation."
  - "How to recognize simplification in practice:
    If a derived word seems to be 'missing' a consonant compared
    to its base form, it is likely спрощення.
    Base: тиждень (has [д]). Derived: тижневий (no [д]).
    Base: щастя (has [т]). Derived: щасливий (no [т]).
    Practice: learners identify the 'missing' consonant in 10+ pairs."
  - "Авраменко Grade 5 p.109: орфограма 'спрощення в групах
    приголосних' — students learn to recognize this as a specific
    spelling pattern that requires rule knowledge, not just memory."
- section: "Винятки: спрощення у вимові, але не на письмі"
  words: 650
  points:
  - "From Заболотний Grade 5 p.110:
    Group 1 — no simplification at all (both speech and writing):
    пестливий, хвастливий, кістлявий — pronounce and write [стл].
    These are EXCEPTIONS to the [стл]->[сл] rule."
  - "Group 2 — simplification in speech only (write the consonant):
    шістнадцять [шіс:нац':ат'], зап'ястний [зап'ас:ний],
    контрастний [контрасний], баластний [баласний].
    Авраменко Grade 5 p.109: 'У словах невістці, шістсот
    i подібних літеру т пишемо, але звук [т] не вимовляємо.'"
  - "How to remember which is which:
    The exceptions that KEEP the letter in writing are mostly
    words where the base form is clearly felt: шість -> шістнадцять
    (the connection to шість is obvious, so the т stays in writing).
    The words where simplification IS in writing have drifted
    farther from their base: щастя -> щасливий
    (the connection is felt less directly)."
- section: "Спрощення [сонце], [серце] та інші особливі випадки"
  words: 600
  points:
  - "Words where simplification is so old it is not always recognized:
    сонце [сонце] — but is there a 'missing' [л]? (cf. солоній)
    серце [серце] — is there a 'missing' [д]? (cf. сердитий, сердечний)
    These etymological simplifications are taught as орфограми:
    in серце, the [д] dropped historically but surfaces in related words."
  - "Голуб Grade 5 p.93, вправа 234: connecting спрощення to
    the concept of милозвучність. Students are asked: 'Чи можна
    вважати спрощення засобом милозвучності? Чому?'
    Answer: yes — Ukrainian avoids difficult consonant clusters
    as part of its phonetic character."
  - "Practice: learners work with word families, identifying where
    simplification occurs and where it does not:
    тиждень: тижневий (спрощення), тижня (біглий голосний from M08),
    щотижня (спрощення). Multiple morphophonemic processes in one family."
- section: "Спрощення у дієслівних формах та прикметниках"
  words: 600
  points:
  - "Simplification in adjective formation from nouns:
    якість — якісний ([стн]->[сн])
    совість — совісний ([стн]->[сн])
    ненависть — ненависний ([стн]->[сн])
    область — обласний ([стн]->[сн])
    These follow the regular [стн]->[сн] pattern."
  - "Simplification in verb-related forms:
    виїзд — виїзний ([здн]->[зн])
    тиск — тиснути ([скн]->[сн])
    блиск — блиснути ([скн]->[сн])
    These show that спрощення applies across parts of speech."
  - "Connecting to previous modules: the learner now has three
    morphophonemic tools: чергування голосних (M08),
    чергування приголосних (M09-10), and спрощення (this module).
    Together, they explain most of Ukrainian's spelling 'irregularities.'"
- section: "Спрощення vs. чергування: порівняння"
  words: 400
  points:
  - "Side-by-side comparison:
    | Feature | Чергування | Спрощення |
    | What happens | Sound A -> Sound B | Sound A -> zero |
    | Example | друг -> друже | щастя -> щасливий |
    | Trigger | Morphological (case, person) | Cluster of 3+ consonants |
    | Reversible? | Yes (друже -> друг) | Yes (щасливий -> щастя) |
    Both are regular, predictable, and essential for Ukrainian spelling."
  - "Practice: mixed exercises where learners identify WHETHER
    a given change is чергування or спрощення, and WHICH specific
    type it is. This integrates learning from M08-M11."
- section: "Підсумок i практика"
  words: 300
  points:
  - "Quick reference: all спрощення patterns with one example each.
    Self-check: Дайте відповіді на запитання:
    1. Чому у слові 'щасливий' немає літери т?
    2. Чому у слові 'шістнадцять' літера т пишеться?
    3. Яка різниця між спрощенням i чергуванням?
    4. Утворіть прикметники: радість, якість, тиждень."
  - "Preview of next module: Iменники на -ар, -яр, -ин (M12) —
    shifting from phonetics to morphology, applying all the
    morphophonemic knowledge to specific noun subclasses."
vocabulary_hints:
  required:
  - "спрощення (simplification — dropping of a consonant from a cluster)"
  - "група приголосних (consonant cluster — sequence of consonants)"
  - "милозвучність (euphony — pleasant sound quality of speech)"
  - "випадати (to drop out — of a sound disappearing)"
  - "вимова (pronunciation — how words are spoken)"
  - "правопис (orthography — correct spelling)"
  - "закріплений (fixed — reflected in standard spelling)"
  - "виняток (exception — case that does not follow the rule)"
  - "словотворення (word formation — creating new words)"
  - "прикметник (adjective)"
  - "іменник (noun)"
  - "основа (stem — the word minus its ending)"
  - "орфограма (orthographic rule — spelling pattern requiring knowledge)"
  - "морфонологія (morphophonology — sound changes in morphology)"
  recommended:
  - "чергування (alternation — for comparison)"
  - "корінь (root)"
  - "суфікс (suffix)"
  - "прислівник (adverb)"
  - "транскрипція (phonetic transcription)"
  - "відмінювання (declension — changing word forms)"
  - "дієприкметник (participle)"
  - "похідний (derived — formed from another word)"
  - "непохідний (underived — base form)"
activity_hints:
- type: fill-in
  focus: "Form adjectives or adverbs from nouns, applying simplification
    (e.g., щастя -> щасл___вий, тиждень -> тижн___вий)"
  items: 8
- type: quiz
  focus: "Decide: does the derived word keep or drop the consonant?
    (e.g., шість + -надцять = шістнадцять [keep] vs.
    радість + -ний = радісний [drop])"
  items: 8
- type: group-sort
  focus: "Sort words into two groups: спрощення закріплене на письмі
    vs. спрощення тільки у вимові"
  items: 10
- type: match-up
  focus: "Match base words with their simplified derivatives
    (e.g., проїзд <-> проїзний, щастя <-> щасливий)"
  items: 8
- type: error-correction
  focus: "Find spelling errors: words written with or without
    the simplified consonant incorrectly
    (e.g., *щастливий -> щасливий, *радісний -> correct as is)"
  items: 6
connects_to:
- "b1-008 (alternation-vowels — vowel alternation as morphophonemic process)"
- "b1-009 (alternation-consonants-nouns — consonant alternation for comparison)"
- "b1-010 (alternation-consonants-verbs — consonant changes in verbs)"
- "b1-012 (noun-subclasses-masculine — applying morphophonemic knowledge)"
prerequisites:
- "A2 completion (learner can form basic adjectives and read consonant clusters)"
- "b1-001 (metalanguage-phonetics — приголосний, група приголосних)"
grammar:
- "Спрощення закріплене на письмі: [ждн]->[жн], [здн]->[зн], [стл]->[сл], [стн]->[сн], [скн]->[сн], [слн]->[сн]"
- "Винятки: пестливий, хвастливий, кістлявий (no simplification)"
- "Спрощення у вимові, але не на письмі: шістнадцять, зап'ястний, контрастний"
- "Distinction between спрощення (sound drops) and чергування (sound changes)"
- "Application across parts of speech: nouns, adjectives, verbs"
register: академічний
references:
- title: "Заболотний Grade 5, p.109-112"
  notes: "Спрощення в групах приголосних (section 26): complete table,
    exceptions (пестливий, хвастливий, кістлявий), written-only cases."
- title: "Литвінова Grade 5, p.180-183"
  notes: "Спрощення в групах приголосних: visual demonstration with
    проїЗДНий, tables of закріплені and незакріплені simplifications."
- title: "Авраменко Grade 5, p.109"
  notes: "Спрощення в групах приголосних: орфограма presentation,
    невістці/шістсот exceptions, exercises."
- title: "Голуб Grade 5, p.93"
  notes: "Спрощення як засіб милозвучності: conceptual framing,
    table-based rule formulation exercise."

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
- Confirmed: спрощення, милозвучність, випадати, вимова, правопис, закріплений, виняток, словотворення, прикметник, іменник, основа, орфограма, морфонологія, чергування, корінь, суфікс, прислівник, транскрипція, відмінювання, дієприкметник, похідний, непохідний.
- Not found: група приголосних (confirmed as a set phrase; individual words 'група' and 'приголосний' are in VESUM).

## Textbook Excerpts
### Section: Що таке спрощення?
> Одним із засобів милозвучності української мови є спрощення приголосних. Якщо в процесі творення чи зміни слів виникають складні для вимови сполучення приголосних, один із них випадає, відбувається спрощення.
> Source: Litvinova, Grade 5, p. 180

### Section: Спрощення, закріплене на письмі
> Спрощений у вимові приголосний, як правило, не пишемо. [ждн] → [жн] (тиждень – тижневий), [здн] → [зн] (проїзд – проїзний), [стл] → [сл] (щастя – щасливий), [стн] → [сн] (радість – радісний).
> Source: Zabolotnyi, Grade 5, p. 110

### Section: Винятки: спрощення у вимові, але не на письмі
> Не відбувається спрощення в таких словах: пестливий, хвастливий, кістлявий. Спрощення у вимові відбувається, проте букву т пишемо в таких словах: шістнадцять, зап’ястний, контрастний, баластний...
> Source: Zabolotnyi, Grade 5, p. 110

### Section: Спрощення [сонце], [серце] та інші особливі випадки
> У буквосполученні -слн- випадає л: масло — масний. [Також згадуються] сонце, серце [як приклади історичного спрощення, що відображається на письмі].
> Source: Pravopys § 28 / Litvinova Grade 5

## Grammar Rules
- Спрощення в буквосполученнях: Правопис § 28 — "У буквосполученнях -ждн-, -здн-, -стн-, -стл- випадають д і т на письмі... Але в словах зап’ястний, кістлявий, пестливий, хвастливий, хвастнуту, шістнадцять, дев’яностники букву т зберігаємо."

## Calque Warnings
- приймати участь: Calque — брати участь
- мати місце: Calque (if meaning 'to occur') — бути, траплятися, відбуватися
- приймати міри: Calque — вживати заходів

## CEFR Check
- спрощення: B2 (as a linguistic term) — OK for B1 metalanguage
- милозвучність: B1+ (related to 'ніжність' B2, 'приємно' A1) — OK
- морфонологія: B2+ (linguistic terminology) — OK as metalanguage
- чергування: B2 (linguistic term) — OK
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
# Verified Knowledge Packet: Спрощення приголосних
**Module:** simplification-consonants | **Phase:** B1.2 [Morphophonemics & Noun Subclasses]
**Textbook grades searched:** 1, 2, 3, 5

---

## Що таке спрощення?

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 180
> **Score:** 0.50
>
> 180
> Фонетика. Графіка. Орфоепія. Орфографія. Спрощення в групах приголосних
> Спрощення в  групах приголосних
> Вправа 296
> 1 Розгляньте схему .
> проїЗД + Н = проїЗДНий = проїзний
> 2. Спробуйте вимовити слово проїзний, додавши між звуками [з] і  [н] ще 
> й  звук [д] . А  тепер вимовте слово правильно . Що ви відчували в  обох 
> випадках?
> 3. Висловте припущення: чому під час утворення слова проїзний випав 
> звук [д]?
> Д
> Одним із засобів милозвучності української мови є спрощення 
> приголосних .
> Якщо в процесі творення чи зміни слів виникають складні для 
> вимови сполучення приголосних, однин із  них випадає, відбува-
> ється спрощення .
> Цей процес може відбуватися як на  рівні усного мовлення, 
> тобто спрощується лише звук, так і  бути закріпленим на  письмі, 
> тобто не  пишемо відповідну літеру .

> **Source:** golub, Grade 5
> **Section:** Сторінка 93
> **Score:** 0.33
>
> 93
> 234   Як ви розумієте значення слова «спрощення»? Доберіть до нього 
> спільнокореневі слова. Доберіть за зразком і запишіть пару до 
> кожного з дібраних слів, визначте, які приголосні випадають 
> у  вказаних групах приголосних. Чи можна вважати спрощення 
> засобом милозвучності? Чому?
> Зразок. Тиждень — тижневий; ждн — жн. 
> Виїздити, область, щастя, проїзд, тріск, ненависть. 
> 235   Розгляньте таблицю. Сформулюйте за її змістом правила спро-
> щення в українській мові.

## Спрощення, закріплене на письмі

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 181
> **Score:** 0.50
>
> 181
> Фонетика. Графіка. Орфоепія. Орфографія. Спрощення в групах приголосних
> Закріплені на  письмі спрощення: 
> Спрощення
> Приклади
> ж(д)н
> тиждень — тижневий
> з(д)н
> проїзд — проїзний
> с(т)н
> користь — корисний
> с(т)л
> лестощі — улесливий
> з(к)н
> бризки — бризнути
> с(к)н
> писк — писнути
> с(л)н
> масло — масний
> Спрощення, не  закріплені на  письмі (які відбуваються лише 
> в  усному мовленні), маємо:
> z
> z у винятках зап’ястний, кістлявий, пестливий, хвастли-
> вий, хвастнути, хворостняк, шістнадцять, випускний, 
> вискнути;
> z
> z у словах іншомовного походження, наприклад: 
> контрастний,  баластний, абстрактний.
> д)
> (д
> (д)
> д
> д)
> (д
> (д)
> д
> т)
> (т(т)т
> т)
> (т(т)т
> к)
> (к(к)к
> к)
> (к(к)к
> л)
> (л(л)л
> Вправа 297
> Вставте пропущені літери, де це потрібно .

> **Source:** golub, Grade 5
> **Section:** Сторінка 93
> **Score:** 0.25
>
> 93
> 234   Як ви розумієте значення слова «спрощення»? Доберіть до нього 
> спільнокореневі слова. Доберіть за зразком і запишіть пару до 
> кожного з дібраних слів, визначте, які приголосні випадають 
> у  вказаних групах приголосних. Чи можна вважати спрощення 
> засобом милозвучності? Чому?
> Зразок. Тиждень — тижневий; ждн — жн. 
> Виїздити, область, щастя, проїзд, тріск, ненависть. 
> 235   Розгляньте таблицю. Сформулюйте за її змістом правила спро-
> щення в українській мові.

## Винятки: спрощення у вимові, але не на письмі

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 113
> **Score:** 0.50
>
> 110
> Спрощений у вимові приголосний, як правило, не пи­
> шемо.
> Групи, у яких  
> відбувається спрощення
> Приклади
> [ждн] → [жн]
> [здн] → [зн]
> [стл] → [сл]
> [стн] → [сн]
> тиждень – тижневий
> проїзд – проїзний
> щастя – щасливий
> радість – радісний
> В И Н Я Т К И
> 1. Не відбувається 
> спрощення в  
> таких словах: 
> пестливий, хвастливий,  
> кістлявий
> _____
> ! У цих словах вимовляємо [стл]
> 2. Спрощення у  
> вимові відбувається, 
> проте букву т  
> пишемо в таких 
> словах: 
> шістнадцять, зап’ястний, 
> контрастний, баластний,  
> компостний, аванпостний,  
> форпостний
> _____
> ! У цих словах вимовляємо [сн]
> ОРФОГРАМА
> Спрощення в групах приголосних
> 268.	І. Замініть подані словосполучення на синонімічні з прикметником 
> (за зразком). Утворені словосполучення вимовте й запишіть. Позначте 
> орфограму.
> ЗРАЗОК.

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 181
> **Score:** 0.33
>
> 181
> Фонетика. Графіка. Орфоепія. Орфографія. Спрощення в групах приголосних
> Закріплені на  письмі спрощення: 
> Спрощення
> Приклади
> ж(д)н
> тиждень — тижневий
> з(д)н
> проїзд — проїзний
> с(т)н
> користь — корисний
> с(т)л
> лестощі — улесливий
> з(к)н
> бризки — бризнути
> с(к)н
> писк — писнути
> с(л)н
> масло — масний
> Спрощення, не  закріплені на  письмі (які відбуваються лише 
> в  усному мовленні), маємо:
> z
> z у винятках зап’ястний, кістлявий, пестливий, хвастли-
> вий, хвастнути, хворостняк, шістнадцять, випускний, 
> вискнути;
> z
> z у словах іншомовного походження, наприклад: 
> контрастний,  баластний, абстрактний.
> д)
> (д
> (д)
> д
> д)
> (д
> (д)
> д
> т)
> (т(т)т
> т)
> (т(т)т
> к)
> (к(к)к
> к)
> (к(к)к
> л)
> (л(л)л
> Вправа 297
> Вставте пропущені літери, де це потрібно .

## Спрощення [сонце], [серце] та інші особливі випадки

> **Source:** vashulenko, Grade 2
> **Section:** Сторінка 39
> **Score:** 0.50
>
> тттг
> розподіляю 
> пояснюю .
> Наведи свої 
> приклади.
> Г
> Чому берези 
> сумували?
> ? значення
> ? значення
> солодкий цукор 
> глибока криниця 
> м'яка тканина 
> сяє сонце 
> ллється вода
> солодкий сон 
> глибока думка 
> м’який характер 
> сяє обличчя 
> ллється музика
> Г
> 2| Випиши слова, ужиті в переносному значенні.
> Прийшла до беріз осінь. Принесла 
> їм золотисті стрічки. Вплела їх берізкам 
> у зелені коси.
> Вийшло із-за хмар сонце. Подивилося воно на 
> берези і не впізнало їх: у зелених косах — золотисті 
> стрічки. Сміється сонечко, а берези сумують... 
> (За Василем Сухомлинським).
> 3[ Випиши сполучення слів, у яких слова вживаються у прямому
> і переносному значеннях. Поясни значення слів.
> У кришталевій воді сонце купається. 
> Кришталева люстра прикрашає музей. 
> Кришталевою росою земля вмилася.

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 277
> **Score:** 0.25
>
> 277
> Складні випадки наголошування
> здалека
> зобрази ти
> зо зла
> зрання
> зру чний
> К
> камбала
> катало г
> ки шка
> кінчи ти
> ко лесо
> ко лія
> кори сний
> ко сий
> котри й
> кро їти
> кропива
> кулінарія
> ку рятина
> Л
> лате
> листопад
> лю стро
> М
> мабу ть
> мере жа
> Н
> навчання
> нанести 
> напі й
> начинка
> ненавидіти
> ненависний
> ненависть
> нести 
> ні здря
> нови й
> О
> обіця нка
> обрання
> обру ч (іменник)
> одинадцять
> одноразо вий
> ознака
> о лень
> отаман
> о цет
> П
> пави ч
> пе карський
> перевезти 
> перевести 
> переля к
> перенести 
> пере пад
> піце рія
> по друга
> по значка
> по ми лка
> помо вчати
> поня ття
> посере дині
> привезти 
> привести 
> при морозок
> принести 
> промі жок

> **Source:** kravtsova, Grade 3
> **Section:** Сторінка 44
> **Score:** 0.33
>
> 44
> 2.	 Добери з поданих заголовків найбільш вдалий. Поясни вибір.
> 	 Щедрий Ведмідь і вдячна Мишка.
> 	 Милосердний Ведмідь і вдячна Мишка.
> 	 Справжні друзі. 
> 124.	 Вправа 
> «Квест».
> 4 5
> 5 6 7
> 1 2 5
> диреѳктор
> 3.	 Запишіть свої розповіді на окремих аркушах. На їх основі 
> створіть книжку.
> 123.	 1.	 Пригадай ситуацію, коли:
> 	 ти проявив / проявила милосердя; 
> 	 до тебе проявили милосердя;
> 	 ти був вдячним / вдячною;
> 	 тобі були вдячні за послугу.
> СЛОВА З ПРЕФІКСАМИ РОЗ-, БЕЗ-
> 1.	 Прочитай текст. Як ти гадаєш, чи потрібні професії модельєра, 
> дизайнера? Доведи свою думку.
> Чимало людей хочуть бути стильними і модними. Як цього 
> досягти?
> — Безкрає море творчості та новизни живе в кожному з 
> нас. Тут не можна бути безвідповідальним і безмовним.

## Спрощення у дієслівних формах та прикметниках

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 181
> **Score:** 0.33
>
> 181
> Фонетика. Графіка. Орфоепія. Орфографія. Спроще

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Що таке спрощення?` (~600 words)
- `## Спрощення, закріплене на письмі` (~850 words)
- `## Винятки: спрощення у вимові, але не на письмі` (~650 words)
- `## Спрощення [сонце], [серце] та інші особливі випадки` (~600 words)
- `## Спрощення у дієслівних формах та прикметниках` (~600 words)
- `## Спрощення vs. чергування: порівняння` (~400 words)
- `## Підсумок i практика` (~300 words)
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
  1. **Dictation exercise in a Дніпро classroom — the teacher reads words aloud and students discuss which letters disappear: серце (not серДце), тижневий (not тижДневий), чесний (not чесТний), щасливий (not щасТливий).**
     Speakers: Вчитель, Студенти
     Why: Consonant simplification: серДце→серце, чесТний→чесний, щасТливий→щасливий

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

**Required:** спрощення (simplification — dropping of a consonant from a cluster), група приголосних (consonant cluster — sequence of consonants), милозвучність (euphony — pleasant sound quality of speech), випадати (to drop out — of a sound disappearing), вимова (pronunciation — how words are spoken), правопис (orthography — correct spelling), закріплений (fixed — reflected in standard spelling), виняток (exception — case that does not follow the rule), словотворення (word formation — creating new words), прикметник (adjective), іменник (noun), основа (stem — the word minus its ending), орфограма (orthographic rule — spelling pattern requiring knowledge), морфонологія (morphophonology — sound changes in morphology)
**Recommended:** чергування (alternation — for comparison), корінь (root), суфікс (suffix), прислівник (adverb), транскрипція (phonetic transcription), відмінювання (declension — changing word forms), дієприкметник (participle), похідний (derived — formed from another word), непохідний (underived — base form)

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
## Що таке спрощення? (~600 words total)
- P1 (~120 words): [Bridge from M08-M10 — Contrast "чергування" (alternation) with "спрощення" (simplification). Explain that while alternation changes a sound (друг -> друже), simplification causes a sound to vanish entirely for the sake of "милозвучність" (euphony).]
- P2 (~130 words): [The Phonetic Rule — Explain the "three-consonant cluster" problem. When three consonants meet (like [здн] or [стн]), the middle one often drops out because it is physically difficult to pronounce clearly in fast speech. Reference Литвінова Grade 5 p.180.]
- P3 (~120 words): [Visual Demonstration — Breakdown of "проїзний". Show the base "проїзд" + suffix "-ний" = "проїздний" -> "проїзний". Explain why the [д] is the victim of the cluster and how it aids the flow of the language.]
- P4 (~130 words): [The Purpose of Simplification — Discuss "милозвучність" as a core value of Ukrainian. Explain that unlike English or Russian which may keep silent letters (e.g., "fasten" or "солнце"), Ukrainian usually updates its spelling to reflect natural pronunciation.]
- Dialogue (~100 words): [Dictation exercise in a Дніпро classroom. The teacher reads "серце", "чесний", and "щасливий". Students discuss which letters they hear versus which ones they expect based on base words like "серденько" or "честь".]

## Спрощення, закріплене на письмі (~850 words total)
- P1 (~150 words): [Intro to Written Simplification — Define "закріплене на письмі". Explain that for most common clusters, the letter is officially removed from the dictionary spelling. You write what you hear.]
- P2 (~150 words): [Deep Dive: Clusters with [д] — Explain [ждн] -> [жн] (тиждень — тижневий) and [здн] -> [зн] (проїзд — проїзний, виїзд — виїзний). Provide 3 examples for each, showing the base noun and the derived adjective.]
- P3 (~150 words): [Deep Dive: Clusters with [т] — Explain [стл] -> [сл] (щастя — щасливий, лестощі — улесливий) and [стн] -> [сн] (радість — радісний, честь — чесний, користь — корисний). Note how these are the most frequent cases for learners.]
- P4 (~150 words): [Minor Clusters — Cover [скн] -> [сн] (тиск — тиснути, блиск — блиснути) and [слн] -> [сн] (масло — масний). Use Авраменко Grade 5 p.109 logic to explain these "орфограми".]
- P5 (~150 words): [The "Search for the Base" Strategy — Teach learners how to check if a letter should be there by finding a related word where the cluster is broken (e.g., check "корисний" against "користь").]
- Exercise (~100 words budget): [Match-up activity: Match base words (щастя, проїзд, тиждень, честь) with their simplified derivatives (щасливий, проїзний, тижневий, чесний). 8 items.]

## Винятки: спрощення у вимові, але не на письмі (~650 words total)
- P1 (~170 words): [Group 1 Exceptions: The "Stubborn Trio" — Introduce words where no simplification occurs in speech OR writing: пестливий, хвастливий, кістлявий. Contrast these with "щасливий" to show the unpredictable nature of these historical remnants.]
- P2 (~170 words): [Group 2 Exceptions: Silent but Written — Explain words where the sound drops in speech but the letter MUST stay: шістнадцять [шіс:нац':ат'], зап'ястний, шістсот. Reference Заболотний Grade 5 p.110.]
- P3 (~160 words): [Foreign Loanwords — Discuss words of foreign origin that keep the 't' in writing: контрастний, баластний, компостний, форпостний. Explain that maintaining the root's international form is prioritized over Ukrainian simplification rules.]
- P4 (~150 words): [Memory Hook — Provide a mnemonic for the "Silent T" group. Explain that words closely tied to numbers (шість -> шістнадцять) or body parts (зап'ястя -> зап'ястний) keep the letter to preserve the visual link to the root.]
- Exercise (~100 words budget): [Quiz: Decide "Keep or Drop?" for derived words like "контраст + ний", "шість + надцять", and "радість + ний". 8 items.]

## Спрощення [сонце], [серце] та інші особливі випадки (~600 words total)
- P1 (~150 words): [Historical Fossils — Explain "сонце" and "серце". Show the "missing" [л] in "сонячний" and [д] in "серденько/сердечний". Explain that these are so old they aren't even taught as "rules" but as facts of the language.]
- P2 (~150 words): [Complexity of Word Families — Analyze the "тиждень" family. Show the interaction of different rules: "тиждень" (base), "тижня" (dropping vowel from M08), "щотижня" (simplification). Use this to show how morphophonemic rules layer on top of each other.]
- P3 (~150 words): [Pedagogical Check — Address the learner directly. Ask: "Is simplification just for laziness?" Explain that it's a structural feature of Ukrainian that prevents the language from becoming "heavy" with consonant piles. Link to "милозвучність".]
- P4 (~150 words): [The "False Simplification" trap — Warn about words that look like they simplified but didn't (e.g., "випускний" where [скн] stays). Explain that rules apply to specific groups, not every sequence of three consonants.]
- Exercise (~100 words budget): [Group-sort: Sort words into two categories — "Спрощення закріплене на письмі" vs. "Спрощення тільки у вимові (винятки)". 10 items.]

## Спрощення у дієслівних формах та прикметниках (~600 words total)
- P1 (~150 words): [Adjective Patterns — Focus on nouns ending in "-ість" (якість, совість, ненависть). Show how they consistently become "-ний" adjectives (якісний, совісний, ненависний). This is high-yield for B1 learners writing essays.]
- P2 (~150 words): [Verbal Patterns — Focus on the "-нути" suffix. Show how "тиск + нути" becomes "тиснути" and "блиск + нути" becomes "блиснути". Explain that the sudden addition of a suffix is the primary "trigger" for simplification.]
- P3 (~150 words): [Geographic and Administrative terms — Explain "обласний" (from область). This is a common word in news and daily life. Contrast it with "контрастний" to reinforce the native vs. foreign distinction.]
- P4 (~150 words): [Consistency of the Rule — Summarize that regardless of the part of speech (noun to adj, noun to verb), the phonetic pressure of the cluster [стн] or [скн] leads to the same outcome.]
- Exercise (~100 words budget): [Fill-in: Form adjectives or verbs from base nouns (область, тиск, совість, радість), applying simplification correctly. 8 items.]

## Спрощення vs. чергування: порівняння (~400 words total)
- P1 (~150 words): [The Structural Difference — Use a side-by-side comparison. Alternation (Substitution): Sound A moves to Sound B. Simplification (Deletion): Sound A moves to Zero. Use "друг/друже" vs "щастя/щасливий" as the anchor examples.]
- P2 (~150 words): [Identifying the Process — Explain that "чергування" is usually triggered by grammar (changing case), while "спрощення" is triggered by word formation (adding a suffix). This helps learners predict when to expect which change.]
- P3 (~100 words): [The "Phonetic Logic" of Ukrainian — Conclude that both processes are part of the same "morphophonemic" system that keeps Ukrainian flexible and pleasant to hear.]

## Підсумок — Summary (~300 words total)
- P1 (~150 words): [Quick reference recap: patterns [ждн]->[жн], [здн]->[зн], [стл]->[сл], [стн]->[сн], [скн]->[сн], [слн]->[сн]. List the exceptions clearly: пестливий, хвастливий, кістлявий (always keep) and шістнадцять, зап'ястний (keep in writing only).]
- Q&A (~150 words): [Self-check list:
  1. Чому у слові «щасливий» немає літери т? (Відповідь: відбулося спрощення групи [стл] у [сл]).
  2. Чому у слові «шістнадцять» літера т пишеться? (Відповідь: це виняток, де спрощення відбувається лише у вимові).
  3. Яка різниця між спрощенням і чергуванням? (Відповідь: при спрощенні звук випадає, а при чергуванні — змінюється).
  4. Утворіть прикметники від слів радість, якість, тиждень. (Відповідь: радісний, якісний, тижневий).]
- Exercise (~100 words budget): [Error-correction: Find the spelling errors in a short paragraph where words like *щастливий, *тиждневий, and *радістний are used incorrectly. 6 items.]

Grand total: ~4000 words
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
