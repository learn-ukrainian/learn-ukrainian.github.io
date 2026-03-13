        # Escalation Fix — validate

        You are an expert Ukrainian language editor. The previous agent could not fix
        these audit violations. Fix them precisely.

        ## Audit Errors

        ```
          > Match the Pairs: 8 items (min 8)
  > Complete the Sentence: 8 items (min 8)
  > Put the Words in Order: 6 items (min 6)
  > True or False?: 8 items (min 8)
  > Sort by Gender: 8 items (min 8)
  > Fix the Mistake: 6 items (min 6)
  > Complete the Sentence: 8 items (min 8)

📚 IMMERSION TOO LOW (24.0% vs 45-65% target)
   FIX: Convert simple explanations to Ukrainian
   FIX: Add more Ukrainian narratives/dialogues
   FIX: Use Ukrainian for engagement boxes (💡🎬🌍)

--- STRICT GATES (Level A2) ---
Persona      ✅ Persona Defined
Words        ✅ 2826/2000 (raw: 3162)
Activities   ✅ 10/10
Density      ✅ All > 8
Unique_types ✅ 7/4 types
Priority     ✅ Priority types used
Engagement   ✅ 4/4
Audio        ℹ️ No audio
Vocab        ✅ 30/1
Structure    ✅ Valid Structure
Lint         ✅ Clean Format
Pedagogy     ✅ Level-appropriate
Content_heavy ℹ️ N/A (standard module)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ℹ️ Quality validation N/A (A1/A2)
Research     ✅ Content aligned with research
Immersion    ❌ 24.0% LOW (target 45-65% (A2.1))

📝 RECOMMENDATION: UPDATE (patch fixes) (severity 40/100)
   → Revision recommended (severity 40/100)
   → Immersion 21% off target (major rebalancing needed)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/audit/being-and-becoming-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/status/being-and-becoming.json

❌ AUDIT FAILED. Correct errors before proceeding.

❌ AUDIT FAILED (see curriculum/l2-uk-en/a2/audit/being-and-becoming-audit.log for details)

Running RAG word verification...
Verifying: being-and-becoming.md
  VESUM misses: 5 — querying RAG...
[embed] Loading BGE-M3 from BAAI/bge-m3...

Fetching 30 files:   0%|          | 0/30 [00:00<?, ?it/s]
Fetching 30 files: 100%|██████████| 30/30 [00:00<00:00, 89877.94it/s]
[embed] BGE-M3 loaded.
You're using a XLMRobertaTokenizerFast tokenizer. Please note that with a fast tokenizer, using the `__call__` method is faster than using a method to encode the text followed by a call to the `pad` method to get a padded encoding.
  Words: 332 | VESUM: 327 (98.5%) | RAG: 3 | Not found: 2
  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/audit/being-and-becoming-rag-audit.md
⚠️  RAG verification found unverified words (see audit report)

VESUM: 327/332 (98%) verified
⚠️ VESUM not found (5): Вашуленко, Кравцова, ою, ІТ, ІТ-сфера
        ```

        ## Current Content of Affected Section(s)

          - section: Презентація: Дієслова та відмінювання — Presentation: Verbs and Governing
  - section: Соціокультурний контекст: Фемінітиви та ІТ
  - section: Практика та запобігання помилкам — Practice and Error Prevention
  - section: Діалоги та кар'єрні плани — Dialogues and Career Plans
  - section: Підсумок
---

<!-- SCOPE
Covers: Professions using instrumental case, verbs бути and стати with correct case government, describing past roles and future aspirations.
Not covered:
  - Spatial Prepositions → a2-07
-->

# Being and Becoming

> **Чому це важливо? — Why is this important?**
>
> Знати, хто ви є — knowing who you are — is important, but talking about ваші ролі (your roles), ваш минулий досвід (your past experiences), та ваші плани на майбутнє (and your future aspirations) is just as crucial for deep conversations. In Ukrainian, changing a single ending can shift a word from meaning your core, permanent identity to the professional job you currently perform (ваша теперішня робота). Let us learn how to express your entire career journey perfectly.

## Вступ

<!-- Source: Вашуленко (Grade 3), p. 152 -->

Наприклад — For example:
| Зараз — Now | У минулому — In the past | У майбутньому — In the future |
|---|---|---|
| Він **лікар**. (He is a doctor.) | Він був **лікарем**. (He was a doctor.) | Він хоче стати **лікарем**. (He wants to become a doctor.) |
| Вона **вчителька**. (She is a teacher.) | Вона була **вчителькою**. (She was a teacher.) | Вона буде **вчителькою**. (She will be a teacher.) |
| Я **студент**. (I am a student.) | Я був **студентом**. (I was a student.) | Я хочу бути **студентом**. (I want to be a student.) |
| Вона **менеджерка**. (She is a manager.) | Вона стала **менеджеркою**. (She became a manager.) | Вона буде **менеджеркою**. (She will be a manager.) |

В українській мові (In the Ukrainian language), те, як ми описуємо професії (the way we describe professions) and personal statuses depends heavily on the concept of time and change (час і зміни). Коли ми говоримо про професії — when we talk about professions right now, in the present moment, у теперішньому часі — in the present tense — ми використовуємо називний відмінок — we use the nominative case. Це словникова форма слова (This is the basic dictionary form of the word). You will notice that in the present tense (теперішній час), Ukrainian does not use a linking verb like the English words "is" or "am". Ви просто ставите підмет і професію разом — you simply place the subject and the profession together. This specific grammatical construction signals a permanent or current state of identity (постійний стан). It tells the listener that this is who the person fundamentally is at this exact moment in time.

Але коли ми говоримо про минуле — but when we talk about the past (минулий час), to the past (минулий час), the future (майбутній час), or a process of changing, the grammar shifts as well. When you discuss a professional role that someone occupied in the past or will occupy in the future, the noun must change its ending to the Instrumental case (орудний відмінок). The Instrumental case signals that the profession is a function (функція), a temporary role (тимчасова роль), or a status that is assumed over a period of time, rather than an unchangeable essence. 

Ця різниця — this difference — is essential for discussing career paths (кар'єра), aspirations, and work history naturally. If you simply use the dictionary form for past and future roles, it sounds highly unnatural and broken to a native Ukrainian speaker. The role is something you act as, a tool you use in society, not just something you simply are. Understanding this philosophical distinction makes mastering the grammar much easier.

> [!warning] The Nominative Trap
> One of the most frequent errors made by English speakers is translating sentences like "He wants to be a doctor" word-for-word. This results in the incorrect sentence: ~~Він хоче бути лікар.~~ In English, "a doctor" remains in the exact same form regardless of the verb. But in Ukrainian, because "to be" (бути) here describes taking on a professional role over time, you must apply the Instrumental case ending (закінчення орудного відмінка). Правильна форма — The correct form is: **Він хоче бути лікарем.** Завжди пам'ятайте — always remember — that verbs of being in the past and future demand this change. 

Understanding this distinction between a present identity and a functional role is your ultimate key to speaking naturally about jobs and professions (робота і професії). У наступному розділі — in the next section — we will explore the specific verbs (дієслова) that govern this rule and learn how to form these crucial endings correctly.

## Презентація: Дієслова та відмінювання

<!-- adapted from: Заболотний Grade 5, вправа 221 -->

Наприклад — For example:
- **бути** (to be) — **Я був лікарем.** (I was a doctor.)
- **стати** (to become) — **Вона хоче стати вчителькою.** (She wants to become a teacher.)
- **ставати** (to be becoming) — **Він стає кращим програмістом.** (He is becoming a better programmer.)
- **працювати** (to work) — **Ми працюємо інженерами.** (We work as engineers.)

Дієслово **бути** дуже часто зустрічається у повсякденному мовленні (The verb **бути** is incredibly common in everyday speech). While it is completely invisible in the present tense for professions, у минулому часі — in the past tense — та в майбутньому часі — and in the future tense — these forms are always visible and require the noun to be in the Instrumental case (орудний відмінок). When you say someone was a professional or will be a professional, you are inherently describing a temporary state (тимчасовий стан) or a role bound by time. 

Подивімося на закінчення — Let us look at the endings (закінчення) for these common professions in the Instrumental case. Ця таблиця показує — this table shows — both masculine and feminine forms (чоловічий і жіночий рід), which is vital for modern fluency.

Порівняйте — Compare:
| Називний — Nominative | Орудний — Instrumental | Переклад — Translation |
|---|---|---|
| лікар | лікарем | doctor (masculine) |
| лікарка | лікаркою | doctor (feminine) |
| вчитель | вчителем | teacher (masculine) |
| вчителька | вчителькою | teacher (feminine) |
| інженер | інженером | engineer (masculine) |
| інженерка | інженеркою | engineer (feminine) |
| програміст | програмістом | programmer (masculine) |
| програмістка | програмісткою | programmer (feminine) |
| журналіст | журналістом | journalist (masculine) |
| журналістка | журналісткою | journalist (feminine) |
| юрист | юристом | lawyer (masculine) |
| юристка | юристкою | lawyer (feminine) |

Зверніть увагу — Notice how чоловічі іменники (masculine nouns) usually take the ending **-ом** or **-ем**, while жіночі іменники (feminine nouns) consistently take the ending **-ою**. These specific endings are the absolute core of expressing professions correctly in Ukrainian. 

Ще одна пара дієслів — another verb pair is **стати** and **ставати**. Ці дієслова означають — these verbs mean "to become" or "to be becoming." The verb **стати** means the change of state is complete or is viewed as a specific, achieved future goal. The verb **ставати** emphasizes the ongoing, continuous process of changing into something else. Both of these verbs strongly demand the Instrumental case (орудний відмінок) because they inherently describe a shift into a completely new role or status. 

Наприклад — For example:
- **Мій брат став юристом.** (My brother became a lawyer.)
- **Його сестра хоче стати журналісткою.** (His sister wants to become a journalist.)

Нарешті, ми маємо дієслово **працювати** (Finally, we have the verb **працювати**). Це дієслово описує — this verb describes — your current, active employment (теперішня робота). When you state your profession using this verb, you are explicitly saying that you function in that role every day. Therefore, it also requires the Instrumental case to show that the job is a function you perform.

> [!caution] The «Як» Calque
> English speakers frequently say "I work as a manager." If you try to translate this directly, you might incorrectly say ~~Я працюю як менеджер.~~ This is a direct language calque and is completely grammatically incorrect in Ukrainian. The verb **працювати** directly takes the Instrumental case (орудний відмінок) without any prepositions or extra words. Правильно сказати — the correct way to say this is **Я працюю менеджером.** The Instrumental case ending itself carries the full meaning of "as a."

By mastering these three grammatical concepts—the past and future of **бути**, the change of state with **стати**, and the employment role with **працювати**—you will speak about careers with immense fluency and precision. The key is to constantly remind yourself that a job is a function you perform (це функція).

## Соціокультурний контекст: Фемінітиви та ІТ

<!-- adapted from: Кравцова Grade 3, сторінка 64 -->

> **(На зустрічі випускників / At a class reunion)**
> — Ким ти зараз працюєш?
> — Я працюю директоркою. А ти?
> — А я став айтівцем.
> — О, це дуже цікаво! Ти програміст?
> — Так, працюю програмістом.

Українська мова — це жива система, яка розвивається разом із суспільством (The Ukrainian language is a living system that evolves alongside its society). Дві важливі зміни — two important changes in modern Ukrainian culture are clearly reflected in how people talk about their professions today: the rapid rise of the technology sector (сфера ІТ) and the official, widespread recognition of feminine professional titles (фемінітиви).

In the year two thousand twenty, a major governmental spelling reform officially codified the use of femininitives. Historically, during the Soviet era, many high-level professions were only used in their masculine forms (чоловічі форми), even when referring directly to women. Today, however, the standard and respectful practice is to use the specific feminine form (жіноча форма) for female professionals. This linguistic update reflects modern Ukrainian societal shifts toward absolute gender equality (гендерна рівність) and professional visibility. 

Наприклад — for instance — the word for a director is no longer strictly masculine. 

Порівняйте — Compare:
- **Він працює директором.** (He works as a director.)
- **Вона працює директоркою.** (She works as a director.)
- **Він хороший менеджер.** (He is a good manager.)
- **Вона хороша менеджерка.** (She is a good manager.)

You will notice this pattern everywhere in modern media, business, and casual conversation. A female economist is an **економістка**, and a female specialist is a **спеціалістка**. Using these forms is a very strong marker of contemporary, highly educated Ukrainian speech (сучасна українська мова). Always strive to learn both the masculine and feminine forms (чоловічий і жіночий рід) of every new profession you encounter.

Також ІТ-сфера змінила — also the IT sector changed — the Ukrainian job market (ринок праці) and the aspirations of its youth (молодь). Ukraine is home to one of the largest and most skilled developer communities in all of Europe, and the IT sector holds immense cultural prestige. The formal, dictionary word for a programmer is **програміст** or sometimes the even more formal term **програмувальник**. However, the conversational reality on the streets of Kyiv or Lviv is slightly different.

> [!culture] The Rise of the «Айтівець»
> In modern conversational Ukrainian, the absolute most ubiquitous term for anyone working in the tech industry is **айтівець** (for a man) or **айтівка** (for a woman). This highly colloquial word is naturally formed from the English abbreviation "IT". It is so common and culturally significant that young Ukrainians often joke that every second person dreams of becoming an **айтівець**. 

Коли ви говорите з молоддю — when you speak with youth, these specific words will appear constantly in your conversations (у розмовах). Whether someone says they want to become a formal specialist or a trendy developer, the grammatical structure remains exactly the same. You will hear these modern, evolved titles paired with the verbs we just learned, always stepping gracefully into the Instrumental case (орудний відмінок) to describe their exciting career journeys.

## Практика та запобігання помилкам

<!-- Reference: Vashulenko 3rd Grade, page 110 -->

Тепер час застосувати ці правила на практиці (Now it is time to put these rules into practice). Хороший спосіб практики — a good way to practice — is to take a simple statement about present identity and transform it into a narrative sentence about a role in the past (минуле) or the future (майбутнє). This specific exercise forces you to actively apply the Instrumental case endings (закінчення орудного відмінка) in real-time.

**Трансформація — Transformation**
Наприклад — For example:
- Він **лікар**. → Він був **лікарем**.
- Вона **вчителька**. → Вона хоче стати **вчителькою**.
- Я **журналіст**. → Я буду **журналістом**.
- Ти **юрист**. → Ти став **юристом**.

Notice carefully how the core meaning shifts from a simple, static fact to a dynamic narrative about time, change, or ambition (час, зміни або амбіції). Ця практика — this practice — will help you deeply internalize the correct endings until they feel automatic. 

Інша важлива тема — another important topic is gender agreement (узгодження в роді). When you use adjectives (прикметники) to describe a professional, the adjective must perfectly match the gender of the noun. Because many English speakers are heavily used to gender-neutral professional titles in their native language, they frequently default to the masculine form (чоловічий рід) in Ukrainian, even when they are talking about a woman. 

> [!tip] Matching the Adjective
> Always ensure the adjective strictly agrees with the noun's gender (рід). Do not say ~~Вона хороший лікар.~~ Since the modern language reform, the absolute best practice is to use the feminitive noun paired with a feminine adjective: **Вона хороша лікарка.** 

Ось кілька прикладів — Here are some examples:
Порівняйте — Compare:
- **Він хороший спеціаліст.** (He is a good specialist.)
- **Вона хороша спеціалістка.** (She is a good specialist.)
- **Він новий директор.** (He is the new director.)
- **Вона нова директорка.** (She is the new director.)

Нарешті, ми повинні — finally, we must — practice avoiding direct translation. that sneak into our speech from English. As we discussed earlier in the lesson, the word "as" (як) simply does not translate directly when you are talking about employment (робота). You must trust the grammar of the Instrumental case (орудний відмінок) to do all the heavy lifting for you. Rewiring your brain to drop the word «як» takes deliberate effort.

Наприклад — For example:
- ~~Він працює як менеджер.~~ → **Він працює менеджером.** (He works as a manager.)
- ~~Я працюю як інженер.~~ → **Я працюю інженером.** (I work as an engineer.)
- ~~Вона працює як економістка.~~ → **Вона працює економісткою.** (She works as an economist.)

By focusing intensely on these three specific areas—transforming present facts into past roles, perfectly matching adjectives to modern femininitives, and entirely dropping the unnecessary translation of the word "as"—you will drastically reduce the most common errors that learners make. The rhythm of these correct sentences will soon feel completely natural to your ear, allowing you to discuss any complex career path (кар'єрний шлях) with absolute confidence.

## Діалоги та кар'єрні плани

<!-- Inspired by: Вашуленко Grade 3, pg. 153 -->

Подивімося — Let's see how these structures function in real life (повсякденне життя). When you meet someone new, discussing work history and future plans is a very standard, polite topic of conversation. 

> **(В офісі / In the office)**
> — Ким ви працюєте?
> — Я працюю менеджером. А ви?
> — Я працюю програмістом. Але раніше я був офіціантом.
> — Це дуже цікаво! Чому ви стали програмістом?
> — Тому що я люблю технології.

In this natural exchange, you can see the fluid, easy movement between теперішня робота (current employment) та минулі ролі (and past roles). The standard question "Ким ви працюєте?" specifically asks for the Instrumental case (орудний відмінок) in the response. The speaker naturally shifts from discussing his current high-tech role to his past profession without ever changing the underlying grammatical logic. 

Люди також часто обговорюють — people also frequently discuss — their long-term plans (довгострокові плани), and dreams for the future. Sometimes, these aspirations go far beyond just a job title and touch upon fundamental concepts of citizenship (громадянство), identity, and belonging. 

> **(В університеті / At the university)**
> — Ким ти хочеш стати після університету?
> — Я хочу стати хорошою юристкою.
> — Це чудова мета. Ти плануєш працювати тут?
> — Так, я мрію стати громадянкою України.

The phrase "мрію стати громадянкою України" is a profoundly beautiful example of how this grammar applies to personal, legal status. The verb **мріяти** (to dream) is very often paired with **стати** (to become), which then absolutely requires the Instrumental case for the specific status you wish to achieve. Whether you are dreaming of becoming a громадянин України (citizen of Ukraine), a renowned technical specialist, or a highly successful company director, the grammatical structure remains perfectly and elegantly consistent.

Наприклад — For example:
- **Він мріє стати економістом.** (He dreams of becoming an economist.)
- **Вона мріє стати громадянкою України.** (She dreams of becoming a citizen of Ukraine.)
- **Я мрію стати лікарем.** (I dream of becoming a doctor.)

Коли ви знаєте ці правила — when you know these rules, you gain a truly powerful tool for personal storytelling (особиста історія). You can accurately describe where you started, what you are actively doing right now, and exactly what you hope to achieve in the future (у майбутньому). You are no longer just stating static, isolated facts; you are describing a dynamic, moving journey of being and becoming. Спробуйте написати — try to write — your own professional narrative using these exact verbs and case endings (закінчення відмінків). Think about your past roles, your current employment, and your biggest future dreams (мрії). By practicing your own personal story, the vocabulary will stick in your memory much faster. Напишіть про вашу кар'єру — write about your career today, ensuring every role takes the correct Instrumental form.

---

# Підсумок

У цьому модулі ми вивчили дуже важливу тему. Тепер ви знаєте, як правильно говорити про свою професію в минулому, теперішньому та майбутньому часі. Ми також вивчили нові слова, такі як айтівець, менеджерка та інші. (In this module, we studied a very important topic. Now you know how to correctly talk about your profession in the past, present, and future tenses. We also learned new words, such as IT professional, manager, and others.)

In this comprehensive module, you learned exactly how to navigate the grammatical differences between stating a permanent identity and describing a temporary professional role. You practiced the crucial, foundational rule that verbs of being (бути), becoming (стати), and working (працювати) require the following noun to take the Instrumental case (орудний відмінок). You also explored the modern Ukrainian workplace in depth, including the widespread, standard use of femininitives (фемінітиви) and the highly popular cultural terminology of the booming IT sector (сфера ІТ). 

**Перевірте себе — Self-Check**
1. How do you correctly say "I work as a manager" without using a translation calque? (Я працюю менеджером.)
2. What specific case directly follows the verbs **бути** and **стати** when discussing jobs and roles? (The Instrumental case / Орудний відмінок.)
3. How do you correctly form the feminine version of the word **директор**? (Директорка.)
4. Which case do you use to state your profession in the present tense without a verb? (The Nominative case / Називний відмінок.)

        ## File Path

        `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/being-and-becoming.md`

        ## Instructions

        1. Fix ONLY the violations listed above
        2. For euphony (в/у, і/й): apply Ukrainian euphony rules strictly
        3. Do NOT add or remove content — only fix the specific violations
        4. Preserve all markdown formatting, headers, and structure

        ## Output Format (MANDATORY)

        Output ONLY the fixed section(s) between delimiters:

        ```
        ===SECTION_FIX_START===
        ## {section title}
        {fixed section content}
        ===SECTION_FIX_END===
        ```

        If multiple sections need fixing, output each in its own delimiter block.
        Do NOT output anything else — no explanations, no commentary.
