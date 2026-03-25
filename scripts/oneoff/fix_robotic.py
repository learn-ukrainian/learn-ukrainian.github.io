import re

with open("curriculum/l2-uk-en/a1/colors-and-clothing.md", "r", encoding="utf-8") as f:
    text = f.read()

replacements = [
    ("Here is the white color.", "Look at the white color."),
    ("Here is the red color.", "This is the red color."),
    ("Here is the blue color.", "Check out the blue color."),
    ("Here is the yellow color.", "We have the yellow color."),
    ("Here is the grey color.", "Now the grey color."),
    ("Here is a black table.", "This is a black table."),
    ("Here is a black window.", "Look at a black window."),
    ("Here is a blue notebook.", "This is a blue notebook."),
    ("Here are the new words.", "These are the new words."),
    ("Here is a dress.", "This is a dress."),
    ("Here is a sweater.", "Look at a sweater."),
    ("Here is a white shirt.", "This is a white shirt."),
    ("Here are pants.", "These are pants."),
    ("Here are glasses.", "Look at glasses."),
    ("Here are black pants.", "These are black pants.")
]

for old, new in replacements:
    text = text.replace(old, new)

with open("curriculum/l2-uk-en/a1/colors-and-clothing.md", "w", encoding="utf-8") as f:
    f.write(text)

print("Fixed robotic structure.")
