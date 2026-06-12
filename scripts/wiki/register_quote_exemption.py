"""Quote-boundary helpers for the wiki register reviewer contract."""

from __future__ import annotations

import re
from dataclasses import dataclass

_SHORT_SOURCE_RE = re.compile(r"\[S[1-9]\d*\]")
_CHUNK_ID_RE = re.compile(r"(?<![0-9A-Za-z_-])[0-9A-Za-z][0-9A-Za-z_-]*_c\d{4,}(?![0-9A-Za-z_-])")
_NO_VERIFY_RE = re.compile(r"<!--\s*NO_VERIFY:", re.IGNORECASE)
_DASH_ATTRIBUTION_RE = re.compile(r"(?m)^\s*(?:>\s*)?[*_`~ ]*[—–-]\s*\S+")
_NAMED_SOURCE_RE = re.compile(
    r"\b(?:ЕУ|ЕСУ|УРЕ)\b|Енциклопеді\w+|Білецьк\w+|Чижевськ\w+|Попович\w+|"
    r"Грушевськ\w+|Франк\w+|Драгоманов\w+|Костомаров\w+",
    re.IGNORECASE,
)
_GUILLEMET_RE = re.compile(r"«[^»]+»", re.DOTALL)
_BLOCKQUOTE_BLOCK_RE = re.compile(r"(?m)(?:^>[^\n]*(?:\n|$))+")


@dataclass(frozen=True)
class RegisterQuoteSpan:
    """A quote span the register reviewer should treat as source-preserved."""

    start: int
    end: int
    quote_text: str
    attribution_context: str


def find_attributed_verbatim_quote_spans(text: str) -> list[RegisterQuoteSpan]:
    """Return attributed verbatim quote spans that are exempt from register findings."""
    spans: list[RegisterQuoteSpan] = []
    spans.extend(_find_attributed_blockquote_spans(text))
    spans.extend(_find_attributed_guillemet_spans(text))
    return sorted(spans, key=lambda span: span.start)


def has_quote_attribution(context: str) -> bool:
    """Return whether quote-adjacent text carries a usable source attribution."""
    if not context.strip() or _NO_VERIFY_RE.search(context):
        return False
    return bool(
        _SHORT_SOURCE_RE.search(context)
        or _CHUNK_ID_RE.search(context)
        or _DASH_ATTRIBUTION_RE.search(context)
        or _NAMED_SOURCE_RE.search(context)
    )


def _find_attributed_guillemet_spans(text: str) -> list[RegisterQuoteSpan]:
    spans: list[RegisterQuoteSpan] = []
    for match in _GUILLEMET_RE.finditer(text):
        context = _quote_paragraph_context(text, match.start(), match.end())
        if has_quote_attribution(context):
            spans.append(
                RegisterQuoteSpan(
                    start=match.start(),
                    end=match.end(),
                    quote_text=match.group(0),
                    attribution_context=context.strip(),
                )
            )
    return spans


def _find_attributed_blockquote_spans(text: str) -> list[RegisterQuoteSpan]:
    spans: list[RegisterQuoteSpan] = []
    for match in _BLOCKQUOTE_BLOCK_RE.finditer(text):
        block = match.group(0)
        if block.lstrip().startswith("> [!"):
            continue
        context = _blockquote_context(text, match.start(), match.end())
        if has_quote_attribution(context):
            spans.append(
                RegisterQuoteSpan(
                    start=match.start(),
                    end=match.end(),
                    quote_text=_strip_blockquote_prefix(block),
                    attribution_context=context.strip(),
                )
            )
    return spans


def _quote_paragraph_context(text: str, start: int, end: int) -> str:
    paragraph_start = text.rfind("\n\n", 0, start)
    if paragraph_start == -1:
        paragraph_start = max(0, start - 240)
    else:
        # Check if the paragraph starts very close to the quote.
        # If so, look back to the preceding paragraph to catch preceding attributions.
        if start - (paragraph_start + 2) < 16:
            second_prev = text.rfind("\n\n", 0, paragraph_start)
            paragraph_start = second_prev + 2 if second_prev != -1 else 0
        else:
            paragraph_start += 2

    paragraph_end = text.find("\n\n", end)
    if paragraph_end == -1:
        paragraph_end = min(len(text), end + 240)
    return text[paragraph_start:paragraph_end]


def _blockquote_context(text: str, start: int, end: int) -> str:
    context_start = text.rfind("\n\n", 0, start)
    if context_start == -1 or start - context_start < 240:
        # Look back further (e.g. 240 chars) to catch the preceding paragraph.
        context_start = max(0, start - 240)
        boundary = text.rfind("\n\n", 0, context_start)
        context_start = boundary + 2 if boundary != -1 else 0
    else:
        context_start += 2
    return text[context_start:min(len(text), end + 320)]


def _strip_blockquote_prefix(block: str) -> str:
    lines = []
    for line in block.splitlines():
        lines.append(re.sub(r"^\s*>\s?", "", line))
    return "\n".join(lines).strip()
