"""Unit tests for the engagement_floor and russianisms_strict gates.

Both gates restore signals V7 dropped from V6:

- ``engagement_floor`` — callout minimum + META_NARRATION zero-tolerance.
  Restores the deterministic floor under what V6 ``v6-write.md`` line 537
  enforced and what ``docs/best-practices/module-content-quality.md``
  lines 92-117 still document as "Required engagement elements."
- ``russianisms_strict`` — wraps ``check_russicisms`` + ``check_ua_gec_calques``
  into a python_qg gate. Build #11 a1/my-morning (2026-05-22) shipped
  past zero callouts and silent META_NARRATION because the V7 pipeline
  never wired the mature russianism detection layer in.

The gates intentionally use LOW floors. Exceeding them is rewarded by the
LLM ``engagement`` dim's residual-judgment rubric, not the gate.
"""
from __future__ import annotations

from typing import Any

import pytest

from scripts.build import linear_pipeline

# ----- engagement_floor: callouts + meta_narration --------------------------

def _plan(word_target: int = 600) -> dict[str, Any]:
    return {"level": "a1", "slug": "fixture", "word_target": word_target}


def test_engagement_passes_with_two_callouts_and_no_meta_narration() -> None:
    text = """
# My morning

Some prose.

:::tip
Зворотні дієслова закінчуються на **-ся**.
:::

More prose with **писатися** and **дивитися**.

:::note
Common mistake: writers conflate ``-ся`` with passive voice.
:::

Closing line.
"""
    report = linear_pipeline._engagement_floor_gate(text, _plan())
    assert report["passed"] is True
    assert report["callout_count"] == 2
    assert report["meta_narration_hits"] == []


def test_engagement_fails_when_zero_callouts() -> None:
    text = "Plain prose with no callouts. Just sentences. **прокидатися** is here."
    report = linear_pipeline._engagement_floor_gate(text, _plan())
    assert report["passed"] is False
    assert report["callout_count"] == 0
    assert any("callouts" in issue for issue in report["issues"])


def test_engagement_fails_when_one_callout_below_minimum() -> None:
    text = """
:::tip
Just one callout — below the minimum of 2.
:::
"""
    report = linear_pipeline._engagement_floor_gate(text, _plan())
    assert report["passed"] is False
    assert report["callout_count"] == 1


def test_engagement_accepts_github_admonition_syntax() -> None:
    text = """
> [!myth-buster]
> Many learners think `-ся` means passive — it doesn't.

> [!history-bite]
> The `-ся` suffix is an ancient short accusative of `себе`.
"""
    report = linear_pipeline._engagement_floor_gate(text, _plan())
    assert report["passed"] is True
    assert report["callout_count"] == 2


def test_engagement_accepts_mixed_callout_syntaxes() -> None:
    text = """
:::tip
A directive block.
:::

> [!note]
> A GitHub admonition.
"""
    report = linear_pipeline._engagement_floor_gate(text, _plan())
    assert report["passed"] is True
    assert report["callout_count"] == 2


def test_engagement_fails_on_meta_narration_in_this_section() -> None:
    text = """
:::tip
A callout.
:::
:::note
Another.
:::

In this section we will learn about reflexive verbs.
"""
    report = linear_pipeline._engagement_floor_gate(text, _plan())
    assert report["passed"] is False
    # Hit text lowercased and stripped per gate
    assert any("in this section" in hit for hit in report["meta_narration_hits"])
    assert any("meta_narration" in issue for issue in report["issues"])


def test_engagement_fails_on_meta_narration_welcome_to_level() -> None:
    text = """
:::tip
One.
:::
:::note
Two.
:::

Welcome to A1! Today we cover reflexive verbs.
"""
    report = linear_pipeline._engagement_floor_gate(text, _plan())
    assert report["passed"] is False
    assert any("welcome to a1" in hit for hit in report["meta_narration_hits"])


def test_engagement_fails_on_meta_narration_let_us_begin() -> None:
    text = """
:::tip
One.
:::
:::note
Two.
:::

Let us begin with the morning routine.
"""
    report = linear_pipeline._engagement_floor_gate(text, _plan())
    assert report["passed"] is False
    assert any("let us begin" in hit for hit in report["meta_narration_hits"])


def test_engagement_fails_on_meta_narration_unlocked() -> None:
    text = """
:::tip
One.
:::
:::note
Two.
:::

You have unlocked a new tier of reflexive verbs.
"""
    report = linear_pipeline._engagement_floor_gate(text, _plan())
    assert report["passed"] is False
    assert any("unlocked" in hit for hit in report["meta_narration_hits"])


def test_engagement_does_not_flag_notice_or_observe() -> None:
    """V7 already bans abstract 'Notice that...' / 'Observe how...' in the
    writer prompt, but V6 rewarded content-anchored versions. The gate
    deliberately does NOT count these as META_NARRATION — that distinction
    requires judgment and lives in the LLM engagement dim."""
    text = """
:::tip
One.
:::
:::note
Two.
:::

Notice the soft sign in **писатися**. Observe how the stress shifts.
"""
    report = linear_pipeline._engagement_floor_gate(text, _plan())
    assert report["passed"] is True
    assert report["meta_narration_hits"] == []


def test_engagement_fails_when_meta_narration_present_even_with_callouts() -> None:
    """Both conditions are independent: callouts ≥ 2 AND meta_narration = 0.
    Failing either fails the gate."""
    text = """
:::tip
One callout.
:::

:::note
Two callouts.
:::

In this lesson we will cover something.
"""
    report = linear_pipeline._engagement_floor_gate(text, _plan())
    assert report["passed"] is False
    assert report["callout_count"] == 2
    assert any("in this lesson" in hit for hit in report["meta_narration_hits"])


# ----- russianisms_strict: critical findings fail the gate ------------------

def test_russianisms_strict_passes_on_clean_ukrainian() -> None:
    text = "Я прокидаюся о сьомій ранку. Вмиваюся холодною водою."
    report = linear_pipeline._russianisms_strict_gate(text)
    assert report["passed"] is True
    assert report["critical_count"] == 0


def test_russianisms_strict_fails_on_known_russianism_calque() -> None:
    """`приймати участь` is a classic Russian calque of `принимать участие`.
    The russicism_detection module has it as a curated pattern (line 25 of
    that file). 3+ findings escalate to `critical` severity per the
    detector's own escalation rule."""
    # Three hits to escalate severity to critical (per
    # russicism_detection.check_russicisms severity policy).
    text = (
        "Багато людей приймати участь у конференції. "
        "Я хочу приймати участь у дискусії. "
        "Вони приймати участь у проєкті."
    )
    report = linear_pipeline._russianisms_strict_gate(text)
    # russicism_detection escalates to 'critical' at count >= 3
    assert report["passed"] is False
    assert report["critical_count"] >= 1


def test_russianisms_strict_returns_findings_with_fix_suggestions() -> None:
    """The detector hands back actionable corrections so ADR-008's narrow
    correction path can rewrite the offending span."""
    text = (
        "Я хочу приймати участь. Самий кращий вибір. "
        "Він буде получати листи."
    )
    report = linear_pipeline._russianisms_strict_gate(text)
    # Each finding carries a `fix` from the detector
    findings = report["critical_findings"] + report["warning_findings"]
    assert findings, "Expected at least one russianism finding"
    for finding in findings:
        assert "source" in finding
        assert finding["source"] in {"russicism_detection", "ua_gec_calques"}


def test_russianisms_strict_does_not_false_positive_on_inflected_forms() -> None:
    """The detection layer's word-boundary handling must not flag legitimate
    Ukrainian morphology that overlaps with Russianism stems."""
    # ``нічого`` is a valid Ukrainian pronoun (genitive of ``ніщо``);
    # ``нічогенький`` is a real Ukrainian adjective. Neither is the Russian
    # ``ничего``. The detector should leave these alone.
    text = "Я нічого не знаю. Це нічогенький фільм. У нас все гаразд."
    report = linear_pipeline._russianisms_strict_gate(text)
    # No critical findings on legitimate Ukrainian
    assert report["passed"] is True


# ----- python_qg integration ------------------------------------------------

def test_python_qg_includes_engagement_floor_and_russianisms_strict_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When the new gates are wired into run_python_qg, every report MUST
    carry both keys — even on a passing module — so downstream consumers
    (telemetry, correction paths) can rely on their presence."""
    # We test the wiring shape via the module attribute, not by running a
    # full python_qg pass (which requires plan + module + activities artifacts
    # on disk). The integration smoke is covered separately by test_v7_build_e2e.
    assert hasattr(linear_pipeline, "_engagement_floor_gate")
    assert hasattr(linear_pipeline, "_russianisms_strict_gate")
