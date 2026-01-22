import re
import sys

file_path = 'curriculum/l2-uk-en/b2-hist/olha-sviatoslav.md'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Parse all H1/H2/H3 headers and their content into a list
sections = []
current_header = "START"
current_content = []

for line in content.split('\n'):
    if re.match(r'^#{1,3} ', line):
        if current_content:
            sections.append((current_header, '\n'.join(current_content)))
        current_header = line.strip()
        current_content = []
    else:
        current_content.append(line)
if current_content:
    sections.append((current_header, '\n'.join(current_content)))

# Now categorize sections
intro_blocks = []
analysis_blocks = []
summary_block = None
practice_block = None

for header, text in sections:
    if header == "START":
        intro_blocks.append((header, text))
    elif header == "# Підсумок":
        summary_block = (header, text)
    elif header == "## Потрібно більше практики?":
        practice_block = (header, text)
    elif header.startswith("### "):
        # List of Analysis headers to move:
        analysis_titles = [
            "Глибший аналіз реформ Ольги",
            "Святослав: Портрет лицаря Степу",
            "Хозарія: Знищення буфера",
            "Балканська епопея: Амбіція і катастрофа",
            "Загибель: Уроки для нащадків", 
            "Жінки у політиці Русі: Феномен Ольги",
            "Ольга і Святослав: Два шляхи розвитку України",
            "Спадщина для нащадків",
            "Уроки для сучасності",
            "Економіка епохи Ольги та Святослава",
            "Християнство і язичництво",
            "Життя звичайних людей",
            "Жінки в суспільстві",
            "Військова культура",
            "Завершення епохи",
            "Археологічні свідчення епохи"
        ]
        
        is_analysis = False
        for title in analysis_titles:
            if title in header:
                is_analysis = True
                break
        
        if is_analysis:
            analysis_blocks.append((header, text))
        else:
            intro_blocks.append((header, text))
    else:
        intro_blocks.append((header, text))

# Reassemble
new_content = ""

# 1. Intro/Decol
for h, t in intro_blocks:
    if h != "START":
        new_content += f"\n\n{h}\n"
    new_content += t

# 2. Analysis
for h, t in analysis_blocks:
    new_content += f"\n\n{h}\n"
    new_content += t

# 3. Summary
if summary_block:
    h, t = summary_block
    new_content += f"\n\n{h}\n"
    new_content += t

# 4. Practice
if practice_block:
    h, t = practice_block
    new_content += f"\n\n{h}\n"
    new_content += t

# Write back
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content.strip() + '\n')

print("Successfully reordered M10 content.")