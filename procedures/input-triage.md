# Input Triage

Classify #unclassified items as #task, #note, or #instruction.

## Contract

**Pre-conditions:**
- PROCESSING.md contains items tagged #unclassified
- SCHEMA.md defines classification signals

**Post-conditions:**
- All #unclassified items are either:
  - Classified (#task/#note/#instruction) and tagged #processing, in "In Progress" section
  - Or tagged #blocked with `blocked_on:` question, in "Blocked" section
- Each classified item has `signals_matched:` and `reasoning:` fields
- **Each #task item has `duplicate_check:` field** (required — either "none" or duplicate info)

**Errors:**
- PROCESSING.md not readable → abort with "Cannot read PROCESSING.md"
- Todoist unavailable for duplicate check → skip duplicate check, log warning, continue

## Classification Signals

**See SCHEMA.md for authoritative signal definitions.** Key rules:
- 2+ task signals, 0 conflicting → #task
- 2+ note signals, 0 conflicting → #note
- Matches instruction pattern → #instruction
- Mixed or weak signals → #blocked (ask user)

## Procedure

### 1. Load items

```python
items = get_items_with_tag(PROCESSING_MD, "#unclassified")
```

```
✓ Verify: items loaded from PROCESSING.md
✗ On fail: abort "Cannot read PROCESSING.md"
```

### 2. For each item: classify and check duplicates

```python
for item in items:
    # Classify
    signals = detect_signals(item.original, SCHEMA_MD)
    reasoning = explain_classification(signals)

    if signals.task >= 2 and signals.conflicting == 0:
        classification = "#task"
        # Duplicate check is PART OF classification for tasks
        similar = todoist.search(item.original)
        item.duplicate_check = f"{similar[0].content} (ID: {similar[0].id})" if similar else "none"
    elif signals.note >= 2 and signals.conflicting == 0:
        classification = "#note"
    elif signals.instruction_pattern:
        classification = "#instruction"
    else:
        classification = "#blocked"
```

```
✓ Verify: classification determined
✓ Verify: if #task, duplicate_check field is set
→ If clear: continue to step 3
→ If blocked: add blocked_on question
```

### 3. Update PROCESSING.md

**If classified:**
```python
item.tags = [classification, "#processing"]
item.signals_matched = signals.list
item.reasoning = reasoning
move_to_section(item, "In Progress")
```

**If blocked:**
```python
item.tags = ["#unclassified", "#blocked"]
item.blocked_on = generate_clarifying_question(signals)
move_to_section(item, "Blocked")
```

```
✓ Verify: item updated in PROCESSING.md
✗ On fail: abort "Failed to update PROCESSING.md"
```

## Entry Format (After Classification)

**Classified task:** (duplicate_check is REQUIRED)
```markdown
### Item {N} #task #processing
- **source:** backlog
- **raw:** call dentist
- **classification:** task
- **duplicate_check:** none
```

**Classified task with duplicate found:**
```markdown
### Item {N} #task #processing
- **source:** backlog
- **raw:** call dentist
- **classification:** task
- **duplicate_check:** "Schedule dental checkup" (ID: abc123)
```

**Classified note/instruction:**
```markdown
### Item {N} #note #processing
- **source:** backlog
- **raw:** https://example.com/article
- **classification:** note (bookmark)
```

**Blocked item:**
```markdown
### Item {N} #unclassified #blocked
- **source:** backlog
- **raw:** dentist
- **blocked_on:** Is this a task to schedule a dentist appointment, or a note about dentist information?
```

## Examples

| Input | Classification | Key Signals |
|-------|---------------|-------------|
| "call the plumber about the leak" | #task | action_verb, clear_completion |
| "Elena learns better with visual aids" | #note | observation, no_action_implied |
| "mark groceries as done" | #instruction | completion_language, references_task |
| "dentist" | #blocked | ambiguous (task or note?) |

## Edge Cases

**Bare URL:** Classify as #note (external content default).

**Time reference without action:** "dentist tomorrow" → still ambiguous, could be reschedule instruction or new task. Block if unclear.
