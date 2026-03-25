import re

with open("curriculum/l2-uk-en/a1/holidays-and-traditions.md", "r") as f:
    text = f.read()

# Fix Dative/Locative 'мові'
text = text.replace("В українській мові ми маємо", "Ми маємо")
text = text.replace("In the Ukrainian language, we", "We")
text = text.replace("як носій мови", "дуже гарно")
text = text.replace("like a native speaker", "very well")
text = text.replace("українською мовою.", "українською.")
text = text.replace("in the Ukrainian language.", "in Ukrainian.")

# Fix Perfective 'зробив', 'написав'
text = text.replace("Її написав український композитор", "Її писав український композитор")
text = text.replace("Микола Леонтович зробив чудову музику", "Микола Леонтович робив чудову музику")

# Fix Subordinate clauses and sentence length
text = text.replace("Ластівка — це пташка, яка прилітає навесні.", "Ластівка — це весняна пташка. Вона прилітає навесні.")
text = text.replace("A swallow is a bird that arrives in spring.", "A swallow is a spring bird. It arrives in spring.")

text = text.replace("Ми бажаємо абстрактні речі, які ми не можемо торкнутися руками.", "Ми бажаємо абстрактні речі. Ми не можемо торкнутися їх руками.")
text = text.replace("We wish for abstract things that we cannot touch with our hands.", "We wish for abstract things. We cannot touch them with our hands.")

text = text.replace("Ми використовуємо його, коли хочемо сказати, що ми когось вітаємо.", "Ми використовуємо його для привітання людей.")
text = text.replace("We use it when we want to say that we are greeting someone.", "We use it for greeting people.")

text = text.replace("Це означає, що людина буде мати багато сил і не буде хворіти.", "Людина буде мати багато сил. Вона не буде хворіти.")
text = text.replace("This means that a person will have a lot of strength and will not be sick.", "A person will have a lot of strength. They will not be sick.")

text = text.replace("Це коли все виходить добре на роботі або у школі.", "Усе виходить добре на роботі або у школі.")
text = text.replace("This is when everything goes well at work or at school.", "Everything goes well at work or at school.")

text = text.replace("Тепер ми знаємо, що всесвітньо відома пісня «Щедрик» має українське походження.", "Всесвітньо відома пісня «Щедрик» має українське походження.")
text = text.replace("Now we know that the globally famous song \"Shchedryk\" has Ukrainian origins.", "The globally famous song \"Shchedryk\" has Ukrainian origins.")

text = text.replace("Ми також кажемо їх, коли зустрічаємо друзів або колег на вулиці.", "Ми також кажемо їх друзям і колегам на вулиці.")
text = text.replace("We also say them when we meet friends or colleagues on the street.", "We also say them to friends and colleagues on the street.")

text = text.replace("Подивіться, як змінюються ці слова, коли ми робимо побажання.", "Подивіться на ці слова. Вони змінюються для побажання.")
text = text.replace("Look at how these words change when we make wishes.", "Look at these words. They change for a wish.")

text = text.replace("Коли ми маємо велике свято, ми кажемо добрі слова.", "На велике свято ми кажемо добрі слова.")
text = text.replace("When we have a big holiday, we say kind words.", "On a big holiday, we say kind words.")

text = text.replace("Коли ви даруєте подарунок, ви кажете:", "Ви даруєте подарунок і кажете:")
text = text.replace("When you give a gift, you say:", "You give a gift and you say:")

text = text.replace("Якщо ви не знаєте точну назву свята, ви можете просто сказати: «Зі святом!».", "Іноді ви не знаєте точну назву свята. Тоді ви можете просто сказати: «Зі святом!».")
text = text.replace("If you do not know the exact name of the holiday, you can simply say: «Зі святом!».", "Sometimes you do not know the exact name of the holiday. Then you can simply say: «Зі святом!».")

text = text.replace("якщо людина бажає вам багато хорошого на свято?", "після хороших побажань на свято?")
text = text.replace("if a person wishes you many good things for a holiday?", "after good wishes for a holiday?")

text = text.replace("Ми дуже пишаємося цією піснею, бо вона показує красу нашої культури.", "Ми дуже пишаємося цією піснею. Вона показує красу нашої культури.")
text = text.replace("We are very proud of this song because it shows the beauty of our culture.", "We are very proud of this song. It shows the beauty of our culture.")

text = text.replace("Кожен член родини має з'їсти хоча б трохи куті.", "Кожен член родини має з'їсти трохи куті.")
text = text.replace("Every family member must eat at least a little bit of Kutia.", "Every family member must eat a little bit of Kutia.")

text = text.replace("Щоб відповісти на це питання, ми використовуємо родовий відмінок для дати.", "Для відповіді ми використовуємо родовий відмінок.")
text = text.replace("To answer this question, we use the Genitive case for the date.", "For the answer, we use the Genitive case.")

text = text.replace("Подару́нок — це спеціальна річ, яку ми даємо іншій людині, щоб зробити її щасливою.", "Подару́нок — це спеціальна річ. Ми даємо її іншій людині для радості.")
text = text.replace("A gift is a special thing that we give to another person to make them happy.", "A gift is a special thing. We give it to another person for joy.")

# Sentence > 10 words
text = text.replace("Для побажань ми завжди використовуємо родовий відмінок і ніколи не використовуємо знахідний.", "Для побажань ми завжди використовуємо родовий відмінок. Ми ніколи не використовуємо знахідний.")
text = text.replace("For wishes, we always use the Genitive case and never use the Accusative.", "For wishes, we always use the Genitive case. We never use the Accusative.")

text = text.replace("Тепер ви можете написати чудову листівку та привітати свого друга з днем народження українською.", "Тепер ви можете написати чудову листівку. Ви можете привітати друга з днем народження.")
text = text.replace("Now you can write a wonderful greeting card and congratulate your friend on their birthday in Ukrainian.", "Now you can write a wonderful greeting card. You can congratulate your friend on their birthday.")
text = text.replace("Тепер ви можете написати чудову листівку та привітати свого друга з днем народження українською мовою.", "Тепер ви можете написати чудову листівку. Ви можете привітати друга з днем народження.")
text = text.replace("Now you can write a wonderful greeting card and congratulate your friend on their birthday in the Ukrainian language.", "Now you can write a wonderful greeting card. You can congratulate your friend on their birthday.")

# Redundancy
text = text.replace("Я вітаю тебе зі святом. Бажаю тобі великого щастя, міцного здоров'я та успіху в роботі.", "Щиро вітаю тебе! Бажаю багато радості, міцного здоров'я та світлих днів.")
text = text.replace("I congratulate you on the holiday. I wish you great happiness, strong health, and success at work.", "I sincerely congratulate you! I wish you much joy, strong health, and bright days.")
text = text.replace("Я вітаю тебе зі святом (I congratulate you on the holiday).", "Я вітаю тебе (I congratulate you).")

# Russicism: 'давайте подивимося'
text = text.replace("Давайте подивимося", "Подивімося")

# Engagement
text = text.replace("[!culture]", "[!cultural]")
text = text.replace("[!fact]", "[!note]")
text = text.replace("[!observe]", "[!note]")
text = text.replace("[!myth-buster]", "[!cultural]")

with open("curriculum/l2-uk-en/a1/holidays-and-traditions.md", "w") as f:
    f.write(text)

print("Replacement done.")
