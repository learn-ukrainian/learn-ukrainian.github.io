        # Escalation Fix — Phase D

        You are an expert Ukrainian language editor. The previous agent could not fix
        these audit violations. Fix them precisely.

        ## Audit Errors

        ```
        ============================================================
  HETMAN VERIFY: emergencies
============================================================

[1/4] Running full audit...
[2/4] Checking sidecar files...
[3/4] Reading status JSON...
[4/4] Checking overall status...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  emergencies
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  overall status is 'fail' (must be 'pass')
  failing gates:
    lesson: 2783/2000 (raw: 2913) | pedagogy: 4 violations
    activities: 10/8 | density: 3 < 12

  Hetman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
    [COMPLEXITY_WORD_COUNT] quiz 'Перевірка розуміння: Кличний відмінок' Q6 prompt length 4 (target: 5-10)
       → FIX: Adjust prompt length to 5-10 words.


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 25/100)
     → 4 violations (moderate)
     → Activity density below minimum


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/emergencies-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/emergencies.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/emergencies-audit.log for details)
        ```

        ## Current Content of Affected Section(s)

        <!-- SCOPE
Covers: Emergency vocabulary, calling emergency services, describing problems, reporting location, the Vocative case for direct address, imperative polite requests.
Not covered:
  - Complex medical terminology → a1-31 (Body and Health)
Related: a1-31 (Body and Health), a1-41 (Phone Basics)
-->

# Emergencies

> **Чому це важливо?**
>
> Learning how to ask for help is arguably the most fundamental and critical skill you can acquire in any new language. While we all sincerely hope that you will never need to use these specific words in a real-life crisis, knowing exactly how to call emergency services, clearly state your current location, and accurately describe a basic problem ensures your personal safety. Navigating a stressful situation is difficult enough; having the right Ukrainian vocabulary prepared in your mind acts as a vital safety net. Today, we will learn how to communicate effectively, calmly, and correctly during critical situations in Ukraine.

## Вступ

### The Core Concept of Help
Коли ви в новій країні й є проблема, найважливіше — знати, як просити про допомогу. In the Ukrainian language, the core noun for assistance or aid is **допомога** (help). Це слово дуже часто звучить у реальному житті. Воно формує основу багатьох критичних фраз. Ви шукаєте вулицю. Потрібен лікар. Потрібна поліція. Усюди допомагає це слово. Вони рятують життя. Ви маєте знати його дуже добре. 

Коли є велика проблема, ви кажете: **«Допоможіть, будь ласка!»** (Help, please!). Це дуже важлива фраза. Також ви можете сказати: **«Тут потрібна термінова допомога.»** (Urgent help is needed here.) або **«Тут потрібна допомога.»** (Help is needed here.).

Ці прості українські фрази дуже корисні на вулиці. Люди бачать проблему. Вони зупиняються. Це головні слова. Вони рятують життя. Формально це слово означає "ви". Але в екстреній ситуації це не має значення. Ви кричите так одному чоловіку. Ви кричите так групі людей. Це універсальний сигнал. Він працює завжди. 

### Emergency Services in Ukraine
В Україні є дуже важливі номери для вашої безпеки. Ви можете телефонувати на новий єдиний номер: **112**. Це універсальний європейський номер. You can dial 112 from any phone to reach a central dispatcher who will route your call. 

Але також є старі номери. Вони працюють дуже добре, і всі люди знають ці номери:

* Номер **101** — це **пожежна** (fire service). Є пожежа. Ви телефонуєте 101.
* Номер **102** — це **поліція** (police). Є аварія. Ви телефонуєте 102.
* Номер **103** — це **швидка** (ambulance). Є травма. Ви телефонуєте 103.

Дуже важливо знати ці номери. Вони гарантують вашу безпеку.

> [!fact] Єдиний номер 112 та євроінтеграція
> The systematic implementation of the unified 112 emergency number across all regions of Ukraine represents a highly significant step in aligning the country's infrastructure with standard European Union protocols. It greatly simplifies the crisis process for both local citizens and foreign visitors, ensuring that a single, easily remembered phone call can simultaneously deploy police, medics, or rescue workers if a complex, multi-layered situation arises.

## Презентація

### The Vocative Case for Emergencies (Кличний відмінок)
Англійською слово "Doctor!" не змінюється. Українська мова працює інакше. Вона має спеціальну форму. Це Кличний відмінок (**кличний відмінок**). Ви змінюєте слово. Так ви звертаєтеся до людини. Це привертає увагу.

У стресовій ситуації ви не використовуєте звичайну форму слова. Ви активно змінюєте закінчення. Це чіткий сигнал. Ви говорите саме до цієї людини. Ваше прохання звучить природно. Це дуже правильно. Давайте подивимося на приклади. Так змінюються професії.

Чоловічі професії мають твердий приголосний в кінці. Ми додаємо голосний **-ю** або **-е**:
* **Лікар** (doctor) transforms into the address form **Лікарю!** (Doctor!)
* **Офіцер** (officer) transforms into the address form **Офіцере!** (Officer!)

For feminine nouns ending in the vowel **-я**, the ending shifts to **-є**:
* **Поліція** (police) transforms into the collective address form **Поліціє!** (Police!)

Наприклад, на вулиці ви можете кричати: **«Лікарю, сюди!»** (Doctor, over here!). Є небезпека. Ви кажете: **«Поліціє, сюди, будь ласка!»** (Police, over here, please!). Також ви можете сказати офіцеру: **«Офіцере, сталася проблема.»** (Officer, a problem happened.). 

Кличний відмінок — це повага. Так ви звертаєтесь до людини прямо. Людина чує свою професію й одразу реагує.

### Calling vs. Summoning: «Дзвонити» vs «Викликати»
Англомовні люди часто роблять помилку. Вони перекладають фразу "to call the police" дослівно. Англійською дієслово "to call" універсальне. Це звичайна розмова. Це ваш друг. Ви просите медичну допомогу. Українською це два різні дієслова. Українська мова вимагає точності.

Дієслово **дзвонити** означає просто розмову. Ви набираєте номер. Ви спілкуєтеся. Ви використовуєте це дієслово для мами. Ви телефонуєте колезі. Ви дзвоните другу.
Дієслово **викликати** має офіційне значення. Це офіційний запит. Ви просите службу приїхати до вас. Це обов'язкове дієслово для екстрених ситуацій.

> [!warning] Увага: Уникайте колоніальних русизмів!
> A very common linguistic error (known as a Russism or a "калька") is using the incorrect word «визивати» when discussing emergencies. This heavily flawed usage stems entirely from historical Russian linguistic influence and is strictly incorrect in modern, normative Ukrainian. You must systematically train yourself to never say "визивати швидку". The only correct, authentic, and beautiful Ukrainian phrasing is **викликати швидку**.

Ви не можете сказати "Я дзвоню поліцію" (Incorrect). Правильна українська фраза звучить так: **«Я викликаю поліцію.»** (Correct: I am officially summoning the police.). Також неправильно казати "Треба визивати швидку" (Incorrect: Colonial Russism). Правильний і дуже красивий варіант: **«Треба викликати швидку.»** (Correct: It is necessary to summon an ambulance.). Це важливо знати.

### Describing Your Location
Диспетчер відповідає на телефон. Перше і дуже важливе запитання: "Де ви?". Ви маєте бути готові. Ви називаєте вашу **адресу** (address) дуже чітко. Іноді ви не знаєте вулицю. Іноді ви не знаєте номер будинку. Тоді ви використовуєте прийменники місця. Це дуже допомагає.

Ви можете використовувати прийменник **біля** (near). Ви називаєте великий об'єкт. Прийменник **біля** вимагає Родового відмінка (Genitive case). Слово змінює закінчення. Але багато іноземних слів не змінюються. Наприклад, слово "метро" завжди "метро".

Наприклад, ви телефонуєте і кажете: **«Я зараз біля метро.»** (I am near the subway right now.). Або ви пояснюєте: **«Ми зараз біля великого парку.»** (We are near the large park right now.). Ви знаєте адресу. Тоді ви говорите: **«Моя точна адреса: вулиця Франка, десять.»** (My exact address is Franko Street, ten.). Також корисна фраза: **«Я стою на розі вулиць.»** (I am standing at the corner of the streets.).

Описуйте місце просто. Називайте великі об'єкти біля вас. Це найкраща стратегія. Це допомагає швидко передати інформацію диспетчеру.

### Stating the Problem
Диспетчер знає вашу адресу. Далі ви швидко описуєте проблему. Це конкретна **небезпека** (danger). Тут не потрібна складна граматика. Одне або два прості слова працюють ідеально. Диспетчер добре розуміє ситуацію. Він знає ситуацію. Правильна допомога їде.

На дорозі є проблема. Машини зіткнулися. Ви використовуєте спеціальне слово **аварія** (accident). В офіційних ситуаціях використовують абревіатуру **ДТП** (дорожньо-транспортна пригода). Вона звучить у поліції. Вона звучить у новинах. 

Людина має фізичний біль. Вона постраждала. Ви обов'язково кажете слово **травма** (injury). Диспетчер чує це слово. Він одразу відправляє швидку медичну допомогу. Людину везуть у місцеву **лікарню** (hospital).

Диспетчер запитує про проблему. Ви відповідаєте: **«Тут на вулиці сталася аварія.»** (An accident happened here on the street.). Ви також можете використати абревіатуру: **«Увага, тут велика ДТП.»** (Attention, there is a major traffic accident here.). Хтось має травму. Тоді ви пояснюєте: **«Тут серйозна травма.»** (There is a serious injury here.). І ви додаєте: **«Тут дуже потрібна лікарня.»** (A hospital is desperately needed here.). Це дає диспетчеру чітку інформацію.

> [!observe] Граматичне спостереження: «Сталася»
> Notice the phrase **«сталася аварія»**. The verb **сталася** means "happened" or "occurred". Because the noun **аварія** is grammatically feminine (ending in -я), the past tense verb must match it, taking the feminine ending **-ася**. This agreement makes your speech sound highly fluent.

## Практика

### Scenario 1: Reporting a Traffic Accident
Let us now systematically put all these individual linguistic pieces together into a highly realistic, practical scenario. Imagine for a moment that you have just witnessed a severe car accident on a busy city street. You immediately dial 112 on your phone. The central dispatcher answers your call. You need to focus, stay entirely calm, state the core problem, provide your exact location, and clearly mention if there is a **свідок** (witness) present at the scene.

Here is exactly how a simple, highly effective emergency phone call might look in practice:

**Диспетчер:** Служба 112. Що саме сталося? (Service 112. What exactly happened?)
**Ви:** Добрий день. Тут сталася велика аварія. (Good afternoon. A major accident happened here.)
**Диспетчер:** Де ви зараз знаходитесь? (Where are you located right now?)
**Ви:** Я стою біля метро «Хрещатик». (I am standing near the Khreshchatyk subway station.)
**Диспетчер:** Чи є травми? Потрібна швидка? (Are there any injuries? Is an ambulance needed?)
**Ви:** Так, терміново потрібна швидка. Тут є травма. (Yes, an ambulance is urgently needed. There is an injury here.)
**Диспетчер:** Зрозуміло. Швидка і патрульна поліція вже їдуть. Ви свідок? (Understood. An ambulance and patrol police are already on their way. Are you a witness?)
**Ви:** Так, я свідок ДТП. Я чекаю поліцію тут. (Yes, I am a witness to the traffic accident. I am waiting for the police here.)

Notice carefully how remarkably short and profoundly direct the Ukrainian sentences are in this dialogue. In a genuine emergency scenario, absolute clarity is infinitely more important than demonstrating complex grammatical fluency.

### Scenario 2: Lost or Stolen Documents
It is important to remember that not all intense emergencies involve immediate physical danger to your body. Sometimes, you might accidentally lose your international passport or have your wallet stolen, which is a highly stressful and disorienting experience, especially when you are navigating life in a foreign country. In these specific cases, you will need to physically approach and speak with a police officer to officially report the unfortunate incident.

You absolutely need to master two key action verbs here: **шукати** (to look for) and **брати** (to take). If you are speaking with a working police officer, they will inevitably ask detailed questions about your missing **документи** (documents) and may formally ask you to sit down and write a detailed **заява** (statement, official report, or application).

> [!tip] Практична порада: Що робити?
> If you are not absolutely sure what happened to your bag, it is usually a much better legal strategy to start the conversation by simply saying you are looking for it (**«Я шукаю...»**). This phrasing immediately initiates the administrative helpful process.

Наприклад, ви можете сказати поліції: **«Я зараз шукаю мої документи.»** (I am currently looking for my documents.). Або ви пояснюєте: **«Я шукаю мій паспорт.»** (I am looking for my passport.). Проблема дуже велика. Ви кажете: **«Хтось бере мою чорну сумку.»** (Someone takes my black bag.). Потім ви додаєте: **«Я хочу офіційно подати заяву в поліцію.»** (I want to officially submit a statement to the police.). Після цього **«Цей працівник поліції перевіряє документ.»** (This police officer is checking the document.).

### Making Polite Urgent Requests
When you are actively interacting with emergency personnel, medical dispatchers, or state officials, you are very often required by the situation to give direct commands or make highly urgent requests. However, as a functional adult in society, you still want to maintain a respectful, socially acceptable tone. In the Ukrainian language, we achieve this delicate balance gracefully by taking the standard imperative (command) form of an action verb and immediately following it with the socially vital magic phrase: **будь ласка** (please).

This simple linguistic combination successfully transforms what could be perceived as a harsh, rude order into a firm, highly polite, and strictly professional request. It is the exact, perfect tone you need to strike when you want a busy police officer or a stressed dispatcher to take immediate action or provide you with critical information rapidly.

Наприклад, працівник каже: **«Скажіть, будь ласка, вашу точну адресу.»** (Tell me, please, your exact address.). Або: **«Дайте, будь ласка, цей офіційний документ.»** (Give me, please, this official document.). Ви також можете попросити: **«Допоможіть, будь ласка, правильно написати заяву.»** (Help me, please, to correctly write a statement.). Іноді офіцер каже: **«Зачекайте, будь ласка, патрульну поліцію на вулиці.»** (Wait, please, for the patrol police on the street.). Ці фрази дуже ввічливі і професійні.

By consistently using these balanced grammatical structures, you manage to assert your immediate needs with absolute clarity while simultaneously respecting the necessary professional boundaries of the hardworking emergency workers assisting you.

## Виробництво та підсумок

### Role-Play: At the Police Station or Embassy
Imagine yourself vividly in a frustrating scenario: you are currently standing inside a local Ukrainian police station or perhaps at the secure window of your home country's embassy in Kyiv. This is because your wallet, containing all your crucial identification, has suddenly gone missing. You must confidently approach the administrative desk and explain your complex situation clearly to the officer or the clerk currently on duty. 

Ви підходите до поліції. Ви кажете:
**Ви:** «Добрий день. Тут терміново потрібна допомога. Я зараз шукаю усі свої документи.» (Good afternoon. Urgent help is needed here. I am currently looking for all my documents.)

Офіцер відповідає спокійно:
**Офіцер:** «Будь ласка, спокійно. Розкажіть про проблему. Де це?» (Please, calmly. Tell me, where exactly did this problem happen?)

Ви називаate ваше місце:
**Ви:** «Я зараз біля великого парку. Я шукаю мій гаманець.» (I am near the large park right now. I am looking for my wallet.)

Після цього офіцер пояснює офіційні кроки:
**Офіцер:** «Все зрозуміло. Дайте, будь ласка, якийсь інший документ. Тут обов'язково треба написати заяву.» (Everything is understood. Give me, please, some other document. It is absolutely necessary to write a statement here.)

By deeply mastering these relatively short, highly specific interactive patterns, you can successfully navigate daunting administrative hurdles with surprising confidence, even when operating under the immense pressure of a stressful, unexpected life event.

### Digital Support in Ukraine: «Дія» and «єДопомога»
Ukraine currently stands as one of the absolute most digitally advanced and integrated countries in the entire world, particularly when it comes to providing essential government services directly to citizens' smartphones. In times of severe national or personal crisis, this robust digital infrastructure rapidly transforms from a mere convenience into an absolute lifeline.

> [!culture] Цифрова держава: Дія та єДопомога
> The revolutionary state smartphone application known as **«Дія»** (which translates to "Action") allows all Ukrainians to legally carry their fully verified digital passports, valid driver's licenses, and official tax numbers right inside their pockets. Crucially, these digital documents possess the exact same rigorous legal power and authority as their traditional paper counterparts. If you happen to tragically lose your physical, leather wallet, opening the «Дія» application can successfully prove your true identity to a police officer almost immediately. Furthermore, the innovative **«єДопомога»** (which translates to "e-Help") digital platform was specifically and rapidly created to quickly, seamlessly connect vulnerable people who desperately need urgent humanitarian aid or vital financial assistance directly with willing volunteers and robust state resources. These remarkable technological tools beautifully highlight the deep, enduring solidarity and the impressive technological resilience of modern, everyday Ukrainian society.

### Rapid-Fire Response Drilling
Коли ви викликаєте допомогу, диспетчер ставить питання швидко. Диспетчер хоче оцінити проблему негайно. У вас немає часу будувати довгі ідеальні речення. Ви маєте давати короткі, але інформативні відповіді. You must diligently practice giving sharp, one- or two-word answers to these highly common dispatcher prompts:

Let us practice this rhythm:

* **Диспетчер:** Де ви зараз? (Where are you right now?)
  * **Ви:** Біля метро. (Near the subway.)
* **Диспетчер:** Що конкретно сталося? (What specifically happened?)
  * **Ви:** Велика аварія. (A major accident.)
* **Диспетчер:** Чи є там травми? (Are there injuries there?)
  * **Ви:** Так, потрібна швидка. (Yes, an ambulance is needed.)
* **Диспетчер:** Хто саме там є? (Who exactly is there?)
  * **Ви:** Я єдиний свідок. (I am the only witness.)

Коли ви говорите просто і прямо, ви економите дорогоцінні секунди. Це дуже важливо в екстреній ситуації.

---

# Підсумок

In this comprehensive module, we have thoroughly covered the essential, life-saving language structures required to confidently navigate unpredictable emergency situations within Ukraine. We learned exactly how to call out for vital **допомога** and clearly established the profound semantic difference between casually dialing a friend on the phone (**дзвонити**) and officially, urgently summoning state services to your physical location (**викликати**). You now intimately know the critical national emergency telephone numbers (101, 102, 103, and the modernized, unified 112 system) and exactly how to address brave professionals properly and respectfully by using the dynamic Vocative case (**Лікарю!**, **Поліціє!**). Furthermore, we extensively practiced describing complex physical problems like an unexpected **аварія** or suddenly lost **документи**, providing our precise **адреса**, and making polite, structurally sound, but highly urgent imperative requests. While we sincerely and deeply hope that you never actually need to utilize this specific stressful vocabulary, possessing these linguistic skills provides a vital, comforting safety net as you confidently continue your exciting journey in mastering the beautiful Ukrainian language.

**Перевірте себе:**
1. What is the newly unified emergency phone number currently being actively implemented across Ukraine, and what broader political concept does its adoption symbolize?
2. Why is it structurally and culturally incorrect to say the phrase "Я дзвоню поліцію", and what is the proper, normative Ukrainian verb you must use instead?
3. How exactly do you alter the grammatical endings of the nouns "Лікар" and "Поліція" when you are calling out to them directly for immediate help?
4. If you accidentally drop your travel passport while running in the city park, which specific Ukrainian verb should you utilize to describe the event: "загубити" or "вкрасти"?
5. How can you effectively transform a blunt, direct grammatical command like "Скажіть адресу" into a socially polite yet urgent request that is entirely suitable for speaking to a stressed emergency dispatcher?

---

        ## File Path

        `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/emergencies.md`

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
