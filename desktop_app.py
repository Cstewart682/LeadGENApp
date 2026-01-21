#!/usr/bin/env python3
"""
Calgary Industrial Lead Generator - Desktop Version
A native Windows/Mac desktop application using Tkinter
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import json
import os
import time
import csv
from pathlib import Path
from datetime import datetime, timedelta
import webbrowser
from threading import Thread

# Import enhanced scraper
try:
    from enhanced_scraper import scrape_website, detect_signals, EnhancedWebScraper
    ENHANCED_SCRAPER_AVAILABLE = True
    print("✓ Enhanced multi-page scraper loaded")
except ImportError:
    # Fallback to basic scraper if enhanced_scraper.py not found
    import requests
    from bs4 import BeautifulSoup
    import re
    ENHANCED_SCRAPER_AVAILABLE = False
    print("⚠ Using basic scraper (enhanced_scraper.py not found)")

    def scrape_website(url):
        """Basic fallback scraper"""
        emails, phones = [], []
        try:
            if not url.startswith('http'):
                url = 'https://' + url
            r = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(r.text, 'html.parser')
            text = soup.get_text()
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = list(set(re.findall(email_pattern, text)))
            phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
            phones = list(set(re.findall(phone_pattern, text)))
        except Exception as e:
            print(f"Scrape error: {e}")
        return {'emails': emails, 'phones': phones}

    def detect_signals(url):
        """Basic fallback signal detector"""
        signals, score = [], 0
        keywords = {'rfp': 50, 'tender': 40, 'expansion': 30, 'hiring': 25, 'project': 20}
        try:
            if not url.startswith('http'):
                url = 'https://' + url
            r = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            text = r.text.lower()
            for keyword, points in keywords.items():
                if keyword in text:
                    signals.append({'keyword': keyword, 'score': points})
                    score += points
        except Exception as e:
            print(f"Signal detection error: {e}")
        return signals, min(score, 100)

# Import unified signal scoring
try:
    from unified_signal_scoring import UnifiedSignalScoring
    UNIFIED_SCORING_AVAILABLE = True
    print("✓ Unified signal scoring loaded")
except ImportError:
    UNIFIED_SCORING_AVAILABLE = False
    print("⚠ Unified signal scoring not available")

# Create data directory
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# ============================================================================
# JOBBER-STYLE COLOR SCHEME
# ============================================================================
COLORS = {
    # Primary colors (Jobber-inspired)
    'primary': '#0E73CC',      # Jobber blue
    'primary_dark': '#0A5494',
    'primary_light': '#E6F2FF',
    'secondary': '#00A3A3',    # Teal/cyan
    'secondary_dark': '#007A7A',

    # Status colors
    'success': '#2E7D32',      # Green
    'warning': '#F57C00',      # Orange
    'danger': '#D32F2F',       # Red
    'info': '#0277BD',         # Light blue

    # Neutral colors
    'bg_primary': '#F7F9FC',   # Light background
    'bg_secondary': '#FFFFFF', # White
    'bg_tertiary': '#E8EEF4',  # Light gray-blue
    'text_primary': '#212529', # Dark text
    'text_secondary': '#6C757D', # Gray text
    'text_light': '#FFFFFF',   # White text
    'border': '#DEE2E6',       # Light border

    # Signal colors
    'signal_high': '#D4EDDA',  # Light green
    'signal_med': '#FFF3CD',   # Light yellow
    'signal_low': '#E9ECEF',   # Light gray
}

# ============================================================================
# BACKEND FUNCTIONS
# ============================================================================

def load_json(path):
    """Load JSON file or return empty dict"""
    if path.exists():
        with open(path, 'r') as f:
            return json.load(f)
    return {}

def save_json(path, data):
    """Save data to JSON file"""
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


# ============================================================================
# MAIN APPLICATION CLASS
# ============================================================================

class LeadGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Calgary Industrial Lead Generator")
        self.root.geometry("1200x700")
        self.root.configure(bg=COLORS['bg_primary'])

        # Load data
        self.leads = load_json(DATA_DIR / "leads.json")
        self.config = load_json(DATA_DIR / "config.json")
        self.tenders = load_json(DATA_DIR / "tenders.json")

        # Create UI
        self.create_menu()
        self.create_stats_bar()
        self.create_notebook()

        # Update stats
        self.update_stats()

    def create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Export Leads to CSV", command=self.export_leads)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def create_stats_bar(self):
        """Create statistics bar at top"""
        stats_frame = tk.Frame(self.root, bg=COLORS['bg_primary'], height=80)
        stats_frame.pack(fill=tk.X, padx=10, pady=10)
        stats_frame.pack_propagate(False)

        # Stats labels
        self.stat_labels = {}
        stats = [
            ("Total Leads", "total"),
            ("With Email", "email"),
            ("Contacted", "contacted"),
            ("Follow-ups Due", "followup"),
            ("New Tenders", "tenders")
        ]

        for i, (label, key) in enumerate(stats):
            frame = tk.Frame(stats_frame, bg=COLORS['bg_secondary'], relief=tk.RAISED,
                           borderwidth=1, highlightbackground=COLORS['border'], highlightthickness=1)
            frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

            value_label = tk.Label(frame, text="0", font=("Arial", 20, "bold"),
                                  bg=COLORS['bg_secondary'], fg=COLORS['primary'])
            value_label.pack(pady=(10, 0))

            text_label = tk.Label(frame, text=label, font=("Arial", 9),
                                 bg=COLORS['bg_secondary'], fg=COLORS['text_secondary'])
            text_label.pack(pady=(0, 10))

            self.stat_labels[key] = value_label

    def create_notebook(self):
        """Create tabbed interface"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Create tabs
        self.create_leads_tab()
        self.create_add_tab()
        self.create_import_tab()
        self.create_outreach_tab()
        self.create_tenders_tab()
        self.create_settings_tab()

    def create_leads_tab(self):
        """Create leads management tab"""
        tab = tk.Frame(self.notebook)
        self.notebook.add(tab, text="📋 Leads")

        # Search and filter frame
        filter_frame = tk.Frame(tab)
        filter_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(filter_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.refresh_leads())
        search_entry = tk.Entry(filter_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(0, 20))

        tk.Label(filter_frame, text="Status:").pack(side=tk.LEFT, padx=(0, 5))
        self.status_filter = ttk.Combobox(filter_frame, width=15,
                                         values=["All", "New", "Contacted", "Qualified"])
        self.status_filter.set("All")
        self.status_filter.bind('<<ComboboxSelected>>', lambda e: self.refresh_leads())
        self.status_filter.pack(side=tk.LEFT, padx=(0, 20))

        tk.Button(filter_frame, text="🔄 Refresh", command=self.refresh_leads).pack(side=tk.LEFT)

        # Leads table
        table_frame = tk.Frame(tab)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical")
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal")
        hsb.pack(side=tk.BOTTOM, fill=tk.X)

        # Treeview
        columns = ("Company", "Contacts", "Signal", "Status")
        self.leads_tree = ttk.Treeview(table_frame, columns=columns, show="headings",
                                       yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.config(command=self.leads_tree.yview)
        hsb.config(command=self.leads_tree.xview)

        # Column headings
        self.leads_tree.heading("Company", text="Company")
        self.leads_tree.heading("Contacts", text="Contact Information")
        self.leads_tree.heading("Signal", text="Signal Score")
        self.leads_tree.heading("Status", text="Status")

        # Column widths
        self.leads_tree.column("Company", width=200)
        self.leads_tree.column("Contacts", width=450)
        self.leads_tree.column("Signal", width=100)
        self.leads_tree.column("Status", width=100)

        self.leads_tree.pack(fill=tk.BOTH, expand=True)

        # Double-click to edit
        self.leads_tree.bind('<Double-Button-1>', self.edit_lead)

        # Buttons
        btn_frame = tk.Frame(tab)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        tk.Button(btn_frame, text="✏️ Edit Selected", command=self.edit_lead,
                 bg=COLORS['primary'], fg=COLORS['text_light'], padx=10, pady=6).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🗑️ Delete Selected", command=self.delete_lead,
                 bg=COLORS['danger'], fg=COLORS['text_light'], padx=10, pady=6).pack(side=tk.LEFT, padx=5)

        self.refresh_leads()

    def create_add_tab(self):
        """Create add new lead tab"""
        tab = tk.Frame(self.notebook)
        self.notebook.add(tab, text="➕ Add New")

        # Create form in a frame
        form_frame = tk.Frame(tab)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Form fields
        fields = [
            ("Company Name *", "company"),
            ("Website", "website"),
            ("Industry", "industry"),
            ("Source", "source"),
            ("General Email", "email"),
            ("General Phone", "phone"),
            ("Contact Name", "contact_name"),
            ("Contact Title", "contact_title"),
        ]

        self.add_vars = {}
        row = 0

        for label, key in fields:
            tk.Label(form_frame, text=label, font=("Arial", 10, "bold")).grid(
                row=row, column=0, sticky=tk.W, pady=5)

            if key == "industry":
                var = tk.StringVar()
                widget = ttk.Combobox(form_frame, textvariable=var, width=40,
                                     values=["", "Manufacturing", "Metal Fabrication",
                                           "Oil & Gas", "Construction", "Other"])
                widget.grid(row=row, column=1, pady=5, sticky=tk.W)
            else:
                var = tk.StringVar()
                widget = tk.Entry(form_frame, textvariable=var, width=42)
                widget.grid(row=row, column=1, pady=5, sticky=tk.W)

            self.add_vars[key] = var
            row += 1

        # Notes field
        tk.Label(form_frame, text="Notes", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.NW, pady=5)
        self.add_notes = tk.Text(form_frame, width=42, height=4)
        self.add_notes.grid(row=row, column=1, pady=5, sticky=tk.W)
        row += 1

        # Buttons
        btn_frame = tk.Frame(form_frame)
        btn_frame.grid(row=row, column=1, pady=20, sticky=tk.W)

        tk.Button(btn_frame, text="➕ Add Lead", command=self.add_lead,
                 bg=COLORS['primary'], fg=COLORS['text_light'], padx=20, pady=8, font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="➕ Add & Scrape Website", command=self.add_and_scrape,
                 bg=COLORS['success'], fg=COLORS['text_light'], padx=20, pady=8, font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🗑️ Clear Form", command=self.clear_add_form,
                 bg=COLORS['text_secondary'], fg=COLORS['text_light'], padx=20, pady=8).pack(side=tk.LEFT, padx=5)

    def create_import_tab(self):
        """Create import tab"""
        tab = tk.Frame(self.notebook)
        self.notebook.add(tab, text="📁 Import")

        # LinkedIn Import section
        li_frame = tk.LabelFrame(tab, text="Import from LinkedIn", padx=20, pady=20)
        li_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(li_frame, text="1. Export connections from LinkedIn (Settings > Data Privacy > Connections)",
                wraplength=600, justify=tk.LEFT).pack(anchor=tk.W, pady=(0, 10))
        tk.Label(li_frame, text="2. Select the Connections.csv file below",
                wraplength=600, justify=tk.LEFT).pack(anchor=tk.W, pady=(0, 10))

        self.li_filter_var = tk.BooleanVar(value=True)
        tk.Checkbutton(li_frame, text="Only import target titles (managers, directors, etc.)",
                      variable=self.li_filter_var).pack(anchor=tk.W, pady=(0, 10))

        tk.Button(li_frame, text="📂 Select LinkedIn CSV File", command=self.import_linkedin,
                 bg=COLORS['info'], fg=COLORS['text_light'], padx=20, pady=8, font=("Arial", 10, "bold")).pack(anchor=tk.W)

        # CSV Import section
        csv_frame = tk.LabelFrame(tab, text="Import from CSV", padx=20, pady=20)
        csv_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(csv_frame, text="Import a CSV file with columns: company, website, email, phone, industry, contact_name, contact_title",
                wraplength=600, justify=tk.LEFT).pack(anchor=tk.W, pady=(0, 10))

        tk.Button(csv_frame, text="📂 Select CSV File", command=self.import_csv,
                 bg=COLORS['primary'], fg=COLORS['text_light'], padx=20, pady=8, font=("Arial", 10, "bold")).pack(anchor=tk.W)

    def create_outreach_tab(self):
        """Create outreach tracking tab"""
        tab = tk.Frame(self.notebook)
        self.notebook.add(tab, text="📧 Outreach")

        # Stats frame
        stats_frame = tk.LabelFrame(tab, text="Outreach Statistics", padx=20, pady=15)
        stats_frame.pack(fill=tk.X, padx=20, pady=10)

        stats_container = tk.Frame(stats_frame)
        stats_container.pack()

        self.outreach_stats = {}
        for i, (label, key) in enumerate([("Not Started", "not_started"), ("Sent", "sent"),
                                          ("Replied", "replied"), ("Due", "due")]):
            frame = tk.Frame(stats_container, bg="white", relief=tk.RAISED, borderwidth=1, width=120, height=80)
            frame.pack(side=tk.LEFT, padx=10)
            frame.pack_propagate(False)

            value = tk.Label(frame, text="0", font=("Arial", 24, "bold"), bg="white", fg="#1a3a5c")
            value.pack(pady=(10, 0))
            text = tk.Label(frame, text=label, font=("Arial", 9), bg="white")
            text.pack()

            self.outreach_stats[key] = value

        # Draft email section
        draft_frame = tk.LabelFrame(tab, text="Generate Email Draft", padx=20, pady=15)
        draft_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Selection frame
        sel_frame = tk.Frame(draft_frame)
        sel_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(sel_frame, text="Lead:").pack(side=tk.LEFT, padx=(0, 5))
        self.draft_lead_var = tk.StringVar()
        self.draft_lead_combo = ttk.Combobox(sel_frame, textvariable=self.draft_lead_var, width=40)
        self.draft_lead_combo.pack(side=tk.LEFT, padx=(0, 20))

        tk.Label(sel_frame, text="Template:").pack(side=tk.LEFT, padx=(0, 5))
        self.draft_template_var = tk.StringVar(value="first")
        template_combo = ttk.Combobox(sel_frame, textvariable=self.draft_template_var, width=20,
                                     values=["first", "followup1", "followup2"],
                                     state="readonly")
        template_combo.pack(side=tk.LEFT, padx=(0, 20))

        tk.Button(sel_frame, text="📝 Generate Draft", command=self.generate_draft,
                 bg=COLORS['primary'], fg=COLORS['text_light'], padx=15, pady=5).pack(side=tk.LEFT)

        # Draft display
        self.draft_display = scrolledtext.ScrolledText(draft_frame, height=15, wrap=tk.WORD)
        self.draft_display.pack(fill=tk.BOTH, expand=True, pady=(10, 10))

        # Draft buttons
        draft_btn_frame = tk.Frame(draft_frame)
        draft_btn_frame.pack(fill=tk.X)

        tk.Button(draft_btn_frame, text="📋 Copy to Clipboard", command=self.copy_draft,
                 bg=COLORS['text_secondary'], fg=COLORS['text_light'], padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        tk.Button(draft_btn_frame, text="✅ Mark as Sent", command=self.mark_sent,
                 bg=COLORS['success'], fg=COLORS['text_light'], padx=15, pady=5).pack(side=tk.LEFT, padx=5)

        self.update_outreach_stats()

    def create_tenders_tab(self):
        """Create tenders monitoring tab"""
        tab = tk.Frame(self.notebook)
        self.notebook.add(tab, text="📢 Tenders")

        # Info and check button
        top_frame = tk.Frame(tab)
        top_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(top_frame, text="Monitor government and public sector contract opportunities",
                font=("Arial", 10)).pack(side=tk.LEFT)

        tk.Button(top_frame, text="🔄 Check for New Tenders", command=self.check_tenders,
                 bg=COLORS['primary'], fg=COLORS['text_light'], padx=20, pady=8, font=("Arial", 10, "bold")).pack(side=tk.RIGHT)

        # Tenders list
        self.tenders_text = scrolledtext.ScrolledText(tab, wrap=tk.WORD)
        self.tenders_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        self.refresh_tenders()

    def create_settings_tab(self):
        """Create settings tab"""
        tab = tk.Frame(self.notebook)
        self.notebook.add(tab, text="⚙️ Settings")

        # Your Info section
        info_frame = tk.LabelFrame(tab, text="Your Information (for email templates)",
                                   padx=20, pady=15)
        info_frame.pack(fill=tk.X, padx=20, pady=10)

        info_fields = [
            ("Your Name", "your_name"),
            ("Your Company", "your_company"),
            ("Your Phone", "your_phone"),
            ("Your Email", "your_email")
        ]

        self.config_vars = {}
        for i, (label, key) in enumerate(info_fields):
            row = i // 2
            col = (i % 2) * 2

            tk.Label(info_frame, text=label).grid(row=row, column=col, sticky=tk.W, padx=(0, 10), pady=5)
            var = tk.StringVar(value=self.config.get(key, ""))
            entry = tk.Entry(info_frame, textvariable=var, width=30)
            entry.grid(row=row, column=col+1, pady=5, padx=(0, 20))
            self.config_vars[key] = var

        # Jobber section
        jobber_frame = tk.LabelFrame(tab, text="Jobber CRM Integration", padx=20, pady=15)
        jobber_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(jobber_frame, text="Client ID").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.config_vars['jobber_client_id'] = tk.StringVar(value=self.config.get('jobber_client_id', ""))
        tk.Entry(jobber_frame, textvariable=self.config_vars['jobber_client_id'], width=40).grid(row=0, column=1, pady=5)

        tk.Label(jobber_frame, text="Client Secret").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.config_vars['jobber_client_secret'] = tk.StringVar(value=self.config.get('jobber_client_secret', ""))
        tk.Entry(jobber_frame, textvariable=self.config_vars['jobber_client_secret'], width=40, show="*").grid(row=1, column=1, pady=5)

        # Tender keywords section
        tender_frame = tk.LabelFrame(tab, text="Tender Monitoring Keywords", padx=20, pady=15)
        tender_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(tender_frame, text="Keywords (comma-separated)").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.config_vars['tender_keywords'] = tk.StringVar(value=", ".join(self.config.get('tender_keywords', [])))
        tk.Entry(tender_frame, textvariable=self.config_vars['tender_keywords'], width=60).grid(row=0, column=1, pady=5)

        tk.Label(tender_frame, text="Locations (comma-separated)").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.config_vars['tender_locations'] = tk.StringVar(value=", ".join(self.config.get('tender_locations', [])))
        tk.Entry(tender_frame, textvariable=self.config_vars['tender_locations'], width=60).grid(row=1, column=1, pady=5)

        # Save button
        tk.Button(tab, text="💾 Save Settings", command=self.save_settings,
                 bg=COLORS['success'], fg=COLORS['text_light'], padx=30, pady=10, font=("Arial", 11, "bold")).pack(pady=20)

    # ========================================================================
    # DATA METHODS
    # ========================================================================

    def update_stats(self):
        """Update statistics bar"""
        leads_list = list(self.leads.values())

        self.stat_labels['total'].config(text=str(len(leads_list)))
        self.stat_labels['email'].config(text=str(len([l for l in leads_list if l.get('general_email') or l.get('contact_email')])))
        self.stat_labels['contacted'].config(text=str(len([l for l in leads_list if l.get('outreach_status') in ['sent', 'replied']])))

        # Count follow-ups due
        now = datetime.now()
        due = 0
        for l in leads_list:
            if l.get('next_followup_date'):
                try:
                    followup_date = datetime.fromisoformat(l['next_followup_date'].replace('Z', '+00:00'))
                    if followup_date <= now and l.get('outreach_status') != 'replied':
                        due += 1
                except:
                    pass
        self.stat_labels['followup'].config(text=str(due))

        # Count unread tenders
        tenders_list = list(self.tenders.values())
        self.stat_labels['tenders'].config(text=str(len([t for t in tenders_list if not t.get('is_read')])))

    def refresh_leads(self):
        """Refresh leads table"""
        # Clear existing
        for item in self.leads_tree.get_children():
            self.leads_tree.delete(item)

        # Get filter values
        search = self.search_var.get().lower()
        status_filter = self.status_filter.get()

        # Filter and display leads
        for lead_id, lead in self.leads.items():
            # Apply filters
            if search and search not in lead.get('company_name', '').lower():
                continue
            if status_filter != "All" and lead.get('status') != status_filter:
                continue

            # Insert parent row (company info)
            parent_id = self.leads_tree.insert('', tk.END, iid=lead_id, values=(
                lead.get('company_name', ''),
                '',  # Contact info will be in child rows
                lead.get('signal_score', 0),
                lead.get('status', 'New')
            ))

            # Get all contacts and insert as child rows
            contact_rows = self._get_all_contact_rows(lead)
            for i, contact_info in enumerate(contact_rows):
                # Insert child row under company
                self.leads_tree.insert(parent_id, tk.END, iid=f"{lead_id}_contact_{i}",
                                     values=('', contact_info, '', ''))

    def _get_all_contact_rows(self, lead):
        """Get list of all contact rows to display (each email/phone as separate row)"""
        rows = []

        # Add contact name first if available
        if lead.get('contact_name'):
            name_part = f"👤 {lead['contact_name']}"
            if lead.get('contact_title'):
                name_part += f" ({lead['contact_title']})"
            rows.append(name_part)

        # Get all emails
        all_emails = lead.get('all_emails', [])
        general_email = lead.get('general_email', '')
        contact_email = lead.get('contact_email', '')

        # If all_emails not populated, use individual email fields
        if not all_emails:
            if general_email:
                all_emails.append(general_email)
            if contact_email and contact_email not in all_emails:
                all_emails.append(contact_email)

        # Add each email as a separate row
        for i, email in enumerate(all_emails):
            if email == general_email or i == 0:
                rows.append(f"📧 {email} (Primary)")
            elif email == contact_email:
                rows.append(f"📧 {email} (Contact)")
            else:
                rows.append(f"📧 {email}")

        # Get all phones
        all_phones = lead.get('all_phones', [])
        general_phone = lead.get('general_phone', '')

        # If all_phones not populated, use individual phone field
        if not all_phones:
            if general_phone:
                all_phones.append(general_phone)

        # Add each phone as a separate row
        for i, phone in enumerate(all_phones):
            if phone == general_phone or i == 0:
                rows.append(f"📞 {phone} (Main)")
            else:
                rows.append(f"📞 {phone}")

        return rows if rows else ["-"]

    def refresh_tenders(self):
        """Refresh tenders display"""
        self.tenders_text.delete(1.0, tk.END)

        tenders_list = sorted(self.tenders.values(),
                            key=lambda x: x.get('relevance_score', 0), reverse=True)

        if not tenders_list:
            self.tenders_text.insert(tk.END, "No tenders found. Click 'Check for New Tenders' to search.\n")
        else:
            for tender in tenders_list[:20]:  # Show top 20
                status = "🆕 NEW" if not tender.get('is_read') else ""
                self.tenders_text.insert(tk.END, f"{status} ", 'new' if not tender.get('is_read') else '')
                self.tenders_text.insert(tk.END, f"[Score: {tender.get('relevance_score', 0)}] ", 'score')
                self.tenders_text.insert(tk.END, f"{tender.get('title', 'No title')}\n", 'title')
                self.tenders_text.insert(tk.END, f"   {tender.get('organization', 'Unknown org')}\n")
                self.tenders_text.insert(tk.END, f"   URL: {tender.get('url', 'No URL')}\n\n", 'url')

        # Configure tags
        self.tenders_text.tag_config('new', foreground='blue', font=('Arial', 10, 'bold'))
        self.tenders_text.tag_config('score', foreground='green', font=('Arial', 9, 'bold'))
        self.tenders_text.tag_config('title', font=('Arial', 10, 'bold'))
        self.tenders_text.tag_config('url', foreground='#0066cc', underline=True)

    def update_outreach_stats(self):
        """Update outreach statistics"""
        leads_list = list(self.leads.values())

        not_started = len([l for l in leads_list if not l.get('outreach_status') or l.get('outreach_status') == 'not_started'])
        sent = len([l for l in leads_list if l.get('outreach_status') == 'sent'])
        replied = len([l for l in leads_list if l.get('outreach_status') == 'replied'])

        now = datetime.now()
        due = 0
        for l in leads_list:
            if l.get('next_followup_date'):
                try:
                    followup_date = datetime.fromisoformat(l['next_followup_date'].replace('Z', '+00:00'))
                    if followup_date <= now and l.get('outreach_status') != 'replied':
                        due += 1
                except:
                    pass

        self.outreach_stats['not_started'].config(text=str(not_started))
        self.outreach_stats['sent'].config(text=str(sent))
        self.outreach_stats['replied'].config(text=str(replied))
        self.outreach_stats['due'].config(text=str(due))

        # Update lead dropdown
        leads_with_email = [(lid, l['company_name']) for lid, l in self.leads.items()
                           if l.get('general_email') or l.get('contact_email')]
        self.draft_lead_combo['values'] = [name for _, name in leads_with_email]
        self.draft_lead_map = {name: lid for lid, name in leads_with_email}

    # ========================================================================
    # ACTION METHODS
    # ========================================================================

    def add_lead(self, scrape=False):
        """Add a new lead"""
        company = self.add_vars['company'].get().strip()
        if not company:
            messagebox.showerror("Error", "Company name is required")
            return

        # Create lead
        lead_id = f"lead_{int(time.time() * 1000)}"
        lead = {
            'id': lead_id,
            'company_name': company,
            'website': self.add_vars['website'].get().strip(),
            'industry': self.add_vars['industry'].get(),
            'source': self.add_vars['source'].get().strip(),
            'general_email': self.add_vars['email'].get().strip(),
            'general_phone': self.add_vars['phone'].get().strip(),
            'contact_name': self.add_vars['contact_name'].get().strip(),
            'contact_title': self.add_vars['contact_title'].get().strip(),
            'notes': self.add_notes.get(1.0, tk.END).strip(),
            'buying_signals': [],
            'signal_score': 0,
            'status': 'New',
            'outreach_status': 'not_started',
            'next_followup_date': None,
            'created_date': datetime.now().isoformat()
        }

        # Scrape if requested
        if scrape and lead['website']:
            self.root.config(cursor="wait")
            self.root.update()

            result = scrape_website(lead['website'])
            if result['emails']:
                lead['general_email'] = result['emails'][0]
            if result['phones']:
                lead['general_phone'] = result['phones'][0]

            signals, score = detect_signals(lead['website'])
            lead['buying_signals'] = signals
            lead['signal_score'] = score

            self.root.config(cursor="")

        # Save
        self.leads[lead_id] = lead
        save_json(DATA_DIR / "leads.json", self.leads)

        # Update UI
        self.refresh_leads()
        self.update_stats()
        self.clear_add_form()

        messagebox.showinfo("Success", f"Added: {company}")

    def add_and_scrape(self):
        """Add lead and scrape website with enhanced intelligence"""
        # First add the lead without scraping
        company = self.add_vars['company'].get().strip()
        if not company:
            messagebox.showerror("Error", "Company name is required")
            return

        # Create lead
        lead_id = f"lead_{int(time.time() * 1000)}"
        lead = {
            'id': lead_id,
            'company_name': company,
            'website': self.add_vars['website'].get().strip(),
            'industry': self.add_vars['industry'].get(),
            'source': self.add_vars['source'].get().strip(),
            'general_email': self.add_vars['email'].get().strip(),
            'general_phone': self.add_vars['phone'].get().strip(),
            'contact_name': self.add_vars['contact_name'].get().strip(),
            'contact_title': self.add_vars['contact_title'].get().strip(),
            'notes': self.add_notes.get(1.0, tk.END).strip(),
            'buying_signals': [],
            'signal_score': 0,
            'status': 'New',
            'outreach_status': 'not_started',
            'next_followup_date': None,
            'created_date': datetime.now().isoformat(),
            'intelligence': None
        }

        # Enhanced scraping if website provided
        if lead['website'] and UNIFIED_SCORING_AVAILABLE:
            self.root.config(cursor="wait")
            self.root.update()

            try:
                # Use unified scoring
                scorer = UnifiedSignalScoring(hunter_api_key=None)  # TODO: Get from settings
                result = scorer.calculate_unified_score(
                    company_name=lead['company_name'],
                    website=lead['website'],
                    email=lead['general_email'] if lead['general_email'] else None,
                    check_news=True,
                    check_permits=True,
                    check_linkedin=True,
                    check_email_enrichment=bool(lead['general_email'])
                )

                # Store comprehensive data
                lead['signal_score'] = result['total_score']
                lead['priority'] = result.get('priority', 'LOW')
                lead['intelligence'] = {
                    'last_updated': result['analysis_date'],
                    'sources': result['sources'],
                    'all_signals': result['all_signals']
                }

                # Extract emails/phones from website scraping
                if 'website' in result['sources']:
                    ws = result['sources']['website']
                    # Run quick scrape to get actual contacts
                    from enhanced_scraper import scrape_website as enhanced_scrape
                    scrape_result = enhanced_scrape(lead['website'])

                    if scrape_result['emails'] and not lead['general_email']:
                        lead['general_email'] = scrape_result['emails'][0]
                    if scrape_result['phones'] and not lead['general_phone']:
                        lead['general_phone'] = scrape_result['phones'][0]

                    lead['all_emails'] = scrape_result['emails']
                    lead['all_phones'] = scrape_result['phones']

                # Convert signals to old format for compatibility
                if result['all_signals']:
                    lead['buying_signals'] = []
                    for signal in result['all_signals']:
                        lead['buying_signals'].append({
                            'keyword': signal['type'],
                            'score': signal['score'],
                            'source': signal['source']
                        })

            except Exception as e:
                print(f"Enhanced scraping error: {e}")
                # Fallback to basic scraping
                result = scrape_website(lead['website'])
                if result['emails']:
                    lead['general_email'] = result['emails'][0]
                if result['phones']:
                    lead['general_phone'] = result['phones'][0]

                signals, score = detect_signals(lead['website'])
                lead['buying_signals'] = signals
                lead['signal_score'] = score

            self.root.config(cursor="")

        elif lead['website']:
            # Basic scraping fallback
            self.root.config(cursor="wait")
            self.root.update()

            result = scrape_website(lead['website'])
            if result['emails']:
                lead['general_email'] = result['emails'][0]
            if result['phones']:
                lead['general_phone'] = result['phones'][0]

            signals, score = detect_signals(lead['website'])
            lead['buying_signals'] = signals
            lead['signal_score'] = score

            self.root.config(cursor="")

        # Save
        self.leads[lead_id] = lead
        save_json(DATA_DIR / "leads.json", self.leads)

        # Update UI
        self.refresh_leads()
        self.update_stats()
        self.clear_add_form()

        messagebox.showinfo("Success", f"Added: {company}\nSignal Score: {lead['signal_score']}/100")

    def clear_add_form(self):
        """Clear the add form"""
        for var in self.add_vars.values():
            var.set("")
        self.add_notes.delete(1.0, tk.END)

    def edit_lead(self, event=None):
        """Edit selected lead"""
        selection = self.leads_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a lead to edit")
            return

        lead_id = selection[0]
        lead = self.leads[lead_id]

        # Create edit dialog
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Edit: {lead['company_name']}")
        dialog.geometry("600x700")

        # Create form
        form = tk.Frame(dialog, padx=20, pady=20)
        form.pack(fill=tk.BOTH, expand=True)

        # Fields
        fields = [
            ("Company Name", "company_name"),
            ("Website", "website"),
            ("General Email", "general_email"),
            ("General Phone", "general_phone"),
            ("Industry", "industry"),
            ("Status", "status"),
            ("Contact Name", "contact_name"),
            ("Contact Title", "contact_title"),
        ]

        edit_vars = {}
        row = 0

        for label, key in fields:
            tk.Label(form, text=label, font=("Arial", 9, "bold")).grid(row=row, column=0, sticky=tk.W, pady=5)

            if key == "status":
                var = tk.StringVar(value=lead.get(key, 'New'))
                widget = ttk.Combobox(form, textvariable=var, width=38,
                                     values=["New", "Contacted", "Qualified"], state="readonly")
            elif key == "industry":
                var = tk.StringVar(value=lead.get(key, ''))
                widget = ttk.Combobox(form, textvariable=var, width=38,
                                     values=["Manufacturing", "Metal Fabrication", "Oil & Gas", "Construction", "Other"])
            else:
                var = tk.StringVar(value=lead.get(key, ''))
                widget = tk.Entry(form, textvariable=var, width=40)

            widget.grid(row=row, column=1, pady=5)
            edit_vars[key] = var
            row += 1

        # Notes
        tk.Label(form, text="Notes", font=("Arial", 9, "bold")).grid(row=row, column=0, sticky=tk.NW, pady=5)
        notes_text = tk.Text(form, width=40, height=4)
        notes_text.insert(1.0, lead.get('notes', ''))
        notes_text.grid(row=row, column=1, pady=5)
        row += 1

        # Buying signals display
        if lead.get('buying_signals'):
            tk.Label(form, text=f"Buying Signals (Score: {lead.get('signal_score', 0)})",
                    font=("Arial", 9, "bold")).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=10)
            row += 1

            signals_text = ", ".join([s['keyword'] for s in lead['buying_signals']])
            tk.Label(form, text=signals_text, wraplength=500, justify=tk.LEFT).grid(
                row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
            row += 1

        # Buttons
        btn_frame = tk.Frame(form)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=20)

        def save_changes():
            for key, var in edit_vars.items():
                lead[key] = var.get()
            lead['notes'] = notes_text.get(1.0, tk.END).strip()

            save_json(DATA_DIR / "leads.json", self.leads)
            self.refresh_leads()
            self.update_stats()
            dialog.destroy()
            messagebox.showinfo("Success", "Lead updated")

        def scrape_now():
            if not lead.get('website'):
                messagebox.showwarning("Warning", "No website entered")
                return

            dialog.config(cursor="wait")
            dialog.update()

            result = scrape_website(lead['website'])
            if result['emails']:
                edit_vars['general_email'].set(result['emails'][0])
            if result['phones']:
                edit_vars['general_phone'].set(result['phones'][0])

            dialog.config(cursor="")
            messagebox.showinfo("Success", f"Found {len(result['emails'])} emails, {len(result['phones'])} phones")

        def detect_now():
            if not lead.get('website'):
                messagebox.showwarning("Warning", "No website entered")
                return

            dialog.config(cursor="wait")
            dialog.update()

            signals, score = detect_signals(lead['website'])
            lead['buying_signals'] = signals
            lead['signal_score'] = score

            dialog.config(cursor="")
            save_json(DATA_DIR / "leads.json", self.leads)
            messagebox.showinfo("Success", f"Signal Score: {score}")
            dialog.destroy()
            self.edit_lead()  # Reopen to show signals

        def enhanced_scrape():
            """Enhanced scraping with unified intelligence gathering"""
            if not lead.get('website'):
                messagebox.showwarning("Warning", "No website entered")
                return

            if not UNIFIED_SCORING_AVAILABLE:
                messagebox.showwarning("Not Available",
                    "Unified signal scoring not available.\n\n" +
                    "Make sure these files are in your LeadGENApp folder:\n" +
                    "• unified_signal_scoring.py\n" +
                    "• enhanced_scraper.py\n" +
                    "• news_monitor.py\n" +
                    "• building_permits.py\n" +
                    "• linkedin_discovery.py\n" +
                    "• email_enrichment.py\n\n" +
                    "Using basic scraping instead...")
                detect_now()
                return

            dialog.config(cursor="wait")
            dialog.update()

            try:
                # Get email from form if entered
                email = edit_vars.get('general_email', tk.StringVar()).get()
                if not email:
                    email = lead.get('general_email')

                # Use unified scoring
                scorer = UnifiedSignalScoring(hunter_api_key=None)  # TODO: Add to settings
                result = scorer.calculate_unified_score(
                    company_name=lead['company_name'],
                    website=lead['website'],
                    email=email,
                    check_news=True,
                    check_permits=True,
                    check_linkedin=True,
                    check_email_enrichment=bool(email)
                )

                # Update lead with comprehensive data
                lead['signal_score'] = result['total_score']
                lead['priority'] = result.get('priority', 'LOW')
                lead['intelligence'] = {
                    'last_updated': result['analysis_date'],
                    'sources': result['sources'],
                    'all_signals': result['all_signals']
                }

                # Extract emails/phones from website scraping
                if 'website' in result['sources'] and 'error' not in result['sources']['website']:
                    # Run quick scrape to get actual contacts
                    from enhanced_scraper import scrape_website as enhanced_scrape
                    scrape_result = enhanced_scrape(lead['website'])

                    if scrape_result['emails']:
                        if not edit_vars['general_email'].get():
                            edit_vars['general_email'].set(scrape_result['emails'][0])
                        lead['all_emails'] = scrape_result['emails']

                    if scrape_result['phones']:
                        if not edit_vars['general_phone'].get():
                            edit_vars['general_phone'].set(scrape_result['phones'][0])
                        lead['all_phones'] = scrape_result['phones']

                # Convert signals to old format for compatibility
                if result['all_signals']:
                    lead['buying_signals'] = []
                    for signal in result['all_signals']:
                        lead['buying_signals'].append({
                            'keyword': signal['type'],
                            'score': signal['score'],
                            'source': signal['source']
                        })

                dialog.config(cursor="")

                # Save immediately
                save_json(DATA_DIR / "leads.json", self.leads)

                # Show summary
                summary = f"✅ Intelligence Gathered!\n\n"
                summary += f"Total Score: {result['total_score']}/100\n"
                summary += f"Priority: {result.get('priority_label', 'Unknown')}\n\n"

                summary += "Sources Checked:\n"
                for source, data in result['sources'].items():
                    if isinstance(data, dict) and 'score' in data:
                        summary += f"  • {source.title()}: +{data['score']} points\n"

                summary += f"\nClick 'View Intelligence' to see full details!"

                messagebox.showinfo("Intelligence Complete", summary)

                # Close and reopen to refresh
                dialog.destroy()
                self.edit_lead()

            except Exception as e:
                dialog.config(cursor="")
                messagebox.showerror("Error", f"Enhanced scraping failed:\n{str(e)}\n\nUsing basic scraping instead...")
                detect_now()

        def view_intel():
            """Wrapper to call view_lead_intelligence"""
            self.view_lead_intelligence(lead, dialog)

        tk.Button(btn_frame, text="💾 Save", command=save_changes,
                 bg=COLORS['primary'], fg=COLORS['text_light'], padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🔍 Basic Scrape", command=scrape_now,
                 bg=COLORS['success'], fg=COLORS['text_light'], padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🎯 Enhanced Scrape", command=enhanced_scrape,
                 bg=COLORS['secondary'], fg=COLORS['text_light'], padx=15, pady=5, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="📊 View Intelligence", command=view_intel,
                 bg=COLORS['warning'], fg=COLORS['text_light'], padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="❌ Cancel", command=dialog.destroy,
                 bg=COLORS['text_secondary'], fg=COLORS['text_light'], padx=15, pady=5).pack(side=tk.LEFT, padx=5)

    def delete_lead(self):
        """Delete selected lead"""
        selection = self.leads_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a lead to delete")
            return

        lead_id = selection[0]
        lead = self.leads[lead_id]

        if messagebox.askyesno("Confirm Delete", f"Delete {lead['company_name']}?"):
            del self.leads[lead_id]
            save_json(DATA_DIR / "leads.json", self.leads)
            self.refresh_leads()
            self.update_stats()
            messagebox.showinfo("Success", "Lead deleted")

    def view_lead_intelligence(self, lead, parent_dialog):
        """Display comprehensive intelligence data for a lead"""
        if not lead.get('intelligence'):
            messagebox.showinfo("No Data",
                "No intelligence data available.\n\n" +
                "Click 'Enhanced Scrape' to gather comprehensive intelligence from:\n" +
                "• Website (multiple pages)\n" +
                "• Google News\n" +
                "• Building Permits\n" +
                "• LinkedIn\n" +
                "• Email Enrichment")
            return

        # Create intelligence viewer window
        intel_window = tk.Toplevel(parent_dialog)
        intel_window.title(f"Intelligence: {lead['company_name']}")
        intel_window.geometry("900x650")

        # Create notebook for different intelligence sources
        notebook = ttk.Notebook(intel_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        intel_data = lead['intelligence']

        # ========== Overview Tab ==========
        overview_tab = tk.Frame(notebook)
        notebook.add(overview_tab, text="📊 Overview")

        overview_text = scrolledtext.ScrolledText(overview_tab, wrap=tk.WORD, font=("Arial", 10))
        overview_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        overview_content = f"""INTELLIGENCE SUMMARY
{'='*70}

Company: {lead['company_name']}
Website: {lead.get('website', 'N/A')}
Email: {lead.get('general_email', 'N/A')}
Last Updated: {intel_data.get('last_updated', 'Unknown')[:19]}

SIGNAL SCORE: {lead.get('signal_score', 0)}/100
Priority: {lead.get('priority', 'Unknown')} Lead

{'='*70}
SCORE BREAKDOWN:
{'='*70}

"""

        total_sources = 0
        for source, data in intel_data.get('sources', {}).items():
            if isinstance(data, dict) and 'score' in data:
                total_sources += 1
                overview_content += f"\n{source.upper()}: +{data['score']} points\n"

                if source == 'website' and 'error' not in data:
                    overview_content += f"  • Pages Scraped: {data.get('pages_scraped', 0)}\n"
                    overview_content += f"  • Emails Found: {data.get('emails_found', 0)}\n"
                    overview_content += f"  • Phones Found: {data.get('phones_found', 0)}\n"

                elif source == 'news' and 'error' not in data:
                    overview_content += f"  • Articles Found: {data.get('articles_found', 0)}\n"

                elif source == 'permits' and 'error' not in data:
                    overview_content += f"  • Permits Found: {data.get('permits_found', 0)}\n"

                elif source == 'linkedin' and 'error' not in data:
                    overview_content += f"  • Company Page: {'Found' if data.get('company_page') else 'Not Found'}\n"
                    overview_content += f"  • Employees Found: {data.get('employees_found', 0)}\n"

                elif source == 'email_enrichment' and 'error' not in data:
                    cb = data.get('clearbit_data', {})
                    if cb and 'error' not in cb:
                        if cb.get('employees'):
                            overview_content += f"  • Company Size: {cb['employees']} employees\n"
                        if cb.get('industry'):
                            overview_content += f"  • Industry: {cb['industry']}\n"
                        if cb.get('estimated_revenue'):
                            overview_content += f"  • Revenue: {cb['estimated_revenue']}\n"

        overview_content += f"\n{'='*70}\n"
        overview_content += f"ALL SIGNALS DETECTED ({len(intel_data.get('all_signals', []))}):\n"
        overview_content += f"{'='*70}\n\n"

        # Sort signals by score
        all_signals = sorted(intel_data.get('all_signals', []),
                           key=lambda x: x.get('score', 0), reverse=True)

        for signal in all_signals:
            source_icon = {
                'website': '🌐',
                'news': '📰',
                'permits': '🏗️',
                'building_permit': '🏗️',
                'linkedin': '💼',
                'email_enrichment': '📧'
            }.get(signal.get('source', ''), '•')

            overview_content += f"{source_icon} [{signal.get('source', 'unknown').upper()}] " \
                              f"{signal.get('type', 'unknown')} (+{signal.get('score', 0)})\n"

        overview_content += f"\n{'='*70}\n"
        overview_content += f"SOURCES CHECKED: {total_sources}\n"
        overview_content += f"RECOMMENDATION: "

        score = lead.get('signal_score', 0)
        if score >= 70:
            overview_content += "🔥 HOT LEAD - Contact immediately!\n"
        elif score >= 40:
            overview_content += "⚡ WARM LEAD - Good potential, follow up soon.\n"
        else:
            overview_content += "❄️ COLD LEAD - Low priority, monitor for changes.\n"

        overview_text.insert(1.0, overview_content)
        overview_text.config(state=tk.DISABLED)

        # ========== News Tab ==========
        if 'news' in intel_data.get('sources', {}):
            news_data = intel_data['sources']['news']
            if not isinstance(news_data, dict) or 'error' in news_data:
                pass  # Skip if error
            elif news_data.get('signals'):
                news_tab = tk.Frame(notebook)
                notebook.add(news_tab, text=f"📰 News ({len(news_data['signals'])})")

                news_text = scrolledtext.ScrolledText(news_tab, wrap=tk.WORD, font=("Arial", 10))
                news_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

                news_content = f"NEWS MONITORING RESULTS\n{'='*70}\n\n"
                news_content += f"Found {len(news_data['signals'])} buying signals in recent news.\n\n"

                for i, signal in enumerate(news_data['signals'], 1):
                    news_content += f"{i}. SIGNAL: {signal.get('keyword', 'unknown').upper()} " \
                                  f"(+{signal.get('score', 0)} points)\n"
                    news_content += f"   Article: {signal.get('article_title', 'N/A')}\n"
                    news_content += f"   Link: {signal.get('article_link', 'N/A')}\n"
                    if signal.get('context'):
                        news_content += f"   Context: {signal['context']}\n"
                    news_content += f"\n{'-'*70}\n\n"

                news_text.insert(1.0, news_content)
                news_text.config(state=tk.DISABLED)

        # ========== Building Permits Tab ==========
        if 'permits' in intel_data.get('sources', {}):
            permits_data = intel_data['sources']['permits']
            if not isinstance(permits_data, dict) or 'error' in permits_data:
                pass  # Skip if error
            elif permits_data.get('signals'):
                permits_tab = tk.Frame(notebook)
                notebook.add(permits_tab, text=f"🏗️ Permits ({len(permits_data['signals'])})")

                permits_text = scrolledtext.ScrolledText(permits_tab, wrap=tk.WORD, font=("Arial", 10))
                permits_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

                permits_content = f"BUILDING PERMITS FOUND\n{'='*70}\n\n"
                permits_content += f"Found {len(permits_data['signals'])} building permits.\n\n"

                for i, signal in enumerate(permits_data['signals'], 1):
                    permits_content += f"{i}. PERMIT: {signal.get('permit_number', 'Unknown')}\n"
                    permits_content += f"   Type: {signal.get('permit_type', 'N/A')}\n"
                    permits_content += f"   Description: {signal.get('description', 'N/A')}\n"
                    permits_content += f"   Address: {signal.get('address', 'N/A')}\n"
                    permits_content += f"   Issued: {signal.get('issued_date', 'N/A')}\n"
                    if signal.get('estimated_cost'):
                        permits_content += f"   Estimated Cost: ${signal['estimated_cost']:,}\n"
                    permits_content += f"   Signal Score: +{signal.get('score', 0)} points\n"
                    permits_content += f"\n{'-'*70}\n\n"

                permits_text.insert(1.0, permits_content)
                permits_text.config(state=tk.DISABLED)

        # ========== LinkedIn Tab ==========
        if 'linkedin' in intel_data.get('sources', {}):
            linkedin_data = intel_data['sources']['linkedin']
            linkedin_tab = tk.Frame(notebook)
            notebook.add(linkedin_tab, text="💼 LinkedIn")

            linkedin_text = scrolledtext.ScrolledText(linkedin_tab, wrap=tk.WORD, font=("Arial", 10))
            linkedin_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            linkedin_content = f"LINKEDIN DISCOVERY\n{'='*70}\n\n"

            if linkedin_data.get('company_page'):
                linkedin_content += f"Company Page Found:\n{linkedin_data['company_page']}\n\n"
                linkedin_content += "(Right-click and copy to open in browser)\n\n"
            else:
                linkedin_content += "Company Page: Not found\n\n"

            linkedin_content += f"Employees Found on LinkedIn: {linkedin_data.get('employees_found', 0)}\n\n"

            if linkedin_data.get('signals'):
                linkedin_content += f"Signals Detected:\n"
                for signal in linkedin_data['signals']:
                    linkedin_content += f"  • {signal.get('description', 'Unknown')} " \
                                      f"(+{signal.get('score', 0)} points)\n"

            linkedin_content += f"\n{'='*70}\n"
            linkedin_content += "NOTE: Employee profiles are discovered but not stored to respect privacy.\n"

            linkedin_text.insert(1.0, linkedin_content)
            linkedin_text.config(state=tk.DISABLED)

        # ========== Email Enrichment Tab ==========
        if 'email_enrichment' in intel_data.get('sources', {}):
            enrich_data = intel_data['sources']['email_enrichment']
            if not isinstance(enrich_data, dict) or 'error' not in enrich_data:
                enrich_tab = tk.Frame(notebook)
                notebook.add(enrich_tab, text="📧 Email Data")

                enrich_text = scrolledtext.ScrolledText(enrich_tab, wrap=tk.WORD, font=("Arial", 10))
                enrich_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

                enrich_content = f"EMAIL DOMAIN ENRICHMENT\n{'='*70}\n\n"

                # Clearbit data
                cb = enrich_data.get('clearbit_data', {})
                if cb and 'error' not in cb:
                    enrich_content += f"Company Information (Clearbit):\n\n"
                    if cb.get('company_name'):
                        enrich_content += f"  Company: {cb['company_name']}\n"
                    if cb.get('industry'):
                        enrich_content += f"  Industry: {cb['industry']}\n"
                    if cb.get('sector'):
                        enrich_content += f"  Sector: {cb['sector']}\n"
                    if cb.get('employees'):
                        enrich_content += f"  Employees: {cb['employees']}\n"
                    if cb.get('estimated_revenue'):
                        enrich_content += f"  Estimated Revenue: {cb['estimated_revenue']}\n"
                    if cb.get('location'):
                        enrich_content += f"  Location: {cb['location']}\n"
                    if cb.get('founded_year'):
                        enrich_content += f"  Founded: {cb['founded_year']}\n"

                    if cb.get('twitter') or cb.get('linkedin') or cb.get('facebook'):
                        enrich_content += f"\n  Social Media:\n"
                        if cb.get('twitter'):
                            enrich_content += f"    Twitter: @{cb['twitter']}\n"
                        if cb.get('linkedin'):
                            enrich_content += f"    LinkedIn: {cb['linkedin']}\n"
                        if cb.get('facebook'):
                            enrich_content += f"    Facebook: {cb['facebook']}\n"

                # Hunter data
                hunter = enrich_data.get('hunter_data', {})
                if hunter and 'error' not in hunter:
                    enrich_content += f"\n\nEmail Intelligence (Hunter.io):\n\n"
                    if hunter.get('emails_found'):
                        enrich_content += f"  Total Emails Found: {hunter['emails_found']}\n"
                    if hunter.get('email_pattern'):
                        enrich_content += f"  Email Pattern: {hunter['email_pattern']}\n"

                    if hunter.get('email_list'):
                        enrich_content += f"\n  Additional Contacts:\n"
                        for email_info in hunter['email_list'][:10]:
                            enrich_content += f"\n    • {email_info.get('email', 'N/A')}\n"
                            if email_info.get('position'):
                                enrich_content += f"      Position: {email_info['position']}\n"
                            if email_info.get('first_name') and email_info.get('last_name'):
                                enrich_content += f"      Name: {email_info['first_name']} {email_info['last_name']}\n"

                # Signals
                if enrich_data.get('signals'):
                    enrich_content += f"\n\nSignals Detected:\n"
                    for signal in enrich_data['signals']:
                        enrich_content += f"  • {signal.get('description', 'Unknown')} " \
                                        f"(+{signal.get('score', 0)} points)\n"

                enrich_text.insert(1.0, enrich_content)
                enrich_text.config(state=tk.DISABLED)

        # Close button
        btn_frame = tk.Frame(intel_window)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(btn_frame, text="Close", command=intel_window.destroy,
                 bg=COLORS['text_secondary'], fg=COLORS['text_light'], padx=20, pady=8, font=("Arial", 10)).pack(side=tk.RIGHT)

    def import_linkedin(self):
        """Import LinkedIn connections"""
        filename = filedialog.askopenfilename(
            title="Select LinkedIn Connections.csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if not filename:
            return

        try:
            from linkedin_parser import parse_linkedin_csv

            filter_titles = self.li_filter_var.get()
            imported = parse_linkedin_csv(filename, filter_titles)

            # Add to leads
            count = 0
            for contact in imported:
                lead_id = f"lead_{int(time.time() * 1000)}_{count}"
                lead = {
                    'id': lead_id,
                    'company_name': contact.get('company', 'Unknown'),
                    'website': '',
                    'industry': '',
                    'source': 'LinkedIn',
                    'general_email': contact.get('email', ''),
                    'general_phone': '',
                    'contact_name': contact.get('name', ''),
                    'contact_title': contact.get('position', ''),
                    'notes': f"LinkedIn connection. Connected on: {contact.get('connected_on', 'Unknown')}",
                    'buying_signals': [],
                    'signal_score': 0,
                    'status': 'New',
                    'outreach_status': 'not_started',
                    'next_followup_date': None,
                    'created_date': datetime.now().isoformat()
                }
                self.leads[lead_id] = lead
                count += 1
                time.sleep(0.001)  # Ensure unique IDs

            save_json(DATA_DIR / "leads.json", self.leads)
            self.refresh_leads()
            self.update_stats()

            messagebox.showinfo("Success", f"Imported {count} leads from LinkedIn")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to import: {str(e)}")

    def import_csv(self):
        """Import generic CSV"""
        filename = filedialog.askopenfilename(
            title="Select CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if not filename:
            return

        try:
            count = 0
            with open(filename, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    lead_id = f"lead_{int(time.time() * 1000)}_{count}"
                    lead = {
                        'id': lead_id,
                        'company_name': row.get('company', row.get('Company', 'Unknown')),
                        'website': row.get('website', row.get('Website', '')),
                        'industry': row.get('industry', row.get('Industry', '')),
                        'source': 'CSV Import',
                        'general_email': row.get('email', row.get('Email', '')),
                        'general_phone': row.get('phone', row.get('Phone', '')),
                        'contact_name': row.get('contact_name', row.get('Contact', '')),
                        'contact_title': row.get('contact_title', row.get('Title', '')),
                        'notes': '',
                        'buying_signals': [],
                        'signal_score': 0,
                        'status': 'New',
                        'outreach_status': 'not_started',
                        'next_followup_date': None,
                        'created_date': datetime.now().isoformat()
                    }
                    self.leads[lead_id] = lead
                    count += 1
                    time.sleep(0.001)

            save_json(DATA_DIR / "leads.json", self.leads)
            self.refresh_leads()
            self.update_stats()

            messagebox.showinfo("Success", f"Imported {count} leads from CSV")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to import: {str(e)}")

    def generate_draft(self):
        """Generate email draft"""
        company_name = self.draft_lead_var.get()
        if not company_name:
            messagebox.showwarning("Warning", "Please select a lead")
            return

        lead_id = self.draft_lead_map.get(company_name)
        if not lead_id:
            return

        lead = self.leads[lead_id]
        template = self.draft_template_var.get()

        # Get config
        your_name = self.config.get('your_name', '[Your Name]')
        your_company = self.config.get('your_company', '[Your Company]')
        your_phone = self.config.get('your_phone', '[Your Phone]')
        your_email = self.config.get('your_email', '[Your Email]')

        # Generate email based on template
        if template == "first":
            subject = f"Industrial Services for {lead['company_name']}"
            body = f"""Hi{(' ' + lead.get('contact_name')) if lead.get('contact_name') else ''},

I hope this email finds you well. My name is {your_name} from {your_company}.

I noticed your company, {lead['company_name']}, and wanted to reach out to introduce our services. We specialize in [your services here] for industrial and manufacturing companies in the Calgary area.

Would you be open to a brief conversation to explore how we might be able to support your operations?

Best regards,
{your_name}
{your_company}
{your_phone}
{your_email}"""

        elif template == "followup1":
            subject = f"Following up - {lead['company_name']}"
            body = f"""Hi{(' ' + lead.get('contact_name')) if lead.get('contact_name') else ''},

I wanted to follow up on my previous email regarding industrial services for {lead['company_name']}.

I understand you're busy, but I believe there could be value in discussing how {your_company} can support your operations.

Would you have 10 minutes this week for a quick call?

Best regards,
{your_name}
{your_company}
{your_phone}
{your_email}"""

        else:  # followup2
            subject = f"Last follow-up - {lead['company_name']}"
            body = f"""Hi{(' ' + lead.get('contact_name')) if lead.get('contact_name') else ''},

This will be my last attempt to reach out. I wanted to ensure you had the opportunity to learn about how {your_company} can support {lead['company_name']}.

If now isn't the right time, I completely understand. Feel free to reach out in the future if your needs change.

Best regards,
{your_name}
{your_company}
{your_phone}
{your_email}"""

        # Display draft
        self.draft_display.delete(1.0, tk.END)
        self.draft_display.insert(tk.END, f"SUBJECT: {subject}\n\n")
        self.draft_display.insert(tk.END, body)

        self.current_draft_lead_id = lead_id

    def copy_draft(self):
        """Copy draft to clipboard"""
        draft = self.draft_display.get(1.0, tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(draft)
        messagebox.showinfo("Success", "Email draft copied to clipboard!")

    def mark_sent(self):
        """Mark email as sent"""
        if not hasattr(self, 'current_draft_lead_id'):
            messagebox.showwarning("Warning", "Please generate a draft first")
            return

        lead = self.leads[self.current_draft_lead_id]
        lead['outreach_status'] = 'sent'
        lead['last_contact_date'] = datetime.now().isoformat()

        # Set follow-up date (3 days from now)
        followup = datetime.now() + timedelta(days=3)
        lead['next_followup_date'] = followup.isoformat()

        save_json(DATA_DIR / "leads.json", self.leads)
        self.update_outreach_stats()
        self.update_stats()

        messagebox.showinfo("Success", f"Marked as sent! Follow-up scheduled for {followup.strftime('%Y-%m-%d')}")

    def check_tenders(self):
        """Check for new tenders (placeholder - would integrate with tender_monitoring.py)"""
        messagebox.showinfo("Info", "Tender checking functionality would connect to tender APIs here.\n\n" +
                           "This requires API keys and is a placeholder in the desktop version.")

    def save_settings(self):
        """Save settings"""
        for key, var in self.config_vars.items():
            if key in ['tender_keywords', 'tender_locations']:
                # Convert comma-separated to list
                value = [s.strip() for s in var.get().split(',') if s.strip()]
                self.config[key] = value
            else:
                self.config[key] = var.get()

        save_json(DATA_DIR / "config.json", self.config)
        messagebox.showinfo("Success", "Settings saved!")

    def export_leads(self):
        """Export leads to CSV"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile="leads_export.csv"
        )

        if not filename:
            return

        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                if not self.leads:
                    messagebox.showinfo("Info", "No leads to export")
                    return

                # Get all possible fields
                fieldnames = set()
                for lead in self.leads.values():
                    fieldnames.update(lead.keys())

                fieldnames = sorted(fieldnames)
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for lead in self.leads.values():
                    # Convert lists/dicts to strings
                    row = {}
                    for k, v in lead.items():
                        if isinstance(v, (list, dict)):
                            row[k] = json.dumps(v)
                        else:
                            row[k] = v
                    writer.writerow(row)

            messagebox.showinfo("Success", f"Exported {len(self.leads)} leads to {filename}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {str(e)}")

    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo("About",
            "Calgary Industrial Lead Generator\n"
            "Desktop Version 2.0\n\n"
            "A tool for managing industrial leads,\n"
            "tracking outreach, and monitoring tenders.\n\n"
            "© 2025")


# ============================================================================
# MAIN
# ============================================================================

def main():
    root = tk.Tk()
    app = LeadGeneratorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
