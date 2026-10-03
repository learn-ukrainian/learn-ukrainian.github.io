"""Runner resume, attribution, judging and report-rule tests with a fake dispatcher (#9623)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

import scripts.eval.uk_preamble.__main__ as cli
from scripts.eval.uk_preamble.common import SEATS, judge_seats, read_json, sha256_text
from scripts.eval.uk_preamble.dataset import load_set
from scripts.eval.uk_preamble.dispatch import DispatchError, TaskOutcome
from scripts.eval.uk_preamble.report import build_report, render_markdown
from scripts.eval.uk_preamble.runner import Executor, candidate_slots, plan_judge_tasks, resolve_seats
from scripts.eval.uk_preamble.scoring import score_judgements

PREAMBLE = "Ти — досвідчений редактор української мови."
_INPUT = re.compile(r"Input:\n```json\n(.*)\n```\n\Z", re.DOTALL)


def _inputs(prompt: str) -> list[dict[str, Any]]:
    return json.loads(_INPUT.search(prompt).group(1))["items"]


class FakeDispatcher:
    """Answers instantly: the preamble variant corrects every seeded error, the baseline none."""

    def __init__(self, mini_set: dict[str, Any]) -> None:
        self.accepted = {item["id"]: item for item in mini_set["review"]}
        self.dispatched: list[tuple[str, bool]] = []
        self.waited: list[str] = []
        self.preflighted: list[str] = []
        self.records: dict[str, TaskOutcome] = {}
        self.status_for: dict[str, str] = {}
        self.model_for: dict[str, str] = {}
        self.garbage_for: set[str] = set()
        self.refuse: set[str] = set()
        self.foreign_prompt: set[str] = set()

    def _review(self, prompt: str) -> dict[str, Any]:
        items = []
        for entry in _inputs(prompt):
            corrections = []
            if prompt.startswith(PREAMBLE):
                for err in self.accepted[entry["id"]]["errors"]:
                    corrections.append(
                        {
                            "span": err["span"],
                            "start": err["start"],
                            "end": err["end"],
                            "correction": err["accepted"][0],
                            "error_type": err["error_type"],
                            "evidence": "rule",
                        }
                    )
            text = entry["text"]
            for c in sorted(corrections, key=lambda c: c["start"], reverse=True):
                text = text[: c["start"]] + c["correction"] + text[c["end"] :]
            items.append(
                {"id": entry["id"], "corrected_text": text, "corrections": corrections, "style_suggestions": []}
            )
        return {"items": items}

    def _respond(self, kind: str, prompt: str) -> str:
        if kind == "review":
            return json.dumps(self._review(prompt), ensure_ascii=False)
        if kind == "writing":
            return json.dumps(
                {"items": [{"id": e["id"], "text": "Сьогодні я відпочиваю вдома з родиною."} for e in _inputs(prompt)]}
            )
        verdicts = [
            {
                "id": e["id"],
                "winner": "A",
                "rationale": "A краще.",
                "scores": {
                    side: dict.fromkeys(("naturalness", "correctness", "task_fit", "level_fit"), 4) for side in "AB"
                },
            }
            for e in _inputs(prompt)
        ]
        return json.dumps({"items": verdicts}, ensure_ascii=False)

    def known(self, task_id: str) -> bool:
        return task_id in self.records

    def dispatch(self, task_id, seat, kind, prompt_path: Path, *, force_new: bool) -> str:
        if task_id in self.refuse:
            raise DispatchError("host admission refused")
        self.dispatched.append((task_id, force_new))
        prompt = prompt_path.read_text(encoding="utf-8")
        response = "I could not do it." if task_id in self.garbage_for else self._respond(kind, prompt)
        self.records[task_id] = TaskOutcome(
            task_id=task_id,
            status=self.status_for.get(task_id, "done"),
            agent=seat.agent,
            model=self.model_for.get(task_id, seat.model),
            substitution=None,
            response_text=response,
            result_sha256=sha256_text(response),
            run_nonce=f"nonce-{task_id}",
            prompt_sha256=sha256_text("another prompt" if task_id in self.foreign_prompt else prompt),
        )
        return f"nonce-{task_id}"

    def preflight(self, task_id, seat, kind, prompt_path) -> None:
        self.preflighted.append(task_id)

    def wait(self, task_id: str, run_nonce: str | None) -> TaskOutcome:
        self.waited.append(task_id)
        return self.records[task_id]


class FakeSources:
    def invalid_forms(self, text: str) -> set[str]:
        return set()

    def writing_metrics(self, text: str, level: str) -> dict[str, Any]:
        return {
            "tokens": 6,
            "words": 6,
            "calque_hits": 0,
            "calque_density": 0.0,
            "vesum_invalid": 0,
            "level_adherence": 1.0,
            "english_intrusion": 0.0,
        }


@pytest.fixture
def env(tmp_path: Path, mini_set_dict: dict[str, Any], monkeypatch: pytest.MonkeyPatch):
    set_path = tmp_path / "set.json"
    set_path.write_text(json.dumps(mini_set_dict, ensure_ascii=False), encoding="utf-8")
    preamble = tmp_path / "adapted.md"
    preamble.write_text(PREAMBLE + "\n", encoding="utf-8")
    fake = FakeDispatcher(mini_set_dict)
    monkeypatch.setattr(cli, "make_dispatcher", lambda args: fake)
    monkeypatch.setattr(cli, "make_sources", FakeSources)
    results = tmp_path / "results"
    run_args = [
        "run",
        "--set",
        str(set_path),
        "--results",
        str(results),
        "--variant",
        "none",
        "--variant",
        f"adapted-v2={preamble}",
        "--repeats",
        "2",
        "--allow-undersized-set",
        "--spawn-interval",
        "0",
        "--max-parallel",
        "2",
    ]
    return {"fake": fake, "results": results, "run": run_args, "set": set_path, "preamble": preamble}


def _task_ids(results: Path) -> list[str]:
    return sorted(p.stem for p in (results / "raw").glob("*.json") if not p.name.endswith(".pending.json"))


# 3 seats x 2 variants x 2 repeats x (1 review chunk + 1 writing chunk)
PLANNED = 24


def test_run_dispatches_every_cell_and_resume_skips_accepted(env):
    assert cli.main(env["run"]) == 0
    assert len(env["fake"].dispatched) == PLANNED
    assert len(_task_ids(env["results"])) == PLANNED
    raw = read_json(env["results"] / "raw" / f"{_task_ids(env['results'])[0]}.json")
    assert raw["accepted"] is True and raw["model"] in {seat.model for seat in SEATS.values()}
    assert cli.main(env["run"]) == 0
    assert len(env["fake"].dispatched) == PLANNED  # nothing re-dispatched


def test_resume_waits_on_dispatched_task_instead_of_redispatching(env):
    assert cli.main(env["run"]) == 0
    raw_dir = env["results"] / "raw"
    pending_id, orphan_id = _task_ids(env["results"])[:2]
    (raw_dir / f"{pending_id}.json").unlink()
    prompt_sha = sha256_text((env["results"] / "prompts" / f"{pending_id}.md").read_text(encoding="utf-8"))
    (raw_dir / f"{pending_id}.pending.json").write_text(json.dumps({"run_nonce": "n", "prompt_sha256": prompt_sha}))
    (raw_dir / f"{orphan_id}.json").unlink()  # dispatched, crashed before the pending marker
    env["fake"].waited.clear()
    assert cli.main(env["run"]) == 0
    assert len(env["fake"].dispatched) == PLANNED
    assert sorted(env["fake"].waited) == sorted([pending_id, orphan_id])
    assert not (raw_dir / f"{pending_id}.pending.json").exists()


def test_failed_task_kept_and_redispatched_only_with_retry(env, capsys):
    slots = candidate_slots(
        load_set(env["set"]),
        resolve_seats(None),
        ["none", "adapted-v2"],
        2,
        ["review", "writing"],
        8,
        load_set(env["set"]).sha256[:10],
    )
    victim = slots[0].task_id
    env["fake"].status_for[victim] = "timeout"
    assert cli.main(env["run"]) == 1
    assert victim in json.loads(capsys.readouterr().out)["failed"]
    assert cli.main(env["run"]) == 1
    assert len(env["fake"].dispatched) == PLANNED
    env["fake"].status_for.clear()
    assert cli.main([*env["run"], "--retry-failed"]) == 0
    assert env["fake"].dispatched[-1] == (victim, True)
    assert len(env["fake"].dispatched) == PLANNED + 1


def test_unattributable_answer_is_not_accepted_and_scores_as_failed(env):
    set_obj = load_set(env["set"])
    slots = candidate_slots(set_obj, resolve_seats(None), ["none", "adapted-v2"], 2, ["review"], 8, set_obj.sha256[:10])
    flash = next(s for s in slots if s.seat.code == "flash")
    env["fake"].model_for[flash.task_id] = "gemini-3.1-pro-preview"
    assert cli.main(env["run"]) == 1
    raw = read_json(env["results"] / "raw" / f"{flash.task_id}.json")
    assert raw["accepted"] is False and "gemini-3.1-pro-preview" in raw["identity_problem"]
    assert cli.main(["score", "--results", str(env["results"]), "--repeats", "2"]) == 0
    scores = read_json(env["results"] / "scores.json")
    failed = [r for r in scores["review"] if r["task_id"] == flash.task_id]
    assert len(failed) == 4 and all(r["failed"] for r in failed)
    assert all("gemini-3.1-pro-preview" in r["reason"] for r in failed)


def test_answer_to_a_different_prompt_is_not_accepted(env):
    set_obj = load_set(env["set"])
    victim = candidate_slots(set_obj, resolve_seats(None), ["none"], 1, ["review"], 8, set_obj.sha256[:10])[0].task_id
    env["fake"].foreign_prompt.add(victim)
    assert cli.main(env["run"]) == 1
    raw = read_json(env["results"] / "raw" / f"{victim}.json")
    assert raw["accepted"] is False and "not the planned" in raw["identity_problem"]


def test_dispatch_refusal_leaves_no_record_and_rerun_dispatches(env):
    set_obj = load_set(env["set"])
    victim = candidate_slots(
        set_obj, resolve_seats(None), ["none", "adapted-v2"], 2, ["review", "writing"], 8, set_obj.sha256[:10]
    )[3].task_id
    env["fake"].refuse.add(victim)
    assert cli.main(env["run"]) == 1
    assert victim not in _task_ids(env["results"])
    env["fake"].refuse.clear()
    assert cli.main(env["run"]) == 0
    assert env["fake"].dispatched[-1] == (victim, False)


def test_changed_preamble_refuses_to_resume(env, capsys):
    assert cli.main(env["run"]) == 0
    env["preamble"].write_text(PREAMBLE + " Змінено.\n", encoding="utf-8")
    assert cli.main(env["run"]) == 2
    assert "variants" in capsys.readouterr().err


def test_undersized_set_refused_without_flag(env, capsys):
    args = [a for a in env["run"] if a != "--allow-undersized-set"]
    assert cli.main(args) == 2
    assert "Protocol v2 minimums" in capsys.readouterr().err


def test_dry_run_preflights_every_task_without_dispatch(env):
    assert cli.main([*env["run"], "--dry-run"]) == 0
    assert len(env["fake"].preflighted) == PLANNED and env["fake"].dispatched == []
    assert all(task_id.endswith("-preflight") for task_id in env["fake"].preflighted)
    assert cli.main(env["run"]) == 0  # a later real run dispatches every task
    assert len(env["fake"].dispatched) == PLANNED


def test_malformed_output_counted_as_failed_items(env):
    set_obj = load_set(env["set"])
    victim = candidate_slots(
        set_obj, resolve_seats(None), ["none", "adapted-v2"], 2, ["review"], 8, set_obj.sha256[:10]
    )[0].task_id
    env["fake"].garbage_for.add(victim)
    assert cli.main(env["run"]) == 0  # the task ran and is attributable; its items fail at scoring
    assert cli.main(["score", "--results", str(env["results"]), "--repeats", "2"]) == 0
    scores = read_json(env["results"] / "scores.json")
    rows = [r for r in scores["review"] if r["task_id"] == victim]
    assert len(rows) == 4 and all(r["failed"] and "unparseable" in r["reason"] for r in rows)
    assert len(scores["review"]) == 3 * 2 * 2 * 4  # every planned item is present


def test_score_judge_and_report_end_to_end(env, capsys):
    assert cli.main(env["run"]) == 0
    assert (
        cli.main(["score", "--results", str(env["results"]), "--repeats", "2", "--judge", "--spawn-interval", "0"]) == 0
    )
    scores = read_json(env["results"] / "scores.json")
    # 3 candidate seats x 2 judges x 1 pair x 2 repeats x 2 writing tasks
    assert len(scores["judge"]) == 24 and not any(r["failed"] for r in scores["judge"])
    for record in scores["judge"]:
        assert SEATS[record["judge_seat"]].family != SEATS[record["candidate_seat"]].family
    capsys.readouterr()
    assert cli.main(["report", "--results", str(env["results"]), "--bootstrap", "500"]) == 0
    markdown = capsys.readouterr().out
    report = read_json(env["results"] / "report.json")
    for seat in SEATS:
        comparison = report["seats"][seat]["comparisons"]["adapted-v2"]
        assert comparison["review"]["recall_variant"] == 100.0
        assert comparison["review"]["recall_baseline"] == 0.0
        assert comparison["rule"]["passes"] is True
        assert report["seats"][seat]["decision"] == "adapted-v2"
    assert "| lexical-russianism |" in markdown


def test_judge_order_is_randomised_blind_and_mapped_back(env):
    assert cli.main(env["run"]) == 0
    set_obj = load_set(env["set"])
    seats = resolve_seats(None)
    slots = candidate_slots(set_obj, seats, ["none", "adapted-v2"], 2, ["review", "writing"], 8, set_obj.sha256[:10])
    tasks = plan_judge_tasks(
        set_obj, env["results"], slots, seats, ["none", "adapted-v2"], 2, 8, 7, set_obj.sha256[:10]
    )
    assert len(tasks) == 3 * 2 * 2
    orders = []
    for task in tasks:
        assert task.seat in judge_seats(task.meta["candidate_seat"])
        assert "adapted-v2" not in task.prompt and PREAMBLE not in task.prompt  # blind
        orders += [entry["A"] for entry in task.meta["order"].values()]
    assert set(orders) == {"none", "adapted-v2"}  # both orders occur
    again = plan_judge_tasks(
        set_obj, env["results"], slots, seats, ["none", "adapted-v2"], 2, 8, 7, set_obj.sha256[:10]
    )
    assert [t.task_id for t in again] == [t.task_id for t in tasks]  # deterministic, resumable
    fake = env["fake"]
    for task in tasks:
        path = env["results"] / "prompts" / f"{task.task_id}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(task.prompt, encoding="utf-8")
        fake.dispatch(task.task_id, task.seat, "judge", path, force_new=False)
        Executor(fake, env["results"], spawn_interval=0)._record(task, fake.records[task.task_id])
    records = score_judgements(env["results"], [t.task_id for t in tasks])
    for record in records:
        task = next(t for t in tasks if t.task_id == record["task_id"])
        assert record["winner"] == task.meta["order"][record["item_id"]]["A"]  # the fake always picks A


# --------------------------------------------------------------------------- adoption rule


def _synthetic(recall: dict[str, list[int]], fa: dict[str, int], density: dict[str, float], writing_failed=()):
    """20 one-error, one-protected-span items; ``recall[label]`` lists hit flags per item."""
    review, writing = [], []
    for label, hits in recall.items():
        for i, hit in enumerate(hits):
            review.append(
                {
                    "seat": "s",
                    "variant": label,
                    "repeat": 1,
                    "item_id": f"R{i}",
                    "failed": False,
                    "errors": [{"id": f"e{i}", "type": "paronym", "hit": bool(hit)}],
                    "protected_count": 1,
                    "hits": hit,
                    "false_alarms": 1 if i < fa[label] else 0,
                    "fa_protected": 0,
                    "fa_other": 0,
                    "fa_unanchored": 0,
                    "wrong_corrections": 0,
                    "unlogged_changes": False,
                    "new_invalid_forms": [],
                    "style": {"total": 0, "on_protected": 0, "on_error": 0},
                }
            )
        for j in range(4):
            failed = (label, j) in writing_failed
            writing.append(
                {
                    "seat": "s",
                    "variant": label,
                    "repeat": 1,
                    "item_id": f"W{j}",
                    "failed": failed,
                    "metrics": None
                    if failed
                    else {
                        "calque_density": density[label] + j * 0.01,
                        "vesum_invalid": 0,
                        "level_adherence": 1.0,
                        "english_intrusion": 0.0,
                    },
                }
            )
    return {"review": review, "writing": writing, "judge": []}


BASE = [1] * 6 + [0] * 14
BETTER = [1] * 14 + [0] * 6


def _decide(scores) -> dict[str, Any]:
    return build_report(scores, iterations=2000, seed=1)["seats"]["s"]


def test_rule_adopts_adapted_when_recall_ci_excludes_zero():
    seat = _decide(
        _synthetic({"none": BASE, "adapted-v2": BETTER}, {"none": 2, "adapted-v2": 2}, {"none": 1.0, "adapted-v2": 1.0})
    )
    assert seat["comparisons"]["adapted-v2"]["review"]["recall_delta"][1] > 0
    assert seat["decision"] == "adapted-v2"


def test_rule_rejects_false_alarm_rise_above_two_points():
    seat = _decide(
        _synthetic({"none": BASE, "adapted-v2": BETTER}, {"none": 2, "adapted-v2": 3}, {"none": 1.0, "adapted-v2": 1.0})
    )
    assert seat["decision"] == "no change"
    assert "false alarms rise" in seat["comparisons"]["adapted-v2"]["rule"]["reasons"][0]


def test_rule_rejects_calque_density_rise_and_falls_back_to_original():
    scores = _synthetic(
        {"none": BASE, "adapted-v2": BETTER, "original": BETTER},
        {"none": 2, "adapted-v2": 2, "original": 2},
        {"none": 1.0, "adapted-v2": 1.5, "original": 0.5},
    )
    seat = _decide(scores)
    assert seat["comparisons"]["adapted-v2"]["rule"]["passes"] is False
    assert seat["decision"] == "original"
    assert "| s | original |" in render_markdown(build_report(scores, iterations=200, seed=1))


def test_rule_inconclusive_when_recall_ci_spans_zero_or_writing_failed():
    noisy = [1] * 7 + [0] * 13
    seat = _decide(
        _synthetic({"none": BASE, "adapted-v2": noisy}, {"none": 2, "adapted-v2": 2}, {"none": 1.0, "adapted-v2": 1.0})
    )
    assert seat["decision"] == "no change"
    failed = _synthetic(
        {"none": BASE, "adapted-v2": BETTER},
        {"none": 2, "adapted-v2": 2},
        {"none": 1.0, "adapted-v2": 0.5},
        writing_failed={("adapted-v2", 0)},
    )
    seat = _decide(failed)
    assert seat["decision"] == "no change"
    assert "writing inconclusive" in " ".join(seat["comparisons"]["adapted-v2"]["rule"]["reasons"])
