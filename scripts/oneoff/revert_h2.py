file_path = "curriculum/l2-uk-en/a1/the-living-verb-i.md"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("## Розповіді (Stories)\n\n### Міні-розповідь (Mini-Story)", "### Міні-розповідь (Mini-Story)")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
