# Process Categorized

Orchestrate processing of all classified items by delegating to type-specific procedures.

## Contract

**Pre-conditions:**
- PROCESSING.md contains items tagged #processing (with #task, #note, or #instruction)
- Items are in "In Progress" section

**Post-conditions:**
- All #processing items are now either:
  - Tagged #ready-to-review, in "Ready for Review" section
  - Or tagged #blocked with `blocked_on:` question, in "Blocked" section

**Errors:**
- Sub-procedure fails → item tagged #blocked with error details
- PROCESSING.md not accessible → abort

## Procedure

### 1. Load items

```python
processing_items = get_items_with_tag(PROCESSING_MD, "#processing")
processing_items = [i for i in processing_items if "#blocked" not in i.tags]
```

```
✓ Verify: items loaded
✗ On fail: abort "Cannot read PROCESSING.md"
```

### 2. Group by classification

```python
tasks = [i for i in processing_items if "#task" in i.tags]
notes = [i for i in processing_items if "#note" in i.tags]
instructions = [i for i in processing_items if "#instruction" in i.tags]
```

### 3. Process each group

#### 3.1 Process tasks

```
for each item in tasks:
    run @process-task.md(item)
```

```
✓ Verify: all tasks are #ready-to-review or #blocked
✗ On fail: tag item #blocked, set blocked_on with error
```

#### 3.2 Process notes

```
for each item in notes:
    run @process-note.md(item)
```

```
✓ Verify: all notes are #ready-to-review or #blocked
✗ On fail: tag item #blocked, set blocked_on with error
```

#### 3.3 Process instructions

```
for each item in instructions:
    run @process-instruction.md(item)
```

```
✓ Verify: all instructions are #ready-to-review or #blocked
✗ On fail: tag item #blocked, set blocked_on with error
```

### 4. Final verification

```
remaining = get_items_with_tag(PROCESSING_MD, "#processing")
remaining = [i for i in remaining if "#blocked" not in i.tags]
```

```
✓ Verify: remaining is empty (all items processed)
✗ On fail: log warning "Some items still in #processing state"
```

## Examples

**Input:** PROCESSING.md contains:
- Item 1: #task #processing
- Item 2: #note #processing
- Item 3: #instruction #processing

**Output:** After running:
- Item 1: #task #ready-to-review (via process-task.md)
- Item 2: #note #ready-to-review (via process-note.md)
- Item 3: #instruction #ready-to-review (via process-instruction.md)

---

**Edge case:** process-task.md can't determine destination

**Behavior:** Item stays #task but gets #blocked added, with `blocked_on: "Which Todoist project?"`

---

**Edge case:** No items in #processing state

**Behavior:** Procedure completes successfully with no changes.
