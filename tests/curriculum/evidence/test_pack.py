"""Tests for module evidence pack builder and verifier (Brief A2)."""

import hashlib
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from scripts.curriculum.evidence import codes, lock, pack, sources, verify


@pytest.fixture
def synthetic_word_store(tmp_path):
    """Minimal level word store required when building example records."""
    ev_dir = tmp_path / "evidence" / "a1"
    ev_dir.mkdir(parents=True, exist_ok=True)
    store_file = ev_dir / "_words.yaml"
    store_data = {
        "evidence_schema": 1,
        "level": "a1",
        "built_with": {
            "mcp_commit": "a" * 40,
            "sources_db": "b" * 64,
            "vesum": "c" * 64,
            "trie": "d" * 64,
            "ulif_forms": "pending",
        },
        "words": [
            {
                "id": "W-001",
                "lemma": "synthetic",
                "pos": "noun",
                "entry": {"source": "vesum", "entry_id": 10},
                "forms": [
                    {
                        "form": "synthetic",
                        "tags": "noun:inanim:f:v_naz",
                        "stress_source": "none",
                        "stressed": "synthetic",
                    }
                ],
            }
        ],
    }
    lock.write(store_file, lock.yaml_bytes(store_data))
    return ev_dir


def test_span_matches(synthetic_sources, synthetic_standard, synthetic_word_store, tmp_path):
    """A span that matches -> quote, sha256, page from the section."""
    req_file = tmp_path / "req.yaml"
    req_file.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "module": "a1/test-mod",
                "texts": [
                    {
                        "id": "T-001",
                        "source": {"table": "textbooks", "chunk_id": "chunk-1"},
                        "span": {"first_words": "synthetic-first", "last_words": "synthetic-last"},
                        "supports": "Grounds the first point.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    src = sources.Sources(sources_db=synthetic_sources, standard_path=synthetic_standard)
    res = pack.build_pack(
        "a1",
        "test-mod",
        req_file,
        evidence_dir=synthetic_word_store,
        sources_instance=src,
        offline=True,
    )
    assert res["status"] == "ok"
    pack_data = res["pack"]
    text_rec = pack_data["texts"][0]
    assert text_rec["quote"] == "synthetic-first middle text synthetic-last"
    assert text_rec["sha256"] == hashlib.sha256(text_rec["quote"].encode("utf-8")).hexdigest()
    assert text_rec["source"]["page"] == 42
    assert text_rec["source"]["section_id"] == 10
    assert text_rec["source"]["file"] == "synthetic-file-1"


def test_chunk_without_section_page_null(synthetic_sources, synthetic_standard, synthetic_word_store, tmp_path):
    """A chunk without a section -> page: null."""
    req_file = tmp_path / "req.yaml"
    req_file.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "module": "a1/test-mod",
                "texts": [
                    {
                        "id": "T-002",
                        "source": {"table": "textbooks", "chunk_id": "chunk-3"},
                        "span": {"first_words": "synthetic-start", "last_words": "synthetic-end"},
                        "supports": "Grounds no section chunk.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    src = sources.Sources(sources_db=synthetic_sources, standard_path=synthetic_standard)
    res = pack.build_pack(
        "a1",
        "test-mod",
        req_file,
        evidence_dir=synthetic_word_store,
        sources_instance=src,
        offline=True,
    )
    assert res["status"] == "ok"
    text_rec = res["pack"]["texts"][0]
    assert text_rec["source"]["page"] is None
    assert text_rec["source"]["section_id"] is None


def test_span_does_not_match_fails_naming_id_and_chunk(
    synthetic_sources, synthetic_standard, synthetic_word_store, tmp_path
):
    """A span that does not match -> build fails naming id and chunk."""
    req_file = tmp_path / "req.yaml"
    req_file.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "module": "a1/test-mod",
                "texts": [
                    {
                        "id": "T-003",
                        "source": {"table": "textbooks", "chunk_id": "chunk-1"},
                        "span": {"first_words": "nonexistent-start", "last_words": "synthetic-last"},
                        "supports": "Fails.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    src = sources.Sources(sources_db=synthetic_sources, standard_path=synthetic_standard)
    with pytest.raises(ValueError) as excinfo:
        pack.build_pack(
            "a1",
            "test-mod",
            req_file,
            evidence_dir=synthetic_word_store,
            sources_instance=src,
            offline=True,
        )
    err = str(excinfo.value)
    assert codes.SPAN_MISMATCH in err
    assert "T-003" in err
    assert "chunk-1" in err


def test_span_with_two_matches_build_fails(synthetic_sources, synthetic_standard, synthetic_word_store, tmp_path):
    """A span with two matches -> build fails."""
    # Insert a duplicate phrase into chunk-1
    with sqlite3.connect(synthetic_sources) as conn:
        conn.execute("UPDATE textbooks SET text = 'repeated repeated middle repeated' WHERE chunk_id = 'chunk-1'")

    req_file = tmp_path / "req.yaml"
    req_file.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "module": "a1/test-mod",
                "texts": [
                    {
                        "id": "T-004",
                        "source": {"table": "textbooks", "chunk_id": "chunk-1"},
                        "span": {"first_words": "repeated", "last_words": "repeated"},
                        "supports": "Two matches fail.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    src = sources.Sources(sources_db=synthetic_sources, standard_path=synthetic_standard)
    with pytest.raises(ValueError) as excinfo:
        pack.build_pack(
            "a1",
            "test-mod",
            req_file,
            evidence_dir=synthetic_word_store,
            sources_instance=src,
            offline=True,
        )
    err = str(excinfo.value)
    assert codes.SPAN_MISMATCH in err
    assert "T-004" in err


def test_moved_chunk_id_with_same_text_passes_with_chunk_id_moved(
    synthetic_sources, synthetic_standard, synthetic_word_store, tmp_path
):
    """A moved chunk id with same text -> verify passes with chunk_id_moved."""
    req_file = tmp_path / "req.yaml"
    req_file.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "module": "a1/test-mod",
                "texts": [
                    {
                        "id": "T-001",
                        "source": {"table": "textbooks", "chunk_id": "chunk-1"},
                        "span": {"first_words": "synthetic-first", "last_words": "synthetic-last"},
                        "supports": "Moved chunk verification.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    src = sources.Sources(sources_db=synthetic_sources, standard_path=synthetic_standard)
    pack.build_pack(
        "a1",
        "test-mod",
        req_file,
        evidence_dir=synthetic_word_store,
        sources_instance=src,
        offline=True,
    )

    src.close()

    # Now simulate a chunk id shift in the database: chunk-1 is re-chunked to chunk-renamed
    with sqlite3.connect(synthetic_sources) as conn:
        conn.execute("UPDATE textbooks SET chunk_id = 'chunk-renamed' WHERE chunk_id = 'chunk-1'")

    # Pack verification should notice chunk_id is moved but quote still exists in synthetic-file-1
    src2 = sources.Sources(sources_db=synthetic_sources, standard_path=synthetic_standard)
    res = verify.verify_pack(
        "a1",
        "test-mod",
        evidence_dir=synthetic_word_store,
        sources_instance=src2,
        offline=True,
    )
    src2.close()
    assert res["status"] == "ok"
    assert "T-001" in res["chunk_id_moved"]


def test_changed_text_fails_with_both_values(synthetic_sources, synthetic_standard, synthetic_word_store, tmp_path):
    """Changed text -> fails with both values."""
    req_file = tmp_path / "req.yaml"
    req_file.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "module": "a1/test-mod",
                "errors": [
                    {
                        "id": "E-001",
                        "source": {
                            "table": "ua_gec_errors",
                            "error": "synthetic-bad",
                            "correct": "synthetic-good",
                        },
                        "pattern": "Learner error pattern",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    src = sources.Sources(sources_db=synthetic_sources, standard_path=synthetic_standard)
    pack.build_pack(
        "a1",
        "test-mod",
        req_file,
        evidence_dir=synthetic_word_store,
        sources_instance=src,
        offline=True,
    )

    src.close()

    # Simulate error row change in source DB
    with sqlite3.connect(synthetic_sources) as conn:
        conn.execute("UPDATE ua_gec_errors SET error = 'mutated-bad' WHERE id = 1")

    src2 = sources.Sources(sources_db=synthetic_sources, standard_path=synthetic_standard)
    res = verify.verify_pack(
        "a1",
        "test-mod",
        evidence_dir=synthetic_word_store,
        sources_instance=src2,
        offline=True,
    )
    src2.close()
    assert res["status"] == "failed"
    err_str = " ".join(res["errors"])
    assert codes.ERROR_MISMATCH in err_str
    # Both expected and got values must appear
    assert "synthetic-bad" in err_str
    assert "mutated-bad" in err_str


def test_error_from_gec_found_by_pair(synthetic_sources, synthetic_standard, synthetic_word_store, tmp_path):
    """An error from GEC found by its pair -> fields copied, nothing else."""
    req_file = tmp_path / "req.yaml"
    req_file.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "module": "a1/test-mod",
                "errors": [
                    {
                        "id": "E-001",
                        "source": {
                            "table": "ua_gec_errors",
                            "error": "synthetic-bad",
                            "correct": "synthetic-good",
                        },
                        "pattern": "Explanation pattern",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    src = sources.Sources(sources_db=synthetic_sources, standard_path=synthetic_standard)
    res = pack.build_pack(
        "a1",
        "test-mod",
        req_file,
        evidence_dir=synthetic_word_store,
        sources_instance=src,
        offline=True,
    )
    assert res["status"] == "ok"
    err_rec = res["pack"]["errors"][0]
    assert err_rec["id"] == "E-001"
    assert err_rec["source"] == {"table": "ua_gec_errors", "id": 1}
    assert err_rec["incorrect"] == "synthetic-bad"
    assert err_rec["correct"] == "synthetic-good"
    assert err_rec["error_type"] == "Grammar"
    assert err_rec["pattern"] == "Explanation pattern"


def test_error_pair_matching_zero_or_two_rows_fails(
    synthetic_sources, synthetic_standard, synthetic_word_store, tmp_path
):
    """A pair matching zero or two rows -> build fails."""
    src = sources.Sources(sources_db=synthetic_sources, standard_path=synthetic_standard)

    # 1. Zero rows
    req_zero = tmp_path / "req_zero.yaml"
    req_zero.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "module": "a1/test-mod",
                "errors": [
                    {
                        "id": "E-001",
                        "source": {
                            "table": "ua_gec_errors",
                            "error": "nonexistent",
                            "correct": "nonexistent",
                        },
                        "pattern": "None",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError) as exc_zero:
        pack.build_pack("a1", "test-mod", req_zero, evidence_dir=synthetic_word_store, sources_instance=src)
    assert codes.INVALID_REQUEST in str(exc_zero.value)

    # 2. Two rows
    req_two = tmp_path / "req_two.yaml"
    req_two.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "module": "a1/test-mod",
                "errors": [
                    {
                        "id": "E-002",
                        "source": {
                            "table": "ua_gec_errors",
                            "error": "synthetic-dup-err",
                            "correct": "synthetic-dup-corr",
                        },
                        "pattern": "Two rows match",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError) as exc_two:
        pack.build_pack("a1", "test-mod", req_two, evidence_dir=synthetic_word_store, sources_instance=src)
    assert codes.INVALID_REQUEST in str(exc_two.value)


def test_style_guide_copied_as_note_never_as_error(
    synthetic_sources, synthetic_standard, synthetic_word_store, tmp_path
):
    """A style-guide note -> copied as a note, never as an error."""
    req_file = tmp_path / "req.yaml"
    req_file.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "module": "a1/test-mod",
                "notes": [{"id": "N-001", "source": {"table": "style_guide", "id": 1}}],
            }
        ),
        encoding="utf-8",
    )

    src = sources.Sources(sources_db=synthetic_sources, standard_path=synthetic_standard)
    res = pack.build_pack(
        "a1",
        "test-mod",
        req_file,
        evidence_dir=synthetic_word_store,
        sources_instance=src,
        offline=True,
    )
    assert res["status"] == "ok"
    assert "notes" in res["pack"]
    assert "errors" not in res["pack"]
    note_rec = res["pack"]["notes"][0]
    assert note_rec["id"] == "N-001"
    assert note_rec["word"] == "synthetic-note-word"
    assert note_rec["text"] == "synthetic note explanation text"
    assert note_rec["source"] == {"table": "style_guide", "id": 1}


def test_request_naming_other_error_source_schema_failure(synthetic_word_store, tmp_path):
    """A request naming any other error source -> schema failure."""
    req_file = tmp_path / "req.yaml"
    req_file.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "module": "a1/test-mod",
                "errors": [
                    {
                        "id": "E-001",
                        "source": {"table": "style_guide", "error": "foo", "correct": "bar"},
                        "pattern": "Invalid table",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError) as exc:
        pack.build_pack("a1", "test-mod", req_file, evidence_dir=synthetic_word_store)
    assert codes.INVALID_REQUEST in str(exc.value)


def test_unsupported_id_dropped_from_previous_build(
    synthetic_sources, synthetic_standard, synthetic_word_store, tmp_path
):
    """A U- id present in the previous build and absent now -> unsupported_dropped."""
    src = sources.Sources(sources_db=synthetic_sources, standard_path=synthetic_standard)

    # First build with U-001 and U-002
    req1 = tmp_path / "req1.yaml"
    req1.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "module": "a1/test-mod",
                "unsupported": [
                    {"id": "U-001", "claim": "claim 1", "searches": [{"tool": "search", "query": "q1"}]},
                    {"id": "U-002", "claim": "claim 2", "searches": [{"tool": "search", "query": "q2"}]},
                ],
            }
        ),
        encoding="utf-8",
    )
    pack.build_pack("a1", "test-mod", req1, evidence_dir=synthetic_word_store, sources_instance=src, offline=True)

    # Second build drops U-002
    req2 = tmp_path / "req2.yaml"
    req2.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "module": "a1/test-mod",
                "unsupported": [{"id": "U-001", "claim": "claim 1", "searches": [{"tool": "search", "query": "q1"}]}],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError) as exc:
        pack.build_pack("a1", "test-mod", req2, evidence_dir=synthetic_word_store, sources_instance=src, offline=True)
    assert codes.UNSUPPORTED_DROPPED in str(exc.value)
    assert "U-002" in str(exc.value)


def test_strict_offline_refused(synthetic_sources, synthetic_standard, synthetic_word_store, tmp_path):
    """--strict --offline refused."""
    src = sources.Sources(sources_db=synthetic_sources, standard_path=synthetic_standard)
    res = verify.verify_pack(
        "a1",
        "test-mod",
        evidence_dir=synthetic_word_store,
        sources_instance=src,
        offline=True,
        strict=True,
    )
    assert res["status"] == "failed"
    assert any("--strict and --offline together are refused" in err for err in res["errors"])


def test_video_with_offline_checked_null_verify_not_checked(
    synthetic_sources, synthetic_standard, synthetic_word_store, tmp_path
):
    """A video with --offline -> checked: null, verify not_checked."""
    req_file = tmp_path / "req.yaml"
    req_file.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "module": "a1/test-mod",
                "videos": [
                    {
                        "id": "V-001",
                        "url": "https://example.com/video",
                        "channel": "corpus-channel",
                        "use": "Video usage description",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    src = sources.Sources(sources_db=synthetic_sources, standard_path=synthetic_standard)
    res = pack.build_pack(
        "a1",
        "test-mod",
        req_file,
        evidence_dir=synthetic_word_store,
        sources_instance=src,
        offline=True,
    )
    assert res["status"] == "ok"
    vid_rec = res["pack"]["videos"][0]
    assert vid_rec["checked"] is None

    # Verify offline reports not_checked without failing
    v_res = verify.verify_pack(
        "a1",
        "test-mod",
        evidence_dir=synthetic_word_store,
        sources_instance=src,
        offline=True,
        strict=False,
    )
    assert v_res["status"] == "ok"
    assert "V-001" in v_res["not_checked"]


def test_check_url_never_called_without_timeout():
    """check_url never called without a timeout."""
    with pytest.raises(ValueError):
        sources.check_url("https://example.com", timeout=0)
    with pytest.raises(ValueError):
        sources.check_url("https://example.com", timeout=-1.0)
    with pytest.raises(ValueError):
        sources.check_url("https://example.com", timeout=None)


def test_open_unsupported_summary_count_non_zero_under_strict_only(
    synthetic_sources, synthetic_standard, synthetic_word_store, tmp_path
):
    """An open unsupported -> summary count, non-zero under --strict only."""
    req_file = tmp_path / "req.yaml"
    req_file.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "module": "a1/test-mod",
                "unsupported": [
                    {"id": "U-001", "claim": "unsupported claim", "searches": [{"tool": "s", "query": "q"}]}
                ],
            }
        ),
        encoding="utf-8",
    )

    src = sources.Sources(sources_db=synthetic_sources, standard_path=synthetic_standard)
    pack.build_pack(
        "a1",
        "test-mod",
        req_file,
        evidence_dir=synthetic_word_store,
        sources_instance=src,
        offline=True,
    )

    # 1. Non-strict: status ok, open count in summary
    res_normal = verify.verify_pack(
        "a1",
        "test-mod",
        evidence_dir=synthetic_word_store,
        sources_instance=src,
        offline=True,
        strict=False,
    )
    assert res_normal["status"] == "ok"
    assert res_normal["unsupported_open_count"] == 1

    # 2. Strict (online mocked): fails non-zero
    with patch(
        "scripts.curriculum.evidence.sources.check_url",
        return_value={"http_status": 200, "final_url": "url", "content_type": "text/html", "date": "2026-09-22"},
    ):
        res_strict = verify.verify_pack(
            "a1",
            "test-mod",
            evidence_dir=synthetic_word_store,
            sources_instance=src,
            offline=False,
            strict=True,
        )
    assert res_strict["status"] == "failed"
    assert any(codes.OPEN_UNSUPPORTED in err for err in res_strict["errors"])


def test_pack_with_words_fails(synthetic_sources, synthetic_standard, synthetic_word_store, tmp_path):
    """A pack with words: -> fails."""
    pack_path = synthetic_word_store / "test-mod.yaml"
    bad_doc = {
        "evidence_schema": 1,
        "module": "a1/test-mod",
        "built_with": {
            "mcp_commit": "a" * 40,
            "sources_db": "b" * 64,
            "vesum": "c" * 64,
            "trie": "d" * 64,
            "ulif_forms": "pending",
            "standard_sha256": "e" * 64,
        },
        "words": [{"id": "W-001", "lemma": "forbidden"}],
    }
    lock.write(pack_path, lock.yaml_bytes(bad_doc))

    src = sources.Sources(sources_db=synthetic_sources, standard_path=synthetic_standard)
    res = verify.verify_pack("a1", "test-mod", evidence_dir=synthetic_word_store, sources_instance=src, offline=True)
    assert res["status"] == "failed"
    assert any(codes.WORDS_FIELD_FORBIDDEN in err for err in res["errors"])


def test_determinism_two_builds_byte_identical(synthetic_sources, synthetic_standard, synthetic_word_store, tmp_path):
    """Determinism: two builds from same request are byte-identical."""
    req_file = tmp_path / "req.yaml"
    req_file.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "module": "a1/test-mod",
                "texts": [
                    {
                        "id": "T-001",
                        "source": {"table": "textbooks", "chunk_id": "chunk-1"},
                        "span": {"first_words": "synthetic-first", "last_words": "synthetic-last"},
                        "supports": "Deterministic check.",
                    }
                ],
                "standard": [{"id": "S-001", "lines": "1-3"}],
            }
        ),
        encoding="utf-8",
    )

    src = sources.Sources(sources_db=synthetic_sources, standard_path=synthetic_standard)
    dir1 = tmp_path / "ev1"
    dir2 = tmp_path / "ev2"

    pack.build_pack("a1", "test-mod", req_file, evidence_dir=dir1, sources_instance=src, offline=True)
    pack.build_pack("a1", "test-mod", req_file, evidence_dir=dir2, sources_instance=src, offline=True)

    bytes1 = (dir1 / "test-mod.yaml").read_bytes()
    bytes2 = (dir2 / "test-mod.yaml").read_bytes()
    assert bytes1 == bytes2
    assert (dir1 / "test-mod.yaml.lock").read_bytes() == (dir2 / "test-mod.yaml.lock").read_bytes()


def test_db_opened_readonly(synthetic_sources):
    """Database opened read-only."""
    conn = sources.open_readonly(synthetic_sources)
    with pytest.raises(sqlite3.OperationalError):
        conn.execute("INSERT INTO style_guide (id, word, text) VALUES (99, 'fail', 'fail')")
    conn.close()


def test_file_modes(synthetic_sources, synthetic_standard, synthetic_word_store, tmp_path):
    """Atomic write sets file modes to 0o644."""
    req_file = tmp_path / "req.yaml"
    req_file.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "module": "a1/test-mod",
                "texts": [
                    {
                        "id": "T-001",
                        "source": {"table": "textbooks", "chunk_id": "chunk-1"},
                        "span": {"first_words": "synthetic-first", "last_words": "synthetic-last"},
                        "supports": "Mode test.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    src = sources.Sources(sources_db=synthetic_sources, standard_path=synthetic_standard)
    res = pack.build_pack(
        "a1",
        "test-mod",
        req_file,
        evidence_dir=synthetic_word_store,
        sources_instance=src,
        offline=True,
    )
    p = Path(res["pack_path"])
    mode = oct(p.stat().st_mode & 0o777)
    assert mode == "0o644"


def _texts_only_request(tmp_path) -> Path:
    req_file = tmp_path / "req.yaml"
    req_file.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "module": "a1/test-mod",
                "texts": [
                    {
                        "id": "T-001",
                        "source": {"table": "textbooks", "chunk_id": "chunk-1"},
                        "span": {"first_words": "synthetic-first", "last_words": "synthetic-last"},
                        "supports": "VESUM identity check.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return req_file


def test_texts_only_build_without_vesum_records_null(
    synthetic_sources, synthetic_standard, synthetic_word_store, tmp_path
):
    """A pack build never opens a missing VESUM file and does not invent its hash."""
    missing_vesum = tmp_path / "absent-vesum.db"
    src = sources.Sources(sources_db=synthetic_sources, vesum_db=missing_vesum, standard_path=synthetic_standard)
    pack.build_pack(
        "a1",
        "test-mod",
        _texts_only_request(tmp_path),
        evidence_dir=synthetic_word_store,
        sources_instance=src,
        offline=True,
    )

    built_with = yaml.safe_load((synthetic_word_store / "test-mod.yaml").read_text(encoding="utf-8"))["built_with"]
    assert built_with["vesum"] is None
    assert "russian_patterns" not in built_with
    assert not missing_vesum.exists()


def test_build_with_vesum_records_its_content_hash(
    synthetic_sources, synthetic_vesum, synthetic_standard, synthetic_word_store, tmp_path
):
    """When the VESUM file exists the pack keeps its real identity hash."""
    src = sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum, standard_path=synthetic_standard)
    pack.build_pack(
        "a1",
        "test-mod",
        _texts_only_request(tmp_path),
        evidence_dir=synthetic_word_store,
        sources_instance=src,
        offline=True,
    )

    built_with = yaml.safe_load((synthetic_word_store / "test-mod.yaml").read_text(encoding="utf-8"))["built_with"]
    expected = sources.Sources(vesum_db=synthetic_vesum)._vesum_identity()[0]
    assert built_with["vesum"] == expected
    assert len(built_with["russian_patterns"]) == 64
