import re

with open("curriculum/l2-uk-en/a2/being-and-becoming.md", "r", encoding="utf-8") as f:
    text = f.read()

# Transliterations specifically found:
text = text.replace("Профе́сія (Nominative)", "Профе́сія")
text = text.replace("Ору́дний відмі́нок (Instrumental)", "Ору́дний відмі́нок")
text = text.replace("Перекла́д (Translation)", "Перекла́д")
text = text.replace("називни́й відмі́нок (Nominative case)", "називни́й відмі́нок")
text = text.replace("ору́дний відмі́нок (Instrumental case)", "ору́дний відмі́нок")

with open("curriculum/l2-uk-en/a2/being-and-becoming.md", "w", encoding="utf-8") as f:
    f.write(text)
