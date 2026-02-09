import yaml
from jsonschema import validate
from typing import Any, Dict

class LineLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        mapping = super().construct_mapping(node, deep=deep)
        mapping['__line__'] = node.start_mark.line + 1
        return mapping

def validate_with_lines(data: Dict[str, Any], schema: Dict[str, Any]):
    # Filter out __line__ before validation
    def filter_lines(obj):
        if isinstance(obj, dict):
            return {k: filter_lines(v) for k, v in obj.items() if k != '__line__'}
        elif isinstance(obj, list):
            return [filter_lines(i) for i in obj]
        return obj

    clean_data = filter_lines(data)
    validate(instance=clean_data, schema=schema)
