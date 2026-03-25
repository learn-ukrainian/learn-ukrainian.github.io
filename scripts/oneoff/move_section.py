file_path = "curriculum/l2-uk-en/a1/the-living-verb-i.md"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Extract Everyday Action Phrases section
import re
match = re.search(r"(### Everyday Action Phrases\n\nLet's apply these verbs.*?відпочиваю\.\*\*\n\n)", content, re.DOTALL)
if match:
    section = match.group(1)
    # Remove from Practice
    content = content.replace(section, "")
    
    # Insert at the end of Presentation
    target = "This predictable system will allow you to quickly expand your vocabulary.\n\n"
    if target in content:
        content = content.replace(target, target + section)
    else:
        print("Target not found")
        
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Section moved successfully.")
else:
    print("Section not found.")
