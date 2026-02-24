import re

filepath = 'curriculum/l2-uk-en/b2/word-formation-adjective-formation.md'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

# Remove English translations in parentheses
text = text.replace(' (Kyivan)', '')
text = text.replace(' (euphony)', '')
text = text.replace(" (parental/father's committee)", "")
text = text.replace(' (autumnal)', '')
text = text.replace(' (legal, lawful)', '')
text = text.replace(' (foggy)', '')
text = text.replace(' (daily, daytime)', '')
text = text.replace(' (musical - related to music)', '')
text = text.replace(' (musical - talented/melodic)', '')
text = text.replace(' (national)', '')
text = text.replace(' (term)', '')
text = text.replace(' (blue-yellow)', '')
text = text.replace(' (bright orange)', '')
text = text.replace(' (white-faced)', '')
text = text.replace(' (numeral)', '')

# Fix euphony
text = text.replace('з суфіксом', 'із суфіксом')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
