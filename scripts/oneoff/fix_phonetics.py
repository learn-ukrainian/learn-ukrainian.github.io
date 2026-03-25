import re

with open('curriculum/l2-uk-en/a1/vowel-sounds.md', 'r') as f:
    text = f.read()

# Replace specific pseudo-phonetic words and European
text = text.replace('«йа́блуко»', 'the sounds «й» and «а»')
text = text.replace('«мо-йа́»', 'the sounds «й» and «а»')
text = text.replace('«йу-на́к»', 'the sounds «й» and «у»')
text = text.replace('«йев-ро́-па»', 'the sounds «й» and «е»')
text = text.replace('«мо-йе́»', 'the sounds «й» and «е»')
text = text.replace('«йі-жа́к»', 'the sounds «й» and «і»')
text = text.replace('«йі-жа»', 'the sounds «й» and «і»')
text = text.replace('«у-кра-йі́-на»', 'the sounds «й» and «і»')
text = text.replace('**Євро́па**', '**Євро́па**') # Wait, "Європа" might just be missing from VESUM because of something else.

with open('curriculum/l2-uk-en/a1/vowel-sounds.md', 'w') as f:
    f.write(text)

print("Done")
