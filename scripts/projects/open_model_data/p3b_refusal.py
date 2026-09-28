"""Explicit refusal for deferred historical open-model-data regeneration."""


class HistoricalProducerDeferredError(RuntimeError):
    """A historical producer cannot publish its managed A/K output set yet."""


def refuse_historical_regeneration(producer: str) -> None:
    """Refuse before a deferred producer attempts any output mutation."""
    raise HistoricalProducerDeferredError(
        f"P3b deferred historical regeneration: {producer}; managed outputs require staged publish-set support (#8809)."
    )
