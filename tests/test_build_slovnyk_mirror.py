"""Tests for the build-time slovnyk.me cache mirror (#3097, #6524)."""

import fcntl
import json
import os
import signal
import subprocess
import sys
from pathlib import Path

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
    monkeypatch.chdir(tmp_path)
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
    # Newly observed misses carry durable identity-bound proof; skip them all.
    assert build_slovnyk_mirror.main(["--manifest", str(manifest)]) == 0
    assert len(calls) == 5
    assert "reused=4" in capsys.readouterr().out


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


def test_mirror_unpublished_success_stops_without_false_completion(mirror_fixture, monkeypatch, capsys):
    manifest, _calls, _queue = mirror_fixture
    calls = []

    def unpublished(lemma, *, outcomes, slugs):
        calls.append(lemma)
        outcomes[slugs[0]] = enrich_manifest_module._SlovnykOutcome("positive", http_status=200)
        return {"lookups": {}}

    monkeypatch.setattr(build_slovnyk_mirror, "_slovnyk_cache", unpublished)
    assert build_slovnyk_mirror.main(["--manifest", str(manifest)]) == 1
    output = capsys.readouterr().out
    assert calls == ["sample"] and "status=incomplete verified_complete=0/2" in output
    assert "fetched=0 reused=0 misses=0 errors=1 pending=3" in output


@pytest.mark.parametrize("collision", ["log-manifest", "log-checkpoint", "checkpoint-manifest", "checkpoint-lock"])
def test_output_collisions_refuse_before_changing_input(mirror_fixture, collision):
    manifest, calls, _queue = mirror_fixture
    before = manifest.read_bytes()
    checkpoint = manifest.parent / "state.json"
    args = ["--manifest", str(manifest), "--checkpoint", str(checkpoint)]
    if collision == "log-manifest":
        args += ["--log-file", str(manifest)]
    elif collision == "log-checkpoint":
        args += ["--log-file", str(checkpoint)]
    elif collision == "checkpoint-manifest":
        args += ["--checkpoint", str(manifest)]
    else:
        args += ["--checkpoint", str(enrich_manifest_module.SLOVNYK_CACHE / ".mirror.lock")]
    with pytest.raises(SystemExit) as exit_code:
        build_slovnyk_mirror.main(args)
    assert exit_code.value.code == 2 and manifest.read_bytes() == before and not calls


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
    replace = enrich_manifest_module.os.replace

    def fail_cache(source, destination):
        if destination.name == ".mirror-checkpoint.json":
            return replace(source, destination)
        raise OSError("private")

    monkeypatch.setattr(enrich_manifest_module.os, "replace", fail_cache)
    assert build_slovnyk_mirror.main(["--manifest", str(manifest)]) == 1
    assert "fetched=0 reused=0 misses=0 errors=1 pending=3" in capsys.readouterr().out
    assert len(calls) == 1


def test_resume_adopts_complete_cache_without_checkpoint(mirror_fixture, capsys):
    manifest, calls, queue = mirror_fixture
    queue(200, 404, 200, 404)
    assert build_slovnyk_mirror.main(["--manifest", str(manifest)]) == 0
    checkpoint = enrich_manifest_module.SLOVNYK_CACHE / ".mirror-checkpoint.json"
    checkpoint.unlink()
    assert build_slovnyk_mirror.main(["--manifest", str(manifest)]) == 0
    assert len(calls) == 4
    assert len(json.loads(checkpoint.read_text())["completed"]) == 2
    assert "verified_complete=2/2 attempted=0" in capsys.readouterr().out


@pytest.mark.parametrize("change", ["missing", "corrupt", "schema", "identity", "row", "manifest", "slugs"])
def test_resume_revalidates_changed_inputs_and_cache(mirror_fixture, monkeypatch, capsys, change):
    manifest, calls, queue = mirror_fixture
    queue(200, 200, 200, 200)
    assert build_slovnyk_mirror.main(["--manifest", str(manifest)]) == 0
    path = enrich_manifest_module._slovnyk_cache_path("sample")
    if change == "missing":
        path.unlink()
    elif change == "corrupt":
        path.write_text("{")
    elif change == "manifest":
        manifest.write_text(json.dumps({"entries": [{"lemma": "sample"}, {"lemma": "new"}, {"lemma": "sample"}]}))
    elif change == "slugs":
        monkeypatch.setattr(build_slovnyk_mirror, "_SLOVNYK_LOOKUP_SLUGS", ("vts", "newsum", "synonyms"))
    else:
        data = json.loads(path.read_text())
        if change == "schema":
            data["schema_version"] = 2
        elif change == "identity":
            data["lemma"] = "other"
        else:
            data["lookups"]["vts"]["text"] = ""
        path.write_text(json.dumps(data))
    expected = 1 if change == "row" else 2
    queue(*([200] * expected))
    assert build_slovnyk_mirror.main(["--manifest", str(manifest)]) == 0
    assert len(calls) == 4 + expected
    assert "checkpoint=" in capsys.readouterr().out


def test_partial_transient_only_retries_missing_slug(mirror_fixture, capsys):
    manifest, calls, queue = mirror_fixture
    queue(200, 503, 200, 200)
    assert build_slovnyk_mirror.main(["--manifest", str(manifest)]) == 1
    output = capsys.readouterr().out
    assert "status=incomplete verified_complete=1/2" in output
    assert "partial=1" in output and "errors=1" in output
    checkpoint = enrich_manifest_module.SLOVNYK_CACHE / ".mirror-checkpoint.json"
    assert set(json.loads(checkpoint.read_text())["completed"]) == {"later"}
    queue(200)
    assert build_slovnyk_mirror.main(["--manifest", str(manifest)]) == 0
    assert len(calls) == 5 and calls[-1].endswith("/newsum/sample")


@pytest.mark.parametrize("when", ["before-data", "after-data", "checkpoint"])
def test_interrupted_run_is_truthful_and_resumable(mirror_fixture, monkeypatch, capsys, when):
    manifest, calls, queue = mirror_fixture
    queue(200, 200, 200, 200)
    original_cache = build_slovnyk_mirror._slovnyk_cache
    original_atomic = build_slovnyk_mirror._atomic_slovnyk_json
    writes = 0

    def interrupt_cache(*args, **kwargs):
        if when == "after-data":
            original_cache(*args, **kwargs)
        raise KeyboardInterrupt

    def interrupt_checkpoint(path, value):
        nonlocal writes
        writes += 1
        if writes == 2:
            raise KeyboardInterrupt
        return original_atomic(path, value)

    with monkeypatch.context() as patch:
        if when == "checkpoint":
            patch.setattr(build_slovnyk_mirror, "_atomic_slovnyk_json", interrupt_checkpoint)
        else:
            patch.setattr(build_slovnyk_mirror, "_slovnyk_cache", interrupt_cache)
        assert build_slovnyk_mirror.main(["--manifest", str(manifest), "--progress-every", "1"]) == 130
    assert "status=interrupted" in capsys.readouterr().out
    queue(200, 200, 200, 200)
    assert build_slovnyk_mirror.main(["--manifest", str(manifest)]) == 0
    assert len(calls) == 4


@pytest.mark.parametrize("state", ["{", "[]", '{"version":2,"completed":{}}'])
def test_corrupt_checkpoint_refuses_without_mutation(mirror_fixture, capsys, state):
    manifest, calls, _queue = mirror_fixture
    checkpoint = enrich_manifest_module.SLOVNYK_CACHE / ".mirror-checkpoint.json"
    checkpoint.parent.mkdir(parents=True)
    checkpoint.write_text(state)
    assert build_slovnyk_mirror.main(["--manifest", str(manifest)]) == 1
    assert checkpoint.read_text() == state and not calls
    assert "status=error" in capsys.readouterr().out


def test_checkpoint_publication_failure_keeps_previous_state(mirror_fixture, monkeypatch, capsys):
    manifest, calls, queue = mirror_fixture
    queue(200, 200, 200, 200)
    original = build_slovnyk_mirror._atomic_slovnyk_json
    writes = 0
    previous = None

    def fail_checkpoint(path, value):
        nonlocal writes, previous
        writes += 1
        if writes == 1:
            original(path, value)
            previous = path.read_bytes()
            return
        raise OSError("private")

    with monkeypatch.context() as patch:
        patch.setattr(build_slovnyk_mirror, "_atomic_slovnyk_json", fail_checkpoint)
        assert build_slovnyk_mirror.main(["--manifest", str(manifest)]) == 1
    checkpoint = enrich_manifest_module.SLOVNYK_CACHE / ".mirror-checkpoint.json"
    assert checkpoint.read_bytes() == previous
    assert "status=error" in capsys.readouterr().out
    assert build_slovnyk_mirror.main(["--manifest", str(manifest)]) == 0
    assert len(calls) == 4


@pytest.mark.parametrize(
    "entries,limit,status,code", [([], None, "complete", 0), ([{"lemma": "sample"}], 0, "limited", 1)]
)
def test_empty_and_zero_limit_stdout_matches_default_log(mirror_fixture, capsys, entries, limit, status, code):
    manifest, calls, _queue = mirror_fixture
    manifest.write_text(json.dumps({"entries": entries}))
    argv = ["--manifest", str(manifest)] + ([] if limit is None else ["--limit", str(limit)])
    assert build_slovnyk_mirror.main(argv) == code
    output = capsys.readouterr().out
    assert f"status={status}" in output and "phase=startup [0/" in output and "ETA=" in output
    logs = list(Path("batch_state/slovnyk-mirror").glob("*.log"))
    assert len(logs) == 1 and logs[0].read_text() == output and not calls


@pytest.mark.parametrize("entries", [[{"lemma": []}], [{"lemma": " "}], "invalid"])
def test_invalid_manifest_stops_without_fetch(mirror_fixture, entries):
    manifest, calls, _queue = mirror_fixture
    manifest.write_text(json.dumps({"entries": entries}))
    assert build_slovnyk_mirror.main(["--manifest", str(manifest)]) == 1
    assert not calls


def test_actual_cli_single_writer_and_sigterm(mirror_fixture):
    manifest, _calls, _queue = mirror_fixture
    repo = Path(build_slovnyk_mirror.__file__).resolve().parents[2]
    cache = enrich_manifest_module.SLOVNYK_CACHE
    env = os.environ | {"LEXICON_SLOVNYK_CACHE": str(cache), "LEXICON_SLOVNYK_OFFLINE": "1"}
    argv = ["--manifest", str(manifest), "--log-file", str(manifest.parent / "cli.log")]
    script = (
        "import time, sys; from scripts.lexicon import build_slovnyk_mirror as m; "
        "m._cache_state = lambda lemma: (time.sleep(30), None); "
        "sys.exit(m.main(sys.argv[1:]))"
    )
    with subprocess.Popen(
        [sys.executable, "-u", "-c", script, *argv], cwd=repo, env=env, stdout=subprocess.PIPE, text=True
    ) as process:
        try:
            assert "validation=starting" in process.stdout.readline()
            second = subprocess.run(
                [sys.executable, "-m", "scripts.lexicon.build_slovnyk_mirror", *argv],
                cwd=repo,
                env=env,
                capture_output=True,
                text=True,
                timeout=15,
            )
            assert second.returncode == 1 and "reason=active-writer" in second.stdout
            process.send_signal(signal.SIGTERM)
            output, _ = process.communicate(timeout=15)
            assert process.returncode == 130 and "status=interrupted" in output
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=15)


def test_same_checkpoint_writer_refused_with_different_cache(mirror_fixture, capsys):
    manifest, calls, _queue = mirror_fixture
    checkpoint = manifest.parent / "shared-state.json"
    lock_path = checkpoint.with_suffix(".json.lock")
    with lock_path.open("a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert build_slovnyk_mirror.main(["--manifest", str(manifest), "--checkpoint", str(checkpoint)]) == 1
    assert "reason=active-writer" in capsys.readouterr().out and not calls and not checkpoint.exists()


def test_sigterm_restores_handler_and_keeps_checkpoint_retryable(mirror_fixture, monkeypatch, capsys):
    manifest, calls, _queue = mirror_fixture
    previous_handler = signal.getsignal(signal.SIGTERM)

    def interrupted(*_args, **_kwargs):
        signal.raise_signal(signal.SIGTERM)

    monkeypatch.setattr(build_slovnyk_mirror, "_slovnyk_cache", interrupted)
    assert build_slovnyk_mirror.main(["--manifest", str(manifest)]) == 130
    assert signal.getsignal(signal.SIGTERM) == previous_handler
    checkpoint = enrich_manifest_module.SLOVNYK_CACHE / ".mirror-checkpoint.json"
    assert json.loads(checkpoint.read_text())["completed"] == {} and not calls
    assert "status=interrupted verified_complete=0/2" in capsys.readouterr().out


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
