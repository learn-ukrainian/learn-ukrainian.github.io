"""Source-free development evidence, never independent real-source reconciliation."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys

import pytest

from scripts.projects.open_model_data import source_completeness_manifest as manifest

IDS = (
    "SRC-ULIF",
    "SRC-VESUM",
    "SRC-SUM20",
    "SRC-VTS",
    "SRC-GRAC",
    "SRC-LITERARY",
    "SRC-TEXTBOOK",
    "SRC-PRAVOPYS",
    "SRC-ANTONENKO",
    "SRC-KARAVANSKY",
    "SRC-UAGEC",
    "SRC-ESUM",
    "SRC-HRINCHENKO",
    "SRC-PHRASEOLOGY",
    "SRC-SPECIALIST",
    "SRC-PULS",
    "SRC-CURRICULUM",
    "SRC-STRESS",
    "SRC-SUM11",
    "SRC-LEGACY123",
)
STAGES = (
    "acquisition",
    "raw_custody",
    "parsing",
    "admission",
    "consumer:Atlas",
    "consumer:Practice",
    "consumer:dataset",
)
MODULE = "scripts.projects.open_model_data.source_completeness_manifest"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return digest(path.read_bytes())


class Fixture:
    def __init__(self, root):
        self.root = root
        self.raw = root / "capture.txt"
        self.raw.write_bytes(b"literal source-free capture\n")
        self.ref = {
            "path": "capture.txt",
            "sha256": digest(self.raw.read_bytes()),
            "schema_version": "opaque-bytes.v1",
            "locator": "fixture:page/1",
        }
        self.paths = {
            name: root / f"{name}.json"
            for name in ("requirements", "source_manifest", "stage_evidence", "lexical_universe", "legacy_membership")
        }
        requirements = []
        ranges = []
        for i, requirement_id in enumerate(IDS):
            gap = "G-LEGACY" if requirement_id == "SRC-LEGACY123" else requirement_id.replace("SRC-", "G-")
            fields = [{"name": "value", "applicability": "applicable", "reason": "fixture source role"}]
            if requirement_id == "SRC-VESUM":
                fields.append({"name": "stress", "applicability": "not_applicable", "reason": "VESUM has no stress"})
            requirements.append(
                {
                    "requirement_id": requirement_id,
                    "gap": gap,
                    "owner": "open-model-data",
                    "fields": fields,
                    "consumers": ["Atlas", "Practice", "dataset"],
                }
            )
            boundary = {
                "range_id": f"range-{i}",
                "requirement_id": requirement_id,
                "edition": "literal-fixture-edition",
                "range": "entire finite fixture",
                "snapshot": "fixture-snapshot",
                "source_locator": f"fixture:register/{i}",
                "register_kind": "checked_register" if i == 0 else "source_index",
                "retrieved_at": "2026-09-28T22:51:41Z",
            }
            # Exact repeated spelling, separate homonym/sense, nested order and occurrences.
            count = 3 if i == 0 else 123 if i == 19 else 1
            units = [
                {
                    "identity": {
                        "key": "fixture-key",
                        "homonym": "2" if n == 2 else "1",
                        "sense": "sense-B" if n == 1 else "sense-A",
                        "path": ["group", "nested", str(n)],
                        "occurrence": n,
                    },
                    "locator": f"fixture:register/{i}/unit/{n}",
                    "sha256": self.ref["sha256"],
                }
                for n in range(count)
            ]
            index_path = root / f"index-{i}.json"
            index_sha = write(index_path, {"schema_version": "source-index.v1", **boundary, "units": units})
            ranges.append(
                {
                    **boundary,
                    "membership": "KNOWN",
                    "units": units,
                    "index": {
                        "path": index_path.name,
                        "sha256": index_sha,
                        "schema_version": "source-index.v1",
                        "locator": boundary["source_locator"],
                    },
                }
            )
        self.docs = {
            "requirements": {
                "schema_version": "source-requirements.v1",
                "matrix_sha256": digest(manifest.MATRIX.read_bytes()),
                "requirements": requirements,
            },
            "source_manifest": {
                "schema_version": "source-manifest.v1",
                "requirements_sha256": "0" * 64,
                "origin": "source_side",
                "ranges": ranges,
            },
            "stage_evidence": {
                "schema_version": "stage-evidence.v1",
                "source_manifest_sha256": "0" * 64,
                "records": [],
            },
        }
        for row in ranges:
            for unit in row["units"]:
                for stage in STAGES:
                    self.docs["stage_evidence"]["records"].append(
                        {
                            "range_id": row["range_id"],
                            "identity": unit["identity"],
                            "source_unit_sha256": unit["sha256"],
                            "field": "value",
                            "stage": stage,
                            "state": "verified-complete",
                            "reason": "literal structural fixture evidence",
                            "evidence": [dict(self.ref)],
                            "absence_evidence": None,
                        }
                    )
        for name, row in [("lexical_universe", ranges[0]), ("legacy_membership", ranges[19])]:
            members = [
                {
                    "member_id": f"fixture-member-{i}",
                    "locator": unit["locator"],
                    "source_units": [{"range_id": row["range_id"], "identity": unit["identity"]}],
                }
                for i, unit in enumerate(row["units"])
            ]
            index_path = root / f"{name}-index.json"
            role = "original_legacy123" if name == "legacy_membership" else "lexical_universe"
            index_sha = write(
                index_path,
                {
                    "schema_version": "membership-index.v1",
                    "origin": "source_side",
                    "members": members,
                    "provenance": {
                        "source_locator": f"fixture:{role}/original",
                        "source_snapshot": "fixture-source-version",
                        "consumer_version": "fixture-consumer-v1",
                        "role": role,
                    },
                },
            )
            self.docs[name] = {
                "schema_version": name.replace("_", "-") + ".v1",
                "source_manifest_sha256": "0" * 64,
                "membership": "KNOWN",
                "members": members,
                "index": {
                    "path": index_path.name,
                    "sha256": index_sha,
                    "schema_version": "membership-index.v1",
                    "locator": f"fixture:{role}/original",
                },
            }
            if name == "legacy_membership":
                self.docs[name]["expected_obligation"] = 123
        self.save()

    def save(self):
        req_sha = write(self.paths["requirements"], self.docs["requirements"])
        self.docs["source_manifest"]["requirements_sha256"] = req_sha
        source_sha = write(self.paths["source_manifest"], self.docs["source_manifest"])
        for name in ("stage_evidence", "lexical_universe", "legacy_membership"):
            self.docs[name]["source_manifest_sha256"] = source_sha
            write(self.paths[name], self.docs[name])

    def source_index(self, index):
        row = self.docs["source_manifest"]["ranges"][index]
        value = {key: value for key, value in row.items() if key not in ("membership", "index")}
        value["schema_version"] = "source-index.v1"
        row["index"]["sha256"] = write(self.root / row["index"]["path"], value)

    def cli(self, out="output", *, extra=None, tmpdir=None):
        args = [sys.executable, "-m", MODULE]
        for name, path in self.paths.items():
            args += ["--" + name.replace("_", "-"), str(path)]
        args += ["--output-dir", str(self.root / out)]
        return subprocess.run(
            args + (extra or []),
            capture_output=True,
            text=True,
            env={**os.environ, "TMPDIR": str(tmpdir or self.root)},
            check=False,
            timeout=60,
        )

    def receipt(self, out="output"):
        return json.loads((self.root / out / "manifest-receipt.json").read_text())

    def source_output(self, requirement="SRC-ULIF", out="output"):
        return json.loads((self.root / out / f"{requirement}.json").read_text())


@pytest.fixture
def fixture(tmp_path):
    return Fixture(tmp_path)


def test_complete_finite_inventory_cli_callable_and_rerun(fixture):
    result = fixture.cli()
    assert (result.returncode, result.stderr) == (0, "")
    assert json.loads(result.stdout) == {"status": "STRUCTURALLY_ACCOUNTED", "gap_count": 0}
    receipt = fixture.receipt()
    assert receipt["required_requirement_count"] == 20
    assert receipt["supplied_unit_count"] == 144
    assert receipt["lexical_member_count"] == 3
    assert receipt["legacy_member_count"] == receipt["legacy_expected_obligation"] == 123
    assert receipt["gaps"] == []
    assert receipt["programme_completeness"] == "UNRESOLVED"
    assert len(receipt["external_prerequisites"]) == 4
    assert [r["requirement_id"] for r in receipt["requirements"]] == list(IDS)
    assert receipt["stage_counts"] == {
        stage: {"verified-complete": 144, "missing": 0, "corrupt": 0, "quarantined": 0, "genuinely_absent": 0}
        for stage in STAGES
    }
    units = fixture.source_output()["units"]
    assert [u["identity"] for u in units] == [
        {"key": "fixture-key", "homonym": "1", "sense": "sense-A", "path": ["group", "nested", "0"], "occurrence": 0},
        {"key": "fixture-key", "homonym": "1", "sense": "sense-B", "path": ["group", "nested", "1"], "occurrence": 1},
        {"key": "fixture-key", "homonym": "2", "sense": "sense-A", "path": ["group", "nested", "2"], "occurrence": 2},
    ]
    assert [u["ordinal"] for u in units] == [0, 1, 2]
    assert fixture.source_output("SRC-VESUM")["units"][0]["fields"][-1] == {
        "field": "stress",
        "state": "not_applicable",
        "reason": "VESUM has no stress",
    }
    for output in receipt["outputs"]:
        raw = (fixture.root / "output" / output["path"]).read_bytes()
        assert (digest(raw), len(raw)) == (output["sha256"], output["bytes"])
    for name, path in fixture.paths.items():
        assert receipt["inputs"][name]["sha256"] == digest(path.read_bytes())
    previous = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in (fixture.root / "output").iterdir()}
    assert fixture.cli().returncode == 0
    assert previous == {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in (fixture.root / "output").iterdir()}
    outputs, callable_receipt = manifest.account(fixture.paths)
    assert callable_receipt["status"] == "STRUCTURALLY_ACCOUNTED"
    assert outputs["SRC-ULIF.json"] == (fixture.root / "output/SRC-ULIF.json").read_bytes()


@pytest.mark.parametrize(
    ("state", "stage", "reason"),
    [
        ("missing", "acquisition", "not acquired"),
        ("corrupt", "raw_custody", "damaged capture"),
        ("missing", "parsing", "parser loss"),
        ("quarantined", "admission", "retained conflict"),
        ("missing", "consumer:Practice", "unchecked not_found"),
    ],
)
def test_stage_gaps_are_independent_never_absence(fixture, state, stage, reason):
    record = next(r for r in fixture.docs["stage_evidence"]["records"] if r["stage"] == stage)
    record.update(state=state, reason=reason)
    fixture.save()
    assert fixture.cli().returncode == 2
    receipt = fixture.receipt()
    assert receipt["gap_count"] == 1
    assert receipt["gaps"][0] == {
        "requirement_id": "SRC-ULIF",
        "field": "value",
        "stage": stage,
        "gap": "G-ULIF",
        "owner": "open-model-data",
        "reason": reason,
        "evidence": [fixture.ref],
        "range_id": "range-0",
        "identity": record["identity"],
    }
    assert receipt["stage_counts"][stage][state] == 1
    assert all(c["genuinely_absent"] == 0 for c in receipt["stage_counts"].values())


def test_missing_evidence_defaults_to_missing_and_keeps_denominator(fixture):
    fixture.docs["stage_evidence"]["records"].pop(0)
    fixture.save()
    assert fixture.cli().returncode == 2
    assert fixture.receipt()["stage_counts"]["acquisition"]["missing"] == 1
    assert fixture.receipt()["supplied_unit_count"] == 144


def test_all20_unknown_ranges_and_original123_not_guessed(fixture):
    fixture.docs["source_manifest"]["ranges"] = []
    fixture.docs["stage_evidence"]["records"] = []
    for name in ("lexical_universe", "legacy_membership"):
        fixture.docs[name].update(membership="UNKNOWN", index=None, members=[])
    fixture.save()
    assert fixture.cli().returncode == 2
    receipt = fixture.receipt()
    assert receipt["gap_count"] == 22
    assert receipt["legacy_member_count"] is receipt["lexical_member_count"] is None
    assert receipt["legacy_expected_obligation"] == 123
    assert [r["requirement_id"] for r in receipt["requirements"]] == list(IDS)
    assert all(r["partition_status"] == "UNPARTITIONED" for r in receipt["requirements"])
    assert all(r["gap_count"] == 1 for r in receipt["requirements"])
    assert fixture.source_output()["units"] == []
    assert receipt["stage_counts"] == {}
    assert receipt["programme_completeness"] == "UNRESOLVED"


def test_unknown_range_is_not_zero_or_absent(fixture):
    row = fixture.docs["source_manifest"]["ranges"][1]
    row.update(membership="UNKNOWN", units=[], index=None)
    fixture.docs["stage_evidence"]["records"] = [
        r for r in fixture.docs["stage_evidence"]["records"] if r["range_id"] != "range-1"
    ]
    fixture.save()
    assert fixture.cli().returncode == 2
    output = fixture.source_output("SRC-VESUM")
    assert output["ranges"][0]["unit_count"] is None
    assert output["ranges"][0]["unit_partitions"] is None
    assert output["ranges"][0]["partition_status"] == "UNPARTITIONED"


@pytest.mark.parametrize("drift", ["missing", "extra", "order", "identity", "duplicate", "digest", "boundary"])
def test_source_index_reconciliation_rejects_drift_before_publication(fixture, drift):
    row = fixture.docs["source_manifest"]["ranges"][0]
    if drift == "missing":
        row["units"].pop()
    elif drift == "extra":
        row["units"].append({**row["units"][0], "locator": "fixture:extra"})
    elif drift == "order":
        row["units"].reverse()
    elif drift == "identity":
        row["units"][0]["identity"]["sense"] = "invented"
    elif drift == "duplicate":
        row["units"][1]["identity"] = copy.deepcopy(row["units"][0]["identity"])
        fixture.source_index(0)
    elif drift == "digest":
        row["units"][0]["sha256"] = "0" * 64
    else:
        row["snapshot"] = "different"
    fixture.save()
    result = fixture.cli()
    assert result.returncode == 3
    assert result.stderr.startswith("INVALID_EVIDENCE:")
    assert not (fixture.root / "output").exists()


@pytest.mark.parametrize("drift", ["extra", "duplicate", "order", "digest", "binding", "reference"])
def test_stage_identity_order_and_digest_rejection(fixture, drift):
    rows = fixture.docs["stage_evidence"]["records"]
    if drift == "extra":
        rows[0]["identity"] = {**rows[0]["identity"], "key": "extra"}
    elif drift == "duplicate":
        rows.append(copy.deepcopy(rows[0]))
    elif drift == "order":
        rows[0], rows[7] = rows[7], rows[0]
    elif drift == "digest":
        rows[0]["source_unit_sha256"] = "0" * 64
    elif drift == "reference":
        fixture.raw.write_bytes(b"changed capture")
    fixture.save()
    if drift == "binding":
        fixture.docs["stage_evidence"]["source_manifest_sha256"] = "0" * 64
        write(fixture.paths["stage_evidence"], fixture.docs["stage_evidence"])
    result = fixture.cli()
    assert result.returncode == 3
    assert "INVALID_EVIDENCE" in result.stderr
    assert not (fixture.root / "output/manifest-receipt.json").exists()


def absence(fixture, ordinal=0):
    record = fixture.docs["stage_evidence"]["records"][ordinal * len(STAGES) + 2]
    source_sha = digest(fixture.paths["source_manifest"].read_bytes())
    content = {
        "schema_version": "source-absence.v1",
        "source_manifest_sha256": source_sha,
        "range_id": "range-0",
        "identity": record["identity"],
        "field": "value",
        "locator": "fixture:register/0",
    }
    sha = write(fixture.root / "absence.json", content)
    record.update(
        state="genuinely_absent",
        reason="source-located field absence",
        absence_evidence={
            "path": "absence.json",
            "sha256": sha,
            "schema_version": "source-absence.v1",
            "locator": "fixture:register/0",
        },
    )
    fixture.save()
    return record


def test_positive_absence_structurally_bound_but_not_authority(fixture):
    absence(fixture)
    assert fixture.cli().returncode == 0
    assert fixture.receipt()["stage_counts"]["parsing"]["genuinely_absent"] == 1
    assert fixture.receipt()["programme_completeness"] == "UNRESOLVED"


@pytest.mark.parametrize("defect", ["unchecked", "acquisition", "missing", "corrupt", "no-proof", "wrong-proof"])
def test_absence_cannot_hide_unchecked_or_capture_loss(fixture, defect):
    record = absence(fixture)
    if defect == "unchecked":
        fixture.docs["source_manifest"]["ranges"][0]["register_kind"] = "unchecked_extension"
        fixture.source_index(0)
        fixture.save()
        record = absence(fixture)
    elif defect == "acquisition":
        record["stage"] = "acquisition"
        fixture.docs["stage_evidence"]["records"].pop(0)
    elif defect in ("missing", "corrupt"):
        fixture.docs["stage_evidence"]["records"][0]["state"] = defect
    elif defect == "no-proof":
        record["absence_evidence"] = None
    else:
        content = json.loads((fixture.root / "absence.json").read_text())
        content["field"] = "wrong"
        record["absence_evidence"]["sha256"] = write(fixture.root / "absence.json", content)
    fixture.save()
    result = fixture.cli()
    assert result.returncode == 3
    assert "INVALID_EVIDENCE" in result.stderr


def test_historical_checked_and_unchecked_extension_remain_separate(fixture):
    row = fixture.docs["source_manifest"]["ranges"][1]
    row.update(requirement_id="SRC-ULIF", register_kind="unchecked_extension", retrieved_at="2026-10-15T18:00:00Z")
    fixture.source_index(1)
    record = next(r for r in fixture.docs["stage_evidence"]["records"] if r["range_id"] == "range-1")
    record.update(state="missing", reason="unchecked not_found")
    fixture.save()
    assert fixture.cli().returncode == 2
    ranges = fixture.source_output()["ranges"]
    assert [(r["register_kind"], r["retrieved_at"], r["unit_count"]) for r in ranges] == [
        ("checked_register", "2026-09-28T22:51:41Z", 3),
        ("unchecked_extension", "2026-10-15T18:00:00Z", 1),
    ]
    assert fixture.receipt()["stage_counts"]["acquisition"]["missing"] == 1


@pytest.mark.parametrize(
    "defect",
    [
        "matrix",
        "owner",
        "requirement",
        "field",
        "consumer",
        "all-na",
        "unknown-units",
        "unknown-members",
        "missing-index",
        "timestamp",
        "extra-range",
        "range-duplicate",
        "member-duplicate",
        "member-drift",
        "legacy122",
        "bad-link",
        "schema",
        "extra-key",
        "bool123",
        "stage-unknown",
        "stage-field",
        "stage-consumer",
        "no-evidence",
        "wrong-raw",
        "unused-absence",
    ],
)
def test_invalid_inputs_fail_closed(fixture, defect):
    req = fixture.docs["requirements"]["requirements"][0]
    row = fixture.docs["source_manifest"]["ranges"][0]
    record = fixture.docs["stage_evidence"]["records"][0]
    members = fixture.docs["legacy_membership"]
    if defect == "matrix":
        fixture.docs["requirements"]["matrix_sha256"] = "0" * 64
    elif defect == "owner":
        req["owner"] = "invented-owner"
    elif defect == "requirement":
        fixture.docs["requirements"]["requirements"].pop()
    elif defect == "field":
        req["fields"].append(copy.deepcopy(req["fields"][0]))
    elif defect == "consumer":
        req["consumers"].append("Atlas")
    elif defect == "all-na":
        req["fields"][0]["applicability"] = "not_applicable"
    elif defect == "unknown-units":
        row["membership"] = "UNKNOWN"
    elif defect == "unknown-members":
        members["membership"] = "UNKNOWN"
    elif defect == "missing-index":
        row["index"] = None
    elif defect == "timestamp":
        row["retrieved_at"] = "October yesterday"
    elif defect == "extra-range":
        row["requirement_id"] = "EXTRA"
    elif defect == "range-duplicate":
        fixture.docs["source_manifest"]["ranges"].append(copy.deepcopy(row))
    elif defect in ("member-duplicate", "member-drift", "legacy122", "bad-link"):
        if defect == "member-duplicate":
            members["members"][1]["member_id"] = members["members"][0]["member_id"]
        elif defect == "member-drift":
            members["members"].reverse()
        elif defect == "legacy122":
            members["members"].pop()
        else:
            members["members"][0]["source_units"][0]["range_id"] = "unknown-range"
        if defect != "member-drift":
            path = fixture.root / members["index"]["path"]
            value = json.loads(path.read_text())
            value["members"] = members["members"]
            members["index"]["sha256"] = write(path, value)
    elif defect == "schema":
        fixture.docs["requirements"]["schema_version"] = "source-requirements.v2"
    elif defect == "extra-key":
        fixture.docs["requirements"]["approve"] = True
    elif defect == "bool123":
        members["expected_obligation"] = True
    elif defect == "stage-unknown":
        record["range_id"] = "unseen"
    elif defect == "stage-field":
        record["field"] = "unseen"
    elif defect == "stage-consumer":
        record["stage"] = "consumer:unseen"
    elif defect == "no-evidence":
        record["evidence"] = []
    elif defect == "wrong-raw":
        path = fixture.root / "wrong.txt"
        path.write_bytes(b"wrong raw")
        record["evidence"] = [{**fixture.ref, "path": "wrong.txt", "sha256": digest(path.read_bytes())}]
    else:
        record["absence_evidence"] = fixture.ref
    fixture.save()
    result = fixture.cli()
    assert result.returncode == 3, result.stdout + result.stderr
    assert "INVALID_EVIDENCE:" in result.stderr
    assert not (fixture.root / "output").exists()


@pytest.mark.parametrize(
    "raw",
    [
        b"{",
        b"[]",
        b'{"schema_version":"a","schema_version":"b"}',
        b'{"x":NaN}',
        b'{"x":Infinity}',
        b'{"x":"\\ud800"}',
        b"\xff",
    ],
)
def test_malformed_json_cli(fixture, raw):
    fixture.paths["requirements"].write_bytes(raw)
    result = fixture.cli()
    assert result.returncode == 3
    assert "INVALID_EVIDENCE:" in result.stderr


def test_missing_input_cli_and_callable(fixture):
    fixture.paths["requirements"].unlink()
    assert fixture.cli().returncode == 3
    with pytest.raises(manifest.InvalidEvidence, match="five"):
        manifest.account({})


def test_linkless_member_is_a_named_gap(fixture):
    document = fixture.docs["lexical_universe"]
    document["members"][0]["source_units"] = []
    path = fixture.root / document["index"]["path"]
    value = json.loads(path.read_text())
    value["members"] = document["members"]
    document["index"]["sha256"] = write(path, value)
    fixture.save()
    assert fixture.cli().returncode == 2
    assert fixture.receipt()["gaps"][0]["reason"] == "member source linkage unresolved"


def test_reference_missing_and_version_drift(fixture):
    row = fixture.docs["source_manifest"]["ranges"][0]
    row["index"]["schema_version"] = "wrong.v2"
    fixture.save()
    assert fixture.cli().returncode == 3
    (fixture.root / row["index"]["path"]).unlink()
    assert fixture.cli().returncode == 3


@pytest.mark.parametrize("failure_at", [1, 5, 22])
def test_cli_interrupted_publication_has_no_receipt(fixture, failure_at):
    # Real module CLI in a fresh interpreter; inject only the filesystem operation.
    program = """
import os, sys
from scripts.projects.open_model_data import source_completeness_manifest as m
original = os.replace
count = 0
def replace(source, target):
    global count
    count += 1
    if count == int(sys.argv[1]):
        raise OSError('injected publication failure')
    original(source, target)
m.os.replace = replace
raise SystemExit(m.main(sys.argv[2:]))
"""
    args = [sys.executable, "-c", program, str(failure_at)]
    for name, path in fixture.paths.items():
        args += ["--" + name.replace("_", "-"), str(path)]
    args += ["--output-dir", str(fixture.root / "failed")]
    result = subprocess.run(
        args, capture_output=True, text=True, check=False, timeout=60, env={**os.environ, "TMPDIR": str(fixture.root)}
    )
    assert result.returncode == 4, result.stdout + result.stderr
    assert "PUBLICATION_FAILURE:" in result.stderr
    assert not (fixture.root / "failed/manifest-receipt.json").exists()
    assert fixture.cli(out="failed").returncode == 4
    assert fixture.cli(out="fresh").returncode == 0


def test_keyboard_interrupt_before_receipt_cannot_commit(fixture, monkeypatch):
    outputs, receipt = manifest.account(fixture.paths)
    monkeypatch.setenv("TMPDIR", str(fixture.root))
    original = manifest.os.replace

    def interrupt(source, target):
        if target.name == "manifest-receipt.json":
            raise KeyboardInterrupt
        original(source, target)

    monkeypatch.setattr(manifest.os, "replace", interrupt)
    with pytest.raises(KeyboardInterrupt):
        manifest.publish(fixture.root / "interrupted", outputs, receipt)
    assert not (fixture.root / "interrupted/manifest-receipt.json").exists()


def test_output_restrictions_and_prior_input_preservation(fixture, tmp_path):
    prior = {name: path.read_bytes() for name, path in fixture.paths.items()}
    assert fixture.cli(out="..").returncode == 4
    (fixture.root / "alias").symlink_to(fixture.root, target_is_directory=True)
    assert fixture.cli(out="alias/output").returncode == 4
    assert fixture.cli(out=".").returncode == 4
    assert fixture.cli().returncode == 0
    (fixture.root / "output/SRC-ULIF.json").write_text("damaged output")
    assert fixture.cli().returncode == 4
    assert prior == {name: path.read_bytes() for name, path in fixture.paths.items()}


def test_help_documents_artifacts_exit_codes_and_scope(fixture):
    result = fixture.cli(extra=["--help"])
    assert result.returncode == 0
    for text in (
        "Outputs:",
        "Exit codes:",
        "Related:",
        "STRUCTURALLY_ACCOUNTED",
        "INCOMPLETE_DIAGNOSTIC",
        "INVALID_EVIDENCE",
        "PUBLICATION_FAILURE",
        "never source approval",
    ):
        assert text in result.stdout


def test_absent_source_homonym_and_sense_stay_null(fixture):
    row = fixture.docs["source_manifest"]["ranges"][0]
    row["units"][0]["identity"].update(homonym=None, sense=None)
    fixture.source_index(0)
    doc = fixture.docs["lexical_universe"]
    path = fixture.root / doc["index"]["path"]
    value = json.loads(path.read_text())
    value["members"] = doc["members"]
    doc["index"]["sha256"] = write(path, value)
    fixture.save()
    assert fixture.cli().returncode == 0
    assert fixture.source_output()["units"][0]["identity"] == {
        "key": "fixture-key",
        "homonym": None,
        "sense": None,
        "path": ["group", "nested", "0"],
        "occurrence": 0,
    }


def test_positive_absent_unit_has_disjoint_unit_partition(fixture):
    prototype = absence(fixture)
    for record in fixture.docs["stage_evidence"]["records"][3:7]:
        record.update(
            state="genuinely_absent", reason=prototype["reason"], absence_evidence=prototype["absence_evidence"]
        )
    fixture.save()
    assert fixture.cli().returncode == 0
    result = fixture.source_output()
    assert result["units"][0]["structural_partition"] == "genuinely_absent"
    assert result["ranges"][0]["unit_partitions"] == {
        "verified-complete": 2,
        "missing": 0,
        "corrupt": 0,
        "quarantined": 0,
        "genuinely_absent": 1,
    }
    assert sum(result["ranges"][0]["unit_partitions"].values()) == 3


def test_invalid_cli_flags_are_invalid_evidence(fixture):
    result = subprocess.run([sys.executable, "-m", MODULE], capture_output=True, text=True, check=False, timeout=60)
    assert result.returncode == 3
    assert result.stderr == "INVALID_EVIDENCE: invalid CLI arguments; use --help\n"


def test_date_without_time_is_not_a_retrieval_timestamp(fixture):
    fixture.docs["source_manifest"]["ranges"][0]["retrieved_at"] = "2026-09-28Z"
    fixture.save()
    assert fixture.cli().returncode == 3


@pytest.mark.parametrize("occurrence", [0.0, -0.0, 1.0])
@pytest.mark.parametrize(
    "boundary",
    [
        "source-manifest",
        "source-index",
        "stage",
        "lexical_universe",
        "lexical_universe-index",
        "legacy_membership",
        "legacy_membership-index",
        "absence",
    ],
)
def test_occurrence_requires_integer_at_every_identity_boundary(fixture, boundary, occurrence):
    ordinal = int(occurrence)
    if boundary == "source-manifest":
        # Shared source/stage/member identities drift together, unlike retained indexes.
        fixture.docs["source_manifest"]["ranges"][0]["units"][ordinal]["identity"]["occurrence"] = occurrence
    elif boundary == "source-index":
        ref = fixture.docs["source_manifest"]["ranges"][0]["index"]
        path = fixture.root / ref["path"]
        value = json.loads(path.read_text())
        value["units"][ordinal]["identity"]["occurrence"] = occurrence
        ref["sha256"] = write(path, value)
    elif boundary == "stage":
        record = fixture.docs["stage_evidence"]["records"][ordinal * len(STAGES)]
        record["identity"] = {**record["identity"], "occurrence": occurrence}
    elif boundary == "absence":
        record = absence(fixture, ordinal)
        path = fixture.root / record["absence_evidence"]["path"]
        value = json.loads(path.read_text())
        value["identity"] = {**record["identity"], "occurrence": occurrence}
        record["absence_evidence"]["sha256"] = write(path, value)
    else:
        name = boundary.removesuffix("-index")
        document = fixture.docs[name]
        if boundary.endswith("-index"):
            path = fixture.root / document["index"]["path"]
            value = json.loads(path.read_text())
            value["members"][ordinal]["source_units"][0]["identity"]["occurrence"] = occurrence
            document["index"]["sha256"] = write(path, value)
        else:
            link = document["members"][ordinal]["source_units"][0]
            link["identity"] = {**link["identity"], "occurrence": occurrence}
    fixture.save()
    result = fixture.cli()
    assert result.returncode == 3, result.stdout + result.stderr
    assert result.stderr.startswith("INVALID_EVIDENCE:")
    assert "type failed" in result.stderr
    assert "Traceback" not in result.stderr
    assert not (fixture.root / "output").exists()


@pytest.mark.parametrize("occurrence", [0.0, -0.0])
@pytest.mark.parametrize("boundary", ["source", "stage", "member"])
def test_float_occurrence_cannot_create_duplicate_identity(fixture, boundary, occurrence):
    if boundary == "source":
        row = fixture.docs["source_manifest"]["ranges"][0]
        duplicate = copy.deepcopy(row["units"][0])
        duplicate["identity"]["occurrence"] = occurrence
        duplicate["locator"] = "fixture:duplicate"
        row["units"].append(duplicate)
        fixture.source_index(0)
        records = fixture.docs["stage_evidence"]["records"]
        for record in copy.deepcopy(records[: len(STAGES)]):
            record["identity"] = duplicate["identity"]
            records.append(record)
    elif boundary == "stage":
        records = fixture.docs["stage_evidence"]["records"]
        duplicate = copy.deepcopy(records[0])
        duplicate["identity"]["occurrence"] = occurrence
        records.append(duplicate)
    else:
        document = fixture.docs["lexical_universe"]
        links = document["members"][0]["source_units"]
        duplicate = copy.deepcopy(links[0])
        duplicate["identity"]["occurrence"] = occurrence
        links.append(duplicate)
        path = fixture.root / document["index"]["path"]
        value = json.loads(path.read_text())
        value["members"] = document["members"]
        document["index"]["sha256"] = write(path, value)
    fixture.save()
    result = fixture.cli()
    assert result.returncode == 3, result.stdout + result.stderr
    assert result.stderr.startswith("INVALID_EVIDENCE:")
    assert "type failed" in result.stderr
    assert "Traceback" not in result.stderr
    assert not (fixture.root / "output").exists()


@pytest.mark.parametrize("path", ["capture\x00.txt", "loop"], ids=["embedded-nul", "symlink-loop"])
@pytest.mark.parametrize("kind", ["source-index", "lexical-index", "legacy-index", "evidence", "absence"])
def test_unresolvable_reference_is_invalid_evidence_without_publication(fixture, kind, path):
    (fixture.root / "loop").symlink_to("loop")
    if kind == "source-index":
        ref = fixture.docs["source_manifest"]["ranges"][0]["index"]
    elif kind in ("lexical-index", "legacy-index"):
        name = "lexical_universe" if kind == "lexical-index" else "legacy_membership"
        ref = fixture.docs[name]["index"]
    elif kind == "evidence":
        ref = fixture.docs["stage_evidence"]["records"][0]["evidence"][0]
    else:
        ref = absence(fixture)["absence_evidence"]
    ref["path"] = path
    fixture.save()
    result = fixture.cli()
    assert result.returncode == 3, result.stdout + result.stderr
    assert result.stdout == ""
    assert result.stderr == "INVALID_EVIDENCE: referenced artifact unavailable\n"
    assert not (fixture.root / "output").exists()


def test_symlink_loop_top_level_input_is_invalid_evidence_without_publication(fixture):
    (fixture.root / "loop").symlink_to("loop")
    fixture.paths["stage_evidence"] = fixture.root / "loop"
    result = fixture.cli()
    assert result.returncode == 3, result.stdout + result.stderr
    assert result.stdout == ""
    assert result.stderr == "INVALID_EVIDENCE: unreadable or invalid JSON input\n"
    assert not (fixture.root / "output").exists()


@pytest.mark.parametrize("loop", ["output", "tmpdir"])
def test_unresolvable_publication_path_is_publication_failure_without_receipt(fixture, loop):
    prior = {name: path.read_bytes() for name, path in fixture.paths.items()}
    (fixture.root / "loop").symlink_to("loop")
    result = fixture.cli(out="loop/output") if loop == "output" else fixture.cli(tmpdir=fixture.root / "loop")
    assert result.returncode == 4, result.stdout + result.stderr
    assert result.stdout == ""
    assert result.stderr == "PUBLICATION_FAILURE: path cannot be resolved\n"
    assert not (fixture.root / "output").exists()
    assert not list(fixture.root.rglob("manifest-receipt.json"))
    assert prior == {name: path.read_bytes() for name, path in fixture.paths.items()}


def test_embedded_nul_output_dir_is_publication_oserror(fixture, monkeypatch):
    # Process arguments cannot carry NUL, so the callable is the only entry point.
    outputs, receipt = manifest.account(fixture.paths)
    monkeypatch.setenv("TMPDIR", str(fixture.root))
    with pytest.raises(OSError, match=r"^path cannot be resolved$"):
        manifest.publish(fixture.root / "out\x00put", outputs, receipt)
    assert not list(fixture.root.rglob("manifest-receipt.json"))
