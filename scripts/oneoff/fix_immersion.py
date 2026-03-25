import re

file_path = "curriculum/l2-uk-en/a2/being-and-becoming.md"
with open(file_path, "r", encoding="utf-8") as f:
    text = f.read()

replacements = [
    (r"\bThe Instrumental case\b", "**Орудний відмінок** (The Instrumental case)"),
    (r"\bthe Instrumental case\b", "**орудний відмінок** (the Instrumental case)"),
    # Avoid replacing if already replaced
    (r"(?<!\()(?<!\*\*)Instrumental case\b", "**орудний відмінок** (Instrumental case)"),
    (r"\bThe Nominative case\b", "**Називний відмінок** (The Nominative case)"),
    (r"\bthe Nominative case\b", "**називний відмінок** (the Nominative case)"),
    (r"(?<!\()(?<!\*\*)Nominative case\b", "**називний відмінок** (Nominative case)"),
    (r"\bpresent tense\b", "**теперішній час** (present tense)"),
    (r"\bpast tense\b", "**минулий час** (past tense)"),
    (r"\bfuture tense\b", "**майбутній час** (future tense)"),
    (r"\bperfective aspect\b", "**доконаний вид** (perfective aspect)"),
    (r"\bimperfective aspect\b", "**недоконаний вид** (imperfective aspect)"),
    (r"\bTo describe your profession\b", "Щоб описати професію (To describe your profession)"),
    (r"\bLanguage is a living reflection\b", "Мова (Language) is a living reflection"),
    (r"\bTo truly master discussing professions\b", "Щоб вільно говорити про професії (To truly master discussing professions)"),
    (r"\bNow that we have explored\b", "Тепер (Now) that we have explored"),
    (r"\bYou have successfully learned\b", "Ви успішно вивчили (You have successfully learned)"),
    (r"Check your knowledge:", "**Перевірте свої знання** (Check your knowledge):"),
    (r"Look at these \*\*теперішній час\*\* \(present tense\) examples of identity", "Подивіться на ці приклади (Look at these **теперішній час** (present tense) examples) of identity"),
    (r"Let us look at some pairs", "Давайте подивимось на пари (Let us look at some pairs)"),
    (r"Let us review our core profession vocabulary", "Давайте повторимо слова (Let us review our core profession vocabulary)"),
    (r"Let us practice the transition", "Давайте попрактикуємось (Let us practice the transition)"),
    (r"Let us look at another conversation", "Давайте подивимось на інший діалог (Let us look at another conversation)"),
    (r"Let us revisit the translation", "Давайте згадаємо (Let us revisit) the translation"),
    (r"\bThe first crucial verb is\b", "Перше важливе дієслово — це (The first crucial verb is)"),
    (r"\bThe next important verbs are\b", "Наступні важливі дієслова — це (The next important verbs are)"),
    (r"\bFinally, we have the highly frequent verb\b", "Нарешті, ми маємо дієслово (Finally, we have the highly frequent verb)"),
    (r"\bWelcome to a fascinating aspect\b", "Вітаємо (Welcome) to a fascinating aspect"),
    (r"In Ukrainian, we draw", "У нашій мові (In Ukrainian), we draw"),
    (r"When we talk about who we are", "Коли ми говоримо про себе (When we talk about who we are)"),
    (r"Look at these corrections", "Подивіться на ці виправлення (Look at these corrections)"),
    (r"The verb \"to be\"", "Дієслово (The verb) \"to be\""),
    (r"When you meet someone new", "Коли ви знайомитеся (When you meet someone new)"),
    (r"In addition to professions", "Крім професій (In addition to professions)"),
    (r"The best way to build accuracy is through transformation patterns", "Найкращий спосіб (The best way) to build accuracy is through transformation patterns"),
    (r"This distinction is at the heart of how we discuss", "Ця різниця (This distinction) is at the heart of how we discuss"),
    (r"Because the IT sector is so prominent", "Оскільки сфера IT така популярна (Because the IT sector is so prominent)"),
]

for old, new in replacements:
    text = re.sub(old, new, text)

# Let's fix potential double formatting
text = text.replace("**Орудний відмінок** (The **орудний відмінок** (Instrumental case))", "**Орудний відмінок** (The Instrumental case)")
text = text.replace("**називний відмінок** (the **називний відмінок** (Nominative case))", "**називний відмінок** (the Nominative case)")

# Check if there are missing 'Наприклад:' or 'Порівняйте:' before examples
text = text.replace("Here are more transformation examples to reinforce your learning (Порівняйте):", "Here are more transformation examples to reinforce your learning.\n\n**Порівняйте** (Compare):")
text = text.replace("Look at these corrections to avoid the Gender Mismatch error (Порівняйте):", "Look at these corrections to avoid the Gender Mismatch error.\n\n**Порівняйте** (Compare):")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(text)

