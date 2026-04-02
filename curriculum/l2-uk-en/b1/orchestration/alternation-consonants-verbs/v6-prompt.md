

---

## Your Writing Identity

**You are: Experienced Ukrainian Language Instructor.** Your persona is *The Cultural Guide*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **6: Чергування приголосних (дієслова)** (B1, B1.1 [Baselines & Morphophonemics]).

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
module: b1-006
level: B1
sequence: 6
slug: alternation-consonants-verbs
version: '3.0'
title: "Чергування приголосних (дієслова)"
subtitle: "Сидіти — сиджу, плакати — плачу: приголосні в дієсловах"
focus: grammar
pedagogy: PPP
phase: "B1.1 [Baselines & Morphophonemics]"
word_target: 4000
objectives:
  - "Learner can predict and produce consonant alternations in the 1st person singular
    (я-form) of II дієвідміна verbs: [д]->[дж], [т]->[ч], [з]->[ж], [с]->[ш], [ст]->[шч(щ)]
    (водити — воджу, крутити — кручу, носити — ношу)"
  - "Learner can predict consonant alternations when forming imperfective verbs with
    suffixes -ати/-увати: зарядити — заряджати, погасити — погашати"
  - "Learner can produce the губний + [л] alternation in 1st person singular: робити
    — роблю, купити — куплю, ловити — ловлю"
  - "Learner can conjugate common II дієвідміна verbs correctly across all persons,
    recognizing that alternation occurs ONLY in the 1st person singular"
dialogue_situations:
  - setting: 'Cooking competition on Ukrainian TV — the host narrates actions with
      consonant changes: Я ходжу (д→дж) по кухні. Він просить (с→с), але: прошу (с→ш).
      Вона возить (з→з), але: я вожу (з→ж).'
    speakers:
      - Ведучий (host)
      - Учасники змагання
    motivation: 'Consonant alternation in verbs: ходити→ходжу, просити→прошу, возити→вожу'
content_outline:
  - section: "Від іменників до дієслів"
    words: 500
    points:
      - "Bridge from M09 (alternation-consonants-nouns): the same consonants [г/к/х]
        that alternate in nouns also alternate in verbs, but the triggers are different.
        In nouns: case endings. In verbs: conjugation (especially 1st person singular).
        Заболотний Grade 7 p.52: 'Закономірними для української мови стали чергування
        приголосних звуків, що відбулися перед давнім суфіксом j.'"
      - "Why the 1st person singular? Historically, the -у/-ю ending of the 1st person
        contained a [й] sound that triggered palatalization of the preceding consonant.
        This is why the alternation appears ONLY in я-forms, not in ти-, він-forms.
        Modern result: сидіти — сиджу (я), сидиш (ти), сидить (він)."
      - "Overview of the three alternation groups in this module: 1. Задньоязикові:
        [г]->[ж], [к]->[ч], [х]->[ш] (same as nouns) 2. Зубні/свистячі: [д]->[дж],
        [т]->[ч], [з]->[ж], [с]->[ш] 3. Губні + [л]: [б]->[бл], [п]->[пл], [в]->[вл],
        [м]->[мл], [ф]->[фл]"
  - section: "Чергування зубних і свистячих: [д]->[дж], [т]->[ч], [з]->[ж], [с]->[ш]"
    words: 800
    points:
      - "From Глазова Grade 10 p.107: [д] -> [дж]: водити — воджу, сидіти — сиджу,
        ходити — ходжу, родити — роджу, будити — буджу, садити — саджу. [т] -> [ч]:
        крутити — кручу, летіти — лечу, світити — свічу, платити — плачу (note: плакати
        — плачу is [к]->[ч], different!). [з] -> [ж]: возити — вожу, морозити — морожу,
        гасити — гашу. [с] -> [ш]: носити — ношу, просити — прошу, косити — кошу,
        місити — мішу."
      - "Compound alternations: [зд] -> [ждж]: їздити — їжджу, бороздити — борожджу.
        [ст] -> [шч] (written as щ): мостити — мощу, простити — прощу, чистити — чищу,
        пустити — пущу. These are regular extensions of the basic alternations."
      - "Practice conjugation: learners conjugate 8-10 common verbs in теперішній
        час, all persons. Key insight: the alternation ONLY affects я-form. Compare:
        я воджу, ти водиш, він водить, ми водимо, ви водите, вони водять. Pattern:
        alternation in 1st sg., base consonant everywhere else."
      - "Common errors: mixing up [д]->[дж] with [д]->[ж] (the correct alternation
        is [д]->[дж] with the affricate, not simple [ж]). Writing *сижу instead of
        сиджу. The дж is one sound, one letter combination."
  - section: "Чергування задньоязикових у дієсловах: [г]->[ж], [к]->[ч], [х]->[ш]"
    words: 600
    points:
      - "Same consonants as in nouns, same targets: [к] -> [ч]: плакати — плачу, тикати
        — тичу, пекти — печу. [г] -> [ж]: могти — можу, берегти — бережу, стригти
        — стрижу. [х] -> [ш]: колихати — колишу, махати — машу. These verbs belong
        to I дієвідміна (unlike the зубні group above)."
      - "Comparison with noun alternations from M09: Noun: друг -> друже (кличний)
        — same [г]->[ж]. Verb: берегти -> бережу (1st sg.) — same [г]->[ж]. The consonant
        change is identical; only the trigger differs (case ending vs. verb person
        ending)."
      - "Practice: learners identify whether a given alternation ([г]->[ж], [к]->[ч])
        comes from a noun or verb context, reinforcing the shared phonological system."
  - section: "Чергування губних + [л]: робити — роблю"
    words: 600
    points:
      - "From Заболотний Grade 7 p.52: [б] -> [бл']: робити — роблю, любити — люблю,
        губити — гублю. [п] -> [пл']: ліпити — ліплю, купити — куплю, сипати — сиплю.
        [в] -> [вл']: ловити — ловлю, ставити — ставлю, правити — правлю. [м] -> [мл']:
        дрімати — дрімлю, ломити — ломлю. [ф] -> [фл']: графити — графлю (rare)."
      - "This alternation is unique: instead of replacing the consonant, it INSERTS
        [л'] after the губний. The labial consonant stays, but gains a lateral partner.
        This is why it only affects 1st person singular — the historical [й] caused
        [л'] insertion."
      - "Practice: learners conjugate common verbs with губні stems across all persons,
        confirming that [л'] appears only in я-form: я ловлю, ти ловиш, він ловить,
        ми ловимо..."
  - section: "Чергування при утворенні недоконаних дієслів"
    words: 550
    points:
      - "From Глазова Grade 10 p.107: When forming imperfective verbs with -ати/-увати
        from perfective stems, the same alternations apply: [д] -> [дж]: зарядити
        — заряджати, засудити — засуджувати. [з] -> [ж]: знизити — знижати, знижувати.
        [с] -> [ш]: погасити — погашати, погашувати. [т] -> [ч]: скоротити — скорочувати,
        збагатити — збагачувати."
      - "Why this matters for word formation: When learners encounter an unfamiliar
        imperfective verb with [ж], [ч], [ш], or [дж] in the root, they can reconstruct
        the perfective stem: прощати <- простити ([ст]->[шч(щ)]). This is a powerful
        decoding strategy for reading."
      - "Practice: given perfective verbs, learners form the imperfective with -ати/-увати,
        applying the correct consonant alternation."
  - section: "Повна парадигма: від інфінітива до всіх форм"
    words: 550
    points:
      - "Bringing it all together: complete conjugation of representative verbs showing
        where alternation does and does not occur. водити: воджу, водиш, водить, водимо,
        водите, водять; водив, водила, водило, водили; водитиму; водь! водіть! Alternation
        ONLY in теперішній час, 1st person singular."
      - "Contrast with наказовий спосіб (imperative): No consonant alternation in
        imperatives: носи! просіть! сидь! (not *нош!, *прош!, *сидж!). This confirms
        the alternation is specific to the 1-st person present/future context."
      - "Decision flowchart for learners: 1. Is the verb II дієвідміна? -> check for
        [д/т/з/с/б/п/в/м] 2. Is it 1st person singular? -> apply alternation 3. Is
        it any other form? -> use the base consonant 4. Are you forming imperfective
        with -ати/-увати? -> apply alternation"
  - section: "Підсумок: таблиця дієслівних чергувань"
    words: 400
    points:
      - "Complete reference table: | Base | Alternation | Examples | | [д] | [дж]
        | водити-воджу, сидіти-сиджу | | [т] | [ч] | крутити-кручу, летіти-лечу |
        | [з] | [ж] | возити-вожу, морозити-морожу | | [с] | [ш] | носити-ношу, просити-прошу
        | | [зд]| [ждж]| їздити-їжджу | | [ст]| [шч(щ)]| простити-прощу, чистити-чищу
        | | [б] | [бл'] | робити-роблю, любити-люблю | | [п] | [пл'] | купити-куплю,
        ліпити-ліплю | | [в] | [вл'] | ловити-ловлю, ставити-ставлю | | [м] | [мл']
        | ломити-ломлю |"
      - "Self-check: Дайте відповіді на запитання: 1. Яке чергування відбувається
        у формі 'я сиджу'? 2. Чому в дієслові 'роблю' з'являється звук [л']? 3. Провідмінюйте
        дієслово 'просити' в теперішньому часі. 4. Утворіть недоконаний вид: простити,
        зарядити, знизити."
      - "Preview: Спрощення приголосних (M11) — when consonant clusters simplify by
        dropping a sound entirely."
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
    focus: "Write the correct 1st person singular form of II дієвідміна verbs (e.g.,
      сидіти -> я сидж___, носити -> я нош___)"
    items: 10
  - type: quiz
    focus: "Identify which alternation type applies to a given verb: зубний, задньоязиковий,
      or губний + [л]"
    items: 8
  - type: match-up
    focus: "Match infinitive forms with their 1st person singular (e.g., водити <->
      воджу, купити <-> куплю)"
    items: 10
  - type: group-sort
    focus: "Sort verbs by alternation type: [д]->[дж], [т]->[ч], [з]->[ж], [с]->[ш],
      губний+[л]"
    items: 10
  - type: fill-in
    focus: "Form imperfective verbs with -ати/-увати from perfective stems (e.g.,
      простити -> прощ___ти, знизити -> знижув___ти)"
    items: 6
  - type: error-correction
    focus: "Find and fix conjugation errors in sentences (e.g., *я сижу -> я сиджу,
      *я робю -> я роблю)"
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
    notes: "Complete table of verb consonant alternations: зубні, задньоязикові, compound
      groups with examples."
  - title: "Заболотний Grade 7, p.52"
    notes: "Historical explanation: alternations before давній суфікс j, full list
      including губні + [л'] insertion."
  - title: "Авраменко Grade 5, p.114-115"
    notes: "Чергування приголосних звуків: exercises with verb forms in прислів'я
      context."
  - title: "Заболотний Grade 5, p.116-119"
    notes: "Чергування приголосних (section 28): systematic presentation with cross-references
      to чергування голосних."

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
- Not found: [] (All planned terms are verified morphological units in Ukrainian).

## Textbook Excerpts
### Section: Від іменників до дієслів
> "Закономірними для української мови стали чергування приголосних звуків, що відбулися перед давнім суфіксом j."
> Source: Заболотний, 7 клас (с. 52)

### Section: Чергування зубних і свистячих: [д]->[дж], [т]->[ч], [з]->[ж], [с]->[ш]
> "У дієсловах II дієвідміни в 1-й особі однини теперішнього часу кінцеві приголосні основи [д], [т], [з], [с] чергуються відповідно з [дж], [ч], [ж], [ш]: водити — воджу, котити — кочу, возити — вожу, просити — прошу."
> Source: Глазова, 10 клас (с. 107)

### Section: Чергування задньоязикових у дієсловах: [г]->[ж], [к]->[ч], [х]->[ш]
> "Приголосні [г], [к], [х] перед суфіксами -и-, -і- у дієсловах I дієвідміни чергуються з [ж], [ч], [ш]: берегти — бережу, пекти — печу, колихати — колишу."
> Source: Заболотний, 7 клас (с. 53)

### Section: Чергування губних + [л]: робити — роблю
> "Губні приголосні [б], [п], [в], [м], [ф] перед суфіксом -ю (історично -j-) чергуються зі сполученням відповідного губного з [л']: робити — роблю, купити — куплю, ловити — ловлю, ломити — ломлю, графити — графлю."
> Source: Заболотний, 7 клас (с. 52)

### Section: Чергування при утворенні недоконаних дієслів
> "При утворенні дієслів недоконаного виду відбувається чергування: [д]—[дж], [т]—[ч], [з]—[ж], [с]—[ш]: засудити — засуджувати, скоротити — скорочувати."
> Source: Глазова, 10 клас (с. 107)

## Grammar Rules
- Чергування приголосних у дієсловах: Правопис § 16 (Чергування приголосних) та § 82 (Дієвідмінювання дієслів) — Під час відмінювання дієслів II дієвідміни в першій особі однини (я) та в усіх формах дієслів I дієвідміни з основою на задньоязикові відбуваються чергування приголосних.

## Calque Warnings
- при утворенні: OK — (Standard linguistic phrasing).
- дати відповіді на запитання: OK — (Standard pedagogical instruction; "відповісти на запитання" is also correct).
- приймати участь: Calque — брати участь.
- вірний: Calque (in sense of 'correct') — правильний.

## CEFR Check
- чергування: B1 — OK (Academic term).
- дієвідміна: B1 — OK (Grammatical baseline).
- палаталізація: C1 — ABOVE TARGET (Linguistic technicality; used for theory section only).
- африката: B2 — ABOVE TARGET (Phonological term; introduced in school, but high for general B1).
- закономірність: B2 — ABOVE TARGET (General academic term).
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
**Module:** alternation-consonants-verbs | **Phase:** B1.1 [Baselines & Morphophonemics]
**Textbook grades searched:** 1, 2, 3, 5

---

## Від іменників до дієслів

*No textbook results found for: Від іменників до дієслів Задньоязикові Зубні свистячі дж Губні*

## Чергування зубних і свистячих: [д]->[дж], [т]->[ч], [з]->[ж], [с]->[ш]

*No textbook results found for: Чергування зубних і свистячих дж Глазова водити воджу сидіти сиджу ходити ходжу родити*

## Чергування задньоязикових у дієсловах: [г]->[ж], [к]->[ч], [х]->[ш]

*No textbook results found for: Чергування задньоязикових у дієсловах плакати плачу тикати тичу пекти печу могти можу берегти*

## Чергування губних + [л]: робити — роблю

*No textbook results found for: Чергування губних робити роблю Заболотний бл' любити люблю губити гублю пл'*

## Чергування при утворенні недоконаних дієслів

*No textbook results found for: Чергування при утворенні недоконаних дієслів Глазова ати увати дж зарядити заряджати засудити засуджувати прощати*

## Повна парадигма: від інфінітива до всіх форм

*No textbook results found for: Повна парадигма від інфінітива до всіх форм водити воджу водиш водить водимо водите водять водив*

## Підсумок: таблиця дієслівних чергувань

*No textbook results found for: Підсумок таблиця дієслівних чергувань дж водити воджу сидіти сиджу крутити кручу летіти*

## Grammar Reference

*No grammar results for: Зубні свистячі дж зд ждж ст шч Задньоязикові Губні л'*


## МійКлас Theory (miyklas.com.ua)

*Ukrainian school curriculum theory — use this terminology and teaching approach.*

### Чергування голосних у коренях слів
> **Source:** МійКлас — [Чергування голосних у коренях слів](https://www.miyklas.com.ua/p/ukrainska-mova/5-klas/fonetika-grafika-orfoepiia-orfografiia-14565/cherguvannia-golosnikh-u-koreniakh-sliv-43524)

### Теорія:

*www.ua.pistacja.tv*  
При творенні спільнокореневого слова чи формотворенні один голосний звук змінюється на інший. Така зміна називається чергуванням.
Чергування \[О\], \[Е\] — \[І\] відбувається
   О, Е                               І
 
Це чергування  властиве  українській мові. Звуки \[о\], \[е\] виступають найчастіше у відкритих складах, звук \[і\] — у закритих:
- у **формах** слова: *сьомий — сім, шести — шість, корені — корінь, гори — гір, мого — мій, радість — радості — радістю, Канів — Канева, Харків — Харкова, Чернігів — Чернігова*;
  
- у **спільнокореневих** словах:* коло — кільцевий, корова — корівник, клопотатися — клопіт, нога — підніжок.* 
Зверни увагу\!

### Основні випадки чергування у–в, і–й, з–із–зі. Правила милозвучності
> **Source:** МійКлас — [Основні випадки чергування у–в, і–й, з–із–зі. Правила милозвучності](https://www.miyklas.com.ua/p/ukrainska-mova/5-klas/fonetika-grafika-orfoepiia-orfografiia-14565/osnovni-vipadki-cherguvannia-u-v-i-i-z-iz-zi-pravila-milozvuchnosti-41612)

### Теорія:

*www.ua.pistacja.tv*  
Правила милозвучності української мови
Українську мову недарма називають солов'їною й співучою.  Звуки в ній  завжди  поєднуються так, щоб вимову ніщо не ускладнювало. Одна з найважливіших умов милозвучності мови: слова можна розібрати й відділити одне від одного в процесі мовлення.
Мелодійність мови досягається завдяки певним правилам:
- Уникаємо збігу голосних. Таке в українських словах допускається лише на межі префікса і твірної основи:  наодинці, виорав, неуважний.
  
- Уникаємо важкого для вимови збігу приголосних: користь — корисний, сердечний — серце, виїзд — виїзний.

### Правила вживання знака м'якшення
> **Source:** МійКлас — [Правила вживання знака м'якшення](https://www.miyklas.com.ua/p/ukrainska-mova/5-klas/fonetika-grafika-orfoepiia-orfografiia-14565/pravila-vzhivannia-znaka-m-iakshennia-39904)

### Теорія:
  

*www.ua.pistacja.tv*  
 
Знаком ь позначаємо м’якість приголосних звуків на письмі.
Знак м’якшення пишемо:
- Ь пишеться після м’яких д, т, з, с, дз, ц, л, н у кінці **слова** та **складу**: *дядько, радість, низько, заносьте, гедзь, доброволець, коваль, тінь.
*  
- Після **м’яких** приголосних у **середині складу** перед о: *чотирьох, дзьоб, сьомий, льодяний, відьом*.

---
**Total textbook excerpts found:** 1
**Grades searched:** 1, 2, 3, 5
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Від іменників до дієслів` (~500 words)
- `## Чергування зубних і свистячих: [д]->[дж], [т]->[ч], [з]->[ж], [с]->[ш]` (~800 words)
- `## Чергування задньоязикових у дієсловах: [г]->[ж], [к]->[ч], [х]->[ш]` (~600 words)
- `## Чергування губних + [л]: робити — роблю` (~600 words)
- `## Чергування при утворенні недоконаних дієслів` (~550 words)
- `## Повна парадигма: від інфінітива до всіх форм` (~550 words)
- `## Підсумок: таблиця дієслівних чергувань` (~400 words)

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
- P1 (~120 words): [Hook: The living nature of Ukrainian phonetics. Introduce the concept of "consonant friction" (alternation) as a natural adjustment for ease of speech, specifically in verbs.]
- P2 (~130 words): [Bridge from M09 (Nouns). Remind the learner of [г/к/х] -> [ж/ч/ш] changes in nouns like друг/друже and нога/нозі. State that verbs follow a similar logic but with different triggers.]
- P3 (~150 words): [The "Historical Why" (Заболотний Grade 7). Explain the ancient [j] suffix that existed in the 1st person singular. Describe how this "invisible" sound melted into the preceding consonant, creating the modern alternations like сидіти + j -> сиджу.]
- P4 (~150 words): [The "Where and When": Clarify that for conjugation, this happens ALMOST exclusively in the 1st person singular (я-form) of II conjugation verbs. Provide a brief roadmap of the three groups: Dental/Sibilant, Velar, and Labial + [л].]

## Чергування зубних і свистячих: [д]->[дж], [т]->[ч], [з]->[ж], [с]->[ш] (~880 words total)
- P1 (~130 words): [Dental [д] -> [дж]. Explain the transition from a hard dental to a soft affricate. Use examples: водити (воджу), сидіти (сиджу), ходити (ходжу). Contrast with the base consonant in ти водиш.]
- P2 (~130 words): [Dental [т] -> [ч]. Explain how the voiceless partner of [д] becomes a voiceless affricate. Examples: крутити (кручу), світити (свічу), платити (плачу). Note: Distinguish from плакати (плачу), which is a different root type.]
- P3 (~130 words): [Sibilant [з] -> [ж] and [с] -> [ш]. Explain the "hushing" effect. Examples: возити (вожу), морозити (морожу), носити (ношу), просити (прошу).]
- P4 (~120 words): [Compound clusters: [зд] -> [ждж] and [ст] -> [щ] (шч). Explain how these clusters shift together. Examples: їздити (їжджу), вимостити (вимощу), пустити (пущу).]
- Dialogue (~120 words): [Cooking competition: Host narrates actions. "Я ходжу (д->дж) по кухні. Я прошу (с->ш) вас почати. Хто возить (з->з) продукти? Я вожу (з->ж) їх сам."]
- P5 (~120 words): [The Conjugation Constraint. Reiterate that these changes are strictly for the "я" form. Compare full paradigms: я сиджу vs ти сидиш, я кручу vs він крутить to show the return to the base stem.]
- Exercise: [group-sort, Sort verbs by alternation type: [д]->[дж], [т]->[ч], [з]->[ж], [с]->[ш], 10 items]
- Exercise: [fill-in, Conjugate verbs in the я-form based on infinitive: (летіти, будити, місити, чистити, садити), 12 items]

## Чергування задньоязикових у дієсловах: [г]->[ж], [к]->[ч], [х]->[ш] (~660 words total)
- P1 (~150 words): [Velar alternations. Mention that while less common in II conjugation, these are standard for I conjugation verbs. Compare the [г/к/х] set here to the noun set from M09.]
- P2 (~130 words): [[к] -> [ч]. Focus on high-frequency verbs: пекти (печу), плакати (плачу), тикати (тичу). Explain the pronunciation shift from the back of the throat to the roof of the mouth.]
- P3 (~130 words): [[г] -> [ж]. Examples: міг/могти (можу), стерегти (стережу), берегти (бережу), стригти (стрижу).]
- P4 (~120 words): [[х] -> [ш]. Examples: колихати (колишу), махати (машу), дихати (дишу/дихаю — compare the two forms).]
- P5 (~130 words): [Contextual summary. Explain that even though the "я" form changes, the "вони" form might follow the new consonant or the old one depending on the conjugation class (печуть vs плачуть).]
- Exercise: [match-up, Match infinitive with 1st person singular (пекти <-> печу, махати <-> машу), 10 items]

## Чергування губних + [л]: робити — роблю (~660 words total)
- P1 (~150 words): [Labial insertions (б, п, в, м, ф). Introduce the concept of "Epenthetic L" (епентетичне л). Explain that labials are too stubborn to change into another sound, so they invite [л] to help them.]
- P2 (~130 words): [[б] -> [бл] and [п] -> [пл]. Examples: робити (роблю), любити (люблю), купити (куплю), ліпити (ліплю). Contrast with ти робиш, він купить.]
- P3 (~130 words): [[в] -> [вл] and [м] -> [мл]. Examples: ловити (ловлю), ставити (ставлю), дрімати (дрімлю), ломити (ломлю).]
- P4 (~120 words): [[ф] -> [фл]. Mention it's rare, using the example: графити (графлю). Explain why this is important for loanwords that follow Ukrainian morphology.]
- P5 (~130 words): [Pronunciation tip. Focus on the soft [л']. It’s not just any 'L', it's a soft 'L' because of the historical palatalization. Practice saying 'rob-lyu' not 'rob-lu'.]
- Exercise: [fill-in, Write the correct 1st person singular of labial-stem verbs: (губити, сипати, правити, ломити), 10 items]

## Чергування при утворенні недоконаних дієслів (~600 words total)
- P1 (~150 words): [Word formation context. Explain that alternations aren't just for conjugation; they also happen when creating new verb forms, specifically shifting from perfective to imperfective aspect.]
- P2 (~150 words): [The -ати/-увати trigger. Using Глазова Grade 10 logic: When a perfective verb takes these suffixes, the root consonant often alternates to match the new rhythm. Example: зарядити (perf) -> заряджати (impf).]
- P3 (~150 words): [Systematic examples: [с] -> [ш] (погасити -> погашати), [т] -> [ч] (скоротити -> скорочувати), [зд] -> [ждж] (об’їздити -> об’їжджати).]
- P4 (~150 words): [Reading strategy. Teach learners that if they see 'заряджати' and don't know it, they should look for a root with 'д' (зарядити) to find the meaning. This is "reverse-engineering" the language.]
- Exercise: [fill-in, Form imperfective with -ати/-увати: (засудити, знизити, збагатити, простити), 6 items]

## Повна парадигма: від інфінітива до всіх форм (~600 words total)
- P1 (~150 words): [The "Alternation Zone" vs "Stable Zone". Provide a complete table for 'водити'. Show that [дж] appears ONLY in я-form present. Past tense (водив, водила) is stable. Future (водитиму) is stable.]
- P2 (~150 words): [The Imperative check. Explain that imperatives like 'носи!' or 'просіть!' DO NOT alternate. This is a common B1 error (saying *нош! instead of носи!). Explain why: the trigger [j] isn't there.]
- P3 (~150 words): [The Multi-Step Decision Flowchart. 1. Is it 1st Person Singular Present? 2. Is it a II conjugation verb? 3. Identify the consonant class. 4. Apply the specific change.]
- P4 (~150 words): [Contrastive examples. Side-by-side comparison of verbs that look similar but have different alternations. плакати (I) vs платити (II). пекти (I) vs сидіти (II).]
- Exercise: [error-correction, Find and fix errors in sentences: (*я сижу, *я робю, *прош мене), 6 items]

## Підсумок — Summary (~450 words total)
- P1 (~150 words): [Recap the three major groups: Dental/Sibilant, Velar, and Labial. Reiterate that the 1st person singular is the primary "stage" for this grammatical performance in conjugation.]
- Exercise: [quiz, Identify alternation type (зубний, задньоязиковий, губний + [л]) for given verbs, 8 items]
- P2 (~300 words): [Follow the plan: Complete reference table and Self-check questions.]
    - | Base | Alternation | Examples |
    - | [д] | [дж] | водити-воджу |
    - | [т] | [ч] | крутити-кручу |
    - | [з] | [ж] | возити-вожу |
    - | [с] | [ш] | носити-ношу |
    - | [зд]| [ждж]| їздити-їжджу |
    - | [ст]| [щ] | простити-прощу |
    - | [б] | [бл] | робити-роблю |
    - | [п] | [пл] | купити-куплю |
    - | [в] | [вл] | ловити-ловлю |
    - | [м] | [мл] | дрімати-дрімлю |
    - **Self-check:**
    - 1. Яке чергування відбувається у формі "я сиджу"? (сидіти: д -> дж)
    - 2. Чому в дієслові "роблю" з'являється звук [л']? (Губний [б] потребує вставного [л] перед я-закінченням)
    - 3. Провідмінюйте дієслово "просити" в теперішньому часі. (я прошу, ти просиш, він просить...)
    - 4. Утворіть недоконаний вид: простити, зарядити, знизити. (прощати, заряджати, знижувати)

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
