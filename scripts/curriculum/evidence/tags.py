"""VESUM atoms to oracle/UD features, without looking up any source.

Semantics: https://github.com/brown-uk/dict_uk/blob/master/doc/tags.txt.
The oracle accepts additional UD features even when its current packed dictionary
does not use them. Contextual POS/number rules are below; annotation-only atoms
are explicitly acknowledged rather than treated as unrecognized grammar.
"""

import warnings
from collections.abc import Callable
from dataclasses import dataclass, field

from . import codes

ATOM_MAP = {
    "noun": ("upos=NOUN",),
    "verb": ("upos=VERB",),
    "adj": ("upos=ADJ",),
    "adv": ("upos=ADV",),
    "advp": ("upos=VERB", "VerbForm=Conv"),
    "prep": ("upos=ADP",),
    "part": ("upos=PART",),
    "intj": ("upos=INTJ",),
    "numr": ("upos=NUM",),
    "conj": (),
    "coord": (),
    "subord": (),
    "v_naz": ("Case=Nom",),
    "v_rod": ("Case=Gen",),
    "v_dav": ("Case=Dat",),
    "v_zna": ("Case=Acc",),
    "v_oru": ("Case=Ins",),
    "v_mis": ("Case=Loc",),
    "v_kly": ("Case=Voc",),
    "m": ("Gender=Masc",),
    "f": ("Gender=Fem",),
    "n": ("Gender=Neut",),
    "s": ("Number=Sing",),
    "p": ("Number=Plur",),
    "ns": ("Number=Plur",),
    "1": ("Person=1",),
    "2": ("Person=2",),
    "3": ("Person=3",),
    "inf": ("VerbForm=Inf",),
    "impers": ("Person=0",),
    "impr": ("Mood=Imp",),
    "pres": ("Tense=Pres",),
    "past": ("Tense=Past",),
    "futr": ("Tense=Fut",),
    "adjp": ("VerbForm=Part",),
    "actv": ("Voice=Act",),
    "pasv": ("Voice=Pass",),
    "imperf": ("Aspect=Imp",),
    "perf": ("Aspect=Perf",),
    "rev": ("Reflex=Yes",),
    "compb": ("Degree=Pos",),
    "compc": ("Degree=Cmp",),
    "comps": ("Degree=Sup",),
    "anim": ("Animacy=Anim",),
    "inanim": ("Animacy=Inan",),
    "ranim": ("Animacy=Anim",),
    "rinanim": ("Animacy=Inan",),
    "pron": (),
    "prop": (),
    "pers": (),
    "refl": ("Reflex=Yes",),
    "pos": ("Poss=Yes",),
    "dem": ("PronType=Dem",),
    "def": ("PronType=Tot",),
    "int": ("PronType=Int",),
    "rel": ("PronType=Rel",),
    "neg": ("PronType=Neg",),
    "ind": ("PronType=Ind",),
    "gen": ("PronType=Tot",),
    "emph": ("PronType=Emp",),
}

# These annotations have no unambiguous feature in the stress dictionary.
IGNORED_ATOMS = frozenset(
    {
        "abbr",
        "alt",
        "arch",
        "bad",
        "dimin",
        "fname",
        "foreign",
        "geo",
        "insert",
        "latin",
        "lname",
        "long",
        "noninfl",
        "number",
        "nv",
        "obsc",
        "onomat",
        "pname",
        "predic",
        "rare",
        "short",
        "slang",
        "subst",
        "unanim",
        "up19",
        "up92",
        "var",
        "vulg",
        "xp1",
        "xp2",
        "xp3",
    }
)
KNOWN_ATOMS = frozenset(ATOM_MAP) | IGNORED_ATOMS


@dataclass
class TagMapper:
    """One instance per build: report each unknown atom once, including in batches."""

    report: Callable[[str], None] | None = None
    unknown_atoms: set[str] = field(default_factory=set, init=False)

    def __call__(self, vesum_tags: str) -> list[str]:
        atoms = set(vesum_tags.split(":")) - {""}
        for atom in sorted(atoms - KNOWN_ATOMS - self.unknown_atoms):
            message = f"{codes.UNKNOWN_TAG}: {atom!r} in {vesum_tags!r}"
            if self.report is None:
                warnings.warn(message, stacklevel=2)
            else:
                self.report(message)
        self.unknown_atoms.update(atoms - KNOWN_ATOMS)
        mapped = {feature for atom in atoms for feature in ATOM_MAP.get(atom, ())}
        # VESUM encodes singular nouns/adjectives/past verbs by gender alone.
        if atoms & {"m", "f", "n"} and not atoms & {"p", "ns"}:
            mapped.add("Number=Sing")
        # numr is also an adjective modifier (ordinal), not always its POS.
        if "adj" in atoms and "numr" in atoms:
            mapped.discard("upos=NUM")
            mapped.add("NumType=Ord")
        if "noun" in atoms and "pron" in atoms:
            mapped.discard("upos=NOUN")
            mapped.add("upos=PRON")
        elif "noun" in atoms and "prop" in atoms:
            mapped.discard("upos=NOUN")
            mapped.add("upos=PROPN")
        if "conj" in atoms:
            # The installed oracle has only CCONJ, including subordinators.
            mapped.add("upos=CCONJ")
        if "pers" in atoms and "pron" in atoms:
            mapped.add("PronType=Prs")
        if "verb" in atoms and atoms & {"pres", "past", "futr", "impr"}:
            mapped.add("VerbForm=Fin")
        return sorted(mapped)

    def summary(self) -> dict:
        return {"known_atoms": len(KNOWN_ATOMS), "unknown_atoms": sorted(self.unknown_atoms)}


def to_oracle(vesum_tags: str) -> list[str]:
    """Single-call convenience; use TagMapper for once-per-build reporting."""
    return TagMapper()(vesum_tags)
