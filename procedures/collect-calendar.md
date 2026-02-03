# Collect Calendar

Fetch events from work and personal calendars for a date range.

## Contract

**Pre:** Fastmail credentials configured (FASTMAIL_USERNAME, FASTMAIL_APP_PASSWORD)
**Post:** Combined event list returned as JSON, sync state updated
**Error:** Script fails → abort with error message

## Calendar Sources

All calendars are accessed via Fastmail CalDAV. Google Calendar (work) syncs to Fastmail automatically.

| Alias | Fastmail Calendar | Description |
|-------|-------------------|-------------|
| `work` | (configured in fetch-events.py) | Work calendar (synced from Google) |
| `personal` | Calendar | Personal events |
| `birthdays` | Birthdays | Contact birthdays |
| `holidays` | Holidays in Canada | Public holidays |

**Note:** Calendar aliases are configured in `tools/calendar/calendars.yaml`. See `calendars.example.yaml` for format.

## Procedure

### 1. Fetch events using script

```bash
# Fetch work + personal calendars for date range
./.clerk/tools/calendar/venv/bin/python .clerk/tools/calendar/fetch-events.py \
    --calendar work \
    --calendar personal \
    --start {start_date} \
    --end {end_date}
```

**Date formats supported:**
- ISO date: `2026-01-24`
- Relative: `today`, `tomorrow`, `+7d`

**Output:** JSON array of events:

```json
[
  {
    "calendar": "work",
    "title": "SaaS Monday Sync",
    "start": "2026-01-26T10:15:00-05:00",
    "end": "2026-01-26T10:30:00-05:00",
    "all_day": false,
    "location": null
  }
]
```

### 2. Common usage patterns

**Today's events:**
```bash
./venv/bin/python fetch-events.py --start today --end +1d
```

**This week:**
```bash
./venv/bin/python fetch-events.py --start today --end +7d
```

**Specific date range:**
```bash
./venv/bin/python fetch-events.py --start 2026-01-26 --end 2026-02-02
```

**Work calendar only:**
```bash
./venv/bin/python fetch-events.py --calendar work --start today --end +1d
```

**List available calendars:**
```bash
./venv/bin/python fetch-events.py --list
```

### 3. Update sync state

```python
sync_state = read_json("_state/calendar-sync.json")
sync_state["last_sync"] = now_iso()
write_json("_state/calendar-sync.json", sync_state)
```

### 4. Return

```python
return events  # JSON array from script output
```

## Error Handling

| Error | Behavior |
|-------|----------|
| Script not found | Abort with "Calendar script missing" |
| Auth failed | Abort with "Fastmail credentials invalid" |
| Calendar not found | Warning logged, continue with other calendars |

## Performance

- ~1.8s for single day query
- ~2.0s for week query
- Server-side filtering (fast regardless of total calendar size)

## Notes

- Events are NOT stored in the vault (privacy)
- Only day/week type classifications are persisted
- Fetch fresh data for each check-in (no caching)
- Google Calendar syncs to Fastmail via CalDAV — no direct Google API needed
- Script location: `.clerk/tools/calendar/fetch-events.py`
- Requires: `caldav`, `icalendar` (installed in `.clerk/tools/calendar/venv/`)
