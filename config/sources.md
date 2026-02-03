# Sources

Sources are processed in priority order (1 = highest).

## 1. Granola

- **location:** Granola local cache (via MCP)
- **pending:** Meetings with `content_updated_at` since last collection OR within 7 days (whichever is more recent)
- **item_separator:** One meeting = one item
- **on_collect:** Create entry directly in PROCESSING.md, track in _state/granola-sync.json
- **on_commit:** Write to destination, update sync state with vault_path
- **re_ingest:** If `content_updated_at` > stored `granola_edited_at`, automatically update vault copy
- **notes:** Meeting notes with link back to original Granola record
- **key_field:** `content_updated_at` (edit timestamp) determines processing, NOT `start_time` (meeting date)
- **IMPORTANT:** Always check Granola first — meeting notes are high-value and time-sensitive

## 2. BACKLOG.md

- **location:** /BACKLOG.md
- **pending:** Non-empty lines
- **item_separator:** Newline
- **on_collect:** Delete line from file; if last item, leave file empty
- **on_commit:** n/a (already deleted on collect)
- **notes:** Single-line captures. File is empty when no items pending (no headers).

## 3. _inbox/

- **location:** /_inbox/*.md
- **pending:** All .md files in folder
- **item_separator:** One file = one item
- **on_collect:** Keep file (store path in source_path:)
- **on_commit:** Delete original file
- **notes:** Full notes written directly in Obsidian

## 4. Todoist Inbox

- **location:** Todoist project "Inbox"
- **pending:** All tasks in Inbox project
- **item_separator:** One task = one item
- **on_collect:** Keep task (store ID in source_id:)
- **on_commit:** Update task in place (move to destination project, set title/description/priority/labels/due)
- **notes:** Quick captures via Todoist app
