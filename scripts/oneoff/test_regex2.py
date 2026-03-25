import re

patterns = [
    r"\*\*{word}\*\*\s*[\(\[—–=-]\s*{meaning}",
    r"\b{word}\b\s*[\(\[]\s*{meaning}",
    r"\b{word}\b\s*[—–=-]+\s*{meaning}",
    r"\b{word}\b\s*[:=]\s*{meaning}",
    r"\|\s*{word}\s*\|\s*{meaning}",
]

cases = [
    ("лук (an onion)", "лук", "onion", 1),
    ("**лук** (red onion)", "лук", "onion", 0),
    ("лук — the onion", "лук", "onion", 2),
    ("| шар | a ball |", "шар", "ball", 4),
]

for text, word, meaning, p_idx in cases:
    p = patterns[p_idx].format(word=re.escape(word), meaning=re.escape(meaning))
    m = re.search(p, text)
    print(f"Text: '{text}', Pattern: '{p}' -> Match: {bool(m)}")

