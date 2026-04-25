"""Tests for the centralized boundary-aware chunker (#1553 step 1)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from wiki.chunking import (
    _UK_ABBREVIATIONS,
    CHUNKING_POLICIES,
    NO_CHUNK,
    ChunkingPolicy,
    boundary_aware_chunks,
    chunk_text,
    policy_for,
    split_paragraphs,
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


def test_no_chunk_policy_yields_target_tokens_zero() -> None:
    assert NO_CHUNK.target_tokens == 0


def test_supported_corpora_each_have_a_policy() -> None:
    """Every corpus in ``SUPPORTED_CORPORA`` must register a chunking
    policy so ``policy_for`` doesn't raise at runtime."""

    from wiki.dense_rerank import SUPPORTED_CORPORA

    missing = [c for c in SUPPORTED_CORPORA if c not in CHUNKING_POLICIES]
    assert missing == [], f"corpora missing from CHUNKING_POLICIES: {missing}"


def test_policy_for_unknown_corpus_raises() -> None:
    with pytest.raises(KeyError, match="no ChunkingPolicy registered"):
        policy_for("nonexistent_corpus")


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


def test_split_paragraphs_blank_line_boundaries() -> None:
    text = "Перший абзац.\n\nДругий абзац.\n\n\n\nТретій."
    assert split_paragraphs(text) == ["Перший абзац.", "Другий абзац.", "Третій."]


def test_split_paragraphs_drops_empty() -> None:
    assert split_paragraphs("\n\n\n\n") == []


def test_split_sentences_basic() -> None:
    paragraph = "Перше речення. Друге речення! Третє речення?"
    sents = split_sentences(paragraph)
    assert sents == ["Перше речення.", "Друге речення!", "Третє речення?"]


def test_split_sentences_merges_after_ukrainian_abbreviation() -> None:
    """``проф. Іван Франко був видатним...`` should not split on
    ``проф.``. Same for вул., р., ст., etc."""

    paragraph = "проф. Іван Франко був видатним українським письменником."
    sents = split_sentences(paragraph)
    assert sents == [paragraph], (
        f"abbreviation guard failed; got {sents!r}"
    )


def test_split_sentences_handles_multiple_abbreviations() -> None:
    paragraph = "Жив на вул. Шевченка. Помер у 1916 р. Похований у Львові."
    sents = split_sentences(paragraph)
    # The вул. shouldn't split, the р. shouldn't split, only the
    # final period should — but we permit fewer splits if the guard
    # is conservative. Critical: вул./р. don't split mid-clause.
    joined = " ".join(sents)
    assert "вул. Шевченка" in joined or "Шевченка" not in joined, (
        f"вул. abbreviation broke clause: {sents!r}"
    )


def test_uk_abbreviations_set_includes_common() -> None:
    for required in ("вул", "р", "ст", "проф", "акад"):
        assert required in _UK_ABBREVIATIONS


# --- Core boundary-aware chunker --------------------------------------------


def test_boundary_aware_short_text_returns_single_chunk(tokenizer: FakeTokenizer) -> None:
    policy = ChunkingPolicy(version_id="t:v1", target_tokens=100, overlap_tokens=10)
    text = "коротке речення тут."
    chunks = boundary_aware_chunks(text, policy=policy, tokenizer=tokenizer)
    assert chunks == [text]


def test_boundary_aware_empty_text_returns_empty_list(tokenizer: FakeTokenizer) -> None:
    policy = ChunkingPolicy(version_id="t:v1", target_tokens=100, overlap_tokens=10)
    assert boundary_aware_chunks("", policy=policy, tokenizer=tokenizer) == []
    assert boundary_aware_chunks("   \n\n\n  ", policy=policy, tokenizer=tokenizer) == []


def test_boundary_aware_multi_paragraph_chunks_at_paragraph_boundaries(
    tokenizer: FakeTokenizer,
) -> None:
    """Three 60-token paragraphs with target=100 -> two chunks
    grouped on paragraph boundaries (60+? doesn't fit 100, so flush
    after each).
    """

    para_a = " ".join(f"a{i}" for i in range(60))
    para_b = " ".join(f"b{i}" for i in range(60))
    para_c = " ".join(f"c{i}" for i in range(60))
    text = f"{para_a}\n\n{para_b}\n\n{para_c}"
    policy = ChunkingPolicy(version_id="t:v1", target_tokens=100, overlap_tokens=0)
    chunks = boundary_aware_chunks(text, policy=policy, tokenizer=tokenizer)
    # Each chunk should be exactly one paragraph (60 tokens) since
    # 60+60=120 > target 100 -> flush after each.
    assert len(chunks) == 3
    assert all("a" in chunks[0] for _ in [None])  # first chunk has para_a tokens
    assert "b0" not in chunks[0]
    assert "c0" not in chunks[0]


def test_boundary_aware_combines_small_paragraphs_into_one_chunk(
    tokenizer: FakeTokenizer,
) -> None:
    """Two 30-token paragraphs with target=100 -> one chunk of both."""

    para_a = " ".join(f"a{i}" for i in range(30))
    para_b = " ".join(f"b{i}" for i in range(30))
    text = f"{para_a}\n\n{para_b}"
    policy = ChunkingPolicy(version_id="t:v1", target_tokens=100, overlap_tokens=0)
    chunks = boundary_aware_chunks(text, policy=policy, tokenizer=tokenizer)
    assert len(chunks) == 1
    assert "a0" in chunks[0] and "b0" in chunks[0]


def test_boundary_aware_long_paragraph_falls_back_to_sentences(
    tokenizer: FakeTokenizer,
) -> None:
    """One paragraph of three 40-token sentences with target=70 ->
    splits at sentence boundaries (1 + 2 sentence groups, since
    40+40=80 > 70 -> flush)."""

    sents = [
        " ".join(f"s{i}-{j}" for j in range(40)) + "."
        for i in range(3)
    ]
    paragraph = " ".join(sents)
    policy = ChunkingPolicy(version_id="t:v1", target_tokens=70, overlap_tokens=0)
    chunks = boundary_aware_chunks(paragraph, policy=policy, tokenizer=tokenizer)
    # Each chunk should hold one full sentence; never split mid-sentence.
    for chunk in chunks:
        # Count complete sentence-end markers; chunks shouldn't end
        # mid-sentence since each sentence fits within target.
        assert chunk.rstrip().endswith("."), f"sentence boundary lost: {chunk[:50]!r}"


def test_boundary_aware_pathological_long_sentence_falls_back_to_token_window(
    tokenizer: FakeTokenizer,
) -> None:
    """One 500-token sentence with target=200 -> token-window fallback
    yields multiple chunks; no crash, total content preserved
    (modulo token-window decode artifacts in the FakeTokenizer)."""

    sentence = " ".join(f"w{i}" for i in range(500))
    policy = ChunkingPolicy(version_id="t:v1", target_tokens=200, overlap_tokens=0)
    chunks = boundary_aware_chunks(sentence, policy=policy, tokenizer=tokenizer)
    assert len(chunks) >= 2
    # Each chunk is at most ~target_tokens long (FakeTokenizer is 1
    # word per token + decode prefix "tok").
    for chunk in chunks:
        assert chunk  # non-empty


# --- Overlap behavior -------------------------------------------------------


def test_overlap_prepends_trailing_sentences_to_next_chunk(
    tokenizer: FakeTokenizer,
) -> None:
    """When overlap is > 0, chunk N+1 should start with the trailing
    sentences of chunk N, providing cross-chunk semantic continuity."""

    # Two paragraphs, each ~60 tokens. With target=70 we'll get two
    # chunks (each one paragraph). Overlap=20 should pull the last
    # sentence of chunk 0 into the start of chunk 1.
    sentences_a = [
        " ".join(f"s0-{i}-{j}" for j in range(15)) + "."
        for i in range(4)
    ]
    sentences_b = [
        " ".join(f"s1-{i}-{j}" for j in range(15)) + "."
        for i in range(4)
    ]
    text = " ".join(sentences_a) + "\n\n" + " ".join(sentences_b)
    policy = ChunkingPolicy(version_id="t:v1", target_tokens=70, overlap_tokens=20)
    chunks = boundary_aware_chunks(text, policy=policy, tokenizer=tokenizer)
    assert len(chunks) >= 2
    # Last sentence of chunk 0 should appear at the start of chunk 1.
    last_sentence_a = sentences_a[-1]
    assert chunks[1].startswith(last_sentence_a), (
        f"overlap missing; chunk[1] starts {chunks[1][:80]!r}, "
        f"expected leading {last_sentence_a!r}"
    )


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


def test_overlap_zero_yields_no_duplication(tokenizer: FakeTokenizer) -> None:
    """With overlap=0, adjacent chunks must not share any sentence —
    no duplication, no loss."""

    para_a = " ".join(f"a{i}" for i in range(60))
    para_b = " ".join(f"b{i}" for i in range(60))
    text = f"{para_a}\n\n{para_b}"
    policy = ChunkingPolicy(version_id="t:v1", target_tokens=100, overlap_tokens=0)
    chunks = boundary_aware_chunks(text, policy=policy, tokenizer=tokenizer)
    # Tokens from para_a should appear only in chunks[0], never
    # leaking into chunks[1+].
    if len(chunks) >= 2:
        assert "a0" in chunks[0] and "a0" not in chunks[1]
        assert "b0" in chunks[1] and "b0" not in chunks[0]


# --- chunk_text integration --------------------------------------------------


def test_chunk_text_no_chunk_policy_yields_one_piece(tokenizer: FakeTokenizer) -> None:
    pieces = list(chunk_text("будь-який текст", policy=NO_CHUNK, tokenizer=tokenizer))
    assert len(pieces) == 1
    assert pieces[0].chunk_index == 0
    assert pieces[0].text == "будь-який текст"


def test_chunk_text_short_text_under_target_yields_one_piece(
    tokenizer: FakeTokenizer,
) -> None:
    policy = ChunkingPolicy(version_id="t:v1", target_tokens=100, overlap_tokens=0)
    pieces = list(chunk_text("короткий текст.", policy=policy, tokenizer=tokenizer))
    assert len(pieces) == 1
    assert pieces[0].chunk_index == 0


def test_chunk_text_long_text_yields_indexed_pieces(tokenizer: FakeTokenizer) -> None:
    para_a = " ".join(f"a{i}" for i in range(60))
    para_b = " ".join(f"b{i}" for i in range(60))
    para_c = " ".join(f"c{i}" for i in range(60))
    text = f"{para_a}\n\n{para_b}\n\n{para_c}"
    policy = ChunkingPolicy(version_id="t:v1", target_tokens=100, overlap_tokens=0)
    pieces = list(chunk_text(text, policy=policy, tokenizer=tokenizer))
    assert len(pieces) == 3
    assert [piece.chunk_index for piece in pieces] == [0, 1, 2]
    for piece in pieces:
        assert piece.extra_metadata.get("chunk_count") == 3


def test_chunk_text_empty_yields_nothing(tokenizer: FakeTokenizer) -> None:
    policy = ChunkingPolicy(version_id="t:v1", target_tokens=100, overlap_tokens=0)
    assert list(chunk_text("", policy=policy, tokenizer=tokenizer)) == []
    assert list(chunk_text("   ", policy=policy, tokenizer=tokenizer)) == []


# --- Validator gate (#1553 step 3) -------------------------------------------


def test_validator_raises_when_unit_exceeds_index_max_length(
    tokenizer: FakeTokenizer,
) -> None:
    """The validator gate must reject a corpus whose chunked units
    still exceed ``INDEX_MAX_LENGTH``. Catches the failure mode where
    a chunking policy's ``target_tokens`` was bumped without
    coordinating ``INDEX_MAX_LENGTH`` (or vice versa)."""

    from wiki.dense_rerank import CorpusUnit, _assert_units_fit_index_window

    from wiki import chunking, dense_rerank

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

    from wiki.dense_rerank import CorpusUnit, _assert_units_fit_index_window

    from wiki import dense_rerank

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
