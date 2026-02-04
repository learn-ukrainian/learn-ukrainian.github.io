"""
Sampling logic for LLM validation tiers.

Implements the sampling strategy:
- Tier 1: Automated (Default)
- Tier 2: LLM Verified (Risk-Based: Low naturalness, sensitive topics)
- Tier 3: Stratified Sampling
"""

import random
import hashlib
from typing import Dict, Any, List, Optional, Set

# Constants
SENSITIVE_TAGS = {
    'politics', 'war', 'religion', 'history', 'ideology', 'gender', 
    'controversial', 'policy', 'identity'
}
NATURALNESS_THRESHOLD = 8.0  # Modules below this score get Tier 2
SAMPLE_RATE = 0.20  # 20% sampling for Tier 3

def determine_tier(module_data: Dict[str, Any]) -> str:
    """
    Determine the implied validation tier based on module characteristics.
    Does NOT return the stored tier, but calculates what it *should* be
    based on risk factors (Tier 2: LLM Verified).
    """
    # Check naturalness
    naturalness = module_data.get('naturalness', {})
    score = 10
    if isinstance(naturalness, dict):
        score = naturalness.get('score', 10)
    
    if score < NATURALNESS_THRESHOLD:
        return 'llm-verified'

    # Check sensitive tags
    tags = set(module_data.get('tags', []))
    if not tags.isdisjoint(SENSITIVE_TAGS):
        return 'llm-verified'
        
    return 'automated'

def get_validation_status(module_data: Dict[str, Any]) -> str:
    """
    Get the actual stored validation status.
    Defaults to 'automated' if not set.
    """
    return module_data.get('validation_tier', 'automated')

def should_sample(slug: str, sample_rate: float = SAMPLE_RATE) -> bool:
    """
    Deterministically decide if a module should be sampled for Tier 3.
    Uses hash of slug to ensure stability.
    """
    # Create a stable hash integer
    hash_val = int(hashlib.sha256(slug.encode('utf-8')).hexdigest(), 16)
    # Normalize to 0-1
    normalized = (hash_val % 1000) / 1000.0
    return normalized < sample_rate

def get_sampling_candidates(modules: List[Dict[str, Any]]) -> List[str]:
    """
    Identify which modules NEED validation but don't have it.
    
    Returns slugs of modules that should be 'llm-verified' but are 'automated'.
    """
    candidates = []
    for m in modules:
        slug = m.get('slug')
        if not slug:
            continue
            
        current_tier = get_validation_status(m)
        
        # If already verified/gold, skip
        if current_tier in ('llm-verified', 'gold-standard'):
            continue
            
        # Check risk factors (Tier 2)
        implied_tier = determine_tier(m)
        if implied_tier == 'llm-verified':
            candidates.append(slug)
            continue
            
        # Check random sampling (Tier 3)
        if should_sample(slug):
            candidates.append(slug)
            
    return candidates

def calculate_sampling_metrics(modules: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate coverage metrics for the report.
    """
    total = len(modules)
    if total == 0:
        return {}
        
    tiers = {
        'automated': 0,
        'llm-verified': 0,
        'gold-standard': 0
    }
    
    risk_triggered = 0
    sample_triggered = 0
    
    for m in modules:
        tier = get_validation_status(m)
        tiers[tier] = tiers.get(tier, 0) + 1
        
        # Analyze why (Tier 2 Risk vs Tier 3 Sample)
        if determine_tier(m) == 'llm-verified':
            risk_triggered += 1
        elif should_sample(m.get('slug', '')):
            sample_triggered += 1
            
    return {
        'total': total,
        'tiers': tiers,
        'coverage_pct': (tiers['llm-verified'] + tiers['gold-standard']) / total * 100,
        'risk_triggered': risk_triggered,
        'sample_triggered': sample_triggered
    }
