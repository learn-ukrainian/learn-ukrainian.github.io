"""The CLI in a clean-environment subprocess, over a synthetic plan, word store and VESUM."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from resolver_helpers import form, record, stressed

from scripts.curriculum.evidence import lock
from scripts.curriculum.resolver import codes

pytestmark = [pytest.mark.reads_content]

REPO_ROOT = Path(__file__).resolve().parents[3]
LEVEL, SLUG, N = "a1", "synthetic-module", 1


def _records() -> list[dict]:
    return [
        record(1, "бзюк", "noun", [form("бзюк", "noun:inanim:m:v_naz", "бзюк")], "synthetic-one"),
        record(2, "фрямба", "noun", [form("фрямба", "noun:inanim:f:v_naz", stressed("фрямба", 2))], "synthetic-a"),
        record(3, "фрямба", "noun", [form("фрямба", "noun:anim:f:v_naz", stressed("фрямба", 2))], "synthetic-b"),
        record(4, "кветур", "noun", [form("кветур", "noun:inanim:m:v_naz", stressed("кветур", 2))]),
        record(5, "кветур", "noun", [form("кветур", "noun:inanim:m:v_naz", stressed("кветур", 4))]),
        record(6, "Жмурбан", "noun", [form("Жмурбан", "noun:anim:m:v_naz:prop:fname", stressed("Жмурбан", 5))]),
        record(7, "шпрок", "noun", [form("шпрок", "noun:inanim:m:v_naz", "шпрок", source="none")]),
    ]


def _write_yaml(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


@pytest.fixture
def lesson_tree(tmp_path: Path) -> dict[str, Path]:
    plans = tmp_path / f"curriculum/l2-uk-en/lesson-plans/{LEVEL}"
    evidence = tmp_path / f"curriculum/l2-uk-en/evidence/{LEVEL}"
    _write_yaml(
        evidence / "_base.request.yaml",
        {"request_schema": 1, "level": LEVEL, "words": [{"lemma": "шпрок", "pos": "noun", "want": "new"}]},
    )
    store = {
        "evidence_schema": 1,
        "level": LEVEL,
        "built_with": {
            "mcp_commit": "0" * 40,
            "sources_db": "0" * 64,
            "vesum": "0" * 64,
            "trie": "0" * 64,
            "ulif_forms": "pending",
        },
        "words": _records(),
    }
    lock.write(evidence / "_words.yaml", lock.yaml_bytes(store))
    _write_yaml(
        plans / f"{SLUG}.yaml",
        {
            "plan_schema": 2,
            "module": SLUG,
            "level": LEVEL,
            "sequence": 1,
            "slug": SLUG,
            "version": "1",
            "title": "Synthetic module",
            "arc_ref": {"level": LEVEL, "position": 1},
            "lessons": [
                {
                    "n": 1,
                    "slug": "synthetic-l01",
                    "inventory": {
                        "vocabulary": {
                            "core": [
                                {"lemma": "бзюк", "evidence": "W-1"},
                                {"lemma": "кветур", "evidence": "W-4"},
                                {"lemma": "кветур", "evidence": "W-5"},
                            ],
                            "incidental": [
                                {"lemma": "фрямба", "evidence": "W-2"},
                                {"lemma": "фрямба", "evidence": "W-3"},
                            ],
                        }
                    },
                    "dialogue": {"speakers": [{"name": "Жмурбан", "evidence": "W-6"}]},
                }
            ],
        },
    )
    expanded = evidence / f"_state/{SLUG}/lesson-{N}.expanded.yaml"
    units = [
        {
            "tab": "urok",
            "activity": None,
            "item": None,
            "block": 0,
            "role": "dialogue_line",
            "text": "Жмурбан: шпрок бзюк кветур фрямба.",
        },
        {
            "tab": "slovnyk",
            "activity": None,
            "item": None,
            "block": "gloss",
            "role": "gloss_ref",
            "text": "{{gloss:W-2}}",
        },
        {"tab": "vpravy", "activity": "act-1", "item": 0, "block": "options", "role": "item_option", "text": "вурдик"},
    ]
    _write_yaml(expanded, {"lesson": {"level": LEVEL, "slug": SLUG, "n": N}, "units": units})
    return {"plans": plans, "evidence": evidence, "state": expanded.parent, "root": tmp_path}


def _cli(tree: dict[str, Path], synthetic_vesum: Path, *args: str) -> subprocess.CompletedProcess:
    command, *rest = args
    flags = [
        "--plans-dir",
        str(tree["plans"]),
        "--evidence-dir",
        str(tree["evidence"]),
        "--vesum-db",
        str(synthetic_vesum),
    ]
    env = {"PATH": "/usr/bin:/bin", "HOME": str(tree["root"]), "LANG": "C.UTF-8"}
    return subprocess.run(
        [sys.executable, "-m", "scripts.curriculum.resolver", command, LEVEL, SLUG, str(N), *rest, *flags],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_help_lists_every_code():
    result = subprocess.run(
        [sys.executable, "-m", "scripts.curriculum.resolver", "--help"],
        cwd=REPO_ROOT,
        env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"},
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    for code in codes.DESCRIPTIONS:
        assert code in result.stdout


def test_cli_resolve_questions_apply_check(lesson_tree, synthetic_vesum):
    resolved = _cli(lesson_tree, synthetic_vesum, "resolve", "--json")
    assert resolved.returncode == 0, resolved.stderr
    stream = json.loads(resolved.stdout)
    assert stream["counts"] == {
        "resolved": 4,
        "skipped:item_option": 1,
        "stress_certain_identity_open": 1,
        "stress_open": 1,
    }
    speaker = next(t for t in stream["tokens"] if t["token"] == "Жмурбан")
    assert speaker["surface"] == codes.PROPER_NOUN and speaker["selected"]["record"] == "W-6"
    assert "progress: tokens: 7/7" in resolved.stderr

    missing = _cli(lesson_tree, synthetic_vesum, "apply", "--json")
    assert missing.returncode == 1 and json.loads(missing.stdout)["code"] == codes.LOCK_MISMATCH

    dry = _cli(lesson_tree, synthetic_vesum, "questions", "--dry-run")
    assert dry.returncode == 0 and not (lesson_tree["state"] / "lesson-1.questions.yaml").exists()
    emitted = _cli(lesson_tree, synthetic_vesum, "questions", "--json")
    assert emitted.returncode == 0, emitted.stderr
    batch = json.loads(emitted.stdout)
    assert [(q["token"], q["blocking"]) for q in batch["questions"]] == [("кветур", True), ("фрямба", False)]
    questions_path = lesson_tree["state"] / "lesson-1.questions.yaml"
    assert lock.check(questions_path) and oct(questions_path.stat().st_mode & 0o777) == "0o644"

    answers = lesson_tree["root"] / "answers.yaml"
    answers.write_text(yaml.safe_dump({"answers": [{"id": "Q-001", "record": "W-1"}]}), encoding="utf-8")
    rejected = _cli(lesson_tree, synthetic_vesum, "apply", str(answers), "--seat", "agy/synthetic-1", "--json")
    assert rejected.returncode == 1 and json.loads(rejected.stdout)["code"] == codes.INVALID_ANSWER

    answers.write_text(
        yaml.safe_dump({"answers": [{"id": "Q-001", "record": "W-4"}, {"id": "Q-002", "record": "W-3"}]}),
        encoding="utf-8",
    )
    applied = _cli(lesson_tree, synthetic_vesum, "apply", str(answers), "--seat", "agy/synthetic-1")
    assert applied.returncode == 0, applied.stderr
    receipts_path = lesson_tree["state"] / "lesson-1.resolutions.yaml"
    receipts = yaml.safe_load(receipts_path.read_text(encoding="utf-8"))
    provenance = {t["token"]: t["provenance"] for t in receipts["tokens"]}
    assert provenance["кветур"] == "question:agy/synthetic-1:Q-001"
    assert provenance["фрямба"] == "question:agy/synthetic-1:Q-002"
    assert oct(receipts_path.stat().st_mode & 0o777) == "0o644"

    checked = _cli(lesson_tree, synthetic_vesum, "check", "--json")
    assert checked.returncode == 0 and json.loads(checked.stdout)["tokens"] == 7
    receipts_path.write_text(receipts_path.read_text(encoding="utf-8").replace("W-4", "W-5"), encoding="utf-8")
    tampered = _cli(lesson_tree, synthetic_vesum, "check", "--json")
    assert tampered.returncode == 1 and json.loads(tampered.stdout)["code"] == codes.LOCK_MISMATCH


def test_cli_stale_questions_and_token_failures(lesson_tree, synthetic_vesum):
    assert _cli(lesson_tree, synthetic_vesum, "questions").returncode == 0
    expanded = lesson_tree["state"] / "lesson-1.expanded.yaml"
    doc = yaml.safe_load(expanded.read_text(encoding="utf-8"))
    doc["units"][0]["text"] = "шпрок кветур фрямба бзюк."
    _write_yaml(expanded, doc)
    stale = _cli(lesson_tree, synthetic_vesum, "apply", "--json")
    assert stale.returncode == 1 and json.loads(stale.stdout)["code"] == codes.STALE_QUESTIONS

    doc["units"][0]["text"] = "шпрок глорт"
    _write_yaml(expanded, doc)
    failed = _cli(lesson_tree, synthetic_vesum, "resolve")
    assert failed.returncode == 1 and "lemma_outside_state: 'глорт'" in failed.stderr
    assert _cli(lesson_tree, synthetic_vesum, "questions").returncode == 1
