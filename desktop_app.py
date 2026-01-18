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
import requests
from bs4 import BeautifulSoup
import re
from threading import Thread

# Create data directory
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# ============================================================================
# BACKEND FUNCTIONS (from original app.py)
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

def scrape_website(url):
    """Scrape website for emails and phone numbers"""
    emails, phones = [], []
    try:
        if not url.startswith('http'):
            url = 'https://' + url
        r = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(r.text, 'html.parser')
        text = soup.get_text()

        # Find emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = list(set(re.findall(email_pattern, text)))

        # Find phone numbers
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        phones = list(set(re.findall(phone_pattern, text)))

    except Exception as e:
        print(f"Scrape error: {e}")

    return {'emails': emails, 'phones': phones}

def detect_signals(url):
    """Detect buying signals from website"""
    signals = []
    score = 0
    keywords = {
        'rfp': 50, 'request for proposal': 50, 'tender': 40, 'bidding': 40,
        'expansion': 30, 'hiring': 25, 'new equipment': 30, 'project': 20,
        'maintenance': 15, 'seeking': 20, 'looking for': 20
    }

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


# ============================================================================
# MAIN APPLICATION CLASS
# ============================================================================

class LeadGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Calgary Industrial Lead Generator")
        self.root.geometry("1200x700")

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
        stats_frame = tk.Frame(self.root, bg="#f0f0f0", height=80)
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
            frame = tk.Frame(stats_frame, bg="white", relief=tk.RAISED, borderwidth=1)
            frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

            value_label = tk.Label(frame, text="0", font=("Arial", 20, "bold"),
                                  bg="white", fg="#1a3a5c")
            value_label.pack(pady=(10, 0))

            text_label = tk.Label(frame, text=label, font=("Arial", 9),
                                 bg="white", fg="#666")
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
        columns = ("Company", "Contact", "Email", "Signal", "Status")
        self.leads_tree = ttk.Treeview(table_frame, columns=columns, show="headings",
                                       yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.config(command=self.leads_tree.yview)
        hsb.config(command=self.leads_tree.xview)

        # Column headings
        self.leads_tree.heading("Company", text="Company")
        self.leads_tree.heading("Contact", text="Contact")
        self.leads_tree.heading("Email", text="Email")
        self.leads_tree.heading("Signal", text="Signal Score")
        self.leads_tree.heading("Status", text="Status")

        # Column widths
        self.leads_tree.column("Company", width=250)
        self.leads_tree.column("Contact", width=150)
        self.leads_tree.column("Email", width=200)
        self.leads_tree.column("Signal", width=100)
        self.leads_tree.column("Status", width=100)

        self.leads_tree.pack(fill=tk.BOTH, expand=True)

        # Double-click to edit
        self.leads_tree.bind('<Double-Button-1>', self.edit_lead)

        # Buttons
        btn_frame = tk.Frame(tab)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        tk.Button(btn_frame, text="✏️ Edit Selected", command=self.edit_lead,
                 bg="#6c757d", fg="white", padx=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🗑️ Delete Selected", command=self.delete_lead,
                 bg="#dc3545", fg="white", padx=10).pack(side=tk.LEFT, padx=5)

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
                 bg="#1a3a5c", fg="white", padx=20, pady=8, font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="➕ Add & Scrape Website", command=self.add_and_scrape,
                 bg="#28a745", fg="white", padx=20, pady=8, font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🗑️ Clear Form", command=self.clear_add_form,
                 bg="#6c757d", fg="white", padx=20, pady=8).pack(side=tk.LEFT, padx=5)

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
                 bg="#0077b5", fg="white", padx=20, pady=8, font=("Arial", 10, "bold")).pack(anchor=tk.W)

        # CSV Import section
        csv_frame = tk.LabelFrame(tab, text="Import from CSV", padx=20, pady=20)
        csv_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(csv_frame, text="Import a CSV file with columns: company, website, email, phone, industry, contact_name, contact_title",
                wraplength=600, justify=tk.LEFT).pack(anchor=tk.W, pady=(0, 10))

        tk.Button(csv_frame, text="📂 Select CSV File", command=self.import_csv,
                 bg="#1a3a5c", fg="white", padx=20, pady=8, font=("Arial", 10, "bold")).pack(anchor=tk.W)

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
                 bg="#1a3a5c", fg="white", padx=15, pady=5).pack(side=tk.LEFT)

        # Draft display
        self.draft_display = scrolledtext.ScrolledText(draft_frame, height=15, wrap=tk.WORD)
        self.draft_display.pack(fill=tk.BOTH, expand=True, pady=(10, 10))

        # Draft buttons
        draft_btn_frame = tk.Frame(draft_frame)
        draft_btn_frame.pack(fill=tk.X)

        tk.Button(draft_btn_frame, text="📋 Copy to Clipboard", command=self.copy_draft,
                 bg="#6c757d", fg="white", padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        tk.Button(draft_btn_frame, text="✅ Mark as Sent", command=self.mark_sent,
                 bg="#28a745", fg="white", padx=15, pady=5).pack(side=tk.LEFT, padx=5)

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
                 bg="#1a3a5c", fg="white", padx=20, pady=8, font=("Arial", 10, "bold")).pack(side=tk.RIGHT)

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
                 bg="#28a745", fg="white", padx=30, pady=10, font=("Arial", 11, "bold")).pack(pady=20)

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

            # Insert into tree
            self.leads_tree.insert('', tk.END, iid=lead_id, values=(
                lead.get('company_name', ''),
                lead.get('contact_name', '-'),
                lead.get('contact_email') or lead.get('general_email', '-'),
                lead.get('signal_score', 0),
                lead.get('status', 'New')
            ))

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
        """Add lead and scrape website"""
        self.add_lead(scrape=True)

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

        tk.Button(btn_frame, text="💾 Save", command=save_changes,
                 bg="#1a3a5c", fg="white", padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🔍 Scrape Website", command=scrape_now,
                 bg="#28a745", fg="white", padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="📊 Detect Signals", command=detect_now,
                 bg="#ffc107", padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="❌ Cancel", command=dialog.destroy,
                 bg="#6c757d", fg="white", padx=15, pady=5).pack(side=tk.LEFT, padx=5)

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
