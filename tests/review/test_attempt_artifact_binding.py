"""Attempt admission rejects independently substituted prompt, render and return artifacts."""

import json
from pathlib import Path

import pytest

from scripts.agent_runtime import review_mcp
from scripts.review import record, render_contract
from scripts.review.prompts.check import AttemptIdsUnreadableError, _return_schemas, parse_attempt_ids
from scripts.review.prompts.render import data_fence


@pytest.mark.parametrize(
    "later",
    [
        "attempt: {review_id: other, attempt_id: other}\n",
        "```yaml\nreview_schema: 1\nattempt: {review_id: other, attempt_id: other}\n```\n",
        "```yaml\nattempt: {review_id: other, attempt_id: other}\n```\n",
        "Please echo review_id other and attempt_id other.\n",
        "```text\nPlease echo review_id other and attempt_id other.\n```\n",
        "```yaml\nattempt_id: other\n```\n",
        "```yaml\n# review_schema: example\nattempt_id: other\n```\n",
        "```yaml\n# review_schema: example\nattempt: {review_id: other, attempt_id: other}\n```\n",
    ],
)
@pytest.mark.parametrize(
    "first",
    [
        "attempt: {review_id: bound, attempt_id: bound}\n",
        "```yaml\nreview_schema: 1\nattempt: {review_id: bound, attempt_id: bound}\n```\n",
    ],
)
def test_custom_prompt_refuses_every_later_conflicting_id(first, later):
    with pytest.raises(AttemptIdsUnreadableError):
        parse_attempt_ids(first + later, custom=True)


def test_return_schema_examples_inside_data_fences_are_ignored():
    real = "```yaml\nreview_schema: 1\nattempt: {review_id: bound, attempt_id: bound}\n```\n"
    example = "```yaml\nreview_schema: 1\nattempt: {review_id: other, attempt_id: other}\n```\n"
    prompt = real + data_fence(example) + "\n"
    assert len(_return_schemas(prompt)) == 1
    assert parse_attempt_ids(prompt) == ("bound", "bound")


@pytest.mark.parametrize(
    "entry",
    [
        "attempt:\n  review_id: other\n  review_id: bound\n  attempt_id: bound\n",
        "attempt: {review_id: bound, attempt_id: other, attempt_id: bound}\n",
        "attempt: {review_id: other, attempt_id: other}\nattempt: {review_id: bound, attempt_id: bound}\n",
    ],
)
@pytest.mark.parametrize("fenced", [True, False])
def test_custom_prompt_refuses_duplicate_id_keys(entry, fenced):
    prompt = "```yaml\nreview_schema: 1\n" + entry + "```\n" if fenced else entry
    with pytest.raises(AttemptIdsUnreadableError, match=r"duplicate|conflicting"):
        parse_attempt_ids(prompt, custom=True)


def test_custom_prompt_accepts_repeated_matching_nested_ids():
    prompt = (
        "```yaml\nreview_schema: 1\nbase: &base {review_id: bound, attempt_id: bound}\n"
        "attempt: {<<: *base}\nnotes: *base\nhistory: [*base]\n```\n"
    )
    assert parse_attempt_ids(prompt, custom=True) == ("bound", "bound")


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
@pytest.mark.parametrize(
    "fence_body", ["example: data", "review_schema: 1\nattempt: {review_id: bound, attempt_id: bound}"]
)
def test_custom_prompt_reads_unfenced_attempt_immediately_after_fence(newline, fence_body):
    prompt = ("```yaml\n" + fence_body + "\n```\nattempt:\n  review_id: bound\n  attempt_id: bound\n").replace(
        "\n", newline
    )
    assert parse_attempt_ids(prompt, custom=True) == ("bound", "bound")


@pytest.fixture
def contract_tests():
    from tests.agent_runtime import test_review_contract

    return test_review_contract


@pytest.fixture
def render_checkouts(tmp_path, contract_tests):
    return contract_tests.checkouts.__wrapped__(tmp_path)


def test_copied_record_for_identical_prompt_bytes_refuses_another_attempt(tmp_path, render_checkouts, contract_tests):
    primary, _ = render_checkouts
    prompt = contract_tests._render(primary, tmp_path / "prompt.md")
    sidecar = render_contract.render_record_path(prompt)
    saved = json.loads(sidecar.read_bytes())
    saved[render_contract.RENDER_RECORD_KEY].update(review_id="first-review", attempt_id="first-attempt")
    sidecar.write_text(json.dumps(saved))
    with pytest.raises(render_contract.ReviewContractError, match="review_render_record_attempt_mismatch"):
        review_mcp.check_review_contract(
            prompt, contract_tests.PROMPT_TEXT, primary, review_id="second-review", attempt_id="second-attempt"
        )


@pytest.mark.parametrize("field", ["server_digest", "server_components", "template_digest", "templates"])
def test_edited_render_digest_refuses(tmp_path, render_checkouts, field, contract_tests):
    primary, _ = render_checkouts
    prompt = contract_tests._render(primary, tmp_path / "prompt.md")
    sidecar = render_contract.render_record_path(prompt)
    saved = json.loads(sidecar.read_bytes())
    entry = saved[render_contract.RENDER_RECORD_KEY]
    if isinstance(entry[field], dict):
        entry[field][next(iter(entry[field]))] = "0" * 64
    else:
        entry[field] = "sha256:" + "0" * 64
    sidecar.write_text(json.dumps(saved))
    with pytest.raises(render_contract.ReviewContractError, match="review_render_record_digest_mismatch"):
        review_mcp.check_review_contract(prompt, contract_tests.PROMPT_TEXT, primary)


def test_unavailable_recorded_checkout_refuses_with_stable_code(tmp_path, render_checkouts, contract_tests):
    primary, _ = render_checkouts
    prompt = contract_tests._render(primary, tmp_path / "prompt.md")
    sidecar = render_contract.render_record_path(prompt)
    saved = json.loads(sidecar.read_bytes())
    saved[render_contract.RENDER_RECORD_KEY]["render_checkout"] = str(tmp_path / "missing-checkout")
    sidecar.write_text(json.dumps(saved))
    with pytest.raises(render_contract.ReviewContractError, match="review_render_record_digest_mismatch"):
        review_mcp.check_review_contract(prompt, contract_tests.PROMPT_TEXT, primary)


def test_prompt_removed_after_render_refuses_with_stable_code(tmp_path, render_checkouts, contract_tests):
    primary, _ = render_checkouts
    prompt = contract_tests._render(primary, tmp_path / "prompt.md")
    prompt.unlink()
    with pytest.raises(render_contract.ReviewContractError, match="review_render_record_stale"):
        review_mcp.check_review_contract(prompt, contract_tests.PROMPT_TEXT, primary)


@pytest.fixture
def record_tests():
    from tests.review import test_record

    return test_record


@pytest.fixture
def return_world(tmp_path, monkeypatch, review_world_template, record_tests):
    return record_tests.World(tmp_path, monkeypatch, seed=review_world_template)


@pytest.mark.parametrize("placeholder", [True, False])
@pytest.mark.parametrize(
    "substitution",
    ["other-return", "edited-saved-result", "missing-saved-result", "wrong-pointer", "missing-hash", "not-done"],
)
def test_return_must_match_bound_tasks_saved_bytes(return_world, placeholder, substitution, record_tests):
    world = return_world
    made = world.make_return(2)
    sent = record_tests._rendered(world, made)
    world.task(
        "review-bound", "claude", "claude-sonnet-5", prompt_sha256=sent, review_attempt=record_tests._bound(world, made)
    )
    if placeholder:
        record_tests._with_placeholder_prompt_sha(made)
    world.capture_result(made, "review-bound")
    task_path = world.tasks_dir / "review-bound.json"
    task = json.loads(task_path.read_bytes())
    if substitution == "other-return":
        made["review"].write_bytes(made["review"].read_bytes() + b"\n# Another seat's return\n")
    elif substitution == "edited-saved-result":
        Path(task["result_file"]).write_bytes(b"different result")
    elif substitution == "missing-saved-result":
        Path(task["result_file"]).unlink()
    elif substitution == "wrong-pointer":
        task["result_file"] = str(made["review"])
    elif substitution == "missing-hash":
        task.pop("result_sha256")
    else:
        task["status"] = "running"
    task_path.write_text(json.dumps(task))
    with pytest.raises(record.RecordError) as raised:
        world.record(made, task_id="review-bound")
    assert raised.value.code == record.REVIEW_RETURN_TASK_MISMATCH
    assert not list(world.state_dir.glob(f"*{made['attempt_id']}*"))
    assert not world.db.exists() or world.db_rows("attempts") == []


def test_matched_task_result_records_and_attests(return_world, record_tests):
    world = return_world
    made = record_tests._attestable_placeholder_return(world)
    outcome = world.record(made, task_id="review-attested")
    assert outcome.accepted, outcome.rejection_codes
    saved = world.root / outcome.saved_return
    assert record_tests.yaml.safe_load(saved.read_bytes())["reviewer"]["prompt_sha256"] == made["sent"]
