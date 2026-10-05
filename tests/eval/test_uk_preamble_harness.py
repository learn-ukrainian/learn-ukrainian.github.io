"""Runner resume, attribution, conditions, judging, paths and report-rule tests with a fake dispatcher (#9623)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

import scripts.eval.uk_preamble.__main__ as cli
from scripts.eval.uk_preamble.common import (
    SCORING_VERSION,
    SEATS,
    HarnessError,
    ResultsDir,
    judge_seats,
    read_json,
    sha256_text,
)
from scripts.eval.uk_preamble.dataset import load_set, parse_variants
from scripts.eval.uk_preamble.dispatch import DispatchError, TaskOutcome, composition_of
from scripts.eval.uk_preamble.report import build_report, render_markdown
from scripts.eval.uk_preamble.runner import (
    Executor,
    candidate_slots,
    pair_checks,
    plan_candidate_tasks,
    plan_judge_tasks,
    rules_block,
)
from scripts.eval.uk_preamble.scoring import LOGGING_KEYS, score_judgements

PREAMBLE = "Ти — досвідчений редактор української мови."
_INPUT = re.compile(r"Input:\n```json\n(.*)\n```\n\Z", re.DOTALL)
SHORT_TEXT = "Сьогодні я відпочиваю вдома з родиною."


def _inputs(prompt: str) -> list[dict[str, Any]]:
    return json.loads(_INPUT.search(prompt).group(1))["items"]


class FakeDispatcher:
    """Answers instantly: the preamble variant corrects every seeded error, the baseline none.

    Composes like delegate in a registered worktree: a rules core and worktree block lead
    the prompt, and the worktree block's sparse note depends on paths the prompt names.
    """

    def __init__(self, eval_set: dict[str, Any], cwd: Path) -> None:
        self.accepted = {item["id"]: item for item in eval_set["review"]}
        self.cwd = cwd
        self.dispatched: list[tuple[str, bool]] = []
        self.waited: list[str] = []
        self.preflighted: list[str] = []
        self.records: dict[str, TaskOutcome] = {}
        self.status_for: dict[str, str] = {}
        self.model_for: dict[str, str] = {}
        self.garbage_for: set[str] = set()
        self.refuse: set[str] = set()
        self.foreign_prompt: set[str] = set()
        self.conditions_for: dict[str, dict[str, Any]] = {}
        self.writing_for: dict[tuple[bool, str], str] = {}  # (has preamble, item id) -> text
        self.hard_timeout = 3600
        self.core = "[rules core]\n\n"

    def _composed(self, prompt: str) -> str:
        sparse = "" if "curriculum/" in prompt else "Sparse-checkout is active: curriculum.\n"
        return f"{self.core}[delegate worktree] {self.cwd}\n{sparse}\n{prompt}"

    def compose(self, prompt: str) -> dict[str, Any]:
        return composition_of(
            self._composed(prompt),
            prompt,
            cwd=str(self.cwd),
            worktree_path=str(self.cwd),
            blocks=["rules_core", "worktree"],
        )

    def _review(self, prompt: str) -> dict[str, Any]:
        items = []
        for entry in _inputs(prompt):
            corrections = []
            if PREAMBLE in prompt:
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
            items = [
                {"id": e["id"], "text": self.writing_for.get((PREAMBLE in prompt, e["id"]), SHORT_TEXT)}
                for e in _inputs(prompt)
            ]
            return json.dumps({"items": items}, ensure_ascii=False)
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

    def expected_args_sha256(self, task_id, seat, kind, prompt_path: Path) -> str:
        return sha256_text(f"{task_id}|{seat.seat_id}|{kind}|{prompt_path}|{self.hard_timeout}")

    def dispatch(self, task_id, seat, kind, prompt_path: Path, *, force_new: bool) -> str:
        if task_id in self.refuse:
            raise DispatchError("host admission refused")
        self.dispatched.append((task_id, force_new))
        prompt = prompt_path.read_text(encoding="utf-8")
        response = "I could not do it." if task_id in self.garbage_for else self._respond(kind, prompt)
        prompt_sha = sha256_text("another prompt" if task_id in self.foreign_prompt else prompt)
        conditions = {
            "effective_prompt_sha256": sha256_text(self._composed(prompt)),
            "prompt_blocks": ["rules_core", "worktree"],
            "dispatch_args_sha256": self.expected_args_sha256(task_id, seat, kind, prompt_path),
            "cwd": str(self.cwd),
            "mode": "read-only",
            "worktree_path": str(self.cwd),
            "research": None,
            "effort": seat.effort,
            "cli_version": "1.0",
            "harness": None,
            "resolved_model": seat.model,
            "output_schema_sha256": None,
            **self.conditions_for.get(task_id, {}),
        }
        self.records[task_id] = TaskOutcome(
            task_id=task_id,
            status=self.status_for.get(task_id, "done"),
            agent=seat.agent,
            model=self.model_for.get(task_id, seat.model),
            substitution=None,
            response_text=response,
            result_sha256=sha256_text(response),
            run_nonce=f"nonce-{task_id}",
            prompt_sha256=prompt_sha,
            conditions=conditions,
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


def _make_env(
    tmp_path: Path, outside_dir: Path, set_dict: dict[str, Any], monkeypatch: pytest.MonkeyPatch, *extra: str
):
    set_path = tmp_path / "set.json"
    set_path.write_text(json.dumps(set_dict, ensure_ascii=False), encoding="utf-8")
    preamble = tmp_path / "adapted.md"
    preamble.write_text(PREAMBLE + "\n", encoding="utf-8")
    worker = tmp_path / "worker"
    worker.mkdir()
    fake = FakeDispatcher(set_dict, worker.resolve())
    workspace = {"head": "commit-a"}

    def make_dispatcher(args, cwd, bound=fake):
        bound.hard_timeout = args.hard_timeout
        return bound

    monkeypatch.setattr(cli, "make_dispatcher", make_dispatcher)
    monkeypatch.setattr(cli, "make_workspace", lambda cwd: lambda: dict(workspace))
    monkeypatch.setattr(cli, "make_sources", FakeSources)
    results = outside_dir / "results"
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
        "--worker-cwd",
        str(worker),
        "--spawn-interval",
        "0",
        "--max-parallel",
        "2",
        *extra,
    ]
    tag = load_set(set_path).sha256[:10]
    return {
        "fake": fake,
        "results": results,
        "run": run_args,
        "set": set_path,
        "preamble": preamble,
        "tag": tag,
        "workspace": workspace,
    }


@pytest.fixture
def env(tmp_path: Path, outside_dir: Path, mini_set_dict: dict[str, Any], monkeypatch: pytest.MonkeyPatch):
    return _make_env(tmp_path, outside_dir, mini_set_dict, monkeypatch, "--repeats", "2", "--smoke")


@pytest.fixture
def full_env(tmp_path: Path, outside_dir: Path, full_set_dict: dict[str, Any], monkeypatch: pytest.MonkeyPatch):
    return _make_env(tmp_path, outside_dir, full_set_dict, monkeypatch, "--chunk-size", "30")


def tid(env, code: str, label: str, repeat: int, kind: str, chunk: int = 0) -> str:
    return f"uk9623-{env['tag']}-{code}-{label}-r{repeat}-{kind}-{chunk:02d}"


def _task_ids(results: Path) -> list[str]:
    return sorted(p.stem for p in (results / "raw").glob("*.json") if not p.name.endswith(".pending.json"))


def _score(env, *extra: str) -> int:
    return cli.main(["score", "--results", str(env["results"]), "--spawn-interval", "0", *extra])


def _report(env, capsys) -> tuple[dict[str, Any], str]:
    capsys.readouterr()
    assert cli.main(["report", "--results", str(env["results"]), "--bootstrap", "300"]) == 0
    return read_json(env["results"] / "report.json"), capsys.readouterr().out


# 3 seats x 2 variants x 2 repeats x (1 review chunk + 1 writing chunk)
PLANNED = 24


# --------------------------------------------------------------------------- run and resume


def _dispatcher_python(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, python: str | None) -> str:
    seen: dict[str, Any] = {}

    class Recorder:
        def __init__(self, **kwargs: Any) -> None:
            seen.update(kwargs)

    monkeypatch.setattr(cli, "DelegateDispatcher", Recorder)
    args = cli.build_parser().parse_args(
        ["run", "--set", "s", "--results", "r", "--variant", "none", *(["--python", python] if python else [])]
    )
    cli.make_dispatcher(args, tmp_path)
    return seen["python"]


def test_default_interpreter_comes_from_the_shared_helper(monkeypatch, tmp_path: Path):
    asked: list[Path] = []

    def fake(root: Path | None = None) -> Path:
        asked.append(root)
        return tmp_path / "shared-python"

    monkeypatch.setattr(cli, "project_interpreter", fake)
    assert _dispatcher_python(monkeypatch, tmp_path, None) == str(tmp_path / "shared-python")
    assert asked == [cli.REPO_ROOT]


def test_python_flag_overrides_the_helper(monkeypatch, tmp_path: Path):
    def refuse(root: Path | None = None) -> Path:
        raise AssertionError("helper must not run when --python is given")

    monkeypatch.setattr(cli, "project_interpreter", refuse)
    assert _dispatcher_python(monkeypatch, tmp_path, "/custom/python") == "/custom/python"


def test_missing_project_interpreter_is_a_harness_error(monkeypatch, tmp_path: Path):
    def missing(root: Path | None = None) -> Path:
        raise FileNotFoundError("no interpreter")

    monkeypatch.setattr(cli, "project_interpreter", missing)
    with pytest.raises(HarnessError, match="--python"):
        _dispatcher_python(monkeypatch, tmp_path, None)


def test_run_dispatches_every_cell_and_resume_skips_accepted(env):
    assert cli.main(env["run"]) == 0
    assert len(env["fake"].dispatched) == PLANNED
    assert len(_task_ids(env["results"])) == PLANNED
    raw = read_json(env["results"] / "raw" / f"{_task_ids(env['results'])[0]}.json")
    assert raw["accepted"] is True and raw["model"] in {seat.model for seat in SEATS.values()}
    assert raw["workspace"] == raw["workspace_after"] == {"head": "commit-a"}
    assert cli.main(env["run"]) == 0
    assert len(env["fake"].dispatched) == PLANNED  # nothing re-dispatched


def test_prompt_is_the_rendered_effective_prompt_with_the_rules_core(env):
    assert cli.main(env["run"]) == 0
    prompt = (env["results"] / "prompts" / f"{tid(env, 'sol', 'adapted-v2', 1, 'review')}.md").read_text("utf-8")
    assert prompt.startswith(rules_block() + "\n\n" + PREAMBLE + "\n\n# Task: proofreading")


def test_resume_waits_on_dispatched_task_and_orphan_without_marker_is_not_accepted(env):
    assert cli.main(env["run"]) == 0
    raw_dir = env["results"] / "raw"
    pending_id, orphan_id = _task_ids(env["results"])[:2]
    (raw_dir / f"{pending_id}.json").unlink()
    prompt_sha = sha256_text((env["results"] / "prompts" / f"{pending_id}.md").read_text(encoding="utf-8"))
    marker = {"run_nonce": "n", "prompt_sha256": prompt_sha, "workspace": {"head": "commit-a"}}
    (raw_dir / f"{pending_id}.pending.json").write_text(json.dumps(marker))
    (raw_dir / f"{orphan_id}.json").unlink()  # dispatched, crashed before the pending marker
    env["fake"].waited.clear()
    assert cli.main(env["run"]) == 1  # the orphan's dispatch-time checkout is unknown
    assert len(env["fake"].dispatched) == PLANNED
    assert sorted(env["fake"].waited) == sorted([pending_id, orphan_id])
    assert not (raw_dir / f"{pending_id}.pending.json").exists()
    assert read_json(raw_dir / f"{pending_id}.json")["accepted"] is True
    orphan = read_json(raw_dir / f"{orphan_id}.json")
    assert orphan["accepted"] is False and "unknown" in orphan["condition_problem"]
    assert cli.main([*env["run"], "--retry-failed"]) == 0
    assert env["fake"].dispatched[-1] == (orphan_id, True)


def test_failed_task_kept_and_redispatched_only_with_retry(env, capsys):
    victim = tid(env, "flash", "none", 1, "review")
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
    victim = tid(env, "flash", "none", 1, "review")
    env["fake"].model_for[victim] = "gemini-3.1-pro-preview"
    assert cli.main(env["run"]) == 1
    raw = read_json(env["results"] / "raw" / f"{victim}.json")
    assert raw["accepted"] is False and "gemini-3.1-pro-preview" in raw["identity_problem"]
    assert _score(env) == 0
    scores = read_json(env["results"] / "scores.json")
    failed = [r for r in scores["review"] if r["task_id"] == victim]
    assert len(failed) == 4 and all(r["failed"] and r["task_state"] == "not_accepted" for r in failed)
    assert all("gemini-3.1-pro-preview" in r["reason"] for r in failed)


def test_answer_to_a_different_prompt_is_not_accepted(env):
    victim = tid(env, "flash", "none", 1, "review")
    env["fake"].foreign_prompt.add(victim)
    assert cli.main(env["run"]) == 1
    raw = read_json(env["results"] / "raw" / f"{victim}.json")
    assert raw["accepted"] is False and "not the planned" in raw["identity_problem"]


def test_dispatch_refusal_leaves_no_record_and_rerun_dispatches(env):
    victim = tid(env, "opus", "none", 1, "review")
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


def test_dry_run_preflights_every_task_without_dispatch(env):
    assert cli.main([*env["run"], "--dry-run"]) == 0
    assert len(env["fake"].preflighted) == PLANNED and env["fake"].dispatched == []
    assert all(task_id.endswith("-preflight") for task_id in env["fake"].preflighted)
    assert cli.main([*env["run"], "--dry-run"]) == 0  # a completed dry run can be repeated
    assert len(env["fake"].preflighted) == PLANNED * 2 and env["fake"].dispatched == []
    assert cli.main(env["run"]) == 0  # a later real run dispatches every task
    assert len(env["fake"].dispatched) == PLANNED


def test_manifest_frozen_under_old_dispatch_arguments_refuses_to_resume(env, capsys):
    assert cli.main([*env["run"], "--dry-run"]) == 0
    path = env["results"] / "manifest.json"
    manifest = read_json(path)
    frozen_args = manifest["frozen"]["dispatch_args_sha256"]
    assert set(frozen_args) == {f"{kind}/{seat}" for kind in ("review", "writing") for seat in SEATS}
    manifest["frozen"]["dispatch_args_sha256"] = {key: "0" * 64 for key in frozen_args}
    path.write_text(json.dumps(manifest), encoding="utf-8")
    capsys.readouterr()
    assert cli.main([*env["run"], "--dry-run"]) == 2
    err = capsys.readouterr().err
    assert "different dispatch arguments" in err and "--run-tag" in err and "never mixed" in err
    assert len(env["fake"].preflighted) == PLANNED and env["fake"].dispatched == []


def test_malformed_output_counted_as_failed_items(env):
    victim = tid(env, "flash", "none", 1, "review")
    env["fake"].garbage_for.add(victim)
    assert cli.main(env["run"]) == 0  # the task ran and is attributable; its items fail at scoring
    assert _score(env) == 0
    scores = read_json(env["results"] / "scores.json")
    rows = [r for r in scores["review"] if r["task_id"] == victim]
    assert len(rows) == 4 and all(r["failed"] and "unparseable" in r["reason"] for r in rows)
    assert len(scores["review"]) == 3 * 2 * 2 * 4  # every planned item is present


# --------------------------------------------------------------------------- finding 1: private outputs stay private


def test_results_inside_this_repository_refused_before_any_write(env, capsys):
    target = cli.REPO_ROOT / "docs" / "evaluations" / "uk9623-escape-probe"
    args = list(env["run"])
    args[args.index("--results") + 1] = str(target)
    assert cli.main(args) == 2
    assert "inside the Git work tree" in capsys.readouterr().err
    assert not target.exists() and env["fake"].dispatched == []
    for command in (["score", "--results", str(target)], ["report", "--results", str(target)]):
        assert cli.main(command) == 2
    assert not target.exists()


def test_results_inside_any_work_tree_or_symlinked_into_one_refused(env, tmp_path: Path):
    other = tmp_path / "other-checkout"
    (other / ".git").mkdir(parents=True)
    link = tmp_path / "innocent-link"
    link.symlink_to(other)
    for target in (other / "results", link / "results", link):
        args = list(env["run"])
        args[args.index("--results") + 1] = str(target)
        assert cli.main(args) == 2
    assert not (other / "results").exists() and env["fake"].dispatched == []


@pytest.mark.parametrize("tag", ["../../docs/evaluations/x", "Upper", "a" * 33, "-lead", "a/b", "safe\n"])
def test_unsafe_run_tag_refused_before_anything_is_written(env, tag, capsys):
    assert cli.main([*env["run"], f"--run-tag={tag}"]) == 2
    assert "--run-tag" in capsys.readouterr().err
    assert not env["results"].exists()


def test_results_paths_stay_inside_the_results_directory(outside_dir: Path):
    results = ResultsDir(outside_dir / "results")
    assert results.path("raw", "uk9623-x.json") == results.root / "raw" / "uk9623-x.json"
    for parts in (("..", "x"), ("raw", "../../x"), (".hidden",), ("raw/x",), ("x.json\n",)):
        with pytest.raises(HarnessError):
            results.path(*parts)
    outside = outside_dir / "elsewhere"
    outside.mkdir()
    (results.root).mkdir()
    (results.root / "raw").symlink_to(outside)
    with pytest.raises(HarnessError, match="outside the private results directory"):
        results.path("raw", "uk9623-x.json")


# --------------------------------------------------------------------------- finding 4: frozen denominator


def test_manifest_freezes_the_complete_plan_and_refuses_plan_drift(env, capsys):
    assert cli.main(env["run"]) == 0
    plan = read_json(env["results"] / "manifest.json")["frozen"]
    assert plan["seats"] == list(SEATS) and plan["repeats"] == 2 and plan["kinds"] == ["review", "writing"]
    assert plan["item_ids"] == {"review": ["R1", "R2", "R3", "R4"], "writing": ["W1", "W2"]}
    assert any("repeats" in s for s in plan["protocol_shortfalls"])
    capsys.readouterr()
    assert cli.main([*env["run"], "--repeats", "3"]) == 2
    assert "repeats" in capsys.readouterr().err
    assert cli.main([*env["run"], "--seat", "gpt-6.1-sol"]) == 2
    assert "seats" in capsys.readouterr().err


@pytest.mark.parametrize("old", [None, "uk-preamble-scoring/1"])
def test_manifest_from_another_scoring_version_is_refused_by_run_score_and_report(env, capsys, old):
    assert cli.main(env["run"]) == 0
    assert _score(env) == 0
    path = env["results"] / "manifest.json"
    manifest = read_json(path)
    assert manifest["frozen"]["scoring"] == SCORING_VERSION == "uk-preamble-scoring/2"
    if old is None:
        del manifest["frozen"]["scoring"]  # written before scoring was versioned
    else:
        manifest["frozen"]["scoring"] = old
    path.write_text(json.dumps(manifest), encoding="utf-8")
    capsys.readouterr()
    for command in (
        lambda: cli.main(env["run"]),
        lambda: _score(env),
        lambda: cli.main(["report", "--results", str(env["results"]), "--bootstrap", "300"]),
    ):
        assert command() == 2
        err = capsys.readouterr().err
        assert "review-scoring version" in err and "never compared across scoring versions" in err


def test_plan_below_protocol_refused_without_smoke(env, capsys):
    args = [a for a in env["run"] if a != "--smoke"]
    assert cli.main(args) == 2
    assert "below Protocol v2" in capsys.readouterr().err


def test_smoke_run_never_authorises_adoption(env, capsys):
    assert cli.main(env["run"]) == 0
    assert _score(env, "--judge") == 0
    report, markdown = _report(env, capsys)
    for seat in SEATS:
        seat_report = report["seats"][seat]
        comparison = seat_report["comparisons"]["adapted-v2"]
        assert comparison["review"]["recall_variant"] == 100.0 and comparison["review"]["recall_baseline"] == 0.0
        assert comparison["complete"] is False and comparison["rule"]["passes"] is False
        assert any(r.startswith("incomplete: smoke plan") for r in comparison["rule"]["reasons"])
        assert seat_report["decision"] == "no change"
    assert "Smoke plan" in markdown and "incomplete run" in markdown
    assert "Logging diagnostics (outside the adoption rule)" in markdown
    totals = report["seats"][next(iter(SEATS))]["totals"]["adapted-v2"]
    assert set(totals["logging"]) == set(LOGGING_KEYS)


def test_full_plan_adopts_end_to_end(full_env, capsys):
    assert cli.main(full_env["run"]) == 0
    assert _score(full_env, "--judge") == 0
    scores = read_json(full_env["results"] / "scores.json")
    assert not any(pair["problem"] for pair in scores["pairs"])
    # 3 candidate seats x 2 judges x 1 pair x 3 repeats x 4 writing tasks
    assert len(scores["judge"]) == 72 and not any(r["failed"] for r in scores["judge"])
    for record in scores["judge"]:
        assert SEATS[record["judge_seat"]].family != SEATS[record["candidate_seat"]].family
    report, markdown = _report(full_env, capsys)
    for seat in SEATS:
        assert report["seats"][seat]["complete"] is True
        assert report["seats"][seat]["decision"] == "adapted-v2"
    assert "| lexical-russianism |" in markdown


def test_missing_planned_task_makes_the_seat_incomplete(full_env, capsys):
    victim = tid(full_env, "sol", "adapted-v2", 3, "review", 1)
    full_env["fake"].refuse.add(victim)
    assert cli.main(full_env["run"]) == 1
    assert _score(full_env) == 0
    report, _ = _report(full_env, capsys)
    sol = report["seats"]["gpt-6.1-sol"]
    assert sol["decision"] == "no change" and sol["complete"] is False
    assert any("not run or not accepted" in r for r in sol["comparisons"]["adapted-v2"]["rule"]["reasons"])
    assert report["seats"]["claude-opus-5-5"]["decision"] == "adapted-v2"  # other seats are complete


def test_report_refuses_scores_from_another_plan(env, capsys):
    assert cli.main(env["run"]) == 0
    assert _score(env) == 0
    path = env["results"] / "scores.json"
    scores = read_json(path)
    scores["plan"]["repeats"] = 1
    path.write_text(json.dumps(scores), encoding="utf-8")
    assert cli.main(["report", "--results", str(env["results"])]) == 2
    assert "frozen plan" in capsys.readouterr().err


# --------------------------------------------------------------------------- finding 5: executed conditions


@pytest.mark.parametrize(
    ("override", "expected"),
    [
        ({"prompt_blocks": ["research"], "effective_prompt_sha256": "x" * 64}, "effective prompt"),
        ({"research": {"pointer_ids": ["r1"]}}, "research"),
        ({"dispatch_args_sha256": "y" * 64}, "dispatch arguments"),
        ({"cwd": "/somewhere/else"}, "cwd"),
        ({"mode": "workspace-write"}, "mode"),
        ({"worktree_path": None}, "worker worktree"),
        ({"prompt_blocks": ["rules_core", "worktree", "research"]}, "prompt blocks"),
    ],
)
def test_task_with_different_effective_context_is_not_accepted(env, override, expected):
    victim = tid(env, "sol", "adapted-v2", 1, "review")
    env["fake"].conditions_for[victim] = override
    assert cli.main(env["run"]) == 1
    raw = read_json(env["results"] / "raw" / f"{victim}.json")
    assert raw["accepted"] is False and expected in raw["condition_problem"]


def test_run_freezes_delegates_frame_and_accepts_wrapped_prompts(env):
    """Round 2: delegate wraps a worktree dispatch in rules-core and worktree blocks; the harness expects that."""
    assert cli.main(env["run"]) == 0
    manifest = read_json(env["results"] / "manifest.json")
    composition = manifest["frozen"]["composition"]
    assert composition["prompt_blocks"] == ["rules_core", "worktree"]
    assert composition["worktree_path"] == str(env["fake"].cwd)
    raw = read_json(env["results"] / "raw" / f"{tid(env, 'sol', 'adapted-v2', 1, 'review')}.json")
    assert raw["accepted"] is True and raw["conditions"]["effective_prompt_sha256"] != raw["prompt_sha256"]
    assert raw["composition"]["effective_prompt_sha256"] == raw["conditions"]["effective_prompt_sha256"]


def test_preamble_that_changes_delegates_frame_is_refused_before_dispatch(env, capsys):
    env["preamble"].write_text(PREAMBLE + " Див. curriculum/a1.\n", encoding="utf-8")
    assert cli.main(env["run"]) == 2
    err = capsys.readouterr().err
    assert "differently" in err and "prefix_sha256" in err and "more than the preamble" in err
    assert env["fake"].dispatched == [] and not (env["results"] / "manifest.json").exists()


def test_changed_composition_refuses_resume_and_mid_run_drift_is_not_dispatched(env, capsys):
    assert cli.main(env["run"]) == 0
    env["fake"].core = "[changed rules core]\n\n"
    capsys.readouterr()
    assert cli.main(env["run"]) == 2
    assert "composition" in capsys.readouterr().err
    # A frame that changes after the plan froze stops the dispatch (no paid run under other conditions).
    plan = read_json(env["results"] / "manifest.json")["frozen"]
    results = ResultsDir(env["results"])
    fake = env["fake"]
    executor = Executor(
        fake, results, worker_cwd=fake.cwd, workspace=lambda: {"head": "commit-a"}, frame=plan["composition"]
    )
    variants = parse_variants(["none", f"adapted-v2={env['preamble']}"])
    task = plan_candidate_tasks(load_set(env["set"]), variants, plan, rules_block())[0]
    (results.root / "raw" / f"{task.task_id}.json").unlink()
    del fake.records[task.task_id]  # never dispatched: the next run dispatches it afresh
    summary = executor.run([task])
    assert summary.not_run == [task.task_id] and len(fake.dispatched) == PLANNED


def test_worker_checkout_change_during_a_task_is_not_accepted(env):
    victim = tid(env, "sol", "adapted-v2", 1, "review")
    original = env["fake"].dispatch

    def moving(task_id, *args, **kwargs):
        if task_id == victim:
            env["workspace"]["head"] = "commit-b"
        return original(task_id, *args, **kwargs)

    env["fake"].dispatch = moving
    assert cli.main([*env["run"], "--max-parallel", "1"]) == 1
    raw = read_json(env["results"] / "raw" / f"{victim}.json")
    assert raw["accepted"] is False and "changed while the task ran" in raw["condition_problem"]


def test_paired_arms_with_different_conditions_are_invalid_and_block_adoption(full_env, capsys):
    victim = tid(full_env, "opus", "adapted-v2", 2, "writing")
    full_env["fake"].conditions_for[victim] = {"cli_version": "2.0"}
    assert cli.main(full_env["run"]) == 0  # each task is individually attested
    assert _score(full_env) == 0
    scores = read_json(full_env["results"] / "scores.json")
    invalid = [p for p in scores["pairs"] if p["problem"]]
    assert [p["variant_task"] for p in invalid] == [victim]
    assert "cli_version" in invalid[0]["problem"]
    report, _ = _report(full_env, capsys)
    opus = report["seats"]["claude-opus-5-5"]
    assert opus["decision"] == "no change"
    assert any("invalid pairs" in r for r in opus["comparisons"]["adapted-v2"]["rule"]["reasons"])
    assert report["seats"]["gpt-6.1-sol"]["decision"] == "adapted-v2"


def test_pair_check_catches_checkout_and_prompt_differences(full_env):
    assert cli.main(full_env["run"]) == 0
    results = ResultsDir(full_env["results"])
    plan = read_json(full_env["results"] / "manifest.json")["frozen"]
    slots = candidate_slots(plan)
    assert not any(p["problem"] for p in pair_checks(results, plan, slots))
    victim = tid(full_env, "flash", "adapted-v2", 1, "review")
    path = full_env["results"] / "raw" / f"{victim}.json"
    raw = read_json(path)
    path.write_text(json.dumps({**raw, "workspace": {"head": "commit-b"}}), encoding="utf-8")
    problems = {p["variant_task"]: p["problem"] for p in pair_checks(results, plan, slots) if p["problem"]}
    assert problems == {victim: "arms ran under different conditions: worker checkout"}
    # An arm framed differently by delegate (its record attests another prefix).
    reframed = {**raw["composition"], "prefix_sha256": "f" * 64}
    path.write_text(json.dumps({**raw, "composition": reframed}), encoding="utf-8")
    problems = {p["variant_task"]: p["problem"] for p in pair_checks(results, plan, slots) if p["problem"]}
    assert problems == {victim: "delegate framed the arms differently or not as frozen"}
    # A prompt that differs in more than the preamble (attested, so the stored file matches the record).
    path.write_text(json.dumps(raw), encoding="utf-8")
    prompt_file = full_env["results"] / "prompts" / f"{victim}.md"
    tampered = prompt_file.read_text("utf-8").replace("# Task: proofreading", "# Task: proofreading!")
    prompt_file.write_text(tampered, encoding="utf-8")
    path.write_text(json.dumps({**raw, "prompt_sha256": sha256_text(tampered)}), encoding="utf-8")
    problems = {p["variant_task"]: p["problem"] for p in pair_checks(results, plan, slots) if p["problem"]}
    assert problems == {victim: "prompts differ in more than the frozen preamble"}


# --------------------------------------------------------------------------- finding 6: judge length control


def test_judge_length_control_excludes_out_of_bound_pairs_and_records_lengths(env):
    long_text = " ".join(["слово"] * 300)
    env["fake"].writing_for[(True, "W1")] = long_text  # 300 words against the baseline's 6: excluded
    env["fake"].writing_for[(True, "W2")] = "Сьогодні я відпочиваю вдома з родиною та друзями."  # 8 words
    env["fake"].writing_for[(False, "W2")] = "Сьогодні я відпочиваю вдома з родиною, друзями."  # 7 words: 0.875
    assert cli.main(env["run"]) == 0
    assert _score(env, "--judge") == 0
    scores = read_json(env["results"] / "scores.json")
    assert scores["judge_terms"]["length_ratio_min"] == 0.8
    excluded = {(e["item_id"], e["reason"]) for e in scores["judge_exclusions"]}
    assert excluded == {("W1", "length ratio 0.02 < 0.8")}
    assert all(e["words"] == {"none": 6, "adapted-v2": 300} for e in scores["judge_exclusions"])
    assert {r["item_id"] for r in scores["judge"]} == {"W2"}
    assert all(r["words"] == {"none": 7, "adapted-v2": 8} for r in scores["judge"])
    judge_prompts = [p for p in (env["results"] / "prompts").glob("*judge*.md")]
    assert judge_prompts and not any(long_text in p.read_text("utf-8") for p in judge_prompts)
    manifest = read_json(env["results"] / "manifest.json")
    assert manifest["judge"]["length_ratio_min"] == 0.8


def test_judge_ratio_exactly_at_the_bound_is_judged_and_terms_are_frozen(env, capsys):
    env["fake"].writing_for[(True, "W1")] = "Один два три чотири."  # 4 words vs 5: ratio 0.8
    env["fake"].writing_for[(False, "W1")] = "Один два три чотири п'ять."
    assert cli.main(env["run"]) == 0
    assert _score(env, "--judge") == 0
    scores = read_json(env["results"] / "scores.json")
    assert "W1" in {r["item_id"] for r in scores["judge"]}
    capsys.readouterr()
    assert _score(env, "--judge-length-ratio", "0.5") == 2
    assert "judge terms were frozen" in capsys.readouterr().err


def test_score_judge_refuses_a_legacy_manifest_before_any_dispatch(env, capsys):
    """A manifest without dispatch_args_sha256 must not start judges (review round 2)."""
    assert cli.main(env["run"]) == 0
    path = env["results"] / "manifest.json"
    manifest = read_json(path)
    del manifest["frozen"]["dispatch_args_sha256"]
    path.write_text(json.dumps(manifest), encoding="utf-8")
    before = list(env["fake"].dispatched)
    capsys.readouterr()
    assert _score(env, "--judge") == 2
    err = capsys.readouterr().err
    assert "dispatch_args_sha256" in err and "--run-tag" in err and "never mixed" in err
    assert env["fake"].dispatched == before
    assert "judge" not in read_json(path)


def test_judge_retry_with_different_arguments_is_refused_before_dispatch(env, capsys):
    """A retry that changes --hard-timeout must not dispatch, or reuse judges frozen earlier."""
    assert cli.main(env["run"]) == 0
    assert _score(env, "--judge") == 0
    manifest = read_json(env["results"] / "manifest.json")
    frozen_args = manifest["judge"]["dispatch_args_sha256"]
    assert set(frozen_args) == set(SEATS)
    judge_ids = [task_id for task_id, _force in env["fake"].dispatched if "-judge-" in task_id]
    assert judge_ids
    victim = judge_ids[0]
    raw_path = env["results"] / "raw" / f"{victim}.json"
    raw = read_json(raw_path)
    raw["accepted"] = False
    raw["status"] = "timeout"
    raw_path.write_text(json.dumps(raw), encoding="utf-8")
    before = list(env["fake"].dispatched)
    capsys.readouterr()
    assert _score(env, "--judge", "--retry-failed", "--hard-timeout", "17") == 2
    err = capsys.readouterr().err
    assert "per seat" in err and "--run-tag" in err and "never mixed" in err
    assert env["fake"].dispatched == before
    assert read_json(env["results"] / "manifest.json")["judge"]["dispatch_args_sha256"] == frozen_args
    # The same frozen arguments still retry only the failed judge.
    assert _score(env, "--judge", "--retry-failed") == 0
    assert env["fake"].dispatched == [*before, (victim, True)]


def _judge_dispatch_ids(env) -> list[str]:
    return [task_id for task_id, _force in env["fake"].dispatched if "-judge-" in task_id]


def _clear_judge_scores(env) -> None:
    path = env["results"] / "scores.json"
    scores = read_json(path)
    scores["judge"] = []
    path.write_text(json.dumps(scores), encoding="utf-8")


def _remove_judge_raw(env) -> None:
    for path in (env["results"] / "raw").glob("*judge*"):
        path.unlink()


@pytest.mark.parametrize("keep", ["result", "record", "score", "pending", "result-no-block"])
def test_missing_judge_hash_with_prior_judge_evidence_is_refused(env, capsys, keep):
    """Judges that ran before per-seat hashes existed must not be mixed with new arguments.

    A manifest with candidate hashes but no judge hash, plus any judge record, result
    or accepted score for this run tag, is refused before the manifest changes and
    before any dispatch. The guidance is a new ``--run-tag``.
    """
    assert cli.main(env["run"]) == 0
    assert _score(env, "--judge") == 0
    judge_ids = _judge_dispatch_ids(env)
    assert len(judge_ids) == 12
    scores = read_json(env["results"] / "scores.json")
    assert any(row.get("failed") is False and "-judge-" in row["task_id"] for row in scores["judge"])
    victim = judge_ids[0]
    raw_path = env["results"] / "raw" / f"{victim}.json"
    raw = read_json(raw_path)
    raw["accepted"] = False
    raw["status"] = "timeout"
    raw_path.write_text(json.dumps(raw), encoding="utf-8")
    path = env["results"] / "manifest.json"
    manifest = read_json(path)
    if keep == "result-no-block":
        del manifest["judge"]
    else:
        del manifest["judge"]["dispatch_args_sha256"]
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if keep in {"record", "score", "pending"}:
        _remove_judge_raw(env)
    if keep != "score":
        _clear_judge_scores(env)
    if keep != "record":
        env["fake"].records.clear()
    if keep == "pending":
        (env["results"] / "raw" / f"{victim}.pending.json").write_text("{}\n", encoding="utf-8")
    raw_names = sorted(p.name for p in (env["results"] / "raw").glob("*judge*"))
    if keep in {"result", "result-no-block"}:
        assert raw_names
        assert not env["fake"].known(victim)
    elif keep == "pending":
        assert raw_names == [f"{victim}.pending.json"]
        assert not env["fake"].known(victim)
    elif keep == "record":
        assert raw_names == []
        assert env["fake"].known(victim)
    else:
        assert raw_names == []
        assert not env["fake"].known(victim)
        assert any(row.get("failed") is False for row in read_json(env["results"] / "scores.json")["judge"])
    blob = path.read_bytes()
    dispatched = list(env["fake"].dispatched)
    waited = list(env["fake"].waited)
    capsys.readouterr()
    assert _score(env, "--judge", "--retry-failed", "--hard-timeout", "17") == 2
    err = capsys.readouterr().err
    assert "never frozen" in err and "already ran" in err and "--run-tag" in err and "never mixed" in err
    if keep == "pending":
        assert f"result {victim}.pending.json" in err
    elif keep == "record":
        assert "judge record " in err
    elif keep == "score":
        assert "accepted score " in err
    else:
        assert "result " in err and ".pending.json" not in err
    assert path.read_bytes() == blob
    assert env["fake"].dispatched == dispatched
    assert env["fake"].waited == waited


def test_first_judge_execution_freezes_arguments_and_dispatches(env):
    """No judge record, result or score: the first ``score --judge`` still freezes and runs.

    An earlier candidate-only score writes ``scores.json`` with an empty judge list.
    That is not judge evidence, so the hash is stored and the judges are dispatched.
    """
    assert cli.main(env["run"]) == 0
    assert _score(env) == 0
    assert read_json(env["results"] / "scores.json")["judge"] == []
    manifest_path = env["results"] / "manifest.json"
    assert "judge" not in read_json(manifest_path)
    before = list(env["fake"].dispatched)
    assert _score(env, "--judge") == 0
    frozen = read_json(manifest_path)["judge"]["dispatch_args_sha256"]
    assert set(frozen) == set(SEATS)
    new = env["fake"].dispatched[len(before) :]
    assert new and all("-judge-" in task_id for task_id, _force in new)
    assert all(read_json(env["results"] / "raw" / f"{task_id}.json")["accepted"] for task_id, _force in new)
    assert _score(env, "--judge") == 0
    assert env["fake"].dispatched == [*before, *new]
    assert read_json(manifest_path)["judge"]["dispatch_args_sha256"] == frozen


def test_judge_terms_freeze_on_the_first_judging_call_even_when_every_pair_is_excluded(env, capsys):
    """Round 2: an all-excluded first ``score --judge`` froze nothing, so ratio 0.005 was accepted later."""
    long_text = " ".join(["слово"] * 300)
    for item_id in ("W1", "W2"):
        env["fake"].writing_for[(True, item_id)] = long_text  # 300 words against 6: every pair excluded
    assert cli.main(env["run"]) == 0
    assert _score(env, "--judge") == 0
    scores = read_json(env["results"] / "scores.json")
    assert scores["judge"] == [] and len(scores["judge_exclusions"]) == 3 * 2 * 2
    assert read_json(env["results"] / "manifest.json")["judge"]["length_ratio_min"] == 0.8
    capsys.readouterr()
    assert _score(env, "--judge", "--judge-length-ratio", "0.005") == 2
    assert "judge terms were frozen" in capsys.readouterr().err
    assert not any("judge" in p.name for p in (env["results"] / "prompts").iterdir())


def test_judge_order_is_randomised_blind_and_mapped_back(env):
    assert cli.main(env["run"]) == 0
    set_obj = load_set(env["set"])
    results = ResultsDir(env["results"])
    plan = read_json(env["results"] / "manifest.json")["frozen"]
    terms = {"seed": 7, "chunk_size": 8, "length_ratio_min": 0.8}
    tasks, exclusions = plan_judge_tasks(set_obj, results, plan, terms, rules_block())
    assert len(tasks) == 3 * 2 * 2 and exclusions == []
    orders = []
    for task in tasks:
        assert task.seat in judge_seats(task.meta["candidate_seat"])
        assert "adapted-v2" not in task.prompt and PREAMBLE not in task.prompt  # blind
        orders += [entry["A"] for entry in task.meta["order"].values()]
    assert set(orders) == {"none", "adapted-v2"}  # both orders occur
    again, _ = plan_judge_tasks(set_obj, results, plan, terms, rules_block())
    assert [t.task_id for t in again] == [t.task_id for t in tasks]  # deterministic, resumable
    fake = env["fake"]
    executor = Executor(fake, results, worker_cwd=fake.cwd, workspace=lambda: {"head": "commit-a"}, spawn_interval=0)
    for task in tasks:
        path = results.path("prompts", f"{task.task_id}.md")
        path.write_text(task.prompt, encoding="utf-8")
        fake.dispatch(task.task_id, task.seat, "judge", path, force_new=False)
        executor._record(task, fake.records[task.task_id], {"head": "commit-a"})
    records = score_judgements(results, tasks)
    assert records and not any(r["failed"] for r in records)
    for record in records:
        task = next(t for t in tasks if t.task_id == record["task_id"])
        assert record["winner"] == task.meta["order"][record["item_id"]]["A"]  # the fake always picks A


# --------------------------------------------------------------------------- adoption rule


def _plan(labels, review_items: int = 20, writing_items: int = 4, repeats: int = 3, shortfalls=()) -> dict[str, Any]:
    return {
        "seats": ["s"],
        "variants": dict.fromkeys(labels, "sha"),
        "repeats": repeats,
        "kinds": ["review", "writing"],
        "item_ids": {
            "review": [f"R{i}" for i in range(review_items)],
            "writing": [f"W{j}" for j in range(writing_items)],
        },
        "protocol_shortfalls": list(shortfalls),
    }


def _synthetic(
    recall: dict[str, list[int]],
    fa: dict[str, int],
    density: dict[str, float],
    writing_failed=(),
    repeats: int = 3,
    writing_items: int = 4,
):
    """20 one-error, one-protected-span items per repeat; ``recall[label]`` lists hit flags per item."""
    review, writing = [], []
    for label, hits in recall.items():
        for repeat in range(1, repeats + 1):
            for i, hit in enumerate(hits):
                review.append(
                    {
                        "seat": "s",
                        "variant": label,
                        "repeat": repeat,
                        "task_id": f"{label}-r{repeat}-review",
                        "task_state": "accepted",
                        "item_id": f"R{i}",
                        "failed": False,
                        "errors": [{"id": f"e{i}", "type": "paronym", "hit": bool(hit)}],
                        "protected_count": 1,
                        "hits": hit,
                        "false_alarms": 1 if i < fa[label] else 0,
                        "fa_protected": 0,
                        "fa_tokens": 0,
                        "fa_insertions": 0,
                        "fa_inserted_tokens": 0,
                        "wrong_corrections": 0,
                        "logging": dict.fromkeys(LOGGING_KEYS, 0),
                        "new_invalid_forms": [],
                        "style": {"total": 0, "on_protected": 0, "on_error": 0},
                    }
                )
            for j in range(writing_items):
                failed = (label, j) in writing_failed
                writing.append(
                    {
                        "seat": "s",
                        "variant": label,
                        "repeat": repeat,
                        "task_id": f"{label}-r{repeat}-writing",
                        "task_state": "accepted",
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
    return {"review": review, "writing": writing, "judge": [], "pairs": []}


BASE = [1] * 6 + [0] * 14
BETTER = [1] * 14 + [0] * 6


def _decide(scores, plan=None) -> dict[str, Any]:
    labels = list(dict.fromkeys(r["variant"] for r in scores["review"]))
    return build_report(scores, plan or _plan(labels), iterations=2000, seed=1)["seats"]["s"]


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
    plan = _plan(["none", "adapted-v2", "original"])
    assert "| s | original |" in render_markdown(build_report(scores, plan, iterations=200, seed=1))


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


def test_reviewer_probe_one_repeat_and_one_of_four_writing_tasks_cannot_adopt():
    """The round-1 probe: a clear recall gain over 1 repeat and 1 of 4 writing tasks adopted adapted-v2."""
    scores = _synthetic(
        {"none": BASE, "adapted-v2": BETTER},
        {"none": 2, "adapted-v2": 2},
        {"none": 1.0, "adapted-v2": 1.0},
        repeats=1,
        writing_items=1,
    )
    seat = _decide(scores, _plan(["none", "adapted-v2"], repeats=3, writing_items=4))
    reasons = " ".join(seat["comparisons"]["adapted-v2"]["rule"]["reasons"])
    assert seat["decision"] == "no change" and seat["complete"] is False
    assert "40 of 60 planned answers missing" in reasons  # review: 2 of 3 repeats missing
    assert "11 of 12 planned answers missing" in reasons  # writing


def test_duplicated_or_unplanned_answers_make_a_comparison_incomplete():
    scores = _synthetic(
        {"none": BASE, "adapted-v2": BETTER}, {"none": 2, "adapted-v2": 2}, {"none": 1, "adapted-v2": 1}
    )
    scores["review"].append({**scores["review"][0]})
    scores["writing"].append({**scores["writing"][0], "item_id": "W99"})
    seat = _decide(scores)
    reasons = " ".join(seat["comparisons"]["adapted-v2"]["rule"]["reasons"])
    assert seat["decision"] == "no change"
    assert "recorded more than once" in reasons and "unplanned answers" in reasons
