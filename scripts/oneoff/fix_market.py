import re

with open("curriculum/l2-uk-en/a1/at-the-market.md", "r") as f:
    text = f.read()

# 1. Replace the "Різниця між" section
text = re.sub(
    r"### Різниця між «здача» та «решта».*?(?=###|\Z)",
    """### Слово «решта» (The Word "Reshta")
Vocabulary nuance is incredibly important for avoiding daily confusion. The word "change" (money returned after a purchase) translates to **ре́шта** in pure Ukrainian. 
Слово «решта» означає гроші після покупки. Ми кажемо «без решти», коли даємо точну суму.
When you give a vendor a large banknote and they hand you smaller money back, that money is exclusively called **ре́шта**. If you have the exact correct amount, you say **без ре́шти** (without change). If you want to leave a polite tip or simply do not need the small coins back, you tell the friendly vendor **залиші́ть ре́шту собі́** (keep the change).
Ось гроші за фрукти. У мене сьогодні є сума без решти. Дуже дякую, залиште решту собі.

> [!warning] False Friends
> Avoid using the Russian word "здача" for financial transactions. Always use "решта" for the financial change.

""",
    text, flags=re.DOTALL
)

# 2. Fix Dative & Participle & Subordinate clause markers
text = text.replace("знають чудові історії", "знають цікаві історії")
text = text.replace("У столиці Києві є", "Київ — це столиця. Там є")
text = text.replace("перший критий ринок", "перший великий ринок")
text = text.replace("Якщо ви хочете зрозуміти українське місто, вам треба", "Ви хочете зрозуміти українське місто? Тоді потрібно")
text = text.replace("Тому що там висока якість", "Там висока якість")
text = text.replace(
    "Хоча в кожному місті є великі сучасні супермаркети, українці дуже люблять купувати свіжі продукти на базарі.",
    "У кожному місті є великі сучасні супермаркети. Але українці дуже люблять купувати свіжі продукти на базарі."
)

# Fix remaining "здача" instances
text = text.replace("Візьміть здачу", "Залиште решту собі")
text = text.replace("візьміть здачу", "залиште решту собі")
text = text.replace("без здачі", "без решти")

# 3. Boost immersion: translate more English into simple Ukrainian
# Let's look at "Ввічливі запити (Polite Requests)"
repl1_old = """Politeness is utterly crucial when interacting with market vendors. You should strongly avoid using direct, demanding verbs like "I want" («я хочу») because it can sound too abrupt or rude. Instead, use the polite imperative or a softer polite question format."""
repl1_new = """Ввічливість дуже важлива на ринку. (Politeness is very important at the market.) Не використовуйте слово «я хочу». (Do not use the word "I want".) Це грубо. (It is rude.) Використовуйте ввічливі слова. (Use polite words.)"""
text = text.replace(repl1_old, repl1_new)

repl2_old = """The verb **да́йте** means "give me" in the polite, formal plural form. Always pair it with **будь ласка** (please). Another extremely natural way to ask is using the word **мо́жна** (is it possible / may I). This creates a respectful and friendly tone, which is the exact foundation of a good market relationship."""
repl2_new = """Слово **да́йте** дуже ввічливе. (The word "дайте" is very polite.) Завжди кажіть **будь ласка**. (Always say "please".) Також ми часто використовуємо слово **мо́жна**. (We also often use the word "можна".) Це створює дружній тон. (This creates a friendly tone.)"""
text = text.replace(repl2_old, repl2_new)

repl3_old = """Finally, after you have selected your fresh produce, you need to know how to ask about the cost and finalize the financial transaction. There are a few key phrases that absolutely every buyer uses at the market."""
repl3_new = """Ви вибрали свіжі продукти. (You have selected fresh produce.) Тепер вам потрібно запитати про ціну. (Now you need to ask about the price.) Всі покупці використовують ці слова. (All buyers use these words.)"""
text = text.replace(repl3_old, repl3_new)

repl4_old = """The most common and useful question is **Скі́льки ко́штує?** (How much does it cost?). If you are specifically pointing to multiple items, you use the plural form **Скі́льки ко́штують?**. When the vendor has weighed everything and you are completely ready to pay the total amount, you ask **Скі́льки з ме́не?** (Literally: How much from me?)."""
repl4_new = """Головне питання — **Скі́льки ко́штує?** (The main question is "How much does it cost?"). Для багатьох речей ми кажемо **Скі́льки ко́штують?** (For many things we say "How much do they cost?"). Коли ви готові платити, запитайте **Скі́льки з ме́не?** (When you are ready to pay, ask "How much from me?")."""
text = text.replace(repl4_old, repl4_new)

with open("curriculum/l2-uk-en/a1/at-the-market.md", "w") as f:
    f.write(text)

print("Updates applied.")
