#!/usr/bin/env python3
"""
Tender & RFP Monitoring Module

Monitors public procurement opportunities from:
- Alberta Purchasing Connection (APC)
- MERX (Canadian public tenders)
- City of Calgary (SAP Ariba)
- CanadaBuys (Federal)

Sends alerts when new relevant tenders are posted.
"""

import os
import re
import json
import hashlib
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Optional
from pathlib import Path

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Tender:
    """Represents a tender/RFP opportunity."""
    id: str
    title: str
    organization: str
    source: str
    url: str
    closing_date: Optional[str] = None
    posted_date: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    value: Optional[str] = None
    description: Optional[str] = None
    relevance_score: int = 0
    seen_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)


class TenderDatabase:
    """Simple JSON-based storage for seen tenders."""
    
    def __init__(self, filepath: str = "data/tenders.json"):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(exist_ok=True)
        self.tenders: dict[str, Tender] = {}
        self.load()
    
    def load(self):
        if self.filepath.exists():
            with open(self.filepath, 'r') as f:
                data = json.load(f)
                self.tenders = {k: Tender.from_dict(v) for k, v in data.items()}
    
    def save(self):
        with open(self.filepath, 'w') as f:
            json.dump({k: v.to_dict() for k, v in self.tenders.items()}, f, indent=2)
    
    def add(self, tender: Tender) -> bool:
        """Add tender if not already seen. Returns True if new."""
        if tender.id not in self.tenders:
            self.tenders[tender.id] = tender
            self.save()
            return True
        return False
    
    def get_new_tenders(self, since: datetime = None) -> list[Tender]:
        """Get tenders added since a given time."""
        if since is None:
            since = datetime.now() - timedelta(days=1)
        
        new_tenders = []
        for tender in self.tenders.values():
            seen_at = datetime.fromisoformat(tender.seen_at)
            if seen_at >= since:
                new_tenders.append(tender)
        
        return sorted(new_tenders, key=lambda t: t.relevance_score, reverse=True)


class TenderMonitor:
    """
    Monitors multiple tender sources for relevant opportunities.
    """
    
    def __init__(
        self,
        keywords: list[str] = None,
        categories: list[str] = None,
        locations: list[str] = None
    ):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Default keywords for industrial services
        self.keywords = keywords or [
            'maintenance', 'repair', 'hvac', 'plumbing', 'electrical',
            'mechanical', 'facilities', 'janitorial', 'cleaning',
            'landscaping', 'snow removal', 'equipment', 'service',
            'preventive maintenance', 'building', 'construction'
        ]
        
        # Categories to monitor
        self.categories = categories or [
            'Construction Services',
            'Maintenance',
            'Facility Services',
            'Building Services',
            'Equipment',
            'HVAC',
            'Electrical',
            'Plumbing'
        ]
        
        # Locations to monitor
        self.locations = locations or [
            'Alberta',
            'Calgary',
            'Edmonton',
            'Red Deer',
            'Lethbridge'
        ]
        
        self.db = TenderDatabase()
    
    def calculate_relevance(self, tender: Tender) -> int:
        """
        Calculate relevance score (0-100) based on keywords, category, location.
        """
        score = 0
        
        # Combine searchable text
        text = f"{tender.title} {tender.description or ''} {tender.category or ''}".lower()
        
        # Keyword matching (max 50 points)
        keyword_matches = sum(1 for kw in self.keywords if kw.lower() in text)
        score += min(keyword_matches * 10, 50)
        
        # Category matching (max 25 points)
        if tender.category:
            for cat in self.categories:
                if cat.lower() in tender.category.lower():
                    score += 25
                    break
        
        # Location matching (max 25 points)
        location_text = f"{tender.location or ''} {tender.organization}".lower()
        for loc in self.locations:
            if loc.lower() in location_text:
                score += 25
                break
        
        return min(score, 100)
    
    # =========================================================================
    # Alberta Purchasing Connection (APC)
    # =========================================================================
    
    def fetch_apc_tenders(self) -> list[Tender]:
        """
        Fetch tenders from Alberta Purchasing Connection.
        
        Note: APC doesn't have a public API, so we scrape the public listing.
        """
        tenders = []
        
        try:
            # APC public tender listing
            url = "https://purchasing.alberta.ca/search"
            
            response = self.session.get(url, timeout=30)
            
            if response.status_code != 200:
                logger.warning(f"APC fetch failed: {response.status_code}")
                return tenders
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Parse tender listings (structure may vary)
            # This is a simplified example - actual parsing depends on APC's HTML structure
            for item in soup.select('.opportunity-item, .tender-row, tr[data-id]'):
                try:
                    title_elem = item.select_one('.title, .opportunity-title, td:first-child a')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    link = title_elem.get('href', '')
                    
                    if not link.startswith('http'):
                        link = f"https://purchasing.alberta.ca{link}"
                    
                    # Generate unique ID
                    tender_id = f"apc_{hashlib.md5(link.encode()).hexdigest()[:12]}"
                    
                    # Extract other details
                    org_elem = item.select_one('.organization, .buyer, td:nth-child(2)')
                    org = org_elem.get_text(strip=True) if org_elem else "Government of Alberta"
                    
                    date_elem = item.select_one('.closing-date, .deadline, td:nth-child(3)')
                    closing = date_elem.get_text(strip=True) if date_elem else None
                    
                    tender = Tender(
                        id=tender_id,
                        title=title,
                        organization=org,
                        source="Alberta Purchasing Connection",
                        url=link,
                        closing_date=closing,
                        location="Alberta"
                    )
                    
                    tender.relevance_score = self.calculate_relevance(tender)
                    tenders.append(tender)
                    
                except Exception as e:
                    logger.debug(f"Error parsing APC item: {e}")
                    continue
            
            logger.info(f"Fetched {len(tenders)} tenders from APC")
            
        except Exception as e:
            logger.error(f"Error fetching APC tenders: {e}")
        
        return tenders
    
    # =========================================================================
    # MERX
    # =========================================================================
    
    def fetch_merx_tenders(self, province: str = "alberta") -> list[Tender]:
        """
        Fetch tenders from MERX for a given province.
        
        Note: MERX requires subscription for full access. This fetches public listings.
        """
        tenders = []
        
        try:
            # MERX public Alberta listings
            url = f"https://www.merx.com/public/solicitations/{province}"
            
            response = self.session.get(url, timeout=30)
            
            if response.status_code != 200:
                logger.warning(f"MERX fetch failed: {response.status_code}")
                return tenders
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Parse tender listings
            for item in soup.select('.solicitation-row, .tender-item, tr.solicitation'):
                try:
                    title_elem = item.select_one('a.title, .solicitation-title a, td a')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    link = title_elem.get('href', '')
                    
                    if not link.startswith('http'):
                        link = f"https://www.merx.com{link}"
                    
                    tender_id = f"merx_{hashlib.md5(link.encode()).hexdigest()[:12]}"
                    
                    org_elem = item.select_one('.buyer-name, .organization')
                    org = org_elem.get_text(strip=True) if org_elem else "Unknown"
                    
                    category_elem = item.select_one('.category, .commodity')
                    category = category_elem.get_text(strip=True) if category_elem else None
                    
                    tender = Tender(
                        id=tender_id,
                        title=title,
                        organization=org,
                        source="MERX",
                        url=link,
                        category=category,
                        location="Alberta"
                    )
                    
                    tender.relevance_score = self.calculate_relevance(tender)
                    tenders.append(tender)
                    
                except Exception as e:
                    logger.debug(f"Error parsing MERX item: {e}")
                    continue
            
            logger.info(f"Fetched {len(tenders)} tenders from MERX")
            
        except Exception as e:
            logger.error(f"Error fetching MERX tenders: {e}")
        
        return tenders
    
    # =========================================================================
    # CanadaBuys (Federal)
    # =========================================================================
    
    def fetch_canadabuys_tenders(self) -> list[Tender]:
        """
        Fetch tenders from CanadaBuys (federal procurement).
        """
        tenders = []
        
        try:
            # CanadaBuys API endpoint for open tenders
            url = "https://canadabuys.canada.ca/en/tender-opportunities"
            
            response = self.session.get(url, timeout=30)
            
            if response.status_code != 200:
                logger.warning(f"CanadaBuys fetch failed: {response.status_code}")
                return tenders
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for item in soup.select('.tender-item, .views-row'):
                try:
                    title_elem = item.select_one('a, .title a')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    link = title_elem.get('href', '')
                    
                    if not link.startswith('http'):
                        link = f"https://canadabuys.canada.ca{link}"
                    
                    tender_id = f"cb_{hashlib.md5(link.encode()).hexdigest()[:12]}"
                    
                    tender = Tender(
                        id=tender_id,
                        title=title,
                        organization="Government of Canada",
                        source="CanadaBuys",
                        url=link,
                        location="Canada"
                    )
                    
                    tender.relevance_score = self.calculate_relevance(tender)
                    
                    # Only include if relevant to Alberta
                    if tender.relevance_score > 0:
                        tenders.append(tender)
                    
                except Exception as e:
                    logger.debug(f"Error parsing CanadaBuys item: {e}")
                    continue
            
            logger.info(f"Fetched {len(tenders)} relevant tenders from CanadaBuys")
            
        except Exception as e:
            logger.error(f"Error fetching CanadaBuys tenders: {e}")
        
        return tenders
    
    # =========================================================================
    # Main Monitoring
    # =========================================================================
    
    def check_all_sources(self, min_relevance: int = 20) -> list[Tender]:
        """
        Check all tender sources and return new relevant tenders.
        
        Args:
            min_relevance: Minimum relevance score to include (0-100)
        
        Returns:
            List of new tenders above relevance threshold
        """
        all_tenders = []
        
        # Fetch from all sources
        all_tenders.extend(self.fetch_apc_tenders())
        all_tenders.extend(self.fetch_merx_tenders())
        all_tenders.extend(self.fetch_canadabuys_tenders())
        
        # Filter and add new tenders
        new_tenders = []
        for tender in all_tenders:
            if tender.relevance_score >= min_relevance:
                if self.db.add(tender):
                    new_tenders.append(tender)
        
        logger.info(f"Found {len(new_tenders)} new relevant tenders")
        
        return sorted(new_tenders, key=lambda t: t.relevance_score, reverse=True)
    
    def get_summary_report(self, tenders: list[Tender]) -> str:
        """Generate a summary report of tenders."""
        if not tenders:
            return "No new relevant tenders found."
        
        report = []
        report.append(f"Found {len(tenders)} New Tender Opportunities")
        report.append("=" * 50)
        report.append("")
        
        for i, tender in enumerate(tenders, 1):
            report.append(f"{i}. {tender.title}")
            report.append(f"   Organization: {tender.organization}")
            report.append(f"   Source: {tender.source}")
            report.append(f"   Relevance: {tender.relevance_score}/100")
            if tender.closing_date:
                report.append(f"   Closing: {tender.closing_date}")
            report.append(f"   URL: {tender.url}")
            report.append("")
        
        return "\n".join(report)


class TenderAlertService:
    """
    Sends alerts when new relevant tenders are found.
    """
    
    def __init__(
        self,
        smtp_host: str = "smtp.gmail.com",
        smtp_port: int = 587,
        smtp_user: str = None,
        smtp_password: str = None,
        from_email: str = None,
        to_emails: list[str] = None
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_email = from_email or smtp_user
        self.to_emails = to_emails or []
    
    def send_email_alert(self, subject: str, body: str, html_body: str = None) -> bool:
        """Send an email alert."""
        if not self.smtp_user or not self.to_emails:
            logger.warning("Email not configured. Skipping alert.")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            
            msg.attach(MIMEText(body, 'plain'))
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Alert email sent to {len(self.to_emails)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def send_tender_alert(self, tenders: list[Tender]) -> bool:
        """Send an alert about new tenders."""
        if not tenders:
            return False
        
        subject = f"🔔 {len(tenders)} New Tender Opportunities Found"
        
        # Plain text body
        body = f"Found {len(tenders)} new relevant tender opportunities:\n\n"
        for tender in tenders:
            body += f"• {tender.title}\n"
            body += f"  Organization: {tender.organization}\n"
            body += f"  Relevance: {tender.relevance_score}/100\n"
            body += f"  Link: {tender.url}\n\n"
        
        # HTML body
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>🔔 {len(tenders)} New Tender Opportunities</h2>
            <p>The following new tenders match your criteria:</p>
        """
        
        for tender in tenders:
            relevance_color = "#28a745" if tender.relevance_score >= 50 else "#ffc107" if tender.relevance_score >= 30 else "#6c757d"
            html += f"""
            <div style="border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px;">
                <h3 style="margin: 0 0 10px 0;">
                    <a href="{tender.url}" style="color: #1e3a5f;">{tender.title}</a>
                </h3>
                <p style="margin: 5px 0;"><strong>Organization:</strong> {tender.organization}</p>
                <p style="margin: 5px 0;"><strong>Source:</strong> {tender.source}</p>
                <p style="margin: 5px 0;">
                    <strong>Relevance:</strong> 
                    <span style="background: {relevance_color}; color: white; padding: 2px 8px; border-radius: 3px;">
                        {tender.relevance_score}/100
                    </span>
                </p>
                {f'<p style="margin: 5px 0;"><strong>Closing:</strong> {tender.closing_date}</p>' if tender.closing_date else ''}
            </div>
            """
        
        html += """
            <p style="color: #666; font-size: 12px; margin-top: 20px;">
                This alert was generated by your Lead Generator tender monitoring system.
            </p>
        </body>
        </html>
        """
        
        return self.send_email_alert(subject, body, html)


# =============================================================================
# Scheduler for Automated Monitoring
# =============================================================================

def run_scheduled_check(
    monitor: TenderMonitor,
    alert_service: TenderAlertService = None,
    min_relevance: int = 20
):
    """
    Run a scheduled tender check.
    
    This function can be called by a scheduler (cron, Windows Task Scheduler, etc.)
    or run in a loop with time.sleep().
    """
    logger.info("Starting scheduled tender check...")
    
    new_tenders = monitor.check_all_sources(min_relevance=min_relevance)
    
    if new_tenders:
        report = monitor.get_summary_report(new_tenders)
        print(report)
        
        if alert_service:
            alert_service.send_tender_alert(new_tenders)
    else:
        logger.info("No new relevant tenders found.")
    
    return new_tenders


# =============================================================================
# CLI Usage
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Tender Monitoring System")
    print("=" * 60)
    
    # Create monitor with custom keywords for your business
    monitor = TenderMonitor(
        keywords=[
            'maintenance', 'hvac', 'plumbing', 'electrical', 'mechanical',
            'facilities', 'building services', 'repair', 'installation',
            'preventive maintenance', 'equipment service'
        ],
        locations=['Alberta', 'Calgary', 'Edmonton']
    )
    
    print("\nChecking for tenders...")
    print("-" * 60)
    
    # Check all sources
    new_tenders = monitor.check_all_sources(min_relevance=20)
    
    # Print report
    print(monitor.get_summary_report(new_tenders))
    
    print("\n" + "=" * 60)
    print("To set up email alerts:")
    print("=" * 60)
    print("""
    from tender_monitoring import TenderMonitor, TenderAlertService
    
    monitor = TenderMonitor(
        keywords=['your', 'service', 'keywords'],
        locations=['Calgary', 'Alberta']
    )
    
    alert_service = TenderAlertService(
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        smtp_user="your-email@gmail.com",
        smtp_password="your-app-password",  # Use App Password for Gmail
        to_emails=["alerts@yourcompany.com"]
    )
    
    # Run check and send alerts
    new_tenders = monitor.check_all_sources()
    if new_tenders:
        alert_service.send_tender_alert(new_tenders)
    
    # For automated monitoring, set up a cron job or scheduled task:
    # Run every hour: 0 * * * * python tender_monitoring.py
    """)
