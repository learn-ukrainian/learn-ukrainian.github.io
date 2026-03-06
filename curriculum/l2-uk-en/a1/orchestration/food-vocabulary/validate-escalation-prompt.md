        # Escalation Fix — validate

        You are an expert Ukrainian language editor. The previous agent could not fix
        these audit violations. Fix them precisely.

        ## Audit Errors

        ```
        Auditing: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/food-vocabulary.md
Saving log to: curriculum/l2-uk-en/krisztiankoos/audit/food-vocabulary-audit.log


========================================
  📋 Loaded Plan from: plans/a1/food-vocabulary.yaml
  📋 Loaded Metadata from YAML sidecar

📋 Auditing: A1 M39 — Food and Drink
   File: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/food-vocabulary.md | Target: 1200 words
  📋 Required activity types from meta: fill-in, group-sort, match-up, quiz
  📋 Template: docs/l2-uk-en/templates/a1-module-template.md (pedagogy: PPP)
Traceback (most recent call last):
  File "/Users/krisztiankoos/projects/learn-ukrainian/scripts/audit_module.py", line 160, in <module>
    success = audit_module(file_path, skip_activities=args.skip_activities,
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/krisztiankoos/projects/learn-ukrainian/scripts/audit/core.py", line 972, in audit_module
    outline_violations = check_outline_compliance(file_path, level_code, module_num)
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/krisztiankoos/projects/learn-ukrainian/scripts/audit/checks/outline_compliance.py", line 298, in check_outline_compliance
    outline_section_names = [s["section"] for s in outline]
                             ~^^^^^^^^^^^
KeyError: 'section'

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/food-vocabulary-audit.log for details)

Running RAG word verification...
Verifying: food-vocabulary.md
  VESUM misses: 10 — querying RAG...
[embed] Loading BGE-M3 from BAAI/bge-m3...

Fetching 30 files:   0%|          | 0/30 [00:00<?, ?it/s]
Fetching 30 files: 100%|██████████| 30/30 [00:00<00:00, 15105.54it/s]
[embed] BGE-M3 loaded.
You're using a XLMRobertaTokenizerFast tokenizer. Please note that with a fast tokenizer, using the `__call__` method is faster than using a method to encode the text followed by a call to the `pad` method to get a padded encoding.
  Words: 602 | VESUM: 592 (98.3%) | RAG: 4 | Not found: 6
  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/food-vocabulary-rag-audit.md
⚠️  RAG verification found unverified words (see audit report)

VESUM: 592/602 (98%) verified
⚠️ VESUM not found (10): Анна, борща, Кушати, Марія, Олена, Олено, сока, сіка, чая, Іван
        ```

        ## Current Content of Affected Section(s)


---
## Мені подобається / Я не їм (Preferences)
Кожна людина має свої власні гастрономічні смаки та особливі вподобання. Ми зараз вчимося говорити про наші особисті смаки. Важливо говорити про свої смаки. Це робить бесіду дуже цікавою. Це дуже корисна тема.

Every single person has their own unique gastronomic tastes and special preferences. We are now actively learning how to talk about our personal tastes. This is an incredibly useful topic for daily conversations and social interactions.

### Як сказати про симпатії

Ви маєте знати просту і дуже корисну фразу. Ми використовуємо дієслово «любити» для опису улюбленої їжі. Це дуже природна граматична структура.

You absolutely must know a simple and highly useful phrase. We use the verb for loving constantly for describing our absolute favorite meals. This is a very natural and fundamental grammatical structure.

Коли ви кажете цю фразу, ви змінюєте слово. Ми використовуємо знахідний відмінок для їжі та напоїв. Правило працює абсолютно однаково.
When you confidently state this phrase, you grammatically alter the following noun. Use the accusative case for the specific items. The rule works exactly the same way as when you order at a restaurant.

*   **Я люблю́ бо́рщ.** (I love borscht.)
*   **Я люблю́ цей гаря́чий су́п.** (I love this hot soup.)
*   **Я люблю́ ка́ву і молоко́.** (I love coffee and milk.)
*   **Я люблю́ сма́жену ри́бу.** (I love fried fish.)

As a general and reliable rule of thumb, use this specific verb construction when you want to confidently express a strong personal attachment. It shows deep passion or active preference for a particular dish. It is a perfectly natural and universally understood way to state your enthusiastic likes.

> [!tip] **Applying the Rule Consistently**
> Remember the golden rule for the Accusative case: feminine nouns ending in **-а** change to **-у** (вода ➡️ воду). Masculine and neuter nouns stay exactly the same (борщ ➡️ борщ). Apply this both when ordering ("Я хочу...") and when expressing preference ("Я люблю...").

### Заперечення

Іноді ми зовсім не хочемо щось їсти або пити. Для цього ми використовуємо просте і чітке заперечення. Це маленьке слово «не».

Sometimes we absolutely do not want to eat or drink something. For this specific situation, we heavily rely on a simple and clear negation. We use a tiny but powerful negative particle.

Правило дуже просте і легке. Ви просто ставите це маленьке слово перед дієсловом.
The grammatical mechanics are incredibly straightforward and wonderfully easy to master. You simply place the small negative word directly and immediately before the main action verb of your sentence.

*   Я ї́м ➡️ Я **не** ї́м (I do not eat)
*   Я п'ю́ ➡️ Я **не** п'ю́ (I do not drink)
*   Я люблю́ ➡️ Я **не** люблю́ (I do not love)

**Приклади в контексті:**
*   Я зо́всім не ї́м м'я́со. (I do not eat meat at all.)
*   Вона́ ніко́ли не п'є́ ка́ву пі́зно вве́чері. (She never drinks coffee late in the evening.)
*   Ми не їмо́ цей су́п. (We do not eat this soup.)
*   Я не люблю́ ри́бу. (I do not love fish.)

Being able to clearly, firmly, and politely state exactly what you do not consume is a vital and non-negotiable survival skill in any foreign environment. This is especially profoundly true if you fiercely hold specific dietary preferences. The grammatical structure is intentionally kept simple and exceptionally direct to completely avoid any dangerous miscommunication.

### Алергія та дієта

Сьогодні багато сучасних людей мають особливі суворі дієти. Вони також можуть мати серйозні медичні алергії. Ви обов'язково маєте знати ці важливі слова.

Today, many modern people strictly follow special and rigorous diets. They can also have serious medical allergies. You absolutely must confidently know these critically important phrases to protect your personal health and safety.

**Корисні фрази:**
*   **У ме́не алер́гія на...** (I have an allergy to...)
    *   У ме́не алер́гія на горі́хи. (I have an allergy to nuts.)
    *   У ме́не алер́гія на молоко́. (I have an allergy to milk.)
*   **Я не мо́жу ї́сти...** (I cannot eat...)
    *   Я не мо́жу ї́сти глюте́н. (I cannot eat gluten.)
    *   Я не мо́жу ї́сти цу́кор. (I cannot eat sugar.)

Місцеві жителі завжди щедро годують гостей. Вони часто просять їсти багато. Але вони дуже поважають медичні алергії. Ви маєте прямо говорити про свою дієту.
Locals are traditionally famous for being incredibly eager to generously feed their welcomed guests. They will enthusiastically try to coax you into taking just one more small bite. However, they deeply respect serious medical allergies. You must clearly and firmly state your strict dietary boundary.

### Діалоги під час обіду

Ось ці тексти. Так різні люди говорять під час спільного обіду. Це дві дуже типові та реальні розмови.

Look very closely at these provided texts. This is exactly how different people actually speak during a shared meal. These are two highly typical and realistic conversational exchanges you might easily overhear.

**Діалог 1: У гостях (Visiting guests)**
**Марі́я:** Оле́но, ти хо́чеш ї́сти бо́рщ? (Olena, do you want to eat borscht?)
**Оле́на:** Ні, дя́кую. Я не ї́м м'я́со. Я люблю́ ті́льки ри́бу. (No, thank you. I don't eat meat. I only love fish.)
**Марі́я:** О, я все розумі́ю. Тоді́ ось ці сві́жі о́вочі для тебе. (Oh, I completely understand. Then here are these fresh vegetables for you.)

**Діалог 2: Вибір напою (Choosing a drink)**
**Іва́н:** Що ти зазвича́й лю́биш пи́ти зра́нку? (What do you usually love to drink in the morning?)
**А́нна:** Я дуже люблю́ міцну́ чо́рну ка́ву. А ти? (I really love strong black coffee. And you?)
**Іва́н:** А я люблю́ зеле́ний ча́й. Я зо́всім не п'ю́ ка́ву. (And I love green tea. I don't drink coffee at all.)

---
## Напої (Drinks)
Тепер ми говоримо про популярні напої. Українці люблять пити смачні напої. Це частина нашої щоденної культури. Україна має надзвичайно багату культуру напоїв. У нас є традиційні домашні рецепти. У нас також є дуже сучасні кав'ярні.

Now we talk in detail about popular drinks. The country proudly boasts an incredibly rich beverage culture. We preserve comforting traditional homemade recipes handed down through generations. At the same time, we also enjoy an exceptionally modern and vibrant urban coffee shop scene.

### Популярні напої

Ми вчимо назви популярних напоїв. Вони дуже важливі щодня. Важливо знати їхній граматичний рід.

We learn the exact names of the most famous and popular drinks. You absolutely need these words every single day in any city. Make a strong mental note of their grammatical gender right now.

**Нові слова:**
| Слово | Рід | Переклад |
|---|---|---|
| **вода́** | жіночий | water |
| **ка́ва** | жіночий | coffee |
| **ча́й** | чоловічий | tea |
| **сі́к** | чоловічий | juice |
| **компо́т** | чоловічий | fruit compote |
| **молоко́** | середній | milk |

**Приклади в контексті:**
*   На столі́ стої́ть холо́дна вода́. (Cold water stands on the table.)
*   Я щора́нку п'ю гаря́чу ка́ву. (I drink hot coffee every morning.)
*   Твій апельси́новий сі́к дуже смачни́й. (Your orange juice is very delicious.)
*   Бабу́ся ро́бить соло́дкий компо́т. (Grandma makes sweet compote.)

The word for compote refers to a deeply traditional homemade beverage. It is created by boiling fresh or dried fruits and berries in water. It is usually sweetened with sugar. It is served in almost every household and offers a genuine taste of home.

### Як замовити напій

У кафе або ресторані важливо знати правила замовлення. Ми використовуємо знахідний відмінок для об'єкта дії. Це дуже важливе граматичне правило.

In a cozy cafe or a large restaurant, it is important to know the proper rules for ordering. We use the accusative case for the direct object of your action. This is an incredibly important grammatical rule that you will use constantly.

When you use the standard phrase for wanting something, the noun that immediately follows it must be transformed. Here is how you apply the rule depending on the noun gender:

Перше правило стосується чоловічого та середнього роду. Ці слова зовсім не змінюють своє закінчення. Вони залишаються у базовій формі.
The first rule applies to masculine and neuter nouns. They stay exactly the same as their basic dictionary form. They do not change their endings at all.
*   ча́й ➡️ Я хо́чу ча́й. (I want tea.)
*   сі́к ➡️ Я хо́чу сі́к. (I want juice.)
*   молоко́ ➡️ Я хо́чу молоко́. (I want milk.)

Друге правило стосується слів жіночого роду на **-а**. Під час замовлення вони змінюють своє закінчення на **-у**.
The second rule targets feminine nouns ending in **-а**. When ordering them as a direct object, their ending changes to **-у**. This Accusative case shift is the most critical one for beginners to remember and practice.
*   вода́ ➡️ Я хо́чу вод**у́**. (I want water.)
*   ка́ва ➡️ Я хо́чу ка́в**у**. (I want coffee.)

> [!culture] **The Feminine Shift**
> Beginners frequently forget to change the feminine ending when ordering. While a polite waiter will certainly understand you, this grammatical error sounds instantly jarring to a native speaker. You must actively train your brain to automatically apply the new ending the moment you decide to confidently order a drink.

### Традиції пиття в Україні

Які саме напої найчастіше п'ють українці? Наші смаки дуже різноманітні і залежать від регіону. Вони також залежать від часу доби.

What exact drinks do locals drink most often? Our tastes are highly diverse and depend heavily on the specific region. They also depend closely on the time of day and the changing seasons.

Гарячий чай — це дуже популярний домашній напій. Взимку люди часто п'ють чай. Вони також люблять лимон і мед. Це дарує тепло і здоров'я. Сучасні міста мають багато нових кав'ярень.
Hot tea is universally cherished across the entire country. This is especially true in the warm comfort of one's home. A classic and beloved way to serve tea during cold winter weather is with lemon and honey. It serves as a powerful symbol of warmth and recovery. Conversely, large cities have cultivated a legendary and sophisticated coffee culture. Today, thriving modern coffee shops are ubiquitous, and ordering an espresso or a cappuccino is an established everyday urban routine.

### Діалог у кафе

Ось як ці граматичні правила працюють у реальному житті. Ось затишне сучасне кафе. Ви замовляєте напої.

Let us look closely at how these grammatical rules actually work in real life. Imagine a cozy and modern local cafe. You order drinks.

**Офіціант:** Добрий день! Що ви хо́чете пи́ти? (Good day! What do you want to drink?)
**Ви:** Добрий день. Я хо́чу ка́ву і молоко́. (Good day. I want coffee and milk.)
**Офіціант:** Гаря́чу чи холо́дну ка́ву? (Hot or cold coffee?)
**Ви:** Гаря́чу ка́ву. І ще я хо́чу вод**у́**. (Hot coffee. And also I want water.)
**Офіціант:** Добре, хвили́нку. (Good, one minute.)

Pay close attention to how the customer flawlessly uses the accusative case for both requested drinks. Furthermore, notice the descriptive adjectives. When the attentive waiter asks about the temperature, the adjective itself impressively shifts to match the feminine accusative form. This simple dialogue beautifully represents the exact standard of conversational fluency you are actively aiming for.


        ## File Path

        `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/food-vocabulary.md`

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
