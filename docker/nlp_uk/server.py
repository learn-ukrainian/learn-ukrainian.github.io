#!/usr/bin/env python3
"""
nlp_uk HTTP API Server for VESUM Word Validation

Provides a simple REST API to validate Ukrainian words against VESUM dictionary.

Endpoints:
    GET  /health          - Health check
    POST /validate        - Validate words exist in VESUM
    POST /tag             - Tag text with POS tags
    POST /lemmatize       - Get lemmas for words

Example:
    curl -X POST http://localhost:8899/validate \
         -H "Content-Type: application/json" \
         -d '{"words": ["привіт", "кушать", "їсти"]}'

    Response:
    {
        "results": {
            "привіт": {"valid": true, "pos": "noun"},
            "кушать": {"valid": false, "suggestion": null},
            "їсти": {"valid": true, "pos": "verb"}
        },
        "invalid_words": ["кушать"],
        "valid_count": 2,
        "invalid_count": 1
    }
"""

import json
import os
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from flask import Flask, request, jsonify

app = Flask(__name__)

NLP_UK_DIR = "/opt/nlp_uk"
GRADLE_CMD = "/opt/gradle/latest/bin/gradle"


def run_tag_text(text: str, show_unknown: bool = True) -> tuple[str, list[str]]:
    """Run nlp_uk tagText on input text, return tagged XML and unknown words."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(text)
        input_file = f.name

    try:
        # Build gradle args
        args = f"-i {input_file}"
        if show_unknown:
            args += " -su"  # Show unknown words

        # Run tagText
        result = subprocess.run(
            [GRADLE_CMD, "--no-daemon", "--offline", "tagText", "-PlocalLib", f"-Pargs={args}"],
            cwd=NLP_UK_DIR,
            capture_output=True,
            text=True,
            timeout=60
        )

        # Read output files
        tagged_file = input_file.replace('.txt', '.tagged.xml')
        unknown_file = input_file.replace('.txt', '.unknown.txt')

        tagged_xml = ""
        unknown_words = []

        if os.path.exists(tagged_file):
            with open(tagged_file, 'r') as f:
                tagged_xml = f.read()
            os.unlink(tagged_file)

        if os.path.exists(unknown_file):
            with open(unknown_file, 'r') as f:
                unknown_words = [line.strip() for line in f if line.strip()]
            os.unlink(unknown_file)

        return tagged_xml, unknown_words

    finally:
        if os.path.exists(input_file):
            os.unlink(input_file)
        # Clean up any .good.txt files too
        good_file = input_file.replace('.txt', '.good.txt')
        if os.path.exists(good_file):
            os.unlink(good_file)


def parse_tagged_xml(xml_content: str) -> tuple[dict, list[str]]:
    """
    Parse tagged XML to extract word info and unknown words.

    Returns:
        Tuple of (word_info dict, unknown_words list)
    """
    word_info = {}
    unknown_words = []

    try:
        root = ET.fromstring(xml_content)
        for token_reading in root.iter('tokenReading'):
            # Get the first token (primary reading)
            tokens = list(token_reading.iter('token'))
            if not tokens:
                continue

            token = tokens[0]
            word = token.get('value', '')
            lemma = token.get('lemma', word)
            tags = token.get('tags', '')

            if not word:
                continue

            word_lower = word.lower()

            # Check if word is unknown
            if tags == 'unknown' or tags == 'unclass' or lemma == '':
                unknown_words.append(word)
                word_info[word_lower] = {
                    'valid': False,
                    'lemma': lemma,
                    'tags': tags,
                    'reason': 'not_in_vesum'
                }
            else:
                # Extract POS from tags (e.g., "noun:inanim:m:v_naz" -> "noun")
                pos = tags.split(':')[0] if tags else ''
                word_info[word_lower] = {
                    'valid': True,
                    'lemma': lemma,
                    'pos': pos,
                    'tags': tags
                }
    except ET.ParseError as e:
        print(f"XML parse error: {e}")

    return word_info, unknown_words


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'service': 'nlp_uk-vesum',
        'version': '1.0.0'
    })


@app.route('/validate', methods=['POST'])
def validate_words():
    """
    Validate if words exist in VESUM dictionary.

    Request: {"words": ["слово1", "слово2"]}
    Response: {"results": {...}, "invalid_words": [...], "valid_count": N, "invalid_count": N}
    """
    data = request.get_json()
    if not data or 'words' not in data:
        return jsonify({'error': 'Missing "words" array in request body'}), 400

    words = data['words']
    if not isinstance(words, list):
        return jsonify({'error': '"words" must be an array'}), 400

    if not words:
        return jsonify({
            'results': {},
            'invalid_words': [],
            'valid_count': 0,
            'invalid_count': 0
        })

    # Create text with one word per line for processing
    text = '\n'.join(words)

    # Run nlp_uk tagText
    tagged_xml, _ = run_tag_text(text)

    # Parse results - now returns word_info AND unknown_words from XML
    word_info, unknown_from_xml = parse_tagged_xml(tagged_xml)
    unknown_set = set(w.lower() for w in unknown_from_xml)

    results = {}
    invalid_words = []

    for word in words:
        word_lower = word.lower()
        if word_lower in word_info:
            results[word] = word_info[word_lower]
            if not word_info[word_lower].get('valid', True):
                invalid_words.append(word)
        elif word_lower in unknown_set:
            results[word] = {'valid': False, 'reason': 'not_in_vesum'}
            invalid_words.append(word)
        else:
            # Word not in results - assume unknown
            results[word] = {'valid': False, 'reason': 'not_processed'}
            invalid_words.append(word)

    return jsonify({
        'results': results,
        'invalid_words': invalid_words,
        'valid_count': len(words) - len(invalid_words),
        'invalid_count': len(invalid_words)
    })


@app.route('/tag', methods=['POST'])
def tag_text():
    """
    Tag Ukrainian text with POS and morphological info.

    Request: {"text": "Привіт, світе!"}
    Response: {"tagged_xml": "...", "unknown_words": [...]}
    """
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'Missing "text" in request body'}), 400

    text = data['text']
    tagged_xml, unknown_words = run_tag_text(text)

    return jsonify({
        'tagged_xml': tagged_xml,
        'unknown_words': unknown_words
    })


@app.route('/lemmatize', methods=['POST'])
def lemmatize():
    """
    Get lemmas for words.

    Request: {"words": ["слова", "книги"]}
    Response: {"lemmas": {"слова": "слово", "книги": "книга"}}
    """
    data = request.get_json()
    if not data or 'words' not in data:
        return jsonify({'error': 'Missing "words" array in request body'}), 400

    words = data['words']
    text = '\n'.join(words)

    tagged_xml, _ = run_tag_text(text, show_unknown=False)
    word_info = parse_tagged_xml(tagged_xml)

    lemmas = {}
    for word in words:
        word_lower = word.lower()
        if word_lower in word_info:
            lemmas[word] = word_info[word_lower].get('lemma', word)
        else:
            lemmas[word] = word

    return jsonify({'lemmas': lemmas})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8899))
    app.run(host='0.0.0.0', port=port, debug=False)
