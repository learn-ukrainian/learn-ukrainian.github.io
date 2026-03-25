import re

filepath = "/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/describing-things-adjectives.md"

with open(filepath, "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace('''In standard daily life, especially when actively shopping in traditional open-air markets or browsing in modern stores, you will constantly need to realistically evaluate various objects based heavily on price and perceived quality. The specific adjectives "expensive" and "cheap" are absolutely essential functional tools for navigating these commercial environments. Let us safely analyze a typical conversational exchange actively comparing items.''', '')

text = text.replace('''As we definitively conclude this comprehensive presentation, let us formally synthesize the entire grammatical system into a single, highly cohesive pattern strictly based on the fundamental questions we initially learned. Your brain should rapidly follow this exact logical loop:''', '')

text = text.replace('''This underlying structural logic remains completely unbroken. By deeply internalizing this specific question-and-answer mechanism, you have successfully unlocked one of the most structurally powerful and expansively useful systems in the entire Ukrainian language.''', '')


with open(filepath, "w", encoding="utf-8") as f:
    f.write(text)

print("Done")