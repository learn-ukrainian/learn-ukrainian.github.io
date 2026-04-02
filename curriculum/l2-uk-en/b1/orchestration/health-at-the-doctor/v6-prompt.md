<correction_directive>
CRITICAL: Your previous attempt failed the following checks. Write the module FROM SCRATCH. All original constraints still apply.

- FIX: Missing section heading: 'Підсумок: здоров'я українською'
- NOTE: Missing 1/16 required vocab: призначити (to prescribe — perfective)
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

Write the full prose content for module **16: Здоров'я і медицина** (B1, B1.2 [Morphophonemics & Noun Subclasses]).

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
module: b1-016
level: B1
sequence: 16
slug: health-at-the-doctor
version: '3.0'
title: "Здоров'я і медицина"
subtitle: "У лікаря — від скарг до рецепта"
focus: communication
pedagogy: PPP
phase: "B1.2 [Morphophonemics & Noun Subclasses]"
word_target: 4000
objectives:
- "Learner can describe symptoms and health complaints in Ukrainian
  using appropriate medical vocabulary (біль, кашель, нежить, температура)"
- "Learner can conduct a basic doctor-patient dialogue in Ukrainian:
  describing symptoms, answering questions, understanding diagnosis"
- "Learner can navigate a pharmacy interaction: asking for ліки,
  understanding рецепт and дозування, describing алергія"
- "Learner can apply morphophonemic knowledge from M08-M15 to medical
  vocabulary: біль-безболісний (чергування), ліки (pluralia tantum),
  здоров'я-здоровий (word formation)"
- "Learner can use correct case government with medical verbs:
  скаржитися на (+ Зн.), хворіти на (+ Зн.), лікуватися від (+ Р.)"
dialogue_situations:
- setting: 'At a поліклініка (f, polyclinic) in Київ — detailed medical consultation:
    У мене болить голова (f) вже тиждень. Температура тіла (n, body) — 37.5. Виписую
    вам рецепт (m, prescription) на ліки (pl, medicine). Зверніться до хірурга (m,
    surgeon).'
  speakers:
  - Пацієнт
  - Терапевт (GP)
  motivation: 'Medical vocabulary + cases: болить голова(f), рецепт на ліки, до хірурга(gen)'
content_outline:
- section: "Здоров'я і самопочуття"
  words: 650
  points:
  - "Core vocabulary introduction (90%+ Ukrainian prose):
    Здоров'я — найважливіше, що є в людини. Коли ми здорові, ми не
    думаємо про лікарів. Але коли хворіємо, нам потрібна допомога.
    Key lexical family: здоров'я (noun) → здоровий (adj) →
    одужати (verb, perfective) → одужувати (verb, imperfective).
    Morphophonemic link: здоров'я shows апостроф after губний [в]
    before [й] — same pattern as м'який знак rules from Phase 1."
  - "Describing how you feel — key constructions:
    Я добре почуваюся. / Мені погано. / У мене болить голова.
    Мені нудить. / Я кашляю. / У мене температура.
    Case patterns: у мене + називний (possession), мені + present
    (dative experiencer), болить + називний (what hurts).
    Connection to M08 чергування: біль — болить — безболісний
    (і→о alternation in open syllable)."
  - "Body parts vocabulary review at B1 level with morphophonemic awareness:
    голова — головний (о→о, no alternation — stress stable),
    ніс — носа (і→о чергування in закритий/відкритий склад),
    вухо — у вусі (х→с чергування from M09),
    око — в оці (к→ц чергування from M09).
    These are the same alternation patterns, now applied to body vocabulary."
- section: "У лікаря: діалог"
  words: 800
  points:
  - "Model dialogue 1 — Прийом у терапевта (appointment with GP):
    Full Ukrainian dialogue demonstrating the consultation flow:
    реєстрація (registration) → скарги (complaints) → огляд (examination)
    → діагноз (diagnosis) → призначення (prescription).
    Лікар: На що скаржитесь? (What are you complaining about?)
    Пацієнт: У мене болить горло і є температура.
    Лікар: Як давно? Пацієнт: Три дні.
    Лікар: Відкрийте рота. Скажіть 'а'. Дихайте глибоко."
  - "Model dialogue 2 — У стоматолога (at the dentist):
    Specialized vocabulary: зуб (tooth), ясна (gums), пломба (filling),
    знеболювальне (anesthetic). Grammatical focus: наказовий спосіб
    in medical commands (відкрийте, покажіть, не рухайтеся).
    Morphophonemic link: зуб — зуби (no alternation) vs зуб — зубний
    (word formation with suffix -н-)."
  - "Key medical verbs and their case government:
    скаржитися на + Зн. (complain about): скаржуся на головний біль.
    хворіти на + Зн. (be sick with): хворіти на грип.
    лікуватися від + Р. (be treated for): лікуватися від застуди.
    оглянути + Зн. (examine): лікар оглянув пацієнта.
    призначити + Зн. (prescribe): лікар призначив ліки.
    одужати від + Р. (recover from): одужати від хвороби."
- section: "Спеціалісти та обстеження"
  words: 650
  points:
  - "Medical specialists vocabulary:
    терапевт (GP), хірург (surgeon), стоматолог (dentist),
    окуліст (eye doctor), педіатр (pediatrician), лікар (doctor).
    Word formation link from M12: лікар belongs to the -ар suffix
    group (II відміна м'яка група). Морфологічна паралель:
    пекар, школяр, лікар — all agent nouns with -ар."
  - "Types of обстеження:
    аналіз крові (blood test — note: крові is родовий III відміна from M14),
    рентген (X-ray), УЗД (ultrasound — abbreviation),
    вимірювання тиску (blood pressure measurement),
    вимірювання температури (temperature measurement).
    Grammar focus: родовий відмінок in medical contexts (аналіз чого?
    крові, сечі; вимірювання чого? тиску, температури)."
  - "Reading practice: a medical report summary in Ukrainian.
    Learners extract key information: діагноз, симптоми, призначення.
    Focus on reading comprehension of medical register Ukrainian."
- section: "В аптеці"
  words: 700
  points:
  - "Pharmacy dialogue:
    Пацієнт: Доброго дня. У мене рецепт від лікаря.
    Аптекар: Покажіть, будь ласка. Ось ваші ліки.
    Пацієнт: Скільки разів на день приймати?
    Аптекар: Тричі на день після їжі.
    Key vocabulary: рецепт, ліки (pluralia tantum from M15!),
    таблетка, мазь, укол, ін'єкція, щеплення, краплі (also pl. tantum),
    дозування (dosage)."
  - "Ліки — a grammar showcase from M15:
    ліки is pluralia tantum: ці ліки (not *цей лік in medical sense),
    ліків (родовий), лікам (давальний), ліками (орудний).
    Other pluralia tantum in medicine: краплі (drops), вершки (cream —
    as in cosmetic), парфуми (perfume — but this is from M15 general)."
  - "Morphophonemic connections in medical vocabulary:
    біль → безболісний (prefix без- + о-alternation),
    хвороба → хворіти → хворий (word family),
    здоров'я → здоровий → оздоровлення (word family with апостроф),
    лікар → лікувати → лікування → ліки (word family, -ар agent noun).
    These word families reinforce the word-formation patterns from M12 and M44."
- section: "Хвороби та симптоми"
  words: 700
  points:
  - "Common illnesses:
    застуда (cold), грип (flu), алергія (allergy),
    запалення (inflammation), нежить (runny nose), кашель (cough).
    Describing symptoms in Ukrainian:
    У мене нежить і кашель. Мені боляче ковтати. Я чхаю.
    У мене висока температура — тридцять вісім і п'ять."
  - "Grammar focus — нежить and кашель as II відміна masculine nouns:
    нежить — нежитю (давальний, м'яка група: like учитель),
    кашель — кашлю (давальний, м'яка група).
    Contrast with III відміна: хвороба is I відміна (feminine -а ending),
    but біль is II відміна masculine (not III!).
    This reinforces the відміна identification skills from M13-M14."
  - "Prevention vocabulary: щеплення (vaccination), імунітет (immunity),
    профілактика (prevention), обстеження (examination/checkup).
    Advice constructions: Вам треба зробити щеплення. Потрібно здати
    аналізи. Раджу більше відпочивати. Не забувайте пити воду."
- section: "Підсумок: здоров'я українською"
  words: 500
  points:
  - "Communicative competence check — can the learner:
    1. Describe symptoms to a doctor?
    2. Understand a diagnosis and prescription?
    3. Navigate a pharmacy interaction?
    4. Use correct case government with medical verbs?
    Morphophonemic integration check — can the learner:
    1. Identify чергування in medical words (біль-болить)?
    2. Recognize pluralia tantum (ліки, краплі)?
    3. Apply word formation patterns (лікар-лікувати-лікування)?"
  - "Self-check: Дайте відповіді українською:
    1. На що ви скаржитеся? (describe three symptoms)
    2. Які спеціалісти працюють у поліклініці?
    3. Що каже аптекар, коли дає ліки?
    4. Утворіть слова від кореня 'здоров-'.
    Preview: M17 — Контрольна робота 2 (review M08-M16)."
vocabulary_hints:
  required:
  - "здоров'я (health — noun, III відміна pattern with апостроф)"
  - "лікар (doctor — II відміна, -ар agent suffix)"
  - "хвороба (disease — I відміна feminine)"
  - "біль (pain — II відміна masculine, чергування: біль-болить)"
  - "температура (temperature — I відміна)"
  - "кашель (cough — II відміна masculine, м'яка група)"
  - "нежить (runny nose — II відміна masculine)"
  - "ліки (medicine — pluralia tantum)"
  - "рецепт (prescription)"
  - "аптека (pharmacy — I відміна)"
  - "діагноз (diagnosis — II відміна)"
  - "симптом (symptom — II відміна)"
  - "скаржитися (to complain — на + Зн.)"
  - "лікувати (to treat — imperfective)"
  - "одужати (to recover — perfective)"
  - "призначити (to prescribe — perfective)"
  recommended:
  - "пацієнт (patient — II відміна)"
  - "лікарня (hospital — I відміна)"
  - "поліклініка (clinic — I відміна)"
  - "терапевт (GP/therapist — II відміна)"
  - "хірург (surgeon — II відміна)"
  - "стоматолог (dentist — II відміна)"
  - "застуда (cold — I відміна)"
  - "грип (flu — II відміна)"
  - "алергія (allergy — I відміна)"
  - "щеплення (vaccination — neuter, -ення suffix)"
  - "обстеження (examination — neuter, -ення suffix)"
  - "таблетка (pill/tablet — I відміна)"
activity_hints:
- type: quiz
  focus: "Match symptoms to the correct specialist (головний біль → терапевт, зубний біль → стоматолог)"
  items: 12
- type: fill-in
  focus: "Complete doctor-patient dialogue with correct case forms (скаржитися на..., лікуватися від...)"
  items: 12
- type: match-up
  focus: "Match medical word families: лікар-лікувати-ліки, біль-болить-безболісний"
  items: 12
- type: sentence-builder
  focus: "Build sentences describing symptoms and medical actions using correct grammar"
  items: 12
- type: error-correction
  focus: "Fix case government errors in medical sentences (*скаржитися від, *хворіти з)"
  items: 12
connects_to:
- "b1-008 (Чергування голосних — біль-болить, ніс-носа: і→о alternation)"
- "b1-009 (Чергування приголосних — вухо-у вусі, око-в оці: к→ц, х→с)"
- "b1-012 (Іменники на -ар — лікар as agent noun pattern)"
- "b1-015 (Іменники у множині — ліки, краплі as pluralia tantum)"
- "b1-014 (Жіночий рід III відміна — кров, мазь as III відміна nouns)"
prerequisites:
- "b1-015 (Pluralia tantum — ліки, краплі in pharmacy context)"
- "b1-008 (Чергування голосних — morphophonemic awareness for medical vocab)"
grammar:
- "Case government: скаржитися на + Зн., хворіти на + Зн., лікуватися від + Р."
- "Наказовий спосіб in medical commands: відкрийте, покажіть, дихайте"
- "Pluralia tantum in medicine: ліки, краплі"
- "Word formation families: здоров'я-здоровий, біль-болить-безболісний, лікар-лікувати"
- "Body part alternations: ніс-носа (і→о), вухо-у вусі (х→с), око-в оці (к→ц)"
- "Давальний of experience: мені боляче, мені нудить"
register: розмовний
references:
- title: "Заболотний Grade 10, p.19"
  notes: "Text 'Коли слово лікує': doctor-patient interaction with medical
    vocabulary (біль, симптом, остеохондроз, пацієнт, лікар)."
- title: "Авраменко Grade 8, p.38"
  notes: "Paronym distinction: доктор (academic degree) vs лікар (medical doctor).
    Important for correct usage in medical context."
- title: "Голуб Grade 5, p.24"
  notes: "Health-themed text about правильне харчування, здоров'я, фізичні вправи.
    Vocabulary: кров'яний тиск, стрес, здорові продукти."
- title: "Заболотний Grade 11, p.166"
  notes: "Text 'Здоров'я у твоїх руках' with health vocabulary in context
    of punctuation exercises."

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
- Confirmed: здоров'я, лікар, хвороба, біль, температура, кашель, нежить, ліки, рецепт, аптека, діагноз, симптом, скаржитися, лікувати, одужати, призначити, пацієнт, лікарня, поліклініка, терапевт, хірург, стоматолог, застуда, грип, алергія, щеплення, обстеження, таблетка, мазь, укол, ін'єкція, краплі.
- Not found: None (All words verified).

## Textbook Excerpts
### Section: Здоров'я і самопочуття
> Здоров’я людини значною мірою залежить від харчування... Пам’ятаймо, що їжа повинна бути нашими ліками, а не ліки – їжею.
> Source: Zabolotnyi, Grade 11

### Section: У лікаря: діалог
> Після кількох запитань й огляду лікар зазначив, що, імовірно, біль є симптомом загострення остеохондрозу... спілкування з пацієнтом у 70–80 % випадків допомагає поставити правильний діагноз.
> Source: Zabolotnyi, Grade 10

### Section: Спеціалісти та обстеження
> Стоматолог — лікар (лікарка), що лікує зуби... Хірург — лікар (лікарка), що оперує хворих.
> Source: Vashulenko, Grade 3

### Section: В аптеці
> Це — медунка... знайомся, звіробій. Лікує сто хвороб! Заболить живіт, серце або кашляти почнеш — він стане в пригоді.
> Source: Zaharijchuk, Grade 1 (Folk context)

### Section: Хвороби та симптоми
> Холод... змушує організм посилювати свій імунітет. Холод пришвидшує циркулювання крові... допомогає покращити активність мозку.
> Source: Zabolotnyi, Grade 5

## Grammar Rules
- Apostrophe in здоров'я: Правопис §7.1 — Апостроф пишемо перед я, ю, є, ї після букв на позначення губних приголосних б, п, в, м, ф.
- II Declension Soft Group: Правопис §31 — Іменники на -ар, -ир належать до м’якої групи, якщо -ар, -ир завжди ненаголошені (аптекар) або наголос переходить на закінчення (перукар — перукаря).
- Alternation Г-З, К-Ц, Х-С: Правопис §12 — У місцевому відмінку: вухо — у вусі, око — в оці, горло — у горлі (no alternation for л, but х→с, к→ц).
- Vowel Alternation (і-о): Правопис §26 — Чергування о, е з і в закритому складі (біль — болю, болить).

## Calque Warnings
- ліки від хвороб: CALQUE — по-українському треба ставити прийменник проти: "Ліки проти ревматизму".
- хворий чим: CALQUE — прикметник хворий вимагає після себе прийменника на з іменником у знахідному відмінку: "хворий на грип".
- відчувати себе: OK but suboptimal — для самопочуття краще використовувати "почуватися".
- лікарський: AMBIGUOUS — "лікарський" (belonging to doctor, e.g., халат) vs "лікувальний" (remedial, e.g., косметика).

## CEFR Check
- діагноз: B1 — OK
- терапевт: B1 — OK
- симптом: A2 — OK
- щеплення: B2 (in some contexts) — OK for B1 module as it's thematic.
- обстеження: B1 — OK
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
# Verified Knowledge Packet: Здоров'я і медицина
**Module:** health-at-the-doctor | **Phase:** B1.2 [Morphophonemics & Noun Subclasses]
**Textbook grades searched:** 1, 2, 3, 5

---

## Здоров'я і самопочуття

> **Source:** golub, Grade 5
> **Section:** Сторінка 24
> **Score:** 0.50
>
> 24
> 1. Перебування на свіжому повітрі не лише знижує 
> кров’яний тиск і покращує функції пам’яті, а й допомагає 
> подолати стрес (Г. Браун). 2. Серце зношується злобою. 
> Сиріч — гнівом, гордощами, заздрістю, невір’ям, непрощен-
> ням (М. Дочинець). 3. Завдяки корисній їжі ми почуваємося 
> енергійними. 4. Подумай, скільки свіжих, здорових продук-
> тів різних кольорів ти можеш з’їсти впродовж дня. 
> 5. Дослідження доводять, що регулярні фізичні вправи пози-
> тивно впливають на здоров’я, а також із допомогою них 
> можна підвищити рівень IQ (Д. Браун, Н. Кей).
>  
> ІІ   Якою темою об’єднані речення? Чому здоров’я і здоровий 
> спосіб життя вважають найвищими цінностями? Додайте 
> кілька своїх порад щодо здорового способу життя.
> 53
>   За словником омонімів дайте відповіді на запитання-загадки.
> 1.

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 35
> **Score:** 0.50
>
> 35
>  
> 	 Які ще теми прислів’їв можуть бути?
>  
> 	 Обговоріть! Яке повчання містить кожне прислів’я?
>  
> 	 Поміркуйте і з’ясуйте, про які риси характеру людини йдеться 
> у двох перших приказках.
>  
> 	 Які прислів’я і приказки ти іще знаєш?
> * * *
> 	 	
> Дає і з рук не випускає.
> 	 	
> Язик без кісток, що хоче, те й лопоче.
> 	 	
> Здоров’я — найдорожчий скарб.
> 	 	
> Без діла псується сила.
> 	 	
> Хто хвалиться, той кається.
> 	 	
> Хто діло робить, а хто ґави ловить.
> 	 	
> Гостре словечко ранить сердечко.
> 	 	
> Згода дім будує, а незгода — руйнує.
> 	 	
> Дружба та братство — найбільше багатство.
> 	 	
> Де праця — там густо, а де лінь — там пусто.
> Приказка — це влучний вислів, який стверджує 
> факт.

## У лікаря: діалог

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 139
> **Score:** 0.50
>
> 139
> 3   Дай письмові відповіді на запитання. Записуй числівники словами. 
>   Що називають числівники? На яке питання відповідають?
>   Запиши утворений текст, подаючи числівники словами. 
> О котрій годині ти прокидаєшся? 
> Скільки часу ти одягаєшся?
> Коли виходиш із дому до школи?
> Скільки часу витрачаєш на дорогу?
> О котрій годині розпочинається  
> перший урок?
> О котрій годині ти повертаєшся додому  
> зі школи?
> Стоматолог — лікар (лікарка), що лікує зуби.
> Чистити зуби необхідно у (3 напрямки): спочатку — ззовні, 
> потім — зсередини, а вкінці — по жувальній поверхні. 
> Щітку слід тримати під кутом (45 градуси). Стоматологи радять 
> чистити зуби не менше (3 хвилини), а зубну щітку міняти кожні 
> (2–3 місяць).
> 	 	
> 4   Прочитай текст, ставлячи слова в дужках у потрібній формі.

> **Source:** golub, Grade 5
> **Section:** Сторінка 230
> **Score:** 0.50
>
> 230
> Шукаємо відповіді на запитання:
> Як стати гарним співрозмовником / гарною співрозмовницею?
> Відповідно до поставленого запитання сформулюйте особис-
> ті цілі.
> 521   Прочитайте «слова дня». Що вони означають? Чи всі вони можуть 
> поєднуватися зі словосполученнями «гарний співрозмовник», 
> «гарна співрозмовниця»? Чому?
> Про що «говорить» усмішка? Вона повідомляє: «Ви мені 
> подобаєтеся! Мені приємно спілкуватися з вами! Я радий / 
> рада вас бачити!» Усміхайтеся!
> 522   Розгляньте світлини. Які ознаки гарного співрозмовника очевид-
> ні? Назвіть їх.
> 523   Складіть діалог двох співрозмовників / співрозмовниць, один / 
> одна з яких любить осінь, а другий / друга — літо, використовую-
> чи подані речення.

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 54
> **Score:** 0.33
>
> 54
> Навчаюся доречно вживати слова в мовленні 
> Хто охороняє здоров’я дерев? Це 
> робить дятел. Цілий день проводить 
> лісовий лікар медичний огляд своєї 
> ділянки. Птах перелітає з дерева на 
> дерево, заглядає в кожну щілину. Від 
> гострого дзьоба незвичайного хірурга 
> не сховатися жодній шкідливій комасі 
> (За Юрієм Старостенком).
> Рожева  чайка
> Рожева чайка — окраса Арктики. Наче яскрава квітка, 
> ширяє рожева чайка серед суворої природи Півночі. Рожева 
> чайка харчується рибою. У незамерзлих ополонках Північного 
> Льодовитого океану проводить рожева чайка більшу частину 
> свого життя. 
> 6   Прочитай.

## Спеціалісти та обстеження

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 139
> **Score:** 0.50
>
> 139
> 3   Дай письмові відповіді на запитання. Записуй числівники словами. 
>   Що називають числівники? На яке питання відповідають?
>   Запиши утворений текст, подаючи числівники словами. 
> О котрій годині ти прокидаєшся? 
> Скільки часу ти одягаєшся?
> Коли виходиш із дому до школи?
> Скільки часу витрачаєш на дорогу?
> О котрій годині розпочинається  
> перший урок?
> О котрій годині ти повертаєшся додому  
> зі школи?
> Стоматолог — лікар (лікарка), що лікує зуби.
> Чистити зуби необхідно у (3 напрямки): спочатку — ззовні, 
> потім — зсередини, а вкінці — по жувальній поверхні. 
> Щітку слід тримати під кутом (45 градуси). Стоматологи радять 
> чистити зуби не менше (3 хвилини), а зубну щітку міняти кожні 
> (2–3 місяць).
> 	 	
> 4   Прочитай текст, ставлячи слова в дужках у потрібній формі.

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 54
> **Score:** 0.25
>
> 54
> Навчаюся доречно вживати слова в мовленні 
> Хто охороняє здоров’я дерев? Це 
> робить дятел. Цілий день проводить 
> лісовий лікар медичний огляд своєї 
> ділянки. Птах перелітає з дерева на 
> дерево, заглядає в кожну щілину. Від 
> гострого дзьоба незвичайного хірурга 
> не сховатися жодній шкідливій комасі 
> (За Юрієм Старостенком).
> Рожева  чайка
> Рожева чайка — окраса Арктики. Наче яскрава квітка, 
> ширяє рожева чайка серед суворої природи Півночі. Рожева 
> чайка харчується рибою. У незамерзлих ополонках Північного 
> Льодовитого океану проводить рожева чайка більшу частину 
> свого життя. 
> 6   Прочитай.

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 239
> **Score:** 0.50
>
> 236
> Додаток 2
> СЛОВНИЧОК ПАРОНІМІВ
> Військовий // воєнний
> Військовий – який стосується війська. Військовий лікар, військова 
> техніка, форма. 
> Воєнний – який стосується війни. Воєнний час.
> Дружний // дружній
> Дружний – який відбувається одночасно, злагоджено, спільно; 
> пов’язаний дружбою і згодою. Дружний колектив.
> Дружній – який ґрунтується на дружбі, прихильності, взаємно 
> доброзичливий. Дружній погляд.
> Економічний // економний
> Економічний – який стосується економіки. Економічний спад.
> Економний – ощадливий, який бережливо витрачає гроші, сили; 
> оснований на економії. Економна людина.
> Лікувати // лічити
> Лікувати – застосовувати ліки та інші засоби припинення болю, за-
> хворювання. Лікувати хворого, лікувати травами.
> Лічити – називати числа в послідовному порядку, рахувати.

## В аптеці

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 139
> **Score:** 0.50
>
> 139
> 3   Дай письмові відповіді на запитання. Записуй числівники словами. 
>   Що називають числівники? На яке питання відповідають?
>   Запиши утворений текст, подаючи числівники словами. 
> О котрій годині ти прокидаєшся? 
> Скільки часу ти одягаєшся?
> Коли виходиш із дому до школи?
> Скільки часу витрачаєш на дорогу?
> О котрій годині розпочинається  
> перший урок?
> О котрій годині ти повертаєшся додому  
> зі школи?
> Стоматолог — лікар (лікарка), що лікує зуби.
> Чистити зуби необхідно у (3 напрямки): спочатку — ззовні, 
> потім — зсередини, а вкінці — по жувальній поверхні. 
> Щітку слід тримати під кутом (45 градуси). Стоматологи радять 
> чистити зуби не менше (3 хвилини), а зубну щітку міняти кожні 
> (2–3 місяць).
> 	 	
> 4   Прочитай текст, ставлячи слова в дужках у потрібній формі.

> **Source:** vashulenko, Grade 2
> **Section:** Сторінка 87
> **Score:** 0.33
>
> Числівники можуть називати і порядок предметів 
> під час лічби. Тоді вони відповідають

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Здоров'я і самопочуття` (~650 words)
- `## У лікаря: діалог` (~800 words)
- `## Спеціалісти та обстеження` (~650 words)
- `## В аптеці` (~700 words)
- `## Хвороби та симптоми` (~700 words)
- `## Підсумок: здоров'я українською` (~500 words)
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
  1. **At a поліклініка (f, polyclinic) in Київ — detailed medical consultation: У мене болить голова (f) вже тиждень. Температура тіла (n, body) — 37.5. Виписую вам рецепт (m, prescription) на ліки (pl, medicine). Зверніться до хірурга (m, surgeon).**
     Speakers: Пацієнт, Терапевт (GP)
     Why: Medical vocabulary + cases: болить голова(f), рецепт на ліки, до хірурга(gen)

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

**Required:** здоров'я (health — noun, III відміна pattern with апостроф), лікар (doctor — II відміна, -ар agent suffix), хвороба (disease — I відміна feminine), біль (pain — II відміна masculine, чергування: біль-болить), температура (temperature — I відміна), кашель (cough — II відміна masculine, м'яка група), нежить (runny nose — II відміна masculine), ліки (medicine — pluralia tantum), рецепт (prescription), аптека (pharmacy — I відміна), діагноз (diagnosis — II відміна), симптом (symptom — II відміна), скаржитися (to complain — на + Зн.), лікувати (to treat — imperfective), одужати (to recover — perfective), призначити (to prescribe — perfective)
**Recommended:** пацієнт (patient — II відміна), лікарня (hospital — I відміна), поліклініка (clinic — I відміна), терапевт (GP/therapist — II відміна), хірург (surgeon — II відміна), стоматолог (dentist — II відміна), застуда (cold — I відміна), грип (flu — II відміна), алергія (allergy — I відміна), щеплення (vaccination — neuter, -ення suffix), обстеження (examination — neuter, -ення suffix), таблетка (pill/tablet — I відміна)

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
## Здоров'я і самопочуття (~720 words total)
- P1 (~160 words): Introduction to the concept of health as the ultimate value (*найвищий скарб*). Explanation of the lexical family: *здоров'я* (noun) with the apostrophe after [в], *здоровий* (adjective), and the verb pair *одужувати* (imperfective) / *одужати* (perfective). Comparison to the Grade 3 proverb "Здоров’я — найдорожчий скарб".
- P2 (~150 words): Describing general well-being using *почуватися*. Contrasting *Я добре почуваюся* with *Мені погано*. Introduction of the Dative experiencer construction for physical sensations: *Мені нудить* (I feel nauseous) and *Мені боляче* (It hurts me).
- P3 (~170 words): Introduction to morphophonemic alternations (B1.2 focus) using the word *біль* (pain). Explain the і→о alternation in closed vs. open syllables: *біль* (closed) vs. *болить* (open). Discussion of the prefix *без-* in *безболісний* (painless) and how the alternation carries over to word formation.
- P4 (~160 words): Review of body parts with a focus on consonant alternations from M09: *вухо* (ear) → *у вусі* (х→с), *око* (eye) → *в оці* (к→ц), and *ніс* (nose) → *носа* (і→о alternation). Contrast with stable stems like *голова* → *головний*.
- Exercise: [match-up, focus: Medical word families and alternations (біль-болить, вухо-вусі), 12 items] (~80 words)

## У лікаря: діалог (~880 words total)
- P1 (~160 words): Setting the scene at a *поліклініка* (clinic). Vocabulary for the medical bureaucracy: *реєстрація* (registration), *черга* (queue), and *медична картка* (medical card). Explanation of the etiquette: *Хто останній?* (Who is last?) and *Можна зайти?* (May I enter?).
- P2 (~180 words): Model Dialogue 1 — The Consultation. A multi-turn dialogue between *Терапевт* and *Пацієнт*. Focus on the phrase *На що скаржитесь?* and the answer *Скаржуся на головний біль*. Emphasis on the case government: *скаржитися на + Accusative* (Знахідний відмінок).
- P3 (~160 words): The physical examination. Introduction of imperative forms (наказовий спосіб) used by doctors: *Відкрийте рота* (Open your mouth), *Дихайте глибоко* (Breathe deeply), *Покажіть горло* (Show your throat), and *Не рухайтеся* (Don't move).
- P4 (~150 words): Model Dialogue 2 — At the Dentist (*У стоматолога*). Specialized vocabulary: *зуб* (tooth), *ясна* (gums), *пломба* (filling), and *знеболювальне* (anesthetic). Use of the word *лікувати* in context: *Лікар лікує зуби*.
- P5 (~140 words): Discussion of the paronym *лікувати* (to treat) vs. *лічити* (to count) based on Avramenko Grade 8. Clarification that *лікар лікує пацієнта*, while *дитина лічить до десяти*.
- Exercise: [fill-in, focus: Complete doctor-patient dialogue with correct case forms (скаржитися на, хворіти на), 12 items] (~90 words)

## Спеціалісти та обстеження (~720 words total)
- P1 (~160 words): Overview of medical specialists: *хірург, окуліст, педіатр, гінеколог, травматолог*. Explanation of the term *лікар* and its female equivalent *лікарка*. Review of the agent suffix *-ар* from M12 (II declension, soft group): *лікар* belongs to the same paradigm as *пекар* or *школяр*.
- P2 (~170 words): Types of medical examinations (*обстеження*). Focus on *аналіз крові* (blood test) and *аналіз сечі* (urine test). Grammar note: *кров* is a III declension feminine noun (from M14), so the genitive is *крові*. Introduction of *УЗД* (ultrasound) and *рентген* (X-ray).
- P3 (~160 words): Measuring vitals. Vocabulary: *тиск* (pressure), *пульс* (pulse), and *температура*. Explain the construction *міряти тиск/температуру*. Mentioning the stable *о* in *тиск* → *тиску* (no alternation) vs. *біль* → *болю*.
- P4 (~140 words): Reading practice. A short simulated medical report summary in Ukrainian. Focus on identifying the *діагноз*, *симптоми*, and *призначення* (treatment plan).
- Exercise: [quiz, focus: Match symptoms to the correct specialist (зубний біль → стоматолог), 12 items] (~90 words)

## В аптеці (~770 words total)
- P1 (~160 words): Entering the *аптека*. Vocabulary: *аптекар/фармацевт* (pharmacist), *рецепт* (prescription), and *ліки* (medicine). Explain that *ліки* is a *pluralia tantum* (only plural) when referring to "medicine" in a medical sense (from M15).
- P2 (~150 words): Model Dialogue 3 — Buying medicine. Patient asks: *У вас є ці ліки за рецептом?* Pharmacist explains usage: *Приймати двічі на день після їжі* (Take twice a day after meals). Introduction of *дозування* (dosage).
- P3 (~180 words): Pharmacy inventory grammar showcase. Discussion of other *pluralia tantum* in medicine: *краплі* (drops), *вітаміни* (vitamins — usually plural), and the forms of *ліки* across cases: *немає ліків* (Genitive), *завдяки лікам* (Dative).
- P4 (~150 words): Forms of medication: *таблетка* (pill), *мазь* (ointment), *укол/ін'єкція* (injection), and *сироп* (syrup). Comparison of word families: *лікар → лікувати → лікування*.
- P5 (~130 words): Discussion of allergic reactions. *У мене алергія на...* + Accusative. Examples: *алергія на антибіотики*, *алергія на пилок*. Use of *протиалергійні засоби*.

## Хвороби та симптоми (~770 words total)
- P1 (~170 words): Common seasonal illnesses: *застуда* (cold), *грип* (flu), and *ангіна* (tonsillitis). Use of the verb *хворіти на...* + Accusative. *Я захворів на грип*. Contrast with *лікуватися від...* + Genitive. *Він лікується від застуди*.
- P2 (~180 words): Focus on *нежить* (runny nose) and *кашель* (cough). Both are II declension masculine nouns. *Нежить* is masculine (not feminine!), soft group: *сильний нежить*, *нежитю* (Dative). *Кашель* also masculine soft: *сильний кашель*, *кашлю*. This reinforces M13-M14 classification skills.
- P3 (~150 words): Describing symptoms in detail: *чхати* (to sneeze), *кашляти* (to cough), *ковтати* (to swallow). *Мені боляче ковтати*. Mentioning *запалення* (inflammation) as a neuter noun with the *-ення* suffix.
- P4 (~150 words): Prevention and immunity. Vocabulary: *щеплення* (vaccination), *імунітет* (immunity), *профілактика* (prevention). Use of advice verbs: *раджу* (I advise), *треба* (it is necessary), *варто* (it is worth).
- Exercise: [sentence-builder, focus: Build sentences describing symptoms and medical actions (У мене нежить, я хворію на грип), 12 items] (~120 words)

## Підсумок (~550 words)
- P1 (~150 words): Recap of communicative goals. Can you now describe your symptoms using *скаржитися на*? Can you identify the correct specialist? Can you navigate the pharmacy using *ліки* and *рецепт*?
- P2 (~150 words): Final review of morphophonemic highlights: the і→о alternation in *біль/болить*, the consonant shifts in *вухо/вусі* and *око/оці*, and the status of *нежить* as a masculine noun.
- P3 (~250 words): Self-check questions:
    - На що ви скаржитеся, якщо у вас висока температура і болить горло?
    - Як називається лікар, який лікує дітей?
    - Яке закінчення має слово «нежить» у давальному відмінку?
    - Назвіть три слова, що належать до родини слова «лікувати».
    - Як сказати «Take medicine three times a day» українською?
    - Preview of M17: Контрольна робота 2 (Checkup 2).

Grand total: ~4460 words
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
