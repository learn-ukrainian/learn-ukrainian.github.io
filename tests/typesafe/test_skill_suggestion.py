"""Unit + optional live tests for TypeSafe skill suggestion (#8201)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from scripts.typesafe import skill_suggestion as ss

ROSTER = (
    ss.SkillRecord(
        name="apple-notes",
        description="Manage Apple Notes via memo CLI: create, search, edit.",
        body_excerpt="Use the memo CLI to create, search, and edit Apple Notes.",
        path="agents_extensions/shared/skills/apple-notes/SKILL.md",
    ),
    ss.SkillRecord(
        name="powerpoint",
        description="Create, read, edit .pptx decks, slides, notes, templates.",
        body_excerpt="General-purpose PowerPoint editing via python-pptx.",
        path="agents_extensions/shared/skills/powerpoint/SKILL.md",
    ),
    ss.SkillRecord(
        name="pptx-author",
        description="Build PowerPoint decks headless with python-pptx.",
        body_excerpt="Headless deck authoring: cover, sections, footnoted valuation numbers.",
        path="agents_extensions/shared/skills/pptx-author/SKILL.md",
    ),
)


class _FakeResponse:
    def __init__(
        self,
        *,
        nouls: dict | None = None,
        choices: dict | None = None,
        model: str = "jev-test",
        input_tokens: int = 10,
        output_tokens: int = 5,
    ):
        self.nouls = {k: SimpleNamespace(noul=v) for k, v in (nouls or {}).items()}
        self.choices = {
            k: SimpleNamespace(
                choice=v["choice"],
                confidence=v.get("confidence", 0.9),
                probabilities=v.get("probabilities", {}),
            )
            for k, v in (choices or {}).items()
        }
        self.model = model
        self.usage = SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens)
        self.request_id = "req-test"


class _FakeClient:
    def __init__(self, response: _FakeResponse):
        self.response = response
        self.calls: list[dict] = []

    def system_one(self, state, questions, *, model=None):
        self.calls.append({"state": state, "questions": questions, "model": model})
        return self.response

    def close(self):
        return None


def test_load_skill_index_reads_real_roster():
    """#8201 — the loader must find and parse the repo's own vendored skills."""
    records = ss.load_skill_index()
    names = {r.name for r in records}
    assert "typesafe-ai" in names
    assert "build-monitoring" in names
    for record in records:
        assert record.name
        assert record.description
        assert len(record.body_excerpt) <= ss.EXCERPT_CHARS


def test_rank_skills_batches_choice_and_three_gate_nouls():
    client = _FakeClient(
        _FakeResponse(
            nouls={
                "gate::acts_on_user_system": 0.9,
                "gate::would_follow_documented_procedure": 0.8,
                "gate::prose_suffices": 0.1,
            },
            choices={
                "which": {
                    "choice": "powerpoint",
                    "probabilities": {"powerpoint": 0.7, "pptx-author": 0.3, "apple-notes": 0.0},
                }
            },
        )
    )
    result = ss.rank_skills("build a pitch deck", ROSTER, client=client)
    assert len(client.calls) == 1
    assert set(client.calls[0]["questions"]) == {
        "which",
        "gate::acts_on_user_system",
        "gate::would_follow_documented_procedure",
        "gate::prose_suffices",
    }
    assert result.ranked[0] == ("powerpoint", pytest.approx(0.7))
    # mean of (0.9, 0.8, 1 - 0.1) = 0.867 -> clears the 0.30 gate
    assert result.gate_score == pytest.approx((0.9 + 0.8 + 0.9) / 3)
    assert result.needs_skill is True


def test_verify_shortlist_picks_winner_when_fit_clears_threshold():
    client = _FakeClient(
        _FakeResponse(
            choices={"which": {"choice": "pptx-author"}},
            nouls={
                "fits::apple-notes": 0.02,
                "fits::powerpoint": 0.38,
                "fits::pptx-author": 0.73,
            },
        )
    )
    result = ss.verify_shortlist("build a pitch deck", list(ROSTER), client=client)
    assert len(client.calls) == 1
    assert set(client.calls[0]["questions"]) == {
        "which",
        "fits::apple-notes",
        "fits::powerpoint",
        "fits::pptx-author",
    }
    assert result.winner == "pptx-author"
    assert result.best_fit == pytest.approx(0.73)
    assert result.accepted is True


def test_verify_shortlist_rejects_all_when_best_fit_is_weak():
    """#8201 — verify call must allow reject-all even when Choice still names a winner."""
    client = _FakeClient(
        _FakeResponse(
            choices={"which": {"choice": "xurl"}},
            nouls={"fits::apple-notes": 0.05, "fits::powerpoint": 0.1, "fits::pptx-author": 0.2},
        )
    )
    result = ss.verify_shortlist("post this to mastodon", list(ROSTER), client=client)
    assert result.winner == "xurl"
    assert result.accepted is False
