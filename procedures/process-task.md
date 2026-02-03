# Process Task

Enrich a #task item with metadata for Todoist commit.

## Contract

**Pre-conditions:**
- Item is tagged #task #processing
- Item has `original:` field
- SCHEMA.md defines routing rules and priorities

**Post-conditions:**
- Item has required fields: `destination:`, `priority:`, `title:`
- Item has optional fields if applicable: `description:`, `labels:`, `due_string:`, `recurring:`
- Item is either #ready-to-review or #blocked

**Errors:**
- Cannot determine destination → #blocked with `blocked_on: "Which Todoist project?"`
- Context fetch fails → continue with available information

## Required Output Fields

| Field | Required | Description |
|-------|----------|-------------|
| destination | Yes | Todoist project name |
| priority | Yes | p1, p2, p3, or p4 |
| title | Yes | Concise, scannable task title |
| description | No | Only if adds value beyond title |
| labels | No | Focus level + other applicable labels |
| due_string | No | Natural language date ("tomorrow", "2025-04-01") |
| recurring | No | Recurrence pattern ("every monday", "every 6 months") |

## Procedure

### 1. Determine destination

```python
destination = match_to_project(item.original, SCHEMA_MD)
```

```
✓ Verify: destination is a valid Todoist project from SCHEMA.md
✗ On fail: set destination="Inbox" OR apply #blocked with blocked_on="Which Todoist project?"
```

Use SCHEMA.md routing rules:
- Match keywords to areas (work-related → Work, health → Health, etc.)
- Check if references existing project
- Fallback: Inbox (but prefer to block and ask)

### 2. Fetch context

```python
area_context = read_area_file(destination)  # e.g., work/work.md
related_tasks = todoist.find_tasks(project=destination, limit=5)
```

```
✓ Verify: context loaded
✗ On fail: log warning, continue without context
```

### 3. Set priority

```python
priority = determine_priority(item.original, area_context, SCHEMA_MD)
```

**See SCHEMA.md for priority criteria.** Default to p3 if unclear.

### 4. Set labels

```python
labels = []

# Focus level (pick one)
if requires_deep_focus(item):
    labels.append("protected")
elif requires_time_block(item):
    labels.append("scheduled")
else:
    labels.append("anytime")

# Other labels
if is_waiting_on_external(item):
    labels.append("waiting")
if requires_leaving_house(item):
    labels.append("errand")
if has_recurrence(item):
    labels.append("recurring")
```

### 5. Extract dates

```python
if has_specific_date(item.original):
    item.due_string = extract_date(item.original)
    # e.g., "tomorrow", "2025-04-01", "next Monday"

if has_recurrence_pattern(item.original):
    item.recurring = extract_recurrence(item.original)
    # e.g., "every 6 months", "weekly", "every monday"
    labels.append("recurring")
```

**Note:** `due_string` and `recurring` are combined at commit time.

### 6. Generate title

```python
title = create_concise_title(item.original)
```

Guidelines:
- Direct and scannable
- Start with action verb when natural
- Remove filler words
- Keep specific details that matter

```
✓ Verify: title is concise and actionable
✗ On fail: use cleaned version of original
```

### 7. Generate description (optional)

```python
if adds_value_beyond_title(item.original, title):
    description = extract_useful_context(item.original, area_context)
else:
    description = None  # Skip entirely
```

**Rules:**
- Include context not obvious from title (specifics, constraints, next steps)
- Skip if title is self-explanatory
- Never restate the title in different words
- Never include "Original: ..." — action log preserves original

### 8. Update item and transition

```python
item.destination = destination
item.priority = priority
item.title = title
item.labels = labels
if description:
    item.description = description
if due_string:
    item.due_string = due_string
if recurring:
    item.recurring = recurring

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
#task #ready-to-review
original: "call plumber about leak tomorrow"
source: backlog
destination: Maintenance
priority: p2
title: "Call plumber about leak"
labels: [anytime]
due_string: "tomorrow"
```

## Edge Cases

**Recurring task:** "change furnace filter every 6 months starting april 1"
→ due_string: "april 1", recurring: "every 6 months", labels include "recurring"

**Ambiguous destination:** "dentist appointment"
→ Could be Health or Admin. Apply #blocked with `blocked_on: "Which project — Health or Admin?"`

**Sub-project match:** "finish the CRM sync doc"
→ If sub-project "CRM Sync" exists under Work, route there instead of top-level.
