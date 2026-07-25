"""Regression for #5776 — do not RLIMIT-poison the pytest worker.

Matrix run ``30167163623`` (``-n auto`` / baseline) looked like it hung on
``tests/wiki/test_ukrainian_wiki_corpus.py::test_main_cli_encode_flag_wires_ingest_to_manifest``.
Log evidence shows that was a misattribution:

- ``gw1`` ran ``test_in_process_slice_stop_after_chunks``, emitted
  ``MemoryError`` from ``sys.unraisablehook`` after the enrich coordinator
  applied ``apply_worker_memory_limit`` to the worker itself, then never
  reported another result.
- ``gw0`` continued and **PASSED** the wiki encode CLI test; the controller
  then stalled waiting for the poisoned worker.

PR #5786 removed the coordinator-side limit application. This module guards
the cross-test failure mode: after an in-process enrich drive, ``RLIMIT_AS``
must be unchanged and a subsequent wiki ``--encode`` CLI path in the same
process must still complete.
"""

from __future__ import annotations

import hashlib
import json
import resource
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "lexicon" / "runner_pr1"
MAX_FIXTURE_LEMMAS = 50

sys.path.insert(0, str(ROOT / "scripts"))

from wiki import dense_rerank, ukrainian_wiki_corpus


def _ensure_enrich_fixture() -> None:
    needed = (
        FIXTURE / "slice_input.json",
        FIXTURE / "sources_slice.sqlite",
        FIXTURE / "kaikki_slice.json",
        FIXTURE / "grac_frequency_slice.json",
    )
    if all(path.is_file() for path in needed):
        return
    from scripts.lexicon.runner.generate_pr1_fixture import main as gen

    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("LEXICON_SLOVNYK_OFFLINE", "1")
        assert gen() == 0
    assert all(path.is_file() for path in needed)


class _FakeTokenizer:
    def encode(
        self,
        text: str,
        add_special_tokens: bool = True,
        truncation: bool = True,
        max_length: int | None = None,
    ) -> list[int]:
        tokens = list(range(1, len(text.split()) + 1))
        if max_length is not None:
            limit = max_length - (2 if add_special_tokens else 0)
            tokens = tokens[:limit]
        if add_special_tokens:
            return [0, *tokens, 1]
        return tokens


class _FakeEncoder:
    def encode(self, texts: list[str], batch_size: int = 16, max_length: int = 512) -> np.ndarray:
        vectors: list[np.ndarray] = []
        for text in texts:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            seed = np.frombuffer(digest * 64, dtype=np.uint8)[: dense_rerank.EMBEDDING_DIMS].astype(
                np.float32
            )
            vector = seed / np.clip(np.linalg.norm(seed), 1e-12, None)
            vectors.append(vector.astype(np.float16))
        return np.stack(vectors, axis=0)


def _install_fake_encoder(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_tokenizer = _FakeTokenizer()
    fake_encoder = _FakeEncoder()
    monkeypatch.setattr(dense_rerank, "_TOKENIZER", fake_tokenizer)
    monkeypatch.setattr(dense_rerank, "_get_tokenizer", lambda: fake_tokenizer)
    monkeypatch.setattr(dense_rerank, "_ENCODER", fake_encoder)
    monkeypatch.setattr(dense_rerank, "_get_encoder", lambda: fake_encoder)


def _run_in_process_enrich(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.lexicon import enrich_manifest as em
    from scripts.lexicon.runner.enrich_offline_20k import main as enrich_main
    from scripts.lexicon.runner.memory import EnforcementProof

    monkeypatch.setattr(em, "_vesum_valid_synonym", lambda term: bool(term))
    monkeypatch.setattr(
        "scripts.lexicon.runner.offline_engine.run_startup_self_test",
        lambda **_kwargs: EnforcementProof(
            kind="rlimit_as",
            enforced=True,
            detail="test stub",
            max_bytes=64 * 1024 * 1024,
        ),
    )

    def _parent_memory_limit_must_not_be_applied(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("the coordinator must not apply a worker memory limit to pytest")

    monkeypatch.setattr(
        "scripts.lexicon.runner.memory.apply_worker_memory_limit",
        _parent_memory_limit_must_not_be_applied,
    )

    def _fake_enrich(payload: dict) -> dict[str, str]:
        entries = json.loads(Path(payload["entries_path"]).read_text(encoding="utf-8"))
        artifact_dir = Path(payload["artifact_dir"])
        artifact_dir.mkdir(parents=True, exist_ok=True)
        arts: dict[str, str] = {}
        for entry in entries:
            lemma_id = str(entry.get("url_slug") or entry.get("lemma") or "")
            body = {
                "lemma": entry.get("lemma"),
                "url_slug": lemma_id,
                "enriched": True,
                "offline_enrich_driver": True,
            }
            raw = json.dumps(body, ensure_ascii=False, sort_keys=True)
            (artifact_dir / f"{lemma_id}.json").write_text(raw + "\n", encoding="utf-8")
            arts[lemma_id] = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return arts

    monkeypatch.setattr(
        "scripts.lexicon.runner.worker_enrich.enrich_chunk_payload",
        _fake_enrich,
    )

    work = tmp_path / "enrich_work"
    out = work / "candidate-enriched.json"
    code = enrich_main(
        [
            "--repo",
            str(ROOT),
            "--work-dir",
            str(work),
            "--candidate",
            str(FIXTURE / "slice_input.json"),
            "--sources-db",
            str(FIXTURE / "sources_slice.sqlite"),
            "--kaikki-json",
            str(FIXTURE / "kaikki_slice.json"),
            "--grac-cache",
            str(FIXTURE / "grac_frequency_slice.json"),
            "--output",
            str(out),
            "--max-lemmas",
            str(MAX_FIXTURE_LEMMAS),
            "--chunk-size",
            "25",
            "--stop-after-chunks",
            "1",
            "--in-process",
        ]
    )
    assert code == 0
    assert out.is_file()


def _run_wiki_encode_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    article = tmp_path / "wiki" / "pedagogy" / "a1" / "simya.md"
    article.parent.mkdir(parents=True, exist_ok=True)
    article.write_text(
        (
            "# Сім'я\n\n"
            "Сім'я — це найближчі люди поряд з учнем [S1]. "
            "Мама, тато, брат і сестра дають першу лексику для A1.\n\n"
            "Учень описує свою родину простими реченнями.\n"
        ),
        encoding="utf-8",
    )
    article_rel = article.relative_to(tmp_path).as_posix()
    article.with_suffix(".sources.yaml").write_text(
        f"# Source registry for {article_rel}\n"
        "sources:\n"
        "  - id: S1\n"
        "    file: ext-demo\n"
        "    type: external\n",
        encoding="utf-8",
    )

    db_path = tmp_path / "sources.db"
    manifest_path = tmp_path / "embeddings" / "manifest.db"

    monkeypatch.setattr(
        ukrainian_wiki_corpus,
        "vesum_batch_lookup",
        lambda words: {word: [{"word": word}] for word in words},
    )
    monkeypatch.setattr(ukrainian_wiki_corpus, "check_russicisms", lambda text, file_path="": [])
    monkeypatch.setattr(ukrainian_wiki_corpus, "pravopys_lookup", lambda term: {"term": term})
    monkeypatch.setattr(ukrainian_wiki_corpus, "search_style_guide", lambda term: [])
    _install_fake_encoder(monkeypatch)

    exit_code = ukrainian_wiki_corpus.main(
        [
            str(article),
            "--db-path",
            str(db_path),
            "--manifest-db",
            str(manifest_path),
            "--min-words",
            "5",
            "--max-chars",
            "1000",
            "--min-vesum-coverage",
            "0.5",
            "--encode",
        ]
    )
    assert exit_code == 0
    assert manifest_path.is_file()


def test_in_process_enrich_does_not_poison_rlimit_before_wiki_encode(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Same-process sequence that hung the -n auto suite when RLIMIT leaked (#5776)."""
    _ensure_enrich_fixture()
    before = resource.getrlimit(resource.RLIMIT_AS)

    _run_in_process_enrich(tmp_path, monkeypatch)

    after_enrich = resource.getrlimit(resource.RLIMIT_AS)
    assert after_enrich == before, (
        "in-process enrich must not clamp RLIMIT_AS on the pytest process; "
        f"before={before!r} after={after_enrich!r}"
    )

    _run_wiki_encode_cli(tmp_path, monkeypatch)

    after_wiki = resource.getrlimit(resource.RLIMIT_AS)
    assert after_wiki == before
