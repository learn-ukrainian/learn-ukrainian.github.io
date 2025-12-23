"""
Content quality validation using LLM evaluation.

Checks if the lesson content is:
- Coherent and well-structured
- Actually teaches what it claims to teach
- Educational (not word salad)
- Has clear explanations and examples
"""

import os
import re
import json
from typing import Optional

# Check if LLM evaluation is enabled
CONTENT_QUALITY_ENABLED = os.getenv('AUDIT_CONTENT_QUALITY', 'false').lower() == 'true'


def extract_lesson_content(content: str) -> str:
    """Extract the main lesson content (everything before Activities section)."""
    # Find the Activities section
    activities_match = re.search(
        r'^## (?:Activities|Вправи)',
        content,
        re.MULTILINE
    )

    if activities_match:
        lesson_content = content[:activities_match.start()]
    else:
        # If no Activities section, take everything up to Vocabulary
        vocab_match = re.search(
            r'^## (?:Vocabulary|Словник)',
            content,
            re.MULTILINE
        )
        if vocab_match:
            lesson_content = content[:vocab_match.start()]
        else:
            # Take everything
            lesson_content = content

    # Remove frontmatter
    frontmatter_match = re.match(r'^---\n.*?\n---\n', lesson_content, re.DOTALL)
    if frontmatter_match:
        lesson_content = lesson_content[frontmatter_match.end():]

    return lesson_content.strip()


def extract_module_metadata(content: str) -> dict:
    """Extract module metadata for context."""
    metadata = {}

    # Extract title
    title_match = re.search(r'^title:\s*(.+)$', content, re.MULTILINE)
    if title_match:
        metadata['title'] = title_match.group(1).strip()

    # Extract phase/level
    phase_match = re.search(r'^phase:\s*(.+)$', content, re.MULTILINE)
    if phase_match:
        metadata['phase'] = phase_match.group(1).strip()

    # Extract module number from title or content
    module_match = re.search(r'^module:\s*(\d+)$', content, re.MULTILINE)
    if module_match:
        metadata['module'] = int(module_match.group(1))

    # Extract pedagogy
    pedagogy_match = re.search(r'^pedagogy:\s*"?([^"\n]+)"?$', content, re.MULTILINE)
    if pedagogy_match:
        metadata['pedagogy'] = pedagogy_match.group(1).strip()

    # Extract first H1 heading as topic
    h1_match = re.search(r'^# (.+)$', content, re.MULTILINE)
    if h1_match:
        metadata['topic'] = h1_match.group(1).strip()

    return metadata


def call_gemini_api(lesson_content: str, metadata: dict) -> Optional[dict]:
    """Call Gemini API to evaluate content quality."""
    try:
        import google.generativeai as genai

        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            return None

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')

        prompt = f"""You are a Ukrainian language curriculum auditor. Evaluate this lesson content for educational quality.

**Module Metadata:**
- Title: {metadata.get('title', 'Unknown')}
- Level: {metadata.get('phase', 'Unknown')}
- Topic: {metadata.get('topic', 'Unknown')}
- Pedagogy: {metadata.get('pedagogy', 'Unknown')}

**Lesson Content:**
{lesson_content[:4000]}  # Limit to avoid token overflow

**Evaluation Criteria:**
1. **Coherence**: Is the content logically organized and easy to follow?
2. **Relevance**: Does it actually teach what the title/topic claims?
3. **Educational Value**: Are there clear explanations and useful examples?
4. **Language Quality**: Is it well-written, not repetitive or confusing?
5. **Word Salad Check**: Does it contain meaningless filler or repetitive patterns?
6. **Linguistic Accuracy**: Are all examples valid Ukrainian words? (Flag any Russian words like 'брать', 'кон', 'ы' disguised as Ukrainian).

**Response Format (JSON only):**
{{
  "coherence_score": 1-5,
  "relevance_score": 1-5,
  "educational_score": 1-5,
  "language_score": 1-5,
  "overall_score": 1-5,
  "is_word_salad": true/false,
  "issues": ["issue 1", "issue 2"],
  "strengths": ["strength 1", "strength 2"],
  "recommendation": "PASS" or "NEEDS_IMPROVEMENT" or "REWRITE"
}}

Respond with ONLY valid JSON, no markdown fences or explanations."""

        response = model.generate_content(prompt)

        # Extract JSON from response
        response_text = response.text.strip()

        # Remove markdown code fences if present
        response_text = re.sub(r'^```json\s*', '', response_text)
        response_text = re.sub(r'\s*```$', '', response_text)

        result = json.loads(response_text)
        return result

    except ImportError:
        print("⚠️  google-generativeai not installed. Install with: pip install google-generativeai")
        return None
    except Exception as e:
        print(f"⚠️  Gemini API error: {e}")
        return None


def call_claude_api(lesson_content: str, metadata: dict) -> Optional[dict]:
    """Call Claude API to evaluate content quality."""
    try:
        import anthropic

        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            return None

        client = anthropic.Anthropic(api_key=api_key)

        prompt = f"""You are a Ukrainian language curriculum auditor. Evaluate this lesson content for educational quality.

**Module Metadata:**
- Title: {metadata.get('title', 'Unknown')}
- Level: {metadata.get('phase', 'Unknown')}
- Topic: {metadata.get('topic', 'Unknown')}
- Pedagogy: {metadata.get('pedagogy', 'Unknown')}

**Lesson Content:**
{lesson_content[:4000]}  # Limit to avoid token overflow

**Evaluation Criteria:**
1. **Coherence**: Is the content logically organized and easy to follow?
2. **Relevance**: Does it actually teach what the title/topic claims?
3. **Educational Value**: Are there clear explanations and useful examples?
4. **Language Quality**: Is it well-written, not repetitive or confusing?
5. **Word Salad Check**: Does it contain meaningless filler or repetitive patterns?

**Response Format (JSON only):**
{{
  "coherence_score": 1-5,
  "relevance_score": 1-5,
  "educational_score": 1-5,
  "language_score": 1-5,
  "overall_score": 1-5,
  "is_word_salad": true/false,
  "issues": ["issue 1", "issue 2"],
  "strengths": ["strength 1", "strength 2"],
  "recommendation": "PASS" or "NEEDS_IMPROVEMENT" or "REWRITE"
}}

Respond with ONLY valid JSON."""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text.strip()

        # Remove markdown code fences if present
        response_text = re.sub(r'^```json\s*', '', response_text)
        response_text = re.sub(r'\s*```$', '', response_text)

        result = json.loads(response_text)
        return result

    except ImportError:
        print("⚠️  anthropic not installed. Install with: pip install anthropic")
        return None
    except Exception as e:
        print(f"⚠️  Claude API error: {e}")
        return None


def check_content_quality(content: str, level_code: str, module_num: int) -> list[dict]:
    """
    Check if lesson content is educational and coherent using LLM evaluation.

    Returns:
        List of violations with format:
        {
            'type': 'CONTENT_QUALITY',
            'severity': 'warning' | 'error',
            'message': 'Description of issue',
            'fix': 'Suggested fix'
        }
    """
    violations = []

    # --- Deterministic Checks (Run regardless of API Key or Enabled Flag) ---
    
    # Check for Russian-only characters (ё, ъ, ы, э)
    # These should almost NEVER appear in Ukrainian content except in explicit "Russian uses..." comparisons
    # NOTE: We scan the ENTIRE content (including Activities) for this check.
    russian_chars = re.compile(r'[ёъыэЁЪЫЭ]')
    matches = list(russian_chars.finditer(content))
    
    if matches:
        # Check if they are inside a "Russian" context (simple heuristic)
        # If the word "Russian" or "російськ" is NOT in the same line/paragraph, flag it.
        bad_matches = []
        for m in matches:
            start, end = max(0, m.start() - 50), min(len(content), m.end() + 50)
            context = content[start:end].lower()
            # STRICTER CHECK: Even with context, we warn about it, but for now let's just flag if context missing
            if 'russian' not in context and 'rocійськ' not in context and 'російськ' not in context:
                bad_matches.append(m.group())
        
        if bad_matches:
             violations.append({
                'type': 'LINGUISTIC_PURITY',
                'severity': 'error',
                'issue': f"Found Russian-only characters in module: {', '.join(set(bad_matches))}",
                'fix': "Remove Russian characters (ё, ъ, ы, э) or ensure they are properly contextually framed."
            })

    if not CONTENT_QUALITY_ENABLED:
        return violations

    # Extract lesson content and metadata for LLM checks
    lesson_content = extract_lesson_content(content)
    metadata = extract_module_metadata(content)

    # Skip if lesson content is too short (less than 500 chars)
    if len(lesson_content) < 500:
        violations.append({
            'type': 'CONTENT_QUALITY',
            'severity': 'warning',
            'issue': f'Lesson content too short ({len(lesson_content)} chars)',
            'fix': 'Expand lesson content with more explanations and examples'
        })
        return violations

    # Try Gemini first, fall back to Claude
    evaluation = call_gemini_api(lesson_content, metadata)
    if evaluation is None:
        evaluation = call_claude_api(lesson_content, metadata)

    if evaluation is None:
        # LLM evaluation unavailable
        violations.append({
            'type': 'CONTENT_QUALITY',
            'severity': 'info',
            'issue': 'LLM evaluation unavailable (set GEMINI_API_KEY or ANTHROPIC_API_KEY)',
            'fix': 'Set API key in environment to enable content quality checks'
        })
        return violations

    if evaluation is None:
        return violations


    # Check overall score
    overall_score = evaluation.get('overall_score', 0)
    if overall_score < 3:
        violations.append({
            'type': 'CONTENT_QUALITY',
            'severity': 'error',
            'issue': f'Low quality score: {overall_score}/5',
            'fix': f"Issues: {', '.join(evaluation.get('issues', []))}"
        })
    elif overall_score == 3:
        violations.append({
            'type': 'CONTENT_QUALITY',
            'severity': 'warning',
            'issue': f'Moderate quality score: {overall_score}/5',
            'fix': f"Consider improvements: {', '.join(evaluation.get('issues', []))}"
        })

    # Check for word salad
    if evaluation.get('is_word_salad', False):
        violations.append({
            'type': 'CONTENT_QUALITY',
            'severity': 'error',
            'issue': 'Content appears to be word salad or meaningless filler',
            'fix': 'Rewrite with clear educational structure and meaningful examples'
        })

    # Check individual scores
    for metric in ['coherence_score', 'relevance_score', 'educational_score', 'language_score']:
        score = evaluation.get(metric, 5)
        if score < 3:
            metric_name = metric.replace('_score', '').title()
            violations.append({
                'type': 'CONTENT_QUALITY',
                'severity': 'warning',
                'issue': f'Low {metric_name} score: {score}/5',
                'fix': f"Improve {metric_name.lower()}"
            })

    # Add recommendation-based violation
    recommendation = evaluation.get('recommendation', 'PASS')
    if recommendation == 'REWRITE':
        violations.append({
            'type': 'CONTENT_QUALITY',
            'severity': 'error',
            'issue': 'LLM recommends complete rewrite',
            'fix': f"Major issues: {', '.join(evaluation.get('issues', []))}"
        })
    elif recommendation == 'NEEDS_IMPROVEMENT':
        violations.append({
            'type': 'CONTENT_QUALITY',
            'severity': 'warning',
            'issue': 'LLM recommends improvements',
            'fix': f"Suggested: {', '.join(evaluation.get('issues', []))}"
        })

    return violations
