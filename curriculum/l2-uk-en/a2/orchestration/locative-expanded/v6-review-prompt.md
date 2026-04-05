<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 20: Місцевий відмінок у нових контекстах (A2, A2.3 [Dative Case])
**Writer:** Gemini
**Word target:** 2000

## Plan (source of truth)

<plan_content>
module: a2-020
level: A2
sequence: 20
slug: locative-expanded
version: '1.0'
title: Місцевий відмінок у нових контекстах
subtitle: Абстрактні іменники, часові вирази та тема розмови у місцевому відмінку
focus: grammar
pedagogy: PPP
phase: A2.3 [Dative Case]
word_target: 2000
objectives:
  - Learner can use the locative case with abstract nouns to express contexts
    and domains (у житті, в освіті, на роботі, у політиці).
  - Learner can use temporal locative expressions for months, weeks, and
    periods (у минулому місяці, на цьому тижні, у дитинстві).
  - Learner can use topic-marking locative with по + locative for
    communication topics (по телефону, по радіо) and розмовляти/говорити
    про + accusative vs. по + locative distinctions.
  - Learner can combine locative with prepositions у/в, на, по in varied
    real-life contexts beyond simple physical location.
dialogue_situations:
  - setting: 'Two friends catching up after a long time — talking about life
      changes: Що нового у твоєму житті? — У минулому місяці я змінила роботу.
      Тепер працюю в освіті. А ти? — Я на новому курсі. Розмовляли по
      телефону з мамою — вона хвилюється.'
    speakers:
      - Марія
      - Ігор
    motivation: 'Natural catch-up triggers all three locative extensions:
      abstract (у житті, в освіті), temporal (у минулому місяці), topic
      (по телефону)'
  - setting: 'Student discussing schedule and interests with a tutor: На цьому
      тижні у мене три заняття. У вільний час я читаю про Україну — у
      підручнику з історії. В дитинстві я мало знав про українську культуру.'
    speakers:
      - Студент
      - Викладач
    motivation: 'Temporal locative (на цьому тижні, в дитинстві) + abstract
      domain (в історії, про культуру)'
content_outline:
  - section: 'Місцевий з абстрактними іменниками (Locative with Abstract Nouns)'
    words: 550
    points:
      - 'A1 taught locative for physical location (у місті, на вулиці). Now
        expanding to abstract domains and contexts.'
      - 'Common abstract locative phrases: у житті (in life), в освіті (in
        education), у політиці (in politics), на роботі (at work), в економіці
        (in economics), у мистецтві (in art).'
      - 'Pattern: у/в + abstract noun in locative = "in the domain/field of."
        Note: на роботі (not *у роботі) — на is fixed for робота.'
      - 'Practice forming locative of abstract feminine nouns in -а/-я:
        наука→у науці, політика→у політиці, культура→у культурі.'
  - section: 'Часовий місцевий відмінок (Temporal Locative)'
    words: 600
    points:
      - 'Months: у січні, у лютому, у березні... all months use у/в + locative.
        Masculine months in -ень: -ні (січень→у січні). Neuter місяць compounds:
        у минулому місяці, у наступному місяці.'
      - 'Weeks: на цьому тижні, на минулому тижні, на наступному тижні. Note:
        тиждень uses на (not у).'
      - 'Life periods: у дитинстві (in childhood), у молодості (in youth),
        у старості (in old age), у минулому (in the past), у майбутньому
        (in the future).'
      - 'Contrast with accusative for duration: у понеділок (on Monday, acc.)
        vs. у минулому місяці (last month, loc.). The question test: Коли?
        (temporal loc.) vs. Як довго? (duration, acc.).'
  - section: 'По телефону, по радіо: місцевий із прийменником «по» (Locative
      with "po")'
    words: 500
    points:
      - 'Topic/means with по + locative: по телефону (by phone), по радіо
        (on the radio), по пошті (by mail), по дорозі (on the way).'
      - 'Distinction: говорити по телефону (the medium of communication) vs.
        говорити про телефон (about the phone as a topic). По + locative =
        means/channel. Про + accusative = topic.'
      - 'Common phrases: Я подзвоню по телефону. Ми почули по радіо. Він
        надіслав по пошті. Зустрілися по дорозі додому.'
      - 'Note: по + locative is the traditional Ukrainian pattern. Some modern
        usage shifts to по + dative for distribution (по одному), but for
        communication means, locative is standard.'
  - section: 'Місцевий відмінок: від місця до сенсу (From Place to Meaning)'
    words: 350
    points:
      - 'Summary: locative is not just "where" — it answers де? (location),
        коли? (time), and як? (means/channel).'
      - 'Consolidation table: physical (у місті), abstract (у житті), temporal
        (у січні), means (по телефону) — all locative, four different functions.'
      - 'Practice: building sentences that use 2-3 locative functions together:
        У минулому місяці я розмовляв по телефону з другом у Києві.'
vocabulary_hints:
  required:
    - місцевий (locative (case))
    - абстрактний (abstract)
    - минулий (past, previous)
    - місяць (month)
    - тиждень (week)
    - телефон (phone, telephone)
    - подорож (journey, trip)
    - зустріч (meeting, encounter)
    - думка (thought, opinion)
    - проблема (problem)
  recommended:
    - дитинство (childhood)
    - молодість (youth)
    - майбутнє (future)
    - освіта (education)
    - мистецтво (art)
activity_hints:
  - type: quiz
    focus: 'Identify the function of locative in each sentence (physical
      location, abstract domain, temporal, or means)'
    items: 8
  - type: fill-in
    focus: Complete sentences with the correct locative form of the noun
      (у минулому ___, на цьому ___, по ___)
    items: 8
  - type: match-up
    focus: Match locative expressions with their English equivalents across
      all four function types
    items: 8
  - type: error-correction
    focus: 'Fix preposition errors (e.g., *у роботі → на роботі, *у
      телефону → по телефону, *на минулому місяці → у минулому місяці)'
    items: 8
references:
  - title: Заболотний Grade 5, §28-30
    notes: Місцевий відмінок іменників, прийменники
  - title: Заболотний Grade 6, §34-35
    notes: Часові конструкції з місцевим відмінком
  - title: 'ULP: Ukrainian Cases — Locative'
    url: https://www.ukrainianlessons.com/locative-case/
    notes: Locative case uses including temporal and abstract

</plan_content>

## Generated Content

<generated_module_content>
## Місцевий з абстрактними іменниками (Locative with Abstract Nouns)

«Читаємо українською»
— **Студент:** Де ти зараз? *(Where are you now?)*
— **Викладач:** Я у школі. *(I am at school.)*
— **Студент:** А де ти працюєш? *(And where do you work?)*
— **Викладач:** Я працюю в освіті. *(I work in education.)*
— **Студент:** Це дуже цікаво! Моя думка така: освіта — це майбутнє. *(This is very interesting! My opinion is this: education is the future.)*
— **Викладач:** Так, робота в освіті — це важливо. *(Yes, work in education is important.)*

You already know how to use the **місцевий відмінок** (locative case) to describe physical locations like «у кімнаті» (in the room) or «у місті» (in the city). In Ukrainian, the concept of "location" extends to abstract domains, fields of activity, and situations. When you are involved in a specific field, you are conceptually "located" inside it. An abstract noun (**абстрактний** іменник) uses the same locative endings as a physical place.

For feminine abstract nouns ending in **-а** or **-я**, the ending changes to **-і**. The preposition **у** or **в** (in) indicates immersion in this domain. 
*   **освіта** (education) → **в освіті** (in education)
*   **культура** (culture) → **у культурі** (in culture)
*   **політика** (politics) → **у політиці** (in politics)
*   **релігія** (religion) → **у релігії** (in religion)
*   **наука** (science) → **у науці** (in science)

«Читаємо українською»
Мій брат працює у політиці. *(My brother works in politics.)*
Він каже, що у політиці багато проблем. *(He says that there are many problems in politics.)*
Моя сестра працює у культурі. *(My sister works in culture.)*
Я дуже люблю працювати в освіті. *(I really love working in education.)*

Masculine and neuter abstract nouns typically take the **-і** ending (or sometimes **-я** depending on the stem). These words express immersion in an aspect of life rather than a physical spot. 

*   **бізнес** (business) → **у бізнесі** (in business)
*   **мистецтво** (art) → **у мистецтві** (in art)
*   **право** (law) → **у праві** (in law)
*   **життя** (life) → **у житті** (in life)
*   **спорт** (sport) → **у спорті** (in sport)

«Читаємо українською»
У житті бувають різні ситуації. *(There are different situations in life.)*
Мій друг працює у великому бізнесі. *(My friend works in big business.)*
Мистецтво дуже важливе для мене, я шукаю нові ідеї у мистецтві. *(Art is very important for me, I look for new ideas in art.)*

While you almost always use the preposition **у/в** to indicate being "inside" a field, the word **робота** (work) is a critical exception. When talking about work as an activity or status, you must use the preposition **на** (on/at). You say **на роботі** (at work), and never «у роботі». You sit **в офісі** (in the office — physical location), you work **у бізнесі** (in business — industry domain), but you are currently **на роботі** (at work — engaged in the activity). 

«Читаємо українською»
— **Марія:** Привіт, Ігоре! Ти де? *(Hi, Ihor! Where are you?)*
— **Ігор:** Привіт! Я зараз на роботі. *(Hi! I am at work now.)*
— **Марія:** Ти працюєш в офісі? *(Do you work in an office?)*
— **Ігор:** Так, я працюю в офісі. *(Yes, I work in an office.)*

<!-- INJECT_ACTIVITY: quiz, Identify the function of locative in each sentence (physical location, abstract domain, temporal, or means) -->

## Часовий місцевий відмінок (Temporal Locative)

«Читаємо українською»
Мій день народження у січні. *(My birthday is in January.)*
Ми завжди відпочиваємо у серпні. *(We always rest in August.)*
Що ви робите у травні? *(What are you doing in May?)*
У минулому місяці мій брат купив машину. *(In the previous month my brother bought a car.)*

Ukrainian calendar months function as temporal containers. To say something happens "in" a certain month, use the preposition **у** or **в** followed by the locative case. Most months are masculine nouns ending in the suffix **-ень**. When forming the locative for these months, the vowel **-е-** drops out, and the ending becomes **-ні**. The word **місяць** (month) also takes a standard locative ending.

* **січень** (January) → **у січні** (in January)
* **березень** (March) → **у березні** (in March)
* **травень** (May) → **у травні** (in May)
* **місяць** (month) → **у місяці** (in a month)

While months use the preposition **у/в**, the word **тиждень** (week) requires the preposition **на** (on/at). The vowel **-е-** also drops out, giving us the form **тижні**. You must memorize the essential temporal triad for talking about weeks using the words **минулий** (past, previous), **цей** (this), and **наступний** (next).

* **на цьому тижні** (this week)
* **на минулому тижні** (last week)
* **на наступному тижні** (next week)

«Читаємо українською»
Що ти робиш на цьому тижні? *(What are you doing this week?)*
На цьому тижні у мене багато роботи. *(This week I have a lot of work.)*
На минулому тижні ми були в театрі. *(Last week we were at the theater.)*
На наступному тижні вона їде до Києва. *(Next week she is going to Kyiv.)*

The locative case also describes broad periods of life or time as backgrounds for events, placing an event "inside" an era. 

* **дитинство** (childhood) → **у дитинстві** (in childhood)
* **молодість** (youth) → **у молодості** (in youth)
* **старість** (old age) → **у старості** (in old age)
* **минуле** (the past) → **у минулому** (in the past)
* **майбутнє** (the future) → **у майбутньому** (in the future)

«Читаємо українською»
У дитинстві я любив грати у футбол. *(In childhood I loved playing football.)*
Моя бабуся багато читала у молодості. *(My grandmother read a lot in youth.)*
У минулому це місто було маленьким. *(In the past this city was small.)*
У майбутньому я хочу працювати в освіті. *(In the future I want to work in education.)*

The locative case answers the question **Коли?** (When? — for months or weeks). To answer the question **Як довго?** (How long?), you must use the accusative case to show the duration of an action.

«Читаємо українською»
Я був там у червні. *(I was there in June.)* — Коли? (Locative)
Я був там увесь червень. *(I was there all June.)* — Як довго? (Accusative)
Вона відпочивала на минулому тижні. *(She rested last week.)* — Коли? (Locative)
Вона відпочивала цілий тиждень. *(She rested the whole week.)* — Як довго? (Accusative)

<!-- INJECT_ACTIVITY: fill-in, Complete sentences with the correct locative form of the noun (у минулому ___, на цьому ___, по ___), 8 items -->

## По телефону, по радіо: місцевий із прийменником «по» (Locative with "po")

«Читаємо українською»
Вони часто розмовляють по телефону. *(They often talk on the phone.)*
Мої батьки рідко дивляться новини по телевізору. *(My parents rarely watch the news on TV.)*
Ми почули дуже гарну пісню по радіо. *(We heard a very beautiful song on the radio.)*
Вона надіслала важливі документи по пошті. *(She sent important documents by mail.)*

When you want to express the means or channel of communication, use the preposition **по** (by, on) followed by the locative case. Masculine nouns in this specific context often take the **-у** ending in the locative case instead of the usual **-і**. 

* **телефон** (phone) → **по телефону** (by phone)
* **телевізор** (TV) → **по телевізору** (on TV)
* **радіо** (radio) → **по радіо** (on the radio)
* **пошта** (mail) → **по пошті** (by mail)

When you talk *about* something, use the preposition **про** (about) with the accusative case to mark the subject matter. When you talk *via* a specific communication channel, use **по** with the locative case. 

«Читаємо українською»
Я довго розмовляв про нову роботу по телефону. *(I talked about the new job on the phone for a long time.)*
Журналісти говорили про економіку по телевізору. *(Journalists talked about the economy on TV.)*

The preposition **по** with the locative case is also used in spatial expressions to describe movement *along* a path or being *within the process* of a journey or trip (**подорож**). A common phrase is **по дорозі** (on the way). This means the action happens while the journey is actively in progress, which is conceptually different from standing physically on the asphalt surface (**на дорозі**). 

«Читаємо українською»
Я купив свіжий хліб по дорозі додому. *(I bought fresh bread on the way home.)*
Обережно, велика машина стоїть прямо на дорозі. *(Careful, a big car is standing right on the road.)*
У нас була довга подорож. *(We had a long journey.)*
У подорожі ми багато говорили. *(On the journey we talked a lot.)*

Також зверніть увагу: по воді, по землі — рух уздовж поверхні. Прийменник «по» часто вказує на маршрут або простір. *(Also pay attention: along the water, along the ground — movement along a surface. The preposition «по» often indicates a route or space.)*

You will also frequently use the locative case when talking about a meeting (**зустріч**). It acts as a temporal and spatial event container.

* **зустріч** (meeting) → **на зустрічі** (at the meeting)

«Читаємо українською»
Ми говорили про це на зустрічі. *(We talked about this at the meeting.)*
На зустрічі було багато людей. *(There were many people at the meeting.)*

<!-- INJECT_ACTIVITY: match-up, Match locative expressions with their English equivalents across all four function types, 8 items -->

## Місцевий відмінок: від місця до сенсу (From Place to Meaning)

«Читаємо українською»
> — **Олена:** Де ти працюєш зараз? *(Where do you work now?)*
> — **Максим:** Я працюю в освіті, а мій брат — у політиці. *(I work in education, and my brother — in politics.)*
> — **Олена:** Коли ти був у Львові? *(When were you in Lviv?)*
> — **Максим:** Ми відпочивали там у минулому місяці. Це була чудова подорож. *(We vacationed there last month. It was a wonderful journey.)*
> — **Олена:** На цьому тижні я дуже зайнята на роботі. У мене важлива зустріч. *(This week I am very busy at work. I have an important meeting.)*
> — **Максим:** Як ти дізналася про це свято? *(How did you find out about this holiday?)*
> — **Олена:** Я почула ці цікаві новини по радіо. *(I heard these interesting news on the radio.)*
> — **Максим:** Тоді ми поговоримо про це по телефону ввечері. Моя думка — треба йти. *(Then we will talk about this on the phone in the evening. My opinion is — we should go.)*

The locative case sets the complete scene for your sentences. It answers three distinct questions:
1. **Де?** (Where?) covers physical locations, abstract spheres like life, work, or education, and events like a meeting (на зустрічі). 
2. **Коли?** (When?) specifies time periods such as specific months, weeks (на минулому тижні), and broad stages of life. 
3. **Як?** (How? / By what means?) explains the channel of your communication, like talking on the phone (по телефону). 

<!-- INJECT_ACTIVITY: error-correction, Fix preposition errors (e.g., *у роботі → на роботі, *у телефону → по телефону, *на минулому місяці → у минулому місяці), 8 items -->

### Підсумок (Summary)

> **Питання:** Який прийменник ми вживаємо для місяців? *(What preposition do we use for months?)*
> **Відповідь:** Прийменник **у** або **в** разом із місцевим відмінком. Наприклад: **у січні** *(in January)*, **у серпні** *(in August)*. *(The preposition "у" or "в" together with the locative case. For example: in January, in August.)*

> **Питання:** Як сказати "this week" українською? *(How to say "this week" in Ukrainian?)*
> **Відповідь:** **На цьому тижні**. Ми завжди використовуємо прийменник **на** для тижнів, а не "у" чи "в". *(On this week. We always use the preposition "на" for weeks, and not "у" or "в".)*

> **Питання:** Як ми позначаємо засіб зв'язку, наприклад, телефон або радіо? *(How do we indicate a means of communication, for example, a phone or radio?)*
> **Відповідь:** За допомогою прийменника **по** та місцевого відмінка. Ми кажемо **по телефону** *(on the phone)* або **по радіо** *(on the radio)*. *(With the help of the preposition "по" and the locative case. We say on the phone or on the radio.)*

> **Питання:** Яке закінчення мають абстрактні іменники жіночого роду, такі як "освіта" чи "політика"? *(What ending do abstract feminine nouns have, such as "education" or "politics"?)*
> **Відповідь:** Вони мають закінчення **-і** у місцевому відмінку. Наприклад: **в освіті** *(in education)*, **у політиці** *(in politics)*. *(They have the ending -і in the locative case. For example: in education, in politics.)*

**Deterministic word count: 2014 words** (calculated by pipeline, do NOT estimate manually)

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

Verified: 240 words | Not found: 6 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Ігоре — NOT IN VESUM
  ✗ Києва — NOT IN VESUM
  ✗ Львові — NOT IN VESUM
  ✗ Марія — NOT IN VESUM
  ✗ Олена — NOT IN VESUM
  ✗ ень — NOT IN VESUM

All 240 other words are confirmed to exist in VESUM.

</vesum_verification>

## Verification Tools (MCP)

You have MCP tools to VERIFY claims in the content. Use them to cite evidence:

**Core Verification:**
- `mcp__rag__verify_words` — batch-verify Ukrainian words against VESUM (409K lemmas)
- `mcp__rag__verify_lemma` — full declension/conjugation for a lemma
- `mcp__rag__search_style_guide` — **HIGH PRIORITY.** Check for calques/Russianisms (Антоненко-Давидович)
- `mcp__rag__query_r2u` — Russian→Ukrainian equivalents. Confirm Russicism alternatives.
- `mcp__rag__query_pravopys` — verify orthography rules (Правопис 2019)

**Content Quality:**
- `mcp__rag__query_cefr_level` — verify vocabulary is level-appropriate (PULS, 5.9K words)
- `mcp__rag__search_definitions` — exact Ukrainian definitions (СУМ-11, 127K entries)
- `mcp__rag__search_etymology` — historical forms, etymology (Грінченко, 67K entries)
- `mcp__rag__search_idioms` — verify idioms are authentic Ukrainian (25K entries)
- `mcp__rag__search_synonyms` — suggest better word choices (Ukrajinet, 122K synsets)
- `mcp__rag__query_grac` — check collocations and frequency in GRAC corpus (2B tokens)

**Reference:**
- `mcp__rag__search_text` — check how textbooks teach the topic (Grades 1-11)
- `mcp__rag__search_literary` — verify literary references against primary sources
- `mcp__rag__query_wikipedia` — fact-check historical/cultural claims

**Evidence standard:** A review that says "this might be a Russicism" is WEAK. A review that says "`search_style_guide` confirms 'приймати участь' is a calque — correct form: 'брати участь'" is STRONG. Cite tool results.
