"""#9389: parse one mapping while binding the entire parent-saved result.

The two fixtures contain only the YAML from the real AGY returns; all prose
wrappers here are synthetic. Integration cases rebind their manifest/hash to
temporary inputs, without replaying or modifying production review state.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import yaml

from scripts.review import record
from scripts.review.validate import codes
from scripts.review.validate.validate import ReviewReturnError, _peek_kind, extract_review_yaml
from tests.build.test_fresh_plan_review import fake_verify, make_manifest
from tests.helpers.plan_review_world import build_env
from tests.review.test_plan_review_validator import Case
from tests.review.test_record import World, _attestable_placeholder_return, _bound, finding

FIXTURES = Path(__file__).parent / "fixtures" / "fenced_returns"
REAL_RETURNS = ("plan-review-a1-p2-agy-r7", "plan-review-a1-p3-agy-r2")


def fenced(data: bytes, info: bytes = b"yaml") -> bytes:
    return b"Synthetic introduction.\n```" + info + b"\n" + data + b"```\nSynthetic report.\n"


@pytest.mark.parametrize("name", REAL_RETURNS)
@pytest.mark.parametrize("info", [b"yaml", b"yml"])
def test_real_yaml_parts_extract_without_rewriting(name, info):
    data = (FIXTURES / f"{name}.yaml").read_bytes()
    assert extract_review_yaml(data) == data
    assert extract_review_yaml(fenced(data, info)) == data


def test_bare_mapping_with_a_fence_in_a_scalar_is_unchanged():
    data = b"kind: plan\nnotes: |\n  ```yaml\n  example: true\n  ```\n"
    assert extract_review_yaml(data) == data


@pytest.mark.parametrize("indent", [1, 2, 3])
def test_block_scalar_closing_fence_refuses_truncated_mapping(indent):
    padding = b" " * indent
    data = b"kind: plan\nnotes: |\n" + padding + b"before\n" + padding + b"```\n" + padding + b"after\nfindings: []\n"
    assert isinstance(yaml.safe_load(data), dict)
    with pytest.raises(ReviewReturnError) as raised:
        extract_review_yaml(fenced(data))
    assert raised.value.code == codes.REVIEW_YAML_FENCE_NOT_MAPPING


def test_block_scalar_four_space_fence_keeps_whole_mapping():
    data = b"kind: plan\nnotes: |\n    before\n    ```\n    after\nfindings: []\n"
    assert extract_review_yaml(fenced(data)) == data


@pytest.mark.parametrize("wrapped", [False, True], ids=["bare-load", "fence-load"])
def test_invalid_date_has_typed_refusal(wrapped):
    data = b"kind: plan\ndate: 2026-13-45\n"
    with pytest.raises(ReviewReturnError) as raised:
        extract_review_yaml(fenced(data) if wrapped else data)
    expected = codes.REVIEW_YAML_FENCE_NOT_MAPPING if wrapped else codes.REVIEW_YAML_FENCE_MISSING
    assert raised.value.code == expected


def test_recorder_docstring_keeps_then_with_numbered_steps():
    assert "then:\n\n1. reserves" in record.__doc__


@pytest.mark.parametrize(
    "data,code",
    [
        (b"Synthetic report only.\n", codes.REVIEW_YAML_FENCE_MISSING),
        (b"- a\n- b\n", codes.REVIEW_YAML_FENCE_MISSING),
        (fenced(b"kind: plan\n") + fenced(b"kind: lesson\n"), codes.REVIEW_YAML_FENCE_MULTIPLE),
        (fenced(b"kind: plan\n") + b"Later prose:\n```yml\nextra: true\n```\n", codes.REVIEW_YAML_FENCE_MULTIPLE),
        (fenced(b"- a\n- b\n"), codes.REVIEW_YAML_FENCE_NOT_MAPPING),
        (fenced(b"plain scalar\n"), codes.REVIEW_YAML_FENCE_NOT_MAPPING),
        (fenced(b""), codes.REVIEW_YAML_FENCE_NOT_MAPPING),
        (fenced(b"kind: [\n"), codes.REVIEW_YAML_FENCE_NOT_MAPPING),
        (fenced(b"kind: plan\n---\nkind: lesson\n"), codes.REVIEW_YAML_FENCE_NOT_MAPPING),
        (b"```yaml\nkind: plan\n", codes.REVIEW_YAML_FENCE_NOT_MAPPING),
        (b"```yaml\nkind: plan\n```\n```yml\n", codes.REVIEW_YAML_FENCE_MULTIPLE),
        (fenced(b"kind: plan\n", b"yaml extra"), codes.REVIEW_YAML_FENCE_MISSING),
        (fenced(b"kind: plan\n", b"YAML"), codes.REVIEW_YAML_FENCE_MISSING),
        (b"````text\n```yaml\nkind: plan\n```\n````\n", codes.REVIEW_YAML_FENCE_MISSING),
        (b"```yaml\n\xff\n```\n", codes.REVIEW_YAML_FENCE_NOT_MAPPING),
    ],
)
def test_unusable_returns_have_typed_codes(data, code):
    with pytest.raises(ReviewReturnError) as raised:
        extract_review_yaml(data)
    assert raised.value.code == code


@pytest.mark.parametrize(
    "data",
    [
        b"Before\n~~~yml\nkind: plan\n~~~\nAfter\n",
        b"Before\n````yaml\nkind: plan\n`````\nAfter\n",
        b"Before\r\n```yaml\r\nkind: plan\r\n```\r\nAfter\r\n",
    ],
)
def test_matching_fence_markers_and_line_endings(data):
    expected = b"kind: plan\r\n" if b"\r\n" in data else b"kind: plan\n"
    assert extract_review_yaml(data) == expected


@pytest.fixture
def plan_case(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("scripts.build.fresh.plan_manifest.verify_pack_strict", fake_verify())
    env = build_env(tmp_path / "tree")
    digest = make_manifest(env, capsys)
    out = tmp_path / "out"
    out.mkdir()
    return Case(env, digest, out)


@pytest.mark.reads_content
@pytest.mark.parametrize("name", REAL_RETURNS)
@pytest.mark.parametrize("wrapped", [False, True])
def test_real_plan_shapes_record_from_bound_saved_result(plan_case, name, wrapped, tmp_path):
    case = plan_case
    review = yaml.safe_load((FIXTURES / f"{name}.yaml").read_bytes())
    review["attempt"]["manifest_sha256"] = case.digest
    review["reviewer"]["prompt_sha256"] = "a" * 64
    bare = yaml.safe_dump(review, sort_keys=False).encode()
    case.review.write_bytes(bare)
    bare_code, bare_payload = case.validate()
    assert bare_code == 0, bare_payload
    case.review.write_bytes(fenced(bare) if wrapped else bare)
    assert _peek_kind(case.review) == "plan"
    assert case.validate() == (bare_code, bare_payload)

    tasks = tmp_path / "tasks"
    tasks.mkdir()
    saved_result = tasks / "agy-review.result"
    raw = case.review.read_bytes()
    saved_result.write_bytes(raw)
    (tasks / "agy-review.json").write_text(
        json.dumps(
            {
                "agent": "agy",
                "model": "gemini-3.8-flash-high",
                "status": "done",
                "review_attempt": {
                    key: review["attempt"][key] for key in ("review_id", "attempt_id", "manifest_sha256")
                },
                "result_file": str(saved_result),
                "result_sha256": hashlib.sha256(raw).hexdigest(),
            }
        )
    )
    outcome = record.record_return(
        saved_result,
        manifest_path=case.manifest,
        ledger_path=case.ledger,
        task_id="agy-review",
        repo_root=case.env.root,
        db_path=tmp_path / "plan.sqlite",
        tasks_dir=tasks,
    )
    assert outcome.accepted and outcome.verdict == bare_payload["verdict"] == "APPROVE", outcome.rejection_codes
    assert (case.env.root / outcome.saved_return).read_bytes() == bare
    assert saved_result.read_bytes() == raw


@pytest.mark.reads_content
@pytest.mark.parametrize(
    "data,code",
    [
        (b"Synthetic report only.\n", codes.REVIEW_YAML_FENCE_MISSING),
        (fenced(b"kind: plan\n") + fenced(b"kind: plan\n"), codes.REVIEW_YAML_FENCE_MULTIPLE),
        (fenced(b"[a, b]\n"), codes.REVIEW_YAML_FENCE_NOT_MAPPING),
        (b"kind: plan\ndate: 2026-13-45\n", codes.REVIEW_YAML_FENCE_MISSING),
        (fenced(b"kind: plan\ndate: 2026-13-45\n"), codes.REVIEW_YAML_FENCE_NOT_MAPPING),
        (
            fenced(b"kind: plan\nnotes: |\n  before\n  ```\n  after\nfindings: []\n"),
            codes.REVIEW_YAML_FENCE_NOT_MAPPING,
        ),
    ],
)
def test_validator_and_recorder_refuse_the_same_shape(plan_case, data, code, tmp_path):
    case = plan_case
    case.review.write_bytes(data)
    assert _peek_kind(case.review) is None
    _, payload = case.validate("--lesson", str(tmp_path / "unused.yaml"))
    assert code in {item["code"] for item in payload["rejections"]}
    with pytest.raises(record.RecordError) as raised:
        record.record_return(
            case.review,
            manifest_path=case.manifest,
            ledger_path=case.ledger,
            task_id="unused",
            repo_root=case.env.root,
            db_path=tmp_path / "plan.sqlite",
            review_id="review",
            attempt_id="attempt",
        )
    assert raised.value.code == code
    assert not (tmp_path / "plan.sqlite").exists()
    assert not list(case.env.state_dir.glob("plan-review.attempt.yaml"))


@pytest.fixture
def world(tmp_path, monkeypatch, review_world_template):
    return World(tmp_path, monkeypatch, seed=review_world_template)


@pytest.mark.reads_content
def test_fenced_placeholder_attests_only_the_extracted_mapping(world):
    made = _attestable_placeholder_return(world)
    bare = made["review"].read_bytes()
    made["review"].write_bytes(fenced(bare))
    world.capture_result(made, "review-attested")
    raw_result = (world.tasks_dir / "review-attested.result").read_bytes()
    outcome = world.record(made, task_id="review-attested")
    assert outcome.accepted, outcome.rejection_codes
    saved = (world.root / outcome.saved_return).read_bytes()
    assert saved == record.attest_prompt_sha256(bare, made["sent"])
    assert (world.tasks_dir / "review-attested.result").read_bytes() == raw_result
    assert world.db_rows("attempts")[0]["return_sha256"] == hashlib.sha256(saved).hexdigest()


@pytest.mark.reads_content
@pytest.mark.parametrize("edit", ["outside-prose", "hand-extracted"])
@pytest.mark.parametrize("placeholder", [False, True])
def test_fenced_binding_still_covers_whole_saved_result(world, edit, placeholder):
    made = _attestable_placeholder_return(world)
    bare = made["review"].read_bytes()
    if not placeholder:
        bare = record.attest_prompt_sha256(bare, made["sent"])
    made["review"].write_bytes(fenced(bare))
    world.capture_result(made, "review-attested")
    made["review"].write_bytes(bare if edit == "hand-extracted" else fenced(bare) + b"Extra prose.\n")
    with pytest.raises(record.RecordError) as raised:
        world.record(made, task_id="review-attested")
    assert raised.value.code == record.REVIEW_RETURN_TASK_MISMATCH
    assert not world.db.exists()
    assert not list(world.state_dir.glob(f"*{made['attempt_id']}*"))


@pytest.mark.reads_content
def test_fenced_lesson_revise_matches_bare_verdict(world):
    bare = world.make_return(2, [finding(severity="MAJOR")])
    before = world.record(bare)
    made = world.make_return(2, [finding(severity="MAJOR")])
    raw_mapping = made["review"].read_bytes()
    made["review"].write_bytes(fenced(raw_mapping))
    world.task("review-fenced", "claude", "claude-sonnet-5", review_attempt=_bound(world, made))
    outcome = world.record(made, task_id="review-fenced")
    assert before.accepted and outcome.accepted, outcome.rejection_codes
    assert outcome.verdict == before.verdict == "REVISE"
    assert (world.root / outcome.saved_return).read_bytes() == raw_mapping
