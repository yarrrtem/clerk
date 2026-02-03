# Review Categorized

Human review of all #ready-to-review items before commit.

## Contract

**Pre-conditions:**
- PROCESSING.md contains items tagged #ready-to-review

**Post-conditions:**
- All approved items tagged #ready-to-commit, in "Ready to Commit" section
- Skipped items removed from PROCESSING.md
- Reclassified items re-processed and approved

**Errors:**
- PROCESSING.md not accessible → abort
- Invalid user response → ask for clarification, don't abort

## Critical Rules

- **MUST read from PROCESSING.md** — never present items from memory
- **MUST batch max 5 items** — never overwhelm the user
- **MUST update PROCESSING.md** after each batch

## Procedure

### 1. Load items

```python
items = get_items_with_tag(PROCESSING_MD, "#ready-to-review")

# Sort by type: notes → tasks → instructions
items.sort(key=lambda i: (
    0 if "#note" in i.tags else 1,
    1 if "#task" in i.tags else 2,
    2  # instructions last
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

Format by type:

**Notes:**
```
[1] NOTE → {destination}
    "{content preview...}"
    Links: [[link1]], [[link2]]
```

**Tasks:**
```
[2] TASK → {destination} ({priority})
    "{title}"
    {description if present}
    Labels: [{labels}]
    Due: {due_string if present}
    ⚠️ Duplicate: "{duplicate_check}" (if not "none")
```

**Instructions:**
```
[3] INSTRUCTION → {action} on "{target}"
    Parameters: {parameters}
```

```
✓ Verify: batch presented to user
✗ On fail: abort "Cannot display items"
```

### 3. Collect user response

Valid responses:
- "ok" / "good" / "approve" — approve all items in batch
- "1: change to p1" — edit specific item
- "2: skip" / "2: duplicate" — remove item
- "3: actually this is a note" — reclassify item
- Multiple: "1: ok, 2: change to p2, 3: skip"

```
✓ Verify: response parsed
✗ On fail: ask for clarification, repeat step 3
```

### 4. Process responses

#### 4a. Approve all

```python
if response in ["ok", "good", "approve", "yes"]:
    for item in batch:
        item.tags.remove("#ready-to-review")
        item.tags.append("#ready-to-commit")
        move_to_section(item, "Ready to Commit")
```

#### 4b. Edit specific item

```python
# Response: "1: change to p1"
item = batch[index]
apply_edit(item, edit_instruction)
# Re-present single item for confirmation
```

Common edits:
- "change to p1/p2/p3/p4" — update priority
- "change destination to X" — update project
- "add label X" — add label
- "remove label X" — remove label
- "change title to X" — update title
- "due tomorrow" — add/change due date

#### 4c. Skip/remove item

```python
# Response: "2: skip" or "2: duplicate"
item = batch[index]
remove_from_processing(item)
log_skipped(item, reason=response)
```

#### 4d. Reclassify item

```python
# Response: "3: actually this is a note"
item = batch[index]
old_class = get_classification(item)
new_class = extract_new_classification(response)

item.tags.remove(f"#{old_class}")
item.tags.remove("#ready-to-review")
item.tags.append(f"#{new_class}")
item.tags.append("#processing")

# Re-run appropriate processor
if new_class == "task":
    run_process_task(item)
elif new_class == "note":
    run_process_note(item)
elif new_class == "instruction":
    run_process_instruction(item)

# Present for immediate review
present_single_item(item)
# User approves → #ready-to-commit
```

```
✓ Verify: all responses processed
✗ On fail: log error, continue to next item
```

### 5. Update PROCESSING.md

```python
save_changes(PROCESSING_MD)
```

```
✓ Verify: PROCESSING.md updated
✗ On fail: abort "Failed to save changes"
```

### 6. Repeat

```python
remaining = get_items_with_tag(PROCESSING_MD, "#ready-to-review")
if remaining:
    goto step_2  # Next batch
```

## Presentation Formats

**Note (general):**
```
[1] NOTE → famiglia/elena-visual-learning.md
    "Elena seems to learn better with visual aids — noticed she responds well to diagrams and pictures."
    Links: [[elena-development]], [[parenting-observations]]
```

**Note (media):**
```
[2] NOTE → playground/books-and-movies.md (## Books)
    "- **The Great Gatsby** (1925) — F. Scott Fitzgerald. Classic novel about the American Dream."
```

**Note (bookmark):**
```
[3] NOTE → work/bookmarks.md (## Articles)
    "### How to Build Better Products"
    Source: medium.com | Type: article
    + Task: "Read: How to Build Better Products" (p4)
```

**Task with duplicate warning:**
```
[4] TASK → Health (p2)
    "Book dentist appointment"
    Labels: [scheduled]
    ⚠️ Duplicate: "Schedule dental checkup" (ID: abc123)
```

**Task with due date:**
```
[5] TASK → Maintenance (p2, due: tomorrow)
    "Call plumber about leak"
    Labels: [anytime]
```

**Instruction:**
```
[6] INSTRUCTION → complete "Buy groceries"
    Target ID: xyz789
```

## Examples

**Mixed responses:**
```
[1] NOTE → work/meeting-notes.md
[2] TASK → Health (p3) "Dentist appointment"
    ⚠️ Duplicate: "Book dentist appointment" (ID: abc123)
[3] TASK → Admin (p4) "Review receipts"
```
User: "1: ok, 2: skip duplicate, 3: change to p2"
Result: Item 1 approved, Item 2 removed, Item 3 updated and re-presented.

**Reclassification:**
```
[1] TASK → Personal (p4) "The Great Gatsby"
```
User: "1: actually this is a book recommendation"
Result: Reclassify as #note → run process-note.md → re-present as media note → user approves.

## Edge Cases

**Empty batch:** Procedure completes successfully.

**Multiple field edits:** "2: change to p1, add label urgent, due tomorrow" → apply all, re-present.
