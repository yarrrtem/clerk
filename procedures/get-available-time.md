# Get Available Time

Calculate available vs meeting time for a day to inform task recommendations.

## Contract

**Pre:** Calendar events for the target date available
**Post:** Returns time breakdown with fragmentation assessment
**Error:** No events → assume full availability

## Output Format

```python
{
    "total_work_hours": 8,        # Assumed work day length
    "meeting_hours": 3.5,         # Sum of meeting durations
    "available_hours": 4.5,       # total - meetings
    "has_protected_block": True,  # 2+ hour gap exists
    "longest_block": 2.5,         # Longest uninterrupted gap
    "fragmentation": "low"        # low/medium/high
}
```

## Procedure

### 1. Define work window

```python
# Typical work day: 9 AM to 5 PM
work_start = time(9, 0)
work_end = time(17, 0)
total_work_hours = 8

# Can be adjusted based on day type
if day_type == "work_day_light":
    total_work_hours = 8
elif day_type == "work_day_heavy":
    total_work_hours = 8  # Same hours, less available
```

### 2. Calculate meeting time

```python
work_events = [e for e in events if e["calendar"] == "work" and not e["all_day"]]

meeting_hours = 0
meeting_blocks = []

for event in work_events:
    start = max(event["start"].time(), work_start)
    end = min(event["end"].time(), work_end)

    if start < end:  # Event overlaps work hours
        duration = (datetime.combine(date.today(), end) -
                   datetime.combine(date.today(), start)).total_seconds() / 3600
        meeting_hours += duration
        meeting_blocks.append((start, end))

# Sort meeting blocks by start time
meeting_blocks.sort(key=lambda x: x[0])
```

### 3. Find gaps between meetings

```python
gaps = []
current = work_start

for block_start, block_end in meeting_blocks:
    if block_start > current:
        gap_hours = (datetime.combine(date.today(), block_start) -
                    datetime.combine(date.today(), current)).total_seconds() / 3600
        gaps.append(gap_hours)
    current = max(current, block_end)

# Final gap to end of day
if current < work_end:
    gap_hours = (datetime.combine(date.today(), work_end) -
                datetime.combine(date.today(), current)).total_seconds() / 3600
    gaps.append(gap_hours)
```

### 4. Assess fragmentation

```python
available_hours = total_work_hours - meeting_hours
longest_block = max(gaps) if gaps else available_hours
has_protected_block = longest_block >= 2.0

# Fragmentation based on number and size of gaps
if len(gaps) <= 2 and longest_block >= 2:
    fragmentation = "low"    # Few gaps, good focus blocks
elif len(gaps) <= 4 and longest_block >= 1:
    fragmentation = "medium" # Some gaps, can do medium tasks
else:
    fragmentation = "high"   # Many small gaps, quick tasks only
```

### 5. Return result

```python
return {
    "total_work_hours": total_work_hours,
    "meeting_hours": round(meeting_hours, 1),
    "available_hours": round(available_hours, 1),
    "has_protected_block": has_protected_block,
    "longest_block": round(longest_block, 1),
    "fragmentation": fragmentation,
    "gap_count": len(gaps)
}
```

## Usage in Daily Check-in

```python
available = get_available_time(today, events)

if available["fragmentation"] == "high":
    # Recommend quick tasks only
    suggest_label("anytime")
    message = f"Fragmented day ({available['gap_count']} gaps). Quick tasks recommended."

elif available["has_protected_block"]:
    # Can suggest deep work
    allow_label("protected")
    message = f"{available['longest_block']}h block available for focused work."

else:
    # Medium tasks
    suggest_label("scheduled")
    message = f"{available['available_hours']}h available in smaller blocks."
```

## Notes

- Only counts work calendar events (personal events are separate commitments)
- Protected blocks = 2+ hours uninterrupted
- Fragmentation affects task recommendations, not capacity
