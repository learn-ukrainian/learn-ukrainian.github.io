"""Subject-name helpers for deterministic BIO source-first gates."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BIO_PLANS_DIR = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "plans" / "bio"

CYRILLIC_WORD_RE = re.compile(r"[А-Яа-яІіЇїЄєҐґ][А-Яа-яІіЇїЄєҐґ'’ʼ-]*")
TITLE_PREFIX_RE = re.compile(r"^#{1,6}\s*")
BIOGRAPHY_PREFIX_RE = re.compile(r"^біографія\s*:\s*", re.IGNORECASE)

LEADING_TITLES = {
    "архієпископ",
    "гетьман",
    "княгиня",
    "княжна",
    "князь",
    "король",
    "митрополит",
    "патріарх",
    "свята",
    "святий",
}

UKRAINIAN_SUFFIXES = (
    "ського",
    "цького",
    "зького",
    "ового",
    "євого",
    "евої",
    "ової",
    "ого",
    "ему",
    "ому",
    "ими",
    "ами",
    "ями",
    "ах",
    "ях",
    "ою",
    "ею",
    "ий",
    "ій",
    "а",
    "я",
    "у",
    "ю",
    "и",
    "і",
)


def subject_phrase(text: str) -> str:
    """Return the likely person-name phrase from a plan title or wiki H1."""
    value = TITLE_PREFIX_RE.sub("", text.strip())
    value = BIOGRAPHY_PREFIX_RE.sub("", value).strip()
    if ":" in value:
        value = value.split(":", 1)[0].strip()
    value = re.split(r"\s+[—–]\s+", value, maxsplit=1)[0].strip()
    for sep in (" та ", " і "):
        if sep in value:
            value = value.split(sep, 1)[0].strip()
            break
    for sep in (" в ", " у "):
        if sep in value:
            prefix = value.split(sep, 1)[0].strip()
            if len(CYRILLIC_WORD_RE.findall(prefix)) >= 2:
                value = prefix
                break
    return value


def cyrillic_tokens(text: str) -> list[str]:
    """Tokenize the subject phrase, dropping leading honorific/title words."""
    tokens = [m.group(0).casefold() for m in CYRILLIC_WORD_RE.finditer(subject_phrase(text))]
    while tokens and tokens[0] in LEADING_TITLES:
        tokens.pop(0)
    return tokens


def token_keys(token: str) -> set[str]:
    """Return conservative stem keys for Ukrainian name-token matching."""
    # Normalize ґ→г: the restored letter ґ was banned under Soviet orthography,
    # so the same person's name appears with either letter across sources
    # (e.g. canonical «Ґео Шкурупій» vs a plan title «Гео Шкурупій»). For
    # person-identity matching they are the same name.
    base = token.casefold().replace("’", "'").replace("ʼ", "'").replace("ґ", "г")
    keys = {base}
    for suffix in UKRAINIAN_SUFFIXES:
        if base.endswith(suffix) and len(base) - len(suffix) >= 4:
            keys.add(base[: -len(suffix)])
    return keys


def surname_keys(text: str) -> set[str]:
    """Return comparable keys for the final token in a subject phrase."""
    tokens = cyrillic_tokens(text)
    if not tokens:
        return set()
    return token_keys(tokens[-1])


def given_name_keys(text: str) -> set[str]:
    """Return comparable keys for the first non-title token in a subject phrase."""
    tokens = cyrillic_tokens(text)
    if not tokens:
        return set()
    return token_keys(tokens[0])


def shares_surname(left: str, right: str) -> bool:
    """True when two subject phrases share a 4+ character surname key."""
    return bool(surname_keys(left) & surname_keys(right))


def same_person(left: str, right: str) -> bool:
    """Conservative person match for wiki H1 checks.

    Surname agreement is required. If both sides have an explicit given name,
    the given-name keys must also agree so Mykola Kulish and Panteleimon Kulish
    remain distinguishable.
    """
    if not shares_surname(left, right):
        return False
    left_tokens = cyrillic_tokens(left)
    right_tokens = cyrillic_tokens(right)
    if len(left_tokens) >= 2 and len(right_tokens) >= 2:
        return bool(given_name_keys(left) & given_name_keys(right))
    return True


def load_plan_title(slug: str, *, plans_dir: Path = BIO_PLANS_DIR) -> str | None:
    """Load a BIO plan title by slug."""
    path = plans_dir / f"{slug}.yaml"
    if not path.exists():
        return None
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        return None
    title = data.get("title")
    return str(title).strip() if title else None
