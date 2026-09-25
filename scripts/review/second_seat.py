"""The second-seat sample (#8430 r4, operator decision 5): one lesson in ten is reviewed twice.

A lesson is selected when ``int(sha256("<level>/<slug>/<n>")) % divisor == 0`` (the
divisor is ``second_seat_divisor`` in ``scripts/config/review_parameters.yaml``). The
second review runs on the **same manifest** as the first, on a seat of a **third** family
(neither the writer's nor the first reviewer's), and is validated like the first. The two
findings files are compared by location and dimension; the result is one ``agreement``
row, and a disagreement on a BLOCKER or MAJOR is a settle item that holds the module.
The module verdict keeps using the first seat's verdict.

Families are never self-reported: they come from the resolver of the code-review
closeout (``scripts.review.reviewer_resolver.resolve_author_family``), which fails closed
for an unknown or ambiguous identity.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

import yaml

from scripts.review import findings_db
from scripts.review.reviewer_resolver import UNRESOLVED_AUTHOR_FAMILIES, resolve_author_family

BLOCKING = frozenset({"BLOCKER", "MAJOR"})
LIVE_STATUSES = frozenset({"active", "persisting"})
_PLACEHOLDER_MODELS = frozenset({"", "unknown", "auto", "unattested-harness"})


class IdentityError(ValueError):
    """An identity (model, harness or family) is unknown, ambiguous or unattested: fail closed."""


class SecondSeatError(ValueError):
    """The second review is not allowed: not selected, wrong family, or no first review on that manifest."""


def concrete_family(identifier: str, *, what: str) -> str:
    """The concrete model family of ``identifier`` (a model id or a seat name); IdentityError otherwise."""
    if not isinstance(identifier, str) or identifier.strip().lower() in _PLACEHOLDER_MODELS:
        raise IdentityError(f"{what}: {identifier!r} names no model")
    family = resolve_author_family(identifier)
    if family in UNRESOLVED_AUTHOR_FAMILIES or family.startswith("cursor"):
        raise IdentityError(f"{what}: {identifier!r} does not resolve to a concrete family ({family})")
    return family


def writer_family(state_dir: Path, n: int) -> str:
    """The family of the seat that wrote lesson ``n``, from ``lesson-<n>.writer.yaml`` through the resolver.

    The recorded seat model is tried first; when it does not resolve, the writer seat name is.
    """
    path = Path(state_dir) / f"lesson-{n}.writer.yaml"
    try:
        meta = yaml.safe_load(path.read_bytes())
    except (OSError, yaml.YAMLError) as error:
        raise IdentityError(f"the writer record {path.name} is unreadable: {error}") from error
    if not isinstance(meta, dict):
        raise IdentityError(f"the writer record {path.name} is not a mapping")
    for key in ("model", "writer"):
        try:
            return concrete_family(meta.get(key), what=f"{path.name} {key}")
        except IdentityError:
            continue
    raise IdentityError(f"{path.name} names no writer model or seat that resolves to a family")


def selected(level: str, slug: str, n: int, divisor: int) -> bool:
    """Whether lesson ``n`` of ``level``/``slug`` is in the second-seat sample (deterministic)."""
    digest = hashlib.sha256(f"{level}/{slug}/{n}".encode()).hexdigest()
    return int(digest, 16) % divisor == 0


def is_third_family(writer: str, first: str, second: str) -> bool:
    return len({writer, first, second}) == 3


# --- comparison -------------------------------------------------------------------------


def _keys(finding: dict[str, Any]) -> list[tuple[str | None, str | None, int | None]]:
    locations = finding.get("locations") or []
    if not locations and isinstance(finding.get("scope"), dict):
        locations = [finding["scope"]]
    return [(item.get("tab"), item.get("activity"), item.get("item")) for item in locations if isinstance(item, dict)]


def _overlap(one: tuple, other: tuple) -> bool:
    if one[0] != other[0]:
        return False
    if one[1] is None or other[1] is None:
        return True
    return one[1] == other[1] and (one[2] is None or other[2] is None or one[2] == other[2])


def _matches(first: dict[str, Any], second: dict[str, Any]) -> bool:
    if first.get("dimension") != second.get("dimension"):
        return False
    return any(_overlap(a, b) for a in _keys(first) for b in _keys(second))


def compare_findings(first: list[dict[str, Any]], second: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare two seats' findings by dimension and location.

    Only active and persisting findings count. A finding with no partner on the other side
    is a ``no_match`` disagreement; a matched pair with one blocking (BLOCKER/MAJOR) and one
    MINOR side is a ``severity_boundary`` disagreement, recorded against the blocking side
    (the two seats would return different verdicts).
    """
    live_a = [item for item in first if item.get("status") in LIVE_STATUSES]
    live_b = [item for item in second if item.get("status") in LIVE_STATUSES]
    taken: set[int] = set()
    entries: list[dict[str, Any]] = []
    for finding in live_a:
        partner = next((i for i, other in enumerate(live_b) if i not in taken and _matches(finding, other)), None)
        if partner is None:
            entries.append(_entry("a", finding, "no_match"))
            continue
        taken.add(partner)
        other = live_b[partner]
        if (finding["severity"] in BLOCKING) != (other["severity"] in BLOCKING):
            blocking_side = ("a", finding) if finding["severity"] in BLOCKING else ("b", other)
            entries.append(_entry(*blocking_side, "severity_boundary"))
    entries.extend(_entry("b", other, "no_match") for i, other in enumerate(live_b) if i not in taken)
    return {"agreed": not entries, "disagreed": entries}


def _entry(side: str, finding: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "side": side,
        "finding_id": finding["id"],
        "dimension": finding["dimension"],
        "severity": finding["severity"],
        "reason": reason,
        "blocking": finding["severity"] in BLOCKING,
    }


# --- recording --------------------------------------------------------------------------


def check_eligible(
    conn: sqlite3.Connection,
    *,
    level: str,
    slug: str,
    lesson_n: int,
    manifest_sha256: str,
    first_attempt: sqlite3.Row | None,
    second_family: str,
    writer: str,
    params: dict[str, Any],
) -> sqlite3.Row:
    """The first attempt this second review is paired with; SecondSeatError when it may not run.

    It must be selected by the rule, a first-seat attempt accepted on the same manifest must
    exist, and the second reviewer's family must differ from the writer's and the first reviewer's.
    """
    if not selected(level, slug, lesson_n, params["second_seat_divisor"]):
        raise SecondSeatError(f"lesson {lesson_n} of {level}/{slug} is not in the second-seat sample")
    first = first_attempt or _first_attempt(conn, level, slug, lesson_n, manifest_sha256)
    if first is None:
        raise SecondSeatError("no first-seat review of this lesson was accepted on this manifest")
    if not is_third_family(writer, first["reviewer_family"], second_family):
        raise SecondSeatError(
            f"the second seat must be a third family: writer {writer}, first seat {first['reviewer_family']}, "
            f"second seat {second_family}"
        )
    return first


def _first_attempt(
    conn: sqlite3.Connection, level: str, slug: str, lesson_n: int, manifest_sha256: str
) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM attempts WHERE level = ? AND slug = ? AND lesson_n = ? AND manifest_sha256 = ? AND role = 'first'"
        " AND seed_id IS NULL AND verdict IN ('APPROVE', 'REVISE') ORDER BY rowid DESC LIMIT 1",
        (level, slug, lesson_n, manifest_sha256),
    ).fetchone()


def _findings_of(conn: sqlite3.Connection, attempt: sqlite3.Row) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT finding_json FROM findings WHERE review_id = ? AND attempt_id = ? ORDER BY rowid",
        (attempt["review_id"], attempt["attempt_id"]),
    ).fetchall()
    return [json.loads(row["finding_json"]) for row in rows]


def record_agreement(
    conn: sqlite3.Connection, first: sqlite3.Row, second: sqlite3.Row, *, opened_at: str
) -> dict[str, Any]:
    """Write the ``agreement`` row for two accepted attempts and open a settle item per blocking disagreement.

    Runs inside the caller's transaction. A blocking disagreement opens the item on the
    blocking finding; that item holds the module verdict until it is decided.
    """
    verdict = compare_findings(_findings_of(conn, first), _findings_of(conn, second))
    findings_db.insert_agreement(
        conn,
        level=first["level"],
        slug=first["slug"],
        lesson_n=first["lesson_n"],
        attempt_a=first["attempt_id"],
        attempt_b=second["attempt_id"],
        agreed=verdict["agreed"],
        disagreed=verdict["disagreed"],
    )
    opened = []
    for entry in verdict["disagreed"]:
        if not entry["blocking"]:
            continue
        owner = first if entry["side"] == "a" else second
        item = findings_db.open_settle_item(
            conn,
            ref=findings_db.finding_ref(owner["review_id"], owner["attempt_id"], entry["finding_id"]),
            kind="second_seat_disagreement",
            level=first["level"],
            slug=first["slug"],
            lesson_n=first["lesson_n"],
            manifest_sha256=first["manifest_sha256"],
            opened_at=opened_at,
        )
        opened.append(item)
    return {**verdict, "settle_items": opened}


# --- CLI --------------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.review.second_seat",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Say whether a lesson is in the second-seat sample (1 in N; N is second_seat_divisor in\n"
            "scripts/config/review_parameters.yaml), or list the sampled lessons of a plan.\n"
            "Use before dispatching a review: a sampled lesson is reviewed a second time, on the same\n"
            "manifest, by a seat of a third family; record --second-seat writes the comparison.\n"
            "Do NOT use it to record a review (scripts.review.record does)."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.review.second_seat select a1 my-module 4\n"
            "  .venv/bin/python -m scripts.review.second_seat plan a1 my-module --lessons 12\n"
            "Outputs: one JSON object on stdout. Writes nothing. Exit 0."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)
    one = sub.add_parser("select", help="is one lesson in the sample")
    one.add_argument("level")
    one.add_argument("slug")
    one.add_argument("n", type=int)
    many = sub.add_parser("plan", help="the sampled lessons among 1..N")
    many.add_argument("level")
    many.add_argument("slug")
    many.add_argument("--lessons", type=int, required=True, help="the module's lesson count")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    divisor = findings_db.load_parameters()["second_seat_divisor"]
    if args.command == "select":
        payload: dict[str, Any] = {"divisor": divisor, "selected": selected(args.level, args.slug, args.n, divisor)}
    else:
        payload = {
            "divisor": divisor,
            "selected": [n for n in range(1, args.lessons + 1) if selected(args.level, args.slug, n, divisor)],
        }
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
