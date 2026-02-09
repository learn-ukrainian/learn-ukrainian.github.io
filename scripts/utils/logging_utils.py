import logging
import json
import sys
from datetime import datetime, timezone

class JsonFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    def format(self, record):
        log_obj = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "func": record.funcName,
            "line": record.lineno
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

def setup_logging(name=None, level=logging.INFO):
    """Setup logging with support for --json-log flag."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Check if --json-log is in sys.argv
    use_json = "--json-log" in sys.argv

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    if use_json:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    logger.addHandler(handler)
    return logger
