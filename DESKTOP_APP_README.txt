========================================
CALGARY LEAD GENERATOR - DESKTOP VERSION
========================================

This is a native desktop application - NO BROWSER NEEDED!

========================================
REQUIREMENTS
========================================

1. Python 3.8 or higher (comes with Tkinter)
2. Required Python packages (install once)

========================================
INSTALLATION - FIRST TIME ONLY
========================================

Step 1: Install Required Packages
----------------------------------
Open Command Prompt (Windows) or Terminal (Mac) and navigate to this folder.

Windows:
  cd path\to\LeadGENApp
  pip install -r requirements.txt

Mac:
  cd path/to/LeadGENApp
  pip3 install -r requirements.txt

========================================
HOW TO RUN THE APPLICATION
========================================

EASIEST METHOD (Windows):
-------------------------
Double-click the file: START_DESKTOP_APP.bat

This will launch the desktop application window.


MANUAL METHOD (Windows):
------------------------
1. Open Command Prompt
2. Navigate to this folder: cd path\to\LeadGENApp
3. Run: python desktop_app.py


MANUAL METHOD (Mac):
-------------------
1. Open Terminal
2. Navigate to this folder: cd path/to/LeadGENApp
3. Run: python3 desktop_app.py

========================================
USING THE APPLICATION
========================================

The application has 6 tabs:

📋 LEADS TAB
- View all your leads in a table
- Search and filter by status
- Double-click any lead to edit it
- Delete leads using the Delete button

➕ ADD NEW TAB
- Manually add new company leads
- Fill in company info, contact details, etc.
- Click "Add Lead" to save
- Click "Add & Scrape Website" to automatically find emails/phones

📁 IMPORT TAB
- Import from LinkedIn CSV export
- Import from generic CSV files
- Filter options for LinkedIn imports

📧 OUTREACH TAB
- See outreach statistics (sent, replied, due for follow-up)
- Generate personalized email drafts
- Copy drafts to clipboard
- Mark emails as sent (auto-schedules follow-ups)

📢 TENDERS TAB
- View government/public contract opportunities
- Monitor tenders matching your keywords

⚙️ SETTINGS TAB
- Enter your contact info for email templates
- Configure Jobber CRM credentials
- Set tender monitoring keywords

========================================
DATA STORAGE
========================================

All data is stored locally in the "data" folder:

- leads.json      - Your leads database
- config.json     - Your settings
- tenders.json    - Tender information

These files persist between sessions. Your data is saved automatically.

========================================
KEY FEATURES
========================================

✅ NO BROWSER - Native desktop app
✅ NO JAVASCRIPT ISSUES - Pure Python/Tkinter
✅ Offline-capable for most functions
✅ Fast and responsive
✅ Automatic data saving
✅ ENHANCED WEBSITE SCRAPING - Automatically checks up to 10 pages per website
   • Finds contact, about, team pages automatically
   • Discovers multiple emails and phone numbers
   • More thorough than basic single-page scraping
✅ Buying signal detection across multiple pages
✅ Email template generation
✅ LinkedIn integration
✅ CSV import/export

========================================
HOW ENHANCED SCRAPING WORKS
========================================

When you click "Add & Scrape" or "Scrape Website" in the edit dialog:

1. The system automatically discovers pages on the website
2. Prioritizes contact-related pages (contact, about, team, careers)
3. Scrapes up to 10 pages per website
4. Collects ALL emails and phone numbers found
5. Detects buying signals across all pages
6. Takes 10-15 seconds instead of 2-3 seconds
7. Finds MORE information than single-page scraping

Example: For cmcmanufacturing.com
• Old scraper: 1 email from homepage
• New scraper: 2 emails + 1 phone from 10 pages (including contact page)

========================================
DIFFERENCES FROM WEB VERSION
========================================

ADVANTAGES:
- No browser compatibility issues
- Faster performance
- Works offline
- Traditional desktop interface
- More reliable
- Enhanced multi-page scraping

LIMITATIONS:
- Tender checking requires manual API setup
- Jobber sync requires additional configuration
- Scraping takes longer (10-15 sec vs 2-3 sec) but finds more data

========================================
TROUBLESHOOTING
========================================

Problem: "No module named tkinter"
Solution: Tkinter comes with Python. Reinstall Python from python.org

Problem: Application won't start
Solution: Make sure you installed requirements with: pip install -r requirements.txt

Problem: "Import error" for linkedin_parser
Solution: The LinkedIn import uses a simplified built-in parser

Problem: Window is too small/big
Solution: You can resize the window by dragging the corners

========================================
EXPORTING YOUR LEADS
========================================

Click File → Export Leads to CSV
This creates a CSV file you can open in Excel

========================================
SUPPORT
========================================

For issues or questions:
1. Check this README
2. Verify Python and packages are installed correctly
3. Make sure you're in the correct folder when running commands

========================================
VERSION
========================================

Desktop App Version 2.0
Last Updated: January 2025
