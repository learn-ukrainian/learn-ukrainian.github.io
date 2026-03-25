import re

with open("curriculum/l2-uk-en/a1/checkpoint-daily-life.md", "r", encoding="utf-8") as f:
    text = f.read()

replacements = [
    ("We will be having lunch together.", "We plan to have lunch together."),
    ("We will be going where? We will be going to work.", "Where are we going? We are going to work."),
    ("We will be having lunch in a new restaurant.", "Our lunch will be in a new restaurant."),
    ("We will write a story about a past day. This story will use the past tense. It will also describe the daily routine. We will add words about food. We will mention the weather.", 
     "Let us write a story about a past day. This story uses the past tense. It also describes the daily routine. Let us add words about food. We also mention the weather."),
    ("We will write plans for tomorrow. We will use the analytical future tense. We will again use words about the day and stores.",
     "Let us write plans for tomorrow. Let us use the analytical future tense. We again use words about the day and stores.")
]

for old, new in replacements:
    text = text.replace(old, new)

with open("curriculum/l2-uk-en/a1/checkpoint-daily-life.md", "w", encoding="utf-8") as f:
    f.write(text)

print("Fixed 'we will' sentences.")
