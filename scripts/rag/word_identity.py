"""Citation identity for receipt comparisons."""

APOSTROPHES = str.maketrans({"’": "'", "ʼ": "'", "`": "'", "\u2018": "'"})


def normalize_evidence_form(text: str) -> str:
    """Fold case, stress and apostrophes for word identity, never lemmatization.

    Whitespace, letters (including Ukrainian і/ї/й) and punctuation stay exact.
    Case correctness belongs to the language judgement, not citation binding.
    """
    return text.translate(APOSTROPHES).replace("\u0301", "").replace("\u0300", "").casefold()
