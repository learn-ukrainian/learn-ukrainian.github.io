import re

with open('curriculum/l2-uk-en/a1/imperative-and-requests.md', 'r') as f:
    text = f.read()

# Safe noun replacements
reps = {
    "the imperative mood": "наказовий спосіб",
    "the verb": "дієслово",
    "the infinitive": "інфінітив",
    "the informal command": "неформальний наказ",
    "the formal command": "формальний наказ",
    "a negative command": "заперечний наказ",
    "negative commands": "заперечні накази",
    "polite requests": "ввічливі прохання",
    "a polite request": "ввічливе прохання",
    "the word": "слово",
    "the rules": "правила",
    "everyday communication": "повсякденне спілкування",
    "daily life": "повсякденне життя"
}

for k, v in reps.items():
    # Only replace if not already next to its translation (to avoid duplicating)
    # Actually, a simple replace is fine since these are safe nouns taught in A1.
    pass

# We will just replace some exact English sentences with Ukrainian
# to boost immersion naturally without inline parentheses.

text = text.replace(
    "To create the informal command for **ти**, we remove the інфінітив (infinitive) ending from дієслово (the verb) stem and add a specific imperative suffix.",
    "Як утворити неформальний наказ (informal command)? We remove the інфінітив (infinitive) ending from дієслово (the verb) stem and add a specific imperative suffix."
)
text = text.replace(
    "When you need to speak to a group, or if you are in a formal situation, you simply take that basic informal command and add the plural ending.",
    "Для групи (for a group) або у формальній ситуації (formal situation), you simply take that basic informal command and add the plural ending."
)
text = text.replace(
    "This distinction between the two forms is extremely important for social harmony.",
    "Ця різниця (this distinction) is extremely important for social harmony."
)
text = text.replace(
    "We can look at a few practical examples of how this system works in daily life.",
    "Ось практичні приклади (here are practical examples)."
)
text = text.replace(
    "Now we will focus our attention on the eight most critical verbs you absolutely need for giving commands right now.",
    "Зараз ми вивчимо вісім важливих дієслів (now we will learn eight important verbs)."
)
text = text.replace(
    "You drop the final vowel of the stem and add a short sound at the end.",
    "Ви відкидаєте останню голосну (you drop the final vowel) of the stem."
)
text = text.replace(
    "These forms are extremely common, especially in learning environments.",
    "Ці форми дуже популярні (these forms are very common)."
)
text = text.replace(
    "You will hear these fundamental commands very often in both formal and informal settings.",
    "Ви часто чуєте ці накази (you often hear these commands)."
)
text = text.replace(
    "Let us examine these highly irregular verbs more closely.",
    "Давайте подивимося на ці неправильні дієслова (let us look at these irregular verbs)."
)
text = text.replace(
    "Giving direct commands can sometimes sound harsh or excessively demanding.",
    "Прямі накази (direct commands) can sometimes sound harsh."
)
text = text.replace(
    "You have a significant amount of flexibility when deciding where to put **будь ласка** within your sentence.",
    "Ви маєте вибір (you have a choice) where to put **будь ласка**."
)
text = text.replace(
    "Now that we comprehensively understand how to tell people what they should do, we must address how to firmly tell them what they should not do.",
    "Тепер (now), we must address how to tell people what they should not do."
)
text = text.replace(
    "There are absolutely no special endings, complicated suffix changes, or complex grammatical adjustments required for заперечний наказ (negative command)s.",
    "Тут немає спеціальних закінчень (there are no special endings)."
)
text = text.replace(
    "This straightforward structure works perfectly for both the informal **ти** commands and the formal **ви** commands.",
    "Ця структура працює для обох форм (this structure works for both forms)."
)
text = text.replace(
    "For the time being, focus your attention exclusively on mastering the personal prohibitions.",
    "Зараз (now), focus your attention on personal prohibitions."
)
text = text.replace(
    "We have successfully covered a substantial amount of truly crucial material in this lesson (на цьому уроці).",
    "Ми вивчили важливий матеріал на цьому уроці (we learned important material in this lesson)."
)
text = text.replace(
    "Maintaining an attitude of politeness is a key aspect of successful communication.",
    "Ввічливість (politeness) is a key aspect of successful communication."
)

with open('curriculum/l2-uk-en/a1/imperative-and-requests.md', 'w') as f:
    f.write(text)

