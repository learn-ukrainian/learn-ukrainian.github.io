import re

with open('curriculum/l2-uk-en/a2/being-and-becoming.md', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix errors
text = text.replace('Він став успішним айтівцем.', 'Він став хорошим айтівцем.')
text = text.replace('Вона була студенткою, а зараз дуже хороша спеціалістка.', 'Вона тоді була студенткою, а зараз дуже хороша спеціалістка.')
text = text.replace('Раніше я була студенткою, а зараз я успішна спеціалістка.', 'Раніше я вчилася і була студенткою, а зараз я успішна спеціалістка.')
text = text.replace('тепер вона стала директоркою школи.', 'тепер вона працює директоркою школи.')
text = text.replace('Вона дуже задоволена своїм вибором.', 'Вона дуже задоволена цим вибором.')
text = text.replace('Я впевнений, що ми будемо хорошими спеціалістами.', 'Я знаю, що ми будемо хорошими спеціалістами.')
text = text.replace('Вона була лікаркою, а зараз працює менеджеркою.', 'Вона працювала лікаркою, а зараз працює менеджеркою.')

# Add Immersion words to Вступ
vstup_list = """- **Я економіст.** — I am an economist.
- **Він спеціаліст.** — He is a specialist.
- **Вона лікарка.** — She is a doctor.
- **Ми студенти.** — We are students."""
vstup_list_new = vstup_list + """
- **Ти програміст.** — You are a programmer.
- **Ви інженери.** — You are engineers.
- **Вони юристи.** — They are lawyers.
- **Я журналістка.** — I am a journalist.
- **Вона вчителька.** — She is a teacher.
- **Він студент.** — He is a student.
- **Ми лікарі.** — We are doctors."""
text = text.replace(vstup_list, vstup_list_new)

# Add Immersion words to Презентація
pres_list = """- **Він був студентом.** — He was a student.
- **Ми були студентами.** — We were students.
- **Я буду інженером.** — I will be an engineer.
- **Вони будуть лікарями.** — They will be doctors."""
pres_list_new = pres_list + """
- **Я була лікаркою.** — I was a doctor.
- **Ти був журналістом.** — You were a journalist.
- **Вона буде вчителькою.** — She will be a teacher.
- **Ви будете менеджерами.** — You will be managers.
- **Ми були програмістами.** — We were programmers.
- **Він буде юристом.** — He will be a lawyer.
- **Вони були економістами.** — They were economists."""
text = text.replace(pres_list, pres_list_new)

# Add Immersion words to Соціокультурний контекст
socio_list = """- **Вона працює лікаркою.** — She works as a doctor.
- **Вона буде чудовою вчителькою.** — She will be a wonderful teacher.
- **Вона хоче стати менеджеркою.** — She wants to become a manager."""
socio_list_new = socio_list + """
- **Моя сестра працює журналісткою.** — My sister works as a journalist.
- **Її мама була директоркою школи.** — Her mother was a school director.
- **Ця дівчина хоче стати юристкою.** — This girl wants to become a lawyer.
- **Вона мріє працювати економісткою.** — She dreams of working as an economist.
- **Наша нова сусідка працює айтівкою.** — Our new neighbor works as an IT professional.
- **Моя подруга стала успішною програмісткою.** — My friend became a successful programmer.
- **Вона працювала інженеркою.** — She worked as an engineer."""
text = text.replace(socio_list, socio_list_new)

# Add Immersion words to Практика
pract_list = """- **Він айтівець.** → **Він працював айтівцем.**
- **Вона айтівка.** → **Вона працювала айтівкою.**
- **Він економіст.** → **Він буде економістом.**
- **Вона економістка.** → **Вона буде економісткою.**"""
pract_list_new = pract_list + """
- **Він юрист.** → **Він хоче стати юристом.**
- **Вона юристка.** → **Вона хоче стати юристкою.**
- **Він лікар.** → **Він мріє бути лікарем.**
- **Вона лікарка.** → **Вона мріє бути лікаркою.**
- **Він програміст.** → **Він працює програмістом.**
- **Вона програмістка.** → **Вона працює програмісткою.**
- **Він вчитель.** → **Він був вчителем.**
- **Вона вчителька.** → **Вона була вчителькою.**"""
text = text.replace(pract_list, pract_list_new)

with open('curriculum/l2-uk-en/a2/being-and-becoming.md', 'w', encoding='utf-8') as f:
    f.write(text)
