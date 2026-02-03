#!/usr/bin/env python3
"""
Fetch contacts from Fastmail via CardDAV.

Usage:
    python fetch-contacts.py                    # All contacts
    python fetch-contacts.py --birthdays        # Only contacts with birthdays
    python fetch-contacts.py --search "Adam"    # Search by name
    python fetch-contacts.py --list             # List address books

Environment variables:
    FASTMAIL_USERNAME - Fastmail email address
    FASTMAIL_CARDDAV_PASSWORD - Fastmail app password with CardDAV (Contacts) access
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Optional
from xml.etree import ElementTree as ET

import requests
import vobject

# Namespaces for CardDAV XML
NAMESPACES = {
    'D': 'DAV:',
    'C': 'urn:ietf:params:xml:ns:carddav',
}


def get_credentials() -> tuple[str, str]:
    """Get CardDAV credentials.

    Uses:
        FASTMAIL_USERNAME (shared with calendar)
        FASTMAIL_CARDDAV_PASSWORD (contacts-specific, falls back to FASTMAIL_APP_PASSWORD)
    """
    username = os.environ.get("FASTMAIL_USERNAME")
    password = os.environ.get("FASTMAIL_CARDDAV_PASSWORD")

    if not username:
        print("Error: FASTMAIL_USERNAME not set", file=sys.stderr)
        sys.exit(1)

    if not password:
        print("Error: FASTMAIL_CARDDAV_PASSWORD not set", file=sys.stderr)
        sys.exit(1)

    return username, password


def get_base_url(username: str) -> str:
    """Get CardDAV base URL for user."""
    return f"https://carddav.fastmail.com/dav/addressbooks/user/{username}/"


def list_addressbooks(username: str, password: str) -> list[dict]:
    """List available address books."""
    base_url = get_base_url(username)

    # PROPFIND to discover address books
    propfind_body = '''<?xml version="1.0" encoding="UTF-8"?>
    <D:propfind xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:carddav">
        <D:prop>
            <D:displayname/>
            <D:resourcetype/>
        </D:prop>
    </D:propfind>'''

    response = requests.request(
        'PROPFIND',
        base_url,
        auth=(username, password),
        headers={
            'Content-Type': 'application/xml',
            'Depth': '1',
        },
        data=propfind_body,
    )

    if response.status_code not in (200, 207):
        print(f"Error: Failed to list address books: {response.status_code}", file=sys.stderr)
        print(f"Response: {response.text[:500]}", file=sys.stderr)
        sys.exit(1)

    # Parse response
    root = ET.fromstring(response.content)
    addressbooks = []

    for response_elem in root.findall('.//D:response', NAMESPACES):
        href = response_elem.find('D:href', NAMESPACES)
        displayname = response_elem.find('.//D:displayname', NAMESPACES)
        resourcetype = response_elem.find('.//D:resourcetype', NAMESPACES)

        # Check if it's an address book (has addressbook resourcetype)
        is_addressbook = resourcetype is not None and \
            resourcetype.find('C:addressbook', NAMESPACES) is not None

        if href is not None and is_addressbook:
            name = displayname.text if displayname is not None and displayname.text else href.text
            addressbooks.append({
                'name': name,
                'href': href.text,
            })

    return addressbooks


def fetch_contacts_from_addressbook(
    username: str,
    password: str,
    addressbook_href: str,
    search_term: Optional[str] = None,
) -> list[dict]:
    """Fetch all contacts from an address book."""
    base_url = f"https://carddav.fastmail.com{addressbook_href}"

    # REPORT query to get all vcards
    if search_term:
        # Use addressbook-query with text-match filter
        report_body = f'''<?xml version="1.0" encoding="UTF-8"?>
        <C:addressbook-query xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:carddav">
            <D:prop>
                <D:getetag/>
                <C:address-data/>
            </D:prop>
            <C:filter>
                <C:prop-filter name="FN">
                    <C:text-match collation="i;unicode-casemap" match-type="contains">{search_term}</C:text-match>
                </C:prop-filter>
            </C:filter>
        </C:addressbook-query>'''
    else:
        report_body = '''<?xml version="1.0" encoding="UTF-8"?>
        <C:addressbook-query xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:carddav">
            <D:prop>
                <D:getetag/>
                <C:address-data/>
            </D:prop>
        </C:addressbook-query>'''

    response = requests.request(
        'REPORT',
        base_url,
        auth=(username, password),
        headers={
            'Content-Type': 'application/xml',
            'Depth': '1',
        },
        data=report_body,
    )

    if response.status_code not in (200, 207):
        print(f"Error: Failed to fetch contacts: {response.status_code}", file=sys.stderr)
        return []

    # Parse response
    root = ET.fromstring(response.content)
    contacts = []

    for response_elem in root.findall('.//D:response', NAMESPACES):
        address_data = response_elem.find('.//C:address-data', NAMESPACES)

        if address_data is not None and address_data.text:
            try:
                vcard = vobject.readOne(address_data.text)
                contact = parse_vcard(vcard)
                if contact:
                    contacts.append(contact)
            except Exception as e:
                # Skip problematic vcards
                pass

    return contacts


def parse_vcard(vcard) -> Optional[dict]:
    """Parse a vCard into a contact dict."""
    contact = {}

    # Full name
    if hasattr(vcard, 'fn'):
        contact['name'] = vcard.fn.value
    elif hasattr(vcard, 'n'):
        n = vcard.n.value
        parts = [n.prefix, n.given, n.additional, n.family, n.suffix]
        contact['name'] = ' '.join(p for p in parts if p).strip()

    if not contact.get('name'):
        return None

    # Birthday
    if hasattr(vcard, 'bday'):
        bday = vcard.bday.value
        if isinstance(bday, str):
            contact['birthday'] = bday
        else:
            # It's a date object
            contact['birthday'] = bday.isoformat() if hasattr(bday, 'isoformat') else str(bday)

    # Email
    if hasattr(vcard, 'email'):
        emails = vcard.contents.get('email', [])
        contact['emails'] = [e.value for e in emails]

    # Phone
    if hasattr(vcard, 'tel'):
        phones = vcard.contents.get('tel', [])
        contact['phones'] = [p.value for p in phones]

    # Organization
    if hasattr(vcard, 'org'):
        contact['organization'] = vcard.org.value[0] if vcard.org.value else None

    # Note
    if hasattr(vcard, 'note'):
        contact['note'] = vcard.note.value

    return contact


def main():
    parser = argparse.ArgumentParser(description="Fetch contacts from Fastmail via CardDAV")
    parser.add_argument("--list", action="store_true", help="List available address books")
    parser.add_argument("--addressbook", "-a", help="Address book to fetch from (default: all)")
    parser.add_argument("--birthdays", "-b", action="store_true", help="Only show contacts with birthdays")
    parser.add_argument("--search", "-s", help="Search contacts by name")
    parser.add_argument("--upcoming", "-u", type=int, metavar="DAYS",
                        help="Show birthdays in the next N days")

    args = parser.parse_args()

    username, password = get_credentials()

    if args.list:
        addressbooks = list_addressbooks(username, password)
        print("Available address books:")
        for ab in addressbooks:
            print(f"  {ab['name']}")
        return

    # Get address books
    addressbooks = list_addressbooks(username, password)

    if args.addressbook:
        addressbooks = [ab for ab in addressbooks if ab['name'] == args.addressbook]
        if not addressbooks:
            print(f"Error: Address book '{args.addressbook}' not found", file=sys.stderr)
            sys.exit(1)

    # Fetch contacts
    all_contacts = []
    for ab in addressbooks:
        contacts = fetch_contacts_from_addressbook(
            username, password, ab['href'],
            search_term=args.search
        )
        for c in contacts:
            c['addressbook'] = ab['name']
        all_contacts.extend(contacts)

    # Filter by birthdays if requested
    if args.birthdays:
        all_contacts = [c for c in all_contacts if c.get('birthday')]

    # Filter by upcoming birthdays
    if args.upcoming:
        today = datetime.now().date()
        upcoming = []
        for c in all_contacts:
            if c.get('birthday'):
                try:
                    # Parse birthday (handle various formats)
                    bday_str = c['birthday']
                    # Try different formats
                    for fmt in ['%Y-%m-%d', '%Y%m%d', '--%m-%d', '%m-%d']:
                        try:
                            if fmt == '--%m-%d':
                                bday = datetime.strptime(bday_str, fmt).date()
                            else:
                                bday = datetime.strptime(bday_str[:len('YYYY-MM-DD')], fmt).date()
                            break
                        except:
                            continue
                    else:
                        continue

                    # Calculate next occurrence this year
                    this_year_bday = bday.replace(year=today.year)
                    if this_year_bday < today:
                        this_year_bday = this_year_bday.replace(year=today.year + 1)

                    days_until = (this_year_bday - today).days
                    if days_until <= args.upcoming:
                        c['days_until_birthday'] = days_until
                        c['next_birthday'] = this_year_bday.isoformat()
                        upcoming.append(c)
                except:
                    pass

        # Sort by days until birthday
        upcoming.sort(key=lambda c: c.get('days_until_birthday', 999))
        all_contacts = upcoming

    # Sort by name
    all_contacts.sort(key=lambda c: c.get('name', '').lower())

    print(json.dumps(all_contacts, indent=2))


if __name__ == "__main__":
    main()
