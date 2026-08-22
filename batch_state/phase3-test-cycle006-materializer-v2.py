#!/usr/bin/env python3
"""Synthetic, source-free behavior proof for the Cycle-006 materializer."""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import stat
import sys
import tempfile
import unittest
from contextlib import contextmanager, redirect_stdout
from pathlib import Path
from typing import Any
from unittest.mock import patch

SCRIPT = Path(__file__).with_name("phase3-materialize-cycle006-successor-v2.py")
SPEC = importlib.util.spec_from_file_location("phase3_materialize_cycle006_successor_v2", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load Cycle-006 materializer")
materializer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = materializer
SPEC.loader.exec_module(materializer)


def _write(path: Path, value: Any, *, raw: bool = False) -> bytes:
    payload = value if raw else materializer.canonical(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    os.chmod(path, materializer.PRIVATE_FILE_MODE)
    return payload


def _row(index: int, lane: str, *, include_cycle: bool) -> dict[str, Any]:
    unit_id = f"synthetic.{lane}.{index:03d}"
    row: dict[str, Any] = {
        "unit_id": unit_id,
        "unit_sha256": hashlib.sha256(unit_id.encode()).hexdigest(),
        "family_id": "synthetic_family",
        "source_text": f"PRIVATE-SYNTHETIC-SOURCE-{index}",
        "source_record": {"locator": f"synthetic-locator-{index}"},
        "nested_source": {"order": [index, "value"], "unicode": "українська"},
    }
    if include_cycle:
        row["evaluation_cycle_id"] = materializer.CYCLE005
    return row


def _fixture(root: Path) -> tuple[Path, Path, Path, list[dict[str, Any]]]:
    source = root / "cycle005-source"
    source.mkdir(mode=materializer.PRIVATE_DIR_MODE)
    os.chmod(source, materializer.PRIVATE_DIR_MODE)
    packet_specs = (("clean_label", 1, 2), ("clean_label", 2, 1), ("residual_label", 1, 3))
    packet_records: list[dict[str, Any]] = []
    all_rows: list[dict[str, Any]] = []
    for lane, index, count in packet_specs:
        start = len(all_rows)
        rows = [_row(start + offset, lane, include_cycle=(start + offset) % 2 == 0) for offset in range(count)]
        all_rows.extend(rows)
        packet = {
            "schema_version": "phase3_cycle005_private_packet_v1",
            "evaluation_cycle_id": materializer.CYCLE005,
            "lane": lane,
            "packet_index": index,
            "row_count": count,
            "rows": rows,
            "packet_identity_set_sha256": materializer.identity_set(rows),
        }
        packet_path = source / lane / f"packet-{index:04d}.json"
        packet_raw = _write(packet_path, packet)
        packet_records.append(
            {
                "lane": lane,
                "packet_index": index,
                "canonical_basename": packet_path.name,
                "row_count": count,
                "raw_sha256": materializer.digest(packet_raw),
                "packet_identity_set_sha256": packet["packet_identity_set_sha256"],
            }
        )
    manifest = {
        "schema_version": "phase3_cycle005_label_manifest_v1",
        "evaluation_cycle_id": materializer.CYCLE005,
        "text_free": True,
        "custody_receipt_raw_sha256": "",
        "packet_count": len(packet_records),
        "row_count": len(all_rows),
        "packets": packet_records,
        "ordered_packet_commitment_sha256": materializer.digest(materializer.canonical(packet_records)),
        "identity_union_commitment_sha256": materializer.digest(
            materializer.canonical(sorted((row["unit_id"], row["unit_sha256"]) for row in all_rows))
        ),
    }
    custody = {
        "schema_version": "phase3_cycle005_custody_receipt_v1",
        "evaluation_cycle_id": materializer.CYCLE005,
        "text_free": True,
        "provider_artifacts_copied": False,
    }
    custody["receipt_sha256"] = materializer._hash_receipt(custody)
    custody_raw = _write(source / "custody-receipt.json", custody)
    manifest["custody_receipt_raw_sha256"] = materializer.digest(custody_raw)
    manifest["receipt_sha256"] = materializer._hash_receipt(manifest)
    _write(source / "label-manifest.json", manifest)
    # A source provider artifact proves the successor is selective.  It is
    # intentionally synthetic and must never appear in the output package.
    _write(source / "label-output-grok-cycle005" / "raw-provider-response.raw", b"PRIVATE-PROVIDER-ARTIFACT", raw=True)
    amendment = root / "synthetic-amendment.md"
    amendment.write_text("synthetic amendment; never a live approval\n", encoding="utf-8")
    os.chmod(amendment, materializer.PRIVATE_FILE_MODE)
    return source, root / "cycle006-successor", amendment, all_rows


def _real_shape_fixture(
    root: Path,
) -> tuple[Path, Path, Path, list[dict[str, Any]], dict[str, str]]:
    """Create the exact real packet/row shape with synthetic source values."""

    source = root / "cycle005-real-shape-source"
    source.mkdir(mode=materializer.PRIVATE_DIR_MODE)
    os.chmod(source, materializer.PRIVATE_DIR_MODE)
    packet_specs = [("clean_label", index, 50) for index in range(1, 41)] + [
        ("residual_label", index, 9 if index == 164 else 50) for index in range(1, 165)
    ]
    packet_records: list[dict[str, Any]] = []
    all_rows: list[dict[str, Any]] = []
    ordered_stream: list[list[Any]] = []
    for lane, index, count in packet_specs:
        start = len(all_rows)
        # The real source has no row-level cycle field.  A few present fields
        # keep the strict branch's preservation proof honest as well.
        rows = [_row(start + offset, lane, include_cycle=(start + offset) % 97 == 0) for offset in range(count)]
        all_rows.extend(rows)
        packet = {
            "schema_version": "phase3_cycle005_private_packet_v1",
            "evaluation_cycle_id": materializer.CYCLE005,
            "lane": lane,
            "packet_index": index,
            "row_count": count,
            "rows": rows,
            "packet_identity_set_sha256": materializer.identity_set(rows),
        }
        packet_path = source / lane / f"packet-{index:04d}.json"
        packet_raw = _write(packet_path, packet)
        packet_records.append(
            {
                "lane": lane,
                "packet_index": index,
                "canonical_basename": packet_path.name,
                "row_count": count,
                "raw_sha256": materializer.digest(packet_raw),
                "packet_identity_set_sha256": packet["packet_identity_set_sha256"],
            }
        )
        for row_index, row in enumerate(rows):
            unit_id, unit_sha = materializer._identity(row)
            ordered_stream.append([lane, index, row_index, unit_id, unit_sha])
    commitment = materializer._ordered_identity_commitment(ordered_stream)
    custody = {
        "schema_version": "phase3_cycle005_custody_receipt_v1",
        "evaluation_cycle_id": materializer.CYCLE005,
        "text_free": True,
        "ordered_identity_commitment_sha256": commitment,
    }
    custody["receipt_sha256"] = materializer._hash_receipt(custody)
    custody_raw = _write(source / "custody-receipt.json", custody)
    manifest = {
        "schema_version": "phase3_cycle005_label_manifest_v1",
        "evaluation_cycle_id": materializer.CYCLE005,
        "text_free": True,
        "custody_receipt_raw_sha256": materializer.digest(custody_raw),
        "packet_count": 204,
        "row_count": 10_159,
        "packets": packet_records,
        "ordered_packet_commitment_sha256": materializer.digest(materializer.canonical(packet_records)),
        "identity_union_commitment_sha256": materializer.digest(
            materializer.canonical(sorted((row["unit_id"], row["unit_sha256"]) for row in all_rows))
        ),
    }
    manifest["receipt_sha256"] = materializer._hash_receipt(manifest)
    manifest_raw = _write(source / "label-manifest.json", manifest)
    # These represent prior provider outputs and an auxiliary source artifact;
    # the successor must not copy any of them.
    for directory, filename in (
        ("label-output-grok-cycle005", "response.raw"),
        ("label-output-gemini-v2", "response.raw"),
        ("dual-label-adjudication-cycle005", "selection.json"),
    ):
        _write(source / directory / filename, b"PRIVATE-PROVIDER-RESPONSE", raw=True)
    _write(source / "privacy-exclusion.json", {"synthetic": "PRIVATE-EXCLUSION"})
    amendment = root / "synthetic-real-shape-amendment.md"
    amendment.write_text("synthetic amendment for strict-shape proof\n", encoding="utf-8")
    os.chmod(amendment, materializer.PRIVATE_FILE_MODE)
    bindings = {
        "amendment": materializer.digest(amendment.read_bytes()),
        "custody": materializer.digest(custody_raw),
        "manifest": materializer.digest(manifest_raw),
        "ordered_identity": commitment,
    }
    return source, root / "cycle006-real-shape-successor", amendment, all_rows, bindings


def _strict_prompt_root(root: Path) -> Path:
    prompt_root = root / "synthetic-prompt-source" / "batch_state"
    prompt_root.mkdir(parents=True)
    for template_name in materializer.PROMPT_TEMPLATES.values():
        (prompt_root / template_name).write_text(
            "# Cycle 005 synthetic prompt template\nReturn only the requested strict JSON response.\n",
            encoding="utf-8",
        )
    return prompt_root


def _rebind_packet_manifest(source: Path, lane: str, index: int) -> str:
    """Rebind synthetic packet metadata after an intentional source edit."""

    manifest_path = source / "label-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    records = manifest["packets"]
    packet_path = source / lane / f"packet-{index:04d}.json"
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    packet_record = next(record for record in records if record["lane"] == lane and record["packet_index"] == index)
    packet_record["raw_sha256"] = materializer.digest(packet_path.read_bytes())
    packet_record["packet_identity_set_sha256"] = packet["packet_identity_set_sha256"]
    all_identities: list[tuple[str, str]] = []
    for record in records:
        current = json.loads((source / record["lane"] / record["canonical_basename"]).read_text(encoding="utf-8"))
        all_identities.extend(materializer._identity(row) for row in current["rows"])
    manifest["ordered_packet_commitment_sha256"] = materializer.digest(materializer.canonical(records))
    manifest["identity_union_commitment_sha256"] = materializer.digest(materializer.canonical(sorted(all_identities)))
    manifest["receipt_sha256"] = materializer._hash_receipt(manifest)
    manifest_raw = _write(manifest_path, manifest)
    return materializer.digest(manifest_raw)


@contextmanager
def _strict_bindings(bindings: dict[str, str], prompt_root: Path):
    with (
        patch.object(materializer, "AMENDMENT_SHA256", bindings["amendment"]),
        patch.object(materializer, "SOURCE_CUSTODY_SHA256", bindings["custody"]),
        patch.object(materializer, "SOURCE_MANIFEST_SHA256", bindings["manifest"]),
        patch.object(materializer, "ORDERED_IDENTITY_COMMITMENT_SHA256", bindings["ordered_identity"]),
        patch.object(materializer, "_source_template_root", return_value=prompt_root),
    ):
        yield


class Cycle006MaterializerBehaviorProof(unittest.TestCase):
    def test_authorized_v3_static_bindings_are_exact(self) -> None:
        amendment = Path(__file__).with_name("phase3-cycle006-restart-amendment-v3.md")
        expected_amendment = "524e6eb4f18d38f104413fb32f421ff73c3d80bc411d338a6d8a31fabc087474"
        expected_identity = "331fd7fbc42e43cb3c218d9c2b790df060c0a553ab7c3a7b3b557f9f2bc3c419"
        self.assertEqual(materializer.digest(amendment.read_bytes()), expected_amendment)
        self.assertEqual(materializer.AMENDMENT_SHA256, expected_amendment)
        self.assertEqual(materializer.ORDERED_IDENTITY_COMMITMENT_SHA256, expected_identity)

    def test_materializes_exact_synthetic_order_and_changes_only_cycle(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source, output, amendment, source_rows = _fixture(Path(temporary))
            result = materializer.materialize(source, output, amendment, fixture=True)
            self.assertEqual(result["packet_count"], 3)
            self.assertEqual(result["row_count"], len(source_rows))
            self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o700)
            self.assertEqual(
                [
                    (record["lane"], record["packet_index"])
                    for record in json.loads((output / "label-manifest.json").read_text())["packets"]
                ],
                [("clean_label", 1), ("clean_label", 2), ("residual_label", 1)],
            )
            actual_rows: list[dict[str, Any]] = []
            for lane, index, _count in (("clean_label", 1, 2), ("clean_label", 2, 1), ("residual_label", 1, 3)):
                packet = json.loads((output / lane / f"packet-{index:04d}.json").read_text())
                self.assertEqual(packet["evaluation_cycle_id"], materializer.CYCLE006)
                for row in packet["rows"]:
                    actual_rows.append(row)
            expected_rows = []
            for row in source_rows:
                expected = dict(row)
                if "evaluation_cycle_id" in row:
                    expected["evaluation_cycle_id"] = materializer.CYCLE006
                expected_rows.append(expected)
            self.assertEqual(actual_rows, expected_rows)
            self.assertTrue(any("evaluation_cycle_id" in row for row in actual_rows))
            self.assertTrue(any("evaluation_cycle_id" not in row for row in actual_rows))
            self.assertFalse((output / "label-output-grok-cycle005").exists())
            self.assertFalse(
                any(
                    "PRIVATE-SYNTHETIC" in path.read_text(errors="ignore")
                    for path in output.rglob("*.json")
                    if path.name.endswith("receipt.json") or "manifest" in path.name
                )
            )

    def test_prompts_are_fresh_and_receipts_are_text_free(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source, output, amendment, _ = _fixture(Path(temporary))
            materializer.materialize(source, output, amendment, fixture=True)
            prompt_names = {path.name for path in (output / "prompts").iterdir()}
            self.assertEqual(prompt_names, set(materializer.PROMPT_FILES.values()))
            for path in (output / "prompts").iterdir():
                payload = path.read_text(encoding="utf-8")
                self.assertNotIn(materializer.CYCLE005, payload)
                if "gemini" in path.name:
                    self.assertIn("labels_by_position", payload)
                    self.assertIn("p01", payload)
                else:
                    self.assertIn("labels envelope", payload)
            for path in (output / "custody-receipt.json", output / "label-manifest.json"):
                payload = path.read_text(encoding="utf-8")
                self.assertNotIn("PRIVATE-SYNTHETIC", payload)
                self.assertNotIn("source_text", payload)
                self.assertTrue(json.loads(payload)["text_free"])

    def test_modes_and_transactional_output_exists_guard(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source, output, amendment, _ = _fixture(Path(temporary))
            materializer.materialize(source, output, amendment, fixture=True)
            for path in output.rglob("*"):
                expected = 0o700 if path.is_dir() else 0o600
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), expected)
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                status = materializer.main(
                    ["--source", str(source), "--output", str(output), "--amendment", str(amendment), "--fixture"]
                )
            self.assertEqual(status, 2)
            result = json.loads(stdout.getvalue())
            self.assertEqual(result, {"ok": False, "failure_code": "output_exists", "text_free": True})
            self.assertNotIn("PRIVATE-SYNTHETIC", stdout.getvalue())

    def test_real_mode_requires_the_frozen_amendment_and_fixture_is_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source, output, amendment, _ = _fixture(Path(temporary))
            with self.assertRaises(materializer.MaterializationError) as context:
                materializer.materialize(source, output, amendment)
            self.assertEqual(context.exception.code, "amendment_binding_drift")
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                status = materializer.main(
                    ["--source", str(source), "--output", str(output), "--amendment", str(amendment)]
                )
            self.assertEqual(status, 2)
            self.assertEqual(json.loads(stdout.getvalue())["failure_code"], "amendment_binding_drift")

    def test_strict_real_shape_branch_is_synthetic_and_text_free(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, output, amendment, source_rows, bindings = _real_shape_fixture(root)
            prompt_root = _strict_prompt_root(root)
            with (
                patch.object(materializer, "AMENDMENT_SHA256", bindings["amendment"]),
                patch.object(materializer, "SOURCE_CUSTODY_SHA256", bindings["custody"]),
                patch.object(materializer, "SOURCE_MANIFEST_SHA256", bindings["manifest"]),
                patch.object(materializer, "ORDERED_IDENTITY_COMMITMENT_SHA256", bindings["ordered_identity"]),
                patch.object(materializer, "_source_template_root", return_value=prompt_root),
            ):
                result = materializer.materialize(source, output, amendment, fixture=False)
            self.assertEqual(result["packet_count"], 204)
            self.assertEqual(result["row_count"], 10_159)
            self.assertEqual(
                set(path.name for path in output.iterdir()),
                materializer.OUTPUT_TOP_LEVEL,
            )
            for provider_directory in (
                "label-output-grok-cycle005",
                "label-output-gemini-v2",
                "dual-label-adjudication-cycle005",
                "privacy-exclusion.json",
            ):
                self.assertFalse((output / provider_directory).exists())
            custody_path = output / "custody-receipt.json"
            manifest_path = output / "label-manifest.json"
            custody_raw = custody_path.read_bytes()
            manifest_raw = manifest_path.read_bytes()
            custody = json.loads(custody_raw)
            manifest = json.loads(manifest_raw)
            self.assertEqual(custody["evaluation_cycle_id"], materializer.CYCLE006)
            self.assertEqual(manifest["evaluation_cycle_id"], materializer.CYCLE006)
            self.assertEqual(custody["packet_count"], 204)
            self.assertEqual(custody["row_count"], 10_159)
            self.assertEqual(custody["lane_row_counts"], {"clean_label": 2_000, "residual_label": 8_159})
            self.assertEqual(manifest["packet_count"], 204)
            self.assertEqual(manifest["row_count"], 10_159)
            self.assertEqual(manifest["custody_receipt_raw_sha256"], materializer.digest(custody_raw))
            self.assertEqual(custody["source_custody_receipt_raw_sha256"], bindings["custody"])
            self.assertEqual(custody["source_label_manifest_raw_sha256"], bindings["manifest"])
            self.assertEqual(custody["cycle006_amendment_raw_sha256"], bindings["amendment"])
            self.assertEqual(custody["ordered_identity_commitment_sha256"], bindings["ordered_identity"])
            self.assertEqual(manifest["ordered_identity_commitment_sha256"], bindings["ordered_identity"])
            self.assertEqual(custody["receipt_sha256"], materializer._hash_receipt(custody))
            self.assertEqual(manifest["receipt_sha256"], materializer._hash_receipt(manifest))
            self.assertTrue(custody["text_free"])
            self.assertTrue(manifest["text_free"])
            self.assertEqual(
                manifest["prompt_sha256s"],
                {path: materializer.digest((output / path).read_bytes()) for path in manifest["prompt_sha256s"]},
            )
            actual_rows: list[dict[str, Any]] = []
            for lane, packet_count in (("clean_label", 40), ("residual_label", 164)):
                for index in range(1, packet_count + 1):
                    packet = json.loads((output / lane / f"packet-{index:04d}.json").read_text())
                    self.assertEqual(packet["evaluation_cycle_id"], materializer.CYCLE006)
                    self.assertEqual(packet["row_count"], len(packet["rows"]))
                    self.assertEqual(packet["packet_identity_set_sha256"], materializer.identity_set(packet["rows"]))
                    actual_rows.extend(packet["rows"])
            expected_rows = []
            for row in source_rows:
                expected = dict(row)
                if "evaluation_cycle_id" in row:
                    expected["evaluation_cycle_id"] = materializer.CYCLE006
                expected_rows.append(expected)
            self.assertEqual(actual_rows, expected_rows)
            self.assertTrue(any("evaluation_cycle_id" in row for row in actual_rows))
            self.assertTrue(any("evaluation_cycle_id" not in row for row in actual_rows))
            for path in output.rglob("*"):
                expected_mode = materializer.PRIVATE_DIR_MODE if path.is_dir() else materializer.PRIVATE_FILE_MODE
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), expected_mode)
            for path in (custody_path, manifest_path):
                text = path.read_text(encoding="utf-8")
                self.assertNotIn("PRIVATE-SYNTHETIC", text)
                self.assertNotIn("PRIVATE-PROVIDER", text)
                self.assertNotIn("PRIVATE-EXCLUSION", text)
                self.assertNotIn("source_text", text)

    def test_strict_branch_rejects_identity_substitution_and_reordering(self) -> None:
        for tamper in ("identity", "order"):
            with self.subTest(tamper=tamper), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                source, output, amendment, _source_rows, bindings = _real_shape_fixture(root)
                packet_path = source / "clean_label" / "packet-0001.json"
                packet = json.loads(packet_path.read_text(encoding="utf-8"))
                if tamper == "identity":
                    packet["rows"][0]["unit_id"] = "synthetic.tampered.identity"
                    packet["rows"][0]["unit_sha256"] = hashlib.sha256(b"synthetic.tampered.identity").hexdigest()
                else:
                    packet["rows"][0], packet["rows"][1] = packet["rows"][1], packet["rows"][0]
                packet["packet_identity_set_sha256"] = materializer.identity_set(packet["rows"])
                _write(packet_path, packet)
                bindings["manifest"] = _rebind_packet_manifest(source, "clean_label", 1)
                prompt_root = _strict_prompt_root(root)
                with (
                    self.assertRaises(materializer.MaterializationError) as context,
                    _strict_bindings(bindings, prompt_root),
                ):
                    materializer.materialize(source, output, amendment, fixture=False)
                self.assertEqual(context.exception.code, "ordered_identity_commitment_failure")
                self.assertFalse(output.exists())
                self.assertEqual(list(output.parent.glob(f".{output.name}.staging-*")), [])

    def test_strict_branch_rejects_missing_or_partial_packet_without_target(self) -> None:
        for state in ("missing", "partial"):
            with self.subTest(state=state), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                source, output, amendment, _source_rows, bindings = _real_shape_fixture(root)
                packet_path = source / "clean_label" / "packet-0001.json"
                if state == "missing":
                    packet_path.unlink()
                else:
                    packet_path.write_bytes(b'{"partial":true}\n')
                prompt_root = _strict_prompt_root(root)
                with (
                    self.assertRaises(materializer.MaterializationError) as context,
                    _strict_bindings(bindings, prompt_root),
                ):
                    materializer.materialize(source, output, amendment, fixture=False)
                self.assertEqual(context.exception.code, "packet_binding_drift")
                self.assertFalse(output.exists())
                self.assertEqual(list(output.parent.glob(f".{output.name}.staging-*")), [])

    def test_strict_branch_rolls_back_after_late_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, output, amendment, _source_rows, bindings = _real_shape_fixture(root)
            prompt_root = _strict_prompt_root(root)
            with (
                self.assertRaises(materializer.MaterializationError) as context,
                _strict_bindings(bindings, prompt_root),
                patch.object(
                    materializer,
                    "_write_prompt_dir",
                    side_effect=materializer.MaterializationError("transaction_failure"),
                ),
            ):
                materializer.materialize(source, output, amendment, fixture=False)
            self.assertEqual(context.exception.code, "transaction_failure")
            self.assertFalse(output.exists())
            self.assertEqual(list(output.parent.glob(f".{output.name}.staging-*")), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
