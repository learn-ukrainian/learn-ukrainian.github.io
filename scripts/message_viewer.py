#!/usr/bin/env python3
"""
Message Viewer - Web UI for Claude-Gemini Communication Archive

A simple Flask app to view, filter, and debug LLM-to-LLM messages.

Usage:
    .venv/bin/python scripts/message_viewer.py

    Then open: http://localhost:5050
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# Database path
DB_PATH = Path(__file__).parent.parent / ".mcp/servers/message-broker/messages.db"

# Also check .gemini/outbox for file-based messages
OUTBOX_PATH = Path(__file__).parent.parent / ".gemini/outbox"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Claude-Gemini Message Archive</title>
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #1a1a2e;
            color: #eee;
        }
        h1 {
            color: #00d4ff;
            border-bottom: 2px solid #00d4ff;
            padding-bottom: 10px;
        }
        .stats {
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
        }
        .stat-box {
            background: #16213e;
            padding: 15px 25px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-box .number {
            font-size: 2em;
            font-weight: bold;
            color: #00d4ff;
        }
        .stat-box .label {
            color: #888;
            font-size: 0.9em;
        }
        .filters {
            background: #16213e;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: flex;
            gap: 15px;
            align-items: center;
        }
        .filters select, .filters input {
            padding: 8px 12px;
            border-radius: 4px;
            border: 1px solid #333;
            background: #0f0f23;
            color: #eee;
        }
        .message {
            background: #16213e;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            border-left: 4px solid #333;
        }
        .message.claude { border-left-color: #ff6b6b; }
        .message.gemini { border-left-color: #4ecdc4; }
        .message-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            font-size: 0.9em;
        }
        .message-from {
            font-weight: bold;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.85em;
        }
        .message-from.claude { background: #ff6b6b; color: #000; }
        .message-from.gemini { background: #4ecdc4; color: #000; }
        .message-meta { color: #888; }
        .message-type {
            background: #333;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.8em;
        }
        .message-content {
            background: #0f0f23;
            padding: 15px;
            border-radius: 4px;
            white-space: pre-wrap;
            font-family: 'JetBrains Mono', 'Fira Code', monospace;
            font-size: 0.9em;
            max-height: 400px;
            overflow-y: auto;
        }
        .message-data {
            margin-top: 10px;
            padding: 10px;
            background: #0a0a1a;
            border-radius: 4px;
            font-size: 0.85em;
            color: #888;
        }
        .task-id {
            background: #2d2d44;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.8em;
        }
        .ack-status {
            font-size: 0.8em;
        }
        .ack-status.yes { color: #4ecdc4; }
        .ack-status.no { color: #ff6b6b; }
        .conversation-group {
            border: 1px solid #333;
            border-radius: 8px;
            margin-bottom: 25px;
            padding: 15px;
        }
        .conversation-header {
            font-weight: bold;
            color: #00d4ff;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #333;
        }
        .refresh-btn {
            background: #00d4ff;
            color: #000;
            border: none;
            padding: 8px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
        }
        .refresh-btn:hover { background: #00b8e6; }
        .outbox-section {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 2px solid #333;
        }
        .outbox-message {
            background: #1a2a1a;
            border-left-color: #4ecdc4;
        }
    </style>
</head>
<body>
    <h1>🤖 Claude-Gemini Message Archive</h1>

    <div class="stats">
        <div class="stat-box">
            <div class="number">{{ total_messages }}</div>
            <div class="label">Total Messages</div>
        </div>
        <div class="stat-box">
            <div class="number">{{ claude_messages }}</div>
            <div class="label">From Claude</div>
        </div>
        <div class="stat-box">
            <div class="number">{{ gemini_messages }}</div>
            <div class="label">From Gemini</div>
        </div>
        <div class="stat-box">
            <div class="number">{{ task_count }}</div>
            <div class="label">Tasks</div>
        </div>
    </div>

    <div class="filters">
        <label>Filter by:</label>
        <select id="fromFilter" onchange="applyFilters()">
            <option value="">All senders</option>
            <option value="claude">Claude only</option>
            <option value="gemini">Gemini only</option>
        </select>
        <select id="taskFilter" onchange="applyFilters()">
            <option value="">All tasks</option>
            {% for task in tasks %}
            <option value="{{ task }}">{{ task }}</option>
            {% endfor %}
        </select>
        <select id="typeFilter" onchange="applyFilters()">
            <option value="">All types</option>
            <option value="request">request</option>
            <option value="response">response</option>
            <option value="discussion">discussion</option>
            <option value="feedback">feedback</option>
            <option value="handoff">handoff</option>
        </select>
        <button class="refresh-btn" onclick="location.reload()">🔄 Refresh</button>
    </div>

    <div id="messages">
    {% if group_by_task %}
        {% for task_id, task_messages in conversations.items() %}
        <div class="conversation-group">
            <div class="conversation-header">
                📋 Task: {{ task_id or 'No Task ID' }} ({{ task_messages|length }} messages)
            </div>
            {% for msg in task_messages %}
            <div class="message {{ msg.from_llm }}" data-from="{{ msg.from_llm }}" data-task="{{ msg.task_id or '' }}" data-type="{{ msg.message_type }}">
                <div class="message-header">
                    <div>
                        <span class="message-from {{ msg.from_llm }}">{{ msg.from_llm|upper }}</span>
                        → <span class="message-from {{ msg.to_llm }}">{{ msg.to_llm|upper }}</span>
                        <span class="message-type">{{ msg.message_type }}</span>
                    </div>
                    <div class="message-meta">
                        #{{ msg.id }} · {{ msg.timestamp }}
                        <span class="ack-status {{ 'yes' if msg.acknowledged else 'no' }}">
                            {{ '✓ ACK' if msg.acknowledged else '○ unread' }}
                        </span>
                    </div>
                </div>
                <div class="message-content">{{ msg.content }}</div>
                {% if msg.data %}
                <div class="message-data">
                    <strong>📎 Attached Data:</strong><br>
                    {{ msg.data[:500] }}{% if msg.data|length > 500 %}...{% endif %}
                </div>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        {% endfor %}
    {% else %}
        {% for msg in messages %}
        <div class="message {{ msg.from_llm }}" data-from="{{ msg.from_llm }}" data-task="{{ msg.task_id or '' }}" data-type="{{ msg.message_type }}">
            <div class="message-header">
                <div>
                    <span class="message-from {{ msg.from_llm }}">{{ msg.from_llm|upper }}</span>
                    → <span class="message-from {{ msg.to_llm }}">{{ msg.to_llm|upper }}</span>
                    <span class="message-type">{{ msg.message_type }}</span>
                    {% if msg.task_id %}
                    <span class="task-id">{{ msg.task_id }}</span>
                    {% endif %}
                </div>
                <div class="message-meta">
                    #{{ msg.id }} · {{ msg.timestamp }}
                    <span class="ack-status {{ 'yes' if msg.acknowledged else 'no' }}">
                        {{ '✓ ACK' if msg.acknowledged else '○ unread' }}
                    </span>
                </div>
            </div>
            <div class="message-content">{{ msg.content }}</div>
            {% if msg.data %}
            <div class="message-data">
                <strong>📎 Attached Data:</strong><br>
                {{ msg.data[:500] }}{% if msg.data|length > 500 %}...{% endif %}
            </div>
            {% endif %}
        </div>
        {% endfor %}
    {% endif %}
    </div>

    {% if outbox_messages %}
    <div class="outbox-section">
        <h2>📤 Gemini Outbox (File-based)</h2>
        {% for msg in outbox_messages %}
        <div class="message outbox-message gemini">
            <div class="message-header">
                <div>
                    <span class="message-from gemini">GEMINI</span>
                    → <span class="message-from claude">CLAUDE</span>
                    <span class="message-type">signal</span>
                </div>
                <div class="message-meta">{{ msg.filename }} · {{ msg.timestamp }}</div>
            </div>
            <div class="message-content">{{ msg.message }}</div>
        </div>
        {% endfor %}
    </div>
    {% endif %}

    <script>
        function applyFilters() {
            const fromFilter = document.getElementById('fromFilter').value;
            const taskFilter = document.getElementById('taskFilter').value;
            const typeFilter = document.getElementById('typeFilter').value;

            document.querySelectorAll('.message').forEach(msg => {
                const matchFrom = !fromFilter || msg.dataset.from === fromFilter;
                const matchTask = !taskFilter || msg.dataset.task === taskFilter;
                const matchType = !typeFilter || msg.dataset.type === typeFilter;
                msg.style.display = (matchFrom && matchTask && matchType) ? 'block' : 'none';
            });
        }
    </script>
</body>
</html>
"""

def get_db():
    """Get database connection."""
    if not DB_PATH.exists():
        return None
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_messages():
    """Fetch all messages from database."""
    conn = get_db()
    if not conn:
        return []

    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, task_id, from_llm, to_llm, message_type, content, data, payload, timestamp, acknowledged, status
        FROM messages
        ORDER BY id DESC
    """)

    messages = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return messages

def get_outbox_messages():
    """Fetch messages from .gemini/outbox/"""
    import yaml

    if not OUTBOX_PATH.exists():
        return []

    messages = []
    for filepath in sorted(OUTBOX_PATH.glob("*.yaml"), reverse=True):
        try:
            with open(filepath) as f:
                data = yaml.safe_load(f)
                data['filename'] = filepath.name
                messages.append(data)
        except Exception:
            pass

    return messages

def get_stats(messages):
    """Calculate statistics."""
    return {
        'total_messages': len(messages),
        'claude_messages': sum(1 for m in messages if m['from_llm'] == 'claude'),
        'gemini_messages': sum(1 for m in messages if m['from_llm'] == 'gemini'),
        'task_count': len(set(m['task_id'] for m in messages if m['task_id'])),
        'tasks': sorted(set(m['task_id'] for m in messages if m['task_id']))
    }

def group_by_task(messages):
    """Group messages by task_id."""
    from collections import defaultdict

    groups = defaultdict(list)
    for msg in messages:
        groups[msg['task_id'] or 'no-task'].append(msg)

    # Sort each group by id ascending (chronological)
    for task_id in groups:
        groups[task_id] = sorted(groups[task_id], key=lambda m: m['id'])

    return dict(groups)

@app.route('/')
def index():
    messages = get_messages()
    outbox = get_outbox_messages()
    stats = get_stats(messages)

    return render_template_string(
        HTML_TEMPLATE,
        messages=messages,
        outbox_messages=outbox,
        conversations=group_by_task(messages),
        group_by_task=True,
        **stats
    )

@app.route('/api/messages')
def api_messages():
    """JSON API for messages."""
    messages = get_messages()
    return jsonify(messages)

@app.route('/api/stats')
def api_stats():
    """JSON API for statistics."""
    messages = get_messages()
    return jsonify(get_stats(messages))

if __name__ == '__main__':
    print(f"📬 Message Viewer starting...")
    print(f"   Database: {DB_PATH}")
    print(f"   Outbox: {OUTBOX_PATH}")
    print(f"\n   Open: http://localhost:5055\n")
    app.run(host='0.0.0.0', port=5055, debug=True)
