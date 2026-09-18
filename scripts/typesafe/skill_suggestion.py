"""TypeSafe (Jev) System One skill suggestion — rank + verify pipeline.

Issue: #8201 (epic #6943)
Cookbook: https://docs.typesafe.ai/cookbooks/skill_suggestion.md

Two batched ``system_one`` requests pick at most one skill from the local
agent skill roster for a given turn:

1. **Rank** — one ``Choice`` over every skill's name + description, plus
   three ``Noul`` gate questions on whether the turn needs a skill at all
   (mean of the three, one inverted, decides ``needs_skill``).
2. **Verify** — the top-3 shortlist re-read with each skill's full
   description + a body excerpt, another ``Choice`` plus one per-candidate
   ``Noul`` ("does this skill actually do it?"). The best fit score gates
   whether any winner is returned; a weak shortlist rejects all three.

The result is advisory only — it ranks one skill higher, never replaces the
agent's own roster or judgment (see ``suggestion_block``).

Credentials: ``TYPESAFE_API_KEY`` or ``~/.secrets/typesafe-ai.key``
(also accepts ``~/.secrets/typesafe-ai.key``).
"""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Protocol

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_GLOB = "agents_extensions/**/skills/*/SKILL.md"

# --- thresholds owned by code (cookbook defaults; tune here) ---
SHORTLIST = 3  # candidates carried from the rank call into the verify call
EXCERPT_CHARS = 700  # SKILL.md body characters each shortlist candidate brings
GATE_THRESHOLD = 0.30  # mean of the three rank-call nouls; below = no suggestion
FITS_THRESHOLD = 0.30  # best verify-call "fits" noul; below = reject the whole shortlist

CHOICE_INSTRUCTIONS = "Which of these skills, if any, is the right one to load to help with the user's current turn?"
GATE_QUESTIONS: dict[str, str] = {
    "acts_on_user_system": (
        "Is the assistant being asked to act on the user's files, accounts, devices, "
        "or online services, rather than only to explain or advise?"
    ),
    "would_follow_documented_procedure": (
        "Would a careful expert answering this consult a specific documented procedure "
        "or set of commands, rather than answering from general understanding?"
    ),
    "prose_suffices": (
        "Could a knowledgeable generalist fully satisfy this request in prose, with "
        "no tools, no documentation, and no access to the user's files or accounts?"
    ),
}
INVERTED_GATE_QUESTIONS = frozenset({"prose_suffices"})  # a yes here points away from needing a skill

RERANK_INSTRUCTIONS = (
    "Exactly one of these skills is the right one to load for the user's current turn. "
    "Which one? Read what each actually does, not just its name."
)


def _question_primitives():
    """Return Choice/Noul classes; stub when SDK absent (hermetic CI)."""
    try:
        from typesafe_sdk import Choice, Noul

        return Choice, Noul
    except ImportError:  # pragma: no cover - exercised in CI without extra-index

        class _Q:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        class Noul(_Q):
            def __init__(self, instructions="", **kwargs):
                super().__init__(instructions=instructions, **kwargs)

        class Choice(_Q):
            def __init__(self, instructions="", criteria=None, **kwargs):
                super().__init__(instructions=instructions, criteria=criteria or {}, **kwargs)

        return Choice, Noul


class _SystemOneClient(Protocol):
    def system_one(
        self,
        state: Any,
        questions: Mapping[str, Any],
        *,
        model: str | None = None,
    ) -> Any: ...


@dataclass(frozen=True)
class TypeSafeReceipt:
    """Usage + model id for spend / reproducibility logs."""

    model: str | None
    input_tokens: int | None
    output_tokens: int | None
    request_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SkillRecord:
    """One vendored ``SKILL.md``: name + description (Call 1) + body excerpt (Call 2)."""

    name: str
    description: str
    body_excerpt: str
    path: str


@dataclass(frozen=True)
class RankResult:
    """Call 1 — Choice ranking over the full roster + the three gate nouls."""

    ranked: tuple[tuple[str, float], ...]
    gate_score: float
    gate_values: Mapping[str, float]
    receipt: TypeSafeReceipt

    @property
    def needs_skill(self) -> bool:
        """#8201 — mean of the (oriented) gate nouls must clear the threshold."""
        return self.gate_score >= GATE_THRESHOLD


@dataclass(frozen=True)
class VerifyResult:
    """Call 2 — Choice over the shortlist + one per-candidate fit noul."""

    winner: str
    fits: Mapping[str, float]
    receipt: TypeSafeReceipt

    @property
    def best_fit(self) -> float:
        return max(self.fits.values()) if self.fits else 0.0

    @property
    def accepted(self) -> bool:
        """#8201 — reject the whole shortlist when even the best fit is weak."""
        return self.best_fit >= FITS_THRESHOLD


@dataclass(frozen=True)
class SkillSuggestion:
    """At most one skill name, plus both calls' receipts for logging."""

    names: tuple[str, ...]
    rank: RankResult
    verify: VerifyResult | None


def _split_frontmatter(text: str, path: Path) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        raise ValueError(f"{path}: missing opening frontmatter delimiter")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError(f"{path}: missing closing frontmatter delimiter")
    data = yaml.safe_load(text[4:end])
    if not isinstance(data, dict):
        raise ValueError(f"{path}: frontmatter must be a mapping")
    return data, text[end + len("\n---\n") :]


def load_skill_index(repo_root: Path = REPO_ROOT) -> list[SkillRecord]:
    """#8201 — name + description (+ body excerpt) from every vendored SKILL.md."""
    records = []
    for path in sorted(repo_root.glob(SKILL_GLOB)):
        data, body = _split_frontmatter(path.read_text(encoding="utf-8"), path)
        records.append(
            SkillRecord(
                name=str(data["name"]).strip(),
                description=str(data["description"]).strip(),
                body_excerpt=body.strip()[:EXCERPT_CHARS],
                path=str(path.relative_to(repo_root)),
            )
        )
    return records


def load_typesafe_api_key() -> str:
    """Load API key from env or host secrets dir. Never logs the value."""
    env = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if env:
        return env
    home = Path.home() / ".secrets"
    for name in ("typesafe-ai.key", "typsafe-ai.key"):
        path = home / name
        if path.is_file():
            return path.read_text(encoding="utf-8").strip().replace("\r", "")
    raise FileNotFoundError(
        "TYPESAFE_API_KEY unset and neither ~/.secrets/typesafe-ai.key nor legacy ~/.secrets/typsafe-ai.key found"
    )


def make_client(api_key: str | None = None) -> Any:
    """Construct a sync TypeSafeClient (lazy import)."""
    from typesafe_sdk import TypeSafeClient

    key = api_key if api_key is not None else load_typesafe_api_key()
    os.environ.setdefault("TYPESAFE_API_KEY", key)
    return TypeSafeClient()


def _receipt_from_response(response: Any) -> TypeSafeReceipt:
    usage = getattr(response, "usage", None)
    return TypeSafeReceipt(
        model=getattr(response, "model", None),
        input_tokens=getattr(usage, "input_tokens", None) if usage else None,
        output_tokens=getattr(usage, "output_tokens", None) if usage else None,
        request_id=getattr(response, "request_id", None),
    )


def rank_skills(
    turn: str,
    skills: Sequence[SkillRecord],
    *,
    client: _SystemOneClient | None = None,
    model: str | None = None,
) -> RankResult:
    """Call 1 — one batched request: Choice over the whole roster + gate nouls."""
    if not skills:
        raise ValueError("skill index is empty")
    Choice, Noul = _question_primitives()

    state = {"turn": turn}
    questions: dict[str, Any] = {
        "which": Choice(
            instructions=CHOICE_INSTRUCTIONS,
            criteria={skill.name: skill.description for skill in skills},
        )
    }
    for key, text in GATE_QUESTIONS.items():
        questions[f"gate::{key}"] = Noul(instructions=text)

    own_client = client is None
    c = client if client is not None else make_client()
    try:
        response = c.system_one(state=state, questions=questions, model=model)
    finally:
        if own_client and hasattr(c, "close"):
            c.close()

    ranked = tuple(
        sorted(
            ((str(name), float(prob)) for name, prob in dict(response.choices["which"].probabilities).items()),
            key=lambda pair: -pair[1],
        )
    )
    gate_values = {
        key.removeprefix("gate::"): float(response.nouls[key].noul) for key in questions if key.startswith("gate::")
    }
    oriented = [(1.0 - v) if k in INVERTED_GATE_QUESTIONS else v for k, v in gate_values.items()]
    gate_score = sum(oriented) / len(oriented)

    return RankResult(
        ranked=ranked,
        gate_score=gate_score,
        gate_values=gate_values,
        receipt=_receipt_from_response(response),
    )


def _rerank_criteria(shortlist: Sequence[SkillRecord]) -> dict[str, str]:
    return {skill.name: f"{skill.description} — {skill.body_excerpt}" for skill in shortlist}


def verify_shortlist(
    turn: str,
    shortlist: Sequence[SkillRecord],
    *,
    client: _SystemOneClient | None = None,
    model: str | None = None,
) -> VerifyResult:
    """Call 2 — deep-read the top-3 shortlist; ``accepted`` may reject all of them."""
    if not shortlist:
        raise ValueError("shortlist is empty")
    Choice, Noul = _question_primitives()

    state = {"turn": turn}
    questions: dict[str, Any] = {
        "which": Choice(instructions=RERANK_INSTRUCTIONS, criteria=_rerank_criteria(shortlist)),
    }
    for skill in shortlist:
        questions[f"fits::{skill.name}"] = Noul(
            instructions=(
                f"Does the skill '{skill.name}' do the specific thing the user's current "
                f"turn asks for? It is described as: {skill.description}"
            )
        )

    own_client = client is None
    c = client if client is not None else make_client()
    try:
        response = c.system_one(state=state, questions=questions, model=model)
    finally:
        if own_client and hasattr(c, "close"):
            c.close()

    fits = {
        key.removeprefix("fits::"): float(response.nouls[key].noul) for key in questions if key.startswith("fits::")
    }
    return VerifyResult(
        winner=str(response.choices["which"].choice),
        fits=fits,
        receipt=_receipt_from_response(response),
    )


def suggest_skill(
    turn: str,
    *,
    skills: Sequence[SkillRecord] | None = None,
    client: _SystemOneClient | None = None,
    model: str | None = None,
) -> SkillSuggestion:
    """#8201 — full two-call pipeline. Returns 0 or 1 skill names."""
    roster = list(skills) if skills is not None else load_skill_index()
    rank = rank_skills(turn, roster, client=client, model=model)
    if not rank.needs_skill:
        return SkillSuggestion(names=(), rank=rank, verify=None)

    by_name = {skill.name: skill for skill in roster}
    shortlist = [by_name[name] for name, _probability in rank.ranked[:SHORTLIST] if name in by_name]
    if not shortlist:
        return SkillSuggestion(names=(), rank=rank, verify=None)

    verify = verify_shortlist(turn, shortlist, client=client, model=model)
    if not verify.accepted:
        return SkillSuggestion(names=(), rank=rank, verify=verify)

    return SkillSuggestion(names=(verify.winner,), rank=rank, verify=verify)


def suggestion_block(names: tuple[str, ...]) -> str:
    """Advisory system-prompt line. The agent keeps its full roster and judgment."""
    body = (
        f"Relevant to the current request: {', '.join(names)}. Ignore this if it does not "
        "fit what the user actually asked for."
        if names
        else "No skill in the roster appears relevant to this request."
    )
    return f"<skill_relevance>\n{body}\n</skill_relevance>"


def _suggestion_to_dict(suggestion: SkillSuggestion) -> dict[str, Any]:
    return {
        "names": list(suggestion.names),
        "block": suggestion_block(suggestion.names),
        "rank": {
            "needs_skill": suggestion.rank.needs_skill,
            "gate_score": suggestion.rank.gate_score,
            "gate_values": dict(suggestion.rank.gate_values),
            "top": [list(pair) for pair in suggestion.rank.ranked[:SHORTLIST]],
            "receipt": suggestion.rank.receipt.to_dict(),
        },
        "verify": (
            None
            if suggestion.verify is None
            else {
                "winner": suggestion.verify.winner,
                "fits": dict(suggestion.verify.fits),
                "accepted": suggestion.verify.accepted,
                "receipt": suggestion.verify.receipt.to_dict(),
            }
        ),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--turn", required=True, help="the user's current turn / request text")
    parser.add_argument("--model", default=None, help="override the TypeSafe model (default jev-latest)")
    args = parser.parse_args(list(argv) if argv is not None else None)

    suggestion = suggest_skill(args.turn, model=args.model)
    print(json.dumps(_suggestion_to_dict(suggestion), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
