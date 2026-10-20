"""Transform registry and content-addressed digests (design r3 §6.1)."""

from __future__ import annotations

import shutil
from dataclasses import replace
from pathlib import Path

import pytest

from scripts.lexdata import rights, transforms
from tests.lexdata._support import FIXTURE_SOURCE, fixture_binding

REPO = transforms.REPO_ROOT


def _shadow_repo(tmp_path: Path, binding: transforms.TransformBinding) -> Path:
    """Copy every file a digest reads into a scratch root that can be edited."""
    root = tmp_path / "shadow"
    manifest = transforms.transform_manifest(FIXTURE_SOURCE, binding)
    paths = {entry["path"] for component in manifest.values() if isinstance(component, dict)
             for key in ("modules", "data_files") for entry in component.get(key, ())}
    paths |= {rights.OWNED_RIGHTS, rights.PERMISSIONS_REGISTER}
    for rel in paths:
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / rel, root / rel)
    return root


def test_transform_registry_covers_project_imports() -> None:
    assert transforms.undeclared_imports() == {}
    assert transforms.undeclared_imports(fixture_binding()) == {}
    shared = transforms._manifest_modules(transforms._shared_components(transforms.DEFAULT_BINDING))
    # Every module that shapes an L1 field is registered; orchestration modules
    # (build_store, verify, generation, l2_stage, cli, transforms) are not transforms.
    assert shared == {f"scripts/lexdata/{name}.py" for name in (
        "normalize", "case_signal", "stress", "rule_tables", "schema", "records", "derive", "canonical", "rights")}


def test_undeclared_import_is_detected(tmp_path) -> None:
    root = _shadow_repo(tmp_path, fixture_binding())
    parser = root / "tests" / "lexdata" / "fixture_parser.py"
    (root / "scripts" / "lexdata" / "sneaky.py").write_text("VALUE = 1\n", encoding="utf-8")
    parser.write_text(parser.read_text(encoding="utf-8") + "\nfrom scripts.lexdata import sneaky  # noqa\n",
                      encoding="utf-8")
    binding = replace(fixture_binding(), repo_root=root)
    problems = transforms.undeclared_imports(binding)
    assert problems == {FIXTURE_SOURCE: ["tests/lexdata/fixture_parser.py imports scripts/lexdata/sneaky.py"]}
    with pytest.raises(transforms.TransformRegistryError):
        transforms.assert_registry_closed(binding)


@pytest.mark.parametrize("rel", [
    "scripts/lexdata/normalize.py", "scripts/lexdata/case_signal.py", "scripts/lexdata/stress.py",
    "scripts/lexdata/rule_tables.py", "scripts/lexdata/schema.py", "scripts/lexdata/records.py",
    "scripts/lexdata/derive.py", "scripts/lexdata/normalization_vectors.json",
    "tests/lexdata/fixture_parser.py", rights.OWNED_RIGHTS,
])
def test_any_byte_change_changes_the_digest_without_a_version_bump(tmp_path, rel) -> None:
    root = _shadow_repo(tmp_path, fixture_binding())
    binding = replace(fixture_binding(), repo_root=root)
    before = transforms.transform_digest(FIXTURE_SOURCE, binding)
    path = root / rel
    path.write_bytes(path.read_bytes() + b"\n")
    assert transforms.transform_digest(FIXTURE_SOURCE, binding) != before


def test_normalizer_digest_tracks_only_query_key_components(tmp_path) -> None:
    root = _shadow_repo(tmp_path, fixture_binding())
    binding = replace(fixture_binding(), repo_root=root)
    before = transforms.normalizer_digest(binding)
    (root / "scripts/lexdata/schema.py").write_text("# changed\n", encoding="utf-8")
    assert transforms.normalizer_digest(binding) == before
    (root / "scripts/lexdata/case_signal.py").write_text("# changed\n", encoding="utf-8")
    assert transforms.normalizer_digest(binding) != before


def test_rights_register_rows_enter_the_digest(tmp_path) -> None:
    base = fixture_binding()
    spec = replace(base.sources[FIXTURE_SOURCE], rights_register_ids=("ulp_private",))
    binding = replace(base, sources={FIXTURE_SOURCE: spec})
    manifest = transforms.transform_manifest(FIXTURE_SOURCE, binding)
    assert manifest["rights"]["contents_sha256"] != transforms.transform_manifest(
        FIXTURE_SOURCE, base)["rights"]["contents_sha256"]
    missing = replace(base, sources={FIXTURE_SOURCE: replace(spec, rights_register_ids=("no_such_row",))})
    with pytest.raises(rights.RightsInputError, match="no row"):
        transforms.transform_digest(FIXTURE_SOURCE, missing)


def test_unregistered_ids_fail_closed() -> None:
    with pytest.raises(transforms.TransformRegistryError, match="not registered"):
        transforms.transform_digest("nope")
    base = fixture_binding()
    bad = replace(base, sources={FIXTURE_SOURCE: replace(base.sources[FIXTURE_SOURCE], list_grammar="puls")})
    with pytest.raises(transforms.TransformRegistryError, match="list grammar"):
        transforms.transform_digest(FIXTURE_SOURCE, bad)
