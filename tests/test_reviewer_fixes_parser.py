from __future__ import annotations

from scripts.build.linear_pipeline import _parse_reviewer_fixes


def test_reviewer_fixes_parser_handles_markdown_in_xml_content_nodes() -> None:
    review = (
        "<fixes>\n"
        "  <fix>\n"
        "    <find>вмива́ю**ся**</find>\n"
        "    <replace>вмиваюся</replace>\n"
        "  </fix>\n"
        "</fixes>"
    )

    fixes = _parse_reviewer_fixes(review)

    assert fixes == [{"find": "вмива́ю**ся**", "replace": "вмиваюся"}]


def test_reviewer_fixes_parser_handles_multiple_markdown_xml_pairs() -> None:
    review = (
        "<fixes>\n"
        "  <fix><find>*ранок*</find><replace>ранок</replace></fix>\n"
        "  <fix><find>**кава**</find><replace>кава</replace></fix>\n"
        "  <fix><find>`дім`</find><replace>дім</replace></fix>\n"
        "</fixes>"
    )

    fixes = _parse_reviewer_fixes(review)

    assert fixes == [
        {"find": "*ранок*", "replace": "ранок"},
        {"find": "**кава**", "replace": "кава"},
        {"find": "`дім`", "replace": "дім"},
    ]


def test_reviewer_fixes_parser_allows_empty_xml_replace() -> None:
    review = "<fixes><fix><find>зайве</find><replace></replace></fix></fixes>"

    fixes = _parse_reviewer_fixes(review)

    assert fixes == [{"find": "зайве", "replace": ""}]


def test_reviewer_fixes_parser_invalid_raw_xml_text_does_not_crash() -> None:
    review = "<fixes><fix><find>2 < 3</find><replace>2 &lt; 3</replace></fix></fixes>"

    fixes = _parse_reviewer_fixes(review)

    assert fixes == []


def test_reviewer_fixes_parser_keeps_yaml_fallback() -> None:
    review = (
        "<fixes>\n"
        "- find: Старий текст\n"
        "  replace: Новий текст\n"
        "</fixes>"
    )

    fixes = _parse_reviewer_fixes(review)

    assert fixes == [{"find": "Старий текст", "replace": "Новий текст"}]
