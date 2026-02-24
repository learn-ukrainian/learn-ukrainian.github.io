import re

with open("curriculum/l2-uk-en/b1/conditionals-mixed-complex.md", "r", encoding="utf-8") as f:
    text = f.read()

sentences = re.split(r'(?<=[.!?])\s+', text)
for s in sentences:
    words = [w for w in s.split() if w.strip()]
    if len(words) >= 30:
        print(f"Len: {len(words)} | {' '.join(words[:15])}...")
