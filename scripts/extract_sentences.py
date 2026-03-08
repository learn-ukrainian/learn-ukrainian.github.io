import re

with open('curriculum/l2-uk-en/a2/audit/hobbies-leisure-audit.md') as f:
    audit = f.read()

with open('curriculum/l2-uk-en/a2/hobbies-leisure.md') as f:
    text = f.read()

prefixes = re.findall(r"First 5 words: '(.*?)'", audit)

# Split text into sentences roughly
sentences = re.split(r'(?<=[.!?])\s+', text)

for prefix in prefixes:
    prefix_clean = prefix.replace('...', '').strip()
    prefix_words = prefix_clean.split()
    if len(prefix_words) < 2:
        continue

    found = False
    for s in sentences:
        s_clean = s.replace('\n', ' ').strip()
        # Create a loose regex for the prefix to handle punctuation
        pattern = r'^' + r'\s*'.join([re.escape(w) for w in prefix_words])
        if re.search(pattern, s_clean, re.IGNORECASE):
            print(f"PREFIX: {prefix}")
            print(f"FULL: {s_clean}\n")
            found = True
            break
    if not found:
        print(f"NOT FOUND: {prefix}\n")

