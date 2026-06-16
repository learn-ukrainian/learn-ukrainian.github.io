"""§6 decolonization moat — active-participle / calque correction dataset.

Authority data for the Word Atlas §6 stylistic-warning layer (#3098). The
moat directly strengthens Ukrainian against Russian interference: the
``-уч-/-юч-/-ач-/-яч-`` active *present participle* used attributively is a
classic Russian calque (рос. ``действующий``, ``окружающий``) that standard
Ukrainian avoids, preferring agent nouns (``-ач``, ``-ник``, ``-альник``),
relative clauses (``той, що …``), or relational adjectives.

CRITICAL — this is NOT a blanket "-учий is wrong" rule. Many ``-уч-/-юч-``
words have lexicalised into legitimate adjectives of *permanent quality* that
have lost the ability to govern a noun (``лежачий камінь``, ``квітучий сад``,
``блискучий``, ``пекучий``, ``правлячий режим``). Antonenko-Davydovych
(«Як ми говоримо», p. 145) draws the line precisely: a ``-уч-`` word is a
calque only when it functions as an active participle (expresses an action,
can govern a noun); it is correct when it is an adjective of constant quality.

Beyond the participle slice this module also carries the §6 *lexical / phrasal
register calques* curated from the grok-swarm extension (#3098): phrasal Russisms
(``точка зору`` → ``погляд``) and — critically — POLYSEMES that are authentic
Ukrainian in one sense but a calque in another (``вірний`` = loyal ✓ but a calque
for "correct" → ``правильний``). Those live in ``SENSE_RESTRICTED_CALQUES`` and
MUST NOT be blanket-flagged: warning on the authentic sense is the same false-
positive failure as flagging ``блискучий``.

THEREFORE the consumer MUST apply the runtime safety gate:
    1. A lemma in CURATED_CALQUES below is a confirmed calque → warn, with the
       cited correction(s).
    2. A lemma in LEXICALISED_SAFE is a confirmed legitimate adjective → never warn.
    3. A lemma in SENSE_RESTRICTED_CALQUES is authentic in ``authentic_sense`` and
       a calque only in ``calque_sense`` → warn ONLY with the sense qualifier
       ("calque when used to mean X"); NEVER a blanket warning, NEVER auto-replace.
       The §6 renderer surfaces it as a soft, sense-scoped note so correct usage
       is never red-flagged.
    4. A phrase in PHRASAL_CALQUES is a confirmed whole-phrase calque → warn.
    5. For any OTHER ``-уч-/-юч-/-ач-/-яч-`` candidate surfaced by a
       morphological detector, gate through ``mcp__sources__search_heritage``:
       if it returns ``russianism_warning=False`` with Грінченко/ЕСУМ
       attestation, it is authentic — do NOT warn. (Validated: ``блискучий``
       → heritage score 96, russianism_warning=False.)

Provenance — every entry is grounded in the State-Standard NUS corpus or a human-
annotated error corpus, NOT invented. Replacement forms are VESUM-verified.
Sources (sources.db chunk ids / corpus refs):
    glazova-11    = 11-klas-ukrajinska-mova-glazova-2019_s0072
    avramenko-11  = 11-klas-ukrajinska-mova-avramenko-2019_s0075
    avramenko-7   = 7-klas-ukrmova-avramenko-2024_s0108
    litvinova-7   = 7-klas-ukrmova-litvinova-2024_s0096
    davydov       = Антоненко-Давидович «Як ми говоримо» (structured via query_slovnyk_me dict=davydov)
    antonenko-p145 = antonenko-davydovych-yak-my-hovorymo_p145 (prose on active participles -учий/-ячий not in Ukrainian; only lexicalised adjs of permanent quality; verified via get_chunk_context + search_heritage guard)
    antonenko-p53 = antonenko-davydovych-yak-my-hovorymo_p053 (дійсний/дійсно/
                    в дійсності/справжній cluster — "є в українській мові, але
                    не треба забувати й інших слів")
    ua-gec        = UA-GEC F/Calque + F/Collocation native-annotator pairs (doc
                    ids cited per entry; re-verified live via search_ua_gec_errors
                    after the #3101 tag_filter fix)
    grinchenko    = Грінченко 1907 (pre-Soviet authentic-sense attestation)
    sum-20        = СУМ-20 via slovnyk.me (modern attestation of authentic sense)
    search_heritage = MCP sources__search_heritage (false-positive guard before flagging; confirms no blanket russianism on lexicalised forms)

PR1 (#3098) active-participle calques verified via: search_heritage (before any flag) + query_slovnyk_me(davydov) for Antonenko entries + get_chunk_context for p145 prose + search_ua_gec_errors (F/Calque). Non-grounded or sense-restricted moved/ excluded. Collocation calques deferred to PR2. Atlas lemmas (0 direct -учий in vocabulary yamls) + related forms gate the seed set; no hand-waved expansion.

This is reference data only; the enrich-manifest wiring (heritage_status + §6_note in _curated_calque path) emits the note with native replacements + source citation for Atlas §6. When wiring SENSE_RESTRICTED_CALQUES, honour rule 3 — a
sense-scoped soft note, never a blanket warn or auto-replace.
"""

from __future__ import annotations

# Confirmed active-participle calques → recommended Ukrainian replacement(s).
# Each value: corrections (ordered, best-first), a short usage note, provenance
# tags, direct source evidence, and the heritage false-positive guard result.
# Corrections that are full phrases (relative clauses) are kept as-is because
# the participle has no single-word agent-noun equivalent.
CURATED_CALQUES: dict[str, dict[str, object]] = {
    "бажаючий": {
        "corrections": ["охочий"],
        "note": "усі бажаючі → усі охочі",
        "source": ["antonenko-p099", "glazova-11"],
        "evidence": [
            "antonenko-davydovych-yak-my-hovorymo_p099: Бажаючий – що (котрий, який) бажає – охочий",
            "11-klas-ukrajinska-mova-glazova-2019_s0072: замість бажаючий — охочий",
        ],
        "heritage_guard": "search_heritage(бажаючий, include_live_slovnyk=false): no matching heritage headword; ЕСУМ hit is a related охочий-family row, not an attestation of бажаючий as safe.",
    },
    "працюючий": {
        "corrections": ["працівник", "той, що працює"],
        "note": "agent noun or relative clause",
        "source": ["antonenko-p101", "antonenko-p144", "glazova-11"],
        "evidence": [
            "antonenko-davydovych-yak-my-hovorymo_p101: Працюючий – що (котрий, який) працює – ... працівник",
            "antonenko-davydovych-yak-my-hovorymo_p144: Тато, що не працює в неділю ... (instead of не працюючий тато)",
            "11-klas-ukrajinska-mova-glazova-2019_s0072: замість працюючий — працівник",
        ],
        "heritage_guard": "search_heritage(працюючий, include_live_slovnyk=false): No heritage evidence found.",
    },
    "завідуючий": {
        "corrections": ["завідувач"],
        "note": "agent noun -ач",
        "source": ["glazova-11", "zabolotnyi-7"],
        "evidence": [
            "11-klas-ukrajinska-mova-glazova-2019_s0072: замість завідуючий — завідувач",
            "7-klas-ukrmova-zabolotnyi-2024_s0124: завідувач бібліотеки / завідуючий бібліотекою",
        ],
        "heritage_guard": "search_heritage(завідуючий, include_live_slovnyk=false): ЕСУМ rows describe зав-/завгосп as Russian-modeled abbreviations, not a safe headword attestation.",
    },
    "мандруючий": {
        "corrections": ["мандрівний"],
        "note": "мандруючий сюжет → мандрівний сюжет",
        "source": ["glazova-11"],
        "evidence": ["11-klas-ukrajinska-mova-glazova-2019_s0072: мандрівний (а не мандруючий) сюжет"],
        "heritage_guard": "search_heritage(мандруючий, include_live_slovnyk=false): No heritage evidence found.",
    },
    "початкуючий": {
        "corrections": ["початківець"],
        "note": "початкуючий художник → художник-початківець",
        "source": ["antonenko-p101", "glazova-11", "zabolotnyi-7"],
        "evidence": [
            "antonenko-davydovych-yak-my-hovorymo_p101: Початкуючий – початківець",
            "11-klas-ukrajinska-mova-glazova-2019_s0072: художник-початківець (а не початкуючий художник)",
            "7-klas-ukrmova-zabolotnyi-2024_s0124: поет-початківець / початкуючий поет",
        ],
        "heritage_guard": "search_heritage(початкуючий, include_live_slovnyk=false): no matching heritage headword; ЕСУМ hit is a related письменець row.",
    },
    "узагальнюючий": {
        "corrections": ["узагальнювальний"],
        "note": "суфікс -альн-",
        "source": ["glazova-11"],
        "evidence": ["11-klas-ukrajinska-mova-glazova-2019_s0072: узагальнювальне (а не узагальнююче) слово"],
        "heritage_guard": "search_heritage(узагальнюючий, include_live_slovnyk=false): No heritage evidence found.",
    },
    "зволожуючий": {
        "corrections": ["зволожувальний"],
        "note": "суфікс -альн- (зволожувальний крем)",
        "source": ["glazova-11", "zabolotnyi-7"],
        "evidence": [
            "11-klas-ukrajinska-mova-glazova-2019_s0072: зволожувальний (а не зволожуючий) крем",
            "7-klas-ukrmova-zabolotnyi-2024_s0124: зволожувальний крем / зволожуючий крем",
        ],
        "heritage_guard": "search_heritage(зволожуючий, include_live_slovnyk=false): No heritage evidence found.",
    },
    "знеболюючий": {
        "corrections": ["знеболювальний"],
        "note": "суфікс -альн- (знеболювальні ліки)",
        "source": ["glazova-11", "zabolotnyi-7"],
        "evidence": [
            "11-klas-ukrajinska-mova-glazova-2019_s0072: знеболювальні (а не знеболюючі) ліки",
            "7-klas-ukrmova-zabolotnyi-2024_s0124: знеболювальний засіб / знеболюючий засіб",
        ],
        "heritage_guard": "search_heritage(знеболюючий, include_live_slovnyk=false): no matching heritage headword; ЕСУМ hit is a новокаїн definition, not a safe headword attestation.",
    },
    "хвилюючий": {
        "corrections": ["зворушливий"],
        "note": "хвилюючий спогад → зворушливий спогад",
        "source": ["glazova-11"],
        "evidence": ["11-klas-ukrajinska-mova-glazova-2019_s0072: зворушливий (а не хвилюючий) спогад"],
        "heritage_guard": "search_heritage(хвилюючий, include_live_slovnyk=false): No heritage evidence found.",
    },
    "діючий": {
        "corrections": ["чинний", "активний"],
        "note": "sense-split: діючий закон → чинний закон; діючий вулкан → активний вулкан (рос. действующий)",
        "source": ["glazova-11", "avramenko-11", "avramenko-7", "zabolotnyi-7"],
        "evidence": [
            "11-klas-ukrajinska-mova-glazova-2019_s0072: чинний (а не діючий) закон",
            "7-klas-ukrmova-avramenko-2024_s0106: синоніми ... діючий — чинний (закон) або активний (вулкан)",
            "7-klas-ukrmova-zabolotnyi-2024_s0124: чинний закон / діючий закон",
        ],
        "heritage_guard": "search_heritage(діючий, include_live_slovnyk=false): no matching heritage headword; ЕСУМ hit is the діянка family row and does not clear діючий закон.",
    },
    "підростаючий": {
        "corrections": ["молодий"],
        "note": "підростаюче покоління → молоде покоління",
        "source": ["glazova-11"],
        "evidence": ["11-klas-ukrajinska-mova-glazova-2019_s0072: молоде (а не підростаюче) покоління"],
        "heritage_guard": "search_heritage(підростаючий, include_live_slovnyk=false): No heritage evidence found.",
    },
    "потопаючий": {
        "corrections": ["той, що потопає"],
        "note": "relative clause",
        "source": ["glazova-11"],
        "evidence": ["11-klas-ukrajinska-mova-glazova-2019_s0072: Щури тікають з корабля, що потопає (not з потопаючого корабля)"],
        "heritage_guard": "search_heritage(потопаючий, include_live_slovnyk=false): No heritage evidence found.",
    },
    "головуючий": {
        "corrections": ["голова"],
        "note": "головуючий на зборах → голова зборів",
        "source": ["avramenko-11"],
        "evidence": ["11-klas-ukrajinska-mova-avramenko-2019_s0075: головуючий на зборах — голова зборів"],
        "heritage_guard": "search_heritage(головуючий, include_live_slovnyk=false): no matching heritage headword; ЕСУМ hit is an unrelated той/prezident row.",
    },
    "домінуючий": {
        "corrections": ["основний", "панівний"],
        "note": "рос. доминирующий",
        "source": ["avramenko-11", "antonenko-p101"],
        "evidence": [
            "11-klas-ukrajinska-mova-avramenko-2019_s0075: домінуючий принцип — основний принцип",
            "antonenko-davydovych-yak-my-hovorymo_p101: пануючий суперечить духу нашої мови; слід ... панівний",
        ],
        "heritage_guard": "search_heritage(домінуючий, include_live_slovnyk=false): no matching calque headword; ЕСУМ has related loan-family rows, so treat only the cited register/collocation as warn-worthy.",
    },
    "оточуючий": {
        "corrections": ["довколишній", "навколишній"],
        "note": "оточуюче середовище → довкілля / навколишнє середовище",
        "source": ["zabolotnyi-7", "zabolotnyi-11"],
        "evidence": [
            "7-klas-ukrmova-zabolotnyi-2024_s0124: навколишнє середовище, довкілля / оточуюче середовище",
            "11-klas-ukrmova-zabolotnyi-2019_s0078: навколишній / оточуючий",
        ],
        "heritage_guard": "search_heritage(оточуючий, include_live_slovnyk=false): No heritage evidence found.",
    },
    "відпочиваючий": {
        "corrections": ["відпочивальник", "той, хто відпочиває"],
        "note": "agent noun or relative clause",
        "source": ["antonenko-p099", "antonenko-p100", "zabolotnyi-7"],
        "evidence": [
            "antonenko-davydovych-yak-my-hovorymo_p099: Відпочиваючий, відпочивальник, що (котрий, який) відпочиває",
            "antonenko-davydovych-yak-my-hovorymo_p100: ... організовано розваги відпочивальників",
            "7-klas-ukrmova-zabolotnyi-2024_s0124: відпочивальник / відпочиваючий",
        ],
        "heritage_guard": "search_heritage(відпочиваючий, include_live_slovnyk=false): No heritage evidence found.",
    },
    "завмираючий": {
        "corrections": ["завмерлий", "той, що завмирає"],
        "note": "завмираючі звуки",
        "source": ["avramenko-7", "antonenko-p144"],
        "evidence": [
            "7-klas-ukrmova-avramenko-2024_s0108: завмираючі звуки — завмерлі звуки",
            "antonenko-davydovych-yak-my-hovorymo_p144: active forms require a relative clause or adverbial construction",
        ],
        "heritage_guard": "search_heritage(завмираючий, include_live_slovnyk=false): No heritage evidence found.",
    },
    "розквітаючий": {
        "corrections": ["розквітлий", "той, що розквітає"],
        "note": "розквітаючі дерева",
        "source": ["avramenko-7", "antonenko-p144"],
        "evidence": [
            "7-klas-ukrmova-avramenko-2024_s0108: розквітаючі дерева — розквітлі дерева",
            "antonenko-davydovych-yak-my-hovorymo_p144: active forms require a relative clause or adverbial construction",
        ],
        "heritage_guard": "search_heritage(розквітаючий, include_live_slovnyk=false): No heritage evidence found.",
    },
    "опадаючий": {
        "corrections": ["опалий"],
        "note": "present-participle calque → past form -лий",
        "source": ["avramenko-7", "antonenko-p144"],
        "evidence": [
            "7-klas-ukrmova-avramenko-2024_s0108: опадаюче листя — опале листя",
            "antonenko-davydovych-yak-my-hovorymo_p144: active forms require a relative clause or adverbial construction",
        ],
        "heritage_guard": "search_heritage(опадаючий, include_live_slovnyk=false): no matching heritage headword; ЕСУМ hit is a кулон definition, not a safe headword attestation.",
    },
    "в’янучий": {
        "corrections": ["зів’ялий"],
        "note": "present-participle calque → past form -лий",
        "source": ["avramenko-7", "antonenko-p144"],
        "evidence": [
            "7-klas-ukrmova-avramenko-2024_s0108: в’янучі квіти — зів’ялі квіти",
            "antonenko-davydovych-yak-my-hovorymo_p144: active forms require a relative clause or adverbial construction",
        ],
        "heritage_guard": "search_heritage(в’янучий, include_live_slovnyk=false): No heritage evidence found.",
    },
    "жовтіючий": {
        "corrections": ["пожовклий"],
        "note": "present-participle calque → past form -лий",
        "source": ["avramenko-7", "antonenko-p144"],
        "evidence": [
            "7-klas-ukrmova-avramenko-2024_s0108: жовтіюче листя — пожовкле листя",
            "antonenko-davydovych-yak-my-hovorymo_p144: active forms require a relative clause or adverbial construction",
        ],
        "heritage_guard": "search_heritage(жовтіючий, include_live_slovnyk=false): No heritage evidence found.",
    },
    "бувший": {"corrections": ["колишній"], "note": "-вш- participle does not exist in Ukrainian (рос. бывший)", "source": ["avramenko-11"]},
    # §6 lexical-calque slice 3 (#3098) — single-word blanket lexical calques.
    "слідуючий": {
        "kind": "lexical",
        "corrections": ["наступний"],
        "note": "рос. следующий; use наступний for 'next'",
        "source": ["voron-9", "zabolotnyi-5"],
        "evidence": [
            "9-klas-ukrajinska-mova-voron-2017_s0232: следующий — тут: наступний; Як правильно перекласти ... следующий? ... наступний",
        ],
        "heritage_guard": "search_heritage(слідуючий, include_live_slovnyk=false): No heritage evidence found.",
    },
    "багаточисельний": {
        "kind": "lexical",
        "corrections": ["численний"],
        "note": "рос. многочисленный; use численний for 'numerous'",
        "source": ["antonenko-p065", "zabolotnyi-11"],
        "evidence": [
            "Антоненко-Давидович: Слова багаточисельний ... нема в українській мові, є прикметник численний",
        ],
        "heritage_guard": "search_heritage(багаточисельний, include_live_slovnyk=false): No heritage evidence found.",
    },
    "міроприємство": {
        "kind": "lexical",
        "corrections": ["захід", "заходи"],
        "note": "рос. мероприятие; use захід / заходи",
        "source": ["antonenko-p044", "glazova-10"],
        "evidence": [
            "Антоненко-Давидович: Відповідником до російських мера, мероприятие є захід, а в множині — заходи",
        ],
        "heritage_guard": "search_heritage(міроприємство, include_live_slovnyk=false): No heritage evidence found.",
    },
    "учбовий": {
        "kind": "lexical",
        "corrections": ["навчальний"],
        "note": "рос. учебный; use навчальний",
        "source": ["avramenko-5", "zabolotnyi-10"],
        "evidence": [
            "5-klas-ukrmova-avramenko-2022_s0038: НЕПРАВИЛЬНО учбовий заклад; ПРАВИЛЬНО навчальний заклад",
        ],
        "heritage_guard": "search_heritage(учбовий, include_live_slovnyk=false): ЕСУМ hits are related/noisy snippets, not safe headword attestation.",
    },
}

# Phrasal / collocation calques (whole-phrase replacement).
PHRASAL_CALQUES: dict[str, dict[str, object]] = {
    "прийняти участь": {
        "corrections": ["взяти участь"],
        "note": "рос. принять участие",
        "source": ["antonenko-p091", "zabolotnyi-10"],
        "evidence": [
            "antonenko-davydovych-yak-my-hovorymo_p091: прийняли участь ... треба було написати взяли участь",
            "10-klas-ukrmova-zabolotnyi-2018_s0027: У змаганнях треба брати участь, а не приймати.",
        ],
        "heritage_guard": "search_heritage(прийняти участь, include_live_slovnyk=false): phrase guard not lexical; no heritage headword can clear the collocation.",
    },
    "приймати участь": {
        "corrections": ["брати участь"],
        "note": "рос. принимать участие",
        "source": ["antonenko-p091", "zabolotnyi-10"],
        "evidence": [
            "antonenko-davydovych-yak-my-hovorymo_p091: Приймати участь – брати участь",
            "10-klas-ukrmova-zabolotnyi-2018_s0027: У змаганнях треба брати участь, а не приймати.",
        ],
        "heritage_guard": "search_heritage(приймати участь, include_live_slovnyk=false): phrase guard not lexical; no heritage headword can clear the collocation.",
    },
    "недремлюче око": {"corrections": ["недремне око"], "note": "Antonenko's example", "source": ["antonenko"]},
    "сидячі місця": {"corrections": ["місця для сидіння"], "note": "ненормативний вираз", "source": ["glazova-11"]},
    "миючі засоби": {"corrections": ["мийні засоби"], "note": "ненормативний вираз", "source": ["glazova-11"]},
    # §6 grok-swarm extension (#3098) — phrasal register calques, UA-GEC/Antonenko-grounded.
    "в дійсності": {"corrections": ["насправді", "на ділі"], "note": "рос. в действительности; Antonenko: надуживають замість насправді", "source": ["antonenko-p53", "grok-3098"]},
    "по відношенню до": {"corrections": ["щодо", "стосовно"], "note": "рос. по отношению к (UA-GEC native: щодо/відносно)", "source": ["ua-gec", "grok-3098"]},  # ua-gec 0981, 1421
    "точка зору": {"corrections": ["погляд"], "note": "рос. точка зрения; цієї точки зору → цього погляду", "source": ["ua-gec", "grok-3098"]},  # ua-gec 0037, 0520
    "з моєї точки зору": {"corrections": ["на мою думку"], "note": "рос. с моей точки зрения", "source": ["ua-gec", "grok-3098"]},  # ua-gec 0573, 1031
    "ні в якому разі": {"corrections": ["аж ніяк", "у жодному разі"], "note": "рос. ни в коем случае", "source": ["ua-gec", "grok-3098"]},  # ua-gec 0717, 1844
    "прийшло в голову": {"corrections": ["спало на думку"], "note": "рос. пришло в голову (F/Collocation); в голову прийшли → спали на гадку", "source": ["ua-gec", "grok-3098"]},  # ua-gec 0834
    # §6 collocation/phrasal slice 2 (#3098) — kept only with direct correction evidence.
    "при допомозі": {
        "corrections": ["за допомогою"],
        "note": "syntactic calque; use the instrumental phrase за допомогою",
        "source": ["glazova-11"],
        "evidence": [
            "11-klas-ukrajinska-mova-glazova-2019_s0079: Неправильно: при допомозі; Правильно: за допомогою",
        ],
        "heritage_guard": "search_heritage(при допомозі, include_live_slovnyk=false): No heritage evidence found.",
    },
    "співпадати": {
        "corrections": ["збігатися"],
        "note": "рос. совпадать; дані співпадають → дані збігаються",
        "source": ["avramenko-5"],
        "evidence": [
            "5-klas-ukrmova-avramenko-2022_s0038: Неправильно: дані співпадають; Правильно: дані збігаються",
        ],
        "heritage_guard": "search_heritage(співпадати, include_live_slovnyk=false): No heritage evidence found.",
    },
    "в кінці кінців": {
        "corrections": ["кінець кінцем", "зрештою", "урешті-решт", "врешті-решт"],
        "note": "рос. в конце концов",
        "source": ["zabolotnyi-9", "ua-gec"],
        "evidence": [
            "9-klas-ukrmova-zabolotnyi-2017_s0291: Правильно: кінець кінцем; НЕправильно: в кінці кінців",
            "UA-GEC 0935: Error: в кінці кінців; Correction: врешті-решт; Type: F/Calque",
        ],
        "heritage_guard": "search_heritage(в кінці кінців, include_live_slovnyk=false): No heritage evidence found.",
    },
}

# Sense-restricted calques (#3098 grok-swarm extension) — POLYSEMES.
# Each headword is authentic Ukrainian in ``authentic_sense`` (heritage-attested,
# russianism_warning=False) but a calque ONLY in ``calque_sense``. The §6
# renderer MUST warn with the sense qualifier and NEVER blanket-flag or auto-
# replace (rule 3). Blanket-flagging these is the same false-positive failure as
# flagging ``блискучий`` — each authentic_sense below is Грінченко/СУМ-attested.
#
# Deliberately EXCLUDED after live heritage/UA-GEC verification (do NOT re-add as
# blanket calques — they over-flag correct usage):
#   * ``дійсно``  — authentic adverb (Грінченко; Antonenko p053 "є в українській
#                   мові"); справді is only register-preferred, not a calque.
#   * ``відносно`` — authentic ("порівняно", СУМ-20 / Грінченко prose); UA-GEC
#                   even offers it AS the correction for "по відношенню до".
#   * ``по-моєму`` / ``з приводу`` / ``з цього приводу`` — standard Ukrainian.
#   * ``ніяк`` — UA-GEC context artifact (= "in no way", not "it seems").
#   * ``вроде`` / ``кажись`` — raw Russian / surzhyk insertions: a different
#                   (surzhyk) layer, NOT a §6 calque-of-an-authentic-word.
SENSE_RESTRICTED_CALQUES: dict[str, dict[str, object]] = {
    "вірний": {
        "corrections": ["правильний", "слушний"],
        "calque_sense": "correct / true (рос. верный = 'correct')",
        "authentic_sense": "loyal, faithful (вірний друг, вірна дружина)",
        "note": "Грінченко: 'верный, преданный'; calque only when it means 'correct' (правильна відповідь, not вірна).",
        "source": ["grinchenko", "antonenko", "grok-3098"],
    },
    "дійсний": {
        "corrections": ["справжній"],
        "calque_sense": "genuine / real (рос. действительный = 'real')",
        "authentic_sense": "valid, in-force (дійсний квиток, дійсний член академії)",
        "note": "Antonenko p053: дійсний 'є в українській мові' — calque only when overused for справжній.",
        "source": ["antonenko-p53", "grinchenko", "grok-3098"],
    },
    "відношення": {
        "corrections": ["ставлення", "стосунок"],
        "calque_sense": "attitude / relationship (рос. отношение)",
        "authentic_sense": "ratio, mathematical/technical relation (числове відношення)",
        "note": "СУМ-20 lists 'стосунок' as a sense; calque only in the attitude/relationship register → ставлення/стосунок.",
        "source": ["sum-20", "antonenko", "grok-3098"],
    },
    "рахувати": {
        "corrections": ["вважати"],
        "calque_sense": "to be of the opinion / consider that (рос. считать = 'deem')",
        "authentic_sense": "to count, reckon, calculate (гроші рахувати)",
        "note": "Грінченко attests 'считать; разсчитывать, взвешивать'; calque only in 'я рахую, що…' → 'я вважаю, що…'.",
        "source": ["grinchenko", "grok-3098"],
    },
    "виглядати": {
        "corrections": ["здаватися", "видаватися"],
        "calque_sense": "to seem / appear that (рос. выглядит = 'it seems')",
        "authentic_sense": "to look (well/ill); to peer out (гарно виглядати; виглядати у вікно)",
        "note": "Грінченко/СУМ-20 attest 'look; peer out'; calque only when 'виглядає' replaces 'здається' (= it seems).",
        "source": ["grinchenko", "sum-20", "grok-3098"],
    },
    "являтися": {
        "corrections": ["бути", "є"],
        "calque_sense": "to be / constitute (рос. являться = 'to be')",
        "authentic_sense": "to appear, show oneself, arrive (явитися комусь / десь)",
        "note": "Грінченко attests являтися as 'show/appear'; calque only in copular use: являтися переможцем → бути переможцем.",
        "source": ["grinchenko", "avramenko-9", "zabolotnyi-9", "ua-gec"],
        "evidence": [
            "9-klas-ukrajinska-mova-avramenko-2017_s0162: Неправильно: являтися переможцем; Правильно: бути переможцем",
            "9-klas-ukrmova-zabolotnyi-2017_s0101: Правильно: він є студентом; НЕПРАВИЛЬНО: він являється студентом",
            "UA-GEC 0301: Error: являється; Correction: є; Type: F/Calque",
            "Грінченко: Являтися ... Являться, явиться, показываться, показаться.",
        ],
        "heritage_guard": "search_heritage(являтися, include_live_slovnyk=false): Грінченко authentic for 'appear/show'; therefore sense-restricted, not blanket.",
    },
    "на протязі": {
        "corrections": ["протягом", "упродовж", "впродовж"],
        "calque_sense": "during / over a time span (рос. на протяжении)",
        "authentic_sense": "in a draft; along/over a distance (сидіти на протязі; на протязі кількох кілометрів)",
        "note": "Calque only for time duration: на протязі години → протягом/упродовж години; keep the draft/distance senses.",
        "source": ["litvinova-7", "zabolotnyi-7", "zabolotnyi-9", "ua-gec"],
        "evidence": [
            "7-klas-ukrmova-litvinova-2024_s0186: для тривалости використовуємо протягом, упродовж/впродовж; на протязі означає на різкому струмені повітря",
            "7-klas-ukrmova-zabolotnyi-2024_s0229: на протязі години ненормативне; для часу вживаємо протягом або впродовж; на протязі можна сидіти / уживати для відстані",
            "UA-GEC 0490: Error: на протязі; Correction: протягом; Type: F/Calque",
            "UA-GEC 1730: Error: на протязі; Correction: упродовж; Type: F/Collocation",
        ],
        "heritage_guard": "search_heritage(на протязі, include_live_slovnyk=false): ЕСУМ row is not a time-duration clearance; textbooks explicitly preserve draft/distance senses.",
    },
    "дякуючи": {
        "corrections": ["завдяки"],
        "calque_sense": "because of / thanks to as a preposition with a cause (рос. благодаря)",
        "authentic_sense": "adverbial participle of дякувати: while thanking someone",
        "note": "Calque only in causal-preposition use: дякуючи підтримці → завдяки підтримці.",
        "source": ["zabolotnyi-7"],
        "evidence": [
            "7-klas-ukrmova-zabolotnyi-2024_s0143: Правильно: Переміг завдяки підтримці друзів; НЕправильно: Переміг, дякуючи підтримці друзів.",
            "7-klas-ukrmova-zabolotnyi-2024_s0229: Правильно: завдяки підтримці; НЕправильно: дякуючи підтримці",
        ],
        "heritage_guard": "search_heritage(дякуючи, include_live_slovnyk=false): no direct safe headword clearance for the causal-preposition use; keep sense-restricted because дієприслівник дякуючи is grammatical.",
    },
    "так як": {
        "corrections": ["оскільки", "бо"],
        "calque_sense": "because / since (рос. так как)",
        "authentic_sense": "comparative construction так, як ('in the way that'), normally comma-marked",
        "note": "Calque only in causal conjunction use: так як → оскільки/бо; do not confuse with так, як.",
        "source": ["ua-gec"],
        "evidence": [
            "UA-GEC 0026: Error: так як; Correction: оскільки; Type: F/Calque",
            "UA-GEC 0569: Error: так як; Correction: бо; Type: F/Calque",
        ],
        "heritage_guard": "search_heritage(так як, include_live_slovnyk=false): no phrase clearance; ЕСУМ hits attest components/other expressions, so this remains sense-restricted.",
    },
    "біля": {
        "corrections": ["близько"],
        "calque_sense": "approximately / about before a quantity (рос. около)",
        "authentic_sense": "next to, near (біля школи, біля будинку)",
        "note": "Грінченко attests біля as 'near'; calque only before approximate quantities: біля двох років → близько двох років.",
        "source": ["grinchenko", "litvinova-7", "zabolotnyi-7", "ua-gec"],
        "evidence": [
            "7-klas-ukrmova-litvinova-2024_s0186: БІЛЯ: біля школи, біля будинку; БЛИЗЬКО: близько третьої години, потрібно близько двадцяти хвилин",
            "7-klas-ukrmova-zabolotnyi-2024_s0229: Правильно: близько двох років; НЕправильно: біля двох років",
            "UA-GEC 0385: Error: біля; Correction: близько; Type: F/Calque",
            "Грінченко: Біля ... Подле, возле, около. Ліг біля моря одпочить.",
        ],
        "heritage_guard": "search_heritage(біля, include_live_slovnyk=false): Грінченко authentic for 'near'; therefore sense-restricted, not blanket.",
    },
    "на рахунок": {
        "corrections": ["щодо", "стосовно"],
        "calque_sense": "regarding / concerning (рос. насчёт)",
        "authentic_sense": "to/onto an account, including bank-account contexts",
        "note": "Calque only in 'regarding' use: на рахунок цього → щодо цього; keep literal account/bank uses.",
        "source": ["avramenko-5", "zabolotnyi-9", "grinchenko", "ua-gec"],
        "evidence": [
            "5-klas-ukrmova-avramenko-2022_s0057: Неправильно: на рахунок цього; Правильно: щодо цього",
            "9-klas-ukrmova-zabolotnyi-2017_s0031: Правильно: рахунок у банку; НЕПРАВИЛЬНО: счьот у банку",
            "UA-GEC 1296: Error: на рахунок; Correction: щодо; Type: F/Calque",
            "Грінченко: Рахунок ... Счет, разсчет. В рахунку помилився.",
        ],
        "heritage_guard": "search_heritage(рахунок, include_live_slovnyk=false): Грінченко authentic for account/count; therefore на рахунок is sense-restricted to the 'regarding' calque.",
    },
    "любий": {
        "corrections": ["будь-який", "кожний", "усякий"],
        "calque_sense": "any / whichever (рос. любой)",
        "authentic_sense": "dear, beloved, pleasant (любий друже; любий мій)",
        "note": "Грінченко attests любий as 'dear/beloved'; calque only when it means 'any' → будь-який.",
        "source": ["ua-gec", "grinchenko", "antonenko"],
        "evidence": [
            "UA-GEC 1846: Error: любий; Correction: будь-який; Type: F/Calque",
        ],
        "heritage_guard": "search_heritage(любий, include_live_slovnyk=false): Грінченко authentic for 'dear/beloved'; therefore sense-restricted, not blanket.",
    },
    "неділя": {
        "corrections": ["тиждень"],
        "calque_sense": "week / a seven-day period (рос. неделя)",
        "authentic_sense": "Sunday (day of the week)",
        "note": "Грінченко attests неділя as Sunday; calque only when it means a week-long period → тиждень.",
        "source": ["glazova-10", "grinchenko"],
        "evidence": [
            "10-klas-ukrmova-glazova-2018_s0075: Прем’єра ... через дві неділі ... Довідка. Тиждень",
        ],
        "heritage_guard": "search_heritage(неділя, include_live_slovnyk=false): Грінченко authentic for Sunday; therefore sense-restricted, not blanket.",
    },
}

# Confirmed-legitimate ``-уч-/-юч-/-ач-/-яч-`` adjectives of permanent quality —
# NEVER flag these (textbook- and/or heritage-attested). A morphological
# detector must skip this set before consulting the heritage gate.
LEXICALISED_SAFE: frozenset[str] = frozenset({
    "лежачий",    # лежачий камінь — litvinova-7, antonenko
    "квітучий",   # квітучий сад — litvinova-7
    "правлячий",  # правлячий режим — litvinova-7
    "пекучий",    # пекучий біль — litvinova-7
    "блискучий",  # heritage score 96, russianism_warning=False
    "блукаючий",  # термін: блукаючий нерв — avramenko-11
    "спляча",     # спляча красуня — avramenko-7 (lexicalised)
    "колючий",
    "родючий",
    "балакучий",
    "плакучий",   # плакуча верба
})

# Morphological rules (categorical — no exceptions, no heritage gate needed):
#   * Active participles are NOT formed from reflexive ``-ся`` verbs:
#     одягаючийся, навчавшийся → relative clause «той, що одягається / навчався».
#     (litvinova-7, avramenko-7)
#   * ``-ш-/-вш-`` participles do not exist in Ukrainian: бувший, робивший,
#     посинівший → past form «-лий» (посинілий) or a relative clause.
#     (litvinova-7, avramenko-7)
REFLEXIVE_PARTICIPLE_SUFFIXES = ("ийся", "ійся", "вшийся")
NONEXISTENT_PARTICIPLE_SUFFIXES = ("вший", "ший")
