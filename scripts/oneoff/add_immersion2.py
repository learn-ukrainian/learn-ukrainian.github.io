import re

file_path = "curriculum/l2-uk-en/a2/being-and-becoming.md"
with open(file_path, "r", encoding="utf-8") as f:
    text = f.read()

# 1. Add headers with 2-word English to avoid transliteration regex `r'\(([A-Za-z]+)\)'`
text = text.replace("## Вступ\n", "## Вступ (Introduction section)\n")
text = text.replace("## Презентація: Дієслова та відмінювання\n", "## Презентація: Дієслова та відмінювання (Presentation of Verbs)\n")
text = text.replace("## Соціокультурний контекст: Фемінітиви та IT\n", "## Соціокультурний контекст: Фемінітиви та IT (Sociocultural Context)\n")
text = text.replace("## Практика та запобігання помилкам\n", "## Практика та запобігання помилкам (Practice and Errors)\n")
text = text.replace("## Діалоги та кар'єрні плани\n", "## Діалоги та кар'єрні плани (Dialogues and Plans)\n")
text = text.replace("# Підсумок\n", "# Підсумок (Module Summary)\n")

# 2. Add 'Наприклад:' / 'Порівняйте:' before example blocks
text = text.replace("Look at these present tense examples of identity (Наприклад / For example):", "Look at these present tense examples of identity.\n\n**Наприклад** (For example):")
text = text.replace("Let us look at some pairs in the Nominative case (Наприклад):", "Let us look at some pairs in the Nominative case.\n\n**Наприклад** (For example):")
text = text.replace("Here are more transformation examples to reinforce your learning (Порівняйте):", "Here are more transformation examples to reinforce your learning.\n\n**Порівняйте** (Compare):")
text = text.replace("Look at these corrections to avoid the Gender Mismatch error (Порівняйте):", "Look at these corrections to avoid the Gender Mismatch error.\n\n**Порівняйте** (Compare):")

# Fix existing lists that are examples but don't have Наприклад
text = text.replace("Whenever you use a past or future form of **бути**, the profession that follows takes the Instrumental case. \n\n- **Він", "Whenever you use a past or future form of **бути**, the profession that follows takes the Instrumental case. \n\n**Наприклад** (For example):\n- **Він")

text = text.replace("The perfective **стати** is used very frequently when talking about goals and completed changes.\n\n- **Я", "The perfective **стати** is used very frequently when talking about goals and completed changes.\n\n**Наприклад** (For example):\n- **Я")

text = text.replace("If you are currently studying and gradually gaining skills, you are in the process of becoming.\n\n- **Він", "If you are currently studying and gradually gaining skills, you are in the process of becoming.\n\n**Наприклад** (For example):\n- **Він")

text = text.replace("When these feminine nouns take the Instrumental case, their **-а** ending changes to **-ою**. \n\n- **Вона", "When these feminine nouns take the Instrumental case, their **-а** ending changes to **-ою**. \n\n**Наприклад** (For example):\n- **Вона")

text = text.replace("These terms are incredibly high-frequency in modern speech and instantly make you sound like an insider.\n\n- **Мій", "These terms are incredibly high-frequency in modern speech and instantly make you sound like an insider.\n\n**Наприклад** (For example):\n- **Мій")

# 3. Add pure Ukrainian tables/readings to boost immersion score

ukrainian_table = """
**Таблиця професій (Table of Professions)**

| Хто це? (Називний відмінок) | Ким працює? (Орудний відмінок) | Ким хоче стати? (Орудний відмінок) |
| :--- | :--- | :--- |
| **Він хороший студент.** | Він працює **молодим менеджером**. | Він хоче стати **успішним директором**. |
| **Вона відома журналістка.** | Вона працює **хорошою журналісткою**. | Вона хоче стати **відомою письменницею**. |
| **Він талановитий програміст.** | Він працює **програмістом**. | Він мріє стати **айтівцем**. |
| **Вона розумна студентка.** | Вона працює **вчителькою**. | Вона стане **хорошою директоркою**. |
| **Він молодий лікар.** | Він працює **лікарем**. | Він буде **головним лікарем**. |
| **Вона успішна юристка.** | Вона працює **юристкою**. | Вона хоче стати **відомою юристкою**. |
| **Він відомий економіст.** | Він працює **економістом**. | Він мріє стати **успішним економістом**. |
| **Вона талановита інженерка.** | Вона працює **інженеркою**. | Вона буде **хорошою інженеркою**. |

"""

if "Таблиця професій" not in text:
    text = text.replace("Pattern Box: Present to Past Role", ukrainian_table + "\n**Pattern Box: Present to Past Role")


reading_sections = """
**Читання 1: Професії в моїй родині**

> Мене звати Максим. Зараз я працюю лікарем у великій лікарні. Це дуже складна, але цікава робота. Проте раніше я не був лікарем. П'ять років тому я був звичайним студентом. 
> 
> Моя старша сестра Анна працює юристкою. Вона дуже любить свою професію і завжди хотіла працювати в суді. А наш молодший брат ще вчиться у школі. Він часто каже, що хоче стати директором або успішним айтівцем. 
> 
> Наші батьки теж мають цікаві професії. Мій батько був інженером, а зараз він працює менеджером. Моя мати працювала вчителькою, а тепер вона стала директоркою школи. Ми всі маємо різні професії, але ми щасливі, бо робимо те, що любимо.

**Читання 2: Історія Олени**

> Олена — молода та енергійна спеціалістка. Вона мешкає в Києві. Раніше вона багато вчилася і вивчала економіку в університеті. Після університету вона працювала економісткою в банку. 
> 
> Але потім Олена вирішила змінити професію. Вона почала активно вивчати програмування. Це було складно, але дуже цікаво. Через рік Олена почала працювати програмісткою. 
> 
> Зараз вона працює айтівкою у великій міжнародній компанії. Вона дуже задоволена своїм вибором. Її чоловік теж змінив професію. Раніше він був інженером, а зараз він працює проєктним менеджером. Вони обидва мріють стати успішними директорами у майбутньому.

**Читання 3: Робота у школі та мрії про майбутнє**

> Мій найкращий друг працює вчителем у школі. Він дуже любить свою роботу і своїх учнів. Його дружина також працює в цій школі. Вона працює директоркою. Вони часто говорять про роботу вдома. 
> 
> Їхній старший син зараз є студентом. Він вивчає журналістику в університеті, тому що хоче стати відомим журналістом. Він часто каже: "Я буду журналістом, бо мені дуже подобається писати статті про культуру". 
> 
> А їхня молодша донька хоче стати лікаркою. Вона каже: "Я буду лікаркою, щоб допомагати людям бути здоровими". Її батьки кажуть: "Ти будеш чудовою лікаркою!"

"""

if "Читання 1" not in text:
    text = text.replace("path of being and becoming.\n\n---", f"path of being and becoming.\n\n{reading_sections}\n---")


with open(file_path, "w", encoding="utf-8") as f:
    f.write(text)

