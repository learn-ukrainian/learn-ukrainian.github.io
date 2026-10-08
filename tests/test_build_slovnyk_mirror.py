"""Tests for the build-time slovnyk.me cache mirror (#3097, #6524)."""

import json

import pytest

from scripts.lexicon import build_slovnyk_mirror
from scripts.lexicon import enrich_manifest as enrich_manifest_module


def _write_cache(cache_path, schema_version: int) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps(
            {
                "schema_version": schema_version,
                "lemma": "книга",
                "lookup_word": "книга",
                "fetched_at": "2026-01-01T00:00:00+00:00",
                "lookups": {
                    "orthoepy": {
                        "dictionary_slug": "orthoepy",
                        "word": "книга",
                        "text": "кн и га [кн и га] -гие",
                        "source_url": "https://slovnyk.me/dict/orthoepy/%D0%BA%D0%BD%D0%B8%D0%B3%D0%B0",
                    }
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_is_fully_cached_rejects_stale_schema_version(monkeypatch, tmp_path) -> None:
    """#6524 P2 (codex re-verdict): a "complete" v2 row -- every lookup slug present --
    must NOT read as already-cached. v2 predates the #6465 corrupted-join fix, so it can
    still carry corrupted ``text``. Before this gate, ``main()`` dropped such a row from
    ``todo`` and it was skipped forever, never healed by a real ``_slovnyk_cache()`` run
    even though the concurrent pre-fix job kept rewriting it."""
    monkeypatch.setattr(enrich_manifest_module, "SLOVNYK_CACHE", tmp_path)
    monkeypatch.setattr(build_slovnyk_mirror, "_SLOVNYK_LOOKUP_SLUGS", ("orthoepy",))
    _write_cache(enrich_manifest_module._slovnyk_cache_path("книга"), schema_version=2)

    assert build_slovnyk_mirror._is_fully_cached("книга") is False


def test_is_fully_cached_accepts_current_schema_version(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(enrich_manifest_module, "SLOVNYK_CACHE", tmp_path)
    monkeypatch.setattr(build_slovnyk_mirror, "_SLOVNYK_LOOKUP_SLUGS", ("orthoepy",))
    _write_cache(
        enrich_manifest_module._slovnyk_cache_path("книга"),
        schema_version=enrich_manifest_module._SLOVNYK_CACHE_SCHEMA_VERSION,
    )

    assert build_slovnyk_mirror._is_fully_cached("книга") is True


@pytest.fixture
def mirror_fixture(tmp_path, monkeypatch):
    from types import SimpleNamespace

    monkeypatch.delenv("LEXICON_SLOVNYK_OFFLINE", raising=False)
    monkeypatch.setattr(enrich_manifest_module, "SLOVNYK_CACHE", tmp_path / "cache")
    monkeypatch.setattr(enrich_manifest_module, "_SLOVNYK_MAX_RETRIES", 0)
    monkeypatch.setattr(enrich_manifest_module, "_polite_slovnyk_delay", lambda: None)
    monkeypatch.setattr(build_slovnyk_mirror, "_SLOVNYK_LOOKUP_SLUGS", ("vts", "newsum"))
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"entries": [{"lemma": "sample"}, {"lemma": "later"}]}))
    calls = []

    def queue(*codes):
        responses = iter(codes)

        def get(url, **kwargs):
            calls.append(url)
            code = next(responses)
            return SimpleNamespace(
                status_code=code,
                headers={},
                text=(
                    '<section id="dictionary-article"><article><p>synthetic article</p></article></section>'
                    if code == 200
                    else ""
                ),
            )

        monkeypatch.setattr(enrich_manifest_module.requests, "get", get)

    return manifest, calls, queue


@pytest.mark.parametrize("terminal", [401, 403, 201, 302])
def test_mirror_stop_preserves_partial_counts_and_cache(mirror_fixture, capsys, terminal):
    manifest, calls, queue = mirror_fixture
    queue(200, terminal)
    assert build_slovnyk_mirror.main(["--manifest", str(manifest)]) == 1
    assert len(calls) == 2
    output = capsys.readouterr().out
    assert "fetched=1 reused=0 misses=0 errors=1 pending=2 denominator=4" in output
    assert f"STOP blocked HTTP={terminal}" in output
    cache = json.loads(enrich_manifest_module._slovnyk_cache_path("sample").read_text())
    assert set(cache["lookups"]) == {"vts"}
    queue(404, 404, 404)
    assert build_slovnyk_mirror.main(["--manifest", str(manifest)]) == 0
    assert "fetched=0 reused=1 misses=3 errors=0 pending=0" in capsys.readouterr().out
    # Legacy null has no HTTP proof on the next invocation; fetch it again.
    queue(404, 404, 404)
    assert build_slovnyk_mirror.main(["--manifest", str(manifest)]) == 0
    assert len(calls) == 8


def test_mirror_parse_stop_and_default_tolerant_caller(mirror_fixture, monkeypatch, capsys):
    manifest, calls, queue = mirror_fixture
    queue(200)
    monkeypatch.setattr(enrich_manifest_module, "_parse_slovnyk_entry", lambda *_args, **_kwargs: None)
    assert build_slovnyk_mirror.main(["--manifest", str(manifest)]) == 1
    assert len(calls) == 1
    assert "fetched=0 reused=0 misses=0 errors=1 pending=3" in capsys.readouterr().out
    queue(403, 200)
    monkeypatch.setattr(enrich_manifest_module, "_SLOVNYK_LOOKUP_SLUGS", ("vts", "newsum"))
    assert enrich_manifest_module._slovnyk_cache("sample")["lookups"] == {"newsum": None}


@pytest.mark.parametrize("mode", ["offline", "empty", "limit"])
def test_mirror_unrequested_work_is_pending(mirror_fixture, monkeypatch, capsys, mode):
    manifest, calls, queue = mirror_fixture
    if mode == "offline":
        monkeypatch.setenv("LEXICON_SLOVNYK_OFFLINE", "1")
    elif mode == "empty":
        monkeypatch.setattr(enrich_manifest_module, "_slovnyk_lookup_word", lambda _lemma: "")
    else:
        queue(404, 404)
    argv = ["--manifest", str(manifest)] + (["--limit", "1"] if mode == "limit" else [])
    assert build_slovnyk_mirror.main(argv) == 1
    output = capsys.readouterr().out
    assert ("misses=2 errors=0 pending=2" if mode == "limit" else "misses=0 errors=0 pending=4") in output
    assert len(calls) == (2 if mode == "limit" else 0)


def test_mirror_empty_result_cannot_count_as_fetched(mirror_fixture, monkeypatch, capsys):
    manifest, calls, _queue = mirror_fixture
    monkeypatch.setattr(build_slovnyk_mirror, "_slovnyk_cache", lambda *_args, **_kwargs: {})
    assert build_slovnyk_mirror.main(["--manifest", str(manifest)]) == 1
    assert "fetched=0 reused=0 misses=0 errors=0 pending=4" in capsys.readouterr().out
    assert not calls


def test_mirror_validated_full_positive_reuse(mirror_fixture, capsys):
    manifest, calls, queue = mirror_fixture
    queue(200, 200, 200, 200)
    assert build_slovnyk_mirror.main(["--manifest", str(manifest)]) == 0
    assert build_slovnyk_mirror._is_fully_cached("sample")
    assert build_slovnyk_mirror.main(["--manifest", str(manifest)]) == 0
    assert len(calls) == 4
    assert "fetched=0 reused=4 misses=0 errors=0 pending=0" in capsys.readouterr().out


def test_mirror_storage_failure_is_error(mirror_fixture, monkeypatch, capsys):
    manifest, calls, queue = mirror_fixture
    queue(200)
    monkeypatch.setattr(enrich_manifest_module.os, "replace", lambda *_args: (_ for _ in ()).throw(OSError("private")))
    assert build_slovnyk_mirror.main(["--manifest", str(manifest)]) == 1
    assert "fetched=0 reused=0 misses=0 errors=1 pending=3" in capsys.readouterr().out
    assert len(calls) == 1


def test_mirror_help_usage_and_manifest_failure(mirror_fixture, capsys):
    manifest, _calls, _queue = mirror_fixture
    with pytest.raises(SystemExit) as help_exit:
        build_slovnyk_mirror.main(["--help"])
    assert help_exit.value.code == 0
    assert "Exit codes: 0" in capsys.readouterr().out
    with pytest.raises(SystemExit) as invalid_exit:
        build_slovnyk_mirror.main(["--progress-every", "0"])
    assert invalid_exit.value.code == 2
    manifest.write_text("{")
    assert build_slovnyk_mirror.main(["--manifest", str(manifest)]) == 1
