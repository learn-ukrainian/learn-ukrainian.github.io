"""#11032: Muse is a change subject without becoming a reviewer."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from scripts.agent_runtime import registry
from scripts.review import subject_seat as subjects
from scripts.review.reviewer_resolver import REVIEW_CANDIDATES, ResolverInputs, resolve_reviewer
from tests.claude_route_accounts import HOST_ACCOUNT

EXISTING_SEATS = (
    "agy",
    "claude",
    "codex",
    "cursor",
    "deepseek",
    "gemini",
    "gemma",
    "glm",
    "grok",
    "kimi",
    "pool",
    "qwen",
)
EXISTING_ALIASES = (
    ("grok-build", "grok"),
    ("grok-hermes", "grok"),
    ("hermes-grok", "grok"),
    ("grok-4.7", "grok"),
    ("grok-4.6", "grok"),
    ("grok-4.5", "grok"),
    ("grok-4.7-cursor-fallback", "grok"),
    ("hermes-deepseek", "deepseek"),
    ("kimicc", "kimi"),
    ("kimi-k3", "kimi"),
    ("kimi-code/k3", "kimi"),
    ("claude-desktop", "claude"),
    ("claude-infra", "claude"),
    ("claude-monitor", "claude"),
    ("codex-desktop", "codex"),
)
ADAPTER_SEATS = {
    "__init__.py": None,
    "_output_schema.py": None,
    "_template.py": None,
    "acpx.py": None,
    "agy.py": "agy",
    "base.py": None,
    "claude.py": "claude",
    "codex.py": "codex",
    "codex_events.py": "codex",
    "cursor.py": "cursor",
    "deepseek.py": "deepseek",
    "gemini.py": "gemini",
    "glm.py": "glm",
    "grok_build.py": "grok",
    "hermes_common.py": None,
    "hermes_deepseek.py": "deepseek",
    "hermes_grok.py": "grok",
    "hermes_qwen.py": "qwen",
    "kimi.py": "kimi",
    "kimicc.py": "kimi",
}
MUSE_PATH = "scripts/agent_runtime/adapters/muse.py"
SHARED_PATH = "scripts/agent_runtime/adapters/__init__.py"


def test_closed_vocabulary_adds_only_muse():
    known = subjects.KNOWN_SUBJECT_SEATS
    aliases = subjects._SUBJECT_ALIASES
    assert known == frozenset((*EXISTING_SEATS, "muse"))
    assert aliases == dict(EXISTING_ALIASES)


@pytest.mark.parametrize(
    "raw,expected", [(seat, seat) for seat in EXISTING_SEATS] + list(EXISTING_ALIASES) + [("muse", "muse")]
)
@pytest.mark.parametrize("spelling", [str.lower, str.upper, str.title, lambda text: " " + text.replace("-", "_") + " "])
def test_subject_names_and_existing_separator_aliases(raw, expected, spelling):
    assert subjects.normalize_subject_seat(spelling(raw)) == expected


@pytest.mark.parametrize(
    "raw", ["museum", "muses", "musette", "amuse", "muse-proxy", "muse_proxy", "not-a-seat", "", " "]
)
def test_unknown_subject_names_remain_refused(raw):
    with pytest.raises(ValueError, match=r"unknown subject seat|non-empty seat id"):
        subjects.normalize_subject_seat(raw)


@pytest.mark.parametrize("field", ["name", "concrete_model"])
@pytest.mark.parametrize("identity", ["muse", "Muse", "MUSE", "muse-spark", "MuSe-SpArK", "muse_spark", "MUSE_SPARK"])
def test_muse_identity_matches_even_on_another_route(field, identity):
    fields = dict(name="unrelated", concrete_model="unrelated", route="openrouter", family="unknown", transport="other")
    fields[field] = identity
    assert subjects.candidate_matches_subject_seat(SimpleNamespace(**fields), "muse")


@pytest.mark.parametrize("route", ["muse", "Muse", "MUSE"])
def test_exact_muse_route_matches_unrelated_model(route):
    assert subjects.candidate_matches_subject_seat(
        SimpleNamespace(name="unrelated", concrete_model="unrelated", route=route), "muse"
    )


@pytest.mark.parametrize("field", ["name", "concrete_model", "route", "family", "transport"])
@pytest.mark.parametrize(
    "identity", ["museum", "muses", "musette", "amuse", "prefix-muse-spark", "prefix_muse_spark", "MuSeUm"]
)
def test_muse_lookalikes_do_not_match(field, identity):
    fields = dict(name="unrelated", concrete_model="unrelated", route="other", family="unknown", transport="other")
    fields[field] = identity
    assert not subjects.candidate_matches_subject_seat(SimpleNamespace(**fields), "muse")


@pytest.mark.parametrize("field", ["route", "family", "transport"])
@pytest.mark.parametrize("identity", ["muse-proxy", "muse_proxy", "MuSe-PrOxY"])
def test_muse_prefix_does_not_identify_a_route_family_or_transport(field, identity):
    fields = dict(name="unrelated", concrete_model="unrelated", route="other", family="unknown", transport="other")
    fields[field] = identity
    assert not subjects.candidate_matches_subject_seat(SimpleNamespace(**fields), "muse")


@pytest.mark.parametrize("seat", EXISTING_SEATS)
def test_existing_route_exclusions_are_unchanged(seat):
    entry = SimpleNamespace(
        name="unrelated", concrete_model="unrelated", route=seat.upper(), family="unknown", transport="other"
    )
    assert {
        other for other in subjects.KNOWN_SUBJECT_SEATS if subjects.candidate_matches_subject_seat(entry, other)
    } == {seat}


def test_existing_reviewer_exclusions_match_golden_table():
    expected = {
        "openai_frontier": {"codex"},
        "grok-4.7": {"grok"},
        "grok-4.7-cursor-fallback": {"cursor", "grok"},
        "glm-5.3": {"glm"},
        "claude-opus-5-5": {"claude"},
        "claude-sonnet-5-5": {"claude"},
        "composer-2.5": {"cursor"},
        "pool": {"pool"},
        "pool-xs": {"pool"},
        "gemini-3.8-flash-high": {"agy"},
    }
    assert {
        name: {seat for seat in subjects.KNOWN_SUBJECT_SEATS if subjects.candidate_matches_subject_seat(entry, seat)}
        for name, entry in REVIEW_CANDIDATES.items()
    } == expected


@pytest.fixture
def muse_registry(monkeypatch):
    monkeypatch.setitem(registry.AGENTS, "muse", {"adapter": "scripts.agent_runtime.adapters.muse:MuseAdapter"})
    subjects.adapter_subject_index.cache_clear()
    yield
    subjects.adapter_subject_index.cache_clear()


@pytest.mark.parametrize("filename,seat", [*ADAPTER_SEATS.items(), ("muse.py", "muse")])
def test_every_adapter_keeps_its_classification(muse_registry, filename, seat):
    result = subjects.classify_owned_path("scripts/agent_runtime/adapters/" + filename)
    assert result.kind == ("seat" if seat else "ambiguous")
    if seat:
        assert result.seats == frozenset({seat})


def test_registered_muse_adapter_infers_one_seat(muse_registry):
    result = subjects.prepare_subject_exclusion(owned_paths=(MUSE_PATH,))
    assert result.fail_closed_reason is None
    assert result.seats == frozenset({"muse"})
    assert result.evidence == (MUSE_PATH,)


@pytest.mark.parametrize("paths", [(SHARED_PATH,), (SHARED_PATH, MUSE_PATH)])
def test_shared_adapter_requires_explicit_subject(muse_registry, paths):
    inferred = subjects.prepare_subject_exclusion(owned_paths=paths)
    assert "ambiguous subject-seat inference" in inferred.fail_closed_reason
    assert SHARED_PATH in inferred.fail_closed_reason
    assert inferred.seats == frozenset()
    explicit = subjects.prepare_subject_exclusion(subject_seats=frozenset({"muse"}), owned_paths=paths)
    assert explicit.fail_closed_reason is None
    assert explicit.seats == frozenset({"muse"})


def test_resolver_admits_explicit_muse_for_shared_branch(muse_registry):
    inputs = ResolverInputs(
        author_model="gpt-6.1-sol", owned_paths=(SHARED_PATH, MUSE_PATH), claude_account=HOST_ACCOUNT
    )
    opus = REVIEW_CANDIDATES["claude-opus-5-5"]
    refused = resolve_reviewer(inputs, ladder=((opus,),))
    assert refused.selected is None
    assert "ambiguous subject-seat inference" in refused.fail_closed_reason
    admitted = resolve_reviewer(replace(inputs, subject_seats=frozenset({"muse"})), ladder=((opus,),))
    assert admitted.fail_closed_reason is None
    assert admitted.selected.name == opus.name


def test_write_dispatch_accepts_explicit_muse_subject():
    from scripts import delegate

    args = delegate.build_parser().parse_args(
        [
            "dispatch",
            "--agent",
            "codex",
            "--model",
            "gpt-6.1-sol",
            "--task-id",
            "muse-subject-test",
            "--mode",
            "workspace-write",
            "--subject-seat",
            "muse",
            "--prompt",
            "Test subject admission.",
        ]
    )
    refusal, target = delegate._admit_dispatch_target(args, agent="codex", trees=None)
    assert refusal is None
    assert target.recipient == "codex"


def test_muse_candidate_is_excluded_from_its_own_subject():
    entry = SimpleNamespace(
        name="muse-spark", concrete_model="unrelated", route="openrouter", family="unknown", transport="other"
    )
    reason = subjects.subject_exclusion_reason(
        entry, seats=frozenset({"muse"}), families=frozenset(), evidence=(MUSE_PATH,)
    )
    assert "subject seat muse" in reason
    assert MUSE_PATH in reason
