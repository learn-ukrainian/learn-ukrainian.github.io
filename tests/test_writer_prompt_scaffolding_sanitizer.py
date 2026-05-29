from __future__ import annotations

import copy

from scripts.build.phases.implementation_map import render_for_writer_prompt


def _payload_with_scaffolding() -> dict:
    return {
        "schema_version": 1,
        "slug": "my-morning",
        "wiki_path": "wiki/pedagogy/a1/my-morning.md",
        "manifest_obligation_count": 1,
        "entries": [
            {
                "obligation_id": "step-1",
                "obligation_type": "sequence_step",
                "artifact": "module.md",
                "location_hint": "Крок 4: §Дієслова на -ся [S7]",
                "treatment_template": {
                    "shape": "prose explanation",
                    "required_claim": "Крок 1: Ознайомлення... [S8] ... [S6, S8]",
                    "nested": {
                        "instruction": "Step 2: use прокидатися [S3]",
                        "summary": "A reflexive verb adds -ся. Крок 5: practice дивитися [S7]",
                        "spaced_marker": "Use умиватися [S1 , S2]",
                        "items": ["Урок 3: reinforce одягатися [С4]"],
                    },
                },
                "manifest_payload": {"id": "step-1"},
            }
        ],
    }


def test_render_for_writer_prompt_strips_scaffolding_without_mutating_payload() -> None:
    payload = _payload_with_scaffolding()
    original = copy.deepcopy(payload)

    rendered = render_for_writer_prompt(payload)

    assert payload == original
    assert "Крок 1:" not in rendered
    assert "Крок 4:" not in rendered
    assert "Крок 5:" not in rendered
    assert "Step 2:" not in rendered
    assert "Урок 3:" not in rendered
    assert "[S8]" not in rendered
    assert "[S6, S8]" not in rendered
    assert "[S7]" not in rendered
    assert "[S3]" not in rendered
    assert "[S1 , S2]" not in rendered
    assert "[С4]" not in rendered
    assert "Ознайомлення" in rendered
    assert "A reflexive verb adds -ся. practice дивитися" in rendered
    assert "§Дієслова на -ся" in rendered
