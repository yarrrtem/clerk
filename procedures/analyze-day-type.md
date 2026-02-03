# Analyze Day Type

Classify a day based on calendar events to determine appropriate task filtering.

## Contract

**Pre:** Calendar events for the target date available
**Post:** Returns day type classification
**Error:** No events → default to work_day (weekday) or weekend

## Day Types

| Type | Description | Task Implications |
|------|-------------|-------------------|
| `work_day` | Normal weekday with meetings | All tasks available |
| `work_day_light` | Weekday, < 2 hours meetings | Good for deep work |
| `work_day_heavy` | Weekday, > 4 hours meetings | Quick tasks only |
| `weekend` | Saturday or Sunday | House projects, no work tasks |
| `leave` | Vacation, PTO, time off | Personal tasks only |
| `parental_leave` | Parental leave day | Minimal tasks, family focus |
| `off_site` | Work off-site or travel | Work tasks, limited availability |
| `holiday` | Public holiday | Personal tasks, relaxation |

## Procedure

### 1. Check day of week

```python
day_of_week = date.weekday()  # 0=Monday, 6=Sunday

if day_of_week >= 5:  # Saturday or Sunday
    return {"type": "weekend", "confidence": "high"}
```

### 2. Check for all-day events (work calendar)

```python
work_events = [e for e in events if e["calendar"] == "work"]
all_day_events = [e for e in work_events if e["all_day"]]

for event in all_day_events:
    title = event["title"].lower()

    # Holiday detection
    if any(kw in title for kw in ["holiday", "jour férié", "statutory"]):
        return {"type": "holiday", "confidence": "high"}

    # Leave detection
    if any(kw in title for kw in ["vacation", "pto", "leave", "off", "congé", "vacances"]):
        if any(kw in title for kw in ["parental", "paternity", "maternity"]):
            return {"type": "parental_leave", "confidence": "high"}
        return {"type": "leave", "confidence": "high"}

    # Off-site detection
    if any(kw in title for kw in ["off-site", "offsite", "retreat", "travel"]):
        return {"type": "off_site", "confidence": "high"}
```

### 3. Calculate meeting load

```python
timed_events = [e for e in work_events if not e["all_day"]]

meeting_hours = 0
for event in timed_events:
    duration = (event["end"] - event["start"]).total_seconds() / 3600
    meeting_hours += duration
```

### 4. Classify by meeting load

```python
if meeting_hours > 4:
    return {"type": "work_day_heavy", "confidence": "medium", "meeting_hours": meeting_hours}
elif meeting_hours < 2:
    return {"type": "work_day_light", "confidence": "medium", "meeting_hours": meeting_hours}
else:
    return {"type": "work_day", "confidence": "medium", "meeting_hours": meeting_hours}
```

## Usage in Check-ins

```python
day_type = analyze_day_type(today, events)

if day_type["type"] in ["leave", "parental_leave", "vacation", "holiday"]:
    # Exclude work tasks
    filter_out_area("work")

elif day_type["type"] == "weekend":
    # Allow house projects, exclude work
    filter_out_area("work")
    prioritize_area("house")

elif day_type["type"] == "work_day_heavy":
    # Suggest quick tasks only
    prefer_label("anytime")

elif day_type["type"] == "work_day_light":
    # Good for deep work
    allow_label("protected")
```

## Notes

- Checks work calendar for leave/off-site (that's where they're typically marked)
- Personal calendar events don't affect day type (they're commitments, not availability)
- Meeting hours only count work calendar events
