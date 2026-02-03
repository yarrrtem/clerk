# Review Blocked

Resolve #blocked and #error items with user input, then complete processing inline.

## Contract

**Pre-conditions:**
- PROCESSING.md contains items tagged #blocked or #error

**Post-conditions:**
- All resolved items are tagged #ready-to-commit
- Unresolved items remain #blocked (user chose to skip)
- Context from user clarifications persisted to relevant area docs

**Errors:**
- PROCESSING.md not accessible → abort
- User provides invalid response → ask for clarification, don't abort

## Critical Rules

- **MUST read from PROCESSING.md** — never present items from memory
- **MUST batch max 5 items** — never overwhelm the user
- **MUST update PROCESSING.md** after resolving each batch

## Procedure

### 1. Load blocked/error items

```python
items = get_items_with_tags(PROCESSING_MD, ["#blocked", "#error"])

# Sort by priority
items.sort(key=lambda i: (
    0 if "#error" in i.tags else 1,      # errors first
    1 if "#unclassified" in i.tags else 2,  # then unclassified
    2 if "#note" in i.tags else 3,          # then notes
    3 if "#task" in i.tags else 4,          # then tasks
    4  # instructions last
))
```

```
✓ Verify: items loaded and sorted
✗ On fail: abort "Cannot read PROCESSING.md"
```

### 2. Present batch (max 5)

```python
batch = items[:5]
```

Format each item:
```
[1] "{original text}"
    → Understanding: {what the system thinks this is}
    → Question: {blocked_on or error_details}

[2] "{original text}"
    → Error: {error_details}
    → Question: Retry now, or skip?
```

```
✓ Verify: batch presented to user
✗ On fail: abort "Cannot display items"
```

### 3. Collect user responses

User responds by index:
- "1: Maintenance" — answer the blocking question
- "2: retry" — retry failed commit
- "3: skip" — remove from processing
- "1: actually this is a note" — reclassify
- Can address multiple: "1: Maintenance, 2: retry, 3: skip"

```
✓ Verify: valid response received
✗ On fail: ask for clarification, repeat step 3
```

### 4. Process each resolution

For each resolved item:

#### 4a. If #error

```python
if user_response == "retry":
    result = retry_commit(item)
    if result.success:
        remove_from_processing(item)
        log_to_action_log(item)
    else:
        item.error_details = result.error
        # Stay in error state for next batch
elif user_response == "skip":
    remove_from_processing(item)
```

#### 4b. If #unclassified #blocked

```python
classification = user_response  # e.g., "task", "note", "instruction"
item.tags.remove("#unclassified")
item.tags.remove("#blocked")
item.tags.append(f"#{classification}")
item.tags.append("#processing")

# Run full processing
if classification == "task":
    run_process_task(item)
elif classification == "note":
    run_process_note(item)
elif classification == "instruction":
    run_process_instruction(item)

# Present for inline review (step 5)
```

#### 4c. If classified #blocked (task/note/instruction)

```python
# Apply user's answer to resolve the block
resolve_block(item, user_response)

# Re-run processing to complete enrichment
reprocess(item)

# Present for inline review (step 5)
```

### 5. Inline review

After processing, present resolved item for approval:

```
Processed as {classification}:
→ {destination/target}
→ {title/content preview}
→ Priority: {p1-p4} | Labels: {labels}

Approve? (yes / edit / skip)
```

```python
if user_response == "yes" or user_response == "ok":
    item.tags.remove("#blocked")
    item.tags.append("#ready-to-commit")
    move_to_section(item, "Ready to Commit")
elif user_response.startswith("edit"):
    apply_edits(item, user_response)
    # Re-present for approval
elif user_response == "skip":
    remove_from_processing(item)
```

```
✓ Verify: item transitioned to #ready-to-commit or removed
✗ On fail: keep in current state, continue to next item
```

### 6. Persist context

```python
if contains_reusable_context(user_response):
    area_doc = identify_relevant_area(item)
    context = extract_context(user_response)
    append_to_section(area_doc, "## Context", context)
```

Example: User says "1: Maintenance — Marc is the fireplace guy"
→ Append to relevant area doc: "Marc: Fireplace company contact (Norea Foyers)"

```
✓ Verify: context persisted if applicable
✗ On fail: log warning, continue (non-blocking)
```

### 7. Repeat

```python
remaining = get_items_with_tags(PROCESSING_MD, ["#blocked", "#error"])
if remaining:
    goto step_2  # Next batch
```

## Presentation Format

**Blocked item:**
```
[1] "call the plumber about the leak"
    → Understanding: Task about home maintenance
    → Question: Which Todoist project — Maintenance or House Projects?
```

**Error item:**
```
[2] "Buy groceries" (TASK)
    → Error: Todoist API timeout after 3 retries
    → Question: Retry now, or skip?
```

**Unclassified blocked:**
```
[3] "dentist"
    → Understanding: Could be task (make appointment) or note (dentist info)
    → Question: Is this a task or a note?
```

## Edge Cases

**User skips all:** "skip all" → Remove all items without committing, log as skipped.

**Context worth persisting:** "1: Health — Dr. Smith is our family doctor at the Verdun clinic"
→ Resolve with destination=Health AND persist "Dr. Smith: Family doctor at Verdun clinic" to health/health.md.

**Reclassification with context:** "1: it's a note about her current schedule"
→ Reclassify as #note, run process-note.md, persist relevant context to area doc.
