"""A1 choice feedback follows the option order emitted for the page."""

import json

from scripts.build.fresh.assemble import page_field_text
from scripts.yaml_activities import ActivityParser


def test_image_to_letter_feedback_follows_page_option_order() -> None:
    parser = ActivityParser()
    activity = parser._parse_activity(
        {
            "type": "image-to-letter",
            "items": [
                {
                    "image": "🍎",
                    "letter": "B",
                    "options": ["A", "B", "C"],
                    "kind": "vocabulary",
                    "option_why": ["A is wrong", "B is right", "C is wrong"],
                    "option_records": ["W-1", "W-2", "W-3"],
                    "target_record": "W-2",
                }
            ],
        }
    )
    item = activity.items[0]
    assert [item.answer, *item.distractors] == ["B", "A", "C"]
    assert item.option_why == ["B is right", "A is wrong", "C is wrong"]
    assert item.option_records == ["W-2", "W-1", "W-3"]
    mdx = parser.to_mdx([activity])
    assert json.dumps(item.option_why) in mdx
    assert json.dumps(item.option_records) in mdx
    page_props = {"items": [{"answer": item.answer, "distractors": item.distractors, "option_why": item.option_why}]}
    for authored_index, feedback in enumerate(("A is wrong", "B is right", "C is wrong")):
        assert (
            page_field_text("image-to-letter", page_props, 0, f"option_why_{authored_index}", key_index=1) == feedback
        )
