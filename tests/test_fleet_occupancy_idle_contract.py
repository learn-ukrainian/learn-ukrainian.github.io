"""UI contract: unavailable occupancy hosts render unknown, never idle (#7139)."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FLEET_HTML = ROOT / "dashboards" / "fleet.html"


def _idle_state_expression(html: str) -> str:
    match = re.search(r"const idleState = (?P<expr>[^;]+);", html)
    assert match is not None, "renderOccupancy must derive an idleState label"
    return match.group("expr").strip()


def test_unavailable_host_burn_pill_is_unknown_never_idle() -> None:
    html = FLEET_HTML.read_text(encoding="utf-8")
    expr = _idle_state_expression(html)

    # New payloads win; the legacy status + idle_or_empty expression remains the fallback.
    assert expr.startswith("host.burn_state ||"), expr
    assert "host.status === 'unavailable' ? 'unknown' :" in expr

    # 'idle' is only reachable in the non-unavailable fallback branch.
    fallback = expr.split("||", 1)[1]
    assert "'idle'" in fallback
    assert "idle_or_empty" in fallback

    # The unavailable branch never produces an idle label.
    unavailable_branch = expr.split("host.status === 'unavailable' ?", 1)[1].split(":", 1)[0]
    assert "'idle'" not in unavailable_branch
    assert unavailable_branch.strip() == "'unknown'"

    # Both occupancy row templates actually render the derived label as a pill.
    assert html.count("pill(idleState)") >= 2
    assert "Object.entries(objectValue(host.burn_sources))" in html
    assert "['active', 'clear', 'unknown'].includes(detail.state)" in html

    # Utilization metrics stay hidden for unavailable hosts.
    assert "if (host.status !== 'unavailable') {" in html
