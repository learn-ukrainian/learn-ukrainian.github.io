# /check-gemini - Gemini Inbox Check

<skill>
name: check-gemini
description: Check for messages from Gemini and optionally process them. Use at session start or when expecting responses.
arguments: none
</skill>

## Purpose

Proactively check the message broker for any messages from Gemini. This ensures we don't miss responses and maintains the collaborative workflow.

## When to Use

- **Session start** - Always check if Gemini sent something while you were away
- **After sending a request** - Check for Gemini's response
- **Before starting new work** - See if there's pending collaborative work

## Workflow

### Step 1: Quick Check

```python
mcp__message-broker__check_inbox(for_llm="claude")
```

This returns count of unread messages.

### Step 2: Read Messages (if any)

```python
mcp__message-broker__receive_messages(for_llm="claude", unread_only=True)
```

### Step 3: Review and Act

For each message from Gemini:

1. **If it's a response to your query:**
   - Read the content
   - Acknowledge the message
   - Incorporate into your work

2. **If it's a request from Gemini:**
   - Understand what's being asked
   - Decide if you can help
   - Respond or escalate to user

3. **If it's a handoff:**
   - Full context was transferred
   - Pick up where Gemini left off
   - Continue the task

4. **If it's an escalation handoff** (task_id starts with `escalate-`):
   - Gemini exhausted fix iterations on this module
   - Parse the failure data (failed gates, blocking issues, iterations tried)
   - Show the user a summary table of all escalated modules
   - Offer to run `/module-fix {track} {num}` for each
   - After fixing, delete the failure file: `batch_state/failures/{track}/{slug}.json`
   - Acknowledge the broker message

### Step 4: Acknowledge

After processing a message:
```python
mcp__message-broker__acknowledge_message(message_id=<id>)
```

## Handling Headless Sessions

Multiple Claude sessions may run in parallel. A headless session might have already:
- Picked up Gemini's message
- Acknowledged it (marking as read)
- Completed the work

**Before assuming work is pending, check full conversation:**
```python
mcp__message-broker__get_conversation(task_id="the-task-id")
```

Look for responses from other Claude sessions.

## Example Output

```
User: /check-gemini

Claude:
📬 Checking Gemini inbox...

Found 2 unread messages:

1. [msg #45] from Gemini (2 hours ago)
   Task: c1-bio-research
   Type: response
   Preview: "Дослідження завершено. Основні факти про Данила Апостола..."

2. [msg #46] from Gemini (30 min ago)
   Task: naturalness-review
   Type: feedback
   Preview: "Перевірив текст модуля. Знайшов 3 неприродні конструкції..."

Would you like me to:
a) Read and process all messages
b) Read specific message (give number)
c) Just acknowledge and continue
```

## Integration with Session Start

This skill should be invoked automatically (or reminded) at session start:

```
# In CLAUDE.md or session init:
> CHECK INBOX AT SESSION START!
> mcp__message-broker__check_inbox(for_llm="claude")
```

## Collaboration Prompts

After checking inbox, consider proactive collaboration:

- "I'm about to write C1-BIO module. Should I ask Gemini to research while I structure?"
- "This content needs naturalness review. Want me to send to Gemini?"
- "Gemini might have insights on this historical figure. Should I query?"
