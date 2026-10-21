from __future__ import annotations

from scripts.audit import stamp_textbook_urls as stamp

URL_MAP = {"9-klas-ukrajinska-mova-voron-2017": "https://pidruchnyk.com.ua/1027-ukrmova-voron-9klas.html"}


def test_stamps_url_after_matching_source_ref() -> None:
    text = (
        '- title: "9 клас"\n'
        "  role: textbook\n"
        "  notes: brief\n"
        "  source_ref: docs/references/textbooks-txt/9-klas-ukrajinska-mova-voron-2017.txt\n"
    )
    new, added, unmapped = stamp.stamp_text(text, URL_MAP)
    assert added == 1
    assert not unmapped
    assert '  url: "https://pidruchnyk.com.ua/1027-ukrmova-voron-9klas.html"\n' in new
    assert new.index("url:") > new.index("source_ref:")  # inserted right after source_ref


def test_idempotent_when_url_already_present() -> None:
    text = (
        '- title: "9 клас"\n'
        "  role: textbook\n"
        "  url: https://existing.example/x\n"
        "  source_ref: docs/references/textbooks-txt/9-klas-ukrajinska-mova-voron-2017.txt\n"
    )
    new, added, _ = stamp.stamp_text(text, URL_MAP)
    assert added == 0
    assert new == text


def test_unmapped_stem_is_reported_not_guessed() -> None:
    text = (
        '- title: "unknown"\n'
        "  role: textbook\n"
        "  source_ref: docs/references/textbooks-txt/99-klas-mystery-2099.txt\n"
    )
    new, added, unmapped = stamp.stamp_text(text, URL_MAP)
    assert added == 0
    assert unmapped == ["99-klas-mystery-2099"]
    assert new == text


def test_non_textbook_reference_untouched() -> None:
    text = "- title: t\n  role: article\n  url: https://x.example\n"
    new, added, _ = stamp.stamp_text(text, URL_MAP)
    assert added == 0 and new == text
