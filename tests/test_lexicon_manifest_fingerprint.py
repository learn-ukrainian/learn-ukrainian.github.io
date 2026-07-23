import json
import os
import subprocess
from pathlib import Path

from scripts.lexicon.check_manifest_freshness import (
    GIT_SCOPE_ENV_VARS,
    check_freshness,
    pr_touches_manifest_scope,
)
from scripts.lexicon.check_manifest_vocabulary_coverage import check_vocabulary_coverage
from scripts.lexicon.manifest_fingerprint import build_fingerprint, write_fingerprint


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
    for name in GIT_SCOPE_ENV_VARS:
        env.pop(name, None)
    subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        env=env,
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
    # The pre-commit hook regenerates the sidecar then `git diff --exit-code`s it.
    # If write_fingerprint were non-deterministic, that gate would block every
    # commit. Guarantee re-running on unchanged code yields byte-identical output.
    root = _fixture_repo(tmp_path)
    sidecar = root / "site" / "src" / "data" / "lexicon-manifest.fingerprint.json"

    write_fingerprint(sidecar, root=root)
    first = sidecar.read_bytes()
    write_fingerprint(sidecar, root=root)
    second = sidecar.read_bytes()

    assert first == second


def test_write_fingerprint_changes_after_lexicon_edit(tmp_path: Path) -> None:
    # Conversely, editing lexicon code MUST change the regenerated sidecar — that
    # is the drift the pre-commit `git diff --exit-code` is meant to catch.
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
    assert json.loads(sidecar.read_text(encoding="utf-8"))["fingerprint"] == written["fingerprint"]
    assert "Atlas manifest freshness OK" in output


def test_manifest_freshness_check_fails_on_mismatched_sidecar(tmp_path: Path, capsys) -> None:
    root = _fixture_repo(tmp_path)
    sidecar = root / "site" / "src" / "data" / "lexicon-manifest.fingerprint.json"
    write_fingerprint(sidecar, root=root)
    (root / "scripts" / "lexicon" / "beta.py").write_text("VALUE = 200\n", encoding="utf-8")

    assert check_freshness(root=root, fingerprint_path=sidecar) == 2
    output = capsys.readouterr().out
    assert "Atlas manifest stale vs lexicon code" in output
    assert "dictionary DB/cache version drift is out of scope" in output


def test_pr_scoped_freshness_allows_unrelated_drift(tmp_path: Path, capsys) -> None:
    root = _fixture_repo(tmp_path)
    sidecar = root / "site" / "src" / "data" / "lexicon-manifest.fingerprint.json"
    write_fingerprint(sidecar, root=root)
    _commit_fixture_repo(root)
    (root / "README.md").write_text("unrelated PR change\n", encoding="utf-8")
    _git(root, "add", "README.md")
    _git(root, "commit", "--quiet", "-m", "docs change")
    (root / "scripts" / "lexicon" / "beta.py").write_text("VALUE = 200\n", encoding="utf-8")

    assert pr_touches_manifest_scope(root=root, base_ref="base") is False
    assert check_freshness(
        root=root,
        fingerprint_path=sidecar,
        pr_scoped=True,
        base_ref="base",
    ) == 0
    assert "allowing unrelated drift" in capsys.readouterr().out


def test_pr_scoped_freshness_fails_when_pr_changes_lexicon(tmp_path: Path, capsys) -> None:
    root = _fixture_repo(tmp_path)
    sidecar = root / "site" / "src" / "data" / "lexicon-manifest.fingerprint.json"
    write_fingerprint(sidecar, root=root)
    _commit_fixture_repo(root)
    (root / "scripts" / "lexicon" / "beta.py").write_text("VALUE = 200\n", encoding="utf-8")
    _git(root, "add", "scripts/lexicon/beta.py")
    _git(root, "commit", "--quiet", "-m", "lexicon change")

    assert pr_touches_manifest_scope(root=root, base_ref="base") is True
    assert check_freshness(
        root=root,
        fingerprint_path=sidecar,
        pr_scoped=True,
        base_ref="base",
    ) == 2
    assert "Atlas manifest stale vs lexicon code" in capsys.readouterr().out


def test_pr_scoped_freshness_fails_when_pr_changes_sidecar(tmp_path: Path, capsys) -> None:
    root = _fixture_repo(tmp_path)
    sidecar = root / "site" / "src" / "data" / "lexicon-manifest.fingerprint.json"
    write_fingerprint(sidecar, root=root)
    _commit_fixture_repo(root)
    sidecar.write_text('{"fingerprint": "stale"}\n', encoding="utf-8")
    _git(root, "add", sidecar.relative_to(root).as_posix())
    _git(root, "commit", "--quiet", "-m", "sidecar change")

    assert pr_touches_manifest_scope(root=root, base_ref="base") is True
    assert check_freshness(
        root=root,
        fingerprint_path=sidecar,
        pr_scoped=True,
        base_ref="base",
    ) == 2
    assert "Atlas manifest stale vs lexicon code" in capsys.readouterr().out


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
