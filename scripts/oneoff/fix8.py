import re

filepath = "/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/describing-things-adjectives.md"

with open(filepath, "r", encoding="utf-8") as f:
    text = f.read()

# Fix Outline issue
text = text.replace("## Вступ: Світ слів-описів", "## Вступ: Світ прикметників")

# Fix Dative 'нам'
text = text.replace("Вони допомагають нам у магазинах і на ринках.", "Ми часто використовуємо їх у магазинах і на ринках.")

# Fix Metalanguage 'однина'
text = text.replace("Однина вимагає чоловічого, жіночого або середнього роду.", "Один об'єкт вимагає чоловічого, жіночого або середнього роду.")

# Fix Redundancy in 'Більшість слів-описів належить до твердої групи.'
text = text.replace("Більшість слів-описів належить до твердої групи. Але ми також маємо елегантну м'яку групу.", "Багато таких слів мають тверду основу. Але є також елегантна м'яка група.")

# Fix Robotic structure 'English: We...'
text = text.replace("English: We see the feminine pattern clearly.", "English: Here is the feminine pattern clearly.")
text = text.replace("English: We have new friends.", "English: They are new friends.")

# Boost Immersion
text = text.replace("""The vast majority of adjectives in the Ukrainian language belong to what we confidently call the "Hard Stem" group. This simply means that the core, unchanging part of the word ends in a hard consonant sound right before the changing gender ending begins. Let us thoroughly break down these essential endings for all three singular genders and the plural form.""", "")

text = text.replace("""When you are describing a masculine noun (a noun that typically ends in a consonant), a hard stem adjective must take the specific ending «-ий». While this grammatical ending consists of two letters, it flows beautifully together as a smooth, relaxed sound at the very end of the word. This is the foundational base form you will encounter first when learning new vocabulary lists. It is the exact form you use when talking about a brother, a physical house, a formal document, or a language lesson.""", "A hard stem adjective for a masculine noun takes the ending «-ий». This is the base dictionary form.")

text = text.replace("""When you shift your descriptive focus to a feminine noun (which usually ends in «-а» or «-я»), the adjective must immediately drop its default masculine ending and adopt the feminine ending «-а». This is a very open, clear, and resonant vowel sound that carries wonderfully in spoken language.""", "For a feminine noun, the adjective takes the ending «-а». This is an open, clear vowel sound.")

text = text.replace("""Neuter nouns (those ending in «-о» or «-е») explicitly require the describing adjective to take the specific neuter ending «-е». This vowel sound is relatively short, relaxed, and sits comfortably right in the middle of the vocal tract. It is absolutely crucial not to confuse this distinct ending with the feminine «-а» or masculine «-ий» endings. Let us observe this in a short, natural dialogue.""", "Neuter nouns require the neuter ending «-е». Let us observe this in a short dialogue.")

text = text.replace("""When we formally move from describing a single object to describing multiple objects, the complex rules of the hard stem group become remarkably simple. In the plural form, all hard stem adjectives invariably take the ending «-і». This is a sharp, clear, and distinct vowel sound that instantly signifies plurality. You do not need to memorize separate plural endings for each gender; the single «-і» ending conveniently covers them all.""", "In the plural form, all hard stem adjectives take the ending «-і». You do not need separate plural endings for each gender.")

text = text.replace("""While the vast majority of adjectives strictly belong to the standard hard group, the Ukrainian language possesses a distinct, highly elegant category of adjectives formally called the "Soft Stem" group. These specific words are universally characterized by a soft, almost gliding, palatalized consonant sound right before the grammatical ending formally begins. This inherent phonetic softness strictly requires a slightly different set of vowel endings to maintain the natural, fluid flow of the spoken language.""", "")

text = text.replace("""The absolute classic and most frequently cited pedagogical example of a soft stem adjective is the word for the color blue. Because the letter «н» in the core stem is pronounced very softly (the tongue touches the roof of the mouth), the subsequent endings must fundamentally adapt to naturally accommodate this phonetic softness. Instead of using the standard hard vowels, we exclusively use soft or iotated vowels to maintain perfect phonetic harmony. The masculine singular ending becomes «-ій». The feminine singular ending becomes «-я». The neuter singular ending becomes «-є».""", "A classic example of a soft stem adjective is the word for blue. The endings use soft vowels to maintain phonetic harmony: «-ій», «-я», «-є».")


with open(filepath, "w", encoding="utf-8") as f:
    f.write(text)

print("Done")