import re
import os
import yaml

# Output directory
OUTPUT_DIR = "curriculum/l2-uk-en/c1/meta"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Function to write YAML
def write_meta(id_num, title, subtitle, phase, focus, tags, desc=""):
    slug_title = title.lower().replace(" ", "-").replace(":", "").replace(",", "").replace(".", "")
    slug_title = re.sub(r'[^a-z0-9\-а-яіїєґ]', '', slug_title)
    
    # Basic transliteration for filename
    uk_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'h', 'ґ': 'g', 'д': 'd', 'е': 'e', 'є': 'ye',
        'ж': 'zh', 'з': 'z', 'и': 'y', 'і': 'i', 'ї': 'yi', 'й': 'y', 'к': 'k', 'л': 'l',
        'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ь': '', 'ю': 'yu', 'я': 'ya'
    }
    slug = ""
    for char in slug_title:
        slug += uk_map.get(char, char)
    
    filename = f"{id_num}-{slug}.yaml"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    # Skip if exists (preserve 108-124)
    if os.path.exists(filepath):
        print(f"Skipping {filename} (already exists)")
        return

    content = {
        "module": f"c1-{id_num}",
        "title": title,
        "subtitle": subtitle,
        "version": "2.0",
        "phase": phase,
        "focus": focus,
        "pedagogy": "narrative" if focus == "biography" else "academic",
        "duration": 120,
        "vocabulary_count": 24,
        "tags": ["c1", focus] + tags,
        "objectives": [f"Master C1 concepts in {title}"],
        "slug": f"{id_num}-{slug}"
    }
    
    if desc:
        content["desc"] = desc

    with open(filepath, 'w', encoding='utf-8') as f:
        yaml.dump(content, f, allow_unicode=True, sort_keys=False)
    print(f"Generated {filename}")

# 1. C1.1 (01-20) - Headers are likely correct
# Hardcoding C1.1 based on reading
c1_1_modules = [
    (1, "B2 Review & Bridge", "Review", ["review", "grammar"]),
    (2, "Academic Style Markers", "Style", ["academic", "register"]),
    (3, "Research Verbs", "Vocabulary", ["verbs", "research"]),
    (4, "Analysis Vocabulary", "Vocabulary", ["analysis", "nouns"]),
    (5, "Logical Connectors", "Grammar", ["connectors", "logic"]),
    (6, "Hedging & Modality", "Grammar", ["hedging", "modality"]),
    (7, "Citation & Reference", "Skills", ["citation", "integrity"]),
    (8, "Essay Structure", "Writing", ["essay", "structure"]),
    (9, "Thesis Development", "Writing", ["thesis", "argument"]),
    (10, "Counterarguments", "Writing", ["debate", "counterargument"]),
    (11, "Summary & Paraphrase", "Skills", ["summary", "paraphrase"]),
    (12, "Genre: Research Article", "Genre", ["article", "research"]),
    (13, "Genre: Abstract", "Genre", ["abstract", "summary"]),
    (14, "Genre: Literature Review", "Genre", ["literature_review", "synthesis"]),
    (15, "Oral Presentations", "Speaking", ["presentation", "speech"]),
    (16, "Advanced Punctuation", "Grammar", ["punctuation", "writing"]),
    (17, "Irregular Verbs Complete", "Grammar", ["verbs", "irregular"]),
    (18, "C1.1 Practice I", "Practice", ["essay", "practice"]),
    (19, "C1.1 Practice II", "Practice", ["critique", "practice"]),
    (20, "C1.1 Checkpoint", "Checkpoint", ["assessment"])
]

for mid, title, focus, tags in c1_1_modules:
    write_meta(mid, title, "Academic Foundation", "C1.1 Academic", focus.lower(), tags)

# 2. C1.2 (21-35)
c1_2_modules = [
    (21, "CV & Resume Writing", "Professional", ["cv", "resume"]),
    (22, "Interview Language", "Professional", ["interview", "speaking"]),
    (23, "Business Etiquette", "Professional", ["etiquette", "culture"]),
    (24, "Digital Communication", "Professional", ["email", "digital"]),
    (25, "Political System", "Social", ["politics", "government"]),
    (26, "Media Landscape", "Social", ["media", "news"]),
    (27, "Global Context", "Social", ["eu", "nato", "global"]),
    (28, "Dialects Overview", "Sociolinguistics", ["dialects", "variation"]),
    (29, "Surzhyk", "Sociolinguistics", ["surzhyk", "mixing"]),
    (30, "Language Policy", "Sociolinguistics", ["policy", "law"]),
    (31, "Diaspora Ukrainian", "Sociolinguistics", ["diaspora", "global"]),
    (32, "C1.2 Practice I", "Practice", ["professional", "practice"]),
    (33, "C1.2 Practice II", "Practice", ["case_study", "practice"]),
    (34, "C1.2 Review", "Review", ["review"]),
    (35, "C1.2 Checkpoint", "Checkpoint", ["assessment"])
]

for mid, title, focus, tags in c1_2_modules:
    write_meta(mid, title, "Professional & Social", "C1.2 Professional", focus.lower(), tags)

# 3. C1.3 (36-107 + 125) - Biographies
# I need to read the file again to get exact names for 36-107.
# Using a simplified list based on the Plan read earlier.
# This list matches the grep output from earlier.
bios = [
    (36, "Княгиня Ольга", "Olha"),
    (37, "Князь Святослав", "Sviatoslav"),
    (38, "Князь Володимир Великий", "Volodymyr the Great"),
    (39, "Князь Ярослав Мудрий", "Yaroslav the Wise"),
    (40, "Княжна Анна Ярославна", "Anna Yaroslavna"),
    (41, "Михайло Чернігівський", "Mykhailo Chernihivskyi"),
    (42, "Роксолана", "Roksolana"),
    (43, "Іов Борецький", "Iov Boretskyi"),
    (44, "Сильвестр Косів", "Sylvestr Kosiv"),
    (45, "Богдан Хмельницький", "Bohdan Khmelnytskyi"),
    (46, "Юрій Немирич", "Yurii Nemyrych"),
    (47, "Іван Мазепа", "Ivan Mazepa"),
    (48, "Кость Гордієнко", "Kost Hordiienko"),
    (49, "Пилип Орлик", "Pylyp Orlyk"),
    (50, "Петро Калнишевський", "Petro Kalnyshevskyi"),
    (51, "Григорій Сковорода", "Hryhorii Skovoroda"),
    (52, "Максим Березовський", "Maksym Berezovskyi"),
    (53, "Дмитро Бортнянський", "Dmytro Bortnianskyi"),
    (54, "Семен Гулак-Артемовський", "Semen Hulak-Artemovskyi"),
    (55, "Тарас Шевченко", "Taras Shevchenko"),
    (56, "Ганна Барвінок", "Hanna Barvinok"),
    (57, "Михайло Драгоманов", "Mykhailo Drahomanov"),
    (58, "Микола Лисенко", "Mykola Lysenko"),
    (59, "Олена Пчілка", "Olena Pchilka"),
    (60, "Наталія Кобринська", "Nataliia Kobrynska"),
    (61, "Марія Заньковецька", "Mariia Zankovetska"),
    (62, "Марія Павлова", "Mariia Pavlova"),
    (63, "Іван Франко", "Ivan Franko"),
    (64, "Євген Чикаленко", "Yevhen Chykalenko"),
    (65, "Борис Грінченко", "Borys Hrinchenko"),
    (66, "Ольга Кобилянська", "Olha Kobylianska"),
    (67, "Кирило Трильовський", "Kyrylo Trylovskyi"),
    (68, "Софія Окуневська", "Sofiia Okunevska"),
    (69, "Іван Липа", "Ivan Lypa"),
    (70, "Михайло Грушевський", "Mykhailo Hrushevskyi"),
    (71, "Микола Василенко", "Mykola Vasylenko"),
    (72, "Марія Вояковська", "Mariia Voiakovska"),
    (73, "Людмила Старицька", "Liudmyla Starytska"),
    (74, "Юліан Бачинський", "Yulian Bachynskyi"),
    (75, "Леся Українка", "Lesia Ukrainka"),
    (76, "Соломія Крушельницька", "Solomiia Krushelnytska"),
    (77, "Микола Міхновський", "Mykola Mikhnovskyi"),
    (78, "Микола Леонтович", "Mykola Leontovych"),
    (79, "Симон Петлюра", "Symon Petliura"),
    (80, "Казимір Малевич", "Kazymyr Malevych"),
    (81, "Олександр Греків", "Oleksandr Hrekiv"),
    (82, "Олександр Богомазов", "Oleksandr Bohomazov"),
    (83, "В'ячеслав Липинський", "Viacheslav Lypynskyi"),
    (84, "Дмитро Донцов", "Dmytro Dontsov"),
    (85, "Петро Болбочан", "Petro Bolbochan"),
    (86, "Наталія Полонська-Василенко", "Nataliia Polonska-Vasylenko"),
    (87, "Валентина Радзимовська", "Valentyna Radzymovska"),
    (88, "Олександр Архипенко", "Oleksandr Arkhypenko"),
    (89, "Лесь Курбас", "Les Kurbas"),
    (90, "Василь Вишиваний", "Vasyl Vyshyvanyi"),
    (91, "Ольга Басараб", "Olha Basarab"),
    (92, "Берта Рапопорт", "Berta Rapoport"),
    (93, "Олена Степанів", "Olena Stepaniv"),
    (94, "Віра Холодна", "Vira Kholodna"),
    (95, "Микола Хвильовий", "Mykola Khvylovyi"),
    (96, "Борис Лятошинський", "Borys Liatoshynskyi"),
    (97, "Клавдія Латишева", "Klavdiia Latysheva"),
    (98, "Катерина Білокур", "Kateryna Bilokur"),
    (99, "Серж Лифар", "Serge Lifar"),
    (100, "Олена Теліга", "Olena Teliha"),
    (101, "Марія Примаченко", "Mariia Prymachenko"),
    (102, "Катерина Ющенко", "Kateryna Yushchenko"),
    (103, "Левко Лук'яненко", "Levko Lukianenko"),
    (104, "Алла Горська", "Alla Horska"),
    (105, "Ліна Костенко", "Lina Kostenko"),
    (106, "В'ячеслав Чорновіл", "Viacheslav Chornovil"),
    (107, "Василь Стус", "Vasyl Stus"),
]

for mid, title, subtitle in bios:
    write_meta(mid, title, subtitle, "C1.3 Biographies", "biography", ["history", "culture"])

# 125 Checkpoint
write_meta(125, "C1.3 Checkpoint", "Review", "C1.3 Biographies", "checkpoint", ["assessment"])

# 4. C1.4 (126-145) - Stylistics
c1_4_modules = [
    (126, "Metaphor & Simile", "Stylistics", ["metaphor", "figurative"]),
    (127, "Irony & Sarcasm", "Stylistics", ["irony", "humor"]),
    (128, "Hyperbole & Litotes", "Stylistics", ["hyperbole", "emphasis"]),
    (129, "Euphemism & Taboo", "Stylistics", ["euphemism", "register"]),
    (130, "Rhetorical Questions", "Rhetoric", ["questions", "persuasion"]),
    (131, "Degrees of Certainty", "Modality", ["certainty", "modality"]),
    (132, "Politeness Strategies", "Pragmatics", ["politeness", "social"]),
    (133, "Indirectness", "Pragmatics", ["indirectness", "implication"]),
    (134, "Ukrainian Humor", "Culture", ["humor", "culture"]),
    (135, "Wordplay & Puns", "Humor", ["wordplay", "pun"]),
    (136, "Anecdotes & Jokes", "Humor", ["anecdote", "storytelling"]),
    (137, "Archaic Verb Forms", "Grammar", ["archaic", "verbs"]),
    (138, "Literary Syntax", "Syntax", ["literary", "syntax"]),
    (139, "Church Slavonicisms", "Vocabulary", ["church_slavonic", "archaic"]),
    (140, "Archaic Pronouns", "Grammar", ["archaic", "pronouns"]),
    (141, "High Formal Register", "Register", ["formal", "official"]),
    (142, "Intimate Register", "Register", ["intimate", "informal"]),
    (143, "Slang & Youth Language", "Register", ["slang", "youth"]),
    (144, "C1.4 Review", "Review", ["review"]),
    (145, "C1.4 Checkpoint", "Checkpoint", ["assessment"])
]

for mid, title, subtitle, tags in c1_4_modules:
    write_meta(mid, title, subtitle, "C1.4 Stylistics", "stylistics", tags)

# 5. C1.5 (146-181) - Folk Culture (Shifted +14 from old 132-167)
# Old 132 -> New 146
c1_5_data = [
    ("Кобзарі та бандура", "Folk Music"),
    ("Обрядові пісні", "Folk Music"),
    ("Колискові та думи", "Folk Music"),
    ("Гопак і козачок", "Folk Dance"),
    ("Регіональні танці", "Folk Dance"),
    ("Писанки", "Folk Crafts"),
    ("Вишиванка", "Folk Crafts"),
    ("Гончарство та різьбярство", "Folk Crafts"),
    ("Народна міфологія", "Folk Beliefs"),
    ("Народна медицина", "Folk Beliefs"),
    ("Козацькі легенди", "Folk Tales"),
    ("Казки та притчі", "Folk Tales"),
    ("Зимові обряди", "Calendar"),
    ("Весна та літо", "Calendar"),
    ("Хрестини та весілля", "Life Rituals"),
    ("Поминальні обряди", "Life Rituals"),
    ("Галичина", "Regional"),
    ("Слобожанщина", "Regional"),
    ("Полісся", "Regional"),
    ("Поділля та Волинь", "Regional"),
    ("Класична музика I", "Fine Arts"),
    ("Класична музика II", "Fine Arts"),
    ("Класична музика III", "Fine Arts"),
    ("Оперне мистецтво", "Fine Arts"),
    ("Вокальне мистецтво", "Fine Arts"),
    ("Образотворче мистецтво I", "Fine Arts"),
    ("Образотворче мистецтво II", "Fine Arts"),
    ("Балет і танець", "Fine Arts"),
    ("Театральне мистецтво I", "Fine Arts"),
    ("Театральне мистецтво II", "Fine Arts"),
    ("Українська архітектура", "Fine Arts"),
    ("Сучасна музика", "Contemporary"),
    ("Українське кіно", "Contemporary"),
    ("C1.5 Практика I", "Practice"),
    ("C1.5 Практика II", "Practice"),
    ("C1.5 Checkpoint", "Checkpoint")
]

start_1_5 = 146
for i, (title, subtitle) in enumerate(c1_5_data):
    mid = start_1_5 + i
    write_meta(mid, title, subtitle, "C1.5 Culture", "culture", ["folk", "arts"])

# 6. C1.6 (182-196) - Literature (Shifted +14 from old 168-182)
# Old 168 -> New 182
c1_6_data = [
    ("Історія української літератури", "Lit History"),
    ("Котляревський: Енеїда", "Classics"),
    ("Шевченко: Щоденник та листи", "Shevchenko"),
    ("Шевченко: Поезія", "Shevchenko"),
    ("Шевченко: Спадщина", "Shevchenko"),
    ("Франко: Громадянська лірика", "Franko"),
    ("Франко: Проза", "Franko"),
    ("Леся Українка: Лірика", "Lesia"),
    ("Леся Українка: Драма", "Lesia"),
    ("Вовчок та Мирний", "Realism"),
    ("Коцюбинський", "Modernism"),
    ("Літературознавча термінологія", "Theory"),
    ("Аналіз поезії", "Skills"),
    ("C1.6 Review", "Review"),
    ("C1.6 Checkpoint", "Checkpoint")
]

start_1_6 = 182
for i, (title, subtitle) in enumerate(c1_6_data):
    mid = start_1_6 + i
    write_meta(mid, title, subtitle, "C1.6 Literature", "literature", ["lit", "analysis"])

