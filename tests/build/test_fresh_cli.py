"""Tests for fresh build engine Part E2 CLI entry, end-to-end loading, and --help standard compliance (#8431 r3)."""

from __future__ import annotations

import argparse
import copy
import hashlib
import re
import stat
import subprocess
import sys
from functools import partial
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from scripts.build.fresh.cli import _build_parser, main
from scripts.build.fresh.manifest import learner_state_document, learner_state_sha256, materialize_learner_state
from scripts.build.fresh.module import build_module
from scripts.build.fresh.path_guard import checked_path
from scripts.build.fresh.prompt import style_card_info
from scripts.build.fresh.regeneration import writer_inputs, writer_task_id
from scripts.build.fresh.writer import WriterCallError, dispatch_writer
from scripts.curriculum.evidence import lesson_lock, lock
from scripts.curriculum.learner_state.planned import planned_state
from scripts.review.prompts.render import ManifestReader, _learner_state_context
from tests.build.test_fresh_draft_schema import load_fixture

pytestmark = pytest.mark.reads_content

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_cli_parser_help_standard_compliance():
    """Verify that main parser and all subparsers meet cli-help-standard.md."""
    parser = _build_parser()

    # 1. Main parser
    assert parser.description is not None
    assert "\n" in parser.description, "description must have at least two lines"
    assert parser.epilog is not None
    for section in ("Examples:", "Outputs:", "Exit codes:", "Related:"):
        assert section in parser.epilog, f"main parser epilog missing {section}"

    # 2. Subparsers
    subparsers_action = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction))
    assert "render-prompt" in subparsers_action.choices
    assert "preflight" in subparsers_action.choices
    assert "write" in subparsers_action.choices

    for cmd_name, subp in subparsers_action.choices.items():
        assert subp.description is not None, f"subparser {cmd_name} missing description"
        assert "\n" in subp.description, f"subparser {cmd_name} description must have at least two lines"
        assert subp.epilog is not None, f"subparser {cmd_name} missing epilog"
        for section in ("Examples:", "Outputs:", "Exit codes:", "Related:"):
            assert section in subp.epilog, f"subparser {cmd_name} epilog missing {section}"
        for action in subp._actions:
            if action.dest != "help":
                assert action.help is not None and len(action.help) > 0, (
                    f"argument {action.dest} in subparser {cmd_name} missing help"
                )


@pytest.mark.parametrize("subcmd", [None, "render-prompt", "preflight", "write"])
def test_cli_subprocess_help(subcmd):
    """Run CLI --help in a clean subprocess with explicit timeout."""
    cmd = [sys.executable, "-m", "scripts.build.fresh.cli"]
    if subcmd:
        cmd.extend([subcmd, "--help"])
    else:
        cmd.append("--help")

    proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=10, check=False)
    assert proc.returncode == 0
    assert "Examples:" in proc.stdout
    assert "Outputs:" in proc.stdout
    assert "Exit codes:" in proc.stdout
    assert "Related:" in proc.stdout


def test_main_module_forwarding():
    """Verify that python -m scripts.build.fresh --help also works and returns code 0."""
    cmd = [sys.executable, "-m", "scripts.build.fresh", "--help"]
    proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=10, check=False)
    assert proc.returncode == 0
    assert "Fresh build engine E2" in proc.stdout


def _build_synthetic_tree(root: Path) -> dict[str, Path]:
    """Helper to build a complete synthetic level tree with plans, locked pack, locked word store, and locks."""
    plans_dir = root / "curriculum" / "l2-uk-en" / "lesson-plans" / "a1"
    plans_dir.mkdir(parents=True, exist_ok=True)
    ev_dir = root / "curriculum" / "l2-uk-en" / "evidence" / "a1"
    ev_dir.mkdir(parents=True, exist_ok=True)

    # Absence must be known from both git's index and HEAD, just as in production.
    subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True, timeout=30)
    subprocess.run(
        ["git", "-C", str(root), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.test",
         "commit", "-q", "--allow-empty", "-m", "fixture"], check=True, capture_output=True, timeout=30,
    )

    # 1. Plan v2
    plan_data = {
        "plan_schema": 2,
        "slug": "synthetic-mod",
        "title": "Synthetic Module",
        "level": "a1",
        "arc_ref": {"level": "a1", "position": 1},
        "lessons": [
            {
                "n": 1,
                "title": "Lesson 1",
                "slug": "lesson-1",
                "kind": "teach",
                "job": "Test Job",
                "rationale": "Test Rationale",
                "word_target": 10,
                "steps": [
                    {
                        "id": "s1",
                        "kind": "teach",
                        "explains": ["T-001"],
                        "ref": "EX-001",
                        "needs": ["example"],
                    }
                ],
                "consolidation": ["a1"],
                "activities": [
                    {
                        "id": "a1",
                        "type": "quiz",
                        "placement": "inline",
                        "focus": "Test",
                    }
                ],
                "inventory": {
                    "vocabulary": {
                        "core": [
                            {
                                "lemma": "слово",
                                "evidence": "W-001",
                                "forms": ["noun:inanim:n:v_naz"],
                            }
                        ],
                        "incidental": [],
                        "recycled": [],
                    },
                    "grammar": [],
                    "phonetics": {"letters": ["А"]},
                },
            },
            {
                "n": 2,
                "title": "Lesson 2 Recap",
                "slug": "lesson-2",
                "kind": "recap",
                "job": "Recap Job",
                "rationale": "Recap Rationale",
                "word_target": 10,
                "steps": [
                    {
                        "id": "s1",
                        "kind": "recap",
                        "explains": ["T-001"],
                        "ref": "EX-001",
                        "needs": ["example"],
                    }
                ],
                "consolidation": ["a1"],
                "activities": [
                    {
                        "id": "a1",
                        "type": "quiz",
                        "placement": "inline",
                        "focus": "Recap",
                    }
                ],
                "inventory": {
                    "vocabulary": {
                        "core": [
                            {
                                "lemma": "слово",
                                "evidence": "W-001",
                                "forms": ["noun:inanim:n:v_naz"],
                            }
                        ],
                        "incidental": [],
                        "recycled": [],
                    },
                    "grammar": [],
                    "phonetics": {"letters": ["А"]},
                },
            },
        ],
    }
    plan_path = plans_dir / "synthetic-mod.yaml"
    plan_path.write_text(yaml.safe_dump(plan_data, allow_unicode=True), encoding="utf-8")

    # 2. Pack
    pack_data = {
        "evidence_schema": 1,
        "module": "a1/synthetic-mod",
        "built_with": {
            "mcp_commit": "0" * 40,
            "sources_db": "0" * 64,
            "vesum": "0" * 64,
            "trie": "0" * 64,
            "ulif_forms": "0" * 64,
            "standard_sha256": "0" * 64,
        },
        "texts": [
            {
                "id": "T-001",
                "source": {
                    "kind": "textbook",
                    "file": "f.txt",
                    "grade": 1,
                    "author": "Author",
                    "section_id": 1,
                    "page": 1,
                    "chunk_id": "c1",
                },
                "quote": "Quote text",
                "sha256": "0" * 64,
                "supports": "Rule",
            }
        ],
        "examples": [
            {
                "id": "EX-001",
                "text": "Example text",
                "source": {
                    "kind": "textbook",
                    "file": "f.txt",
                    "grade": 1,
                    "author": "Author",
                    "section_id": 1,
                    "page": 1,
                    "chunk_id": "c2",
                },
                "sha256": "0" * 64,
                "sentence_ref": {"words": ["W-001"]},
            }
        ],
    }
    pack_path = ev_dir / "synthetic-mod.yaml"
    lock.write(pack_path, lock.yaml_bytes(pack_data))

    # 3. Word store
    words_data = {
        "words": [
            {
                "id": "W-001",
                "lemma": "слово",
                "pos": "noun",
                "forms": [
                    {
                        "form": "слово",
                        "tags": "noun:inanim:n:v_naz",
                        "stressed": "сло́во",
                        "stress_source": "vesum",
                        "learner": True,
                    }
                ],
            }
        ]
    }
    words_path = ev_dir / "_words.yaml"
    lock.write(words_path, lock.yaml_bytes(words_data))

    # 4. Registry and base request
    reg_path = ev_dir / "_words.registry.yaml"
    lock.write(reg_path, lock.yaml_bytes([]))
    base_req_path = ev_dir / "_base.request.yaml"
    base_req_path.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "level": "a1",
                "words": [{"lemma": "слово", "pos": "noun", "want": "new"}],
            }
        ),
        encoding="utf-8",
    )

    # 5. Lesson lock
    lesson_lock.write_lesson_lock("a1", "synthetic-mod", repo_root=root)

    return {
        "plan": plan_path,
        "pack": pack_path,
        "words": words_path,
        "state_dir": ev_dir / "_state",
    }


def test_cli_render_prompt_end_to_end_synthetic_tree(tmp_path):
    """Finding 1: End-to-end CLI test on a synthetic level tree with injected --repo-root.

    Asserts that the rendered prompt contains every cited record id and real non-zero hashes.
    """
    paths = _build_synthetic_tree(tmp_path)
    output_prompt = tmp_path / "rendered_prompt.md"

    code = main(
        [
            "render-prompt",
            "a1",
            "synthetic-mod",
            "--lesson",
            "1",
            "-o",
            str(output_prompt),
            "--repo-root",
            str(tmp_path),
        ]
    )
    assert code == 0

    assert output_prompt.is_file()
    rendered = output_prompt.read_text(encoding="utf-8")

    # 1. Contains every cited record id
    assert "W-001" in rendered
    assert "EX-001" in rendered
    assert "T-001" in rendered
    assert "No external cited records required." not in rendered

    # 2. Contains real, non-zero hashes in the inputs block (Finding 1, MINOR: all 5 checked)
    assert 'plan_sha256: "0000000000000000000000000000000000000000000000000000000000000000"' not in rendered
    assert 'pack_lock: "0000000000000000000000000000000000000000000000000000000000000000"' not in rendered
    assert 'words_lock: "0000000000000000000000000000000000000000000000000000000000000000"' not in rendered
    assert (
        'lesson_lock_entry_sha256: "0000000000000000000000000000000000000000000000000000000000000000"' not in rendered
    )
    assert 'learner_state_sha256: "0000000000000000000000000000000000000000000000000000000000000000"' not in rendered
    for h in ("plan_sha256:", "pack_lock:", "words_lock:", "lesson_lock_entry_sha256:", "learner_state_sha256:"):
        assert h in rendered

    # Verify sha256 sidecar file was always recorded (#8431, Finding 11)
    sha_file = paths["state_dir"] / "synthetic-mod" / "lesson-1.prompt.sha256"
    assert sha_file.is_file()
    recorded_sha = sha_file.read_text(encoding="ascii").strip()
    assert len(recorded_sha) == 64
    assert recorded_sha == hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def test_cli_repo_root_injected_via_env_var(tmp_path):
    """Repo root can be injected via LEARN_UKRAINIAN_REPO_ROOT environment variable."""
    _build_synthetic_tree(tmp_path)
    output_prompt = tmp_path / "env_rendered_prompt.md"

    with patch.dict("os.environ", {"LEARN_UKRAINIAN_REPO_ROOT": str(tmp_path)}):
        code = main(["render-prompt", "a1", "synthetic-mod", "--lesson", "1", "-o", str(output_prompt)])
        assert code == 0
    assert output_prompt.is_file()


def test_cli_recap_fails_closed_when_built_lesson_missing(tmp_path, capsys):
    """Finding 1: Recap fails closed and names missing built lesson (never a placeholder)."""
    _build_synthetic_tree(tmp_path)
    output_prompt = tmp_path / "rendered_recap.md"

    # Lesson 2 is recap, but lesson 1 has no built MDX, passing gates, or current manifest.
    code = main(
        [
            "render-prompt",
            "a1",
            "synthetic-mod",
            "--lesson",
            "2",
            "--recap",
            "-o",
            str(output_prompt),
            "--repo-root",
            str(tmp_path),
        ]
    )
    assert code == 1

    captured = capsys.readouterr()
    assert "recap_inputs_not_built: lesson 1" in captured.err
    assert not output_prompt.exists()


def test_cli_write_fails_preflight_writes_gap_report_atomically(tmp_path, capsys):
    """Finding 4: A failed preflight writes the gap report atomically (mode 0o644) and makes no writer call."""
    tree = _build_synthetic_tree(tmp_path)

    # Empty examples in pack to cause preflight evidence gap (missing record EX-001)
    pack_path = tree["pack"]
    pack_data = yaml.safe_load(pack_path.read_text(encoding="utf-8"))
    pack_data["examples"] = []
    lock.write(pack_path, lock.yaml_bytes(pack_data))
    # Update lesson lock so lock integrity check passes
    lesson_lock.write_lesson_lock("a1", "synthetic-mod", repo_root=tmp_path)

    code = main(
        [
            "write",
            "a1",
            "synthetic-mod",
            "--lesson",
            "1",
            "--writer",
            "agy",
            "--repo-root",
            str(tmp_path),
        ]
    )
    assert code == 1

    captured = capsys.readouterr()
    assert "Preflight FAILED" in captured.err

    # Check gap report file written atomically with mode 0o644
    gap_report = tree["state_dir"] / "synthetic-mod" / "lesson-1.gaps.yaml"
    assert gap_report.is_file()
    assert stat.S_IMODE(gap_report.stat().st_mode) == 0o644
    content = yaml.safe_load(gap_report.read_text(encoding="utf-8"))
    assert content["status"] == "evidence_gap"


def test_cli_write_refuses_cited_pending_form_before_prompt_render(tmp_path, capsys):
    tree = _build_synthetic_tree(tmp_path)
    words_path = tree["words"]
    words_data = yaml.safe_load(words_path.read_text(encoding="utf-8"))
    cited_form = words_data["words"][0]["forms"][0]
    del cited_form["stressed"]
    cited_form["stress_source"] = "pending"
    lock.write(words_path, lock.yaml_bytes(words_data))
    lesson_lock.write_lesson_lock("a1", "synthetic-mod", repo_root=tmp_path)

    code = main(["write", "a1", "synthetic-mod", "--lesson", "1", "--writer", "agy", "--repo-root", str(tmp_path)])

    assert code == 1
    assert "cited_form_stress_pending" in capsys.readouterr().err
    output_dir = tree["state_dir"] / "synthetic-mod"
    gaps = yaml.safe_load((output_dir / "lesson-1.gaps.yaml").read_text(encoding="utf-8"))["gaps"]
    assert any(gap["need"] == "cited_form_stress_pending" and "'слово'" in gap["detail"] for gap in gaps)
    assert not (output_dir / "lesson-1.prompt.md").exists()


def test_cli_preflight_passes_on_synthetic_tree(tmp_path, capsys):
    """MAJOR C: CLI preflight passes with exit code 0 on a synthetic tree with injected --repo-root."""
    _build_synthetic_tree(tmp_path)
    code = main(["preflight", "a1", "synthetic-mod", "--lesson", "1", "--repo-root", str(tmp_path)])
    assert code == 0
    captured = capsys.readouterr()
    assert "Preflight status: ok" in captured.out
    assert "Homographs detected: 0" in captured.out


def _synthetic_draft_yaml() -> str:
    """A valid writer reply for synthetic-mod lesson 1."""
    my_draft = copy.deepcopy(load_fixture("a1")[0])
    my_draft["lesson"]["module"] = "a1/synthetic-mod"
    my_draft["lesson"]["n"] = 1
    my_draft["activities"] = [a for a in my_draft["activities"] if a["id"] == "a1"]
    my_draft["steps"][0]["blocks"] = [
        b for b in my_draft["steps"][0]["blocks"] if not (b.get("kind") == "activity" and b.get("ref") != "a1")
    ]
    my_draft["consolidation"] = {"lead_in": "The larger practice block.", "activities": []}
    return yaml.safe_dump(my_draft, allow_unicode=True)


_INPUT_FILES = {"plan_sha256": "plan", "pack_lock": "pack", "words_lock": "words"}


@pytest.mark.parametrize("effort", [None, "low", "medium", "high", "xhigh"])
def test_cli_write_reaches_fake_seat_synthetic_tree(tmp_path, capsys, effort):
    """MAJOR C: CLI write reaches the fake seat on a synthetic tree where preflight passes."""
    paths = _build_synthetic_tree(tmp_path)
    draft_yaml = _synthetic_draft_yaml()

    fake_seat = tmp_path / "fake_seat.py"
    fake_seat.write_text(
        f"""
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--task-id", required=True)
parser.add_argument("--prompt-file", required=True)
parser.add_argument("--result-file", required=True)
parser.add_argument("--effort", default=None)
args = parser.parse_args()
assert args.effort == {effort!r}

result_path = Path(args.result_file)
result_path.parent.mkdir(parents=True, exist_ok=True)
result_path.write_text('''```yaml
{draft_yaml}
```''', encoding="utf-8")
""",
        encoding="utf-8",
    )

    code = main(
        [
            "write",
            "a1",
            "synthetic-mod",
            "--lesson",
            "1",
            "--writer",
            "agy",
            "--fake-seat",
            str(fake_seat),
            "--repo-root",
            str(tmp_path),
            *(["--writer-effort", effort] if effort else []),
        ]
    )
    assert code == 0
    captured = capsys.readouterr()
    assert "Writer call succeeded for a1/synthetic-mod lesson 1 (seat: agy)" in captured.out

    draft_file = paths["state_dir"] / "synthetic-mod" / "lesson-1.draft.yaml"
    assert draft_file.is_file()
    meta = yaml.safe_load(draft_file.with_name("lesson-1.writer.yaml").read_text())
    assert meta["effort"] == "unknown"
    # The CLI keys the task ID on the same complete input snapshot as the module build (#8425).
    inputs = writer_inputs(
        {key: hashlib.sha256(paths[name].read_bytes()).hexdigest() for key, name in _INPUT_FILES.items()},
        style_card_info("a1")[2],
        meta["prompt_sha256"],
    )
    assert meta["task_id"] == writer_task_id("a1", "synthetic-mod", 1, 1, effort, inputs)


@pytest.mark.parametrize("module_first", [True, False])
def test_module_build_and_cli_write_share_one_task_id(tmp_path, module_first):
    """Both entry points share one ID; a fake harness refusing that ID must not spend writer budget."""
    _build_synthetic_tree(tmp_path)
    cards = tmp_path / "docs/style-cards"
    cards.mkdir(parents=True)
    for name in ("a1.md", "a1.sha256"):
        (cards / name).write_bytes((REPO_ROOT / "docs/style-cards" / name).read_bytes())
    executions = tmp_path / "executions.log"
    reply = f"```yaml\n{_synthetic_draft_yaml()}```"
    fake_seat = tmp_path / "fake_seat.py"
    fake_seat.write_text(
        f"""
import argparse
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--task-id", required=True)
parser.add_argument("--prompt-file", required=True)
parser.add_argument("--result-file", required=True)
parser.add_argument("--effort", default=None)
args = parser.parse_args()
result = Path(args.result_file)
# Mirror delegate.py: a task ID that already has a result is never run again.
if result.exists():
    sys.exit(f"task_id {{args.task_id!r}} is already done")
with Path({str(executions)!r}).open("a", encoding="utf-8") as log:
    log.write(args.task_id + "\\n")
result.write_text({reply!r}, encoding="utf-8")
""",
        encoding="utf-8",
    )

    def module_build():
        return build_module(
            "a1",
            "synthetic-mod",
            repo_root=tmp_path,
            lesson_n=1,
            writer_seat="agy:fake-model",
            writer_dispatch=partial(dispatch_writer, effort="high", fake_seat=fake_seat),
            runner=lambda *a, **kw: {"passed": True, "manifest_sha256": "a" * 64},
        )

    def cli_write():
        args = ["write", "a1", "synthetic-mod", "--lesson", "1", "--writer", "agy", "--writer-effort", "high"]
        return main([*args, "--fake-seat", str(fake_seat), "--repo-root", str(tmp_path)])

    if module_first:
        assert module_build()["lessons"][0]["passed"]
        with pytest.raises(WriterCallError, match="already done") as refused:
            cli_write()
        refusal = str(refused.value)
    else:
        assert cli_write() == 0
        stopped = module_build()["lessons"][0]
        assert (stopped["passed"], stopped["layer"]) == (False, "engine")
        assert stopped["regenerations"] == 0
        assert stopped["terminal_layer"] is None
        state = tmp_path / "curriculum/l2-uk-en/evidence/a1/_state/synthetic-mod"
        harness = yaml.safe_load((state / "lesson-1.writer-harness.yaml").read_text())
        assert harness["layer"] == "harness"
        assert len(harness["failures"]) == 1
        refusal = stopped["reason"]
    # Exactly one paid writer execution, and the refused dispatch named that same task ID.
    (task_id,) = executions.read_text(encoding="utf-8").split()
    assert re.fullmatch(r"write-a1-synthetic-mod-1-1-[0-9a-f]{10}-high", task_id)
    assert repr(task_id) in refusal


def test_cli_recap_render_prompt_and_write(tmp_path, capsys):
    """MAJOR B: Recap lesson selects recap prompt template and loads built lessons in both render-prompt and write."""
    paths = _build_synthetic_tree(tmp_path)
    state_dir = paths["state_dir"] / "synthetic-mod"
    state_dir.mkdir(parents=True, exist_ok=True)

    # Settlement 11 requires the real built page, passing gates, and a current manifest.
    page = tmp_path / "site/src/content/docs/a1/synthetic-mod/1.mdx"
    page.parent.mkdir(parents=True)
    page.write_text("# Built lesson 1\n\nReal recap source.\n", encoding="utf-8")
    (state_dir / "lesson-1.gates.yaml").write_text("passed: true\n", encoding="utf-8")
    manifest = state_dir / "lesson-1.manifest.yaml"
    manifest.write_text(
        yaml.safe_dump({"inputs": {"lesson": {"sha256": hashlib.sha256(page.read_bytes()).hexdigest()}}}),
        encoding="utf-8",
    )
    (state_dir / "lesson-1.manifest.sha256").write_text(
        hashlib.sha256(manifest.read_bytes()).hexdigest() + "\n", encoding="ascii"
    )

    # 1. render-prompt on lesson 2 (which is kind: recap in plan)
    output_prompt = tmp_path / "recap_prompt.md"
    code = main(
        [
            "render-prompt",
            "a1",
            "synthetic-mod",
            "--lesson",
            "2",
            "-o",
            str(output_prompt),
            "--repo-root",
            str(tmp_path),
        ]
    )
    assert code == 0
    assert output_prompt.is_file()
    prompt_text = output_prompt.read_text(encoding="utf-8")
    assert "Built lesson 1" in prompt_text

    # 2. write on lesson 2 (kind: recap) reaches fake seat with recap prompt rendered
    valid_draft_template, _ = load_fixture("a1")
    recap_draft = copy.deepcopy(valid_draft_template)
    recap_draft["lesson"]["module"] = "a1/synthetic-mod"
    recap_draft["lesson"]["n"] = 2
    recap_draft["activities"] = [a for a in recap_draft["activities"] if a["id"] == "a1"]
    recap_draft["steps"][0]["blocks"] = [
        b for b in recap_draft["steps"][0]["blocks"] if not (b.get("kind") == "activity" and b.get("ref") != "a1")
    ]
    recap_draft["consolidation"] = {"lead_in": "The larger practice block.", "activities": []}
    recap_draft_yaml = yaml.safe_dump(recap_draft, allow_unicode=True)

    fake_seat = tmp_path / "fake_seat_recap.py"
    fake_seat.write_text(
        f"""
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--task-id", required=True)
parser.add_argument("--prompt-file", required=True)
parser.add_argument("--result-file", required=True)
args = parser.parse_args()

result_path = Path(args.result_file)
result_path.parent.mkdir(parents=True, exist_ok=True)
result_path.write_text('''```yaml
{recap_draft_yaml}
```''', encoding="utf-8")
""",
        encoding="utf-8",
    )

    code_write = main(
        [
            "write",
            "a1",
            "synthetic-mod",
            "--lesson",
            "2",
            "--writer",
            "agy",
            "--fake-seat",
            str(fake_seat),
            "--repo-root",
            str(tmp_path),
        ]
    )
    assert code_write == 0
    assert (state_dir / "lesson-2.draft.yaml").is_file()


@pytest.mark.parametrize("effort", [None, "low", "medium", "high", "xhigh"])
def test_cli_build_writer_effort(tmp_path, effort):
    from scripts.build.fresh import cli

    def build(level, slug, **kwargs):
        if effort is None:
            assert "writer_dispatch" not in kwargs
        else:
            kwargs["writer_dispatch"](writer="codex")
        return {"lessons": [], "complete": False}

    with (
        patch("scripts.build.fresh.module.build_module", side_effect=build),
        patch.object(cli, "dispatch_writer") as writer,
    ):
        assert (
            main(
                [
                    "build",
                    "a1",
                    "fixture-module",
                    "--lesson",
                    "1",
                    "--writer-seat",
                    "codex:gpt-6.1-sol",
                    "--repo-root",
                    str(tmp_path),
                    *(["--writer-effort", effort] if effort else []),
                ]
            )
            == 1
        )
        if effort is None:
            writer.assert_not_called()
        else:
            writer.assert_called_once_with(writer="codex", effort=effort)


@pytest.mark.parametrize("command,seat", [("write", ["--writer", "codex"]), ("build", [])])
def test_cli_rejects_invalid_writer_effort(command, seat):
    with pytest.raises(SystemExit, match="2"):
        _build_parser().parse_args([command, "a1", "fixture-module", "--lesson", "1", *seat, "--writer-effort", "max"])


def test_cli_recap_flag_disagreement_fails(tmp_path, capsys):
    """MAJOR B: --recap flag that disagrees with plan lesson kind fails."""
    _build_synthetic_tree(tmp_path)

    # Lesson 1 is teach, but --recap is asserted
    code = main(
        [
            "render-prompt",
            "a1",
            "synthetic-mod",
            "--lesson",
            "1",
            "--recap",
            "--repo-root",
            str(tmp_path),
        ]
    )
    assert code == 1
    captured = capsys.readouterr()
    assert "disagrees with plan lesson kind" in captured.err

    # Lesson 2 is recap, but --no-recap is asserted
    code2 = main(
        [
            "write",
            "a1",
            "synthetic-mod",
            "--lesson",
            "2",
            "--no-recap",
            "--writer",
            "agy",
            "--repo-root",
            str(tmp_path),
        ]
    )
    assert code2 == 1
    captured2 = capsys.readouterr()
    assert "disagrees with plan lesson kind" in captured2.err


@pytest.mark.parametrize("slug", ["../../plans/x", "nested/module", "/tmp/absolute"])
@pytest.mark.parametrize(
    "command,extra",
    [
        ("render-prompt", ["--lesson", "1"]),
        ("preflight", ["--lesson", "1"]),
        ("write", ["--lesson", "1", "--writer", "agy"]),
        ("assemble", ["--lesson", "1"]),
        ("build", ["--module"]),
        ("closure", []),
    ],
)
def test_cli_rejects_invalid_slug_before_read(tmp_path, capsys, slug, command, extra):
    with patch("scripts.build.fresh.cli._load_lesson_data", side_effect=AssertionError("read attempted")):
        assert main([command, "a1", slug, *extra, "--repo-root", str(tmp_path)]) == 1
    assert "invalid_slug" in capsys.readouterr().err


def test_cli_rejects_symlinked_level_before_read(tmp_path, capsys):
    lesson_plans = tmp_path / "curriculum/l2-uk-en/lesson-plans"
    forbidden = tmp_path / "curriculum/l2-uk-en/plans"
    lesson_plans.mkdir(parents=True)
    forbidden.mkdir(parents=True)
    (lesson_plans / "a1").symlink_to(forbidden, target_is_directory=True)
    with patch("scripts.build.fresh.cli._load_lesson_data", side_effect=AssertionError("read attempted")):
        assert main(["render-prompt", "a1", "safe-slug", "--lesson", "1", "--repo-root", str(tmp_path)]) == 1
    assert "path_outside_allowed_root" in capsys.readouterr().err


def test_path_guard_rejects_symlinked_sidecar_and_schema(tmp_path):
    forbidden = tmp_path / "curriculum/l2-uk-en/plans"
    forbidden.mkdir(parents=True)
    target = forbidden / "secret.yaml"
    target.write_text("forbidden", encoding="utf-8")
    evidence = tmp_path / "curriculum/l2-uk-en/evidence/a1"
    evidence.mkdir(parents=True)
    (evidence / "safe-slug.yaml.lock").symlink_to(target)
    with pytest.raises(ValueError, match="path_outside_allowed_root"):
        checked_path(tmp_path, "curriculum/l2-uk-en/evidence/a1/safe-slug.yaml.lock", "curriculum/l2-uk-en/evidence")
    schemas = tmp_path / "schemas"
    schemas.mkdir()
    (schemas / "fresh-lesson-gates-v1.schema.json").symlink_to(target)
    with pytest.raises(ValueError, match="path_outside_allowed_root"):
        checked_path(tmp_path, "schemas/fresh-lesson-gates-v1.schema.json", "schemas")


@pytest.mark.parametrize("sidecar_name", ["pack", "lesson_lock"])
def test_cli_rejects_symlinked_sidecar_before_read(tmp_path, capsys, sidecar_name):
    tree = _build_synthetic_tree(tmp_path)
    forbidden = tmp_path / "curriculum/l2-uk-en/plans"
    forbidden.mkdir(parents=True)
    secret = forbidden / "private.lock"
    secret.write_text("private", encoding="utf-8")
    source = tree["pack"] if sidecar_name == "pack" else tree["state_dir"] / "synthetic-mod/lessons.lock.yaml"
    sidecar = Path(f"{source}.lock")
    sidecar.unlink()
    sidecar.symlink_to(secret)
    with patch("scripts.build.fresh.cli._load_lesson_data", side_effect=AssertionError("read attempted")):
        assert main(["render-prompt", "a1", "synthetic-mod", "--lesson", "1", "--repo-root", str(tmp_path)]) == 1
    assert "path_outside_allowed_root" in capsys.readouterr().err


def test_cli_rejects_symlinked_draft_before_assemble(tmp_path, capsys):
    state = tmp_path / "curriculum/l2-uk-en/evidence/a1/_state/safe-slug"
    state.mkdir(parents=True)
    forbidden = tmp_path / "curriculum/l2-uk-en/plans"
    forbidden.mkdir(parents=True)
    target = forbidden / "secret.yaml"
    target.write_text("private", encoding="utf-8")
    (state / "lesson-1.draft.yaml").symlink_to(target)
    with patch("scripts.build.fresh.assemble.assemble_lesson", side_effect=AssertionError("read attempted")):
        assert main(["assemble", "a1", "safe-slug", "--lesson", "1", "--repo-root", str(tmp_path)]) == 1
    assert "path_outside_allowed_root" in capsys.readouterr().err


# --- build --module refuses to complete on a stale module verdict (#8774 r5) -----------------------------------


def test_stale_module_verdict_problems_is_empty_before_any_review(tmp_path):
    """A module never reviewed has no module-verdict.yaml yet: that is not staleness."""
    from scripts.build.fresh.cli import _stale_module_verdict_problems

    assert _stale_module_verdict_problems("a1", "fixture-module", repo_root=tmp_path) == []


def _fake_complete_module_report(level, slug, *, repo_root, lesson_n, writer_seat, question_seat):
    return {"level": level, "slug": slug, "complete": True, "lessons": []}


def test_build_module_completion_refuses_a_stale_module_verdict(tmp_path, capsys):
    from scripts.build.fresh import cli

    with (
        patch("scripts.build.fresh.module.build_module", side_effect=_fake_complete_module_report),
        patch.object(
            cli, "_stale_module_verdict_problems", return_value=["the file disagrees with a fresh recomputation"]
        ),
    ):
        assert main(["build", "a1", "fixture-module", "--module", "--repo-root", str(tmp_path)]) == 1
    assert "module-verdict.yaml is stale" in capsys.readouterr().err


def test_build_module_completion_passes_when_the_verdict_check_finds_nothing(tmp_path, capsys):
    from scripts.build.fresh import cli

    with (
        patch("scripts.build.fresh.module.build_module", side_effect=_fake_complete_module_report),
        patch.object(cli, "_stale_module_verdict_problems", return_value=[]),
    ):
        assert main(["build", "a1", "fixture-module", "--module", "--repo-root", str(tmp_path)]) == 0


def test_writer_echo_is_the_learner_state_identity_the_reviewer_recomputes(tmp_path):
    """#9182: render-prompt echoes the learner_state_sha256 the manifest records and the reviewer recomputes."""
    paths = _build_synthetic_tree(tmp_path)
    output_prompt = tmp_path / "rendered_prompt.md"
    argv = ["render-prompt", "a1", "synthetic-mod", "--lesson", "1", "-o", str(output_prompt)]
    assert main([*argv, "--repo-root", str(tmp_path)]) == 0
    echoed = re.search(r'learner_state_sha256: "([0-9a-f]{64})"', output_prompt.read_text(encoding="utf-8"))[1]

    # The manifest writer's path: the same planned state, materialized as YAML, its identity recorded.
    state = planned_state(
        "a1", 1, 1, allow_missing_prior=True, plans_dir=paths["plan"].parent, evidence_dir=paths["words"].parent
    )
    state_path = paths["state_dir"] / "synthetic-mod" / "lesson-1.learner-state.yaml"
    manifest = {
        "kind": "module",
        "inputs": {"learner_state": materialize_learner_state(state_path, learner_state_document(state), tmp_path)},
        "learner_state": {"sha256": learner_state_sha256(state), "source": "planned_state"},
    }
    # The reviewer's path: re-read the pinned YAML and recompute the identity (refuses a mismatch with the record).
    reviewed = _learner_state_context(ManifestReader(manifest, tmp_path), manifest)["learner_state_sha256"]

    assert echoed == reviewed == manifest["learner_state"]["sha256"]
    assert echoed != hashlib.sha256(lock.yaml_bytes(state.to_dict())).hexdigest()  # not the YAML-bytes hash


@pytest.mark.parametrize("caller", ["render-prompt", "write", "build_module"])
@pytest.mark.parametrize("lesson_n", [1, 2])
def test_a1_reference_all_production_callers(tmp_path, monkeypatch, caller, lesson_n):
    paths = _build_synthetic_tree(tmp_path)
    source = tmp_path / "curriculum/l2-uk-en/a1-v1/synthetic-mod/module.md"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"June reference: {{ literal }} TODO: value: None W-999 Lesson 99\n````\n")
    # A lesson slug also has an archive; it must never be selected.
    other = source.parent.parent / f"lesson-{lesson_n}" / "module.md"
    other.parent.mkdir()
    other.write_text("WRONG LESSON SLUG")
    cards = tmp_path / "docs/style-cards"
    cards.mkdir(parents=True)
    (cards / "a1.md").write_bytes((REPO_ROOT / "docs/style-cards/a1.md").read_bytes())
    state_dir = paths["state_dir"] / "synthetic-mod"
    state_dir.mkdir(parents=True, exist_ok=True)
    if lesson_n == 2:
        page = tmp_path / "site/src/content/docs/a1/synthetic-mod/1.mdx"
        page.parent.mkdir(parents=True)
        page.write_text("# Built lesson 1\n")
        (state_dir / "lesson-1.gates.yaml").write_text("passed: true\n")
        manifest_path = state_dir / "lesson-1.manifest.yaml"
        manifest_path.write_text(yaml.safe_dump({"inputs": {"lesson": {"sha256": hashlib.sha256(page.read_bytes()).hexdigest()}}}))
        manifest_path.with_suffix(".sha256").write_text(hashlib.sha256(manifest_path.read_bytes()).hexdigest() + "\n")
    captured = []

    def dispatch(**kwargs):
        captured.append(kwargs["prompt_file"].read_text())
        assert kwargs["preflight_result"].passed
        assert kwargs["prompt_sha256"] == hashlib.sha256(captured[-1].encode()).hexdigest()
        return {"draft_file": "test prompt boundary"}

    monkeypatch.setattr("scripts.build.fresh.cli.dispatch_writer", dispatch)
    output = tmp_path / "rendered.md"
    if caller == "build_module":
        result = build_module("a1", "synthetic-mod", repo_root=tmp_path, lesson_n=lesson_n)
        assert result["lessons"][0]["reason"] == "writer_seat_required", result
        output = state_dir / f"lesson-{lesson_n}.prompt.md"
    else:
        args = [caller, "a1", "synthetic-mod", "--lesson", str(lesson_n), "--repo-root", str(tmp_path)]
        args += ["-o", str(output)] if caller == "render-prompt" else ["--writer", "codex"]
        assert main(args) == 0
        if caller == "write":
            output = state_dir / f"lesson-{lesson_n}.prompt.md"
            assert captured == [output.read_text()]
    prompt = output.read_text()
    assert "WRONG LESSON SLUG" not in prompt
    assert "Source: `curriculum/l2-uk-en/a1-v1/synthetic-mod/module.md`" in prompt
    assert hashlib.sha256(source.read_bytes()).hexdigest() in prompt
    assert source.read_text() in prompt
    assert prompt.endswith("<!-- END A1_REFERENCE -->\n")


@pytest.mark.parametrize("field,value", [("level", "a2"), ("slug", "wrong-module")])
def test_a1_reference_refuses_wrong_plan_identity(tmp_path, monkeypatch, field, value):
    from scripts.build.fresh.cli import _load_lesson_data
    from scripts.curriculum.validate.loader import load_plan

    paths = _build_synthetic_tree(tmp_path)
    plan = load_plan(paths["plan"])
    plan[field] = value
    monkeypatch.setattr("scripts.build.fresh.cli.load_plan", lambda _: plan)
    with pytest.raises(ValueError, match="plan_module_identity_mismatch"):
        _load_lesson_data("a1", "synthetic-mod", 1, repo_root=tmp_path)
