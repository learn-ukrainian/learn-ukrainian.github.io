"""ULIF synonym-dictionary groups as the evidence for synonym cards (#8714).

A synonym card ships only when both words stand in one checked ULIF synonym
group (``ulif_dictua_sections`` kind ``synonyms`` of an ``ulif_dictua_entries``
row with ``homonym_checked = 1`` and ``status = 'ok'``).  Group members are the
parsed ``terms``; stress marks are stripped for matching.

Membership alone is too loose for a learner card: a group row is a dominant
word with its definition, then its synonyms, then further ``;``-separated
clusters with narrower senses, register labels (розм., заст., рідко …),
member-specific notes and a ``Док.:`` row of perfective partners.  Two members
of one row are not interchangeable in general (ІТИ́ (про дощ, сніг), ПА́ДАТИ …
ДОЩИ́ТИ розм.).  A pair is therefore *core* only when one word is the row's
dominant and the other is an unlabelled member of the dominant's own cluster
with no note of its own; the dominant's note is the sense the card displays.
Any co-membership, core or not, still blocks a word as a distractor.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import unicodedata
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ULIF_SYNONYMS_SOURCE = "ulif-synonyms"
ULIF_DICTUA_URL = "https://lcorp.ulif.org.ua/dictua"

_ANCHOR_TAG = re.compile(r"<a\b[^>]*>|</a>|<font\b[^>]*>|</font>")
_ANY_TAG = re.compile(r"<[^>]+>")
_LETTER = re.compile(r"\w")
# Government words (НОСИ́ТИ кого, що) describe syntax, not register or sense.
_GOVERNMENT_LABEL = re.compile(
    r"^(?:кого|чого|кому|чому|що|чим|ким|на|за|в|у|до|від|з|із|про|над|перед|по|при|[\s,-])+$"
)
_QUERY_CHUNK = 500


def plain(value: str) -> str:
    """Matching key of a ULIF term or Atlas lemma: no stress, brackets or apostrophe variants."""
    text = unicodedata.normalize("NFD", str(value or ""))
    text = text.replace("́", "").replace("̀", "")
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"[\[\]]", " ", text)
    text = re.sub(r"\s*-\s*", "-", text)
    text = text.replace("’", "'").replace("ʼ", "'").replace("`", "'")
    return re.sub(r"\s+", " ", text).strip().casefold()


class UlifSynonymDataUnavailable(RuntimeError):
    """Approved synonym pairs need ULIF synonym groups, and none could be read."""


@dataclass(frozen=True)
class UlifMember:
    lemma: str
    cluster: int
    labels: tuple[str, ...]
    note: str | None
    perfective: bool

    @property
    def register_labels(self) -> tuple[str, ...]:
        return tuple(label for label in self.labels if not _GOVERNMENT_LABEL.match(label.strip(" ,")))


@dataclass(frozen=True)
class UlifSynonymGroup:
    group_id: str
    terms: tuple[str, ...]
    members: tuple[UlifMember, ...]

    @property
    def dominant(self) -> UlifMember:
        return self.members[0]


@dataclass(frozen=True)
class UlifPairEvidence:
    """Why a pair may ship: the group, its dominant, and the displayed sense note."""

    group_id: str
    dominant: str
    sense: str | None

    def as_item_evidence(self) -> dict[str, str]:
        evidence = {"source": ULIF_SYNONYMS_SOURCE, "groupId": self.group_id, "dominant": self.dominant}
        evidence["url"] = ULIF_DICTUA_URL
        return evidence


def _row_tokens(raw_html: str) -> list[tuple[str, str]]:
    """Tokenise one group's HTML: bold terms, italics, parenthesised notes, separators, ``Док.:``."""
    html = _ANCHOR_TAG.sub("", raw_html)
    tokens: list[tuple[str, str]] = []
    index, size = 0, len(html)
    while index < size:
        if html.startswith("<b>", index):
            end = html.find("</b>", index)
            end = size if end < 0 else end
            tokens.append(("term", _ANY_TAG.sub("", html[index + 3 : end])))
            index = end + 4
        elif html.startswith("<i>", index):
            end = html.find("</i>", index)
            end = size if end < 0 else end
            tokens.append(("italic", _ANY_TAG.sub("", html[index + 3 : end])))
            index = end + 4
        elif html[index] == "(":
            depth, end = 1, index + 1
            while end < size and depth:
                depth += (html[end] == "(") - (html[end] == ")")
                end += 1
            note = re.sub(r"\s+", " ", _ANY_TAG.sub("", html[index + 1 : end - 1])).strip()
            tokens.append(("note", note))
            index = end
        elif html.startswith("Док.", index):
            tokens.append(("perfective", ""))
            index += 4
        elif html[index] in ",;.":
            tokens.append(("sep", html[index]))
            index += 1
        elif html[index] == "<":
            end = html.find(">", index)
            index = size if end < 0 else end + 1
        else:
            index += 1
    return tokens


def parse_group_members(raw_html: str) -> list[UlifMember]:
    """Members of the synonym row with cluster, labels, own note and ``Док.`` flag.

    Parsing stops at the first token that cannot belong to the row (the
    example citations), so a malformed tail can only lose members, never
    attach a wrong note or label to one.
    """
    members: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []
    cluster, perfective, closed, previous = 0, False, False, ""
    for kind, value in _row_tokens(raw_html):
        if closed:
            if kind != "perfective":
                break
            closed, perfective, current = False, True, []
        elif kind == "term":
            if not _LETTER.search(value):
                continue
            member = {"lemma": plain(value), "cluster": cluster, "labels": [], "note": None, "perfective": perfective}
            # ОСТАВЛЯ́ТИ [ЗОСТАВЛЯ́ТИ] рідко: a bracketed variant shares what follows.
            current = [*current, member] if value.strip().startswith("[") and current else [member]
            members.append(member)
        elif kind == "italic":
            label = value.strip()
            # Labels follow a term, possibly split over several italics
            # (ЖУВА́ТИ розм., ірон.,); anything else is an example citation.
            continued = previous == "label" and len(label) <= 40 and label.endswith((".", ",", ";"))
            if not current or (previous != "term" and not continued):
                break
            for member in current:
                member["labels"].append(label.rstrip(" ,;"))
            if label.endswith(";"):
                # ЗАНЕПА́ДОК заст.; ПІДУПА́Д …: the cluster separator sits inside the italic.
                cluster += 1
                current = []
            kind = "label"
        elif kind == "note":
            if not current or any(member["note"] is not None for member in current):
                break
            for member in current:
                member["note"] = value
        elif kind == "sep":
            if value == ";":
                cluster += 1
                current = []
            elif value == ",":
                current = []
            elif members:
                closed = True
        elif kind == "perfective":
            perfective, current = True, []
        previous = kind
    return [
        UlifMember(
            lemma=str(member["lemma"]),
            cluster=int(member["cluster"]),
            labels=tuple(member["labels"]),
            note=member["note"],
            perfective=bool(member["perfective"]),
        )
        for member in members
        if member["lemma"]
    ]


def payload_from_row_html(raw_html: str) -> dict[str, Any]:
    """A ``payload_json``-shaped object from one row's HTML (fixtures and ad-hoc checks)."""
    html = _ANCHOR_TAG.sub("", raw_html)
    terms = [{"text": _ANY_TAG.sub("", term)} for term in re.findall(r"<b>(.*?)</b>", html)]
    return {"raw_html": raw_html, "terms": terms, "text": re.sub(r"\s+", " ", _ANY_TAG.sub(" ", html)).strip()}


def group_from_payload(payload: dict[str, Any]) -> UlifSynonymGroup | None:
    """One group from a ``payload_json`` object; ``None`` when its row cannot be read safely."""
    terms = tuple(
        plain(term.get("text") if isinstance(term, dict) else str(term)) for term in payload.get("terms") or []
    )
    terms = tuple(term for term in terms if term)
    text = str(payload.get("text") or "")
    if not terms or not text:
        return None
    members = parse_group_members(str(payload.get("raw_html") or ""))
    dominant_cluster = [member.lemma for member in members if member.cluster == 0 and not member.perfective]
    # The structured row must agree with the dictionary's own term list; otherwise
    # keep the group for distractor exclusion only.
    if not dominant_cluster or list(terms[: len(dominant_cluster)]) != dominant_cluster:
        members = []
    group_id = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    return UlifSynonymGroup(group_id=group_id, terms=terms, members=tuple(members))


def _lists_any(terms_json: str | None, keys: set[str]) -> bool:
    """Whether a group's ``terms`` JSON names any of ``keys``; unreadable terms name nothing."""
    try:
        terms = json.loads(terms_json or "[]")
    except (TypeError, ValueError):
        return False
    if not isinstance(terms, list):
        return False
    return any(plain(term.get("text") if isinstance(term, dict) else str(term)) in keys for term in terms)


class UlifSynonymGroups:
    """Index of checked ULIF synonym groups by member."""

    def __init__(self, groups: Iterable[UlifSynonymGroup]) -> None:
        self._groups: dict[str, UlifSynonymGroup] = {}
        for group in groups:
            self._groups.setdefault(group.group_id, group)
        self._by_term: dict[str, list[UlifSynonymGroup]] = {}
        for group_id in sorted(self._groups):
            group = self._groups[group_id]
            for term in dict.fromkeys(group.terms):
                self._by_term.setdefault(term, []).append(group)

    @classmethod
    def from_payloads(cls, payloads: Iterable[dict[str, Any]]) -> UlifSynonymGroups:
        return cls(group for group in (group_from_payload(payload) for payload in payloads) if group is not None)

    @classmethod
    def from_sources_db(cls, db_path: Path, lemmas: Iterable[str]) -> UlifSynonymGroups | None:
        """Every checked group listing any of ``lemmas`` as a term; ``None`` when the data is absent.

        A group is filed under one headword's entry but lists several words, so
        the match runs over each group's terms, not over ``normalized_query``:
        a group filed under a third headword that lists both an answer and a
        candidate distractor must still block that distractor.  A database
        without the tables, or without a single checked synonym group, counts
        as absent.
        """
        if not db_path.exists():
            return None
        keys = {plain(lemma) for lemma in lemmas} - {""}
        payloads: list[dict[str, Any]] = []
        with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as conn:
            try:
                checked = conn.execute(
                    "SELECT s.id, json_extract(s.payload_json, '$.terms') FROM ulif_dictua_sections s "
                    "JOIN ulif_dictua_entries e ON e.id = s.entry_id "
                    "WHERE s.kind = 'synonyms' AND e.homonym_checked = 1 AND e.status = 'ok'"
                ).fetchall()
                if not checked:
                    return None
                section_ids = [section_id for section_id, terms_json in checked if _lists_any(terms_json, keys)]
                for start in range(0, len(section_ids), _QUERY_CHUNK):
                    chunk = section_ids[start : start + _QUERY_CHUNK]
                    marks = ",".join("?" * len(chunk))
                    rows = conn.execute(f"SELECT payload_json FROM ulif_dictua_sections WHERE id IN ({marks})", chunk)
                    for (payload_json,) in rows:
                        try:
                            payload = json.loads(payload_json)
                        except (TypeError, ValueError):
                            continue
                        if isinstance(payload, dict):
                            payloads.append(payload)
            except sqlite3.OperationalError:
                return None
        return cls.from_payloads(payloads)

    def __len__(self) -> int:
        return len(self._groups)

    def fingerprint(self) -> str:
        """Stable digest of every loaded membership and core-pair input."""
        payload = [asdict(self._groups[group_id]) for group_id in sorted(self._groups)]
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()[:16]

    def co_members(self, lemma: str) -> set[str]:
        """Every word sharing any group with ``lemma`` (any cluster, label or aspect row)."""
        key = plain(lemma)
        return {term for group in self._by_term.get(key, []) for term in group.terms} - {key}

    def shares_group(self, a: str, b: str) -> bool:
        return plain(b) in self.co_members(a)

    def core_pair(self, a: str, b: str) -> UlifPairEvidence | None:
        """Evidence that ``a`` and ``b`` are dominant + plain member of one sense cluster, else ``None``."""
        a_key, b_key = plain(a), plain(b)
        if not a_key or not b_key or a_key == b_key:
            return None
        for group in self._by_term.get(a_key, []):
            if not group.members:
                continue
            dominant = group.dominant
            if dominant.lemma not in (a_key, b_key) or dominant.register_labels:
                continue
            other_key = b_key if dominant.lemma == a_key else a_key
            other = next((member for member in group.members if member.lemma == other_key), None)
            if other is None or other.cluster != 0 or other.perfective:
                continue
            if other.register_labels or other.note is not None:
                continue
            return UlifPairEvidence(group_id=group.group_id, dominant=dominant.lemma, sense=dominant.note)
        return None
