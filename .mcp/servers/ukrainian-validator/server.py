#!/usr/bin/env python3
"""
MCP Server: Ukrainian Grammar Validator
Bridges Claude Code ↔ gemini for automated validation

This server provides a tool for validating Ukrainian content using gemini.
It loads the Ukrainian Grammar Validator prompt and passes content to Gemini
for linguistic analysis.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

# MCP Server Protocol
# Reference: https://modelcontextprotocol.io/docs/concepts/tools


class UkrainianValidatorServer:
    """MCP server for Ukrainian content validation via gemini."""

    def __init__(self):
        """Initialize the server with paths to project resources."""
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.prompt_path = self.project_root / "scripts" / "audit" / "ukrainian_grammar_validator_prompt.md"
        self.config_path = self.project_root / ".gemini" / "config.yaml"

        if not self.prompt_path.exists():
            raise FileNotFoundError(f"Ukrainian validator prompt not found: {self.prompt_path}")
        if not self.config_path.exists():
            raise FileNotFoundError(f"Gemini config not found: {self.config_path}")

    def validate_ukrainian(self, content: str, level: str) -> Dict[str, Any]:
        """
        Validate Ukrainian content using gemini.

        Args:
            content: Ukrainian text from module
            level: CEFR level (A1, A2, B1, B2, C1, C2)

        Returns:
            Dict with violations and summary
        """
        # Load Ukrainian Grammar Validator prompt
        validator_prompt = self.prompt_path.read_text(encoding='utf-8')

        # Build full prompt for Gemini
        full_prompt = f"""{validator_prompt}

---

**Level**: {level}
**Content to validate**:

{content}

Please validate all Ukrainian text and return JSON with violations found.
Use this format:
{{
  "violations": [
    {{
      "type": "RUSSIANISM|CALQUE|CASE_AGREEMENT|ASPECT|REGISTER",
      "severity": "critical|high|medium|low",
      "line": 42,
      "text": "original text with error",
      "error": "specific error",
      "correction": "correct form",
      "explanation_uk": "Ukrainian explanation",
      "explanation_en": "English explanation",
      "confidence": 0.95
    }}
  ],
  "summary": {{
    "total": 3,
    "critical": 1,
    "high": 1,
    "medium": 1,
    "recommendation": "Fix critical Russianism before commit"
  }}
}}
"""

        try:
            # Choose model based on level
            # A1-B1: gemini-3-flash-preview (simpler content, faster/cheaper)
            # B2+: gemini-3-pro-preview (complex immersed content, better quality)
            if level.upper() in ('A1', 'A2', 'B1'):
                model = 'gemini-3-flash-preview'
            else:
                model = 'gemini-3-pro-preview'

            # Update config.yaml with selected model
            config_content = self.config_path.read_text(encoding='utf-8')
            # Replace model line (preserve other settings)
            import re
            updated_config = re.sub(r'^model:.*$', f'model: {model}', config_content, flags=re.MULTILINE)
            self.config_path.write_text(updated_config, encoding='utf-8')

            # Call gemini CLI (uses model from config.yaml)
            # -y: auto-confirm (YOLO mode)
            result = subprocess.run(
                ['gemini', '-y'],
                input=full_prompt,
                capture_output=True,
                text=True,
                timeout=60,  # Increased timeout for LLM response
                cwd=self.project_root
            )

            if result.returncode != 0:
                return {
                    'error': 'gemini execution failed',
                    'stderr': result.stderr,
                    'returncode': result.returncode
                }

            # Parse Gemini's response
            # Gemini might return JSON or markdown with JSON code block
            output = result.stdout.strip()

            # Try to extract JSON from markdown code block if present
            if '```json' in output:
                json_start = output.find('```json') + 7
                json_end = output.find('```', json_start)
                json_str = output[json_start:json_end].strip()
            elif '```' in output:
                json_start = output.find('```') + 3
                json_end = output.find('```', json_start)
                json_str = output[json_start:json_end].strip()
            else:
                json_str = output

            try:
                violations = json.loads(json_str)
                return violations
            except json.JSONDecodeError:
                # If JSON parsing fails, return raw output for debugging
                return {
                    'error': 'Failed to parse Gemini response as JSON',
                    'raw_output': output,
                    'violations': [],
                    'summary': {
                        'total': 0,
                        'recommendation': 'Manual review needed - parsing failed'
                    }
                }

        except subprocess.TimeoutExpired:
            return {
                'error': 'gemini timeout (>30s)',
                'violations': [],
                'summary': {'total': 0, 'recommendation': 'Retry validation'}
            }
        except FileNotFoundError:
            return {
                'error': 'gemini not found in PATH',
                'help': 'Install gemini or add to PATH',
                'violations': [],
                'summary': {'total': 0, 'recommendation': 'Install gemini'}
            }
        except Exception as e:
            return {
                'error': f'Unexpected error: {str(e)}',
                'violations': [],
                'summary': {'total': 0, 'recommendation': 'Check MCP server logs'}
            }

    def check_naturalness(self, content: str, level: str, context: str = '') -> Dict[str, Any]:
        """
        Check if Ukrainian text sounds natural at the given CEFR level.

        Args:
            content: Ukrainian text to evaluate
            level: CEFR level (A1-C2)
            context: Optional context (e.g., "mark-the-words activity", "dialogue")

        Returns:
            Dict with score (1-10), issues, and recommendation
        """
        import re

        prompt = f"""You are an expert Ukrainian language educator evaluating text naturalness.

**Task**: Rate how natural this Ukrainian text sounds for a {level} learner.

**Context**: {context or 'curriculum content'}

**Text to evaluate**:
{content}

**Evaluation criteria**:
1. **Flow**: Do sentences connect naturally? Are there discourse markers (потім, тому, але, тоді)?
2. **Coherence**: Is there a logical narrative or theme, or just random disconnected sentences?
3. **Register**: Does the language match {level} expectations (not too simple, not too complex)?
4. **Authenticity**: Would a native speaker write/say this naturally?

**Red flags for robotic text**:
- Sentences that don't relate to each other
- Repetitive subject-verb patterns ("Я зробив X. Я зробив Y. Я зробив Z.")
- No temporal or logical connectors
- Unnatural topic jumps

Return JSON:
{{
  "score": 8,
  "issues": ["list of specific problems"],
  "recommendation": "brief actionable advice",
  "rewrite_needed": false
}}

Score guide:
- 9-10: Excellent, sounds like native writing
- 7-8: Good, minor improvements possible
- 5-6: Acceptable but noticeably artificial
- 3-4: Poor, clearly robotic/disconnected
- 1-2: Unusable, random sentences
"""

        try:
            # Use flash model for quick evaluation
            model = 'gemini-2.0-flash'

            config_content = self.config_path.read_text(encoding='utf-8')
            updated_config = re.sub(r'^model:.*$', f'model: {model}', config_content, flags=re.MULTILINE)
            self.config_path.write_text(updated_config, encoding='utf-8')

            result = subprocess.run(
                ['gemini', '-y'],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.project_root
            )

            if result.returncode != 0:
                return {'error': 'gemini execution failed', 'stderr': result.stderr}

            output = result.stdout.strip()

            # Extract JSON
            if '```json' in output:
                json_start = output.find('```json') + 7
                json_end = output.find('```', json_start)
                json_str = output[json_start:json_end].strip()
            elif '```' in output:
                json_start = output.find('```') + 3
                json_end = output.find('```', json_start)
                json_str = output[json_start:json_end].strip()
            else:
                json_str = output

            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                return {'error': 'Failed to parse response', 'raw_output': output}

        except subprocess.TimeoutExpired:
            return {'error': 'gemini timeout'}
        except Exception as e:
            return {'error': str(e)}

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP JSON-RPC request."""
        method = request.get('method')
        params = request.get('params', {})
        request_id = request.get('id')

        # Wrap response in JSON-RPC format
        def make_response(result):
            if request_id is not None:
                return {'jsonrpc': '2.0', 'id': request_id, 'result': result}
            return result

        def make_error(code, message):
            if request_id is not None:
                return {'jsonrpc': '2.0', 'id': request_id, 'error': {'code': code, 'message': message}}
            return {'error': message}

        # MCP Protocol: initialize handshake
        if method == 'initialize':
            return make_response({
                'protocolVersion': '2024-11-05',
                'capabilities': {
                    'tools': {}
                },
                'serverInfo': {
                    'name': 'ukrainian-validator',
                    'version': '1.0.0'
                }
            })

        # MCP Protocol: notifications (no response needed)
        if method == 'notifications/initialized':
            return None  # No response for notifications

        if method == 'tools/list':
            # Return list of available tools
            return make_response({
                'tools': [
                    {
                        'name': 'validate_ukrainian',
                        'description': 'Validate Ukrainian grammar using Gemini via gemini CLI',
                        'inputSchema': {
                            'type': 'object',
                            'properties': {
                                'content': {
                                    'type': 'string',
                                    'description': 'Ukrainian text to validate'
                                },
                                'level': {
                                    'type': 'string',
                                    'enum': ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'],
                                    'description': 'CEFR level for context-aware validation'
                                }
                            },
                            'required': ['content', 'level']
                        }
                    },
                    {
                        'name': 'check_naturalness',
                        'description': 'Check if Ukrainian text sounds natural (detects robotic/disconnected content)',
                        'inputSchema': {
                            'type': 'object',
                            'properties': {
                                'content': {
                                    'type': 'string',
                                    'description': 'Ukrainian text to evaluate'
                                },
                                'level': {
                                    'type': 'string',
                                    'enum': ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'],
                                    'description': 'CEFR level for appropriate register'
                                },
                                'context': {
                                    'type': 'string',
                                    'description': 'Optional context (e.g., "dialogue", "mark-the-words activity")'
                                }
                            },
                            'required': ['content', 'level']
                        }
                    }
                ]
            })

        elif method == 'tools/call':
            tool_name = params.get('name')
            arguments = params.get('arguments', {})

            if tool_name == 'validate_ukrainian':
                content = arguments.get('content', '')
                level = arguments.get('level', 'B2')

                result = self.validate_ukrainian(content, level)

                return make_response({
                    'content': [
                        {
                            'type': 'text',
                            'text': json.dumps(result, indent=2, ensure_ascii=False)
                        }
                    ]
                })

            if tool_name == 'check_naturalness':
                content = arguments.get('content', '')
                level = arguments.get('level', 'B2')
                context = arguments.get('context', '')

                result = self.check_naturalness(content, level, context)

                return make_response({
                    'content': [
                        {
                            'type': 'text',
                            'text': json.dumps(result, indent=2, ensure_ascii=False)
                        }
                    ]
                })

            return make_error(-32601, f'Unknown tool: {tool_name}')

        return make_error(-32601, f'Unknown method: {method}')

    def run(self):
        """Run the MCP server (stdio mode)."""
        print("Ukrainian Validator MCP Server started", file=sys.stderr)
        print(f"Prompt path: {self.prompt_path}", file=sys.stderr)

        # Read requests from stdin, write responses to stdout
        for line in sys.stdin:
            try:
                request = json.loads(line)
                response = self.handle_request(request)
                # Only send response if not None (notifications don't get responses)
                if response is not None:
                    print(json.dumps(response), flush=True)
            except json.JSONDecodeError as e:
                error_response = {'jsonrpc': '2.0', 'id': None, 'error': {'code': -32700, 'message': f'Parse error: {str(e)}'}}
                print(json.dumps(error_response), flush=True)
            except Exception as e:
                error_response = {'jsonrpc': '2.0', 'id': None, 'error': {'code': -32603, 'message': f'Internal error: {str(e)}'}}
                print(json.dumps(error_response), flush=True)


if __name__ == '__main__':
    server = UkrainianValidatorServer()
    server.run()
