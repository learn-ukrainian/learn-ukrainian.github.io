import sys
from pathlib import Path
from scripts.audit.checks.content_gaming import extract_words_from_activities, smart_vocabulary_match, extract_ukrainian_words, load_module_vocabulary

md_path = Path("curriculum/l2-uk-en/a1/checkpoint-sentences.md")
content = md_path.read_text(encoding="utf-8")
vocab = load_module_vocabulary(md_path)
content_words = extract_ukrainian_words(content)
activity_words = extract_words_from_activities(md_path)
all_used_words = content_words | activity_words

for lemma in vocab:
    if ' ' in lemma:
        phrase_words = [w for w in lemma.lower().split() if len(w) > 2]
        matched = all(smart_vocabulary_match(pw, all_used_words)[0] for pw in phrase_words)
        print(f"Phrase '{lemma}' matched: {matched}")
    else:
        matched, _ = smart_vocabulary_match(lemma, all_used_words)
        print(f"Word '{lemma}' matched: {matched}")
