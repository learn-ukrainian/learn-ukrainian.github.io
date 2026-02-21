
lines = open('curriculum/l2-uk-en/c1/activities/31-diaspora-ukrainian.yaml').readlines()
new_lines = []
for i, line in enumerate(lines):
    new_lines.append(line)
    # Check if this line is an option text
    if line.strip().startswith('- text:'):
        # Look ahead
        if i + 1 < len(lines):
            next_line = lines[i+1]
            if not next_line.strip().startswith('correct:'):
                # Calculate indentation
                indent = line[:line.find('- text:')] + '  '
                new_lines.append(f"{indent}correct: false\n")

# Add Unjumble item if needed (naive append if not present)
# Target "title: Факти про діаспору" -> "items:" -> append
# But regex/line-based is risky for append in middle.
# I will output the file and use multi_replace for unjumble item separately because it's safer.

with open('curriculum/l2-uk-en/c1/activities/31-diaspora-ukrainian.yaml', 'w') as f:
    f.writelines(new_lines)
