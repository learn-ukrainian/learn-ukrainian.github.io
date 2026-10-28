"""Blind lesson-section A/B scorer: manifest, mechanical checks, judging in both orders, report and unblinding."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, ClassVar

import pytest

import scripts.eval.lesson_ab.__main__ as cli
from scripts.eval.lesson_ab.core import (
    load_key,
    load_manifest,
    mark_attested,
    marked_words,
    split_capitalised,
    stress_metrics,
    strip_stress,
)
from scripts.eval.lesson_ab.judge import JUDGE_CRITERIA, plan_judge_tasks, resolve_judges, validate_verdict
from scripts.eval.lesson_ab.report import build_report, cohen_kappa, sign_test
from scripts.eval.uk_preamble.common import SEATS, HarnessError, sha256_text
from scripts.eval.uk_preamble.dispatch import TaskOutcome, composition_of, seat_mode
from scripts.eval.uk_preamble.runner import Executor

GEMINI, OPUS = "gemini-3.8-flash-high", "claude-opus-5-5"
GOOD = "Добрий день! Я живу́ в Ки́єві."
WEAK = "Добрий день! Я живе́те в Києві."
TASKS = ("t1", "t2", "t3")
# Blind assignment: the better text (GOOD) is A in t1 and t3, B in t2.
GOOD_SIDE = {"t1": "A", "t2": "B", "t3": "A"}
KEY = {
    "writers": {"alpha": "openai", "beta": "openai"},
    "tasks": {"t1": {"A": "alpha", "B": "beta"}, "t2": {"A": "beta", "B": "alpha"}, "t3": {"A": "alpha", "B": "beta"}},
}


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def build_packet(root: Path, **overrides: Any) -> Path:
    tasks = []
    for task_id in TASKS:
        plan = _write(root / "plans" / f"{task_id}.yaml", f"level: A1\ntitle: {task_id}\ncontent_outline: []\n")
        prompt = _write(root / "prompts" / f"{task_id}.md", f"Write the first section of {plan.name}.\n")
        good, weak = (GOOD, WEAK) if GOOD_SIDE[task_id] == "A" else (WEAK, GOOD)
        tasks.append(
            {
                "task_id": task_id,
                "plan_path": f"plans/{task_id}.yaml",
                "prompt_path": f"prompts/{task_id}.md",
                "prompt_sha256": sha256_text(prompt.read_text(encoding="utf-8")),
                "output_a": str(_write(root / "blind" / f"{task_id}-A.md", f"## {task_id}\n\n{good}\n")),
                "output_b": str(_write(root / "blind" / f"{task_id}-B.md", f"## {task_id}\n\n{weak}\n")),
            }
        )
    key = _write(root / "key.json", json.dumps(KEY))
    manifest = {
        "evaluation_id": "fixture",
        "writer_families": ["openai"],
        "key_sha256": sha256_text(key.read_text(encoding="utf-8")),
        "provenance": "fixture outputs",
        "tasks": tasks,
        **overrides,
    }
    return _write(root / "manifest.json", json.dumps(manifest))


class FakeSources:
    def writing_metrics(self, text: str, level: str) -> dict[str, Any]:
        invalid = ["Можна", "живе"] if "живе" in text else []
        return {"words": len(text.split()), "vesum_invalid": len(invalid), "vesum_invalid_forms": invalid}


class FakeChecks:
    """Stress readings for the fixture words; VESUM attests ``можна`` only."""

    READINGS: ClassVar[dict[str, list[int]]] = {"живу": [3], "києві": [1], "живете": [5], "важливіша": [4, 6]}

    def ambiguous(self, plain_text: str, marked: list[str]) -> list[str]:
        return []

    def verify(self, word: str) -> dict[str, Any]:
        positions = self.READINGS.get(strip_stress(word).lower())
        return {"matches": [] if positions is None else [{"stressed_form": word, "vowel_indices": positions}]}

    def attested(self, forms: list[str]) -> set[str]:
        return {form for form in forms if form == "можна"}


class FakeJudges:
    """Gemini prefers the GOOD text; Opus always prefers Text 1 (position-biased) and abstains on t3."""

    def __init__(self, cwd: Path) -> None:
        self.cwd = cwd
        self.records: dict[str, TaskOutcome] = {}
        self.dispatched: list[str] = []
        self.garbage: set[str] = set()

    def compose(self, prompt: str) -> dict[str, Any]:
        return composition_of(prompt, prompt, cwd=str(self.cwd), worktree_path=str(self.cwd), blocks=[])

    def known(self, task_id: str) -> bool:
        return task_id in self.records

    def expected_args_sha256(self, task_id, seat, kind, prompt_path: Path) -> str:
        return sha256_text(f"{task_id}|{seat.seat_id}|{kind}")

    def preflight(self, task_id, seat, kind, prompt_path) -> None:
        pass

    def _answer(self, seat_id: str, prompt: str) -> str:
        comparison = re.search(r"Comparison id: (\S+)", prompt).group(1)
        text_1 = re.search(r"<text_1>\n(.*?)\n</text_1>", prompt, re.DOTALL).group(1)
        good_first = GOOD in text_1
        position_biased = "abstain" if comparison == "t3" else "1"
        preferred = ("1" if good_first else "2") if seat_id == GEMINI else position_biased
        verdict = {
            "criteria": dict.fromkeys(
                ("naturalness", "correctness", "task_fit", "level_fit", "pedagogy", "plan_fidelity"), 4
            ),
            "errors": [],
        }
        weak = {
            **verdict,
            "score": 5,
            "errors": [{"quote": "живе́те", "correction": "живу́", "kind": "language", "severity": "P1"}],
        }
        good = {**verdict, "score": 9}
        return json.dumps(
            {
                "id": comparison,
                "text_1": good if good_first else weak,
                "text_2": weak if good_first else good,
                "preferred": preferred,
                "rationale": "Одна помилка в тексті.",
                "sources_checked": False,
            },
            ensure_ascii=False,
        )

    def dispatch(self, task_id, seat, kind, prompt_path: Path, *, force_new: bool) -> str:
        self.dispatched.append(task_id)
        prompt = prompt_path.read_text(encoding="utf-8")
        response = "no json here" if task_id in self.garbage else self._answer(seat.seat_id, prompt)
        self.records[task_id] = TaskOutcome(
            task_id=task_id,
            status="done",
            agent=seat.agent,
            model=seat.model,
            substitution=None,
            response_text=response,
            result_sha256=sha256_text(response),
            run_nonce=f"nonce-{task_id}",
            prompt_sha256=sha256_text(prompt),
            conditions={
                "effective_prompt_sha256": sha256_text(prompt),
                "prompt_blocks": [],
                "dispatch_args_sha256": self.expected_args_sha256(task_id, seat, kind, prompt_path),
                "cwd": str(self.cwd),
                "worktree_path": str(self.cwd),
                "mode": seat_mode(seat),
                "research": None,
            },
        )
        return f"nonce-{task_id}"

    def wait(self, task_id: str, run_nonce: str | None) -> TaskOutcome:
        return self.records[task_id]


@pytest.fixture
def env(tmp_path: Path, outside_dir: Path, monkeypatch: pytest.MonkeyPatch):
    manifest = build_packet(tmp_path / "packet")
    judges = FakeJudges(tmp_path)
    monkeypatch.setattr(cli, "make_sources", FakeSources)
    monkeypatch.setattr(cli, "LocalChecks", FakeChecks)
    monkeypatch.setattr(cli, "rules_block", lambda: "[rules core]")
    monkeypatch.setattr(
        cli,
        "make_executor",
        lambda args, results, cwd: Executor(
            judges, results, worker_cwd=cwd, workspace=lambda: {"head": "x"}, max_parallel=1, spawn_interval=0
        ),
    )
    return manifest, outside_dir / "results", judges, tmp_path


def _run(manifest: Path, results: Path, *extra: str) -> int:
    return cli.main(["--manifest", str(manifest), "--results", str(results), *extra])


# --------------------------------------------------------------------------- manifest and key


def test_manifest_verifies_the_prompt_digest_and_derives_the_level(tmp_path: Path) -> None:
    path = build_packet(tmp_path)
    manifest = load_manifest(path)
    assert [t.level for t in manifest.tasks] == ["A1"] * 3
    data = json.loads(path.read_text())
    data["tasks"][0]["prompt_sha256"] = "0" * 64
    path.write_text(json.dumps(data))
    with pytest.raises(HarnessError, match="does not match prompt_sha256"):
        load_manifest(path)


def test_manifest_requires_writer_families(tmp_path: Path) -> None:
    with pytest.raises(HarnessError, match="writer_families"):
        load_manifest(build_packet(tmp_path, writer_families=[]))


def test_key_must_match_the_commitment_and_cover_every_task(tmp_path: Path) -> None:
    manifest = load_manifest(build_packet(tmp_path))
    assert load_key(tmp_path / "key.json", manifest)["commitment"] == "verified"
    _write(tmp_path / "other.json", json.dumps({**KEY, "tasks": {"t1": KEY["tasks"]["t1"]}}))
    with pytest.raises(HarnessError, match="key_sha256 commitment"):
        load_key(tmp_path / "other.json", manifest)


@pytest.mark.parametrize(
    ("writers", "message"),
    [
        ({"alpha": "google", "beta": "openai"}, "not in the manifest's writer_families"),
        ({"tie": "openai", "beta": "openai"}, None),
    ],
)
def test_key_families_must_be_declared_and_any_writer_name_is_safe(
    tmp_path: Path, writers: dict[str, str], message: str | None
) -> None:
    names = list(writers)
    key = {"writers": writers, "tasks": {t: {"A": names[0], "B": names[1]} for t in TASKS}}
    manifest = load_manifest(build_packet(tmp_path, key_sha256=None))
    path = _write(tmp_path / "custom-key.json", json.dumps(key))
    if message:
        with pytest.raises(HarnessError, match=message):
            load_key(path, manifest)
        return
    # Writers named like status values: an abstention and a failure stay what they are.
    judgements = [
        {"judge": GEMINI, "judge_family": "google", "task_id": "t1", "order": "AB", "failed": False,
         "preferred": "abstain", "preferred_position": "abstain", "texts": {s: {"score": None, "criteria": dict.fromkeys(JUDGE_CRITERIA), "errors": []} for s in "AB"}},
        {"judge": GEMINI, "judge_family": "google", "task_id": "t1", "order": "BA", "failed": True, "preferred": None, "texts": None},
    ]  # fmt: skip
    report = build_report(manifest, [], judgements, judges=[GEMINI], key=load_key(path, manifest), iterations=10)
    t1 = report["tasks"][0]
    assert t1["outcome"] == {"result": "no verdict", "winner": None}
    assert t1["votes"] == {"writers": {"beta": 0, "tie": 0}, "tie": 0, "abstain": 1, "failed": 1}
    assert report["totals"]["wins"] == report["totals"]["ties"] == 0


# --------------------------------------------------------------------------- mechanical checks


def test_stress_marks_are_stripped_and_classified() -> None:
    assert strip_stress("Ки́єві й ї") == "Києві й ї"
    assert marked_words("Я живу́ в Ки́єві, пам'ять") == ["живу́", "Ки́єві"]
    # NFC would fold these marks into one letter (ѐ, ѝ, ѓ); each stays a combining mark.
    assert marked_words("сѐла сѝла ѓрати") == ["се\u0300ла", "си\u0300ла", "г\u0301рати"]
    assert marked_words("café, Ки́єві") == ["Ки́єві"]
    metrics = stress_metrics("Ви живе́те. Ро́стик.", "Ви живете. Ростик.", FakeChecks())
    assert metrics["stress_wrong"] == 1 and metrics["stress_wrong_forms"][0]["form"] == "живе́те"
    assert metrics["stress_unverified"] == 1 and metrics["stress_attested"] == 0


def test_a_single_mark_on_a_variant_stress_reading_is_attested() -> None:
    reading = [{"vowel_indices": [4, 6]}]
    assert mark_attested("важливі́ша", reading)
    assert not mark_attested("ва́жливіша", reading)


def test_capitalised_forms_known_in_lowercase_are_not_vesum_invalid() -> None:
    metrics = {"vesum_invalid": 2, "vesum_invalid_forms": ["Можна", "живе"]}
    split_capitalised(metrics, FakeChecks())
    assert metrics["vesum_invalid_forms"] == ["живе"] and metrics["vesum_capitalised_forms"] == ["Можна"]


# --------------------------------------------------------------------------- judging


def test_judges_in_a_writer_family_are_refused() -> None:
    with pytest.raises(HarnessError, match="outside them"):
        resolve_judges(["gpt-6.1-sol"], ["openai"])


def test_every_judge_sees_every_task_in_both_orders(tmp_path: Path) -> None:
    manifest = load_manifest(build_packet(tmp_path))
    tasks = plan_judge_tasks(manifest, resolve_judges([GEMINI, OPUS], ["openai"]), "tag", "[rules]")
    assert len(tasks) == 2 * 3 * 2
    for spec in tasks:
        task = next(t for t in manifest.tasks if t.task_id == spec.meta["lesson_task"])
        first = task.texts[spec.meta["text_1"]].strip()
        assert spec.prompt.index(first) < spec.prompt.index(task.texts[spec.meta["text_2"]].strip())
        assert "-A.md" not in spec.prompt and "output_a" not in spec.prompt
    assert {(s.seat.seat_id, s.meta["lesson_task"], s.meta["order"]) for s in tasks} == {
        (j, t, o) for j in (GEMINI, OPUS) for t in TASKS for o in ("AB", "BA")
    }


def test_verdicts_must_match_the_schema_and_id() -> None:
    assert validate_verdict("{}", "t1")[1].startswith("schema violation")
    assert validate_verdict(None, "t1") == (None, "no response")
    text = {"criteria": dict.fromkeys(JUDGE_CRITERIA), "score": None, "errors": []}
    answer = {"id": "t1", "text_1": text, "text_2": text, "rationale": "", "sources_checked": False}
    # A preference needs both SCOREs; only an abstention may leave them null.
    assert "without a SCORE" in validate_verdict(json.dumps({**answer, "preferred": "1"}), "t1")[1]
    assert validate_verdict(json.dumps({**answer, "preferred": "abstain"}), "t1")[1] is None


# --------------------------------------------------------------------------- end to end


def test_mechanical_only_run_writes_a_blind_report(env) -> None:
    manifest, results, judges, _ = env
    assert _run(manifest, results) == 0
    report = json.loads((results / "report-blind.json").read_text())
    assert report["label"] == "exploratory: 3 tasks" and report["blinded"]
    assert report["provenance"]["outputs"].startswith("imported")
    assert report["metrics"]["vesum_invalid"]["tasks"] == 3 and not judges.dispatched


def test_judged_run_keeps_failures_and_abstentions_then_unblinds(env, tmp_path: Path) -> None:
    manifest, results, judges, packet = env
    assert _run(manifest, results, "--judge", GEMINI, "--judge", OPUS) == 0
    assert len(judges.dispatched) == 12
    blind = json.loads((results / "report-blind.json").read_text())
    t1 = next(t for t in blind["tasks"] if t["task_id"] == "t1")
    # Gemini prefers A (GOOD) in both orders; Opus prefers Text 1, so A once and B once.
    assert t1["votes"] == {"writers": {"A": 3, "B": 1}, "tie": 0, "abstain": 0, "failed": 0}
    assert t1["outcome"] == {"result": "win", "winner": "A"}
    t3 = next(t for t in blind["tasks"] if t["task_id"] == "t3")
    assert t3["votes"]["abstain"] == 2
    opus = blind["judges"]["per_judge"][OPUS]
    assert opus["abstained"] == 2 and opus["position_inconsistent"] == 2 and opus["first_position_preferred"] == 1.0
    assert blind["judges"]["per_judge"][GEMINI]["position_consistency"] == 1.0

    # Stored judgements are reused: nothing is dispatched again; unblinding orients by writer.
    ratings = packet / "human"
    for task_id in TASKS:
        for side, score in (("A", 9), ("B", 5)) if GOOD_SIDE[task_id] == "A" else (("A", 5), ("B", 9)):
            _write(
                ratings / f"r-{task_id}-{side}.yaml",
                f"reviewer: native\nmodule: {{level: ab, slug: {task_id}-{side}}}\nscores: {{linguistic_accuracy: {score}}}\n",
            )
    code = _run(
        manifest, results, "--judge", GEMINI, "--judge", OPUS, "--no-dispatch",
        "--key", str(packet / "packet" / "key.json"), "--human-ratings", str(ratings),
    )  # fmt: skip
    assert code == 0 and len(judges.dispatched) == 12
    unblinded = json.loads((results / "report-unblinded.json").read_text())
    assert unblinded["labels"] == ["alpha", "beta"] and not unblinded["families"]["violations"]
    # alpha wrote the better text in every task (A in t1 and t3, B in t2).
    assert unblinded["metrics"]["judge_score"]["difference"] == pytest.approx(4.0)
    assert unblinded["totals"] == {"wins": 3, "ties": 0, "losses": 0, "no_verdict": 0, "sign_test_p": 0.25}
    assert unblinded["human"]["texts_rated"] == 6 and unblinded["human"]["pearson_with_judge_score"] == pytest.approx(
        1.0
    )


def test_unparseable_judgements_are_failed_records_and_exit_one(env) -> None:
    manifest, results, judges, _ = env
    tasks = plan_judge_tasks(load_manifest(manifest), [SEATS[GEMINI]], manifest_tag(manifest), "[rules core]")
    judges.garbage = {tasks[0].task_id}
    assert _run(manifest, results, "--judge", GEMINI) == 1
    report = json.loads((results / "report-blind.json").read_text())
    assert report["judges"]["per_judge"][GEMINI]["failed"] == 1
    assert sum(t["votes"]["failed"] for t in report["tasks"]) == 1


def manifest_tag(path: Path) -> str:
    return load_manifest(path).sha256[:10]


def test_changed_outputs_are_refused_after_freezing(env) -> None:
    manifest, results, _, packet = env
    assert _run(manifest, results) == 0
    _write(packet / "packet" / "blind" / "t1-A.md", "changed")
    assert _run(manifest, results) == 2


# --------------------------------------------------------------------------- statistics


def test_sign_test_and_kappa() -> None:
    assert sign_test(0, 0) is None
    assert sign_test(5, 0) == pytest.approx(2 / 32)
    assert sign_test(3, 3) == 1.0
    assert cohen_kappa(["A", "B", "A"], ["A", "B", "A"]) == 1.0
    assert cohen_kappa(["A", "A"], ["A", "A"]) is None
