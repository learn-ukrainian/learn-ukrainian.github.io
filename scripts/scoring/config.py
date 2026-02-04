"""
Track-specific scoring criteria definitions and weights.

Each track has unique scoring criteria optimized for its content type:
- Standard tracks: Grammar/content balance, skills distribution
- B2-HIST: Historical accuracy, decolonization, primary sources
- C1-HIST: Historiographical methodology, source criticism
- C1-BIO: Biographical accuracy, cultural context, legacy analysis
- LIT: Literary analysis, authentic text engagement, stylistic devices
"""

from typing import TypedDict, Optional


class CriterionConfig(TypedDict):
    """Configuration for a single scoring criterion."""
    name: str
    weight: float  # 0.0 to 1.0, must sum to 1.0 for track
    description: str
    measurement: str  # How this criterion is measured
    auto_fail_threshold: Optional[float]  # Score below this = auto-fail
    cap_conditions: Optional[dict]  # Conditions that cap this score


class TrackConfig(TypedDict):
    """Configuration for a curriculum track."""
    name: str
    level_dir: str  # Directory name in curriculum
    module_count: int
    criteria: dict[str, CriterionConfig]


# =============================================================================
# TRACK CONFIGURATIONS
# =============================================================================

TRACK_CONFIGS: dict[str, TrackConfig] = {

    # =========================================================================
    # B2-HIST: Ukrainian History (B2 Level)
    # =========================================================================
    'b2-hist': {
        'name': 'B2-HIST: Ukrainian History',
        'level_dir': 'b2-hist',
        'module_count': 140,
        'criteria': {
            'audit_pass_rate': {
                'name': 'Audit Pass Rate',
                'weight': 0.15,
                'description': 'Percentage of modules passing automated audit',
                'measurement': 'status_json_pass_count / total_modules',
                'auto_fail_threshold': 0.7,
                'cap_conditions': None,
            },
            'primary_source_integration': {
                'name': 'Primary Source Integration',
                'weight': 0.15,
                'description': 'Integration of primary historical sources',
                'measurement': 'avg_quote_callouts_per_module',
                'auto_fail_threshold': None,
                'cap_conditions': {
                    'zero_quotes': {'max_score': 3, 'condition': 'total_quote_callouts == 0'},
                },
            },
            'historical_accuracy': {
                'name': 'Historical Accuracy',
                'weight': 0.15,
                'description': 'Factual correctness of historical content',
                'measurement': 'manual_verification + naturalness_gate',
                'auto_fail_threshold': 0.7,
                'cap_conditions': None,
            },
            'decolonization_perspective': {
                'name': 'Decolonization Perspective',
                'weight': 0.10,
                'description': 'Ukrainian-centric historical framing',
                'measurement': 'myth_buster_count + agency_markers + toponym_consistency',
                'auto_fail_threshold': None,
                'cap_conditions': {
                    'zero_myth_busters': {'max_score': 4, 'condition': 'total_myth_buster_callouts == 0'},
                    'low_agency': {'max_score': 6, 'condition': 'agency_marker_ratio < 0.10'},
                },
            },
            'era_vocabulary': {
                'name': 'Era-Appropriate Vocabulary',
                'weight': 0.10,
                'description': 'Period-specific vocabulary coverage',
                'measurement': 'vocab_files_with_items / total_modules',
                'auto_fail_threshold': None,
                'cap_conditions': None,
            },
            'chronological_coherence': {
                'name': 'Chronological Coherence',
                'weight': 0.10,
                'description': 'Logical timeline progression',
                'measurement': 'date_sequence_validation',
                'auto_fail_threshold': None,
                'cap_conditions': None,
            },
            'critical_analysis_skills': {
                'name': 'Critical Analysis Skills',
                'weight': 0.10,
                'description': 'Source analysis and critical thinking activities',
                'measurement': 'critical_analysis_activities + analysis_callouts',
                'auto_fail_threshold': None,
                'cap_conditions': None,
            },
            'activity_coverage': {
                'name': 'Activity Coverage',
                'weight': 0.10,
                'description': 'Completeness of activity files',
                'measurement': 'activity_files_present / total_modules',
                'auto_fail_threshold': 0.8,
                'cap_conditions': None,
            },
            'internal_consistency': {
                'name': 'Internal Consistency',
                'weight': 0.05,
                'description': 'Cross-references and terminology consistency',
                'measurement': 'cross_reference_count + terminology_consistency',
                'auto_fail_threshold': None,
                'cap_conditions': {
                    'zero_xrefs': {'max_score': 5, 'condition': 'total_cross_references == 0'},
                },
            },
        },
    },

    # =========================================================================
    # C1-HIST: Historiography (C1 Level)
    # =========================================================================
    'c1-hist': {
        'name': 'C1-HIST: Ukrainian Historiography',
        'level_dir': 'c1-hist',
        'module_count': 30,  # Approximate
        'criteria': {
            'audit_pass_rate': {
                'name': 'Audit Pass Rate',
                'weight': 0.15,
                'description': 'Percentage of modules passing automated audit',
                'measurement': 'status_json_pass_count / total_modules',
                'auto_fail_threshold': 0.7,
                'cap_conditions': None,
            },
            'historiographical_methodology': {
                'name': 'Historiographical Methodology',
                'weight': 0.15,
                'description': 'Discussion of historical methods and approaches',
                'measurement': 'methodology_sections + source_diversity_score',
                'auto_fail_threshold': None,
                'cap_conditions': None,
            },
            'source_criticism_skills': {
                'name': 'Source Criticism Skills',
                'weight': 0.15,
                'description': 'Training in evaluating historical sources',
                'measurement': 'source_analysis_activities + methodology_callouts',
                'auto_fail_threshold': None,
                'cap_conditions': None,
            },
            'thematic_coherence': {
                'name': 'Thematic Coherence',
                'weight': 0.10,
                'description': 'Consistency of themes across modules',
                'measurement': 'thematic_tag_coverage + cross_reference_density',
                'auto_fail_threshold': None,
                'cap_conditions': None,
            },
            'primary_source_integration': {
                'name': 'Primary Source Integration',
                'weight': 0.15,
                'description': 'Integration of primary historical sources',
                'measurement': 'avg_quote_callouts_per_module',
                'auto_fail_threshold': None,
                'cap_conditions': {
                    'zero_quotes': {'max_score': 3, 'condition': 'total_quote_callouts == 0'},
                },
            },
            'activity_coverage': {
                'name': 'Activity Coverage',
                'weight': 0.10,
                'description': 'Completeness of activity files',
                'measurement': 'activity_files_present / total_modules',
                'auto_fail_threshold': 0.8,
                'cap_conditions': None,
            },
            'vocabulary_coverage': {
                'name': 'Vocabulary Coverage',
                'weight': 0.10,
                'description': 'Academic vocabulary coverage',
                'measurement': 'vocab_files_with_items / total_modules',
                'auto_fail_threshold': None,
                'cap_conditions': None,
            },
            'internal_consistency': {
                'name': 'Internal Consistency',
                'weight': 0.10,
                'description': 'Cross-references and terminology consistency',
                'measurement': 'cross_reference_count + terminology_consistency',
                'auto_fail_threshold': None,
                'cap_conditions': {
                    'zero_xrefs': {'max_score': 5, 'condition': 'total_cross_references == 0'},
                },
            },
        },
    },

    # =========================================================================
    # C1-BIO: Ukrainian Biographies (C1 Level)
    # =========================================================================
    'c1-bio': {
        'name': 'C1-BIO: Ukrainian Biographies',
        'level_dir': 'c1-bio',
        'module_count': 128,
        'criteria': {
            'audit_pass_rate': {
                'name': 'Audit Pass Rate',
                'weight': 0.15,
                'description': 'Percentage of modules passing automated audit',
                'measurement': 'status_json_pass_count / total_modules',
                'auto_fail_threshold': 0.7,
                'cap_conditions': None,
            },
            'biographical_accuracy': {
                'name': 'Biographical Accuracy',
                'weight': 0.15,
                'description': 'Factual correctness of biographical content',
                'measurement': 'manual_verification + naturalness_gate',
                'auto_fail_threshold': 0.7,
                'cap_conditions': None,
            },
            'source_reliability': {
                'name': 'Source Reliability',
                'weight': 0.10,
                'description': 'Quality and variety of sources used',
                'measurement': 'source_type_diversity + quote_count',
                'auto_fail_threshold': None,
                'cap_conditions': {
                    'zero_quotes': {'max_score': 4, 'condition': 'total_quote_callouts == 0'},
                },
            },
            'cultural_historical_context': {
                'name': 'Cultural/Historical Context',
                'weight': 0.15,
                'description': 'Contextualization within Ukrainian culture/history',
                'measurement': 'context_callouts + era_references',
                'auto_fail_threshold': None,
                'cap_conditions': None,
            },
            'significance_assessment': {
                'name': 'Significance Assessment',
                'weight': 0.10,
                'description': 'Analysis of subject\'s impact and legacy',
                'measurement': 'legacy_sections + influence_markers',
                'auto_fail_threshold': None,
                'cap_conditions': {
                    'no_legacy': {'max_score': 6, 'condition': 'legacy_section_count == 0'},
                },
            },
            'activity_coverage': {
                'name': 'Activity Coverage',
                'weight': 0.10,
                'description': 'Completeness of activity files',
                'measurement': 'activity_files_present / total_modules',
                'auto_fail_threshold': 0.8,
                'cap_conditions': None,
            },
            'vocabulary_coverage': {
                'name': 'Vocabulary Coverage',
                'weight': 0.10,
                'description': 'Biographical/academic vocabulary coverage',
                'measurement': 'vocab_files_with_items / total_modules',
                'auto_fail_threshold': None,
                'cap_conditions': None,
            },
            'internal_consistency': {
                'name': 'Internal Consistency',
                'weight': 0.10,
                'description': 'Cross-references and terminology consistency',
                'measurement': 'cross_reference_count + terminology_consistency',
                'auto_fail_threshold': None,
                'cap_conditions': {
                    'zero_xrefs': {'max_score': 5, 'condition': 'total_cross_references == 0'},
                },
            },
            'cefr_alignment': {
                'name': 'CEFR Alignment',
                'weight': 0.05,
                'description': 'Content appropriate for C1 level',
                'measurement': 'level_tag_verification',
                'auto_fail_threshold': None,
                'cap_conditions': None,
            },
        },
    },

    # =========================================================================
    # LIT: Ukrainian Literature (Post-C1)
    # =========================================================================
    'lit': {
        'name': 'LIT: Ukrainian Literature',
        'level_dir': 'lit',
        'module_count': 30,
        'criteria': {
            'audit_pass_rate': {
                'name': 'Audit Pass Rate',
                'weight': 0.15,
                'description': 'Percentage of modules passing automated audit',
                'measurement': 'status_json_pass_count / total_modules',
                'auto_fail_threshold': 0.7,
                'cap_conditions': None,
            },
            'literary_depth': {
                'name': 'Literary Depth/Analysis',
                'weight': 0.20,
                'description': 'Quality of literary analysis',
                'measurement': 'stylistic_device_density + analysis_sections',
                'auto_fail_threshold': None,
                'cap_conditions': {
                    'no_analysis': {'max_score': 5, 'condition': 'analysis_section_count == 0'},
                },
            },
            'authentic_text_engagement': {
                'name': 'Authentic Text Engagement',
                'weight': 0.15,
                'description': 'Engagement with original literary texts',
                'measurement': 'citation_ratio + literary_quote_count',
                'auto_fail_threshold': None,
                'cap_conditions': {
                    'low_citation': {'max_score': 5, 'condition': 'citation_ratio < 0.05'},
                },
            },
            'archaic_literary_vocab': {
                'name': 'Archaic/Literary Vocabulary',
                'weight': 0.10,
                'description': 'Coverage of literary and archaic vocabulary',
                'measurement': 'archaic_vocab_items + literary_terms',
                'auto_fail_threshold': None,
                'cap_conditions': None,
            },
            'intertextual_links': {
                'name': 'Intertextual Links',
                'weight': 0.10,
                'description': 'Connections between literary works',
                'measurement': 'intertextual_reference_count',
                'auto_fail_threshold': None,
                'cap_conditions': None,
            },
            'activity_coverage': {
                'name': 'Activity Coverage',
                'weight': 0.10,
                'description': 'Completeness of activity files',
                'measurement': 'activity_files_present / total_modules',
                'auto_fail_threshold': 0.8,
                'cap_conditions': None,
            },
            'vocabulary_coverage': {
                'name': 'Vocabulary Coverage',
                'weight': 0.10,
                'description': 'Literary vocabulary coverage',
                'measurement': 'vocab_files_with_items / total_modules',
                'auto_fail_threshold': None,
                'cap_conditions': None,
            },
            'internal_consistency': {
                'name': 'Internal Consistency',
                'weight': 0.05,
                'description': 'Cross-references and thematic links',
                'measurement': 'cross_reference_count',
                'auto_fail_threshold': None,
                'cap_conditions': {
                    'zero_xrefs': {'max_score': 5, 'condition': 'total_cross_references == 0'},
                },
            },
            'cefr_alignment': {
                'name': 'CEFR Alignment',
                'weight': 0.05,
                'description': 'Content appropriate for advanced level',
                'measurement': 'level_tag_verification',
                'auto_fail_threshold': None,
                'cap_conditions': None,
            },
        },
    },

    # =========================================================================
    # Standard Tracks (A1, A2, B1, B2, C1, C2)
    # =========================================================================
    'standard': {
        'name': 'Standard Track',
        'level_dir': '',  # Varies by level
        'module_count': 0,  # Varies by level
        'criteria': {
            'audit_pass_rate': {
                'name': 'Audit Pass Rate',
                'weight': 0.20,
                'description': 'Percentage of modules passing automated audit',
                'measurement': 'status_json_pass_count / total_modules',
                'auto_fail_threshold': 0.7,
                'cap_conditions': None,
            },
            'grammar_content_coverage': {
                'name': 'Grammar/Content Coverage',
                'weight': 0.15,
                'description': 'Coverage of required grammar and topics',
                'measurement': 'plan_coverage_percentage',
                'auto_fail_threshold': 0.8,
                'cap_conditions': None,
            },
            'skills_balance': {
                'name': 'Skills Balance',
                'weight': 0.10,
                'description': 'Distribution of reading/writing/listening/speaking',
                'measurement': 'activity_type_distribution_variance',
                'auto_fail_threshold': None,
                'cap_conditions': None,
            },
            'activity_coverage': {
                'name': 'Activity Coverage',
                'weight': 0.15,
                'description': 'Completeness and quality of activities',
                'measurement': 'activity_files_present / total_modules',
                'auto_fail_threshold': 0.8,
                'cap_conditions': None,
            },
            'vocabulary_coverage': {
                'name': 'Vocabulary Coverage',
                'weight': 0.10,
                'description': 'Coverage of required vocabulary',
                'measurement': 'vocab_files_with_items / total_modules',
                'auto_fail_threshold': None,
                'cap_conditions': None,
            },
            'cefr_alignment': {
                'name': 'CEFR Alignment',
                'weight': 0.10,
                'description': 'Content appropriate for CEFR level',
                'measurement': 'level_tag_verification + grammar_constraints',
                'auto_fail_threshold': None,
                'cap_conditions': None,
            },
            'checkpoint_structure': {
                'name': 'Checkpoint Structure',
                'weight': 0.05,
                'description': 'Proper checkpoint module format',
                'measurement': 'checkpoint_format_validation',
                'auto_fail_threshold': None,
                'cap_conditions': None,
            },
            'state_standard_compliance': {
                'name': 'State Standard Compliance',
                'weight': 0.05,
                'description': 'Alignment with Ukrainian state standards',
                'measurement': 'state_standard_checklist',
                'auto_fail_threshold': None,
                'cap_conditions': None,
            },
            'internal_consistency': {
                'name': 'Internal Consistency',
                'weight': 0.10,
                'description': 'Cross-references and terminology consistency',
                'measurement': 'cross_reference_count + terminology_consistency',
                'auto_fail_threshold': None,
                'cap_conditions': {
                    'zero_xrefs': {'max_score': 5, 'condition': 'total_cross_references == 0'},
                },
            },
        },
    },
}


# Standard track variants with level-specific module counts
STANDARD_TRACK_VARIANTS: dict[str, dict] = {
    'a1': {'level_dir': 'a1', 'module_count': 44},
    'a2': {'level_dir': 'a2', 'module_count': 70},
    'b1': {'level_dir': 'b1', 'module_count': 92},
    'b2': {'level_dir': 'b2', 'module_count': 94},
    'c1': {'level_dir': 'c1', 'module_count': 106},
    'c2': {'level_dir': 'c2', 'module_count': 100},
}


def get_track_config(track_id: str) -> TrackConfig:
    """
    Get configuration for a track.

    Args:
        track_id: Track identifier (b2-hist, c1-bio, c1-hist, lit, a1, a2, etc.)

    Returns:
        TrackConfig for the specified track

    Raises:
        ValueError: If track_id is not recognized
    """
    # Check specialized tracks first
    if track_id in TRACK_CONFIGS:
        return TRACK_CONFIGS[track_id]

    # Check standard track variants
    if track_id in STANDARD_TRACK_VARIANTS:
        config = TRACK_CONFIGS['standard'].copy()
        variant = STANDARD_TRACK_VARIANTS[track_id]
        config['level_dir'] = variant['level_dir']
        config['module_count'] = variant['module_count']
        config['name'] = f"Standard Track ({track_id.upper()})"
        return config

    raise ValueError(f"Unknown track: {track_id}. Valid tracks: {list(TRACK_CONFIGS.keys()) + list(STANDARD_TRACK_VARIANTS.keys())}")


def get_all_track_ids() -> list[str]:
    """Get list of all valid track IDs."""
    specialized = list(TRACK_CONFIGS.keys())
    specialized.remove('standard')  # Don't include generic standard
    return specialized + list(STANDARD_TRACK_VARIANTS.keys())
