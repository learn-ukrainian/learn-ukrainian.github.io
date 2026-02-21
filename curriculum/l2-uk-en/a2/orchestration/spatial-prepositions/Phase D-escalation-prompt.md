        # Escalation Fix — Phase D

        You are an expert Ukrainian language editor. The previous agent could not fix
        these audit violations. Fix them precisely.

        ## Audit Errors

        ```
        ============================================================
  HETMAN VERIFY: spatial-prepositions
============================================================

[1/4] Running full audit...
[2/4] Checking sidecar files...
[3/4] Reading status JSON...
[4/4] Checking overall status...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  spatial-prepositions
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  overall status is 'fail' (must be 'pass')
  failing gates:
    lesson: 3640/3000 (raw: 3852) | pedagogy: 17 violations
    activities: 12/10 | density: 1 < 12

  Hetman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
       → FIX: Adjust prompt length to 5-15 words.


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 60/100)
     → Revision recommended (severity 60/100)
     → 17 violations (severe - consider revision)
     → Activity density below minimum


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/audit/spatial-prepositions-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/status/spatial-prepositions.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/spatial-prepositions-audit.log for details)
        ```

        ## Current Content of Affected Section(s)

        ### Descriptive Drill: Опишіть свою кімнату

Спробуйте самостійно описати кімнату, в якій ви зараз знаходитеся. Використовуйте всі прийменники, які ми вивчили.

1. Що знаходиться **перед вами**? (Наприклад: Перед мною стоїть великий комп'ютер.)
2. Що лежить **на столі**? (Наприклад: На столі лежать книги та зошити.)
3. Що висить **на стіні**? (Наприклад: На стіні висить красива картина.)
4. Хто або що сидить **біля вас**? (Наприклад: Біля мене сидить мій собака.)
5. Що знаходиться **під вашим стільцем**? (Наприклад: Під моїм стільцем лежить мій рюкзак.)

Практикуйте ці питання щодня, і ви дуже швидко запам'ятаєте всі правильні закінчення. Відмінки в українській мові — це як математика простору. Треба просто зрозуміти логіку!

### Static Drill: Where is the cat?

Imagine a mischievous cat named **Мурчик**. He is exploring the living room. Look at his position and the case ending used.

1.  **На столі** : Murka is sitting **on** the table. The surface supports him.
2.  **Під столом** : Now he is hiding **under** the table. He is below the surface.
3.  **За диваном** : He is **behind** the sofa. You cannot see him clearly.
4.  **Між кріслами** : He is sitting **between** the armchairs.
5.  **Перед телевізором** : He is sitting **in front of** the TV. He is blocking the screen!
6.  **В коробці** : He climbed **inside** a box. He is enclosed.
7.  **Напроти дзеркала** : He is sitting **opposite** the mirror, looking at himself.

### Motion Drill: Where does the cat go?

Now Mурчик gets the "zoomies" (runs around crazy). Notice how the cases change because he is moving **Куди?**.

1.  Він стрибає **на стіл** . 
2.  Він лізе **під диван** . 
3.  Він біжить **за шафу** . 
4.  Він заліз **у коробку** . 

> [!observe] **The Pattern of Change**
> Notice the shift:
> *   **Location:** *Кіт у коробц**і**.* 
> *   **Motion:** *Кіт лізе у коробк**у**.* 
> This ending change *(-і* vs *-у*) is the only signal telling you whether he is resting or moving.

### Correction Challenge

Read these sentences. They contain common errors. Let's fix them together.

**Mistake 1:** *Я йду в магазині.*
**Analysis:** *В магазині* is Locative . But *йду* is a motion verb. You cannot "be located" while "going to".
**Правильно:** Я йду **в магазин** .

**Mistake 2:** *Книга лежить на стіл.*
**Analysis:** *На стіл* is Accusative . But *лежить* (lies) is a static state.
**Правильно:** Книга лежить **на столі** .

**Mistake 3:** *Він стоїть біля магазин.*
**Analysis:** *Магазин* is Nominative. The preposition *біля* demands the Genitive case.
**Правильно:** Він стоїть **біля магазину** .

**Mistake 4:** *Ми живемо у вулиці Шевченка.*
**Analysis:** A street is an open surface, not an enclosed building. We do not use *в*.
**Правильно:** Ми живемо **на вулиці** Шевченка .

---

## Діалоги / Dialogues


### Dialogue 4: У супермаркеті

Анна шукає потрібні продукти в новому супермаркеті. Вона запитує працівника про допомогу.

**Анна:** Перепрошую, ви можете мені допомогти? Я не можу знайти молоко і сир.
**Працівник:** Звісно! Молочні продукти знаходяться **в кінці залу**, **біля хлібного відділу**. Вам треба йти прямо **через весь магазин**.
**Анна:** Дякую! А де я можу знайти свіжі овочі та фрукти? Вони зазвичай лежать **біля входу**, але тут їх немає.
**Працівник:** У нашому магазині відділ свіжих овочів знаходиться **напроти кас**. Вам потрібно повернутися **до входу** і подивитися **наліво**.
**Анна:** Зрозуміло. І ще одне питання: де лежить кава? Я бачила чай **на полицях** **між солодощами**, але кави там не було.
**Працівник:** Кава знаходиться **на наступному ряду**, **за відділом напоїв**. Вона лежить **на верхній полиці**, тому її іноді важко помітити.
**Анна:** Дуже вам дякую за детальну інформацію! Ви мені дуже допомогли.
**Працівник:** Нема за що. Якщо вам ще щось знадобиться, я буду **біля кас** або **в молочному відділі**. Гарних вам покупок!

### Dialogue 1: Searching for Keys

Oleh cannot find his keys. Watch how he and Iryna use static prepositions (**Де?**) to search the room.

**Олег:** Ірино, ти не знаєш, де мої ключі? Я запізнююся!
**Ірина:** А де ти їх поклав? Може, вони **на столі**?
**Олег:** Ні, **на столі** їх немає. Там тільки журнал.
**Ірина:** Подивися **в сумці**. Ти вчора ходив з нею.
**Олег:** Дивлюся... Ні, **в сумці** пусто.
**Ірина:** А це що **під кріслом**?
**Олег:** Де? А, точно! Вони впали **під крісло**. Дякую!
**Ірина:** Ти як завжди. Клади їх **на полицю** біля дверей, і не будеш шукати.

**Олег:** Де ж вони можуть бути? Я вже шукав **у машині**, але там їх немає.
**Ірина:** Можливо, вони впали **за диван**?
**Олег:** Я дивився **за диваном**. Там тільки старі іграшки нашого кота.
**Ірина:** А **на тумбочці** **в коридорі**?
**Олег:** Я завжди кладу їх **на тумбочку**, але сьогодні їх там немає.
**Ірина:** Добре, давай шукати разом. Я подивлюся **на кухні** **в шафках**.
**Олег:** А я перевірю **у ванній кімнаті**. Може, я залишив їх **біля раковини**.
**Ірина:** О! Я знайшла їх! Вони були **під газетою** **на кухонному столі**.
**Олег:** Ой, точно. Я читав газету і поклав їх **під неї**.
**Ірина:** Наступного разу будь уважнішим і клади ключі тільки **на їхнє місце**.


*Vocabulary Note:*
*   *на столі*  - location check.
*   *в сумці*  - location check.
*   *під кріслом*  - location check.
*   *під крісло*  - motion (they fell *to* under the chair).
*   *на полицю*  - advice to place them *onto* the shelf.

### Dialogue 2: The Interior Designer

Imagine we are arranging a new apartment. We need to decide where to place furniture. This involves "Motion" grammar (placing things) and "Location" grammar (visualizing the result).

**Дизайнер:** Отже, це ваша вітальня. Вона дуже світла. Де ми поставимо диван?
**Клієнт:** Я думаю, краще поставити його **біля стіни**, **напроти вікна**.
**Дизайнер:** Гарна ідея. Тоді телевізор буде висіти **на стіні** **перед диваном**.
**Клієнт:** Так. А **між диваном** і **вікном** ми поставимо велику квітку.
**Дизайнер:** Чудово. А де буде стіл?
**Клієнт:** Стіл нехай стоїть **посеред кімнати**, **під люстрою**.
**Дизайнер:** Згода. А килим?
**Клієнт:** Килим ми покладемо **на підлогу** **під стіл**.
**Дизайнер:** Виходить дуже затишно. У вас хороший смак!

**Дизайнер:** А як щодо спальні? Які у вас ідеї?
**Клієнт:** Я хочу поставити ліжко **посеред кімнати**, щоб воно не стояло **біля стіни**.
**Дизайнер:** Це цікаво. Тоді ми повісимо балдахін **над ліжком**. А де буде шафа?
**Клієнт:** Шафу краще поставити **в кутку**, **за дверима**. Вона велика і не повинна заважати.
**Дизайнер:** Чудово. А туалетний столик? Ми можемо поставити його **між вікном** та **ліжком**.
**Клієнт:** Так, це ідеальне місце. А пуфик я поставлю **перед столиком**.
**Дизайнер:** Залишилося знайти місце для картин.
**Клієнт:** Ми повісимо картини **на стіни** **напроти ліжка**.
**Дизайнер:** Прекрасний вибір. Ваша квартира буде дуже сучасною і комфортною.


*Key Phrases:*
*   *поставити біля стіни* (Motion/Placement + Genitive).
*   *напроти вікна* .
*   *на стіні* (Locative - static result).
*   *перед диваном* (Instrumental - relative position).
*   *між диваном і вікном* (Instrumental - separation).
*   *під люстрою* (Instrumental - vertical alignment).
*   *покладемо на підлогу* (Motion + Accusative).

### Dialogue 3: On the Street (Asking Directions)

You are lost in Lviv. You need to find the Opera House.

**Турист:** Перепрошую, ви не скажете, де тут Оперний театр?
**Перехожий:** Добрий день. Так, це недалеко. Дивіться, ви зараз стоїте **біля пам'ятника**.
**Турист:** Так.
**Перехожий:** Ідіть прямо **через парк**. Театр буде **напроти музею**.
**Турист:** А музей де?
**Перехожий:** Музей стоїть **за церквою**. Бачите той купол?
**Турист:** Так, бачу.
**Перехожий:** Отже, ідіть **до церкви**, потім поверніть наліво. Театр буде прямо **перед вами**.
**Турист:** Дякую!
**Перехожий:** Будь ласка. Гарного дня **у Львові**!

**Турист:** А де тут можна випити хорошої кави?
**Перехожий:** О, кав'ярні тут всюди! Але найкраща знаходиться **біля Ратуші**.
**Турист:** Це далеко звідси?
**Перехожий:** Ні, всього п'ять хвилин пішки. Ідіть **по цій вулиці** прямо, потім поверніть направо **біля фонтану**.
**Турист:** Добре, я зрозумів. А чи є якийсь хороший ресторан **недалеко від театру**?
**Перехожий:** Так, **за театром** є чудова ресторація української кухні. Вона розташована **в старому підвалі**.
**Турист:** Це звучить дуже цікаво. Я обов'язково туди зайду **після вистави**.
**Перехожий:** Раджу вам замовити столик заздалегідь, бо **ввечері** там завжди багато людей.
**Турист:** Дуже вам вдячний за допомогу!
**Перехожий:** Прошу дуже! Насолоджуйтесь вашим часом **у нашому місті**.


*Analysis:*
*   *біля пам'ятника*  - current location.
*   *напроти музею*  - relative location.
*   *за церквою*  - hidden location.
*   *до церкви*  - destination .
*   *перед вами*  - relative location.
*   *у Львові*  - location in a city.

---

# Підсумок

Congratulations! You have just learned the map of the Ukrainian spatial universe. You now know that describing space is not just about naming a spot; it is about describing the energy of the object. Is it resting  or is it moving ?

**Key Takeaways:**
1.  **В/На + Locative** = Resting place (Where?).
2.  **В/На + Accusative** = Destination (Where to?).
3.  **Під/Над/Перед/За/Між + Instrumental** = Relative position (Where?).
4.  **Біля/Напроти/До/З + Genitive** = Proximity and Approach.

**Перевірте себе:**

1.  If I want to say "The book is on the table", which case do I use for "table"? (Locative or Accusative?)
2.  If I say "I am putting the book on the table", does the case change? Why?
3.  Which preposition means "under"? Which case does it use when the object is staying there?
4.  Translate the logic: Why do we say "Я йду в банк"  but "Я був у банку" ?
5.  What is the difference between **біля** (near) and **напроти** (opposite)?
6.  Explain the "Open Space" rule for using **НА** instead of **В**. Why do we say **на концерті**?

In the next modules, we will practice these cases more deeply. But for now, look around your room. Where is your phone? *На столі*? Or *в кишені*? Try to label the world around you!

        ## File Path

        `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/spatial-prepositions.md`

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
