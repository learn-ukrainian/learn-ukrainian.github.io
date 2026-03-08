"""Shared constants for the batch Gemini runner package."""

import logging
import shutil

from batch_gemini_config import PROJECT_ROOT

# Gemini binary location
GEMINI_BIN = shutil.which("gemini") or "/opt/homebrew/bin/gemini"

# Paths
AUDIT_SCRIPT = PROJECT_ROOT / "scripts" / "audit_module.sh"
FAILURES_DIR = PROJECT_ROOT / "batch_state" / "failures"
API_USAGE_DIR = PROJECT_ROOT / "batch_state" / "api_usage"
LOCK_DIR = PROJECT_ROOT / "batch_state" / "locks"

# Retry / timeout settings
MAX_RETRIES = 3
MAX_FIX_ITERATIONS = 8
TIMEOUT_SECONDS = 900  # 15 minutes
QUOTA_RETRY_WAIT_SECONDS = 90
QUOTA_MAX_RETRIES = 2  # retries before switching account

# Logger
log = logging.getLogger("batch")
