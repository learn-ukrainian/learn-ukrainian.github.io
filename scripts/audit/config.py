"""
Configuration constants for module auditing.

Contains grammar constraints, case patterns, level configurations,
and activity requirements for each CEFR level.
"""

# Grammar constraints by level (what's ALLOWED at each level)
GRAMMAR_CONSTRAINTS = {
    'A1': {
        'cases_allowed': ['nominative', 'accusative', 'locative', 'genitive', 'vocative'],
        'cases_forbidden': ['dative', 'instrumental'],
        'aspect': 'imperfective_only',
        'participles': False,
        'subordinate_clauses': False,
        'max_words_per_sentence': 10,
        'max_clauses': 1,
    },
    'A2': {
        'cases_allowed': ['nominative', 'accusative', 'locative', 'genitive', 'dative', 'instrumental', 'vocative'],
        'cases_forbidden': [],
        'aspect': 'pairs_introduced',
        'participles': False,
        'subordinate_clauses': 'simple',
        'max_words_per_sentence': 15,
        'max_clauses': 2,
    },
    'B1': {
        'cases_allowed': ['nominative', 'accusative', 'locative', 'genitive', 'dative', 'instrumental', 'vocative'],
        'cases_forbidden': [],
        'aspect': 'full',
        'participles': True,
        'subordinate_clauses': 'complex',
        'max_words_per_sentence': 25,
        'max_clauses': 4,
    },
    'B2': {
        'cases_allowed': ['nominative', 'accusative', 'locative', 'genitive', 'dative', 'instrumental', 'vocative'],
        'cases_forbidden': [],
        'aspect': 'full',
        'participles': True,
        'adverbial_participles': True,
        'subordinate_clauses': 'complex',
        'max_words_per_sentence': 35,
        'max_clauses': 6,
    },
    'C1': {'max_words_per_sentence': 50, 'max_clauses': 10},
    'C2': {'max_words_per_sentence': 100, 'max_clauses': 20},
}

# Ukrainian case ending patterns (simplified detection)
CASE_PATTERNS = {
    'dative': [
        # -ові/-еві/-єві endings are dative ONLY when NOT preceded by locative prepositions
        # в Києві, у Львові = LOCATIVE (allowed at A1 from M13)
        # дати братові = DATIVE (not allowed at A1)
        # Use negative lookbehind to exclude locative contexts
        r'(?<![вуВУ]\s)\b\w+ові\b(?!\s*[,.])',  # Not after в/у
        r'(?<![вуВУ]\s)\b\w+еві\b(?!\s*[,.])',  # Not after в/у
        r'(?<![вуВУ]\s)\b\w+єві\b(?!\s*[,.])',  # Not after в/у
        # Dative pronouns - but NOT їм which is also verb "I eat" from їсти
        # їм is only dative in context like "подобається їм", "дати їм"
        r'\bмені\b', r'\bтобі\b', r'\bйому\b', r'\bїй\b', r'\bнам\b', r'\bвам\b',
        # їм as dative: only when preceded by dative-taking verbs
        r'(?:подобається|дати|сказати|показати|допомогти)\s+їм\b',
        r'\b\w+і\b.*подобається',
    ],
    'instrumental': [
        r'\bз\s+\w+ом\b', r'\bз\s+\w+ем\b', r'\bз\s+\w+ям\b',
        r'\bз\s+\w+ою\b', r'\bз\s+\w+ею\b',
        r'\bмною\b', r'\bтобою\b', r'\bним\b', r'\bнею\b', r'\bнами\b', r'\bвами\b', r'\bними\b',
        r'\bпід\s+\w+ом\b', r'\bнад\s+\w+ом\b', r'\bперед\s+\w+ом\b', r'\bза\s+\w+ом\b',
    ],
    'perfective_markers': [
        r'\bпо\w+ив\b', r'\bпро\w+ав\b', r'\bз\w+ив\b', r'\bна\w+ав\b',
        r'\bнаписав\b', r'\bпрочитав\b', r'\bзробив\b', r'\bсказав\b', r'\bвзяв\b',
        r'\bпоїв\b', r'\bвипив\b', r'\bз\'їв\b', r'\bподивився\b',
    ],
    'participles': [
        r'\b\w+уючий\b', r'\b\w+ючий\b', r'\b\w+ачий\b',
        r'\b\w+аний\b', r'\b\w+ений\b', r'\b\w+итий\b',
        r'\bчитаючи\b', r'\bговорячи\b', r'\bйдучи\b',
    ],
    'subordinate_markers': [
        # Relative pronouns (який/яка/яке/які) - only flag when preceded by a noun/comma
        # This indicates a relative clause, not a question
        r',\s*який\s+[а-яіїєґ]', r',\s*яка\s+[а-яіїєґ]', r',\s*яке\s+[а-яіїєґ]', r',\s*які\s+[а-яіїєґ]',
        # "що" as subordinate - only when preceded by verb/clause (not sentence-initial questions)
        # Pattern: verb + що + word (subordinate) vs. Що + word? (question)
        r'[а-яіїєґ],?\s+що\s+(?!це\b)[а-яіїєґ]',
        # Temporal/conditional conjunctions as subordinate (preceded by main clause)
        # коли/якщо at sentence start are questions/conditionals, not subordinate
        r'[а-яіїєґ],?\s+коли\s+[а-яіїєґ]',
        r'\bякщо\s+[а-яіїєґ]', r'\bтому що\s+[а-яіїєґ]',
        # "бо" (because) - require following word, exclude accent marks breaking word boundary
        r'(?<![а-яіїєґА-ЯІЇЄҐ\u0301])бо\s+[а-яіїєґ]',
        r'\bхоча\s+[а-яіїєґ]', r'\bщоб\s+[а-яіїєґ]', r'\bпоки\s+[а-яіїєґ]', r'\bдоки\s+[а-яіїєґ]',
    ],
}

# Activity stage ordering for PPP, TTT, and CLIL/Narrative
STAGE_ORDER = {
    'PPP': ['presentation', 'recognition', 'discrimination', 'controlled-production', 'free-production'],
    'TTT': ['diagnostic', 'recognition', 'presentation', 'controlled-production', 'free-production'],
    'CLIL': ['pre-engagement', 'immersion', 'narrative', 'deep-dive', 'recognition', 'controlled-production', 'free-production'],
    'NARRATIVE': ['pre-engagement', 'immersion', 'narrative', 'deep-dive', 'recognition', 'controlled-production', 'free-production'],
}

# Valid activity types
VALID_ACTIVITY_TYPES = [
    "match-up", "fill-in", "quiz", "true-false", "group-sort", "unjumble",
    "error-correction", "anagram", "select", "translate", "cloze",
    "dialogue-reorder", "mark-the-words"
]

# Activity keywords for detection
ACTIVITY_KEYWORDS = [
    "match-up", "gap-fill", "quiz", "true-false", "group-sort", "unjumble",
    "fill-in", "error-correction", "anagram", "cloze",
    "select", "translate", "dialogue-reorder", "mark-the-words"
]

# Activity-type-specific minimum items (overrides level default)
# Some activities naturally have fewer items (e.g., dialogue-reorder, cloze)
ACTIVITY_MIN_ITEMS = {
    'quiz': 8,
    'match-up': 8,
    'fill-in': 8,
    'true-false': 8,
    'group-sort': 8,
    'unjumble': 6,          # Sentences are longer, fewer needed
    'anagram': 8,
    'error-correction': 6,  # Each item requires careful construction
    'cloze': 6,             # Single passage with multiple blanks
    'select': 6,
    'translate': 6,
    'dialogue-reorder': 5,  # Dialogues can't be too long
    'mark-the-words': 6,    # Single passage
    'gap-fill': 8,          # Alias for fill-in
}

# Core section keywords (not activities)
CORE_KEYWORDS = [
    "warm-up", "presentation", "introduction", "narrative", "context",
    "diagnostic", "cultural", "culture", "story", "dialogue", "reading",
    "deep dive", "riddle", "insight", "conversation", "review", "concept",
    "core", "usage", "matters", "transformation", "memory", "tip",
    "pattern", "summary",
    # Ukrainian equivalents for B1+ modules
    "діагностика", "аналіз", "занурення", "глибоке", "помилки",
    "культур", "розмова", "текст", "діалог", "читання", "підсумок"
]

# Section keywords to exclude from core word count
EXCLUDE_KEYWORDS = ["activities", "activity", "production", "vocabulary", "check"]

# Level-specific configuration
LEVEL_CONFIG = {
    'A1': {
        'target_words': 750,
        'min_activities': 8,
        'min_items_per_activity': 12,
        'min_types_unique': 4,
        'min_vocab': 20,
        'min_engagement': 3,
        'immersion_graduated': True,
        'transliteration_allowed': True,
        'priority_types': {'fill-in', 'match-up', 'anagram', 'unjumble', 'quiz'}
    },
    'A2': {
        'target_words': 1000,
        'min_activities': 10,
        'min_items_per_activity': 12,
        'min_types_unique': 4,
        'min_vocab': 25,
        'min_engagement': 4,
        'min_immersion': 40,
        'max_immersion': 50,
        'transliteration_allowed': False,
        'priority_types': {'error-correction', 'unjumble', 'fill-in'}
    },
    'B1-grammar': {
        'target_words': 1250,
        'min_activities': 12,
        'min_items_per_activity': 14,
        'min_types_unique': 4,
        'min_vocab': 20,
        'min_engagement': 5,
        'min_immersion': 50,
        'max_immersion': 55,
        'transliteration_allowed': False,
        'priority_types': {'error-correction', 'fill-in', 'unjumble', 'cloze'}
    },
    'B1-vocab': {
        'target_words': 1250,
        'min_activities': 12,
        'min_items_per_activity': 14,
        'min_types_unique': 4,
        'min_vocab': 30,
        'min_engagement': 5,
        'min_immersion': 65,
        'max_immersion': 70,
        'transliteration_allowed': False,
        'priority_types': {'match-up', 'mark-the-words', 'translate', 'quiz'}
    },
    'B1': {
        'target_words': 1250,
        'min_activities': 12,
        'min_items_per_activity': 14,
        'min_types_unique': 4,
        'min_vocab': 25,
        'min_engagement': 5,
        'min_immersion': 50,
        'max_immersion': 70,
        'transliteration_allowed': False,
        'priority_types': {'fill-in', 'unjumble', 'error-correction'}
    },
    'B2-grammar': {
        'target_words': 1500,
        'min_activities': 14,
        'min_items_per_activity': 16,
        'min_types_unique': 4,
        'min_vocab': 20,
        'min_engagement': 6,
        'min_immersion': 65,
        'max_immersion': 70,
        'transliteration_allowed': False,
        'priority_types': {'error-correction', 'fill-in', 'unjumble', 'cloze'}
    },
    'B2-vocab': {
        'target_words': 1500,
        'min_activities': 14,
        'min_items_per_activity': 16,
        'min_types_unique': 4,
        'min_vocab': 30,
        'min_engagement': 6,
        'min_immersion': 80,
        'max_immersion': 85,
        'transliteration_allowed': False,
        'priority_types': {'match-up', 'mark-the-words', 'translate', 'quiz'}
    },
    'B2': {
        'target_words': 1500,
        'min_activities': 14,
        'min_items_per_activity': 16,
        'min_types_unique': 4,
        'min_vocab': 25,
        'min_engagement': 6,
        'min_immersion': 65,
        'max_immersion': 85,
        'transliteration_allowed': False,
        'priority_types': {'fill-in', 'unjumble', 'error-correction'}
    },
    'C1': {
        'target_words': 1750,
        'min_activities': 16,
        'min_items_per_activity': 18,
        'min_types_unique': 4,
        'min_vocab': 25,
        'min_engagement': 7,
        'min_immersion': 95,
        'max_immersion': 100,
        'transliteration_allowed': False,
        'priority_types': {'fill-in', 'unjumble', 'error-correction'}
    },
    'C2': {
        'target_words': 2000,
        'min_activities': 16,
        'min_items_per_activity': 18,
        'min_types_unique': 4,
        'min_vocab': 25,
        'min_engagement': 8,
        'min_immersion': 95,  # Allow 5% for Latin/Greek scholarly terms
        'max_immersion': 100,
        'transliteration_allowed': False,
        'priority_types': {'fill-in', 'unjumble', 'error-correction'}
    },
    'LIT': {
        'target_words': 2000,
        'min_activities': 0,
        'min_items_per_activity': 0,
        'min_types_unique': 0,
        'min_vocab': 0,
        'min_engagement': 4,
        'min_immersion': 95,  # Allow 5% for Latin/Greek scholarly terms
        'max_immersion': 100,
        'transliteration_allowed': False,
        'priority_types': set()
    }
}

# Activity level restrictions
ACTIVITY_RESTRICTIONS = {
    'A1': {
        'forbidden': ['error-correction', 'cloze', 'mark-the-words', 'dialogue-reorder', 'select', 'translate'],
        'anagram_limit': 10
    },
    'A2': {'forbidden': [], 'anagram_forbidden': True},
    'B1': {'forbidden': [], 'anagram_forbidden': True},
    'B2': {'forbidden': [], 'anagram_forbidden': True},
    'C1': {'forbidden': [], 'anagram_forbidden': True},
    'C2': {'forbidden': [], 'anagram_forbidden': True},
}

# Common words that don't need to be in vocabulary section
# Includes pronouns, conjunctions, prepositions, basic verbs, and high-frequency words
COMMON_WORDS = {
    # Pronouns
    'я', 'ти', 'він', 'вона', 'воно', 'ми', 'ви', 'вони',
    'мене', 'тебе', 'його', 'її', 'нас', 'вас', 'їх',
    'мені', 'тобі', 'йому', 'їй', 'нам', 'вам', 'їм',
    'мною', 'тобою', 'ним', 'нею', 'нами', 'вами', 'ними',
    'себе', 'собі', 'собою',
    # Demonstratives
    'це', 'то', 'той', 'та', 'те', 'ті', 'цей', 'ця', 'ці',
    'такий', 'така', 'таке', 'такі', 'сам', 'сама', 'само', 'самі',
    # Conjunctions
    'і', 'й', 'та', 'або', 'чи', 'а', 'але', 'бо', 'проте', 'однак', 'тому',
    'якщо', 'коли', 'поки', 'хоча', 'щоб', 'тому що', 'через те що',
    # Prepositions
    'в', 'у', 'на', 'з', 'із', 'зі', 'до', 'від', 'для', 'по', 'за', 'під', 'над',
    'про', 'при', 'між', 'через', 'біля', 'коло', 'після', 'перед', 'без', 'крім',
    # Verbs: бути (to be)
    'є', 'був', 'була', 'було', 'були', 'буде', 'будуть', 'бути', 'будемо', 'будете',
    # Verbs: мати (to have)
    'має', 'мав', 'мала', 'мало', 'мали', 'мати', 'маю', 'маєш', 'маємо', 'маєте', 'мають',
    # Verbs: робити (to do)
    'робить', 'робив', 'робила', 'робили', 'робити', 'роблю', 'робиш', 'робимо', 'робите', 'роблять',
    # Verbs: знати, хотіти, могти, йти, іти
    'знає', 'знав', 'знала', 'знати', 'знаю', 'знаєш', 'знаємо', 'знають',
    'хоче', 'хотів', 'хотіла', 'хотіти', 'хочу', 'хочеш', 'хочемо', 'хочете', 'хочуть',
    'може', 'міг', 'могла', 'могти', 'можу', 'можеш', 'можемо', 'можете', 'можуть',
    'іде', 'йде', 'йшов', 'йшла', 'йти', 'іти', 'іду', 'ідеш', 'ідемо', 'ідете', 'ідуть',
    # Verbs: говорити, казати, сказати
    'говорить', 'говорив', 'говорила', 'говорити', 'говорю', 'говориш', 'говоримо', 'говорять',
    'каже', 'казав', 'казала', 'казати', 'кажу', 'кажеш', 'кажемо', 'кажуть',
    'сказав', 'сказала', 'сказати', 'скажу', 'скажеш', 'скажемо', 'скажуть',
    # Verbs: бачити, чути, читати, писати
    'бачить', 'бачив', 'бачила', 'бачити', 'бачу', 'бачиш', 'бачимо', 'бачать',
    'чує', 'чув', 'чула', 'чути', 'чую', 'чуєш', 'чуємо', 'чують',
    'читає', 'читав', 'читала', 'читати', 'читаю', 'читаєш', 'читаємо', 'читають',
    'пише', 'писав', 'писала', 'писати', 'пишу', 'пишеш', 'пишемо', 'пишуть',
    # Particles & adverbs
    'так', 'ні', 'не', 'ще', 'вже', 'теж', 'також', 'лише', 'тільки', 'навіть',
    'дуже', 'тут', 'там', 'зараз', 'потім', 'завжди', 'ніколи', 'часто', 'рідко',
    'добре', 'погано', 'швидко', 'повільно', 'багато', 'мало', 'трохи',
    # Question words
    'що', 'як', 'де', 'коли', 'чому', 'хто', 'який', 'яка', 'яке', 'які',
    'скільки', 'куди', 'звідки', 'чий', 'чия', 'чиє', 'чиї',
    # Possessives
    'мій', 'моя', 'моє', 'мої', 'твій', 'твоя', 'твоє', 'твої',
    'його', 'її', 'наш', 'наша', 'наше', 'наші', 'ваш', 'ваша', 'ваше', 'ваші', 'їх', 'їхній',
    # Numbers
    'один', 'одна', 'одне', 'два', 'дві', 'три', 'чотири', 'п\'ять',
    'перший', 'перша', 'перше', 'другий', 'друга', 'друге', 'третій', 'третя', 'третє',
    # Common nouns
    'людина', 'люди', 'людей', 'людям', 'людьми',
    'час', 'часу', 'день', 'дня', 'рік', 'року', 'років',
    'місце', 'місця', 'слово', 'слова', 'слів',
    'річ', 'речі', 'справа', 'справи',
    # Common adjectives
    'великий', 'велика', 'велике', 'великі', 'малий', 'мала', 'мале', 'малі',
    'новий', 'нова', 'нове', 'нові', 'старий', 'стара', 'старе', 'старі',
    'добрий', 'добра', 'добре', 'добрі', 'поганий', 'погана', 'погане', 'погані',
    'інший', 'інша', 'інше', 'інші', 'весь', 'вся', 'все', 'всі',
    'кожний', 'кожна', 'кожне', 'кожні', 'цілий', 'ціла', 'ціле', 'цілі',
    # Ukrainian-specific high-frequency
    'українська', 'український', 'українське', 'українські', 'україна', 'україні', 'україни',
    'мова', 'мови', 'мову', 'мовою', 'мовна', 'мовний', 'мовне',
    # Common foods and household items (often used as examples)
    'сіль', 'солі', 'сіллю', 'цукор', 'цукру',
    # Common names
    'анна', 'ганна', 'іван', 'марія', 'петро', 'оксана', 'тарас',
    # Parsing artifact fragments (from Cyrillic letter splitting)
    'вропа', 'мать',  # artifacts from "Європа", "(mother)"
}

# Required frontmatter fields
REQUIRED_METADATA = [
    ('duration', r'duration:'),
    ('transliteration', r'transliteration:'),
    ('tags', r'tags:'),
    ('objectives', r'objectives:'),
    ('grammar', r'grammar:'),
    ('pedagogy', r'pedagogy:')
]

# AI contamination patterns to detect
AI_CONTAMINATION_PATTERNS = [
    r"Let's say",
    r"context suggests",
    r"Usually '.*' here",
    r'\bAI:',
    r'printed your printing',
    r"\bCorrection:",
    r"\bWait, actually",
    r"\bWait, no\b",
    r"\bOops\b",
    r"\bNote to self\b",
    r"\bAI note\b",
    r"\bignore this\b",
    r"\bdisregard this\b",
    r"\bLet's change\b",
    r"\bRewrite this\b",
    r"\bDraft:\b",
    r"\bCheck this\b",
    r"\bI made a mistake\b",
    r"\bSelf-correction\b",
    r"\bApologies\b",
    r"\bSorry,\b",
    r"\bAs an AI\b",
    r"\bMy previous\b",
    r"\bIn the previous\b",
]


def get_a1_immersion_range(module_num: int) -> tuple[int, int]:
    """Returns (min%, max%) for A1 based on module number."""
    if module_num <= 5:
        return (5, 15)  # Early modules need more English for Cyrillic learning
    elif module_num <= 10:
        return (15, 25)
    elif module_num <= 20:
        return (25, 35)
    else:
        return (35, 40)


def get_level_config(level_code: str, module_focus: str = None) -> dict:
    """Get configuration for a specific level, optionally with focus."""
    config_key = level_code
    if module_focus and level_code in ('B1', 'B2'):
        specific_key = f"{level_code}-{module_focus}"
        if specific_key in LEVEL_CONFIG:
            config_key = specific_key
    return LEVEL_CONFIG.get(config_key, LEVEL_CONFIG['A1'])


def get_word_target(level_code: str, module_num: int) -> int:
    """Get word target for a level, with A1 graduation."""
    config = get_level_config(level_code)
    if level_code == 'A1':
        if module_num <= 5:
            return 300
        elif module_num <= 10:
            return 500
        else:
            return 750
    return config['target_words']
