"""Configuration constants for richness scoring.

Contains module type mappings, scoring targets, weights, and regex marker
patterns used by the richness calculator. Separated from the main module
to improve maintainability and reduce file complexity.
"""

# Module type detection from pedagogy field
MODULE_TYPE_MAP = {
    # Grammar types
    'ttt': 'grammar',
    'ppp': 'grammar',
    'grammar': 'grammar',
    # Vocabulary types
    'vocabulary': 'vocabulary',
    'vocab': 'vocabulary',
    'lexical': 'vocabulary',
    # Cultural types
    'cultural': 'cultural',
    'culture': 'cultural',
    'cbi': 'content',
    # History types
    'history': 'history',
    'historical': 'history',
    'synthesis': 'history',
    # Phraseology types
    'phraseology': 'phraseology',
    'idioms': 'phraseology',
    # Biography types
    'biography': 'biography',
    'biographical': 'biography',
    # Academic types
    'academic': 'academic',
    'sociolinguistics': 'academic',
    # Style types
    'style': 'style',
    'stylistics': 'style',
    'creative production': 'style',
    # Professional types
    'professional': 'professional',
    'specialized': 'professional',
    # Skills types
    'skills': 'skills',
    'communication': 'skills',
    # Literature types
    'literature': 'literature',
    'literary': 'literature',
    'lit': 'literature',
    # Bridge types (Metalanguage)
    'bridge': 'bridge',
    'metalanguage': 'bridge',
    # Checkpoint types
    'checkpoint': 'checkpoint',
    'review': 'checkpoint',
    'assessment': 'checkpoint',
}

# Richness targets by MODULE TYPE (not just level)
MODULE_TYPE_TARGETS = {
    'grammar': {
        'engagement': 5,
        'examples': 24,
        'dialogues': 4,
        'cultural': 3,
        'realworld': 3,
        'questions': 5,
        'proverbs': 1,
        'visual': 3,
        'tables': 2,
        'threshold': 95,
    },
    'vocabulary': {
        'engagement': 4,
        'collocations': 20,
        'usage_examples': 15,
        'register_notes': 5,
        'cultural': 3,
        'visual': 3,
        'threshold': 95,
    },
    'cultural': {
        'engagement': 6,
        'authentic_refs': 3,
        'regional_refs': 5,
        'contemporary': 3,
        'cultural': 5,
        'visual': 4,
        'questions': 4,
        'threshold': 95,
    },
    'history': {
        'engagement': 6,
        'primary_sources': 3,
        'timeline_markers': 10,
        'decolonization': 2,
        'cultural': 4,
        'visual': 4,
        'questions': 3,
        'threshold': 95,
    },
    'phraseology': {
        'engagement': 4,
        'idiom_contexts': 15,
        'etymology': 5,
        'register_notes': 5,
        'contrastive': 5,
        'visual': 3,
        'threshold': 95,
    },
    'biography': {
        'engagement': 6,
        'primary_sources': 4,
        'quotes': 3,
        'timeline_markers': 8,
        'legacy': 2,
        'cultural': 4,
        'visual': 4,
        'questions': 3,
        'threshold': 95,
    },
    'academic': {
        'engagement': 5,
        'citations': 5,
        'data_refs': 3,
        'frameworks': 2,
        'case_studies': 2,
        'visual': 5,
        'questions': 4,
        'threshold': 95,
    },
    'style': {
        'engagement': 5,
        'exemplar_texts': 2,
        'model_answers': 3,
        'register_analysis': 5,
        'transformations': 2,
        'visual': 4,
        'threshold': 95,
    },
    'professional': {
        'engagement': 4,
        'domain_terms': 20,
        'document_examples': 3,
        'register_notes': 3,
        'scenarios': 3,
        'visual': 3,
        'threshold': 95,
    },
    'bridge': {
        'engagement': 5,
        'examples': 20,
        'cultural': 2,
        'realworld': 2,
        'questions': 4,
        'visual': 4,
        'tables': 2,
        'threshold': 90,
    },
    'literature': {
        'engagement': 4,
        'analysis_sections': 5,
        'literary_citations': 5,
        'historical_context': 3,
        'essays': 2,
        'resources': 3,
        'visual': 1,
        'threshold': 90,
    },
    'checkpoint': {
        'engagement': 3,
        'activity_types': 8,
        'review_sections': 3,
        'visual': 3,
        'threshold': 85,
    },
    'beginner': {
        'engagement': 2,    # Mar 2026: lowered from 3 — phonetics modules have fewer natural engagement points
        'examples': 8,      # Mar 2026: lowered from 12 — alphabet modules use letter lists not example sentences
        'dialogues': 0,     # Not applicable for phonetics
        'cultural': 0,      # Mar 2026: lowered from 1 — cultural content comes at M7+
        'realworld': 0,     # Mar 2026: lowered from 1 — phonetics is abstract
        'questions': 2,
        'tables': 0,        # Mar 2026: lowered from 1 — not all phonetics topics need tables
        'video_embeds': 2,
        'threshold': 60,    # Mar 2026: lowered from 70 — phonetics modules are inherently less rich
    },
    'skills': {
        'engagement': 5,
        'examples': 15,
        'realworld': 3,
        'visual': 2,
        'questions': 4,
        'threshold': 80,
    },
    'content': {
        'engagement': 5,
        'examples': 15,
        'cultural': 4,
        'realworld': 3,
        'visual': 4,
        'questions': 4,
        'threshold': 95,
    },
}

# Module type weights - what matters for each type
MODULE_TYPE_WEIGHTS = {
    'grammar': {
        'engagement': 0.15,
        'examples': 0.20,
        'dialogues': 0.15,
        'variety': 0.10,
        'cultural': 0.10,
        'realworld': 0.10,
        'questions': 0.05,
        'proverbs': 0.03,
        'visual': 0.05,
        'paragraph_var': 0.03,
        'tables': 0.04,
    },
    'history': {
        'engagement': 0.15,
        'primary_sources': 0.25,
        'timeline_markers': 0.15,
        'decolonization': 0.15,
        'cultural': 0.10,
        'visual': 0.10,
        'variety': 0.05,
        'paragraph_var': 0.05,
    },
    'biography': {
        'engagement': 0.15,
        'primary_sources': 0.20,
        'quotes': 0.15,
        'timeline_markers': 0.10,
        'legacy': 0.10,
        'cultural': 0.10,
        'visual': 0.10,
        'variety': 0.05,
        'paragraph_var': 0.05,
    },
    'style': {
        'engagement': 0.15,
        'exemplar_texts': 0.25,
        'model_answers': 0.20,
        'register_analysis': 0.15,
        'transformations': 0.10,
        'visual': 0.10,
        'variety': 0.05,
    },
    'literature': {
        'engagement': 0.15,
        'analysis_sections': 0.20,
        'literary_citations': 0.20,
        'historical_context': 0.15,
        'essays': 0.15,
        'resources': 0.10,
        'variety': 0.05,
    },
    'vocabulary': {
        'engagement': 0.15,
        'collocations': 0.25,
        'usage_examples': 0.20,
        'register_notes': 0.10,
        'cultural': 0.10,
        'visual': 0.10,
        'variety': 0.05,
        'paragraph_var': 0.05,
    },
    'cultural': {
        'engagement': 0.15,
        'cultural': 0.25,
        'authentic_refs': 0.15,
        'regional_refs': 0.15,
        'contemporary': 0.10,
        'visual': 0.10,
        'variety': 0.05,
        'paragraph_var': 0.05,
    },
    'checkpoint': {
        'engagement': 0.10,
        'activity_types': 0.25,
        'variety': 0.15,
        'cultural': 0.10,
        'visual': 0.10,
        'review_sections': 0.20,
        'paragraph_var': 0.10,
    },
    'beginner': {
        'engagement': 0.15,
        'examples': 0.20,
        'tables': 0.15,
        'video_embeds': 0.15,
        'variety': 0.10,
        'cultural': 0.05,
        'realworld': 0.05,
        'questions': 0.05,
        'visual': 0.05,
        'paragraph_var': 0.05,
    },
    'skills': {
        'engagement': 0.19,
        'examples': 0.25,
        'variety': 0.12,
        'realworld': 0.12,
        'visual': 0.06,
        'questions': 0.06,
        'paragraph_var': 0.06,
        'cultural': 0.12,
    },
    'phraseology': {
        'engagement': 0.15,
        'collocations': 0.25,
        'usage_examples': 0.20,
        'register_notes': 0.15,
        'cultural': 0.10,
        'variety': 0.10,
        'paragraph_var': 0.05,
    },
    'academic': {
        'engagement': 0.10,
        'citations': 0.25,
        'data_refs': 0.20,
        'questions': 0.15,
        'visual': 0.15,
        'variety': 0.10,
        'paragraph_var': 0.05,
    },
    'bridge': {
        'engagement': 0.20,
        'examples': 0.30,
        'cultural': 0.10,
        'realworld': 0.10,
        'visual': 0.10,
        'variety': 0.10,
        'paragraph_var': 0.05,
        'tables': 0.05,
    },
}

# Fallback weights for types not explicitly defined
DEFAULT_WEIGHTS = {
    'engagement': 0.15,
    'examples': 0.20,
    'dialogues': 0.15,
    'variety': 0.10,
    'cultural': 0.10,
    'realworld': 0.10,
    'questions': 0.05,
    'proverbs': 0.05,
    'visual': 0.05,
    'paragraph_var': 0.05,
}

# Ukrainian place names for cultural reference detection
UKRAINIAN_PLACES = {
    'Київ', 'Львів', 'Одеса', 'Харків', 'Дніпро', 'Запоріжжя',
    'Карпати', 'Крим', 'Буковина', 'Закарпаття', 'Волинь', 'Поділля',
    'Полтава', 'Чернігів', 'Суми', 'Вінниця', 'Житомир', 'Рівне',
    'Тернопіль', 'Івано-Франківськ', 'Чернівці', 'Ужгород', 'Луцьк',
    'Хрещатик', 'Майдан', 'Софія', 'Лавра', 'Андріївський',
    'Бесарабський', 'Подол', 'Поштова', 'Говерла', 'Дністер',
}

# Cultural terms and traditions
CULTURAL_TERMS = {
    'вишиванка', 'писанка', 'борщ', 'вареники', 'галушки', 'сало',
    'козак', 'гетьман', 'кобзар', 'бандура', 'трембіта', 'гопак',
    'калина', 'верба', 'рушник', 'вінок', 'коровай', 'весілля',
    'Різдво', 'Великдень', 'Купала', 'Маланка', 'колядки', 'щедрівки',
    'Шевченко', 'Франко', 'Леся', 'Котляревський', 'Сковорода',
    'Мазепа', 'Хмельницький', 'Грушевський', 'Бандера',
    'толока', 'вечорниці', 'обжинки', 'досвітки', 'колядування',
    'петриківський', 'Петриківка', 'косівська', 'опішнянська',
    'Нестор', 'літопис', 'Повість минулих літ',
    'Карпенко-Карий', 'Стельмах',
}

# Proverb/idiom markers
PROVERB_MARKERS = [
    r'кажуть[:\s]',
    r'приказка',
    r'прислів\'я',
    r'ідіома',
    r'вислів',
    r'«[^»]{10,}»',
    r'як кажуть',
    r'є вираз',
]

# Primary source markers (for history/biography)
PRIMARY_SOURCE_MARKERS = [
    r'📜',
    r'\[!quote\]',
    r'писав:',
    r'казав:',
    r'свідчить:',
    r'згадує:',
    r'у листі',
    r'у мемуарах',
    r'у спогадах',
    r'цитата:',
    r'документ',
    r'джерело:',
    r'«[^»]{30,}»',
]

# Timeline markers (for history/biography)
TIMELINE_MARKERS = [
    r'\b1[0-9]{3}\b',
    r'\b20[0-2][0-9]\b',
    r'\b[IVX]+\s*ст\.?',
    r'\b\d+\s*ст\.?',
    r'століття',
    r'епоха',
    r'період',
    r'доба',
    r'рік',
    r'роки',
    r'році',
]

# Decolonization markers
DECOLONIZATION_MARKERS = [
    r'імпер',
    r'колоніал',
    r'русифікац',
    r'національн',
    r'спротив',
    r'незалежн',
    r'автоном',
    r'самовизначен',
    r'деколоніз',
    r'українськ\w+\s+перспектив',
]

# Academic citation markers
CITATION_MARKERS = [
    r'\(\d{4}\)',
    r'за\s+\w+\s*\(\d{4}\)',
    r'дослідження\s+показ',
    r'згідно\s+з',
    r'науков\w+\s+джерел',
    r'статистик',
    r'\d+\s*%',
]

# Collocation markers (for vocabulary modules)
COLLOCATION_PATTERNS = [
    r'\+\s*[А-ЯІЇЄҐа-яіїєґ]+',
    r'типов\w+\s+сполучен',
    r'колокаці',
    r'вживається\s+з',
    r'поєднується\s+з',
]

# Register markers
REGISTER_MARKERS = [
    r'розмовн\w+',
    r'формальн\w+',
    r'офіційн\w+',
    r'нейтральн\w+',
    r'книжн\w+',
    r'літературн\w+',
    r'просторічн\w+',
    r'регістр',
    r'діалект\w+',
    r'архаїзм\w+',
    r'жаргон\w+',
    r'сленг\w+',
    r'суржик',
]

# Analysis section markers (for LIT modules)
ANALYSIS_MARKERS = [
    r'аналіз',
    r'інтерпретаці',
    r'символ\w+',
    r'образ\w+',
    r'мотив',
    r'тема',
    r'стиль\w+',
    r'поетик',
    r'наратив',
]

# Legacy markers (for biography)
LEGACY_MARKERS = [
    r'спадщина',
    r'вплив',
    r'значення',
    r'внесок',
    r'пам\'ят',
    r'вшануван',
    r'сьогодні',
    r'сучасн',
]
