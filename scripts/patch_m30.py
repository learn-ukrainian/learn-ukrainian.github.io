
lines = open('curriculum/l2-uk-en/c1/activities/30-history-of-language.yaml').readlines()
# Line 35 (Index 34)
lines[34] = "  - question: У якому саме столітті українська мова стала офіційною державною мовою діловодства та судочинства у Великому князівстві Литовському, закріпивши свій статус у Литовських статутах?\n"
# Line 346 (Index 345) - Verify if it starts with "- question: " or "  - question: "
# Using grep output: 346:  - question: ...
lines[345] = "  - question: Хто з відомих літературознавців вперше запровадив у науковий обіг термін \"Розстріляне відродження\" для позначення знищеної тоталітарним режимом української культури 1920-30-х років?\n"

with open('curriculum/l2-uk-en/c1/activities/30-history-of-language.yaml', 'w') as f:
    f.write(''.join(lines))
