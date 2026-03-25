import re

with open("curriculum/l2-uk-en/a1/the-cyrillic-code-ii.md", "r", encoding="utf-8") as f:
    text = f.read()

# Fix the grammar violation (Уявіть, що ви) -> (Уявіть: ви)
text = text.replace("Уявіть, що ви в Україні", "Уявіть: ви в Україні")

# Remove inline translations in parentheses that I added
replacements = {
    r" \((Welcome to the next major stage)\)": ". \g<1>",
    r" \((Let us start with a quick review)\)": ". \g<1>",
    r" \((In this module)\)": ". \g<1>",
    r" \((We are adding)\)": ". \g<1>",
    r" \((Let's look at some examples)\)": ". \g<1>",
    r" \((Watch this video guide)\)": ". \g<1>",
    r" \((Let's practice)\)": ". \g<1>",
    r" \((Now we encounter)\)": ". \g<1>",
    r" \((We return)\)": ". \g<1>",
    r" \((Finally, we have)\)": ". \g<1>",
    r" \((You now know)\)": ". \g<1>",
    r" \((Let's explore)\)": ". \g<1>",
    r" \((For practice)\)": ". \g<1>",
    r" \((Check yourself)\)": " - \g<1>",
    r" \((In the next module)\)": ". \g<1>",
    r" \((Watch how the lips form a distinct smile)\)": ". \g<1>",
    r" \((Here is the video demonstration)\)": ". \g<1>",
    r" \((Here is the video guide)\)": ". \g<1>",
    r" \((Watch the pronunciation guide here)\)": ". \g<1>",
    r" \((Watch the video for the exact articulation)\)": ". \g<1>",
    r" \((Watch the explanation here)\)": ". \g<1>",
    r" \((Let's combine some food vocabulary)\)": ". \g<1>",
    r" \((Let's look at common beverages)\)": ". \g<1>",
    r" \((Let's build a phrase)\)": ". \g<1>",
    r" \((Now you can read)\)": ". \g<1>",
    r" \((Imagine you are in Ukraine)\)": ". \g<1>",
    r" \((We begin)\)": ". \g<1>"
}

for pattern, replacement in replacements.items():
    text = re.sub(pattern, replacement, text)

# Just to be safe, find any remaining translations in parentheses that start with English words
text = re.sub(r" \(([A-Z][a-zA-Z\s,']+)\)", r". \1", text)

with open("curriculum/l2-uk-en/a1/the-cyrillic-code-ii.md", "w", encoding="utf-8") as f:
    f.write(text)
