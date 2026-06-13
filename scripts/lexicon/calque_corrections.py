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
    antonenko     = antonenko-davydovych-yak-my-hovorymo_p145
    antonenko-p53 = antonenko-davydovych-yak-my-hovorymo_p053 (дійсний/дійсно/
                    в дійсності/справжній cluster — "є в українській мові, але
                    не треба забувати й інших слів")
    ua-gec        = UA-GEC F/Calque + F/Collocation native-annotator pairs (doc
                    ids cited per entry; re-verified live via search_ua_gec_errors
                    after the #3101 tag_filter fix)
    grinchenko    = Грінченко 1907 (pre-Soviet authentic-sense attestation)
    sum-20        = СУМ-20 via slovnyk.me (modern attestation of authentic sense)
    grok-3098     = grok-swarm §6 candidates (2026-06-14), Claude-curated:
                    docs/research/atlas/grok-swarm-calque-candidates-2026-06-14
    issue-3098    = GitHub issue #3098 (participle slice spec)

This is reference data only; the enrich-manifest wiring (`_calque_warning`) and
the §6 template card are the remaining #3098 follow-up that edits
enrich_manifest.py (the earlier 3-way conflict with #3102/#3099 is resolved now
that both have merged). When wiring SENSE_RESTRICTED_CALQUES, honour rule 3 — a
sense-scoped soft note, never a blanket warn or auto-replace.
"""

from __future__ import annotations

# Confirmed active-participle calques → recommended Ukrainian replacement(s).
# Each value: corrections (ordered, best-first), a short usage note, and the
# provenance tag(s). Corrections that are full phrases (relative clauses) are
# kept as-is because the participle has no single-word agent-noun equivalent.
CURATED_CALQUES: dict[str, dict[str, object]] = {
    "бажаючий": {"corrections": ["охочий"], "note": "усі бажаючі → усі охочі", "source": ["glazova-11", "avramenko-7"]},
    "працюючий": {"corrections": ["працівник", "той, що працює"], "note": "agent noun or relative clause", "source": ["glazova-11", "issue-3098"]},
    "завідуючий": {"corrections": ["завідувач"], "note": "agent noun -ач", "source": ["glazova-11"]},
    "мандруючий": {"corrections": ["мандрівний"], "note": "мандруючий сюжет → мандрівний сюжет", "source": ["glazova-11"]},
    "початкуючий": {"corrections": ["початківець"], "note": "початкуючий художник → художник-початківець", "source": ["glazova-11"]},
    "узагальнюючий": {"corrections": ["узагальнювальний"], "note": "суфікс -альн-", "source": ["glazova-11"]},
    "зволожуючий": {"corrections": ["зволожувальний"], "note": "суфікс -альн- (зволожувальний крем)", "source": ["glazova-11"]},
    "знеболюючий": {"corrections": ["знеболювальний"], "note": "суфікс -альн- (знеболювальні ліки)", "source": ["glazova-11"]},
    "хвилюючий": {"corrections": ["зворушливий"], "note": "хвилюючий спогад → зворушливий спогад", "source": ["glazova-11"]},
    "діючий": {"corrections": ["чинний"], "note": "діючий закон → чинний закон (рос. действующий)", "source": ["glazova-11", "avramenko-11"]},
    "підростаючий": {"corrections": ["молодий"], "note": "підростаюче покоління → молоде покоління", "source": ["glazova-11"]},
    "потопаючий": {"corrections": ["той, що потопає"], "note": "relative clause", "source": ["glazova-11"]},
    "головуючий": {"corrections": ["голова"], "note": "головуючий на зборах → голова зборів", "source": ["avramenko-11"]},
    "домінуючий": {"corrections": ["основний", "панівний"], "note": "рос. доминирующий", "source": ["avramenko-11"]},
    "оточуючий": {"corrections": ["довколишній", "навколишній"], "note": "оточуюче середовище → довкілля / навколишнє середовище", "source": ["issue-3098"]},
    "відпочиваючий": {"corrections": ["відпочивальник", "той, хто відпочиває"], "note": "agent noun or relative clause", "source": ["issue-3098"]},
    "завмираючий": {"corrections": ["завмерлий", "той, що завмирає"], "note": "завмираючі звуки", "source": ["avramenko-7"]},
    "розквітаючий": {"corrections": ["розквітлий", "той, що розквітає"], "note": "розквітаючі дерева", "source": ["avramenko-7"]},
    "опадаючий": {"corrections": ["опалий"], "note": "present-participle calque → past form -лий", "source": ["avramenko-7"]},
    "в’янучий": {"corrections": ["зів’ялий"], "note": "present-participle calque → past form -лий", "source": ["avramenko-7"]},
    "жовтіючий": {"corrections": ["пожовклий"], "note": "present-participle calque → past form -лий", "source": ["avramenko-7"]},
    "бувший": {"corrections": ["колишній"], "note": "-вш- participle does not exist in Ukrainian (рос. бывший)", "source": ["avramenko-11"]},
}

# Phrasal / collocation calques (whole-phrase replacement).
PHRASAL_CALQUES: dict[str, dict[str, object]] = {
    "прийняти участь": {"corrections": ["взяти участь"], "note": "рос. принять участие", "source": ["issue-3098"]},
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
