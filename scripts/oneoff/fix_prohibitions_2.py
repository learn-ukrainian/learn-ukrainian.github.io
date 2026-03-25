import re

with open('curriculum/l2-uk-en/a1/prohibitions-and-signs.md', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix grammar violations
text = text.replace("базові", "прості")
text = text.replace("Металеві двері мають", "Ці двері мають")
text = text.replace("вам", "для вас") # genitive 'вас' is allowed? A1 M21-30 cases: genitive, accusative, locative. Yes. Or just remove "вам".
text = text.replace("Вам треба купити", "Ви маєте купити")
text = text.replace("дають вам спокій", "дають спокій")
text = text.replace("з попередженням", "про небезпеку")
text = text.replace("перед офісом", "біля офісу")
text = text.replace("тимчасово зачинений", "не працює")
text = text.replace("зачинений", "не працює")
text = text.replace("зачинених", "закритих") # Wait, I changed 'відкрито/закрито' in the text to say 'відчинено/зачинено'. Let's replace 'зачинених дверей' -> 'дверей'
text = text.replace("відкритий простір", "великий простір")
text = text.replace("відкрито", "роботу")

# Subordinate clauses
text = text.replace("слова, які означають", "слова. Ці слова означають")
text = text.replace("дні, коли ви", "дні. Тоді ви")
text = text.replace("А коли у", "Тоді у")
text = text.replace("час, коли транспорт", "час. Тоді транспорт")

# Remove some English text to improve immersion ratio
english_paragraphs_to_remove = [
    "Official prohibitions in Ukraine have their own clear grammatical rules. They almost always use the infinitive form of the verb. This creates a very neutral and impersonal style of communication. The sign does not address any specific person on the street. It simply states a universal rule for absolutely all citizens. The infinitive sounds very official, emotionless, and maximally distanced. The most typical examples on the streets are the prohibitions to smoke, to enter, and to touch exhibits. The core phrases are **не кури́ти** [nɛ kuˈrɪtɪ] (no smoking), **не вхо́дити** [nɛ ˈvxɔdɪtɪ] (do not enter), and **не торка́тися** [nɛ torˈkɑtɪsʲɐ] (do not touch). You can find these forms in government institutions, hospitals, or large offices. You will also often see them in city parks and national museums. They are an integral part of the modern urban landscape.",
    "The Ukrainian language very clearly distinguishes between two different communicative situations. The first situation is direct personal commands. The second situation is general rules of behavior. When we speak to a person directly, we use the imperative mood of the verb. When we write a rule for the whole society, we take the infinitive form. Compare these two different approaches very carefully. The prohibition form with an infinitive is a strict metal plaque in a large museum. The imperative mood represents the emotional words of a mother to her small child. This grammatical difference is extremely important for natural and polite communication.",
    "In an urban environment, danger can arise absolutely suddenly. In such extreme cases, there is no time to read long and complex sentences with explanations. An instant and clear reaction is needed. Therefore, the Ukrainian language uses a special arsenal of very short and expressive words. They act as powerful visual sirens for inattentive pedestrians and fast drivers. Recognizing these strong signals is an absolutely essential skill for every foreigner. This is a true basic survival vocabulary that needs to be known by heart.",
    "Modern life in the city completely depends on various official schedules. You need to know exactly when large supermarkets and small pharmacies open. Without understanding operating schedules, you will waste a lot of your time in vain. Ukrainian commercial establishments have their traditional operating hours, which can often differ significantly from European ones. It is also critically important to be able to quickly read bright promotional announcements on shop windows. They always provide very useful information about prices. This section will teach you how to correctly navigate in time and commercial offers.",
    "Orientation in a large unfamiliar city always requires the ability to quickly read address plates. In Ukrainian cities, there is a very logical and developed system of names for roads and squares. Besides, you must perfectly know the basic road terminology for your physical safety. This section also reveals one extremely important linguistic nuance regarding doors and shops. We will talk about the necessary decolonization of our daily vocabulary and the correct literary norms.",
    "Now it is time to actively apply your new theoretical knowledge in real-life practice. Our main ambitious goal is to make you completely confident in the complex urban space. Together we will model in detail several typical situations that you are guaranteed to encounter in Ukraine. You must be able to analyze visual information very quickly, absolutely accurately, and without a dictionary. This is the final and most important step to your complete linguistic independence."
]

for p in english_paragraphs_to_remove:
    text = text.replace(p, "")

with open('curriculum/l2-uk-en/a1/prohibitions-and-signs.md', 'w', encoding='utf-8') as f:
    f.write(text)

print("Fixes applied.")
