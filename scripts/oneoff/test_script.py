import sys
import os

sys.path.append(os.getcwd())

# test words
from scripts.rag.vesum_api import verify_words
words = ["це", "сім'я", "і", "м'яч", "ранок", "вечір"]
for w in words:
    print(w, verify_words([w]))
