"""Boundary-aware chunking policies for the dense retrieval index.

Replaces the per-iterator ad-hoc chunkers (#1348 only chunked Wikipedia
at 450/50 tokens via ``chunk_wikipedia_article``; textbook / external /
literary corpora ran un-chunked through a 512-token encoder window,
silently truncating long sources). #1553 centralizes chunking here:
one policy per corpus, one algorithm, one place to change.

Design notes:

- ``ChunkingPolicy`` carries a ``version_id`` that gets stamped into
  ``embedding_units.chunk_policy_version``. Bumping the version forces
  re-encode of that corpus alone — see #1553 step 0.
- Boundary-aware splitting tries paragraph -> sentence -> token-window
  in that order, so chunk boundaries land at semantic seams whenever
  possible. MIRACL precedent for paragraph-first segmentation.
- Ukrainian uses the same terminal punctuation as English (.!?…), so
  the splitter is mostly language-agnostic. A small abbreviation
  guard handles the most common Ukrainian period-non-terminators
  (вул., р., ст., etc.) without claiming exhaustive coverage —
  false negatives produce slightly longer chunks, which is harmless.
- The chunker uses the BGE-M3 tokenizer for length accounting so its
  count matches what the encoder will see.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Protocol

from .embedding_manifest_schema import LEGACY_CHUNK_POLICY_VERSION


class TokenizerProtocol(Protocol):
    def encode(
        self,
        text: str,
        *,
        add_special_tokens: bool = ...,
        truncation: bool = ...,
    ) -> list[int]: ...


@dataclass(frozen=True)
class ChunkingPolicy:
    """Per-corpus chunking strategy + manifest version stamp.

    ``target_tokens`` of 0 disables chunking entirely — the original
    unit is yielded unchanged. Used for corpora that are already
    ingest-time chunked to a sensible size (``ukrainian_wiki``,
    literary).

    ``version_id`` is what gets written to
    ``embedding_units.chunk_policy_version``. By convention:
    ``"<corpus>:<algo>-v<n>"`` — so a textbook chunker change does
    not invalidate Wikipedia embeddings. The shipped value
    ``LEGACY_CHUNK_POLICY_VERSION`` is reserved for the no-chunk
    case so legacy manifest rows stay valid.
    """

    version_id: str
    target_tokens: int
    overlap_tokens: int


#: No-op policy for corpora that are already pre-chunked at ingest
#: (``ukrainian_wiki``, ``modern_literary``, ``archaic_literary``).
NO_CHUNK = ChunkingPolicy(
    version_id=LEGACY_CHUNK_POLICY_VERSION,
    target_tokens=0,
    overlap_tokens=0,
)


def _paragraph_aware_policy(corpus: str, *, target: int, overlap: int) -> ChunkingPolicy:
    """Construct a paragraph-aware policy whose ``version_id`` encodes
    the parameters.

    Codex review (msg #457): "Include policy params in version_id or
    make version bumps mandatory when target_tokens / overlap_tokens
    change." Auto-deriving the version from params makes accidental
    silent reuse impossible — bumping ``target`` or ``overlap``
    mechanically bumps the manifest stamp.
    """

    return ChunkingPolicy(
        version_id=f"{corpus}:paragraph-aware-{target}t-o{overlap}-v1",
        target_tokens=target,
        overlap_tokens=overlap,
    )


#: Step 1 chunk size. Matches the #1348-shipped Wikipedia chunker
#: (450 tokens with 50-token overlap) so chunks fit within the
#: current ``INDEX_MAX_LENGTH=512`` window without any encoder-side
#: truncation. Bakeoff (#1553 step 5) will override this with larger
#: values once ``INDEX_MAX_LENGTH`` bumps to 2048+; the auto-derived
#: ``version_id`` mechanically forces a re-encode when that lands.
_STEP1_TARGET_TOKENS = 450
_STEP1_OVERLAP_TOKENS = 50


#: Per-corpus chunking policies. SUPPORTED_CORPORA must be a subset
#: of these keys — see the ``_assert_full_coverage`` sanity check at
#: import time.
CHUNKING_POLICIES: dict[str, ChunkingPolicy] = {
    # Already paragraph-pre-chunked at ingest, p99 ~240 tokens.
    "ukrainian_wiki": NO_CHUNK,
    # Ingest-time chunked at ~620 tokens, p99 ~1300 tokens — already
    # fits the current 512-token encoder window for the bulk of
    # rows; re-chunking would invalidate 137K vectors for marginal
    # tail-recall gain.
    "modern_literary": NO_CHUNK,
    "archaic_literary": NO_CHUNK,
    # Long-form corpora that #1348 left un-chunked. Median token
    # counts: textbook 1000, external 4500, wikipedia 3800. All
    # exceed the current 512-token encoder window without chunking.
    "wikipedia": _paragraph_aware_policy(
        "wikipedia", target=_STEP1_TARGET_TOKENS, overlap=_STEP1_OVERLAP_TOKENS
    ),
    "external": _paragraph_aware_policy(
        "external", target=_STEP1_TARGET_TOKENS, overlap=_STEP1_OVERLAP_TOKENS
    ),
    "textbook_sections": _paragraph_aware_policy(
        "textbook_sections",
        target=_STEP1_TARGET_TOKENS,
        overlap=_STEP1_OVERLAP_TOKENS,
    ),
}


def policy_for(corpus: str) -> ChunkingPolicy:
    """Return the active ``ChunkingPolicy`` for ``corpus``.

    Raises ``KeyError`` for corpora not registered in
    ``CHUNKING_POLICIES``. Codex review (msg #457): "Avoid
    ``CHUNKING_POLICIES.get(corpus, NO_CHUNK)`` silently masking
    unknown corpora if corpus names are expected to be closed."
    Closed they are — ``SUPPORTED_CORPORA`` in dense_rerank is the
    canonical list and a NEW corpus must register its policy
    explicitly.
    """

    try:
        return CHUNKING_POLICIES[corpus]
    except KeyError as exc:
        known = sorted(CHUNKING_POLICIES)
        raise KeyError(
            f"no ChunkingPolicy registered for corpus {corpus!r}; "
            f"register one in CHUNKING_POLICIES or use NO_CHUNK explicitly. "
            f"Known: {known}"
        ) from exc


# --- Boundary-aware splitter -------------------------------------------------

_PARA_RE = re.compile(r"\n\n+")
_SENT_RE = re.compile(r"(?<=[.!?…])\s+")

#: Conservative list of Ukrainian abbreviations that look like sentence
#: terminators but aren't. False negatives just produce slightly longer
#: chunks; false positives would split mid-clause, which is worse, so
#: we err toward including more here.
_UK_ABBREVIATIONS: frozenset[str] = frozenset({
    "акад",        # академік
    "вул",         # вулиця
    "грн",         # гривень
    "ім",          # імені
    "ін",          # інше
    "напр",        # наприклад
    "наприкл",     # наприклад
    "обл",         # область
    "п",           # пан / пункт
    "проф",        # професор
    "р",           # рік / річка
    "рр",          # роки
    "ст",          # стаття / століття
    "т",           # том
    "тт",          # томи
    "т.зв",        # так званий
    "т.т",         # тобто
})


def split_paragraphs(text: str) -> list[str]:
    """Split ``text`` on blank-line boundaries, dropping empties."""

    return [paragraph.strip() for paragraph in _PARA_RE.split(text) if paragraph.strip()]


def split_sentences(paragraph: str) -> list[str]:
    """Split a paragraph on terminal-punctuation+whitespace boundaries.

    Merges fragments whose preceding token is a known Ukrainian
    abbreviation, so ``"проф. Іван Франко був..."`` stays one
    sentence instead of splitting on ``"проф."``.
    """

    raw = _SENT_RE.split(paragraph)
    out: list[str] = []
    for fragment in raw:
        fragment = fragment.strip()
        if not fragment:
            continue
        if out:
            previous = out[-1]
            tail_word = _last_alpha_token(previous).lower()
            if tail_word in _UK_ABBREVIATIONS:
                out[-1] = f"{previous} {fragment}"
                continue
        out.append(fragment)
    return out


def _last_alpha_token(text: str) -> str:
    # Find last "word." pattern: last alphabetic run before a trailing dot.
    match = re.search(r"([A-Za-zА-Яа-яҐґЄєІіЇї]+)\.\s*$", text)
    return match.group(1) if match else ""


def _count_tokens(text: str, *, tokenizer: TokenizerProtocol) -> int:
    """Token count using the encoder's tokenizer; matches what the
    encoder will see at index time."""

    return len(tokenizer.encode(text, add_special_tokens=False, truncation=False))


def boundary_aware_chunks(
    text: str,
    *,
    policy: ChunkingPolicy,
    tokenizer: TokenizerProtocol,
) -> list[str]:
    """Return a list of chunk strings for ``text`` per ``policy``.

    Empty input -> empty list. Text under ``target_tokens`` -> a
    single-element list containing the original (possibly stripped)
    text. ``policy.target_tokens == 0`` is invalid here; callers
    should short-circuit at the registry level via ``NO_CHUNK``.
    """

    if policy.target_tokens <= 0:
        raise ValueError("boundary_aware_chunks requires target_tokens > 0")

    text = text.strip()
    if not text:
        return []

    total_tokens = _count_tokens(text, tokenizer=tokenizer)
    if total_tokens <= policy.target_tokens:
        return [text]

    paragraphs = split_paragraphs(text)
    if not paragraphs:
        return [text]

    chunks: list[str] = []
    buffer: list[str] = []
    buffer_tokens = 0

    for paragraph in paragraphs:
        paragraph_tokens = _count_tokens(paragraph, tokenizer=tokenizer)
        # Case 1: a single paragraph blows the budget on its own.
        if paragraph_tokens > policy.target_tokens:
            if buffer:
                chunks.append("\n\n".join(buffer))
                buffer = []
                buffer_tokens = 0
            chunks.extend(_chunk_long_paragraph(paragraph, policy=policy, tokenizer=tokenizer))
            continue
        # Case 2: adding this paragraph would overflow the buffer.
        if buffer_tokens + paragraph_tokens > policy.target_tokens:
            chunks.append("\n\n".join(buffer))
            buffer = []
            buffer_tokens = 0
        buffer.append(paragraph)
        buffer_tokens += paragraph_tokens

    if buffer:
        chunks.append("\n\n".join(buffer))

    return _apply_overlap(chunks, policy=policy, tokenizer=tokenizer)


def _chunk_long_paragraph(
    paragraph: str,
    *,
    policy: ChunkingPolicy,
    tokenizer: TokenizerProtocol,
) -> list[str]:
    """Split a paragraph that exceeds the target into sentence-aligned
    chunks, falling back to raw token windows for pathologically long
    single sentences."""

    sentences = split_sentences(paragraph)
    if not sentences:
        return [paragraph]

    chunks: list[str] = []
    buffer: list[str] = []
    buffer_tokens = 0
    for sentence in sentences:
        sentence_tokens = _count_tokens(sentence, tokenizer=tokenizer)
        if sentence_tokens > policy.target_tokens:
            if buffer:
                chunks.append(" ".join(buffer))
                buffer = []
                buffer_tokens = 0
            chunks.extend(_chunk_token_window(sentence, policy=policy, tokenizer=tokenizer))
            continue
        if buffer_tokens + sentence_tokens > policy.target_tokens:
            chunks.append(" ".join(buffer))
            buffer = []
            buffer_tokens = 0
        buffer.append(sentence)
        buffer_tokens += sentence_tokens

    if buffer:
        chunks.append(" ".join(buffer))

    return chunks


def _chunk_token_window(
    text: str,
    *,
    policy: ChunkingPolicy,
    tokenizer: TokenizerProtocol,
) -> list[str]:
    """Last-resort token-window splitter for pathological single
    sentences that exceed the chunk target. Decode-encodes round-trip
    so the chunk text can be measured by the same tokenizer.
    """

    token_ids = tokenizer.encode(text, add_special_tokens=False, truncation=False)
    if not token_ids:
        return []
    if len(token_ids) <= policy.target_tokens:
        return [text]

    # The tokenizer object also exposes ``decode`` on real BGE-M3, but
    # the protocol here only types ``encode``. Cast at use site to
    # keep the public surface narrow; tests pass a fake tokenizer
    # that supports both.
    decode = getattr(tokenizer, "decode", None)
    if decode is None:  # pragma: no cover — defensive
        # If decode isn't available we can't safely chop tokens back
        # into text. Yield the text whole and let the encoder
        # truncate — degrades gracefully.
        return [text]

    chunks: list[str] = []
    step = max(1, policy.target_tokens - policy.overlap_tokens)
    start = 0
    while start < len(token_ids):
        end = min(len(token_ids), start + policy.target_tokens)
        piece = decode(token_ids[start:end], skip_special_tokens=True).strip()
        if piece:
            chunks.append(piece)
        if end >= len(token_ids):
            break
        start += step
    return chunks


def _apply_overlap(
    chunks: list[str],
    *,
    policy: ChunkingPolicy,
    tokenizer: TokenizerProtocol,
) -> list[str]:
    """Prepend the trailing ``overlap_tokens`` of chunk N to chunk
    N+1, taken at sentence boundaries when possible.

    Token-aligned overlap is a fallback. Sentence-aligned overlap is
    preferred because it preserves clause boundaries — the whole
    point of boundary-aware chunking.
    """

    if policy.overlap_tokens <= 0 or len(chunks) < 2:
        return chunks

    out: list[str] = [chunks[0]]
    for idx in range(1, len(chunks)):
        prev = out[-1]
        overlap = _trailing_sentences_for_overlap(
            prev,
            target_tokens=policy.overlap_tokens,
            tokenizer=tokenizer,
        )
        if overlap:
            out.append(f"{overlap} {chunks[idx]}".strip())
        else:
            out.append(chunks[idx])
    return out


def _trailing_sentences_for_overlap(
    text: str,
    *,
    target_tokens: int,
    tokenizer: TokenizerProtocol,
) -> str:
    """Pick the trailing sentences of ``text`` that fit within
    ``target_tokens``. Empty string if no sentence fits."""

    sentences = split_sentences(text)
    if not sentences:
        return ""
    chosen: list[str] = []
    chosen_tokens = 0
    for sentence in reversed(sentences):
        sentence_tokens = _count_tokens(sentence, tokenizer=tokenizer)
        if chosen_tokens + sentence_tokens > target_tokens and chosen:
            break
        chosen.insert(0, sentence)
        chosen_tokens += sentence_tokens
        if chosen_tokens >= target_tokens:
            break
    return " ".join(chosen)


# --- Unit-level chunking integration -----------------------------------------

#: Result of chunking a single ``CorpusUnit``. Caller (in
#: ``dense_rerank.load_corpus_units``) maps these back to
#: ``CorpusUnit`` objects with proper unit_key/parent_key/metadata.
@dataclass(frozen=True)
class ChunkedPiece:
    chunk_index: int
    text: str
    extra_metadata: dict[str, object] = field(default_factory=dict)


def chunk_text(
    text: str,
    *,
    policy: ChunkingPolicy,
    tokenizer: TokenizerProtocol,
) -> Iterator[ChunkedPiece]:
    """Yield ``ChunkedPiece`` instances for ``text`` per ``policy``.

    The integration point used by ``dense_rerank.load_corpus_units``.
    Yields exactly one piece (chunk_index=0) when ``policy`` is
    ``NO_CHUNK`` or the text already fits — preserving the
    "single-chunk" contract that pre-#1553 ingest expects.
    """

    if policy.target_tokens <= 0:
        # NO_CHUNK — caller wants the original unit back unchanged.
        yield ChunkedPiece(chunk_index=0, text=text)
        return

    pieces = boundary_aware_chunks(text, policy=policy, tokenizer=tokenizer)
    if len(pieces) <= 1:
        # Either empty (no text) or single-chunk (under target).
        if not pieces:
            return
        yield ChunkedPiece(chunk_index=0, text=pieces[0])
        return

    for index, piece in enumerate(pieces):
        yield ChunkedPiece(
            chunk_index=index,
            text=piece,
            extra_metadata={"chunk_index": index, "chunk_count": len(pieces)},
        )
