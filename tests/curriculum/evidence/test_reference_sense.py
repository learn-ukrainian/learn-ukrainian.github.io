"""Synthetic exact-match, integrity, provenance, privacy and product regressions."""

import copy
import hashlib
import json
import sqlite3
import subprocess
from pathlib import Path

import pytest
import yaml

from scripts.build.fresh import assemble, runner
from scripts.curriculum.evidence import pack, sense_cli, sources, verify, words
from scripts.curriculum.evidence import reference_sense_v1 as matcher
from scripts.curriculum.evidence import sense_bindings as bindings
from scripts.curriculum.validate import a1_reference
from scripts.ingest import build_ohoiko_a1_reference as extractor
from scripts.ingest import prove_ohoiko_a1_reference as proof
from scripts.review.receipts import ledger

FIXTURE = json.loads((Path(__file__).parent / "fixtures/reference_sense_synthetic.json").read_text())
WORD = {"id": "W-001", "lemma": "synthetic", "pos": "noun"}
KEY = FIXTURE["key"].encode()


def row(value, index=1, *, word="synthetic", pos="noun"):
    return {"id": index, "word": word, "pos": pos, "translations": json.dumps(value), "text": "", "source": "synthetic"}


@pytest.mark.parametrize(
    "value,expected",
    [
        (" To GO (verb). ", "go"),
        ("to go (figurative)", "go (figurative)"),
        ("GO [intransitive]", "go"),
        ("to go (mechanical)", "go (mechanical)"),
    ],
)
def test_normalization_closed_grammar(value, expected):
    assert matcher.normalize(value, "verb") == expected
    assert matcher.normalize("to go", "noun") == "to go"
    assert matcher.normalize("e\u0301", "noun") == "é"
    for label in matcher.GRAMMATICAL_ANNOTATIONS:
        assert matcher.normalize(f"target ({label})", "noun") == "target"
    assert matcher.normalize("target (unlisted grammar)", "noun") == "target (unlisted grammar)"


@pytest.mark.parametrize(
    "dictionary,meaning,reason",
    [
        (["arm, lever (mechanical)"], "arm", "reference_no_match"),
        (["arm (anatomical)"], "arm (mechanical)", "reference_no_match"),
        (["target (figurative)"], "target", "reference_no_match"),
        (["target, goal"], "target, goal", "reference_multi_head"),
        (["target"], "tar", "reference_no_match"),
        (["targets"], "target", "reference_no_match"),
        (["target (one), goal (two)"], "target", "reference_no_match"),
        (["TARGET", "target"], "target", "reference_ambiguous"),
        (["target", "other"], "target / absent", "reference_multi_head"),
    ],
)
def test_exact_only_and_qualifier_scope(dictionary, meaning, reason):
    result = matcher.select(WORD, [row(dictionary)], meaning)
    assert result.gloss is None
    assert result.reason == reason


def test_same_visible_span_tie_and_multihead_one_span():
    result = matcher.select(WORD, [row(["target"], 7), row(["target"], 3)], "TARGET.")
    assert result.ref["id"] == 3
    assert result.ref["span_index"] == 0
    assert matcher.select(WORD, [row(["target / goal"])], "target, goal").reason == "reference_multi_head"
    assert matcher.select(WORD, [row(["target / goal (mechanical)"])], "target (mechanical)").gloss == "target"


def test_lemma_pos_homonym_and_kaikki_gates():
    assert not matcher.candidates(WORD, [row(["target"], word="other"), row(["target"], pos="verb")])
    entries = [
        {"id": n, "canonical_headword": "synthetic", "homonym_index": n, "grammatical_label": "іменник чоловічого роду"}
        for n in [1, 2]
    ]
    assert matcher.select(WORD, [row(["other", "target"])], "target", ulif_entries=entries).ref["span_index"] == 1
    assert (
        matcher.select(WORD, [row(["target", "TARGET (noun)"])], "target", ulif_entries=entries).reason
        == "reference_ambiguous"
    )
    assert (
        matcher.select(WORD, [], "target", {"pos": ["noun"], "glosses": ["target"]}).reason == "reference_kaikki_only"
    )


def test_span_indexes_follow_existing_parser():
    r = row(["one, two; three (a definition)", "four"])
    pool = matcher.candidates(WORD, [r])
    expected = [
        span
        for s in json.loads(r["translations"])
        for part in sources._sub_senses(s)
        for span in sources._sense_spans(part)
    ]
    assert [span for span, _ in matcher.row_spans(r)] == expected
    assert [c["span"] for c in pool] == ["one", "two", "three", "four"]
    assert all(c["atom_index"] == 0 for c in pool)
    assert [c["span_index"] for c in pool] == list(range(len(expected)))


@pytest.fixture
def bound(tmp_path, monkeypatch, synthetic_sources, synthetic_vesum):
    inventory = tmp_path / "inventory.yaml"
    inventory.write_text(yaml.safe_dump(FIXTURE["inventory"]))
    monkeypatch.setattr(a1_reference, "INVENTORY_PATH", inventory)
    with sqlite3.connect(synthetic_sources) as db:
        db.execute("UPDATE dmklinger_uk_en SET translations=? WHERE id=2", (json.dumps(FIXTURE["translations"]),))
    api = sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum)
    pool = api.gloss_rows([("synthetic", "noun")]).raw[("synthetic", "noun")]
    result = matcher.select(WORD, pool, FIXTURE["private"]["meaning"])
    assert result.ref
    b = bindings.reference_binding(WORD, result.ref, FIXTURE["private"], KEY, "test-key")
    bindings.write(tmp_path / bindings.BINDINGS, "a1", {WORD["id"]: b})
    yield tmp_path, api, b
    api.close()


@pytest.mark.parametrize(
    "field,value",
    [("row_sha256", "0" * 64), ("span_index", 0), ("span", "invented"), ("atom_index", 1), ("locator", "p999#1")],
)
def test_public_binding_mutations_withhold(bound, field, value):
    root, api, b = bound
    b = {**b, field: value}
    bindings.write(root / bindings.BINDINGS, "a1", {WORD["id"]: b})
    context = bindings.Context.read("a1", root)
    assert (
        context.select(WORD, api.gloss_rows([("synthetic", "noun")]).raw[("synthetic", "noun")], None).reason
        == "reference_binding_invalid"
    )


def test_missing_invalid_and_nonmember_fallback(bound):
    root, api, _b = bound
    pool = api.gloss_rows([("synthetic", "noun")]).raw[("synthetic", "noun")]
    context = bindings.Context("a1", {}, bindings.public_entries(a1_reference.INVENTORY_PATH))
    assert context.select(WORD, pool, None).reason == "reference_binding_missing"
    context.invalid = True
    assert context.select(WORD, pool, None).reason == "reference_binding_invalid"
    assert context.select({**WORD, "lemma": "outsider"}, [], None).reason == "reference_binding_invalid"
    assert bindings.Context("a2", {}, []).select(WORD, [row(["target"])], None).gloss == "target"
    path = root / bindings.BINDINGS
    path.write_text(path.read_text() + "# mutation\n")
    assert bindings.Context.read("a1", root).invalid


@pytest.mark.parametrize("method", ["a1_reference_meaning.v1", "reviewed.v1"])
def test_builder_verifier_pack_gate_render_and_immersion_same_string(bound, monkeypatch, capsys, method):
    root, api, b = bound
    if method == "reviewed.v1":
        # A plausible but fabricated reviewer block passes only the public row
        # checks. CI must never imply it verified the nonexistent local review.
        b = {k: v for k, v in b.items() if k not in {"inventory", "locator", "commitment", "key_id"}}
        b.update(
            method=method,
            reviewer={
                "task_id": "fabricated-review",
                "model": "claude-opus-5-5",
                "family": "anthropic",
                "harness": "claude",
                "author_model": "gpt-6.1-sol",
                "date": "2026-10-03",
                "candidates_sha256": "a" * 64,
                "result_sha256": "b" * 64,
            },
        )
        bindings.write(root / bindings.BINDINGS, "a1", {WORD["id"]: b})
    # Synthetic forms use a deterministic synthetic stress oracle, as the
    # existing builder/verifier fixtures do. This asserts no linguistic fact.
    monkeypatch.setattr(
        sources.stress,
        "verify_stress",
        lambda w, **kw: {
            "status": "ok",
            "matches": [
                {
                    "stressed_form": f"{w}-stressed",
                    "unstressed_form": w,
                    "vowel_index": 0,
                    "vowel_indices": [0],
                    "vesum": None,
                    "required_tags": [],
                    "override_applied": False,
                }
            ],
            "source": {"digest": "t" * 64},
        },
    )
    req = root / "request.yaml"
    req.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "level": "a1",
                "words": [
                    {"lemma": "synthetic", "pos": "noun", "want": "new", "entry": {"source": "vesum", "entry_id": 10}}
                ],
            }
        )
    )
    store = words.build_words("a1", req, evidence_dir=root, sources_instance=api, mcp_commit="a" * 40)["store"]
    record = store["words"][0]
    assert record["gloss_en"] == b["span"] == "target"
    result = verify.verify_words_store("a1", evidence_dir=root, plans_dir=root, sources_instance=api)
    assert not result["errors"], result
    assert any(bindings.CI_NOTICE in w for w in result["warnings"])
    unchecked = "W-001:private_commitment" if method == matcher.METHOD else "W-001:review_provenance"
    assert unchecked in result["not_checked"]
    plan = {"vocabulary": {"core": ["W-001"]}}
    context = bindings.Context.read("a1", root)
    assert verify.verify_plan_glosses(plan, store, "a1/synthetic", api, binding_context=context) == []
    plans_dir = root / "plans"
    plans_dir.mkdir()
    (plans_dir / "synthetic.yaml").write_text(yaml.safe_dump(plan))
    pack_request = root / "pack-request.yaml"
    pack_request.write_text(yaml.safe_dump({"request_schema": 1, "module": "a1/synthetic"}))
    pack.build_pack("a1", "synthetic", pack_request, evidence_dir=root, sources_instance=api, offline=True)
    verified_pack = verify.verify_pack(
        "a1", "synthetic", evidence_dir=root, plans_dir=plans_dir, sources_instance=api, offline=True
    )
    assert not verified_pack["errors"], verified_pack
    assert unchecked in verified_pack["not_checked"]
    assert any(bindings.CI_NOTICE in w for w in verified_pack["warnings"])
    if method == "reviewed.v1":
        with monkeypatch.context() as patched:
            patched.setattr(sources, "Sources", lambda **kw: api)
            assert verify.main(["a1", "--evidence-dir", str(root), "--plans-dir", str(root), "--json"]) == 0
            cli_words = json.loads(capsys.readouterr().out)
            assert unchecked in cli_words["not_checked"]
            assert any(bindings.CI_NOTICE in w for w in cli_words["warnings"])
            assert (
                verify.main_pack(
                    [
                        "a1",
                        "synthetic",
                        "--evidence-dir",
                        str(root),
                        "--plans-dir",
                        str(plans_dir),
                        "--offline",
                        "--json",
                    ]
                )
                == 0
            )
            cli_pack = json.loads(capsys.readouterr().out)
            assert unchecked in cli_pack["not_checked"]
            assert any(bindings.CI_NOTICE in w for w in cli_pack["warnings"])
    record["sense_gloss"] = "unchecked override must be ignored"
    rendered = assemble.render_unit_piece("{{gloss:W-001}}", assemble.gloss_replacer(store))
    assert rendered == "synthetic (target)"
    count = runner.check_6_count({"units": [{"tab": "urok", "role": "gloss_ref", "text": "{{gloss:W-001}}"}]}, 0, store)
    assert count["details"]["urok_tokens"] == 2
    from types import SimpleNamespace

    from tests.build.test_fresh_render_coverage import check_render, maximal_draft

    draft, page_plan, page_pack, _page_words = maximal_draft("a1")
    page_inputs = json.loads(
        json.dumps([draft, page_plan, page_pack])
        .replace("W-1", "W-001")
        .replace("W-2", "W-002")
        .replace("noun:inanim:m:v_naz", "noun:inanim:f:v_naz")
    )
    page_words = {"words": [record, {**record, "id": "W-002"}]}
    monkeypatch.setattr(assemble.lesson_lock, "check_lesson_lock", lambda *a, **k: (True, ""))
    monkeypatch.setattr(
        assemble.lesson_lock, "compute_lesson_lock", lambda *a, **k: {"lessons": [{"n": 1, "entry_sha256": "0" * 64}]}
    )
    monkeypatch.setattr(assemble, "atlas_href_for", lambda *a, **k: None)
    monkeypatch.setattr(
        assemble, "planned_state", lambda *a, **k: SimpleNamespace(waiver=None, cumulative_core_count=2)
    )
    rendered_page, _ = check_render((*page_inputs, page_words), "a1")
    assert rendered_page.passed, rendered_page
    assert "synthetic (target)" in rendered_page.artifacts["mdx"]
    assert "unchecked override" not in rendered_page.artifacts["mdx"]
    record["gloss_en"] = "wrong"
    assert verify.verify_plan_glosses(plan, store, "a1/synthetic", api, binding_context=context)


def test_private_coverage_and_keyed_commitment(bound):
    root, _api, b = bound
    p = root / "private.jsonl"
    p.write_text(json.dumps(FIXTURE["private"]) + "\n")
    entries = bindings.private_entries(p, bindings.public_entries(a1_reference.INVENTORY_PATH))
    assert list(entries) == [FIXTURE["private"]["locator"]]
    assert b["commitment"] != hashlib.sha256(bindings.canonical(FIXTURE["private"])).hexdigest()
    assert bindings.keyed(FIXTURE["private"], KEY) != bindings.keyed({**FIXTURE["private"], "meaning": "wrong"}, KEY)
    with pytest.raises(ValueError, match="commitment_key_invalid"):
        bindings.keyed({}, b"short")
    p.write_text(p.read_text() * 2)
    with pytest.raises(ValueError, match="coverage"):
        bindings.private_entries(p, bindings.public_entries(a1_reference.INVENTORY_PATH))


@pytest.mark.parametrize(
    "change", ["head", "bindings_sha256", "private_input_commitment", "matcher", "key_id", "leak_scan_scope"]
)
def test_receipt_replay_refused(tmp_path, change):
    payload = {
        "head": "a" * 40,
        "bindings_sha256": "b" * 64,
        "private_input_commitment": "c" * 64,
        "matcher": matcher.VERSION,
        "key_id": "test",
        "leak_scan_scope": {
            "kind": "diff",
            "merge_base": "d" * 40,
            "head": "a" * 40,
            "changed_path_count": 2,
            "commit_count": 1,
        },
    }
    p = tmp_path / "receipt"
    bindings.write_receipt(p, payload, KEY)
    assert bindings.verify_receipt(p, payload, KEY)
    mutated = {**payload, change: "changed"}
    assert not bindings.verify_receipt(p, mutated, KEY)
    receipt = json.loads(p.read_text())
    receipt["seal"] = "0" * 64
    p.write_text(json.dumps(receipt))
    assert not bindings.verify_receipt(p, payload, KEY)


def test_measurement_is_sanitized_and_uses_all_reference_entries(bound):
    _root, api, b = bound
    store = {"level": "a1", "words": [WORD, {**WORD, "id": "W-002", "lemma": "outsider"}]}
    selected, decisions = sense_cli.select_store(
        store,
        bindings.public_entries(a1_reference.INVENTORY_PATH),
        {FIXTURE["private"]["locator"]: FIXTURE["private"]},
        api,
        KEY,
        "test-key",
    )
    assert selected["W-001"]["id"] == b["id"]
    assert decisions == [
        {
            "word": "W-001",
            "id": 2,
            "span_index": 1,
            "atom_index": 0,
            "unknown_label_spans": 0,
            "uncertain_scope_spans": 0,
        },
        {"word": "W-002", "reason": "reference_non_member"},
    ]
    assert "TARGET" not in json.dumps(decisions)


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True, timeout=30).stdout


@pytest.mark.parametrize("unchanged_binding", [False, True])
def test_leak_scan_validated_location_only_and_commit_messages(bound, tmp_path, unchanged_binding):
    root, api, b = bound
    repo = tmp_path / "git-probe"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "fixture@example.invalid")
    git(repo, "config", "user.name", "Fixture")
    (repo / "baseline").write_text("baseline\n")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "baseline")
    base = git(repo, "rev-parse", "HEAD").strip()
    path = repo / "curriculum/l2-uk-en/evidence/a1"
    path.mkdir(parents=True)
    bindings.write(path / bindings.BINDINGS, "a1", {"W-001": b})
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "public binding")
    if unchanged_binding:
        base = git(repo, "rev-parse", "HEAD").strip()
    context = bindings.Context.read("a1", root)
    store = {"words": [WORD]}
    private = {FIXTURE["private"]["locator"]: {**FIXTURE["private"], "meaning": "invented private destination"}}
    result = sense_cli.leak_scan(repo, private, context, store, api, base=base)
    assert result["status"] == "checked", result
    assert result["pr_text"] == "unverified"
    (repo / "leak.txt").write_text("invented private destination\n")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "invented private destination")
    result = sense_cli.leak_scan(repo, private, context, store, api, base=base, pr_text="invented private destination")
    assert result["counts"] == {"committed_files": 1, "commit_messages": 1, "pr_text": 1}
    assert "invented private destination" not in json.dumps(result)
    assert result["signals"] == {"distinctive_wording": 3, "mapping_copy": 0}
    payload = bindings.receipt_payload(root / bindings.BINDINGS, private, KEY, "test", repo)
    (repo / "leak.txt").write_text("dirty")
    with pytest.raises(ValueError, match="clean_head"):
        bindings.receipt_payload(root / bindings.BINDINGS, private, KEY, "test", repo)
    assert payload["head"] == git(repo, "rev-parse", "HEAD").strip()


def test_privacy_exemptions_use_scalar_locations_not_occurrence_counts(bound):
    root, api, _b = bound
    context = bindings.Context.read("a1", root)
    store = {"W-001": WORD}
    content = (root / bindings.BINDINGS).read_bytes()
    # A comment beside the valid span remains visible to the scan.
    content = content.replace(b"span: target", b"span: target # target")
    redacted = sense_cli._redact_validated_locations(content, context, store, api, kind="bindings")
    assert b"# target" in redacted and b"span: target" not in redacted
    # An alias must never move an exemption to a disallowed origin.
    content = content.replace(b"span: target # target", b"span: *value")
    content = b"note: &value target\n" + content
    assert sense_cli._redact_validated_locations(content, context, store, api, kind="bindings") == content


@pytest.mark.parametrize("location", ["unchanged", "changed", "message", "bindings", "words"])
def test_diff_gate_and_report_only_full_tree(bound, tmp_path, location):
    root, api, _b = bound
    repo = tmp_path / "diff-probe"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "fixture@example.invalid")
    git(repo, "config", "user.name", "Fixture")
    level = repo / "curriculum/l2-uk-en/evidence/a1"
    level.mkdir(parents=True)
    leak = "invented private destination"
    path = (
        level / bindings.BINDINGS
        if location == "bindings"
        else level / "_words.yaml"
        if location == "words"
        else repo / "note.txt"
    )
    path.write_text(leak if location in {"unchanged", "bindings", "words"} else "baseline")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "baseline")
    base = git(repo, "rev-parse", "HEAD").strip()
    if location == "changed":
        path.write_text(leak)
    (repo / "changed.txt").write_text("public content")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", leak if location == "message" else "change")
    context = bindings.Context.read("a1", root)
    private = {FIXTURE["private"]["locator"]: {**FIXTURE["private"], "meaning": leak}}
    report = tmp_path / "full-tree.json"
    result = sense_cli.leak_scan(repo, private, context, {"words": [WORD]}, api, base=base, full_tree_report=report)
    assert (result["status"] == "failed") == (location != "unchanged")
    assert result["scope"] == {
        "kind": "diff",
        "merge_base": base,
        "head": git(repo, "rev-parse", "HEAD").strip(),
        "changed_path_count": 2 if location == "changed" else 1,
        "commit_count": 1,
    }
    full = json.loads(report.read_text())
    assert full["status"] == "report_only"
    assert full["counts"]["committed_files"] == int(location != "message")
    if location == "unchanged":
        assert full["suspects"][0]["path"] == "note.txt"
        assert result["suspects"] == []
        assert result["tracked_files"] == 1
    assert leak not in json.dumps(result) + report.read_text()
    plain = sense_cli.leak_scan(repo, private, context, {"words": [WORD]}, api, base=base)
    assert plain == result
    with pytest.raises(ValueError, match="private_output_inside_repository"):
        sense_cli.leak_scan(
            repo, private, context, {"words": [WORD]}, api, base=base, full_tree_report=repo / "report.json"
        )


def test_head_blob_reader_path_filter_and_nonblob(tmp_path):
    repo = tmp_path / "reader"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "fixture@example.invalid")
    git(repo, "config", "user.name", "Fixture")
    (repo / "one").write_bytes(b"one\x00")
    (repo / "two").write_bytes(b"two")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "baseline")
    head = git(repo, "rev-parse", "HEAD").strip()
    git(repo, "update-index", "--add", "--cacheinfo", f"160000,{head},submodule")
    git(repo, "commit", "-qm", "gitlink")
    assert dict(sense_cli._head_blobs(repo)) == {"one": b"one\x00", "two": b"two"}
    assert dict(sense_cli._head_blobs(repo, {"two"})) == {"two": b"two"}
    assert list(sense_cli._head_blobs(repo, set())) == []


@pytest.mark.parametrize(
    "meaning,content,name,expected",
    [
        ("confidential", "An unrelated confidential note", "note.txt", False),
        ("confidential", "synthetic: confidential", "note.txt", True),
        ("confidential", "form-alias: confidential", "note.txt", True),
        ("confidential", "lemma: synthetic\nmeaning: confidential\n", "note.yaml", True),
        ("confidential", '{"lemma": "synthetic",\n"meaning": "confidential"}', "note.json", True),
        ("confidential", r'{"lemma": "\u0073ynthetic", "meaning": "\u0063onfidential"}', "note.json", True),
        ("confidential", "- lemma: synthetic\n- meaning: confidential\n", "note.yaml", False),
        ("target", "synthetic: target", "note.txt", False),
        ("invented private destination", "INVENTED  PRIVATE\nDESTINATION", "note.txt", True),
        ("open dictionary destination", "open dictionary destination", "note.txt", False),
        ("target (an intended destination)", "target (an intended destination)", "note.txt", False),
    ],
)
def test_leak_signals_mapping_wording_and_public_exceptions(bound, tmp_path, meaning, content, name, expected):
    root, api, _b = bound
    api.close()
    with sqlite3.connect(api.sources_db) as db:
        db.execute(
            "UPDATE dmklinger_uk_en SET translations=? WHERE id=1",
            (json.dumps(["open dictionary destination", "target (an intended destination)"]),),
        )
    repo = tmp_path / "scan-probe"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "fixture@example.invalid")
    git(repo, "config", "user.name", "Fixture")
    git(repo, "commit", "--allow-empty", "-qm", "base")
    (repo / name).write_text(content)
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "baseline")
    context = bindings.Context.read("a1", root)
    private = {FIXTURE["private"]["locator"]: {**FIXTURE["private"], "meaning": meaning}}
    store = {"words": [{**WORD, "forms": [{"form": "form-alias"}]}]}
    result = sense_cli.leak_scan(repo, private, context, store, api, base="HEAD^")
    assert (result["status"] == "failed") == expected, result
    assert result["tracked_files"] == 1
    assert result["tracked_bytes"] == len(content.encode())
    assert meaning not in json.dumps(result)
    assert result["pr_text"] == "unverified"


def test_scan_pattern_overlapping_prefixes_boundaries_and_unicode():
    pattern, prefixes = sense_cli._scan_pattern({"cat", "cat food", "food", "é"})
    hits = [term for m in pattern.finditer("cat food cats é") for term in prefixes[m[1]]]
    assert hits == ["cat", "cat food", "food", "é"]
    assert sense_cli._scan_normalize(" E\u0301 \n Cat ") == "é cat"
    empty, _ = sense_cli._scan_pattern(set())
    assert not list(empty.finditer("anything"))


@pytest.mark.parametrize(
    "dictionary,meaning,pos",
    [
        ("kaikki dictionary destination", "kaikki dictionary destination", "noun"),
        ("target", "To TARGET (verb).", "verb"),
    ],
)
def test_leak_scan_public_kaikki_atoms_and_matcher_normalization(
    bound, tmp_path, monkeypatch, dictionary, meaning, pos
):
    root, api, _b = bound
    from types import SimpleNamespace

    monkeypatch.setattr(
        api, "kaikki_rows", lambda lemmas: SimpleNamespace(raw={"synthetic": {"glosses": [dictionary]}})
    )
    repo = tmp_path / "public-probe"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "fixture@example.invalid")
    git(repo, "config", "user.name", "Fixture")
    git(repo, "commit", "--allow-empty", "-qm", "base")
    (repo / "note.txt").write_text(f"synthetic: {meaning}")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "baseline")
    context = bindings.Context.read("a1", root)
    context.inventory[0]["pos"] = pos
    private = {FIXTURE["private"]["locator"]: {**FIXTURE["private"], "meaning": meaning}}
    result = sense_cli.leak_scan(repo, private, context, {"words": [WORD]}, api, base="HEAD^")
    assert result["status"] == "checked"
    assert result["signals"] == {"distinctive_wording": 0, "mapping_copy": 0}


def test_record_texts_preserve_nested_fields_but_not_siblings():
    records = list(
        sense_cli._record_texts(
            {
                "words": [
                    {"lemma": "synthetic", "forms": [{"form": "alias"}], "gloss_ref": {"span": "target"}},
                    {"lemma": "other", "meaning": "confidential"},
                ]
            }
        )
    )
    assert any(all(term in r for term in ("synthetic", "alias", "target")) for r in records)
    assert not any("synthetic" in r and "confidential" in r for r in records)
    cyclic = {"lemma": "synthetic", "meaning": "confidential"}
    cyclic["self"] = cyclic
    assert len(list(sense_cli._record_texts(cyclic))) == 1


def test_head_blobs_uses_one_batch_process_and_committed_bytes(tmp_path, monkeypatch):
    repo = tmp_path / "blob-probe"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "fixture@example.invalid")
    git(repo, "config", "user.name", "Fixture")
    (repo / "one.txt").write_bytes(b"committed\x00binary")
    (repo / "two.txt").write_text("second")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "baseline")
    (repo / "one.txt").write_text("uncommitted")
    original = subprocess.Popen
    calls = []

    def process(command, **kwargs):
        if command[:2] == ["git", "cat-file"]:
            calls.append(command)
        return original(command, **kwargs)

    monkeypatch.setattr(subprocess, "Popen", process)
    assert dict(sense_cli._head_blobs(repo)) == {"one.txt": b"committed\x00binary", "two.txt": b"second"}
    assert calls == [["git", "cat-file", "--batch"]]


def span(text, font="ArialMT", size=9, x=50, y=100):
    return {
        "text": text,
        "font": font,
        "size": size,
        "bbox": [x, y, x + len(text), y + 10],
        "chars": [{"c": c, "bbox": [x + i, y, x + i + 1, y + 10]} for i, c in enumerate(text)],
    }


def line(*spans, y=100):
    return {"bbox": [50, y, 200, y + 10], "spans": list(spans)}


def test_private_wrapped_and_multi_entry_accounting_and_independent_boundaries():
    first = line(
        span("alpha", "Arial-BoldMT"),
        span(", ч., "),
        span("beta", "Arial-BoldMT"),
        span(", ж., "),
        span("target", "Arial-ItalicMT"),
    )
    continuation = line(span("continued", "Arial-ItalicMT", y=110), y=110)
    second = line(
        span("gamma", "Arial-BoldMT", y=120), span(", ч., ", y=120), span("next", "Arial-ItalicMT", y=120), y=120
    )
    rows, accounting = extractor.private_glossary([first, continuation, second], 200)
    expected = proof.raw_glossary_meanings([first, continuation, second], 200)
    assert [r["meaning"].strip() for r in rows] == ["target continued", "target continued", "next"]
    assert [m for _, m in expected] == [r["meaning"].strip() for r in rows]
    assert len(accounting) == 3
    assert accounting[1]["classification"] == "continuation"
    mutation = copy.deepcopy(first)
    mutation["spans"][-1] = span("changed", "Arial-ItalicMT")
    assert proof.raw_glossary_meanings([mutation, continuation, second], 200) != expected


def test_private_output_repository_guard(tmp_path):
    with pytest.raises(ValueError, match="inside_repository"):
        extractor.write_private(Path.cwd() / "private.jsonl", [FIXTURE["private"]], Path.cwd())
    output = tmp_path / "outside.jsonl"
    extractor.write_private(output, [FIXTURE["private"]], Path.cwd())
    assert output.stat().st_mode & 0o777 == 0o600


@pytest.fixture
def review_dispatch(tmp_path):
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    pool = bindings.candidate_list(WORD, [row(["target"])])
    subject = {"word": "W-001", "candidates_sha256": bindings.digest(pool), **pool[0]}
    verdict = {"verdict": "APPROVE", "subject": subject}
    result = tmp_path / "review.result"
    result.write_text(json.dumps(verdict))
    task = {
        "task_id": "review-test",
        "status": "done",
        "review_profile": "ukrainian",
        "review_author_model": "gpt-6.1-sol",
        "effort": "high",
        "model": "claude-opus-5-5",
        "agent": "claude",
        "finished_at": "2026-10-03T00:00:00Z",
        "result_file": str(result),
        "result_sha256": hashlib.sha256(result.read_bytes()).hexdigest(),
        "review_attempt": {"review_id": "review-test", "attempt_id": "attempt-test", "manifest_sha256": "a" * 64},
    }
    record = tasks / "review-test.json"
    record.write_text(json.dumps(task))
    ledger_path = tmp_path / "review-receipts/review-test/attempt-test.jsonl"
    ledger_path.parent.mkdir(parents=True)
    ledger.append(
        ledger_path,
        review_id="review-test",
        attempt_id="attempt-test",
        manifest_sha256="a" * 64,
        tool="verify_words",
        server_version="fixture",
        arguments={"words": ["synthetic"]},
        snapshots={},
        status="ok",
        result="synthetic proof",
    )
    for tool, arguments, result_text in [
        ("query_cefr_level", {"query": "synthetic"}, "No results in PULS CEFR"),
        ("check_russian_shadow", {"word": "synthetic"}, '{"matches_russian":false}'),
    ]:
        ledger.append(
            ledger_path,
            review_id="review-test",
            attempt_id="attempt-test",
            manifest_sha256="a" * 64,
            tool=tool,
            server_version="fixture",
            arguments=arguments,
            snapshots={},
            status="ok",
            result=result_text,
        )
    return tasks, pool, record, result, task, verdict


def test_reviewed_binding_derives_identity_and_approving_subject(review_dispatch):
    tasks, pool, _record, _result, task, _verdict = review_dispatch
    bound = bindings.reviewed_binding(WORD, pool, 1, 0, "review-test", tasks, "gpt-6.1-sol")
    assert bound["reviewer"]["family"] == "anthropic"
    assert bound["reviewer"]["model"] == task["model"]
    assert bound["span"] == "target"


@pytest.mark.parametrize(
    "mutation",
    [
        "failed",
        "running",
        "unrelated",
        "model",
        "hash",
        "word",
        "row",
        "span_index",
        "atom_index",
        "span",
        "candidates",
        "verdict",
        "mcp",
    ],
)
def test_reviewed_binding_rejects_incomplete_unrelated_or_stale(review_dispatch, mutation):
    tasks, pool, record, result, task, verdict = review_dispatch
    if mutation in {"failed", "running"}:
        task["status"] = mutation
    elif mutation == "unrelated":
        task["review_profile"] = "code"
    elif mutation == "model":
        task["model"] = "gpt-6.1-sol"
    elif mutation == "hash":
        task["result_sha256"] = "0" * 64
    elif mutation == "mcp":
        task["review_attempt"] = {}
    else:
        field = {"word": "word", "row": "row_sha256", "candidates": "candidates_sha256"}.get(mutation, mutation)
        if mutation == "verdict":
            verdict["verdict"] = "REJECT"
        else:
            verdict["subject"][field] = "changed"
        result.write_text(json.dumps(verdict))
        task["result_sha256"] = hashlib.sha256(result.read_bytes()).hexdigest()
    record.write_text(json.dumps(task))
    with pytest.raises(ValueError):
        bindings.reviewed_binding(WORD, pool, 1, 0, "review-test", tasks, "gpt-6.1-sol")


@pytest.mark.parametrize("command", ["select", "bind"])
def test_cli_help_exits(command, capsys):
    with pytest.raises(SystemExit) as result:
        sense_cli.main(["--help"], command=command)
    assert result.value.code == 0
    assert "Exit codes" in capsys.readouterr().out


@pytest.mark.parametrize(
    "mode",
    [
        "dry",
        "write",
        "check",
        "replay",
        "commitment",
        "leak",
        "missing_key",
        "missing_receipt",
        "pr_timeout",
        "pr_unavailable",
        "pr_malformed",
        "pr_available",
        "full_tree",
        "full_tree_without_check",
        "full_tree_inside",
    ],
)
def test_select_cli_mutations_and_receipt(bound, monkeypatch, capsys, mode):
    root, api, b = bound
    (root / "_words.yaml").write_text(yaml.safe_dump({"level": "a1", "words": [WORD]}))
    private = root / "private.jsonl"
    private.write_text(json.dumps(FIXTURE["private"]) + "\n")
    key = root / "key"
    key.write_bytes(KEY)
    receipt = root / "receipt"
    monkeypatch.setattr(sources, "Sources", lambda **kw: api)
    monkeypatch.setattr(bindings, "git", lambda repo, *args: b"" if args[0] == "status" else b"a" * 40)
    monkeypatch.setattr(
        sense_cli,
        "leak_scan",
        lambda *a, **k: {
            "status": "failed" if mode == "leak" else "checked",
            "pr_text": "unverified",
            "scope": {"kind": "diff"},
        },
    )
    args = ["a1", "--evidence-dir", str(root), "--private-input", str(private)]
    if mode.startswith("pr_"):
        original_run = subprocess.run

        def run(command, **kwargs):
            if command[0] != "gh":
                return original_run(command, **kwargs)
            assert kwargs["timeout"] == 60
            if mode == "pr_timeout":
                raise subprocess.TimeoutExpired(command, 60)
            text = (
                "invalid"
                if mode == "pr_malformed"
                else json.dumps({"title": "public", "body": "public", "comments": []})
            )
            return subprocess.CompletedProcess(command, int(mode == "pr_unavailable"), text)

        monkeypatch.setattr(subprocess, "run", run)

        def scan(*args, **kwargs):
            assert kwargs["pr_text"] == ("public public" if mode == "pr_available" else None)
            return {
                "status": "checked",
                "pr_text": "scanned" if kwargs["pr_text"] else "unverified",
                "scope": {"kind": "diff"},
            }

        monkeypatch.setattr(sense_cli, "leak_scan", scan)
        args += ["--pr", "1"]
    if mode.startswith("full_tree"):
        report = Path.cwd() / "batch_state/report.json" if mode == "full_tree_inside" else root / "tree-report.json"
        args += ["--full-tree-report", str(report)]
    if mode not in {"dry", "full_tree_without_check"}:
        args += ["--write" if mode == "write" else "--check"]
        if mode != "missing_key":
            args += ["--key-file", str(key), "--key-id", "test-key"]
        if mode not in {"write", "missing_receipt"}:
            args += ["--receipt", str(receipt)]
    if mode == "commitment":
        bindings.write(root / bindings.BINDINGS, "a1", {"W-001": {**b, "commitment": "0" * 64}})
    if mode == "replay":
        bindings.write_receipt(receipt, {"head": "stale"}, KEY)
        args += ["--verify-receipt"]
    result = sense_cli.main(args)
    assert result == int(
        mode
        in {
            "commitment",
            "replay",
            "leak",
            "missing_key",
            "missing_receipt",
            "full_tree_without_check",
            "full_tree_inside",
        }
    )
    output = capsys.readouterr().out
    assert "TARGET" not in output
    if mode in {"check", "full_tree"}:
        payload = json.loads(receipt.read_text())["payload"]
        assert payload["head"] == "a" * 40
        assert payload["leak_scan_scope"] == {"kind": "diff"}
        assert bindings.verify_receipt(receipt, payload, KEY)


@pytest.mark.parametrize("atom_index", [0, 1])
def test_bind_cli_candidate_list_and_review(bound, review_dispatch, monkeypatch, capsys, atom_index):
    root, api, _b = bound
    # The approving subject must match the API's complete current list.
    tasks, _pool, record, result, task, verdict = review_dispatch
    pool = bindings.candidate_list(WORD, api.gloss_rows([("synthetic", "noun")]).raw[("synthetic", "noun")])
    selected = next(c for c in pool if c["span"] == ("target" if atom_index == 0 else "goal"))
    verdict["subject"] = {"word": "W-001", "candidates_sha256": bindings.digest(pool), **selected}
    result.write_text(json.dumps(verdict))
    task["result_sha256"] = hashlib.sha256(result.read_bytes()).hexdigest()
    record.write_text(json.dumps(task))
    (root / "_words.yaml").write_text(yaml.safe_dump({"level": "a1", "words": [WORD]}))
    monkeypatch.setattr(sources, "Sources", lambda **kw: api)
    monkeypatch.setattr(sense_cli, "tasks_dir", lambda: tasks)
    args = ["a1", "--evidence-dir", str(root), "--word", "W-001"]
    assert sense_cli.main([*args, "--candidates"], command="bind") == 0
    assert "candidates_sha256" in capsys.readouterr().out
    assert (
        sense_cli.main(
            [
                *args,
                "--row-id",
                "2",
                "--span-index",
                "1",
                "--atom-index",
                str(atom_index),
                "--review-task",
                "review-test",
                "--author-model",
                "gpt-6.1-sol",
            ],
            command="bind",
        )
        == 0
    )
    assert bindings.load(root / bindings.BINDINGS, "a1")["W-001"]["method"] == "reviewed.v1"
    private = root / "private.jsonl"
    private.write_text(json.dumps(FIXTURE["private"]) + "\n")
    key = root / "key"
    key.write_bytes(KEY)
    monkeypatch.setattr(bindings, "git", lambda repo, *args: b"" if args[0] == "status" else b"a" * 40)
    monkeypatch.setattr(
        sense_cli,
        "leak_scan",
        lambda *a, **k: {"status": "checked", "pr_text": "unverified", "scope": {"kind": "diff"}},
    )
    assert (
        sense_cli.main(
            [
                "a1",
                "--evidence-dir",
                str(root),
                "--private-input",
                str(private),
                "--check",
                "--key-file",
                str(key),
                "--key-id",
                "test-key",
                "--receipt",
                str(root / "receipt"),
            ]
        )
        == 0
    )


def test_extraction_and_proof_private_modes_synthetic_document(tmp_path, monkeypatch, capsys):
    lexical_line = line(span("alpha", "Arial-BoldMT"), span(", ч., "), span("target", "Arial-ItalicMT"))
    repeated_line = line(
        span("alpha", "Arial-BoldMT", y=120), span(", ч., ", y=120), span("other", "Arial-ItalicMT", y=120), y=120
    )
    appendix_left = line(span("аа", "Arial-BoldMT", 10, x=80, y=400), y=400)
    appendix_left["bbox"] = [80, 400, 100, 410]
    appendix_right = {"bbox": [280, 400, 320, 410], "spans": [span("бб", "Arial-BoldMT", 10, x=280, y=400)]}
    appendix_meaning = {"bbox": [480, 400, 530, 410], "spans": [span("target", "Arial-ItalicMT", 10, x=480, y=400)]}

    class Page:
        def __init__(self, index):
            self.index = index

        def get_text(self, mode):
            lines = (
                [lexical_line, repeated_line]
                if self.index == 199
                else [appendix_left, appendix_right, appendix_meaning]
                if self.index == 216
                else []
            )
            return {"blocks": [{"lines": lines}]}

    class Document:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def __getitem__(self, index):
            return Page(index)

    monkeypatch.setattr(extractor.pymupdf, "open", lambda _: Document())
    public = [
        extractor.headword_fields("alpha", "noun", 200),
        extractor.headword_fields("alpha", "noun", 200),
        extractor.headword_fields("аа", "verb", 217, "vp-001"),
        extractor.headword_fields("бб", "verb", 217, "vp-001"),
    ]
    inventory = tmp_path / "inventory.yaml"
    inventory.write_text(yaml.safe_dump({"sources": [{"headwords": public}]}))
    output = tmp_path / "private.jsonl"
    args = ["--pdf", str(tmp_path / "fake.pdf"), "--inventory", str(inventory)]
    assert extractor.main([*args, "--private-meanings", str(output)]) == 0
    assert proof.main([*args, "--meanings", str(output)]) == 0
    report = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert report["actual_entries"] == 4 and report["unexplained_differences"] == 0
    rows = [json.loads(l) for l in output.read_text().splitlines()]
    rows[0]["meaning"], rows[1]["meaning"] = rows[1]["meaning"], rows[0]["meaning"]
    output.write_text("".join(json.dumps(r) + "\n" for r in rows))
    assert proof.main([*args, "--meanings", str(output)]) == 1
    swapped = json.loads(capsys.readouterr().out)
    assert swapped["unexplained_differences"] == 0 and len(swapped["mismatch_locators"]) == 2
    rows[0]["meaning"], rows[1]["meaning"] = rows[1]["meaning"], rows[0]["meaning"]
    rows[0]["meaning"] = "wrong"
    output.write_text("".join(json.dumps(r) + "\n" for r in rows))
    assert proof.main([*args, "--meanings", str(output)]) == 1
    assert "wrong" not in capsys.readouterr().out


def test_cli_does_not_echo_untrusted_exception_text(bound, monkeypatch, capsys):
    root, _api, _b = bound
    monkeypatch.setattr(Path, "read_text", lambda *a, **k: (_ for _ in ()).throw(ValueError("privateword")))
    assert sense_cli.main(["a1", "--evidence-dir", str(root), "--private-input", "private"]) == 1
    assert "privateword" not in capsys.readouterr().out


def test_private_output_symlink_leaf_cannot_write_inside_git(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    outside = tmp_path / "private.jsonl"
    link = repo / "private.jsonl"
    link.symlink_to(outside)
    with pytest.raises(ValueError, match="inside_repository"):
        extractor.write_private(link, [FIXTURE["private"]], repo)
    assert not outside.exists()


@pytest.mark.parametrize(
    "mutation", ["unqualified", "author_missing", "cursor_unknown", "unrelated_sources", "unavailable_sources"]
)
def test_review_role_author_and_sources_provenance_rejected(review_dispatch, mutation):
    tasks, pool, record, _result, task, _verdict = review_dispatch
    if mutation == "unqualified":
        task["model"] = "claude-sonnet-5-5"
    elif mutation == "author_missing":
        task.pop("review_author_model")
    elif mutation == "cursor_unknown":
        task["agent"] = "cursor"
    elif mutation == "unrelated_sources":
        other = {**WORD, "lemma": "unrelated"}
        with pytest.raises(ValueError, match="sources_unproven"):
            bindings.reviewed_binding(other, pool, 1, 0, "review-test", tasks, "gpt-6.1-sol")
        return
    else:
        attempt = {**task["review_attempt"], "attempt_id": "unavailable"}
        task["review_attempt"] = attempt
        ledger_path = tasks.parent / "review-receipts/review-test/unavailable.jsonl"
        ledger.append(
            ledger_path,
            review_id="review-test",
            attempt_id="unavailable",
            manifest_sha256="a" * 64,
            tool="verify_words",
            server_version="fixture",
            arguments={"words": ["synthetic"]},
            snapshots={},
            status="ok",
            result='{"status":"unavailable"}',
        )
    record.write_text(json.dumps(task))
    with pytest.raises(ValueError):
        bindings.reviewed_binding(WORD, pool, 1, 0, "review-test", tasks, "gpt-6.1-sol")


@pytest.mark.parametrize("invalidate", [False, True])
def test_partial_build_revalidates_carried_reference_gloss(bound, monkeypatch, synthetic_vesum, invalidate):
    root, api, b = bound
    with sqlite3.connect(synthetic_vesum) as db:
        db.execute(
            "INSERT INTO forms_all VALUES (?,?,?,?,?,?,?,?)",
            (5, 50, "outsider", "outsider", "noun", "noun:inanim:f:v_naz", "", "synthetic"),
        )
    monkeypatch.setattr(
        sources.stress,
        "verify_stress",
        lambda w, **kw: {
            "status": "ok",
            "matches": [
                {
                    "stressed_form": f"{w}-stressed",
                    "unstressed_form": w,
                    "vowel_index": 0,
                    "vowel_indices": [0],
                    "vesum": None,
                    "required_tags": [],
                    "override_applied": False,
                }
            ],
            "source": {"digest": "t" * 64},
        },
    )
    req = root / "request.yaml"
    req.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "level": "a1",
                "words": [
                    {"lemma": "synthetic", "pos": "noun", "want": "new", "entry": {"source": "vesum", "entry_id": 10}}
                ],
            }
        )
    )
    words.build_words("a1", req, evidence_dir=root, sources_instance=api, mcp_commit="a" * 40)
    # The second request owns another word, so the existing gloss must be rechecked.
    if invalidate:
        bindings.write(root / bindings.BINDINGS, "a1", {"W-001": {**b, "span_index": 0}})
    req.write_text(
        yaml.safe_dump(
            {"request_schema": 1, "level": "a1", "words": [{"lemma": "outsider", "pos": "noun", "want": "new"}]}
        )
    )
    result = words.build_words("a1", req, evidence_dir=root, sources_instance=api, mcp_commit="a" * 40)
    carried = next(w for w in result["store"]["words"] if w["id"] == "W-001")
    if invalidate:
        assert "gloss_en" not in carried and "gloss_ref" not in carried
        assert any(d["word_id"] == "W-001" and d["reason"] == "reference_binding_invalid" for d in result["unglossed"])
    else:
        assert carried["gloss_en"] == carried["gloss_ref"]["span"] == b["span"]


@pytest.mark.parametrize(
    "dictionary,meaning,display,index",
    [
        ("stadium (venue where sporting events are held)", "stadium", "stadium", 0),
        ("egg (an oval object laid by a bird)", "egg", "egg", 0),
        ("fox (Vulpes)", "fox", "fox", 0),
        ("page (one side of a leaf of a book)", "page", "page", 0),
        ("(possessive) our, ours", "our", "our", 0),
        ("(possessive) our, ours", "ours", "ours", 0),
        ("to go (transitive)", "go", "to go", 0),
        ("Target / Goal (an intended destination)", "goal", "Goal", 1),
        ("target (countable), goal", "goal", "goal", 0),
    ],
)
def test_definition_grammar_and_exact_source_atom(dictionary, meaning, display, index):
    word = {**WORD, "pos": "verb"} if dictionary.startswith("to ") else WORD
    result = matcher.select(word, [row([dictionary], pos=word["pos"])], meaning)
    assert result.gloss == result.ref["span"] == display
    assert result.ref["atom_index"] == index
    assert display in dictionary


@pytest.mark.parametrize("label", sorted(matcher.GRAMMATICAL_ANNOTATIONS))
@pytest.mark.parametrize("shape", ["({label}) target, goal", "target ({label}), goal", "target / goal ({label})"])
def test_grammatical_labels_ignored_at_every_position(label, shape):
    text = shape.format(label=label)
    assert matcher.select(WORD, [row([text])], "target").gloss == "target"
    assert matcher.select(WORD, [row([text])], "goal").gloss == "goal"


@pytest.mark.parametrize("labels", [matcher.RESTRICTING_LABELS, matcher.TOPIC_LABELS])
def test_closed_restricting_and_domain_labels_require_reference_label(labels):
    for label, canonical in labels.items():
        for text in (f"({label}) target", f"target ({label})", f"target (({label}) an intended destination)"):
            assert matcher.select(WORD, [row([text])], "target").reason == "reference_no_match"
            selected = matcher.select(WORD, [row([text])], f"target ({canonical})")
            assert selected.gloss == "target", (label, text)
            assert selected.candidates[0]["labels"] == (canonical,)


@pytest.mark.parametrize(
    "dictionary,meaning",
    [
        ("(historical) circus (in ancient Rome)", "circus"),
        ("venom ((figurative) malice)", "malice"),
        ("venom ((figurative) malice)", "venom"),
        ("(mechanics) tooth (of a gear)", "tooth"),
        ("(historical) target, goal (old usage)", "target"),
        ("(historical) target, goal (old usage)", "goal"),
        ("(historical) target; goal (old usage)", "goal"),
        ("target / goal (mechanical)", "target"),
        ("target (anatomical)", "target (mechanical)"),
        ("billion (short scale)", "billion"),
        ("billion (long scale)", "billion (short scale)"),
        ("target (sports)", "target (music)"),
    ],
)
def test_driver_observed_restrictions_cannot_escape_group(dictionary, meaning):
    assert matcher.select(WORD, [row([dictionary])], meaning).reason == "reference_no_match"


def test_unrestricted_definition_wins_over_historical_circus():
    result = matcher.select(
        WORD, [row(["(historical) circus (in ancient Rome)", "circus (company that performs acrobatics)"])], "circus"
    )
    assert result.gloss == "circus"
    assert result.ref["span_index"] == 1
    assert result.candidates[0]["definitions"] == ("company that performs acrobatics",)


@pytest.mark.parametrize(
    "text",
    [
        "(unknown label) target",
        "(possessive, invented-label) target",
        "target (rare, invented-label)",
        "target ((rare, invented-label) a destination)",
        "target ((unknown label) a destination)",
    ],
)
def test_unknown_labels_excluded_and_counted(text):
    report = {}
    assert matcher.candidates(WORD, [row([text])], report=report) == []
    assert report == {"unknown_label_spans": 1}
    assert matcher.select(WORD, [row([text])], "target").reason == "reference_no_match"


@pytest.mark.parametrize(
    "text", ["target (one), goal (two)", "target (historical), goal", "target (broken", "((rare) target"]
)
def test_uncertain_scope_is_not_split(text):
    assert matcher.atoms(text, "noun") == ()
    assert not matcher.candidates(WORD, [row([text])])


def test_atom_provenance_rederived_and_missing_index_refused():
    dictionary = row(["target / Goal (an intended destination)"])
    result = matcher.select(WORD, [dictionary], "goal")
    b = bindings.reference_binding(WORD, result.ref, FIXTURE["private"], KEY, "test-key")
    context = bindings.Context("a1", {"W-001": b}, [{"lemma": "synthetic", "locator": b["locator"]}])
    assert context.select(WORD, [dictionary], None).gloss == "Goal"
    b["atom_index"] = 0
    assert context.select(WORD, [dictionary], None).reason == "reference_binding_invalid"
    b.pop("atom_index")
    assert context.select(WORD, [dictionary], None).reason == "reference_binding_invalid"


def test_definitions_are_evidence_but_same_display_and_labels_collapse():
    result = matcher.select(
        WORD, [row(["target (first definition)"], 7), row(["target (second definition)"], 3)], "target"
    )
    assert result.ref["id"] == 3
    assert result.gloss == "target"
    assert result.candidates[0]["definitions"] == ("second definition",)
    assert matcher.select(WORD, [row(["Target", "target"])], "target").reason == "reference_ambiguous"


def test_atoms_only_split_documented_separators():
    assert matcher.source_atoms("target / goal, aim; object") == ("target", "goal", "aim", "object")
    assert matcher.atoms("target or goal", "noun") == ("target or goal",)
    assert matcher.select(WORD, [row(["target or goal"])], "target").reason == "reference_no_match"


def test_row_parsing_invalid_and_non_string_entries():
    assert matcher.row_spans(row("not-json")) == []
    assert matcher.row_spans({"translations": "bad JSON"}) == []
    assert matcher.row_spans(row([None, "target"])) == [("target", "target")]
    assert matcher.classify("(rare)").reason == "uncertain_scope"


def test_definition_part_of_sense_signature():
    pool = matcher.candidates(WORD, [row(["target (first definition)", "target (second definition)"])])
    assert matcher.signature(pool[0]) != matcher.signature(pool[1])
    assert matcher.display_signature(pool[0]) == matcher.display_signature(pool[1])


def test_unknown_label_counts_in_store_diagnostics(bound):
    _root, api, _b = bound
    api.close()
    with sqlite3.connect(api.sources_db) as db:
        db.execute("UPDATE dmklinger_uk_en SET translations=? WHERE id=2", (json.dumps(["(unknown label) target"]),))
    _selected, decisions = sense_cli.select_store(
        {"level": "a1", "words": [WORD]},
        bindings.public_entries(a1_reference.INVENTORY_PATH),
        {FIXTURE["private"]["locator"]: FIXTURE["private"]},
        api,
    )
    assert decisions[0]["unknown_label_spans"] == 1
    assert decisions[0]["reason"] == "reference_no_match"
    assert "TARGET" not in json.dumps(decisions)


@pytest.mark.parametrize(
    "label",
    [
        "familiar",
        "childish",
        "endearing",
        "endearment",
        "proscribed",
        "jocular",
        "technical",
        "colloq",
        "colloquial",
        "colloquially",
        "obsolescent",
        "uncommon",
        "rude",
        "taboo",
        "polite",
        "non standard",
        "figuratively",
        "archaically",
        "dialectally",
    ],
)
def test_shared_register_vocabulary_restricts_reference_selection(label):
    assert sources._REGISTER_LABEL.fullmatch(label)
    assert sources._register_note(label)
    assert matcher.select(WORD, [row([f"target ({label} address)"])], "target").reason == "reference_no_match"
    assert matcher.select(WORD, [row([f"target ({label})"])], f"target ({label})").gloss == "target"


@pytest.mark.parametrize("label", sorted(matcher.TOPIC_LABELS))
def test_topic_colon_prefix_must_match_reference_labels(label):
    assert matcher.select(WORD, [row([f"{label}: target"])], "target").reason == "reference_no_match"
    result = matcher.select(WORD, [row([f"{label}: target"])], f"target ({label})")
    assert result.gloss == "target"
    assert matcher.classify("unknown-topic: target").reason == "unknown_label"


@pytest.mark.parametrize("label", [*sorted(matcher.TOPIC_LABELS), "unknown-topic"])
@pytest.mark.parametrize("prefix", [False, True])
def test_topic_senses_compete_but_cannot_be_selected_bare(label, prefix):
    labelled = f"{label}: target" if prefix else f"target ({label})"
    result = matcher.select(WORD, [row([labelled, "target (an unrelated definition)"])], "target")
    expected = "reference_ambiguous" if label != "unknown-topic" or prefix else None
    assert result.reason == expected
    alone = matcher.select(WORD, [row([labelled])], "target")
    assert alone.reason == (None if label == "unknown-topic" and not prefix else "reference_no_match")
    if label == "unknown-topic" and prefix:
        assert matcher.candidates(WORD, [row([labelled])]) == []


@pytest.mark.parametrize("label", sorted(set(matcher.RESTRICTING_LABELS.values()) - set(matcher.TOPIC_LABELS.values())))
def test_register_mismatch_does_not_compete(label):
    assert matcher.select(WORD, [row([f"target ({label})", "target"])], "target").gloss == "target"
    assert matcher.select(WORD, [row([f"anatomy: target ({label})", "target"])], "target").gloss == "target"
    assert matcher.select(WORD, [row([f"{label}: target", "target"])], "target").gloss == "target"


@pytest.mark.parametrize("label", ["ukraine", "us", "uk"])
def test_region_names_only_restrict_whole_edge_or_nested_labels(label):
    assert matcher.classify(f"target (capital city of {label})").labels == ()
    assert matcher.select(WORD, [row([f"target (capital city of {label})"])], "target").gloss == "target"
    for text in (f"({label}) target", f"target ({label})", f"target (({label}) a destination)"):
        assert matcher.select(WORD, [row([text])], "target").reason == "reference_no_match"
        assert matcher.select(WORD, [row([text])], f"target ({label})").gloss == "target"


@pytest.mark.parametrize("ambiguous", [False, True])
def test_multiple_inventory_entries_distinguish_no_match_from_ambiguity(bound, ambiguous):
    _root, api, _b = bound
    inventory = [{"lemma": "synthetic", "locator": str(i)} for i in range(2)]
    meanings = ("TARGET.", "goal") if ambiguous else ("absent", "missing")
    private = {str(i): {"meaning": value} for i, value in enumerate(meanings)}
    _selected, decisions = sense_cli.select_store({"level": "a1", "words": [WORD]}, inventory, private, api)
    assert decisions[0]["reason"] == ("reference_ambiguous" if ambiguous else "reference_no_match")


def test_reviewed_binding_requires_exact_atom_index(review_dispatch):
    tasks, _pool, record, result, task, verdict = review_dispatch
    pool = bindings.candidate_list(WORD, [row(["target / Goal (an intended destination)"])])
    verdict["subject"] = {"word": "W-001", "candidates_sha256": bindings.digest(pool), **pool[1]}
    result.write_text(json.dumps(verdict))
    task["result_sha256"] = hashlib.sha256(result.read_bytes()).hexdigest()
    record.write_text(json.dumps(task))
    b = bindings.reviewed_binding(WORD, pool, 1, 0, "review-test", tasks, atom_index=1)
    assert b["span"] == "Goal" and b["atom_index"] == 1
    with pytest.raises(ValueError, match="review_subject_stale_or_unapproved"):
        bindings.reviewed_binding(WORD, pool, 1, 0, "review-test", tasks, atom_index=0)
