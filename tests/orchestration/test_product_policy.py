"""Product admission policy (#12680, AC-01): stub and real policy agree; no policy refuses.

The stub is built here from today's machinery constants (the rules core's content
agent types, the Ukrainian review seats and the reviewer resolver's learner paths),
so the equivalence cases prove the real product file preserves today's decisions.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from lu_machinery.lib import rules_core
from lu_machinery.orchestration import dispatch_admission, product_policy
from lu_machinery.review import reviewer_resolver, ukrainian_seats

REAL = product_policy.default_policy_path()


def _stub_document() -> dict:
    document = {
        "schema": product_policy.SCHEMA,
        "schema_version": product_policy.SCHEMA_VERSION,
        "origin": product_policy.POLICY_REL,
        "seats": {
            "content_agent_types": sorted(rules_core.CONTENT_AGENT_TYPES),
            "ukrainian_content_families": sorted(reviewer_resolver._UKRAINIAN_CONTENT_FAMILIES),
            "ukrainian_review_seats": [
                {"route": route, "family": family} for route, family in sorted(ukrainian_seats.UKRAINIAN_SEAT_ROUTES)
            ],
        },
        "receipts": {
            "learner_payload_paths": list(reviewer_resolver.UKRAINIAN_CONTENT_PATHS),
            "review_receipts_by_author_family": {
                author: sorted(ukrainian_seats.required_ukrainian_seats({author}))
                for author in sorted(ukrainian_seats.UKRAINIAN_SEAT_FAMILIES)
            },
            "review_receipts_default": sorted(ukrainian_seats.UKRAINIAN_SEAT_FAMILIES),
        },
    }
    document["content_sha256"] = product_policy.canonical_digest(document)
    return document


def _write(directory: Path, document: dict) -> Path:
    path = directory / "admission_policy.v1.json"
    path.write_text(json.dumps(document, indent=2), encoding="utf-8")
    return path


@pytest.fixture(params=["stub", "real"])
def policy(request, tmp_path: Path) -> product_policy.ProductPolicy:
    if request.param == "real":
        return product_policy.load_policy(REAL)
    return product_policy.load_policy(_write(tmp_path, _stub_document()))


LOOKALIKE = "lookalike"
NOT_CANONICAL = "not-canonical"
INVALID = "invalid-input"

# (case id, changes, expected): True/False, or the refusal kind.
CHANGE_CASES = [
    # metadata beside learner content
    ("status-json", ["curriculum/l2-uk-en/a1/status/my-family.json"], True),
    ("arc-doc", ["docs/epics/fresh-build-a1-arc.md"], True),
    ("other-epic-doc", ["docs/epics/machinery-move.md"], False),
    ("machinery-config", ["scripts/config.py"], False),
    ("readme", ["README.md"], False),
    ("empty-change-set", [], False),
    # learner payloads
    ("lesson-page", ["curriculum/l2-uk-en/a1/my-family.md"], True),
    ("lexicon-ui", ["site/src/lib/lexicon/entry.ts"], True),
    ("writer-prompt", ["scripts/build/fresh/prompt.py"], True),
    ("activity-schema", ["schemas/activities-v2.json"], True),
    ("stress-overrides", ["scripts/data/stress_overrides.yaml"], True),
    ("engine-not-prompt", ["scripts/build/fresh/assemble.py"], False),
    ("mixed", ["scripts/config.py", "scripts/lexicon/normalize.py"], True),
    # rename origins: either side counts
    ("rename-out-of-curriculum", [("curriculum/l2-uk-en/a1/old.md", "docs/archive/old.md")], True),
    ("rename-into-lexicon", [("docs/notes.md", "scripts/lexicon/notes.py")], True),
    ("rename-outside", [("docs/a.md", "docs/b.md")], False),
    # lookalikes fold to a learner path but are not one
    ("case-lookalike", ["Curriculum/l2-uk-en/a1/x.md"], LOOKALIKE),
    ("cyrillic-lookalike", ["сurriculum/l2-uk-en/a1/x.md"], LOOKALIKE),
    ("slash-lookalike", ["scripts/lexicon∕normalize.py"], LOOKALIKE),
    ("digit-lookalike", ["scripts/curricu1um/x.py"], LOOKALIKE),
    ("rename-origin-lookalike", [("Curriculum/x.md", "docs/x.md")], LOOKALIKE),
    # paths that are not canonical never reach a decision
    ("dot-prefix", ["./curriculum/x.md"], NOT_CANONICAL),
    ("absolute", ["/curriculum/x.md"], NOT_CANONICAL),
    ("parent-escape", ["curriculum/../scripts/config.py"], NOT_CANONICAL),
    ("padded", [" curriculum/x.md"], NOT_CANONICAL),
    ("zero-width", ["curriculum/​x.md"], NOT_CANONICAL),
    ("not-a-string", [None], NOT_CANONICAL),
    ("rename-wrong-arity", [("curriculum/x.md",)], NOT_CANONICAL),
    ("bare-string-not-a-collection", "curriculum/x.md", NOT_CANONICAL),
]

SEAT_CASES = [
    ("content-seat", "curriculum-orchestrator", True),
    ("infra-seat", "infra-orchestrator", False),
    ("other-seat", "claude", False),
    ("case-lookalike", "Curriculum-Orchestrator", LOOKALIKE),
    ("underscore-lookalike", "curriculum_orchestrator", LOOKALIKE),
    ("hyphen-lookalike", "curriculum‑orchestrator", LOOKALIKE),
    ("cyrillic-lookalike", "curriculum-оrchestrator", LOOKALIKE),
    ("padded-lookalike", "curriculum-orchestrator ", LOOKALIKE),
]

REVIEW_SEAT_CASES = [
    ("gemini-seat", ("agy", "google"), True),
    ("sol-seat", ("codex", "openai"), True),
    ("claude-not-a-seat", ("claude", "anthropic"), False),
    ("crossed-route", ("agy", "openai"), False),
    ("route-lookalike", ("Codex", "openai"), LOOKALIKE),
    ("family-lookalike", ("codex", "0penai"), LOOKALIKE),
]

FAMILY_CASES = [
    ("anthropic", "anthropic", True),
    ("openai", "openai", True),
    ("google", "google", True),
    ("xai", "xai", False),
    ("deepseek", "deepseek", False),
    ("lookalike", "Google", LOOKALIKE),
]

RECEIPT_CASES = [
    ("sol-author", {"openai"}, {"google"}),
    ("gemini-author", {"google"}, {"openai"}),
    ("claude-author", {"anthropic"}, {"google", "openai"}),
    ("mixed-authors", {"openai", "google"}, {"google", "openai"}),
    ("unattested", set(), {"google", "openai"}),
    ("lookalike-author", {"OpenAI"}, LOOKALIKE),
    ("bare-string-not-a-collection", "openai", INVALID),
]


def _outcome(call):
    try:
        return call()
    except product_policy.ProductPolicyError as exc:
        return {"lookalike_seat_name": LOOKALIKE, "lookalike_learner_path": LOOKALIKE,
                "change_path_not_canonical": NOT_CANONICAL, "decision_input_invalid": INVALID}.get(exc.code, exc.code)


@pytest.mark.parametrize(("case", "changes", "expected"), CHANGE_CASES, ids=[c[0] for c in CHANGE_CASES])
def test_learner_payload_receipt_decision(policy, case, changes, expected) -> None:
    assert _outcome(lambda: policy.requires_ukrainian_review(changes)) == expected


ANSWERED_CHANGE_CASES = [case for case in CHANGE_CASES if isinstance(case[2], bool)]


@pytest.mark.parametrize(
    ("case", "changes", "expected"), ANSWERED_CHANGE_CASES, ids=[c[0] for c in ANSWERED_CHANGE_CASES]
)
def test_answered_decisions_match_todays_resolver(case, changes, expected) -> None:
    paths = tuple(path for change in changes for path in (change if isinstance(change, tuple) else (change,)))
    inputs = SimpleNamespace(language_lane=False, review_profile="code", changed_paths=paths, owned_paths=())
    assert reviewer_resolver.is_ukrainian_content_change(inputs) is expected


@pytest.mark.parametrize(("case", "agent_type", "expected"), SEAT_CASES, ids=[c[0] for c in SEAT_CASES])
def test_content_seat_decision(policy, case, agent_type, expected) -> None:
    assert _outcome(lambda: policy.is_content_seat(agent_type)) == expected
    if isinstance(expected, bool):
        assert (agent_type in rules_core.CONTENT_AGENT_TYPES) is expected


@pytest.mark.parametrize(("case", "seat", "expected"), REVIEW_SEAT_CASES, ids=[c[0] for c in REVIEW_SEAT_CASES])
def test_ukrainian_review_seat_decision(policy, case, seat, expected) -> None:
    assert _outcome(lambda: policy.is_ukrainian_review_seat(*seat)) == expected
    if isinstance(expected, bool):
        assert (seat in ukrainian_seats.UKRAINIAN_SEAT_ROUTES) is expected


@pytest.mark.parametrize(("case", "family", "expected"), FAMILY_CASES, ids=[c[0] for c in FAMILY_CASES])
def test_ukrainian_content_family_decision(policy, case, family, expected) -> None:
    assert _outcome(lambda: policy.ukrainian_content_family_allowed(family)) == expected
    if isinstance(expected, bool):
        assert (family in reviewer_resolver._UKRAINIAN_CONTENT_FAMILIES) is expected


@pytest.mark.parametrize(("case", "authors", "expected"), RECEIPT_CASES, ids=[c[0] for c in RECEIPT_CASES])
def test_review_receipt_decision(policy, case, authors, expected) -> None:
    result = _outcome(lambda: policy.required_review_receipts(authors))
    assert result == (expected if expected in (LOOKALIKE, INVALID) else frozenset(expected))
    if expected not in (LOOKALIKE, INVALID):
        assert ukrainian_seats.required_ukrainian_seats(authors) == frozenset(expected)


def test_stub_and_real_policy_are_the_same_decisions(tmp_path: Path) -> None:
    assert product_policy.load_policy(_write(tmp_path, _stub_document())) == product_policy.load_policy(REAL)


def test_admission_interface_reads_the_real_policy() -> None:
    assert dispatch_admission.is_content_seat("curriculum-orchestrator") is True
    assert dispatch_admission.ukrainian_content_family_allowed("google") is True
    assert dispatch_admission.is_ukrainian_review_seat("codex", "openai") is True
    assert dispatch_admission.requires_ukrainian_review([("curriculum/x.md", "docs/x.md")]) is True
    assert dispatch_admission.required_review_receipts({"openai"}) == frozenset({"google"})


# --- fail closed ------------------------------------------------------------


@pytest.fixture
def no_policy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    missing = tmp_path / "absent" / "admission_policy.v1.json"
    monkeypatch.setattr(product_policy, "default_policy_path", lambda: missing)
    return missing


@pytest.fixture
def wrong_version(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    document = _stub_document()
    document["schema_version"] = 2
    document["content_sha256"] = product_policy.canonical_digest(document)
    path = _write(tmp_path, document)
    monkeypatch.setattr(product_policy, "default_policy_path", lambda: path)
    return path


@pytest.mark.parametrize(
    ("fixture", "code"), [("no_policy", "policy_missing"), ("wrong_version", "policy_version_incompatible")]
)
def test_admission_fails_closed(request, fixture, code, tmp_path: Path) -> None:
    request.getfixturevalue(fixture)
    swept: list[Path] = []
    for mode in ("workspace-write", "danger", "read-only"):
        with pytest.raises(product_policy.ProductPolicyError) as raised:
            dispatch_admission.evaluate(mode, tmp_path / "tasks", on_dead=lambda path, _state: swept.append(path))
        assert raised.value.code == code
        assert isinstance(raised.value, ValueError)
    with pytest.raises(product_policy.ProductPolicyError, match=code):
        dispatch_admission.precheck("workspace-write")
    for decide in (
        lambda: dispatch_admission.is_content_seat("curriculum-orchestrator"),
        lambda: dispatch_admission.ukrainian_content_family_allowed("google"),
        lambda: dispatch_admission.is_ukrainian_review_seat("codex", "openai"),
        lambda: dispatch_admission.requires_ukrainian_review(["curriculum/x.md"]),
        lambda: dispatch_admission.required_review_receipts({"openai"}),
    ):
        with pytest.raises(product_policy.ProductPolicyError, match=code):
            decide()
    assert swept == []
    assert not (tmp_path / "tasks").exists()


@pytest.mark.parametrize("version", [2, 0, True, "1", 1.0, None])
def test_wrong_schema_version_is_refused(tmp_path: Path, version) -> None:
    document = _stub_document()
    document["schema_version"] = version
    document["content_sha256"] = product_policy.canonical_digest(document)
    with pytest.raises(product_policy.ProductPolicyError) as raised:
        product_policy.load_policy(_write(tmp_path, document))
    assert raised.value.code == "policy_version_incompatible"


def test_missing_policy_file_is_refused(tmp_path: Path) -> None:
    with pytest.raises(product_policy.ProductPolicyError) as raised:
        product_policy.load_policy(tmp_path / "admission_policy.v1.json")
    assert raised.value.code == "policy_missing"
