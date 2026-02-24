import re

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/health-basics.md', 'r') as f:
    content = f.read()

# The engagement is failing because it looks for 
# > [!note], [!tip], [!warning], [!caution], [!important], [!cultural], [!history-bite], [!myth-buster], [!quote], [!context], [!analysis], [!source], [!legacy], [!reflection], [!fact], [!culture], [!military], [!perspective], [!biography]
# But MUST be on a new line after a paragraph. It is currently:
# [!note] **Родова гармонія**
# > Кожна...

# Wait, let's look at a working callout from another file or the original file.
# Original file had:
# [!culture] **Медицина вдома**
# > В Україні є дуже корисна традиція...

# Wait, the audit script looks for "> [!note]" not "[!note]"!!!
# Let's fix ALL callouts to be:
# > [!callout] **Header**
# > Text

content = content.replace('[!culture]', '> [!culture]')
content = content.replace('[!cultural]', '> [!cultural]')
content = content.replace('[!tip]', '> [!tip]')
content = content.replace('[!note]', '> [!note]')
content = content.replace('[!history-bite]', '> [!history-bite]')
content = content.replace('[!warning]', '> [!warning]')
content = content.replace('[!observe]', '> [!observe]')

# The current format:
# > [!note] **Родова гармонія**
# > Кожна частина тіла...
# Wait, some lines might already have > and some don't.
# Let's do a regex replacement.
content = re.sub(r'^(?!> )\[!', '> [!', content, flags=re.MULTILINE)

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/health-basics.md', 'w') as f:
    f.write(content)

