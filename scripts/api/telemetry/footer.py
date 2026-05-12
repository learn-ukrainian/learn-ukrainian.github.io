"""Pure renderer for context-window telemetry footers."""


PREMIUM_THRESHOLD_TOKENS = 200_000


def render_footer(*, tokens: int, prev_tokens: int | None, turn: int | None) -> str:
    """Render the [ctx: ...] footer line. Pure; no I/O."""
    delta = f" (+{(tokens - prev_tokens) // 1000}K this turn)" if prev_tokens is not None else ""
    tier = "premium" if tokens > PREMIUM_THRESHOLD_TOKENS else "base"
    distance = (
        (PREMIUM_THRESHOLD_TOKENS - tokens) // 1000
        if tier == "base"
        else (tokens - PREMIUM_THRESHOLD_TOKENS) // 1000
    )
    distance_str = f", {distance}K {'to premium' if tier == 'base' else 'over premium'}"
    turn_str = f", turn: {turn}" if turn is not None else ""
    return f"[ctx: {tokens // 1000}K{delta}, tier: {tier}{distance_str}{turn_str}]"
