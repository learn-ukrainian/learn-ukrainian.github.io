path = '/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/imperative-and-requests.md'
with open(path, 'r') as f:
    text = f.read()

text = text.replace('Do not ', "Don't ")

with open(path, 'w') as f:
    f.write(text)
