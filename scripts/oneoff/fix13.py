import re

filepath = "/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/describing-things-adjectives.md"

with open(filepath, "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace('''One of the most highly effective pedagogical methods to learn and permanently retain descriptive vocabulary is to actively memorize adjectives in pairs of absolute opposites. This practical strategy gives your brain a built-in logical contrast mechanism, making vocabulary recall much faster and far more reliable during a live conversation. Let us carefully examine two extremely high-frequency pairs of opposites that perfectly follow the hard stem pattern.''', '')

text = text.replace('''Now that we have deeply explored the foundational architectural rules of adjectives, it is officially time to bring them to vibrant life. Language is fundamentally a tool for describing reality, engaging with rich cultural history, and successfully managing daily routines. Let us thoroughly apply these grammatical endings to authentic Ukrainian contexts.''', '')

text = text.replace('''In Ukrainian sentence structure, descriptive adjectives can be placed directly before the noun they describe, or they can be placed entirely after the noun to state a direct, declarative fact about its condition. The truly incredible thing is that the grammatical adjective endings do not change based on their position in the sentence.''', '')

text = text.replace('''When the adjective is placed immediately before the noun, it is an attributive position. When placed entirely after the noun, usually to make a definitive statement, it is a predicative position. In present tense Ukrainian, we brilliantly and efficiently omit the verb "to be" completely. Let us compare these positions directly.''', '')

text = text.replace('''Let us shift abruptly from ancient folklore to a highly practical, fast-paced modern conversational scenario. Real estate in Ukraine is booming, and you must skillfully use descriptive adjectives to confidently sell the physical features of an apartment. We will effectively integrate vocabulary from your daily routine lessons to create a highly realistic context.''', '')

text = text.replace('''Observe closely the rapid, dynamic shifting between grammatical genders. The noun «квартира» instantly triggers «нова» and «велика». The noun «вікно» strictly requires «велике». Finally, «дім» perfectly aligns with «старий» and «дорогий». The professional agent seamlessly adjusts the adjective endings to match the constantly changing nouns in the environment.''', '')

with open(filepath, "w", encoding="utf-8") as f:
    f.write(text)

print("Done")