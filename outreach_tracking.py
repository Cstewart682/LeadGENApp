#!/usr/bin/env python3
"""
Outreach Tracking & Email Drafting Module

Tracks outreach activities and generates personalized email drafts.

Features:
- Track email sent/opened/replied status
- Schedule follow-up reminders
- Generate personalized email templates
- A/B test subject lines
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path
from enum import Enum
import random
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OutreachStatus(Enum):
    NOT_STARTED = "not_started"
    DRAFTED = "drafted"
    SENT = "sent"
    OPENED = "opened"
    REPLIED = "replied"
    MEETING_SCHEDULED = "meeting_scheduled"
    NOT_INTERESTED = "not_interested"
    BOUNCED = "bounced"


@dataclass
class OutreachRecord:
    """Tracks outreach to a single lead."""
    lead_id: str
    company_name: str
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    
    # Current status
    status: str = "not_started"
    
    # Outreach history
    touches: list = field(default_factory=list)  # List of touch events
    total_touches: int = 0
    
    # Email tracking
    last_email_sent: Optional[str] = None
    last_email_subject: Optional[str] = None
    last_email_opened: Optional[str] = None
    reply_received: Optional[str] = None
    
    # Follow-up scheduling
    next_followup_date: Optional[str] = None
    followup_notes: Optional[str] = None
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def add_touch(self, touch_type: str, notes: str = None):
        """Record a touch (email, call, LinkedIn message, etc.)"""
        touch = {
            'type': touch_type,
            'timestamp': datetime.now().isoformat(),
            'notes': notes
        }
        self.touches.append(touch)
        self.total_touches += 1
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)


class OutreachTracker:
    """
    Tracks outreach activities across all leads.
    """
    
    def __init__(self, filepath: str = "data/outreach.json"):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(exist_ok=True)
        self.records: dict[str, OutreachRecord] = {}
        self.load()
    
    def load(self):
        if self.filepath.exists():
            with open(self.filepath, 'r') as f:
                data = json.load(f)
                self.records = {k: OutreachRecord.from_dict(v) for k, v in data.items()}
    
    def save(self):
        with open(self.filepath, 'w') as f:
            json.dump({k: v.to_dict() for k, v in self.records.items()}, f, indent=2)
    
    def get_or_create(self, lead_id: str, company_name: str, **kwargs) -> OutreachRecord:
        """Get existing record or create new one."""
        if lead_id not in self.records:
            self.records[lead_id] = OutreachRecord(
                lead_id=lead_id,
                company_name=company_name,
                **kwargs
            )
            self.save()
        return self.records[lead_id]
    
    def update_status(self, lead_id: str, status: OutreachStatus):
        """Update outreach status for a lead."""
        if lead_id in self.records:
            self.records[lead_id].status = status.value
            self.records[lead_id].updated_at = datetime.now().isoformat()
            self.save()
    
    def record_email_sent(
        self,
        lead_id: str,
        subject: str,
        followup_days: int = 3
    ):
        """Record that an email was sent."""
        if lead_id in self.records:
            record = self.records[lead_id]
            record.status = OutreachStatus.SENT.value
            record.last_email_sent = datetime.now().isoformat()
            record.last_email_subject = subject
            record.next_followup_date = (datetime.now() + timedelta(days=followup_days)).isoformat()
            record.add_touch('email', f"Subject: {subject}")
            self.save()
    
    def record_reply(self, lead_id: str, notes: str = None):
        """Record that a reply was received."""
        if lead_id in self.records:
            record = self.records[lead_id]
            record.status = OutreachStatus.REPLIED.value
            record.reply_received = datetime.now().isoformat()
            record.next_followup_date = None  # Clear follow-up
            record.add_touch('reply_received', notes)
            self.save()
    
    def get_due_followups(self) -> list[OutreachRecord]:
        """Get records that need follow-up."""
        due = []
        now = datetime.now()
        
        for record in self.records.values():
            if record.next_followup_date:
                followup_date = datetime.fromisoformat(record.next_followup_date)
                if followup_date <= now and record.status not in [
                    OutreachStatus.REPLIED.value,
                    OutreachStatus.MEETING_SCHEDULED.value,
                    OutreachStatus.NOT_INTERESTED.value
                ]:
                    due.append(record)
        
        return sorted(due, key=lambda r: r.next_followup_date)
    
    def get_statistics(self) -> dict:
        """Get outreach statistics."""
        stats = {
            'total': len(self.records),
            'by_status': {},
            'total_touches': sum(r.total_touches for r in self.records.values()),
            'avg_touches': 0,
            'reply_rate': 0,
            'due_followups': len(self.get_due_followups())
        }
        
        # Count by status
        for record in self.records.values():
            status = record.status
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
        
        # Calculate rates
        if stats['total'] > 0:
            stats['avg_touches'] = round(stats['total_touches'] / stats['total'], 1)
            replied = stats['by_status'].get('replied', 0) + stats['by_status'].get('meeting_scheduled', 0)
            sent = sum(1 for r in self.records.values() if r.status != 'not_started')
            if sent > 0:
                stats['reply_rate'] = round(replied / sent * 100, 1)
        
        return stats


# =============================================================================
# Email Template System
# =============================================================================

@dataclass
class EmailTemplate:
    """Email template with variable substitution."""
    name: str
    subject: str
    body: str
    category: str = "general"  # first_touch, follow_up, intro, etc.
    
    def render(self, variables: dict) -> tuple[str, str]:
        """
        Render template with variables.
        
        Variables can include:
        - {company_name}
        - {contact_name}
        - {contact_first_name}
        - {title}
        - {industry}
        - {your_name}
        - {your_company}
        - {your_phone}
        - {custom_hook}  # Personalized opening
        """
        subject = self.subject
        body = self.body
        
        for key, value in variables.items():
            placeholder = "{" + key + "}"
            subject = subject.replace(placeholder, str(value) if value else "")
            body = body.replace(placeholder, str(value) if value else "")
        
        # Clean up any unreplaced variables
        subject = re.sub(r'\{[^}]+\}', '', subject)
        body = re.sub(r'\{[^}]+\}', '', body)
        
        return subject.strip(), body.strip()


class EmailDraftGenerator:
    """
    Generates personalized email drafts for outreach.
    """
    
    # Default templates
    DEFAULT_TEMPLATES = [
        # First touch templates
        EmailTemplate(
            name="industrial_intro",
            subject="Quick question about {company_name}'s maintenance needs",
            body="""Hi {contact_first_name},

I came across {company_name} and noticed you're in the {industry} space here in Calgary.

We work with several industrial and manufacturing companies in the area, helping them reduce equipment downtime and maintenance costs.

I'd love to learn more about how {company_name} currently handles maintenance and see if there might be a fit.

Would you have 15 minutes this week for a quick call?

Best regards,
{your_name}
{your_company}
{your_phone}""",
            category="first_touch"
        ),
        
        EmailTemplate(
            name="value_proposition",
            subject="Helping {company_name} reduce unplanned downtime",
            body="""Hi {contact_first_name},

Many {industry} companies we work with were struggling with unplanned equipment failures and reactive maintenance before partnering with us.

We've helped companies like yours:
• Reduce emergency repair calls by 40%
• Extend equipment life through preventive maintenance
• Lower overall maintenance costs

I'd like to share how we might be able to help {company_name} achieve similar results.

Do you have time for a brief conversation this week?

Best,
{your_name}
{your_company}""",
            category="first_touch"
        ),
        
        EmailTemplate(
            name="referral_mention",
            subject="Introduction from a fellow Calgary business",
            body="""Hi {contact_first_name},

{custom_hook}

We specialize in helping industrial companies in the Calgary area with their maintenance and facility needs.

I thought it might be worth connecting to see if we could be a resource for {company_name}.

Would you be open to a quick conversation?

Best regards,
{your_name}
{your_company}
{your_phone}""",
            category="first_touch"
        ),
        
        # Follow-up templates
        EmailTemplate(
            name="follow_up_1",
            subject="Re: {company_name} maintenance needs",
            body="""Hi {contact_first_name},

I wanted to follow up on my previous email about how we might help {company_name} with maintenance and facility services.

I understand you're busy - if now isn't a good time, I'm happy to reconnect in a few weeks.

Or if there's someone else at {company_name} I should be speaking with, I'd appreciate the introduction.

Thanks,
{your_name}""",
            category="follow_up"
        ),
        
        EmailTemplate(
            name="follow_up_2",
            subject="One more try - {company_name}",
            body="""Hi {contact_first_name},

I've reached out a couple of times about potentially helping {company_name} with maintenance services.

I'll assume the timing isn't right if I don't hear back, but wanted to leave the door open in case things change.

Feel free to reach out anytime if {company_name} needs support with:
• Preventive maintenance programs
• Emergency repairs
• Facility services

Best of luck,
{your_name}
{your_phone}""",
            category="follow_up"
        ),
        
        EmailTemplate(
            name="follow_up_value_add",
            subject="Thought you might find this useful, {contact_first_name}",
            body="""Hi {contact_first_name},

I came across an article on reducing maintenance costs in {industry} operations and thought of {company_name}.

[LINK TO RELEVANT ARTICLE OR RESOURCE]

Hope you find it useful. Happy to discuss how these strategies might apply to your situation.

Best,
{your_name}""",
            category="follow_up"
        ),
        
        # Tender/opportunity templates
        EmailTemplate(
            name="tender_response",
            subject="Re: {company_name} RFP - Qualified Local Provider",
            body="""Hi {contact_first_name},

I noticed {company_name} recently posted an RFP for maintenance services.

We're a Calgary-based company that specializes in exactly this type of work, and I wanted to introduce ourselves as a qualified local provider.

A few quick highlights:
• [X] years serving Calgary industrial clients
• [Relevant certification or capability]
• [Relevant project or client reference]

I'd welcome the opportunity to discuss our qualifications in more detail. Would you have a few minutes for a call?

Best regards,
{your_name}
{your_company}
{your_phone}""",
            category="tender"
        ),
    ]
    
    def __init__(self, your_name: str, your_company: str, your_phone: str = None):
        self.your_name = your_name
        self.your_company = your_company
        self.your_phone = your_phone or ""
        self.templates = {t.name: t for t in self.DEFAULT_TEMPLATES}
        self.custom_templates: dict[str, EmailTemplate] = {}
    
    def add_template(self, template: EmailTemplate):
        """Add a custom template."""
        self.custom_templates[template.name] = template
    
    def get_template(self, name: str) -> Optional[EmailTemplate]:
        """Get a template by name."""
        return self.custom_templates.get(name) or self.templates.get(name)
    
    def list_templates(self, category: str = None) -> list[str]:
        """List available templates."""
        all_templates = {**self.templates, **self.custom_templates}
        if category:
            return [name for name, t in all_templates.items() if t.category == category]
        return list(all_templates.keys())
    
    def generate_draft(
        self,
        template_name: str,
        lead: dict,
        custom_hook: str = None
    ) -> tuple[str, str]:
        """
        Generate an email draft for a lead.
        
        Args:
            template_name: Name of template to use
            lead: Lead dictionary with company/contact info
            custom_hook: Optional personalized opening line
        
        Returns:
            Tuple of (subject, body)
        """
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template not found: {template_name}")
        
        # Extract first name from contact name
        contact_name = lead.get('contact_name', '')
        first_name = contact_name.split()[0] if contact_name else ''
        
        variables = {
            'company_name': lead.get('company_name', 'your company'),
            'contact_name': contact_name,
            'contact_first_name': first_name or 'there',
            'title': lead.get('contact_title', ''),
            'industry': lead.get('industry', 'industrial'),
            'your_name': self.your_name,
            'your_company': self.your_company,
            'your_phone': self.your_phone,
            'custom_hook': custom_hook or '',
        }
        
        return template.render(variables)
    
    def generate_first_touch(self, lead: dict) -> tuple[str, str]:
        """Generate a first-touch email for a lead."""
        # Select appropriate template based on available info
        if lead.get('industry'):
            template_name = 'industrial_intro'
        else:
            template_name = 'value_proposition'
        
        return self.generate_draft(template_name, lead)
    
    def generate_follow_up(self, lead: dict, touch_number: int = 1) -> tuple[str, str]:
        """Generate a follow-up email."""
        if touch_number == 1:
            template_name = 'follow_up_1'
        elif touch_number == 2:
            template_name = 'follow_up_2'
        else:
            template_name = 'follow_up_value_add'
        
        return self.generate_draft(template_name, lead)
    
    def generate_ab_subjects(self, lead: dict, count: int = 3) -> list[str]:
        """Generate multiple subject line variations for A/B testing."""
        company = lead.get('company_name', 'your company')
        contact_first = lead.get('contact_name', '').split()[0] if lead.get('contact_name') else ''
        industry = lead.get('industry', 'industrial')
        
        variations = [
            f"Quick question about {company}'s maintenance needs",
            f"Helping {company} reduce downtime",
            f"{contact_first}, a question about {company}" if contact_first else f"Question about {company}",
            f"Local maintenance partner for {company}",
            f"Idea for {company}'s {industry} operations",
            f"15 minutes to discuss {company}'s needs?",
            f"Calgary company looking to help {company}",
        ]
        
        return random.sample(variations, min(count, len(variations)))


# =============================================================================
# CLI Usage
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Outreach Tracking & Email Drafting")
    print("=" * 60)
    
    # Example usage
    print("\n--- Email Draft Generator Example ---\n")
    
    generator = EmailDraftGenerator(
        your_name="John Smith",
        your_company="ABC Services Ltd",
        your_phone="(403) 555-1234"
    )
    
    sample_lead = {
        'company_name': 'Western Steel Fabricators',
        'contact_name': 'Mike Johnson',
        'contact_title': 'Plant Manager',
        'industry': 'Metal Fabrication',
    }
    
    subject, body = generator.generate_first_touch(sample_lead)
    print(f"Subject: {subject}")
    print("-" * 40)
    print(body)
    
    print("\n" + "=" * 60)
    print("Usage:")
    print("=" * 60)
    print("""
    from outreach_tracking import OutreachTracker, EmailDraftGenerator
    
    # Initialize
    tracker = OutreachTracker()
    drafter = EmailDraftGenerator(
        your_name="Your Name",
        your_company="Your Company",
        your_phone="(403) 555-0000"
    )
    
    # Generate email draft
    subject, body = drafter.generate_first_touch(lead)
    
    # Record outreach
    record = tracker.get_or_create(lead['id'], lead['company_name'])
    tracker.record_email_sent(lead['id'], subject, followup_days=3)
    
    # Check for due follow-ups
    due = tracker.get_due_followups()
    for record in due:
        print(f"Follow up with: {record.company_name}")
    
    # Get statistics
    stats = tracker.get_statistics()
    print(f"Reply rate: {stats['reply_rate']}%")
    """)
