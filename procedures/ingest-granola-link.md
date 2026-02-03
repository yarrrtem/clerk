# Ingest Granola Link

Process a single Granola meeting link on-demand, bypassing the normal batch flow.

## Contract

**Pre-conditions:**
- User provides a Granola meeting URL: `https://notes.granola.ai/t/{meeting-id}`
- Granola MCP server available

**Post-conditions:**
- Meeting notes written to destination (after user confirms routing)
- Sync state updated
- No PROCESSING.md involvement (direct flow)

**Errors:**
- Invalid URL format → abort with "Invalid Granola URL format"
- Meeting not found → abort with "Meeting not found in Granola"
- MCP unavailable → abort with "Granola MCP server unavailable"

## Triggers

| Trigger | Action |
|---------|--------|
| User pastes Granola link | Run this procedure |
| "ingest this meeting" + link | Run this procedure |
| "import from granola" + link | Run this procedure |

## Procedure

### 1. Parse meeting ID from URL

```python
# Expected formats:
# https://notes.granola.ai/t/{meeting-id}
# https://granola.ai/t/{meeting-id}

url_pattern = r'https?://(?:notes\.)?granola\.ai/t/([a-f0-9-]+)'
match = re.match(url_pattern, url)

if not match:
    abort("Invalid Granola URL. Expected: https://notes.granola.ai/t/{meeting-id}")

meeting_id = match.group(1)
```

### 2. Fetch meeting via MCP

```python
try:
    details = granola_mcp.get_meeting(meeting_id=meeting_id)
    notes = granola_mcp.get_meeting_notes(meeting_id=meeting_id)
except:
    abort("Could not fetch meeting from Granola. Is the MCP server running?")

if not details:
    abort(f"Meeting not found: {meeting_id}")

# Extract the edit timestamp (this is authoritative, not start_time)
content_edited_at = details.content_updated_at
```

### 3. Build meeting note

```python
content = build_meeting_note(details, notes)
```

Meeting note format:

```markdown
# {Meeting Title}

**Date:** {YYYY-MM-DD}
**Source:** [Granola](https://notes.granola.ai/t/{meeting-id})

---

{Meeting notes content}

## Participants

- {participant 1}
- {participant 2}
```

### 4. Determine routing

Analyze meeting content to suggest destination:

```python
# Check meeting title and content for area signals
signals = extract_area_signals(details.title, notes.summary)

suggested_area = match_area(signals)  # From SCHEMA.md routing keywords
date = details.start_time[:10]  # YYYY-MM-DD
sanitized_title = sanitize_filename(details.title)
suggested_path = f"{suggested_area}/{date}-{sanitized_title}.md"

# Or if project context is clear
if project_match:
    suggested_path = f"{area}/projects/{project}/{date}-{sanitized_title}.md"
```

### 5. Confirm with user

Present to user:

```
Meeting: "{title}"
Date: {date}
Participants: {count} people

Suggested destination: {suggested_path}

Options:
1. Accept suggested destination
2. Choose different area/project
3. Cancel
```

```
✓ On accept: continue to write
✓ On different: user specifies path
✗ On cancel: abort "Import cancelled"
```

### 6. Write to destination

```python
final_path = user_confirmed_path
write_file(final_path, content)
```

```
✓ Verify: file created at destination
✗ On fail: abort with error details
```

### 7. Update sync state

**Before writing:** Echo the `content_updated_at` value from the API to the user for confirmation.

```python
sync_state = read_json("_state/granola-sync.json")

# Show user: "Storing edit timestamp: {details.content_updated_at}"
sync_state["meetings"][meeting_id] = {
    "title": details.title,
    "imported_at": now_iso(),
    "granola_edited_at": details.content_updated_at,
    "vault_path": final_path
}

write_json("_state/granola-sync.json", sync_state)
```

**After writing:** Read back and confirm the stored `granola_edited_at` matches what was shown.

### 8. Confirm completion

```
Imported "{title}" to {final_path}
```

## Examples

**Scenario:** Simple import

1. User: "https://notes.granola.ai/t/abc123"
2. Fetch meeting: "Weekly Product Sync"
3. Suggest: `work/2026-01-20-weekly-product-sync.md`
4. User accepts
5. File written, sync state updated
6. "Imported 'Weekly Product Sync' to work/2026-01-20-weekly-product-sync.md"

---

**Scenario:** Import to project

1. User: "import this meeting to the CRM project: https://notes.granola.ai/t/abc123"
2. Fetch meeting: "CRM Integration Planning"
3. Suggest: `work/projects/crm-sync/2026-01-20-crm-integration-planning.md`
4. User accepts
5. File written with project context

---

**Scenario:** User overrides destination

1. User: "https://notes.granola.ai/t/abc123"
2. Fetch meeting: "Coffee Chat"
3. Suggest: `playground/2026-01-20-coffee-chat.md` (default)
4. User: "Actually put this in career/"
5. Write to: `career/2026-01-20-coffee-chat.md`

---

**Scenario:** Invalid URL

1. User: "https://example.com/meeting/123"
2. Abort: "Invalid Granola URL. Expected: https://notes.granola.ai/t/{meeting-id}"

---

**Scenario:** Already imported (no changes)

1. User provides link for previously imported meeting
2. Check sync state: meeting at `work/2026-01-15-product-sync.md`
3. Compare `content_updated_at` with stored `granola_edited_at`
4. If same: "This meeting is already up to date at {path}."
5. If user insists: proceed with re-import

---

**Scenario:** Already imported (with updates)

1. User provides link for previously imported meeting
2. Check sync state: meeting at `work/2026-01-15-product-sync.md`
3. Compare `content_updated_at` with stored `granola_edited_at`
4. If newer: "Meeting updated in Granola since last import. Update local copy?"
5. On yes: overwrite and update sync state
6. On no: keep existing version

## Area Routing Signals

When determining suggested destination, look for:

| Signal | Area |
|--------|------|
| "product", "engineering", "sales", company keywords | work |
| "family", "mom", "dad", names of family members | family |
| "house", "apartment", "renovation", "contractor" | house |
| "doctor", "gym", "therapy", "health" | health |
| "tax", "insurance", "bank", "legal" | admin |
| "interview", "networking", "job" | career |
| "course", "learn", "study", "workshop" | learning |
| (no clear signal) | playground |

These should align with routing keywords in each area's `{area}.md` file.
