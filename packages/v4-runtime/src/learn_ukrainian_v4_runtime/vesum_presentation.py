"""Readable VESUM tags for presentation only; never an authority hash input."""

from __future__ import annotations

# Meanings from https://github.com/brown-uk/dict_uk/blob/master/doc/tags.txt.
# Translate explicit tokens only: do not infer features absent from the tags.
_TAG_GLOSSES = {
    "noun": "noun",
    "verb": "verb",
    "adj": "adjective",
    "adjp": "participle",
    "adv": "adverb",
    "advp": "adverbial participle",
    "prep": "preposition",
    "conj": "conjunction",
    "part": "particle",
    "intj": "interjection",
    "numr": "numeral",
    "pron": "pronoun",
    "noninfl": "uninflected component",
    "m": "masculine",
    "f": "feminine",
    "n": "neuter",
    "s": "singular",
    "p": "plural",
    "v_naz": "nominative",
    "v_rod": "genitive",
    "v_dav": "dative",
    "v_zna": "accusative",
    "v_oru": "instrumental",
    "v_mis": "locative",
    "v_kly": "vocative",
    "anim": "animate",
    "inanim": "inanimate",
    "unanim": "unspecified animacy",
    "ranim": "for animate referents",
    "rinanim": "for inanimate referents",
    "imperf": "imperfective",
    "perf": "perfective",
    "inf": "infinitive",
    "pres": "present tense",
    "past": "past tense",
    "futr": "future tense",
    "impr": "imperative",
    "impers": "impersonal form",
    "rev": "reflexive verb",
    "1": "first person",
    "2": "second person",
    "3": "third person",
    "compb": "positive degree",
    "compc": "comparative degree",
    "comps": "superlative degree",
    "actv": "active",
    "pasv": "passive",
    "nv": "indeclinable",
    "ns": "plural-only noun",
    "arch": "archaic (sometimes dialectal)",
}


def tag_gloss(tags: str | None) -> str:
    """Decode known tokens, explicitly preserving unknown or missing tags."""
    tokens = [token for token in (tags or "").split(":") if token]
    return "; ".join(_TAG_GLOSSES.get(token, f"unrecognized tag [{token}]") for token in tokens) or "No morphological tags supplied"
