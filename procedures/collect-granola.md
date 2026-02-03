# Collect Granola

**PRIORITY 1** — First source checked during backlog processing.

## Contract

**Pre:** Granola MCP available, `_state/granola-sync.json` exists
**Post:** New meetings returned for PROCESSING.md, updated meetings auto-written to vault_path
**Error:** MCP unavailable → log warning, continue with other sources

## Procedure

### 1. Query & filter

```python
recent = granola_mcp.list_meetings(from_date="7d")
sync_state = read_json("_state/granola-sync.json")

# Cutoff: last_collection OR 7 days ago, whichever is more recent
cutoff = max(sync_state.get("last_collection"), now() - 7.days) or (now() - 7.days)

for meeting in recent:
    if not meeting.title or not meeting.has_transcript:
        continue  # Skip empty/abandoned meetings

    # CRITICAL: Fetch details to get content_updated_at
    details = granola_mcp.get_meeting(meeting.id)
    edit_ts = details.content_updated_at  # THIS is the authoritative timestamp

    if meeting.id in sync_state["meetings"]:
        stored_ts = sync_state["meetings"][meeting.id]["granola_edited_at"]
        if edit_ts > stored_ts:
            reingestion_candidates.append((meeting, details, edit_ts))
    elif edit_ts > cutoff:
        new_meetings.append((meeting, details, edit_ts))
```

### 2. Process new meetings

```python
for meeting, details, edit_ts in new_meetings:
    notes = granola_mcp.get_meeting_notes(meeting.id)

    # Echo to user: "Storing content_updated_at: {edit_ts}"
    sync_state["meetings"][meeting.id] = {
        "title": meeting.title,
        "imported_at": now_iso(),
        "granola_edited_at": edit_ts,  # Must match content_updated_at exactly
        "vault_path": None  # Set on commit
    }
```

Return to collect-inputs.md for PROCESSING.md entry creation.

### 3. Handle re-ingestion

```python
for meeting, details, edit_ts in reingestion_candidates:
    notes = granola_mcp.get_meeting_notes(meeting.id)
    content = build_meeting_note(meeting, details, notes)
    vault_path = sync_state["meetings"][meeting.id]["vault_path"]

    if vault_path:
        write_file(vault_path, content)
        log(f"Updated: {meeting.title} at {vault_path}")
    else:
        # No vault_path yet — write to _inbox/ for re-processing
        filename = f"_inbox/{meeting.start_time[:10]}-{sanitize(meeting.title)}.md"
        write_file(filename, content)

    sync_state["meetings"][meeting.id]["granola_edited_at"] = edit_ts
    sync_state["meetings"][meeting.id]["imported_at"] = now_iso()
```

### 4. Save & return

```python
sync_state["last_collection"] = now_iso()
write_json("_state/granola-sync.json", sync_state)
return {"new_meetings": new_meetings, "updated_meetings": reingestion_candidates}
```

## Key Rule

**`content_updated_at` is the only timestamp that matters for processing.**

- `start_time` = when meeting occurred (irrelevant for sync)
- `content_updated_at` = when notes were last edited (use this)

Always echo `content_updated_at` to user before storing. Always verify stored value matches.

## Sync State Format

```json
{
  "last_collection": "2026-01-21T10:30:00Z",
  "meetings": {
    "{meeting-id}": {
      "title": "Product sync",
      "imported_at": "2026-01-20T14:00:00Z",
      "granola_edited_at": "2026-01-20T13:45:00Z",
      "vault_path": "area/path/to/file.md"
    }
  }
}
```

## Helpers

See `ingest-granola-link.md` for `build_meeting_note()` and `sanitize_filename()` definitions.
