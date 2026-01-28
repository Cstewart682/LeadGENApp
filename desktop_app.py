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
from difflib import SequenceMatcher

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

# Import multi-source enrichment
try:
    from multi_source_enrichment import MultiSourceEnrichment
    MULTI_SOURCE_AVAILABLE = True
    print("✓ Multi-source enrichment loaded")
except ImportError:
    MULTI_SOURCE_AVAILABLE = False
    print("⚠ Multi-source enrichment not available")

# Create data directory
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# ============================================================================
# JOBBER-STYLE COLOR SCHEME - ENHANCED
# ============================================================================
COLORS = {
    # Primary colors (Jobber-inspired - more vibrant)
    'primary': '#0D6EFD',      # Bright blue
    'primary_dark': '#0B5ED7',
    'primary_light': '#CFE2FF',
    'primary_hover': '#0A58CA',

    'secondary': '#06B6D4',    # Bright cyan
    'secondary_dark': '#0891B2',
    'secondary_light': '#CFFAFE',
    'secondary_hover': '#0E7490',

    # Status colors (more vibrant)
    'success': '#10B981',      # Emerald green
    'success_dark': '#059669',
    'success_light': '#D1FAE5',

    'warning': '#F59E0B',      # Amber
    'warning_dark': '#D97706',
    'warning_light': '#FEF3C7',

    'danger': '#EF4444',       # Red
    'danger_dark': '#DC2626',
    'danger_light': '#FEE2E2',

    'info': '#3B82F6',         # Blue
    'info_dark': '#2563EB',
    'info_light': '#DBEAFE',

    # Neutral colors
    'bg_primary': '#F8FAFC',   # Very light blue-gray
    'bg_secondary': '#FFFFFF', # White
    'bg_tertiary': '#E2E8F0',  # Light slate
    'bg_card': '#FFFFFF',      # Card background

    'text_primary': '#1E293B', # Slate-900
    'text_secondary': '#64748B', # Slate-500
    'text_light': '#FFFFFF',   # White
    'text_muted': '#94A3B8',   # Slate-400

    'border': '#E2E8F0',       # Light border
    'border_dark': '#CBD5E1',  # Darker border

    # Shadow
    'shadow': '#0000001A',     # 10% black

    # Signal colors
    'signal_high': '#D1FAE5',  # Light emerald
    'signal_med': '#FEF3C7',   # Light amber
    'signal_low': '#F1F5F9',   # Light slate
}

# ============================================================================
# CUSTOM WIDGETS - PROFESSIONAL UI COMPONENTS
# ============================================================================

class RoundedButton(tk.Canvas):
    """Modern rounded button with hover effects"""
    def __init__(self, parent, text="Button", command=None, bg_color=COLORS['primary'],
                 text_color=COLORS['text_light'], hover_color=None, width=120, height=40,
                 corner_radius=8, font=("Segoe UI", 10, "bold"), **kwargs):
        self.bg_color = bg_color
        self.text_color = text_color
        self.hover_color = hover_color or self._darken_color(bg_color)
        self.corner_radius = corner_radius
        self.command = command
        self.width = width
        self.height = height

        super().__init__(parent, width=width, height=height, bg=COLORS['bg_primary'],
                        highlightthickness=0, **kwargs)

        # Create rounded rectangle
        self.rounded_rect = self._create_rounded_rect(2, 2, width-2, height-2, corner_radius, fill=bg_color)

        # Create text
        self.text_item = self.create_text(width/2, height/2, text=text, fill=text_color, font=font)

        # Bind events
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _create_rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        """Create a rounded rectangle"""
        points = [
            x1+radius, y1,
            x2-radius, y1,
            x2, y1,
            x2, y1+radius,
            x2, y2-radius,
            x2, y2,
            x2-radius, y2,
            x1+radius, y2,
            x1, y2,
            x1, y2-radius,
            x1, y1+radius,
            x1, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)

    def _darken_color(self, hex_color):
        """Darken a hex color by 10%"""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r, g, b = max(0, r-20), max(0, g-20), max(0, b-20)
        return f'#{r:02x}{g:02x}{b:02x}'

    def _on_enter(self, event):
        """Hover effect"""
        self.itemconfig(self.rounded_rect, fill=self.hover_color)
        self.config(cursor="hand2")

    def _on_leave(self, event):
        """Remove hover effect"""
        self.itemconfig(self.rounded_rect, fill=self.bg_color)
        self.config(cursor="")

    def _on_click(self, event):
        """Handle click"""
        if self.command:
            self.command()

    def configure_text(self, text):
        """Update button text"""
        self.itemconfig(self.text_item, text=text)

class CardFrame(tk.Frame):
    """Card-style frame with shadow effect"""
    def __init__(self, parent, **kwargs):
        # Create container with padding for shadow
        container = tk.Frame(parent, bg=COLORS['bg_primary'])
        container.pack(**kwargs) if 'pack' not in str(kwargs) else None

        # Shadow frame
        shadow = tk.Frame(container, bg=COLORS['border'], bd=0)
        shadow.pack(padx=(2, 0), pady=(2, 0))

        # Main card frame
        super().__init__(shadow, bg=COLORS['bg_card'], relief=tk.FLAT, bd=0)
        super().pack(padx=0, pady=0)

        self.container = container


def create_stat_card(parent, value="0", label="Stat", color=COLORS['primary']):
    """Create a modern stat card"""
    card = tk.Frame(parent, bg=COLORS['bg_card'], relief=tk.FLAT, bd=0)

    # Add subtle border
    border = tk.Frame(card, bg=color, height=4)
    border.pack(fill=tk.X, side=tk.TOP)

    # Content area
    content = tk.Frame(card, bg=COLORS['bg_card'])
    content.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

    # Value
    value_label = tk.Label(content, text=value, font=("Segoe UI", 24, "bold"),
                          bg=COLORS['bg_card'], fg=color)
    value_label.pack()

    # Label
    label_widget = tk.Label(content, text=label, font=("Segoe UI", 10),
                           bg=COLORS['bg_card'], fg=COLORS['text_secondary'])
    label_widget.pack()

    return card, value_label

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
        self.root.geometry("1280x800")
        self.root.configure(bg=COLORS['bg_primary'])

        # Load data
        self.leads = load_json(DATA_DIR / "leads.json")
        self.config = load_json(DATA_DIR / "config.json")
        self.tenders = load_json(DATA_DIR / "tenders.json")

        # Create UI
        self.create_header()
        self.create_menu()
        self.create_stats_bar()
        self.create_notebook()

        # Update stats
        self.update_stats()

    def create_header(self):
        """Create modern app header"""
        header = tk.Frame(self.root, bg=COLORS['primary'], height=70)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        # App title
        title_frame = tk.Frame(header, bg=COLORS['primary'])
        title_frame.pack(side=tk.LEFT, padx=30, pady=15)

        tk.Label(title_frame, text="Calgary Industrial Lead Generator",
                font=("Segoe UI", 18, "bold"), bg=COLORS['primary'],
                fg=COLORS['text_light']).pack(side=tk.LEFT)

        # Version badge
        badge = tk.Label(title_frame, text="v2.0",
                        font=("Segoe UI", 9, "bold"),
                        bg=COLORS['primary_light'], fg=COLORS['primary'],
                        padx=8, pady=4)
        badge.pack(side=tk.LEFT, padx=(15, 0))

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
        """Create modern statistics dashboard"""
        stats_container = tk.Frame(self.root, bg=COLORS['bg_primary'])
        stats_container.pack(fill=tk.X, padx=20, pady=(15, 10))

        # Stats labels
        self.stat_labels = {}
        stats_config = [
            ("Total Leads", "total", COLORS['primary']),
            ("With Email", "email", COLORS['success']),
            ("Contacted", "contacted", COLORS['info']),
            ("Follow-ups Due", "followup", COLORS['warning']),
            ("New Tenders", "tenders", COLORS['secondary'])
        ]

        for i, (label, key, color) in enumerate(stats_config):
            # Create card frame with shadow effect
            card_container = tk.Frame(stats_container, bg=COLORS['bg_primary'])
            card_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=6)

            # Shadow
            shadow = tk.Frame(card_container, bg=COLORS['border_dark'])
            shadow.pack(fill=tk.BOTH, expand=True, padx=(0, 2), pady=(0, 2))

            # Card
            card = tk.Frame(shadow, bg=COLORS['bg_card'], relief=tk.FLAT, bd=0)
            card.pack(fill=tk.BOTH, expand=True)

            # Top colored bar
            top_bar = tk.Frame(card, bg=color, height=5)
            top_bar.pack(fill=tk.X, side=tk.TOP)

            # Content
            content = tk.Frame(card, bg=COLORS['bg_card'])
            content.pack(fill=tk.BOTH, expand=True, padx=15, pady=12)

            # Value
            value_label = tk.Label(content, text="0", font=("Segoe UI", 28, "bold"),
                                  bg=COLORS['bg_card'], fg=color)
            value_label.pack()

            # Label
            text_label = tk.Label(content, text=label, font=("Segoe UI", 10),
                                 bg=COLORS['bg_card'], fg=COLORS['text_secondary'])
            text_label.pack(pady=(2, 0))

            self.stat_labels[key] = value_label

    def create_notebook(self):
        """Create modern tabbed interface"""
        # Style the notebook
        style = ttk.Style()
        style.theme_use('clam')  # Use clam theme for better customization
        style.configure('TNotebook', background=COLORS['bg_primary'], borderwidth=0)
        style.configure('TNotebook.Tab', padding=[20, 12], font=('Segoe UI', 10, 'bold'),
                       background=COLORS['bg_tertiary'], foreground=COLORS['text_primary'])
        style.map('TNotebook.Tab',
                 background=[('selected', COLORS['bg_card'])],
                 foreground=[('selected', COLORS['primary'])],
                 expand=[('selected', [1, 1, 1, 0])])

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))

        # Create tabs
        self.create_leads_tab()
        self.create_add_tab()
        self.create_import_tab()
        self.create_outreach_tab()
        self.create_tenders_tab()
        self.create_settings_tab()

    def create_leads_tab(self):
        """Create leads management tab"""
        tab = tk.Frame(self.notebook, bg=COLORS['bg_primary'])
        self.notebook.add(tab, text="📋 Leads")

        # Search and filter frame - Modern card style
        filter_container = tk.Frame(tab, bg=COLORS['bg_primary'])
        filter_container.pack(fill=tk.X, padx=20, pady=(15, 10))

        # Shadow for filter card
        filter_shadow = tk.Frame(filter_container, bg=COLORS['border_dark'])
        filter_shadow.pack(fill=tk.X, padx=(0, 2), pady=(0, 2))

        filter_frame = tk.Frame(filter_shadow, bg=COLORS['bg_card'])
        filter_frame.pack(fill=tk.X, padx=15, pady=12)

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

        tk.Label(filter_frame, text="Enrichment:").pack(side=tk.LEFT, padx=(0, 5))
        self.enrichment_filter = ttk.Combobox(filter_frame, width=18,
                                             values=["All", "Enriched", "Not Enriched", "Needs Update"])
        self.enrichment_filter.set("All")
        self.enrichment_filter.bind('<<ComboboxSelected>>', lambda e: self.refresh_leads())
        self.enrichment_filter.pack(side=tk.LEFT, padx=(0, 20))

        RoundedButton(filter_frame, text="🔄 Refresh", command=self.refresh_leads,
                     bg_color=COLORS['info'], width=110, height=36, corner_radius=6).pack(side=tk.LEFT, padx=5)
        RoundedButton(filter_frame, text="✅ Validate Emails", command=self.bulk_validate_emails,
                     bg_color=COLORS['success'], width=150, height=36, corner_radius=6).pack(side=tk.LEFT, padx=5)

        # Leads table - Card style container
        table_container = tk.Frame(tab, bg=COLORS['bg_primary'])
        table_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 10))

        # Shadow for table card
        table_shadow = tk.Frame(table_container, bg=COLORS['border_dark'])
        table_shadow.pack(fill=tk.BOTH, expand=True, padx=(0, 2), pady=(0, 2))

        table_frame = tk.Frame(table_shadow, bg=COLORS['bg_card'])
        table_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical")
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal")
        hsb.pack(side=tk.BOTTOM, fill=tk.X)

        # Treeview
        columns = ("Company", "Contacts", "Signal", "Enrichment", "Status")
        self.leads_tree = ttk.Treeview(table_frame, columns=columns, show="headings",
                                       yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.config(command=self.leads_tree.yview)
        hsb.config(command=self.leads_tree.xview)

        # Column headings
        self.leads_tree.heading("Company", text="Company")
        self.leads_tree.heading("Contacts", text="Contact Information")
        self.leads_tree.heading("Signal", text="Signal Score")
        self.leads_tree.heading("Enrichment", text="Enrichment Status")
        self.leads_tree.heading("Status", text="Status")

        # Column widths
        self.leads_tree.column("Company", width=180)
        self.leads_tree.column("Contacts", width=400)
        self.leads_tree.column("Signal", width=100)
        self.leads_tree.column("Enrichment", width=140)
        self.leads_tree.column("Status", width=100)

        self.leads_tree.pack(fill=tk.BOTH, expand=True)

        # Double-click to edit
        self.leads_tree.bind('<Double-Button-1>', self.edit_lead)

        # Buttons - Modern rounded style
        btn_frame = tk.Frame(tab, bg=COLORS['bg_primary'])
        btn_frame.pack(fill=tk.X, padx=20, pady=(10, 15))

        RoundedButton(btn_frame, text="✏️ Edit Selected", command=self.edit_lead,
                     bg_color=COLORS['primary'], width=150, height=42).pack(side=tk.LEFT, padx=5)
        RoundedButton(btn_frame, text="🔄 Re-enrich Selected", command=self.re_enrich_lead,
                     bg_color=COLORS['secondary'], width=170, height=42).pack(side=tk.LEFT, padx=5)
        RoundedButton(btn_frame, text="🚀 Bulk Enrich", command=self.bulk_enrich_unenriched,
                     bg_color=COLORS['success'], width=140, height=42).pack(side=tk.LEFT, padx=5)
        RoundedButton(btn_frame, text="🔍 Find Duplicates", command=self.show_duplicates_dialog,
                     bg_color=COLORS['warning'], width=160, height=42).pack(side=tk.LEFT, padx=5)
        RoundedButton(btn_frame, text="🗑️ Delete Selected", command=self.delete_lead,
                     bg_color=COLORS['danger'], width=150, height=42).pack(side=tk.LEFT, padx=5)

        self.refresh_leads()

    def create_add_tab(self):
        """Create add new lead tab"""
        tab = tk.Frame(self.notebook, bg=COLORS['bg_primary'])
        self.notebook.add(tab, text="➕ Add New")

        # Create form in a card
        form_container = tk.Frame(tab, bg=COLORS['bg_primary'])
        form_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Shadow for form card
        form_shadow = tk.Frame(form_container, bg=COLORS['border_dark'])
        form_shadow.pack(fill=tk.BOTH, expand=True, padx=(0, 2), pady=(0, 2))

        form_frame = tk.Frame(form_shadow, bg=COLORS['bg_card'])
        form_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)

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

        RoundedButton(btn_frame, text="➕ Add Lead", command=self.add_lead,
                     bg_color=COLORS['primary'], width=140, height=44).pack(side=tk.LEFT, padx=5)
        RoundedButton(btn_frame, text="➕ Add & Scrape", command=self.add_and_scrape,
                     bg_color=COLORS['success'], width=160, height=44).pack(side=tk.LEFT, padx=5)
        RoundedButton(btn_frame, text="🗑️ Clear Form", command=self.clear_add_form,
                     bg_color=COLORS['text_secondary'], width=130, height=44).pack(side=tk.LEFT, padx=5)

    def create_import_tab(self):
        """Create import tab"""
        tab = tk.Frame(self.notebook, bg=COLORS['bg_primary'])
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

        RoundedButton(li_frame, text="📂 Select LinkedIn CSV File", command=self.import_linkedin,
                     bg_color=COLORS['info'], width=220, height=44).pack(anchor=tk.W, pady=5)

        # CSV Import section
        csv_frame = tk.LabelFrame(tab, text="Import from CSV", padx=20, pady=20)
        csv_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(csv_frame, text="Import a CSV file with columns: company, website, email, phone, industry, contact_name, contact_title",
                wraplength=600, justify=tk.LEFT).pack(anchor=tk.W, pady=(0, 10))

        RoundedButton(csv_frame, text="📂 Select CSV File", command=self.import_csv,
                     bg_color=COLORS['primary'], width=180, height=44).pack(anchor=tk.W, pady=5)

    def create_outreach_tab(self):
        """Create outreach tracking tab"""
        tab = tk.Frame(self.notebook, bg=COLORS['bg_primary'])
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

        RoundedButton(sel_frame, text="📝 Generate Draft", command=self.generate_draft,
                     bg_color=COLORS['primary'], width=160, height=38).pack(side=tk.LEFT, padx=5)

        # Draft display
        self.draft_display = scrolledtext.ScrolledText(draft_frame, height=15, wrap=tk.WORD)
        self.draft_display.pack(fill=tk.BOTH, expand=True, pady=(10, 10))

        # Draft buttons
        draft_btn_frame = tk.Frame(draft_frame, bg=COLORS['bg_primary'])
        draft_btn_frame.pack(fill=tk.X)

        RoundedButton(draft_btn_frame, text="📋 Copy to Clipboard", command=self.copy_draft,
                     bg_color=COLORS['text_secondary'], width=180, height=38).pack(side=tk.LEFT, padx=5)
        RoundedButton(draft_btn_frame, text="✅ Mark as Sent", command=self.mark_sent,
                     bg_color=COLORS['success'], width=160, height=38).pack(side=tk.LEFT, padx=5)

        self.update_outreach_stats()

    def create_tenders_tab(self):
        """Create tenders monitoring tab"""
        tab = tk.Frame(self.notebook, bg=COLORS['bg_primary'])
        self.notebook.add(tab, text="📢 Tenders")

        # Info and check button
        top_frame = tk.Frame(tab)
        top_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(top_frame, text="Monitor government and public sector contract opportunities",
                font=("Arial", 10)).pack(side=tk.LEFT)

        RoundedButton(top_frame, text="🔄 Check for New Tenders", command=self.check_tenders,
                     bg_color=COLORS['primary'], width=220, height=42).pack(side=tk.RIGHT, padx=5)

        # Tenders list
        self.tenders_text = scrolledtext.ScrolledText(tab, wrap=tk.WORD)
        self.tenders_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        self.refresh_tenders()

    def create_settings_tab(self):
        """Create settings tab"""
        tab = tk.Frame(self.notebook, bg=COLORS['bg_primary'])
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

        # API Keys section
        api_frame = tk.LabelFrame(tab, text="API Keys (for Enhanced Intelligence)", padx=20, pady=15)
        api_frame.pack(fill=tk.X, padx=20, pady=10)

        # Hunter.io
        tk.Label(api_frame, text="Hunter.io API Key").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.config_vars['hunter_api_key'] = tk.StringVar(value=self.config.get('hunter_api_key', ""))
        tk.Entry(api_frame, textvariable=self.config_vars['hunter_api_key'], width=50, show="*").grid(row=0, column=1, pady=5, sticky=tk.W)
        tk.Label(api_frame, text="hunter.io/users/sign_up (50 free/month)",
                font=("Arial", 8), fg=COLORS['text_secondary']).grid(row=0, column=2, sticky=tk.W, padx=(10, 0))
        self.config_vars['hunter_enabled'] = tk.BooleanVar(value=self.config.get('hunter_enabled', True))
        tk.Checkbutton(api_frame, text="Enabled", variable=self.config_vars['hunter_enabled']).grid(row=0, column=3, sticky=tk.W, padx=(10, 0))

        # Apollo.io
        tk.Label(api_frame, text="Apollo.io API Key").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.config_vars['apollo_api_key'] = tk.StringVar(value=self.config.get('apollo_api_key', ""))
        tk.Entry(api_frame, textvariable=self.config_vars['apollo_api_key'], width=50, show="*").grid(row=1, column=1, pady=5, sticky=tk.W)
        tk.Label(api_frame, text="app.apollo.io (50 free/month)",
                font=("Arial", 8), fg=COLORS['text_secondary']).grid(row=1, column=2, sticky=tk.W, padx=(10, 0))
        self.config_vars['apollo_enabled'] = tk.BooleanVar(value=self.config.get('apollo_enabled', True))
        tk.Checkbutton(api_frame, text="Enabled", variable=self.config_vars['apollo_enabled']).grid(row=1, column=3, sticky=tk.W, padx=(10, 0))

        # PeopleDataLabs
        tk.Label(api_frame, text="PeopleDataLabs API Key").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.config_vars['pdl_api_key'] = tk.StringVar(value=self.config.get('pdl_api_key', ""))
        tk.Entry(api_frame, textvariable=self.config_vars['pdl_api_key'], width=50, show="*").grid(row=2, column=1, pady=5, sticky=tk.W)
        tk.Label(api_frame, text="peopledatalabs.com (1,000 free/month)",
                font=("Arial", 8), fg=COLORS['text_secondary']).grid(row=2, column=2, sticky=tk.W, padx=(10, 0))
        self.config_vars['pdl_enabled'] = tk.BooleanVar(value=self.config.get('pdl_enabled', True))
        tk.Checkbutton(api_frame, text="Enabled", variable=self.config_vars['pdl_enabled']).grid(row=2, column=3, sticky=tk.W, padx=(10, 0))

        # Google Places
        tk.Label(api_frame, text="Google Places API Key").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.config_vars['google_places_api_key'] = tk.StringVar(value=self.config.get('google_places_api_key', ""))
        tk.Entry(api_frame, textvariable=self.config_vars['google_places_api_key'], width=50, show="*").grid(row=3, column=1, pady=5, sticky=tk.W)
        tk.Label(api_frame, text="console.cloud.google.com ($200 credit/month)",
                font=("Arial", 8), fg=COLORS['text_secondary']).grid(row=3, column=2, sticky=tk.W, padx=(10, 0))
        self.config_vars['google_places_enabled'] = tk.BooleanVar(value=self.config.get('google_places_enabled', True))
        tk.Checkbutton(api_frame, text="Enabled", variable=self.config_vars['google_places_enabled']).grid(row=3, column=3, sticky=tk.W, padx=(10, 0))

        # ZeroBounce
        tk.Label(api_frame, text="ZeroBounce API Key").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.config_vars['zerobounce_api_key'] = tk.StringVar(value=self.config.get('zerobounce_api_key', ""))
        tk.Entry(api_frame, textvariable=self.config_vars['zerobounce_api_key'], width=50, show="*").grid(row=4, column=1, pady=5, sticky=tk.W)
        tk.Label(api_frame, text="zerobounce.net (100 free/month)",
                font=("Arial", 8), fg=COLORS['text_secondary']).grid(row=4, column=2, sticky=tk.W, padx=(10, 0))
        self.config_vars['zerobounce_enabled'] = tk.BooleanVar(value=self.config.get('zerobounce_enabled', True))
        tk.Checkbutton(api_frame, text="Enabled", variable=self.config_vars['zerobounce_enabled']).grid(row=4, column=3, sticky=tk.W, padx=(10, 0))

        # Proxycurl
        tk.Label(api_frame, text="Proxycurl API Key").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.config_vars['proxycurl_api_key'] = tk.StringVar(value=self.config.get('proxycurl_api_key', ""))
        tk.Entry(api_frame, textvariable=self.config_vars['proxycurl_api_key'], width=50, show="*").grid(row=5, column=1, pady=5, sticky=tk.W)
        tk.Label(api_frame, text="nubela.co/proxycurl ($0.02-0.03 per profile)",
                font=("Arial", 8), fg=COLORS['text_secondary']).grid(row=5, column=2, sticky=tk.W, padx=(10, 0))
        self.config_vars['proxycurl_enabled'] = tk.BooleanVar(value=self.config.get('proxycurl_enabled', True))
        tk.Checkbutton(api_frame, text="Enabled", variable=self.config_vars['proxycurl_enabled']).grid(row=5, column=3, sticky=tk.W, padx=(10, 0))

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

        # API Credit Dashboard section
        credit_frame = tk.LabelFrame(tab, text="API Credit Dashboard", padx=20, pady=15)
        credit_frame.pack(fill=tk.X, padx=20, pady=10)

        # Create text widget to display credits
        self.credits_display = scrolledtext.ScrolledText(credit_frame, height=8, wrap=tk.WORD, font=("Courier", 9))
        self.credits_display.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.credits_display.insert(tk.END, "Click 'Check API Credits' to view remaining credits for each service.")
        self.credits_display.config(state=tk.DISABLED)

        # Refresh credits button
        RoundedButton(credit_frame, text="🔄 Check API Credits", command=self.refresh_api_credits,
                     bg_color=COLORS['info'], width=200, height=44).pack(pady=5)

        # Save button
        RoundedButton(tab, text="💾 Save Settings", command=self.save_settings,
                     bg_color=COLORS['success'], width=220, height=50, font=("Segoe UI", 11, "bold")).pack(pady=20)

    # ========================================================================
    # DATA METHODS
    # ========================================================================

    def _get_multi_source_enricher(self):
        """Create multi-source enricher with all API keys from config"""
        if not MULTI_SOURCE_AVAILABLE:
            return None

        api_keys = {}

        # Only include APIs that have both a key AND are enabled
        if self.config.get('apollo_enabled', True) and self.config.get('apollo_api_key'):
            api_keys['apollo_api_key'] = self.config['apollo_api_key']

        if self.config.get('pdl_enabled', True) and self.config.get('pdl_api_key'):
            api_keys['pdl_api_key'] = self.config['pdl_api_key']

        if self.config.get('google_places_enabled', True) and self.config.get('google_places_api_key'):
            api_keys['google_places_api_key'] = self.config['google_places_api_key']

        if self.config.get('zerobounce_enabled', True) and self.config.get('zerobounce_api_key'):
            api_keys['zerobounce_api_key'] = self.config['zerobounce_api_key']

        if self.config.get('proxycurl_enabled', True) and self.config.get('proxycurl_api_key'):
            api_keys['proxycurl_api_key'] = self.config['proxycurl_api_key']

        if not api_keys:
            return None

        return MultiSourceEnrichment(api_keys)

    def _calculate_similarity(self, str1, str2):
        """Calculate similarity ratio between two strings (0.0 to 1.0)"""
        if not str1 or not str2:
            return 0.0
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

    def _extract_domain(self, url):
        """Extract domain from URL"""
        if not url:
            return ""
        domain = url.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
        return domain.lower()

    def find_duplicates(self, company_name, website=None, threshold=0.85):
        """
        Find potential duplicate leads

        Args:
            company_name: Company name to check
            website: Optional website URL
            threshold: Similarity threshold (0.85 = 85% match)

        Returns:
            List of potential duplicate lead IDs and their similarity scores
        """
        duplicates = []

        for lead_id, lead in self.leads.items():
            # Check company name similarity
            name_similarity = self._calculate_similarity(company_name, lead.get('company_name', ''))

            # Check domain similarity if both have websites
            domain_match = False
            if website and lead.get('website'):
                new_domain = self._extract_domain(website)
                existing_domain = self._extract_domain(lead['website'])
                if new_domain and existing_domain and new_domain == existing_domain:
                    domain_match = True

            # Consider it a duplicate if:
            # 1. Name similarity is above threshold, OR
            # 2. Domains match exactly
            if name_similarity >= threshold or domain_match:
                duplicates.append({
                    'lead_id': lead_id,
                    'lead': lead,
                    'name_similarity': name_similarity,
                    'domain_match': domain_match,
                    'confidence': 'HIGH' if domain_match else ('HIGH' if name_similarity >= 0.9 else 'MEDIUM')
                })

        # Sort by confidence and similarity
        duplicates.sort(key=lambda x: (x['domain_match'], x['name_similarity']), reverse=True)
        return duplicates

    def scan_all_duplicates(self):
        """Scan all leads for duplicates and return groups of duplicates"""
        duplicate_groups = []
        checked = set()

        for lead_id, lead in self.leads.items():
            if lead_id in checked:
                continue

            # Find duplicates for this lead
            dupes = self.find_duplicates(
                lead.get('company_name', ''),
                lead.get('website'),
                threshold=0.85
            )

            # If we found duplicates (excluding self)
            if len(dupes) > 1:
                group = {
                    'primary': {'id': lead_id, 'lead': lead},
                    'duplicates': [d for d in dupes if d['lead_id'] != lead_id]
                }
                duplicate_groups.append(group)

                # Mark all leads in this group as checked
                checked.add(lead_id)
                for d in dupes:
                    checked.add(d['lead_id'])

        return duplicate_groups

    def get_api_credits(self):
        """Fetch remaining API credits for all configured services"""
        credits = {}

        # ZeroBounce credits
        if self.config.get('zerobounce_api_key') and self.config.get('zerobounce_enabled', True):
            try:
                from zerobounce_integration import ZeroBounceIntegration
                zb = ZeroBounceIntegration(self.config['zerobounce_api_key'])
                result = zb.get_credits()
                if result.get('success'):
                    credits['zerobounce'] = {
                        'available': result.get('credits', 'N/A'),
                        'status': 'OK'
                    }
                else:
                    credits['zerobounce'] = {
                        'available': 'Error',
                        'status': result.get('error', 'Unknown error')
                    }
            except Exception as e:
                credits['zerobounce'] = {
                    'available': 'Error',
                    'status': str(e)
                }

        # Note: Most other APIs don't provide credit checking endpoints
        # Adding placeholders for consistency
        if self.config.get('hunter_api_key') and self.config.get('hunter_enabled', True):
            credits['hunter'] = {
                'available': 'Check hunter.io dashboard',
                'status': 'API key configured'
            }

        if self.config.get('apollo_api_key') and self.config.get('apollo_enabled', True):
            credits['apollo'] = {
                'available': 'Check app.apollo.io dashboard',
                'status': 'API key configured'
            }

        if self.config.get('pdl_api_key') and self.config.get('pdl_enabled', True):
            credits['peopledatalabs'] = {
                'available': 'Check peopledatalabs.com dashboard',
                'status': 'API key configured'
            }

        if self.config.get('google_places_api_key') and self.config.get('google_places_enabled', True):
            credits['google_places'] = {
                'available': 'Check console.cloud.google.com',
                'status': 'API key configured'
            }

        if self.config.get('proxycurl_api_key') and self.config.get('proxycurl_enabled', True):
            credits['proxycurl'] = {
                'available': 'Check nubela.co dashboard',
                'status': 'API key configured'
            }

        return credits

    def log_activity(self, lead_id, activity_type, description, details=None):
        """
        Log an activity for a lead

        Args:
            lead_id: ID of the lead
            activity_type: Type of activity (created, contacted, enriched, note, status_change, etc.)
            description: Human-readable description
            details: Optional additional details dictionary
        """
        if lead_id not in self.leads:
            return

        if 'activity_log' not in self.leads[lead_id]:
            self.leads[lead_id]['activity_log'] = []

        activity = {
            'timestamp': datetime.now().isoformat(),
            'type': activity_type,
            'description': description,
            'details': details or {}
        }

        self.leads[lead_id]['activity_log'].append(activity)

    def get_enrichment_status(self, lead):
        """
        Determine enrichment status of a lead

        Returns:
            tuple: (status_text, status_icon, needs_update)
            - status_text: "Enriched", "Not Enriched", "Needs Update"
            - status_icon: emoji icon
            - needs_update: boolean indicating if data is stale
        """
        has_intelligence = lead.get('intelligence') is not None
        has_multi_source = has_intelligence and lead['intelligence'].get('multi_source') is not None

        # If no intelligence data at all
        if not has_intelligence:
            return ("Not Enriched", "❌", False)

        # Check if intelligence is recent (within 30 days)
        last_updated = lead.get('intelligence', {}).get('last_updated')
        needs_update = False

        if last_updated:
            try:
                updated_date = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                days_old = (datetime.now() - updated_date).days
                if days_old > 30:
                    needs_update = True
            except:
                pass

        # Has intelligence and multi-source data
        if has_multi_source:
            sources_count = len(lead['intelligence'].get('multi_source', {}).get('sources_used', []))
            if needs_update:
                return ("Needs Update", "⚠️", True)
            return (f"✓ Enriched ({sources_count} APIs)", "✅", False)

        # Has basic intelligence only
        if needs_update:
            return ("Needs Update", "⚠️", True)
        return ("✓ Basic", "🔵", False)

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
        enrichment_filter = self.enrichment_filter.get()

        # Filter and display leads
        for lead_id, lead in self.leads.items():
            # Apply filters
            if search and search not in lead.get('company_name', '').lower():
                continue
            if status_filter != "All" and lead.get('status') != status_filter:
                continue

            # Apply enrichment filter
            enrichment_status, enrichment_icon, needs_update = self.get_enrichment_status(lead)
            if enrichment_filter == "Enriched" and "Not Enriched" in enrichment_status:
                continue
            elif enrichment_filter == "Not Enriched" and "Not Enriched" not in enrichment_status:
                continue
            elif enrichment_filter == "Needs Update" and not needs_update:
                continue

            # Insert parent row (company info)
            parent_id = self.leads_tree.insert('', tk.END, iid=lead_id, values=(
                lead.get('company_name', ''),
                '',  # Contact info will be in child rows
                lead.get('signal_score', 0),
                f"{enrichment_icon} {enrichment_status}",
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

        # Check for duplicates
        website = self.add_vars['website'].get().strip()
        duplicates = self.find_duplicates(company, website, threshold=0.85)

        if duplicates:
            # Show duplicate warning dialog
            dupe = duplicates[0]  # Get best match
            confidence = dupe['confidence']
            existing_lead = dupe['lead']

            message = f"⚠️ Potential Duplicate Detected!\n\n"
            message += f"Match Confidence: {confidence}\n"
            message += f"Existing Lead: {existing_lead.get('company_name')}\n"
            if existing_lead.get('website'):
                message += f"Website: {existing_lead['website']}\n"
            message += f"\nDo you want to:\n"
            message += f"• YES - Add anyway (will create duplicate)\n"
            message += f"• NO - Cancel and edit existing lead"

            if not messagebox.askyesno("Duplicate Found", message):
                # User chose NO - don't add, just return
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
            'activity_log': [{
                'timestamp': datetime.now().isoformat(),
                'type': 'created',
                'description': f'Lead created from {self.add_vars["source"].get() or "manual entry"}',
                'details': {}
            }]
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

        # Check for duplicates
        website = self.add_vars['website'].get().strip()
        duplicates = self.find_duplicates(company, website, threshold=0.85)

        if duplicates:
            # Show duplicate warning dialog
            dupe = duplicates[0]  # Get best match
            confidence = dupe['confidence']
            existing_lead = dupe['lead']

            message = f"⚠️ Potential Duplicate Detected!\n\n"
            message += f"Match Confidence: {confidence}\n"
            message += f"Existing Lead: {existing_lead.get('company_name')}\n"
            if existing_lead.get('website'):
                message += f"Website: {existing_lead['website']}\n"
            message += f"\nDo you want to:\n"
            message += f"• YES - Add anyway (will create duplicate)\n"
            message += f"• NO - Cancel and edit existing lead"

            if not messagebox.askyesno("Duplicate Found", message):
                # User chose NO - don't add, just return
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
            'intelligence': None,
            'activity_log': [{
                'timestamp': datetime.now().isoformat(),
                'type': 'created',
                'description': f'Lead created with enhanced scraping from {self.add_vars["source"].get() or "manual entry"}',
                'details': {}
            }]
        }

        # Enhanced scraping if website provided
        if lead['website'] and UNIFIED_SCORING_AVAILABLE:
            self.root.config(cursor="wait")
            self.root.update()

            try:
                # Use unified scoring with Hunter.io API key from settings
                hunter_key = self.config.get('hunter_api_key', None)
                if hunter_key == '':
                    hunter_key = None
                scorer = UnifiedSignalScoring(hunter_api_key=hunter_key)
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

        # Multi-source enrichment (additional APIs)
        enricher = self._get_multi_source_enricher()
        if enricher and lead['website']:
            try:
                self.root.config(cursor="wait")
                self.root.update()

                # Extract domain from website
                domain = lead['website'].replace('https://', '').replace('http://', '').split('/')[0]

                # Enrich company data
                company_data = enricher.enrich_company(
                    company_name=lead['company_name'],
                    domain=domain,
                    location="Calgary, AB"
                )

                if company_data.get('sources_used'):
                    # Store multi-source data
                    if not lead.get('intelligence'):
                        lead['intelligence'] = {}
                    lead['intelligence']['multi_source'] = company_data

                    # Extract additional phones
                    aggregated = company_data.get('aggregated', {})
                    if aggregated.get('phones'):
                        if not lead.get('all_phones'):
                            lead['all_phones'] = []
                        for phone in aggregated['phones']:
                            if phone not in lead['all_phones']:
                                lead['all_phones'].append(phone)

                # Find additional contacts
                contacts_data = enricher.find_contacts(lead['company_name'], domain, limit=10)

                if contacts_data.get('total_contacts', 0) > 0:
                    # Store contact data
                    if not lead.get('intelligence'):
                        lead['intelligence'] = {}
                    lead['intelligence']['contacts'] = contacts_data

                    # Add emails to all_emails list
                    if not lead.get('all_emails'):
                        lead['all_emails'] = []

                    for contact in contacts_data['all_contacts']:
                        email = contact.get('email')
                        if email and email not in lead['all_emails']:
                            lead['all_emails'].append(email)

                        # Store contact details
                        if not lead.get('contact_details'):
                            lead['contact_details'] = []
                        lead['contact_details'].append({
                            'email': contact.get('email'),
                            'name': contact.get('name'),
                            'title': contact.get('title'),
                            'phone': contact.get('phone'),
                            'source': contact.get('source'),
                            'verified': contact.get('verified', False)
                        })

                self.root.config(cursor="")

            except Exception as e:
                print(f"Multi-source enrichment error: {e}")
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

        # Activity Timeline
        tk.Label(form, text="Activity Timeline", font=("Arial", 9, "bold")).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        row += 1

        activity_frame = tk.Frame(form, relief=tk.SUNKEN, borderwidth=1)
        activity_frame.grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=5)

        activity_text = scrolledtext.ScrolledText(activity_frame, height=6, wrap=tk.WORD, font=("Arial", 9))
        activity_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Display activity log
        if lead.get('activity_log'):
            for activity in reversed(lead['activity_log']):  # Most recent first
                timestamp = datetime.fromisoformat(activity['timestamp'].replace('Z', '+00:00'))
                time_str = timestamp.strftime('%Y-%m-%d %H:%M')

                icon = {
                    'created': '🆕',
                    'enriched': '🔍',
                    'contacted': '📧',
                    'note': '📝',
                    'status_change': '📊',
                    'validated': '✅'
                }.get(activity['type'], '•')

                activity_text.insert(tk.END, f"{icon} {time_str} - {activity['description']}\n")

            activity_text.config(state=tk.DISABLED)
        else:
            activity_text.insert(tk.END, "No activity recorded yet.")
            activity_text.config(state=tk.DISABLED)

        row += 1

        # Add Note button
        def add_note_to_lead():
            note_dialog = tk.Toplevel(dialog)
            note_dialog.title("Add Note")
            note_dialog.geometry("400x250")

            tk.Label(note_dialog, text="Add a note to this lead:", font=("Arial", 10, "bold")).pack(pady=10)

            note_input = scrolledtext.ScrolledText(note_dialog, height=8, wrap=tk.WORD)
            note_input.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            def save_note():
                note_content = note_input.get(1.0, tk.END).strip()
                if note_content:
                    self.log_activity(lead_id, 'note', f'Note added: {note_content[:50]}...', {'full_note': note_content})
                    save_json(DATA_DIR / "leads.json", self.leads)
                    messagebox.showinfo("Success", "Note added!")
                    note_dialog.destroy()
                    dialog.destroy()
                    self.edit_lead()  # Reopen to show new note

            tk.Button(note_dialog, text="💾 Save Note", command=save_note,
                     bg=COLORS['primary'], fg=COLORS['text_light'], padx=15, pady=5).pack(pady=5)

        tk.Button(form, text="📝 Add Note", command=add_note_to_lead,
                 bg=COLORS['info'], fg=COLORS['text_light'], padx=10, pady=4).grid(
            row=row, column=1, pady=5, sticky=tk.E)
        row += 1

        # Buttons
        btn_frame = tk.Frame(form)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=20)

        def save_changes():
            # Check for status change
            old_status = lead.get('status')
            new_status = edit_vars['status'].get()

            for key, var in edit_vars.items():
                lead[key] = var.get()
            lead['notes'] = notes_text.get(1.0, tk.END).strip()

            # Log status change activity
            if old_status != new_status:
                self.log_activity(lead_id, 'status_change',
                    f'Status changed from "{old_status}" to "{new_status}"')

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

                # Use unified scoring with Hunter.io API key from settings
                hunter_key = self.config.get('hunter_api_key', None)
                if hunter_key == '':
                    hunter_key = None
                scorer = UnifiedSignalScoring(hunter_api_key=hunter_key)
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

    def re_enrich_lead(self):
        """Re-enrich selected lead with latest intelligence"""
        selection = self.leads_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a lead to re-enrich")
            return

        # Get lead_id (filter out child rows)
        lead_id = selection[0]
        if '_contact_' in lead_id:
            # User selected a contact row, extract parent lead_id
            lead_id = lead_id.split('_contact_')[0]

        if lead_id not in self.leads:
            messagebox.showerror("Error", "Invalid lead selected")
            return

        lead = self.leads[lead_id]

        # Check if lead has a website
        if not lead.get('website'):
            messagebox.showwarning("Warning",
                f"{lead['company_name']} has no website.\n\n" +
                "Please add a website URL first before re-enriching.")
            return

        # Confirm action
        if not messagebox.askyesno("Confirm Re-enrich",
            f"Re-enrich {lead['company_name']}?\n\n" +
            "This will:\n" +
            "• Gather latest intelligence from all enabled sources\n" +
            "• Update signal scores\n" +
            "• Find new contacts\n\n" +
            "Note: This may use API credits."):
            return

        # Start enrichment
        self.root.config(cursor="wait")
        self.root.update()

        try:
            # Run unified scoring if available
            if UNIFIED_SCORING_AVAILABLE:
                hunter_key = self.config.get('hunter_api_key', None)
                if hunter_key == '':
                    hunter_key = None

                # Only use hunter if enabled
                if not self.config.get('hunter_enabled', True):
                    hunter_key = None

                scorer = UnifiedSignalScoring(hunter_api_key=hunter_key)
                result = scorer.calculate_unified_score(
                    company_name=lead['company_name'],
                    website=lead['website'],
                    email=lead.get('general_email') if lead.get('general_email') else None,
                    check_news=True,
                    check_permits=True,
                    check_linkedin=True,
                    check_email_enrichment=bool(lead.get('general_email'))
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
                    from enhanced_scraper import scrape_website as enhanced_scrape
                    scrape_result = enhanced_scrape(lead['website'])

                    if scrape_result['emails']:
                        if not lead.get('general_email'):
                            lead['general_email'] = scrape_result['emails'][0]
                        lead['all_emails'] = scrape_result['emails']

                    if scrape_result['phones']:
                        if not lead.get('general_phone'):
                            lead['general_phone'] = scrape_result['phones'][0]
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

            # Run multi-source enrichment
            enricher = self._get_multi_source_enricher()
            if enricher:
                # Extract domain from website
                domain = lead['website'].replace('https://', '').replace('http://', '').split('/')[0]

                # Enrich company data
                company_data = enricher.enrich_company(
                    company_name=lead['company_name'],
                    domain=domain,
                    location="Calgary, AB"
                )

                if company_data.get('sources_used'):
                    # Store multi-source data
                    if not lead.get('intelligence'):
                        lead['intelligence'] = {}
                    lead['intelligence']['multi_source'] = company_data

                    # Extract additional phones
                    aggregated = company_data.get('aggregated', {})
                    if aggregated.get('phones'):
                        if not lead.get('all_phones'):
                            lead['all_phones'] = []
                        for phone in aggregated['phones']:
                            if phone not in lead['all_phones']:
                                lead['all_phones'].append(phone)

                # Find additional contacts
                contacts_data = enricher.find_contacts(lead['company_name'], domain, limit=10)

                if contacts_data.get('total_contacts', 0) > 0:
                    # Store contact data
                    if not lead.get('intelligence'):
                        lead['intelligence'] = {}
                    lead['intelligence']['contacts'] = contacts_data

                    # Add emails to all_emails list
                    if not lead.get('all_emails'):
                        lead['all_emails'] = []

                    for contact in contacts_data['all_contacts']:
                        email = contact.get('email')
                        if email and email not in lead['all_emails']:
                            lead['all_emails'].append(email)

                        # Store contact details (replace old ones)
                        if not lead.get('contact_details'):
                            lead['contact_details'] = []

                        # Check if contact already exists
                        existing = False
                        for i, existing_contact in enumerate(lead['contact_details']):
                            if existing_contact.get('email') == email:
                                # Update existing contact
                                lead['contact_details'][i] = {
                                    'email': contact.get('email'),
                                    'name': contact.get('name'),
                                    'title': contact.get('title'),
                                    'phone': contact.get('phone'),
                                    'source': contact.get('source'),
                                    'verified': contact.get('verified', False)
                                }
                                existing = True
                                break

                        # Add new contact if it doesn't exist
                        if not existing:
                            lead['contact_details'].append({
                                'email': contact.get('email'),
                                'name': contact.get('name'),
                                'title': contact.get('title'),
                                'phone': contact.get('phone'),
                                'source': contact.get('source'),
                                'verified': contact.get('verified', False)
                            })

            # Log enrichment activity
            sources_used = []
            if lead.get('intelligence'):
                if lead['intelligence'].get('sources'):
                    sources_used.extend(lead['intelligence']['sources'].keys())
                if lead['intelligence'].get('multi_source', {}).get('sources_used'):
                    sources_used.extend(lead['intelligence']['multi_source']['sources_used'])

            if sources_used:
                self.log_activity(lead_id, 'enriched',
                    f'Lead re-enriched using {len(set(sources_used))} data sources',
                    {'sources': list(set(sources_used)), 'score': lead.get('signal_score', 0)})

            # Save
            save_json(DATA_DIR / "leads.json", self.leads)

            # Update UI
            self.refresh_leads()
            self.update_stats()

            self.root.config(cursor="")

            summary = f"✅ Re-enrichment Complete!\n\n"
            summary += f"Company: {lead['company_name']}\n"
            summary += f"Updated Signal Score: {lead.get('signal_score', 0)}/100\n"
            summary += f"Priority: {lead.get('priority', 'Unknown')}\n\n"

            if sources_used:
                summary += f"Data Sources Used:\n"
                for source in set(sources_used):
                    summary += f"  • {source.title()}\n"

            if lead.get('all_emails'):
                summary += f"\nTotal Emails Found: {len(lead['all_emails'])}\n"
            if lead.get('all_phones'):
                summary += f"Total Phones Found: {len(lead['all_phones'])}\n"

            messagebox.showinfo("Re-enrichment Complete", summary)

        except Exception as e:
            self.root.config(cursor="")
            messagebox.showerror("Error", f"Re-enrichment failed:\n\n{str(e)}")
            print(f"Re-enrichment error: {e}")

    def show_duplicates_dialog(self):
        """Show dialog with all duplicate leads found"""
        # Scan for duplicates
        self.root.config(cursor="wait")
        self.root.update()

        duplicate_groups = self.scan_all_duplicates()

        self.root.config(cursor="")

        if not duplicate_groups:
            messagebox.showinfo("No Duplicates", "No duplicate leads found!\n\nYour database is clean.")
            return

        # Create duplicates dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Duplicate Leads Found")
        dialog.geometry("800x600")

        # Header
        header = tk.Label(dialog, text=f"🔍 Found {len(duplicate_groups)} Duplicate Groups",
                         font=("Arial", 14, "bold"), fg=COLORS['warning'])
        header.pack(pady=10)

        # Instructions
        instructions = tk.Label(dialog,
            text="Review each group and choose which leads to keep/delete.\n" +
                 "The first lead in each group is suggested as primary.",
            wraplength=750)
        instructions.pack(pady=5)

        # Scrollable frame for duplicates
        canvas = tk.Canvas(dialog)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Display duplicate groups
        for i, group in enumerate(duplicate_groups):
            primary = group['primary']['lead']
            duplicates = group['duplicates']

            # Group frame
            group_frame = tk.LabelFrame(scrollable_frame,
                text=f"Group {i+1}: {primary.get('company_name')} ({len(duplicates) + 1} matches)",
                padx=10, pady=10, font=("Arial", 10, "bold"))
            group_frame.pack(fill=tk.X, padx=10, pady=5)

            # Primary lead
            primary_frame = tk.Frame(group_frame, relief=tk.RAISED, borderwidth=1, bg=COLORS['primary_light'])
            primary_frame.pack(fill=tk.X, pady=2)

            tk.Label(primary_frame, text="PRIMARY (Keep this one):",
                    font=("Arial", 9, "bold"), bg=COLORS['primary_light']).pack(anchor=tk.W, padx=5, pady=2)
            tk.Label(primary_frame, text=f"  Company: {primary.get('company_name')}",
                    bg=COLORS['primary_light']).pack(anchor=tk.W, padx=5)
            if primary.get('website'):
                tk.Label(primary_frame, text=f"  Website: {primary.get('website')}",
                        bg=COLORS['primary_light']).pack(anchor=tk.W, padx=5)
            tk.Label(primary_frame, text=f"  Score: {primary.get('signal_score', 0)} | Status: {primary.get('status', 'New')}",
                    bg=COLORS['primary_light']).pack(anchor=tk.W, padx=5)

            # Duplicate leads
            for d in duplicates:
                dupe_lead = d['lead']
                dupe_id = d['lead_id']
                confidence = d['confidence']

                dupe_frame = tk.Frame(group_frame, relief=tk.SUNKEN, borderwidth=1)
                dupe_frame.pack(fill=tk.X, pady=2)

                info_label = tk.Label(dupe_frame, text=f"DUPLICATE ({confidence} confidence):",
                                     font=("Arial", 9, "bold"), fg=COLORS['danger'])
                info_label.pack(anchor=tk.W, padx=5, pady=2)

                tk.Label(dupe_frame, text=f"  Company: {dupe_lead.get('company_name')}").pack(anchor=tk.W, padx=5)
                if dupe_lead.get('website'):
                    tk.Label(dupe_frame, text=f"  Website: {dupe_lead.get('website')}").pack(anchor=tk.W, padx=5)
                tk.Label(dupe_frame, text=f"  Score: {dupe_lead.get('signal_score', 0)} | Status: {dupe_lead.get('status', 'New')}").pack(anchor=tk.W, padx=5)

                # Delete button for duplicate
                tk.Button(dupe_frame, text="🗑️ Delete This Duplicate",
                         command=lambda lid=dupe_id, dlg=dialog: self.delete_duplicate(lid, dlg),
                         bg=COLORS['danger'], fg=COLORS['text_light'], padx=10, pady=4).pack(anchor=tk.E, padx=5, pady=5)

        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")

        # Close button
        tk.Button(dialog, text="Close", command=dialog.destroy,
                 bg=COLORS['text_secondary'], fg=COLORS['text_light'], padx=20, pady=8).pack(pady=10)

    def delete_duplicate(self, lead_id, dialog):
        """Delete a duplicate lead and refresh the duplicates dialog"""
        if lead_id in self.leads:
            lead = self.leads[lead_id]
            if messagebox.askyesno("Confirm Delete", f"Delete duplicate: {lead['company_name']}?"):
                del self.leads[lead_id]
                save_json(DATA_DIR / "leads.json", self.leads)
                self.refresh_leads()
                self.update_stats()
                messagebox.showinfo("Success", "Duplicate deleted!")

                # Close and reopen dialog to refresh
                dialog.destroy()
                self.show_duplicates_dialog()

    def bulk_validate_emails(self):
        """Validate all emails in database using ZeroBounce"""
        # Check if ZeroBounce is configured
        if not self.config.get('zerobounce_api_key') or not self.config.get('zerobounce_enabled', True):
            messagebox.showwarning("ZeroBounce Not Configured",
                "Please configure your ZeroBounce API key in Settings\n" +
                "and make sure it's enabled before validating emails.")
            return

        # Collect all emails
        all_emails = set()
        email_to_leads = {}  # Map email to lead IDs

        for lead_id, lead in self.leads.items():
            # Collect general email
            if lead.get('general_email'):
                email = lead['general_email'].strip().lower()
                all_emails.add(email)
                if email not in email_to_leads:
                    email_to_leads[email] = []
                email_to_leads[email].append(lead_id)

            # Collect all_emails
            if lead.get('all_emails'):
                for email in lead['all_emails']:
                    email = email.strip().lower()
                    all_emails.add(email)
                    if email not in email_to_leads:
                        email_to_leads[email] = []
                    email_to_leads[email].append(lead_id)

        if not all_emails:
            messagebox.showinfo("No Emails", "No emails found in your leads database.")
            return

        # Confirm action
        if not messagebox.askyesno("Confirm Bulk Validation",
            f"Validate {len(all_emails)} unique emails?\n\n" +
            f"This will use {len(all_emails)} ZeroBounce credits.\n\n" +
            "Valid emails will be marked with ✓\n" +
            "Invalid emails will be flagged.\n\n" +
            "Continue?"):
            return

        # Create progress dialog
        progress_dialog = tk.Toplevel(self.root)
        progress_dialog.title("Validating Emails...")
        progress_dialog.geometry("500x300")
        progress_dialog.transient(self.root)

        tk.Label(progress_dialog, text="Email Validation in Progress",
                font=("Arial", 12, "bold")).pack(pady=10)

        progress_text = scrolledtext.ScrolledText(progress_dialog, height=10, wrap=tk.WORD)
        progress_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        progress_label = tk.Label(progress_dialog, text="Starting validation...")
        progress_label.pack(pady=5)

        # Perform validation in a thread to keep UI responsive
        def validate_thread():
            try:
                from zerobounce_integration import ZeroBounceIntegration
                zb = ZeroBounceIntegration(self.config['zerobounce_api_key'])

                email_list = list(all_emails)
                valid_count = 0
                invalid_count = 0
                error_count = 0

                for i, email in enumerate(email_list):
                    progress_label.config(text=f"Validating {i+1}/{len(email_list)}...")
                    progress_text.insert(tk.END, f"Checking {email}... ")
                    progress_text.see(tk.END)
                    progress_dialog.update()

                    result = zb.validate_email(email)

                    if result.get('success'):
                        status = result.get('status', 'unknown')
                        if status == 'valid':
                            progress_text.insert(tk.END, "✓ VALID\n", 'valid')
                            valid_count += 1

                            # Update leads with validation status
                            for lead_id in email_to_leads.get(email, []):
                                if 'email_validation' not in self.leads[lead_id]:
                                    self.leads[lead_id]['email_validation'] = {}
                                self.leads[lead_id]['email_validation'][email] = {
                                    'status': 'valid',
                                    'validated_at': datetime.now().isoformat()
                                }
                        else:
                            progress_text.insert(tk.END, f"✗ {status.upper()}\n", 'invalid')
                            invalid_count += 1

                            # Update leads with validation status
                            for lead_id in email_to_leads.get(email, []):
                                if 'email_validation' not in self.leads[lead_id]:
                                    self.leads[lead_id]['email_validation'] = {}
                                self.leads[lead_id]['email_validation'][email] = {
                                    'status': status,
                                    'validated_at': datetime.now().isoformat()
                                }
                    else:
                        progress_text.insert(tk.END, f"ERROR: {result.get('error', 'Unknown')}\n", 'error')
                        error_count += 1

                    progress_text.see(tk.END)

                    # Small delay to avoid rate limiting
                    time.sleep(0.5)

                # Save updated leads
                save_json(DATA_DIR / "leads.json", self.leads)

                # Summary
                progress_text.insert(tk.END, "\n" + "=" * 50 + "\n")
                progress_text.insert(tk.END, f"VALIDATION COMPLETE\n", 'header')
                progress_text.insert(tk.END, f"Total Emails: {len(email_list)}\n")
                progress_text.insert(tk.END, f"✓ Valid: {valid_count}\n", 'valid')
                progress_text.insert(tk.END, f"✗ Invalid: {invalid_count}\n", 'invalid')
                if error_count > 0:
                    progress_text.insert(tk.END, f"⚠ Errors: {error_count}\n", 'error')

                progress_label.config(text="Validation Complete!")

                # Configure text tags
                progress_text.tag_config('valid', foreground='green', font=('Arial', 9, 'bold'))
                progress_text.tag_config('invalid', foreground='red')
                progress_text.tag_config('error', foreground='orange')
                progress_text.tag_config('header', font=('Arial', 10, 'bold'))

                # Add close button
                tk.Button(progress_dialog, text="Close", command=progress_dialog.destroy,
                         bg=COLORS['primary'], fg=COLORS['text_light'], padx=20, pady=8).pack(pady=10)

            except Exception as e:
                progress_text.insert(tk.END, f"\n\nERROR: {str(e)}\n", 'error')
                progress_label.config(text="Validation Failed!")

        # Start validation thread
        thread = Thread(target=validate_thread)
        thread.daemon = True
        thread.start()

    def bulk_enrich_unenriched(self):
        """Bulk enrich all unenriched leads"""
        # Find all unenriched leads
        unenriched_leads = []
        needs_update_leads = []

        for lead_id, lead in self.leads.items():
            if not lead.get('website'):
                continue  # Skip leads without websites

            status_text, icon, needs_update = self.get_enrichment_status(lead)

            if "Not Enriched" in status_text:
                unenriched_leads.append((lead_id, lead))
            elif needs_update:
                needs_update_leads.append((lead_id, lead))

        total_to_enrich = len(unenriched_leads) + len(needs_update_leads)

        if total_to_enrich == 0:
            messagebox.showinfo("All Enriched",
                "All leads with websites are already enriched!\n\n" +
                "No action needed.")
            return

        # Show confirmation dialog
        message = f"Found leads to enrich:\n\n"
        message += f"• {len(unenriched_leads)} not enriched\n"
        message += f"• {len(needs_update_leads)} need update (>30 days old)\n"
        message += f"\nTotal: {total_to_enrich} leads\n\n"
        message += "This will:\n"
        message += "• Run unified signal scoring\n"
        message += "• Gather multi-source intelligence\n"
        message += "• Find contacts\n"
        message += "• Use API credits\n\n"
        message += f"Estimated time: ~{total_to_enrich * 2} seconds\n\n"
        message += "Continue?"

        if not messagebox.askyesno("Bulk Enrich Confirmation", message):
            return

        # Create progress dialog
        progress_dialog = tk.Toplevel(self.root)
        progress_dialog.title("Bulk Enrichment in Progress...")
        progress_dialog.geometry("600x400")
        progress_dialog.transient(self.root)

        tk.Label(progress_dialog, text="Bulk Enrichment Progress",
                font=("Arial", 12, "bold")).pack(pady=10)

        progress_text = scrolledtext.ScrolledText(progress_dialog, height=15, wrap=tk.WORD)
        progress_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        progress_label = tk.Label(progress_dialog, text="Starting bulk enrichment...")
        progress_label.pack(pady=5)

        # Progress bar
        progress_bar = ttk.Progressbar(progress_dialog, length=500, mode='determinate')
        progress_bar.pack(pady=10)
        progress_bar['maximum'] = total_to_enrich
        progress_bar['value'] = 0

        # Perform enrichment in thread
        def enrich_thread():
            try:
                all_leads = unenriched_leads + needs_update_leads
                success_count = 0
                error_count = 0

                for i, (lead_id, lead) in enumerate(all_leads):
                    progress_label.config(text=f"Enriching {i+1}/{total_to_enrich}: {lead['company_name']}")
                    progress_text.insert(tk.END, f"\n[{i+1}/{total_to_enrich}] {lead['company_name']}...\n")
                    progress_text.see(tk.END)
                    progress_dialog.update()

                    try:
                        # Run unified scoring
                        if UNIFIED_SCORING_AVAILABLE:
                            hunter_key = self.config.get('hunter_api_key') if self.config.get('hunter_enabled', True) else None
                            if hunter_key == '':
                                hunter_key = None

                            from unified_signal_scoring import UnifiedSignalScoring
                            scorer = UnifiedSignalScoring(hunter_api_key=hunter_key)
                            result = scorer.calculate_unified_score(
                                company_name=lead['company_name'],
                                website=lead['website'],
                                email=lead.get('general_email'),
                                check_news=True,
                                check_permits=True,
                                check_linkedin=True,
                                check_email_enrichment=bool(lead.get('general_email'))
                            )

                            # Update lead
                            lead['signal_score'] = result['total_score']
                            lead['priority'] = result.get('priority', 'LOW')
                            lead['intelligence'] = {
                                'last_updated': result['analysis_date'],
                                'sources': result['sources'],
                                'all_signals': result['all_signals']
                            }

                        # Run multi-source enrichment
                        enricher = self._get_multi_source_enricher()
                        if enricher:
                            domain = lead['website'].replace('https://', '').replace('http://', '').split('/')[0]

                            company_data = enricher.enrich_company(
                                company_name=lead['company_name'],
                                domain=domain,
                                location="Calgary, AB"
                            )

                            if company_data.get('sources_used'):
                                if not lead.get('intelligence'):
                                    lead['intelligence'] = {}
                                lead['intelligence']['multi_source'] = company_data

                            contacts_data = enricher.find_contacts(lead['company_name'], domain, limit=10)

                            if contacts_data.get('total_contacts', 0) > 0:
                                if not lead.get('intelligence'):
                                    lead['intelligence'] = {}
                                lead['intelligence']['contacts'] = contacts_data

                                if not lead.get('contact_details'):
                                    lead['contact_details'] = []

                                for contact in contacts_data['all_contacts']:
                                    lead['contact_details'].append({
                                        'email': contact.get('email'),
                                        'name': contact.get('name'),
                                        'title': contact.get('title'),
                                        'phone': contact.get('phone'),
                                        'source': contact.get('source'),
                                        'verified': contact.get('verified', False)
                                    })

                        # Log activity
                        self.log_activity(lead_id, 'enriched',
                            f'Bulk enriched with score {lead.get("signal_score", 0)}')

                        progress_text.insert(tk.END, f"  ✓ Success (Score: {lead.get('signal_score', 0)})\n", 'success')
                        success_count += 1

                    except Exception as e:
                        progress_text.insert(tk.END, f"  ✗ Error: {str(e)}\n", 'error')
                        error_count += 1

                    progress_bar['value'] = i + 1
                    progress_dialog.update()

                    # Small delay to avoid rate limiting
                    time.sleep(1)

                # Save all changes
                save_json(DATA_DIR / "leads.json", self.leads)

                # Refresh UI
                self.refresh_leads()
                self.update_stats()

                # Summary
                progress_text.insert(tk.END, "\n" + "=" * 60 + "\n")
                progress_text.insert(tk.END, "BULK ENRICHMENT COMPLETE\n", 'header')
                progress_text.insert(tk.END, f"Total Processed: {total_to_enrich}\n")
                progress_text.insert(tk.END, f"✓ Successful: {success_count}\n", 'success')
                if error_count > 0:
                    progress_text.insert(tk.END, f"✗ Errors: {error_count}\n", 'error')

                progress_label.config(text="Bulk Enrichment Complete!")

                # Configure tags
                progress_text.tag_config('success', foreground='green', font=('Arial', 9, 'bold'))
                progress_text.tag_config('error', foreground='red')
                progress_text.tag_config('header', font=('Arial', 10, 'bold'))

                # Add close button
                tk.Button(progress_dialog, text="Close", command=progress_dialog.destroy,
                         bg=COLORS['primary'], fg=COLORS['text_light'], padx=20, pady=8).pack(pady=10)

            except Exception as e:
                progress_text.insert(tk.END, f"\n\nFATAL ERROR: {str(e)}\n", 'error')
                progress_label.config(text="Bulk Enrichment Failed!")

        # Start enrichment thread
        thread = Thread(target=enrich_thread)
        thread.daemon = True
        thread.start()

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

        # Log activity
        self.log_activity(self.current_draft_lead_id, 'contacted',
            f'Email sent, follow-up scheduled for {followup.strftime("%Y-%m-%d")}')

        save_json(DATA_DIR / "leads.json", self.leads)
        self.update_outreach_stats()
        self.update_stats()

        messagebox.showinfo("Success", f"Marked as sent! Follow-up scheduled for {followup.strftime('%Y-%m-%d')}")

    def check_tenders(self):
        """Check for new tenders (placeholder - would integrate with tender_monitoring.py)"""
        messagebox.showinfo("Info", "Tender checking functionality would connect to tender APIs here.\n\n" +
                           "This requires API keys and is a placeholder in the desktop version.")

    def refresh_api_credits(self):
        """Refresh and display API credits"""
        self.root.config(cursor="wait")
        self.root.update()

        try:
            credits = self.get_api_credits()

            # Update display
            self.credits_display.config(state=tk.NORMAL)
            self.credits_display.delete(1.0, tk.END)

            if not credits:
                self.credits_display.insert(tk.END, "No API keys configured or enabled.\n\n")
                self.credits_display.insert(tk.END, "Configure API keys above and enable them to see credit information.")
            else:
                self.credits_display.insert(tk.END, "API CREDIT SUMMARY\n")
                self.credits_display.insert(tk.END, "=" * 70 + "\n\n")

                for api_name, info in credits.items():
                    available = info.get('available', 'N/A')
                    status = info.get('status', 'Unknown')

                    self.credits_display.insert(tk.END, f"{api_name.upper().replace('_', ' ')}:\n")
                    self.credits_display.insert(tk.END, f"  Credits: {available}\n")
                    self.credits_display.insert(tk.END, f"  Status: {status}\n\n")

                self.credits_display.insert(tk.END, "-" * 70 + "\n\n")
                self.credits_display.insert(tk.END, "NOTE: Most APIs don't provide programmatic credit checking.\n")
                self.credits_display.insert(tk.END, "Check the respective dashboards for accurate credit counts.\n")
                self.credits_display.insert(tk.END, "\nFree Tier Limits:\n")
                self.credits_display.insert(tk.END, "  • Hunter.io: 50 requests/month\n")
                self.credits_display.insert(tk.END, "  • Apollo.io: 50 credits/month\n")
                self.credits_display.insert(tk.END, "  • PeopleDataLabs: 1,000 requests/month\n")
                self.credits_display.insert(tk.END, "  • Google Places: $200 credit/month\n")
                self.credits_display.insert(tk.END, "  • ZeroBounce: 100 validations/month\n")
                self.credits_display.insert(tk.END, "  • Proxycurl: Pay-per-use (~$0.02-0.03/profile)\n")

            self.credits_display.config(state=tk.DISABLED)

        except Exception as e:
            self.credits_display.config(state=tk.NORMAL)
            self.credits_display.delete(1.0, tk.END)
            self.credits_display.insert(tk.END, f"Error fetching credits:\n{str(e)}")
            self.credits_display.config(state=tk.DISABLED)

        self.root.config(cursor="")

    def save_settings(self):
        """Save settings"""
        for key, var in self.config_vars.items():
            if key in ['tender_keywords', 'tender_locations']:
                # Convert comma-separated to list
                value = [s.strip() for s in var.get().split(',') if s.strip()]
                self.config[key] = value
            elif key.endswith('_enabled'):
                # Save boolean values
                self.config[key] = var.get()
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
