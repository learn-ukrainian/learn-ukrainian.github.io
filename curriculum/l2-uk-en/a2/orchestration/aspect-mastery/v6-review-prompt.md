<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 42: 30 найважливіших видових пар (A2, A2.6 [Aspect, Tenses, and Motion])
**Writer:** Gemini
**Word target:** 2000

## Plan (source of truth)

<plan_content>
module: a2-042
level: A2
sequence: 42
slug: aspect-mastery
version: '1.0'
title: 30 найважливіших видових пар
subtitle: Морфологія видових пар та вибір виду в контексті
focus: grammar
pedagogy: PPP
phase: A2.6 [Aspect, Tenses, and Motion]
word_target: 2000
objectives:
  - Learner can produce both members of 30 essential aspect pairs from memory, 
    organized by morphological pattern (prefix, suffix change, stem change, 
    suppletive).
  - Learner can identify the four main formation patterns for aspect pairs and 
    predict the perfective or imperfective partner of an unfamiliar verb using 
    these patterns.
  - Learner can choose the correct aspect in complex sentences involving 
    sequence, interruption, habitual action, and single result — beyond simple 
    signal words.
  - Learner can use aspect pairs fluently in short dialogues about daily plans, 
    completed tasks, and ongoing activities.
dialogue_situations:
  - setting: 'Parent and child doing homework — choosing the right aspect: Ти написав
      (pf) домашнє завдання? Ні, я ще пишу (impf). Прочитай (pf) цей абзац. Я читаю
      (impf) вже годину!'
    speakers:
      - Мама/Тато
      - Школяр (student)
    motivation: '30 aspect pairs in homework context: писати/написати, читати/прочитати'
content_outline:
  - section: Як утворюються видові пари (How Aspect Pairs Are Formed)
    words: 500
    points:
      - 'Pattern 1 — Prefixation (most common): писати → написати, читати → прочитати,
        робити → зробити, їсти → з''їсти, варити → зварити. The prefix adds completion
        without changing the base meaning.'
      - 'Pattern 2 — Suffix change: записувати → записати (-увати → -ати), розповідати
        → розповісти (-ідати → -істи), пояснювати → пояснити (-ювати → -ити). Imperfective
        suffixes are longer.'
      - 'Pattern 3 — Stem change: допомагати → допомогти, відповідати → відповісти.
        The stem itself transforms.'
      - 'Pattern 4 — Suppletive (different roots): брати → взяти, говорити → сказати,
        класти → покласти. These must be memorized as pairs.'
  - section: '30 пар: Список і приклади (30 Pairs: List and Examples)'
    words: 600
    points:
      - 'Group A — Daily actions (10 pairs): робити/зробити, писати/написати, читати/прочитати,
        готувати/приготувати, їсти/з''їсти, пити/випити, варити/зварити, мити/помити,
        прибирати/прибрати, прасувати/випрасувати.'
      - 'Group B — Communication & learning (10 pairs): говорити/сказати, питати/запитати,
        відповідати/відповісти, пояснювати/пояснити, вчити/вивчити, розуміти/зрозуміти,
        казати/сказати, розповідати/розповісти, записувати/записати, перекладати/перекласти.'
      - 'Group C — Movement & interaction (10 pairs): брати/взяти, давати/дати, класти/покласти,
        відкривати/відкрити, закривати/закрити, починати/почати, закінчувати/закінчити,
        допомагати/допомогти, купувати/купити, платити/заплатити.'
      - 'Each pair shown in a minimal contrast sentence: Я варив суп (was cooking)
        vs. Я зварив суп (cooked it, done).'
  - section: Вибір виду в складних ситуаціях (Aspect Choice in Complex 
      Situations)
    words: 500
    points:
      - 'Sequence of completed events — all perfective: Я встав, вмився, поснідав
        і пішов на роботу (I got up, washed, had breakfast, and left for work).'
      - 'Interruption — imperfective background + perfective event: Коли я готувала
        вечерю, подзвонила подруга (While I was cooking dinner, a friend called).'
      - 'Habitual vs. single — imperfective for habit, perfective for one-time: Вона
        завжди допомагала сусідам (She always helped the neighbors) vs. Вона допомогла
        сусідці вчора (She helped the neighbor yesterday).'
      - 'Negation nuance: Я не читав цю книгу (I haven''t read it / never read it)
        vs. Я не прочитав цю книгу (I didn''t finish reading it — started but didn''t
        complete).'
  - section: Практика у діалогах (Practice in Dialogues)
    words: 400
    points:
      - 'Dialogue 1: Що ти зробив сьогодні? — Listing completed tasks with perfective.
        А що ти робив увечері? — Describing an ongoing evening activity with imperfective.'
      - 'Dialogue 2: Planning and reporting. Що ти будеш робити завтра? (impf.) vs.
        Що ти зробиш до п''ятниці? (pf.) — aspect in future context too.'
      - 'Common conversational patterns with aspect: Ти вже зробив? (Have you done
        it yet?), Я ще роблю (I''m still doing it), Я тільки що зробив (I just did
        it).'
vocabulary_hints:
  required:
    - видова пара (aspect pair)
    - префікс (prefix)
    - суфікс (suffix)
    - брати / взяти (to take — impf./pf.)
    - давати / дати (to give — impf./pf.)
    - говорити / сказати (to say — impf./pf.)
    - класти / покласти (to put — impf./pf.)
    - починати / почати (to begin — impf./pf.)
    - закінчувати / закінчити (to finish — impf./pf.)
    - допомагати / допомогти (to help — impf./pf.)
  recommended:
    - утворення (formation)
    - морфологія (morphology)
    - тільки що (just now)
    - вже (already)
activity_hints:
  - type: match-up
    focus: Match imperfective verbs with their perfective partners from the 30 
      pairs
    items: 8
  - type: fill-in
    focus: Complete sentences by choosing the correct aspect based on context 
      (sequence, interruption, habit, single event)
    items: 8
  - type: group-sort
    focus: Sort aspect pairs by formation pattern (prefix, suffix, stem change, 
      suppletive)
    items: 8
  - type: quiz
    focus: Read a mini-situation and choose the correct aspect form with 
      justification
    items: 8
references:
  - title: Заболотний Grade 6, §52-54
    notes: Видові пари дієслів — formation patterns and usage
  - title: 'Ohoiko, 500+ Ukrainian Verbs (2024)'
    notes: Comprehensive aspect pair reference with conjugation tables

</plan_content>

## Generated Content

<generated_module_content>
## Як утворюються видові пари (~550 words)

In Ukrainian, aspect is part of verb **морфологія**. We create a **видова пара** (aspect pair) by changing the verb itself: the imperfective form shows process, habit, or repetition, while the perfective form highlights completion or a single result.

The most common way to form the perfective aspect is by adding a **префікс** (prefix) to the imperfective verb. Let us look at how this works in practice.

Це дуже популярний спосіб утворення. Ми кажемо «писати», коли дія триває. Але ми кажемо «написати», коли текст готовий. Інші пари працюють так само. Слово «читати» стає «прочитати». Слово «робити» стає «зробити». Також «їсти» стає «з'їсти», а «варити» стає «зварити». Перед літерами «к», «п», «т», «ф» та «х» ми використовуємо префікс «с-». Тому ми кажемо «сфотографувати», «сказати» та «спекти».

> *This pattern usually marks completion: писати → написати, читати → прочитати, робити → зробити.*

The second pattern works in reverse. We take a perfective verb and make it imperfective by changing or adding a **суфікс** (suffix). Imperfective suffixes are usually longer, reflecting the ongoing process. A great example is the pair **записувати / записати** (to write down — impf./pf.).

Ми часто додаємо суфікси «-ува-», «-а-» або «-я-». Наприклад, доконане дієслово «записати» стає «записувати». Слово «розповісти» стає «розповідати», а «пояснити» стає «пояснювати». Іноді змінюються не тільки суфікси, але й приголосні звуки в корені слова.

> *We often add the suffixes "-uva-", "-a-", or "-ya-". For example, the perfective verb "to have recorded" becomes "to record". The word "to have told" becomes "to tell", and "to have explained" becomes "to explain". Sometimes not only the suffixes change, but also the consonant sounds in the root of the word.*

Третій спосіб — це зміна основи або наголосу. Іноді корінь змінюється помітно. Наприклад, дієслово «відповідати» має форму доконаного виду «відповісти». В інших випадках змінюється тільки наголос. Слово «розрізати» може бути недоконаного або доконаного виду. Все залежить від наголосу.

> *The third method is a change of the stem or stress. Sometimes the root changes noticeably. For example, the verb "to answer" has the perfective form "to have answered". In other cases, only the stress changes. The word "to cut" can be of imperfective or perfective aspect. It all depends on the stress.*

:::info
**Grammar box** — Remember that adding a prefix usually creates a perfective verb, while adding a longer suffix usually creates an imperfective verb. These two patterns cover the vast majority of verbs you will encounter!
:::

Finally, the fourth pattern includes verbs that use different roots in the imperfective and perfective. These suppletive pairs must be memorized. The most crucial examples for daily communication are **брати / взяти** (to take — impf./pf.) and **казати / сказати** (to say — impf./pf.).

Ці слова виглядають по-різному. Ви не можете утворити їх за правилами. Якщо ви довго шукаєте ключі, ви кажете «шукати». Коли процес завершено, ви кажете «знайти». Те саме працює для дієслів «ловити» та «піймати». Їх треба вивчити напам'ять.

> *These words look different. You cannot form them by rules. If you look for keys for a long time, you say "to look for". When the process is finished, you say "to have found". The same works for the verbs "to catch" (process) and "to catch" (result). You need to learn them by heart.*

<!-- INJECT_ACTIVITY: group-sort-formation -->

## 30 пар: Список і приклади

Below are thirty high-frequency aspect pairs grouped by topic. Learn each verb together with its partner, not as an isolated word.

The first group covers everyday actions at home and in the kitchen. Most pairs here are prefix-based: the imperfective shows the process, and the perfective shows the finished result.

**робити / зробити** — *to do*
**писати / написати** — *to write*
**читати / прочитати** — *to read*
**готувати / приготувати** — *to cook, to prepare*
**їсти / з'їсти** — *to eat*
**пити / випити** — *to drink*
**варити / зварити** — *to boil, to cook*
**мити / помити** — *to wash*
**прибирати / прибрати** — *to clean, to tidy up*
**прасувати / випрасувати** — *to iron*

**Я варив суп.** — *I was cooking soup (process).*
**Я зварив суп.** — *I cooked the soup (result is ready).*

Учора я довго варив суп на обід. Нарешті я зварив його. Моя сестра прибирала кімнату цілий ранок. Коли вона прибрала кімнату, стало дуже чисто. Ми робимо всі домашні справи в суботу.

> *Yesterday I cooked soup for lunch for a long time. Finally I cooked it. My sister was cleaning the room all morning. When she finished cleaning the room, it became very clean. We do all the household chores on Saturday.*

The second group contains verbs related to communication, studying, and processing new information. In this category, you will see many pairs where the imperfective verb has a longer suffix, while the perfective partner is shorter. Pay close attention to the pair **казати / сказати** (to say — impf./pf.), which is a true aspect pair used constantly in everyday speech.

**казати / сказати** — *to say, to tell*
**питати / запитати** — *to ask*
**відповідати / відповісти** — *to answer*
**пояснювати / пояснити** — *to explain*
**вчити / вивчити** — *to learn, to study*
**розуміти / зрозуміти** — *to understand*
**казати / сказати** — *to tell, to say*
**розповідати / розповісти** — *to tell, to narrate*
**записувати / записати** — *to record, to write down*
**перекладати / перекласти** — *to translate*

**Вчитель довго пояснював правило.** — *The teacher was explaining the rule for a long time (process).*
**Нарешті він пояснив правило.** — *Finally he explained the rule (completed fact).*

Сьогодні на уроці ми вчили нові слова. Учитель довго пояснював граматику. Ми слухали, але не розуміли. Потім він пояснив усе ще раз і навів гарний приклад. Тоді кожен студент зрозумів цю тему. Усі швидко записали нові приклади в зошит.

> *Today in the lesson we were learning new words. The teacher was explaining the grammar for a long time. We listened, but did not understand. Then he explained everything one more time and gave a good example. Then every student understood this topic. Everyone quickly wrote down the new examples in the notebook.*

Group C deals with movement, physical interaction with objects, and the structure of activities. You will find verbs that define the temporal boundaries of an action, like **починати / почати** (to begin — impf./pf.) and **закінчувати / закінчити** (to finish — impf./pf.). Another crucial verb in this category is **допомагати / допомогти** (to help — impf./pf.).

This group also includes highly irregular pairs that you simply must memorize, such as **брати / взяти** (to take — impf./pf.) and **давати / дати** (to give — impf./pf.). You must also pay attention to verbs with stem changes, like **класти / покласти** (to put — impf./pf.). 

**брати / взяти** — *to take*
**давати / дати** — *to give*
**класти / покласти** — *to put*
**відкривати / відкрити** — *to open*
**закривати / закрити** — *to close*
**починати / почати** — *to begin*
**закінчувати / закінчити** — *to finish*
**допомагати / допомогти** — *to help*
**купувати / купити** — *to buy*
**платити / заплатити** — *to pay*

:::tip
**Did you know?** — The suppletive pairs **брати / взяти** and **давати / дати** are completely irregular because they evolved from very old, distinct roots. They are used in countless idioms and everyday phrases.
:::

**Я брав книгу.** — *I was taking the book (process).*
**Я взяв книгу.** — *I took the book (completed fact).*

Кожного ранку я відкриваю магазин. Учора було свято, тому я закрив його рано. Мій брат часто просить мене допомогти з математикою. Я радий, коли можу допомогти йому закінчити завдання. Ми кладемо зошити на стіл і починаємо працювати.

> *Every morning I open the store. Yesterday was a holiday, so I closed it early. My brother often asks me to help with math. I am glad when I can help him finish the task. We put the notebooks on the table and begin to work.*

<!-- INJECT_ACTIVITY: match-up-pairs -->

## Вибір виду в складних ситуаціях (~550 words)

Now let us see how aspect works in real context. The four key situations below show when Ukrainian chooses process and when it chooses result.

The first scenario is a sequence of completed events. When you are telling a story or describing a chronological chain of actions, you must use perfective verbs for every single step. One action finishes completely, and only then does the next one begin. This creates a fast-paced narrative where the plot moves forward step by step. You might use verbs like **починати / почати** (to begin — impf./pf.) or **закінчувати / закінчити** (to finish — impf./pf.) to frame these steps. If you use an imperfective verb here, it sounds like the actions were happening at the same time, which breaks the sequence.

Учора вранці мій брат дуже швидко зібрався. Він встав, вмився, поснідав і пішов на роботу. Він зробив усе це за двадцять хвилин і нічого не забув.

> *Yesterday morning my brother got ready very quickly. He got up, washed, had breakfast, and left for work. He did all this in twenty minutes and did not forget anything.*

The second scenario is interruption: a long background action is imperfective, and the sudden interrupting event is perfective. Verbs of speech, such as **казати / сказати** (to say — impf./pf.), often appear in this contrast.

Увечері я була вдома і спокійно відпочивала. Коли я готувала вечерю, раптом подзвонила подруга. Ми говорили дуже довго, тому моя вечеря згоріла.

> *In the evening I was at home and resting calmly. While I was cooking dinner, a friend suddenly called. We talked for a very long time, so my dinner burned.*

:::info
**Grammar box** — Think of the imperfective verb as the stage setting, and the perfective verb as the main event that suddenly happens on that stage. The word «коли» (when/while) often connects these two contrasting actions.
:::

The third scenario contrasts habit with a single result: repeated actions take the imperfective, while one specific achievement takes the perfective. This is clear with **допомагати / допомогти** (to help — impf./pf.) and **давати / дати** (to give — impf./pf.).

Моя сестра дуже добра людина. Вона завжди допомагала сусідам, коли мала вільний час. Але вона допомогла сусідці вчора ввечері, тому що та була дуже хвора.

> *My sister is a very kind person. She always helped the neighbors when she had free time. But she helped the neighbor yesterday evening because she was very sick.*

The final scenario is negation. With the imperfective, «не» usually means the action did not happen at all or is true in general; with the perfective, it often means the speaker did not reach the result.

Я взагалі не читав цю книгу, тому не знаю її сюжету. Мій друг купив її минулого тижня. Я почав читати, але я не прочитав цю книгу до кінця, бо вона нудна.

> *I have not read this book at all, so I do not know its plot. My friend bought it last week. I started reading, but I did not finish reading this book because it is boring.*

<!-- INJECT_ACTIVITY: fill-in-context -->

## Практика у діалогах (~440 words)

In conversation, speakers switch aspect depending on whether they ask about a process or check a result. Watch the contrast between **брати / взяти**, **давати / дати**, **казати / сказати**, **класти / покласти**, **починати / почати**, **закінчувати / закінчити**, and **допомагати / допомогти** in the dialogues below.

> — **Мама:** Ти вже написав домашнє завдання? *(Have you already written your homework?)*
> — **Школяр:** Ні, я ще пишу. *(No, I am still writing.)*
> — **Мама:** Прочитай цей абзац. *(Read this paragraph.)*
> — **Школяр:** Я читаю вже годину! *(I have been reading for an hour already!)*

The parent asks about the result, while the student emphasizes the unfinished process.

Другий діалог показує різницю між переліком результатів та звичайним вечірнім відпочинком. Запитання про те, що людина зробила сьогодні, вимагає чіткого переліку повністю виконаних завдань. Натомість запитання про вечірні справи фокусується на тривалому, розслабленому процесі, який не обов'язково має фінальний результат.

> *The second dialogue shows the difference between a list of results and normal evening relaxation. A question about what a person has done today requires a clear list of fully completed tasks. Instead, a question about evening activities focuses on a long, relaxed process that does not necessarily have a final result.*

> — **Олена:** Що ти зробив сьогодні? *(What did you get done today?)*
> — **Андрій:** Я написав звіт, купив хліб і поклав гроші в банк. *(I wrote a report, bought bread, and put money in the bank.)*
> — **Олена:** А що ти робив увечері? *(And what were you doing in the evening?)*
> — **Андрій:** Я дивився фільм і готував вечерю. *(I was watching a movie and cooking dinner.)*

Нарешті, зверніть увагу на майбутній час: недоконаний вид описує запланований процес, а доконаний — очікуваний результат.

> *In the future, the imperfective describes the planned process, while the perfective highlights the expected result.*

> — **Керівник:** Що ти будеш робити завтра? *(What will you be doing tomorrow?)*
> — **Співробітник:** Я буду писати звіт. *(I will be writing the report.)*
> — **Керівник:** Що ти зробиш до п'ятниці? *(What will you get done by Friday?)*
> — **Співробітник:** Я закінчу проект. *(I will finish the project.)*

:::info
**Grammar box** — The imperfective future uses the verb «бути» plus the infinitive, focusing on the process. The perfective future uses a single word, focusing on the final result.
:::

<!-- INJECT_ACTIVITY: quiz-read-a-mini-situation-and-choose-the-correct-aspect-form-with-justification -->
</generated_module_content>

**PIPELINE NOTE — Word count: 2100 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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
| 7 | **Structural integrity** | 5% | DEDUCT for: missing H2 headings from plan, duplicate summary sections, meta-commentary sections ("Content notes:"), word count BELOW 2000 (more content is always welcome — never penalize for exceeding the target), dangling/incomplete sentences, stray tags or formatting artifacts. REWARD for: clean markdown, all sections present and ordered correctly, word count at or above target. |
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

Verified: 357 words | Not found: 3 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Андрій — NOT IN VESUM
  ✗ Олена — NOT IN VESUM
  ✗ ува — NOT IN VESUM

All 357 other words are confirmed to exist in VESUM.

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
