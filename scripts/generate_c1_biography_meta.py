import os
import yaml

# Data for Modules 108-124
modules = [
    {
        "id": "108",
        "slug": "myroslav-marynovych",
        "title": "Мирослав Маринович",
        "subtitle": "Myroslav Marynovych",
        "desc": "Moral authority, dissident, and human rights defender.",
        "tags": ["dissident", "human_rights", "philosophy", "gulag", "moral_authority"]
    },
    {
        "id": "109",
        "slug": "leonid-kadenyuk",
        "title": "Леонід Каденюк",
        "subtitle": "Leonid Kadenyuk",
        "desc": "The first astronaut of independent Ukraine.",
        "tags": ["science", "space", "technology", "exploration"]
    },
    {
        "id": "110",
        "slug": "vasyl-shkliar",
        "title": "Василь Шкляр",
        "subtitle": "Vasyl Shkliar",
        "desc": "Master of historical fiction and author of 'Black Raven'.",
        "tags": ["literature", "historical_fiction", "insurgency", "best_seller"]
    },
    {
        "id": "111",
        "slug": "yuri-vynnychuk",
        "title": "Юрій Винничук",
        "subtitle": "Yuri Vynnychuk",
        "desc": "Postmodernist writer and creator of the 'Lviv Myth'.",
        "tags": ["literature", "postmodernism", "lviv", "mystification", "humor"]
    },
    {
        "id": "112",
        "slug": "kvitka-cisyk",
        "title": "Квітка Цісик",
        "subtitle": "Kvitka Cisyk",
        "desc": "The golden voice of the Ukrainian diaspora.",
        "tags": ["music", "diaspora", "folk_songs", "cultural_preservation"]
    },
    {
        "id": "113",
        "slug": "halyna-pahutiak",
        "title": "Галина Пагутяк",
        "subtitle": "Halyna Pahutiak",
        "desc": "Writer of mystical prose and gothic philosophy.",
        "tags": ["literature", "mysticism", "gothic", "philosophy", "mythology"]
    },
    {
        "id": "114",
        "slug": "maria-matios",
        "title": "Марія Матіос",
        "subtitle": "Maria Matios",
        "desc": "Explorer of historical trauma and Bukovinian fate.",
        "tags": ["literature", "history", "trauma", "bukovyna", "family_saga"]
    },
    {
        "id": "115",
        "slug": "oksana-zabuzhko",
        "title": "Оксана Забужко",
        "subtitle": "Oksana Zabuzhko",
        "desc": "Leading public intellectual, feminist, and essayist.",
        "tags": ["literature", "feminism", "intellectual", "essays", "philosophy"]
    },
    {
        "id": "116",
        "slug": "yaroslav-hrytsak",
        "title": "Ярослав Грицак",
        "subtitle": "Yaroslav Hrytsak",
        "desc": "Historian who connects Ukraine to global processes.",
        "tags": ["history", "global_context", "intellectual", "modernity", "critical_thinking"]
    },
    {
        "id": "117",
        "slug": "vitaliy-portnikov",
        "title": "Віталій Портников",
        "subtitle": "Vitaliy Portnikov",
        "desc": "Journalist and political analyst on statehood and identity.",
        "tags": ["journalism", "politics", "analysis", "national_identity", "media"]
    },
    {
        "id": "118",
        "slug": "taras-prokhasko",
        "title": "Тарас Прохасько",
        "subtitle": "Taras Prokhasko",
        "desc": "Master of existential, slow, and atmospheric prose.",
        "tags": ["literature", "existentialism", "carpathians", "philosophy", "nature"]
    },
    {
        "id": "119",
        "slug": "serhiy-zhadan",
        "title": "Сергій Жадан",
        "subtitle": "Serhiy Zhadan",
        "desc": "The poetic voice of Eastern Ukraine and the war generation.",
        "tags": ["literature", "poetry", "war", "donbas", "music", "activism"]
    },
    {
        "id": "120",
        "slug": "oleh-sentsov",
        "title": "Олег Сенцов",
        "subtitle": "Oleh Sentsov",
        "desc": "Filmmaker, former political prisoner, and soldier.",
        "tags": ["cinema", "resistance", "human_rights", "war", "memoirs", "crimea"]
    },
    {
        "id": "121",
        "slug": "tamara-horiha-zernia",
        "title": "Тамара Горіха Зерня",
        "subtitle": "Tamara Horiha Zernia",
        "desc": "Author of 'Dotsia' and chronicler of the volunteer movement.",
        "tags": ["literature", "war", "volunteering", "donbas", "resistance"]
    },
    {
        "id": "122",
        "slug": "kateryna-kalytko",
        "title": "Катерина Калитко",
        "subtitle": "Kateryna Kalytko",
        "desc": "Poet of war, borders, and the physical experience of trauma.",
        "tags": ["literature", "poetry", "war", "trauma", "balkans"]
    },
    {
        "id": "123",
        "slug": "sofia-andrukhovych",
        "title": "Софія Андрухович",
        "subtitle": "Sofia Andrukhovych",
        "desc": "Stylistic master of memory, history, and forgotten identities.",
        "tags": ["literature", "style", "history", "memory", "aesthetics"]
    },
    {
        "id": "124",
        "slug": "oleksandra-matviichuk",
        "title": "Олександра Матвійчук",
        "subtitle": "Oleksandra Matviichuk",
        "desc": "Nobel Peace Prize laureate and human rights lawyer.",
        "tags": ["human_rights", "nobel_prize", "law", "civil_society", "justice"]
    }
]

output_dir = "curriculum/l2-uk-en/c1/meta"

for mod in modules:
    filename = f"{mod['id']}-{mod['slug']}.yaml"
    filepath = os.path.join(output_dir, filename)
    
    content = {
        "module": f"c1-{mod['id']}",
        "title": mod['title'],
        "subtitle": mod['subtitle'],
        "version": "2.0",
        "phase": "C1.3 Biographies",
        "focus": "biography",
        "pedagogy": "narrative",
        "duration": 120,
        "transliteration": "none",
        "vocabulary_count": 24,
        "tags": ["biography", "c1"] + mod['tags'],
        "grammar": [
            "Biographical narrative register",
            "Advanced stylistic analysis"
        ],
        "objectives": [
            f"Analyze the contribution of {mod['subtitle']} to modern Ukraine",
            "Master vocabulary related to " + ", ".join(mod['tags'][:2]),
            "Discuss the historical context of their work"
        ],
        "slug": f"{mod['id']}-{mod['slug']}"
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        yaml.dump(content, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
        
print(f"Generated {len(modules)} metadata files in {output_dir}")
