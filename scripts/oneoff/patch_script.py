import re

with open('scripts/audit/checks/cross_file_integrity.py', 'r') as f:
    code = f.read()

# Fix length check
code = code.replace("if len(word) > 1", "if len(word) >= 1")

# Remove specific words from exclude set
words_to_remove = ["'і'", "'в'", "'з'", "'у'", "'та'", "'мати'"]
for w in words_to_remove:
    code = code.replace(w + ", ", "")
    code = code.replace(", " + w, "")

with open('scripts/audit/checks/cross_file_integrity.py', 'w') as f:
    f.write(code)
