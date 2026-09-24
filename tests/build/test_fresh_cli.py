"""Tests for fresh build engine Part E2 CLI entry, end-to-end loading, and --help standard compliance (#8431 r3)."""

from __future__ import annotations

import argparse
import copy
import hashlib
import stat
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from scripts.build.fresh.cli import _build_parser, main
from scripts.build.fresh.path_guard import checked_path
from scripts.curriculum.evidence import lesson_lock, lock

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


def test_cli_preflight_passes_on_synthetic_tree(tmp_path, capsys):
    """MAJOR C: CLI preflight passes with exit code 0 on a synthetic tree with injected --repo-root."""
    _build_synthetic_tree(tmp_path)
    code = main(["preflight", "a1", "synthetic-mod", "--lesson", "1", "--repo-root", str(tmp_path)])
    assert code == 0
    captured = capsys.readouterr()
    assert "Preflight status: ok" in captured.out
    assert "Homographs detected: 0" in captured.out


def test_cli_write_reaches_fake_seat_synthetic_tree(tmp_path, capsys):
    """MAJOR C: CLI write reaches the fake seat on a synthetic tree where preflight passes."""
    paths = _build_synthetic_tree(tmp_path)
    valid_draft_template = yaml.safe_load(
        (Path(__file__).parent / "fixtures" / "fresh" / "lesson-draft-a1-valid.yaml").read_text(encoding="utf-8")
    )
    my_draft = copy.deepcopy(valid_draft_template)
    my_draft["lesson"]["module"] = "a1/synthetic-mod"
    my_draft["lesson"]["n"] = 1
    my_draft["activities"] = [a for a in my_draft["activities"] if a["id"] == "a1"]
    my_draft["steps"][0]["blocks"] = [
        b for b in my_draft["steps"][0]["blocks"] if not (b.get("kind") == "activity" and b.get("ref") != "a1")
    ]
    my_draft["consolidation"] = {"lead_in": "The larger practice block.", "activities": []}
    draft_yaml = yaml.safe_dump(my_draft, allow_unicode=True)

    fake_seat = tmp_path / "fake_seat.py"
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
        ]
    )
    assert code == 0
    captured = capsys.readouterr()
    assert "Writer call succeeded for a1/synthetic-mod lesson 1 (seat: agy)" in captured.out

    draft_file = paths["state_dir"] / "synthetic-mod" / "lesson-1.draft.yaml"
    assert draft_file.is_file()


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
    manifest.write_text(yaml.safe_dump({"inputs": {"lesson": {"sha256": hashlib.sha256(page.read_bytes()).hexdigest()}}}),
                        encoding="utf-8")
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
    valid_draft_template = yaml.safe_load(
        (Path(__file__).parent / "fixtures" / "fresh" / "lesson-draft-a1-valid.yaml").read_text(encoding="utf-8")
    )
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
        checked_path(tmp_path, "curriculum/l2-uk-en/evidence/a1/safe-slug.yaml.lock",
                     "curriculum/l2-uk-en/evidence")
    schemas = tmp_path / "schemas"
    schemas.mkdir()
    (schemas / "fresh-lesson-gates-v1.schema.json").symlink_to(target)
    with pytest.raises(ValueError, match="path_outside_allowed_root"):
        checked_path(tmp_path, "schemas/fresh-lesson-gates-v1.schema.json", "schemas")


def test_cli_rejects_symlinked_pack_sidecar_before_read(tmp_path, capsys):
    tree = _build_synthetic_tree(tmp_path)
    forbidden = tmp_path / "curriculum/l2-uk-en/plans"
    forbidden.mkdir(parents=True)
    secret = forbidden / "private.lock"
    secret.write_text("private", encoding="utf-8")
    sidecar = Path(f"{tree['pack']}.lock")
    sidecar.unlink()
    sidecar.symlink_to(secret)
    with patch("scripts.build.fresh.cli._load_lesson_data", side_effect=AssertionError("read attempted")):
        assert main(["render-prompt", "a1", "synthetic-mod", "--lesson", "1",
                     "--repo-root", str(tmp_path)]) == 1
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
