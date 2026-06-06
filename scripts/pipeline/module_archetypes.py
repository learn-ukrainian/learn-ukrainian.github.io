"""Module archetype contract resolver.

The learner state tells the writer what the learner already knows. The module
archetype tells the writer what kind of lesson it is allowed to write.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

SEMINAR_TRACKS = {
    "bio",
    "hist",
    "istorio",
    "lit",
    "lit-crimea",
    "lit-doc",
    "lit-drama",
    "lit-essay",
    "lit-fantastika",
    "lit-hist-fic",
    "lit-humor",
    "lit-war",
    "lit-youth",
    "oes",
    "ruth",
}

CORE_TRACKS = {"a1", "a2", "b1", "b2", "c1", "c2"}

DEFAULT_TAB_CONTRACT = {
    "product_tabs": ["Lesson", "Workbook", "Vocabulary", "Resources"],
    "starlight_current_tabs": ["Lesson", "Vocabulary", "Activities", "Resources"],
    "resource_policy": (
        "Required resources appear at the point of use and are also listed "
        "canonically in Resources. Internal AI-facing wiki pages are not "
        "student-facing resources."
    ),
}

MODULE_ARCHETYPES: dict[str, dict[str, Any]] = {
    "a1-zero-script-onboarding": {
        "label": "A1 zero-script onboarding",
        "scope": "A1 M01 only",
        "teaching_language": "English-led; Ukrainian appears in tiny controlled chunks.",
        "learner_assumptions": [
            "Learner may know zero Cyrillic.",
            "No Ukrainian grammar metalanguage can be assumed.",
            "Every Ukrainian term used in an activity must be introduced first.",
        ],
        "must_introduce_before_use": True,
        "tab_contract": DEFAULT_TAB_CONTRACT,
        "activity_families": [
            "watch-and-repeat",
            "letter recognition",
            "sound classification",
            "matching",
            "tiny phrase recall",
            "workbook review",
        ],
        "review_gates": [
            "plan coverage",
            "required resource coverage",
            "introduced-before-use",
            "no internal wiki links",
            "zero-learner readability",
        ],
        "golden_reference": "A1 M01 sounds-letters-and-hello",
    },
    "a1-script-building": {
        "label": "A1 script-building",
        "scope": "A1 M02-M04",
        "teaching_language": "English-led with Ukrainian-first micro examples.",
        "learner_assumptions": [
            "Learner has seen the alphabet map but cannot read fluently.",
            "Ukrainian examples must remain decodable or immediately glossed.",
            "Sound, stress, and spelling concepts require explicit setup.",
        ],
        "must_introduce_before_use": True,
        "tab_contract": DEFAULT_TAB_CONTRACT,
        "activity_families": [
            "watch-and-repeat",
            "letter-sound mapping",
            "stress listening",
            "sorting",
            "matching",
            "short workbook checks",
        ],
        "review_gates": [
            "ULP ramp fidelity",
            "introduced-before-use",
            "decodable examples",
            "required media at point of use",
        ],
    },
    "a1-first-contact-survival": {
        "label": "A1 first-contact survival",
        "scope": "A1 M05-M07",
        "teaching_language": "English-led; short Ukrainian dialogue artifacts first, breakdown after.",
        "learner_assumptions": [
            "Learner can recognize some letters and memorized phrases.",
            "Grammar is chunked, not explained as paradigms.",
            "Dialogues must be short and immediately reusable.",
        ],
        "must_introduce_before_use": True,
        "tab_contract": DEFAULT_TAB_CONTRACT,
        "activity_families": [
            "dialogue recognition",
            "phrase matching",
            "listen-and-choose",
            "tiny production",
            "checkpoint review",
        ],
        "review_gates": [
            "dialogue before explanation",
            "phrase introduced before activity",
            "checkpoint covers M01-M06",
        ],
    },
    "a1-grammar-first-contact": {
        "label": "A1 grammar first contact",
        "scope": "A1 M08-M24",
        "teaching_language": "English-led explanations with Ukrainian pattern boxes and examples.",
        "learner_assumptions": [
            "Learner can read controlled Ukrainian words and short phrases.",
            "New grammar requires English explanation and tightly bounded examples.",
            "Do not re-explain known grammar beyond a brief reminder.",
        ],
        "must_introduce_before_use": True,
        "tab_contract": DEFAULT_TAB_CONTRACT,
        "activity_families": [
            "pattern recognition",
            "fill-in",
            "match-up",
            "select",
            "guided production",
            "workbook spiral review",
        ],
        "review_gates": [
            "known-grammar reuse",
            "new grammar scoped to plan",
            "A1 sentence-length constraints",
        ],
    },
    "a1-a2-expansion-ramp": {
        "label": "A1/A2 expansion ramp",
        "scope": "late A1 and A2",
        "teaching_language": "ULP-style ramp: Ukrainian-first artifacts with English scaffold receding.",
        "learner_assumptions": [
            "Learner can read controlled Ukrainian.",
            "English support recedes as cumulative vocabulary grows.",
            "Narrative and dialogue length can increase only with learner state.",
        ],
        "must_introduce_before_use": True,
        "tab_contract": DEFAULT_TAB_CONTRACT,
        "activity_families": [
            "dialogue",
            "reading",
            "grammar transformation",
            "cloze",
            "short writing",
            "spiral review",
        ],
        "review_gates": [
            "ULP-derived immersion band",
            "unknown vocabulary gate",
            "resource coverage",
        ],
    },
    "b1-plus-core": {
        "label": "B1+ core module",
        "scope": "B1-C2 core tracks",
        "teaching_language": "Ukrainian-only body; English only in Vocabulary translations.",
        "learner_assumptions": [
            "Learner can read Ukrainian lesson prose.",
            "The module should build from known grammar instead of restarting.",
            "Vocabulary tab may use English for anchoring only.",
        ],
        "must_introduce_before_use": True,
        "tab_contract": DEFAULT_TAB_CONTRACT,
        "activity_families": [
            "grammar analysis",
            "error correction",
            "cloze",
            "essay response",
            "reading",
            "register comparison",
        ],
        "review_gates": [
            "100 percent Ukrainian outside Vocabulary",
            "known-grammar reuse",
            "corpus/source grounding",
        ],
    },
    "seminar-source-analysis": {
        "label": "Seminar source analysis",
        "scope": "BIO, HIST, LIT, OES, RUTH, ISTORIO and seminar variants",
        "teaching_language": "Ukrainian academic prose.",
        "learner_assumptions": [
            "Learner is ready for source-based analytical work.",
            "Lesson body centers sources, context, and argumentation.",
            "Activities are seminar tasks, not beginner drills.",
        ],
        "must_introduce_before_use": True,
        "tab_contract": DEFAULT_TAB_CONTRACT,
        "activity_families": [
            "source-evaluation",
            "critical-analysis",
            "essay-response",
            "comparative-study",
            "authorial-intent",
            "debate",
            "etymology-trace",
            "transcription",
            "paleography-analysis",
            "dialect-comparison",
        ],
        "review_gates": [
            "source provenance",
            "decolonization/bias check",
            "seminar activity family",
            "no shallow summary",
        ],
    },
    "folk-experiential": {
        "label": "Folk experiential",
        "scope": "FOLK track modules",
        "teaching_language": "Ukrainian C1+ cultural prose with corpus-grounded explanation.",
        "learner_assumptions": [
            "Learner can read extended Ukrainian academic prose.",
            "Folk culture is aural, performative, symbolic, and material, not only textual.",
            "Lesson prose must be rich enough to stand on its own before activities.",
            "Activities may use recordings, images, ritual sequences, variants, formulas, and performance tasks.",
        ],
        "must_introduce_before_use": True,
        "tab_contract": DEFAULT_TAB_CONTRACT,
        "lesson_blocks": [
            "audio-block: pair a named recording with a verify_quote-confirmed text when dossier sources support audio",
            "symbolic-decode: use dossier image chunk_ids and clickable hotspots to decode motifs or symbols",
            "high-culture bridge: connect the folk form to opera, literature, art, or modern cultural circulation",
            "myth-box: correct imperial, Soviet, or romantic-nationalist myths with dossier-grounded evidence",
        ],
        "activity_families": [
            "#40 Aural Genre-ID",
            "#41 Symbolic Decoding",
            "#42 Ritual Sequencing",
            "#43 Variant Comparison",
            "#44 Motif / Formula",
            "#45 Performance",
        ],
        "review_gates": [
            "4-tab shell intact and no tab empty",
            "audio/symbolic-decode/high-culture bridge used where dossier evidence supports them",
            "at least one decolonization myth-box",
            "rich corpus-grounded Ukrainian lesson prose",
            "folk activity families #40-#45 instead of generic seminar-only tasks",
            "Resources are dossier-derived; no YouTube resources",
        ],
    },
}


def resolve_module_archetype(track: str, module_num: int) -> dict[str, Any]:
    """Return the archetype contract for a track/module position."""
    normalized_track = track.lower()

    if normalized_track == "a1":
        if module_num == 1:
            archetype_id = "a1-zero-script-onboarding"
        elif 2 <= module_num <= 4:
            archetype_id = "a1-script-building"
        elif 5 <= module_num <= 7:
            archetype_id = "a1-first-contact-survival"
        elif 8 <= module_num <= 24:
            archetype_id = "a1-grammar-first-contact"
        else:
            archetype_id = "a1-a2-expansion-ramp"
    elif normalized_track == "a2":
        archetype_id = "a1-a2-expansion-ramp"
    elif normalized_track in CORE_TRACKS:
        archetype_id = "b1-plus-core"
    elif normalized_track == "folk":
        archetype_id = "folk-experiential"
    elif normalized_track in SEMINAR_TRACKS:
        archetype_id = "seminar-source-analysis"
    else:
        archetype_id = "seminar-source-analysis"

    contract = deepcopy(MODULE_ARCHETYPES[archetype_id])
    contract["id"] = archetype_id
    contract["track"] = normalized_track
    contract["module_num"] = module_num
    return contract


def format_module_archetype(contract: dict[str, Any]) -> str:
    """Format an archetype contract for prompt injection."""
    lines = [
        f"MODULE ARCHETYPE: {contract['id']} — {contract['label']}",
        f"Scope: {contract['scope']}",
        f"Teaching language: {contract['teaching_language']}",
        "",
        "Learner assumptions:",
    ]
    lines.extend(f"- {item}" for item in contract["learner_assumptions"])
    lines.extend([
        "",
        "Required tab surface:",
        "- Product tabs: " + ", ".join(contract["tab_contract"]["product_tabs"]),
        "- Current Starlight tabs: " + ", ".join(contract["tab_contract"]["starlight_current_tabs"]),
        "- Resource policy: " + contract["tab_contract"]["resource_policy"],
    ])
    if lesson_blocks := contract.get("lesson_blocks"):
        lines.extend(["", "Required lesson blocks:"])
        lines.extend(f"- {item}" for item in lesson_blocks)
    lines.extend([
        "",
        "Allowed activity families:",
    ])
    lines.extend(f"- {item}" for item in contract["activity_families"])
    lines.extend(["", "Review gates:"])
    lines.extend(f"- {item}" for item in contract["review_gates"])
    return "\n".join(lines)
