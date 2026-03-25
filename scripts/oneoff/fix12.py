import re

filepath = "/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/describing-things-adjectives.md"

with open(filepath, "r", encoding="utf-8") as f:
    text = f.read()

# Fix Robotic structure 'English: We...'
text = text.replace("English: We see new houses.", "English: Look at these new houses.")
text = text.replace("English: We see new students. (Originally masculine)", "English: These are new students. (Originally masculine)")
text = text.replace("English: We see new books. (Originally feminine)", "English: Here are new books. (Originally feminine)")
text = text.replace("English: We see beautiful days.", "English: What beautiful days.")
text = text.replace("English: We see beautiful girls.", "English: Notice the beautiful girls.")

# Boost Immersion even more by reducing long English explanations

# The English "To find out what something is physically or abstractly like..." paragraph is about 40 words.
text = text.replace("To find out what something is physically or abstractly like, you need to ask the right question. Because of the strict rules of agreement, even the question word meaning "what kind of" changes its grammatical ending to match the target noun. We use four distinct variations of this vital question.", "")

# "Memorizing these four specific question words..."
text = text.replace("Memorizing these four specific question words is incredibly useful and highly recommended for every beginner. They effectively give you the exact ending you need for your answer. If the question naturally uses «який», your descriptive adjective will likely end with those exact same sounds. This structural echoing creates a predictable, reliable, and highly systematic foundation for building sentences.", "")

# "Built in the early eleventh century..."
text = text.replace("Built in the early eleventh century, St. Sophia's Cathedral stands as a magnificent, breathtaking testament to early Ukrainian history and architectural brilliance. It is a stunning, monumental structure that strictly requires rich, vivid descriptive vocabulary to truly capture its spiritual essence. When you stand in front of this cathedral, you naturally need descriptive words like "old," "grand," and "beautiful" to express your admiration for its golden domes and ancient mosaics.", "St. Sophia's Cathedral is a magnificent testament to early Ukrainian history and architectural brilliance.")

# "By consciously using masculine adjectives..."
text = text.replace("By consciously using masculine adjectives to describe this majestic masculine noun («собор»), you are actively engaging in authentic Ukrainian expression. You are connecting directly with the physical reality of Ukraine's capital city using the precise grammatical structures that native speakers use every single day.", "")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(text)

print("Done")