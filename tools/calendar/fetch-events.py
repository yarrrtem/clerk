#!/usr/bin/env python3
"""
Fetch calendar events from Fastmail and return clean JSON.

Usage:
    python fetch-events.py [--start DATE] [--end DATE] [--calendar CALENDAR]

Examples:
    python fetch-events.py --start 2026-01-26 --end 2026-02-01
    python fetch-events.py --start today --end +7d
    python fetch-events.py --calendar work --start today --end +1d

Environment variables:
    FASTMAIL_USERNAME - Fastmail email address
    FASTMAIL_CALDAV_PASSWORD - Fastmail app password with CalDAV (Calendars) access
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import caldav
import yaml
from caldav.calendarobjectresource import Event
from icalendar import Calendar

# Load calendar aliases from config file
def load_calendar_aliases() -> dict:
    """Load calendar aliases from calendars.yaml."""
    config_path = Path(__file__).parent / "calendars.yaml"
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
    # Fallback defaults
    return {
        "personal": "Calendar",
        "birthdays": "Birthdays",
    }

CALENDAR_ALIASES = load_calendar_aliases()

# Cache for discovered calendars
_calendar_cache: dict = {}
_client = None


def get_client():
    """Get authenticated CalDAV client."""
    global _client
    if _client:
        return _client

    username = os.environ.get("FASTMAIL_USERNAME")
    password = os.environ.get("FASTMAIL_CALDAV_PASSWORD") or os.environ.get("FASTMAIL_APP_PASSWORD")

    if not username or not password:
        print("Error: FASTMAIL_USERNAME and FASTMAIL_CALDAV_PASSWORD must be set", file=sys.stderr)
        sys.exit(1)

    base_url = f"https://caldav.fastmail.com/dav/calendars/user/{username}/"
    _client = caldav.DAVClient(url=base_url, username=username, password=password)
    return _client


def discover_calendars(client) -> dict:
    """Discover available calendars and return name->calendar mapping."""
    global _calendar_cache
    if _calendar_cache:
        return _calendar_cache

    principal = client.principal()
    for cal in principal.calendars():
        _calendar_cache[cal.name] = cal

    return _calendar_cache


def parse_date(date_str: str) -> datetime:
    """Parse date string with support for relative dates."""
    if date_str == "today":
        return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    elif date_str == "tomorrow":
        return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    elif date_str.startswith("+") and date_str.endswith("d"):
        days = int(date_str[1:-1])
        return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=days)
    else:
        return datetime.fromisoformat(date_str)


def get_datetime(dt_prop) -> tuple[datetime, bool]:
    """Extract datetime from icalendar property, handling DATE vs DATE-TIME."""
    dt = dt_prop.dt
    is_all_day = not isinstance(dt, datetime)
    if is_all_day:
        dt = datetime.combine(dt, datetime.min.time())
    return dt, is_all_day


def fetch_events(
    calendar_names: list[str],
    start: datetime,
    end: datetime,
) -> list[dict]:
    """Fetch events from specified calendars."""
    client = get_client()
    available_calendars = discover_calendars(client)

    events = []

    for cal_name in calendar_names:
        # Resolve alias to actual calendar name
        actual_name = CALENDAR_ALIASES.get(cal_name, cal_name)

        calendar = available_calendars.get(actual_name)
        if not calendar:
            print(f"Warning: Calendar '{cal_name}' ({actual_name}) not found", file=sys.stderr)
            print(f"Available: {list(available_calendars.keys())}", file=sys.stderr)
            continue

        try:
            # Use search() with comp_class=Event for server-side filtering
            # This is much faster than fetching all events and filtering client-side
            cal_events = calendar.search(
                start=start,
                end=end,
                comp_class=Event,
                expand=True,  # Expand recurring events
            )

            for event in cal_events:
                try:
                    ical = Calendar.from_ical(event.data)
                    for component in ical.walk():
                        if component.name == "VEVENT":
                            dtstart = component.get("dtstart")
                            dtend = component.get("dtend")
                            summary = str(component.get("summary", ""))
                            location = str(component.get("location", "")) if component.get("location") else None

                            if dtstart:
                                start_dt, is_all_day = get_datetime(dtstart)
                                end_dt = None
                                if dtend:
                                    end_dt, _ = get_datetime(dtend)

                                events.append({
                                    "calendar": cal_name,
                                    "title": summary,
                                    "start": start_dt.isoformat(),
                                    "end": end_dt.isoformat() if end_dt else None,
                                    "all_day": is_all_day,
                                    "location": location,
                                })
                except Exception as e:
                    # Skip problematic events
                    pass

        except Exception as e:
            print(f"Warning: Failed to fetch calendar '{cal_name}': {e}", file=sys.stderr)

    # Sort by start time
    events.sort(key=lambda e: e["start"])

    return events


def list_calendars():
    """List available calendars."""
    client = get_client()
    calendars = discover_calendars(client)
    print("Available calendars:")
    for name in sorted(calendars.keys()):
        alias = next((k for k, v in CALENDAR_ALIASES.items() if v == name), None)
        if alias:
            print(f"  {name} (alias: {alias})")
        else:
            print(f"  {name}")


def main():
    parser = argparse.ArgumentParser(description="Fetch calendar events from Fastmail")
    parser.add_argument("--start", default="today", help="Start date (YYYY-MM-DD, 'today', 'tomorrow', or '+Nd')")
    parser.add_argument("--end", default="+1d", help="End date (YYYY-MM-DD or '+Nd')")
    parser.add_argument("--calendar", "-c", action="append", dest="calendars",
                        help="Calendar to fetch (work, personal, or actual name). Can specify multiple.")
    parser.add_argument("--all", action="store_true", help="Fetch from all calendars")
    parser.add_argument("--list", action="store_true", help="List available calendars")

    args = parser.parse_args()

    if args.list:
        list_calendars()
        return

    start = parse_date(args.start)
    end = parse_date(args.end)

    if args.all:
        client = get_client()
        calendars = list(discover_calendars(client).keys())
    elif args.calendars:
        calendars = args.calendars
    else:
        calendars = ["work", "personal"]  # Default

    events = fetch_events(calendars, start, end)
    print(json.dumps(events, indent=2))


if __name__ == "__main__":
    main()
