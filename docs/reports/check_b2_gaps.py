import glob
import os

plan_dir = "curriculum/l2-uk-en/plans/b2"
files = sorted(glob.glob(os.path.join(plan_dir, "*.yaml")))

print(f"Found {len(files)} B2 plan files.")

missing_new_module = not os.path.exists(os.path.join(plan_dir, "pronoun-system-advanced.yaml"))
print(f"Missing 'pronoun-system-advanced.yaml': {missing_new_module}")

def check_expansion(filename, keywords):
    fpath = os.path.join(plan_dir, filename)
    if not os.path.exists(fpath):
        return f"File {filename} not found"
    with open(fpath, encoding="utf-8") as f:
        content = f.read().lower()
        if any(k.lower() in content for k in keywords):
            return "Expanded"
        else:
            return "Needs expansion"

print(f"numeral-declension-compound-numbers: {check_expansion('numeral-declension-compound-numbers.yaml', ['fractional', 'fraction', 'collective', 'збірн'])}")
print(f"advanced-case-semantics: {check_expansion('advanced-case-semantics.yaml', ['noun declension', 'парадигм', 'pluralia'])}")
print(f"word-formation-abstract-nouns: {check_expansion('word-formation-abstract-nouns.yaml', ['zero-suffix', 'zero suffix', 'нульов'])}")
