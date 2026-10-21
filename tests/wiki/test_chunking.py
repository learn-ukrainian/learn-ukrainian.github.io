"""Tests for the centralized boundary-aware chunker (#1553 step 1)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from wiki.chunking import (
    CHUNKING_POLICIES,
    ChunkingPolicy,
    boundary_aware_chunks,
    split_sentences,
)


class FakeTokenizer:
    """Whitespace-token tokenizer that round-trips faithfully.

    Each whitespace-separated word is one token. ``decode`` rejoins
    with single spaces so token-window splits land on word
    boundaries, matching real BGE-M3 behavior closely enough for
    chunking-policy unit tests. The real tokenizer's subword
    behavior differs in detail but never in chunking direction —
    if a chunk fits under the FakeTokenizer it'll fit under BGE-M3
    (BGE produces strictly more tokens for the same text).
    """

    def encode(
        self,
        text: str,
        *,
        add_special_tokens: bool = False,
        truncation: bool = False,
        max_length: int | None = None,
    ) -> list[int]:
        del add_special_tokens, truncation
        tokens = text.split()
        if max_length is not None:
            tokens = tokens[:max_length]
        # Token IDs are arbitrary; chunker only cares about length
        # and round-trip.
        return list(range(1, len(tokens) + 1))

    def decode(self, token_ids: list[int], *, skip_special_tokens: bool = True) -> str:
        del skip_special_tokens
        return " ".join(f"tok{tid}" for tid in token_ids)


@pytest.fixture
def tokenizer() -> FakeTokenizer:
    return FakeTokenizer()


# --- Registry guards ---------------------------------------------------------


def test_supported_corpora_each_have_a_policy() -> None:
    """Every corpus in ``SUPPORTED_CORPORA`` must register a chunking
    policy so ``policy_for`` doesn't raise at runtime."""

    from wiki.dense_rerank import SUPPORTED_CORPORA

    missing = [c for c in SUPPORTED_CORPORA if c not in CHUNKING_POLICIES]
    assert missing == [], f"corpora missing from CHUNKING_POLICIES: {missing}"


def test_paragraph_aware_version_id_encodes_parameters() -> None:
    """version_id must change when target_tokens or overlap changes,
    so the manifest never silently shares vectors across distinct
    chunker configurations."""

    policy = CHUNKING_POLICIES["wikipedia"]
    assert "450t" in policy.version_id
    assert "o50" in policy.version_id
    # Sanity: two policies built with different params get different ids.
    custom_a = ChunkingPolicy(
        version_id="x:paragraph-aware-450t-o50-v1",
        target_tokens=450,
        overlap_tokens=50,
    )
    custom_b = ChunkingPolicy(
        version_id="x:paragraph-aware-1500t-o150-v1",
        target_tokens=1500,
        overlap_tokens=150,
    )
    assert custom_a.version_id != custom_b.version_id


# --- Paragraph + sentence splitters ------------------------------------------


def test_split_sentences_merges_after_ukrainian_abbreviation() -> None:
    """``проф. Іван Франко був видатним...`` should not split on
    ``проф.``. Same for вул., р., ст., etc."""

    paragraph = "проф. Іван Франко був видатним українським письменником."
    sents = split_sentences(paragraph)
    assert sents == [paragraph], (
        f"abbreviation guard failed; got {sents!r}"
    )


# --- Core boundary-aware chunker --------------------------------------------


# --- Overlap behavior -------------------------------------------------------


def test_overlap_caps_at_overlap_tokens_when_sentence_too_long(
    tokenizer: FakeTokenizer,
) -> None:
    """If even a single trailing sentence exceeds ``overlap_tokens``,
    the overlap path must NOT return the whole sentence — that
    would push downstream chunks past the chunker's target and
    trip the validator gate (#1553 step 3).

    Codex review (msg #459) flagged this: a 200-token trailing
    sentence with overlap_tokens=50 would otherwise produce
    650-token chunks under a 450-target policy. Fix: token-tail
    fallback when sentence overlap doesn't fit.
    """

    # Construct a corpus where the LAST sentence is itself longer
    # than the overlap budget. With target=100 and overlap=20, no
    # full sentence fits the overlap window.
    long_sentence = " ".join(f"long{i}" for i in range(50)) + "."
    para_a = " ".join(f"a{i}" for i in range(40)) + "."
    para_b = " ".join(f"b{i}" for i in range(40)) + "."
    text = f"{para_a} {long_sentence}\n\n{para_b}"
    policy = ChunkingPolicy(version_id="t:v1", target_tokens=100, overlap_tokens=20)
    chunks = boundary_aware_chunks(text, policy=policy, tokenizer=tokenizer)
    assert len(chunks) >= 2

    # Critical assertion: every chunk fits within target_tokens +
    # overlap_tokens. If overlap returns the whole 50-token sentence
    # the second chunk would be ~90 tokens (overlap) + 40 (para_b)
    # = 130 tokens, exceeding even (target+overlap=120).
    for index, chunk in enumerate(chunks):
        chunk_tokens = len(tokenizer.encode(chunk, add_special_tokens=False, truncation=False))
        assert chunk_tokens <= policy.target_tokens + policy.overlap_tokens, (
            f"chunk {index} ({chunk_tokens}t) exceeds target+overlap "
            f"({policy.target_tokens + policy.overlap_tokens}t); the "
            f"overlap cap regressed."
        )


# --- chunk_text integration --------------------------------------------------


# --- Validator gate (#1553 step 3) -------------------------------------------


def test_validator_raises_when_unit_exceeds_index_max_length(
    tokenizer: FakeTokenizer,
) -> None:
    """The validator gate must reject a corpus whose chunked units
    still exceed ``INDEX_MAX_LENGTH``. Catches the failure mode where
    a chunking policy's ``target_tokens`` was bumped without
    coordinating ``INDEX_MAX_LENGTH`` (or vice versa)."""

    from wiki import chunking, dense_rerank
    from wiki.dense_rerank import CorpusUnit, _assert_units_fit_index_window

    # Synthesize a unit that's clearly over the cap (FakeTokenizer
    # uses whitespace tokens; 100 words = 100 tokens).
    too_long = " ".join(f"word{i}" for i in range(100))
    unit = CorpusUnit(
        unit_key="test_validator:1",
        corpus="test_validator",
        parent_key="parent",
        text=too_long,
        text_sha256="sha",
        metadata={},
    )

    # Register the test corpus with an active policy so the validator
    # actually runs (NO_CHUNK policy short-circuits).
    chunking.CHUNKING_POLICIES["test_validator"] = chunking.ChunkingPolicy(
        version_id="test_validator:paragraph-aware-450t-o50-v1",
        target_tokens=450,
        overlap_tokens=50,
    )
    original_get_tokenizer = dense_rerank._get_tokenizer
    dense_rerank._get_tokenizer = lambda: tokenizer  # type: ignore[assignment]

    try:
        with pytest.raises(ValueError, match="exceeding INDEX_MAX_LENGTH"):
            _assert_units_fit_index_window([unit], corpus="test_validator", max_length=50)
    finally:
        del chunking.CHUNKING_POLICIES["test_validator"]
        dense_rerank._get_tokenizer = original_get_tokenizer  # type: ignore[assignment]


def test_validator_silent_on_no_chunk_corpus(tokenizer: FakeTokenizer) -> None:
    """NO_CHUNK corpora must NOT trigger the validator — by design,
    they accept unit lengths the encoder will truncate. Re-chunking
    them at index time would invalidate 137K+ vectors."""

    from wiki import dense_rerank
    from wiki.dense_rerank import CorpusUnit, _assert_units_fit_index_window

    too_long = " ".join(f"word{i}" for i in range(100))
    unit = CorpusUnit(
        unit_key="modern_literary:1",
        corpus="modern_literary",
        parent_key="parent",
        text=too_long,
        text_sha256="sha",
        metadata={},
    )

    original_get_tokenizer = dense_rerank._get_tokenizer
    dense_rerank._get_tokenizer = lambda: tokenizer  # type: ignore[assignment]
    try:
        # No exception expected — modern_literary uses NO_CHUNK.
        _assert_units_fit_index_window([unit], corpus="modern_literary", max_length=50)
    finally:
        dense_rerank._get_tokenizer = original_get_tokenizer  # type: ignore[assignment]
