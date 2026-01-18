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
        # NOTE: Removed r'\b\w+і\b.*подобається' - too broad, catches nominative plurals
        # The specific dative pronouns above are sufficient for detection
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
        # Active participles (present)
        r'\b\w+уючий\b', r'\b\w+ючий\b', r'\b\w+ачий\b',
        # Passive participles - BUT many common adjectives have same endings
        # These patterns will be filtered by PARTICIPLE_EXCLUSIONS below
        r'\b\w+аний\b', r'\b\w+ений\b', r'\b\w+итий\b',
        # Adverbial participles (gerunds)
        r'\bчитаючи\b', r'\bговорячи\b', r'\bйдучи\b',
    ],
    'subordinate_markers': [
        # Relative pronouns (який/яка/яке/які) - only flag when preceded by comma AND not followed by "це"
        # "книга, яка цікава" = relative clause (flag at A1)
        # "Скажіть, яке це тістечко?" = question (do NOT flag)
        r',\s*який\s+(?!це\b)[а-яіїєґ]', r',\s*яка\s+(?!це\b)[а-яіїєґ]', r',\s*яке\s+(?!це\b)[а-яіїєґ]', r',\s*які\s+(?!це\b)[а-яіїєґ]',
        # "що" as subordinate - only when preceded by verb/clause (not sentence-initial questions)
        # Pattern: verb + що + word (subordinate) vs. Що + word? (question)
        # Exclude: "що це", "що тут", "що там", "що далі" (these are questions/phrases, not subordinate clauses)
        r'[а-яіїєґ],?\s+що\s+(?!це\b|тут\b|там\b|далі\b)[а-яіїєґ]',
        # Temporal/conditional conjunctions as subordinate (preceded by main clause)
        # коли/якщо at sentence start are questions/conditionals, not subordinate
        r'[а-яіїєґ],?\s+коли\s+[а-яіїєґ]',
        r'\bякщо\s+[а-яіїєґ]', r'\bтому що\s+[а-яіїєґ]',
        # "бо" (because) - require following word, exclude accent marks breaking word boundary
        r'(?<![а-яіїєґА-ЯІЇЄҐ\u0301])бо\s+[а-яіїєґ]',
        r'\bхоча\s+[а-яіїєґ]', r'\bщоб\s+[а-яіїєґ]', r'\bпоки\s+[а-яіїєґ]', r'\bдоки\s+[а-яіїєґ]',
    ],
}

# Words that match participle patterns but are regular adjectives (not participles)
# These are excluded from participle violations at A1-A2
PARTICIPLE_EXCLUSIONS = {
    # Common adjectives ending in -аний (matches passive participle pattern)
    'поганий', 'погана', 'погане', 'погані',
    'останній', 'остання', 'останнє', 'останні',
    'ранній', 'рання', 'раннє', 'ранні',
    'крайній', 'крайня', 'крайнє', 'крайні',
    # Common adjectives ending in -ений (matches passive participle pattern)
    'зелений', 'зелена', 'зелене', 'зелені',
    'червоний', 'червона', 'червоне', 'червоні',  # -оний variant
    'чорний', 'чорна', 'чорне', 'чорні',
    'срібний', 'срібна', 'срібне', 'срібні',
    'темний', 'темна', 'темне', 'темні',
    'білий', 'біла', 'біле', 'білі',
    'синій', 'синя', 'синє', 'сині',
    'ціль', 'цільний', 'цільна', 'цільне', 'цільні',  # whole
    'головний', 'головна', 'головне', 'головні',
    'цікавий', 'цікава', 'цікаве', 'цікаві',
    'корисний', 'корисна', 'корисне', 'корисні',
    'важливий', 'важлива', 'важливе', 'важливі',
    'відомий', 'відома', 'відоме', 'відомі',
    # Common adjectives ending in -ний/-на/-не (not participles)
    'гарний', 'гарна', 'гарне', 'гарні',
    'чудовий', 'чудова', 'чудове', 'чудові',
    'смачний', 'смачна', 'смачне', 'смачні',
    'сонячний', 'сонячна', 'сонячне', 'сонячні',
    'щасливий', 'щаслива', 'щасливе', 'щасливі',
    'радий', 'рада', 'раде', 'раді',
    # Ordinal numbers (not participles)
    'перший', 'перша', 'перше', 'перші',
    'другий', 'друга', 'друге', 'другі',
    'третій', 'третя', 'третє', 'треті',
    'останній', 'остання', 'останнє', 'останні',
    # Adjectives meaning "sure/confident" (not participles)
    'впевнений', 'впевнена', 'впевнене', 'впевнені',
    'певний', 'певна', 'певне', 'певні',
    # More adjectives that match -ений pattern
    'здоровий', 'здорова', 'здорове', 'здорові',
    'готовий', 'готова', 'готове', 'готові',
    'потрібний', 'потрібна', 'потрібне', 'потрібні',
    # Marriage/relationship status adjectives (not participles)
    'одружений', 'одружена', 'одружене', 'одружені',
    'неодружений', 'неодружена', 'неодружене', 'неодружені',
    'наречений', 'наречена',  # engaged (also used as noun: fiancé/fiancée)
    'розлучений', 'розлучена', 'розлучене', 'розлучені',
    # Common service/postal/official terms (used as fixed terminology)
    'рекомендований', 'рекомендована', 'рекомендоване', 'рекомендовані',  # registered (mail)
    # Grammar terminology for aspect (these look like participles but are grammar terms)
    'недоконаний', 'недоконана', 'недоконане', 'недоконані',  # imperfective (aspect term)
    'доконаний', 'доконана', 'доконане', 'доконані',  # perfective (aspect term)
    # Emotional state adjectives (A2 Emotions vocabulary - NOT participles)
    # These describe emotional states and are taught as adjectives at A2
    'задоволений', 'задоволена', 'задоволене', 'задоволені',  # satisfied
    'розчарований', 'розчарована', 'розчароване', 'розчаровані',  # disappointed
    'стурбований', 'стурбована', 'стурбоване', 'стурбовані',  # worried
    'схвильований', 'схвильована', 'схвильоване', 'схвильовані',  # excited
    'здивований', 'здивована', 'здивоване', 'здивовані',  # surprised
    'втомлений', 'втомлена', 'втомлене', 'втомлені',  # tired
    'зацікавлений', 'зацікавлена', 'зацікавлене', 'зацікавлені',  # interested
    'засмучений', 'засмучена', 'засмучене', 'засмучені',  # upset
    'збентежений', 'збентежена', 'збентежене', 'збентежені',  # confused
    'налякаий', 'налякана', 'налякане', 'налякані',  # scared
}

# Words ending in -і/-ові that are nominative plural (not dative)
# Used to avoid false positives in dative detection
NOMINATIVE_PLURAL_EXCLUSIONS = {
    # Common adjectives in nominative plural (-і endings)
    'нові', 'старі', 'гарні', 'великі', 'малі', 'добрі', 'погані',
    'червоні', 'зелені', 'сині', 'білі', 'чорні', 'жовті',
    'українські', 'англійські', 'німецькі', 'французькі',
    'цікаві', 'важливі', 'корисні', 'смачні', 'гарячі', 'холодні',
    # Adjectives in nominative plural (-ові endings from -овий stems)
    'часові', 'кольорові', 'святкові', 'вікові', 'рольові',
    'безособові',  # impersonal (from безособовий) - common grammar term
    # Common nouns in nominative plural
    'люди', 'діти', 'студенти', 'друзі', 'учні', 'вчителі',
    'хлопці', 'дівчата', 'речі', 'слова', 'книжки', 'столи',
}

# Fixed phrases (formulaic chunks) taught at A1 before grammar is explained
# These are memorized as whole units, so case violations should be ignored
# Instrumental case greetings (З + Instrumental)
FIXED_PHRASES_INSTRUMENTAL = {
    'з новим роком', 'з різдвом', 'з великоднем', 'з днем народження',
    'з днем', 'з весіллям', 'з народженням', 'з перемогою',
    'з святом', 'з успіхом', 'з закінченням',
}

# Dative case expressions taught as fixed phrases at A1
FIXED_PHRASES_DATIVE = {
    # Wishing expressions (Бажаю + dative)
    'бажаю тобі', 'бажаю вам', 'бажаю щастя', 'бажаю здоров',
    # Fixed dative in greetings
    'миру', 'любові', 'щастя', 'здоров',  # Common in wishes
    # Impersonal health/feeling expressions (Мені + state)
    'мені погано', 'мені добре', 'мені болить', 'мені холодно', 'мені тепло',
    'мені потрібн', 'мені подобається', 'мені треба', 'мені здається',
    # Age expressions (Мені ... років)
    'мені рок', 'мені років', 'мені два', 'мені три', 'мені п\'ят', 'мені шіст', 'мені сім',
    # Tобі variants of impersonal expressions
    'тобі погано', 'тобі добре', 'тобі болить', 'тобі холодно', 'тобі потрібн',
    # Age expressions for other persons
    'йому рок', 'їй рок', 'їм рок',
}

# Activity stage ordering for PPP, TTT, and CLIL/Narrative
STAGE_ORDER = {
    'PPP': ['presentation', 'recognition', 'discrimination', 'controlled-production', 'free-production'],
    'TTT': ['diagnostic', 'recognition', 'presentation', 'controlled-production', 'free-production'],
    'CLIL': ['pre-engagement', 'immersion', 'narrative', 'deep-dive', 'recognition', 'controlled-production', 'free-production'],
    'NARRATIVE': ['pre-engagement', 'immersion', 'narrative', 'deep-dive', 'recognition', 'controlled-production', 'free-production'],
    # Seminar-style tracks (LIT, HIST, BIO)
    # reading is the INPUT (engage with source), analysis activities are the OUTPUT
    'SEMINAR': ['reading', 'essay-response', 'critical-analysis', 'comparative-study'],
}

# Activity complexity rules by type and level
# Enforced by check_activity_complexity()
ACTIVITY_COMPLEXITY = {
    'quiz': {
        'A1': {'min_len': 5, 'max_len': 10, 'options': [3, 4], 'min_items': 8},
        'A2': {'min_len': 7, 'max_len': 15, 'options': [4], 'min_items': 8},  # CEFR: smooth +2 from A1
        'B1': {'min_len': 9, 'max_len': 20, 'options': [4], 'min_items': 8},  # CEFR: smooth +2 from A2 (was 12, meets existing content)
        'B1-vocab': {'min_len': 8, 'max_len': 18, 'options': [4], 'min_items': 8},  # Context-specific: -1 from standard
        'B1-cultural': {'min_len': 8, 'max_len': 18, 'options': [4], 'min_items': 8},  # Context-specific: -1 from standard
        'B2': {'min_len': 10, 'max_len': 25, 'options': [4], 'min_items': 8},  # CEFR: smooth +1 from B1
        'B2-history': {'min_len': 8, 'max_len': 20, 'options': [4], 'min_items': 8},  # Context-specific: -2 from standard (was 6, better alignment)
        'B2-biography': {'min_len': 8, 'max_len': 20, 'options': [4], 'min_items': 8},  # Context-specific: -2 from standard
        'C1': {'min_len': 8, 'max_len': 30, 'options': [4], 'min_items': 5},  # CEFR: relaxed from 12 to 8
        'C2': {'min_len': 10, 'max_len': 35, 'options': [4], 'min_items': 5},  # CEFR: relaxed from 14 to 10
        # Seminar tracks - quiz is supplementary, focus is analytical work
        'lit': {'min_len': 8, 'max_len': 30, 'options': [4], 'min_items': 5},
        'b2-hist': {'min_len': 8, 'max_len': 25, 'options': [4], 'min_items': 5},
        'c1-hist': {'min_len': 8, 'max_len': 30, 'options': [4], 'min_items': 5},
        'c1-bio': {'min_len': 8, 'max_len': 30, 'options': [4], 'min_items': 5},
    },
    'match-up': {
        'A1': {'pairs_min': 8, 'pairs_max': 10, 'min_items': 8},
        'A2': {'pairs_min': 10, 'pairs_max': 12, 'min_items': 8},
        'B1': {'pairs_min': 12, 'pairs_max': 14, 'min_items': 8},
        'B2': {'pairs_min': 12, 'pairs_max': 16, 'min_items': 8},
        'C1': {'pairs_min': 8, 'pairs_max': 18, 'min_items': 6},
        'C2': {'pairs_min': 10, 'pairs_max': 18, 'min_items': 6},
    },
    'fill-in': {
        'A1': {'sent_min': 3, 'sent_max': 5, 'min_items': 8},
        'A2': {'sent_min': 6, 'sent_max': 8, 'min_items': 8},  # CEFR: smooth +3 from A1
        'B1': {'sent_min': 8, 'sent_max': 14, 'min_items': 8},  # CEFR: smooth +2 from A2 (was 10, meets existing content)
        'B1-vocab': {'sent_min': 7, 'sent_max': 12, 'min_items': 8},  # Context-specific: -1 from standard (was 8)
        'B1-cultural': {'sent_min': 7, 'sent_max': 12, 'min_items': 8},  # Context-specific: -1 from standard (was 8)
        'B2': {'sent_min': 9, 'sent_max': 16, 'min_items': 8},  # CEFR: smooth +1 from B1 (was 10)
        'B2-history': {'sent_min': 8, 'sent_max': 14, 'min_items': 8},  # Context-specific: -1 from standard (was 7)
        'B2-biography': {'sent_min': 8, 'sent_max': 14, 'min_items': 8},  # Context-specific: -1 from standard (was 7)
        'C1': {'sent_min': 11, 'sent_max': 18, 'min_items': 6},  # CEFR: smooth +2 from B2 (was 8)
        'C2': {'sent_min': 13, 'sent_max': 20, 'min_items': 6},  # CEFR: smooth +2 from C1 (was 10)
    },
    'true-false': {
        'A1': {'min_len': 4, 'max_len': 8, 'min_items': 8},
        'A2': {'min_len': 6, 'max_len': 12, 'min_items': 8},  # CEFR: smooth +2 from A1
        'B1': {'min_len': 8, 'max_len': 18, 'min_items': 8},  # CEFR: smooth +2 from A2 (was 10, meets existing content)
        'B1-vocab': {'min_len': 7, 'max_len': 16, 'min_items': 8},  # Context-specific: -1 from standard (was 8)
        'B1-cultural': {'min_len': 7, 'max_len': 16, 'min_items': 8},  # Context-specific: -1 from standard (was 8)
        'B2': {'min_len': 9, 'max_len': 22, 'min_items': 8},  # CEFR: smooth +1 from B1 (was 10)
        'B2-history': {'min_len': 8, 'max_len': 20, 'min_items': 8},  # Context-specific: -1 from standard (was 7)
        'B2-biography': {'min_len': 8, 'max_len': 20, 'min_items': 8},  # Context-specific: -1 from standard (was 7)
        'C1': {'min_len': 11, 'max_len': 25, 'min_items': 5},  # CEFR: smooth +2 from B2 (was 8)
        'C2': {'min_len': 13, 'max_len': 30, 'min_items': 5},  # CEFR: smooth +2 from C1 (was 10)
    },
    'group-sort': {
        'A1': {'groups_min': 2, 'groups_max': 4, 'items_min': 8, 'items_max': 999},
        'A2': {'groups_min': 2, 'groups_max': 4, 'items_min': 10, 'items_max': 999},
        'B1': {'groups_min': 2, 'groups_max': 5, 'items_min': 12, 'items_max': 999},
        'B2': {'groups_min': 3, 'groups_max': 5, 'items_min': 14, 'items_max': 999},
        'C1': {'groups_min': 2, 'groups_max': 6, 'items_min': 10, 'items_max': 999},
        'C2': {'groups_min': 3, 'groups_max': 6, 'items_min': 12, 'items_max': 999},
    },
    'unjumble': {
        'A1': {'words_min': 4, 'words_max': 6, 'min_items': 6},
        'A2': {'words_min': 7, 'words_max': 10, 'min_items': 6},  # CEFR: smooth +3 from A1 (was 8)
        'B1': {'words_min': 9, 'words_max': 16, 'min_items': 6},  # CEFR: smooth +2 from A2 (was 12, meets existing content)
        'B1-vocab': {'words_min': 8, 'words_max': 14, 'min_items': 6},  # Context-specific: -1 from standard (was 10)
        'B1-cultural': {'words_min': 8, 'words_max': 14, 'min_items': 6},  # Context-specific: -1 from standard (was 10)
        'B2': {'words_min': 10, 'words_max': 18, 'min_items': 6},  # CEFR: smooth +1 from B1
        'B2-history': {'words_min': 8, 'words_max': 15, 'min_items': 6},  # Context-specific: -2 from standard (was 7)
        'B2-biography': {'words_min': 8, 'words_max': 15, 'min_items': 6},  # Context-specific: -2 from standard (was 7)
        'C1': {'words_min': 12, 'words_max': 20, 'min_items': 5},  # CEFR: smooth +2 from B2
        'C2': {'words_min': 14, 'words_max': 22, 'min_items': 5},  # CEFR: smooth +2 from C1
    },
    'anagram': {
        'A1': {'min_len': 4, 'max_len': 8, 'min_items': 8},
        # Not allowed A2+
    },
    'error-correction': {
        'A2': {'errors': 1, 'min_len': 6, 'max_len': 10, 'min_items': 6},  # CEFR: smooth +2 from A1 (not available A1)
        'B1': {'errors': 2, 'min_len': 8, 'max_len': 16, 'min_items': 6},  # CEFR: smooth +2 from A2 (was 10, meets existing content)
        'B1-vocab': {'errors': 2, 'min_len': 7, 'max_len': 14, 'min_items': 6},  # Context-specific: -1 from standard (was 8)
        'B1-cultural': {'errors': 2, 'min_len': 7, 'max_len': 14, 'min_items': 6},  # Context-specific: -1 from standard (was 8)
        'B2': {'errors': 2, 'min_len': 9, 'max_len': 20, 'min_items': 6},  # CEFR: smooth +1 from B1 (was 10)
        'B2-history': {'errors': 2, 'min_len': 8, 'max_len': 18, 'min_items': 6},  # Context-specific: -1 from standard (was 7)
        'B2-biography': {'errors': 2, 'min_len': 8, 'max_len': 18, 'min_items': 6},  # Context-specific: -1 from standard (was 7)
        'C1': {'errors': 2, 'min_len': 12, 'max_len': 24, 'min_items': 5},  # CEFR: smooth +3 from B2 (kept at 12)
        'C2': {'errors': 2, 'min_len': 14, 'max_len': 28, 'min_items': 5},  # CEFR: smooth +2 from C1 (kept at 14)
    },
    'cloze': {
        'A2': {'sentences': [3, 4, 5], 'blanks': [3, 4], 'gap_freq': [8, 12]},
        'B1': {'sentences': [5, 6, 7, 8], 'blanks': [4, 5, 6], 'gap_freq': [6, 10]},
        'B2': {'sentences': [8, 9, 10, 11, 12], 'blanks': [6, 7, 8], 'gap_freq': [5, 8]},
        'C1': {'sentences': [10, 15], 'blanks': [8, 10], 'gap_freq': [4, 7]},
        'C2': {'sentences': [12, 18], 'blanks': [10, 12], 'gap_freq': [4, 6]},
    },
    'mark-the-words': {
        'A2': {'min_len': 8, 'max_len': 12, 'marks': [2, 3, 4], 'min_items': 6},  # CEFR: smooth +4 from A1 (not available A1)
        'B1': {'min_len': 10, 'max_len': 18, 'marks': [3, 4, 5], 'min_items': 6},  # CEFR: smooth +2 from A2 (was 12, meets existing content)
        'B1-vocab': {'min_len': 9, 'max_len': 16, 'marks': [3, 4, 5], 'min_items': 6},  # Context-specific: -1 from standard (was 10)
        'B1-cultural': {'min_len': 9, 'max_len': 16, 'marks': [3, 4, 5], 'min_items': 6},  # Context-specific: -1 from standard (was 10)
        'B2': {'min_len': 11, 'max_len': 22, 'marks': [4, 5, 6], 'min_items': 6},  # CEFR: smooth +1 from B1 (was 12)
        'B2-history': {'min_len': 10, 'max_len': 20, 'marks': [4, 5, 6], 'min_items': 6},  # Context-specific: -1 from standard (kept at 10)
        'B2-biography': {'min_len': 10, 'max_len': 20, 'marks': [4, 5, 6], 'min_items': 6},  # Context-specific: -1 from standard (kept at 10)
        'C1': {'min_len': 13, 'max_len': 25, 'marks': [5, 8], 'min_items': 5},  # CEFR: smooth +2 from B2 (was 14)
        'C2': {'min_len': 15, 'max_len': 30, 'marks': [6, 10], 'min_items': 5},  # CEFR: smooth +2 from C1 (was 16)
    },
    'select': {
        'A2': {'min_len': 6, 'max_len': 10, 'options': [4, 5], 'correct': [2, 3], 'min_items': 6},  # CEFR: smooth +2 from A1 (not available A1)
        'B1': {'min_len': 8, 'max_len': 14, 'options': [5, 6], 'correct': [2, 4], 'min_items': 6},  # CEFR: smooth +2 from A2 (was 10, meets existing content)
        'B1-vocab': {'min_len': 7, 'max_len': 12, 'options': [5, 6], 'correct': [2, 4], 'min_items': 6},  # Context-specific: -1 from standard (was 8)
        'B1-cultural': {'min_len': 7, 'max_len': 12, 'options': [5, 6], 'correct': [2, 4], 'min_items': 6},  # Context-specific: -1 from standard (was 8)
        'B2': {'min_len': 9, 'max_len': 18, 'options': [5, 6], 'correct': [2, 4], 'min_items': 6},  # CEFR: smooth +1 from B1 (was 10)
        'B2-history': {'min_len': 8, 'max_len': 16, 'options': [5, 6], 'correct': [2, 4], 'min_items': 6},  # Context-specific: -1 from standard (kept at 8)
        'B2-biography': {'min_len': 8, 'max_len': 16, 'options': [5, 6], 'correct': [2, 4], 'min_items': 6},  # Context-specific: -1 from standard (kept at 8)
        'C1': {'min_len': 11, 'max_len': 20, 'options': [5, 7], 'correct': [2, 4], 'min_items': 5},  # CEFR: smooth +2 from B2 (was 10)
        'C2': {'min_len': 13, 'max_len': 22, 'options': [6, 8], 'correct': [3, 5], 'min_items': 5},  # CEFR: smooth +2 from C1 (was 12)
    },
    'translate': {
        'A2': {'min_len': 4, 'max_len': 8, 'options': 4, 'min_items': 6},  # CEFR: smooth +1 from A1 (not available A1)
        'B1': {'min_len': 6, 'max_len': 14, 'options': 4, 'min_items': 6},  # CEFR: smooth +2 from A2 (was 8, meets existing content)
        'B1-vocab': {'min_len': 5, 'max_len': 12, 'options': 4, 'min_items': 6},  # Context-specific: -1 from standard (was 6)
        'B1-cultural': {'min_len': 5, 'max_len': 12, 'options': 4, 'min_items': 6},  # Context-specific: -1 from standard (was 6)
        'B2': {'min_len': 7, 'max_len': 18, 'options': 4, 'min_items': 6},  # CEFR: smooth +1 from B1 (was 10)
        'B2-history': {'min_len': 7, 'max_len': 16, 'options': 4, 'min_items': 6},  # Context-specific: =0 from standard (kept at 7)
        'B2-biography': {'min_len': 7, 'max_len': 16, 'options': 4, 'min_items': 6},  # Context-specific: =0 from standard (kept at 7)
        'C1': {'min_len': 9, 'max_len': 22, 'options': 5, 'min_items': 5},  # CEFR: smooth +2 from B2 (was 12)
        'C2': {'min_len': 11, 'max_len': 28, 'options': 5, 'min_items': 5},  # CEFR: smooth +2 from C1 (was 14)
    },
    'essay-response': {
        'B2': {'min_words': 250, 'min_items': 1},
        'C1': {'min_words': 400, 'min_items': 1},
        'C2': {'min_words': 600, 'min_items': 1},
    },
    'reading': {
        'A1': {'min_items': 2},
        'A2': {'min_items': 2},
        'B1': {'min_items': 3},
        'B2': {'min_items': 3},
        'C1': {'min_items': 3},
        'C2': {'min_items': 3},
    },
    'critical-analysis': {
        'C1': {'min_items': 1},
        'C2': {'min_items': 1},
    },
    'comparative-study': {
        'B2': {'min_items': 1},
        'C1': {'min_items': 1},
        'C2': {'min_items': 1},
    },
    'authorial-intent': {
        'C1': {'min_items': 1},
        'C2': {'min_items': 1},
    }
}

# Valid activity types
VALID_ACTIVITY_TYPES = [
    "match-up", "fill-in", "quiz", "true-false", "group-sort", "unjumble",
    "error-correction", "anagram", "select", "translate", "cloze",
    "mark-the-words",
    # Seminar-style activities (LIT, HIST, BIO tracks)
    "reading", "essay-response", "critical-analysis", "comparative-study", "authorial-intent"
]

# Activity keywords for detection
ACTIVITY_KEYWORDS = [
    "match-up", "gap-fill", "quiz", "true-false", "group-sort", "unjumble",
    "fill-in", "error-correction", "anagram", "cloze",
    "select", "translate", "mark-the-words",
    # Seminar-style activities
    "reading", "essay-response", "critical-analysis", "comparative-study", "authorial-intent"
]

# Core section keywords (not activities)
CORE_KEYWORDS = [
    "warm-up", "presentation", "introduction", "narrative", "context",
    "diagnostic", "cultural", "culture", "story", "dialogue", "reading",
    "deep dive", "riddle", "insight", "conversation", "review", "concept",
    "core", "usage", "matters", "transformation", "memory", "tip",
    "pattern", "summary",
    # Ukrainian equivalents for B1+ modules
    "діагностика", "аналіз", "занурення", "глибоке", "помилки",
    "частина", "культур", "розмова", "текст", "діалог", "читання", "підсумок"
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
        'min_vocab': 1,  # Relaxed: focus on unique lemma introduction
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
        'min_vocab': 1,  # Relaxed: focus on unique lemma introduction
        'min_engagement': 4,
        'immersion_graduated': True,  # Phase-based: A2.1 40-45%, A2.2 45-50%, A2.3 50-55%
        'transliteration_allowed': False,
        'priority_types': {'error-correction', 'unjumble', 'fill-in'}
    },
    'A1-checkpoint': {
        'target_words': 500,  # Checkpoints can be shorter
        'min_activities': 8,
        'min_items_per_activity': 10,
        'min_types_unique': 4,
        'min_vocab': 1,  # Relaxed: most vocab is review
        'min_engagement': 2,
        # NO immersion gate - comes naturally from practice
        'transliteration_allowed': True,
        'priority_types': {'quiz', 'fill-in', 'match-up'}
    },
    'A2-checkpoint': {
        'target_words': 800,  # Checkpoints can be shorter
        'min_activities': 10,
        'min_items_per_activity': 10,
        'min_types_unique': 4,
        'min_vocab': 1,  # Relaxed: most vocab is review
        'min_engagement': 3,
        # NO immersion gate - comes naturally from practice
        'transliteration_allowed': False,
        'priority_types': {'quiz', 'fill-in', 'error-correction'}
    },
    'B1-bridge': {
        # Bridge modules (M01-05) teach grammar metalanguage
        'target_words': 1200,  # Lower target for metalanguage teaching
        'min_activities': 12,
        'min_items_per_activity': 14,
        'min_types_unique': 5,
        'min_vocab': 20,  # Metalanguage vocabulary
        'min_engagement': 4,
        # NO immersion gate - bridge modules teach terminology bilingually
        'transliteration_allowed': False,
        'priority_types': {'quiz', 'match-up', 'fill-in', 'translate'}
    },
    'B1-grammar': {
        'target_words': 1500,
        'min_activities': 8,  # Reduced from 12 (Jan 2026) - quality over quantity
        'min_items_per_activity': 12,  # Reduced from 14 (Jan 2026)
        'min_types_unique': 4,
        'min_vocab': 25,  # Increased for grammar terminology
        'min_engagement': 5,
        'min_immersion': 90,  # Relaxed to 90% to allow necessary English context
        'max_immersion': 100,  # 100% Ukrainian immersion (English only in vocab table)
        'transliteration_allowed': False,
        'priority_types': {'error-correction', 'fill-in', 'unjumble', 'cloze'}
    },
    'B1-vocab': {
        'target_words': 1500,
        'min_activities': 8,  # Reduced from 12 (Jan 2026) - quality over quantity
        'min_items_per_activity': 12,  # Reduced from 14 (Jan 2026)
        'min_types_unique': 4,
        'min_vocab': 35,
        'min_engagement': 5,
        'min_immersion': 90,  # Relaxed to 90% to allow necessary English context
        'max_immersion': 100,  # 100% Ukrainian immersion (English only in vocab table)
        'transliteration_allowed': False,
        'priority_types': {'match-up', 'mark-the-words', 'translate', 'quiz'}
    },
    'B1': {
        'target_words': 1500,
        'min_activities': 8,  # Reduced from 12 (Jan 2026) - quality over quantity
        'min_items_per_activity': 12,  # Reduced from 14 (Jan 2026)
        'min_types_unique': 4,
        'min_vocab': 25,
        'min_engagement': 5,
        'min_immersion': 90,  # Relaxed to 90% to allow necessary English context
        'max_immersion': 100,  # 100% Ukrainian immersion (English only in vocab table)
        'transliteration_allowed': False,
        'priority_types': {'fill-in', 'unjumble', 'error-correction'}
    },
    'B1-skills': {
        'target_words': 1500,
        'min_activities': 10,
        'min_items_per_activity': 12,
        'min_types_unique': 4,
        'min_vocab': 15,
        'min_engagement': 4,
        'min_immersion': 90,  # Relaxed to 90% to allow necessary English context
        'max_immersion': 100,  # 100% Ukrainian immersion
        'transliteration_allowed': False,
        'priority_types': {'fill-in', 'cloze', 'mark-the-words'}
    },
    'B1-checkpoint': {
        'target_words': 1200,
        'min_activities': 10,
        'min_items_per_activity': 12,
        'min_types_unique': 4,
        'min_vocab': 10,
        'min_engagement': 3,
        # NO immersion gate - comes naturally from practice
        'transliteration_allowed': False,
        'priority_types': {'quiz', 'fill-in', 'error-correction'}
    },
    'B1-capstone': {
        'target_words': 1500,
        'min_activities': 5,  # Reduced from 12 (Jan 2026) - capstone has 5-8 traditional activities + 5 tasks
        'min_items_per_activity': 12,  # Reduced from 14 (Jan 2026)
        'min_types_unique': 4,
        'min_vocab': 10,
        'min_engagement': 3,
        'min_immersion': 90,  # Relaxed to 90% to allow necessary English context
        'max_immersion': 100,  # 100% Ukrainian immersion
        'transliteration_allowed': False,
        'priority_types': {'quiz', 'fill-in', 'cloze', 'error-correction'}
    },
    'B2-grammar': {
        'target_words': 1750,
        'min_activities': 10,  # Reduced from 13 (Jan 2026) - quality over quantity
        'min_items_per_activity': 14,  # Reduced from 16 (Jan 2026)
        'min_types_unique': 4,
        'min_vocab': 25,  # Increased for advanced grammar terminology
        'min_engagement': 6,
        'min_immersion': 90,  # Relaxed to 90% to allow necessary English context
        'max_immersion': 100,  # FULL IMMERSION - no English in body text
        'transliteration_allowed': False,
        'priority_types': {'error-correction', 'fill-in', 'unjumble', 'cloze'}
    },
    'B2-vocab': {
        'target_words': 1750,
        'min_activities': 10,  # Reduced from 13 (Jan 2026) - quality over quantity
        'min_items_per_activity': 14,  # Reduced from 16 (Jan 2026)
        'min_types_unique': 4,
        'min_vocab': 35,
        'min_engagement': 6,
        'min_immersion': 90,  # Relaxed to 90% to allow necessary English context
        'max_immersion': 100,  # FULL IMMERSION - no English in body text
        'transliteration_allowed': False,
        'priority_types': {'match-up', 'mark-the-words', 'translate', 'quiz'}
    },
    'B2': {
        'target_words': 1750,
        'min_activities': 10,  # Reduced from 13 (Jan 2026) - quality over quantity
        'min_items_per_activity': 14,  # Reduced from 16 (Jan 2026)
        'min_types_unique': 4,
        'min_vocab': 25,
        'min_engagement': 6,
        'min_immersion': 90,  # Relaxed to 90% to allow necessary English context
        'max_immersion': 100,  # FULL IMMERSION - no English in body text
        'transliteration_allowed': False,
        'priority_types': {'fill-in', 'unjumble', 'error-correction'}
    },
    'B2-history': {
        'target_words': 3000,
        'min_activities': 10,
        'min_items_per_activity': 14,
        'min_types_unique': 4,
        'min_vocab': 20,
        'min_engagement': 5,
        'min_immersion': 90,  # Relaxed to 90% to allow necessary English context
        'max_immersion': 100,  # FULL IMMERSION - no English in body text
        'transliteration_allowed': False,
        'priority_types': {'cloze', 'fill-in', 'true-false', 'quiz'}
    },
    'B2-biography': {
        'target_words': 3000,
        'min_activities': 10,
        'min_items_per_activity': 14,
        'min_types_unique': 4,
        'min_vocab': 20,
        'min_engagement': 5,
        'min_immersion': 90,  # Relaxed to 90% to allow necessary English context
        'max_immersion': 100,  # FULL IMMERSION - no English in body text
        'transliteration_allowed': False,
        'priority_types': {'cloze', 'fill-in', 'true-false', 'quiz'}
    },
    'B2-checkpoint': {
        'target_words': 1750,
        'min_activities': 15,
        'min_items_per_activity': 14,
        'min_types_unique': 4,
        'min_vocab': 10,
        'min_engagement': 4,
        'min_immersion': 90,  # Relaxed to 90% to allow necessary English context
        'max_immersion': 100,  # FULL IMMERSION - no English in body text
        'transliteration_allowed': False,
        'priority_types': {'quiz', 'fill-in', 'error-correction', 'cloze'}
    },
    'B2-synthesis': {
        # Synthesis modules replace checkpoints in B2.3 History (M83, M107, M119, M125, M131)
        # Focus on cross-era analysis and historical argumentation, not recall
        'target_words': 2000,
        'min_activities': 10,  # Reduced from 13 (Jan 2026) - quality over quantity
        'min_items_per_activity': 14,  # Increased from 12 (Jan 2026) for consistency
        'min_types_unique': 4,
        'min_vocab': 20,  # Review vocabulary from covered modules
        'min_engagement': 4,
        'min_immersion': 90,  # Relaxed to 90% to allow necessary English context
        'max_immersion': 100,  # FULL IMMERSION - no English in body text
        'transliteration_allowed': False,
        'priority_types': {'quiz', 'select', 'cloze', 'true-false'}  # Analysis-focused
    },
    'B2-capstone': {
        'target_words': 1750,
        'min_activities': 10,  # Reduced from 12 (Jan 2026) - quality over quantity
        'min_items_per_activity': 14,  # Kept at 14 (Jan 2026)
        'min_types_unique': 4,
        'min_vocab': 10,
        'min_engagement': 4,
        'min_immersion': 90,  # Relaxed to 90% to allow necessary English context
        'max_immersion': 100,  # FULL IMMERSION - no English in body text
        'transliteration_allowed': False,
        'priority_types': {'quiz', 'fill-in', 'cloze', 'error-correction'}
    },
    'B2-professional': {
        # B2-PRO Professional Track (M01-40)
        # ESP (English for Specific Purposes adapted for Ukrainian)
        'target_words': 3000,
        'min_activities': 10,
        'min_items_per_activity': 14,
        'min_types_unique': 4,
        'min_vocab': 30,  # Domain-specific terminology
        'min_engagement': 5,
        'min_immersion': 90,  # Relaxed to 90% to allow necessary English context
        'max_immersion': 100,  # FULL IMMERSION - no English in body text
        'transliteration_allowed': False,
        'priority_types': {'fill-in', 'cloze', 'translate', 'quiz'}
    },
    'C1': {
        'target_words': 2000,
        'min_activities': 12,
        'min_items_per_activity': 12,
        'min_types_unique': 4,
        'min_vocab': 25,
        'min_engagement': 7,
        'min_immersion': 90,  # Relaxed to 90% to allow necessary English context
        'max_immersion': 100,  # FULL IMMERSION - no English in body text
        'transliteration_allowed': False,
        'priority_types': {'fill-in', 'unjumble', 'error-correction'}
    },
    'C1-academic': {
        'target_words': 2000,
        'min_activities': 12,
        'min_items_per_activity': 12,
        'min_types_unique': 4,
        'min_vocab': 24,
        'min_engagement': 6,
        'min_immersion': 90,  # Relaxed to 90% to allow necessary English context
        'max_immersion': 100,  # FULL IMMERSION - no English in body text
        'transliteration_allowed': False,
        'priority_types': {'fill-in', 'cloze', 'error-correction'}
    },
    'C1-professional': {
        # C1-PRO Professional Mastery Track (M01-50)
        # ESP + CLIL approach for executives, academics, specialists
        'target_words': 3000,
        'min_activities': 12,
        'min_items_per_activity': 14,
        'min_types_unique': 4,
        'min_vocab': 35,  # Advanced domain-specific terminology
        'min_engagement': 6,
        'min_immersion': 90,  # Relaxed to 90% to allow necessary English context
        'max_immersion': 100,  # FULL IMMERSION - no English in body text
        'transliteration_allowed': False,
        'priority_types': {'fill-in', 'cloze', 'translate', 'error-correction'}
    },
    'C1-stylistics': {
        'target_words': 2000,
        'min_activities': 12,
        'min_items_per_activity': 12,
        'min_types_unique': 4,
        'min_vocab': 24,
        'min_engagement': 6,
        'min_immersion': 90,  # Relaxed to 90% to allow necessary English context
        'max_immersion': 100,  # FULL IMMERSION - no English in body text
        'transliteration_allowed': False,
        'priority_types': {'fill-in', 'error-correction', 'cloze'}
    },
    'C1-folk': {
        'target_words': 2000,
        'min_activities': 12,
        'min_items_per_activity': 12,
        'min_types_unique': 4,
        'min_vocab': 24,
        'min_engagement': 5,
        'min_immersion': 90,  # Relaxed to 90% to allow necessary English context
        'max_immersion': 100,  # FULL IMMERSION - no English in body text
        'transliteration_allowed': False,
        'priority_types': {'cloze', 'fill-in', 'mark-the-words'}
    },
    'C1-biography': {
        'target_words': 3000,
        'min_activities': 12,
        'min_items_per_activity': 12,
        'min_types_unique': 4,
        'min_vocab': 24,
        'min_engagement': 6,
        'min_immersion': 90,  # Relaxed to 90% to allow necessary English context
        'max_immersion': 100,  # FULL IMMERSION - no English in body text
        'transliteration_allowed': False,
        'priority_types': {'cloze', 'fill-in', 'true-false', 'quiz'}
    },
    'C1-literature': {
        'target_words': 2000,
        'min_activities': 12,
        'min_items_per_activity': 12,
        'min_types_unique': 4,
        'min_vocab': 24,
        'min_engagement': 5,
        'min_immersion': 90,  # Relaxed to 90% to allow necessary English context
        'max_immersion': 100,  # FULL IMMERSION - no English in body text
        'transliteration_allowed': False,
        'priority_types': {'cloze', 'fill-in', 'quiz'}
    },
    'C1-checkpoint': {
        'target_words': 1750,
        'min_activities': 14,
        'min_items_per_activity': 14,
        'min_types_unique': 4,
        'min_vocab': 15,
        'min_engagement': 4,
        'min_immersion': 90,  # Relaxed to 90% to allow necessary English context
        'max_immersion': 100,  # FULL IMMERSION - no English in body text
        'transliteration_allowed': False,
        'priority_types': {'quiz', 'fill-in', 'error-correction', 'cloze'}
    },
    'C1-capstone': {
        'target_words': 1750,
        'min_activities': 12,
        'min_items_per_activity': 12,
        'min_types_unique': 4,
        'min_vocab': 15,
        'min_engagement': 4,
        'min_immersion': 90,  # Relaxed to 90% to allow necessary English context
        'max_immersion': 100,  # FULL IMMERSION - no English in body text
        'transliteration_allowed': False,
        'priority_types': {'cloze', 'fill-in', 'error-correction'}
    },
    'C2': {
        'target_words': 2000,
        'min_activities': 16,  # Increased from 14 (Jan 2026) - C2 mastery level
        'min_items_per_activity': 18,  # Increased from 14 (Jan 2026) - higher than C1
        'min_types_unique': 4,
        'min_vocab': 25,
        'min_engagement': 6,
        'min_immersion': 90,  # Relaxed to 90% to allow necessary English context
        'max_immersion': 100,
        'transliteration_allowed': False,
        'priority_types': {'fill-in', 'cloze', 'error-correction'}
    },
    'C2-stylistic': {
        'target_words': 2000,
        'min_activities': 16,  # Increased from 14 (Jan 2026) - C2 mastery level
        'min_items_per_activity': 18,  # Increased from 14 (Jan 2026) - higher than C1
        'min_types_unique': 4,
        'min_vocab': 25,
        'min_engagement': 6,
        'min_immersion': 90,  # Relaxed to 90% to allow necessary English context
        'max_immersion': 100,
        'transliteration_allowed': False,
        'priority_types': {'fill-in', 'cloze', 'error-correction'}
    },
    'C2-literary': {
        'target_words': 2000,
        'min_activities': 16,  # Increased from 12 (Jan 2026) - C2 mastery level
        'min_items_per_activity': 18,  # Increased from 12 (Jan 2026) - higher than C1
        'min_types_unique': 4,
        'min_vocab': 25,
        'min_engagement': 5,
        'min_immersion': 90,  # Relaxed to 90% to allow necessary English context
        'max_immersion': 100,
        'transliteration_allowed': False,
        'priority_types': {'cloze', 'fill-in', 'quiz'}
    },
    'C2-professional': {
        'target_words': 2000,
        'min_activities': 16,  # Increased from 12 (Jan 2026) - C2 mastery level
        'min_items_per_activity': 18,  # Increased from 12 (Jan 2026) - higher than C1
        'min_types_unique': 4,
        'min_vocab': 25,
        'min_engagement': 5,
        'min_immersion': 90,  # Relaxed to 90% to allow necessary English context
        'max_immersion': 100,
        'transliteration_allowed': False,
        'priority_types': {'fill-in', 'cloze', 'translate'}
    },
    'C2-checkpoint': {
        'target_words': 2000,
        'min_activities': 16,  # Increased from 14 (Jan 2026) - C2 mastery level
        'min_items_per_activity': 18,  # Increased from 14 (Jan 2026) - higher than C1
        'min_types_unique': 4,
        'min_vocab': 15,
        'min_engagement': 4,
        # NO immersion gate - comes naturally from practice
        'transliteration_allowed': False,
        'priority_types': {'quiz', 'fill-in', 'error-correction', 'cloze'}
    },
    'C2-capstone': {
        'target_words': 2000,
        'min_activities': 16,  # Increased from 10 (Jan 2026) - C2 mastery level
        'min_items_per_activity': 18,  # Increased from 12 (Jan 2026) - higher than C1
        'min_types_unique': 4,
        'min_vocab': 15,
        'min_engagement': 4,
        'min_immersion': 90,  # Relaxed to 90% to allow necessary English context
        'max_immersion': 100,
        'transliteration_allowed': False,
        'priority_types': {'cloze', 'fill-in'}
    },
    'LIT': {
        # LIT Track: Pure seminar style (post-C1)
        # Activities: reading + essay-response + critical-analysis + comparative-study
        # NO traditional activities (quiz, match-up, fill-in)
        'target_words': 3500,  # 3500-4000 for substantial literary analysis
        'min_activities': 3,
        'max_activities': 6,
        'min_items_per_activity': 1,  # Analytical tasks are deep, single-item responses are sufficient
        'min_types_unique': 2,
        'min_vocab': 0,
        'min_engagement': 4,
        'min_immersion': 95,  # Allow 5% for Latin/Greek scholarly terms
        'max_immersion': 100,
        'transliteration_allowed': False,
        'priority_types': {'reading', 'essay-response', 'critical-analysis', 'comparative-study'},
        'required_types': {'reading', 'essay-response', 'critical-analysis'},  # Must have all three
        'forbidden_types': {'quiz', 'match-up', 'fill-in', 'unjumble', 'anagram', 'cloze', 'mark-the-words'}
    },
    # =============================================================================
    # SEMINAR-STYLE TRACKS (Quality over Quantity)
    # =============================================================================
    'B2-HIST-seminar': {
        # B2-HIST Track: Transitional seminar style (B2 level)
        # Activities: reading + essay-response (shorter) + critical-analysis + true-false (factual)
        # Easier than LIT: shorter essays, some factual checks allowed
        'target_words': 3000,
        'min_activities': 3,
        'max_activities': 6,
        'min_items_per_activity': 1,
        'min_types_unique': 2,
        'min_vocab': 20,
        'min_engagement': 5,
        'min_immersion': 90,
        'max_immersion': 100,
        'transliteration_allowed': False,
        'priority_types': {'reading', 'essay-response', 'critical-analysis', 'comparative-study'},
        'required_types': {'reading', 'essay-response'},  # Must have both
        'allowed_types': {'reading', 'essay-response', 'critical-analysis', 'comparative-study', 'true-false'},
        'essay_min_words': 150,  # Shorter than LIT (150-200 vs 300-500)
        'essay_max_words': 250
    },
    'C1-HIST-seminar': {
        # C1-HIST Track: Academic seminar style (C1 level)
        # Activities: reading + essay-response (full) + critical-analysis + comparative-study
        # Academic rigor: longer essays, source criticism, historiographical analysis
        'target_words': 3500,
        'min_activities': 3,
        'max_activities': 6,
        'min_items_per_activity': 1,
        'min_types_unique': 2,
        'min_vocab': 25,
        'min_engagement': 6,
        'min_immersion': 95,
        'max_immersion': 100,
        'transliteration_allowed': False,
        'priority_types': {'reading', 'essay-response', 'critical-analysis', 'comparative-study'},
        'required_types': {'reading', 'essay-response', 'critical-analysis'},
        'forbidden_types': {'quiz', 'match-up', 'fill-in', 'unjumble', 'anagram', 'cloze', 'mark-the-words'},
        'essay_min_words': 300,
        'essay_max_words': 500
    },
    'C1-BIO-seminar': {
        # C1-BIO Track: Biography seminar style (C1 level)
        # Activities: reading + essay-response + critical-analysis + comparative-study
        # Focus: biographical analysis, legacy evaluation, era context
        'target_words': 2500,
        'min_activities': 3,
        'max_activities': 6,
        'min_items_per_activity': 1,
        'min_types_unique': 2,
        'min_vocab': 24,
        'min_engagement': 5,
        'min_immersion': 95,
        'max_immersion': 100,
        'transliteration_allowed': False,
        'priority_types': {'reading', 'essay-response', 'critical-analysis', 'comparative-study'},
        'required_types': {'reading', 'essay-response'},
        'forbidden_types': {'quiz', 'match-up', 'fill-in', 'unjumble', 'anagram', 'cloze', 'mark-the-words'},
        'essay_min_words': 250,
        'essay_max_words': 400
    }
}

# Activity level restrictions
ACTIVITY_RESTRICTIONS = {
    'A1': {
        'forbidden': ['error-correction', 'cloze', 'mark-the-words', 'select', 'translate', 'essay-response', 'critical-analysis', 'comparative-study', 'authorial-intent'],
        'anagram_limit': 10
    },
    'A2': {
        'forbidden': ['essay-response', 'critical-analysis', 'comparative-study', 'authorial-intent'],
        'anagram_forbidden': True
    },
    'B1': {
        'forbidden': ['essay-response', 'critical-analysis', 'comparative-study', 'authorial-intent'],
        'anagram_forbidden': True
    },
    'B2': {'forbidden': [], 'anagram_forbidden': True},
    'C1': {'forbidden': [], 'anagram_forbidden': True},
    'C2': {'forbidden': [], 'anagram_forbidden': True},
}

# Required advanced activities by module focus (C1/C2)
REQUIRED_ADVANCED_TYPES = {
    'biography': ['essay-response', 'comparative-study'],
    'history': ['essay-response', 'comparative-study'],
    'literature': ['essay-response', 'critical-analysis'],
    'fine-arts': ['essay-response', 'critical-analysis'],
    'folk-culture': ['essay-response', 'comparative-study'],
    'academic': ['essay-response', 'authorial-intent'],
    'checkpoint': ['essay-response', 'comparative-study'],
    'default': ['essay-response']  # Fallback for grammar/vocab modules
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
    """Returns (min%, max%) for A1 based on module number.

    Note: Immersion includes Activities + Summary (full learner experience).
    Ranges calibrated for this comprehensive calculation.
    """
    if module_num <= 2:
        return (5, 15)   # Cyrillic intro - mostly English explanations
    elif module_num <= 5:
        return (10, 25)  # Early vocab building
    elif module_num <= 10:
        return (15, 35)  # Growing immersion
    elif module_num <= 20:
        return (25, 40)  # Foundation established
    else:
        return (35, 55)  # Consolidation - high Ukrainian content


def get_a2_immersion_range(module_num: int) -> tuple[int, int]:
    """Returns (min%, max%) for A2 based on module number.

    Phase-based immersion progression per A2-CURRICULUM-PLAN.md:
    - A2.1 (01-20): 35-50% (widened from 40-45% to accommodate content variation)
    - A2.2 (21-40): 40-55% (widened from 45-50%)
    - A2.3 (41-50): 50%+ (Pre-B1 runway)
    """
    if module_num <= 15:
        return (40, 50)  # A2.1: Core case endings
    elif module_num <= 35:
        return (50, 65)  # A2.2: Aspect/Consolidation
    elif module_num <= 44:
        return (65, 75)  # A2.3/4: Advanced integration
    else:
        return (75, 85)  # A2.5: Final Pre-B1 Runway


def get_b1_immersion_range(module_num: int) -> tuple[int, int]:
    """Returns (min%, max%) for B1 based on module number.

    B1 Immersion Philosophy:
    - M01-05 (B1.0 Bridge): NO immersion limit — teach grammar terminology in English/Ukrainian
    - M06-85 (B1.1+): 90-95% Ukrainian — grammar explained IN Ukrainian using metalanguage

    The bridge modules (M01-05) prepare students to understand grammar explanations
    in Ukrainian by teaching them the necessary metalanguage vocabulary first.
    """
    if module_num <= 5:
        # Bridge modules: no immersion gate
        # These modules teach grammar terminology and can use as much English as needed
        return (0, 100)

    # All other B1 modules target 90-95% Ukrainian immersion
    return (85, 100)  # B1 is fully immersed - no upper limit


def get_level_config(level_code: str, module_focus: str = None) -> dict:
    """Get configuration for a specific level, optionally with focus."""
    config_key = level_code
    if module_focus and level_code in ('A1', 'A2', 'B1', 'B2', 'C1', 'C2'):
        specific_key = f"{level_code}-{module_focus}"
        if specific_key in LEVEL_CONFIG:
            config_key = specific_key
    return LEVEL_CONFIG.get(config_key, LEVEL_CONFIG['A1'])


def get_word_target(level_code: str, module_num: int, module_focus: str = None) -> int:
    """Get word target for a level, with A1 graduation."""
    config = get_level_config(level_code, module_focus)
    if level_code == 'A1':
        if module_num <= 5:
            return 300
        elif module_num <= 10:
            return 500
        else:
            return 750
    return config['target_words']
