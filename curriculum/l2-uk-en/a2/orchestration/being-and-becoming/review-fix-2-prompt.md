# Phase D.2: Targeted Repair

> **You are an expert Ukrainian language editor applying targeted fixes based on a review.**
> The review already applied some fixes. You handle what's still failing.
> You have **Edit** and **Grep** tools — fix files directly.

---

## Editing Principles

- **IMPROVE, don't destroy.** Every rewrite should teach MORE than the original, not less.
- **PRESERVE the author's intent.** If a paragraph explains something poorly, rewrite it to explain it well — don't delete it.
- **MATCH the surrounding voice.** Your rewrite should read like the original author wrote it on a better day.
- Only DELETE truly empty sentences (pure cheerleading with zero information that cannot be salvaged). This should be rare.

---

## Fix Plan (from Phase D.1 review)

## Plan Adherence Issues (Deterministic — MUST FIX)

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥12 items
  - Actual: Activity has 8 items
  - Fix: Add 4 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥12 items
  - Actual: Activity has 8 items
  - Fix: Add 4 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥12 items
  - Actual: Activity has 8 items
  - Fix: Add 4 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥12 items
  - Actual: Activity has 8 items
  - Fix: Add 4 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥12 items
  - Actual: Activity has 8 items
  - Fix: Add 4 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥12 items
  - Actual: Activity has 8 items
  - Fix: Add 4 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:quiz`
  - Expected: Plan requires ≥10 items
  - Actual: Activity has 8 items
  - Fix: Add 2 more items to 'quiz' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:match-up`
  - Expected: Plan requires ≥10 items
  - Actual: Activity has 8 items
  - Fix: Add 2 more items to 'match-up' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:match-up`
  - Expected: Plan requires ≥10 items
  - Actual: Activity has 8 items
  - Fix: Add 2 more items to 'match-up' activity


---

## Critical Issues Found

### Issue 1: Vocabulary Inconsistency — айтівець vs айтішник (Plan Deviation + Internal Inconsistency)
- **Location**: Lines 109-122 vs Line 195 / Section "Соціокультурний контекст: Фемінітиви та IT" and "Діалоги та кар'єрні плани"
- **Original**: Content introduces 「**айтівець** (IT guy) or **айтівка** (IT girl)」 on line 109 and uses this form consistently (lines 111-115, 121-122), but line 195 switches to 「Я хочу стати айтішником」
- **Problem**: (1) The plan specifies `айтішник / айтішниця`, not `айтівець / айтівка`. Both are valid VESUM words, but the plan is the source of truth. (2) The module is internally inconsistent — it teaches `айтівець` but then uses `айтішник` in dialogue. This is confusing for A2 learners who will wonder if these are the same word.
- **Fix**: Standardize to `айтішник / айтішниця` per plan throughout, or if `айтівець` is preferred, update plan and teach both forms explicitly with a note that they're synonyms. At minimum, fix the inconsistency — pick one.

### Issue 2: Misleading Instrumental Case Explanation
- **Location**: Line 85 / Section "Презентація: Дієслова та відмінювання"
- **Original**: 「Він працює лікарем literally means "He works by means of a doctor," which is how Ukrainian expresses "He works as a doctor."」
- **Problem**: The predicative instrumental (характеристика особи) is NOT the instrumental of means (знаряддя дії). Saying "by means of a doctor" is a false etymology that will confuse learners when they encounter the actual instrumental of means (e.g., `писати ручкою` — write with a pen). The learner might incorrectly generalize that all instrumental = "by means of."
- **Fix**: Replace with: "The instrumental case here signals the role or capacity in which someone works — literally answering 'as what?' rather than 'by what means?'"

### Issue 3: Missing Plan Points in Section "Діалоги та кар'єрні плани"
- **Location**: Section "Діалоги та кар'єрні плани" (lines 168-231)
- **Problem**: The plan specifies three elements missing from this section: (1) `став тестувальником` — no тестувальник appears anywhere; (2) `був офіціантом` as a past-role example — no офіціант appears; (3) a synthesis activity where learners describe their own path — no such prompt exists.
- **Fix**: Add a dialogue that includes a career-change narrative using `тестувальник` and `офіціант` (e.g., "I used to work as a waiter, then became a tester"). Add a synthesis prompt at the end: "Now describe your own path: What were you? What are you now? What do you want to become?"

### Issue 4: Richness Gaps — Missing Tables and Cultural Callouts
- **Location**: Module-wide
- **Problem**: Richness at 82% (target 95%). Gaps: engagement 3/5, cultural 1/3, tables 0/2. Only one `[!culture]` callout (line 121). No comparison tables despite the module being about nominative↔instrumental transformations — a natural fit for tabular presentation.
- **Fix**: (1) Add a comparison table showing Nominative → Instrumental for all taught professions (both genders). (2) Add a `[!did-you-know]` callout about the question word `ким` being the instrumental of `хто`. (3) Add a `[!culture]` callout about the State Standard citizenship example's resonance for learners.

### Issue 5: Factual Concern — "2020" Feminitives Reform Date
- **Location**: Line 99 / Section "Соціокультурний контекст: Фемінітиви та IT"
- **Original**: 「In 2020, Ukraine officially updated its national grammar rules to explicitly include and standardize *feminitives*」
- **Problem**: The major Ukrainian orthography reform (Український правопис) was adopted by the Cabinet of Ministers on May 22, 2019, not 2020. The 2019 reform is what standardized feminitives. The date "2020" may be inaccurate.
- **Fix**: Verify the exact date and change to "In 2019" if referring to the Правопис reform. If a separate 2020 update exists, specify which document.

---

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 85 | 「literally means "He works by means of a doctor"」 | "signals the role or capacity — answering 'as what?'" | Misleading explanation |
| 109/195 | Mixed `айтівець` and `айтішник` | Standardize to one form (plan says `айтішник`) | Inconsistency |

---

## Fix Plan to Reach 9/10 (REQUIRED — score is 8.2)

### Language: 8/10 → 9/10
**What to fix:**
1. Line 85: Replace "literally means 'He works by means of a doctor'" with a correct explanation of predicative instrumental
2. Standardize айтівець/айтішник throughout — either switch all to `айтішник` per plan, or explicitly teach both as synonyms

**Expected score after fix:** 9/10

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Add a brief "Today you'll learn to..." preview after the opening quote block (after line 12)
2. Replace the quiz-style ending (lines 238-245) with a warm "You can now..." celebration + preview of next module

**Expected score after fix:** 9/10

### Pedagogy: 8/10 → 9/10
**What to fix:**
1. Add a Nominative → Instrumental comparison table after line 82 (covers richness table gap too)
2. Add the missing synthesis activity in section "Діалоги та кар'єрні плани"
3. Add `тестувальник` and `офіціант` per plan

**Expected score after fix:** 9/10

### Activities: 8/10 → 9/10
**What to fix:**
1. Increase fill-in items in activities 1 and 2 to meet plan's 12+ target
2. Increase quiz items in activity 3 to meet plan's 10+ target

**Expected score after fix:** 9/10

### Beginner Safety: 8/10 → 9/10
**What to fix:**
1. Add learning preview at start
2. Add warm closing with encouragement and progress celebration

**Expected score after fix:** 9/10

### LLM Fingerprint: 8/10 → 9/10
**What to fix:**
1. Line 236: Replace 「the profound importance」 with simpler phrasing like "why it matters to use"

**Expected score after fix:** 9/10

### Projected Overall After Fixes
(9×1.5 + 9×1.1 + 9×1.2 + 9×1.3 + 9×1.3 + 9×1.0 + 9×1.5) / 8.9 = (13.5+9.9+10.8+11.7+11.7+9.0+13.5) / 8.9 = 80.1 / 8.9 = **9.0/10**

---

## Audit Failures (from automated re-audit)

```
Практика та запобігання помилкам (Practice and Error Prevention)                           457 /  400  ✅ (+57)
📚 IMMERSION TOO LOW (44.1% vs 45-65% target)
--- STRICT GATES (Level A2) ---
Immersion    ❌ 44.1% LOW (target 45-65% (A2.1))
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a2/audit/being-and-becoming-audit.log for details)
⚠️  RAG verification found unverified words (see audit report)
--- VESUM WORD VERIFICATION FAILURES ---
These words were NOT found in the VESUM morphological dictionary.
Check if they are valid Ukrainian forms. Fix misspellings or Russianisms.
  ❌ `Анна` (source: prose)
  ❌ `Антон` (source: prose)
  ❌ `ею` (source: prose)
  ❌ `Марія` (source: prose)
  ❌ `Олег` (source: prose)
  ❌ `Олена` (source: prose)
  ❌ `ою` (source: prose)
  ❌ `Петро` (source: prose)
  ❌ `Іван` (source: prose)
  ❌ `Ірина` (source: prose)
```

---

## File Contents (for reference)

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/being-and-becoming.md`

```markdown
<!-- SCOPE
Covers: Professions and Instrumental Case with verbs бути, стати, працювати
Not covered:
  - Spatial Prepositions → a2-07
-->

# Being and Becoming

> **Чому це важливо?**
>
> Talking about what we do, what we did, and what we want to become is a core part of human connection. Whether you are at a job interview, catching up with an old friend, or dreaming about the future, you need to describe your role in society. In Ukrainian, changing your role or talking about your profession requires the instrumental case.

**Today you'll learn to:** describe professions using the instrumental case, talk about past and future roles with **бути**, **стати**, and **працювати**, use modern feminitives, and discuss career aspirations in natural conversation.

## Вступ

When we talk about who we are right now in a permanent sense, we use the nominative case (the dictionary form). This is your identity. You are simply stating a fact about your existence. But when we talk about what we *want to become*, what we *used to be*, or what we *work as*, we are talking about a role, a function, or a phase in life. In Ukrainian grammar, roles, functions, and temporary states always use the **орудний відмінок** (instrumental case). 

Let's look closely at the difference. If you say **Я лікар** (I am a doctor), you are talking about your present identity. There is no verb "to be" used in the present tense, and the noun is in the nominative case. However, if you are studying at a medical university and want to express a future goal, you cannot just use the dictionary form. You are talking about a transition, a goal, a state that you will step into. 

Learners often fall into the Nominative Trap. Because English says "He wants to be a doctor," English speakers naturally try to translate this word for word and say ~~Він хоче бути лікар~~. This is entirely incorrect in standard Ukrainian. After verbs like **бути** (to be) and **стати** (to become), Ukrainian firmly requires the instrumental case. The correct sentence is **Він хоче бути лікарем**.

Here is how the pattern works in practice:
- **Я студент.** — I am a student. (present identity, nominative case)
- **Я хочу бути студентом.** — I want to be a student. (future role, instrumental case)
- **Вона вчителька.** — She is a teacher. (present identity, nominative case)
- **Вона хоче стати вчителькою.** — She wants to become a teacher. (change of state, instrumental case)
- **Він програміст.** — He is a programmer. (present identity, nominative case)
- **Він буде програмістом.** — He will be a programmer. (future role, instrumental case)

Understanding this philosophical difference between identity and function is the key to mastering the instrumental case for professions.

> **(Читання / Reading Practice)**
>
> Мій брат зараз студент. Він вивчає медицину в університеті. Він дуже хоче бути лікарем. Його подруга Олена вже закінчила університет. Минулого року вона змогла стати лікаркою. Зараз вона працює лікаркою в Києві.
>
> *(My brother is a student right now. He studies medicine at the university. He really wants to be a doctor. His friend Olena already finished university. Last year she was able to become a doctor. Now she works as a doctor in Kyiv.)*

> **(Самостійне читання / Independent Reading)**
>
> Кожна людина має свою історію. Хто ми зараз і ким ми хочемо стати — це важливе питання. Сьогодні я студентка. Я вивчаю різні предмети, читаю багато книжок і готуюся до іспитів. Але в майбутньому я хочу стати лікаркою. Я розумію, що це складна професія. Мені потрібно багато вчитися і багато працювати. Мій брат також має велику мрію. Він хоче стати програмістом і працювати у великій компанії. Наші батьки підтримують нас. Вони завжди кажуть, що ми повинні наполегливо працювати. Моя мама зараз працює вчителькою, а батько працює інженером. Раніше вони теж були просто студентами, як і ми.

> **(Коротка розмова / Short conversation)**
> — Привіт! Ким ти мрієш стати?
> — Привіт! Я мрію стати відомим інженером і будувати великі будинки. А ти?
> — А я хочу стати хорошою юристкою. Моя мама також працює юристкою.
> — Це чудово! Я знаю, що ми станемо професіоналами. Успіхів тобі у навчанні!
> — Дякую! Тобі також успіхів! Ми обов'язково досягнемо своїх цілей.

## Презентація: Дієслова та відмінювання

Certain verbs trigger the instrumental case when discussing professions. The most common is the verb **бути** (to be) when it is used in the past or future tense. Remember that in the present tense, we usually drop the verb "to be" entirely and use the nominative case. But in the past and future, we must use **був / була / було / були** and **буду / будеш / буде / будемо / будете / будуть** followed by the instrumental case.

- **Він був студентом.** — He was a student.
- **Вони були вчительками.** — They were teachers.
- **Я буду лікарем.** — I will be a doctor.
- **Ми будемо інженерами.** — We will be engineers.
- **Вони були економістами.** — They were economists.

The next important verbs are **стати** (to become, perfective aspect) and **ставати** (to be becoming, imperfective aspect). Use these verbs to describe a definitive change of state or a process of transformation.
- **Він хоче стати інженером.** — He wants to become an engineer.
- **Вона мріє стати програмісткою.** — She dreams of becoming a programmer.
- **Я хочу ставати кращим.** — I want to become (be becoming) better.
- **Мій друг став спеціалістом.** — My friend became a specialist.
- **Вони стали директорками.** — They became directors.

Finally, we use the verb **працювати** (to work) to describe our current professional roles. A very common and stubborn mistake among English speakers is using the English structure "work as" by adding the word **як** (like / as). You must never say ~~Вона працює як менеджер~~. Instead, just use the verb **працювати** directly with the instrumental case. The instrumental case itself carries the meaning of "as a...".
- **Він працює менеджером.** — He works as a manager.
- **Вона працює юристкою.** — She works as a lawyer.
- **Я працюю програмістом.** — I work as a programmer.
- **Ти працюєш журналістом.** — You work as a journalist.
- **Ми працюємо інженерами.** — We work as engineers.

Let's review the primary vocabulary forms for professions and see how their endings change in the instrumental case:
- **лікар** → **лікарем** (doctor, masculine)
- **лікарка** → **лікаркою** (doctor, feminine)
- **вчитель** → **вчителем** (teacher, masculine)
- **вчителька** → **вчителькою** (teacher, feminine)
- **інженер** → **інженером** (engineer, masculine)
- **інженерка** → **інженеркою** (engineer, feminine)
- **програміст** → **програмістом** (programmer, masculine)
- **програмістка** → **програмісткою** (programmer, feminine)
- **журналіст** → **журналістом** (journalist, masculine)
- **журналістка** → **журналісткою** (journalist, feminine)

| Nominative (хто?) | Instrumental masculine (ким?) | Instrumental feminine (ким?) |
|---|---|---|
| лікар / лікарка | лікар**ем** | лікарк**ою** |
| вчитель / вчителька | вчител**ем** | вчительк**ою** |
| інженер / інженерка | інженер**ом** | інженерк**ою** |
| програміст / програмістка | програміст**ом** | програмістк**ою** |
| журналіст / журналістка | журналіст**ом** | журналістк**ою** |
| менеджер / менеджерка | менеджер**ом** | менеджерк**ою** |

> [!did-you-know] **Ким? — The Instrumental of Хто**
> The question word **ким** is simply the instrumental case of **хто** (who). So **Ким ти працюєш?** literally asks "By whom do you work?" — meaning "What do you work as?" This is the standard way to ask about someone's profession.

> [!tip] **The "Як" Calque**
> Remember: **працювати** + instrumental case. Do not use **як**. In **Він працює лікарем**, the instrumental case signals the role or capacity — answering "as what?" (**ким?**), not "by what means?" This is how Ukrainian expresses "He works as a doctor."

> **(Читання / Reading Practice)**
>
> Раніше Іван був студентом. Тепер він працює менеджером у великій компанії. Його сестра Анна працює юристкою. Вона дуже любить свою роботу. Їхній спільний друг Марко мріє стати програмістом. Він хоче працювати програмістом.
>
> *(Previously Ivan was a student. Now he works as a manager in a big company. His sister Anna works as a lawyer. She loves her job very much. Their mutual friend Marko dreams of becoming a programmer. He wants to work as a programmer.)*

> **(Самостійне читання / Independent Reading)**
>
> Ми всі студенти. Ми вивчаємо іноземні мови в університеті. Після університету ми будемо спеціалістами. Я мрію стати відомим журналістом і багато подорожувати. Мій найкращий друг хоче стати інженером. Він дуже розумний і багато вчиться. Наша подруга Марія вже працює менеджеркою. Вона почала працювати менеджеркою минулого року. Раніше вона була просто студенткою. Ми завжди підтримуємо одне одного. Наші викладачі кажуть, що ми всі станемо хорошими професіоналами. Вони також колись були студентами, а тепер працюють викладачами. Це дуже цікаво — бачити, як люди змінюються.

## Соціокультурний контекст: Фемінітиви та IT

In 2019, Ukraine officially updated its national grammar rules to explicitly include and standardize *feminitives* (feminine forms of professions). While older texts or more conservative speakers might still use masculine forms for everyone (for example, calling a female director a «директор»), modern standard Ukrainian actively and proudly uses feminine endings for women's professions. This reform reflects modern Ukrainian societal shifts toward gender equality and visibility. 

You should consistently use both forms depending on the gender of the person you are talking about. This is a marker of educated, contemporary speech:
- **Він директор.** ↔ **Вона директорка.** (director)
- **Він менеджер.** ↔ **Вона менеджерка.** (manager)
- **Він юрист.** ↔ **Вона юристка.** (lawyer)
- **Він економіст.** ↔ **Вона економістка.** (economist)
- **Він спеціаліст.** ↔ **Вона спеціалістка.** (specialist)
- **Він журналіст.** ↔ **Вона журналістка.** (journalist)

Beyond grammar, it is essential to understand the professional landscape. Ukraine is one of Europe's largest IT hubs. Working in the tech sector is highly prestigious and desirable. While the formal, academic term for a programmer is **програмувальник**, almost everyone uses the word **програміст** (masculine) or **програмістка** (feminine). Even more common in everyday modern speech is the colloquial term **айтішник** (IT guy) or **айтішниця** (IT girl). You may also hear the synonyms **айтівець** / **айтівка** — both pairs mean exactly the same thing. These colloquial terms are used everywhere, from casual chats to news articles.

- **Він став айтішником.** — He became an IT professional.
- **Вона працює айтішницею.** — She works as an IT professional.
- **Мій брат хоче стати програмістом.** — My brother wants to become a programmer.
- **Моя сестра працює програмісткою.** — My sister works as a programmer.
- **Вони працюють айтішниками.** — They work as IT professionals.

Another extremely important word is **громадянин** (citizen) and its feminine form **громадянка**. Many people studying Ukrainian might relate to the following example, which is actually taken directly from the official Ukrainian State Standard for language proficiency:
- **Вона мріє стати громадянкою України.** — She dreams of becoming a citizen of Ukraine.
- **Він став громадянином України.** — He became a citizen of Ukraine.

> [!culture] **Громадянин / Громадянка**
> For many Ukrainian language learners, the sentence **Вона мріє стати громадянкою України** is more than a grammar exercise — it reflects a real aspiration. This example comes directly from the State Standard (*Державний стандарт*) for Ukrainian language proficiency, recognizing that citizenship is a meaningful life goal for many learners.

> [!culture] **Айтішники**
> The word **айтішник** is so incredibly common that it's practically a cultural phenomenon in modern Ukraine. Young Ukrainians often joke that every second person «хоче стати айтішником.» It represents a modern, successful lifestyle.

> **(Читання / Reading Practice)**
>
> Київ — дуже велике місто. Тут працює багато спеціалістів. Моя подруга Марія — дуже талановита економістка. А її чоловік працює айтішником. Вони хороші професіонали. Марія хоче стати директоркою у великому банку. Її чоловік працює програмістом.
>
> *(Kyiv is a very big city. Many specialists work here. My friend Mariia is a very talented economist. And her husband works as an IT professional. They are good professionals. Mariia wants to become a director in a big bank. Her husband works as a programmer.)*

> **(Самостійне читання / Independent Reading)**
> 
> Сучасний світ швидко змінюється. Сьогодні в Україні багато людей хочуть працювати у сфері технологій. Студенти вчать математику та програмування. Вони мріють стати айтішниками. Це дуже цікава і сучасна професія. Але ми також потребуємо розумних економістів, хороших лікарів і талановитих вчителів. Жінки в Україні сьогодні активно працюють у всіх сферах. Вони стають директорками, менеджерками, програмістками. Це показує, що суспільство розвивається. Важливо пам'ятати: не має значення, ким ви працюєте. Має значення те, як добре ви робите свою роботу.

## Практика та запобігання помилкам

<!-- adapted from: Kravtsova, Grade 4, вправа 125 -->
Now we will practice the transformation from present identity (nominative case) to past or future roles (instrumental case). Pay close attention to the endings. Masculine nouns usually take **-ом** or **-ем**, while feminine nouns take **-ою** or **-ею**. Notice how the role completely changes the ending of the word.

- **Він лікар.** → **Він був лікарем.** (He is a doctor. → He was a doctor.)
- **Вона лікарка.** → **Вона буде лікаркою.** (She is a doctor. → She will be a doctor.)
- **Я вчитель.** → **Я працюю вчителем.** (I am a teacher. → I work as a teacher.)
- **Вона вчителька.** → **Вона працювала вчителькою.** (She is a teacher. → She worked as a teacher.)
- **Він інженер.** → **Він працює інженером.** (He is an engineer. → He works as an engineer.)
- **Вона директорка.** → **Вона працює директоркою.** (She is a director. → She works as a director.)

It is absolutely critical to match the gender of the person with the profession. English uses the word "doctor" for both men and women, but Ukrainian uses **лікар** for a man and **лікарка** for a woman. Failing to match the gender is a very common beginner mistake. Let's look at incorrect sentences and their correct versions:
- ~~Вона хороший лікар.~~ → **Вона хороша лікарка.** (She is a good doctor.)
- ~~Він працює вчителькою.~~ → **Він працює вчителем.** (He works as a teacher.)
- ~~Анна хоче стати менеджером.~~ → **Анна хоче стати менеджеркою.** (Anna wants to become a manager.)
- ~~Олег буде економісткою.~~ → **Олег буде економістом.** (Oleh will be an economist.)

> [!warning] **Nominative vs. Instrumental Trap**
> Remember this fundamental rule: present identity is nominative, while a role or function is instrumental.
> **Він інженер.** (identity, nominative)
> **Він хоче стати інженером.** (role/function, instrumental)
> **Він працює інженером.** (current role, instrumental)

> **(Читання / Reading Practice)**
>
> У дитинстві Петро мріяв стати журналістом. Він дуже любив читати. Але зараз він працює юристом. Його колега Ірина також працює юристкою. Раніше вона працювала журналісткою, але змінила професію. Вони працюють дуже добре.
>
> *(In childhood, Petro dreamed of becoming a journalist. He loved reading very much. But now he works as a lawyer. His colleague Iryna also works as a lawyer. Previously she worked as a journalist, but changed her profession. They work very well.)*

> **(Самостійне читання / Independent Reading)**
>
> Моя родина дуже велика, і всі мають різні професії. Мій дідусь раніше був лікарем. Він багато працював у лікарні. Моя бабуся працювала вчителькою у школі. Вона дуже любила дітей. Мій батько зараз працює інженером. Він будує великі мости. Моя мама — успішна директорка. Вона багато працює з документами. Мій старший брат хоче стати програмістом. Він уже вивчає комп'ютери. А моя сестра мріє стати журналісткою, тому що вона любить писати цікаві історії. Я ще студент, але в майбутньому хочу працювати менеджером у великій компанії. Ми всі розуміємо, що кожна професія важлива. Головне — багато працювати і любити свою роботу. Тоді кожен може стати справжнім професіоналом.

## Діалоги та кар'єрні плани

Let's look at how people discuss professions and career history in natural, everyday conversations. "What do you do?" or "Who do you work as?" are very common questions when meeting someone new. The question word **ким** (who, the instrumental form of **хто**) is heavily used here.

> **(Знайомство / Meeting someone new)**
> — Привіт! Мене звати Антон. А тебе?
> — Привіт! Я Олена. Дуже приємно. Ти тут працюєш?
> — Ні, я ще студент. Але я мрію стати юристом. А ким ти працюєш?
> — Я вже працюю юристкою у цій компанії.
> — О, це чудово! Я хочу бути таким хорошим спеціалістом, як ти.
> — Дякую! Тобі треба багато вчитися, і ти станеш найкращим юристом.

Notice how people ask and answer professionally. 

<!-- adapted from: Kravtsova, Grade 4, вправа 159 -->
> **(В офісі / In the office)**
> — Добрий день! Ким ви працюєте?
> — Добрий день! Я працюю програмісткою. А ви?
> — А я працюю менеджером у цьому відділі.
> — Це дуже цікаво! Ви давно стали менеджером?
> — Ні, я став менеджером тільки минулого року. Раніше я був економістом.
> — Зрозуміло. Приємно познайомитися!

Here is a conversation between friends discussing future aspirations. Dreams and goals are a huge part of learning to talk about yourself.

> **(У кафе / In the cafe)**
> — Слухай, ким ти хочеш стати після університету?
> — Я хочу стати айтішником. Я вже вивчаю код. А ти?
> — Я мрію стати лікаркою. Це складно, але важливо.
> — Так, це чудова професія. Твій батько теж був лікарем, так?
> — Ні, він був інженером. Але моя мама працює лікаркою.

When describing your path, you combine these elements to tell a short story about your career. You describe what you used to be (**був / була**), what you do now (**працюю**), and what you want to become (**хочу стати**). This creates a full narrative of your professional life.

> **(На зустрічі випускників / At a reunion)**
> — Привіт! Як справи? Ким ти зараз працюєш?
> — Привіт! Я працюю економісткою. Раніше я була просто студенткою, а тепер я спеціалістка.
> — Клас! Ти багато вчилася. А я працюю журналістом. 
> — О, ти завжди хотів бути журналістом! Ти вже став дуже відомим журналістом?
> — Ще ні, але я багато працюю!

> **(Зміна професії / Career change)**
> — Ким ти зараз працюєш?
> — Я працюю тестувальником у великій компанії.
> — О, круто! А раніше ти теж працював у сфері технологій?
> — Ні, раніше я працював офіціантом у ресторані. Але потім я вирішив стати тестувальником.
> — Цікаво! Моя сестра теж була офіціанткою, а тепер стала програмісткою.
> — Так буває! Головне — не боятися змін.
>
> *(— What do you work as now? — I work as a tester at a big company. — Oh, cool! Did you also work in tech before? — No, I used to work as a waiter in a restaurant. But then I decided to become a tester. — Interesting! My sister was also a waitress, and now she became a programmer. — That happens! The main thing is not to be afraid of change.)*

Now it's your turn. Think about your own path and describe it using the patterns you've learned: **What were you? What are you now? What do you want to become?** For example: *Раніше я був студентом. Зараз я працюю менеджером. Я хочу стати директором.*

> [!tip] **Ким? (By whom / As what?)**
> When asking about professions, use **Ким ти працюєш?** (Who do you work as?) and **Ким ти хочеш стати?** (Who do you want to become?). This is the standard polite way to inquire about careers.

> **(Читання / Reading Practice)**
>
> Я хочу стати хорошим спеціалістом. Зараз я працюю айтішником. Раніше я був економістом. Моя подруга мріє стати директоркою компанії. Зараз вона працює менеджеркою. Вона амбітна жінка.
>
> *(I want to become a good specialist. Now I work as an IT professional. Previously I was an economist. My friend dreams of becoming a director of a company. Now she works as a manager. She is an ambitious woman.)*

> **(Співбесіда / Job Interview)**
> — Добрий день! Розкажіть про себе.
> — Добрий день! Мене звати Анна. Раніше я була просто студенткою. Я вивчала економіку в університеті. Після університету я почала працювати менеджеркою.
> — Де ви працюєте зараз?
> — Зараз я працюю менеджеркою у банку. Але я мрію стати директоркою.
> — Чудово! Ми шукаємо таких амбітних людей. Ви хочете працювати директоркою у нашому відділі?
> — Так, звичайно. Я стану хорошою директоркою.

> **(Розмова про колег / Talk about colleagues)**
> — Хто ця жінка? Вона нова співробітниця?
> — Так, це Марія. Вона працює айтішницею. 
> — О, я думав, що вона працювала економісткою. 
> — Ні, вона завжди працювала айтішницею. Вона дуже хороший спеціаліст. А той чоловік поруч — він працює програмістом. Вони разом працюють над новим проєктом.

---

# Підсумок

You can now talk about who you are, who you were, and who you want to become — all using the instrumental case. Here's what you've mastered:

- **Present identity** uses the nominative case: **Я лікар.**
- **Past, future, and professional roles** use the instrumental case with **бути**, **стати**, and **працювати**: **Я буду лікарем**, **Він став айтішником**, **Вона працює менеджеркою**.
- **Modern feminitives** like **директорка**, **лікарка**, and **програмістка** are standard in contemporary Ukrainian.
- **No "як" with працювати** — the instrumental case alone carries the meaning of "as a..."

In the next module, you'll build on this foundation as you learn to describe locations and directions using spatial prepositions.

---
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/activities/being-and-becoming.yaml`

```yaml
- type: fill-in
  title: "Transform to Past Tense Role"
  instruction: "Change the present identity into a past role. Watch the case endings!"
  items:
    - sentence: "Він лікар. → Він був ___."
      answer: "лікарем"
      options: ["лікарем", "лікаркою", "лікар", "лікарі"]
    - sentence: "Вона вчителька. → Вона була ___."
      answer: "вчителькою"
      options: ["вчителькою", "вчителем", "вчителька", "вчительки"]
    - sentence: "Я студент. → Я був ___."
      answer: "студентом"
      options: ["студентом", "студенткою", "студент", "студенти"]
    - sentence: "Я студентка. → Я була ___."
      answer: "студенткою"
      options: ["студенткою", "студентом", "студентка", "студентки"]
    - sentence: "Він інженер. → Він був ___."
      answer: "інженером"
      options: ["інженером", "інженеркою", "інженер", "інженери"]
    - sentence: "Вона економістка. → Вона була ___."
      answer: "економісткою"
      options: ["економісткою", "економістом", "економістка", "економістки"]
    - sentence: "Він спеціаліст. → Він був ___."
      answer: "спеціалістом"
      options: ["спеціалістом", "спеціалісткою", "спеціаліст", "спеціалісти"]
    - sentence: "Вона юристка. → Вона була ___."
      answer: "юристкою"
      options: ["юристкою", "юристом", "юристка", "юристки"]
    - sentence: "Він менеджер. → Він був ___."
      answer: "менеджером"
      options: ["менеджером", "менеджеркою", "менеджер", "менеджери"]
    - sentence: "Вона директорка. → Вона була ___."
      answer: "директоркою"
      options: ["директоркою", "директором", "директорка", "директорки"]
    - sentence: "Він журналіст. → Він був ___."
      answer: "журналістом"
      options: ["журналістом", "журналісткою", "журналіст", "журналісти"]
    - sentence: "Вона програмістка. → Вона була ___."
      answer: "програмісткою"
      options: ["програмісткою", "програмістом", "програмістка", "програмістки"]

- type: fill-in
  title: "Choose the Correct Verb Form"
  instruction: "Complete the sentence with the correct form of бути or стати."
  items:
    - sentence: "Він хоче ___ інженером."
      answer: "стати"
      options: ["стати", "став", "стала", "стаєш"]
    - sentence: "Вона мріє стати ___."
      answer: "програмісткою"
      options: ["програмісткою", "програмістом", "програмістка", "програмістки"]
    - sentence: "Я хочу ___ кращим."
      answer: "ставати"
      options: ["ставати", "стаєш", "стає", "стають"]
    - sentence: "Мій друг ___ спеціалістом."
      answer: "став"
      options: ["став", "стала", "стали", "стаю"]
    - sentence: "Вона ___ директоркою."
      answer: "стала"
      options: ["стала", "став", "стали", "стає"]
    - sentence: "Я ___ лікарем."
      answer: "буду"
      options: ["буду", "буде", "будемо", "будуть"]
    - sentence: "Ми ___ інженерами."
      answer: "будемо"
      options: ["будемо", "буду", "буде", "будуть"]
    - sentence: "Вони ___ економістами."
      answer: "були"
      options: ["були", "був", "була", "було"]
    - sentence: "Він ___ тестувальником."
      answer: "став"
      options: ["став", "стала", "стали", "стає"]
    - sentence: "Вона ___ офіціанткою."
      answer: "була"
      options: ["була", "був", "були", "було"]
    - sentence: "Ти ___ програмістом."
      answer: "будеш"
      options: ["будеш", "буду", "буде", "будуть"]
    - sentence: "Вони хочуть ___ айтішниками."
      answer: "стати"
      options: ["стати", "став", "стала", "стають"]

- type: quiz
  title: "Translate the Phrase"
  instruction: "Choose the correct Ukrainian translation."
  items:
    - question: "How do you say: 'He works as a manager'?"
      explanation: "Use працювати directly with the instrumental case. Do not use 'як'."
      options:
        - text: "Він працює менеджером."
          correct: true
        - text: "Він працює як менеджер."
          correct: false
        - text: "Він працює менеджер."
          correct: false
        - text: "Він працює менеджеркою."
          correct: false
    - question: "How do you say: 'She works as a lawyer'?"
      explanation: "Use the feminine feminitive in the instrumental case."
      options:
        - text: "Вона працює юристкою."
          correct: true
        - text: "Вона працює юристом."
          correct: false
        - text: "Вона працює як юристка."
          correct: false
        - text: "Вона працює юристка."
          correct: false
    - question: "How do you say: 'I work as a programmer (masculine)'?"
      explanation: "Use the masculine instrumental case without 'як'."
      options:
        - text: "Я працюю програмістом."
          correct: true
        - text: "Я працюю як програміст."
          correct: false
        - text: "Я працює програмістом."
          correct: false
        - text: "Я працюю програмісткою."
          correct: false
    - question: "How do you say: 'You work as a journalist (masculine)'?"
      explanation: "Use the masculine instrumental case without 'як'."
      options:
        - text: "Ти працюєш журналістом."
          correct: true
        - text: "Ти працюєш як журналіст."
          correct: false
        - text: "Ти працюєш журналісткою."
          correct: false
        - text: "Ти працює журналістом."
          correct: false
    - question: "How do you say: 'We work as engineers'?"
      explanation: "Use the plural instrumental case."
      options:
        - text: "Ми працюємо інженерами."
          correct: true
        - text: "Ми працюємо інженер."
          correct: false
        - text: "Ми працюєте інженерами."
          correct: false
        - text: "Ми працюємо як інженери."
          correct: false
    - question: "How do you say: 'He works as an IT professional'?"
      explanation: "Use the masculine instrumental case for the colloquial term."
      options:
        - text: "Він працює айтівцем."
          correct: true
        - text: "Він працює айтівкою."
          correct: false
        - text: "Він працює як айтівець."
          correct: false
        - text: "Він працюєш айтівцем."
          correct: false
    - question: "How do you say: 'She works as an IT professional'?"
      explanation: "Use the feminine instrumental case for the colloquial term."
      options:
        - text: "Вона працює айтівкою."
          correct: true
        - text: "Вона працює айтівцем."
          correct: false
        - text: "Вона працює як айтівка."
          correct: false
        - text: "Вона працюєш айтівкою."
          correct: false
    - question: "How do you say: 'He works as a doctor'?"
      explanation: "Use the masculine instrumental case without 'як'."
      options:
        - text: "Він працює лікарем."
          correct: true
        - text: "Він працює як лікар."
          correct: false
        - text: "Він працює лікаркою."
          correct: false
        - text: "Він працює лікарі."
          correct: false
    - question: "How do you say: 'He became a tester'?"
      explanation: "Use стати with the instrumental case."
      options:
        - text: "Він став тестувальником."
          correct: true
        - text: "Він став тестувальник."
          correct: false
        - text: "Він стала тестувальником."
          correct: false
        - text: "Він став як тестувальник."
          correct: false
    - question: "How do you say: 'She was a waitress'?"
      explanation: "Use була with the feminine instrumental case."
      options:
        - text: "Вона була офіціанткою."
          correct: true
        - text: "Вона була офіціантом."
          correct: false
        - text: "Вона була офіціантка."
          correct: false
        - text: "Вона був офіціанткою."
          correct: false

- type: match-up
  title: "Match Person to Profession Form"
  instruction: "Match the starting phrase with the grammatically correct profession ending."
  pairs:
    - left: "Вона працює (teacher)"
      right: "вчителькою"
    - left: "Він працює (teacher)"
      right: "вчителем"
    - left: "Вона буде (doctor)"
      right: "лікаркою"
    - left: "Він буде (doctor)"
      right: "лікарем"
    - left: "Вона стала (IT professional)"
      right: "айтівкою"
    - left: "Він став (IT professional)"
      right: "айтівцем"
    - left: "Вона була (manager)"
      right: "менеджеркою"
    - left: "Він був (manager)"
      right: "менеджером"
    - left: "Вона стала (tester)"
      right: "тестувальницею"
    - left: "Він був (waiter)"
      right: "офіціантом"

- type: fill-in
  title: "Complete the Career Aspiration"
  instruction: "Fill in the blanks with the correct verbs or nouns."
  items:
    - sentence: "Вона мріє стати ___ України."
      answer: "громадянкою"
      options: ["громадянкою", "громадянином", "громадянка", "громадяни"]
    - sentence: "Мій брат ___ стати програмістом."
      answer: "хоче"
      options: ["хоче", "хочу", "хочеш", "хочуть"]
    - sentence: "Моя сестра працює ___."
      answer: "програмісткою"
      options: ["програмісткою", "програмістом", "програмістка", "програмістки"]
    - sentence: "Вони працюють ___."
      answer: "айтівцями"
      options: ["айтівцями", "айтівцем", "айтівка", "айтівці"]
    - sentence: "Він став ___ України."
      answer: "громадянином"
      options: ["громадянином", "громадянкою", "громадянин", "громадяни"]
    - sentence: "Вона ___ стати директоркою."
      answer: "хоче"
      options: ["хоче", "хочу", "хочеш", "хочуть"]
    - sentence: "Він дуже хоче ___ лікарем."
      answer: "бути"
      options: ["бути", "буду", "буде", "будеш"]
    - sentence: "Я мрію ___ лікаркою."
      answer: "стати"
      options: ["стати", "став", "стала", "стають"]
    - sentence: "Раніше він працював ___."
      answer: "офіціантом"
      options: ["офіціантом", "офіціанткою", "офіціант", "офіціанти"]
    - sentence: "Вона стала ___."
      answer: "тестувальницею"
      options: ["тестувальницею", "тестувальником", "тестувальниця", "тестувальники"]
    - sentence: "Ми всі хочемо стати ___."
      answer: "спеціалістами"
      options: ["спеціалістами", "спеціалістом", "спеціалісти", "спеціаліст"]
    - sentence: "Він мріє ___ журналістом."
      answer: "стати"
      options: ["стати", "став", "стала", "стають"]

- type: true-false
  title: "Grammar Rules True or False"
  instruction: "Decide if the statement about Ukrainian grammar is correct."
  items:
    - statement: "You should use the word 'як' to say 'work as' (e.g., працювати як менеджер)."
      correct: false
      explanation: "Never use 'як' with працювати. Just use the instrumental case."
    - statement: "Present tense identity uses the nominative case."
      correct: true
      explanation: "Yes, 'Я лікар' uses the dictionary form (nominative)."
    - statement: "Past tense roles with 'бути' use the instrumental case."
      correct: true
      explanation: "Yes, 'Він був студентом' uses the instrumental case."
    - statement: "Вона працює лікаркою is the grammatically correct way to say 'She works as a doctor'."
      correct: true
      explanation: "It correctly uses 'працювати' with the feminine instrumental form."
    - statement: "The word 'програміст' is only used for women."
      correct: false
      explanation: "Програміст is masculine. The feminine form is програмістка."
    - statement: "Він хоче стати інженер is grammatically correct."
      correct: false
      explanation: "It must be 'інженером' because 'стати' requires the instrumental case."
    - statement: "The word 'директорка' is a modern feminitive form."
      correct: true
      explanation: "Yes, it is the officially recognized feminine form of директор."
    - statement: "The instrumental case answers the question 'ким?'."
      correct: true
      explanation: "Yes, 'Ким ти працюєш?' means 'Who do you work as?'"

- type: group-sort
  title: "Sort Professions by Gender"
  instruction: "Group the professions into masculine and feminine forms."
  groups:
    - name: "Masculine"
      items: ["лікар", "вчитель", "програміст", "айтівець"]
    - name: "Feminine"
      items: ["лікарка", "вчителька", "програмістка", "айтівка"]

- type: unjumble
  title: "Build the Sentence"
  instruction: "Put the words in the correct order to form a natural sentence."
  items:
    - words: ["Він", "хоче", "стати", "інженером"]
      answer: "Він хоче стати інженером"
    - words: ["Зараз", "вона", "працює", "успішною", "юристкою"]
      answer: "Зараз вона працює успішною юристкою"
    - words: ["Тепер", "я", "працюю", "програмістом", "у компанії"]
      answer: "Тепер я працюю програмістом у компанії"
    - words: ["Вона", "мріє", "стати", "програмісткою"]
      answer: "Вона мріє стати програмісткою"
    - words: ["Минулого", "року", "він", "був", "студентом"]
      answer: "Минулого року він був студентом"
    - words: ["Сьогодні", "ми", "разом", "працюємо", "інженерами"]
      answer: "Сьогодні ми разом працюємо інженерами"

- type: match-up
  title: "Nominative to Instrumental"
  instruction: "Match the dictionary form to its instrumental form."
  pairs:
    - left: "лікар"
      right: "лікарем"
    - left: "лікарка"
      right: "лікаркою"
    - left: "вчитель"
      right: "вчителем"
    - left: "вчителька"
      right: "вчителькою"
    - left: "інженер"
      right: "інженером"
    - left: "менеджерка"
      right: "менеджеркою"
    - left: "журналіст"
      right: "журналістом"
    - left: "програмістка"
      right: "програмісткою"
    - left: "офіціант"
      right: "офіціантом"
    - left: "тестувальник"
      right: "тестувальником"

- type: error-correction
  title: "Fix the Beginner Mistakes"
  instruction: "Find the grammatical error and choose the correct word to replace it."
  items:
    - sentence: "Він хоче бути лікар."
      error: "лікар"
      answer: "лікарем"
      options: ["лікарем", "лікарка", "лікарі", "лікаря"]
      explanation: "Use the instrumental case after 'бути'."
    - sentence: "Вона стала менеджер."
      error: "менеджер"
      answer: "менеджеркою"
      options: ["менеджеркою", "менеджера", "менеджери", "менеджеру"]
      explanation: "Use the feminine instrumental case."
    - sentence: "Вона хороший лікар."
      error: "лікар"
      answer: "лікарка"
      options: ["лікарка", "лікарем", "лікаркою", "лікарі"]
      explanation: "Match the gender for present identity."
    - sentence: "Ти працюєш директор."
      error: "директор"
      answer: "директором"
      options: ["директором", "директорка", "директори", "директору"]
      explanation: "Use the instrumental case with 'працюєш'."
    - sentence: "Він працює вчителькою."
      error: "вчителькою"
      answer: "вчителем"
      options: ["вчителем", "вчителька", "вчитель", "вчителі"]
      explanation: "Match the masculine gender."
    - sentence: "Він буде економісткою."
      error: "економісткою"
      answer: "економістом"
      options: ["економістом", "економіст", "економістці", "економістка"]
      explanation: "Match the masculine gender."
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/vocabulary/being-and-becoming.yaml`

```yaml
items:
  - lemma: "бути"
    translation: "to be"
    pos: "verb"
  - lemma: "стати"
    translation: "to become"
    pos: "verb"
  - lemma: "ставати"
    translation: "to be becoming"
    pos: "verb"
  - lemma: "працювати"
    translation: "to work"
    pos: "verb"
  - lemma: "лікар"
    translation: "doctor (masculine)"
    pos: "noun"
    gender: "m"
  - lemma: "лікарка"
    translation: "doctor (feminine)"
    pos: "noun"
    gender: "f"
  - lemma: "вчитель"
    translation: "teacher (masculine)"
    pos: "noun"
    gender: "m"
  - lemma: "вчителька"
    translation: "teacher (feminine)"
    pos: "noun"
    gender: "f"
  - lemma: "програміст"
    translation: "programmer (masculine)"
    pos: "noun"
    gender: "m"
  - lemma: "програмістка"
    translation: "programmer (feminine)"
    pos: "noun"
    gender: "f"
  - lemma: "програмувальник"
    translation: "programmer (formal)"
    pos: "noun"
    gender: "m"
  - lemma: "айтівець"
    translation: "IT professional (masculine)"
    pos: "noun"
    gender: "m"
  - lemma: "айтівка"
    translation: "IT professional (feminine)"
    pos: "noun"
    gender: "f"
  - lemma: "орудний"
    translation: "instrumental (case)"
    pos: "adj"
    gender: "m"
  - lemma: "відмінок"
    translation: "case (grammar)"
    pos: "noun"
    gender: "m"
  - lemma: "інженер"
    translation: "engineer (masculine)"
    pos: "noun"
    gender: "m"
  - lemma: "інженерка"
    translation: "engineer (feminine)"
    pos: "noun"
    gender: "f"
  - lemma: "журналіст"
    translation: "journalist (masculine)"
    pos: "noun"
    gender: "m"
  - lemma: "журналістка"
    translation: "journalist (feminine)"
    pos: "noun"
    gender: "f"
  - lemma: "юрист"
    translation: "lawyer (masculine)"
    pos: "noun"
    gender: "m"
  - lemma: "юристка"
    translation: "lawyer (feminine)"
    pos: "noun"
    gender: "f"
  - lemma: "економіст"
    translation: "economist (masculine)"
    pos: "noun"
    gender: "m"
  - lemma: "економістка"
    translation: "economist (feminine)"
    pos: "noun"
    gender: "f"
  - lemma: "менеджер"
    translation: "manager (masculine)"
    pos: "noun"
    gender: "m"
  - lemma: "менеджерка"
    translation: "manager (feminine)"
    pos: "noun"
    gender: "f"
  - lemma: "спеціаліст"
    translation: "specialist (masculine)"
    pos: "noun"
    gender: "m"
  - lemma: "спеціалістка"
    translation: "specialist (feminine)"
    pos: "noun"
    gender: "f"
  - lemma: "громадянин"
    translation: "citizen (masculine)"
    pos: "noun"
    gender: "m"
  - lemma: "громадянка"
    translation: "citizen (feminine)"
    pos: "noun"
    gender: "f"
  - lemma: "директор"
    translation: "director (masculine)"
    pos: "noun"
    gender: "m"
  - lemma: "директорка"
    translation: "director (feminine)"
    pos: "noun"
    gender: "f"
  - lemma: "айтішник"
    translation: "IT professional (masculine, colloquial)"
    pos: "noun"
    gender: "m"
  - lemma: "айтішниця"
    translation: "IT professional (feminine, colloquial)"
    pos: "noun"
    gender: "f"
  - lemma: "тестувальник"
    translation: "tester (masculine)"
    pos: "noun"
    gender: "m"
  - lemma: "тестувальниця"
    translation: "tester (feminine)"
    pos: "noun"
    gender: "f"
  - lemma: "офіціант"
    translation: "waiter (masculine)"
    pos: "noun"
    gender: "m"
  - lemma: "офіціантка"
    translation: "waitress (feminine)"
    pos: "noun"
    gender: "f"
```

---

## Instructions

1. For each issue in the Fix Plan or audit failures, use **Grep** to verify the exact text exists in the file
2. Use the **Edit** tool to fix each issue directly in the file
3. Only fix issues documented above — no silent extra changes
4. Prioritize: audit gate failures first, then review issues

---

## How to Fix

Use the Edit tool for each fix. The workflow for each issue:

1. **Grep** the file to confirm the text exists and is unique
2. **Edit** the file: provide `old_string` (exact text from file) and `new_string` (corrected text)
3. Move to next issue

File paths:
- Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/being-and-becoming.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/activities/being-and-becoming.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/vocabulary/being-and-becoming.yaml`

## Fix Rules

- Only fix issues documented in the Fix Plan or audit failures above
- You MAY add new activities or modify existing ones if the Fix Plan explicitly requests it
- Do NOT add new prose sections or vocabulary items unless the Fix Plan explicitly requests it
- Maximum **20 edits** total (prioritize the most impactful fixes)
- If nothing needs fixing, state that clearly

---

## Friction Report (MANDATORY)

After all fixes, output:

```
===FRICTION_START===
**Phase**: Phase D.2: Targeted Repair
**Step**: {what you were doing when friction occurred, or "Full Phase D.2"}
**Friction Type**: NONE | EDIT_FAILED | TEXT_NOT_FOUND | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===
```

---

## Boundaries

- Do NOT write a review — that was already done in Phase D.1
- Do NOT output ===REVIEW_START=== blocks
- Do NOT output FIND/REPLACE blocks — use the Edit tool instead
- You MAY add/modify activities if the Fix Plan requests it
- Do NOT make cosmetic changes beyond what the review flagged
