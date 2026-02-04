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

from .config import TRACK_CONFIGS, get_track_config
from .metrics import extract_module_metrics
from .aggregator import aggregate_track_metrics, calculate_track_score
from .caps import apply_critical_caps
from .report import generate_track_report, format_metrics_table

__all__ = [
    'TRACK_CONFIGS',
    'get_track_config',
    'extract_module_metrics',
    'aggregate_track_metrics',
    'calculate_track_score',
    'apply_critical_caps',
    'generate_track_report',
    'format_metrics_table',
]
