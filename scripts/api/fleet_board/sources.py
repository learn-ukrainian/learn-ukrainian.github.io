"""Source status for the fleet board.

Location settings come from ``FLEET_*`` variables. An unset or blank value is
``not_configured``. Nothing here supplies a location. A failed check is
``unavailable`` and does not raise to the caller.
"""

from __future__ import annotations

import math
import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

Status = Literal["ok", "stale", "unavailable", "not_configured"]
STATUSES: frozenset[str] = frozenset({"ok", "stale", "unavailable", "not_configured"})
UNAVAILABLE_ERROR = "unavailable"


SourceKind = Literal["json_file", "directory", "url"]


@dataclass(frozen=True)
class ExternalSource:
    """One optional external location. Unset means ``not_configured``."""

    name: str
    env_var: str
    kind: SourceKind


EXTERNAL_SOURCES: tuple[ExternalSource, ...] = (
    ExternalSource("roster_snapshot", "FLEET_ROSTER_SNAPSHOT", "json_file"),
    ExternalSource("harness_snapshot", "FLEET_HARNESS_SNAPSHOT", "json_file"),
    ExternalSource("downloads", "FLEET_DOWNLOAD_STATUS", "json_file"),
    ExternalSource("backups", "FLEET_BACKUP_STATE_DIR", "directory"),
    ExternalSource("mq_state", "FLEET_MQ_STATE_DIR", "directory"),
    ExternalSource("stats", "FLEET_PROMETHEUS_URL", "url"),
    ExternalSource("alerts", "FLEET_ALERTMANAGER_URL", "url"),
    ExternalSource("links", "FLEET_GRAFANA_URL", "url"),
)

LOCATION_ENV_VARS: tuple[str, ...] = tuple(source.env_var for source in EXTERNAL_SOURCES)


@dataclass(frozen=True)
class SourceReport:
    name: str
    status: Status
    age_s: float | None
    error: str | None

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "status": self.status,
            "age_s": self.age_s,
            "error": self.error,
        }


def _finite_age(age_s: float | None) -> float | None:
    if age_s is None:
        return None
    value = float(age_s)
    if not math.isfinite(value) or value < 0:
        raise ValueError
    return value


def _checked(name: str, status: str, age_s: float | None, error: str | None) -> SourceReport:
    if not isinstance(name, str) or not name or status not in STATUSES:
        raise ValueError
    if status == "not_configured":
        return SourceReport(name, "not_configured", None, None)
    if status == "unavailable":
        return SourceReport(name, "unavailable", None, UNAVAILABLE_ERROR)
    if status not in {"ok", "stale"} or error is not None:
        raise ValueError
    return SourceReport(name, status, _finite_age(age_s), None)


def report(
    name: str,
    status: str,
    *,
    age_s: float | None = None,
    error: str | None = None,
) -> SourceReport:
    """Build one source row. Invalid input becomes ``unavailable``."""
    try:
        return _checked(name, status, age_s, error)
    except Exception:
        safe_name = name if isinstance(name, str) and name else "source"
        return SourceReport(safe_name, "unavailable", None, UNAVAILABLE_ERROR)


def read_location(env_var: str, environ: Mapping[str, str] | None = None) -> str | None:
    """Return a configured location, or None when unset or blank.

    No default is applied. Callers must not copy the value into a response.
    """
    source = os.environ if environ is None else environ
    raw = source.get(env_var)
    if raw is None:
        return None
    value = raw.strip()
    if not value:
        return None
    return value


def configuration_status(
    source: ExternalSource,
    environ: Mapping[str, str] | None = None,
) -> SourceReport:
    """Report whether one location variable is set. Never raises."""
    try:
        if read_location(source.env_var, environ) is None:
            return report(source.name, "not_configured")
        return report(source.name, "ok")
    except Exception:
        return report(source.name, "unavailable")


def collect_source_reports(environ: Mapping[str, str] | None = None) -> tuple[SourceReport, ...]:
    """One report per declared location. One failure does not drop the rest."""
    reports: list[SourceReport] = []
    for source in EXTERNAL_SOURCES:
        try:
            reports.append(configuration_status(source, environ))
        except Exception:
            reports.append(report(source.name, "unavailable"))
    return tuple(reports)
