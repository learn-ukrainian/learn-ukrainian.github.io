import json
from pathlib import Path

from scripts.lexicon.check_manifest_freshness import check_freshness
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


def test_manifest_fingerprint_is_stable_across_runs(tmp_path: Path) -> None:
    root = _fixture_repo(tmp_path)

    first = build_fingerprint(root)
    second = build_fingerprint(root)

    assert first == second
    assert first["stats"] == {"lexicon_code_files": 2, "vocabulary_lemmas": 2}


def test_manifest_fingerprint_changes_when_lexicon_source_byte_changes(tmp_path: Path) -> None:
    root = _fixture_repo(tmp_path)
    before = build_fingerprint(root)["fingerprint"]

    (root / "scripts" / "lexicon" / "alpha.py").write_text("VALUE = 10\n", encoding="utf-8")
    after = build_fingerprint(root)["fingerprint"]

    assert after != before


def test_manifest_fingerprint_changes_when_vocab_lemma_is_added(tmp_path: Path) -> None:
    root = _fixture_repo(tmp_path)
    before = build_fingerprint(root)["fingerprint"]

    vocabulary = root / "curriculum" / "l2-uk-en" / "a1" / "hello" / "vocabulary.yaml"
    vocabulary.write_text(vocabulary.read_text(encoding="utf-8") + "- uk: школа\n", encoding="utf-8")
    after = build_fingerprint(root)["fingerprint"]

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
    assert "Atlas manifest stale vs lexicon code / vocab" in output
    assert "dictionary DB/cache version drift is out of scope" in output
