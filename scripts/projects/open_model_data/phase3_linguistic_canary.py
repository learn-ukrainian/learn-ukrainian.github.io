#!/usr/bin/env python3
"""Build the public, qualified-human Phase 3 semantic canary battery."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.projects.open_model_data import phase3_linguistic_representation as representation

UA_GEC_REPOSITORY = "https://github.com/grammarly/ua-gec"
UA_GEC_COMMIT = "4757f72f192c4a41e4c8fb1d9690a948f87cf6d6"
RIGHTS = {"status": "public_qualified_human_corpus", "license": "CC BY 4.0"}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _locator(path: str, partition: str, annotator: str, selection: str) -> dict[str, str]:
    return {
        "repository": UA_GEC_REPOSITORY,
        "commit": UA_GEC_COMMIT,
        "path": path,
        "partition": partition,
        "annotator": annotator,
        "selection": selection,
    }


def _evidence(
    *,
    canary_id: str,
    locator: Mapping[str, Any],
    document_sha256: str,
    evidence_text: str,
    source_text: str,
    corrected_text: str,
) -> list[dict[str, Any]]:
    return [
        {
            "kind": "ua_gec",
            "evidence_id": f"ua-gec-qualified-human:{canary_id}",
            "locator": dict(locator),
            "locator_sha256": representation.sha256_value(locator),
            "source_document_bytes_sha256": document_sha256,
            "evidence_text": evidence_text,
            "evidence_text_sha256": representation.sha256_text(evidence_text),
            "source_context_sha256": representation.sha256_text(source_text),
            "corrected_context_sha256": representation.sha256_text(corrected_text),
            "qualified_human": True,
            "authority": "qualified_human",
        }
    ]


def _corroboration(
    *,
    canary_id: str,
    locator: Mapping[str, Any],
    document_sha256: str,
    retrieved_text: str,
) -> list[dict[str, Any]]:
    return [
        {
            "evidence_id": f"ua-gec-corpus-retrieval:{canary_id}",
            "locator": dict(locator),
            "locator_sha256": representation.sha256_value(locator),
            "source_document_bytes_sha256": document_sha256,
            "retrieved_text": retrieved_text,
            "retrieved_text_sha256": representation.sha256_text(retrieved_text),
            "retrieval_status": "exact",
        }
    ]


def _span(text: str, value: str, *, occurrence: int = 0) -> dict[str, int]:
    start = -1
    for _ in range(occurrence + 1):
        start = text.index(value, start + 1)
    return {"start": start, "end": start + len(value)}


def _function_word_ids(text: str, construction: Mapping[str, int], words: Sequence[str]) -> list[str]:
    tokens = representation.tokenize(text)
    selected: list[str] = []
    for word in words:
        token = next(
            item
            for item in tokens
            if item["text"] == word
            and construction["start"] <= item["start"]
            and item["end"] <= construction["end"]
            and item["token_id"] not in selected
        )
        selected.append(token["token_id"])
    return selected


def _build(spec: Mapping[str, Any]) -> dict[str, Any]:
    source_text = spec["source_text"]
    corrected_text = spec["corrected_text"]
    locator = _locator(spec["path"], spec["partition"], spec["annotator"], spec["selection"])
    construction_spans = [_span(source_text, value) for value in spec["constructions"]]
    minimal_edit_spans = [{"start": item["start"], "end": item["end"]} for item in spec["edits"]]
    evidence = _evidence(
        canary_id=spec["canary_id"],
        locator=locator,
        document_sha256=spec["document_sha256"],
        evidence_text=spec["evidence_text"],
        source_text=source_text,
        corrected_text=corrected_text,
    )
    corroborating_spec = spec["corroborating"]
    corroborating_locator = _locator(
        corroborating_spec["path"],
        corroborating_spec["partition"],
        corroborating_spec["annotator"],
        corroborating_spec["selection"],
    )
    corroborating = _corroboration(
        canary_id=spec["canary_id"],
        locator=corroborating_locator,
        document_sha256=corroborating_spec["document_sha256"],
        retrieved_text=corroborating_spec["retrieved_text"],
    )
    packet = representation.build_representation(
        document_or_edition_identity=f"ua-gec@{UA_GEC_COMMIT}:{spec['path']}",
        frozen_locator=locator,
        source_document_bytes_sha256=spec["document_sha256"],
        source_text=source_text,
        paragraph_span={"start": 0, "end": len(source_text)},
        sentence_span={"start": 0, "end": len(source_text)},
        edit_shape=spec["edit_shape"],
        edits=spec["edits"],
        minimal_edit_spans=minimal_edit_spans,
        construction_spans=construction_spans,
        unchanged_function_word_token_ids=_function_word_ids(
            source_text, construction_spans[0], spec.get("unchanged_function_words", [])
        ),
        primary_role_id="corrected_example",
        correction_evidence=evidence,
        corroborating_corpus_evidence=corroborating,
        rights=RIGHTS,
        secondary_attributes=["qualified_human_correction", spec["edit_shape"]],
        register="mixed_public_corpus",
        period="contemporary",
        genre="ua_gec_source_sentence",
    )
    if packet["corrected"]["complete_text"] != corrected_text:
        raise representation.LinguisticRepresentationError(
            f"canary {spec['canary_id']} does not reproduce its qualified-human correction"
        )
    return packet


def _specs() -> list[dict[str, Any]]:
    exact_source = (
        "Він чекав близько двадцяти хвилин, а потім високий чоловік у довгому пальто, з коміром, "
        "піднятим до вух, швидко перейшов дорогу з іншої сторони вулиці."
    )
    exact_old = "іншої сторони"
    exact_start = exact_source.index(exact_old)

    insertion_source = "Це свідчить, що вони відігравали велику роль для держави."
    insertion_at = insertion_source.index(", що")

    deletion_source = "Чи це те ж саме, що й бути Іншим, чи ні?"
    deletion_start = deletion_source.index("ж ")

    reorder_source = (
        "Після цього разу дні два чи три вона бачила перед собою якісь шаблі, що тьмяно "
        "відсвічували і лежали у відкритих чорних футлярах, і збагнула, що це ріки."
    )
    reorder_old = "дні два чи три"
    reorder_start = reorder_source.index(reorder_old)

    punctuation_source = "Але не думаю, що проблема у самому ресурсі – він просто дав людям те, чого вони хотіли."
    punctuation_start = punctuation_source.index("–")

    multi_source = "Цього разу нічого грандіозного не планую, тому дрес-код вільний, шашликовий я б сказала."
    comma_at = multi_source.index(" я б сказала")
    b_start = multi_source.index(" б сказала")
    final_b_at = multi_source.index("сказала") + len("сказала")

    return [
        {
            "canary_id": "agreement-spread-substitution",
            "path": "data/gec-fluency/test/annotated/0192.a2.ann",
            "partition": "gec-fluency/test",
            "annotator": "a2",
            "selection": "first sentence, F/Calque annotation",
            "document_sha256": "6f845ebfc90a7f5613f6d7ed6ff90cf8586b45d96c09ee9aec82a62e88d6fb4b",
            "source_text": exact_source,
            "corrected_text": exact_source[:exact_start] + "іншого боку" + exact_source[exact_start + len(exact_old) :],
            "evidence_text": "{іншої сторони=>іншого боку:::error_type=F/Calque}",
            "edit_shape": "substitution",
            "edits": [{"start": exact_start, "end": exact_start + len(exact_old), "replacement": "іншого боку"}],
            "constructions": ["з іншої сторони"],
            "unchanged_function_words": ["з"],
            "corroborating": {
                "path": "data/gec-fluency/train/target-sentences/0301.a1.txt",
                "partition": "gec-fluency/train",
                "annotator": "a1",
                "selection": "exact corrected phrase at line 27",
                "document_sha256": "6b95908b7477a861de00088adfe541e97568832b98dc9235c898a53ebbe2ac08",
                "retrieved_text": "З іншого боку",
            },
        },
        {
            "canary_id": "qualified-human-insertion",
            "path": "data/gec-fluency/train/annotated/0103.a1.ann",
            "partition": "gec-fluency/train",
            "annotator": "a1",
            "selection": "sentence containing a single F/PoorFlow insertion",
            "document_sha256": "805f4ce6feaaa72efbd761047aa8bdb3d1b64027ff218df41a46538bdcb1f71a",
            "source_text": insertion_source,
            "corrected_text": insertion_source[:insertion_at] + " про те" + insertion_source[insertion_at:],
            "evidence_text": "Це свідчить{=> про те:::error_type=F/PoorFlow}, що вони відігравали велику роль для держави.",
            "edit_shape": "insertion",
            "edits": [{"start": insertion_at, "end": insertion_at, "replacement": " про те"}],
            "constructions": ["свідчить, що"],
            "corroborating": {
                "path": "data/gec-fluency/train/target-sentences/0103.a1.txt",
                "partition": "gec-fluency/train",
                "annotator": "a1",
                "selection": "exact corrected sentence at line 12",
                "document_sha256": "5ecb845f2b445e13af3421456013850a53cc7b325edd1b46d4b1638a4c2d00dc",
                "retrieved_text": "Це свідчить про те, що вони відігравали велику роль для держави.",
            },
        },
        {
            "canary_id": "qualified-human-deletion",
            "path": "data/gec-fluency/train/annotated/0022.a1.ann",
            "partition": "gec-fluency/train",
            "annotator": "a1",
            "selection": "sentence containing a single F/PoorFlow deletion",
            "document_sha256": "75f61fe24f29d8e3ae686a5332d947f14ddd888217612e3956672f387077d353",
            "source_text": deletion_source,
            "corrected_text": deletion_source[:deletion_start] + deletion_source[deletion_start + 2 :],
            "evidence_text": "Чи це те {ж =>:::error_type=F/PoorFlow}саме, що й бути Іншим, чи ні?",
            "edit_shape": "deletion",
            "edits": [{"start": deletion_start, "end": deletion_start + 2, "replacement": ""}],
            "constructions": ["те ж саме"],
            "corroborating": {
                "path": "data/gec-fluency/train/target-sentences/0022.a1.txt",
                "partition": "gec-fluency/train",
                "annotator": "a1",
                "selection": "exact corrected sentence at line 12",
                "document_sha256": "1d364dc0eab80b5ea0688386d742fa203f81942d74ad9adc4488c1c129c23922",
                "retrieved_text": "Чи це те саме, що й бути Іншим, чи ні?",
            },
        },
        {
            "canary_id": "qualified-human-reordering",
            "path": "data/gec-fluency/train/annotated/1851.a1.ann",
            "partition": "gec-fluency/train",
            "annotator": "a1",
            "selection": "first sentence, paired F/PoorFlow move annotations",
            "document_sha256": "b3a0f8e9cdbfa1c5ce73cd183e1fe614481c0e252b245ae64db5da208117e7b0",
            "source_text": reorder_source,
            "corrected_text": reorder_source[:reorder_start]
            + "два чи три дні"
            + reorder_source[reorder_start + len(reorder_old) :],
            "evidence_text": "Після цього разу {дні =>:::error_type=F/PoorFlow}два чи три{=> дні:::error_type=F/PoorFlow} вона бачила перед собою якісь шаблі, що тьмяно відсвічували і лежали у відкритих чорних футлярах, і збагнула, що це ріки.",
            "edit_shape": "reordering",
            "edits": [
                {"start": reorder_start, "end": reorder_start + len(reorder_old), "replacement": "два чи три дні"}
            ],
            "constructions": ["разу дні два чи три вона"],
            "corroborating": {
                "path": "data/gec-fluency/train/target-sentences/1851.a1.txt",
                "partition": "gec-fluency/train",
                "annotator": "a1",
                "selection": "exact corrected sentence at line 1",
                "document_sha256": "321c227004828733a396cf7cfa1397df3fba6713a55756bf7a8eae531a56d2b9",
                "retrieved_text": "Після цього разу два чи три дні вона бачила перед собою якісь шаблі, що тьмяно відсвічували і лежали у відкритих чорних футлярах, і збагнула, що це ріки.",
            },
        },
        {
            "canary_id": "qualified-human-punctuation-only",
            "path": "data/gec-fluency/train/annotated/0000.a1.ann",
            "partition": "gec-fluency/train",
            "annotator": "a1",
            "selection": "sentence containing a single Punctuation substitution",
            "document_sha256": "65795f5bfc58512e579c7b5bfd2b0785f8b44ec045c33f3267c88443a18b7e93",
            "source_text": punctuation_source,
            "corrected_text": punctuation_source[:punctuation_start]
            + "—"
            + punctuation_source[punctuation_start + 1 :],
            "evidence_text": "Але не думаю, що проблема у самому ресурсі {–=>—:::error_type=Punctuation} він просто дав людям те, чого вони хотіли.",
            "edit_shape": "punctuation_only",
            "edits": [{"start": punctuation_start, "end": punctuation_start + 1, "replacement": "—"}],
            "constructions": ["ресурсі – він"],
            "corroborating": {
                "path": "data/gec-fluency/train/target-sentences/0000.a1.txt",
                "partition": "gec-fluency/train",
                "annotator": "a1",
                "selection": "exact corrected sentence at line 78",
                "document_sha256": "f5c3f762682673568162109034ee65e3d753eaa8c4cadef0cb68d5431d6c63d0",
                "retrieved_text": "Але не думаю, що проблема у самому ресурсі — він просто дав людям те, чого вони хотіли.",
            },
        },
        {
            "canary_id": "qualified-human-multi-edit",
            "path": "data/gec-fluency/train/annotated/0009.a1.ann",
            "partition": "gec-fluency/train",
            "annotator": "a1",
            "selection": "sentence containing punctuation plus paired F/PoorFlow move annotations",
            "document_sha256": "2258d26e1ce03b4e14502d785fa6971bf3117a1289951b82f758c0ab27315003",
            "source_text": multi_source,
            "corrected_text": (
                "Цього разу нічого грандіозного не планую, тому дрес-код вільний, шашликовий, я сказала б."
            ),
            "evidence_text": "Цього разу нічого грандіозного не планую, тому дрес-код вільний, шашликовий{=>,:::error_type=Punctuation} я{ б=>:::error_type=F/PoorFlow} сказала{=> б:::error_type=F/PoorFlow}.",
            "edit_shape": "multi_edit",
            "edits": [
                {"start": comma_at, "end": comma_at, "replacement": ","},
                {"start": b_start, "end": b_start + 2, "replacement": ""},
                {"start": final_b_at, "end": final_b_at, "replacement": " б"},
            ],
            "constructions": ["шашликовий я б сказала"],
            "corroborating": {
                "path": "data/gec-fluency/train/target-sentences/0009.a1.txt",
                "partition": "gec-fluency/train",
                "annotator": "a1",
                "selection": "exact corrected sentence at line 11",
                "document_sha256": "94cdaa4595d2159154922dc788a10c437278ca2e7fdc90c6abedc5c1200f8e1e",
                "retrieved_text": "Цього разу нічого грандіозного не планую, тому дрес-код вільний, шашликовий, я сказала б.",
            },
        },
    ]


def build_canary_battery() -> dict[str, Any]:
    packets = [_build(spec) for spec in _specs()]
    battery = {
        "schema_version": "phase3_linguistic_canary_battery_v3",
        "source_corpus": {"repository": UA_GEC_REPOSITORY, "commit": UA_GEC_COMMIT, "license": "CC BY 4.0"},
        "provider_calls": False,
        "packets": packets,
    }
    battery["battery_sha256"] = representation.sha256_value(battery)
    return battery


def verify_pinned_corpus(battery: Mapping[str, Any], checkout: Path) -> dict[str, Any]:
    """Verify every embedded locator, document hash, and exact retrieval locally."""
    root = checkout.resolve()
    if not root.is_dir():
        raise representation.LinguisticRepresentationError("UA-GEC checkout is missing")
    try:
        commit = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise representation.LinguisticRepresentationError("cannot verify UA-GEC checkout commit") from exc
    if commit != UA_GEC_COMMIT:
        raise representation.LinguisticRepresentationError("UA-GEC checkout is not at the pinned commit")

    manifest: list[dict[str, str]] = []
    document_paths: set[str] = set()
    for packet in battery["packets"]:
        evidence_groups = (
            ("correction", packet["evidence"]["correction_evidence"], "evidence_text", "evidence_text_sha256"),
            (
                "corroboration",
                packet["evidence"]["corroborating_corpus_evidence"],
                "retrieved_text",
                "retrieved_text_sha256",
            ),
        )
        for kind, evidence_items, text_field, text_hash_field in evidence_groups:
            for item in evidence_items:
                relative = Path(item["locator"]["path"])
                document = (root / relative).resolve()
                if not document.is_relative_to(root) or not document.is_file():
                    raise representation.LinguisticRepresentationError(
                        "evidence locator escapes or misses pinned checkout"
                    )
                observed_hash = _sha256_file(document)
                if observed_hash != item["source_document_bytes_sha256"]:
                    raise representation.LinguisticRepresentationError("evidence document bytes hash mismatch")
                evidence_text = item[text_field]
                if representation.sha256_text(evidence_text) != item[text_hash_field]:
                    raise representation.LinguisticRepresentationError("evidence retrieval text hash mismatch")
                if evidence_text not in document.read_text(encoding="utf-8"):
                    raise representation.LinguisticRepresentationError(
                        "exact evidence text is absent from pinned document"
                    )
                relative_text = relative.as_posix()
                document_paths.add(relative_text)
                manifest.append(
                    {
                        "kind": kind,
                        "path": relative_text,
                        "document_sha256": observed_hash,
                        "retrieval_sha256": item[text_hash_field],
                    }
                )
    manifest.sort(key=lambda item: (item["kind"], item["path"], item["retrieval_sha256"]))
    receipt = {
        "status": "verified_pinned_public_checkout",
        "repository": UA_GEC_REPOSITORY,
        "commit": commit,
        "documents_verified": len(document_paths),
        "retrievals_verified": len(manifest),
        "manifest_sha256": representation.sha256_value(manifest),
        "source_text_in_receipt": False,
    }
    receipt["verification_sha256"] = representation.sha256_value(receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--ua-gec-root", type=Path)
    args = parser.parse_args()
    battery = build_canary_battery()
    if args.ua_gec_root:
        battery["source_corpus_verification"] = verify_pinned_corpus(battery, args.ua_gec_root)
    rendered = json.dumps(battery, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
