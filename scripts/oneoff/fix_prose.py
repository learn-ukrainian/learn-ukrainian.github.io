import re

with open("curriculum/l2-uk-en/a1/the-cyrillic-code-ii.md", encoding="utf-8") as f:
    text = f.read()

# Fix the grammar violation (Уявіть, що ви) -> (Уявіть: ви)
text = text.replace("Уявіть, що ви в Україні", "Уявіть: ви в Україні")

# Remove inline translations in parentheses that I added
replacements = {
    r" \((Welcome to the next major stage)\)": r". \g<1>",
    r" \((Let us start with a quick review)\)": r". \g<1>",
    r" \((In this module)\)": r". \g<1>",
    r" \((We are adding)\)": r". \g<1>",
    r" \((Let's look at some examples)\)": r". \g<1>",
    r" \((Watch this video guide)\)": r". \g<1>",
    r" \((Let's practice)\)": r". \g<1>",
    r" \((Now we encounter)\)": r". \g<1>",
    r" \((We return)\)": r". \g<1>",
    r" \((Finally, we have)\)": r". \g<1>",
    r" \((You now know)\)": r". \g<1>",
    r" \((Let's explore)\)": r". \g<1>",
    r" \((For practice)\)": r". \g<1>",
    r" \((Check yourself)\)": r" - \g<1>",
    r" \((In the next module)\)": r". \g<1>",
    r" \((Watch how the lips form a distinct smile)\)": r". \g<1>",
    r" \((Here is the video demonstration)\)": r". \g<1>",
    r" \((Here is the video guide)\)": r". \g<1>",
    r" \((Watch the pronunciation guide here)\)": r". \g<1>",
    r" \((Watch the video for the exact articulation)\)": r". \g<1>",
    r" \((Watch the explanation here)\)": r". \g<1>",
    r" \((Let's combine some food vocabulary)\)": r". \g<1>",
    r" \((Let's look at common beverages)\)": r". \g<1>",
    r" \((Let's build a phrase)\)": r". \g<1>",
    r" \((Now you can read)\)": r". \g<1>",
    r" \((Imagine you are in Ukraine)\)": r". \g<1>",
    r" \((We begin)\)": r". \g<1>"
}

for pattern, replacement in replacements.items():
    text = re.sub(pattern, replacement, text)

# Just to be safe, find any remaining translations in parentheses that start with English words
text = re.sub(r" \(([A-Z][a-zA-Z\s,']+)\)", r". \1", text)

with open("curriculum/l2-uk-en/a1/the-cyrillic-code-ii.md", "w", encoding="utf-8") as f:
    f.write(text)
