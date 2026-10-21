from __future__ import annotations

import csv
import gzip
import json
import stat
import zipfile
from pathlib import Path

import pytest

from scripts.projects.open_model_data import phase3_historical_materialization as materialization
from scripts.projects.open_model_data.phase3_historical_materialization import (
    HistoricalMaterializationError,
    build_ud_record,
    file_sha256,
    materialize_canary,
    paragraph_units,
    parse_conllu,
)

UD_FIXTURE = """# newdoc = uk__fixture__1413
# lang = orv-uk
# created = 1413
# title = Fixture charter
# sent_id = uk__fixture__1413-1
# text = Во имя Отца и С[ы]на.
1\tВо\tво\tADP\t_\t_\t2\tcase\t_\t_
2\tимя\tимя\tNOUN\t_\tCase=Acc\t0\troot\t_\t_
3\tОтца\tотецъ\tNOUN\t_\tCase=Gen\t2\tnmod\t_\t_
4\tи\tи\tCCONJ\t_\t_\t5\tcc\t_\t_
5\tС[ы]на\tсынъ\tNOUN\t_\tCase=Gen\t3\tconj\t_\tSpaceAfter=No
6\t.\t.\tPUNCT\t_\t_\t2\tpunct\t_\t_

# newdoc = adjacent__unresolved
# sent_id = adjacent__unresolved-1
# text = Не класифікувати.
1\tНе\tне\tPART\t_\t_\t2\tadvmod\t_\t_
2\tкласифікувати\tкласифікувати\tVERB\t_\tVerbForm=Inf\t0\troot\t_\tSpaceAfter=No
3\t.\t.\tPUNCT\t_\t_\t2\tpunct\t_\t_
"""

PLUG_HEADERS = [
    "path",
    "doc.name",
    "doc.date",
    "doc.publicationYear",
    "doc.tokenCount",
    "doc.sentenceCount",
    "doc.original",
    "doc.style",
    "doc.genre",
    "doc.source",
    "doc.orthography",
    "doc.mediaName",
    "doc.author",
    "doc.authorSex",
    "doc.authorBorn",
    "doc.authorLocCode",
    "doc.translator",
    "doc.translatorSex",
    "doc.translatorBorn",
    "doc.translatorLocCode",
    "doc.publication",
    "doc.publicationCity",
    "doc.publisher",
]


def _make_inputs(tmp_path: Path, *, unsafe_member: bool = False) -> tuple[Path, Path, Path]:
    ud_dir = tmp_path / "ud"
    ud_dir.mkdir()
    ud_file = ud_dir / "fixture.conllu"
    ud_file.write_text(UD_FIXTURE, encoding="utf-8")

    metadata = tmp_path / "metadata.psv"
    rows = [
        {
            "path": "A/uk.txt",
            "doc.name": "Ukrainian fixture",
            "doc.date": "1913",
            "doc.publicationYear": "",
            "doc.tokenCount": "8",
            "doc.sentenceCount": "2",
            "doc.original": "UK",
            "doc.style": "FIC",
            "doc.genre": "",
            "doc.source": "PRI",
            "doc.orthography": "",
            "doc.mediaName": "",
            "doc.author": "Fixture",
            "doc.authorSex": "",
            "doc.authorBorn": "",
            "doc.authorLocCode": "UA-X",
            "doc.translator": "",
            "doc.translatorSex": "",
            "doc.translatorBorn": "",
            "doc.translatorLocCode": "",
            "doc.publication": "",
            "doc.publicationCity": "",
            "doc.publisher": "",
        },
        {
            "path": "B/context.txt",
            "doc.name": "Context fixture",
            "doc.date": "1914",
            "doc.publicationYear": "",
            "doc.tokenCount": "3",
            "doc.sentenceCount": "1",
            "doc.original": "PL",
            "doc.style": "",
            "doc.genre": "",
            "doc.source": "PRI",
            "doc.orthography": "ZHEL",
            "doc.mediaName": "",
            "doc.author": "Fixture",
            "doc.authorSex": "",
            "doc.authorBorn": "",
            "doc.authorLocCode": "",
            "doc.translator": "",
            "doc.translatorSex": "",
            "doc.translatorBorn": "",
            "doc.translatorLocCode": "",
            "doc.publication": "",
            "doc.publicationCity": "",
            "doc.publisher": "",
        },
    ]
    with metadata.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=PLUG_HEADERS, delimiter="|", quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)

    archive = tmp_path / "texts.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as handle:
        handle.writestr("PLuG2_texts/", "")
        handle.writestr("PLuG2_texts/A/", "")
        handle.writestr("PLuG2_texts/B/", "")
        handle.writestr("PLuG2_texts/A/uk.txt", "Перший рядок.\n\nДругий рядок.")
        handle.writestr("PLuG2_texts/B/context.txt", "Nie kandydat.")
        if unsafe_member:
            handle.writestr("../escape.txt", "forbidden")
    return ud_dir, archive, metadata


def _fixture_arguments(
    *,
    ud_dir: Path,
    archive: Path,
    metadata: Path,
    output: Path,
    expected_ud_denominator: dict[str, int] | None = None,
    expected_plug2_denominator: dict[str, int] | None = None,
) -> dict[str, object]:
    return {
        "ud_dir": ud_dir,
        "plug2_archive": archive,
        "plug2_metadata": metadata,
        "private_output_dir": output,
        "receipt_output": output / "receipt.json",
        "ud_fraction": 0.01,
        "plug2_fraction": 0.01,
        "expected_ud_sha256": {"fixture.conllu": file_sha256(ud_dir / "fixture.conllu")},
        "expected_plug2_archive_sha256": file_sha256(archive),
        "expected_plug2_metadata_sha256": file_sha256(metadata),
        "expected_ud_denominator": expected_ud_denominator or {"documents": 1, "sentences": 1, "token_rows": 6},
        "expected_plug2_denominator": expected_plug2_denominator
        or {
            "documents": 2,
            "token_sum": 11,
            "uk_documents": 1,
            "non_uk_or_unknown_documents": 1,
        },
    }


def _run(tmp_path: Path, *, unsafe_member: bool = False):
    ud_dir, archive, metadata = _make_inputs(tmp_path, unsafe_member=unsafe_member)
    output = tmp_path / "private"
    receipt_path = output / "receipt.json"
    ud_hash = file_sha256(ud_dir / "fixture.conllu")
    receipt = materialize_canary(
        ud_dir=ud_dir,
        plug2_archive=archive,
        plug2_metadata=metadata,
        private_output_dir=output,
        receipt_output=receipt_path,
        ud_fraction=0.01,
        plug2_fraction=0.01,
        expected_ud_sha256={"fixture.conllu": ud_hash},
        expected_plug2_archive_sha256=file_sha256(archive),
        expected_plug2_metadata_sha256=file_sha256(metadata),
        expected_ud_denominator={"documents": 1, "sentences": 1, "token_rows": 6},
        expected_plug2_denominator={
            "documents": 2,
            "token_sum": 11,
            "uk_documents": 1,
            "non_uk_or_unknown_documents": 1,
        },
    )
    return receipt, output, receipt_path


def test_conllu_analysis_preserves_authoritative_source_tokenization(tmp_path: Path) -> None:
    ud_dir, _, _ = _make_inputs(tmp_path)
    source_hash = file_sha256(ud_dir / "fixture.conllu")
    sentences = parse_conllu(ud_dir / "fixture.conllu", source_file_sha256=source_hash)
    record = build_ud_record(sentences[0])
    analysis = next(item for item in record["linguistic_analyses"] if item["source_surface"] == "С[ы]на")
    assert analysis["token_ids"] == ["tok:000005"]
    assert record["text_layers"][0]["tokens"][4]["text"] == "С[ы]на"
    assert record["analysis_provenance"]["tokenization_alignment"] == "exact"
    assert record["safeguards"]["modern_correction_eligible"] is False
    assert record["provider_calls"] is False


def test_conllu_source_boundaries_override_generic_compound_tokenization(tmp_path: Path) -> None:
    path = tmp_path / "compound.conllu"
    path.write_text(
        """# newdoc = uk__compound__1436
# lang = orv-uk
# sent_id = uk__compound__1436-1
# text = А-любо.
1\tА\tа\tCCONJ\t_\t_\t3\tcc\t_\tSpaceAfter=No
2\t-\t-\tPUNCT\t_\t_\t1\tpunct\t_\tSpaceAfter=No
3\tлюбо\tлюбо\tCCONJ\t_\t_\t0\troot\t_\tSpaceAfter=No
4\t.\t.\tPUNCT\t_\t_\t3\tpunct\t_\t_
""",
        encoding="utf-8",
    )
    sentence = parse_conllu(path, source_file_sha256=file_sha256(path))[0]
    record = build_ud_record(sentence)

    assert [token["text"] for token in record["text_layers"][0]["tokens"]] == ["А", "-", "любо", "."]
    assert [analysis["token_ids"] for analysis in record["linguistic_analyses"]] == [
        ["tok:000001"],
        ["tok:000002"],
        ["tok:000003"],
        ["tok:000004"],
    ]


def test_rejects_cyclic_ud_dependency_graph(tmp_path: Path) -> None:
    ud_dir, _, _ = _make_inputs(tmp_path)
    path = ud_dir / "fixture.conllu"
    path.write_text(
        UD_FIXTURE.replace(
            "2\tимя\tимя\tNOUN\t_\tCase=Acc\t0\troot",
            "2\tимя\tимя\tNOUN\t_\tCase=Acc\t5\troot",
        ),
        encoding="utf-8",
    )
    sentences = parse_conllu(path, source_file_sha256=file_sha256(path))
    with pytest.raises(HistoricalMaterializationError, match="dependency cycle"):
        build_ud_record(sentences[0])


def test_rejects_unknown_ud_dependency_head(tmp_path: Path) -> None:
    ud_dir, _, _ = _make_inputs(tmp_path)
    path = ud_dir / "fixture.conllu"
    path.write_text(
        UD_FIXTURE.replace(
            "2\tимя\tимя\tNOUN\t_\tCase=Acc\t0\troot",
            "2\tимя\tимя\tNOUN\t_\tCase=Acc\t99\troot",
        ),
        encoding="utf-8",
    )
    sentences = parse_conllu(path, source_file_sha256=file_sha256(path))
    with pytest.raises(HistoricalMaterializationError, match="dependency head is unknown"):
        build_ud_record(sentences[0])


def test_rejects_duplicate_ud_token_id(tmp_path: Path) -> None:
    ud_dir, _, _ = _make_inputs(tmp_path)
    path = ud_dir / "fixture.conllu"
    path.write_text(
        UD_FIXTURE.replace(
            "3\tОтца\tотецъ\tNOUN\t_\tCase=Gen\t2\tnmod",
            "2\tОтца\tотецъ\tNOUN\t_\tCase=Gen\t2\tnmod",
        ),
        encoding="utf-8",
    )
    with pytest.raises(HistoricalMaterializationError, match="duplicate CoNLL-U token id"):
        parse_conllu(path, source_file_sha256=file_sha256(path))


def test_ud_overlap_is_rejected(tmp_path: Path) -> None:
    ud_dir, _, _ = _make_inputs(tmp_path)
    path = ud_dir / "fixture.conllu"
    sentence = parse_conllu(path, source_file_sha256=file_sha256(path))[0]
    text, spans = materialization._ud_surface(sentence)
    overlapping_spans = list(spans)
    overlapping_spans[1] = overlapping_spans[0]
    with pytest.raises(HistoricalMaterializationError, match="stale UD analysis span"):
        materialization._ud_analyses(sentence, text, overlapping_spans)


def test_ud_surface_preserves_source_comment_whitespace(tmp_path: Path) -> None:
    ud_dir, _, _ = _make_inputs(tmp_path)
    path = ud_dir / "fixture.conllu"
    path.write_text(
        UD_FIXTURE.replace(
            "# text = Во имя Отца и С[ы]на.",
            "# text = Во  имя Отца и С[ы]на.",
        ),
        encoding="utf-8",
    )
    sentence = parse_conllu(path, source_file_sha256=file_sha256(path))[0]
    text, spans = materialization._ud_surface(sentence)
    assert text == "Во  имя Отца и С[ы]на."
    assert [text[start:end] for start, end in spans] == [
        "Во",
        "имя",
        "Отца",
        "и",
        "С[ы]на",
        ".",
    ]
    record = build_ud_record(sentence)
    assert record["text_layers"][0]["text"] == text


def test_ud_surface_rejects_non_whitespace_comment_disagreement(tmp_path: Path) -> None:
    ud_dir, _, _ = _make_inputs(tmp_path)
    path = ud_dir / "fixture.conllu"
    path.write_text(
        UD_FIXTURE.replace(
            "# text = Во имя Отца и С[ы]на.",
            "# text = Во інше Отца и С[ы]на.",
        ),
        encoding="utf-8",
    )
    sentence = parse_conllu(path, source_file_sha256=file_sha256(path))[0]
    with pytest.raises(HistoricalMaterializationError, match="disagrees with token rows"):
        build_ud_record(sentence)


def test_canary_is_deterministic_text_private_and_receipt_text_free(tmp_path: Path) -> None:
    receipt, output, receipt_path = _run(tmp_path)
    first_hashes = {path.name: file_sha256(path) for path in output.iterdir()}
    second_output = tmp_path / "private-second"
    second_receipt = second_output / "receipt.json"
    ud_dir = tmp_path / "ud"
    materialize_canary(
        ud_dir=ud_dir,
        plug2_archive=tmp_path / "texts.zip",
        plug2_metadata=tmp_path / "metadata.psv",
        private_output_dir=second_output,
        receipt_output=second_receipt,
        ud_fraction=0.01,
        plug2_fraction=0.01,
        expected_ud_sha256={"fixture.conllu": file_sha256(ud_dir / "fixture.conllu")},
        expected_plug2_archive_sha256=file_sha256(tmp_path / "texts.zip"),
        expected_plug2_metadata_sha256=file_sha256(tmp_path / "metadata.psv"),
        expected_ud_denominator={"documents": 1, "sentences": 1, "token_rows": 6},
        expected_plug2_denominator={
            "documents": 2,
            "token_sum": 11,
            "uk_documents": 1,
            "non_uk_or_unknown_documents": 1,
        },
    )
    assert first_hashes == {path.name: file_sha256(path) for path in output.iterdir()}
    assert receipt == json.loads(second_receipt.read_text(encoding="utf-8"))
    receipt_text = receipt_path.read_text(encoding="utf-8")
    assert "Перший рядок" not in receipt_text
    assert "Во имя" not in receipt_text
    assert receipt["denominators"]["plug2_original_counts"] == {"PL": 1, "UK": 1}
    assert receipt["residuals"]["plug2_non_uk_or_unknown_excluded"] is True
    with gzip.open(output / "plug2-uk-canary.jsonl.gz", "rt", encoding="utf-8") as handle:
        records = [json.loads(line) for line in handle]
    assert len(records) == 2
    assert all(item["historical_context"]["orthography"] is None for item in records)


def test_paragraph_unitization_preserves_exact_offsets() -> None:
    source = "  Перший.  \r\n\r\nДругий.\n"
    units = paragraph_units(source)
    assert [(start, end) for start, end, _ in units] == [(0, 11), (15, 22)]
    assert all(source[start:end] == text for start, end, text in units)


def test_rejects_canary_fraction_above_one_percent(tmp_path: Path) -> None:
    ud_dir, archive, metadata = _make_inputs(tmp_path)
    with pytest.raises(HistoricalMaterializationError, match="canary fraction"):
        materialize_canary(
            ud_dir=ud_dir,
            plug2_archive=archive,
            plug2_metadata=metadata,
            private_output_dir=tmp_path / "private",
            receipt_output=tmp_path / "private" / "receipt.json",
            ud_fraction=0.02,
            expected_ud_sha256={"fixture.conllu": file_sha256(ud_dir / "fixture.conllu")},
            expected_plug2_archive_sha256=file_sha256(archive),
            expected_plug2_metadata_sha256=file_sha256(metadata),
            expected_ud_denominator={"documents": 1, "sentences": 1, "token_rows": 6},
            expected_plug2_denominator={
                "documents": 2,
                "token_sum": 11,
                "uk_documents": 1,
                "non_uk_or_unknown_documents": 1,
            },
        )


def test_rejects_private_output_inside_any_git_checkout(tmp_path: Path) -> None:
    checkout = tmp_path / "other-checkout"
    (checkout / ".git").mkdir(parents=True)
    output = checkout / "private-output"
    with pytest.raises(HistoricalMaterializationError, match="inside a Git checkout"):
        materialize_canary(
            ud_dir=tmp_path / "missing-ud",
            plug2_archive=tmp_path / "missing.zip",
            plug2_metadata=tmp_path / "missing.psv",
            private_output_dir=output,
            receipt_output=output / "receipt.json",
        )


def test_rejects_existing_immutable_output(tmp_path: Path) -> None:
    ud_dir, archive, metadata = _make_inputs(tmp_path)
    output = tmp_path / "private"
    output.mkdir()
    with pytest.raises(HistoricalMaterializationError, match="already exists"):
        materialize_canary(**_fixture_arguments(ud_dir=ud_dir, archive=archive, metadata=metadata, output=output))


def test_rejects_hash_drift_before_output(tmp_path: Path) -> None:
    ud_dir, archive, metadata = _make_inputs(tmp_path)
    with pytest.raises(HistoricalMaterializationError, match="SHA-256 mismatch"):
        materialize_canary(
            ud_dir=ud_dir,
            plug2_archive=archive,
            plug2_metadata=metadata,
            private_output_dir=tmp_path / "private",
            receipt_output=tmp_path / "private" / "receipt.json",
            expected_ud_sha256={"fixture.conllu": "0" * 64},
            expected_plug2_archive_sha256=file_sha256(archive),
            expected_plug2_metadata_sha256=file_sha256(metadata),
            expected_ud_denominator={"documents": 1, "sentences": 1, "token_rows": 6},
            expected_plug2_denominator={
                "documents": 2,
                "token_sum": 11,
                "uk_documents": 1,
                "non_uk_or_unknown_documents": 1,
            },
        )
    assert not (tmp_path / "private").exists()


def test_rejects_projection_above_ceiling_without_promotion(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ud_dir, archive, metadata = _make_inputs(tmp_path)
    output = tmp_path / "private"
    monkeypatch.setattr(materialization, "OUTPUT_CEILING_GIB", 0.0)
    with pytest.raises(HistoricalMaterializationError, match="exceeds 5 GiB ceiling"):
        materialize_canary(**_fixture_arguments(ud_dir=ud_dir, archive=archive, metadata=metadata, output=output))
    assert not output.exists()
    assert not list(tmp_path.glob(".private.staging-*"))


def test_rejects_unsafe_zip_member(tmp_path: Path) -> None:
    ud_dir, archive, metadata = _make_inputs(tmp_path, unsafe_member=True)
    with pytest.raises(HistoricalMaterializationError, match="unsafe ZIP member"):
        materialize_canary(
            ud_dir=ud_dir,
            plug2_archive=archive,
            plug2_metadata=metadata,
            private_output_dir=tmp_path / "private",
            receipt_output=tmp_path / "private" / "receipt.json",
            expected_ud_sha256={"fixture.conllu": file_sha256(ud_dir / "fixture.conllu")},
            expected_plug2_archive_sha256=file_sha256(archive),
            expected_plug2_metadata_sha256=file_sha256(metadata),
            expected_ud_denominator={"documents": 1, "sentences": 1, "token_rows": 6},
            expected_plug2_denominator={
                "documents": 2,
                "token_sum": 11,
                "uk_documents": 1,
                "non_uk_or_unknown_documents": 1,
            },
        )
    assert not (tmp_path / "private").exists()


def test_rejects_zip_symlink_member_before_output(tmp_path: Path) -> None:
    ud_dir, archive, metadata = _make_inputs(tmp_path)
    symlink = zipfile.ZipInfo("PLuG2_texts/link.txt")
    symlink.create_system = 3
    symlink.external_attr = (stat.S_IFLNK | 0o777) << 16
    with zipfile.ZipFile(archive, "a") as handle:
        handle.writestr(symlink, "A/uk.txt")
    output = tmp_path / "private"
    with pytest.raises(HistoricalMaterializationError, match="unsafe ZIP symlink member"):
        materialize_canary(**_fixture_arguments(ud_dir=ud_dir, archive=archive, metadata=metadata, output=output))
    assert not output.exists()


def test_rejects_unexpected_zip_root_before_output(tmp_path: Path) -> None:
    ud_dir, archive, metadata = _make_inputs(tmp_path)
    with zipfile.ZipFile(archive, "a") as handle:
        handle.writestr("WrongRoot/extra.txt", "forbidden")
    output = tmp_path / "private"
    with pytest.raises(HistoricalMaterializationError, match="unexpected PluG2 ZIP root"):
        materialize_canary(**_fixture_arguments(ud_dir=ud_dir, archive=archive, metadata=metadata, output=output))
    assert not output.exists()


def test_rejects_duplicate_zip_member_before_output(tmp_path: Path) -> None:
    ud_dir, archive, metadata = _make_inputs(tmp_path)
    with zipfile.ZipFile(archive, "a") as handle, pytest.warns(UserWarning, match="Duplicate name"):
        handle.writestr("PLuG2_texts/A/uk.txt", "duplicate")
    output = tmp_path / "private"
    with pytest.raises(HistoricalMaterializationError, match="duplicate PluG2 ZIP member"):
        materialize_canary(**_fixture_arguments(ud_dir=ud_dir, archive=archive, metadata=metadata, output=output))
    assert not output.exists()


@pytest.mark.parametrize(
    ("denominator", "expected_message"),
    [
        ("ud", "UD candidate denominator drift"),
        ("plug2", "PluG2 denominator drift"),
    ],
)
def test_rejects_denominator_drift_before_output(
    tmp_path: Path,
    denominator: str,
    expected_message: str,
) -> None:
    ud_dir, archive, metadata = _make_inputs(tmp_path)
    output = tmp_path / "private"
    arguments = _fixture_arguments(ud_dir=ud_dir, archive=archive, metadata=metadata, output=output)
    if denominator == "ud":
        arguments["expected_ud_denominator"] = {"documents": 2, "sentences": 1, "token_rows": 6}
    else:
        arguments["expected_plug2_denominator"] = {
            "documents": 3,
            "token_sum": 11,
            "uk_documents": 1,
            "non_uk_or_unknown_documents": 1,
        }
    with pytest.raises(HistoricalMaterializationError, match=expected_message):
        materialize_canary(**arguments)
    assert not output.exists()


def test_rejects_malformed_metadata_integer_before_output(tmp_path: Path) -> None:
    ud_dir, archive, metadata = _make_inputs(tmp_path)
    metadata.write_text(metadata.read_text(encoding="utf-8").replace('"8"', '"not-an-int"', 1), encoding="utf-8")
    output = tmp_path / "private"
    with pytest.raises(HistoricalMaterializationError, match="invalid PluG2 integer field"):
        materialize_canary(**_fixture_arguments(ud_dir=ud_dir, archive=archive, metadata=metadata, output=output))
    assert not output.exists()


def test_receipt_schema_rejects_unbounded_count_keys(tmp_path: Path) -> None:
    receipt, _, _ = _run(tmp_path)
    receipt["denominators"]["plug2_original_counts"] = {"raw prose": 1}
    with pytest.raises(HistoricalMaterializationError, match="receipt schema violation"):
        materialization._validate_receipt(receipt)


def test_rejects_metadata_archive_path_mismatch(tmp_path: Path) -> None:
    ud_dir, archive, metadata = _make_inputs(tmp_path)
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as handle:
        handle.writestr("PLuG2_texts/A/uk.txt", "Перший рядок.")
    with pytest.raises(HistoricalMaterializationError, match="path-set mismatch"):
        materialize_canary(
            ud_dir=ud_dir,
            plug2_archive=archive,
            plug2_metadata=metadata,
            private_output_dir=tmp_path / "private",
            receipt_output=tmp_path / "private" / "receipt.json",
            expected_ud_sha256={"fixture.conllu": file_sha256(ud_dir / "fixture.conllu")},
            expected_plug2_archive_sha256=file_sha256(archive),
            expected_plug2_metadata_sha256=file_sha256(metadata),
            expected_ud_denominator={"documents": 1, "sentences": 1, "token_rows": 6},
            expected_plug2_denominator={
                "documents": 2,
                "token_sum": 11,
                "uk_documents": 1,
                "non_uk_or_unknown_documents": 1,
            },
        )
