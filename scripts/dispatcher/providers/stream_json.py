"""One stream-json model observer, shared by every provider that attests from its own stdout."""


def model_observer(stdout_path, extract):
    """Attest one model from complete stream-json lines, under the exactly-one rule.

    ``extract(event)`` returns the model strings that event reports. No string attests
    nothing, and more than one distinct string across the stream attests nothing.
    Settlement re-derives the model from the whole stream and overwrites this value.
    """
    offset, pending, models = 0, b"", set()

    def observed():
        nonlocal offset, pending
        with stdout_path.open("rb") as stream:
            stream.seek(offset)
            chunk = stream.read()
            offset = stream.tell()
        lines = (pending + chunk).split(b"\n")
        pending = lines.pop()
        for line in lines:
            try:
                reported = extract(json_event(line))
            except ValueError:  # invalid JSON or invalid UTF-8: not a valid record, so it attests nothing
                continue
            models.update(reported)
        return next(iter(models)) if len(models) == 1 else None

    return observed


def json_event(line: bytes):
    import json

    return json.loads(line.decode())


def one_model(models: set[str]) -> str | None:
    """The single reported model, or None when the stream reported none or several."""
    return next(iter(models)) if len(models) == 1 else None
