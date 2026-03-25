import re

with open('curriculum/l2-uk-en/a1/imperative-and-requests.md', 'r') as f:
    text = f.read()

reps = {
    "You drop the final vowel of the stem and add a short sound at the end.": "Ви відкидаєте останню голосну і додаєте новий звук. You drop the final vowel of the stem and add a short sound at the end.",
    "A teacher will use them frequently.": "Вчитель часто їх використовує. A teacher will use them frequently.",
    "They are incredibly useful for basic directions.": "Вони дуже корисні для вказівок. They are incredibly useful for basic directions.",
    "You cannot guess their imperative forms simply by looking at the інфінітив (infinitive).": "Ви не можете вгадати форму з інфінітива. You cannot guess their imperative forms simply by looking at the infinitive.",
    "They require extra practice to master completely.": "Вони потребують додаткової практики. They require extra practice to master completely.",
    "You must diligently memorize the irregular forms such as **дай**, **скажи**, and **стій**.": "Ви повинні запам'ятати ці неправильні форми. You must diligently memorize the irregular forms such as **дай**, **скажи**, and **стій**.",
    "The most common and natural-sounding position in everyday speech is immediately following дієслово (the verb).": "Найкраща позиція — після дієслова. The most common position is immediately following the verb.",
    "This straightforward structure works perfectly for both the informal **ти** commands and the formal **ви** commands.": "Ця структура працює для обох форм. This structure works perfectly for both the informal and formal commands.",
    "A printed sign prominently displayed on a museum wall might state:": "Знак на стіні музею може сказати: A printed sign on a museum wall might state:",
    "Always remember to utilize the formal **ви** command when you are speaking to strangers, to elders, or to any assembled group of people.": "Використовуйте форму «ви» для незнайомих людей та груп. Always remember to utilize the formal **ви** command when speaking to strangers or groups.",
    "Never forget to actively include **будь ласка** to properly soften your direct requests and sound respectful.": "Не забувайте казати «будь ласка». Never forget to include **будь ласка** to sound respectful.",
}

for k, v in reps.items():
    text = text.replace(k, v)

# Also let's boost some English with just Ukrainian.
text = text.replace("we use when we want to give commands, issue instructions, or make direct requests.", "we use for commands and requests.")
text = text.replace("The imperative mood is absolutely essential for effective and natural communication.", "Наказовий спосіб необхідний для спілкування. The imperative mood is essential for communication.")
text = text.replace("Constructing a clear заперечний наказ (negative command) is as straightforward as adding the word **не** directly before the imperative verb form you already know.", "Для заперечення просто додайте слово **не**. To make a negative command, just add **не**.")

with open('curriculum/l2-uk-en/a1/imperative-and-requests.md', 'w') as f:
    f.write(text)

