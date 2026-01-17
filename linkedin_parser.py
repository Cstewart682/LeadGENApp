#!/usr/bin/env python3
"""
LinkedIn Data Parser

Parses LinkedIn data exports and Sales Navigator exports to extract leads.

LinkedIn allows you to export your connections and Sales Navigator lists.
This module parses those exports and converts them to leads for the system.

IMPORTANT: This tool processes YOUR OWN LinkedIn exports.
It does not scrape LinkedIn directly (which violates their ToS).
"""

import csv
import json
import re
import logging
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LinkedInContact:
    """Parsed contact from LinkedIn export."""
    first_name: str
    last_name: str
    full_name: str = ""
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    linkedin_url: Optional[str] = None
    location: Optional[str] = None
    industry: Optional[str] = None
    connected_on: Optional[str] = None
    notes: Optional[str] = None
    tags: list = field(default_factory=list)
    
    def __post_init__(self):
        if not self.full_name:
            self.full_name = f"{self.first_name} {self.last_name}".strip()
    
    def to_lead(self) -> dict:
        """Convert to lead format for the main system."""
        return {
            'company_name': self.company or '',
            'website': None,  # LinkedIn doesn't export this
            'contact_name': self.full_name,
            'contact_title': self.title,
            'contact_email': self.email,
            'contact_phone': self.phone,
            'industry': self.industry,
            'city': self._extract_city(),
            'province': self._extract_province(),
            'source': 'LinkedIn Import',
            'notes': self.notes,
            'linkedin_url': self.linkedin_url,
        }
    
    def _extract_city(self) -> Optional[str]:
        """Extract city from location string."""
        if not self.location:
            return None
        
        # Common patterns: "Calgary, Alberta, Canada" or "Calgary Metropolitan Area"
        parts = self.location.split(',')
        if parts:
            return parts[0].strip().replace(' Metropolitan Area', '')
        return None
    
    def _extract_province(self) -> Optional[str]:
        """Extract province from location string."""
        if not self.location:
            return None
        
        # Look for province names or abbreviations
        province_map = {
            'alberta': 'AB', 'ab': 'AB',
            'british columbia': 'BC', 'bc': 'BC',
            'ontario': 'ON', 'on': 'ON',
            'quebec': 'QC', 'qc': 'QC',
            'saskatchewan': 'SK', 'sk': 'SK',
            'manitoba': 'MB', 'mb': 'MB',
        }
        
        location_lower = self.location.lower()
        for name, abbrev in province_map.items():
            if name in location_lower:
                return abbrev
        
        return None
    
    def matches_criteria(
        self,
        titles: list[str] = None,
        industries: list[str] = None,
        locations: list[str] = None,
        companies: list[str] = None
    ) -> bool:
        """Check if contact matches filter criteria."""
        
        # Title filter
        if titles:
            if not self.title:
                return False
            title_lower = self.title.lower()
            if not any(t.lower() in title_lower for t in titles):
                return False
        
        # Industry filter
        if industries:
            if not self.industry:
                return False
            industry_lower = self.industry.lower()
            if not any(i.lower() in industry_lower for i in industries):
                return False
        
        # Location filter
        if locations:
            if not self.location:
                return False
            location_lower = self.location.lower()
            if not any(loc.lower() in location_lower for loc in locations):
                return False
        
        # Company filter
        if companies:
            if not self.company:
                return False
            company_lower = self.company.lower()
            if not any(c.lower() in company_lower for c in companies):
                return False
        
        return True


class LinkedInExportParser:
    """
    Parses LinkedIn data exports.
    
    LinkedIn exports can be requested at:
    Settings > Data Privacy > Get a copy of your data
    
    The export includes a Connections.csv file with your connections.
    """
    
    # Standard column mappings for LinkedIn exports
    COLUMN_MAPS = {
        # Standard LinkedIn export
        'first_name': ['First Name', 'first_name', 'firstName'],
        'last_name': ['Last Name', 'last_name', 'lastName'],
        'email': ['Email Address', 'email', 'Email'],
        'company': ['Company', 'company', 'Organization'],
        'title': ['Position', 'Title', 'title', 'Job Title'],
        'connected_on': ['Connected On', 'connected_on', 'Connection Date'],
        'url': ['Profile URL', 'URL', 'LinkedIn URL', 'url'],
    }
    
    def __init__(self):
        self.contacts: list[LinkedInContact] = []
    
    def _find_column(self, headers: list[str], column_names: list[str]) -> Optional[int]:
        """Find column index from possible column names."""
        headers_lower = [h.lower().strip() for h in headers]
        for name in column_names:
            if name.lower() in headers_lower:
                return headers_lower.index(name.lower())
        return None
    
    def parse_connections_csv(self, filepath: str) -> list[LinkedInContact]:
        """
        Parse LinkedIn Connections.csv export.
        
        This is the standard export format from LinkedIn's data download.
        """
        contacts = []
        
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            # Skip any header rows that aren't the actual CSV header
            lines = f.readlines()
            
            # Find the actual header row (contains 'First Name' or similar)
            header_idx = 0
            for i, line in enumerate(lines):
                if 'first name' in line.lower() or 'email' in line.lower():
                    header_idx = i
                    break
            
            # Parse CSV starting from header
            reader = csv.reader(lines[header_idx:])
            headers = next(reader)
            
            # Map columns
            col_map = {}
            for field, names in self.COLUMN_MAPS.items():
                idx = self._find_column(headers, names)
                if idx is not None:
                    col_map[field] = idx
            
            # Parse rows
            for row in reader:
                if not row or len(row) < 2:
                    continue
                
                try:
                    contact = LinkedInContact(
                        first_name=row[col_map.get('first_name', 0)] if 'first_name' in col_map else '',
                        last_name=row[col_map.get('last_name', 1)] if 'last_name' in col_map else '',
                        email=row[col_map['email']] if 'email' in col_map and col_map['email'] < len(row) else None,
                        company=row[col_map['company']] if 'company' in col_map and col_map['company'] < len(row) else None,
                        title=row[col_map['title']] if 'title' in col_map and col_map['title'] < len(row) else None,
                        connected_on=row[col_map['connected_on']] if 'connected_on' in col_map and col_map['connected_on'] < len(row) else None,
                        linkedin_url=row[col_map['url']] if 'url' in col_map and col_map['url'] < len(row) else None,
                    )
                    
                    # Clean up empty strings
                    if contact.email == '':
                        contact.email = None
                    if contact.company == '':
                        contact.company = None
                    
                    contacts.append(contact)
                    
                except Exception as e:
                    logger.debug(f"Error parsing row: {e}")
                    continue
        
        self.contacts.extend(contacts)
        logger.info(f"Parsed {len(contacts)} contacts from LinkedIn export")
        return contacts
    
    def parse_sales_navigator_csv(self, filepath: str) -> list[LinkedInContact]:
        """
        Parse Sales Navigator list export.
        
        Sales Navigator exports have more fields but similar structure.
        """
        contacts = []
        
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    # Sales Navigator uses different column names
                    first_name = row.get('First Name', row.get('firstName', ''))
                    last_name = row.get('Last Name', row.get('lastName', ''))
                    
                    contact = LinkedInContact(
                        first_name=first_name,
                        last_name=last_name,
                        email=row.get('Email', row.get('email')),
                        company=row.get('Company', row.get('Account Name', row.get('company'))),
                        title=row.get('Title', row.get('Job Title', row.get('title'))),
                        linkedin_url=row.get('LinkedIn URL', row.get('Profile URL', row.get('url'))),
                        location=row.get('Location', row.get('Geography', row.get('location'))),
                        industry=row.get('Industry', row.get('industry')),
                        phone=row.get('Phone', row.get('phone')),
                    )
                    
                    contacts.append(contact)
                    
                except Exception as e:
                    logger.debug(f"Error parsing Sales Navigator row: {e}")
                    continue
        
        self.contacts.extend(contacts)
        logger.info(f"Parsed {len(contacts)} contacts from Sales Navigator export")
        return contacts
    
    def parse_generic_csv(self, filepath: str) -> list[LinkedInContact]:
        """
        Parse a generic CSV that might be from LinkedIn or similar.
        
        Attempts to auto-detect column mappings.
        """
        contacts = []
        
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    # Try to find first/last name columns
                    first_name = None
                    last_name = None
                    full_name = None
                    
                    for key, value in row.items():
                        key_lower = key.lower()
                        if 'first' in key_lower and 'name' in key_lower:
                            first_name = value
                        elif 'last' in key_lower and 'name' in key_lower:
                            last_name = value
                        elif key_lower in ['name', 'full name', 'fullname']:
                            full_name = value
                    
                    # If only full name, split it
                    if full_name and not first_name:
                        parts = full_name.split(' ', 1)
                        first_name = parts[0]
                        last_name = parts[1] if len(parts) > 1 else ''
                    
                    if not first_name:
                        continue
                    
                    # Find other columns
                    email = None
                    company = None
                    title = None
                    location = None
                    phone = None
                    url = None
                    
                    for key, value in row.items():
                        key_lower = key.lower()
                        if 'email' in key_lower and not email:
                            email = value
                        elif 'company' in key_lower or 'organization' in key_lower:
                            company = value
                        elif 'title' in key_lower or 'position' in key_lower:
                            title = value
                        elif 'location' in key_lower or 'city' in key_lower:
                            location = value
                        elif 'phone' in key_lower:
                            phone = value
                        elif 'linkedin' in key_lower or 'url' in key_lower:
                            url = value
                    
                    contact = LinkedInContact(
                        first_name=first_name or '',
                        last_name=last_name or '',
                        email=email if email else None,
                        company=company if company else None,
                        title=title if title else None,
                        location=location if location else None,
                        phone=phone if phone else None,
                        linkedin_url=url if url else None,
                    )
                    
                    contacts.append(contact)
                    
                except Exception as e:
                    logger.debug(f"Error parsing row: {e}")
                    continue
        
        self.contacts.extend(contacts)
        logger.info(f"Parsed {len(contacts)} contacts from CSV")
        return contacts
    
    def filter_contacts(
        self,
        titles: list[str] = None,
        industries: list[str] = None,
        locations: list[str] = None,
        companies: list[str] = None,
        has_email: bool = False,
        has_company: bool = True
    ) -> list[LinkedInContact]:
        """
        Filter contacts based on criteria.
        
        Args:
            titles: List of job titles to match (partial match)
            industries: List of industries to match
            locations: List of locations to match (e.g., ['Calgary', 'Alberta'])
            companies: List of company names to match
            has_email: Only include contacts with email addresses
            has_company: Only include contacts with company names
        
        Returns:
            Filtered list of contacts
        """
        filtered = []
        
        for contact in self.contacts:
            # Basic filters
            if has_email and not contact.email:
                continue
            if has_company and not contact.company:
                continue
            
            # Criteria filters
            if not contact.matches_criteria(titles, industries, locations, companies):
                continue
            
            filtered.append(contact)
        
        logger.info(f"Filtered to {len(filtered)} contacts")
        return filtered
    
    def export_to_leads(
        self,
        contacts: list[LinkedInContact] = None,
        filepath: str = "linkedin_leads.json"
    ) -> list[dict]:
        """
        Export contacts as leads in the main system format.
        """
        if contacts is None:
            contacts = self.contacts
        
        leads = [contact.to_lead() for contact in contacts]
        
        with open(filepath, 'w') as f:
            json.dump(leads, f, indent=2)
        
        logger.info(f"Exported {len(leads)} leads to {filepath}")
        return leads
    
    def get_statistics(self) -> dict:
        """Get statistics about parsed contacts."""
        stats = {
            'total': len(self.contacts),
            'with_email': sum(1 for c in self.contacts if c.email),
            'with_company': sum(1 for c in self.contacts if c.company),
            'with_title': sum(1 for c in self.contacts if c.title),
            'with_location': sum(1 for c in self.contacts if c.location),
            'unique_companies': len(set(c.company for c in self.contacts if c.company)),
            'top_companies': {},
            'top_titles': {},
            'top_locations': {},
        }
        
        # Count top values
        from collections import Counter
        
        companies = [c.company for c in self.contacts if c.company]
        stats['top_companies'] = dict(Counter(companies).most_common(10))
        
        titles = [c.title for c in self.contacts if c.title]
        stats['top_titles'] = dict(Counter(titles).most_common(10))
        
        locations = [c.location for c in self.contacts if c.location]
        stats['top_locations'] = dict(Counter(locations).most_common(10))
        
        return stats


# =============================================================================
# Convenience Functions
# =============================================================================

def parse_linkedin_export(filepath: str, export_type: str = 'auto') -> LinkedInExportParser:
    """
    Parse a LinkedIn export file.
    
    Args:
        filepath: Path to CSV file
        export_type: 'connections', 'sales_navigator', or 'auto'
    
    Returns:
        LinkedInExportParser with parsed contacts
    """
    parser = LinkedInExportParser()
    
    if export_type == 'auto':
        # Try to detect type from filename or content
        filename = Path(filepath).name.lower()
        if 'connection' in filename:
            export_type = 'connections'
        elif 'sales' in filename or 'navigator' in filename:
            export_type = 'sales_navigator'
        else:
            export_type = 'generic'
    
    if export_type == 'connections':
        parser.parse_connections_csv(filepath)
    elif export_type == 'sales_navigator':
        parser.parse_sales_navigator_csv(filepath)
    else:
        parser.parse_generic_csv(filepath)
    
    return parser


def filter_for_calgary_industrial(parser: LinkedInExportParser) -> list[LinkedInContact]:
    """
    Filter contacts for Calgary industrial/manufacturing targets.
    """
    return parser.filter_contacts(
        titles=[
            'Plant Manager', 'Operations Manager', 'Purchasing Manager',
            'Maintenance Manager', 'Facilities Manager', 'Engineering Manager',
            'Procurement', 'Buyer', 'Director of Operations', 'VP Operations',
            'General Manager', 'Owner', 'President'
        ],
        locations=['Calgary', 'Alberta', 'AB'],
        has_company=True
    )


# =============================================================================
# CLI Usage
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("LinkedIn Export Parser")
    print("=" * 60)
    print("""
How to Export Your LinkedIn Data:
----------------------------------

1. STANDARD CONNECTIONS EXPORT:
   - Go to LinkedIn > Settings > Data Privacy
   - Click "Get a copy of your data"
   - Select "Connections"
   - Download and extract the ZIP file
   - Use the Connections.csv file

2. SALES NAVIGATOR EXPORT (if you have Sales Navigator):
   - Go to your Lead List
   - Click "..." menu > "Export to CSV"
   - Use the exported CSV file

Usage:
------
    from linkedin_parser import parse_linkedin_export, filter_for_calgary_industrial
    
    # Parse your LinkedIn export
    parser = parse_linkedin_export("Connections.csv")
    
    # See statistics
    stats = parser.get_statistics()
    print(f"Total contacts: {stats['total']}")
    print(f"With email: {stats['with_email']}")
    
    # Filter for your target roles
    filtered = filter_for_calgary_industrial(parser)
    print(f"Matching contacts: {len(filtered)}")
    
    # Export as leads
    leads = parser.export_to_leads(filtered, "my_leads.json")
    
    # Or filter with custom criteria
    custom_filtered = parser.filter_contacts(
        titles=['Manager', 'Director', 'VP'],
        locations=['Calgary'],
        has_email=True
    )

Target Titles for Industrial Outreach:
--------------------------------------
- Plant Manager
- Operations Manager
- Purchasing Manager / Procurement Manager
- Maintenance Manager / Supervisor
- Facilities Manager
- Engineering Manager
- General Manager
- Owner / President
    """)
