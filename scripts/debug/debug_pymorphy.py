
import pymorphy2
import sys

def debug_pymorphy(words):
    morph = pymorphy2.MorphAnalyzer(lang='uk')
    
    for word in words:
        print(f"\n--- Analyzing '{word}' ---")
        parses = morph.parse(word)
        for p in parses:
            print(f"Normal Form: {p.normal_form} | Tag: {p.tag} | Score: {p.score}")
            
        if not parses:
            print("No parse found.")

if __name__ == "__main__":
    test_words = sys.argv[1:] if len(sys.argv) > 1 else ["пілота", "медсестр", "пілото", "метро", "S.T.A.L.K.E.R."]
    debug_pymorphy(test_words)
