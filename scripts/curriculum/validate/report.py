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
        }

    def render_text(self) -> str:
        lines = [VALIDATOR_NOTE, f"plan: {self.level}/{self.slug}", f"status: {self.status}"]
        if self.mode != "final":
            lines.append(f"mode: {self.mode}")
        lines += [f"FAIL {o.render()}" for o in self.failures]
        lines += [f"NOTE {o.render()}" for o in self.notes]
        lines += [f"NOT_CHECKED {o.render()}" for o in self.not_checked]
        lines += [f"waived: {o.code} ({o.message})" for o in self.waivers]
        return "\n".join(lines)
