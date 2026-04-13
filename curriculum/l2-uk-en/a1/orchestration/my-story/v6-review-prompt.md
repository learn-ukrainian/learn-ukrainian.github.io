<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 52: My Story (A1, A1.8 [Past, Future, Graduation])
**Writer:** Gemini
**Word target:** 1200

## Plan (source of truth)

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

## Generated Content

<generated_module_content>
## Dialogues

This module teaches a simple life story pattern: where you were born, where you live now, and what you plan to do next.
 

**Моя подорож**
Кожна людина має свою історію. Я народився в одному місті. Зараз я живу в іншому місті. Далі я буду працювати і вчитися. Це проста історія про життя.

> *Every person has their story. We live in different cities. We work a lot. We study interestingly. We have big plans. Next we will talk about this.*

When you meet someone new or talk to family, sharing your life journey is a natural step. Let's listen to a grandfather sharing his past, present, and future with his grandchildren.

> **Онук:** **Дідусю, розкажи про себе!** *(Grandpa, tell about yourself!)*
> **Дідусь:** **Я народився в селі.** *(I was born in a village.)*
> **Дідусь:** **Там я ходив у школу.** *(There I went to school.)*
> **Онука:** **А зараз ти живеш тут?** *(And now you live here?)*
> **Дідусь:** **Зараз я живу в місті.** *(Now I live in a city.)*
> **Дідусь:** **Я працюю в лікарні.** *(I work in a hospital.)*
> **Онук:** **А що ти будеш робити далі?** *(And what will you do next?)*
> **Дідусь:** **Я буду відпочивати на дачі!** *(I will rest at the dacha!)*

Now, let's look at another conversation where two friends, Marko and David, get to know each other deeply.

> **Марко:** **Розкажи про себе!** *(Tell about yourself!)*
> **Девід:** **Я народився в Канаді.** *(I was born in Canada.)*
> **Девід:** **Це було у Торонто.** *(It was in Toronto.)*
> **Марко:** **А зараз ти живеш тут?** *(And now you live here?)*
> **Девід:** **Так, зараз я живу в Києві.** *(Yes, now I live in Kyiv.)*
> **Марко:** **Чому ти переїхав?** *(Why did you move?)*
> **Девід:** **Я хотів вивчати українську.** *(I wanted to study Ukrainian.)*
> **Девід:** **Мої дідусь і бабуся з України.** *(My grandfather and grandmother are from Ukraine.)*
> **Марко:** **А що ти будеш робити далі?** *(And what will you do next?)*
> **Девід:** **Я буду працювати тут і вчити мову.** *(I will work here and study the language.)*
> **Марко:** **Цікаво. Тобі подобається Київ?** *(Interesting. Do you like Kyiv?)*
> **Девід:** **Так, мені тут добре.** *(Yes, I feel good here.)*
> **Марко:** **Чудово! Успіхів тобі!** *(Wonderful! Success to you!)*

This dialogue moves clearly through past, present, and future: origin, current life, then plans.

Anna's dialogue uses the same sequence: past in Lviv, present in Kyiv, then future plans.

> **Максим:** **Анно, розкажи свою історію.** *(Anna, tell your story.)*
> **Анна:** **Я народилася у Львові.** *(I was born in Lviv.)*
> **Анна:** **Там я вчилася в школі.** *(There I studied in school.)*
> **Анна:** **Потім я переїхала в Київ.** *(Then I moved to Kyiv.)*
> **Анна:** **Тут я закінчила університет.** *(Here I graduated university.)*
> **Анна:** **Зараз я працюю вчителькою.** *(Now I work as a teacher.)*
> **Анна:** **Я живу в центрі міста.** *(I live in the city center.)*
> **Максим:** **А що далі?** *(And what next?)*
> **Анна:** **Я буду подорожувати!** *(I will travel!)*
> **Анна:** **Я хочу побачити Японію.** *(I want to see Japan.)*
> **Максим:** **І ти будеш вчити японську?** *(And you will study Japanese?)*
> **Анна:** **Може! Але спочатку — українська!** *(Maybe! But first — Ukrainian!)*

Anna begins with her past in Lviv, using the feminine past tense verb **народилася**. She brings us to the present with **працюю**. Then she reveals her **мрія** (dream, f) for the future using **буду подорожувати**. 

## Три часи разом (Three Tenses Together)

A life story usually moves through three questions: where you were born, how you live now, and what you will do next. Here is how the three tenses work together.

**Мій брат**
Раніше мій брат жив у селі. Він багато читав. Зараз він живе в місті. Він працює в університеті. Далі він буде писати книгу. Він буде багато подорожувати.

> *Earlier my brother lived in a village. He read a lot. Now he lives in a city. He works at a university. Next he will write a book. He will travel a lot.*

The past tense (**минулий час**) is the foundation of your biography. When talking about yourself, the past tense strictly requires gender agreement for the pronoun **я** (I). A male speaker must use the masculine ending **-в**, while a female speaker must use the feminine ending **-ла**. This gender distinction is a core feature of the Ukrainian past tense. It is crucial to remember that the past tense does not change based on who you are talking to, but rather the gender of who is speaking or who you are talking about.

| Pronoun | Verb (to live) | English |
|---------|----------------|---------|
| Я (masculine) | **жив** | I lived |
| Я (feminine) | **жила** | I lived |
| Він (He) | **жив** | He lived |
| Вона (She) | **жила** | She lived |
| Ми (We) | **жили** | We lived |

*   **Я народився в місті.** *(I was born in a city. — masculine)*
*   **Я народилася в селі.** *(I was born in a village. — feminine)*
*   **Я жив тут.** *(I lived here. — masculine)*
*   **Я жила там.** *(I lived there. — feminine)*
*   **Я вчився добре.** *(I studied well. — masculine)*
*   **Я працювала в школі.** *(I worked in a school. — feminine)*

The present tense (**теперішній час**) describes your current situation and regular habits. Unlike the past tense, the present tense does not use gender endings. Instead, it relies on standard person endings based on the subject pronoun. The present tense focuses entirely on the person performing the action. Notice that the ending **-ю** is common for the first person singular (**я**).

| Pronoun | Verb (to live) | English |
|---------|----------------|---------|
| Я | **живу** | I live |
| Ти | **живеш** | You live |
| Він / Вона | **живе** | He / She lives |
| Ми | **живемо** | We live |

*   **Зараз я живу в місті.** *(Now I live in a city.)*
*   **Я працюю в лікарні.** *(I work in a hospital.)*
*   **Я вивчаю українську мову.** *(I am studying the Ukrainian language.)*
*   **Я люблю читати книги.** *(I love to read books.)*
*   **Мій друг працює програмістом.** *(My friend works as a programmer.)*

The future tense (**майбутній час**) allows you to share your goals. The most common and simple way to express the future is by using the compound form. You create this by combining the conjugated helper verb **бути** (to be) with the infinitive form of the main action verb. This compound future is incredibly flexible because you only need to conjugate the helper verb. The main verb always stays in its dictionary infinitive form.

| Pronoun | Verb (to work) | English |
|---------|----------------|---------|
| Я | **буду працювати** | I will work |
| Ти | **будеш працювати** | You will work |
| Він / Вона | **буде працювати** | He / She will work |
| Ми | **будемо працювати** | We will work |

*   **Я буду працювати тут.** *(I will work here.)*
*   **Я буду вивчати історію.** *(I will study history.)*
*   **Я буду жити в місті.** *(I will live in a city.)*
*   **Я буду подорожувати.** *(I will travel.)*
*   **Вона буде читати книгу.** *(She will read a book.)*

To help your listener clearly follow your story, you should use time signal words. These words act as anchors, marking tense shifts on your timeline. For the past tense, use words like **раніше** (before/earlier) or **у дитинстві**. For the present tense, use **зараз** (now) or **сьогодні** (today). For the future tense, use **потім** (then) or **далі** (further/next). These signal words prepare the listener for the grammar that follows.

*   **Раніше я жив у Лондоні.** *(Before I lived in London.)*
*   **Зараз я живу в Києві.** *(Now I live in Kyiv.)*
*   **Далі я буду жити в Одесі.** *(Next I will live in Odesa.)*

<!-- INJECT_ACTIVITY: matching-tense -->
<!-- INJECT_ACTIVITY: fill-in-signal-words -->

## Моя історія (My Story)

Now it is time to transition from individual sentences to a complete, structured monologue. Telling a personal narrative requires organization. A clear story always has three main parts: an introduction, a main body, and a conclusion. By combining your past, present, and future into this structure, you can confidently **розповідати** (to tell/narrate) your unique biography.

Let's read a model text that brings everything together. This is Taras's life story. Notice how he structures his narrative.

**Моя історія**
Я народився в Одесі у тисяча дев'ятсот дев'яносто п'ятому році. Я жив там з батьками і сестрою. Я ходив у школу. Я любив математику. Потім я переїхав у Київ. Там я вчився в університеті. Зараз я живу в Києві. Я працюю програмістом. Я люблю свою роботу. У вільний час я граю у футбол. Я читаю книжки. Далі я буду подорожувати. Я буду вивчати англійську. І я буду жити в Києві. Це моє місто!

> *I was born in Odesa in nineteen ninety-five. I lived there with my parents and sister. I went to school. I loved math. Then I moved to Kyiv. There I studied at a university. Now I live in Kyiv. I work as a programmer. I love my work. In my free time I play football. I read books. Next I will travel. I will study English. And I will live in Kyiv. This is my city!*

Let's deconstruct Taras's story to see how it works. His biography has a clear, logical chronological flow. He starts his introduction in the past to establish his background, using verbs like **народився** (was born), **жив** (lived), and **переїхав** (moved). Then, the main body transitions to his present reality using verbs like **живу** (live) and **працюю** (work). Finally, his conclusion looks to the future using the compound constructions **буду подорожувати** (will travel) and **буду вивчати** (will study).

Now it is your turn to create your own biography. Use this scaffolding template to build your narrative block by block. 

Start with your origin in the past tense: 
*   **Я народився / Я народилася в...** (I was born in...)
*   **Я жив / Я жила...** (I lived...)
*   **Я вчився / Я вчилася...** (I studied...)

Then, move your story to the present tense: 
*   **Зараз я живу...** (Now I live...)
*   **Я працюю...** (I work...)

Finally, share your future plans: 
*   **Я буду...** (I will...)
*   **Я хочу...** (I want...)

Try to use at least three verbs for each tense to build a complete text. This structured approach helps you build a complex story from simple parts.

<!-- INJECT_ACTIVITY: ordering-chronological -->
<!-- INJECT_ACTIVITY: fill-in-biography -->

## Summary

Here is the recap. The past tense uses gender endings for the speaker: **Я народився** or **Я народилася**. The present tense uses person endings, for example **Я живу** and **Я працюю**. The future tense uses **буду** + infinitive, for example **Я буду працювати**. Together, these forms build a clear life story.

**Наші плани**
Раніше ми жили в Америці. Там ми вчили англійську мову. Зараз ми живемо в Україні. Тут ми вчимо українську мову. Далі ми будемо вільно говорити.

> *Earlier we lived in America. There we studied the English language. Now we live in Ukraine. Here we study the Ukrainian language. Next we will speak fluently.*

Do not forget the crucial signal words that guide the narrative timeline. These anchors help your listener understand exactly when an event happened. Use **раніше** (before/earlier) to signal the past tense. Use **зараз** (now) to mark the present tense. Finally, use **далі** (further/next) to introduce your future plans.

Let's quickly recap your core biographical vocabulary. Your foundation includes the verbs **народитися** (to be born), **жити** (to live), **вчитися** (to study), **переїхати** (to move), and **подорожувати** (to travel). When discussing your career, remind yourself to use the instrumental case for professions. For example, you should say **Я працюю програмістом** (I work as a programmer) or **Я працюю вчителькою** (I work as a teacher). Achieving **успіх** (success, m) in storytelling is all about using these blocks correctly. Mastering these verbs will give you the confidence to speak about your life in any situation. You can discuss your early life or your time at the **університет** (university, m).

Self-check: Write your own life story in eight to ten sentences using all three tenses. Ensure you include where you were born, where you live now, and your future plans.
</generated_module_content>

**PIPELINE NOTE — Word count: 2058 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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
| 6 | **Engagement & tone** | 10% | The writer's persona is an encouraging teacher — natural teacher phrasing like "Let us look at..." or "Have you noticed..." is FINE and should NOT be penalized. DEDUCT ONLY for: self-congratulatory openers ("Welcome to A2! Congratulations on completing..."), gamified/corporate language ("You have unlocked...", "You now possess...", "Your journey begins..."), empty filler that adds words but zero information ("This is a very important concept that you will use frequently in your daily life"), generic enthusiasm not specific to Ukrainian ("incredibly beautiful language", "wonderfully consistent system"). REWARD for: teacher warmth with substance, specific cultural details, humor, concrete Ukrainian examples, natural classroom energy. |
| 7 | **Structural integrity** | 5% | DEDUCT for: missing H2 headings from plan, duplicate summary sections, meta-commentary sections ("Content notes:"), word count BELOW 1200 (more content is always welcome — never penalize for exceeding the target), dangling/incomplete sentences, stray tags or formatting artifacts. REWARD for: clean markdown, all sections present and ordered correctly, word count at or above target. |
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
- The `find` string MUST be an EXACT copy-paste from the module content. DO NOT change quotes (« » to " "), dashes (— to -), or spacing. If you change a single character in the `find` string, the automated replacement will fail.
- Keep fixes minimal — change only what's wrong, preserve surrounding text. Provide enough context (e.g. 5-7 words) to make the match unique.
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

Verified: 158 words | Not found: 10 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Америці — NOT IN VESUM
  ✗ Анна — NOT IN VESUM
  ✗ Анно — NOT IN VESUM
  ✗ Девід — NOT IN VESUM
  ✗ Канаді — NOT IN VESUM
  ✗ Лондоні — NOT IN VESUM
  ✗ Львові — NOT IN VESUM
  ✗ Одесі — NOT IN VESUM
  ✗ Торонто — NOT IN VESUM
  ✗ Японію — NOT IN VESUM

All 158 other words are confirmed to exist in VESUM.

</vesum_verification>

---

## Verification Tools (Shell Commands)

You have access to verification tools via shell commands. Use these to verify
Ukrainian vocabulary, check grammar, and search textbook content **as you write**.

**IMPORTANT:** Run verification commands BEFORE finalizing any Ukrainian text.
Batch multiple verifications together to minimize round-trips.

### 1. Batch-verify Ukrainian words exist in VESUM (preferred — one call for many words)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from rag.query import verify_words
results = verify_words(['слово1', 'слово2', 'слово3'])
for w, matches in results.items():
    if matches:
        print(f'{w}: FOUND — lemma={matches[0][\"lemma\"]}, pos={matches[0][\"pos\"]}')
    else:
        print(f'{w}: NOT FOUND — may not exist in standard Ukrainian')
"
```

### 2. Verify a single Ukrainian word in VESUM (with full morphological tags)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from rag.query import verify_word
results = verify_word('WORD_HERE')
if results:
    for m in results:
        print(f'lemma={m[\"lemma\"]}, pos={m[\"pos\"]}, tags={m[\"tags\"]}')
else:
    print('NOT FOUND in VESUM')
"
```

### 3. Get all inflected forms of a lemma (declension/conjugation)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from rag.query import verify_lemma
forms = verify_lemma('LEMMA_HERE')
for f in forms[:20]:
    print(f'{f[\"word_form\"]:20s} {f[\"pos\"]:8s} {f[\"tags\"]}')
print(f'... {len(forms)} forms total')
"
```

### 4. Check CEFR level of a word (is it level-appropriate?)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import query_cefr_level
results = query_cefr_level('WORD_HERE')
for r in results:
    print(f'{r[\"word\"]}: {r[\"level\"]} ({r[\"pos\"]})')
if not results:
    print('Not in CEFR database')
"
```

### 5. Search textbook content (Ukrainian school textbooks, Grades 1-11)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_textbooks
keywords = {'keyword1', 'keyword2'}
results = search_textbooks(keywords, 5)
for r in results:
    title = r.get('section_title', r.get('title', ''))
    grade = r.get('grade', '?')
    text = r.get('text', '')[:200]
    print(f'Grade {grade} | {title}')
    print(f'  {text}')
    print()
"
```

### 6. Search style guide for calques/Russianisms (Антоненко-Давидович, 279 entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_style_guide
results = search_style_guide('TOPIC_HERE', 3)
for r in results:
    print(f'--- {r.get(\"word\", \"\")} [{r.get(\"section\", \"\")}]')
    print(r.get('text', '')[:300])
    print()
if not results:
    print('No style guide entries found')
"
```

### 7. Look up word definition in СУМ-11 (Ukrainian explanatory dictionary, 127K entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_definitions
results = search_definitions('WORD_HERE', 3)
for r in results:
    print(f'{r.get(\"word\", \"\")}: {str(r.get(\"definition\", r.get(\"text\", \"\")))[:200]}')
"
```

### 8. Search idioms (Фразеологічний словник, 25K entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_idioms
results = search_idioms('WORD_HERE', 5)
for r in results:
    print(f'{r.get(\"word\", \"\")}: {str(r.get(\"text\", r.get(\"definition\", \"\")))[:200]}')
"
```

### 9. English-to-Ukrainian translation (Балла, 79K entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import translate_en_uk
results = translate_en_uk('ENGLISH_WORD', 5)
for r in results:
    print(f'{r.get(\"word\", \"\")}: {str(r.get(\"definition\", r.get(\"text\", \"\")))[:200]}')
"
```

---

**WHEN to use these tools:**

1. **Before writing any Ukrainian text** — batch-verify all key vocabulary with
   `verify_words` (tool 1). Any word that returns NOT FOUND must be replaced.
2. **When you suspect a Russicism or calque** — search the style guide (tool 6)
   and verify the correct Ukrainian form with `verify_word` (tool 2).
3. **When writing for A1/A2** — check CEFR levels (tool 4) to ensure vocabulary
   is level-appropriate.
4. **When unsure about a case ending or conjugation** — use `verify_lemma` (tool 3)
   to see the full paradigm.
5. **When covering a grammar topic** — search textbooks (tool 5) to see how
   Ukrainian school textbooks teach it.
6. **When you need the precise Ukrainian meaning** — use СУМ-11 (tool 7).
7. **When looking for natural Ukrainian expressions** — search idioms (tool 8).

**Batching rule:** Collect all words you want to verify, then run ONE `verify_words`
call instead of multiple `verify_word` calls. This is faster and uses fewer tokens.
