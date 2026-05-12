<plan_reasoning section="Діалоги">
<word_budget>Target 300 words (270-330). One 65-word English intro framing reflexives + two blockquoted dialogues (~50 UK words + ~56 EN gloss + 8 name tokens) + 95-word closing English paragraph + 25-word transition. Tally ≈ 319.</word_budget>
<plan_vocab>Required lemmas grounded: прокидатися ("Я прокидаюся о сьомій."), вмиватися ("Вмиваюся, одягаюся і снідаю."), одягатися (same), снідати (same), йти ("коли ти йдеш на роботу?"), потім ("Що ти робиш потім?"). Recommended: навчатися, поспішати, пізно, вранці, дивитися, лежати.</plan_vocab>
<register>A1.3 ramp, 15-35% Ukrainian. English explanatory prose; Ukrainian only inside blockquoted dialogues with line-by-line English gloss. Ukrainian sentences ≤ 10 words. No teacher-framing phrases ("Let's", "We will", "Note that").</register>
<teaching_sequence>Wiki packet pedagogy/a1/my-morning.md :: Послідовність введення [S8] directs Step 1 = recognize reflexive in real context BEFORE the formal rule. Wiki :: Приклади з підручників [S5, ULP audio] grounds dialogue-style introduction over schematic drills.</teaching_sequence>
<verification_plan>VESUM-verify every dialogue surface form via verify_words. Russian-shadow on suspect lemmas. No literary quotes used — verify_quote not applicable.</verification_plan>
<verification_trace>
mcp__sources__verify_words(words=["прокидатися","прокидаюся","прокидаєшся","прокидається","вмиватися","вмиваюся","одягатися","одягаюся","снідати","снідаю","йти","йдеш","потім","субота","сьома","восьма","навчатися","навчаюся","поспішати","пізно","вранці","лежати","лежу","дивитися","дивлюся","телефон","гуляю"]) — all FOUND in VESUM.
mcp__sources__check_russian_shadow(word="вмиватися") — matches_russian=false (0.0).
mcp__sources__check_russian_shadow(word="потім") — matches_russian=false (0.0).
</verification_trace>
</plan_reasoning>

<plan_reasoning section="Дієслова на -ся">
<word_budget>Target 300 words (270-330). ~26 EN setup, ~53 UK verbatim Karaman quote, ~70 EN etymology bridge, ~22 EN table intro + ~12 UK paradigm cells, ~36 EN pronunciation intro, ~10 UK Захарійчук transcription block, ~46 EN closing rule. Tally ≈ 325.</word_budget>
<plan_vocab>Reuses прокидатися, вмиватися in paradigm table (full 1sg/2sg/3sg). Karaman quote introduces навчатися, закохатися, взуватися, боюся as standard reflexive examples. Захарійчук transcription block contains прокидається, хлюпається, спиняєшся, навчаєшся.</plan_vocab>
<register>15-35% Ukrainian. English prose explains; Ukrainian appears only inside verbatim textbook blockquotes (citation metadata), the paradigm table, and inline-bolded lemma mentions in English prose. No flowing prose in Ukrainian. No teacher framing.</register>
<teaching_sequence>Karaman 10 клас с. 176 supplies the canonical rule + etymology (chunk 10-klas-ukrmova-karaman-2018_s0315, retrieved verbatim). Захарійчук 4 клас с. 163 supplies the pronunciation table (chunk 4-klas-ukrmova-zaharijchuk_s0162, retrieved verbatim). Wiki Послідовність введення Steps 2-4 — base paradigm → -ся overlay → pronunciation rule.</teaching_sequence>
<verification_plan>search_text supplied verbatim chunks for both citations, so verify_source_attribution is redundant here. verify_words covers paradigm and pronunciation-table forms.</verification_plan>
<verification_trace>
mcp__sources__search_text(query="зворотні дієслова суфікс -ся -сь дія спрямована на себе", limit=5) — returned 10-klas-ukrmova-karaman-2018_s0315 page 176 with verbatim rule beginning "Дієслова із суфіксом -ся(-сь), які виражають зворотну дію, називаються зворотними".
mcp__sources__search_text(query="Захарійчук дієслова -ся вимова правопис вправи", limit=5) — returned 4-klas-ukrmova-zaharijchuk_s0162 page 163 with verbatim transcription table [прокидайец':а] прокидається / [спиен айес':а] спиняєшся.
mcp__sources__search_text(query="вимова -шся -ться подовжений приголосний", limit=5) — corroborating Avramenko 7 клас с. 67 + Litvinova 5 клас с. 107.
mcp__sources__verify_words(words=["прокидаюся","прокидаєшся","прокидається","вмиваюся","вмиваєшся","вмивається","навчаєшся","спиняєшся","взуватися","закохатися"]) — all FOUND.
</verification_trace>
</plan_reasoning>

<plan_reasoning section="Мій ранок">
<word_budget>Target 300 words (270-330). ~12 EN setup, ~42 vocab list (7 UK lemmas + EN gloss), ~52 EN summary of pattern + ~5 UK refs, ~13 UK йти paradigm cells, ~17 EN stem note, ~16 sequence-words list (4 UK + 12 EN), ~10 EN time-order intro, ~34 monologue (14 UK + 20 EN), ~26 EN closing + ~9 UK. Tally ≈ 277.</word_budget>
<plan_vocab>Full plan-required vocab covered: прокидатися, вмиватися, одягатися, снідати, йти, спочатку, потім. Recommended added: збиратися, повертатися, після цього, нарешті. Irregular йти gets full paradigm (я йду, ти йдеш, він йде, ми йдемо, ви йдете, вони йдуть).</plan_vocab>
<register>15-35% Ukrainian. English prose introduces each lexical group; Ukrainian in bulleted lists (UK — EN gloss), paradigm table, and blockquoted monologue. Ukrainian sentences ≤ 10 words. No teacher-framing.</register>
<teaching_sequence>Wiki :: Словниковий мінімум [S1, S3] orders vocab by frequency (★★★ tier first). Wiki :: Послідовність введення Step 5 [S1, S3] expands to sequence adverbs after the grammar mechanic. йти irregular is plan-explicit for A1.3.</teaching_sequence>
<verification_plan>verify_words for full vocab + йти paradigm + sequence adverbs.</verification_plan>
<verification_trace>
mcp__sources__verify_words(words=["спочатку","потім","після","нарешті","вранці","пізно","рано","збиратися","повертатися","навчатися","поспішати","йти","йду","йдеш","йде","снідати","снідаю","роботу","школи","університету"]) — all FOUND. "після" returned both adv and prep readings; "після цього" used as prep phrase.
mcp__sources__verify_words(words=["вмивати","одягати","прокидати","навчати","мити","мию","миє"]) — all FOUND (transitive partners for match-up activity).
</verification_trace>
</plan_reasoning>

<plan_reasoning section="Підсумок">
<word_budget>Target 300 words (270-330). ~2 EN heading, ~24 EN "One" intro, ~21 pattern bullets (UK forms + EN arrows), ~12 EN paradigm bridge, ~80 EN "Two" pronunciation recap with ~6 UK verb refs, ~11 EN "Three" intro, ~12 sequence bullets, ~48 EN self-check directive, ~50 worked example (UK + EN gloss), ~24 EN closing + ~35 EN fusion note. Tally ≈ 300.</word_budget>
<plan_vocab>Consolidates прокидатися, вмиватися, одягатися, збиратися, снідати, йти as the "seven verbs minus two" core. Re-cycles all four sequence words (спочатку, потім, після цього, нарешті). Worked example block uses verified forms only.</plan_vocab>
<register>15-35% Ukrainian. Heavier English in recap prose; Ukrainian in pattern boxes, conjugation skeleton, transcription cheat sheet, sequence list, and worked-example blockquote with line-by-line gloss. No teacher framing.</register>
<teaching_sequence>Recap of Karaman G10 p.176 rule + Захарійчук G4 p.163 pronunciation rule — both already cited verbatim in §2. Wiki :: Послідовність введення closing step [S6, S8] frames the learner-produced 4-5 sentence morning narrative as the self-check.</teaching_sequence>
<verification_plan>No new lemmas. Re-uses verified forms only. verify_source_attribution(style_guide, "зворотні дієслова -ся") returned discusses=false — so I do NOT cite Антоненко-Давидович for the rule.</verification_plan>
<verification_trace>
mcp__sources__verify_source_attribution(source="style_guide", claim="зворотні дієслова -ся") — discusses=false, evidence_count=0. Confirms NOT to cite Антоненко-Давидович for the reflexive-verb rule.
mcp__sources__verify_words covered all forms in earlier batches.
mcp__sources__search_style_guide(query="сніданок завтрак") — no results, confirms сніданок is the standard form with no calque concern flagged.
mcp__sources__check_russian_shadow(word="сніданок") — matches_russian=false.
</verification_trace>
</plan_reasoning>

```markdown file=module.md
## Діалоги

Most Ukrainian verbs about a morning routine — waking, washing, getting dressed — end in **-ся** or **-сь**. These are reflexive verbs (in Ukrainian, **зворотні дієслова**): the action turns back on the person doing it. **Вмивати** is to wash someone else; **вмиватися** is to wash yourself. The two dialogues below show the pattern in context before section two pulls the rule out into the open.

Two roommates, Ліна and Настя, share an apartment. Their work weeks and weekends sound very different.

> **Ліна:** Коли ти прокидаєшся? — *When do you wake up?*
> **Настя:** Я прокидаюся о сьомій. — *I wake up at seven.*
> **Ліна:** Що ти робиш потім? — *What do you do next?*
> **Настя:** Вмиваюся, одягаюся і снідаю. — *I wash, get dressed, and have breakfast.*
> **Ліна:** А коли ти йдеш на роботу? — *And when do you leave for work?*
> **Настя:** О восьмій. — *At eight.*

Saturday morning has a different rhythm:

> **Настя:** У суботу я не поспішаю. — *On Saturday I'm not in a hurry.*
> **Настя:** Прокидаюся пізно. Лежу. Дивлюся в телефон. — *I wake up late. I lie there. I look at my phone.*
> **Ліна:** А я навчаюся вранці. — *I study in the morning.*
> **Ліна:** Потім гуляю. — *Then I take a walk.*

The same verb — **прокидаюся** — sits in both dialogues. On a workday it is the start of a chain (wake → wash → dress → eat). On Saturday it stands by itself, with nothing rushing after it. The shift is rhythmic, not lexical: same verb, very different soundtrack around it. Every bolded verb in both dialogues ends in **-ся** or **-сь**; the only verb in either dialogue without that suffix is **снідаю** (*I have breakfast*), because having breakfast is not an action a person performs on themselves. For the rest of this module, the **-ся** ending is a constant — it appears in every paradigm table below and in most of the activity items.

<!-- INJECT_ACTIVITY: act-2 -->

## Дієслова на -ся

The grammar fact, in one line: take a regular verb, add **-ся** at the end, and you have its reflexive partner. The Ukrainian school curriculum spells it out:

> Дієслова із суфіксом -ся(-сь), які виражають зворотну дію, називаються зворотними: навчатися, закохатися. Сучасний дієслівний суфікс -ся(-сь) — це давня коротка форма зворотного займенника себе в Зн. в. однини: Я не боюся. — Я ся не бою (діал.). Уживається -ся(-сь) після інфінітивного суфікса -ти(-ть) або закінчення в особових формах дієслова: вмивати — вмиватися, взувати — взуватися.
> — Караман, 10 клас, с. 176

The historical note is worth pausing on: the **-ся** ending was once the short reflexive pronoun **себе** in the accusative — *Я ся не бою* meant *Я не боюся*. That history is why Ukrainian conjugates the verb stem normally and parks the leftover pronoun at the end, rather than restructuring the whole verb. The endings before **-ся** are exactly the same set you would use for a non-reflexive first-conjugation verb.

In the present tense:

| Особа | прокидатися | вмиватися |
| --- | --- | --- |
| я | прокидаюся | вмиваюся |
| ти | прокидаєшся | вмиваєшся |
| він / вона | прокидається | вмивається |

<!-- INJECT_ACTIVITY: act-1 -->

The trap is pronunciation. Written **-шся** is pronounced as a single long soft **[с′:а]**; written **-ться** is pronounced as a single long soft **[ц′:а]**. The 4th-grade textbook lays this out side by side:

> Вимовляємо | Пишемо
> [прокидайец′:а] | прокидається
> [хл'упайец′:а] | хлюпається
> [спиен айес′:а] | спиняєшся
> [навчайес′:а] | навчаєшся
> — Захарійчук, 4 клас, с. 162

The т + с at the end fuses into a long **[ц′:]**, and ш + с fuses into a long **[с′:]**. These consonant assimilations are a feature of Ukrainian phonology, not a typing convenience. Spell the verb the long way; say the short way.

<!-- INJECT_ACTIVITY: act-5 -->

## Мій ранок

Seven verbs and four sequence words run the whole module. The verbs:

- **прокидатися** — *to wake up*
- **вмиватися** — *to wash your face and hands*
- **одягатися** — *to get dressed*
- **збиратися** — *to get yourself ready (gather your things)*
- **снідати** — *to have breakfast (not reflexive)*
- **повертатися** — *to come back, to return*
- **йти** — *to go (on foot — irregular)*

The first four take **-ся** and behave like **прокидатися** above. **Повертатися** is the same pattern, just longer in meaning. **Снідати** is the only one without **-ся**, because having breakfast is not an action one performs on oneself. **Йти** is the irregular one, and it is worth a paradigm of its own:

| Особа | йти |
| --- | --- |
| я | йду |
| ти | йдеш |
| він / вона | йде |
| ми | йдемо |
| ви | йдете |
| вони | йдуть |

The stem **йд-** does not appear anywhere in the infinitive, so this is a paradigm to memorize rather than derive.

The sequence words:

- **спочатку** — *first*
- **потім** — *then*
- **після цього** — *after that*
- **нарешті** — *finally*

Set the verbs in time order and the morning writes itself:

> Спочатку я прокидаюся. — *First I wake up.*
> Потім вмиваюся і одягаюся. — *Then I wash and get dressed.*
> Після цього снідаю. — *After that I have breakfast.*
> Нарешті йду на роботу. — *Finally I head to work.*

Four sentences, four cues, every step of the morning covered. Swap **йду на роботу** for **йду до школи** or **йду до університету** depending on where the morning ends.

<!-- INJECT_ACTIVITY: act-3 -->

<!-- INJECT_ACTIVITY: act-6 -->

<!-- INJECT_ACTIVITY: act-7 -->

## Підсумок

Three takeaways.

One — a reflexive Ukrainian verb is a regular verb plus **-ся** at the end. The endings before **-ся** are the standard first-conjugation set:

- я + **-юся** → **прокидаюся**
- ти + **-єшся** → **прокидаєшся**
- він / вона + **-ється** → **прокидається**

The same six endings, same person markers, no second paradigm to memorize.

Two — the spelling and the pronunciation diverge. Written **-шся** sounds like **[с′:а]**; written **-ться** sounds like **[ц′:а]**. There is no rule to "fix" this; it is what Ukrainian does at those consonant boundaries. The fusion is automatic in native speech — once you hear it a few dozen times the spelling stops being confusing. Until then, treat the pronunciation as a separate piece of information from the writing. Three of the seven verbs from section three — **прокидатися**, **вмиватися**, **одягатися** — show this fusion every time they are conjugated; **збиратися** does the same. **Снідати**, the only non-reflexive verb in the lineup, keeps its endings simple and never grows a long **[с′:]** or **[ц′:]**.

Three — four small words turn a list of verbs into a paragraph.

- **спочатку** — *first*
- **потім** — *then*
- **після цього** — *after that*
- **нарешті** — *finally*

The self-check: describe your own morning in four to five sentences, using all four cues and the verb forms from sections two and three. Worked example to anchor yours — substitute your own times and places:

> Спочатку я прокидаюся о сьомій. — *First I wake up at seven.*
> Потім вмиваюся і одягаюся. — *Then I wash and get dressed.*
> Після цього снідаю і збираюся. — *After that I have breakfast and get ready.*
> Нарешті йду до університету. — *Finally I head to the university.*

Try it out loud before you write it down. The long **[с′:]** and **[ц′:]** sounds want to be spoken, not just read.

<!-- INJECT_ACTIVITY: act-8 -->
```

```json file=activities.yaml
[
  {
    "id": "act-1",
    "type": "fill-in",
    "title": "Suffix -ся or no suffix",
    "instruction": "Add -ся to the verb stem if the action is reflexive (turning back on the speaker). Choose — (no suffix) if the verb is not reflexive.",
    "items": [
      {"sentence": "Я вмиваю__ холодною водою.", "answer": "ся", "options": ["ся", "—"]},
      {"sentence": "Ти одягаєш__ швидко.", "answer": "ся", "options": ["ся", "—"]},
      {"sentence": "Я прокидаю__ о сьомій.", "answer": "ся", "options": ["ся", "—"]},
      {"sentence": "Я снідаю__ о восьмій.", "answer": "—", "options": ["ся", "—"]},
      {"sentence": "Ти збираєш__ на роботу.", "answer": "ся", "options": ["ся", "—"]},
      {"sentence": "Я навчаю__ вранці.", "answer": "ся", "options": ["ся", "—"]},
      {"sentence": "Ти повертаєш__ пізно.", "answer": "ся", "options": ["ся", "—"]},
      {"sentence": "Я мию__ руки.", "answer": "—", "options": ["ся", "—"]},
      {"sentence": "Ти прокидаєш__ рано?", "answer": "ся", "options": ["ся", "—"]},
      {"sentence": "Я йду__ на роботу.", "answer": "—", "options": ["ся", "—"]}
    ]
  },
  {
    "id": "act-2",
    "type": "quiz",
    "title": "Reflexive or transitive?",
    "instruction": "Choose the verb form that fits each sentence — the transitive form (action on someone else) or the reflexive form (action on oneself).",
    "items": [
      {"question": "Мама ____ дитину.", "options": ["вмиває", "вмивається"], "answer": "вмиває"},
      {"question": "Мама ____ перед роботою.", "options": ["вмиває", "вмивається"], "answer": "вмивається"},
      {"question": "Я ____ сина о сьомій.", "options": ["прокидаю", "прокидаюся"], "answer": "прокидаю"},
      {"question": "Я ____ о сьомій.", "options": ["прокидаю", "прокидаюся"], "answer": "прокидаюся"},
      {"question": "Тато ____ доньку.", "options": ["одягає", "одягається"], "answer": "одягає"},
      {"question": "Тато ____ швидко.", "options": ["одягає", "одягається"], "answer": "одягається"},
      {"question": "Учитель ____ учнів.", "options": ["навчає", "навчається"], "answer": "навчає"},
      {"question": "Я ____ вдома вранці.", "options": ["навчаю", "навчаюся"], "answer": "навчаюся"}
    ]
  },
  {
    "id": "act-3",
    "type": "fill-in",
    "title": "Sequence words",
    "instruction": "Fill in each gap with the correct sequence word.",
    "items": [
      {"sentence": "____ я прокидаюся.", "answer": "Спочатку", "options": ["Спочатку", "Потім", "Нарешті"]},
      {"sentence": "____ вмиваюся.", "answer": "Потім", "options": ["Потім", "Спочатку", "Нарешті"]},
      {"sentence": "____ одягаюся.", "answer": "Після цього", "options": ["Після цього", "Спочатку", "Нарешті"]},
      {"sentence": "____ снідаю.", "answer": "Потім", "options": ["Потім", "Спочатку", "Нарешті"]},
      {"sentence": "____ йду на роботу.", "answer": "Нарешті", "options": ["Нарешті", "Спочатку", "Потім"]},
      {"sentence": "____ збираюся.", "answer": "Спочатку", "options": ["Спочатку", "Нарешті", "Після цього"]}
    ]
  },
  {
    "id": "act-4",
    "type": "fill-in",
    "title": "Describe your morning",
    "instruction": "Complete each frame to describe your own morning. Use a verb from this module in the я-form.",
    "items": [
      {"sentence": "Спочатку я ____ о сьомій.", "answer": "прокидаюся", "options": ["прокидаюся", "вмиваюся", "снідаю"]},
      {"sentence": "Потім я ____ і одягаюся.", "answer": "вмиваюся", "options": ["вмиваюся", "снідаю", "йду"]},
      {"sentence": "Нарешті я ____ до університету.", "answer": "йду", "options": ["йду", "вмиваюся", "снідаю"]}
    ]
  },
  {
    "id": "act-5",
    "type": "match-up",
    "title": "Transitive ↔ reflexive pairs",
    "instruction": "Match each transitive verb with its reflexive partner.",
    "pairs": [
      {"left": "вмивати", "right": "вмиватися"},
      {"left": "одягати", "right": "одягатися"},
      {"left": "прокидати", "right": "прокидатися"},
      {"left": "навчати", "right": "навчатися"}
    ]
  },
  {
    "id": "act-6",
    "type": "order",
    "title": "Morning in order",
    "instruction": "Put the morning steps into the correct chronological order.",
    "items": [
      "Йду на роботу.",
      "Прокидаюся.",
      "Снідаю.",
      "Одягаюся.",
      "Вмиваюся.",
      "Збираюся."
    ],
    "correct_order": [1, 4, 3, 2, 5, 0]
  },
  {
    "id": "act-7",
    "type": "unjumble",
    "title": "Restore the sentence",
    "instruction": "Reorder the words to form a correct Ukrainian sentence.",
    "items": [
      {"words": ["о", "Я", "сьомій", "прокидаюся"], "correct": "Я прокидаюся о сьомій"},
      {"words": ["вмиваюся", "холодною", "Я", "водою"], "correct": "Я вмиваюся холодною водою"},
      {"words": ["до", "Нарешті", "йду", "університету"], "correct": "Нарешті йду до університету"},
      {"words": ["швидко", "Тато", "одягається"], "correct": "Тато одягається швидко"}
    ]
  },
  {
    "id": "act-8",
    "type": "true-false",
    "title": "Pronunciation and spelling",
    "instruction": "Decide whether each statement about Ukrainian pronunciation and morphology is true or false.",
    "items": [
      {"statement": "Written -шся is pronounced as a single long soft [с':а].", "answer": true},
      {"statement": "Written -ться is pronounced as a single long soft [ц':а].", "answer": true},
      {"statement": "The verb прокидається is pronounced [прокидайец':а].", "answer": true},
      {"statement": "The verb навчаєшся is pronounced with a clearly separate [ш] and [с].", "answer": false},
      {"statement": "The reflexive suffix -ся is etymologically a short form of the pronoun себе.", "answer": true},
      {"statement": "Снідати is a reflexive verb that ends in -ся.", "answer": false}
    ]
  },
  {
    "id": "act-9",
    "type": "error-correction",
    "title": "Fix the verb form",
    "instruction": "Each sentence contains an error in the verb form. Rewrite the sentence with the correct form.",
    "items": [
      {"sentence": "Я вмивається о сьомій.", "errors": ["вмивається"], "corrected": "Я вмиваюся о сьомій."},
      {"sentence": "Ти прокидаюся рано.", "errors": ["прокидаюся"], "corrected": "Ти прокидаєшся рано."},
      {"sentence": "Він одягаюся швидко.", "errors": ["одягаюся"], "corrected": "Він одягається швидко."},
      {"sentence": "Я снідаюся о восьмій.", "errors": ["снідаюся"], "corrected": "Я снідаю о восьмій."},
      {"sentence": "Ми навчаюся вдома.", "errors": ["навчаюся"], "corrected": "Ми навчаємося вдома."},
      {"sentence": "Я йдуся на роботу.", "errors": ["йдуся"], "corrected": "Я йду на роботу."}
    ]
  },
  {
    "id": "act-10",
    "type": "translate",
    "title": "Translate the morning",
    "instruction": "Translate each English sentence into Ukrainian using verbs from this module.",
    "items": [
      {"source": "I wake up at seven.", "target": "Я прокидаюся о сьомій."},
      {"source": "First I wash and get dressed.", "target": "Спочатку я вмиваюся і одягаюся."},
      {"source": "Then I have breakfast.", "target": "Потім я снідаю."},
      {"source": "Finally I head to work.", "target": "Нарешті я йду на роботу."},
      {"source": "On Saturday I wake up late.", "target": "У суботу я прокидаюся пізно."}
    ]
  }
]
```

```json file=vocabulary.yaml
[
  {"lemma": "прокидатися", "translation": "to wake up", "pos": "verb", "usage": "Я прокидаюся о сьомій."},
  {"lemma": "вмиватися", "translation": "to wash one's face and hands", "pos": "verb", "usage": "Я вмиваюся холодною водою."},
  {"lemma": "одягатися", "translation": "to get dressed", "pos": "verb", "usage": "Я одягаюся швидко."},
  {"lemma": "збиратися", "translation": "to get ready, gather one's things", "pos": "verb", "usage": "Я збираюся на роботу."},
  {"lemma": "повертатися", "translation": "to come back, to return", "pos": "verb", "usage": "Я повертаюся пізно."},
  {"lemma": "навчатися", "translation": "to study, to learn", "pos": "verb", "usage": "Я навчаюся вранці."},
  {"lemma": "снідати", "translation": "to have breakfast (not reflexive)", "pos": "verb", "usage": "Я снідаю о восьмій."},
  {"lemma": "йти", "translation": "to go (on foot — irregular)", "pos": "verb", "usage": "Я йду на роботу."},
  {"lemma": "поспішати", "translation": "to hurry", "pos": "verb", "usage": "У суботу я не поспішаю."},
  {"lemma": "дивитися", "translation": "to look, to watch", "pos": "verb", "usage": "Я дивлюся в телефон."},
  {"lemma": "лежати", "translation": "to lie down, to be lying", "pos": "verb", "usage": "Я лежу і дивлюся в телефон."},
  {"lemma": "спочатку", "translation": "first, at first", "pos": "adv", "usage": "Спочатку я прокидаюся."},
  {"lemma": "потім", "translation": "then, next", "pos": "adv", "usage": "Потім вмиваюся."},
  {"lemma": "після цього", "translation": "after that", "pos": "phrase", "usage": "Після цього я снідаю."},
  {"lemma": "нарешті", "translation": "finally, at last", "pos": "adv", "usage": "Нарешті йду на роботу."},
  {"lemma": "вранці", "translation": "in the morning", "pos": "adv", "usage": "Я навчаюся вранці."},
  {"lemma": "пізно", "translation": "late", "pos": "adv", "usage": "У суботу я прокидаюся пізно."},
  {"lemma": "ранок", "translation": "morning", "pos": "noun", "usage": "Доброго ранку!"},
  {"lemma": "сніданок", "translation": "breakfast", "pos": "noun", "usage": "Сніданок о восьмій."},
  {"lemma": "субота", "translation": "Saturday", "pos": "noun", "usage": "У суботу я не поспішаю."}
]
```

```json file=resources.yaml
[
  {"title": "Караман, 10 клас, с. 176", "notes": "Зворотні дієслова: суфікс -ся(-сь) означає дію, спрямовану на себе; історично — давня коротка форма зворотного займенника себе в Зн. в. однини (Я ся не бою — діал. = Я не боюся). Verbatim chunk 10-klas-ukrmova-karaman-2018_s0315, retrieved via mcp__sources__search_text."},
  {"title": "Захарійчук, 4 клас, с. 162-163", "notes": "Вимова та правопис дієслів на -ся: таблиця [прокидайец':а] прокидається / [спиен айес':а] спиняєшся; вірш Дмитра Білоуса 'Закон письма і вимови вивчай: написано -шся, а ти [с':а] вимовляй'. Verbatim chunk 4-klas-ukrmova-zaharijchuk_s0162."},
  {"title": "Кравцова, 4 клас, с. 112-113", "notes": "Вступ до зворотних дієслів через контраст транзитивної та зворотної дії: умивати (когось) ↔ умиватися (себе); обливати ↔ обливатися; розчісувати ↔ розчісуватися. Chunk 4-klas-ukrayinska-mova-kravtsova-2021-1_s0110."},
  {"title": "Авраменко, 7 клас, с. 67", "notes": "Корелятивне підтвердження правила: '-ться [ц':а] пишуться [пишуц':а]; -шся [с':а] дивишся [дивиес':а]'. Chunk 7-klas-ukrmova-avramenko-2024_s0075, supporting Захарійчук."}
]
```

<end_gate>
<rescanned_words>прокидатися, прокидаюся, прокидаєшся, прокидається, вмиватися, вмиваюся, вмиваєшся, вмивається, одягатися, одягаюся, одягаєшся, одягається, снідати, снідаю, снідаєш, снідає, йти, йду, йдеш, йде, спочатку, потім, збиратися, повертатися, навчатися, поспішати, після, нарешті, вранці, пізно, рано, ранок, робота, роботу, школа, школи, сьома, сьомій, восьма, восьмій, шостій, дев'ятій, субота, телефон, кава, каву, сніданок, руки, обличчя, дзеркало, куртка, дивитися, дивлюся, лежати, лежу, гуляю, разом, хвилин, учитель, учнів, учні, учень, тато, мама, доньку, донька, сина, син, дитину, вдома, на, до, для, її, його, свого, свою, холодною, водою, мити, мию, миє, вмивати, вмиваю, вмиває, одягати, одягаю, одягає, прокидати, прокидаю, прокидає, навчати, навчає, взуватися, закохатися — all FOUND in VESUM via two batch verify_words calls (50 + 43 + 28 = 121 words verified, only 3 NOT FOUND were apostrophe-encoding edge cases for inflected "п'ю" / "п'ють" / "дев'ятій" with curly U+2019; straight-apostrophe "дев'ятій" did verify; "п'ю" forms intentionally excluded from final artifacts).</rescanned_words>
<rescanned_sources>Караман 10 клас с. 176 — chunk 10-klas-ukrmova-karaman-2018_s0315 retrieved verbatim via search_text. Захарійчук 4 клас с. 162-163 — chunk 4-klas-ukrmova-zaharijchuk_s0162 retrieved verbatim via search_text. Кравцова 4 клас с. 112-113 — chunk 4-klas-ukrayinska-mova-kravtsova-2021-1_s0110 retrieved via search_text. Авраменко 7 клас с. 67 — chunk 7-klas-ukrmova-avramenko-2024_s0075 retrieved via search_text. verify_source_attribution(style_guide, "зворотні дієслова -ся") returned discusses=false — Антоненко-Давидович is NOT cited for the reflexive-verb rule.</rescanned_sources>
<grammar_claims_grounded>Reflexive-verb rule (suffix -ся = "action directed on self") — Караман 10 клас с. 176 verbatim quote. Etymology (-ся as historical short form of accusative себе) — same Караман chunk verbatim. Pronunciation rule (-шся = [с':а], -ться = [ц':а]) — Захарійчук 4 клас с. 162-163 verbatim transcription table; corroborated by Авраменко 7 клас с. 67. Transitive ↔ reflexive contrast pedagogy — Кравцова 4 клас с. 112-113 (вмивати ↔ вмиватися framing). Sequence-adverb usage (спочатку → потім → після цього → нарешті) and морфологічна паралель з -ться/-шся — grounded in wiki packet pedagogy/a1/my-morning.md :: Послідовність введення Step 5 and :: Словниковий мінімум.</grammar_claims_grounded>
<removed_unverified>"п'ю" (1sg of пити) in all candidate activity items + worked example — VESUM returned NOT FOUND under U+2019 apostrophe encoding; substituted with "снідаю" / "збираюся" throughout. Quiz items referencing "учнів" passed re-verification. Dropped a planned "ліжко" (bed) reference in the Saturday-morning vocab gloss because it was not verified; rephrased "Lying in bed" as "Я лежу і дивлюся в телефон" using verified forms only. Did not invent any Bilous / Sevchenko / literary quotes — only textbook-grounded verbatim blocks are cited.</removed_unverified>
</end_gate>