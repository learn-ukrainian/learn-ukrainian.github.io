import re

file_path = "curriculum/l2-uk-en/a2/being-and-becoming.md"
with open(file_path, "r", encoding="utf-8") as f:
    text = f.read()

# 1. Add 'Наприклад:' / 'Порівняйте:' before example blocks
text = text.replace("Look at these present tense examples of identity (Наприклад / For example):", "Look at these present tense examples of identity.\n\n**Наприклад** (For example):")
text = text.replace("Let us look at some pairs in the Nominative case (Наприклад):", "Let us look at some pairs in the Nominative case.\n\n**Наприклад** (For example):")
text = text.replace("Here are more transformation examples to reinforce your learning (Порівняйте):", "Here are more transformation examples to reinforce your learning.\n\n**Порівняйте** (Compare):")
text = text.replace("Look at these corrections to avoid the Gender Mismatch error (Порівняйте):", "Look at these corrections to avoid the Gender Mismatch error.\n\n**Порівняйте** (Compare):")

# 2. Add Ukrainian dialogues and readings to increase immersion

dialogue_intro = """
> **(На співбесіді / At a job interview)**
> — Добрий день! Хто ви за професією?
> — Добрий день! Я економіст.
> — А ким ви хочете стати в нашій компанії?
> — Я хочу стати хорошим спеціалістом.
> — Ви працювали менеджером?
> — Так, я працював менеджером.
"""

if "На співбесіді" not in text:
    text = text.replace("## Вступ\n", f"## Вступ\n\n{dialogue_intro}\n")

reading_sections = """

**Читання 1: Професії в моїй родині**

> Мене звати Максим. Зараз я працюю лікарем у великій лікарні. Це дуже складна, але цікава робота. Проте раніше я не був лікарем. П'ять років тому я був звичайним студентом. 
> 
> Моя старша сестра Анна працює юристкою. Вона дуже любить свою професію і завжди хотіла працювати в суді. А наш молодший брат ще вчиться у школі. Він часто каже, що хоче стати директором або успішним айтівцем. 
> 
> Наші батьки теж мають цікаві професії. Мій батько був інженером, а зараз він працює менеджером. Моя мати працювала вчителькою, а тепер вона стала директоркою школи. Ми всі маємо різні професії, але ми щасливі, бо робимо те, що любимо.

*(Translation: My name is Maksym. Now I work as a doctor in a big hospital. It is a very difficult but interesting job. However, earlier I was not a doctor. Five years ago I was a regular student. My older sister Anna works as a lawyer. She really loves her profession and always wanted to work in court. And our younger brother is still studying at school. He often says that he wants to become a director or a successful IT professional. Our parents also have interesting professions. My father was an engineer, and now he works as a manager. My mother worked as a teacher, and now she has become a school principal. We all have different professions, but we are happy because we do what we love.)*

**Читання 2: Історія Олени**

> Олена — молода та енергійна спеціалістка. Вона мешкає в Києві. Раніше вона багато вчилася і вивчала економіку в університеті. Після університету вона працювала економісткою в банку. 
> 
> Але потім Олена вирішила змінити професію. Вона почала активно вивчати програмування. Це було складно, але дуже цікаво. Через рік Олена почала працювати програмісткою. 
> 
> Зараз вона працює айтівкою у великій міжнародній компанії. Вона дуже задоволена своїм вибором. Її чоловік теж змінив професію. Раніше він був інженером, а зараз він працює проєктним менеджером. Вони обидва мріють стати успішними директорами у майбутньому.

*(Translation: Olena is a young and energetic specialist. She lives in Kyiv. Previously she studied a lot and studied economics at the university. After university, she worked as an economist in a bank. But then Olena decided to change her profession. She started actively studying programming. It was difficult but very interesting. A year later, Olena started working as a programmer. Now she works as an IT professional in a large international company. She is very satisfied with her choice. Her husband also changed his profession. Previously he was an engineer, and now he works as a project manager. They both dream of becoming successful directors in the future.)*

**Читання 3: Робота у школі та мрії про майбутнє**

> Мій найкращий друг працює вчителем у школі. Він дуже любить свою роботу і своїх учнів. Його дружина також працює в цій школі. Вона працює директоркою. Вони часто говорять про роботу вдома. 
> 
> Їхній старший син зараз є студентом. Він вивчає журналістику в університеті, тому що хоче стати відомим журналістом. Він часто каже: "Я буду журналістом, бо мені дуже подобається писати статті про культуру". 
> 
> А їхня молодша донька хоче стати лікаркою. Вона каже: "Я буду лікаркою, щоб допомагати людям бути здоровими". Її батьки кажуть: "Ти будеш чудовою лікаркою!"

*(Translation: My best friend works as a teacher at a school. He really loves his job and his students. His wife also works at this school. She works as a principal. They often talk about work at home. Their older son is currently a student. He is studying journalism at the university because he wants to become a famous journalist. He often says: "I will be a journalist because I really like writing articles about culture." And their younger daughter wants to become a doctor. She says: "I will be a doctor to help people be healthy." Her parents say: "You will be a wonderful doctor!")*

"""

if "Читання 1" not in text:
    text = text.replace("path of being and becoming.\n\n---", f"path of being and becoming.\n{reading_sections}\n---")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(text)

