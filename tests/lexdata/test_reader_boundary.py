"""Reader compatibility and malformed metadata (design r3 §6.3, §6.5, §7.1)."""

from __future__ import annotations

from contextlib import closing
from dataclasses import replace

import pytest

from scripts.lexdata import build_store, generation, transforms, verify
from scripts.lib.readonly_sqlite import open_readonly
from tests.lexdata._support import FIXTURE_SOURCE, fixture_binding, mutate_sqlite

pytestmark = pytest.mark.usefixtures("local_fs")


def _with_parser_version(binding: transforms.TransformBinding, version: str) -> transforms.TransformBinding:
    parser_id = next(iter(binding.parsers))
    return replace(binding, parsers={parser_id: replace(binding.parsers[parser_id], version=version)})


def test_changed_parser_digest_is_stale_without_any_caller_argument(harness) -> None:
    """The reviewer's shape: only the parser changed, and the caller passes no expected digests."""
    built = fixture_binding()
    result = harness.build(binding=built)
    changed = _with_parser_version(built, "changed")
    assert transforms.normalizer_digest(changed) == transforms.normalizer_digest(built)
    assert transforms.transform_digest(FIXTURE_SOURCE, changed) != transforms.transform_digest(FIXTURE_SOURCE, built)
    view = generation.open_generation(result.published, binding=changed, repository_root=harness.repository_root)
    assert view == generation.Unavailable("lexdata_stale", result.generation)
    same = generation.open_generation(result.published, binding=built, repository_root=harness.repository_root)
    assert isinstance(same, generation.OpenGeneration)
    same.close()


def test_registered_source_set_must_match_the_generation(harness) -> None:
    result = harness.build()
    # The production registry (no fixture source) is stale against a fixture generation ...
    assert generation.open_generation(result.published).reason == "lexdata_stale"
    # ... and so is a registry that has a source the generation was not built with.
    extra = fixture_binding()
    extra = replace(extra, sources={**extra.sources,
                                    "fixture_extra": replace(extra.sources[FIXTURE_SOURCE], source_id="fixture_extra")})
    assert generation.open_generation(result.published, binding=extra).reason == "lexdata_stale"


def test_changed_generation_schema_version_is_stale(harness) -> None:
    result = harness.build()
    mutate_sqlite(result.published, "UPDATE meta SET generation_schema_version = 'old'")
    assert generation.open_generation(result.published, binding=fixture_binding()).reason == "lexdata_stale"


def test_status_cli_uses_the_current_registry(harness, capsys, monkeypatch) -> None:
    import json

    from scripts.lexdata import cli

    result = harness.build()
    monkeypatch.setenv("LU_LEXDATA_DB", str(result.published))
    assert cli.main(["status"]) == 2
    assert json.loads(capsys.readouterr().out) == {
        "generation": result.generation, "reason": "lexdata_stale", "status": "unavailable"}


@pytest.mark.parametrize("value", ["not-json", "[]", "null"])
def test_malformed_meta_is_unavailable_and_closes_the_connection(harness, monkeypatch, value) -> None:
    result = harness.build()
    mutate_sqlite(result.published, "UPDATE meta SET transform_manifest = ?", (value,))
    handles = []

    def tracking_open(path):
        conn = open_readonly(path)
        handles.append(conn)
        return conn

    monkeypatch.setattr(generation, "open_readonly", tracking_open)
    view = generation.open_generation(result.published, binding=fixture_binding())
    assert view == generation.Unavailable("lexdata_unavailable")
    with pytest.raises(Exception, match="closed"):
        handles[0].execute("SELECT 1")


def test_reader_closes_its_connection_when_a_check_raises(harness, monkeypatch) -> None:
    result = harness.build()
    handles = []

    def tracking_open(path):
        conn = open_readonly(path)
        handles.append(conn)
        return conn

    def boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(generation, "open_readonly", tracking_open)
    monkeypatch.setattr(generation, "check_meta", boom)
    with pytest.raises(RuntimeError, match="boom"):
        generation.open_generation(result.published, binding=fixture_binding())
    with pytest.raises(Exception, match="closed"):
        handles[0].execute("SELECT 1")


def test_malformed_meta_is_a_verify_violation_and_blocks_the_next_build(harness) -> None:
    result = harness.build()
    mutate_sqlite(result.published, "UPDATE meta SET diff_receipt = 'not-json'")
    with closing(open_readonly(result.published)) as conn:
        report = verify.verify_generation(conn, binding=fixture_binding())
    assert report.violations["meta_malformed"] == 1 and not report.ok
    with pytest.raises(build_store.BuildRefused, match="published_meta_malformed"):
        harness.build()
