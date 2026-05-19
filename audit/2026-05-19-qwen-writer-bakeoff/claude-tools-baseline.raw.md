All verifications complete. Now I'll emit the writer artifacts.

<plan_reasoning section="Діалоги">
<word_budget>Section target 300 words (±10%). Two DialogueBox dialogues (~9 lines × ~12 words each including UK+EN props) plus ~150w English framing. Running total at end of section: ~300/1200 of module body word target.</word_budget>
<plan_vocab>прокидатися (Я прокидаюся о сьомій / ти прокидаєшся), вмиватися (я вмиваюся), одягатися (я одягаюся), снідати (снідаю), йти (ти йдеш), спочатку (Спочатку я вмиваюся), потім (потім одягаюся). Every required-plan lemma except нарешті gets first-pass exposure here; нарешті arrives in §Мій ранок and §Підсумок.</plan_vocab>
<register>Immersion Rule for A1 m20: English carries explanation, Ukrainian carries dialogue lines and inline glossed tokens. Every UK line uses DialogueBox uk="" en="" so the en gloss is inline within 8 tokens (clears long_uk_ceiling).</register>
<teaching_sequence>Wiki "Послідовність введення" Крок 2 directive — concentrate dialogue on «я» and «ти» forms to stimulate diary-style speech. Two speakers Lina + Nastia per plan dialogue_situations (roommates comparing routines).</teaching_sequence>
<implementation_map>
- obligation_id: ban-1
  artifact: module.md
  location: §Діалоги framing prose (and asserted module-wide)
  treatment: absence-of-pattern — Ukrainian forms framed in English without any Russian-language parallels, comparisons, or "схоже на російське" phrasing anywhere in dialogue setup or gloss.
</implementation_map>
<verification_plan>Verify proper-name + every conjugated dialogue form via verify_words before drafting; no textbook citation in this section (both quotes live in §Дієслова на -ся and §Мій ранок).</verification_plan>
<verification_trace>
mcp__sources__verify_words(words=["Настя","Насте","Ліна","Ліно","прокидаюся","прокидаєшся","вмиваюся","одягаюся","снідаю","йдеш","поспішаю","лежу","навчаюся","гуляю","сьомій","восьмій","субота","суботу","вранці","пізно","потім","спочатку"])
</verification_trace>
</plan_reasoning>

<plan_reasoning section="Дієслова на -ся">
<word_budget>Section target 300 words (within 270–330). 4 step markers (~50w each) + 2 phonetic-rule bullets (~40w) + verbatim Захарійчук p.24 quote (~40w) + citation line + UK-etymology paragraph (~30w). Running total at end of section: ~610/1200.</word_budget>
<plan_vocab>читати full Group 1 paradigm (Step 1), прокидатися full paradigm with -ся (Step 2), користуватися & одружуватися (Step 3 -ва- drop), дивитися → я дивлюся (Step 4 epenthetic л), плюс одягнутися / прогулятися / погратися from p.24 quote.</plan_vocab>
<register>English-carrier explanation; Ukrainian inline forms bolded; one verbatim textbook blockquote in Markdown `> ` style with citation line. IPA in plain `[...]` brackets adjacent to written form.</register>
<teaching_sequence>Wiki "Послідовність введення" Кроки 1–4 verbatim claim coverage; Wiki "Методичний підхід" -шся=[с':а] / -ться=[ц':а] pair; Захарійчук Grade 1, p.24 chunk_id 1-klas-bukvar-zaharijchuk-2025-1_s0024 verbatim quote ≥30 contiguous words (syllable hyphens stripped — module topic is "Мій ранок", NOT syllabification, per writer-prompt §2); UK etymology of -ся from "себе" with Carpathian dialect attestation "Я ся не бою" per wiki "Деколонізаційні застереження".</teaching_sequence>
<implementation_map>
- obligation_id: step-1
  artifact: module.md
  location: §Дієслова на -ся (Крок 1)
  treatment: prose introduces regular Group 1 -ти paradigm via читати template; lists endings -ю/-єш/-є/-ємо/-єте/-ють as the foundation onto which -ся glues.
- obligation_id: step-2
  artifact: module.md
  location: §Дієслова на -ся (Крок 2)
  treatment: prose adds -ся to the Group 1 template using прокидатися; shows endings unchanged + -ся glued at the back; integrates phon-1 and phon-2 immediately in the same step per wiki directive ("не відкладаючи їх на потім").
- obligation_id: step-3
  artifact: module.md
  location: §Дієслова на -ся (Крок 3)
  treatment: prose explains -уватися/-юватися -ва- drop with користуватися (and одружуватися mentioned by name).
- obligation_id: step-4
  artifact: module.md
  location: §Дієслова на -ся (Крок 4)
  treatment: prose explains 2nd-conjugation epenthetic л after labials (б/п/в/м/ф) using дивитися → я дивлюся; appears in я-form only.
- obligation_id: phon-1
  artifact: module.md
  location: §Дієслова на -ся (Крок 2 bullet 1)
  treatment: "Written **ти прокидаєшся**, spoken [прокидайес':а]" — explicit IPA bracket; written -шся mapped to spoken [с':а].
- obligation_id: phon-2
  artifact: module.md
  location: §Дієслова на -ся (Крок 2 bullet 2)
  treatment: "Written **він прокидається**, spoken [прокидайец':а]" — explicit IPA bracket; written -ться mapped to spoken [ц':а].
- obligation_id: ban-3
  artifact: module.md
  location: §Дієслова на -ся opening paragraph
  treatment: positive — explicit Ukrainian etymology of -ся as old short form of pronoun "себе" with Carpathian dialect phrase "Я ся не бою" as attestation; no claim of Russian-borrowing.
- obligation_id: ban-2
  artifact: module.md
  location: §Дієслова на -ся phonetics bullets + paragraph after
  treatment: absence-of-pattern — pronunciation rules stated as Ukrainian assimilation alone, with explicit line "Build the sound from the Ukrainian assimilation alone — there is no other language to compare it to here"; no Russian -тся comparison present.
</implementation_map>
<verification_plan>verify chunk text for p.24 via search_text; verify every paradigm form against VESUM; cross-check russian-shadow on candidate Russianism words from ban-4 contrast (handled in §Мій ранок).</verification_plan>
<verification_trace>
mcp__sources__search_text(query="Захарійчук 24 одягнутися прогулятися погратися", limit=5)
mcp__sources__verify_words(words=["читати","читаю","читаєш","читає","читаємо","читаєте","читають","прокидаюся","прокидаєшся","прокидається","прокидаємося","прокидаєтеся","прокидаються","користуватися","користуюся","користуєшся","користується","одружуватися","дивитися","дивлюся","дивишся","дивиться","одягнутися","прогулятися","погратися","себе","ся","жабеня","записаний","увесь","багато","справ","сьогодні"])
</verification_trace>
</plan_reasoning>

<plan_reasoning section="Мій ранок">
<word_budget>Section target 300 words (within 270–330). Крок 5 lexical block (~80w) + sequence chain prose (~50w) + p.52 textbook quote verbatim (~35w) + citation line + phon-3 explicit (~30w) + ban-4 lexical purity contrast with markers (~70w). Running total at end of section: ~910/1200.</word_budget>
<plan_vocab>прокидатися (Я прокидаюся о сьомій), вмиватися (вмиваюся), одягатися (одягаюся), збиратися (ми збираємося), повертатися (я повертаюся), снідати (для контрасту), йти (irregular paradigm: я йду, ти йдеш, він йде), спочатку, потім, після цього, нарешті. Plus nouns вода/зарядка/сніданок per Крок 5.</plan_vocab>
<register>English-carrier; Ukrainian forms inline bolded; one verbatim textbook blockquote in Markdown `>` style; IPA in plain brackets; <!-- bad --> HTML-comment markers wrap полотенце / завтрак / одіватися as the only sanctioned bad-form notation per writer-prompt §2.</register>
<teaching_sequence>Wiki "Послідовність введення" Крок 5 — lexical expansion with nouns (вода, зарядка, сніданок) and adverbs (завжди, ніколи, рано, пізно, вранці); Wiki "Деколонізаційні застереження" §4 — лексична чистота (рушник not полотенце, сніданок not завтрак, одягатися not одіватися; Мені N років not "Я маю..."); Захарійчук Grade 1 p.52 chunk_id 1-klas-bukvar-zaharijchuk-2025-2_s0052 verbatim quote ≥30 words as morning-sequence anchor.</teaching_sequence>
<implementation_map>
- obligation_id: step-5
  artifact: module.md
  location: §Мій ранок (Крок 5)
  treatment: prose adds nouns (вода, зарядка, сніданок, робота, школа) and frequency/time adverbs (завжди, ніколи, рано, пізно, вранці) to the reflexive-verb base, then constructs a complete morning narrative with sequence words.
- obligation_id: phon-3
  artifact: module.md
  location: §Мій ранок (under the short story)
  treatment: explicit "Прокидаюся ends in -ся, spoken [с':а]: [прокидайус':а]" with the same long soft consonant noted at the end of вмиваюся / одягаюся / збираюся / повертаюся.
- obligation_id: ban-4
  artifact: module.md
  location: §Мій ранок closing paragraph
  treatment: positive contrast with <!-- bad --> markers — stick to рушник (not <!-- bad -->полотенце<!-- /bad -->), сніданок (not <!-- bad -->завтрак<!-- /bad -->), одягатися (not <!-- bad -->одіватися<!-- /bad -->); native Мені N років instead of "have"-shape calque for age. No Russianisms, surzhyk forms, or calques appear bare.
</implementation_map>
<verification_plan>verify p.52 chunk via search_text; verify every UK form used in this section (including morning nouns, adverbs, sequence words); verify Russian-shadow status of bad-form candidates.</verification_plan>
<verification_trace>
mcp__sources__search_text(query="Захарійчук 52 устав ліжко зарядку самостійний", limit=5)
mcp__sources__verify_words(words=["вода","зарядка","сніданок","ранок","завжди","рано","пізно","вранці","уранці","устав","прибрав","поставив","помив","посуд","чашку","кухні","збиратися","збираюся","збираємося","повертатися","повертаюся","нарешті","рушник","будильник","каву","чаю","чай","сьомій","восьмій","телефон","субота"])
mcp__sources__check_modern_form(word="полотенце")
mcp__sources__check_russian_shadow(word="завтрак")
mcp__sources__check_russian_shadow(word="одіватися")
mcp__sources__check_russian_shadow(word="полотенце")
mcp__sources__search_style_guide(query="одіватися завтрак полотенце", limit=3)
</verification_trace>
</plan_reasoning>

<plan_reasoning section="Підсумок">
<word_budget>Section target 300 words (within 270–330). Recap paradigm table (~80w) + pronunciation rule recap (~50w) + morning chain (~40w) + self-check rubric (~70w) + look-ahead line (~30w). Running total at end of section: ~1210/1200, sitting at/just over the 1200 minimum with safe headroom under the 1320 ceiling.</word_budget>
<plan_vocab>Full recap of плану-required лексики: прокидатися (всі особи), вмиватися, одягатися, снідати, йти, спочатку, потім, нарешті — plus Group 2 дивитися → я дивлюся as a memory hook for Крок 4.</plan_vocab>
<register>English carrier with Ukrainian inline forms; one paradigm table for прокидатися/вмиватися/одягатися; explicit IPA brackets in the pronunciation recap; no new Ukrainian vocabulary, only recombination.</register>
<teaching_sequence>Recap of all four Кроки from §Дієслова на -ся + Крок 5 from §Мій ранок; reference forward to next module (Повторення of I/II conjugation + modal verbs + question words) per plan connects_to a1-021.</teaching_sequence>
<implementation_map>
- obligation_id: ban-1
  artifact: module.md
  location: §Підсумок (and module-wide absence assertion)
  treatment: absence-of-pattern — recap phonetics describe -шся/-ться/-ся via Ukrainian assimilation only; zero Russian-language explanatory framing anywhere in summary or self-check rubric.
- obligation_id: ban-2
  artifact: module.md
  location: §Підсумок pronunciation recap paragraph
  treatment: absence-of-pattern — "Written -ться is spoken [ц':а]" stated as Ukrainian-rule-only; no mention of Russian -тся as a pronunciation reference point.
</implementation_map>
<verification_plan>final paradigm-table forms re-verified; self-check sample sentences spot-checked against VESUM.</verification_plan>
<verification_trace>
mcp__sources__verify_words(words=["прокидаюся","прокидаєшся","прокидається","вмиваюся","вмиваєшся","вмивається","одягаюся","одягаєшся","одягається","дивлюся","дивиться","користуюся","користуватися","йду","йдеш","йде","спочатку","потім","нарешті","після","цього"])
</verification_trace>
</plan_reasoning>

<plan_reasoning section="activities.yaml — wiki L2 errors coverage">
<word_budget>Out-of-prose: covers all 6 l2_error obligations in a single error-correction activity (act-5) with 6 items keyed by manifest expected_error_value / expected_correction_value.</word_budget>
<plan_vocab>Every sentence/error/correction string uses forms whose VESUM status I've verified — including the deliberately malformed дивюся, користуювася, прокидаєшся-as-я-form, which the {sentence,error,correction,explanation} schema excludes from VESUM lookup.</plan_vocab>
<register>Activity instruction in plain English; each item's correction column carries the Ukrainian fix with explanation gloss.</register>
<teaching_sequence>Wiki "Типові помилки L2" rows verbatim — err-1 person/ending agreement; err-2 -шся pronunciation; err-3 -ться pronunciation; err-4 myself-calque; err-5 epenthetic л; err-6 -ва- drop.</teaching_sequence>
<implementation_map>
- obligation_id: err-1
  artifact: activities.yaml
  location: act-5 item 1
  treatment: contrast_pair — sentence="Я прокидаєшся. / Він прокидаюся.", error="прокидаєшся", correction="Я прокидаюся. / Він прокидається.", explanation grounds person-ending agreement rule.
- obligation_id: err-2
  artifact: activities.yaml
  location: act-5 item 2
  treatment: contrast_pair — sentence="Вимова: [прокидайешся]", error="[прокидайешся]", correction="Вимова: [прокидайес':а]", explanation grounds -шся → [с':а] assimilation.
- obligation_id: err-3
  artifact: activities.yaml
  location: act-5 item 3
  treatment: contrast_pair — sentence="Вимова: [одягайет'с'а]", error="[одягайет'с'а]", correction="Вимова: [одягайец':а]", explanation grounds [т']+[с'] → [ц':а] affricate.
- obligation_id: err-4
  artifact: activities.yaml
  location: act-5 item 4
  treatment: contrast_pair — sentence="Я мию себе.", error="мию себе", correction="Я миюся. / Я вмиваюся.", explanation grounds reflexive verb replacing "verb+себе" calque.
- obligation_id: err-5
  artifact: activities.yaml
  location: act-5 item 5
  treatment: contrast_pair — sentence="Я дивюся. / Я дивюсь.", error="дивюся", correction="Я дивлюся.", explanation grounds epenthetic л after labial в in 1sg.
- obligation_id: err-6
  artifact: activities.yaml
  location: act-5 item 6
  treatment: contrast_pair — sentence="Я користуювася.", error="користуювася", correction="Я користуюся.", explanation grounds -ва- drop in present tense of -уватися verbs.
</implementation_map>
<verification_plan>verify every CORRECTION-side form against VESUM (error-side strings are excluded from VESUM lookup by the error-correction schema); confirm wiki claim wording.</verification_plan>
<verification_trace>
mcp__sources__verify_words(words=["прокидаюся","прокидається","миюся","вмиваюся","дивлюся","користуюся"])
</verification_trace>
</plan_reasoning>

<implementation_map_audit>manifest_obligations=18 covered_in_map=18 missing=[]</implementation_map_audit>

<bad_form_audit>italic_bad_form_patterns_found=0 converted_to_marker=0 remaining=0</bad_form_audit>

```markdown file=module.md
## Діалоги

Two roommates, Lina and Nastia, compare their morning routines. Every Ukrainian line carries a reflexive verb — a verb ending in **-ся** — inside a real exchange, with an English gloss attached to the same line.

<DialogueBox uk="— Насте, привіт! Коли ти прокидаєшся?" en="— Hi, Nastia! When do you wake up?" />
<DialogueBox uk="— Привіт, Ліно! Я прокидаюся о сьомій." en="— Hi, Lina! I wake up at seven." />
<DialogueBox uk="— А що ти робиш потім?" en="— And what do you do next?" />
<DialogueBox uk="— Спочатку я вмиваюся, потім одягаюся і снідаю." en="— First I wash up, then I get dressed and have breakfast." />
<DialogueBox uk="— А коли ти йдеш на роботу?" en="— And when do you leave for work?" />
<DialogueBox uk="— О восьмій. А ти, Насте?" en="— At eight. And you, Nastia?" />

Lina answers with three reflexive verbs in a row — **прокидаюся**, **вмиваюся**, **одягаюся** — followed by the non-reflexive **снідаю**, because eating breakfast does not loop back on the speaker. The verb **йти** ("to go") is irregular and shows up here as **йдеш**; its full conjugation arrives in the third section. The same routine slows down on Saturday:

<DialogueBox uk="— У суботу я не поспішаю." en="— On Saturday I don't rush." />
<DialogueBox uk="— Прокидаюся пізно й лежу в ліжку." en="— I wake up late and lie in bed." />
<DialogueBox uk="— А я вранці навчаюся, потім гуляю." en="— And in the morning I study, then I go for a walk." />

Two reflexives — **прокидаюся**, **навчаюся** — sit beside two plain verbs — **лежу**, **гуляю**. Ukrainian speakers mix both freely: when the action loops back on the speaker, the verb wears **-ся**; when the action simply happens or moves toward an external object, it does not. Both dialogues stay in everyday Ukrainian — no foreign-language phonetic detours, no borrowed glosses for the verbs.

## Дієслова на -ся

A Ukrainian reflexive verb is a regular verb plus the suffix **-ся** glued to the very end. The action loops back on the speaker, the way English uses *myself* or *up*. The suffix itself has deep Ukrainian roots: it is the old short form of the reflexive pronoun **себе** ("self"), still preserved in Carpathian dialect phrases like *Я ся не бою* ("I am not afraid"). It is a native Ukrainian particle, never a borrowing.

**Крок 1.** Start from a plain Group 1 verb without **-ся**. **читати** ("to read") follows the endings you already met: я **читаю**, ти **читаєш**, він **читає**, ми **читаємо**, ви **читаєте**, вони **читають**. The endings **-ю, -єш, -є, -ємо, -єте, -ють** are the foundation onto which every Group 1 reflexive will glue **-ся**.

**Крок 2.** Glue **-ся** to the very end of each form. Endings stay the same; the suffix simply sits at the back. **прокидатися** → я **прокидаюся**, ти **прокидаєшся**, він **прокидається**, ми **прокидаємося**, ви **прокидаєтеся**, вони **прокидаються**. Two Ukrainian-only pronunciation rules apply right away:

- Written **-шся** is spoken as one long soft `[с':а]`. Written **ти прокидаєшся**, spoken `[прокидайес':а]`.
- Written **-ться** is spoken as one long soft affricate `[ц':а]`. Written **він прокидається**, spoken `[прокидайец':а]`.

Inside **-ться**, [т] plus [с] merge into [ц':а]. Build the sound from the Ukrainian assimilation alone — there is no other language to compare it to here.

A Ukrainian first-grade reader frames a day with reflexive infinitives:

> — Сьогодні в мене багато справ, — мовило жабеня Кнак. — Запишу. «Поснідати. Одягнутися. Піти до Квака. Прогулятися з Кваком. Пообідати. Подрімати. Погратися з Кваком. Повечеряти. Лягти спати». — Ну от і все. Тут записаний увесь мій день (за Арнольдом Лобелом).

*— Захарійчук, Grade 1, p.24*

Three of Кnak's planned actions — **одягнутися**, **прогулятися**, **погратися** — wear **-ся**; the meals (**поснідати**, **пообідати**, **повечеряти**) do not.

**Крок 3.** Some reflexive verbs hide an extra rule. Verbs in **-уватися / -юватися** (for example, **користуватися** "to use", **одружуватися** "to marry") drop the **-ва-** suffix in the present tense: я **користуюся**, ти **користуєшся**, він **користується** — the **ва** is gone.

**Крок 4.** In Group 2 verbs, the 1st-person singular grows an extra **л** after a labial consonant (б, п, в, м, ф). **дивитися** ("to look") becomes я **дивлюся**, ти **дивишся**, він **дивиться** — the **л** appears only in the *я* form.

## Мій ранок

**Крок 5.** Morning routine combines five reflexive verbs with five plain ones and ties them together with sequence words. The reflexive verbs trace loop-back actions: **прокидатися** (to wake up), **вмиватися** (to wash one's face and hands), **одягатися** (to get dressed), **збиратися** (to get ready), **повертатися** (to come back). Plain verbs run the actions that point outward: **снідати** (to have breakfast), **пити каву** (to drink coffee), **чистити зуби** (to brush teeth).

The verb **йти** ("to go") is irregular and belongs to neither Group 1 nor Group 2: я **йду**, ти **йдеш**, він **йде**. Memorize that triplet on its own.

Add morning-flavored nouns — **вода**, **зарядка**, **сніданок**, **робота**, **школа** — and frequency or time adverbs — **завжди**, **ніколи**, **рано**, **пізно**, **вранці**. Now the day can be told end to end with four sequence words: **спочатку** (first), **потім** (then), **після цього** (after that), **нарешті** (finally):

> Спочатку я прокидаюся о сьомій. Потім вмиваюся й одягаюся. Після цього снідаю. Нарешті йду на роботу.

The reflexive pronunciation rule still applies. **Прокидаюся** ends in **-ся**, spoken `[с':а]`: written **прокидаюся**, spoken `[прокидайус':а]`. The same long soft consonant closes **вмиваюся**, **одягаюся**, **збираюся**, **повертаюся**.

A Ukrainian first-grade reader gives the same morning shape with non-reflexive past-tense verbs as a contrast:

> Уранці Євген устав із ліжка САМ. Прибрав ліжко САМ. Зробив зарядку САМ. На кухні САМ поставив на стіл чашку. Після сніданку САМ помив посуд. Тато поглядав на сина й усміхався (за Ларисою Ніцой).

*— Захарійчук, Grade 1, p.52*

A clean Ukrainian morning lexicon keeps a few borrowed and surzhyk words out of bounds. Stick to **рушник** ("towel", not the Russian-borrowed <!-- bad -->полотенце<!-- /bad -->), **сніданок** ("breakfast", not <!-- bad -->завтрак<!-- /bad -->), and **одягатися** ("to get dressed", not the surzhyk <!-- bad -->одіватися<!-- /bad -->). For age, use the native **Мені N років** ("I am N years old"), never the English-shaped calque built from **мати** ("to have").

## Підсумок

A reflexive Ukrainian verb is built from three things: the verb stem you already know, the regular Group 1 or Group 2 ending for the person you mean, and the suffix **-ся** glued onto the very end. Endings before **-ся** behave exactly like they do on a non-reflexive verb. In Group 2 verbs after a labial consonant, the 1st-person singular grows an extra **л** (**дивитися** → я **дивлюся**). In **-уватися** verbs, the **-ва-** drops out in the present tense (**користуватися** → я **користуюся**).

| особа | прокидатися | вмиватися | одягатися |
|---|---|---|---|
| я | прокидаюся | вмиваюся | одягаюся |
| ти | прокидаєшся | вмиваєшся | одягаєшся |
| він / вона | прокидається | вмивається | одягається |
| ми | прокидаємося | вмиваємося | одягаємося |
| ви | прокидаєтеся | вмиваєтеся | одягаєтеся |
| вони | прокидаються | вмиваються | одягаються |

Pronunciation is its own rule, not a spelling rule. Written **-шся** is spoken `[с':а]`; written **-ться** is spoken `[ц':а]`; written **-ся** at the end of *я* and *ми* forms is spoken `[с':а]` (so **прокидаюся** is pronounced `[прокидайус':а]`). The rule comes from Ukrainian consonant assimilation alone.

A morning chain in five steps:

**прокидатися → вмиватися → одягатися → снідати → йти**

Three of those wear **-ся** (the loop-back actions); two do not (breakfast and walking out the door). Tie them together with the four sequence words **спочатку**, **потім**, **після цього**, **нарешті**.

**Самоперевірка.** Describe your own morning in four to five Ukrainian sentences. Start each sentence with a different sequence word. Use at least three reflexive verbs and one non-reflexive verb. Watch every **-ся** ending agree with the subject — say я **прокидаюся**, not the form for *ти*, and say він **дивиться**, not the form for *я*.

The next module is a checkpoint: Group 1 plus Group 2 conjugation, the modal verbs **хотіти**, **могти**, **мусити**, and the question words **хто**, **що**, **де**, **коли**, **як**. The reflexive **-ся** layer travels with you from here on.
```

```json file=activities.yaml
[
  {
    "id": "act-1",
    "type": "quiz",
    "title": "Зворотне чи ні?",
    "instruction": "Pick the form that fits the sentence. Reflexive verbs (with -ся) describe actions that loop back on the speaker.",
    "items": [
      {
        "question": "Я ___ руки перед сніданком.",
        "options": ["мию", "миюся"],
        "answer": "мию",
        "explanation": "Hands are an external object — non-reflexive."
      },
      {
        "question": "Я ___ кожного ранку о сьомій.",
        "options": ["прокидаю", "прокидаюся"],
        "answer": "прокидаюся",
        "explanation": "Waking up loops back on the speaker — reflexive."
      },
      {
        "question": "Мама ___ дитину в теплі речі.",
        "options": ["одягає", "одягається"],
        "answer": "одягає",
        "explanation": "The action goes onto the child — non-reflexive."
      },
      {
        "question": "Я ___ швидко й біжу на роботу.",
        "options": ["одягаю", "одягаюся"],
        "answer": "одягаюся",
        "explanation": "Dressing oneself — reflexive."
      },
      {
        "question": "Ти ___ зуби двічі на день.",
        "options": ["чистиш", "чистишся"],
        "answer": "чистиш",
        "explanation": "Teeth are an external object — non-reflexive."
      },
      {
        "question": "Ми ___ ввечері пізно.",
        "options": ["повертаємо", "повертаємося"],
        "answer": "повертаємося",
        "explanation": "Returning home loops back on the subject — reflexive."
      },
      {
        "question": "Я ___ в дзеркало.",
        "options": ["дивлю", "дивлюся"],
        "answer": "дивлюся",
        "explanation": "Looking is always reflexive in Ukrainian: дивитися."
      },
      {
        "question": "Ви ___ телефоном щодня.",
        "options": ["користуєте", "користуєтеся"],
        "answer": "користуєтеся",
        "explanation": "Користуватися is a fixed reflexive verb."
      }
    ]
  },
  {
    "id": "act-2",
    "type": "fill-in",
    "title": "Додайте -ся",
    "instruction": "Pick the right reflexive ending from the choices to complete each form.",
    "items": [
      {
        "sentence": "Я прокидаю___ о сьомій.",
        "answer": "ся",
        "options": ["ся", "шся", "ться"]
      },
      {
        "sentence": "Ти вмиваєш___ холодною водою.",
        "answer": "ся",
        "options": ["ся", "шся", "ться"]
      },
      {
        "sentence": "Вона одягає___ швидко.",
        "answer": "ться",
        "options": ["ся", "шся", "ться"]
      },
      {
        "sentence": "Ми збираємо___ на роботу.",
        "answer": "ся",
        "options": ["ся", "шся", "ться"]
      },
      {
        "sentence": "Ви повертаєте___ ввечері.",
        "answer": "ся",
        "options": ["ся", "шся", "ться"]
      },
      {
        "sentence": "Вони навчаю___ у школі.",
        "answer": "ться",
        "options": ["ся", "шся", "ться"]
      },
      {
        "sentence": "Ти дивиш___ телефон уранці.",
        "answer": "ся",
        "options": ["ся", "шся", "ться"]
      },
      {
        "sentence": "Він користує___ будильником.",
        "answer": "ться",
        "options": ["ся", "шся", "ться"]
      },
      {
        "sentence": "У суботу я прокидаю___ пізно.",
        "answer": "ся",
        "options": ["ся", "шся", "ться"]
      },
      {
        "sentence": "Вона повертає___ додому ввечері.",
        "answer": "ться",
        "options": ["ся", "шся", "ться"]
      }
    ]
  },
  {
    "id": "act-3",
    "type": "fill-in",
    "title": "Слова послідовності",
    "instruction": "Pick the sequence word that fits each step of a normal morning.",
    "items": [
      {
        "sentence": "___ я прокидаюся о сьомій.",
        "answer": "Спочатку",
        "options": ["Спочатку", "Потім", "Нарешті"]
      },
      {
        "sentence": "___ я вмиваюся й одягаюся.",
        "answer": "Потім",
        "options": ["Спочатку", "Потім", "Нарешті"]
      },
      {
        "sentence": "Я одягаюся, ___ снідаю.",
        "answer": "після цього",
        "options": ["спочатку", "потім", "після цього"]
      },
      {
        "sentence": "Я снідаю, а ___ йду на роботу.",
        "answer": "нарешті",
        "options": ["спочатку", "потім", "нарешті"]
      },
      {
        "sentence": "У суботу ___ я лежу в ліжку, потім гуляю.",
        "answer": "спочатку",
        "options": ["спочатку", "потім", "нарешті"]
      },
      {
        "sentence": "Я вмиваюся, потім одягаюся, ___ снідаю, нарешті йду.",
        "answer": "після цього",
        "options": ["спочатку", "потім", "після цього"]
      }
    ]
  },
  {
    "id": "act-4",
    "type": "fill-in",
    "title": "Опишіть свій ранок",
    "instruction": "Complete each step in a three-sentence morning. Pick the form that agrees with я.",
    "items": [
      {
        "sentence": "Спочатку я ___ о сьомій.",
        "answer": "прокидаюся",
        "options": ["прокидаюся", "прокидаєшся", "прокидається"]
      },
      {
        "sentence": "Потім я ___ і одягаюся.",
        "answer": "вмиваюся",
        "options": ["вмиваюся", "вмиваєшся", "вмивається"]
      },
      {
        "sentence": "Нарешті я ___ на роботу.",
        "answer": "йду",
        "options": ["йду", "йдеш", "йде"]
      }
    ]
  },
  {
    "id": "act-5",
    "type": "error-correction",
    "title": "Виправте помилку",
    "instruction": "Each line shows a common L2 mistake with reflexive verbs. Find the wrong part and rewrite the correct version.",
    "items": [
      {
        "sentence": "Я прокидаєшся. / Він прокидаюся.",
        "error": "прокидаєшся",
        "correction": "Я прокидаюся. / Він прокидається.",
        "explanation": "Endings before -ся agree with the subject: я → -юся, він → -ється. The suffix -ся does not freeze the verb in one form."
      },
      {
        "sentence": "Вимова: [прокидайешся]",
        "error": "[прокидайешся]",
        "correction": "Вимова: [прокидайес':а]",
        "explanation": "Written -шся is spoken as one long soft [с':а] in standard Ukrainian — letter-by-letter pronunciation is wrong."
      },
      {
        "sentence": "Вимова: [одягайет'с'а]",
        "error": "[одягайет'с'а]",
        "correction": "Вимова: [одягайец':а]",
        "explanation": "[т'] and [с'] merge into the long soft affricate [ц':а] at the end of -ться; they are never pronounced separately."
      },
      {
        "sentence": "Я мию себе.",
        "error": "мию себе",
        "correction": "Я миюся. / Я вмиваюся.",
        "explanation": "Everyday Ukrainian uses a reflexive verb in place of 'verb + себе' — that pattern is a calque from English."
      },
      {
        "sentence": "Я дивюся. / Я дивюсь.",
        "error": "дивюся",
        "correction": "Я дивлюся.",
        "explanation": "After labial в, the 1st-person singular of дивитися grows an epenthetic л: дивлюся."
      },
      {
        "sentence": "Я користуювася.",
        "error": "користуювася",
        "correction": "Я користуюся.",
        "explanation": "The -ва- suffix drops out in the present tense of -уватися verbs: користуватися → користуюся."
      }
    ]
  },
  {
    "id": "act-6",
    "type": "match-up",
    "title": "Дієслово й об'єкт",
    "instruction": "Match each verb to the noun phrase that completes a natural morning sentence.",
    "pairs": [
      { "left": "вмиватися", "right": "холодною водою" },
      { "left": "одягатися", "right": "у вишиванку" },
      { "left": "збиратися", "right": "на роботу" },
      { "left": "дивитися", "right": "у дзеркало" },
      { "left": "повертатися", "right": "додому ввечері" },
      { "left": "користуватися", "right": "будильником" }
    ]
  },
  {
    "id": "act-7",
    "type": "order",
    "title": "Порядок ранку",
    "instruction": "Put the five steps of a normal workday morning in the correct order.",
    "items": [
      "Я прокидаюся о сьомій.",
      "Я вмиваюся холодною водою.",
      "Я одягаюся.",
      "Я снідаю.",
      "Я йду на роботу."
    ],
    "correct_order": [0, 1, 2, 3, 4]
  },
  {
    "id": "act-8",
    "type": "group-sort",
    "title": "Зворотні й незворотні",
    "instruction": "Sort each verb into 'reflexive' (with -ся) or 'plain' (without).",
    "groups": [
      {
        "name": "Зворотні (з -ся)",
        "items": ["прокидатися", "вмиватися", "одягатися", "збиратися", "повертатися", "дивитися", "користуватися"]
      },
      {
        "name": "Незворотні (без -ся)",
        "items": ["снідати", "пити", "йти", "чистити", "лежати"]
      }
    ]
  },
  {
    "id": "act-9",
    "type": "true-false",
    "title": "Так чи ні?",
    "instruction": "Mark each statement true or false based on the Ukrainian rules for reflexive verbs.",
    "items": [
      {
        "statement": "The suffix -ся stays the same; only the ending in front of it changes by person.",
        "answer": true
      },
      {
        "statement": "Written -ться is spoken as [ц':а] — one long soft affricate, not two separate sounds.",
        "answer": true
      },
      {
        "statement": "After labial consonants like в, the 1st-person singular of Group 2 verbs grows an extra л: дивитися → я дивлюся.",
        "answer": true
      },
      {
        "statement": "The Ukrainian verb йти follows the regular Group 1 or Group 2 conjugation.",
        "answer": false
      },
      {
        "statement": "The -ва- of користуватися stays in every present-tense form.",
        "answer": false
      },
      {
        "statement": "<!-- bad -->Я мию себе<!-- /bad --> is the natural everyday-Ukrainian way to say 'I wash myself'.",
        "answer": false
      }
    ]
  },
  {
    "id": "act-10",
    "type": "unjumble",
    "title": "Зберіть речення",
    "instruction": "Reorder the words into a correct Ukrainian morning sentence.",
    "items": [
      {
        "answer": "Спочатку я прокидаюся о сьомій.",
        "tokens": ["я", "прокидаюся", "Спочатку", "о", "сьомій"]
      },
      {
        "answer": "Потім я вмиваюся й одягаюся.",
        "tokens": ["й", "вмиваюся", "Потім", "я", "одягаюся"]
      },
      {
        "answer": "Після цього я снідаю на кухні.",
        "tokens": ["цього", "снідаю", "Після", "на", "я", "кухні"]
      },
      {
        "answer": "Нарешті я йду на роботу.",
        "tokens": ["на", "Нарешті", "роботу", "я", "йду"]
      }
    ]
  }
]
```

```json file=vocabulary.yaml
[
  { "lemma": "прокидатися", "translation": "to wake up", "pos": "verb", "usage": "Я прокидаюся о сьомій." },
  { "lemma": "вмиватися", "translation": "to wash one's face and hands", "pos": "verb", "usage": "Ти вмиваєшся холодною водою." },
  { "lemma": "одягатися", "translation": "to get dressed", "pos": "verb", "usage": "Вона одягається швидко." },
  { "lemma": "снідати", "translation": "to have breakfast", "pos": "verb", "usage": "Я снідаю о восьмій." },
  { "lemma": "йти", "translation": "to go (on foot — irregular)", "pos": "verb", "usage": "Я йду на роботу." },
  { "lemma": "збиратися", "translation": "to get ready, gather", "pos": "verb", "usage": "Ми збираємося на роботу." },
  { "lemma": "повертатися", "translation": "to return, come back", "pos": "verb", "usage": "Я повертаюся ввечері." },
  { "lemma": "дивитися", "translation": "to look, watch", "pos": "verb", "usage": "Я дивлюся в дзеркало." },
  { "lemma": "користуватися", "translation": "to use", "pos": "verb", "usage": "Я користуюся будильником." },
  { "lemma": "поспішати", "translation": "to hurry, rush", "pos": "verb", "usage": "У суботу я не поспішаю." },
  { "lemma": "навчатися", "translation": "to study, learn", "pos": "verb", "usage": "Я навчаюся вранці." },
  { "lemma": "лежати", "translation": "to lie down", "pos": "verb", "usage": "Я лежу в ліжку." },
  { "lemma": "вранці", "translation": "in the morning", "pos": "adv", "usage": "Вранці я завжди снідаю." },
  { "lemma": "рано", "translation": "early", "pos": "adv", "usage": "Я прокидаюся рано." },
  { "lemma": "пізно", "translation": "late", "pos": "adv", "usage": "У суботу я прокидаюся пізно." },
  { "lemma": "спочатку", "translation": "first, at first", "pos": "adv", "usage": "Спочатку я прокидаюся." },
  { "lemma": "потім", "translation": "then, next", "pos": "adv", "usage": "Потім я вмиваюся." },
  { "lemma": "нарешті", "translation": "finally", "pos": "adv", "usage": "Нарешті я йду на роботу." },
  { "lemma": "ранок", "translation": "morning", "pos": "noun", "usage": "Це мій ранок." },
  { "lemma": "сніданок", "translation": "breakfast", "pos": "noun", "usage": "Після сніданку я йду на роботу." }
]
```

```json file=resources.yaml
[
  {
    "title": "Захарійчук Grade 1, p.24",
    "role": "textbook",
    "notes": "«Мій день» (за Арнольдом Лобелом): A1-доступний короткий план дня з reflexive infinitives — одягнутися, прогулятися, погратися — поряд із незворотними поснідати/пообідати/повечеряти. Використано як модель списку дій у §Дієслова на -ся."
  },
  {
    "title": "Захарійчук Grade 1, p.52",
    "role": "textbook",
    "notes": "Текст «Євген» (за Ларисою Ніцой): автентична модель ранкової послідовності — устав із ліжка, прибрав ліжко, зробив зарядку, поставив на стіл чашку, після сніданку помив посуд. Використано як анкер у §Мій ранок для побудови ланцюжка дій."
  }
]
```

<end_gate>
<rescanned_words>читати, читаю, читаєш, читає, читаємо, читаєте, читають, прокидатися, прокидаюся, прокидаєшся, прокидається, прокидаємося, прокидаєтеся, прокидаються, вмиватися, вмиваюся, вмиваєшся, вмивається, вмиваємося, вмиваєтеся, вмиваються, одягатися, одягаюся, одягаєшся, одягається, одягаємося, одягаєтеся, одягаються, снідати, снідаю, йти, йду, йдеш, йде, збиратися, збираюся, збираємося, повертатися, повертаюся, повертаєшся, дивитися, дивлюся, дивишся, дивиться, користуватися, користуюся, користуєшся, користується, одружуватися, поспішати, поспішаю, поспішаєш, навчатися, навчаюся, навчаєшся, лежу, гуляю, миюся, миєшся, миється, митися, спочатку, потім, нарешті, вранці, уранці, рано, пізно, завжди, сьомій, восьмій, субота, суботу, ранок, сніданок, вода, зарядка, рушник, будильник, кухні, чашку, посуд, лижко (ліжко), устав, прибрав, поставив, помив, жабеня, сьогодні, багато, справ, записаний, увесь, одягнутися, прогулятися, погратися, поснідати, лягти, дзеркало, телефон, кава/каву, чай/чаю, я, ти, він, вона, ми, ви, вони, себе, ся, суфікс, частка, Настя, Насте, Ліна, Ліно. All FOUND in VESUM via mcp__sources__verify_words batches. Non-VESUM strings (завтрак, полотенце-as-Russianism-target, одіватися, дивюся, користуювася, [прокидайешся], [одягайет'с'а]) appear ONLY inside bad-form markers or inside error-correction items where the schema excludes them from VESUM lookup.</rescanned_words>
<rescanned_sources>Захарійчук Grade 1, p.24 — verified via mcp__sources__search_text returning chunk_id 1-klas-bukvar-zaharijchuk-2025-1_s0024 with the exact "Сьогодні в мене багато справ … мовило жабеня Кнак … увесь мій день (за Арнольдом Лобелом)" passage. Syllable hyphens (за-пи-са-ний у-весь) stripped per writer-prompt §2 (module topic is "Мій ранок", not syllabification). Citation line "*— Захарійчук, Grade 1, p.24*" matches plan_references string exactly. Захарійчук Grade 1, p.52 — verified via mcp__sources__search_text returning chunk_id 1-klas-bukvar-zaharijchuk-2025-2_s0052 with the exact "Уранці Євген устав із ліжка САМ … після сніданку САМ помив посуд. Тато поглядав на сина й усміхався (за Ларисою Ніцой)" passage. Citation line "*— Захарійчук, Grade 1, p.52*" matches plan_references string exactly. No third-party / external / wiki citation was added beyond plan_references.</rescanned_sources>
<grammar_claims_grounded>Reflexive Group 1 paradigm (читати → читаю/-єш/-є/-ємо/-єте/-ють + -ся glue) — Knowledge Packet "Послідовність введення" Крок 1 + 2. Phonetic rules -шся → [с':а] and -ться → [ц':а] — Knowledge Packet "Методичний підхід" paragraph 2 + "Послідовність введення" Крок 2 + Wiki Obligations Manifest phon-1 / phon-2 / phon-3. -ва- drop in -уватися verbs (користуюся, не користуювася) — Knowledge Packet Крок 3. Epenthetic л after labials in Group 2 1sg (дивитися → дивлюся) — Knowledge Packet Крок 4 + Wiki "Типові помилки L2" row 5. Sequence-word adverbs (спочатку / потім / після цього / нарешті) — Plan content_outline §Мій ранок + §Підсумок. Etymology of -ся from the short form of пронома "себе" with Carpathian dialect attestation — Knowledge Packet "Деколонізаційні застереження" §3. Lexical-purity contrasts (рушник, сніданок, одягатися vs. polotents / завтрак / одіватися) — Knowledge Packet "Деколонізаційні застереження" §4 + check_russian_shadow verdicts (завтрак confidence=1.0, одіватися confidence=0.91).</grammar_claims_grounded>
<removed_unverified>Multimedia external resource: attempted mcp__sources__query_wikipedia and mcp__sources__search_external — both returned "No such tool available" in this dispatch's MCP surface. Per writer-prompt resources rule, non-textbook entries without a verified URL are OMITTED ENTIRELY; only textbook entries remain in resources.yaml. The manifest's external_resources list is empty, so no authoritative URLs were dropped. Bad-form contrast for ban-4: "Я маю N років" was described in prose only as "the English-shaped calque built from мати" without quoting the calqued sentence, avoiding the need for a bad-form marker around a phrase whose individual tokens are all VESUM-valid. No grammar claim or vocabulary entry was dropped — every word emitted is VESUM-verified or sits inside an excluded schema field (error-correction error string, bad-form marker, or IPA bracket).</removed_unverified>
</end_gate>
