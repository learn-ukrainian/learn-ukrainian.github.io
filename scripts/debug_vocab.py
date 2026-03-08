with open('curriculum/l2-uk-en/a2/hobbies-leisure.md') as f:
    lines = f.readlines()

in_vocab = False
for line in lines:
    if '| Українською мовою | In English translation |' in line:
        in_vocab = True
    if in_vocab:
        print(line.strip())
        if line.strip() == '' and len(line) < 5:
            break
