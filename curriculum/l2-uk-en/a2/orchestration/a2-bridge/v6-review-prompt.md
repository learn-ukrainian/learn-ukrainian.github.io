<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 1: Ласкаво просимо до рівня А2 (A2, A2.1 [Foundation and Aspect Introduction])
**Writer:** Gemini Pro
**Word target:** 2000

## Plan (source of truth)

<plan_content>
module: a2-001
level: A2
sequence: 1
slug: a2-bridge
version: '1.0'
title: Ласкаво просимо до рівня А2
subtitle: Огляд граматики А1 та підготовка до нових тем
focus: review
pedagogy: PPP
phase: A2.1 [Foundation and Aspect Introduction]
word_target: 2000
objectives:
- Learner can confidently recall and use the Nominative, Accusative, Locative, and
  Vocative cases for nouns and adjectives learned in A1.
- Learner can recognize and predict common vowel alternations (e.g., о/і, е/і in closed
  syllables) and consonant mutations (г/з/ж, к/ц/ч) in noun and verb stems.
- Learner can actively apply basic euphonic rules (у/в, і/й, з/зі/із) to produce more
  natural-sounding Ukrainian.
- Learner can understand the roadmap for the A2 level, including the introduction
  of the Genitive, Dative, and Instrumental cases.
dialogue_situations:
- setting: 'Arrival at a Kyiv language school on the first day of A2 — reviewing what
    you know: Я з Канади (genitive). Мені 25 (dative). Я вивчаю українську мову (accusative).
    Я живу в Києві (locative).'
  speakers:
  - Новий студент
  - Викладач (teacher)
  motivation: Review all A1 cases in a natural intro conversation
content_outline:
- section: Пригадуємо відмінки (Reviewing Cases)
  words: 600
  points:
  - 'Quick review of the four A1 cases: Nominative (Хто? Що?), Accusative (Кого? Що?),
    Locative (Де? На кому? На чому?), and Vocative (звертання).'
  - 'Practice exercises: identifying case usage in sentences and declining familiar
    noun-adjective pairs.'
  - 'Introducing the full case system map: showing all seven cases and highlighting
    the three new ones for A2 (Genitive, Dative, Instrumental).'
- section: Магія української фонології (The Magic of Ukrainian Phonology)
  words: 700
  points:
  - 'Revisiting key vowel alternations: о/і, е/і (e.g., стіл/стола, Київ/Києва). Explaining
    the ''closed syllable'' rule.'
  - 'Revisiting key consonant alternations: the first palatalization (г/ж, к/ч, х/ш)
    and its effect on noun and verb forms (нога/ніжка, рука/ручка).'
  - 'Introduction to stress patterns: identifying common patterns and using stress
    to disambiguate words (e.g., замок "castle" vs. замок "lock").'
- section: 'Милозвучність мови: евфонія (The Melody of Language: Euphony)'
  words: 400
  points:
  - Formalizing the rules for у/в and і/й alternation based on surrounding sounds
    (vowel vs. consonant).
  - Explaining the use of з/зі/із before difficult consonant clusters.
  - Practice creating fluid sentences by choosing the correct euphonic particle.
- section: Що нас чекає на рівні А2? (What Awaits Us in A2?)
  words: 300
  points:
  - 'A clear roadmap of the A2 curriculum: introduction to aspect, mastering all seven
    noun cases, verb conjugation patterns, and verbs of motion.'
  - 'Setting expectations: A2 is where learners begin to express more complex ideas
    and move beyond simple statements.'
vocabulary_hints:
  required:
  - відмінок (case)
  - називний (nominative)
  - знахідний (accusative)
  - місцевий (locative)
  - кличний (vocative)
  - чергування (alternation)
  - голосний (vowel)
  - приголосний (consonant)
  - наголос (stress (accent))
  recommended:
  - милозвучність (euphony, melodiousness)
  - огляд (review, overview)
  - система (system)
  - правило (rule)
activity_hints:
- type: quiz
  focus: Case Identification Drill
  items: 8
- type: fill-in
  focus: Phonological Alternation Pairs
  items: 8
- type: match-up
  focus: Euphony Choice Exercise
  items: 8
references:
- title: Заболотний Grade 5, §1-10
  notes: Повторення вивченого в початкових класах

</plan_content>

## Generated Content

<generated_module_content>
## Пригадуємо відмінки (Reviewing Cases)

<div class="dialogue">

<div class="dialogue-line"><span class="speaker">Викладач:</span> Добрий день! Ласкаво просимо на курс А2. Як вас звати?</div>

</div>
>
<div class="dialogue">

<div class="dialogue-line"><span class="speaker">Майкл:</span> Добрий день! Мене звати Майкл. Я з Канади.</div>

</div>
>
<div class="dialogue">

<div class="dialogue-line"><span class="speaker">Викладач:</span> О, з Канади! Дуже цікаво. А скільки вам років?</div>

</div>
>
<div class="dialogue">

<div class="dialogue-line"><span class="speaker">Майкл:</span> Мені двадцять п'ять років.</div>

</div>
>
<div class="dialogue">

<div class="dialogue-line"><span class="speaker">Викладач:</span> Чудово! Що ви вивчаєте?</div>

</div>
>
<div class="dialogue">

<div class="dialogue-line"><span class="speaker">Майкл:</span> Я вивчаю українську мову. Я дуже люблю Україну.</div>

</div>
>
<div class="dialogue">

<div class="dialogue-line"><span class="speaker">Викладач:</span> А де ви зараз живете?</div>

</div>
>
<div class="dialogue">

<div class="dialogue-line"><span class="speaker">Майкл:</span> Я живу в Києві. У мене маленька квартира біля метро.</div>

</div>
>
<div class="dialogue">

<div class="dialogue-line"><span class="speaker">Викладач:</span> Прекрасно! Дуже приємно, Майкле! Сідайте, будь ласка.</div>

</div>

Did you notice? In that short conversation, Майкл and the teacher used four different case forms without thinking about it. «З Канади» — the noun changed. «Мені» — another form. «Українську мову» — the adjective and noun both changed. «В Києві» — yet another ending. And at the very end, even Майкл's own name shifted: «Майкле!»

Помітили? Ви вже знаєте чотири **відмінки** *(cases)*. In A1, you learned to use these forms in real conversations — now it's time to name them and understand why the endings change. The key diagnostic tool is simple: the question a word answers reveals its **відмінок**. Each case has its own question pair, and once you know them, you can identify any case instantly.

### Називний відмінок (Nominative — Хто? Що?)

The **називний** *(nominative)* case is the dictionary form — the form you find when you look up a word. It marks the subject of a sentence and answers **Хто?** *(Who?)* for living beings and **Що?** *(What?)* for things.

Adjectives in the nominative agree with their noun in gender:

- Masculine: **новий студент** *(new student)*, **цікавий підручник** *(interesting textbook)*
- Feminine: **нова книга** *(new book)*, **українська мова** *(Ukrainian language)*
- Neuter: **нове місто** *(new city)*, **велике вікно** *(big window)*

Це цікавий підручник. Марія — студентка. Київ — велике місто.

Think of the називний as your starting point. Every other case is a *change* from this base form — a different ending that signals a different role in the sentence.

### Знахідний відмінок (Accusative — Кого? Що?)

The **знахідний** *(accusative)* case marks the direct object — the thing or person receiving the action. It answers **Кого?** *(Whom?)* for animate nouns and **Що?** *(What?)* for inanimate ones.

Three patterns to remember:

**Feminine nouns** change their ending: книга → книгу, кава → каву, земля → землю. The -а becomes -у, the -я becomes -ю.

**Masculine inanimate nouns** stay the same as називний: підручник → підручник, урок → урок. Хто? Що? and Кого? Що? look identical — context tells you the difference.

**Masculine animate nouns** add -а or -я, just like the родовий case — a key rule you'll use constantly: студент → студента, учитель → учителя.

Here are natural verb-noun pairs you already know:

Я читаю книгу. Олена п'є каву. Ти знаєш відповідь. Ми любимо Україну. Вони бачать студента.

### Місцевий відмінок (Locative — Де? На чому? В чому?)

The **місцевий** *(locative)* case answers **Де?** *(Where?)*, **На чому?** *(On what?)*, **В чому?** *(In what?)*. It has one absolute rule: місцевий *never* appears without a **прийменник** *(preposition)*. The prepositions в/у, на, при, and по always come before it.

Look at these city names — each one takes the ending -і:

Я живу в Києві. Вона вчиться у Харкові. Ми були у Львові.

The same ending appears with common nouns: на уроці, в університеті, при школі, по дорозі.

Soft-stem neuter nouns also take -і: місто → у місті, море → на морі.

Remember the dialogue? «Я живу в Києві» — that's місцевий in action. The preposition в plus the ending -і together signal location.

### Кличний відмінок (Vocative — Звертання)

The **кличний** *(vocative)* case is the case of direct address — you use it when calling someone by name or title. This case is uniquely important in Ukrainian. It shows respect and warmth.

Hard-stem masculine nouns take **-е**: Тарас → Тарасе, друг → друже, хлопець → хлопче.

Soft-stem masculine nouns take **-ю**: Сергій → Сергію, Василь → Василю.

Feminine nouns ending in -а take **-о**: мама → мамо, Ганна → Ганно. Feminine nouns ending in -ія take **-є**: Марія → Маріє.

Some forms are fixed: тато → тату.

Remember how the teacher ended the dialogue? «Дуже приємно, Майкле!» That's кличний — the teacher addressed Майкл directly, and his name changed to show it.

Привіт, Сергію! Мамо, де моя книга? Друже, ходімо на каву!

<!-- INJECT_ACTIVITY: quiz, Case Identification Drill -->

### Сім відмінків (The Full Case Map)

Now let's see the complete picture — all seven Ukrainian cases. Four you already know from A1. Three new ones await you in the coming modules.

| | Відмінок | Питання | Функція | Приклад |
|---|---|---|---|---|
| ✅ | Називний | Хто? Що? | Subject | студент читає |
| ✅ | Знахідний | Кого? Що? | Direct object | бачу студента |
| ✅ | Місцевий | Де? На чому? | Location | у Києві |
| ✅ | Кличний | — | Direct address | Майкле! |
| 🔜 | Родовий | Кого? Чого? | Possession, negation | книга студента |
| 🔜 | Давальний | Кому? Чому? | Recipient, age | мені двадцять п'ять |
| 🔜 | Орудний | Ким? Чим? | Means, company | пишу ручкою |

The **родовий** *(genitive)* case shows possession and appears after negation. The **давальний** *(dative)* marks the recipient of an action and expresses age. The **орудний** *(instrumental)* shows the tool or means used, and the person you do something *with*.

Три нові відмінки — це три нові способи виражати думки. Почнемо вже в наступному модулі.

## Магія української фонології (The Magic of Ukrainian Phonology)

Ukrainian words change in ways that can surprise you at first. You learned that **стіл** means *table* — so why does the genitive form become **стола**? That і disappeared, and an о appeared in its place. This is not an exception. This is a **чергування** *(alternation)* — a predictable sound change built into the language. Ukrainian has two categories of alternations: **чергування голосних** *(vowel alternations)* and **чергування приголосних** *(consonant alternations)*. Both follow clear rules based on two triggers: whether a syllable is **закритий** *(closed)* or **відкритий** *(open)*, and which consonant sits before a front vowel. After this section, you will understand *why* стіл becomes стола — not just memorize it.

### Чергування о/і (The О/І Vowel Alternation)

This is the most important vowel alternation in Ukrainian. The rule is elegant: when a **склад** *(syllable)* is **закритий** — meaning it ends in a consonant with no vowel after it — the vowel becomes **і**. When an ending adds a vowel and the syllable **opens**, the і reverts to **о**. Look at these four anchor pairs:

| Називний (закритий склад) | Родовий (відкритий склад) |
|---|---|
| стіл | стола |
| кіт | кота |
| ніч | ночі |
| піч | печі |

In the називний form, the word ends in a consonant — the syllable is closed, so the vowel is **і**. In the родовий, the ending -а or -і opens the syllable, and the vowel shifts back to **о** or **е**.

Ось речення з обома формами: «На столі стоїть новий стіл.» The місцевий form **столі** keeps the і because the stress pattern preserves the closed-syllable quality — but the root vowel tells you exactly what happened historically.

### Чергування е/і (The Е/І Alternation)

The same closed-syllable rule governs another set of words — but here the vowel alternates between **е** and **і** instead of о and і. These are two expressions of one phenomenon, just with different historical source vowels.

Корінь → кореня. Камінь → каменя. Осінь → осені.

In the називний, the syllable is closed: **корінь**, **камінь**, **осінь** — all with і. In the родовий, the ending -я or -і opens the syllable, and і becomes е: **кореня**, **каменя**, **осені**.

You will not need to produce these forms from scratch at this stage. You will encounter them in case endings and need to *recognize* the pattern. Practical tip: when a родовий or давальний form looks unfamiliar, check whether the називний has і — if it does, the open-syllable form likely restores о or е. Це одне правило — два варіанти.

### Чергування приголосних (Consonant Alternations)

Ukrainian consonants also alternate — and they follow a three-way pattern. The consonants **г**, **к**, **х** each have two alternate forms depending on the grammatical context.

| Основа | Перша зміна (ж/ч/ш) | Друга зміна (з/ц/с) |
|---|---|---|
| г → | ж (нога → ніжка) | з (нога → нозі) |
| к → | ч (рука → ручка) | ц (рука → руці) |
| х → | ш (вухо → вушко) | с (вухо → у вусі) |

The first change (г→ж, к→ч, х→ш) appears in diminutives and some verb forms. The second change (г→з, к→ц, х→с) appears in the **місцевий** case singular — the very case you reviewed in the previous section.

«Я пишу рукою — але я тримаю ручку.»

«Де моя рука? На руці — браслет.»

These consonant alternations directly preview the місцевий endings you will build in A2 modules 3–5. When you see руці instead of руки, you now know why.

In verbs, the same pattern appears: пекти → печу (к→ч), бігти → біжу (г→ж), їхати → їду (х drops entirely). Ці зміни — не випадкові. Вони системні.

### Наголос як розрізнювач значень (Stress as a Meaning-Differentiator)

Ukrainian **наголос** *(stress)* is **вільний** *(free)* — it is not fixed to a particular syllable position the way it is in Polish or French. It is also **рухомий** *(mobile)* — it can shift from one syllable to another within the same word's paradigm.

This means stress can change meaning entirely. **Замок** with stress on the first syllable means *castle*. **Замок** with stress on the second syllable means *lock*. **Атлас** with first-syllable stress means *atlas* (a book of maps). **Атлас** with second-syllable stress means *satin fabric*.

Stress also shifts within paradigms: рука (називний) → руки (родовий однини) → руки (називний множини). Сестра → сестри → сестер. The word changes its stress depending on case and number.

Practical advice: Ukrainian dictionaries always mark stress. Use goroh.pp.ua to check any new word. Запам'ятовуйте наголос разом зі словом — не лише літери.

### Чергування приголосних у дієсловах (Verb Consonant Alternations Preview)

The same г/к/х → ж/ч/ш pattern appears in verb conjugation — specifically in the **first person singular** present tense. This makes the phonology you just learned directly actionable.

Писати → пишу (с→ш). Казати → кажу (з→ж). Їздити → їжджу (зд→жд). Просити → прошу (с→ш). Водити → воджу (д→дж).

This is a bonus payoff: if you understand the consonant alternation pattern, you already know why these verb forms look different from their infinitives. You will not need to memorize each form as a separate exception — the pattern is the same one you saw in nouns.

«Я кажу вам: ця закономірність — системна.»

When you reach verb conjugation tables in later A2 modules, these changes will feel familiar. Фонологія — ваш найкращий друг.

<!-- INJECT_ACTIVITY: fill-in, Phonological Alternation Pairs -->

## Милозвучність мови: евфонія (The Melody of Language: Euphony)

The phonological patterns you just reviewed — vowel and consonant alternations — serve a deeper purpose. Ukrainian actively avoids dissonant sound clusters through alternating variant pairs. This is not optional style — it is the norm. The term for this quality is **милозвучність** *(euphony, melodiousness)* — literally, «милозвучна мова» means *melodious language*. Three alternating pairs to master at A2: **у/в**, **і/й**, and **з/зі/із**. Consider this sentence from a Ukrainian textbook exercise: «В ваших родинах панує злагода.» Read it aloud. The «в в» collision grates against the ear. The correct form flows naturally: «У ваших родинах панує злагода.»

### У/В

The core rule is simple: **after a vowel, use в**; **after a consonant or at the start of a sentence before a consonant, use у**.

«Я в університеті.»

The word «я» ends in a vowel — so «в» follows.

«Він у університеті.»

The word «він» ends in a consonant — so «у» follows.

The same logic applies everywhere:

«Ми в Харкові.» — «ми» ends in a vowel.

«Студент у Харкові.» — «студент» ends in a consonant.

At the beginning of a sentence, check the first sound of the next word. Before a consonant, use «у»: «У Києві є метро.» Before a vowel, use «в»: «В Одесі є море.»

A common learner error: «В вторник.» This is wrong in two ways — «вторник» is a Russian word, and «в в» breaks euphony. The correct Ukrainian form: «У вівторок.»

### І/Й

The same phonetic logic governs the conjunction **і/й** *(and)*: **after a consonant or at sentence start, use і**; **after a vowel, use й**.

«Мати і батько.» — «мати» ends in a vowel? No — the sound is [и], classified as a vowel, so this seems contradictory. The practical rule: «і» is the default form, «й» appears after clear open vowels.

«Батько й мати.» — «батько» ends in [о], a vowel — so «й» follows.

«Марія й Олег.» — «Марія» ends in [а] — so «й».

«Олег і Марія.» — «Олег» ends in a consonant — so «і».

Note: both the **сполучник** *(conjunction)* і/й and the **прийменник** *(preposition)* у/в obey the same vowel-consonant logic. Russian «и» has no such alternation. Милозвучність — це суто українська риса.

### З/Зі/Із

The preposition **з** *(from, with)* has three forms. Use «з» before most words starting with a single consonant or a vowel: «з Канади», «з Києва», «з тобою.» Use **зі** before consonant clusters that are hard to pronounce — especially лв-, шк-, зл-, зб-: «зі Львова», «зі школи», «зі зламаним замком.» Use **із** before words starting with з- or с-: «із Запоріжжя», «із сестрою.»

The rule of thumb: whichever variant flows most smoothly when you say it aloud is almost always correct.

<!-- INJECT_ACTIVITY: match-up, Euphony Choice Exercise -->

Милозвучність becomes automatic with exposure. Native speakers do not consciously apply these rules — they hear what sounds natural. For learners, the best practice is simple: read Ukrainian text aloud, paying attention to transitions between words. When something sounds awkward — two consonants colliding, two vowels bumping — that is your ear signaling a euphony error. Спробуйте читати вголос щоразу, коли вивчаєте нові тексти. By B1, these choices will feel natural rather than calculated.

## Що нас чекає на рівні А2? (What Awaits Us in A2?)

At A1, you learned four cases — enough to name things, point to them, say where you are, and call someone by name. Three new cases will unlock the rest of Ukrainian communication.

**Родовий відмінок** *(Genitive case)* answers «Кого? Чого?» and expresses what English handles with "of," "no," and quantity words. Right now you cannot say whose book it is. After Genitive: «Це книга **брата**.» You cannot negate existence. After Genitive: «У мене нема **часу**.» You cannot count beyond one. After Genitive: «Багато **студентів** приїхали з різних країн.»

**Давальний відмінок** *(Dative case)* answers «Кому? Чому?» — it marks the recipient, the person affected. «Я дав книгу **другові**.» Remember the dialogue? «**Мені** двадцять п'ять років.» That was Dative — age in Ukrainian belongs to the person, not describes them. Obligation works the same way: «**Студентам** треба вчитися щодня.»

**Орудний відмінок** *(Instrumental case)* answers «Ким? Чим?» — the tool, the companion, the profession. «Я пишу **ручкою**.» «Я іду **з другом** у кафе.» «Він є **лікарем**.» These three patterns — tool, company, identity — appear in nearly every Ukrainian conversation.

Aspect is the conceptual heart of A2. Ukrainian verbs come in pairs: **недоконаний вид** *(imperfective)* for ongoing or repeated actions, **доконаний вид** *(perfective)* for completed, single events. «Я **читав** цю книгу щодня.» — a habit, repeated. «Я **прочитав** цю книгу вчора.» — finished, done. Core pairs to learn: читати/прочитати, писати/написати, говорити/сказати, робити/зробити. Dedicated modules on aspect begin in A2.2.

Ukrainian also has a dedicated system for **дієслова руху** *(verbs of motion)*. Two core pairs: **іти/ходити** *(on foot)* and **їхати/їздити** *(by vehicle)*. «Я **іду** зараз на урок.» — one direction, right now. «Я **ходжу** на уроки щодня.» — habitual, repeated. Prefixes transform meaning entirely: при-їхати *(arrive)*, ви-їхати *(depart)*, пере-їхати *(cross)*. Mastering motion verbs unlocks travel, daily routines, and storytelling.

A1 gave you simple facts. A2 is the inflection point — you begin to **explain**, **compare**, and **narrate**. Пригадайте початок уроку. Майкл сказав: «Я з Канади» і «Я живу в Києві.» By the end of A2, he will say: «Книга, яку я купив **у центрі міста**, написана **відомим українським автором**.» Шлях починається тут.

**Deterministic word count: 2768 words** (calculated by pipeline, do NOT estimate manually)

</generated_module_content>

---

## Review Protocol

### Step 1: Scan for linguistic errors

Scan the Ukrainian text for errors. Report ONLY problems found — do not echo correct text.

**Four SEPARATE checks (these are four different problems):**
1. **Russianisms** — Russian words used instead of Ukrainian (кот→кіт, хорошо→добре, конечно→звичайно, сейчас→зараз)
2. **Surzhyk** — mixed Russian-Ukrainian forms (шо→що, чо→чому, тіпа→типу)
3. **Calques** — literal translations from Russian that sound wrong in Ukrainian (приймати душ→брати душ, приймати рішення→ухвалювати рішення)
4. **Paronyms** — similar-sounding words with different meanings used incorrectly (тактична≠тактовна, ефектний≠ефективний)

**Also check:**
- Russian characters (ы, э, ё, ъ) — these must NEVER appear
- Incorrect gender assignment or case endings
- Factually wrong claims about Ukrainian phonetics, grammar, or culture

**Authority hierarchy for verification (check in this order):**
1. VESUM — does this word/form exist? POS? Gender? (415K lemmas)
2. Правопис 2019 — is it spelled correctly? Orthography rules.
3. Горох — stress position, word frequency, synonyms.
4. Антоненко-Давидович «Як ми говоримо» — is this natural Ukrainian or a calque/Russicism?
5. Грінченко «Словарь» — etymology, original meaning.

**Online fallbacks (if RAG/tools are unavailable):**
- VESUM: https://vesum.com.ua/
- Правопис 2019: https://2019.pravopys.net/
- Горох: https://goroh.pp.ua/
- Антоненко-Давидович: https://www.ukrlib.com.ua/books/printit.php?tid=4002
- Грінченко: https://hrinchenko.com/
- Словник.ua (aggregator): https://slovnyk.me/

**VESUM verification data is provided at the end of this prompt.** Use it to verify word existence before flagging linguistic errors. If a word is marked ✓ in the VESUM data, it EXISTS in Ukrainian — do not flag it as an error. If a word is marked ✗ (NOT IN VESUM), investigate further — it may be a proper noun, a compound, or genuinely wrong.

**CRITICAL: Your pre-training is contaminated by Russian.** Do NOT trust your instincts about Ukrainian words. If you are not 100% certain a word/form/usage is wrong, you MUST flag it as `[NEEDS RAG VERIFICATION]` instead of marking it as a definitive error. Wrong review findings cause wrong fixes. A false positive in the review is worse than a missed error.

If no errors found, state: "No linguistic errors found."

**Do NOT check for stress marks** — stress annotation is handled by a separate deterministic tool after the review phase. Their absence is correct.

### Step 2: Check exercises

The writer places `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. A separate ACTIVITIES step generates structured YAML exercises (`activities/{slug}.yaml`) that are injected at these markers during PUBLISH.

Check the markers and any inline exercises:
- Does each marker appear AFTER the relevant teaching section? (exercise should test what was just taught)
- Do marker IDs match the plan's `activity_hints`? (each hint should have a corresponding marker)
- Are markers spread evenly through the module? (not clustered at the end)
- For seminar modules: DSL exercise blocks (:::quiz, :::fill-in) may appear inline — check their logic

For each exercise (DSL or marker), check:
- Does the exercise test what was just taught? (language skill, not content recall)
- Is the logic correct? (correct answers are actually correct, distractors are plausible but wrong)
- Can a learner complete this with the knowledge taught so far in this module?
- Does the exercise match one of the plan's `activity_hints` in type and focus?

Also check: Are there enough exercise markers/blocks total? The plan's `activity_hints` specifies the expected count.

**Note:** Exercise content is generated by a separate tool from YAML. If exercise LOGIC is wrong, flag it. If the FORMAT looks unusual (React components, YAML structure), that is expected.

### PROOF OF ABSENCE — mandatory before claiming ANYTHING is missing

**Before you claim a word, symbol, notation, or plan point is MISSING from the content, you MUST search for it.** Use your MCP tools (`verify_words`, `search_text`) or carefully re-read the specific section where it should appear.

Rules:
- If you claim "[•] notation is missing" — you must have searched the content for `[•]` and confirmed 0 occurrences
- If you claim "vocabulary word X is missing" — you must have searched for that exact word
- If you claim "plan point Y was not covered" — you must quote which section you expected it in and confirm it's not there
- **NO CLAIMS OF ABSENCE WITHOUT EVIDENCE.** Your tokenizer can miss special characters like [•], [–], [=], «», and other non-alphanumeric symbols. Do not trust a quick scan.
- Euphony alternation (у/в, і/й) is a MINOR stylistic issue, NEVER a critical error. Both forms are attested in published Ukrainian literature.

**A false finding wastes an entire rebuild cycle. Be precise.**

### Step 3: Score on 9 dimensions

Rate each dimension 1-10 with SPECIFIC evidence (cite the section/paragraph, quote the actual text).

| # | Dimension | Weight | What to check |
|---|-----------|--------|---------------|
| 1 | **Plan adherence** | 15% | DEDUCT for: missing content_outline points, section word budgets off by >10%, plan references not cited, vocabulary from plan absent from prose. REWARD for: every plan point covered with specific examples, correct section pacing, textbook references integrated naturally. Quote the plan point that was missed or covered. |
| 2 | **Linguistic accuracy** | 15% | All Ukrainian correct? No Russianisms/Surzhyk/calques? Correct phonetic descriptions? Gender/case correct? |
| 3 | **Pedagogical quality** | 15% | DEDUCT for: grammar rules presented as bare lists without examples, concepts taught before prerequisite knowledge, >100 words of English theory without a Ukrainian example, bare vocabulary lists instead of contextualized introduction. REWARD for: PPP flow (situation→pattern→practice), 3+ examples per grammar point, textbook pedagogy (Большакова, Захарійчук), grammar scope respected. |
| 4 | **Vocabulary coverage** | 10% | All required vocab from plan used naturally in prose? Recommended vocab included? New words introduced in context, not as lists? |
| 5 | **Exercise quality** | 15% | DEDUCT for: all correct answers at the same index position, trivially easy exercises (1:9 group sort ratios, every answer is the same word), exercises that test content recall instead of language skill, items fewer than plan's activity_hints count, exercises placed before the concept is taught. REWARD for: varied answer positions, plausible distractors, exercises testing what was just taught, matching plan's activity_hints type and focus exactly. |
| 6 | **Engagement & tone** | 10% | DEDUCT for: motivational openers ("Numbers unlock the real Ukraine!"), meta-commentary ("Let us look at...", "Let us now explore..."), generic enthusiasm ("incredibly melodic", "hugely important"), telling instead of showing ("You now possess...", "You have unlocked..."), gamified language ("unlocked the ability"), corporate-speak ("precision and accuracy"), "The magic of...", any sentence that could apply to any language course unchanged. REWARD for: specific cultural details, natural dialogues, humor, concrete examples, teacher demonstrating rather than lecturing about how great the content is. |
| 7 | **Structural integrity** | 5% | DEDUCT for: missing H2 headings from plan, duplicate summary sections, meta-commentary sections ("Content notes:"), word count outside target range, stray tags or formatting artifacts. REWARD for: clean markdown, all sections present and ordered correctly, word count in range. |
| 8 | **Cultural accuracy** | 5% | Decolonized (Ukrainian on its own terms, never "like Russian but...")? Factually correct claims about Ukrainian? Respectful representation? |
| 9 | **Dialogue & conversation quality** | 10% | DEDUCT for: purely transactional exchanges ("Do you have X? Yes."), dialogues where one speaker interrogates the other, anonymous em dashes instead of named speakers, stilted/textbook-robotic phrasing. REWARD for: natural multi-turn conversations, real situations (searching for keys, ordering at a cafe, meeting a friend), culturally appropriate responses, named speakers with distinct voices. |

**Note:** Vocabulary tables (словник), video embeds, and external resource links are added by a downstream ENRICH step — do NOT penalize their absence or quality. If you see a vocabulary table with wrong translations, missing words, or formatting issues, that content was NOT written by the writer — it was generated deterministically by the ENRICH step. Do NOT flag словník problems as linguistic errors or deduct points from the writer. Report them separately under "ENRICH issues" in your findings (informational only, not scored).

### Step 4: Output raw scores

Output ONLY the raw 1-10 scores in the table below. Do NOT calculate the weighted total — the pipeline script handles the math deterministically. Just write your per-dimension scores.

### Step 5: List findings

**CRITICAL RULE: If you mention ANY error, mistake, or inaccuracy in the evidence column of your scores table, you MUST also list it as a structured finding below AND include it in your `<fixes>` block.** Identifying an error in evidence but not outputting a finding+fix means the error ships to learners. This is a language curriculum — every error you identify must be fixed. No exceptions.

For every issue found, provide:
```
[DIMENSION] [SEVERITY: critical/major/minor]
Location: [specific section/paragraph — quote the actual text]
Issue: [what's wrong]
Fix: [exactly how to fix it]
```

Severity guide:
- **Critical** = factual/linguistic error that teaches wrong Ukrainian (wrong form, wrong rule, wrong example). Module cannot ship.
- **Major** = quality below standard but not factually wrong (weak explanation, awkward phrasing, missing examples).
- **Minor** = polish item (tone, word choice, style).

**Any factual or linguistic error is CRITICAL, not minor.** A wrong syllable division, a wrong phonetic claim, a contradictory grammar rule — these are critical because learners will memorize them as truth.

### Step 6: Verdict

Base your verdict on the **severity of findings** — the pipeline calculates the weighted score separately.

| Verdict | Condition |
|---------|-----------|
| **PASS** | Zero findings mentioning errors/mistakes/inaccuracies. All dimensions ≥9. |
| **REVISE** | Has findings with fixes. Any dimension <9 with identified errors = REVISE, not PASS. |
| **REJECT** | Fundamental structural/pedagogical problems requiring rewrite. |

### Step 7: Fix it yourself (REVISE only)

If your verdict is **REVISE**, you MUST output a `<fixes>` block with exact find/replace pairs. The pipeline applies these deterministically — no LLM regeneration, no rewriting from scratch.

Rules for fixes:
- Each fix is a YAML entry with `find:` (exact text from the module) and `replace:` (corrected text)
- The `find` string must be an EXACT substring of the module content — copy-paste it
- Keep fixes minimal — change only what's wrong, preserve surrounding text
- Do NOT fix словник/vocabulary tables (those are generated by a downstream tool)
- For word count issues: add content as a new `insert_after:` entry instead of find/replace

---

## Output Format

```
## Linguistic Scan
[errors found, or "No linguistic errors found"]

## Exercise Check
[placeholder inventory and issues]

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | X/10 | [specific evidence from the text] |
| ... | ... | ... |

## Findings
[list all findings with dimension/severity/location/issue/fix]

## Verdict: PASS / REVISE / REJECT
[justification — reference both score gate and severity gate]

<fixes>
- find: "exact text from module"
  replace: "corrected text"
- find: "another exact problem"
  replace: "the fix"
</fixes>
```

**The `<fixes>` block is REQUIRED for REVISE verdicts.** Without it, the pipeline cannot apply your fixes. For PASS verdicts, omit the `<fixes>` block. For REJECT verdicts, the module needs a full rebuild — `<fixes>` is optional.


<vesum_verification>
The following Ukrainian words from the content were verified against VESUM (415K lemmas). Use this data to check linguistic claims — do NOT guess about words.

Verified: 331 words | Not found: 24 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Василь — NOT IN VESUM
  ✗ Василю — NOT IN VESUM
  ✗ Ганна — NOT IN VESUM
  ✗ Ганно — NOT IN VESUM
  ✗ Запоріжжя — NOT IN VESUM
  ✗ Канади — NOT IN VESUM
  ✗ Києва — NOT IN VESUM
  ✗ Львова — NOT IN VESUM
  ✗ Львові — NOT IN VESUM
  ✗ Майкл — NOT IN VESUM
  ✗ Майкл' — NOT IN VESUM
  ✗ Майкле — NOT IN VESUM
  ✗ Марія — NOT IN VESUM
  ✗ Маріє — NOT IN VESUM
  ✗ Одесі — NOT IN VESUM
  ✗ Олег — NOT IN VESUM
  ✗ Олена — NOT IN VESUM
  ✗ Сергій — NOT IN VESUM
  ✗ Сергію — NOT IN VESUM
  ✗ Тарас — NOT IN VESUM
  ✗ Тарасе — NOT IN VESUM
  ✗ Харкові — NOT IN VESUM
  ✗ вторник — NOT IN VESUM
  ✗ розрізнювач — NOT IN VESUM

All 331 other words are confirmed to exist in VESUM.

</vesum_verification>

## Verification Tools (MCP)

You have MCP tools to VERIFY claims in the content. Use them to cite evidence:

**Core Verification:**
- `mcp_rag_verify_words` — batch-verify Ukrainian words against VESUM (409K lemmas)
- `mcp_rag_verify_lemma` — full declension/conjugation for a lemma
- `mcp_rag_search_style_guide` — **HIGH PRIORITY.** Check for calques/Russianisms (Антоненко-Давидович)
- `mcp_rag_query_r2u` — Russian→Ukrainian equivalents. Confirm Russicism alternatives.
- `mcp_rag_query_pravopys` — verify orthography rules (Правопис 2019)

**Content Quality:**
- `mcp_rag_query_cefr_level` — verify vocabulary is level-appropriate (PULS, 5.9K words)
- `mcp_rag_search_definitions` — exact Ukrainian definitions (СУМ-11, 127K entries)
- `mcp_rag_search_etymology` — historical forms, etymology (Грінченко, 67K entries)
- `mcp_rag_search_idioms` — verify idioms are authentic Ukrainian (25K entries)
- `mcp_rag_search_synonyms` — suggest better word choices (Ukrajinet, 122K synsets)
- `mcp_rag_query_grac` — check collocations and frequency in GRAC corpus (2B tokens)

**Reference:**
- `mcp_rag_search_text` — check how textbooks teach the topic (Grades 1-11)
- `mcp_rag_search_literary` — verify literary references against primary sources
- `mcp_rag_query_wikipedia` — fact-check historical/cultural claims

**Evidence standard:** A review that says "this might be a Russicism" is WEAK. A review that says "`search_style_guide` confirms 'приймати участь' is a calque — correct form: 'брати участь'" is STRONG. Cite tool results.
