# Commit Reviewed

Execute all #ready-to-commit items: create tasks, write notes, run instructions.

## Contract

**Pre-conditions:**
- PROCESSING.md contains items tagged #ready-to-commit
- Todoist API is accessible
- Vault is writable

**Post-conditions:**
- Successfully committed items are logged to ACTION_LOG.md and removed from PROCESSING.md
- Failed items are tagged #error with `error_details:`, in "Error" section
- Source cleanup rules applied (BACKLOG.md lines deleted, _inbox/ files removed, Todoist tasks updated)

**Errors:**
- Todoist API fails → retry 3x, then tag #error
- Vault write fails → retry 3x, then tag #error
- Instruction target not found → tag #blocked

## Procedure

### 1. Load items

```python
items = get_items_with_tag(PROCESSING_MD, "#ready-to-commit")

# Process in order: tasks first (instructions may depend on them)
items.sort(key=lambda i: (
    0 if "#task" in i.tags else 1,
    1 if "#note" in i.tags else 2,
    2  # instructions last
))
```

```
✓ Verify: items loaded
✗ On fail: abort "Cannot read PROCESSING.md"
```

### 2. Commit each item

#### 2a. Commit #note items

**If appending to existing file (media/bookmark):**

```python
if item.append_to_section:
    file_content = read(item.destination)

    # Find or create section
    section_content = find_section(file_content, item.append_to_section)

    if item.media_entry:
        # Append media entry
        new_content = append_to_section(
            file_content,
            item.append_to_section,
            item.media_entry
        )
    elif item.bookmark_entry:
        # Append bookmark entry
        new_content = append_to_section(
            file_content,
            item.append_to_section,
            item.bookmark_entry
        )

    write(item.destination, new_content)

    # Also create task if flagged
    if item.create_task:
        todoist.add_task(
            content=item.task_title,
            project=item.task_project,
            priority=priority_to_int(item.task_priority),
            labels=["anytime"]
        )
```

**If creating new file (general note):**

```python
else:
    file_path = f"{item.destination}/{item.filename}"
    content = item.content

    # Add wiki links if present
    if item.links:
        content += "\n\n## Related\n"
        for link in item.links:
            content += f"- [[{link}]]\n"

    write(file_path, content)
```

```
✓ Verify: file written/updated successfully
✗ On fail: retry 3x, then tag #error
```

#### 2b. Commit #task items

```python
# Build due string
due_string = None
if item.due_string and item.recurring:
    due_string = f"{item.due_string} {item.recurring}"
elif item.due_string:
    due_string = item.due_string
elif item.recurring:
    due_string = item.recurring

# Create task
result = todoist.add_task(
    content=item.title,
    description=item.description or "",
    project=item.destination,
    priority=priority_to_int(item.priority),  # p1→4, p2→3, p3→2, p4→1
    labels=item.labels or [],
    due_string=due_string
)

item.todoist_id = result.id
```

```
✓ Verify: task created with ID returned
✗ On fail: retry 3x, then tag #error
```

#### 2c. Commit #instruction items

```python
# Resolve target if needed
if not item.target_id:
    # Target might be another item in this batch
    target_item = find_in_processing(item.target, PROCESSING_MD)
    if target_item and target_item.todoist_id:
        item.target_id = target_item.todoist_id
    else:
        apply_blocked(item, "Target task not ready")
        continue

# Execute action
if item.action == "complete":
    todoist.complete_task(item.target_id)

elif item.action == "delete":
    todoist.delete_task(item.target_id)

elif item.action == "reschedule":
    todoist.update_task(item.target_id, due_string=item.parameters["new_date"])

elif item.action == "reprioritize":
    todoist.update_task(item.target_id, priority=item.parameters["new_priority"])

elif item.action == "move_project":
    todoist.update_task(item.target_id, project=item.parameters["new_project"])

elif item.action == "rename":
    todoist.update_task(item.target_id, content=item.parameters["new_title"])

elif item.action == "add_label":
    todoist.update_task(item.target_id, labels=[...existing, item.parameters["label"]])

elif item.action == "remove_label":
    todoist.update_task(item.target_id, labels=[...existing - item.parameters["label"]])

elif item.action == "add_comment":
    todoist.add_comment(item.target_id, content=item.parameters["comment"])
```

```
✓ Verify: action executed successfully
✗ On fail: retry 3x, then tag #error
```

### 3. Source cleanup

```python
# From SOURCES.md on_commit rules
if item.source == "backlog":
    pass  # Already deleted on collect

elif item.source == "inbox":
    delete_file(item.source_path)

elif item.source == "todoist":
    # Task was in Inbox, now updated in place
    # (moved to destination project with all metadata)
    pass
```

```
✓ Verify: source cleanup completed
✗ On fail: log warning, continue (non-critical)
```

### 4. Log success

```python
append_to_action_log(item)
remove_from_processing(item)
```

Log format:
```markdown
### {date} Process Backlog

**Created ({count} new tasks):**
- {destination}: "{title}" ({priority}, {labels})

**Created ({count} notes):**
- {destination}

**Updated ({count} tasks):**
- {destination}: "{title}" — {change description}

**Completed ({count} tasks):**
- "{title}"
```

```
✓ Verify: logged and removed from PROCESSING.md
✗ On fail: abort "Failed to update state"
```

### 5. Handle errors

```python
if commit_failed_after_retries:
    item.tags.remove("#ready-to-commit")
    item.tags.append("#error")
    item.error_details = error_message
    move_to_section(item, "Error")
```

```
✓ Verify: failed items in Error section
✗ On fail: log critical error
```

## Priority Mapping

Todoist uses inverted priority numbers:
| Our Priority | Todoist Priority |
|--------------|------------------|
| p1 (urgent)  | 4                |
| p2 (high)    | 3                |
| p3 (normal)  | 2                |
| p4 (low)     | 1                |

## ACTION_LOG.md Format

```markdown
### {date} Process Backlog

**Created ({N} new tasks):**
- {Project}: "{Title}" ({priority}, {labels}) — {description if notable}

**Created ({N} notes):**
- {destination/filename}

**Updated ({N} tasks):**
- {Project}: "{Title}" — moved from Inbox, updated priority to p2

**Completed ({N} tasks):**
- "{Title}"

**Skipped:**
- "{original}" — {reason}

**Corrections:**
- Item N: {what was corrected}
```

## Edge Cases

**Instruction target is in same batch:**

Input:
```markdown
### Item 5
#task #ready-to-commit
title: "Buy milk"
...

### Item 6
#instruction #ready-to-commit
action: complete
target: "Buy milk"
target_id: None
```

Behavior:
1. Process Item 5 first (task)
2. Item 5 gets todoist_id after creation
3. Process Item 6, resolve target_id from Item 5
4. Complete the task

---

**Edge case:** API failure

Behavior:
- Retry 3 times with backoff
- If still failing, tag #error with details
- Continue processing other items
- Errors will be addressed in review-blocked
