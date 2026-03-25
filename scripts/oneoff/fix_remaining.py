import re

md_file = "/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-cyrillic-code-iii.md"

with open(md_file, "r") as f:
    md = f.read()

md = md.replace("* **мій друг** (my friend)", "* **та́то і друг** (dad and friend)")
md = md.replace("* **твій дім** (your house)", "* **банк і дім** (bank and house)")

with open(md_file, "w") as f:
    f.write(md)

