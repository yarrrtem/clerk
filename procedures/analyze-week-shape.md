# Analyze Week Shape

Classify the overall shape of a week for weekly check-in planning.

## Contract

**Pre:** Calendar events for the week available
**Post:** Returns week shape classification with confidence
**Error:** No events → default to normal_work

## Week Shapes

| Shape | Description | Planning Implications |
|-------|-------------|----------------------|
| `normal_work` | Standard 5-day work week | Full task planning |
| `vacation` | 3+ days of leave | Minimal tasks, pre/post prep |
| `parental_leave` | On parental leave | Family focus, emergencies only |
| `off_site` | Work off-site/retreat | Work focus, limited personal |
| `travel` | Multiple travel days | Reduced capacity, travel tasks |
| `light_week` | < 50% normal meeting load | Deep work opportunity |
| `heavy_week` | > 150% normal meeting load | Survival mode, quick tasks |

## Procedure

### 1. Analyze each day

```python
week_start = get_monday(target_week)
day_types = {}

for i in range(7):
    day = week_start + timedelta(days=i)
    day_events = [e for e in events if e["start"].date() == day]
    day_types[day] = analyze_day_type(day, day_events)
```

### 2. Count special days

```python
leave_days = sum(1 for dt in day_types.values()
                 if dt["type"] in ["leave", "parental_leave", "holiday"])

parental_days = sum(1 for dt in day_types.values()
                    if dt["type"] == "parental_leave")

off_site_days = sum(1 for dt in day_types.values()
                    if dt["type"] == "off_site")

work_days = sum(1 for dt in day_types.values()
                if "work" in dt["type"])

# Calculate total meeting hours for the week
total_meeting_hours = sum(
    dt.get("meeting_hours", 0) for dt in day_types.values()
)
```

### 3. Classify week shape

```python
# Priority order: most specific first

if parental_days >= 3:
    return {
        "shape": "parental_leave",
        "confidence": "high",
        "details": f"{parental_days} parental leave days"
    }

if leave_days >= 3:
    return {
        "shape": "vacation",
        "confidence": "high",
        "details": f"{leave_days} leave days"
    }

if off_site_days >= 2:
    return {
        "shape": "off_site",
        "confidence": "high",
        "details": f"{off_site_days} off-site days"
    }

# Meeting load thresholds (assuming ~20 hrs/week normal)
if total_meeting_hours > 30:
    return {
        "shape": "heavy_week",
        "confidence": "medium",
        "details": f"{total_meeting_hours:.1f} meeting hours"
    }

if total_meeting_hours < 10 and work_days >= 4:
    return {
        "shape": "light_week",
        "confidence": "medium",
        "details": f"{total_meeting_hours:.1f} meeting hours"
    }

return {
    "shape": "normal_work",
    "confidence": "medium",
    "details": f"{work_days} work days, {total_meeting_hours:.1f} meeting hours"
}
```

### 4. Store confirmed shape

After user confirms in weekly check-in:

```python
sync_state = read_json("_state/calendar-sync.json")
sync_state["week_shape"] = {
    "confirmed_at": now_iso(),
    "shape": confirmed_shape,
    "week_start": week_start.isoformat()
}
write_json("_state/calendar-sync.json", sync_state)
```

## Usage in Weekly Check-in

```python
week_shape = analyze_week_shape(this_week, events)

prompt = f"""
Looking at your calendar, this looks like a **{week_shape["shape"]}** week.
{week_shape["details"]}

Does that sound right?
"""

# User confirms or corrects
if user_confirms:
    store_week_shape(week_shape)
else:
    corrected = get_user_correction()
    store_week_shape(corrected)
```

## Notes

- Week shape affects which areas get attention
- Off-site weeks: focus on work, defer house/admin
- Vacation weeks: pre-trip prep, post-trip catch-up
- Heavy weeks: protect health, defer non-urgent
