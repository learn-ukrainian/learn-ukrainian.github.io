"""
Track Scoring Verification System.

This package provides automated verification for scoring criteria
across curriculum tracks, enabling objective 10/10 scoring.

Modules:
    config: Track-specific criteria definitions and weights
    metrics: Metric extraction functions (automated, no LLM)
    aggregator: Module-to-track score aggregation
    caps: Critical failure cap logic
    report: Output formatting and reporting
"""

from .aggregator import aggregate_track_metrics, calculate_track_score
from .caps import apply_critical_caps
from .config import TRACK_CONFIGS, get_track_config
from .metrics import extract_module_metrics
from .report import format_metrics_table, generate_track_report

__all__ = [
    'TRACK_CONFIGS',
    'aggregate_track_metrics',
    'apply_critical_caps',
    'calculate_track_score',
    'extract_module_metrics',
    'format_metrics_table',
    'generate_track_report',
    'get_track_config',
]
