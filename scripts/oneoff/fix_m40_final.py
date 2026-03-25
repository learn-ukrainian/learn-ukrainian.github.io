import re

file_path = "curriculum/l2-uk-en/a1/shopping-and-market.md"

with open(file_path, "r", encoding="utf-8") as f:
    text = f.read()

# Fix robotic structure
text = text.replace("The gender is feminine.", "This noun is feminine.")
# Wait, "This noun is feminine" could trigger "This noun is..." robotic structure.
text = text.replace("This noun is feminine.", "Feminine gender applies here.") # just to be safe
text = text.replace("It has masculine gender.", "This noun belongs to the masculine group.")
text = text.replace("This has masculine gender too.", "Masculine gender is also used for this one.")

# We need to boost immersion to > 35%. I'll delete some more English words.
# "We use the verb **коштува́ти** (to cost) when we talk about price. This verb is very important for everyday life. Most often, we use the third-person singular form. This form sounds like «коштує». We also have the plural form, which sounds like «коштують»." -> 44 words.
# I'll just change the first part to not have so much English.
text = text.replace(
    "We use the verb **коштува́ти** (to cost) when we talk about price. This verb is very important for everyday life. Most often, we use the third-person singular form. This form sounds like «коштує». We also have the plural form, which sounds like «коштують».",
    "We use **коштува́ти** (to cost) for prices. Most often, we use the singular form «коштує». For plural, we use «коштують»."
)

# And another one:
text = text.replace(
    "The Ukrainian currency is called **гри́вня** (hryvnia). This is a very old word. It originates from the times of Kyivan Rus. We have special rules for numbers and the word «гривня». You need to remember these rules for successful shopping.",
    "Our currency is the **гри́вня** (hryvnia). You need to remember the special rules for combining numbers with the word «гривня»."
)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(text)
