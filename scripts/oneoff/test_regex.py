import re

patterns = [
    r"[\(\[—–=-]",
    r"[—–=-]+"
]

for p in patterns:
    print(f"Pattern {p}:")
    try:
        r = re.compile(p)
        for char in r"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789=-><@[\]^_`":
            if r.match(char):
                print(f"  Matches: {char!r}")
    except Exception as e:
        print(f"  Error: {e}")
