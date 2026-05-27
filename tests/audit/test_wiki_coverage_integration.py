from __future__ import annotations

from typing import Any

from scripts.audit.wiki_coverage_gate import check_wiki_coverage


def _sequence_step_manifest() -> dict[str, Any]:
    return {
        "slug": "my-morning",
        "wiki_path": "wiki/grammar/a1/my-morning.md",
        "sequence_steps": [
            {
                "id": "step-4",
                "required_claim": "Крок 4: Відмінювання дієслова `дивлюся` [S3].",
                "source_lines": "25",
            },
            {
                "id": "step-5",
                "required_claim": (
                    "Крок 5: Розширення лексичного контексту. "
                    "Тема ранкової рутини наповнюється іменниками "
                    "(вода, зарядка, сніданок) та прислівниками "
                    "часу і частотності (раненько, швиденько, завжди, ніколи) [S7]."
                ),
                "source_lines": "31",
            }
        ],
        "l2_errors": [],
        "phonetic_rules": [],
        "decolonization_bans": [],
    }

def test_wiki_coverage_integration_m20_scenario():
    """Verify that the gate correctly handles the m20 drift scenario.

    - step-4: Writer included 'дивлюся' but not the label 'Крок 4'. Should PASS.
    - step-5: Writer included 'сніданок' but missing others. Should FAIL with specific missing items.
    """
    manifest = _sequence_step_manifest()

    # Module text mimicking the writer's output (clean, no scaffolding)
    module_md = """
# Мій ранок

Я прокидаюся і **дивлюся** у вікно. Потім я готую **сніданок**.
Це мій ранок.
"""

    implementation_map = {
        "step-4": {
            "artifact": "module.md",
            "location": "whole file",
            "treatment": "conjugation",
        },
        "step-5": {
            "artifact": "module.md",
            "location": "whole file",
            "treatment": "vocabulary expansion",
        }
    }

    report = check_wiki_coverage(
        manifest=manifest,
        implementation_map=implementation_map,
        module_md=module_md,
        activities_yaml="[]",
    )

    results = {item["obligation_id"]: item for item in report["obligations"]}

    # Assert step-4 passes because 'дивлюся' is present (even without 'Крок 4')
    assert results["step-4"]["status"] == "PASS"

    # Assert step-5 fails because of missing items
    assert results["step-5"]["status"] == "FAIL"
    reason = results["step-5"]["reason"]
    assert "sequence_claim_missing" in reason
    # It should report exactly what is missing
    assert "вода" in reason
    assert "зарядка" in reason
    assert "раненько" in reason
    assert "швиденько" in reason
    assert "завжди" in reason
    assert "ніколи" in reason
    # But 'сніданок' should NOT be in the missing list
    assert "сніданок" not in reason

def test_wiki_coverage_integration_l2_error():
    """Verify l2_error also passes via direct item matching."""
    manifest = {
        "l2_errors": [
            {
                "id": "err-1",
                "incorrect": "Вимова: [одягайет'с'а]",
                "correct": "Вимова: [одягайец':а]",
                "why": "assimilation",
                "treatment": "contrast_pair",
            }
        ]
    }

    # In activities.yaml, item-level
    activities_yaml = """
- id: act-1
  type: error-correction
  items:
    - sentence: "Я одягаюся."
      error: "Вимова: [одягайет'с'а]"
      correction: "Вимова: [одягайец':а]"
"""

    implementation_map = {
        "err-1": {
            "artifact": "activities.yaml",
            "location": "act-1",
            "treatment": "contrast_pair",
        }
    }

    report = check_wiki_coverage(
        manifest=manifest,
        implementation_map=implementation_map,
        module_md="",
        activities_yaml=activities_yaml,
    )

    assert report["obligations"][0]["status"] == "PASS"
