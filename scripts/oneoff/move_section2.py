file_path = "curriculum/l2-uk-en/a1/the-living-verb-i.md"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

start_idx = content.find("### Everyday Action Phrases")
end_idx = content.find("### Міні-розповідь (Mini-Story)")

if start_idx != -1 and end_idx != -1:
    section = content[start_idx:end_idx]
    content = content[:start_idx] + content[end_idx:]
    
    target = "This predictable system will allow you to quickly expand your vocabulary.\n\n"
    if target in content:
        content = content.replace(target, target + section)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("Moved")
    else:
        print("Target not found")
else:
    print("Indices not found")
