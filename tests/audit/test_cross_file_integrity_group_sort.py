from scripts.audit.checks.cross_file_integrity import _extract_text_from_activity


def test_group_sort_mapping_groups_contribute_activity_text() -> None:
    texts = _extract_text_from_activity(
        {
            "type": "group-sort",
            "title": "Вид дієслова",
            "groups": {
                "Доконаний вид": ["написати", "прочитати"],
                "Недоконаний вид": ["писати", "читати"],
            },
        }
    )

    assert "Доконаний вид" in texts
    assert "написати" in texts
    assert "Недоконаний вид" in texts
    assert "читати" in texts
