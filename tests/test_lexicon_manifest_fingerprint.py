import json
import os
import subprocess
from pathlib import Path

import pytest

from scripts.lexicon.check_manifest_freshness import check_freshness
from scripts.lexicon.check_manifest_vocabulary_coverage import check_vocabulary_coverage
from scripts.lexicon.manifest_fingerprint import build_fingerprint, sidecar_payload, write_fingerprint

pytestmark = pytest.mark.repo_invariant

REPO_ROOT = Path(__file__).resolve().parents[1]
_GIT_SCOPE_ENV_VARS = ("GIT_COMMON_DIR", "GIT_DIR", "GIT_INDEX_FILE", "GIT_PREFIX", "GIT_WORK_TREE")


def _fixture_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "scripts" / "lexicon").mkdir(parents=True)
    (root / "curriculum" / "l2-uk-en" / "a1" / "hello").mkdir(parents=True)
    (root / "site" / "src" / "data").mkdir(parents=True)
    (root / "scripts" / "lexicon" / "alpha.py").write_text("VALUE = 1\n", encoding="utf-8")
    (root / "scripts" / "lexicon" / "beta.py").write_text("VALUE = 2\n", encoding="utf-8")
    (root / "curriculum" / "l2-uk-en" / "a1" / "hello" / "vocabulary.yaml").write_text(
        "- lemma: привіт\n"
        "  translation: hello\n"
        "- word: дім\n"
        "  translation: house\n",
        encoding="utf-8",
    )
    return root


def _git(root: Path, *args: str) -> None:
    env = os.environ.copy()
    for name in _GIT_SCOPE_ENV_VARS:
        env.pop(name, None)
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )


def _commit_fixture_repo(root: Path) -> None:
    _git(root, "init", "--quiet", "-b", "main")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "Test")
    _git(root, "add", ".")
    _git(root, "commit", "--quiet", "-m", "base")
    _git(root, "branch", "base")


def _write_manifest(root: Path, entries: list[dict]) -> Path:
    manifest = root / "site" / "src" / "data" / "lexicon-manifest.json"
    manifest.write_text(
        json.dumps({"version": "test", "entries": entries}, ensure_ascii=False),
        encoding="utf-8",
    )
    return manifest


def _manifest_entry(lemma: str, *modules: tuple[str, str]) -> dict:
    return {
        "lemma": lemma,
        "course_usage": [
            {"track": track, "module_num": 1, "slug": slug, "context": "built_vocabulary"}
            for track, slug in modules
        ],
    }


def test_manifest_fingerprint_is_stable_across_runs(tmp_path: Path) -> None:
    root = _fixture_repo(tmp_path)

    first = build_fingerprint(root)
    second = build_fingerprint(root)

    assert first == second
    assert first["stats"] == {"lexicon_code_files": 2}
    assert set(first["inputs"]) == {"lexicon_code"}


def test_manifest_fingerprint_changes_when_lexicon_source_byte_changes(tmp_path: Path) -> None:
    root = _fixture_repo(tmp_path)
    before = build_fingerprint(root)["fingerprint"]

    (root / "scripts" / "lexicon" / "alpha.py").write_text("VALUE = 10\n", encoding="utf-8")
    after = build_fingerprint(root)["fingerprint"]

    assert after != before


def test_manifest_fingerprint_excludes_release_asset_loader(tmp_path: Path) -> None:
    root = _fixture_repo(tmp_path)
    (root / "scripts" / "lexicon" / "manifest_io.py").write_text("VALUE = 999\n", encoding="utf-8")

    paths = {item["path"] for item in build_fingerprint(root)["inputs"]["lexicon_code"]}

    assert "scripts/lexicon/manifest_io.py" not in paths


def test_manifest_fingerprint_ignores_vocab_lemma_churn(tmp_path: Path) -> None:
    root = _fixture_repo(tmp_path)
    before = build_fingerprint(root)["fingerprint"]

    vocabulary = root / "curriculum" / "l2-uk-en" / "a1" / "hello" / "vocabulary.yaml"
    vocabulary.write_text(vocabulary.read_text(encoding="utf-8") + "- uk: школа\n", encoding="utf-8")
    after = build_fingerprint(root)["fingerprint"]

    assert after == before


def test_write_fingerprint_is_idempotent(tmp_path: Path) -> None:
    # The PR-tier repo-invariant guard compares the committed sidecar with the
    # real lexicon tree. If write_fingerprint were non-deterministic, that guard
    # would report drift on every run. Guarantee byte-identical output.
    root = _fixture_repo(tmp_path)
    sidecar = root / "site" / "src" / "data" / "lexicon-manifest.fingerprint.json"

    write_fingerprint(sidecar, root=root)
    first = sidecar.read_bytes()
    write_fingerprint(sidecar, root=root)
    second = sidecar.read_bytes()

    assert first == second


def test_sidecar_omits_aggregate_fields_that_cause_concurrent_conflicts(tmp_path: Path) -> None:
    root = _fixture_repo(tmp_path)
    sidecar = root / "site" / "src" / "data" / "lexicon-manifest.fingerprint.json"

    written = write_fingerprint(sidecar, root=root)

    assert json.loads(sidecar.read_text(encoding="utf-8")) == sidecar_payload(written)
    assert "fingerprint" not in json.loads(sidecar.read_text(encoding="utf-8"))
    assert "stats" not in json.loads(sidecar.read_text(encoding="utf-8"))


def test_write_fingerprint_changes_after_lexicon_edit(tmp_path: Path) -> None:
    # Conversely, editing lexicon code MUST change the regenerated sidecar — that
    # is the drift the PR-tier repo-invariant guard is meant to catch.
    root = _fixture_repo(tmp_path)
    sidecar = root / "site" / "src" / "data" / "lexicon-manifest.fingerprint.json"

    write_fingerprint(sidecar, root=root)
    before = sidecar.read_bytes()
    (root / "scripts" / "lexicon" / "alpha.py").write_text("VALUE = 999\n", encoding="utf-8")
    write_fingerprint(sidecar, root=root)
    after = sidecar.read_bytes()

    assert after != before


def test_manifest_freshness_check_passes_on_matching_sidecar(tmp_path: Path, capsys) -> None:
    root = _fixture_repo(tmp_path)
    sidecar = root / "site" / "src" / "data" / "lexicon-manifest.fingerprint.json"
    written = write_fingerprint(sidecar, root=root)

    assert check_freshness(root=root, fingerprint_path=sidecar) == 0
    output = capsys.readouterr().out
    assert json.loads(sidecar.read_text(encoding="utf-8")) == sidecar_payload(written)
    assert "Atlas manifest freshness OK" in output


def test_committed_manifest_fingerprint_matches_real_lexicon_tree(capsys) -> None:
    """The PR tier must catch drift in the committed sidecar itself."""
    assert check_freshness(root=REPO_ROOT) == 0
    assert "Atlas manifest freshness OK" in capsys.readouterr().out


def test_manifest_freshness_check_fails_on_mismatched_sidecar(tmp_path: Path, capsys) -> None:
    root = _fixture_repo(tmp_path)
    sidecar = root / "site" / "src" / "data" / "lexicon-manifest.fingerprint.json"
    write_fingerprint(sidecar, root=root)
    (root / "scripts" / "lexicon" / "beta.py").write_text("VALUE = 200\n", encoding="utf-8")

    assert check_freshness(root=root, fingerprint_path=sidecar) == 2
    output = capsys.readouterr().out
    assert "Atlas manifest stale vs lexicon code" in output
    assert "python -m scripts.lexicon.manifest_fingerprint --write" in output
    assert "make atlas" in output
    assert "dictionary DB/cache version drift is out of scope" in output


def test_manifest_freshness_check_fails_cleanly_on_malformed_sidecar(tmp_path: Path, capsys) -> None:
    root = _fixture_repo(tmp_path)
    sidecar = root / "site" / "src" / "data" / "lexicon-manifest.fingerprint.json"
    sidecar.write_text('{"inputs": [}\n', encoding="utf-8")

    assert check_freshness(root=root, fingerprint_path=sidecar) == 2
    assert "Atlas manifest stale vs lexicon code" in capsys.readouterr().out


def test_manifest_freshness_allows_identical_union_duplicate_record(tmp_path: Path) -> None:
    root = _fixture_repo(tmp_path)
    sidecar = root / "site" / "src" / "data" / "lexicon-manifest.fingerprint.json"
    payload = sidecar_payload(write_fingerprint(sidecar, root=root))
    records = payload["inputs"]["lexicon_code"]
    records.append(dict(records[0]))
    sidecar.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    assert check_freshness(root=root, fingerprint_path=sidecar) == 0


def test_manifest_freshness_rejects_conflicting_union_duplicate_record(tmp_path: Path) -> None:
    root = _fixture_repo(tmp_path)
    sidecar = root / "site" / "src" / "data" / "lexicon-manifest.fingerprint.json"
    payload = sidecar_payload(write_fingerprint(sidecar, root=root))
    records = payload["inputs"]["lexicon_code"]
    records.append({"path": records[0]["path"], "sha256": "not-the-recorded-hash"})
    sidecar.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    assert check_freshness(root=root, fingerprint_path=sidecar) == 2


def test_union_merge_keeps_independent_fingerprint_updates_fresh(tmp_path: Path) -> None:
    """Independent concurrent path records remain fresh after a union-style merge.

    Git's built-in ``merge=union`` is line-oriented and version-sensitive on JSON.
    This test therefore constructs the merge-friendly outcome the sidecar format
    is designed for: both parents' path digests present, with identical
    duplicates collapsed by ``_normalized_sidecar``.
    """
    root = _fixture_repo(tmp_path)
    sidecar = root / "site" / "src" / "data" / "lexicon-manifest.fingerprint.json"
    write_fingerprint(sidecar, root=root)
    (root / ".gitattributes").write_text(
        "site/src/data/lexicon-manifest.fingerprint.json merge=union\n",
        encoding="utf-8",
    )
    _commit_fixture_repo(root)

    _git(root, "checkout", "--quiet", "-b", "left", "base")
    (root / "scripts" / "lexicon" / "gamma.py").write_text("VALUE = 10\n", encoding="utf-8")
    write_fingerprint(sidecar, root=root)
    left_payload = json.loads(sidecar.read_text(encoding="utf-8"))
    _git(root, "add", ".")
    _git(root, "commit", "--quiet", "-m", "left update")

    _git(root, "checkout", "--quiet", "-b", "right", "base")
    (root / "scripts" / "lexicon" / "zeta.py").write_text("VALUE = 20\n", encoding="utf-8")
    write_fingerprint(sidecar, root=root)
    right_payload = json.loads(sidecar.read_text(encoding="utf-8"))
    _git(root, "add", ".")
    _git(root, "commit", "--quiet", "-m", "right update")

    _git(root, "checkout", "--quiet", "left")
    # Reconstruct a merge=union style sidecar: both sides' records, including an
    # intentional identical duplicate of a shared base path (union may keep it).
    left_records = list(left_payload["inputs"]["lexicon_code"])
    right_records = list(right_payload["inputs"]["lexicon_code"])
    shared = next(r for r in left_records if r["path"].endswith("alpha.py"))
    merged = {
        "schema_version": left_payload["schema_version"],
        "scope": left_payload["scope"],
        "inputs": {
            "lexicon_code": left_records + right_records + [dict(shared)],
        },
    }
    sidecar.write_text(json.dumps(merged, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    # Also land both source files so current fingerprint includes gamma+zeta.
    (root / "scripts" / "lexicon" / "zeta.py").write_text("VALUE = 20\n", encoding="utf-8")

    assert check_freshness(root=root, fingerprint_path=sidecar) == 0

def test_manifest_vocabulary_coverage_fails_when_new_vocab_lemma_missing(
    tmp_path: Path,
    capsys,
) -> None:
    root = _fixture_repo(tmp_path)
    vocabulary = root / "curriculum" / "l2-uk-en" / "a1" / "hello" / "vocabulary.yaml"
    vocabulary.write_text(
        vocabulary.read_text(encoding="utf-8")
        + "- lemma: новеслово\n"
        "  translation: fake new word\n",
        encoding="utf-8",
    )
    manifest = _write_manifest(
        root,
        [
            _manifest_entry("привіт", ("a1", "hello")),
            _manifest_entry("дім", ("a1", "hello")),
        ],
    )

    assert check_vocabulary_coverage(root=root, manifest_path=manifest) == 2
    output = capsys.readouterr().out
    assert "Atlas manifest stale vs module vocabulary" in output
    assert "run `make atlas` locally and commit" in output
    assert "новеслово" in output


def test_manifest_vocabulary_coverage_passes_when_vocab_lemma_present(
    tmp_path: Path,
    capsys,
) -> None:
    root = _fixture_repo(tmp_path)
    vocabulary = root / "curriculum" / "l2-uk-en" / "a1" / "hello" / "vocabulary.yaml"
    vocabulary.write_text(
        vocabulary.read_text(encoding="utf-8")
        + "- lemma: новеслово\n"
        "  translation: fake new word\n",
        encoding="utf-8",
    )
    manifest = _write_manifest(
        root,
        [
            _manifest_entry("привіт", ("a1", "hello")),
            _manifest_entry("дім", ("a1", "hello")),
            _manifest_entry("новеслово", ("a1", "hello")),
        ],
    )

    assert check_vocabulary_coverage(root=root, manifest_path=manifest) == 0
    output = capsys.readouterr().out
    assert "Atlas vocabulary coverage OK" in output


def test_manifest_vocabulary_coverage_fails_when_module_usage_missing(
    tmp_path: Path,
    capsys,
) -> None:
    root = _fixture_repo(tmp_path)
    other = root / "curriculum" / "l2-uk-en" / "a1" / "second"
    other.mkdir()
    (other / "vocabulary.yaml").write_text(
        "- lemma: привіт\n"
        "  translation: hello again\n",
        encoding="utf-8",
    )
    manifest = _write_manifest(
        root,
        [
            _manifest_entry("привіт", ("a1", "hello")),
            _manifest_entry("дім", ("a1", "hello")),
        ],
    )

    assert check_vocabulary_coverage(root=root, manifest_path=manifest) == 2
    output = capsys.readouterr().out
    assert "missing course_usage links" in output
    assert "привіт: a1/second" in output
