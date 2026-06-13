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

THEREFORE the consumer MUST apply the runtime safety gate:
    1. A lemma in CURATED_CALQUES below is a confirmed calque → warn, with the
       cited correction(s).
    2. A lemma in LEXICALISED_SAFE is a confirmed legitimate adjective → never warn.
    3. For any OTHER ``-уч-/-юч-/-ач-/-яч-`` candidate surfaced by a
       morphological detector, gate through ``mcp__sources__search_heritage``:
       if it returns ``russianism_warning=False`` with Грінченко/ЕСУМ
       attestation, it is authentic — do NOT warn. (Validated: ``блискучий``
       → heritage score 96, russianism_warning=False.)

Provenance — every entry is grounded in the State-Standard NUS corpus, NOT
invented. Replacement forms are VESUM-verified. Sources (sources.db chunk ids):
    glazova-11   = 11-klas-ukrajinska-mova-glazova-2019_s0072
    avramenko-11 = 11-klas-ukrajinska-mova-avramenko-2019_s0075
    avramenko-7  = 7-klas-ukrmova-avramenko-2024_s0108
    litvinova-7  = 7-klas-ukrmova-litvinova-2024_s0096
    antonenko    = antonenko-davydovych-yak-my-hovorymo_p145
    issue-3098   = GitHub issue #3098 (participle slice spec)

This is reference data only; the enrich-manifest wiring (`_calque_warning`)
and the §6 template card are a follow-up that edits enrich_manifest.py — held
until PRs #3102 (#2971/#3092) and #3099 (§12) land, to avoid a 3-way conflict
on that file.
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
