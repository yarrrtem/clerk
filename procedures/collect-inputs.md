# Collect Inputs

Gather pending items from all sources into PROCESSING.md.

## Contract

**Pre-conditions:**
- SOURCES.md defines input sources and their rules
- PROCESSING.md exists

**Post-conditions:**
- All pending items from all sources are in PROCESSING.md "Incoming" section
- Each item tagged #unclassified
- Each item has `original:`, `source:` fields
- Source-specific fields populated (`source_path:` for _inbox/, `source_id:` for Todoist)
- `on_collect:` rules from SOURCES.md applied

**Errors:**
- PROCESSING.md not writable → abort with "Cannot write to PROCESSING.md"
- Todoist API unavailable → skip Todoist source, log warning, continue
- Image analysis fails → create entry with "[Image: analysis failed]", continue

## Procedure

### 1. Initialize

```python
item_number = get_last_item_number(PROCESSING_MD) + 1
```

### 2. Process each source

Process sources in priority order from SOURCES.md:

#### 2.1 Granola (Priority 1) — ALWAYS CHECK FIRST

**IMPORTANT:** Granola must be checked first. Meeting notes are high-value and time-sensitive.

```python
# Call collect-granola procedure - creates entries directly in PROCESSING.md
granola_items = run_procedure("collect-granola.md")

for meeting in granola_items.new_meetings:
    create_entry(
        number=item_number++,
        original=meeting.summary,
        source="granola",
        source_id=meeting.id,
        meeting_title=meeting.title,
        meeting_date=meeting.start_time[:10],
        tags=["#unclassified"]
    )

for meeting in granola_items.updated_meetings:
    # Updated meetings are auto-written to their vault_path
    # Log but don't create new entry
    log(f"Auto-updated: {meeting.title} at {meeting.vault_path}")
```

```
✓ Verify: new meetings create entries, updated meetings logged
✗ On fail: log "Granola collection failed", continue with other sources
```

#### 2.2 BACKLOG.md (Priority 2)

```python
lines = read_non_empty_lines("BACKLOG.md")

for line in lines:
    create_entry(
        number=item_number++,
        original=line,
        source="backlog",
        tags=["#unclassified"]
    )
    delete_line_from("BACKLOG.md", line)  # on_collect rule
```

```
✓ Verify: each line creates exactly one entry
✗ On fail: log "Failed to process line: {line}", continue
```

#### 2.3 _inbox/ (Priority 3)

```python
files = glob("_inbox/*.md")

for file in files:
    content = read(file)
    create_entry(
        number=item_number++,
        original=content,
        source="inbox",
        source_path=file,
        tags=["#unclassified"]
    )
    # Keep file until commit (on_collect rule)
```

```
✓ Verify: each file creates exactly one entry
✗ On fail: log "Failed to process file: {file}", continue
```

#### 2.4 Todoist Inbox (Priority 4)

```python
inbox_tasks = todoist.find_tasks(project="Inbox")

for task in inbox_tasks:
    create_entry(
        number=item_number++,
        original=task.content,
        source="todoist",
        source_id=task.id,
        tags=["#unclassified"]
    )
    # Keep task until commit (on_collect rule)
```

```
✓ Verify: each task creates exactly one entry
✗ On fail: log "Failed to process task: {task.id}", continue
```

### 3. Handle images

If item is or contains an image:

```python
if is_image(item):
    analysis = analyze_image(item)

    if analysis.type == "whiteboard_or_list":
        # Extract individual items
        for extracted in analysis.items:
            create_entry(
                number=item_number++,
                original=extracted,
                source="backlog (image)",
                tags=["#unclassified"]
            )
    else:
        # Single entry with description
        create_entry(
            number=item_number++,
            original=f"[Image: {analysis.description}]",
            source="backlog (image)",
            tags=["#unclassified"]
        )

    move_file(item, "_attachments/")
```

```
✓ Verify: image moved to _attachments/
✗ On fail: log "Failed to move image", continue
```

### 4. Write to PROCESSING.md

Append all entries to "Incoming" section:

```markdown
### Item {N}
#unclassified
original: "{verbatim content}"
source: {source}
source_path: {path}  <!-- if _inbox/ -->
source_id: {id}      <!-- if Todoist -->
```

```
✓ Verify: PROCESSING.md updated with all entries
✗ On fail: abort "Failed to write PROCESSING.md: {error}"
```

## Entry Format

```markdown
### Item {N}
#unclassified
original: "{verbatim content}"
source: backlog | inbox | todoist | backlog (image)
source_path: {path}  <!-- _inbox/ items only -->
source_id: {id}      <!-- Todoist items only -->
```

## Edge Cases

**Image of whiteboard:** Creates separate entry for each extracted item, moves image to _attachments/.

**Todoist API unavailable:** Log warning, skip Todoist source, continue with other sources.

**Granola MCP unavailable:** Log warning, continue with other sources.
