import re

filepath = "/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/describing-things-adjectives.md"

with open(filepath, "r", encoding="utf-8") as f:
    text = f.read()

# Fix Robotic structure 'English: We...'
text = text.replace("English: We use four different questions.", "English: There are four different questions.")
text = text.replace("English: We use the short ending «-е».", "English: The short ending «-е» is standard.")
text = text.replace("English: We will learn a few important opposites.", "English: Here are a few important opposites.")
text = text.replace("English: We will speak confidently.", "English: This builds your confidence.")
text = text.replace("English: We will use our knowledge in real situations.", "English: Real situations help apply our knowledge.")

# Boost Immersion even more by reducing long English explanations

text = text.replace('In the English language, adjectives are entirely static and rigid. They never change their shape or form regardless of what specific object they describe. You say «a new car», «a new house», and «new friends», keeping the descriptive word «new» exactly the same every single time. Ukrainian grammar, however, operates on a highly dynamic and flexible principle. An adjective cannot simply stand next to a noun in isolation; it must actively match the noun it describes. This continuous matching process ensures that words in a sentence are tightly bound together in perfect harmony. You will learn to correctly recognize the noun first, then seamlessly adjust the adjective to fit it perfectly. This might feel like a series of extra steps at first, but it quickly becomes an intuitive, natural rhythm.', '')

text = text.replace('To find out what something is physically or abstractly like, you need to ask the right question. Because of the strict rules of agreement, even the question word meaning "what kind of" changes its grammatical ending to match the target noun. We use four distinct variations of this vital question.', '')

text = text.replace('Before we can even begin to choose the right adjective ending, we must know the grammatical gender of the noun. Let us briefly review the "Gender Code" from your earlier lessons (Module A1-07), as it serves as the mandatory foundation for everything we do in this current module. You cannot correctly form the adjective until you have correctly analyzed the noun.', '')

text = text.replace('Built in the early eleventh century, St. Sophia's Cathedral stands as a magnificent, breathtaking testament to early Ukrainian history and architectural brilliance. It is a stunning, monumental structure that strictly requires rich, vivid descriptive vocabulary to truly capture its spiritual essence. When you stand in front of this cathedral, you naturally need descriptive words like "old," "grand," and "beautiful" to express your admiration for its golden domes and ancient mosaics.', 'St. Sophia's Cathedral is a magnificent testament to early Ukrainian history and architecture.')

text = text.replace('By consciously using masculine adjectives to describe this majestic masculine noun («собор»), you are actively engaging in authentic Ukrainian expression. You are connecting directly with the physical reality of Ukraine's capital city using the precise grammatical structures that native speakers use every single day.', '')

text = text.replace('While vocabulary words denoting colors like «синій» are the most overwhelmingly common everyday examples, you will certainly encounter other important adjectives that strictly follow this exact same soft pattern. Several of these refer specifically to periods of time, relative location, or seasons.', 'Other soft group words refer specifically to periods of time, relative location, or seasons.')

text = text.replace('For instance, to say "early morning," you write «ра́нній ранок». To describe a "late night," you use «пі́зня ніч». An "evening newspaper" becomes a «вечі́рня газета». You can even describe "spring rain" using «весня́ний дощ». Notice very clearly how all of these different conceptual words rigidly maintain the distinct soft endings («-ій», «-я», «-є»). They behave grammatically exactly like «синій».', 'Notice how these time-related words maintain the distinct soft endings («-ій», «-я», «-є»).')

text = text.replace('To effectively practice our feminine adjectives, we consciously turn to one of the most famous and universally beloved figures in all of Ukrainian folklore and classic literature. Mavka is a mystical forest spirit, the central, defining character in Lesya Ukrainka's renowned poetic masterpiece "The Forest Song" (Лісова пісня). She profoundly represents the pure soul of nature and its eternal, untamed beauty. By reading the Ukrainian sentences above, you are actively processing feminine adjective endings («молода», «гарна», «цікава») firmly anchored to the feminine nouns «дівчина» and «історія». Concurrently, the descriptive adjective «зелений» correctly modifies the masculine noun «ліс». This is exactly how grammar serves the high art of cultural storytelling.', 'Mavka is a mystical forest spirit, the central character in Lesya Ukrainka's poetic masterpiece "The Forest Song". She represents the pure soul of nature and its eternal beauty.')

with open(filepath, "w", encoding="utf-8") as f:
    f.write(text)

print("Done")