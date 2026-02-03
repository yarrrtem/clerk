# Process Instruction

Prepare an #instruction item for execution against existing Todoist tasks.

## Contract

**Pre-conditions:**
- Item is tagged #instruction #processing
- Item has `original:` field
- Todoist API is accessible for task lookup

**Post-conditions:**
- Item has required fields: `action:`, `target:`, `target_id:` (if task exists)
- Item has `parameters:` if action requires them
- Item is either #ready-to-review or #blocked

**Errors:**
- Cannot determine action → #blocked with `blocked_on: "What action?"`
- Cannot find target task → #blocked with `blocked_on: "Which task?"`
- Missing required parameters → #blocked with `blocked_on:` describing what's needed
- Todoist API unavailable → #blocked with error details

## Supported Actions

| Action | Parameters | Description |
|--------|------------|-------------|
| complete | — | Mark task as done |
| delete | — | Remove task entirely |
| reschedule | new_date | Change due date |
| reprioritize | new_priority | Change priority (p1-p4) |
| move_project | new_project | Move to different project |
| move_section | new_section | Move to different section |
| rename | new_title | Change task title |
| edit_description | new_description | Update description |
| add_label | label | Add a label |
| remove_label | label | Remove a label |
| add_comment | comment | Add comment to task |

## Procedure

### 1. Determine action

```python
action = detect_action(item.original)

action_patterns = {
    "complete": ["done", "finished", "completed", "check off", "mark done"],
    "delete": ["delete", "remove", "cancel", "nevermind", "forget"],
    "reschedule": ["move to", "postpone", "reschedule", "due", "change date"],
    "reprioritize": ["urgent", "bump", "deprioritize", "p1", "p2", "p3", "p4"],
    "move_project": ["move to project", "put in"],
    "rename": ["rename", "change title", "call it"],
    "add_label": ["add label", "tag with"],
    "remove_label": ["remove label", "untag"],
    "add_comment": ["add note", "comment", "note:"]
}
```

```
✓ Verify: action is one of supported actions
✗ On fail: apply #blocked with blocked_on="What action do you want to take on this task?"
```

### 2. Find target task

```python
# Extract task reference from original
task_reference = extract_task_reference(item.original)

# Search Todoist
matching_tasks = todoist.find_tasks(search=task_reference)

if len(matching_tasks) == 1:
    item.target = matching_tasks[0].content
    item.target_id = matching_tasks[0].id
elif len(matching_tasks) > 1:
    # Multiple matches — need user clarification
    item.candidate_tasks = matching_tasks[:5]
    apply_blocked(item, f"Multiple tasks match '{task_reference}'. Which one?")
    return
elif len(matching_tasks) == 0:
    # Check if target is in current PROCESSING.md batch
    processing_match = find_in_processing(task_reference, PROCESSING_MD)
    if processing_match:
        item.target = processing_match.title or task_reference
        item.target_id = None  # Will be resolved at commit time
    else:
        apply_blocked(item, f"Cannot find task '{task_reference}'. Which task?")
        return
```

```
✓ Verify: target identified (name and optionally ID)
✗ On fail: apply #blocked with candidates or ask for clarification
```

### 3. Extract parameters

```python
if action == "reschedule":
    item.parameters = {"new_date": extract_date(item.original)}
    if not item.parameters["new_date"]:
        apply_blocked(item, "When should this task be rescheduled to?")
        return

elif action == "reprioritize":
    item.parameters = {"new_priority": extract_priority(item.original)}
    if not item.parameters["new_priority"]:
        apply_blocked(item, "What priority? (p1, p2, p3, or p4)")
        return

elif action == "move_project":
    item.parameters = {"new_project": extract_project(item.original)}
    if not item.parameters["new_project"]:
        apply_blocked(item, "Which project should this move to?")
        return

elif action == "rename":
    item.parameters = {"new_title": extract_new_title(item.original)}
    if not item.parameters["new_title"]:
        apply_blocked(item, "What should the new title be?")
        return

elif action == "add_label" or action == "remove_label":
    item.parameters = {"label": extract_label(item.original)}
    if not item.parameters["label"]:
        apply_blocked(item, "Which label?")
        return

elif action == "add_comment":
    item.parameters = {"comment": extract_comment(item.original)}
    if not item.parameters["comment"]:
        apply_blocked(item, "What comment should be added?")
        return

else:
    item.parameters = {}  # complete, delete don't need params
```

```
✓ Verify: parameters populated if required by action
✗ On fail: apply #blocked asking for missing parameter
```

### 4. Transition

```python
item.action = action
item.tags.remove("#processing")
item.tags.append("#ready-to-review")
move_to_section(item, "Ready for Review")
```

```
✓ Verify: item in "Ready for Review" section
✗ On fail: abort "Failed to update PROCESSING.md"
```

## Entry Format (After Processing)

```markdown
### Item {N}
#instruction #ready-to-review
original: "mark groceries as done"
source: backlog
action: complete
target: "Buy groceries"
target_id: abc123
parameters: {}
```

```markdown
### Item {N}
#instruction #ready-to-review
original: "move dentist to next friday"
source: backlog
action: reschedule
target: "Dentist appointment"
target_id: def456
parameters: {"new_date": "next friday"}
```

## Edge Cases

**Multiple matching tasks:** "mark call done"
→ Finds "Call plumber", "Call dentist", "Call mom". Apply #blocked listing candidates.

**Target in current batch:** "mark buy milk as done" (where "buy milk" is Item 5 in PROCESSING.md)
→ Set target_id=None. At commit time, Item 5 is processed first, then this instruction resolves against it.

**Ambiguous action:** "dentist tomorrow"
→ Could be reschedule or new task. Apply #blocked: "Reschedule existing dentist task, or create new one?"
