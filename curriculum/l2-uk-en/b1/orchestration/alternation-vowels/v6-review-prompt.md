# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 8: Чергування голосних (B1, B1.2 [Morphophonemics & Noun Subclasses])
**Writer:** Gemini Pro
**Word target:** 4000

## Plan (source of truth)

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
content_outline:
- section: "Що таке чергування голосних? (What is vowel alternation?)"
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
- section: "Чергування [о], [е] з [i] (The [o]/[e] to [i] alternation)"
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
- section: "Чергування [о], [е] з нулем звука (Fleeting vowels)"
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
  - "Rule from Караман Grade 10 p.56:
    After [ж], [ч], [ш], [дж], [й]:
    — write е before м'який приголосний or before syllables with [е], [и]:
    вечеря, вишень, джерело, женити.
    — write о before твердий приголосний or before syllables with [а], [о], [у]:
    бджола, будиночок, пшоно, знайомий."
  - "Exceptions to memorize: чепурний, шепіт, жебоніти, щедрий,
    черствий, чекати (е despite the rule), and чоло, бджола (о despite
    the rule). These are listed explicitly in Караман Grade 10 p.56."
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
- section: "Підсумок: правила i практика (Summary and practice)"
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
- title: "Караман Grade 10, p.55-56"
  notes: "Чергування [о] з [е] після шиплячих: rule formulation,
    exceptions, practice exercises."

</plan_content>

## Generated Content

<generated_module_content>
## Що таке чергування голосних? (What is vowel alternation?)

Уявіть: ви вже знаєте слово «стіл». Ви хочете сказати «на столі» — і раптом літера «і» зникає, а замість неї з'являється «о». Чому «стіл», але «столу»? Чому «сіль», але «солі»? Це не випадковість і не виняток — це система. В українській мові звуки в корені слова змінюються за чіткими правилами, і ці правила пов'язані з поняттями, які ви вже знаєте з першого модуля: **голосний** (vowel), **приголосний** (consonant), **наголос** (stress), **відкритий склад** (open syllable) і **закритий склад** (closed syllable). Усі ці фонетичні характеристики не просто описують вимову — вони активно визначають, як пишуться українські слова. Те, що здавалося окремими фактами про звуки, тепер стає ключем до правопису.

Це мовне явище називається **чергування** (alternation) — систематична зміна звуків у **корені** (root) слова при словозміні або словотворенні. Як пояснює підручник Авраменка для п'ятого класу: «Іноді, коли утворюємо нове слово або його форму, звук може змінюватися на інший: сіль — соляний, солі; корінь — кореня. Це мовне явище називають чергуванням звуків.» Зверніть увагу на ці приклади: у слові «сіль» кореневий голосний — [і], а у слові «соляний» він стає [о]. У слові «корінь» є голосний [е] у другому складі, а у **формі слова** (word form) «кореня» цей голосний зберігається, але в інших формах може змінюватися. Чергування — це не помилка мовця, а закономірність, вбудована в саму структуру української мови.

Чому це так важливо? Тому що **чергування голосних** (vowel alternation) — визначальна риса української фонології, яка вирізняє її серед інших східнослов'янських мов. Як зазначає Глазова у підручнику для десятого класу: «Таке чергування характерне для української мови й вирізняє її серед інших східнослов'янських мов.» У російській мові, наприклад, слово «стол» зберігає голосний «о» в усіх відмінках: стол, стола, столу. В українській мові — «стіл», але «столу», «на столі». Ця система не ускладнює мову — навпаки, вона робить її логічною. Коли ви зрозумієте правила чергування, ви зможете правильно писати тисячі слів без зубріння кожної окремої форми. Замість того щоб запам'ятовувати, що «двір» у родовому відмінку — «двору», ви просто застосуєте правило.

У цьому модулі ми розглянемо три основні типи чергування голосних. Перший — це чергування [о] та [е] з [і], пов'язане з правилом відкритого та закритого складу: дво-ри (відкритий) → двір (закритий). Другий — чергування [о] та [е] з **нулем звука** (zero sound), коли голосний просто зникає: день → дня. Такі голосні називають **випадними (біглими) голосними** (fleeting vowels). Третій — чергування [о] з [е] після **шиплячих** (hushing consonants: ж, ч, ш, дж) та [й]: бджола, але вечеря. Кожен тип має свою логіку, свої закономірності та свої винятки. Опанувавши їх, ви отримаєте потужний інструмент для **правопису** (orthography) — замість механічного запам'ятовування ви будете розуміти, чому слово пишеться саме так.

## Чергування [о], [е] з [i] (The [o]/[e] to [i] alternation)

Це найпоширеніший і найважливіший тип чергування в українській мові. Правило сформульоване чітко у підручнику Заболотного для п'ятого класу: коли склад змінюється з відкритого на закритий або навпаки, голосний [о] або [е] у корені чергується з [і]. Пригадаймо: **відкритий склад** (open syllable) закінчується на голосний звук: дво-ри, ко-ні, ро-ку. **Закритий склад** (closed syllable) закінчується на приголосний: двір, кінь, рік. Отже, схема виглядає так: [о] або [е] у відкритому складі перетворюється на [і] у закритому складі — і навпаки. Це не виняток — це регулярна, передбачувана закономірність.

Розглянемо систематичні приклади для іменників. Називний **відмінок** (grammatical case) має закритий склад (і тому [і] в корені), а родовий відмінок відкриває склад (і [і] повертається до [о] або [е]):

| Називний (закритий склад) | Родовий (відкритий склад) | Чергування |
|---|---|---|
| стіл | столу | [і] ~ [о] |
| двір | двору | [і] ~ [о] |
| сіль | солі | [і] ~ [о] |
| віз | воза | [і] ~ [о] |
| ніс | носа | [і] ~ [о] |
| рік | року | [і] ~ [о] |
| річ | речі | [і] ~ [е] |

Зверніть увагу: у парі «річ — речі» чергується [і] з [е], а не з [о]. Який саме голосний з'являється — [о] чи [е] — залежить від історичного кореня слова. Але принцип однаковий: закритий склад → [і], відкритий склад → [о] або [е].

Це ж правило працює для прикметників і дієслів. У прикметниках чергування видно при порівнянні похідних форм: **осінній** (autumn, adj.) має [і] у закритому складі «осін-», але **спільнокореневе** (cognate) слово «осени» — [е] у відкритому складі «о-се-ни». Так само **вечірній** (evening, adj.) — від «вечора»: закритий склад «вечір-» дає [і], відкритий «ве-чо-ра» зберігає [о]. Серед дієслів: «нести» — «ніс» (закритий склад: ніс), «везти» — «віз» (закритий склад: віз). Форми минулого часу чоловічого роду мають закритий склад, тому кореневий голосний стає [і].

Але не кожне слово підкоряється цьому правилу. Запозичені слова, як правило, не чергуються. Слово «мотор» у родовому відмінку має форму «мотору», а не «*мотіру». Так само «доктор — доктора», «професор — професора». Деякі питомо українські слова також мають застиглі форми, де чергування не відбувається. Ці винятки треба запам'ятовувати окремо, але їх значно менше, ніж слів, що підкоряються правилу. Якщо слово — давнє українське, чергування майже напевно працює. Якщо слово запозичене з латини, грецької чи іншої мови — швидше за все, ні.

:::fill-in
title: "Застосуйте правило відкритого та закритого складу"
---
- sentence: "двір — двор___"
  answer: "у"
- sentence: "стіл — стол___"
  answer: "у"
- sentence: "рік — рок___"
  answer: "у"
- sentence: "сіль — сол___"
  answer: "і"
- sentence: "ніс — нос___"
  answer: "а"
- sentence: "віз — воз___"
  answer: "а"
- sentence: "кінь — кон___"
  answer: "я"
- sentence: "річ — реч___"
  answer: "і"
:::

А тепер прочитайте цей короткий текст і зверніть увагу на слова з чергуванням:

«Село прокидається рано. На подвір'ї стоїть великий стіл — дідусь виніс його ще ввечері. Біля воріт сидить кіт і дивиться на двір. У хаті тепло: піч горить з ранку. Через вікна видно білий сніг на полі. На розі вулиці стоїть старий віз — колись ним возили сіль із далеких міст. Тепер він стоїть без діла, і лід покрив його колеса. Рік минає, другий рік настає, а двори в селі все ті самі — тихі, затишні, з духом хліба і диму.»

Цей текст — справжня скарбниця чергувань. Знайдімо їх усі. «Двір» — закритий склад, [і] в корені. Але «на подвір'ї» — закритий склад зберігається, тому [і] залишається. А ось «двори» — від-кри-тий склад «дво-ри», тому [о]. Пара: двір — двори, [і] ~ [о]. «Стіл» — закритий склад, [і]. Але коли ми говоримо «на столі», родовий «столу» — відкритий склад, [о]. Пара: стіл — столу. «Кіт» — закритий склад, [і], а «кота» — відкритий, [о]. Пара: кіт — кота. «Сніг» — тут [і] у закритому складі; «снігу» зберігає закритий склад, а у формі «сніговий» [і] також зберігається. Чому? Бо [і] у слові «сніг» походить від давнього звука [ě] (ять), який в українській мові став [і] в усіх позиціях — і у відкритому, і в закритому складі. Тому правило чергування [о]/[е] з [і] до нього не застосовується. «Віз» — закритий склад, [і]; «возили» — від-кри-тий, [о]. Пара: віз — возити. «Сіль» — закритий склад, [і]; «солі» — відкритий, [о]. «Рік» — «року»: [і] ~ [о]. «Лід» — «льоду»: [і] ~ [о] з появою м'якого знака. Бачите, як одне правило пояснює десятки слів?

## Чергування [о], [е] з нулем звука (Fleeting vowels)

Другий тип чергування ще драматичніший: голосний не просто змінюється на інший — він зникає повністю. Як пояснює Заболотний у підручнику для п'ятого класу: у деяких словах [о] або [е] зникає зовсім при зміні форми слова. Голосний присутній в одній формі, але відсутній в іншій. Це називається «чергування з **нулем звука**» (zero sound), а самі голосні, що зникають, називають **випадними (біглими) голосними** (fleeting vowels). Наприклад: «день» має [е] у називному відмінку, але «дня» — голосного немає взагалі. Він «втік» — і назва «біглий голосний» передає саме цю ідею.

Найчастіше біглі голосні зустрічаються в іменниках чоловічого роду. Голосний [е] або [о] в останньому складі називного відмінка зникає, коли додається **закінчення** (ending) непрямого відмінка. Ось основні приклади:

| Називний | Родовий | Що зникло |
|---|---|---|
| учень | учня | [е] зник |
| день | дня | [е] зник |
| вітер | вітру | [е] зник |
| сон | сну | [о] зник |
| хлопець | хлопця | [е] зник |
| пень | пня | [е] зник |

Зверніть увагу: деякі слова, як-от «камінь — каменя», виглядають схоже, але це не біглий голосний — там [і] чергується з [е] за правилом відкритого та закритого складу з попереднього розділу. Справжній біглий голосний — це коли звук зникає повністю, як у «сон — сну»: голосного [о] у формі «сну» просто немає.

Біглі голосні часто з'являються в певних **суфіксах** (suffix). Запам'ятайте три найпоширеніші моделі. Суфікс **-ець/-ця**: молодець — молодця, хлопець — хлопця. Голосний [е] у суфіксі -ець зникає в непрямих відмінках. Суфікс **-ок/-ка**: замок — замка, гурток — гуртка. Голосний [о] у суфіксі -ок зникає. Суфікс **-ень/-ня**: корінь — кореня, пень — пня. Тут також [е] зникає при додаванні закінчення. Знання цих суфіксів дозволяє передбачити: якщо іменник чоловічого роду закінчується на -ець, -ок або -ень, його голосний, найімовірніше, біглий.

:::match-up
title: "Знайдіть пари: називний та непрямий відмінки"
---
- left: "сон"
  right: "сну"
- left: "молодець"
  right: "молодця"
- left: "день"
  right: "дня"
- left: "вітер"
  right: "вітру"
- left: "хлопець"
  right: "хлопця"
- left: "замок"
  right: "замка"
- left: "гурток"
  right: "гуртка"
- left: "пень"
  right: "пня"
:::

Але як відрізнити біглий голосний від стабільного? Один із способів — подумати про приголосні, які залишаються після зникнення голосного. Якщо видалення голосного створює групу приголосних, що здається неможливою, голосний може бути стабільним. Але обережно: українська мова добре толерує складні групи приголосних, як-от «-дня» (від «день — дня») або «-тру» (від «вітер — вітру»). Порівняйте мінімальні пари: «сон — сну» (голосний [о] біглий — він зникає в родовому відмінку) проти «стогін — стогону» (голосний [о] стабільний — він зберігається). Чому? Тому що «сон» належить до іншого типу відмінювання, ніж «стогін». Єдиний надійний спосіб — перевірити форму в словнику або запам'ятати типові суфікси.

Спробуйте самостійно передбачити, що відбудеться з голосним у родовому відмінку цих слів: «вогонь», «перець», «палець». Чи зникне голосний? «Вогонь — вогню» — так, [о] біглий. «Перець — перцю» — так, [е] біглий. «Палець — пальця» — так, [е] біглий. Модель передбачувана: суфікси -ець, -онь майже завжди мають біглий голосний.

## Чергування [о] з [е] після шиплячих та [й]

Третій тип чергування стосується вибору між [о] та [е] після особливої групи приголосних — **шиплячих** (hushing consonants): [ж], [ч], [ш], [дж], а також після [й]. Як пояснює Караман у підручнику для десятого класу, правило має дві частини. Перша: після шиплячих та [й] пишемо **е**, якщо наступний приголосний — **м'який** (soft, palatalized) або якщо в наступному складі є голосний [е] чи [и]. Приклади: «вечеря» (після [ч] стоїть м'який [р'], далі — [а]), «вишень» (після [ш] стоїть м'який [н']), «джерело» (після [дж] — [е] в наступному складі), «женити» (після [ж] — [е] в наступному складі).

Друга частина правила: після шиплячих та [й] пишемо **о**, якщо наступний приголосний — **твердий** (hard, non-palatalized) або якщо в наступному складі є голосний [а], [о] чи [у]. Приклади: «бджола» (після [дж] стоїть твердий [л], далі — [а]), «будиночок» (після [ч] — твердий [к]), «пшоно» (після [ш] — твердий [н], далі — [о]), «знайомий» (після [й] — твердий [м]). Ключ до правильного вибору — чутливість до наступного приголосного: він твердий чи м'який? І який голосний стоїть у наступному складі?

Але є винятки, які треба просто запам'ятати. Слова з [е] всупереч правилу: «чепурний», «шепіт», «жебоніти», «щедрий», «черствий», «чекати». У цих словах за правилом мало б стояти [о], але пишеться [е]. Слова з [о] всупереч правилу: «чоло», «бджола». Ці винятки перелічені у Карамана на сторінці 56, і їх варто виписати окремо як **орфограми** (orthographic rules) для запам'ятовування.

:::quiz
title: "Знайдіть і виправте помилки у написанні голосних після шиплячих"
---
- q: "Яке слово написане правильно?"
  o: ["вечоря", "вечеря", "вечіря"]
  a: 1
- q: "Оберіть правильний варіант: пш___но"
  o: ["пшено", "пшоно", "пшіно"]
  a: 1
- q: "Яке слово написане з помилкою?"
  o: ["бджола", "джерело", "жонити"]
  a: 2
- q: "Оберіть правильний варіант: ч___пурний"
  o: ["чопурний", "чепурний", "чіпурний"]
  a: 1
- q: "Яке слово має виняткове написання [е] після шиплячого?"
  o: ["пшоно", "шепіт", "бджола"]
  a: 1
- q: "Оберіть правильний варіант: ж___нити"
  o: ["жонити", "женити", "жінити"]
  a: 1
:::

Чому цей тип чергування такий важливий для тих, хто вивчає українську? Тому що саме ця **орфограма** — одне з найчастіших джерел помилок під впливом суржику. У російській мові такого розрізнення немає: після шиплячих завжди пишуть одну й ту саму літеру незалежно від м'якості чи твердості наступного приголосного. Тому носії російської та люди, які виросли в двомовному середовищі, часто плутають «о» та «е» після шиплячих в українських словах. Для свідомого українського **правопису** (orthography) треба щоразу ставити собі питання: що стоїть після шиплячого? Якщо м'який приголосний або склад з [е]/[и] — пишемо «е». Якщо твердий або склад з [а]/[о]/[у] — пишемо «о». А винятки — вчимо напам'ять.

## Чергування голосних у дієслівних коренях

До цього моменту ми розглядали чергування переважно в іменниках та прикметниках. Тепер перейдемо до дієслів, де чергування голосних у корені пов'язане з наголосом і суфіксами. Як показує Заболотний у вправі 275 (п'ятий клас), багато дієслівних пар демонструють регулярну зміну кореневого голосного:

| Дієслово 1 | Дієслово 2 | Чергування |
|---|---|---|
| летіти | літати | [е] ~ [і] |
| котити | катати | [о] ~ [а] |
| терти | стирати | [е] ~ [и] |

Ці пари — не випадковість. Вони відображають систематичний зв'язок між видовими формами дієслів або різними способами дії.

Який саме фонетичний механізм стоїть за цими змінами? Кореневий голосний реагує на те, що стоїть після нього — конкретно, на **суфікс** і на позицію **наголосу** (stress). Загальна модель: [е] ~ [і] ~ [и] залежно від суфікса (-а-, -и-, -іти-) та місця наголосу. Коли суфікс -а- перетягує на себе наголос, кореневий голосний змінюється. Наприклад, у парі «летіти — літати» наголос у «літати» падає на суфікс -а-, і кореневий [е] стає [і]. У парі «терти — стирати» кореневий [е] стає [и] перед наголошеним суфіксом -а-.

Вправа 276 у Заболотного дає ширший набір прикладів цієї системи:

| Дієслово 1 | Дієслово 2 | Чергування |
|---|---|---|
| захопити | хапати | [о] ~ [а] |
| сплести | сплітати | [е] ~ [і] |
| завмерти | завмирати | [е] ~ [и] |
| заберу | забирати | [е] ~ [и] |

Модель стає очевидною: перед наголошеним суфіксом -а- кореневий голосний змінюється передбачувано. [е] може стати [і] (сплести — сплітати) або [и] (завмерти — завмирати). [о] може стати [а] (захопити — хапати). Ця зміна сигналізує про видову або аспектну різницю між дієсловами.

А тепер — найцікавіше. Ви вже знаєте всі ці дієслова. На рівні А2 ви вивчили «забирати», «літати», «збирати» як окремі слова. Ви запам'ятовували їхні форми одну за одною. Тепер ви бачите систему, що стоїть за ними. «Заберу — забирати» — це не два різні слова з випадково схожими коренями. Це одне дієслівне гніздо, де кореневий голосний чергується за правилом. Те, що раніше здавалося винятками для зубріння, тепер стає продуктивним правилом. Ви можете передбачити форму незнайомого дієслова, якщо знаєте його пару. Це і є мета **морфонології** (morphophonology) — перетворити хаос на систему.

## Чергування i наголос: як вони пов'язані

Ми вже кілька разів згадували **наголос** (stress) як рушійну силу чергувань. Тепер поглянемо на цей зв'язок прямо. Ключова лінгвістична закономірність: коли наголос зміщується з кореневого голосного на інший склад (наприклад, на закінчення або суфікс), голосний у корені може змінитися. Найяскравіший приклад: «рік» — наголос на [і] у закритому складі. Але «років» — наголос зміщується на **закінчення** (ending), а в корені з'являється [о]. Або «двір» (наголос на [і]) — «дворів» (наголос на закінченні, корінь має [о]). Наголос ніби «тримає» [і] у корені, а коли він іде — [і] повертається до свого історичного стану [о] або [е].

Це спостереження веде до глибшого розуміння. Як зазначає Авраменко (п'ятий клас): чергування часто виявляє первісний голосний, який існував у корені до того, як відбувся історичний зсув до [і] в закритих складах. Іншими словами, [о] і [е] — це «старші» голосні, а [і] — результат фонетичного розвитку. Коли ми бачимо пару «стіл — столу», ми бачимо одночасно і сучасну мову, і її історію. [О] у «столу» — це той самий голосний, який був у корені сотні років тому. [І] у «стіл» — інновація, характерна саме для української мови. Ось чому це чергування вирізняє українську мову серед інших слов'янських.

Це знання має практичне застосування — стратегію перевірки правопису, яку називають «**перевірне слово**» (checking word). Литвінова пояснює у підручнику для п'ятого класу: «Якщо під час зміни слова сумнівний звук чергується з [і] в закритому складі — пишемо и: осені (бо осінь).» Як це працює? Якщо ви не впевнені, чи писати «е» чи «и» в **ненаголошеному** (unstressed) складі, змініть форму слова. Якщо в закритому складі з'являється [і] — значить, у відкритому складі треба писати «е». Наприклад: пишемо «осені» з «е», бо називний відмінок — «осінь» (з [і]). Пишемо «вечора» з «е», бо є форма «вечір» (з [і]). Це **перевірне слово** — форма того самого слова, де чергування підказує правильну літеру.

:::quiz
title: "Визначте тип чергування у парах слів"
---
- q: "рік — року"
  o: ["[о] ~ [і] (відкритий/закритий склад)", "біглий голосний", "чергування після шиплячого", "немає чергування"]
  a: 0
- q: "день — дня"
  o: ["[о] ~ [і] (відкритий/закритий склад)", "біглий голосний", "чергування після шиплячого", "дієслівне чергування"]
  a: 1
- q: "вечеря — вечора"
  o: ["[о] ~ [і]", "біглий голосний", "чергування [о] з [е] після шиплячого", "немає чергування"]
  a: 2
- q: "летіти — літати"
  o: ["[о] ~ [і]", "біглий голосний", "чергування після шиплячого", "дієслівне чергування в корені"]
  a: 3
- q: "стіл — столу"
  o: ["[о] ~ [і] (відкритий/закритий склад)", "біглий голосний", "чергування після шиплячого", "немає чергування"]
  a: 0
- q: "хлопець — хлопця"
  o: ["[о] ~ [і]", "біглий голосний", "чергування після шиплячого", "дієслівне чергування"]
  a: 1
- q: "пшоно — пшениця"
  o: ["[о] ~ [і]", "біглий голосний", "чергування [о] з [е] після шиплячого", "немає чергування"]
  a: 2
- q: "заберу — забирати"
  o: ["[о] ~ [і]", "біглий голосний", "чергування після шиплячого", "дієслівне чергування в корені"]
  a: 3
:::

Зведемо все до однієї таблиці:

| Тип чергування | Модель | Приклади | Тригер |
|---|---|---|---|
| [о]/[е] ~ [і] | Відкритий склад: [о]/[е]; закритий: [і] | стіл — столу, двір — двори | Зміна типу складу |
| Біглий голосний | Голосний є → голосного немає | день — дня, вітер — вітру | Додавання закінчення |
| Після шиплячих | [о] перед твердим; [е] перед м'яким | бджола, вечеря | Твердість/м'якість наступного приголосного |

## Підсумок: правила i практика (Summary and practice)

Як застосовувати знання про чергування голосних на практиці? Ось покроковий алгоритм для будь-якого слова, де ви сумніваєтесь у написанні:

**Крок 1:** Визначте тип складу. Склад відкритий (закінчується на голосний) чи закритий (закінчується на приголосний)? Якщо голосний [о] або [е] в одній формі стає [і] в іншій — це чергування [о]/[е] з [і] за правилом відкритого та закритого складу. Приклад: «дво-ри» (відкритий, [о]) → «двір» (закритий, [і]).

**Крок 2:** Чи зникає голосний повністю? Якщо в одній формі голосний є, а в іншій — ні, це біглий голосний. Приклад: «день» (є [е]) → «дня» (немає голосного).

**Крок 3:** Чи стоїть голосний після шиплячого ([ж], [ч], [ш], [дж]) або [й]? Тоді перевірте наступний приголосний: м'який → пишіть «е», твердий → пишіть «о». Приклад: «вечеря» (після [ч] м'який [р']).

**Крок 4:** Чи це дієслівний корінь зі зміною суфікса? Перевірте, чи наголошений суфікс -а- викликає чергування. Приклад: «заберу» → «забирати».

Дайте відповіді на запитання:

1. Чому в слові «двір» пишемо і, а в слові «двори» — о?
2. Яке чергування відбувається у словах «день — дня»?
3. Після яких приголосних чергуються [о] з [е]?
4. Запишіть три пари слів із чергуванням [о] ~ [і].

:::group-sort
title: "Розподіліть пари слів за типами чергування"
---
groups:
  - name: "Чергування [о] ~ [і]"
    items: ["стіл — столу", "двір — двору", "рік — року"]
  - name: "Чергування [е] ~ [і]"
    items: ["річ — речі", "вечір — вечора", "осінь — осені"]
  - name: "Біглий голосний"
    items: ["день — дня", "вітер — вітру", "пень — пня"]
  - name: "Немає чергування"
    items: ["мотор — мотору", "доктор — доктора", "професор — професора"]
:::

У наступному модулі ми перейдемо до **чергування приголосних в іменниках** — ще одного прояву морфонологічної системи, де приголосні змінюються за тими самими структурними принципами. Якщо в цьому модулі ми бачили, як [о] стає [і] і як зникають голосні, то в наступному побачимо, як [к] стає [ц'], [г] стає [з'], а [х] — [с']. Логіка та сама: зміна форми слова → зміна звука. Опанувавши обидва модулі, ви матимете повну картину того, як українська мова трансформує свої слова зсередини.

**Deterministic word count: 2943 words** (calculated by pipeline, do NOT estimate manually)

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

List every exercise block (`:::quiz`, `:::fill-in`, `:::match-up`, `:::group-sort`, `:::true-false`). These are filled exercises — a deterministic tool converted placeholders to real content.

For each exercise, check:
- Does the exercise test what was just taught? (language skill, not content recall)
- Is the logic correct? (correct answers are actually correct, distractors are plausible but wrong)
- Can a learner complete this with the knowledge taught so far in this module?
- Does the exercise match one of the plan's `activity_hints` in type and focus?
- Are there enough items per exercise? (check against plan's `activity_hints`)

Also check: Are there enough exercises total? The plan's `activity_hints` specifies the expected count.

**Note:** Exercises are generated by a deterministic tool from the writer's placeholders. If the exercise LOGIC is wrong (e.g., matching unrelated items), flag it — the tool's input data needs fixing. If the exercise FORMAT looks unusual, that is expected (the tool uses a specific DSL syntax).

### Step 3: Score on 9 dimensions

Rate each dimension 1-10 with SPECIFIC evidence (cite the section/paragraph, quote the actual text).

| # | Dimension | Weight | What to check |
|---|-----------|--------|---------------|
| 1 | **Plan adherence** | 15% | Every content_outline point covered? Section word budgets respected (±10%)? All plan references used? |
| 2 | **Linguistic accuracy** | 15% | All Ukrainian correct? No Russianisms/Surzhyk/calques? Correct phonetic descriptions? Gender/case correct? |
| 3 | **Pedagogical quality** | 15% | PPP (Present→Practice→Produce) applied? Textbook pedagogy used (Большакова, Захарійчук)? Grammar scope respected (no A2 in A1)? |
| 4 | **Vocabulary coverage** | 10% | All required vocab from plan used naturally in prose? Recommended vocab included? New words introduced in context, not as lists? |
| 5 | **Exercise quality** | 15% | Placeholders specific enough? Test the right skills? Placed after relevant teaching? Match plan's activity_hints? Sufficient items? |
| 6 | **Engagement & tone** | 10% | Interesting for teens/adults? Authoritative but warm (like a skilled teacher)? No LLM filler ("Good news!", "Don't panic!", "Fun fact!")? Cultural hooks? |
| 7 | **Structural integrity** | 5% | All H2 headings from plan present? Word count in range? No duplicate sections? No meta-commentary? Clean markdown? |
| 8 | **Cultural accuracy** | 5% | Decolonized (Ukrainian on its own terms, never "like Russian but...")? Factually correct claims about Ukrainian? Respectful representation? |
| 9 | **Dialogue & conversation quality** | 10% | Dialogues natural and culturally appropriate? Real situations, real responses? Speaker roles clear? Not stilted or textbook-robotic? |

**Note:** Vocabulary tables (словник), video embeds, and external resource links are added by a downstream ENRICH step — do NOT penalize their absence or quality. If you see a vocabulary table with wrong translations, missing words, or formatting issues, that content was NOT written by the writer — it was generated deterministically by the ENRICH step. Do NOT flag словník problems as linguistic errors or deduct points from the writer. Report them separately under "ENRICH issues" in your findings (informational only, not scored).

### Step 4: Output raw scores

Output ONLY the raw 1-10 scores in the table below. Do NOT calculate the weighted total — the pipeline script handles the math deterministically. Just write your per-dimension scores.

### Step 5: List findings

For every issue found, provide:
```
[DIMENSION] [SEVERITY: critical/major/minor]
Location: [specific section/paragraph — quote the actual text]
Issue: [what's wrong]
Fix: [exactly how to fix it]
```

Critical = module cannot ship. Major = quality below standard. Minor = polish item.

### Step 6: Verdict

Base your verdict on the **severity of findings** — the pipeline calculates the weighted score separately.

| Verdict | Condition |
|---------|-----------|
| **PASS** | Zero critical findings, at most minor issues |
| **REVISE** | Has major findings but no criticals — fixable without rewrite |
| **REJECT** | Has any critical finding — fundamental problems requiring rewrite |

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

Verified: 890 words | Not found: 26 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Авраменка — NOT IN VESUM
  ✗ Авраменко — NOT IN VESUM
  ✗ Біглий — NOT IN VESUM
  ✗ Глазова — NOT IN VESUM
  ✗ Караман — NOT IN VESUM
  ✗ Карамана — NOT IN VESUM
  ✗ Литвінова — NOT IN VESUM
  ✗ біглий — NOT IN VESUM
  ✗ біглими — NOT IN VESUM
  ✗ вечоря — NOT IN VESUM
  ✗ вечіря — NOT IN VESUM
  ✗ дво — NOT IN VESUM
  ✗ ень — NOT IN VESUM
  ✗ ець — NOT IN VESUM
  ✗ жонити — NOT IN VESUM
  ✗ жінити — NOT IN VESUM
  ✗ кри — NOT IN VESUM
  ✗ мотіру — NOT IN VESUM
  ✗ онь — NOT IN VESUM
  ✗ осін — NOT IN VESUM
  ✗ пшено — NOT IN VESUM
  ✗ пшіно — NOT IN VESUM
  ✗ стол — NOT IN VESUM
  ✗ тий — NOT IN VESUM
  ✗ чопурний — NOT IN VESUM
  ✗ чіпурний — NOT IN VESUM

All 890 other words are confirmed to exist in VESUM.

</vesum_verification>