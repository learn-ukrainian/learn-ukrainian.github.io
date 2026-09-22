import pytest

from scripts.curriculum.evidence import codes, sources, tags


@pytest.mark.parametrize(
    ("vesum", "expected"),
    [
        ("noun:inanim:f:v_rod", {"upos=NOUN", "Animacy=Inan", "Gender=Fem", "Number=Sing", "Case=Gen"}),
        ("noun:anim:m:p:v_naz", {"upos=NOUN", "Animacy=Anim", "Gender=Masc", "Number=Plur", "Case=Nom"}),
        ("verb:imperf:pres:s:1", {"upos=VERB", "Aspect=Imp", "Tense=Pres", "Number=Sing", "Person=1", "VerbForm=Fin"}),
        ("verb:perf:inf", {"upos=VERB", "Aspect=Perf", "VerbForm=Inf"}),
        ("verb:impers", {"upos=VERB", "Person=0"}),
        ("advp:perf", {"upos=VERB", "Aspect=Perf", "VerbForm=Conv"}),
        ("noun:prop:m:v_naz", {"upos=PROPN", "Gender=Masc", "Number=Sing", "Case=Nom"}),
        ("noun:s:v_naz:pron:pers:1", {"upos=PRON", "Number=Sing", "Case=Nom", "PronType=Prs", "Person=1"}),
        ("adj:m:v_naz:numr", {"upos=ADJ", "Gender=Masc", "Number=Sing", "Case=Nom", "NumType=Ord"}),
        ("adj:p:v_naz:compc", {"upos=ADJ", "Number=Plur", "Case=Nom", "Degree=Cmp"}),
        ("adv:comps", {"upos=ADV", "Degree=Sup"}),
        ("conj:subord", {"upos=CCONJ"}),
    ],
)
def test_contextual_mapping(vesum, expected):
    assert set(tags.to_oracle(vesum)) == expected


def test_unknowns_are_reported_once_per_build():
    messages = []
    mapper = tags.TagMapper(messages.append)
    assert mapper("noun:synthetic-new") == ["upos=NOUN"]
    mapper("noun:synthetic-new")
    assert len(messages) == 1
    assert codes.UNKNOWN_TAG in messages[0]
    assert mapper.summary()["unknown_atoms"] == ["synthetic-new"]
    with pytest.warns(UserWarning, match="synthetic-new"):
        tags.to_oracle("synthetic-new")


def test_every_declared_atom_is_handled():
    mapper = tags.TagMapper()
    for atom in tags.KNOWN_ATOMS:
        mapper(atom)
    assert mapper.unknown_atoms == set()
    assert not tags.IGNORED_ATOMS & tags.ATOM_MAP.keys()


def test_every_live_vesum_atom_is_declared():
    if not sources.VESUM_DB_PATH.is_file():
        pytest.skip("live VESUM is not provisioned; synthetic tests still run")
    inventory = sources.Sources().tag_inventory()
    unknown = set(inventory.raw["atoms"]) - tags.KNOWN_ATOMS
    print(f"tag-map: atoms={len(inventory.raw['atoms'])} unknown={sorted(unknown)} vesum={inventory.content_hash}")
    print(f"form_markers={inventory.raw['markers']} exclusion_list={sorted(codes.EXCLUDING_MARKERS)}")
    assert not unknown, f"new VESUM atoms need explicit mapping: {sorted(unknown)!r}"
    assert set(inventory.raw["markers"]) == codes.EXCLUDING_MARKERS
