<correction_directive>
CRITICAL: Your previous attempt failed the following checks. Write the module FROM SCRATCH. All original constraints still apply.

- FIX: Missing section heading: 'Summary'
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

**You are: Patient & Supportive Ukrainian Tutor.** Your persona is *The Helpful Teacher*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **52: My Story** (A1, A1.8 [Past, Future, Graduation]).

**Target: 1200–1800 words** of prose (Ukrainian examples count toward word total, headings and exercise placeholders do not).

---

## Step 1: Pacing Plan (output this FIRST)

Before writing any content, output a `<pacing_plan>` block. Evaluate each section from the plan and commit to a word budget. This prevents frontloading early sections and rushing later ones.

```
<pacing_plan>
Section 1 "Title": ~XXX words — [1-sentence content focus]
Section 2 "Title": ~XXX words — [1-sentence content focus]
...
Summary: ~150 words
Total: 1200+ words
</pacing_plan>
```

Then begin writing the module content. Follow your own pacing plan — each section must hit its word budget (±10%).

---

## 9 Hard Rules

1. **IMMERSION TARGET: 20-35% Ukrainian** — this is the percentage of Ukrainian text in your output. The audit will REJECT the module if you exceed it. For early modules, the learner CANNOT READ CYRILLIC — English must dominate. Ukrainian appears only as bolded inline words/phrases. Do NOT write long Ukrainian passages, Ukrainian-only paragraphs, or Ukrainian text without English translation.
2. **EVERY plan point MUST appear in your output.** The plan's `content_outline` lists specific points for each section. You MUST cover ALL of them — every textbook reference, every notation, every example. If the plan says "Захарійчук Grade 1: [•] for vowels, [–] for consonants", you MUST include that notation. Skipping plan points is the #1 reason modules get rejected. Before submitting, mentally check each plan point against your output.
3. **NO IPA, NO Latin transliteration** — never write [mɑmɑ], (khlib), or phonetic brackets. Describe sounds by comparison: "Х sounds like «ch» in Scottish «loch»."
4. **NO "In this lesson we will..."** — never use formulaic openers. Start with a dialogue, a question, or a situation.
5. **Ukrainian quotes: «...»** for Ukrainian text. Use regular quotes "..." for English metalanguage (e.g., "like the 'a' in 'father'").
6. **Place exercise markers only** — do NOT write exercises directly. Place `<!-- INJECT_ACTIVITY: {id} -->` markers where exercises should appear. A separate pipeline step generates the actual exercises from the plan's activity_hints.
7. **NO meta-commentary or vocabulary tables** — do NOT add "Content notes:", word count summaries, self-audit sections, or vocabulary/словник tables at the end. A downstream tool generates vocabulary tables automatically. Just write the module content and stop.
8. **Hit the word target** — you MUST write 1200–1800 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.
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
module: a1-052
level: A1
sequence: 52
slug: my-story
version: '1.2'
title: My Story
subtitle: Я народився, я живу, я буду... — your life in three tenses
focus: communicative
pedagogy: PPP
phase: A1.8 [Past, Future, Graduation]
word_target: 1200
objectives:
- Combine all three tenses (past, present, future) in one coherent narrative
- Tell a simple life story: where you were born, where you live, what you plan
- Use time expressions to signal tense shifts
- Understand a short biography read aloud or in text
dialogue_situations:
- setting: Grandparent telling their life story — Я народився в селі (n, village).
    Ходив у школу (f). Зараз живу в місті (n, city). Працюю в лікарні (f, hospital).
    Буду відпочивати на дачі (f, dacha).
  speakers:
  - Дідусь/Бабуся
  - Онуки
  motivation: Three tenses with село(n), школа(f), місто(n), лікарня(f), дача(f)
content_outline:
- section: Dialogues
  words: 300
  points:
  - 'Dialogue 1 — Getting to know someone deeply: — Розкажи про себе! — Я народився
    в Канаді, у Торонто. — А зараз ти живеш тут? — Так, зараз я живу в Києві. — Чому
    ти переїхав? — Я хотів вивчати українську. Мої бабуся і дідусь з України. — А
    що ти будеш робити далі? — Я буду працювати тут і вчити мову. — Чудово! Успіхів
    тобі! All three tenses in one conversation.'
  - 'Dialogue 2 — Anna''s story: — Я народилася у Львові. Там я вчилася в школі. —
    Потім я переїхала в Київ і закінчила університет. — Зараз я працюю вчителькою
    і живу в центрі міста. — А що далі? — Я буду подорожувати! Я хочу побачити Японію.
    — І ти будеш вчити японську? — Може! Але спочатку — українська для тебе! Past
    → present → future flow.'
- section: Три часи разом (Three Tenses Together)
  words: 300
  points:
  - 'Life story structure: PAST (минулий час): Я народився/народилася в... Я жив/жила
    в... Я вчився/вчилася... Я працював/працювала... PRESENT (теперішній час): Зараз
    я живу в... Я працюю... Я вивчаю... Я люблю... FUTURE (майбутній час): Я буду
    працювати... Я буду вивчати... Я буду жити...'
  - 'Signal words that mark tense shifts: Past: раніше (before), у дитинстві (in childhood),
    коли я був/була маленьким/маленькою (when I was little). Present: зараз (now),
    сьогодні (today), цього року (this year). Future: потім (then), далі (further),
    наступного року (next year). These words help the listener know which tense is
    coming.'
- section: Моя історія (My Story)
  words: 300
  points:
  - 'Model story — Taras''s life: Я народився в Одесі у тисяча дев''ятсот дев''яносто
    п''ятому році. Я жив там з батьками і сестрою. Я ходив у школу і любив математику.
    Потім я переїхав у Київ і вчився в університеті. Зараз я живу в Києві. Я працюю
    програмістом. Я люблю свою роботу. У вільний час я граю у футбол і читаю книжки.
    Далі я буду подорожувати. Я буду вивчати англійську. І я буду жити в Києві — це
    моє місто! Past (народився, жив, ходив) → Present (живу, працюю) → Future (буду
    подорожувати).'
  - 'Your turn — tell YOUR story: Start: Я народився/народилася в [city/country].
    Past: Я жив/жила... Я вчився/вчилася... Я працював/працювала... Present: Зараз
    я живу... Я працюю... Я вивчаю українську, тому що... Future: Я буду... Я хочу...
    Use at least 3 past verbs, 3 present verbs, and 3 future constructions.'
- section: Summary
  words: 300
  points:
  - 'Three tenses — one story: Past: -в/-ла/-ло/-ли (gender endings). Я народився.
    Я жила. Present: person endings. Я живу. Ти працюєш. Вона вивчає. Future: буду
    + infinitive. Я буду працювати. Вона буде жити. Signal words: раніше → past, зараз
    → present, далі → future. Life story vocabulary: народитися (to be born), жити
    (to live), вчитися (to study), переїхати (to move), подорожувати (to travel).
    Self-check: Write your life story in 8-10 sentences using all three tenses.'
vocabulary_hints:
  required:
  - народитися (to be born)
  - жити (to live)
  - вчитися (to study)
  - переїхати (to move)
  - зараз (now)
  - раніше (before/earlier)
  - далі (further/next)
  - розповідати (to tell/narrate)
  recommended:
  - подорожувати (to travel)
  - закінчити (to finish/graduate)
  - дитинство (childhood, n)
  - університет (university, m)
  - програміст (programmer, m)
  - успіх (success, m)
  - мрія (dream, f)
  - батьки (parents, pl)
activity_hints:
- type: ordering
  focus: Put the life events in logical chronological order
  items:
  - Я народився в Торонто.
  - У дитинстві я жив з батьками.
  - Потім я вчився в університеті.
  - Зараз я живу в Києві і працюю програмістом.
  - Далі я буду подорожувати.
- type: fill-in
  focus: Use signal words to determine the correct tense
  items:
  - Раніше я {жив|живу|буду жити} в Канаді.
  - Зараз я {працюю|працював|буду працювати} в університеті.
  - Далі я {буду вивчати|вивчав|вивчаю} українську мову.
  - У дитинстві вона {любила|любить|буде любити} читати.
  - Сьогодні ми {живемо|жили|будемо жити} в Україні.
- type: matching
  focus: Match the life event verb to the correct tense category
  pairs:
  - народився: Минулий час (Past)
  - переїхала: Минулий час (Past)
  - живу: Теперішній час (Present)
  - працюю: Теперішній час (Present)
  - буду подорожувати: Майбутній час (Future)
  - будемо вчитися: Майбутній час (Future)
- type: fill-in
  focus: Complete a biography combining all three tenses
  items:
  - Я {народилася|народився|народилися} у Львові.
  - Там я {вчилася|вчився|вчилися} в школі.
  - Зараз я {працюю|працювала|буду працювати} вчителькою.
  - Наступного року я {буду подорожувати|подорожувала|подорожую}.
connects_to:
- a1-053 (Health)
prerequisites:
- a1-051 (My Plans)
grammar:
- 'All three tenses combined: past (-в/-ла), present (person endings), future (буду
  + inf)'
- 'Tense-shift signal words: раніше, зараз, далі'
- 'Life story verbs: народитися, жити, вчитися, переїхати'
register: розмовний
references:
- title: State Standard 2024, §4.2.4.1
  notes: All three tenses combined in narrative — capstone grammar for A1.

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

**Confirmed (16/16):**
- ✅ народитися (verb)
- ✅ жити (verb)
- ✅ вчитися (verb)
- ✅ переїхати (verb)
- ✅ зараз (adv)
- ✅ раніше (adv)
- ✅ далі (adv)
- ✅ розповідати (verb)
- ✅ подорожувати (verb)
- ✅ закінчити (verb)
- ✅ дитинство (noun)
- ✅ університет (noun)
- ✅ програміст (noun)
- ✅ успіх (noun)
- ✅ мрія (noun)
- ✅ батьки (noun)

**Not found:** none — all 16 plan vocabulary items confirmed in VESUM.

---

## Textbook Excerpts

### Section: Dialogues (знайомство, розповідь про себе)
> "Чи помічали ви, яке прохання більшість із нас ставить у глухий кут? «Розкажіть про себе». Фахівці радять: розповідь має бути цікавою і не дуже довгою, від 3 до 5 хвилин. Основну інформацію про себе давайте стисло, чітко й зрозуміло… Будьте щирими, розповідаючи про себе."
> Source: Голуб, Grade 5, 2022 (tier 1)

> "Розіграйте діалог-знайомство. Представтеся самі або представте когось третій особі."
> Source: Литвинова, Grade 7, 2024 (tier 1) — explicit dialogue roleplay instruction confirming the activity format

### Section: Три часи разом (Three Tenses Together)
> "Часи дієслова: Теперішній — дія, що відбувається в момент мовлення. Минулий — дія, що відбулася до моменту мовлення. Майбутній — дія, що відбуватиметься після моменту мовлення. Дієслова змінюються за: [минулий] родом, числом; [теперішній/майбутній] особою, числом."
> Source: Литвинова, Grade 7, 2024 (tier 1) — § 9 Часи дієслова, full paradigm table

> "Майбутній час: Складна (синтетична) і складена (аналітична) форми — від дієслів недоконаного виду: казати — казатиму, буду казати."
> Source: Караман, Grade 10, 2018 (tier 2) — confirms both synthetic and compound future

### Section: Моя історія (autobiographical narrative)
> "У мене нема жодного сумніву в тому, що я народився… Трапилася ця подія 1 листопада 1989 року в містечку Груні… Оддали мене в школу. Вчив мене хороший учитель… Скінчив школу."
> Source: Воронь, Grade 9, 2017 (tier 2) — Остап Вишня «Моя автобіографія» — a first-person life narrative using past tense across decades. Ideal model for the Taras story format in the plan.

### Section: Summary (signal words / tense markers)
> "Я роблю вчора уроки / Я робила завтра уроки / Я робитиму зараз уроки — Поміркуйте, чи правильно побудовані речення. Що в них не так? [answer: tense-adverb mismatch] — Час дієслова — це морфологічна ознака, що визначає відношення дії до моменту мовлення (зараз — у минулому — у майбутньому)."
> Source: Литвинова, Grade 7, 2024 (tier 1) — § 9, opening exercise. Direct textbook support for teaching temporal signal words (зараз / вчора / завтра → раніше / далі).

---

## Grammar Rules

Правопис 2019 does not contain entries on verb tense formation (that is morphology, covered in grammar textbooks, not orthography). However, textbooks confirm two relevant rules:

- **Past tense formation**: Основа інфінітива + суфікс -в- (masc.) / -ла (fem.) / -ло (neut.) / -ли (pl.) — Source: Заболотний Gr.7, Карaman Gr.10
- **Future compound**: буду/будеш/буде + infinitive (аналітична форма, from imperfective verbs) — Source: Zaharijchuk Gr.4, Zabolotnyi Gr.7
- **Future synthetic**: -тиму/-тимеш/-тиме (синтетична форма) — also valid. ⚠️ **Plan teaches ONLY the compound form (буду + infinitive).** This is pedagogically correct for A1 — synthetic future is A2 territory. No fix needed, but writer should NOT introduce synthetic forms.
- **Soft sign in verb forms**: Правопис rule confirmed via textbook (Avramenko Gr.7): -ться always with soft sign (живеться, вчиться); -шся without soft sign (вчишся). Relevant for any reflexive verbs used.

---

## Calque Warnings

- **"розповідати про себе"**: ✅ OK — natural Ukrainian, confirmed by Голуб Gr.5 textbook usage ("розповідь про себе" used directly). No calque.
- **"успіхів тобі!"**: ✅ OK — genuine Ukrainian farewell phrase (genitive plural as optative wish). Антоненко-Давидович does not flag it. Standard in Ukrainian communication etiquette.
- **"вчитися / навчатися"**: ✅ OK — both confirmed natural. Антоненко-Давидович (ad-125) explicitly confirms вчитися + genitive governs correctly: "вчити, вчитися, навчати, навчатися" all standard. Plan uses вчитися correctly.
- **"хотів вивчати українську"**: ✅ OK — хотіти + infinitive is standard Ukrainian construction. No Russian calque pattern detected.
- ⚠️ **"у вільний час" (Taras story)**: FLAG — Антоненко-Давидович prefers "на дозвіллі" over "у вільний час" (calque from рос. в свободное время). Recommend replacing with "на дозвіллі" or "вільного часу" in the Taras model story.

---

## CEFR Check

| Word | PULS Level | Status |
|---|---|---|
| народитися | **A2** | ⚠️ Above A1 — core narrative verb, justified as active stretch at A1.8 graduation |
| університет | A1 | ✅ On target |
| подорожувати | A1 | ✅ On target |
| програміст | A1 | ✅ On target |
| закінчити | A1 | ✅ On target |
| успіх | **A2** | ⚠️ Above A1 — thematic word, acceptable as receptive vocabulary |
| мрія | **A2** | ⚠️ Above A1 — thematic/aspirational word, acceptable as receptive vocabulary |
| дитинство | **B1** | ⚠️⚠️ Two levels above A1 — notable flag. Used in signal phrase "у дитинстві". Writer must gloss explicitly and keep passive (recognition only). |
| переїхати | **B1** | ⚠️⚠️ Two levels above A1 — narrative verb, core to story arc. Must be introduced with explicit support (translation + example). Keep passive at A1. |

**Summary of CEFR flags:**
- 5/9 checked words are at or above target level (A1)
- 2 words are B1 (переїхати, дитинство) — writer must treat these as **passive/receptive vocabulary** with explicit glossing, not production targets
- 3 words are A2 (народитися, успіх, мрія) — acceptable stretch at A1.8 graduation module; gloss on first use
- 4 words are solidly A1 ✅
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
# Verified Knowledge Packet: My Story
**Module:** my-story | **Phase:** A1.8 [Past, Future, Graduation]
**Textbook grades searched:** 5, 6, 7

---

## Dialogues

> **Source:** avramenko, Grade 7
> **Section:** Сторінка 56
> **Score:** 0.25
>
> 53
> •	 Прочитавши життєві відо-
> мості й розмістивши їх у 
> логічній (ча­совій) послідов-
> ності, ознайомтеся з біогра-
> фією письменника. 
> О	
> Андрій Чайковський народився в Галичині, яка тоді входила до 
> складу Австрійської імперії. 
> Ь	
> Вступив на філософський факультет Львівського університету, але 
> згодом перейшов на юридичний. 
> Н	
> Під час навчання в Самбірській гімназії Андрій входив до підпіль-
> ного товариства «Студентська громада». 
> А	
> Велику популярність здобули його прозові твори на історичну 
> (козацьку) тематику в романтичному стилі (повісті «За сестрою», 
> «Козацька помста», роман «Сагайдачний» та ін.). 
> Ю	 Читати навчався польською, бо українського букваря тоді не було. 
> К	
> Життя А.

> **Source:** avramenko, Grade 5
> **Section:** Сторінка 132
> **Score:** 0.50
>
> 132
> Єв­ген Гу­ца­ло на­ро­див­ся в с. Ста­рий Жи­во­тів на Він­нич­
> чи­ні в учи­тель­ській сім’ї: бать­ко вик­ла­дав ук­ра­їн­ську мо­ву 
> й лі­те­ра­ту­ру, ма­ма — хі­мію та бі­о­ло­гію. Ось звід­ки в Єв­ге­на 
> була та­ка лю­бов і до мо­ви, і до при­ро­ди. Ко­ли хлопчику бу­ло 
> чо­ти­ри ро­ки, розпо­ча­ла­ся Друга світова вій­на, яка не мог­ла 
> не поз­на­чи­ти­ся в май­бут­ньо­му на твор­чос­ті пись­мен­ни­ка.
> Та­лант до сло­ва в Єв­ге­на про­я­вив­ся ра­но. Якось тре­ба бу­ло 
> на­пи­са­ти твір на віль­ну те­му, і він за­люб­ки це зро­бив.

> **Source:** zabolotnyi, Grade 7
> **Section:** Сторінка 140
> **Score:** 0.33
>
> 138
> Розділ 3.  ЙДУЧИ ДОРОГАМИ ЖИТТЯ
> Розділ 3. 
> ЙДУЧИ ДОРОГАМИ ЖИТТЯ
> МУДРІСТЬ КОБЗАРЯ
> Тарас ШЕВЧЕНКО
> (1814–1861)
> Тарас Шевченко народився 9 берез-
> ня 
> 1814 
> р. 
> в 
> селі 
> М;оринці 
> на 
> Черкащині. Дитячі роки  пройшли в 
> селі Кир;илівці (тепер – Шевченкове). 
> Хлопець був кріпаком, тому вимуше-
> но 
> переїхав 
> разом 
> із 
> паном 
> Енгельгардтом спочатку до Вільна 
> (зараз Вільнюс – столиця Литви), 
> а згодом – до Петербурга, на довгі 
> роки залишаючи Україну. 
> 22 квітня 1838 року Тараса Шевченка звільнили з кріпацтва 
> (тоді йому було 24 роки). Уже наступного дня він став учнем 
> Петербурзької академії мистецтв. Усе це було, як уві сні або в 
> чарівній казці.

## Три часи разом (Three Tenses Together)

> **Source:** litvinova, Grade 7
> **Section:** Сторінка 41
> **Score:** 0.33
>
> Розділ 1  ДІЄСЛОВО
> 38
> § 9  Часи діє слова
> Вправа 48
> 1   Прочитайте речення 
> Я 
> роблю  
> вчора 
> уроки.
> Я 
> робила  
> завтра 
> уроки.
> Я 
> робитиму 
> зараз 
> уроки.
> 2   Поміркуйте, чи правильно побудовані речення  
> Що в  них не так?
> 3   Скоригуйте й  запишіть правильні варіанти 
> 4   Поміркуйте, у  якій частині діє слова закладено значення часу 
> Дієслова у формі дійсного способу виражають дію, що 
> відбувалася, відбувається або відбувати меться. Вони  мають 
> форми трьох часів: теперішнього, минулого та майбутнього.

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 220
> **Score:** 0.50
>
> 220
> Відомості із синтаксису й пунктуації. Обставина
> Якийсь час прабабуня жила з нами в місті. А потім зібра-
> ла речі й повернулася назад. «У Заліссі народилася, в Заліссі 
> й помру», — сказала мамі.
> Раз на рік я приїжджаю в гості. Мені частіше не можна, 
> «бо радіація» У цей день час летить, мов шалений. Не всти-
> гає прабабуня показати мені своє господарство: ягоди, гриби, 
> фрукти, овочі, — як час повертатися додому. А я ще навіть 
> з її сусідами не познайомилася. Сусідами прабабуня називає 
> ведмедів, лисиць, вовків, лосів і коней, які мешкають у лісі.
> 2. Знайдіть і випишіть обставини разом зі словами, від яких вони залежать .
> 3. З’ясуйте за  словником значення невідомих слів .
> 4. Що ви знаєте про Чорнобильську трагедію? Поділіться інформацією одне 
> з одним .
> Вправа 359
> 1.

> **Source:** kovalenko, Grade 6
> **Section:** Сторінка 209
> **Score:** 0.50
>
> часу минуло багато лiт, певно бiльше як тридцять. Я був тодi 
> невеличкий сiльський хлопчина i бiгав, граючись, по лiсах 
> i полях мойого рiдного села. Власне надiйшла весна, один iз перших гарних теплих днiв. Перший раз по довгiй зимовiй неволi в тiсних душних хатах 
> ми, сiльськi дiти, могли побiгати собi свобiдно. Ми вибiгли 
> на сiножать, що ще була гола i сiра вiд скиненої недавно зи-
> мової перини. Тiльки десь-не-десь прокльовувалася з землi 
> свiжа зелень: сквапливi острi листки тростини, ще позвиванi 
> в острi шила листки хрiну та лопухiв над потоком. Тiльки 
> в недалекiм лiсi сподом усе забiлiлося вiд дикого часнику, що 
> власне починав уже вiдцвiтати, вiд бiлих i синiх пiдлiшкiв.

## Моя історія (My Story)

> **Source:** mishhenko, Grade 7
> **Section:** Сторінка 57
> **Score:** 0.33
>
> 57
> розділ 2
> «Мені аж страшно,
> як згадаю оту хатину край села...». Дитинство поета
> Народився Т. Шевченко в селі Моринцях на Черкащині 9 березня 1814 ро -
> ку в кріпацькій родині. Згодом родина переїхала в село Кирилівку. У віці 
> 9 років він втратив матір, у 11 – батька. До 14 років жив у родичів, чужих 
> людей, пас череду, намагався знайти вчителя, аби опанувати мистецтво 
> малювання. У 14 років узятий до панських по коїв, згодом стає козачком 
> у молодшого пана Енгельгардта. Це просто перелік біографічних відомостей, а за ними – маленький 
> обда рований хлопчина, який думав, що небо тримається на високих за-
> лізних стовпах. Він навіть ходив їх шукати, бо дуже вже цікаво було дізнатись, як 
> вони підпирають небо.

## Summary

> **Source:** mishhenko, Grade 7
> **Section:** Сторінка 99
> **Score:** 0.50
>
> 11. Бува лихо, що плаче, а бува, що й скаче. 12. Яка гребля, такий млин; який батько, такий син. 13. Посієш 
> вчинок, виросте звичка. 14. Вже ж і в пеклі гірше не буде. 15. Луч-
> че птиці на сухій гілці, чим у золотій клітці. Визначте і перерахуйте у 
> про читаному вами творі 
> елементи композиції.

> **Source:** avramenko, Grade 7
> **Section:** Сторінка 51
> **Score:** 0.33
>
> 48
> 2.	 Випишіть дієслова. 
> Везти, марення, існуватимуть, зелений, тільки, кіно, дано, спориш, су-
> шиш, прохання, вітаю, осмисливши, єднаючи, їла, хвала, автомати, три-
> мати, ігноруючи, названо, веретено, іскритися, Марися, холодно, напува-
> ючи, надвоє, зненацька, емігрувати, клеймо, виспівуємо, тисни, екрани, 
> екранізувати, чвалає, хокей, кредо, експлуатуючи, початківець, шиєш.
> 	
> З перших букв виписаних слів складіть приказку.
> 3.	 Перепишіть речення та виконайте завдання. 
> 1. Подивилась ясно — заспівали скрипки! 2. Ліс мовчав у смутку, в чор-
> ному акорді. 3. Спустила хмарка на луги мережані подолки. 4. Усе спить 
> ще: і поле, і зорі безсилі… 5. Жито усміхнеться: тінь, тінь! (П. Тичина).
> А.	 Надпишіть над кожним дієсловом особу, число, час і рід (якщо є).

## Grammar Reference

> **Source:** avramenko, Grade 6
> **Section:** Сторінка 143
> **Score:** 0.50
>
> І якраз у яму 
> втрапить. А ми вже вириємо, постараємося.


## МійКлас Theory (miyklas.com.ua)

*Ukrainian school curriculum theory — use this terminology and teaching approach.*

### Дієслово: загальне значення, морфологічні ознаки
> **Source:** МійКлас — [Дієслово: загальне значення, морфологічні ознаки](https://www.miyklas.com.ua/p/ukrainska-mova/7-klas/diyeslovo-14736/diyeslovo-zagalne-znachennia-morfologichni-oznaki-sintaksichna-rol-38752)

### Теорія:

*www.ua.pistacja.tv*  
Загальне значення
**Звернімо увагу на слова у двох стовпчиках:**
 

| *** боротьба  *** |  *** боротися  *** | 
|---|---|
|  ***спів*** |   ***заспівати*** | 
|  ***синій*** |   ***синіти*** | 
| *** зелений*** |   ***зазеленіти  *** | 
*** *** 
**Якщо порівняти ці слова як частини мови, зробимо висновок:**
- слова «боротьба», «спів» означають назву дії і відповідають на питання ***що?***, отже,  це іменники;

- слова «синій», «зелений» вказують на ознаку і відповідають на питання *

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Dialogues` (~300 words)
- `## Три часи разом (Three Tenses Together)` (~300 words)
- `## Моя історія (My Story)` (~300 words)
- `## Summary` (~300 words)
- `## Підсумок` (~150 words)

Each section should follow the word budget specified. The total must reach 1200 words minimum.

---

## Content Rules

TARGET: 20-35% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: English prose — brief and clear. Show, don't tell.
- PARADIGM TABLES: Conjugation/declension tables with all cells Ukrainian.
- EXAMPLE LISTS: Ukrainian sentences in bulleted lists (each: Ukrainian — English gloss).
- DIALOGUES: Mini-dialogues in blockquotes with English gloss per line.
- PATTERN BOXES: Show transformations: `читати → читай → читайте`.
- INLINE: Ukrainian words/phrases bolded in English prose.
- STRUCTURAL RULE: Paragraphs are English with inline bold Ukrainian. Full Ukrainian sentences go in tables, bulleted lists, dialogues, or pattern boxes.
Ukrainian sentences max 10 words. Mix container types.

HARD GRAMMAR RULES (audit will reject violations):
- Max 10 words per Ukrainian sentence (STRICT — count every word)
- ONLY 1 clause per sentence (no compound sentences)
- Dative case FORBIDDEN (no мені, тобі, йому, їй, вам, їм, -ові/-еві endings)
  Exception: нам is taught as decodable vocabulary in M1 (reading drill word, not grammar)
  Exception (M15 what-i-like): Dative forms мені/тобі/йому/їй/нам/вам/їм allowed
    ONLY in the fixed construction «Мені подобається + noun/infinitive». Teach as a memorized
    chunk — do NOT explain dative case rules or paradigms.
- Instrumental case FORBIDDEN (no з другом, з мамою, -ом/-ою/-ем/-ею endings)
  Exception: M37 introduces basic Instrumental 'з' (кава з молоком)
- NO subordinate clauses: який/яка/яке, що-clause, коли, якщо, тому що, бо, щоб, поки are ALL BANNED
- Only imperfective aspect verbs
- No participles
- Allowed cases: Nominative, Accusative, Locative (from M30), Genitive (basics), Vocative

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
- Use callout boxes (:::tip, :::caution, :::note) sparingly — max 3 per module
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
  1. **Grandparent telling their life story — Я народився в селі (n, village). Ходив у школу (f). Зараз живу в місті (n, city). Працюю в лікарні (f, hospital). Буду відпочивати на дачі (f, dacha).**
     Speakers: Дідусь/Бабуся, Онуки
     Why: Three tenses with село(n), школа(f), місто(n), лікарня(f), дача(f)

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

GRAMMAR CONSTRAINTS (A1.8 — Past, Future & Graduation, M51-M60):
Full A1 grammar including past and future tense.

ALLOWED:
- Past tense (він читав, вона читала — gendered!)
- Future tense (я буду читати, ми будемо працювати)
- All cases, moods, and constructions from A1.1-A1.7
- Combining tenses in connected speech

BANNED: Participles, passive voice, complex literary constructions

### Vocabulary

**Required:** народитися (to be born), жити (to live), вчитися (to study), переїхати (to move), зараз (now), раніше (before/earlier), далі (further/next), розповідати (to tell/narrate)
**Recommended:** подорожувати (to travel), закінчити (to finish/graduate), дитинство (childhood, n), університет (university, m), програміст (programmer, m), успіх (success, m), мрія (dream, f), батьки (parents, pl)

### Pronunciation Videos

**Do NOT embed YouTube videos in your prose.** A downstream ENRICH tool automatically places pronunciation videos from the plan. If you embed `<YouTubeVideo>` components, they will be duplicated. Simply reference the videos' existence when relevant (e.g., "Watch the pronunciation video for this letter") but do NOT insert `<YouTubeVideo>` tags.

Available videos (for reference only — ENRICH handles placement):


---

### Style Reference (match this tone and structure)

> **(У магазині / At the store)**
> — Добрий день! Скільки коштує хліб? (Good day! How much does the bread cost?)
> — Дванадцять гривень. (Twelve hryvnias.)
> — Дякую! Ось, будь ласка. (Thanks! Here you go.)

Notice that the shopkeeper uses **Добрий день** — the formal greeting for strangers. If this were a friend, they would say **Привіт** instead.

The word **скільки** (how much/how many) is one of the most useful question words. It always pairs with the genitive case: **скільки коштує** (how much does it cost), **скільки часу** (how much time).

*Note: Short dialogues in Ukrainian with per-line English glosses. Grammar explained in English. Ukrainian sentences in blockquotes and bulleted lists.*



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
## Dialogues (~330 words total)

- P1 (~30 words): Scene-setter — introduce two people meeting for the first time and wanting to understand each other's full story: past, present, future.

- Dialogue 1 (~130 words): Multi-turn exchange between Maksym (Canadian-Ukrainian diaspora) and Oksana (Kyiv local). Covers all three tenses in one conversation:
  — Розкажи про себе! — Я народився в Канаді, у Торонто.
  — А зараз ти живеш тут? — Так, зараз я живу в Києві.
  — Чому ти переїхав? — Я хотів вивчати українську. Мої бабуся і дідусь з України.
  — А що ти будеш робити далі? — Я буду працювати тут і вчити мову.
  — Чудово! Успіхів тобі!
  Label each verb with its tense in a margin note: народився (past) / живу (present) / буду працювати (future).

- P2 (~20 words): Transition — now hear Anna tell HER story in three tenses, from birth to future dreams.

- Dialogue 2 (~130 words): Anna narrates her life to a new colleague:
  — Я народилася у Львові. Там я вчилася в школі.
  — Потім я переїхала в Київ і закінчила університет.
  — Зараз я працюю вчителькою і живу в центрі міста.
  — А що далі? — Я буду подорожувати! Я хочу побачити Японію.
  — І ти будеш вчити японську? — Може! Але спочатку — українська для тебе!
  Flow annotation: past (народилася, вчилася, переїхала, закінчила) → present (працюю, живу) → future (буду подорожувати, буду вчити).

- P3 (~20 words): Observation — notice how the story moves: past events first, then now, then dreams. That is the shape of every life story in Ukrainian.

---

## Три часи разом (Three Tenses Together) (~330 words total)

- P1 (~100 words): Present the three-part life story scaffold with a structured list (not a table — lists build reading skill):
  МИНУЛИЙ ЧАС — things that already happened: Я народився / народилася в... Я жив / жила в... Я вчився / вчилася... Я працював / працювала...
  ТЕПЕРІШНІЙ ЧАС — what is true right now: Зараз я живу в... Я працюю... Я вивчаю... Я люблю...
  МАЙБУТНІЙ ЧАС — what will come: Я буду працювати... Я буду вивчати... Я буду жити...
  Emphasise the gender split in past forms: -в (Я народивСЯ — masculine) vs. -ла (Я народиЛАся — feminine). Three examples each: народився/народилася, жив/жила, вчився/вчилася.

- P2 (~100 words): Signal words are the listener's roadmap. Each tense has its own set of signal words that tell the listener which tense is coming BEFORE they hear the verb:
  Past signals: раніше (before/earlier), у дитинстві (in childhood), коли я був/була маленьким/маленькою (when I was little), тоді (back then).
  Present signals: зараз (now), сьогодні (today), цього року (this year).
  Future signals: потім (then/later), далі (further/next), наступного року (next year), скоро (soon).
  Contrast pair to notice: Раніше я жив у Канаді. (past) vs. Зараз я живу в Україні. (present) — same verb root, opposite tense, different signal word.

- P3 (~60 words): Natural transition tip — Ukrainian speakers often use "А потім..." to move from past to present and "А далі..." to move from present to future. These two phrases are the hinges of a life story. Practice: Я народився в Одесі. А потім я переїхав у Київ. А далі — я буду подорожувати!

- Exercise (~70 words of framing + items): fill-in — use the signal word to choose the correct tense form (5 items):
  Раніше я ___ (жив / живу / буду жити) в Канаді.
  Зараз я ___ (працюю / працював / буду працювати) в університеті.
  Далі я ___ (буду вивчати / вивчав / вивчаю) українську мову.
  У дитинстві вона ___ (любила / любить / буде любити) читати.
  Сьогодні ми ___ (живемо / жили / будемо жити) в Україні.

---

## Моя історія (My Story) (~330 words total)

- P1 (~30 words): Introduction — now we read a full model story. Taras is a programmer from Odesa who moved to Kyiv. Read his story and notice how all three tenses flow together.

- P2 (~150 words): Taras's model story in continuous prose (no labels — the reader sees natural flow):
  Я народився в Одесі у тисяча дев'ятсот дев'яносто п'ятому році. Я жив там з батьками і сестрою. У дитинстві я ходив у школу і любив математику. Потім я переїхав у Київ і вчився в університеті.
  Зараз я живу в Києві. Я працюю програмістом. Я люблю свою роботу. У вільний час я граю у футбол і читаю книжки.
  Далі я буду подорожувати. Я буду вивчати англійську. І я буду жити в Києві — це моє місто!
  After the story: highlight the tense shifts in a short annotation: past verbs — народився, жив, ходив, любив, переїхав, вчився; present verbs — живу, працюю, люблю, граю, читаю; future constructions — буду подорожувати, буду вивчати, буду жити.

- Exercise 1 (~50 words of framing + items): ordering — put Taras's life events in chronological order (5 events provided scrambled):
  Я народився в Торонто.
  У дитинстві я жив з батьками.
  Потім я вчився в університеті.
  Зараз я живу в Києві і працюю програмістом.
  Далі я буду подорожувати.

- P3 (~70 words): Your turn — structured prompt guiding the learner to tell THEIR own story using the same scaffold:
  Start: Я народився / народилася в [місто/країна].
  Past: Я жив/жила... Я вчився/вчилася... (use at least 3 past verbs)
  Present: Зараз я живу... Я працюю... Я вивчаю українську, тому що...
  Future: Я буду... Я хочу... (use at least 3 future constructions)
  Target: 8–10 sentences. Use раніше / зараз / далі to signal each tense shift.

- Exercise 2 (~30 words of framing + items): fill-in — complete Anna's biography (4 items), choosing the correct tense form:
  Я ___ (народилася / народився / народилися) у Львові.
  Зараз я ___ (працюю / працювала / буду працювати) вчителькою.
  Наступного року я ___ (буду подорожувати / подорожувала / подорожую).
  Там я ___ (вчилася / вчилися / буду вчитися) в школі.

---

## Підсумок (~330 words total)

- P1 (~120 words): Grammar recap — three tenses side by side with the key patterns:
  Минулий час — past: add -в (masc), -ла (fem), -ло (neut), -ли (pl) to the verb stem: народи-В, народи-ЛА, жи-В, жи-ЛА, вчи-В-ся, вчи-ЛА-ся.
  Теперішній час — present: person endings: я живу, ти живеш, він/вона живе, ми живемо, ви живете, вони живуть.
  Майбутній час — future: буду + infinitive: я буду подорожувати, ти будеш працювати, він/вона буде вивчати.
  Key reminder: future тense at A1 always uses буду + infinitive — never a single conjugated form.

- P2 (~80 words): Signal words quick reference — three columns, one for each tense:
  МИНУЛИЙ: раніше, у дитинстві, тоді, колись, коли я був/була маленьким/маленькою, потім (when narrating past sequence).
  ТЕПЕРІШНІЙ: зараз, сьогодні, цього року, щодня.
  МАЙБУТНІЙ: далі, потім (when pointing forward), наступного року, скоро, я хочу + infinitive.
  Tip: the same word потім can signal past sequence OR future — context tells you which.

- P3 (~80 words): Life story core vocabulary — words every story needs:
  народитися (to be born) — я народився / народилася
  жити (to live) — я жив / жила / живу / буду жити
  вчитися (to study) — я вчився / вчилася / вчуся / буду вчитися
  переїхати (to move/relocate) — я переїхав / переїхала (past only at A1 — perfective)
  подорожувати (to travel) — я буду подорожувати
  закінчити (to finish/graduate) — я закінчив / закінчила
  розповідати (to tell/narrate) — я розповідаю / розповідав / буду розповідати

- Self-check (~50 words): Bulleted questions for self-assessment:
  • Can you say where you were born in Ukrainian? (Я народився/народилася в...)
  • Can you describe where you live NOW? (Зараз я живу в...)
  • Can you say THREE things you did in the past? (-в/-ла forms)
  • Can you say TWO things you plan to do in the future? (буду + infinitive)
  • Can you tell your whole story in 8 sentences, using signal words?

Grand total: ~1320 words
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
