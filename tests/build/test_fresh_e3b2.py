"""Contract checks for check-12 manifests, immutable closure and draft freshness."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

from scripts.build.fresh import manifest
from scripts.build.fresh.closure import compute_closure
from scripts.build.fresh.module import draft_is_current
from scripts.build.fresh.regeneration import load_ledger, record_failure, record_success
from scripts.curriculum.evidence import lock
from scripts.review.digest.generator import GENERATOR_VERSION, check_digest
from scripts.review.receipts import ledger as receipts_ledger

pytestmark = pytest.mark.reads_content


def _fixture(root: Path):
    from tests.build.test_fresh_runner import _fixture as lesson_fixture

    level, slug = "a1", "fixture-module"
    plan_dir = root / "curriculum/l2-uk-en/lesson-plans/a1"
    evidence_dir = root / "curriculum/l2-uk-en/evidence/a1"
    state_dir = evidence_dir / "_state" / slug
    page_dir = root / "site/src/content/docs/a1" / slug
    cards = root / "docs/style-cards"
    schemas_dir = root / "schemas"
    for folder in (plan_dir, evidence_dir, state_dir, page_dir, cards, schemas_dir):
        folder.mkdir(parents=True, exist_ok=True)
    for name in ("module-plan-v2", "resolution-receipts-v1", "learner-observed-v1", "module-digest-v1"):
        (schemas_dir / f"{name}.schema.json").write_bytes(
            (Path(__file__).resolve().parents[2] / "schemas" / f"{name}.schema.json").read_bytes()
        )
    _, base_plan, _, _ = lesson_fixture()
    lessons = []
    for n in (1, 2, 3):
        lesson = copy.deepcopy(base_plan["lessons"][0])
        lesson.update(n=n, slug=f"lesson-{n}", title=f"Lesson {n}", kind="recap" if n == 3 else "teach")
        lessons.append(lesson)
    plan = {**base_plan, "module": slug, "slug": slug, "lessons": lessons}
    (plan_dir / f"{slug}.yaml").write_bytes(lock.yaml_bytes(plan))
    (plan_dir / "_decisions.yaml").write_text("decisions: []\n", encoding="utf-8")
    lock.write(evidence_dir / f"{slug}.yaml", b"records: []\n")
    lock.write(evidence_dir / "_words.yaml", b"words: []\n")
    (cards / "a1.md").write_text("A1 style\n", encoding="utf-8")
    (cards / "a1.sha256").write_text(
        hashlib.sha256((cards / "a1.md").read_bytes()).hexdigest() + "\n", encoding="ascii"
    )
    (state_dir / "lessons.lock.yaml").write_bytes(
        lock.yaml_bytes({"lessons": [{"n": n, "entry_sha256": f"{n}" * 64} for n in (1, 2, 3)]})
    )
    for n in (1, 2, 3):
        (page_dir / f"{n}.mdx").write_text(f"# Lesson {n}\n", encoding="utf-8")
        (state_dir / f"lesson-{n}.gates.yaml").write_bytes(lock.yaml_bytes({"passed": True}))
        lesson_id = {"level": level, "slug": slug, "n": n}
        lock.write(
            state_dir / f"lesson-{n}.observed.yaml",
            lock.yaml_bytes(
                {
                    "observed_schema": 1,
                    "lesson": lesson_id,
                    "records": [],
                    "untaught_forms": {"count": 0, "share": 0.0, "forms": []},
                }
            ),
        )
        lock.write(
            state_dir / f"lesson-{n}.resolutions.yaml",
            lock.yaml_bytes(
                {
                    "resolutions_schema": 1,
                    "lesson": lesson_id,
                    "inputs": {
                        key: "0" * 64
                        for key in ("expanded_sha256", "allowlist_sha256", "words_lock", "vesum", "trie_digest")
                    },
                    "tokens": [],
                }
            ),
        )
        (state_dir / f"lesson-{n}.provenance.yaml").write_bytes(
            lock.yaml_bytes(
                {
                    "provenance_schema": 1,
                    "lesson": lesson_id,
                    "spans": [],
                }
            )
        )
    return level, slug, plan_dir, evidence_dir, state_dir, page_dir


def _fake_state(data: dict | None = None, *, cumulative_core_count: int = 0):
    """A planned-state stand-in exposing what the manifest reads: to_dict, the count and the waiver."""
    return type(
        "State",
        (),
        {"to_dict": lambda self: dict(data or {}), "cumulative_core_count": cumulative_core_count, "waiver": None},
    )()


def _write(level, slug, n, state_dir, plan_dir, evidence_dir, page_dir, root):
    return manifest.write_manifest(
        level,
        slug,
        n,
        lesson_kind="recap" if n == 3 else "lesson",
        state_dir=state_dir,
        repo_root=root,
        plans_dir=plan_dir,
        evidence_dir=evidence_dir,
        position=1,
        site_dir=page_dir,
    )


def test_manifest_names_every_file_a_reviewer_receives(tmp_path, monkeypatch):
    level, slug, plan_dir, evidence_dir, state_dir, page_dir = _fixture(tmp_path)
    calls = []
    state = _fake_state({"level": "a1", "core_ids": {"W-1": {"position": 1, "lesson": 1}}}, cumulative_core_count=12)

    def planned(*args, **kwargs):
        calls.append(args)
        return state

    monkeypatch.setattr(manifest, "planned_state", planned)
    from scripts.build.fresh.immersion import compute_immersion_payload

    payloads = {}
    for n in (1, 2, 3):
        calls.clear()
        doc, _ = _write(level, slug, n, state_dir, plan_dir, evidence_dir, page_dir, tmp_path)
        assert len(calls) == 1  # one planned_state result feeds the identity hash and the materialized file
        Draft202012Validator(json.loads(manifest.SCHEMA.read_text(encoding="utf-8"))).validate(doc)
        inputs = doc["inputs"]
        for name in ("plan", "pack", "pack_lock", "words", "words_lock", "learner_state", "lesson"):
            assert inputs[name]["sha256"] == hashlib.sha256((tmp_path / inputs[name]["path"]).read_bytes()).hexdigest()
        assert inputs["pack"]["path"] == f"curriculum/l2-uk-en/evidence/a1/{slug}.yaml"
        assert inputs["words"]["path"] == "curriculum/l2-uk-en/evidence/a1/_words.yaml"
        assert lock.check(tmp_path / inputs["pack"]["path"]) and lock.check(tmp_path / inputs["words"]["path"])
        state_path = tmp_path / inputs["learner_state"]["path"]
        assert inputs["learner_state"]["path"].endswith(f"/_state/{slug}/lesson-{n}.learner-state.yaml")
        assert lock.check(state_path)  # the sidecar
        document = yaml.safe_load(state_path.read_bytes())
        assert document["learner_state"] == state.to_dict()
        assert document["immersion"] == compute_immersion_payload("a1", 1, n, cumulative_core_count=12).to_dict()
        assert set(document["immersion"]["permitted_languages"]) >= {"narration", "activity_instruction", "gloss"}
        assert state_path.read_bytes() == lock.yaml_bytes(document)
        assert doc["learner_state"] == {"sha256": manifest.learner_state_sha256(state), "source": "planned_state"}
        assert doc["previous_attempt"] is None and doc["diff"] is None  # a first review
        assert [row["n"] for row in doc["upstream_lessons"]] == list(range(1, n))
        for row in doc["upstream_lessons"]:
            assert row["path"] == f"site/src/content/docs/a1/{slug}/{row['n']}.mdx"
            assert row["sha256"] == hashlib.sha256((tmp_path / row["path"]).read_bytes()).hexdigest()
        payloads[n] = state_path.read_bytes()
    assert doc["recap"] is True and len(doc["upstream_lessons"]) == 2  # the recap reviewer receives lessons 1..2
    # a byte-stable rerun: same manifest, same materialized state
    first = (state_dir / "lesson-3.manifest.yaml").read_bytes()
    _write(level, slug, 3, state_dir, plan_dir, evidence_dir, page_dir, tmp_path)
    assert (state_dir / "lesson-3.manifest.yaml").read_bytes() == first
    assert (state_dir / "lesson-3.learner-state.yaml").read_bytes() == payloads[3]


def _valid_review(review_id, attempt_id, digest):
    return {
        "review_schema": 1,
        "taxonomy": 1,
        "kind": "lesson",
        "attempt": {
            "review_id": review_id,
            "attempt_id": attempt_id,
            "manifest_sha256": digest,
            "previous_attempt_id": None,
        },
        "reviewer": {
            "resolved_model": "fixture-model",
            "harness": "fixture-harness",
            "family": "fixture-family",
            "prompt_sha256": "cd" * 32,
        },
        "checks": {"closing_shape": "clean"},
        "findings": [],
    }


def _rereview_setup(tmp_path, monkeypatch, *, review_id="rev-1", attempt_id="attempt-1"):
    """Lesson 2 reviewed once (a schema-valid review and a sidecar-verified ledger), then rebuilt with different text."""
    level, slug, plan_dir, evidence_dir, state_dir, page_dir = _fixture(tmp_path)
    monkeypatch.setattr(manifest, "planned_state", lambda *a, **kw: _fake_state())
    first, digest = _write(level, slug, 2, state_dir, plan_dir, evidence_dir, page_dir, tmp_path)
    review = state_dir / f"lesson-2.review.{attempt_id}.yaml"
    review.write_bytes(lock.yaml_bytes(_valid_review(review_id, attempt_id, digest)))
    ledger = tmp_path / "batch_state" / "review-receipts" / review_id / f"{attempt_id}.jsonl"
    receipts_ledger.create_empty_ledger(ledger)

    def entry(path):
        return {"path": path.relative_to(tmp_path).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

    previous = {"attempt_id": attempt_id, "review": entry(review), "ledger": entry(ledger)}
    (page_dir / "2.mdx").write_text("# Lesson 2\nNew sentence.\n", encoding="utf-8")
    return (level, slug, plan_dir, evidence_dir, state_dir, page_dir), first, previous, review


def test_a_re_review_manifest_pins_the_previous_findings_and_a_real_diff(tmp_path, monkeypatch):
    (level, slug, plan_dir, evidence_dir, state_dir, page_dir), first, previous, _review = _rereview_setup(
        tmp_path, monkeypatch
    )
    doc, digest = manifest.write_manifest(
        level,
        slug,
        2,
        lesson_kind="lesson",
        state_dir=state_dir,
        repo_root=tmp_path,
        plans_dir=plan_dir,
        evidence_dir=evidence_dir,
        position=1,
        site_dir=page_dir,
        previous_attempt=previous,
    )
    Draft202012Validator(json.loads(manifest.SCHEMA.read_text(encoding="utf-8"))).validate(doc)
    assert doc["previous_attempt"] == previous
    diff_path = tmp_path / doc["diff"]["path"]
    assert diff_path.name == f"lesson-2.diff.attempt-1.{doc['diff']['sha256'][:16]}.patch"
    assert doc["diff"] == {
        "path": diff_path.relative_to(tmp_path).as_posix(),
        "sha256": hashlib.sha256(diff_path.read_bytes()).hexdigest(),
    }
    text = diff_path.read_text(encoding="utf-8")
    assert "+New sentence." in text and " # Lesson 2" in text
    assert f"@{first['inputs']['lesson']['sha256'][:12]}" in text
    assert doc["inputs"]["lesson"]["sha256"] != first["inputs"]["lesson"]["sha256"]
    # a byte-stable rerun of the same re-review
    manifest.write_manifest(
        level,
        slug,
        2,
        lesson_kind="lesson",
        state_dir=state_dir,
        repo_root=tmp_path,
        plans_dir=plan_dir,
        evidence_dir=evidence_dir,
        position=1,
        site_dir=page_dir,
        previous_attempt=previous,
    )
    assert (state_dir / "lesson-2.manifest.sha256").read_text(encoding="ascii") == f"{digest}\n"


@pytest.mark.parametrize("target", ["review", "ledger", "lesson_snapshot"])
def test_a_tampered_previous_attempt_input_is_refused(tmp_path, monkeypatch, target):
    (level, slug, plan_dir, evidence_dir, state_dir, page_dir), first, previous, review = _rereview_setup(
        tmp_path, monkeypatch
    )
    victim = {
        "review": review,
        "ledger": tmp_path / previous["ledger"]["path"],
        "lesson_snapshot": manifest.lesson_snapshot_path(state_dir, 2, first["inputs"]["lesson"]["sha256"]),
    }[target]
    victim.write_bytes(victim.read_bytes() + b"tampered\n")
    with pytest.raises(manifest.ManifestInputError) as refused:
        manifest.write_manifest(
            level,
            slug,
            2,
            lesson_kind="lesson",
            state_dir=state_dir,
            repo_root=tmp_path,
            plans_dir=plan_dir,
            evidence_dir=evidence_dir,
            position=1,
            site_dir=page_dir,
            previous_attempt=previous,
        )
    assert refused.value.path == victim.relative_to(tmp_path).as_posix()


def test_a_previous_attempt_at_the_wrong_path_is_refused(tmp_path, monkeypatch):
    (level, slug, plan_dir, evidence_dir, state_dir, page_dir), _first, previous, _review = _rereview_setup(
        tmp_path, monkeypatch
    )
    previous["ledger"]["path"] = "batch_state/review-receipts/other/attempt-1.jsonl"
    with pytest.raises(manifest.ManifestInputError, match="not at its expected path"):
        manifest.write_manifest(
            level,
            slug,
            2,
            lesson_kind="lesson",
            state_dir=state_dir,
            repo_root=tmp_path,
            plans_dir=plan_dir,
            evidence_dir=evidence_dir,
            position=1,
            site_dir=page_dir,
            previous_attempt=previous,
        )


def _rereview(level, slug, plan_dir, evidence_dir, state_dir, page_dir, tmp_path, previous):
    return manifest.write_manifest(
        level,
        slug,
        2,
        lesson_kind="lesson",
        state_dir=state_dir,
        repo_root=tmp_path,
        plans_dir=plan_dir,
        evidence_dir=evidence_dir,
        position=1,
        site_dir=page_dir,
        previous_attempt=previous,
    )


def _repin(tmp_path, previous, key, path):
    previous[key] = {
        "path": path.relative_to(tmp_path).as_posix(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def test_a_previous_review_that_breaks_the_review_schema_is_refused(tmp_path, monkeypatch):
    setup, _first, previous, review = _rereview_setup(tmp_path, monkeypatch)
    document = yaml.safe_load(review.read_bytes())
    del document["findings"]
    review.write_bytes(lock.yaml_bytes(document))
    _repin(tmp_path, previous, "review", review)
    with pytest.raises(manifest.ManifestInputError, match=r"does not conform to review-v1.*findings") as refused:
        _rereview(*setup, tmp_path, previous)
    assert refused.value.path == review.relative_to(tmp_path).as_posix()


def test_a_previous_ledger_without_a_sidecar_is_refused(tmp_path, monkeypatch):
    setup, _first, previous, _review = _rereview_setup(tmp_path, monkeypatch)
    ledger = tmp_path / previous["ledger"]["path"]
    ledger.write_text('{"receipt": 1}\n', encoding="utf-8")
    receipts_ledger._sidecar(ledger).unlink()
    _repin(tmp_path, previous, "ledger", ledger)
    with pytest.raises(manifest.ManifestInputError, match=r"previous ledger not verified.*sidecar missing"):
        _rereview(*setup, tmp_path, previous)


def test_a_previous_ledger_whose_sidecar_does_not_verify_is_refused(tmp_path, monkeypatch):
    setup, _first, previous, _review = _rereview_setup(tmp_path, monkeypatch)
    ledger = tmp_path / previous["ledger"]["path"]
    ledger.write_text('{"receipt_id": "r-1"}\n', encoding="utf-8")
    receipts_ledger._sidecar(ledger).write_text("0" * 64 + "\n", encoding="ascii")  # covers other bytes
    _repin(tmp_path, previous, "ledger", ledger)
    with pytest.raises(manifest.ManifestInputError, match=r"previous ledger not verified.*sidecar mismatch"):
        _rereview(*setup, tmp_path, previous)


def test_two_rebuilds_against_one_previous_attempt_keep_their_own_diffs(tmp_path, monkeypatch):
    setup, _first, previous, _review = _rereview_setup(tmp_path, monkeypatch)
    page_dir = setup[-1]
    docs = [_rereview(*setup, tmp_path, previous)[0]]
    (page_dir / "2.mdx").write_text("# Lesson 2\nA different sentence.\n", encoding="utf-8")
    docs.append(_rereview(*setup, tmp_path, previous)[0])
    first_diff, second_diff = (doc["diff"] for doc in docs)
    assert first_diff["path"] != second_diff["path"]
    for diff in (first_diff, second_diff):
        assert hashlib.sha256((tmp_path / diff["path"]).read_bytes()).hexdigest() == diff["sha256"]
    assert b"+New sentence." in (tmp_path / first_diff["path"]).read_bytes()
    assert b"+A different sentence." in (tmp_path / second_diff["path"]).read_bytes()


def test_a_different_diff_at_an_existing_content_address_is_refused(tmp_path):
    state_dir = tmp_path / "curriculum/l2-uk-en/evidence/a1/_state/s"
    path = manifest._write_diff(tmp_path, state_dir, 2, "attempt-1", b"one\n")
    assert manifest._write_diff(tmp_path, state_dir, 2, "attempt-1", b"one\n") == path  # identical bytes reused
    path.write_bytes(b"other\n")
    with pytest.raises(manifest.ManifestInputError, match="diff path collision"):
        manifest._write_diff(tmp_path, state_dir, 2, "attempt-1", b"one\n")


def test_the_manifest_and_the_writer_prompt_share_one_immersion_payload_under_a_waiver(tmp_path, monkeypatch):
    from scripts.build.fresh import cli, module

    level, slug, plan_dir, evidence_dir, state_dir, page_dir = _fixture(tmp_path)
    plan = yaml.safe_load((plan_dir / f"{slug}.yaml").read_bytes())
    paths = {
        "plan": plan_dir / f"{slug}.yaml",
        "pack": evidence_dir / f"{slug}.yaml",
        "words": evidence_dir / "_words.yaml",
        "lock": state_dir / "lessons.lock.yaml",
        "state_dir": evidence_dir / "_state",
    }
    waived = _fake_state({"level": "a1"}, cumulative_core_count=4)
    waived.waiver = "waived: prior_plans_missing (missing positions: [1])"
    monkeypatch.setattr(
        cli, "_load_lesson_data", lambda _l, _s, n, **_kw: (plan, plan["lessons"][n - 1], {}, {}, paths)
    )
    monkeypatch.setattr(
        cli,
        "_compute_input_hashes",
        lambda *a: {
            k: "0" * 64
            for k in ("plan_sha256", "pack_lock", "words_lock", "lesson_lock_entry_sha256", "learner_state_sha256")
        },
    )
    monkeypatch.setattr(cli, "_load_cited_records", lambda *a: {})
    monkeypatch.setattr(module, "planned_state", lambda *a, **kw: waived)
    monkeypatch.setattr(manifest, "planned_state", lambda *a, **kw: waived)
    seen = {}

    def render(_entry, **kw):
        seen["immersion"] = kw["immersion"]
        return "prompt"

    monkeypatch.setattr(module, "render_lesson_prompt", render)
    monkeypatch.setattr(
        module, "check_rendered_prompt", lambda *a, **kw: type("Result", (), {"passed": True, "errors": []})()
    )
    module.build_module(level, slug, repo_root=tmp_path, lesson_n=1)
    doc, _ = _write(level, slug, 1, state_dir, plan_dir, evidence_dir, page_dir, tmp_path)
    materialized = yaml.safe_load((tmp_path / doc["inputs"]["learner_state"]["path"]).read_bytes())["immersion"]
    assert seen["immersion"].waiver == waived.waiver
    assert materialized == seen["immersion"].to_dict()


def test_a_pack_or_word_store_that_disagrees_with_its_lock_fails_naming_it(tmp_path, monkeypatch):
    level, slug, plan_dir, evidence_dir, state_dir, page_dir = _fixture(tmp_path)
    monkeypatch.setattr(manifest, "planned_state", lambda *a, **kw: _fake_state())
    for target in (evidence_dir / f"{slug}.yaml", evidence_dir / "_words.yaml"):
        original = target.read_bytes()
        target.write_bytes(original + b"# edited without rewriting the lock\n")
        with pytest.raises(manifest.ManifestInputError, match="lock mismatch") as exc:
            _write(level, slug, 1, state_dir, plan_dir, evidence_dir, page_dir, tmp_path)
        assert exc.value.path == target.relative_to(tmp_path).as_posix()
        assert target.name in str(exc.value)
        target.write_bytes(original)
    _write(level, slug, 1, state_dir, plan_dir, evidence_dir, page_dir, tmp_path)


def test_a_changed_pack_or_state_gives_a_different_manifest(tmp_path, monkeypatch):
    level, slug, plan_dir, evidence_dir, state_dir, page_dir = _fixture(tmp_path)
    current = {"state": _fake_state({"a": 1})}
    monkeypatch.setattr(manifest, "planned_state", lambda *a, **kw: current["state"])
    _, first = _write(level, slug, 1, state_dir, plan_dir, evidence_dir, page_dir, tmp_path)
    lock.write(evidence_dir / f"{slug}.yaml", b"records: [changed]\n")  # lock rewritten: still a different pack
    _, second = _write(level, slug, 1, state_dir, plan_dir, evidence_dir, page_dir, tmp_path)
    assert second != first
    current["state"] = _fake_state({"a": 2})
    doc, third = _write(level, slug, 1, state_dir, plan_dir, evidence_dir, page_dir, tmp_path)
    assert third not in {first, second}
    assert yaml.safe_load((tmp_path / doc["inputs"]["learner_state"]["path"]).read_bytes())["learner_state"] == {"a": 2}


def test_manifest_history_and_closure_preserve_stale_attempts(tmp_path, monkeypatch):
    level, slug, plan_dir, evidence_dir, state_dir, page_dir = _fixture(tmp_path)
    monkeypatch.setattr(manifest, "planned_state", lambda *a, **kw: _fake_state({"b": 2, "a": 1}))
    assert manifest.learner_state_sha256(type("State", (), {"to_dict": lambda self: {"a": 1, "b": 2}})()) == (
        hashlib.sha256(b'{"a":1,"b":2}').hexdigest()
    )
    old = {}
    for n in (1, 2, 3):
        _, old[n] = manifest.write_manifest(
            level,
            slug,
            n,
            lesson_kind="recap" if n == 3 else "lesson",
            state_dir=state_dir,
            repo_root=tmp_path,
            plans_dir=plan_dir,
            evidence_dir=evidence_dir,
            position=1,
            site_dir=page_dir,
        )
        data = yaml.safe_load((state_dir / f"lesson-{n}.manifest.yaml").read_text(encoding="utf-8"))
        Draft202012Validator(json.loads(manifest.SCHEMA.read_text(encoding="utf-8"))).validate(data)
        assert data["recap"] is (n == 3)
        digest_path = tmp_path / data["module_digest"]["path"]
        assert data["module_digest"]["sha256"] == hashlib.sha256(digest_path.read_bytes()).hexdigest()
        assert data["review_eligible"] is True and data["blocked_by"] == []
        assert data["digest_generator_version"] == GENERATOR_VERSION
        assert check_digest(level, slug, n, repo_root=tmp_path)[0] == digest_path
        assert [row["n"] for row in data["upstream_lessons"]] == list(range(1, n))
    lessons = [{"n": n, "kind": "recap" if n == 3 else "teach"} for n in (1, 2, 3)]
    clean = compute_closure(level, slug, lessons, repo_root=tmp_path, state_dir=state_dir, site_dir=page_dir)
    assert clean["stale"] == []
    (page_dir / "1.mdx").write_text("# Lesson 1 changed\n", encoding="utf-8")
    observed_path = state_dir / "lesson-1.observed.yaml"
    observed = yaml.safe_load(observed_path.read_text(encoding="utf-8"))
    observed["records"].append({"id": "W-1", "role": "exposed", "forms": []})
    lock.write(observed_path, lock.yaml_bytes(observed))
    old_digest = yaml.safe_load((state_dir / "lesson-3.manifest.yaml").read_text(encoding="utf-8"))["module_digest"][
        "sha256"
    ]
    for n in (1, 2, 3):
        manifest.write_manifest(
            level,
            slug,
            n,
            lesson_kind="recap" if n == 3 else "lesson",
            state_dir=state_dir,
            repo_root=tmp_path,
            plans_dir=plan_dir,
            evidence_dir=evidence_dir,
            position=1,
            site_dir=page_dir,
        )
    changed = compute_closure(level, slug, lessons, repo_root=tmp_path, state_dir=state_dir, site_dir=page_dir)
    new_digest = yaml.safe_load((state_dir / "lesson-3.manifest.yaml").read_text(encoding="utf-8"))["module_digest"][
        "sha256"
    ]
    assert new_digest != old_digest
    upstream = [row for row in changed["stale"] if row["input"].startswith("upstream_lessons[")]
    assert {(row["n"], row["manifest_sha256"]) for row in upstream} == {(2, old[2]), (3, old[3])}
    assert all(row["upstream"] == 1 for row in upstream)
    # the superseded lesson 1 attempt pinned the lesson text that has since changed; nothing else is stale
    assert {(row["n"], row["manifest_sha256"], row["input"]) for row in changed["stale"] if row not in upstream} >= {
        (1, old[1], "inputs.lesson")
    }
    assert all(row["manifest_sha256"] in set(old.values()) for row in changed["stale"])


def _closure_of_three(tmp_path, monkeypatch):
    level, slug, plan_dir, evidence_dir, state_dir, page_dir = _fixture(tmp_path)
    monkeypatch.setattr(manifest, "planned_state", lambda *a, **kw: _fake_state({"a": 1}))
    for n in (1, 2, 3):
        _write(level, slug, n, state_dir, plan_dir, evidence_dir, page_dir, tmp_path)
    lessons = [{"n": n, "kind": "recap" if n == 3 else "teach"} for n in (1, 2, 3)]

    def closure():
        return compute_closure(level, slug, lessons, repo_root=tmp_path, state_dir=state_dir, site_dir=page_dir)

    assert closure()["stale"] == []
    return evidence_dir, state_dir, slug, closure


@pytest.mark.parametrize("which", ["pack", "words", "learner_state"])
def test_closure_goes_stale_when_a_pinned_input_changes_and_names_it(tmp_path, monkeypatch, which):
    evidence_dir, state_dir, slug, closure = _closure_of_three(tmp_path, monkeypatch)
    target = {
        "pack": evidence_dir / f"{slug}.yaml",
        "words": evidence_dir / "_words.yaml",
        "learner_state": state_dir / "lesson-2.learner-state.yaml",
    }[which]
    before = hashlib.sha256(target.read_bytes()).hexdigest()
    lock.write(target, target.read_bytes() + b"# reviewed change, lock rewritten\n")  # the lock agrees: still stale
    stale = closure()["stale"]
    named = {(row["n"], row["input"]) for row in stale}
    if which == "learner_state":
        assert named == {(2, "inputs.learner_state")}
    else:  # shared by every lesson; the rewritten lock file is a pinned input too
        assert named == {(n, f"inputs.{name}") for n in (1, 2, 3) for name in (which, f"{which}_lock")}
    row = next(row for row in stale if row["input"] == f"inputs.{which}")
    assert row["path"] == target.relative_to(tmp_path).as_posix()
    assert row["recorded_sha256"] == before and row["current_sha256"] == hashlib.sha256(target.read_bytes()).hexdigest()
    assert "upstream" not in row


def _rereview_closure(tmp_path, monkeypatch):
    (level, slug, plan_dir, evidence_dir, state_dir, page_dir), _first, previous, review = _rereview_setup(
        tmp_path, monkeypatch
    )
    doc, digest = manifest.write_manifest(
        level, slug, 2, lesson_kind="lesson", state_dir=state_dir, repo_root=tmp_path, plans_dir=plan_dir,
        evidence_dir=evidence_dir, position=1, site_dir=page_dir, previous_attempt=previous,
    )

    def stale_of_rereview():
        result = compute_closure(
            level, slug, [{"n": 2, "kind": "lesson"}], repo_root=tmp_path, state_dir=state_dir, site_dir=page_dir
        )
        return [row for row in result["stale"] if row["manifest_sha256"] == digest]

    assert stale_of_rereview() == []
    return doc, review, stale_of_rereview


@pytest.mark.parametrize("location", ["module_digest", "diff", "previous_attempt.review", "previous_attempt.ledger"])
def test_closure_goes_stale_when_a_pin_outside_inputs_changes(tmp_path, monkeypatch, location):
    doc, _review, stale_of_rereview = _rereview_closure(tmp_path, monkeypatch)
    entry = doc
    for part in location.split("."):
        entry = entry[part]
    target = tmp_path / entry["path"]
    target.write_bytes(target.read_bytes() + b"\nchanged after the manifest pinned it\n")
    (row,) = stale_of_rereview()
    assert (row["input"], row["path"], row["recorded_sha256"]) == (location, entry["path"], entry["sha256"])
    assert row["current_sha256"] == hashlib.sha256(target.read_bytes()).hexdigest()


def test_the_pin_walk_covers_every_pinned_file_in_the_manifest(tmp_path, monkeypatch):
    doc, _review, _stale = _rereview_closure(tmp_path, monkeypatch)
    names = [name for name, _entry in manifest.pinned_entries(doc)]
    assert {"module_digest", "diff", "previous_attempt.review", "previous_attempt.ledger", "inputs.plan"} <= set(names)
    assert "inputs.activity_data[0]" in names or not doc["inputs"]["activity_data"]
    assert len(names) == len(set(names))
    # not a pin: the lock entry (entry_sha256) and the learner-state identity (no path)
    assert "lesson_lock_entry" not in names and "learner_state" not in names


def test_a_new_pinned_field_anywhere_is_detected_without_code_changes(tmp_path):
    (tmp_path / "notes").mkdir()
    for name in ("a.txt", "b.txt", "c.txt"):
        (tmp_path / "notes" / name).write_text(name, encoding="utf-8")

    def pin(name):
        return {"path": f"notes/{name}", "sha256": hashlib.sha256(name.encode()).hexdigest()}

    doc = {
        "future_top_level": pin("a.txt"),
        "future_section": {"nested": [pin("b.txt"), {"deeper": pin("c.txt")}]},
        "not_a_pin": {"path": "notes/a.txt", "entry_sha256": "0" * 64},
    }
    assert manifest.changed_inputs(doc, tmp_path) == []
    (tmp_path / "notes" / "a.txt").write_text("edited", encoding="utf-8")
    (tmp_path / "notes" / "c.txt").unlink()
    assert {(row["input"], row["current_sha256"] is None) for row in manifest.changed_inputs(doc, tmp_path)} == {
        ("future_top_level", False),
        ("future_section.nested[1].deeper", True),
    }


def test_closure_reports_a_deleted_pinned_input_as_missing(tmp_path, monkeypatch):
    _, state_dir, _, closure = _closure_of_three(tmp_path, monkeypatch)
    (state_dir / "lesson-3.learner-state.yaml").unlink()
    (row,) = closure()["stale"]
    assert (row["n"], row["input"], row["current_sha256"]) == (3, "inputs.learner_state", None)


def test_style_card_sidecar_mismatch_fails_manifest(tmp_path, monkeypatch):
    level, slug, plan_dir, evidence_dir, state_dir, page_dir = _fixture(tmp_path)
    monkeypatch.setattr(manifest, "planned_state", lambda *a, **kw: _fake_state())
    (tmp_path / "docs/style-cards/a1.sha256").write_text("0" * 64 + "\n", encoding="ascii")
    with pytest.raises(ValueError, match="style card sidecar mismatch"):
        manifest.write_manifest(
            level,
            slug,
            1,
            lesson_kind="lesson",
            state_dir=state_dir,
            repo_root=tmp_path,
            plans_dir=plan_dir,
            evidence_dir=evidence_dir,
            position=1,
            site_dir=page_dir,
        )
    assert not (state_dir / "lesson-1.manifest.yaml").exists()


def test_digest_path_guard_rejects_override_and_outside_path(tmp_path):
    level, slug, _plan_dir, evidence_dir, state_dir, page_dir = _fixture(tmp_path)
    outside = tmp_path.parent / "other-plan-directory"
    with pytest.raises(manifest.ManifestInputError, match="digest_path_mismatch") as exc:
        manifest.write_manifest(
            level,
            slug,
            1,
            lesson_kind="lesson",
            state_dir=state_dir,
            repo_root=tmp_path,
            plans_dir=outside,
            evidence_dir=evidence_dir,
            position=1,
            site_dir=page_dir,
        )
    assert exc.value.path == outside.resolve().as_posix()
    assert not (state_dir / "lesson-1.manifest.yaml").exists()
    assert not (state_dir / "digest-upto-1.yaml").exists()


def test_successful_manifest_clears_stale_check_12_error(tmp_path, monkeypatch):
    level, slug, plan_dir, evidence_dir, state_dir, page_dir = _fixture(tmp_path)
    monkeypatch.setattr(manifest, "planned_state", lambda *a, **kw: _fake_state())
    manifest.write_manifest_error(state_dir, 1, "old failure", "docs/style-cards/a1.sha256", "2026-01-01T00:00:00Z")
    manifest.write_manifest(
        level,
        slug,
        1,
        lesson_kind="lesson",
        state_dir=state_dir,
        repo_root=tmp_path,
        plans_dir=plan_dir,
        evidence_dir=evidence_dir,
        position=1,
        site_dir=page_dir,
    )
    assert not (state_dir / "lesson-1.manifest-error.yaml").exists()


def test_manifest_hashes_all_imported_activity_data_sorted(tmp_path, monkeypatch):
    level, slug, plan_dir, evidence_dir, state_dir, page_dir = _fixture(tmp_path)
    monkeypatch.setattr(manifest, "planned_state", lambda *a, **kw: _fake_state())
    data_dir = tmp_path / "site/src/data"
    data_dir.mkdir(parents=True)
    for name in ("activity-z.json", "activity-a.json"):
        (data_dir / name).write_text("{}\n", encoding="utf-8")
    (page_dir / "1.mdx").write_text(
        'import z from "@site/src/data/activity-z.json";\nimport a from "@site/src/data/activity-a.json";\n',
        encoding="utf-8",
    )
    doc, _ = manifest.write_manifest(
        level,
        slug,
        1,
        lesson_kind="lesson",
        state_dir=state_dir,
        repo_root=tmp_path,
        plans_dir=plan_dir,
        evidence_dir=evidence_dir,
        position=1,
        site_dir=page_dir,
    )
    assert [item["path"] for item in doc["inputs"]["activity_data"]] == [
        "site/src/data/activity-a.json",
        "site/src/data/activity-z.json",
    ]
    (data_dir / "activity-a.json").unlink()
    with pytest.raises(FileNotFoundError, match=r"activity-a\.json"):
        manifest.write_manifest(
            level,
            slug,
            1,
            lesson_kind="lesson",
            state_dir=state_dir,
            repo_root=tmp_path,
            plans_dir=plan_dir,
            evidence_dir=evidence_dir,
            position=1,
            site_dir=page_dir,
        )


def test_build_cli_requires_exactly_one_target():
    from scripts.build.fresh.cli import _build_parser

    parser = _build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["build", "a1", "fixture-module"])
    with pytest.raises(SystemExit):
        parser.parse_args(["build", "a1", "fixture-module", "--lesson", "1", "--module"])


def test_success_snapshot_controls_draft_reuse(tmp_path):
    draft = tmp_path / "lesson-1.draft.yaml"
    draft.write_text("lesson: one\n", encoding="utf-8")
    keys = ("plan_sha256", "pack_lock", "words_lock", "card_sha256", "prompt_sha256")
    inputs = {key: "a" * 64 for key in keys}
    path = tmp_path / "lesson-1.regeneration.yaml"
    record_success(
        path,
        "fixture-module",
        1,
        {**inputs, "draft_sha256": hashlib.sha256(draft.read_bytes()).hexdigest()},
        at="2026-01-01T00:00:00Z",
    )
    ledger = load_ledger(path, "fixture-module", 1)
    assert draft_is_current(ledger, draft, inputs)
    assert not draft_is_current(ledger, draft, {**inputs, "prompt_sha256": "b" * 64})
    record_failure(
        path,
        "fixture-module",
        1,
        {"check": 11, "reason": "render_failed", "layer": "engine"},
        inputs,
        at="2026-01-02T00:00:00Z",
    )
    ledger = load_ledger(path, "fixture-module", 1)
    assert ledger["attempts"][0]["failed_check"] == 11
    assert not draft_is_current(ledger, draft, inputs)


def test_module_build_three_lessons_and_rebuild_closure(tmp_path, monkeypatch, capsys):
    """Exercise the real checks 1-12 with injected model, resolver, and render edges."""
    from scripts.build.fresh import assemble, cli, module, runner
    from scripts.build.fresh.preflight import PreflightResult
    from scripts.curriculum.learner_state.inventory_gate import GateReport
    from scripts.curriculum.resolver.inputs import Allowlist
    from tests.build.test_fresh_assemble import validate_fixture_plan
    from tests.build.test_fresh_runner import _fixture as lesson_fixture
    from tests.build.test_fresh_runner import _FixtureSources

    level, slug, plan_dir, evidence_dir, state_dir, page_dir = _fixture(tmp_path)
    base_draft, base_plan, pack, words = lesson_fixture()
    lessons = []
    for n in (1, 2, 3):
        entry = copy.deepcopy(base_plan["lessons"][0])
        entry.update(n=n, slug=f"lesson-{n}", title=f"Lesson {n}", kind="recap" if n == 3 else "teach")
        lessons.append(entry)
    plan = {**base_plan, "module": slug, "slug": slug, "lessons": lessons}
    validate_fixture_plan(plan)
    (plan_dir / f"{slug}.yaml").write_bytes(lock.yaml_bytes(plan))
    paths = {
        "plan": plan_dir / f"{slug}.yaml",
        "pack": evidence_dir / f"{slug}.yaml",
        "words": evidence_dir / "_words.yaml",
        "lock": state_dir / "lessons.lock.yaml",
        "state_dir": evidence_dir / "_state",
    }

    class State:
        cumulative_core_count = 10
        waiver = None

        def to_dict(self):
            return {"lesson": 1}

    def load_data(_level, _slug, n, **_kw):
        return plan, lessons[n - 1], pack, words, paths

    def hashes(_paths, n, _state):
        return {
            "plan_sha256": hashlib.sha256(paths["plan"].read_bytes()).hexdigest(),
            "pack_lock": "0" * 64,
            "words_lock": "0" * 64,
            "lesson_lock_entry_sha256": "0" * 64,
            "learner_state_sha256": "0" * 64,
        }

    monkeypatch.setattr(cli, "_load_lesson_data", load_data)
    monkeypatch.setattr(cli, "_compute_input_hashes", hashes)
    monkeypatch.setattr(cli, "_load_cited_records", lambda *a: {})
    monkeypatch.setattr(module, "planned_state", lambda *a, **kw: State())
    monkeypatch.setattr(manifest, "planned_state", lambda *a, **kw: State())
    monkeypatch.setattr(assemble, "planned_state", lambda *a, **kw: State())
    monkeypatch.setattr(assemble.lesson_lock, "check_lesson_lock", lambda *a, **kw: (True, ""))
    monkeypatch.setattr(
        assemble.lesson_lock,
        "compute_lesson_lock",
        lambda *a, **kw: {"lessons": [{"n": n, "entry_sha256": "0" * 64} for n in (1, 2, 3)]},
    )
    monkeypatch.setattr(assemble, "compute_lesson_immersion_band", lambda **kw: type("Band", (), {"band_key": "a1"})())
    monkeypatch.setattr(
        module,
        "preflight_lesson",
        lambda *a, **kw: PreflightResult(passed=True, status="ok", gaps=[], homographs=[], homograph_count=0),
    )
    monkeypatch.setattr(module, "render_lesson_prompt", lambda _entry, **kw: "lesson prompt " + kw["plan_sha256"])
    monkeypatch.setattr(
        module,
        "render_recap_prompt",
        lambda _entry, *, built_lessons, **kw: (
            "recap prompt " + " ".join(item["sha256"] for item in built_lessons) + kw["plan_sha256"]
        ),
    )
    monkeypatch.setattr(
        module, "check_rendered_prompt", lambda prompt, *a, **kw: type("Result", (), {"passed": True, "errors": []})()
    )
    monkeypatch.setattr(module, "lesson_immersion_payload", lambda *a, **kw: {})
    allowlist = Allowlist.from_records(words["words"], words_lock="f" * 64)
    calls = []
    version = [1]

    def writer_call(**kw):
        n = kw["lesson_n"]
        calls.append(n)
        draft = copy.deepcopy(base_draft)
        draft["lesson"] = {"module": f"a1/{slug}", "n": n}
        draft["inputs"].update(hashes(paths, n, None))
        draft["inputs"]["style_card_sha256"] = hashlib.sha256(
            (tmp_path / "docs/style-cards/a1.md").read_bytes()
        ).hexdigest()
        if n == 1 and version[0] == 2:
            draft["steps"][0]["blocks"][0]["text"] += " слово"
        lock.atomic_write(state_dir / f"lesson-{n}.draft.yaml", lock.yaml_bytes(draft))

    def question_call(batch, seat):
        return {"answers": [{"id": q["id"], "record": q["candidates"][0]["record"]} for q in batch["questions"]]}

    def run_actual(*args, **kwargs):
        def observed_writer(_level, _slug, n, *, resolutions_doc, state_dir, **_kw):
            records = sorted(
                {token["selected"]["record"] for token in resolutions_doc["tokens"] if token.get("selected")}
            )
            lock.write(
                state_dir / f"lesson-{n}.observed.yaml",
                lock.yaml_bytes(
                    {
                        "observed_schema": 1,
                        "lesson": {"level": _level, "slug": _slug, "n": n},
                        "records": [{"id": record, "role": "taught", "forms": []} for record in records],
                        "untaught_forms": {"count": 0, "share": 0.0, "forms": []},
                    }
                ),
            )

        return runner.run_lesson(
            *args,
            **kwargs,
            sources=_FixtureSources(),
            allowlist=allowlist,
            question_dispatch=question_call,
            inventory_gate=lambda *a, **kw: GateReport("a1", slug, args[2], ()),
            observed_writer=observed_writer,
            render_check=lambda *a, **kw: assemble.CheckResult(
                check=11, passed=True, artifacts={"verify_shippable": {"shippable": True}}
            ),
        )

    evidence_path = os.environ.get("E3B2_EVIDENCE_DIR")
    saved = Path(evidence_path) if evidence_path else None
    if saved:
        saved.mkdir(parents=True, exist_ok=True)
    no_seat = module.build_module(level, slug, repo_root=tmp_path, runner=run_actual)
    assert not no_seat["complete"] and no_seat["lessons"][0]["stopping_check"] == 0
    assert no_seat["lessons"][0]["reason"] == "writer_seat_required"
    if saved:
        shutil.copy2(state_dir / "module.build.yaml", saved / "writer-seat-required.build.yaml")
    no_recap = module.build_module(
        level, slug, repo_root=tmp_path, lesson_n=3, writer_seat="codex:gpt-6-sol", runner=run_actual
    )
    assert not no_recap["complete"] and no_recap["lessons"][0]["reason"] == "recap_inputs_not_built"
    if saved:
        shutil.copy2(state_dir / "module.build.yaml", saved / "recap-inputs-not-built.build.yaml")
    build_with_injections = module.build_module
    with monkeypatch.context() as patch:
        patch.setattr(
            module,
            "build_module",
            lambda *a, **kw: build_with_injections(*a, writer_dispatch=writer_call, runner=run_actual, **kw),
        )
        assert (
            cli.main(
                [
                    "build",
                    level,
                    slug,
                    "--module",
                    "--writer-seat",
                    "codex:gpt-6-sol",
                    "--question-seat",
                    "codex:gpt-6-sol",
                    "--repo-root",
                    str(tmp_path),
                ]
            )
            == 0
        )
    first = json.loads(capsys.readouterr().out)
    assert first["complete"] and calls == [1, 2, 3], first
    assert cli.main(["closure", level, slug, "--repo-root", str(tmp_path)]) == 0
    assert json.loads(capsys.readouterr().out)["stale"] == []
    assert all(row["passed_through"] == 12 and row["manifest_sha256"] for row in first["lessons"])
    for n in (1, 2, 3):
        data = yaml.safe_load((state_dir / f"lesson-{n}.manifest.yaml").read_text(encoding="utf-8"))
        digest_path = tmp_path / data["module_digest"]["path"]
        assert data["module_digest"]["sha256"] == hashlib.sha256(digest_path.read_bytes()).hexdigest()
        assert check_digest(level, slug, n, repo_root=tmp_path)[0] == digest_path
        assert data["review_eligible"] is True and data["blocked_by"] == []
        assert data["digest_generator_version"] == GENERATOR_VERSION
    for n in (1, 2, 3):
        gates = yaml.safe_load((state_dir / f"lesson-{n}.gates.yaml").read_text(encoding="utf-8"))
        assert [row["check"] for row in gates["checks"]] == list(range(1, 12))
        assert gates["passed"] is True
    recap = yaml.safe_load((state_dir / "lesson-3.manifest.yaml").read_text(encoding="utf-8"))
    assert recap["recap"] is True and [item["n"] for item in recap["upstream_lessons"]] == [1, 2]
    # the live runner (check 12) wrote the materialized state and named the pack and word store
    for n in (1, 2, 3):
        inputs = yaml.safe_load((state_dir / f"lesson-{n}.manifest.yaml").read_text(encoding="utf-8"))["inputs"]
        assert (tmp_path / inputs["learner_state"]["path"]).is_file()
        assert lock.check(tmp_path / inputs["learner_state"]["path"])
        assert inputs["pack"]["path"].endswith(f"/{slug}.yaml") and inputs["words"]["path"].endswith("/_words.yaml")
    assert [(item["n"], item["path"].rsplit("/", 1)[-1]) for item in recap["upstream_lessons"]] == [
        (1, "1.mdx"),
        (2, "2.mdx"),
    ]
    assert yaml.safe_load((state_dir / "module.closure.yaml").read_text(encoding="utf-8"))["stale"] == []
    stable_before = {
        name: (state_dir / name).read_bytes()
        for name in (
            "module.build.yaml",
            "module.closure.yaml",
            "lesson-1.manifest.yaml",
            "lesson-2.manifest.yaml",
            "lesson-3.manifest.yaml",
            "lesson-1.regeneration.yaml",
            "lesson-2.regeneration.yaml",
            "lesson-3.regeneration.yaml",
        )
    }
    if evidence_path:
        shutil.copy2(paths["plan"], saved / "fixture-module.yaml")
        for n in (1, 2, 3):
            shutil.copy2(page_dir / f"{n}.mdx", saved / f"initial-{n}.mdx")
            shutil.copy2(state_dir / f"lesson-{n}.gates.yaml", saved / f"lesson-{n}.gates.yaml")
            shutil.copy2(state_dir / f"lesson-{n}.manifest.yaml", saved / f"initial-{n}.manifest.yaml")
        shutil.copy2(state_dir / "module.build.yaml", saved / "initial-module.build.yaml")
        shutil.copy2(state_dir / "module.closure.yaml", saved / "initial-module.closure.yaml")
    before = {n: hashlib.sha256((page_dir / f"{n}.mdx").read_bytes()).hexdigest() for n in (1, 2, 3)}
    second = module.build_module(
        level,
        slug,
        repo_root=tmp_path,
        writer_seat="codex:gpt-6-sol",
        question_seat="codex:gpt-6-sol",
        writer_dispatch=writer_call,
        runner=run_actual,
    )
    assert second["complete"] and calls == [1, 2, 3]
    assert stable_before == {name: (state_dir / name).read_bytes() for name in stable_before}
    assert before == {n: hashlib.sha256((page_dir / f"{n}.mdx").read_bytes()).hexdigest() for n in (1, 2, 3)}
    version[0] = 2
    draft_path = state_dir / "lesson-1.draft.yaml"
    draft_path.write_bytes(draft_path.read_bytes() + b"# force writer rewrite\n")
    third = module.build_module(
        level,
        slug,
        repo_root=tmp_path,
        writer_seat="codex:gpt-6-sol",
        question_seat="codex:gpt-6-sol",
        writer_dispatch=writer_call,
        runner=run_actual,
    )
    assert third["complete"] and calls == [1, 2, 3, 1, 3], third
    assert hashlib.sha256((page_dir / "1.mdx").read_bytes()).hexdigest() != before[1]
    closure = yaml.safe_load((state_dir / "module.closure.yaml").read_text(encoding="utf-8"))
    assert {(row["n"], row["upstream"]) for row in closure["stale"] if "upstream" in row} >= {(2, 1), (3, 1)}
    if evidence_path:
        shutil.copy2(state_dir / "module.build.yaml", saved / "rebuilt-module.build.yaml")
        shutil.copy2(state_dir / "module.closure.yaml", saved / "rebuilt-module.closure.yaml")
    (tmp_path / "docs/style-cards/a1.sha256").write_text("0" * 64 + "\n", encoding="ascii")
    mismatch = module.build_module(
        level,
        slug,
        repo_root=tmp_path,
        lesson_n=1,
        writer_seat="codex:gpt-6-sol",
        question_seat="codex:gpt-6-sol",
        writer_dispatch=writer_call,
        runner=run_actual,
    )
    assert not mismatch["complete"] and mismatch["lessons"][0]["stopping_check"] == 12
    assert mismatch["lessons"][0]["terminal_layer"] == "driver"
    error = yaml.safe_load((state_dir / "lesson-1.manifest-error.yaml").read_text(encoding="utf-8"))
    assert error["check"] == 12 and "sidecar mismatch" in error["reason"]
    assert error["path"] == "docs/style-cards/a1.sha256"
    assert not (state_dir / "lesson-1.manifest.yaml").exists()
    if evidence_path:
        shutil.copy2(state_dir / "lesson-1.manifest-error.yaml", saved / "lesson-1.manifest-error.yaml")
        shutil.copy2(state_dir / "module.build.yaml", saved / "mismatch-module.build.yaml")
    terminal = module.build_module(
        level, slug, repo_root=tmp_path, lesson_n=1, writer_seat="codex:gpt-6-sol", runner=run_actual
    )
    assert terminal["lessons"][0]["terminal_layer"] == "driver"
    if evidence_path:
        shutil.copy2(state_dir / "module.build.yaml", saved / "terminal-module.build.yaml")
    card = tmp_path / "docs/style-cards/a1.md"
    (tmp_path / "docs/style-cards/a1.sha256").write_text(
        hashlib.sha256(card.read_bytes()).hexdigest() + "\n", encoding="ascii"
    )
    (state_dir / "lesson-1.observed.yaml").unlink()
    report = run_actual(
        level,
        slug,
        2,
        draft=yaml.safe_load((state_dir / "lesson-2.draft.yaml").read_text(encoding="utf-8")),
        plan=plan,
        pack=pack,
        words=words,
        state_dir=state_dir,
        repo_root=tmp_path,
        plans_dir=plan_dir,
        evidence_dir=evidence_dir,
        question_seat="codex:gpt-6-sol",
        site_dir=page_dir,
    )
    assert report["passed_through"] == 12 and report["manifest_sha256"] is None
    assert "digest_error:observed_missing:" in report["reason"]
    error = yaml.safe_load((state_dir / "lesson-2.manifest-error.yaml").read_text(encoding="utf-8"))
    assert error["layer"] == "engine" and error["reason"] == report["reason"]
    assert not (state_dir / "lesson-2.manifest.yaml").exists()
