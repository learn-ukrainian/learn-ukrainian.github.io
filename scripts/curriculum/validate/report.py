"""The validation report primitives shared by every check module.

Kept import-light (no yaml, no jsonschema) so scope.py, registry.py and
cross.py can build outcomes without importing validate.py, which imports
them. A run has three outcome kinds that never fail it (notes, not_checked,
waivers) and one that does (failures). A waived run — a run that used a
waiver flag such as --allow-missing-prior — is never reported as a clean
pass: the status is "waived", the summary line and --json say so, and the
CLI exit code differs from a clean pass.
"""

from __future__ import annotations

from dataclasses import dataclass, field

VALIDATOR_NOTE = (
    "plan-validate: the §6 gate of docs/epics/fresh-build-plan-schema.md — §2 rules 1–7 "
    "with the semantics of §2a (single-plan and cross-plan). not_checked items are "
    "reported, never passed silently."
)


@dataclass(frozen=True)
class Outcome:
    """One produced outcome: a failure, a note, a not_checked line or a waiver."""

    code: str
    message: str
    lesson: int | None = None
    step: str | None = None

    def render(self) -> str:
        where = ""
        if self.lesson is not None:
            where = f"lesson {self.lesson}"
            if self.step is not None:
                where += f" step {self.step}"
            where += ": "
        return f"{self.code}: {where}{self.message}"


@dataclass
class Report:
    """Everything one validation run produced."""

    level: str
    slug: str
    failures: list[Outcome] = field(default_factory=list)
    notes: list[Outcome] = field(default_factory=list)
    not_checked: list[Outcome] = field(default_factory=list)
    waivers: list[Outcome] = field(default_factory=list)
    #: "final" (evidence_ref.sha256 must equal the pack) or "provisional" (the
    #: comparison is a not_checked pending_promotion item; --provisional-pack).
    mode: str = "final"
    #: Every file the run read, as {repo-relative path: sha256}; the plan-review
    #: manifest refuses a report whose recorded hashes differ from the files.
    inputs: dict[str, str] = field(default_factory=dict)
    #: The plan-stage activity report (issue #8889 r5 §A2; activity_report.plan_report),
    #: empty when the plan could not be loaded far enough to build one.
    activity_report: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.failures

    @property
    def status(self) -> str:
        if self.failures:
            return "fail"
        return "waived" if self.waivers else "pass"

    def codes(self) -> set[str]:
        return {o.code for o in self.failures + self.notes + self.not_checked + self.waivers}

    def to_json(self) -> dict:
        def entries(items: list[Outcome]) -> list[dict]:
            return [{"code": o.code, "lesson": o.lesson, "step": o.step, "message": o.message} for o in items]

        return {
            "validator": VALIDATOR_NOTE,
            "level": self.level,
            "slug": self.slug,
            "status": self.status,
            "mode": self.mode,
            "inputs": dict(sorted(self.inputs.items())),
            "failures": entries(self.failures),
            "notes": entries(self.notes),
            "not_checked": entries(self.not_checked),
            "waivers": entries(self.waivers),
            "activity_report": self.activity_report,
        }

    def render_text(self) -> str:
        lines = [VALIDATOR_NOTE, f"plan: {self.level}/{self.slug}", f"status: {self.status}"]
        if self.mode != "final":
            lines.append(f"mode: {self.mode}")
        lines += [f"FAIL {o.render()}" for o in self.failures]
        lines += [f"NOTE {o.render()}" for o in self.notes]
        lines += [f"NOT_CHECKED {o.render()}" for o in self.not_checked]
        lines += [f"waived: {o.code} ({o.message})" for o in self.waivers]
        if self.activity_report:
            stage = self.activity_report.get("stage", "plan")
            module = self.activity_report.get("module", {})
            lines.append(
                f"activity_report ({stage} stage) module: "
                f"workbook_activities={module.get('workbook_activities')} "
                f"inline_activities={module.get('inline_activities')} "
                f"workbook_presence_complete={module.get('workbook_presence_complete')} "
                f"largest_workbook_type_share={module.get('largest_workbook_type_share')} "
                f"longest_same_type_workbook_run={module.get('longest_same_type_workbook_run')}"
            )
            for lesson in self.activity_report.get("lessons", []):
                lines.append(f"activity_report ({stage} stage) lesson {lesson.get('n')}: {_render_lesson(lesson)}")
        return "\n".join(lines)


def _render_lesson(lesson: dict) -> str:
    """One lesson's activity-report fields, whichever stage produced them
    (plan_report, draft_report or rendered_report — issue #8889 r5 §A2)."""
    parts = []
    if "kind" in lesson:
        parts.append(f"kind={lesson['kind']}")
    activities = lesson.get("activities")
    if isinstance(activities, dict):
        parts.append(f"inline={activities.get('inline', {}).get('total')}")
        parts.append(f"workbook={activities.get('workbook', {}).get('total')}")
    if "distinct_types" in lesson:
        parts.append(f"distinct_types={','.join(lesson['distinct_types'])}")
    if "has_workbook" in lesson:
        parts.append(f"has_workbook={lesson['has_workbook']}")
    if "response_opportunities" in lesson:
        parts.append(f"response_opportunities={lesson['response_opportunities']}")
    if "explanation_coverage" in lesson:
        parts.append(f"explanation_coverage={lesson['explanation_coverage']}")
    if "planned_workbook" in lesson:
        parts.append(f"planned_workbook={lesson['planned_workbook']}")
    if "rendered_and_playable" in lesson:
        parts.append(f"rendered_and_playable={lesson['rendered_and_playable']}")
    return " ".join(parts)
