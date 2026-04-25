import json
import logging
import logging.config
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOGGING_CONFIG = PROJECT_ROOT / "scripts" / "api" / "logging.json"


def _load_logging_config() -> None:
    with LOGGING_CONFIG.open() as handle:
        logging.config.dictConfig(json.load(handle))


def test_access_formatter_handles_uvicorn_access_record() -> None:
    _load_logging_config()
    formatter = logging.getLogger("uvicorn.access").handlers[0].formatter

    record = logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg='%s - "%s %s HTTP/%s" %d',
        args=("127.0.0.1:1234", "GET", "/x", "1.1", 200),
        exc_info=None,
    )

    formatted = formatter.format(record)

    assert '127.0.0.1:1234 "GET /x HTTP/1.1" 200 OK' in formatted


def test_default_formatter_handles_standard_info_record() -> None:
    _load_logging_config()
    formatter = logging.getLogger("uvicorn").handlers[0].formatter

    record = logging.LogRecord(
        name="uvicorn",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="server started",
        args=(),
        exc_info=None,
    )

    formatted = formatter.format(record)

    assert "[INFO] uvicorn: server started" in formatted
