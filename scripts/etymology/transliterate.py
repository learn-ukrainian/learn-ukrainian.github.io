"""Ukrainian Cyrillic to ASCII slug transliteration."""

from __future__ import annotations

import unicodedata

UK_TO_ASCII = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "h",
    "ґ": "g",
    "д": "d",
    "е": "e",
    "є": "ie",
    "ж": "zh",
    "з": "z",
    "и": "y",
    "і": "i",
    "ї": "i",
    "й": "i",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "kh",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "shch",
    "ь": "",
    "ю": "iu",
    "я": "ia",
    "'": "",
    "ʼ": "",
}


def transliterate(text: str) -> str:
    """Lower-case Ukrainian Cyrillic -> ASCII slug-safe form.

    Strips stress marks (combining acute U+0301), apostrophes, soft signs.
    Collapses non-letter runs to single hyphens. Strips leading/trailing hyphens.

    Examples:
        'серце' -> 'sertse'
        'дім' -> 'dim'
        'жінка' -> 'zhinka'
        'абре́віатура' (with stress mark) -> 'abreviatura'
    """

    pieces: list[str] = []
    pending_hyphen = False

    normalized = unicodedata.normalize("NFD", text.lower())
    for char in normalized:
        if char == "\u0301" or unicodedata.category(char) == "Mn":
            continue

        replacement = UK_TO_ASCII.get(char)
        if replacement is not None:
            if replacement:
                if pending_hyphen and pieces:
                    pieces.append("-")
                pieces.append(replacement)
                pending_hyphen = False
            continue

        if char.isascii() and char.isalnum():
            if pending_hyphen and pieces:
                pieces.append("-")
            pieces.append(char)
            pending_hyphen = False
        else:
            pending_hyphen = bool(pieces)

    return "".join(pieces).strip("-")
