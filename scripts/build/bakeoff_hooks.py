"""Product calls for the B1 writer bakeoff.

Machinery runners load this module by a non-literal name and call through
the returned module. The functions and tables here are the same objects the
writer pipeline uses, so a bakeoff run and its score stay on that path.
"""

from __future__ import annotations

from scripts.audit.wiki_coverage_gate import (
    check_wiki_coverage,
    parse_implementation_map,
    validate_obligations,
)
from scripts.build import linear_pipeline
from scripts.build.phases.implementation_map import (
    read_implementation_map,
    seed_implementation_map,
    write_implementation_map,
)
from scripts.yaml_activities import ActivityParser

WRITER_ARTIFACTS = linear_pipeline.WRITER_ARTIFACTS
WRITER_CHOICES = linear_pipeline.WRITER_CHOICES
WRITER_DEFAULTS = linear_pipeline.WRITER_DEFAULTS
RESOURCE_ROLES = linear_pipeline.RESOURCE_ROLES

plan_path_for = linear_pipeline.plan_path_for
load_plan = linear_pipeline.load_plan
validate_plan = linear_pipeline.validate_plan
build_knowledge_packet = linear_pipeline.build_knowledge_packet
build_wiki_manifest_data = linear_pipeline.build_wiki_manifest_data
build_wiki_coverage_obligation_checklist = (
    linear_pipeline.build_wiki_coverage_obligation_checklist
)
render_writer_prompt = linear_pipeline.render_writer_prompt
invoke_writer = linear_pipeline.invoke_writer
parse_writer_output = linear_pipeline.parse_writer_output
word_count_gate = linear_pipeline._word_count_gate

__all__ = [
    "RESOURCE_ROLES",
    "WRITER_ARTIFACTS",
    "WRITER_CHOICES",
    "WRITER_DEFAULTS",
    "ActivityParser",
    "build_knowledge_packet",
    "build_wiki_coverage_obligation_checklist",
    "build_wiki_manifest_data",
    "check_wiki_coverage",
    "invoke_writer",
    "load_plan",
    "parse_implementation_map",
    "parse_writer_output",
    "plan_path_for",
    "read_implementation_map",
    "render_writer_prompt",
    "seed_implementation_map",
    "validate_obligations",
    "validate_plan",
    "word_count_gate",
    "write_implementation_map",
]
