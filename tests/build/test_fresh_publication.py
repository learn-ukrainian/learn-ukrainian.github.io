"""Rendered quote rights, verbatim excerpt, and visible attribution regressions."""

import pytest

from scripts.build.fresh.assemble import AssemblerError, _render_urok_markdown
from scripts.curriculum.evidence import publication

BOOK = "1-klas-bukvar-zaharijchuk-2025-1"


def render_quote(file=BOOK, quote="Synthetic exact excerpt", page=39):
    draft = {"steps": [{"id": "s1", "blocks": [{"kind": "quote", "ref": "T-001"}]}]}
    record = {"id": "T-001", "quote": quote, "source": {"kind": "textbook", "file": file, "page": page}}
    stressed = {"units": [{"tab": "urok", "step": "s1", "block": 0, "role": "record_print", "text": quote}]}
    return _render_urok_markdown(draft, stressed, {"texts": [record]}, {"words": []})


def test_rendered_quote_is_verbatim_and_attributed():
    quote = "Synthetic exact excerpt —  preserve  spacing!"
    markdown, units = render_quote(quote=quote)
    entry = publication.load_registry()[BOOK]
    assert f"> {quote}\n>\n> — *{entry['author']}, {BOOK}, grade 1, 2025, page 39*" in markdown
    assert units.texts()[0] == quote


@pytest.mark.parametrize(
    "file,quote,page,code",
    [
        ("ulp-1-00-lesson-notes", "Synthetic excerpt", 39, "publication_right"),
        ("not-registered", "Synthetic excerpt", 39, "publication_right"),
        (BOOK, "x" * 801, 39, "publication_limit"),
        (BOOK, "Synthetic excerpt", None, "publication_attribution"),
    ],
)
def test_renderer_cannot_bypass_quote_admission(file, quote, page, code):
    with pytest.raises(AssemblerError) as caught:
        render_quote(file, quote, page)
    assert caught.value.code == code
