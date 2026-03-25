import re

with open("curriculum/l2-uk-en/a2/being-and-becoming.md", "r") as f:
    content = f.read()

content = content.replace(
    "— Вона була вчителькою минулого року. Тепер вона стала директоркою школи.",
    "— Минулого року вона працювала вчителькою. Тепер вона працює директоркою школи."
)

content = content.replace(
    "* **Вона раніше була журналісткою, а тепер працює менеджеркою.**",
    "* **Раніше вона працювала журналісткою, а тепер працює менеджеркою.**"
)

content = content.replace(
    "Для цієї функції українська мова використовує Instrumental case.",
    "Українська мова використовує Instrumental case для цієї функції."
)

with open("curriculum/l2-uk-en/a2/being-and-becoming.md", "w") as f:
    f.write(content)
