<correction_directive>
CRITICAL: Your previous attempt failed the following checks. Write the module FROM SCRATCH. All original constraints still apply.

- FIX: Missing section heading: 'Підсумок: таблиця дієслівних чергувань'
- NOTE: Missing 1/14 required vocab: теперішній час (present tense)
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

# Section-by-Section Generation — Section 1/7

You are writing ONE SECTION of a Ukrainian language module. Write ONLY this section — nothing else.

**Module:** 6: Чергування приголосних (дієслова) (B1, B1.1 [Baselines & Morphophonemics])
**Section to write:** Від іменників до дієслів (~550 words total)
**Word target for this section:** 550 words (aim for 605 to account for undershoot)

---

## Section Skeleton (follow this exactly)

## Від іменників до дієслів (~550 words total)
- P1 (~120 words): [Hook: The living nature of Ukrainian phonetics. Introduce the concept of "consonant friction" (alternation) as a natural adjustment for ease of speech, specifically in verbs.]
- P2 (~130 words): [Bridge from M09 (Nouns). Remind the learner of [г/к/х] -> [ж/ч/ш] changes in nouns like друг/друже and нога/нозі. State that verbs follow a similar logic but with different triggers.]
- P3 (~150 words): [The "Historical Why" (Заболотний Grade 7). Explain the ancient [j] suffix that existed in the 1st person singular. Describe how this "invisible" sound melted into the preceding consonant, creating the modern alternations like сидіти + j -> сиджу.]
- P4 (~150 words): [The "Where and When": Clarify that for conjugation, this happens ALMOST exclusively in the 1st person singular (я-form) of II conjugation verbs. Provide a brief roadmap of the three groups: Dental/Sibilant, Velar, and Labial + [л].]

---
## Full Plan (for reference)

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

## Knowledge Packet

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

## Rules

Full Ukrainian immersion. Grammar explained IN Ukrainian. English only for disambiguation of false friends. Sentences max 30 words.

GRAMMAR RULES:
- Max 30 words per Ukrainian sentence
- Max 4 clauses per sentence
- All grammar constructions allowed
- Participles allowed
- Complex subordinate clauses allowed



- **NO IPA, NO Latin transliteration** — describe sounds by comparison.
- **Ukrainian quotes: «...»** for Ukrainian text.
- **Place exercise markers only** — write `<!-- INJECT_ACTIVITY: type, topic hint -->` where the skeleton places exercises. Do NOT write :::quiz or :::fill-in DSL directly.
- **NO meta-commentary** — no "In this section we will...", no vocabulary tables, no word count notes.
- **Zero Russian, zero Surzhyk, zero calques.**
- **Every bold Ukrainian word MUST have an English translation on first use.**
- **NO stress marks** — a deterministic tool adds them later.
- **Dialogue formatting:** Use blockquote `>` with speaker names in bold. Each turn on its own `>` line. NO blank lines between turns — all lines must be consecutive. Example:
  > — **Оксана:** Привіт! *(Hi!)*
  > — **Степан:** Добрий день! *(Good day!)*
  > — **Оксана:** Як справи? *(How are you?)*

## Output

Write the section starting with the H2 heading. Output ONLY the section content — no preamble, no summary, no notes.
