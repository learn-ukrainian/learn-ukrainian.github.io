import re

MD_PATH = "/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/description-adverbs.md"

with open(MD_PATH, "r", encoding="utf-8") as f:
    text = f.read()

# Fix Euphony
text = text.replace("повільно і уважно", "повільно й уважно")

# Fix metalanguage (remove іменник, прикметник)
text = text.replace("Іменник — це цеглина. Він називає людину або об'єкт.", "A noun is a brick. It names a person or an object.")
text = text.replace("Прикметник — це фарба. Він яскраво описує іменник.", "An adjective is paint. It describes a noun.")
text = text.replace("Прикметники описують іменники.", "Adjectives describe nouns.")
text = text.replace("Ви берете прикметник.", "You take an adjective.")

eng_to_ukr = {
    # 1. Час та частота
    """Adverbs of frequency are absolutely essential because they allow us to share our schedules, explain our routines, and set clear expectations with other people. Without these specific adverbs, every single action you describe sounds like an isolated, one-time event happening exactly right now. With them, you can communicate the entire rhythm of your lifestyle.""":
    "Прислівники часу показують ваш розклад. Ви пояснюєте вашу рутину. Без них дія відбувається тільки зараз. З ними ви описуєте ритм вашого життя. Це дуже корисно для комунікації.",
    
    """Here is the visual frequency scale, ranging from one hundred percent absolute consistency down to zero percent. Memorizing this scale will allow you to precisely describe your daily life.""":
    "Ось візуальна шкала частоти. Вона йде від ста відсотків до нуля. Вивчайте цю шкалу. Вона допомагає описувати ваше щоденне життя.",
    
    """Let's look at how these fundamental words function in complete, natural sentences. Notice that adverbs of frequency typically appear directly before the verb they modify, setting the temporal expectation before the action is even announced.""":
    "Ось як ці слова працюють у реченнях. Зверніть увагу: прислівники часу стоять перед дієсловом. Вони створюють контекст.",
    
    """The zero percent frequency marker, **ніко́ли** [nʲiˈkɔlɪ], requires special, focused attention because it operates completely differently from English grammar. This is one of the most common stumbling blocks for English speakers because it feels inherently redundant to our linguistic instincts.""":
    "Слово **ніколи** вимагає особливої уваги. Воно працює інакше, ніж в англійській мові. Це типова проблема для студентів.",
    
    """In the English language, the word "never" carries the absolute entirety of the negative meaning for the whole sentence. You simply say "I never drink tea." You do not add another negative word.""":
    "В англійській мові слово "never" не потребує інших заперечень. Ви кажете "I never drink tea".",
    
    """Ukrainian grammar, however, demands a strict double negation to convey this exact same meaning. The adverb **ніко́ли** must always, without exception, be paired with the negative particle **не**. Furthermore, this negative particle must be placed directly before the main verb. The adverb "ніко́ли" signals that the frequency is mathematically zero, and the "не" negates the action itself.""":
    "Українська граматика вимагає подвійного заперечення. Слово **ніколи** завжди працює зі словом **не**. Слово **не** стоїть прямо перед дієсловом.",
    
    """Let's look at how this rigid, unyielding structure appears in standard sentences.""":
    "Подивіться на цю структуру в стандартних реченнях.",
    
    """Alongside adverbs of manner and adverbs of frequency, we also rely heavily on adverbs that specify time and place. These are essential foundational markers that locate your actions in physical reality and chronological time. They conceptually ground your sentences.""":
    "Ми також використовуємо прислівники місця та часу. Вони локалізують ваші дії в просторі та часі. Вони створюють базу.",
    
    """The Ukrainian State Standard for language proficiency explicitly categorizes these specific words as essential, foundational vocabulary for the A1 level. You simply cannot navigate basic daily situations without them.""":
    "Стандарт української мови відносить ці слова до базового рівня А1. Вони дуже потрібні для щоденного життя.",
    
    """For spatial markers indicating location, we use the simple, powerful words **тут** (here) and **там** (there). For temporal markers indicating time, we use the vital words **сього́дні** (today) and **за́втра** (tomorrow). These are basic, independent adverbs. They do not change their form, they do not decline through complex case systems, and they do not have hidden grammatical rules. You simply insert them into the sentence to provide immediate context.""":
    "Для локації ми використовуємо слова **тут** та **там**. Для часу ми використовуємо **сьогодні** та **завтра**. Це незалежні слова. Вони не змінюють форму. Ви просто ставите їх у речення.",
    
    """These straightforward markers are the fundamental building blocks of daily planning and practical scheduling. You can easily combine them with the adverbs of manner and frequency that you learned earlier to create highly descriptive, complex, and nuanced sentences.""":
    "Ці слова — це база для планування. Ви комбінуєте їх з іншими словами. Ви створюєте складні речення.",
    
    # Синтаксис
    """To achieve this precision, we use specific words called intensity modifiers. These words adjust the strength, power, and magnitude of your primary adverb. They are the fine-tuning dials of your sentences.""":
    "Для цієї точності ми використовуємо модифікатори. Вони змінюють силу вашого слова. Це панель налаштувань вашого речення.",
    
    """The most common and useful intensity modifiers are:""":
    "Найбільш типові модифікатори:",
    
    """Here is exactly how they amplify or soften an adverb in a real sentence context.""":
    "Ось як вони змінюють силу в реченні.",
    
    """Syntax—the strict rules governing the absolute order of words in a sentence—can sometimes be flexible in conversational Ukrainian, but certain rules are set in stone. There is a strict, unbreakable syntax rule regarding these intensity modifiers.""":
    "Синтаксис (порядок слів) в українській мові гнучкий. Але деякі правила дуже суворі. Є одне важливе правило для модифікаторів.",
    
    """The intensifier word MUST immediately precede the adverb or adjective that it is actively modifying. They operate as a strictly inseparable pair.""":
    "Модифікатор ЗАВЖДИ стоїть перед словом. Вони працюють як пара.",
    
    """In English, you have a lot of syntactic freedom. You can sometimes place an intensifier at the absolute end of a sentence for dramatic, poetic effect, or separate it entirely from the main adverb. In Ukrainian, this kind of syntactic separation is strictly forbidden. The modifier word, like **ду́же**, must be permanently glued to the front of the word it intensifies. If you break this bond, the sentence loses its structural integrity and immediately marks you as a beginner who is translating directly from English.""":
    "В англійській мові у вас є свобода. В українській мові такої свободи немає. Слово **дуже** завжди стоїть попереду. Якщо ви змінюєте порядок, речення звучить неправильно.",
    
    """Let's look at a clear visual comparison of correct and structurally incorrect usage to burn this pattern into your mind.""":
    "Подивіться на це візуальне порівняння правильного та неправильного використання.",
    
    """To truly understand how all of these different adverbs function together in natural, flowing speech, let's observe a realistic scenario.""":
    "Щоб розуміти ці слова, давайте подивимося на реальний сценарій.",
    
    """Imagine a highly demanding, professional food critic visiting a new, popular restaurant in the center of Kyiv. The critic is observing everything and taking detailed mental notes. Observe closely how the adverbs of manner, the adverbs of frequency, and the intensity modifiers all work seamlessly together to create a vivid, highly descriptive picture of the dining experience.""":
    "Уявіть критика ресторанів у Києві. Він уважно дивиться. Він робить нотатки. Подивіться, як він використовує слова, щоб створити яскраву картину."
}

for eng, ukr in eng_to_ukr.items():
    text = text.replace(eng, ukr)

with open(MD_PATH, "w", encoding="utf-8") as f:
    f.write(text)

print("Translated large chunks and removed metalanguage to boost immersion safely.")
